from generator.create.controllers import sample_slot, slot_to_metadata_tags
from generator.create.taxonomy import (
    build_prompt_hints,
    rating_to_difficulty,
    tags_to_category,
)


def test_tags_to_category():
    assert tags_to_category(["恐怖", "经典"]) == "horror"
    assert tags_to_category(["搞笑", "清汤"]) == "comedy"
    assert tags_to_category(["红汤"]) == "horror"


def test_rating_to_difficulty():
    assert rating_to_difficulty(9.0) == "hard"
    assert rating_to_difficulty(6.0) == "medium"
    assert rating_to_difficulty(None) == "medium"


def test_sample_slot_with_histogram():
    stats = {
        "tag_histogram": {"恐怖": 10, "搞笑": 2, "红汤": 5},
        "rating_by_tag": {"恐怖": 8.5, "红汤": 9.0},
    }
    cat, diff, tags, hints = sample_slot(aggregate_stats=stats)
    assert cat
    assert diff in ("easy", "medium", "hard")
    assert tags
    assert hints
    assert slot_to_metadata_tags(tags)
