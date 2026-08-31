# CARD-G4-4 (BATCH-2026-09-01-第八批) — /rag/query 显式 VaultScope · API 面契约
"""POST /api/v1/rag/query 的 vault_id 必填 + 409 + 作用域注入契约。

锁四件事:

1. **422** — vault_id 必填 (pydantic 把守); 请求 schema 的 required 集 =
   {query, vault_id}, 除新增 vault_id 外不新增任何必填 (旧调用方只破
   「缺 vault_id」这一件事)。
2. **409** — 请求 vault 与进程 active vault 不一致 → 409 fail-closed,
   且 rag_service.query **一次都不被调用** (拒绝发生在服务之前)。
3. **注入与契约** — 显式 vault_id + subject_id → ContextVar 注入
   group_id 形态 (vault:<vid>:<subject>), 这是「删缺省不注入旁路」的
   行为证明: 旧代码注入裸 subject_id ("math"), 新代码注入 D16 group;
   旧必填键与响应 schema 全保留 (沿 test_rag_four_state_api.py 的
   Legacy 副本手法)。
4. **agents scope_source 三值** — agents 端点 (recommend_action, 依赖链
   最短) 的 X-Vault-Scope-Source 响应头在 explicit / legacy / derived
   三种解析来源下各出一例 (完成条件 c)。

形态纪律: 沿 test_rag_four_state_api.py —— 局部 ``FastAPI()`` +
``dependency_overrides``, TestClient **不起 with** (不触发生命周期,
不连 7691); agents 端点用同样手法 override 依赖。全文件不做
with 形式的 TestClient 生命周期构造 (判据 5 的字面 grep 门,
docstring 刻意不逐字写出该模式)。

本文件不比什么: 不证明真实检索隔离 (单元文件双 vault 真库门职责);
不证明 rag_service 全图执行 (mock 服务层, 防 LLM 外发)。
"""

from typing import Any, Dict, List, Literal, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.api.v1.endpoints.agents import agents_router
from app.api.v1.endpoints.rag import RAGQueryRequest, rag_router
from app.services.rag_service import get_rag_service


# ═══════════════════════════════════════════════════════════════════════════
# 夹具
# ═══════════════════════════════════════════════════════════════════════════


def _state() -> Dict[str, Any]:
    """rag_service.query() 返回的最小 state 形态 (四态字段无关本卡, 随手给)。"""
    return {
        "reranked_results": [
            {"doc_id": "node-1", "content": "逆否命题…", "score": 0.9, "metadata": {}}
        ],
        "multimodal_results": [],
        "quality_grade": "high",
        "graphiti_latency_ms": 12.0,
        "lancedb_latency_ms": 8.0,
        "fusion_latency_ms": 1.0,
        "query_rewritten": False,
        "rewrite_count": 0,
        "fusion_strategy": "rrf",
        "reranking_strategy": "hybrid_auto",
        "retrieval_status": "ok",
        "retrieval_status_reason": None,
    }


@pytest.fixture
def mock_rag_service() -> MagicMock:
    service = MagicMock()
    service.query = AsyncMock(return_value=_state())
    return service


@pytest.fixture
def client(mock_rag_service: MagicMock) -> TestClient:
    app = FastAPI()
    app.include_router(rag_router, prefix="/api/v1/rag")

    async def _override_service():
        return mock_rag_service

    app.dependency_overrides[get_rag_service] = _override_service
    return TestClient(app)


@pytest.fixture
def proc_vault(monkeypatch) -> str:
    """把进程级 active vault 钉到可控值。

    vault_scope 延迟 import app.config — 必须 patch 源模块命名空间
    (vault_scope.py 模块 docstring Patch-target 注记)。别名集合的
    ACTIVE_VAULT / CANVAS_BASE_PATH 两路在本环境下都收敛到同一稳定 ID
    (canvas_vault), patch get_current_vault_id 后别名集 = {canvas_vault,
    v_active}; 用例里 active 用 v_active、冲突用一个绝不在别名集的值。
    """
    import app.config as app_config_mod

    monkeypatch.setattr(
        app_config_mod, "get_current_vault_id", lambda: "v_active", raising=True
    )
    return "v_active"


