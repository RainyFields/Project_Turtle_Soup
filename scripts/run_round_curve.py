#!/usr/bin/env python3
"""Exp 1 standalone CLI: round-curve study (checkpoint accuracy per round)."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

import time

from evaluation.round_studies import JudgeSpec, ModelSpec, build_app_config, run_round_curve
from evaluation.study_report_html import write_json_and_html
from engine.game import load_puzzle


def add_common_study_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--puzzles", nargs="+", default=["refsoup_008"])
    p.add_argument("--questioner-provider", default="mock")
    p.add_argument("--questioner-model", default="mock")
    p.add_argument("--oracle-provider", default="mock")
    p.add_argument("--oracle-model", default="mock")
    p.add_argument("--seeds", nargs="+", type=int, default=[0], help="Recorded per run")
    p.add_argument("--mock", action="store_true", help="Force mock providers for both agents")
    p.add_argument("--judge", choices=["heuristic", "composite"], default="heuristic")
    p.add_argument("--judge-provider", default=None, help="Logic rater for composite judge")
    p.add_argument("--judge-model", default=None)
    p.add_argument("--logic-samples", type=int, default=3)
    p.add_argument("--output", default=None)


def build_judge_spec(args: argparse.Namespace) -> JudgeSpec:
    return JudgeSpec(
        mode=args.judge,
        provider=args.judge_provider,
        model=args.judge_model,
        logic_samples=args.logic_samples,
    )


def resolve_models(args: argparse.Namespace) -> ModelSpec:
    if args.mock:
        args.questioner_provider = args.questioner_model = "mock"
        args.oracle_provider = args.oracle_model = "mock"
    return ModelSpec(
        name=args.questioner_model,
        provider=args.questioner_provider,
        model=args.questioner_model,
    )


def main() -> int:
    p = argparse.ArgumentParser(description="Exp 1: checkpoint accuracy by round")
    add_common_study_args(p)
    p.add_argument("--max-rounds", type=int, default=30)
    args = p.parse_args()

    questioner = resolve_models(args)
    judge = build_judge_spec(args)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output) if args.output else ROOT / "results" / "round_curve" / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for seed in args.seeds:
        for pid in args.puzzles:
            puzzle = load_puzzle(pid)
            app = build_app_config(
                oracle_provider=args.oracle_provider,
                oracle_model=args.oracle_model,
                questioner=questioner,
                max_rounds=args.max_rounds,
            )
            app.game.seed = seed
            t0 = time.perf_counter()
            row = run_round_curve(
                puzzle,
                app_config=app,
                max_checkpoint_round=args.max_rounds,
                oracle_provider=args.oracle_provider,
                questioner_provider=questioner.provider,
                judge=judge,
            )
            row["seed"] = seed
            row["questioner"] = questioner.__dict__
            row["elapsed_s"] = round(time.perf_counter() - t0, 3)
            rows.append(row)
            print(
                f"[curve] {pid} seed={seed}: rounds={row['total_played_rounds']} "
                f"end={row['natural_end_round']} ({row['elapsed_s']}s)"
            )

    report = {
        "study": "round_curve",
        "max_rounds": args.max_rounds,
        "puzzle_ids": args.puzzles,
        "seeds": args.seeds,
        "questioner": questioner.__dict__,
        "oracle": {"provider": args.oracle_provider, "model": args.oracle_model},
        "judge": judge.to_dict(),
        "results": rows,
    }
    out_path = out_dir / "round_curve.json"
    html_path = write_json_and_html(report, out_path, title="Round Curve Study (Exp 1)")
    print(f"Report: {out_path}")
    print(f"HTML:   {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
