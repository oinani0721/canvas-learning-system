"""T4 方案 A (2026-07-10, 用户拍板) — 针对性考察素材服务。

给定节点, 沿增殖投影图 (CanvasNode-[CANVAS_EDGE{label=原因}]-CanvasNode,
T2 起带 group_id) 找 1-hop 邻居, 读每个邻居的**当前态错误**作为跨节点
出题素材: "你之前在 A 犯过 X 错, 现在考你 B 里同源的概念"。

素材来源 (P1 A+-prime 裁决: 当前态读 frontmatter, Graphiti 是历史流):
- 邻居发现: Neo4j 投影 (1 条 cypher, 双向 1-hop + 边 label 原因, group 过滤)
- 邻居错误: frontmatter `errors[]` (Story 2.5.X 用户 accept 确认的正式错误,
  优先) + `tips[] tag==error` (用户手标) — 两者都是学生自己的错误记录,
  不是定义正文, 信息隔离 (d=1.50) 不破。

降级契约: Neo4j 不可用 / 无邻居 / 邻居无错误 → materials=[] + degraded
标记, 调用方 (start-exam-board skill 经 API) 静默退回仅本节点素材。
"""

from __future__ import annotations

import logging
from typing import Any

import frontmatter

from app.graphiti.group_id_compat import to_physical_group_id
from app.services.frontmatter_signals import _node_md_path

logger = logging.getLogger(__name__)

#: 单邻居最多贡献的错误条数 (防单点噪音淹没 prompt)
_MAX_ERRORS_PER_NEIGHBOR = 3


def _read_neighbor_errors(node_id: str) -> list[str]:
    """读邻居节点当前态错误描述 (正式 errors[] 优先 + tips tag=error)。"""
    # 纵深防御: neighbor_id 来自图内受控数据 (sync 写入 md.stem), 但
    # _node_md_path 本身无穿越防护 — 含路径分隔/父目录引用一律拒绝
    if "/" in node_id or "\\" in node_id or ".." in node_id:
        logger.warning("[T4] 拒绝可疑 neighbor_id: %r", node_id)
        return []
    path = _node_md_path(node_id)
    if path is None:
        return []
    try:
        post = frontmatter.load(str(path))
    except (OSError, ValueError, UnicodeDecodeError) as e:
        logger.debug("[T4] frontmatter 读取失败 %s: %s", node_id, e)
        return []
    fm = post.metadata or {}
    out: list[str] = []
    # 正式 errors[] — 2.5.X accept/edited 移入, 用户主权确认过的错误
    for err in fm.get("errors") or []:
        if isinstance(err, dict):
            desc = str(err.get("description") or "").strip()
            if desc:
                out.append(desc)
    # tips[] 中用户手标的 error
    for tip in fm.get("tips") or []:
        if isinstance(tip, dict) and tip.get("tag") == "error":
            text = str(tip.get("text") or "").strip()
            if text:
                out.append(text)
    return out[:_MAX_ERRORS_PER_NEIGHBOR]


async def collect_targeting_material(
    node_id: str,
    group_id: str,
    budget_chars: int = 1200,
) -> dict[str, Any]:
    """收集节点的跨节点针对性考察素材。

    Args:
        node_id: 被考察节点 id (文件 basename, 扁平节点池约定)。
        group_id: 逻辑 D16 group_id (vault:x) — 内部物理化后过滤投影图。
        budget_chars: 素材总字符预算 (超出截断, 邻居顺序 = 图返回顺序)。

    Returns:
        {materials: [{source_node, relation_reason, kind, text}],
         degraded: bool, degraded_reason: str | None}
    """
    result: dict[str, Any] = {
        "materials": [],
        "degraded": False,
        "degraded_reason": None,
    }
    try:
        from app.clients.neo4j_client import get_neo4j_client

        client = get_neo4j_client()
        # T1/T2: 投影图物理 __ 格式; 双向 1-hop, 边 label = 用户增殖原因
        records = await client.run_query(
            """
            MATCH (n:CanvasNode {id: $node_id})-[e:CANVAS_EDGE]-(m:CanvasNode)
            WHERE e.group_id = $group_id AND m.id <> $node_id
            RETURN DISTINCT m.id AS neighbor_id, e.label AS reason
            LIMIT 10
            """,
            node_id=node_id,
            group_id=to_physical_group_id(group_id),
        )
    except Exception as e:  # noqa: BLE001 — 读侧降级, 不炸出题
        logger.debug("[T4] 邻居查询失败 (降级仅本节点): %s", e)
        result["degraded"] = True
        result["degraded_reason"] = f"neo4j_unavailable: {type(e).__name__}"
        return result

    used = 0
    for rec in records or []:
        data = rec if isinstance(rec, dict) else rec.data()
        neighbor_id = str(data.get("neighbor_id") or "")
        reason = str(data.get("reason") or "").strip()
        if not neighbor_id:
            continue
        for err_text in _read_neighbor_errors(neighbor_id):
            if used + len(err_text) > budget_chars:
                logger.debug("[T4] 素材达字符预算 %d, 截断", budget_chars)
                return result
            result["materials"].append(
                {
                    "source_node": neighbor_id,
                    "relation_reason": reason,
                    "kind": "error",
                    "text": err_text,
                }
            )
            used += len(err_text)
    return result
