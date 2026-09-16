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
# 代价(如实): 契约覆盖面从 206 个 operation 收窄到 **89** 条 —— 93 个 GET(HEAD 面为 0)
# 再减去下方追加排除的 4 条会写盘的只读端点。被排除的共 **117** 条(POST 96 / DELETE 9 /
# PUT 6 / PATCH 2 / GET 4), 清单见
# `_bmad-output/审查/evidence-hyg-openapi/excluded-operations.txt`
# (`comm -23 collect-before.txt collect-after.txt` 实测)。合约测试本就
# **不在 CI 白名单**(`.github/workflows/test.yml`), 只在本机以 importorskip 形式跑,
# 故此次收窄不减少 CI 覆盖面。写端点的契约校验需另立隔离夹具后恢复。
#
# API 形态实测(schemathesis 4.14.3): `BaseSchema.include` / `.exclude` 见
# `schemathesis/schemas.py:132` / `:182`; `filters.py:66` 对 method 正则用 re.IGNORECASE,
# `:84-87` 把 method 取值统一大写 ⇒ `^(GET|HEAD)$` 成立。
# 追加排除的**只读方法**(逐条列理由, 不做无清单的放宽)。
#
# (1) 直接写原语命中 —— AST 扫描 `backend/app` 全树 93 个 `<任意名>.get` handler
#     (与收集到的 GET 数逐一对齐, 存档 `evidence-hyg-openapi/get-handler-write-primitive-scan-*.txt`),
#     正则 `mkdir|write_text|write_bytes|os.replace|save_state|add_documents|drop_table|
#     append_event|subprocess` 在 handler 函数体内命中 1 条:
#   - `GET /api/v1/health/lancedb` → `check_lancedb_health` (`endpoints/health.py:1139`):
#     `lancedb_path = getattr(settings, "lancedb_path", "./data/lancedb")` 是**相对路径**,
#     紧接着 `db_path.mkdir(parents=True, exist_ok=True)` ⇒ 从 `backend/` 起跑会造出
#     `backend/data/lancedb/`。
#
# (2) **间接**写(handler 自身无写原语, 调用的 service 写盘) —— 上面那次 AST 扫描只看
#     handler 函数体一层文本, 抓不到这类; 由 Codex round-2 独立审查补出, 作者已逐条核过源码:
#   - `GET /api/v1/review/fsrs-state/{concept_id}` (`endpoints/review.py:1430`)
#     → `review_service.get_fsrs_state()` → 该 concept 无卡且不受 frontmatter 管辖时
#     auto-create 默认卡 → `_save_card_states()` (`services/review_service.py:2507`)
#     → `:600 mkdir` + `:604 write_text` + `:605 replace` 写
#     `_CARD_STATES_FILE`(`:116-118` = `backend/data/fsrs_card_states.json`)。
#     **请求期写盘**, 不是启动期一次性写 —— 全跑实测该文件 mtime 落在跑中(18:26)。
#   - `GET /api/v1/health/storage` (`endpoints/health.py:1671`) → `_check_json_health()`
#     (`:1444` 默认 `./data` → `:1448 mkdir` → `:1452-1453` 对 `.health_check` touch/unlink)。
#     探针会被删掉, 所以跑完的 `find -newer` **看不见**它 —— 更该在生成面就排除。
#   - `GET /api/v1/multimodal/health` (`endpoints/multimodal.py:251`)
#     → `multimodal_service.get_health_status()` (`services/multimodal_service.py:1034-1036`)
#     `.health_check` write_text/unlink; 该服务构造器还会创建媒体目录。
schema = (
    schemathesis.openapi.from_asgi("/api/v1/openapi.json", app)
    .include(method_regex=r"^(GET|HEAD)$")
    .exclude(path_regex=r"^/api/v1/health/lancedb$")
    .exclude(path_regex=r"^/api/v1/review/fsrs-state/\{concept_id\}$")
    .exclude(path_regex=r"^/api/v1/health/storage$")
    .exclude(path_regex=r"^/api/v1/multimodal/health$")
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


# ═══════════════════════════════════════════════════════════════════════════════
# Security scheme 悬空引用门(非 schemathesis) — CARD-SEC-DANGLING
# ═══════════════════════════════════════════════════════════════════════════════
#
# [BATCH-2026-09-11-第十四批 / CARD-SEC-DANGLING]
#
# 本门证明什么: 真实 `app.openapi()` 里**每一处** `security` 引用(31 处 per-operation +
#   1 处文档根全局)的方案名都能在 `components.securitySchemes` 找到定义 —— 即契约零悬空。
#   覆盖面的完整性依据见 `_iter_security_refs` 的 docstring(本仓快照普查实测)。
# 本门不证明什么:
#   - 不验证运行时鉴权行为(`require_internal_api_key` 的 fail-closed matrix / 403 / 503
#     归本批 T10-E), 本门是纯文档/契约层断言;
#   - 不验证 committed `backend/openapi.json` 是否与 live 同步(那是同目录
#     `test_openapi_snapshot_drift.py::test_committed_snapshot_has_no_drift`);
#   - 不验证方案定义本身的字段(type / in / name)是否写对。
#
# 为什么不复用同文件的 schemathesis 门: `test_api_contract` 每个 operation 都发真实
#   HTTP 请求, 在 W4 端口门下每次 16-19s > `deadline=10000` ⇒ 恒 `DeadlineExceeded`,
#   对「方案名是否被声明」这条**纯静态**性质是瞎的。本门只做进程内 schema 断言,
#   不发任何请求、不经 `@schema.parametrize()`(故可按 nodeid 直接点选)。
#
# 取 schema 的路径与快照漂移门**同源**: 复用
#   `scripts/spec-tools/check-openapi-drift.py::load_live_schema()` —— 它对
#   `import app.main` 与 `app.openapi()` 全程 socket-connect 禁闭, 不起 lifespan、
#   不连 7691/7687。同源保证本门与漂移门看见的是同一份 schema。


def _load_drift_module_for_security():
    """加载文件名带连字符的 drift 工具(不能走普通 import; 与漂移门同法)。"""
    import importlib.util
    import sys
    from pathlib import Path

    backend_dir = Path(__file__).resolve().parents[2]
    tool = backend_dir.parent / "scripts" / "spec-tools" / "check-openapi-drift.py"
    spec = importlib.util.spec_from_file_location("_check_openapi_drift_secdangling", tool)
    if spec is None or spec.loader is None:  # pragma: no cover — 路径错时立即失败
        raise RuntimeError(f"无法加载 {tool}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # 不往 scripts/spec-tools/ 落 __pycache__
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _iter_security_refs(schema):
    """产出 (位置, 方案名) —— schema 里**每一处** `security` 需求引用的每个方案名。

    覆盖面 = OpenAPI 3.1 里 `security` 的两个合法位置:
      - 每个 operation 的 `paths[<path>][<method>].security` (位置写作 "GET /api/v1/x");
      - 文档根的全局 `security` (位置写作 "<root>")。
    2026-09-16 于本仓快照普查实测: 这两处合计 32 处(31 per-op + 1 root)已是全部 ——
    该 schema 无 `webhooks`、无 `components.callbacks`/`pathItems`; WebSocket 路由
    (`app/main.py` 的 `@app.websocket`)不产出 OpenAPI operation, 其鉴权走
    `app/security.py::verify_websocket_internal_key` 手工校验, 根本不是 OpenAPI 安全方案,
    故不在本门(也不在任何 OpenAPI 契约门)的覆盖面内。
    """
    for requirement in schema.get("security") or []:
        for scheme_name in requirement:
            yield "<root>", scheme_name
    for path, methods in (schema.get("paths") or {}).items():
        for method, operation in methods.items():
            if not isinstance(operation, dict):
                continue
            for requirement in operation.get("security") or []:
                for scheme_name in requirement:
                    yield f"{method.upper()} {path}", scheme_name


def test_security_schemes_cover_all_security_refs():
    """每一处 `security` 引用的方案名必须 ∈ `components.securitySchemes`(悬空数必须等于 0)。

    两条防 vacuous-pass 的前置断言不可删: 若 `securitySchemes` 为空、或整份 schema 一条
    `security` 需求都没有, 悬空集自然是空集 —— 那时本门「绿」不代表契约自洽。
    """
    drift = _load_drift_module_for_security()
    schema = drift.load_live_schema()

    declared = set((schema.get("components") or {}).get("securitySchemes") or {})
    assert declared, (
        "components.securitySchemes 为空 —— 本门会 vacuously pass。"
        "先查 `app/main.py:_custom_openapi` 是否还在写 securitySchemes。"
    )

    refs = list(_iter_security_refs(schema))
    assert refs, (
        "整份 schema 没有任何 `security` 需求 —— 本门会 vacuously pass。"
        "先查安全依赖(`Depends(require_internal_api_key)`)是否还挂在路由上。"
    )
    per_op_refs = [ref for ref in refs if ref[0] != "<root>"]
    assert per_op_refs, (
        "整份 schema 没有任何 per-operation `security`(只剩全局 security) —— 本门对 per-op 面会"
        " vacuously pass。先查安全依赖是否还挂在路由上。"
    )

    dangling = [ref for ref in refs if ref[1] not in declared]
    system_dangling = [ref for ref in dangling if "/system/" in ref[0]]

    assert not dangling, (
        f"OpenAPI 契约里有 {len(dangling)} 处 security 悬空引用"
        f"(其中 /system/* {len(system_dangling)} 处) —— 方案名不在 "
        f"components.securitySchemes={sorted(declared)} 里, 第三方工具无法推导鉴权。\n"
        "常见根因: `fastapi.security.APIKeyHeader(...)` 未传 `scheme_name=`, FastAPI 退回按**类名**"
        "命名(`fastapi/security/api_key.py` 的 `self.scheme_name = scheme_name or self.__class__.__name__`), "
        "而 `app/main.py:_custom_openapi` 又整体覆盖了 securitySchemes。\n"
        f"引用总数={len(refs)}(其中 per-op {len(per_op_refs)}); 悬空前 10 条 (位置 -> 方案名):\n"
        + "\n".join(f"  {loc} -> {name}" for loc, name in dangling[:10])
        + "\n其中 /system/* 前 5 条:\n"
        + "\n".join(f"  {loc} -> {name}" for loc, name in system_dangling[:5])
    )
