#!/usr/bin/env python
"""端到端验证: 「累积批注 / 节点增殖+原因 → 检验白板针对性考察」主链。

用户 2026-06-03 决策(方向1): 先验证读侧已部分接通的主链真能用, 而非堆地基。
对应研究文档: _bmad-output/研究/2026-06-03-S2-2批注重塑认知-下一步开发计划.md

验证目标 (用户模型的读取闭环):
  question_generator.assemble_acp(node_id) 聚合:
    - _get_tips(node_id)          ← 累积批注  (EpisodicNode{source_description, node_id})
    - _get_error_history(node_id) ← 错误标记  (EpisodicNode{source_description, node_id})
    - _get_edge_reasons(node_id)  ← 节点增殖原因 (CanvasNode-[CANVAS_EDGE{label}]->CanvasNode)

三层探针 (DD-03: 全用真实 Neo4j + 真实服务, 无 mock):
  Probe 0  真实数据普查 — 你现有图谱里 canonical EpisodicNode 有多少带 node_id
           (直接照出 GAP-D: 真实批注能否被 _get_tips 查到)
  Layer 1  读路径正确性 — 隔离 seed 正确形状数据 → 跑读查询 → 断言非空
           (证明读查询本身对; 隔离 test 标识, 跑完清理)
  Layer 2  写路径真实性 — 真调 record_knowledge_entity → 查产出 EpisodicNode 是否带可查 node_id
           (GAP-D 决定性证据; 依赖 worker/Gemini, 不可用时降级报告)

用法 (需 Neo4j 在跑, 否则 JSON fallback 不算真验证):
  cd backend && .venv/bin/python scripts/verify_targeted_exam_chain.py
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# standalone 脚本: 把 backend 根加进 path (scripts/ 的父目录), 否则 import app 失败
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 隔离 test 标识 (跑完清理, 不污染真实图谱)
PROBE = "__e2e_probe__"
T_NODE = f"{PROBE}_node_src"
T_NODE2 = f"{PROBE}_node_tgt"
T_NODE_W = f"{PROBE}_node_write"
T_CANVAS = f"{PROBE}_canvas"
T_GROUP = "vault:__e2e_probe__:main"

CALLOUT_SRC = "callout-annotation-record"
ERROR_SRC = "misconception-record"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"  {GREEN}✅ PASS{RESET}  {msg}")


def fail(msg: str) -> None:
    print(f"  {RED}❌ BREAK{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}⚠️  {RESET}{msg}")


def header(msg: str) -> None:
    print(f"\n{'=' * 72}\n{msg}\n{'=' * 72}")


async def _cleanup(client) -> None:
    """删除所有 probe 数据 (幂等)。"""
    await client.run_query(
        "MATCH (e:EpisodicNode) WHERE e.node_id STARTS WITH $p DETACH DELETE e", p=PROBE
    )
    await client.run_query(
        "MATCH (n:CanvasNode) WHERE n.id STARTS WITH $p DETACH DELETE n", p=PROBE
    )


async def probe0_real_data_census(client) -> None:
    """Probe 0: 你现有真实图谱里, canonical 批注 EpisodicNode 有多少带 node_id。"""
    header("Probe 0 — 真实数据普查 (你现有图谱的累积批注可查性)")
    rows = await client.run_query(
        """
        MATCH (e:EpisodicNode)
        WHERE e.source_description IN [
            'learning-tip-record', 'callout-annotation-record',
            'misconception-record', 'problem-trap-record',
            'logical-fallacy-record', 'guided-thinking-record'
        ]
        RETURN
          count(e) AS total,
          count(CASE WHEN e.node_id IS NOT NULL AND e.node_id <> '' THEN 1 END) AS with_node_id
        """
    )
    if not rows:
        warn("查询无返回 (图谱可能为空)。")
        return
    total = rows[0].get("total", 0)
    with_nid = rows[0].get("with_node_id", 0)
    print(f"  canonical 批注/错误 EpisodicNode 总数: {total}")
    print(f"  其中带可查 node_id 的:            {with_nid}")
    if total == 0:
        warn(
            "图谱里还没有 canonical 批注节点 (你可能还没在真实 vault 打过批注, 或写入未落库)。"
        )
    elif with_nid == 0:
        fail(
            f"GAP-D 实锤: {total} 条批注/错误节点【全部缺 node_id】→ "
            f"_get_tips/_get_error_history 的 `AND e.node_id = $node_id` 永远 0 命中 → "
            f"检验白板看不到你的累积批注。"
        )
    elif with_nid < total:
        warn(
            f"部分缺失: {total - with_nid}/{total} 条缺 node_id (这部分批注检验白板取不到)。"
        )
    else:
        ok(f"全部 {total} 条批注/错误节点都带 node_id (累积批注可被检验白板查到)。")


async def layer1_read_correctness(client) -> bool:
    """Layer 1: seed 正确形状数据 → 跑读查询 → 断言非空 (证明读查询本身对)。"""
    header("Layer 1 — 读路径正确性 (seed 正确形状 → 跑 exam 读 → 断言非空)")
    now = datetime.now(timezone.utc).isoformat()

    # seed: 累积批注 + 错误 (EpisodicNode 带 node_id + canonical source_description)
    await client.run_query(
        """
        CREATE (e:EpisodicNode {
            uuid: $u1, node_id: $nid, source_description: $callout_src,
            content: '递归一定要先想 base case', created_at: $now, group_id: $gid
        })
        CREATE (e2:EpisodicNode {
            uuid: $u2, node_id: $nid, source_description: $error_src,
            error_type: 'knowledge_gap', description: '忘了写 base case',
            content: '忘了写 base case', created_at: $now, group_id: $gid
        })
        """,
        u1=f"{PROBE}-ep1",
        u2=f"{PROBE}-ep2",
        nid=T_NODE,
        callout_src=CALLOUT_SRC,
        error_src=ERROR_SRC,
        now=now,
        gid=T_GROUP,
    )
    # seed: 节点增殖 + 原因边 (CanvasNode-[CANVAS_EDGE{label}]->CanvasNode)
    await client.run_query(
        """
        MERGE (a:CanvasNode {id: $src}) SET a.canvasId = $cv
        MERGE (b:CanvasNode {id: $tgt}) SET b.canvasId = $cv
        MERGE (a)-[r:CANVAS_EDGE {id: $eid}]->(b)
        SET r.label = $label, r.canvasId = $cv, r.createdAt = $now
        """,
        src=T_NODE,
        tgt=T_NODE2,
        cv=T_CANVAS,
        eid=f"{PROBE}-edge",
        label="base case 是 recursion 的前置 — 学递归必须先懂它",
        now=now,
    )

    # 跑真实 exam 读路径
    from app.services.question_generator import QuestionGenerator

    qg = QuestionGenerator()
    tips = await qg._get_tips(T_NODE)
    errors = await qg._get_error_history(T_NODE)
    reasons = await qg._get_edge_reasons(T_NODE)

    all_pass = True
    if tips:
        ok(f"_get_tips 读到累积批注: {tips}")
    else:
        fail("_get_tips 读不到 seed 的批注 (读查询与写 schema 不对齐!)")
        all_pass = False
    if errors:
        ok(f"_get_error_history 读到错误: {errors}")
    else:
        fail("_get_error_history 读不到 seed 的错误。")
        all_pass = False
    if reasons:
        ok(f"_get_edge_reasons 读到节点增殖原因: {reasons}")
    else:
        fail("_get_edge_reasons 读不到 seed 的原因边 (CANVAS_EDGE.label 不对齐!)")
        all_pass = False

    if all_pass:
        ok("读路径全通: 数据形状正确时, 检验白板能取到批注+错误+原因。")
    return all_pass


async def layer2_write_reality(client) -> None:
    """Layer 2: 真调 record_knowledge_entity → 查产出 EpisodicNode 是否带可查 node_id (GAP-D)。"""
    header("Layer 2 — 写路径真实性 (真实写入是否产出可查 EpisodicNode)")
    try:
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        await svc.initialize()
        await svc.record_knowledge_entity(
            event_type="callout_annotation",
            content="probe: 写入端真实性检验",
            metadata={"node_id": T_NODE_W, "title": "probe"},
            group_id=T_GROUP,
        )
        # Graphiti enqueue 是异步 (worker + Gemini); 给一点时间落库
        await asyncio.sleep(3)
        rows = await client.run_query(
            """
            MATCH (e:EpisodicNode)
            WHERE e.node_id = $nid
            RETURN e.source_description AS src, e.node_id AS node_id
            """,
            nid=T_NODE_W,
        )
        if not rows:
            fail(
                "GAP-D 确认: record_knowledge_entity 调用后, 图谱里【没有】带该 node_id 的 "
                "EpisodicNode → 写入端没产出 _get_tips 能查的节点 (node_id 没落成顶层属性, "
                "或 Graphiti worker/Gemini 未运行)。"
            )
            warn(
                "注: 若 episode_worker / Gemini 未启动, Graphiti add_episode 不会同步落库; "
                "这种情况也证明'纯靠 worker 异步'时检验白板取不到刚打的批注。"
            )
        else:
            srcs = [r.get("src") for r in rows]
            ok(f"写入产出 EpisodicNode (node_id={T_NODE_W}, source_description={srcs})")
            if any(
                s in ("learning-tip-record", "callout-annotation-record") for s in srcs
            ):
                ok("且 source_description 是 canonical → _get_tips 能查到。")
            else:
                fail(
                    f"但 source_description={srcs} 不在 _get_tips 的 canonical 白名单。"
                )
    except Exception as e:  # noqa: BLE001 — 诊断脚本, 任何异常都报告不中断
        warn(f"Layer 2 无法完整执行 (服务依赖未就绪): {type(e).__name__}: {e}")
        warn("可在后端完整启动 (worker + Gemini) 后重跑本层。")


async def layer3_node_spawn_reason(client) -> bool:
    """Layer 3 (GAP-E): 临时 vault md frontmatter relationships → sync → _get_edge_reasons。

    模拟用户拉新节点标原因 → Fix-E1 后端扫描 → 检验白板读到原因。
    """
    import shutil
    import tempfile

    header("Layer 3 — 节点增殖原因边 (frontmatter → Fix-E1 sync → _get_edge_reasons)")
    reason = "base case 是 recursion 的前置 — 我为此拉出这个节点"
    tmpdir = tempfile.mkdtemp(prefix="e2e_probe_vault_")
    try:
        md = Path(tmpdir) / f"{T_NODE}.md"
        md.write_text(
            "---\n"
            "type: concept\n"
            "relationships:\n"
            "  - type: prerequisite\n"
            f'    target: "[[{T_NODE2}]]"\n'
            f"    description: {reason}\n"
            "---\n\n选中文本派生而来。\n",
            encoding="utf-8",
        )

        from app.services.canvas_projection_sync import (
            get_canvas_projection_sync,
        )

        result = await get_canvas_projection_sync().sync(tmpdir)
        print(f"  Fix-E1 sync: {result}")

        from app.services.question_generator import QuestionGenerator

        reasons = await QuestionGenerator()._get_edge_reasons(T_NODE)
        if reason in reasons:
            ok(f"_get_edge_reasons 读到节点增殖原因: {reasons}")
            return True
        fail(f"_get_edge_reasons 没读到同步的原因 (得到: {reasons})")
        return False
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


async def main() -> int:
    from app.clients.neo4j_client import get_neo4j_client

    client = get_neo4j_client()
    await client.run_query("RETURN 1 AS ok")  # 触发初始化

    if getattr(client, "_use_json_fallback", False):
        print(
            f"{RED}Neo4j 处于 JSON fallback 模式 (未连真实 Neo4j) — 这不算真验证。{RESET}"
        )
        print("请先启动 Neo4j (docker compose up) 再跑本脚本。")
        return 2

    print(f"{GREEN}已连真实 Neo4j。开始三层探针。{RESET}")
    try:
        await _cleanup(client)  # 清旧 probe 残留
        await probe0_real_data_census(client)
        l1 = await layer1_read_correctness(client)
        await layer2_write_reality(client)
        l3 = await layer3_node_spawn_reason(client)
    finally:
        await _cleanup(client)
        print(f"\n{GREEN}probe 数据已清理。{RESET}")

    header("结论")
    print("  · Probe 0 = 你真实图谱里累积批注的可查性 (GAP-D 现实证据)")
    print("  · Layer 1 = 读查询本身对不对 (数据形状正确时能否取到)")
    print("  · Layer 2 = 真实写入端产出的形状对不对 (GAP-D 写侧根因)")
    print("  · Layer 3 = 节点增殖原因边写→读 (GAP-E: Fix-E1 frontmatter→CANVAS_EDGE)")
    print(
        "  若 Layer 1 ✅ 但 Probe0/Layer2 ❌ → 读对、写断 → 修写入端补 node_id 即可打通主链。"
    )
    return 0 if (l1 and l3) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
