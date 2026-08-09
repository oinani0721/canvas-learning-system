# RAG-S2-2026-08-09 阶段 2 T4 dedup+rerank — 契约测试（三组）
#
# 组 A retrieval_reranker 客户端: index 对齐 / sigmoid / 400+100 字截断 /
#       500·连接错误·响应缺洞 → None 不抛 / 3 连败熔断 60s 不再发 HTTP
# 组 B _dedup_by_source: 同源收敛取最高分保序 / taint·injection_risk·legacy
#       fail-closed 合并 / 无 source_path 不合并
# 组 C search_supplementary 集成: CE 是交付门不是排序器 (⛔ 两轮校准实证
#       CE 排序让转录反扑) — 门杀垃圾/放行低 raw 正解, 排序永远是加权序;
#       CE 失败字节级回落 (重过滤 min_relevance); env off = 旧行为;
#       内部字段 (_ce_text/_filter_score) 不泄漏; 金集 Tier R 兼容
#       (min_relevance=0 → 门不激活且零 CE 调用)
#
# CE HTTP 用 httpx.MockTransport 注入, 不碰真 18012。
#
# [Source: _bmad-output/研究/2026-08-09-RAG阶段2-强化fastpath实施计划.md T4]

import asyncio
import json
import math

import httpx
import pytest

from app.services import retrieval_reranker as rr
from app.services import supplementary_search_service as svc

# ═══════════════════════════════════════════════════════════════════════════════
# fixtures / helpers
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _reset_reranker_state():
    """熔断/长活 client 是模块全局 — 每个测试从干净状态出发。"""
    rr._fail_streak = 0
    rr._breaker_open_until = 0.0
    rr._client = None
    yield
    rr._fail_streak = 0
    rr._breaker_open_until = 0.0
    rr._client = None


def _install_transport(handler):
    """把 MockTransport 装进模块级 client 槽位。"""
    rr._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _rerank_response(scores_by_index: dict) -> dict:
    return {"results": [{"index": i, "relevance_score": logit} for i, logit in scores_by_index.items()]}


async def _close():
    await rr.close_retrieval_reranker()


# ═══════════════════════════════════════════════════════════════════════════════
# 组 A — retrieval_reranker 客户端
# ═══════════════════════════════════════════════════════════════════════════════


def test_scores_aligned_by_index_and_sigmoid():
    """乱序 index 响应 → 分数按 documents 顺序对齐; logit 0 → 0.5。"""

    def handler(request):
        return httpx.Response(200, json=_rerank_response({1: 6.0, 0: 0.0, 2: -6.0}))

    async def run():
        _install_transport(handler)
        out = await rr.score_documents("q", ["a", "b", "c"])
        await _close()
        return out

    scores = asyncio.run(run())
    assert scores is not None
    assert scores[0] == pytest.approx(0.5)
    assert scores[1] == pytest.approx(1.0 / (1.0 + math.exp(-6.0)))
    assert scores[2] == pytest.approx(1.0 / (1.0 + math.exp(6.0)))


def test_maxp_windows_and_query_truncation_in_payload():
    """⛔ 整批 500 防御: 900 字 doc 切 3 窗口 (400/400/100) 各 ≤400 字,
    query ≤100 字 — 每个 pair 都在 512 token 内。"""
    seen = {}

    def handler(request):
        payload = json.loads(request.content)
        seen["query"] = payload["query"]
        seen["documents"] = payload["documents"]
        return httpx.Response(200, json=_rerank_response({i: 1.0 for i in range(len(payload["documents"]))}))

    async def run():
        _install_transport(handler)
        out = await rr.score_documents("问" * 300, ["文" * 900])
        await _close()
        return out

    assert asyncio.run(run()) is not None
    assert len(seen["query"]) == 100
    assert len(seen["documents"]) == 3, "900 字应切 3 个 MaxP 窗口"
    assert all(len(d) <= 400 for d in seen["documents"])


def test_maxp_takes_max_window_score():
    """MaxP 聚合: 正解在 chunk 尾部窗口也能被看到 (单头截断 ce=0 事故回归锁)。"""

    def handler(request):
        payload = json.loads(request.content)
        assert len(payload["documents"]) == 2
        return httpx.Response(200, json=_rerank_response({0: -6.0, 1: 6.0}))

    async def run():
        _install_transport(handler)
        out = await rr.score_documents("q", ["头部无关内容" * 60 + "尾部正解文本" * 30])
        await _close()
        return out

    scores = asyncio.run(run())
    assert scores is not None
    assert scores[0] == pytest.approx(1.0 / (1.0 + math.exp(-6.0))), "文档分 = 窗口最大分"


