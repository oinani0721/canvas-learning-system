"""CARD-W4-SENTINEL-REBIND [BATCH-2026-09-11-第十四批]

W4 哨兵判据由「会漂移的 nodeid 集」改绑到两个不变量，外加 conftest 卫生快照的 sha 三态。

⛔ 本卡要解决的病：同一份代码**原样重跑两次**，W4 哨兵红会挂到**不同的 nodeid** 上
（U10-A 实测 ``candidate422`` ↔ ``mock_warning``），因为哨兵红归属取决于哪个用例恰好
触发了那次 lifespan 健康检查 —— 与代码无关。逐 nodeid diff 因此自带 flaky，不能当判据。

改绑到：① 被拦下的次数；② 失败正文身份（地址 + 线程类别）。

⚠️ **本文件里的口径更正（与卡文字面冲突，依据见
``_bmad-output/审查/evidence-w4-sentinel-rebind/coverage-corrections-*.txt``）**：

* 更正③ 失败正文产出点是 **3** 处不是 2 处（多一个 ``backend/tests/conftest.py:184``）
  ⇒ 同一条记录可被印两次 ⇒ **只判集合、不判条数**；
* 更正④ 线程名里的 ``asyncio-portal-<hex>`` 是**对象地址、每跑不同**
  ⇒ 照卡文字面拿整串当身份，新判据会**原样继承它要替换掉的那个 flaky**
  ⇒ 身份必须**归一线程名**（抹地址、留类别）；
* 更正⑤ 两个 ``blocked=`` 产出点是同一**单调**计数器的两个时刻（``:282`` 归零、
  ``:355``/``:361`` 只 ``+= 1``），**不等是合法的**
  ⇒ 不变量是 ``final >= summary``，不是卡文写的「必须相等」。
"""

from __future__ import annotations

import pytest

from tests.support.hygiene_snapshot_tristate import classify_sha_change
from tests.support.w4_sentinel_identity import (
    W4LedgerConflict,
    blocked_count,
    failure_body_identities,
    naive_failed_nodeids,
    summary_quad,
)

# ═══════════════════════════════════════════════════════════════════════════
# 固定样本：复刻 U10-A 的「同 blocked、异 nodeid」形态（卡文 (e)）
# ⛔ 逐字复制产出点格式，含全角 —— / ： / ；。抄成半角 = 判据锚的是想象中的格式。
# ═══════════════════════════════════════════════════════════════════════════

#: r4 那一跑：哨兵红挂在 candidate422 上。
SAMPLE_R4 = """\
============================= test session starts ==============================
collected 5141 items

tests/unit/test_candidate_service.py .....F....                           [ 12%]
tests/unit/test_mock_degradation_transparency.py .........                [ 34%]

=================================== FAILURES ===================================
______________ test_accept_candidate_already_accepted_returns_422 ______________
live Neo4j port connect attempted —— 本用例期间有 1 次到现网 Neo4j 的连接尝试被拦下。
（连接处抛出的异常被 app/main.py 的 lifespan try/except 吞掉了，
  所以由本哨兵把它转成用例失败——否则这道门什么都证明不了。）
  - ('::1', 7691, 0, 0) on thread MainThread (owner=tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422)
=========================== short test summary info ============================
FAILED tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)
= 1 failed, 5140 passed in 401.42s =
"""

#: r4b 那一跑：**同一份代码原样重跑**，哨兵红改挂在 mock_warning 上。
#: 两个不变量（blocked 次数、失败正文身份）逐字不变，变的只有 nodeid 归属。
SAMPLE_R4B = """\
============================= test session starts ==============================
collected 5141 items

tests/unit/test_candidate_service.py ..........                           [ 12%]
tests/unit/test_mock_degradation_transparency.py ....F....                [ 34%]

=================================== FAILURES ===================================
_____________ TestMockScoringWarningLogs.test_mock_mode_logs_warning ___________
live Neo4j port connect attempted —— 本用例期间有 1 次到现网 Neo4j 的连接尝试被拦下。
（连接处抛出的异常被 app/main.py 的 lifespan try/except 吞掉了，
  所以由本哨兵把它转成用例失败——否则这道门什么都证明不了。）
  - ('::1', 7691, 0, 0) on thread MainThread (owner=tests/unit/test_mock_degradation_transparency.py::TestMockScoringWarningLogs::test_mock_mode_logs_warning)
=========================== short test summary info ============================
FAILED tests/unit/test_mock_degradation_transparency.py::TestMockScoringWarningLogs::test_mock_mode_logs_warning
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)
= 1 failed, 5140 passed in 398.77s =
"""

