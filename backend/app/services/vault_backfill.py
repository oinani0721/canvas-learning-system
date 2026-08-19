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

# callout 头: "> [!tip]+ ..." 以及插件实际输出的列表嵌套形态 "* > [!tips]+ ..."
# (实测 2026-06-11: Cmd+Shift+A 在列表项内批注时, Obsidian 写出 `* > [!tips]+`,
#  tips 为复数 — 旧正则 ^> + 单数词表两个条件都漏掉, 用户批注全部丢失)
_CALLOUT_HEAD_RE = re.compile(r"^(?:\s*[*+-]\s+)?>\s*\[!([\w/-]+)\][+-]?\s*(.*)$")
# 回填的批注类型 → (写入通道, 参数)
_CALLOUT_BACKFILL_TYPES = {"tip", "tips", "question", "hint", "note", "warning", "info"}
_ERROR_TYPES = {"error"}
# 跳过: 派生标记(relation/*, 由 frontmatter relationships 回填) / 引用 / 视频等
_SKIP_PREFIXES = ("relation/", "quote", "video")
# 理解度勾选模板行 (- [ ] / - [x])
_CHECKBOX_RE = re.compile(r"^-\s*\[([ x])\]\s*(.*)$")
# 插件脚手架模板 callout (非用户批注, 回填会污染每个派生节点的 tips)
_TEMPLATE_MARKERS = ("💬 围绕这个概念讨论",)
# 泛型标签标题 (插件写的 "💡 Tips" 等) — 丢弃以让正文首行=选中文本;
# 人工 callout 的实义标题则保留进正文
_GENERIC_TITLE_RE = re.compile(r"^\W*(Tips|Error|Question|Keypoint)\W*$", re.I)
# P0 (A+-prime 2026-06-26): 稳定批注身份, 嵌在标题行 "%%cb-xxx%%" (前端同构)
_ANNOTATION_ID_RE = re.compile(r"%%\s*(cb-[a-z0-9]+)\s*%%", re.I)


def _understanding_from_label(label: str) -> str:
    """勾选行文案 → understanding 值 (镜像前端 callout.ts 映射)。"""
    if "已懂" in label:
        return "understood"
    if "模糊" in label:
        return "fuzzy"
    if "不懂" in label:
        return "not-understood"
    return ""


