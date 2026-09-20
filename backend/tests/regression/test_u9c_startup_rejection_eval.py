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
  2. **HTTP 层**（本文件 `TestHttpLayerMasksMessage`，**两条用例分测两个栈
     形态**）：都用真处理器 / 真中间件，无替身。
       - 只挂 `register_exception_handlers` ⇒ 消息被屏蔽（handler 契约）；
       - 加挂生产的真 `CORSExceptionMiddleware` ⇒ 体同样是泛化文案，产出方
         不同（`error_type` 键在 ⇒ 中间件产出）。
     ⚠️ **自 CARD-EXC-HANDLER-WIRE-REDACT（第十五批）起本条已翻转**：初版
     钉的两件事 ——「生产**从未调用** `register_exception_handlers`」与
     「中间件把消息原文送进 500 体」—— **都不再成立**。生产 `main.py` 现在
     以 `override_fastapi_defaults=False` 接线（保留 FastAPI 默认 422/`detail`），
     中间件 500 体也改成了泛化文案 + `error_type` + `bug_id`。两条用例现在
     方向一致，差别只剩产出方指纹。
  3. **工厂中段**（`get_review_service` 先建 memory / canvas / graphiti 依赖
     再到 `:2996`）：**本文件不覆盖** —— 真工厂会连 Neo4j / LanceDB，本卡
     硬边界禁连。该段由评估文档以只读证据覆盖，并在验收单
     「本卡未证明什么」如实登记。

**本文件替换了哪些真实现（如实全列，Codex r1 C 项整改）**：
  - `app.core.subject_config.get_current_subject_id` / `default_vault_group_id`
    —— 由 `_unresolved_vault_scope` 替换，目的是**制造**作用域解析失败这个
    被测前置条件（不是绕过被测逻辑）；两者在 `finally` 里显式还原。
  - `app.core.exception_handlers.bug_tracker` —— 只换**落盘路径**（指向 pytest
    临时目录），`log_error` 行为一行未改。
  除这三处外，被测链上的函数、处理器、中间件全是真实现。

**为什么不调 `get_review_service()`**：它在实例化 ReviewService **之前**先
`await get_memory_service()` / `CanvasService(...)` / `get_graphiti_temporal_client()`，
跑真工厂 = 连真服务（7691 面）。本文件改用最小 app + 真 `from_persisted`
作异常源，离线钉住「两个栈形态各自返回什么 + 进程不崩」这几条契约。
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

    本组**改前跑即绿**（零生产改动，钉的是既有行为）。判据的可判定性由
    `test_no_legacy_does_not_raise` 这条对照输入承担，但它的覆盖面是**有限的**
    ——只接得住「入口处 / legacy 分支之前」的无条件抛出，接不住 legacy 分支
    内部判定被改成恒真。完整的「谁接住什么」逐条列在该用例自己的 docstring 里。
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
        """负控（对照输入）：无 legacy 裸键时**不抛**，且数据原样载入。

        跑在与 `test_unresolved_scope_raise_carries_card_g3_5` **完全相同**的
        unresolved 环境里：它证明上面那条的抛出是「legacy 存在 + 归不掉」
        触发的，不是「作用域一解析不出来就抛」。

        ⚠️ **覆盖面如实（Codex r1 MEDIUM-2 整改，初稿措辞过强）**：
        初稿写「若有人把 fail-fast 改成无条件抛，本条必红」——**不成立**。
        纯嵌套输入在 `review_service.py:561` 的 `if not legacy: return cls(buckets)`
        就已返回，**根本到不了** `:565` 的作用域判定。Codex 以内存 AST 变异
        实测：把 `:565` 的 `if vault_id is None:` 改成 `if True:`，本条仍然通过。

        所以本条真正能检出的是：**在 `from_persisted` 入口处或 legacy 分支
        之前**新增的无条件抛出。它**不覆盖** legacy 分支内部判定被改成恒真
        的那一类变异。那一类由谁接住（逐条列，不留空白）：
          - `:565` 判定恒真 → 被本文件
            `test_clobbered_legacy_raise_carries_card_g3_5` 接住（该用例的
            作用域可解析，走的是 `:593` 同名分支，消息内容不同）；
          - `:589` 判定恒真 → 被既有同族
            `test_g3_5_vault_keyed_card_states.py::test_non_conflicting_legacy_is_adopted_normally`
            正控接住（有效作用域 + 不冲突 legacy 必须正常归桶）。

        不只断言「没抛」，还断言 `to_nested()` 原样回来 —— 「没抛但静默丢了
        数据」和「没抛且正常载入」是两回事，只断言前者会放过静默丢数据。
        """
        from app.services.review_service import _VaultScopedCardStates

        raw: Dict[str, Any] = {"vault_a": {"c1": "A"}}
        with _unresolved_vault_scope(monkeypatch):
            states = _VaultScopedCardStates.from_persisted(raw)

        assert states.to_nested() == raw


