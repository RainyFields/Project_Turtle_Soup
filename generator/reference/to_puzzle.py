from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from generator.create.taxonomy import rating_to_difficulty, tags_to_category, tags_to_metadata_tags
from generator.reference.key_clues import extract_key_clues


def _clues_from_solution(surface: str, solution: str, *, max_clues: int = 5) -> List[str]:
    return extract_key_clues(surface, solution, max_clues=max_clues)


def _forbidden_from_solution(solution: str, *, max_items: int = 4) -> List[str]:
    """Heuristic spoiler terms for Oracle — last substantive clauses."""
    parts = [p.strip() for p in re.split(r"[。！？；\n]+", solution.strip()) if len(p.strip()) >= 4]
    if not parts:
        return []
    tail = parts[-max_items:]
    out: List[str] = []
    for chunk in tail:
        if len(chunk) <= 24:
            out.append(chunk)
        else:
            out.append(chunk[:24])
    return out


def _answerable_topics(tags: List[str]) -> List[str]:
    base = ["人物", "地点", "时间", "原因", "经过"]
    for tag in tags:
        if tag not in base:
            base.append(tag)
    return base[:10]


def reference_sample_to_puzzle(
    sample: Dict[str, Any],
    *,
    puzzle_id: str = "",
) -> Dict[str, Any]:
    """Convert crawled reference JSONL row to benchmark puzzle schema."""
    surface = (sample.get("surface") or "").strip()
    solution = (sample.get("solution") or "").strip()
    if not surface or not solution:
        raise ValueError("reference sample missing surface or solution")

    tags = list(sample.get("tags") or [])
    category = tags_to_category(tags) if tags else (sample.get("category") or "mystery")
    if category in ("恐怖", "经典", "搞笑"):
        category = tags_to_category([category])

    rating = sample.get("rating")
    difficulty = rating_to_difficulty(float(rating) if rating is not None else None)

    external_id = str(sample.get("external_id") or "")
    return {
        "id": puzzle_id or f"refsoup_pending_{external_id}",
        "title": (sample.get("title") or f"参考汤 {external_id}").strip(),
        "difficulty": difficulty,
        "category": category,
        "surface": surface,
        "solution": solution,
        "key_clues": _clues_from_solution(surface, solution),
        "oracle_rules": {
            "answerable_topics": _answerable_topics(tags),
            "forbidden_reveal": _forbidden_from_solution(solution),
        },
        "metadata": {
            "source": "reference",
            "language": "zh",
            "tags": tags_to_metadata_tags(tags),
            "reference_site": sample.get("source_site", "ahelumos"),
            "external_id": external_id,
            "reference_url": sample.get("url", ""),
            "rating": rating,
            "rating_count": sample.get("rating_count"),
            "author": sample.get("author", ""),
        },
    }


def is_importable_sample(sample: Dict[str, Any]) -> bool:
    return bool((sample.get("surface") or "").strip() and (sample.get("solution") or "").strip())
