#!/usr/bin/env python3
"""Annotate under-determination for a puzzle family.

    python scripts/annotate_puzzle_dimensions.py --dry-run --only refsoup_008
    python scripts/annotate_puzzle_dimensions.py --model z-ai/glm-5.3-flash

Writes data/puzzles/dimensions.json (a sidecar, so puzzle files and their
schema stay untouched and the annotation can be re-run independently).
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

from engine.game import list_puzzle_ids, load_puzzle
from evaluation.judge import LLMJudge
from generator.analysis.puzzle_dimensions import (
    count_dangling_details,
    under_determination,
)

OUT = ROOT / "data" / "puzzles" / "dimensions.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="openrouter")
    ap.add_argument("--model", default="z-ai/glm-5.3-flash")
    ap.add_argument("--family", default="real")
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--candidates", type=int, default=12, help="Cold guesses per puzzle")
    # Dangling-detail counting is kept but off by default: it saturates (values
    # 1-3, bounded by how few odd details a 9-108 character surface can hold) so
    # it cannot serve as a grouping variable, and it triples the calls per puzzle.
    # Still useful qualitatively — it names what makes one puzzle hard.
    ap.add_argument("--with-dangling", action="store_true")
    ap.add_argument("--dangling-samples", type=int, default=3)
    # 8192 fits the short solutions this puzzle set now has (max 279 chars) and
    # stays inside a free-tier credit ceiling; the old 32768 was sized for long
    # solutions that are no longer in the set.
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--skip-done", action="store_true", help="Skip ids already in the sidecar")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ids = args.only or list_puzzle_ids(family=args.family)
    rater = LLMJudge(provider_name=args.provider, model=args.model, max_tokens=args.max_tokens)
    out = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}

    for pid in ids:
        if args.skip_done and out.get(pid, {}).get("under_determination") is not None:
            print(f"skip {pid} (已标注)", flush=True)
            continue
        puzzle = load_puzzle(pid)
        surface, solution = puzzle["surface"], puzzle["solution"]
        try:
            ud = under_determination(
                surface, solution, rater=rater, n=args.candidates
            )
            dangling = (
                count_dangling_details(
                    surface, solution, rater=rater, samples=args.dangling_samples
                )
                if args.with_dangling
                else {}
            )
        except Exception as exc:  # keep going; a partial run is still useful
            print(f"FAIL {pid}: {type(exc).__name__}: {exc}", flush=True)
            continue

        # An empty candidate list means the generation failed (unparseable JSON,
        # or retries exhausted). Recording index=None would look like a result
        # and would be skipped by --skip-done on the next pass.
        if ud.get("index") is None:
            print(f"FAIL {pid}: no candidate stories generated", flush=True)
            continue

        row = {
            "id": pid,
            "title": puzzle.get("title"),
            # primary dimension: how far the surface alone leaves you from the answer
            "under_determination": ud["index"],
            "cold_best": ud.get("cold_best"),
            "cold_mean": ud.get("cold_mean"),
            "cold_scores": ud.get("scores"),
            "distinct_stories": ud.get("distinct"),
            "candidate_stories": ud.get("stories"),
            "dangling_count": dangling.get("dangling_count"),
            "dangling_items": dangling.get("items"),
            "key_clue_count": len(puzzle.get("key_clues", [])),
            "surface_chars": len(surface),
            "solution_chars": len(solution),
        }
        out[pid] = row
        print(
            f"{pid} [{str(puzzle.get('title'))[:14]}] "
            f"UD={ud['index']} cold_best={ud.get('cold_best')} "
            f"distinct={ud.get('distinct')}/{args.candidates}",
            flush=True,
        )
        if not args.dry_run:
            OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'(dry-run) ' if args.dry_run else ''}标注 {len(ids)} 道 → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
