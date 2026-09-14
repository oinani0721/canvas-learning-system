"""Tests for BackgroundTaskManager — P0-2 multi-vault ContextVar inheritance.

回归 Story 2.5.Y 留下的串库风险:
``asyncio.create_task(coro)`` 不继承 ContextVar,导致 fire-and-forget background
task 内 ``get_current_subject_id()`` 返回默认值而非主任务的 vault_id.

修复:``BackgroundTaskManager.create_task`` 内用 ``contextvars.copy_context()``
snapshot 当前上下文,Python 3.11+ ``asyncio.create_task(coro, context=ctx)``
原生支持.
"""

import asyncio

import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def _reset_manager():
    from app.services.background_task_manager import BackgroundTaskManager

    BackgroundTaskManager.reset_instance()
    yield
    BackgroundTaskManager.reset_instance()


class TestContextVarInheritance:
    """P0-2 hotfix — background task 必须继承 caller 的 ContextVar."""

    @pytest.mark.asyncio
    async def test_create_task_inherits_contextvar(self):
        """主任务 set vault_C → fire-and-forget background task → background task
        内 get_current_subject_id() == vault_C (而非默认值)."""
        from app.core.subject_config import (
            _current_subject_id,
            get_current_subject_id,
        )
        from app.services.background_task_manager import BackgroundTaskManager

        manager = BackgroundTaskManager.get_instance()

        captured: dict = {}
        observed = asyncio.Event()

        async def background_work():
            # 这里如果没继承 ContextVar, 会拿到 DEFAULT_SUBJECT_ID
            captured["subject_id"] = get_current_subject_id()
            observed.set()
            return "ok"

        # 主上下文设 vault_C
        token = _current_subject_id.set("vault_C_test")
        try:
            task_id = await manager.create_task("test", background_work)
        finally:
            _current_subject_id.reset(token)

        # 等 background task 执行完
        await asyncio.wait_for(observed.wait(), timeout=2.0)

        # 主上下文已经 reset,但 background task 应保留它启动时的 snapshot
        assert captured.get("subject_id") == "vault_C_test", (
            f"P0-2 violation: background task 没继承 ContextVar, "
            f"实际 subject_id={captured.get('subject_id')}"
        )

        # task 应正常完成
        info = manager.get_task_status(task_id)
        # 给一点时间让 wrapped_task 走到 COMPLETED 状态(observed.set 之后还有
        # task_info 状态更新代码)
        for _ in range(20):
            if info.status.value == "completed":
                break
            await asyncio.sleep(0.01)
            info = manager.get_task_status(task_id)
        assert info.status.value == "completed"
        assert info.result == "ok"

    @pytest.mark.asyncio
    async def test_create_task_with_different_contextvars(self):
        """两个 background task 在不同主上下文下创建,各自保留独立 vault_id."""
        from app.core.subject_config import (
            _current_subject_id,
            get_current_subject_id,
        )
        from app.services.background_task_manager import BackgroundTaskManager

        manager = BackgroundTaskManager.get_instance()

        results: dict[str, str] = {}
        done_a = asyncio.Event()
        done_b = asyncio.Event()

        async def work_a():
            # 模拟 background 内做一些异步活儿
            await asyncio.sleep(0.05)
            results["a"] = get_current_subject_id()
            done_a.set()

        async def work_b():
            await asyncio.sleep(0.02)
            results["b"] = get_current_subject_id()
            done_b.set()

        # 在 vault_A 上下文起 task A
        token_a = _current_subject_id.set("vault_A_iso")
        try:
            await manager.create_task("test_a", work_a)
        finally:
            _current_subject_id.reset(token_a)

        # 在 vault_B 上下文起 task B
        token_b = _current_subject_id.set("vault_B_iso")
        try:
            await manager.create_task("test_b", work_b)
        finally:
            _current_subject_id.reset(token_b)

        # 两个 task 都在主上下文 reset 之后才真正跑(asyncio.sleep)
        await asyncio.wait_for(done_a.wait(), timeout=2.0)
        await asyncio.wait_for(done_b.wait(), timeout=2.0)

        assert results["a"] == "vault_A_iso", (
            f"task_a 应保留 vault_A_iso, 实际={results['a']}"
        )
        assert results["b"] == "vault_B_iso", (
            f"task_b 应保留 vault_B_iso, 实际={results['b']}"
        )

    @pytest.mark.asyncio
    async def test_default_contextvar_propagates(self):
        """无显式 set 时 background task 应拿到 DEFAULT_SUBJECT_ID."""
        from app.core.subject_config import (
            DEFAULT_SUBJECT_ID,
            _current_subject_id,
            get_current_subject_id,
        )
        from app.services.background_task_manager import BackgroundTaskManager

        manager = BackgroundTaskManager.get_instance()

        captured: dict = {}
        observed = asyncio.Event()

        async def work():
            captured["subject_id"] = get_current_subject_id()
            observed.set()

        # 显式 reset 到 default
        token = _current_subject_id.set(DEFAULT_SUBJECT_ID)
        try:
            await manager.create_task("test_default", work)
        finally:
            _current_subject_id.reset(token)

        await asyncio.wait_for(observed.wait(), timeout=2.0)
        assert captured["subject_id"] == DEFAULT_SUBJECT_ID


