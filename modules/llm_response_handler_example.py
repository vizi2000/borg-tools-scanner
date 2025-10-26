"""
Usage Examples for LLM Response Handler

Demonstrates how to use the response parser in real-world scenarios.

Created by The Collective Borg.tools
"""

from llm_response_handler import (
    parse_llm_response,
    parse_batch_responses,
    parse_aggregated_response,
    get_response_schema,
    validate_response_data
)
import json


def example_1_basic_parsing():
    """Example 1: Basic JSON response parsing"""
    print("=" * 60)
    print("EXAMPLE 1: Basic JSON Response Parsing")
    print("=" * 60)

    # Simulate an LLM response
    llm_output = """
Here's my architecture analysis:

```json
{
    "architecture_assessment": "The codebase follows a well-structured hexagonal architecture with clear separation of concerns. Domain logic is isolated from infrastructure concerns.",
    "design_patterns": ["Hexagonal Architecture", "Repository Pattern", "Dependency Injection", "Factory Pattern"],
    "scalability_notes": "The architecture supports horizontal scaling through stateless services. Consider implementing event sourcing for better auditability.",
    "technical_debt_priority": "medium"
}
```

This structure will serve the project well as it grows.
"""

    # Parse the response
    result = parse_llm_response(llm_output, 'architect')

    print(f"Parsing Method: {result['parsing_method']}")
    print(f"Confidence Score: {result['confidence']}")
    print(f"Validation Error: {result['validation_error']}")
    print(f"\nParsed Data:")
    print(json.dumps(result['data'], indent=2))
    print()


def example_2_heuristic_fallback():
    """Example 2: Heuristic extraction when JSON is missing"""
    print("=" * 60)
    print("EXAMPLE 2: Heuristic Fallback")
    print("=" * 60)

    # Natural language response without JSON
    llm_output = """
After analyzing the business aspects, here's what I found:

Problem Solved: This tool automates the tedious process of code quality analysis,
saving development teams hours of manual review time.

Target Audience: Software development teams, CTOs, and engineering managers at
mid-sized to large companies who want to maintain code quality standards.

Monetization: A SaaS model with tiered pricing would work well:
- Free tier for open source projects
- Professional tier at $99/month for teams up to 10 developers
- Enterprise tier with custom pricing

Market Viability: 8/10 - Strong demand for automated code analysis tools

Portfolio Suitable: yes - This demonstrates technical depth and addresses a real pain point
"""

    # Parse with heuristic fallback enabled (default)
    result = parse_llm_response(llm_output, 'business')

    print(f"Parsing Method: {result['parsing_method']}")
    print(f"Confidence Score: {result['confidence']}")
    print(f"\nExtracted Data:")
    print(json.dumps(result['data'], indent=2))
    print()


def example_3_batch_processing():
    """Example 3: Process multiple responses in batch"""
    print("=" * 60)
    print("EXAMPLE 3: Batch Processing")
    print("=" * 60)

    # Multiple LLM responses
    responses = {
        'architect': """```json
{
    "architecture_assessment": "Microservices with event-driven communication",
    "design_patterns": ["Microservices", "Event Sourcing", "CQRS"],
    "technical_debt_priority": "high"
}
```""",
        'deployment': """
Deployment Strategy: Docker containers orchestrated with Kubernetes

Infrastructure: Use managed Kubernetes (GKE or EKS) with automatic scaling

MVP Roadmap:
1. Create Dockerfiles
2. Setup CI/CD with GitHub Actions
3. Deploy to staging
4. Production rollout
""",
        'business': """```json
{
    "problem_solved": "Automates deployment pipeline",
    "target_audience": "DevOps teams",
    "market_viability": 7,
    "portfolio_suitable": true
}
```"""
    }

    # Parse all at once
    results = parse_batch_responses(responses)

    print(f"Processed {len(results)} responses:\n")
    for response_type, result in results.items():
        print(f"{response_type.upper()}:")
        print(f"  Method: {result['parsing_method']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Has Data: {bool(result['data'])}")
        print()


