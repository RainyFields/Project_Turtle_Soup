#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from agents.base_agent import ModelConfig
from engine.config import AppConfig, load_app_config
from engine.game import TurtleSoupGame, load_puzzle
from engine.trajectory import save_trajectory
from evaluation.judge import JudgeResult, LLMJudge, composite_judge, heuristic_judge
from evaluation.metrics import compute_metrics
from evaluation.report import print_evaluation_report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run a single turtle-soup game")
    p.add_argument("--puzzle", default="turtle_001", help="Puzzle id (e.g. turtle_001)")
    p.add_argument("--config", default=None, help="Path to config.yaml")
    p.add_argument("--oracle-provider", default=None)
    p.add_argument("--oracle-model", default=None)
    p.add_argument("--questioner-provider", default=None)
    p.add_argument("--questioner-model", default=None)
    p.add_argument("--max-rounds", type=int, default=None)
    p.add_argument("--min-rounds", type=int, default=None, help="Min rounds before final answer")
    p.add_argument("--debug", action="store_true")
    p.add_argument(
        "--force-final-answer",
        action="store_true",
        help="On the last round, require a FINAL_ANSWER instead of ending unanswered",
    )
    p.add_argument("--mock", action="store_true", help="Use mock providers for both agents")
    p.add_argument("--no-save", action="store_true", help="Do not write trajectory json")
    p.add_argument("--no-judge", action="store_true", help="Skip LLM judge (heuristic only)")
    p.add_argument("--judge-provider", default="openai")
    p.add_argument("--judge-model", default="gpt-4o")
    p.add_argument(
        "--composite-judge",
        action="store_true",
        help="Score with composite_judge (clue recall 70 + logic 30) instead of "
        "the single-call LLM judge; --no-judge/--mock drops the logic 30",
    )
    p.add_argument("--logic-samples", type=int, default=3, help="Logic ratings to average")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--quiet", action="store_true")
    return p


def apply_overrides(app: AppConfig, args: argparse.Namespace) -> AppConfig:
    if args.mock:
        app.oracle = ModelConfig(provider="mock", model="mock")
        app.questioner = ModelConfig(provider="mock", model="mock")
    if args.oracle_provider:
        app.oracle = ModelConfig(
            provider=args.oracle_provider,
            model=args.oracle_model or app.oracle.model,
            temperature=app.oracle.temperature,
            max_tokens=app.oracle.max_tokens,
        )
    elif args.oracle_model:
        app.oracle = ModelConfig(
            provider=app.oracle.provider,
            model=args.oracle_model,
            temperature=app.oracle.temperature,
            max_tokens=app.oracle.max_tokens,
        )
    if args.questioner_provider:
        app.questioner = ModelConfig(
            provider=args.questioner_provider,
            model=args.questioner_model or app.questioner.model,
            temperature=app.questioner.temperature,
            max_tokens=app.questioner.max_tokens,
        )
    elif args.questioner_model:
        app.questioner = ModelConfig(
            provider=app.questioner.provider,
            model=args.questioner_model,
            temperature=app.questioner.temperature,
            max_tokens=app.questioner.max_tokens,
        )
    if args.max_rounds is not None:
        app.game.max_rounds = args.max_rounds
    if args.min_rounds is not None:
        app.game.min_rounds_before_answer = args.min_rounds
    if args.force_final_answer:
        app.game.force_final_answer_on_max_rounds = True
    if args.debug:
        app.game.debug_mode = True
    if args.no_save:
        app.game.save_trajectory = False
    if args.seed is not None:
        app.game.seed = args.seed
    return app


def main() -> int:
    args = build_parser().parse_args()
    config_path = Path(args.config) if args.config else None
    app = apply_overrides(load_app_config(config_path), args)

    puzzle = load_puzzle(args.puzzle)
    game = TurtleSoupGame(puzzle, app_config=app)
    result = game.run(verbose=not args.quiet)
    traj = result.trajectory

    extra_evaluation: dict = {}
    judge = heuristic_judge(
        solution=puzzle["solution"],
        final_answer=traj.final_answer,
        key_clues=puzzle.get("key_clues", []),
    )
    if args.composite_judge:
        rater = None
        if not args.no_judge and traj.final_answer and not args.mock:
            try:
                rater = LLMJudge(provider_name=args.judge_provider, model=args.judge_model)
            except Exception:
                rater = None
        comp = composite_judge(
            solution=puzzle["solution"],
            final_answer=traj.final_answer,
            key_clues=puzzle.get("key_clues", []),
            logic_rater=rater,
            logic_samples=args.logic_samples,
        )
        extra_evaluation = comp.to_dict()
        judge = JudgeResult(
            score=extra_evaluation["score"],
            reasoning=(
                f"composite：关键词 {comp.key_clue_score:.1f}/70"
                f" + 逻辑 {comp.logic_score:.1f}/30"
                f"（难度 {comp.difficulty_band}，逻辑采样 {len(comp.logic_samples)} 次）"
            ),
            hit_elements=comp.hit_clues,
            missed_elements=comp.missed_clues,
        )
    elif not args.no_judge and traj.final_answer and not args.mock:
        try:
            llm_judge = LLMJudge(provider_name=args.judge_provider, model=args.judge_model)
            judge = llm_judge.judge(
                solution=puzzle["solution"],
                final_answer=traj.final_answer,
                key_clues=puzzle.get("key_clues", []),
                use_llm=True,
            )
        except Exception:
            pass

    metrics = compute_metrics(traj, key_clues=puzzle.get("key_clues", []), judge_score=judge.score)
    traj.evaluation = {
        "score": judge.score,
        **judge.to_dict(),
        **extra_evaluation,
    }

    if result.trajectory_path:
        save_trajectory(traj, result.trajectory_path)

    if not args.quiet:
        print_evaluation_report(metrics=metrics, judge=judge)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
