# Puzzle Generator — 工作流说明

原创海龟汤生产管线（代号 **A→E**）。参考站内容**仅作本地研究**，经分析 → 生成 → 自动过滤 → **人工审核**后，才写入可公开的 benchmark 题库 `data/puzzles/`。

> 评测框架（双 Agent 对局）见仓库根 [README.md](../README.md) 与 [AGENTS.md](../AGENTS.md)。

---

## 核心原则

| 原则 | 说明 |
|------|------|
| **物理隔离** | `data/reference/`（参考原文）与 `data/puzzles/`（发布题库）平级，互不混用 |
| **单点发布** | 只有 Step E 人工确认后，才调用 `publish` 写入 `data/puzzles/turtle_NNN.json` |
| **Schema 单源** | 候选与发布题均经 `generator/schema.py` 校验，字段对齐 `refsoup_008.json` 等 benchmark 题 |
| **来源标记** | 发布题强制 `metadata.source = "generated"`，并记录 `generator_batch` |
| **分析不喂原文** | Layer B 输出统计/模板；生成 prompt 用脱敏特征，降低洗稿风险 |
| **git 边界** | `data/reference/`、`data/generator/` 本地 gitignore；**不进仓库、不对外分发** |

---

## 管线总览

```text
  参考站 (ahelumos)                    仅本地、永不发布
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  A  Reference     crawl → parse → samples.jsonl         │
│     data/reference/                                     │
└────────────────────────────┬────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────┐
│  B  Analysis      aggregate.json + patterns.json        │
│     标签分布 · 长度 · 难度校准 (高评分汤 ≥8.0)            │
└────────────────────────────┬────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────┐
│  C  Generation    LLM → staging/{batch}/turtle_candidate_* │
│     category/difficulty 由 B 层控制器抽样                  │
└────────────────────────────┬────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────┐
│  D  Filter (CLI)  schema · 泄底 · 相似度 → *.filter.json │
│     不修改候选 JSON；仅写报告，供人工参考                    │
└────────────────────────────┬────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────┐
│  E  Review (UI/CLI)  编辑 · 标记 · 发布 → data/puzzles/    │
│     queue.json 记录审核状态与 published_id                 │
└─────────────────────────────────────────────────────────┘
```

**工具边界（已定稿）：**

- **D 层**：仅命令行 `filter_candidates.py`，不在 Web UI 中重跑
- **E 层**：Web UI（`review_ui.py`）负责审核与发布；D 的 `.filter.json` 可人工查阅，UI 不展示 filter 操作

---

## 端到端工作流

典型一次「从参考到入库」按顺序执行：

```bash
# 0. 环境
pip install -r requirements.txt
cp .env.example .env          # 填写 QWEN_API_KEY / GEMINI_API_KEY 等

# A — 爬参考（本地）
python scripts/crawl_reference.py --sort rating_desc --max-pages 3

# B — 统计分析
python scripts/analyze_reference.py

# C — 生成候选（batch id 自定，如 v5）
python scripts/generate_puzzles.py --batch v5 --count 5

# D — 自动过滤（写 sidecar 报告）
python scripts/filter_candidates.py --batch v5

# E — 人工审核 + 发布
python scripts/review_ui.py     # http://127.0.0.1:8765/
```

人工在 E 层完成：读汤面/汤底 → 必要时改 staging JSON → 标记通过/拒绝 → 单条或批量发布。

### 支线 R — 参考站直导入（评测用）

生成题（`turtle_*`）偏难时，可从 Layer A 爬取结果**直接导入** benchmark，与原创题区分命名：

| 原创（E 层） | 参考导入（R 支线） |
|-------------|-------------------|
| `turtle_006` … | `refsoup_001` … |
| `metadata.source: generated` | `metadata.source: reference` |
| 经 LLM 生成 + 人工审核 | 来自 ahelumos 原文（汤面/汤底） |

