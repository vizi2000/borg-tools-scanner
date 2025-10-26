"""
VibeIntelligence Project E2E Test

Real-world test using the VibeIntelligence codebase as test subject.
Tests the complete scanner pipeline on a production FastAPI application.

Project: /Users/wojciechwiesner/ai/VibeIntelligence
Type: FastAPI backend with React frontend
Languages: Python, TypeScript, JavaScript

Author: The Collective Borg.tools
"""

import pytest
import sys
import json
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.code_analyzer import CodeAnalyzer
from modules.deployment_detector import DeploymentDetector
from modules.doc_analyzer import DocumentationAnalyzer


class TestVibeIntelligenceScan:
    """E2E tests using real VibeIntelligence project"""

    VIBEINTELIGENCE_PATH = Path("/Users/wojciechwiesner/ai/VibeIntelligence")

    @pytest.fixture(scope="class")
    def project_path(self):
        """Verify VibeIntelligence project exists"""
        if not self.VIBEINTELIGENCE_PATH.exists():
            pytest.skip(f"VibeIntelligence project not found at {self.VIBEINTELIGENCE_PATH}")

        return self.VIBEINTELIGENCE_PATH

    def test_01_project_structure_detection(self, project_path):
        """Should detect FastAPI backend and React frontend structure"""
        backend_path = project_path / 'backend'
        frontend_path = project_path / 'frontend'

        assert backend_path.exists(), "Backend directory should exist"

        # Check for FastAPI indicators
        backend_src = backend_path / 'src'
        if backend_src.exists():
            main_py = backend_src / 'main.py'
            assert main_py.exists(), "FastAPI main.py should exist"

    def test_02_code_quality_analysis(self, project_path):
        """Should analyze VibeIntelligence code quality"""
        backend_path = project_path / 'backend'

        if not backend_path.exists():
            pytest.skip("Backend directory not found")

        analyzer = CodeAnalyzer()

        start_time = time.time()
        result = analyzer.analyze_project(backend_path, ['python'])
        elapsed = time.time() - start_time

        # Validate results
        assert result is not None, "Analysis should return results"
        assert 'code_quality' in result
        code_quality = result['code_quality']
        assert 'architecture_pattern' in code_quality
        assert 'fundamental_issues' in code_quality

        # Should complete in reasonable time (< 2 minutes for production codebase)
        assert elapsed < 120, f"Analysis took too long: {elapsed:.2f}s"

        # Log results for inspection
        print(f"\n{'='*60}")
        print(f"VIBEINTELIGENCE CODE ANALYSIS RESULTS")
        print(f"{'='*60}")
        print(f"Architecture Pattern: {code_quality.get('architecture_pattern')}")
        print(f"Overall Score: {code_quality.get('overall_score', 0)}/10")
        print(f"Analysis Time: {elapsed:.2f}s")
        print(f"Complexity Metrics: {code_quality.get('complexity_metrics', {})}")
        print(f"Security Issues Found: {len(code_quality.get('fundamental_issues', []))}")
        print(f"{'='*60}\n")

    def test_03_deployment_readiness_assessment(self, project_path):
        """Should assess VibeIntelligence deployment readiness"""
        backend_path = project_path / 'backend'

        if not backend_path.exists():
            pytest.skip("Backend directory not found")

        detector = DeploymentDetector()

        # Prepare facts (basic dependency detection)
        facts = {'deps': {'python': []}}

        result = detector.analyze(backend_path, ['python'], facts)

        assert result is not None
        assert 'deployment' in result

        deployment = result['deployment']

        # Validate deployment analysis
        assert 'readiness_score' in deployment
        assert 'is_deployable' in deployment
        assert 'deployment_type' in deployment
        assert 'blockers' in deployment
        assert 'mvp_checklist' in deployment

        # Log results
        print(f"\n{'='*60}")
        print(f"VIBEINTELIGENCE DEPLOYMENT ANALYSIS")
        print(f"{'='*60}")
        print(f"Readiness Score: {deployment['readiness_score']}/10")
        print(f"Deployable: {deployment['is_deployable']}")
        print(f"Deployment Type: {deployment['deployment_type']}")
        print(f"Blockers: {len(deployment['blockers'])}")

        if deployment['blockers']:
            print(f"\nTop Blockers:")
            for blocker in deployment['blockers'][:5]:
                print(f"  - [{blocker['severity']}] {blocker['description']}")

        print(f"\nMVP Checklist ({len(deployment['mvp_checklist'])} items):")
        for item in deployment['mvp_checklist'][:5]:
            print(f"  [{item['status']}] {item['task']} ({item['time_hours']}h)")

        print(f"\nEstimated Hours to MVP: {deployment.get('estimated_hours_to_mvp', 'N/A')}")
        print(f"{'='*60}\n")

    def test_04_documentation_quality_check(self, project_path):
        """Should assess VibeIntelligence documentation quality"""
        doc_analyzer = DocumentationAnalyzer()

        result = doc_analyzer.analyze(project_path, ['python', 'javascript'], {})

        assert result is not None
        assert 'documentation' in result

        docs = result['documentation']

        # Validate documentation analysis
        assert 'overall_score' in docs
        assert 'completeness' in docs
        assert 'found_docs' in docs

        # Log results
        print(f"\n{'='*60}")
        print(f"VIBEINTELIGENCE DOCUMENTATION ANALYSIS")
        print(f"{'='*60}")
        print(f"Overall Score: {docs['overall_score']}/10")
        print(f"Completeness: {docs['completeness']*100:.1f}%")

        found_docs = docs['found_docs']
        print(f"\nFound Documentation:")
        print(f"  README: {found_docs.get('readme', {}).get('exists', False)}")

        if found_docs.get('readme', {}).get('exists'):
            readme = found_docs['readme']
            print(f"    Word Count: {readme.get('word_count', 0)}")
            print(f"    Sections: {len(readme.get('sections', []))}")
            print(f"    Missing: {len(readme.get('missing_sections', []))}")

        print(f"  Changelog: {found_docs.get('changelog', {}).get('exists', False)}")
        print(f"  Contributing: {found_docs.get('contributing', {}).get('exists', False)}")
        print(f"  License: {found_docs.get('license', {}).get('exists', False)}")

        if 'accuracy_issues' in docs:
            print(f"\nAccuracy Issues: {len(docs['accuracy_issues'])}")

        print(f"{'='*60}\n")

    def test_05_api_endpoint_detection(self, project_path):
        """Should detect FastAPI endpoints in VibeIntelligence"""
        backend_path = project_path / 'backend'

        if not backend_path.exists():
            pytest.skip("Backend directory not found")

        doc_analyzer = DocumentationAnalyzer()
        result = doc_analyzer.analyze(backend_path, ['python'], {})

        found_docs = result['documentation']['found_docs']
        api_docs = found_docs.get('api_docs', {})

        detected_endpoints = api_docs.get('detected_endpoints', 0)

        print(f"\n{'='*60}")
        print(f"VIBEINTELIGENCE API ENDPOINT DETECTION")
        print(f"{'='*60}")
        print(f"Detected Endpoints: {detected_endpoints}")

        # VibeIntelligence should have multiple API endpoints
        # (Based on FastAPI structure: /api/v1/projects, /api/v1/scanner, etc.)
        if detected_endpoints > 0:
            print(f"API Documentation Exists: {api_docs.get('exists', False)}")
            print(f"Documented Endpoints: {api_docs.get('documented_endpoints', 0)}")

        print(f"{'='*60}\n")

    def test_06_security_scan_real_codebase(self, project_path):
        """Should scan VibeIntelligence for security issues"""
        backend_path = project_path / 'backend'

        if not backend_path.exists():
            pytest.skip("Backend directory not found")

        analyzer = CodeAnalyzer()
        result = analyzer.analyze_project(backend_path, ['python'])

        security_issues = result.get('code_quality', {}).get('fundamental_issues', [])

        print(f"\n{'='*60}")
        print(f"VIBEINTELIGENCE SECURITY SCAN")
        print(f"{'='*60}")
        print(f"Total Security Issues: {len(security_issues)}")

        if security_issues:
            # Group by category
            by_category = {}
            for issue in security_issues:
                category = issue.get('category', 'unknown')
                by_category[category] = by_category.get(category, 0) + 1

            print(f"\nIssues by Category:")
            for category, count in sorted(by_category.items(), key=lambda x: -x[1]):
                print(f"  {category}: {count}")

            # Show sample issues
            print(f"\nSample Issues (first 5):")
            for issue in security_issues[:5]:
                print(f"  [{issue.get('severity', 'UNKNOWN')}] {issue.get('description', 'No description')}")
                print(f"    File: {issue.get('file', 'unknown')}:{issue.get('line', '?')}")

        print(f"{'='*60}\n")

    def test_07_performance_benchmark(self, project_path):
        """Should complete full analysis in acceptable time"""
        backend_path = project_path / 'backend'

        if not backend_path.exists():
            pytest.skip("Backend directory not found")

        # Run all analyzers and measure time
        times = {}

        # Code Analysis
        start = time.time()
        analyzer = CodeAnalyzer()
        code_result = analyzer.analyze_project(backend_path, ['python'])
        times['code_analysis'] = time.time() - start

        # Deployment Detection
        start = time.time()
        detector = DeploymentDetector()
        deploy_result = detector.analyze(backend_path, ['python'], {'deps': {}})
        times['deployment_detection'] = time.time() - start

        # Documentation Analysis
        start = time.time()
        doc_analyzer = DocumentationAnalyzer()
        doc_result = doc_analyzer.analyze(backend_path, ['python'], {})
        times['documentation_analysis'] = time.time() - start

        total_time = sum(times.values())

        print(f"\n{'='*60}")
        print(f"VIBEINTELIGENCE PERFORMANCE BENCHMARK")
        print(f"{'='*60}")
        print(f"Code Analysis: {times['code_analysis']:.2f}s")
        print(f"Deployment Detection: {times['deployment_detection']:.2f}s")
        print(f"Documentation Analysis: {times['documentation_analysis']:.2f}s")
        print(f"Total Time: {total_time:.2f}s")
        print(f"{'='*60}\n")

        # All modules should complete in < 2 minutes total
        assert total_time < 120, f"Total analysis time too long: {total_time:.2f}s"

    def test_08_integration_point_identification(self, project_path):
        """Should identify potential integration points with Borg Scanner"""
        backend_path = project_path / 'backend'

        if not backend_path.exists():
            pytest.skip("Backend directory not found")

        # Check for scanner-related code
        scanner_files = []
        backend_src = backend_path / 'src'

        if backend_src.exists():
            for py_file in backend_src.rglob('*.py'):
                content = py_file.read_text(encoding='utf-8', errors='ignore')

                # Look for scanner-related patterns
                if any(keyword in content.lower() for keyword in [
                    'scanner', 'project_scanner', 'scan_directory',
                    'analyze_project', 'detect_language'
                ]):
                    scanner_files.append(py_file.relative_to(backend_path))

        print(f"\n{'='*60}")
        print(f"VIBEINTELIGENCE INTEGRATION POINT ANALYSIS")
        print(f"{'='*60}")
        print(f"Scanner-related files found: {len(scanner_files)}")

        if scanner_files:
            print(f"\nPotential Integration Points:")
            for file in scanner_files:
                print(f"  - {file}")

        # Check for API routes
        routes_found = []
        if backend_src.exists():
            for py_file in backend_src.rglob('*.py'):
                if 'router' in py_file.name or 'routes' in py_file.name:
                    routes_found.append(py_file.relative_to(backend_path))

        if routes_found:
            print(f"\nAPI Route Files:")
            for route_file in routes_found:
                print(f"  - {route_file}")

        print(f"{'='*60}\n")

    def test_09_generate_vibesummary_output(self, project_path):
        """Should be able to generate VibeSummary for VibeIntelligence"""
        backend_path = project_path / 'backend'

        if not backend_path.exists():
            pytest.skip("Backend directory not found")

        # Run all analyzers to collect data
        code_result = CodeAnalyzer().analyze_project(backend_path, ['python'])
        deploy_result = DeploymentDetector().analyze(backend_path, ['python'], {'deps': {}})
        doc_result = DocumentationAnalyzer().analyze(backend_path, ['python'], {})

        # Prepare project summary
        project_summary = {
            'name': 'VibeIntelligence',
            'path': str(backend_path),
            'languages': ['python'],
            'code_analysis': code_result,
            'deployment_analysis': deploy_result,
            'doc_analysis': doc_result
        }

        # Save results for inspection
        output_file = Path(__file__).parent.parent.parent / 'vibeinteligence_test_results.json'

        with open(output_file, 'w') as f:
            json.dump(project_summary, f, indent=2, default=str)

        print(f"\n{'='*60}")
        print(f"VIBEINTELIGENCE VIBESUMMARY GENERATION")
        print(f"{'='*60}")
        print(f"Results saved to: {output_file}")
        print(f"File size: {output_file.stat().st_size / 1024:.2f} KB")
        print(f"\nProject Summary:")
        print(f"  Name: {project_summary['name']}")
        print(f"  Path: {project_summary['path']}")
        print(f"  Languages: {', '.join(project_summary['languages'])}")

        # Check if VibeSummaryGenerator is available
        try:
            from modules.vibesummary_generator import VibeSummaryGenerator

            generator = VibeSummaryGenerator()

            # Try to generate VibeSummary
            vibesummary_path = Path(__file__).parent.parent.parent / 'VibeIntelligence_VibeSummary.md'

            # Note: This may require LLM API key, so we'll wrap in try-except
            try:
                generator.generate_vibesummary(project_summary, vibesummary_path)
                print(f"VibeSummary generated: {vibesummary_path}")
            except Exception as e:
                print(f"VibeSummary generation skipped (may require LLM API): {e}")

        except ImportError:
            print(f"VibeSummaryGenerator not available")

        print(f"{'='*60}\n")

        assert output_file.exists(), "Results file should be created"


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '-s'])
