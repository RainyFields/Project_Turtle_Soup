from agents.base_agent import ModelConfig
from engine.config import AppConfig, GameConfig
from engine.game import TurtleSoupGame, load_puzzle
from evaluation.round_studies import ModelSpec, run_round_cap, run_round_curve


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
    puzzle = load_puzzle("turtle_002")
    game = TurtleSoupGame(puzzle, app_config=_mock_app(3, force=True))
    result = game.run(verbose=False)
    assert result.trajectory.final_answer
    assert result.trajectory.terminated_by in {"final_answer", "max_rounds"}


def test_round_curve_returns_per_round_scores():
    puzzle = load_puzzle("turtle_001")
    row = run_round_curve(
        puzzle,
        app_config=_mock_app(30),
        max_checkpoint_round=8,
    )
    assert len(row["accuracy_by_round"]) >= 1
    assert all(0.0 <= v <= 1.0 for v in row["accuracy_by_round"].values())


def test_round_cap_sweep():
    puzzle = load_puzzle("turtle_001")
    row = run_round_cap(puzzle, app_config=_mock_app(5, force=True), round_cap=5)
    assert row["round_cap"] == 5
    assert row["final_answer"]
    assert 0.0 <= row["score"] <= 1.0