```bash
# 需先 crawl（Layer A）
python scripts/crawl_reference.py --sort rating_desc --max-pages 3

# 预览：短 + 经典
python scripts/import_reference_puzzles.py --replace --require-classic \
  --max-surface-chars 120 --max-solution-chars 200 --limit 10 --dry-run

# 导入 → data/puzzles/refsoup_001.json …
python scripts/import_reference_puzzles.py --replace --require-classic \
  --max-surface-chars 120 --max-solution-chars 200 --limit 10
```

`key_clues` 由 `generator/reference/key_clues.py` 从汤底提取短关键词（过滤汤面重复与无关词）；可用 `scripts/refresh_reference_key_clues.py` 批量刷新。`oracle_rules.forbidden_reveal` 仅用于 D 层泄底检查，**游戏运行时未注入 Oracle**。

导入记录见 `data/generator/reference_import/manifest.json`。

评测选题（默认示例题 `refsoup_008`）：

```bash
python scripts/run_game.py --puzzle refsoup_008 ...
python scripts/run_benchmark.py --puzzles refsoup ...
python scripts/run_pilot.py --puzzles refsoup_008 --mock
```

---

## Layer A — Reference Data

**目的：** 抓取参考站结构与标签分布，**不**进入 benchmark。

| 项 | 值 |
|----|-----|
| 参考站 | [soup.ahelumos.com](https://soup.ahelumos.com/) |
| 实现 | `generator/reference/ahelumos.py`, `crawler.py`, `parser.py` |
| 输出 | `data/reference/parsed/samples.jsonl`（汤面+汤底+标签+评分） |
| 合规 | 遵守 robots / 速率限制（`generator/config.yaml` → `rate_limit_seconds`） |

```bash
python scripts/crawl_reference.py                          # 默认首页
python scripts/crawl_reference.py --sort rating_desc         # 按评分排序
python scripts/crawl_reference.py --max-pages 3            # 多页列表
python scripts/crawl_reference.py --no-details             # 仅列表，无汤底
python scripts/crawl_reference.py --fresh                  # 清空 JSONL 重爬
```

---

## Layer B — Feature Analysis

**目的：** 从参考库提取**聚合统计**与**写作模板**，驱动 C 层的 category / difficulty 抽样。

| 输出文件 | 内容 |
|----------|------|
| `data/generator/analysis/aggregate.json` | 标签分布、长度区间、分类计数 |
| `data/generator/analysis/patterns.json` | 高评分汤结构模板、`difficulty_weights` |

**难度校准：** 默认取评分 ≥ `8.0` 的参考汤（可在 `config.yaml` 或 CLI 调整），统计 easy/medium/hard 比例，供 `generate_puzzles.py` 抽样。

```bash
python scripts/analyze_reference.py
python scripts/analyze_reference.py --min-rating 8.5
python scripts/analyze_reference.py --output data/generator/analysis/
```

标签 → category 映射见 `generator/create/taxonomy.py`（红汤/清汤/黑汤/恐怖/规则怪谈等）。

---

## Layer C — Original Generation

**目的：** LLM 生成**原创**候选，写入 staging，schema 对齐 benchmark。

| 项 | 说明 |
|----|------|
| 入口 | `scripts/generate_puzzles.py` |
| 核心 | `generator/create/llm_generator.py`（JSON mode + 重试） |
| 控制器 | `generator/create/controllers.py` — 按 B 层权重抽 category/difficulty |
| 输出 | `data/generator/staging/{batch}/turtle_candidate_NNN.json` |
| Provider | 默认 `qwen` + `qwen-plus`（见 `generator/config.yaml`） |

```bash
# 真实模型（读 .env）
python scripts/generate_puzzles.py --batch v5 --count 5

# 离线占位（Mock 汤，勿发布）
python scripts/generate_puzzles.py --batch demo --count 3 --mock

# 覆盖 provider / model
python scripts/generate_puzzles.py --batch v5 --count 2 --provider gemini --model gemini-2.5-flash
```

**Provider 回退逻辑：** 未配置 API Key 时自动 `--mock`；Gemini 免费档建议 `gemini-2.5-flash` 并注意 `gemini_delay_seconds` 限流。

候选 JSON 字段：`id`, `title`, `difficulty`, `category`, `surface`, `solution`, `key_clues`, `oracle_rules`, `metadata`（`source: generated`）。

---

## Layer D — Safety / Quality / Similarity

**目的：** 对 staging 候选做**只读**自动检查，结果写入 sidecar，**不**自动删改或发布。

| 检查项 | 实现 |
|--------|------|
| Schema | `generator/filter/checks.py` |
| 汤面泄底 | `forbidden_reveal` 词是否出现在 `surface` |
| 分类一致 | category 与 metadata 标签 |
| 相似度 | 候选汤面 vs 参考库汤面，阈值默认 `0.85` |

```bash
python scripts/filter_candidates.py --batch v5
# → 每题生成 turtle_candidate_NNN.filter.json
#   { "passed": true/false, "errors": [...], "similarity_score": 0.xx }
```

**人工用法：** 发布前查阅 `.filter.json`；FAIL 的题在 E 层编辑 staging 后，可重新跑 D。**UI 不提供重跑 filter**（保持 D/E 职责分离）。

---

## Layer E — Human Review + Publishing

**目的：** 唯一写入 `data/puzzles/` 的关口。人工读题、改 staging、标记状态、分配正式 ID。

### 状态机

审核状态保存在 `data/generator/review/queue.json`：

| status | 含义 |
|--------|------|
| `pending` | 待审（默认） |
| `accepted` | 人工通过，可发布 |
| `needs_edit` | 需修改后再审 |
| `rejected` | 拒绝，不发布 |

每条记录：`key`（`batch/filename`）、`status`、`notes`、可选 `published_id` / `published_path`。

### Web UI（推荐）

```bash
python scripts/review_ui.py              # 默认 http://127.0.0.1:8765/
python scripts/review_ui.py --port 9000
```

| 功能 | 说明 |
|------|------|
| 表格 | 按批次/审核状态筛选；显示 schema 校验 |
| 详情 | 编辑汤面、汤底、key_clues、oracle_rules；保存回 staging |
| 审核 | 通过 / 需修改 / 拒绝 + 备注 |
| 单条发布 | 写入 `data/puzzles/turtle_NNN.json`，更新 queue |
| **批量发布选中** | 勾选多条，一次发布（跳过已发布） |
| **发布本批次已通过** | 当前批次内 `accepted` 且未发布的题一键发布 |

实现：`generator/review/web_app.py` + `service.py` + `templates/review.html`。

### CLI 单条发布

```bash
python scripts/publish_puzzle.py \
  --candidate data/generator/staging/v5/turtle_candidate_001.json \
  --batch v5
```

### 发布规则（`generator/review/publish.py`）

1. 校验 staging 候选 schema
2. 分配下一个 `turtle_NNN`（扫描 `data/puzzles/`，不覆盖已有）
3. 强制 `metadata.source = "generated"`，写入 `metadata.generator_batch`
4. 再次 `validate_puzzle(..., for_publish=True)` 后落盘

---

## 目录与产物

```text
data/
├── puzzles/                          # ✅ 发布面（git 跟踪）
│   ├── turtle_*.json …
│   └── refsoup_008.json …          # R 支线参考导入
├── reference/                        # 🔒 参考原文（gitignore）
│   ├── parsed/samples.jsonl
│   └── raw/                          # 可选 HTML 快照
└── generator/                        # 🔒 生成中间态（gitignore）
    ├── analysis/
    │   ├── aggregate.json
    │   └── patterns.json
    ├── staging/{batch}/
    │   ├── turtle_candidate_001.json
    │   └── turtle_candidate_001.filter.json   # D 层报告
    └── review/
        └── queue.json                           # E 层审核队列

generator/
├── config.yaml                       # 路径、provider、filter 阈值
├── schema.py                         # 校验单源
├── reference/                        # A 层 + R 支线（to_puzzle, key_clues, import_publish）
├── analysis/                         # B 层
├── create/                           # C 层
├── filter/                           # D 层
└── review/                           # E 层（含 Web UI）

scripts/
├── crawl_reference.py                # A
├── analyze_reference.py              # B
├── generate_puzzles.py               # C
├── filter_candidates.py              # D
├── review_ui.py                      # E (UI)
├── publish_puzzle.py                 # E (CLI)
├── import_reference_puzzles.py       # R 支线
└── refresh_reference_key_clues.py    # R 支线 key_clues 刷新
```

---

## 配置要点

`generator/config.yaml`：

| 区块 | 作用 |
|------|------|
| `reference.*` | 爬取 URL、速率、User-Agent |
| `paths.*` | reference / staging / review / puzzles 路径 |
| `analysis.min_rating_for_calibration` | 高评分阈值（默认 8.0） |
| `generation.provider` / `model` | 默认 `qwen` / `qwen-plus` |
| `filter.similarity_threshold` | 与参考库相似度上限（默认 0.85） |
| `publish.puzzles_dir` | 发布目录（默认 `data/puzzles`） |

环境变量（`.env`）：

| Key | Provider |
|-----|----------|
| `QWEN_API_KEY` | 通义千问（默认） |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Gemini |
| `DEEPSEEK_API_KEY` | DeepSeek |
| `OPENAI_API_KEY` | OpenAI |

---

## 与 benchmark 的关系

发布后的 `data/puzzles/turtle_NNN.json` 与 `refsoup_NNN.json` **格式相同**，可直接用于：

```bash
python scripts/run_game.py --puzzle refsoup_008 --mock
python scripts/run_benchmark.py --puzzles refsoup --mock
```

`engine.load_puzzle` / `list_puzzle_ids(family="all"|"turtle"|"refsoup")` **只读** `data/puzzles/`，不接触 reference 或 staging。

---

## 操作备忘

| 场景 | 做法 |
|------|------|
| 新一批生成 | B 可跳过（若 analysis 未变）→ C → D → E |
| Filter FAIL | E 层改 staging → 重跑 D → 再审 |
| Mock 批次 (v1/v2) | 仅开发用，勿发布 |
| 已发布题 | queue 有 `published_id`；UI 禁止重复发布 |
| 批量入库 | UI「发布本批次已通过」或勾选「批量发布选中」 |

---

## 实现状态

A→E 与 R 支线均已可用。后续非阻塞：benchmark M4b、更多 provider、发布前 mock smoke test。

---

## 下一阶段：题库的深度与广度

当前管线只产出与参考站同类的**经典短汤（单解、线性推理）**。Benchmark 需要两个新维度
（完整计划见仓库根 [`plan.md`](../plan.md)「下一阶段」）：

### 深度 — 刁钻问题题库

目标：朴素提问路径走不通，必须做非平凡的假设跳跃。

- **Layer C**：`create/controllers.py` 目前只按 B 层统计抽样 category/difficulty，
  没有「刁钻度」控制维度，需要新增可控机制。
- **Layer D**：可加自动筛选 —— 用一个强 Questioner 试解候选，N 轮内被解出的判为深度不足。
  实测参照：`refsoup_008` 被 `z-ai/glm-5.3-flash` 5 轮线性推到底。

### 广度 — 一个汤面多个成立的解答

**这不是加个字段就行**，`solution` 是单个字符串，整条链路按单解写死：

| 位置 | 需要改什么 |
|------|-----------|
| `schema.py` | `REQUIRED_TOP_LEVEL` 含 `solution: str`，需扩成多解结构并向后兼容 |
| `../agents/oracle_agent.py` | 模板只注入一个 `solution`；多解下是非判定规则需重新定义 |
| `../evaluation/judge.py` | `composite_judge` 需按**最佳匹配解**打分 |
| `key_clues` | 需按解分组，否则关键词分会跨解混算 |

**待决**：多解时 Oracle 对「A 解成立、B 解不成立」的问题该答什么？这决定 schema 怎么设计。
