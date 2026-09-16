"""CARD-U9C-EVAL — U9-C「VaultScopeUnresolved 拒启」真实表征的口径钉。

[BATCH-2026-09-11-第十四批 / CARD-U9C-EVAL]

本文件钉的是**既有行为**（本卡零生产改动），目的是把 U9-C 原立面的三处
口径偏差固定成可回归的断言，后续若生产改动翻转其中任一条，这里必须同步翻。

**前提更正（本卡实测，见评估文档 §1）**：U9-C 原写「CLI/后台无 vault 上下文
构造 ReviewService ⇒ 拒启」不成立 —— `scripts/` 与 `backend/scripts/` 对
`ReviewService(` **0 命中**，生产唯一实例化点在 HTTP 依赖链
（`review_service.py:2996`，工厂 `get_review_service` `:2939` 内），且
`main.py` 的 lifespan 对 `get_review_service` / `ReviewService(` / `review_service`
三支交替 pattern **0 命中**。⇒ 真正的拒启面是**启动后首个命中
`get_review_service()` 的请求**，进程启动本身不崩。

**三层覆盖（防「为验 B 层 mock 掉 A 层」）**：

  1. **实例化层**（本文件 `TestConstructionLayerRaises`）：真
     `_VaultScopedCardStates.from_persisted` 在两条抛出点上真抛，断言消息
     携带 `CARD-G3-5` 前缀与迁移脚本指引。零 mock —— 被测函数是真的。
  2. **HTTP 层**（本文件 `TestHttpLayerMasksMessage`）：真
     `register_exception_handlers` 注册的真 `generic_exception_handler`，
     断言 500 响应体**屏蔽**了 CARD-G3-5 原文。零 mock —— 处理器是真的；
     唯一被替换的是 `bug_tracker` 的**落盘路径**（见该类 docstring），
     行为本身未被替换。
  3. **工厂中段**（`get_review_service` 先建 memory / canvas / graphiti 依赖
     再到 `:2996`）：**本文件不覆盖** —— 真工厂会连 Neo4j / LanceDB，本卡
     硬边界禁连。该段由评估文档以只读 grep 证据覆盖，并在验收单
     「本卡未证明什么」如实登记。

**为什么不调 `get_review_service()`**：它在实例化 ReviewService **之前**先
`await get_memory_service()` / `CanvasService(...)` / `get_graphiti_temporal_client()`，
跑真工厂 = 连真服务（7691 面）。本文件改用最小 app + 真 `from_persisted`
作异常源，离线钉住「屏蔽 + 进程不崩」这两条契约。
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator, List

import pytest

# ═══════════════════════════════════════════════════════════════════════════
# 作用域工具 —— 与 test_g3_5_vault_keyed_card_states.py 同源
# ═══════════════════════════════════════════════════════════════════════════


@contextmanager
def _unresolved_vault_scope(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """把 vault 作用域解析链打断，使 `_resolve_vault` 返 None。

    与 `test_g3_5_vault_keyed_card_states.py::
    test_legacy_without_scope_is_fail_fast_not_silently_dropped` 同款：
    `get_current_subject_id` 恒返回 `DEFAULT_SUBJECT_ID`（不带 vault 段）、
    `default_vault_group_id` 抛 —— 于是 `require_read_group(None)` 三级链
    全部落空，抛 `VaultScopeUnresolved`，`_resolve_vault` 捕获后返 None。

    ⚠️ 退出用**显式还原**而不是 `monkeypatch.undo()`：undo 会把同一个
    MonkeyPatch 实例上**别人**（如同测试内的落盘重定向）打的桩一起撤掉，
    那会让后续写入落回真实路径。
    """
    from app.core import subject_config

    def _broken() -> str:
        raise RuntimeError("probe: derivation broken at load time")

    real_get = subject_config.get_current_subject_id
    real_derive = subject_config.default_vault_group_id
    monkeypatch.setattr(
        subject_config,
        "get_current_subject_id",
        lambda: subject_config.DEFAULT_SUBJECT_ID,
    )
    monkeypatch.setattr(subject_config, "default_vault_group_id", _broken)
    try:
        yield
    finally:
        monkeypatch.setattr(subject_config, "get_current_subject_id", real_get)
        monkeypatch.setattr(subject_config, "default_vault_group_id", real_derive)


@contextmanager
def _vault_scope(vault_id: str) -> Iterator[None]:
    """把 per-request 作用域切到 `vault_id`，退出时还原。

    与生产注入点同源：`review.py::_resolve_vault_group_id` 末行调的就是
    `set_current_subject_id(<D16 group_id>)`。
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


