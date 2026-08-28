"""统一服务四态状态类型 — CARD-G4-2 (BATCH-2026-08-28-第五批).

问题 (计划书 :290 P1-03/04 + :125 §3.3): Neo4j/LanceDB/Graphiti 故障在
service 层被静默降为空列表 — 调用方无法区分「真没有数据」和「存储挂了」,
故障假装空结果。本模块定义全后端统一的 ok/empty/degraded/unavailable
四态 (复用 C2/D1 总览页四态徽标语义先例), 贯穿 MemoryService 读路径、
rag_service 与 CanvasRAGState。

四态语义 (值域契约, 由 ``StatusedResult`` 构造校验强制):

- ``ok``          — 服务正常, 有结果。reason 必须为 None。
- ``empty``       — 服务正常, 真空结果 (查询成功但命中 0)。reason 必须为 None
                    (「空」是数据事实, 不是故障, 不需要理由)。
- ``degraded``    — 部分源失败但仍有兜底/部分结果 (如 Graphiti 挂了走
                    Neo4j fulltext / 内存缓存)。必须带非空 reason。
- ``unavailable`` — 服务不可达/全部源失败, 结果不可信 (不是空!)。
                    必须带非空 reason。

兼容铁律 (卡文记录):

- ``search_memories`` 保 list 契约 (~12 处直接迭代) — 采用「新状态方法 +
  旧方法委托」形态: ``search_memories_with_status()`` 返回本包装,
  旧 ``search_memories()`` 委托新方法并返回 ``.items``。
- ``ScoreHistoryResponse`` 只加带默认值的可选字段 (status/status_reason)。
- ``LearningMemoryClient`` 对外契约冻结, 其四态化列 followup。

``CanvasRAGState.retrieval_status`` 用 Literal 镜像本枚举 —
``RETRIEVAL_STATUS_VALUES`` 是两侧值域一致性契约测试的锚点
(tests/unit/test_service_status_contract.py)。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class ServiceStatus(str, Enum):
    """统一四态 — str 枚举, 可直接 JSON 序列化/与 Literal 镜像比较。"""

    OK = "ok"
    EMPTY = "empty"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


#: Literal 镜像与契约测试的权威值域 (顺序即语义严重度递增)。
SERVICE_STATUS_VALUES: tuple = ("ok", "empty", "degraded", "unavailable")

#: 必须携带非空 reason 的状态。
_REASON_REQUIRED = frozenset({ServiceStatus.DEGRADED, ServiceStatus.UNAVAILABLE})


@dataclass(frozen=True)
class StatusedResult:
    """带状态的结果包装 — service 层读路径的统一返回结构。

    Attributes:
        status: 四态之一。
        items: 结果载荷 (list; unavailable 时恒为空 list — 空载荷是
            「不可信」而非「无数据」, 由 status 区分)。
        reason: 故障说明 — degraded/unavailable 必填, ok/empty 禁止。

    构造即校验 (值域契约): 违反 reason 规则直接 ValueError, 让「带 reason
    的 empty」或「无 reason 的 unavailable」在写代码时就炸, 不进生产。
    """

    status: ServiceStatus
    items: List[Any] = field(default_factory=list)
    reason: Optional[str] = None

    def __post_init__(self) -> None:
        status = ServiceStatus(self.status)  # 兼容裸 str 传入
        object.__setattr__(self, "status", status)

        # ── reason 不变量 ────────────────────────────────────────────
        if status in _REASON_REQUIRED:
            if not isinstance(self.reason, str) or not self.reason.strip():
                raise ValueError(
                    f"ServiceStatus.{status.name} requires a non-empty str reason "
                    "(G4-2 值域契约: 故障必须给出诊断信息)"
                )
        else:
            if self.reason is not None:
                raise ValueError(
                    f"ServiceStatus.{status.name} must not carry a reason "
                    "(G4-2 值域契约: ok/empty 不是故障态)"
                )

        # ── 载荷不变量 (Codex round-1 MEDIUM-12) ─────────────────────
        # 状态与载荷必须自洽, 否则「ok 却空手」「empty 却有货」这类矛盾
        # 会让消费方两边都不敢信。
        if not isinstance(self.items, list):
            raise TypeError(
                f"StatusedResult.items must be a list, got {type(self.items).__name__}"
            )
        # 冻结载荷: frozen=True 挡不住 items.append(), 复制成新 list 隔断
        # 外部引用, 避免构造后被旁路修改破坏不变量。
        object.__setattr__(self, "items", list(self.items))

        if status is ServiceStatus.OK and not self.items:
            raise ValueError("ServiceStatus.OK requires a non-empty items payload")
        if status is ServiceStatus.EMPTY and self.items:
            raise ValueError("ServiceStatus.EMPTY must carry an empty items payload")
        if status is ServiceStatus.UNAVAILABLE and self.items:
            raise ValueError(
                "ServiceStatus.UNAVAILABLE must carry an empty items payload "
                "(载荷不可信, 不得夹带部分结果 — 部分结果请用 DEGRADED)"
            )

    # ── 工厂方法 (推荐入口, 杜绝手写状态判断分歧) ──────────────────────

    @classmethod
    def from_items(cls, items: List[Any]) -> "StatusedResult":
        """成功路径统一入口: 有结果 → ok, 真空 → empty。

        MEDIUM-12: 拒绝 None —— None 通常意味着「调用失败」而非「空结果」,
        把它当成可信的 EMPTY 正是本卡要消灭的伪装。
        """
        if items is None:
            raise ValueError(
                "from_items(None) is ambiguous — 用 unavailable()/degraded() "
                "表达故障, 用 from_items([]) 表达真空"
            )
        return cls(
            status=ServiceStatus.OK if items else ServiceStatus.EMPTY,
            items=list(items),
        )

    @classmethod
    def degraded(cls, items: Optional[List[Any]], reason: str) -> "StatusedResult":
        """部分源失败但有兜底结果。"""
        return cls(status=ServiceStatus.DEGRADED, items=items or [], reason=reason)

    @classmethod
    def unavailable(cls, reason: str) -> "StatusedResult":
        """服务不可达 — 载荷恒空, 且这个空不可信。"""
        return cls(status=ServiceStatus.UNAVAILABLE, items=[], reason=reason)

    # ── 便捷谓词 ──────────────────────────────────────────────────────

    @property
    def is_trustworthy(self) -> bool:
        """结果载荷是否可信 (ok/empty/degraded 可用, unavailable 不可用)。"""
        return self.status is not ServiceStatus.UNAVAILABLE

    def to_dict(self) -> dict:
        """JSON 友好形态 (API/trace 面 G4-3 消费)。"""
        payload: dict = {"status": self.status.value, "items": self.items}
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


def max_severity(*statuses: ServiceStatus) -> ServiceStatus:
    """返回若干状态里**严重度最高**的一个 (ok < empty < degraded < unavailable)。

    ⚠️ 这是**组件级严重度排序**, 不是整体结果折算 (Codex round-1
    MEDIUM-15 更名): 按本函数, ``OK + UNAVAILABLE → UNAVAILABLE``,
    但若已经拿到了健康结果, 整体应当是 **DEGRADED** 而非 unavailable。
    整体折算请用 ``fold_overall_status()``。
    """
    if not statuses:
        raise ValueError("max_severity() requires at least one status")
    order = {s: i for i, s in enumerate(SERVICE_STATUS_VALUES)}
    # 先归一到枚举再取最值 — 否则传入裸 str 时返回值类型会跟着输入漂移
    normalized = [ServiceStatus(s) for s in statuses]
    return max(normalized, key=lambda s: order[s.value])


def fold_overall_status(
    *, has_results: bool, failed_sources: int, healthy_sources: int
) -> ServiceStatus:
    """把「各源成败 + 有无结果」折算成整体四态 (Codex round-1 MEDIUM-15)。

    规则 (与 memory_service / fuse_results 的手写折算同口径):

    - 有失败 且 无结果 且 无健康源 → ``unavailable`` (这个空不可信)
    - 有失败 (但有结果 或 还有健康源) → ``degraded`` (部分面)
    - 无失败 且 有结果 → ``ok``
    - 无失败 且 无结果 → ``empty`` (真空是数据事实)

    Args:
        has_results: 是否拿到了任何可用结果 (含兜底层)。
        failed_sources: 失败的数据源数量。
        healthy_sources: 确认健康 (已尝试且未失败) 的数据源数量。
    """
    if failed_sources:
        if not has_results and healthy_sources == 0:
            return ServiceStatus.UNAVAILABLE
        return ServiceStatus.DEGRADED
    return ServiceStatus.OK if has_results else ServiceStatus.EMPTY
