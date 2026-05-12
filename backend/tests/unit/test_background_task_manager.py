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