def test_empty_document_scores_zero_without_request():
    """空文档得 0.0, 不占请求窗口。"""
    seen = {}

    def handler(request):
        payload = json.loads(request.content)
        seen["documents"] = payload["documents"]
        return httpx.Response(200, json=_rerank_response({0: 2.0}))

    async def run():
        _install_transport(handler)
        out = await rr.score_documents("q", ["", "有内容"])
        await _close()
        return out

    scores = asyncio.run(run())
    assert scores is not None
    assert scores[0] == 0.0
    assert scores[1] == pytest.approx(1.0 / (1.0 + math.exp(-2.0)))
    assert seen["documents"] == ["有内容"]


def test_http_500_returns_none_not_raise():
    def handler(request):
        return httpx.Response(500, json={"error": {"code": 500, "message": "too large"}})

    async def run():
        _install_transport(handler)
        out = await rr.score_documents("q", ["a", "b"])
        await _close()
        return out

    assert asyncio.run(run()) is None


def test_connect_error_returns_none():
    def handler(request):
        raise httpx.ConnectError("dead service")

    async def run():
        _install_transport(handler)
        out = await rr.score_documents("q", ["a"])
        await _close()
        return out

    assert asyncio.run(run()) is None


def test_incomplete_results_returns_none():
    """响应索引缺洞 → 整批失败 (部分分数会撕裂排序语义)。"""

    def handler(request):
        return httpx.Response(200, json=_rerank_response({0: 1.0}))  # 缺 index 1

    async def run():
        _install_transport(handler)
        out = await rr.score_documents("q", ["a", "b"])
        await _close()
        return out

    assert asyncio.run(run()) is None


def test_circuit_breaker_opens_after_three_failures():
    """3 连败 → 开路 60s, 第 4 次调用不再发 HTTP。"""
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(500)

    async def run():
        _install_transport(handler)
        for _ in range(3):
            assert await rr.score_documents("q", ["a"]) is None
        assert calls["n"] == 3
        # 第 4 次: 熔断开路, 不发请求
        assert await rr.score_documents("q", ["a"]) is None
        assert calls["n"] == 3
        await _close()

    asyncio.run(run())
    assert rr._breaker_open_until > 0


def test_success_resets_breaker_streak():
    state = {"fail": True}

    def handler(request):
        if state["fail"]:
            return httpx.Response(500)
        return httpx.Response(200, json=_rerank_response({0: 1.0}))

    async def run():
        _install_transport(handler)
        await rr.score_documents("q", ["a"])
        await rr.score_documents("q", ["a"])  # streak=2, 未达阈值
        state["fail"] = False
        assert await rr.score_documents("q", ["a"]) is not None
        await _close()

    asyncio.run(run())
    assert rr._fail_streak == 0


def test_empty_documents_short_circuit():
    async def run():
        return await rr.score_documents("q", [])

    assert asyncio.run(run()) == []


# ═══════════════════════════════════════════════════════════════════════════════
# 组 B — _dedup_by_source
# ═══════════════════════════════════════════════════════════════════════════════


def _mat(path, score, taint="clean", risk=0.0, **kw):
    return {
        "source_path": path,
        "score": score,
        "taint": taint,
        "injection_risk": risk,
        **kw,
    }


def test_dedup_keeps_first_highest_and_order():
    """materials 按 score 降序 → 首见即最高分; 文件间相对顺序保持。"""
    mats = [
        _mat("节点/A.md", 0.9),
        _mat("节点/A.md", 0.8),
        _mat("节点/B.md", 0.7),
        _mat("节点/A.md", 0.6),
        _mat("节点/C.md", 0.5),
    ]
    out = svc._dedup_by_source(mats)
    assert [m["source_path"] for m in out] == ["节点/A.md", "节点/B.md", "节点/C.md"]
    assert out[0]["score"] == 0.9


def test_dedup_merges_taint_fail_closed():
    """被合并 chunk 的 quarantine/风险分/legacy 旗帜不得被洗掉。"""
    mats = [
        _mat("节点/A.md", 0.9, taint="clean", risk=0.1),
        _mat("节点/A.md", 0.8, taint="quarantine", risk=0.7, is_legacy_fallback=True),
    ]
    out = svc._dedup_by_source(mats)
    assert len(out) == 1
    assert out[0]["taint"] == "quarantine"
    assert out[0]["injection_risk"] == 0.7
    assert out[0]["is_legacy_fallback"] is True


def test_dedup_no_source_path_not_merged():
    mats = [_mat("", 0.9), _mat("", 0.8)]
    assert len(svc._dedup_by_source(mats)) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# 组 C — search_supplementary 集成
