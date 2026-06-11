#!/usr/bin/env python3
"""Pilot Exp1 + Exp2 on a small puzzle set with wall-clock timing."""
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

from evaluation.round_studies import ModelSpec, run_pilot


def main() -> int:
    p = argparse.ArgumentParser(description="Pilot round studies with timing")
    p.add_argument("--puzzles", nargs="+", default=["turtle_001", "turtle_002"])
    p.add_argument("--max-rounds", type=int, default=30)
    p.add_argument("--round-caps", nargs="+", type=int, default=[5, 10, 15, 20, 25, 30])
    p.add_argument("--questioner-provider", default="mock")
    p.add_argument("--questioner-model", default="mock")
    p.add_argument("--oracle-provider", default="mock")
    p.add_argument("--oracle-model", default="mock")
    p.add_argument("--output", default=None)
    args = p.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(args.output) if args.output else ROOT / "results" / "pilot" / ts

    q = ModelSpec(name=args.questioner_model, provider=args.questioner_provider, model=args.questioner_model)
    report = run_pilot(
        puzzle_ids=args.puzzles,
        questioner=q,
        oracle_provider=args.oracle_provider,
        oracle_model=args.oracle_model,
        max_rounds=args.max_rounds,
        round_caps=args.round_caps,
        output_dir=out,
    )

    t = report["timing"]
    ext = report["extrapolation_full_study"]
    print("=== Pilot complete ===")
    print(f"Puzzles: {', '.join(args.puzzles)}")
    print(f"Questioner: {args.questioner_provider}/{args.questioner_model}")
    print(f"Exp1 ({args.max_rounds} checkpoint rounds): {t['exp1_total_s']}s total "
          f"({t['avg_exp1_per_puzzle_s']}s/puzzle)")
    print(f"Exp2 ({len(args.round_caps)} caps × {len(args.puzzles)} puzzles): {t['exp2_total_s']}s total "
          f"({t['avg_exp2_per_game_s']}s/game)")
    print(f"Total wall time: {t['total_s']}s")
    print()
    api = report["api_calls"]
    print(f"API calls (pilot): Exp1={api['exp1_questioner_oracle_checkpoint']} Exp2={api['exp2_total']} "
          f"total={api['pilot_total']}")
    print("Extrapolation → full study (11 puzzles × 3 models × 3 seeds):")
    print(f"  API calls: Exp1 ~{api['full_study_exp1_estimated']:,} | Exp2 ~{api['full_study_exp2_estimated']:,}")
    print(f"  @ {ext['at_sec_per_call']}s/call → Exp1 ~{ext['exp1_estimated_h']}h | "
          f"Exp2 ~{ext['exp2_estimated_h']}h | Combined ~{ext['combined_estimated_h']}h")
    print(f"Report: {report['output_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
