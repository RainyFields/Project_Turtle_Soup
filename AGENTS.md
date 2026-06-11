# Agent Guide — turtle-soup-bench

本文件供 Cursor Agent **持久记忆**使用。用户新开对话时，请先阅读本文件、**`plan.md`**（评测计划）与 `.cursor/rules/turtle-soup-bench.mdc`。

## 项目目标

构建可复现的海龟汤双 Agent 框架：Oracle 持汤底回答三值；Questioner 仅见汤面主动提问，最终提交 `FINAL_ANSWER:`。

## 架构（已实现）

| 路径 | 职责 |
|------|------|
| `agents/oracle_agent.py` | 汤主，输出 clamp 到 是/不是/与此无关 |
| `agents/questioner_agent.py` | 猜题者，提问或 FINAL_ANSWER |
| `agents/provider_factory.py` | openai / anthropic / deepseek / qwen / zai / gemini / ollama / mock |
| `engine/game.py` | `TurtleSoupGame` 主循环 |
| `engine/trajectory.py` | 轨迹 JSON |
| `evaluation/` | metrics + heuristic/LLM judge |
| `scripts/run_game.py` | 单局 CLI |
| `scripts/run_benchmark.py` | 批量评测（单次 max_rounds） |

## 数据集（本地）

| 来源 | IDs | 数量 |
|------|-----|------|
| MVP 手工题 | `turtle_001`–`005` | 5 |
| Generator 审核发布 | `turtle_010`–`015` | 6 |
| **已发布合计** | | **11** |
| **候选 staging** | `data/generator/staging/<batch>/` | 见最新 batch |

`data/reference/`、`data/generator/` 本地 gitignore，不进 git。

### Generator 管线（A→E，已合并到 main）

```bash
python scripts/crawl_reference.py --max-pages 2 --sort rating_desc   # A
python scripts/analyze_reference.py                                   # B
python scripts/generate_puzzles.py --batch jun11_v1 --count 8 --mock  # C（无 key 用 mock）
python scripts/filter_candidates.py --batch jun11_v1                    # D
python scripts/review_ui.py                                             # E 人工审核
```

最新 batch：`jun11_v1` — 8 候选，filter 全部 PASS。发布需 review UI 或 `publish_puzzle.py`。

## 评测计划（当前优先级）

详见 **`plan.md`**。两项研究（均未跑完，脚本待实现）：

### Exp 1 — 准确率 vs 对话轮数（无进度压力）

- **X**：轮次 \(1 \ldots 30\)
- **Y**：该轮 checkpoint 的 judge 准确率（均值）
- **线**：3 个开源推理 Questioner（`deepseek-reasoner`, `qwq-32b`, `llama3.3:70b`）
- **设定**：`min_rounds_before_answer=0`，不强迫多问；自然对局 + 每轮 checkpoint 评估
- **Oracle / Judge**：固定 `gpt-4o`

### Exp 2 — 固定轮数预算下的最终表现

- **X**：最大轮数 \(\{5, 10, 15, 20, 25, 30\}\)
- **Y**：该局结束时的 judge 准确率
- **设定**：到 cap 未作答则强制 `FINAL_ANSWER`
- **模型**：同 Exp 1

### Pilot（2026-06-11）

```bash
python scripts/run_pilot.py --puzzles turtle_001 turtle_002   # mock 管线验证 + 计时
```

- 报告：`results/pilot/<timestamp>/pilot_timing.json`
- Mock 2 题 ~0.015s；**勿用 mock 秒数外推真实耗时**

**真实 API 计时（Qwen 等）：**

```bash
cp .env.example .env   # 填写 QWEN_API_KEY
python scripts/run_real_timing.py --puzzle turtle_001 --questioner-model qwen-plus --max-rounds 8
```

- 报告：`results/real_timing/<timestamp>/real_timing.json`
- 用**实测 mean sec/call** 外推全量（非 mock 墙钟）

### 待实现

- `scripts/run_round_curve.py` / `run_round_cap_sweep.py`（独立 CLI）
- `evaluation/plot_round_studies.py`
- 真实模型 3×11×3 全量跑

## API Key 配置（每位开发者本地完成）

> 完整说明见 **`CONTRIBUTING.md`**。Agent **不要**要求用户在聊天中粘贴 key；只引导其在本地 `.env` 配置。

### 安全规则

- **禁止**在 Cursor 聊天、GitHub PR/issue、Slack 中发送 API key
- **禁止**把 key 写入 `config.yaml` 或提交到 git
- `.env`、`config.local.yaml` 已 gitignore — **每人一份**，协作者互不影响

### 首次配置（推荐流程）

