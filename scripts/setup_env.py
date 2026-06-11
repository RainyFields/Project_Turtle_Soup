#!/usr/bin/env python3
"""
Interactive local .env setup. Keys stay on your machine — never paste them in chat or git.
"""
from __future__ import annotations

import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
EXAMPLE_PATH = ROOT / ".env.example"

PROVIDER_FIELDS = [
    ("OPENAI_API_KEY", "OpenAI (gpt-4o, etc.)"),
    ("ANTHROPIC_API_KEY", "Anthropic (Claude)"),
    ("DEEPSEEK_API_KEY", "DeepSeek"),
    ("QWEN_API_KEY", "Qwen / DashScope"),
    ("ZAI_API_KEY", "Z.AI / GLM (z.ai subscription)"),
    ("GEMINI_API_KEY", "Google Gemini"),
    ("MISTRAL_API_KEY", "Mistral"),
]


def main() -> int:
    print("=" * 60)
    print("turtle-soup-bench — local API key setup")
    print("=" * 60)
    print()
    print("SECURITY:")
    print("  • Keys are written ONLY to .env (gitignored)")
    print("  • Do NOT send API keys in Slack, email, or AI chat")
    print("  • Each collaborator uses their own subscription")
    print()

    if ENV_PATH.exists():
        ans = input(".env already exists. Merge new keys? [y/N]: ").strip().lower()
        if ans != "y":
            print("Cancelled.")
            return 0
        existing = ENV_PATH.read_text(encoding="utf-8")
    else:
        existing = EXAMPLE_PATH.read_text(encoding="utf-8") if EXAMPLE_PATH.exists() else ""
        print(f"Creating {ENV_PATH} from .env.example\n")

    lines = existing.splitlines()
    values: dict[str, str] = {}
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            values[k.strip()] = v.strip()

    print("Enter API keys to configure (press Enter to skip):\n")
    for env_name, label in PROVIDER_FIELDS:
        if values.get(env_name):
            skip = input(f"  {label}: already set — replace? [y/N]: ").strip().lower()
            if skip != "y":
                continue
        key = getpass.getpass(f"  {label} ({env_name}): ")
        if key.strip():
            values[env_name] = key.strip()

    ollama = input("\nOllama base URL [http://localhost:11434]: ").strip()
    if ollama:
        values["OLLAMA_BASE_URL"] = ollama

    # Rebuild file: keep comments/structure from example, update values
    out_lines: list[str] = []
    written_keys: set[str] = set()
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            k = line.split("=", 1)[0].strip()
            if k in values:
                out_lines.append(f"{k}={values[k]}")
                written_keys.add(k)
            else:
                out_lines.append(line)
        else:
            out_lines.append(line)

    for k, v in values.items():
        if k not in written_keys:
            out_lines.append(f"{k}={v}")

    ENV_PATH.write_text("\n".join(out_lines).rstrip() + "\n", encoding="utf-8")
    print(f"\nWrote {ENV_PATH}")
    print("Verify (no secrets shown): python scripts/check_env.py")
    print("\nOptional: copy config.local.yaml.example → config.local.yaml for your default models.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
