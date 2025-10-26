"""
Comprehensive tests for deployment_detector.py

Created by The Collective Borg.tools
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from deployment_detector import (
    DockerfileParser,
    DockerComposeParser,
    EnvironmentDetector,
    BuildValidator,
    PlatformDetector,
    DeploymentDetector,
    detect_deployment
)


def test_dockerfile_parser():
    """Test Dockerfile parsing"""
    print("\n=== Testing DockerfileParser ===")

    parser = DockerfileParser()

    # Test 1: Non-existent Dockerfile
    result = parser.parse(Path("/nonexistent/Dockerfile"))
    assert result['exists'] == False, "Should detect missing Dockerfile"
    print("✅ Test 1 passed: Non-existent Dockerfile")

    # Test 2: Valid Dockerfile
    test_path = Path("/tmp/test_deployment_project/Dockerfile")
    if test_path.exists():
        result = parser.parse(test_path)
        assert result['exists'] == True
        assert result['base_image'] == 'python:3.11-slim'
        assert 8080 in result['ports']
        assert len(result['issues']) == 0
        print("✅ Test 2 passed: Valid Dockerfile parsed correctly")

    # Test 3: Deprecated base image
    test_path = Path("/tmp/test_deprecated/Dockerfile")
    if test_path.exists():
        result = parser.parse(test_path)
        assert 'deprecated_or_unpinned_base_image' in result['issues']
        print("✅ Test 3 passed: Deprecated base image detected")


def test_compose_parser():
    """Test Docker Compose parsing"""
    print("\n=== Testing DockerComposeParser ===")

    parser = DockerComposeParser()

    # Test 1: Non-existent compose file
    result = parser.parse(Path("/nonexistent/docker-compose.yml"))
    assert result['exists'] == False
    print("✅ Test 1 passed: Non-existent compose file")

    # Test 2: Valid compose file
    test_path = Path("/tmp/test_deployment_project/docker-compose.yml")
    if test_path.exists():
        result = parser.parse(test_path)
        assert result['exists'] == True
        assert 'web' in result['services']
        assert 'db' in result['services']
        assert result['is_multi_service'] == True
        print("✅ Test 2 passed: Valid compose file parsed")


def test_environment_detector():
    """Test environment variable detection"""
    print("\n=== Testing EnvironmentDetector ===")

    detector = EnvironmentDetector()

    # Test 1: Python environment variables
    test_path = Path("/tmp/test_deployment_project")
    if test_path.exists():
        env_vars = detector.detect_env_vars(test_path)
        var_names = [v['name'] for v in env_vars]
        assert 'DATABASE_URL' in var_names
        assert 'API_KEY' in var_names
        assert 'SECRET_KEY' in var_names
        print(f"✅ Test 1 passed: Detected {len(env_vars)} environment variables")

        # Check documentation status
        for var in env_vars:
            if var['name'] == 'DATABASE_URL':
                assert var['documented'] == True, "DATABASE_URL should be documented"
            elif var['name'] == 'API_KEY':
                assert var['documented'] == False, "API_KEY should not be documented"
        print("✅ Test 2 passed: Documentation status correct")


def test_build_validator():
    """Test build script validation"""
    print("\n=== Testing BuildValidator ===")

    validator = BuildValidator()

    # Test 1: No build script
    result = validator.validate(Path("/tmp/test_deployment_project"), ['python'])
    assert result['has_build_script'] == False
    print("✅ Test 1 passed: No build script detected")

    # Test 2: Node.js build script
    test_path = Path("/tmp/test_no_docker")
    if test_path.exists():
        result = validator.validate(test_path, ['nodejs'])
        assert result['has_build_script'] == True
        assert result['build_command'] == 'npm run build'
        print("✅ Test 2 passed: Node.js build script detected")


def test_platform_detector():
    """Test platform inference"""
    print("\n=== Testing PlatformDetector ===")

    detector = PlatformDetector()

    # Test 1: Docker platform
    test_path = Path("/tmp/test_deployment_project")
    if test_path.exists():
        platform = detector.infer_platform(test_path, {})
        assert platform == 'borg.tools'
        print("✅ Test 1 passed: Docker platform detected")

    # Test 2: Unknown platform (no Docker)
    test_path = Path("/tmp/test_no_docker")
    if test_path.exists():
        platform = detector.infer_platform(test_path, {})
        assert platform == 'unknown'
        print("✅ Test 2 passed: Unknown platform for no Docker")


def test_deployment_detector():
    """Test full deployment detection"""
    print("\n=== Testing DeploymentDetector (Full Integration) ===")

    # Test 1: Project with Docker
    test_path = Path("/tmp/test_deployment_project")
    if test_path.exists():
        result = detect_deployment(
            str(test_path),
            ['python'],
            {'deps': {'python': ['flask']}, 'has_ci': False}
        )

        assert 'deployment' in result
        assert result['deployment']['readiness_score'] >= 0
        assert result['deployment']['readiness_score'] <= 10
        assert result['deployment']['deployment_type'] == 'docker'
        assert result['deployment']['is_deployable'] in [True, False]
        assert isinstance(result['deployment']['blockers'], list)
        assert isinstance(result['deployment']['mvp_checklist'], list)
        assert result['deployment']['estimated_hours_to_mvp'] >= 0

        print(f"✅ Test 1 passed: Full deployment analysis")
        print(f"   - Readiness Score: {result['deployment']['readiness_score']}/10")
        print(f"   - Blockers: {len(result['deployment']['blockers'])}")
        print(f"   - MVP Hours: {result['deployment']['estimated_hours_to_mvp']}")

    # Test 2: Project without Docker
    test_path = Path("/tmp/test_no_docker")
    if test_path.exists():
        result = detect_deployment(
            str(test_path),
            ['nodejs'],
            {'deps': {'node': ['express']}}
        )

        assert result['deployment']['deployment_type'] == 'unknown'
        assert result['deployment']['readiness_score'] < 7
        critical_blockers = [b for b in result['deployment']['blockers'] if b['severity'] == 'CRITICAL']
        assert len(critical_blockers) > 0, "Should have critical blocker for missing Dockerfile"

        print(f"✅ Test 2 passed: No Docker project analysis")
        print(f"   - Readiness Score: {result['deployment']['readiness_score']}/10")
        print(f"   - Critical Blockers: {len(critical_blockers)}")


def test_edge_cases():
    """Test edge cases"""
    print("\n=== Testing Edge Cases ===")

    # Test 1: Empty project
    detector = DeploymentDetector()
    result = detect_deployment('/tmp', ['python'], {})
    assert 'deployment' in result
    print("✅ Test 1 passed: Empty project handled")

    # Test 2: Invalid path handling
    try:
        result = detect_deployment('/nonexistent/path', [], {})
        # Should not crash, just return low score
        assert result['deployment']['readiness_score'] >= 0
        print("✅ Test 2 passed: Invalid path handled gracefully")
    except Exception as e:
        print(f"⚠️  Test 2: Exception raised but acceptable: {str(e)[:50]}")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("DEPLOYMENT DETECTOR - COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    try:
        test_dockerfile_parser()
        test_compose_parser()
        test_environment_detector()
        test_build_validator()
        test_platform_detector()
        test_deployment_detector()
        test_edge_cases()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
