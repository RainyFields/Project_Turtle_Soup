from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional


# Scripted questions for offline demo (turtle_001-style puzzles)
_SCRIPTED_QUESTIONS: List[str] = [
    "男人的自杀和这碗海龟汤有直接关系吗？",
    "男人以前也喝过类似的汤吗？",
    "他们曾经历过海难吗？",
    "妻子还在人世吗？",
    "当年喝下的汤和真正的海龟汤味道不同吗？",
]

_ORACLE_KEYWORDS_YES = ["海难", "妻子", "味道", "以前", "不同", "自杀", "汤"]
_ORACLE_KEYWORDS_NO = ["餐厅", "出了意外", "被下毒", "外星人"]


class MockProvider:
    """
    Deterministic provider for tests and offline runs.
    """

    _questioner_round: int = 0

    def generate(
        self,
        *,
        system: str,
        user: str,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 512,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        _ = (model, temperature, max_tokens, extra)

        if "你正在玩「海龟汤」推理游戏" in system:
            return self._questioner_turn(system, user)

        if "你是「海龟汤」游戏的出题者" in system or "（汤主）" in system:
            return self._oracle_answer(user)

        if "海龟汤出题专家" in system or "输出必须是单个 JSON 对象" in system:
            return self._generate_puzzle_json(user)

        return user.strip()[:200]

    def _generate_puzzle_json(self, user: str) -> str:
        category_m = re.search(r"分类：(\S+)", user)
        difficulty_m = re.search(r"难度：(\S+)", user)
        category = category_m.group(1) if category_m else "mystery"
        difficulty = difficulty_m.group(1) if difficulty_m else "medium"
        idx = MockProvider._questioner_round
        MockProvider._questioner_round += 1

        puzzle = {
            "id": f"turtle_candidate_{idx + 1:03d}",
            "title": f"Mock原创汤 #{idx + 1}",
            "difficulty": difficulty,
            "category": category,
            "surface": "深夜，独居的我听到衣柜里传来敲击声。我打开柜门，里面空无一物，敲击却停了。",
            "solution": "敲击来自邻居装修；柜门打开后声波路径改变，所以我以为停了。",
            "key_clues": [
                "声音在深夜出现",
                "打开柜门后声音停止",
                "柜内没有可见声源",
                "邻居可能在装修",
            ],
            "oracle_rules": {
                "answerable_topics": ["声音来源", "邻居", "柜门", "时间"],
                "forbidden_reveal": ["声波", "装修"],
            },
            "metadata": {"source": "generated", "language": "zh", "tags": [category]},
        }
        return json.dumps(puzzle, ensure_ascii=False)

    def _oracle_answer(self, user: str) -> str:
        if user.upper().startswith("FINAL_ANSWER"):
            if any(k in user for k in ["海难", "味道", "海龟汤", "妻子"]):
                return "是"
            return "不是"

        for kw in _ORACLE_KEYWORDS_NO:
            if kw in user:
                return "不是"
        for kw in _ORACLE_KEYWORDS_YES:
            if kw in user:
                return "是"
        return "与此无关"

    def _questioner_turn(self, system: str, user: str) -> str:
        # Count completed Q/A pairs in history
        rounds = len(re.findall(r"^Q\d+:", system + "\n" + user, flags=re.MULTILINE))
        if rounds >= len(_SCRIPTED_QUESTIONS):
            return (
                "FINAL_ANSWER: 男人曾在海难中喝过并非真正海龟汤的汤，"
                "今天在餐厅喝到真海龟汤后发现味道不同，意识到可怕真相后自杀。"
            )
        idx = min(rounds, len(_SCRIPTED_QUESTIONS) - 1)
        MockProvider._questioner_round = rounds + 1
        return _SCRIPTED_QUESTIONS[idx]
