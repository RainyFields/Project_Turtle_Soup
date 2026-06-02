#!/usr/bin/env python3
"""Layer C: generate original puzzle candidates into staging."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def _has_gemini_key() -> bool:
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


def _has_deepseek_key() -> bool:
    return bool(os.getenv("DEEPSEEK_API_KEY"))


def _has_qwen_key() -> bool:
    return bool(os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY"))


def _resolve_provider_and_model(
    *,
    use_mock: bool,
    gen_cfg: dict,
) -> tuple[str, str]:
    if use_mock:
        return "mock", gen_cfg.get("model", "qwen-plus")

    provider = (gen_cfg.get("provider") or "qwen").lower().strip()
    model = gen_cfg.get("model", "qwen-plus")

    if provider in ("qwen", "dashscope", "tongyi"):
        if not _has_qwen_key():
            print("QWEN_API_KEY not set — falling back to --mock")
            return "mock", model
        return "qwen", model

    if provider in ("deepseek",):
        if not _has_deepseek_key():
            print("DEEPSEEK_API_KEY not set — falling back to --mock")
            return "mock", model
        if not (os.getenv("DEEPSEEK_API_KEY") or "").strip().startswith("sk-"):
            print("DEEPSEEK_API_KEY format looks invalid — expected key from platform.deepseek.com")
        return "deepseek", model

    if provider in ("gemini", "google", "google-ai"):
        if not _has_gemini_key():
            print("GEMINI_API_KEY not set — falling back to --mock")
            return "mock", model
        return "gemini", model

    if provider in ("openai", "gpt"):
        if not os.getenv("OPENAI_API_KEY"):
            if _has_gemini_key():
                print("OPENAI_API_KEY not set — using Gemini")
                return "gemini", model if "gemini" in model else "gemini-2.0-flash"
            print("OPENAI_API_KEY not set — falling back to --mock")
            return "mock", model
        return "openai", model

    return provider, model


from generator.create.controllers import sample_slot, slot_to_metadata_tags
from generator.create.llm_generator import generate_one


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", required=True, help="Batch id (subdir under staging)")
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--mock", action="store_true", help="Use mock provider")
    p.add_argument("--config", default="generator/config.yaml")
    p.add_argument(
        "--provider",
        default="",
        help="Override provider (deepseek, gemini, mock)",
    )
    p.add_argument(
        "--model",
        default="",
        help="Override model from config (e.g. gemini-2.5-flash)",
    )
    args = p.parse_args()

    root = ROOT
    cfg = yaml.safe_load((root / args.config).read_text(encoding="utf-8"))
    gen = cfg.get("generation", {})
    if args.provider:
        gen = {**gen, "provider": args.provider}
    paths = cfg.get("paths", {})
    staging = root / paths.get("staging_dir", "data/generator/staging") / args.batch
    staging.mkdir(parents=True, exist_ok=True)

    patterns_path = root / paths.get("analysis_output", "data/generator/analysis") / "patterns.json"
    aggregate_path = root / paths.get("analysis_output", "data/generator/analysis") / "aggregate.json"
    pattern_hints = {}
    aggregate_stats = {}
    if patterns_path.exists():
        pattern_hints = json.loads(patterns_path.read_text(encoding="utf-8"))
    if aggregate_path.exists():
        aggregate_stats = json.loads(aggregate_path.read_text(encoding="utf-8"))

    provider, model = _resolve_provider_and_model(use_mock=args.mock, gen_cfg=gen)
    if args.model:
        model = args.model

    import time

    delay = float(
        gen.get("request_delay_seconds", 0)
        if provider == "deepseek"
        else gen.get("gemini_delay_seconds", 21)
        if provider == "gemini"
        else 0
    )

    for i in range(args.count):
        cal = pattern_hints.get("difficulty_calibration") or aggregate_stats.get(
            "difficulty_calibration"
        )
        cat, diff, source_tags, style_hints = sample_slot(
            aggregate_stats=aggregate_stats,
            difficulty_calibration=cal,
        )
        cid = f"turtle_candidate_{i + 1:03d}"
        puzzle = generate_one(
            category=cat,
            difficulty=diff,
            pattern_hints=pattern_hints,
            provider_name=provider,
            model=model,
            candidate_id=cid,
            style_hints=style_hints,
            source_tags=source_tags,
            metadata_tags=slot_to_metadata_tags(source_tags),
        )
        out = staging / f"{cid}.json"
        out.write_text(json.dumps(puzzle, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {out} ({cat}/{diff})")
        if delay and i + 1 < args.count:
            time.sleep(delay)

    print(f"batch {args.batch}: {args.count} candidate(s)")


if __name__ == "__main__":
    main()
