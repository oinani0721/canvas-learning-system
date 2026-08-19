"""P1-05b (R11-BATCH2-2026-08-17): 唯一路径准入函数 — 文件扫描类记忆写入口共用。

背景
----
黑名单**常量**在 b5706b04 已收敛为唯一策略源 (settings.effective_vault_skip_dirs
= 可配置串 ∪ IMMUTABLE_VAULT_SKIP_DIRS), 但 containment **判定逻辑**此前有六份
互不相同的拷贝, 且四条活文件扫描链各自为政:

  - canvas_projection_sync.sync   完全无过滤 (连根级 Dashboard.md 都写 CANVAS_EDGE,
                                  其 label 经 question_generator._get_edge_reasons
                                  直通出题链)
  - relationship_sync_service     模块私有 SKIP_DIRS, 缺四个铁律目录
  - sync_relationships_for_note   接受任意字符串路径, 绝对路径/../symlink 全放行
  - error_rebuild fallback        扫 vault 根级 *.md

本模块 = "哪些路径不许进记忆系统" 的那**一个**函数。任何新的文件扫描写入口
都必须过 check_vault_path, 不许再长出私有黑名单或私有 containment。

containment 蓝本: verification_service._resolve_canvas_path
(.resolve() → relative_to → 后缀白名单)。
返回值语义对齐: vault_index_orchestrator.should_index 的 (ok, reason-slug)。
"""

from __future__ import annotations

import os
from pathlib import Path

#: check_vault_path 的全部 reason slug (机器可读, 供调用方/测试穷举)。
ADMISSION_REASONS = frozenset(
    {
        "ok",
        "not_markdown",
        "outside_vault",
        "symlink_escape",
        "blacklisted_dir",
        "blacklisted_file",
        "root_level",
    }
)


def check_vault_path(path: str | Path, vault_root: str | Path) -> tuple[bool, str]:
    """判定一个路径是否允许进入记忆系统 (LanceDB/Neo4j/Graphiti 的文件扫描写入口)。

    Args:
        path: 候选文件路径。绝对路径, 或相对 vault_root 的相对路径。
        vault_root: vault 根目录。

    Returns:
        (ok, reason)。reason ∈ ADMISSION_REASONS:
          - ok               通过
          - outside_vault    resolve 后不在 vault 内 (绝对路径逃逸 / `../` 上跳)
          - symlink_escape   词法上在 vault 内, 但中途 symlink 把它带出了 vault
          - not_markdown     后缀白名单只收 .md
          - root_level       vault 根级直下的 md (Dashboard/CLAUDE/杂项) 不是学习
                             节点 — 学习内容都在 节点/原白板/raw 等子目录
          - blacklisted_dir  目录部件命中 effective_vault_skip_dirs (fnmatch)
          - blacklisted_file 文件名命中 DEFAULT_VAULT_SKIP_FILES / 根级文件黑名单

    ⛔ 黑白名单判定**只作用于 relative_to(vault_root).parts** — 绝不用绝对
    path.parts: 本仓的 worktree 就位于 `.claude/worktrees/` 下, 对绝对 parts 判
    `startswith(".")` 会让整个 vault 静默零扫描 (error_reader / relationship_sync
    的既有 bug 根源, 本轮一并修掉)。
    """
    vault_raw = Path(vault_root)
    try:
        vault_res = vault_raw.resolve()
    except (OSError, RuntimeError):
        return False, "outside_vault"

    raw = Path(path)
    if not raw.is_absolute():
        raw = vault_raw / raw

    # 词法归一 (normpath 不解 symlink, 只折叠 `..`) — 用于区分两种逃逸:
    # 词法已越界 = outside_vault; 词法在内但 resolve 跳出 = symlink_escape
    lexical = Path(os.path.normpath(str(raw)))
    try:
        resolved = raw.resolve()
    except (OSError, RuntimeError):
        return False, "outside_vault"

    if not resolved.is_relative_to(vault_res):
        if lexical.is_relative_to(vault_res) or lexical.is_relative_to(vault_raw):
            return False, "symlink_escape"
        return False, "outside_vault"

    if resolved.suffix.lower() != ".md":
        return False, "not_markdown"

    rel_parts = resolved.relative_to(vault_res).parts
    if len(rel_parts) <= 1:
        return False, "root_level"

    # 黑名单源 = 唯一策略源 (可配置串 ∪ 不可撤销硬底)。禁止模块私有集合。
    # P1-05c (Codex 三轮 F-01a): 匹配走 _fnmatch_canon (NFC+casefold) — APFS
    # 大小写不敏感, .CLAUDE/ 与 .claude/ 是同一物理目录, 裸 fnmatch 放行即旁路。
    from agentic_rag.clients.lancedb_client import _fnmatch_canon

    from app.config import settings

    skip_dirs = settings.effective_vault_skip_dirs()
    for part in rel_parts[:-1]:
        if any(_fnmatch_canon(part, pat) for pat in skip_dirs):
            return False, "blacklisted_dir"

    # 文件名黑名单复用 LanceDB 两条索引路径的同一判定 (任意层级 + 仅根级两套规则)
    from agentic_rag.clients.lancedb_client import (
        DEFAULT_VAULT_SKIP_FILES,
        _is_skipped_vault_file,
    )

    if _is_skipped_vault_file("/".join(rel_parts), DEFAULT_VAULT_SKIP_FILES):
        return False, "blacklisted_file"

    return True, "ok"
