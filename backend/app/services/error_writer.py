# Story 2.5 Task 4 — 错误双写 (frontmatter + Graphiti)
#
# AC #4: errors[] 数组追加到 frontmatter (双标签 D 方案: pedagogy + legacy)
#        + memory_service.record_knowledge_entity 写 Graphiti
# AC #6: Graphiti 失败 → frontmatter 仍成功 (本地优先) + structlog warning
#        + 自动重试 (3 次, 间隔 1s)
#
# [Source: _bmad-output/implementation-artifacts/epic-2/2-5-error-extraction-classification.md#Task 4]

from __future__ import annotations

import asyncio
import hashlib
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import structlog
import yaml

from app.services.error_classifier import ClassifiedError

# Story 2.5.X (D15 = C+) — write_error_dual mode 选项
WriteMode = Literal["candidate_only", "write_confirmed"]
CANDIDATE_INITIAL_STATUS = "pending"
CANDIDATE_SOURCE_AI = "ai_suggested"

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# 配置常量 (PRD AC #4 + #6)
# ═══════════════════════════════════════════════════════════════════════════════

GRAPHITI_TIMEOUT_S = 0.5  # 单次 record_knowledge_entity 超时 (Task 4.3)
GRAPHITI_MAX_RETRIES = 3  # 重试上限 (Task 4.4)
GRAPHITI_RETRY_INTERVAL_S = 1.0  # 重试间隔

# Story 2.5 P0 fix (ChatGPT 二轮审查 2026-05-04):
# per-file async lock 防并发 read-modify-write 丢数据.
# 多个 record_error 并发写同一个 .md 时 errors[] 不丢条.
_FILE_LOCKS: dict[str, asyncio.Lock] = {}


def _get_file_lock(file_path: str | Path) -> asyncio.Lock:
    """Per-file async lock (Story 2.5 P0 fix concurrency)."""
    key = str(Path(file_path).resolve())
    if key not in _FILE_LOCKS:
        _FILE_LOCKS[key] = asyncio.Lock()
    return _FILE_LOCKS[key]


def _make_dedupe_hash(error: ClassifiedError, node_id: str) -> str:
    """Story 2.5 HIGH#11 fix — error 去重 hash (ChatGPT 二轮审查).

    同 (pedagogy_type, description, node_id) 视为同一错误, 避免无限增长.
    """
    raw = f"{error.pedagogy_type.value}|{error.description}|{node_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════════════════════
# Story 2.5.X Task 1 — Candidate writer (C+ 渐进式确认)
# ═══════════════════════════════════════════════════════════════════════════════


def _make_candidate_record(
    error: ClassifiedError,
    *,
    node_id: str,
    session_id: str,
    group_id: str,
    candidate_id: str,
    dedupe_hash: str,
    now_iso: str,
    ai_reason: str | None = None,
    evidence_turns: list[int] | None = None,
    raw_dialog_excerpt: str | None = None,
) -> dict[str, Any]:
    """Story 2.5.X AC #1 — 构造 candidate dict (含 6 状态机初始值 pending)."""
    return {
        "id": candidate_id,
        "status": CANDIDATE_INITIAL_STATUS,
        "source": CANDIDATE_SOURCE_AI,
        "node_id": node_id,
        "session_id": session_id,
        "group_id": group_id,
        "candidate_dedupe_hash": dedupe_hash,
        "pedagogy_type": error.pedagogy_type.value,
        "legacy_type": error.legacy_type.value,
        "description": error.description,
        "context": error.context,
        "ai_reason": ai_reason,  # Task 5 LLM 升级后填
        "evidence_turns": evidence_turns or [],  # Task 5 LLM 升级后填
        "raw_dialog_excerpt": raw_dialog_excerpt,  # Task 5 透传后填
        "confidence": round(error.confidence, 3),
        "confidence_source": "llm",  # 当前 ErrorClassifier 已输出 confidence
        "sub_tags": list(error.sub_tags),
        "suggested_remedy_strategies": [r.value for r in error.pedagogy_remedies],
        "legacy_remedy": error.legacy_remedy.value,
        "created_at": now_iso,
        "last_seen_at": now_iso,
        "seen_count": 1,
        "seen_sessions": [session_id] if session_id else [],
        "status_changed_at": None,  # 状态变更时填 (AC #2)
        "status_changed_by": None,
    }


