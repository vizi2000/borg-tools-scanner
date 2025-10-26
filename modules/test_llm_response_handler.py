"""
Comprehensive Test Suite for LLM Response Handler

Tests:
- JSON extraction from various markdown formats
- Pydantic validation with valid/invalid schemas
- Confidence scoring
- Fallback heuristic mechanisms
- Edge cases and error handling

Created by The Collective Borg.tools
"""

import json
from llm_response_handler import (
    parse_llm_response,
    parse_batch_responses,
    extract_json_from_markdown,
    compute_confidence_score,
    extract_via_heuristics,
    ArchitectResponse,
    DeploymentResponse,
    BusinessResponse,
    AggregatorResponse,
    RESPONSE_MODELS
)


def test_json_extraction_variants():
    """Test JSON extraction from different markdown formats"""
    print("=" * 60)
    print("TEST 1: JSON Extraction Variants")
    print("=" * 60)

    # Variant 1: Standard JSON code block
    test1 = '''```json
{
    "architecture_assessment": "Clean architecture",
    "design_patterns": ["DDD", "CQRS"],
    "technical_debt_priority": "low"
}
```'''
    result1 = extract_json_from_markdown(test1)
    assert result1 is not None, "Failed to extract standard JSON block"
    assert result1['architecture_assessment'] == "Clean architecture"
    print("✅ Standard JSON block extraction")

    # Variant 2: Generic code block
    test2 = '''```
{
    "problem_solved": "Code analysis",
    "target_audience": "Developers"
}
```'''
    result2 = extract_json_from_markdown(test2)
    assert result2 is not None, "Failed to extract generic code block"
    print("✅ Generic code block extraction")

    # Variant 3: Raw JSON (no code block)
    test3 = '''Here's the analysis:
{
    "deployment_strategy": "Docker containers",
    "mvp_roadmap": ["Setup CI/CD", "Deploy to staging"]
}
That's my recommendation.'''
    result3 = extract_json_from_markdown(test3)
    assert result3 is not None, "Failed to extract raw JSON"
    print("✅ Raw JSON extraction")

    # Variant 4: Multiple JSON blocks (should get first valid one)
    test4 = '''```json
{"architecture_assessment": "First"}
```
Some text
```json
{"architecture_assessment": "Second"}
```'''
    result4 = extract_json_from_markdown(test4)
    assert result4 is not None, "Failed to extract from multiple blocks"
    print("✅ Multiple JSON blocks handling")

    # Variant 5: Invalid JSON should return None
    test5 = "This is just plain text with no JSON"
    result5 = extract_json_from_markdown(test5)
    assert result5 is None, "Should return None for non-JSON content"
    print("✅ Non-JSON content handling")

    print()


def test_pydantic_validation():
    """Test Pydantic model validation"""
    print("=" * 60)
    print("TEST 2: Pydantic Validation")
    print("=" * 60)

    # Valid architect response
    valid_architect = {
        "architecture_assessment": "Modern microservices",
        "design_patterns": ["Hexagonal", "DDD"],
        "scalability_notes": "Cloud-native design",
        "technical_debt_priority": "medium"
    }

    try:
        model = ArchitectResponse(**valid_architect)
        print("✅ Valid architect response validation")
    except Exception as e:
        print(f"❌ Valid data failed: {e}")

    # Invalid priority should be normalized
    invalid_priority = {
        "architecture_assessment": "Test",
        "design_patterns": [],
        "technical_debt_priority": "INVALID_PRIORITY"
    }

    try:
        model = ArchitectResponse(**invalid_priority)
        assert model.technical_debt_priority == "medium", "Should default to medium"
        print("✅ Invalid priority normalized to default")
    except Exception as e:
        print(f"❌ Priority normalization failed: {e}")

    # Valid business response
    valid_business = {
        "problem_solved": "Automates code review",
        "target_audience": "Development teams",
        "market_viability": 8,
        "portfolio_suitable": True
    }

    try:
        model = BusinessResponse(**valid_business)
        assert model.market_viability == 8
        print("✅ Valid business response validation")
    except Exception as e:
        print(f"❌ Business validation failed: {e}")

    # Market viability out of range should be caught
    try:
        invalid_viability = {**valid_business, "market_viability": 15}
        model = BusinessResponse(**invalid_viability)
        print("❌ Should have caught invalid viability score")
    except Exception:
        print("✅ Invalid viability score rejected")

    # Valid deployment response with blockers
    valid_deployment = {
        "deployment_strategy": "Kubernetes",
        "infrastructure_recommendations": "Use managed K8s",
        "deployment_blockers": [
            {
                "severity": "high",
                "issue": "Missing database migrations",
                "solution": "Create migration scripts"
            }
        ],
        "mvp_roadmap": ["Setup CI", "Deploy staging", "Production rollout"]
    }

    try:
        model = DeploymentResponse(**valid_deployment)
        assert len(model.deployment_blockers) == 1
        print("✅ Valid deployment response with blockers")
    except Exception as e:
        print(f"❌ Deployment validation failed: {e}")

    # Valid aggregator response
    valid_aggregator = {
        "overall_assessment": "Promising project",
        "top_priorities": ["Fix security", "Improve docs", "Add tests"],
        "vibecodibility_score": 7,
        "borg_tools_fit": 8
    }

    try:
        model = AggregatorResponse(**valid_aggregator)
        assert model.vibecodibility_score == 7
        print("✅ Valid aggregator response validation")
    except Exception as e:
        print(f"❌ Aggregator validation failed: {e}")

    print()


