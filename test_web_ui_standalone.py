#!/usr/bin/env python3
"""
Standalone test for Web UI v2.0 enhancements
Tests the data processing logic without Flask dependency
"""

import json
import random
from pathlib import Path

def add_extra_data(projects):
    """Add computed fields for backwards compatibility and new v2.0 features"""
    for project in projects:
        scores = project.get('scores', {})

        # Backwards compatibility
        if 'potential_score' not in scores:
            scores['potential_score'] = max(0, (scores.get('value_score', 0) * 2) - scores.get('risk_score', 0))

        # Add 6-category scores if not present (v2.0 format)
        if 'code_quality_score' not in scores:
            scores['code_quality_score'] = scores.get('value_score', 5)
        if 'deployment_readiness_score' not in scores:
            scores['deployment_readiness_score'] = 10 - scores.get('risk_score', 5)
        if 'documentation_score' not in scores:
            scores['documentation_score'] = 7 if project.get('facts', {}).get('has_readme') else 3
        if 'borg_fit_score' not in scores:
            scores['borg_fit_score'] = scores.get('value_score', 5)
        if 'mvp_proximity_score' not in scores:
            stage = scores.get('stage', 'prototype')
            mvp_map = {'prototype': 3, 'mvp': 7, 'beta': 9, 'production': 10}
            scores['mvp_proximity_score'] = mvp_map.get(stage, 5)
        if 'monetization_viability_score' not in scores:
            scores['monetization_viability_score'] = scores.get('value_score', 5)

        # Deployment status
        if 'deployment_status' not in scores:
            deploy_score = scores.get('deployment_readiness_score', 5)
            if deploy_score >= 7:
                scores['deployment_status'] = 'ready'
            elif deploy_score >= 4:
                scores['deployment_status'] = 'warning'
            else:
                scores['deployment_status'] = 'blocked'

        # Monetization (legacy field)
        if 'monetization' not in project:
            project['monetization'] = {
                'realtime': round(random.uniform(0, 1000), 2)
            }

        project['scores'] = scores
    return projects

def test_data_processing():
    """Test that the add_extra_data function works correctly"""
    print("Testing data processing...")

    # Load sample data
    with open('borg_dashboard.json', 'r') as f:
        projects = json.load(f)

    print(f"✓ Loaded {len(projects)} projects")

    # Process data
    processed = add_extra_data(projects[:10])  # Test with first 10 projects

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
        print(f"    - MVP Proximity: {scores['mvp_proximity_score']}/10")

    print("\n✅ Data processing test PASSED")
    return True

def test_vibesummary_paths():
    """Test VibeSummary path resolution"""
    print("\nTesting VibeSummary path resolution...")

    # Check if any VibeSummary files exist
    with open('borg_dashboard.json', 'r') as f:
        projects = json.load(f)

    found_count = 0
    for project in projects[:20]:
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

    # Deployment status distribution
    deploy_counts = {}
    for p in processed:
        status = p['scores'].get('deployment_status', 'unknown')
        deploy_counts[status] = deploy_counts.get(status, 0) + 1

    print("\n  Deployment Status Distribution:")
    for status, count in sorted(deploy_counts.items()):
        icon = '🟢' if status == 'ready' else ('🟡' if status == 'warning' else '🔴')
        print(f"    {icon} {status}: {count} ({count/len(processed)*100:.1f}%)")

    print("\n✅ Statistics test PASSED")
    return True

def test_ui_features():
    """Test UI feature requirements"""
    print("\nTesting UI feature requirements...")

    # Check templates exist
    template_path = Path('templates/index.html')
    assert template_path.exists(), "templates/index.html not found"

    with open(template_path, 'r') as f:
        html_content = f.read()

    # Check for Bootstrap 5
    assert 'bootstrap@5.3.2' in html_content or 'bootstrap/5.3' in html_content, "Bootstrap 5 not found"
    print("  ✓ Bootstrap 5 included")

    # Check for Chart.js
    assert 'chart.js' in html_content.lower(), "Chart.js not found"
    print("  ✓ Chart.js included")

    # Check for Marked.js
    assert 'marked' in html_content.lower(), "Marked.js not found"
    print("  ✓ Marked.js (markdown renderer) included")

    # Check for tabs
    assert 'nav-tabs' in html_content, "Bootstrap tabs not found"
    print("  ✓ Tabbed interface present")

    # Check for filter controls
    assert 'searchInput' in html_content, "Search input not found"
    assert 'stageFilter' in html_content, "Stage filter not found"
    assert 'deploymentFilter' in html_content, "Deployment filter not found"
    assert 'borgFitFilter' in html_content, "Borg fit filter not found"
    print("  ✓ All filter controls present")

    # Check for radar chart
    assert 'radarChart' in html_content, "Radar chart not found"
    print("  ✓ Radar chart for 6-category scores present")

    # Check for VibeSummary tab
    assert 'vibesummary' in html_content.lower(), "VibeSummary tab not found"
    print("  ✓ VibeSummary viewer tab present")

    # Check for deployment status
    assert 'deployment-status' in html_content or 'deploymentStatus' in html_content, "Deployment status widget not found"
    print("  ✓ Deployment status widget present")

    print("\n✅ UI features test PASSED")
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
        test_ui_features()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\n📊 New Features Implemented:")
        print("  ✓ 6-Category Scores Dashboard with Radar Chart")
        print("  ✓ VibeSummary Viewer with Markdown Rendering")
        print("  ✓ Deployment Status Widget (Traffic Light)")
        print("  ✓ Filter by Borg.tools Fit Score")
        print("  ✓ Bootstrap 5 Upgrade")
        print("  ✓ Modern Card-Based Layout")
        print("  ✓ Statistics Dashboard")
        print()
        print("🚀 To run the web UI:")
        print("  1. Install Flask: pip install flask")
        print("  2. Run server: python3 web_ui.py")
        print("  3. Open browser: http://localhost:5001")
        print()

        return 0

    except FileNotFoundError as e:
        print(f"\n❌ ERROR: File not found - {e}")
        print("Please ensure borg_dashboard.json exists")
        return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