#: 更正④ 的样本：线程名带每跑不同的对象地址。两份「同一份代码重跑」只差 hex。
SAMPLE_PORTAL_RUN1 = """\
live Neo4j port connect attempted —— 本用例期间有 1 次到现网 Neo4j 的连接尝试被拦下。
  - ('::1', 7691, 0, 0) on thread asyncio-portal-15f0ef460 (owner=tests/unit/test_startup_health_check.py::TestStartupCheck::test_endpoint_exists)
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)
"""

SAMPLE_PORTAL_RUN2 = """\
live Neo4j port connect attempted —— 本用例期间有 1 次到现网 Neo4j 的连接尝试被拦下。
  - ('::1', 7691, 0, 0) on thread asyncio-portal-14867cb40 (owner=tests/unit/test_startup_health_check.py::TestStartupCheck::test_endpoint_exists)
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)
"""


class TestSampleFidelity:
    """样本必须真的复刻 U10-A 形态，否则后面所有断言都是在测想象中的输入。"""

    def test_samples_differ_only_in_attribution(self):
        """两份样本的 nodeid 归属不同 —— 这是本卡存在的前提。"""
        assert naive_failed_nodeids(SAMPLE_R4) != naive_failed_nodeids(SAMPLE_R4B), (
            "两份样本的 FAILED nodeid 集相同 —— 那就没复刻 U10-A 的归属漂移，"
            "后面『新判据相等而旧判据不等』的对照失去意义"
        )

    def test_samples_are_not_accidentally_identical(self):
        assert SAMPLE_R4 != SAMPLE_R4B


class TestBlockedCount:
    """不变量①：被拦下的次数。"""

    def test_r4_and_r4b_agree(self):
        assert blocked_count(SAMPLE_R4) == blocked_count(SAMPLE_R4B) == 1

    def test_no_gate_output_is_none_not_zero(self):
        """⛔ 找不到门产出行 ⇒ None（没查成），**不是** 0（查了，是零）。

        把「没查成」压成「没问题」正是本卡在 conftest 侧同时要收的那个病。
        """
        assert blocked_count("= 5141 passed in 400.00s =\n") is None

    def test_summary_and_final_may_differ_legitimately(self):
        """更正⑤：final >= summary 是不变量，**相等不是**。

        blocked 是单调计数器（``live_port_guard.py:282`` 归零、``:355``/``:361`` 只 ``+= 1``），
        summary 在 ``pytest_terminal_summary`` 取、final 在 atexit 取 —— 中间窗口里
        被拦下的连接会让 final 更大。卡文写的「必须相等」会把门**正常工作**的那天判成工具错误。
        """
        text = (
            "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=2 (blocked=2, advisory=0, unaccounted=0)\n"
            "*** live Neo4j port connect attempted —— 最终总账：blocked=3 "
            "unaccounted=1 reported_status=1；进程被强制以退出码 3 结束（迟到连接不得以 0 收场）***\n"
        )
        assert blocked_count(text) == 3, "final 在场时应取较晚的那个值"

    def test_counter_going_backwards_is_a_conflict(self):
        """final < summary 在单调计数器下不可能 ⇒ 混档，必须说话而不是挑一个。"""
        text = (
            "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=5 (blocked=5, advisory=0, unaccounted=0)\n"
            "*** live Neo4j port connect attempted —— 最终总账：blocked=2 "
            "unaccounted=0 reported_status=1；进程被强制以退出码 3 结束（迟到连接不得以 0 收场）***\n"
        )
        with pytest.raises(W4LedgerConflict, match="倒退"):
            blocked_count(text)

    def test_arithmetic_self_consistency_is_enforced(self):
        """total == blocked + advisory（``record()`` 每次恰加一次）。不自洽 = 伪造/拼接。"""
        with pytest.raises(W4LedgerConflict, match="自洽"):
            blocked_count("NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=9 (blocked=1, advisory=0, unaccounted=0)\n")

    def test_multiple_runs_in_one_file_is_a_conflict(self):
        """一份存档里两条汇总行 = 混了两次运行，比它没有意义。"""
        text = (
            "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)\n"
            "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=2 (blocked=2, advisory=0, unaccounted=0)\n"
        )
        with pytest.raises(W4LedgerConflict, match="混了多次运行"):
            blocked_count(text)


