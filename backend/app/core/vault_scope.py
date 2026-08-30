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
from typing import Dict, Optional

# CARD-G4-1a: 跨 vault 豁免装饰器只有**一个**真相源 — 复用 cypher_helpers 的
# 既有实现 re-export, 不另造同名装饰器 (两个 allow_cross_vault 会让静态审计
# 与 lefthook lint 只认其中一个)。cypher_helpers 无 app 内部依赖, 顶层导入
# 不引入循环。
from app.utils.cypher_helpers import allow_cross_vault

logger = logging.getLogger(__name__)

__all__ = [
    "VaultScope",
    "VaultScopeUnresolved",
    "active_vault_aliases",
    "allow_cross_vault",
    "current_group_id",
    "current_vault_id",
    "group_in_read_scope",
    "read_group_filter",
    "read_scope_params",
    "require_read_group",
    "resolve_hook_cwd_scope",
    "resolve_vault_group_id",
    "resolve_vault_scope",
]


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


# ═══════════════════════════════════════════════════════════════════════════
# 读侧作用域 — CARD-G4-1a (BATCH-2026-08-29-第六批)
#
# 上面的 resolve_* 族是**请求边界**的写读通用解析点 (G2-2)。本节是**读侧**
# 专用的 fail-closed 收口: service 层再也不许把 group_id=None 直通 Neo4j
# (= 全库扫描, R4 违规)。契约见 .claude/rules/cypher-read-contract.md R1/R4。
#
# 前缀语义 (本节核心, 与 R1 "vault 内二级 namespace" 口径一致):
#   一个 vault 的数据并不全落在 vault 根组。写侧按 D16 规约把白板级内容写进
#   二级子组 —— canvas 子组 (vault__v__board)、语义影子组
#   (vault__v__semantic)、中文白板 punycode 组 (vault__v__xn--...)。
#   2026-08-30 现网 7691 只读实测: 全库唯一的 Concept 与唯一的 LEARNED 边
#   都落在 `vault__canvas_vault__xn--jhqx6ce6ettpca6420ada2925d`, vault 根组
#   零命中。因此读侧若用**等值**过滤锚 vault 根组, 泄漏是堵住了, 但"复习
#   建议"会全空 —— 比泄漏更像产品坏了。
#   规则: 命中 = 与 scope 组等值 **或** 以 `scope + "__"` 为前缀。
#
# 该规则同时满足两个方向相反的需求, 无需分叉:
#   scope=vault__v        (无 canvas 上下文) → 放行 vault 全部子组   [保召回]
#   scope=vault__v__brdA  (canvas 级读)      → 只放行自己的影子子组, 兄弟板
#                                              vault__v__brdB 仍不可见 [保隔离]
#   scope=vault__v        vs 他库 vault__w   → 既不等值也不前缀       [零泄漏]
#
# `__` 分隔符是锚点的一部分: 裸前缀会让 vault__a 误配 vault__ab
# (subjects.py:57 `_CANVAS_NODE_GROUP_FILTER` 先例已踩过这个坑)。
# ═══════════════════════════════════════════════════════════════════════════

#: 物理 group_id 的层级分隔符 (T1 契约: graphiti validator 拒冒号, 全图用 __)
_PHYSICAL_SEPARATOR = "__"


class VaultScopeUnresolved(Exception):
    """读侧作用域无法解析 — fail-closed 显式抛出, 不静默降级。

    抛出即代表作用域**不可信**: 进程连 active vault 都推导不出来 (配置断裂),
    或推导结果是 ``vault:default`` 污染桶 / 形状非法的组。正常运行路径
    **不会**触发: ``current_group_id()`` 在 ContextVar 未注入时也会推导
    active vault 组。

    ⚠️ **故意不继承 ``RuntimeError``**(Codex round-1 H-3 整改 2026-08-30):
    本仓多处优雅降级 handler 写作
    ``except (RuntimeError, ConnectionError, asyncio.TimeoutError)``
    (``conversation_inheritance.py`` / ``learning_context_service.py``), 若继
    承 RuntimeError, 作用域解析失败会被当成"Neo4j 暂时不可用"吞掉并返回空
    列表 —— 恰好把 fail-closed 退化成本卡要防的**静默断读**。继承裸
    ``Exception`` 让它绕开这些依赖故障 handler; 仍可能被 ``except Exception``
    捕获的调用点已逐个显式 ``except VaultScopeUnresolved: raise`` 前置放行。

    捕获本异常后返回空结果 = 把"配置坏了"伪装成"没有数据", 属 CARD-G4-2
    明令禁止的静默降级, 调用方不得这样做。
    """


