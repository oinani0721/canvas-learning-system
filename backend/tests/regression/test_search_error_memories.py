"""批次2' 线3 补齐 search_error_memories (MEM-FLYWHEEL-2026-07-22)。

方法自 2026-05-13 起被 chat.py /enrich-context 调用但本体从未实现 —
现网 500 (BUG-32DB6194)。锁定契约: 签名 / 错误信号过滤 / error_record schema。
"""

from unittest.mock import AsyncMock, patch

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
    svc = MemoryService()
    with patch.object(svc, "search_memories", new=AsyncMock(return_value=hits)):
        return await svc.search_error_memories(
            node_id="Eigenvalues", group_id="vault:cs_61b", **kwargs
        )


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
