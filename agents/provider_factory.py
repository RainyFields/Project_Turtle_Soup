from __future__ import annotations

from typing import Any

from .base_agent import BaseProvider
from .model_providers.anthropic_provider import AnthropicProvider
from .model_providers.local_provider import OllamaProvider
from .model_providers.mock_provider import MockProvider
from .model_providers.deepseek_provider import DeepSeekProvider
from .model_providers.openai_provider import OpenAIProvider


def get_provider(provider_name: str) -> BaseProvider:
    name = (provider_name or "mock").lower().strip()
    if name in ("mock", "test"):
        return MockProvider()
    if name in ("openai", "gpt"):
        return OpenAIProvider()
    if name in ("anthropic", "claude"):
        return AnthropicProvider()
    if name in ("local", "ollama"):
        return OllamaProvider()
    if name in ("deepseek",):
        return DeepSeekProvider()
    raise ValueError(f"Unknown provider: {provider_name}")


def get_provider_safe(provider_name: str, *, fallback_mock: bool = True) -> BaseProvider:
    try:
        return get_provider(provider_name)
    except Exception:
        if fallback_mock:
            return MockProvider()
        raise
