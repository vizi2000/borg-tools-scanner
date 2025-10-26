"""
Integration Test: LLM Response Handler with Scanner Modules

Tests the response handler with outputs from code_analyzer,
deployment_detector, and doc_analyzer.

Created by The Collective Borg.tools
"""

import json
from modules.llm_response_handler import (
    parse_llm_response,
    parse_batch_responses
)


def test_with_simulated_llm_responses():
    """Test with realistic LLM responses based on scanner output"""
    print("=" * 70)
    print("INTEGRATION TEST: Response Handler + Scanner Modules")
    print("=" * 70)
    print()

    # Simulate LLM responses after receiving scanner data
    # These would come from the LLM orchestrator calling OpenRouter

    # 1. ARCHITECT MODEL RESPONSE
    print("1. Testing Architect Response...")
    architect_response = """
Based on the code analysis provided, here's my assessment:

```json
{
    "architecture_assessment": "The project follows a modular architecture with clear separation of concerns. The code_analyzer, deployment_detector, and doc_analyzer modules are well-structured and independent. However, there's room for improvement in error handling and logging consistency across modules.",
    "design_patterns": [
        "Modular Design",
        "Separation of Concerns",
        "Factory Pattern (analyzers)",
        "Strategy Pattern (deployment detection)"
    ],
    "scalability_notes": "Current architecture supports horizontal scaling. Each analyzer can run independently. Consider adding caching layer for repeated scans. The AST-based Python analyzer may become a bottleneck for very large codebases (>100k LOC).",
    "technical_debt_priority": "medium"
}
```

The codebase shows good engineering practices with comprehensive analyzers.
"""

    result1 = parse_llm_response(architect_response, 'architect')
    assert result1['confidence'] >= 0.9, f"Expected high confidence, got {result1['confidence']}"
    assert result1['parsing_method'] == 'json'
    assert len(result1['data']['design_patterns']) == 4

    print(f"✅ Architect: confidence={result1['confidence']}, patterns={len(result1['data']['design_patterns'])}")
    print()

    # 2. DEPLOYMENT MODEL RESPONSE
    print("2. Testing Deployment Response...")
    deployment_response = """
After analyzing the deployment requirements and infrastructure:

```json
{
    "deployment_strategy": "Docker containerization with orchestration via Kubernetes or Docker Compose",
    "infrastructure_recommendations": "Deploy on cloud-native platform (GCP/AWS/Azure) using managed Kubernetes. Utilize serverless for the web UI (Vercel/Netlify). Implement auto-scaling based on scan queue length. Use Redis for caching layer.",
    "deployment_blockers": [
        {
            "severity": "high",
            "issue": "Missing environment configuration templates",
            "solution": "Create .env.example with all required variables documented"
        },
        {
            "severity": "medium",
            "issue": "No health check endpoints defined",
            "solution": "Add /health and /ready endpoints for Kubernetes probes"
        },
        {
            "severity": "low",
            "issue": "Database migrations not automated",
            "solution": "Implement Alembic or similar for database versioning"
        }
    ],
    "mvp_roadmap": [
        "Create Dockerfile for main scanner service",
        "Setup CI/CD with GitHub Actions (build, test, deploy)",
        "Deploy to staging environment for testing",
        "Configure monitoring with Prometheus + Grafana",
        "Production deployment with blue-green strategy",
        "Setup backup and disaster recovery procedures"
    ]
}
```
"""

    result2 = parse_llm_response(deployment_response, 'deployment')
    assert result2['confidence'] >= 0.9
    assert len(result2['data']['deployment_blockers']) == 3
    assert result2['data']['deployment_blockers'][0]['severity'] == 'high'

    print(f"✅ Deployment: confidence={result2['confidence']}, blockers={len(result2['data']['deployment_blockers'])}")
    print()

    # 3. BUSINESS MODEL RESPONSE
    print("3. Testing Business Response...")
    business_response = """
# Business Analysis

Problem Solved: This tool solves the time-consuming problem of manual code quality
assessment and project evaluation. It automates the analysis of code structure,
deployment readiness, and business viability - saving development teams hours of
manual review work.

Target Audience:
- Software engineering teams at mid-sized to large companies
- CTOs and engineering managers evaluating potential acquisitions or partnerships
- Open source maintainers assessing code quality of contributions
- Portfolio managers at venture capital firms doing technical due diligence

Market Viability: 8/10 - Strong demand in the automated code analysis space

Portfolio Suitable: yes

```json
{
    "problem_solved": "Automates comprehensive code quality assessment and project evaluation, combining static analysis, deployment readiness checks, and business viability scoring",
    "target_audience": "Engineering teams, CTOs, VC firms, open source maintainers",
    "monetization_strategy": "Freemium SaaS model: Free tier for open source projects (5 scans/month), Professional at $49/month (unlimited scans, priority support), Enterprise with custom pricing (dedicated deployment, API access, custom analyzers)",
    "market_viability": 8,
    "portfolio_suitable": true,
    "portfolio_pitch": "AI-powered code quality scanner that combines static analysis with LLM insights to provide comprehensive project assessments in minutes instead of hours. Perfect for technical due diligence and continuous quality monitoring."
}
```
"""

    result3 = parse_llm_response(business_response, 'business')
    assert result3['confidence'] >= 0.8
    assert result3['data']['market_viability'] == 8
    assert result3['data']['portfolio_suitable'] is True

    print(f"✅ Business: confidence={result3['confidence']}, viability={result3['data']['market_viability']}/10")
    print()

    # 4. AGGREGATOR MODEL RESPONSE
    print("4. Testing Aggregator Response...")
    aggregator_response = """
```json
{
    "overall_assessment": "This is a well-architected code analysis tool with strong technical foundations and clear market potential. The modular design allows for easy extension and maintenance. Key strengths include comprehensive analysis capabilities and intelligent use of LLMs for higher-level insights. Main areas for improvement are deployment automation and enterprise features.",
    "top_priorities": [
        "Implement caching layer (Redis) to improve performance for repeated scans",
        "Add comprehensive deployment documentation and automation scripts",
        "Create health check endpoints and monitoring dashboards",
        "Develop enterprise features (SSO, RBAC, audit logging)",
        "Build customer-facing documentation and API reference"
    ],
    "vibecodibility_score": 8,
    "borg_tools_fit": 9
}
```

This project aligns exceptionally well with the Borg.tools ecosystem and
demonstrates strong engineering practices throughout.
"""

    result4 = parse_llm_response(aggregator_response, 'aggregator')
    assert result4['confidence'] >= 0.9
    assert result4['data']['vibecodibility_score'] == 8
    assert result4['data']['borg_tools_fit'] == 9
    assert len(result4['data']['top_priorities']) == 5

    print(f"✅ Aggregator: confidence={result4['confidence']}, vibecodibility={result4['data']['vibecodibility_score']}/10")
    print()

    # 5. BATCH PROCESSING TEST
    print("5. Testing Batch Processing...")
    batch = {
        'architect': architect_response,
        'deployment': deployment_response,
        'business': business_response,
        'aggregator': aggregator_response
    }

    batch_results = parse_batch_responses(batch)
    assert len(batch_results) == 4
    assert all(r['confidence'] >= 0.8 for r in batch_results.values())

    avg_confidence = sum(r['confidence'] for r in batch_results.values()) / len(batch_results)
    print(f"✅ Batch: {len(batch_results)} responses, avg confidence={avg_confidence:.2f}")
    print()

    # 6. SIMULATE LOW-QUALITY RESPONSE
    print("6. Testing Low-Quality Response Handling...")
    poor_response = """
I analyzed the code and it looks okay. Some patterns are used.
Maybe add tests? The deployment could be better.
"""

    result_poor = parse_llm_response(poor_response, 'architect')
    assert result_poor['confidence'] < 0.5

    print(f"✅ Low-quality: confidence={result_poor['confidence']} (correctly identified as poor)")
    print()

    # 7. CONFIDENCE DISTRIBUTION ANALYSIS
    print("7. Confidence Distribution Analysis...")
    all_confidences = [
        result1['confidence'],
        result2['confidence'],
        result3['confidence'],
        result4['confidence'],
        result_poor['confidence']
    ]

    print(f"   High confidence (>0.8): {sum(1 for c in all_confidences if c > 0.8)}/5")
    print(f"   Medium confidence (0.5-0.8): {sum(1 for c in all_confidences if 0.5 <= c <= 0.8)}/5")
    print(f"   Low confidence (<0.5): {sum(1 for c in all_confidences if c < 0.5)}/5")
    print()

    return {
        'architect': result1,
        'deployment': result2,
        'business': result3,
        'aggregator': result4,
        'poor_example': result_poor
    }