# ═══════════════════════════════════════════════════════════════════════════════


class _DummyClient:
    _initialized = True


def _raw_row(path, raw_score, content="真实学习内容。" * 10):
    return {
        "score": raw_score,
        "_raw_score": raw_score,
        "content": content,
        "canvas_file": path,
        "metadata": {"canvas_file": path, "doc_type": "concept"},
    }


@pytest.fixture
def wired(monkeypatch):
    """把 svc 接到确定性测试替身上: 检索结果可注入 / 文件存在检查恒真 /
    source_priority 恒等 (加权重排不进本契约)。"""
    rows = []

    async def fake_two_tier(client, query, num_results):
        return list(rows)

    monkeypatch.setattr(svc, "_two_tier_search", fake_two_tier)
    monkeypatch.setattr(svc, "_is_real_vault_file", lambda path: True)

    import app.core.reference_config as ref

    monkeypatch.setattr(ref, "apply_source_priority", lambda r: r)
    return rows


def _search(**kw):
    return asyncio.run(svc.search_supplementary("测试查询", _DummyClient(), **kw))


def test_ce_gate_kills_junk_keeps_weighted_order(wired, monkeypatch):
    """CE 门: 垃圾被杀, 幸存者保持加权序, 内部字段不泄漏。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "true")
    wired.extend(
        [
            _raw_row("节点/A.md", 0.60),  # 加权分最高但 CE 判垃圾 → 被门杀
            _raw_row("节点/B.md", 0.55),
            _raw_row("节点/C.md", 0.52),
        ]
    )

    async def fake_scores(query, docs):
        return [0.001, 0.99, 0.6]

    monkeypatch.setattr(rr, "score_documents", fake_scores)
    result = _search(min_relevance=0.50, elbow_drop_threshold=0.25, hard_cap=10)
    paths = [m["source_path"] for m in result["materials"]]
    assert paths == ["节点/B.md", "节点/C.md"], "A(ce 0.001<0.02) 被门杀, 余下保持加权序"
    for m in result["materials"]:
        assert "_ce_text" not in m and "_filter_score" not in m
        assert "ce_score" in m


def test_ce_rescues_low_raw_score_hit(wired, monkeypatch):
    """核心受益面 (vq-a01/a02/a05): raw 0.4x 被 0.50 杀 → 放宽召回 + CE 高分交付。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "true")
    wired.extend(
        [
            _raw_row("节点/杂音.md", 0.55),
            _raw_row("节点/咖啡正解.md", 0.42),  # 旧行为: 0.42 < 0.50 永不进池
        ]
    )

    async def fake_scores(query, docs):
        return [0.005, 0.98]

    monkeypatch.setattr(rr, "score_documents", fake_scores)
    result = _search(min_relevance=0.50, elbow_drop_threshold=0.25, hard_cap=10)
    paths = [m["source_path"] for m in result["materials"]]
    assert paths == ["节点/咖啡正解.md"], "低 raw 正解被 CE 拯救, 高 raw 垃圾被 CE 处决"


def test_ce_failure_falls_back_to_legacy_behavior(wired, monkeypatch):
    """CE 整批失败: 收回放宽预过滤 (0.42 重新出局) + score 排序 + 旧 elbow。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "true")
    wired.extend(
        [
            _raw_row("节点/A.md", 0.60),
            _raw_row("节点/咖啡正解.md", 0.42),
        ]
    )

    async def fake_scores(query, docs):
        return None

    monkeypatch.setattr(rr, "score_documents", fake_scores)
    result = _search(min_relevance=0.50, elbow_drop_threshold=0.25, hard_cap=10)
    paths = [m["source_path"] for m in result["materials"]]
    assert paths == ["节点/A.md"], "回落必须与旧行为一致 (0.42 < min_relevance 出局)"
    assert all("ce_score" not in m for m in result["materials"])


def test_env_off_is_legacy_behavior(wired, monkeypatch):
    """RETRIEVAL_RERANKER_ENABLED=false → 预过滤即 min_relevance, 无 CE 调用。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "false")
    called = {"n": 0}

    async def fake_scores(query, docs):
        called["n"] += 1
        return [0.9]

    monkeypatch.setattr(rr, "score_documents", fake_scores)
    wired.extend([_raw_row("节点/A.md", 0.60), _raw_row("节点/低分.md", 0.42)])
    result = _search(min_relevance=0.50, elbow_drop_threshold=0.25, hard_cap=10)
    assert [m["source_path"] for m in result["materials"]] == ["节点/A.md"]
    assert called["n"] == 0


