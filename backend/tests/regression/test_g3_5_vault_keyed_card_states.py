"""CARD-G3-5 回归门 — FSRS 投影状态的 vault 维度（双 vault 同名 concept 不撞键）。

[BATCH-2026-09-07-第十三批 / CARD-G3-5]

背景（卡文 §〇 实测）：`review_service._card_states` 原本以**裸 `concept_id`**
为键，落盘 `backend/data/fsrs_card_states.json` 也是扁平 `{concept_id: card}`。
两个 vault 的同名 concept 因此撞同一条内存记录与同一个 JSON 键，**后写覆盖先写**。

本门锁的是键化后的三条不变量：
  1. 同一 `concept_id` 在两个 vault 下各自独立存活，互不覆盖（d4 核心）；
  2. 落盘 JSON 是 `{vault_id: {concept_id: card}}` **嵌套**形态，
     不是分隔符拼接的复合键字符串（d1）；
  3. vault 作用域解析不出来时 **fail-closed**：不推进投影、记 logger.error
     （d2）—— 本条同时是负控 N2 的靶子，拆掉守卫它必须变红。

作用域注入走 `set_current_subject_id(build_vault_group_id(vid))`，与生产
请求路径（`review.py::_resolve_vault_group_id` → `set_current_subject_id`）同源。
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest


# ═══════════════════════════════════════════════════════════════════════════
# fixtures
# ═══════════════════════════════════════════════════════════════════════════


@contextmanager
def vault_scope(vault_id: str):
    """把 per-request 作用域切到 `vault_id`，退出时还原。

    与生产注入点同源：`review.py::_resolve_vault_group_id` 末行调的就是
    `set_current_subject_id(<D16 group_id>)`（`vault_scope._inject` 同形）。
    """
    from app.core.subject_config import (
        build_vault_group_id,
        get_current_subject_id,
        set_current_subject_id,
    )

    prev = get_current_subject_id()
    set_current_subject_id(build_vault_group_id(vault_id))
    try:
        yield
    finally:
        set_current_subject_id(prev)


@pytest.fixture
def states_file(tmp_path, monkeypatch):
    """把投影文件隔离到 tmp_path —— 禁写车道树 backend/data/（卡文 (i) 零写门）。"""
    target = tmp_path / "fsrs_card_states.json"
    monkeypatch.setattr("app.services.review_service._CARD_STATES_FILE", target, raising=True)
    return target


@pytest.fixture
def svc(states_file):
    """ReviewService，FSRS manager 用替身 —— 本门只证键化，不证调度算法。"""
    from app.services.review_service import ReviewService

    fsrs = MagicMock()
    canvas = MagicMock()
    canvas.get_canvas = AsyncMock(return_value={"nodes": [], "edges": []})
    return ReviewService(
        canvas_service=canvas,
        task_manager=MagicMock(),
        fsrs_manager=fsrs,
    )


CONCEPT_ID = "共享概念-shared-concept"
CARD_A = '{"stability": 1.5, "vault": "A"}'
CARD_B = '{"stability": 9.9, "vault": "B"}'


# ═══════════════════════════════════════════════════════════════════════════
# d4 — 双 vault 同名 concept 不撞键（本门核心）
# ═══════════════════════════════════════════════════════════════════════════


class TestTwoVaultsSameConceptId:
    @pytest.mark.asyncio
    async def test_second_vault_write_does_not_clobber_first(self, svc):
        """vault_b 写同名 concept 后，vault_a 的那条必须原样还在。

        键化前：两次写命中同一个裸键 `CONCEPT_ID`，vault_a 读回 CARD_B。
        """
        with vault_scope("vault_a"):
            assert await svc._save_card_states(pending=(CONCEPT_ID, CARD_A)) is True
        with vault_scope("vault_b"):
            assert await svc._save_card_states(pending=(CONCEPT_ID, CARD_B)) is True

        with vault_scope("vault_a"):
            got_a = await svc.load_card_state(CONCEPT_ID)
        with vault_scope("vault_b"):
            got_b = await svc.load_card_state(CONCEPT_ID)

        assert got_a == CARD_A, (
            f"vault_a 的投影被 vault_b 的同名 concept 覆盖了 —— 这正是 G3-5 要修的撞键缺陷 (读回 {got_a!r})"
        )
        assert got_b == CARD_B, f"vault_b 应读回自己那条, 实得 {got_b!r}"

    @pytest.mark.asyncio
    async def test_one_vault_cannot_see_the_other(self, svc):
        """只有 vault_a 写过时，vault_b 必须读不到（隔离方向的反面）。"""
        with vault_scope("vault_a"):
            assert await svc._save_card_states(pending=(CONCEPT_ID, CARD_A)) is True

        with vault_scope("vault_b"):
            leaked = await svc.load_card_state(CONCEPT_ID)

        assert leaked is None, f"vault_b 读到了 vault_a 的投影 {leaked!r} —— 跨 vault 泄漏"


# ═══════════════════════════════════════════════════════════════════════════
# d1 — 落盘形态是嵌套字典，不是拼接复合键
# ═══════════════════════════════════════════════════════════════════════════


class TestPersistedShapeIsNested:
    @pytest.mark.asyncio
    async def test_json_is_vault_nested_not_concatenated_key(self, svc, states_file):
        """落盘 JSON 顶层是 vault_id，二层才是 concept_id。

        禁分隔符拼接（如 `"vault_a:concept"`）：`concept_id` 是节点文件
        basename，可含任意分隔符字面量，拼接方案会让 `vault_a` 的键面吃掉
        `vault_ab` 的（同 `read_group_filter` 的 `__` 定界符教训）。
        """
        with vault_scope("vault_a"):
            assert await svc._save_card_states(pending=(CONCEPT_ID, CARD_A)) is True
        with vault_scope("vault_b"):
            assert await svc._save_card_states(pending=(CONCEPT_ID, CARD_B)) is True

        assert states_file.exists(), "投影文件应已落盘"
        data = json.loads(states_file.read_text(encoding="utf-8"))

        assert set(data.keys()) == {"vault_a", "vault_b"}, f"顶层键应是 vault_id 集合, 实得 {sorted(data.keys())!r}"
        assert data["vault_a"] == {CONCEPT_ID: CARD_A}
        assert data["vault_b"] == {CONCEPT_ID: CARD_B}

        # 反向断言：任何一层都不得出现拼接复合键
        for vault_id, bucket in data.items():
            assert isinstance(bucket, dict), f"{vault_id!r} 的值应是 concept 字典, 实得 {type(bucket).__name__}"
            for cid in bucket:
                assert cid == CONCEPT_ID, f"二层键应是裸 concept_id, 实得 {cid!r} (疑似拼接复合键)"


# ═══════════════════════════════════════════════════════════════════════════
# d2 — 作用域解析不出来时 fail-closed（负控 N2 的靶子）
# ═══════════════════════════════════════════════════════════════════════════


class TestFailClosedWhenScopeUnresolved:
    @pytest.mark.asyncio
    async def test_write_is_not_advanced_when_scope_unresolved(self, svc, states_file, monkeypatch, caplog):
        """ContextVar 未注入且 active vault 推导被打断 ⇒ 不写投影 + logger.error。

        ⚠️ 判据取自 `require_read_group(None)` 抛 `VaultScopeUnresolved`，
        **不是** `current_vault_id()` —— 后者**不会主动拒绝**无 ContextVar 的
        情形（未注入时回落进程级 active vault，返回值里没有"解析不出来"的
        信号），拿"缺 ContextVar"当它的失败判据，那条分支永远走不到（假
        fail-closed，读契约 R4「静默退化」同族）。

        本用例是负控 N2 的靶子：拆掉 fail-closed 守卫后它必须变红。
        """
        from app.core import subject_config

        def _broken_derivation():
            raise RuntimeError("probe: active vault derivation broken")

        # 打断解析链两级：ContextVar 落到 DEFAULT，active vault 推导抛错。
        monkeypatch.setattr(subject_config, "get_current_subject_id", lambda: subject_config.DEFAULT_SUBJECT_ID)
        monkeypatch.setattr(subject_config, "default_vault_group_id", _broken_derivation)

        caplog.set_level(logging.ERROR, logger="app.services.review_service")
        persisted = await svc._save_card_states(pending=(CONCEPT_ID, CARD_A))

        assert persisted is False, (
            "作用域解析不出来时必须 fail-closed 返回 False —— 静默落进某个缺省桶等于把配置断裂伪装成写入成功"
        )
        assert not states_file.exists() or CONCEPT_ID not in states_file.read_text(encoding="utf-8"), (
            "fail-closed 时不得把投影写进文件"
        )
        assert any(
            "vault scope unresolved" in rec.message.lower() or "作用域" in rec.message
            for rec in caplog.records
            if rec.levelno >= logging.ERROR
        ), f"fail-closed 必须留下 logger.error 痕迹, 实得 {[r.message for r in caplog.records]!r}"


# ═══════════════════════════════════════════════════════════════════════════
# Codex r1 HIGH-1 —— 混合快照必须**逐条**分形态, 不能整体判
# ═══════════════════════════════════════════════════════════════════════════


class TestLoadMixedSnapshot:
    def test_already_migrated_bucket_is_not_downgraded_to_concept(self, svc):
        """混合快照 {"vaultA": {...}, "裸键": "卡"} 不得把 vaultA 桶当成 concept。

        整体判形态 (`all(isinstance(v, dict) ...)`) 时, 一条裸键就会让**已经迁好
        的桶**被降格成一个名叫 "vaultA" 的 concept, 其卡数据变成 dict。
        """
        from app.services.review_service import _VaultScopedCardStates

        raw = {
            "vault_already": {"c-migrated": '{"v":"old"}'},
            "c-legacy": '{"v":"flat"}',
        }
        states = _VaultScopedCardStates.from_persisted(raw)
        nested = states.to_nested()

        assert "vault_already" in nested, f"已迁桶被吃掉了: {nested!r}"
        assert nested["vault_already"] == {"c-migrated": '{"v":"old"}'}, f"已迁桶被降格成 concept: {nested!r}"
        # 裸键归进了当前作用域桶 (推定归属), 且没有污染已迁桶
        assert "c-legacy" not in nested["vault_already"]
        assert any("c-legacy" in bucket for k, bucket in nested.items() if k != "vault_already"), (
            f"legacy 裸键未被归入任何当前作用域桶: {nested!r}"
        )

    def test_legacy_does_not_overwrite_existing_bucket_entry(self, svc):
        """H3: 同名冲突时保留**桶内**那份(明确身份), legacy 那份不覆盖也不丢。

        反例形态: 当前作用域 A, 输入 {"A": {"c": "A-new"}, "c": "legacy-unknown"}。
        `bucket.update(legacy)` 会把 A.c 覆盖成推定归属的旧值, 下次落盘固化。
        用**推定**去覆盖**明确**是反的。
        """
        from app.services.review_service import _VaultScopedCardStates

        with vault_scope("vault_a"):
            states = _VaultScopedCardStates.from_persisted({"vault_a": {"c": "A-new"}, "c": "legacy-unknown"})
            nested = states.to_nested()

        assert nested["vault_a"]["c"] == "A-new", f"桶内明确身份的记录被推定归属的 legacy 覆盖了: {nested!r}"
        # ⛔ 本卡范围（用户 2026-09-09 裁定 ③）：冲突的那份 legacy **未载入**，
        # legacy 兼容（隔离区/保留键/多份候选）整体移交下一张卡。这里只锁住
        # 「不能用推定归属覆盖明确身份」这条 —— 磁盘上的原文件没被动过。
        assert set(nested.keys()) == {"vault_a"}, f"不应产生 vault_a 以外的顶层键: {nested!r}"

    def test_legacy_without_scope_is_fail_fast_not_silently_dropped(self, svc, monkeypatch):
        """作用域解析不出来时对 legacy 裸键 **fail-fast**，而不是"这次不加载"。

        Codex r2 H4：只"不加载"的话，下一次成功写入的全量快照会把这些 legacy 从
        磁盘**永久删除** —— fail-closed 变成静默删数据。拒绝构造则文件原样躺在
        磁盘上没人动它，数据零风险。

        ⛔ 本卡范围（用户 2026-09-09 裁定 ③）：legacy 兼容整体归下一张卡，本卡
        只保证「不丢」这条最小性质。
        """
        from app.core import subject_config
        from app.core.vault_scope import VaultScopeUnresolved
        from app.services.review_service import _VaultScopedCardStates

        def _broken():
            raise RuntimeError("probe: derivation broken at load time")

        real_get = subject_config.get_current_subject_id
        real_derive = subject_config.default_vault_group_id
        monkeypatch.setattr(subject_config, "get_current_subject_id", lambda: subject_config.DEFAULT_SUBJECT_ID)
        monkeypatch.setattr(subject_config, "default_vault_group_id", _broken)
        try:
            with pytest.raises(VaultScopeUnresolved):
                _VaultScopedCardStates.from_persisted({"orphan-c": "legacy-card"})
        finally:
            monkeypatch.setattr(subject_config, "get_current_subject_id", real_get)
            monkeypatch.setattr(subject_config, "default_vault_group_id", real_derive)

    def test_pure_nested_snapshot_is_loaded_as_is(self, svc):
        """纯嵌套快照原样载入, 不触发 legacy 归桶。"""
        from app.services.review_service import _VaultScopedCardStates

        raw = {"va": {"c1": "A"}, "vb": {"c1": "B"}}
        assert _VaultScopedCardStates.from_persisted(raw).to_nested() == raw


# ═══════════════════════════════════════════════════════════════════════════
# 迁移器行为门 —— Codex r1 HIGH-2 / HIGH-3 / HIGH-4
# ═══════════════════════════════════════════════════════════════════════════


def _migrator():
    """按路径加载迁移器 (scripts/ 不是包)。"""
    import importlib.util
    import sys
    from pathlib import Path as _P

    path = _P(__file__).resolve().parents[2] / "scripts" / ("migrate_fsrs_card_states_vault_key_g35.py")
    spec = importlib.util.spec_from_file_location("g35_migrator", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # 先注册再 exec —— 模块级 dataclass 自省会取 sys.modules[cls.__module__]
    sys.modules["g35_migrator"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestMigratorWriteGuards:
    def test_out_aliasing_file_is_refused_in_dry_run(self, tmp_path):
        """HIGH-2: `--dry-run --file X --out X` 会让报告覆盖输入 ⇒ 必须拒。"""
        m = _migrator()
        snap = tmp_path / "snap.json"
        snap.write_text(json.dumps({"c": "card"}), encoding="utf-8")
        before = snap.read_bytes()

        rc = m.main(["--dry-run", "--file", str(snap), "--out", str(snap)])

        assert rc == 2, "别名的 --out 必须被拒 (rc=2)"
        assert snap.read_bytes() == before, "输入快照被报告覆盖了 —— dry-run 非零写入"

    def test_out_pointing_at_live_file_is_refused(self, tmp_path, monkeypatch):
        """HIGH-2: `--out` 也要过现网闸, 不能只检查 `--file`。

        ⚠️ Codex r2 H5: **绝不能**把真实 `LIVE_CARD_STATES` 传给 `--out` —— 一旦
        被测守卫回归成放行, 这条门自己就会把现网投影覆写成统计报告 (缺陷显形时
        测试本身违反禁写现网边界)。改用 tmp 下的替身受保护文件, 与硬链接那条门
        同一隔离方式。
        """
        m = _migrator()
        snap = tmp_path / "snap.json"
        snap.write_text(json.dumps({"c": "card"}), encoding="utf-8")
        fake_live = tmp_path / "fake-live.json"
        fake_live.write_text(json.dumps({"live": "untouched"}), encoding="utf-8")
        before = fake_live.read_bytes()
        monkeypatch.setattr(m, "LIVE_CARD_STATES", fake_live)

        rc = m.main(["--dry-run", "--file", str(snap), "--out", str(fake_live)])
        assert rc == 2, "指向现网文件的 --out 必须被拒"
        assert fake_live.read_bytes() == before, "受保护文件被报告覆写了"

    def test_hardlink_of_live_file_is_refused(self, tmp_path):
        """HIGH-4: 硬链接与现网文件同 inode、路径不同 —— 闸必须认身份。

        用一个**本地**受保护文件做等价验证: 直接给现网文件建硬链接会污染现网面。
        这里把 `LIVE_CARD_STATES` 临时指到 tmp 下的一份文件, 再给它建硬链接。
        """
        m = _migrator()
        protected = tmp_path / "protected.json"
        protected.write_text(json.dumps({"c": "card"}), encoding="utf-8")
        link = tmp_path / "innocent-looking.json"
        os.link(protected, link)  # 同 inode, 不同路径

        original = m.LIVE_CARD_STATES
        try:
            m.LIVE_CARD_STATES = protected
            refusal = m.assert_target_is_not_live(link)
        finally:
            m.LIVE_CARD_STATES = original

        assert refusal is not None, "硬链接与受保护文件同 inode, 闸必须拒 —— 纯路径比对会放行它"
        assert "inode" in refusal or "同一个文件" in refusal

    def test_write_failure_after_truncation_rolls_back(self, tmp_path, monkeypatch):
        """HIGH-3: 目标**已被截断之后**再失败, 必须回滚且以 rc=1 退出。

        ⚠️ Codex r2 M1: 旧写法在真正打开/截断之前就抛, 原文件从未损坏 —— 那样
        即使 `_restore()` 什么都不做也能通过。这里先把目标**真的截断成空**再抛,
        缺陷显形点才落在判据覆盖范围内。
        """
        m = _migrator()
        snap = tmp_path / "snap.json"
        snap.write_text(json.dumps({"c-legacy": "card"}), encoding="utf-8")

        real_write_text = type(snap).write_text

        def _truncate_then_boom(self, *a, **kw):
            if self == snap:
                real_write_text(self, "", encoding="utf-8")  # 真截断
                raise OSError("probe: disk full after truncation")
            return real_write_text(self, *a, **kw)

        monkeypatch.setattr(type(snap), "write_text", _truncate_then_boom)
        rc = m.main(["--apply", "--vault-id", "vx", "--file", str(snap)])

        assert rc == 1, f"截断后写失败应回滚并以 1 退出 (1=已回滚, 3=回滚也失败), 实得 {rc}"
        assert json.loads(snap.read_text(encoding="utf-8")) == {"c-legacy": "card"}, (
            "截断后未回滚到迁移前内容 —— 判据的核心就是这一条"
        )

    def test_encoding_failure_does_not_escape_rollback(self, tmp_path):
        """H2: lone surrogate 让 write_text 在截断后抛 UnicodeEncodeError(非 OSError)。

        只捕 OSError 时它会逃逸回滚: 目标已空, 却以 rc=1 退出 —— 直接推翻
        「rc=1 ⇒ 未写入或已安全回滚」。
        """
        m = _migrator()
        snap = tmp_path / "snap.json"
        snap.write_text('{"\\ud800": "{}"}', encoding="utf-8")
        assert json.loads(snap.read_text(encoding="utf-8"))  # 前提: 读得出

        rc = m.main(["--apply", "--vault-id", "vx", "--file", str(snap)])

        assert rc in (1, 3), f"编码失败必须走回滚路径 (1 或 3), 实得 {rc}"
        content = snap.read_text(encoding="utf-8")
        assert content.strip(), f"目标被截断成空且未还原: {content!r}"
        assert json.loads(content), "还原后的内容读不出来"

    def test_restore_failure_reports_rc3(self, tmp_path, monkeypatch):
        """HIGH-3 的另一半: 回滚**也失败**必须以 rc=3 退出, 与 rc=1 分得开。"""
        m = _migrator()
        snap = tmp_path / "snap.json"
        snap.write_text(json.dumps({"c-legacy": "card"}), encoding="utf-8")

        real_write_text = type(snap).write_text

        def _truncate_then_boom(self, *a, **kw):
            if self == snap:
                real_write_text(self, "", encoding="utf-8")
                raise OSError("probe: disk full after truncation")
            return real_write_text(self, *a, **kw)

        monkeypatch.setattr(type(snap), "write_text", _truncate_then_boom)

        real_copy2 = m.shutil.copy2
        calls = {"n": 0}

        def _copy2(src, dst, *a, **kw):
            calls["n"] += 1
            if calls["n"] > 2:  # 前两次是备份(须成功), 之后的还原调用失败
                raise OSError("probe: restore cannot write")
            return real_copy2(src, dst, *a, **kw)

        monkeypatch.setattr(m.shutil, "copy2", _copy2)
        rc = m.main(["--apply", "--vault-id", "vx", "--file", str(snap)])

        assert rc == 3, f"回滚失败必须以 3 退出 (与 1=已回滚 分开), 实得 {rc}"

    def test_backup_path_pointing_at_protected_file_is_refused(self, tmp_path, monkeypatch):
        """H1: 两条派生备份路径也必须过闸。

        反例 (Codex r2 H1): `--file` 是普通临时副本, 而 `<file>.json.bak` 本身
        已是受保护文件的硬链接 —— 只检查 --file / --out 时, 第二次 copy2 就把
        受保护文件覆写了。用 tmp 下的替身受保护文件构造 (不碰真现网)。
        """
        m = _migrator()
        protected = tmp_path / "protected.json"
        protected.write_text(json.dumps({"protected": "do-not-touch"}), encoding="utf-8")
        before = protected.read_bytes()
        monkeypatch.setattr(m, "LIVE_CARD_STATES", protected)

        snap = tmp_path / "h1.json"
        snap.write_text(json.dumps({"c-legacy": "card"}), encoding="utf-8")
        # 简单备份路径预置成受保护文件的硬链接 (同 inode, 不同路径)
        os.link(protected, snap.with_suffix(".json.bak"))

        rc = m.main(["--apply", "--vault-id", "vx", "--file", str(snap)])

        assert rc == 2, f"备份路径指向受保护文件时必须拒 (rc=2), 实得 {rc}"
        assert protected.read_bytes() == before, "受保护文件被备份写入覆写了"
        assert json.loads(snap.read_text(encoding="utf-8")) == {"c-legacy": "card"}, "被拒时不得改动输入"

    def test_stamped_backup_symlinked_to_out_is_refused(self, tmp_path, monkeypatch):
        """r4 M2: 时间戳备份是指向 `--out` 的符号链接时，静态命名检查抓不到。

        时间戳路径要到运行时才存在，故判据必须在生成它之后按解析后的真实路径复验。
        """
        m = _migrator()
        snap = tmp_path / "snap.json"
        snap.write_text(json.dumps({"c-legacy": "card"}), encoding="utf-8")
        report = tmp_path / "report.json"
        report.write_text("{}", encoding="utf-8")

        fixed_ts = "20260101_000000"

        class _FixedDatetime:
            @staticmethod
            def now():
                class _D:
                    @staticmethod
                    def strftime(fmt):
                        return fixed_ts

                return _D()

        monkeypatch.setattr(m, "datetime", _FixedDatetime)
        (tmp_path / f"snap.json.bak.{fixed_ts}").symlink_to(report)

        rc = m.main(["--apply", "--vault-id", "vx", "--file", str(snap), "--out", str(report)])
        assert rc == 2, f"时间戳备份与 --out 同指一处必须拒, 实得 rc={rc}"
        assert json.loads(snap.read_text(encoding="utf-8")) == {"c-legacy": "card"}, "被拒时源文件不得改动"

    def test_vault_id_with_colon_is_refused(self, tmp_path):
        """M3: 含冒号的 --vault-id 会写出 service 永远选不中的桶 ⇒ 必须拒。"""
        m = _migrator()
        snap = tmp_path / "snap.json"
        before = json.dumps({"c": "card"})
        snap.write_text(before, encoding="utf-8")

        rc = m.main(["--apply", "--vault-id", "vault_a:subject", "--file", str(snap)])

        assert rc == 2, "含冒号的桶键必须被拒 (消费端 split(':')[1] 取不到它)"
        assert snap.read_text(encoding="utf-8") == before, "被拒时不得改动输入"