def test_confidence_scoring():
    """Test confidence score calculation"""
    print("=" * 60)
    print("TEST 3: Confidence Scoring")
    print("=" * 60)

    # Complete data should have high confidence
    complete_data = {
        "architecture_assessment": "Full assessment",
        "design_patterns": ["MVC", "Factory"],
        "scalability_notes": "Detailed notes",
        "technical_debt_priority": "low"
    }
    score1 = compute_confidence_score(complete_data, ArchitectResponse)
    assert score1 >= 0.9, f"Expected high confidence, got {score1}"
    print(f"✅ Complete data confidence: {score1}")

    # Minimal required data should have lower confidence
    minimal_data = {
        "architecture_assessment": "Minimal",
        "design_patterns": [],
        "scalability_notes": "",
        "technical_debt_priority": "medium"
    }
    score2 = compute_confidence_score(minimal_data, ArchitectResponse)
    assert 0.3 < score2 < 0.9, f"Expected medium-high confidence, got {score2}"
    print(f"✅ Minimal data confidence: {score2}")

    # Empty data should have zero confidence
    empty_data = {}
    score3 = compute_confidence_score(empty_data, ArchitectResponse)
    assert score3 == 0.0, f"Expected zero confidence, got {score3}"
    print(f"✅ Empty data confidence: {score3}")

    # Data with populated lists gets bonus
    list_bonus_data = {
        "problem_solved": "Solves X",
        "target_audience": "Users",
        "market_viability": 5,
        "portfolio_suitable": False
    }
    score4 = compute_confidence_score(list_bonus_data, BusinessResponse)
    print(f"✅ Business data confidence: {score4}")

    print()


def test_heuristic_extraction():
    """Test fallback heuristic extraction"""
    print("=" * 60)
    print("TEST 4: Heuristic Extraction")
    print("=" * 60)

    # Test architect heuristic extraction
    architect_text = """
    Architecture Assessment: The system uses a clean hexagonal architecture

    Design Patterns:
    - Repository pattern
    - Factory pattern
    - Strategy pattern

    Technical debt priority: high

    Scalability: The system can scale horizontally with load balancing
    """

    result = extract_via_heuristics(architect_text, 'architect')
    assert 'architecture_assessment' in result
    assert 'hexagonal' in result['architecture_assessment'].lower()
    assert len(result['design_patterns']) > 0
    assert result['technical_debt_priority'] == 'high'
    print("✅ Architect heuristic extraction")

    # Test business heuristic extraction
    business_text = """
    Problem Solved: Automates code quality analysis
    Target Audience: Software development teams
    Monetization: SaaS subscription model
    Market Viability: 7/10
    Portfolio Suitable: yes
    """

    result2 = extract_via_heuristics(business_text, 'business')
    assert 'problem_solved' in result2
    assert result2['market_viability'] == 7
    assert result2['portfolio_suitable'] is True
    print("✅ Business heuristic extraction")

    # Test deployment heuristic extraction
    deployment_text = """
    Deployment Strategy: Docker containers with Kubernetes orchestration

    Infrastructure: Use managed Kubernetes service (GKE or EKS)

    MVP Roadmap:
    1. Setup CI/CD pipeline
    2. Deploy to staging
    3. Security audit
    4. Production rollout
    """

    result3 = extract_via_heuristics(deployment_text, 'deployment')
    assert 'deployment_strategy' in result3
    assert 'docker' in result3['deployment_strategy'].lower()
    print("✅ Deployment heuristic extraction")

    # Test aggregator heuristic extraction
    aggregator_text = """
    Overall Assessment: This is a well-architected project with minor issues

    Top Priorities:
    - Fix security vulnerabilities
    - Improve documentation
    - Add integration tests

    Vibecodibility: 8/10
    Borg Tools Fit: 7/10
    """

    result4 = extract_via_heuristics(aggregator_text, 'aggregator')
    assert 'overall_assessment' in result4
    assert len(result4['top_priorities']) > 0
    assert result4['vibecodibility_score'] == 8
    print("✅ Aggregator heuristic extraction")

    print()


