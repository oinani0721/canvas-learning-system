"""Shared vault_id ContextVar resolver — Wave-5 Stage B (extracted Stage B 续 2026-05-12).

历史:
    Stage B 把 _resolve_vault_group_id helper inline 放在 mastery.py.
    Stage B 续覆盖 canvas/agents/sync/wikilink/tips/suggestions/archive/edges/context/skills 等
    11 个剩余 endpoint files,如继续 inline 复制会复制到 11 处 → DD-03 / 复制即 bug 源.
    提取到共享模块,所有 endpoint file 统一 `from ._vault_id_resolver import resolve_vault_group_id`.

行为契约:
    优先级 vault_id > legacy_group_id > DEFAULT_GROUP_ID.
    每次调用都 set_current_subject_id(group_id) 注入 ContextVar 防多 vault 串库.
    legacy 路径走 canonical_group_id 归一化, 避免 'cs188' / 'canvas-dev' 直进 Neo4j (Round-23 Patch 2).
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def resolve_vault_group_id(
    vault_id: Optional[str],
    subject_id: Optional[str] = None,
    canvas_path: Optional[str] = None,
    legacy_group_id: Optional[str] = None,
) -> str:
    """Wave-5 Stage B 共享 helper — vault_id → ContextVar 注入 + group_id 派生.

    Args:
        vault_id: Plugin 端 inferVaultId(app.vault.getName()) 取的 raw vault name.
        subject_id: 可选 vault 内学科二级 (Stage A 透传).
        canvas_path: 可选 canvas 路径 (subject_id 为空时 fallback).
        legacy_group_id: 兼容旧 plugin 调用 (deprecated, 仅 vault_id 空时使用).

    Returns:
        Sanitized + canonical vault: 前缀 group_id (注入 ContextVar 后再返回).

    兼容策略:
        vault_id 提供 → 走新路径 (推荐).
        vault_id 空 + group_id 提供 → 走 deprecated 路径 (warning log).
        两者都空 → DEFAULT_GROUP_ID fallback.
    """
    # 延迟 import 避开循环依赖 (app.config 早期 import 链)
    from app.config import DEFAULT_GROUP_ID, sanitize_vault_id
    from app.core.subject_config import (
        build_vault_group_id,
        canonical_group_id,
        set_current_subject_id,
    )

    if vault_id and vault_id.strip():
        sanitized = sanitize_vault_id(vault_id)
        derived = build_vault_group_id(
            sanitized,
            subject_id=subject_id,
            canvas_path=canvas_path,
        )
    elif legacy_group_id and legacy_group_id.strip():
        logger.warning(
            "Wave-5 Stage B: vault_id missing, falling back to deprecated "
            "group_id=%s. Update plugin caller to pass vault_id.",
            legacy_group_id,
        )
        derived = canonical_group_id(legacy_group_id)
    else:
        logger.warning(
            "Wave-5 Stage B: both vault_id and group_id missing, "
            "falling back to DEFAULT_GROUP_ID=%s.",
            DEFAULT_GROUP_ID,
        )
        derived = DEFAULT_GROUP_ID

    set_current_subject_id(derived)
    return derived
