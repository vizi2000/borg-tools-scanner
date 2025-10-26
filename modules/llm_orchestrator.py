"""
LLM Model Orchestrator - Borg Tools Scanner v2.0

Async multi-model pipeline for OpenRouter with:
- Parallel execution (3 models concurrent, then aggregator)
- Token bucket rate limiting
- Exponential backoff retry
- Cache integration (ready for Task 2D)
- Response parsing (ready for Task 2C)

Created by The Collective Borg.tools
"""

import asyncio
import aiohttp
import os
import time
import json
from typing import Dict, Any, List, Optional
from pathlib import Path


class OpenRouterClient:
    """Async HTTP client for OpenRouter API"""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")

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

        Args:
            model: OpenRouter model identifier
            prompt: User prompt to send
            temperature: Sampling temperature (0.0-1.0)
            max_retries: Maximum retry attempts

        Returns:
            API response JSON

        Raises:
            Exception: If all retries fail
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
                print(f"  ⏱️  Timeout on attempt {attempt+1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
            except aiohttp.ClientError as e:
                print(f"  ❌ Client error on attempt {attempt+1}/{max_retries}: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise Exception(f"Failed after {max_retries} attempts")


class RateLimiter:
    """Token bucket rate limiter for API calls"""

    def __init__(self, calls_per_minute: int = 10):
        self.calls_per_minute = calls_per_minute
        self.tokens = float(calls_per_minute)
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


class CacheManager:
    """
    Stub cache manager - will be replaced by Task 2D implementation
    For now, provides no-op caching
    """

    def get_cached(self, project_path: str, model_name: str) -> Optional[Dict]:
        """Get cached response if available"""
        # TODO: Implement in Task 2D
        return None

    def set_cache(self, project_path: str, model_name: str, response: Dict):
        """Store response in cache"""
        # TODO: Implement in Task 2D
        pass

    def is_stale(self, cache_entry: Dict, max_age_days: int = 7) -> bool:
        """Check if cache entry is stale"""
        # TODO: Implement in Task 2D
        return True


def parse_llm_response(content: str, role: str) -> Dict[str, Any]:
    """
    Stub response parser - will be replaced by Task 2C implementation
    For now, provides basic JSON extraction

    Args:
        content: Raw LLM response text
        role: Model role (architect, deployment, business)

    Returns:
        Parsed response dictionary
    """
    # Try to extract JSON from markdown code blocks
    import re

    # Look for ```json ... ``` blocks
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find raw JSON in the content
    try:
        # Find first { and last }
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1:
            json_str = content[start:end+1]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Fallback: return the raw content
    return {
        'raw_response': content,
        'parsed': False,
        'role': role,
        'note': 'Failed to parse JSON - using raw response'
    }


def load_prompt(template_name: str, project_data: Dict) -> str:
    """
    Stub prompt loader - will be replaced by Task 2B implementation
    For now, generates basic prompts

    Args:
        template_name: Name of the prompt template
        project_data: Project information to inject

    Returns:
        Formatted prompt string
    """
    # Extract role from template name (e.g., "architect_prompt.txt" -> "architect")
    role = template_name.replace('_prompt.txt', '')

    # Basic prompts for each role
    prompts = {
        'architect': f"""You are a Senior Software Architect. Analyze this codebase and provide insights.

Project: {project_data.get('name', 'Unknown')}
Languages: {', '.join(project_data.get('languages', []))}

Code Analysis:
{json.dumps(project_data.get('code_analysis', {}), indent=2)}

Provide your analysis in JSON format with these fields:
{{
  "architecture_assessment": "overall assessment of the architecture",
  "design_patterns": ["list", "of", "patterns", "detected"],
  "scalability_notes": "notes on scalability",
  "technical_debt_priority": "low/medium/high"
}}""",

        'deployment': f"""You are a DevOps Engineer. Analyze the deployment strategy for this project.

Project: {project_data.get('name', 'Unknown')}
Deployment Analysis:
{json.dumps(project_data.get('deployment_analysis', {}), indent=2)}

Provide your analysis in JSON format with these fields:
{{
  "deployment_strategy": "recommended deployment approach",
  "infrastructure_recommendations": "infrastructure suggestions",
  "deployment_blockers": [{{"issue": "description", "severity": "high/medium/low"}}],
  "mvp_roadmap": ["step1", "step2", "step3"]
}}""",

        'business': f"""You are a Business Analyst. Assess the business viability of this project.

Project: {project_data.get('name', 'Unknown')}
Documentation:
{json.dumps(project_data.get('doc_analysis', {}), indent=2)}

Provide your analysis in JSON format with these fields:
{{
  "problem_solved": "what problem does this solve",
  "target_audience": "who is this for",
  "monetization_strategy": "how could this make money",
  "market_viability": 7,
  "portfolio_suitable": true,
  "portfolio_pitch": "elevator pitch for portfolio"
}}"""
    }

    return prompts.get(role, f"Analyze this project: {project_data.get('name', 'Unknown')}")


class ModelPipeline:
    """Orchestrates parallel calls to 4 specialized models"""

    MODELS = {
        'architect': 'meta-llama/llama-4-scout:free',
        'deployment': 'mistralai/mistral-small-3.1:free',  # Using Mistral Small
        'business': 'deepseek/deepseek-r1:free',
        'aggregator': 'meta-llama/llama-4-maverick:free'
    }

    # Fallback models in case free tier models change
    FALLBACK_MODELS = {
        'architect': 'meta-llama/llama-3.1-8b-instruct:free',
        'deployment': 'meta-llama/llama-3.1-8b-instruct:free',
        'business': 'meta-llama/llama-3.1-8b-instruct:free',
        'aggregator': 'meta-llama/llama-3.1-8b-instruct:free'
    }

    def __init__(self, dry_run: bool = False):
        """
        Initialize the model pipeline

        Args:
            dry_run: If True, use mock responses instead of real API calls
        """
        self.client = OpenRouterClient()
        self.rate_limiter = RateLimiter(calls_per_minute=10)
        self.cache_manager = CacheManager()
        self.dry_run = dry_run

    async def run_parallel_analysis(self, project_data: Dict) -> Dict:
        """
        Main entry point: runs 4 models in parallel (3 + 1 aggregator)

        Args:
            project_data: Dictionary containing project information including:
                - name: Project name
                - path: Project path
                - languages: List of languages
                - code_analysis: Code quality metrics
                - deployment_analysis: Deployment info
                - doc_analysis: Documentation analysis

        Returns:
            Complete LLM analysis results
        """
        print(f"🤖 [LLM PIPELINE] Analyzing {project_data.get('name', 'Unknown')}...")
        start_time = time.time()
        cache_hits = 0
        api_calls = 0

        # Check cache first
        cached_results = {}
        project_path = project_data.get('path', '')

        for role in ['architect', 'deployment', 'business']:
            cached = self.cache_manager.get_cached(
                project_path,
                self.MODELS[role]
            )
            if cached and not self.cache_manager.is_stale(cached):
                cached_results[role] = cached.get('response', {})
                cache_hits += 1
                print(f"  ✅ Cache hit: {role}")

        # Prepare prompts for non-cached models
        tasks = []
        roles_to_run = []

        for role in ['architect', 'deployment', 'business']:
            if role not in cached_results:
                roles_to_run.append(role)
                prompt = load_prompt(f"{role}_prompt.txt", project_data)
                tasks.append(self._call_with_rate_limit(role, prompt))
                api_calls += 1

        # Run models in parallel (only non-cached)
        if tasks:
            print(f"  🔄 Running {len(tasks)} models in parallel...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, role in enumerate(roles_to_run):
                if isinstance(results[i], Exception):
                    print(f"  ❌ {role} model failed: {results[i]}")
                    cached_results[role] = self._fallback_response(role)
                else:
                    cached_results[role] = results[i]
                    # Cache successful responses
                    self.cache_manager.set_cache(
                        project_path,
                        self.MODELS[role],
                        cached_results[role]
                    )

        # Run aggregator model (needs results from previous 3)
        print(f"  🔄 Running aggregator model...")
        aggregator_prompt = self._prepare_aggregator_prompt(
            project_data,
            cached_results
        )

        if not self.dry_run:
            await self.rate_limiter.acquire()
            api_calls += 1
            try:
                aggregator_result = await self.client.call_model(
                    self.MODELS['aggregator'],
                    aggregator_prompt,
                    temperature=0.2
                )
                aggregated = parse_llm_response(
                    aggregator_result['choices'][0]['message']['content'],
                    'aggregator'
                )
            except Exception as e:
                print(f"  ❌ Aggregator model failed: {e}")
                aggregated = self._fallback_aggregated_response()
        else:
            # Dry run: use mock aggregated response
            aggregated = self._mock_aggregated_response(project_data)

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
                    'total_time_seconds': round(elapsed, 2),
                    'cache_hits': cache_hits,
                    'api_calls': api_calls
                }
            }
        }

    async def _call_with_rate_limit(self, role: str, prompt: str) -> Dict:
        """
        Rate-limited API call

        Args:
            role: Model role (architect, deployment, business)
            prompt: Formatted prompt

        Returns:
            Parsed LLM response
        """
        if self.dry_run:
            # Mock response for dry run
            print(f"  🎭 [DRY RUN] Calling {role} model...")
            await asyncio.sleep(0.5)  # Simulate API delay
            return self._mock_response(role)

        await self.rate_limiter.acquire()
        print(f"  🤖 Calling {role} model...")

        response = await self.client.call_model(
            self.MODELS[role],
            prompt,
            temperature=0.3
        )

        # Parse response
        parsed = parse_llm_response(
            response['choices'][0]['message']['content'],
            role
        )

        return parsed

    def _prepare_aggregator_prompt(self, project_data: Dict, specialist_results: Dict) -> str:
        """
        Prepare aggregator prompt that synthesizes specialist analyses

        Args:
            project_data: Project information
            specialist_results: Results from architect, deployment, business models

        Returns:
            Formatted aggregator prompt
        """
        return f"""You are a Senior Technical Lead synthesizing multiple expert analyses.

Project: {project_data.get('name', 'Unknown')}

ARCHITECT ANALYSIS:
{json.dumps(specialist_results.get('architect', {}), indent=2)}

DEPLOYMENT ANALYSIS:
{json.dumps(specialist_results.get('deployment', {}), indent=2)}

BUSINESS ANALYSIS:
{json.dumps(specialist_results.get('business', {}), indent=2)}

IMPORTANT: Respond with ONLY valid JSON. Do not include any markdown, explanations, or text outside the JSON object.

Return this exact JSON structure:
{{
  "overall_assessment": "unified assessment combining all perspectives (string)",
  "top_priorities": ["priority1", "priority2", "priority3"],
  "vibecodibility_score": 8,
  "borg_tools_fit": 7
}}

Focus on actionable insights and alignment between technical and business perspectives.
Response must be valid JSON only - no markdown, no code blocks, just raw JSON."""

    def _fallback_response(self, role: str) -> Dict:
        """Return safe fallback if LLM fails"""
        return {
            'error': f'{role} model unavailable',
            'fallback': True,
            'assessment': 'LLM analysis unavailable - using heuristics only'
        }

    def _fallback_aggregated_response(self) -> Dict:
        """Return safe fallback for aggregator"""
        return {
            'overall_assessment': 'Aggregation unavailable - see individual analyses',
            'top_priorities': ['Review individual model outputs'],
            'vibecodibility_score': 5,
            'borg_tools_fit': 5,
            'fallback': True
        }

    def _mock_response(self, role: str) -> Dict:
        """Generate mock response for dry run testing"""
        mock_responses = {
            'architect': {
                'architecture_assessment': 'Well-structured modular architecture with clear separation of concerns',
                'design_patterns': ['MVC', 'Dependency Injection', 'Factory Pattern'],
                'scalability_notes': 'Good foundation for horizontal scaling, consider caching layer',
                'technical_debt_priority': 'medium'
            },
            'deployment': {
                'deployment_strategy': 'Containerized deployment with Docker + Kubernetes',
                'infrastructure_recommendations': 'Use managed services for database and caching',
                'deployment_blockers': [
                    {'issue': 'Missing health check endpoints', 'severity': 'medium'},
                    {'issue': 'No CI/CD pipeline configured', 'severity': 'high'}
                ],
                'mvp_roadmap': [
                    'Set up Docker containerization',
                    'Configure CI/CD pipeline',
                    'Deploy to staging environment'
                ]
            },
            'business': {
                'problem_solved': 'Automates code quality analysis and deployment readiness assessment',
                'target_audience': 'Development teams and DevOps engineers',
                'monetization_strategy': 'SaaS subscription with tiered pricing based on project count',
                'market_viability': 8,
                'portfolio_suitable': True,
                'portfolio_pitch': 'AI-powered code intelligence platform that helps teams ship better software faster'
            }
        }
        return mock_responses.get(role, {'mock': True, 'role': role})

    def _mock_aggregated_response(self, project_data: Dict) -> Dict:
        """Generate mock aggregated response for dry run"""
        return {
            'overall_assessment': 'Strong technical foundation with clear business value. Ready for MVP deployment with minor improvements to CI/CD infrastructure.',
            'top_priorities': [
                'Set up automated CI/CD pipeline',
                'Implement health check endpoints',
                'Add monitoring and observability'
            ],
            'vibecodibility_score': 8,
            'borg_tools_fit': 9
        }


