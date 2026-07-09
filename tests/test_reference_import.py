import json
from pathlib import Path

from generator.reference.import_publish import (
    clear_reference_puzzles,
    publish_reference_sample,
    select_samples_for_import,
)
from generator.reference.to_puzzle import is_importable_sample, reference_sample_to_puzzle
from generator.schema import validate_puzzle


def test_reference_sample_to_puzzle():
    sample = {
        "external_id": "99",
        "title": "测试参考汤",
        "surface": "汤面内容。",
        "solution": "真相是第一句。真相是第二句。",
        "tags": ["经典", "清汤"],
        "rating": 9.0,
        "url": "https://soup.ahelumos.com/soups/99",
        "source_site": "ahelumos",
    }
    puzzle = reference_sample_to_puzzle(sample, puzzle_id="refsoup_001")
    ok, errors = validate_puzzle(puzzle, for_publish=True)
    assert ok, errors
    assert puzzle["id"] == "refsoup_001"
    assert puzzle["metadata"]["source"] == "reference"
    assert puzzle["difficulty"] == "hard"
    assert len(puzzle["key_clues"]) >= 1


def test_publish_reference_sample(tmp_path: Path):
    sample = {
        "external_id": "42",
        "title": "导入测试",
        "surface": "一个人走进房间。",
        "solution": "他其实从未离开。结局令人意外。",
        "tags": ["搞笑"],
        "rating": 7.5,
    }
    puzzles_dir = tmp_path / "puzzles"
    manifest = tmp_path / "manifest.json"
    path, pid = publish_reference_sample(
        sample, puzzles_dir=puzzles_dir, manifest_path=manifest
    )
    assert pid == "refsoup_001"
    assert path.name == "refsoup_001.json"
    assert manifest.exists()


def test_select_samples_skips_without_solution():
    rows = select_samples_for_import(
        [
            {"external_id": "1", "surface": "a", "solution": ""},
            {"external_id": "2", "surface": "b", "solution": "汤底", "rating": 9},
        ],
        limit=5,
    )
    assert len(rows) == 1
    assert rows[0]["external_id"] == "2"
    assert is_importable_sample(rows[0])


def test_select_samples_prefers_short_classic():
    rows = select_samples_for_import(
        [
            {
                "external_id": "1",
                "surface": "短汤面。",
                "solution": "短汤底。",
                "tags": ["经典"],
                "rating": 2,
            },
            {
                "external_id": "2",
                "surface": "x" * 100,
                "solution": "汤底",
                "tags": ["经典"],
                "rating": 10,
            },
        ],
        limit=5,
        require_classic=True,
        max_surface_chars=20,
    )
    assert [r["external_id"] for r in rows] == ["1"]


def test_clear_reference_puzzles(tmp_path: Path):
    puzzles = tmp_path / "puzzles"
    puzzles.mkdir()
    (puzzles / "refsoup_001.json").write_text("{}", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"imported":[{"external_id":"1"}]}', encoding="utf-8")
    n = clear_reference_puzzles(puzzles, manifest_path=manifest)
    assert n == 1
    assert not list(puzzles.glob("refsoup_*.json"))
    assert json.loads(manifest.read_text())["imported"] == []
