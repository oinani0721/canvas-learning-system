"""批次2' 线3 补齐 search_error_memories (MEM-FLYWHEEL-2026-07-22)。

方法自 2026-05-13 起被 chat.py /enrich-context 调用但本体从未实现 —
现网 500 (BUG-32DB6194)。锁定契约: 签名 / 错误信号过滤 / error_record schema。
"""

from unittest.mock import AsyncMock, MagicMock, patch

from app.models.service_status import StatusedResult
from app.services.memory_service import MemoryService


def _hit(content, episode_type="graphiti_search", ts="2026-07-20T00:00:00Z"):
    return {
        "episode_id": "ep-1",
        "content": content,
        "episode_type": episode_type,
        "timestamp": ts,
        "group_id": "vault:cs_61b",
    }


async def _call(hits, **kwargs):
    """四条用例共用的调用壳 —— CARD-W4-3c 把它从「假 mock」改成真 mock。

    ⛔ 旧写法 patch 的是 ``svc.search_memories``（``memory_service.py:2450``），
    那是一个**兼容壳**：它自己反过来委托 ``search_memories_with_status``。而被测的
    ``search_error_memories`` → ``search_error_memories_with_status``（``:2477``）
    在 ``:2496`` **直接**调 ``self.search_memories_with_status`` —— 压根不经过那层壳。
    于是 patch 落在一条没人走的路上，真实链路一路走下去（2026-09-04 装门实测，
    哨兵报 ``blocked=1``；本车道 2026-09-05 复现，地址 ``('::1', 7691, 0, 0)``）：

        memory_service.py:2496 ``self.search_memories_with_status()``
          -> :2319 ``await self.initialize()``
          -> :278  ``await self.neo4j.initialize()``
          -> neo4j_client.py:402 ``health_check()`` -> ``verify_connectivity()``
          -> bolt://…:7691（现网库）

    连接异常被 ``health_check`` 吞成 "Falling back to JSON storage mode" ——
    **在这道门存在之前，用例照样绿**，所以它一直在偷连正式库而没人发现。
    这是第十批集成树的门在 ``tests/regression`` 目录级跑里抓到的第二个主干既有偷连
    （第一个是 ``test_story_38_3``，范式见
    ``tests/unit/test_story_38_3_fsrs_init_guarantee.py``）。

    ⚠️ 时态要分清（2026-09-05 本车道实测）：门装上**之后**，同一份旧代码是
    ``3 failed, 1 passed`` + ``blocked=1`` —— 结账哨兵把「用例期间发生过拦截」
    转成了用例失败。1 条能过是因为 ``Neo4jClient`` 单例首次 initialize 失败后转
    JSON fallback、后续不再重连（台账里那个「×3」正是这个口径）。
    所以本卡的验收判据是 **blocked=0 且 mock 被 assert_awaited**，
    **不是**「用例数从 3 红变 0 红」。

    两处修正，缺一不可：

    1. **patch 目标改成被测路径真正调用的那个方法** ``search_memories_with_status``，
       返回值形状随之变成 ``StatusedResult``（与 ``:2530`` 同源），
       由 ``:2501 search_result.items`` 取回 list —— 断言语义一字不变。
    2. **构造时注入 ``neo4j_client``**：``__init__``（``:231-243``）写的是
       ``self.neo4j = neo4j_client or get_neo4j_client()``，不注入就抓**进程单例**，
       本文件会顺手污染它（单例首次 initialize 失败后转 JSON fallback、后续不再重连，
       台账里那个「×3」正是这么来的 —— 所以**「3 变 0」不能当验收判据**）。

    ⚠️ ``assert_awaited_once()`` 是**防回归断言**：它证明 patch 真的落在被测路径上。
    它与门是**两层**，不能互相替代：

    * 门（结账哨兵）只在**真的发生了连接尝试**时才说话。它管的是后果。
    * 本断言管的是原因 —— patch 有没有打在被测路径上。目标一旦被改回兼容壳，
      它当场报 "Expected to have been awaited once. Awaited 0 times."，
      直接指向根因；而门那边给出的是一条 health_check 警告，要顺着链路读半天。

    ⚠️ 别把「删掉断言会不会红」当成它的价值判据（2026-09-05 实测：只删断言仍
    ``4 passed`` + ``blocked=0``，因为链路没变）。它防的是**下一个人把 patch 目标
    改回去**——那时门在场会给 3 红，门不在场就又是一次无人察觉的偷连。
    """
    svc = MemoryService(neo4j_client=MagicMock())
    mock_search = AsyncMock(return_value=StatusedResult.from_items(hits))
    with patch.object(svc, "search_memories_with_status", new=mock_search):
        records = await svc.search_error_memories(node_id="Eigenvalues", group_id="vault:cs_61b", **kwargs)
    mock_search.assert_awaited_once()
    return records


async def test_filters_to_error_signals_only():
    hits = [
        _hit("学生混淆了 admissibility 和 consistency"),
        _hit("PCA uses 协方差矩阵的特征向量"),  # 无错误信号 → 排除
        _hit("mistake: forgot base case in recursion"),
    ]
    records = await _call(hits)
    assert len(records) == 2
    assert all("特征向量" not in r["description"] for r in records)


async def test_error_record_schema_complete():
    records = await _call([_hit("误解: DFS 一定找到最短路")])
    r = records[0]
    for field in (
        "error_type",
        "description",
        "corrected_at",
        "tags",
        "source_session",
        "_episode_id",
        "_node_id",
    ):
        assert field in r, f"缺 schema 字段 {field}"
    assert r["_node_id"] == "Eigenvalues"
    assert r["corrected_at"] == "2026-07-20T00:00:00Z"


async def test_limit_respected():
    hits = [_hit(f"错误记录 {i}") for i in range(10)]
    records = await _call(hits, limit=3)
    assert len(records) == 3


async def test_empty_hits_returns_empty_list():
    assert await _call([]) == []
