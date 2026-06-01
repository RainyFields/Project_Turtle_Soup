from __future__ import annotations

from typing import Any, Dict

from .judge import JudgeResult
from .metrics import MetricsSummary


def print_evaluation_report(
    *,
    metrics: MetricsSummary,
    judge: JudgeResult,
    verbose: bool = True,
) -> Dict[str, Any]:
    report = {
        "metrics": metrics.to_dict(),
        "evaluation": judge.to_dict(),
    }
    if not verbose:
        return report

    print(f"📊 评分：{judge.score:.2f}")
    print(
        "🎯 命中要素："
        + (" | ".join(judge.hit_elements) if judge.hit_elements else "(无)")
        + " ✓"
    )
    if judge.missed_elements:
        print(
            "❌ 缺失要素："
            + " | ".join(judge.missed_elements)
            + " ✗"
        )
    print()
    print("— 自动指标 —")
    for k, v in metrics.to_dict().items():
        print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")
    if judge.reasoning:
        print(f"\n📝 裁判备注：{judge.reasoning}")
    return report
