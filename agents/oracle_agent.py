from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base_agent import BaseAgent, ModelConfig


ORACLE_SYSTEM_TEMPLATE = """你是「海龟汤」游戏的出题者（汤主）。

【汤面】（猜题者知道）：
{surface}

【汤底】（只有你知道，绝对不能直接透露）：
{solution}

游戏规则：
1. 猜题者会向你提问，你只能回答以下三种之一：
   - "是"：问题描述符合汤底事实
   - "不是"：问题描述与汤底事实相悖
   - "与此无关"：问题所问的内容对解谜没有帮助，或与故事无关
2. 你不能主动透露汤底的核心线索
3. 你不能回答超出是/否/无关范围的任何内容
4. 如果猜题者提交了最终答案（以 FINAL_ANSWER: 开头），你需要判断其是否基本正确，并仅输出：
   - "是"（基本正确）或 "不是"（不正确）

请严格遵守以上规则。
"""


@dataclass(frozen=True)
class OracleInputs:
    surface: str
    solution: str


class OracleAgent(BaseAgent):
    def __init__(self, *, provider, model_cfg: ModelConfig, inputs: OracleInputs, debug_mode: bool = False):
        super().__init__(provider=provider, model_cfg=model_cfg)
        self.inputs = inputs
        self.debug_mode = debug_mode

    def answer(self, question_or_final: str) -> str:
        system = ORACLE_SYSTEM_TEMPLATE.format(surface=self.inputs.surface, solution=self.inputs.solution)
        user = question_or_final.strip()
        out = self.complete(system=system, user=user)

        # Hard clamp to allowed outputs
        allowed = {"是", "不是", "与此无关"}
        if out in allowed:
            return out
        # Try to extract first matching token
        for tok in ["与此无关", "不是", "是"]:
            if tok in out:
                return tok
        return "与此无关"