def write_candidate_to_frontmatter(
    file_path: str | Path,
    error: ClassifiedError,
    *,
    node_id: str,
    session_id: str = "",
    group_id: str = "",
    candidate_id: str | None = None,
    ai_reason: str | None = None,
    evidence_turns: list[int] | None = None,
    raw_dialog_excerpt: str | None = None,
) -> tuple[bool, str | None]:
    """Story 2.5.X Task 1 — 追加候选错误到 frontmatter `error_candidates[]` (原子写入).

    与 `write_error_to_frontmatter` 区别：
    - 写 `error_candidates[]` 而非 `errors[]` (双数组并存)
    - candidate.status = "pending" (6 状态机初始值, AC #2)
    - 不写 Graphiti (AC #1: candidate 阶段不进知识图谱)
    - 复用同一 dedupe_hash 算法 (不含 session_id, AC #3)
    - 重复同错误时更新 last_seen_at / seen_count / seen_sessions (不 append)

    Args:
        file_path: 节点 .md 路径
        error: ClassifiedError 双标签错误
        node_id: Canvas 节点 ID (用于 dedupe + metadata)
        session_id: 当前对话 session ID (Round-2 修正: 加 frontmatter 但不进 dedupe)
        group_id: vault namespace (Story 2.5.Y 前期占位, 当前可为 "")
        candidate_id: 可选 UUID, None 时自动生成
        ai_reason: AI 判错理由 (Task 5 升级 LLM 后传)
        evidence_turns: 触发轮次 (Task 5 升级 LLM 后传)
        raw_dialog_excerpt: 原始对话摘录 (Task 5 透传后传)

    Returns:
        (success, candidate_id) — 重复错误算成功 (返回 existing id).
    """
    p = Path(file_path)
    if not p.exists():
        logger.warning("candidate_writer.file_not_found", path=str(p))
        return False, None

    try:
        text = p.read_text(encoding="utf-8")
        fm_str, body = _split_frontmatter(text)

        fm_dict = yaml.safe_load(fm_str) if fm_str else {}
        if not isinstance(fm_dict, dict):
            fm_dict = {}

        candidates_list = fm_dict.get("error_candidates", [])
        if not isinstance(candidates_list, list):
            candidates_list = []

        # AC #3: dedupe hash 复用 errors[] 算法 (不含 session_id, 跨 session 同错应 update 不 append)
        dedupe_hash = _make_dedupe_hash(error, node_id)
        now_iso = datetime.now(timezone.utc).isoformat()

        existing_idx: int | None = None
        for i, rec in enumerate(candidates_list):
            if (
                isinstance(rec, dict)
                and rec.get("candidate_dedupe_hash") == dedupe_hash
                and rec.get("status") == CANDIDATE_INITIAL_STATUS  # 仅 pending 算重复
            ):
                existing_idx = i
                break

        if existing_idx is not None:
            # AC #3: 同错误重复 → 更新 last_seen_at / seen_count / seen_sessions / max(confidence)
            existing = candidates_list[existing_idx]
            existing["last_seen_at"] = now_iso
            existing["seen_count"] = int(existing.get("seen_count", 1)) + 1

            existing_sessions = existing.get("seen_sessions") or []
            if not isinstance(existing_sessions, list):
                existing_sessions = []
            if session_id and session_id not in existing_sessions:
                existing_sessions.append(session_id)
            existing["seen_sessions"] = existing_sessions

            # 取最大 confidence (Round-2 修正建议)
            existing_conf = float(existing.get("confidence", 0.0))
            new_conf = round(error.confidence, 3)
            if new_conf > existing_conf:
                existing["confidence"] = new_conf

            existing_id = existing.get("id") or candidate_id or str(uuid.uuid4())
            existing["id"] = existing_id

            logger.info(
                "candidate_writer.frontmatter_duplicate_updated",
                path=str(p),
                candidate_id=existing_id,
                seen_count=existing["seen_count"],
                seen_sessions=len(existing_sessions),
            )
            candidate_id = existing_id
        else:
            # 新候选: append 完整 record
            if candidate_id is None:
                candidate_id = str(uuid.uuid4())
            new_record = _make_candidate_record(
                error,
                node_id=node_id,
                session_id=session_id,
                group_id=group_id,
                candidate_id=candidate_id,
                dedupe_hash=dedupe_hash,
                now_iso=now_iso,
                ai_reason=ai_reason,
                evidence_turns=evidence_turns,
                raw_dialog_excerpt=raw_dialog_excerpt,
            )
            candidates_list.append(new_record)

        fm_dict["error_candidates"] = candidates_list

        new_fm = yaml.safe_dump(fm_dict, allow_unicode=True, sort_keys=False)
        new_text = f"---\n{new_fm}---\n{body}"

        # 复用 errors[] 的原子写入模式 (AC #4 Task 4.5 from Story 2.5 v1.0)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=p.parent,
            prefix=f".{p.name}.tmp",
        ) as tmp:
            tmp.write(new_text)
            tmp_path = tmp.name
        os.replace(tmp_path, p)

        logger.info(
            "candidate_writer.frontmatter_written",
            path=str(p),
            pedagogy_type=error.pedagogy_type.value,
            confidence=error.confidence,
            candidate_id=candidate_id,
            duplicate=existing_idx is not None,
        )
        return True, candidate_id
    except Exception as e:
        logger.warning(
            "candidate_writer.frontmatter_failed",
            path=str(file_path),
            error=str(e),
            error_type=type(e).__name__,
        )
        return False, None


