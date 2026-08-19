"""P1-05b SnapshotV3 — 磁盘快照的 allowlist 严格模型 (extra="forbid")。

分层 (为什么与 serve 视图模型分离):
  - 本模块 (SnapshotV3*):  磁盘读写层。extra="forbid" — 任何新增字段必须显式
    声明, 杜绝 scan_vault superset 静默落盘 (v1 未脱敏事故的结构性根除:
    denylist pop 三键挡不住**下一个**新增字段)。
  - models/board_manifest.py (ExamNodeEntry/StudyNodeEntry): API serve 层,
    extra="ignore" **保持不动** — 那正是 exam 泄漏控制的当前机制 (superset
    里的禁项被结构性丢弃, board_manifest.py:7)。直接改 forbid 会让 serve
    路径传 superset 立刻 ValidationError。

读写共用同一 validator (P1-01 验收门):
  写: project_full_state(full) — 从 scan_vault full state **显式逐字段提取**
      → 模型校验 → dict。未声明字段结构上进不了磁盘。
  读: SnapshotV3.model_validate(data) → to_full_state() 还原 _carve 期望的
      内部形状 (被删字段以安全默认补位)。多余字段 / 错型 / 未来版本 →
      ValidationError → 调用方一律按 cache miss。

字段裁决 (用户 2026-08-19 裁定):
  保留  node_id/board_id (严格校验) · 枚举/布尔/时区时间 ·
        mastery{source,a,b,score} · attempt_count · last_examined (pick 重算
        枢轴) · relation.target_node_id · source_note (已 resolve_node_id
        归一) · parse_errors[].error_code (Literal) · orphans[].reason
        (Literal) · capabilities.history_text=false
  新增  pick_eligible: bool — ⛔ 投毒节点 (inf/nan mastery) 在快照里与"真的
        从未评估"长得一模一样 (都是 source=="absent"), 唯一区别是运行态的
        pick_hint is None。天真重算会让投毒节点复活竞秩 (违反 RAG-S2.6
        HIGH-2)。显式携带资格位, 读侧重算以它为门。
  删除  title · aliases · past_question_digests[].digest ·
        relation.derived_reason · orphans[].source_board_raw · pick_hint 整个
        (读时用 6 字段重算) · created_at/created_from/next_review/
        calibration_count · parse_errors[].error 自由文本
"""

from __future__ import annotations

import math
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SNAPSHOT_V3_VERSION = 3

#: parse_errors 的机器码 (快照不保留自由文本 error)
ParseErrorCode = Literal[
    "file_parse_failed",
    "mastery_invalid",
    "last_examined_invalid",
    "pick_hint_failed",
    "unknown",
]

#: error_code → 降级态 serve 的定长文案 (ParseErrorOut.error 必填, 需合成)
ERROR_CODE_TEXT: dict[str, str] = {
    "file_parse_failed": "文件解析失败 (快照降级态, 原始详情不保留)",
    "mastery_invalid": "mastery 字段无效 (非有限数值或非正), 按未评估处理",
    "last_examined_invalid": "last_examined 无法解析, 按从未考",
    "pick_hint_failed": "pick_hint 计算失败",
    "unknown": "解析错误 (快照降级态, 原始详情不保留)",
}

OrphanReason = Literal["no_source_board", "unknown_board"]

#: scan_vault 的定长中文文案 ↔ 快照 slug (读侧还原成与 live 相同的文案)
ORPHAN_REASON_TEXT: dict[str, str] = {
    "no_source_board": "无 source_board",
    "unknown_board": "source_board 指向不存在的白板",
}
_ORPHAN_TEXT_TO_SLUG = {v: k for k, v in ORPHAN_REASON_TEXT.items()}


def _require_finite(v: Optional[float]) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise ValueError("必须是有限数值或 null")
    return float(v)


#: ID 语义字段 (node_id/board_id/exam_board_id/概念名 = 文件 stem) 的上限。
#: APFS 文件名 ≤255 bytes (中文 ~85 字), 200 字对真实 stem 永不触发 —
#: 触发即伪造/损坏, **拒绝而非截断** (截断会让 ID 指向另一个实体, F-06)。
_ID_MAX = 200


def _require_id_like(v: Optional[str]) -> Optional[str]:
    """ID 类字段校验 (P1-05c, Codex 三轮 F-06): 拒路径分隔/控制字符/../超长。"""
    if v is None:
        return None
    if not v or len(v) > _ID_MAX:
        raise ValueError("ID 为空或超长")
    # P1-05d (Codex 四轮 V5): 控制字符全拒 (<0x20 含 tab 与 0x7f), 不再逐个点名
    if any(ch in ("/", "\\") or ord(ch) < 0x20 or ord(ch) == 0x7F for ch in v) or v in (".", ".."):
        raise ValueError("ID 含路径分隔/控制字符")
    return v


