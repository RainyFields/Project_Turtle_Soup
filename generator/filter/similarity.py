from __future__ import annotations

from typing import Dict, List, Tuple


def char_ngrams(text: str, n: int = 3) -> set:
    text = "".join(text.split())
    if len(text) < n:
        return {text} if text else set()
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def max_similarity_to_reference(
    surface: str,
    reference_surfaces: List[str],
    *,
    n: int = 3,
) -> Tuple[float, int]:
    """Return (max_score, index_of_nearest)."""
    probe = char_ngrams(surface, n)
    best, idx = 0.0, -1
    for i, ref in enumerate(reference_surfaces):
        score = jaccard(probe, char_ngrams(ref, n))
        if score > best:
            best, idx = score, i
    return best, idx
