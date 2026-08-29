from agents.base_agent import ModelConfig
from engine.config import AppConfig, GameConfig
from engine.game import TurtleSoupGame, load_puzzle


def _a_real_puzzle_id():
    """First puzzle of the verified set — avoids hardcoding ids that get renumbered."""
    from engine.game import list_puzzle_ids

    ids = list_puzzle_ids(family="real")
    assert ids, "no puzzles in data/puzzles/real/"
    return ids[0]
from evaluation.judge import composite_judge
from evaluation.round_studies import (
    JudgeSpec,
    ModelSpec,
    _judge_score,
    run_round_cap,
    run_round_curve,
)


def _mock_app(max_rounds: int, *, force: bool = False) -> AppConfig:
    return AppConfig(
        oracle=ModelConfig(provider="mock", model="mock"),
        questioner=ModelConfig(provider="mock", model="mock"),
        game=GameConfig(
            max_rounds=max_rounds,
            min_rounds_before_answer=0,
            save_trajectory=False,
            force_final_answer_on_max_rounds=force,
        ),
    )


def test_force_final_on_max_rounds():
    puzzle = load_puzzle(_a_real_puzzle_id())
    game = TurtleSoupGame(puzzle, app_config=_mock_app(3, force=True))
    result = game.run(verbose=False)
    assert result.trajectory.final_answer
    assert result.trajectory.terminated_by in {"final_answer", "max_rounds"}


def test_round_curve_returns_per_round_scores():
    puzzle = load_puzzle(_a_real_puzzle_id())
    row = run_round_curve(
        puzzle,
        app_config=_mock_app(30),
        max_checkpoint_round=8,
    )
    assert len(row["accuracy_by_round"]) >= 1
    assert all(0.0 <= v <= 1.0 for v in row["accuracy_by_round"].values())


def test_round_cap_sweep():
    puzzle = load_puzzle(_a_real_puzzle_id())
    row = run_round_cap(puzzle, app_config=_mock_app(5, force=True), round_cap=5)
    assert row["round_cap"] == 5
    assert row["final_answer"]
    assert 0.0 <= row["score"] <= 1.0


class _FixedRater:
    """Always rates the causal logic 1.0."""

    def complete(self, *, system, user):
        return '{"logic": 1.0}'


def test_composite_spec_matches_direct_composite_call():
    puzzle = load_puzzle(_a_real_puzzle_id())
    spec = JudgeSpec(mode="composite")
    answer = puzzle["solution"]
    expected = composite_judge(
        solution=puzzle["solution"],
        final_answer=answer,
        key_clues=puzzle.get("key_clues", []),
        logic_rater=None,
        logic_samples=0,
    ).to_dict()["score"]
    assert _judge_score(puzzle, answer, judge=spec) == expected


def test_composite_spec_rater_adds_logic_points():
    puzzle = load_puzzle(_a_real_puzzle_id())
    spec = JudgeSpec(mode="composite", logic_samples=2)
    answer = "一个与线索无关的答案"
    clue_only = _judge_score(puzzle, answer, judge=spec)
    with_rater = _judge_score(puzzle, answer, judge=spec, rater=_FixedRater())
    assert abs((with_rater - clue_only) - 0.3) < 1e-6  # logic contributes 30/100


def test_round_cap_accepts_composite_judge():
    puzzle = load_puzzle(_a_real_puzzle_id())
    row = run_round_cap(
        puzzle,
        app_config=_mock_app(4, force=True),
        round_cap=4,
        judge=JudgeSpec(mode="composite"),
    )
    assert 0.0 <= row["score"] <= 1.0
