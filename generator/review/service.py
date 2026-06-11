from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from generator.review.publish import publish_candidate
from generator.review.queue import ReviewStatus, load_queue, save_queue
from generator.schema import puzzle_dict_to_json_ready, validate_puzzle


def load_generator_config(root: Path, config_path: str = "generator/config.yaml") -> Dict[str, Any]:
    return yaml.safe_load((root / config_path).read_text(encoding="utf-8"))


def _staging_root(cfg: Dict[str, Any], root: Path) -> Path:
    return root / cfg.get("paths", {}).get("staging_dir", "data/generator/staging")


def _review_queue_path(cfg: Dict[str, Any], root: Path) -> Path:
    return root / cfg.get("paths", {}).get("review_dir", "data/generator/review") / "queue.json"


def _queue_key(batch: str, filename: str) -> str:
    return f"{batch}/{filename}"


def list_batches(root: Path, cfg: Dict[str, Any]) -> List[str]:
    staging = _staging_root(cfg, root)
    if not staging.exists():
        return []
    return sorted(
        d.name
        for d in staging.iterdir()
        if d.is_dir() and any(d.glob("turtle_candidate_*.json"))
    )


def _get_review_entry(queue: List[Dict[str, Any]], batch: str, filename: str) -> Dict[str, Any]:
    key = _queue_key(batch, filename)
    for item in queue:
        if item.get("key") == key:
            return item
    return {"key": key, "batch": batch, "file": filename, "status": ReviewStatus.PENDING.value, "notes": ""}


def list_candidates(root: Path, cfg: Dict[str, Any], *, batch: Optional[str] = None) -> List[Dict[str, Any]]:
    staging = _staging_root(cfg, root)
    queue = load_queue(_review_queue_path(cfg, root))
    batches = [batch] if batch else list_batches(root, cfg)
    rows: List[Dict[str, Any]] = []

    for b in batches:
        batch_dir = staging / b
        if not batch_dir.is_dir():
            continue
        for path in sorted(batch_dir.glob("turtle_candidate_*.json")):
            puzzle = json.loads(path.read_text(encoding="utf-8"))
            review = _get_review_entry(queue, b, path.name)
            ok, schema_errors = validate_puzzle(puzzle, for_publish=False)
            rows.append(
                {
                    "batch": b,
                    "filename": path.name,
                    "key": _queue_key(b, path.name),
                    "title": puzzle.get("title", ""),
                    "difficulty": puzzle.get("difficulty", ""),
                    "category": puzzle.get("category", ""),
                    "surface_preview": (puzzle.get("surface") or "")[:72],
                    "review_status": review.get("status", ReviewStatus.PENDING.value),
                    "review_notes": review.get("notes", ""),
                    "published_id": review.get("published_id"),
                    "published_path": review.get("published_path"),
                    "schema_ok": ok,
                    "schema_errors": schema_errors,
                }
            )
    return rows


def get_candidate(root: Path, cfg: Dict[str, Any], batch: str, filename: str) -> Dict[str, Any]:
    path = _staging_root(cfg, root) / batch / filename
    if not path.exists():
        raise FileNotFoundError(path)
    puzzle = json.loads(path.read_text(encoding="utf-8"))
    queue = load_queue(_review_queue_path(cfg, root))
    review = _get_review_entry(queue, batch, filename)
    ok, schema_errors = validate_puzzle(puzzle, for_publish=False)
    publish_ok, publish_errors = validate_puzzle(puzzle, for_publish=True)
    return {
        "batch": batch,
        "filename": filename,
        "puzzle": puzzle,
        "review": review,
        "schema_ok": ok,
        "schema_errors": schema_errors,
        "publish_ready": publish_ok,
        "publish_errors": publish_errors,
    }


def save_candidate(
    root: Path, cfg: Dict[str, Any], batch: str, filename: str, puzzle: Dict[str, Any]
) -> Dict[str, Any]:
    path = _staging_root(cfg, root) / batch / filename
    if not path.exists():
        raise FileNotFoundError(path)
    data = puzzle_dict_to_json_ready(puzzle)
    ok, errors = validate_puzzle(data, for_publish=False)
    if not ok:
        raise ValueError("; ".join(errors))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return get_candidate(root, cfg, batch, filename)