def _id_ok(v: object) -> bool:
    """写侧过滤判定 — 与读侧 _require_id_like **同源** (P1-05d V5):
    非法 ID (超长/控制字符/路径分隔) 的条目在投影时丢弃, 而不是让整包
    ValidationError 写失败 (201 字 ASCII stem 在 APFS 合法, 曾杀整个降级缓存)。"""
    try:
        _require_id_like(str(v))
        return True
    except ValueError:
        return False


def _require_iso_or_none(v: Optional[str]) -> Optional[str]:
    """时间字段必须可被 fromisoformat 解析 (拒 'not-a-time' 类伪造, F-06)。"""
    if v is None:
        return None
    from datetime import datetime as _dt

    try:
        _dt.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError as e:
        raise ValueError(f"非法 ISO 时间: {e}") from e
    return v


class _Forbid(BaseModel):
    # P1-05c (F-06): strict=True 杀 pydantic lax 强转 — "yes"→True / "2"→2 /
    # "3.0"→3.0 等静默类型改写全部拒绝; forbid 只挡多余键, 挡不住错型值。
    model_config = ConfigDict(extra="forbid", strict=True)


class SnapshotV3Mastery(_Forbid):
    source: Literal["beta", "score_only", "legacy_v2", "absent"]
    score: Optional[float] = None
    a: Optional[float] = None
    b: Optional[float] = None

    _finite = field_validator("score", "a", "b")(classmethod(lambda cls, v: _require_finite(v)))


class SnapshotV3Relation(_Forbid):
    type: str = Field(min_length=1, max_length=60)
    target_node_id: Optional[str] = Field(default=None, max_length=200)
    derived_at: Optional[str] = Field(default=None, max_length=64)
    # derived_reason 已删除 (自由文本不落盘)

    _id = field_validator("target_node_id")(classmethod(lambda cls, v: _require_id_like(v)))
    _t = field_validator("derived_at")(classmethod(lambda cls, v: _require_iso_or_none(v)))


class SnapshotV3Digest(_Forbid):
    exam_board_id: str = Field(min_length=1, max_length=200)
    qid: Optional[str] = Field(default=None, max_length=40)
    asked_at: Optional[str] = Field(default=None, max_length=64)
    score: Optional[float] = None
    score_scale: Optional[str] = Field(default=None, max_length=40)
    self_confidence: Optional[str] = Field(default=None, max_length=40)
    # digest 已删除 — capabilities.history_text=false 显式申报

    _finite = field_validator("score")(classmethod(lambda cls, v: _require_finite(v)))
    _id = field_validator("exam_board_id", "qid")(classmethod(lambda cls, v: _require_id_like(v)))
    _t = field_validator("asked_at")(classmethod(lambda cls, v: _require_iso_or_none(v)))


class SnapshotV3Member(_Forbid):
    node_id: str = Field(min_length=1, max_length=200)
    exists: bool
    role: Literal["seed", "derived", "unknown"]
    is_stub: bool
    #: ⛔ 必填无默认 — 投毒节点 (inf/nan mastery) 不得在快照往返后复活竞秩
    pick_eligible: bool
    relation: Optional[SnapshotV3Relation] = None
    mastery: SnapshotV3Mastery
    attempt_count: Optional[int] = Field(default=None, ge=0)
    last_examined: Optional[str] = Field(default=None, max_length=64)
    source_note: Optional[str] = Field(default=None, max_length=200)
    past_question_digests: list[SnapshotV3Digest] = Field(default_factory=list, max_length=500)

    _id = field_validator("node_id", "source_note")(classmethod(lambda cls, v: _require_id_like(v)))
    _t = field_validator("last_examined")(classmethod(lambda cls, v: _require_iso_or_none(v)))


class SnapshotV3Board(_Forbid):
    board_id: str = Field(min_length=1, max_length=200)
    board_name: str = Field(max_length=120)
    board_name_mismatch: bool
    doc_count_declared: Optional[int] = None
    concepts_listed: list[str] = Field(default_factory=list, max_length=2000)
    members: list[SnapshotV3Member] = Field(default_factory=list, max_length=5000)

    _id = field_validator("board_id")(classmethod(lambda cls, v: _require_id_like(v)))

    @field_validator("concepts_listed")
    @classmethod
    def _concepts_are_ids(cls, v: list[str]) -> list[str]:
        # P1-05c (F-06): 拒绝而非截断 — 201 字 concept 曾被静默截成 200 字,
        # dual_source_gap 拿截断值比对把真实存在的 node 误判 exists=false。
        # 写侧 (project_full_state) 已过滤超长项; 读到超长 = 伪造/损坏 → 拒。
        for x in v:
            _require_id_like(x)
        return v


