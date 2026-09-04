"""BDD tests for the health **route contract**.

[BATCH-2026-09-01-第九批 / CARD-TEST-isolate-lifespan-R1]

⚠️ 承诺边界：根 ``client`` fixture（tests/conftest.py）用 ``no_lifespan`` 关掉了
``app.main`` 的 startup，所以这里跑的**不是**一个真实启动过的服务。本文件只承诺
route-availability：health 路由挂在应用上、按响应契约返回状态码与字段形状。

旧措辞 ``the API server is running`` 是过承诺 —— 第八批实测：把 LanceDB 环境设成
会令 ``app/main.py`` 真实 startup 失败的冲突值后，这两条场景仍 ``2 passed``。
换句话说，那句 Given 断言的东西从来没有被这套测试证明过。真实 startup 的验证需要
integration/e2e 面（安全隔离外部依赖但真实执行 startup），本卡未做，不在此声明。

Uses pytest-bdd to execute Gherkin scenarios.
"""

import pytest
from pytest_bdd import given, parsers, scenario, then, when

pytestmark = pytest.mark.bdd


@scenario("features/health.feature", "Basic health check")
def test_basic_health():
    pass


@scenario("features/health.feature", "Health check includes components")
def test_health_components():
    pass


@given("the health route is mounted on a lifespan-free test client", target_fixture="api_client")
def health_route_mounted(client):
    """只声明「路由表里有 health 这条路由」，不声明「服务已启动」。

    ``client`` 来自根 conftest —— ``with no_lifespan(app), TestClient(app)``，
    startup 副作用整条不跑。这里显式复核路由确实挂着，让这句 Given 有实据：
    否则它只是「把 fixture 原样返回」，什么都没证明。
    """
    paths = {getattr(route, "path", None) for route in client.app.routes}
    assert "/api/v1/health" in paths, f"health 路由未挂在应用上；已挂载路径样本={sorted(p for p in paths if p)[:10]}"
    return client


@when("I request the health endpoint", target_fixture="response")
def request_health(api_client):
    return api_client.get("/api/v1/health")


@then(parsers.parse("the response status is {status:d}"))
def check_status(response, status):
    assert response.status_code == status


@then(parsers.parse('the response contains status "{expected_status}"'))
def check_health_status(response, expected_status):
    data = response.json()
    assert data["status"] == expected_status


@then("the response contains component status")
def check_components(response):
    """字段必须**存在**且是个非空字典。

    R1 Codex MEDIUM：旧实现是 ``if "components" in data: assert isinstance(...)``
    —— 字段整个消失时这条 then 一个断言都不执行，场景照样绿，与它自称的
    「响应契约」不符（一个从不失败的断言不是契约）。
    2026-09-03 实测端点返回的 components 键为
    ``batch_orchestrator / batch_sessions / fsrs / neo4j``。
    """
    data = response.json()
    assert "components" in data, f"响应缺少 components 字段；实得键={sorted(data.keys())}"
    components = data["components"]
    assert isinstance(components, dict), f"components 不是 dict，而是 {type(components).__name__}"
    assert components, "components 是空字典 —— 契约要求它至少报告一个组件"