def example_4_validation():
    """Example 4: Validate data against schema"""
    print("=" * 60)
    print("EXAMPLE 4: Schema Validation")
    print("=" * 60)

    # Valid data
    valid_data = {
        "overall_assessment": "Strong technical foundation with minor issues",
        "top_priorities": ["Fix security vulns", "Add tests", "Update docs"],
        "vibecodibility_score": 8,
        "borg_tools_fit": 7
    }

    is_valid, error = validate_response_data(valid_data, 'aggregator')
    print(f"Valid data check: {is_valid}")
    if error:
        print(f"Error: {error}")

    # Invalid data (score out of range)
    invalid_data = {
        "overall_assessment": "Test",
        "top_priorities": [],
        "vibecodibility_score": 15,  # Should be 0-10
        "borg_tools_fit": 7
    }

    is_valid, error = validate_response_data(invalid_data, 'aggregator')
    print(f"\nInvalid data check: {is_valid}")
    if error:
        print(f"Error: {error[:100]}...")  # Truncate error message

    print()


def example_5_low_confidence_handling():
    """Example 5: Handle low confidence results"""
    print("=" * 60)
    print("EXAMPLE 5: Low Confidence Handling")
    print("=" * 60)

    # Ambiguous or incomplete response
    poor_response = """
Some analysis here but not much structure or detail.
Maybe it's using Docker? Not sure about the architecture.
"""

    result = parse_llm_response(poor_response, 'architect')

    print(f"Confidence Score: {result['confidence']}")
    print(f"Parsing Method: {result['parsing_method']}")

    # Decision logic based on confidence
    if result['confidence'] > 0.8:
        print("\n✅ High confidence - use the data directly")
    elif result['confidence'] > 0.5:
        print("\n⚠️  Medium confidence - use with caution, may need human review")
    else:
        print("\n❌ Low confidence - discard or request clarification from LLM")

    print()


def example_6_integration_pattern():
    """Example 6: Integration pattern with LLM orchestrator"""
    print("=" * 60)
    print("EXAMPLE 6: Integration Pattern")
    print("=" * 60)

    print("Typical integration flow:")
    print("""
# In your LLM orchestrator:

async def call_architect_model(project_data):
    # 1. Generate prompt
    prompt = prepare_architect_prompt(project_data)

    # 2. Call LLM API
    raw_response = await openrouter_client.call(
        model='meta-llama/llama-4-scout:free',
        prompt=prompt
    )

    # 3. Parse response
    from modules.llm_response_handler import parse_llm_response

    parsed = parse_llm_response(
        raw_response['choices'][0]['message']['content'],
        'architect'
    )

    # 4. Check confidence
    if parsed['confidence'] < 0.5:
        logger.warning(f"Low confidence: {parsed['confidence']}")
        # Maybe retry with different prompt or use fallback

    # 5. Return structured data
    return parsed['data']


# Usage in pipeline:
results = await asyncio.gather(
    call_architect_model(project_data),
    call_deployment_model(project_data),
    call_business_model(project_data)
)

# Results are now validated and structured!
""")
    print()


def example_7_confidence_thresholds():
    """Example 7: Using confidence scores for quality control"""
    print("=" * 60)
    print("EXAMPLE 7: Quality Control with Confidence Scores")
    print("=" * 60)

    test_responses = [
        ("Complete JSON", """```json
{
    "architecture_assessment": "Complete analysis",
    "design_patterns": ["MVC", "Factory"],
    "scalability_notes": "Detailed notes",
    "technical_debt_priority": "low"
}
```"""),
        ("Partial heuristic", """
Architecture Assessment: Brief analysis
Technical debt priority: medium
"""),
        ("Empty response", "No useful information here.")
    ]

    print("Confidence-based decision making:\n")

    for name, response in test_responses:
        result = parse_llm_response(response, 'architect')
        confidence = result['confidence']

        print(f"{name}:")
        print(f"  Confidence: {confidence:.2f}")

        # Decision logic
        if confidence >= 0.8:
            action = "✅ Accept - High quality"
        elif confidence >= 0.6:
            action = "⚠️  Review - Medium quality"
        elif confidence >= 0.4:
            action = "🔄 Retry - Low quality"
        else:
            action = "❌ Reject - Failed to parse"

        print(f"  Action: {action}\n")


def run_all_examples():
    """Run all usage examples"""
    print("\n")
    print("🚀 LLM RESPONSE HANDLER - USAGE EXAMPLES")
    print("=" * 60)
    print()

    example_1_basic_parsing()
    example_2_heuristic_fallback()
    example_3_batch_processing()
    example_4_validation()
    example_5_low_confidence_handling()
    example_6_integration_pattern()
    example_7_confidence_thresholds()

    print("=" * 60)
    print("✅ All examples complete!")
    print("=" * 60)
    print()


if __name__ == '__main__':
    run_all_examples()
