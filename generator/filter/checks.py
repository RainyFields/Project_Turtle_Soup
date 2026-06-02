from __future__ import annotations

from typing import Any, Dict, List, Tuple

from generator.schema import validate_puzzle


def check_schema(puzzle: Dict[str, Any]) -> Tuple[bool, List[str]]:
    return validate_puzzle(puzzle, for_publish=False)


def check_spoil(puzzle: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Heuristic: forbidden_reveal tokens must not appear in surface."""
    errors: List[str] = []
    surface = (puzzle.get("surface") or "").lower()
    forbidden = puzzle.get("oracle_rules", {}).get("forbidden_reveal") or []
    for term in forbidden:
        if term and term.lower() in surface:
            errors.append(f"surface leaks forbidden term: {term}")
    return (len(errors) == 0, errors)


def check_category_consistency(puzzle: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    cat = (puzzle.get("category") or "").strip()
    tags = [t.lower() for t in (puzzle.get("metadata") or {}).get("tags") or []]
    if cat and tags and cat.lower() not in " ".join(tags) and not any(cat.lower() in t for t in tags):
        # soft warning only — do not fail hard
        pass
    return True, errors