#: 归一化污染桶 —— ``canonical_group_id`` 对空/非法输入的兜底产物, 也是
#: ``sanitize_vault_id("")`` 的产物 (config.py: 空 ACTIVE_VAULT → "default")。
#: **推导**得到它 = 配置断裂, 必须 fail-closed; 调用方**显式**传入 (deprecated
#: 兼容层 'cs188' → 'vault:default', G2-2 契约 4) 则放行并告警。
_DEFAULT_POLLUTION_GROUP = "vault:default"


def require_read_group(group_id: Optional[str] = None, *, context: str) -> str:
    """读侧作用域必填解析 (逻辑 D16 格式) — CARD-G4-1a fail-closed 收口。

    解析链 (三级, 无 DEFAULT_GROUP_ID 兜底):
      1. 显式 ``group_id`` 非空 → canonical 化后直接用 (调用方意图优先);
      2. ``None`` → ``current_group_id()`` — per-request ContextVar, 未注入时
         推导进程 active vault 组;
      3. 仍拿不到 / 落到 ``vault:default`` 污染桶 / 形状非法
         → 抛 ``VaultScopeUnresolved``。

    ⚠️ 显式传**空白串**(``""`` / ``"   "``)不走第 2 级, 直接抛 —— 与写侧
    ``neo4j_client._resolve_physical_group_id`` 的 C1 口径统一: 调用方以为自己
    传了作用域, 静默改用另一个作用域比报错危险得多。想走推导链请显式传 None。

    与旧模式 ``group_id or DEFAULT_GROUP_ID`` 的区别: DEFAULT_GROUP_ID 归一
    后是 ``vault:default`` 空桶, 与写侧 active vault 组异组, 召回必空手
    (UAT D2 实测根因); 与旧模式 ``group_id=None → 不过滤`` 的区别: 后者是
    直接的跨 vault 泄漏面 (R4 违规)。

    Args:
        group_id: 调用方显式作用域 (逻辑或物理格式皆可, 内部 canonical 化)。
        context: 调用点标识 (如 ``"memory_service.get_review_suggestions"``),
            仅用于异常/日志可读性 — 出问题时能直接定位是谁没有作用域。

    Returns:
        逻辑 D16 格式 group_id (``vault:<vid>[:<二级>]``)。物理化留给落库
        边界 —— Cypher 绑定请改用 :func:`read_scope_params`。

    Raises:
        VaultScopeUnresolved: 三级链全部落空。
    """
    if isinstance(group_id, str) and not group_id.strip():
        # 与写侧 `_resolve_physical_group_id` 的 C1 口径统一 (Codex G2-3
        # round-2/3): **显式传了字符串但内容为空 = 调用方 bug**, 不得静默回退
        # 推导链落到另一个作用域。想走推导链请显式传 None。
        raise VaultScopeUnresolved(
            f"read scope unresolved [context: {context}]: explicit group_id is "
            f"blank ({group_id!r}) — 拒绝据此推导到另一个作用域; 想走推导链请传 None"
        )

    if group_id:
        from app.core.subject_config import canonical_group_id

        raw = group_id.strip()
        if raw.startswith("vault" + _PHYSICAL_SEPARATOR):
            # 输入已是**物理**格式 (vault__x)。canonical_group_id 认不出它
            # (只认 'vault:' 前缀), 会走"其他"分支腐化成 vault:vault_x ——
            # 再 to_physical 就是 vault__vault_x 的数据损坏。先还原成逻辑
            # 格式再走统一链路 (与 to_physical_group_id 自身的幂等防御同型)。
            from app.graphiti.group_id_compat import (
                desanitize_group_id_from_graphiti,
            )

            raw = desanitize_group_id_from_graphiti(raw)
        resolved = canonical_group_id(raw)
        if resolved and resolved.strip():
            return _validate_scope_shape(resolved, context=context, explicit=True)
        raise VaultScopeUnresolved(
            f"read scope unresolved [context: {context}]: explicit group_id "
            f"{group_id!r} canonicalized to empty"
        )

    # ⚠️ Codex round-3 (2026-08-30) — **来源必须可分辨**。此前这里直接调
    # ``current_group_id()``, 把两种来源混成一个值再统一按"推导"校验, 于是
    # deprecated 兼容层被误伤: ``resolve_vault_scope(legacy_group_id='cs188')``
    # 会把归一化产物 ``vault:default`` **注入 ContextVar**, service 层再读时
    # 就被当成"配置断裂推导出污染桶"而抛错 —— 整条 legacy 路径在读侧断掉
    # (G2-2 契约 4 明确本卡不推翻兼容层)。
    #   · ContextVar 有真实值 = **有人显式设过**(请求边界解析 / SessionEnd 归档
    #     / 测试) ⇒ 按 explicit 处置, 与调用方直接传参同权;
    #   · 只有落到 active vault 推导这一支才是 derived, 才对污染桶 fail-closed。
    from app.core.subject_config import (
        DEFAULT_SUBJECT_ID,
        canonical_group_id,
        default_vault_group_id,
        get_current_subject_id,
    )

    ctx = get_current_subject_id()
    if ctx and ctx != DEFAULT_SUBJECT_ID:
        return _validate_scope_shape(
            canonical_group_id(ctx), context=context, explicit=True
        )

    try:
        resolved = default_vault_group_id()
    except Exception as e:  # noqa: BLE001 — 任何解析失败都转成显式 fail-closed
        raise VaultScopeUnresolved(
            f"read scope unresolved [context: {context}]: no explicit group_id "
            f"and active vault derivation failed ({type(e).__name__}: {e}). "
            "拒绝无作用域读取 (会跨 vault 全库扫描)。"
        ) from e

    if not resolved or not resolved.strip():
        raise VaultScopeUnresolved(
            f"read scope unresolved [context: {context}]: no explicit group_id "
            "and active vault derivation returned empty. 拒绝无作用域读取。"
        )
    return _validate_scope_shape(resolved, context=context, explicit=False)


