#!/usr/bin/env python3
"""Exp 2 standalone CLI: round-cap sweep (end accuracy under a fixed budget)."""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from engine.game import load_puzzle
from evaluation.round_studies import ModelSpec, build_app_config, run_round_cap
from evaluation.study_report_html import write_json_and_html
from scripts.run_round_curve import (
    add_common_study_args,
    build_judge_spec,
    require_cross_family,
    resolve_models,
)


def main() -> int:
    p = argparse.ArgumentParser(description="Exp 2: end accuracy vs round cap")
    add_common_study_args(p)
    p.add_argument("--round-caps", nargs="+", type=int, default=[5, 10, 15, 20, 25, 30])
    args = p.parse_args()

    # Without this, omitting the providers silently produced a full run of mock
    # data that looks like a result. --mock stays available for pipeline checks.
    if not args.mock and not (args.questioner_provider and args.oracle_provider):
        p.error(
            "--questioner-provider and --oracle-provider are required "
            "(or pass --mock for an offline pipeline check)"
        )
    require_cross_family(p, args)

    questioner = resolve_models(args)
    judge = build_judge_spec(args)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output) if args.output else ROOT / "results" / "round_cap" / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for seed in args.seeds:
        for cap in args.round_caps:
            for pid in args.puzzles:
                puzzle = load_puzzle(pid)
                app = build_app_config(
                    oracle_provider=args.oracle_provider,
                    oracle_model=args.oracle_model,
                    questioner=questioner,
                    max_rounds=cap,
                    force_final_answer_on_max_rounds=True,
                )
                app.game.seed = seed
                t0 = time.perf_counter()
                row = run_round_cap(
                    puzzle,
                    app_config=app,
                    round_cap=cap,
                    oracle_provider=args.oracle_provider,
                    questioner_provider=questioner.provider,
                    judge=judge,
                )
                row["seed"] = seed
                row["questioner"] = questioner.__dict__
                row["elapsed_s"] = round(time.perf_counter() - t0, 3)
                rows.append(row)
                print(
                    f"[cap] {pid} seed={seed} cap={cap}: score={row['score']:.2f} "
                    f"rounds={row['total_rounds']} by={row['terminated_by']} "
                    f"({row['elapsed_s']}s)"
                )

    report = {
        "study": "round_cap_sweep",
        "round_caps": args.round_caps,
        "puzzle_ids": args.puzzles,
        "seeds": args.seeds,
        "questioner": questioner.__dict__,
        "oracle": {"provider": args.oracle_provider, "model": args.oracle_model},
        "judge": judge.to_dict(),
        "results": rows,
    }
    out_path = out_dir / "round_cap_sweep.json"
    html_path = write_json_and_html(report, out_path, title="Round Cap Sweep (Exp 2)")
    print(f"Report: {out_path}")
    print(f"HTML:   {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
