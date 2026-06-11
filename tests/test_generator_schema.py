import json
from pathlib import Path

from generator.schema import validate_puzzle

_ROOT = Path(__file__).resolve().parents[1]


def test_existing_puzzle_validates():
    puzzle = json.loads((_ROOT / "data/puzzles/turtle_001.json").read_text(encoding="utf-8"))
    ok, errors = validate_puzzle(puzzle)
    assert ok, errors


def test_publish_requires_generated_source():
    puzzle = json.loads((_ROOT / "data/puzzles/turtle_001.json").read_text(encoding="utf-8"))
    ok, errors = validate_puzzle(puzzle, for_publish=True)
    assert not ok
    assert any("generated" in e for e in errors)
