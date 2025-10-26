#!/usr/bin/env python3
"""
Agent Zero Autonomous Code Auditor
Workflow orchestration and result parsing for Agent Zero code audits

Created by The Collective Borg.tools
"""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


@dataclass
class AuditResults:
    """Standardized audit results from Agent Zero"""
    # Code Quality
    code_quality_score: float = 0.0
    pylint_score: float = 0.0
    pylint_errors: int = 0
    pylint_warnings: int = 0
    flake8_issues: int = 0
    eslint_errors: int = 0
    eslint_warnings: int = 0
    overall_score: float = 0.0

    # Security
    security_score: float = 10.0
    high_severity_issues: int = 0
    medium_severity_issues: int = 0
    low_severity_issues: int = 0
    secrets_found: int = 0
    vulnerable_dependencies: int = 0
    security_issues: List[Dict] = field(default_factory=list)

    # Complexity
    complexity_score: float = 10.0
    avg_cyclomatic_complexity: float = 0.0
    high_complexity_count: int = 0
    long_functions_count: int = 0
    technical_debt_score: float = 0.0
    maintainability_index: float = 100.0
    complexity_warnings: List[Dict] = field(default_factory=list)

    # Aggregate metrics
    total_lines: int = 0
    code_lines: int = 0
    comment_ratio: float = 0.0

    # Metadata
    workflow: str = ""
    duration: float = 0.0
    success: bool = True
    error_message: str = ""


