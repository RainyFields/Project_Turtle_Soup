from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List

from .difficulty import calibrate_difficulty_distribution


def extract_record_features(sample: Dict[str, Any]) -> Dict[str, Any]:
    surface = sample.get("surface") or ""
    solution = sample.get("solution") or ""
    return {
        "surface_len": len(surface),
        "solution_len": len(solution),
        "category": sample.get("category") or "unknown",
        "rating": sample.get("rating"),
        "tag_count": len(sample.get("tags") or []),
    }


def aggregate_features(
    samples: List[Dict[str, Any]],
    *,
    min_rating: float = 8.0,
) -> Dict[str, Any]:
    by_cat: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    ratings: List[float] = []
    tag_ratings: Dict[str, List[float]] = defaultdict(list)
    for s in samples:
        feat = extract_record_features(s)
        by_cat[feat["category"]].append(feat)
        r = feat.get("rating")
        if r is not None:
            ratings.append(float(r))
            for tag in s.get("tags") or []:
                tag_ratings[str(tag)].append(float(r))

    def avg(key: str, rows: List[Dict[str, Any]]) -> float:
        vals = [r[key] for r in rows if r.get(key) is not None]
        return sum(vals) / len(vals) if vals else 0.0

    category_stats = {
        cat: {
            "count": len(rows),
            "avg_surface_len": avg("surface_len", rows),
            "avg_solution_len": avg("solution_len", rows),
        }
        for cat, rows in by_cat.items()
    }
    rating_by_tag = {
        tag: sum(vals) / len(vals) for tag, vals in tag_ratings.items() if vals
    }
    difficulty_calibration = calibrate_difficulty_distribution(
        samples, min_rating=min_rating
    )
    return {
        "total": len(samples),
        "category_stats": category_stats,
        "tag_histogram": dict(Counter(t for s in samples for t in (s.get("tags") or []))),
        "rating_by_tag": rating_by_tag,
        "difficulty_calibration": difficulty_calibration,
        "difficulty_weights": difficulty_calibration.get("difficulty_weights"),
        "rating_thresholds": difficulty_calibration.get("rating_thresholds"),
    }