# ═══════════════════════════════════════════════════════════════════════════
# 1. vault_id 必填 → 422
# ═══════════════════════════════════════════════════════════════════════════


class TestVaultIdRequired:
    def test_missing_vault_id_rejected_with_422(self, client, mock_rag_service):
        """旧调用方形态 (不带 vault_id) — 422, 且服务一次都不被调。"""
        response = client.post("/api/v1/rag/query", json={"query": "什么是逆否命题？"})

        assert response.status_code == 422
        assert "vault_id" in response.text
        assert mock_rag_service.query.await_count == 0, "422 不应触达服务层"

    def test_blank_vault_id_rejected_with_422(self, client):
        response = client.post(
            "/api/v1/rag/query", json={"query": "q", "vault_id": ""}
        )
        assert response.status_code == 422

    @pytest.mark.parametrize("blank", ["   ", "\t\n ", "　"])
    def test_whitespace_only_vault_id_rejected_with_422(
        self, client, mock_rag_service, blank
    ):
        """Codex round-1 HIGH-2: min_length=1 拦不住纯空白; resolve_vault_scope
        把空白当「缺失」走双缺失推导 → 空白请求曾以 active 作用域 200 通过。
        模型层 validator fail-closed 后, 任何空白形态必须 422 且服务不被触达。"""
        response = client.post(
            "/api/v1/rag/query", json={"query": "q", "vault_id": blank}
        )
        assert response.status_code == 422, (
            f"空白 vault_id {blank!r} 未被 422 — 契约被绕过"
        )
        assert mock_rag_service.query.await_count == 0

    def test_request_schema_required_set_is_query_plus_vault_id_only(self):
        """required = {query, vault_id} — 旧必填键保留, 新必填只加 vault_id。"""
        required = set(RAGQueryRequest.model_json_schema().get("required", []))

        assert required == {"query", "vault_id"}, (
            f"必填集漂移: {required} — 加性契约破坏"
        )

    def test_legacy_request_keys_all_accepted(self, client, mock_rag_service, proc_vault):
        """旧请求的全部可选键照常被接受并透传 (带 vault_id 后 200)。"""
        response = client.post(
            "/api/v1/rag/query",
            json={
                "query": "什么是逆否命题？",
                "vault_id": proc_vault,
                "canvas_file": "离散数学.canvas",
                "subject_id": "math",
                "cross_subject": True,
                "is_review_canvas": True,
                "fusion_strategy": "weighted",
                "reranking_strategy": "local",
            },
        )

        assert response.status_code == 200
        kwargs = mock_rag_service.query.await_args.kwargs
        for key, expected in (
            ("query", "什么是逆否命题？"),
            ("canvas_file", "离散数学.canvas"),
            ("subject_id", "math"),
            ("cross_subject", True),
            ("is_review_canvas", True),
            ("fusion_strategy", "weighted"),
            ("reranking_strategy", "local"),
        ):
            assert kwargs.get(key) == expected, f"旧键 {key} 透传被破坏"


# ═══════════════════════════════════════════════════════════════════════════
# 2. 请求 vault ≠ active → 409 (不静默改写)
# ═══════════════════════════════════════════════════════════════════════════


class TestVaultConflict:
    def test_mismatched_vault_rejected_with_409(
        self, client, mock_rag_service, proc_vault
    ):
        response = client.post(
            "/api/v1/rag/query",
            json={"query": "q", "vault_id": "definitely_not_active_vault"},
        )

        assert response.status_code == 409
        assert mock_rag_service.query.await_count == 0, (
            "409 必须发生在服务调用之前 — 不允许静默改写成 active vault 继续"
        )
        assert "definitely_not_active_vault" in response.text

    def test_active_vault_by_stable_id_accepted(self, client, mock_rag_service, proc_vault):
        response = client.post(
            "/api/v1/rag/query", json={"query": "q", "vault_id": proc_vault}
        )
        assert response.status_code == 200
        assert mock_rag_service.query.await_count == 1


