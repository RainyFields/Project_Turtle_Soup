from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import urlparse

from . import ahelumos


def _is_ahelumos(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return "ahelumos.com" in host or host == ""


def parse_html_page(html: str, *, url: str = "") -> List[Dict[str, Any]]:
    """
    Parse one HTML page into reference soup records.

    - Index/home: multiple card stubs
    - /soups/{id}: single full record (surface + solution)
    """
    if "/soups/" in url:
        return [parse_detail_page(html, url=url)]
    if _is_ahelumos(url) or 'href="/soups/' in html:
        return parse_index_page(html, url=url)
    return []


def parse_index_page(html: str, *, url: str = "") -> List[Dict[str, Any]]:
    return ahelumos.parse_index_cards(html)


def parse_detail_page(html: str, *, soup_id: str = "", url: str = "") -> Dict[str, Any]:
    if soup_id == "" and "/soups/" in url:
        soup_id = url.rstrip("/").split("/")[-1]
    return ahelumos.parse_detail_page(html, soup_id=soup_id, url=url)


def to_raw_sample(record: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize parser output for JSONL storage (reference layer only)."""
    return {
        "external_id": str(record.get("external_id", "")),
        "title": record.get("title", ""),
        "surface": record.get("surface") or record.get("surface_preview", ""),
        "solution": record.get("solution", ""),
        "rating": record.get("rating"),
        "rating_count": record.get("rating_count"),
        "like_count": record.get("like_count"),
        "tags": list(record.get("tags") or []),
        "category": record.get("category", ""),
        "author": record.get("author", ""),
        "url": record.get("url", ""),
        "source_site": record.get("source_site", ahelumos.SITE_NAME),
        "crawled_for": "local_reference_only",
    }
