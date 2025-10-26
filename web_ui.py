
from flask import Flask, render_template, jsonify, request, send_from_directory

import json
import os
from pathlib import Path
import markdown

import random

app = Flask(__name__)

def add_extra_data(projects):
    """Add computed fields for backwards compatibility and new v2.0 features"""
    for project in projects:
        scores = project.get('scores', {})

        # Backwards compatibility
        if 'potential_score' not in scores:
            scores['potential_score'] = max(0, (scores.get('value_score', 0) * 2) - scores.get('risk_score', 0))

        # Add 6-category scores if not present (v2.0 format)
        if 'code_quality_score' not in scores:
            scores['code_quality_score'] = scores.get('value_score', 5)
        if 'deployment_readiness_score' not in scores:
            scores['deployment_readiness_score'] = 10 - scores.get('risk_score', 5)
        if 'documentation_score' not in scores:
            scores['documentation_score'] = 7 if project.get('facts', {}).get('has_readme') else 3
        if 'borg_fit_score' not in scores:
            scores['borg_fit_score'] = scores.get('value_score', 5)
        if 'mvp_proximity_score' not in scores:
            stage = scores.get('stage', 'prototype')
            mvp_map = {'prototype': 3, 'mvp': 7, 'beta': 9, 'production': 10}
            scores['mvp_proximity_score'] = mvp_map.get(stage, 5)
        if 'monetization_viability_score' not in scores:
            scores['monetization_viability_score'] = scores.get('value_score', 5)

        # Deployment status
        if 'deployment_status' not in scores:
            deploy_score = scores.get('deployment_readiness_score', 5)
            if deploy_score >= 7:
                scores['deployment_status'] = 'ready'
            elif deploy_score >= 4:
                scores['deployment_status'] = 'warning'
            else:
                scores['deployment_status'] = 'blocked'

        # Monetization (legacy field)
        if 'monetization' not in project:
            project['monetization'] = {
                'realtime': round(random.uniform(0, 1000), 2)
            }

        project['scores'] = scores
    return projects

@app.route('/')
def index():
    # Check if borg_dashboard.json exists
    if not os.path.exists('borg_dashboard.json'):
        return "borg_dashboard.json not found. Please run the scan first."

    with open('borg_dashboard.json', 'r') as f:
        projects = json.load(f)
    
    projects = add_extra_data(projects)
    
    return render_template('index.html', projects=projects)

@app.route('/api/projects')
def api_projects():
    if not os.path.exists('borg_dashboard.json'):
        return jsonify({"error": "borg_dashboard.json not found. Please run the scan first."}), 404
        
    with open('borg_dashboard.json', 'r') as f:
        projects = json.load(f)
        
    projects = add_extra_data(projects)
    
    return jsonify(projects)


import urllib.request

def chat_with_llm(user_message, projects):
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return "OPENROUTER_API_KEY not set."

    summarized_projects = []
    for project in projects:
        summarized_projects.append({
            'name': project['facts']['name'],
            'description': project['suggestions']['description']
        })

    prompt = f"""
    You are a helpful assistant who can answer questions about software projects.
    Here is a list of projects:
    {json.dumps(summarized_projects, indent=2)}

    The user asks: {user_message}

    Please provide a helpful and conversational response.
    """

    payload = json.dumps({
        "model": "anthropic/claude-3-haiku:beta",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        method="POST",
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://borg-tools',
            'X-Title': 'Borg Tools Scanner'
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.load(resp)
        content = data['choices'][0]['message']['content']
        return content
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error calling LLM: {e}"

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    user_message = data.get('message')

    if not os.path.exists('borg_dashboard.json'):
        return jsonify({"error": "borg_dashboard.json not found. Please run the scan first."}), 404

    with open('borg_dashboard.json', 'r') as f:
        projects = json.load(f)

    response_text = chat_with_llm(user_message, projects)

    return jsonify({'response': response_text})

@app.route('/api/vibesummary/<project_name>')
def get_vibesummary(project_name):
    """Fetch VibeSummary.md content for a project"""
    # Load projects to find the path
    if not os.path.exists('borg_dashboard.json'):
        return jsonify({"error": "borg_dashboard.json not found"}), 404

    with open('borg_dashboard.json', 'r') as f:
        projects = json.load(f)

    # Find the project
    project = None
    for p in projects:
        if p.get('facts', {}).get('name') == project_name:
            project = p
            break

    if not project:
        return jsonify({"error": f"Project {project_name} not found"}), 404

    # Try to find VibeSummary.md in the project directory
    project_path = Path(project.get('facts', {}).get('path', ''))
    vibesummary_paths = [
        project_path / 'VibeSummary.md',
        project_path / 'docs' / 'VibeSummary.md',
        project_path / 'specs' / 'VibeSummary.md',
    ]

    for vibe_path in vibesummary_paths:
        if vibe_path.exists():
            with open(vibe_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({
                'content': content,
                'path': str(vibe_path)
            })

    # If not found, return a default message
    return jsonify({
        'content': f"# VibeSummary for {project_name}\n\nVibeSummary not yet generated. Run the scanner with `--deep-scan` to generate.",
        'path': None
    })

@app.route('/api/project/<project_name>')
def get_project_detail(project_name):
    """Get detailed project information"""
    if not os.path.exists('borg_dashboard.json'):
        return jsonify({"error": "borg_dashboard.json not found"}), 404

    with open('borg_dashboard.json', 'r') as f:
        projects = json.load(f)

    projects = add_extra_data(projects)

    for project in projects:
        if project.get('facts', {}).get('name') == project_name:
            return jsonify(project)

    return jsonify({"error": f"Project {project_name} not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5001)
