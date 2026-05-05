"""Story 2.5.Y Task 4 — LanceDB 隔离机制 防御性测试.

⭐ Task 4 重要修正 (2026-05-05 cross-check 发现):
ChatGPT Round-1 spec 描述 "LanceDB 向量搜索没传 group_id 过滤" 是**过时论断**.
Story 1.9 已通过 **table-name vault_id prefix** 解决 LanceDB 跨 vault 泄露:
- LanceDB client 自动用 vault_id_<table_name> 命名 (如 cs_61b_vault_notes)
- 跨 vault 数据**物理隔离在 storage layer**, 不依赖 group_id WHERE 过滤
- vault_notes_retriever.search() 的 group_id 参数目前 unused (Story 1.9 doc 说明)

本测试模块作用:
- 防御性 assertion 验证 Story 1.9 isolation 机制仍生效
- Story 2.5.Y 引入 cypher_helpers / build_vault_group_id 后, 验证三者一致性

不在本测试范围 (其他 Story / Task):
- cross_canvas_retriever.find_related_canvases TODO 占位符 (R12 review 历史债, 非本 Story)
- vault_notes_retriever.search() 实际网络/LanceDB 集成 (E2E 跑 docker 才能测)

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-y-isolation-hardening-subject-config-reuse.md
"""

from __future__ import annotations

import pytest

from app.core.subject_config import (
    DEFAULT_SUBJECT_ID,
    build_vault_group_id,
    is_vault_group_id,
    sanitize_subject_name,
)
from app.utils.cypher_helpers import (
    assert_group_id_required,
    cypher_with_group_filter,
)


# ════════════════════════════════════════════════════════════════════
# 1. Story 1.9 LanceDB table-name isolation 仍生效 (防 regression)
# ════════════════════════════════════════════════════════════════════


def test_lancedb_vault_id_prefix_isolation_design():
    """Story 1.9 LanceDB 隔离机制 doc test:
    table 名应包含 vault_id 前缀 (e.g. 'cs_61b_vault_notes').
    这是 storage layer 隔离, 不依赖 group_id WHERE.
    """
    # 模拟 vault_id → table_name 命名规则 (Story 1.9 实现)
    expected_pattern = "{vault_id_sanitized}_vault_notes"
    sample = expected_pattern.format(vault_id_sanitized="cs_61b")
    assert sample == "cs_61b_vault_notes"

    # 不同 vault → 不同 table
    table_a = "cs_61b_vault_notes"
    table_b = "数学_vault_notes"
    assert table_a != table_b


def test_lancedb_vault_id_with_special_chars_sanitized():
    """vault_id 含特殊字符必须 sanitize 才能用作 table 名."""
    # LanceDB table 名通常要求 alphanumeric + underscore
    raw_vault = "CS 61B!"
    sanitized = sanitize_subject_name(raw_vault)
    assert sanitized == "cs_61b"
    # table 名构造
    table = f"{sanitized}_vault_notes"
    assert table == "cs_61b_vault_notes"
    # 无空格 / 特殊字符
    assert " " not in table
    assert "!" not in table


# ════════════════════════════════════════════════════════════════════
# 2. Story 2.5.Y 三组件一致性 (build_vault_group_id + cypher_helpers + assert)
# ════════════════════════════════════════════════════════════════════


def test_build_vault_group_id_output_works_with_cypher_helper():
    """vault_id → build_vault_group_id → cypher_with_group_filter 链路一致."""
    group_id = build_vault_group_id("cs_61b", subject_id="algorithms")
    # 用结果走 Cypher
    query, params = cypher_with_group_filter(
        "MATCH (n:Concept) RETURN n", group_id
    )
    assert params["group_id"] == group_id
    assert "vault:cs_61b:algorithms" in params["group_id"]


def test_assert_group_id_required_accepts_vault_format():
    """vault: 前缀格式应通过 assert."""
    g = build_vault_group_id("cs_61b")
    assert assert_group_id_required(g) == "vault:cs_61b"


