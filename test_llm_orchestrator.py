"""
Test LLM Orchestrator with real API calls

This script tests the LLM orchestrator with a small real project
to verify parallel execution, rate limiting, and API integration.

Created by The Collective Borg.tools
"""

import asyncio
import json
import time
from pathlib import Path
from modules.llm_orchestrator import analyze_with_llm


async def test_with_sample_project():
    """Test with current project (small subset)"""

    print("=" * 70)
    print("LLM ORCHESTRATOR - REAL API TEST")
    print("=" * 70)
    print()

    # Use the current project as test data
    project_data = {
        'name': 'Borg.tools_scan',
        'path': str(Path.cwd()),
        'languages': ['python'],
        'code_analysis': {
            'code_quality': {
                'overall_score': 7.8,
                'architecture_pattern': 'Feature-based',
                'modularity_score': 8.0,
                'complexity_metrics': {
                    'avg_cyclomatic': 4.5,
                    'avg_cognitive': 3.2
                },
                'readability': {
                    'score': 7.5,
                    'documentation_coverage': 0.75
                }
            }
        },
        'deployment_analysis': {
            'deployment_confidence': 0.85,
            'dockerfile_present': False,
            'docker_compose_present': False,
            'ci_cd_configured': False,
            'blockers': [
                {
                    'severity': 'medium',
                    'issue': 'No containerization configured',
                    'recommendation': 'Add Dockerfile for consistent deployment'
                }
            ]
        },
        'doc_analysis': {
            'documentation_quality': 0.8,
            'readme_present': True,
            'api_docs_present': False,
            'examples_present': True
        }
    }

    print("📋 Project Information:")
    print(f"  Name: {project_data['name']}")
    print(f"  Languages: {', '.join(project_data['languages'])}")
    print(f"  Code Quality Score: {project_data['code_analysis']['code_quality']['overall_score']}/10")
    print()

    # Test 1: Dry run first
    print("🎭 TEST 1: Dry Run (Mock Responses)")
    print("-" * 70)
    start = time.time()
    dry_result = await analyze_with_llm(project_data, dry_run=True)
    dry_elapsed = time.time() - start

    print(f"\n✅ Dry run completed in {dry_elapsed:.2f}s")
    print(f"  API Calls: {dry_result['llm_results']['metadata']['api_calls']}")
    print(f"  Cache Hits: {dry_result['llm_results']['metadata']['cache_hits']}")
    print()

    # Test 2: Real API call
    print("🚀 TEST 2: Real API Call")
    print("-" * 70)
    print("⚠️  This will make real API calls to OpenRouter")

    # Check if API key is set
    import os
    if not os.getenv('OPENROUTER_API_KEY'):
        print("❌ OPENROUTER_API_KEY not set - skipping real API test")
        print("   Set the environment variable to test with real API")
        return

    print("✅ API key found - proceeding with real API test")
    print()

    start = time.time()
    try:
        real_result = await analyze_with_llm(project_data, dry_run=False)
        real_elapsed = time.time() - start

        print(f"\n✅ Real API test completed in {real_elapsed:.2f}s")
        print()
        print("📊 Results Summary:")
        print("-" * 70)

        metadata = real_result['llm_results']['metadata']
        print(f"  Total Time: {metadata['total_time_seconds']:.2f}s")
        print(f"  API Calls: {metadata['api_calls']}")
        print(f"  Cache Hits: {metadata['cache_hits']}")
        print()

        # Show architect analysis
        arch = real_result['llm_results']['architect_analysis']
        print("🏗️  Architect Analysis:")
        if 'architecture_assessment' in arch:
            print(f"  Assessment: {arch['architecture_assessment'][:100]}...")
        else:
            print(f"  {json.dumps(arch, indent=4)}")
        print()

        # Show deployment analysis
        deploy = real_result['llm_results']['deployment_analysis']
        print("🚀 Deployment Analysis:")
        if 'deployment_strategy' in deploy:
            print(f"  Strategy: {deploy['deployment_strategy'][:100]}...")
        else:
            print(f"  {json.dumps(deploy, indent=4)}")
        print()

        # Show business analysis
        business = real_result['llm_results']['business_analysis']
        print("💼 Business Analysis:")
        if 'problem_solved' in business:
            print(f"  Problem: {business['problem_solved'][:100]}...")
            if 'market_viability' in business:
                print(f"  Market Viability: {business['market_viability']}/10")
        else:
            print(f"  {json.dumps(business, indent=4)}")
        print()

        # Show aggregated insights
        insights = real_result['llm_results']['aggregated_insights']
        print("🎯 Aggregated Insights:")
        if 'vibecodibility_score' in insights:
            print(f"  Vibecodibility Score: {insights['vibecodibility_score']}/10")
            print(f"  Borg.tools Fit: {insights['borg_tools_fit']}/10")
        if 'top_priorities' in insights:
            print(f"  Top Priorities:")
            for i, priority in enumerate(insights['top_priorities'][:3], 1):
                print(f"    {i}. {priority}")
        print()

        # Verify parallel execution
        print("⚡ Performance Analysis:")
        print("-" * 70)
        models_called = metadata['api_calls']
        avg_time_per_model = metadata['total_time_seconds'] / max(models_called, 1)

        print(f"  Models Called: {models_called}")
        print(f"  Average Time per Model: {avg_time_per_model:.2f}s")

        if models_called >= 3:
            # If we called 3+ models, check if time suggests parallelism
            # Sequential would be ~3x the average, parallel should be ~1x
            expected_sequential = avg_time_per_model * 3
            speedup = expected_sequential / metadata['total_time_seconds']
            print(f"  Parallel Speedup: {speedup:.2f}x")

            if speedup > 1.5:
                print("  ✅ Parallel execution confirmed!")
            else:
                print("  ⚠️  Execution may be sequential (low speedup)")
        print()

        # Save full results to file
        output_file = Path.cwd() / 'test_llm_results.json'
        with open(output_file, 'w') as f:
            json.dump(real_result, f, indent=2)
        print(f"💾 Full results saved to: {output_file}")
        print()

    except Exception as e:
        print(f"\n❌ Real API test failed: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


async def test_rate_limiter():
    """Test rate limiter in isolation"""
    from modules.llm_orchestrator import RateLimiter

    print("\n🧪 Testing Rate Limiter")
    print("-" * 70)

    limiter = RateLimiter(calls_per_minute=10)

    print("Acquiring 5 tokens rapidly...")
    start = time.time()
    for i in range(5):
        await limiter.acquire()
        print(f"  Token {i+1} acquired at {time.time() - start:.2f}s")

    elapsed = time.time() - start
    print(f"\n✅ Acquired 5 tokens in {elapsed:.2f}s")
    print(f"  Expected: ~0s (tokens available)")
    print(f"  Tokens should be available instantly\n")


async def main():
    """Run all tests"""
    # Test rate limiter first
    await test_rate_limiter()

    # Test with sample project
    await test_with_sample_project()


if __name__ == '__main__':
    asyncio.run(main())
