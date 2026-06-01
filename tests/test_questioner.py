from agents.base_agent import ModelConfig
from agents.model_providers.mock_provider import MockProvider
from agents.questioner_agent import QuestionerAgent, QuestionerInputs


def test_questioner_returns_next_question():
    agent = QuestionerAgent(
        provider=MockProvider(),
        model_cfg=ModelConfig(provider="mock", model="mock"),
        inputs=QuestionerInputs(surface="一个男人点了海龟汤后自杀。", min_questions=3),
    )
    q1 = agent.next_turn("(无)")
    assert q1
    assert not q1.upper().startswith("FINAL_ANSWER")


def test_questioner_eventually_submits_final_answer():
    agent = QuestionerAgent(
        provider=MockProvider(),
        model_cfg=ModelConfig(provider="mock", model="mock"),
        inputs=QuestionerInputs(surface="一个男人点了海龟汤后自杀。", min_questions=1),
    )
    history = ""
    turn = ""
    for i in range(8):
        turn = agent.next_turn(history)
        if turn.upper().startswith("FINAL_ANSWER"):
            break
        n = i + 1
        history += f"\nQ{n}: {turn}\nA{n}: 是"
    assert turn.upper().startswith("FINAL_ANSWER")
