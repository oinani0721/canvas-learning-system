"""Tests for Story 1.6: KG health check + .gitignore generation."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path


class TestGitignoreGeneration:
    def test_creates_gitignore(self, tmp_path):
        from app.services.vault_init_service import VaultInitService

        svc = VaultInitService()
        svc._ensure_gitignore(tmp_path)
        gi = tmp_path / ".gitignore"
        assert gi.exists()
        content = gi.read_text()
        assert "data/lancedb/" in content
        assert "data/neo4j/" in content
        assert ".obsidian/workspace.json" in content

    def test_does_not_overwrite_existing(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text("custom content\n")
        from app.services.vault_init_service import VaultInitService

        VaultInitService._ensure_gitignore(tmp_path)
        assert gi.read_text() == "custom content\n"


class TestGitPluginDetection:
    def test_detects_installed(self, tmp_path):
        from app.services.vault_init_service import VaultInitService

        (tmp_path / ".obsidian" / "plugins" / "obsidian-git").mkdir(parents=True)
        assert VaultInitService.has_git_plugin(str(tmp_path)) is True

    def test_not_installed(self, tmp_path):
        from app.services.vault_init_service import VaultInitService

        assert VaultInitService.has_git_plugin(str(tmp_path)) is False


class TestKGHealthEndpoint:
    @pytest.fixture(autouse=True)
    def stub_neo4j_driver(self):
        """把 ``AsyncGraphDatabase.driver`` 换成不开 socket 的桩 (真连点)。

        ``app/api/v1/endpoints/kg_health.py`` 的 driver 是**端点函数体内**新建的
        (:39 ``from neo4j import AsyncGraphDatabase`` + :41-44 ``.driver(...)``),
        模块全局里没有这个名字 ⇒ 只能 patch ``neo4j.AsyncGraphDatabase.driver``
        本身 —— 函数体内的 import 在调用时从 ``sys.modules['neo4j']`` 解析, 所以
        patch 得到。

        让它抛而不是返回假 driver: 端点 :72-77 的 ``except`` 把任何异常吞成
        ``neo4j_available=False`` + ``error="Neo4j 未连接: …"``, 这正是今天 W4
        端口门在场时的**真实产物**, 用例的两条键存在性断言原样成立。

        ⛔ 生产 ``kg_health.py`` 一字不改 (卡文 §三: 它不在本卡地盘, 只有本测试
        文件在, 且只允许测试侧打桩)。该端点仍无鉴权、真连点仍在 —— 本 fixture
        只保证**单元测试进程**不去拨 7691。
        """
        from unittest.mock import patch

        with patch(
            "neo4j.AsyncGraphDatabase.driver",
            side_effect=RuntimeError("stubbed by unit test: live Neo4j is never dialled here (W4 port gate)"),
        ) as stub:
            yield stub

    @pytest.fixture
    def client(self):
        from app.main import app

        return TestClient(app, raise_server_exceptions=False)

    def test_endpoint_returns_200(self, client):
        resp = client.get("/api/v1/kg/health")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_nodes" in data
        assert "neo4j_available" in data
