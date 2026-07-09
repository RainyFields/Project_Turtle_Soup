from generator.reference.key_clues import extract_key_clues


def test_desert_body_clues_exclude_surface_terms():
    surface = "沙漠里躺着一具男尸，手里紧紧攥着半根火柴，周围散落着一些行李箱、衣物。"
    solution = (
        "一行人乘坐热气球穿越沙漠，途中热气球故障、超重，必须扔行李减重。"
        "扔完物品还是超重，众人决定抽签：抽中半根短火柴的人，被直接扔下去减重。"
        "死者就是倒霉抽中短火柴的人，被扔下高空坠落死亡。"
    )
    clues = extract_key_clues(surface, solution, max_clues=5)
    assert clues
    assert all(len(c) <= 10 for c in clues)
    joined = "".join(clues)
    assert "抽签" in clues or "抽签" in joined
    assert "热气球" in clues
    assert "沙漠" not in clues
    assert "火柴" not in clues
    assert "男尸" not in clues


def test_turtle_soup_clues_exclude_surface():
    surface = "一个男人走进一家餐馆，点了一碗海龟汤。刚喝了一口，他就崩溃了。为什么？"
    solution = (
        "男人曾和好友在海上遇难，濒临饿死。好友声称自己出去找食物，带回一碗“肉汤”救了他。"
        "男人获救后得知好友再未归来，并被告知海龟汤是当地的特色菜。"
        "他喝下后瞬间明白，当年的“肉汤”其实是好友割下自己的肉为他做的，巨大的愧疚感让他崩溃。"
    )
    clues = extract_key_clues(surface, solution, max_clues=5)
    assert clues
    assert "海龟汤" not in clues
    assert "崩溃" not in clues
    assert "餐馆" not in clues
    joined = "".join(clues)
    assert any(k in joined for k in ("海难", "遇难", "肉汤", "割肉", "愧疚", "好友"))


def test_clues_are_short():
    clues = extract_key_clues("短汤面。", "真相是隐藏的关键词在这里出现。")
    assert all(len(c) <= 12 for c in clues)
