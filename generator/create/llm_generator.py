from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from agents.provider_factory import get_provider

from .templates import build_user_prompt, load_system_prompt


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def generate_one(
    *,
    category: str,
    difficulty: str,
    pattern_hints: Dict[str, Any],
    provider_name: str = "mock",
    model: str = "gpt-4o",
    candidate_id: str = "turtle_candidate_001",
    style_hints: str = "",
    source_tags: Optional[List[str]] = None,
    metadata_tags: Optional[List[str]] = None,
    max_attempts: int = 3,
) -> Dict[str, Any]:
    provider = get_provider(provider_name)
    system = load_system_prompt()
    user = build_user_prompt(
        category=category,
        difficulty=difficulty,
        pattern_hints=pattern_hints,
        style_hints=style_hints,
        source_tags=source_tags,
    )
    last_err: Optional[Exception] = None
    for attempt in range(max_attempts):
        try:
            raw = provider.generate(
                system=system,
                user=user,
                model=model,
                temperature=0.85 + attempt * 0.05,
                max_tokens=4096,
                extra={
                    "json_mode": provider_name
                    in ("gemini", "google", "google-ai", "deepseek", "qwen", "dashscope", "tongyi")
                },
            )
            data = _extract_json(raw)
            break
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            if attempt + 1 >= max_attempts:
                raise
    else:
        raise last_err or RuntimeError("generate_one failed")
    data.setdefault("id", candidate_id)
    data.setdefault("category", category)
    data.setdefault("difficulty", difficulty)
    meta = data.setdefault("metadata", {})
    if isinstance(meta, dict):
        meta.setdefault("source", "generated")
        meta.setdefault("language", "zh")
        if metadata_tags:
            meta.setdefault("tags", metadata_tags)
        if source_tags:
            meta.setdefault("source_tags", source_tags)
    return data
