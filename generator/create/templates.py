from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


def load_system_prompt() -> str:
    path = Path(__file__).parent / "prompts" / "generation_system.txt"
    return path.read_text(encoding="utf-8")


def build_user_prompt(
    *,
    category: str,
    difficulty: str,
    pattern_hints: Dict[str, Any],
    style_hints: str = "",
    source_tags: Optional[List[str]] = None,
) -> str:
    hints = pattern_hints.get("writing_hints") or []
    hint_block = "\n".join(f"- {h}" for h in hints)
    sl = pattern_hints.get("surface_len_p25_p75") or [30, 120]
    sol = pattern_hints.get("solution_len_p25_p75") or [80, 400]
    tags_line = ""
    if source_tags:
        tags_line = f"参考标签（ahelumos）：{'、'.join(source_tags)}\n"
    style_line = f"风格说明：{style_hints}\n" if style_hints else ""
    return (
        f"分类：{category}\n"
        f"难度：{difficulty}\n"
        f"{tags_line}"
        f"{style_line}"
        f"建议汤面长度区间（字）：{sl[0]}–{sl[1]}\n"
        f"建议汤底长度区间（字）：{sol[0]}–{sol[1]}\n"
        f"写作要点：\n{hint_block}\n"
        "请输出 JSON，不要 markdown 代码块。"
    )
