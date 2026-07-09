# Evaluation Plan — Round-Curve & Round-Cap Studies

**Project**: `turtle-soup-bench`  
**Updated**: 2026-07-08  
**Status**: Pilot **可跑**（`run_pilot.py`）；全量 11×3×3 **未跑**

---

## Goals

| Study | Question | X-axis | Y-axis |
|-------|----------|--------|--------|
| **Exp 1** | 对话变长后准确率是否提升？ | Round \(1 \ldots 30\) | Checkpoint accuracy |
| **Exp 2** | 固定轮数预算下表现如何？ | Cap \(\{5,10,15,20,25,30\}\) | End accuracy |

Oracle 固定；Questioner 为对比变量。

---

## Setup

| Role | Planned | Notes |
|------|---------|-------|
| Oracle | `gpt-4o` | 正式研究 |
| Judge | `gpt-4o` LLM | **当前 pilot 用 `heuristic_judge`** |
| Questioner | deepseek-r1 / qwq-32b / llama3.3:70b | 或本地 Ollama |

**默认 pilot 题**：`refsoup_006`（经典、难度适中）。

**输出**：`results/pilot/<dir>/pilot_timing.json` + `pilot_timing.html`

---

## 已实现

- `engine/game.py`：`force_final_answer_on_max_rounds`、`format_qa_history`
- `evaluation/round_studies.py`：`run_round_curve`、`run_round_cap`、`run_pilot`
- `scripts/run_pilot.py`、`scripts/run_real_timing.py`
- `evaluation/study_report_html.py`、`evaluation/api_timing.py`
- Providers：qwen / zai / gemini / ollama / mock

---

## 运行示例

```bash
# Mock 管线验证
python scripts/run_pilot.py --puzzles refsoup_006 --mock

# Ollama（已跑通 refsoup_006 + qwen2.5:7b，~270s）
python scripts/run_pilot.py --puzzles refsoup_006 \
  --max-rounds 12 --round-caps 5 10 12 \
  --questioner-provider ollama --questioner-model qwen2.5:7b \
  --oracle-provider ollama --oracle-model qwen2.5:7b \
  --output results/pilot/refsoup_006

# 真实 API 计时外推
python scripts/run_real_timing.py \
  --puzzle refsoup_006 \
  --questioner-provider qwen --questioner-model qwen-plus \
  --max-rounds 8 --round-caps 5 10
```

---

## 待做

- [ ] 独立 CLI：`run_round_curve.py`、`run_round_cap_sweep.py`
- [ ] `evaluation/plot_round_studies.py`
- [ ] 全量：11 puzzles × 3 models × 3 seeds
- [ ] 可选：pilot 切换 LLM judge；Exp 1 每 5 轮 checkpoint

---

## 成本粗算

| 项 | 估计 |
|----|------|
| 全量 Exp 1 | 99 games + checkpoint calls |
| 全量 Exp 2 | 594 games |
| 单题 pilot（12 轮 + 3 caps，Ollama） | ~93 calls，~270s |

@ 12s/call 规划：全量合计约 **31h** API 时间。

---

## 开放问题

1. Judge：heuristic vs gpt-4o
2. Oracle 是否注入 `qa_history`
3. 数据集：`refsoup_*` 作 easy baseline vs 仅 `turtle_*` 11 题
