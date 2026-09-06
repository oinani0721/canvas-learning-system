"""Story 1.1 Task 4-5: Startup health check and setup wizard tests.

Verifies the startup_health_check endpoint returns structured results
for each component, and the setup-wizard orchestrates initialization.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


class TestStartupCheck:
    """Task 4: GET /api/v1/system/startup-check."""

    def test_endpoint_exists(self, client: TestClient):
        resp = client.get("/api/v1/system/startup-check")
        assert resp.status_code != 404, "startup-check endpoint must exist"

    def test_returns_structured_response(self, client: TestClient):
        resp = client.get("/api/v1/system/startup-check")
        data = resp.json()
        assert "data" in data
        assert "checks" in data["data"]

    def test_each_check_has_required_fields(self, client: TestClient):
        resp = client.get("/api/v1/system/startup-check")
        checks = resp.json()["data"]["checks"]
        for check in checks:
            assert "service" in check
            assert "status" in check
            assert "latency_ms" in check

    def test_checks_neo4j_ollama_fastapi_mcp(self, client: TestClient):
        resp = client.get("/api/v1/system/startup-check")
        checks = resp.json()["data"]["checks"]
        service_names = [c["service"] for c in checks]
        assert "neo4j" in service_names
        assert "ollama" in service_names
        assert "fastapi" in service_names
        assert "mcp" in service_names


class TestSetupWizard:
    """Task 5: POST /api/v1/system/setup-wizard."""

    def test_endpoint_exists(self, client: TestClient, tmp_path: Path):
        # CARD-TEST-hygiene-vaultinit: 原为硬编码 "/tmp/test-vault" —— 每跑一次就在
        # /tmp 下留一份真 vault 骨架 (本卡 (a) 二分实测: 该 nodeid 单跑即产生
        # /tmp/test-vault 且不产生 /tmp/test-vault-wizard)。改走 tmp_path。
        resp = client.post(
            "/api/v1/system/setup-wizard",
            json={"vault_path": str(tmp_path / "test-vault")},
        )
        assert resp.status_code != 404, "setup-wizard endpoint must exist"

    def test_returns_structured_report(self, client: TestClient, tmp_path: Path):
        # CARD-TEST-hygiene-vaultinit: 原为硬编码 "/tmp/test-vault-wizard"。
        resp = client.post(
            "/api/v1/system/setup-wizard",
            json={"vault_path": str(tmp_path / "test-vault-wizard")},
        )
        data = resp.json()
        assert "data" in data
        report = data["data"]
        assert "vault_ready" in report
        assert "plugins" in report
        assert "backend" in report
        assert "overall_status" in report


class TestSetupWizardPathValidation:
    """CARD-TEST-hygiene-vaultinit (b): vault_path 必须是绝对路径。

    为什么在 pydantic 层拒而不是补 `system.py` 的黑名单: `setup_wizard` 里
    `Path(request.vault_path).resolve()` 对相对路径 / 空串是**静默**拼 cwd 的,
    黑名单跑在 resolve() 之后, 看到的已经是一个合法绝对路径 —— 永远追不上。
    """

    @pytest.mark.parametrize(
        "bad_path",
        [
            pytest.param("", id="empty"),
            pytest.param(".", id="dot"),
            pytest.param("./x", id="dot-slash"),
            pytest.param("relative/x", id="relative"),
            pytest.param("   ", id="blank"),
            pytest.param("~/vault", id="tilde-unexpanded"),
        ],
    )
    def test_rejects_non_absolute_path(self, client: TestClient, bad_path: str):
        """这些输入过去都会 resolve() 成 cwd (= backend/), 把骨架写进代码目录。

        `~/vault` 也在内: Path 不展开 ~, resolve() 会把它当相对路径拼 cwd。
        """
        resp = client.post("/api/v1/system/setup-wizard", json={"vault_path": bad_path})
        assert resp.status_code == 422, f"非绝对路径 {bad_path!r} 必须被 pydantic 拒绝, 实得 {resp.status_code}"

    def test_accepts_absolute_path(self, client: TestClient, tmp_path: Path):
        """正控: 合法绝对路径 (macOS tmp_path 形态 /private/var/folders/...) 不被拒。

        patch 掉 startup_health_check —— 它会去连现网 Neo4j 7691 并被 W4 端口门
        哨兵转红, 与本用例要证的「校验器放行绝对路径」无关。
        """
        vault = tmp_path / "accepted-vault"
        fake_health = AsyncMock(return_value={"data": {"checks": [], "overall_status": "ready"}})
        with patch("app.api.v1.system.startup_health_check", fake_health):
            resp = client.post("/api/v1/system/setup-wizard", json={"vault_path": str(vault)})
        assert resp.status_code != 422, f"绝对路径必须放行, 实得 {resp.status_code}: {resp.text[:200]}"
        # 骨架确实落在 tmp_path 内, 而不是仓库里
        assert (vault / "raw").is_dir()
