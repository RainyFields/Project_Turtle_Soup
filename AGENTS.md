# Agent Guide — turtle-soup-bench

本文件供 Cursor Agent **持久记忆**使用。新开对话请先读本文、`plan.md`、`generator/README.md`、`.cursor/rules/turtle-soup-bench.mdc`。

## 项目目标

海龟汤双 Agent 评测：Oracle 三值回答；Questioner 仅见汤面提问，最终 `FINAL_ANSWER:`。

## 架构

| 路径 | 职责 |
|------|------|
| `agents/` | Oracle / Questioner + providers（openai, anthropic, deepseek, qwen, zai, gemini, **openrouter**, **tinker**, ollama, mock） |
| `engine/game.py` | `TurtleSoupGame`；`list_puzzle_ids(family=)` |
| `evaluation/round_studies.py` | Exp 1 曲线 + Exp 2 cap |
| `evaluation/judge.py` | `heuristic_judge`、`LLMJudge`、**`composite_judge`（70+30）** |
| `evaluation/metrics.py` | 含 **`question_novelty` / `new_vocab_ratio`**（退化检测） |
| `evaluation/study_report_html.py` | pilot JSON → HTML |
| `scripts/run_game.py` | 单局 |
| `scripts/run_pilot.py` | Exp 1+2 pilot |
| `scripts/run_benchmark.py` | 批量；`--puzzles refsoup` |
| `generator/` | A→E 生成 + R 支线 `refsoup_*` 导入 |

## 数据集

**按来源隔离，见 `data/puzzles/README.md`：**

| 目录 | 内容 | 实验可用 |
|------|------|---------|
| `real/` | **22 题**，全部来自 soup.ahelumos.com 且带 `reference_url` | ✅ |
| `generated/` | LLM 生成 + 团队自撰 9 题 | ❌ |

题库经两轮人工审核定稿：站点「经典」标签 27 题 → 删 11 → 补 10（站点经典题已用尽）→ 删 1 → 删 4（难度无法标注）。构成为 12 题 classic 标签，其余为 horror/comedy/original/everyday/mystery。

```
汤面  中位 35 字   范围 9–108
汤底  中位 102 字  范围 13–279     ← 全部题目在 4096 token 预算下安全
线索  共 97 条，全部 ≥5 字
```

**编号已重排**：旧 `refsoup_006`（沙漠里的尸体）现为 **`refsoup_008`**。

取题一律用 `list_puzzle_ids(family="real")`；`"all"` / `"turtle"` / `"refsoup"` 会跨目录。
`key_clues` 由 `scripts/refresh_key_clues_llm.py` 用 LLM 统一抽取。旧的词典抽取器
（`generator/reference/key_clues.py`）**只对最早 10 题有效**，在其他题上退化成机械切分，
产出句中碎片和空泛词 —— 那会让 composite_judge 的 70 分在给噪声打分。
新抽取器要求每条线索是因果环节、不出现在汤面、且扎根于汤底用词。

站点数据有三类格式损坏（汤面被截断成占位符而真汤面塞在汤底里、抓取噪声、作者前言），
用 `scripts/clean_reference_surfaces.py` 修复，幂等且带 `--dry-run`。

`data/reference/`、`data/generator/`、`results/`、`data/trajectories/` 已 gitignore。

### 参考汤（R 支线）

```bash
python scripts/import_reference_puzzles.py --replace --require-classic \
  --max-surface-chars 120 --max-solution-chars 200 --limit 10
python scripts/refresh_reference_key_clues.py
```

`key_clues`：`generator/reference/key_clues.py`（词典匹配 + 过滤汤面重复词）。

## ⚠️ 跑实验前的两条硬规则

**规则 1：Oracle 与逻辑裁判必须来自与 Questioner 不同的模型家族。**

不只是"准确率要够"。Oracle 和 Questioner 同家族时，两者共享训练数据、分词器与表述
习惯，同家族的提问更容易被"听懂"，而这份优势不会平等地给到别家族的模型。当网格
比较的是同一家族的不同规模时（如 4B / 27B / 397B），其中一个恰好与 Oracle 同款，
**「规模效应」就和「与 Oracle 的相似度」绑死了，无法分离**。逻辑裁判同理，且风险更大 ——
那是模型给自己的答案打分。

