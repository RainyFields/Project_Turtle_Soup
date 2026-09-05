#!/usr/bin/env python3
"""Publication figures for the IAB 2026 paper, from the 2026-09 grid.

Figure 1 (fig1_flatness): (a) E1 checkpoint accuracy by round, mean with 95% CI,
full 0-1 axis; (b) per-game final score against sustained peak, with y=x and
y=x/2 references. Together: gains stop after round ten, and the plateau is an
equilibrium of finding and losing.

Figure 2 (fig2_geometry): (a) mean stride and (b) drift slope against best
checkpoint score per trace: circling regime separation, and the within-model
flatness behind H3's negative result.

Run from the repo root:  .venv/bin/python docs/paper/figures/make_figures.py
"""
from __future__ import annotations

import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FIGDIR = ROOT / "docs/paper/figures"
SKILL_SCRIPTS = Path.home() / ".claude/skills/nature-figure/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 7,
        "axes.titlesize": 7.5,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.8,
        "legend.frameon": False,
    }
)

# Models ordered by scale; one sequential family, red reserved for references.
MODELS = ["Qwen3.5-4B", "Qwen3.6-27B", "Qwen3.5-397B"]
LABELS = {"Qwen3.5-4B": "4B", "Qwen3.6-27B": "27B", "Qwen3.5-397B": "397B"}
COLORS = {"Qwen3.5-4B": "#9DB8D9", "Qwen3.6-27B": "#4C7BB8", "Qwen3.5-397B": "#173A66"}
ACCENT = "#C0504D"


def load_e1():
    """Per-model: per-puzzle accuracy_by_round and per-game (peak, final, committed)."""
    curves = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))  # m -> puzzle -> rd -> vals
    retention = defaultdict(list)
    for f in sorted(glob.glob(str(ROOT / "results/grid_2026_09/*/curve/round_curve.json"))):
        model = (
            Path(f).parts[-3].rsplit("_s", 1)[0]
            .replace("Qwen_Qwen", "Qwen")
            .replace("-A17B", "")
        )
        for r in json.load(open(f))["results"]:
            acc = {int(k): v for k, v in (r.get("accuracy_by_round") or {}).items()}
            if len(acc) < 2:
                continue
            for rd, v in acc.items():
                curves[model][r["puzzle_id"]][rd].append(v)
            vals = [acc[rd] for rd in sorted(acc)]
            speak = max(min(vals[i], vals[i + 1]) for i in range(len(vals) - 1))
            retention[model].append(
                (speak, vals[-1], r.get("natural_end_round") is not None))
    return curves, retention


def clustered_band(per_puzzle, rounds, n_boot=1000, seed=0):
    """95% CI for the round means, bootstrapping puzzles (the clustering unit)."""
    rng = np.random.default_rng(seed)
    puzzles = sorted(per_puzzle)
    pz_means = np.array([[np.mean(per_puzzle[p].get(rd, [np.nan])) for rd in rounds]
                         for p in puzzles])
    boots = np.empty((n_boot, len(rounds)))
    for b in range(n_boot):
        idx = rng.integers(0, len(puzzles), len(puzzles))
        boots[b] = np.nanmean(pz_means[idx], axis=0)
    return (np.nanmean(pz_means, axis=0),
            np.percentile(boots, 2.5, axis=0),
            np.percentile(boots, 97.5, axis=0))


def save(fig, stem):
    require_matplotlib_panel_alignment(
        fig,
        json_out=str(FIGDIR / f"{stem}.alignment.json"),
        overlay_svg=str(FIGDIR / f"{stem}.alignment.svg"),
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        strict=True,
    )
    fig.savefig(FIGDIR / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(FIGDIR / f"{stem}.png", dpi=400, bbox_inches="tight")
    print("wrote", stem)


def fig1():
    curves, retention = load_e1()
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(5.2, 1.7))

    for m in MODELS:
        rounds = sorted({rd for pz in curves[m].values() for rd in pz})
        mean, lo, hi = clustered_band(curves[m], rounds)
        ax_a.fill_between(rounds, lo, hi, color=COLORS[m], alpha=0.18, lw=0)
        ax_a.plot(rounds, mean, color=COLORS[m], lw=1.4)
        # Dodge the 27B/397B end labels: their final means sit 0.026 apart.
        dodge = {"Qwen3.5-4B": 0, "Qwen3.6-27B": 0, "Qwen3.5-397B": 8}[m]
        ax_a.annotate(LABELS[m], xy=(rounds[-1], mean[-1]),
                      xytext=(3, dodge), textcoords="offset points",
                      va="center", color=COLORS[m], fontsize=7)
    ax_a.axvline(10, color="0.6", lw=0.7, ls=(0, (2, 2)))
    ax_a.set_xlim(1, 33.5)
    ax_a.set_ylim(0, 1.0)
    ax_a.set_xticks([1, 10, 20, 30])
    ax_a.set_xlabel("Round")
    ax_a.set_ylabel("Checkpoint accuracy")
    ax_a.set_title("Gains stop after round ten", pad=3)
    # Inset: the early rise the full-range axis hides.
    ins = ax_a.inset_axes([0.42, 0.52, 0.55, 0.42])
    for m in MODELS:
        rounds = sorted({rd for pz in curves[m].values() for rd in pz})
        mean, _, _ = clustered_band(curves[m], rounds, n_boot=200)
        sel = [i for i, rd in enumerate(rounds) if rd <= 14]
        ins.plot([rounds[i] for i in sel], [mean[i] for i in sel],
                 color=COLORS[m], lw=1.1)
    ins.axvline(10, color="0.6", lw=0.6, ls=(0, (2, 2)))
    ins.set_xlim(1, 14)
    ins.set_ylim(0.0, 0.24)
    ins.set_xticks([1, 10])
    ins.set_yticks([0.0, 0.2])
    ins.tick_params(labelsize=5.5, pad=1)
    ins.set_title("rounds 1-14", fontsize=5.5, pad=1.5)

    lim = 1.02
    ax_b.plot([0, lim], [0, lim], color="0.7", lw=0.7, ls=(0, (4, 2)))
    ax_b.axvline(0.5, color="0.6", lw=0.7, ls=(0, (2, 2)))
    for m in MODELS:
        pk = [p for p, f, c in retention[m]]
        fn = [f for p, f, c in retention[m]]
        com = [c for p, f, c in retention[m]]
        # Marker shape encodes commitment: filled = volunteered a final story.
        ax_b.scatter([p for p, c in zip(pk, com) if not c],
                     [f for f, c in zip(fn, com) if not c],
                     s=10, facecolors="none", edgecolors=COLORS[m], lw=0.7,
                     alpha=0.8, label=f"{LABELS[m]} (no commit)")
        ax_b.scatter([p for p, c in zip(pk, com) if c],
                     [f for f, c in zip(fn, com) if c],
                     s=11, color=COLORS[m], alpha=0.95, lw=0)
    ax_b.set_xlim(0, lim)
    ax_b.set_ylim(0, lim)
    ax_b.set_xlabel("Sustained peak (best held 2 rounds)")
    ax_b.set_ylabel("Final-round score")
    ax_b.set_title("Found but rarely committed", pad=3)
    ax_b.legend(loc="upper left", handletextpad=0.1, borderaxespad=0.2,
                labelspacing=0.15, fontsize=5.5)

    for ax, lab in ((ax_a, "a"), (ax_b, "b")):
        ax.text(-0.24, 1.06, lab, transform=ax.transAxes,
                fontsize=9, fontweight="bold", va="bottom")
    fig.tight_layout(w_pad=2.2)
    save(fig, "fig1_flatness")


