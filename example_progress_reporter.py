#!/usr/bin/env python3
"""
Example integration of ProgressReporter with Borg Tools Scanner

This demonstrates how to integrate the rich progress reporter
into the main scanning workflow.

Created by The Collective Borg.tools
"""

import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.progress_reporter import ProgressReporter


def example_scan_with_progress():
    """
    Simulate scanning projects with rich progress output.

    This shows how the ProgressReporter would be integrated
    into the actual borg_tools_scan.py main() function.
    """

    # Initialize reporter
    reporter = ProgressReporter(verbose=True)

    # Show header
    reporter.show_header("🤖 Borg Tools Project Scanner")

    # Mock project data
    mock_projects = [
        {
            "name": "borg-tools-mvp",
            "files": 142,
            "architecture": "Hexagonal (DDD)",
            "security_issues": 3,
            "stage": "beta",
            "value": 7.5,
            "risk": 3.2,
            "priority": 14,
            "languages": ["python", "typescript"],
            "errors": []
        },
        {
            "name": "xpress-delivery-api",
            "files": 87,
            "architecture": "REST API",
            "security_issues": 1,
            "stage": "mvp",
            "value": 8.0,
            "risk": 2.5,
            "priority": 16,
            "languages": ["python"],
            "errors": []
        },
        {
            "name": "prototype-experiment",
            "files": 23,
            "architecture": "Monolith",
            "security_issues": 7,
            "stage": "prototype",
            "value": 4.5,
            "risk": 7.8,
            "priority": 6,
            "languages": ["python", "javascript"],
            "errors": ["brak testów", "brak CI", "brak LICENSE"]
        }
    ]

    total = len(mock_projects)
    results = []

    # Scan each project
    for idx, project in enumerate(mock_projects, 1):
        # Start project
        reporter.start_project(project["name"], idx, total)

        # Log scanning steps
        reporter.log_step("📄", f"Scanning {project['files']} Python files...", "cyan")

        # Show progress for file scanning (simulate)
        for i in range(0, project['files'] + 1, max(1, project['files'] // 5)):
            reporter.show_progress_bar(
                current=min(i, project['files']),
                total=project['files'],
                description="Files"
            )

        # Architecture detection
        reporter.log_step("🏗️", f"Architecture: {project['architecture']}", "blue")

        # Security scan
        issues = project['security_issues']
        if issues == 0:
            reporter.log_step("🔒", "Security scan: No issues found", "green")
        elif issues <= 3:
            reporter.log_step("🔒", f"Security scan: {issues} issues found", "yellow")
        else:
            reporter.log_step("🔒", f"Security scan: {issues} issues found", "red")

        # Code quality analysis
        if project['value'] >= 7:
            reporter.log_step("📊", "Code quality: Good", "green")
        elif project['value'] >= 5:
            reporter.log_step("📊", "Code quality: Fair", "yellow")
        else:
            reporter.log_step("📊", "Code quality: Needs improvement", "red")

        # Complete project
        scores = {
            "stage": project['stage'],
            "value_score": project['value'],
            "risk_score": project['risk'],
            "priority": project['priority']
        }
        reporter.complete_project(scores)

        # Collect for summary
        results.append({
            "name": project['name'],
            "stage": project['stage'],
            "value_score": project['value'],
            "risk_score": project['risk'],
            "priority": project['priority'],
            "languages": project['languages'],
            "fundamental_errors": project['errors']
        })

    # Show summary table
    reporter.show_summary_table(results)

    # Calculate stats
    high_value = sum(1 for p in results if p['value_score'] >= 7)
    high_risk = sum(1 for p in results if p['risk_score'] >= 7)

    # Show footer
    reporter.show_footer({
        "total": total,
        "high_value": high_value,
        "high_risk": high_risk
    })

    print("\n✅ Scan complete! Reports generated:")
    print("   - BORG_INDEX.md")
    print("   - borg_dashboard.csv")
    print("   - borg_dashboard.json")
    print("   - Individual REPORT.md files in each project\n")


def example_minimal_output():
    """
    Example with minimal output (verbose=False).
    """
    print("\n" + "="*60)
    print("MINIMAL OUTPUT MODE")
    print("="*60 + "\n")

    reporter = ProgressReporter(verbose=False)

    # Only show start/complete without detailed steps
    reporter.start_project("quiet-project", 1, 1)
    reporter.complete_project({
        "stage": "mvp",
        "value_score": 8.0,
        "risk_score": 2.0,
        "priority": 16
    })


def example_error_handling():
    """
    Example showing error and warning messages.
    """
    print("\n" + "="*60)
    print("ERROR HANDLING DEMO")
    print("="*60 + "\n")

    reporter = ProgressReporter()

    reporter.start_project("problem-project", 1, 1)

    # Show various message types
    reporter.show_warning("Project has no README file")
    reporter.show_warning("No tests found in project")
    reporter.show_error("Failed to parse package.json - invalid JSON")

    reporter.log_step("⚠️", "Continuing with limited data...", "yellow")
    reporter.complete_project({
        "stage": "prototype",
        "value_score": 3.0,
        "risk_score": 8.5,
        "priority": 4
    })


def example_integration_points():
    """
    Show how to integrate into borg_tools_scan.py main() function.
    """
    print("\n" + "="*60)
    print("INTEGRATION GUIDE")
    print("="*60 + "\n")

    integration_code = '''
# In borg_tools_scan.py main() function:

from modules.progress_reporter import ProgressReporter

def main():
    # ... argparse setup ...

    # Initialize reporter
    reporter = ProgressReporter(verbose=True)
    reporter.show_header("Borg Tools Scanner")

    projects = list_projects(root)
    total = len(projects)
    summaries = []

    for idx, p in enumerate(projects, 1):
        # Start project
        reporter.start_project(p.name, idx, total)

        try:
            # Log scanning steps
            reporter.log_step("📄", f"Scanning files in {p.name}...", "cyan")

            # Perform scan
            ps = scan_project(p)

            # Log architecture
            if ps.facts.languages:
                langs = ", ".join(ps.facts.languages)
                reporter.log_step("🏗️", f"Languages: {langs}", "blue")

            # Log security/quality
            if ps.scores.fundamental_errors:
                reporter.show_warning(f"{len(ps.scores.fundamental_errors)} fundamental issues found")

            # Complete
            reporter.complete_project({
                "stage": ps.scores.stage,
                "value_score": ps.scores.value_score,
                "risk_score": ps.scores.risk_score,
                "priority": ps.scores.priority
            })

            summaries.append(ps)

        except Exception as e:
            reporter.show_error(f"Failed to scan {p.name}: {e}")

    # Show summary
    reporter.show_summary_table([{
        "name": ps.facts.name,
        "stage": ps.scores.stage,
        "value_score": ps.scores.value_score,
        "risk_score": ps.scores.risk_score,
        "priority": ps.scores.priority,
        "languages": ps.facts.languages,
        "fundamental_errors": ps.scores.fundamental_errors
    } for ps in summaries])

    # Footer
    reporter.show_footer({
        "total": len(summaries),
        "high_value": sum(1 for ps in summaries if ps.scores.value_score >= 7),
        "high_risk": sum(1 for ps in summaries if ps.scores.risk_score >= 7)
    })
'''

    print(integration_code)


if __name__ == "__main__":
    print("\n🎨 ProgressReporter Integration Examples\n")

    # Run examples
    print("=" * 60)
    print("FULL SCAN SIMULATION")
    print("=" * 60)
    example_scan_with_progress()

    # Other examples
    example_minimal_output()
    example_error_handling()
    example_integration_points()

    print("\n✨ All examples completed!\n")
