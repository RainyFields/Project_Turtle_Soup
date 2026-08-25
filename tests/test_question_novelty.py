from evaluation.metrics import _vocabulary, question_novelty


def test_empty_rounds():
    assert question_novelty([]) == (0.0, 0.0)


def test_first_round_is_always_novel():
    novelty, new_share = question_novelty(["死者是自杀吗？"])
    assert novelty == 1.0
    assert new_share == 1.0


def test_identical_repeats_are_flagged_as_stalled():
    q = "死者是被烧死的吗？"
    novelty, new_share = question_novelty([q, q, q, q])
    assert novelty == 0.25  # only the first round introduces vocabulary
    assert new_share == 0.25


def test_distinct_questions_stay_novel():
    novelty, _ = question_novelty(
        ["死者是自杀吗？", "现场还有其他人吗？", "那半根火柴是抽签用的吗？"]
    )
    assert novelty == 1.0


def test_growing_recap_without_new_content_is_caught():
    # the observed degeneration: an ever-repeated recap that asks nothing new
    recap = "基于目前的问答记录梳理：环境是沙漠，死者手里攥着半根火柴。"
    novelty, new_share = question_novelty([recap, recap + "环境是沙漠。", recap])
    assert novelty < 1.0
    assert new_share < 0.5


def test_diversity_blind_spot_is_covered():
    # near-identical rounds differ textually, so unique-ratio calls them diverse
    from evaluation.metrics import _unique_question_ratio

    rounds = ["沙漠里的男尸手攥火柴。", "沙漠里的男尸手攥火柴", "沙漠里的男尸手攥火柴。 "]
    assert _unique_question_ratio(rounds) > 0.5  # looks fine to the old metric
    novelty, _ = question_novelty(rounds)
    assert novelty < 0.5  # novelty sees they add nothing


def test_vocabulary_mixes_cjk_bigrams_and_ascii_words():
    v = _vocabulary("热气球 balloon")
    assert "热气" in v and "气球" in v
    assert "balloon" in v


def test_openrouter_retries_then_succeeds(monkeypatch, capsys):
    """A burst 429 must not kill a benchmark run."""
    import agents.model_providers.openrouter_provider as orp

    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    monkeypatch.setattr(orp.time, "sleep", lambda s: None)
    provider = orp.OpenRouterProvider()

    calls = {"n": 0}

    class _Msg:
        content = "是"

    class _Resp:
        choices = [type("C", (), {"message": _Msg()})()]

    def fake_create(**kwargs):
        calls["n"] += 1
        if calls["n"] < 3:
            raise orp.RateLimitError(
                "rate limited", response=_FakeResponse(429), body=None
            )
        return _Resp()

    monkeypatch.setattr(provider.client.chat.completions, "create", fake_create)
    assert provider.generate(system="s", user="u", model="stealth/ox-alpha") == "是"
    assert calls["n"] == 3


def test_openrouter_does_not_retry_client_errors(monkeypatch):
    import agents.model_providers.openrouter_provider as orp

    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    monkeypatch.setattr(orp.time, "sleep", lambda s: None)
    provider = orp.OpenRouterProvider()

    calls = {"n": 0}

    def fake_create(**kwargs):
        calls["n"] += 1
        raise orp.APIStatusError("bad request", response=_FakeResponse(400), body=None)

    monkeypatch.setattr(provider.client.chat.completions, "create", fake_create)
    import pytest

    with pytest.raises(orp.APIStatusError):
        provider.generate(system="s", user="u", model="stealth/ox-alpha")
    assert calls["n"] == 1  # 4xx is not retried


class _FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code
        self.headers = {}
        self.request = None
