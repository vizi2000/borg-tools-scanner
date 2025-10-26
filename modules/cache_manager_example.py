#!/usr/bin/env python3
"""
Example usage of CacheManager for LLM response caching.

This example demonstrates:
1. Basic cache operations (set, get)
2. Staleness detection
3. Cache statistics
4. Integration with LLM scanning workflow

Created by The Collective Borg.tools
"""

import json
from pathlib import Path
from cache_manager import CacheManager


def simulate_llm_analysis(project_path: str) -> dict:
    """
    Simulate an expensive LLM analysis operation.
    In real usage, this would call an actual LLM API.
    """
    print(f"🤖 Performing expensive LLM analysis for {project_path}...")
    # Simulate processing time
    import time
    time.sleep(0.5)

    return {
        'analysis': 'Comprehensive code analysis',
        'quality_score': 85,
        'findings': [
            'Good code structure',
            'Missing some unit tests',
            'Documentation could be improved'
        ],
        'metrics': {
            'complexity': 12,
            'maintainability': 78,
            'test_coverage': 65
        }
    }


def analyze_project_with_cache(
    project_path: str,
    model_name: str = "gpt-4",
    cache_db: str = "cache.db",
    force_refresh: bool = False
) -> dict:
    """
    Analyze project with caching support.

    Args:
        project_path: Path to project directory
        model_name: LLM model name
        cache_db: Path to cache database
        force_refresh: If True, skip cache and force new analysis

    Returns:
        Analysis results dictionary
    """
    with CacheManager(cache_db) as cache:
        if not force_refresh:
            # Try to get cached response
            cached = cache.get_cached(project_path, model_name)
            if cached:
                print(f"✅ Using cached analysis for {project_path}")
                return cached

        # Perform new analysis
        print(f"🔍 No valid cache found, performing new analysis...")
        result = simulate_llm_analysis(project_path)

        # Cache the result
        cache.set_cache(project_path, model_name, result)
        print(f"💾 Analysis cached for future use")

        return result


def main():
    """Demonstrate cache manager usage."""
    print("="*60)
    print("CacheManager Example - LLM Response Caching")
    print("="*60)

    # Use temporary cache database for demo
    cache_db = "demo_cache.db"
    project_path = "/tmp/example_project"

    # Ensure project directory exists
    Path(project_path).mkdir(exist_ok=True)
    (Path(project_path) / "main.py").write_text("print('hello')")

    print("\n1️⃣ First scan (cache miss - will be slow)")
    print("-" * 60)
    result1 = analyze_project_with_cache(project_path, cache_db=cache_db)
    print(f"Quality Score: {result1['quality_score']}")
    print(f"Findings: {len(result1['findings'])} items")

    print("\n2️⃣ Second scan (cache hit - instant)")
    print("-" * 60)
    result2 = analyze_project_with_cache(project_path, cache_db=cache_db)
    print(f"Quality Score: {result2['quality_score']}")

    print("\n3️⃣ Modify project file (will invalidate cache)")
    print("-" * 60)
    import time
    time.sleep(0.1)  # Ensure different mtime
    (Path(project_path) / "main.py").write_text("print('hello world')")
    result3 = analyze_project_with_cache(project_path, cache_db=cache_db)
    print(f"Cache was invalidated due to file modification")

    print("\n4️⃣ Cache statistics")
    print("-" * 60)
    with CacheManager(cache_db) as cache:
        stats = cache.get_stats()
        print(f"Total cached entries: {stats['total_entries']}")
        print(f"Database size: {stats['database_size_mb']} MB")
        print(f"Oldest entry: {stats['oldest_entry']}")
        print(f"Newest entry: {stats['newest_entry']}")

    print("\n5️⃣ Multiple models example")
    print("-" * 60)

    # Cache with different models
    with CacheManager(cache_db) as cache:
        gpt_result = {'model': 'gpt-4', 'score': 90}
        claude_result = {'model': 'claude-3', 'score': 92}

        cache.set_cache(project_path, "gpt-4", gpt_result)
        cache.set_cache(project_path, "claude-3", claude_result)

        # Retrieve separately
        cached_gpt = cache.get_cached(project_path, "gpt-4")
        cached_claude = cache.get_cached(project_path, "claude-3")

        print(f"GPT-4 result: {cached_gpt}")
        print(f"Claude-3 result: {cached_claude}")

    print("\n6️⃣ Cache hit rate demonstration")
    print("-" * 60)

    with CacheManager(cache_db) as cache:
        hits = 0
        misses = 0

        for i in range(10):
            result = cache.get_cached(project_path, "gpt-4")
            if result:
                hits += 1
            else:
                misses += 1

        hit_rate = (hits / (hits + misses)) * 100
        print(f"Cache hits: {hits}")
        print(f"Cache misses: {misses}")
        print(f"Hit rate: {hit_rate:.1f}%")

    print("\n" + "="*60)
    print("✅ Demo completed successfully!")
    print("="*60)

    # Cleanup
    import os
    if os.path.exists(cache_db):
        print(f"\n💡 Cache database created at: {os.path.abspath(cache_db)}")
        print(f"   Use 'rm {cache_db}' to clean up")


if __name__ == "__main__":
    main()
