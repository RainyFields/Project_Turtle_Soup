from __future__ import annotations

import re
from typing import Iterable, List, Set, Tuple


# Common content words for forward maximum matching (no external segmenter).
_ZH_WORDS: Tuple[str, ...] = tuple(
    sorted(
        {
            w
            for w in """
            英语 英语书 语文 语文课 学渣 同桌 上课 睡觉 学生 老师 回答问题
            红眼 红眼病 租客 隔壁 洞里 红色 房东 出租屋 墙壁
            绝症 推下 推下去 失足 摔死 山顶 女儿 妻子 爬山 锻炼 制裁 可爱
            追踪器 逃犯 伪装 击毙 拘捕 硬币 警方 通缉 藏身处 施舍 空碗
            热气球 抽签 故障 超重 减重 坠落 行李 扔下 穿越 沙漠 倒霉 高空
            海难 遇难 好友 肉汤 割肉 愧疚 特色菜 饿死 获救 归来 崩溃 餐馆
            盲人 砍手 欺骗 探险 食物 鼓掌 蜡烛 聚会 无法忍受 砍下 双手 砍下来
            海难 遇难 割肉 濒临 学渣 英语书 割下 海上 绝症
            服毒 自尽 剪掉 血流 玩笑 当真 带一 六岁 一岁 新闻 母亲 儿子
            邻居 双倍 报复 富人 穷人 接济 瞎眼 愿望 上帝 食物 生活用品
            头颅 排风扇 劫匪 入室 搏斗 组织液 割掉 干枯 浴室 警察 现场
            报警 发现 死亡 杀死 藏 躲 藏 躲藏 藏身处 信号 抓取 过程
            治疗 经济 条件 生活 正常 法律 风景 打算 转过 突然 不久 生下
            新闻 帮忙 出门 叮嘱 晚上 血流不止 打死 自尽 服毒自尽
            疾病 患者 病人 手术 医院 医生 护士 药物 中毒 自杀 他杀 谋杀
            绑架 抢劫 盗窃 诈骗 陷阱 误会 真相 秘密 隐藏 伪装 假扮 身份
            记忆 回忆 忘记 想起 明白 瞬间 意识到 愧疚感 巨大 崩溃
            抽签 减重 故障 超重 扔下 坠落 高空 热气球 穿越
            海难 遇难 好友 肉汤 割肉 愧疚 特色菜 濒临 获救
            追踪器 逃犯 伪装 击毙 拘捕 硬币 警方 通缉
            绝症 推下 推下去 失足 摔死 山顶
            红眼病 隔壁 洞里
            英语书 语文课 学渣 同桌
            头颅 排风扇 劫匪 入室 搏斗 组织液
            邻居 双倍 报复 富人 穷人 接济
            盲人 砍手 欺骗 探险
            """.split()
            if len(w) >= 2
        },
        key=len,
        reverse=True,
    )
)

_GENERIC = frozenset(
    """
    超重 倒霉 扔下 发现 打算 不久 巨大 母亲 女儿 儿子 男人 女人 自己 死亡
    回答 上课 睡觉 打算 突然 转过 一天 一次 一起 一直 可能 好像 实际上
    没想到 瞬间 制裁 可爱 归来 食物 获救 明白 学生 老师 帮忙 帮忙 风景
    回答问题 山顶 锻炼 经济 条件 生活 正常 法律 风景 抱起 转过头来
    治疗 生下 新闻
    """.split()
)

_TWIST_HINT = re.compile(r"(决定|原来|其实|没想到|明白|瞬间|当真|伪装|击毙|推下|抽签|剪掉)")

_STOPWORDS = frozenset(
    """
    一个 一些 这个 那个 就是 已经 仍然 还是 他们 我们 你们 可以 没有 不是
    因为 所以 如果 但是 然后 之后 之前 当时 当年 今天 明天 必须 进行 出现
    直接 其实 非常 可能 应该 需要 知道 明白 觉得 认为 开始 最后 为什么
    一行 众人 决定 途中 扔完 物品 死者 男人 女人 自己 怎么 什么 于是 便
    的人 任何 每个 其中 其他 以及 并且 这样 那样 所有 这位 那位 可能 好像
    当时 并不 一直 几年 后来 一天 一次 一段 一起 一下 一种 一位 一件
    回答问题 一句话 上课 睡觉
    """.split()
)

_PARTICLE_SPLIT = re.compile(r"[的了是在把被给和与及或但于是所以从向对将着过也要还又再很更最]")
_PUNCT_SPLIT = re.compile(r"[，、：；""''（）()《》【】\\[\\]\\s]+")
_CLAUSE_SPLIT = re.compile(r"[。！？；\n]+")
_HAN = re.compile(r"[\u4e00-\u9fff]+")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def _surface_fragments(surface: str, *, max_len: int = 4) -> Set[str]:
    surface = _normalize(surface)
    return {surface[i : i + n] for n in range(2, max_len + 1) for i in range(len(surface) - n + 1)}


def _in_surface(term: str, surface: str) -> bool:
    term = _normalize(term)
    surface = _normalize(surface)
    if not term:
        return False
    if term in surface:
        return True
    if len(term) >= 3:
        return any(term[i : i + 3] in surface for i in range(len(term) - 2))
    return False


def _forbidden_spans(solution: str, surface_frags: Set[str]) -> List[Tuple[int, int]]:
    spans: List[Tuple[int, int]] = []
    for frag in surface_frags:
        if len(frag) < 2:
            continue
        start = 0
        while True:
            idx = solution.find(frag, start)
            if idx < 0:
                break
            spans.append((idx, idx + len(frag)))
            start = idx + 1
    return spans