# ═══════════════════════════════════════════════════════════════════════════
# 3. ContextVar 注入 + 删旁路的行为证明 + 响应契约
# ═══════════════════════════════════════════════════════════════════════════


class TestScopeInjectionAndContract:
    @staticmethod
    def _capture_injected_scope(mock_rag_service) -> List[str]:
        """在服务调用点读取 ContextVar。

        ⚠️ 不能在请求返回后读: TestClient 把 handler 跑在 worker 线程的
        任务上下文里, handler 内 set 的 ContextVar 对测试主线程不可见。
        服务层调用发生在同一任务上下文内, 在 side_effect 里读 = 生产
        下游服务真实看到的值。"""
        from app.core.subject_config import get_current_subject_id

        seen: List[str] = []

        async def _spy(**kwargs):
            seen.append(get_current_subject_id())
            return _state()

        mock_rag_service.query = AsyncMock(side_effect=_spy)
        return seen

    def test_subject_id_injects_group_form_not_bare_subject(
        self, client, mock_rag_service, proc_vault
    ):
        """「删缺省不注入旁路」的行为证明 — 旧代码注入裸 subject_id
        ("math"), 新代码注入 D16 group (vault:<vid>:math)。"""
        seen = self._capture_injected_scope(mock_rag_service)

        response = client.post(
            "/api/v1/rag/query",
            json={"query": "q", "vault_id": proc_vault, "subject_id": "math"},
        )

        assert response.status_code == 200
        assert seen == [f"vault:{proc_vault}:math"], (
            f"服务看到的 ContextVar = {seen!r} — 不是 group 形态, "
            "「缺省不注入/裸注入」旁路可能回来了"
        )

    def test_without_subject_injects_vault_base_group(
        self, client, mock_rag_service, proc_vault
    ):
        """无 subject 也不再是「不注入」— 注入 vault 基组 (LanceDB 表
        命名空间由此而来, 缺省不注入 = 检索落表解析的 legacy 分支)。"""
        seen = self._capture_injected_scope(mock_rag_service)

        response = client.post(
            "/api/v1/rag/query", json={"query": "q", "vault_id": proc_vault}
        )

        assert response.status_code == 200
        assert seen == [f"vault:{proc_vault}"]


class LegacySearchResultItem(BaseModel):
    doc_id: str
    content: str
    score: float
    metadata: dict = Field(default_factory=dict)


class LegacyLatencyInfo(BaseModel):
    graphiti: Optional[float] = None
    lancedb: Optional[float] = None
    multimodal: Optional[float] = None
    fusion: Optional[float] = None
    reranking: Optional[float] = None


class LegacyRAGQueryMetadata(BaseModel):
    query_rewritten: bool = False
    rewrite_count: int = 0
    fusion_strategy: Optional[str] = None
    reranking_strategy: Optional[str] = None


class LegacyRAGQueryResponse(BaseModel):
    """本卡改动前 RAGQueryResponse 的字段契约语义等价副本
    (沿 test_rag_four_state_api.py 手法 — 副本不得比原模型宽松)。"""

    results: List[LegacySearchResultItem] = Field(default_factory=list)
    multimodal_results: list = Field(default_factory=list)
    quality_grade: str = "low"
    result_count: int = 0
    latency_ms: LegacyLatencyInfo = Field(default_factory=LegacyLatencyInfo)
    total_latency_ms: float = 0.0
    metadata: LegacyRAGQueryMetadata = Field(default_factory=LegacyRAGQueryMetadata)