def _validate_scope_shape(
    group_id: str, *, context: str, explicit: bool
) -> str:
    """作用域形状校验 — Codex round-1 H-1 / M-4 整改 (2026-08-30)。

    只检查"非空"不够, 有两类**看似有值实为无效**的作用域会把配置故障伪装成
    正常的空结果:

    1. ``vault:default`` 污染桶。``config.sanitize_vault_id("")`` 对空
       ``ACTIVE_VAULT`` 返回 ``"default"``, 于是配置坏掉的进程会稳定推导出
       ``vault:default`` —— 与写侧 active vault 组异组, 召回恒空 (UAT D2 实测
       根因)。**推导**出它 = fail-closed; 调用方**显式**传入则放行 + 告警
       (deprecated 兼容层 ``canonical_group_id('cs188') == 'vault:default'``,
       G2-2 契约 4 不在本卡范围内推翻)。
    2. 空段 / 裸前缀。``canonical_group_id("vault:")`` 原样返回 ``"vault:"``,
       物理化成 ``"vault__"`` —— 前缀 ``"vault____"`` 匹配不到任何东西, 同样
       是"非法配置伪装成空结果"。

    Args:
        group_id: 逻辑 D16 格式候选值。
        context: 调用点标识 (进异常信息)。
        explicit: 是否来自调用方显式入参 (决定 ``vault:default`` 的处置)。

    Returns:
        校验通过的 group_id (原样)。

    Raises:
        VaultScopeUnresolved: 形状非法 / 推导出污染桶。
    """
    value = group_id.strip()

    if not value.startswith("vault:"):
        raise VaultScopeUnresolved(
            f"read scope unresolved [context: {context}]: {group_id!r} is not a "
            "D16 vault: group — 拒绝以非规范作用域读取"
        )

    segments = value.split(":")[1:]
    if not segments or any(not seg.strip() for seg in segments):
        raise VaultScopeUnresolved(
            f"read scope unresolved [context: {context}]: {group_id!r} has an "
            "empty segment (裸 'vault:' / 'vault__' 之类) — 该作用域匹配不到任何"
            "数据, 会把非法配置伪装成正常空结果"
        )

    # Codex round-2 (2026-08-30) — 物理 ID 碰撞: 逻辑段内含 `__` 时,
    # ``vault:a__board`` 与 ``vault:a:board`` 物理化后**同为** ``vault__a__board``
    # (group_id_compat 自己也对这种输入告警"roundtrip will be lossy")。作为
    # **读作用域**这不只是往返失真: 一个真叫 `a__board` 的 vault 会与 vault `a`
    # 的 `board` 子组共用可见面 —— 前缀语义在这里会跨 vault。标准管线
    # (sanitize_vault_id / sanitize_subject_name 均折叠连续下划线) 产不出这种值,
    # 出现即配置有误, 拒绝而不是带着歧义继续读。
    if any(_PHYSICAL_SEPARATOR in seg for seg in segments):
        raise VaultScopeUnresolved(
            f"read scope unresolved [context: {context}]: {group_id!r} 的段内含 "
            f"{_PHYSICAL_SEPARATOR!r} — 物理化后与 'vault:<段1>:<段2>' 形态**同名**, "
            "两个不同 vault 会共用可见面。请修配置 (标准 sanitize 链会折叠连续下划线)。"
        )

    if value == _DEFAULT_POLLUTION_GROUP:
        if explicit:
            logger.warning(
                "vault_scope: read scope is the DEFAULT pollution bucket %r "
                "[context: %s] — 显式传入放行 (deprecated 兼容层), 但它与写侧 "
                "active vault 组异组, 召回大概率为空。",
                value,
                context,
            )
            return value
        if _default_is_configured():
            # 边界 (自查, 2026-08-30): vault **真的叫** default 时,
            # `vault:default` 是合法作用域, 不能与"没配置"混为一谈。判据是配置
            # 里确有非空 vault 身份 (yaml vault_id / ACTIVE_VAULT), 而不是
            # sanitize 对空输入的兜底产物。
            return value
        raise VaultScopeUnresolved(
            f"read scope unresolved [context: {context}]: derived scope is the "
            f"DEFAULT pollution bucket {value!r} — 进程没有可用的 active vault "
            "(config.sanitize_vault_id 对空 ACTIVE_VAULT 返回 'default')。"
            "拒绝读污染桶: 它与写侧异组, 会给出'查询成功但一条都没有'的假空。"
            "修法: 在 backend/.env 设 ACTIVE_VAULT=<你的 vault 目录名>, "
            "或在 vault 根的 .canvas-config.yaml 里写 vault_id。"
        )

    return value


