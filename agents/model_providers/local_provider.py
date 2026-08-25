from __future__ import annotations

import os
import random
import time
from typing import Any, Dict, Optional

import requests

from ..base_agent import EmptyResponseError

# The Ollama server can drop in-flight requests when it restarts (e.g. the
# desktop app reclaiming port 11434). A benchmark run is dozens of sequential
# calls, so one dropped connection would otherwise throw away the whole run.
MAX_ATTEMPTS = int(os.getenv("OLLAMA_MAX_ATTEMPTS", "4"))
BASE_BACKOFF_S = float(os.getenv("OLLAMA_BACKOFF_S", "3"))
MAX_BACKOFF_S = 30.0


def _env_think() -> Optional[bool]:
    raw = os.getenv("OLLAMA_THINK")
    if raw is None or not raw.strip():
        return None
    return raw.strip().lower() not in ("0", "false", "no", "off")


class OllamaProvider:
    """
    Minimal Ollama chat provider.
    model example: "llama3.3" or "ollama/llama3.3" (prefix is stripped).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_s: Optional[float] = None,
        think: Optional[bool] = None,
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")
        env_timeout = os.getenv("OLLAMA_TIMEOUT")
        self.timeout_s = timeout_s if timeout_s is not None else float(env_timeout or 600.0)
        # Reasoning models (qwen3.5, deepseek-r1…) think by default, which costs
        # ~100x latency for the 是/不是 answers this benchmark needs. OLLAMA_THINK=0
        # turns it off. Unset → field omitted, so non-thinking models still work.
        self.think = think if think is not None else _env_think()

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
            # num_predict is Ollama's max_tokens; without it small local models
            # ramble past the one-question-per-turn contract the agents assume.
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if self.think is not None:
            payload["think"] = self.think
        if extra:
            base_options = payload["options"]
            payload.update(extra)
            extra_options = extra.get("options")
            if isinstance(extra_options, dict):
                # merge rather than clobber the options set above
                payload["options"] = {**base_options, **extra_options}
        delay = BASE_BACKOFF_S
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                resp = requests.post(
                    f"{self.base_url}/api/chat", json=payload, timeout=self.timeout_s
                )
                resp.raise_for_status()
                data = resp.json()
                content = (data.get("message", {}) or {}).get("content", "").strip()
                if content:
                    return content
                # Thinking can consume the whole num_predict budget, leaving
                # content empty; that must not pass as a silent wasted round.
                failure: Exception = EmptyResponseError(
                    f"{model_name} returned empty content"
                )
            except (requests.ConnectionError, requests.Timeout) as exc:
                failure = exc
            if attempt == MAX_ATTEMPTS:
                raise failure
            delay = self._sleep_backoff(delay, attempt, failure)
        raise RuntimeError("unreachable")

    @staticmethod
    def _sleep_backoff(delay: float, attempt: int, exc: Exception) -> float:
        # jitter so parallel runs do not retry in lockstep
        wait = delay + random.uniform(0, delay * 0.25)
        print(
            f"[ollama] {type(exc).__name__} on attempt {attempt}; "
            f"retrying in {wait:.1f}s",
            flush=True,
        )
        time.sleep(wait)
        return min(delay * 2, MAX_BACKOFF_S)

