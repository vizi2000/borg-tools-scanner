#!/usr/bin/env python3
"""
Example: Integrating doc_analyzer with main scanner

This demonstrates how the documentation analyzer integrates into the
Borg.tools Scanner workflow.

Created by The Collective Borg.tools
"""

import sys
import json
from pathlib import Path

# Import the documentation analyzer
sys.path.insert(0, str(Path(__file__).parent / 'modules'))
from doc_analyzer import analyze_documentation


def scan_project_documentation(project_path: str) -> dict:
    """
    Main integration point for documentation analysis.

    This would be called from the main scanner after:
    1. Language detection (to know which file types to scan)
    2. Dependency analysis (to check accuracy)
    3. Code structure analysis (to find entry points)

    Args:
        project_path: Path to the project to analyze

    Returns:
        Dictionary with documentation metrics and recommendations
    """
    project_path = Path(project_path)

    print(f"\n{'='*70}")
    print(f"SCANNING: {project_path.name}")
    print(f"{'='*70}")

    # Step 1: Detect languages (would come from code_analyzer in real implementation)
    print("\n[1/4] Detecting languages...")
    languages = detect_languages(project_path)
    print(f"      Found: {', '.join(languages)}")

    # Step 2: Analyze dependencies (would come from deps_analyzer)
    print("\n[2/4] Analyzing dependencies...")
    facts = analyze_dependencies(project_path)
    print(f"      Dependencies: {sum(len(v) for v in facts['deps'].values())} total")

    # Step 3: Find entry points (would come from code_analyzer)
    print("\n[3/4] Finding entry points...")
    entry_points = find_entry_points(project_path, languages)
    print(f"      Entry points: {', '.join(entry_points) if entry_points else 'None'}")

    # Step 4: Analyze documentation
    print("\n[4/4] Analyzing documentation...")
    result = analyze_documentation(
        str(project_path),
        languages,
        facts,
        entry_points
    )

    # Generate recommendations
    recommendations = generate_recommendations(result)

    # Combine results
    final_result = {
        **result,
        'recommendations': recommendations,
        'summary': generate_summary(result)
    }

    return final_result


def detect_languages(project_path: Path) -> list:
    """
    Simplified language detection.
    In real implementation, this comes from code_analyzer module.
    """
    languages = []

    if list(project_path.glob('*.py')) or list(project_path.rglob('*.py')):
        languages.append('python')

    if list(project_path.glob('*.js')) or list(project_path.rglob('*.js')):
        languages.append('javascript')

    if (project_path / 'package.json').exists():
        languages.append('nodejs')

    return languages or ['unknown']


def analyze_dependencies(project_path: Path) -> dict:
    """
    Simplified dependency analysis.
    In real implementation, this comes from deps_analyzer module.
    """
    facts = {'deps': {}}

    # Python dependencies
    req_file = project_path / 'requirements.txt'
    if req_file.exists():
        try:
            deps = [line.strip() for line in req_file.read_text().splitlines()
                   if line.strip() and not line.startswith('#')]
            facts['deps']['python'] = deps
        except Exception:
            pass

    # Node dependencies
    pkg_json = project_path / 'package.json'
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text())
            deps = []
            for dep_type in ['dependencies', 'devDependencies']:
                if dep_type in data:
                    for name, version in data[dep_type].items():
                        deps.append(f"{name}@{version}")
            facts['deps']['nodejs'] = deps
        except Exception:
            pass

    return facts


def find_entry_points(project_path: Path, languages: list) -> list:
    """
    Find likely entry points for the project.
    In real implementation, this comes from code_analyzer module.
    """
    entry_points = []

    # Python entry points
    if 'python' in languages:
        for name in ['main.py', 'app.py', '__main__.py', 'run.py', 'server.py']:
            if (project_path / name).exists():
                entry_points.append(name)

    # Node entry points
    if 'nodejs' in languages or 'javascript' in languages:
        pkg_json = project_path / 'package.json'
        if pkg_json.exists():
            try:
                data = json.loads(pkg_json.read_text())
                if 'main' in data:
                    entry_points.append(data['main'])
            except Exception:
                pass

        for name in ['index.js', 'server.js', 'app.js']:
            if (project_path / name).exists() and name not in entry_points:
                entry_points.append(name)

    return entry_points