class TestSummaryQuad:
    """更正⑥：advisory 是「只记不拦」= 放行，只判 blocked 会把真连当没事。"""

    def test_quad_is_parsed(self):
        assert summary_quad(SAMPLE_R4) == (1, 1, 0, 0)

    def test_advisory_difference_is_visible_in_the_quad(self):
        """两份 blocked 都是 0，但一份 advisory=12 —— 那 12 次是真连上了现网。"""
        a = "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=12 (blocked=0, advisory=12, unaccounted=0)\n"
        b = "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)\n"
        assert blocked_count(a) == blocked_count(b) == 0, "单判 blocked 看不出差别"
        assert summary_quad(a) != summary_quad(b), "四元组必须看得出 advisory 的差别"


class TestFailureBodyIdentities:
    """不变量②：失败正文身份。"""

    def test_r4_and_r4b_have_the_same_identity(self):
        assert failure_body_identities(SAMPLE_R4) == failure_body_identities(SAMPLE_R4B)

    def test_identity_excludes_owner(self):
        """owner 就是那个会漂的 nodeid，必须排除在身份之外。"""
        for ident in failure_body_identities(SAMPLE_R4):
            assert "owner" not in ident
            assert "candidate" not in ident

    def test_identity_is_the_expected_string(self):
        assert failure_body_identities(SAMPLE_R4) == {"('::1', 7691, 0, 0) on thread MainThread"}

    def test_portal_thread_address_is_normalised(self):
        """⛔ 更正④：不归一线程名，新判据就原样继承了旧判据的 flaky。"""
        assert failure_body_identities(SAMPLE_PORTAL_RUN1) == failure_body_identities(SAMPLE_PORTAL_RUN2), (
            "两跑只差线程对象地址，身份却不等 —— 判据把『每跑不同的量』算进了身份，等于把 nodeid 漂移换成了线程地址漂移"
        )

    def test_normalisation_keeps_thread_class(self):
        """归一只抹地址，不抹类别：MainThread 与 portal 线程仍须可区分。"""
        assert failure_body_identities(SAMPLE_R4) != failure_body_identities(SAMPLE_PORTAL_RUN1)

    def test_both_indent_forms_are_collected(self):
        """三个产出点里 2 空格与 4 空格缩进各有，两种都要收。"""
        two = "  - ('::1', 7691, 0, 0) on thread MainThread (owner=x)\n"
        four = "    - ('::1', 7691, 0, 0) on thread MainThread (owner=y)\n"
        assert failure_body_identities(two) == failure_body_identities(four)
        assert len(failure_body_identities(two + four)) == 1, "同一身份印两次仍是一个身份"

    def test_ipv4_two_tuple_is_collected(self):
        """IPv4 是 2 元组；只认 4 元组会整条漏掉。"""
        text = "  - ('127.0.0.1', 7691) on thread MainThread (owner=z)\n"
        assert failure_body_identities(text) == {"('127.0.0.1', 7691) on thread MainThread"}

    def test_owner_containing_on_thread_does_not_leak_into_identity(self):
        """⛔ parametrize id 可含空格/括号/等号。贪婪从右切会把 owner 切进身份。"""
        text = (
            "  - ('::1', 7691, 0, 0) on thread MainThread "
            "(owner=tests/unit/test_p.py::test_q[a on thread b (owner=c)])\n"
        )
        assert failure_body_identities(text) == {"('::1', 7691, 0, 0) on thread MainThread"}


