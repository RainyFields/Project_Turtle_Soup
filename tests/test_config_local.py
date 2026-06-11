from pathlib import Path

import yaml

from engine.config import load_app_config


def test_config_local_merge(tmp_path: Path):
    base = tmp_path / "config.yaml"
    local = tmp_path / "config.local.yaml"
    base.write_text(
        yaml.dump({"oracle": {"provider": "openai", "model": "gpt-4o"}, "questioner": {"provider": "mock", "model": "mock"}}),
        encoding="utf-8",
    )
    local.write_text(
        yaml.dump({"questioner": {"provider": "zai", "model": "glm-4.7"}}),
        encoding="utf-8",
    )
    # load_app_config looks for config.local.yaml next to repo root only;
    # test merge helper via full load by patching path — use direct merge test instead
    from engine.config import _deep_merge

    merged = _deep_merge(
        yaml.safe_load(base.read_text()),
        yaml.safe_load(local.read_text()),
    )
    assert merged["oracle"]["provider"] == "openai"
    assert merged["questioner"]["provider"] == "zai"
