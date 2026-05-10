"""Tests for Story 1.8: Vault Switch Runtime API.

Covers AC #1 (switch), #2 (validation), #3 (current), #4 (cache clear).
"""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def _obsidian_vault(tmp_path):
    """Create a temporary directory that looks like an Obsidian vault."""
    vault = tmp_path / "test-vault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    return vault


@pytest.fixture
def _second_vault(tmp_path):
    vault = tmp_path / "second-vault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    return vault


@pytest.fixture
def _non_vault(tmp_path):
    """Directory without .obsidian/ — should fail validation."""
    d = tmp_path / "not-a-vault"
    d.mkdir()
    return d


class TestSanitizeVaultId:
    def test_simple_name(self):
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("canvas-vault") == "canvas_vault"

    def test_spaces_and_caps(self):
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("CS 61B") == "cs_61b"

    def test_special_chars(self):
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("my.vault (2026)") == "my_vault_2026"

    def test_empty_string(self):
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("") == "default"

    def test_chinese_chars_preserved(self):
        """Phase B0.1 (Round-4): CJK 必须保留, 不再坍缩 default 防跨 vault 数据泄漏."""
        from app.config import sanitize_vault_id

        # 旧 bug: assert == "default" (反 pattern 把 bug 当 expected)
        # 修后: CJK 字符保留, vault_id 唯一性恢复
        assert sanitize_vault_id("笔记库") == "笔记库"

    def test_japanese_chars_preserved(self):
        """Phase B0.1: 日文 vault 名保留 (平假名 + 片假名 + 汉字)."""
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("プログラミング") == "プログラミング"
        assert sanitize_vault_id("数学のノート") == "数学のノート"

    def test_korean_chars_preserved(self):
        """Phase B0.1: 韩文 vault 名保留 (谚文音节)."""
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("수학 노트") == "수학_노트"

    def test_mixed_ascii_cjk(self):
        """Phase B0.1: ASCII + CJK 混合 vault 名."""
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("CS 61B 数据结构") == "cs_61b_数据结构"
        assert sanitize_vault_id("Math 101 微积分") == "math_101_微积分"

    def test_distinct_chinese_vaults_no_collision(self):
        """Phase B0.1 P0 防御: 多个中文 vault 不再共享 'default' 命名空间.

        修复前: '数学101' / '英语写作' / '物理实验' 全部 → 'default' 共享 LanceDB table → 数据泄漏
        修复后: 各自独立 vault_id, 互不干扰.
        """
        from app.config import sanitize_vault_id

        a = sanitize_vault_id("数学101")
        b = sanitize_vault_id("英语写作")
        c = sanitize_vault_id("物理实验")
        # 三个 vault_id 必须各不相同 (不再共享 'default')
        assert a == "数学101"
        assert b == "英语写作"
        assert c == "物理实验"
        assert len({a, b, c}) == 3
        assert "default" not in {a, b, c}

    def test_nfkc_normalization(self):
        """Phase B0.1: NFKC 归一化 (拆合字 + 兼容字符)."""
        from app.config import sanitize_vault_id

        # 合字 ﬁ (U+FB01) → fi (NFKC 拆解)
        assert sanitize_vault_id("ﬁle") == "file"
        # 重音 é 保留 (NFKC 不改 NFC 内字符)
        assert sanitize_vault_id("café") == "café"

    def test_emoji_stripped_but_text_preserved(self):
        """Phase B0.1: emoji 不是 \\w → 替为 _, 但相邻 CJK 保留."""
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("📚 笔记本") == "笔记本"

    def test_path_traversal_defused(self):
        """Phase B0.1: shell injection / path traversal 字符全部 → underscore."""
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("../etc/passwd") == "etc_passwd"
        assert sanitize_vault_id("a;rm -rf /") == "a_rm_rf"
        assert sanitize_vault_id("$(whoami)") == "whoami"

    def test_all_special_chars_fallback(self):
        """Phase B0.1: 全特殊字符 → default fallback (与空串行为一致)."""
        from app.config import sanitize_vault_id

        assert sanitize_vault_id("***") == "default"
        assert sanitize_vault_id("!@#$") == "default"
        assert sanitize_vault_id("====") == "default"


class TestReloadSettings:
    def test_cache_clear_picks_up_new_value(self):
        from app.config import get_settings, reload_settings

        original = get_settings().ACTIVE_VAULT

        reload_settings(overrides={"ACTIVE_VAULT": "new-vault"})
        assert get_settings().ACTIVE_VAULT == "new-vault"

        # Restore
        reload_settings(overrides={"ACTIVE_VAULT": original})

    def test_vault_id_changes_after_reload(self):
        from app.config import get_current_vault_id, get_settings, reload_settings

        original = get_settings().ACTIVE_VAULT

        reload_settings(overrides={"ACTIVE_VAULT": "CS 61B"})
        assert get_current_vault_id() == "cs_61b"

        reload_settings(overrides={"ACTIVE_VAULT": original})


class TestVaultSwitchEndpoint:
    """Test POST /api/v1/vault/switch and GET /api/v1/vault/current."""

    @pytest.fixture(autouse=True)
    def _restore_settings(self):
        from app.config import get_settings, reload_settings

        original_path = get_settings().CANVAS_BASE_PATH
        original_vault = get_settings().ACTIVE_VAULT
        yield
        reload_settings(
            overrides={
                "CANVAS_BASE_PATH": original_path,
                "ACTIVE_VAULT": original_vault,
            }
        )

    @pytest.fixture
    def client(self):
        from app.main import app

        return TestClient(app, raise_server_exceptions=False)

    def test_switch_valid_vault(self, client, _obsidian_vault):
        resp = client.post(
            "/api/v1/vault/switch", json={"vault_path": str(_obsidian_vault)}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["vault_name"] == "test-vault"
        assert data["vault_id"] == "test_vault"
        assert data["vault_path"] == str(_obsidian_vault)

    def test_switch_nonexistent_path(self, client, tmp_path):
        resp = client.post(
            "/api/v1/vault/switch", json={"vault_path": str(tmp_path / "nope")}
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"] == "vault_not_found"

    def test_switch_non_vault_dir(self, client, _non_vault):
        resp = client.post("/api/v1/vault/switch", json={"vault_path": str(_non_vault)})
        assert resp.status_code == 400
        assert "missing .obsidian" in resp.json()["detail"]["message"]

    def test_get_current(self, client):
        resp = client.get("/api/v1/vault/current")
        assert resp.status_code == 200
        data = resp.json()
        assert "vault_path" in data
        assert "vault_id" in data

    def test_switch_then_current_reflects_new(self, client, _obsidian_vault):
        client.post("/api/v1/vault/switch", json={"vault_path": str(_obsidian_vault)})
        resp = client.get("/api/v1/vault/current")
        assert resp.json()["vault_name"] == "test-vault"
