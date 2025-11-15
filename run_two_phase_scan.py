#!/usr/bin/env python3
"""
Two-Phase Deep Scan Runner - Borg Tools Scanner v2.0

Runs intelligent two-phase scanning with OpenRouter auto model:
1. Phase 1: Fast triage (all projects)
2. Phase 2: Deep analysis with premium models (top 40%)

Usage:
    python3 run_two_phase_scan.py --root ~/Projects
    python3 run_two_phase_scan.py --root ~/Projects --top-percent 30
    python3 run_two_phase_scan.py --root ~/Projects --limit 20

Created by The Collective Borg.tools
"""

import argparse
import sys
import os
import json
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from borg_tools_scan import (
    list_projects,
    scan_project,
    render_index_md,
    ProjectSummary
)
from modules.two_phase_scanner import TwoPhaseScanner
from modules.duplicate_detector import detect_and_mark_duplicates
from modules.premium_model_router import PremiumModelRouter, ModelUsageTracker
import dataclasses
import time


def scan_project_wrapper(project_path, deep_scan=False, use_llm=False, use_auto_model=True):
    """
    Wrapper for scan_project that handles different scan modes
    
    Args:
        project_path: Path to project
        deep_scan: Enable deep analysis
        use_llm: Enable LLM analysis
        use_auto_model: Use OpenRouter auto model
    
    Returns:
        ProjectSummary object
    """
    # Create args object for scan_project
    class Args:
        def __init__(self):
            self.deep_scan = deep_scan
            self.skip_llm = not use_llm
            self.use_agent_zero = False
            self.resume = True
            self.verbose = False
            self.use_llm = None  # Legacy flag
            self.model = None
    
    args = Args()
    
    # Run scan
    summary = scan_project(project_path, args=args, reporter=None, cache_manager=None)
    
    return summary


