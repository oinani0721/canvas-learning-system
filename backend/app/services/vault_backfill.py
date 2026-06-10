"""Phase 4.5 (GRAPHITI-NATIVE-MEMORY-2026-06-10): vault 历史数据回填。

读侧切到 Graphiti-native 后, 旧图 (:Episodic 无 node_id / CANVAS_EDGE) 里的历史
上下文检验白板取不到 → 用户体感"升级后记忆丢了" (ChatGPT 计划审查必加项)。
本项目的历史记忆真相在 vault markdown (callout + frontmatter relationships),
故回填 = 重放 vault 经 structured_writer 写入 :Entity/RELATES_TO。

幂等: writer 边 uuid = uuid5(类型:节点:group:内容hash) → 重跑 MERGE 不重复。
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# callout 头: "> [!tip]+ 标题..." / "> [!question]- ..." / "> [!relation/related_to]+ ..."
_CALLOUT_HEAD_RE = re.compile(r"^>\s*\[!([\w/-]+)\][+-]?\s*(.*)$")
# 回填的批注类型 → (写入通道, 参数)
_CALLOUT_BACKFILL_TYPES = {"tip", "question", "hint", "note", "warning", "info"}
_ERROR_TYPES = {"error"}
# 跳过: 派生标记(relation/*, 由 frontmatter relationships 回填) / 引用 / 视频等
_SKIP_PREFIXES = ("relation/", "quote", "video")
# 插件脚手架模板 callout (非用户批注, 回填会污染每个派生节点的 tips)
_TEMPLATE_MARKERS = ("💬 围绕这个概念讨论",)


def extract_callouts(md_text: str) -> list[tuple[str, str]]:
    """从 markdown 提取用户批注 callout → [(类型, 完整文本)]。

    多行 callout: 头行标题 + 后续 "> " 续行合并; 嵌套新 [!] 头开新块。
    跳过派生标记 [!relation/*]、[!quote]、[!video]。
    """
    results: list[tuple[str, str]] = []
    current: Optional[tuple[str, list[str]]] = None

    def _flush():
        nonlocal current
        if current is not None:
            ctype, parts = current
            text = " ".join(p for p in parts if p).strip()
            if text and not text.startswith(_TEMPLATE_MARKERS):
                results.append((ctype, text))
            current = None

    for line in md_text.splitlines():
        head = _CALLOUT_HEAD_RE.match(line)
        if head:
            _flush()
            ctype = head.group(1).lower()
            if ctype.startswith(_SKIP_PREFIXES):
                current = None
                continue
            if ctype in _CALLOUT_BACKFILL_TYPES or ctype in _ERROR_TYPES:
                current = (ctype, [head.group(2).strip()])
            else:
                current = None
        elif current is not None and line.startswith(">"):
            current[1].append(line.lstrip("> ").strip())
        else:
            _flush()
    _flush()
    return results


async def backfill_vault(
    vault_path: str,
    driver: Any,
    embedder: Optional[Any],
    group_id: str,
    execute: bool = False,
) -> dict[str, int]:
    """扫 vault md → callout/error/relation 回填进 Graphiti 结构化图。

    execute=False (默认 dry-run): 只统计将写入的条数, 不动图。
    幂等: 同内容重跑 MERGE 同 uuid, 不重复。
    """
    from app.services.canvas_projection_sync import (
        CanvasProjectionSync,
        _resolve_node_id,
    )
    from app.services.graphiti_structured_writer import (
        write_callout,
        write_error,
        write_relation_reason,
    )

    base = Path(vault_path)
    stats = {"callouts": 0, "errors": 0, "relations": 0, "files": 0, "failed": 0}
    if not base.exists():
        logger.warning("[Backfill] vault 不存在: %s", vault_path)
        return stats

    occurred = datetime.now(timezone.utc)  # 回填统一时间戳 (原始时间 vault 无记录)

    for md in sorted(base.rglob("*.md")):
        if ".obsidian" in md.parts or "templates" in md.parts:
            continue
        node_id = md.stem
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        callouts = extract_callouts(text)
        rels = CanvasProjectionSync._read_relationships(md) or []
        if not callouts and not rels:
            continue
        stats["files"] += 1

        for ctype, body in callouts:
            try:
                if execute:
                    if ctype in _ERROR_TYPES:
                        await write_error(
                            driver,
                            embedder,
                            node_id=node_id,
                            group_id=group_id,
                            error_type="user_marked",
                            description=body,
                            occurred_at=occurred,
                        )
                    else:
                        await write_callout(
                            driver,
                            embedder,
                            node_id=node_id,
                            group_id=group_id,
                            callout_type=ctype,
                            text=body,
                            occurred_at=occurred,
                        )
                stats["errors" if ctype in _ERROR_TYPES else "callouts"] += 1
            except Exception as e:  # noqa: BLE001 — 单条失败不阻断回填
                stats["failed"] += 1
                logger.debug("[Backfill] callout 写失败 %s: %s", node_id, e)

        for rel in rels:
            target = _resolve_node_id(rel.get("target"))
            if not target or target == node_id:
                continue
            reason = str(rel.get("description") or rel.get("type") or "").strip()
            if not reason:
                continue
            try:
                if execute:
                    await write_relation_reason(
                        driver,
                        embedder,
                        source_node_id=node_id,
                        target_node_id=target,
                        group_id=group_id,
                        relation_type=str(rel.get("type") or "related_to"),
                        reason=reason,
                        occurred_at=occurred,
                    )
                stats["relations"] += 1
            except Exception as e:  # noqa: BLE001
                stats["failed"] += 1
                logger.debug("[Backfill] relation 写失败 %s: %s", node_id, e)

    return stats
