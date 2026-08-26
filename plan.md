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

## 待做（当前阶段）

- [x] 独立 CLI：`run_round_curve.py`、`run_round_cap_sweep.py`（支持 `--seeds`、`--judge composite`、`--mock`）
- [x] `evaluation/plot_round_studies.py`（吃 `pilot_timing.json` / 两个新 CLI 的 JSON，出 PNG）
- [x] 把 `composite_judge` 接进 `run_game.py` / `round_studies.py`
  - `run_game.py --composite-judge [--logic-samples N]`；judge provider/model 复用现有 flag
  - `round_studies.py` 走 `JudgeSpec(mode="composite", provider=..., model=...)`；
    不给 provider 则只算关键词 70 分（Exp 1 checkpoint 逐轮打分时可保持零额外调用）
- [ ] 全量：11 puzzles × 3 models × 3 seeds
- [ ] 可选：Exp 1 每 5 轮 checkpoint（降低 checkpoint 调用量）

---

# 下一阶段 — 题库设计 + 联想轨迹评测

> 现状：只跑过 `refsoup_*` 这类**经典短汤**（单解、线性推理）。
> `generator/` 的 A→E 管线已可用但只产出同类题。下面两件事是方向性的，不是零散待办。

## A. Benchmark 汤面汤底设计：深度 × 广度

现有题库在两个维度上都不够：

| 维度 | 目标 | 现状 |
|------|------|------|
| **深度** | 设计**刁钻问题**题库 —— 朴素提问路径走不通，必须做非平凡的假设跳跃 | 反面例子：`refsoup_006` 被 ox-alpha 5 轮线性推到底 |
| **广度** | 一个汤面**允许多个成立的解答** —— 考察 Agent 能否发现「不止一个答案」并区分 | 反面例子：全部题目单解，Oracle 照单一汤底判是非 |

### 广度的代码阻塞（不是加字段就行）

`solution` 目前是**单个字符串**，整条链路都按单解假设写死：

| 位置 | 需要改什么 |
|------|-----------|
| `generator/schema.py` | `REQUIRED_TOP_LEVEL` 含 `solution: str`；需扩成多解结构并保持向后兼容 |
| `agents/oracle_agent.py` | `ORACLE_SYSTEM_TEMPLATE` 只注入一个 `solution`；多解下「是/不是」的判定规则需重新定义 |
| `evaluation/judge.py` | `composite_judge` 需按**最佳匹配解**打分，而非固定解 |
| `key_clues` | 需按解分组，否则关键词那 70 分会跨解混算 |

**待决**：多解时 Oracle 对「某一解成立、另一解不成立」的问题该答什么？这决定了整套 schema 怎么设计。

### 深度的抓手

`generator/create/controllers.py` 目前只按 B 层统计抽样 category/difficulty，没有「刁钻度」控制维度。
需要给 Layer C 增加可控的难度机制，并用 Layer D 自动筛掉朴素可解的候选
（例如：用一个强 Questioner 试解，N 轮内被解出的候选判为深度不足）。

## B. Exp 3 — 联想轨迹（Association Trajectory）

**核心想法**：把「人类词义词表」和「前后轮关键词」放进同一个 hidden space 量距离，
刻画 Agent **基于汤面的联想 trajectory**。

| 量 | 含义 |
|----|------|
| 前后轮关键词之间的距离 | Agent 每轮的**移动步长与方向** |
| 每轮关键词 → 人类词表的距离 | 偏离**人类联想路径**的程度 |

这能区分现有指标分不开的两种失败：

1. **原地打转** —— 步长趋近 0。已在实测中观测到：qwen3.5:4b 后期逐字重复提问。
2. **系统性走偏** —— 步长正常但持续远离人类词表。

> 现有的 `question_novelty` / `new_vocab_ratio`（`evaluation/metrics.py`）是这件事的
> **词面近似版**：字符 bigram 判断有无新词。它抓得住第 1 种失败，抓不住第 2 种
> （换一批同义词重问同一件事会被判为「新」）。Exp 3 是它的语义版。

### 前置条件

- **需要 embedding 能力**：现有 provider 全是 chat 接口（`BaseProvider.generate`），
  没有 embeddings。需新增接口或独立的 embedding provider。
- **需要人类词义词表**：每题一份人工标注的联想词。
  ⚠️ `generator/reference/key_clues.py` 里的 `_ZH_WORDS` **不能拿来用** ——
  那是为特定几道题硬编码的匹配词典，不是人类联想数据。
- **需要逐轮关键词抽取**：目前只有对最终答案的 `key_clues` 匹配，没有对每轮提问的抽取。

---

## 成本粗算

| 项 | 估计 |
|----|------|
| 全量 Exp 1 | 99 games + checkpoint calls |
| 全量 Exp 2 | 594 games |
| 单题 pilot（12 轮 + 3 caps，Ollama） | ~93 calls，~270s |

@ 12s/call 规划：全量合计约 **31h** API 时间。

### Tinker（$2k 预算）可行性 — 2026-08-25

Tinker 支持对开源大模型直接采样推理（SamplingClient），按 token 计费
（prefill / sample / train 三档，cached prefill 打 2 折）。代表性价格（$/M tokens，prefill/sample）：
Qwen3.5-397B-A17B $3.00/$7.50，Kimi-K2.6 $2.21/$5.49，DeepSeek-V3.1 $1.70/$4.22，
GPT-OSS-120B $0.33/$0.84。

全量 11×3×3 的 Questioner 侧 token 粗算：Exp2 594 games（~18 轮/game，历史随轮增长）
≈ 12.5M prefill + 思考型输出 ~11M sample；Exp1 99 games（30 轮 × 3 调用）≈ 8M + 6M。
合计 ~20M prefill + ~17M sample →
**Qwen3.5-397B 全量约 $190，Kimi-K2.6 约 $140**；就算思考 token 放大 5 倍也 <$700。
**结论：$2k 足够在最大档位模型上跑数遍全量。**

注意：
1. Tinker 是 SDK 接口（非 OpenAI 兼容 REST），需新增 `agents/model_providers/tinker_provider.py`
   （参照 `openrouter_provider.py`，实现 `BaseProvider.generate` → SamplingClient）。
2. 纯推理 OpenRouter 已接好且同类开源模型往往更便宜；Tinker 预算的**独特价值在 train 档**
   （LoRA 微调/RL 训练 Questioner，composite score 可直接作 reward）。建议推理基准走
   OpenRouter/qwen，Tinker 额度留给训练实验。

---

## 开放问题

1. Judge：heuristic vs gpt-4o
2. Oracle 是否注入 `qa_history`
3. 数据集：`refsoup_*` 作 easy baseline vs 仅 `turtle_*` 11 题
