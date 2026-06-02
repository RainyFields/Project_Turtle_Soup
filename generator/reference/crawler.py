from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import requests

from . import ahelumos
from .parser import parse_detail_page, parse_index_page


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def crawl_pages(
    start_url: str,
    *,
    max_pages: int = 10,
    rate_limit_seconds: float = 2.0,
    user_agent: str = "turtle-soup-bench-research/0.1",
) -> Iterator[Dict[str, Any]]:
    """
    Yield raw page records {url, html, fetched_at, status}.
    For ahelumos, start_url is typically https://soup.ahelumos.com/ (optional ?page=).
    """
    session = requests.Session()
    session.headers["User-Agent"] = user_agent
    url: Optional[str] = start_url
    count = 0
    while url and count < max_pages:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        yield {
            "url": url,
            "html": resp.text,
            "status": resp.status_code,
            "fetched_at": _utc_now(),
        }
        count += 1
        url = None


def crawl_ahelumos(
    *,
    max_index_pages: int = 1,
    fetch_details: bool = True,
    sort: str = "",
    rate_limit_seconds: float = 2.0,
    user_agent: str = "turtle-soup-bench-research/0.1",
) -> Iterator[Dict[str, Any]]:
    """
    Crawl https://soup.ahelumos.com/ listing + optional per-soup detail pages.
    Yields normalized reference records ready for JSONL (via to_raw_sample).
    """
    session = requests.Session()
    session.headers["User-Agent"] = user_agent
    session.headers["Accept-Language"] = "zh-CN,zh;q=0.9"

    all_stubs: List[Dict[str, Any]] = []
    for page in range(1, max_index_pages + 1):
        index_url = ahelumos.build_index_url(page=page, sort=sort)
        resp = session.get(index_url, timeout=30)
        resp.raise_for_status()
        stubs = parse_index_page(resp.text, url=index_url)
        if not stubs:
            break
        all_stubs.extend(stubs)
        time.sleep(rate_limit_seconds)

    seen: set[str] = set()
    unique_stubs: List[Dict[str, Any]] = []
    for stub in all_stubs:
        sid = stub.get("external_id", "")
        if sid and sid not in seen:
            seen.add(sid)
            unique_stubs.append(stub)

    for stub in unique_stubs:
        record = dict(stub)
        if fetch_details:
            detail_url = ahelumos.build_soup_url(stub["external_id"])
            resp = session.get(detail_url, timeout=30)
            resp.raise_for_status()
            detail = parse_detail_page(
                resp.text, soup_id=stub["external_id"], url=detail_url
            )
            record = ahelumos.merge_stub_and_detail(stub, detail)
            time.sleep(rate_limit_seconds)
        yield record


def save_raw_page(record: Dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = str(abs(hash(record["url"])))
    path = out_dir / f"page_{slug}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return path
