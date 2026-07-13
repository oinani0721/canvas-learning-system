"""
Graphiti group_id compatibility shim.

Background:
    Canvas D16 group_id 规约 (Story 2.5.Y AC #2, locked 2026-05-05) uses
    colon-separated format: `vault:<vault_id>` / `vault:<vault_id>:<subject>`.

    Graphiti's upstream validation rejects any group_id containing characters
    outside `[A-Za-z0-9_-]`, which means **all Canvas group_ids fail Graphiti
    add_episode / search calls** with `GroupIdValidationError`.

    This compatibility shim sanitizes Canvas group_ids at the Graphiti API
    boundary (and only at the boundary). All Canvas business logic (Cypher
    queries, subject_config, memory_service writers/readers) continues to use
    the Canvas D16 format internally.

    Boundary locations (must call sanitize before passing to graphiti_core):
    - `episode_worker._process_task` → graphiti.add_episode(group_id=...)
    - `memory_service._search_graphiti` → graphiti.search_(group_ids=[...])
    - `memory_service._search_graphiti_legacy` → graphiti.search(group_ids=[...])

    Reverse direction: not currently needed — Canvas readers query
    Neo4j's EpisodicNode.source_description / node_id, not its group_id
    field (which is owned by Graphiti and stored in sanitized form).

Source:
    P0-5 (2026-05-14) — discovered after P0 三件套 + P0-4 schema fixes
    finally let GraphitiEpisodeWorker run to add_episode and hit the
    upstream group_id validator.
"""

import re

_GRAPHITI_SEPARATOR = "__"

#: M1-E2E 修复 (2026-07-13): graphiti_core validator 只收 [A-Za-z0-9_-],
#: 而 S27 决策"group_id 按白板名"使 canvas 段天然含中文 (特征值与特征向量)。
#: 结构化主链直写 Cypher 绕过 validator 从未暴露; 语义通道 add_episode
#: 一触即拒 (3 重试全挂)。修复采用 IDNA 同款方案 (RFC 3492): 非法段
#: punycode 编码 + xn-- 前缀 — 确定性、可逆、输出字母表恒合规。
#: 前提: 段由上游 sanitizer (NFKC + Unicode \w 折叠) 产出, 只含词字符;
#: 已编码段 (xn--*) 本身合规, sanitize 幂等。
_VALID_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_-]*$")
_PUNY_PREFIX = "xn--"


def _encode_segment(segment: str) -> str:
    """非法段 → xn--<punycode>; 合规段 (含已编码段) 原样返回。"""
    if _VALID_SEGMENT_RE.match(segment):
        return segment
    return _PUNY_PREFIX + segment.encode("punycode").decode("ascii")


def _decode_segment(segment: str) -> str:
    """xn-- 段 → 原文; 解码失败 (罕见: 真名恰为 xn--*) 原样返回。"""
    if not segment.startswith(_PUNY_PREFIX):
        return segment
    try:
        return segment[len(_PUNY_PREFIX) :].encode("ascii").decode("punycode")
    except (UnicodeError, ValueError):
        return segment


def sanitize_group_id_for_graphiti(canvas_group_id: str) -> str:
    """Convert Canvas D16 group_id to Graphiti-safe form.

    Examples:
        vault:cs_61b              → vault__cs_61b
        vault:cs_61b:algorithms   → vault__cs_61b__algorithms
        vault:cv:特征值与特征向量  → vault__cv__xn--<punycode> (可逆)
        vault:default             → vault__default
        cs188 (legacy, no colon)  → cs188 (unchanged)

    幂等: 已物理化/已编码输入再过一遍输出不变 (分隔符自适应 : 或 __)。

    Args:
        canvas_group_id: Canvas-side group_id in D16 format.

    Returns:
        Graphiti-safe equivalent (only [A-Za-z0-9_-] characters).
    """
    if not canvas_group_id:
        return canvas_group_id
    sep = ":" if ":" in canvas_group_id else _GRAPHITI_SEPARATOR
    return _GRAPHITI_SEPARATOR.join(
        _encode_segment(seg) for seg in canvas_group_id.split(sep)
    )


def desanitize_group_id_from_graphiti(graphiti_group_id: str) -> str:
    """Convert Graphiti-stored group_id back to Canvas D16 format.

    Inverse of `sanitize_group_id_for_graphiti` (含 xn-- 段 punycode 解码,
    中文白板名往返无损)。Useful when surfacing Graphiti's group_id back
    to Canvas-side code that expects D16 colons.

    Caveat: this splits on "__", which is unambiguous only if no Canvas
    group_id segment legitimately contains "__". D16 segments are
    vault_id / subject_id which use single underscores (cs_61b, not
    cs__61b), so this is safe under the current spec.
    """
    if not graphiti_group_id:
        return graphiti_group_id
    return ":".join(
        _decode_segment(seg) for seg in graphiti_group_id.split(_GRAPHITI_SEPARATOR)
    )


