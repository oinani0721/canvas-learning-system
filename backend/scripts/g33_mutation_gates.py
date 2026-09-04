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

用法: `backend/.venv/bin/python backend/scripts/g33_mutation_gates.py [--json <out>]`
      (从仓库根或 backend/ 跑均可; 只读 live vault 与 7691, 不碰它们)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import signal
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

#: (id, 文件, 原文片段, 变异后片段, 必须变红的 nodeid, 一句话说明)
MUTATIONS = [
    (
        "M1-per-node-lock",
        SKILL,
        '_lock_exclusive(_lk_fd, _LOCK_TIMEOUT_S, "per-node 写锁", _lk_path)',
        f"pass  # {MARK}: 去掉 per-node 写锁",
        "tests/regression/test_g3_3_cas.py::test_concurrent_same_node_no_lost_update",
        "两进程同节点评分不再互斥 ⇒ 各按旧基线算 ⇒ attempt 双双写 1 (lost update)",
    ),
    (
        "M2-cas-guard",
        SKILL,
        '_cas_guard("正常路径发布")',
        f"pass  # {MARK}: 去掉发布前 CAS 门",
        "tests/regression/test_g3_3_cas.py::test_cas_conflict_refuses_and_rerun_converges",
        "外部写者插队后照常整份覆盖 ⇒ 用户刚写的正文被静默吃掉",
    ),
    (
        "M3-ledger-lock-backend",
        EVLOG,
        "            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\n            return True",
        f"            return True  # {MARK}: 不真的加锁, 直接报成功",
        "tests/regression/test_g3_3_cas.py::test_append_event_refuses_when_ledger_locked",
        "查重与追加不再互斥 ⇒ 同一个 event_id 被并发写多行 ⇒ 幂等键唯一性破裂",
    ),
    (
        "M5-cas-revision-only",
        BRIDGE,
        '    if cur.get("sha256") == token.get("sha256"):\n        return None',
        f'    if all(cur.get(k) == token.get(k) for k in ("fsrs_last_review", "attempt_count")):'
        f"  # {MARK}: 只比 revision 不比正文\n        return None",
        "tests/regression/test_g3_3_cas.py::test_cas_body_only_change_is_a_conflict",
        "CAS 只比 revision 两字段 ⇒ 正文改动被判「无冲突」⇒ 覆盖照做",
    ),
    (
        "M6-ledger-lock-skill",
        SKILL,
        '_lock_exclusive(_fd, _LEDGER_LOCK_TIMEOUT_S, "账本追加锁", EV)',
        f"pass  # {MARK}: 去掉写点侧账本追加锁",
        "tests/regression/test_g3_3_cas.py::test_writer_waits_for_held_ledger_lock",
        "写点侧账本追加不再互斥 (LF 守卫 + 追加的窗口暴露)",
    ),
    (
        "M8-thread-lock-lifetime",
        EVLOG,
        "        with _write_lock:\n            fd = os.open(path",
        f"        with _write_lock:  # {MARK}: 线程锁不再罩住 close\n            pass\n        if True:\n            fd = os.open(path",
        "tests/regression/test_g3_3_cas.py::test_thread_critical_sections_do_not_overlap",
        "线程锁不再覆盖 open→close 全生命周期 ⇒ 两线程临界区重叠 ⇒ 后者的锁被前者 close 撤销",
    ),
    (
        "M9-splitlines-instead-of-lf",
        EVLOG,
        '    parts = text.split("\\n")',
        f'    parts = text.splitlines()  # {MARK}: 改回 splitlines\n    _unused = text.split("\\n")',
        "tests/regression/test_g3_3_cas.py::test_dedup_scan_splits_only_on_physical_lf",
        "查重按 splitlines 切行 ⇒ 含裸 U+2028/NEL 的合法记录被切碎 ⇒ 查重漏命中 ⇒ 双写",
    ),
    (
        "M10-short-write-unchecked",
        EVLOG,
        "                if written != len(line_bytes):",
        f"                if False:  # {MARK}: 不检查短写",
        "tests/regression/test_g3_3_cas.py::test_short_write_is_not_reported_as_success",
        "短写不检查 ⇒ 残行被报告成写入成功",
    ),
    (
        "M11-out-of-order-auto-guess",
        EVLOG,
        "                if is_review and not out_of_order:",
        f"                if is_review and not out_of_order and payload_out.setdefault('out_of_order', True):  # {MARK}: 自动猜",
        "tests/regression/test_g3_3_cas.py::test_out_of_order_is_caller_declared_not_auto_guessed",
        "账本侧自动猜乱序 ⇒ 误标会让写点对该节点永久 fail-closed",
    ),
    (
        "M12-a3-node-lock",
        SKILL,
        "        fcntl.lockf(_lk_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\n        break",
        f"        break  # {MARK}: A3 增量块根本不取 per-node 锁",
        "tests/regression/test_g3_3_cas.py::test_incremental_block_waits_for_node_lock",
        "A3 增量归纳块不再等 per-node 锁 ⇒ 与写分块并发时互相覆盖",
    ),
    (
        "M13-a3-cas",
        SKILL,
        "    _c = cas_conflict(NODE, _tok)\n    if _c is not None:",
        f"    _c = None  # {MARK}: A3 去掉 CAS\n    if _c is not None:",
        "tests/regression/test_g3_3_cas.py::test_incremental_block_cas_preserves_racing_edit",
        "A3 增量块去掉 CAS ⇒ 冲突时拿旧 body 覆盖",
    ),
    (
        "M14-exam-board-ledger-lock",
        REPO / "canvas-vault" / ".claude" / "skills" / "start-exam-board" / "SKILL.md",
        "                fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\n                break",
        f"                break  # {MARK}: 建板不再取账本锁",
        "tests/regression/test_g3_3_cas.py::test_exam_board_waits_for_held_ledger_lock",
        "建板写点不再取账本锁 ⇒ 与别的写者并发时查重/追加不互斥",
    ),
    (
        "M15-post-lock-redup",
        SKILL,
        '                if isinstance(_o_lock, dict) and _o_lock.get("event_id") == evid:',
        f"                if False:  # {MARK}: 取锁后不再重查\n                if isinstance(_o_lock, dict) and False:",
        "tests/regression/test_g3_3_cas.py::test_writer_refuses_when_other_writer_took_the_event_id",
        "取锁后不重查 ⇒ 别的写者抢先写了同 event_id 时本块照常追加 ⇒ 同 ID 两行",
    ),
    (
        "M7-lock-dropped-by-second-fd",
        EVLOG,
        "                raw = _read_all(fd)",
        f"                raw = path.read_bytes()  # {MARK}: 持锁期间另开 fd ⇒ POSIX 锁整体释放",
        "tests/regression/test_g3_3_cas.py::test_append_event_still_holds_lock_at_the_moment_of_write",
        "持锁期间 open 第二个 fd ⇒ 本进程在该文件上的记录锁整体释放, 后半段临界区裸奔",
    ),
]

