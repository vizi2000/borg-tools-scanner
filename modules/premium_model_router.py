"""
Premium Model Router - Borg Tools Scanner v2.0

OpenRouter auto model integration with preference for cloaked premium models.
Implements intelligent routing with fallback strategies.

Created by The Collective Borg.tools
"""

import os
import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional


class PremiumModelRouter:
    """Routes requests to OpenRouter with premium model preferences"""

    # Cloaked premium models (free during testing period)
    CLOAKED_MODELS = [
        "openrouter/sonoma-sky-alpha",    # Maximum intelligence, 2M context
        "openrouter/horizon-beta",         # Improved general purpose
        "openrouter/cypher-alpha",         # All-purpose, long-context
        "openrouter/optimus-alpha",        # Real-world use cases
        "openrouter/quasar-alpha",         # Powerful, long-context
        "openrouter/sonoma-dusk-alpha",   # Fast, intelligent
    ]

    # Premium fallback models
    PREMIUM_MODELS = [
        "deepseek/deepseek-r1",           # Excellent reasoning (free)
        "anthropic/claude-3.5-sonnet",    # Premium quality
        "openai/gpt-4o",                  # Premium quality
        "google/gemini-2.0-flash-exp:free",  # Fast and free
        "meta-llama/llama-3.1-70b-instruct:free",  # Good free option
    ]

    # Fast models for triage
    FAST_MODELS = [
        "meta-llama/llama-3.1-8b-instruct:free",
        "google/gemini-2.0-flash-exp:free",
        "mistralai/mistral-7b-instruct:free",
    ]

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, mode: str = "auto", prefer_free: bool = True):
        """
        Initialize premium model router

        Args:
            mode: Routing mode - "auto", "cloaked", "premium", "fast"
            prefer_free: Prefer free models when possible
        """
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")

        self.mode = mode
        self.prefer_free = prefer_free
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://borg.tools',
            'X-Title': 'Borg Tools Scanner V2 - Premium'
        }

    def get_model_for_role(self, role: str, complexity: str = "medium") -> str:
        """
        Get appropriate model for a specific role and complexity

        Args:
            role: Model role (architect, deployment, business, aggregator, triage)
            complexity: Task complexity (low, medium, high)

        Returns:
            Model identifier
        """
        if self.mode == "fast" or role == "triage":
            return self.FAST_MODELS[0]

        if self.mode == "cloaked":
            return self.CLOAKED_MODELS[0]

        if self.mode == "auto":
            # Use openrouter/auto with preferences
            return "openrouter/auto"

        # Premium mode - select based on role and complexity
        if complexity == "high" or role == "aggregator":
            return self.CLOAKED_MODELS[0]  # Best model
        elif complexity == "medium":
            return self.PREMIUM_MODELS[0]  # Good balance
        else:
            return self.FAST_MODELS[0]  # Fast for simple tasks

    def get_provider_preferences(self) -> Dict[str, Any]:
        """
        Get provider routing preferences for OpenRouter

        Returns:
            Provider preferences dictionary
        """
        if self.prefer_free:
            # Prefer free models, but allow paid fallback
            return {
                "order": [
                    "DeepSeek",      # Free R1 model
                    "Meta",          # Free Llama models
                    "Google",        # Free Gemini
                    "Mistral",       # Some free models
                    "Anthropic",     # Premium fallback
                    "OpenAI"         # Premium fallback
                ],
                "allow_fallbacks": True,
                "require_parameters": True
            }
        else:
            # Prefer quality over cost
            return {
                "order": [
                    "Anthropic",     # Claude (best quality)
                    "OpenAI",        # GPT (good quality)
                    "DeepSeek",      # R1 (excellent reasoning)
                    "Google",        # Gemini
                    "Meta"           # Llama
                ],
                "allow_fallbacks": True,
                "require_parameters": True
            }

    async def call_model(
        self,
        role: str,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        complexity: str = "medium"
    ) -> Dict[str, Any]:
        """
        Call model with automatic routing and fallback

        Args:
            role: Model role
            prompt: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            complexity: Task complexity

        Returns:
            API response with model metadata
        """
        model = self.get_model_for_role(role, complexity)
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # Add provider preferences for auto mode
        if model == "openrouter/auto":
            payload["provider"] = self.get_provider_preferences()

        # Try primary model
        try:
            response = await self._make_request(payload)
            
            # Extract which model was actually used
            actual_model = response.get('model', model)
            
            return {
                'success': True,
                'response': response,
                'requested_model': model,
                'actual_model': actual_model,
                'role': role,
                'content': response['choices'][0]['message']['content']
            }

        except Exception as e:
            print(f"  ⚠️  Primary model failed ({model}): {e}")
            
            # Fallback strategy
            return await self._fallback_call(role, prompt, temperature, max_tokens, str(e))

    async def _make_request(self, payload: Dict) -> Dict:
        """Make HTTP request to OpenRouter API"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.BASE_URL}/chat/completions",
                json=payload,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")

    async def _fallback_call(
        self,
        role: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
        error: str
    ) -> Dict[str, Any]:
        """
        Fallback to alternative models if primary fails

        Args:
            role: Model role
            prompt: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            error: Error from primary call

        Returns:
            Fallback response or error
        """
        # Try fallback models in order
        fallback_models = self.PREMIUM_MODELS + self.FAST_MODELS

        for fallback_model in fallback_models[:3]:  # Try up to 3 fallbacks
            try:
                print(f"  🔄 Trying fallback: {fallback_model}")
                
                payload = {
                    "model": fallback_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }

                response = await self._make_request(payload)
                
                return {
                    'success': True,
                    'response': response,
                    'requested_model': 'fallback',
                    'actual_model': fallback_model,
                    'role': role,
                    'content': response['choices'][0]['message']['content'],
                    'fallback': True,
                    'original_error': error
                }

            except Exception as e:
                print(f"  ⚠️  Fallback failed ({fallback_model}): {e}")
                continue

        # All fallbacks failed
        return {
            'success': False,
            'error': f"All models failed. Last error: {error}",
            'role': role,
            'content': None,
            'fallback': True
        }

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about available models

        Returns:
            Dictionary with model information
        """
        return {
            'mode': self.mode,
            'prefer_free': self.prefer_free,
            'cloaked_models': self.CLOAKED_MODELS,
            'premium_models': self.PREMIUM_MODELS,
            'fast_models': self.FAST_MODELS,
            'provider_preferences': self.get_provider_preferences()
        }


