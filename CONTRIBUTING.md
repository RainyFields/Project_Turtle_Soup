# Contributing — API keys & local setup

## Do not share API keys

- **Never** paste API keys in GitHub issues, PRs, Slack, or AI chat (including Cursor).
- **Never** commit `.env` or `config.local.yaml` — they are gitignored.
- Each person uses **their own** subscription (OpenAI, Z.AI / GLM, Qwen, etc.).

## First-time setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 1) Configure your keys locally (interactive, hidden input)
python scripts/setup_env.py

# 2) Verify — shows which providers are ready, not the secrets
python scripts/check_env.py

# 3) Optional — personal default models (not shared via git)
cp config.local.yaml.example config.local.yaml
# edit provider/model to match the key you added in .env

# 4) Smoke test without spending credits
python scripts/run_game.py --puzzle turtle_001 --mock
```

## Pick any supported provider

| Provider | `.env` variable | Example model | CLI flag |
|----------|-----------------|---------------|----------|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o` | `--questioner-provider openai` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-sonnet-4-6` | `--questioner-provider anthropic` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek-reasoner` | `--questioner-provider deepseek` |
| Qwen | `QWEN_API_KEY` | `qwen-plus` | `--questioner-provider qwen` |
| **Z.AI / GLM** | `ZAI_API_KEY` | `glm-4.7` | `--questioner-provider zai` |
| Gemini | `GEMINI_API_KEY` | `gemini-2.0-flash` | `--questioner-provider gemini` |
| Ollama | `OLLAMA_BASE_URL` | `llama3.3:70b` | `--questioner-provider ollama` |
| Offline | *(none)* | `mock` | `--mock` |

Keys go in **`.env` only**. Model choice goes in **`config.local.yaml`** (optional) or CLI flags.

### Z.AI / GLM notes

- Use the **general API** endpoint (default in code): `https://api.z.ai/api/paas/v4`
- The **Coding Plan** endpoint (`/api/coding/paas/v4`) is for IDE tools; avoid it for batch benchmark scripts.
- See [Z.AI docs](https://docs.z.ai/api-reference/introduction).

## Running with your models

```bash
# Uses config.yaml + config.local.yaml + .env
python scripts/run_game.py --puzzle turtle_001

# Or explicit overrides
python scripts/run_game.py --puzzle turtle_001 \
  --questioner-provider zai --questioner-model glm-4.7 \
  --oracle-provider zai --oracle-model glm-4.7

# Real timing pilot (one puzzle)
python scripts/run_real_timing.py --questioner-provider zai --questioner-model glm-4.7
```

## What gets committed

| File | Commit? |
|------|---------|
| `.env.example`, `config.local.yaml.example` | ✅ templates only |
| `.env`, `config.local.yaml` | ❌ never |
| `config.yaml` | ✅ shared defaults (no secrets) |
| `results/`, `data/trajectories/` | ❌ gitignored outputs |

## PRs & CI

- Use `--mock` in automated tests (`pytest -q`).
- Do not add team-wide API keys to the repository or GitHub Actions unless using org-level secrets with explicit approval.
