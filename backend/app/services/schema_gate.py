# Canvas Learning System - Canvas Schema Gate
# P0-SYNC-ISO-2026-08-17 · R10 复审 P2-02
"""启动/请求时的 Neo4j 约束在位校验 — 缺约束时写入 fail-closed.

R10 复审 P2-02: 部署链不会自动应用 migrations/003, 重建 volume 后不能
假设复合唯一约束存在 (本项目实测过一次: 001 从未在现网生效, SHOW
CONSTRAINTS 为空跑了数月)。缺约束时六条写 Cypher 的并发竞态失去数据库
层兜底 — 同 (group_id, id) 可能写出两份。

Gate 语义 (三态):
- **True (已验证齐全)**: 放行, 后续请求零开销。
- **False (确认缺失)**: /sync/batch 拒绝写入 (503 + 指明缺哪条 + 修法)。
- **None (未知 — DB 不可达/未验证)**: 不拦。理由: DB 不可达时写入自身
  就会 503, gate 重复拦截无增益; 只有「连上了且确认缺约束」才是 gate
  独有的信息, 才值得 fail closed。每次请求遇 None 会重试验证 (lazy)。

[Source: _bmad-output/审查/2026-08-17-Codex对抗审查-R10第一批次实际成果.md P2-02]
[Source: backend/migrations/003_canvas_group_isolation.cypher STEP 4]
"""

from __future__ import annotations

import structlog
from neo4j import AsyncDriver, AsyncGraphDatabase

from app.config import get_settings

logger = structlog.get_logger(__name__)

# migrations/003 STEP 4 建立的三条复合唯一约束 — 写侧隔离的数据库层兜底
REQUIRED_CANVAS_CONSTRAINTS: frozenset[str] = frozenset(
    {
        "canvasnode_group_id_unique",
        "canvasboard_group_id_unique",
        "canvasboard_group_subject_name_unique",
    }
)


class CanvasSchemaGate:
    """三态 gate: True=齐 / False=确认缺失 (拦写) / None=未知 (不拦, 重试)."""

    def __init__(self) -> None:
        self._driver: AsyncDriver | None = None
        self._verified: bool | None = None
        self._missing: frozenset[str] = frozenset()

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

    @property
    def verified(self) -> bool | None:
        return self._verified

    @property
    def missing(self) -> frozenset[str]:
        return self._missing

    async def verify(self) -> bool | None:
        """SHOW CONSTRAINTS 精确校验; 返回新的三态结果 (并缓存)."""
        try:
            driver = await self._get_driver()
            settings = get_settings()
            async with driver.session(database=settings.NEO4J_DATABASE) as session:
                result = await session.run("SHOW CONSTRAINTS")
                rows = await result.data()
            present = {row.get("name") for row in rows}
            missing = REQUIRED_CANVAS_CONSTRAINTS - present
            self._missing = frozenset(missing)
            self._verified = not missing
            if missing:
                logger.error(
                    "canvas_schema_gate_missing_constraints",
                    missing=sorted(missing),
                    hint=("run: python scripts/migrate_canvas_group_isolation.py --apply (migrations/003)"),
                )
            else:
                logger.info("canvas_schema_gate_ok", required=len(REQUIRED_CANVAS_CONSTRAINTS))
            return self._verified
        except Exception as e:  # noqa: BLE001 — DB 不可达 → 未知态, 不误拦
            logger.warning("canvas_schema_gate_verify_failed", error=str(e)[:200])
            self._verified = None
            return None

    async def block_reason(self) -> str | None:
        """写入前调用: 返回 None=放行, 返回文案=503 拒绝.

        未知态 (None) 每次重试验证 — 覆盖「启动时 DB 没起来, 之后起来了
        但 volume 是新建的 (零约束)」的窗口。
        """
        if self._verified is None:
            await self.verify()
        if self._verified is False:
            return (
                "Canvas schema constraints missing: "
                f"{sorted(self._missing)} — writes refused (data-integrity "
                "fail-closed). Apply migrations/003 via "
                "scripts/migrate_canvas_group_isolation.py --apply"
            )
        return None


_gate: CanvasSchemaGate | None = None


def get_canvas_schema_gate() -> CanvasSchemaGate:
    """Singleton accessor."""
    global _gate
    if _gate is None:
        _gate = CanvasSchemaGate()
    return _gate


async def cleanup_canvas_schema_gate() -> None:
    """Shutdown hook."""
    global _gate
    if _gate is not None:
        await _gate.close()
        _gate = None
