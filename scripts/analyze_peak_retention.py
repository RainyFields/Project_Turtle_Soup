#!/usr/bin/env python3
"""Peak-vs-final retention: how much of the understanding a model reaches
mid-game survives to the end of it.

For every E1 game, compare the best checkpoint score the model ever reached
(its peak) with the score at the final round. Two peak definitions guard
against scoring jitter (rewording the same story can swing the clue half):

- raw peak: best single checkpoint;
- sustained peak: best value held over two consecutive checkpoints.

The flat mean curves of E1 hide this churn: a plateau can be an equilibrium of
finding and losing, not stagnation. Writes docs/paper/figures/peak_retention.json.

  python scripts/analyze_peak_retention.py [--run results/grid_2026_09]
"""
from __future__ import annotations

import argparse
import glob
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="results/grid_2026_09")
    args = ap.parse_args()

    games = defaultdict(list)
    for f in sorted(glob.glob(f"{args.run}/*/curve/round_curve.json")):
        model = Path(f).parts[-3].rsplit("_s", 1)[0].replace("Qwen_Qwen", "Qwen")
        for r in json.load(open(f))["results"]:
            acc = {int(k): v for k, v in (r.get("accuracy_by_round") or {}).items()}
            if len(acc) < 2:
                continue
            vals = [acc[rd] for rd in sorted(acc)]
            games[model].append(
                dict(
                    puzzle=r["puzzle_id"],
                    seed=r.get("seed"),
                    peak=max(vals),
                    sustained_peak=max(min(vals[i], vals[i + 1]) for i in range(len(vals) - 1)),
                    final=vals[-1],
                )
            )

    out = {}
    for m, gs in sorted(games.items()):
        n = len(gs)
        out[m] = {
            "n": n,
            "mean_peak": round(statistics.mean(g["peak"] for g in gs), 3),
            "mean_sustained_peak": round(statistics.mean(g["sustained_peak"] for g in gs), 3),
            "mean_final": round(statistics.mean(g["final"] for g in gs), 3),
            "retention_raw": round(
                statistics.mean(g["final"] / g["peak"] for g in gs if g["peak"] > 0), 3
            ),
            "retention_sustained": round(
                statistics.mean(
                    g["final"] / g["sustained_peak"] for g in gs if g["sustained_peak"] > 0
                ),
                3,
            ),
            "games_final_below_half_sustained_peak": sum(
                1 for g in gs if g["sustained_peak"] > 0 and g["final"] < g["sustained_peak"] / 2
            ),
            "games_sustained_peak_ge_0.5": sum(1 for g in gs if g["sustained_peak"] >= 0.5),
            "games_raw_peak_ge_0.5": sum(1 for g in gs if g["peak"] >= 0.5),
        }

    dst = ROOT / "docs/paper/figures/peak_retention.json"
    dst.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nWrote {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
