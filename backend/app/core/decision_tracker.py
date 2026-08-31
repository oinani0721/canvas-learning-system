"""Decision ID tracker for business logic traceability.

Generates DECN-{uuid8} IDs at key decision points and logs them
via structlog for correlation with request_id.

Usage in service functions:
    from app.core.decision_tracker import log_decision

    log_decision(
        function="determine_mastery_level",
        input_summary={"node_id": node_id, "score": score},
        output="Developing",
        reason="score 0.45 < proficient_threshold 0.6",
        request_id=request_id,  # optional
    )
"""

import json
import logging
import uuid
from typing import Any, Dict, Optional

import structlog

from app.models.service_status import ServiceStatus

logger = logging.getLogger(__name__)


def generate_decision_id() -> str:
    """Generate a unique decision ID in DECN-{8-hex} format."""
    return f"DECN-{uuid.uuid4().hex[:8].upper()}"


def log_decision(
    function: str,
    input_summary: Dict[str, Any],
    output: Any,
    reason: str,
    request_id: Optional[str] = None,
    story_id: Optional[str] = None,
) -> str:
    """Log a business decision with a unique ID. Returns the decision_id.

    If request_id is not provided, auto-reads from structlog contextvars
    (set by MetricsMiddleware for every HTTP request).
    story_id is optional — set by contextvars when running within a BMAD Story scope.
    """
    if request_id is None:
        ctx = structlog.contextvars.get_contextvars()
        request_id = ctx.get("request_id", "unknown")

    if story_id is None:
        ctx = structlog.contextvars.get_contextvars()
        story_id = ctx.get("current_story_id")

    decision_id = generate_decision_id()
    extra = {
        "decision_id": decision_id,
        "function": function,
        "input": json.dumps(input_summary, default=str),
        "output": str(output),
        "reason": reason,
        "request_id": request_id,
    }
    if story_id:
        extra["story_id"] = story_id
    logger.info("decision_recorded", extra=extra)
    return decision_id


# =============================================================================
# CARD-G4-3 (BATCH-2026-08-31-第七批) — trace 面与统一四态枚举对齐
# =============================================================================

#: 需要落 trace 的状态。ok/empty 是正常流量, 落进决策日志只会把真正的故障淹掉。
#: 值从枚举派生而非硬编字符串 —— 本卡的正事就是消灭词汇分裂, 这里再抄一遍
#: 字面量就是给未来留一处会悄悄失配的副本。
#: 依赖方向安全性 (2026-08-31 实查): 导入子模块会执行 ``app/models/__init__.py``,
#: 但 ``app/models/*.py`` **零** ``from app.<非models>`` 导入 —— 该包是叶子,
#: core → models 单向, 不可能成环。两种导入顺序均已实测通过。
_TRACEABLE_FAULT_STATES = frozenset({ServiceStatus.DEGRADED.value, ServiceStatus.UNAVAILABLE.value})


def log_retrieval_status_decision(
    *,
    function: str,
    status: Any,
    reason: Optional[str],
    input_summary: Dict[str, Any],
) -> Optional[str]:
    """检索四态的 trace 单点入口 — 仅故障态落账, output 恒为枚举 **value**。

    存在的理由是**一个会静默产生错值的坑**: ``log_decision`` 内部做
    ``str(output)``, 而 ``class ServiceStatus(str, Enum)`` 的 ``__str__``
    继承自 ``Enum``, 返回 ``'ServiceStatus.DEGRADED'`` 而非 ``'degraded'``
    (只有 3.11+ 的 ``StrEnum`` 才返回 value)。传错不会报错, 只会让 trace 里
    多出一个不在统一值域内的字符串, 使后续按状态聚合的查询全部落空。

    把归一收在这一个函数里, 是为了避免"每个端点各写一遍、其中一处忘了
    ``.value``"这种只能靠人眼发现的分歧。

    Args:
        function: 决策点名称 (端点级, 如 ``"memory.get_learning_history"``)。
        status: 四态值 —— ``ServiceStatus`` 枚举或其 value 字符串, 或 None
            (表示本次未产出状态, 不落账)。
        reason: 故障说明。G4-2 契约规定 degraded/unavailable 必带 reason;
            缺失时**不静默补漂亮话**, 而是把"没给理由"本身记进 trace。
        input_summary: 决策输入摘要。

    Returns:
        decision_id (落账时) 或 None (正常态 / 无状态, 未落账)。
    """
    if status is None:
        return None

    # 枚举 → value; 裸字符串原样。刻意不用 ServiceStatus(status) 强转: 观测
    # 代码不该成为新的失败源。越界脏值在这里只是"不落账", 该由响应模型的
    # 枚举值域去拦 (它会让请求 5xx —— 见 test_out_of_domain_status_fails_loud)。
    # 换言之, 拦截的职责在 schema, 这里只负责不把脏值写进 trace。
    normalized = getattr(status, "value", status)
    if not isinstance(normalized, str):
        normalized = str(normalized)

    if normalized not in _TRACEABLE_FAULT_STATES:
        return None

    # ── fail-open: 观测面不得成为业务面的失败源 ──────────────────────────
    # 本函数在四个端点的 return 之前被同步调用, 而那些调用点都裹在
    # ``try/except Exception -> HTTP 500`` 里。若落账抛异常 (日志后端故障、
    # handler 配置错误、input_summary 不可序列化…), 一次**本该 200 的降级
    # 响应**会变成 500, 而且异常还会被外层的 except 误报成
    # "Failed to query learning history: <落账的错>" —— 谎称了失败原因。
    # 实测 (2026-08-31): patch log_decision 抛错 → /memory/episodes 返回
    # 500 且 detail 写着查询失败, 但查询其实成功了。
    # 这里吞掉异常并降级到本模块 logger, 保证「记不下这条 trace」最多损失
    # 可观测性, 不损失响应。
    try:
        return log_decision(
            function=function,
            input_summary=input_summary,
            output=normalized,
            reason=reason or f"retrieval_status={normalized} reported without reason",
        )
    except Exception:  # noqa: BLE001 — 观测面刻意兜底, 见上
        try:
            logger.exception(
                "retrieval status decision logging failed (fail-open); function=%s status=%s",
                function,
                normalized,
            )
        except Exception:  # noqa: BLE001
            # 兜底的兜底: 若 logging 后端本身就是坏的, 上面这行同样会抛。
            # 观测彻底失效仍不得波及业务响应 —— 这是本函数的唯一硬要求。
            pass
        return None
