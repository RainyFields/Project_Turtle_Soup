#!/usr/bin/env python3
"""Figure for the v0.15 spine: the answer barely changes what the agent does next.

(a) Stride after confirmation minus stride after refutation, per tier, paired
    inside (puzzle, round-bin) cells so the earlier arrival of yes cannot
    manufacture the effect. A rational searcher would sit left of zero.
(b) Why the geometry describes these failures without scoring them: in
    abandoning games the move that loses the answer is the same semantic size as
    ordinary within-game motion.

House style follows docs/paper/figures/make_figures.py. The nature-figure
alignment audit runs when that skill is installed and is skipped otherwise, so
this is runnable on a machine without it.

    python docs/paper/figures/make_feedback_figure.py
"""
from __future__ import annotations

import glob
import json
import random
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FIGDIR = ROOT / "docs/paper/figures"
sys.path.insert(0, str(ROOT))

SKILL_SCRIPTS = Path.home() / ".claude/skills/nature-figure/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
try:
    from audit_panel_alignment import require_matplotlib_panel_alignment
except ImportError:  # skill not installed on this machine
    require_matplotlib_panel_alignment = None

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

MODELS = ["Qwen3.5-4B", "Qwen3.6-27B", "Qwen3.5-397B"]
LABELS = {"Qwen3.5-4B": "4B", "Qwen3.6-27B": "27B", "Qwen3.5-397B": "397B"}
COLORS = {"Qwen3.5-4B": "#9DB8D9", "Qwen3.6-27B": "#4C7BB8", "Qwen3.5-397B": "#173A66"}
ACCENT = "#C0504D"
MODEL_KEY = {
    "Qwen/Qwen3.5-4B": "Qwen3.5-4B",
    "Qwen/Qwen3.6-27B": "Qwen3.6-27B",
    "Qwen/Qwen3.5-397B-A17B": "Qwen3.5-397B",
}
BINS = [(1, 5), (6, 10), (11, 15), (16, 20), (21, 25), (26, 29)]
RUN = ROOT / "results/grid_2026_09"


def games():
    geo = {
        (t["label"], t["puzzle_id"], t["seed"]): t
        for t in json.loads((FIGDIR / "e3_geometry.json").read_text())["traces"]
    }
    for path in sorted(glob.glob(str(RUN / "*/curve/round_curve.json"))):
        report = json.loads(Path(path).read_text())
        tier = MODEL_KEY[report["questioner"]["model"]]
        for game in report["results"]:
            trace = geo.get((tier, game["puzzle_id"], game.get("seed")))
            if trace and len(trace["step_sizes"]) == len(game["qa_rounds"]) - 1:
                yield tier, game, trace


