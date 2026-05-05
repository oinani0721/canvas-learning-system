"""Story 2.5.Y Task 5 — Cypher 防御性 group_id 注入 helpers.

强制所有 Cypher 查询都带 group_id 过滤, 防止"忘记传 group_id 导致跨 vault 数据泄漏".

设计原则:
- 调用方必须显式传 group_id (空 / None → ValueError 不静默)
- 自动注入 WHERE 子句 (复用 SubjectConfig.build_neo4j_subject_filter 模式)
- 与 Story 1.9 build_neo4j_subject_filter 互补:
  · build_neo4j_subject_filter: 接受 None/general 时返回空 clause (Story 1.9 跨学科默认)
  · cypher_with_group_filter: Story 2.5.Y 严格强制必填 (multi-vault 隔离)

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-y-isolation-hardening-subject-config-reuse.md
"""

from __future__ import annotations

from typing import Tuple


def cypher_with_group_filter(
    base_query: str,
    group_id: str,
    *,
    node_alias: str = "n",
    where_keyword: str = "WHERE",
) -> Tuple[str, dict]:
    """Story 2.5.Y AC #5 — 强制注入 group_id WHERE 子句.

    Args:
        base_query: 原始 Cypher 查询 (无 WHERE 子句, 如 "MATCH (n:Concept) RETURN n")
        group_id: 必填 group_id (空 → ValueError)
        node_alias: Cypher 变量名 (默认 "n")
        where_keyword: "WHERE" 或 "AND" (用于已有 WHERE 子句的查询追加过滤)

    Returns:
        (modified_query, params) — params 含 {"group_id": <value>} 供 tx.run(query, **params) 用

    Raises:
        ValueError: group_id 为空 (Story 2.5.Y 严格必填)

    Examples:
        >>> q, p = cypher_with_group_filter("MATCH (n:Concept) RETURN n", "vault:cs_61b")
        >>> q
        'MATCH (n:Concept) WHERE n.group_id = $group_id RETURN n'
        >>> p
        {'group_id': 'vault:cs_61b'}

        >>> # 已有 WHERE 子句 → 用 where_keyword="AND"
        >>> q, p = cypher_with_group_filter(
        ...     "MATCH (n:Concept) WHERE n.mastery > 0.5 RETURN n",
        ...     "vault:cs_61b",
        ...     where_keyword="AND",
        ... )
        >>> "AND n.group_id = $group_id" in q
        True
    """
    if not group_id or not group_id.strip():
        raise ValueError(
            "Story 2.5.Y AC #5: group_id is required for cypher query "
            "(防止跨 vault 数据泄漏). 调用方必须显式传值, 不能静默 fallback."
        )

    filter_clause = f"{where_keyword} {node_alias}.group_id = $group_id"

    # Heuristic: 在 RETURN / WITH / ORDER BY 等关键字前插入 filter
    # 优先级 (大写匹配, 然后小写):
    insert_keywords = [
        "RETURN ",
        "WITH ",
        "ORDER BY ",
        "SET ",
        "DELETE ",
        "DETACH DELETE ",
        "REMOVE ",
        "CREATE ",
        "MERGE ",
    ]

    upper_query = base_query.upper()
    insert_pos = -1
    for kw in insert_keywords:
        idx = upper_query.find(kw)
        if idx != -1 and (insert_pos == -1 or idx < insert_pos):
            insert_pos = idx

    if insert_pos == -1:
        # 没找到关键字 → 追加到末尾
        modified = f"{base_query.rstrip()} {filter_clause}"
    else:
        modified = (
            f"{base_query[:insert_pos].rstrip()} "
            f"{filter_clause} "
            f"{base_query[insert_pos:].lstrip()}"
        )

    return modified, {"group_id": group_id}


def assert_group_id_required(group_id: str | None, context: str = "") -> str:
    """Story 2.5.Y Task 5 防御性 helper — 调用方一致性校验.

    用于服务层入口校验, 提前 fail 而不是等到 Cypher 拼装时.

    Args:
        group_id: 待校验 group_id (None / "" / "   " → 抛错)
        context: 错误提示上下文 (如调用方函数名 / endpoint 路径)

    Returns:
        Validated group_id (stripped)

    Raises:
        ValueError: group_id 缺失或全空白

    Examples:
        >>> assert_group_id_required("vault:cs_61b", "memory_service.search")
        'vault:cs_61b'
        >>> assert_group_id_required("", "X.Y")  # 抛 ValueError
    """
    if not group_id or not group_id.strip():
        ctx_str = f" [context: {context}]" if context else ""
        raise ValueError(
            f"Story 2.5.Y AC #5: group_id is required{ctx_str}. "
            "缺失会导致跨 vault 数据泄漏, 调用方必须显式传值."
        )
    return group_id.strip()
