"""Round-23 Story 8.4 · Relationship sync — frontmatter `relationships[]` → Graphiti edges.

修复 Round-14 残缺 #4 (前后端零同步): 用户在 Obsidian 编辑节点 frontmatter
``relationships:`` 字段, 但变更不流入 Graphiti, 导致 Graphiti edge graph 与 vault
真相分裂.

本模块提供:
- ``sync_relationships_for_note`` — 单节点 frontmatter relationships → Graphiti edges
- ``sync_relationships_in_vault`` — 扫 vault 全量同步 (dry-run 默认)

frontmatter schema (read 路径已用, 见 wikilink_context_service):
  relationships:
    - type: prerequisite
      target: "[[Fundamentals]]"
    - type: elaborates
      target: "[[Advanced Topics]]"

[Source: _bmad-output/research/round-23-chatgpt-dr-result-and-synthesis-2026-05-08.md Stage 2 Task 4]
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import structlog
import yaml

from app.services.error_writer import _split_frontmatter

logger = structlog.get_logger(__name__)


# Skip Obsidian/git internal dirs (与 error_reader 一致)
SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules", ".canvas-learning"}


def _extract_target_from_wikilink(target_str: str) -> str:
    """从 wikilink 字符串提取目标节点名.

    支持格式:
        "[[Foo]]"          -> "Foo"
        "[[Foo|alias]]"    -> "Foo"
        "[[folder/Foo]]"   -> "folder/Foo"
        "Foo"              -> "Foo" (raw)

    Args:
        target_str: frontmatter relationships[].target 字段 raw 值.

    Returns:
        清洗后的目标节点 slug (无 [[]], 无 alias).
    """
    if not isinstance(target_str, str):
        return ""
    s = target_str.strip()
    m = re.match(r"^\[\[(.+?)\]\]$", s)
    if m:
        s = m.group(1)
    if "|" in s:
        s = s.split("|", 1)[0]
    return s.strip()


def _parse_frontmatter_relationships(file_path: Path) -> list[dict[str, Any]]:
    """读单 .md 文件 frontmatter 的 relationships[] 字段.

    Returns:
        relationships list (空表示无关系或文件不存在).
    """
    if not file_path.exists() or not file_path.is_file():
        return []

    try:
        text = file_path.read_text(encoding="utf-8")
        fm_str, _ = _split_frontmatter(text)
        if not fm_str:
            return []
        fm_dict = yaml.safe_load(fm_str)
        if not isinstance(fm_dict, dict):
            return []
        rels = fm_dict.get("relationships", [])
        if not isinstance(rels, list):
            return []
        return [r for r in rels if isinstance(r, dict)]
    except (OSError, yaml.YAMLError) as e:
        logger.warning(
            "relationship_sync.parse_failed",
            path=str(file_path),
            error_type=type(e).__name__,
            error=str(e)[:200],
        )
        return []


async def sync_relationships_for_note(
    note_path: str | Path,
    vault_root: str | Path,
    *,
    group_id: Optional[str] = None,
    edge_client: Any = None,
) -> dict[str, Any]:
    """单节点 frontmatter relationships → Graphiti edges 同步.

    Args:
        note_path: 节点 .md 路径 (绝对或 vault 相对).
        vault_root: vault 根目录.
        group_id: Graphiti group_id (默认从 settings 推断).
        edge_client: 可选 Neo4jEdgeClient (test injection).

    Returns:
        dict 含 synced (edge 数), skipped (无效条目), errors.
    """
    p_note = Path(note_path)
    if not p_note.is_absolute():
        p_note = Path(vault_root) / p_note

    relationships = _parse_frontmatter_relationships(p_note)
    if not relationships:
        return {"synced": 0, "skipped": 0, "errors": []}

    if edge_client is None:
        from app.clients.neo4j_edge_client import get_neo4j_edge_client

        edge_client = get_neo4j_edge_client()
    if edge_client is None:
        return {
            "synced": 0,
            "skipped": len(relationships),
            "errors": ["edge_client unavailable"],
        }

    if group_id is None:
        from app.config import DEFAULT_GROUP_ID

        group_id = DEFAULT_GROUP_ID

    from app.clients.neo4j_edge_client import EdgeRelationship

    from_node_id = p_note.stem  # basename 无 .md
    canvas_path = (
        str(p_note.relative_to(vault_root))
        if p_note.is_relative_to(vault_root)
        else str(p_note)
    )

    synced = 0
    skipped = 0
    errors: list[str] = []

    for rel in relationships:
        rel_type = rel.get("type", "")
        target_raw = rel.get("target", "")
        target_slug = _extract_target_from_wikilink(target_raw)

        if not target_slug or not isinstance(rel_type, str) or not rel_type:
            skipped += 1
            continue

        try:
            edge = EdgeRelationship(
                canvas_path=canvas_path,
                from_node_id=from_node_id,
                to_node_id=target_slug,
                edge_label=rel_type.upper(),
                edge_id=f"{from_node_id}--{rel_type}--{target_slug}",
                group_id=group_id,
            )
            ok = await edge_client.add_edge_relationship(edge)
            if ok:
                synced += 1
            else:
                errors.append(f"add_edge_relationship returned False: {edge.edge_id}")
        except Exception as e:
            errors.append(f"{type(e).__name__}: {str(e)[:100]}")

    logger.info(
        "relationship_sync.note_synced",
        note_path=str(p_note),
        group_id=group_id,
        synced=synced,
        skipped=skipped,
        error_count=len(errors),
    )

    return {"synced": synced, "skipped": skipped, "errors": errors}


async def sync_relationships_in_vault(
    vault_root: str | Path,
    *,
    group_id: Optional[str] = None,
    dry_run: bool = True,
    edge_client: Any = None,
) -> dict[str, Any]:
    """全量扫 vault .md → 累计 Graphiti edges 同步统计.

    Args:
        vault_root: vault 根目录.
        group_id: Graphiti group_id.
        dry_run: True 默认仅扫描计数 (不写 Graphiti).
        edge_client: 可选 Neo4jEdgeClient (test injection).

    Returns:
        dict 含 files_scanned, total_synced, total_skipped, errors[].
    """
    vault = Path(vault_root)
    if not vault.is_dir():
        return {
            "files_scanned": 0,
            "total_synced": 0,
            "total_skipped": 0,
            "errors": [f"vault_root not a directory: {vault}"],
            "dry_run": dry_run,
        }

    files_scanned = 0
    total_synced = 0
    total_skipped = 0
    all_errors: list[str] = []

    for md_file in vault.rglob("*.md"):
        if any(part in SKIP_DIRS or part.startswith(".") for part in md_file.parts):
            continue

        files_scanned += 1
        relationships = _parse_frontmatter_relationships(md_file)
        if not relationships:
            continue

        if dry_run:
            valid = sum(
                1
                for r in relationships
                if isinstance(r, dict)
                and r.get("type")
                and _extract_target_from_wikilink(r.get("target", ""))
            )
            total_synced += valid
            total_skipped += len(relationships) - valid
        else:
            result = await sync_relationships_for_note(
                md_file,
                vault,
                group_id=group_id,
                edge_client=edge_client,
            )
            total_synced += result["synced"]
            total_skipped += result["skipped"]
            all_errors.extend(result["errors"])

    return {
        "files_scanned": files_scanned,
        "total_synced": total_synced,
        "total_skipped": total_skipped,
        "errors": all_errors,
        "dry_run": dry_run,
    }
