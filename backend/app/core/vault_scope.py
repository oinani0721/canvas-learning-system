"""Unified per-request VaultScope resolution — CARD-G2-2 (BATCH-2026-08-28-第五批).

本模块是请求作用域(vault → group_id)的**唯一**解析点, 收敛此前分裂的 8 处实现:
共享 ``_vault_id_resolver`` (11 endpoint 文件) + 5 个本地克隆 (exam/metadata/
memory/errors/exam_sessions inline) + tips 私有 helper + boards 手写 409。

契约 (计划书 L209 硬边界3 "每请求只解析一次 VaultScope"):

1. **每请求恰一次解析** — endpoint 入口调 ``resolve_vault_scope()`` (或兼容
   包装 ``resolve_vault_group_id()``) 恰一次; 解析结果注入 ContextVar
   (``app.core.subject_config._current_subject_id``, 不新增第二真相源);
   service 层**只**经 ``current_group_id()`` / ``current_vault_id()`` 读,
   禁止自行解析或旁路兜底 DEFAULT_GROUP_ID。"恰一次"由结构保证:
   唯一解析代码路径 + 读写分离, 不做运行时计数断言。

2. **显式不一致 → 409 fail-closed** (boards.py:70-76 先例语义, 2026-08-10):
   请求显式携带 vault_id 且 sanitize 后**不在** ``active_vault_aliases()``
   (稳定 ID / ACTIVE_VAULT / 挂载目录 basename 三候选, 详见该函数) 之内时抛
   ``HTTPException(409)``, 禁止静默改写作用域。命中别名的请求放行并**归一到
   稳定 ID**, 防同一 vault 因入口不同分裂成两个 group 桶。

3. **双缺失 → 推导 active vault** (memory.py:100 / 批次1'① MEM-FLYWHEEL 姿势):
   vault_id 与 legacy_group_id 双缺失时**不**回落 DEFAULT_GROUP_ID
   (vault:default 污染桶), 而是 ``default_vault_group_id()`` 推导当前
   active vault 组 — 写读恒同 vault 命名空间。

4. **legacy_group_id 路径不做 409** (本卡显式裁定, 2026-08-28): deprecated
   兼容层经 ``canonical_group_id`` 归一化 (如 'cs188' → 'vault:default'),
   若对其做 active vault 一致性检查, 归一化产物几乎必然 409, 等于静默删除
   兼容层 — 超出本卡范围。deprecated 面收敛归 G2-4 / G4 消费链。

5. **hook cwd 推导 = 显式合法构造路径, 不 409** (chat.py P0-3 2026-07-31):
   Claude Code hook 的 payload 自带宿主 cwd, 由 ``_vault_id_from_hook_cwd``
   与 VAULTS_ROOT 目录名匹配推导 vault。该路径是 hook 请求唯一的
   per-request vault 信号 (hook 无 vault_id 字段), 推导结果与进程 active
   vault 不同属**设计内合法**(用户在另一 vault 目录起 Claude Code 会话),
   走 ``resolve_hook_cwd_scope()`` 显式建模, 不经 409 检查。

Patch-target 注记 (与 C6 test_memory_service_contextvar_leak 同坑): 本模块
所有依赖均函数体内延迟 import — 测试必须 patch ``app.config.
get_current_vault_id`` / ``app.core.subject_config.set_current_subject_id``
源模块命名空间, patch 本模块命名空间无效。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VaultScope:
    """一次请求作用域解析的结果 (不可变)。

    Attributes:
        group_id: 逻辑 D16 冒号格式 group_id (``vault:<vid>[:<二级>]``)。
            物理化 (``vault__x``) 是落库边界的事, 本对象保持逻辑格式。
        vault_id: sanitize 后的 vault 段 (group_id 的第二段)。
        source: 解析来源 — ``request-vault`` (显式 vault_id, 已过 409 门) /
            ``legacy-group`` (deprecated group_id 归一化) /
            ``active-vault`` (双缺失推导) / ``hook-cwd`` (hook 合法例外)。
    """

    group_id: str
    vault_id: str
    source: str


def _vault_segment(group_id: str, fallback: str) -> str:
    """取 D16 group_id 的 vault 段; 非 vault: 前缀时回落 fallback。"""
    if group_id.startswith("vault:"):
        parts = group_id.split(":")
        if len(parts) >= 2 and parts[1]:
            return parts[1]
    return fallback


def active_vault_aliases() -> set:
    """当前 active vault 的**全部合法别名** (sanitize 后)。

    Codex CARD-G2-2 round-1 HIGH-10 整改: ``Settings.vault_id`` 优先取
    ``.canvas-config.yaml`` 的显式稳定 ID, 而插件 / SessionEnd hook /
    exam skill 发来的往往是 **vault 目录名或 display name**。二者在
    「稳定 ID ≠ 目录名」的合法配置下并不相等 —— 只比稳定 ID 会把每一个
    正常请求都误判成跨 vault 并 409, 等于全站瘫痪。

    因此一致性判定采用别名集合:
      1. ``get_current_vault_id()`` — 稳定 ID (yaml 显式值优先)
      2. ``sanitize_vault_id(ACTIVE_VAULT)`` — 环境变量里的目录名
      3. ``sanitize_vault_id(basename(CANVAS_BASE_PATH))`` — 实际挂载目录名

    命中任一即视为「指向当前挂载 vault」。fail-closed 不被削弱: 真正
    指向**另一个** vault 的请求三项都不命中, 仍然 409。
    """
    import os

    from app.config import get_current_vault_id, get_settings, sanitize_vault_id

    aliases = {get_current_vault_id()}
    try:
        settings = get_settings()
        if settings.ACTIVE_VAULT:
            aliases.add(sanitize_vault_id(settings.ACTIVE_VAULT))
        base = settings.CANVAS_BASE_PATH
        if base:
            aliases.add(sanitize_vault_id(os.path.basename(str(base).rstrip("/"))))
    except Exception as e:  # noqa: BLE001 — 别名扩展失败只收窄到稳定 ID
        logger.debug("vault_scope: alias expansion skipped (%s)", e)
    return {a for a in aliases if a}


def resolve_vault_scope(
    vault_id: Optional[str],
    subject_id: Optional[str] = None,
    canvas_path: Optional[str] = None,
    legacy_group_id: Optional[str] = None,
) -> VaultScope:
    """请求边界唯一作用域解析 (模块 docstring 契约 1-4)。

    Args:
        vault_id: 请求显式携带的 vault 名 (插件 inferVaultId / API 字段)。
        subject_id: 可选 vault 内学科二级。
        canvas_path: 可选 canvas 路径 (subject_id 为空时的二级 fallback)。
        legacy_group_id: deprecated 旧 plugin group_id (仅 vault_id 空时用)。

    Returns:
        VaultScope — group_id 已注入 ContextVar。

    Raises:
        fastapi.HTTPException: 409 — 显式 vault_id 与进程 active vault 不一致。
    """
    from app.config import get_current_vault_id, sanitize_vault_id
    from app.core.subject_config import build_vault_group_id, canonical_group_id

    active_vault = get_current_vault_id()

    if vault_id and vault_id.strip():
        requested = sanitize_vault_id(vault_id)
        # HIGH-10 整改: 与别名集合比较 (稳定 ID / ACTIVE_VAULT / 挂载目录名),
        # 防「稳定 ID ≠ 目录名」的合法配置被全量误 409。
        if requested not in active_vault_aliases():
            # boards.py:70-76 先例: fail-closed, 防 vault split-brain 把
            # A vault 的请求静默写进 B vault 的作用域。
            from fastapi import HTTPException

            raise HTTPException(
                status_code=409,
                detail=f"vault 未激活: {requested} (当前挂载: {active_vault}) — "
                "请求 vault 与进程 active vault 不一致, 拒绝静默改写作用域 "
                "(CARD-G2-2 fail-closed)",
            )
        # 归一到稳定 ID: 请求可能用目录名/display name 命中别名, 但落库
        # group 必须恒为稳定 ID, 否则同一 vault 因入口不同分裂成两个桶。
        derived = build_vault_group_id(
            active_vault, subject_id=subject_id, canvas_path=canvas_path
        )
        source = "request-vault"
    elif legacy_group_id and legacy_group_id.strip():
        logger.warning(
            "vault_scope: vault_id missing, falling back to deprecated "
            "group_id=%s. Update caller to pass vault_id.",
            legacy_group_id,
        )
        derived = canonical_group_id(legacy_group_id)
        source = "legacy-group"
    else:
        # 契约 3: 双缺失推导 active vault, 不落 DEFAULT_GROUP_ID 污染桶。
        # 二级 (subject_id/canvas_path) 仍透传 — 与 metadata.py G-DEFAULT
        # 根治版行为对齐 (memory.py 版无二级透传, 此处取两者超集)。
        logger.warning(
            "vault_scope: both vault_id and group_id missing, deriving "
            "ACTIVE vault group (fail-closed, no DEFAULT_GROUP_ID fallback)"
        )
        derived = build_vault_group_id(
            active_vault, subject_id=subject_id, canvas_path=canvas_path
        )
        source = "active-vault"

    _inject(derived)
    return VaultScope(
        group_id=derived,
        vault_id=_vault_segment(derived, active_vault),
        source=source,
    )


def resolve_vault_group_id(
    vault_id: Optional[str],
    subject_id: Optional[str] = None,
    canvas_path: Optional[str] = None,
    legacy_group_id: Optional[str] = None,
) -> str:
    """兼容包装 — 与 Wave-5 Stage B 共享 helper 同签名, 返回 group_id str。

    既有 endpoint 调用面 (共享 ``_vault_id_resolver`` 的 re-export 与原
    5 处本地克隆的替换点) 统一走这里; 语义差异见模块 docstring
    (409 fail-closed + 双缺失推导 active vault)。
    """
    return resolve_vault_scope(
        vault_id,
        subject_id=subject_id,
        canvas_path=canvas_path,
        legacy_group_id=legacy_group_id,
    ).group_id


def resolve_hook_cwd_scope(cwd_vault_id: Optional[str]) -> VaultScope:
    """chat.py hook 路径专用 — cwd 推导 vault 的显式合法构造 (契约 5)。

    与 ``resolve_vault_scope`` 的区别: cwd 推导出的 vault 与进程 active
    vault 不一致**不是**冲突 (hook 会话本来就可能开在另一 vault 目录),
    不做 409; 推导失败 (None) 回落 active vault。

    Args:
        cwd_vault_id: ``_vault_id_from_hook_cwd`` 的推导结果 (已 sanitize),
            命中 0 或 >1 个 vault 时为 None。
    """
    from app.config import get_current_vault_id
    from app.core.subject_config import build_vault_group_id

    active_vault = get_current_vault_id()
    # HIGH-10 后半整改: cwd 推导出的是**目录名**。若它只是当前 vault 的
    # 别名 (稳定 ID ≠ 目录名的合法配置), 必须归一到稳定 ID —— 否则同一
    # vault 的 hook 路径与 API 路径写进两个不同的 group, 互相查不到。
    if cwd_vault_id and cwd_vault_id in active_vault_aliases():
        cwd_vault_id = active_vault
    if cwd_vault_id and cwd_vault_id != active_vault:
        logger.info(
            "vault_scope: hook cwd-derived vault %r differs from active %r — "
            "using cwd vault (documented legal exception, no 409)",
            cwd_vault_id,
            active_vault,
        )
    effective = cwd_vault_id or active_vault
    derived = build_vault_group_id(effective)
    _inject(derived)
    return VaultScope(
        group_id=derived,
        vault_id=effective,
        source="hook-cwd" if cwd_vault_id else "active-vault",
    )


def current_group_id() -> str:
    """service 层统一读取口 — 当前作用域的逻辑 group_id。

    ContextVar 已注入 (请求路径, 或 SessionEnd 归档等显式 set 的路径) →
    canonical 化返回; 未注入 (后台任务/CLI/scheduler) → 推导 active vault
    组。**取代** service 层旧的 ``canonical_group_id(ctx) if ctx else
    DEFAULT_GROUP_ID`` 兜底模式 — DEFAULT_GROUP_ID (vault:default) 是
    污染桶, 与写侧 active vault 组异组, 召回必空手 (UAT D2 实测根因)。

    物理化留给落库边界: 需要 Neo4j 物理格式的调用方自行
    ``to_physical_group_id(current_group_id())``。
    """
    from app.core.subject_config import (
        DEFAULT_SUBJECT_ID,
        canonical_group_id,
        default_vault_group_id,
        get_current_subject_id,
    )

    ctx = get_current_subject_id()
    if ctx and ctx != DEFAULT_SUBJECT_ID:
        return canonical_group_id(ctx)
    return default_vault_group_id()


def current_vault_id() -> str:
    """service 层统一读取口 — 当前作用域的 vault 段 (sanitized)。

    per-request 作用域已注入 → 取其 vault 段 (409 门保证请求路径下它与
    active vault 一致, 唯 hook-cwd 合法例外可不同); 未注入 → 进程
    active vault (``get_current_vault_id()``)。

    memory_service 写组 (``_vault_scoped_group_id``) 的 vault 来源改经
    这里 — 根治 C6 记录的"进程级单 active vault"双真相源。
    """
    from app.config import get_current_vault_id
    from app.core.subject_config import (
        DEFAULT_SUBJECT_ID,
        canonical_group_id,
        get_current_subject_id,
    )

    ctx = get_current_subject_id()
    if ctx and ctx != DEFAULT_SUBJECT_ID:
        canon = canonical_group_id(ctx)
        if canon.startswith("vault:"):
            seg = canon.split(":")[1] if len(canon.split(":")) >= 2 else ""
            if seg:
                return seg
    return get_current_vault_id()


def _inject(group_id: str) -> None:
    """解析结果注入 ContextVar (唯一注入点, 延迟 import 保 patch 可达)。"""
    from app.core.subject_config import set_current_subject_id

    set_current_subject_id(group_id)
