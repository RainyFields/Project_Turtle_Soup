#!/usr/bin/env python3
"""Does the Oracle's answer change what the agent does next?

Section 5's Limitations call feedback incorporation "the most direct separator of
the two patterns" and leave it unmeasured. This measures it: for every round we
pair the answer received with the stride taken into the next round, and ask
whether refutation and confirmation move the agent differently.

Round position is a confound and it matters: "yes" answers arrive earlier than
"no" (round ~10 against ~16) and early strides are larger, which manufactures the
effect on its own. Pairs are therefore formed inside (puzzle, round-bin) cells,
and CIs are bootstrapped over puzzles.

    python scripts/feedback_response.py [--out figures/feedback_response.json]
"""
from __future__ import annotations

import argparse
import glob
import json
import random
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_LABEL = {
    "Qwen/Qwen3.5-4B": "Qwen3.5-4B",
    "Qwen/Qwen3.6-27B": "Qwen3.6-27B",
    "Qwen/Qwen3.5-397B-A17B": "Qwen3.5-397B",
}
TIERS = ["Qwen3.5-4B", "Qwen3.6-27B", "Qwen3.5-397B"]
ROUND_BINS = [(1, 5), (6, 10), (11, 15), (16, 20), (21, 25), (26, 29)]


def classify(answer: str) -> str:
    a = answer.strip()
    if a.startswith("是"):
        return "yes"
    if a.startswith("不是"):
        return "no"
    return "irrelevant"


def load(run: Path):
    """Join each round's Oracle answer to the stride taken into the next round."""
    geo = {
        (t["label"], t["puzzle_id"], t["seed"]): t
        for t in json.loads((ROOT / "docs/paper/figures/e3_geometry.json").read_text())["traces"]
    }
    rows, skipped = [], 0
    for path in sorted(glob.glob(str(run / "*/curve/round_curve.json"))):
        report = json.loads(Path(path).read_text())
        tier = MODEL_LABEL[report["questioner"]["model"]]
        for game in report["results"]:
            trace = geo.get((tier, game["puzzle_id"], game.get("seed")))
            qa = game["qa_rounds"]
            # step_sizes[i] is the move from round i+1 into round i+2, so it is
            # the response to the answer given at round i+1.
            if not trace or len(trace["step_sizes"]) != len(qa) - 1:
                skipped += 1
                continue
            for i, stride in enumerate(trace["step_sizes"]):
                rows.append((tier, game["puzzle_id"], i + 1, classify(qa[i]["answer"]), stride))
    return rows, skipped


def bootstrap_ci(by_puzzle, rng, n_boot=4000):
    puzzles = list(by_puzzle)
    means = []
    for _ in range(n_boot):
        sample = [v for p in (rng.choice(puzzles) for _ in puzzles) for v in by_puzzle[p]]
        means.append(st.mean(sample))
    means.sort()
    return means[int(0.025 * n_boot)], means[int(0.975 * n_boot) - 1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="results/grid_2026_09")
    ap.add_argument("--out", default=None)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    rows, skipped = load(ROOT / args.run)
    print(f"{len(rows)} rounds joined; {skipped} games skipped (no matching trace)\n")

    out = {"answer_mix": {}, "round_position": {}, "uncontrolled": {}, "controlled": {}}

    print("Oracle answer mix, and when each answer arrives")
    for tier in TIERS:
        mine = [r for r in rows if r[0] == tier]
        n = len(mine)
        mix = {k: sum(1 for r in mine if r[3] == k) / n for k in ("yes", "no", "irrelevant")}
        pos = {k: st.mean([r[2] for r in mine if r[3] == k]) for k in ("yes", "no")}
        out["answer_mix"][tier] = {k: round(v, 4) for k, v in mix.items()}
        out["round_position"][tier] = {k: round(v, 2) for k, v in pos.items()}
        print(f"  {tier:14} yes {mix['yes']:.1%}  no {mix['no']:.1%}  irrelevant {mix['irrelevant']:.1%}"
              f"   | mean round: yes {pos['yes']:.1f}, no {pos['no']:.1f}")

    print("\nStride after confirmation minus stride after refutation")
    print("  uncontrolled pairs the two within a game; controlled pairs them inside")
    print("  (puzzle, round-bin) cells, which is what removes the position confound.\n")
    for tier in TIERS:
        # Uncontrolled: one difference per game.
        per_game = defaultdict(lambda: {"yes": [], "no": []})
        cells = defaultdict(lambda: {"yes": [], "no": []})
        for t, puzzle, rd, kind, stride in rows:
            if t != tier or kind == "irrelevant":
                continue
            cells[(puzzle, next(i for i, (lo, hi) in enumerate(ROUND_BINS) if lo <= rd <= hi))][kind].append(stride)
        for t, puzzle, rd, kind, stride in rows:
            if t == tier and kind != "irrelevant":
                per_game[puzzle][kind].append(stride)

        raw = {}
        for label, source in (("uncontrolled", per_game), ("controlled", cells)):
            by_puzzle = defaultdict(list)
            for key, v in source.items():
                if v["yes"] and v["no"]:
                    puzzle = key if isinstance(key, str) else key[0]
                    by_puzzle[puzzle].append(st.mean(v["yes"]) - st.mean(v["no"]))
            values = [d for ds in by_puzzle.values() for d in ds]
            mean = st.mean(values)
            lo, hi = bootstrap_ci(by_puzzle, rng)
            raw[label] = {"n_units": len(values), "delta": round(mean, 4),
                          "ci95": [round(lo, 4), round(hi, 4)]}
            out[label][tier] = raw[label]
        u, c = raw["uncontrolled"], raw["controlled"]
        verdict = "responds (inverted)" if c["ci95"][0] > 0 else "no detected response"
        print(f"  {tier:14} uncontrolled {u['delta']:+.4f} [{u['ci95'][0]:+.4f}, {u['ci95'][1]:+.4f}]"
              f"   controlled {c['delta']:+.4f} [{c['ci95'][0]:+.4f}, {c['ci95'][1]:+.4f}]   {verdict}")

    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=1))
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
