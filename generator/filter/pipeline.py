from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .checks import check_category_consistency, check_schema, check_spoil
from .similarity import max_similarity_to_reference


@dataclass
class FilterResult:
    passed: bool
    errors: List[str] = field(default_factory=list)
    similarity_score: Optional[float] = None


def run_filters(
    puzzle: Dict[str, Any],
    *,
    reference_surfaces: Optional[List[str]] = None,
    similarity_threshold: float = 0.85,
) -> FilterResult:
    errors: List[str] = []
    ok, errs = check_schema(puzzle)
    if not ok:
        errors.extend(errs)
    ok, errs = check_spoil(puzzle)
    if not ok:
        errors.extend(errs)
    check_category_consistency(puzzle)

    sim_score = None
    if reference_surfaces:
        sim_score, _ = max_similarity_to_reference(
            puzzle.get("surface") or "", reference_surfaces
        )
        if sim_score >= similarity_threshold:
            errors.append(f"similarity too high vs reference: {sim_score:.3f}")

    return FilterResult(passed=len(errors) == 0, errors=errors, similarity_score=sim_score)