class ModelUsageTracker:
    """Tracks which models are used and estimates costs"""

    def __init__(self):
        self.usage = []
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0

    def record_call(self, result: Dict[str, Any]):
        """Record a model call"""
        self.total_calls += 1
        
        if result.get('success'):
            self.successful_calls += 1
        else:
            self.failed_calls += 1

        self.usage.append({
            'role': result.get('role'),
            'requested_model': result.get('requested_model'),
            'actual_model': result.get('actual_model'),
            'success': result.get('success'),
            'fallback': result.get('fallback', False)
        })

    def get_summary(self) -> Dict[str, Any]:
        """Get usage summary"""
        model_counts = {}
        for call in self.usage:
            model = call.get('actual_model', 'unknown')
            model_counts[model] = model_counts.get(model, 0) + 1

        return {
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'success_rate': f"{(self.successful_calls/self.total_calls*100):.1f}%" if self.total_calls > 0 else "0%",
            'models_used': model_counts,
            'unique_models': len(model_counts)
        }

    def print_summary(self):
        """Print usage summary"""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("MODEL USAGE SUMMARY")
        print("=" * 60)
        print(f"Total calls: {summary['total_calls']}")
        print(f"Successful: {summary['successful_calls']}")
        print(f"Failed: {summary['failed_calls']}")
        print(f"Success rate: {summary['success_rate']}")
        print(f"\nModels used ({summary['unique_models']} unique):")
        for model, count in sorted(summary['models_used'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {model}: {count} calls")


if __name__ == '__main__':
    # Test the router
    print("=" * 60)
    print("PREMIUM MODEL ROUTER - TEST")
    print("=" * 60)

    router = PremiumModelRouter(mode="auto", prefer_free=True)
    info = router.get_model_info()

    print(f"\nMode: {info['mode']}")
    print(f"Prefer free: {info['prefer_free']}")
    print(f"\nCloaked models available: {len(info['cloaked_models'])}")
    for model in info['cloaked_models'][:3]:
        print(f"  - {model}")
    
    print(f"\nProvider preferences:")
    prefs = info['provider_preferences']
    print(f"  Order: {', '.join(prefs['order'][:5])}")
    print(f"  Allow fallbacks: {prefs['allow_fallbacks']}")

    print("\nModel selection by role:")
    for role in ['triage', 'architect', 'business', 'aggregator']:
        model = router.get_model_for_role(role, complexity="medium")
        print(f"  {role}: {model}")