class TestNaiveNodeidsIsTheFalsificationAnchor:
    """验伪锚（卡文 (e)）：旧判据在同两份样本上**必须**不等，证明改绑的必要性。"""

    def test_old_criterion_drifts_on_the_same_samples(self):
        old_a, old_b = naive_failed_nodeids(SAMPLE_R4), naive_failed_nodeids(SAMPLE_R4B)
        assert old_a and old_b, "朴素提取器一条都没抓到 —— 锚哑火，证明不了任何事"
        assert old_a != old_b, "旧判据在两份样本上相等 ⇒ 本卡的改绑失去理由"

    def test_new_criterion_holds_where_old_one_drifts(self):
        """同一对样本：旧判据漂、新判据稳。这一条是本卡的全部主张。"""
        assert naive_failed_nodeids(SAMPLE_R4) != naive_failed_nodeids(SAMPLE_R4B)
        assert blocked_count(SAMPLE_R4) == blocked_count(SAMPLE_R4B)
        assert failure_body_identities(SAMPLE_R4) == failure_body_identities(SAMPLE_R4B)


class TestClassifyShaChange:
    """conftest 卫生快照的 sha 三态。"""

    def test_same_hash_is_unchanged(self):
        assert classify_sha_change("a" * 64, "a" * 64) == "unchanged"

    def test_different_hash_is_changed(self):
        assert classify_sha_change("a" * 64, "b" * 64) == "changed"

    def test_none_to_hash_is_unchecked(self):
        """⛔ 不是 changed：None 表示「这一次没读到」，不是「内容变了」。"""
        assert classify_sha_change(None, "a" * 64) == "unchecked"

    def test_hash_to_none_is_unchecked(self):
        assert classify_sha_change("a" * 64, None) == "unchecked"

    def test_none_to_none_is_unchecked_not_unchanged(self):
        """⛔ 本卡的要害：两次都没读到 ⇒ **没查完**，不是「没问题」。

        旧实现 ``after != before`` 在 None↔None 下为假 ⇒ 静默当「未变化」放过，
        那正是「把没检查当没问题」。
        """
        assert classify_sha_change(None, None) == "unchecked"

    def test_only_three_verdicts_exist(self):
        cases = [("a" * 64, "a" * 64), ("a" * 64, "b" * 64), (None, "a" * 64), ("a" * 64, None), (None, None)]
        assert {classify_sha_change(*c) for c in cases} <= {"unchanged", "changed", "unchecked"}


class TestToolTouchesNoNetwork:
    """卡文 (i)：工具不得连网。静态 grep 只是可观测性，这里让它**被强制**。"""

    def test_module_imports_nothing_from_app(self):
        import tests.support.w4_sentinel_identity as mod

        src = __import__("inspect").getsource(mod)
        for token in ("import app", "from app", "addaudithook", "urllib", "httpx", "requests"):
            assert token not in src, f"工具源码里出现了 {token!r}"

    def test_parsing_opens_no_socket(self):
        """在**门已装好的** pytest 进程里跑解析：真发起连接会被 guard 记账并打红本用例。

        这比 grep 强：grep 证明「源码里没写」，这条证明「跑起来没连」。
        未证明面：不覆盖子进程连网与 C 扩展绕过审计事件。
        """
        import socket as _socket

        seen: list[object] = []
        original = _socket.socket.connect

        def _spy(self, addr):  # pragma: no cover - 不该被调用
            seen.append(addr)
            return original(self, addr)

        _socket.socket.connect = _spy
        try:
            blocked_count(SAMPLE_R4)
            failure_body_identities(SAMPLE_R4)
            summary_quad(SAMPLE_R4)
            classify_sha_change(None, None)
        finally:
            _socket.socket.connect = original
        assert seen == [], f"解析过程发起了 socket 连接: {seen}"
