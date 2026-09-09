# ✅ Verified from Context7:/schemathesis/schemathesis (topic: pytest integration FastAPI)
"""
OpenAPI Contract Tests using Schemathesis.

This module contains property-based tests that validate the API implementation
against its OpenAPI specification. Schemathesis generates test cases based on
the schema and validates responses match the expected format.

[Source: docs/stories/15.6.story.md#Testing - AC: Contract Testing]
[Source: ADR-008 - Testing Framework pytest]
"""

import os

import pytest

schemathesis = pytest.importorskip("schemathesis", reason="schemathesis not installed")
from app.main import app
from hypothesis import Phase, settings

# ═══════════════════════════════════════════════════════════════════════════════
# Schema Loading
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Context7:/schemathesis/schemathesis (topic: from_asgi)
# Pattern: Load OpenAPI schema from ASGI app for testing
#
# CARD-HYGIENE-openapi [BATCH-2026-09-07-第十三批] —— `.include(method_regex=...)` 只保留
# GET/HEAD, 把全部写方法(POST/PUT/PATCH/DELETE)排除出 schemathesis 的生成面。
#
# 为什么: 写端点在 TestClient 下对**真文件系统 / LanceDB / 进程内 state** 有副作用,
# 而这里没有任何一个跑在夹具隔离下 ——
#   - `POST /api/v1/system/setup-wizard` (`app/api/v1/system.py:456`) 调
#     `VaultInitService.initialize_vault()` (`app/services/vault_init_service.py:18-23,:93-104`),
#     按请求体 `vault_path` 建整套 vault 骨架(raw/ wiki/ outputs/ CLAUDE.md/ .gitkeep/ .gitignore)。
#     已有冻结污染现场: worktree `card-z4-redbase` @ c8611a89 的 `backend/` 下四项俱在。
#     Y6-A 的 `_must_be_absolute` (`system.py:430-455`) 只拒相对路径/空串, 且 field_validator
#     不进 JSON Schema, 生成面依旧覆盖任意**绝对**路径 —— 写面是挪走了, 不是消失。
#   - `tests/conftest.py` 把 `CANVAS_BASE_PATH` 设成相对的 `"./test_canvas"`, canvas /
#     index / sync 端点因此写进 `backend/test_canvas/`。
#
# 代价(如实): 契约覆盖面从 206 个 operation 收窄到 **92** 条 —— 93 个 GET(HEAD 面为 0)
# 再减去下方追加排除的 1 条只读端点。被排除的共 **114** 条(POST 96 / DELETE 9 / PUT 6 /
# PATCH 2 / GET 1), 清单见 `_bmad-output/审查/evidence-hyg-openapi/excluded-operations.txt`
# (`comm -23 collect-before.txt collect-after.txt` 实测)。合约测试本就
# **不在 CI 白名单**(`.github/workflows/test.yml`), 只在本机以 importorskip 形式跑,
# 故此次收窄不减少 CI 覆盖面。写端点的契约校验需另立隔离夹具后恢复。
#
# API 形态实测(schemathesis 4.14.3): `BaseSchema.include` / `.exclude` 见
# `schemathesis/schemas.py:132` / `:182`; `filters.py:66` 对 method 正则用 re.IGNORECASE,
# `:84-87` 把 method 取值统一大写 ⇒ `^(GET|HEAD)$` 成立。
# 追加排除的**只读方法**(逐条列理由, 不做无清单的放宽):
#   - `GET /api/v1/health/lancedb` → `check_lancedb_health`
#     (`app/api/v1/endpoints/health.py:1139`) 里
#     `lancedb_path = getattr(settings, "lancedb_path", "./data/lancedb")` 是**相对路径**,
#     紧接着 `db_path.mkdir(parents=True, exist_ok=True)` —— 从 `backend/` 起跑的合约测试
#     会因此在代码目录里造出 `backend/data/lancedb/`。这是 93 条 GET 里唯一一条直接写原语
#     命中(扫描面 = `backend/app` 全树 93 个 `<任意名>.get` handler, 与收集到的 GET 数逐一对齐;
#     存档 `evidence-hyg-openapi/get-handler-write-primitive-scan-*.txt`)。
schema = (
    schemathesis.openapi.from_asgi("/api/v1/openapi.json", app)
    .include(method_regex=r"^(GET|HEAD)$")
    .exclude(path_regex=r"^/api/v1/health/lancedb$")
)


# ═══════════════════════════════════════════════════════════════════════════════
# Contract Tests
# ═══════════════════════════════════════════════════════════════════════════════


