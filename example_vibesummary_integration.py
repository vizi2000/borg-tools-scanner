#!/usr/bin/env python3
"""
Example: Integration of VibeSummary Generator with Full Scanner Pipeline

This demonstrates how to use the VibeSummary generator after collecting
all analysis data from:
- Task 1A: Code Analyzer
- Task 1B: Deployment Detector
- Task 1C: Documentation Analyzer
- Task 2A+2C: LLM Orchestrator + Response Handler

Created by The Collective Borg.tools
"""

import sys
import json
from pathlib import Path

# Import all analysis modules
sys.path.insert(0, str(Path(__file__).parent / 'modules'))

from code_analyzer import analyze_code
from deployment_detector import detect_deployment
from doc_analyzer import analyze_documentation
from vibesummary_generator import generate_vibesummary


def run_full_analysis(project_path: str, project_name: str = None) -> dict:
    """
    Run complete project analysis and generate VibeSummary.

    This is the complete integration workflow:
    1. Analyze code quality
    2. Detect deployment readiness
    3. Analyze documentation
    4. (Would call LLM orchestrator in production)
    5. Generate VibeSummary.md

    Args:
        project_path: Path to the project to analyze
        project_name: Optional project name (defaults to directory name)

    Returns:
        Dictionary with all analysis results
    """
    project_path = Path(project_path).resolve()
    if project_name is None:
        project_name = project_path.name

    print(f"\n{'='*80}")
    print(f"BORG.TOOLS SCANNER V2.0 - FULL ANALYSIS")
    print(f"{'='*80}")
    print(f"Project: {project_name}")
    print(f"Path: {project_path}")
    print(f"{'='*80}\n")

    # Step 1: Language detection (simple heuristic)
    print("[1/5] Detecting languages...")
    languages = detect_languages(project_path)
    print(f"      Found: {', '.join(languages)}\n")

    # Step 2: Code analysis
    print("[2/5] Analyzing code quality...")
    code_analysis = analyze_code(str(project_path), languages)
    print(f"      Code Quality Score: {code_analysis['code_quality']['overall_score']}/10\n")

    # Step 3: Deployment detection
    print("[3/5] Detecting deployment configuration...")
    facts = {'deps': {}}  # Would be populated by dependency analyzer
    deployment_analysis = detect_deployment(str(project_path), languages, facts)
    print(f"      Deployment Readiness: {deployment_analysis['deployment']['readiness_score']}/10\n")

    # Step 4: Documentation analysis
    print("[4/5] Analyzing documentation...")
    doc_analysis = analyze_documentation(str(project_path), languages, facts)
    print(f"      Documentation Score: {doc_analysis['documentation']['overall_score']}/10\n")

    # Step 5: LLM analysis (mocked for this example)
    print("[5/5] Running LLM analysis...")
    print("      (Using mock LLM data for demonstration)")
    llm_analysis = generate_mock_llm_analysis(
        project_name, code_analysis, deployment_analysis, doc_analysis
    )
    print(f"      Overall Assessment: {llm_analysis['aggregator']['data']['overall_assessment']}\n")

    # Combine all results
    project_summary = {
        'project_name': project_name,
        'project_path': str(project_path),
        'languages': languages,
        'code_analysis': code_analysis,
        'deployment_analysis': deployment_analysis,
        'documentation_analysis': doc_analysis,
        'llm_analysis': llm_analysis
    }

    return project_summary


def detect_languages(project_path: Path) -> list:
    """Simple language detection based on file extensions"""
    languages = []

    if list(project_path.rglob('*.py')):
        languages.append('python')

    if list(project_path.rglob('*.js')) or list(project_path.rglob('*.ts')):
        languages.append('javascript')

    if (project_path / 'package.json').exists():
        if 'nodejs' not in languages:
            languages.append('nodejs')

    if list(project_path.rglob('*.go')):
        languages.append('go')

    if list(project_path.rglob('*.rs')):
        languages.append('rust')

    return languages or ['unknown']