def panel_a(ax, rng):
    """Show the two quantities being compared, not their difference.

    An earlier version plotted only the delta. A reader arriving at the figure
    cold could not see what was differenced, had no definition of stride, and
    had no reason to think a positive value was the wrong sign. This plots both
    adjusted means, joins them with an arrow in the direction the model actually
    moves, and says on the panel what the rational direction would be.

    Means are adjusted for round position: yes arrives around round 10 and no
    around round 16, and early strides are larger, so raw means would show the
    effect even if none existed. Each stride has its (puzzle, round-bin) mean
    removed and the tier's grand mean added back, which leaves the difference
    equal to the controlled estimate reported in the text.
    """
    cells = defaultdict(lambda: defaultdict(lambda: {"yes": [], "no": []}))
    for tier, game, trace in games():
        for i, stride in enumerate(trace["step_sizes"]):
            answer = game["qa_rounds"][i]["answer"].strip()
            kind = "yes" if answer.startswith("\u662f") else "no" if answer.startswith("\u4e0d\u662f") else None
            if kind is None:
                continue
            b = next(k for k, (lo, hi) in enumerate(BINS) if lo <= i + 1 <= hi)
            cells[tier][(game["puzzle_id"], b)][kind].append(stride)

    for y, tier in enumerate(MODELS):
        usable = {k: v for k, v in cells[tier].items() if v["yes"] and v["no"]}
        grand = st.mean([x for v in usable.values() for x in v["yes"] + v["no"]])
        yes_adj, no_adj, by_puzzle = [], [], defaultdict(list)
        for (puzzle, _), v in usable.items():
            cell_mean = st.mean(v["yes"] + v["no"])
            yes_adj.append(st.mean(v["yes"]) - cell_mean + grand)
            no_adj.append(st.mean(v["no"]) - cell_mean + grand)
            by_puzzle[puzzle].append(st.mean(v["yes"]) - st.mean(v["no"]))
        my, mn = st.mean(yes_adj), st.mean(no_adj)
        puzzles = list(by_puzzle)
        boot = sorted(
            st.mean([x for p in (rng.choice(puzzles) for _ in puzzles) for x in by_puzzle[p]])
            for _ in range(4000)
        )
        lo, hi, delta = boot[100], boot[3899], my - mn
        c = COLORS[tier]
        ax.annotate("", xy=(my, y), xytext=(mn, y),
                    arrowprops=dict(arrowstyle="-|>", color=c, lw=1.3, shrinkA=2, shrinkB=2))
        ax.plot([mn], [y], "o", mfc="white", mec=c, mew=1.2, ms=5.5, zorder=3)
        ax.plot([my], [y], "o", color=c, ms=5.5, zorder=3)
        sig = "" if lo <= 0 <= hi else "*"
        ax.text(max(my, mn) + 0.006, y, f"{delta:+.3f}{sig}", va="center", fontsize=6, color=c)

    # Direct labels on the top row instead of a legend: a legend would sit in the
    # same corner as the smallest tier's markers, and the reader would have to
    # look away from the data to decode the two symbols.
    # Label the row with the widest gap; on the narrowest one the two texts
    # would overlap each other.
    top = 1
    ref = cells[MODELS[top]]
    usable = {k: v for k, v in ref.items() if v["yes"] and v["no"]}
    grand = st.mean([x for v in usable.values() for x in v["yes"] + v["no"]])
    mn_top = st.mean([st.mean(v["no"]) - st.mean(v["yes"] + v["no"]) + grand for v in usable.values()])
    my_top = st.mean([st.mean(v["yes"]) - st.mean(v["yes"] + v["no"]) + grand for v in usable.values()])
    # Short labels: the title and the axis already say what "no" and "yes" mean,
    # and the full phrases were wide enough to run into each other.
    ax.annotate("no", xy=(mn_top, top - 0.14), xytext=(mn_top - 0.010, top - 0.46),
                fontsize=6, color="0.35", ha="center",
                arrowprops=dict(arrowstyle="-", color="0.65", lw=0.6))
    ax.annotate("yes", xy=(my_top, top - 0.14), xytext=(my_top + 0.010, top - 0.46),
                fontsize=6, color="0.35", ha="center",
                arrowprops=dict(arrowstyle="-", color="0.65", lw=0.6))
    ax.set_yticks(range(len(MODELS)))
    ax.set_yticklabels([LABELS[m] for m in MODELS])
    ax.set_ylim(-0.5, len(MODELS) + 0.15)
    ax.set_xlim(0.030, 0.200)
    ax.set_xlabel("Mean stride, round-adjusted")
    ax.set_title("Stride by answer received", pad=4, loc="left")


def panel_b(ax):
    """Embed each game's checkpoints once, then read every pair off the matrix.

    Pairing texts and embedding each pair separately would re-embed the same
    story up to thirty times; this is the same numbers at 1/400th the calls.
    """
    from evaluation.trajectory import embed

    rows, abandon = [], []
    for tier, game, _ in games():
        cp = {int(k): v for k, v in (game.get("checkpoints_by_round") or {}).items()}
        acc = {int(k): v for k, v in (game.get("accuracy_by_round") or {}).items()}
        if len(cp) < 5 or not acc:
            continue
        keys = sorted(cp)
        V = embed([cp[k] for k in keys])
        rows.append((game["puzzle_id"], keys, V))
        peak, last = max(acc, key=lambda k: acc[k]), max(cp)
        if acc[peak] >= 0.3 and acc[last] < acc[peak] * 0.5 and peak in cp and last in cp:
            abandon.append(float(V[keys.index(peak)] @ V[keys.index(last)]))

    within = [
        float(V[i] @ V[j])
        for _, keys, V in rows
        for i in range(len(keys))
        for j in range(i + 1, len(keys))
    ]
    finals = {}
    for puzzle, keys, V in rows:
        finals.setdefault(puzzle, V[-1])
    names_ = sorted(finals)
    cross = [
        float(finals[names_[i]] @ finals[names_[j]])
        for i in range(len(names_))
        for j in range(i + 1, len(names_))
    ]

    # Horizontal, so the three distributions read as one scale the eye can walk
    # along, and so the labels can be written as full questions rather than as
    # terms the reader would have to have learnt from Section 5.
    data = [cross, within, abandon]
    names = ["different puzzles", "same game,\nany two rounds", "peak $\\to$ final,\nabandoning games"]
    colors = ["#9DB8D9", "#4C7BB8", ACCENT]
    parts = ax.violinplot(data, positions=range(3), widths=0.75, vert=False,
                          showextrema=False, showmedians=False)
    for body, c in zip(parts["bodies"], colors):
        body.set_facecolor(c)
        body.set_alpha(0.38)
        body.set_edgecolor("none")
    for i, (vals, c) in enumerate(zip(data, colors)):
        ax.plot([st.median(vals)] * 2, [i - 0.24, i + 0.24], color=c, lw=1.8)
        # Top distribution labels above, the others below: stacked horizontally
        # they would otherwise land on each other's neighbours.
        off, va = (0.40, "bottom") if i == 2 else (-0.40, "top")
        ax.text(st.median(vals), i + off, f"{st.median(vals):.2f}", ha="center",
                va=va, fontsize=6, color=c)
    ax.set_yticks(range(3))
    ax.set_yticklabels(names, fontsize=6.0)
    ax.set_xlabel("Cosine similarity")
    ax.set_xlim(0.18, 1.06)
    ax.set_ylim(-0.8, 3.0)
    ax.set_title("Distance between stories", pad=4, loc="left")
    return {"abandon_median": round(st.median(abandon), 4), "n_abandon": len(abandon),
            "within_median": round(st.median(within), 4), "n_within": len(within),
            "cross_median": round(st.median(cross), 4), "n_cross": len(cross)}


