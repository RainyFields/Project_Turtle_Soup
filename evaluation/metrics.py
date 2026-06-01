from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from engine.trajectory import GameTrajectory, RoundRecord


@dataclass
class MetricsSummary:
    key_element_coverage: float
    question_efficiency: float
    question_diversity: float
    convergence_speed: float
    false_positive_rate: float
    final_answer_accuracy: float
    total_rounds: int

    def to_dict(self) -> Dict[str, float]:
        return {
            "key_element_coverage": self.key_element_coverage,
            "question_efficiency": self.question_efficiency,
            "question_diversity": self.question_diversity,
            "convergence_speed": self.convergence_speed,
            "false_positive_rate": self.false_positive_rate,
            "final_answer_accuracy": self.final_answer_accuracy,
            "total_rounds": float(self.total_rounds),
        }


def _normalize_question(q: str) -> str:
    return "".join(q.lower().split())


def _unique_question_ratio(questions: List[str]) -> float:
    if not questions:
        return 0.0
    normalized = [_normalize_question(q) for q in questions]
    return len(set(normalized)) / len(normalized)


def key_element_coverage(final_answer: Optional[str], key_clues: List[str]) -> float:
    from evaluation.judge import _clue_matches_answer

    if not key_clues:
        return 0.0
    if not final_answer:
        return 0.0
    hits = sum(1 for clue in key_clues if clue and _clue_matches_answer(clue, final_answer))
    return hits / len(key_clues)


def compute_metrics(
    traj: GameTrajectory,
    *,
    key_clues: List[str],
    judge_score: Optional[float] = None,
) -> MetricsSummary:
    rounds: List[RoundRecord] = traj.trajectory
    questions = [r.question for r in rounds if not r.question.upper().startswith("FINAL_ANSWER")]
    answers = [r.answer for r in rounds]

    yes_count = sum(1 for a in answers if a == "是")
    no_count = sum(1 for a in answers if a == "不是")
    total_answers = len(answers) or 1

    coverage = key_element_coverage(traj.final_answer, key_clues)
    diversity = _unique_question_ratio(questions)
    convergence = yes_count / total_answers
    false_positive = no_count / total_answers

    # efficiency: fewer rounds is better when correct; scale inversely capped at 1
    efficiency = 1.0
    if traj.total_rounds > 0:
        efficiency = min(1.0, 10.0 / traj.total_rounds)

    accuracy = judge_score if judge_score is not None else coverage

    return MetricsSummary(
        key_element_coverage=coverage,
        question_efficiency=efficiency,
        question_diversity=diversity,
        convergence_speed=convergence,
        false_positive_rate=false_positive,
        final_answer_accuracy=accuracy,
        total_rounds=traj.total_rounds,
    )


def compute_metrics_from_dict(traj_dict: Dict[str, Any], key_clues: List[str]) -> MetricsSummary:
    traj = GameTrajectory.from_dict(traj_dict)
    judge_score = None
    if traj.evaluation and "score" in traj.evaluation:
        judge_score = float(traj.evaluation["score"])
    return compute_metrics(traj, key_clues=key_clues, judge_score=judge_score)
