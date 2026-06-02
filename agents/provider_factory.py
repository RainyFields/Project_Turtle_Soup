from __future__ import annotations

from typing import Any

from .base_agent import BaseProvider
from .model_providers.mock_provider import MockProvider


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
    raise ValueError(f"Unknown provider: {provider_name}")


def get_provider_safe(provider_name: str, *, fallback_mock: bool = True) -> BaseProvider:
    try:
        return get_provider(provider_name)
    except Exception:
        if fallback_mock:
            return MockProvider()
        raise
