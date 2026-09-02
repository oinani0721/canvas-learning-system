"""独立的 pytest 插件：尽早安装 7691 socket 门，不依赖根 conftest 的发现。

[BATCH-2026-09-01-第九批 / CARD-TEST-isolate-lifespan-R1]

为什么存在：负控脚本会在子进程里跑「摘掉 no_lifespan 的变异文件」——此时若只靠
根 conftest 装门，``--rootdir``/``--confcutdir``/``PYTEST_ADDOPTS`` 之类都能让
conftest 不被发现，门就静默缺席，变异运行会真连现网 7691（Codex round-1
BLOCKER）。本插件由负控用 ``-p tests.support.guard_plugin`` **显式点名加载**，
显式 ``-p`` 不受 rootdir/confcutdir 影响。

根 conftest 也会调用本插件对应的函数（幂等），保证一次 pytest 会话只有一份门。

**装门在 import 期，不在 ``pytest_configure``**（第八批 Codex MEDIUM）：
``-p`` 指定的插件在 pytest 启动早期被 import，而 ``pytest_configure`` 要等
autoload 插件、``PYTEST_PLUGINS`` 和 initial conftest 全部 import 完之后才跑 ——
那段「门前窗口」里任何 import 副作用发起的连接都不受保护。把 ``install()`` 放到
模块顶层，窗口收敛到「本模块被 import 的那一刻」。``pytest_configure`` 保留一次
幂等复核，用来发现「import 之后门被人拆了」。

本插件**只装门**，不做哨兵/汇总（那些留在根 conftest）——这样即使有人在绕过
conftest 的场景下跑测试，也不会得到「门缺席但哨兵也缺席 = 一切照常绿」的假象：
门在，connect 就会被拦。
"""

from __future__ import annotations

import pytest

from tests.support import live_port_guard

# ⚠️ import 期装门：早于 pytest_configure，把门前窗口收敛到本模块被 import 那一刻。
# ⚠️ 只装不卸：迟到线程在 unconfigure 后仍可能连库，先恢复 socket 会留下无账窗口
#    （Codex round-2 HIGH）。门随测试进程存活到退出。
live_port_guard.install()


def pytest_configure(config):
    # 幂等复核：install() 内部会走 assert_guard_live()，import 之后被拆掉的门在此暴露。
    live_port_guard.install()


@pytest.fixture(scope="session", autouse=True)
def _guard_plugin_session_asserts():
    """门在位自证（与根 conftest 的同名 fixture 断言一致；幂等双保险）。"""
    live_port_guard.assert_guard_live("guard_plugin session fixture")
    live_port_guard.assert_test_uri_not_blocked()
    yield
