#!/usr/bin/env python3
"""Layer A: crawl reference site into data/reference/ (local only, never published)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.reference import ahelumos
from generator.reference.crawler import crawl_ahelumos, crawl_pages, save_raw_page
from generator.reference.parser import parse_html_page, to_raw_sample
from generator.reference.storage import append_jsonl


def main() -> None:
    p = argparse.ArgumentParser(description="Crawl reference soups (not published)")
    p.add_argument("--config", default="generator/config.yaml")
    p.add_argument("--start-url", default="", help="Override index URL")
    p.add_argument("--max-pages", type=int, default=1, help="Index pages (?page=N)")
    p.add_argument(
        "--sort",
        default="",
        help="Index sort, e.g. rating_desc (see site home.js)",
    )
    p.add_argument(
        "--no-details",
        action="store_true",
        help="Skip /soups/{id} detail fetch (no full solution)",
    )
    p.add_argument(
        "--legacy-raw",
        action="store_true",
        help="Also save raw HTML pages under data/reference/raw",
    )
    p.add_argument("--limit", type=int, default=0, help="Max soups (0 = all on index pages)")
    p.add_argument(
        "--fresh",
        action="store_true",
        help="Truncate parsed JSONL before crawl (avoid duplicates)",
    )
    args = p.parse_args()

    root = ROOT
    cfg = yaml.safe_load((root / args.config).read_text(encoding="utf-8"))
    ref = cfg.get("reference", {})
    paths = cfg.get("paths", {})
    rate = float(ref.get("rate_limit_seconds", 2.0))
    ua = str(ref.get("user_agent", "turtle-soup-bench-research/0.1"))

    raw_dir = root / paths.get("reference_raw", "data/reference/raw")
    parsed_path = root / paths.get("reference_parsed", "data/reference/parsed") / "samples.jsonl"
    parsed_path.parent.mkdir(parents=True, exist_ok=True)
    if args.fresh and parsed_path.exists():
        parsed_path.write_text("", encoding="utf-8")
        print(f"truncated {parsed_path}")

    base = (args.start_url or ref.get("base_url") or ahelumos.SITE_BASE).rstrip("/")
    if "ahelumos.com" not in base:
        raise SystemExit("Only soup.ahelumos.com is configured; set reference.base_url in config.")

    if args.legacy_raw:
        start = ahelumos.build_index_url(page=1, sort=args.sort) if not args.start_url else base
        for page in crawl_pages(start, max_pages=args.max_pages, rate_limit_seconds=rate, user_agent=ua):
            save_raw_page(page, raw_dir)
            records = [to_raw_sample(r) for r in parse_html_page(page["html"], url=page["url"])]
            if records:
                append_jsonl(parsed_path, records)

    count = 0
    for record in crawl_ahelumos(
        max_index_pages=args.max_pages,
        fetch_details=not args.no_details,
        sort=args.sort,
        rate_limit_seconds=rate,
        user_agent=ua,
    ):
        if args.limit and count >= args.limit:
            break
        append_jsonl(parsed_path, [to_raw_sample(record)])
        count += 1
        title = record.get("title", "")[:24]
        print(f"  {record.get('external_id')} | {title} | rating={record.get('rating')}")

    print(f"done: {count} soups → {parsed_path}")


if __name__ == "__main__":
    main()
