# Evaluation Plan — Round-Curve & Round-Cap Studies

**Project**: `turtle-soup-bench`  
**Updated**: 2026-07-08  
**Status**: 题集与工具链就绪（22 道，标注 100%）；**全量网格未跑** —— 见「下一阶段」

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

**默认 pilot 题**：`refsoup_008`（沙漠里的尸体）。

> ⚠️ **本节以下的运行示例是历史记录，不要照抄。**它们用 `--mock` 或单题，
> 且写于题集重建之前。正式重跑请照「下一阶段 → 怎么跑」的四条命令。

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
python scripts/run_pilot.py --puzzles refsoup_008 --mock

# Ollama（已跑通 refsoup_008 + qwen2.5:7b，~270s）
python scripts/run_pilot.py --puzzles refsoup_008 \
  --max-rounds 12 --round-caps 5 10 12 \
  --questioner-provider ollama --questioner-model qwen2.5:7b \
  --oracle-provider ollama --oracle-model qwen2.5:7b \
  --output results/pilot/refsoup_008

# 真实 API 计时外推
python scripts/run_real_timing.py \
  --puzzle refsoup_008 \
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
    不给 provider 则只算关键词 70 分（满分 0.70）。
    ⚠️ **网格里 E1 和 E2 现已统一都开逻辑分** —— 否则两条曲线标度不同却被并排讨论
- [ ] 全量网格 —— 见「下一阶段 → 怎么跑」（22 道 × 模型 × seed）
- [ ] 可选：Exp 1 每 5 轮 checkpoint（降低 checkpoint 调用量）

---

# 论文 — IAB (Interpreting Agent Behavior) @ NeurIPS 2026

**目标**：4 页 workshop 论文，内容 = 本 plan 的实验体系 + 创意 proposal 的故事线。
**工作方式**：每完成一版草稿即提交给作者反馈，**收到反馈前不推进下一版**；
认为达到"好论文"标准即停。草稿在 `docs/paper/iab2026-draft.md`。

## 进度日志

| 版本 | 日期 | 内容 | 状态 |
|------|------|------|------|
| v0.1 | 2026-08-25 | 完整 4 页结构：故事线 = "失败模式在交互轨迹几何中可读"（H1 stalling / H2 drifting / H3 predictivity）；E1–E4 实验设计；pilot 观察作初步证据；12 篇参考文献全部逐一核验（每条带链接）；文末 5 个待作者决策的问题 | ✅ 已收到部分反馈 |
| v0.2 | 2026-08-26 | **全量 693 局跑完**（E1 99 + E2 594，零错误）。核心结果：① E1 三模型 checkpoint 准确率 30 轮全程平坦（27B≈0.20 ≥ 397B≈0.18 > 4B≈0.14）；② E2 大模型对预算不敏感（0.32–0.36），4B 随预算**单调退化**（cap15 0.23 → cap30 0.10，29/198 局 token 超限）；③ E3 几何解释平坦性且**随规模反转**：drift 斜率预测失败（pooled r=−0.28，27B −0.43），步长 4B ρ=−0.46 vs 397B +0.21；④ 提交行为分化（4B 0/33 从不提交，27B 9/33 @8.7 轮）。Figure 1 用真实 30 轮轨迹重做（4B late-step 0.003 停摆 vs 397B 0.16→0.02 探索收敛）。**PDF 已产出**（`docs/paper/iab2026.pdf`，tectonic XeLaTeX，5 页=4 正文+参考文献，中文正常）。Artifact 已更新至 v0.2 | ✅ 反馈已消化 |
| v0.3 | 2026-08-26 | 按作者反馈：① **摘要/引言改为平坦性结果先行**；② **混合效应分析已跑**（`scripts/mixed_effects_h3.py` → `h3_mixed_effects.json`）：puzzle 随机截距吸收 drift 信号（drift LRT p=0.28，stride×tier p=0.73，puzzle 方差 0.050）→ **H3 不成立**，论文改为主张"轨迹几何是解释性仪器而非结果预测器"（诚实呈报）；md/tex/PDF/artifact 四处同步 | ⏸ 等作者反馈 |

## 作者反馈（2026-09-03）

- ✅ **论文只保留最重要的结论与结果，不罗列测试/失败实验。**
  已按此裁剪草稿 §6（四条 → 两条，被裁两条的实质已由 §3.2/§3.3/附录覆盖）。
  重跑后回填 §5 时同样适用：报主结果与核心失败模式对比，
  pilot 数字、评分 bug、被否决的度量等留在 plan/AGENTS，不进论文。
- ✅ **Oracle/裁判可走 Tinker**（无 OpenRouter 余额时）：DeepSeek-V3.1 审计 95% 通过。

## 作者反馈（2026-08-26）

- ✅ 决策 2：**跑满 E1–E3**（Tinker 预算已批）
- ✅ 决策 5：**Figure 1 用 pilot 数据先做**
- ✅ 新要求：**最终交付 PDF**（本机已有 tectonic，走 LaTeX；官方 pdf skill 已装）
- ⏳ 决策 1（故事侧重）、3（中文联想 norms）、4（标题）仍待反馈

