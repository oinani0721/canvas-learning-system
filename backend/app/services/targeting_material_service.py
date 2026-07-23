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

import difflib
import logging
import re
import unicodedata
from typing import Any

import frontmatter

from app.graphiti.group_id_compat import to_physical_group_id
from app.services.frontmatter_signals import _node_md_path

_PUNCT_RE = re.compile(r"[\s\W_]+", re.UNICODE)


def _norm_for_dispute(text: str) -> str:
    """dispute 匹配归一化: NFKC + casefold + 去空白/标点 (P1, 终验对账裁决 6)。"""
    return _PUNCT_RE.sub("", unicodedata.normalize("NFKC", text).casefold())


def _matches_disputed(text: str, disputed_norms: list[str], ratio: float = 0.75) -> bool:
    """归一化后精确或 difflib 模糊 (≥ratio) 命中任一 disputed 文本 → 排除。"""
    tn = _norm_for_dispute(text)
    if not tn:
        return False
    for dn in disputed_norms:
        if tn == dn:
            return True
        if dn and difflib.SequenceMatcher(None, tn, dn).ratio() >= ratio:
            return True
    return False


logger = logging.getLogger(__name__)

#: 单邻居最多贡献的错误条数 (防单点噪音淹没 prompt)
_MAX_ERRORS_PER_NEIGHBOR = 3


def _read_neighbor_errors(node_id: str, group_id: str = "") -> list[str]:
    """读邻居节点当前态错误描述 (正式 errors[] 优先 + tips tag=error)。

    轨道 B P2 (2026-07-20): 两道新防线 —
    ① vault 归属校验: 邻居 md 的 errors[].group_id 与请求 group 不一致
       一律拒收 (UAT-2.5.X-test 的 CS188 素材曾混入线代 vault 出题链);
    ② 泄题防御 (P5/硬要求③): 优先读 misconception 字段 (误解半句),
       缺失才回退 description — 更正半句永不进出题素材。
    """
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
    # 批次3' dispute 三件套第二件「出题排除」(MEM-FLYWHEEL): 用户 dispute 过的
    # 候选文本不得再进出题素材 — 不再拿你否认过的点考你。disputed 候选留在
    # error_candidates[] (终态, 状态机保证不入 errors[])。
    # P1 升级 (2026-07-24, 终验对账裁决 6): 精确匹配一字改写即绕过 →
    # 归一化 (NFKC/casefold/去空白标点) + difflib 模糊相似 (≥0.75) 拦截
    # 改字/标点/词序变体; embedding 语义版记中期。
    disputed_texts: set[str] = set()
    for cand in fm.get("error_candidates") or []:
        if isinstance(cand, dict) and cand.get("status") == "disputed":
            for key in ("misconception", "description"):
                t = str(cand.get(key) or "").strip()
                if t:
                    disputed_texts.add(t)
    disputed_norms = [_norm_for_dispute(t) for t in disputed_texts]
    # 正式 errors[] — 2.5.X accept/edited 移入, 用户主权确认过的错误
    for err in fm.get("errors") or []:
        if isinstance(err, dict):
            # 批次1'② (MEM-FLYWHEEL): fail-closed — 缺 group_id 一律拒收。
            # 「缺失放行」曾是 C1 泄漏通道 (UAT-2.5.X 测试种子 errors[] 无
            # group_id 混入线代出题链, 2026-07-22 对抗审查实锤); 缺失兼容
            # 只准存在于离线迁移工具, 不在线上主路径 (ChatGPT R1 三层防线)。
            err_group = str(err.get("group_id") or "").strip()
            if group_id and err_group != group_id:
                logger.info(
                    "[T4-P2] 拒收邻居素材 (fail-closed): node=%s err_group=%r req_group=%s",
                    node_id,
                    err_group,
                    group_id,
                )
                continue
            desc = str(err.get("misconception") or err.get("description") or "").strip()
            if desc and _matches_disputed(desc, disputed_norms):
                logger.info("[T4-dispute] 排除已 dispute 素材: node=%s", node_id)
                continue
            if desc:
                out.append(desc)
    # tips[] 中用户手标的 error
    for tip in fm.get("tips") or []:
        if isinstance(tip, dict) and tip.get("tag") == "error":
            text = str(tip.get("text") or "").strip()
            if text and _matches_disputed(text, disputed_norms):
                logger.info("[T4-dispute] 排除已 dispute tips 素材: node=%s", node_id)
                continue
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
        # 批次1'② (MEM-FLYWHEEL): 三处收紧 —
        # ① n/e/m 三侧 group 谓词严格相等 (IS NULL 放行是 C1 同源洞, 移除);
        # ② OPTIONAL MATCH 区分 node_not_found / no_neighbors 两态;
        # ③ ORDER BY neighbor_id 确定性排序 (原纯存储顺序=随机;
        #    批次4' 投影边补 created_at 后改按时间)。
        # 批次4' 3-3: e.invalidated_at IS NULL 过滤幽灵边 (已删/改名的旧关系
        # 不再进出题素材); 3-2: ORDER BY 升级为派生时间倒序 (created_at 已补,
        # 最近拆分的关系优先), neighbor_id 兜底保确定性
        records = await client.run_query(
            """
            MATCH (n:CanvasNode {id: $node_id})
            WHERE n.group_id = $group_id
            OPTIONAL MATCH (n)-[e:CANVAS_EDGE]-(m:CanvasNode)
            WHERE e.group_id = $group_id AND m.id <> $node_id
              AND m.group_id = $group_id AND e.invalidated_at IS NULL
            RETURN DISTINCT m.id AS neighbor_id, e.label AS reason,
                   e.created_at AS edge_created_at
            ORDER BY edge_created_at DESC, neighbor_id
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

    if not records:
        result["degraded"] = True
        result["degraded_reason"] = "node_not_found"
        return result
    neighbor_rows = [
        data for rec in records if (data := rec if isinstance(rec, dict) else rec.data()).get("neighbor_id")
    ]
    if not neighbor_rows:
        result["degraded"] = True
        result["degraded_reason"] = "no_neighbors"
        return result

    used = 0
    for data in neighbor_rows:
        neighbor_id = str(data.get("neighbor_id") or "")
        reason = str(data.get("reason") or "").strip()
        for err_text in _read_neighbor_errors(neighbor_id, group_id=group_id):
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
    if not result["materials"]:
        # 有邻居但全部无可用错误素材 — 与「无邻居」区分, 调用方可选不同兜底话术
        result["degraded"] = True
        result["degraded_reason"] = "no_neighbor_errors"
    return result
