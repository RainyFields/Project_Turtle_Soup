# turtle-soup-bench

**海龟汤双 Agent 推理系统** — 用 Oracle（汤主）与 Questioner（猜题者）评测大模型的主动提问能力（Active Question-Asking）。

| 项 | 说明 |
|----|------|
| 代号 | `turtle-soup-bench` |
| PRD | v0.1（2026-06-01） |
| 默认测试题 | `refsoup_006`（沙漠里的尸体） |
| Python | **3.10+**（推荐 3.11） |

---

## 功能概览

- **双 Agent 对局**：Questioner 仅见汤面；Oracle 持汤底，仅回答「是 / 不是 / 与此无关」
- **游戏引擎**：可配置最大轮数、最少提问轮数、token 预算、轨迹保存
- **评估**：启发式 / LLM-as-Judge / `composite_judge`（关键词 70 + 逻辑 30，满分 100）；
  轮数研究 Exp 1 / Exp 2（`run_pilot.py`）
- **批量评测**：`run_benchmark.py`；选题族 `all` / `turtle` / `refsoup`
- **题库生成（A→E）** + **参考汤导入（R）**：见 [`generator/README.md`](generator/README.md)
- **离线模式**：`--mock` 无需 API Key

---

## Quickstart

```bash
cd Project_Turtle_Soup
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/setup_env.py && python scripts/check_env.py
cp config.local.yaml.example config.local.yaml   # 可选
```

详见 **[CONTRIBUTING.md](CONTRIBUTING.md)**。

```bash
# 离线单局
python scripts/run_game.py --puzzle refsoup_006 --mock

# 真实模型
python scripts/run_game.py --puzzle refsoup_006

# 轮数评测 Pilot（Exp 1 + Exp 2）
python scripts/run_pilot.py --puzzles refsoup_006 --mock
# → results/pilot/<dir>/pilot_timing.json + pilot_timing.html

# 真实 API 单题计时
python scripts/run_real_timing.py --puzzle refsoup_006 --questioner-provider qwen --questioner-model qwen-plus

# 批量 benchmark
python scripts/run_benchmark.py --puzzles refsoup --questioner-models mock --mock

pytest -q
```

---

## 配置

| 角色 | 默认 Provider | 默认 Model |
|------|---------------|------------|
| Oracle | openai | gpt-4o |
| Questioner | anthropic | claude-opus-4-6 |

密钥：`.env`；模型覆盖：`config.local.yaml` 或 CLI。  
Provider：`openai` · `anthropic` · `deepseek` · `qwen` · `zai` · `gemini` · `openrouter` · `ollama` · `mock`  
Ollama 慢模型：`OLLAMA_TIMEOUT=600`（默认 600s）。推理模型（qwen3.5、deepseek-r1）设
`OLLAMA_THINK=0` 关闭思考，否则延迟涨约 100 倍。

> **换 Oracle / Questioner 前请先读 [AGENTS.md](AGENTS.md)「模型选型」** —— 有各模型的
> Oracle 准确率实测、推理模型空回复陷阱，以及交接用的最短上手路径。

---

## 项目结构

```text
turtle-soup-bench/
├── README.md · AGENTS.md · plan.md · CONTRIBUTING.md
├── docs/proposals/        # TurtleSoup-Creativity proposal v0.1
├── docs/plans/            # creativity toy experiment plan (M6)
├── data/puzzles/          # turtle_* + refsoup_*
├── agents/ · engine/ · evaluation/ · generator/ · scripts/ · tests/
```

---

## 题库

| 来源 | ID 前缀 | 说明 |
|------|---------|------|
| MVP + Generator（git） | `turtle_*` | 11 题（`005` + `010`–`015`） |
| 参考站导入（本地） | `refsoup_*` | 经典短汤，如 `refsoup_006` |

---

## 里程碑

| 阶段 | 状态 | 内容 |
|------|------|------|
| M0–M3 | ✅ | 框架、11 题、评测、测试 |
| Generator | ✅ | A→E + R 支线 |
| M4a | 🔶 | Pilot 可跑；全量 11×3×3 + 绘图未做 |
| M4b | 🔲 | benchmark CSV、async |
| M5 | 🔲 | 多 Questioner |
| M6 | 🔲 | TurtleSoup-Creativity toy 实验（见 `docs/plans/creativity-toy-experiment-plan.md`） |

---

## License

研究/内部项目（待补充）。
