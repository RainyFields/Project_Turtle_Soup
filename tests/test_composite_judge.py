from evaluation.judge import (
    KEY_CLUE_POINTS,
    LOGIC_POINTS,
    CompositeScore,
    composite_judge,
)

SOLUTION = "一行人乘热气球穿越沙漠，超重后抽签，抽中短火柴的人被扔下去坠亡。"
CLUES = ["抽签", "热气球", "减重", "坠落", "故障"]


class _Rater:
    """Returns a scripted logic rating per call."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def complete(self, *, system, user):
        self.calls += 1
        return self.replies.pop(0) if self.replies else '{"logic": 0.0}'


def test_no_answer_scores_zero():
    r = composite_judge(solution=SOLUTION, final_answer=None, key_clues=CLUES)
    assert r.total == 0.0
    assert r.missed_clues == CLUES


def test_clue_only_scoring_is_capped_at_70():
    answer = "他们坐热气球，故障后为了减重抽签，抽中的人坠落而死"
    r = composite_judge(solution=SOLUTION, final_answer=answer, key_clues=CLUES)
    assert len(r.hit_clues) == 5
    assert r.key_clue_score == KEY_CLUE_POINTS
    assert r.logic_score == 0.0  # no rater supplied
    assert r.total == KEY_CLUE_POINTS


def test_partial_clues_score_proportionally():
    answer = "他坐热气球时坠落死亡"
    r = composite_judge(solution=SOLUTION, final_answer=answer, key_clues=CLUES)
    assert set(r.hit_clues) == {"热气球", "坠落"}
    assert r.key_clue_score == 2 / 5 * KEY_CLUE_POINTS


def test_logic_samples_are_averaged():
    rater = _Rater(['{"logic": 1.0}', '{"logic": 0.4}', '{"logic": 0.7}'])
    r = composite_judge(
        solution=SOLUTION,
        final_answer="他坐热气球时坠落死亡",
        key_clues=CLUES,
        logic_rater=rater,
        logic_samples=3,
    )
    assert rater.calls == 3
    assert r.logic_samples == [1.0, 0.4, 0.7]
    assert abs(r.logic_score - (2.1 / 3) * LOGIC_POINTS) < 1e-9


def test_full_marks_reach_100():
    rater = _Rater(['{"logic": 1.0}'] * 3)
    answer = "热气球故障超重，众人抽签减重，抽中短火柴者坠落身亡"
    r = composite_judge(
        solution=SOLUTION, final_answer=answer, key_clues=CLUES,
        logic_rater=rater, logic_samples=3,
    )
    assert abs(r.total - 100.0) < 1e-9


def test_unparseable_and_failing_ratings_are_skipped():
    class _Broken:
        calls = 0

        def complete(self, *, system, user):
            _Broken.calls += 1
            if _Broken.calls == 1:
                raise RuntimeError("upstream 500")
            return "sorry, no json here"

    r = composite_judge(
        solution=SOLUTION, final_answer="他坐热气球时坠落死亡", key_clues=CLUES,
        logic_rater=_Broken(), logic_samples=3,
    )
    assert r.logic_samples == []
    assert r.logic_score == 0.0
    assert r.key_clue_score > 0  # clue half is unaffected


def test_difficulty_band_follows_clue_count():
    def band(n):
        return composite_judge(
            solution="s", final_answer="x", key_clues=[f"线索{i}" for i in range(n)]
        ).difficulty_band

    assert band(2) == "easy"
    assert band(4) == "medium"
    assert band(6) == "hard"


def test_score_field_stays_normalised_for_existing_consumers():
    rater = _Rater(['{"logic": 1.0}'] * 3)
    answer = "热气球故障超重，众人抽签减重，抽中短火柴者坠落身亡"
    d = composite_judge(
        solution=SOLUTION, final_answer=answer, key_clues=CLUES,
        logic_rater=rater, logic_samples=3,
    ).to_dict()
    assert d["score"] == 1.0
    assert d["total_score"] == 100.0
