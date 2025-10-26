#!/usr/bin/env python3
"""
Agent Zero Integration Example
Demonstrates how to integrate Agent Zero audits into the main scanner

Created by The Collective Borg.tools
"""

import json
from pathlib import Path
from typing import Dict, Optional
from modules.agent_zero_auditor import AgentZeroAuditor, AuditResults, calculate_bonus_score


def integrate_agent_zero_audit(
    project_path: Path,
    use_agent_zero: bool = False,
    workflows: list = None
) -> Dict:
    """
    Integrate Agent Zero audit into project scanning

    Args:
        project_path: Path to project to scan
        use_agent_zero: Whether to use Agent Zero for auditing
        workflows: List of workflow names to run (default: all)

    Returns:
        Dictionary with audit results and bonus score
    """
    if not use_agent_zero:
        return {
            "enabled": False,
            "bonus_score": 0.0,
            "results": None
        }

    if workflows is None:
        workflows = ["code_audit", "security_scan", "complexity_analysis"]

    auditor = AgentZeroAuditor()

    print(f"\n{'=' * 60}")
    print(f"Running Agent Zero Audits on: {project_path.name}")
    print(f"{'=' * 60}\n")

    all_results = []

    for workflow in workflows:
        print(f"📋 Running {workflow}...")

        # In production, this would use Agent Zero Bridge:
        # from modules.agent_zero_bridge import AgentZeroBridge
        # bridge = AgentZeroBridge()
        # task_id = bridge.submit_task(str(project_path), workflow)
        # raw_result = bridge.get_result(task_id)

        # For now, simulate with mock data
        raw_result = _mock_agent_zero_result(workflow)

        # Parse results
        parsed_result = auditor.parse_agent_zero_audit(raw_result, workflow)
        all_results.append(parsed_result)

        print(f"✅ {workflow} completed")
        if workflow == "code_audit":
            print(f"   Code Quality Score: {parsed_result.code_quality_score:.1f}/10")
        elif workflow == "security_scan":
            print(f"   Security Score: {parsed_result.security_score:.1f}/10")
        elif workflow == "complexity_analysis":
            print(f"   Complexity Score: {parsed_result.complexity_score:.1f}/10")
        print()

    # Aggregate results
    aggregated = auditor.aggregate_results(all_results)

    print(f"\n{'=' * 60}")
    print(f"Agent Zero Audit Summary")
    print(f"{'=' * 60}\n")
    print(f"Overall Score: {aggregated['overall_score']:.1f}/10")
    print(f"Bonus Score for Main Scanner: +{aggregated['bonus_score']:.1f} points")
    print()
    print("Recommendations:")
    for i, rec in enumerate(aggregated["recommendations"], 1):
        print(f"  {i}. {rec}")
    print()

    return {
        "enabled": True,
        "bonus_score": aggregated["bonus_score"],
        "results": aggregated,
        "raw_results": [r.__dict__ for r in all_results]
    }


def _mock_agent_zero_result(workflow: str) -> Dict:
    """Generate mock Agent Zero results for testing"""
    if workflow == "code_audit":
        return {
            "pylint_score": 7.8,
            "pylint_errors": 3,
            "pylint_warnings": 12,
            "flake8_issues": 5,
            "eslint_errors": 2,
            "eslint_warnings": 8,
            "overall_score": 7.9
        }
    elif workflow == "security_scan":
        return {
            "security_score": 8.2,
            "high_severity": 1,
            "medium_severity": 3,
            "low_severity": 7,
            "secrets_found": 0,
            "vulnerable_dependencies": 2,
            "security_issues": [
                {
                    "severity": "HIGH",
                    "file": "app.py",
                    "line": 45,
                    "issue": "Potential SQL injection",
                    "source": "semgrep"
                }
            ]
        }
    elif workflow == "complexity_analysis":
        return {
            "complexity_score": 8.5,
            "avg_cyclomatic_complexity": 8.3,
            "high_complexity_count": 3,
            "long_functions_count": 2,
            "technical_debt_score": 25.4,
            "maintainability_index": 74.6,
            "total_lines": 3500,
            "code_lines": 2800,
            "comment_ratio": 0.18,
            "complexity_warnings": [
                {
                    "type": "HIGH_COMPLEXITY",
                    "function": "process_data",
                    "file": "processor.py",
                    "complexity": 15,
                    "recommendation": "Consider refactoring to reduce complexity"
                }
            ]
        }
    else:
        return {}


