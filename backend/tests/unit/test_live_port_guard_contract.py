"""live-port guard 的契约回归门（纯函数面 + 门在位自证）。

[BATCH-2026-09-01-第九批 / CARD-TEST-isolate-lifespan-R1]

⚠️ 本文件**刻意不发起任何连接**。门一旦拦下一次非豁免连接，整个 pytest 进程的
退出码就会被总账改成 3（这是门的设计），所以「在普通套件里真连一次看看拦不拦」
会把整条测试线染红。真实连接形态的证明放在
``backend/scripts/lifespan_isolation_guard_probes.py`` —— 每条都在独立子进程里跑，
父进程核对 rc 与唯一裁定行。这里只锁**判定逻辑**与**门在位**这两件不需要连接的事。
"""

from __future__ import annotations

import ast
import inspect
import json
import textwrap
import threading
from pathlib import Path

import pytest

from tests.support import live_port_guard as guard


class _CustomBaseException(BaseException):
    """直接继承 ``BaseException`` 的自定义异常（``except Exception`` 捕不到）。"""


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

    @pytest.mark.parametrize("exc_type", [ValueError, RuntimeError])
    def test_index_raising_non_typeerror_is_fail_closed(self, exc_type):
        """``__index__`` 抛 ``TypeError`` 之外的异常 ⇒ 取端口必须**返回 None，不得抛**。

        ⛔ RV-C H-1a：``extract_port`` 上半段读底层槽位用的是 ``except Exception``
        （fail-closed），下半段 ``operator.index(raw)`` 却只捕 ``TypeError`` —— 同一个
        函数里两半口径不一致。``__index__`` 是**调用方给的任意用户代码**，抛
        ``ValueError`` / ``RuntimeError`` 时异常从这里逸出，越过 ``_audit_hook`` 里
        ``STATE.record()`` 那一行 ⇒ 连接确实被阻断了（异常传给调用方），账本却是零。
        与 round-1 HIGH-1（seam 抛异常跳过记账）是同一形态。

        地址用 tuple **子类**：neo4j 驱动自己的 ``Address`` 家族就是 tuple 子类，
        而门读的是底层槽位（见 ``extract_port`` 的说明）。
        """

        class _Addr(tuple):
            __slots__ = ()

        class _Port:
            def __index__(self):
                raise exc_type("__index__ 故意抛出 —— 取端口必须 fail-closed")

        assert guard.extract_port(_Addr(("127.0.0.1", _Port()))) is None

    @pytest.mark.parametrize("exc_type", [SystemExit, KeyboardInterrupt, _CustomBaseException])
    def test_index_raising_baseexception_is_also_fail_closed(self, exc_type):
        """``__index__`` 抛 ``BaseException`` 子类时同样必须返回 None（round-1 HIGH-1）。

        ⛔ 本卡第一版只把 ``except TypeError`` 扩到 ``except Exception``，
        ``SystemExit`` / ``KeyboardInterrupt`` / 自定义 ``BaseException`` 仍会逸出并越过
        ``STATE.record()`` —— 缺陷原样存在，只是触发它要换一个异常类型。
        与 ``_safe_repr``（U7-B 立的同型防线）口径统一为 ``BaseException``。

        ⛔ 断言写成「**自己捕获**再判有没有逃出来」，而不是直接调用（round-2 Codex LOW）：
        直接调用时，回退实现里逃出来的 ``KeyboardInterrupt`` 会被 pytest 当成**会话中断**
        （实测 rc=2），后面的参数**根本不跑** —— 存档里只会看到一个参数失败，另两个
        「未验证」。自己捕获之后，三个参数都以普通 ``AssertionError`` 各自翻红，
        失败正文还点名了逃出来的异常类型。
        """

        class _Addr(tuple):
            __slots__ = ()

        class _Port:
            def __index__(self):
                raise exc_type("__index__ 抛 BaseException —— 取端口仍必须 fail-closed")

        escaped = None
        got = "<未取到>"
        try:
            got = guard.extract_port(_Addr(("127.0.0.1", _Port())))
        except BaseException as exc:  # noqa: BLE001 —— 正是要判它有没有逃出来
            escaped = exc

        assert escaped is None, (
            f"取端口把 {type(escaped).__name__} 放了出来 —— 它会越过 STATE.record()，这次尝试整条不进账"
        )
        assert got is None

    def test_audit_hook_still_accounts_when_index_raises(self, isolated_state):
        """行为面：``__index__`` 抛非 ``TypeError`` 时，审计回调**仍然记账**（H-1a）。

        上一条锁的是纯函数返回值；这条锁的是**后果** —— 端口取不到 ⇒
        ``port_is_trustworthy`` 判不可信 ⇒ 走受拦分支 ⇒ ``record()`` 照常进账、
        非豁免连接照常抛本门的 ``RuntimeError``。

        修前这里抛的是 ``ValueError``（``__index__`` 自己那条），``pytest.raises``
        原样再抛 ⇒ 用例红，且 ``STATE.total`` 停在 0 —— 那正是「已阻断、零账本」。
        """

        class _Addr(tuple):
            __slots__ = ()

        class _Port:
            def __index__(self):
                raise ValueError("__index__ 故意抛出 —— 不得跳过记账")

        with pytest.raises(RuntimeError, match=guard.BLOCK_REASON):
            guard._audit_hook("socket.connect", (None, _Addr(("127.0.0.1", _Port()))))

        assert isolated_state.total == 1, "取端口时抛异常把这次尝试整条跳过了记账"
        assert isolated_state.blocked == 1
        assert isolated_state.late_snapshot()["unaccounted"] == 1


class TestTargetScopePrecheck:
    """``assert_neo4j_target_blocked``（负控专用）也必须用驱动口径。

    原来这里测的是 ``_port_of_uri`` —— 本模块自写的第二个解析器。它已被删除：
    round-2 Codex 实证它把 query / fragment 里的数字当端口，于是「目标必须在射程内」
    这道预检会**假通过**。现在两个预检同源，测的也就是同一件事。
    """

    @pytest.mark.parametrize(
        "uri,ports",
        [
            ("bolt://127.0.0.1:7691", (7691,)),
            ("bolt://127.0.0.1:7687", (7687,)),
            # ⛔ 旧解析器把 fragment / query 里的数字当端口（分别读成 7687 / 7691），
            #    于是这两条会被误判成"目标在受拦射程内"而放行装门。
            ("bolt://127.0.0.1:11434#tag:7687", (11434,)),
            ("bolt://127.0.0.1:7692?x=:7691", (7692,)),
        ],
    )
    def test_canonical_ports_match_driver_not_string_scan(self, uri, ports):
        got, why = guard.canonical_target_ports(uri)
        assert got == ports, why

    def test_target_in_scope_is_accepted(self, monkeypatch):
        monkeypatch.setenv(guard.ENV_REQUIRE_BLOCKED_TARGET, "1")
        monkeypatch.setenv("NEO4J_URI", "bolt://127.0.0.1:7691")
        guard.assert_neo4j_target_blocked()

    @pytest.mark.parametrize(
        "uri",
        [
            "bolt://127.0.0.1:11434#tag:7687",  # 真实端口 11434，射程外
            "bolt://127.0.0.1:7692?x=:7691",  # 真实端口 7692，射程外
            "bolt://127.0.0.1:7692",
        ],
    )
    def test_target_out_of_scope_is_refused(self, uri, monkeypatch):
        """射程外 ⇒ 拒绝装门。前两条在旧解析器下会假通过。"""
        monkeypatch.setenv(guard.ENV_REQUIRE_BLOCKED_TARGET, "1")
        monkeypatch.setenv("NEO4J_URI", uri)
        with pytest.raises(RuntimeError, match="不在受拦集合"):
            guard.assert_neo4j_target_blocked()

    def test_unparseable_target_is_fail_closed(self, monkeypatch):
        monkeypatch.setenv(guard.ENV_REQUIRE_BLOCKED_TARGET, "1")
        monkeypatch.setenv("NEO4J_URI", "ftp://127.0.0.1:7691")
        with pytest.raises(RuntimeError, match="解析不出端口"):
            guard.assert_neo4j_target_blocked()


class TestBlockedPortsContract:
    def test_live_ports_blocked_test_container_not(self):
        assert 7691 in guard.BLOCKED_PORTS
        assert 7687 in guard.BLOCKED_PORTS
        assert 7692 not in guard.BLOCKED_PORTS, "测试容器 7692 被拦会让真库门测试整条不可用"

    def test_test_uri_pointing_at_live_port_is_an_error(self, monkeypatch):
        """指向现网端口必须拒。

        文案随 CARD-W4-3a 从「受拦端口」改成白名单口径（判据由黑名单改成
        `ALLOWED_TEST_PORTS` 正面白名单），断言跟着改；语义没变，仍是「必须拒」。
        """
        monkeypatch.setenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7691")
        with pytest.raises(RuntimeError, match="白名单"):
            guard.assert_test_uri_not_blocked()

    def test_test_uri_on_container_port_is_fine(self, monkeypatch):
        monkeypatch.setenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7692")
        guard.assert_test_uri_not_blocked()

    def test_test_uri_unset_is_not_our_business(self, monkeypatch):
        monkeypatch.delenv("NEO4J_TEST_URI", raising=False)
        guard.assert_test_uri_not_blocked()


