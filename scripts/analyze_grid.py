#!/usr/bin/env python3
"""Aggregate the full-grid results: E1 curves, E3 trajectory geometry, H1-H3 stats.

Usage: analyze_grid.py --run results/full_20260826 --out docs/paper/figures
Outputs:
  fig_e1_curves.png     mean checkpoint accuracy by round, per model
  fig_e3_scatter.png    trajectory geometry vs. outcome (H3)
  fig_e2_caps.png       end accuracy vs round cap, per model (if E2 reports exist)
  e3_geometry.json      per-trace geometry summaries + correlation stats
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODEL_LABELS = {
    "Qwen/Qwen3.5-4B": "Qwen3.5-4B",
    "Qwen/Qwen3.6-27B": "Qwen3.6-27B",
    "Qwen/Qwen3.5-397B-A17B": "Qwen3.5-397B",
}
COLORS = {"Qwen3.5-4B": "tab:red", "Qwen3.6-27B": "tab:blue", "Qwen3.5-397B": "tab:green"}


def _mpl():
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams["font.family"] = [
        "Arial Unicode MS", "PingFang SC", "Hiragino Sans GB", "sans-serif",
    ]
    import matplotlib.pyplot as plt

    return plt


def _pearson(x, y):
    import numpy as np

    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or x.std() == 0 or y.std() == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def _spearman(x, y):
    import numpy as np

    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    return _pearson(rx, ry)


def load_reports(run_dir: Path, kind: str):
    name = "curve/round_curve.json" if kind == "e1" else "caps/round_cap_sweep.json"
    for shard in sorted(run_dir.iterdir()):
        path = shard / name
        if path.exists():
            yield json.loads(path.read_text())


def plot_e1(reports, out_path: Path, max_rounds: int = 30):
    import numpy as np

    plt = _mpl()
    by_model = defaultdict(list)
    for rep in reports:
        label = MODEL_LABELS.get(rep["questioner"]["model"], rep["questioner"]["model"])
        for row in rep["results"]:
            accs = {int(k): v for k, v in row["accuracy_by_round"].items()}
            curve = [accs.get(r, np.nan) for r in range(1, max_rounds + 1)]
            by_model[label].append(curve)

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for label, curves in by_model.items():
        arr = np.array(curves, float)
        mean = np.nanmean(arr, axis=0)
        sem = np.nanstd(arr, axis=0) / np.sqrt(np.sum(~np.isnan(arr), axis=0).clip(min=1))
        xs = np.arange(1, max_rounds + 1)
        c = COLORS.get(label)
        ax.plot(xs, mean, lw=1.8, color=c, label=f"{label} (n={len(curves)})")
        ax.fill_between(xs, mean - sem, mean + sem, alpha=0.15, color=c)
    ax.set_xlabel("Round")
    ax.set_ylabel("Checkpoint accuracy (clue recall)")
    ax.set_title("E1 — checkpoint accuracy by round (11 puzzles × 3 seeds)")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_e2(reports, out_path: Path):
    import numpy as np

    plt = _mpl()
    by_model = defaultdict(lambda: defaultdict(list))
    for rep in reports:
        label = MODEL_LABELS.get(rep["questioner"]["model"], rep["questioner"]["model"])
        for row in rep["results"]:
            by_model[label][int(row["round_cap"])].append(float(row["score"]))
    if not by_model:
        return False
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for label, caps in by_model.items():
        xs = sorted(caps)
        mean = [np.mean(caps[c]) for c in xs]
        sem = [np.std(caps[c]) / max(1, np.sqrt(len(caps[c]))) for c in xs]
        ax.errorbar(xs, mean, yerr=sem, marker="s", capsize=3,
                    color=COLORS.get(label), label=f"{label}")
    ax.set_xlabel("Round cap")
    ax.set_ylabel("End accuracy (composite / 100, normalized)")
    ax.set_title("E2 — end accuracy vs round budget")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return True


def e3_geometry(reports, out_json: Path, out_fig: Path):
    import numpy as np

    from engine.game import load_puzzle
    from evaluation.trajectory import trace_geometry

    plt = _mpl()
    rows = []
    puzzles = {}
    for rep in reports:
        label = MODEL_LABELS.get(rep["questioner"]["model"], rep["questioner"]["model"])
        for row in rep["results"]:
            if not row.get("qa_rounds"):
                continue
            pid = row["puzzle_id"]
            puzzles.setdefault(pid, load_puzzle(pid))
            geo = trace_geometry(row["qa_rounds"], puzzles[pid], label=label)
            if geo is None:
                continue
            s = geo.summary()
            # Keep the per-round series, not just its summary: the paper's central
            # figure is stride and anchor distance against round, and a run that
            # stores only means cannot draw it without being repeated.
            s["step_sizes"] = [round(x, 5) for x in geo.step_sizes]
            s["anchor_dists"] = [round(x, 5) for x in geo.human_dists]
            accs = row.get("accuracy_by_round", {})
            s["best_acc"] = max(accs.values()) if accs else row.get("score", 0.0)
            s["seed"] = row.get("seed")
            s["committed"] = bool(row.get("natural_final_answer"))
            rows.append(s)
            print(f"  geo {label} {pid} s{row.get('seed')}: step={s['mean_step']} h_slope={s['human_dist_slope']} best={s['best_acc']:.2f}", flush=True)

    # H3 correlations, per model and pooled
    stats = {}
    def corr_block(sub):
        best = [r["best_acc"] for r in sub]
        return {
            "n": len(sub),
            "pearson_step_best": _pearson([r["mean_step"] for r in sub], best),
            "spearman_step_best": _spearman([r["mean_step"] for r in sub], best),
            "pearson_hslope_best": _pearson([r["human_dist_slope"] for r in sub], best),
            "spearman_hslope_best": _spearman([r["human_dist_slope"] for r in sub], best),
            "pearson_hdist_best": _pearson([r["mean_human_dist"] for r in sub], best),
        }
    stats["pooled"] = corr_block(rows)
    for label in {r["label"] for r in rows}:
        stats[label] = corr_block([r for r in rows if r["label"] == label])

    out_json.write_text(json.dumps({"traces": rows, "correlations": stats}, ensure_ascii=False, indent=1))

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4))
    for label in sorted({r["label"] for r in rows}):
        sub = [r for r in rows if r["label"] == label]
        c = COLORS.get(label)
        axes[0].scatter([r["mean_step"] for r in sub], [r["best_acc"] for r in sub],
                        s=26, alpha=0.7, color=c, label=label)
        axes[1].scatter([r["human_dist_slope"] for r in sub], [r["best_acc"] for r in sub],
                        s=26, alpha=0.7, color=c, label=label)
    axes[0].set_xlabel("Mean association step size  $\\bar{s}$")
    axes[0].set_ylabel("Best checkpoint accuracy")
    axes[0].set_title("H1: stride vs outcome")
    axes[1].set_xlabel("Human-distance slope  $dh/dt$")
    axes[1].set_title("H2: drift vs outcome")
    axes[1].axvline(0, color="gray", lw=0.8, ls=":")
    for ax in axes:
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_fig, dpi=200)
    plt.close(fig)
    return stats


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run", default="results/full_20260826")
    p.add_argument("--out", default="docs/paper/figures")
    p.add_argument("--skip-e3", action="store_true")
    args = p.parse_args()
    run, out = Path(args.run), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    e1 = list(load_reports(run, "e1"))
    print(f"E1 reports: {len(e1)}")
    plot_e1(e1, out / "fig_e1_curves.png")
    print(f"Wrote {out/'fig_e1_curves.png'}")

    e2 = list(load_reports(run, "e2"))
    print(f"E2 reports: {len(e2)}")
    if plot_e2(e2, out / "fig_e2_caps.png"):
        print(f"Wrote {out/'fig_e2_caps.png'}")

    if not args.skip_e3:
        stats = e3_geometry(e1, out / "e3_geometry.json", out / "fig_e3_scatter.png")
        print(f"Wrote {out/'fig_e3_scatter.png'} and e3_geometry.json")
        print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
