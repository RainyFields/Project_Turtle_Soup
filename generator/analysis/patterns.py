from __future__ import annotations

from typing import Any, Dict, List

from .difficulty import calibrate_difficulty_distribution


def high_rating_patterns(
    samples: List[Dict[str, Any]],
    *,
    min_rating: float = 4.0,
    top_n: int = 50,
) -> Dict[str, Any]:
    """
  Summarize structural patterns from high-rated reference soups.
  Output is statistics/templates only — not verbatim soup text.
  """
    ranked = [s for s in samples if (s.get("rating") or 0) >= min_rating]
    ranked.sort(key=lambda s: float(s.get("rating") or 0), reverse=True)
    ranked = ranked[:top_n]

    surface_lens = [len(s.get("surface") or "") for s in ranked]
    solution_lens = [len(s.get("solution") or "") for s in ranked]

    def pct(xs: List[int], p: float) -> int:
        if not xs:
            return 0
        xs = sorted(xs)
        i = min(int(len(xs) * p), len(xs) - 1)
        return xs[i]

    difficulty_calibration = calibrate_difficulty_distribution(
        samples, min_rating=min_rating
    )
    return {
        "count": len(ranked),
        "min_rating": min_rating,
        "surface_len_p25_p75": [pct(surface_lens, 0.25), pct(surface_lens, 0.75)],
        "solution_len_p25_p75": [pct(solution_lens, 0.25), pct(solution_lens, 0.75)],
        "writing_hints": [
            "汤面只呈现异常现象，不解释因果",
            "汤底包含单一核心反转，关键线索 3–5 条",
            "避免汤面出现汤底专有名词",
        ],
        "difficulty_calibration": difficulty_calibration,
    }