def fig2():
    traces = json.load(open(FIGDIR / "e3_geometry.json"))["traces"]
    by = defaultdict(list)
    for t in traces:
        by[t["label"]].append(t)

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(5.2, 1.7))
    rng = np.random.default_rng(0)
    for i, m in enumerate(MODELS):
        ts = by[m]
        strides = np.array([t["mean_step"] for t in ts])
        x = i + rng.uniform(-0.16, 0.16, len(strides))
        ax_a.scatter(x, strides, s=7, color=COLORS[m], alpha=0.6, lw=0)
        mu = strides.mean()
        ci = 1.96 * strides.std(ddof=1) / np.sqrt(len(strides))
        ax_a.errorbar(i + 0.30, mu, yerr=ci, fmt="o", ms=3.2, color=COLORS[m],
                      ecolor=COLORS[m], elinewidth=1.0, capsize=2)
        ax_b.scatter([t["human_dist_slope"] for t in ts],
                     [t["best_acc"] for t in ts],
                     s=7, color=COLORS[m], alpha=0.75, lw=0)
    ax_a.set_xticks(range(len(MODELS)))
    ax_a.set_xticklabels([LABELS[m] for m in MODELS])
    ax_a.set_xlim(-0.5, len(MODELS) - 0.2)
    ax_a.set_ylabel(r"Mean stride $\bar{s}$ per game")
    ax_a.set_title("Stride: 4B below the larger tiers", pad=3)
    ax_b.axvline(0.0, color="0.55", lw=0.8, ls=(0, (4, 2)))
    lim_b = 0.055
    ax_b.set_xlim(-lim_b, lim_b)
    ax_b.set_xlabel(r"Drift slope $dh/dt$ (solution-aware anchor)")
    ax_b.set_ylabel("Best accuracy")
    ax_b.set_title("Drift slopes cluster near zero", pad=3)
    ax_b.set_ylim(0, 1.05)
    for ax, lab in ((ax_a, "a"), (ax_b, "b")):
        ax.text(-0.24, 1.06, lab, transform=ax.transAxes,
                fontsize=9, fontweight="bold", va="bottom")
    fig.tight_layout(w_pad=2.2)
    save(fig, "fig2_geometry")


def fig3_worked():
    """Appendix story figure: the refsoup_021 game, found at round 10, abandoned."""
    src = ROOT / "results/grid_2026_09/Qwen_Qwen3.5-397B-A17B_s2/curve/round_curve.json"
    r = next(x for x in json.load(open(src))["results"] if x["puzzle_id"] == "refsoup_021")
    acc = {int(k): v for k, v in r["accuracy_by_round"].items()}
    rounds = sorted(acc)
    vals = [acc[k] for k in rounds]

    fig, ax = plt.subplots(figsize=(4.4, 1.55))
    ax.plot(rounds, vals, color=COLORS["Qwen3.5-397B"], lw=1.4, marker="o", ms=2.6)
    ax.axhspan(0.95, 1.03, color="#3B7A3B", alpha=0.10, lw=0)
    ax.text(30.1, 0.965, "solution reached (1.00), rounds 10-11",
            ha="right", va="top", fontsize=6.5, color="#3B7A3B")
    ax.set_xlim(0.5, 30.5)
    ax.set_ylim(0, 1.05)
    ax.set_xticks([1, 10, 20, 30])
    ax.set_xlabel("Round")
    ax.set_ylabel("Checkpoint score")
    fig.tight_layout()
    save(fig, "fig3_worked")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3_worked()