# ✅ Verified from Context7:/schemathesis/schemathesis (topic: call_and_validate)
# Pattern: Use call_and_validate() with specific checks for placeholder implementation
@schema.parametrize()
@settings(
    max_examples=10,  # Reduced for faster CI runs
    phases=[Phase.explicit, Phase.generate],  # Skip shrinking for speed
    deadline=10000,  # 10 second timeout per test
)
def test_api_contract(case):
    """
    Property-based contract test for all API endpoints.

    Schemathesis generates test cases based on the OpenAPI schema
    and validates that responses match the expected format.

    Note: Current implementation uses placeholder routers that don't fully validate input.
    We only check response schema conformance, not negative data rejection.

    [Source: docs/stories/15.6.story.md#Testing - AC: 9]
    """
    # Only run positive validation checks (response schema conformance)
    # Skip negative_data_rejection check since routers are placeholders
    #
    # CARD-TOOL-dredd-decide [BATCH-2026-09-05-第十一批] —— 这是**防御性加固**,
    # 不是 bug 修复。措辞经 Codex round-1 打回两次后按实测重写:
    #
    # 原写法 `schemathesis.checks.status_code_conformance` 是**模块属性**访问。
    # 它在 3.25/3.30/3.39 上直接可用; 在 4.14.3 上, `schemathesis.checks` 有动态
    # `__getattr__`, 且 pytest 插件在**收集期**(pytest/plugin.py:146 的 _gen_items)
    # 就调了 load_all_checks(), 所以属性同样可用。
    # 实测(把改前版本原样跑真 pytest, 一个 operation): 拒因是
    # `hypothesis.errors.DeadlineExceeded: Test took 20857.69ms`, **不是 AttributeError**
    # —— 即原写法在当前环境下**并没有坏**。
    #
    # 那为什么还要改: 原写法依赖"插件恰好已经加载过检查"这个**隐式前提**。
    # 一旦有人在别的入口(非 pytest / 手搓 Case / CLI 以外的路径)复用这段逻辑,
    # 属性就取不到。改成显式 `load_all_checks()` + 注册表取名后, 不再依赖该前提。
    # **不削弱任何检查**: Codex 独立验证过 get_by_names 返回的四个函数与加载后的
    # 四个模块属性**逐一是同一对象**; 缺名会抛 KeyError 而不是悄悄少取。
    # 代价: 这套写法是 **4.x 专用**(3.39.0 没有 load_all_checks/CHECKS),
    # 所以依赖下限必须同批抬到 >=4.0。
    _CHECK_NAMES = (
        "status_code_conformance",
        "content_type_conformance",
        "response_headers_conformance",
        "response_schema_conformance",
    )
    schemathesis.checks.load_all_checks()
    case.call_and_validate(checks=tuple(schemathesis.checks.CHECKS.get_by_names(_CHECK_NAMES)))


# ═══════════════════════════════════════════════════════════════════════════════
# Stateful Testing (Optional - for complex workflows)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCanvasWorkflow:
    """
    Stateful tests for canvas workflow.

    Tests that canvas operations work together correctly.
    Note: Current implementation uses placeholder data - tests verify endpoint accessibility.
    """

    @pytest.fixture
    def test_canvas_name(self):
        """Generate unique canvas name for testing."""
        import uuid

        return f"test-canvas-{uuid.uuid4().hex[:8]}"

    @pytest.mark.skipif(
        not os.environ.get("RUN_E2E_TESTS"),
        reason="E2E tests require RUN_E2E_TESTS=1 and running backend",
    )
    def test_canvas_crud_workflow(self, test_canvas_name):
        """
        Test complete canvas CRUD workflow.

        Note: Current placeholder implementation returns 200 for all operations.
        Real implementation will return 201 for creates.

        [Source: docs/stories/15.2.story.md#Testing]
        """
        from fastapi.testclient import TestClient

        test_client = TestClient(app)

        # Read canvas (placeholder returns data)
        response = test_client.get(f"/api/v1/canvas/{test_canvas_name}")
        assert response.status_code == 200
        assert "name" in response.json()

        # Create node - placeholder returns 200 with mock data
        # Note: Real implementation should return 201
        response = test_client.post(
            f"/api/v1/canvas/{test_canvas_name}/nodes",
            json={"text": "Test Node", "x": 0, "y": 0},
        )
        # Accept both 200 (placeholder) and 201 (real implementation)
        assert response.status_code in [200, 201]
        assert "id" in response.json()