_TARGET_FILES = sorted({m[1] for m in MUTATIONS}, key=str)

#: 基线 `304f03ca` 上**本来就**含 MARK 字面量的文件 (既有卡的负控脚本)。
#: 复核判据 = 跑完后的集合与它相同; 多出来的才是本脚本的残留。
BASELINE_MARK_FILES = {
    str(BACKEND / "scripts" / "g32b_mutation_gates.py"),
    str(BACKEND / "scripts" / "g32cb_mutation_gates.py"),
    str(BACKEND / "scripts" / "openapi_drift_negative_control.py"),
    str(BACKEND / "tests" / "regression" / "recap_domain_negverify.py"),
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _failed_nodeids(stdout: str) -> set[str]:
    """从 pytest 输出抽失败的 nodeid。

    ⛔ 用 `-rf` 的 short summary 而不是猜: 「某处有 FAILED」不能证明**指定的那道
    门**红了 —— 拿粗判据判 KILLED 是假杀的经典形态。
    """
    return set(re.findall(r"^FAILED (\S+?)(?: - .*)?$", stdout, re.M))


def _hit(nodeid: str, failed: set[str]) -> bool:
    """声明的 nodeid 是否命中失败集 —— **含参数化用例**。

    ⛔ 实测教训: 声明 `...::test_x` 而 pytest 报的是 `...::test_x[1]`,
    直接用 `nodeid in failed` 会把真 KILLED 误报成 SURVIVED —— 判据自己坏了,
    却长得跟「门不承重」一模一样。
    """
    return any(f == nodeid or f.startswith(nodeid + "[") for f in failed)


def _run_gate(nodeid: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rf", "--no-header", nodeid],
        cwd=str(BACKEND),
        capture_output=True,
        text=True,
        timeout=1800,
        env={"PYTHONDONTWRITEBYTECODE": "1", **_env()},
    )
    return proc.returncode, proc.stdout + proc.stderr


def _env() -> dict:
    import os

    return dict(os.environ)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=None, help="把结果写成 JSON")
    ap.add_argument("--only", default=None, help="只跑某一条变异 (id 前缀)")
    args = ap.parse_args()

    for p in _TARGET_FILES:
        if not p.exists():
            print(f"⛔ 目标文件不存在: {p}", file=sys.stderr)
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

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, _on_signal)

    results = []
    try:
        for mid, path, old, new, nodeid, why in MUTATIONS:
            if args.only and not mid.startswith(args.only):
                continue
            src = path.read_text(encoding="utf-8")
            n = src.count(old)
            if n != 1:
                results.append({"id": mid, "verdict": "ANCHOR-DRIFT", "hits": n, "nodeid": nodeid, "why": why})
                print(f"⛔ {mid}: 锚点命中 {n} 次 (应为 1) — 生产代码已漂移, 变异未施加")
                continue
            path.write_text(src.replace(old, new, 1), encoding="utf-8")
            try:
                rc, out = _run_gate(nodeid)
            finally:
                # 逐条立即还原: 下一条变异必须打在干净的树上。
                for sp, (data, _) in baseline.items():
                    Path(sp).write_bytes(data)
            failed = _failed_nodeids(out)
            # ⛔ 判据 = rc 非零 **且 指定的那道门**在失败集里。只判 rc 会被别的
            # 门红了喂饱 (同一天栽过三次的「粗判据」)。
            killed = rc != 0 and _hit(nodeid, failed)
            results.append(
                {
                    "id": mid,
                    "verdict": "KILLED" if killed else "SURVIVED",
                    "rc": rc,
                    "nodeid": nodeid,
                    "failed": sorted(failed),
                    "why": why,
                    "tail": out.strip().splitlines()[-3:],
                }
            )
            print(f"{'✅ KILLED  ' if killed else '❌ SURVIVED'} {mid}: rc={rc} failed={sorted(failed) or '∅'}")
    finally:
        restore_all()

    drift = [str(p) for p in _TARGET_FILES if _sha(p) != baseline[str(p)][1]]
    ok_restore = not drift

    # ⛔ 判据是「与基线集合相同」而不是「= 0」: 基线 304f03ca 上就有 4 个既有
    # 负控脚本含该字面量 (g32b / g32cb / openapi_drift_negative_control /
    # recap_domain_negverify)。拿「= 0」当判据在本仓**恒不可达** —— 那是期望值
    # 没有独立来源的典型形态。
    def _mark_files() -> set[str]:
        out = subprocess.run(
            [
                "grep",
                "-rln",
                MARK,
                str(REPO / "canvas-vault"),
                str(BACKEND / "app"),
                str(BACKEND / "scripts"),
                str(BACKEND / "tests"),
            ],
            capture_output=True,
            text=True,
        ).stdout.split()
        # 本脚本自身的 MARK 是拼接出来的, grep 命不中; 这里仍显式排除以防将来改写。
        return {f for f in out if Path(f).resolve() != Path(__file__).resolve()}

    leftovers = sorted(_mark_files() - BASELINE_MARK_FILES)

    print("\n── 汇总 ──")
    print(f"还原逐字节相同: {'是' if ok_restore else '否 — ' + ', '.join(drift)}")
    print(f"{MARK} 新增残留 (基线之外): {leftovers or '无'}")
    survived = [r for r in results if r["verdict"] != "KILLED"]
    for r in survived:
        print(f"  · {r['id']} {r['verdict']} — {r['why']}")
    if args.json:
        args.json.write_text(
            json.dumps(
                {"results": results, "restore_identical": ok_restore, "leftovers": leftovers},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    # ⛔ 退出码必须反映**负控本身的结论**, 不只是「还原干净」(独立复核 M4 实测:
    # 用一条无效变异跑真实门, 得到 SURVIVED 却 rc=0 —— 一条死门可以让整份负控
    # 看起来通过)。判据: 有选到东西 + 无锚点漂移 + 全部 KILLED + 还原干净 + 无残留。
    all_killed = bool(results) and all(r["verdict"] == "KILLED" for r in results)
    if not results:
        print("⛔ 没有任何变异被选中 (--only 过滤过窄?) — 判失败, 免得空跑被当成通过")
    return 0 if (all_killed and ok_restore and not leftovers) else 1


if __name__ == "__main__":
    sys.exit(main())