class TestCleanupScheduler:
    """CARD-TAIL-CLEANUP-LOOP [BATCH-2026-09-11-第十四批] — 清理调度器不得退化为忙循环.

    T-new-4 真缺陷: ``cleanup_loop`` 的 ``while True`` 里唯一的 yield 点是
    ``await asyncio.sleep(settings.TASK_CLEANUP_INTERVAL_SECONDS)``, 而 ``Settings``
    上**没有**这个字段 ⇒ 参数求值发生在 ``await`` 执行**之前**、直接抛
    ``AttributeError`` → 被 ``except Exception`` 接住 → 无等待立刻回到循环顶
    ⇒ 整个清理调度退化成 CPU 紧循环 (从不交还事件循环)。

    两条测试各钉住修复的一半:
    - A 正常路径: 循环顶 sleep 真的拿到配置间隔, 走到 cleanup_old_tasks, **并继续下一轮**;
    - B 异常路径: ``except Exception`` 分支**就地 await 一个 > 0 的等待**再回循环顶,
      且失败恢复后**循环仍在周期运行**。

    ⚠️ 每个测试的**首行**是 ``assert hasattr(settings, ...)`` fail-fast 守卫, 必须
    排在任何 ``start_cleanup_scheduler()`` 之前。原因: 在**未修**的代码上真驱动
    ``cleanup_loop`` 会卡死事件循环 (try 块内无 yield 点), 拿不到可判定的 FAILED,
    只会 hang; 有守卫才能在改前得到「秒级返回的干净 FAILED」。别把守卫挪到后面。

    ⚠️ 终止靠 spy 抛 ``asyncio.CancelledError`` (BaseException, 不会被
    ``except Exception`` 吞掉), **不靠墙钟**。``wait_for`` 的 timeout 只是防挂起的
    兜底网, 不是通过条件。

    ⚠️ spy 同时记 ``sleep-enter`` 与 ``sleep-exit`` 两个事件 —— 少了 exit 就分不出
    「就地 await 了等待」和「把等待丢进 create_task 后立刻回到循环顶」: 后者两个
    ``sleep-enter`` 会连着出现, 前者必是 enter/exit 成对。只数 sleep 次数看不出差别
    (Codex round-1 LOW-1 指出的门未覆盖的路径)。

    **本类不证明什么**(如实, 别当它证明了):
    - 不钉死异常分支的等待秒数**等于**配置间隔 —— 卡文契约是「> 0 即可, 车道可换用
      独立常量」, 所以这里刻意只断言 > 0; 值的取舍属移交事项, 不是门的漏洞。
    - 不证明真实定时器在高并发下的行为 (spy 拦截, 不走真实时间)。
    """

    @pytest.mark.asyncio
    async def test_cleanup_loop_sleeps_the_configured_interval(self, monkeypatch):
        """A 正常路径 — 循环顶 sleep 拿到配置间隔且 > 0, 进到清理, 并继续跑下一轮。"""
        assert hasattr(settings, "TASK_CLEANUP_INTERVAL_SECONDS"), "no field"

        from app.services.background_task_manager import BackgroundTaskManager

        # ⚠️ 必须在 monkeypatch 之前抓原件: spy 内部用它真让出一次事件循环。
        # 否则 spy 是「立即返回的协程」, 循环从不 yield, 下面 wait_for 的兜底网
        # 永远等不到调度 —— 那恰恰是本卡要修的忙循环形态。
        real_sleep = asyncio.sleep

        events: list[tuple[str, float]] = []
        enters: list[float] = []
        stop_after = 3  # S1 → cleanup → S2 → cleanup → S3(抛 Cancel) ⇒ 至少跑满两轮

        async def spy_sleep(delay, *args, **kwargs):
            enters.append(delay)
            events.append(("sleep-enter", delay))
            if len(enters) >= stop_after:
                # 落在循环顶 try 内 ⇒ 被 `except asyncio.CancelledError: break` 接住,
                # cleanup_loop 干净收尾, task 正常完成。
                raise asyncio.CancelledError
            await real_sleep(0)
            events.append(("sleep-exit", delay))

        manager = BackgroundTaskManager.get_instance()

        async def fake_cleanup(*args, **kwargs):
            events.append(("cleanup", 0))
            return 0

        monkeypatch.setattr(manager, "cleanup_old_tasks", fake_cleanup)
        monkeypatch.setattr(asyncio, "sleep", spy_sleep)

        await manager.start_cleanup_scheduler()
        cleanup_task = manager._cleanup_task
        assert cleanup_task is not None, "start_cleanup_scheduler 没有建出 _cleanup_task"
        await asyncio.wait_for(cleanup_task, timeout=5.0)

        interval = settings.TASK_CLEANUP_INTERVAL_SECONDS
        assert interval > 0, f"配置间隔必须 > 0, 否则 sleep(0) 仍是忙循环; 实测 {interval}"
        assert events[:3] == [("sleep-enter", interval), ("sleep-exit", interval), ("cleanup", 0)], (
            "第一轮必须是「进入循环顶 sleep(配置间隔) → 该 sleep 完成 → 进 cleanup_old_tasks」; "
            f"走到 cleanup 就证明取配置不再抛 AttributeError。实测事件序列 = {events}"
        )
        cleanups = [kind for kind, _ in events].count("cleanup")
        assert cleanups == 2, (
            "调度器必须**继续**周期运行: 本用例让 spy 在第 3 次进入 sleep 时才终止, "
            f"期间应完成 2 轮清理; 只有 1 轮说明循环在首轮后就退出了。实测 {cleanups} 轮, 序列 = {events}"
        )

    @pytest.mark.asyncio
    async def test_cleanup_loop_backs_off_after_exception(self, monkeypatch):
        """B 异常路径 — except Exception 分支就地 await 一个 > 0 的等待, 且之后循环继续。

        判据是**因果位置 + enter/exit 配对**, 不是数值: 等待复用同一个间隔, 所以
        「有没有等待」在数值上完全看不出来。看的是「抛异常那次清理」与「下一次清理」
        之间的 sleep 事件序列 ——
          就地 await:      enter/exit(异常分支) + enter/exit(循环顶) = 4 个事件
          没有等待:        enter/exit(循环顶)                        = 2 个事件
          丢进 create_task: 两个 enter 会连着出现, 不成对
        三种形态互不相同, 所以这条断言同时拦住「删掉等待」和「没有就地 await」。
        """
        assert hasattr(settings, "TASK_CLEANUP_INTERVAL_SECONDS"), "no field"

        from app.services.background_task_manager import BackgroundTaskManager

        real_sleep = asyncio.sleep

        events: list[tuple[str, float]] = []
        enters: list[float] = []
        # S1 → cleanup(抛) → 等待 → S2 → cleanup ok → S3 → cleanup ok → S4(抛 Cancel)
        # ⇒ 失败恢复后仍完成 2 轮清理; 若生产在 cleanup 后提前退出, 下面的 >= 2 断言会红。
        stop_after = 5

        async def spy_sleep(delay, *args, **kwargs):
            enters.append(delay)
            events.append(("sleep-enter", delay))
            if len(enters) >= stop_after:
                raise asyncio.CancelledError
            await real_sleep(0)
            events.append(("sleep-exit", delay))

        manager = BackgroundTaskManager.get_instance()
        cleanup_calls: list[int] = []

        async def flaky_cleanup(*args, **kwargs):
            cleanup_calls.append(1)
            if len(cleanup_calls) == 1:
                events.append(("cleanup-raise", 0))
                raise RuntimeError("对照输入: 让本轮清理失败一次")
            events.append(("cleanup-ok", 0))
            return 0

        monkeypatch.setattr(manager, "cleanup_old_tasks", flaky_cleanup)
        monkeypatch.setattr(asyncio, "sleep", spy_sleep)

        await manager.start_cleanup_scheduler()
        cleanup_task = manager._cleanup_task
        assert cleanup_task is not None, "start_cleanup_scheduler 没有建出 _cleanup_task"
        # gather(return_exceptions=True): 万一 Cancel 落在异常分支的等待里(在 except 块内),
        # 它不会被 `except asyncio.CancelledError` 接住而是穿出协程 —— 这里一并容纳。
        outcome = await asyncio.wait_for(asyncio.gather(cleanup_task, return_exceptions=True), timeout=5.0)
        assert not isinstance(outcome[0], Exception), f"cleanup_loop 不应以业务异常收尾(取消除外), 实测 {outcome[0]!r}"

        kinds = [kind for kind, _ in events]
        assert "cleanup-raise" in kinds, f"没驱动到「清理抛异常」那一步, 实测 = {events}"
        raise_at = kinds.index("cleanup-raise")
        after_raise = kinds[raise_at + 1 :]
        assert "cleanup-ok" in after_raise, f"异常之后没有回到下一轮清理, 实测 = {events}"
        between = after_raise[: after_raise.index("cleanup-ok")]
        assert between == ["sleep-enter", "sleep-exit", "sleep-enter", "sleep-exit"], (
            "except Exception 分支必须**就地 await** 一个等待(enter/exit 成对), 再经循环顶 sleep "
            "才进下一轮清理 —— 共 4 个 sleep 事件。少于 4 个 = 异常分支没等待(错误会被立刻重试); "
            "两个 enter 连着 = 等待没有被就地 await。⚠️ 注意: 这不等于说少了它就恢复成原先那个"
            "「不交还事件循环」的忙循环 —— 循环顶的 sleep 仍会让出; 本条钉的是「异常路径必须等待」"
            f"这条约定本身。实测异常与下一轮清理之间 = {between}; 完整序列 = {events}"
        )
        backoff_delay = events[raise_at + 1][1]
        assert backoff_delay > 0, f"异常分支的等待秒数必须 > 0, 否则等于没等待; 实测 {backoff_delay}"
        recovered = after_raise.count("cleanup-ok")
        assert recovered >= 2, (
            "失败恢复后调度器必须**继续**周期运行: spy 在第 5 次进入 sleep 才终止, "
            f"期间应至少完成 2 轮成功清理; 实测 {recovered} 轮, 序列 = {events}"
        )
