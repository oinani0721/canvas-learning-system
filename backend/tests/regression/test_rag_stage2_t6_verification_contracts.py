# RAG-S2-2026-08-09 阶段 2 T6 验证收尾 — 对抗审查 CONFIRMED findings 回归锁（五组）
#
# 组 A elbow 前置 (审查 HIGH): 悬崖检测在 dedup/CE 门抽稀之前的全量序列上做
#       — 抽稀后幸存者 gap telescoping 不再是语义悬崖, 不得误砍放行的真材料
# 组 B fts_confirmed 名实 (审查 HIGH, 双 lens 同报): _rrf_score 写给所有融合
#       行不承载通道信息; 双通道确认 = _fts_hit and not _fts_only —
#       dense-only 恒 False / FTS-only False / 真双通道 True
# 组 C 检索层故障诚实化 (审查 MEDIUM×2): _search_internal 全分支故障 raise
#       (受 search() 外层 enable_fallback 门控, 默认 True 调用方行为不变);
#       hook singleton 关吞噬 + init 失败不缓存
# 组 D HARD-ISO 查询侧排除传播 (审查 HIGH, live 泄漏): vault_notes_retriever
#       默认排除表补 exam_board; react_agent / tool_executor / agent_graph
#       三条 flag-gated 链同批补齐 (纵深)
# 组 E 全量序列悬崖在 top_k 之外时不误伤池内条目 (elbow 分数线边界)
#
# [Source: T6 workflow 对抗审查 8 CONFIRMED (wf_34353886-9a2) + 逐条证伪]

import asyncio

import pytest

from app.api.v1.endpoints import chat as chat_module
from app.services import retrieval_reranker as rr
from app.services import supplementary_search_service as svc

# ═══════════════════════════════════════════════════════════════════════════════
# fixtures / helpers（与 chain_unify 契约文件同源姿势）
# ═══════════════════════════════════════════════════════════════════════════════


class _DummyClient:
    _initialized = True

    async def _get_query_vector(self, query):
        return [0.1, 0.2]


def _raw_row(path, raw_score, score=None, fts=False):
    metadata = {"canvas_file": path, "doc_type": "concept", "_rrf_score": 0.032}
    if fts:
        metadata["_fts_hit"] = True
    return {
        "score": score if score is not None else raw_score,
        "_raw_score": raw_score,
        "content": "真实学习内容。" * 10,
        "canvas_file": path,
        "metadata": metadata,
    }


@pytest.fixture
def wired(monkeypatch):
    rows = []

    async def canned_two_tier(client, query, num_results):
        return list(rows)

    monkeypatch.setattr(svc, "_two_tier_search", canned_two_tier)
    monkeypatch.setattr(svc, "_is_real_vault_file", lambda path: True)

    import app.core.reference_config as ref

    monkeypatch.setattr(ref, "apply_source_priority", lambda r: r)
    return rows


def _search(**kw):
    return asyncio.run(svc.search_supplementary("测试查询", _DummyClient(), **kw))


# ═══════════════════════════════════════════════════════════════════════════════
# 组 A — elbow 前置: 抽稀不得制造假悬崖
# ═══════════════════════════════════════════════════════════════════════════════