def update_project_score_with_agent_zero(
    base_score: int,
    agent_zero_result: Dict
) -> int:
    """
    Update project score with Agent Zero bonus

    Args:
        base_score: Base project score from main scanner
        agent_zero_result: Result from Agent Zero audit

    Returns:
        Updated score
    """
    if not agent_zero_result["enabled"]:
        return base_score

    bonus = agent_zero_result["bonus_score"]
    updated_score = base_score + int(bonus)

    print(f"Score Update: {base_score} + {int(bonus)} (Agent Zero) = {updated_score}")

    return updated_score


# Example integration into scan_project() function
def example_scan_project_with_agent_zero(project_path: Path, use_agent_zero: bool = False) -> Dict:
    """
    Example showing how to integrate Agent Zero into main scanner's scan_project()

    This would be added to borg_tools_scan.py
    """

    # ... existing scan_project() code ...

    # Simulated base facts and scores
    facts = {
        "name": project_path.name,
        "path": str(project_path),
        "languages": ["python"],
        "has_readme": True,
        "has_tests": True,
        "has_ci": False
    }

    base_scores = {
        "stage": "mvp",
        "value_score": 7,
        "risk_score": 4,
        "priority": 12
    }

    print(f"\n{'=' * 60}")
    print(f"Scanning Project: {project_path.name}")
    print(f"{'=' * 60}\n")
    print(f"Base Value Score: {base_scores['value_score']}/10")

    # Agent Zero Integration
    if use_agent_zero:
        print("\n🤖 Initiating Agent Zero Autonomous Audit...")
        a0_result = integrate_agent_zero_audit(project_path, use_agent_zero=True)

        # Update scores with Agent Zero bonus
        base_scores["code_quality_score"] = a0_result["results"]["overall_score"]
        base_scores["value_score"] = update_project_score_with_agent_zero(
            base_scores["value_score"],
            a0_result
        )

        # Add audit details to results
        base_scores["agent_zero_audit"] = {
            "overall_score": a0_result["results"]["overall_score"],
            "bonus_applied": a0_result["bonus_score"],
            "code_quality": a0_result["results"].get("code_quality", {}),
            "security": a0_result["results"].get("security", {}),
            "complexity": a0_result["results"].get("complexity", {}),
            "recommendations": a0_result["results"]["recommendations"]
        }
    else:
        print("\n⏭️  Agent Zero audits disabled (use --use-agent-zero to enable)")

    print(f"\n{'=' * 60}")
    print(f"Final Scores")
    print(f"{'=' * 60}")
    print(f"Value Score: {base_scores['value_score']}/10")
    print(f"Risk Score: {base_scores['risk_score']}/10")
    print(f"Priority: {base_scores['priority']}/20")

    if use_agent_zero and "agent_zero_audit" in base_scores:
        print(f"\nAgent Zero Audit:")
        print(f"  Overall Score: {base_scores['agent_zero_audit']['overall_score']:.1f}/10")
        print(f"  Bonus Applied: +{base_scores['agent_zero_audit']['bonus_applied']:.1f}")

    return {
        "facts": facts,
        "scores": base_scores
    }


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Agent Zero Integration Example")
    print("=" * 60)

    # Example 1: Without Agent Zero
    print("\n\n### EXAMPLE 1: Standard Scan (No Agent Zero) ###\n")
    project_path = Path.cwd()
    result1 = example_scan_project_with_agent_zero(project_path, use_agent_zero=False)

    # Example 2: With Agent Zero
    print("\n\n### EXAMPLE 2: Scan with Agent Zero Audits ###\n")
    result2 = example_scan_project_with_agent_zero(project_path, use_agent_zero=True)

    # Show the difference
    print("\n\n### COMPARISON ###\n")
    print(f"Without Agent Zero: Value Score = {result1['scores']['value_score']}")
    print(f"With Agent Zero:    Value Score = {result2['scores']['value_score']}")
    print(f"Improvement: +{result2['scores']['value_score'] - result1['scores']['value_score']} points")

    # Save example output
    output_file = Path("agent_zero_example_output.json")
    with open(output_file, 'w') as f:
        json.dump({
            "without_agent_zero": result1,
            "with_agent_zero": result2
        }, f, indent=2, default=str)

    print(f"\n✅ Example output saved to: {output_file}")
