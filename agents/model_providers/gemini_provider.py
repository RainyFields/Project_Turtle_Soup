from __future__ import annotations

import os
from typing import Any, Dict, Optional


def _gemini_api_key(explicit: Optional[str] = None) -> str:
    key = explicit or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError(
            "Missing GEMINI_API_KEY (or GOOGLE_API_KEY). Set in .env — get one at "
            "https://aistudio.google.com/apikey"
        )
    return key


class GeminiProvider:
    """Google Gemini via google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None):
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise RuntimeError(
                "Install Gemini support: pip install google-genai"
            ) from e
        self._genai = genai
        self._types = types
        self.client = genai.Client(api_key=_gemini_api_key(api_key))

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
        config_kwargs: Dict[str, Any] = {
            "system_instruction": system,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if extra and extra.get("json_mode"):
            config_kwargs["response_mime_type"] = "application/json"
        config = self._types.GenerateContentConfig(**config_kwargs)
        resp = self.client.models.generate_content(
            model=model,
            contents=user,
            config=config,
        )
        text = getattr(resp, "text", None) or ""
        return text.strip()
