from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base_agent import ModelConfig
from agents.oracle_agent import OracleAgent, OracleInputs
from agents.provider_factory import get_provider
from agents.questioner_agent import QuestionerAgent, QuestionerInputs

from .config import AppConfig, GameConfig
from .trajectory import GameTrajectory, RoundRecord, _utc_now_iso, new_game_id, save_trajectory


FINAL_ANSWER_PREFIX = "FINAL_ANSWER:"


@dataclass
class GameResult:
    trajectory: GameTrajectory
    trajectory_path: Optional[Path] = None


def load_puzzle(puzzle_id: str, puzzles_dir: Optional[Path] = None) -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    directory = puzzles_dir or (root / "data" / "puzzles")
    path = directory / f"{puzzle_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Puzzle not found: {path}")
    import json

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_puzzle_ids(puzzles_dir: Optional[Path] = None) -> List[str]:
    root = Path(__file__).resolve().parents[1]
    directory = puzzles_dir or (root / "data" / "puzzles")
    return sorted(p.stem for p in directory.glob("turtle_*.json"))


def format_qa_history(rounds: List[RoundRecord]) -> str:
    if not rounds:
        return "(无)"
    lines = []
    for r in rounds:
        lines.append(f"Q{r.round}: {r.question}")
        lines.append(f"A{r.round}: {r.answer}")
    return "\n".join(lines)


def parse_final_answer(text: str) -> Optional[str]:
    if text.strip().upper().startswith(FINAL_ANSWER_PREFIX.upper()):
        return text.split(":", 1)[1].strip()
    m = re.search(r"FINAL_ANSWER:\s*(.+)$", text, flags=re.IGNORECASE)
    return m.group(1).strip() if m else None


def is_final_answer_turn(text: str) -> bool:
    return parse_final_answer(text) is not None


class TurtleSoupGame:
    def __init__(
        self,
        puzzle: Dict[str, Any],
        *,
        app_config: AppConfig,
        oracle_provider_name: Optional[str] = None,
        questioner_provider_name: Optional[str] = None,
        trajectories_dir: Optional[Path] = None,
    ):
        self.puzzle = puzzle
        self.app_config = app_config
        self.game_config: GameConfig = app_config.game
        self.trajectories_dir = trajectories_dir or (
            Path(__file__).resolve().parents[1] / "data" / "trajectories"
        )

        oracle_cfg = app_config.oracle
        questioner_cfg = app_config.questioner
        if oracle_provider_name:
            oracle_cfg = ModelConfig(
                provider=oracle_provider_name,
                model=oracle_cfg.model,
                temperature=oracle_cfg.temperature,
                max_tokens=oracle_cfg.max_tokens,
            )
        if questioner_provider_name:
            questioner_cfg = ModelConfig(
                provider=questioner_provider_name,
                model=questioner_cfg.model,
                temperature=questioner_cfg.temperature,
                max_tokens=questioner_cfg.max_tokens,
            )

        oracle_provider = get_provider(oracle_cfg.provider)
        questioner_provider = get_provider(questioner_cfg.provider)

        self.oracle = OracleAgent(
            provider=oracle_provider,
            model_cfg=oracle_cfg,
            inputs=OracleInputs(surface=puzzle["surface"], solution=puzzle["solution"]),
            debug_mode=self.game_config.debug_mode,
        )
        self.questioner = QuestionerAgent(
            provider=questioner_provider,
            model_cfg=questioner_cfg,
            inputs=QuestionerInputs(
                surface=puzzle["surface"],
                min_questions=self.game_config.min_rounds_before_answer,
            ),
        )
        self._token_estimate = 0

    def _budget_exceeded(self) -> bool:
        return self._token_estimate >= self.game_config.token_budget

    def _record_tokens(self, *texts: str) -> None:
        # rough estimate: 1 token ~ 2 chars for zh/en mix
        for t in texts:
            self._token_estimate += max(1, len(t) // 2)

    def run(self, *, game_id: Optional[str] = None, verbose: bool = True) -> GameResult:
        puzzle_id = self.puzzle["id"]
        gid = game_id or new_game_id(puzzle_id)
        traj = GameTrajectory(
            game_id=gid,
            puzzle_id=puzzle_id,
            oracle_model=f"{self.oracle.model_cfg.provider}/{self.oracle.model_cfg.model}",
            questioner_model=f"{self.questioner.model_cfg.provider}/{self.questioner.model_cfg.model}",
            start_time=_utc_now_iso(),
        )

        if verbose:
            print("🐢 海龟汤游戏开始")
            print(f"📖 汤面：{self.puzzle['surface'][:80]}{'...' if len(self.puzzle['surface']) > 80 else ''}")
            print()

        final_answer: Optional[str] = None
        terminated_by = "max_rounds"

        for round_idx in range(1, self.game_config.max_rounds + 1):
            if self._budget_exceeded():
                terminated_by = "token_budget"
                if verbose:
                    print("⚠️ 已达到 token 预算上限，强制终止")
                break

            history = format_qa_history(traj.trajectory)
            question = self.questioner.next_turn(history)
            self._record_tokens(history, question)

            at_last_round = round_idx == self.game_config.max_rounds
            if (
                at_last_round
                and self.game_config.force_final_answer_on_max_rounds
                and not is_final_answer_turn(question)
            ):
                question = self.questioner.request_final_answer(history)
                self._record_tokens(question)

            if is_final_answer_turn(question):
                if round_idx < self.game_config.min_rounds_before_answer:
                    if verbose:
                        print(
                            f"[Round {round_idx}] Questioner 过早提交答案，继续提问 "
                            f"(最少 {self.game_config.min_rounds_before_answer} 轮)"
                        )
                    question = "请再提出一个有助于缩小假设空间的问题（不要提交最终答案）。"
                    question = self.questioner.next_turn(history + f"\n(系统提示: {question})")
                    self._record_tokens(question)
                    if is_final_answer_turn(question):
                        # still final — accept
                        pass

            parsed = parse_final_answer(question)
            if parsed is not None:
                final_answer = parsed
                answer = self.oracle.answer(f"{FINAL_ANSWER_PREFIX} {final_answer}")
                self._record_tokens(final_answer, answer)
                record = RoundRecord(round=round_idx, question=question, answer=answer)
                traj.add_round(record)
                if verbose:
                    print(f"[Round {round_idx}] Questioner: {question}")
                    print(f"[Round {round_idx}] Oracle: {answer}")
                terminated_by = "final_answer"
                break

            answer = self.oracle.answer(question)
            self._record_tokens(question, answer)
            reasoning = None
            if self.game_config.debug_mode:
                reasoning = f"(debug) Q: {question}"

            record = RoundRecord(
                round=round_idx,
                question=question,
                answer=answer,
                oracle_reasoning=reasoning,
            )
            traj.add_round(record)

            if verbose:
                print(f"[Round {round_idx}] Questioner: {question}")
                print(f"[Round {round_idx}] Oracle: {answer}")
                print()

        traj.finish(terminated_by=terminated_by, final_answer=final_answer)

        path: Optional[Path] = None
        if self.game_config.save_trajectory:
            path = self.trajectories_dir / f"{traj.game_id}.json"
            save_trajectory(traj, path)

        if verbose:
            print(f"✅ 游戏结束（{traj.total_rounds} 轮，终止原因: {terminated_by}）")
            if final_answer:
                print(f"📝 最终答案：{final_answer}")

        return GameResult(trajectory=traj, trajectory_path=path)
