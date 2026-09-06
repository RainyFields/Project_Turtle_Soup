#!/usr/bin/env python3
"""Pre-flight: can each puzzle actually be played, and at what token budget?

Reasoning models spend their output budget thinking before emitting anything, and
short, abstract surfaces need more of it. Under too small a budget the Questioner
returns empty content, the turn is discarded, and a whole game can end with zero
rounds played. Finding that one puzzle at a time costs a game each; this finds it
for the whole set in one call per puzzle per budget.

    python scripts/check_puzzle_runnability.py --budgets 512 2048 8192
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from agents.provider_factory import get_provider
from agents.questioner_agent import QUESTIONER_SYSTEM_TEMPLATE
from engine.game import has_question_content, list_puzzle_ids, load_puzzle


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="openrouter")
    ap.add_argument("--model", default="z-ai/glm-5.3-flash")
    ap.add_argument("--family", default="real")
    ap.add_argument("--budgets", nargs="+", type=int, default=[2048, 8192, 16384])
    # One probe per budget mis-classifies: the same puzzle came back ok at 512 and
    # empty at 2048 on separate single draws, so emptiness is partly sampling
    # noise rather than a clean budget threshold. A puzzle counts as playable at a
    # budget if any attempt produces a question.
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    provider = get_provider(args.provider)
    ids = args.only or list_puzzle_ids(family=args.family)
    print(f"probes per budget: {args.attempts}\n")
    print(f"{'puzzle':<14}{'surface':>8}  " + "".join(f"{b:>9}" for b in args.budgets))
    print("-" * (24 + 9 * len(args.budgets)))

    needs = {}
    for pid in ids:
        puzzle = load_puzzle(pid)
        system = QUESTIONER_SYSTEM_TEMPLATE.format(
            surface=puzzle["surface"], qa_history="(无)", min_questions=0
        )
        row, smallest_ok = [], None
        for budget in args.budgets:
            wins = 0
            for _ in range(args.attempts):
                try:
                    out = provider.generate(
                        system=system, user="请继续。", model=args.model, max_tokens=budget
                    )
                    wins += bool(has_question_content(out))
                except Exception:
                    pass
            row.append(f"{wins}/{args.attempts}")
            if wins and smallest_ok is None:
                smallest_ok = budget
        needs[pid] = smallest_ok
        print(
            f"{pid:<14}{len(puzzle['surface']):>8}  "
            + "".join(f"{c:>9}" for c in row)
            + ("" if smallest_ok else "   ← unplayable at every budget tried")
        )

    unplayable = [p for p, b in needs.items() if b is None]
    worst = max((b for b in needs.values() if b), default=None)
    print(f"\nsmallest budget that works for every playable puzzle: {worst}")
    if unplayable:
        print(f"never produced a question: {', '.join(unplayable)}")
    return 1 if unplayable else 0


if __name__ == "__main__":
    raise SystemExit(main())
