#!/usr/bin/env python3
"""Refresh key_clues on existing refsoup_*.json using keyword extraction."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.reference.key_clues import extract_key_clues
from generator.schema import puzzle_dict_to_json_ready, validate_puzzle


def main() -> int:
    puzzles_dir = ROOT / "data" / "puzzles"
    updated = 0
    for path in sorted(puzzles_dir.glob("refsoup_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        clues = extract_key_clues(data.get("surface", ""), data.get("solution", ""))
        data["key_clues"] = clues
        data = puzzle_dict_to_json_ready(data)
        ok, errors = validate_puzzle(data, for_publish=False)
        if not ok:
            print(f"SKIP {path.name}: {errors}")
            continue
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{path.stem}: {clues}")
        updated += 1
    print(f"\nUpdated {updated} refsoup puzzle(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
