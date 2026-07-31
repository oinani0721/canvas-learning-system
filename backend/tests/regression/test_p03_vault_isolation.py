"""P0-3 vault 隔离回归 (2026-07-31 二轮对抗审查).

三条契约:
1. enrich-hook 从 cwd（宿主机路径）按「路径段名 ↔ VAULTS_ROOT vault 目录名」
   推导 vault_id —— 不探测 cwd 文件系统（容器内不可见），无匹配回退全局。
2. tips 四个写 schema 的 vault_id 必填（写侧禁止静默回退全局 vault）。
3. /vault/switch 410 契约在 test_vault_switch.py::TestVaultSwitchQuarantine。
"""

import pytest
from pydantic import ValidationError

from app.api.v1.endpoints.chat import _vault_id_from_hook_cwd


class _FakeSettings:
    def __init__(self, vaults_root: str):
        self.VAULTS_ROOT = vaults_root


@pytest.fixture
def vaults_root(tmp_path, monkeypatch):
    """VAULTS_ROOT 下三个 vault（canvas-vault / 数学 / café-notes）+ 一个非 vault 目录。"""
    for name in ("canvas-vault", "数学", "café-notes"):
        (tmp_path / name / ".obsidian").mkdir(parents=True)
    (tmp_path / "not-a-vault").mkdir()

    import app.config as config_module

    monkeypatch.setattr(config_module, "get_settings", lambda: _FakeSettings(str(tmp_path)))
    return tmp_path


class TestHookCwdVaultDerivation:
    def test_host_cwd_matches_vault_by_segment_name(self, vaults_root):
        # 宿主机路径在容器内不存在 —— 只有段名 "canvas-vault" 匹配注册表
        cwd = "/Users/someone/Desktop/canvas/canvas-learning-system/canvas-vault"
        assert _vault_id_from_hook_cwd(cwd) == "canvas_vault"

    def test_subdirectory_of_vault_matches(self, vaults_root):
        cwd = "/Users/someone/Desktop/x/canvas-vault/节点/深层目录"
        assert _vault_id_from_hook_cwd(cwd) == "canvas_vault"

    def test_cjk_vault_name(self, vaults_root):
        assert _vault_id_from_hook_cwd("/Users/someone/vaults/数学") == "数学"

    def test_none_and_empty_cwd(self, vaults_root):
        assert _vault_id_from_hook_cwd(None) is None
        assert _vault_id_from_hook_cwd("") is None

    def test_unknown_cwd_falls_through(self, vaults_root):
        assert _vault_id_from_hook_cwd("/Users/someone/other-project") is None

    def test_non_vault_dir_name_not_matched(self, vaults_root):
        # 目录存在于 VAULTS_ROOT 但无 .obsidian/ → 不算 vault
        assert _vault_id_from_hook_cwd("/Users/someone/not-a-vault") is None

    def test_multiple_vault_segments_fall_back(self, vaults_root):
        # 审查修正: 路径同时命中多个注册 vault 段名时不猜 —— 返回 None
        # 回退全局 (串库代价高于回退), 并发 warning 日志
        cwd = "/Users/someone/canvas-vault/exports/数学"
        assert _vault_id_from_hook_cwd(cwd) is None

    def test_nfd_cwd_matches_nfc_vault_dir(self, vaults_root):
        # macOS 文件名常为 NFD —— cwd 段与 vault 目录名经 NFC 归一后必须互认。
        # 注意用真正可分解的名字 (é → e+U+0301)；CJK 表意字 NFD==NFC 测不出问题
        import unicodedata

        from app.config import sanitize_vault_id

        nfd = unicodedata.normalize("NFD", "café-notes")
        assert nfd != "café-notes"  # 前置: 该名字确实会分解
        assert _vault_id_from_hook_cwd(f"/Users/someone/vaults/{nfd}") == sanitize_vault_id("café-notes")


class TestEnrichHookEndpointSmoke:
    """端点级冒烟 —— helper 单测接不住调用点的 NameError/接线错误。"""

    def test_hook_with_cwd_does_not_500(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/chat/rag/enrich-hook",
            json={
                "session_id": "p03-smoke",
                "cwd": "/Users/someone/Desktop/anywhere/canvas-vault",
                "prompt": "特征值是什么",
            },
        )
        # 测试环境无 INTERNAL_API_KEY 时会被鉴权层拒 (非 500) —— 冒烟目标只是
        # 排除 handler 内部错误 (如 P0-3 首版的 NameError 500)
        assert resp.status_code != 500, resp.text
        if resp.status_code == 200:
            assert "hookSpecificOutput" in resp.json()


class TestTipsVaultIdRequired:
    """P0-3: tips 写侧 vault_id 必填 —— 空串/缺省都必须被 422 掉。"""

    def _minimal_payloads(self):
        from app.api.v1.endpoints.tips import (
            BatchSyncRequest,
            CalloutDirectRequest,
            SaveRelationRequest,
            SaveTipRequest,
        )

        return [
            (SaveTipRequest, {"node_id": "n1", "content": "tip"}),
            (
                SaveRelationRequest,
                {"source_node": "a", "target_node": "b", "reason": "r"},
            ),
            (BatchSyncRequest, {"file_path": "节点/x.md", "callouts": []}),
            (
                CalloutDirectRequest,
                {"node_id": "n1", "callout_type": "tip", "content": "c"},
            ),
        ]

    def test_empty_vault_id_rejected(self):
        for model, payload in self._minimal_payloads():
            with pytest.raises(ValidationError):
                model(vault_id="", **payload)

    def test_missing_vault_id_rejected(self):
        for model, payload in self._minimal_payloads():
            with pytest.raises(ValidationError):
                model(**payload)
