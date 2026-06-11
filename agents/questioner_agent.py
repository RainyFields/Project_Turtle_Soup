from __future__ import annotations

from dataclasses import dataclass

from .base_agent import BaseAgent, ModelConfig


QUESTIONER_SYSTEM_TEMPLATE = """你正在玩「海龟汤」推理游戏。

【游戏规则】
你只知道以下「汤面」，需要通过提问来还原完整故事。
每次只能提一个问题，出题者只会回答「是」「不是」「与此无关」。
当你认为自己已经掌握了足够的信息，可以用 FINAL_ANSWER: 开头提交最终答案。

【汤面】：
{surface}

【已有问答记录】：
{qa_history}

【提问策略建议】
- 优先确认关键人物、时间、地点的基本事实
- 用假设性问题缩小可能性空间
- 避免重复已问过的问题
- 在 {min_questions} 轮后再考虑提交最终答案

请提出你的下一个问题，或提交最终答案。
"""


@dataclass(frozen=True)
class QuestionerInputs:
    surface: str
    min_questions: int = 5


class QuestionerAgent(BaseAgent):
    def __init__(self, *, provider, model_cfg: ModelConfig, inputs: QuestionerInputs):
        super().__init__(provider=provider, model_cfg=model_cfg)
        self.inputs = inputs

    def next_turn(self, qa_history: str) -> str:
        return self._complete_turn(qa_history, user="请继续。")

    def request_final_answer(self, qa_history: str) -> str:
        user = (
            "根据目前的问答记录，请仅用 FINAL_ANSWER: 开头给出你认为最完整的故事还原，"
            "不要提出新问题。"
        )
        return self._complete_turn(qa_history, user=user)

    def _complete_turn(self, qa_history: str, *, user: str) -> str:
        system = QUESTIONER_SYSTEM_TEMPLATE.format(
            surface=self.inputs.surface,
            qa_history=qa_history.strip() or "(无)",
            min_questions=self.inputs.min_questions,
        )
        out = self.complete(system=system, user=user).strip()
        return out.replace("\n", " ").strip()

