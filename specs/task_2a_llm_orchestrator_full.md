# Task 2A: LLM Model Orchestrator - FULL SPECIFICATION

## Objective
Create async multi-model LLM pipeline with rate limiting, caching, and fallback handling for OpenRouter free tier models.

## Priority
🔴 **CRITICAL** | Time: 5h | Dependencies: Task 1A, 1B, 1C (needs their output formats)

## Context
OpenRouter free tier provides access to:
- `meta-llama/llama-4-scout:free` (512K context)
- `mistralai/mistral-small-3.1:free` (24B params)
- `deepseek/deepseek-r1:free` (reasoning model)
- `meta-llama/llama-4-maverick:free` (400B params)

Rate limits: ~10 req/min free tier

## Input Format
```python
{
    "project": {
        "name": "project-name",
        "path": "/path/to/project",
        "languages": ["python", "nodejs"],
        "code_analysis": {...},  # from Task 1A
        "deployment_analysis": {...},  # from Task 1B
        "doc_analysis": {...}  # from Task 1C
    }
}
```

## Output Format
```python
{
    "llm_results": {
        "architect_analysis": {
            "architecture_assessment": str,
            "design_patterns": List[str],
            "scalability_notes": str,
            "technical_debt_priority": str
        },
        "deployment_analysis": {
            "deployment_strategy": str,
            "infrastructure_recommendations": str,
            "deployment_blockers": List[Dict],
            "mvp_roadmap": List[str]
        },
        "business_analysis": {
            "problem_solved": str,
            "target_audience": str,
            "monetization_strategy": str,
            "market_viability": int,  # 0-10
            "portfolio_suitable": bool,
            "portfolio_pitch": str
        },
        "aggregated_insights": {
            "overall_assessment": str,
            "top_priorities": List[str],
            "vibecodibility_score": int,  # 0-10
            "borg_tools_fit": int  # 0-10
        },
        "metadata": {
            "models_used": List[str],
            "total_time_seconds": float,
            "cache_hits": int,
            "api_calls": int
        }
    }
}
```

## Implementation Details

### 1. Async HTTP Client
```python
import asyncio
import aiohttp
import os
from typing import Dict, Any, List
import time

class OpenRouterClient:
    """Async HTTP client for OpenRouter API"""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")

        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://borg.tools',
            'X-Title': 'Borg Tools Scanner V2'
        }

    async def call_model(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.3,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make async API call with exponential backoff retry
        """
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.BASE_URL}/chat/completions",
                        json=payload,
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:  # Rate limit
                            wait = 2 ** attempt  # Exponential backoff
                            print(f"  ⏳ Rate limited, waiting {wait}s...")
                            await asyncio.sleep(wait)
                        else:
                            error_text = await response.text()
                            raise Exception(f"API error {response.status}: {error_text}")
            except asyncio.TimeoutError:
                print(f"  ⏱️  Timeout on attempt {attempt+1}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise Exception(f"Failed after {max_retries} attempts")
```

### 2. Rate Limiter
```python
class RateLimiter:
    """Token bucket rate limiter for API calls"""

    def __init__(self, calls_per_minute: int = 10):
        self.calls_per_minute = calls_per_minute
        self.tokens = calls_per_minute
        self.last_refill = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Wait until token available"""
        async with self.lock:
            # Refill tokens based on time passed
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(
                self.calls_per_minute,
                self.tokens + (elapsed / 60.0) * self.calls_per_minute
            )
            self.last_refill = now

            # Wait if no tokens
            while self.tokens < 1:
                wait_time = (1 - self.tokens) / self.calls_per_minute * 60
                print(f"  ⏳ Rate limit: waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                now = time.time()
                elapsed = now - self.last_refill
                self.tokens += (elapsed / 60.0) * self.calls_per_minute
                self.last_refill = now

            self.tokens -= 1
```

