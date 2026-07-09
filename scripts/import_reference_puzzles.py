#!/usr/bin/env python3
"""Import reference-site soups into data/puzzles/ as refsoup_NNN (separate from turtle_NNN)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.reference.import_publish import (
    clear_reference_puzzles,
    imported_external_ids,
    load_import_manifest,
    publish_reference_sample,
    select_samples_for_import,
)
from generator.reference.storage import load_all_samples


def main() -> int:
    p = argparse.ArgumentParser(description="Import ahelumos reference soups → refsoup_NNN")
    p.add_argument("--config", default="generator/config.yaml")
    p.add_argument("--limit", type=int, default=10, help="Max puzzles to import this run")
    p.add_argument("--min-rating", type=float, default=None, help="Only import rated soups ≥ this")
    p.add_argument("--require-classic", action="store_true", help="Only soups tagged 经典")
    p.add_argument("--max-surface-chars", type=int, default=None, help="Max 汤面 character length")
    p.add_argument("--max-solution-chars", type=int, default=None, help="Max 汤底 character length")
    p.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing refsoup_*.json and reset manifest before import",
    )
    p.add_argument("--dry-run", action="store_true", help="Preview selection without writing")
    args = p.parse_args()

    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    paths = cfg.get("paths", {})
    parsed_dir = ROOT / paths.get("reference_parsed", "data/reference/parsed")
    puzzles_dir = ROOT / cfg.get("publish", {}).get("puzzles_dir", "data/puzzles")
    manifest_path = ROOT / paths.get("reference_import_dir", "data/generator/reference_import") / "manifest.json"

    samples = load_all_samples(parsed_dir)
    if not samples:
        print(f"No reference samples in {parsed_dir}. Run: python scripts/crawl_reference.py")
        return 1

    manifest = load_import_manifest(manifest_path)
    skip = imported_external_ids(manifest, puzzles_dir) if not args.replace else set()

    if args.replace and not args.dry_run:
        n = clear_reference_puzzles(puzzles_dir, manifest_path=manifest_path)
        print(f"Removed {n} existing refsoup_* puzzle(s); manifest reset.")
        skip = set()

    picked = select_samples_for_import(
        samples,
        limit=args.limit,
        min_rating=args.min_rating,
        skip_external_ids=skip,
        require_classic=args.require_classic,
        max_surface_chars=args.max_surface_chars,
        max_solution_chars=args.max_solution_chars,
    )

    if not picked:
        print("No importable samples matched filters (or all already imported).")
        return 0

    print(f"Selected {len(picked)} reference soup(s):")
    for s in picked:
        surf = len((s.get("surface") or ""))
        print(
            f"  - [{s.get('external_id')}] surf={surf} rating={s.get('rating')} "
            f"tags={','.join(s.get('tags') or [])} "
            f"{(s.get('title') or '')[:36]}"
        )

    if args.dry_run:
        print("Dry run — no files written.")
        return 0

    published = []
    for s in picked:
        out_path, pid = publish_reference_sample(
            s, puzzles_dir=puzzles_dir, manifest_path=manifest_path
        )
        published.append(pid)
        print(f"published {pid} ← external_id={s.get('external_id')} → {out_path}")

    print(f"\nDone. Imported {len(published)} puzzle(s) as refsoup_* in {puzzles_dir}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
