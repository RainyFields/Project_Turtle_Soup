from __future__ import annotations

import html as html_lib
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urljoin

SITE_BASE = "https://soup.ahelumos.com"
SITE_NAME = "ahelumos"

_LIST_CARD_ANCHOR = re.compile(
    r'<a href="/soups/(\d+)" class="cursor-pointer group block">(.*?)</a>',
    re.DOTALL,
)
_TAG_RE = re.compile(
    r'<span class="inline-flex rounded-full border border-neutral-200 bg-neutral-50 px-2 py-0\.5 font-mono text-\[[^\]]+\] text-neutral-500">([^<]+)</span>'
)


def build_index_url(
    *,
    page: Optional[int] = None,
    sort: str = "",
    tags: Optional[List[str]] = None,
    q: str = "",
) -> str:
    params: Dict[str, str] = {}
    if page is not None and page > 1:
        params["page"] = str(page)
    if sort:
        params["sort"] = sort
    if tags:
        params["tags"] = ",".join(tags)
    if q:
        params["q"] = q
    if not params:
        return f"{SITE_BASE}/"
    return f"{SITE_BASE}/?{urlencode(params)}"


def build_soup_url(soup_id: str | int) -> str:
    return urljoin(SITE_BASE, f"/soups/{soup_id}")


def _clean_text(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_rating(raw: str) -> Optional[float]:
    raw = raw.strip()
    if not raw or "暂无" in raw:
        return None
    m = re.search(r"([\d.]+)", raw)
    if not m:
        return None
    val = float(m.group(1))
    return val if 0.0 <= val <= 10.0 else None


def parse_index_cards(html: str) -> List[Dict[str, Any]]:
    """Parse listing cards from the home/search page (stubs without full solution)."""
    records: List[Dict[str, Any]] = []
    seen: set[str] = set()

    for soup_id, block in _LIST_CARD_ANCHOR.findall(html):
        if soup_id in seen:
            continue
        seen.add(soup_id)

        title_m = re.search(r"<h3[^>]*>(.*?)</h3>", block, re.DOTALL)
        rating_m = re.search(
            r"shrink-0 inline-flex items-center gap-1[^>]*>.*?<span>([^<]+)</span>\s*</span>",
            block,
            re.DOTALL,
        )
        surface_m = re.search(
            r'class="text-neutral-600 line-clamp-2[^"]*"[^>]*>\s*(.*?)\s*</p>',
            block,
            re.DOTALL,
        )
        author_m = re.search(r"<span>作者[：:]\s*([^<]+)</span>", block)
        likes_m = re.search(
            r'inline-flex items-center gap-1">\s*<svg[\s\S]*?</svg>\s*<span>(\d+)</span>',
            block,
        )

        tags = _TAG_RE.findall(block)
        records.append(
            {
                "external_id": soup_id,
                "title": _clean_text(title_m.group(1)) if title_m else "",
                "surface_preview": _clean_text(surface_m.group(1)) if surface_m else "",
                "solution": "",
                "rating": _parse_rating(rating_m.group(1)) if rating_m else None,
                "tags": tags,
                "category": tags[0] if tags else "",
                "author": _clean_text(author_m.group(1)) if author_m else "",
                "like_count": int(likes_m.group(1)) if likes_m else None,
                "url": build_soup_url(soup_id),
                "source_site": SITE_NAME,
            }
        )
    return records


def parse_detail_page(html: str, *, soup_id: str = "", url: str = "") -> Dict[str, Any]:
    """Parse /soups/{id} page: full surface + solution (汤底 on card back)."""
    id_m = re.search(r'data-soup-id="(\d+)"', html)
    external_id = soup_id or (id_m.group(1) if id_m else "")

    title_m = re.search(
        r"<!-- 正面：汤面 -->.*?<h3[^>]*>(.*?)</h3>",
        html,
        re.DOTALL,
    )
    surface_m = re.search(
        r"<!-- 正面：汤面 -->.*?<p class=\"[^\"]*whitespace-pre-wrap[^\"]*\"[^>]*>(.*?)</p>",
        html,
        re.DOTALL,
    )
    solution_m = re.search(
        r"<!-- 背面：汤底 -->.*?<p class=\"[^\"]*whitespace-pre-wrap[^\"]*\"[^>]*>(.*?)</p>",
        html,
        re.DOTALL,
    )
    rating_m = re.search(
        r'id="ratingSummaryText"[^>]*>\s*([\d.]+)\s*分',
        html,
    )
    rating_count_m = re.search(r'id="ratingCountText"[^>]*>\s*(\d+)\s*人打分', html)
    author_m = re.search(
        r'class="soup-card-footer[^"]*"[^>]*>[\s\S]*?<span>By\s+([^<]+)</span>',
        html,
    )
    if not author_m:
        author_m = re.search(r"<span>By\s+([^<]+)</span>", html)

    tags = _TAG_RE.findall(html)
    surface = _clean_text(surface_m.group(1)) if surface_m else ""
    solution = _clean_text(solution_m.group(1)) if solution_m else ""

    return {
        "external_id": external_id,
        "title": _clean_text(title_m.group(1)) if title_m else "",
        "surface": surface,
        "solution": solution,
        "rating": float(rating_m.group(1)) if rating_m else None,
        "rating_count": int(rating_count_m.group(1)) if rating_count_m else None,
        "tags": tags,
        "category": tags[0] if tags else "",
        "author": _clean_text(author_m.group(1)) if author_m else "",
        "url": url or build_soup_url(external_id),
        "source_site": SITE_NAME,
    }


def merge_stub_and_detail(stub: Dict[str, Any], detail: Dict[str, Any]) -> Dict[str, Any]:
    out = {**stub, **detail}
    out["like_count"] = stub.get("like_count")
    if not out.get("rating") and stub.get("rating") is not None:
        out["rating"] = stub["rating"]
    return out
