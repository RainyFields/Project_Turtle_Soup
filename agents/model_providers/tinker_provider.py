from __future__ import annotations

import os
import random
import re
import time
from typing import Any, Dict, Optional, Tuple

from ..base_agent import EmptyResponseError

MAX_ATTEMPTS = int(os.getenv("TINKER_MAX_ATTEMPTS", "4"))
BASE_BACKOFF_S = float(os.getenv("TINKER_BACKOFF_S", "5"))
MAX_BACKOFF_S = 60.0

# Raw sampling returns the model's full output stream, so unlike the chat APIs
# thinking arrives inline as <think>…</think> (Qwen3-style templates may even
# open the tag inside the generation prompt, leaving only a dangling close).
_THINK_BLOCK = re.compile(r"<think>.*?</think>", flags=re.DOTALL)
_THINK_DANGLING = re.compile(r"^.*?</think>", flags=re.DOTALL)


def _strip_thinking(text: str) -> str:
    text = _THINK_BLOCK.sub("", text)
    text = _THINK_DANGLING.sub("", text)
    return text.strip()


class TinkerProvider:
    """Thinking Machines Tinker — token-billed sampling on open-weight models.

    `model` is either a base-model name as listed on
    https://tinker-docs.thinkingmachines.ai/tinker/models/ (e.g.
    "Qwen/Qwen3-235B-A22B-Instruct-2507") or a "tinker://…" checkpoint path
    from one of our training runs, so RL-trained Questioners plug straight
    into the benchmark.

    Uses the native SDK's SamplingClient rather than the OpenAI-compatible
    beta endpoint: serverless chat there only covers Inkling variants, while
    SDK sampling covers every supported base model. Chat formatting goes
    through the model tokenizer's own chat template.

    max_tokens includes thinking tokens (same trap as Ollama/OpenRouter —
    see AGENTS.md); give reasoning models at least 1024.
    """

    def __init__(self, api_key: Optional[str] = None):
        key = (api_key or os.getenv("TINKER_API_KEY") or "").strip()
        if not key:
            raise RuntimeError(
                "Missing TINKER_API_KEY. Create one at "
                "https://tinker.thinkingmachines.ai/keys — keep in local .env only."
            )
        os.environ.setdefault("TINKER_API_KEY", key)
        try:
            import tinker
        except ImportError as exc:
            raise RuntimeError(
                "The tinker SDK is not installed: pip install tinker"
            ) from exc
        self._types = tinker.types
        self.service_client = tinker.ServiceClient()
        self._clients: Dict[str, Tuple[Any, Any]] = {}

    def _get_client(self, model: str) -> Tuple[Any, Any]:
        """(sampling_client, tokenizer) per model, cached across rounds."""
        cached = self._clients.get(model)
        if cached is not None:
            return cached
        if model.startswith("tinker://"):
            client = self.service_client.create_sampling_client(model_path=model)
        else:
            client = self.service_client.create_sampling_client(base_model=model)
        tokenizer = client.get_tokenizer()
        self._clients[model] = (client, tokenizer)
        return client, tokenizer

    def _render_prompt(self, tokenizer: Any, system: str, user: str) -> Any:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        if getattr(tokenizer, "chat_template", None):
            ids = tokenizer.apply_chat_template(
                messages, add_generation_prompt=True, tokenize=True
            )
        else:
            ids = tokenizer.encode(f"{system}\n\n{user}\n")
        return self._types.ModelInput.from_ints(ids)

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
        client, tokenizer = self._get_client(model)
        prompt = self._render_prompt(tokenizer, system, user)
        params_kwargs: Dict[str, Any] = dict(extra or {})
        params_kwargs.pop("json_mode", None)  # no JSON mode in raw sampling
        params = self._types.SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            **params_kwargs,
        )

        delay = BASE_BACKOFF_S
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                result = client.sample(
                    prompt=prompt, num_samples=1, sampling_params=params
                )
                if hasattr(result, "result"):  # sample() returns a Future
                    result = result.result()
                tokens = result.sequences[0].tokens
                content = _strip_thinking(
                    tokenizer.decode(tokens, skip_special_tokens=True)
                )
                if content:
                    return content
                failure: Exception = EmptyResponseError(
                    f"{model} returned empty content (thinking may have "
                    f"consumed the {max_tokens}-token budget)"
                )
            except EmptyResponseError:
                raise
            except Exception as exc:  # SDK surfaces transport errors variously
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
            f"[tinker] {type(exc).__name__} on attempt {attempt}; "
            f"retrying in {wait:.1f}s",
            flush=True,
        )
        time.sleep(wait)
        return min(delay * 2, MAX_BACKOFF_S)