def set_review_status(
    root: Path,
    cfg: Dict[str, Any],
    batch: str,
    filename: str,
    status: str,
    notes: str = "",
) -> Dict[str, Any]:
    queue_path = _review_queue_path(cfg, root)
    queue = load_queue(queue_path)
    key = _queue_key(batch, filename)
    found = False
    for item in queue:
        if item.get("key") == key:
            item["status"] = status
            item["notes"] = notes
            item["batch"] = batch
            item["file"] = filename
            found = True
            break
    if not found:
        queue.append(
            {
                "key": key,
                "batch": batch,
                "file": filename,
                "status": status,
                "notes": notes,
            }
        )
    save_queue(queue_path, queue)
    return _get_review_entry(queue, batch, filename)


def _candidate_targets(
    root: Path,
    cfg: Dict[str, Any],
    *,
    items: Optional[List[Dict[str, str]]] = None,
    batch: Optional[str] = None,
) -> List[Tuple[str, str]]:
    if items:
        return [(i["batch"], i["filename"]) for i in items if i.get("batch") and i.get("filename")]
    if batch:
        return [
            (r["batch"], r["filename"])
            for r in list_candidates(root, cfg, batch=batch)
        ]
    return []


def publish_staging_batch(
    root: Path,
    cfg: Dict[str, Any],
    *,
    items: Optional[List[Dict[str, str]]] = None,
    batch: Optional[str] = None,
    only_accepted: bool = True,
    skip_published: bool = True,
) -> Dict[str, Any]:
    queue = load_queue(_review_queue_path(cfg, root))
    targets = _candidate_targets(root, cfg, items=items, batch=batch)
    published: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    failed: List[Dict[str, Any]] = []

    for b, filename in targets:
        review = _get_review_entry(queue, b, filename)
        if skip_published and review.get("published_id"):
            skipped.append({"batch": b, "filename": filename, "reason": "already_published"})
            continue
        if only_accepted and review.get("status") != ReviewStatus.ACCEPTED.value:
            skipped.append({"batch": b, "filename": filename, "reason": "not_accepted"})
            continue
        try:
            out_path, puzzle_id = publish_staging_candidate(root, cfg, b, filename)
            published.append(
                {
                    "batch": b,
                    "filename": filename,
                    "published_id": puzzle_id,
                    "published_path": str(out_path.relative_to(root)),
                }
            )
            queue = load_queue(_review_queue_path(cfg, root))
        except (FileNotFoundError, ValueError) as e:
            failed.append({"batch": b, "filename": filename, "error": str(e)})

    return {"published": published, "skipped": skipped, "failed": failed}


def publish_staging_candidate(
    root: Path, cfg: Dict[str, Any], batch: str, filename: str
) -> Tuple[Path, str]:
    path = _staging_root(cfg, root) / batch / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    pub = cfg.get("publish", {})
    puzzles_dir = root / pub.get("puzzles_dir", "data/puzzles")
    out_path = publish_candidate(data, puzzles_dir=puzzles_dir, batch_id=batch)
    puzzle_id = json.loads(out_path.read_text(encoding="utf-8"))["id"]

    queue_path = _review_queue_path(cfg, root)
    queue = load_queue(queue_path)
    key = _queue_key(batch, filename)
    entry = None
    for item in queue:
        if item.get("key") == key:
            item["status"] = ReviewStatus.ACCEPTED.value
            item["published_id"] = puzzle_id
            item["published_path"] = str(out_path.relative_to(root))
            entry = item
            break
    if entry is None:
        entry = {
            "key": key,
            "batch": batch,
            "file": filename,
            "status": ReviewStatus.ACCEPTED.value,
            "notes": "",
            "published_id": puzzle_id,
            "published_path": str(out_path.relative_to(root)),
        }
        queue.append(entry)
    save_queue(queue_path, queue)
    return out_path, puzzle_id
