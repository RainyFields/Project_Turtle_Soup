from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from .taxonomy import (
    AHELMOS_TAGS,
    TAG_TO_CATEGORY,
    build_prompt_hints,
    rating_to_difficulty,
    tags_to_category,
    tags_to_metadata_tags,
)

DEFAULT_CATEGORIES = [
    "horror",
    "classic",
    "comedy",
    "rule_horror",
    "everyday",
    "mystery",
    "non_standard",
]

DEFAULT_DIFFICULTIES = ["easy", "medium", "hard"]

DEFAULT_DIFFICULTY_WEIGHTS = {"easy": 1 / 3, "medium": 1 / 3, "hard": 1 / 3}


def _weighted_tag_choice(tag_histogram: Dict[str, int]) -> List[str]:
    """Sample 1–2 tags weighted by reference corpus frequency."""
    pool = [t for t in AHELMOS_TAGS if tag_histogram.get(t, 0) > 0]
    if not pool:
        primary = random.choice(list(AHELMOS_TAGS))
        return [primary]

    weights = [tag_histogram.get(t, 1) for t in pool]
    primary = random.choices(pool, weights=weights, k=1)[0]
    tags = [primary]

    # Optionally add a style tag (红/清/黑)
    style_pool = [t for t in ("红汤", "清汤", "黑汤") if t != primary and tag_histogram.get(t, 0) > 0]
    if style_pool and random.random() < 0.45:
        sw = [tag_histogram.get(t, 1) for t in style_pool]
        tags.append(random.choices(style_pool, weights=sw, k=1)[0])
    return tags


def sample_difficulty(
    calibration: Optional[Dict[str, Any]] = None,
    *,
    aggregate_stats: Optional[Dict[str, Any]] = None,
    difficulties: Optional[List[str]] = None,
) -> str:
    """
    Sample difficulty from high-rated calibrated weights, else uniform.
    """
    diffs = difficulties or DEFAULT_DIFFICULTIES
    weights_map: Optional[Dict[str, float]] = None
    thresholds: Optional[Dict[str, float]] = None

    if calibration:
        weights_map = calibration.get("difficulty_weights")
        thresholds = calibration.get("rating_thresholds")

    if not weights_map and aggregate_stats:
        weights_map = aggregate_stats.get("difficulty_weights")
        thresholds = aggregate_stats.get("rating_thresholds")

    if weights_map:
        labels = [d for d in diffs if weights_map.get(d, 0) > 0]
        if labels:
            w = [weights_map[d] for d in labels]
            return random.choices(labels, weights=w, k=1)[0]

    if aggregate_stats:
        avg = _avg_rating_for_tags(aggregate_stats, [])
        if avg is None:
            by_tag = aggregate_stats.get("rating_by_tag") or {}
            if by_tag:
                avg = sum(by_tag.values()) / len(by_tag)
        if avg is not None:
            return rating_to_difficulty(avg, thresholds=thresholds)

    return random.choice(diffs)


def sample_slot(
    categories: List[str] | None = None,
    difficulties: List[str] | None = None,
    *,
    aggregate_stats: Optional[Dict[str, Any]] = None,
    difficulty_calibration: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str, List[str], str]:
    """
    Return (category, difficulty, source_tags, prompt_hints).
    When aggregate_stats contains tag_histogram from ahelumos crawl, sample tags from it.
    Difficulty is sampled from high-rated calibration when available.
    """
    tag_histogram: Dict[str, int] = {}
    if aggregate_stats:
        tag_histogram = dict(aggregate_stats.get("tag_histogram") or {})

    if tag_histogram:
        source_tags = _weighted_tag_choice(tag_histogram)
        category = tags_to_category(source_tags)
        hints = build_prompt_hints(source_tags)
        difficulty = sample_difficulty(
            difficulty_calibration,
            aggregate_stats=aggregate_stats,
            difficulties=difficulties,
        )
    else:
        cats = categories or DEFAULT_CATEGORIES
        category = random.choice(cats)
        source_tags = [t for t in AHELMOS_TAGS if TAG_TO_CATEGORY.get(t) == category][:1]
        if not source_tags:
            source_tags = [random.choice(list(AHELMOS_TAGS))]
        hints = build_prompt_hints(source_tags)
        difficulty = sample_difficulty(
            difficulty_calibration,
            aggregate_stats=aggregate_stats,
            difficulties=difficulties,
        )

    return category, difficulty, source_tags, hints


def _avg_rating_for_tags(stats: Dict[str, Any], tags: List[str]) -> Optional[float]:
    by_tag = stats.get("rating_by_tag") or {}
    vals: List[float] = []
    for t in tags:
        v = by_tag.get(t)
        if v is not None:
            vals.append(float(v))
    return sum(vals) / len(vals) if vals else None


def slot_to_metadata_tags(source_tags: List[str]) -> List[str]:
    return tags_to_metadata_tags(source_tags)