def main():
    parser = argparse.ArgumentParser(
        description='Borg Tools Two-Phase Deep Scanner with OpenRouter Auto Model'
    )
    
    # Basic options
    parser.add_argument(
        '--root',
        default='..',
        help='Root directory containing projects (default: parent directory)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=0,
        help='Limit number of projects to scan (0 = all)'
    )
    
    # Two-phase options
    parser.add_argument(
        '--top-percent',
        type=int,
        default=40,
        help='Percentage of top projects for deep scan (default: 40)'
    )
    parser.add_argument(
        '--duplicate-threshold',
        type=float,
        default=0.8,
        help='Similarity threshold for duplicates (0.0-1.0, default: 0.8)'
    )
    
    # Model options
    parser.add_argument(
        '--model-mode',
        choices=['auto', 'cloaked', 'premium', 'fast'],
        default='auto',
        help='Model selection mode (default: auto)'
    )
    parser.add_argument(
        '--prefer-paid',
        action='store_true',
        help='Prefer paid models over free (default: prefer free)'
    )
    
    # Output options
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--output-dir',
        default='.',
        help='Output directory for reports (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Validate environment
    if not os.getenv('OPENROUTER_API_KEY'):
        print("❌ ERROR: OPENROUTER_API_KEY environment variable not set")
        print("\nPlease set your OpenRouter API key:")
        print("  export OPENROUTER_API_KEY='your-key-here'")
        print("\nGet your key at: https://openrouter.ai/keys")
        sys.exit(1)
    
    # Resolve paths
    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        print(f"❌ ERROR: Root directory not found: {root}")
        sys.exit(1)
    
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Print configuration
    print("=" * 70)
    print("BORG TOOLS TWO-PHASE DEEP SCANNER")
    print("=" * 70)
    print(f"\n📁 Configuration:")
    print(f"  Root directory: {root}")
    print(f"  Output directory: {output_dir}")
    print(f"  Top percent for deep scan: {args.top_percent}%")
    print(f"  Duplicate threshold: {args.duplicate_threshold}")
    print(f"  Model mode: {args.model_mode}")
    print(f"  Prefer free models: {not args.prefer_paid}")
    print(f"  Verbose: {args.verbose}")
    
    # Discover projects
    print(f"\n🔍 Discovering projects...")
    all_projects = list_projects(root)
    
    if args.limit > 0:
        all_projects = all_projects[:args.limit]
    
    print(f"  Found {len(all_projects)} projects")
    
    if len(all_projects) == 0:
        print("❌ No projects found!")
        sys.exit(1)
    
    # Initialize scanner
    scanner = TwoPhaseScanner(
        top_percent=args.top_percent / 100.0,
        duplicate_threshold=args.duplicate_threshold,
        use_auto_model=(args.model_mode == 'auto'),
        prefer_free=(not args.prefer_paid),
        verbose=args.verbose
    )
    
    # Show model info
    model_info = scanner.router.get_model_info()
    print(f"\n🤖 Model Configuration:")
    print(f"  Mode: {model_info['mode']}")
    print(f"  Cloaked models available: {len(model_info['cloaked_models'])}")
    if args.verbose and model_info['cloaked_models']:
        for model in model_info['cloaked_models'][:3]:
            print(f"    - {model}")
    
    total_start = time.time()
    
    # ========== PHASE 1: FAST TRIAGE ==========
    print("\n" + "=" * 70)
    print("PHASE 1: FAST TRIAGE SCAN")
    print("=" * 70)
    print(f"Scanning {len(all_projects)} projects with fast heuristics...")
    
    phase1_start = time.time()
    phase1_summaries = []
    
    for i, project_path in enumerate(all_projects, 1):
        if args.verbose:
            print(f"\n[{i}/{len(all_projects)}] {project_path.name}")
        else:
            print(f"  [{i}/{len(all_projects)}] {project_path.name}", end='\r')
        
        try:
            summary = scan_project_wrapper(
                project_path,
                deep_scan=False,
                use_llm=False,
                use_auto_model=False
            )
            phase1_summaries.append(summary)
        except Exception as e:
            print(f"\n  ⚠️  Failed to scan {project_path.name}: {e}")
    
    phase1_elapsed = time.time() - phase1_start
    print(f"\n\n✅ Phase 1 complete in {phase1_elapsed:.1f}s")
    
    # ========== DUPLICATE DETECTION ==========
    print(f"\n🔍 Detecting duplicates...")
    
    summary_dicts = [
        {
            'facts': dataclasses.asdict(s.facts),
            'scores': dataclasses.asdict(s.scores),
            'suggestions': dataclasses.asdict(s.suggestions)
        }
        for s in phase1_summaries
    ]
    
    updated_dicts, duplicate_info = detect_and_mark_duplicates(
        summary_dicts,
        threshold=args.duplicate_threshold
    )
    
    # Update summaries with duplicate markers
    for i, summary in enumerate(phase1_summaries):
        dup_data = updated_dicts[i].get('suggestions', {})
        summary.suggestions.is_duplicate = dup_data.get('is_duplicate', False)
        summary.suggestions.duplicate_of = dup_data.get('duplicate_of')
        summary.suggestions.duplicate_group = dup_data.get('duplicate_group', [])
    
    print(f"  Found {duplicate_info['total_duplicates']} duplicate pairs")
    print(f"  Unique projects: {duplicate_info['unique_projects']}")
    
    # ========== SELECT TOP PROJECTS ==========
    print(f"\n📊 Selecting top {args.top_percent}% for deep analysis...")
    
    top_projects, remaining = scanner.select_top_projects(
        phase1_summaries,
        duplicate_info
    )
    
    print(f"  Selected {len(top_projects)} projects for deep scan")
    print(f"  Skipping {len(remaining)} lower-priority projects")
    
    # Show top 10
    print(f"\n🏆 Top 10 projects by priority:")
    scored = [(p, scanner.calculate_priority_score(p)) for p in phase1_summaries]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    for i, (proj, score) in enumerate(scored[:10], 1):
        stage_emoji = {
            'prod': '🚀', 'beta': '🔧', 'mvp': '🎯',
            'prototype': '🧪', 'idea': '💡', 'abandoned': '💀'
        }.get(proj.scores.stage, '📦')
        
        is_deep = proj in top_projects
        marker = "→ DEEP SCAN" if is_deep else ""
        
        print(f"  {i:2d}. {stage_emoji} {proj.facts.name:35s} "
              f"Score: {score:5.1f}  {marker}")
    
    # ========== PHASE 2: DEEP ANALYSIS ==========
    print("\n" + "=" * 70)
    print("PHASE 2: DEEP ANALYSIS WITH PREMIUM MODELS")
    print("=" * 70)
    print(f"Deep scanning {len(top_projects)} projects...")
    print(f"Using OpenRouter {args.model_mode} mode with premium model preferences")
    
    phase2_start = time.time()
    phase2_summaries = []
    
    for i, project_summary in enumerate(top_projects, 1):
        print(f"\n[{i}/{len(top_projects)}] 🔬 Deep scan: {project_summary.facts.name}")
        
        try:
            deep_summary = scan_project_wrapper(
                Path(project_summary.facts.path),
                deep_scan=True,
                use_llm=True,
                use_auto_model=True
            )
            phase2_summaries.append(deep_summary)
            
            # Track model usage
            if hasattr(deep_summary, 'llm_results'):
                scanner.usage_tracker.record_call({
                    'success': True,
                    'role': 'deep_scan',
                    'requested_model': 'openrouter/auto',
                    'actual_model': 'openrouter/auto'
                })
        
        except Exception as e:
            print(f"  ⚠️  Deep scan failed: {e}")
            phase2_summaries.append(project_summary)  # Use phase 1 summary
    
    phase2_elapsed = time.time() - phase2_start
    print(f"\n✅ Phase 2 complete in {phase2_elapsed:.1f}s")
    
    # ========== GENERATE OUTPUTS ==========
    total_elapsed = time.time() - total_start
    
    print("\n" + "=" * 70)
    print("GENERATING OUTPUTS")
    print("=" * 70)
    
    # Merge summaries (phase 2 replaces phase 1 for top projects)
    final_summaries = phase1_summaries.copy()
    for deep_summary in phase2_summaries:
        for i, summary in enumerate(final_summaries):
            if summary.facts.name == deep_summary.facts.name:
                final_summaries[i] = deep_summary
                break
    
    # Sort by priority
    final_summaries.sort(
        key=lambda x: (x.scores.priority, x.scores.value_score),
        reverse=True
    )
    
    # Generate BORG_INDEX.md
    index_path = output_dir / 'BORG_INDEX.md'
    index_content = render_index_md(final_summaries)
    index_path.write_text(index_content, encoding='utf-8')
    print(f"  ✅ {index_path}")
    
    # Generate CSV
    import csv
    csv_path = output_dir / 'borg_dashboard.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow([
            'name', 'path', 'stage', 'value', 'risk', 'priority',
            'last_commit', 'languages', 'is_duplicate', 'duplicate_of'
        ])
        for ps in final_summaries:
            w.writerow([
                ps.facts.name,
                ps.facts.path,
                ps.scores.stage,
                ps.scores.value_score,
                ps.scores.risk_score,
                ps.scores.priority,
                ps.facts.last_commit_dt or '',
                ','.join(ps.facts.languages),
                getattr(ps.suggestions, 'is_duplicate', False),
                getattr(ps.suggestions, 'duplicate_of', '')
            ])
    print(f"  ✅ {csv_path}")
    
    # Generate JSON
    json_path = output_dir / 'borg_dashboard.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump([{
            'facts': dataclasses.asdict(ps.facts),
            'scores': dataclasses.asdict(ps.scores),
            'suggestions': dataclasses.asdict(ps.suggestions),
        } for ps in final_summaries], f, ensure_ascii=False, indent=2)
    print(f"  ✅ {json_path}")
    
    # Generate scan report
    report = scanner.generate_scan_report(
        phase1_summaries,
        phase2_summaries,
        duplicate_info,
        total_elapsed
    )
    
    report_path = output_dir / 'two_phase_scan_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  ✅ {report_path}")
    
    # ========== FINAL SUMMARY ==========
    scanner.print_final_report(report)
    
    print(f"\n📁 All outputs saved to: {output_dir}")
    print(f"\n⏱️  Total time: {total_elapsed:.1f}s")
    print(f"   Phase 1 (triage): {phase1_elapsed:.1f}s")
    print(f"   Phase 2 (deep): {phase2_elapsed:.1f}s")
    print(f"\n✅ Scan complete!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