class SnapshotV3Orphan(_Forbid):
    node_id: str = Field(min_length=1, max_length=200)
    reason: OrphanReason
    # source_board_raw 已删除 (untrusted 自由文本不落盘)

    _id = field_validator("node_id")(classmethod(lambda cls, v: _require_id_like(v)))


class SnapshotV3ExamHistory(_Forbid):
    exam_board_id: str = Field(min_length=1, max_length=200)
    board_id: Optional[str] = Field(default=None, max_length=200)
    created_at: Optional[str] = Field(default=None, max_length=64)
    status: Optional[str] = Field(default=None, max_length=40)
    selected_node: Optional[str] = Field(default=None, max_length=200)
    question_count: int = Field(ge=0)

    _id = field_validator("exam_board_id", "board_id", "selected_node")(classmethod(lambda cls, v: _require_id_like(v)))
    _t = field_validator("created_at")(classmethod(lambda cls, v: _require_iso_or_none(v)))


class SnapshotV3ParseError(_Forbid):
    path: str = Field(max_length=200)
    error_code: ParseErrorCode
    # error 自由文本已删除 — 读侧从 error_code 合成定长文案


class SnapshotV3Freshness(_Forbid):
    generated_at: str = Field(min_length=1, max_length=64)
    generation: str = Field(pattern=r"^[0-9a-f]{12}$")
    lag_seconds: Optional[float] = None
    stale: bool = False

    # P1-05d (V5): NaN/±inf 会让 json.dumps 吐非标字面量 — finite 或 None
    _fin = field_validator("lag_seconds")(classmethod(lambda cls, v: _require_finite(v)))

    _t = field_validator("generated_at")(classmethod(lambda cls, v: _require_iso_or_none(v)))


class SnapshotV3Capabilities(_Forbid):
    #: 快照不保留历史题面摘句原文 (digest) — 消费侧据此得知降级态无 history 文本
    history_text: Literal[False] = False


class SnapshotV3(_Forbid):
    snapshot_schema_version: Literal[3]
    capabilities: SnapshotV3Capabilities = Field(default_factory=SnapshotV3Capabilities)
    freshness: SnapshotV3Freshness
    boards: dict[str, SnapshotV3Board] = Field(max_length=500)
    node_stems: list[str] = Field(default_factory=list, max_length=20000)
    orphans: list[SnapshotV3Orphan] = Field(default_factory=list, max_length=5000)
    exam_history: list[SnapshotV3ExamHistory] = Field(default_factory=list, max_length=5000)
    parse_errors: list[SnapshotV3ParseError] = Field(default_factory=list, max_length=5000)

    @field_validator("node_stems")
    @classmethod
    def _stems_are_ids(cls, v: list[str]) -> list[str]:
        # P1-05c (F-06): node_stems 曾接受 10000 字+换行的项 — 逐项 ID 校验
        for x in v:
            _require_id_like(x)
        return v

    @model_validator(mode="after")
    def _board_keys_match(self) -> "SnapshotV3":
        # P1-05c (F-06 实锤): boards={"outer": {board_id:"inner"}} 曾可加载 —
        # _carve 按 key 查、按内容 serve, 请求 outer 得 inner / 请求 inner 404
        for key, board in self.boards.items():
            if key != board.board_id:
                raise ValueError(f"boards key {key!r} != board_id {board.board_id!r}")
        return self

    @field_validator("snapshot_schema_version", mode="before")
    @classmethod
    def _version_strict_int(cls, v: Any) -> Any:
        # ⛔ type(v) is int 且 == 3: 拒绝 "3" / 3.0 / True / None / dict / list。
        # bool 是 int 子类, Literal[3] 不挡 True==... (True != 3, 但显式更稳)
        if type(v) is not int or v != SNAPSHOT_V3_VERSION:
            raise ValueError(f"snapshot_schema_version 必须是 int {SNAPSHOT_V3_VERSION}, got {v!r}")
        return v

    # ── 读侧: 还原 _carve 期望的内部 full-state 形状 ──────────────────────
    def to_full_state(self) -> dict[str, Any]:
        """被删字段以安全默认补位: pick_hint=None (读侧重算) / tips 等空列表 /
        parse_errors.error 与 orphans.reason 从机器码合成定长文案。"""
        boards: dict[str, Any] = {}
        for bid, board in self.boards.items():
            members = []
            for m in board.members:
                members.append(
                    {
                        "node_id": m.node_id,
                        "exists": m.exists,
                        "role": m.role,
                        "is_stub": m.is_stub,
                        "pick_eligible": m.pick_eligible,
                        "relation": (
                            {
                                "type": m.relation.type,
                                "target_node_id": m.relation.target_node_id,
                                "derived_reason": None,
                                "derived_at": m.relation.derived_at,
                            }
                            if m.relation is not None
                            else None
                        ),
                        "mastery": m.mastery.model_dump(),
                        "attempt_count": m.attempt_count,
                        "last_examined": m.last_examined,
                        "pick_hint": None,  # 恒由 _carve 以请求级 now 重算
                        "past_question_digests": [{**d.model_dump(), "digest": None} for d in m.past_question_digests],
                        # study-only 字段的安全默认 (v3 不保留)
                        "title": None,
                        "aliases": [],
                        "created_at": None,
                        "created_from": None,
                        "source_note": m.source_note,
                        "tips": [],
                        "errors": [],
                        "error_candidates": [],
                        "next_review": None,
                        "calibration_count": 0,
                    }
                )
            boards[bid] = {
                "board_id": board.board_id,
                "board_name": board.board_name,
                "board_name_mismatch": board.board_name_mismatch,
                "doc_count_declared": board.doc_count_declared,
                "concepts_listed": list(board.concepts_listed),
                "members": members,
            }
        return {
            "snapshot_schema_version": self.snapshot_schema_version,
            "capabilities": self.capabilities.model_dump(),
            "freshness": self.freshness.model_dump(),
            "boards": boards,
            "node_stems": list(self.node_stems),
            "orphans": [
                {
                    "node_id": o.node_id,
                    "reason": ORPHAN_REASON_TEXT[o.reason],
                    "reason_code": o.reason,
                    "source_board_raw": None,
                }
                for o in self.orphans
            ],
            "exam_history": [e.model_dump() for e in self.exam_history],
            "parse_errors": [
                {"path": p.path, "error": ERROR_CODE_TEXT[p.error_code], "error_code": p.error_code}
                for p in self.parse_errors
            ],
        }