## 执行状态（2026-08-26）

- **Oracle 审计通过**：Tinker Qwen3.5-397B（thinking off），yes/no 探针 15/15=100%
  （`scripts/audit_oracle.py`，三条"与此无关"探针答"不是"，属软通过）
- **评分修复（跑全量前的关键 bug）**：句子式 key_clues 是连续中文串，token 匹配退化为
  精确子串 → 正确的意译答案得 0（实测 397B 解对 turtle_002 得 0.00）。已加
  **字符 bigram 召回 ≥0.5 兜底**（`_clue_matches_answer`），修复后正确答案 70/70、
  错误答案 0/70
- **E1/E2 全量已启动**（⚠️ 历史记录，该批数据已作废）：9 个并行 shard，11 puzzles；
  Questioner = Qwen3.5-4B / Qwen3.6-27B / Qwen3.5-397B-A17B；Oracle/judge = 397B；
  E1 clue-only checkpoint 评分，E2 composite + 397B 逻辑评分（2 samples）；
  输出 `results/full_20260826/`；`qa_rounds`（逐轮 Q/A 全文）已随报告落盘供 E3 用
- **E3 工具链**：`evaluation/trajectory.py`（jieba 关键词 → bge-small-zh 嵌入 →
  step size + 代理人类流形距离）+ `scripts/plot_figure1.py`；
  ⚠️ 流形目前是代理版（汤面/汤底/key_clues 词），SWOW 版待决策 3

---

# 下一阶段 — 重跑与待决事项

> 本节取代原「题库设计：深度 × 广度」计划。深度与广度**已合并为单一维度**并完成标注，
> 详见下文与 `AGENTS.md`「题目难度」。

## ⚠️ 首要：下一轮网格是完全重跑，不是增量

自上一轮 693 局以来有**三处同时变更**，任何一处都足以让新旧数字不可比：

| 变更 | 影响 |
|------|------|
| 题集 11 → 22 道已验证题 | **零重叠**。旧题里 6 道 LLM 生成（含 mock 占位符、三道近重复），2 道手工经典题已删 |
| Oracle / 裁判须换家族 | 旧网格中 Qwen3.5-397B 同时是 Questioner、Oracle 和裁判，「规模效应」与「与 Oracle 的相似度」分不开 |
| 锚点新增 `surface_only` | 旧锚点含汤底信息，换锚点后 drift 斜率在部分轨迹上符号翻转 |

**论文 §5 的每个数字都需重新建立，不能与新结果并排比较。**

## 需要人决定的只有两件事

其余都有可用的默认值，脚本会自己往下走。

1. **测哪些 Questioner。** 默认是 `Qwen3.5-4B / Qwen3.6-27B / Qwen3.5-397B-A17B`
   经 tinker 采样，三个 seed。换模型或缩小范围：
   `MODELS="a b" SEEDS="0" bash scripts/run_all_shards.sh <outdir>`
2. **预算。** 22 题 × 模型数 × seed 数，E1 每题 30 轮、每轮 3 次调用，
   E2 六个 cap 各一局。Oracle 与裁判默认走 OpenRouter（`z-ai/glm-5.3-flash`，$0），
   需要 OpenRouter key；**没有 key 时可全走 Tinker**：
   `ORACLE_PROVIDER=tinker ORACLE_MODEL=deepseek-ai/DeepSeek-V3.1`
   （2026-09-03 审计通过：yes/no 20/21 = 95%，跨家族），费用记入 $2k Tinker 额度。
   `run_full_grid.sh` 的守卫已从「不同 provider」改为「不同**模型家族**」，
   同一 tinker 账号下 Qwen Questioner + DeepSeek Oracle 是合法组合；
   `tinker://` checkpoint 无法从名字判家族，需显式 `QUESTIONER_FAMILY=...`。

**默认锚点用哪个不需要决定** —— `analyze_grid.py` 已改为**两个锚点都算**，
逐轮距离各存一份（`anchor_dists` 与 `surface_anchor_dists`）。
默认值仍是 `with_solution`，只影响单独调用 `trace_geometry` 时的行为。

**逻辑分是否保留也不需要现在决定** —— E1 与 E2 现已用**同一把尺**
（都开逻辑分，`LOGIC_SAMPLES` 可调）。此前 E1 只算关键词、满分 0.70，
而 E2 满分 1.00，两条曲线并排讨论时不可比。同尺之后，
在 E1 上对比「仅关键词」与「关键词+逻辑」的排序即可回答这个问题。

## 怎么跑

```bash
# 1. 预检：确认 token 预算对全部 22 道够用。
#    ⚠️ 探的是 **Questioner**（预算不足时它返回空内容，整局零轮结束），
#    所以要传实际要跑的 Questioner，不是 Oracle。默认值是 OpenRouter，没有 key 时必须改：
python scripts/check_puzzle_runnability.py \
  --provider tinker --model Qwen/Qwen3.5-4B

# 2. 审计 Oracle：≥90%，且必须与 Questioner 不同家族
python scripts/audit_oracle.py --provider openrouter --model z-ai/glm-5.3-flash

# 3. 跑完整网格（所有分片，可中断续跑）
bash scripts/run_all_shards.sh results/grid_2026_09

# 4. 分析
python scripts/analyze_grid.py --run results/grid_2026_09
```

