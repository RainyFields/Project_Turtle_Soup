from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from agents.base_agent import ModelConfig


@dataclass
class GameConfig:
    max_rounds: int = 30
    min_rounds_before_answer: int = 5
    debug_mode: bool = False
    save_trajectory: bool = True
    language: str = "zh"
    token_budget: int = 50_000
    seed: Optional[int] = None
    force_final_answer_on_max_rounds: bool = False


@dataclass
class AppConfig:
    oracle: ModelConfig
    questioner: ModelConfig
    game: GameConfig
    config_path: Optional[Path] = None


def _model_cfg(section: Dict[str, Any]) -> ModelConfig:
    return ModelConfig(
        provider=str(section.get("provider", "mock")),
        model=str(section.get("model", "mock")),
        temperature=float(section.get("temperature", 0.2)),
        max_tokens=int(section.get("max_tokens", 512)),
    )


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_app_config(config_path: Optional[Path] = None) -> AppConfig:
    root = Path(__file__).resolve().parents[1]
    path = config_path or (root / "config.yaml")
    raw: Dict[str, Any] = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

    local_path = root / "config.local.yaml"
    if local_path.exists() and config_path is None:
        with local_path.open("r", encoding="utf-8") as f:
            local_raw = yaml.safe_load(f) or {}
        if isinstance(local_raw, dict):
            raw = _deep_merge(raw, local_raw)

    game_raw = raw.get("game") or {}
    return AppConfig(
        oracle=_model_cfg(raw.get("oracle") or {}),
        questioner=_model_cfg(raw.get("questioner") or {}),
        game=GameConfig(
            max_rounds=int(game_raw.get("max_rounds", 30)),
            min_rounds_before_answer=int(game_raw.get("min_rounds_before_answer", 5)),
            debug_mode=bool(game_raw.get("debug_mode", False)),
            save_trajectory=bool(game_raw.get("save_trajectory", True)),
            language=str(game_raw.get("language", "zh")),
            token_budget=int(game_raw.get("token_budget", 50_000)),
            seed=game_raw.get("seed"),
        ),
        config_path=path,
    )


def load_game_config(config_path: Optional[Path] = None) -> GameConfig:
    return load_app_config(config_path).game
