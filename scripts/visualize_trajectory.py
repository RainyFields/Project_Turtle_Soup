#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.trajectory import load_trajectory


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Print a human-readable trajectory")
    p.add_argument("trajectory", type=Path, help="Path to trajectory JSON")
    return p


def main() -> int:
    args = build_parser().parse_args()
    traj = load_trajectory(args.trajectory)

    print(f"Game: {traj.game_id}")
    print(f"Puzzle: {traj.puzzle_id}")
    print(f"Oracle: {traj.oracle_model}")
    print(f"Questioner: {traj.questioner_model}")
    print(f"Rounds: {traj.total_rounds} | End: {traj.terminated_by}")
    print()

    for r in traj.trajectory:
        print(f"--- Round {r.round} ---")
        print(f"Q: {r.question}")
        print(f"A: {r.answer}")
        if r.oracle_reasoning:
            print(f"  {r.oracle_reasoning}")
        print()

    if traj.final_answer:
        print(f"Final answer: {traj.final_answer}")
    if traj.evaluation:
        print(f"Evaluation: {traj.evaluation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
