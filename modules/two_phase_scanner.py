"""
Two-Phase Scanner - Borg Tools Scanner v2.0

Orchestrates intelligent two-phase scanning:
1. Phase 1: Fast triage scan (all projects)
2. Phase 2: Deep analysis (top 40%)

Created by The Collective Borg.tools
"""

import asyncio
import time
from typing import List, Dict, Any, Tuple
from pathlib import Path
import dataclasses

from modules.duplicate_detector import detect_and_mark_duplicates
from modules.premium_model_router import PremiumModelRouter, ModelUsageTracker


class TwoPhaseScanner:
    """Orchestrates two-phase scanning strategy"""

    def __init__(
        self,
        top_percent: float = 0.4,
        duplicate_threshold: float = 0.8,
        use_auto_model: bool = True,
        prefer_free: bool = True,
        verbose: bool = False
    ):
        """
        Initialize two-phase scanner

        Args:
            top_percent: Percentage of projects to deep scan (0.0-1.0)
            duplicate_threshold: Similarity threshold for duplicates
            use_auto_model: Use OpenRouter auto model
            prefer_free: Prefer free models
            verbose: Enable verbose logging
        """
        self.top_percent = top_percent
        self.duplicate_threshold = duplicate_threshold
        self.use_auto_model = use_auto_model
        self.prefer_free = prefer_free
        self.verbose = verbose
        
        # Initialize model router
        mode = "auto" if use_auto_model else "fast"
        self.router = PremiumModelRouter(mode=mode, prefer_free=prefer_free)
        self.usage_tracker = ModelUsageTracker()

    def calculate_priority_score(self, project_summary: Any) -> float:
        """
        Calculate priority score for ranking projects

        Args:
            project_summary: ProjectSummary object

        Returns:
            Priority score (higher = more important)
        """
        facts = project_summary.facts
        scores = project_summary.scores

        # Base score from existing priority
        base_score = scores.priority

        # Recency bonus (0-2 points)
        recency_bonus = 0
        if facts.last_commit_dt:
            try:
                from datetime import datetime, timedelta
                last_commit = datetime.fromisoformat(facts.last_commit_dt)
                days_ago = (datetime.now() - last_commit).days
                
                if days_ago <= 14:
                    recency_bonus = 2
                elif days_ago <= 30:
                    recency_bonus = 1
            except:
                pass

        # Completeness bonus (0-3 points)
        completeness_bonus = 0
        if facts.has_readme:
            completeness_bonus += 1
        if facts.has_tests:
            completeness_bonus += 1
        if facts.has_ci:
            completeness_bonus += 1

        # Language diversity bonus (0-1 point)
        lang_bonus = min(1, len(facts.languages) * 0.3)

        # Weighted formula
        priority_score = (
            scores.value_score * 1.5 +      # Value is most important
            (10 - scores.risk_score) * 1.0 + # Lower risk is better
            recency_bonus +
            completeness_bonus +
            lang_bonus
        )

        return round(priority_score, 2)

    def select_top_projects(
        self,
        projects: List[Any],
        duplicate_info: Dict
    ) -> Tuple[List[Any], List[Any]]:
        """
        Select top projects for deep analysis

        Args:
            projects: List of ProjectSummary objects
            duplicate_info: Duplicate detection results

        Returns:
            Tuple of (top_projects, remaining_projects)
        """
        # Calculate priority scores
        scored_projects = []
        for proj in projects:
            score = self.calculate_priority_score(proj)
            scored_projects.append((proj, score))

        # Sort by priority score (descending)
        scored_projects.sort(key=lambda x: x[1], reverse=True)

        # Filter out duplicates (keep only primary)
        filtered_projects = []
        for proj, score in scored_projects:
            # Check if this is a duplicate
            is_duplicate = False
            if hasattr(proj, 'suggestions') and hasattr(proj.suggestions, 'is_duplicate'):
                is_duplicate = proj.suggestions.is_duplicate
            
            if not is_duplicate:
                filtered_projects.append((proj, score))

        # Select top percentage
        top_count = max(1, int(len(filtered_projects) * self.top_percent))
        
        top_projects = [proj for proj, score in filtered_projects[:top_count]]
        remaining_projects = [proj for proj, score in filtered_projects[top_count:]]

        if self.verbose:
            print(f"\n📊 Project Selection:")
            print(f"  Total projects: {len(projects)}")
            print(f"  Duplicates filtered: {len(projects) - len(filtered_projects)}")
            print(f"  Selected for deep scan: {len(top_projects)} ({self.top_percent*100:.0f}%)")
            print(f"  Remaining: {len(remaining_projects)}")

        return top_projects, remaining_projects

    def print_phase_summary(
        self,
        phase: int,
        projects: List[Any],
        elapsed: float,
        duplicate_info: Dict = None
    ):
        """Print summary after each phase"""
        print("\n" + "=" * 60)
        print(f"PHASE {phase} COMPLETE")
        print("=" * 60)
        print(f"Projects processed: {len(projects)}")
        print(f"Time elapsed: {elapsed:.1f}s")
        print(f"Average time per project: {elapsed/len(projects):.1f}s")

        if duplicate_info:
            print(f"\nDuplicate Detection:")
            print(f"  Duplicate pairs found: {duplicate_info['total_duplicates']}")
            print(f"  Unique projects: {duplicate_info['unique_projects']}")
            
            if duplicate_info['duplicate_groups']:
                print(f"\n  Duplicate groups:")
                for group in duplicate_info['duplicate_groups'][:5]:  # Show first 5
                    print(f"    - {group['primary']} (+ {len(group['projects'])-1} duplicates)")

        # Show top projects by priority
        if phase == 1:
            print(f"\nTop 10 projects by priority:")
            scored = [(p, self.calculate_priority_score(p)) for p in projects]
            scored.sort(key=lambda x: x[1], reverse=True)
            
            for i, (proj, score) in enumerate(scored[:10], 1):
                stage_emoji = {
                    'prod': '🚀',
                    'beta': '🔧',
                    'mvp': '🎯',
                    'prototype': '🧪',
                    'idea': '💡',
                    'abandoned': '💀'
                }.get(proj.scores.stage, '📦')
                
                print(f"    {i:2d}. {stage_emoji} {proj.facts.name:30s} "
                      f"(Priority: {score:.1f}, Value: {proj.scores.value_score}/10)")

    def generate_scan_report(
        self,
        phase1_projects: List[Any],
        phase2_projects: List[Any],
        duplicate_info: Dict,
        total_time: float
    ) -> Dict[str, Any]:
        """
        Generate comprehensive scan report

        Args:
            phase1_projects: All projects from phase 1
            phase2_projects: Projects that received deep analysis
            duplicate_info: Duplicate detection results
            total_time: Total scan time

        Returns:
            Report dictionary
        """
        # Model usage summary
        usage_summary = self.usage_tracker.get_summary()

        # Stage distribution
        stage_counts = {}
        for proj in phase1_projects:
            stage = proj.scores.stage
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        # Language distribution
        lang_counts = {}
        for proj in phase1_projects:
            for lang in proj.facts.languages:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1

        return {
            'summary': {
                'total_projects': len(phase1_projects),
                'deep_scanned': len(phase2_projects),
                'duplicates_found': duplicate_info['total_duplicates'],
                'unique_projects': duplicate_info['unique_projects'],
                'total_time_seconds': round(total_time, 2),
                'avg_time_per_project': round(total_time / len(phase1_projects), 2)
            },
            'stage_distribution': stage_counts,
            'language_distribution': dict(sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'model_usage': usage_summary,
            'duplicate_groups': duplicate_info['duplicate_groups'],
            'top_projects': [
                {
                    'name': proj.facts.name,
                    'stage': proj.scores.stage,
                    'value': proj.scores.value_score,
                    'priority': proj.scores.priority,
                    'priority_score': self.calculate_priority_score(proj)
                }
                for proj in sorted(
                    phase2_projects,
                    key=lambda p: self.calculate_priority_score(p),
                    reverse=True
                )[:20]
            ]
        }

    def print_final_report(self, report: Dict[str, Any]):
        """Print final scan report"""
        print("\n" + "=" * 60)
        print("TWO-PHASE SCAN COMPLETE")
        print("=" * 60)
        
        summary = report['summary']
        print(f"\n📊 Summary:")
        print(f"  Total projects scanned: {summary['total_projects']}")
        print(f"  Deep analysis performed: {summary['deep_scanned']}")
        print(f"  Duplicates detected: {summary['duplicates_found']}")
        print(f"  Unique projects: {summary['unique_projects']}")
        print(f"  Total time: {summary['total_time_seconds']:.1f}s")
        print(f"  Avg time/project: {summary['avg_time_per_project']:.1f}s")

        print(f"\n📈 Stage Distribution:")
        for stage, count in sorted(report['stage_distribution'].items(), key=lambda x: x[1], reverse=True):
            bar = "█" * min(50, count)
            print(f"  {stage:12s}: {bar} {count}")

        print(f"\n💻 Top Languages:")
        for lang, count in list(report['language_distribution'].items())[:5]:
            print(f"  {lang:15s}: {count} projects")

        print(f"\n🤖 Model Usage:")
        usage = report['model_usage']
        print(f"  Total API calls: {usage['total_calls']}")
        print(f"  Success rate: {usage['success_rate']}")
        print(f"  Unique models used: {usage['unique_models']}")
        
        if usage['models_used']:
            print(f"\n  Models breakdown:")
            for model, count in list(usage['models_used'].items())[:5]:
                model_short = model.split('/')[-1] if '/' in model else model
                print(f"    - {model_short:30s}: {count} calls")

        print(f"\n🏆 Top 10 Projects (Deep Scanned):")
        for i, proj in enumerate(report['top_projects'][:10], 1):
            stage_emoji = {
                'prod': '🚀',
                'beta': '🔧',
                'mvp': '🎯',
                'prototype': '🧪',
                'idea': '💡',
                'abandoned': '💀'
            }.get(proj['stage'], '📦')
            
            print(f"  {i:2d}. {stage_emoji} {proj['name']:30s} "
                  f"(Value: {proj['value']}/10, Priority: {proj['priority_score']:.1f})")

        print("\n" + "=" * 60)


def run_two_phase_scan(
    projects: List[Any],
    scan_function: callable,
    top_percent: float = 0.4,
    duplicate_threshold: float = 0.8,
    use_auto_model: bool = True,
    prefer_free: bool = True,
    verbose: bool = False
) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Run complete two-phase scan

    Args:
        projects: List of project paths
        scan_function: Function to scan a single project
        top_percent: Percentage for deep scan
        duplicate_threshold: Duplicate similarity threshold
        use_auto_model: Use OpenRouter auto
        prefer_free: Prefer free models
        verbose: Verbose output

    Returns:
        Tuple of (all_summaries, scan_report)
    """
    scanner = TwoPhaseScanner(
        top_percent=top_percent,
        duplicate_threshold=duplicate_threshold,
        use_auto_model=use_auto_model,
        prefer_free=prefer_free,
        verbose=verbose
    )

    total_start = time.time()

    # Phase 1: Fast triage scan
    print("\n" + "=" * 60)
    print("PHASE 1: FAST TRIAGE SCAN")
    print("=" * 60)
    print(f"Scanning {len(projects)} projects with fast heuristics...")
    
    phase1_start = time.time()
    phase1_summaries = []
    
    for i, project_path in enumerate(projects, 1):
        if verbose:
            print(f"\n[{i}/{len(projects)}] Scanning: {project_path.name}")
        
        # Run fast scan (heuristic only, no LLM)
        summary = scan_function(project_path, deep_scan=False, use_llm=False)
        phase1_summaries.append(summary)

    phase1_elapsed = time.time() - phase1_start

    # Detect duplicates
    if verbose:
        print("\n🔍 Detecting duplicates...")
    
    # Convert summaries to dict format for duplicate detector
    summary_dicts = [
        {
            'facts': dataclasses.asdict(s.facts),
            'scores': dataclasses.asdict(s.scores),
            'suggestions': dataclasses.asdict(s.suggestions) if hasattr(s, 'suggestions') else {}
        }
        for s in phase1_summaries
    ]
    
    updated_dicts, duplicate_info = detect_and_mark_duplicates(
        summary_dicts,
        threshold=duplicate_threshold
    )

    # Update original summaries with duplicate markers
    for i, summary in enumerate(phase1_summaries):
        dup_data = updated_dicts[i].get('suggestions', {})
        if hasattr(summary, 'suggestions'):
            summary.suggestions.is_duplicate = dup_data.get('is_duplicate', False)
            summary.suggestions.duplicate_of = dup_data.get('duplicate_of')
            summary.suggestions.duplicate_group = dup_data.get('duplicate_group', [])

    scanner.print_phase_summary(1, phase1_summaries, phase1_elapsed, duplicate_info)

    # Select top projects
    top_projects, remaining = scanner.select_top_projects(phase1_summaries, duplicate_info)

    # Phase 2: Deep analysis
    print("\n" + "=" * 60)
    print("PHASE 2: DEEP ANALYSIS")
    print("=" * 60)
    print(f"Deep scanning top {len(top_projects)} projects with premium LLM models...")
    
    phase2_start = time.time()
    phase2_summaries = []
    
    for i, project_summary in enumerate(top_projects, 1):
        if verbose:
            print(f"\n[{i}/{len(top_projects)}] Deep scan: {project_summary.facts.name}")
        
        # Run deep scan with LLM
        deep_summary = scan_function(
            Path(project_summary.facts.path),
            deep_scan=True,
            use_llm=True,
            use_auto_model=use_auto_model
        )
        phase2_summaries.append(deep_summary)

    phase2_elapsed = time.time() - phase2_start
    scanner.print_phase_summary(2, phase2_summaries, phase2_elapsed)

    # Generate final report
    total_elapsed = time.time() - total_start
    report = scanner.generate_scan_report(
        phase1_summaries,
        phase2_summaries,
        duplicate_info,
        total_elapsed
    )

    scanner.print_final_report(report)

    # Return all summaries (phase 2 replaces phase 1 for top projects)
    final_summaries = phase1_summaries.copy()
    for deep_summary in phase2_summaries:
        # Find and replace in final list
        for i, summary in enumerate(final_summaries):
            if summary.facts.name == deep_summary.facts.name:
                final_summaries[i] = deep_summary
                break

    return final_summaries, report


if __name__ == '__main__':
    # Test
    print("=" * 60)
    print("TWO-PHASE SCANNER - TEST")
    print("=" * 60)
    
    scanner = TwoPhaseScanner(
        top_percent=0.4,
        duplicate_threshold=0.8,
        use_auto_model=True,
        prefer_free=True,
        verbose=True
    )
    
    print(f"\nConfiguration:")
    print(f"  Top percent: {scanner.top_percent*100:.0f}%")
    print(f"  Duplicate threshold: {scanner.duplicate_threshold}")
    print(f"  Auto model: {scanner.use_auto_model}")
    print(f"  Prefer free: {scanner.prefer_free}")
    
    info = scanner.router.get_model_info()
    print(f"\nModel Router:")
    print(f"  Mode: {info['mode']}")
    print(f"  Cloaked models: {len(info['cloaked_models'])}")
    print(f"  Premium models: {len(info['premium_models'])}")
