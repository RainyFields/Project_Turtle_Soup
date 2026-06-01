from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from agents.base_agent import ModelConfig
from agents.provider_factory import get_provider
from agents.base_agent import BaseAgent


JUDGE_PROMPT = """你是海龟汤游戏的裁判。请比较猜题者的最终答案和标准汤底，给出 0-1 的分数。

【标准汤底】：{solution}
【猜题者答案】：{final_answer}
【关键要素】：{key_clues}

评分标准：
- 1.0：完全正确，所有关键要素都涵盖
- 0.7-0.9：核心逻辑正确，少数细节缺失
- 0.4-0.6：抓住了部分线索，但逻辑有明显缺失
- 0.1-0.3：有些相关猜测，但整体方向错误
- 0.0：完全错误

请只返回 JSON：{{"score": 0.85, "reasoning": "...", "hit_elements": [...], "missed_elements": [...]}}
"""


@dataclass
class JudgeResult:
    score: float
    reasoning: str
    hit_elements: List[str]
    missed_elements: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "judge_notes": self.reasoning,
            "key_elements_hit": self.hit_elements,
            "key_elements_missed": self.missed_elements,
        }


def _parse_judge_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def _clue_matches_answer(clue: str, answer: str) -> bool:
    if not clue:
        return False
    if clue in answer:
        return True
    tokens = [t for t in re.findall(r"[\u4e00-\u9fff]{2,}", clue) if len(t) >= 2]
    if not tokens:
        return False
    hits = sum(1 for t in tokens if t in answer)
    return hits >= max(1, (len(tokens) + 1) // 2)


def heuristic_judge(
    *,
    solution: str,
    final_answer: Optional[str],
    key_clues: List[str],
) -> JudgeResult:
    if not final_answer:
        return JudgeResult(
            score=0.0,
            reasoning="未提交最终答案",
            hit_elements=[],
            missed_elements=list(key_clues),
        )

    hit = [c for c in key_clues if c and _clue_matches_answer(c, final_answer)]
    missed = [c for c in key_clues if c and c not in hit]
    ratio = (len(hit) / len(key_clues)) if key_clues else 0.0

    # boost if solution keywords appear
    solution_terms = [w for w in re.split(r"[\s，。；、]+", solution) if len(w) >= 2][:20]
    sol_hits = sum(1 for w in solution_terms if w in final_answer)
    boost = min(0.2, sol_hits * 0.02)
    score = min(1.0, ratio * 0.8 + boost + (0.1 if ratio >= 0.5 else 0))

    return JudgeResult(
        score=round(score, 2),
        reasoning="启发式评分（基于 key_clues 子串匹配）",
        hit_elements=hit,
        missed_elements=missed,
    )


class LLMJudge(BaseAgent):
    def __init__(self, *, provider_name: str = "openai", model: str = "gpt-4o"):
        provider = get_provider(provider_name)
        super().__init__(provider=provider, model_cfg=ModelConfig(provider=provider_name, model=model))

    def judge(
        self,
        *,
        solution: str,
        final_answer: Optional[str],
        key_clues: List[str],
        use_llm: bool = True,
    ) -> JudgeResult:
        if not use_llm or not final_answer:
            return heuristic_judge(solution=solution, final_answer=final_answer, key_clues=key_clues)

        prompt = JUDGE_PROMPT.format(
            solution=solution,
            final_answer=final_answer,
            key_clues=", ".join(key_clues),
        )
        try:
            raw = self.complete(system="你是严格的海龟汤裁判。", user=prompt)
            data = _parse_judge_json(raw)
            return JudgeResult(
                score=float(data.get("score", 0)),
                reasoning=str(data.get("reasoning", "")),
                hit_elements=list(data.get("hit_elements", [])),
                missed_elements=list(data.get("missed_elements", [])),
            )
        except Exception:
            return heuristic_judge(solution=solution, final_answer=final_answer, key_clues=key_clues)