### 3. Model Pipeline Orchestrator
```python
class ModelPipeline:
    """Orchestrates parallel calls to 4 specialized models"""

    MODELS = {
        'architect': 'meta-llama/llama-4-scout:free',
        'deployment': 'mistralai/mistral-small-3.1:free',
        'business': 'deepseek/deepseek-r1:free',
        'aggregator': 'meta-llama/llama-4-maverick:free'
    }

    def __init__(self):
        self.client = OpenRouterClient()
        self.rate_limiter = RateLimiter(calls_per_minute=10)
        self.cache_manager = CacheManager()  # from Task 2D

    async def run_parallel_analysis(self, project_data: Dict) -> Dict:
        """
        Main entry point: runs 4 models in parallel
        """
        print(f"🤖 [LLM PIPELINE] Analyzing {project_data['name']}...")
        start_time = time.time()
        cache_hits = 0
        api_calls = 0

        # Check cache first
        cached_results = {}
        for role in ['architect', 'deployment', 'business']:
            cached = self.cache_manager.get_cached(
                project_data['path'],
                self.MODELS[role]
            )
            if cached and not self.cache_manager.is_stale(cached):
                cached_results[role] = cached['response']
                cache_hits += 1
                print(f"  ✅ Cache hit: {role}")

        # Prepare prompts
        prompts = self._prepare_prompts(project_data)

        # Run models in parallel (only non-cached)
        tasks = []
        for role in ['architect', 'deployment', 'business']:
            if role not in cached_results:
                tasks.append(self._call_with_rate_limit(role, prompts[role]))
                api_calls += 1

        # Wait for all parallel calls
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, role in enumerate([r for r in ['architect', 'deployment', 'business'] if r not in cached_results]):
                if isinstance(results[i], Exception):
                    print(f"  ❌ {role} model failed: {results[i]}")
                    cached_results[role] = self._fallback_response(role)
                else:
                    cached_results[role] = results[i]
                    # Cache successful responses
                    self.cache_manager.set_cache(
                        project_data['path'],
                        self.MODELS[role],
                        cached_results[role]
                    )

        # Run aggregator model (needs results from previous 3)
        print(f"  🔄 Running aggregator model...")
        aggregator_prompt = self._prepare_aggregator_prompt(
            project_data,
            cached_results
        )

        await self.rate_limiter.acquire()
        api_calls += 1
        aggregator_result = await self.client.call_model(
            self.MODELS['aggregator'],
            aggregator_prompt,
            temperature=0.2
        )

        aggregated = self._parse_aggregator_response(aggregator_result)

        elapsed = time.time() - start_time
        print(f"  ✅ Pipeline complete in {elapsed:.1f}s ({api_calls} API calls, {cache_hits} cache hits)")

        return {
            'llm_results': {
                'architect_analysis': cached_results.get('architect', {}),
                'deployment_analysis': cached_results.get('deployment', {}),
                'business_analysis': cached_results.get('business', {}),
                'aggregated_insights': aggregated,
                'metadata': {
                    'models_used': list(self.MODELS.values()),
                    'total_time_seconds': elapsed,
                    'cache_hits': cache_hits,
                    'api_calls': api_calls
                }
            }
        }

    async def _call_with_rate_limit(self, role: str, prompt: str) -> Dict:
        """Rate-limited API call"""
        await self.rate_limiter.acquire()
        print(f"  🤖 Calling {role} model...")

        response = await self.client.call_model(
            self.MODELS[role],
            prompt,
            temperature=0.3
        )

        # Parse response (handled by Task 2C)
        from modules.llm_response_handler import parse_llm_response
        return parse_llm_response(response['choices'][0]['message']['content'], role)

    def _prepare_prompts(self, project_data: Dict) -> Dict[str, str]:
        """Load prompts from Task 2B templates"""
        from modules.prompt_loader import load_prompt

        prompts = {}
        for role in ['architect', 'deployment', 'business']:
            template = load_prompt(f"{role}_prompt.txt")
            prompts[role] = template.format(**project_data)

        return prompts

    def _fallback_response(self, role: str) -> Dict:
        """Return safe fallback if LLM fails"""
        return {
            'error': f'{role} model unavailable',
            'fallback': True,
            'assessment': 'LLM analysis unavailable - using heuristics only'
        }
```

## Test Criteria

1. **Concurrent Execution**: 3 models run in parallel (verify via timing: should be ~1x model time, not 3x)
2. **Rate Limiting**: No 429 errors from OpenRouter
3. **Caching**: Second run on same project uses cache (0 API calls)
4. **Fallback**: If model fails, pipeline continues with fallback
5. **Total Time**: <3min for full 4-model pipeline (per project)

## Libraries Required
```bash
pip install aiohttp asyncio
```

## Output File
`modules/llm_orchestrator.py`

## Success Criteria
- ✅ 4 models execute successfully
- ✅ Parallel execution (not sequential)
- ✅ Rate limiting works (no API errors)
- ✅ Caching reduces repeat API calls
- ✅ Graceful fallback on model failure
- ✅ Total time <3min per project

---

**Created by The Collective Borg.tools**
**Task Owner**: LLM Orchestrator Session (GRUPA 2 - Track 1)