def test_gate_thinning_elbow_is_deliberate_t4_behavior(wired, monkeypatch):
    """⛔ 三轮金集 A/B 裁决记录锁 (2026-08-10, 勿无据翻案): CE 门抽稀后的
    telescoping gap 截断**保留** — 审查 CONFIRMED 其数学伪影性质
    ([0.95,0.80,0.62] 门杀中段后 [0.95,0.62] gap 0.33 截掉已放行的 0.62),
    但两种修复都被金集打回:
      门后 elbow (T4, 本行为)      交付 81.82% / 污染 39.83% / FPR 6%
      全量序列 floor (审查 fix 版)  交付 83.64% / 污染 57.38% / FPR 8%
      dedup 后门前 floor (二次校准) 交付 81.82% / 污染 48.25% / FPR 8%
    +1.8pp 命中换不回 +8~17pp 污染 — 门后截断是净正收益的保守护栏。
    翻案条件: 新的金集 A/B 数据证明相反, 并同步改本锁与 svc 调用点注释。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "true")
    wired.extend(
        [
            _raw_row("节点/A.md", 0.63, score=0.95),
            _raw_row("节点/中段垃圾.md", 0.53, score=0.80),
            _raw_row("节点/正解.md", 0.62, score=0.62),
        ]
    )

    async def canned_scores(query, docs):
        return [0.9, 0.001, 0.9]  # 中段被 CE 门杀

    monkeypatch.setattr(rr, "score_documents", canned_scores)
    result = _search(min_relevance=0.50, elbow_drop_threshold=0.25, hard_cap=10)
    paths = [m["source_path"] for m in result["materials"]]
    assert paths == ["节点/A.md"], "T4 行为: 门抽稀后 gap 0.33>0.25 截断 (金集裁决的保守护栏, 见 docstring)"


def test_dedup_collapsed_sequence_true_cliff_still_cuts(wired, monkeypatch):
    """⛔ 金集二次校准回归锁 (交付污染 39.83%→57.38% 打回全量版的实证):
    悬崖域 = dedup 之后 — 同文件重复 chunk 的相邻分数不得填平文件间
    真悬崖 (填平 → 转录尾巴全放行)。dedup 收敛后 [0.95, 0.47] gap 0.48
    是真实文件间落差, 照常截断。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "false")
    wired.extend(
        [
            _raw_row("节点/手写.md", 0.63, score=0.95),
            _raw_row("节点/手写.md", 0.53, score=0.80),  # 同文件次 chunk 填平 gap
            _raw_row("raw/转录尾巴.md", 0.55, score=0.55),
        ]
    )
    result = _search(min_relevance=0.50, elbow_drop_threshold=0.25, hard_cap=10)
    paths = [m["source_path"] for m in result["materials"]]
    assert paths == ["节点/手写.md"], "dedup 后 0.95→0.55 gap 0.40 是真悬崖 — 重复 chunk 不得替转录尾巴续命"


