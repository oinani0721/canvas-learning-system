"""RAG-S2 T4 (2026-08-10) — vault 检索链 cross-encoder 精排客户端。

bge-reranker-v2-m3 @ llama-server --rerank (:18012, POST /v1/rerank) 的
检索侧适配层。与 graphiti 记忆链的 LlamaServerRerankerClient
(app/graphiti/rerank_client.py) 同服务不同消费者 — 该客户端 rank() 以
文本为键丢 index 身份、每次调用新建 AsyncClient、零降级, 不适合检索精排
(T4 侦察实锤), 故此处独立实现:

- 模块级长活 httpx.AsyncClient (懒初始化 + close_retrieval_reranker 收尾)
- 消费 results[].index 保序保身份 (重复文本不塌缩)
- ⛔ 整批 500 防御 (实测): 任一 query+doc pair 超 512 token → llama-server
  整请求 500, 短文档也拿不到分。doc 截 400 字 + query 截 100 字
  (中文 XLM-R ≈1 token/字, 最坏 ~504 + 特殊 token < 512)
- 失败静默降级: 显式 catch httpx.HTTPError (含 Timeout/Connect/Status),
  返回 None → 调用方回落原排序; ⛔ 勿抄 memory_service 的窄 except 元组
  (HTTPStatusError 逃逸前科)
- 熔断: 连续 3 败开路 60s — 18012 是 11 天孤儿进程单点, 服务死亡时
  不给每条查询加恒定超时税

env (os.getenv 回落链, 照抄 app/graphiti/llm_factory.py 风格):
- RETRIEVAL_RERANKER_ENABLED: 默认 true
- RETRIEVAL_RERANKER_BASE_URL → GRAPHITI_RERANKER_BASE_URL →
  http://host.docker.internal:18012/v1 (容器内实测通)
- RETRIEVAL_RERANKER_TIMEOUT: 整批预算秒数, 默认 1.5
"""

from __future__ import annotations

import asyncio
import math
import os
import time

import httpx
import structlog

logger = structlog.get_logger(__name__)

_DEFAULT_BASE_URL = "http://host.docker.internal:18012/v1"
_DEFAULT_TIMEOUT_S = 1.5
_CONNECT_TIMEOUT_S = 0.5  # 服务死时快速 ConnectError, 不让握手吃光整批预算

# MaxP 多窗口 (Dai & Callan 2019 长文档 CE 标准范式): 单 400 字头部截断
# 会瞎 — 实测 chunk 尾部的正解文本 (咖啡句) 被截掉后 ce=0.0000 与垃圾
# 不可分。chunk 切 ≤5 个 400 字窗口全送评, 按窗口最大分聚合;
# 每个 query+窗口 pair 仍 < 512 token (整批 500 防御不破)。
# 2000 字覆盖英文 500-token chunk (≈4 chars/token, 审查 MEDIUM: 1200 字
# 让英文 chunk 尾部 40% 对 CE 不可见); 含长代码块的原子保护 chunk 可能
# 仍超 2000, 残余盲区已知 (全文切窗的调用量/延迟不划算)。
_DOC_CHAR_LIMIT = 2000
_WINDOW_CHARS = 400
_MAX_WINDOWS = 5
_QUERY_CHAR_LIMIT = 100

_BREAKER_FAIL_THRESHOLD = 3
_BREAKER_COOLDOWN_S = 60.0

_client: httpx.AsyncClient | None = None
_fail_streak = 0
_breaker_open_until = 0.0


def is_enabled() -> bool:
    """RETRIEVAL_RERANKER_ENABLED 真值检测 (默认 true — rerank 是 T4 主链)。"""
    val = os.environ.get("RETRIEVAL_RERANKER_ENABLED", "true").strip().lower()
    return val in ("1", "true", "yes", "on")


def _resolve_base_url() -> str:
    url = os.getenv("RETRIEVAL_RERANKER_BASE_URL") or os.getenv("GRAPHITI_RERANKER_BASE_URL") or _DEFAULT_BASE_URL
    return url.rstrip("/")


def _resolve_model() -> str:
    return os.getenv("GRAPHITI_RERANKER_MODEL") or "bge-reranker-v2-m3"


def _resolve_timeout() -> float:
    try:
        return float(os.getenv("RETRIEVAL_RERANKER_TIMEOUT", "") or _DEFAULT_TIMEOUT_S)
    except ValueError:
        return _DEFAULT_TIMEOUT_S


def _get_client(timeout_s: float) -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_s, connect=min(_CONNECT_TIMEOUT_S, timeout_s)),
        )
    return _client


async def close_retrieval_reranker() -> None:
    """FastAPI lifespan shutdown 收尾 — 关闭长活 client。"""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


def _breaker_is_open() -> bool:
    return time.monotonic() < _breaker_open_until


