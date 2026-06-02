#!/usr/bin/env python3
"""Layer D: filter staging candidates; write filter_report.json per file."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.filter.pipeline import run_filters
from generator.reference.storage import load_all_samples


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", required=True)
    p.add_argument("--config", default="generator/config.yaml")
    args = p.parse_args()

    root = ROOT
    cfg = yaml.safe_load((root / args.config).read_text(encoding="utf-8"))
    paths = cfg.get("paths", {})
    filt = cfg.get("filter", {})
    staging = root / paths.get("staging_dir", "data/generator/staging") / args.batch

    parsed_dir = root / paths.get("reference_parsed", "data/reference/parsed")
    ref_surfaces = [s.get("surface", "") for s in load_all_samples(parsed_dir) if s.get("surface")]

    for path in sorted(staging.glob("turtle_candidate_*.json")):
        puzzle = json.loads(path.read_text(encoding="utf-8"))
        result = run_filters(
            puzzle,
            reference_surfaces=ref_surfaces or None,
            similarity_threshold=float(filt.get("similarity_threshold", 0.85)),
        )
        report = {
            "candidate": path.name,
            "passed": result.passed,
            "errors": result.errors,
            "similarity_score": result.similarity_score,
        }
        report_path = path.with_suffix(".filter.json")
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {path.name}: {result.errors or 'ok'}")


if __name__ == "__main__":
    main()
