from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


class OllamaProvider:
    """
    Minimal Ollama chat provider.
    model example: "llama3.3" or "ollama/llama3.3" (prefix is stripped).
    """

    def __init__(self, base_url: Optional[str] = None, timeout_s: float = 120.0):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")
        self.timeout_s = timeout_s

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
        model_name = model.split("/", 1)[-1]
        payload: Dict[str, Any] = {
            "model": model_name,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {"temperature": temperature},
        }
        if extra:
            payload.update(extra)
        # Ollama doesn't strictly honor max_tokens; keep for interface parity
        resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout_s)
        resp.raise_for_status()
        data = resp.json()
        return (data.get("message", {}) or {}).get("content", "").strip()

