"""Story 2.5.Y Task 5 — cypher_helpers 单元测试.

覆盖 AC #5:
- cypher_with_group_filter 注入 WHERE 子句 + params
- 空 group_id 抛 ValueError (严格必填)
- 各种 base_query 场景: RETURN / WITH / SET / 已有 WHERE
- node_alias 自定义
- assert_group_id_required 防御性入口校验

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-y-isolation-hardening-subject-config-reuse.md
"""

from __future__ import annotations

import pytest

from app.utils.cypher_helpers import (
    allow_cross_vault,
    assert_group_id_required,
    cypher_with_group_filter,
)


# ════════════════════════════════════════════════════════════════════
# cypher_with_group_filter — 严格必填校验
# ════════════════════════════════════════════════════════════════════


def test_empty_group_id_raises_value_error():
    with pytest.raises(ValueError, match="group_id is required"):
        cypher_with_group_filter("MATCH (n) RETURN n", "")


def test_whitespace_group_id_raises():
    with pytest.raises(ValueError):
        cypher_with_group_filter("MATCH (n) RETURN n", "   ")


def test_none_group_id_raises():
    with pytest.raises(ValueError):
        cypher_with_group_filter("MATCH (n) RETURN n", None)  # type: ignore[arg-type]


# ════════════════════════════════════════════════════════════════════
# cypher_with_group_filter — 基础注入 (RETURN 前)
# ════════════════════════════════════════════════════════════════════


def test_inject_before_return_clause():
    """MATCH (n) RETURN n → MATCH (n) WHERE n.group_id = $group_id RETURN n."""
    q, params = cypher_with_group_filter("MATCH (n:Concept) RETURN n", "vault:cs_61b")
    assert "WHERE n.group_id = $group_id" in q
    assert q.index("WHERE") < q.index("RETURN")  # filter 在 RETURN 前
    assert params == {"group_id": "vault:cs_61b"}


def test_inject_with_unicode_group_id():
    q, params = cypher_with_group_filter("MATCH (n) RETURN n", "vault:数学:离散")
    assert "WHERE n.group_id = $group_id" in q
    assert params["group_id"] == "vault:数学:离散"


# ════════════════════════════════════════════════════════════════════
# cypher_with_group_filter — 不同 base_query 场景
# ════════════════════════════════════════════════════════════════════


def test_inject_before_with_clause():
    """MATCH (n) WITH ... → 注入到 WITH 前."""
    q, _ = cypher_with_group_filter(
        "MATCH (n:Concept) WITH n, count(*) as cnt RETURN cnt",
        "vault:cs_61b",
    )
    assert "WHERE" in q
    # filter 在 WITH 前, WITH 在 RETURN 前
    assert q.index("WHERE") < q.index("WITH")


def test_inject_before_set_clause():
    """MATCH (n) SET n.x = 1 → 注入到 SET 前."""
    q, _ = cypher_with_group_filter(
        "MATCH (n:Concept) SET n.modified = true", "vault:cs_61b"
    )
    assert "WHERE n.group_id = $group_id" in q
    assert q.index("WHERE") < q.index("SET")


def test_inject_before_delete_clause():
    """MATCH (n) DELETE n → 注入到 DELETE 前 (防误删跨 vault 数据)."""
    q, _ = cypher_with_group_filter("MATCH (n:Concept) DELETE n", "vault:cs_61b")
    assert q.index("WHERE") < q.index("DELETE")


def test_inject_into_query_without_keywords():
    """无 RETURN / WITH 等关键字 → 追加到末尾."""
    q, _ = cypher_with_group_filter("MATCH (n:Concept)", "vault:cs_61b")
    assert q.endswith("WHERE n.group_id = $group_id")


# ════════════════════════════════════════════════════════════════════
# cypher_with_group_filter — 已有 WHERE 子句 (where_keyword="AND")
# ════════════════════════════════════════════════════════════════════


