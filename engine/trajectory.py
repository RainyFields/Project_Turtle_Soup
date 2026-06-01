from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class RoundRecord:
    round: int
    question: str
    answer: str
    oracle_reasoning: Optional[str] = None


@dataclass
class GameTrajectory:
    game_id: str
    puzzle_id: str
    oracle_model: str
    questioner_model: str
    start_time: str
    trajectory: List[RoundRecord] = field(default_factory=list)
    end_time: Optional[str] = None
    total_rounds: int = 0
    terminated_by: Optional[str] = None
    final_answer: Optional[str] = None
    evaluation: Optional[Dict[str, Any]] = None

    def add_round(self, record: RoundRecord) -> None:
        self.trajectory.append(record)
        self.total_rounds = len(self.trajectory)

    def finish(self, *, terminated_by: str, final_answer: Optional[str] = None) -> None:
        self.end_time = _utc_now_iso()
        self.terminated_by = terminated_by
        self.final_answer = final_answer
        self.total_rounds = len(self.trajectory)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["trajectory"] = [asdict(r) for r in self.trajectory]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameTrajectory":
        rounds = [RoundRecord(**r) for r in data.get("trajectory", [])]
        return cls(
            game_id=data["game_id"],
            puzzle_id=data["puzzle_id"],
            oracle_model=data["oracle_model"],
            questioner_model=data["questioner_model"],
            start_time=data["start_time"],
            trajectory=rounds,
            end_time=data.get("end_time"),
            total_rounds=int(data.get("total_rounds", len(rounds))),
            terminated_by=data.get("terminated_by"),
            final_answer=data.get("final_answer"),
            evaluation=data.get("evaluation"),
        )


def save_trajectory(traj: GameTrajectory, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(traj.to_dict(), f, ensure_ascii=False, indent=2)
    return path


def load_trajectory(path: Path) -> GameTrajectory:
    with path.open("r", encoding="utf-8") as f:
        return GameTrajectory.from_dict(json.load(f))


def new_game_id(puzzle_id: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"game_{ts}_{puzzle_id}"
