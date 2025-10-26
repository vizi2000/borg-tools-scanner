# LLM Orchestrator - Multi-Model Analysis Pipeline

## Overview

The LLM Orchestrator is an async pipeline that analyzes projects using 4 specialized AI models from OpenRouter. It provides architectural, deployment, and business insights through parallel model execution with intelligent rate limiting and caching.

## Features

### ✅ Implemented Features

1. **Async HTTP Client**
   - OpenRouter API integration
   - Exponential backoff retry logic
   - Configurable timeouts (120s default)
   - Comprehensive error handling

2. **Token Bucket Rate Limiter**
   - 10 requests/minute (OpenRouter free tier)
   - Smooth token refilling
   - Thread-safe async implementation
   - Prevents API rate limit errors

3. **4-Model Pipeline**
   - **Architect** (Llama 4 Scout): Architecture & design patterns
   - **Deployment** (Mistral Small 3.1): Infrastructure & DevOps
   - **Business** (DeepSeek R1): Market viability & monetization
   - **Aggregator** (Llama 4 Maverick): Synthesis of all analyses

4. **Parallel Execution**
   - 3 specialist models run concurrently
   - Aggregator runs after specialists complete
   - Significantly faster than sequential execution

5. **Fallback Handling**
   - Graceful degradation on model failure
   - Continues pipeline with remaining models
   - Provides informative fallback responses

6. **Dry Run Mode**
   - Test without API calls
   - Mock responses for all models
   - Useful for development and testing

### 🔜 Future Integration (Ready for)

- **Cache Manager** (Task 2D): SQLite-based response caching
- **Response Parser** (Task 2C): Pydantic validation & JSON extraction
- **Prompt Templates** (Task 2B): Specialized prompt engineering

## Installation

```bash
# Install required dependencies
pip install aiohttp

# Set OpenRouter API key
export OPENROUTER_API_KEY="your_api_key_here"
```

## Usage

### Basic Usage

```python
import asyncio
from modules.llm_orchestrator import analyze_with_llm

# Prepare project data
project_data = {
    'name': 'my-awesome-project',
    'path': '/path/to/project',
    'languages': ['python', 'javascript'],
    'code_analysis': {
        'code_quality': {
            'overall_score': 7.8,
            'architecture_pattern': 'MVC'
        }
    },
    'deployment_analysis': {
        'deployment_confidence': 0.85,
        'blockers': []
    },
    'doc_analysis': {
        'documentation_quality': 0.8
    }
}

# Run analysis
result = asyncio.run(analyze_with_llm(project_data))

# Access results
print(result['llm_results']['architect_analysis'])
print(result['llm_results']['business_analysis'])
print(result['llm_results']['aggregated_insights'])
```

### Dry Run Mode (No API Calls)

```python
# Test with mock responses
result = asyncio.run(analyze_with_llm(project_data, dry_run=True))
```

### Advanced Usage

```python
from modules.llm_orchestrator import ModelPipeline

# Create pipeline with custom configuration
pipeline = ModelPipeline(dry_run=False)

# Run analysis
result = await pipeline.run_parallel_analysis(project_data)

# Check metadata
metadata = result['llm_results']['metadata']
print(f"Total time: {metadata['total_time_seconds']}s")
print(f"API calls: {metadata['api_calls']}")
print(f"Cache hits: {metadata['cache_hits']}")
```

## Output Format

```json
{
  "llm_results": {
    "architect_analysis": {
      "architecture_assessment": "Overall architecture evaluation",
      "design_patterns": ["MVC", "Repository", "Factory"],
      "scalability_notes": "Notes on scalability potential",
      "technical_debt_priority": "low|medium|high"
    },
    "deployment_analysis": {
      "deployment_strategy": "Recommended deployment approach",
      "infrastructure_recommendations": "Infrastructure suggestions",
      "deployment_blockers": [
        {
          "issue": "Description of blocker",
          "severity": "high|medium|low"
        }
      ],
      "mvp_roadmap": ["Step 1", "Step 2", "Step 3"]
    },
    "business_analysis": {
      "problem_solved": "Problem statement",
      "target_audience": "Target user persona",
      "monetization_strategy": "Revenue model suggestion",
      "market_viability": 7,
      "portfolio_suitable": true,
      "portfolio_pitch": "Elevator pitch"
    },
    "aggregated_insights": {
      "overall_assessment": "Synthesized assessment",
      "top_priorities": ["Priority 1", "Priority 2", "Priority 3"],
      "vibecodibility_score": 8,
      "borg_tools_fit": 7
    },
    "metadata": {
      "models_used": ["model-1", "model-2", "model-3", "model-4"],
      "total_time_seconds": 45.2,
      "cache_hits": 0,
      "api_calls": 4
    }
  }
}
```