def test_append_to_existing_where_with_and_keyword():
    """已有 WHERE 子句 → 调用方用 where_keyword='AND' 追加."""
    q, params = cypher_with_group_filter(
        "MATCH (n:Concept) WHERE n.mastery_score > 0.5 RETURN n",
        "vault:cs_61b",
        where_keyword="AND",
    )
    assert "AND n.group_id = $group_id" in q
    assert q.count("WHERE") == 1  # 仅原 WHERE, 不重复


# ════════════════════════════════════════════════════════════════════
# cypher_with_group_filter — node_alias 自定义
# ════════════════════════════════════════════════════════════════════


def test_custom_node_alias():
    """node_alias='c' → c.group_id 而非 n.group_id."""
    q, _ = cypher_with_group_filter(
        "MATCH (c:Concept) RETURN c", "vault:cs_61b", node_alias="c"
    )
    assert "c.group_id = $group_id" in q
    assert "n.group_id" not in q


# ════════════════════════════════════════════════════════════════════
# assert_group_id_required — 防御性入口校验
# ════════════════════════════════════════════════════════════════════


def test_assert_group_id_required_valid_returns_stripped():
    assert assert_group_id_required("vault:cs_61b") == "vault:cs_61b"
    assert assert_group_id_required("  vault:cs_61b  ") == "vault:cs_61b"


def test_assert_group_id_required_empty_raises():
    with pytest.raises(ValueError, match="group_id is required"):
        assert_group_id_required("")


def test_assert_group_id_required_whitespace_raises():
    with pytest.raises(ValueError):
        assert_group_id_required("   \n\t  ")


def test_assert_group_id_required_none_raises():
    with pytest.raises(ValueError):
        assert_group_id_required(None)


def test_assert_group_id_required_context_appears_in_error():
    """context 参数应出现在 error message (帮助调试)."""
    with pytest.raises(ValueError, match="memory_service.search"):
        assert_group_id_required("", context="memory_service.search")


# ════════════════════════════════════════════════════════════════════
# 业务场景 — 模拟实际调用
# ════════════════════════════════════════════════════════════════════


def test_typical_concept_search_query():
    """场景 1: 搜节点 by description."""
    q, params = cypher_with_group_filter(
        "MATCH (c:Concept) WHERE c.description CONTAINS $query RETURN c",
        "vault:cs_61b",
        node_alias="c",
        where_keyword="AND",
    )
    assert "AND c.group_id = $group_id" in q
    assert params == {"group_id": "vault:cs_61b"}


def test_typical_misconception_query():
    """场景 2: 搜 misconception 节点."""
    q, _ = cypher_with_group_filter(
        "MATCH (m:Misconception) RETURN m ORDER BY m.created_at DESC",
        "vault:cs_61b",
        node_alias="m",
    )
    # filter 应在 RETURN 前 (而非 ORDER BY 前)
    assert q.index("WHERE") < q.index("RETURN")


# ════════════════════════════════════════════════════════════════════
# Wave-5 Stage C — allow_cross_vault decorator + helper return contract
# ════════════════════════════════════════════════════════════════════


def test_allow_cross_vault_decorator_marks_function():
    """Decorator must stamp _allow_cross_vault_reason on the wrapped fn."""

    @allow_cross_vault(reason="admin migration scans all vaults")
    def scan_all_group_ids():
        return "ok"

    assert (
        scan_all_group_ids._allow_cross_vault_reason
        == "admin migration scans all vaults"
    )
    # Wrapper must remain the original callable (no wraps swap; pass-through).
    assert scan_all_group_ids() == "ok"


def test_cypher_with_group_filter_returns_filtered_query():
    """Helper must (a) inject WHERE n.group_id = $group_id, (b) return params dict."""
    q, params = cypher_with_group_filter(
        "MATCH (n:Concept) RETURN n.id", "vault:cs_61b"
    )
    # (a) WHERE clause injected before RETURN
    assert "WHERE n.group_id = $group_id" in q
    assert q.index("WHERE") < q.index("RETURN")
    # (b) params dict carries the group_id (ready for tx.run(q, **params))
    assert params == {"group_id": "vault:cs_61b"}