async def write_candidate_to_frontmatter_async(
    file_path: str | Path,
    error: ClassifiedError,
    *,
    node_id: str,
    session_id: str = "",
    group_id: str = "",
    candidate_id: str | None = None,
    ai_reason: str | None = None,
    evidence_turns: list[int] | None = None,
    raw_dialog_excerpt: str | None = None,
) -> tuple[bool, str | None]:
    """Story 2.5.X — Async wrapper 复用 per-file lock 防并发数据丢失.

    多个 candidate write 并发写同一 .md 时, error_candidates[] 不丢条.
    """
    lock = _get_file_lock(file_path)
    async with lock:
        return await asyncio.to_thread(
            write_candidate_to_frontmatter,
            file_path,
            error,
            node_id=node_id,
            session_id=session_id,
            group_id=group_id,
            candidate_id=candidate_id,
            ai_reason=ai_reason,
            evidence_turns=evidence_turns,
            raw_dialog_excerpt=raw_dialog_excerpt,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Frontmatter 写入 (Task 4.1, 4.5)
# ═══════════════════════════════════════════════════════════════════════════════


def write_error_to_frontmatter(
    file_path: str | Path,
    error: ClassifiedError,
    error_id: str | None = None,
    node_id_for_dedupe: str = "",
) -> tuple[bool, str | None]:
    """Story 2.5 Task 4.1 — 追加错误到 .md frontmatter `errors[]` (原子写入).

    Story 2.5 ChatGPT 二轮审查 fix (2026-05-04):
    - HIGH#10: error_id 写入 frontmatter, 与 Graphiti misconception_id 一致
    - HIGH#11: dedupe_hash 检测同错误重复 → update last_seen_at + count 不 append
    - 注意: 并发安全由 write_error_to_frontmatter_async() 提供 per-file lock

    PRD §3.2 schema (扩展含 D 方案双标签 + dedupe):
    ```yaml
    errors:
      - id: <uuid>                          # 与 Graphiti misconception_id 一致
        dedupe_hash: <16 chars sha256>      # 同错误检测 key
        type: conceptual_confusion           # PRD pedagogy 标签
        legacy_type: knowledge_gap           # Story 3.6 兼容
        legacy_remedy: backtrack_definition  # Story 3.6 单一策略 (MEDIUM#13)
        description: "..."
        corrected_at: null
        last_seen_at: "2026-05-04T..."       # 重复错误更新
        seen_count: 1                        # 重复次数
        tags: [synonym_confusion]
        remedy_strategies: [discrimination_comparison]
        confidence: 0.85
        confidence_source: llm | heuristic   # MEDIUM (二轮审查建议)
        created_at: "2026-05-04T..."
    ```

    Args:
        file_path: 节点 .md 路径.
        error: ClassifiedError 双标签错误.
        error_id: 可选 UUID, 与 Graphiti misconception_id 关联.
        node_id_for_dedupe: 用于生成 dedupe_hash 的 node_id.

    Returns:
        (success, error_id) — 成功时返回 (True, error_id used);
        失败时返回 (False, None). 重复错误算成功 (返回 existing id).
    """
    p = Path(file_path)
    if not p.exists():
        logger.warning("error_writer.file_not_found", path=str(p))
        return False, None

    try:
        text = p.read_text(encoding="utf-8")
        fm_str, body = _split_frontmatter(text)

        fm_dict = yaml.safe_load(fm_str) if fm_str else {}
        if not isinstance(fm_dict, dict):
            fm_dict = {}

        errors_list = fm_dict.get("errors", [])
        if not isinstance(errors_list, list):
            errors_list = []

        # Story 2.5 HIGH#11 fix — dedupe 检测
        dedupe_hash = _make_dedupe_hash(error, node_id_for_dedupe)
        now_iso = datetime.now(timezone.utc).isoformat()

        existing_idx: int | None = None
        for i, rec in enumerate(errors_list):
            if (
                isinstance(rec, dict)
                and rec.get("dedupe_hash") == dedupe_hash
                and rec.get("corrected_at") is None  # 已纠正的不算重复
            ):
                existing_idx = i
                break

        if existing_idx is not None:
            # 同错误重复: 更新 last_seen_at + seen_count, 不 append
            existing = errors_list[existing_idx]
            existing["last_seen_at"] = now_iso
            existing["seen_count"] = int(existing.get("seen_count", 1)) + 1
            existing_id = existing.get("id") or error_id or str(uuid.uuid4())
            existing["id"] = existing_id
            logger.info(
                "error_writer.frontmatter_duplicate_updated",
                path=str(p),
                error_id=existing_id,
                seen_count=existing["seen_count"],
            )
            error_id = existing_id
        else:
            # 新错误: append 完整 record
            if error_id is None:
                error_id = str(uuid.uuid4())
            new_record = {
                "id": error_id,
                "dedupe_hash": dedupe_hash,
                "type": error.pedagogy_type.value,
                "legacy_type": error.legacy_type.value,
                "legacy_remedy": error.legacy_remedy.value,  # MEDIUM#13 fix
                "description": error.description,
                "corrected_at": None,
                "last_seen_at": now_iso,
                "seen_count": 1,
                "tags": list(error.sub_tags),
                "remedy_strategies": [r.value for r in error.pedagogy_remedies],
                "confidence": round(error.confidence, 3),
                "created_at": now_iso,
            }
            errors_list.append(new_record)

        fm_dict["errors"] = errors_list

        new_fm = yaml.safe_dump(fm_dict, allow_unicode=True, sort_keys=False)
        new_text = f"---\n{new_fm}---\n{body}"

        # AC #4 Task 4.5: 原子写入 (临时文件 + os.replace)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=p.parent,
            prefix=f".{p.name}.tmp",
        ) as tmp:
            tmp.write(new_text)
            tmp_path = tmp.name
        os.replace(tmp_path, p)

        logger.info(
            "error_writer.frontmatter_written",
            path=str(p),
            pedagogy_type=error.pedagogy_type.value,
            legacy_type=error.legacy_type.value,
            confidence=error.confidence,
            error_id=error_id,
            duplicate=existing_idx is not None,
        )
        return True, error_id
    except Exception as e:
        logger.warning(
            "error_writer.frontmatter_failed",
            path=str(file_path),
            error=str(e),
            error_type=type(e).__name__,
        )
        return False, None


