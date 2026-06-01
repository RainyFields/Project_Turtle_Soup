from agents.base_agent import ModelConfig
from agents.model_providers.mock_provider import MockProvider
from agents.oracle_agent import OracleAgent, OracleInputs


def test_oracle_clamps_to_allowed_answers():
    agent = OracleAgent(
        provider=MockProvider(),
        model_cfg=ModelConfig(provider="mock", model="mock"),
        inputs=OracleInputs(
            surface="汤面",
            solution="男人经历海难，妻子失踪，味道不同导致自杀。",
        ),
    )
    assert agent.answer("他们曾经历过海难吗？") in {"是", "不是", "与此无关"}
    assert agent.answer("男人在餐厅出了意外吗？") == "不是"


def test_oracle_final_answer_judgment():
    agent = OracleAgent(
        provider=MockProvider(),
        model_cfg=ModelConfig(provider="mock", model="mock"),
        inputs=OracleInputs(surface="汤面", solution="海难与妻子相关的故事。"),
    )
    verdict = agent.answer("FINAL_ANSWER: 海难中喝过假海龟汤，味道不同后自杀")
    assert verdict in {"是", "不是"}
