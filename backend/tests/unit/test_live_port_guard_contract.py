"""live-port guard 的契约回归门（纯函数面 + 门在位自证）。

[BATCH-2026-09-01-第九批 / CARD-TEST-isolate-lifespan-R1]

⚠️ 本文件**刻意不发起任何连接**。门一旦拦下一次非豁免连接，整个 pytest 进程的
退出码就会被总账改成 3（这是门的设计），所以「在普通套件里真连一次看看拦不拦」
会把整条测试线染红。真实连接形态的证明放在
``backend/scripts/lifespan_isolation_guard_probes.py`` —— 每条都在独立子进程里跑，
父进程核对 rc 与唯一裁定行。这里只锁**判定逻辑**与**门在位**这两件不需要连接的事。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.support import live_port_guard as guard


class _StubItem:
    """``is_exempt`` 只用到 ``get_closest_marker`` 与 ``path`` 两个面。"""

    def __init__(self, path: Path, markers: set[str] | None = None) -> None:
        self.path = path
        self._markers = markers or set()

    def get_closest_marker(self, name: str):
        return object() if name in self._markers else None


class TestExtractPort:
    """端口提取必须覆盖 CPython socket 实际接受的全部端口形态。"""

    def test_ipv4_two_tuple(self):
        assert guard.extract_port(("127.0.0.1", 7691)) == 7691

    def test_ipv6_four_tuple(self):
        # 2026-09-01 实测 neo4j 驱动走的正是 IPv6 四元组；只认 len==2 会整条漏掉
        assert guard.extract_port(("::1", 7691, 0, 0)) == 7691

    def test_index_protocol_port_object(self):
        """CPython socket 接受任何实现 ``__index__`` 的端口对象（2026-09-03 实测连接成功）。

        旧实现用 ``isinstance(port, int)``，这类地址整条漏掉 = 门有洞。
        """

        class IndexPort:
            def __index__(self) -> int:
                return 7691

        assert guard.extract_port(("127.0.0.1", IndexPort())) == 7691

    def test_bool_is_index_able(self):
        assert guard.extract_port(("127.0.0.1", True)) == 1

    def test_str_port_is_not_index_able(self):
        assert guard.extract_port(("127.0.0.1", "7691")) is None

    def test_af_unix_address(self):
        assert guard.extract_port("/tmp/sock") is None

    def test_non_tuple(self):
        assert guard.extract_port(None) is None
        assert guard.extract_port(["127.0.0.1", 7691]) is None


class TestPortOfUri:
    """``assert_neo4j_target_blocked`` 的解析器：看不懂一律 None（调用方 fail-closed）。"""

    @pytest.mark.parametrize(
        "uri,expected",
        [
            ("bolt://localhost:7691", 7691),
            ("bolt://127.0.0.1:7687", 7687),
            ("neo4j+s://host.example:7473/db", 7473),
            ("bolt://user:pass@host:7691", 7691),  # userinfo 里的冒号不能当端口
            ("bolt://[::1]:7691", 7691),
            ("bolt://localhost", None),  # 没有端口
            ("bolt://user:pass@host", None),  # 只有 userinfo 冒号，无端口
            ("not-a-uri", None),
            ("bolt://host:notaport", None),
        ],
    )
    def test_parse(self, uri, expected):
        assert guard._port_of_uri(uri) == expected


class TestBlockedPortsContract:
    def test_live_ports_blocked_test_container_not(self):
        assert 7691 in guard.BLOCKED_PORTS
        assert 7687 in guard.BLOCKED_PORTS
        assert 7692 not in guard.BLOCKED_PORTS, "测试容器 7692 被拦会让真库门测试整条不可用"

    def test_test_uri_pointing_at_live_port_is_an_error(self, monkeypatch):
        monkeypatch.setenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7691")
        with pytest.raises(RuntimeError, match="受拦端口"):
            guard.assert_test_uri_not_blocked()

    def test_test_uri_on_container_port_is_fine(self, monkeypatch):
        monkeypatch.setenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7692")
        guard.assert_test_uri_not_blocked()


class TestExemption:
    def test_marker_exempts(self, tmp_path):
        item = _StubItem(tmp_path / "tests" / "x.py", {"integration"})
        exempt, why = guard.is_exempt(item, tmp_path / "tests")
        assert exempt and why == "marker:integration"

    def test_no_exempt_mode_overrides_marker(self, tmp_path, monkeypatch):
        """负控模式下豁免彻底关闭 —— 这个开关只会让门更严，不会更松。"""
        monkeypatch.setenv(guard.ENV_NO_EXEMPT, "1")
        item = _StubItem(tmp_path / "tests" / "x.py", {"integration"})
        exempt, why = guard.is_exempt(item, tmp_path / "tests")
        assert exempt is False and why == "no-exempt-mode"

    def test_absolute_path_containing_integration_is_not_exempt(self, tmp_path):
        """按相对化首段目录判定，不做整条路径 substring。"""
        tests_dir = tmp_path / "integration-lookalike" / "tests"
        target = tests_dir / "unit" / "x.py"
        target.parent.mkdir(parents=True)
        target.write_text("", encoding="utf-8")
        exempt, _ = guard.is_exempt(_StubItem(target), tests_dir)
        assert exempt is False


class TestGuardLiveness:
    """门在位：这几条在**当前正在跑的这个 pytest 进程**里自证。"""

    def test_audit_hook_round_trip(self):
        """承重 audit hook 的在位性是**跑出来的**，不是读一个布尔值。"""
        assert guard.audit_hook_alive() is True

    def test_assert_guard_live_passes(self):
        guard.assert_guard_live("unit test")

    def test_belt_identity_matches(self):
        import socket

        assert socket.socket.connect is guard._guarded_connect
        assert socket.socket.connect_ex is guard._guarded_connect_ex

    def test_uvloop_is_poisoned(self):
        import sys

        assert sys.modules.get("uvloop") is None, "uvloop 走 libuv，不触发 socket.connect 审计事件"

    def test_ledger_shape(self):
        led = guard.STATE.ledger()
        for key in ("total", "blocked", "advisory", "billed", "unaccounted", "reported_status", "installed"):
            assert key in led, f"账本缺字段 {key} —— 父进程复核会读它"
        assert led["installed"] is True
