"""Story 2.1 Task 5.2 — ChatContextAssembler 单元测试。

覆盖 AC #2（上下文组装）+ AC #3（token 预算压缩 + 公式/代码块保护）。
"""

import os
from unittest.mock import patch

import pytest

from app.services.chat_context_assembler import (
    DEFAULT_TOKEN_BUDGET,
    AssembledContext,
    ChatContextAssembler,
    CurrentNoteContext,
    _drop_orphan_placeholders,
    _extract_atomic_blocks,
    _resolve_token_budget,
    _restore_atomic_blocks,
)
from app.services.wikilink_context_service import WikilinkNeighborContext


def _make_neighbor(
    slug: str,
    hop: int = 1,
    relationship_type: str | None = None,
    content_summary: str | None = None,
    **fm,
) -> WikilinkNeighborContext:
    return WikilinkNeighborContext(
        slug=slug,
        path=f"节点/{slug}.md",
        hop_distance=hop,
        relationship_type=relationship_type,
        frontmatter=fm,
        content_summary=content_summary,
    )


# ════════════════════════════════════════════════════════════════════
# _resolve_token_budget
# ════════════════════════════════════════════════════════════════════


def test_resolve_budget_default():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("CHAT_CONTEXT_TOKEN_BUDGET", None)
        assert _resolve_token_budget() == DEFAULT_TOKEN_BUDGET


def test_resolve_budget_override():
    assert _resolve_token_budget(4096) == 4096


def test_resolve_budget_env_var():
    with patch.dict(os.environ, {"CHAT_CONTEXT_TOKEN_BUDGET": "2048"}):
        assert _resolve_token_budget() == 2048


def test_resolve_budget_invalid_env_falls_back():
    with patch.dict(os.environ, {"CHAT_CONTEXT_TOKEN_BUDGET": "not-a-number"}):
        assert _resolve_token_budget() == DEFAULT_TOKEN_BUDGET


# ════════════════════════════════════════════════════════════════════
# atomic 块提取/恢复
# ════════════════════════════════════════════════════════════════════


def test_extract_atomic_blocks_latex_double_dollar():
    text = "前面文本 $$E = mc^2$$ 后面文本"
    placeholder, blocks = _extract_atomic_blocks(text)
    assert "<<ATOM_0>>" in placeholder
    assert blocks == ["$$E = mc^2$$"]


def test_extract_atomic_blocks_code_block():
    text = "前面\n```python\nprint('hi')\n```\n后面"
    placeholder, blocks = _extract_atomic_blocks(text)
    assert "<<ATOM_0>>" in placeholder
    assert blocks[0].startswith("```python")


def test_extract_atomic_blocks_mixed():
    text = "$$a$$ 中间 ```code``` 后面 $b$"
    placeholder, blocks = _extract_atomic_blocks(text)
    assert len(blocks) == 3
    # placeholder 内不应残留原 atomic 内容
    assert "$$a$$" not in placeholder
    assert "```code```" not in placeholder


def test_restore_atomic_blocks_roundtrip():
    text = "前 $$x^2$$ 后"
    placeholder, blocks = _extract_atomic_blocks(text)
    restored = _restore_atomic_blocks(placeholder, blocks)
    assert restored == text


def test_drop_orphan_placeholders():
    assert _drop_orphan_placeholders("前 <<ATOM_3>> 后") == "前  后"


# ════════════════════════════════════════════════════════════════════
# count_tokens
# ════════════════════════════════════════════════════════════════════


def test_count_tokens_basic():
    a = ChatContextAssembler()
    assert a.count_tokens("hello world") > 0


def test_count_tokens_empty():
    a = ChatContextAssembler()
    assert a.count_tokens("") == 0


def test_count_tokens_chinese():
    a = ChatContextAssembler()
    # 中文字符通常 2-3 token / char
    assert a.count_tokens("特征值是矩阵") >= 4


# ════════════════════════════════════════════════════════════════════
# compress_content — 公式保护 + 句子边界
# ════════════════════════════════════════════════════════════════════


def test_compress_within_budget_returns_full():
    a = ChatContextAssembler()
    text = "短文本不需要压缩。"
    result = a.compress_content(text, max_tokens=1000)
    assert result == text


def test_compress_max_tokens_zero_returns_empty():
    a = ChatContextAssembler()
    assert a.compress_content("任意文本", max_tokens=0) == ""


def test_compress_protects_latex_formula_block():
    """AC #3 — $$...$$ 整块保留，不被截断破坏内部。"""
    a = ChatContextAssembler()
    text = "句子一。$$\\sum_{i=1}^n x_i = N$$这是公式后的句子。再来一句。"
    result = a.compress_content(text, max_tokens=15)
    if "$$" in result:
        # 公式保留则必须完整两个 $$
        assert result.count("$$") % 2 == 0