def _default_is_configured() -> bool:
    """vault 身份是否**显式配置**为 ``default``。

    判据必须是"配置里写着 default", 不能是"配置里写了点什么"——后者会让
    ``ACTIVE_VAULT=canvas-vault`` 的正常进程在推导异常落到 ``vault:default``
    时被误判成合法, H-1 的 fail-closed 就白做了。

    ``sanitize_vault_id("")`` 返回 ``"default"`` 是**空输入的兜底**;
    ``ACTIVE_VAULT="default"`` 才是显式配置。两者只能靠原始值区分。
    """
    try:
        from app.config import get_settings, sanitize_vault_id

        active = (get_settings().ACTIVE_VAULT or "").strip()
        return bool(active) and sanitize_vault_id(active) == "default"
    except Exception as e:  # noqa: BLE001 — 读不到配置一律按"未配置"处理
        logger.debug("vault_scope: default-config probe failed (%s)", e)
        return False


def read_scope_params(
    group_id: Optional[str] = None, *, context: str
) -> Dict[str, str]:
    """读侧 Cypher 的 group 绑定参数 (物理格式 + 前缀锚)。

    与 :func:`read_group_filter` 成对使用::

        params = read_scope_params(group_id, context="svc.method")
        rows = await client.run_query(
            f"MATCH (n:Concept) WHERE {read_group_filter('n')} RETURN n",
            **params,
        )

    Returns:
        ``{"group_id": <物理组>, "group_prefix": <物理组 + "__">}``。
        两个键名与 ``subjects.py::_resolve_read_group_params`` 既有先例
        一致 —— 同一形态在库内只有一种写法。

    Raises:
        VaultScopeUnresolved: 作用域解析失败 (见 :func:`require_read_group`)。
    """
    from app.graphiti.group_id_compat import to_physical_group_id

    physical = to_physical_group_id(require_read_group(group_id, context=context))
    return {"group_id": physical, "group_prefix": physical + _PHYSICAL_SEPARATOR}


