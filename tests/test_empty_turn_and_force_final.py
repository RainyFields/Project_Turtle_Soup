import pytest

from agents.base_agent import ModelConfig
from engine.config import AppConfig, GameConfig
from engine.game import TurtleSoupGame

PUZZLE = {
    "id": "t_empty",
    "surface": "沙漠里躺着一具男尸。",
    "solution": "他从热气球上被扔下去摔死了。",
    "key_clues": ["热气球", "坠落"],
}


class _ScriptedProvider:
    """Replays a fixed list of questioner turns; the oracle always says 是."""

    def __init__(self, turns):
        self.turns = list(turns)
        self.calls = 0

    def generate(self, *, system, user, model, temperature=0.2, max_tokens=512, extra=None):
        if "汤底" in system:  # oracle prompt
            return "是"
        self.calls += 1
        return self.turns.pop(0) if self.turns else "还有别的线索吗？"


def _game(turns, **game_kwargs):
    cfg = AppConfig(
        oracle=ModelConfig(provider="mock", model="m"),
        questioner=ModelConfig(provider="mock", model="m"),
        game=GameConfig(save_trajectory=False, min_rounds_before_answer=0, **game_kwargs),
    )
    game = TurtleSoupGame(PUZZLE, app_config=cfg)
    provider = _ScriptedProvider(turns)
    game.oracle.provider = provider
    game.questioner.provider = provider
    return game


def test_empty_turns_do_not_consume_rounds():
    # two empty replies interleaved; all 3 real questions must still be asked
    turns = ["问题一？", "", "问题二？", "", "问题三？"]
    traj = _game(turns, max_rounds=3, max_empty_turns=5).run(verbose=False).trajectory
    assert traj.total_rounds == 3
    assert [r.question for r in traj.trajectory] == ["问题一？", "问题二？", "问题三？"]


def test_persistent_empty_replies_terminate_the_game():
    traj = _game([""] * 10, max_rounds=5, max_empty_turns=3).run(verbose=False).trajectory
    assert traj.terminated_by == "empty_response"
    assert traj.total_rounds == 0


def test_without_force_flag_max_rounds_ends_unanswered():
    traj = _game(["问题一？", "问题二？"], max_rounds=2).run(verbose=False).trajectory
    assert traj.terminated_by == "max_rounds"
    assert traj.final_answer is None


def test_force_final_answer_extracts_an_answer_on_the_last_round():
    turns = ["问题一？", "问题二？", "FINAL_ANSWER: 他从热气球上掉下来摔死了"]
    traj = _game(
        turns, max_rounds=2, force_final_answer_on_max_rounds=True
    ).run(verbose=False).trajectory
    assert traj.terminated_by == "final_answer"
    assert "热气球" in traj.final_answer


def test_config_loader_reads_force_final_answer(tmp_path):
    from engine.config import load_app_config

    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        "game:\n  force_final_answer_on_max_rounds: true\n  max_rounds: 7\n",
        encoding="utf-8",
    )
    loaded = load_app_config(cfg)
    assert loaded.game.force_final_answer_on_max_rounds is True
    assert loaded.game.max_rounds == 7


def test_provider_exception_is_treated_as_an_empty_turn():
    """A provider that gives up after retries must not crash the game."""
    from agents.base_agent import EmptyResponseError

    class _Flaky:
        def __init__(self):
            self.n = 0

        def generate(self, *, system, user, model, temperature=0.2, max_tokens=512, extra=None):
            if "汤底" in system:
                return "是"
            self.n += 1
            if self.n == 1:
                raise EmptyResponseError("gave up")
            return "真正的问题？"

    cfg = AppConfig(
        oracle=ModelConfig(provider="mock", model="m"),
        questioner=ModelConfig(provider="mock", model="m"),
        game=GameConfig(save_trajectory=False, min_rounds_before_answer=0, max_rounds=1),
    )
    game = TurtleSoupGame(PUZZLE, app_config=cfg)
    provider = _Flaky()
    game.oracle.provider = provider
    game.questioner.provider = provider

    traj = game.run(verbose=False).trajectory
    assert traj.total_rounds == 1
    assert traj.trajectory[0].question == "真正的问题？"


def test_config_loader_reads_max_empty_turns(tmp_path):
    from engine.config import load_app_config

    cfg = tmp_path / "c.yaml"
    cfg.write_text("game:\n  max_empty_turns: 9\n", encoding="utf-8")
    assert load_app_config(cfg).game.max_empty_turns == 9
