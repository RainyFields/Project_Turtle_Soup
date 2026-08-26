import pytest

from agents.base_agent import EmptyResponseError
from agents.model_providers import tinker_provider
from agents.model_providers.tinker_provider import TinkerProvider, _strip_thinking


class _FakeTokenizer:
    chat_template = "{{ messages }}"

    def __init__(self):
        self.rendered = None
        self.template_kwargs = None

    def apply_chat_template(self, messages, *, add_generation_prompt, tokenize, **kwargs):
        self.rendered = messages
        self.template_kwargs = kwargs
        assert add_generation_prompt and tokenize
        return {"input_ids": [1, 2, 3]}  # newer transformers: BatchEncoding-style

    def encode(self, text):  # pragma: no cover - chat template path is used
        return [0]

    def decode(self, tokens, *, skip_special_tokens):
        return tokens


class _FakeSequence:
    def __init__(self, text):
        self.tokens = text  # fake decode() passes tokens straight through


class _FakeResponse:
    def __init__(self, text):
        self.sequences = [_FakeSequence(text)]


class _FakeSamplingClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def sample(self, *, prompt, num_samples, sampling_params):
        self.calls.append(sampling_params)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return _FakeResponse(reply)


class _FakeTypes:
    class ModelInput:
        @staticmethod
        def from_ints(ids):
            return ids

    @staticmethod
    def SamplingParams(**kwargs):
        return kwargs


def _provider(monkeypatch, replies):
    provider = TinkerProvider.__new__(TinkerProvider)  # skip SDK-import __init__
    provider._types = _FakeTypes()
    client = _FakeSamplingClient(replies)
    tokenizer = _FakeTokenizer()
    provider._clients = {"m": (client, tokenizer)}
    monkeypatch.setattr(tinker_provider, "BASE_BACKOFF_S", 0.0)
    monkeypatch.setattr(
        TinkerProvider, "_sleep_backoff", staticmethod(lambda delay, attempt, exc: 0.0)
    )
    return provider, client, tokenizer


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("TINKER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="TINKER_API_KEY"):
        TinkerProvider()


def test_generate_strips_thinking_and_renders_chat(monkeypatch):
    provider, client, tokenizer = _provider(
        monkeypatch, ["<think>盘算中…</think>他是盲人吗？"]
    )
    out = provider.generate(system="sys", user="usr", model="m", max_tokens=64)
    assert out == "他是盲人吗？"
    assert tokenizer.rendered[0] == {"role": "system", "content": "sys"}
    assert client.calls[0]["max_tokens"] == 64


def test_empty_after_thinking_retries_then_raises(monkeypatch):
    monkeypatch.setattr(tinker_provider, "MAX_ATTEMPTS", 2)
    provider, client, _ = _provider(monkeypatch, ["<think>只想不说</think>", ""])
    with pytest.raises(EmptyResponseError):
        provider.generate(system="s", user="u", model="m")
    assert len(client.calls) == 2


def test_transport_error_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr(tinker_provider, "MAX_ATTEMPTS", 3)
    provider, client, _ = _provider(
        monkeypatch, [ConnectionError("blip"), "答案是抽签。"]
    )
    assert provider.generate(system="s", user="u", model="m") == "答案是抽签。"
    assert len(client.calls) == 2


def test_tinker_think_env_disables_template_thinking(monkeypatch):
    monkeypatch.setenv("TINKER_THINK", "0")
    provider, _, tokenizer = _provider(monkeypatch, ["问题？"])
    provider.generate(system="s", user="u", model="m")
    assert tokenizer.template_kwargs == {"enable_thinking": False}


def test_no_think_env_keeps_template_default(monkeypatch):
    monkeypatch.delenv("TINKER_THINK", raising=False)
    provider, _, tokenizer = _provider(monkeypatch, ["问题？"])
    provider.generate(system="s", user="u", model="m")
    assert tokenizer.template_kwargs == {}


def test_dangling_close_tag_is_stripped():
    # Qwen3-style templates can open <think> inside the generation prompt.
    assert _strip_thinking("推理若干…</think>\n最终答案") == "最终答案"


def test_factory_returns_singleton_tinker(monkeypatch):
    # Tinker caps active sessions; the factory must reuse one provider per process.
    import agents.provider_factory as pf

    created = []

    class _FakeProvider:
        def __init__(self):
            created.append(self)

    monkeypatch.setattr(pf, "_TINKER_SINGLETON", None)
    import agents.model_providers.tinker_provider as tp

    monkeypatch.setattr(tp, "TinkerProvider", _FakeProvider)
    a = pf.get_provider("tinker")
    b = pf.get_provider("thinking-machines")
    assert a is b and len(created) == 1