def test_true_cliff_in_full_sequence_still_cuts(wired, monkeypatch):
    """全量序列上的真悬崖仍然截断 (R1 校准语义不变)。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "false")
    wired.extend(
        [
            _raw_row("节点/A.md", 0.60),
            _raw_row("节点/B.md", 0.55),
            _raw_row("节点/C.md", 0.22),
        ]
    )
    result = _search(min_relevance=0.20, elbow_drop_threshold=0.25, hard_cap=10)
    paths = [m["source_path"] for m in result["materials"]]
    assert paths == ["节点/A.md", "节点/B.md"], "gap 0.33 > 0.25 的真悬崖照常截断"


def test_elbow_score_floor_unit():
    """分数线语义: 悬崖下沿分数; 无悬崖 -inf。"""
    mats = [{"score": 0.9}, {"score": 0.8}, {"score": 0.4}, {"score": 0.35}]
    assert svc._elbow_score_floor(mats, drop_threshold=0.25) == pytest.approx(0.4)
    assert svc._elbow_score_floor(mats, drop_threshold=0.5) == float("-inf")
    assert svc._elbow_score_floor([], drop_threshold=0.25) == float("-inf")


# ═══════════════════════════════════════════════════════════════════════════════
# 组 B — fts_confirmed 名实修复
# ═══════════════════════════════════════════════════════════════════════════════


def test_rrf_fuse_marks_fts_channel_membership():
    """_rrf_fuse 层: _fts_hit 只写给 FTS 通道成员; dense-only 行只有
    _rrf_score (对所有行恒在, 不承载通道信息)。"""
    from agentic_rag.clients.lancedb_client import LanceDBClient

    client = LanceDBClient.__new__(LanceDBClient)  # 不跑 __init__, 只用纯函数
    vector_rows = [
        {"doc_id": "dual", "content": "双通道", "_distance": 0.3},
        {"doc_id": "dense_only", "content": "纯向量", "_distance": 0.35},
    ]
    fts_rows = [
        {"doc_id": "dual", "content": "双通道"},
        {"doc_id": "fts_only", "content": "纯词法"},
    ]
    fused = {r["doc_id"]: r for r in client._rrf_fuse(vector_rows, fts_rows, limit=10)}

    assert fused["dual"].get("_fts_hit") is True
    assert not fused["dual"].get("_fts_only")
    assert fused["dense_only"].get("_fts_hit") is None, "dense-only 不得有 FTS 成员标记"
    assert fused["dense_only"].get("_rrf_score"), "_rrf_score 对所有融合行恒在 (名不副实的旧信号)"
    assert fused["fts_only"].get("_fts_hit") is True
    assert fused["fts_only"].get("_fts_only") is True


def test_fts_confirmed_semantics_at_normalize_layer():
    """svc 层: dense-only 恒 False (旧公式恒 True 的名实颠倒回归锁);
    FTS-only False (不给特权); 真双通道 True。"""
    dense_only = svc._normalize_material({"score": 0.6, "metadata": {"canvas_file": "a.md", "_rrf_score": 0.03}})
    assert dense_only["fts_confirmed"] is False, "dense-only 命中不得再冒充双通道确认"

    fts_only = svc._normalize_material(
        {"score": 0.47, "metadata": {"canvas_file": "b.md", "_rrf_score": 0.03, "_fts_hit": True, "_fts_only": True}}
    )
    assert fts_only["fts_confirmed"] is False, "FTS-only 不给特权 (维持 R1 定案)"

    dual = svc._normalize_material(
        {"score": 0.6, "metadata": {"canvas_file": "c.md", "_rrf_score": 0.03, "_fts_hit": True}}
    )
    assert dual["fts_confirmed"] is True


def test_fts_hit_passes_convert_whitelist():
    """_convert_to_search_results 白名单必须透传 _fts_hit — 否则名实修复
    在生产链路上是 dead field。"""
    from agentic_rag.clients.lancedb_client import LanceDBClient

    client = LanceDBClient.__new__(LanceDBClient)
    out = client._convert_to_search_results(
        [{"doc_id": "d1", "content": "x", "_distance": 0.3, "_rrf_score": 0.03, "_fts_hit": True}]
    )
    assert out and out[0]["metadata"].get("_fts_hit") is True


# ═══════════════════════════════════════════════════════════════════════════════
# 组 C — 检索层故障诚实化
# ═══════════════════════════════════════════════════════════════════════════════


class _BrokenDB:
    """open_table 恒抛 — 模拟表损坏/丢失的基础设施故障。"""

    def open_table(self, name):
        raise ValueError("dataset corrupted")


def _make_lightweight_client(enable_fallback):
    from agentic_rag.clients.lancedb_client import LanceDBClient

    client = LanceDBClient(db_path="/tmp/nonexistent-t6-test", enable_fallback=enable_fallback)
    client._db = _BrokenDB()
    client._initialized = True
    return client


def test_open_table_failure_raises_with_fallback_off():
    """审查 MEDIUM 回归锁: enable_fallback=False 时表打不开必须 raise
    (旧行为吞成 [] → 假 empty_index/ok_empty, 阶段 0 契约 3 被架空)。"""
    client = _make_lightweight_client(enable_fallback=False)
    with pytest.raises(Exception, match="open_table|failed"):
        asyncio.run(client.search(query="q", table_name="vault_notes", num_results=5))


def test_open_table_failure_swallowed_with_fallback_on():
    """enable_fallback=True (默认) 调用方行为不变: 外层门吞成 []。"""
    client = _make_lightweight_client(enable_fallback=True)
    out = asyncio.run(client.search(query="q", table_name="vault_notes", num_results=5))
    assert out == []


def test_hook_singleton_disables_fallback_and_rejects_bad_init(monkeypatch):
    """审查 MEDIUM 回归锁: hook singleton 必须关吞噬 (enable_fallback=False),
    且 initialize 失败的 client 不得入缓存 (与 MCP _get_fast_client 同契约)。"""

    class _StubClient:
        _initialized = False
        _db = None
        enable_fallback = True

        async def initialize(self):
            return False  # LanceDBClient 失败语义: return False 不抛

    stub = _StubClient()
    monkeypatch.setattr(chat_module, "_supp_lancedb_singleton", None)
    monkeypatch.setattr(chat_module, "_supp_init_task", None)

    import app.api.v1.endpoints.metadata as metadata_module

    monkeypatch.setattr(metadata_module, "get_lancedb_client", lambda: stub)
    result = asyncio.run(chat_module._init_supp_lancedb_singleton())
    assert result is None, "init 失败的 client 不得缓存"
    assert chat_module._supp_lancedb_singleton is None
    assert stub.enable_fallback is False, "hook 专属实例必须关掉 search() 异常吞噬"

    class _GoodClient(_StubClient):
        async def initialize(self):
            self._db = object()
            self._initialized = True
            return True

    good = _GoodClient()
    monkeypatch.setattr(metadata_module, "get_lancedb_client", lambda: good)
    result2 = asyncio.run(chat_module._init_supp_lancedb_singleton())
    assert result2 is good
    assert good.enable_fallback is False
    # 清理模块全局, 不污染其他测试
    monkeypatch.setattr(chat_module, "_supp_lancedb_singleton", None)


def test_hook_empty_note_does_not_assert_retrieval_healthy():
    """审查 MEDIUM 文案锁: 空交付标注不得替检索层做「正常」的主动断言。"""
    note = chat_module._empty_supp_context({"materials": [], "degraded": False, "reason": "empty_index"})
    assert "未检测到降级信号" in note
    assert "检索正常但确无" not in note


# ═══════════════════════════════════════════════════════════════════════════════
# 组 D — HARD-ISO 查询侧排除传播
# ═══════════════════════════════════════════════════════════════════════════════


def test_vault_notes_retriever_default_excludes_exam_board():
    """⛔ 审查 HIGH 回归锁 (live 泄漏通道): LangGraph retrieve_vault_notes
    节点默认口径必须含 exam_board — 经无鉴权 /api/v1/rag/query 可达。"""
    from agentic_rag.retrievers.vault_notes_retriever import VaultNotesRetrieverConfig

    excludes = VaultNotesRetrieverConfig().default_exclude_doc_types
    assert "exam_board" in excludes
    assert "whiteboard" in excludes


def test_react_agent_search_excludes_exam_board(monkeypatch):
    """flag-gated 纵深 (ENABLE_REACT_AGENT): search_vault_notes 两条调用
    都必须带 exam_board 排除。"""
    from app.services import react_agent

    calls = []

    class _CaptureClient:
        async def search(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise RuntimeError("hybrid down")  # 逼出 vector 回退调用
            return []

    monkeypatch.setattr(react_agent, "_lancedb_client", _CaptureClient())
    asyncio.run(react_agent.search_vault_notes.ainvoke({"query": "q", "num_results": 3}))
    assert len(calls) == 2
    for kw in calls:
        assert "exam_board" in kw.get("exclude_doc_types", []), "react agent 链不得成为题面泄漏通道"


def test_tool_executor_search_excludes_exam_board(monkeypatch):
    """flag-gated 纵深 (ENABLE_TOOL_CALLING): ToolExecutor 主查+回退表都带
    exam_board 排除。"""
    from app.services.tool_executor import ToolExecutor

    calls = []

    class _CaptureClient:
        async def search(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise RuntimeError("vault_notes down")  # 逼出回退表调用
            return []

    executor = ToolExecutor(lancedb_client=_CaptureClient())
    asyncio.run(executor._search_vault_notes(query="q"))
    assert len(calls) == 2
    for kw in calls:
        assert "exam_board" in kw.get("exclude_doc_types", [])


def test_agent_graph_retrieve_excludes_exam_board():
    """flag-gated 纵深 (ENABLE_AGENT_GRAPH): retrieve 节点 vault_notes 主查
    带 exam_board 排除 (静态源码锁 — get_instance 单例不宜在测试进程实例化)。"""
    import inspect

    from agentic_rag import agent_graph

    src = inspect.getsource(agent_graph.retrieve)
    assert "exam_board" in src, "agent_graph.retrieve 的 vault_notes 查询必须排除 exam_board"


# ═══════════════════════════════════════════════════════════════════════════════
# 组 E — elbow 分数线边界
# ═══════════════════════════════════════════════════════════════════════════════


def test_cliff_beyond_topk_does_not_evict_pool(wired, monkeypatch):
    """全量序列的悬崖出现在 top_k_max 之外时, 分数线只影响悬崖之下 —
    池内条目 (score 全在悬崖之上) 不受影响。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "false")
    wired.extend([_raw_row(f"节点/N{i}.md", 0.60 - i * 0.01) for i in range(4)])
    wired.append(_raw_row("节点/悬崖下.md", 0.21))  # gap 0.36 > 0.25, 在第 5 位
    result = _search(min_relevance=0.20, elbow_drop_threshold=0.25, hard_cap=10, top_k_max=4)
    paths = [m["source_path"] for m in result["materials"]]
    assert paths == [f"节点/N{i}.md" for i in range(4)], "悬崖之上的池内条目全保留, 悬崖之下截断"