# ── 写侧: 从 scan_vault full state 显式逐字段提取 (allowlist 投影) ──────────


def _member_from_full(m: dict[str, Any]) -> dict[str, Any]:
    relation = m.get("relation")
    rel_out = None
    if isinstance(relation, dict) and relation.get("type"):
        # ID 语义不截断 (截断会指向另一实体, F-06) — 超长 target = 非法引用,
        # 丢弃 relation 而非让整份快照写失败
        _tgt = str(relation["target_node_id"]) if relation.get("target_node_id") else None
        if _tgt and len(_tgt) > _ID_MAX:
            _tgt = None
        rel_out = {
            "type": str(relation["type"])[:60],
            "target_node_id": _tgt,
            "derived_at": (str(relation["derived_at"])[:64] if relation.get("derived_at") else None),
        }
    mastery = m.get("mastery") or {}
    digests = []
    for d in m.get("past_question_digests") or []:
        if not isinstance(d, dict) or not d.get("exam_board_id"):
            continue
        if len(str(d["exam_board_id"])) > _ID_MAX:
            continue  # ID 不截断 — 超长即丢弃该条 (F-06)
        digests.append(
            {
                "exam_board_id": str(d["exam_board_id"]),
                # P1-05d (V5): ID 语义一律"超长丢弃不切片" — 切片值是另一个 ID
                "qid": (str(d["qid"]) if d.get("qid") and len(str(d["qid"])) <= 40 else None),
                "asked_at": (str(d["asked_at"])[:64] if d.get("asked_at") else None),
                "score": d.get("score"),
                "score_scale": (str(d["score_scale"])[:40] if d.get("score_scale") else None),
                "self_confidence": (str(d["self_confidence"])[:40] if d.get("self_confidence") else None),
            }
        )
    attempt = m.get("attempt_count")
    return {
        "node_id": m["node_id"],
        "exists": bool(m.get("exists", True)),
        "role": m.get("role") if m.get("role") in ("seed", "derived", "unknown") else "unknown",
        "is_stub": bool(m.get("is_stub", False)),
        # 旧形态 full state (无 pick_eligible 字段) 的等价信号是"scan 算出过
        # 非空 hint" — P1-05c (F-06): 旧写法 `is not None` 会把 pick_hint={}
        # 误判 eligible (生产不可达但防御收紧: 空 dict 不是有效 hint)
        "pick_eligible": bool(
            m["pick_eligible"]
            if "pick_eligible" in m
            else (isinstance(m.get("pick_hint"), dict) and bool(m.get("pick_hint")))
        ),
        "relation": rel_out,
        "mastery": {
            "source": mastery.get("source", "absent"),
            "score": mastery.get("score"),
            "a": mastery.get("a"),
            "b": mastery.get("b"),
        },
        "attempt_count": (int(attempt) if isinstance(attempt, (int, float)) and attempt >= 0 else None),
        "last_examined": (str(m["last_examined"])[:64] if m.get("last_examined") else None),
        "source_note": (
            str(m["source_note"]) if m.get("source_note") and len(str(m["source_note"])) <= _ID_MAX else None
        ),
        "past_question_digests": digests,
    }


