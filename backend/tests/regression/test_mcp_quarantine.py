"""P0-2 MCP 写侧隔离回归测试 (2026-07-31 二轮对抗审查).

契约（quarantine-first-delete-second 第一阶段）:
1. 14 个隔离工具的路径返回 410（不是 404 —— 隐藏调用方能得到明确信号 + 服务端日志现形）。
2. 隔离路径不出现在 OpenAPI schema（include_in_schema=False → FastApiMCP
   include_tags 过滤后也不会进 MCP 工具列表）。
3. 打 "MCP Tools" tag 的存活路由恰为 6 个只读工具，多一个少一个都算回归
   —— 新增 MCP 写工具必须先过 approval token 设计，不允许静默重新暴露。
   (RAG-S2.5-2026-08-10: +get_board_manifest 只读结构读模型, 5→6)
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.mcp.server import QUARANTINED_MCP_TOOLS, _register_tool_routes

ALLOWED_READONLY_TOOLS = {
    "search_memories",
    "search_notes",
    "get_neighbors",
    "read_note",
    "check_backend_health",
    "get_board_manifest",  # RAG-S2.5: 白板结构读模型 (只读)
}


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = FastAPI()
    _register_tool_routes(app)
    return TestClient(app)


def test_quarantine_list_covers_14_tools():
    assert len(QUARANTINED_MCP_TOOLS) == 14
    assert set(QUARANTINED_MCP_TOOLS).isdisjoint(ALLOWED_READONLY_TOOLS)


@pytest.mark.parametrize("tool_name", QUARANTINED_MCP_TOOLS)
def test_quarantined_tool_returns_410(client: TestClient, tool_name: str):
    resp = client.post(f"/mcp/tools/{tool_name}", json={})
    assert resp.status_code == 410, f"{tool_name} 应返回 410 Gone（隔离态），实际 {resp.status_code}"
    body = resp.json()
    assert body["error"] == "gone"
    assert tool_name in body["detail"]


@pytest.mark.parametrize("tool_name", QUARANTINED_MCP_TOOLS)
def test_quarantined_tool_absent_from_openapi(client: TestClient, tool_name: str):
    paths = client.app.openapi()["paths"]
    assert f"/mcp/tools/{tool_name}" not in paths, f"{tool_name} 不得出现在 OpenAPI —— 否则 FastApiMCP 可能重新暴露它"


def test_exactly_five_readonly_tools_tagged_for_mcp(client: TestClient):
    schema = client.app.openapi()
    mcp_tagged = {
        path.removeprefix("/mcp/tools/")
        for path, ops in schema["paths"].items()
        if path.startswith("/mcp/tools/") and any("MCP Tools" in op.get("tags", []) for op in ops.values())
    }
    assert mcp_tagged == ALLOWED_READONLY_TOOLS, (
        f"MCP 暴露面漂移: 期望 {sorted(ALLOWED_READONLY_TOOLS)}, 实际 {sorted(mcp_tagged)}"
    )


def test_fastapi_mcp_tools_list_exposes_exactly_five(client: TestClient):
    """构造层验证真实 MCP 暴露面（审查 MEDIUM-3）。

    OpenAPI 投影只是代理指标 —— FastApiMCP 构造时的 tools/operation_map
    才是 JSON-RPC tools/list 与 tools/call 的真实可达面。若未来任何
    router 给路由打上 "MCP Tools" tag，或隔离 stub 意外进入 schema，
    此测试直接在暴露层报警。
    """
    FastApiMCP = pytest.importorskip("fastapi_mcp").FastApiMCP

    mcp = FastApiMCP(client.app, name="quarantine-test", include_tags=["MCP Tools"])
    exposed = {t.name for t in mcp.tools}
    assert exposed == ALLOWED_READONLY_TOOLS, (
        f"FastApiMCP 真实暴露面漂移: 期望 {sorted(ALLOWED_READONLY_TOOLS)}, 实际 {sorted(exposed)}"
    )
    assert set(mcp.operation_map) == ALLOWED_READONLY_TOOLS, "tools/call 可达面 (operation_map) 与只读白名单不一致"


def test_get_board_manifest_input_schema_exposes_params(client: TestClient):
    """RAG-S2.5 UAT 实锤回归锁: handler 用 `X | None = None` 签名时 requestBody
    变 anyOf, fastapi-mcp 展不开 properties → MCP inputSchema 参数全丢,
    Claudian 只能无参列板 (board_id/view 调不出)。参数面必须完整暴露。"""
    FastApiMCP = pytest.importorskip("fastapi_mcp").FastApiMCP

    mcp = FastApiMCP(client.app, name="schema-test", include_tags=["MCP Tools"])
    (tool,) = [t for t in mcp.tools if t.name == "get_board_manifest"]
    props = set((tool.inputSchema or {}).get("properties", {}))
    assert {"board_id", "view", "include_exam_history"} <= props, f"get_board_manifest MCP 参数面缺失: {sorted(props)}"