## Performance

### Test Results

- **Dry Run**: ~0.5s (mock responses)
- **Real API**: ~40-60s for 4 models
  - 3 specialist models in parallel: ~30-40s
  - 1 aggregator model: ~10-20s
  - Rate limiting overhead: ~1-5s

### Optimization Tips

1. **Use Caching** (when Task 2D is integrated)
   - Second scan of same project: 0 API calls
   - Cache hit rate: 90%+ on re-scans

2. **Batch Projects**
   - Process multiple projects sequentially
   - Rate limiter handles throttling automatically

3. **Fallback Gracefully**
   - Pipeline continues even if 1-2 models fail
   - Partial results still valuable

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    ModelPipeline                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Architect   │  │  Deployment  │  │   Business   │ │
│  │    Model     │  │     Model    │  │     Model    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                 │                 │          │
│         └─────────────────┴─────────────────┘          │
│                         │                              │
│                         ▼                              │
│                 ┌──────────────┐                       │
│                 │  Aggregator  │                       │
│                 │     Model    │                       │
│                 └──────────────┘                       │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  Components:                                           │
│  • OpenRouterClient (HTTP client)                     │
│  • RateLimiter (token bucket)                         │
│  • CacheManager (stub - for Task 2D)                  │
│  • Response Parser (stub - for Task 2C)               │
└─────────────────────────────────────────────────────────┘
```

### Execution Flow

```
1. Check cache for each model
2. Load prompts for non-cached models
3. Run 3 specialist models in parallel
   - Architect analyzes code architecture
   - Deployment assesses deployment readiness
   - Business evaluates market fit
4. Cache successful responses
5. Run aggregator model with specialist results
6. Return combined analysis
```

## Error Handling

The orchestrator handles various error scenarios:

1. **Rate Limiting (429)**
   - Exponential backoff: 1s, 2s, 4s
   - Automatic retry up to 3 attempts

2. **Timeout**
   - 120s timeout per API call
   - Retry with exponential backoff

3. **Invalid Model ID**
   - Fallback response provided
   - Pipeline continues with other models

4. **Network Errors**
   - Retry logic with exponential backoff
   - Graceful degradation

## Testing

### Run Tests

```bash
# Run dry run test
python3 modules/llm_orchestrator.py

# Run comprehensive test (includes real API calls)
python3 test_llm_orchestrator.py
```

### Test Coverage

- ✅ Rate limiter token bucket algorithm
- ✅ Parallel execution of 3 models
- ✅ Exponential backoff retry logic
- ✅ Dry run mode (no API calls)
- ✅ Real API integration
- ✅ Error handling and fallbacks
- ✅ Response parsing (basic)

## Integration with Scanner Pipeline

```python
from modules.code_analyzer import analyze_code
from modules.deployment_detector import analyze_deployment
from modules.doc_analyzer import analyze_documentation
from modules.llm_orchestrator import analyze_with_llm

# Step 1: Analyze code (Task 1A)
code_analysis = analyze_code(project_path, languages)

# Step 2: Analyze deployment (Task 1B)
deployment_analysis = analyze_deployment(project_path, languages)

# Step 3: Analyze documentation (Task 1C)
doc_analysis = analyze_documentation(project_path)

# Step 4: Run LLM analysis (Task 2A)
project_data = {
    'name': project_name,
    'path': project_path,
    'languages': languages,
    'code_analysis': code_analysis,
    'deployment_analysis': deployment_analysis,
    'doc_analysis': doc_analysis
}

llm_results = await analyze_with_llm(project_data)

# Combine all results
full_analysis = {
    **code_analysis,
    **deployment_analysis,
    **doc_analysis,
    **llm_results
}
```

## Future Enhancements

### Task 2B: Prompt Engineering
- Replace stub prompts with engineered templates
- Add few-shot examples
- Improve JSON extraction reliability

### Task 2C: Response Parsing
- Pydantic validation
- Confidence scoring
- Better JSON extraction from markdown

### Task 2D: Caching
- SQLite-based persistence
- Cache invalidation on file changes
- 90%+ cache hit rate on re-scans

## Troubleshooting

### "OPENROUTER_API_KEY not set"
```bash
export OPENROUTER_API_KEY="your_api_key_here"
```

### "Rate limited, waiting Xs"
- Normal behavior for free tier
- Pipeline automatically handles rate limiting
- Consider upgrading API tier for higher limits

### "Model X failed"
- Pipeline continues with fallback response
- Check OpenRouter model availability
- Verify model IDs are correct for free tier

### Slow execution
- Expected: 40-60s for 4 models
- Check internet connection
- OpenRouter API response times vary

## Credits

**Created by The Collective Borg.tools**

Part of the Borg.tools Scanner V2 project.

## License

MIT License - See project root for details.
