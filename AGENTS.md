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
| `real/` | 参考站「经典」标签全量 27 题，每题带 `reference_url` | ✅ |
| `generated/` | LLM 生成 + 团队自撰 9 题 | ❌ |

取题一律用 `list_puzzle_ids(family="real")`；`"all"` / `"turtle"` / `"refsoup"` 会跨目录。
`key_clues` 由 `scripts/refresh_key_clues_llm.py` 用 LLM 统一抽取（因果要素，非孤立名词）。

`data/reference/`、`data/generator/`、`results/`、`data/trajectories/` 已 gitignore。

### 参考汤（R 支线）

```bash
python scripts/import_reference_puzzles.py --replace --require-classic \
  --max-surface-chars 120 --max-solution-chars 200 --limit 10
python scripts/refresh_reference_key_clues.py
```

`key_clues`：`generator/reference/key_clues.py`（词典匹配 + 过滤汤面重复词）。

## 模型选型（2026-08-25 实测，`refsoup_008` 10 题探针）

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

推理模型的思考量随输入增长。`real/` 里有 5 道汤底超过 600 字，最长 1497 字，
实测 `z-ai/glm-5.3-flash` 在这些题上：

| 汤底长度 | 够用的 max_tokens |
|---------|------------------|
| < 200 字 | 4096 |
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

> ⚠️ 难度定义冲突未决：`refsoup_008` 的 JSON 标 `"difficulty": "easy"`，
> 按 `key_clue_count=5` 算却是 `hard`。两套定义并存，尚未统一。
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

## 已知结果（2026-08-25）

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
4. 统一难度定义：puzzle JSON 的 `difficulty` vs `key_clue_count`
5. `convergence_speed` 指标方向是反的：它数「是」的比例，会**奖励**退化局
   （退化局 0.667 > 正常局 0.000）。需改为只统计有新词的轮次
6. 可选：Oracle 注入历史；pilot 切换 LLM judge

## 开放问题

- Exp 1 checkpoint 每 5 轮采样降成本
- key_clues 与 LLM judge 对齐
