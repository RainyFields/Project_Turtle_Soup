#!/usr/bin/env python3
"""Figure 1. Panel (a) is the round curve; (b) is what the paper asks about.

Two other panel-(b) designs were tried and are kept as functions rather than
outputs: plateau height against slope (redundant with panel a) and reached
against volunteered (too few counts to carry half a figure). Pass --all to
render them.

The rejected first attempt put a large question mark and a bulleted box in (b).
That reads as a slide: the argument was carried by prose, not by the marks. In
all three options here (b) is data, and the question is one short line anchored
to it.

Panel (a) keeps the full 0-1 axis, because autoscaling a flat curve renders its
noise as a trend, and keeps the inset, because at full range the early rise is
otherwise invisible.

    python docs/paper/figures/make_intro_options.py
"""
from __future__ import annotations

import glob, json, random, statistics as st, sys
from collections import defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FIGDIR = ROOT / "docs/paper/figures"
RUN = ROOT / "results/grid_2026_09"
sys.path.insert(0, str(Path.home() / ".claude/skills/nature-figure/scripts"))
try:
    from audit_panel_alignment import require_matplotlib_panel_alignment
except ImportError:
    require_matplotlib_panel_alignment = None

mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 7, "axes.titlesize": 7.5,
    "axes.spines.right": False, "axes.spines.top": False, "axes.linewidth": 0.8,
    "legend.frameon": False,
})
MODELS = ["Qwen3.5-4B", "Qwen3.6-27B", "Qwen3.5-397B"]
LAB = {"Qwen3.5-4B": "4B", "Qwen3.6-27B": "27B", "Qwen3.5-397B": "397B"}
COL = {"Qwen3.5-4B": "#9DB8D9", "Qwen3.6-27B": "#4C7BB8", "Qwen3.5-397B": "#173A66"}
ACCENT = "#C0504D"
KEY = {"Qwen/Qwen3.5-4B": "Qwen3.5-4B", "Qwen/Qwen3.6-27B": "Qwen3.6-27B",
       "Qwen/Qwen3.5-397B-A17B": "Qwen3.5-397B"}


def load():
    by = defaultdict(lambda: defaultdict(list))
    games = defaultdict(list)
    for path in sorted(glob.glob(str(RUN / "*/curve/round_curve.json"))):
        rep = json.loads(Path(path).read_text())
        tier = KEY[rep["questioner"]["model"]]
        for g in rep["results"]:
            acc = {int(k): v for k, v in (g.get("accuracy_by_round") or {}).items()}
            if not acc:
                continue
            by[tier][g["puzzle_id"]].append(acc)
            vals = [acc[r] for r in sorted(acc)]
            sustained = max((min(vals[i], vals[i + 1]) for i in range(len(vals) - 1)), default=0.0)
            games[tier].append((sustained, vals[-1], bool(g.get("natural_final_answer"))))
    return by, games


def panel_a(ax, by, rng):
    rounds = np.arange(1, 31)
    for tier in MODELS:
        pp = by[tier]
        mean = [st.mean([a[r] for g in pp.values() for a in g if r in a]) for r in rounds]
        keys = list(pp)
        boot = [[st.mean([a[r] for g in (pp[k] for k in (rng.choice(keys) for _ in keys))
                          for a in g if r in a]) for r in rounds] for _ in range(400)]
        arr = np.array(boot)
        c = COL[tier]
        ax.plot(rounds, mean, lw=1.5, color=c, zorder=3)
        ax.fill_between(rounds, np.percentile(arr, 2.5, 0), np.percentile(arr, 97.5, 0),
                        color=c, alpha=0.15, lw=0)
        nudge = {"Qwen3.5-397B": +0.030, "Qwen3.6-27B": -0.030}.get(tier, 0.0)
        ax.text(30.7, mean[-1] + nudge, LAB[tier], color=c, fontsize=6.2, va="center")
    ax.axvline(10, color="0.6", lw=0.7, ls=(0, (2, 2)))
    ax.set_xlim(1, 34); ax.set_ylim(0, 1.0)
    ax.set_xlabel("Round"); ax.set_ylabel("Checkpoint accuracy")
    ax.set_title("Gains stop after round ten", pad=3, loc="left")

    ins = ax.inset_axes([0.36, 0.55, 0.60, 0.40])
    for tier in MODELS:
        pp = by[tier]
        m = [st.mean([a[r] for g in pp.values() for a in g if r in a]) for r in range(1, 15)]
        ins.plot(range(1, 15), m, lw=1.2, color=COL[tier])
    ins.axvline(10, color="0.6", lw=0.6, ls=(0, (2, 2)))
    ins.set_xlim(1, 14); ins.set_ylim(0, 0.26)
    ins.set_xticks([1, 10]); ins.set_yticks([0, 0.2])
    ins.tick_params(labelsize=5.2, length=2, pad=1)
    ins.set_title("rounds 1–14", fontsize=5.4, pad=1.5)


