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
import stat
import subprocess
import traceback
import sys
from collections.abc import Callable
from pathlib import Path

# ⛔ 判据本体已抽成共用模块 (CARD-DEBT-mutation-kill-identity): 四套 harness
# 共用同一份「击杀必须落在声称的断言上 + 变异体先编译自检」，避免同一道封堵
# 在四个文件里各写一遍、各漂一点。本文件只保留**它自己的**变异表与跑法。
from mutation_kill_identity import (
    VERDICTS,
    RestoreGuard,
    check_expect_msg_unique,
    failed_locations,
    failed_reasons,
    gate_hit,
    judge_env,
    judge_flags,
    kill_identity,
    parse_failed_nodeids,
    syntax_check,
)

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
#: `expect_msg` = **预期打红的那一条断言**的消息片段。
#: ⛔ **口径更正(Codex round-7 LOW)**: 此前这里写「判据只取 pytest 回溯里以 `E ` 开头的行」
#: ——**与实际不符**。round-19 统一走 `kill_identity()` 之后, 真正进裁决的是**摘要区**
#: (`-rf` 的 `FAILED <nodeid> - <reason>`) 里该 nodeid 的 reason;
#: 本文件下面那个 `err_text = _error_lines(out)` 只进 `results` 当**诊断记录**, 不参与裁决。
#: 原来那条纪律本身仍然成立, 只是落点换了: ⛔ 不得拿 `msg in stdout` 当判据 ——
#: pytest 的 long traceback 会把**整个测试函数的源码**打出来, 于是该函数里每一条断言的
#: 消息串都出现在 stdout 里, 那等于「判据被自己要找的东西喂饱」。摘要区取法(而不是整份
#: stdout)才是现在兜住它的东西。
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


#: 编译自检委托给共用模块的 `syntax_check()`。
#:
#: ⚠️ 与本卡之前的实现有**一处放宽**且是刻意的: 原正则 `python3 - <<'PYEOF'` 与
#: `test_g3_3_cas.py:36` 逐字相同, 但它匹配不到 `start-exam-board/SKILL.md:246`
#: 那种**带参数**的引导行 (`python3 - "节点/<target>.md" <<'PYEOF'`) —— 该文件
#: 3 个块里有 1 个从来没被编译自检覆盖过, 而 M14 正是打在这个文件上。共用模块
#: 用的是广义正则, 5 个块全覆盖; 未变异状态下 5 块逐块 compile 均通过 (实测),
#: 所以放宽只增加覆盖面, 不制造假 SYNTAX-INVALID。
def _syntax_error(path: Path, text: str) -> str | None:
    return syntax_check(path, text)


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


def _check_expect_msg_unique() -> list[str]:
    """每条 `expect_msg` 必须在它绑定的门文件里**恰好出现一次** (共用门, 见模块)。"""
    return check_expect_msg_unique(
        [(m[0], str(BACKEND / m[4].split("::", 1)[0]), m[6]) for m in MUTATIONS],
        prod_roots=(REPO / "canvas-vault", BACKEND / "app"),
    )


def _run_gate(nodeid: str) -> tuple[int, str]:
    proc = subprocess.run(
        # ⛔ round-19: 命令行开关统一从 `judge_flags()` 取（四套一份）。本套原先
        # **没有** `--tb=line` ⇒ 输出里根本没有失败位置行, (c)① 的位置判据无从求值;
        # 也没有 `--show-capture=no` ⇒ captured 区里被测进程可以伪造摘要行。
        [sys.executable, "-m", "pytest", *judge_flags(), "--no-header", nodeid],
        cwd=str(BACKEND),
        capture_output=True,
        text=True,
        timeout=1800,
        # ⛔ 判据面所需的环境 (COLUMNS 给足, 否则 `-rf` 的 reason 被截成空串 ⇒
        # 判据恒不命中 = 假 SURVIVED) 统一由共用模块的 judge_env() 给。
        env={**_env(), **judge_env()},
    )
    return proc.returncode, proc.stdout + proc.stderr


def _env() -> dict:
    import os

    return dict(os.environ)


#: `RestoreGuard` 收到信号、**还原成功**后抛的退出码；还原失败时它抛 `+1`（= 131）。
_SIGNAL_EXIT_CODE = 130