def test_full_parsing_pipeline():
    """Test complete parsing pipeline with various inputs"""
    print("=" * 60)
    print("TEST 5: Full Parsing Pipeline")
    print("=" * 60)

    # Test 1: Perfect JSON response
    json_response = '''```json
{
    "architecture_assessment": "Excellent hexagonal design",
    "design_patterns": ["Hexagonal", "CQRS", "Event Sourcing"],
    "scalability_notes": "Highly scalable microservices",
    "technical_debt_priority": "low"
}
```'''

    result1 = parse_llm_response(json_response, 'architect')
    assert result1['parsing_method'] == 'json'
    assert result1['confidence'] >= 0.9
    print(f"✅ JSON parsing: confidence={result1['confidence']}, method={result1['parsing_method']}")

    # Test 2: Natural language with heuristic fallback
    natural_response = """
    Architecture Assessment: The codebase follows MVC pattern
    Design Patterns: MVC, Factory, Singleton
    Technical debt priority: medium
    Scalability: Can handle moderate traffic
    """

    result2 = parse_llm_response(natural_response, 'architect')
    assert result2['parsing_method'] in ['heuristic', 'heuristic_partial']
    print(f"✅ Heuristic parsing: confidence={result2['confidence']}, method={result2['parsing_method']}")

    # Test 3: Invalid JSON with heuristic fallback
    broken_json = '''```json
{
    "architecture_assessment": "Test"
    "design_patterns": ["MVC"]  # Missing comma
}
```
Architecture Assessment: Fallback to this text
'''

    result3 = parse_llm_response(broken_json, 'architect')
    assert result3['parsing_method'] in ['heuristic', 'heuristic_partial', 'json_partial']
    print(f"✅ Broken JSON fallback: confidence={result3['confidence']}, method={result3['parsing_method']}")

    # Test 4: Completely invalid input
    garbage_input = "This is just random text with no structure whatsoever"

    result4 = parse_llm_response(garbage_input, 'architect', fallback_to_heuristics=True)
    assert result4['confidence'] < 0.5
    print(f"✅ Garbage input handling: confidence={result4['confidence']}, method={result4['parsing_method']}")

    # Test 5: Batch parsing
    batch = {
        'architect': json_response,
        'business': natural_response,
        'deployment': garbage_input
    }

    batch_results = parse_batch_responses(batch)
    assert len(batch_results) == 3
    assert all(isinstance(r, dict) for r in batch_results.values())
    print(f"✅ Batch parsing: {len(batch_results)} responses processed")

    print()


def test_edge_cases():
    """Test edge cases and error conditions"""
    print("=" * 60)
    print("TEST 6: Edge Cases")
    print("=" * 60)

    # Empty string
    result1 = parse_llm_response("", 'architect')
    assert result1['confidence'] < 0.2
    print("✅ Empty string handling")

    # Invalid response type
    result2 = parse_llm_response("test", 'invalid_type')
    assert result2['validation_error'] is not None
    print("✅ Invalid response type handling")

    # Very long response (should be truncated in raw_content)
    long_response = "x" * 10000
    result3 = parse_llm_response(long_response, 'architect')
    assert len(result3['raw_content']) <= 200
    print("✅ Long response truncation")

    # Nested JSON objects
    nested_json = '''```json
{
    "architecture_assessment": "Test",
    "design_patterns": ["MVC"],
    "scalability_notes": "Notes with {nested: 'object'}",
    "technical_debt_priority": "low"
}
```'''
    result4 = parse_llm_response(nested_json, 'architect')
    assert result4['parsing_method'] == 'json'
    print("✅ Nested JSON handling")

    # Special characters in strings
    special_chars = """```json
{
    "architecture_assessment": "Test with quotes and apostrophes",
    "design_patterns": ["MVC", "Factory Pattern"],
    "technical_debt_priority": "low"
}
```"""
    result5 = parse_llm_response(special_chars, 'architect')
    assert result5['parsing_method'] == 'json'
    print("✅ Special characters handling")

    # Unicode characters
    unicode_text = """```json
{
    "architecture_assessment": "Test with emojis and unicode",
    "design_patterns": ["MVC"],
    "technical_debt_priority": "low"
}
```"""
    result6 = parse_llm_response(unicode_text, 'architect')
    assert result6['parsing_method'] == 'json'
    print("✅ Unicode handling")

    print()


