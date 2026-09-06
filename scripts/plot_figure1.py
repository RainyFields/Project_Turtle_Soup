#!/usr/bin/env python3
"""Build Figure 1 (association trajectories) from study report JSONs.

Usage:
  plot_figure1.py --reports a.json b.json --puzzle turtle_002 --out fig1.png

Each report contributes the trace(s) matching --puzzle; the label comes from
the report's questioner model. Also prints per-trace geometry summaries
(mean/late step size, human-dist slope) for the paper's §5.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.game import load_puzzle
from evaluation.trajectory import figure1, load_qa_rows, trace_geometry


def main() -> int:
    p = argparse.ArgumentParser(description="Render Figure 1 from study reports")
    p.add_argument("--reports", nargs="+", required=True)
    p.add_argument("--puzzle", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--max-traces", type=int, default=4)
    p.add_argument("--title", default="")
    args = p.parse_args()

    puzzle = load_puzzle(args.puzzle)
    traces = []
    for path in args.reports:
        report = json.loads(Path(path).read_text())
        model = (report.get("questioner") or {}).get("model", Path(path).stem)
        label = model.split("/")[-1]
        for row in load_qa_rows(Path(path)):
            if row.get("puzzle_id") != args.puzzle:
                continue
            if row.get("seed") not in (None, 0):
                continue  # one representative trace per model
            geo = trace_geometry(row["qa_rounds"], puzzle, label=label)
            if geo is not None:
                geo.extra["score"] = row.get("score")
                traces.append(geo)
            break

    if len(traces) < 2:
        print(f"Need >=2 traces for {args.puzzle}; found {len(traces)}")
        return 1
    traces = traces[: args.max_traces]

    out = figure1(traces, puzzle, Path(args.out), title=args.title)
    print(f"Wrote {out}")
    for t in traces:
        print(json.dumps(t.summary(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
