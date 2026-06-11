from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base_agent import ModelConfig
from agents.questioner_agent import QuestionerInputs
from engine.config import AppConfig, GameConfig
from engine.game import (
    TurtleSoupGame,
    format_qa_history,
    is_final_answer_turn,
    load_puzzle,
    parse_final_answer,
)
from engine.trajectory import RoundRecord
from evaluation.judge import heuristic_judge


@dataclass
class ModelSpec:
    name: str
    provider: str
    model: str


@dataclass
class TimingRecord:
    label: str
    elapsed_s: float
    extra: Dict[str, Any] = field(default_factory=dict)


def _judge_score(puzzle: Dict[str, Any], final_answer: Optional[str]) -> float:
    return heuristic_judge(
        solution=puzzle["solution"],
        final_answer=final_answer,
        key_clues=puzzle.get("key_clues", []),
    ).score


def build_app_config(
    *,
    oracle_provider: str,
    oracle_model: str,
    questioner: ModelSpec,
    max_rounds: int,
    min_rounds_before_answer: int = 0,
    force_final_answer_on_max_rounds: bool = False,
    save_trajectory: bool = False,
) -> AppConfig:
    return AppConfig(
        oracle=ModelConfig(provider=oracle_provider, model=oracle_model),
        questioner=ModelConfig(provider=questioner.provider, model=questioner.model),
        game=GameConfig(
            max_rounds=max_rounds,
            min_rounds_before_answer=min_rounds_before_answer,
            save_trajectory=save_trajectory,
            force_final_answer_on_max_rounds=force_final_answer_on_max_rounds,
        ),
    )