def generate_recommendations(result: dict) -> list:
    """
    Generate actionable recommendations based on analysis results.
    """
    recommendations = []
    doc = result['documentation']

    # Overall score recommendations
    score = doc['overall_score']
    if score < 4:
        recommendations.append({
            'priority': 'HIGH',
            'category': 'documentation',
            'action': 'Create comprehensive README with all standard sections',
            'impact': 'Critical for project adoption and maintenance'
        })
    elif score < 7:
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'documentation',
            'action': 'Improve documentation completeness and accuracy',
            'impact': 'Better developer experience'
        })

    # Missing sections
    if doc['found_docs']['readme'].get('missing_sections'):
        missing = doc['found_docs']['readme']['missing_sections']
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'documentation',
            'action': f"Add missing README sections: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}",
            'impact': 'Improved documentation completeness',
            'auto_generated': True  # We can auto-generate these!
        })

    # API documentation
    api_docs = doc['found_docs']['api_docs']
    if api_docs['detected_endpoints'] > 0 and api_docs['documented_endpoints'] < api_docs['detected_endpoints']:
        coverage = (api_docs['documented_endpoints'] / api_docs['detected_endpoints']) * 100
        recommendations.append({
            'priority': 'HIGH' if coverage < 50 else 'MEDIUM',
            'category': 'api_documentation',
            'action': f"Document {api_docs['detected_endpoints'] - api_docs['documented_endpoints']} undocumented API endpoints",
            'impact': 'Essential for API usability',
            'auto_generated': True
        })

    # Accuracy issues
    for issue in doc['accuracy_issues']:
        recommendations.append({
            'priority': issue['severity'],
            'category': 'accuracy',
            'action': f"Fix: {issue['description']}",
            'impact': 'Prevents user confusion and errors'
        })

    return recommendations


def generate_summary(result: dict) -> str:
    """
    Generate human-readable summary of documentation quality.
    """
    doc = result['documentation']
    score = doc['overall_score']

    if score >= 8:
        quality = "Excellent"
        emoji = "🌟"
    elif score >= 6:
        quality = "Good"
        emoji = "✅"
    elif score >= 4:
        quality = "Fair"
        emoji = "⚠️"
    else:
        quality = "Poor"
        emoji = "❌"

    summary = f"{emoji} {quality} ({score}/10)\n"
    summary += f"   Completeness: {doc['completeness']:.0%}\n"
    summary += f"   Accuracy: {doc['accuracy']:.0%}\n"

    if doc['accuracy_issues']:
        summary += f"   Issues: {len(doc['accuracy_issues'])} detected"

    return summary


def main():
    """
    Example usage: Scan a project's documentation.
    """
    import sys

    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        # Default to current project
        project_path = Path(__file__).parent

    result = scan_project_documentation(str(project_path))

    # Display summary
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\n{result['summary']}")

    # Display recommendations
    if result['recommendations']:
        print(f"\n{'='*70}")
        print("RECOMMENDATIONS")
        print("="*70)

        for i, rec in enumerate(result['recommendations'][:5], 1):  # Show top 5
            priority_emoji = "🔴" if rec['priority'] == 'HIGH' else "🟡" if rec['priority'] == 'MEDIUM' else "🟢"
            print(f"\n{i}. {priority_emoji} [{rec['priority']}] {rec['category'].upper()}")
            print(f"   Action: {rec['action']}")
            print(f"   Impact: {rec['impact']}")
            if rec.get('auto_generated'):
                print(f"   💡 Can be auto-generated!")

        if len(result['recommendations']) > 5:
            print(f"\n   ... and {len(result['recommendations']) - 5} more")

    # Save detailed results
    output_file = Path(project_path) / 'documentation_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n{'='*70}")
    print(f"📄 Detailed report saved to: {output_file}")
    print("="*70)


if __name__ == '__main__':
    main()
