# Agent Guide — turtle-soup-bench

本文件供 Cursor Agent **持久记忆**使用。新开对话请先读本文、`plan.md`、`generator/README.md`、`.cursor/rules/turtle-soup-bench.mdc`。

## 项目目标

海龟汤双 Agent 评测：Oracle 三值回答；Questioner 仅见汤面提问，最终 `FINAL_ANSWER:`。

## 架构

| 路径 | 职责 |
|------|------|
| `agents/` | Oracle / Questioner + providers（openai, qwen, zai, gemini, ollama, mock…） |
| `engine/game.py` | `TurtleSoupGame`；`list_puzzle_ids(family=)` |
| `evaluation/round_studies.py` | Exp 1 曲线 + Exp 2 cap |
| `evaluation/study_report_html.py` | pilot JSON → HTML |
| `scripts/run_game.py` | 单局 |
| `scripts/run_pilot.py` | Exp 1+2 pilot |
| `scripts/run_benchmark.py` | 批量；`--puzzles refsoup` |
| `generator/` | A→E 生成 + R 支线 `refsoup_*` 导入 |

## 数据集

| 来源 | IDs |
|------|-----|
| git 发布 | `turtle_*` 11 题 |
| 本地导入 | `refsoup_001`…（`import_reference_puzzles.py`） |

`data/reference/`、`data/generator/`、`results/`、`data/trajectories/` 已 gitignore。

### 参考汤（R 支线）

```bash
python scripts/import_reference_puzzles.py --replace --require-classic \
  --max-surface-chars 120 --max-solution-chars 200 --limit 10
python scripts/refresh_reference_key_clues.py
```

`key_clues`：`generator/reference/key_clues.py`（词典匹配 + 过滤汤面重复词）。

## 评测（`plan.md`）

- **Exp 1**：每轮 checkpoint → `heuristic_judge`
- **Exp 2**：round cap + 强制 `FINAL_ANSWER`
- Pilot 示例：

```bash
python scripts/run_pilot.py --puzzles refsoup_006 \
  --max-rounds 12 --round-caps 5 10 12 \
  --questioner-provider ollama --questioner-model qwen2.5:7b \
  --oracle-provider ollama --oracle-model qwen2.5:7b \
  --output results/pilot/refsoup_006
```

报告：`pilot_timing.json` + `pilot_timing.html`。正式全量研究前可切换 LLM judge。

## API Key

见 **`CONTRIBUTING.md`**。勿在聊天中索要 key。

```bash
python scripts/setup_env.py && python scripts/check_env.py
python scripts/run_game.py --puzzle refsoup_006 --mock
```

Ollama：`OLLAMA_TIMEOUT`（默认 600）。Z.AI Coding Plan：`ZAI_USE_CODING_ENDPOINT=1`。

## 关键约定

- **默认测试题**：`refsoup_006`
- 离线：`--mock`；测试：`pytest -q`（34 tests）
- Questioner 每轮收到完整 `qa_history`；Oracle 仅当前问题
- `forbidden_reveal` 仅 D 层 filter，运行时未注入 Oracle

## 常用命令

```bash
python scripts/run_game.py --puzzle refsoup_006 --mock
python scripts/run_pilot.py --puzzles refsoup_006 --mock
python scripts/run_benchmark.py --puzzles refsoup --questioner-models mock --mock
pytest -q
```

## 待办

1. 全量 Exp 1/2（11×3×3）+ `plot_round_studies.py`
2. benchmark CSV / async（M4b）
3. 可选：Oracle 注入历史；pilot 切换 LLM judge

## 开放问题

- Exp 1 checkpoint 每 5 轮采样降成本
- key_clues 与 LLM judge 对齐