def test_compress_protects_code_block():
    """AC #3 — 代码块整块保留，不被中间截断。"""
    a = ChatContextAssembler()
    text = "前文。```python\nprint('hi')\nprint('bye')\n```后文。再后文。"
    result = a.compress_content(text, max_tokens=20)
    if "```" in result:
        # 代码块保留必须 3 个反引号成对
        assert result.count("```") % 2 == 0


def test_compress_truncates_at_sentence_boundary():
    a = ChatContextAssembler()
    text = "句子一。句子二。句子三。句子四。句子五。"
    result = a.compress_content(text, max_tokens=4)
    # 应在句子边界截断（不在句子中间）
    assert result.endswith("。") or result == ""


# ════════════════════════════════════════════════════════════════════
# assemble_context — 优先级填充
# ════════════════════════════════════════════════════════════════════


def _current_note(content: str = "当前笔记内容。") -> CurrentNoteContext:
    return CurrentNoteContext(
        path="节点/Eigenvalues.md",
        content=content,
        frontmatter={"type": "concept", "mastery_score": 0.5},
    )


def test_assemble_includes_current_note_first():
    a = ChatContextAssembler(token_budget=4096)
    result = a.assemble_context(_current_note(), [])
    assert "current_note" in result.sections_included
    assert "节点/Eigenvalues.md" in result.text
    assert result.truncated is False


def test_assemble_with_1hop_neighbor_metadata():
    a = ChatContextAssembler(token_budget=4096)
    n = _make_neighbor(
        "Linear-Independence",
        hop=1,
        relationship_type="prerequisite",
        type="concept",
        mastery_score=0.3,
        tips=["关键性质 A", "关键性质 B"],
    )
    result = a.assemble_context(_current_note(), [n])
    assert "1hop_fm_tips_errors" in result.sections_included
    assert "Linear-Independence" in result.text
    assert "prerequisite" in result.text
    assert "Mastery: 0.30" in result.text
    assert "关键性质 A" in result.text


def test_assemble_with_2hop_neighbor_lower_priority():
    a = ChatContextAssembler(token_budget=4096)
    n1 = _make_neighbor("Direct", hop=1, type="concept")
    n2 = _make_neighbor("Distant", hop=2, type="concept")
    result = a.assemble_context(_current_note(), [n1, n2])
    assert "1hop_fm_tips_errors" in result.sections_included
    assert "2hop_fm" in result.sections_included
    # 1-hop 块在 2-hop 块前
    assert result.text.index("Direct") < result.text.index("Distant")


def test_assemble_with_summary():
    a = ChatContextAssembler(token_budget=4096)
    n = _make_neighbor(
        "Linear-Independence",
        hop=1,
        type="concept",
        content_summary="这是关于线性独立性的简介摘要文本。",
    )
    result = a.assemble_context(_current_note(), [n])
    assert "1hop_summary" in result.sections_included
    assert "线性独立性" in result.text


def test_assemble_drops_neighbors_when_budget_too_small():
    """budget 太小，邻居被 drop（truncated=True）。"""
    a = ChatContextAssembler(token_budget=20)
    n = _make_neighbor("X", hop=1, type="concept", mastery_score=0.5)
    result = a.assemble_context(_current_note("当前笔记很长" * 5), [n])
    assert result.truncated is True


def test_assemble_returns_dataclass():
    a = ChatContextAssembler(token_budget=4096)
    result = a.assemble_context(_current_note(), [])
    assert isinstance(result, AssembledContext)
    assert result.budget == 4096
    assert result.used_tokens > 0
    assert isinstance(result.sections_included, list)


def test_assemble_empty_neighbors_only_current_note():
    a = ChatContextAssembler()
    result = a.assemble_context(_current_note(), [])
    assert result.sections_included == ["current_note"]


def test_assemble_neighbors_sorted_in_text():
    """1-hop / 2-hop 分组顺序：先所有 1-hop，再所有 2-hop。"""
    a = ChatContextAssembler(token_budget=4096)
    neighbors = [
        _make_neighbor("HopTwoA", hop=2, type="concept"),
        _make_neighbor("HopOneA", hop=1, type="concept"),
        _make_neighbor("HopTwoB", hop=2, type="concept"),
        _make_neighbor("HopOneB", hop=1, type="concept"),
    ]
    result = a.assemble_context(_current_note(), neighbors)
    # 1-hop 段先于 2-hop 段
    one_hop_idx = result.text.index("1-hop")
    two_hop_idx = result.text.index("2-hop")
    assert one_hop_idx < two_hop_idx
