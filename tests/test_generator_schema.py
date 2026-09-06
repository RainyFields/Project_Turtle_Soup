import json


def _a_real_puzzle_id():
    """First puzzle of the verified set — avoids hardcoding ids that get renumbered."""
    from engine.game import list_puzzle_ids

    ids = list_puzzle_ids(family="real")
    assert ids, "no puzzles in data/puzzles/real/"
    return ids[0]

from engine.game import load_puzzle
from pathlib import Path

from generator.schema import validate_puzzle

_ROOT = Path(__file__).resolve().parents[1]


def test_existing_puzzle_validates():
    puzzle = load_puzzle(_a_real_puzzle_id())
    ok, errors = validate_puzzle(puzzle)
    assert ok, errors


def test_publish_rejects_an_unrecognised_source():
    puzzle = load_puzzle(_a_real_puzzle_id())
    puzzle["metadata"] = {**puzzle["metadata"], "source": "hand-written"}
    ok, errors = validate_puzzle(puzzle, for_publish=True)
    assert not ok
    assert any("source" in e for e in errors)


def test_publish_accepts_a_reference_import_under_its_own_prefix():
    puzzle = load_puzzle(_a_real_puzzle_id())
    ok, errors = validate_puzzle(puzzle, for_publish=True)
    assert ok, errors