def _swallowed_cause(exc: BaseException) -> BaseException | None:
    """穿过 `__cause__` / `__context__` 链，找出被 `SystemExit` **盖住**的原始异常。

    ⛔ Codex round-5 MEDIUM：`RestoreGuard.critical()` 的 `finally` 在**本体已经抛了
    `OSError`** 的情况下仍会跑 `_finish(pending)` —— 它重试 `restore()` 这次成功了，于是抛
    `SystemExit(130)`。Python 把正在处理的 `OSError` 挂到新异常的 `__context__` 上，而调用
    方只看见一个**干净形态**的 130 ⇒ 首次那次真实的还原失败**一点痕迹都不留**。

    判据：`SystemExit` 底下压着非 `SystemExit` 的异常 ⇒ 这不是「干净的信号退出」，
    而是「一次被盖住的失败」。返回那个原始异常（没有则 `None`）。

    ⛔ `exc` **本身不是 `SystemExit`** 时返回 `None` —— 那种情况下没有任何东西被「盖住」，
    异常就摆在那儿。（初版漏了这个前置判断，于是一个普通的 `OSError` 也被报成「被退出码
    盖住」，措辞又一次说得比事实宽 —— 与同轮要修的 LOW 是同一个病。）

    ⛔⛔ **两支都要走**（Codex round-6 MEDIUM）：`raise SystemExit(130) from SystemExit(130)`
    在处理 `OSError` 时抛出 ⇒ `__cause__` 是那个 `SystemExit`、`__context__` 才是 `OSError`。
    上一版写 `cur.__cause__ or cur.__context__`（优先链），沿 `__cause__` 走到底就返回 `None`，
    `OSError` 被整条漏掉。现在按**广度**遍历 `__cause__` 与 `__context__` **两支**。
    ⛔⛔ **不理会 `__suppress_context__`**（这一条是上面那条修复的第二次迭代）：
    `raise X from Y` **总是**把 `__suppress_context__` 置真 —— 它是给 **traceback 打印**
    用的显示提示，不是「那次失败没发生」。初版拿它当豁免，结果恰好把 Codex 的反例
    （`raise SystemExit(130) from SystemExit(130)`，`__context__` 里压着 `OSError`）放行了 ——
    一个**给判据用的**豁免口，正好是本函数要堵的那类洞。本函数是 fail-closed 的诊断判据：
    ⚠️ 代价如实说 —— `raise ... from None` 之后若确实有别的异常在处理中，本函数**会**把它
    报出来。对这个判据而言宁可多报一次，也不能放过一次被盖住的还原失败。
    """
    if not isinstance(exc, SystemExit):
        return None
    seen: set[int] = {id(exc)}
    queue: list[BaseException] = [n for n in (exc.__cause__, exc.__context__) if n is not None]
    while queue:
        cur = queue.pop(0)
        if id(cur) in seen:
            continue
        seen.add(id(cur))
        if not isinstance(cur, SystemExit):
            return cur
        queue.extend(n for n in (cur.__cause__, cur.__context__) if n is not None)
    return None


def _report_restore_concern(headline: str, detail_of: str, verify: Callable[[], list[str]] | None) -> None:
    """把一件「还原相关、需要人看一眼」的事实**印出来**，并就地跑还原逐字节自检。

    ⛔ `headline` 由调用方给 —— 这个函数**不许**替调用方断言发生了什么。
    round-5 LOW 抓到的正是这一点：末次还原**成功**、只是本轮早些时候有失败被吞时，
    上一版照样印「末次还原失败」，那是本卡要消灭的那类措辞（说得比证据宽）。

    ⛔ 自检本身失败不得掩盖被报的事：那时「还原干净」这句话是**「未知」而不是「是」**
    （与 g33 汇总段对扫描失败的措辞同口径）。本函数**不抛**——诊断绝不能改变控制流。
    """
    drift: list[str] | str | None
    if verify is None:
        # ⛔ Codex round-7 MEDIUM：**没跑自检就不能说「未检出漂移」**。上一版把 `None`
        # 和「跑了、结果是空」折成同一个分支，于是一条根本没做的检查被报成了「没问题」——
        # 这正是本卡从头到尾在消灭的那类话。
        drift = None
    else:
        try:
            drift = list(verify())
        except BaseException as verr:  # noqa: BLE001  自检失败不得掩盖被报的事
            drift = f"⛔ 自检本身失败({verr!r}) —— 「还原干净」此刻是「未知」而不是「是」"
    if drift is None:
        detail = "⛔ **未跑**(本次调用没给自检回调) —— 「还原干净」此刻是「未知」而不是「是」"
    elif isinstance(drift, str):
        detail = drift
    elif drift:
        detail = f"漂移 {', '.join(drift)}"
    else:
        # ⛔ Codex round-8 LOW：后缀也不得替调用方归因。标题已写「未必来自还原本身」，
        # 后缀却仍说「本轮还原报过错」—— 外层 TimeoutError 展开、还原其实三次全成功时
        # 那句就是假的。只说「本次有异常要报」这个不带归因的事实。
        detail = "未检出漂移(但本次有异常要报, 不得据此断言一切正常)"
    try:
        print(f"⛔ {headline}: {detail_of} —— 还原逐字节自检: {detail}", file=sys.stderr, flush=True)
    except BaseException:  # noqa: BLE001  日志失败不改变控制流
        pass