async def write_error_to_frontmatter_async(
    file_path: str | Path,
    error: ClassifiedError,
    error_id: str | None = None,
    node_id_for_dedupe: str = "",
) -> tuple[bool, str | None]:
    """Story 2.5 P0 fix — Async wrapper with per-file lock 防并发数据丢失.

    多个 record_error 并发写同一 .md 时, errors[] 不丢条.
    """
    lock = _get_file_lock(file_path)
    async with lock:
        return await asyncio.to_thread(
            write_error_to_frontmatter,
            file_path,
            error,
            error_id,
            node_id_for_dedupe,
        )


def _split_frontmatter(text: str) -> tuple[str, str]:
    """切分 markdown frontmatter (--- ... ---) 与 body.

    支持兼容: BOM (\ufeff) + CRLF (\r\n).
    返回: (frontmatter_yaml_str, body_str). 无 frontmatter 时 fm_yaml_str = "".
    """
    s = text.lstrip("\ufeff")
    if not s.startswith("---"):
        return "", text  # 保留原 text (含 BOM)
    parts = s.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1].lstrip("\r\n"), parts[2].lstrip("\r\n")


# ═══════════════════════════════════════════════════════════════════════════════
# Graphiti 写入 (Task 4.2, 4.3, 4.4) — 通过 memory_service.record_knowledge_entity
# ═══════════════════════════════════════════════════════════════════════════════