async def analyze_with_llm(project_data: Dict, dry_run: bool = False) -> Dict:
    """
    Main entry point for LLM analysis

    Args:
        project_data: Complete project information including:
            - name: Project name
            - path: Project path
            - languages: List of languages
            - code_analysis: From Task 1A
            - deployment_analysis: From Task 1B
            - doc_analysis: From Task 1C
        dry_run: If True, use mock responses instead of real API calls

    Returns:
        Complete LLM analysis results
    """
    pipeline = ModelPipeline(dry_run=dry_run)
    return await pipeline.run_parallel_analysis(project_data)


if __name__ == '__main__':
    # Test with mock data
    print("=" * 60)
    print("LLM ORCHESTRATOR - DRY RUN TEST")
    print("=" * 60)

    test_project = {
        'name': 'test-project',
        'path': '/tmp/test-project',
        'languages': ['python', 'javascript'],
        'code_analysis': {
            'code_quality': {
                'overall_score': 7.5,
                'architecture_pattern': 'MVC'
            }
        },
        'deployment_analysis': {
            'deployment_confidence': 0.75,
            'blockers': []
        },
        'doc_analysis': {
            'documentation_quality': 0.8
        }
    }

    # Run async test
    result = asyncio.run(analyze_with_llm(test_project, dry_run=True))

    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print(json.dumps(result, indent=2))