def _record_failure(reason: str) -> None:
    global _fail_streak, _breaker_open_until
    _fail_streak += 1
    if _fail_streak >= _BREAKER_FAIL_THRESHOLD:
        _breaker_open_until = time.monotonic() + _BREAKER_COOLDOWN_S
        logger.warning(
            "[RetrievalReranker] 连续失败达阈值, 熔断开路",
            streak=_fail_streak,
            cooldown_s=_BREAKER_COOLDOWN_S,
            reason=reason,
        )


def _record_success() -> None:
    global _fail_streak, _breaker_open_until
    _fail_streak = 0
    _breaker_open_until = 0.0


def _sigmoid(logit: float) -> float:
    # clamp 防 math.exp 溢出 (logit 实测范围 ±15 内, ±60 已远超)
    clamped = max(-60.0, min(60.0, logit))
    return 1.0 / (1.0 + math.exp(-clamped))


def _split_windows(text: str) -> list[str]:
    """文档 → ≤_MAX_WINDOWS 个 _WINDOW_CHARS 字窗口 (MaxP 输入)。"""
    text = (text or "")[:_DOC_CHAR_LIMIT]
    windows = []
    for start in range(0, len(text), _WINDOW_CHARS):
        piece = text[start : start + _WINDOW_CHARS].strip()
        if piece:
            windows.append(piece)
        if len(windows) >= _MAX_WINDOWS:
            break
    return windows


async def score_documents(query: str, documents: list[str]) -> list[float] | None:
    """整批 MaxP 精排 — 返回与 documents 同序对齐的 sigmoid(logit) 分数列表。

    每个文档切 ≤3 个 400 字窗口, 全部窗口一个请求送评,
    文档分 = 其窗口最大分 (MaxP)。空文档得 0.0 (不占请求)。

    任何失败 (超时/连接/HTTP 状态/响应缺洞/熔断开路) → None,
    调用方据此整批回落原排序。绝不抛异常、绝不返回残缺列表。
    """
    if not documents:
        return []
    if _breaker_is_open():
        return None

    windows: list[str] = []
    owner: list[int] = []  # windows[j] 属于 documents[owner[j]]
    for i, doc in enumerate(documents):
        for piece in _split_windows(doc):
            windows.append(piece)
            owner.append(i)

    scores = [0.0] * len(documents)  # 空文档留 0.0
    if not windows:
        return scores

    timeout_s = _resolve_timeout()
    payload = {
        "model": _resolve_model(),
        "query": (query or "")[:_QUERY_CHAR_LIMIT],
        "documents": windows,
    }
    try:
        client = _get_client(timeout_s)
        resp = await client.post(f"{_resolve_base_url()}/rerank", json=payload)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results") if isinstance(data, dict) else None
    except asyncio.CancelledError:
        # hook 外层预算 (chat.py wait_for 5s) 中途取消 — 记账后必须重抛
        # (CancelledError 不可吞); 不记账则慢检索模式下熔断永不开路,
        # 每条请求重复付 CE 税 (审查 LOW)
        _record_failure("cancelled")
        raise
    except httpx.HTTPError as e:
        _record_failure(type(e).__name__)
        logger.warning(
            "[RetrievalReranker] 精排失败, 回落原排序",
            error=str(e)[:120],
            docs=len(documents),
            windows=len(windows),
        )
        return None
    except (ValueError, KeyError, TypeError, AttributeError) as e:  # JSON 解析/结构异常
        _record_failure(type(e).__name__)
        logger.warning("[RetrievalReranker] 响应解析失败", error=str(e)[:120])
        return None

    if not isinstance(results, list):
        # 畸形 200 响应 (顶层非 dict / results 非 list — base_url 误配到
        # 非 rerank 端点时的实况): 走失败记账, 不违背 "绝不抛异常" 契约
        _record_failure("malformed_body")
        logger.warning("[RetrievalReranker] 响应体形状非法, 回落原排序")
        return None

    window_scores: list[float | None] = [None] * len(windows)
    for r in results:
        if not isinstance(r, dict):
            continue
        idx = r.get("index")
        if isinstance(idx, int) and 0 <= idx < len(windows):
            try:
                window_scores[idx] = _sigmoid(float(r["relevance_score"]))
            except (KeyError, TypeError, ValueError):
                pass
    if any(s is None for s in window_scores):
        # 响应缺洞 → 整批失败 (部分窗口分会让 MaxP 聚合语义撕裂)
        _record_failure("incomplete_results")
        logger.warning(
            "[RetrievalReranker] 响应索引缺洞, 回落原排序",
            expected=len(windows),
            got=len(results),
        )
        return None

    for j, ws in enumerate(window_scores):
        i = owner[j]
        if ws > scores[i]:  # type: ignore[operator]
            scores[i] = ws  # MaxP: 文档分 = 窗口最大分

    _record_success()
    return scores


__all__ = [
    "is_enabled",
    "score_documents",
    "close_retrieval_reranker",
]
