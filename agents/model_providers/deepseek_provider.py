from __future__ import annotations

import os
from typing import Any, Dict, Optional

from openai import OpenAI


class DeepSeekProvider:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com"):
        key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not key:
            raise RuntimeError("Missing DEEPSEEK_API_KEY (set env or .env)")
        self.client = OpenAI(api_key=key, base_url=base_url)

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
        resp = self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **(extra or {}),
        )
        return (resp.choices[0].message.content or "").strip()