class TestDriverCanonicalPortContract:
    """CARD-W4-3a：判据必须按**驱动自己的**解析口径，而不是本模块的字符串推断。

    X4 两轮独立终审给出同一条 BLOCKER：``bolt://127.0.0.1:0`` 的端口 ``0`` 既不是
    None、又不在黑名单里，旧判据放行；而驱动把 ``:0`` 归一成 **7687**（现网默认端口），
    再经 ``is_exempt()`` 的 integration/e2e advisory 路径**真连开发库**。

    下面每条的 canonical 端口都由 ``neo4j.Address.parse(default_port=7687)`` 实际算出
    （2026-09-05 于本车道 venv 实跑确认全是 7687），断言错误文案里必须出现这个数字 ——
    读到报错的人应当立刻看见「它其实会连 7687」，而不是只看见"不合规"。
    """

    #: 全部会被驱动归一成 7687 的写法。前四条是 X4 BLOCKER 的直接形态。
    CANONICALIZES_TO_LIVE = [
        "bolt://127.0.0.1:0",  # 端口 0：`port or default_port` 的 falsy 分支
        "bolt://127.0.0.1:00",  # int("00") == 0，同上
        "bolt://[::1]:0",  # IPv6 分支（_addressing.py 另一条 return）
        "bolt://127.0.0.1",  # 压根不写端口
        "neo4j://host",  # 另一种 scheme，同样吃默认端口
    ]

    @pytest.mark.parametrize("uri", CANONICALIZES_TO_LIVE)
    def test_uri_canonicalizing_to_live_port_is_rejected(self, uri, monkeypatch):
        monkeypatch.setenv("NEO4J_TEST_URI", uri)
        with pytest.raises(RuntimeError, match="7687"):
            guard.assert_test_uri_not_blocked()

    @pytest.mark.parametrize("uri", CANONICALIZES_TO_LIVE)
    def test_canonical_port_helper_agrees_with_driver(self, uri):
        """判据函数本身也钉住：这些 URI 的 canonical 端口就是 7687。

        与上一条分开写是刻意的：上一条测「拒不拒」，这一条测「**为什么**拒」。
        只有前者的话，把判据改成「一律拒绝」也能全绿。
        """
        ports, why = guard.canonical_target_ports(uri)
        assert ports == (7687,), why

    def test_container_port_canonicalizes_to_itself(self):
        ports, why = guard.canonical_target_ports("bolt://127.0.0.1:7692")
        assert ports == (7692,), why

    def test_userinfo_uri_is_fail_closed(self, monkeypatch):
        """驱动的 ``parse_neo4j_uri`` 对带 userinfo 的 URI 直接 ConfigurationError。

        我们解析不出可信端口 ⇒ fail-closed 拒绝，而不是猜一个端口放行。
        """
        monkeypatch.setenv("NEO4J_TEST_URI", "bolt://user:pass@127.0.0.1:7692")
        with pytest.raises(RuntimeError, match="无法按驱动口径解析"):
            guard.assert_test_uri_not_blocked()

    def test_garbage_uri_is_fail_closed(self, monkeypatch):
        monkeypatch.setenv("NEO4J_TEST_URI", "bolt://127.0.0.1:notaport")
        with pytest.raises(RuntimeError, match="无法按驱动口径解析"):
            guard.assert_test_uri_not_blocked()

    #: 驱动的 ``parse_neo4j_uri`` 对这些 scheme 直接 ConfigurationError（连 driver 都建不起来）。
    #: ``bolt+routing`` 是被改名的旧 scheme，驱动对它单独报错。
    UNSUPPORTED_SCHEME_URIS = [
        # ⚠️ ftp / http / https 三条走的是**同一条**判据分支（驱动 `parse_neo4j_uri`
        #    对未知 scheme 一律 ConfigurationError）—— RV-C L-2 点名的重复。三条**保留
        #    不删**：删掉会让「这三种 scheme 都拒」这句话失去用例（属放宽），而它们是
        #    最容易被人手滑写进 NEO4J_TEST_URI 的三个。留着的成本是 2 个多余的
        #    parametrize 实例，收益是这句承诺仍有判据。
        "ftp://127.0.0.1:7692",
        "http://127.0.0.1:7692",
        "https://127.0.0.1:7692",
        # 下面两条各自是**独立**分支，不与上面三条同源：
        "bolt+routing://127.0.0.1:7692",  # 被改名的旧 scheme，驱动单独报错
        "127.0.0.1:7692",  # 压根没有 scheme（urlparse 会把 127.0.0.1 当 scheme）
    ]

    @pytest.mark.parametrize("uri", UNSUPPORTED_SCHEME_URIS)
    def test_unsupported_scheme_is_fail_closed(self, uri, monkeypatch):
        """scheme 不受驱动支持 ⇒ fail-closed，且拒因必须说清是 scheme 的事。

        2026-09-05 自查补的一段：先前只做 userinfo + `Address.parse`，于是
        ``ftp://127.0.0.1:7692`` 会被算出 7692 而**放行**。那不是安全洞（驱动
        `ConfigurationError`，连都建不起来），但它让「按驱动解析链复算」这句
        **比实现宽**，而且拒因会给错（说"会连 7687"）。
        """
        monkeypatch.setenv("NEO4J_TEST_URI", uri)
        with pytest.raises(RuntimeError, match="scheme"):
            guard.assert_test_uri_not_blocked()

    def test_supported_schemes_come_from_the_driver_itself(self):
        """scheme 集合必须取自驱动的公开常量，不是抄下来的字面值。

        抄下来的字符串会随驱动升级悄悄过期；这条测试在驱动改名/增删 scheme 时
        当场报错，而不是等到某个 URI 被误判。
        """
        from neo4j import api as neo4j_api

        expected = {
            neo4j_api.URI_SCHEME_BOLT,
            neo4j_api.URI_SCHEME_BOLT_SELF_SIGNED_CERTIFICATE,
            neo4j_api.URI_SCHEME_BOLT_SECURE,
            neo4j_api.URI_SCHEME_NEO4J,
            neo4j_api.URI_SCHEME_NEO4J_SELF_SIGNED_CERTIFICATE,
            neo4j_api.URI_SCHEME_NEO4J_SECURE,
        }
        # 每个受支持 scheme 配一个 7692 URI，全部必须放行；
        # 被改名的 bolt+routing 必须仍然拒（它不在 expected 里）。
        for scheme in expected:
            ports, why = guard.canonical_target_ports(f"{scheme}://127.0.0.1:7692")
            assert ports == (7692,), f"{scheme} 应被支持，实得 {ports}（{why}）"
        ports, why = guard.canonical_target_ports(f"{neo4j_api.URI_SCHEME_BOLT_ROUTING}://127.0.0.1:7692")
        assert ports is None and "scheme" in why, f"bolt+routing 应被拒，实得 {ports}（{why}）"

    #: round-1 Codex BLOCKER 的实测反例 —— routing scheme 的 netloc 会被
    #: ``Address.parse_list`` **按空白拆成多个地址**，驱动取 ``[0]``。
    #: 单值 ``Address.parse`` 对这些串给出 7692（放行），而驱动真实连的是现网端口。
    ROUTING_MULTI_ADDRESS_TRAPS = [
        ("neo4j://127.0.0.1 :7692", (7687, 7692)),
        ("neo4j+s://127.0.0.1 :7692", (7687, 7692)),
        ("neo4j+ssc://127.0.0.1 :7692", (7687, 7692)),
        ("neo4j://[::1]:7691 [::1]:7692", (7691, 7692)),
        ("neo4j://ok.example:7692 evil.example:7691", (7692, 7691)),
    ]

    @pytest.mark.parametrize("uri,expected_ports", ROUTING_MULTI_ADDRESS_TRAPS)
    def test_routing_uri_multi_address_is_rejected(self, uri, expected_ports, monkeypatch):
        """routing 的**每一个**初始候选地址都要合规，不是只看驱动先用的那个。"""
        ports, why = guard.canonical_target_ports(uri)
        assert ports == expected_ports, f"解析口径与驱动不一致：{ports}（{why}）"
        monkeypatch.setenv("NEO4J_TEST_URI", uri)
        with pytest.raises(RuntimeError, match="白名单"):
            guard.assert_test_uri_not_blocked()

    def test_routing_uri_with_all_container_addresses_is_accepted(self, monkeypatch):
        """反方向：多地址**全部**是 7692 时必须放行（驱动接受这种写法）。

        第一版把 routing 当 direct 解析，这条会被误拒 —— 收紧过头同样是缺陷。
        """
        uri = "neo4j://127.0.0.1:7692 localhost:7692"
        ports, why = guard.canonical_target_ports(uri)
        assert ports == (7692, 7692), why
        monkeypatch.setenv("NEO4J_TEST_URI", uri)
        guard.assert_test_uri_not_blocked()

    def test_allowed_ports_whitelist_is_load_bearing(self, monkeypatch):
        """验伪锚：白名单清空后连 7692 也必须被拒。

        没有这一条，「7692 放行」可能只是因为判据恒真 —— 那样白名单就是装饰品。
        """
        monkeypatch.setattr(guard, "ALLOWED_TEST_PORTS", frozenset())
        monkeypatch.setenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7692")
        with pytest.raises(RuntimeError, match="白名单"):
            guard.assert_test_uri_not_blocked()

    #: 合法的测试容器写法 —— 白名单是**默认拒绝**语义，代价就是误拒，所以
    #: 「不该拒的别拒」必须有门。这些形态 2026-09-05 在本车道 venv 上逐个实跑过。
    #: ⚠️ 最朴素的那条 ``bolt://127.0.0.1:7692`` **刻意不在这里**（RV-C L-2 去重）：
    #: 它与 ``TestBlockedPortsContract::test_test_uri_on_container_port_is_fine``
    #: 输入、调用、期望三者完全相同。保留的是那一条独立用例而不是这里的列表项 ——
    #: 它在那个类里承担**局部验伪锚**：没有它，同类的
    #: ``test_test_uri_pointing_at_live_port_is_an_error`` 会被「一律拒绝」的实现骗过。
    #: 本列表要覆盖的是 scheme / 大小写 / 路径 / query / IPv6 这些**变体**，少一条朴素形态
    #: 不丢分支。
    LEGITIMATE_CONTAINER_URIS = [
        "bolt+s://127.0.0.1:7692",
        "bolt+ssc://127.0.0.1:7692",
        "neo4j://127.0.0.1:7692",
        "neo4j+s://127.0.0.1:7692",
        "neo4j+ssc://127.0.0.1:7692",
        "bolt://localhost:7692",
        "bolt://[::1]:7692",  # IPv6 字面量
        "BOLT://127.0.0.1:7692",  # scheme 大小写
        "bolt://127.0.0.1:7692/",  # 末尾斜杠
        "neo4j://127.0.0.1:7692?routing=false",  # 带 query（routing context 只有 neo4j scheme 合法）
        "bolt://127.0.0.1:7692/neo4j",  # 带 path
        "bolt://host.docker.internal:7692",  # 容器内主机名
    ]

    @pytest.mark.parametrize("uri", LEGITIMATE_CONTAINER_URIS)
    def test_legitimate_container_uri_is_not_rejected(self, uri, monkeypatch):
        monkeypatch.setenv("NEO4J_TEST_URI", uri)
        guard.assert_test_uri_not_blocked()

    def test_whitelist_does_not_admit_live_port_by_construction(self):
        """白名单与受拦集合必须不相交 —— 往白名单里加 7687 是最省事的拆门方式。

        探针 ``guard-allowed-test-ports-cannot-admit-live`` 在运行期钉同一件事；
        这里是静态的那一半。
        """
        assert not (guard.ALLOWED_TEST_PORTS & guard.BLOCKED_PORTS), (
            "ALLOWED_TEST_PORTS 与 BLOCKED_PORTS 相交 —— 白名单把现网端口放进来了"
        )
        assert 7692 in guard.ALLOWED_TEST_PORTS


