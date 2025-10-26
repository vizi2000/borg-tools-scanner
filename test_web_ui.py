#!/usr/bin/env python3
"""
Test script for Web UI v2.0 enhancements
Validates all new features without running the server
"""

import json
import sys
from pathlib import Path

def test_data_processing():
    """Test that the add_extra_data function works correctly"""
    print("Testing data processing...")

    # Load sample data
    with open('borg_dashboard.json', 'r') as f:
        projects = json.load(f)

    print(f"✓ Loaded {len(projects)} projects")

    # Import the function from web_ui
    sys.path.insert(0, str(Path.cwd()))
    from web_ui import add_extra_data

    # Process data
    processed = add_extra_data(projects[:5])  # Test with first 5 projects

    # Validate new fields
    for project in processed:
        scores = project['scores']

        # Check all 6-category scores exist
        assert 'code_quality_score' in scores, "Missing code_quality_score"
        assert 'deployment_readiness_score' in scores, "Missing deployment_readiness_score"
        assert 'documentation_score' in scores, "Missing documentation_score"
        assert 'borg_fit_score' in scores, "Missing borg_fit_score"
        assert 'mvp_proximity_score' in scores, "Missing mvp_proximity_score"
        assert 'monetization_viability_score' in scores, "Missing monetization_viability_score"

        # Check deployment status
        assert 'deployment_status' in scores, "Missing deployment_status"
        assert scores['deployment_status'] in ['ready', 'warning', 'blocked'], \
            f"Invalid deployment status: {scores['deployment_status']}"

        # Check legacy fields
        assert 'potential_score' in scores, "Missing potential_score"
        assert 'monetization' in project, "Missing monetization"

        print(f"  ✓ {project['facts']['name']}: All fields present")
        print(f"    - Code Quality: {scores['code_quality_score']}/10")
        print(f"    - Deployment: {scores['deployment_readiness_score']}/10 ({scores['deployment_status']})")
        print(f"    - Borg Fit: {scores['borg_fit_score']}/10")

    print("\n✅ Data processing test PASSED")
    return True

def test_vibesummary_paths():
    """Test VibeSummary path resolution"""
    print("\nTesting VibeSummary path resolution...")

    # Check if any VibeSummary files exist
    with open('borg_dashboard.json', 'r') as f:
        projects = json.load(f)

    found_count = 0
    for project in projects[:10]:
        project_path = Path(project['facts']['path'])
        vibesummary_paths = [
            project_path / 'VibeSummary.md',
            project_path / 'docs' / 'VibeSummary.md',
            project_path / 'specs' / 'VibeSummary.md',
        ]

        for vibe_path in vibesummary_paths:
            if vibe_path.exists():
                print(f"  ✓ Found VibeSummary: {vibe_path}")
                found_count += 1
                break

    if found_count == 0:
        print("  ℹ No VibeSummary files found (expected - will show default message)")
    else:
        print(f"  ✓ Found {found_count} VibeSummary files")

    print("\n✅ VibeSummary path test PASSED")
    return True

def test_score_statistics():
    """Test statistical calculations"""
    print("\nTesting score statistics...")

    with open('borg_dashboard.json', 'r') as f:
        projects = json.load(f)

    sys.path.insert(0, str(Path.cwd()))
    from web_ui import add_extra_data

    processed = add_extra_data(projects)

    # Calculate stats
    ready_count = sum(1 for p in processed if p['scores'].get('deployment_status') == 'ready')
    borg_fit_count = sum(1 for p in processed if p['scores'].get('borg_fit_score', 0) >= 7)
    avg_code_quality = sum(p['scores'].get('code_quality_score', 0) for p in processed) / len(processed)

    print(f"  Total Projects: {len(processed)}")
    print(f"  Ready to Deploy: {ready_count} ({ready_count/len(processed)*100:.1f}%)")
    print(f"  Borg.tools Fit (≥7): {borg_fit_count} ({borg_fit_count/len(processed)*100:.1f}%)")
    print(f"  Avg Code Quality: {avg_code_quality:.1f}/10")

    # Stage distribution
    stage_counts = {}
    for p in processed:
        stage = p['scores'].get('stage', 'unknown')
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    print("\n  Stage Distribution:")
    for stage, count in sorted(stage_counts.items()):
        print(f"    - {stage}: {count} ({count/len(processed)*100:.1f}%)")

    print("\n✅ Statistics test PASSED")
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("Web UI v2.0 Enhancement Tests")
    print("=" * 60)
    print()

    try:
        test_data_processing()
        test_vibesummary_paths()
        test_score_statistics()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nTo run the web UI:")
        print("  1. Install Flask: pip install flask")
        print("  2. Run server: python3 web_ui.py")
        print("  3. Open browser: http://localhost:5001")
        print()

        return 0

    except FileNotFoundError:
        print("\n❌ ERROR: borg_dashboard.json not found")
        print("Please run the scanner first to generate data")
        return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