`run_all_shards.sh` **跳过已完成的分片**，失败后重跑只补失败的那些；
单个分片失败不会中断其余；结束时列出需要重试的分片。
E1 失败则跳过该分片的 E2（否则会在坏数据上继续烧钱）。

`run_full_grid.sh` 已改为：题目列表运行时从 `family="real"` 取（不会漏题也不会
混入生成题）、Oracle 与裁判默认异构且同家族时**拒绝启动**、解释器用当前环境
（不再硬编码 `.venv/bin/python`）。`analyze_grid.py` 现在会保存**逐轮**
step 与 anchor 距离，而不只是均值 —— 否则核心图画不出来，跑完还得再跑一遍。

## 重跑时必须一次做到位（否则要再跑一遍）

- [ ] **两个锚点都算**（`surface_only` 与 `with_solution`），并排报告
- [ ] **保存逐轮步长与逐轮距离** —— 目前只存汇总量，论文核心图（步长/距离 vs 轮次）
      因此画不出来
- [ ] **`qa_rounds` 入库**（可压缩），否则任何人（含作者本人）都无法复核 E3
- [ ] **跑前做可跑性预检**：`python scripts/check_puzzle_runnability.py`。
      推理模型把 token 预算先花在思考上，预算不足时 Questioner 返回空内容、
      整局可能零轮结束；而空轮若不被识别会被当作正常轮记入曲线
- [ ] **Oracle 先审计**：`python scripts/audit_oracle.py --provider <p> --model <m>`，
      通过线 ≥90%，且**必须与 Questioner 不同家族**

## 待决事项

- [ ] **默认锚点用哪个。** 现为 `with_solution`（保持旧结果可复现），
      科学上 `surface_only` 更干净。建议改默认并让 `analyze_grid.py` 打印当前锚点。
      重跑时两个都算，故此决定只影响「未指定参数时用哪个」。
- [ ] **逻辑分那 30 分是否保留。** 线索加长后，同内容答案的评分噪声消失
      （0.35/0.117 → 0.60/0.60），说明逻辑分当初要补的洞很大一块是线索质量。
      单题实测两种评分排序完全一致（ρ=1.000）。需在更多题上复测再定。
- [ ] **记忆混淆检验。** 欠定度最低的两道恰是流传最广的两道，可能在测熟悉度而非难度。
      记忆探针（不给汤面直接问答案）即可区分，22 次调用。
- [ ] **难度标注的人工复核**（8–10 道报 agreement）—— LLM 标注，投稿时会被问效度来源。
- [ ] 若接 SWOW-zh 做人类锚点：先验证覆盖率，`热气球` `抽签` 未必是 SWOW cue。

## 已完成（勿重做）

| 项 | 结论 |
|----|------|
| 题集重建 | 22 道，全部有人类游玩记录，来源隔离由代码强制并有回归测试 |
| 难度度量 | **欠定度**，22/22 标注完成，范围 0.173–0.577。**与汤面长度无关**（r=−0.22, n.s.），可作题目层协变量 |
| 深度 × 广度 | **已合并为欠定度**。分开测时两者都撞天花板，且本身不独立 |
| Oracle 选型 | 四模型实测在案；准确率不是正确度量，应报互信息 |
| 锚点问题 | 代码支持三种锚点；论文措辞已改为实际做法 |

**已否决的做法**（勿重走）：汤面–汤底单点 embedding 距离（ρ=−0.005，把最浅的题判成最深）；
依次加 key_clues 看落差（距离不单调）；深度 1–5 绝对打分（全打 4 分）；
候选去重计数（恒为满值）；悬置细节计数（值域被汤面长度锁死）。

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

（历史估算，题集已变）全量 11×3×3 的 Questioner 侧 token 粗算：Exp2 594 games（~18 轮/game，历史随轮增长）
≈ 12.5M prefill + 思考型输出 ~11M sample；Exp1 99 games（30 轮 × 3 调用）≈ 8M + 6M。
合计 ~20M prefill + ~17M sample →
**Qwen3.5-397B 全量约 $190，Kimi-K2.6 约 $140**；就算思考 token 放大 5 倍也 <$700。
**结论：$2k 足够在最大档位模型上跑数遍全量。**

注意：
1. ~~需新增 tinker_provider~~ **已接入**：`--questioner-provider tinker`，
   支持 base model 名和 `tinker://` 训练 checkpoint（用法见 AGENTS.md Tinker 节）。
2. 纯推理 OpenRouter 已接好且同类开源模型往往更便宜；Tinker 预算的**独特价值在 train 档**
   （LoRA 微调/RL 训练 Questioner，composite score 可直接作 reward）。建议推理基准走
   OpenRouter/qwen，Tinker 额度留给训练实验。

---

## 开放问题

1. Judge：heuristic vs gpt-4o
2. Oracle 是否注入 `qa_history`
3. 数据集：`refsoup_*` 作 easy baseline vs 仅 `turtle_*` 11 题
