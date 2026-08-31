from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


class EmptyResponseError(RuntimeError):
    """A provider returned a success response with no usable content.

    Reasoning models can spend their whole token budget thinking and reply with
    an empty message. Callers must treat this as a failed turn rather than a
    real (blank) answer.
    """


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model: str
    temperature: float = 0.2
    # Reasoning models spend this budget thinking before emitting anything, and a
    # short, abstract surface needs more of it. At 512 the Questioner returned
    # empty content on 10 of 21 puzzles — the turn is then discarded and a game
    # can end with zero rounds played. 2048 cleared 19 of 21; see
    # scripts/check_puzzle_runnability.py.
    max_tokens: int = 2048


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

