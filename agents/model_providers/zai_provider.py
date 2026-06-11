from __future__ import annotations

import os
from typing import Any, Dict, Optional

from openai import OpenAI

# General API (benchmark / scripts): https://docs.z.ai/api-reference/introduction
DEFAULT_BASE_URL = "https://api.z.ai/api/paas/v4"
# GLM Coding Plan endpoint — IDE tools only; do not use for batch benchmark by default
CODING_BASE_URL = "https://api.z.ai/api/coding/paas/v4"


class ZaiProvider:
    """Z.AI / GLM — OpenAI-compatible API (https://docs.z.ai/)."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        key = (api_key or os.getenv("ZAI_API_KEY") or os.getenv("Z_AI_API_KEY") or "").strip()
        if not key:
            raise RuntimeError(
                "Missing ZAI_API_KEY. Create one at https://z.ai — keep in local .env only."
            )
        if base_url:
            url = base_url
        elif os.getenv("ZAI_USE_CODING_ENDPOINT", "").lower() in ("1", "true", "yes"):
            url = os.getenv("ZAI_BASE_URL") or CODING_BASE_URL
        else:
            url = os.getenv("ZAI_BASE_URL") or DEFAULT_BASE_URL
        self.client = OpenAI(api_key=key, base_url=url.rstrip("/"))

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
        create_kwargs: Dict[str, Any] = dict(extra or {})
        json_mode = create_kwargs.pop("json_mode", False)
        if json_mode:
            create_kwargs["response_format"] = {"type": "json_object"}
        resp = self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **create_kwargs,
        )
        return (resp.choices[0].message.content or "").strip()
