from generator.analysis.difficulty import calibrate_difficulty_distribution
from generator.create.controllers import sample_difficulty
from generator.create.taxonomy import rating_to_difficulty


def _sample(rating: float, sid: str = "1") -> dict:
    return {"external_id": sid, "rating": rating, "surface": "x" * 50, "solution": "y" * 100}


def test_rating_to_difficulty_with_thresholds():
    th = {"easy_max": 6.0, "medium_max": 9.0}
    assert rating_to_difficulty(5.0, thresholds=th) == "easy"
    assert rating_to_difficulty(7.0, thresholds=th) == "medium"
    assert rating_to_difficulty(9.5, thresholds=th) == "hard"


def test_calibrate_from_high_rated():
    samples = [
        _sample(10.0, "a"),
        _sample(9.5, "b"),
        _sample(8.5, "c"),
        _sample(8.0, "d"),
        _sample(2.0, "noise"),
        _sample(4.0, "low"),
    ]
    cal = calibrate_difficulty_distribution(samples, min_rating=8.0)
    assert cal["high_rated_count"] == 4
    w = cal["difficulty_weights"]
    assert abs(sum(w.values()) - 1.0) < 0.01
    assert all(d in w for d in ("easy", "medium", "hard"))


def test_sample_difficulty_uses_weights():
    cal = {
        "difficulty_weights": {"easy": 0.0, "medium": 0.0, "hard": 1.0},
        "rating_thresholds": {"easy_max": 5.0, "medium_max": 8.5},
    }
    for _ in range(20):
        assert sample_difficulty(cal) == "hard"
