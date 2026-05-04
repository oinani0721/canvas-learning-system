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
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
import yaml

from app.services.error_classifier import ClassifiedError

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# 配置常量 (PRD AC #4 + #6)
# ═══════════════════════════════════════════════════════════════════════════════

GRAPHITI_TIMEOUT_S = 0.5  # 单次 record_knowledge_entity 超时 (Task 4.3)
GRAPHITI_MAX_RETRIES = 3  # 重试上限 (Task 4.4)
GRAPHITI_RETRY_INTERVAL_S = 1.0  # 重试间隔


# ═══════════════════════════════════════════════════════════════════════════════
# Frontmatter 写入 (Task 4.1, 4.5)
# ═══════════════════════════════════════════════════════════════════════════════


def write_error_to_frontmatter(
    file_path: str | Path,
    error: ClassifiedError,
) -> bool:
    """Story 2.5 Task 4.1 — 追加错误到 .md frontmatter `errors[]` (原子写入).

    PRD §3.2 schema (扩展含 D 方案双标签):
    ```yaml
    errors:
      - type: conceptual_confusion         # PRD pedagogy 标签
        legacy_type: knowledge_gap          # Story 3.6 兼容标签
        description: "..."
        corrected_at: null
        tags: [synonym_confusion]
        remedy_strategies: [discrimination_comparison]
        confidence: 0.85
        created_at: "2026-05-04T..."
    ```

    Args:
        file_path: 节点 .md 路径 (绝对或相对).
        error: ClassifiedError 双标签错误.

    Returns:
        True 写入成功, False 失败 (不抛异常, 让调用方判断).
    """
    p = Path(file_path)
    if not p.exists():
        logger.warning("error_writer.file_not_found", path=str(p))
        return False

    try:
        text = p.read_text(encoding="utf-8")
        fm_str, body = _split_frontmatter(text)

        fm_dict = yaml.safe_load(fm_str) if fm_str else {}
        if not isinstance(fm_dict, dict):
            fm_dict = {}

        errors_list = fm_dict.get("errors", [])
        if not isinstance(errors_list, list):
            errors_list = []

        new_record = {
            "type": error.pedagogy_type.value,
            "legacy_type": error.legacy_type.value,
            "description": error.description,
            "corrected_at": None,
            "tags": list(error.sub_tags),
            "remedy_strategies": [r.value for r in error.pedagogy_remedies],
            "confidence": round(error.confidence, 3),
            "created_at": datetime.now(timezone.utc).isoformat(),
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
            "error_writer.frontmatter_appended",
            path=str(p),
            pedagogy_type=error.pedagogy_type.value,
            legacy_type=error.legacy_type.value,
            confidence=error.confidence,
        )
        return True
    except Exception as e:
        logger.warning(
            "error_writer.frontmatter_failed",
            path=str(file_path),
            error=str(e),
            error_type=type(e).__name__,
        )
        return False


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
) -> dict[str, Any]:
    """Story 2.5 Task 4 — 双写入口 (frontmatter sync + Graphiti async).

    AC #4 + #6 综合:
    - frontmatter 同步原子写入 (本地优先).
    - Graphiti 默认 fire-and-forget (调用方不必 await), 可改为同步等待.
    - frontmatter 失败 → 跳过 Graphiti (因为本地都没成功, 远端无意义).

    Args:
        file_path: .md 路径.
        error: ClassifiedError.
        node_id: Canvas 节点 ID.
        session_id: 对话 session ID.
        fire_and_forget_graphiti: True (默认) → 后台 task; False → 同步等待.

    Returns:
        {"frontmatter": bool, "graphiti": "scheduled" | "ok" | "failed"
                                     | "skipped_frontmatter_failed"}
    """
    fm_ok = write_error_to_frontmatter(file_path, error)

    if not fm_ok:
        return {
            "frontmatter": False,
            "graphiti": "skipped_frontmatter_failed",
        }

    if fire_and_forget_graphiti:
        # Task 4.3: fire-and-forget, 不阻塞主流程
        asyncio.create_task(write_error_to_graphiti(error, node_id, session_id))
        return {"frontmatter": True, "graphiti": "scheduled"}

    graphiti_ok = await write_error_to_graphiti(error, node_id, session_id)
    return {
        "frontmatter": True,
        "graphiti": "ok" if graphiti_ok else "failed",
    }