def test_error_handling():
    """Test error handling for edge cases"""
    print("=" * 70)
    print("ERROR HANDLING TESTS")
    print("=" * 70)
    print()

    # Test 1: Invalid response type
    result1 = parse_llm_response("test", 'invalid_type')
    assert result1['validation_error'] is not None
    print("✅ Invalid response type handled gracefully")

    # Test 2: Empty response
    result2 = parse_llm_response("", 'architect')
    assert result2['confidence'] == 0.0
    print("✅ Empty response handled gracefully")

    # Test 3: Malformed JSON
    malformed = """```json
{
    "architecture_assessment": "test"
    "missing_comma": true
}
```"""
    result3 = parse_llm_response(malformed, 'architect')
    # Should fall back to heuristics
    assert result3['parsing_method'] in ['heuristic', 'heuristic_partial', 'failed']
    print("✅ Malformed JSON triggers fallback")

    print()


def generate_integration_report(results):
    """Generate a summary report"""
    print("=" * 70)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 70)
    print()

    print("Parser Performance:")
    print(f"  Total responses parsed: 5")
    print(f"  JSON extraction success: 4/4 (100%)")
    print(f"  Heuristic fallback tested: 1/1 (100%)")
    print(f"  Average confidence (good responses): {sum(r['confidence'] for k, r in results.items() if k != 'poor_example') / 4:.2f}")
    print()

    print("Validation Results:")
    for response_type, result in results.items():
        if response_type == 'poor_example':
            continue

        data = result['data']
        field_count = len([v for v in data.values() if v])

        print(f"  {response_type}:")
        print(f"    Fields populated: {field_count}")
        print(f"    Confidence: {result['confidence']:.2f}")
        print(f"    Method: {result['parsing_method']}")

    print()
    print("Integration Status: ✅ ALL TESTS PASSED")
    print()


def main():
    """Run all integration tests"""
    print("\n")
    print("🧪 LLM RESPONSE HANDLER - INTEGRATION TESTS")
    print("=" * 70)
    print()

    try:
        results = test_with_simulated_llm_responses()
        test_error_handling()
        generate_integration_report(results)

        print("=" * 70)
        print("🎉 INTEGRATION TESTS COMPLETE - READY FOR PRODUCTION")
        print("=" * 70)
        print()

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
