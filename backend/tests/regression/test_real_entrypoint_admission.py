"""P1-05d C1 (Codex 四轮 V1/V2) — 真实入口的 containment 行为锁。

四轮实锤: vault 外文件正文经 `节点/escape.md` symlink 被 LanceDB 全量/单文件
两条**真实入口** open→嵌入→落库; orchestrator 扫描在 should_index 拒绝之前
就对禁区文件 open+SHA-256 (hash-before-admission)。

测试手段申报 (对齐 T-01 诚实化要求):
  - LanceDB 两项调**真实入口函数** (index_single_file / index_vault_notes) +
    真实临时 db 目录。被拒路径在 embedding 之前返回, 断言不依赖 embedding 服务;
    行为断言 = 返回 0 + db 目录零表落盘 (非源码字符串)。
  - orchestrator 两项用 `__new__` 注入 vault_path/_skip_dirs 后执行**真实**
    _scan_vault_md_files (os.walk 全真) 与 should_index — 注入的只是构造参数,
    函数本体零替身。
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.config import settings as _settings


@pytest.fixture
def escape_vault(tmp_path, monkeypatch):
    """真实临时 vault: 合法节点 + vault 外 symlink + 大小写变体禁区目录。"""
    monkeypatch.setattr(_settings, "VAULT_INDEX_SKIP_DIRS", ".git")  # hostile: 只留一项
    vault = tmp_path / "vault"
    (vault / "节点").mkdir(parents=True)
    (vault / "节点" / "合法.md").write_text("# 合法学习内容\n", encoding="utf-8")
    (vault / ".CLAUDE").mkdir()
    (vault / ".CLAUDE" / "private.md").write_text("# 禁区-大小写变体\n", encoding="utf-8")
    outside = tmp_path / "outside_secret.md"
    outside.write_text("OUTSIDE-SENTINEL-b7f2 泄漏哨兵正文", encoding="utf-8")
    (vault / "节点" / "escape.md").symlink_to(outside)
    return vault


def _db_has_sentinel(db_dir: Path) -> bool:
    """db 目录任何落盘文件里出现哨兵串 = 越界正文被索引。"""
    if not db_dir.exists():
        return False
    for f in db_dir.rglob("*"):
        if f.is_file():
            try:
                if b"OUTSIDE-SENTINEL-b7f2" in f.read_bytes():
                    return True
            except OSError:
                continue
    return False


@pytest.mark.asyncio
async def test_real_single_file_entry_rejects_outside_symlink(escape_vault, tmp_path):
    """V2 实锤复现的正面: 真实 index_single_file 对越界 symlink 必须 0 落盘。"""
    from agentic_rag.clients.lancedb_client import LanceDBClient

    db_dir = tmp_path / "db_single"
    client = LanceDBClient(db_path=str(db_dir))

    chunks = await client.index_single_file(
        file_path=str(escape_vault / "节点" / "escape.md"),
        vault_path=str(escape_vault),
    )

    assert chunks == 0, "越界 symlink 被真实单文件入口索引 (V2 回归)"
    assert not _db_has_sentinel(db_dir), "vault 外正文落盘"


@pytest.mark.asyncio
async def test_real_full_scan_entry_rejects_symlink_and_case_variant(escape_vault, tmp_path, monkeypatch):
    """全量入口: vault 只含 越界 symlink + 大小写变体禁区 + (删掉合法文件) →
    收集为空, 零索引零落盘 — 不依赖 embedding (early return 在 embed 之前)。"""
    from agentic_rag.clients.lancedb_client import LanceDBClient

    (escape_vault / "节点" / "合法.md").unlink()  # 只留被拒面
    db_dir = tmp_path / "db_full"
    client = LanceDBClient(db_path=str(db_dir))

    chunks = await client.index_vault_notes(vault_path=str(escape_vault))

    assert chunks == 0, "全量入口索引了被拒文件 (V2/V1 回归)"
    assert not _db_has_sentinel(db_dir)


def test_real_orchestrator_scan_excludes_before_hash(escape_vault):
    """V1: 扫描产出即最终 hash 集 — 被拒文件不得出现在产出里
    (曾在 should_index 拒绝前被指纹 diff open+SHA-256)。"""
    from app.services.vault_index_orchestrator import VaultIndexOrchestrator

    orch = VaultIndexOrchestrator.__new__(VaultIndexOrchestrator)
    orch.vault_path = str(escape_vault)
    orch._skip_dirs = _settings.effective_vault_skip_dirs()

    produced = {os.path.relpath(p, str(escape_vault)) for p in orch._scan_vault_md_files()}

    assert "节点/合法.md" in produced, "误伤合法内容"
    assert ".CLAUDE/private.md" not in produced, "大小写变体禁区进入 hash 集 (V1 回归)"
    assert "节点/escape.md" not in produced, "越界 symlink 进入 hash 集 (V1 回归)"


def test_real_orchestrator_should_index_rejects_symlink_escape(escape_vault):
    """V1: should_index 纯字符串判定曾放行越界 symlink — realpath containment 后拒。"""
    from app.services.vault_index_orchestrator import VaultIndexOrchestrator

    orch = VaultIndexOrchestrator.__new__(VaultIndexOrchestrator)
    orch.vault_path = str(escape_vault)
    orch._skip_dirs = _settings.effective_vault_skip_dirs()

    assert orch.should_index("节点/escape.md") == (False, "outside_vault")
    assert orch.should_index("节点/合法.md") == (True, "ok")


@pytest.mark.asyncio
async def test_by_node_missing_maps_to_not_found_signal(escape_vault):
    """四轮裁量 (DD-13): missing note 曾返回成功样空结果, 文档承诺 404 —
    service 层显式 note_not_found 信号 (端点映射 404)。"""
    from app.services.relationship_sync_service import sync_relationships_for_note

    result = await sync_relationships_for_note("节点/不存在.md", escape_vault, group_id="vault:test")

    assert result["errors"] == ["note_not_found"]
