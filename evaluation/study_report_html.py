from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _esc(value: Any) -> str:
    if value is None:
        return "—"
    return html.escape(str(value))


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _round_chart_bars(accuracy_by_round: Dict[str, float], *, max_height: int = 120) -> str:
    if not accuracy_by_round:
        return "<p class='muted'>无数据</p>"
    rounds = sorted(accuracy_by_round.keys(), key=lambda k: int(k))
    bars: List[str] = []
    for r in rounds:
        score = float(accuracy_by_round[r])
        h = max(2, int(score * max_height))
        bars.append(
            f"<div class='bar-col' title='Round {r}: {_pct(score)}'>"
            f"<div class='bar' style='height:{h}px'></div>"
            f"<span class='bar-label'>{_esc(r)}</span></div>"
        )
    return f"<div class='bar-chart'>{''.join(bars)}</div>"


def render_study_report_html(report: Dict[str, Any], *, title: str = "Round Study Report") -> str:
    """Render pilot_timing.json or real_timing.json as a standalone HTML page."""
    puzzle_ids = report.get("puzzle_ids") or (
        [report["puzzle_id"]] if report.get("puzzle_id") else []
    )
    questioner = report.get("questioner") or {}
    oracle = report.get("oracle") or {}
    timing = report.get("timing") or report.get("wall_clock_s") or {}
    api_calls = report.get("api_calls") or report.get("api_calls_pilot") or {}
    extrap = report.get("extrapolation_full_study") or {}
    exp1_rows = report.get("exp1_results") or (
        [report["exp1_result"]] if report.get("exp1_result") else []
    )
    exp2_rows = report.get("exp2_results") or []

    exp1_sections: List[str] = []
    for row in exp1_rows:
        pid = row.get("puzzle_id", "?")
        acc = row.get("accuracy_by_round") or {}
        exp1_sections.append(
            f"<section class='card'>"
            f"<h3>Exp1 · {_esc(pid)}</h3>"
            f"<p>Played rounds: <strong>{_esc(row.get('total_played_rounds'))}</strong> · "
            f"Natural end: <strong>{_esc(row.get('natural_end_round'))}</strong> · "
            f"Elapsed: <strong>{_esc(row.get('elapsed_s'))}s</strong></p>"
            f"{_round_chart_bars(acc)}"
            f"<details><summary>Checkpoint accuracy table</summary>"
            f"<table><thead><tr><th>Round</th><th>Accuracy</th></tr></thead><tbody>"
            + "".join(
                f"<tr><td>{_esc(r)}</td><td>{_pct(float(v))}</td></tr>"
                for r, v in sorted(acc.items(), key=lambda kv: int(kv[0]))
            )
            + "</tbody></table></details>"
            f"</section>"
        )

    exp2_rows_html = "".join(
        f"<tr>"
        f"<td>{_esc(r.get('puzzle_id'))}</td>"
        f"<td>{_esc(r.get('round_cap'))}</td>"
        f"<td>{_pct(float(r.get('score', 0)))}</td>"
        f"<td>{_esc(r.get('total_rounds'))}</td>"
        f"<td>{_esc(r.get('terminated_by'))}</td>"
        f"<td>{_esc(r.get('elapsed_s'))}s</td>"
        f"<td><details><summary>答案</summary><pre>{_esc(r.get('final_answer'))}</pre></details></td>"
        f"</tr>"
        for r in exp2_rows
    )

    per_call = report.get("per_call_timing") or {}
    per_task = timing.get("per_task") if isinstance(timing, dict) else None
    per_task_rows = ""
    if per_task:
        per_task_rows = "".join(
            f"<tr><td>{_esc(t.get('label'))}</td><td>{_esc(t.get('elapsed_s'))}s</td></tr>"
            for t in per_task
        )

    total_s = timing.get("total_s") or timing.get("total")
    exp1_s = timing.get("exp1_total_s") or timing.get("exp1")
    exp2_s = timing.get("exp2_total_s") or timing.get("exp2")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_esc(title)}</title>
  <style>
    :root {{
      --bg: #f6f3ec; --card: #fff; --ink: #1a1a1a; --muted: #666;
      --border: #ddd; --accent: #2563eb; --bar: #3b82f6;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: system-ui, sans-serif; background: var(--bg); color: var(--ink); }}
    header {{ background: var(--card); border-bottom: 2px solid var(--ink); padding: 20px 28px; }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 24px 28px 48px; }}
    h1 {{ margin: 0 0 8px; font-size: 1.4rem; }}
    h2 {{ margin: 28px 0 12px; font-size: 1.1rem; }}
    h3 {{ margin: 0 0 12px; font-size: 1rem; }}
    .muted {{ color: var(--muted); font-size: 0.9rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
    .stat {{ font-size: 1.5rem; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--card); font-size: 0.9rem; }}
    th, td {{ border: 1px solid var(--border); padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #efeae0; }}
    pre {{ white-space: pre-wrap; word-break: break-word; margin: 8px 0 0; font-size: 0.85rem; }}
    details summary {{ cursor: pointer; color: var(--accent); }}
    .bar-chart {{ display: flex; align-items: flex-end; gap: 6px; height: 140px; padding-top: 8px; }}
    .bar-col {{ display: flex; flex-direction: column; align-items: center; flex: 1; min-width: 24px; }}
    .bar {{ width: 100%; max-width: 36px; background: var(--bar); border-radius: 4px 4px 0 0; }}
    .bar-label {{ font-size: 0.7rem; color: var(--muted); margin-top: 4px; }}
  </style>
</head>
<body>
  <header>
    <h1>{_esc(title)}</h1>
    <p class="muted">
      Puzzles: {_esc(", ".join(puzzle_ids))} ·
      Questioner: {_esc(questioner.get("provider"))}/{_esc(questioner.get("model"))} ·
      Oracle: {_esc(oracle.get("provider"))}/{_esc(oracle.get("model"))}
    </p>
  </header>
  <main>
    <h2>Summary</h2>
    <div class="grid">
      <div class="card"><div class="muted">Total wall time</div><div class="stat">{_esc(total_s)}s</div></div>
      <div class="card"><div class="muted">Exp1</div><div class="stat">{_esc(exp1_s)}s</div></div>
      <div class="card"><div class="muted">Exp2</div><div class="stat">{_esc(exp2_s)}s</div></div>
      <div class="card"><div class="muted">Pilot API calls</div><div class="stat">{_esc(api_calls.get("pilot_total") or api_calls.get("total"))}</div></div>
    </div>

    <h2>Exp1 — Learning curve</h2>
    {''.join(exp1_sections) or "<p class='muted'>无 Exp1 数据</p>"}

    <h2>Exp2 — Round budget</h2>
    <div class="card" style="padding:0; overflow:auto">
      <table>
        <thead><tr>
          <th>Puzzle</th><th>Cap</th><th>Score</th><th>Rounds</th><th>End</th><th>Time</th><th>Final answer</th>
        </tr></thead>
        <tbody>{exp2_rows_html or "<tr><td colspan='7'>无数据</td></tr>"}</tbody>
      </table>
    </div>

    <h2>Extrapolation (full study)</h2>
    <div class="card">
      <p>Assumption: {_esc(extrap.get("assumption", "11 puzzles × 3 models × 3 seeds"))}</p>
      <p>Combined API calls (est.): <strong>{_esc((extrap.get("api_calls_estimated") or {}).get("combined"))}</strong></p>
      <p>Combined hours @ {_esc(extrap.get("at_sec_per_call"))}s/call: <strong>{_esc(extrap.get("combined_estimated_h") or extrap.get("combined_hours"))}h</strong></p>
    </div>

    {"<h2>Per-task timing</h2><div class='card' style='padding:0'><table><thead><tr><th>Task</th><th>Elapsed</th></tr></thead><tbody>" + per_task_rows + "</tbody></table></div>" if per_task_rows else ""}

    {"<h2>Per-call timing (measured)</h2><div class='card'><p>Calls: <strong>" + _esc(per_call.get("count")) + "</strong> · mean: <strong>" + _esc(per_call.get("mean_s")) + "s</strong> · median: <strong>" + _esc(per_call.get("median_s")) + "s</strong> · p95: <strong>" + _esc(per_call.get("p95_s")) + "s</strong></p></div>" if per_call else ""}
  </main>
</body>
</html>"""


def write_report_html(report: Dict[str, Any], json_path: Path, *, title: Optional[str] = None) -> Path:
    """Write sibling HTML file for a report JSON path."""
    html_path = json_path.with_suffix(".html")
    page_title = title or f"turtle-soup-bench · {json_path.stem}"
    html_path.write_text(
        render_study_report_html(report, title=page_title),
        encoding="utf-8",
    )
    return html_path


def write_json_and_html(report: Dict[str, Any], json_path: Path, *, title: Optional[str] = None) -> Path:
    """Write report JSON and companion HTML; return HTML path."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return write_report_html(report, json_path, title=title)
