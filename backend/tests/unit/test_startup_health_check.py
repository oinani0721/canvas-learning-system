"""Story 1.1 Task 4-5: Startup health check and setup wizard tests.

Verifies the startup_health_check endpoint returns structured results
for each component, and the setup-wizard orchestrates initialization.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security import INTERNAL_API_KEY_HEADER_NAME
from tests.support.authed_client import (  # noqa: F401 — authed_client 由 fixture 请求
    authed_client,
    authed_settings_override,
)
from tests.support.lifespan import no_lifespan

#: 桩件返回的 message。⛔ 不抄真实异常文案 —— 那会让读者以为这里真去连过一次
#: (DD-13 名实一致)。断言只看字段存在性, 不看内容 (:37-40 / :74-77)。
_STUB_DETAIL = "stubbed by unit test: live Neo4j is never dialled here (W4 port gate)"


@pytest.fixture(autouse=True)
def stub_neo4j_probe():
    """把 ``_check_neo4j`` 换成**不开 socket** 的等价件。

    为什么打在这一层: ``app/api/v1/system.py:47-74`` 的 ``_check_neo4j`` 每次被调
    都新建一个 ``AsyncGraphDatabase.driver`` 并 ``session.run("RETURN 1")`` ——
    socket 就开在这里, 而 :72-74 的 ``except`` 把连接异常吞成一个 "unhealthy"
    的 ``ComponentStatus``。``startup_health_check`` :258-260 与 ``setup_wizard``
    :478 (它内部再调 ``startup_health_check``) 都在调用时从**模块全局**解析这个
    名字, 所以 patch 模块属性一处即可覆盖本文件全部端点用例。

    为什么返回 "unhealthy" 而不是 "healthy": 桩件必须复刻**今天这个环境里的产物**
    —— W4 端口门在, 真实 ``_check_neo4j`` 走的就是 :72-74 那条 except 分支。返
    "healthy" 会悄悄换掉被测语义 (例如让 ``_probe_with_timeout`` 的
    "unhealthy"→"unavailable" 映射失效)。⛔ 本 fixture 不放宽端口门、不改生产码。
    """
    from app.api.v1.system import ComponentStatus

    stub = AsyncMock(return_value=ComponentStatus(name="neo4j", status="unhealthy", message=_STUB_DETAIL))
    with patch("app.api.v1.system._check_neo4j", stub):
        yield stub


@pytest.fixture
def client(authed_client: TestClient) -> TestClient:  # noqa: F811
    """带 ``X-CLS-Internal-Key`` 的 TestClient (``tests/support/authed_client.py``)。

    ``system.py:28`` 的 router 自本卡起挂 ``require_internal_api_key``, 裸
    ``TestClient(app)`` 会在业务逻辑之前被 ``security.py:144-152`` 判 403。
    """
    return authed_client


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


#: 「这个键本来不存在」与「本来是 None」的区分哨兵 —— 退出还原时用。
_ABSENT = object()


class TestSystemRouterAuth:
    """CARD-RED-A1-sentinel (g): ``system.py:28`` 的 router 级鉴权真的挂上了。

    没有这两条, 「所有端点测试都带着 key」与「router 根本没挂依赖」在测试面上
    **不可区分** —— 全绿既可能是鉴权生效, 也可能是它压根不存在。

    期望码是 **403 不是 503**: 两档共用 ``authed_settings_override`` (已配置 key
    + ``DEBUG=True``), 落 ``app/security.py:144-152`` Branch 3。503 只来自 Branch 1
    (:96-105, ``DEBUG=False`` + 空 key) 与 Branch 2 (:110-142, ``DEBUG=True`` +
    空 key + 无 loopback bypass), 本档一个都不沾。Branch 1 那档在本分支连
    ``Settings`` 都建不出来 (``app/config.py:295-298`` 直接 raise), 归 U10-E。
    """

    @pytest.fixture
    def unauthed_client(self):
        """**不带任何 key 头**的 TestClient, settings 档与 ``authed_client`` 逐项相同。

        为什么另起一个而不是在 ``authed_client`` 上「不带头」: 后者把 key 挂在
        ``TestClient(app, headers=...)`` 的**实例级默认头**上, httpx 会把默认头并
        进它发出的每个请求 —— 在那个 client 上发不出「一个头都不带」的请求, 照字
        面写会得到「用例名说不带头、实际带着头」的名实不符 (DD-13)。

        settings 复用 ``authed_settings_override`` 而不是自己抄一份, 免得两处
        Settings 在别的字段上分叉。⛔ 只 import, 不改 ``tests/support/authed_client.py``。
        """
        from app.config import get_settings

        previous = app.dependency_overrides.get(get_settings, _ABSENT)
        app.dependency_overrides[get_settings] = authed_settings_override
        try:
            with no_lifespan(app), TestClient(app) as test_client:
                yield test_client
        finally:
            if previous is _ABSENT:
                app.dependency_overrides.pop(get_settings, None)
            else:
                app.dependency_overrides[get_settings] = previous

    def test_system_router_rejects_without_key_403(self, unauthed_client: TestClient):
        """无 key 头 ⇒ 403, 且 detail 逐字绑到 Branch 3。

        只断状态码不够: Branch 1/2 也可能被别的配置变更打出来, 但它们的 detail 是
        ``Internal API key not configured…``。绑住文案 = 绑住「被哪一层拒的」。
        """
        resp = unauthed_client.get("/api/v1/system/startup-check")
        assert resp.status_code == 403, f"实得 {resp.status_code}: {resp.text[:200]}"
        assert resp.json()["detail"] == "Invalid internal API key"

    def test_system_router_accepts_with_key_200(self, client: TestClient):
        """同一端点带正确 key ⇒ 原状态码 200 (鉴权没有顺手打坏正常路径)。"""
        resp = client.get("/api/v1/system/startup-check")
        assert resp.status_code == 200, f"实得 {resp.status_code}: {resp.text[:200]}"

    def test_wrong_key_also_403(self, unauthed_client: TestClient):
        """key 不匹配 (Branch 4 :154-160) 与缺头同码同文案 —— 防「换条分支也能绿」。"""
        resp = unauthed_client.get(
            "/api/v1/system/startup-check",
            headers={INTERNAL_API_KEY_HEADER_NAME: "definitely-not-the-key"},
        )
        assert resp.status_code == 403, f"实得 {resp.status_code}: {resp.text[:200]}"
        assert resp.json()["detail"] == "Invalid internal API key"
