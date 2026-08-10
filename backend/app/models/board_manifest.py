"""RAG-S2.5 (2026-08-10): Board Manifest 双视图 Pydantic 投影 — 唯一泄漏控制点。

exam 视图禁项 = **模型结构性缺字段** (白名单投影, 非黑名单过滤):
tips / errors / error_candidates / misconception / correction /
raw_dialog_excerpt / evidence_turns / ai_reason / title / aliases /
source_note / body / calibration_log 这些键名在 ExamNodeEntry 上不存在,
extra="ignore" 使 service superset dict 里的它们被结构性丢弃。
misconception 同样不进 exam (targeting-material 已承载, 不重复建泄漏面)。

live 与快照两条 serve 路径都必须经 project_manifest() — 控制点唯一
(HARD-ISO 信息隔离铁律, 检验白板 v1 审计 A5-7 同源)。

exam 白名单自由文本槽位只有两个, 都带硬截断:
  relation.derived_reason ≤500 字 (用户派生原因, untrusted)
  past_question_digests[].digest ≤160 字 (已曝光题面摘句)
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.services.board_manifest_service import ANNOTATION_TRUST


class RelationOut(BaseModel):
    """派生边 (relationships[0] 或 derived-from 归一)。"""

    model_config = ConfigDict(extra="ignore")

    type: str
    target_node_id: str | None = None
    derived_reason: str | None = Field(default=None, max_length=500)
    derived_at: str | None = None


class MasteryOut(BaseModel):
    """掌握度四态显式申报 (absent 即 score=null, 不编数)。"""

    model_config = ConfigDict(extra="ignore")

    score: float | None = None
    a: float | None = None
    b: float | None = None
    source: Literal["beta", "score_only", "legacy_v2", "absent"]


class PickHintOut(BaseModel):
    """选点提示 μ−σ (含闲置回升); 数值与 decay_beta.py 真相源 1e-9 等价。"""

    model_config = ConfigDict(extra="ignore")

    mu: float
    sigma: float
    pick_score: float
    days_idle: float | None = None


class QuestionDigestOut(BaseModel):
    """历史考题摘句 (题面已在考察时曝光, exam 视图可携带; ≤160 字硬截断)。"""

    model_config = ConfigDict(extra="ignore")

    exam_board_id: str
    qid: str | None = None
    asked_at: str | None = None
    score: float | None = None
    self_confidence: str | None = None
    digest: str | None = Field(default=None, max_length=160)


class ExamNodeEntry(BaseModel):
    """exam 视图节点白名单 — 出题上下文安全面。

    ⛔ 不得添加自由文本字段 (contract 组 D 逐键断言 + G6 禁串扫描把守)。
    """

    model_config = ConfigDict(extra="ignore")

    node_id: str
    exists: bool = True
    role: Literal["seed", "derived", "unknown"] = "unknown"
    is_stub: bool = False
    relation: RelationOut | None = None
    mastery: MasteryOut
    attempt_count: int | None = None
    last_examined: str | None = None
    pick_hint: PickHintOut | None = None
    past_question_digests: list[QuestionDigestOut] = Field(default_factory=list)


class StudyNodeEntry(ExamNodeEntry):
    """study 视图 = exam 全字段 + 学习面补充 (tips/纠错候选等)。

    study 视图也不返回节点正文 (内容是 read_note 的职责, manifest 只答结构)。
    """

    title: str | None = None
    aliases: list[str] = Field(default_factory=list)
    created_at: str | None = None
    created_from: str | None = None
    source_note: str | None = None
    tips: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    error_candidates: list[dict[str, Any]] = Field(default_factory=list)
    next_review: str | None = None
    calibration_count: int = 0


class FreshnessOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    generated_at: str
    generation: str
    lag_seconds: float | None = 0.0
    stale: bool = False


class BoardInfoOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    board_id: str
    board_name: str
    board_name_mismatch: bool = False
    doc_count_declared: int | None = None
    member_count_actual: int


class BoardSummaryOut(BoardInfoOut):
    exam_board_count: int = 0


class GapEntryOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    node_id: str
    exists: bool


class DualSourceGapOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    concepts_only: list[GapEntryOut] = Field(default_factory=list)
    frontmatter_only: list[str] = Field(default_factory=list)


class OrphanOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    node_id: str
    reason: str
    source_board_raw: str | None = None


class ExamHistoryOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    exam_board_id: str
    board_id: str | None = None
    created_at: str | None = None
    status: str | None = None
    selected_node: str | None = None
    question_count: int = 0


class ParseErrorOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    path: str
    error: str


class _ManifestEnvelope(BaseModel):
    """顶层诚实信号 (source/degraded/freshness/差集告警/孤儿/解析错误)。"""

    model_config = ConfigDict(extra="ignore")

    source: Literal["live", "local_json"]
    source_status: Literal["ok", "snapshot", "error"]
    freshness: FreshnessOut | None = None
    degraded: bool = False
    degraded_reason: str | None = None
    annotation_trust: Literal["untrusted_user_data"] = ANNOTATION_TRUST
    id_stability: str
    board: BoardInfoOut | None = None
    boards: list[BoardSummaryOut] | None = None
    orphans: list[OrphanOut] = Field(default_factory=list)
    dual_source_gap: DualSourceGapOut | None = None
    exam_history: list[ExamHistoryOut] = Field(default_factory=list)
    parse_errors: list[ParseErrorOut] = Field(default_factory=list)


class ExamManifestResponse(_ManifestEnvelope):
    view: Literal["exam"] = "exam"
    nodes: list[ExamNodeEntry] = Field(default_factory=list)


class StudyManifestResponse(_ManifestEnvelope):
    view: Literal["study"] = "study"
    nodes: list[StudyNodeEntry] = Field(default_factory=list)


BoardManifestResponse = StudyManifestResponse | ExamManifestResponse


def project_manifest(raw: dict[str, Any], view: str) -> StudyManifestResponse | ExamManifestResponse:
    """service 全量 dict → 视图投影。live 与快照 serve 都必须走这里 (控制点唯一)。"""
    if view == "exam":
        return ExamManifestResponse.model_validate({**raw, "view": "exam"})
    if view == "study":
        return StudyManifestResponse.model_validate({**raw, "view": "study"})
    raise ValueError(f"未知视图: {view!r} (只支持 study|exam)")
