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

import inspect
import pathlib

import pytest

from tests.support.hygiene_snapshot_tristate import classify_sha_change
from tests.support import w4_sentinel_identity as w4id
from tests.support.w4_sentinel_identity import (
    W4LedgerConflict,
    blocked_count,
    failure_body_identities,
    main,
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
（连接处抛出的异常被 app/main.py 的 lifespan try/except 吞掉了，
  所以由本哨兵把它转成用例失败——否则这道门什么都证明不了。）
  - ('::1', 7691, 0, 0) on thread asyncio-portal-15f0ef460 (owner=tests/unit/test_startup_health_check.py::TestStartupCheck::test_endpoint_exists)
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)
"""

SAMPLE_PORTAL_RUN2 = """\
live Neo4j port connect attempted —— 本用例期间有 1 次到现网 Neo4j 的连接尝试被拦下。
（连接处抛出的异常被 app/main.py 的 lifespan try/except 吞掉了，
  所以由本哨兵把它转成用例失败——否则这道门什么都证明不了。）
  - ('::1', 7691, 0, 0) on thread asyncio-portal-14867cb40 (owner=tests/unit/test_startup_health_check.py::TestStartupCheck::test_endpoint_exists)
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)
"""


def sentinel_block(*records: str, declared: int | None = None) -> str:
    """按 ``format_sentinel`` 的真实形态包一个**自报条数的记录块**。

    ⛔ 判据（round-3 改写后）只读被抬头自报过条数的块 —— 裸记录行不再被扫描。
    所以测试也必须喂真实形态，否则测的是想象中的输入。
    ``declared`` 显式给值时可造出「自报数 ≠ 实有数」的负控。
    """
    n = len(records) if declared is None else declared
    return (
        f"live Neo4j port connect attempted —— 本用例期间有 {n} 次到现网 Neo4j 的连接尝试被拦下。\n"
        "（连接处抛出的异常被 app/main.py 的 lifespan try/except 吞掉了，\n"
        "  所以由本哨兵把它转成用例失败——否则这道门什么都证明不了。）\n" + "".join(records)
    )


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
        """两份 blocked 都是 0，但一份 advisory=12 —— 那 12 次连接尝试被**放行**了。

        ⛔ 措辞（Codex round-1 LOW-7 / round-3 LOW-6）：advisory = 「只记不拦」= 放行，
        **不等于连上了** —— 对端仍可能拒连。不得据 advisory 推断连接成功。
        """
        a = "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=12 (blocked=0, advisory=12, unaccounted=0)\n"
        b = "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)\n"
        assert blocked_count(a) == blocked_count(b) == 0, "单判 blocked 看不出差别"
        assert summary_quad(a) != summary_quad(b), "四元组必须看得出 advisory 的差别"


class TestCliActuallyUsesWhatItClaims:
    """⛔ Codex round-1 HIGH-1：能力存在 ≠ 能力接上了。

    初版**写了** :func:`summary_quad` 却从没把它接进 CLI —— `_describe()` 只返回
    ``blocked`` 与 bodies，于是 ``advisory=12``（12 次到现网的连接尝试**被放行**）
    与全零档被判成一致，而我在 docstring 与验收单里已经写了「CLI 比对整条四元组」。
    上一版的测试只证明 helper 能区分，**没有证明 CLI 会用它** —— 这一类就是缺口。
    """

    def test_cli_rejects_advisory_only_difference(self, tmp_path):
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)\n")
        b.write_text("NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=12 (blocked=0, advisory=12, unaccounted=0)\n")
        assert main([str(a), str(b)]) == 1, (
            "两份 blocked 都是 0 但一份 advisory=12（12 次连接尝试被放行），CLI 判成一致 = 假绿"
        )

    def test_cli_zero_case_is_labelled_not_overclaimed(self, tmp_path, capsys):
        """⛔ Codex round-1 HIGH-2：全零 ≠「门在位且查完了」。

        汇总行由 ``summary_line()`` 产而它**不含 ``installed``**（账本 dict 有、汇总行没有）；
        pytest-xdist 下每 worker 独立 STATE。纯文本无从区分「门在位、零连接」与「门缺席」。
        仍退 0（否则每次干净跑都红），但裁定词必须是 ``CONSISTENT-ZERO`` 并带明示，
        不得让 ``CONSISTENT`` 在全零档上冒充「门证明了什么」。
        """
        z = "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)\n"
        a, b = tmp_path / "a.txt", tmp_path / "b.txt"
        a.write_text(z)
        b.write_text(z)
        assert main([str(a), str(b)]) == 0
        out = capsys.readouterr().out
        assert "CONSISTENT-ZERO" in out
        assert "不能证明门当时在位" in out

    def test_cli_refuses_when_a_file_has_no_summary_line(self, tmp_path):
        """⛔ Codex round-2 HIGH-1 残留：缺四元组的档**不可比**。

        初版把 ``None`` 从 ``quad_vals`` 里滤掉，于是「A 只有总账行（advisory 未知）
        + B 有 advisory=12」被判一致。没有汇总行就不知道 advisory 是多少，说不清就非 0。
        """
        a, b = tmp_path / "a.txt", tmp_path / "b.txt"
        a.write_text(
            "  - ('::1', 7691, 0, 0) on thread MainThread (owner=x)\n"
            "*** live Neo4j port connect attempted —— 最终总账：blocked=1 "
            "unaccounted=0 reported_status=1；结束***\n"
        )
        b.write_text(
            "  - ('::1', 7691, 0, 0) on thread MainThread (owner=x)\n"
            "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=13 (blocked=1, advisory=12, unaccounted=0)\n"
        )
        assert main([str(a), str(b)]) == 2, "一份 advisory 未知却判一致 = 假绿"

    def test_zero_label_needs_the_whole_quad_to_be_zero(self, tmp_path, capsys):
        """⛔ Codex round-2 MEDIUM-4：``CONSISTENT-ZERO`` 不得只看 ``blocked``。

        ``(12, 0, 12, 0)`` —— 12 次 advisory 放行 —— 初版也被打上「全零」标签。
        """
        z = "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=12 (blocked=0, advisory=12, unaccounted=0)\n"
        a, b = tmp_path / "a.txt", tmp_path / "b.txt"
        a.write_text(z)
        b.write_text(z)
        assert main([str(a), str(b)]) == 0, "两份相同，一致性判定本身没问题"
        assert "CONSISTENT-ZERO" not in capsys.readouterr().out, "advisory=12 不是全零"

    def test_cli_still_consistent_on_the_r4_pair(self, tmp_path):
        """反向锚：真正该判一致的那一对仍然 rc=0，且不是 ZERO 那条路径。"""
        a, b = tmp_path / "r4.txt", tmp_path / "r4b.txt"
        a.write_text(SAMPLE_R4)
        b.write_text(SAMPLE_R4B)
        assert main([str(a), str(b)]) == 0


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
        two = sentinel_block("  - ('::1', 7691, 0, 0) on thread MainThread (owner=x)\n")
        four = sentinel_block("    - ('::1', 7691, 0, 0) on thread MainThread (owner=y)\n")
        assert failure_body_identities(two) == failure_body_identities(four)
        assert len(failure_body_identities(two + four)) == 1, "同一身份被两个产出点各印一次，仍是一个身份"

    def test_ipv4_two_tuple_is_collected(self):
        """IPv4 是 2 元组；只认 4 元组会整条漏掉。"""
        text = sentinel_block("  - ('127.0.0.1', 7691) on thread MainThread (owner=z)\n")
        assert failure_body_identities(text) == {"('127.0.0.1', 7691) on thread MainThread"}

    def test_thread_name_with_spaces_is_not_silently_dropped(self):
        """⛔ Codex round-1 HIGH-3：解析不了的记录行**不得静默丢弃**。

        ``threading.Thread(name=...)`` 允许含空格的线程名（实测 ``Thread-1 (worker)``）。
        初版用 ``\\S+`` 匹配线程名，匹配不上时 ``if m:`` 让整行**静默消失** ⇒ 身份集变空
        ⇒ 两份形态完全不同的存档被判一致。**每一个 `if 匹配成功:` 都藏着一个未写的
        else，而那个 else 通常就是假绿。**
        """
        text = sentinel_block("  - ('::1', 7691, 0, 0) on thread Thread-1 (worker) (owner=x)\n")
        assert failure_body_identities(text) == {"('::1', 7691, 0, 0) on thread Thread-1 (worker)"}

    def test_unparseable_body_line_raises_instead_of_vanishing(self):
        """看得出是记录行、却解析不出身份 ⇒ 必须抛，不得当成「没有这条记录」。"""
        with pytest.raises(W4LedgerConflict, match="解析不出身份"):
            failure_body_identities(sentinel_block("- 某个畸形地址 on thread\n"))

    def test_thread_name_with_embedded_newline_is_refused_not_dropped(self):
        """⛔ Codex round-2 HIGH-3 残留：线程名含 ``\\n`` 时整条被切成两半。

        首半段恰好止于 ``on thread``（截断痕迹），后半段含 ``(owner=`` 却不以 ``- `` 开头
        （孤儿痕迹）。初版的宽松候选规则两半都不认 ⇒ 记录静默消失 ⇒ 两份不同的档判一致。
        """
        text = sentinel_block("  - ('::1', 7691, 0, 0) on thread \nworker (owner=x)\n", declared=1)
        with pytest.raises(W4LedgerConflict, match="解析不出身份"):
            failure_body_identities(text)

    def test_ordinary_log_line_is_not_mistaken_for_a_malformed_record(self):
        """⛔ Codex round-2 MEDIUM-3：候选规则不得把普通日志当畸形记录（假红）。

        captured stdout 里 ``- waiting on thread worker`` 这种行随处可见；
        判定只认**截断痕迹**与**孤儿痕迹**，不去猜「这行像不像哨兵记录」。
        """
        text = (
            sentinel_block("  - ('::1', 7691, 0, 0) on thread MainThread (owner=x)\n")
            + "- waiting on thread worker\n"
            + "cache refreshed (owner=worker)\n"
            + "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)\n"
        )
        assert failure_body_identities(text) == {"('::1', 7691, 0, 0) on thread MainThread"}

    def test_cli_rejects_two_files_whose_bodies_differ_via_spaced_threads(self, tmp_path):
        """HIGH-3 的 CLI 面：两份含空格线程名、内容不同的存档必须判不一致。"""
        s1 = (
            sentinel_block("  - ('::1', 7691, 0, 0) on thread Thread-1 (worker) (owner=x)\n")
            + "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)\n"
        )
        s2 = (
            sentinel_block("  - ('127.0.0.1', 7687) on thread Thread-2 (worker) (owner=x)\n")
            + "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)\n"
        )
        a, b = tmp_path / "a.txt", tmp_path / "b.txt"
        a.write_text(s1)
        b.write_text(s2)
        assert main([str(a), str(b)]) == 1, "两份正文身份不同却判一致 = 假绿"

    def test_owner_containing_on_thread_does_not_leak_into_identity(self):
        """⛔ parametrize id 可含空格/括号/等号。贪婪从右切会把 owner 切进身份。"""
        text = sentinel_block(
            "  - ('::1', 7691, 0, 0) on thread MainThread "
            "(owner=tests/unit/test_p.py::test_q[a on thread b (owner=c)])\n"
        )
        assert failure_body_identities(text) == {"('::1', 7691, 0, 0) on thread MainThread"}


class TestDeclaredBlockContract:
    """⛔ Codex round-3 HIGH-1 后重写的判据：**只读被自报过条数的块，块内必须行行可解析**。

    前三版都是「扫全文猜这行坏没坏」，被连续三轮各证伪一次（``\\S+`` / 宽松候选 /
    截断+孤儿痕迹）。下面前五条就是 r3 举出的、两条痕迹**都不命中**的输入 ——
    在旧口径下它们全部静默变成空身份集、两份不同的存档判一致（假绿）。
    """

    # ── HIGH-1：四类「不留断口」的破坏形态 ──────────────────────────────
    def test_thread_newline_followed_by_dash_is_refused(self):
        """续段以 ``- `` 开头 ⇒ 逃过孤儿检查；首段不止于 ``on thread`` ⇒ 逃过截断检查。"""
        text = sentinel_block("  - ('::1', 7691, 0, 0) on thread worker\n- continued (owner=x)\n", declared=1)
        with pytest.raises(W4LedgerConflict, match="解析不出身份"):
            failure_body_identities(text)

    def test_carriage_return_variant_is_refused(self):
        """``\\r`` 与 ``\\n`` 在 :func:`_lines` 下同样切行，必须同样拒判。"""
        text = sentinel_block("  - ('::1', 7691, 0, 0) on thread worker\r- continued (owner=x)\n", declared=1)
        with pytest.raises(W4LedgerConflict, match="解析不出身份"):
            failure_body_identities(text)

    def test_empty_thread_name_is_refused(self):
        """``Thread(name="")`` 合法；空线程名两条痕迹都不命中，旧口径整条丢失。"""
        text = sentinel_block("  - ('::1', 7691, 0, 0) on thread  (owner=x)\n")
        with pytest.raises(W4LedgerConflict, match="解析不出身份"):
            failure_body_identities(text)

    def test_address_newline_leaving_a_valid_looking_tail_is_refused(self):
        """地址含换行 ⇒ 后半段**自成一条合法记录**，旧口径不但不报还给出错误身份。"""
        text = sentinel_block("  - ADDR-A\n- tail on thread worker (owner=x)\n", declared=1)
        with pytest.raises(W4LedgerConflict, match="解析不出身份"):
            failure_body_identities(text)

    def test_truncation_before_owner_is_refused(self):
        """owner 出现前就被截断 —— r2 曾有覆盖此类的测试，r3 指出它被换成了恰好止于
        ``on thread`` 的输入，原输入重新漏过。这条把它钉回去。"""
        text = sentinel_block("  - ('::1', 7691, 0, 0) on thread worker\n")
        with pytest.raises(W4LedgerConflict, match="解析不出身份"):
            failure_body_identities(text)

    # ── 块条数对账（闭合判据的核心）─────────────────────────────────────
    def test_block_with_more_records_than_declared_is_refused(self):
        text = sentinel_block(
            "  - ('::1', 7691, 0, 0) on thread MainThread (owner=x)\n",
            "  - ('::1', 7687, 0, 0) on thread MainThread (owner=y)\n",
            declared=1,
        )
        with pytest.raises(W4LedgerConflict, match="自报条数与实际不符"):
            failure_body_identities(text)

    def test_block_truncated_mid_way_is_refused(self):
        text = sentinel_block("  - ('::1', 7691, 0, 0) on thread MainThread (owner=x)\n", declared=3)
        with pytest.raises(W4LedgerConflict, match="存档被截断"):
            failure_body_identities(text)

    def test_ledger_says_blocked_but_no_block_at_all_is_refused(self):
        """身份集为空**不代表**没有记录 —— 也可能是块被截掉或抬头文案漂了。"""
        with pytest.raises(W4LedgerConflict, match="一个自报条数的记录块都没有"):
            failure_body_identities("NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)\n")

    def test_clean_run_with_zero_blocked_and_no_block_is_fine(self):
        """⛔ 反向锚：干净跑（本卡自己的目录级存档形态）必须照常退，不能自伤。"""
        assert (
            failure_body_identities("NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)\n")
            == set()
        )

    # ── MEDIUM-2：块外的行根本不看（假红一并消失）───────────────────────
    @pytest.mark.parametrize(
        "noise",
        [
            "cache refreshed (owner=worker)\n",
            '    print(f"    - {address} on thread {thread} (owner={owner})")\n',
            "- waiting on thread\n",
            "- waiting on thread worker\n",
        ],
    )
    def test_ordinary_output_outside_a_block_never_causes_a_verdict(self, noise):
        """⛔ 这四条在 r2/r3 口径下分别触发过假红（rc=2）。块外的行不参与判定。"""
        text = sentinel_block("  - ('::1', 7691, 0, 0) on thread MainThread (owner=x)\n") + noise
        assert failure_body_identities(text) == {"('::1', 7691, 0, 0) on thread MainThread"}

    # ── 反向锚：真实样本不得被新判据自伤 ────────────────────────────────
    def test_real_samples_still_parse_and_still_match(self):
        assert failure_body_identities(SAMPLE_R4) == failure_body_identities(SAMPLE_R4B)
        assert failure_body_identities(SAMPLE_R4) == {"('::1', 7691, 0, 0) on thread MainThread"}
        assert failure_body_identities(SAMPLE_PORTAL_RUN1) == failure_body_identities(SAMPLE_PORTAL_RUN2)


class TestRound4Closures:
    """⛔ Codex round-4 的四条发现 —— 「闭合」在入口和边界上仍有开放式的口子。"""

    def test_empty_first_segment_from_real_formatter_is_refused(self):
        """**HIGH-1**：`address="\\n- tail"` 让首条记录退化成只剩 ``- ``。

        上一版按「扫到第一条 ``- `` 行」定位记录起点，而 ``  - `` strip 后是 ``-``、
        不满足 ``startswith("- ")`` ⇒ 被当说明行**跳过**，扫描继续前进落到后半段
        ``- tail on thread worker (owner=x)`` 上并解析成功 ⇒ 两份不同的档判一致。
        ⛔ 根因：**只要还有任何一处是「向前找找看」，它就还是开放式规则。**
        现在记录起点是已知常量（A/B 抬头下一行、C 抬头后 2 行说明），不扫。
        """
        from tests.support import live_port_guard

        bad = live_port_guard.format_sentinel("x", [{"address": "\n- tail", "thread": "worker", "owner": "x"}])
        with pytest.raises(W4LedgerConflict, match="解析不出身份"):
            failure_body_identities(bad + "\n")

    def test_empty_first_segment_carriage_return_variant_is_refused(self):
        from tests.support import live_port_guard

        bad = live_port_guard.format_sentinel("x", [{"address": "\r- tail", "thread": "worker", "owner": "x"}])
        with pytest.raises(W4LedgerConflict, match="解析不出身份"):
            failure_body_identities(bad + "\n")

    def test_orphan_record_outside_any_block_is_refused(self):
        """**MEDIUM-2**：一个块正常、另一个块抬头漂了 ⇒ 漂掉那块的记录静默消失。

        旧兜底只管「一个块都没有」，所以「还识别到任何一个块（含零条块）」时就接不住。
        新规则：**每一行完整匹配 `_BODY_RE` 的记录行都必须被某个块认领**。
        """
        from tests.support import live_port_guard

        ok = live_port_guard.format_sentinel(
            "a", [{"address": "('::1', 7691, 0, 0)", "thread": "MainThread", "owner": "x"}]
        )
        drifted = ok.replace("本用例期间有", "本用例期间有大约")  # 抬头文案漂移
        with pytest.raises(W4LedgerConflict, match="不属于任何自报条数的记录块"):
            failure_body_identities(ok + "\n" + drifted + "\n")

    def test_orphan_check_does_not_fire_on_ordinary_output(self):
        """⛔ 反向锚：孤儿检查**只认完整记录行**，不得把普通输出当孤儿（否则假红回来）。"""
        from tests.support import live_port_guard

        ok = live_port_guard.format_sentinel(
            "a", [{"address": "('::1', 7691, 0, 0)", "thread": "MainThread", "owner": "x"}]
        )
        noise = (
            "cache refreshed (owner=worker)\n"
            '    print(f"    - {address} on thread {thread} (owner={owner})")\n'
            "- waiting on thread\n"
            "- waiting on thread worker\n"
        )
        assert failure_body_identities(ok + "\n" + noise) == {"('::1', 7691, 0, 0) on thread MainThread"}

    def test_header_b_does_not_match_arbitrary_prefix(self):
        """**MEDIUM-4**：``*** cache —— 1 次拦截无人结账`` 曾被当成缺正文的正式块 ⇒ 假红。"""
        text = (
            "*** cache —— 1 次拦截无人结账\nNEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)\n"
        )
        assert failure_body_identities(text) == set(), "B 抬头仍接受任意前缀 ⇒ 普通输出被当成块"

    def test_missing_quad_gate_is_actually_reached(self, tmp_path):
        """**MEDIUM-5**：上一版这条测试的 B 档是「裸记录 + blocked=1 汇总」，

        先被**缺块门**拦住，根本没走到缺四元组那条分支 —— 门是绿的，但覆盖是假的。
        现在两档都带**正常 C 块**，只有 A 缺汇总行，才真正打在缺四元组门上。
        """
        from tests.support import live_port_guard

        blk = live_port_guard.format_sentinel(
            "x", [{"address": "('::1', 7691, 0, 0)", "thread": "MainThread", "owner": "x"}]
        )
        a, b = tmp_path / "a.txt", tmp_path / "b.txt"
        a.write_text(
            blk + "\n*** live Neo4j port connect attempted —— 最终总账：blocked=1 "
            "unaccounted=0 reported_status=3；进程被强制以退出码 3 结束（迟到连接不得以 0 收场）***\n",
            encoding="utf-8",
        )
        b.write_text(
            blk + "\nNEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)\n",
            encoding="utf-8",
        )
        assert main([str(a), str(b)]) == 2, "A 缺汇总行（advisory 未知）却被判可比较"


class TestJudgeIsBoundToTheRealProducers:
    """⛔ 新判据只认**抬头**；抬头文案一漂，判据就对那个块**失明**（方向是记录消失）。

    所以必须有一条把判据钉在**真产出方**上的测试：直接调 ``live_port_guard.format_sentinel``
    造真输出，再让判据去解析。产出方改文案 ⇒ 这里真红，而不是判据静默看不见。
    这条是 r3 整改引入的那个代价的**唯一防线**。
    """

    def test_judge_parses_real_format_sentinel_output(self):
        from tests.support import live_port_guard

        records = [
            {"address": "('::1', 7691, 0, 0)", "thread": "MainThread", "owner": "ignored"},
            {"address": "('127.0.0.1', 7687)", "thread": "asyncio-portal-15f0ef460", "owner": "ignored"},
        ]
        real = live_port_guard.format_sentinel("tests/unit/test_x.py::test_y", records)
        assert failure_body_identities(real + "\n") == {
            "('::1', 7691, 0, 0) on thread MainThread",
            "('127.0.0.1', 7687) on thread asyncio-portal-<id>",
        }, "判据解析不了真产出方的输出 —— 抬头/记录文案已漂，判据对该块失明"

    def test_zero_record_sentinel_does_not_swallow_the_next_block(self):
        """``format_sentinel(owner, [])`` 自报 0 条：不得吞掉后一个块的记录。

        ⛔ 「别处的记录」必须放进**它自己的合法块**里 —— 一条不属于任何块的完整记录行
        本身就该被拒判（见 ``test_orphan_record_outside_any_block_is_refused``），
        拿它当噪声等于把两件事混在一条测试里。
        """
        from tests.support import live_port_guard

        empty = live_port_guard.format_sentinel("owner", [])
        elsewhere = live_port_guard.format_sentinel(
            "other", [{"address": "('::1', 7691, 0, 0)", "thread": "MainThread", "owner": "x"}]
        )
        assert failure_body_identities(empty + "\n" + elsewhere + "\n") == {
            "('::1', 7691, 0, 0) on thread MainThread"
        }, "自报 0 条的块吞掉了后一个块的记录"

    def test_block_reason_literal_still_matches_the_guard(self):
        """三条抬头正则都把 ``BLOCK_REASON`` 写死了 —— 它必须仍等于守卫本体的值。"""
        from tests.support import live_port_guard

        src = inspect.getsource(w4id)
        assert live_port_guard.BLOCK_REASON in src, (
            f"守卫的 BLOCK_REASON={live_port_guard.BLOCK_REASON!r} 已不在判据源码里，抬头正则锚已漂，判据会对整个块失明"
        )

    def test_final_ledger_header_literal_still_matches_the_guard(self):
        """抬头 A 与 B 的源码锚：**锚住判据实际依赖的那一段，不多不少**。

        ⛔ Codex round-4 MEDIUM-3：上一版锚得太松 —— A 把 ``unaccounted=`` 改成
        ``unaccounted_count=``、B 在第一段字面量末尾加个空格，源码锚都**照样为真**，
        而抬头正则已经不匹配了（块静默失明）。现在两条锚各自覆盖到正则依赖的末端为止。
        """
        guard_src = inspect.getsource(__import__("tests.support.live_port_guard", fromlist=["x"]))
        conftest_src = pathlib.Path(__file__).resolve().parents[1].joinpath("conftest.py").read_text(encoding="utf-8")
        # A：_FINAL_RE 一路依赖到 reported_status=
        assert "—— 最终总账：blocked={blocked} " in guard_src, "抬头 A 的 blocked 段文案已漂"
        assert "unaccounted={unaccounted} reported_status={status}；" in guard_src, (
            "抬头 A 的 unaccounted/reported_status 段文案已漂，_FINAL_RE 将不匹配"
        )
        # B：_BLOCK_HEAD_B_RE 只依赖到「N 次拦截」为止 —— 锚也只锚到这里。
        #    ⛔ 抬头 B 在源码里是**跨两个相邻字面量**拼的，「次拦截无人结账」在源码里不连续；
        #    正好判据也不依赖后半段，所以锚到 ``次拦截`` 收尾既够用又不过度。
        assert "—— {len(unaccounted)} 次拦截" in conftest_src, "抬头 B 判据依赖的那一段文案已漂"

    def test_header_b_regex_matches_the_runtime_string(self):
        """抬头 B 的源码锚只能分段核 ⇒ 这条按产出方的**运行期**拼法复原整行再喂正则。"""
        from tests.support import live_port_guard

        runtime = (
            f"*** {live_port_guard.BLOCK_REASON} —— 2 次拦截"
            "无人结账（迟到线程 / collection 期 / 未知线程），进程将以退出码 3 失败 ***"
        )
        block = (
            runtime
            + "\n"
            + (
                "    - ('::1', 7691, 0, 0) on thread MainThread (owner=a)\n"
                "    - ('127.0.0.1', 7687) on thread MainThread (owner=b)\n"
            )
        )
        assert failure_body_identities(block) == {
            "('::1', 7691, 0, 0) on thread MainThread",
            "('127.0.0.1', 7687) on thread MainThread",
        }, "判据认不出抬头 B 的运行期形态"

    def test_header_a_regex_matches_the_runtime_string(self):
        """抬头 A：自报的 ``unaccounted=M`` 按 ``live_port_guard.py:443-444`` 的构造
        恒等于随后遍历的 ``ledger["unaccounted_records"]`` 长度
        （``"unaccounted": len(unaccounted)`` 与 ``"unaccounted_records": unaccounted``
        是同一个 list）。这条按产出方写法复原整块再喂判据。

        ⛔ 未证明面：本卡四份真实样本**全是 C 型**，A 型块只在此处按源码复原，
        没在真实存档里见过。
        """
        from tests.support import live_port_guard

        head = (
            f"*** {live_port_guard.BLOCK_REASON} —— 最终总账：blocked=3 "
            f"unaccounted=2 reported_status=3；"
            f"进程被强制以退出码 {live_port_guard.FINAL_EXIT_CODE} 结束（迟到连接不得以 0 收场）***"
        )
        block = (
            head
            + "\n"
            + (
                "    - ('::1', 7691, 0, 0) on thread MainThread (owner=a)\n"
                "    - ('127.0.0.1', 7687) on thread Thread-9 (late) (owner=b)\n"
            )
        )
        assert failure_body_identities(block) == {
            "('::1', 7691, 0, 0) on thread MainThread",
            "('127.0.0.1', 7687) on thread Thread-9 (late)",
        }, "判据认不出抬头 A 的运行期形态"

    def test_header_a_with_zero_unaccounted_reads_no_records(self):
        """A 的第二个触发分支：``blocked>0 且 status==0`` 时抬头写 ``unaccounted=0``、
        后面零条记录。该块必须读 0 条，且**不得吞掉**后一个块的记录。"""
        from tests.support import live_port_guard

        head = (
            f"*** {live_port_guard.BLOCK_REASON} —— 最终总账：blocked=1 "
            f"unaccounted=0 reported_status=0；"
            f"进程被强制以退出码 {live_port_guard.FINAL_EXIT_CODE} 结束（迟到连接不得以 0 收场）***"
        )
        elsewhere = live_port_guard.format_sentinel(
            "other", [{"address": "('::1', 7691, 0, 0)", "thread": "MainThread", "owner": "x"}]
        )
        assert failure_body_identities(head + "\n" + elsewhere + "\n") == {
            "('::1', 7691, 0, 0) on thread MainThread"
        }, "A 型自报 0 条的块吞掉了后一个块的记录"


class TestArchiveDecoding:
    """⛔ Codex round-3 MEDIUM-3：读不清的存档不得靠替换字符凑出「相等」。"""

    def test_undecodable_archive_is_refused_not_replaced(self, tmp_path):
        good = (
            sentinel_block("  - ('::1', 7691, 0, 0) on thread MainThread (owner=x)\n")
            + "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)\n"
        )
        a, b = tmp_path / "a.txt", tmp_path / "b.txt"
        a.write_text(good, encoding="utf-8")
        # 线程名的原始字节含**非法 UTF-8**：errors="replace" 会把它变成 U+FFFD。
        # ⛔ 不能直接写 "\\x80" —— 那是 U+0080，编码后是合法的 b"\\xc2\\x80"。
        #    必须先放一个哨兵字符、编码后再换成裸字节。
        marker = "\ufffe"
        b.write_bytes(
            good.replace("MainThread", f"Main{marker}Thread").encode("utf-8").replace(marker.encode("utf-8"), b"\x80")
        )
        assert main([str(a), str(b)]) == 2, "读不出原文却参与比较 = 拿替换字符凑相等"

    def test_two_differently_corrupted_archives_are_not_called_consistent(self, tmp_path):
        """两份**不同**的损坏字节在 errors='replace' 下会变成同一个 U+FFFD ⇒ 假绿。"""
        body = "  - ('::1', 7691, 0, 0) on thread work{}er (owner=x)\n"
        tail = "NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)\n"
        paths = []
        for name, bad in (("a.txt", b"\x80"), ("b.txt", b"\x81")):
            f = tmp_path / name
            head = sentinel_block(body.format("\ufffe")).encode("utf-8")
            f.write_bytes(head.replace("\ufffe".encode("utf-8"), bad) + tail.encode("utf-8"))
            paths.append(str(f))
        assert main(paths) == 2, "两份不同的损坏被判一致 = 解码失败被压成了『内容相同』"


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
