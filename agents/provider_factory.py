from __future__ import annotations

from .base_agent import BaseProvider
from .model_providers.mock_provider import MockProvider

_TINKER_SINGLETON = None


def get_provider(provider_name: str) -> BaseProvider:
    name = (provider_name or "mock").lower().strip()
    if name in ("mock", "test"):
        return MockProvider()
    if name in ("openai", "gpt"):
        from .model_providers.openai_provider import OpenAIProvider

        return OpenAIProvider()
    if name in ("anthropic", "claude"):
        from .model_providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    if name in ("local", "ollama"):
        from .model_providers.local_provider import OllamaProvider

        return OllamaProvider()
    if name in ("deepseek",):
        from .model_providers.deepseek_provider import DeepSeekProvider

        return DeepSeekProvider()
    if name in ("gemini", "google", "google-ai"):
        from .model_providers.gemini_provider import GeminiProvider

        return GeminiProvider()
    if name in ("qwen", "dashscope", "tongyi"):
        from .model_providers.qwen_provider import QwenProvider

        return QwenProvider()
    if name in ("openrouter", "or"):
        from .model_providers.openrouter_provider import OpenRouterProvider

        return OpenRouterProvider()
    if name in ("tinker", "thinking-machines"):
        # One ServiceClient per process: Tinker caps active sessions account-wide,
        # and a fresh client per game accumulates until the server 400s
        # ("Too many active sessions") — observed killing all E2 shards.
        global _TINKER_SINGLETON
        if _TINKER_SINGLETON is None:
            from .model_providers.tinker_provider import TinkerProvider

            _TINKER_SINGLETON = TinkerProvider()
        return _TINKER_SINGLETON
    if name in ("zai", "glm", "z.ai"):
        from .model_providers.zai_provider import ZaiProvider

        return ZaiProvider()
    raise ValueError(f"Unknown provider: {provider_name}")


def get_provider_safe(provider_name: str, *, fallback_mock: bool = True) -> BaseProvider:
    try:
        return get_provider(provider_name)
    except Exception:
        if fallback_mock:
            return MockProvider()
        raise
