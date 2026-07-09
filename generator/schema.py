from __future__ import annotations

from typing import Any, Dict, List, Tuple

DIFFICULTIES = frozenset({"easy", "medium", "hard"})
PUBLISH_SOURCES = frozenset({"generated", "reference"})
GENERATED_ID_PREFIX = "turtle_"
REFERENCE_ID_PREFIX = "refsoup_"
REQUIRED_TOP_LEVEL = (
    "id",
    "title",
    "difficulty",
    "category",
    "surface",
    "solution",
    "key_clues",
    "oracle_rules",
    "metadata",
)


def validate_puzzle(data: Dict[str, Any], *, for_publish: bool = False) -> Tuple[bool, List[str]]:
    """Validate dict against benchmark puzzle schema (see data/puzzles/turtle_001.json)."""
    errors: List[str] = []

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"missing field: {key}")

    if "difficulty" in data and data["difficulty"] not in DIFFICULTIES:
        errors.append(f"invalid difficulty: {data['difficulty']}")

    for text_key in ("surface", "solution"):
        if text_key in data and (not isinstance(data[text_key], str) or not data[text_key].strip()):
            errors.append(f"empty {text_key}")

    if "key_clues" in data:
        if not isinstance(data["key_clues"], list) or not data["key_clues"]:
            errors.append("key_clues must be a non-empty list")
        elif not all(isinstance(c, str) and c.strip() for c in data["key_clues"]):
            errors.append("key_clues must be non-empty strings")

    rules = data.get("oracle_rules")
    if rules is not None:
        if not isinstance(rules, dict):
            errors.append("oracle_rules must be an object")
        else:
            for rk in ("answerable_topics", "forbidden_reveal"):
                if rk in rules and not isinstance(rules[rk], list):
                    errors.append(f"oracle_rules.{rk} must be a list")

    meta = data.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        errors.append("metadata must be an object")

    if for_publish:
        source = data.get("metadata", {}).get("source")
        pid = data.get("id", "")
        if source not in PUBLISH_SOURCES:
            errors.append("metadata.source must be 'generated' or 'reference' for publish")
        elif source == "generated":
            if not isinstance(pid, str) or not pid.startswith(GENERATED_ID_PREFIX):
                errors.append(f"id must match {GENERATED_ID_PREFIX}NNN for generated publish")
        elif source == "reference":
            if not isinstance(pid, str) or not pid.startswith(REFERENCE_ID_PREFIX):
                errors.append(f"id must match {REFERENCE_ID_PREFIX}NNN for reference publish")

    return (len(errors) == 0, errors)


def puzzle_dict_to_json_ready(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize lists/strings for stable JSON output."""
    out = dict(data)
    if "key_clues" in out:
        out["key_clues"] = [str(c).strip() for c in out["key_clues"]]
    rules = out.get("oracle_rules") or {}
    out["oracle_rules"] = {
        "answerable_topics": list(rules.get("answerable_topics") or []),
        "forbidden_reveal": list(rules.get("forbidden_reveal") or []),
    }
    return out
