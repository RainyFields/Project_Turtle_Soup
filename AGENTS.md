# Agent Guide — turtle-soup-bench

本文件供 Cursor Agent **持久记忆**使用。用户新开对话时，请先阅读本文件与 `.cursor/rules/turtle-soup-bench.mdc`。

## 项目目标

构建可复现的海龟汤双 Agent 框架：Oracle 持汤底回答三值；Questioner 仅见汤面主动提问，最终提交 `FINAL_ANSWER:`。

## 架构（已实现）

| 路径 | 职责 |
|------|------|
| `agents/oracle_agent.py` | 汤主，输出 clamp 到 是/不是/与此无关 |
| `agents/questioner_agent.py` | 猜题者，提问或 FINAL_ANSWER |
| `agents/provider_factory.py` | openai / anthropic / deepseek / ollama / mock |
| `engine/game.py` | `TurtleSoupGame` 主循环 |
| `engine/trajectory.py` | 轨迹 JSON |
| `evaluation/` | metrics + heuristic/LLM judge |
| `scripts/run_game.py` | 单局 CLI |
| `scripts/run_benchmark.py` | 批量评测 |

## 关键约定

- 默认测试题：`data/puzzles/turtle_001.json`
- 离线开发：一律加 `--mock`（`MockProvider` 有脚本化问答）
- 轨迹写入：`data/trajectories/`（已 gitignore）
- Python 3.10+；勿用系统 3.7
- 改代码保持最小 diff；测试用 `pytest -q`

## 常用命令

```bash
python scripts/run_game.py --puzzle turtle_001 --mock
python scripts/run_benchmark.py --puzzles all --questioner-models gpt-4o --mock --output results/
pytest -q
```

## 待办（优先级）

1. **M4**：benchmark 汇总报告（表格/CSV）、可选 async 并发
2. **Provider**：Qwen、Mistral（OpenAI 兼容 base_url）
3. **Oracle debug**：`debug_mode` 下输出 oracle 推理片段
4. **评估**：key_clues 与 judge 对齐 PRD 指标定义
5. **Phase 2**：多 Questioner 协作（见 PRD §8）

## 开放问题（PRD §9）

- Oracle 是否允许「接近了」类提示（当前严格三值）
- key_clues 人工标注 vs LLM 生成
- 难度分级客观标准

## 负责人

Xiaoxuan — 2026-06-01 初始化实现（M0–M3 基础可用）