async def write_error_to_graphiti(
    error: ClassifiedError,
    node_id: str,
    session_id: str = "",
    error_id: str | None = None,
) -> bool:
    """Story 2.5 Task 4.2 — 通过 memory_service.record_knowledge_entity 写 Graphiti.

    AC #6: 失败 → structlog warning + 3 次重试 (间隔 1s) + 最终返回 False.

    Args:
        error: ClassifiedError 双标签.
        node_id: Canvas 节点 ID.
        session_id: 对话 session ID.

    Returns:
        True 写入成功, False 重试耗尽仍失败.
    """
    try:
        from app.config import DEFAULT_GROUP_ID
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()
    except (ImportError, AttributeError, RuntimeError) as e:
        logger.warning(
            "error_writer.memory_service_unavailable",
            error=str(e),
            error_type=type(e).__name__,
            node_id=node_id,
        )
        return False

    metadata: dict[str, Any] = {
        "misconception_id": error_id,  # Story 2.5 HIGH#10 fix — 与 frontmatter id 关联
        "pedagogy_type": error.pedagogy_type.value,
        "legacy_type": error.legacy_type.value,
        "description": error.description,
        "context": error.context,
        "remedy_strategies": [r.value for r in error.pedagogy_remedies],
        "legacy_remedy": error.legacy_remedy.value,
        "sub_tags": list(error.sub_tags),
        "confidence": round(error.confidence, 3),
        "node_id": node_id,
        "session_id": session_id,
    }
    content = (
        f"Error ({error.pedagogy_type.value} / {error.legacy_type.value}): "
        f"{error.description}"
    )

    for attempt in range(1, GRAPHITI_MAX_RETRIES + 1):
        try:
            await asyncio.wait_for(
                memory_svc.record_knowledge_entity(
                    event_type="misconception",
                    content=content,
                    metadata=metadata,
                    group_id=DEFAULT_GROUP_ID,
                ),
                timeout=GRAPHITI_TIMEOUT_S,
            )
            logger.info(
                "error_writer.graphiti_written",
                node_id=node_id,
                attempt=attempt,
                pedagogy_type=error.pedagogy_type.value,
            )
            return True
        except asyncio.TimeoutError:
            logger.warning(
                "error_writer.graphiti_timeout",
                attempt=attempt,
                timeout_s=GRAPHITI_TIMEOUT_S,
                node_id=node_id,
            )
        except Exception as e:
            logger.warning(
                "error_writer.graphiti_attempt_failed",
                attempt=attempt,
                error=str(e),
                error_type=type(e).__name__,
                node_id=node_id,
            )
        if attempt < GRAPHITI_MAX_RETRIES:
            await asyncio.sleep(GRAPHITI_RETRY_INTERVAL_S)

    logger.warning(
        "error_writer.graphiti_max_retries_exceeded",
        node_id=node_id,
        max_retries=GRAPHITI_MAX_RETRIES,
    )
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# 双写入口 (Task 4 综合)
# ═══════════════════════════════════════════════════════════════════════════════


