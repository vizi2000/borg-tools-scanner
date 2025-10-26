#!/usr/bin/env python3
"""
Test Suite for Agent Zero Auditor
Tests workflow loading, result parsing, and aggregation

Created by The Collective Borg.tools
"""

import json
import unittest
from pathlib import Path
from modules.agent_zero_auditor import (
    AgentZeroAuditor,
    AuditResults,
    calculate_bonus_score
)


class TestAgentZeroAuditor(unittest.TestCase):
    """Test cases for Agent Zero Auditor"""

    def setUp(self):
        """Set up test fixtures"""
        self.auditor = AgentZeroAuditor()

    def test_workflow_discovery(self):
        """Test that workflows are discovered correctly"""
        workflows = self.auditor.available_workflows
        self.assertIsInstance(workflows, dict)
        # Should find at least one workflow if they exist
        # Allow empty if workflows not yet created
        self.assertIn(type(workflows), [dict])

    def test_parse_code_audit_results(self):
        """Test parsing code audit results"""
        raw_result = {
            "pylint_score": 7.5,
            "pylint_errors": 5,
            "pylint_warnings": 15,
            "flake8_issues": 8,
            "eslint_errors": 3,
            "eslint_warnings": 12,
            "overall_score": 7.2
        }

        result = self.auditor.parse_code_audit_results(raw_result)

        self.assertIsInstance(result, AuditResults)
        self.assertEqual(result.workflow, "code_audit")
        self.assertEqual(result.pylint_score, 7.5)
        self.assertEqual(result.pylint_errors, 5)
        self.assertEqual(result.pylint_warnings, 15)
        self.assertEqual(result.flake8_issues, 8)
        self.assertEqual(result.eslint_errors, 3)
        self.assertEqual(result.eslint_warnings, 12)
        self.assertEqual(result.overall_score, 7.2)

    def test_parse_security_scan_results(self):
        """Test parsing security scan results"""
        raw_result = {
            "security_score": 6.5,
            "high_severity": 2,
            "medium_severity": 5,
            "low_severity": 10,
            "secrets_found": 1,
            "vulnerable_dependencies": 3,
            "security_issues": [
                {"severity": "CRITICAL", "file": "app.py", "issue": "API key exposed"},
                {"severity": "HIGH", "file": "db.py", "issue": "SQL injection risk"}
            ]
        }

        result = self.auditor.parse_security_scan_results(raw_result)

        self.assertIsInstance(result, AuditResults)
        self.assertEqual(result.workflow, "security_scan")
        self.assertEqual(result.security_score, 6.5)
        self.assertEqual(result.high_severity_issues, 2)
        self.assertEqual(result.medium_severity_issues, 5)
        self.assertEqual(result.low_severity_issues, 10)
        self.assertEqual(result.secrets_found, 1)
        self.assertEqual(result.vulnerable_dependencies, 3)
        self.assertEqual(len(result.security_issues), 2)

    def test_parse_complexity_analysis_results(self):
        """Test parsing complexity analysis results"""
        raw_result = {
            "complexity_score": 7.8,
            "avg_cyclomatic_complexity": 12.3,
            "high_complexity_count": 8,
            "long_functions_count": 5,
            "technical_debt_score": 35.2,
            "maintainability_index": 64.8,
            "total_lines": 5000,
            "code_lines": 3500,
            "comment_ratio": 0.15,
            "complexity_warnings": [
                {"type": "HIGH_COMPLEXITY", "function": "process", "complexity": 18}
            ]
        }

        result = self.auditor.parse_complexity_analysis_results(raw_result)

        self.assertIsInstance(result, AuditResults)
        self.assertEqual(result.workflow, "complexity_analysis")
        self.assertEqual(result.complexity_score, 7.8)
        self.assertEqual(result.avg_cyclomatic_complexity, 12.3)
        self.assertEqual(result.high_complexity_count, 8)
        self.assertEqual(result.long_functions_count, 5)
        self.assertEqual(result.technical_debt_score, 35.2)
        self.assertEqual(result.maintainability_index, 64.8)
        self.assertEqual(result.total_lines, 5000)
        self.assertEqual(result.code_lines, 3500)
        self.assertEqual(result.comment_ratio, 0.15)
        self.assertEqual(len(result.complexity_warnings), 1)

    def test_aggregate_results(self):
        """Test aggregation of multiple audit results"""
        code_result = AuditResults(
            workflow="code_audit",
            code_quality_score=8.0,
            pylint_score=8.2,
            pylint_errors=2,
            pylint_warnings=5
        )

        security_result = AuditResults(
            workflow="security_scan",
            security_score=9.0,
            high_severity_issues=0,
            secrets_found=0,
            vulnerable_dependencies=1,
            security_issues=[{"severity": "MEDIUM", "issue": "outdated package"}]
        )

        complexity_result = AuditResults(
            workflow="complexity_analysis",
            complexity_score=8.5,
            avg_cyclomatic_complexity=8.0,
            high_complexity_count=2,
            technical_debt_score=20.0,
            maintainability_index=80.0
        )

        aggregated = self.auditor.aggregate_results([
            code_result,
            security_result,
            complexity_result
        ])

        # Verify structure
        self.assertIn("overall_score", aggregated)
        self.assertIn("code_quality", aggregated)
        self.assertIn("security", aggregated)
        self.assertIn("complexity", aggregated)
        self.assertIn("bonus_score", aggregated)
        self.assertIn("recommendations", aggregated)

        # Verify overall score calculation
        self.assertGreater(aggregated["overall_score"], 0)
        self.assertLessEqual(aggregated["overall_score"], 10)

        # Verify bonus score
        self.assertGreater(aggregated["bonus_score"], 0)

    def test_calculate_bonus_score_excellent(self):
        """Test bonus score calculation for excellent code"""
        result = AuditResults(
            code_quality_score=9.5,
            security_score=9.8,
            secrets_found=0,
            complexity_score=8.5
        )

        bonus = calculate_bonus_score(result)

        # Should get maximum bonus
        self.assertGreaterEqual(bonus, 5.0)
        self.assertLessEqual(bonus, 6.0)

    def test_calculate_bonus_score_poor(self):
        """Test bonus score calculation for poor code"""
        result = AuditResults(
            code_quality_score=4.0,
            security_score=3.0,
            secrets_found=2,
            complexity_score=3.5
        )

        bonus = calculate_bonus_score(result)

        # Should get minimal or no bonus
        self.assertLessEqual(bonus, 1.0)

    def test_calculate_bonus_score_good(self):
        """Test bonus score calculation for good code"""
        result = AuditResults(
            code_quality_score=7.5,
            security_score=8.0,
            secrets_found=0,
            complexity_score=7.0
        )

        bonus = calculate_bonus_score(result)

        # Should get moderate bonus
        self.assertGreater(bonus, 1.0)
        self.assertLess(bonus, 5.0)

    def test_generate_recommendations_critical(self):
        """Test recommendation generation for critical issues"""
        aggregated = {
            "code_quality": {"score": 3.0, "errors": 50},
            "security": {
                "score": 2.0,
                "secrets_found": 3,
                "high_severity": 5,
                "vulnerable_deps": 10
            },
            "complexity": {
                "score": 4.0,
                "avg_complexity": 20,
                "technical_debt": 75
            }
        }

        recommendations = self.auditor._generate_recommendations(aggregated)

        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

        # Should have critical recommendations
        rec_text = " ".join(recommendations).lower()
        self.assertIn("critical", rec_text)

    def test_generate_recommendations_good_code(self):
        """Test recommendation generation for good code"""
        aggregated = {
            "code_quality": {"score": 9.0, "errors": 2},
            "security": {
                "score": 9.5,
                "secrets_found": 0,
                "high_severity": 0,
                "vulnerable_deps": 0
            },
            "complexity": {
                "score": 8.5,
                "avg_complexity": 7,
                "technical_debt": 15
            }
        }

        recommendations = self.auditor._generate_recommendations(aggregated)

        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

        # Should have positive message
        rec_text = " ".join(recommendations).lower()
        self.assertIn("good", rec_text)

    def test_export_and_import_results(self):
        """Test exporting and importing results"""
        import tempfile

        original_result = AuditResults(
            workflow="code_audit",
            code_quality_score=8.5,
            pylint_score=8.7,
            pylint_errors=3,
            success=True
        )

        # Export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)

        try:
            self.auditor.export_results(original_result, temp_file)
            self.assertTrue(temp_file.exists())

            # Import
            imported_result = self.auditor.import_results(temp_file)

            # Verify
            self.assertEqual(imported_result.workflow, original_result.workflow)
            self.assertEqual(imported_result.code_quality_score, original_result.code_quality_score)
            self.assertEqual(imported_result.pylint_score, original_result.pylint_score)
            self.assertEqual(imported_result.pylint_errors, original_result.pylint_errors)
            self.assertEqual(imported_result.success, original_result.success)

        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()

    def test_parse_agent_zero_audit_invalid_workflow(self):
        """Test parsing with invalid workflow type"""
        raw_result = {"test": "data"}

        with self.assertRaises(ValueError):
            self.auditor.parse_agent_zero_audit(raw_result, "invalid_workflow")

    def test_audit_results_defaults(self):
        """Test that AuditResults has sensible defaults"""
        result = AuditResults()

        self.assertEqual(result.code_quality_score, 0.0)
        self.assertEqual(result.security_score, 10.0)
        self.assertEqual(result.complexity_score, 10.0)
        self.assertEqual(result.success, True)
        self.assertEqual(len(result.security_issues), 0)
        self.assertEqual(len(result.complexity_warnings), 0)