def test_tier_r_compat_no_gate_no_ce_call(wired, monkeypatch):
    """金集 Tier R: min_relevance=0 → 门不激活且不花 CE 预算, 全量加权序可评。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "true")
    wired.extend(
        [
            _raw_row("节点/A.md", 0.60),
            _raw_row("节点/B.md", 0.55),
            _raw_row("节点/C.md", 0.52),
        ]
    )
    called = {"n": 0}

    async def fake_scores(query, docs):
        called["n"] += 1
        return [0.9] * len(docs)

    monkeypatch.setattr(rr, "score_documents", fake_scores)
    result = _search(min_relevance=0.0, elbow_drop_threshold=1.01, hard_cap=20)
    paths = [m["source_path"] for m in result["materials"]]
    assert paths == ["节点/A.md", "节点/B.md", "节点/C.md"], "全量保留, 加权序不动"
    assert called["n"] == 0, "min_relevance=0 时不应花 CE 预算"


def test_dedup_active_in_both_paths(wired, monkeypatch):
    """同文件多 chunk 收敛为一条 — CE 成功与回落两路都生效。"""
    rows = [
        _raw_row("节点/A.md", 0.60),
        _raw_row("节点/A.md", 0.58),
        _raw_row("节点/B.md", 0.55),
    ]
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "true")
    wired.extend(rows)

    async def ok_scores(query, docs):
        assert len(docs) == 2, "dedup 应在 rerank 前收敛, CE 只见 2 条"
        return [0.9, 0.8]

    monkeypatch.setattr(rr, "score_documents", ok_scores)
    result = _search(min_relevance=0.50, elbow_drop_threshold=0.25, hard_cap=10)
    assert [m["source_path"] for m in result["materials"]] == ["节点/A.md", "节点/B.md"]

    async def fail_scores(query, docs):
        return None

    monkeypatch.setattr(rr, "score_documents", fail_scores)
    result2 = _search(min_relevance=0.50, elbow_drop_threshold=0.25, hard_cap=10)
    assert [m["source_path"] for m in result2["materials"]] == ["节点/A.md", "节点/B.md"]


def test_ce_never_reorders_weighted_ranking(wired, monkeypatch):
    """⛔ 两轮校准事故回归锁: CE 分数再高也不得重排 — 排序永远是
    T2/T3 验证过的加权序 (手写优先用户初衷), CE 只能杀不能排。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "true")
    hand = _raw_row("节点/手写.md", 0.5)
    hand["score"] = 0.75  # source_priority ×1.5
    hand["_raw_score"] = 0.5
    raw = _raw_row("raw/转录.md", 0.5)
    raw["score"] = 0.55  # 与手写 gap 0.2 < elbow 0.25, 不触发截断
    raw["_raw_score"] = 0.5
    wired.extend([hand, raw])

    async def fake_scores(query, docs):
        return [0.7, 0.95]  # 转录纯语义分更高 — 也不得爬到手写前面

    monkeypatch.setattr(rr, "score_documents", fake_scores)
    result = _search(min_relevance=0.50, elbow_drop_threshold=0.25, hard_cap=10)
    paths = [m["source_path"] for m in result["materials"]]
    assert paths == ["节点/手写.md", "raw/转录.md"], "CE 重排 = 转录反扑 (校准轮事故)"
    assert result["materials"][0]["ce_score"] == pytest.approx(0.7)
    assert "ce_rank_score" not in result["materials"][0], "融合排序键已废弃"


def test_breaker_half_open_recovery_and_reopen():
    """审查补锁: cooldown 到期后半开恢复发 HTTP; 再败立即复开。"""
    import time as _time

    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(500)

    async def run():
        _install_transport(handler)
        for _ in range(3):
            await rr.score_documents("q", ["a"])
        assert calls["n"] == 3 and rr._breaker_open_until > 0
        # cooldown 到期 (直接拨过开路时刻)
        rr._breaker_open_until = _time.monotonic() - 1
        await rr.score_documents("q", ["a"])
        assert calls["n"] == 4, "半开后应恢复发 HTTP"
        assert rr._breaker_open_until > _time.monotonic(), "再败应立即复开"
        await _close()

    asyncio.run(run())


