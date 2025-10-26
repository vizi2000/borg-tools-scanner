# Task 2B: Prompt Engineering (4 Models)

## Objective
Specialized prompts per model role.

## Priority: 🟡 HIGH | Time: 4h | Dependencies: None (parallel z 2A)

## Outputs
- `prompts/architect_prompt.txt` - system + user templates
- `prompts/deployment_prompt.txt`
- `prompts/business_prompt.txt`
- `prompts/aggregator_prompt.txt`

## Key Sections per Prompt
1. ROLE definition
2. INPUT format (JSON schema)
3. OUTPUT format (strict JSON schema)
4. EXAMPLES (few-shot)
5. CONSTRAINTS (no hallucinations, specific fields)

## Test: LLM returns valid JSON matching schema (90% success rate)
