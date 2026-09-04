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
    """Per-model: accuracy_by_round arrays and per-game (sustained_peak, final)."""
    curves = defaultdict(lambda: defaultdict(list))
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
                curves[model][rd].append(v)
            vals = [acc[rd] for rd in sorted(acc)]
            speak = max(min(vals[i], vals[i + 1]) for i in range(len(vals) - 1))
            retention[model].append((speak, vals[-1]))
    return curves, retention


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
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(5.6, 2.25))

    for m in MODELS:
        rounds = sorted(curves[m])
        mean = np.array([np.mean(curves[m][rd]) for rd in rounds])
        sem = np.array(
            [np.std(curves[m][rd], ddof=1) / np.sqrt(len(curves[m][rd])) for rd in rounds]
        )
        ax_a.fill_between(rounds, mean - 1.96 * sem, mean + 1.96 * sem,
                          color=COLORS[m], alpha=0.18, lw=0)
        ax_a.plot(rounds, mean, color=COLORS[m], lw=1.4)
        # Dodge the 27B/397B end labels: their final means sit 0.026 apart.
        dodge = {"Qwen3.5-4B": 0, "Qwen3.6-27B": -4, "Qwen3.5-397B": 8}[m]
        ax_a.annotate(LABELS[m], xy=(rounds[-1], mean[-1]),
                      xytext=(3, dodge), textcoords="offset points",
                      va="center", color=COLORS[m], fontsize=7)
    ax_a.set_xlim(1, 33.5)
    ax_a.set_ylim(0, 1.0)
    ax_a.set_xticks([1, 10, 20, 30])
    ax_a.set_xlabel("Round")
    ax_a.set_ylabel("Checkpoint accuracy")
    ax_a.set_title("Gains stop after round ten", pad=3)

    lim = 1.02
    ax_b.plot([0, lim], [0, lim], color="0.55", lw=0.8, ls=(0, (4, 2)))
    ax_b.plot([0, lim], [0, lim / 2], color=ACCENT, lw=0.8, ls=(0, (2, 2)))
    ax_b.annotate("kept all", xy=(0.30, 0.52), ha="left", va="bottom",
                  color="0.4", fontsize=6, rotation=38)
    ax_b.annotate("kept half", xy=(0.72, 0.30), ha="left", va="top",
                  color=ACCENT, fontsize=6, rotation=21)
    for m in MODELS:
        pk, fn = zip(*retention[m])
        ax_b.scatter(pk, fn, s=9, color=COLORS[m], alpha=0.75, lw=0,
                     label=LABELS[m])
    ax_b.set_xlim(0, lim)
    ax_b.set_ylim(0, lim)
    ax_b.set_xlabel("Sustained peak (best held 2 rounds)")
    ax_b.set_ylabel("Final-round score")
    ax_b.set_title("Models keep ~0.7 of what they find", pad=3)
    ax_b.legend(loc="upper left", handletextpad=0.1, borderaxespad=0.2,
                labelspacing=0.2)

    for ax, lab in ((ax_a, "a"), (ax_b, "b")):
        ax.text(-0.18, 1.06, lab, transform=ax.transAxes,
                fontsize=9, fontweight="bold", va="bottom")
    fig.tight_layout(w_pad=2.2)
    save(fig, "fig1_flatness")


def fig2():
    traces = json.load(open(FIGDIR / "e3_geometry.json"))["traces"]
    by = defaultdict(list)
    for t in traces:
        by[t["label"]].append(t)

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(5.6, 2.25))
    for m in MODELS:
        ts = by[m]
        ax_a.scatter([t["mean_step"] for t in ts], [t["best_acc"] for t in ts],
                     s=9, color=COLORS[m], alpha=0.75, lw=0, label=LABELS[m])
        ax_b.scatter([t["human_dist_slope"] for t in ts], [t["best_acc"] for t in ts],
                     s=9, color=COLORS[m], alpha=0.75, lw=0)
    ax_a.set_xlabel(r"Mean stride $\bar{s}$")
    ax_a.set_ylabel("Best checkpoint accuracy")
    ax_a.set_title("Circling: small model, small strides", pad=3)
    ax_a.legend(loc="upper right", handletextpad=0.1, borderaxespad=0.2,
                labelspacing=0.2)
    ax_b.axvline(0.0, color="0.55", lw=0.8, ls=(0, (4, 2)))
    ax_b.set_xlabel(r"Drift slope $dh/dt$")
    ax_b.set_ylabel("Best checkpoint accuracy")
    ax_b.set_title("Drift barely appears at any scale", pad=3)
    for ax, lab in ((ax_a, "a"), (ax_b, "b")):
        ax.set_ylim(0, 1.05)
        ax.text(-0.18, 1.06, lab, transform=ax.transAxes,
                fontsize=9, fontweight="bold", va="bottom")
    fig.tight_layout(w_pad=2.2)
    save(fig, "fig2_geometry")


if __name__ == "__main__":
    fig1()
    fig2()