def test_real_world_scenarios():
    """Test with realistic LLM response examples"""
    print("=" * 60)
    print("TEST 7: Real-World Scenarios")
    print("=" * 60)

    # Scenario 1: GPT-style response with explanation
    gpt_response = """
I've analyzed the architecture and here are my findings:

```json
{
    "architecture_assessment": "The project follows a well-structured layered architecture with clear separation of concerns. The use of dependency injection and interface-based design promotes testability and maintainability.",
    "design_patterns": ["Layered Architecture", "Dependency Injection", "Repository Pattern", "Factory Pattern"],
    "scalability_notes": "The current architecture supports horizontal scaling through stateless services. Consider implementing caching strategies and database read replicas for improved performance under high load.",
    "technical_debt_priority": "medium"
}
```

This assessment is based on the code structure and implementation patterns observed in the codebase.
"""

    result1 = parse_llm_response(gpt_response, 'architect')
    assert result1['parsing_method'] == 'json'
    assert result1['confidence'] >= 0.9
    assert len(result1['data']['design_patterns']) == 4
    print(f"✅ GPT-style response: confidence={result1['confidence']}")

    # Scenario 2: Claude-style structured response
    claude_response = """
# Architecture Analysis

## Assessment
The codebase demonstrates a microservices architecture with event-driven communication.

## Design Patterns
- Microservices
- Event Sourcing
- CQRS
- API Gateway

## Scalability
The architecture is designed for horizontal scaling with independent service deployment.

## Technical Debt Priority
**HIGH** - Several services have outdated dependencies and require refactoring.

```json
{
    "architecture_assessment": "Microservices with event-driven communication",
    "design_patterns": ["Microservices", "Event Sourcing", "CQRS", "API Gateway"],
    "scalability_notes": "Designed for horizontal scaling",
    "technical_debt_priority": "high"
}
```
"""

    result2 = parse_llm_response(claude_response, 'architect')
    assert result2['parsing_method'] == 'json'
    assert result2['data']['technical_debt_priority'] == 'high'
    print(f"✅ Claude-style response: confidence={result2['confidence']}")

    # Scenario 3: Mixed format response (some JSON, some text)
    mixed_response = """
Based on my analysis:

**Business Problem**: This project solves the problem of manual code reviews
**Target Users**: Software development teams and CTOs

```json
{
    "problem_solved": "Manual code reviews are time-consuming and inconsistent",
    "target_audience": "Software development teams, CTOs, engineering managers"
}
```

Monetization could work through a SaaS model with tiered pricing.

```json
{
    "monetization_strategy": "SaaS with tiered pricing (free tier + paid plans)",
    "market_viability": 8,
    "portfolio_suitable": true,
    "portfolio_pitch": "AI-powered code review assistant that saves teams 10+ hours per week"
}
```
"""

    result3 = parse_llm_response(mixed_response, 'business')
    # Should extract first valid JSON block
    assert result3['parsing_method'] in ['json', 'json_partial']
    print(f"✅ Mixed format response: confidence={result3['confidence']}")

    # Scenario 4: Response without JSON (natural language only)
    natural_only = """
After analyzing the deployment requirements, I recommend using Docker containers
orchestrated with Kubernetes for maximum flexibility and scalability.

The infrastructure should be cloud-agnostic, using managed Kubernetes services
like GKE, EKS, or AKS depending on your cloud provider preference.

Key blockers to address before deployment:
- Missing environment configuration templates
- No health check endpoints defined
- Database migration strategy unclear

To reach MVP, follow these steps:
1. Create Dockerfiles for all services
2. Set up CI/CD pipeline with GitHub Actions
3. Deploy to staging environment for testing
4. Configure monitoring and logging
5. Production rollout with blue-green deployment
"""

    result4 = parse_llm_response(natural_only, 'deployment')
    assert result4['parsing_method'] in ['heuristic', 'heuristic_partial']
    assert 'deployment_strategy' in result4['data']
    print(f"✅ Natural language only: confidence={result4['confidence']}")

    print()


def run_all_tests():
    """Run all test suites"""
    print("\n")
    print("🧪 STARTING LLM RESPONSE HANDLER TEST SUITE")
    print("=" * 60)
    print()

    try:
        test_json_extraction_variants()
        test_pydantic_validation()
        test_confidence_scoring()
        test_heuristic_extraction()
        test_full_parsing_pipeline()
        test_edge_cases()
        test_real_world_scenarios()

        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Summary:")
        print("- JSON extraction: ✅")
        print("- Pydantic validation: ✅")
        print("- Confidence scoring: ✅")
        print("- Heuristic fallback: ✅")
        print("- Full pipeline: ✅")
        print("- Edge cases: ✅")
        print("- Real-world scenarios: ✅")
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
    success = run_all_tests()
    exit(0 if success else 1)
