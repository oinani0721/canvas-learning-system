# RAG-S0-2026-08-02 阶段 0 止血 — 第一批契约测试
#
# 锁住六条不许回潮的契约：
#   1. search_notes 默认走 fast path（不 invoke LangGraph 死管道）
#   2. 响应体必须申报 execution_mode（诚实状态取代 quality 假信号）
#   3. 健康空结果 (ok_empty) 与基础设施故障 (error) 必须可区分
#   4. docker-compose 与 agentic_rag config 使用同一 LanceDB 路径
#      （P0-B 根因：代码读 LANCEDB_PATH、compose 设 LANCEDB_DATA_PATH → 空目录 3 个月）
#   5. LANCEDB_DATA_PATH 与 LANCEDB_PATH 冲突时启动 fail-fast
#   6. requirements.txt 锁死 langgraph 精确版本（容器实测 1.1.10）
#
# [Source: RAG-S0-2026-08-02 — _bmad-output/研究/2026-08-02-RAG修复计划-用户审阅版.md]

import re
from pathlib import Path

import pytest
import yaml

from app.mcp.tools import note_search_tools

_REPO_ROOT = Path(__file__).parents[3]  # backend/tests/regression/ -> repo root
_COMPOSE_PATH = _REPO_ROOT / "docker-compose.yml"
_REQUIREMENTS_PATH = _REPO_ROOT / "requirements.txt"


