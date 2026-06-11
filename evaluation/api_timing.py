from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CallRecord:
    role: str  # questioner | oracle | judge
    elapsed_s: float
    label: str = ""


@dataclass
class TimingSession:
    records: List[CallRecord] = field(default_factory=list)

    def add(self, role: str, elapsed_s: float, *, label: str = "") -> None:
        self.records.append(CallRecord(role=role, elapsed_s=elapsed_s, label=label))

    def summary(self) -> Dict[str, Any]:
        if not self.records:
            return {"count": 0}
        all_s = [r.elapsed_s for r in self.records]
        by_role: Dict[str, List[float]] = {}
        for r in self.records:
            by_role.setdefault(r.role, []).append(r.elapsed_s)

        def _stats(vals: List[float]) -> Dict[str, float]:
            return {
                "count": len(vals),
                "mean_s": round(statistics.mean(vals), 3),
                "median_s": round(statistics.median(vals), 3),
                "p95_s": round(sorted(vals)[max(0, int(len(vals) * 0.95) - 1)], 3),
                "total_s": round(sum(vals), 3),
            }

        return {
            "count": len(all_s),
            "mean_s": round(statistics.mean(all_s), 3),
            "median_s": round(statistics.median(all_s), 3),
            "p95_s": round(sorted(all_s)[max(0, int(len(all_s) * 0.95) - 1)], 3),
            "total_s": round(sum(all_s), 3),
            "by_role": {role: _stats(vals) for role, vals in by_role.items()},
        }


def patch_agent_timing(session: TimingSession) -> None:
    """Monkey-patch BaseAgent.complete to record per-call latency."""
    from agents import base_agent

    if getattr(base_agent.BaseAgent, "_timing_patched", False):
        return

    original = base_agent.BaseAgent.complete

    def timed_complete(self, *, system: str, user: str, extra: Optional[Dict[str, Any]] = None) -> str:
        role = "unknown"
        cls = type(self).__name__.lower()
        if "questioner" in cls:
            role = "questioner"
        elif "oracle" in cls:
            role = "oracle"
        elif "judge" in cls or "llmjudge" in cls:
            role = "judge"
        elif "final" in user.lower() or "final_answer" in user.lower():
            role = "questioner"
        elif "汤主" in system or "出题者" in system:
            role = "oracle"
        elif "推理游戏" in system:
            role = "questioner"

        t0 = time.perf_counter()
        out = original(self, system=system, user=user, extra=extra)
        session.add(role, time.perf_counter() - t0, label=user[:40])
        return out

    base_agent.BaseAgent.complete = timed_complete  # type: ignore[method-assign]
    base_agent.BaseAgent._timing_patched = True


def extrapolate_full_study(
    *,
    sec_per_call: float,
    exp1_api_calls_pilot: int,
    exp2_api_calls_pilot: int,
    n_puzzles_pilot: int,
    n_caps_pilot: int,
    n_puzzles_full: int = 11,
    n_models: int = 3,
    n_seeds: int = 3,
    n_caps_full: int = 6,
) -> Dict[str, Any]:
    exp1_full_games = n_puzzles_full * n_models * n_seeds
    exp2_full_games = n_caps_full * n_puzzles_full * n_models * n_seeds
    exp1_calls = int(exp1_api_calls_pilot / max(n_puzzles_pilot, 1) * exp1_full_games)
    exp2_calls = int(exp2_api_calls_pilot / max(n_puzzles_pilot * n_caps_pilot, 1) * exp2_full_games)
    combined = exp1_calls + exp2_calls

    def _hours(calls: int) -> float:
        return round(calls * sec_per_call / 3600, 2)

    return {
        "sec_per_call": sec_per_call,
        "exp1_api_calls": exp1_calls,
        "exp2_api_calls": exp2_calls,
        "combined_api_calls": combined,
        "exp1_hours": _hours(exp1_calls),
        "exp2_hours": _hours(exp2_calls),
        "combined_hours": _hours(combined),
        "assumption": f"{n_puzzles_full} puzzles × {n_models} models × {n_seeds} seeds",
    }