> 已知问题：2026-08 的 693 局网格中，`Qwen3.5-397B-A17B` 同时担任 Questioner、
> Oracle 和逻辑裁判。重跑时必须换掉。当前可用的异构 Oracle 是
> `openrouter` / `z-ai/glm-5.3-flash`（ZAI 家族，实测 90%）。
> 注意 `qwen-flash` 虽然准确率也是 90%，但**仍属 Qwen 家族，对 Qwen Questioner 不适用**。

**规则 2：Oracle 先审计再跑，不合格不开始。**

```bash
python scripts/audit_oracle.py --provider openrouter --model z-ai/glm-5.3-flash
```

通过线 ≥90%（yes/no 项）。脚本退出码非 0 即未通过。探针题目取自当前题库，
若题库变动导致探针题缺失，脚本会提示并跳过而不是崩溃。

**报准确率不够，要报互信息 `I(Y;Ŷ)`。** 弱 Oracle 的错误会全部塌陷成「与此无关」——
零信息回答。实测 30% 的 Oracle 在 30 轮只传 8.4 bits，而在 |Z|≈1000 的假设空间里
识别正解需约 10 bits：**理想 Questioner 也解不出**，此时的 0 分测的是环境不是模型。
注意准确率 70% 与 90% 的两个 Oracle 互信息完全相同 —— 准确率连排序都不对。

## 模型选型（2026-08 实测，`refsoup_008` 10 题探针）

**Oracle 是基准真值的来源，必须强。** 弱 Oracle 会把答不出的问题全塌陷成「与此无关」，
Questioner 拿不到任何反馈，整题在信息论意义上无解 —— 此时的全 0 分测的是 Oracle 坏掉，
**不是** Questioner 弱。实测已验证：Oracle 从 30% 提到 100%，4B Questioner 的成绩一分未变。

| Oracle | 准确率 | 每次调用 | 备注 |
|--------|--------|----------|------|
| ollama `qwen3.5:4b`，thinking off | 30% | 0.7s | 不可用作 Oracle |
| ollama `qwen3.5:4b`，thinking on | 70% | 136s | 仍有 3/10 错 |
| qwen `qwen-flash` | 90% | 0.46s | 免费额度内可用 |
| openrouter `z-ai/glm-5.3-flash` | **100%** | ~5s | $0，但有共享池限流 |

`qwen-plus` / `qwen-turbo` 已被 **403 free quota exhausted** 挡住（需在阿里云控制台补付款信息
或关闭「仅免费额度」模式）。

### 推理模型的两个坑（换模型时必看）

1. **思考 token 算进输出预算**。Ollama 的 `num_predict` 和 OpenRouter 的 `max_tokens` 都含思考
   部分。给小了会返回**空 content** —— Oracle 侧会被 `oracle_agent.py` 的 clamp 兜底成
   「与此无关」，**静默给出错误答案且无任何报错**。
   - Oracle `max_tokens: 8` 只在**关闭思考**时安全；开思考至少给 512。
   - Questioner 用 `z-ai/glm-5.3-flash` 时 256 会返回空，需 ≥1024。
2. **思考让延迟涨约 100 倍**（qwen3.5:4b：0.67s → 79s）。本地跑务必 `.env` 设 `OLLAMA_THINK=0`。

### token 预算随汤底长度伸缩（新题集尤其重要）

推理模型的思考量随输入增长。**当前题集最长汤底 279 字，4096 预算即安全** ——
这是重建题库的附带收益。历史参考（旧题集含 1497 字汤底时的实测）：

| 汤底长度 | 够用的 max_tokens |
|---------|------------------|
| < 300 字 | 4096（当前题集全部落在此档） |
| 600–700 字 | 16384 |
| 1497 字 | 32768 |