def _sample_supp_result(n: int = 2):
    """Shaped like search_supplementary output (RAG-S2 T5: fast path 走共享链,
    _fast_path_search 返回整个 supp dict 而非裸行列表)。"""
    return {
        "materials": [
            {
                "title": f"note-{i}",
                "wikilink": f"[[note-{i}]]",
                "snippet": f"chunk-{i}",
                "content": f"chunk-{i} full content",
                "score": 0.9 - i * 0.1,
                "source_path": f"note-{i}.md",
                "taint": "clean",
                "fts_confirmed": True,
                "doc_type": "concept",
            }
            for i in range(n)
        ],
        "degraded": False,
        "reason": None if n else "all_filtered_below_threshold",
        "confidence": {"level": "medium", "signals": {"delivered": n}},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 契约 1: 默认 fast path，LangGraph 管道不得被 invoke
# ═══════════════════════════════════════════════════════════════════════════════


async def test_search_notes_defaults_to_fast_path(monkeypatch):
    monkeypatch.delenv("RAG_EXTENDED_MODE", raising=False)
    calls = {"fast": 0}

    async def fast_path_double(query, max_results):
        calls["fast"] += 1
        return _sample_supp_result()

    monkeypatch.setattr(note_search_tools, "_fast_path_search", fast_path_double)

    import app.services.rag_service as rag_service_module

    def pipeline_tripwire():
        raise AssertionError(
            "LangGraph pipeline must NOT be invoked on the default path "
            "(RAG-S0-2026-08-02: 6-source pipeline retired from default chain)"
        )

    monkeypatch.setattr(rag_service_module, "get_rag_service", pipeline_tripwire)

    out = await note_search_tools.search_notes(query="特征值")

    assert calls["fast"] == 1
    assert out["execution_mode"] == "fast"
    assert out["status"] == "ok"
    assert out["total_count"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# 契约 2: 响应体申报 execution_mode，quality 假信号不得回潮
# ═══════════════════════════════════════════════════════════════════════════════


async def test_response_declares_execution_mode(monkeypatch):
    monkeypatch.delenv("RAG_EXTENDED_MODE", raising=False)

    async def fast_path_double(query, max_results):
        return _sample_supp_result()

    monkeypatch.setattr(note_search_tools, "_fast_path_search", fast_path_double)

    out = await note_search_tools.search_notes(query="q")

    assert out["execution_mode"] in ("fast", "extended", "fallback")
    assert out["source_status"] in ("ok_nonempty", "ok_empty", "error")
    # 废除的假信号不得回潮：死管道对自身空结果评出的恒 low
    assert "quality_grade" not in out


# ═══════════════════════════════════════════════════════════════════════════════
# 契约 3: 健康空结果 ≠ 基础设施故障
# ═══════════════════════════════════════════════════════════════════════════════


async def test_healthy_empty_is_distinct_from_error(monkeypatch):
    monkeypatch.delenv("RAG_EXTENDED_MODE", raising=False)

    async def empty_fast_path(query, max_results):
        return _sample_supp_result(0)

    monkeypatch.setattr(note_search_tools, "_fast_path_search", empty_fast_path)
    ok_empty = await note_search_tools.search_notes(query="q")

    assert ok_empty["status"] == "ok"
    assert ok_empty["source_status"] == "ok_empty"
    assert ok_empty["total_count"] == 0

    async def broken_fast_path(query, max_results):
        raise RuntimeError("bge-m3 embedding returned None")

    monkeypatch.setattr(note_search_tools, "_fast_path_search", broken_fast_path)
    err = await note_search_tools.search_notes(query="q")

    assert err["status"] == "error"
    assert err["source_status"] == "error"
    assert err["message"] != ""
    # 核心契约：空结果与故障永不混同
    assert ok_empty["source_status"] != err["source_status"]


# ═══════════════════════════════════════════════════════════════════════════════
# 契约 4: compose 与 agentic_rag config 指向同一 LanceDB 容器路径
# ═══════════════════════════════════════════════════════════════════════════════


def test_compose_and_agentic_config_use_same_lancedb_path(monkeypatch):
    compose = yaml.safe_load(_COMPOSE_PATH.read_text(encoding="utf-8"))
    env = compose["services"]["backend"]["environment"]
    if isinstance(env, dict):
        compose_val = env.get("LANCEDB_DATA_PATH")
    else:
        compose_val = next(
            (entry.split("=", 1)[1] for entry in env if entry.startswith("LANCEDB_DATA_PATH=")),
            None,
        )
    assert compose_val, (
        "docker-compose backend must set LANCEDB_DATA_PATH (P0-B root cause: env name mismatch -> empty directory)"
    )

    from agentic_rag.config import _resolve_lancedb_db_path

    monkeypatch.setenv("LANCEDB_DATA_PATH", compose_val)
    monkeypatch.delenv("LANCEDB_PATH", raising=False)
    assert _resolve_lancedb_db_path() == compose_val


# ═══════════════════════════════════════════════════════════════════════════════
# 契约 5: 双 env 冲突必须 fail-fast（防静默连空目录重演）
# ═══════════════════════════════════════════════════════════════════════════════


def test_conflicting_lancedb_env_fails_startup(monkeypatch):
    from agentic_rag.config import _resolve_lancedb_db_path

    monkeypatch.setenv("LANCEDB_DATA_PATH", "/lancedb")
    monkeypatch.setenv("LANCEDB_PATH", "/somewhere/else")
    with pytest.raises(RuntimeError, match="Conflicting LanceDB paths"):
        _resolve_lancedb_db_path()

    # 接线断言：agentic_rag/__init__ 与 rag_service 会把 import 时的 RuntimeError
    # 吞成 AGENTIC_RAG_AVAILABLE=False（静默降级）。只有 main.py lifespan 无守护
    # 直调 resolver，冲突才能真正阻断启动——锁住这根线不被移除。
    main_src = (_REPO_ROOT / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    assert "_resolve_lancedb_db_path()" in main_src, (
        "main.py lifespan must call _resolve_lancedb_db_path() unguarded, "
        "otherwise the env-conflict RuntimeError is swallowed into silent "
        "degradation and never aborts startup"
    )

    # 同值不算冲突；单设 legacy 仍兼容可读
    monkeypatch.setenv("LANCEDB_PATH", "/lancedb")
    assert _resolve_lancedb_db_path() == "/lancedb"

    monkeypatch.delenv("LANCEDB_DATA_PATH")
    monkeypatch.setenv("LANCEDB_PATH", "/legacy/only")
    assert _resolve_lancedb_db_path() == "/legacy/only"


# ═══════════════════════════════════════════════════════════════════════════════
# 契约 6: langgraph 必须锁精确版本（docker pip install -r 不消费 uv.lock）
# ═══════════════════════════════════════════════════════════════════════════════


def test_requirements_pins_langgraph_exact():
    text = _REQUIREMENTS_PATH.read_text(encoding="utf-8")
    specs = []
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        if re.match(r"^langgraph([=<>!~ ]|$)", stripped):
            specs.append(stripped)

    assert specs, "requirements.txt must declare langgraph"
    assert len(specs) == 1, f"expected exactly one langgraph spec, got {specs!r}"
    assert re.fullmatch(r"langgraph==\d+\.\d+\.\d+", specs[0]), (
        f"langgraph must be pinned exact (==x.y.z), got: {specs[0]!r}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 契约 7 (Code-Review HIGH-1): 初始化失败的 client 不得入缓存，下次请求必须重试
# LanceDBClient.initialize() 失败时 return False 而非抛异常——若不检查返回值，
# 坏 client (_db=None) 会被缓存并毒化整个进程生命周期的所有请求。
# ═══════════════════════════════════════════════════════════════════════════════


async def test_failed_init_is_not_cached_and_retries(monkeypatch):
    monkeypatch.setattr(note_search_tools, "_fast_client", None)
    monkeypatch.setattr(note_search_tools, "_fast_client_lock", None)

    import agentic_rag.clients as clients_module

    attempts = {"n": 0}

    class _InitFlakyClient:
        def __init__(self, db_path, **kwargs):
            self.db_path = db_path
            self._db = None

        async def initialize(self):
            attempts["n"] += 1
            if attempts["n"] == 1:
                return False  # LanceDBClient 失败语义: return False, 不抛
            self._db = object()
            return True

    monkeypatch.setattr(clients_module, "LanceDBClient", _InitFlakyClient)

    with pytest.raises(RuntimeError, match="not cached"):
        await note_search_tools._get_fast_client()
    assert note_search_tools._fast_client is None, "a client whose initialize() failed must NOT be cached"

    retried = await note_search_tools._get_fast_client()
    assert attempts["n"] == 2, "second call must retry initialization"
    assert note_search_tools._fast_client is retried


# ═══════════════════════════════════════════════════════════════════════════════
# 契约 8 (Code-Review MEDIUM-1): extended 分支的归因语义
# 管道空/抛异常 → fallback 交付, execution_mode 必须申报 "fallback";
# fallback 自身再失败, 错误也必须归因 "fallback" 而非 "extended"——
# 阶段 4 shadow 评估依赖此归因区分管道故障与 fast path 基础设施故障。
# ═══════════════════════════════════════════════════════════════════════════════


class _DeadPipelineService:
    async def query(self, **kwargs):
        raise RuntimeError("pipeline dead")


async def test_extended_pipeline_failure_reports_fallback(monkeypatch):
    monkeypatch.setenv("RAG_EXTENDED_MODE", "1")

    import app.services.rag_service as rag_service_module

    monkeypatch.setattr(rag_service_module, "get_rag_service", lambda: _DeadPipelineService())

    async def fast_path_double(query, max_results):
        return _sample_supp_result()

    monkeypatch.setattr(note_search_tools, "_fast_path_search", fast_path_double)

    out = await note_search_tools.search_notes(query="q")

    assert out["execution_mode"] == "fallback"
    assert out["status"] == "ok"
    assert out["source_status"] == "ok_nonempty"


async def test_fallback_failure_attributed_to_fallback_not_pipeline(monkeypatch):
    monkeypatch.setenv("RAG_EXTENDED_MODE", "1")

    import app.services.rag_service as rag_service_module

    monkeypatch.setattr(rag_service_module, "get_rag_service", lambda: _DeadPipelineService())

    async def broken_fast_path(query, max_results):
        raise RuntimeError("fast path infrastructure down")

    monkeypatch.setattr(note_search_tools, "_fast_path_search", broken_fast_path)

    out = await note_search_tools.search_notes(query="q")

    assert out["execution_mode"] == "fallback", (
        "fast-path failure during fallback must be attributed to 'fallback', "
        "not 'extended' — otherwise shadow evaluation blames the pipeline"
    )
    assert out["status"] == "error"
    assert out["source_status"] == "error"