class TestPortTrustworthiness:
    """R1 Codex LOW：有状态的 ``__index__`` 会被求值两次（TOCTOU）。"""

    def test_exact_int_is_trustworthy(self):
        assert guard.port_is_trustworthy(("127.0.0.1", 7692)) is True

    def test_index_object_is_not_trustworthy(self):
        class Flaky:
            def __init__(self):
                self.n = 0

            def __index__(self) -> int:
                self.n += 1
                return 7691 if self.n == 1 else 1

        assert guard.port_is_trustworthy(("127.0.0.1", Flaky())) is False

    def test_bool_is_not_an_exact_int(self):
        # bool 是 int 子类，但当端口毫无意义；不给它「可信」的待遇
        assert guard.port_is_trustworthy(("127.0.0.1", True)) is False

    def test_non_tuple_address_is_out_of_scope(self):
        assert guard.port_is_trustworthy("/tmp/sock") is True

    def test_tuple_subclass_lying_about_port_is_read_from_slots(self):
        """X4 §7.10 A 类 HIGH #2（本卡两次修才对）。

        地址是 tuple **子类**时，``[1]`` 走可重载的 ``__getitem__``，而 CPython 的
        socket 读**底层槽位** —— 下面这个类对 Python 层报"端口 1"（安全），
        槽位里躺着的却是 7691。

        ⚠️ 本卡第一版的修法是「tuple 子类一律不可信」，被 round-1 打回：
        neo4j 驱动自己的地址类就是 tuple 子类（见下一条测试），一律拒绝会**误拦
        合法的 7692 连接**。正解是绕开重载、直接读槽位。
        """

        class Sneaky(tuple):
            def __getitem__(self, i):
                return 1 if i == 1 else super().__getitem__(i)

        addr = Sneaky(("127.0.0.1", 7691))
        assert addr[1] == 1, "前提：这个子类确实对 Python 层谎报端口"
        assert tuple.__getitem__(addr, 1) == 7691, "前提：底层槽位里仍是受拦端口"
        # 读槽位 ⇒ 看见真实的 7691，而不是它想让我们看见的 1
        assert guard.extract_port(addr) == 7691
        assert guard.port_is_trustworthy(addr) is True  # 槽位里是精确 int

    def test_tuple_subclass_overriding_len_is_read_from_slots(self):
        """同族的另一种写法：把 ``__len__`` 压到 2 以下让长度检查整条跳过。"""

        class ShortLen(tuple):
            def __len__(self):
                return 0

        addr = ShortLen(("127.0.0.1", 7691))
        assert len(addr) == 0, "前提：这个子类确实对 Python 层谎报长度"
        assert guard.extract_port(addr) == 7691  # tuple.__len__ 看到的是 2
        assert guard.port_is_trustworthy(addr) is True

    def test_real_driver_address_is_not_falsely_blocked(self):
        """round-1 Codex HIGH：驱动的地址类**就是 tuple 子类**，不能一律拒绝。

        `neo4j._addressing.Address` 家族（`IPv4Address` / `ResolvedIPv4Address` …）
        由 `_bolt_socket.py` 直接交给 `s.connect()`。本卡第一版「子类一律不可信」
        会把**合法的 7692 测试容器连接**当场拦掉 —— 那是把门变成了故障源。
        """
        from neo4j import Address

        safe = Address.parse("127.0.0.1:7692")
        assert type(safe) is not tuple and isinstance(safe, tuple), "前提：驱动地址是 tuple 子类"
        assert guard.extract_port(safe) == 7692
        assert guard.port_is_trustworthy(safe) is True
        assert guard._audit_hook("socket.connect", (None, safe)) is None, "合法 7692 不该被拦"

    def test_real_driver_address_on_live_port_is_still_blocked(self):
        """对照：同一个类型指向 7691 时必须**仍然**拦下（否则上一条是放水）。

        这里只断言分类，不调 hook —— 调了会记账、结账哨兵会把本用例判红。
        """
        from neo4j import Address

        live = Address.parse("127.0.0.1:7691")
        assert guard.extract_port(live) == 7691
        assert guard.extract_port(live) in guard.BLOCKED_PORTS


