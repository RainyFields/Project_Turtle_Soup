# 题库：按来源隔离

**两个目录不可混用。** 实验对象只能取 `real/`。

| 目录 | 内容 | 能否用于实验 |
|------|------|-------------|
| `real/` | **仅**参考站（ahelumos）收录且带「经典」标签的题，每题有 `reference_url` | ✅ **是** |
| `generated/` | LLM 生成、或团队自撰未经外部验证的题 | ❌ **否** |

## 为什么必须隔离

实验要成立，前提是**题目本身人类能解出**。只有这样，模型解不出才说明模型的问题。

`generated/` 里的题没有这个保证：没人验证过它们可解、汤底是否唯一、线索是否充分。
模型在这类题上得 0 分，无法区分「模型弱」和「题目本身有问题」。

`generated/` 中已知的具体问题：

- `turtle_010` 标题就是 **"Mock原创汤 #3"** —— batch v1 的 mock 占位符，
  `generator/README.md` 明确写了「Mock 批次 (v1/v2)：仅开发用，勿发布」，它被误发布了。
  其"汤底"是物理常识解释，不含横向跳跃，不构成海龟汤。
- `turtle_012` / `turtle_014` / `turtle_015` 是同批次「红指甲」母题的**三个近重复变体**，
  作为独立题目计入会造成样本不独立。
- `turtle_003` / `004` / `005` 标 `source: original`（团队自撰）。非 LLM 生成，
  但同样缺乏外部验证，因此也不放进 `real/`。
- `turtle_001`（餐厅里的男人）、`turtle_002`（电梯里的矮人）曾以 `source: classic`
  手工加入，**已删除**：它们不来自参考站，无从证明有人真的玩过并解出。
  而且 `turtle_001` 与站点的 `refsoup_009`（海龟汤）是同一个经典故事的两个版本。
  需要时可从 git 取回：`git show HEAD:data/puzzles/turtle_001.json`。

## 用法

```python
from engine.game import list_puzzle_ids, load_puzzle

list_puzzle_ids(family="real")        # ✅ 实验用这个
list_puzzle_ids(family="generated")   # 仅用于生成管线开发
list_puzzle_ids(family="all")         # ⚠️ 会混入 generated
```

`load_puzzle(id)` 会同时搜索两个目录（按 id 取题时不受目录影响）。
`family="turtle"` / `"refsoup"` 按 id 前缀匹配，**会跨目录**，谨慎使用。

## 新增题目

- 参考站导入 → `scripts/import_reference_puzzles.py`，写入 `real/`
- 生成管线发布 → `scripts/publish_puzzle.py` / 审核 UI，写入 `generated/`
