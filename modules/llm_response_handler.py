"""
LLM Response Parser & Validator - Borg Tools Scanner v2.0

This module handles parsing and validation of LLM responses from multiple models:
- Extracts JSON from markdown code blocks
- Validates responses with Pydantic schemas
- Computes confidence scores based on field completeness
- Provides fallback heuristics for failed parses

Created by The Collective Borg.tools
"""

import re
import json
from typing import Dict, Any, List, Optional, Type, Union
from pydantic import BaseModel, Field, ValidationError, field_validator
from enum import Enum


# ============================================================================
# PYDANTIC MODELS FOR EACH RESPONSE TYPE
# ============================================================================

class ArchitectResponse(BaseModel):
    """Response schema for Architect model analysis"""
    architecture_assessment: str = Field(
        ...,
        description="Overall architecture quality and design assessment"
    )
    design_patterns: List[str] = Field(
        default_factory=list,
        description="List of detected design patterns"
    )
    scalability_notes: str = Field(
        default="",
        description="Notes on scalability and performance considerations"
    )
    technical_debt_priority: str = Field(
        default="medium",
        description="Priority level for addressing technical debt (low, medium, high, critical)"
    )

    @field_validator('technical_debt_priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Ensure priority is one of the valid values"""
        valid = ['low', 'medium', 'high', 'critical']
        v_lower = v.lower()
        if v_lower not in valid:
            return 'medium'  # Default fallback
        return v_lower


class DeploymentBlocker(BaseModel):
    """Individual deployment blocker"""
    severity: str = Field(..., description="Blocker severity: low, medium, high, critical")
    issue: str = Field(..., description="Description of the blocker")
    solution: str = Field(default="", description="Suggested solution")


class DeploymentResponse(BaseModel):
    """Response schema for Deployment model analysis"""
    deployment_strategy: str = Field(
        ...,
        description="Recommended deployment strategy (e.g., Docker, Kubernetes, serverless)"
    )
    infrastructure_recommendations: str = Field(
        default="",
        description="Infrastructure setup recommendations"
    )
    deployment_blockers: List[DeploymentBlocker] = Field(
        default_factory=list,
        description="List of issues blocking deployment"
    )
    mvp_roadmap: List[str] = Field(
        default_factory=list,
        description="Steps to reach MVP deployment"
    )


class BusinessResponse(BaseModel):
    """Response schema for Business model analysis"""
    problem_solved: str = Field(
        ...,
        description="What business problem this project solves"
    )
    target_audience: str = Field(
        ...,
        description="Who the target users/customers are"
    )
    monetization_strategy: str = Field(
        default="",
        description="Potential monetization approaches"
    )
    market_viability: int = Field(
        default=5,
        ge=0,
        le=10,
        description="Market viability score 0-10"
    )
    portfolio_suitable: bool = Field(
        default=False,
        description="Whether suitable for portfolio inclusion"
    )
    portfolio_pitch: str = Field(
        default="",
        description="Elevator pitch for portfolio"
    )


class AggregatorResponse(BaseModel):
    """Response schema for Aggregator model (meta-analysis)"""
    overall_assessment: str = Field(
        ...,
        description="High-level summary of all analyses"
    )
    top_priorities: List[str] = Field(
        default_factory=list,
        description="Top 3-5 priority actions"
    )
    vibecodibility_score: int = Field(
        default=5,
        ge=0,
        le=10,
        description="How codeable/viable is this project (0-10)"
    )
    borg_tools_fit: int = Field(
        default=5,
        ge=0,
        le=10,
        description="How well it fits Borg.tools ecosystem (0-10)"
    )


# Response type mapping
RESPONSE_MODELS = {
    'architect': ArchitectResponse,
    'deployment': DeploymentResponse,
    'business': BusinessResponse,
    'aggregator': AggregatorResponse
}


# ============================================================================
# JSON EXTRACTION FROM MARKDOWN
# ============================================================================

def extract_json_from_markdown(content: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from markdown code blocks or raw JSON.

    Supports multiple formats:
    - ```json {...} ```
    - ```{...}```
    - Raw JSON {...}

    Args:
        content: Raw LLM response content

    Returns:
        Parsed JSON dict or None if extraction fails
    """
    # Pattern 1: JSON code block with language tag
    json_block_pattern = r'```json\s*\n(.*?)\n```'
    matches = re.findall(json_block_pattern, content, re.DOTALL | re.IGNORECASE)

    if matches:
        # Try each match (in case there are multiple blocks)
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

    # Pattern 2: Generic code block
    generic_block_pattern = r'```\s*\n(\{.*?\})\n```'
    matches = re.findall(generic_block_pattern, content, re.DOTALL)

    if matches:
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

    # Pattern 3: Raw JSON (find first complete JSON object)
    # Look for {...} pattern that spans potentially multiple lines
    json_object_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
    matches = re.findall(json_object_pattern, content, re.DOTALL)

    if matches:
        # Try the largest match first (most likely to be complete)
        for match in sorted(matches, key=len, reverse=True):
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

    # Pattern 4: Try to parse entire content as JSON
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass

    return None


def extract_json_array_from_markdown(content: str) -> Optional[List[Dict[str, Any]]]:
    """
    Extract JSON array from markdown (for lists like deployment_blockers).

    Args:
        content: Raw LLM response content

    Returns:
        Parsed JSON array or None
    """
    # Pattern for JSON array in code blocks
    array_pattern = r'```json\s*\n(\[.*?\])\n```'
    matches = re.findall(array_pattern, content, re.DOTALL | re.IGNORECASE)

    if matches:
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

    # Try raw array pattern
    array_pattern = r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'
    matches = re.findall(array_pattern, content, re.DOTALL)

    if matches:
        for match in sorted(matches, key=len, reverse=True):
            try:
                parsed = json.loads(match.strip())
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                continue

    return None


# ============================================================================
# CONFIDENCE SCORING
# ============================================================================

def compute_confidence_score(data: Dict[str, Any], model_class: Type[BaseModel]) -> float:
    """
    Compute confidence score based on field completeness.

    Score calculation:
    - Required fields present: +0.4
    - Optional fields populated: +0.6 (weighted by field count)
    - Valid types/formats: bonus

    Args:
        data: Parsed data dictionary
        model_class: Pydantic model class to validate against

    Returns:
        Confidence score between 0.0 and 1.0
    """
    if not data:
        return 0.0

    # Get model schema
    schema_fields = model_class.model_fields
    required_fields = [
        name for name, field in schema_fields.items()
        if field.is_required()
    ]
    optional_fields = [
        name for name, field in schema_fields.items()
        if not field.is_required()
    ]

    # Check required fields
    required_present = sum(1 for field in required_fields if field in data and data[field])
    required_score = (required_present / len(required_fields)) * 0.4 if required_fields else 0.4

    # Check optional fields
    optional_present = sum(
        1 for field in optional_fields
        if field in data and data[field] is not None and data[field] != ""
    )
    optional_score = (optional_present / len(optional_fields)) * 0.6 if optional_fields else 0.6

    base_score = required_score + optional_score

    # Bonus for list fields that are non-empty
    list_bonus = 0.0
    for field_name, field_info in schema_fields.items():
        if field_name in data:
            value = data[field_name]
            # Check if it's a list type and non-empty
            if isinstance(value, list) and len(value) > 0:
                list_bonus += 0.05

    final_score = min(1.0, base_score + list_bonus)
    return round(final_score, 2)


# ============================================================================
# FALLBACK HEURISTICS
# ============================================================================

def extract_via_heuristics(content: str, response_type: str) -> Dict[str, Any]:
    """
    Fallback heuristic extraction when JSON parsing fails.

    Uses regex patterns to extract key information from natural language.

    Args:
        content: Raw LLM response content
        response_type: Type of response (architect, deployment, business, aggregator)

    Returns:
        Best-effort extracted data
    """
    result = {}

    if response_type == 'architect':
        # Extract architecture assessment
        arch_patterns = [
            r'architecture\s+(?:assessment|analysis)?:?\s*([^\n]+)',
            r'overall\s+architecture:?\s*([^\n]+)',
            r'(?:the\s+)?architecture\s+(?:is|appears|seems):?\s*([^\n]+)'
        ]
        for pattern in arch_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                result['architecture_assessment'] = match.group(1).strip()
                break

        # Extract design patterns
        patterns_match = re.search(
            r'(?:design\s+)?patterns?:?\s*([^\n]+(?:\n-[^\n]+)*)',
            content,
            re.IGNORECASE
        )
        if patterns_match:
            patterns_text = patterns_match.group(1)
            # Split by comma or newline with dash
            patterns = re.split(r',|\n-', patterns_text)
            result['design_patterns'] = [p.strip().strip('-').strip() for p in patterns if p.strip()]

        # Extract technical debt priority
        priority_match = re.search(
            r'(?:technical\s+debt|debt)\s+priority:?\s*(low|medium|high|critical)',
            content,
            re.IGNORECASE
        )
        if priority_match:
            result['technical_debt_priority'] = priority_match.group(1).lower()

        # Extract scalability notes
        scalability_match = re.search(
            r'scalability[:\s]+([^\n]+(?:\n(?!#)[^\n]+)*)',
            content,
            re.IGNORECASE
        )
        if scalability_match:
            result['scalability_notes'] = scalability_match.group(1).strip()

    elif response_type == 'deployment':
        # Extract deployment strategy
        strategy_patterns = [
            r'deployment\s+strategy:?\s*([^\n]+)',
            r'recommended\s+deployment:?\s*([^\n]+)',
            r'deploy\s+(?:using|via|with):?\s*([^\n]+)',
            r'recommend\s+(?:using|deploying with):?\s*([^\n]+)',
            r'(?:use|using)\s+(docker[^\n]+)',
            r'(?:orchestrated?\s+with|using)\s+(kubernetes[^\n]+)'
        ]
        for pattern in strategy_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                result['deployment_strategy'] = match.group(1).strip()
                break

        # Extract infrastructure recommendations
        infra_match = re.search(
            r'infrastructure[:\s]+([^\n]+(?:\n(?!#)[^\n]+)*)',
            content,
            re.IGNORECASE
        )
        if infra_match:
            result['infrastructure_recommendations'] = infra_match.group(1).strip()

        # Extract MVP roadmap items
        roadmap_match = re.search(
            r'(?:mvp\s+)?roadmap:?\s*([^\n]+(?:\n-[^\n]+)*)',
            content,
            re.IGNORECASE
        )
        if roadmap_match:
            roadmap_text = roadmap_match.group(1)
            items = re.split(r'\n-|\d+\.', roadmap_text)
            result['mvp_roadmap'] = [item.strip() for item in items if item.strip()]

    elif response_type == 'business':
        # Extract problem solved
        problem_match = re.search(
            r'problem\s+solved:?\s*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if problem_match:
            result['problem_solved'] = problem_match.group(1).strip()

        # Extract target audience
        audience_match = re.search(
            r'target\s+audience:?\s*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if audience_match:
            result['target_audience'] = audience_match.group(1).strip()

        # Extract monetization strategy
        monetization_match = re.search(
            r'monetization:?\s*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if monetization_match:
            result['monetization_strategy'] = monetization_match.group(1).strip()

        # Extract viability score
        viability_match = re.search(
            r'(?:market\s+)?viability:?\s*(\d+)(?:/10)?',
            content,
            re.IGNORECASE
        )
        if viability_match:
            result['market_viability'] = int(viability_match.group(1))

        # Extract portfolio suitability
        portfolio_match = re.search(
            r'portfolio\s+suitable:?\s*(yes|no|true|false)',
            content,
            re.IGNORECASE
        )
        if portfolio_match:
            result['portfolio_suitable'] = portfolio_match.group(1).lower() in ['yes', 'true']

    elif response_type == 'aggregator':
        # Extract overall assessment
        assessment_match = re.search(
            r'overall\s+assessment:?\s*([^\n]+(?:\n(?!#)[^\n]+)*)',
            content,
            re.IGNORECASE
        )
        if assessment_match:
            result['overall_assessment'] = assessment_match.group(1).strip()

        # Extract top priorities
        priorities_match = re.search(
            r'(?:top\s+)?priorities:?\s*([^\n]+(?:\n-[^\n]+)*)',
            content,
            re.IGNORECASE
        )
        if priorities_match:
            priorities_text = priorities_match.group(1)
            items = re.split(r'\n-|\d+\.', priorities_text)
            result['top_priorities'] = [item.strip() for item in items if item.strip()]

        # Extract scores
        vibe_match = re.search(
            r'vibecodibility:?\s*(\d+)(?:/10)?',
            content,
            re.IGNORECASE
        )
        if vibe_match:
            result['vibecodibility_score'] = int(vibe_match.group(1))

        borg_match = re.search(
            r'borg[.\s]+tools[.\s]+fit:?\s*(\d+)(?:/10)?',
            content,
            re.IGNORECASE
        )
        if borg_match:
            result['borg_tools_fit'] = int(borg_match.group(1))

    return result


# ============================================================================
# MAIN PARSING FUNCTION
# ============================================================================

def parse_llm_response(
    content: str,
    response_type: str,
    fallback_to_heuristics: bool = True
) -> Dict[str, Any]:
    """
    Main entry point for parsing LLM responses.

    Process:
    1. Extract JSON from markdown
    2. Validate with appropriate Pydantic model
    3. Compute confidence score
    4. If parsing fails and fallback enabled, use heuristics

    Args:
        content: Raw LLM response content
        response_type: Type of response (architect, deployment, business, aggregator)
        fallback_to_heuristics: Whether to use heuristic extraction on failure

    Returns:
        Dictionary with parsed data, validation status, and confidence score:
        {
            'data': {...},
            'confidence': 0.0-1.0,
            'validation_error': str | None,
            'parsing_method': 'json' | 'heuristic' | 'fallback',
            'raw_content': str (first 200 chars)
        }
    """
    result = {
        'data': {},
        'confidence': 0.0,
        'validation_error': None,
        'parsing_method': None,
        'raw_content': content[:200] if content else ""
    }

    # Validate response_type
    if response_type not in RESPONSE_MODELS:
        result['validation_error'] = f"Unknown response type: {response_type}"
        return result

    model_class = RESPONSE_MODELS[response_type]

    # Step 1: Try JSON extraction
    extracted_json = extract_json_from_markdown(content)

    if extracted_json:
        try:
            # Validate with Pydantic
            validated_model = model_class(**extracted_json)
            result['data'] = validated_model.model_dump()
            result['confidence'] = compute_confidence_score(result['data'], model_class)
            result['parsing_method'] = 'json'
            return result
        except ValidationError as e:
            # JSON found but invalid schema
            result['validation_error'] = str(e)
            # Try to use partial data
            result['data'] = extracted_json
            result['confidence'] = compute_confidence_score(extracted_json, model_class) * 0.5
            result['parsing_method'] = 'json_partial'

    # Step 2: Fallback to heuristics if enabled
    if fallback_to_heuristics:
        heuristic_data = extract_via_heuristics(content, response_type)

        if heuristic_data:
            try:
                # Try to validate heuristic extraction
                validated_model = model_class(**heuristic_data)
                result['data'] = validated_model.model_dump()
                result['confidence'] = compute_confidence_score(result['data'], model_class) * 0.7
                result['parsing_method'] = 'heuristic'
                return result
            except ValidationError:
                # Use partial heuristic data
                result['data'] = heuristic_data
                result['confidence'] = compute_confidence_score(heuristic_data, model_class) * 0.4
                result['parsing_method'] = 'heuristic_partial'
                return result

    # Step 3: Complete fallback - return minimal valid structure
    try:
        minimal_model = model_class()
        result['data'] = minimal_model.model_dump()
        result['confidence'] = 0.1
        result['parsing_method'] = 'fallback'
    except Exception:
        result['data'] = {}
        result['confidence'] = 0.0
        result['parsing_method'] = 'failed'

    return result


def parse_aggregated_response(content: str) -> Dict[str, Any]:
    """
    Convenience wrapper for parsing aggregator responses.

    Args:
        content: Raw aggregator LLM response

    Returns:
        Parsed aggregator response
    """
    return parse_llm_response(content, 'aggregator')


# ============================================================================
# BATCH PARSING
# ============================================================================

def parse_batch_responses(responses: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    """
    Parse multiple LLM responses at once.

    Args:
        responses: Dict mapping response_type -> content

    Returns:
        Dict mapping response_type -> parsed_result
    """
    results = {}

    for response_type, content in responses.items():
        if response_type in RESPONSE_MODELS:
            results[response_type] = parse_llm_response(content, response_type)
        else:
            results[response_type] = {
                'data': {},
                'confidence': 0.0,
                'validation_error': f'Unknown response type: {response_type}',
                'parsing_method': 'failed'
            }

    return results


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_response_schema(response_type: str) -> Optional[Type[BaseModel]]:
    """
    Get the Pydantic schema for a response type.

    Args:
        response_type: Type of response

    Returns:
        Pydantic model class or None
    """
    return RESPONSE_MODELS.get(response_type)


def validate_response_data(data: Dict[str, Any], response_type: str) -> tuple[bool, Optional[str]]:
    """
    Validate response data against schema without parsing.

    Args:
        data: Data dictionary to validate
        response_type: Type of response

    Returns:
        Tuple of (is_valid, error_message)
    """
    if response_type not in RESPONSE_MODELS:
        return False, f"Unknown response type: {response_type}"

    model_class = RESPONSE_MODELS[response_type]

    try:
        model_class(**data)
        return True, None
    except ValidationError as e:
        return False, str(e)


# ============================================================================
# ENTRY POINT FOR TESTING
# ============================================================================

if __name__ == '__main__':
    # Simple test cases
    print("Testing LLM Response Handler...\n")

    # Test 1: JSON extraction
    test_json = '''
    Here's my analysis:

    ```json
    {
        "architecture_assessment": "Well-structured MVC pattern",
        "design_patterns": ["MVC", "Factory", "Singleton"],
        "scalability_notes": "Can handle moderate load",
        "technical_debt_priority": "medium"
    }
    ```
    '''

    result = parse_llm_response(test_json, 'architect')
    print(f"Test 1 (JSON): confidence={result['confidence']}, method={result['parsing_method']}")
    print(f"Data: {result['data']}\n")

    # Test 2: Heuristic extraction
    test_heuristic = '''
    Architecture Assessment: The codebase follows a microservices pattern

    Design Patterns:
    - Repository pattern
    - CQRS
    - Event sourcing

    Technical debt priority: high

    Scalability: Horizontally scalable with proper load balancing
    '''

    result2 = parse_llm_response(test_heuristic, 'architect')
    print(f"Test 2 (Heuristic): confidence={result2['confidence']}, method={result2['parsing_method']}")
    print(f"Data: {result2['data']}\n")

    # Test 3: Batch parsing
    batch = {
        'architect': test_json,
        'business': '''
        Problem Solved: Helps developers analyze code quality
        Target Audience: Software developers and tech leads
        Market Viability: 8/10
        Portfolio Suitable: yes
        '''
    }

    batch_results = parse_batch_responses(batch)
    print(f"Test 3 (Batch):")
    for resp_type, result in batch_results.items():
        print(f"  {resp_type}: confidence={result['confidence']}, method={result['parsing_method']}")

    print("\n✅ All tests complete!")
