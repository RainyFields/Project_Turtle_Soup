import json
from pathlib import Path

from evaluation.study_report_html import render_study_report_html, write_report_html


def test_render_pilot_report_contains_sections():
    report = {
        "puzzle_ids": ["turtle_011"],
        "questioner": {"provider": "ollama", "model": "qwen2.5:7b"},
        "oracle": {"provider": "ollama", "model": "qwen2.5:7b"},
        "timing": {"total_s": 100, "exp1_total_s": 60, "exp2_total_s": 40},
        "api_calls": {"pilot_total": 50},
        "extrapolation_full_study": {"combined_estimated_h": 10.5},
        "exp1_results": [
            {
                "puzzle_id": "turtle_011",
                "accuracy_by_round": {"1": 0.0, "2": 0.5},
                "total_played_rounds": 2,
                "elapsed_s": 60,
            }
        ],
        "exp2_results": [
            {
                "puzzle_id": "turtle_011",
                "round_cap": 5,
                "score": 0.2,
                "final_answer": "test answer",
                "total_rounds": 5,
                "terminated_by": "final_answer",
                "elapsed_s": 20,
            }
        ],
    }
    html = render_study_report_html(report, title="Test Report")
    assert "Exp1 — Learning curve" in html
    assert "Exp2 — Round budget" in html
    assert "turtle_011" in html
    assert "test answer" in html


def test_write_report_html_sibling(tmp_path: Path):
    report = {"puzzle_ids": ["turtle_001"], "exp1_results": [], "exp2_results": []}
    json_path = tmp_path / "pilot_timing.json"
    json_path.write_text(json.dumps(report), encoding="utf-8")
    html_path = write_report_html(report, json_path)
    assert html_path == tmp_path / "pilot_timing.html"
    assert html_path.exists()
