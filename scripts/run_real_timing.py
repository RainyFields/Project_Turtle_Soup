#!/usr/bin/env python3
"""Run one puzzle with real APIs; measure per-call latency and extrapolate full study."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from evaluation.api_timing import TimingSession, extrapolate_full_study, patch_agent_timing
from evaluation.round_studies import ModelSpec, run_round_cap, run_round_curve


def _has_key(*names: str) -> bool:
    return any((os.getenv(n) or "").strip() for n in names)


def main() -> int:
    p = argparse.ArgumentParser(description="Real API timing pilot (one puzzle)")
    p.add_argument("--puzzle", default="turtle_001")
    p.add_argument("--questioner-provider", default="qwen")
    p.add_argument("--questioner-model", default="qwen-plus")
    p.add_argument("--oracle-provider", default="")
    p.add_argument("--oracle-model", default="qwen-plus")
    p.add_argument("--max-rounds", type=int, default=8, help="Exp1 checkpoint rounds (keep low for cost)")
    p.add_argument("--round-caps", nargs="+", type=int, default=[5, 10])
    p.add_argument("--output", default="")
    args = p.parse_args()

    provider = args.questioner_provider.lower()
    if provider in ("qwen", "dashscope", "tongyi") and not _has_key("QWEN_API_KEY", "DASHSCOPE_API_KEY"):
        print("ERROR: Set QWEN_API_KEY in .env (see .env.example)")
        return 1
    if provider in ("zai", "glm", "z.ai") and not _has_key("ZAI_API_KEY", "Z_AI_API_KEY"):
        print("ERROR: Set ZAI_API_KEY in local .env (see .env.example)")
        return 1
    if provider not in ("mock", "test", "qwen", "dashscope", "tongyi", "zai", "glm", "z.ai"):
        if provider == "openai" and not _has_key("OPENAI_API_KEY"):
            print("ERROR: Set OPENAI_API_KEY in .env")
            return 1

    oracle_provider = args.oracle_provider or (
        "openai" if _has_key("OPENAI_API_KEY") else args.questioner_provider
    )
    oracle_model = args.oracle_model
    if oracle_provider == "openai" and not _has_key("OPENAI_API_KEY"):
        oracle_provider = args.questioner_provider
        oracle_model = args.questioner_model
        print(f"No OPENAI_API_KEY — using {oracle_provider}/{oracle_model} for Oracle too")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output) if args.output else ROOT / "results" / "real_timing" / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    session = TimingSession()
    patch_agent_timing(session)

    q = ModelSpec(
        name=args.questioner_model,
        provider=args.questioner_provider,
        model=args.questioner_model,
    )

    from evaluation.round_studies import build_app_config

    print(f"=== Real timing pilot: {args.puzzle} ===")
    print(f"Questioner: {args.questioner_provider}/{args.questioner_model}")
    print(f"Oracle: {oracle_provider}/{oracle_model}")
    print(f"Exp1 rounds: {args.max_rounds} | Exp2 caps: {args.round_caps}")
    print()

    t0 = time.perf_counter()

    from engine.game import load_puzzle

    puzzle = load_puzzle(args.puzzle)

    exp1_row = run_round_curve(
        puzzle,
        app_config=build_app_config(
            oracle_provider=oracle_provider,
            oracle_model=oracle_model,
            questioner=q,
            max_rounds=args.max_rounds,
        ),
        max_checkpoint_round=args.max_rounds,
        questioner_provider=args.questioner_provider,
        oracle_provider=oracle_provider,
    )
    exp1_wall = time.perf_counter() - t0

    exp2_rows = []
    t_exp2 = time.perf_counter()
    for cap in args.round_caps:
        row = run_round_cap(
            puzzle,
            app_config=build_app_config(
                oracle_provider=oracle_provider,
                oracle_model=oracle_model,
                questioner=q,
                max_rounds=cap,
            ),
            round_cap=cap,
            questioner_provider=args.questioner_provider,
            oracle_provider=oracle_provider,
        )
        exp2_rows.append(row)
    exp2_wall = time.perf_counter() - t_exp2
    total_wall = time.perf_counter() - t0

    timing = session.summary()
    sec_per_call = timing.get("mean_s") or timing.get("median_s") or 0.0

    exp1_api = exp1_row.get("api_calls_estimate", 0)
    exp2_api = sum(r.get("api_calls_estimate", 0) for r in exp2_rows)
    extrap = extrapolate_full_study(
        sec_per_call=sec_per_call,
        exp1_api_calls_pilot=exp1_api,
        exp2_api_calls_pilot=exp2_api,
        n_puzzles_pilot=1,
        n_caps_pilot=len(args.round_caps),
    )

    report = {
        "puzzle_id": args.puzzle,
        "questioner": {"provider": args.questioner_provider, "model": args.questioner_model},
        "oracle": {"provider": oracle_provider, "model": oracle_model},
        "pilot_config": {
            "max_rounds": args.max_rounds,
            "round_caps": args.round_caps,
        },
        "wall_clock_s": {
            "exp1": round(exp1_wall, 2),
            "exp2": round(exp2_wall, 2),
            "total": round(total_wall, 2),
        },
        "api_calls_pilot": {"exp1": exp1_api, "exp2": exp2_api, "total": exp1_api + exp2_api},
        "per_call_timing": timing,
        "extrapolation_full_study": extrap,
        "exp1_result": exp1_row,
        "exp2_results": exp2_rows,
    }

    out_path = out_dir / "real_timing.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("--- Per-call timing (measured) ---")
    print(f"  calls: {timing.get('count', 0)}")
    print(f"  mean: {timing.get('mean_s', 0)}s | median: {timing.get('median_s', 0)}s | p95: {timing.get('p95_s', 0)}s")
    if timing.get("by_role"):
        for role, st in timing["by_role"].items():
            print(f"  {role}: mean={st['mean_s']}s n={st['count']}")
    print()
    print("--- Wall clock (this run) ---")
    print(f"  Exp1: {exp1_wall:.1f}s | Exp2: {exp2_wall:.1f}s | total: {total_wall:.1f}s")
    print()
    print("--- Extrapolation (full study) ---")
    print(f"  @ {sec_per_call}s/call (measured mean)")
    print(f"  Exp1: ~{extrap['exp1_hours']}h ({extrap['exp1_api_calls']:,} calls)")
    print(f"  Exp2: ~{extrap['exp2_hours']}h ({extrap['exp2_api_calls']:,} calls)")
    print(f"  Combined: ~{extrap['combined_hours']}h")
    print(f"\nReport: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