def restore_or_keep_exit_code(
    restore_all: Callable[[], None],
    exiting: Callable[[], bool],
    *,
    final: bool = False,
    verify: Callable[[], list[str]] | None = None,
    clean_exit_code: int | None = None,
    pending_failures: list[str] | None = None,
) -> bool:
    """还原一次；返回 `True` = 还原成功。

    `_finish` 抛 `SystemExit(131)` 后栈展开仍进 `finally` 再还原一次；还原若持续
    遇到同一个 I/O 错误，第二次异常会替换掉 131 —— 约定的「还原失败」信号丢了。
    ⇒ 已在退出展开中时吞掉二次异常，保住约定退出码（round-3 MEDIUM）。

    ⛔ round-4 HIGH：绑**进入时**的状态。`exiting()` 在 `_finish` 抛出之前就置位，
    于是「正常还原期间收到信号」产生的首次 `SystemExit(130)` 会被这里吞掉，进程继续
    跑下一条变异 —— 信号退出彻底失效。只抑制**进来前就已在退出展开**的那一类。
    这条约定本轮**不变**：还原成功时控制流一动不动，首次信号的 130 照旧保号。

    ⛔ round-20（MEDIUM②）收口的是另一件事：**末次还原的新失败被静默吞掉**。
    收口前 `except` 分支只 `traceback.print_exc()` 后 `pass`，于是
      · 「还原失败过」这个事实除了一段 traceback 之外**不留痕**；
      · 原先那个 `SystemExit(130)` 继续展开 ⇒ `main()` 走不到汇总段的 `drift` /
        `ok_restore` 计算与那道 rc=3 检查 ⇒ **SHA 自检根本没跑**，而「变异体可能留在
        生产文件里」正是这个 harness 最不能漏报的一件事。
    现在：
      · 非末次失败 —— 仍吞异常保号（退出码约定不变），但**返回 `False`** 让调用方记账。
        ⚠️ 那本账（`restore_failures`）只有主循环**正常跑完**时才走得到汇总段与 `--json`
        写块；若当时正有 `SystemExit` 在展开（信号退出），记完账后原异常继续上抛，汇总段
        一行都执行不到。
        ⛔ **round-3 那版的收窄声明仍然说得太宽**（Codex round-4 LOW 实测）：它说这条路
        「由守卫退出码与末次还原的报告兜」—— 但「守卫首次还原成功 → 中途某条还原失败 →
        末次还原成功」这一串跑下来，退出码是 **130**（不是 131）、末次也**不报失败**，
        于是那次中途失败只剩一段 traceback，两个「兜底」一个都没兜上。
        ⇒ 现在把账**传进来**（`pending_failures`）：末次还原**即使成功**，只要这本账非空
        就照样打印并跑一次逐字节自检。这样信号展开那条路上它也显形。
      · 末次失败（`final=True`）—— 先跑 `verify()`（还原逐字节自检）并把结果印出来，
        **且仅当进来时已在退出展开**（`exiting()` 为真）才把退出码升到 3
        （「变异体可能留在生产文件里」比「被信号中断」严重，与 `main()` 里
        `not ok_restore ⇒ return 3` 同口径）。⛔ 进来时**没在**退出展开时，原异常
        **原样重抛**、不升 3 —— 那条路上异常本来就会自己浮出来，替它换个退出码反而
        把真实失败类型盖掉（Codex round-6 LOW：上一版这句漏写了前置条件）。

    ⚠️ 本函数原为 `main()` 内的**嵌套 def**，无模块级符号 ⇒ 末次还原这条路径在进程内
    根本驱动不了，负控也就无从落地（`--selfcheck-syntax` 早返回、走不到这里；只要
    **走到主 `try`**，`finally` 就会对 `_TARGET_FILES` 全量写回，含零写者铁律覆盖的
    `fsrs_bridge.py`）。
    ⛔ round-21（Codex round-18 LOW）**更正原文「其它任何入口都会写回」这句过强的说法**：
    主 `try` **之前**还有**两处早返回**（目标文件不存在 ⇒ `return 2`；`_check_expect_msg_unique()`
    自检失败 ⇒ `return 2`），走那两条路不写回。但结论不变 —— 它们**不可依赖**
    （取决于工作树当时的状态），所以「负控不起 g33 子进程」这条纪律照旧。
    提为模块级 + 注入 `restore_all` / `exiting` 回调是
    为了让它可被单测**在进程内**驱动（CARD-DEBT-mutkill-R3 (h)④，主 session 已按
    R-B14-9 补裁接受由此带来的 diff 扩大）。
    """
    was_exiting = exiting()
    try:
        restore_all()
    except BaseException as exc:
        # ⛔ Codex round-1 LOW：**干净的信号退出不是还原失败**。`RestoreGuard` 收到信号时
        # 先把 `restore()` 跑完、再抛 `SystemExit(exit_code)`；若该信号落在**本次**还原期间
        # （进来时 `exiting()` 为假、出来时为真），这个 SystemExit 说明的是「还原做完了，
        # 然后按约定退出」，⛔ 不是「还原失败」。不分辨的话，一次**正常**的 Ctrl-C 会让
        # 报告印出「末次还原失败／不得当成干净」—— 那正是本卡要消灭的那类谎报。
        #
        # ⛔⛔ Codex round-2 MEDIUM：但**只认那一个退出码**。`RestoreGuard._finish` 在
        # 「还原本身失败」时抛的是 `SystemExit(exit_code + 1)`（= 131）—— 那恰恰**是**
        # 还原失败的约定信号。上一版把「是不是 SystemExit」当判据，于是 131 被当成干净
        # 退出放行，末次逐字节自检**零次调用** = 把本卡承诺的那道检查又丢了一次。
        # `clean_exit_code=None`（未告知干净码）⇒ **fail-closed**：一律按还原失败处置。
        # ⛔ round-6：干净退出还要求**底下没压着别的异常**。守卫在「本体已抛 OSError」时
        # 仍会重试 `restore()`，重试成功就抛形态干净的 130，把首次那次真实失败盖成
        # `__context__` —— 只看退出码分不出「一次成功的信号退出」和「一次被盖住的失败」。
        # ⛔ round-17（本轮 25 层负控自查抓到，不是 Codex 提的）：这里**曾经**还挂着
        # `and swallowed is None`。拆掉它跑全套单测 **0 红** —— 于是去核为什么：`guard_exit`
        # 全模块只被下面那个 `elif` 读一次，而走到 `elif` 就意味着上面的 `if swallowed is not
        # None` 为假 ⇒ 那个合取项在**唯一**的读取点上恒为真，**永远改不了任何分支**。
        # 它不是一层防线，是一句读起来像防线的重复条件 —— 正是本卡要消灭的那类措辞。
        # ⇒ 删掉，并把「谁保证了它」写在这里。⚠️ 后人若把下面的 `elif` 改成 `if`，
        # 这个前提就没了，那时必须把 `and swallowed is None` 加回来。
        # （原始意图见上一段注释：守卫重试成功会把首次真实失败盖成 `__context__`；
        #   那件事由紧接着的 `if swallowed is not None:` 分支负责报，不靠这个合取项。）
        swallowed = _swallowed_cause(exc)
        guard_exit = (
            clean_exit_code is not None
            and isinstance(exc, SystemExit)
            and exc.code == clean_exit_code
            and not was_exiting
            and exiting()
        )
        if swallowed is not None:
            # ⛔ Codex round-6 MEDIUM：**不分 final 与否都要报**。逐条还原那条路
            # （`final=False`）在 `was_exiting` 为假时直接 `raise`，记账那行根本走不到 ——
            # 于是「守卫重试成功、盖住首次真实失败」在**逐条**入口上仍旧一点痕迹不留。
            # 这行打印是那条路上唯一能留下痕迹的地方。
            # ⛔ Codex round-7 LOW：**不得把它归因给「还原」**。`__context__` 链上压着的
            # 可能是更外层的异常（例如跑门时的 `TimeoutExpired` 正在展开，还原其实三次全成功），
            # 本函数分辨不了来源 —— 那就只说「有异常被退出码盖住」，把 repr 给出来让人判断。
            _report_restore_concern(
                f"{'末次' if final else '逐条'}还原的退出码盖住了一个异常(未必来自还原本身)",
                repr(swallowed),
                verify,
            )
        elif final and not guard_exit:
            # ⛔ SHA/还原逐字节自检**必须在这里就跑**：往下无论是 `raise`（把原异常
            # 继续展开）还是 `SystemExit(3)`，`main()` 的汇总段都一行都到不了。
            _report_restore_concern("末次还原失败", repr(exc), verify)
        if not was_exiting:
            raise
        # ⚠️ `traceback.print_exc()` 只在**吞没**这条路上打 —— 要 `raise` 的那条由上层
        # 打，这里再打一遍就是同一个异常印两次（收口前也是只在这条路上打，不改它）。
        try:
            traceback.print_exc()
        except BaseException:  # noqa: BLE001  日志失败不改变控制流
            pass
        if final:
            # ⛔ 升到 3 而不是继续保 130：「变异体可能留在生产文件里」是更严重、且
            # **必须盖过一切**的硬事实（与 `main()` 里 `not ok_restore ⇒ return 3` 同口径）。
            raise SystemExit(3) from exc
        return False
    if final and pending_failures:
        # ⛔ 末次还原**成功**，但这一轮里有还原**失败过** —— 信号展开那条路上汇总段到不了，
        # 这里是这件事最后一次能被说出来的地方（Codex round-4 LOW）。
        # ⚠️ 措辞必须说实话：末次是**成功**的（round-5 LOW —— 上一版照抄「末次还原失败」）。
        _report_restore_concern(
            "末次还原成功, 但本轮早些时候有还原失败被吞",
            f"{len(pending_failures)} 次（{', '.join(pending_failures)}）",
            verify,
        )
    return True


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

    def restore_all() -> None:
        # ⛔ round-19: 去掉 `restored["done"]` 早退闩。它让「还原」变成**一次性**事件,
        # 而后面每条变异跑完都要还原一次 —— 早退闩一旦置位, 之后的还原全被跳过。
        # (收口前它没出事只是因为调用点恰好都在最后; 这类闩是「降级开关是闩不是事件」
        #  那条教训的同族。) 现在无条件写回, 幂等。
        with _guard.critical():  # 还原期收到的信号只记待办、不打断
            for sp, (data, _) in baseline.items():
                Path(sp).write_bytes(data)

    # ⛔ 四个信号 + 先还原再退出 + **还原期不可打断**, 四套统一（见 RestoreGuard）。
    # 收口前这里已经是「先还原再退出」且四信号齐全, 缺的是最后一条: 还原循环本身
    # 若被第二个信号打断, 会停在「还原了一半」的状态。
    # SIGKILL 挡不住, 如实声明: 被 -9 打断时变异体会留在生产文件里, 须手动 restore。
    # ⛔ 干净信号退出码与「还原失败」码（= 它 + 1，见 `RestoreGuard._finish`）必须有
    # **单一来源**：末次还原路径要靠它分辨「还原做完了才退出」与「还原失败才退出」。
    _guard = RestoreGuard(restore_all, exit_code=_SIGNAL_EXIT_CODE)
    _guard.install()

    def _verify_restore() -> list[str]:
        """还原逐字节自检：与基线 sha 不同的目标文件（空 = 还原干净）。

        ⛔ 这个闭包是**唯一**一份「怎么算漂移」的写法，汇总段与末次还原失败路径都调它
        —— 两份手抄的判据必然漂移，而漂移正是这道门要抓的东西。
        """
        return [str(p) for p in _TARGET_FILES if _sha(p) != baseline[str(p)][1]]

    #: 还原**报过错**的那几次（异常被吞以保住约定退出码时仍记账）。⛔ 空列表才算干净：
    #: 「最后 sha 对得上」证明不了「中间没出过事」。
    restore_failures: list[str] = []
    results = []
    try:
        for mid, path, old, new, nodeid, why, expect_msg in MUTATIONS:
            if args.only and not mid.startswith(args.only):
                continue
            src = path.read_text(encoding="utf-8")
            n = src.count(old)
            if n != 1:
                # ⛔ round-19 改名: 收口前本套叫 `ANCHOR-DRIFT`, 另三套叫 `ANCHOR-ERROR`
                # —— 同义不同名, 跨套对照汇总时要靠人脑翻译。统一成后者。
                results.append({"id": mid, "verdict": "ANCHOR-ERROR", "hits": n, "nodeid": nodeid, "why": why})
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
                # ⛔ round-19: 走 `restore_all()`（内含 `critical()`）而不是自己写循环 ——
                # 循环中途收到信号时旧写法会停在还原了一半的状态。
                # ⛔ round-20: 吞异常保号可以，但「还原失败过」这件事不得丢失 —— 记账,
                # 汇总段的 `ok_restore` 会把它算进去（sha 对得上也不算数: 还原过程报过错）。
                # ⛔ round-7: 逐条这一路也要给 `verify` 与 `clean_exit_code` ——
                # 缺 `verify` 会让报告把「没跑自检」说成「未检出漂移」(M-2)；
                # 缺 `clean_exit_code` 会让这一路 fail-closed 成「一律按失败处置」。
                if not restore_or_keep_exit_code(
                    restore_all,
                    _guard.exiting,
                    verify=_verify_restore,
                    clean_exit_code=_SIGNAL_EXIT_CODE,
                ):
                    restore_failures.append(mid)
            # ⛔ 先问「判据面在不在」再问「杀没杀死」: 缺 `-rf` 时短摘要不存在,
            # 判据会安静退化成恒假 ⇒ 全报 SURVIVED, 长得跟「门都不承重」一样。
            failed = parse_failed_nodeids(out)
            err_text = _error_lines(out)
            reasons = [r for nid, r in failed_reasons(out) if gate_hit(nodeid, {nid})]
            expect_hit = expect_msg is None or any(expect_msg in r for r in reasons)
            locs = [(Path(_p).name, _ln) for _p, _ln, _ in failed_locations(out)]
            # ⛔ round-19: 裁决统一走共用模块的 `kill_identity()`, 六档口径与另三套逐字
            # 一致。判据依次是: 判据面在不在 → rc 恰为 1 → 摘要区里失败的是不是**指定的
            # 那道门** → 失败**位置**在不在门文件里 ((c)① 弱位置判据) → 摘要区 reason
            # 含不含 `expect_msg`。只判 rc 会被别的门红了喂饱; 只判 nodeid 会被**同一个
            # 门里别的断言**喂饱 —— 后者正是旧 M15 假杀的形态。
            # ⚠️ 按用户裁定 D-28 本套**不加** `expect_loc` ⇒ 挡不住 Y1-B HIGH-1 那种
            # 「前提断言把子进程输出插进消息首行」的形态, 已登记移交第十四批。
            # ⛔ `judge_surface_missing` 不再在这里单独调用后 `return 2`: 判据面缺失现在
            # 由 `kill_identity()` 判成 `HARNESS-ERROR` 并**继续跑完其余条目** ——
            # 原先一条判据面异常就整份中止, 「其余 17 条还好着」这个信息也一起丢掉。
            verdict, why_v = kill_identity(
                rc, out, nodeid, expect_msg, gate_file=BACKEND / TESTS, require_gate_file=True
            )
            killed = verdict.startswith("KILLED")
            results.append(
                {
                    "id": mid,
                    "verdict": verdict,
                    "verdict_why": why_v,
                    "rc": rc,
                    "nodeid": nodeid,
                    "failed": sorted(failed),
                    "expect_msg": expect_msg,
                    "expect_hit": expect_hit,
                    "failed_locations": locs,
                    "why": why,
                    "failed_reasons": reasons,
                    "error_lines": err_text.splitlines()[:8],
                    "tail": out.strip().splitlines()[-3:],
                }
            )
            print(
                f"{'✅ ' if killed else '❌ '}{verdict:15} {mid}: rc={rc} "
                f"failed={sorted(failed) or '∅'} expect_hit={expect_hit} loc={locs or '∅'} — {why_v}"
            )
    finally:
        # ⛔ round-20 (MEDIUM②): 末次还原。新失败不再被静默吞掉 —— 函数内部会先跑
        # `_verify_restore()` 把还原逐字节自检印出来。⚠️ SHA 自检必须在**那里面**跑:
        # 若原先那个 SystemExit(130) 继续展开, 下面的汇总段一行都到不了 (这正是收口前
        # 「仍报 130 且 SHA 不执行」的形态)。
        # ⚠️ **口径更正(Codex round-7 LOW)**: 此前这句写「再把退出码升到 3」——**说宽了**。
        # 升 3 **只在进来时已在退出展开**(`exiting()` 为真)那一路; 否则原异常原样重抛、
        # 不换码(替它换码反而把真实失败类型盖掉)。函数 docstring 已写明, 这里同步。
        if not restore_or_keep_exit_code(
            restore_all,
            _guard.exiting,
            final=True,
            verify=_verify_restore,
            clean_exit_code=_SIGNAL_EXIT_CODE,
            pending_failures=restore_failures,
        ):
            restore_failures.append("final")

    # ⛔ round-19 修回归: 收口前「判据面不成立」是 `return 2`(负控自己坏了)，改走
    # `kill_identity` 判 HARNESS-ERROR 之后, 它会和 SURVIVED 一起压进 rc=1 ——
    # 「门不承重」与「pytest 没跑成」两个方向完全相反的结论共用一个退出码, 正是本族
    # 反复栽的坑。⇒ 有 HARNESS-ERROR 时仍以 rc=2 报出, 且**跑完**其余条目再报
    # (收口前是当场中止, 会把「其余 17 条还好着」这个信息一起丢掉)。
    n_harness_err = sum(1 for r in results if r["verdict"] == "HARNESS-ERROR")
    # ⛔ round-20: 用 `_verify_restore()` 而不是在这里再手抄一遍判据 —— 末次还原失败
    # 路径与这里必须逐字同口径，两份手抄的清单必然漂移。
    drift = _verify_restore()
    # ⛔ round-20 (MEDIUM②): 「还原过程报过错」与「跑完 sha 对得上」是两件事。逐条还原
    # 若失败过（异常被吞以保住约定退出码），即便最后一次恰好把文件写回对了, 也不得报
    # 「还原逐字节相同」—— 中间那段窗口里到底发生了什么, 这份报告证不了。
    # ⚠️ 覆盖面如实说（Codex round-3 LOW）: 这里只在主循环**正常跑完**时才到得了；信号
    # 展开期间记下的 `restore_failures` 进不了汇总，那条路由守卫退出码与末次还原的报告兜。
    ok_restore = not drift and not restore_failures

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

    # ⛔ round-19: 六档口径与另三套逐字一致（`mutation_kill_identity.VERDICTS`）。
    # 收口前本套只有 KILLED / SURVIVED / SYNTAX-INVALID 三档, 锚点异常还另叫
    # `ANCHOR-DRIFT` —— 同一个 `kill_identity` 在四套里被四种口径消费。
    nv = {v: sum(1 for r in results if r["verdict"] == v) for v in VERDICTS}
    n_killed = nv["KILLED"]
    n_syntax = nv["SYNTAX-INVALID"]
    print("\n── 汇总 ──")
    # ⛔ 文案不得比证据宽：本套按 D-28 **没有** `expect_loc`，位置只绑到门文件一级。
    print(
        f"KILLED (绑定: 消息 + 失败位置在门文件内; ⚠️ 未绑到具体断言, expect_loc 按 D-28 移交十四批): "
        f"{n_killed}/{len(results)}"
    )
    print(f"KILLED-UNBOUND: {nv['KILLED-UNBOUND']} (仅证明指定门红了)")
    print(f"SURVIVED: {nv['SURVIVED']}")
    print(f"HARNESS-ERROR: {nv['HARNESS-ERROR']} (负控自己坏了, 不是关于被测物的结论)")
    print(f"ANCHOR-ERROR: {nv['ANCHOR-ERROR']} (变异未施加, 不是结论)")
    print(f"SYNTAX-INVALID: {n_syntax} (>0 说明负控自己坏了, 不是被测物坏了)")
    # ⛔ 分母必须是「本次**应该**处理多少条变异」，不是 `len(results)` —— 后者恒等于
    # 六档之和（每个写进 `results` 的裁决值都字面来自 `VERDICTS`），那是个**恒真判据**，
    # 什么也证不了（独立复核 2026-09-08 指出；收口时我照抄了 g32b 的形态却换错了分母）。
    # 用「选中的变异条数」当分母，才能抓住「某条变异跑完没落进任何一档」。
    _selected = [m for m in MUTATIONS if not args.only or m[0].startswith(args.only)]
    _total = sum(nv.values())
    _sum_ok = _total == len(_selected)
    print(f"六档之和: {_total} (应 = 选中的变异条数 {len(_selected)}) {'✓' if _sum_ok else '⛔ 对不上'}")
    # ⛔ round-20: 两件事分开报 —— 「跑完 sha 对不对得上」(drift) 与「还原过程有没有
    # 报过错」(restore_failures)。只印前者时，一次被吞掉的还原失败在报告里完全不存在。
    _restore_note = (
        "是"
        if ok_restore
        else "否 — "
        + ", ".join(
            ([f"字节漂移 {', '.join(drift)}"] if drift else [])
            + ([f"还原报错 {', '.join(restore_failures)}"] if restore_failures else [])
        )
    )
    print(f"还原逐字节相同: {_restore_note}")
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
                    # ⛔ total 用「选中的变异条数」而不是 len(results) —— 后者恒等于
                    # 六档之和, 消费方拿它复现「sum==total」会得到恒真式(独立复核)。
                    "total": len(_selected),
                    "partial": bool(args.only),
                    "syntax_invalid": n_syntax,
                    # round-19: 六档计数进 JSON, 消费方不必自己从 results 里数
                    "verdict_counts": nv,
                    "verdict_sum_matches_total": _sum_ok,
                    "restore_identical": ok_restore,
                    # ⛔ round-20: 还原**报过错**的那几次单列, 给消费方一份**明细**。
                    # ⚠️ 口径更正(Codex round-6 LOW): 此前这里写「与 `restore_identical`
                    # 不是同一件事(后者只看跑完的 sha)」——**不对**。`ok_restore` 已经是
                    # `not drift and not restore_failures`, 所以 `restore_identical` 在
                    # 本账非空时也是 False。两者的区别是**粒度**(布尔结论 vs 哪几条失败),
                    # 不是「看不看这本账」。
                    "restore_failures": restore_failures,
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
    all_killed = bool(results) and all(r["verdict"].startswith("KILLED") for r in results)
    if not results:
        print("⛔ 没有任何变异被选中 (--only 过滤过窄?) — 判失败, 免得空跑被当成通过")
    # ⛔⛔ 「部分跑 rc=4」这条**不能**放在还原/残留检查之前（独立复核 2026-09-08 抓到:
    # 我上一版就是那么放的）——那样 `--only` 会把「还原失败 / 标记残留 / 扫描失败」
    # 全部吞掉，而这三件正是**必须**盖过一切的。次序: 先报硬事实, 再报「部分跑」。
    if not ok_restore:
        print(f"⛔ 还原未能证明干净: {_restore_note} —— 变异体可能留在生产文件里 (rc=3)")
        return 3
    if not scan_ok:
        print(f"⛔ {MARK} 扫描失败 —— 「无残留」这句话此刻是「未知」而不是「无」 (rc=3)")
        return 3
    if leftovers or baseline_missing:
        print(f"⛔ {MARK} 残留/基线缺失: 新增={leftovers} 基线缺失={baseline_missing} (rc=3)")
        return 3
    # ⛔ 退出码语义四套统一（独立复核 2026-09-08：原先 HARNESS-ERROR 与 SURVIVED 压成
    # 同一个 rc=1 —— 「pytest 没跑成」与「门不承重」两个方向完全相反的结论共用一个码）：
    #   rc=2  有 HARNESS-ERROR（负控自己坏了，先去修 harness，别去改门）
    #   rc=1  有 SURVIVED 或别的 failures（关于被测物的结论）
    #   rc=4  部分跑（--only / --probe / --list 自检不过）—— 不构成全量结论
    #   rc=0  全部 KILLED；⚠️ **已登记**的 KILLED-UNBOUND 残留只报不判失败 ——
    #         未登记的那种在跑之前就被 `_check_expect_loc()` / `_check_expect_msg()`
    #         挡在 rc=2 上了，走不到这里。
    if n_harness_err:
        print(f"⛔ HARNESS-ERROR {n_harness_err} 条 —— 负控自己坏了, 不是关于被测物的结论 (rc=2)")
        return 2
    if args.only:
        # ⛔ 与 g32b / g32ccr1 同口径：部分跑**不构成全量结论**，rc 恒为 4。
        # 收口前 `--only M1` 跑完照样 rc=0 + 「六档之和 ✓」，与全量通过在输出上不可分 ——
        # 而定点复核的输出正是最容易被当成存档证据的那种（独立复核 2026-09-08）。
        print(f"\n⚠️ --only {args.only!r} 选中 {len(_selected)}/{len(MUTATIONS)} 条 —— 部分跑不构成全量结论，rc 恒为 4")
        return 4
    # 到这里 ok_restore / scan_ok / leftovers / baseline_missing 已各自单独判过并早退,
    # 保留在条件里是**冗余的**第二道 —— 冗余不等于多余: 它让「rc=0」这句话不依赖上面
    # 那几个早退分支的完整性（少写一个早退, 这里仍会把 rc 压到 1）。
    return 0 if (all_killed and ok_restore and scan_ok and not leftovers and not baseline_missing and _sum_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
