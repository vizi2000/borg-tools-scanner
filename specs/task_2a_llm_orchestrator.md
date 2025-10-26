# Task 2A: LLM Model Orchestrator

## Objective
Multi-model async pipeline z rate limiting dla OpenRouter free tier.

## Priority: 🔴 CRITICAL | Time: 5h | Dependencies: Task 1A, 1B, 1C

## Output
```python
# llm_orchestrator.py
class ModelPipeline:
    async def run_parallel_analysis(project_data: Dict) -> Dict:
        # Concurrent calls to 4 models
        # Returns aggregated analysis
```

## Key Implementation
- `asyncio.gather()` dla parallel requests
- Rate limit: 10 req/min (free tier)
- Exponential backoff retry
- Cache responses (expensive!)
- Models:
  - architect: meta-llama/llama-4-scout:free
  - deployment: mistralai/mistral-small-3.1:free
  - business: deepseek/deepseek-r1:free
  - aggregator: meta-llama/llama-4-maverick:free

## Test: Verify 4 concurrent requests complete in <3min
