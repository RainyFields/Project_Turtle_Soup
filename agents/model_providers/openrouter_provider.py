from __future__ import annotations

import os
import random
import time
from typing import Any, Dict, Optional

from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

from ..base_agent import EmptyResponseError

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
# Free/stealth models sit behind a shared upstream pool that returns 429 in
# bursts. A benchmark run is ~40+ sequential calls, so one un-retried 429
# would throw away the whole run.
MAX_ATTEMPTS = int(os.getenv("OPENROUTER_MAX_ATTEMPTS", "6"))
BASE_BACKOFF_S = float(os.getenv("OPENROUTER_BACKOFF_S", "5"))
MAX_BACKOFF_S = 60.0


class OpenRouterProvider:
    """OpenRouter — OpenAI-compatible gateway (https://openrouter.ai/docs).

    Models are namespaced, e.g. "anthropic/claude-sonnet-4.5" or
    "deepseek/deepseek-r1:free"; pass the id through unchanged.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        key = (api_key or os.getenv("OPENROUTER_API_KEY") or "").strip()
        if not key:
            raise RuntimeError(
                "Missing OPENROUTER_API_KEY. Create one at https://openrouter.ai/keys "
                "— keep in local .env only."
            )
        url = (base_url or os.getenv("OPENROUTER_BASE_URL") or DEFAULT_BASE_URL).strip()
        # Optional attribution headers; OpenRouter ranks callers that send them.
        headers = {}
        referer = os.getenv("OPENROUTER_SITE_URL")
        title = os.getenv("OPENROUTER_APP_NAME", "turtle-soup-bench")
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title
        self.client = OpenAI(api_key=key, base_url=url.rstrip("/"), default_headers=headers or None)

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
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        delay = BASE_BACKOFF_S
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    messages=messages,
                    **create_kwargs,
                )
                content = (resp.choices[0].message.content or "").strip()
                if content:
                    return content
                # Reasoning models can spend the whole budget thinking and return
                # an empty message. Silently accepting it burns a game round.
                if attempt == MAX_ATTEMPTS:
                    raise EmptyResponseError(
                        f"{model} returned empty content after {attempt} attempts"
                    )
                self._sleep_backoff(delay, attempt, EmptyResponseError("empty content"))
                delay = min(delay * 2, MAX_BACKOFF_S)
                continue
            except (RateLimitError, APIConnectionError) as exc:
                if attempt == MAX_ATTEMPTS:
                    raise
                self._sleep_backoff(delay, attempt, exc)
                delay = min(delay * 2, MAX_BACKOFF_S)
            except APIStatusError as exc:
                # 5xx from the upstream provider is worth retrying; 4xx is not
                if exc.status_code < 500 or attempt == MAX_ATTEMPTS:
                    raise
                self._sleep_backoff(delay, attempt, exc)
                delay = min(delay * 2, MAX_BACKOFF_S)
        raise RuntimeError("unreachable")

    @staticmethod
    def _sleep_backoff(delay: float, attempt: int, exc: Exception) -> None:
        # jitter so parallel runs do not retry in lockstep
        wait = delay + random.uniform(0, delay * 0.25)
        print(
            f"[openrouter] {type(exc).__name__} on attempt {attempt}; "
            f"retrying in {wait:.1f}s",
            flush=True,
        )
        time.sleep(wait)
