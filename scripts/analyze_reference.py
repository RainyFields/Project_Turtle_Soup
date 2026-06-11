#!/usr/bin/env python3
"""Layer B: aggregate reference features and writing patterns."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.analysis.features import aggregate_features
from generator.analysis.patterns import high_rating_patterns
from generator.reference.storage import load_all_samples


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="generator/config.yaml")
    p.add_argument("--output", default="")
    p.add_argument(
        "--min-rating",
        type=float,
        default=None,
        help="Min rating for high-rated difficulty calibration (default from config)",
    )
    args = p.parse_args()

    root = ROOT
    cfg = yaml.safe_load((root / args.config).read_text(encoding="utf-8"))
    paths = cfg.get("paths", {})
    parsed_dir = root / paths.get("reference_parsed", "data/reference/parsed")
    out_dir = Path(args.output) if args.output else root / paths.get(
        "analysis_output", "data/generator/analysis"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    analysis_cfg = cfg.get("analysis", {})
    min_rating = (
        args.min_rating
        if args.min_rating is not None
        else float(analysis_cfg.get("min_rating_for_calibration", 8.0))
    )

    samples = load_all_samples(parsed_dir)
    stats = aggregate_features(samples, min_rating=min_rating)
    patterns = high_rating_patterns(samples, min_rating=min_rating)

    (out_dir / "aggregate.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "patterns.json").write_text(
        json.dumps(patterns, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    cal = stats.get("difficulty_calibration") or {}
    w = cal.get("difficulty_weights") or {}
    print(
        f"wrote {out_dir}/aggregate.json, patterns.json (n={len(samples)}, "
        f"high-rated>={min_rating}: {cal.get('high_rated_count', 0)}, "
        f"difficulty weights easy={w.get('easy', 0):.2f} medium={w.get('medium', 0):.2f} hard={w.get('hard', 0):.2f})"
    )


if __name__ == "__main__":
    main()
