# Task 2C: Response Parsers & Validators

## Objective
Extract JSON from LLM markdown, validate schemas.

## Priority: 🟡 HIGH | Time: 3h | Dependencies: Task 2B

## Output
```python
# llm_response_handler.py
def parse_llm_response(content: str, schema: Type[BaseModel]) -> Dict:
    # Extract JSON from ```json blocks or markdown
    # Validate with pydantic
    # Return parsed + confidence score
```

## Key Features
- Regex extraction: ```json...```
- Pydantic models per response type
- Confidence scoring (field completeness)
- Fallback to heuristics if parse fails

## Test: Parse 100 sample responses with 95% success
