# turtle-soup-bench

**海龟汤双 Agent 推理系统** — 用 Oracle（汤主）与 Questioner（猜题者）评测大模型的主动提问能力（Active Question-Asking）。

| 项 | 说明 |
|----|------|
| 代号 | `turtle-soup-bench` |
| PRD | v0.1（2026-06-01） |
| 默认测试题 | `turtle_001`（餐厅里的男人） |
| Python | **3.10+**（推荐 3.11） |

---

## 功能概览

- **双 Agent 对局**：Questioner 仅见汤面；Oracle 持汤底，仅回答「是 / 不是 / 与此无关」
- **游戏引擎**：可配置最大轮数、最少提问轮数、token 预算、轨迹保存
- **评估**：启发式 + 可选 LLM-as-Judge；自动指标（覆盖率、效率、多样性等）
- **批量评测**：`run_benchmark.py` 多题 × 多模型组合
- **离线模式**：`--mock` 无需 API Key（CI / 本地开发）

---

## Quickstart

```bash
cd Project_Turtle_Soup
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 每位开发者用自己的 API Key（勿提交 .env，勿在聊天里发送 key）
python scripts/setup_env.py
python scripts/check_env.py

# 可选：个人默认模型（gitignore）
cp config.local.yaml.example config.local.yaml
```

详见 **[CONTRIBUTING.md](CONTRIBUTING.md)**（协作者必读）。

**离线单局（推荐首次验证）：**

```bash
python scripts/run_game.py --puzzle turtle_001 --mock
```

**真实模型：**

```bash
python scripts/run_game.py --puzzle turtle_001
```

**批量 benchmark：**

```bash
python scripts/run_benchmark.py \
  --puzzles all \
  --questioner-models claude-opus-4-6 gpt-4o deepseek-v3 \
  --oracle-model gpt-4o \
  --runs-per-combo 3 \
  --output results/benchmark_v1/
```

**查看轨迹：**

```bash
python scripts/visualize_trajectory.py data/trajectories/game_*.json
```

**测试：**

```bash
pytest -q
```

---

## 配置

`config.yaml` 默认：

| 角色 | Provider | Model |
|------|----------|-------|
| Oracle | openai | gpt-4o |
| Questioner | anthropic | claude-opus-4-6 |

密钥在 **`.env`**（每人一份）；模型默认可在 **`config.local.yaml`** 覆盖。  
支持：`openai` · `anthropic` · `deepseek` · `qwen` · **`zai` (GLM)** · `gemini` · `ollama` · `mock`

---

## 项目结构

```text
turtle-soup-bench/
├── README.md
├── AGENTS.md                 # Cursor Agent 工作指引（含项目记忆）
├── config.yaml
├── requirements.txt
├── .env.example
├── data/
│   ├── puzzles/              # turtle_001 … turtle_005
│   └── trajectories/         # 对局 JSON（gitignored）
├── agents/                   # Oracle / Questioner + providers
├── engine/                   # 游戏循环、轨迹
├── evaluation/               # 指标、judge、报告
├── scripts/                  # CLI
└── tests/
```

---

## 里程碑（PRD）

| 阶段 | 状态 | 内容 |
|------|------|------|
| M0 | ✅ | Repo、README、基础结构 |
| M1 | ✅ | `data/` 五道题 |
| M2 | ✅ | `agents/` + `engine/`，单局可跑 |
| M3 | ✅ | `evaluation/` 启发式 + LLM judge |
| M4 | 🔲 | benchmark 报告增强、async |
| M5 | 🔲 | 多 Questioner 协作（Phase 2） |

---

## 在 Cursor 中继续开发

打开本项目后，Agent 会自动加载 **`.cursor/rules/`** 与 **`AGENTS.md`** 中的项目记忆。  
新开对话时可以说：

> Continue turtle-soup-bench — 查看 AGENTS.md 与当前里程碑。

---

## License

研究/内部项目（待补充）。