class TestSelftestAddressClassification:
    """round-2 Codex HIGH-1：自证分类决定「拦截要不要记账」，必须比端口判据更严。

    旧实现 `isinstance(address, tuple) and len(address) >= 1 and address[0] == _SELFTEST_HOST`
    三处都可被重载，于是**真实的受拦连接**能被分类成自证 —— 抛出的
    `_SelfTestBlocked` 继承 `RuntimeError`、普通 `except` 就能吞掉，而
    `STATE.record()` 在这之后才跑 ⇒ **账本为零**，结账无从据此拒绝 rc=0。
    """

    def test_genuine_selftest_address_is_classified(self):
        assert guard._is_selftest_address((guard._SELFTEST_HOST, 7691)) is True

    def test_tuple_subclass_disguise_is_not_selftest(self):
        """底层是真实受拦地址，`[0]` 伪装成哨兵。"""

        class Disguise(tuple):
            def __getitem__(self, i):
                return guard._SELFTEST_HOST if i == 0 else super().__getitem__(i)

        addr = Disguise(("127.0.0.1", 7691))
        assert addr[0] == guard._SELFTEST_HOST, "前提：表面确实伪装成了哨兵"
        assert tuple.__getitem__(addr, 0) == "127.0.0.1", "前提：底层是真实主机"
        assert guard._is_selftest_address(addr) is False

    def test_str_subclass_eq_disguise_is_not_selftest(self):
        """主机名是 `str` 子类，其 `__eq__` 对哨兵恒真。"""

        class AlwaysEqual(str):
            def __eq__(self, other):
                return True

            __hash__ = str.__hash__

        addr = (AlwaysEqual("127.0.0.1"), 7691)
        assert addr[0] == guard._SELFTEST_HOST, "前提：__eq__ 确实对哨兵返回真"
        assert guard._is_selftest_address(addr) is False

    def test_non_tuple_is_not_selftest(self):
        assert guard._is_selftest_address("/tmp/sock") is False
        assert guard._is_selftest_address(()) is False

    def test_audit_hook_does_not_block_plain_safe_address(self):
        """对照：普通 tuple + 非受拦端口必须**不**被拦。

        没有这一条，「把 hook 改成一律抛」也能让上面全绿。
        """
        addr = ("127.0.0.1", 11434)  # Ollama 那类本地端口
        assert guard._audit_hook("socket.connect", (None, addr)) is None

    def test_genuine_selftest_address_reaches_blocking_path(self):
        """真自证地址 + 受拦端口 ⇒ 抛 `_SelfTestBlocked`（证明拦截分支可达且不记账）。"""
        with pytest.raises(guard._SelfTestBlocked):
            guard._audit_hook("socket.connect", (None, (guard._SELFTEST_HOST, 7691)))

    # ── RV-C H-2：哨兵常量本身要有独立断言 ────────────────────────────────
    def test_selftest_host_is_an_unconnectable_sentinel(self):
        """``_SELFTEST_HOST`` 必须是**连不上任何东西**的哨兵，而不是普通主机名。

        ⛔ RV-C H-2：本类原有 6 条用例**没有一条**能拦住「把哨兵常量改成
        ``"localhost"``」—— 4 条以该常量为输入或期望值（跟着常量一起变），另 2 条
        （非 tuple / 普通安全地址）本就不看它。于是「自证地址不进账」这条豁免的**前提**
        （这个主机名不可能是真实 connect 的目标）从来没有被判据钉住：常量一改，
        任何连 ``localhost`` 的真实拦截都会被分类成自证 ⇒ 不记账 ⇒ 结账无从拒绝 rc=0。

        判据分两层，缺一不可：

        * **行为层**（``ord`` / ``len``）—— 常量的**值**必须首字符是 NUL。这一层
          grep 证不了；
        * **拼写层**（裁判 7 的 ``grep '\\x00'``）—— 源码里必须写转义，不许敲
          不可见字符（否则工具链会静默把它换掉，且 code review 看不出来）。

        ``len == 28`` 是本树实测值（1 个 NUL + 27 个字符），改常量长度会顶红 ——
        这是刻意的：改它就该有人重新想一遍这条豁免的前提。
        """
        host = guard._SELFTEST_HOST
        assert type(host) is str, "哨兵必须是精确 str（_is_selftest_address 用 type(...) is str 判）"
        assert ord(host[0]) == 0, "哨兵首字符必须是 NUL —— 那才是它连不上任何东西的理由"
        assert len(host) == 28, f"哨兵长度变了（实测 {len(host)}）—— 改它请重新论证这条豁免的前提"
        # ⚠️ 下面三条是**说明性**的，不算三份独立检出能力（round-1 Codex LOW）：
        #    前两条断言（精确 str + 首字符 NUL）已经蕴含它们，没有哪种输入能只让这三条红。
        #    留着是给读代码的人一眼看出「哨兵不能是普通主机名」这个意图。
        assert host != "localhost"
        assert host != "127.0.0.1"
        assert "\x00" in host

    # ── RV-C M-1：普通 tuple + 真实主机 + 受拦端口的直判负例 ──────────────
    #
    # 原有用例只有一条正例（真哨兵 ⇒ True）与两条**形状**负例（非 tuple / 空 tuple），
    # 缺这一类：形状完全合法、只是主机名不对。Codex 原话是「把实现改成只判
    # ``type(host) is str``，该类六个测试仍能满足」—— 那个实现会把每一条到 7691 的
    # 真实连接都判成自证、从而不记账。旁证 ``test_audit_hook_does_not_block_plain_safe_address``
    # 用的是**非**受拦端口 11434，挡不住这条（那条地址本来就不进受拦分支）。
    #
    # 三条分开写而不参数化：三种地址形态（IPv4 / 主机名 / IPv6 四元组）各自可归因，
    # 且判据 ``grep -c '_is_selftest_address(('`` 数的是这个字面调用形态。
    def test_plain_ipv4_on_blocked_port_is_not_selftest(self):
        assert guard._is_selftest_address(("127.0.0.1", 7691)) is False

    def test_plain_hostname_on_blocked_port_is_not_selftest(self):
        assert guard._is_selftest_address(("localhost", 7687)) is False

    def test_plain_ipv6_four_tuple_on_blocked_port_is_not_selftest(self):
        assert guard._is_selftest_address(("::1", 7691, 0, 0)) is False

    def test_selftest_lookalike_without_the_nul_is_not_selftest(self):
        """**去掉 NUL** 的近似哨兵不得被判成自证（round-1 Codex LOW 建议补的负例）。

        上面三条杀得掉「只判 ``type(host) is str``」那个变异，但杀不掉
        ``host.endswith("w4-live-port-guard-selftest")`` 这类**后缀匹配**实现 ——
        那种实现会把这个不含 NUL、因而**连得上**的同名主机也判成自证 ⇒ 不记账。
        NUL 才是「这个名字连不上任何东西」的全部理由，所以判据必须是精确相等。
        """
        assert guard._is_selftest_address(("w4-live-port-guard-selftest", 7691)) is False


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

        # key 必须**存在且为 None**：只判 `.get(...) is None` 的话，
        # `del sys.modules["uvloop"]` 之后表达式恒成立，检查形同虚设
        # （R1 Codex HIGH）。
        assert "uvloop" in sys.modules, "毒化条目被删除 = 可以重新 import"
        assert sys.modules["uvloop"] is None

    def test_uvloop_key_removal_is_detected(self, monkeypatch):
        """把毒化条目删掉，边界自证必须当场翻红（而不是「None is not None → 通过」）。"""
        import sys

        monkeypatch.delitem(sys.modules, "uvloop", raising=False)
        with pytest.raises(guard.GuardDrift, match="毒化条目被删除"):
            guard.assert_guard_live("unit test: uvloop key removed")

    def test_uvloop_import_is_blocked_by_audit(self):
        """承重的关门方式是 audit ``import`` 事件（摘不掉），不是 sys.modules 毒化。"""
        import sys

        saved = sys.modules.pop("uvloop", None)
        try:
            with pytest.raises(RuntimeError, match="uvloop 的 import 被本门拦下"):
                sys.audit("import", "uvloop", None, None, None, None)
        finally:
            if saved is not None or "uvloop" not in sys.modules:
                sys.modules["uvloop"] = saved

    @pytest.mark.parametrize(
        "module_name",
        ["uvloop", "uvloop.loop", "uvloop.includes", "uvloop._noop", "uvloop._version"],
    )
    def test_uvloop_submodule_import_is_blocked_by_audit(self, module_name):
        """子模块的 ``import`` 事件也必须被拦（RV-C M-4，2026-09-08 实测定案）。

        ⛔ 实测（``evidence-w47/m4-importlib-*.txt``）：``importlib.import_module("uvloop")``
        **不会**为「uvloop」这个顶层名抛 ``import`` 审计事件 —— 该事件由 ``__import__``
        （即 ``import`` 语句）抛出，``import_module`` 走的是 ``_bootstrap._gcd_import``。
        于是 ``del sys.modules["uvloop"]`` 绕过非承重的毒化层之后，
        ``importlib.import_module("uvloop")`` **两层防御全都越过、成功导入**。

        但 hook 并非没被调用：uvloop 的 ``__init__.py`` 自己 ``import`` 子模块，**那些走
        ``import`` 语句**、照常抛事件。证据 ``evidence-w47/m4-importlib-r3-*.txt`` 的
        `uvloop 事件` 行（两个形态各有记录，**都限定本机 CPython 3.14.4 + 本 venv 的
        uvloop 版本**）：

        * ``no-guard__baseline``（**不装门**、只挂旁观 hook）⇒
          ``['uvloop.includes', 'uvloop.loop', 'uvloop.loop', 'uvloop._noop', 'uvloop._version']``
          —— 5 个事件，``uvloop.loop`` 出现两次；
        * ``importlib__poison-removed``（**装了门**）⇒ ``['uvloop.includes']`` 一条，
          因为门在第一条上就抛了。

        两个记录含义不同，别混用。

        判据从「``args[0] == "uvloop"``」放宽到「``uvloop`` 或 ``uvloop.`` 开头」即可在
        **同一层**（audit import 事件）关上这条路 —— 承重方式没变。
        """
        import sys

        saved = sys.modules.pop("uvloop", None)
        try:
            with pytest.raises(RuntimeError, match="uvloop 的 import 被本门拦下"):
                sys.audit("import", module_name, None, None, None, None)
        finally:
            if saved is not None or "uvloop" not in sys.modules:
                sys.modules["uvloop"] = saved

    @pytest.mark.parametrize("value", ["uvloop", "uvloop.loop"])
    def test_str_subclass_module_name_is_still_blocked(self, value):
        """``str`` **子类**的模块名照样要拦（round-1 Codex HIGH-2 打回的判定回退）。

        ⛔ 本卡第一版把判据写成 ``type(name) is not str: return False`` —— 本意是不信任
        可重载的比较方法，实际效果却**比旧实现更宽**：一个毫无重载、值就是 ``"uvloop"``
        的 ``str`` 子类，旧的 ``args[0] == "uvloop"`` 拦得住，那一版反而放行。
        CPython 接受 Unicode 子类、绝对导入保留原 name 对象、审计事件原样传递，
        所以这不是只有手工 ``sys.audit`` 才构造得出的形态。
        """

        class _Name(str):
            __slots__ = ()

        import sys

        saved = sys.modules.pop("uvloop", None)
        try:
            with pytest.raises(RuntimeError, match="uvloop 的 import 被本门拦下"):
                sys.audit("import", _Name(value), None, None, None, None)
        finally:
            if saved is not None or "uvloop" not in sys.modules:
                sys.modules["uvloop"] = saved

    @pytest.mark.parametrize("value", ["uvloop", "uvloop.loop"])
    def test_denying_str_subclass_is_still_blocked(self, value):
        """两个比较方法**恒说不是**的 ``str`` 子类，仍必须按真实值拦下。

        ⛔ round-2 Codex MEDIUM：上一版用的是「取反」型说谎子类，对
        ``_Liar("uvloop")`` 而言 ``startswith("uvloop.")`` 恰好返回 **True**（原串本来就
        不以带点前缀开头，取反成真），于是**即使把判据错误地改回绑定调用**，正向那半仍绿。
        Codex 给的静态反例是::

            str.__eq__(name, "uvloop") is True or (
                str.startswith(name, "uvloop.") and name.startswith("uvloop.")
            )

        它能满足普通子类用例、取反型 ``"uvloop"`` 与 ``"json"`` 用例，却**放行**
        ``uvloop.loop``。改成「两个方法恒返回 False」的子类 + 参数化两个真实值之后，
        那个反例在 ``uvloop.loop`` 这一参数上必红。
        """

        class _Denier(str):
            __slots__ = ()

            def __eq__(self, other):  # noqa: D105
                return False

            def __ne__(self, other):  # noqa: D105
                return True

            def startswith(self, *a, **k):  # noqa: D102
                return False

            __hash__ = str.__hash__

        import sys

        saved = sys.modules.pop("uvloop", None)
        try:
            with pytest.raises(RuntimeError, match="uvloop 的 import 被本门拦下"):
                sys.audit("import", _Denier(value), None, None, None, None)
        finally:
            if saved is not None or "uvloop" not in sys.modules:
                sys.modules["uvloop"] = saved

    def test_affirming_str_subclass_is_not_mistakenly_blocked(self):
        """两个比较方法**恒说是**的 ``str`` 子类，真实值无关时不得误拦（反方向）。

        与上一条配对：上一条防「按子类的谎话放行」，这一条防「按子类的谎话误拦」。
        判据只认未绑定 ``str.__eq__`` / ``str.startswith`` 读到的真实值。
        """

        class _Affirmer(str):
            __slots__ = ()

            def __eq__(self, other):  # noqa: D105
                return True

            def __ne__(self, other):  # noqa: D105
                return False

            def startswith(self, *a, **k):  # noqa: D102
                return True

            __hash__ = str.__hash__

        assert guard._audit_hook("import", (_Affirmer("json"), None, None, None, None)) is None

    @pytest.mark.parametrize("module_name", ["uvloopx", "uvloop_shim", "myuvloop", "uv"])
    def test_lookalike_module_names_are_not_blocked(self, module_name):
        """验伪锚：名字**像** uvloop 但不是它的模块不得被误拦（M-4 收紧的反向）。

        判据用 ``"uvloop."`` 带点前缀而不是裸 ``startswith("uvloop")``，正是为了
        ``uvloopx`` 这类名字 —— 没有这条，「一律拒绝以 uvloop 开头的模块」也能让上一条全绿。
        """
        assert guard._audit_hook("import", (module_name, None, None, None, None)) is None

    def test_ledger_shape(self):
        led = guard.STATE.ledger()
        for key in ("total", "blocked", "advisory", "billed", "unaccounted", "reported_status", "installed"):
            assert key in led, f"账本缺字段 {key} —— 父进程复核会读它"
        assert led["installed"] is True


# ═══════════════════════════════════════════════════════════════════════════
# CARD-W4-4：结算原子性 / 单快照 / install 顺序 / 预检-豁免顺序 / 注入点惰性
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def isolated_state(monkeypatch):
    """给结算类用例一份**独立的** :class:`_GuardState`。

    ⛔ 绝不能在真 ``guard.STATE`` 上试结算：一旦把它置成「已结算」，本进程后续
    每一次到受拦端口的连接都会走迟到路径 ``os._exit(3)`` —— 整条测试线当场消失，
    而且是以「进程没了」这种最难归因的形式。
    """
    state = guard._GuardState()
    monkeypatch.setattr(guard, "STATE", state)
    return state


def _fn_ast(func) -> ast.FunctionDef:
    """取某个函数的 AST（用于「顺序」「有没有调某某」这类**结构性**断言）。

    有些性质在进程内观测不到——例如「``install()`` 里装 hook 是不是排在预检之前」，
    真跑一次只会得到一个已经装好的门。这类断言只能盯源码结构；对应的**行为**证明
    在 ``scripts/lifespan_isolation_guard_probes.py`` 的子进程探针里。
    """
    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    node = tree.body[0]
    assert isinstance(node, ast.FunctionDef)
    return node


def _called_names(node: ast.AST) -> list[str]:
    """节点子树里所有被调用的名字（``f()`` 记 ``f``；``a.b()`` 记 ``b``）。"""
    names: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name):
                names.append(func.id)
            elif isinstance(func, ast.Attribute):
                names.append(func.attr)
    return names


def _callers_of(callee: str) -> list[str]:
    """整个 ``live_port_guard`` 模块里，直接调用 ``callee()`` 的函数名（可重复）。

    用于「某个写盘/取锁的原语只准从一个地方调」这类**全模块**判据 —— 只看单个函数的
    ``_called_names`` 挡不住「别处又新开一个调用点」。
    """
    tree = ast.parse(inspect.getsource(guard))
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    def enclosing(node: ast.AST) -> str:
        current: ast.AST | None = node
        while current is not None:
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return current.name
            current = parents.get(current)
        return "<module>"

    return [
        enclosing(node)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == callee
    ]


def _is_self_attr(node: ast.AST, attr: str) -> bool:
    """严格判 ``self.<attr>``（``self`` 必须是最里层的 ``Name``）。

    ``self.pending.setdefault`` 这类链式访问的 ``value`` 是另一个 ``Attribute``，
    不算 —— 判据要盯的是「直接对 self 做的那一下」。
    """
    return (
        isinstance(node, ast.Attribute)
        and node.attr == attr
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    )


def _self_lock_with_nodes(func) -> list[ast.With]:
    """函数体里所有 ``with self._lock:`` 临界区（按源码顺序）。"""
    return [
        node
        for node in ast.walk(_fn_ast(func))
        if isinstance(node, ast.With) and node.items and _is_self_attr(node.items[0].context_expr, "_lock")
    ]