# ═══════════════════════════════════════════════════════════════════════════
# 层 2 — HTTP 层：CARD-G3-5 原文进不进 500 体，取决于哪一层接住
#          （仅 handler ⇒ 屏蔽；加生产中间件 ⇒ 原文进体。两条用例方向相反）
# ═══════════════════════════════════════════════════════════════════════════


def _build_probe_app(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
    raised: List[BaseException],
    *,
    with_production_middleware: bool = False,
) -> Any:
    """最小 app：真异常处理器 + 一条会抛的 probe 路由 + 一条存活路由。

    `with_production_middleware=True` 时额外挂上生产那条
    `CORSExceptionMiddleware`，用来对照「生产栈实际返回什么」。

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
    if with_production_middleware:
        # 复刻 main.py:757 的注册。它比 starlette 的 ServerErrorMiddleware
        # 更靠内，会先接住路由抛出的异常 —— 也就是先于 generic_exception_handler。
        #
        # ⚠️ 生产 main.py:751 的注释写「CORSExceptionMiddleware ← 最外层」是
        # **错的**：:757 之后还 add 了 Encoding(:762) / CORS(:767) / Metrics(:779)，
        # 后 add 的在更外层，实际从外到内是 Metrics → CORS → Encoding →
        # CORSException。它其实是**最内层**的 user middleware。这不影响本用例
        # （路由抛的异常它照样先接住），但「捕获所有未处理异常」这个说法过强。
        from app.main import CORSExceptionMiddleware

        app.add_middleware(CORSExceptionMiddleware)

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
    """请求期抛出 ⇒ 500 + 进程不崩；消息进不进响应体**取决于哪一层接住**。

    ⚠️ 类名里的 `MasksMessage` 是初稿遗留，**只描述下面第一条用例**；
    本类整体测的是两个**方向相反**的结果（见下表），不是单向的「屏蔽」。

    ⚠️ **口径更正（Codex r1 HIGH-1，本卡实测确认并加强）**：本类初稿断言
    「CARD-G3-5 被 `generic_exception_handler` 从响应体屏蔽」并把它当成生产
    表征 —— **那是错的**，错在「能力存在 ≠ 能力接上」：

      1. `register_exception_handlers` 在生产**从未被调用**。本树非测试命中
         只有 3 处，全在 `exception_handlers.py` 自身（定义 `:275` + docstring
         示例 `:294`/`:297`）。运行时自证：`app.main.app.exception_handlers`
         的键只有 `HTTPException` / `RequestValidationError` /
         `WebSocketRequestValidationError` —— **没有 `Exception`**。
         ⇒ `generic_exception_handler` 在生产 app 上这条路径是死代码。
      2. 即便它被注册，也轮不到它：`CORSExceptionMiddleware`
         （`main.py:634` 定义、`:757` 注册）的 `except Exception`（`:694`）
         会先接住，返回
         `{"code":500, "message": str(e)[:500], "error_type":..., "bug_id":...}`
         （`:738-741`；`safe_message` 在 `:709-715` 就是 `str(e)` 的 UTF-8
         round-trip，**无脱敏**）。

    ⇒ 第十四批的生产真实表征与该文件初稿**相反**：CARD-G3-5 原文会进 500 体。

    ⚠️ **第二次翻转（CARD-EXC-HANDLER-WIRE-REDACT，第十五批）**：上面两条
    「生产从未调用 `register_exception_handlers`」「中间件把原文送进体」
    **均已失效**。生产现在接线（`main.py` 调
    `register_exception_handlers(app, override_fastapi_defaults=False)`，
    运行期 `app.main.app.exception_handlers` 的键含
    `app.core.exceptions.CanvasException` 与 `Exception`），且
    `CORSExceptionMiddleware` 的 500 体改为 `"Internal server error"` +
    `error_type` + `bug_id`。⇒ 下面第二条用例的断言方向随之翻转
    （`..._redacts_message`）；`error_type` 作为**产出方指纹**的作用不变。

    ⚠️ 本类名里的 `MasksMessage` 是初稿留下的名字，**只对下面第一条用例成立**；
    类整体钉的是「**哪一层接住，就决定消息进不进响应体**」。改名会动到
    既有引用，故保留名字、在此写明语义。

    本类因此分两条用例，各自钉一层，并**各自证明自己测的是哪一层**：

    | 用例 | 栈形态 | 谁接住 | 响应体 |
    |---|---|---|---|
    | `..._handler_only_masks_message` | 只挂 handler | `generic_exception_handler` | 3 键，**无** `error_type`，消息被屏蔽 |
    | `..._production_stack_redacts_message` | 加挂真中间件 | `CORSExceptionMiddleware` | 4 键，**有** `error_type`，消息为泛化文案 |

    **`error_type` 是两层唯一的区分指纹**。初稿用「`code==500` + 存在
    `bug_id`」做排他判据是**无效的** —— 两层的 body 都有这两个键，它证明
    不了是谁产出的（Codex r1 HIGH-1 同条）。
    """

    def test_handler_only_stack_masks_message_and_does_not_crash(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """**仅挂 handler** 的栈：消息被屏蔽（这是 handler 契约，不是生产表征）。

        钉的是 `generic_exception_handler` 自身的行为契约 ——
        它**若**被接上，就不会把内部细节透出去（`:210` docstring 写明此意图）。
        生产当前没接它（见类 docstring），所以本条**不能**被引用为
        「用户看不到 CARD-G3-5」；那条由下面的生产栈用例给出，结论相反。

        ⚠️ 只断言「响应体里没有 CARD-G3-5」是**假绿面**：若 probe 因别的原因
        抛（拼错属性名、import 失败……），响应体同样不含该字符串，断言照过。
        故本条先断言路由捕获到的那个真实异常对象是 `VaultScopeUnresolved`
        且其 `str()` **含** CARD-G3-5 —— 确认消息真的产生了、且响应体里的
        缺席是**处理器屏蔽**的结果，不是消息压根没产生。

        **分层指纹**：断言 `error_type` **不在** body 里 —— 那是
        `CORSExceptionMiddleware` 独有的键。没有这条，本用例无法证明自己
        测到的是 handler 而不是别的什么东西产出的 500。

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
        # 分层指纹：中间件独有键必须缺席，否则接住它的不是 handler
        assert "error_type" not in body

        # ── handler 契约：原文被屏蔽，不进响应体 ──
        assert "CARD-G3-5" not in resp.text

        # ── 进程不崩：同一个 app 仍在服务后续请求 ──
        assert alive.status_code == 200
        assert alive.json() == {"alive": True}

    def test_production_stack_redacts_message_in_500_body(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
        """**生产栈形态**：真 `CORSExceptionMiddleware` 的 500 体只剩泛化文案。

        这条钉的是用户/运维在**当前**生产配置下实际看到的东西。

        ⚠️ **口径翻转（CARD-EXC-HANDLER-WIRE-REDACT，第十五批；评估文档议题 α
        按默认「脱敏」落地）**：本用例原名 `..._exposes_message_in_500_body`，
        断的是「CARD-G3-5 原文进 500 体」。该行为已被修复 ——
        `main.py` 的中间件体改成 `"Internal server error"` + `error_type` +
        `bug_id`，原文只留在服务端日志与 `bug_log.jsonl`。原用例 docstring
        写「若将来采纳议题 α，本条断言方向要重新裁定」，这就是那次裁定。

        本条现在钉住三件事：
          1. 中间件确实在 handler 之前接住（`error_type` 键在 ⇒ 产出方是中间件，
             这条指纹与翻转前一样重要：没有它，本用例证明不了自己测的是哪一层）；
          2. 体内**零原文** —— 不只查两个子串，而是拿异常自身的 `str()` 整段比
             （子串缺席证明不了脱敏，Codex r3 LOW-3 的原话反过来同样成立）；
          3. 进程照常服务后续请求。

        ⚠️ **不再覆盖的面（如实登记）**：翻转前这条用例顺带钉着
        `safe_message[:500]` 的截断口径（等式右侧的 `[:500]`）。原文不再进体后，
        该上限对响应体已无意义；「体有界 + 超长消息不进体」由
        `tests/unit/test_exception_handlers_wire.py::test_middleware_500_body_is_redacted_and_bounded`
        用 6000 字符消息覆盖（本文件不重复造那个样本）。
        """
        from fastapi.testclient import TestClient

        from app.core.vault_scope import VaultScopeUnresolved

        raised: List[BaseException] = []
        app = _build_probe_app(monkeypatch, tmp_path, raised, with_production_middleware=True)
        client = TestClient(app, raise_server_exceptions=False)

        with _unresolved_vault_scope(monkeypatch):
            resp = client.get("/_u9c_probe")
            alive = client.get("/_alive")

        # ── 异常侧：同一个真异常 ──
        assert len(raised) == 1
        assert isinstance(raised[0], VaultScopeUnresolved)

        # ── 响应侧：500，且分层指纹表明产出方是中间件而非 handler ──
        assert resp.status_code == 500
        body = resp.json()
        assert body["code"] == 500
        assert body["error_type"] == "VaultScopeUnresolved"
        assert "bug_id" in body

        # ── 自 CARD-EXC-HANDLER-WIRE-REDACT 起：体只剩泛化文案 ──
        assert body["message"] == "Internal server error"

        # ── 原文零泄漏：整段 str() 都不在响应文本里（不是只查两个子串）──
        assert str(raised[0]) not in resp.text
        assert "CARD-G3-5" not in resp.text
        assert "migrate_fsrs_card_states_vault_key_g35.py" not in resp.text

        # ── 进程不崩 ──
        assert alive.status_code == 200
        assert alive.json() == {"alive": True}