```bash
# 1) 安装依赖后，交互式写入 .env（输入不回显）
python scripts/setup_env.py

# 2) 检查哪些 provider 已就绪（不打印密钥）
python scripts/check_env.py

# 3) 可选：个人默认模型（不进 git）
cp config.local.yaml.example config.local.yaml
# 编辑 provider / model，须与 .env 里已配置的 key 对应

# 4) 无 key 时先验证管线
python scripts/run_game.py --puzzle turtle_001 --mock
```

也可手动：`cp .env.example .env`，只填写**自己会用的** provider 对应变量。

### 支持的 Provider

| Provider | `.env` 变量 | CLI `--questioner-provider` | 示例 model |
|----------|-------------|-------------------------------|------------|
| OpenAI | `OPENAI_API_KEY` | `openai` | `gpt-4o` |
| Anthropic | `ANTHROPIC_API_KEY` | `anthropic` | `claude-sonnet-4-6` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek` | `deepseek-reasoner` |
| Qwen | `QWEN_API_KEY` | `qwen` | `qwen-plus` |
| **Z.AI / GLM** | `ZAI_API_KEY` | `zai` | `glm-4.7` |
| Gemini | `GEMINI_API_KEY` | `gemini` | `gemini-2.0-flash` |
| Ollama | `OLLAMA_BASE_URL` | `ollama` | `llama3.3:70b` |
| 离线 | *(无)* | `mock` 或 `--mock` | `mock` |

- **密钥** → 仅 `.env`
- **模型默认** → `config.local.yaml`（覆盖 `config.yaml`）或 CLI `--oracle-provider` / `--questioner-model`

### Z.AI / GLM（Coding Plan 用户必读）

实测：仅 **GLM Coding Plan** 月订时，通用 API 可能返回 `429 Insufficient balance`；Coding 端点可用。

在 `.env` 中：

```bash
ZAI_API_KEY=...                    # 仅本地填写，勿提交
ZAI_USE_CODING_ENDPOINT=1          # Coding Plan 用户设为 1
# ZAI_BASE_URL=https://api.z.ai/api/paas/v4   # 默认通用端点；Coding 时由上面开关切换
```

`config.local.yaml` 示例：

```yaml
oracle:
  provider: zai
  model: glm-4.7
questioner:
  provider: zai
  model: glm-4.7
```

验证与试跑：

```bash
python scripts/check_env.py          # 应显示 [✓] zai / glm
python scripts/run_game.py --puzzle turtle_001 --max-rounds 8 \
  --questioner-provider zai --questioner-model glm-4.7 \
  --oracle-provider zai --oracle-model glm-4.7

python scripts/run_real_timing.py \  # 单题真实耗时外推
  --questioner-provider zai --questioner-model glm-4.7 \
  --puzzle turtle_001 --max-rounds 8 --round-caps 5 10
```

报告：`results/real_timing/<timestamp>/real_timing.json`（用实测 `mean_s/call` 外推，勿用 mock 墙钟）。

### Agent 协助用户时的检查清单

1. 是否已有 `.env`？→ 建议 `setup_env.py` / `check_env.py`
2. 是否要用真实 API？→ 确认对应 env 变量为 `[✓]`
3. Z.AI 报 429？→ 提示加 `ZAI_USE_CODING_ENDPOINT=1` 或充值通用 API
4. 协作者？→ 各自 `.env` + `config.local.yaml`，或 `--mock`

## 关键约定

- 默认测试题：`data/puzzles/turtle_001.json`
- 全量评测：`--puzzles all`（11 题）
- 离线开发：一律加 `--mock`
- 轨迹 / 结果：`data/trajectories/`、`results/`（gitignore）
- Python 3.10+；改代码保持最小 diff；测试用 `pytest -q`

## 常用命令

```bash
python scripts/run_game.py --puzzle turtle_001 --mock
python scripts/run_benchmark.py --puzzles all --questioner-models gpt-4o --mock --output results/
pytest -q
```

## 待办（优先级）

1. **评测 M4a**：按 `plan.md` 实现 Exp 1 / Exp 2 脚本与绘图
2. **Provider**：从 feature 分支合并 `qwen_provider`（QwQ-32B）
3. **Pilot**：2 题 × 1 模型验证后再跑 11 题 × 3 模型 × 3 seeds
4. **benchmark 报告**：CSV 汇总、async 并发（可选）
5. **Phase 2**：多 Questioner 协作

## 开放问题

- Exp 1 每轮 checkpoint 是否改为每 5 轮（降 API 成本）— 见 `plan.md`
- Oracle 是否改用开源模型以保持全栈开源
- key_clues 与 judge 对齐；难度分级标准

## 负责人

Xiaoxuan — 2026-06-01 初始化（M0–M3）；2026-06-11 扩充题库至 11 题 + 轮数评测计划