class AgentZeroAuditor:
    """
    Agent Zero Auditor - Autonomous code audit workflow executor
    """

    def __init__(self, workflows_dir: Optional[Path] = None):
        """
        Initialize Agent Zero Auditor

        Args:
            workflows_dir: Directory containing workflow YAML files
        """
        self.workflows_dir = workflows_dir or Path(__file__).parent.parent / "agent_zero_workflows"
        self.available_workflows = self._discover_workflows()

    def _discover_workflows(self) -> Dict[str, Path]:
        """Discover available workflow YAML files"""
        workflows = {}
        if self.workflows_dir.exists():
            for yaml_file in self.workflows_dir.glob("*.yaml"):
                workflows[yaml_file.stem] = yaml_file
        return workflows

    def load_workflow(self, workflow_name: str) -> Optional[Dict]:
        """
        Load a workflow YAML file

        Args:
            workflow_name: Name of workflow (without .yaml extension)

        Returns:
            Workflow configuration dictionary or None if not found
        """
        if workflow_name not in self.available_workflows:
            return None

        workflow_path = self.available_workflows[workflow_name]
        try:
            with open(workflow_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading workflow {workflow_name}: {e}")
            return None

    def parse_code_audit_results(self, raw_result: Dict) -> AuditResults:
        """
        Parse code audit workflow results

        Args:
            raw_result: Raw result dictionary from Agent Zero

        Returns:
            Standardized AuditResults
        """
        results = AuditResults(workflow="code_audit")

        # Extract code quality metrics
        results.overall_score = raw_result.get('overall_score', 0.0)
        results.code_quality_score = raw_result.get('overall_score', 0.0)
        results.pylint_score = raw_result.get('pylint_score', 0.0)
        results.pylint_errors = raw_result.get('pylint_errors', 0)
        results.pylint_warnings = raw_result.get('pylint_warnings', 0)
        results.flake8_issues = raw_result.get('flake8_issues', 0)
        results.eslint_errors = raw_result.get('eslint_errors', 0)
        results.eslint_warnings = raw_result.get('eslint_warnings', 0)

        return results

    def parse_security_scan_results(self, raw_result: Dict) -> AuditResults:
        """
        Parse security scan workflow results

        Args:
            raw_result: Raw result dictionary from Agent Zero

        Returns:
            Standardized AuditResults
        """
        results = AuditResults(workflow="security_scan")

        # Extract security metrics
        results.security_score = raw_result.get('security_score', 10.0)
        results.high_severity_issues = raw_result.get('high_severity', 0)
        results.medium_severity_issues = raw_result.get('medium_severity', 0)
        results.low_severity_issues = raw_result.get('low_severity', 0)
        results.secrets_found = raw_result.get('secrets_found', 0)
        results.vulnerable_dependencies = raw_result.get('vulnerable_dependencies', 0)
        results.security_issues = raw_result.get('security_issues', [])

        return results

    def parse_complexity_analysis_results(self, raw_result: Dict) -> AuditResults:
        """
        Parse complexity analysis workflow results

        Args:
            raw_result: Raw result dictionary from Agent Zero

        Returns:
            Standardized AuditResults
        """
        results = AuditResults(workflow="complexity_analysis")

        # Extract complexity metrics
        results.complexity_score = raw_result.get('complexity_score', 10.0)
        results.avg_cyclomatic_complexity = raw_result.get('avg_cyclomatic_complexity', 0.0)
        results.high_complexity_count = raw_result.get('high_complexity_count', 0)
        results.long_functions_count = raw_result.get('long_functions_count', 0)
        results.technical_debt_score = raw_result.get('technical_debt_score', 0.0)
        results.maintainability_index = raw_result.get('maintainability_index', 100.0)
        results.complexity_warnings = raw_result.get('complexity_warnings', [])

        # Extract LOC metrics
        results.total_lines = raw_result.get('total_lines', 0)
        results.code_lines = raw_result.get('code_lines', 0)
        results.comment_ratio = raw_result.get('comment_ratio', 0.0)

        return results

    def parse_agent_zero_audit(self, raw_result: Dict, workflow_type: str = "code_audit") -> AuditResults:
        """
        Parse Agent Zero audit results based on workflow type

        Args:
            raw_result: Raw result dictionary from Agent Zero
            workflow_type: Type of workflow (code_audit, security_scan, complexity_analysis)

        Returns:
            Standardized AuditResults
        """
        if workflow_type == "code_audit":
            return self.parse_code_audit_results(raw_result)
        elif workflow_type == "security_scan":
            return self.parse_security_scan_results(raw_result)
        elif workflow_type == "complexity_analysis":
            return self.parse_complexity_analysis_results(raw_result)
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

    def aggregate_results(self, results_list: List[AuditResults]) -> Dict[str, Any]:
        """
        Aggregate multiple audit results into a comprehensive report

        Args:
            results_list: List of AuditResults from different workflows

        Returns:
            Aggregated results dictionary
        """
        aggregated = {
            "overall_score": 0.0,
            "code_quality": {},
            "security": {},
            "complexity": {},
            "bonus_score": 0.0,
            "recommendations": []
        }

        for result in results_list:
            if result.workflow == "code_audit":
                aggregated["code_quality"] = {
                    "score": result.code_quality_score,
                    "pylint_score": result.pylint_score,
                    "errors": result.pylint_errors + result.flake8_issues + result.eslint_errors,
                    "warnings": result.pylint_warnings + result.eslint_warnings
                }

            elif result.workflow == "security_scan":
                aggregated["security"] = {
                    "score": result.security_score,
                    "high_severity": result.high_severity_issues,
                    "medium_severity": result.medium_severity_issues,
                    "low_severity": result.low_severity_issues,
                    "secrets_found": result.secrets_found,
                    "vulnerable_deps": result.vulnerable_dependencies,
                    "critical_issues": result.security_issues[:5]  # Top 5
                }

            elif result.workflow == "complexity_analysis":
                aggregated["complexity"] = {
                    "score": result.complexity_score,
                    "avg_complexity": result.avg_cyclomatic_complexity,
                    "high_complexity_count": result.high_complexity_count,
                    "technical_debt": result.technical_debt_score,
                    "maintainability_index": result.maintainability_index,
                    "warnings": result.complexity_warnings[:5]  # Top 5
                }

        # Calculate overall score (weighted average)
        scores = []
        if aggregated["code_quality"]:
            scores.append(aggregated["code_quality"]["score"])
        if aggregated["security"]:
            scores.append(aggregated["security"]["score"])
        if aggregated["complexity"]:
            scores.append(aggregated["complexity"]["score"])

        if scores:
            aggregated["overall_score"] = sum(scores) / len(scores)

        # Calculate bonus score for main scanner
        # Bonus: +2 for excellent code quality, +3 for good security, +1 for low complexity
        bonus = 0.0
        if aggregated["code_quality"] and aggregated["code_quality"]["score"] >= 8.0:
            bonus += 2.0
        if aggregated["security"] and aggregated["security"]["score"] >= 8.0:
            bonus += 3.0
        if aggregated["complexity"] and aggregated["complexity"]["score"] >= 7.0:
            bonus += 1.0

        aggregated["bonus_score"] = bonus

        # Generate recommendations
        aggregated["recommendations"] = self._generate_recommendations(aggregated)

        return aggregated

    def _generate_recommendations(self, aggregated: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on audit results"""
        recommendations = []

        # Code quality recommendations
        if aggregated["code_quality"]:
            cq = aggregated["code_quality"]
            if cq["score"] < 5.0:
                recommendations.append("CRITICAL: Code quality is poor. Run linters and fix critical errors.")
            if cq["errors"] > 20:
                recommendations.append(f"Fix {cq['errors']} linting errors to improve code quality.")

        # Security recommendations
        if aggregated["security"]:
            sec = aggregated["security"]
            if sec["secrets_found"] > 0:
                recommendations.append(f"CRITICAL: {sec['secrets_found']} potential secrets found. Remove hardcoded credentials.")
            if sec["high_severity"] > 0:
                recommendations.append(f"Fix {sec['high_severity']} high-severity security issues immediately.")
            if sec["vulnerable_deps"] > 5:
                recommendations.append(f"Update {sec['vulnerable_deps']} vulnerable dependencies.")

        # Complexity recommendations
        if aggregated["complexity"]:
            comp = aggregated["complexity"]
            if comp["avg_complexity"] > 15:
                recommendations.append("Refactor high-complexity functions to improve maintainability.")
            if comp["technical_debt"] > 50:
                recommendations.append("Technical debt is high. Consider refactoring and adding tests.")

        if not recommendations:
            recommendations.append("Code quality is good. Continue maintaining standards.")

        return recommendations

    def run_local_simulation(self, project_path: Path, workflow_type: str = "code_audit") -> AuditResults:
        """
        Run a local simulation of the audit (without Agent Zero)
        Useful for testing workflow definitions

        Args:
            project_path: Path to project to audit
            workflow_type: Type of workflow to simulate

        Returns:
            Simulated AuditResults
        """
        # This is a placeholder for local testing
        # In production, this would call Agent Zero Bridge
        results = AuditResults(workflow=workflow_type, success=False)
        results.error_message = "Local simulation not implemented. Use Agent Zero Bridge for actual audits."

        return results

    def export_results(self, results: AuditResults, output_file: Path) -> None:
        """
        Export audit results to JSON file

        Args:
            results: AuditResults to export
            output_file: Path to output JSON file
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(asdict(results), f, indent=2)

    def import_results(self, input_file: Path) -> AuditResults:
        """
        Import audit results from JSON file

        Args:
            input_file: Path to input JSON file

        Returns:
            AuditResults object
        """
        with open(input_file, 'r') as f:
            data = json.load(f)

        return AuditResults(**data)


def calculate_bonus_score(audit_results: AuditResults) -> float:
    """
    Calculate bonus score for integration with main scanner

    Args:
        audit_results: Results from Agent Zero audit

    Returns:
        Bonus score (0-6 points)
    """
    bonus = 0.0

    # Code quality bonus (0-2 points)
    if audit_results.code_quality_score >= 9.0:
        bonus += 2.0
    elif audit_results.code_quality_score >= 7.0:
        bonus += 1.0

    # Security bonus (0-3 points)
    if audit_results.security_score >= 9.0 and audit_results.secrets_found == 0:
        bonus += 3.0
    elif audit_results.security_score >= 7.0:
        bonus += 1.5

    # Complexity bonus (0-1 point)
    if audit_results.complexity_score >= 8.0:
        bonus += 1.0

    return bonus


# Example usage
if __name__ == "__main__":
    import sys

    auditor = AgentZeroAuditor()

    print("Agent Zero Autonomous Code Auditor")
    print("=" * 60)
    print(f"Available workflows: {list(auditor.available_workflows.keys())}")
    print()

    # Example: Parse mock results
    mock_code_audit = {
        "pylint_score": 7.2,
        "pylint_errors": 5,
        "pylint_warnings": 15,
        "flake8_issues": 8,
        "eslint_errors": 3,
        "eslint_warnings": 12,
        "overall_score": 7.5
    }

    mock_security_scan = {
        "security_score": 6.5,
        "high_severity": 2,
        "medium_severity": 5,
        "low_severity": 10,
        "secrets_found": 1,
        "vulnerable_dependencies": 3,
        "security_issues": [
            {"severity": "CRITICAL", "file": "app.py", "issue": "Hardcoded API key"},
            {"severity": "HIGH", "file": "config.py", "issue": "SQL injection vulnerability"}
        ]
    }

    mock_complexity = {
        "complexity_score": 7.8,
        "avg_cyclomatic_complexity": 12.3,
        "high_complexity_count": 8,
        "long_functions_count": 5,
        "technical_debt_score": 35.2,
        "maintainability_index": 64.8,
        "total_lines": 5000,
        "code_lines": 3500,
        "comment_ratio": 0.15
    }

    # Parse results
    code_results = auditor.parse_agent_zero_audit(mock_code_audit, "code_audit")
    security_results = auditor.parse_agent_zero_audit(mock_security_scan, "security_scan")
    complexity_results = auditor.parse_agent_zero_audit(mock_complexity, "complexity_analysis")

    # Aggregate
    aggregated = auditor.aggregate_results([code_results, security_results, complexity_results])

    print("Aggregated Audit Results:")
    print(json.dumps(aggregated, indent=2))
    print()
    print(f"Bonus Score for Main Scanner: +{aggregated['bonus_score']:.1f} points")
    print()
    print("Recommendations:")
    for i, rec in enumerate(aggregated["recommendations"], 1):
        print(f"  {i}. {rec}")
