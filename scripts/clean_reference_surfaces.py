#!/usr/bin/env python3
"""Repair surfaces damaged by the source site's own formatting.

Three defects seen in the 经典 import:
  * the site truncates long surfaces to a placeholder and prints the real
    surface inside the solution body under a "汤面：" heading;
  * a scrape artefact ("提问次数：30次") is prepended to the surface;
  * an author's preamble ("ps. 这个汤是根据…改编的") precedes the surface.

Run with --dry-run first; every change is printed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.schema import puzzle_dict_to_json_ready, validate_puzzle

PLACEHOLDER = re.compile(r"汤面太长|点击去汤底|详见汤底")
SCRAPE_NOISE = re.compile(r"^\s*提问次数\s*[:：]\s*\d+\s*次\s*")
AUTHOR_NOTE = re.compile(r"^\s*ps[.．]\s*[^\n]*?(改编|设定)[^\n]*?(推理|剧情)[^\n]*?\s")
SURFACE_IN_SOLUTION = re.compile(r"汤面\s*[:：]\s*(.+?)(?=\s*汤底\s*[:：]|\Z)", re.DOTALL)


def repair(data: dict) -> tuple[dict, list[str]]:
    surface, solution = data["surface"], data["solution"]
    notes: list[str] = []

    if PLACEHOLDER.search(surface):
        m = SURFACE_IN_SOLUTION.search(solution)
        if m:
            recovered = m.group(1).strip()
            solution = solution[m.end():].strip() or solution
            surface = recovered
            notes.append("汤面从汤底中恢复")
        else:
            notes.append("⚠️ 汤面是占位符但无法恢复")

    cleaned = SCRAPE_NOISE.sub("", surface)
    if cleaned != surface:
        surface, _ = cleaned, notes.append("去除抓取噪声「提问次数」")

    cleaned = AUTHOR_NOTE.sub("", surface)
    if cleaned != surface:
        surface, _ = cleaned, notes.append("去除作者前言")

    data = {**data, "surface": surface.strip(), "solution": solution.strip()}
    return data, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", default="real")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    directory = ROOT / "data" / "puzzles" / args.family
    changed = 0
    for path in sorted(directory.glob("refsoup_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        fixed, notes = repair(data)
        if not notes:
            continue
        print(f"{data['id']} [{data.get('title','')[:16]}] — {'; '.join(notes)}")
        print(f"   旧汤面: {data['surface'][:70]}")
        print(f"   新汤面: {fixed['surface'][:70]}")
        if args.dry_run:
            continue
        fixed = puzzle_dict_to_json_ready(fixed)
        ok, errors = validate_puzzle(fixed, for_publish=True)
        if not ok:
            print(f"   ⚠️ schema 失败，跳过: {errors}")
            continue
        path.write_text(json.dumps(fixed, ensure_ascii=False, indent=2), encoding="utf-8")
        changed += 1
    print(f"\n{'(dry-run) ' if args.dry_run else ''}修复 {changed} 道")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