def project_full_state(full: dict[str, Any]) -> SnapshotV3:
    """scan_vault full state → SnapshotV3 模型 (写盘前的唯一投影点)。

    抛 pydantic.ValidationError = 拒写 (write_snapshot_if_changed 捕获为
    warning, 不影响 live)。不修改入参 (live 与快照共用同一 state 契约)。
    """
    boards_out: dict[str, Any] = {}
    for bid, board in (full.get("boards") or {}).items():
        if not isinstance(board, dict) or not _id_ok(bid):
            continue  # P1-05d (V5): 非法 board key 丢 board, 不让整包写失败
        boards_out[str(bid)] = {
            # board_id 恒用 dict key — 模型 _board_keys_match 强制 key 一致 (F-06)
            "board_id": str(bid),
            "board_name": str(board.get("board_name") or bid)[:120],
            "board_name_mismatch": bool(board.get("board_name_mismatch", False)),
            "doc_count_declared": board.get("doc_count_declared"),
            # ID 语义超长项**过滤**而非截断 (截断值会在 dual_source_gap 比对时
            # 把真实存在的 node 误判 exists=false, F-06 实锤)
            "concepts_listed": [str(c) for c in board.get("concepts_listed") or [] if _id_ok(c)],
            "members": [
                _member_from_full(m)
                for m in board.get("members") or []
                if isinstance(m, dict) and _id_ok(m.get("node_id"))
            ],
        }
    orphans_out = []
    for o in full.get("orphans") or []:
        if not isinstance(o, dict) or not _id_ok(o.get("node_id")):
            continue
        slug = o.get("reason_code") or _ORPHAN_TEXT_TO_SLUG.get(str(o.get("reason") or ""))
        if slug not in ("no_source_board", "unknown_board"):
            continue  # 无法归码的孤儿不落盘 (真实 scan 只产两类, 此处防御合成态)
        orphans_out.append({"node_id": o["node_id"], "reason": slug})
    parse_errors_out = []
    for p in full.get("parse_errors") or []:
        if not isinstance(p, dict):
            continue
        code = p.get("error_code")
        if code not in ERROR_CODE_TEXT:
            code = "unknown"
        parse_errors_out.append({"path": str(p.get("path") or "")[:200], "error_code": code})
    exam_out = []
    for e in full.get("exam_history") or []:
        if not isinstance(e, dict) or not e.get("exam_board_id"):
            continue
        if len(str(e["exam_board_id"])) > _ID_MAX:
            continue  # P1-05d (V5): ID 超长丢条目, 不切片
        exam_out.append(
            {
                "exam_board_id": str(e["exam_board_id"]),
                "board_id": (str(e["board_id"]) if e.get("board_id") and len(str(e["board_id"])) <= _ID_MAX else None),
                "created_at": (str(e["created_at"])[:64] if e.get("created_at") else None),
                "status": (str(e["status"])[:40] if e.get("status") else None),
                "selected_node": (
                    str(e["selected_node"])
                    if e.get("selected_node") and len(str(e["selected_node"])) <= _ID_MAX
                    else None
                ),
                "question_count": max(0, int(e.get("question_count") or 0)),
            }
        )
    return SnapshotV3.model_validate(
        {
            "snapshot_schema_version": SNAPSHOT_V3_VERSION,
            "capabilities": {"history_text": False},
            "freshness": {
                "generated_at": str((full.get("freshness") or {}).get("generated_at") or "")[:64],
                "generation": str((full.get("freshness") or {}).get("generation") or ""),
                "lag_seconds": (full.get("freshness") or {}).get("lag_seconds"),
                "stale": bool((full.get("freshness") or {}).get("stale", False)),
            },
            "boards": boards_out,
            "node_stems": [str(s) for s in full.get("node_stems") or [] if _id_ok(s)],
            "orphans": orphans_out,
            "exam_history": exam_out,
            "parse_errors": parse_errors_out,
        }
    )
