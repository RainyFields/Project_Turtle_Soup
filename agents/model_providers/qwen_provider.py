from __future__ import annotations

import os
from typing import Any, Dict, Optional

from openai import OpenAI

DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"


class QwenProvider:
    """Qwen Cloud — OpenAI-compatible API (https://docs.qwencloud.com/)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        key = (api_key or os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY") or "").strip()
        if not key:
            raise RuntimeError(
                "Missing QWEN_API_KEY. Create one at https://home.qwencloud.com/api-keys"
            )
        url = (base_url or os.getenv("QWEN_BASE_URL") or DEFAULT_BASE_URL).strip()
        self.client = OpenAI(api_key=key, base_url=url)

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