def extract_callouts(md_text: str) -> list[tuple[str, str, str, str]]:
    """从 markdown 提取用户批注 callout → [(类型, understanding, 裸正文, 稳定id)]。

    去重修复 (2026-06-13): 输出与实时通道同构 — 正文不含标题/勾选模板,
    首行 = 用户选中的文本。勾选的理解度单独提取为字段 (而非混在正文里)。
    P0 (A+-prime 2026-06-26): 标题行 "%%cb-xxx%%" 提取为稳定身份 (第 4 元),
    无则 "" (历史批注回退首行)。
    跳过派生标记 [!relation/*]、[!quote]、[!video]、脚手架模板。
    """
    results: list[tuple[str, str, str, str]] = []
    current: Optional[tuple[str, str, list[str]]] = None  # (ctype, title, lines)

    def _flush():
        nonlocal current
        if current is None:
            return
        ctype, title, lines = current
        current = None
        if title.startswith(_TEMPLATE_MARKERS):
            return
        # P0: 先从标题剥离稳定 id, 再做泛型标题判定
        id_match = _ANNOTATION_ID_RE.search(title)
        annotation_id = id_match.group(1) if id_match else ""
        title = _ANNOTATION_ID_RE.sub("", title).strip()
        understanding = ""
        body_lines: list[str] = []
        for ln in lines:
            cb = _CHECKBOX_RE.match(ln)
            if cb:
                if cb.group(1) == "x" and not understanding:
                    understanding = _understanding_from_label(cb.group(2))
                continue  # 勾选模板行不进正文
            if ln:
                body_lines.append(ln)
        # 正文 = 续行内容 (与前端同构, 首行=选中文本)。实义标题保留进正文,
        # 泛型标签 ("💡 Tips") 丢弃; 仅标题型 callout 退用标题。
        if body_lines:
            if title and not _GENERIC_TITLE_RE.match(title):
                body_lines.insert(0, title)
            body = "\n".join(body_lines).strip()
        else:
            body = title
        if body:
            results.append((ctype, understanding, body, annotation_id))

    for line in md_text.splitlines():
        head = _CALLOUT_HEAD_RE.match(line)
        if head:
            _flush()
            ctype = head.group(1).lower()
            if ctype.startswith(_SKIP_PREFIXES):
                current = None
                continue
            if ctype in _CALLOUT_BACKFILL_TYPES or ctype in _ERROR_TYPES:
                current = (ctype, head.group(2).strip(), [])
            else:
                current = None
        elif current is not None and line.startswith(">"):
            current[2].append(line.lstrip("> ").strip())
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
        invalidate_missing_callouts,
        write_callout,
        write_error,
        write_relation_reason,
    )

    base = Path(vault_path)
    stats = {
        "callouts": 0,
        "errors": 0,
        "relations": 0,
        "files": 0,
        "failed": 0,
        "invalidated": 0,
    }
    if not base.exists():
        logger.warning("[Backfill] vault 不存在: %s", vault_path)
        return stats

    fallback_now = datetime.now(timezone.utc)

    # D2 修复 (2026-07-12 对抗审查): 复用 LanceDB 索引同款黑名单 — 旧逻辑只跳
    # .obsidian/templates, 检验白板/Dashboard/skill 文档的 callout 全被当用户
    # 批注回填进图 (Neo4j 已实测出现 'SKILL'/'Dashboard'/检验白板会话实体),
    # 信息隔离 (d=1.50) 在 Graphiti 层破口: 考题内容可经 memory 读侧回流。
    #
    # ⛔ P1-05 (Codex 复核 2026-08-19): 上一行的"复用同款黑名单"此前是**直接 split
    # 原始 env 串**再硬补 .obsidian/templates —— 完全绕过 effective_vault_skip_dirs()
    # 的不可撤销硬底。而本函数由 main.py:387-392 在**启动时**以 execute=True 调用,
    # 会把漏过的 callout/error 直接写进 Graphiti。即: LanceDB 两条路径加了 union,
    # 并不等于"所有记忆索引入口"已上锁 —— 图层这条才是最难清理的那条
    # (写进去的边要靠 invalid_at 失效, 不像 LanceDB 能 orphan sweep 自动收敛)。
    #
    # 现改为与索引路径**共用唯一策略源**: settings.effective_vault_skip_dirs()
    # = 可配置串 ∪ IMMUTABLE_VAULT_SKIP_DIRS。env 只能追加, 不能删除安全边界。
    from fnmatch import fnmatch

    from app.config import settings as _settings

    _skip_dirs = set(_settings.effective_vault_skip_dirs())
    # templates 不在硬底里 (它是"非学习内容"而非"安全边界"), 保留原有硬补
    _skip_dirs.add("templates")

    def _is_blacklisted(md_path: Path) -> bool:
        rel_parts = md_path.relative_to(base).parts
        # vault 根级直下的 md (Dashboard/CLAUDE/杂项) 不是学习节点 — 学习内容
        # 都在 节点/原白板/raw 等子目录; 根级 callout (如 Dashboard 的 info 块)
        # 进图就是噪音/泄漏
        if len(rel_parts) == 1:
            return True
        return any(any(fnmatch(part, pat) for pat in _skip_dirs) for part in rel_parts)

    for md in sorted(base.rglob("*.md")):
        if _is_blacklisted(md):
            continue
        node_id = md.stem
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # P3 (A4): 回填用文件 mtime 作源事件时间近似(非统一 now)。配合 writer 的
        # create-or-preserve, 此时间只用于"从未实时写过"的历史边; 已有边保留原始时间。
        try:
            occurred = datetime.fromtimestamp(md.stat().st_mtime, timezone.utc)
        except (OSError, ValueError):
            occurred = fallback_now

        callouts = extract_callouts(text)
        rels = CanvasProjectionSync._read_relationships(md) or []
        if not callouts and not rels:
            continue
        stats["files"] += 1

        for ctype, understanding, body, annotation_id in callouts:
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
                            understanding=understanding or None,
                            annotation_id=annotation_id or None,
                        )
                stats["errors" if ctype in _ERROR_TYPES else "callouts"] += 1
            except Exception as e:  # noqa: BLE001 — 单条失败不阻断回填
                stats["failed"] += 1
                logger.debug("[Backfill] callout 写失败 %s: %s", node_id, e)

        # P5 (A2): 删除对账 — 当前 frontmatter 已无的批注边置 invalid_at。
        # 仅当本文件仍有带 id 的 callout 时跑 (keep 集合非空); 删光所有 callout
        # 是边界场景, 当前不在此处理 (已知项, 影响仅图整洁非出题, P1 已隔离)。
        keep_ids = {aid for (_, _, _, aid) in callouts if aid}
        if execute and keep_ids:
            try:
                stats["invalidated"] += await invalidate_missing_callouts(
                    driver,
                    embedder,
                    node_id=node_id,
                    group_id=group_id,
                    keep_annotation_ids=keep_ids,
                    occurred_at=occurred,
                )
            except Exception as e:  # noqa: BLE001 — 对账失败不阻断回填
                logger.debug("[Backfill] 删除对账失败 %s: %s", node_id, e)

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