def _overlaps_forbidden_span(term: str, solution: str, spans: List[Tuple[int, int]]) -> bool:
    start = 0
    while True:
        idx = solution.find(term, start)
        if idx < 0:
            return False
        end = idx + len(term)
        for s, e in spans:
            if not (end <= s or idx >= e):
                return True
        start = idx + 1


def _forward_max_match(text: str, lexicon: Iterable[str]) -> List[str]:
    words: List[str] = []
    i = 0
    while i < len(text):
        matched = ""
        for length in range(min(6, len(text) - i), 1, -1):
            piece = text[i : i + length]
            if piece in lexicon:
                matched = piece
                break
        if matched:
            words.append(matched)
            i += len(matched)
        else:
            i += 1
    return words


def _quoted_terms(solution: str) -> Set[str]:
    terms: Set[str] = set()
    for m in re.finditer(r"[“\"']([^”\"']+)[”\"']", solution):
        chunk = _normalize(m.group(1))
        if 2 <= len(chunk) <= 8 and _HAN.fullmatch(chunk):
            terms.add(chunk)
        else:
            terms.update(w for w in _forward_max_match(chunk, _ZH_WORDS) if len(w) >= 2)
    return terms


def _particle_chunks(text: str) -> Set[str]:
    chunks: Set[str] = set()
    for part in _PARTICLE_SPLIT.split(text):
        part = part.strip()
        if 2 <= len(part) <= 6 and _HAN.fullmatch(part):
            chunks.add(part)
        for sub in _PUNCT_SPLIT.split(part):
            sub = sub.strip()
            if 2 <= len(sub) <= 6 and _HAN.fullmatch(sub):
                chunks.add(sub)
    return chunks


def _tail_terms(clause: str) -> Set[str]:
    """Prefer clause-ending keywords (twist often appears at clause end)."""
    terms: Set[str] = set()
    for piece in _PUNCT_SPLIT.split(clause):
        piece = piece.strip()
        if len(piece) < 2:
            continue
        for length in (4, 3, 2):
            if len(piece) >= length:
                terms.add(piece[-length:])
    return terms


def _is_valid_term(term: str) -> bool:
    if not _HAN.fullmatch(term) or len(term) < 2 or len(term) > 6:
        return False
    if term in _STOPWORDS:
        return False
    if term[0] in "的了吗呢吧啊" or term[-1] in "的了吗呢吧啊":
        return False
    if "死亡" in term or term in {"男人", "女人", "自己", "他们", "我们", "一行", "众人"}:
        return False
    if "的是" in term or "在一" in term or "了一" in term:
        return False
    if "的" in term[:-1]:
        return False
    return True


def _score(term: str, *, source: str, surface: str, forbidden: List[Tuple[int, int]], solution: str) -> float:
    if not _is_valid_term(term):
        return -1.0
    if _in_surface(term, surface):
        return -1.0
    if _overlaps_forbidden_span(term, solution, forbidden):
        return -1.0

    score = 0.0
    if source == "lexicon":
        score += 1.0
    elif source == "quoted":
        score += 0.95
    elif source == "particle":
        score += 0.65
    else:
        score += 0.45

    if len(term) == 2:
        score += 0.35
    elif len(term) == 3:
        score += 0.5
    elif len(term) == 4:
        score += 0.45
    else:
        score += 0.25

    score += min(solution.count(term), 3) * 0.08

    if term in _GENERIC:
        score -= 0.4
    if _TWIST_HINT.search(solution[max(0, solution.find(term) - 4) : solution.find(term) + len(term)]):
        score += 0.25

    return score


def extract_key_clues(
    surface: str,
    solution: str,
    *,
    max_clues: int = 5,
    min_clues: int = 3,
) -> List[str]:
    """
    Extract short keywords from solution via lexicon matching and clause heuristics.
    Filters out terms already implied by the surface or repeated surface phrases.
    """
    surface_n = _normalize(surface)
    solution_n = _normalize(solution)
    if not solution_n:
        return []

    frags = _surface_fragments(surface_n)
    forbidden = _forbidden_spans(solution_n, frags)
    lexicon = set(_ZH_WORDS)

    scored: List[Tuple[float, str, str]] = []
    seen: Set[str] = set()

    def add(term: str, source: str) -> None:
        term = _normalize(term)
        if not term or term in seen:
            return
        seen.add(term)
        s = _score(term, source=source, surface=surface_n, forbidden=forbidden, solution=solution_n)
        if s >= 0.5:
            scored.append((s, term, source))

    for term in _quoted_terms(solution_n):
        add(term, "quoted")

    for term in _forward_max_match(solution_n, lexicon):
        add(term, "lexicon")

    for clause in _CLAUSE_SPLIT.split(solution_n):
        cleaned = clause
        for frag in sorted(frags, key=len, reverse=True):
            if len(frag) >= 2:
                cleaned = cleaned.replace(frag, " ")
        for term in _particle_chunks(cleaned):
            add(term, "particle")
        for term in _tail_terms(cleaned):
            add(term, "tail")

    scored.sort(key=lambda x: (-x[0], -len(x[1]), x[1]))

    selected: List[str] = []
    for pass_sources in (("lexicon", "quoted"), ("particle", "tail")):
        for _, term, source in scored:
            if source not in pass_sources:
                continue
            if any(term in other or other in term for other in selected):
                continue
            selected.append(term)
            if len(selected) >= max_clues:
                break
        if len(selected) >= max_clues:
            break

    if len(selected) < min_clues:
        for _, term, _ in scored:
            if term not in selected:
                selected.append(term)
            if len(selected) >= min_clues:
                break

    return selected[:max_clues]
