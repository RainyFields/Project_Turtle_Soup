#!/usr/bin/env python3
"""Oracle audit: probe a candidate Oracle with held-out (question, expected) pairs.

The paper's methodological prerequisite (E-prereq): a weak Oracle collapses
questions to 与此无关 and makes every game unwinnable, so Oracle accuracy must
be established before any Questioner claim. Pass bar: >=90% on yes/no items.
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

from agents.base_agent import ModelConfig
from agents.oracle_agent import OracleAgent
from engine.config import AppConfig, GameConfig
from engine.game import TurtleSoupGame, load_puzzle

# Hand-crafted probes; expected in {是, 不是, 与此无关}.
PROBES = {
    "refsoup_006": [
        ("死者是从高处坠落死亡的吗？", "是"),
        ("死者生前参与了抽签吗？", "是"),
        ("死者是渴死的吗？", "不是"),
        ("半根火柴和抽签有关吗？", "是"),
        ("死者当时乘坐热气球吗？", "是"),
        ("行李是为了减轻重量被扔下来的吗？", "是"),
        ("死者是本地沙漠居民吗？", "不是"),
        ("死者手里的火柴是用来生火做饭的吗？", "不是"),
        ("这个故事和外星人有关吗？", "与此无关"),
        ("当天下雨了吗？", "与此无关"),
    ],
    "turtle_001": [
        ("男人以前喝过所谓的海龟汤吗？", "是"),
        ("这次的海龟汤味道和他记忆中的不同吗？", "是"),
        ("男人曾经历过海难吗？", "是"),
        ("男人自杀是因为汤太难喝吗？", "不是"),
        ("男人的妻子还活着吗？", "不是"),
        ("餐厅老板毒死了他吗？", "不是"),
        ("男人自杀与他意识到当年的真相有关吗？", "是"),
        ("男人是一名厨师吗？", "与此无关"),
    ],
}


def normalize(ans: str) -> str:
    a = ans.strip()
    if a.startswith("是"):
        return "是"
    if a.startswith("不是") or a.startswith("否"):
        return "不是"
    return "与此无关"


def main() -> int:
    p = argparse.ArgumentParser(description="Audit an Oracle on held-out probes")
    p.add_argument("--provider", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--max-tokens", type=int, default=1024)
    args = p.parse_args()

    hard_total = hard_ok = irr_total = irr_ok = irr_soft = 0
    for pid, probes in PROBES.items():
        puzzle = load_puzzle(pid)
        app = AppConfig(
            oracle=ModelConfig(provider=args.provider, model=args.model, max_tokens=args.max_tokens),
            questioner=ModelConfig(provider="mock", model="mock"),
            game=GameConfig(max_rounds=1, save_trajectory=False),
        )
        game = TurtleSoupGame(puzzle, app_config=app)
        for q, expected in probes:
            got = normalize(game.oracle.answer(q))
            mark = "✓" if got == expected else "✗"
            if expected == "与此无关":
                irr_total += 1
                irr_ok += got == expected
                irr_soft += got in ("与此无关", "不是")
            else:
                hard_total += 1
                hard_ok += got == expected
            print(f"  [{mark}] {pid} | {q}  期望 {expected} / 实得 {got}")

    print(f"\nyes/no items: {hard_ok}/{hard_total} = {hard_ok/hard_total:.0%}  (pass bar 90%)")
    print(f"irrelevant items: exact {irr_ok}/{irr_total}, soft(含不是) {irr_soft}/{irr_total}")
    return 0 if hard_ok / hard_total >= 0.9 else 1


if __name__ == "__main__":
    raise SystemExit(main())
