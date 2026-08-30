"""Shared vault_id resolver — CARD-G2-2 起为 ``app.core.vault_scope`` 的 re-export。

历史:
    Stage B 把 _resolve_vault_group_id helper inline 放在 mastery.py;
    Stage B 续 (2026-05-12) 提取到本共享模块覆盖 11 个 endpoint 文件。
    CARD-G2-2 (2026-08-28) 把解析本体收敛到 ``app.core.vault_scope``
    唯一解析点, 本模块只保留 import 兼容面 (mastery.py 等的 alias 同一性
    与既有 ``from ._vault_id_resolver import resolve_vault_group_id``
    调用面零改动)。

行为契约 (语义变更, 详见 app/core/vault_scope.py 模块 docstring):
    - 显式 vault_id 与进程 active vault 不一致 → HTTPException 409
      (fail-closed, boards.py 先例)。
    - vault_id 空 + legacy group_id → canonical_group_id 归一化 (deprecated
      warning, 不 409 — 本卡显式裁定)。
    - 双缺失 → 推导 active vault 组 (不再回落 DEFAULT_GROUP_ID)。
    - 每次解析 set_current_subject_id(group_id) 注入 ContextVar。
"""

from __future__ import annotations

from app.core.vault_scope import resolve_vault_group_id

__all__ = ["resolve_vault_group_id"]
