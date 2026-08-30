"""Under-determination: one number for how hard a puzzle is to crack cold.

Depth (how many reframings the solution needs) and breadth (how many stories
the surface admits) were measured separately and both saturated — every puzzle
scored 4/5 on depth and 7-8/8 on breadth, so neither discriminated. They also
were not independent: a surface loose enough to admit many mechanisms is, for
that same reason, one whose single true mechanism takes more reframing to
reach. They are merged here into one continuous quantity.

**Under-determination** = how far the surface alone leaves you from the answer.
Sample N complete stories from the surface with no Oracle and no feedback, and
score each against the real solution by clue recall (objective, no judge model).
A puzzle whose surface pins the story down gets hit by some cold guess; a
puzzle turning on a non-obvious leap does not. The index is 1 - best hit, so
larger means more under-determined, which is the thing both original
dimensions were circling.


Both dimensions describe the *puzzle*, never an agent's performance on it, so
they stay independent of the round counts they will later be plotted against.

The annotator never sees the solution while generating, and the measure never
touches an agent's round count — so it stays independent of the accuracy-vs-
rounds axis it will be plotted against.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

CANDIDATE_PROMPT = """下面是一道「海龟汤」的汤面。汤底你不知道。

【汤面】
{surface}

请提出 {n} 个**机制上互不相同**的完整故事，每个都要能自圆其说地解释汤面的全部细节。

要求：
- 「机制不同」指致死/致因的原理不同，不是换个人名或场景。
- 每个故事一句话，20-60 字，说清「因为什么 → 发生了什么 → 所以出现汤面的景象」。
- 不要写「可能」「也许」，直接陈述。

只返回 JSON：{{"stories": ["...", "..."]}}
"""

DEPTH_PROMPT = """你在为「海龟汤」推理难度做标注。

【汤面】（猜题者可见）
{surface}

【汤底】（隐藏答案）
{solution}

问题：从汤面推到汤底，需要几次**非显然的重新解释**？

「重新解释」指猜题者必须推翻一个自然假设，例如：把日常物品重新理解为别的用途、
把人物关系或身份重新定位、把时间顺序倒过来、把场景整体重新框定。
仅仅补充细节不算。

评分：
1 = 汤面几乎直接指向机制，只需确认细节
2 = 需要一次很自然的联想
3 = 需要一次关键重构，但方向有汤面线索指引
4 = 需要两次重构，或一次几乎无线索指引的重构
5 = 需要多次连环重构，每次都违反直觉

只返回 JSON：{{"depth": 3, "leaps": ["..."], "reason": "..."}}
"""


def _parse_json(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None


def sample_candidate_stories(surface: str, *, rater: Any, n: int = 8) -> List[str]:
    raw = rater.complete(
        system="你是海龟汤推理高手，只输出 JSON。",
        user=CANDIDATE_PROMPT.format(surface=surface, n=n),
    )
    data = _parse_json(raw) or {}
    stories = data.get("stories")
    return [str(s).strip() for s in stories if str(s).strip()] if isinstance(stories, list) else []


def count_distinct(stories: List[str], *, threshold: float = 0.80) -> int:
    """Greedy embedding dedup: how many mechanistically distinct stories remain."""
    if len(stories) <= 1:
        return len(stories)
    from evaluation.trajectory import embed

    vecs = embed(stories)
    kept: List[int] = []
    for i in range(len(stories)):
        if all(float(vecs[i] @ vecs[j]) < threshold for j in kept):
            kept.append(i)
    return len(kept)


DANGLING_PROMPT = """下面是一道「海龟汤」。

【汤面】
{surface}

【汤底】
{solution}

任务：列出汤面中**在知道汤底之前无法解释**的细节。

判定标准：一个细节算「悬置」，当且仅当——只读汤面时，它显得反常、多余或说不通，
必须等汤底揭示的机制出现，它才被解释。日常合理、读汤面时就不觉得奇怪的细节不算。

