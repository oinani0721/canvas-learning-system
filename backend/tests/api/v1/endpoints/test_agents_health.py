# Canvas Learning System - Story 12.G.3 Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Story 12.G.3 - Agent Health Check Endpoint Tests

Tests for GET /api/v1/agents/health endpoint:
- AC1: Returns health status (healthy/degraded/unhealthy)
- AC2: Checks API key configuration (without exposing key)
- AC3: Checks GeminiClient initialization
- AC4: Checks prompt template availability
- AC5: Optional API call test (include_api_test=true)
- AC6: 60-second TTL cache (ADR-007)
- AC7: Response matches JSON Schema

[Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#Testing]
[Source: specs/data/health-check-response.schema.json]
"""

import ast
import time
from datetime import datetime, timezone

import pytest
from app.api.v1.endpoints.agents import (
    HEALTH_CHECK_CACHE_TTL,
    get_agent_health,
)
from app.models import (
    AgentHealthCheckResponse,
    AgentHealthChecks,
    AgentHealthStatus,
    PromptTemplateCheck,
)


class MockAgentService:
    """Mock AgentService for testing Story 12.G.3."""

    # 真相源 = backend/app/services/agent_service.py::AgentService.health_check
    # 的局部 expected_templates —— 它决定 /agents/health 的 total/available。
    # 本 mock 不读生产表，所以必须手工同名同序跟随；漂了由
    # test_mock_expected_templates_match_production_truth_source 报。
    # [CARD-RED-HYGIENE] 2026-09-16: 生产已是 13 项（第 13 项 hint-generation），
    # 本 mock 此前停在 12 项，端点测试因此绿着却与生产脱节。
    EXPECTED_TEMPLATES = [
        "basic-decomposition",
        "deep-decomposition",
        "question-decomposition",
        "oral-explanation",
        "four-level-explanation",
        "clarification-path",
        "comparison-table",
        "example-teaching",
        "memory-anchor",
        "scoring-agent",
        "verification-question-agent",
        "canvas-orchestrator",
        "hint-generation",
    ]

    def __init__(
        self,
        api_key_configured: bool = True,
        gemini_initialized: bool = True,
        missing_templates: list[str] | None = None,
        api_test_success: bool = True,
    ):
        """
        Initialize mock service.

        Args:
            api_key_configured: Whether API key is configured
            gemini_initialized: Whether GeminiClient is initialized
            missing_templates: List of missing template names
            api_test_success: Whether API test should succeed
        """
        self.api_key_configured = api_key_configured
        self.gemini_initialized = gemini_initialized
        self.missing_templates = missing_templates or []
        self.api_test_success = api_test_success
        self.health_check_call_count = 0

    async def health_check(self, include_api_test: bool = False) -> dict:
        """Mock health_check method."""
        self.health_check_call_count += 1

        expected_templates = self.EXPECTED_TEMPLATES

        available_count = len(expected_templates) - len(self.missing_templates)

        # Determine status
        if not self.api_key_configured or not self.gemini_initialized:
            status = "unhealthy"
        elif len(self.missing_templates) > 0:
            status = "degraded"
        else:
            status = "healthy"

        api_test_result = {"enabled": False, "result": None}
        if include_api_test:
            if self.api_test_success:
                api_test_result = {"enabled": True, "result": "success"}
            else:
                api_test_result = {"enabled": True, "result": "API Error"}

        return {
            "status": status,
            "checks": {
                "api_key_configured": self.api_key_configured,
                "gemini_client_initialized": self.gemini_initialized,
                "prompt_templates": {
                    "total": len(expected_templates),
                    "available": available_count,
                    "missing": self.missing_templates,
                },
                "api_test": api_test_result,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AC1: Health Status Tests
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_health_check_healthy_status():
    """
    AC1.1: Returns 'healthy' when all checks pass.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-1.1]
    """
    # Clear cache to ensure fresh check
    import app.api.v1.endpoints.agents as agents_module

    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService(
        api_key_configured=True,
        gemini_initialized=True,
        missing_templates=[],
    )

    response = await get_agent_health(mock_service, include_api_test=False)

    assert response.status == AgentHealthStatus.healthy
    assert response.checks.api_key_configured is True
    assert response.checks.gemini_client_initialized is True
    assert response.checks.prompt_templates.total == 13
    assert response.checks.prompt_templates.available == 13
    assert response.checks.prompt_templates.missing == []
    assert response.cached is False


@pytest.mark.asyncio
async def test_health_check_degraded_status():
    """
    AC1.2: Returns 'degraded' when some templates are missing.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-1.2]
    """
    import app.api.v1.endpoints.agents as agents_module

    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService(
        api_key_configured=True,
        gemini_initialized=True,
        missing_templates=["comparison-table", "review-board"],
    )

    response = await get_agent_health(mock_service, include_api_test=False)

    assert response.status == AgentHealthStatus.degraded
    assert response.checks.prompt_templates.missing == [
        "comparison-table",
        "review-board",
    ]
    assert response.checks.prompt_templates.available == 11


@pytest.mark.asyncio
async def test_health_check_unhealthy_no_api_key():
    """
    AC1.3: Returns 'unhealthy' when API key is not configured.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-1.3]
    """
    import app.api.v1.endpoints.agents as agents_module

    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService(
        api_key_configured=False,
        gemini_initialized=True,
    )

    response = await get_agent_health(mock_service, include_api_test=False)

    assert response.status == AgentHealthStatus.unhealthy
    assert response.checks.api_key_configured is False


@pytest.mark.asyncio
async def test_health_check_unhealthy_no_client():
    """
    AC1.4: Returns 'unhealthy' when GeminiClient is not initialized.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-1.4]
    """
    import app.api.v1.endpoints.agents as agents_module

    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService(
        api_key_configured=True,
        gemini_initialized=False,
    )

    response = await get_agent_health(mock_service, include_api_test=False)

    assert response.status == AgentHealthStatus.unhealthy
    assert response.checks.gemini_client_initialized is False


# ═══════════════════════════════════════════════════════════════════════════════
# AC5: Optional API Test
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_health_check_with_api_test_success():
    """
    AC5.1: Returns successful API test result when include_api_test=true.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-5.1]
    """
    import app.api.v1.endpoints.agents as agents_module

    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService(
        api_key_configured=True,
        gemini_initialized=True,
        api_test_success=True,
    )

    response = await get_agent_health(mock_service, include_api_test=True)

    assert response.checks.api_test is not None
    assert response.checks.api_test.enabled is True
    assert response.checks.api_test.result == "success"


@pytest.mark.asyncio
async def test_health_check_with_api_test_failure():
    """
    AC5.2: Returns error message when API test fails.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-5.2]
    """
    import app.api.v1.endpoints.agents as agents_module

    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService(
        api_key_configured=True,
        gemini_initialized=True,
        api_test_success=False,
    )

    response = await get_agent_health(mock_service, include_api_test=True)

    assert response.checks.api_test is not None
    assert response.checks.api_test.enabled is True
    assert response.checks.api_test.result == "API Error"


@pytest.mark.asyncio
async def test_health_check_without_api_test():
    """
    AC5.3: API test is disabled by default.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-5.3]
    """
    import app.api.v1.endpoints.agents as agents_module

    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService()

    response = await get_agent_health(mock_service, include_api_test=False)

    assert response.checks.api_test is not None
    assert response.checks.api_test.enabled is False
    assert response.checks.api_test.result is None


# ═══════════════════════════════════════════════════════════════════════════════
# AC6: Cache Tests (60-second TTL per ADR-007)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_health_check_cache_ttl():
    """
    AC6.1: Results are cached for 60 seconds (ADR-007).

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-6.1]
    [Source: ADR-007 - Cache TTL]
    """
    import app.api.v1.endpoints.agents as agents_module

    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService()

    # First call - should NOT be cached
    response1 = await get_agent_health(mock_service, include_api_test=False)
    assert response1.cached is False
    assert mock_service.health_check_call_count == 1

    # Second call immediately - should be cached
    response2 = await get_agent_health(mock_service, include_api_test=False)
    assert response2.cached is True
    assert mock_service.health_check_call_count == 1  # No additional call

    # Verify cache TTL constant
    assert HEALTH_CHECK_CACHE_TTL == 60


@pytest.mark.asyncio
async def test_health_check_cache_expired():
    """
    AC6.2: Cache is invalidated after 60 seconds.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-6.2]
    """
    import app.api.v1.endpoints.agents as agents_module

    mock_service = MockAgentService()

    # Set cache to expired state (61 seconds ago)
    agents_module._health_check_cache = {
        "health_False": {
            "status": "healthy",
            "checks": {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }
    agents_module._health_check_cache_time = time.time() - 61

    # Call should NOT use cache (expired)
    response = await get_agent_health(mock_service, include_api_test=False)
    assert response.cached is False
    assert mock_service.health_check_call_count == 1


@pytest.mark.asyncio
async def test_health_check_separate_cache_keys():
    """
    AC6.3: Different cache keys for include_api_test=true/false.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-6.3]
    """
    import app.api.v1.endpoints.agents as agents_module

    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService()

    # First call without API test
    response1 = await get_agent_health(mock_service, include_api_test=False)
    assert response1.cached is False
    assert mock_service.health_check_call_count == 1

    # Call with API test - should NOT use cache (different key)
    response2 = await get_agent_health(mock_service, include_api_test=True)
    assert response2.cached is False
    assert mock_service.health_check_call_count == 2


# ═══════════════════════════════════════════════════════════════════════════════
# AC7: Response Model Validation
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_health_check_response_model():
    """
    AC7.1: Response matches AgentHealthCheckResponse model.

    [Source: specs/data/health-check-response.schema.json]
    """
    import app.api.v1.endpoints.agents as agents_module

    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService()

    response = await get_agent_health(mock_service, include_api_test=False)

    # Verify response type
    assert isinstance(response, AgentHealthCheckResponse)
    assert isinstance(response.status, AgentHealthStatus)
    assert isinstance(response.checks, AgentHealthChecks)
    assert isinstance(response.checks.prompt_templates, PromptTemplateCheck)
    assert isinstance(response.timestamp, datetime)
    assert isinstance(response.cached, bool)


@pytest.mark.asyncio
async def test_health_check_timestamp_format():
    """
    AC7.2: Timestamp is in ISO 8601 format.

    [Source: specs/data/health-check-response.schema.json#timestamp]
    """
    import app.api.v1.endpoints.agents as agents_module

    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService()

    response = await get_agent_health(mock_service, include_api_test=False)

    # Verify timestamp is valid datetime
    assert response.timestamp is not None
    assert response.timestamp.tzinfo is not None  # Has timezone info


# ═══════════════════════════════════════════════════════════════════════════════
# 防漂 guard：mock 期望表 vs 生产真相源
# [CARD-RED-HYGIENE] BATCH-2026-09-11-第十四批
# ═══════════════════════════════════════════════════════════════════════════════


_TRUTH_SOURCE_NAME = "expected_templates"

#: 会就地改动 list 的方法名。生产若在绑定之后调用它们中的任何一个，
#: 「赋值处的字面量」就不再等于「运行时的名单」，本 guard 的取值前提即失效。
_LIST_MUTATORS = frozenset({"append", "extend", "insert", "remove", "pop", "clear", "sort", "reverse"})


def _own_statements(node):
    """遍历 ``node`` 自己作用域内的语句，**不下钻**进嵌套函数 / lambda / 类。

    ``ast.walk`` 会把嵌套函数体里的同名赋值一起收进来。生产哪天在
    ``health_check`` 里定义一个内部辅助函数、里面恰好也有个叫
    ``expected_templates`` 的局部变量，``ast.walk`` 就会取到两处赋值 ——
    要么误判 FOUND-2，要么（若外层那处被改成别的形态）取到内层那个不相干的表。
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        yield child
        yield from _own_statements(child)


def _root_name(node):
    """把 ``a[0][1].x`` / ``*a`` 这类写目标剥到最外层的根 ``Name``；不以 Name 为根则返回 None。"""
    while isinstance(node, (ast.Subscript, ast.Attribute, ast.Starred)):
        node = node.value
    return node if isinstance(node, ast.Name) else None


def _enclosing_scope_parts(node):
    """嵌套 def / lambda / class 里那些在**外层**作用域求值的部分。

    函数体是独立作用域（不该下钻），但默认参数、装饰器、基类这些表达式是在
    **定义它的那个作用域**里求值的 —— ``def helper(unused=expected_templates.pop())``
    在定义 helper 的那一刻就改了名单，根本不用调用 helper（Codex r3 MEDIUM-1）。
    """
    args = getattr(node, "args", None)
    if args is not None:
        yield from args.defaults
        yield from (d for d in args.kw_defaults if d is not None)
    yield from getattr(node, "decorator_list", [])
    yield from getattr(node, "bases", [])
    for keyword in getattr(node, "keywords", []):
        yield keyword.value


def _own_nodes(node):
    """产出 ``node`` 自身作用域内的所有 AST 节点。

    跳过嵌套 def / lambda / class 的**函数体**（独立作用域，里面的同名变量与这里无关），
    但仍下钻它们在外层求值的部分（见 :func:`_enclosing_scope_parts`）。
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            for part in _enclosing_scope_parts(child):
                yield part
                yield from _own_nodes(part)
            continue
        yield child
        yield from _own_nodes(child)


def _collect_writes(nodes, name: str):
    """把该作用域里对 ``name`` 的写入点分成两类返回：``(绑定点, 其它写入)``。

    ⚠️ **判定方式是 AST 的 ``ctx``，不是枚举语句类型。**
    这是 Codex 连着三轮（r1 / r2 / r3）打出来的教训：先前按
    ``Assign`` / ``AugAssign`` / ``Delete`` / ``For`` … 一条条列，每轮都被找出没列到的形态
    （下标 ``AugAssign`` → 多 target → 解包绑定 → ``with as`` 下标 → 推导式 target →
    默认参数里的 ``.pop()``）。枚举永远追不完。

    Python 的 AST 已经把**每一个**写目标标成 ``ctx=Store`` 或 ``ctx=Del``，
    按 ctx 判定是构造上穷尽的：不管它出现在哪种语句里，只要是写就带这个标记。

    返回：
      * ``binds``  —— 直接绑定该名字的 ``Name`` 节点（``x = …`` / ``for x in`` /
        ``with … as x`` / ``x: T = …`` / ``x += …`` / 解包 / 多 target，全都算）
      * ``others`` —— 其余写入：删名字、写它的下标或属性、以及就地变更方法调用
    """
    binds, others = [], []
    for node in nodes:
        if isinstance(node, ast.Name) and node.id == name:
            if isinstance(node.ctx, ast.Store):
                binds.append(node)
            elif isinstance(node.ctx, ast.Del):
                others.append(("del 掉这个名字", node))
        elif isinstance(node, (ast.Subscript, ast.Attribute)):
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                root = _root_name(node)
                if root is not None and root.id == name:
                    others.append(("写它的下标 / 属性", node))
        elif isinstance(node, ast.Call):
            func = node.func
            # ⚠️ 只认**裸 Name** 作接收者：`x.append(...)` 改的是 x 本身；
            # 而 `x[:].reverse()` 改的是切片副本、`x[0].append()` 改的是元素，
            # 都不改 x 的名单内容 —— 剥到根会把这两种误判成写入（Codex r3 LOW-1）。
            if (
                isinstance(func, ast.Attribute)
                and func.attr in _LIST_MUTATORS
                and isinstance(func.value, ast.Name)
                and func.value.id == name
            ):
                others.append((f"调用就地变更方法 .{func.attr}()", node))
    return binds, others


def _production_expected_templates() -> list[str]:
    """从生产真相源里取出 ``expected_templates`` 字面量。

    真相源 = ``backend/app/services/agent_service.py`` 的
    ``AgentService.health_check``，其局部变量 ``expected_templates`` 决定
    ``/api/v1/agents/health`` 返回的 ``total`` / ``available``。

    为什么用 AST 读字面量而不是调 ``health_check()``：真正调用它要按
    ``settings.AGENT_PROMPT_PATH`` 去磁盘逐个探 prompt 文件，那是端到端面
    （本卡未覆盖，见验收单「本卡未证明什么」）。

    取值前提（三条，逐条显式断言、失效即红，不会静默降级）：
      1. ``inspect.getsource`` 取到的是单个函数定义；
      2. 该函数**自己的**作用域里对这个名字**恰好只有一处绑定**，且它来自
         ``Assign`` / ``AnnAssign`` 且右值是字面量 list；
      3. 该作用域里**没有任何其它写入**（删名字 / 写下标或属性 / 就地变更方法）。

    第 2、3 条统一用 :func:`_collect_writes` 按 AST 的 ``ctx`` 判定，不枚举语句类型。

    ⚠️ **覆盖声明**（三轮 Codex 之后的最终口径，不再说「必然一致」）：
    本 guard 钉住的是「mock 的名单 == 生产在**绑定处声明**的字面量」。它**不读运行时值**。
    上面第 3 条把「本作用域内可见的、会让声明 ≠ 运行时」的写法挡在门外并报红，
    但这**不等于**「门通过时两者必然一致」—— 下面这些它看不见：
      * **别名写入**：``alias = expected_templates`` 之后改 ``alias``；
      * **传出去改**：把它传进别的函数 / 方法，由被调方修改；
      * **动态手段**：``locals()`` / ``globals()`` / ``setattr`` / ``exec`` 等。
    这些都需要别名分析或运行期观测，不在本 guard 的能力范围内。
    真要钉运行时值，得改成在运行时取真实名单（那是另一张卡的面）。
    """
    import inspect
    import textwrap

    from app.services.agent_service import AgentService

    tree = ast.parse(textwrap.dedent(inspect.getsource(AgentService.health_check)))
    assert len(tree.body) == 1 and isinstance(tree.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)), (
        "inspect.getsource(AgentService.health_check) 取到的不是单个函数定义，本 guard 的取值方式已失效"
    )

    nodes = list(_own_nodes(tree.body[0]))
    binds, others = _collect_writes(nodes, _TRUTH_SOURCE_NAME)

    assert len(binds) == 1, (
        f"在 AgentService.health_check 自己的作用域里找到 {len(binds)} 处对 "
        f"{_TRUTH_SOURCE_NAME} 的绑定，期望恰好 1 处；生产形态变了，本 guard 需同步改"
    )
    if others:
        kind, node = others[0]
        raise AssertionError(
            f"生产在这个作用域里对 {_TRUTH_SOURCE_NAME} 还有别的写入：{kind}"
            f"（{type(node).__name__}，源码第 {getattr(node, 'lineno', '?')} 行，"
            "行号相对 health_check 起始；共 "
            f"{len(others)} 处）。本 guard 读的是绑定处的字面量，这类写入会让它与运行时"
            "名单分叉、却仍然比对通过 —— 门会在名单真漂了的时候保持绿。"
            "请改为在运行时取真实名单，或连同本 guard 一起改，不要放宽断言"
        )

    the_bind = binds[0]
    literal = None
    for node in nodes:
        if isinstance(node, ast.Assign) and any(t is the_bind for t in node.targets):
            literal = node.value
        elif isinstance(node, ast.AnnAssign) and node.target is the_bind:
            literal = node.value
    assert literal is not None, (
        f"{_TRUTH_SOURCE_NAME} 的那处绑定不是普通赋值（可能是 for / with as / 解包），取不到字面量；本 guard 需同步改"
    )
    assert isinstance(literal, ast.List), (
        f"生产的 {_TRUTH_SOURCE_NAME} 不再是字面量列表，本 guard 的取值方式已失效——请连同本函数一起改，不要放宽断言"
    )
    return [ast.literal_eval(elt) for elt in literal.elts]


def test_mock_expected_templates_match_production_truth_source():
    """MockAgentService 的期望表必须与生产真相源逐元素同名同序。

    为什么需要这条：``MockAgentService.health_check`` 不读生产表，它自带一份
    手抄名单。生产在 ``agent_service.py`` 加了第 13 项 ``hint-generation`` 之后，
    本文件的 AC1 断言仍写 ``total == 12`` 且照常通过——测试绿着，而它声称在测
    的那个数字已经和生产对不上了。只把 12 改成 13 治不了这个：下一次生产加第
    14 项时同样不会有人红。这条 guard 把 mock 钉在生产**绑定处声明的**字面量上。

    ⚠️ 覆盖声明（按 Codex r1 LOW-1 / r2 LOW-2 收窄，原先那句「增/删/改名/换序
    任一发生都会在这里红」过强，已撤回）：
      * 生产**在绑定处**增 / 删 / 改名 / 换序 → 这里红（逐元素比较，等长改名也抓得到）；
      * 生产改成非字面量形态（常量 / 文件 / 推导）、出现多处绑定、变量改名 →
        ``_production_expected_templates()`` 的断言红；
      * 生产在绑定**之后**写这个名字（``+=`` / 下标赋值 / ``del`` / 八个 list 变更方法）→
        ``_assert_not_mutated_after_binding()`` 红；
      * ⛔ **看不见**的：通过别名写入、传进函数由被调方改、``locals()``/``setattr``
        之类的动态改动 —— 那需要别名分析，不在本 guard 能力范围内。

    [CARD-RED-HYGIENE] 真相源锚点 = AgentService.health_check 的 expected_templates
    """
    production = _production_expected_templates()

    # 钉住本卡落定的快照：生产与 mock 当前都是 13 项
    assert len(MockAgentService.EXPECTED_TEMPLATES) == 13

    # 承重：mock 必须跟随生产真相源（含顺序）
    assert MockAgentService.EXPECTED_TEMPLATES == production, (
        "mock 的 EXPECTED_TEMPLATES 与 AgentService.health_check 的 expected_templates "
        "不一致；生产改了名单就要同步改这里，并复核本文件里所有 total/available 断言"
    )