# ═══════════════════════════════════════════════════════════════════════════
# 层 1 — 实例化层：两条抛出点的消息都要带 CARD-G3-5 + 迁移脚本指引
# ═══════════════════════════════════════════════════════════════════════════


class TestConstructionLayerRaises:
    """`from_persisted`（`review_service.py:521`）的两条 fail-fast 抛出点。

    两处均在 `ReviewService.__init__ :850 → _load_card_states :876 → :893`
    这条实例化链上，故「拒启」的源头在实例化期而不是请求逻辑期。

    本组**改前跑即绿**（零生产改动，钉的是既有行为）；判据的可判定性由
    `test_no_legacy_does_not_raise` 这条负控承担 —— 若把断言误写成无条件
    抛出，负控必红。
    """

    def test_unresolved_scope_raise_carries_card_g3_5(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """None 分支（`:570`）：作用域解析不出来 ⇒ 抛，且消息可运维。

        既有 `test_legacy_without_scope_is_fail_fast_not_silently_dropped`
        只断言「抛了」，不看消息内容。本条的增量 = 断言消息**能把人引到
        出路上**：`CARD-G3-5` 前缀（定位是哪张卡的契约）+ 迁移脚本文件名
        （给出解开拒启的具体动作）。
        """
        from app.core.vault_scope import VaultScopeUnresolved
        from app.services.review_service import _VaultScopedCardStates

        with _unresolved_vault_scope(monkeypatch):
            with pytest.raises(VaultScopeUnresolved) as ei:
                _VaultScopedCardStates.from_persisted({"orphan-c": "legacy-card"})

        message = str(ei.value)
        assert "CARD-G3-5" in message
        assert "migrate_fsrs_card_states_vault_key_g35.py" in message

    def test_clobbered_legacy_raise_carries_card_g3_5(self) -> None:
        """同名分支（`:593`）：作用域解析成功但 legacy 撞桶内 ⇒ 抛。

        ⚠️ 迁移脚本名在源码里是**跨两个字符串字面量拼接**的
        （`"...请先跑 backend/scripts/"` + `"migrate_..._g35.py 裁定归属。"`），
        单行 grep 找不到完整串，但运行时拼接后成立 —— 故这里连同拼接结果
        一起断言，防未来有人拆行时把指引拆断。
        """
        from app.core.vault_scope import VaultScopeUnresolved
        from app.services.review_service import _VaultScopedCardStates

        with _vault_scope("vault_a"):
            with pytest.raises(VaultScopeUnresolved) as ei:
                _VaultScopedCardStates.from_persisted({"vault_a": {"c": "A-new"}, "c": "legacy-unknown"})

        message = str(ei.value)
        assert "CARD-G3-5" in message
        assert "同名" in message
        assert "migrate_fsrs_card_states_vault_key_g35.py" in message

    def test_no_legacy_does_not_raise(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """负控（验伪锚，承重）：无 legacy 裸键时**不抛**，且数据原样载入。

        跑在与 `test_unresolved_scope_raise_carries_card_g3_5` **完全相同**的
        unresolved 环境里 —— 这是本条的全部承重之处：它证明上面那条的抛出是
        「legacy 存在 + 归不掉」触发的，不是「作用域解析不出来就无条件抛」。
        若哪天有人把 fail-fast 改成无条件抛（或把断言误写成无条件），本条必红。

        不只断言「没抛」，还断言 `to_nested()` 原样回来 —— 「没抛但静默丢了
        数据」和「没抛且正常载入」是两回事，只断言前者会放过静默丢数据。
        """
        from app.services.review_service import _VaultScopedCardStates

        raw: Dict[str, Any] = {"vault_a": {"c1": "A"}}
        with _unresolved_vault_scope(monkeypatch):
            states = _VaultScopedCardStates.from_persisted(raw)

        assert states.to_nested() == raw


# ═══════════════════════════════════════════════════════════════════════════
# 层 2 — HTTP 层：CARD-G3-5 原文被 generic_exception_handler 从 500 体屏蔽
# ═══════════════════════════════════════════════════════════════════════════


def _build_probe_app(monkeypatch: pytest.MonkeyPatch, tmp_path: Any, raised: List[BaseException]) -> Any:
    """最小 app：真异常处理器 + 一条会抛的 probe 路由 + 一条存活路由。

    **落盘重定向（不是行为替换）**：`generic_exception_handler` 会真调
    `bug_tracker.log_error(...)` 写 JSONL，而 `app.core.bug_tracker.bug_tracker`
    是模块级单例、`log_path` 默认 `"data/bug_log.jsonl"` **相对 CWD** ——
    pytest 从 `backend/` 跑，真写的就是车道树 `backend/data/bug_log.jsonl`。
    这里换掉 `exception_handlers` 命名空间里的**别名**，指向 `tmp_path`：
    与 `tests/conftest.py::_neo4j_live_port_guard` 对 `app.main` 的做法同型，
    同样**不碰** `app.core.bug_tracker` 单例本身（它的默认路径契约另有测试
    在锁）。换的是文件落点，`log_error` 的真实行为一行未改 —— 处理器仍然
    真跑完整条 bug 记账路径，本测试断言的那条链没有被 mock 掉。
    """
    from fastapi import FastAPI

    from app.core import exception_handlers
    from app.core.bug_tracker import BugTracker
    from app.services.review_service import _VaultScopedCardStates

    monkeypatch.setattr(
        exception_handlers,
        "bug_tracker",
        BugTracker(log_path=str(tmp_path / "bug_log.jsonl")),
    )

    app = FastAPI()
    exception_handlers.register_exception_handlers(app)

    @app.get("/_u9c_probe")
    def _probe() -> Dict[str, Any]:
        try:
            _VaultScopedCardStates.from_persisted({"orphan-c": "legacy-card"})
        except Exception as exc:  # 记下真实异常对象后原样重抛给处理器
            raised.append(exc)
            raise
        return {"unreachable": True}

    @app.get("/_alive")
    def _alive() -> Dict[str, Any]:
        return {"alive": True}

    return app


class TestHttpLayerMasksMessage:
    """请求期抛出 ⇒ 500 + 消息屏蔽 + 进程不崩（本卡关键发现）。

    `VaultScopeUnresolved` 是裸 `Exception` 子类（`vault_scope.py:359`）且
    **无专用处理器**，逸出后落到 `generic_exception_handler`
    （`exception_handlers.py:200` 定义、`:312` 以 `Exception` 注册），该处理器
    刻意不暴露内部细节：响应体恒为
    `{"code": 500, "message": "Internal server error", "bug_id": ...}`
    （`:262-266`）。CARD-G3-5 原文只进 `logger.error(error_message=...)` 与
    `bug_tracker.log_error(...)`。

    ⇒ U9-C 设计稿「请求 500 **带 CARD-G3-5 消息**」只对了一半：500 成立、
    进日志成立，**进 HTTP 响应体不成立**。本卡按实测钉口径，不改生产去暴露
    消息（那属评估文档 §5 议题 α，设计级、需用户裁）。
    """

    def test_unresolved_scope_surfaces_as_masked_500_not_crash(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """同一次请求里两侧同时钉：异常**含**消息、响应体**不含**消息。

        ⚠️ 只断言「响应体里没有 CARD-G3-5」是**假绿面**：若 probe 因别的原因
        抛（拼错属性名、import 失败……），响应体同样不含该字符串，断言照过。
        故本条先断言路由捕获到的那个真实异常对象是 `VaultScopeUnresolved`
        且其 `str()` **含** CARD-G3-5 —— 确认消息真的产生了、且响应体里的
        缺席是**处理器屏蔽**的结果，不是消息压根没产生。

        排他性：`code == 500` + 存在 `bug_id` 键共同证明这个 500 出自
        `generic_exception_handler`（`:262-266` 的 body 形状），不是 starlette
        的某个默认 500 页面。

        `raise_server_exceptions=False` 是必需的：否则 TestClient 会把异常
        重新抛进测试，拿不到响应体，也就看不到「被屏蔽成什么样」。
        """
        from fastapi.testclient import TestClient

        from app.core.vault_scope import VaultScopeUnresolved

        raised: List[BaseException] = []
        app = _build_probe_app(monkeypatch, tmp_path, raised)
        # 不用 `with TestClient(...)`：那会跑 lifespan。本 app 无 lifespan 需求，
        # 直接构造可避免任何 startup 副作用。
        client = TestClient(app, raise_server_exceptions=False)

        with _unresolved_vault_scope(monkeypatch):
            resp = client.get("/_u9c_probe")
            alive = client.get("/_alive")

        # ── 异常侧：消息确实产生了 ──
        assert len(raised) == 1
        assert isinstance(raised[0], VaultScopeUnresolved)
        assert "CARD-G3-5" in str(raised[0])

        # ── 响应侧：500，且形状确属 generic_exception_handler ──
        assert resp.status_code == 500
        body = resp.json()
        assert body["code"] == 500
        assert body["message"] == "Internal server error"
        assert "bug_id" in body

        # ── 关键发现：原文被屏蔽，不进响应体 ──
        assert "CARD-G3-5" not in resp.text

        # ── 进程不崩：同一个 app 仍在服务后续请求 ──
        assert alive.status_code == 200
        assert alive.json() == {"alive": True}
