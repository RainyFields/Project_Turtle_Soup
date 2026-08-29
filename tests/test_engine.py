from agents.base_agent import ModelConfig
from engine.config import AppConfig, GameConfig
from engine.game import TurtleSoupGame, load_puzzle, parse_final_answer


def _a_real_puzzle_id():
    """First puzzle of the verified set — avoids hardcoding ids that get renumbered."""
    from engine.game import list_puzzle_ids

    ids = list_puzzle_ids(family="real")
    assert ids, "no puzzles in data/puzzles/real/"
    return ids[0]
from evaluation.judge import heuristic_judge
from evaluation.metrics import compute_metrics


def _mock_app() -> AppConfig:
    return AppConfig(
        oracle=ModelConfig(provider="mock", model="mock"),
        questioner=ModelConfig(provider="mock", model="mock"),
        game=GameConfig(
            max_rounds=15,
            min_rounds_before_answer=5,
            save_trajectory=False,
            debug_mode=False,
        ),
    )


def test_load_puzzle_turtle_001():
    puzzle = load_puzzle(_a_real_puzzle_id())
    assert puzzle["id"] == _a_real_puzzle_id()
    assert "surface" in puzzle and "solution" in puzzle


def test_parse_final_answer():
    assert parse_final_answer("FINAL_ANSWER: 海难") == "海难"
    assert parse_final_answer("final_answer: x") == "x"
    assert parse_final_answer("普通问题？") is None


def test_full_game_mock():
    puzzle = load_puzzle(_a_real_puzzle_id())
    game = TurtleSoupGame(puzzle, app_config=_mock_app())
    result = game.run(verbose=False)
    traj = result.trajectory
    assert traj.total_rounds >= 1
    assert traj.terminated_by in {"final_answer", "max_rounds", "token_budget"}
    if traj.final_answer:
        judge = heuristic_judge(
            solution=puzzle["solution"],
            final_answer=traj.final_answer,
            key_clues=puzzle["key_clues"],
        )
        metrics = compute_metrics(traj, key_clues=puzzle["key_clues"], judge_score=judge.score)
        assert 0.0 <= metrics.final_answer_accuracy <= 1.0