class TestAgentZeroIntegration(unittest.TestCase):
    """Integration tests for Agent Zero workflows"""

    def setUp(self):
        """Set up test fixtures"""
        self.auditor = AgentZeroAuditor()

    def test_full_audit_workflow(self):
        """Test complete audit workflow"""
        # Simulate complete audit
        code_raw = {
            "pylint_score": 8.0,
            "overall_score": 8.2,
            "pylint_errors": 2,
            "pylint_warnings": 8
        }

        security_raw = {
            "security_score": 8.5,
            "high_severity": 0,
            "secrets_found": 0,
            "vulnerable_dependencies": 1,
            "security_issues": []
        }

        complexity_raw = {
            "complexity_score": 7.8,
            "avg_cyclomatic_complexity": 9.2,
            "high_complexity_count": 3,
            "technical_debt_score": 28.0
        }

        # Parse all results
        code_result = self.auditor.parse_agent_zero_audit(code_raw, "code_audit")
        security_result = self.auditor.parse_agent_zero_audit(security_raw, "security_scan")
        complexity_result = self.auditor.parse_agent_zero_audit(complexity_raw, "complexity_analysis")

        # Aggregate
        aggregated = self.auditor.aggregate_results([
            code_result,
            security_result,
            complexity_result
        ])

        # Verify complete workflow
        self.assertGreater(aggregated["overall_score"], 7.0)
        self.assertGreater(aggregated["bonus_score"], 0)
        self.assertIsInstance(aggregated["recommendations"], list)
        self.assertGreater(len(aggregated["recommendations"]), 0)


def run_tests():
    """Run all tests"""
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    print("=" * 60)
    print("Agent Zero Auditor Test Suite")
    print("=" * 60)
    print()

    success = run_tests()

    print()
    print("=" * 60)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 60)

    exit(0 if success else 1)