预算不足时返回**空 content**，而 `composite_judge` 捕获异常后会**静默跳过**那次逻辑采样，
均值少一个样本却不报错。一次 27 题的抽取触发了 35 次空回复重试。
**按汤底长度设 `max_tokens`，不要用固定值。**`LLMJudge(max_tokens=...)` 已支持。

### 稳健性（已内置，长跑必需）

- 两个 provider 均带**指数退避重试**：OpenRouter 处理 429/5xx/连接错误（`OPENROUTER_MAX_ATTEMPTS`，
  默认 6）；Ollama 处理连接中断/超时（`OLLAMA_MAX_ATTEMPTS`，默认 4）。
  免费 stealth 池限流频繁，一次 pilot 触发 7 次 429 属正常。
- **空回复**：provider 重试后仍空则抛 `agents.base_agent.EmptyResponseError`；
  引擎捕获后**不计入轮次**并继续，连续 `max_empty_turns`（默认 3）次才以
  `terminated_by="empty_response"` 终止。Oracle 侧的空回复**故意不兜底**，直接抛出让跑失败，
  避免污染基准真值。
- Ollama 服务被重启（如桌面 App 抢占 11434 端口）会导致 `RemoteDisconnected`。
  **不要另起 `ollama serve`**，端口留给桌面 App。长跑前先确认服务活着。

## 评测（`plan.md`）

- **Exp 1**：每轮 checkpoint → `heuristic_judge`
- **Exp 2**：round cap + 强制 `FINAL_ANSWER`

### Tinker provider（大模型采样 / 训练后 checkpoint）

- `--questioner-provider tinker --questioner-model Qwen/Qwen3-235B-A22B-Instruct-2507`；
  model 也可以是训练产物 `tinker://…/sampler_weights/…`，RL 训出来的 Questioner 直接进评测。
