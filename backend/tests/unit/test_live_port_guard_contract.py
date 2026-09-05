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
        "ftp://127.0.0.1:7692",
        "http://127.0.0.1:7692",
        "https://127.0.0.1:7692",
        "bolt+routing://127.0.0.1:7692",
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
    LEGITIMATE_CONTAINER_URIS = [
        "bolt://127.0.0.1:7692",
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

    def test_ledger_shape(self):
        led = guard.STATE.ledger()
        for key in ("total", "blocked", "advisory", "billed", "unaccounted", "reported_status", "installed"):
            assert key in led, f"账本缺字段 {key} —— 父进程复核会读它"
        assert led["installed"] is True
