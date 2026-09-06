from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from generator.reference.to_puzzle import is_importable_sample, reference_sample_to_puzzle
from generator.schema import puzzle_dict_to_json_ready, validate_puzzle

REFERENCE_PREFIX = "refsoup_"


# Reference-site imports are externally verifiable, so they belong in the
# real/ provenance folder (see data/puzzles/README.md).
REAL_SUBDIR = "real"


def _real_dir(puzzles_dir: Path) -> Path:
    d = puzzles_dir / REAL_SUBDIR
    return d if d.exists() or not puzzles_dir.exists() else d


def _existing_reference_files(puzzles_dir: Path):
    """refsoup_*.json in both the flat dir and real/, so ids never collide."""
    return list(puzzles_dir.glob(f"{REFERENCE_PREFIX}*.json")) + list(
        (puzzles_dir / REAL_SUBDIR).glob(f"{REFERENCE_PREFIX}*.json")
    )


def next_reference_puzzle_id(puzzles_dir: Path, prefix: str = REFERENCE_PREFIX) -> str:
    nums: List[int] = []
    for p in _existing_reference_files(puzzles_dir):
        m = re.match(rf"{re.escape(prefix)}(\d+)$", p.stem)
        if m:
            nums.append(int(m.group(1)))
    n = max(nums, default=0) + 1
    return f"{prefix}{n:03d}"


def _load_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"imported": []}
    return json.loads(path.read_text(encoding="utf-8"))


def load_import_manifest(path: Path) -> Dict[str, Any]:
    return _load_manifest(path)


def imported_external_ids(manifest: Dict[str, Any], puzzles_dir: Path) -> set[str]:
    return _imported_external_ids(manifest, puzzles_dir)


def _save_manifest(path: Path, manifest: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def _imported_external_ids(manifest: Dict[str, Any], puzzles_dir: Path) -> set[str]:
    ids = {str(x.get("external_id")) for x in manifest.get("imported", []) if x.get("external_id")}
    for p in _existing_reference_files(puzzles_dir):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            ext = (data.get("metadata") or {}).get("external_id")
            if ext:
                ids.add(str(ext))
        except (json.JSONDecodeError, OSError):
            continue
    return ids


def publish_reference_sample(
    sample: Dict[str, Any],
    *,
    puzzles_dir: Path,
    manifest_path: Optional[Path] = None,
) -> Tuple[Path, str]:
    if not is_importable_sample(sample):
        raise ValueError("sample not importable (needs surface + solution)")

    puzzle = reference_sample_to_puzzle(sample)
    ok, errors = validate_puzzle(puzzle, for_publish=False)
    if not ok:
        raise ValueError("reference puzzle invalid: " + "; ".join(errors))

    pid = next_reference_puzzle_id(puzzles_dir)
    out = puzzle_dict_to_json_ready(puzzle)
    out["id"] = pid

    ok, errors = validate_puzzle(out, for_publish=True)
    if not ok:
        raise ValueError("reference publish validation failed: " + "; ".join(errors))

    target_dir = puzzles_dir / REAL_SUBDIR
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{pid}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    if manifest_path:
        manifest = _load_manifest(manifest_path)
        imported = list(manifest.get("imported", []))
        imported.append(
            {
                "refsoup_id": pid,
                "external_id": sample.get("external_id"),
                "title": sample.get("title"),
                "reference_url": sample.get("url"),
                "path": str(path),
            }
        )
        manifest["imported"] = imported
        _save_manifest(manifest_path, manifest)

    return path, pid


def clear_reference_puzzles(puzzles_dir: Path, *, manifest_path: Optional[Path] = None) -> int:
    """Remove all refsoup_*.json from puzzles_dir; optionally reset manifest."""
    removed = 0
    for p in list(_existing_reference_files(puzzles_dir)):
        p.unlink()
        removed += 1
    if manifest_path is not None:
        _save_manifest(manifest_path, {"imported": []})
    return removed


def select_samples_for_import(
    samples: List[Dict[str, Any]],
    *,
    limit: int = 10,
    min_rating: Optional[float] = None,
    skip_external_ids: Optional[set[str]] = None,
    require_classic: bool = False,
    max_surface_chars: Optional[int] = None,
    max_solution_chars: Optional[int] = None,
) -> List[Dict[str, Any]]:
    skip = skip_external_ids or set()
    rows: List[Dict[str, Any]] = []
    for s in samples:
        if not is_importable_sample(s):
            continue
        ext = str(s.get("external_id") or "")
        if ext and ext in skip:
            continue
        tags = list(s.get("tags") or [])
        if require_classic and "经典" not in tags:
            continue
        surface = (s.get("surface") or "").strip()
        solution = (s.get("solution") or "").strip()
        if max_surface_chars is not None and len(surface) > max_surface_chars:
            continue
        if max_solution_chars is not None and len(solution) > max_solution_chars:
            continue
        rating = s.get("rating")
        if min_rating is not None:
            if rating is None or float(rating) < min_rating:
                continue
        rows.append(s)

    rows.sort(
        key=lambda x: (
            len((x.get("surface") or "").strip()),
            len((x.get("solution") or "").strip()),
            -float(x.get("rating") or 0),
        )
    )
    # limit <= 0 means "no cap", matching crawl_reference.py's --limit
    return rows if limit is None or limit <= 0 else rows[:limit]
