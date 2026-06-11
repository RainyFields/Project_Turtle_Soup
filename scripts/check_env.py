#!/usr/bin/env python3
"""Check which API providers are configured (never prints secret values)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

PROVIDERS = [
    ("openai", ["OPENAI_API_KEY"]),
    ("anthropic", ["ANTHROPIC_API_KEY"]),
    ("deepseek", ["DEEPSEEK_API_KEY"]),
    ("qwen", ["QWEN_API_KEY", "DASHSCOPE_API_KEY"]),
    ("zai / glm", ["ZAI_API_KEY", "Z_AI_API_KEY"]),
    ("gemini", ["GEMINI_API_KEY", "GOOGLE_API_KEY"]),
    ("mistral", ["MISTRAL_API_KEY"]),
    ("ollama (local)", ["OLLAMA_BASE_URL"]),  # no key; URL defaults to localhost
]


def _set(name: str) -> bool:
    v = (os.getenv(name) or "").strip()
    return bool(v) and v not in ("your-key-here", "sk-...")


def main() -> int:
    env_path = ROOT / ".env"
    local_cfg = ROOT / "config.local.yaml"

    print("turtle-soup-bench — environment check\n")
    print(f"  .env file:           {'found' if env_path.exists() else 'MISSING (run: python scripts/setup_env.py)'}")
    print(f"  config.local.yaml:   {'found' if local_cfg.exists() else 'optional (see config.local.yaml.example)'}\n")

    configured = []
    for label, vars_ in PROVIDERS:
        ok = any(_set(v) for v in vars_)
        mark = "✓" if ok else "·"
        print(f"  [{mark}] {label}")
        if ok:
            configured.append(label)

    print()
    if configured:
        print(f"Ready for: {', '.join(configured)}")
        print("Example:")
        if any("zai" in c for c in configured):
            print("  python scripts/run_real_timing.py --questioner-provider zai --questioner-model glm-4.7")
        elif any("qwen" in c for c in configured):
            print("  python scripts/run_real_timing.py --questioner-provider qwen --questioner-model qwen-plus")
        else:
            print("  python scripts/run_game.py --puzzle turtle_001 --questioner-provider <provider> --questioner-model <model>")
    else:
        print("No API keys detected. Use --mock for offline runs:")
        print("  python scripts/run_game.py --puzzle turtle_001 --mock")
        print("\nOr configure keys: python scripts/setup_env.py")

    return 0 if configured or env_path.exists() else 1


if __name__ == "__main__":
    raise SystemExit(main())
