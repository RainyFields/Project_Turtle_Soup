# Contributing — API keys & local setup

## Do not share API keys

- **Never** paste API keys in GitHub issues, PRs, Slack, or AI chat (including Cursor).
- **Never** commit `.env` or `config.local.yaml` — they are gitignored.
- Each person uses **their own** subscription.

## First-time setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/setup_env.py
python scripts/check_env.py
cp config.local.yaml.example config.local.yaml   # optional

python scripts/run_game.py --puzzle refsoup_008 --mock
```

## Providers

| Provider | `.env` | Example model | CLI |
|----------|--------|---------------|-----|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o` | `openai` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-sonnet-4-6` | `anthropic` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek-reasoner` | `deepseek` |
| Qwen | `QWEN_API_KEY` | `qwen-plus` | `qwen` |
| Z.AI / GLM | `ZAI_API_KEY` | `glm-4.7` | `zai` |
| Gemini | `GEMINI_API_KEY` | `gemini-2.0-flash` | `gemini` |
| Ollama | `OLLAMA_BASE_URL` | `qwen2.5:7b` | `ollama` |
| Offline | — | `mock` | `--mock` |

### Ollama

- Timeout default **600s** (`OLLAMA_TIMEOUT` to override).
- Slow models (`qwen3.5:4b`) need warmup; budget 40–60 min for full pilot.

### Z.AI / GLM

- Coding Plan: `ZAI_USE_CODING_ENDPOINT=1` in `.env`.

## Running

```bash
python scripts/run_game.py --puzzle refsoup_008

python scripts/run_game.py --puzzle refsoup_008 \
  --questioner-provider zai --questioner-model glm-4.7 \
  --oracle-provider zai --oracle-model glm-4.7

python scripts/run_pilot.py --puzzles refsoup_008 --mock

python scripts/run_pilot.py --puzzles refsoup_008 \
  --questioner-provider ollama --questioner-model qwen2.5:7b \
  --oracle-provider ollama --oracle-model qwen2.5:7b \
  --max-rounds 12 --round-caps 5 10 12

python scripts/run_real_timing.py \
  --puzzle refsoup_008 --questioner-provider qwen --questioner-model qwen-plus \
  --max-rounds 8 --round-caps 5 10
```

Reports: `results/pilot/` or `results/real_timing/` (JSON + HTML).

## Reference import

```bash
python scripts/crawl_reference.py --sort rating_desc --max-pages 3
python scripts/import_reference_puzzles.py --replace --require-classic \
  --max-surface-chars 120 --max-solution-chars 200 --limit 10
```

See **`generator/README.md`** § R 支线.

## Git

| File | Commit? |
|------|---------|
| `.env.example`, `config.local.yaml.example` | ✅ |
| `.env`, `config.local.yaml`, `results/`, `data/trajectories/` | ❌ |

CI: `pytest -q` with `--mock`.
