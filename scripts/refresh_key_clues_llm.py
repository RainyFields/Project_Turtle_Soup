#!/usr/bin/env python3
"""Re-extract key_clues for the real/ puzzle set with an LLM.

    python scripts/refresh_key_clues_llm.py --dry-run
    python scripts/refresh_key_clues_llm.py --provider openrouter --model stealth/ox-alpha
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from engine.game import list_puzzle_ids
from evaluation.judge import LLMJudge
from generator.reference.key_clues_llm import MAX_CLUES, MIN_CLUES, extract_key_clues_llm
from generator.schema import puzzle_dict_to_json_ready, validate_puzzle


def main() -> int:
    p = argparse.ArgumentParser(description="LLM key_clues extraction for real/ puzzles")
    p.add_argument("--provider", default="openrouter")
    p.add_argument("--model", default="stealth/ox-alpha")
    p.add_argument("--family", default="real", help="Puzzle family to refresh")
    p.add_argument("--only", nargs="*", default=None, help="Specific puzzle ids")
    p.add_argument("--min-clues", type=int, default=MIN_CLUES)
    p.add_argument("--max-clues", type=int, default=MAX_CLUES)
    p.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Raise for reasoning models — thinking counts against this budget",
    )
    p.add_argument("--dry-run", action="store_true", help="Print, do not write")
    p.add_argument("--report", default=None, help="Write a JSON report here")
    args = p.parse_args()

    puzzles_dir = ROOT / "data" / "puzzles" / args.family
    ids = args.only or list_puzzle_ids(family=args.family)
    rater = LLMJudge(
        provider_name=args.provider, model=args.model, max_tokens=args.max_tokens
    )

    report, updated, failed = [], 0, []
    for pid in ids:
        path = puzzles_dir / f"{pid}.json"
        if not path.exists():
            failed.append((pid, "file not found"))
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        try:
            out = extract_key_clues_llm(
                data.get("surface", ""),
                data.get("solution", ""),
                rater=rater,
                min_clues=args.min_clues,
                max_clues=args.max_clues,
            )
        except Exception as exc:  # keep going; a partial refresh is still useful
            failed.append((pid, f"{type(exc).__name__}: {exc}"))
            print(f"FAIL {pid}: {type(exc).__name__}", flush=True)
            continue

        clues = out["clues"]
        row = {"id": pid, "title": data.get("title"), "old": data.get("key_clues"), **out}
        report.append(row)
        print(f"{pid} [{str(data.get('title'))[:14]}]", flush=True)
        print(f"   旧: {data.get('key_clues')}")
        print(f"   新: {clues}")
        if out["rejected"]:
            print(f"   剔除: {out['rejected']}")

        if len(clues) < args.min_clues:
            failed.append((pid, f"only {len(clues)} valid clues"))
            print("   ⚠️ 有效线索不足，跳过写入")
            continue
        if args.dry_run:
            continue
        data["key_clues"] = clues
        data = puzzle_dict_to_json_ready(data)
        ok, errors = validate_puzzle(data, for_publish=False)
        if not ok:
            failed.append((pid, str(errors)))
            print(f"   ⚠️ schema 失败: {errors}")
            continue
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        updated += 1

    if args.report:
        Path(args.report).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(f"\n{'(dry-run) ' if args.dry_run else ''}Updated {updated}/{len(ids)}；失败 {len(failed)}")
    for pid, why in failed:
        print(f"  - {pid}: {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