- 需 `TINKER_API_KEY`（`scripts/setup_env.py` 会问）+ `pip install tinker`（已在 requirements）。
  模型名以 [官方列表](https://tinker-docs.thinkingmachines.ai/tinker/models/) 为准；按 token 计费。
- 走原生 SDK 采样（serverless 的 OpenAI 兼容端点只覆盖 Inkling 系列，不用它）。
  聊天格式用模型 tokenizer 自带 chat template；`<think>…</think>` 会被剥掉。
- **max_tokens 同样含思考 token**（同上面第 1 个坑），且 Qwen3.5 类混合推理模型默认开思考 ——
  512 预算会在思考中途截断，Questioner 整局输出乱码式思考文本（已实测）。
  **跑基准务必 `TINKER_THINK=0`**（经 chat template 的 `enable_thinking=False` 关闭），
  或给 ≥2048。实测 `TINKER_THINK=0` + questioner 2048 / oracle 1024：
  Qwen3.5-397B 8 轮解出 refsoup_008，composite 0.58（关键词 28/70 + 逻辑 30/30）。
- 重试：`TINKER_MAX_ATTEMPTS`（默认 4）指数退避，空回复抛 `EmptyResponseError`。

### 评分：`composite_judge`（推荐，满分 100）

`heuristic_judge` 只做 `key_clues` 子串匹配，**语义正确但换词表述会得 0 分** —— 实测中
glm-5.3-flash 已还原完整因果链却被判 0.00。`composite_judge` 解决这点：

| 部分 | 计算 |
|------|------|
| 关键词 **70** 分 | 命中数 / 总数 × 70（客观可验，沿用 `_clue_matches_answer`） |
| 逻辑 **30** 分 | Oracle 按纯因果链评 0–1，**采样 3 次取平均** × 30 |
| 难度 | 由 `key_clue_count` 划定：≤2 easy，≤4 medium，≥5 hard |

逻辑 prompt 明确要求「不因用词不同扣分」，避免与前 70 分重复惩罚。解析失败/调用异常的样本
被丢弃，不拉低均值。`to_dict()["score"]` 仍是归一化 0–1，现有消费方无需改动。

> ⚠️ **不要用这两套里的任何一套当难度。**`difficulty_band` 只是 `composite_judge`
> 内部给分数分档用的副产品，不是题目难度的度量。

## 题目难度：用欠定度，不要用现有的两个字段

题库里并存着三套「难度」，前两套互相矛盾且都不可用：

| 来源 | 取值 | 为什么不能用 |
|------|------|-------------|
| puzzle JSON 的 `difficulty` | hard 3 / medium 17 / easy 5 | 来自站点评分，测的是「好不好玩」不是「好不好解」 |
| `composite_judge.difficulty_band` | hard 15 / medium 9 / easy 1 | 只按线索条数分档，与推理难度无关；同一批题给出与上一行几乎相反的分布 |
| **欠定度**（`generator/analysis/puzzle_dimensions.py`） | 连续 [0,1] | ✅ 用这个 |

**这个量是「深度 × 广度」那轮讨论的最终结论，不是另起炉灶的新指标。**
原本想把题目分成两个维度 —— **深度**（汤底离汤面远，需要很多轮「是」才能确定）与
**广度**（可能很少轮就探到，也可能很多轮，因为「是否」更多在做排除）。实测下两个都
撞天花板（depth 全打 4/5 分，breadth 恒为满值），而且它们本来就不独立：汤面松到能容纳
很多机制，正因为松，其唯一真解才需要更多次重构才能锁定 —— **是同一件事的两个说法**。
合并后的量同时吃掉两者：跳跃越非显然（深）冷猜越猜不到，可能性越多（广）任一次命中
概率越低。文中说「题目难度」「欠定度」「深度广度」时指的是同一件事。

**欠定度 = 汤面单独留给你的距离有多远。**只给汤面、不给任何 Oracle 反馈，
让模型独立冷猜 N 次（默认 12），取最接近正解的一次，`欠定度 = 1 − 最佳接近度`。
接近度用候选与汤底的 embedding 相似度，不用关键词召回 —— 冷猜若用自己的话说对了机制
（「抽火柴定谁跳下」对线索「抽签」）字面对不上，那样测的是用词不是难度。

```bash
python scripts/annotate_puzzle_dimensions.py            # → data/puzzles/dimensions.json
```

**为什么可以直接用作分组变量**：它**完全不碰轮数**，因此可以安全地作为
「accuracy vs 所需轮数」图的分组变量；若用「需要多少轮」来定义难度，横轴与分组变量同源，
图会自证。

**已被否决的做法**（勿重走）：

| 做法 | 否决原因 |
|------|---------|
| 汤面–汤底 embedding 单点距离 | 与实测成绩 ρ = −0.005；`refsoup_008` 被判最深，实际是五轮直线可解的最浅题 |
| 依次加入 `key_clues` 看距离落差 | 距离**不单调**，多个线索是负贡献 |
| 深度 1–5 绝对打分 | 5 道全打 4 分，无区分度（模型没有校准过的标尺） |
| 候选去重计数（广度） | 恒为满值（12/12），被候选数上限锁死 |
| 悬置细节计数 | 值域 1–3，被汤面长度锁死；**定性上仍有用**，可用 `--with-dangling` 开启 |

首批实测跨度 0.197–0.528，排序与独立证据一致（`refsoup_008` 最好猜，正是 ox-alpha
五轮解出的那道）。**标注由 LLM 产出，投稿前需人工复核 8–10 道报 agreement。**
- Pilot 示例：

```bash
python scripts/run_pilot.py --puzzles refsoup_008 \
  --max-rounds 12 --round-caps 5 10 12 \
  --questioner-provider ollama --questioner-model qwen2.5:7b \
  --oracle-provider ollama --oracle-model qwen2.5:7b \
  --output results/pilot/refsoup_008
```

报告：`pilot_timing.json` + `pilot_timing.html`。正式全量研究前可切换 LLM judge。

## API Key

见 **`CONTRIBUTING.md`**。勿在聊天中索要 key。

```bash
python scripts/setup_env.py && python scripts/check_env.py
python scripts/run_game.py --puzzle refsoup_008 --mock
```

Ollama：`OLLAMA_TIMEOUT`（默认 600）。Z.AI Coding Plan：`ZAI_USE_CODING_ENDPOINT=1`。

## 关键约定

- **默认测试题**：`refsoup_008`
- 离线：`--mock`；测试：`pytest -q`（58 tests）
- Questioner 每轮收到完整 `qa_history`；Oracle 仅当前问题
- `forbidden_reveal` 仅 D 层 filter，运行时未注入 Oracle
- 跑满轮数默认**不**强制交答案 → 记为「未提交最终答案」得 0 分。
  用 `run_game.py --force-final-answer` 或 yaml `game.force_final_answer_on_max_rounds: true`
- `max_tokens` 按角色在 config yaml 里设（Oracle 短、Questioner 长），
  Ollama 侧已映射到 `options.num_predict`

## 常用命令

```bash
python scripts/run_game.py --puzzle refsoup_008 --mock
python scripts/run_pilot.py --puzzles refsoup_008 --mock
python scripts/run_benchmark.py --puzzles refsoup --questioner-models mock --mock
pytest -q
```

## ⚠️ 重跑 693 局：这是一次完全重跑，不是增量更新

自上一轮网格（99 E1 + 594 E2）以来有**三处同时变更**，任何一处都足以让新旧数字不可比：

| 变更 | 影响 |
|------|------|
| **题集**：11 道旧题 → 22 道已验证题 | **零重叠**。旧题里 6 道是 LLM 生成（含一道 mock 占位符、三道近重复），2 道手工添加的经典题已删 |
| **Oracle / 裁判**：不能再用 Qwen3.5-397B | 它与被测的 Questioner 同家族，「规模效应」和「与 Oracle 的相似度」在旧结果里分不开 |
| **锚点**：新增 `surface_only` 选项 | 旧结果用的 `with_solution` 含汤底信息，换锚点后 drift 斜率在 4/11 条轨迹上符号翻转 |

**因此：论文 §5 的每一个数字都需要重新建立，不能与新结果混用或做前后对比。**
新旧之间没有可以直接对照的量。这不是缺陷，是题集与环境都被修正后的必然结果。

重跑时请一并做到：

1. **两个锚点都算**（`manifold_source="surface_only"` 与 `"with_solution"`），并排报告
2. **保存逐轮数据** —— 逐轮步长与逐轮距离。目前 `e3_geometry.json` 只有汇总量，
   因此论文的核心图（步长/距离 vs 轮次）画不出来，且 E3 无法被任何人复核
3. **`qa_rounds` 入库**（可压缩），否则复核只能依赖你本机的 `results/`

## 换 Oracle / Questioner 的最短路径

1. 填 `.env`（**只在本地，绝不粘贴到对话或 PR**），然后 `python scripts/check_env.py`
2. 写一份 config yaml，按角色分别设 provider / model / `max_tokens`：

```yaml
oracle:
  provider: openrouter        # openai|anthropic|deepseek|qwen|zai|gemini|openrouter|tinker|ollama|mock
  model: z-ai/glm-5.3-flash
  max_tokens: 512             # 推理模型别设太小，思考会吃掉预算 → 空回复

questioner:
  provider: ollama
  model: qwen3.5:4b
  max_tokens: 400             # glm-5.3-flash 当 Questioner 需 ≥1024

game:
  max_rounds: 12
  min_rounds_before_answer: 5
  force_final_answer_on_max_rounds: true
  max_empty_turns: 3
```

3. 先验证 Oracle 质量再跑实验（**这一步别跳过**）：拿一组已知答案的探针问 Oracle，
   准确率低于 ~90% 就别用，否则测出来的是 Oracle 而不是 Questioner。
4. `python scripts/run_game.py --puzzle refsoup_008 --config your.yaml --no-judge`
5. 单局合理再跑 `run_pilot.py`。

`run_game.py` 默认用 `gpt-4o` 当裁判；没有 `OPENAI_API_KEY` 时加 `--no-judge`。

## 论文状态：实验章节已清空，等待重跑

`docs/paper/iab2026-draft.md` 是**内容真源**，改稿流向是单向的：

```
paper-outline.md → iab2026-draft.md → iab2026.tex → iab2026.pdf
```

直接改 `.tex` 会让 draft 失真 —— 交接时读的是 draft。

**旧的 693 局数字已从论文整体删除**，未作为 preliminary 保留。原因不只是题集换了：
当时 Oracle 与 Questioner 同家族、锚点含汤底信息、token 预算过低导致部分轮次为空。
四重问题叠加，那些数字不具参考价值，标成 preliminary 只会诱使人做前后对比。

draft 里有 **7 处 ⚠️ 待填标记**，§5 附有「需要产生的数据」表和「重跑前必须确认」清单。
**注意主线本身可能要换** —— 现有框架建立在「更多交互无用」上，若重跑不能复现，
钩子要改为「失败模式的区分」本身。引言里已写明这个条件分支。

**写作尺度：广而不细。**token 预算数值、bigram 算术、`MIN_CLUE_CHARS`、
误删又取回的经过等工程细节**不进论文** —— 它们记录在
`data/puzzles/README.md`、本文件与 `plan.md` 中。论文只写结论。

## 历史结果（已作废，仅供参考）

`refsoup_008` + Questioner `qwen3.5:4b`，三种 Oracle 全部 **0 分**，Exp1 曲线贴地、
从未主动交答案 → 结论是 4B 的能力天花板，与反馈信号质量无关。
结果在 `results/pilot/{qwen35_4b_local,qwen35_4b_vs_qwenflash,qwen35_4b_vs_oxalpha}/`。

`z-ai/glm-5.3-flash` 当 Questioner 时**第 6 轮即还原完整汤底**，但因三个管线缺陷记为 0 分
（Oracle 对长复合问句答错、5 轮空回复、跑满轮数不交答案）。前两条已修，第三条给了开关。
该局的推理内容用 `composite_judge` 重算是 **72/100**（关键词 3/5=42，逻辑 30/30）。

## 下一阶段（方向性，详见 `plan.md`「下一阶段」）

现状：只跑过 `refsoup_*` 这类**经典短汤**（单解、线性推理）。`generator/` 的 A→E 管线
已可用但只产出同类题。

**A. 题库设计：深度 × 广度**

- **深度** — 设计刁钻问题题库，朴素提问路径走不通。反面例子：`refsoup_008` 被
  glm-5.3-flash 5 轮线性推到底。抓手在 `generator/create/controllers.py`（目前无「刁钻度」维度）。
- **广度** — 一个汤面允许多个成立的解答。**代码阻塞**：`solution` 是单个字符串，
  `schema.py` / `oracle_agent.py` / `composite_judge` / `key_clues` 全按单解写死。
  待决：多解时 Oracle 对「A 解成立、B 解不成立」的问题该答什么。

**B. Exp 3 — 联想轨迹**

把「人类词义词表」和「前后轮关键词」放进同一 hidden space 量距离，刻画 Agent
基于汤面的联想 trajectory：前后轮距离＝移动步长；到人类词表的距离＝偏离人类联想的程度。
用于区分「原地打转」与「系统性走偏」——现有 `question_novelty` / `new_vocab_ratio`
是它的**词面近似版**，只抓得住前者。

前置：需要 embedding 接口（现有 provider 全是 chat）、每题一份人工标注词表
（`key_clues.py` 的 `_ZH_WORDS` 是硬编码匹配词典，**不能当人类词表用**）、逐轮关键词抽取。

## 待办

1. 全量 Exp 1/2（11×3×3）+ `plot_round_studies.py`
2. benchmark CSV / async（M4b）
3. 把 `composite_judge` 接进 `run_game.py` / `round_studies.py`（目前仅提供函数，未接线）
4. 清理遗留难度字段：puzzle JSON 的 `difficulty` 与 `difficulty_band` 都不该被当作难度用（见「题目难度」一节），考虑移除或改名
5. `convergence_speed` 指标方向是反的：它数「是」的比例，会**奖励**退化局
   （退化局 0.667 > 正常局 0.000）。需改为只统计有新词的轮次
6. 可选：Oracle 注入历史；pilot 切换 LLM judge

## 开放问题

- Exp 1 checkpoint 每 5 轮采样降成本
- key_clues 与 LLM judge 对齐
