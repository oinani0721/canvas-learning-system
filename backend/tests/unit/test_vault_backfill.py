"""Phase 4.5 (GRAPHITI-NATIVE-MEMORY-2026-06-10): vault 回填单测。"""

import pytest

from app.services.vault_backfill import backfill_vault, extract_callouts

# ═══════════════════════════════════════════════════════════════════════════════
# extract_callouts — 纯解析
# ═══════════════════════════════════════════════════════════════════════════════


def test_extract_single_tip():
    md = "# 标题\n\n> [!tip]+ 先想 base case\n\n正文"
    assert extract_callouts(md) == [("tip", "先想 base case")]


def test_extract_multiline_callout():
    md = "> [!question]+ 为什么递归要终止\n> 因为否则栈会爆\n> 第二行"
    assert extract_callouts(md) == [
        ("question", "为什么递归要终止 因为否则栈会爆 第二行")
    ]


def test_extract_error_callout():
    md = "> [!error]+ 我把 base case 写漏了"
    assert extract_callouts(md) == [("error", "我把 base case 写漏了")]


def test_skip_relation_quote_video():
    md = (
        "> [!relation/related_to]+ 已派生为 [[节点/x]] · 相关\n"
        "> [!quote]+ 派生起点\n"
        "> 引用正文\n"
        "> [!video]- 播放器\n"
        "> [!tip] 真批注\n"
    )
    assert extract_callouts(md) == [("tip", "真批注")]


def test_multiple_callouts_separated():
    md = "> [!tip] A\n\n中间正文\n\n> [!note] B\n> 续行"
    assert extract_callouts(md) == [("tip", "A"), ("note", "B 续行")]


def test_empty_callout_dropped():
    assert extract_callouts("> [!tip]+\n") == []


# ═══════════════════════════════════════════════════════════════════════════════
# backfill_vault — dry-run 统计 + execute 真调 writer (spy)
# ═══════════════════════════════════════════════════════════════════════════════


def _make_vault(tmp_path):
    (tmp_path / "节点").mkdir()
    (tmp_path / "节点" / "recursion.md").write_text(
        "---\n"
        "type: concept\n"
        "relationships:\n"
        "  - type: refines\n"
        '    target: "[[lecture 2]]"\n'
        "    description: 我想单独讨论这个点\n"
        "---\n"
        "> [!tip]+ 先想 base case\n"
        "> [!error]+ 写漏了终止条件\n",
        encoding="utf-8",
    )
    (tmp_path / "节点" / "plain.md").write_text("无批注", encoding="utf-8")
    return tmp_path


async def test_dry_run_counts_without_writing(tmp_path, monkeypatch):
    vault = _make_vault(tmp_path)
    calls = []

    async def spy(*a, **kw):
        calls.append(kw)

    for fn in ("write_callout", "write_error", "write_relation_reason"):
        monkeypatch.setattr(f"app.services.graphiti_structured_writer.{fn}", spy)

    stats = await backfill_vault(str(vault), object(), None, "vault:g", execute=False)
    assert stats["callouts"] == 1
    assert stats["errors"] == 1
    assert stats["relations"] == 1
    assert stats["files"] == 1
    assert calls == []  # dry-run 不写


async def test_execute_calls_writers(tmp_path, monkeypatch):
    vault = _make_vault(tmp_path)
    written = {"callout": [], "error": [], "relation": []}

    async def spy_callout(driver, embedder, **kw):
        written["callout"].append(kw)

    async def spy_error(driver, embedder, **kw):
        written["error"].append(kw)

    async def spy_rel(driver, embedder, **kw):
        written["relation"].append(kw)

    monkeypatch.setattr(
        "app.services.graphiti_structured_writer.write_callout", spy_callout
    )
    monkeypatch.setattr(
        "app.services.graphiti_structured_writer.write_error", spy_error
    )
    monkeypatch.setattr(
        "app.services.graphiti_structured_writer.write_relation_reason", spy_rel
    )

    stats = await backfill_vault(str(vault), object(), None, "vault:g", execute=True)
    assert stats["failed"] == 0
    assert written["callout"][0]["text"] == "先想 base case"
    assert written["callout"][0]["node_id"] == "recursion"
    assert written["error"][0]["description"] == "写漏了终止条件"
    assert written["relation"][0]["target_node_id"] == "lecture 2"
    assert written["relation"][0]["reason"] == "我想单独讨论这个点"
