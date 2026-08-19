"""终验审查修正 — 幽灵边对账保护语义 (2026-07-24, ChatGPT 第三轮 §幽灵边)。

「未扫描到 ≠ 不存在」: 解析失败的文件旧边豁免失效, 写失败的边计入 alive,
只有「文件确认无此关系」才允许失效。
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.canvas_projection_sync import CanvasProjectionSync


def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    (vault / "节点").mkdir(parents=True)
    return vault


def _write(vault: Path, name: str, content: str) -> None:
    (vault / "节点" / f"{name}.md").write_text(content, encoding="utf-8")


async def _run_sync(vault: Path):
    sync = CanvasProjectionSync()
    client = MagicMock()
    client.run_query = AsyncMock(return_value=[{"c": 0}])
    with patch.object(sync, "_client", return_value=client):
        result = await sync.sync(str(vault), group_id="vault:test", execute=True)
    return result, client


async def test_broken_frontmatter_protects_old_edges(tmp_path):
    """解析失败的文件 → 其边前缀进 protected, 失效查询排除它。"""
    vault = _make_vault(tmp_path)
    _write(vault, "broken", "---\nrelationships: [unclosed\n---\n正文")
    _write(
        vault,
        "good",
        '---\nrelationships:\n  - type: extends\n    target: "[[other]]"\n---\n',
    )
    _, client = await _run_sync(vault)
    invalidate_call = client.run_query.call_args_list[-1]
    protected = invalidate_call.kwargs["protected"]
    assert any("broken" in p for p in protected), "损坏文件的边前缀应被保护"
    assert "invalidated_at IS NULL" in invalidate_call.args[0]
    assert "STARTS WITH p" in invalidate_call.args[0]


async def test_missing_relationships_field_not_protected(tmp_path):
    """字段缺失 = 正常无关系 → 不保护 (用户删光关系正是失效该发生的场景)。"""
    vault = _make_vault(tmp_path)
    _write(vault, "plain", "---\ntype: concept\n---\n正文无关系")
    _, client = await _run_sync(vault)
    protected = client.run_query.call_args_list[-1].kwargs["protected"]
    assert protected == []


async def test_merge_failure_edge_still_alive(tmp_path):
    """写入失败的边仍计入 alive — 写失败 ≠ 边该死。"""
    vault = _make_vault(tmp_path)
    _write(
        vault,
        "src",
        '---\nrelationships:\n  - type: extends\n    target: "[[dst]]"\n---\n',
    )
    sync = CanvasProjectionSync()
    client = MagicMock()

    async def run_query(cypher, **kwargs):
        if "MERGE" in cypher:
            raise ConnectionError("boom")
        return [{"c": 0}]

    client.run_query = AsyncMock(side_effect=run_query)
    with patch.object(sync, "_client", return_value=client):
        result = await sync.sync(str(vault), group_id="vault:test", execute=True)
    assert result["failed"] == 1
    alive = client.run_query.call_args_list[-1].kwargs["alive_ids"]
    assert any("src" in e and "dst" in e for e in alive)