def read_group_filter(alias: str, *, allow_null: bool = False) -> str:
    """生成单个 alias 的 R1 组过滤片段 (等值 OR 前缀)。

    Args:
        alias: Cypher 中的节点/关系变量名。
        allow_null: 是否容忍 ``group_id IS NULL`` 的存量数据。**默认 False**
            (严格) —— NULL 容忍等于让无归属数据对所有 vault 可见, 是泄漏面。
            仅在"该 alias 的隔离已由同查询中其他 alias 充分保证、且放行 NULL
            纯粹为保召回"时显式开启, 并在调用点注明理由。

    Returns:
        形如 ``(n.group_id = $group_id OR n.group_id STARTS WITH $group_prefix)``
        的 WHERE 片段。参数由 :func:`read_scope_params` 提供。

    Note:
        alias 由调用方以字面量传入 (非用户输入), 与 subjects.py 既有
        f-string 片段拼接约定同口径, 无注入面。
    """
    clauses = [
        f"{alias}.group_id = $group_id",
        f"{alias}.group_id STARTS WITH $group_prefix",
    ]
    if allow_null:
        clauses.insert(0, f"{alias}.group_id IS NULL")
    return "(" + " OR ".join(clauses) + ")"


def group_in_read_scope(candidate: Optional[str], scope: Optional[str]) -> bool:
    """内存侧的同语义判定 (与 :func:`read_group_filter` 逐字对应)。

    memory_service 的内存兜底 (``_episodes``)、failed_writes 回放等路径不
    走 Cypher, 但必须与 Cypher 侧**同一套**可见性规则, 否则 Neo4j 可用与
    降级两条路径给出不同的隔离结果。

    两侧一律先 ``to_physical_group_id()`` 再比较: 内存 episode 存的是逻辑
    格式 (``vault:v:board``), 库内是物理格式 (``vault__v__board``), 混比会
    静默失配 —— T1 契约踩过的原坑。

    Args:
        candidate: 待判定记录的 group_id (逻辑或物理格式)。
        scope: 当前读作用域 (逻辑或物理格式)。

    Returns:
        candidate 是否落在 scope 的可见面内。scope 为空 → False
        (无作用域不放行任何东西, fail-closed)。
    """
    if not scope or not str(scope).strip():
        return False
    if not candidate or not str(candidate).strip():
        # 无归属记录不属于任何 vault 的可见面 (与 allow_null=False 同口径)
        return False

    from app.graphiti.group_id_compat import to_physical_group_id

    cand_phys = to_physical_group_id(str(candidate).strip())
    scope_phys = to_physical_group_id(str(scope).strip())
    return cand_phys == scope_phys or cand_phys.startswith(
        scope_phys + _PHYSICAL_SEPARATOR
    )