def opt1(ax, by, games):
    """Height climbs, slope stays at zero."""
    for i, tier in enumerate(MODELS):
        pp = by[tier]
        lvl = st.mean([a[r] for g in pp.values() for a in g for r in a if r >= 10])
        sl = st.mean([a[30] - a[10] for g in pp.values() for a in g if 30 in a and 10 in a])
        c = COL[tier]
        ax.barh(i, lvl, height=0.42, color=c, alpha=0.85, lw=0)
        ax.annotate("", xy=(lvl + 0.075 + sl * 3, i), xytext=(lvl + 0.02, i),
                    arrowprops=dict(arrowstyle="-|>", color=c, lw=1.2))
        ax.text(lvl + 0.10, i, f"slope {sl:+.3f}", fontsize=5.8, color="0.4", va="center")
    ax.set_yticks(range(3)); ax.set_yticklabels([LAB[m] for m in MODELS])
    ax.set_xlim(0, 0.33); ax.set_ylim(-0.75, 2.6)
    ax.set_xlabel("Height of the plateau (rounds 10–30)")
    ax.annotate("", xy=(0.203, 2.32), xytext=(0.056, 2.32),
                arrowprops=dict(arrowstyle="<->", color=ACCENT, lw=0.8))
    ax.text(0.13, 2.42, "3.6×", fontsize=6.4, color=ACCENT, ha="center")
    ax.set_title("Plateau height and slope", pad=3, loc="left")


def opt_stride(ax, by, games):
    """Stride contracts four- to fivefold while accuracy stands still.

    This replaces a peak-versus-final panel. That panel plotted the gap between
    a maximum and one particular element of the same noisy sequence, which a
    within-game permutation null reproduces (Appendix C); it showed something
    the paper's own null test cannot separate from scoring jitter. Stride
    contraction is a direct measurement with no selection step, and together
    with panel (a) it is the title: narrowing, without converging.
    """
    import glob, json
    from pathlib import Path
    geo = json.loads((FIGDIR / "e3_geometry.json").read_text())["traces"]
    per = defaultdict(lambda: defaultdict(list))
    for t in geo:
        for i, s_ in enumerate(t["step_sizes"]):
            per[t["label"]][i + 1].append(s_)
    for tier in MODELS:
        rounds = sorted(r for r in per[tier] if r <= 29)
        mean = [st.mean(per[tier][r]) for r in rounds]
        c = COL[tier]
        ax.plot(rounds, mean, lw=1.5, color=c)
        # 27B and 397B end within 0.01 of each other; nudge the labels apart.
        nudge = {"Qwen3.6-27B": +0.011, "Qwen3.5-397B": -0.011}.get(tier, 0.0)
        ax.text(rounds[-1] + 0.7, mean[-1] + nudge, LAB[tier], color=c,
                fontsize=6.2, va="center")
    ax.set_xlim(1, 33)
    ax.set_ylim(0, 0.26)
    ax.set_xlabel("Round")
    ax.set_ylabel("Semantic stride")
    ax.set_title("Stride contracts four- to fivefold", pad=3, loc="left")
    ax.grid(alpha=0.18)


def opt2(ax, by, games):
    """What is found, versus what survives to the end."""
    for i, tier in enumerate(MODELS):
        pk = st.mean([g[0] for g in games[tier]])
        fi = st.mean([g[1] for g in games[tier]])
        c = COL[tier]
        ax.plot([0, 1], [pk, fi], color=c, lw=1.4, marker="o", ms=5, zorder=3)
        ax.text(-0.06, pk, LAB[tier], color=c, fontsize=6.2, ha="right", va="center")
        ax.text(1.05, fi, f"−{(pk-fi)/pk:.0%}", color=c, fontsize=5.8, va="center")
    ax.set_xlim(-0.30, 1.30); ax.set_ylim(0, 0.36)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["best reached", "final"], fontsize=6.4)
    ax.set_ylabel("Accuracy")
    ax.set_title("Best reached vs. final", pad=3, loc="left")


def opt3(ax, by, games):
    """Counts: reaching a solution-grade answer, and volunteering it."""
    w = 0.34
    for i, tier in enumerate(MODELS):
        sol = sum(1 for g in games[tier] if g[0] >= 0.5)
        com = sum(1 for g in games[tier] if g[0] >= 0.5 and g[2])
        c = COL[tier]
        ax.bar(i - w / 2, sol, w, color=c, alpha=0.85, lw=0)
        ax.bar(i + w / 2, com, w, color=c, alpha=0.30, lw=0,
               edgecolor=c, hatch="///")
        ax.text(i - w / 2, sol + 0.4, str(sol), ha="center", fontsize=6.2, color=c)
        ax.text(i + w / 2, com + 0.4, str(com), ha="center", fontsize=6.2, color=c)
    ax.set_xticks(range(3)); ax.set_xticklabels([LAB[m] for m in MODELS])
    ax.set_ylim(0, 15); ax.set_ylabel("Games out of 66")
    ax.set_title("Reached vs. volunteered", pad=3, loc="left")


def build(name, fn, by, games):
    rng = random.Random(0)
    fig, (a, b) = plt.subplots(1, 2, figsize=(5.6, 2.0),
                               gridspec_kw={"width_ratios": [1.0, 0.95]})
    panel_a(a, by, rng)
    fn(b, by, games)
    for ax, lab in ((a, "a"), (b, "b")):
        ax.text(-0.16, 1.16, lab, transform=ax.transAxes, fontsize=8.5,
                fontweight="bold", va="top")
    fig.tight_layout(w_pad=2.4)
    fig.savefig(FIGDIR / f"{name}.png", dpi=340, bbox_inches="tight")
    fig.savefig(FIGDIR / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


if __name__ == "__main__":
    import sys
    by, games = load()
    build("fig1_plateau", opt_stride, by, games)
    if "--all" in sys.argv:
        build("fig1_alt_height", opt1, by, games)
        build("fig1_alt_counts", opt3, by, games)
        build("fig1_alt_peakfinal", opt2, by, games)
