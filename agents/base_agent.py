from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model: str
    temperature: float = 0.2
    max_tokens: int = 512


class BaseProvider(Protocol):
    def generate(
        self,
        *,
        system: str,
        user: str,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 512,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str: ...


class BaseAgent:
    def __init__(self, *, provider: BaseProvider, model_cfg: ModelConfig):
        self.provider = provider
        self.model_cfg = model_cfg

    def complete(self, *, system: str, user: str, extra: Optional[Dict[str, Any]] = None) -> str:
        return self.provider.generate(
            system=system,
            user=user,
            model=self.model_cfg.model,
            temperature=self.model_cfg.temperature,
            max_tokens=self.model_cfg.max_tokens,
            extra=extra,
        )

