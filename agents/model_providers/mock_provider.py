from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional


# Scripted questions for offline demo (turtle_001-style puzzles)
_TURTLE_SOUP_QUESTIONS: List[str] = [
    "男人的自杀和这碗海龟汤有直接关系吗？",
    "男人以前也喝过类似的汤吗？",
    "他们曾经历过海难吗？",
    "妻子还在人世吗？",
    "当年喝下的汤和真正的海龟汤味道不同吗？",
]

_ELEVATOR_QUESTIONS: List[str] = [
    "矮个子是因为身高问题才在中途下电梯吗？",
    "他住在顶层吗？",
    "下雨天他会带伞吗？",
    "伞可以帮助他按到更高楼层的按钮吗？",
    "平时他是因为够不到顶层按钮才走楼梯吗？",
]

_FINAL_TURTLE_SOUP = (
    "FINAL_ANSWER: 男人曾在海难中喝过并非真正海龟汤的汤，"
    "今天在餐厅喝到真海龟汤后发现味道不同，意识到可怕真相后自杀。"
)
_FINAL_ELEVATOR = (
    "FINAL_ANSWER: 矮个子够不到电梯顶层按钮，只能按中途楼层后走楼梯；"
    "下雨天带伞，用伞柄可以按到顶层按钮。"
)

_ORACLE_KEYWORDS_YES = ["海难", "妻子", "味道", "以前", "不同", "自杀", "汤", "身高", "伞", "顶层", "按钮", "矮"]
_ORACLE_KEYWORDS_NO = ["餐厅", "出了意外", "被下毒", "外星人", "鬼魂"]


class MockProvider:
    """
    Deterministic provider for tests and offline runs.
    """

    _questioner_round: int = 0
    _generator_idx: int = 0

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
        category_m = re.search(r"分类[：:]\s*(\S+)", user)
        difficulty_m = re.search(r"难度[：:]\s*(\S+)", user)
        category = category_m.group(1) if category_m else "mystery"
        difficulty = difficulty_m.group(1) if difficulty_m else "medium"
        idx = MockProvider._generator_idx
        MockProvider._generator_idx += 1

        surfaces = [
            "深夜，独居的我听到衣柜里传来敲击声。我打开柜门，里面空无一物，敲击却停了。",
            "快递员把包裹放在门口后离开，主人开门却发现包裹不见了，监控里没有人靠近。",
            "一个男人在沙漠中醒来，身边只有一瓶水。他喝了一口后哭了。",
            "图书馆里一本书永远没人借走，但每天管理员都会把它放回书架原位。",
            "女子收到一束花，高兴插进花瓶。第二天花枯萎了，她却报警了。",
            "电梯每到13层都会停一下，但从未有人进出。",
            "画家完成最后一笔后立刻销毁了作品，观众却鼓掌称赞。",
        ]
        solutions = [
            "敲击来自邻居装修；柜门打开后声波路径改变，所以我以为停了。",
            "包裹是冰做的，放在门口很快融化消失，监控拍不到融化过程。",
            "瓶里装的是海水，他意识到自己其实在海边而非沙漠。",
            "书是图书馆的占位假书，用于撑开书架防止倒塌，每天都要归位。",
            "花束里藏着窃听器，花枯说明装置失效，她担心被监视而报警。",
            "13层是设备层，电梯自检会短暂停靠，并非闹鬼。",
            "观众看的是投影草稿，真迹被画家藏起来用于保险索赔。",
        ]
        i = idx % len(surfaces)
        puzzle = {
            "id": f"turtle_candidate_{idx + 1:03d}",
            "title": f"Mock原创汤 #{idx + 1}",
            "difficulty": difficulty,
            "category": category,
            "surface": surfaces[i],
            "solution": solutions[i],
            "key_clues": [
                "表面现象与直觉不符",
                "关键在环境或时间因素",
                "答案可逻辑自洽",
            ],
            "oracle_rules": {
                "answerable_topics": ["时间", "环境", "人物动机"],
                "forbidden_reveal": [],
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

    def _script_for_surface(self, system: str) -> tuple[List[str], str]:
        if "电梯" in system:
            return _ELEVATOR_QUESTIONS, _FINAL_ELEVATOR
        return _TURTLE_SOUP_QUESTIONS, _FINAL_TURTLE_SOUP

    def _questioner_turn(self, system: str, user: str) -> str:
        questions, final_answer = self._script_for_surface(system)
        rounds = len(re.findall(r"^Q\d+:", system + "\n" + user, flags=re.MULTILINE))
        if "FINAL_ANSWER" in user or "最完整的故事" in user:
            return final_answer
        if rounds >= len(questions):
            return final_answer
        idx = min(rounds, len(questions) - 1)
        MockProvider._questioner_round = rounds + 1
        return questions[idx]
