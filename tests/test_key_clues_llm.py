from generator.reference.key_clues_llm import (
    _parse_clues,
    extract_key_clues_llm,
    validate_clues,
)

SURFACE = "沙漠里躺着一具男尸，手里紧紧攥着半根火柴。"
SOLUTION = "一行人乘热气球穿越沙漠，超重后抽签，抽中半根短火柴的人被扔下去减重，坠落而死。"


class _Rater:
    def __init__(self, reply):
        self.reply = reply

    def complete(self, *, system, user):
        return self.reply


def test_parses_bare_json():
    assert _parse_clues('{"clues": ["热气球", "抽签"]}') == ["热气球", "抽签"]


def test_parses_json_wrapped_in_prose():
    assert _parse_clues('好的：\n{"clues": ["热气球"]}\n以上。') == ["热气球"]


def test_unparseable_reply_yields_nothing():
    assert _parse_clues("抱歉，我无法完成") == []


def test_surface_words_are_rejected_as_free_points():
    # long enough to pass the length gate, so the surface check is what rejects it
    kept, rejected = validate_clues(["紧紧攥着半根火柴", "抽签减重被扔下"], SURFACE, SOLUTION)
    assert kept == ["抽签减重被扔下"]
    assert any("火柴" in r and "汤面" in r for r in rejected)


def test_clues_too_short_for_the_paraphrase_fallback_are_rejected():
    """An N-character clue has N-1 bigrams and the judge's fallback needs 4, so
    anything under 5 characters can only ever match by exact substring."""
    kept, rejected = validate_clues(["抽签", "热气球", "抽签减重被扔下"], SURFACE, SOLUTION)
    assert kept == ["抽签减重被扔下"]
    assert sum("只能逐字匹配" in r for r in rejected) == 2


def test_invented_content_is_rejected():
    kept, rejected = validate_clues(["外星人绑架"], SURFACE, SOLUTION)
    assert kept == []
    assert any("臆造" in r for r in rejected)


def test_condensed_wording_from_the_solution_is_kept():
    # not a verbatim substring, but built from the solution's own vocabulary
    kept, _ = validate_clues(["抽签减重被扔下"], SURFACE, SOLUTION)
    assert kept == ["抽签减重被扔下"]


def test_duplicates_and_length_bounds():
    kept, rejected = validate_clues(
        ["抽签减重被扔下", "抽签减重被扔下", "人", "一行人乘热气球穿越沙漠超重抽签"],
        SURFACE, SOLUTION,
    )
    assert kept == ["抽签减重被扔下"]
    assert len(rejected) == 3


def test_end_to_end_keeps_only_valid_clues():
    out = extract_key_clues_llm(
        SURFACE,
        SOLUTION,
        rater=_Rater('{"clues": ["乘热气球穿越沙漠", "抽签减重被扔下", "火柴", "抽签"]}'),
    )
    assert out["clues"] == ["乘热气球穿越沙漠", "抽签减重被扔下"]
    assert len(out["rejected"]) == 2  # 火柴 is in the surface; 抽签 is too short
