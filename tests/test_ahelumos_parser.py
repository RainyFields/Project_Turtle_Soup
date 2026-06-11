from generator.reference.ahelumos import parse_detail_page, parse_index_cards

_LIST_SNIPPET = """
<a href="/soups/128" class="cursor-pointer group block">
  <h3 class="text-xl font-serif font-bold line-clamp-2">测试标题</h3>
  <span class="shrink-0 inline-flex items-center gap-1 rounded-full"><span>10.0</span></span>
  <span class="inline-flex rounded-full border border-neutral-200 bg-neutral-50 px-2 py-0.5 font-mono text-[10px] text-neutral-500">恐怖</span>
  <p class="text-neutral-600 line-clamp-2 font-medium">汤面摘要文字</p>
  <span>作者：tester</span>
</a>
"""

_DETAIL_SNIPPET = """
<div data-soup-id="128" class="js-flip-root">
<!-- 正面：汤面 -->
<h3>测试标题</h3>
<p class="text-base whitespace-pre-wrap !mt-4">完整汤面内容</p>
<!-- 背面：汤底 -->
<p class="text-base whitespace-pre-wrap !mt-4">完整汤底真相</p>
</div>
<div id="ratingSummaryText">10.0 分</div>
<span>By tester</span>
"""


def test_parse_index_card():
    rows = parse_index_cards(_LIST_SNIPPET)
    assert len(rows) == 1
    assert rows[0]["external_id"] == "128"
    assert rows[0]["title"] == "测试标题"
    assert rows[0]["rating"] == 10.0
    assert "恐怖" in rows[0]["tags"]


def test_parse_detail_page():
    row = parse_detail_page(_DETAIL_SNIPPET, soup_id="128")
    assert row["surface"] == "完整汤面内容"
    assert row["solution"] == "完整汤底真相"
    assert row["rating"] == 10.0
