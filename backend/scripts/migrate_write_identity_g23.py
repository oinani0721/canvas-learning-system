#!/usr/bin/env python3
"""G2-3 Concept/LEARNED 写身份迁移器 (BATCH-2026-08-28-第五批 / CARD-G2-3).

背景: G2-1 审计确认 create_learning_relationship / fallback_sync 旧实现按
`MERGE (c:Concept {name})` 单身份合并 + 事后 SET group_id — 跨 vault 同名
概念冲撞、last-write-wins 劫持归属 (W1 违规)。G2-3 已把写路径改为
{name, group_id} 复合身份键; 本脚本处理**存量**单身份数据:

1. census (只读): Concept/LEARNED 写身份健康普查 — 组分布、NULL 组、
   边组与端点组错配 (clobber 证据)。
2. pending 裁定: 需要分裂/回填的概念与边清单。现网勘探预期 pending=0
   ("迁移 = 证明零动作"), pending>0 时 exit 2 提示需人工过目后 --apply。
3. --apply (可选): 按 LEARNED 边组分裂概念节点 + 迁移边 + NULL 边组
   回填 — **对 :7691 现网硬拒绝** (live 只读铁律), 只允许测试/隔离库。

契约对齐:
- W4 declared cross-vault write: 本工具为显式声明的迁移器, 默认 dry-run。
- 零写入证明: dry-run 全程使用 READ access-mode session (服务端拒写),
  另附前后节点/关系计数对账 (reconciliation) 写入证据 JSON。
- Canvas/Node/Episode 层无组存量**不在本卡迁移范围** (卡题 = 概念/LEARNED
  身份), 仅作 legacy_informational 如实披露, 收敛归 G2-9 隔离 canary 链。

用法:
    # 现网 dry-run (只读), 证据 JSON 落盘
    python scripts/migrate_write_identity_g23.py \
        --uri bolt://localhost:7691 --out evidence.json
    # 测试容器上执行迁移
    python scripts/migrate_write_identity_g23.py \
        --uri bolt://127.0.0.1:7692 --apply

Exit codes: 0 = pending==0 (或 apply 完成且复查归零); 2 = dry-run 发现
pending>0 (需人工裁定); 1 = 运行错误。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

try:
    from neo4j import READ_ACCESS, WRITE_ACCESS, GraphDatabase
except ImportError:  # pragma: no cover - 环境缺依赖时显式失败
    print("ERROR: neo4j driver not installed (pip install neo4j)", file=sys.stderr)
    raise

LIVE_PORT = 7691
DEFAULT_LIVE_URI = "bolt://localhost:7691"


def targets_live_db(uri: str) -> bool:
    """现网端口判定 — 解析端口而非子串匹配（第一道闸，非充分条件）.

    子串 ``":7691" in uri`` 会被等价写法绕过 (``:07691`` 数值同端口、
    URL 编码、大小写主机名)。用 urlsplit 取端口的整数值判定, 解析失败
    一律按"是现网"处理 (fail-closed: 拿不准就拒绝写)。

    ⚠️ 端口 ≠ 数据库身份 (Codex round-1 BLOCKER): 端口转发/路由种子可以
    让"非现网端口"落到现网库。故 ``--apply`` 还必须过
    :func:`assert_target_is_not_live` 的**库身份**闸。
    """
    try:
        parsed = urlsplit(uri)
        port = parsed.port
    except ValueError:
        return True  # 端口非法/畸形 URI — 拒绝
    if port is None:
        return True  # 无显式端口: 可能走默认路由到现网, 拒绝
    return port == LIVE_PORT


def fetch_store_identity(driver, database: str) -> Optional[str]:
    """取库的稳定身份 (``db.info().id`` = store id, 与端口/主机无关).

    实测 (Neo4j 5.26, 2026-08-28): ``CALL db.info()`` 返回
    ``{id, name, creationDate}``, id 为 store 级 64 位十六进制指纹 —
    同一物理库无论经哪个端口/转发访问都返回同值, 正是端口判定缺的那条
    身份证据。取不到时返回 None (调用方按"无法自证"fail-closed)。
    """
    try:
        with driver.session(database=database, default_access_mode=READ_ACCESS) as s:
            rec = s.run("CALL db.info() YIELD id, name, creationDate RETURN id, name, creationDate").single()
        if not rec:
            return None
        return f"{rec['id']}::{rec['name']}::{rec['creationDate']}"
    except Exception:  # noqa: BLE001 — 任何失败都视为"无法自证身份"
        return None


# 现网 (7691) 的 store identity 指纹 — 2026-08-28 于本机实测取得。
# store id 不是机密 (它标识本地开发库), 钉在代码里是为了让身份闸在**没有
# 现网凭据**的环境 (如测试容器) 里也决定性生效; 可用 NEO4J_LIVE_STORE_ID
# 覆盖。现网库若被重建, 指纹会变 → 该闸对新库失效, 但端口闸仍然拦截 ——
# 两道闸各自覆盖对方的盲区 (端口闸挡不住端口转发, 指纹闸挡不住库重建)。
KNOWN_LIVE_STORE_IDENTITY = (
    "C43B910072C97DA5907C9687316EBBCA7F05731C606638B4689AB43B5BC39759::neo4j::2026-05-06T16:44:07.865Z"
)


def assert_target_is_not_live(
    target_driver,
    database: str,
    live_uri: str,
    auth,
    allow_unverified: bool = False,
) -> Optional[str]:
    """库身份闸: 证明 --apply 的目标**不是**现网库, 否则拒绝.

    端口不是数据库身份 (Codex round-1 BLOCKER): ``bolt://localhost:7692``
    经端口转发/路由种子可以落到现网 writer。故比对 store identity:

    1. 目标库身份读不到 → 无法自证 → 拒绝 (除非 --allow-unverified-target)。
    2. 目标库身份 == 已知现网指纹 (常量或 NEO4J_LIVE_STORE_ID) → 拒绝。
    3. 若能连上 --live-uri (有凭据时), 再做一次**实时**比对 —— 覆盖现网
       库重建导致常量指纹过期的情况。连不上不视为失败 (常量比对已给出
       结论), 只在 stderr 记一行提示。

    Returns: None 表示放行; 非 None 为拒绝原因字符串。
    """
    target_id = fetch_store_identity(target_driver, database)
    if target_id is None:
        if allow_unverified:
            return None
        return "无法读取目标库 store identity (db.info()) — 无法证明它不是现网, 拒绝 --apply"

    known_live = os.getenv("NEO4J_LIVE_STORE_ID", KNOWN_LIVE_STORE_IDENTITY)
    if known_live and target_id == known_live:
        return "目标库 store identity 与已知现网指纹一致 — 端口不同也是同一物理库, 拒绝 --apply"

    # 实时比对 (best-effort): 现网可能已重建, 常量指纹会过期
    try:
        live_driver = GraphDatabase.driver(live_uri, auth=auth)
        try:
            live_driver.verify_connectivity()
            live_id = fetch_store_identity(live_driver, database)
        finally:
            live_driver.close()
    except Exception:  # noqa: BLE001
        live_id = None

    if live_id is None:
        # round-3/4 C6: 实时比对不可达时, 判定只能依赖**可能过期**的常量指纹
        # (现网库重建后常量失效)。round-4 收紧: 换个不可达的 --live-uri 也
        # 算"表态"等于没有门 —— 现在只认两类**真实依据**:
        #   ① NEO4J_LIVE_STORE_ID: 操作者提供了当前现网指纹 (实证据);
        #   ② --allow-unverified-target: 明知未验证仍要执行 ([Decision] 约束)。
        supplied_fingerprint = bool(os.getenv("NEO4J_LIVE_STORE_ID"))
        if not (supplied_fingerprint or allow_unverified):
            return (
                f"实时身份比对不可达 ({live_uri}), 判定只能依赖可能过期的常量指纹 — "
                "拒绝 --apply。请设 NEO4J_LIVE_STORE_ID 提供当前现网指纹, "
                "或在 [Decision] 批准下显式加 --allow-unverified-target"
            )
        print(
            f"NOTE: 无法连 {live_uri} 做实时身份比对 (凭据/可达性), "
            "已按已知现网指纹常量 + 操作者显式表态判定放行 — 若现网库曾重建, "
            "请更新 KNOWN_LIVE_STORE_IDENTITY 或设 NEO4J_LIVE_STORE_ID。",
            file=sys.stderr,
        )
        return None
    if live_id == target_id:
        return f"目标库 store identity 与现网实时指纹一致 ({live_uri}) — 拒绝 --apply"
    return None


# -- census 查询 (全部只读) --------------------------------------------------

_CENSUS_QUERIES = {
    "concept_total": "MATCH (c:Concept) RETURN count(c) AS n",
    # C5 (Codex round-2): 空白口径全链统一 —— 计数器也必须按 trim 判"无组",
    # 否则 group_id='' 的概念不计入 null_group, 报表与 pending 口径打架。
    "concept_no_group": ("MATCH (c:Concept) WHERE coalesce(trim(c.group_id), '') = '' RETURN count(c) AS n"),
    "learned_total": "MATCH ()-[r:LEARNED]->() RETURN count(r) AS n",
    "learned_no_group": ("MATCH ()-[r:LEARNED]->() WHERE coalesce(trim(r.group_id), '') = '' RETURN count(r) AS n"),
    "learned_group_mismatch": (
        "MATCH ()-[r:LEARNED]->(c:Concept) "
        "WHERE coalesce(trim(r.group_id), '') <> '' AND r.group_id <> coalesce(c.group_id, '') "
        "RETURN count(r) AS n"
    ),
    "user_total": "MATCH (u:User) RETURN count(u) AS n",
}

# ⚠️ 空串 = 无组 (Codex round-1 HIGH 整改): `IS NOT NULL` 会把 "" 当作
# 合法身份 → 空 gid 进 MERGE 键 / NULL 边被回填成空串, 复查还报成功。
# 全部谓词统一用 `coalesce(trim(x.group_id), '') = ''` 判"无组"。
_NO_GROUP = "coalesce(trim({alias}.group_id), '') = ''"
_HAS_GROUP = "coalesce(trim({alias}.group_id), '') <> ''"

_CONCEPT_GROUP_DIST = (
    "MATCH (c:Concept) "
    "RETURN CASE WHEN " + _NO_GROUP.format(alias="c") + " THEN '<NULL_OR_BLANK>' "
    "ELSE c.group_id END AS gid, count(c) AS n ORDER BY gid"
)

# 需要分裂的概念: 存在非空边组 ≠ 端点组的 LEARNED 边
_SPLIT_NEEDED = (
    "MATCH (u:User)-[r:LEARNED]->(c:Concept) "
    "WHERE " + _HAS_GROUP.format(alias="r") + " AND r.group_id <> coalesce(c.group_id, '') "
    "RETURN c.name AS name, "
    "CASE WHEN " + _NO_GROUP.format(alias="c") + " THEN '<NULL_OR_BLANK>' ELSE c.group_id END AS anchor_gid, "
    "collect(DISTINCT r.group_id) AS foreign_gids, count(r) AS edge_count "
    "ORDER BY name"
)

# NULL/空组边回填候选: 边无组但端点组明确
_NULL_EDGE_BACKFILL = (
    "MATCH ()-[r:LEARNED]->(c:Concept) "
    "WHERE " + _NO_GROUP.format(alias="r") + " AND " + _HAS_GROUP.format(alias="c") + " "
    "RETURN c.name AS name, c.group_id AS gid, count(r) AS edge_count "
    "ORDER BY name"
)

# 不可自动裁定: 无组概念 (无带组边可推断)
_MANUAL_NULL_CONCEPT = (
    "MATCH (c:Concept) WHERE " + _NO_GROUP.format(alias="c") + " "
    "AND NOT EXISTS { MATCH ()-[r:LEARNED]->(c) WHERE " + _HAS_GROUP.format(alias="r") + " } "
    "RETURN c.name AS name, "
    "count { MATCH ()-[r0:LEARNED]->(c) } AS edge_count ORDER BY name"
)

# 逻辑重复概念节点 (C4, Codex round-2): 现网无 Concept 唯一约束 (MEMORY
# 2026-08-17 实查), 同 (name, group_id) 可能存在**多个物理节点** —— 此时
# 按物理节点分组的边去重看不到逻辑重复 (每个物理节点各留一条规范边)。
# 本卡**只检测不自动合并**: 合并节点要搬迁其全部关系, 风险远超"身份键"
# 范围; 计入 manual pending 交人工裁定, 绝不让工具报 OK 掩盖它。
_DUPLICATE_CONCEPT_NODES = (
    "MATCH (c:Concept) WHERE coalesce(trim(c.group_id), '') <> '' "
    "WITH c.name AS name, c.group_id AS gid, count(*) AS node_count "
    "WHERE node_count > 1 "
    "RETURN name, gid, node_count ORDER BY name, gid"
)

# 同身份重复边 (历史遗留或早期回填造成): 同 (u, c, group_id) 多条 LEARNED
_DUPLICATE_IDENTITY_EDGES = (
    "MATCH (u:User)-[r:LEARNED]->(c:Concept) "
    "WHERE " + _HAS_GROUP.format(alias="r") + " "
    "WITH u, c, r.group_id AS gid, collect(r) AS rs "
    "WHERE size(rs) > 1 "
    "RETURN c.name AS name, gid, size(rs) AS edge_count ORDER BY name, gid"
)

# Canvas/Node/Episode 层 informational (本卡不迁移, 归 G2-9 链)
# ⚠️ duplicate_concept_nodes 只披露不自动合并: 合并**节点**要搬迁其全部
# 关系, 风险与爆炸半径远超本卡的"身份键"范围 (旧写路径按 name 单键 MERGE
# 不可能产出同 (name, group) 重复节点, 若出现说明另有写入源, 须人工裁定)。
_LEGACY_INFORMATIONAL = {
    "duplicate_concept_nodes": (
        "MATCH (c:Concept) WHERE coalesce(trim(c.group_id), '') <> '' "
        "WITH c.name AS name, c.group_id AS gid, count(*) AS n "
        "WHERE n > 1 RETURN count(*) AS n"
    ),
    "canvas_nodes_ungrouped": ("MATCH (c:Canvas) WHERE c.group_id IS NULL RETURN count(c) AS n"),
    "node_nodes_ungrouped": ("MATCH (n:Node) WHERE n.group_id IS NULL RETURN count(n) AS n"),
    "connects_to_ungrouped": ("MATCH ()-[r:CONNECTS_TO]->() WHERE r.group_id IS NULL RETURN count(r) AS n"),
    "contains_node_ungrouped": ("MATCH ()-[r:CONTAINS_NODE]->() WHERE r.group_id IS NULL RETURN count(r) AS n"),
    "associated_with_ungrouped": ("MATCH ()-[r:ASSOCIATED_WITH]->() WHERE r.group_id IS NULL RETURN count(r) AS n"),
    "episode_ungrouped": ("MATCH (e:Episode) WHERE e.group_id IS NULL RETURN count(e) AS n"),
}

_TOTALS = "MATCH (n) WITH count(n) AS nodes MATCH ()-[r]->() RETURN nodes, count(r) AS rels"

# 属性敏感指纹 (Codex round-1 MEDIUM / round-2 C2 整改): 纯计数对账检测不到
# "属性被改"与"净计数为零的增删"。取 Concept/LEARNED 面的**全属性**内容指纹
# (逐 key 展开, 不写死字段清单 —— 写死会漏掉 next_review/agent_type 等),
# 前后相等才算零写入; 与 READ access mode 的运行时拒写探针形成双证据。
#: 返回 (前缀, 属性 k=v 列表) —— key 顺序由 Python 侧排序保证确定性
#: (keys() 的顺序 Cypher 不保证, 纯 Cypher 排序无 apoc 不便)。
_SCOPE_ROWS = (
    "MATCH (c:Concept) "
    "RETURN 'C|' + coalesce(c.name,'<null>') AS head, "
    "  [k IN keys(c) | k + '=' + coalesce(toString(c[k]), '<null>')] AS props "
    "UNION ALL "
    "MATCH (u:User)-[r:LEARNED]->(c2:Concept) "
    "RETURN 'R|' + coalesce(u.id,'<null>') + '|' + coalesce(c2.name,'<null>') + '|' + "
    "  coalesce(c2.group_id,'<null>') AS head, "
    "  [k IN keys(r) | k + '=' + coalesce(toString(r[k]), '<null>')] AS props"
)
#: 运行时零写入探针 — 在 READ 模式会话里试写, 期望服务端拒绝。
#: 把"READ access mode 拒写"从硬编码断言变成**实测**证据 (Codex round-2 C2)。
_WRITE_PROBE = "CREATE (:__G23WriteProbe {probe: true})"
#: READ 模式拒写的**精确**错误码 (2026-08-28 于 Neo4j 5.26 实测)
_ACCESS_MODE_ERROR_CODE = "Neo.ClientError.Statement.AccessMode"


def _single(session, query: str, **params) -> Dict[str, Any]:
    return session.run(query, **params).single().data()


def _scope_fingerprint(session) -> str:
    """Concept/LEARNED 面的**全属性**内容指纹 (排序后 sha256).

    逐 key 展开而非写死字段清单 —— 写死会漏掉 next_review/agent_type 等
    属性的改动 (Codex round-2 C2)。key 与行都在 Python 侧排序保证确定性。
    """
    rows = sorted(f"{r['head']}|{'|'.join(sorted(r['props']))}" for r in session.run(_SCOPE_ROWS))
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


def probe_read_access_enforced(session) -> Optional[bool]:
    """实测 READ 模式会话是否被服务端拒写 (不硬编码结论, Codex round-2 C2).

    round-3 修正 (C2a): 只有**明确的 access-mode 拒绝**才算"已强制";
    连接抖动等其他异常一律返回 None (未知) —— 原实现把任意异常都当成
    拒写, 一次网络故障就能伪造出"零写入有服务端保障"的结论。

    Returns: True=服务端拒写 / False=竟然写成功(该部署不拒写) / None=未知
    """
    try:
        session.run(_WRITE_PROBE).consume()
    except Exception as exc:  # noqa: BLE001 — 需按错误码精确区分
        # round-4 C2a: **只认错误码**, 不再退而求其次匹配异常文本 ——
        # 任意异常的 message 里恰好含 "read access mode" 就能伪装成
        # "服务端拒写"。实测码 (Neo4j 5.26, neo4j.exceptions.ClientError):
        # Neo.ClientError.Statement.AccessMode
        if getattr(exc, "code", None) == _ACCESS_MODE_ERROR_CODE:
            return True
        return None  # 其他失败: 未知, 不得据此声称零写入有保障
    # 竟然写成功: 说明该部署的 READ 模式不拒写 — 清理探针并如实报告
    try:
        session.run("MATCH (n:__G23WriteProbe) DELETE n").consume()
    except Exception:  # noqa: BLE001
        pass
    return False


def run_census(driver, database: str) -> Dict[str, Any]:
    """只读普查 — READ access mode + 运行时拒写探针 + 全属性指纹对账."""
    with driver.session(database=database, default_access_mode=READ_ACCESS) as s:
        read_enforced = probe_read_access_enforced(s)
        totals_before = _single(s, _TOTALS)
        fp_before = _scope_fingerprint(s)
        census = {k: _single(s, q)["n"] for k, q in _CENSUS_QUERIES.items()}
        census["concept_by_group"] = {row["gid"]: row["n"] for row in s.run(_CONCEPT_GROUP_DIST)}
        split_needed = [dict(row) for row in s.run(_SPLIT_NEEDED)]
        null_edge_backfill = [dict(row) for row in s.run(_NULL_EDGE_BACKFILL)]
        manual = [dict(row) for row in s.run(_MANUAL_NULL_CONCEPT)]
        duplicates = [dict(row) for row in s.run(_DUPLICATE_IDENTITY_EDGES)]
        dup_nodes = [dict(row) for row in s.run(_DUPLICATE_CONCEPT_NODES)]
        legacy = {k: _single(s, q)["n"] for k, q in _LEGACY_INFORMATIONAL.items()}
        totals_after = _single(s, _TOTALS)
        fp_after = _scope_fingerprint(s)

    auto_total = len(split_needed) + len(null_edge_backfill) + len(duplicates)
    # C4: 逻辑重复概念节点计入 manual —— 工具不得在存在逻辑重复时报 OK
    manual_total = len(manual) + len(dup_nodes)
    counts_equal = totals_before["nodes"] == totals_after["nodes"] and totals_before["rels"] == totals_after["rels"]
    return {
        "census": census,
        "pending": {
            "split_needed_concepts": split_needed,
            "null_edge_group_backfill": null_edge_backfill,
            "duplicate_identity_edges": duplicates,
            "manual_null_group_concepts": manual,
            "manual_duplicate_concept_nodes": dup_nodes,
            "auto_total": auto_total,
            "manual_total": manual_total,
            "total": auto_total + manual_total,
        },
        "legacy_informational": legacy,
        "reconciliation": {
            "nodes_before": totals_before["nodes"],
            "rels_before": totals_before["rels"],
            "nodes_after": totals_after["nodes"],
            "rels_after": totals_after["rels"],
            "scope_fingerprint_before": fp_before,
            "scope_fingerprint_after": fp_after,
            "counts_equal": counts_equal,
            "fingerprint_equal": fp_before == fp_after,
            # 三重证据 (皆为实测, 无硬编码断言):
            # ① READ 模式服务端拒写探针 (True/False/None=未知)
            # ② 计数相等 ③ 全属性指纹相等
            "read_access_mode_enforced": read_enforced,
            "zero_writes": counts_equal and fp_before == fp_after and read_enforced is True,
        },
    }


# -- apply 引擎 (7692/隔离库专用; 7691 硬拒) ---------------------------------

# 所有 apply 查询遵循同一"按身份聚合"纪律 (Codex round-1 两条 HIGH 整改):
# 先 collect 出同一目标身份 (u, name, gid) 的全部源边, 用 reduce 选出
# **唯一** LWW 赢家, 再对唯一目标边写一次 —— 逐行 SET 的结果依赖 Cypher
# 未保证的行序, 多源/多 NULL 边场景下不确定且可能留下重复边。
# LWW 赢家选择: 时间戳大者胜; **并列或全 NULL 时以 elementId 字典序**
# 兜底 (Codex round-2 C3) —— 否则赢家取决于 collect() 的无序首项, 同一
# 数据两次运行可能得到不同结果。elementId 在库内稳定唯一, 保证确定性。
_LWW_PICK = (
    "reduce(best = null, x IN {rows} | "
    "  CASE WHEN best IS NULL "
    "         OR (x.timestamp IS NOT NULL AND best.timestamp IS NULL) "
    "         OR (x.timestamp IS NOT NULL AND best.timestamp IS NOT NULL "
    "             AND x.timestamp > best.timestamp) "
    "         OR (coalesce(toString(x.timestamp),'') = coalesce(toString(best.timestamp),'') "
    "             AND elementId(x) < elementId(best)) "
    "  THEN x ELSE best END) AS best"
)

_APPLY_SPLIT = (
    # 把挂错组的 LEARNED 边迁到 {name, group} 复合身份概念节点上。
    # ⚠️ LWW 守卫: 目标边 r2 可能是 G2-3 修复后写入的**更新**边 (混合时代:
    # 代码先修、存量后迁)。整体 `SET r2 += properties(r)` 会用陈旧属性覆盖
    # 新分数/时间戳 (静默数据损坏), 且会把 group_id 一起搬回旧值。
    "MATCH (u:User)-[r:LEARNED {group_id: $gid}]->(c:Concept {name: $name}) "
    "WHERE coalesce(c.group_id, '') <> $gid "
    "WITH u, collect(r) AS srcs "
    "WITH u, srcs, " + _LWW_PICK.format(rows="srcs") + " "
    "MERGE (c2:Concept {name: $name, group_id: $gid}) "
    "MERGE (u)-[r2:LEARNED {group_id: $gid}]->(c2) "
    "WITH srcs, best, r2, "
    "     CASE WHEN r2.timestamp IS NULL OR "
    "               (best.timestamp IS NOT NULL AND r2.timestamp <= best.timestamp) "
    "          THEN true ELSE false END AS take_source "
    # 属性**整体**迁移 (Codex round-2): 只搬 score/timestamp/next_review/
    # review_count 四个字段会丢掉 agent_type/source 等其余 LEARNED 属性。
    # `+= properties(best)` 复制全部, 随后立即把 group_id 钉回身份值
    # (SET 子句从左到右生效), 保证身份键不被源边的旧组覆盖。
    "SET r2 += CASE WHEN take_source THEN properties(best) ELSE {} END, "
    "    r2.group_id = $gid "
    "WITH srcs, take_source "
    "FOREACH (x IN srcs | DELETE x) "
    "RETURN count(*) AS identities, sum(size(srcs)) AS moved, "
    "       sum(CASE WHEN take_source THEN 1 ELSE 0 END) AS applied_source, "
    "       sum(CASE WHEN take_source THEN 0 ELSE 1 END) AS kept_target"
)

_APPLY_NULL_EDGE_BACKFILL = (
    # 无组边按端点组归位。统一形态: 无论是否已有同身份兄弟边, 都 MERGE 出
    # 唯一的规范边再 LWW 写入, 最后删掉全部无组边 ——
    # · 无兄弟边: MERGE 新建 = 等价于"relabel", 但天然不会留下多条;
    # · 有兄弟边: MERGE 命中它, 无组边的赢家属性按 LWW 并入后删除。
    # 空串组按无组处理 (Codex round-1 HIGH: `IS NOT NULL` 会放行 "")。
    "MATCH (u)-[r:LEARNED]->(c:Concept {name: $name, group_id: $gid}) "
    "WHERE coalesce(trim(r.group_id), '') = '' "
    "WITH u, c, collect(r) AS nulls "
    "WITH u, c, nulls, " + _LWW_PICK.format(rows="nulls") + " "
    "MERGE (u)-[r2:LEARNED {group_id: $gid}]->(c) "
    "WITH nulls, best, r2, "
    "     CASE WHEN r2.timestamp IS NULL OR "
    "               (best.timestamp IS NOT NULL AND r2.timestamp <= best.timestamp) "
    "          THEN true ELSE false END AS take_source "
    # 属性**整体**迁移 (Codex round-2): 只搬 score/timestamp/next_review/
    # review_count 四个字段会丢掉 agent_type/source 等其余 LEARNED 属性。
    # `+= properties(best)` 复制全部, 随后立即把 group_id 钉回身份值
    # (SET 子句从左到右生效), 保证身份键不被源边的旧组覆盖。
    "SET r2 += CASE WHEN take_source THEN properties(best) ELSE {} END, "
    "    r2.group_id = $gid "
    "WITH nulls, take_source "
    "FOREACH (x IN nulls | DELETE x) "
    "RETURN count(*) AS identities, sum(size(nulls)) AS backfilled, "
    "       sum(CASE WHEN take_source THEN 1 ELSE 0 END) AS applied_source"
)

_APPLY_DEDUPE_IDENTITY = (
    # 同 (u, c, group_id) 的重复 LEARNED 边收敛为一条 (LWW 赢家属性),
    # 覆盖历史遗留与早期裸回填造成的重复 —— 业务侧 MERGE 命中重复边中
    # 的任意一条会造成分数漂移。
    "MATCH (u:User)-[r:LEARNED {group_id: $gid}]->(c:Concept {name: $name, group_id: $gid}) "
    "WITH u, c, collect(r) AS rs "
    "WHERE size(rs) > 1 "
    "WITH u, c, rs, " + _LWW_PICK.format(rows="rs") + " "
    "WITH rs, best, head([x IN rs WHERE x = best | x]) AS keep "
    "WITH rs, keep, [x IN rs WHERE NOT x = keep | x] AS dropped "
    "FOREACH (x IN dropped | DELETE x) "
    "RETURN count(*) AS identities, sum(size(dropped)) AS deleted"
)

_APPLY_PRUNE_ORPHAN = (
    # 分裂后失去全部关系的无组旧壳节点清除 (仅限本次迁移涉及的名字)
    "MATCH (c:Concept {name: $name}) "
    "WHERE coalesce(trim(c.group_id), '') = '' AND NOT (c)--() "
    "DELETE c RETURN count(c) AS pruned"
)


def run_apply(driver, database: str, plan: Dict[str, Any]) -> Dict[str, Any]:
    """执行迁移动作 (显式 W4 跨 vault 写; 调用方已过端口闸 + 库身份闸).

    执行顺序与跳过规则 (Codex round-3 整改):
    1. **先**收敛同身份重复边 —— 去重排在 split/backfill 之后会让后者的
       ``MERGE`` 撞上多个目标边、多行展开重复处理同一源集合。
    2. 逻辑重复概念身份 (同 name+group 多物理节点) **跳过自动处理**:
       ``MERGE (c2 {name, gid})`` 面对重复节点会多匹配并扇出写入,
       必须先由人合并节点。跳过项显式登记, 绝不静默略过。
    3. 绑定值一律用 **stripped** gid (round-3 C5: 原实现只用 strip 判空,
       绑定的仍是含空白的原值 → 身份键里混进空白)。
    """
    actions: List[Dict[str, Any]] = []
    dup_identities = {
        (item["name"], (item.get("gid") or "").strip())
        for item in plan["pending"].get("manual_duplicate_concept_nodes", [])
    }

    def _skip_for_dup(name: str, gid: str, action: str) -> bool:
        if (name, gid) in dup_identities:
            actions.append(
                {
                    "action": f"{action}_skipped_duplicate_concept_nodes",
                    "name": name,
                    "gid": gid,
                    "reason": "同 (name, group_id) 存在多个物理 Concept 节点 — 需人工先合并",
                }
            )
            return True
        return False

    def _skip_untrimmed(name: str, raw_gid: str, action: str) -> bool:
        """round-3 C5 终局: 带首尾空白的 group_id 本身是脏数据.

        绑 stripped 值匹配不上库里的原值 (静默空转), 绑原值则把空白写进
        身份键 —— 两种绑定都错。正确处置是**跳过 + 登记**交人工清洗。
        """
        if raw_gid != raw_gid.strip():
            actions.append(
                {
                    "action": f"{action}_skipped_untrimmed_gid",
                    "name": name,
                    "gid": raw_gid,
                    "reason": "group_id 含首尾空白 — 脏数据, 需人工清洗后再迁",
                }
            )
            return True
        return False

    with driver.session(database=database, default_access_mode=WRITE_ACCESS) as s:
        # ① 去重先行
        for item in plan["pending"].get("duplicate_identity_edges", []):
            raw_gid = item.get("gid") or ""
            gid = raw_gid.strip()
            if not gid or _skip_untrimmed(item["name"], raw_gid, "dedupe_identity"):
                continue
            if _skip_for_dup(item["name"], gid, "dedupe_identity"):
                continue
            row = _single(s, _APPLY_DEDUPE_IDENTITY, name=item["name"], gid=gid)
            actions.append({"action": "dedupe_identity", "name": item["name"], "gid": gid, **row})

        # ② 分裂错挂边
        for item in plan["pending"]["split_needed_concepts"]:
            for raw_gid in item["foreign_gids"]:
                raw = raw_gid or ""
                gid = raw.strip()
                if not gid:
                    actions.append({"action": "split_skipped_blank_gid", "name": item["name"]})
                    continue
                if _skip_untrimmed(item["name"], raw, "split"):
                    continue
                if _skip_for_dup(item["name"], gid, "split"):
                    continue
                row = _single(s, _APPLY_SPLIT, name=item["name"], gid=gid)
                actions.append({"action": "split", "name": item["name"], "gid": gid, **row})
            pr = _single(s, _APPLY_PRUNE_ORPHAN, name=item["name"])
            if pr["pruned"]:
                actions.append({"action": "prune_orphan", "name": item["name"], **pr})

        # ③ 无组边回填
        for item in plan["pending"]["null_edge_group_backfill"]:
            raw_gid = item.get("gid") or ""
            gid = raw_gid.strip()
            if not gid:
                actions.append({"action": "backfill_skipped_blank_gid", "name": item["name"]})
                continue
            if _skip_untrimmed(item["name"], raw_gid, "null_edge_backfill"):
                continue
            if _skip_for_dup(item["name"], gid, "null_edge_backfill"):
                continue
            row = _single(s, _APPLY_NULL_EDGE_BACKFILL, name=item["name"], gid=gid)
            actions.append({"action": "null_edge_backfill", "name": item["name"], "gid": gid, **row})
    return {"actions": actions}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7691"))
    parser.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--password", default=os.getenv("NEO4J_PASSWORD", ""))
    parser.add_argument("--database", default=os.getenv("NEO4J_DATABASE", "neo4j"))
    parser.add_argument(
        "--apply",
        action="store_true",
        help="执行迁移写入 (现网双闸硬拒: 端口 + 库身份; 默认 dry-run 只读)",
    )
    parser.add_argument(
        "--live-uri",
        default=os.getenv("NEO4J_LIVE_URI", DEFAULT_LIVE_URI),
        help="现网 URI — 用于 --apply 前比对 store identity (防端口转发绕过)",
    )
    parser.add_argument(
        "--allow-unverified-target",
        action="store_true",
        help="现网身份无法比对时仍允许 --apply (须 [Decision] 批准, 默认 fail-closed 拒绝)",
    )
    parser.add_argument("--out", help="证据 JSON 输出路径 (缺省打印 stdout)")
    args = parser.parse_args(argv)

    if args.apply and targets_live_db(args.uri):
        print(
            "REFUSED: --apply 不允许指向现网端口 7691 (live 只读铁律)。"
            "如确需对现网迁移, 须另行 [Decision] 批准并在隔离窗口执行。",
            file=sys.stderr,
        )
        return 1

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    try:
        driver.verify_connectivity()
        # 第二道闸: 库身份比对 (端口 ≠ 数据库身份, Codex round-1 BLOCKER)
        if args.apply:
            reason = assert_target_is_not_live(
                driver,
                args.database,
                args.live_uri,
                (args.user, args.password),
                allow_unverified=args.allow_unverified_target,
            )
            if reason:
                print(f"REFUSED: {reason}", file=sys.stderr)
                return 1
        report: Dict[str, Any] = {
            "script": "migrate_write_identity_g23",
            "card": "BATCH-2026-08-28-第五批 / CARD-G2-3",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target_uri": args.uri,
            "mode": "apply" if args.apply else "dry-run",
        }
        plan = run_census(driver, args.database)
        report.update(plan)

        # round-3 C2b: dry-run 的零写入结论为假 = 完整性事故, 必须影响退出码。
        # 原实现只把它写进 JSON, 工具照样 exit 0 —— 等于自证失败还报成功。
        integrity_ok = plan["reconciliation"]["zero_writes"]
        if not args.apply and not integrity_ok:
            print(
                "INTEGRITY FAILURE: dry-run 无法证明零写入 "
                f"(counts_equal={plan['reconciliation']['counts_equal']}, "
                f"fingerprint_equal={plan['reconciliation']['fingerprint_equal']}, "
                f"read_access_mode_enforced={plan['reconciliation']['read_access_mode_enforced']})",
                file=sys.stderr,
            )

        if args.apply and plan["pending"]["auto_total"] > 0:
            report["apply"] = run_apply(driver, args.database, plan)
            # 迁移后复查: 自动可迁项必须归零; manual 项列明留人裁定
            recheck = run_census(driver, args.database)
            report["post_apply"] = {
                "census": recheck["census"],
                "pending_auto_total": recheck["pending"]["auto_total"],
                "pending_manual_total": recheck["pending"]["manual_total"],
                "remaining_manual": recheck["pending"]["manual_null_group_concepts"],
                "remaining_duplicate_concept_nodes": recheck["pending"]["manual_duplicate_concept_nodes"],
            }
            success = recheck["pending"]["auto_total"] == 0 and recheck["pending"]["manual_total"] == 0
        else:
            success = plan["pending"]["total"] == 0 and (args.apply or integrity_ok)

        payload = json.dumps(report, ensure_ascii=False, indent=2)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(payload + "\n")
            print(f"evidence written: {args.out}")
        print(
            f"mode={report['mode']} "
            f"pending={plan['pending']['total']} "
            f"(auto={plan['pending']['auto_total']} "
            f"manual={plan['pending']['manual_total']}) "
            f"census_zero_writes={plan['reconciliation']['zero_writes']} "
            f"result={'OK' if success else 'ACTION-NEEDED'}"
        )
        return 0 if success else 2
    finally:
        driver.close()


if __name__ == "__main__":
    sys.exit(main())
