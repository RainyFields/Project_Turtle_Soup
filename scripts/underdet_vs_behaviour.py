#!/usr/bin/env python3
"""Do the behavioural indicators respond to how under-determined a puzzle is?

The mixed model in Section 5.3 asks whether under-determination predicts the
*score*, and finds it does not. That leaves the question this workshop actually
cares about unasked: whether the puzzle's structure changes what the agent
*does*. This regresses each per-trace indicator on the puzzle's
under-determination, per tier, and reports permutation p-values.

Reads only committed artifacts, so it runs without results/:
    docs/paper/figures/e3_geometry.json   (198 traces)
    data/puzzles/dimensions.json          (22 under-determination scores)

    python scripts/underdet_vs_behaviour.py [--permutations 5000]
"""
from __future__ import annotations

import argparse
import json
import random
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIERS = ["Qwen3.5-4B", "Qwen3.6-27B", "Qwen3.5-397B"]
# best_acc is the outcome; the rest are behaviour. Keeping the outcome in the
# same table is the point: it is the row that does not move either.
INDICATORS = [
    ("best_acc", "best accuracy (outcome)"),
    ("mean_step", "mean stride"),
    ("late_step", "late-game stride"),
    ("human_dist_slope", "drift slope"),
    ("mean_human_dist", "mean anchor distance"),
    ("surface_human_dist_slope", "drift slope (surface anchor)"),
    ("rounds", "rounds played"),
    ("committed", "commit rate"),
]


def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(xs, ys):
    rx, ry = _ranks(xs), _ranks(ys)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else 0.0


def permutation_p(xs, ys, observed, n_perm, rng):
    hits = 0
    shuffled = list(ys)
    for _ in range(n_perm):
        rng.shuffle(shuffled)
        if abs(spearman(xs, shuffled)) >= abs(observed) - 1e-12:
            hits += 1
    return hits / n_perm


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--permutations", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None, help="write results as JSON here")
    args = ap.parse_args()
    rng = random.Random(args.seed)

    traces = json.loads((ROOT / "docs/paper/figures/e3_geometry.json").read_text())["traces"]
    dims = json.loads((ROOT / "data/puzzles/dimensions.json").read_text())
    ud = {k: v["under_determination"] for k, v in dims.items() if v.get("under_determination") is not None}

    # One value per (tier, puzzle): the seeds are replicates, not observations.
    cells = defaultdict(lambda: defaultdict(list))
    for t in traces:
        for key, _ in INDICATORS:
            value = t.get(key)
            if value is not None:
                cells[(t["label"], t["puzzle_id"])][key].append(float(value))

    puzzles = sorted(ud, key=lambda p: ud[p])
    xs = [ud[p] for p in puzzles]
    out = {"n_puzzles": len(puzzles), "permutations": args.permutations, "by_indicator": {}}

    width = max(len(name) for _, name in INDICATORS)
    print(f"Spearman rho against under-determination, {len(puzzles)} puzzles, "
          f"seeds averaged, {args.permutations} permutations\n")
    print(" " * (width + 2) + "".join(f"{t:>22}" for t in TIERS))
    for key, name in INDICATORS:
        row, record = f"  {name:<{width}}", {}
        for tier in TIERS:
            ys = [st.mean(cells[(tier, p)][key]) for p in puzzles]
            rho = spearman(xs, ys)
            p = permutation_p(xs, ys, rho, args.permutations, rng)
            record[tier] = {"rho": round(rho, 3), "p": round(p, 4)}
            row += f"{rho:>+13.3f} p={p:.2f}"
        print(row)
        out["by_indicator"][key] = record

    # Commit rate is the one that moves, so report it pooled and by tercile too.
    pooled = defaultdict(list)
    for t in traces:
        pooled[t["puzzle_id"]].append(1.0 if t["committed"] else 0.0)
    acc = defaultdict(list)
    for t in traces:
        acc[t["puzzle_id"]].append(t["best_acc"])
    commit = [st.mean(pooled[p]) for p in puzzles]
    accuracy = [st.mean(acc[p]) for p in puzzles]
    r_c = spearman(xs, commit)
    r_a = spearman(xs, accuracy)
    out["pooled"] = {
        "commit_rate": {"rho": round(r_c, 3), "p": round(permutation_p(xs, commit, r_c, args.permutations, rng), 4)},
        "best_accuracy": {"rho": round(r_a, 3), "p": round(permutation_p(xs, accuracy, r_a, args.permutations, rng), 4)},
        "commit_vs_accuracy_rho": round(spearman(commit, accuracy), 3),
    }
    n = len(puzzles)
    groups = [puzzles[: n // 3], puzzles[n // 3 : 2 * n // 3], puzzles[2 * n // 3 :]]
    out["terciles"] = [
        {
            "mean_under_determination": round(st.mean([ud[p] for p in g]), 3),
            "commit_rate": round(st.mean([st.mean(pooled[p]) for p in g]), 3),
            "best_accuracy": round(st.mean([st.mean(acc[p]) for p in g]), 3),
        }
        for g in groups
    ]

    print("\nPooled over all 198 traces:")
    print(f"  commit rate     rho={r_c:+.3f} p={out['pooled']['commit_rate']['p']:.3f}")
    print(f"  best accuracy   rho={r_a:+.3f} p={out['pooled']['best_accuracy']['p']:.3f}")
    print(f"  commit vs accuracy rho={out['pooled']['commit_vs_accuracy_rho']:+.3f} "
          "(the two are not independent axes)")
    print("\nBy under-determination tercile:")
    for label, row in zip(("low", "mid", "high"), out["terciles"]):
        print(f"  {label:<5} u={row['mean_under_determination']:.2f}  "
              f"commit {row['commit_rate']:.3f}  accuracy {row['best_accuracy']:.3f}")
    print(f"\n{len(INDICATORS) * len(TIERS)} tests were run; at alpha=0.05 the chance "
          f"expectation is {len(INDICATORS) * len(TIERS) * 0.05:.1f} significant results.")

    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=1, ensure_ascii=False))
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