def run_round_curve(
    puzzle: Dict[str, Any],
    *,
    app_config: AppConfig,
    max_checkpoint_round: int = 30,
    oracle_provider: Optional[str] = None,
    questioner_provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Exp 1: play up to max_checkpoint_round; after each round, checkpoint-judge
    the Questioner's best answer so far (extra LLM call per round).
    """
    cfg = app_config.game
    cfg.max_rounds = max_checkpoint_round
    cfg.min_rounds_before_answer = 0
    cfg.force_final_answer_on_max_rounds = False

    game = TurtleSoupGame(
        puzzle,
        app_config=app_config,
        oracle_provider_name=oracle_provider,
        questioner_provider_name=questioner_provider,
    )
    game.game_config = cfg
    game.questioner.inputs = QuestionerInputs(surface=puzzle["surface"], min_questions=0)

    traj_rounds: List[RoundRecord] = []
    accuracy_by_round: Dict[int, float] = {}
    natural_end_round: Optional[int] = None
    natural_final_answer: Optional[str] = None

    for round_idx in range(1, max_checkpoint_round + 1):
        history = format_qa_history(traj_rounds)
        question = game.questioner.next_turn(history)

        if is_final_answer_turn(question):
            parsed = parse_final_answer(question)
            if parsed is not None:
                answer = game.oracle.answer(f"FINAL_ANSWER: {parsed}")
                traj_rounds.append(RoundRecord(round=round_idx, question=question, answer=answer))
                natural_end_round = round_idx
                natural_final_answer = parsed
                for r in range(round_idx, max_checkpoint_round + 1):
                    accuracy_by_round[r] = _judge_score(puzzle, parsed)
                break

        answer = game.oracle.answer(question)
        traj_rounds.append(RoundRecord(round=round_idx, question=question, answer=answer))

        checkpoint = game.questioner.request_final_answer(format_qa_history(traj_rounds))
        checkpoint_answer = parse_final_answer(checkpoint)
        accuracy_by_round[round_idx] = _judge_score(puzzle, checkpoint_answer)

    api_calls = len(traj_rounds) * 3  # question + oracle + checkpoint per round played
    return {
        "puzzle_id": puzzle["id"],
        "accuracy_by_round": accuracy_by_round,
        "natural_end_round": natural_end_round,
        "natural_final_answer": natural_final_answer,
        "total_played_rounds": len(traj_rounds),
        "api_calls_estimate": api_calls,
    }


def run_round_cap(
    puzzle: Dict[str, Any],
    *,
    app_config: AppConfig,
    round_cap: int,
    oracle_provider: Optional[str] = None,
    questioner_provider: Optional[str] = None,
) -> Dict[str, Any]:
    """Exp 2: hard cap at round_cap; force FINAL_ANSWER on last turn if needed."""
    cfg = app_config.game
    cfg.max_rounds = round_cap
    cfg.min_rounds_before_answer = 0
    cfg.force_final_answer_on_max_rounds = True

    game = TurtleSoupGame(
        puzzle,
        app_config=app_config,
        oracle_provider_name=oracle_provider,
        questioner_provider_name=questioner_provider,
    )
    game.game_config = cfg
    game.questioner.inputs = QuestionerInputs(surface=puzzle["surface"], min_questions=0)

    result = game.run(verbose=False)
    traj = result.trajectory
    score = _judge_score(puzzle, traj.final_answer)
    api_calls = traj.total_rounds * 2 + (1 if traj.final_answer else 0)
    return {
        "puzzle_id": puzzle["id"],
        "round_cap": round_cap,
        "score": score,
        "final_answer": traj.final_answer,
        "total_rounds": traj.total_rounds,
        "terminated_by": traj.terminated_by,
        "api_calls_estimate": api_calls,
    }


def run_pilot(
    *,
    puzzle_ids: List[str],
    questioner: ModelSpec,
    oracle_provider: str = "mock",
    oracle_model: str = "mock",
    max_rounds: int = 30,
    round_caps: Optional[List[int]] = None,
    output_dir: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    caps = round_caps or [5, 10, 15, 20, 25, 30]
    timings: List[TimingRecord] = []
    exp1_rows: List[Dict[str, Any]] = []
    exp2_rows: List[Dict[str, Any]] = []

    t_study = time.perf_counter()

    for pid in puzzle_ids:
        puzzle = load_puzzle(pid)

        t0 = time.perf_counter()
        row = run_round_curve(
            puzzle,
            app_config=build_app_config(
                oracle_provider=oracle_provider,
                oracle_model=oracle_model,
                questioner=questioner,
                max_rounds=max_rounds,
            ),
            max_checkpoint_round=max_rounds,
            questioner_provider=questioner.provider,
            oracle_provider=oracle_provider,
        )
        elapsed = time.perf_counter() - t0
        row["elapsed_s"] = round(elapsed, 3)
        exp1_rows.append(row)
        timings.append(TimingRecord(f"exp1:{pid}", elapsed, {"rounds": max_rounds}))

    t_exp1 = time.perf_counter() - t_study

    for cap in caps:
        for pid in puzzle_ids:
            puzzle = load_puzzle(pid)
            t0 = time.perf_counter()
            row = run_round_cap(
                puzzle,
                app_config=build_app_config(
                    oracle_provider=oracle_provider,
                    oracle_model=oracle_model,
                    questioner=questioner,
                    max_rounds=cap,
                ),
                round_cap=cap,
                questioner_provider=questioner.provider,
                oracle_provider=oracle_provider,
            )
            elapsed = time.perf_counter() - t0
            row["elapsed_s"] = round(elapsed, 3)
            exp2_rows.append(row)
            timings.append(TimingRecord(f"exp2:{pid}:cap{cap}", elapsed))

    t_total = time.perf_counter() - t_study
    t_exp2 = t_total - t_exp1

    n_puzzles = len(puzzle_ids)
    n_caps = len(caps)
    # Full study extrapolation: 11 puzzles, 3 models, 3 seeds
    exp1_full_games = 11 * 3 * 3
    exp2_full_games = n_caps * 11 * 3 * 3
    avg_exp1_per_game = t_exp1 / max(n_puzzles, 1)
    avg_exp2_per_game = t_exp2 / max(n_puzzles * n_caps, 1)

    exp1_api = sum(r.get("api_calls_estimate", 0) for r in exp1_rows)
    exp2_api = sum(r.get("api_calls_estimate", 0) for r in exp2_rows)
    sec_per_call = 12.0  # planning estimate for reasoning models (edit per hardware)

    report = {
        "puzzle_ids": puzzle_ids,
        "questioner": questioner.__dict__,
        "oracle": {"provider": oracle_provider, "model": oracle_model},
        "max_rounds": max_rounds,
        "round_caps": caps,
        "api_calls": {
            "exp1_questioner_oracle_checkpoint": exp1_api,
            "exp2_total": exp2_api,
            "pilot_total": exp1_api + exp2_api,
            "full_study_exp1_estimated": int(exp1_api / max(n_puzzles, 1) * exp1_full_games),
            "full_study_exp2_estimated": int(exp2_api / max(n_puzzles * n_caps, 1) * exp2_full_games),
        },
        "timing": {
            "exp1_total_s": round(t_exp1, 3),
            "exp2_total_s": round(t_exp2, 3),
            "total_s": round(t_total, 3),
            "avg_exp1_per_puzzle_s": round(avg_exp1_per_game, 3),
            "avg_exp2_per_game_s": round(avg_exp2_per_game, 3),
            "per_task": [{"label": t.label, "elapsed_s": round(t.elapsed_s, 3), **t.extra} for t in timings],
        },
        "extrapolation_full_study": {
            "assumption": "11 puzzles × 3 models × 3 seeds",
            "wall_clock_mock": {
                "exp1_estimated_h": round(avg_exp1_per_game * exp1_full_games / 3600, 4),
                "exp2_estimated_h": round(avg_exp2_per_game * exp2_full_games / 3600, 4),
            },
            "api_calls_estimated": {
                "exp1": int(exp1_api / max(n_puzzles, 1) * exp1_full_games),
                "exp2": int(exp2_api / max(n_puzzles * n_caps, 1) * exp2_full_games),
                "combined": int(exp1_api / max(n_puzzles, 1) * exp1_full_games)
                + int(exp2_api / max(n_puzzles * n_caps, 1) * exp2_full_games),
            },
            "at_sec_per_call": sec_per_call,
            "exp1_estimated_h": round(
                (exp1_api / max(n_puzzles, 1) * exp1_full_games * sec_per_call) / 3600, 1
            ),
            "exp2_estimated_h": round(
                (exp2_api / max(n_puzzles * n_caps, 1) * exp2_full_games * sec_per_call) / 3600, 1
            ),
            "combined_estimated_h": round(
                (
                    exp1_api / max(n_puzzles, 1) * exp1_full_games
                    + exp2_api / max(n_puzzles * n_caps, 1) * exp2_full_games
                )
                * sec_per_call
                / 3600,
                1,
            ),
        },
        "exp1_results": exp1_rows,
        "exp2_results": exp2_rows,
    }

    out_path = output_dir / "pilot_timing.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    report["output_path"] = str(out_path)
    return report
