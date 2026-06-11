from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from generator.create.taxonomy import rating_to_difficulty

DEFAULT_MIN_RATING = 8.0
VALID_RATING_MIN = 3.0
VALID_RATING_MAX = 10.0


def is_valid_rating(rating: Any) -> bool:
    if rating is None:
        return False
    try:
        val = float(rating)
    except (TypeError, ValueError):
        return False
    return VALID_RATING_MIN <= val <= VALID_RATING_MAX


def filter_high_rated(
    samples: List[Dict[str, Any]],
    *,
    min_rating: float = DEFAULT_MIN_RATING,
) -> List[Dict[str, Any]]:
    return [
        s
        for s in samples
        if is_valid_rating(s.get("rating")) and float(s["rating"]) >= min_rating
    ]


def _percentile(sorted_vals: List[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    i = min(int(len(sorted_vals) * p), len(sorted_vals) - 1)
    return sorted_vals[i]


def calibrate_rating_thresholds(
    high_rated: List[Dict[str, Any]],
) -> Dict[str, float]:
    """
    Tertile thresholds on the high-rated subset for rating_to_difficulty().
    """
    ratings = sorted(float(s["rating"]) for s in high_rated if is_valid_rating(s.get("rating")))
    if len(ratings) < 6:
        return {"easy_max": 5.0, "medium_max": 8.5}
    return {
        "easy_max": _percentile(ratings, 1 / 3),
        "medium_max": _percentile(ratings, 2 / 3),
    }


def calibrate_difficulty_distribution(
    samples: List[Dict[str, Any]],
    *,
    min_rating: float = DEFAULT_MIN_RATING,
    thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Build difficulty histogram + sampling weights from high-rated reference soups.
    """
    high = filter_high_rated(samples, min_rating=min_rating)
    th = thresholds or calibrate_rating_thresholds(high)

    difficulties: List[str] = []
    for s in high:
        difficulties.append(
            rating_to_difficulty(
                float(s["rating"]) if is_valid_rating(s.get("rating")) else None,
                thresholds=th,
            )
        )

    counts = Counter(difficulties)
    total = sum(counts.values()) or 1
    weights = {d: counts.get(d, 0) / total for d in ("easy", "medium", "hard")}
    # Ensure every bucket exists for random.choices
    for d in ("easy", "medium", "hard"):
        weights.setdefault(d, 0.0)

    rated_all = [s for s in samples if is_valid_rating(s.get("rating"))]
    return {
        "min_rating": min_rating,
        "high_rated_count": len(high),
        "rated_total": len(rated_all),
        "rating_thresholds": th,
        "difficulty_counts": dict(counts),
        "difficulty_weights": weights,
        "avg_rating_high": (
            sum(float(s["rating"]) for s in high) / len(high) if high else None
        ),
    }