class TestResponseContractAdditive:
    def test_legacy_response_schema_parses_new_response(
        self, client, mock_rag_service, proc_vault
    ):
        response = client.post(
            "/api/v1/rag/query", json={"query": "q", "vault_id": proc_vault}
        )
        assert response.status_code == 200

        parsed = LegacyRAGQueryResponse.model_validate(response.json())
        assert parsed.quality_grade == "high"
        assert parsed.result_count == 1

    def test_all_legacy_response_keys_present(
        self, client, mock_rag_service, proc_vault
    ):
        body = client.post(
            "/api/v1/rag/query", json={"query": "q", "vault_id": proc_vault}
        ).json()

        for key in (
            "results",
            "multimodal_results",
            "quality_grade",
            "result_count",
            "latency_ms",
            "total_latency_ms",
            "metadata",
        ):
            assert key in body, f"旧响应键 {key} 丢失 — 违反加性"

    def test_response_model_has_no_new_required_fields(self):
        from app.api.v1.endpoints.rag import RAGQueryResponse

        required = set(RAGQueryResponse.model_json_schema().get("required", []))
        assert required == set(), (
            f"RAGQueryResponse 冒出必填字段 {required} — 响应面不是加性"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 4. agents 端点 X-Vault-Scope-Source 三值
# ═══════════════════════════════════════════════════════════════════════════


def _agents_client(monkeypatch) -> TestClient:
    """recommend_action 依赖链最短 (memory_service 一项), 用于 scope_source 三值。"""
    from app.api.v1.endpoints.memory import MemoryServiceDep

    app = FastAPI()
    app.include_router(agents_router, prefix="/api/v1/agents")

    memory_service = MagicMock()
    memory_service.get_learning_history = AsyncMock(return_value={"items": []})

    async def _override_memory():
        return memory_service

    # MemoryServiceDep 是 Annotated[MemoryService, Depends(get_memory_service)]
    from app.services.memory_service import get_memory_service

    app.dependency_overrides[get_memory_service] = _override_memory
    return TestClient(app)


class TestAgentScopeSourceHeader:
    """完成条件 (c): agents 端点 scope_source 三值各一例。

    VaultScope.source 实际值域 = request-vault / legacy-group / active-vault
    (vault_scope.py:84-86); 卡文笔名 explicit/legacy_group_id/derived_active
    是语义描述不是字面值, 验收单已声明映射。
    """

    @pytest.fixture(autouse=True)
    def _pin_active_vault(self, monkeypatch):
        import app.config as app_config_mod

        monkeypatch.setattr(
            app_config_mod, "get_current_vault_id", lambda: "v_active", raising=True
        )

    @staticmethod
    def _post(monkeypatch, *, vault_id=None, group_id=None, node_id="n1"):
        """node_id 必须逐用例唯一 — agents 的 dedup 缓存是模块级进程态,
        同 (canvas, node, type) 二连发会撞 409。"""
        import uuid

        client = _agents_client(monkeypatch)
        body: Dict[str, Any] = {
            "score": 85,
            "node_id": f"{node_id}-{uuid.uuid4().hex[:8]}",
            "canvas_name": "b.canvas",
        }
        if vault_id is not None:
            body["vault_id"] = vault_id
        if group_id is not None:
            body["group_id"] = group_id
        return client.post("/api/v1/agents/recommend-action", json=body)

    def test_explicit_vault_maps_to_request_vault(self, monkeypatch):
        response = self._post(monkeypatch, vault_id="v_active")
        assert response.status_code == 200, response.text
        assert response.headers["X-Vault-Scope-Source"] == "request-vault"

    def test_legacy_group_id_maps_to_legacy_group(self, monkeypatch):
        response = self._post(monkeypatch, group_id="cs188")
        assert response.status_code == 200, response.text
        assert response.headers["X-Vault-Scope-Source"] == "legacy-group"

    def test_double_missing_maps_to_active_vault(self, monkeypatch):
        response = self._post(monkeypatch)
        assert response.status_code == 200, response.text
        assert response.headers["X-Vault-Scope-Source"] == "active-vault"

    def test_conflicting_vault_still_409(self, monkeypatch):
        """agents 契约里 409 不变 (G2-2 语义), header 不出现在失败响应。"""
        response = self._post(monkeypatch, vault_id="definitely_not_active_vault")
        assert response.status_code == 409
        assert "X-Vault-Scope-Source" not in response.headers
