"""
Example usage of deployment_detector.py

This demonstrates how to use the deployment detector in your scanning workflow.

Created by The Collective Borg.tools
"""

import sys
from pathlib import Path
import json

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from deployment_detector import detect_deployment


def example_basic_usage():
    """Basic usage example"""
    print("=" * 60)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 60)

    result = detect_deployment(
        project_path="/Users/wojciechwiesner/ai/_Borg.tools_scan",
        languages=["python"],
        facts={"deps": {"python": []}, "has_ci": False}
    )

    print(f"\nDeployment Readiness: {result['deployment']['readiness_score']}/10")
    print(f"Is Deployable: {result['deployment']['is_deployable']}")
    print(f"Target Platform: {result['deployment']['target_platform']}")
    print(f"\nBlockers ({len(result['deployment']['blockers'])}):")
    for blocker in result['deployment']['blockers']:
        print(f"  [{blocker['severity']}] {blocker['description']}")
        print(f"      → {blocker['suggestion']}")
        print(f"      Time: {blocker['estimated_fix_time_hours']}h")


def example_with_docker():
    """Example with Docker project"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Docker Project Analysis")
    print("=" * 60)

    result = detect_deployment(
        project_path="/tmp/test_deployment_project",
        languages=["python"],
        facts={
            "deps": {"python": ["flask", "gunicorn", "psycopg2-binary"]},
            "has_ci": False
        }
    )

    deployment = result['deployment']

    print(f"\nDeployment Type: {deployment['deployment_type']}")
    print(f"Readiness Score: {deployment['readiness_score']}/10")
    print(f"Platform: {deployment['target_platform']}")

    print(f"\nDetected Artifacts:")
    for artifact, exists in deployment['detected_artifacts'].items():
        status = "✅" if exists else "❌"
        print(f"  {status} {artifact}")

    print(f"\nEnvironment Variables ({len(deployment['environment_vars'])}):")
    for var in deployment['environment_vars']:
        doc_status = "📝" if var['documented'] else "⚠️ "
        print(f"  {doc_status} {var['name']}")

    print(f"\nServices: {', '.join(deployment['services']) if deployment['services'] else 'None'}")
    print(f"Ports: {', '.join(map(str, deployment['ports'])) if deployment['ports'] else 'None'}")

    print(f"\nMVP Checklist (Total: {deployment['estimated_hours_to_mvp']}h):")
    for item in deployment['mvp_checklist']:
        status_icon = {"done": "✅", "blocked": "🔴", "missing": "⚠️", "pending": "⏳"}
        icon = status_icon.get(item['status'], "❓")
        print(f"  {icon} [{item['status'].upper()}] {item['task']} ({item['time_hours']}h)")


def example_json_output():
    """Example showing JSON output for integration"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: JSON Output (for integration)")
    print("=" * 60)

    result = detect_deployment(
        project_path="/tmp/test_no_docker",
        languages=["nodejs"],
        facts={"deps": {"node": ["express"]}}
    )

    # This JSON can be integrated into larger scan results
    print(json.dumps(result, indent=2))


def example_integration_workflow():
    """Example showing integration with main scanner"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Integration Workflow")
    print("=" * 60)

    # Simulate scanner flow
    projects = [
        {"path": "/tmp/test_deployment_project", "languages": ["python"]},
        {"path": "/tmp/test_no_docker", "languages": ["nodejs"]},
    ]

    results = []
    for project in projects:
        print(f"\n🔍 Scanning: {project['path']}")

        result = detect_deployment(
            project_path=project['path'],
            languages=project['languages'],
            facts={"deps": {}}
        )

        deployment = result['deployment']
        results.append({
            "project": project['path'],
            "score": deployment['readiness_score'],
            "deployable": deployment['is_deployable'],
            "platform": deployment['target_platform'],
            "blockers": len(deployment['blockers']),
            "hours_to_mvp": deployment['estimated_hours_to_mvp']
        })

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"{r['project']}")
        print(f"  Score: {r['score']}/10 | Deployable: {r['deployable']}")
        print(f"  Platform: {r['platform']} | Blockers: {r['blockers']}")
        print(f"  MVP Time: {r['hours_to_mvp']}h\n")


if __name__ == "__main__":
    example_basic_usage()
    example_with_docker()
    example_json_output()
    example_integration_workflow()

    print("\n" + "=" * 60)
    print("✅ All examples completed successfully!")
    print("=" * 60)