def generate_mock_llm_analysis(project_name: str, code_analysis: dict,
                               deployment_analysis: dict, doc_analysis: dict) -> dict:
    """
    Generate mock LLM analysis for demonstration.

    In production, this would call the actual LLM orchestrator.
    """
    code_score = code_analysis['code_quality']['overall_score']
    deploy_score = deployment_analysis['deployment']['readiness_score']
    doc_score = doc_analysis['documentation']['overall_score']

    # Simple assessment based on scores
    avg_score = (code_score + deploy_score + doc_score) / 3

    if avg_score >= 8:
        assessment = f"{project_name} is production-ready with excellent quality across all areas"
    elif avg_score >= 6:
        assessment = f"{project_name} is a solid project with good fundamentals, close to production-ready"
    elif avg_score >= 4:
        assessment = f"{project_name} shows promise but needs improvement in key areas"
    else:
        assessment = f"{project_name} is in early stages and requires significant work"

    # Generate priorities based on weakest areas
    priorities = []
    if code_score < 6:
        priorities.append("Improve code quality and reduce complexity")
    if deploy_score < 6:
        priorities.append("Complete deployment configuration")
    if doc_score < 6:
        priorities.append("Enhance documentation completeness")

    if not priorities:
        priorities = ["Add comprehensive test coverage", "Setup CI/CD pipeline", "Add monitoring and observability"]

    return {
        'business': {
            'data': {
                'problem_solved': f"Analysis suggests {project_name} addresses developer productivity and automation needs",
                'target_audience': 'Software developers and engineering teams',
                'monetization_strategy': 'Open-source with enterprise support options' if code_score >= 7 else 'Not ready for monetization',
                'market_viability': min(10, int(avg_score) + 1),
                'portfolio_suitable': avg_score >= 6,
                'portfolio_pitch': f"{project_name}: Well-architected solution demonstrating best practices" if avg_score >= 6 else ""
            }
        },
        'aggregator': {
            'data': {
                'overall_assessment': assessment,
                'top_priorities': priorities[:5],
                'vibecodibility_score': int(avg_score),
                'borg_tools_fit': 8 if deployment_analysis['deployment']['deployment_type'] == 'docker' else 6
            }
        },
        'architect': {
            'data': {
                'design_patterns': ['MVC', 'Factory'],  # Simplified for mock
                'scalability_notes': 'Architecture supports horizontal scaling' if code_score >= 7 else 'Scalability needs assessment',
                'architecture_assessment': f"Code follows {code_analysis['code_quality']['architecture_pattern']} pattern",
                'technical_debt_priority': 'low' if code_score >= 8 else 'medium' if code_score >= 6 else 'high'
            }
        },
        'deployment': {
            'data': {
                'mvp_roadmap': ['Setup CI/CD', 'Add monitoring', 'Complete documentation'],  # Simplified list
                'deployment_strategy': deployment_analysis['deployment']['deployment_type'],
                'infrastructure_recommendations': f"Target platform: {deployment_analysis['deployment']['target_platform']}"
            }
        }
    }


def main():
    """
    Main entry point for full analysis + VibeSummary generation.
    """
    import sys

    if len(sys.argv) > 1:
        project_path = sys.argv[1]
        project_name = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # Default to analyzing the scanner itself
        project_path = Path(__file__).parent
        project_name = "Borg.tools Scanner V2"

    # Run full analysis
    project_summary = run_full_analysis(str(project_path), project_name)

    # Generate VibeSummary
    print("="*80)
    print("GENERATING VIBESUMMARY")
    print("="*80 + "\n")

    output_path = Path(project_path) / 'VibeSummary.md'
    success = generate_vibesummary(project_summary, output_path)

    if success:
        print(f"\n{'='*80}")
        print("ANALYSIS COMPLETE")
        print("="*80)
        print(f"\n✅ VibeSummary generated: {output_path}")
        print(f"\n📊 Overall Vibecodibility: {project_summary['llm_analysis']['aggregator']['data']['vibecodibility_score']}/10")

        # Display summary stats
        print(f"\n📈 Score Breakdown:")
        print(f"   - Code Quality: {project_summary['code_analysis']['code_quality']['overall_score']}/10")
        print(f"   - Deployment: {project_summary['deployment_analysis']['deployment']['readiness_score']}/10")
        print(f"   - Documentation: {project_summary['documentation_analysis']['documentation']['overall_score']}/10")
        print(f"   - Borg.tools Fit: {project_summary['llm_analysis']['aggregator']['data']['borg_tools_fit']}/10")

        print(f"\n🎯 Top Priorities:")
        for i, priority in enumerate(project_summary['llm_analysis']['aggregator']['data']['top_priorities'][:3], 1):
            print(f"   {i}. {priority}")

        print(f"\n{'='*80}")

        # Save JSON report as well
        json_output = Path(project_path) / 'analysis_report.json'
        with open(json_output, 'w') as f:
            json.dump(project_summary, f, indent=2, default=str)
        print(f"📄 JSON report saved: {json_output}")
        print("="*80 + "\n")

        return True
    else:
        print("\n❌ VibeSummary generation failed")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