#: M2 双图隔离 (2026-07-13, 路线图 v2 / R3-Q1 对抗审查): 语义影子图后缀。
#: LLM 抽取产物绝不与结构化主图共享 group — graphiti 的 dedupe/invalidation
#: 以 group_id 为搜索边界, 隔离后跨路径污染在机制上不可能 (LLM 抽取实体
#: 不会被 resolve 到主图 uuid5 节点上, 也不会 invalidate 主图边)。
_SEMANTIC_SUFFIX = "semantic"


def semantic_group_id(group_id: str) -> str:
    """主图 group_id → 语义影子图 sibling group_id (逻辑 D16 形态)。

    任何经 LLM 抽取的内容 (add_episode 语义通道) 必须写入本函数返回的
    影子分组; 分组由服务端代码固定, 不暴露给任何调用方 (含 MCP 工具与
    hook 端点) — 即使提示词被污染也没有通路碰到主图。

    Examples:
        vault:canvas_vault   → vault:canvas_vault:semantic
        vault__canvas_vault  → vault__canvas_vault__semantic (物理形态输入)
        cs188 (legacy 裸值)  → cs188__semantic (无冒号即视为物理形态,
                               冒号后缀会被 graphiti validator 拒绝)
        已带 :semantic 后缀  → 原样返回 (幂等)
    """
    if not group_id:
        return group_id
    if group_id.endswith(f":{_SEMANTIC_SUFFIX}") or group_id.endswith(
        f"{_GRAPHITI_SEPARATOR}{_SEMANTIC_SUFFIX}"
    ):
        return group_id
    sep = ":" if ":" in group_id else _GRAPHITI_SEPARATOR
    return f"{group_id}{sep}{_SEMANTIC_SUFFIX}"


def to_physical_group_id(group_id: str) -> str:
    """任意来源 group_id → Neo4j 物理存储格式 (T1 统一, 2026-07-10 交接任务书).

    这是**唯一物理边界入口**: 一切直接读写 Neo4j group_id 属性的 Cypher
    (MERGE/SET/WHERE), 参数绑定前必须过本函数。物理规范 = 双下划线形态
    (`vault__cs_61b`), 因为 graphiti_core 上游 validator 拒绝冒号, 全图
    只能向 `__` 统一; D16 冒号格式仍是业务层/API 的逻辑规约不变。

    组合链: canonical_group_id (逻辑归一, deprecated 值映射 + WARNING)
    → sanitize_group_id_for_graphiti (冒号 → __)。

    幂等防御: canonical_group_id 会把已物理化的 `vault__x` 误判为未规范
    输入回旋成 `vault:vault__x` (再 sanitize = `vault__vault__x` 数据损坏),
    故检测到 `vault__` 前缀直接原样返回, 双重调用安全。

    Examples:
        vault:cs_61b        → vault__cs_61b
        vault__cs_61b       → vault__cs_61b   (幂等)
        cs188 (deprecated)  → vault__default  (canonical WARNING)
        CS 61B              → vault__cs_61b
    """
    if not group_id:
        return group_id
    if group_id.startswith(f"vault{_GRAPHITI_SEPARATOR}"):
        # M1-E2E (2026-07-13): 早退也过 sanitize — ASCII 输入幂等不变,
        # 中文物理历史形态 (vault__x__中文, 结构化直写产物) 收敛到 punycode。
        return sanitize_group_id_for_graphiti(group_id)
    # MEDIUM-1 防御 (T1 对抗审查 2026-07-10): canonical_group_id 对 vault:
    # 前缀输入直通、不做段级 sanitize — 若段内含 __ (如 .env 手写
    # vault:my__vault), sanitize 后 desanitize 会层级错乱 (vault:my:vault)。
    # 标准管线 (sanitize_vault_id / sanitize_subject_name 均折叠 _+) 不会
    # 产出这种值, 检测到即告警提示修配置。
    if group_id.startswith("vault:") and _GRAPHITI_SEPARATOR in group_id:
        import logging

        logging.getLogger(__name__).warning(
            "group_id %r contains '__' inside a vault: segment — "
            "desanitize roundtrip will be lossy; fix the source config "
            "(expected single underscores, e.g. from sanitize_vault_id)",
            group_id,
        )
    # Lazy import: core 层不反向依赖 graphiti 层, 无循环, 但保持与
    # config.py 相同的延迟加载姿势避免 Settings 初始化顺序问题。
    from app.core.subject_config import canonical_group_id

    return sanitize_group_id_for_graphiti(canonical_group_id(group_id))
