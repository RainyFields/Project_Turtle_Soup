from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List


def append_jsonl(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def iter_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_all_samples(parsed_dir: Path) -> List[Dict[str, Any]]:
    samples: List[Dict[str, Any]] = []
    for p in sorted(parsed_dir.glob("*.jsonl")):
        samples.extend(iter_jsonl(p))
    return samples