例：汤面「沙漠里躺着一具男尸，手里紧紧攥着半根火柴，周围散落着行李箱、衣物」
悬置细节 = 半根火柴（为何是半根、为何紧攥）、散落的行李箱、脱下的衣物
——三者都要等「热气球超重抛物、抽签定生死」才能一次性解释。

只返回 JSON：{{"dangling": ["...", "..."], "explained_by": "..."}}
"""


def count_dangling_details(
    surface: str, solution: str, *, rater: Any, samples: int = 3
) -> Dict[str, Any]:
    """How many surface details stay unexplained until the solution lands.

    An alternative to rubric scoring: this is *counted*, so it does not depend
    on the annotator holding a calibrated 1-5 scale in its head.
    """
    counts: List[int] = []
    listings: List[List[str]] = []
    for _ in range(samples):
        try:
            raw = rater.complete(
                system="你是严谨的推理游戏标注员，只输出 JSON。",
                user=DANGLING_PROMPT.format(surface=surface, solution=solution),
            )
        except Exception:
            continue
        data = _parse_json(raw)
        if not data:
            continue
        items = data.get("dangling")
        if isinstance(items, list):
            items = [str(x).strip() for x in items if str(x).strip()]
            counts.append(len(items))
            listings.append(items)
    if not counts:
        return {"dangling_count": None, "samples": [], "items": []}
    ordered = sorted(counts)
    median = ordered[len(ordered) // 2]
    return {
        "dangling_count": median,
        "samples": counts,
        "spread": max(counts) - min(counts),
        "items": listings[counts.index(median)],
    }


def under_determination(
    surface: str,
    solution: str,
    key_clues: List[str],
    *,
    rater: Any,
    n: int = 12,
) -> Dict[str, Any]:
    """Score N cold guesses at the puzzle; return the merged index and its parts.

    Closeness is embedding similarity to the solution, not clue recall: a cold
    guess that reaches the right mechanism in its own words ("抽火柴定谁跳下"
    against the clue "抽签") scores zero under string matching, which would make
    the index measure vocabulary rather than difficulty.
    """
    from evaluation.trajectory import embed

    stories = sample_candidate_stories(surface, rater=rater, n=n)
    if not stories:
        return {"index": None, "stories": [], "scores": []}

    vecs = embed(stories + [solution])
    sol = vecs[-1]
    scores = [float(vecs[i] @ sol) for i in range(len(stories))]
    best = max(scores)
    return {
        "index": round(1.0 - best, 4),      # larger = harder to reach cold
        "cold_best": round(best, 4),
        "cold_mean": round(sum(scores) / len(scores), 4),
        "hits": sum(1 for x in scores if x >= 0.75),
        "n": len(stories),
        "distinct": count_distinct(stories),
        "scores": [round(x, 3) for x in scores],
        "stories": stories,
    }


def rate_depth(surface: str, solution: str, *, rater: Any, samples: int = 3) -> Dict[str, Any]:
    scores: List[int] = []
    leaps: List[List[str]] = []
    reasons: List[str] = []
    for _ in range(samples):
        try:
            raw = rater.complete(
                system="你是严谨的推理难度标注员，只输出 JSON。",
                user=DEPTH_PROMPT.format(surface=surface, solution=solution),
            )
        except Exception:
            continue
        data = _parse_json(raw)
        if not data:
            continue
        try:
            d = int(data.get("depth"))
        except (TypeError, ValueError):
            continue
        if 1 <= d <= 5:
            scores.append(d)
            leaps.append([str(x) for x in (data.get("leaps") or [])])
            reasons.append(str(data.get("reason", "")))
    if not scores:
        return {"depth": None, "samples": [], "leaps": [], "reason": ""}
    ordered = sorted(scores)
    median = ordered[len(ordered) // 2]
    best = scores.index(median)
    return {
        "depth": median,
        "samples": scores,
        "spread": max(scores) - min(scores),
        "leaps": leaps[best],
        "reason": reasons[best],
    }
