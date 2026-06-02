from pathlib import Path

import yaml

from generator.review import service
from generator.review.queue import ReviewStatus


def test_list_candidates_includes_review_fields(tmp_path):
    root = tmp_path
    cfg = {
        "paths": {
            "staging_dir": "data/generator/staging",
            "review_dir": "data/generator/review",
        }
    }
    (root / "generator").mkdir()
    (root / "generator/config.yaml").write_text(yaml.dump(cfg), encoding="utf-8")
    staging = root / "data/generator/staging/v9"
    staging.mkdir(parents=True)
    (staging / "turtle_candidate_001.json").write_text(
        """{
  "id": "turtle_candidate_001",
  "title": "测试",
  "difficulty": "medium",
  "category": "mystery",
  "surface": "汤面",
  "solution": "汤底",
  "key_clues": ["a"],
  "oracle_rules": {"answerable_topics": [], "forbidden_reveal": []},
  "metadata": {"source": "generated", "language": "zh"}
}""",
        encoding="utf-8",
    )
    rows = service.list_candidates(root, cfg, batch="v9")
    assert len(rows) == 1
    assert rows[0]["review_status"] == ReviewStatus.PENDING.value
    assert rows[0]["title"] == "测试"


def test_publish_staging_batch_skips_not_accepted(tmp_path):
    root = tmp_path
    cfg = {
        "paths": {
            "staging_dir": "data/generator/staging",
            "review_dir": "data/generator/review",
        },
        "publish": {"puzzles_dir": "data/puzzles"},
    }
    (root / "generator").mkdir()
    (root / "generator/config.yaml").write_text(yaml.dump(cfg), encoding="utf-8")
    staging = root / "data/generator/staging/v9"
    staging.mkdir(parents=True)
    puzzle = """{
  "id": "turtle_candidate_001",
  "title": "测试",
  "difficulty": "medium",
  "category": "mystery",
  "surface": "汤面",
  "solution": "汤底",
  "key_clues": ["a"],
  "oracle_rules": {"answerable_topics": ["x"], "forbidden_reveal": []},
  "metadata": {"source": "generated", "language": "zh"}
}"""
    (staging / "turtle_candidate_001.json").write_text(puzzle, encoding="utf-8")
    (root / "data/puzzles").mkdir(parents=True)

    result = service.publish_staging_batch(root, cfg, batch="v9", only_accepted=True)
    assert result["published"] == []
    assert len(result["skipped"]) == 1
    assert result["skipped"][0]["reason"] == "not_accepted"

    service.set_review_status(root, cfg, "v9", "turtle_candidate_001.json", ReviewStatus.ACCEPTED.value)
    result2 = service.publish_staging_batch(root, cfg, batch="v9", only_accepted=True)
    assert len(result2["published"]) == 1
    assert result2["published"][0]["published_id"].startswith("turtle_")
