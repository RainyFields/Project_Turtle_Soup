#!/usr/bin/env python3
"""Plot Exp 1 round curves and Exp 2 cap sweeps from study JSON reports.

Accepts any of the three report shapes and emits PNGs next to the JSON:
- ``pilot_timing.json``      (``exp1_results`` + ``exp2_results``)
- ``round_curve.json``       (``study: round_curve``)
- ``round_cap_sweep.json``   (``study: round_cap_sweep``)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _mpl():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "matplotlib is required for plotting: pip install matplotlib"
        ) from exc


def _row_label(row: Dict[str, Any]) -> str:
    q = row.get("questioner") or {}
    model = q.get("model") or q.get("name")
    parts = [str(row.get("puzzle_id", "?"))]
    if model and model != "mock":
        parts.append(str(model))
    if row.get("seed") is not None:
        parts.append(f"seed{row['seed']}")
    return " · ".join(parts)


def plot_round_curve(rows: List[Dict[str, Any]], out_path: Path, *, title: str) -> Optional[Path]:
    rows = [r for r in rows if r.get("accuracy_by_round")]
    if not rows:
        return None
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(8, 5))
    for row in rows:
        curve = {int(k): v for k, v in row["accuracy_by_round"].items()}
        xs = sorted(curve)
        ax.plot(xs, [curve[x] for x in xs], marker="o", markersize=3, label=_row_label(row))
        if row.get("natural_end_round"):
            ax.axvline(row["natural_end_round"], linestyle=":", alpha=0.4)
    ax.set_xlabel("Round")
    ax.set_ylabel("Checkpoint accuracy")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_round_cap(rows: List[Dict[str, Any]], out_path: Path, *, title: str) -> Optional[Path]:
    rows = [r for r in rows if r.get("round_cap") is not None]
    if not rows:
        return None
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(8, 5))

    by_cap: Dict[int, List[float]] = defaultdict(list)
    for row in rows:
        by_cap[int(row["round_cap"])].append(float(row.get("score", 0.0)))
        ax.scatter(row["round_cap"], row.get("score", 0.0), alpha=0.35, color="tab:blue", s=18)
    caps = sorted(by_cap)
    means = [sum(by_cap[c]) / len(by_cap[c]) for c in caps]
    ax.plot(caps, means, marker="s", color="tab:red", label="mean")

    ax.set_xlabel("Round cap")
    ax.set_ylabel("End accuracy")
    ax.set_ylim(-0.05, 1.05)
    ax.set_xticks(caps)
    ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_report(json_path: Path, out_dir: Optional[Path] = None) -> List[Path]:
    report = json.loads(json_path.read_text(encoding="utf-8"))
    out_dir = out_dir or json_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    exp1_rows = report.get("exp1_results")
    exp2_rows = report.get("exp2_results")
    if exp1_rows is None and exp2_rows is None:
        rows = report.get("results", [])
        if report.get("study") == "round_curve":
            exp1_rows = rows
        elif report.get("study") == "round_cap_sweep":
            exp2_rows = rows
        else:  # unlabeled: split by row shape
            exp1_rows = [r for r in rows if "accuracy_by_round" in r]
            exp2_rows = [r for r in rows if "round_cap" in r]

    written: List[Path] = []
    if exp1_rows:
        p = plot_round_curve(
            exp1_rows, out_dir / "round_curve.png", title="Exp 1 — checkpoint accuracy by round"
        )
        if p:
            written.append(p)
    if exp2_rows:
        p = plot_round_cap(
            exp2_rows, out_dir / "round_cap_sweep.png", title="Exp 2 — end accuracy vs round cap"
        )
        if p:
            written.append(p)
    return written


def main() -> int:
    p = argparse.ArgumentParser(description="Plot round-study reports")
    p.add_argument("json_paths", nargs="+", help="pilot_timing.json / round_curve.json / round_cap_sweep.json")
    p.add_argument("--out-dir", default=None, help="Directory for PNGs (default: next to each JSON)")
    args = p.parse_args()

    any_written = False
    for raw in args.json_paths:
        written = plot_report(Path(raw), Path(args.out_dir) if args.out_dir else None)
        for path in written:
            any_written = True
            print(f"Wrote {path}")
        if not written:
            print(f"No plottable rows in {raw}")
    return 0 if any_written else 1


if __name__ == "__main__":
    raise SystemExit(main())
