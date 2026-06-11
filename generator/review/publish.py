from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

from generator.schema import puzzle_dict_to_json_ready, validate_puzzle


def next_puzzle_id(puzzles_dir: Path, prefix: str = "turtle_") -> str:
    nums = []
    for p in puzzles_dir.glob(f"{prefix}*.json"):
        m = re.match(rf"{re.escape(prefix)}(\d+)$", p.stem)
        if m:
            nums.append(int(m.group(1)))
    n = max(nums, default=0) + 1
    return f"{prefix}{n:03d}"


def publish_candidate(
    candidate: Dict[str, Any],
    *,
    puzzles_dir: Path,
    batch_id: str = "",
) -> Path:
    ok, errors = validate_puzzle(candidate, for_publish=False)
    if not ok:
        raise ValueError("candidate invalid: " + "; ".join(errors))

    pid = next_puzzle_id(puzzles_dir)
    out = puzzle_dict_to_json_ready(dict(candidate))
    out["id"] = pid
    meta = dict(out.get("metadata") or {})
    meta["source"] = "generated"
    if batch_id:
        meta["generator_batch"] = batch_id
    out["metadata"] = meta

    ok, errors = validate_puzzle(out, for_publish=True)
    if not ok:
        raise ValueError("publish validation failed: " + "; ".join(errors))

    path = puzzles_dir / f"{pid}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return path