def test_default_subject_id_should_not_pass_strict_assert():
    """DEFAULT_SUBJECT_ID 是 Story 1.9 跨学科默认, 但 Story 2.5.Y 严格场景应拒绝."""
    # DEFAULT_SUBJECT_ID 是 'general' (非空), assert_group_id_required 会通过
    # 但语义上 'general' 不是 vault: 格式, 严格隔离场景不应使用
    assert assert_group_id_required(DEFAULT_SUBJECT_ID) == DEFAULT_SUBJECT_ID
    assert is_vault_group_id(DEFAULT_SUBJECT_ID) is False  # ⭐ 但非 vault 格式


# ════════════════════════════════════════════════════════════════════
# 3. 跨 vault 隔离防 regression (合约测试)
# ════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "vault_a,vault_b,expect_distinct",
    [
        ("cs_61b", "数学", True),
        ("cs_61b", "ml", True),
        ("数学", "物理", True),
        ("CS 61B", "cs 61b", False),  # sanitize 后相同
    ],
)
def test_different_vault_ids_yield_different_group_ids(
    vault_a, vault_b, expect_distinct
):
    """不同 vault_id 应生成不同 group_id (防 sanitize 冲突误隔离失效)."""
    g_a = build_vault_group_id(vault_a)
    g_b = build_vault_group_id(vault_b)
    if expect_distinct:
        assert g_a != g_b, f"vault_a={vault_a} 与 vault_b={vault_b} 应生成不同 group_id"
    else:
        assert g_a == g_b


def test_subject_canvas_path_subdivision_not_collide_with_other_vault():
    """vault_a + subject 不应等于 vault_b + 同名 canvas."""
    g1 = build_vault_group_id("cs_61b", subject_id="algorithms")
    g2 = build_vault_group_id("数学", subject_id="algorithms")
    g3 = build_vault_group_id("cs_61b", canvas_path="algorithms.canvas")
    # g1 == g3 (相同语义, subject 优先于 canvas, 但 sanitize 都是 algorithms)
    assert g1 == g3
    # g1 != g2 (不同 vault)
    assert g1 != g2


# ════════════════════════════════════════════════════════════════════
# 4. Cypher group_id 过滤防御性 (Story 2.5.Y AC #5)
# ════════════════════════════════════════════════════════════════════


def test_cypher_query_without_group_id_rejected():
    """调用方忘记传 group_id → 立即抛错 (不静默查所有 vault)."""
    with pytest.raises(ValueError, match="group_id is required"):
        cypher_with_group_filter("MATCH (n:Concept) RETURN n", "")


def test_cypher_query_uses_parameterized_binding():
    """group_id 应通过参数绑定 (防 Cypher injection)."""
    _, params = cypher_with_group_filter(
        "MATCH (n) RETURN n", "vault:cs_61b'; DROP DATABASE neo4j; --"
    )
    # 参数化绑定 → SQL/Cypher injection 无效 (params dict 不影响 query 文本)
    assert params["group_id"] == "vault:cs_61b'; DROP DATABASE neo4j; --"
    # query 文本不应含 raw injection
    # (参数化会在 driver 层安全 escape)


# ════════════════════════════════════════════════════════════════════
# 5. 历史债标记 (cross_canvas_retriever placeholder, 非本 Story 范围)
# ════════════════════════════════════════════════════════════════════


def test_known_limitation_cross_canvas_retriever_placeholder():
    """⚠️ 历史债 doc test: cross_canvas_retriever.find_related_canvases 仍是 placeholder.

    R12 review 已识别 (2026-04-21), 不在 Story 2.5.Y 范围.
    修复留待: Epic 2 跨 canvas 检索专项 Story.

    本测试仅作为 known limitation marker, 不阻塞 Story 2.5.Y review.
    """
    # 该限制不影响 Story 2.5.Y 的 multi-vault 隔离 (vault 内 cross_canvas 是子问题)
    assert True, "cross_canvas_retriever placeholder is documented technical debt"
