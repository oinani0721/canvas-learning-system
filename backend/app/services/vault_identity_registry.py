# Canvas Learning System - Vault Identity Registry
# P0-SYNC-ISO-2026-08-17 · R10 复审 P0-01
"""物理 group_id 的唯一身份注册表 — 堵死「非单射 vault 映射」损坏路径.

R10 复审 (ChatGPT/Codex 2026-08-17) 实测确认: sanitize_vault_id 是**有损
规范化** — 'CS 61B' / 'CS-61B' / 'cs_61b' 三个不同 filesystem vault 全部
落到同一个物理 group `vault__cs_61b`; '!!!' / '???' 等垃圾输入全部落
`vault__default`。碰撞发生时, 六条复合键 Cypher 依然无法区分两库, 跨
vault 覆盖/误删路径原样复活。

防御 (审查收官要求的「后端唯一注册」方案):
1. **默认桶封死**: 规范化坍缩到 'default' 的输入 (除非 raw 本来就叫
   default) 一律拒绝 — 垃圾名不允许写入任何桶。
2. **首claim绑定**: 每个物理 group 由第一个使用它的 raw 身份认领
   (Neo4j `:VaultIdentity` 节点, physical_gid 唯一约束兜并发)。
3. **碰撞 fail-closed**: 后来者 raw 身份 (NFKC+casefold 归一后) 与
   认领者不同 → VaultIdentityCollisionError, 上层转 409, 拒绝写入。

raw 身份比较用 NFKC+casefold+strip 归一 — 同一 vault 经 APFS NFD/NFC
差异不误报碰撞; 'CS 61B' vs 'CS-61B' 这类真碰撞必报。

[Source: _bmad-output/审查/2026-08-17-Codex对抗审查-R10第一批次实际成果.md P0-01]
"""

from __future__ import annotations

import unicodedata

import structlog
from neo4j import AsyncDriver, AsyncGraphDatabase

from app.config import get_settings

logger = structlog.get_logger(__name__)

# 注册表自身的唯一约束 (MERGE 并发竞态兜底), ensure 一次后进程内不再重发
_REGISTRY_CONSTRAINT = (
    "CREATE CONSTRAINT vault_identity_gid_unique IF NOT EXISTS FOR (v:VaultIdentity) REQUIRE v.physical_gid IS UNIQUE"
)

_CLAIM_QUERY = """
MERGE (v:VaultIdentity {physical_gid: $physical_gid})
ON CREATE SET v.raw_name = $raw_name,
              v.registered_at = datetime()
RETURN v.raw_name AS owner
"""


class VaultIdentityError(Exception):
    """Base — vault 身份无法安全绑定到物理 group."""


class VaultIdentityUnresolvableError(VaultIdentityError):
    """输入规范化后坍缩到 default 桶 — 不允许任何写入落进去."""


class VaultIdentityCollisionError(VaultIdentityError):
    """两个不同 raw 身份规范化到同一物理 group — fail closed."""


def _normalize_raw(raw: str) -> str:
    """身份比较基准: NFKC (APFS NFD/NFC 兼容) + casefold + strip."""
    return unicodedata.normalize("NFKC", raw).casefold().strip()


class VaultIdentityRegistry:
    """physical_gid → 首个认领 raw 身份的注册表 (Neo4j 持久 + 进程内缓存)."""

    def __init__(self) -> None:
        self._driver: AsyncDriver | None = None
        self._constraint_ensured = False
        # 进程内正向缓存: physical_gid -> normalized owner raw name。
        # 身份不可变, 无需 TTL; 碰撞判定可零 DB 往返。
        self._owner_cache: dict[str, str] = {}

    async def _get_driver(self) -> AsyncDriver:
        if self._driver is None:
            settings = get_settings()
            self._driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
        return self._driver

    async def close(self) -> None:
        if self._driver is not None:
            await self._driver.close()
            self._driver = None

    async def assert_identity(self, *, raw_vault_id: str, physical_gid: str) -> None:
        """校验 (raw 身份, 物理 group) 绑定; 违规抛异常, 通过则静默.

        Raises:
            VaultIdentityUnresolvableError: 垃圾输入坍缩 default 桶。
            VaultIdentityCollisionError: 物理 group 已被其他 raw 身份认领。
        """
        from app.config import sanitize_vault_id

        normalized_raw = _normalize_raw(raw_vault_id)

        # 防线 1: 默认桶封死 — sanitize 坍缩到 'default' 说明 raw 不含
        # 任何可用字符 (纯符号/空串), 不允许它认领任何桶。
        if sanitize_vault_id(raw_vault_id) == "default" and normalized_raw != "default":
            raise VaultIdentityUnresolvableError(
                f"vault_id {raw_vault_id!r} 规范化后无可用身份字符 "
                "(坍缩 default 桶), 拒绝写入 — 请使用含字母/数字的 vault 名"
            )

        # 防线 2+3: 首claim绑定 + 碰撞 fail-closed
        cached_owner = self._owner_cache.get(physical_gid)
        if cached_owner is not None:
            if cached_owner != normalized_raw:
                raise VaultIdentityCollisionError(
                    f"物理 group {physical_gid!r} 已被 vault "
                    f"{cached_owner!r} 认领, 拒绝 {raw_vault_id!r} 共用 "
                    "(有损规范化碰撞 — 请改 vault 名或人工迁移)"
                )
            return

        driver = await self._get_driver()
        settings = get_settings()
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            if not self._constraint_ensured:
                await session.run(_REGISTRY_CONSTRAINT)
                self._constraint_ensured = True
            result = await session.run(
                _CLAIM_QUERY,
                physical_gid=physical_gid,
                raw_name=normalized_raw,
            )
            record = await result.single()

        owner = record["owner"] if record else None
        if owner is None:
            # MERGE + RETURN 不可能空行; 空行=driver 降级/异常态, fail closed
            raise VaultIdentityError(f"vault identity claim for {physical_gid!r} returned no rows")
        if _normalize_raw(owner) != normalized_raw:
            raise VaultIdentityCollisionError(
                f"物理 group {physical_gid!r} 已被 vault {owner!r} 认领, "
                f"拒绝 {raw_vault_id!r} 共用 (有损规范化碰撞 — "
                "请改 vault 名或人工迁移)"
            )
        self._owner_cache[physical_gid] = _normalize_raw(owner)


_registry: VaultIdentityRegistry | None = None


def get_vault_identity_registry() -> VaultIdentityRegistry:
    """Singleton accessor."""
    global _registry
    if _registry is None:
        _registry = VaultIdentityRegistry()
    return _registry


async def cleanup_vault_identity_registry() -> None:
    """Shutdown hook."""
    global _registry
    if _registry is not None:
        await _registry.close()
        _registry = None
