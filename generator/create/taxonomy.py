from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# Tags as shown on https://soup.ahelumos.com/ filter panel
AHELMOS_TAGS = (
    "红汤",
    "搞笑",
    "恐怖",
    "原创",
    "经典",
    "非本格汤",
    "清汤",
    "黑汤",
    "规则怪谈",
)

STYLE_TAGS = frozenset({"红汤", "清汤", "黑汤"})
THEME_TAGS = frozenset({"恐怖", "搞笑", "经典", "规则怪谈", "非本格汤", "原创"})

# Maps site tag → benchmark `category` field (English slug for prompts / schema)
TAG_TO_CATEGORY: Dict[str, str] = {
    "恐怖": "horror",
    "经典": "classic",
    "搞笑": "comedy",
    "规则怪谈": "rule_horror",
    "清汤": "everyday",
    "红汤": "horror",
    "黑汤": "horror",
    "非本格汤": "non_standard",
    "原创": "original",
}

# Human-readable hints injected into generation prompt
STYLE_HINTS: Dict[str, str] = {
    "红汤": "红汤：血腥/重口反转，汤面可含死亡/暴力暗示但不明说",
    "清汤": "清汤：日常场景+细思极恐，避免血腥描写",
    "黑汤": "黑汤：黑暗压抑，心理/伦理边界",
}

THEME_HINTS: Dict[str, str] = {
    "恐怖": "恐怖向",
    "搞笑": "搞笑/无厘头，但汤底需逻辑自洽",
    "经典": "经典海龟汤结构：短汤面+意外反转",
    "规则怪谈": "规则怪谈：多条规则，违反即危险",
    "非本格汤": "非本格：允许超自然/时空/身份诡计",
    "原创": "原创设定，避免复刻经典原题",
}


def tags_to_category(tags: List[str]) -> str:
    for tag in tags:
        if tag in TAG_TO_CATEGORY and tag not in STYLE_TAGS:
            return TAG_TO_CATEGORY[tag]
    for tag in tags:
        if tag in TAG_TO_CATEGORY:
            return TAG_TO_CATEGORY[tag]
    return "mystery"


def tags_to_metadata_tags(tags: List[str]) -> List[str]:
    out: List[str] = []
    for tag in tags:
        slug = TAG_TO_CATEGORY.get(tag, tag)
        if slug not in out:
            out.append(slug)
    return out or ["mystery"]


def pick_style_and_theme(tags: List[str]) -> Tuple[Optional[str], Optional[str]]:
    style = next((t for t in tags if t in STYLE_TAGS), None)
    theme = next((t for t in tags if t in THEME_TAGS and t != "原创"), None)
    return style, theme


def build_prompt_hints(tags: List[str]) -> str:
    style, theme = pick_style_and_theme(tags)
    parts: List[str] = []
    if style and style in STYLE_HINTS:
        parts.append(STYLE_HINTS[style])
    if theme and theme in THEME_HINTS:
        parts.append(THEME_HINTS[theme])
    if "原创" in tags:
        parts.append(THEME_HINTS["原创"])
    return "；".join(parts) if parts else "通用海龟汤"


def rating_to_difficulty(
    rating: Optional[float],
    *,
    thresholds: Optional[Dict[str, float]] = None,
) -> str:
    if rating is None:
        return "medium"
    easy_max = 5.0
    medium_max = 8.5
    if thresholds:
        easy_max = float(thresholds.get("easy_max", easy_max))
        medium_max = float(thresholds.get("medium_max", medium_max))
    if rating >= medium_max:
        return "hard"
    if rating >= easy_max:
        return "medium"
    return "easy"
