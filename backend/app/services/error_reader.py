"""Round-23 Story 7.4 · Patch 4 — Error reading path.

修复 Round-14 残缺 #1 (错误管理只写不读) — error_writer 已有 4 个写函数,
但读路径之前缺失. 本模块提供按 node / type / canvas 查错误历史的 API.

Schema 参考 error_writer.write_error_to_frontmatter (frontmatter `errors[]`):
  - id, dedupe_hash, type, legacy_type, description
  - created_at, last_seen_at, seen_count, corrected_at
  - tags, remedy_strategies, confidence

[Source: _bmad-output/research/round-23-chatgpt-dr-result-and-synthesis-2026-05-08.md Stage 1 Task 4]
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
import yaml

from app.services.error_writer import _split_frontmatter

logger = structlog.get_logger(__name__)


SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules", ".canvas-learning"}


async def read_errors_from_node(file_path: str | Path) -> list[dict[str, Any]]:
    """读单个节点 .md frontmatter 的 errors[].

    Args:
        file_path: 节点 .md 路径 (绝对或 vault 相对).

    Returns:
        errors 列表 (空列表表示无错误 / 文件不存在 / 解析失败).
        每个 record 含完整 schema (id/type/description/...).
    """
    p = Path(file_path)
    if not p.exists() or not p.is_file():
        return []

    try:
        text = p.read_text(encoding="utf-8")
        fm_str, _ = _split_frontmatter(text)
        if not fm_str:
            return []

        fm_dict = yaml.safe_load(fm_str)
        if not isinstance(fm_dict, dict):
            return []

        errors = fm_dict.get("errors", [])
        if not isinstance(errors, list):
            return []

        return [e for e in errors if isinstance(e, dict)]
    except (OSError, yaml.YAMLError) as e:
        logger.warning(
            "error_reader.read_failed",
            path=str(p),
            error_type=type(e).__name__,
            error=str(e)[:200],
        )
        return []


async def query_errors_by_type(
    vault_path: str | Path,
    misconception_type: str,
    *,
    only_uncorrected: bool = True,
    match_legacy_type: bool = True,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """扫 vault 内所有 .md 文件, 按 misconception type 过滤错误.

    实现 ChatGPT Stage 1 Task 4 "按 misconception 类型查历史" 核心需求.

    Args:
        vault_path: Vault 根目录 (绝对路径推荐).
        misconception_type: 目标类型 (匹配 type 或 legacy_type).
        only_uncorrected: True 仅返回 corrected_at 为 None 的活跃错误.
        match_legacy_type: True 同时匹配 legacy_type 字段 (Story 3.6 兼容).
        limit: 可选结果数上限.

    Returns:
        匹配错误列表, 按 last_seen_at 降序 (最近活跃在前).
        每条 record 增加 'node_path' 字段 (vault 相对) 用于定位来源节点.
    """
    vault = Path(vault_path)
    if not vault.is_dir():
        logger.warning("error_reader.vault_not_dir", path=str(vault))
        return []

    matched: list[dict[str, Any]] = []
    for md_file in vault.rglob("*.md"):
        if any(part in SKIP_DIRS or part.startswith(".") for part in md_file.parts):
            continue

        errors = await read_errors_from_node(md_file)
        for err in errors:
            type_match = err.get("type") == misconception_type
            legacy_match = (
                match_legacy_type and err.get("legacy_type") == misconception_type
            )
            if not (type_match or legacy_match):
                continue
            if only_uncorrected and err.get("corrected_at") is not None:
                continue

            try:
                rel_path = str(md_file.relative_to(vault))
            except ValueError:
                rel_path = str(md_file)

            matched.append({**err, "node_path": rel_path})

    matched.sort(key=lambda r: r.get("last_seen_at") or "", reverse=True)

    if limit is not None and limit > 0:
        return matched[:limit]
    return matched


async def query_errors_by_canvas(
    vault_path: str | Path,
    canvas_path: str | None = None,
    *,
    only_uncorrected: bool = True,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """列 vault 或某 canvas 内的全部错误 (含已纠正可选).

    Args:
        vault_path: Vault 根目录.
        canvas_path: 可选 canvas/board 路径过滤 (通过 frontmatter canvas 字段比对).
        only_uncorrected: True 仅返回未纠正错误.
        limit: 可选结果数上限.

    Returns:
        错误列表, 按 last_seen_at 降序.
    """
    vault = Path(vault_path)
    if not vault.is_dir():
        return []

    matched: list[dict[str, Any]] = []
    for md_file in vault.rglob("*.md"):
        if any(part in SKIP_DIRS or part.startswith(".") for part in md_file.parts):
            continue

        if canvas_path:
            try:
                text = md_file.read_text(encoding="utf-8")
                fm_str, _ = _split_frontmatter(text)
                fm_dict = yaml.safe_load(fm_str) if fm_str else {}
                if not isinstance(fm_dict, dict):
                    continue
                node_canvas = fm_dict.get("canvas")
                if node_canvas != canvas_path:
                    continue
            except (OSError, yaml.YAMLError):
                continue

        errors = await read_errors_from_node(md_file)
        for err in errors:
            if only_uncorrected and err.get("corrected_at") is not None:
                continue
            try:
                rel_path = str(md_file.relative_to(vault))
            except ValueError:
                rel_path = str(md_file)
            matched.append({**err, "node_path": rel_path})

    matched.sort(key=lambda r: r.get("last_seen_at") or "", reverse=True)

    if limit is not None and limit > 0:
        return matched[:limit]
    return matched