def _referenced_names(node: ast.AST) -> set[str]:
    """子树里出现的所有裸名字（``Name`` 节点的 ``id``）。"""
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _contains(haystack: ast.AST, needle: ast.AST) -> bool:
    """``needle`` 这个**具体节点**是否落在 ``haystack`` 子树里（按身份，不是按内容）。"""
    return any(n is needle for n in ast.walk(haystack))


def _parent_map(node: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(node):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _guard_state_ast() -> ast.ClassDef:
    """``_GuardState`` 的类 AST。"""
    node = ast.parse(textwrap.dedent(inspect.getsource(guard._GuardState))).body[0]
    assert isinstance(node, ast.ClassDef)
    return node


def _locked_helper_names() -> set[str]:
    """``_GuardState`` 里以 ``_locked`` 结尾的方法名，**从源码 AST 导出**。

    白名单不写死，是为了让「有人新加了一个已持锁 helper」这件事被那条相等断言逼出来，
    而不是让判据悄悄跟着源码漂移（见 ``test_settlement_path_never_nests_the_lock``）。
    """
    return {n.name for n in _guard_state_ast().body if isinstance(n, ast.FunctionDef) and n.name.endswith("_locked")}


def _direct_self_calls(node: ast.AST) -> list[str]:
    """子树里所有 ``self.<name>(...)`` 的 ``<name>``（只认直接对 self 的调用）。"""
    names: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
            if isinstance(child.func.value, ast.Name) and child.func.value.id == "self":
                names.append(child.func.attr)
    return names


def _is_dead_branch(node: ast.AST) -> bool:
    """``if False:`` / ``while 0:`` 这类**恒假**分支（Codex round-1 MEDIUM-7）。

    只认字面常量：``if False`` / ``if 0`` / ``if None`` / ``if ""``。变量条件一律当
    可达（保守方向 —— 判据宁可多数一条，也不能把真调用当死代码放过）。
    """
    return isinstance(node, (ast.If, ast.While)) and isinstance(node.test, ast.Constant) and not node.test.value


def _live_called_names(node: ast.AST) -> list[str]:
    """同 :func:`_called_names`，但**跳过恒假分支的 body**（Codex round-1 MEDIUM-7）。

    ``_called_names`` 走 ``ast.walk``，于是 ``if False: _install_audit_hook()`` 这条
    死代码也会被数进去 —— 顺序类断言（谁排在谁前面）因此可以被一个**诱饵**骗过：
    把恒假分支里的假调用摆在前面，真调用挪到后面，旧门照样绿。这里按控制流剪枝：
    恒假分支的 ``body`` 不算数，``test`` 与 ``orelse`` 仍算（``if False: A`` 的
    ``else`` 支是会跑的）。

    ⛔ 剪枝判定必须发生在**进入每个节点时**，包括传进来的那个根节点。初版只在
    ``iter_child_nodes`` 的子节点上判，于是 ``_live_called_names(<if False 语句>)``
    ——顺序门正是这么逐条调它的——从该 ``If`` 的子节点开始遍历，恒假分支的 body 原样
    被数进去，诱饵照样生效。负控 case 4 当场抓到（2026-09-08 实测：新门在变异体上
    仍 passed）。
    """
    names: list[str] = []

    def visit(current: ast.AST) -> None:
        if _is_dead_branch(current):
            assert isinstance(current, (ast.If, ast.While))
            visit(current.test)
            for stmt in current.orelse:
                visit(stmt)
            return
        if isinstance(current, ast.Call):
            func = current.func
            if isinstance(func, ast.Name):
                names.append(func.id)
            elif isinstance(func, ast.Attribute):
                names.append(func.attr)
        for child in ast.iter_child_nodes(current):
            visit(child)

    visit(node)
    return names


class TestSettlementAtomicity:
    """结算标志 / 账本快照 / 记账必须在**同一把锁**里（CARD-W4-4 的要害）。

    行为面的证明（真的制造交错、看进程 rc）在探针
    ``guard-finalize-race-loses-record`` 里 —— 迟到路径以 ``os._exit(3)`` 收场，
    在 pytest 进程内跑不了。这里锁的是**判定本身**。
    """

    def test_record_before_finalize_is_block(self, isolated_state):
        assert isolated_state.record(("127.0.0.1", 7691)) == guard.RECORD_BLOCK

    def test_record_after_finalize_returns_late(self, isolated_state):
        """结算之后再落地的记录必须拿到「迟到」信号，而不是普通的「该拦」。"""
        isolated_state.finalize_and_snapshot()
        assert isolated_state.record(("127.0.0.1", 7691)) == guard.RECORD_LATE

    def test_finalize_snapshot_is_frozen_against_later_records(self, isolated_state):
        """快照取走之后落地的记录**不得**回头改写那份快照。

        它必须体现在两个地方：``STATE.late`` 计数，以及**重新取**的账本
        （``late_snapshot``）。这样迟到路径重写账本文件时，文件才与 rc=3 对得上。
        """
        snapshot = isolated_state.finalize_and_snapshot()
        assert snapshot["unaccounted"] == 0 and snapshot["blocked"] == 0

        assert isolated_state.record(("127.0.0.1", 7691)) == guard.RECORD_LATE

        assert snapshot["unaccounted"] == 0, "结算快照被事后改写了 —— 它必须是那一刻的定格"
        assert isolated_state.late == 1
        later = isolated_state.late_snapshot()
        assert later["unaccounted"] == 1 and later["blocked"] == 1

    def test_late_record_is_blocked_even_when_the_item_is_exempt(self, isolated_state, monkeypatch):
        """迟到路径**不看豁免**：结算之后已无人能把 advisory 变成非零 rc。

        （旧实现的 ``if _FINALIZING`` 同样不看豁免，这条锁的是语义没被改松。）
        """
        guard.begin_item("tests/integration/test_x.py::test_y", True)
        try:
            isolated_state.precheck_done = True
            guard.begin_item("tests/integration/test_x.py::test_y", True)
            assert guard._EXEMPT_CV.get() is True, "前置条件没成立：这条用例本该是豁免的"
            isolated_state.finalize_and_snapshot()
            assert isolated_state.record(("127.0.0.1", 7691)) == guard.RECORD_LATE
            assert isolated_state.advisory == 0
            assert isolated_state.blocked == 1
            assert isolated_state.late_snapshot()["unaccounted"] == 1
        finally:
            guard.end_item()

    def test_exempt_item_still_gets_advisory_before_finalize(self, isolated_state):
        """反向锚：结算**之前**豁免照常生效 —— 否则上一条只是「什么都豁免不了」。"""
        isolated_state.precheck_done = True
        guard.begin_item("tests/integration/test_x.py::test_y", True)
        try:
            assert isolated_state.record(("127.0.0.1", 7691)) == guard.RECORD_ADVISORY
            assert isolated_state.advisory == 1 and isolated_state.blocked == 0
        finally:
            guard.end_item()

    def test_finalize_and_snapshot_sets_the_flag_and_snapshots_under_one_lock(self):
        """``finalize_and_snapshot`` 的函数体里，置标志与取快照必须在**同一个** with。

        这是本卡的核心不变量：拆成两条独立语句（哪怕都各自持锁）就重新打开了那个
        夹缝。断言盯的是「``self.finalizing = True`` 与取快照同属一个
        ``with self._lock``」。

        ⚠️ 收紧（Codex round-1 MEDIUM-7）：旧写法对 ``ast.dump(withs[0])`` 做**子串**
        匹配，于是 ``with self.unrelated_lock:`` 只要体内出现那两个名字就照样绿 ——
        判据完全没检查这个 ``with`` 锁的是不是 ``self._lock``。现在按结构判：
        同一个 ``With``、``items[0]`` 必须是 ``self._lock``、体内同时有对
        ``self.finalizing`` 的赋值与对 ``_ledger_locked`` 的调用。
        """
        node = _fn_ast(guard._GuardState.finalize_and_snapshot)
        withs = [n for n in node.body if isinstance(n, ast.With)]
        assert len(withs) == 1, "结算必须只有一个临界区"
        critical = withs[0]
        assert critical.items and _is_self_attr(critical.items[0].context_expr, "_lock"), (
            "结算的临界区锁的不是 self._lock —— 换成别的锁，夹缝原样存在"
        )
        assigns_flag = any(
            isinstance(stmt, ast.Assign) and any(_is_self_attr(t, "finalizing") for t in stmt.targets)
            for stmt in ast.walk(critical)
        )
        assert assigns_flag, "结算标志不是在这个临界区里赋的值"
        assert "_ledger_locked" in _direct_self_calls(critical), "快照不在同一个临界区里"

    def test_settlement_path_never_nests_the_lock(self):
        """持锁方法的临界区里，对 self 的直接调用必须**恰好**是已持锁 helper。

        ``_lock`` 不可重入 ⇒ 在临界区里调任何会自己取锁的方法就是死锁，而死锁在
        atexit 期表现为「进程挂住」，比翻红难查得多。

        ⚠️ 收紧（Codex round-1 MEDIUM-7）：旧写法是黑名单
        ``("ledger", "unaccounted_blocked", "summary_line", "take")`` —— 名单外的任何
        新公共读接口一律漏网。改成白名单：临界区内 ``self.<name>()`` 的 ``<name>``
        必须落在以 ``_locked`` 结尾的方法集里。该集合从源码 AST 导出，并与手写清单做
        **相等**断言 —— 新增一个 ``_locked`` helper 会当场把这条门顶红，逼人确认它
        确实不再取锁，而不是让白名单悄悄变宽。

        受检方法也从源码导出（凡是有 ``with self._lock:`` 的都算），不写死名单。
        """
        allowed = _locked_helper_names()
        assert allowed == {"_unaccounted_locked", "_ledger_locked"}, (
            f"_GuardState 的 _locked 方法集漂移了：{sorted(allowed)} —— "
            "新增的『已持锁』helper 会自动进白名单，先确认它体内确实不再取 self._lock"
        )
        checked: list[str] = []
        for method in _guard_state_ast().body:
            if not isinstance(method, ast.FunctionDef):
                continue
            for critical in ast.walk(method):
                if not (
                    isinstance(critical, ast.With)
                    and critical.items
                    and _is_self_attr(critical.items[0].context_expr, "_lock")
                ):
                    continue
                checked.append(method.name)
                for name in _direct_self_calls(critical):
                    assert name in allowed, (
                        f"{method.name} 的临界区里调了 self.{name}() —— 不在已持锁 helper "
                        f"白名单 {sorted(allowed)} 内；_lock 不可重入，调了就是死锁"
                    )
        assert checked, "一个 with self._lock 都没找到 —— 判据失去锚点，先核 _GuardState"

    def test_audit_hook_reads_the_settlement_state_through_record(self):
        """hook 不得再对结算标志做**锁外读**（这正是被修掉的那个缺陷）。

        ⚠️ 收紧（Codex round-1 MEDIUM-7）：旧写法只查旧拼写 ``_FINALIZING``，于是
        ``if STATE.finalizing:`` 这种**新拼写**的锁外读照样漏网 —— 而它正是同一个
        缺陷（锁外读标志 + 另一把锁记账，两步之间的夹缝整条丢记录）。现在按 AST 数
        ``finalizing`` 这个属性名在 hook 里出现的次数，必须是 0。
        """
        called = _called_names(_fn_ast(guard._audit_hook))
        assert "record" in called, "hook 必须经 record() 拿归宿"
        src = inspect.getsource(guard._audit_hook)
        assert "_FINALIZING" not in src, "hook 里又出现了锁外读的模块级结算标志"
        reads = [
            n for n in ast.walk(_fn_ast(guard._audit_hook)) if isinstance(n, ast.Attribute) and n.attr == "finalizing"
        ]
        assert not reads, (
            f"hook 里出现了 {len(reads)} 处 .finalizing 属性访问 —— 那是锁外读结算标志，判定必须留在 record() 的锁内"
        )

    def test_record_does_not_format_the_address_inside_the_lock(self):
        """``repr(address)`` 必须在 ``self._lock`` **外面**算（Codex round-1 MEDIUM-8）。

        ``address`` 完全由调用方给，``__repr__`` 是任意用户代码。在临界区里调它有两个
        后果：回调 :meth:`ledger` ⇒ 再取同一把**不可重入**的锁 ⇒ 自死锁（表现为进程
        挂住）；抛异常 ⇒ 从 ``total += 1`` **之前**逃出去 ⇒ 这次尝试整条不进账。

        两条断言配着用：临界区里不做格式化（既不 ``repr`` 也不 ``_safe_repr``），
        **且** ``record`` 里仍然有一次 ``_safe_repr`` —— 只断前者的话，把格式化整个
        删掉（账本从此没有地址）也能过。
        """
        withs = _self_lock_with_nodes(guard._GuardState.record)
        assert len(withs) == 1, f"record() 应恰有一个 self._lock 临界区，实测 {len(withs)}"
        formatting = {"repr", "_safe_repr"}
        inside = set(_called_names(withs[0])) & formatting
        assert not inside, (
            f"record() 在锁内做地址格式化（{sorted(inside)}）—— __repr__ 回调 ledger() 会自死锁，抛异常则整条跳过记账"
        )
        assert "_safe_repr" in _called_names(_fn_ast(guard._GuardState.record)), (
            "record() 里已经没有地址格式化了 —— 账本会丢掉地址这一列"
        )

    def test_block_message_binds_the_reason_despite_a_hostile_repr(self, isolated_state):
        """拒因里的 ``BLOCK_REASON`` 绑定不得被恶意 ``__repr__`` 劫持（MEDIUM-8 后半）。

        同一条受拦路径上格式化地址的有两处：``record``（已由上一条门锁住）与
        ``_block_message``。后者决定**拒因文本** —— 裸 ``{address!r}`` 时，地址的
        ``__repr__`` 抛什么，逃出 hook 的就是什么：父进程与探针全按
        ``BLOCK_REASON in str(e)`` 判「红得是因为这件事」，这个绑定一断，
        「连接没发生」还在，「红的原因可归因」没了。

        判据放在**最远下游**（真 ``sys.audit`` 走完整条承重路径，不是直接调
        ``_block_message``）：地址是 tuple 子类（``extract_port`` 按底层槽位照常取到
        7691、进受拦分支），``__repr__`` 抛异常 —— 抛出的 ``RuntimeError`` 必须仍以
        ``BLOCK_REASON`` 开头，且账已记上。
        """

        class BoomAddr(tuple):
            def __new__(cls):
                return tuple.__new__(cls, ("127.0.0.1", 7691))

            def __repr__(self):
                raise RuntimeError("__repr__ 故意抛出 —— 不得劫持拒因绑定")

        with pytest.raises(RuntimeError, match=guard.BLOCK_REASON):
            import sys as _sys

            _sys.audit("socket.connect", None, BoomAddr())

        assert isolated_state.blocked == 1 and isolated_state.total == 1
        assert isolated_state.records[0]["address"] == "<unrepr BoomAddr>"

    def test_record_survives_an_address_whose_repr_raises(self, isolated_state):
        """地址的 ``__repr__`` 抛异常，仍必须 ``total += 1`` 且归宿正确（MEDIUM-8）。"""

        class Boom:
            def __repr__(self):
                raise RuntimeError("__repr__ 故意抛出 —— 不得让这次尝试逃出账本")

        assert isolated_state.record(Boom()) == guard.RECORD_BLOCK
        assert isolated_state.total == 1 and isolated_state.blocked == 1
        assert isolated_state.records[0]["address"] == "<unrepr Boom>"
        assert isolated_state.late_snapshot()["unaccounted"] == 1

    def test_record_does_not_deadlock_when_repr_reads_the_ledger(self, isolated_state, monkeypatch):
        """地址的 ``__repr__`` 回调 ``ledger()`` 不得自死锁（MEDIUM-8）。

        ``_lock`` 不可重入：repr 若在锁内跑（正是本门要抓的回退），worker 会**永久
        持有** ``isolated_state._lock``。判定用独立线程 + ``Event.wait(10)`` ——
        主线程超时即翻红。

        ⚠️ 两处写法是「红真的能落地」的前提（自查 HIGH 修正，2026-09-08；初版两处
        都没做，回退一旦发生是**整条 session 挂住**而不是一条红 —— conftest 哨兵
        ``pytest_runtest_makereport`` 会在 call 报告期无超时地 ``STATE.take()``，取的
        正是那把已被永久持有的锁）：

        * ``__repr__`` **闭包引用 fixture 实例**（``isolated_state.ledger()``）而不是
          读 ``guard.STATE`` —— 要复现的就是「回调**同一个**正在记账的 state」这个
          死锁形态；经 ``guard.STATE`` 间接读会让复现依赖 monkeypatch 的摆法。
        * ``guard.STATE`` 在本用例内被指到**另一份全新 state**：fixture 换进来的那把
          锁一旦被回退卡死，session 里所有走 ``guard.STATE`` 的消费者（哨兵 ``take``
          / ``summary_line``）碰的都是这份新的，照常返回；卡死的 worker 只是一个
          daemon 线程，随进程退出。monkeypatch 在 teardown 期自动还原，真 STATE
          不受影响。
        """

        class Reentrant:
            def __repr__(self) -> str:
                return f"<addr unaccounted={isolated_state.ledger()['unaccounted']}>"

        monkeypatch.setattr(guard, "STATE", guard._GuardState())
        done = threading.Event()
        outcome: list = []

        def run() -> None:
            try:
                outcome.append(isolated_state.record(Reentrant()))
            finally:
                done.set()

        worker = threading.Thread(target=run, name="w4-repr-reentrant", daemon=True)
        worker.start()
        assert done.wait(10), "record() 挂住了 —— repr 在锁内回调 ledger()，不可重入锁自死锁"
        assert outcome == [guard.RECORD_BLOCK]
        assert isolated_state.total == 1
        assert isolated_state.records[0]["address"] == "<addr unaccounted=0>"

    def test_module_level_finalizing_global_is_gone(self):
        """模块级 ``_FINALIZING`` 必须整个消失，不能只是「没人读」。

        留着一个同名全局，下一个人很容易顺手再读它一次 —— 缺陷就回来了。
        """
        assert not hasattr(guard, "_FINALIZING")


class TestSingleLedgerSnapshot:
    """裁定与落盘必须是**同一个 dict 对象**。"""

    def test_final_accounting_hands_its_own_snapshot_to_write_ledger(self, isolated_state, monkeypatch, tmp_path):
        """身份断言，不是等值断言。

        ``==`` 会被「两次快照恰好内容相同」骗过 —— 而内容相同正是绝大多数时候的
        情形，缺陷只在那条记录恰好落在两次之间时才现形。要锁的是「只取了一次」，
        所以判据必须是 ``is``。
        """
        taken: list[dict] = []
        original = isolated_state.finalize_and_snapshot

        def spy_finalize():
            snap = original()
            taken.append(snap)
            return snap

        captured: dict = {}

        def fake_write(path, ledger=None):
            captured["path"] = path
            captured["ledger"] = ledger

        def forbidden_ledger():
            raise AssertionError("结算路径又去取了第二次快照（STATE.ledger()）")

        monkeypatch.setattr(isolated_state, "finalize_and_snapshot", spy_finalize)
        monkeypatch.setattr(isolated_state, "ledger", forbidden_ledger)
        monkeypatch.setattr(guard, "write_ledger", fake_write)
        monkeypatch.setenv(guard.ENV_LEDGER, str(tmp_path / "ledger.json"))

        guard._final_accounting()

        assert len(taken) == 1, "结算快照必须恰好取一次"
        assert captured["ledger"] is taken[0], "落盘写的不是裁定用的那一份快照"

    def test_settlement_paths_publish_instead_of_writing_directly(self):
        """两条写盘路径都必须经 ``_publish_ledger``（Codex round-1 MEDIUM-4）。

        结算与迟到重写各自「先取快照、后 ``open(path,"w")`` 整写」，中间没有发布顺序
        控制：结算取到零账快照 → 迟到线程记账并写出 ``unaccounted=1`` → 结算拿旧快照
        把文件盖回零账 → 迟到线程 ``os._exit(3)``。进程 rc=3 而文件说什么都没发生。

        三条断言配着用：两条路径各自**只**调 ``_publish_ledger``；且全模块的
        ``write_ledger()`` 调用点恰好落在 ``_publish_ledger`` 里 —— 少了第三条，
        「在别处新开一个直写调用点」这条路照样通。

        行为面在探针 ``guard-late-ledger-survives-stale-final-write``。
        """
        for func in (guard._final_accounting, guard._rewrite_ledger_after_late_record):
            called = _called_names(_fn_ast(func))
            assert "_publish_ledger" in called, f"{func.__name__} 没走 _publish_ledger"
            assert "write_ledger" not in called, (
                f"{func.__name__} 直接调了 write_ledger —— 绕过发布顺序，陈旧快照能盖掉新账"
            )
        callers = _callers_of("write_ledger")
        assert callers == ["_publish_ledger"], f"write_ledger() 的调用点应恰好只有 _publish_ledger 一处，实测 {callers}"

    def test_publish_ledger_refuses_a_stale_snapshot(self, tmp_path, isolated_state):
        """序号落后的快照**不得**回写（MEDIUM-4 的判定本体）。

        这里不造线程交错（那在探针里），只把 ``_publish_ledger`` 的判定本身钉死：
        先发布新的、再拿旧的去发布，文件必须一字不动。

        用 ``late_snapshot()`` 而不是 ``ledger()`` 取快照 —— 发布序只盖在**要发布的**
        快照上，纯读取不消耗序号（见 ``_ledger_locked`` 的 ``stamp``）。
        """
        path = str(tmp_path / "ledger.json")
        stale = isolated_state.late_snapshot()
        isolated_state.record(("127.0.0.1", 7691))
        fresh = isolated_state.late_snapshot()
        assert fresh["seq"] > stale["seq"], "账本快照没有单调序 —— 发布顺序无从判起"

        assert guard._publish_ledger(path, fresh) is True
        assert json.loads(Path(path).read_text(encoding="utf-8"))["unaccounted"] == 1
        assert guard._publish_ledger(path, stale) is False, "陈旧快照被回写了"
        assert json.loads(Path(path).read_text(encoding="utf-8"))["unaccounted"] == 1

    def test_publish_ledger_accepts_a_newer_snapshot(self, tmp_path, isolated_state):
        """验伪锚：序号更大的快照必须照常发布（不是「恒拒绝」）。"""
        path = str(tmp_path / "ledger.json")
        first = isolated_state.late_snapshot()
        assert guard._publish_ledger(path, first) is True
        isolated_state.record(("127.0.0.1", 7691))
        later = isolated_state.late_snapshot()
        assert guard._publish_ledger(path, later) is True
        assert json.loads(Path(path).read_text(encoding="utf-8"))["unaccounted"] == 1

    def test_publish_ledger_refuses_stale_even_after_a_failed_write(self, tmp_path, isolated_state, monkeypatch):
        """新快照写盘**失败**后，陈旧快照仍然不得回写（I/O 失败不得重开 MEDIUM-4 的门）。

        初版把 ``_PUBLISHED_SEQ = seq`` 放在 ``write_ledger`` 成功之后：较新的那份写
        失败（磁盘满 / 权限）⇒ 序号没动 ⇒ 紧接着的陈旧发布 ``seq <= _PUBLISHED_SEQ``
        判假 ⇒ 照写 ⇒ 文件是合法的零账 JSON 而进程 rc=3 —— MEDIUM-4 关掉的交错从
        I/O 失败这条缝里原样回来。先行推进后，失败方向是「更旧的也别写」：文件根本
        不存在 / 停留在上一份的完好内容，父进程要么读到新账、要么 ``json.loads``
        直接报错 —— 可辨识的坏，不是可信的谎。
        """
        path = str(tmp_path / "ledger.json")
        calls = {"n": 0}
        real_write = guard.write_ledger

        def flaky_write(p, ledger=None):
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError("磁盘满（负控：新快照的写盘失败）")
            return real_write(p, ledger)

        monkeypatch.setattr(guard, "write_ledger", flaky_write)
        stale = isolated_state.late_snapshot()
        isolated_state.record(("127.0.0.1", 7691))
        fresh = isolated_state.late_snapshot()
        assert fresh["seq"] > stale["seq"]

        # 新快照写盘失败：异常照常向上传（调用点各自的 try 负责），不吞不藏
        with pytest.raises(OSError, match="磁盘满"):
            guard._publish_ledger(path, fresh)
        # 随后的陈旧发布必须被拒 —— 且根本轮不到写盘（第二次调用是成功的）
        assert guard._publish_ledger(path, stale) is False, (
            "新快照写盘失败后，陈旧快照反而写成功了 —— I/O 失败把 MEDIUM-4 的门重开了"
        )
        assert calls["n"] == 1, "陈旧那次真的调了 write_ledger —— 判据被假喂饱了"
        assert not Path(path).exists()

    def test_plain_ledger_read_does_not_consume_a_publish_seq(self, isolated_state):
        """「随手看一眼账面」不得推进发布序（2026-09-08 实测教训）。

        起初把 ``seq`` 加在 ``_ledger_locked`` 的无条件路径上，于是**纯读取**也自增 ——
        探针 ``guard-finalize-seam-inert-when-unset`` 的「前后账本逐字节相同」当场恒假、
        转红。那是本设计的错（读不该有副作用），不是那道判据该让路，所以序号收窄到只盖
        在要发布的快照上。这条门把「读无副作用」钉住，防止再被放回无条件路径。
        """
        first = isolated_state.ledger()
        second = isolated_state.ledger()
        assert "seq" not in first and "seq" not in second, "ledger() 这种纯读取不该带发布序"
        assert first == second, "两次纯读取之间账本变了 —— 读取有副作用"
        assert "seq" in isolated_state.late_snapshot(), "要发布的快照必须带发布序"

    def test_write_ledger_dumps_exactly_what_it_is_given(self, tmp_path):
        """给了快照就写那一份，不得自己再取一次（那正是双快照的来源）。"""
        path = tmp_path / "ledger.json"
        handed = {"total": 41, "blocked": 7, "advisory": 0, "unaccounted": 7}
        guard.write_ledger(str(path), handed)
        assert json.loads(path.read_text(encoding="utf-8")) == handed

    def test_write_ledger_without_a_snapshot_still_works_standalone(self, tmp_path, isolated_state):
        """``ledger=None`` 是**结算之外**的独立调用留的口子，必须仍然可用。"""
        path = tmp_path / "ledger.json"
        guard.write_ledger(str(path))
        assert json.loads(path.read_text(encoding="utf-8"))["total"] == 0


class TestInstallOrder:
    """T-14：承重 hook 必须装在任何预检之前。"""

    def test_audit_hook_is_installed_before_the_target_precheck(self):
        """``install()`` 体内 ``_install_audit_hook()`` 必须排在预检之前。

        行为面的证明是探针 ``guard-install-order-precheck-is-guarded``
        （在预检内部真发一次连接，看它被不被拦 + 记不记账）。这里锁的是顺序本身 ——
        进程内跑一次 ``install()`` 只会看到一个已经装好的门，顺序观测不到。

        ⚠️ 下标只数**可达**语句（``_live_called_names``，Codex round-1 MEDIUM-7）：旧写法
        用 ``_called_names`` 走 ``ast.walk``，于是 ``if False: _install_audit_hook()``
        这条死代码也算数 —— 把诱饵摆在前面、真调用挪到预检之后，旧门照样绿。
        """
        node = _fn_ast(guard.install)
        hook_at = precheck_at = None
        for index, stmt in enumerate(node.body):
            names = _live_called_names(stmt)
            if hook_at is None and "_install_audit_hook" in names:
                hook_at = index
            if precheck_at is None and "assert_neo4j_target_blocked" in names:
                precheck_at = index
        assert hook_at is not None, "install() 里找不到（可达的）_install_audit_hook()"
        assert precheck_at is not None, "install() 里找不到（可达的）assert_neo4j_target_blocked()"
        assert hook_at < precheck_at, (
            "承重 hook 装在预检之后 —— 预检（含 canonical_target_ports 的延迟 "
            "import neo4j）整段在门外，那里的连接既不被拦也不进账"
        )

    def test_final_accounting_is_registered_before_the_precheck(self):
        """结算器必须排在预检**之前**（Codex round-1 HIGH-2 的翻转）。

        ⛔ 旧断言要求的是**预检下标在注册下标之前**（本用例旧名
        ``…_registered_after_the_precheck``），docstring 写「相对顺序不变：预检抛出时
        就该拒绝装门，不留一个会 os._exit 的 atexit」——**那把缺陷钉成了规格**。
        （旧断言原文见 ``_bmad-output/审查/evidence-w44b/d-old-contract-verbatim.txt``；
        这里刻意不复写它的字面量，好让「旧写法已绝迹」可以用 grep 判。）
        真实情形是：``_install_audit_hook()`` 摘不掉（CPython 无
        ``sys.removeaudithook``），预检抛出时 hook 已经不可撤销地生效、照常拦照常记账，
        而结算器没注册 —— 那些记录无人交账，进程 ``exit 0``（Codex 实测
        ``audit_installed=True / final_registered=False / unaccounted=1 / rc=0``）。

        「不留 atexit」这个目标本身是错的：atexit 处理器不是负担而是**责任**。正确目标
        是「装了 hook 就必有结算」，所以顺序反过来，断言也跟着反过来。零账时最终总账
        不改退出码，留下它没有代价。

        行为面在 ``test_partial_install_still_registers_final_accounting``（同类）与探针
        ``guard-partial-install-settles-late-connection``。
        """
        node = _fn_ast(guard.install)
        precheck_at = register_at = hook_at = None
        for index, stmt in enumerate(node.body):
            names = _live_called_names(stmt)
            if precheck_at is None and "assert_neo4j_target_blocked" in names:
                precheck_at = index
            if register_at is None and "register_final_accounting" in names:
                register_at = index
            if hook_at is None and "_install_audit_hook" in names:
                hook_at = index
        assert precheck_at is not None and register_at is not None and hook_at is not None
        assert register_at < precheck_at, (
            "结算器注册排在预检之后 —— 预检抛出时 hook 已不可撤销地生效却无人结账，"
            "迟到连接以 rc=0 收场（Codex round-1 HIGH-2）"
        )
        assert hook_at < register_at, (
            "结算器排到了 hook 前面 —— 本门的因果是单向的「装了 hook 就必有结算」，"
            "倒过来写会把这条因果读反（纵深断言；``_install_audit_hook`` 唯一的抛出点"
            "是模块单例冲突，而那蕴含另一份实例已装 hook）"
        )

    def test_partial_install_still_registers_final_accounting(self, monkeypatch):
        """预检抛出 ⇒ 装门失败，但**结算器必须已经注册**（Codex round-1 HIGH-2）。

        ``_install_audit_hook()`` 不可撤销（CPython 无 ``sys.removeaudithook``）。旧顺序
        把 ``register_final_accounting()`` 排在预检之后，于是
        ``W4_GUARD_REQUIRE_BLOCKED_TARGET=1`` 而目标不在射程内时，进程停在
        「hook 已生效 / 结算器没注册 / ``STATE.installed`` 仍 False」这个**部分安装态** ——
        此后被拦下的连接照常记账，却没有任何人在退出时把账交出来，进程 ``exit 0``。

        断言两条缺一不可：``_FINAL_REGISTERED`` 置位，**且**注册进 atexit 的确实是
        ``_final_accounting``。只断前者会被「把 ``_FINAL_REGISTERED = True`` 挪到预检
        之前但不真注册」骗过 —— 判据必须绑定「是哪一层做的」。

        行为面（真的走一遍部分安装态、看进程 rc）在探针
        ``guard-partial-install-settles-late-connection`` 里；那条要跑到进程退出，
        pytest 进程内做不了。
        """
        registered: list = []

        class _FakeAtexit:
            """只替换 ``guard`` 命名空间里的 ``atexit``，真模块一动不动。

            本用例必须把 ``_FINAL_REGISTERED`` 复位才观测得到注册动作，而真注册会给
            本进程留下**第二个** ``_final_accounting`` 处理器 —— monkeypatch 撤不回
            ``atexit.register``，那是不可撤销的进程级副作用。
            """

            @staticmethod
            def register(func, *args, **kwargs):
                registered.append(func)
                return func

        def boom() -> None:
            raise RuntimeError("预检故意抛出 —— 目标不在受拦集合内")

        monkeypatch.setenv(guard.ENV_REQUIRE_BLOCKED_TARGET, "1")
        monkeypatch.setattr(guard, "assert_neo4j_target_blocked", boom)
        monkeypatch.setattr(guard, "atexit", _FakeAtexit)
        monkeypatch.setattr(guard, "_FINAL_REGISTERED", False)

        with pytest.raises(RuntimeError, match="预检故意抛出"):
            guard.install()

        assert guard._FINAL_REGISTERED is True, (
            "预检抛出后结算器没注册 —— audit hook 已不可撤销地生效、照常记账，"
            "却没有人在退出时结账：迟到连接以 rc=0 收场"
        )
        assert registered == [guard._final_accounting], f"注册进 atexit 的不是 _final_accounting：{registered!r}"


class TestPrecheckBeforeExemption:
    """T-10：``NEO4J_TEST_URI`` 预检必须早于任何豁免作用域。"""

    def test_begin_item_refuses_exemption_before_the_precheck(self, isolated_state):
        """预检没完成 ⇒ integration 路径的连接**不得**被记成 advisory。

        这正是旧接线的洞：预检跑在 session fixture 里，而 session fixture 的 setup
        跑在首个用例的 ``runtest_protocol`` 之内 —— 首个用例若在 tests/integration，
        预检整段都在豁免窗口里。
        """
        assert isolated_state.precheck_done is False
        guard.begin_item("tests/integration/test_x.py::test_y", True)
        try:
            assert guard._EXEMPT_CV.get() is False, "预检未完成却发了豁免票"
            assert isolated_state.record(("127.0.0.1", 7691)) == guard.RECORD_BLOCK
            assert isolated_state.advisory == 0 and isolated_state.blocked == 1
        finally:
            guard.end_item()

    def test_begin_item_grants_exemption_after_the_precheck(self, isolated_state):
        """反向锚：预检完成后豁免照常发 —— 否则上一条只证明了「永远不豁免」。"""
        isolated_state.precheck_done = True
        guard.begin_item("tests/integration/test_x.py::test_y", True)
        try:
            assert guard._EXEMPT_CV.get() is True
            assert isolated_state.record(("127.0.0.1", 7691)) == guard.RECORD_ADVISORY
        finally:
            guard.end_item()

    def test_successful_precheck_marks_done(self, isolated_state, monkeypatch):
        monkeypatch.setenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7692")
        guard.assert_test_uri_not_blocked()
        assert isolated_state.precheck_done is True

    def test_unset_test_uri_still_marks_done(self, isolated_state, monkeypatch):
        """没配测试容器 URI = 射程外，预检算完成（否则整条会话永久失去豁免）。"""
        monkeypatch.delenv("NEO4J_TEST_URI", raising=False)
        guard.assert_test_uri_not_blocked()
        assert isolated_state.precheck_done is True

    def test_failed_precheck_does_not_mark_done(self, isolated_state, monkeypatch):
        """预检失败 ⇒ 标志保持关闭 ⇒ 豁免继续关着（fail-closed）。"""
        monkeypatch.setenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7691")
        with pytest.raises(RuntimeError):
            guard.assert_test_uri_not_blocked()
        assert isolated_state.precheck_done is False

    @pytest.mark.parametrize(
        "module_path",
        [
            Path(__file__).resolve().parents[1] / "conftest.py",
            Path(__file__).resolve().parents[1] / "support" / "guard_plugin.py",
        ],
        ids=["root-conftest", "guard-plugin"],
    )
    def test_precheck_lives_in_pytest_configure_not_in_a_session_fixture(self, module_path):
        """两处接线都必须把预检放在 ``pytest_configure``，而不是 session fixture。

        放回 fixture 里就等于把它塞进首个用例的 ``begin_item(exempt=…)`` 作用域。
        """
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        found_in: list[str] = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and "assert_test_uri_not_blocked" in _called_names(node):
                found_in.append(node.name)
        assert found_in == ["pytest_configure"], (
            f"{module_path.name} 里预检出现在 {found_in}；必须且只能在 pytest_configure"
        )


class TestFinalizeRaceSeam:
    """注入点：未替换时完全惰性，被替换时当场算漂移。"""

    def test_seam_is_the_noop_by_default(self):
        assert guard._finalize_race_seam_hook is guard._finalize_race_seam
        assert guard._finalize_race_seam_hook() is None

    def test_seam_body_is_empty(self):
        """默认注入点的函数体只有 docstring —— 没有任何可执行语句。"""
        body = _fn_ast(guard._finalize_race_seam).body
        assert len(body) == 1 and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)

    def test_seam_is_called_unconditionally_not_inside_a_condition(self):
        """注入点必须是**受拦分支里的一条独立语句**，且不出现在任何判据里。

        ⚠️ 收紧（Codex round-1 MEDIUM-7）：旧写法只要求「没进 ``if`` 的条件」+「存在
        某条含它的 ``Expr``」，于是 ``if False: _finalize_race_seam_hook()`` 照样绿 ——
        注入点被摘掉而门看不见。四条子规则：

        (i)   它是一条独立 ``Expr``（保留旧断言的这一半）；
        (ii)  它落在**受拦分支**内 —— 即 ``_audit_hook`` 里那个 ``if port in
              BLOCKED_PORTS or not port_is_trustworthy(address)`` 的 ``body`` 子树。
              该 ``If`` 用 AST 定位而不是写死行号；**定位不到就报红**（提示去核
              ``_audit_hook`` 的受拦判据），不是默默放行 —— 找不到锚点却当通过，是
              判据恒真的经典写法；
        (iii) 祖先链上不得有**恒假分支**（``if False:`` / ``while 0:`` 之类）；
        (iv)  它不得出现在任何 ``If`` / ``While`` / ``IfExp`` 的 ``test`` 或 ``BoolOp``
              的短路项里（旧断言的另一半，保留）。

        (v) ``Try`` **允许**并且必须允许：现状里它就包在 ``try/except BaseException``
        里，那是 Codex round-1 HIGH-1 的整改本身（seam 抛异常不得跳过记账）。所以
        「祖先链不含任何复合语句」这种写法是**自伤门** —— 它在未改动的代码上就直接红。
        """
        seam = "_finalize_race_seam_hook"
        node = _fn_ast(guard._audit_hook)
        parents = _parent_map(node)

        # (iv) 不得进任何判据
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.IfExp)):
                assert seam not in _called_names(child.test), "注入点进了分支条件"
            if isinstance(child, ast.BoolOp):
                for value in child.values:
                    assert seam not in _called_names(value), "注入点进了布尔短路判据"

        # (i) 恰好一处调用，且是一条独立语句
        calls = [
            n for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == seam
        ]
        assert len(calls) == 1, f"注入点调用点应恰好 1 处，实测 {len(calls)}"
        seam_call = calls[0]
        assert isinstance(parents.get(seam_call), ast.Expr), "注入点必须是一条独立的调用语句"

        # 祖先链（由内到外）
        chain: list[ast.AST] = []
        cursor = parents.get(seam_call)
        while cursor is not None:
            chain.append(cursor)
            cursor = parents.get(cursor)

        # (iii) 祖先链上没有恒假分支
        for ancestor in chain:
            assert not _is_dead_branch(ancestor), (
                "注入点落在恒假分支里 —— 等于被摘掉，而『存在一条含它的 Expr』照样成立"
            )

        # (ii) 必须落在受拦分支的 body 里
        guarded = [
            n
            for n in ast.walk(node)
            if isinstance(n, ast.If)
            and ("BLOCKED_PORTS" in _referenced_names(n.test) or "port_is_trustworthy" in _called_names(n.test))
        ]
        assert guarded, (
            "在 _audit_hook 里定位不到受拦分支（test 含 BLOCKED_PORTS 或 "
            "port_is_trustworthy 的那个 if）—— 受拦判据的措辞变了，先核 _audit_hook "
            "的 event/port 两层 if，再决定这条门怎么改"
        )
        assert any(any(_contains(stmt, seam_call) for stmt in branch.body) for branch in guarded), (
            "注入点不在受拦分支内 —— 它会对每一次 socket.connect 触发，而它存在的理由只是在『即将记账』那一点制造交错"
        )

    def test_seam_replacement_is_detected_as_drift(self, monkeypatch):
        """有人拿注入点当旁路 ⇒ 下一个用例边界就 GuardDrift。"""
        monkeypatch.setattr(guard, "_finalize_race_seam_hook", lambda: None)
        with pytest.raises(guard.GuardDrift, match="注入点"):
            guard.assert_guard_live("unit test: seam replaced")

    def test_seam_untouched_passes_liveness(self):
        """反向锚：没动它时自证照常通过。"""
        guard.assert_guard_live("unit test: seam intact")

    def test_throwing_seam_cannot_skip_accounting(self, isolated_state, monkeypatch):
        """注入点抛异常**不得**跳过记账（Codex round-1 HIGH-1）。

        原实现里 seam 的调用没有包 try：替换成一个抛 ``RuntimeError`` 的函数之后，
        连接确实被阻断了（异常传给调用方），但 ``STATE.record()`` 根本没跑到 ⇒
        账本为零、进程 exit 0 —— 这个「只为测试存在」的缝就成了一条跳过记账的旁路。
        Codex 独立实测得到 ``blocked=0, unaccounted=0``、子进程退出 0。

        现在 seam 被 ``try/except BaseException`` 包住，它对控制流的影响面是 0：
        记账照做，非豁免连接照常抛 ``RuntimeError``。
        """

        def boom() -> None:
            raise RuntimeError("seam 故意抛出 —— 不得影响记账与拦截")

        monkeypatch.setattr(guard, "_finalize_race_seam_hook", boom)

        # 走完整条承重路径：合成一次到受拦端口的审计事件（不建立任何真实连接）
        with pytest.raises(RuntimeError, match=guard.BLOCK_REASON):
            import sys as _sys

            _sys.audit("socket.connect", None, ("127.0.0.1", 7691))

        assert isolated_state.blocked == 1, "seam 抛异常把记账整条跳过了"
        assert isolated_state.total == 1
        assert isolated_state.late_snapshot()["unaccounted"] == 1
