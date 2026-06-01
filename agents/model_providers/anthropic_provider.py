from __future__ import annotations

import os
from typing import Any, Dict, Optional

from anthropic import Anthropic


class AnthropicProvider:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("Missing ANTHROPIC_API_KEY (set env or .env)")
        self.client = Anthropic(api_key=key)

    def generate(
        self,
        *,
        system: str,
        user: str,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 512,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        msg = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
            **(extra or {}),
        )
        # anthropic returns list blocks
        parts = []
        for b in msg.content:
            if getattr(b, "type", None) == "text":
                parts.append(b.text)
        return ("".join(parts)).strip()