async def write_error_dual(
    file_path: str | Path,
    error: ClassifiedError,
    node_id: str,
    session_id: str = "",
    fire_and_forget_graphiti: bool = True,
    *,
    mode: WriteMode = "candidate_only",
    group_id: str = "",
    ai_reason: str | None = None,
    evidence_turns: list[int] | None = None,
    raw_dialog_excerpt: str | None = None,
) -> dict[str, Any]:
    """Story 2.5 Task 4 + Story 2.5.X Task 1 — 双写入口 (含 C+ 渐进式确认 mode).

    Story 2.5.X (D15 = C+) 修正 (2026-05-04):
    - 加 `mode` 参数 (默认 "candidate_only" — AI 不直接写 errors[], 写候选区)
    - mode="candidate_only" → 调 write_candidate_to_frontmatter_async, 跳过 Graphiti (AC #1)
    - mode="write_confirmed" → 现有 v1.0 行为 (用户 accept_candidate 时使用)

    Story 2.5 v1.0 ChatGPT 二轮审查 fix (commit 0d05ad8):
    - P0#3 fix: 使用 write_error_to_frontmatter_async + per-file lock 防并发
    - HIGH#5 fix: graphiti_status "queued" 表示异步任务已调度
    - HIGH#10 fix: error_id 在 frontmatter + Graphiti metadata 一致
    - HIGH#11 fix: dedupe 同错误重复时返回相同 error_id, 不 append

    Args:
        file_path: .md 路径.
        error: ClassifiedError.
        node_id: Canvas 节点 ID.
        session_id: 对话 session ID.
        fire_and_forget_graphiti: True → 后台 task; False → 同步等待 (仅 write_confirmed 模式生效).
        mode: "candidate_only" (默认 Story 2.5.X) → 写 error_candidates[] / "write_confirmed" → 写 errors[] + Graphiti.
        group_id: vault namespace (Story 2.5.Y 前期占位).
        ai_reason / evidence_turns / raw_dialog_excerpt: candidate 模式的辅助元数据 (Task 5 升级 LLM 后使用).

    Returns:
        candidate_only mode:
        {
          "mode": "candidate_only",
          "frontmatter": bool,
          "graphiti": "skipped_candidate_mode" | "skipped_frontmatter_failed",
          "candidate_id": str | None,
        }
        write_confirmed mode:
        {
          "mode": "write_confirmed",
          "frontmatter": bool,
          "graphiti": "queued" | "ok" | "failed" | "skipped_frontmatter_failed",
          "error_id": str | None,
        }
    """
    # Story 2.5.X Task 1: candidate_only 模式 (默认) — 写 error_candidates[], 不写 Graphiti
    if mode == "candidate_only":
        fm_ok, candidate_id = await write_candidate_to_frontmatter_async(
            file_path,
            error,
            node_id=node_id,
            session_id=session_id,
            group_id=group_id,
            ai_reason=ai_reason,
            evidence_turns=evidence_turns,
            raw_dialog_excerpt=raw_dialog_excerpt,
        )
        if not fm_ok:
            return {
                "mode": "candidate_only",
                "frontmatter": False,
                "graphiti": "skipped_frontmatter_failed",
                "candidate_id": None,
            }
        return {
            "mode": "candidate_only",
            "frontmatter": True,
            "graphiti": "skipped_candidate_mode",  # AC #1: candidate 阶段不进 Graphiti
            "candidate_id": candidate_id,
        }

    # mode == "write_confirmed" — Story 2.5 v1.0 原行为 (accept_candidate 触发)
    fm_ok, error_id = await write_error_to_frontmatter_async(
        file_path, error, error_id=None, node_id_for_dedupe=node_id
    )

    if not fm_ok:
        return {
            "mode": "write_confirmed",
            "frontmatter": False,
            "graphiti": "skipped_frontmatter_failed",
            "error_id": None,
        }

    if fire_and_forget_graphiti:
        asyncio.create_task(
            write_error_to_graphiti(error, node_id, session_id, error_id=error_id)
        )
        return {
            "mode": "write_confirmed",
            "frontmatter": True,
            "graphiti": "queued",
            "error_id": error_id,
        }

    graphiti_ok = await write_error_to_graphiti(
        error, node_id, session_id, error_id=error_id
    )
    return {
        "mode": "write_confirmed",
        "frontmatter": True,
        "graphiti": "ok" if graphiti_ok else "failed",
        "error_id": error_id,
    }