def test_gate_kill_all_reports_distinct_reason(wired, monkeypatch):
    """审查补锁: CE 整批枪毙 → reason='ce_gate_all_filtered' (≠ raw 全低)。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "true")
    wired.extend([_raw_row("节点/A.md", 0.60), _raw_row("节点/B.md", 0.55)])

    async def fake_scores(query, docs):
        return [0.0, 0.0]

    monkeypatch.setattr(rr, "score_documents", fake_scores)
    result = _search(min_relevance=0.50, elbow_drop_threshold=0.25, hard_cap=10)
    assert result["materials"] == []
    assert result["degraded"] is False
    assert result["reason"] == "ce_gate_all_filtered"


def test_ce_score_not_rendered_in_xml(wired, monkeypatch):
    """审查补锁: ce_score 是内部量纲, 不得渗入 prompt 面 XML。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "true")
    wired.extend([_raw_row("节点/A.md", 0.60)])

    async def fake_scores(query, docs):
        return [0.987]

    monkeypatch.setattr(rr, "score_documents", fake_scores)
    result = _search(min_relevance=0.50, elbow_drop_threshold=0.25, hard_cap=10)
    assert result["materials"] and "ce_score" in result["materials"][0]
    xml = svc.format_supplementary_xml(result)
    assert "ce_score" not in xml


def test_relaxed_pool_does_not_evict_high_raw_hits(wired, monkeypatch):
    """⛔ 审查 HIGH 回归锁: 放宽地板行不占 top_k_max 配额 — CE 失败回落
    必须与旧版逐条一致 (被挤出的 raw>=min_relevance 正解不得丢失)。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "true")
    # 前 6 条 raw 0.45 (仅放宽池) + 后 3 条 raw 0.60 (旧版应交付的正解)
    wired.extend([_raw_row(f"节点/低分{i}.md", 0.45) for i in range(6)])
    wired.extend([_raw_row(f"节点/正解{i}.md", 0.60) for i in range(3)])

    async def fail_scores(query, docs):
        return None

    monkeypatch.setattr(rr, "score_documents", fail_scores)
    # top_k_max=6: 旧版 break 逻辑会让 6 条低分行填满池, 3 条正解全被挤出
    result = _search(min_relevance=0.50, elbow_drop_threshold=1.01, hard_cap=6, top_k_max=6)
    paths = [m["source_path"] for m in result["materials"]]
    assert paths == ["节点/正解0.md", "节点/正解1.md", "节点/正解2.md"], "回落必须找回被放宽行挤占的正解 (旧版等价)"

    # 门控路径: 正解也必须能被 CE 看到
    async def ok_scores(query, docs):
        assert len(docs) == 9, "CE 应看到全部 9 条候选 (含被旧 break 挤出的正解)"
        return [0.001] * 6 + [0.9] * 3

    monkeypatch.setattr(rr, "score_documents", ok_scores)
    result2 = _search(min_relevance=0.50, elbow_drop_threshold=1.01, hard_cap=6, top_k_max=6)
    paths2 = [m["source_path"] for m in result2["materials"]]
    assert paths2 == ["节点/正解0.md", "节点/正解1.md", "节点/正解2.md"]


def test_dedup_merges_ce_text_evidence(wired, monkeypatch):
    """审查 MEDIUM 回归锁: 同文件被合并 chunk 的 _ce_text 拼给幸存者 —
    正解在低分 chunk 时 CE 仍能看到 (文件粒度头截断瞎评的治法)。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "true")
    high = _raw_row("节点/A.md", 0.60, content="高分 chunk 的无关正文。")
    low = _raw_row("节点/A.md", 0.55, content="低分 chunk 里藏着咖啡烘焙正解。")
    wired.extend([high, low])
    seen = {}

    async def fake_scores(query, docs):
        seen["docs"] = list(docs)
        return [0.9]

    monkeypatch.setattr(rr, "score_documents", fake_scores)
    _search(min_relevance=0.50, elbow_drop_threshold=0.25, hard_cap=10)
    assert len(seen["docs"]) == 1, "dedup 后同文件只送一条"
    assert "咖啡烘焙正解" in seen["docs"][0], "被合并 chunk 的 CE 证据必须拼入"


def test_legacy_elbow_still_cuts_after_gate(wired, monkeypatch):
    """门杀之后 elbow 仍在加权 score 量纲工作 (gap 0.33 > 0.25 截断)。"""
    monkeypatch.setenv("RETRIEVAL_RERANKER_ENABLED", "true")
    wired.extend(
        [
            _raw_row("节点/A.md", 0.60),
            _raw_row("节点/B.md", 0.55),
            _raw_row("节点/C.md", 0.22),
        ]
    )

    async def fake_scores(query, docs):
        return [0.95, 0.9, 0.9]

    monkeypatch.setattr(rr, "score_documents", fake_scores)
    result = _search(min_relevance=0.20, elbow_drop_threshold=0.25, hard_cap=10)
    paths = [m["source_path"] for m in result["materials"]]
    assert paths == ["节点/A.md", "节点/B.md"], "悬崖后的 C 被加权序 elbow 截掉"