def panel_mid(ax):
    """Found, and not volunteered: the middle link of the argument.

    Solid bar is games that reached a solution-grade answer (sustained peak at
    or above half the scale); the hatched bar is how many of those the agent
    ever volunteered of its own accord.
    """
    sol, com = {}, {}
    for tier, game, _ in games():
        acc = {int(k): v for k, v in (game.get("accuracy_by_round") or {}).items()}
        if not acc:
            continue
        v = [acc[k] for k in sorted(acc)]
        sustained = max((min(v[i], v[i + 1]) for i in range(len(v) - 1)), default=0.0)
        sol.setdefault(tier, 0); com.setdefault(tier, 0)
        if sustained >= 0.5:
            sol[tier] += 1
            com[tier] += 1 if game.get("natural_final_answer") else 0
    w = 0.36
    for i, tier in enumerate(MODELS):
        c = COLORS[tier]
        ax.bar(i - w / 2, sol.get(tier, 0), w, color=c, lw=0)
        ax.bar(i + w / 2, com.get(tier, 0), w, facecolor="white", edgecolor=c,
               lw=0.9, hatch="////")
        for x, n in ((i - w / 2, sol.get(tier, 0)), (i + w / 2, com.get(tier, 0))):
            ax.text(x, n + 0.18, str(n), ha="center", fontsize=6.2, color=c)
    ax.set_xticks(range(3))
    ax.set_xticklabels([LABELS[m] for m in MODELS])
    ax.set_ylim(0, 8.2)
    ax.set_yticks([0, 2, 4, 6, 8])
    ax.set_ylabel("Games (of 66)")
    ax.set_title("Solution-grade games", pad=4, loc="left")


def main() -> None:
    rng = random.Random(0)
    fig, (ax_a, ax_m, ax_b) = plt.subplots(1, 3, figsize=(6.9, 1.9),
                                           gridspec_kw={"width_ratios": [1.0, 0.85, 1.05]})
    panel_a(ax_a, rng)
    panel_mid(ax_m)
    stats = panel_b(ax_b)
    for ax, lab in ((ax_a, "a"), (ax_m, "b"), (ax_b, "c")):
        ax.text(-0.20, 1.20, lab, transform=ax.transAxes, fontsize=8.5,
                fontweight="bold", va="top")
    fig.tight_layout(w_pad=2.2)

    stem = "fig_feedback"
    if require_matplotlib_panel_alignment is not None:
        require_matplotlib_panel_alignment(
            fig,
            json_out=str(FIGDIR / f"{stem}.alignment.json"),
            overlay_svg=str(FIGDIR / f"{stem}.alignment.svg"),
            tolerance_pt=1.5,
            gutter_tolerance_pt=1.5,
            strict=True,
        )
    else:
        print("note: nature-figure skill not installed here; alignment audit skipped")
    fig.savefig(FIGDIR / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(FIGDIR / f"{stem}.png", dpi=400, bbox_inches="tight")
    print("wrote", stem, json.dumps(stats))


if __name__ == "__main__":
    main()
