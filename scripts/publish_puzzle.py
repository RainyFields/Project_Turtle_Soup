#!/usr/bin/env python3
"""Layer E: publish human-approved candidate to data/puzzles/."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.review.publish import publish_candidate


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", required=True, help="Path to approved JSON")
    p.add_argument("--batch", default="")
    p.add_argument("--config", default="generator/config.yaml")
    args = p.parse_args()

    root = ROOT
    cfg = yaml.safe_load((root / args.config).read_text(encoding="utf-8"))
    pub = cfg.get("publish", {})
    puzzles_dir = root / pub.get("puzzles_dir", "data/puzzles")

    candidate_path = Path(args.candidate)
    if not candidate_path.is_absolute():
        candidate_path = root / candidate_path
    data = json.loads(candidate_path.read_text(encoding="utf-8"))
    out = publish_candidate(data, puzzles_dir=puzzles_dir, batch_id=args.batch)
    print(f"published → {out}")


if __name__ == "__main__":
    main()
