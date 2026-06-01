#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from agents.base_agent import ModelConfig
from engine.config import load_app_config
from engine.game import TurtleSoupGame, list_puzzle_ids, load_puzzle
from engine.trajectory import save_trajectory
from evaluation.judge import heuristic_judge
from evaluation.metrics import compute_metrics
from evaluation.report import print_evaluation_report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Batch benchmark for turtle-soup")
    p.add_argument("--puzzles", nargs="+", default=["all"], help="Puzzle ids or 'all'")
    p.add_argument("--questioner-models", nargs="+", required=True)
    p.add_argument("--questioner-provider", default="anthropic")
    p.add_argument("--oracle-model", default="gpt-4o")
    p.add_argument("--oracle-provider", default="openai")
    p.add_argument("--runs-per-combo", type=int, default=1)
    p.add_argument("--output", default="results/benchmark_v1")
    p.add_argument("--mock", action="store_true")
    p.add_argument("--max-rounds", type=int, default=None)
    return p


def resolve_puzzles(names: List[str]) -> List[str]:
    if len(names) == 1 and names[0] == "all":
        return list_puzzle_ids()
    return names


def main() -> int:
    args = build_parser().parse_args()
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    puzzle_ids = resolve_puzzles(args.puzzles)
    summary_rows = []

    for puzzle_id in puzzle_ids:
        puzzle = load_puzzle(puzzle_id)
        for q_model in args.questioner_models:
            for run_idx in range(args.runs_per_combo):
                app = load_app_config()
                if args.mock:
                    app.oracle = ModelConfig(provider="mock", model="mock")
                    app.questioner = ModelConfig(provider="mock", model="mock")
                else:
                    app.oracle = ModelConfig(
                        provider=args.oracle_provider,
                        model=args.oracle_model,
                    )
                    app.questioner = ModelConfig(
                        provider=args.questioner_provider,
                        model=q_model,
                    )
                if args.max_rounds:
                    app.game.max_rounds = args.max_rounds

                game = TurtleSoupGame(puzzle, app_config=app)
                result = game.run(verbose=False)
                traj = result.trajectory

                judge = heuristic_judge(
                    solution=puzzle["solution"],
                    final_answer=traj.final_answer,
                    key_clues=puzzle.get("key_clues", []),
                )
                metrics = compute_metrics(
                    traj, key_clues=puzzle.get("key_clues", []), judge_score=judge.score
                )
                traj.evaluation = {"score": judge.score, **judge.to_dict()}
                if result.trajectory_path:
                    save_trajectory(traj, result.trajectory_path)

                row = {
                    "puzzle_id": puzzle_id,
                    "questioner_model": q_model,
                    "oracle_model": args.oracle_model,
                    "run": run_idx + 1,
                    "score": judge.score,
                    "rounds": traj.total_rounds,
                    "terminated_by": traj.terminated_by,
                    "metrics": metrics.to_dict(),
                    "trajectory_path": str(result.trajectory_path) if result.trajectory_path else None,
                }
                summary_rows.append(row)
                print(
                    f"{puzzle_id} | {q_model} | run {run_idx + 1} | "
                    f"score={judge.score:.2f} rounds={traj.total_rounds}"
                )

    summary_path = out_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary_rows, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {summary_path} ({len(summary_rows)} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
