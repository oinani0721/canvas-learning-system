"""R10 复审 P0-01 — vault 身份注册表行为测试.

背景 (审查实测): sanitize_vault_id 有损规范化非单射 — 'CS 61B'/'CS-61B'
/'cs_61b' 全落 vault__cs_61b, '!!!'/'???' 全落 vault__default。注册表
职责: 默认桶封死 + 首claim绑定 + 碰撞 fail-closed。
"""

from __future__ import annotations

from typing import Any

import pytest

from app.services.vault_identity_registry import (
    VaultIdentityCollisionError,
    VaultIdentityRegistry,
    VaultIdentityUnresolvableError,
)


class _FakeResult:
    def __init__(self, record: dict[str, Any] | None) -> None:
        self._record = record

    async def single(self) -> dict[str, Any] | None:
        return self._record


class _FakeSession:
    """模拟 MERGE ON CREATE 语义: gid 首次认领入 store, 之后返回原认领者."""

    def __init__(self, store: dict[str, str], calls: list[dict[str, Any]]) -> None:
        self._store = store
        self.calls = calls

    async def run(self, query: str, **params: Any) -> _FakeResult:
        self.calls.append({"query": query, "params": params})
        if "MERGE (v:VaultIdentity" in query:
            gid = params["physical_gid"]
            if gid not in self._store:
                self._store[gid] = params["raw_name"]
            return _FakeResult({"owner": self._store[gid]})
        return _FakeResult(None)  # CREATE CONSTRAINT 等

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *args: Any) -> None:
        return None


class _FakeDriver:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.calls: list[dict[str, Any]] = []

    def session(self, database: str | None = None) -> _FakeSession:
        return _FakeSession(self.store, self.calls)


def _make_registry() -> tuple[VaultIdentityRegistry, _FakeDriver]:
    reg = VaultIdentityRegistry()
    driver = _FakeDriver()
    reg._driver = driver  # type: ignore[assignment]
    return reg, driver


class TestDefaultBucketRejection:
    @pytest.mark.asyncio
    async def test_garbage_input_rejected(self) -> None:
        """'!!!' sanitize 坍缩 'default' → 拒绝, 且不发任何 DB 查询."""
        reg, driver = _make_registry()
        with pytest.raises(VaultIdentityUnresolvableError):
            await reg.assert_identity(raw_vault_id="!!!", physical_gid="vault__default")
        assert driver.calls == []

    @pytest.mark.asyncio
    async def test_literal_default_name_allowed(self) -> None:
        """vault 真叫 'default' 是合法身份, 走正常认领."""
        reg, _ = _make_registry()
        await reg.assert_identity(raw_vault_id="default", physical_gid="vault__default")


class TestFirstClaimBinding:
    @pytest.mark.asyncio
    async def test_new_gid_claimed_ok(self) -> None:
        reg, driver = _make_registry()
        await reg.assert_identity(raw_vault_id="CS 61B", physical_gid="vault__cs_61b")
        assert driver.store["vault__cs_61b"] == "cs 61b"  # NFKC+casefold 归一

    @pytest.mark.asyncio
    async def test_same_raw_repeat_ok_and_cached(self) -> None:
        """同一 raw 重复认领 → 通过; 第二次走进程内缓存零 DB 往返."""
        reg, driver = _make_registry()
        await reg.assert_identity(raw_vault_id="CS 61B", physical_gid="vault__cs_61b")
        claim_calls_before = len([c for c in driver.calls if "MERGE (v:VaultIdentity" in c["query"]])
        await reg.assert_identity(raw_vault_id="CS 61B", physical_gid="vault__cs_61b")
        claim_calls_after = len([c for c in driver.calls if "MERGE (v:VaultIdentity" in c["query"]])
        assert claim_calls_after == claim_calls_before  # 缓存命中

    @pytest.mark.asyncio
    async def test_case_and_nfkc_variants_not_false_collision(self) -> None:
        """'CS 61B' vs 'cs 61b' 是同一身份 (casefold) — 不误报碰撞."""
        reg, _ = _make_registry()
        await reg.assert_identity(raw_vault_id="CS 61B", physical_gid="vault__cs_61b")
        await reg.assert_identity(raw_vault_id="cs 61b", physical_gid="vault__cs_61b")


class TestCollisionFailClosed:
    @pytest.mark.asyncio
    async def test_different_raw_same_gid_rejected(self) -> None:
        """审查 P0-01 核心反例: 'CS 61B' 与 'CS-61B' 坍缩同一物理 group
        — 后来者必须被拒, 不许静默共桶."""
        reg, _ = _make_registry()
        await reg.assert_identity(raw_vault_id="CS 61B", physical_gid="vault__cs_61b")
        with pytest.raises(VaultIdentityCollisionError):
            await reg.assert_identity(raw_vault_id="CS-61B", physical_gid="vault__cs_61b")

    @pytest.mark.asyncio
    async def test_collision_detected_via_cache_without_db(self) -> None:
        """碰撞判定在缓存命中时零 DB 往返."""
        reg, driver = _make_registry()
        await reg.assert_identity(raw_vault_id="CS 61B", physical_gid="vault__cs_61b")
        calls_before = len(driver.calls)
        with pytest.raises(VaultIdentityCollisionError):
            await reg.assert_identity(raw_vault_id="CS-61B", physical_gid="vault__cs_61b")
        assert len(driver.calls) == calls_before

    @pytest.mark.asyncio
    async def test_persisted_owner_collision_without_cache(self) -> None:
        """跨进程场景: 认领在 DB 里 (缓存冷) — 仍必须报碰撞."""
        reg, driver = _make_registry()
        driver.store["vault__cs_61b"] = "cs 61b"  # 别的进程先认领
        with pytest.raises(VaultIdentityCollisionError):
            await reg.assert_identity(raw_vault_id="CS-61B", physical_gid="vault__cs_61b")
