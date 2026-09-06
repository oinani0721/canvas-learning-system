#!/usr/bin/env python3
"""CARD-G3-3 负控: 逐条拆掉并发防线, 断言**指定的那道门**变红。

为什么需要它: `test_g3_3_cas.py` 首跑即全绿 —— 而「一次就绿」既可能是实现对,
也可能是门根本不承重 (死门)。只有把防线拆掉后**那一道**门真的变红, 才证明
它测的是这条防线。

⛔ 三条硬约束 (都是本仓踩过的坑, 见 `.claude/rules` 与记忆):
  1. **串行**: 原地变异并发跑会互踩, 「还原后逐字节相同」这道自检会自证;
  2. **无条件还原**: try/finally **加** SIGTERM/SIGINT 处置 —— 默认 SIGTERM
     不做栈展开, finally 不执行, 变异体会留在生产文件里;
  3. **判据绑失败身份**: 只看 `rc != 0` 会被「别的门红了」喂饱。每条变异声明
     它**必须**打红的 nodeid, 该 nodeid 不在失败集里就算 SURVIVED。

⛔ 第四条 (CARD-G3-3-R1 新增, 由第十一批复核裁定 §三 抓出的**假杀**推出):
  4. **变异体必须语法合法, 且判据必须绑到那一条断言**。旧 M15 的替换串是两行
     且缩进错位, 施加后写点子进程**编译期**就死 —— 于是账本 0 行、`ids.count(...)
     == 1` 反而通过, 真正红的是「拒因不对」那条, 而卡文声称的「同 event_id 被写了
     两遍」**从未被打红过**。两道封堵: ① 施加后先做编译自检, 不通过判第三种裁决
     `SYNTAX-INVALID` (既不算 KILLED 也不算 SURVIVED); ② 每条变异声明 `expect_msg`
     —— 预期打红的**那一条断言**的消息片段, 不在输出里就不算 KILLED。

用法: `backend/.venv/bin/python backend/scripts/g33_mutation_gates.py [--json <out>]`
      `... --selfcheck-syntax`  (负控之负控: 旧 M15 串必判 SYNTAX-INVALID, 新串必通过)
      (从仓库根或 backend/ 跑均可; 只读 live vault 与 7691, 不碰它们)
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import signal
import stat
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
SKILL = REPO / "canvas-vault" / ".claude" / "skills" / "quiz-answer" / "SKILL.md"
BRIDGE = REPO / "canvas-vault" / ".claude" / "scripts" / "fsrs_bridge.py"
EVLOG = BACKEND / "app" / "services" / "learning_event_log.py"
TESTS = "tests/regression/test_g3_3_cas.py"

#: 变异体标记。⛔ 本文件里**不写它的字面量**(拼接构造): 写了的话本脚本自己就会
#: 被卡文的 `grep -rn <标记> canvas-vault/ backend/` 判据数进去 —— 判据自指。
MARK = "MUT" + "ANT"

#: (id, 文件, 原文片段, 变异后片段, 必须变红的 nodeid, 一句话说明, expect_msg)
#:
#: `expect_msg` = **预期打红的那一条断言**的消息片段。判据只取 pytest 回溯里
#: 以 `E ` 开头的行 (即真正抛出来的异常文本), **不是**整份 stdout ——
#: ⛔ pytest 的 long traceback 会把**整个测试函数的源码**打出来, 于是该函数里
#: 每一条断言的消息串都出现在 stdout 里; 拿 `msg in stdout` 当判据等于恒真,
#: 那是「判据被自己要找的东西喂饱」的又一种形态。
MUTATIONS = [
    (
        "M1-per-node-lock",
        SKILL,
        '_lock_exclusive(_lk_fd, _LOCK_TIMEOUT_S, "per-node 写锁", _lk_path)',
        f"pass  # {MARK}: 去掉 per-node 写锁",
        "tests/regression/test_g3_3_cas.py::test_concurrent_same_node_no_lost_update",
        "两进程同节点评分不再互斥 ⇒ 各按旧基线算 ⇒ attempt 双双写 1 (lost update)",
        "有评分被另一次覆盖掉了",
    ),
    (
        "M2-cas-guard",
        SKILL,
        '_cas_guard("正常路径发布")',
        f"pass  # {MARK}: 去掉发布前 CAS 门",
        "tests/regression/test_g3_3_cas.py::test_cas_conflict_refuses_and_rerun_converges",
        "外部写者插队后照常整份覆盖 ⇒ 用户刚写的正文被静默吃掉",
        "外部写者插队后仍照常发布",
    ),
    (
        "M3-ledger-lock-backend",
        EVLOG,
        "            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\n            return True",
        f"            return True  # {MARK}: 不真的加锁, 直接报成功",
        "tests/regression/test_g3_3_cas.py::test_append_event_refuses_when_ledger_locked",
        "查重与追加不再互斥 ⇒ 同一个 event_id 被并发写多行 ⇒ 幂等键唯一性破裂",
        "别人持着账本锁时 append_event 却报了写入成功",
    ),
    (
        "M5-cas-revision-only",
        BRIDGE,
        '    if cur.get("sha256") == token.get("sha256"):\n        return None',
        f'    if all(cur.get(k) == token.get(k) for k in ("fsrs_last_review", "attempt_count")):'
        f"  # {MARK}: 只比 revision 不比正文\n        return None",
        "tests/regression/test_g3_3_cas.py::test_cas_body_only_change_is_a_conflict",
        "CAS 只比 revision 两字段 ⇒ 正文改动被判「无冲突」⇒ 覆盖照做",
        "正文改动未判冲突",
    ),
    (
        "M6-ledger-lock-skill",
        SKILL,
        '_lock_exclusive(_fd, _LEDGER_LOCK_TIMEOUT_S, "账本追加锁", EV)',
        f"pass  # {MARK}: 去掉写点侧账本追加锁",
        "tests/regression/test_g3_3_cas.py::test_writer_waits_for_held_ledger_lock",
        "写点侧账本追加不再互斥 (LF 守卫 + 追加的窗口暴露)",
        "持锁方释放前账本已经变大",
    ),
    (
        "M8-thread-lock-lifetime",
        EVLOG,
        "        with _write_lock:\n            fd = os.open(path",
        f"        with _write_lock:  # {MARK}: 线程锁不再罩住 close\n            pass\n        if True:\n            fd = os.open(path",
        "tests/regression/test_g3_3_cas.py::test_thread_critical_sections_do_not_overlap",
        "线程锁不再覆盖 open→close 全生命周期 ⇒ 两线程临界区重叠 ⇒ 后者的锁被前者 close 撤销",
        "两个线程的临界区重叠了",
    ),
    (
        "M9-splitlines-instead-of-lf",
        EVLOG,
        '    parts = text.split("\\n")',
        f'    parts = text.splitlines()  # {MARK}: 改回 splitlines\n    _unused = text.split("\\n")',
        "tests/regression/test_g3_3_cas.py::test_dedup_scan_splits_only_on_physical_lf",
        "查重按 splitlines 切行 ⇒ 含裸 U+2028/NEL 的合法记录被切碎 ⇒ 查重漏命中 ⇒ 双写",
        "第二次写入没有被幂等挡住",
    ),
    (
        "M10-short-write-unchecked",
        EVLOG,
        "                if written != len(line_bytes):",
        f"                if False:  # {MARK}: 不检查短写",
        "tests/regression/test_g3_3_cas.py::test_short_write_is_not_reported_as_success",
        "短写不检查 ⇒ 残行被报告成写入成功",
        "短写被报告成成功",
    ),
    (
        "M11-out-of-order-auto-guess",
        EVLOG,
        "                if is_review and not out_of_order:",
        f"                if is_review and not out_of_order and payload_out.setdefault('out_of_order', True):  # {MARK}: 自动猜",
        "tests/regression/test_g3_3_cas.py::test_out_of_order_is_caller_declared_not_auto_guessed",
        "账本侧自动猜乱序 ⇒ 误标会让写点对该节点永久 fail-closed",
        "账本侧自动猜了乱序",
    ),
    (
        "M12-a3-node-lock",
        SKILL,
        "        fcntl.lockf(_lk_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\n        break",
        f"        break  # {MARK}: A3 增量块根本不取 per-node 锁",
        "tests/regression/test_g3_3_cas.py::test_incremental_block_waits_for_node_lock",
        "A3 增量归纳块不再等 per-node 锁 ⇒ 与写分块并发时互相覆盖",
        "归纳出现在持锁方那段之前",
    ),
    (
        "M13-a3-cas",
        SKILL,
        "    _c = cas_conflict(NODE, _tok)\n    if _c is not None:",
        f"    _c = None  # {MARK}: A3 去掉 CAS\n    if _c is not None:",
        "tests/regression/test_g3_3_cas.py::test_incremental_block_cas_preserves_racing_edit",
        "A3 增量块去掉 CAS ⇒ 冲突时拿旧 body 覆盖",
        "CAS 没挡住: 增量块拿读盘时的旧 body",
    ),
    (
        "M14-exam-board-ledger-lock",
        REPO / "canvas-vault" / ".claude" / "skills" / "start-exam-board" / "SKILL.md",
        "                fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\n                break",
        f"                break  # {MARK}: 建板不再取账本锁",
        "tests/regression/test_g3_3_cas.py::test_exam_board_waits_for_held_ledger_lock",
        "建板写点不再取账本锁 ⇒ 与别的写者并发时查重/追加不互斥",
        "建板在别人持锁时抢写了账本",
    ),
    (
        "M15-post-lock-redup",
        SKILL,
        '                if isinstance(_o_lock, dict) and _o_lock.get("event_id") == evid:',
        # ⛔ **单行短路**, 不新增行、缩进保持 16 —— 下一行 `raise SystemExit(...)`
        # 缩进 20, 仍旧挂在这个 if 底下, 语法合法。上一版换成两行 (`if False:` 无
        # 块体) 让整个 PYEOF 块 IndentationError, 写点子进程编译期就死 ⇒ 账本 0 行
        # ⇒「同 event_id 被写了两遍」那条断言反而通过, 红落在「拒因不对」上 —— 那是
        # 假杀 (第十一批复核裁定 §三)。
        f'                if False and isinstance(_o_lock, dict) and _o_lock.get("event_id") == evid:  # {MARK}: 取锁后不再重查',
        "tests/regression/test_g3_3_cas.py::test_writer_refuses_when_other_writer_took_the_event_id",
        "取锁后不重查 ⇒ 别的写者抢先写了同 event_id 时本块照常追加 ⇒ 同 ID 两行",
        "同 event_id 被写了两遍",
    ),
    (
        "M16-a2-foreign-cas",
        SKILL,
        '    _cas_guard("A2 foreign 重放后的恢复发布")',
        f"    pass  # {MARK}: 去掉 foreign 恢复发布前 CAS 门",
        "tests/regression/test_g3_3_cas.py::test_a2_foreign_recovery_publish_respects_cas",
        "foreign 恢复发布不再做 CAS ⇒ 拿内存里的旧 body 整份覆盖 ⇒ 外部写者的正文被吃掉",
        "CAS 门没挡住 A2 foreign 恢复发布",
    ),
    (
        "M17-dup-recovery-cas",
        SKILL,
        '    _cas_guard("dup 恢复路径发布")',
        f"    pass  # {MARK}: 去掉 dup 恢复发布前 CAS 门",
        "tests/regression/test_g3_3_cas.py::test_dup_recovery_publish_respects_cas",
        "dup 恢复路径发布不再做 CAS ⇒ 同上, 恢复动作自己把并发正文编辑吃掉",
        "CAS 门没挡住 dup 恢复路径发布",
    ),
    (
        "M4a-payload-in-place",
        EVLOG,
        "                payload_out = dict(payload or {})",
        f"                payload_out = payload if payload is not None else {{}}  # {MARK}: 不复制, 就地改调用方的 dict",
        "tests/regression/test_g3_3_cas.py::test_out_of_order_marker_is_additive",
        "不复制调用方 payload ⇒ 打标记就是就地污染 ⇒ 同一个 dict 被复用时把标记带到下一条事件",
        "append_event 就地污染了调用方的 payload",
    ),
    (
        "M4b-marker-not-additive",
        EVLOG,
        '                    payload_out["out_of_order"] = True',
        f'                    payload_out = {{"out_of_order": True}}  # {MARK}: 标记不再加性, 其余键全丢',
        "tests/regression/test_g3_3_cas.py::test_out_of_order_marker_is_additive",
        "补录标记不再是加性的 ⇒ 除标记外的 payload 键全被丢掉 ⇒ 那次复习的载荷永久消失",
        "out_of_order 标记不是加性的",
    ),
    (
        "M7-lock-dropped-by-second-fd",
        EVLOG,
        "                raw = _read_all(fd)",
        f"                raw = path.read_bytes()  # {MARK}: 持锁期间另开 fd ⇒ POSIX 锁整体释放",
        "tests/regression/test_g3_3_cas.py::test_append_event_still_holds_lock_at_the_moment_of_write",
        "持锁期间 open 第二个 fd ⇒ 本进程在该文件上的记录锁整体释放, 后半段临界区裸奔",
        "落盘那一刻账本锁已经不在手上",
    ),
]

_TARGET_FILES = sorted({m[1] for m in MUTATIONS}, key=str)

#: 基线 `03ac8bf8` 上**本来就**含 MARK 字面量的文件 (既有卡的负控脚本)。
#: 复核判据 = 跑完后的集合与它相同; 多出来的才是本脚本的残留。
#: ⛔ 基线口径随主干前进 (CARD-G3-3-R1): 原先写的 `304f03ca` 上是 4 项, 而本车道
#: HEAD 已预合主干 `03ac8bf8` —— 第十一批 Z6-A (`d0fc7d7f`) 新增的
#: `g32ccr1_negative_controls.py` 是第 5 项。少列它 ⇒ 它被算成「本脚本的残留」
#: ⇒ 什么都没错也返 1。判据仍是**与基线集合相同**, 不改成 `= 0` 或恒真: 拿「= 0」
#: 当判据在本仓恒不可达, 那是期望值没有独立来源的典型形态。
BASELINE_MARK_FILES = {
    str(BACKEND / "scripts" / "g32b_mutation_gates.py"),
    str(BACKEND / "scripts" / "g32cb_mutation_gates.py"),
    str(BACKEND / "scripts" / "g32ccr1_negative_controls.py"),
    str(BACKEND / "scripts" / "openapi_drift_negative_control.py"),
    str(BACKEND / "tests" / "regression" / "recap_domain_negverify.py"),
}

#: 与 `test_g3_3_cas.py:36` **同一条**正则 —— SKILL.md 的写点是逐字提取 PYEOF 块
#: 后以 `python -c` 跑的, 所以「变异体语法合法吗」这个问题必须问在同一批块上。
_PYEOF_RE = re.compile(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", re.DOTALL)


def _syntax_error(path: Path, text: str) -> str | None:
    """变异后的文本能不能编译? 返回错误串; None = 通过。

    ⛔ 这道自检是**假杀的结构性封堵**: 语法不合法的变异体会让写点子进程在编译期
    就死, 于是「防线被拆掉之后本该发生的坏事」根本没机会发生, 而门却因为别的
    断言红了被记成 KILLED。它照出的是**负控自己坏了**, 不是被测物坏了 —— 所以
    单列第三种裁决, 不并进 KILLED / SURVIVED 任何一边。
    """
    try:
        if path.suffix == ".md":
            for i, blk in enumerate(_PYEOF_RE.findall(text)):
                compile(blk, f"<{path.name}#PYEOF{i}>", "exec")
        else:
            compile(text, str(path), "exec")
    except SyntaxError as e:  # IndentationError/TabError 都是它的子类
        return f"{type(e).__name__}: {e}"
    return None


def _error_lines(out: str) -> str:
    """只取 pytest 回溯里真正抛出来的异常文本 (以 `E ` 开头的行)。

    ⛔ 不能拿整份 stdout 做 `expect_msg in out`: long traceback 会把**整个测试
    函数的源码**打出来, 该函数里每一条断言的消息串都在里面 —— 判据会被自己要找
    的东西喂饱, 等于恒真。
    """
    return "\n".join(re.findall(r"^E\s+(.*)$", out, re.M))


#: 旧的 (坏的) M15 替换串 —— **只**作为负控之负控的输入保留, 不在 MUTATIONS 表里。
#: 施加后 `if False:` 没有块体, 而原来挂在它下面的 `raise SystemExit(...)` 缩进 20,
#: 整个 PYEOF 块 IndentationError ⇒ 写点子进程编译期就死。
_M15_OLD_ANCHOR = '                if isinstance(_o_lock, dict) and _o_lock.get("event_id") == evid:'
_M15_OLD_REPL = (
    f"                if False:  # {MARK}: 取锁后不再重查\n                if isinstance(_o_lock, dict) and False:"
)


def _selfcheck_syntax() -> int:
    """负控之负控: 旧 M15 串必须被判 SYNTAX-INVALID, 新串与原文必须通过。

    ⛔ 只在**内存里**施加, 不落盘 —— 跑前跑后各打一次 SKILL.md 的 sha 自证。
    ⚠️ 两个验伪锚 (②③) 不可省: 只测「坏的被判坏」的话, 一个**恒判 SYNTAX-INVALID**
    的自检也能过那一半 —— 而它会把整份负控全判成坏的, 比没有自检更糟。
    """
    sha_before = _sha(SKILL)
    src = SKILL.read_text(encoding="utf-8")
    print(f"SKILL.md sha (跑前): {sha_before}")
    ok = True

    if src.count(_M15_OLD_ANCHOR) != 1:
        print(f"⛔ 旧 M15 锚点命中 {src.count(_M15_OLD_ANCHOR)} 次 (应为 1) — 自检输入不可信")
        return 2
    err_bad = _syntax_error(SKILL, src.replace(_M15_OLD_ANCHOR, _M15_OLD_REPL, 1))
    print(f"① 旧 M15 (两行/缩进错位): {'SYNTAX-INVALID — ' + err_bad if err_bad else '⛔ 竟然通过 —— 自检不承重'}")
    ok = ok and err_bad is not None

    m15 = next(m for m in MUTATIONS if m[0].startswith("M15"))
    if src.count(m15[2]) != 1:
        print(f"⛔ 新 M15 锚点命中 {src.count(m15[2])} 次 (应为 1)")
        return 2
    err_good = _syntax_error(SKILL, src.replace(m15[2], m15[3], 1))
    print(f"② 新 M15 (单行短路): {'⛔ 被判 SYNTAX-INVALID — ' + err_good if err_good else '通过 (验伪锚一成立)'}")
    ok = ok and err_good is None

    err_base = _syntax_error(SKILL, src)
    print(f"③ 未变异原文: {'⛔ ' + err_base if err_base else '通过 (验伪锚二成立)'}")
    ok = ok and err_base is None

    sha_after = _sha(SKILL)
    print(f"SKILL.md sha (跑后): {sha_after}")
    same = sha_before == sha_after
    print(f"未落盘 (跑前跑后 sha 逐字节相同): {'是' if same else '否'}")
    return 0 if (ok and same) else 1


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _source_of(p: Path) -> str:
    """把 `X/__pycache__/name.cpython-314.pyc` 归到它的源文件 `X/name.py`。

    ⛔ 这不是放宽判据: 归属判的仍然是「这个 MARK 属于**哪个源文件**」。本脚本自身
    与基线负控脚本的字节码是它们自己的派生物, 不算残留; 而**生产文件**的 `.pyc`
    若含 MARK, 归到那个生产文件后照样落进 leftovers。

    ⛔ 用 stdlib 的 `source_from_cache` 而不是自己 `split('.')`: 后者对**带点号的
    模块名**会算错 —— `foo.bar.cpython-314.pyc` 被算成 `foo.py`(实测), 于是一个
    与它无关的源文件替它顶了包。stdlib 对这种形态直接抛 ValueError, 落到 fallback
    后该文件保持自身路径 ⇒ 进 leftovers **报出来**, 而不是被静默归错。
    形态不认识时宁可多报, 不可少报。
    """
    if p.suffix == ".pyc" and p.parent.name == "__pycache__":
        try:
            return str(Path(importlib.util.source_from_cache(str(p))).resolve())
        except (ValueError, NotImplementedError):
            return str(p.resolve())
    return str(p.resolve())


def _failed_nodeids(stdout: str) -> set[str]:
    """从 pytest 输出抽失败的 nodeid。

    ⛔ 用 `-rf` 的 short summary 而不是猜: 「某处有 FAILED」不能证明**指定的那道
    门**红了 —— 拿粗判据判 KILLED 是假杀的经典形态。
    """
    return set(re.findall(r"^FAILED (\S+?)(?: - .*)?$", stdout, re.M))


def _failed_reasons(stdout: str) -> list[tuple[str, str]]:
    """`-rf` 短摘要行 `FAILED <nodeid> - <reason>` 的 (nodeid, reason) 列表。

    ⛔ 判据要用**这一行**而不是回溯里的 `E ` 行 (独立复核 round-2 R2-01)。
    实测: 短摘要的 reason 只取失败断言消息的**第一行** —— 断言消息里内嵌的
    `{out}` / `{err}` / `{ctx}` (都在换行之后) 进不来。而 `E ` 行会把多行消息
    逐行加前缀, 于是**前提断言**失败时子进程的整份输出都灌进判据面; 被测进程只要
    在运行期把期望片段拼出来打到 stderr, 就能让「目标断言其实没红」照样判 KILLED。
    ⚠️ 配套: `_run_gate` 必须设 `COLUMNS`, 否则 80 列下 reason 会被截成空串。
    """
    return [(m[0], m[1]) for m in re.findall(r"^FAILED (\S+?)(?: - (.*))?$", stdout, re.M)]


def _hit(nodeid: str, failed: set[str]) -> bool:
    """声明的 nodeid 是否命中失败集 —— **含参数化用例**。

    ⛔ 实测教训: 声明 `...::test_x` 而 pytest 报的是 `...::test_x[1]`,
    直接用 `nodeid in failed` 会把真 KILLED 误报成 SURVIVED —— 判据自己坏了,
    却长得跟「门不承重」一模一样。
    """
    return any(f == nodeid or f.startswith(nodeid + "[") for f in failed)


def _check_expect_msg_unique() -> list[str]:
    """每条 `expect_msg` 必须在它绑定的门文件里**恰好出现一次**。返回违规说明列表。

    ⛔ 为什么要把它写成门, 而不是「作者跑一次 grep 确认过」: 手工查出来的不变量不写成
    判据 = 没查 —— 本卡自己就当场破过一次 (给前提断言加注释时把 `expect_msg` 的原文
    复述进了注释, 那条片段在门文件里变成 2 次)。注释里的复述不进 pytest 的 `E ` 行,
    功能上无害, 但「唯一」这个前提一旦不成立, 判据就不再能证明红在**哪一条**断言上,
    而且下一次的复述可能就落在另一条断言的消息里。宁可严到连注释也不许复述。
    """
    problems: list[str] = []
    cache: dict[str, str] = {}
    for mid, _path, _old, _new, nodeid, _why, expect_msg in MUTATIONS:
        if not expect_msg:
            problems.append(f"{mid}: expect_msg 为空 (每条必须填实值或显式声明理由)")
            continue
        gate_file = nodeid.split("::", 1)[0]
        if gate_file not in cache:
            p = BACKEND / gate_file
            if not p.exists():
                problems.append(f"{mid}: 门文件不存在 {p}")
                continue
            cache[gate_file] = p.read_text(encoding="utf-8")
        n = cache[gate_file].count(expect_msg)
        if n != 1:
            problems.append(f"{mid}: expect_msg {expect_msg!r} 在 {gate_file} 里出现 {n} 次 (应为 1)")
        # ⛔ 还要求它**不在被测的生产代码里出现** (内部对抗审查): pytest 会给多行断言消息的
        # **每一行**都加 `E ` 前缀, 于是一条内嵌 `{out}/{err}/{ctx}` 的断言一旦红, 子进程的
        # 全部输出都进了判据面。只要 expect_msg 在生产侧命中 0 次, 生产输出就喂不饱它。
        for prod in (REPO / "canvas-vault", BACKEND / "app"):
            for f in prod.rglob("*"):
                if f.is_symlink() or not f.is_file():
                    continue
                try:
                    if expect_msg.encode() in f.read_bytes():
                        problems.append(f"{mid}: expect_msg {expect_msg!r} 也出现在生产文件 {f} 里 (须 0 次)")
                except OSError:
                    continue
    return problems


def _run_gate(nodeid: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rf", "--no-header", nodeid],
        cwd=str(BACKEND),
        capture_output=True,
        text=True,
        timeout=1800,
        # ⛔ COLUMNS 必须给足: pytest 的 `-rf` 短摘要按终端宽度截断, 80 列下
        # `FAILED … - <reason>` 的 reason 会被截成空串 ⇒ 判据恒不命中 (假 SURVIVED)。
        env={"PYTHONDONTWRITEBYTECODE": "1", "COLUMNS": "1000", **_env()},
    )
    return proc.returncode, proc.stdout + proc.stderr


def _env() -> dict:
    import os

    return dict(os.environ)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=None, help="把结果写成 JSON")
    ap.add_argument("--only", default=None, help="只跑某一条变异 (id 前缀)")
    ap.add_argument(
        "--selfcheck-syntax",
        action="store_true",
        help="负控之负控: 只跑编译自检 (旧 M15 串必判 SYNTAX-INVALID), 不改盘、不跑门",
    )
    args = ap.parse_args()

    if args.selfcheck_syntax:
        return _selfcheck_syntax()

    for p in _TARGET_FILES:
        if not p.exists():
            print(f"⛔ 目标文件不存在: {p}", file=sys.stderr)
            return 2

    # ⛔ 判据本身先自检: expect_msg 在门文件里不唯一 ⇒ 「红在哪一条断言上」不再可证。
    if bad := _check_expect_msg_unique():
        for b in bad:
            print(f"⛔ expect_msg 唯一性自检失败 — {b}", file=sys.stderr)
        return 2

    # ⛔ 基线覆盖**所有会被变异的文件**, 不是只盯一个: grep 标记有盲区
    # (变异体文本未必含该字样), 全文件 sha 才是外部锚点。
    baseline = {str(p): (p.read_bytes(), _sha(p)) for p in _TARGET_FILES}
    restored = {"done": False}

    def restore_all() -> None:
        if restored["done"]:
            return
        for sp, (data, _) in baseline.items():
            Path(sp).write_bytes(data)
        restored["done"] = True

    def _on_signal(signum, _frame):
        # ⛔ SIGTERM 默认处置不做栈展开 ⇒ finally 不执行 ⇒ 变异体留在生产文件里。
        restore_all()
        print(f"\n⚠️ 收到信号 {signum}, 已无条件还原全部目标文件后退出", file=sys.stderr)
        sys.exit(130)

    # SIGQUIT (Ctrl-\) 的默认处置同样不做栈展开 —— 漏了它 finally 一样不执行。
    # SIGKILL 挡不住, 如实声明: 被 -9 打断时变异体会留在生产文件里, 须手动 restore。
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT):
        signal.signal(sig, _on_signal)

    results = []
    try:
        for mid, path, old, new, nodeid, why, expect_msg in MUTATIONS:
            if args.only and not mid.startswith(args.only):
                continue
            src = path.read_text(encoding="utf-8")
            n = src.count(old)
            if n != 1:
                results.append({"id": mid, "verdict": "ANCHOR-DRIFT", "hits": n, "nodeid": nodeid, "why": why})
                print(f"⛔ {mid}: 锚点命中 {n} 次 (应为 1) — 生产代码已漂移, 变异未施加")
                continue
            mutated = src.replace(old, new, 1)
            # ⛔ 先编译自检, 再跑门: 语法不合法的变异体制造的是**假杀**, 不是结论。
            syn = _syntax_error(path, mutated)
            if syn is not None:
                results.append(
                    {"id": mid, "verdict": "SYNTAX-INVALID", "nodeid": nodeid, "why": why, "syntax_error": syn}
                )
                print(f"⛔ SYNTAX-INVALID {mid}: 变异体编译不过 — {syn}")
                continue
            path.write_text(mutated, encoding="utf-8")
            try:
                rc, out = _run_gate(nodeid)
            finally:
                # 逐条立即还原: 下一条变异必须打在干净的树上。
                for sp, (data, _) in baseline.items():
                    Path(sp).write_bytes(data)
            failed = _failed_nodeids(out)
            err_text = _error_lines(out)
            # ⛔ 判据只看**失败那一条断言自己的消息**(短摘要 reason), 不看整份回溯:
            # 见 `_failed_reasons` 的 docstring (独立复核 round-2 R2-01)。
            reasons = [r for nid, r in _failed_reasons(out) if _hit(nodeid, {nid})]
            expect_hit = expect_msg is None or any(expect_msg in r for r in reasons)
            # ⛔ 判据 = rc 非零 **且 指定的那道门**在失败集里 **且 指定的那一条断言**
            # 真的抛了。只判 rc 会被别的门红了喂饱; 只判 nodeid 会被**同一个门里
            # 别的断言**喂饱 —— 后者正是旧 M15 假杀的形态。
            killed = rc != 0 and _hit(nodeid, failed) and expect_hit
            results.append(
                {
                    "id": mid,
                    "verdict": "KILLED" if killed else "SURVIVED",
                    "rc": rc,
                    "nodeid": nodeid,
                    "failed": sorted(failed),
                    "expect_msg": expect_msg,
                    "expect_hit": expect_hit,
                    "why": why,
                    "failed_reasons": reasons,
                    "error_lines": err_text.splitlines()[:8],
                    "tail": out.strip().splitlines()[-3:],
                }
            )
            _why_not = "" if killed else (" (expect_msg 未命中抛出的异常文本)" if not expect_hit else "")
            print(
                f"{'✅ KILLED  ' if killed else '❌ SURVIVED'} {mid}: rc={rc} "
                f"failed={sorted(failed) or '∅'} expect_hit={expect_hit}{_why_not}"
            )
    finally:
        restore_all()

    drift = [str(p) for p in _TARGET_FILES if _sha(p) != baseline[str(p)][1]]
    ok_restore = not drift

    # ⛔ 判据是「与基线集合相同」而不是「= 0」: 基线 03ac8bf8 上就有 5 个既有
    # 负控脚本含该字面量 (g32b / g32cb / g32ccr1 / openapi_drift_negative_control /
    # recap_domain_negverify)。拿「= 0」当判据在本仓**恒不可达** —— 那是期望值
    # 没有独立来源的典型形态。
    def _mark_files() -> set[str] | None:
        """含 MARK 字面量的文件集合; 扫描本身失败时返回 None (不是空集)。

        ⛔ **不 shell out 到 `grep`** (2026-09-05 实测, 独立复核 R1-05 的延伸):
          ① 同一个名字在不同环境解析到**不同程序** —— 本机交互 shell 的 `grep`
             是个函数, 最终跑的是 ugrep 7.8.4, 它对**二进制文件默认静默跳过**;
             而 Python 的 subprocess 解析到 `/usr/bin/grep` (BSD), 它会报。于是
             「同一条判据」的结论取决于 PATH, 换台机器就可能静默失明 —— 那正是
             负控最不能有的东西。实测同一个 `.pyc`: shell 的 grep rc=1 (没看见),
             `/usr/bin/grep -l` 报出文件名。
          ② `.pyc` 里的常量折叠会把 `"MUT" + "ANT"` 变成一个**真正的** MARK
             字面量 —— 那也是残留, 不该因为它是二进制就看不见。
        扫描面 1166 个文件 / 19.6 MB (实测), 逐字节扫的代价可以忽略。
        """
        roots = (REPO / "canvas-vault", BACKEND / "app", BACKEND / "scripts", BACKEND / "tests")
        needle = MARK.encode()
        # ⛔ root 不存在时 rglob 静默返回空 —— 那会让扫描面缩水而判据照样报「无残留」。
        for root in roots:
            if not root.is_dir():
                print(f"⛔ MARK 扫描面缺失: {root} 不存在 — 判扫描失败, 不当成「没有残留」")
                return None
        hits: set[str] = set()
        walk_failed = False

        def _on_walk_error(err: OSError) -> None:
            # ⛔ `Path.rglob` 对**读不进去的目录**是静默跳过的 —— 扫描面缩水而判据照样
            # 报「无残留」。`os.walk(onerror=...)` 是唯一能把它变成信号的方式 (内部对抗
            # 审查: 不可读**文件**硬 fail-closed、不可读**目录**却静默跳过, 两种相反结局)。
            nonlocal walk_failed
            print(f"⛔ MARK 扫描失败 (遍历 {getattr(err, 'filename', '?')} 出错): {err}")
            walk_failed = True

        for root in roots:
            for dirpath, _dirnames, filenames in os.walk(root, onerror=_on_walk_error, followlinks=False):
                for fn in filenames:
                    p = Path(dirpath) / fn
                    try:
                        # ⛔ 用 `os.lstat` 而不是 `Path.is_file()` / `is_symlink()`
                        # (独立复核 round-2 R2-02): pathlib 的这两个谓词把 `OSError`
                        # **吞成 False** —— 目录能列名字但没有搜索权限时, stat 的 EACCES
                        # 被转成「不是普通文件」直接跳过, 而 `walk_failed` 仍是 False
                        # ⇒ 漏扫了还报告扫描成功。`os.lstat` 会把错误抛出来。
                        # symlink 不跟随。⚠️ 依据如实收窄 (内部对抗审查): 这**不是**因为
                        # 扫描面里现在有 symlink —— 实测扫描面里 symlink 数 = 0, 而且
                        # `os.walk(followlinks=False)` 本来就不进目录 symlink。留着它是
                        # 纵深: 将来若有人往这四个 root 里放一个指向仓外的链接, 跟随会把
                        # 扫描面悄悄扩出去(或绕回来数两遍), 那两种都会让判据不可信。
                        st = os.lstat(p)
                        if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
                            continue
                    except OSError as e:
                        print(f"⛔ MARK 扫描失败 (lstat {p} 出错): {e}")
                        return None
                    try:
                        with p.open("rb") as fh:
                            tail = b""
                            while True:
                                chunk = fh.read(1 << 20)
                                if not chunk:
                                    break
                                if needle in tail + chunk:
                                    hits.add(str(p))
                                    break
                                # 跨块边界的命中要靠这段重叠尾巴, 不能只看单块。
                                # (len(needle)==1 时 `chunk[-0:]` 会取**整块**, 尾巴逐块
                                #  翻倍 ⇒ 内存爆掉。当前 MARK 是 6 字符走不到, 别留坑。)
                                tail = chunk[-(len(needle) - 1) :] if len(needle) > 1 else b""
                    except OSError as e:
                        print(f"⛔ MARK 扫描失败 (读 {p} 出错): {e}")
                        return None
        if walk_failed:
            return None
        return hits

    # ⛔ 判据是**集合相等**, 两个方向都要看 (独立复核 R1-05): 只算 actual - baseline
    # 时, 基线里某个文件被删/改名会静默通过 —— 而那意味着基线本身已经过期,
    # 「与基线相同」这句话不再成立。
    _raw_marks = _mark_files()
    scan_ok = _raw_marks is not None
    _self_src = str(Path(__file__).resolve())
    if scan_ok:
        # leftovers 报**实际那个文件**(不是归一化后的源路径), 否则读日志的人不知道
        # 到底是哪个文件留了残留。
        leftovers = sorted(
            f for f in _raw_marks if _source_of(Path(f)) != _self_src and _source_of(Path(f)) not in BASELINE_MARK_FILES
        )
        # ⛔ baseline_missing 只认**源文件自身**的直接命中, 不认它的 `.pyc` (内部对抗审查):
        # 归一化会让一份陈旧的 `__pycache__` 字节码替一个已被删掉/改名的基线源文件顶包,
        # 于是「基线是否还成立」这个方向静默失效 —— 而它正是 R1-05 新加进来的那一半。
        _direct = {str(Path(f).resolve()) for f in _raw_marks}
        baseline_missing = sorted(BASELINE_MARK_FILES - _direct)
    else:
        # ⛔ 不往**路径列表**字段里塞哨兵字符串 (内部对抗审查): JSON 消费方会把
        # `"<扫描失败>"` 读成「有一个叫这个名字的残留文件」。失败用 `mark_scan_ok`
        # 这个布尔表达, 两个列表置 None ⇒ 语义是「未知」, 不是「无」。
        leftovers = None
        baseline_missing = None

    n_killed = sum(1 for r in results if r["verdict"] == "KILLED")
    n_syntax = sum(1 for r in results if r["verdict"] == "SYNTAX-INVALID")
    print("\n── 汇总 ──")
    print(f"杀灭: {n_killed}/{len(results)}")
    print(f"SYNTAX-INVALID: {n_syntax} (>0 说明负控自己坏了, 不是被测物坏了)")
    print(f"还原逐字节相同: {'是' if ok_restore else '否 — ' + ', '.join(drift)}")
    print(f"{MARK} 扫描: {'完成' if scan_ok else '⛔ 失败 (见上)'}")
    _unknown = "⛔ 未知 (扫描失败, 不等于「无」)"
    print(f"{MARK} 新增残留 (基线之外): {_unknown if leftovers is None else (leftovers or '无')}")
    print(
        f"{MARK} 基线缺失 (基线里有而实测没有): {_unknown if baseline_missing is None else (baseline_missing or '无')}"
    )
    survived = [r for r in results if r["verdict"] != "KILLED"]
    for r in survived:
        print(f"  · {r['id']} {r['verdict']} — {r['why']}")
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "results": results,
                    "killed": n_killed,
                    "total": len(results),
                    "syntax_invalid": n_syntax,
                    "restore_identical": ok_restore,
                    "mark_scan_ok": scan_ok,
                    "leftovers": leftovers,
                    "baseline_missing": baseline_missing,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    # ⛔ 退出码必须反映**负控本身的结论**, 不只是「还原干净」(独立复核 M4 实测:
    # 用一条无效变异跑真实门, 得到 SURVIVED 却 rc=0 —— 一条死门可以让整份负控
    # 看起来通过)。判据: 有选到东西 + 无锚点漂移 + 全部 KILLED + 还原干净 +
    # 扫描真的跑成了 + 无残留 + 基线不缺项 (后三条见独立复核 R1-05)。
    all_killed = bool(results) and all(r["verdict"] == "KILLED" for r in results)
    if not results:
        print("⛔ 没有任何变异被选中 (--only 过滤过窄?) — 判失败, 免得空跑被当成通过")
    return 0 if (all_killed and ok_restore and scan_ok and not leftovers and not baseline_missing) else 1


if __name__ == "__main__":
    sys.exit(main())
