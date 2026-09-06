"""LLM extraction of key_clues, replacing the hand-built lexicon matcher.

`key_clues.py` does forward-maximum-matching against a hardcoded word list that
was written for the original ten puzzles. On any other puzzle it degrades to
mechanical segmentation and emits mid-sentence fragments ("住打击", "而我并"),
which makes the 70-point clue-recall half of composite_judge meaningless.

Clues here are the causal elements a correct reconstruction must state. They are
rejected when they already appear in the surface — the Questioner is given the
surface, so such a clue would be free points.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

# Some solutions are a single sentence ("弟弟想要更大的巧克力于是杀死小明") and
# genuinely contain only two causal elements; forcing three would invent one.
MIN_CLUES = 2
# A clue shorter than this can only ever match by exact substring. The judge's
# paraphrase fallback works on character bigrams and needs at least four of them,
# and an N-character clue yields N-1 — so "抽签" (1 bigram) scores zero against an
# answer that says the same thing as "用抽火柴的方式决定谁跳下". That is the game's
# vocabulary leaking into a measurement meant to be about lateral thinking, so
# clues are required to be long enough for the fallback to apply.
MIN_CLUE_CHARS = 5
MAX_CLUES = 6
MAX_CLUE_CHARS = 12
# A clue need not be a verbatim substring of the solution — condensing
# "把亲生女儿卖了" to "卖亲生女儿" is legitimate — but it must be built from the
# solution's own vocabulary, or the model has invented content no answer can match.
MIN_SOLUTION_GROUNDING = 0.6

EXTRACT_PROMPT = """你在为「海龟汤」推理评测标注关键要素。

【汤面】（猜题者可见）：
{surface}

【汤底】（隐藏答案）：
{solution}

请从汤底中提取 {min_clues}–{max_clues} 个**关键要素**，用于判定猜题者的最终答案是否还原了故事。

要求：
1. 每个要素是**因果链上必不可少**的一环——起因、机制、或结果。缺了它，故事就不成立。
2. 只写**汤底有、汤面没有**的信息。猜题者已经知道汤面，写汤面里的词等于白送分。
3. 每个要素是 {min_chars}–{max_chars} 字的短语。**不足 {min_chars} 字的要素必须补足**——
   把「抽签」写成「抽签决定谁跳下」，把「热气球」写成「乘坐热气球穿越沙漠」。
   评分时短于 {min_chars} 字的要素只能逐字匹配，猜题者用别的说法表达同一件事就会判错。
   但仍然不要写成整句，不要加解释。
4. 用汤底原文的词，不要改写成同义词。
5. 不要用「真相」「秘密」「过程」「意识到」这类任何故事都适用的空泛词。

只返回 JSON：{{"clues": ["...", "..."]}}
"""


def _parse_clues(raw: str) -> List[str]:
    text = raw.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not m:
            return []
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return []
    clues = data.get("clues") if isinstance(data, dict) else None
    return [str(c).strip() for c in clues if str(c).strip()] if isinstance(clues, list) else []


def _bigrams(text: str) -> set:
    chars = re.sub(r"\s+", "", text)
    if len(chars) < 2:
        return {chars} if chars else set()
    return {chars[i : i + 2] for i in range(len(chars) - 1)}


def grounding(clue: str, solution: str) -> float:
    """Share of the clue's character bigrams that occur in the solution."""
    bg = _bigrams(clue)
    if not bg:
        return 0.0
    sol = _bigrams(solution)
    return sum(1 for b in bg if b in sol) / len(bg)


def validate_clues(clues: List[str], surface: str, solution: str) -> Tuple[List[str], List[str]]:
    """(kept, rejected-with-reason). Order preserved, duplicates dropped."""
    kept: List[str] = []
    rejected: List[str] = []
    seen = set()
    for c in clues:
        if c in seen:
            rejected.append(f"{c} (重复)")
            continue
        if len(c) < MIN_CLUE_CHARS:
            rejected.append(f"{c} (不足 {MIN_CLUE_CHARS} 字，只能逐字匹配)")
            continue
        if len(c) > MAX_CLUE_CHARS:
            rejected.append(f"{c} (过长)")
            continue
        if c in surface:
            rejected.append(f"{c} (已在汤面中)")
            continue
        g = grounding(c, solution)
        if g < MIN_SOLUTION_GROUNDING:
            rejected.append(f"{c} (与汤底用词脱节 {g:.0%}，疑似臆造)")
            continue
        seen.add(c)
        kept.append(c)
    return kept, rejected


def extract_key_clues_llm(
    surface: str,
    solution: str,
    *,
    rater: Any,
    min_clues: int = MIN_CLUES,
    max_clues: int = MAX_CLUES,
) -> Dict[str, Any]:
    """`rater` is anything with .complete(system=, user=) -> str."""
    prompt = EXTRACT_PROMPT.format(
        surface=surface,
        solution=solution,
        min_clues=min_clues,
        max_clues=max_clues,
        min_chars=MIN_CLUE_CHARS,
        max_chars=MAX_CLUE_CHARS,
    )
    raw = rater.complete(system="你是严谨的推理游戏标注员，只输出 JSON。", user=prompt)
    proposed = _parse_clues(raw)
    kept, rejected = validate_clues(proposed, surface, solution)
    return {"clues": kept, "proposed": proposed, "rejected": rejected}
