"""
RAG-P0 (2026-05-10) — A1+A2+A4 doc_type filtering & whiteboard boilerplate stripping.

Why these tests:
- A1: frontmatter.type → metadata.doc_type / doc.doc_type column (source-aware filter input)
- A2: _build_where_filters supports doc_type IN / NOT IN with NULL fallback for legacy rows
- A4: whiteboard bodies are stripped of dataviewjs / HTML comments / callouts /
      Recent Activity, so MOC/index whiteboards stop generating high-rank
      boilerplate chunks like "你在这白板里能做什么\\n选中任意文本→Cmd+Shift+D".
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))

from agentic_rag.clients.lancedb_client import LanceDBClient


# ─────────────────────────────────────────────────────────────────
# A1 — doc_type extracted from frontmatter, defaults to 'note'
# ─────────────────────────────────────────────────────────────────


def test_split_md_by_heading_extracts_doc_type_whiteboard():
    content = """---
type: whiteboard
board_name: "线性代数"
---

# 线性代数

## Concepts

- [[节点/特征值]]
- [[节点/线性变换]]

real prose here
"""
    chunks = LanceDBClient._split_md_by_heading(content, "原白板/线性代数.md")
    assert chunks, "non-empty whiteboard with prose should produce chunks"
    for c in chunks:
        assert c["doc_type"] == "whiteboard"


def test_split_md_by_heading_extracts_doc_type_default_note():
    content = """---
course: CS 61B
---

# Recursion

Definition: a function that calls itself.
"""
    chunks = LanceDBClient._split_md_by_heading(content, "节点/recursion.md")
    assert chunks
    assert all(c["doc_type"] == "note" for c in chunks)


def test_split_md_by_heading_no_frontmatter_defaults_to_note():
    content = "# Linear algebra\n\nVectors and matrices."
    chunks = LanceDBClient._split_md_by_heading(content, "节点/linalg.md")
    assert chunks
    assert all(c["doc_type"] == "note" for c in chunks)


# ─────────────────────────────────────────────────────────────────
# A2 — _build_where_filters source-aware doc_type SQL generation
# ─────────────────────────────────────────────────────────────────


def _client():
    # _build_where_filters is an instance method but doesn't touch self state
    return LanceDBClient.__new__(LanceDBClient)


def test_where_filters_exclude_whiteboard_with_null_fallback():
    clauses = _client()._build_where_filters(exclude_doc_types=["whiteboard"])
    assert any(
        "doc_type NOT IN ('whiteboard')" in c and "doc_type IS NULL" in c
        for c in clauses
    ), "exclude must pass legacy NULL rows through, not drop them"


def test_where_filters_include_note_with_null_fallback():
    clauses = _client()._build_where_filters(doc_type=["note"])
    assert any(
        "doc_type IN ('note')" in c and "doc_type IS NULL" in c for c in clauses
    ), "include 'note' must also accept legacy NULL rows (treated as note)"


def test_where_filters_include_lecture_strict_no_null_fallback():
    clauses = _client()._build_where_filters(doc_type=["lecture", "discussion"])
    sql = " ".join(clauses)
    assert "doc_type IN ('lecture', 'discussion')" in sql
    assert "IS NULL" not in sql, (
        "include without 'note' must be strict — NULL rows can't be assumed lecture"
    )


def test_where_filters_compose_with_other_filters():
    clauses = _client()._build_where_filters(
        subject="cs_61b",
        course_id="CS 61B",
        exclude_doc_types=["whiteboard"],
    )
    sql = " ".join(clauses)
    assert "subject = 'cs_61b'" in sql
    assert "course = 'CS 61B'" in sql
    assert "doc_type NOT IN" in sql


def test_where_filters_no_doc_type_param_unchanged():
    clauses = _client()._build_where_filters(subject="cs_61b")
    sql = " ".join(clauses)
    assert "doc_type" not in sql, "absent doc_type/exclude_doc_types → no clause"


# ─────────────────────────────────────────────────────────────────
# A4 — _strip_whiteboard_boilerplate removes templated content
# ─────────────────────────────────────────────────────────────────


WHITEBOARD_SAMPLE = """
> [!info]+ 原白板说明（扁平架构 · round-11）
> 这是学习主题"线性代数"的原白板。
>
> ## 你在这白板里能做什么
> - Cmd+Shift+D 让 AI 派生新节点

## Concepts

<!--
本 section 由三处维护
-->

- [[节点/特征值]]

## 🔗 节点关系图

```dataviewjs
const here = dv.current().file.link;
chart += "graph TD\\n";
```

> **白板 = 节点关系**

## Recent Activity

- 2026-04-30T08:42:11Z: Whiteboard created
- 2026-05-01T09:00:00Z: Concept added
"""


def test_strip_whiteboard_removes_dataviewjs():
    out = LanceDBClient._strip_whiteboard_boilerplate(WHITEBOARD_SAMPLE)
    assert "dataviewjs" not in out
    assert "graph TD" not in out
    assert "dv.current" not in out


def test_strip_whiteboard_removes_html_comments():
    out = LanceDBClient._strip_whiteboard_boilerplate(WHITEBOARD_SAMPLE)
    assert "本 section 由三处维护" not in out


def test_strip_whiteboard_removes_admonition_callouts():
    out = LanceDBClient._strip_whiteboard_boilerplate(WHITEBOARD_SAMPLE)
    assert "原白板说明" not in out
    assert "你在这白板里能做什么" not in out
    assert "Cmd+Shift+D 让 AI 派生新节点" not in out


def test_strip_whiteboard_preserves_concepts_section():
    out = LanceDBClient._strip_whiteboard_boilerplate(WHITEBOARD_SAMPLE)
    assert "## Concepts" in out
    assert "[[节点/特征值]]" in out


def test_strip_whiteboard_preserves_user_blockquote_prose():
    # Plain blockquotes (without [!type]+ admonition syntax) are user prose
    # and must be kept.
    out = LanceDBClient._strip_whiteboard_boilerplate(WHITEBOARD_SAMPLE)
    assert "白板 = 节点关系" in out


def test_strip_whiteboard_removes_recent_activity():
    out = LanceDBClient._strip_whiteboard_boilerplate(WHITEBOARD_SAMPLE)
    assert "Recent Activity" not in out
    assert "Whiteboard created" not in out


def test_strip_whiteboard_idempotent():
    once = LanceDBClient._strip_whiteboard_boilerplate(WHITEBOARD_SAMPLE)
    twice = LanceDBClient._strip_whiteboard_boilerplate(once)
    assert once == twice


def test_strip_whiteboard_size_reduction():
    # Real-world reduction: ~85%+ on actual whiteboard files
    before = len(WHITEBOARD_SAMPLE)
    after = len(LanceDBClient._strip_whiteboard_boilerplate(WHITEBOARD_SAMPLE))
    assert after < before * 0.5, (
        f"expected >50% reduction, got {after}/{before} = {after / before:.1%}"
    )


# ─────────────────────────────────────────────────────────────────
# A4 integration — whiteboard with only boilerplate produces no chunks
# ─────────────────────────────────────────────────────────────────


def test_whiteboard_with_only_boilerplate_skipped_entirely():
    content = """---
type: whiteboard
---

# 空白板

> [!info]+ 原白板说明
> 模板说明

```dataviewjs
return "auto-generated";
```

## Recent Activity

- 2026-04-30: created
"""
    chunks = LanceDBClient._split_md_by_heading(content, "原白板/empty.md")
    assert chunks == [], (
        "whiteboard with only boilerplate should produce zero chunks "
        "(saves storage + index time + force_rebuild churn)"
    )
