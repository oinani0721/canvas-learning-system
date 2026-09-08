#!/usr/bin/env python3
"""(e) 两条承重负控：Y1-B Codex HIGH-1 / HIGH-2 的形态，旧版判据放行、新版拒。

⛔ 两个判据吃的是**同一份 pytest 输出**（同一次子进程运行的 stdout+stderr）——
不是各跑各的。否则「新版拒了」可能只是因为它跑的那次输出不同（对照组不成立）。

⛔ 门文件只落在 `tempfile.mkdtemp()` 里，跑完删；**不碰 `tests/**` 真门**，也不碰
任何生产文件（卡文 §三）。

负控矩阵（含正控 —— 只有负控时「新版全拒」与「新版坏了」不可区分）：
  N1  前提断言把子进程 stderr 插进消息首行，目标断言**没执行**   → 旧 True / 新 False
  N2  captured 区伪造一行 `FAILED <nodeid> - <expect_msg>`        → 旧 True / 新 False
  P1  目标断言**真的**红了（正控）                                 → 旧 True / 新 True
  D   `--show-capture=no` 这道独立防线单独对照（不与解析收紧混算）
"""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TREE = Path(__file__).resolve().parents[3]
NEW_MOD = TREE / "backend" / "scripts" / "mutation_kill_identity.py"
VENV_PY = TREE / "backend" / ".venv" / "bin" / "python"
#: U8-A 末 commit —— 旧版判据从这里取出，⛔ 不改工作树（禁 git stash / git checkout）。
OLD_REV = os.environ.get("MUTKILL_OLD_REV", "3f073a1a")

EXPECT_MSG = "不得再推进水位线"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    # ⛔ 先注册再 exec：Python 3.14 的 dataclass 自省取 `sys.modules[__module__]`，
    # 不注册的话动态加载的模块里一有 dataclass 就崩（MEMORY 有这条）。
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


GATE_SRC = '''\
import subprocess
import sys


def test_n1_premise_feeds_stderr():
    """HIGH-1 形态：前提断言把子进程 stderr 插进消息首行，目标断言根本没执行。"""
    r = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.stderr.write('不得再推进' + '水位线' + ' 尾巴\\\\n'); sys.exit(1)"],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[:250]
    assert False, "不得再推进水位线"


def test_n2_forged_summary_line():
    """HIGH-2 形态：captured 区伪造一行短摘要；真正的失败在别处、消息也不同。"""
    print("FAILED negctl_gate.py::test_n2_forged_summary_line - AssertionError: 不得再推进水位线")
    assert False, "真实拒因与期望消息无关"


def test_p1_target_really_red():
    """正控：目标断言**真的**红了，两版都必须判 KILLED。"""
    assert False, "不得再推进水位线（正控专用后缀，防指纹与 N1 撞车）"
'''


def run_gate(gate: Path, test: str, flags: list[str]) -> tuple[int, str]:
    env = {**os.environ, "COLUMNS": "1000", "PYTHONDONTWRITEBYTECODE": "1"}
    r = subprocess.run(
        [str(VENV_PY), "-m", "pytest", f"{gate.name}::{test}", *flags, "--rootdir", str(gate.parent)],
        cwd=str(gate.parent), capture_output=True, text=True, env=env, timeout=300,
    )
    return r.returncode, r.stdout + r.stderr


#: ⚠️ 故意**不带** `--show-capture=no`：负控要证的是解析器本身的收紧，喂给两版
#: 判据的必须是**含 captured 区**的那种输出（旧版的实际工作条件）。
#: `--show-capture=no` 是另一道独立防线，在 D 段单独对照。
OLD_FLAGS = ["-q", "-p", "no:cacheprovider", "--tb=line", "-rf"]


def nodeid_of(gate: Path, test: str, out: str) -> str:
    """pytest 报出来的 nodeid（相对 cwd），从摘要行实测取，不自己拼。"""
    m = re.search(rf"^FAILED (\S*{re.escape(gate.name)}::{re.escape(test)})", out, re.M)
    return m.group(1) if m else f"{gate.name}::{test}"


def target_assert_line(src_lines: list[str], func: str) -> int:
    """该测试函数里**最后一条** `assert` 的行号 = 目标断言。

    ⛔ 从门文件**源码**算，不从跑出来的结果回填 —— 回填的话期望值与被测量同源，
    N1 里「位置对不上」这个结论就不成立了（MEMORY: 期望值须独立来源）。
    """
    fn = next(i for i, l in enumerate(src_lines, 1) if l.startswith(f"def {func}("))
    nxt = next((i for i, l in enumerate(src_lines, 1) if i > fn and l.startswith("def ")), len(src_lines) + 1)
    return max(i for i, l in enumerate(src_lines, 1) if fn < i < nxt and l.startswith("    assert "))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="mutkill-negctl-")).resolve()
    bad = 0
    try:
        gate = tmp / "negctl_gate.py"
        gate.write_text(GATE_SRC, encoding="utf-8")
        old_dir = tmp / "old"
        old_dir.mkdir()

        old_path = old_dir / "mutation_kill_identity_old.py"
        blob = subprocess.run(
            ["git", "show", f"{OLD_REV}:backend/scripts/mutation_kill_identity.py"],
            cwd=str(TREE), capture_output=True, text=True, check=True,
        ).stdout
        old_path.write_text(blob, encoding="utf-8")
        old = _load("mutation_kill_identity_old", old_path)
        new = _load("mutation_kill_identity_new", NEW_MOD)

        print(f"旧版判据取自 {OLD_REV}:backend/scripts/mutation_kill_identity.py "
              f"({len(blob.splitlines())} 行) → {old_path}")
        print(f"新版判据 {NEW_MOD} ({len(NEW_MOD.read_text(encoding='utf-8').splitlines())} 行)")
        if old_path.read_bytes() == NEW_MOD.read_bytes():
            print("⛔ 验伪锚0 FAIL: 新旧判据逐字节相同 —— 「旧放行/新拒」会是拿同一份代码自证")
            return 1
        print("验伪锚0 新旧两份判据逐字节不同: PASS")
        print()

        src_lines = GATE_SRC.splitlines()
        cases = [
            # (名字, test 名, expect_msg, 取 expect_loc 的函数名 or None, 期望旧, 期望新)
            ("N1 前提断言喂饱 (Y1-B HIGH-1)", "test_n1_premise_feeds_stderr", EXPECT_MSG,
             "test_n1_premise_feeds_stderr", True, False),
            ("N2 captured 区伪摘要行 (Y1-B HIGH-2)", "test_n2_forged_summary_line", EXPECT_MSG,
             "test_n2_forged_summary_line", True, False),
            ("P1 目标断言真的红了 (正控)", "test_p1_target_really_red", EXPECT_MSG,
             "test_p1_target_really_red", True, True),
        ]

        for name, test, msg, loc_from, want_old, want_new in cases:
            rc, out = run_gate(gate, test, OLD_FLAGS)
            nodeid = nodeid_of(gate, test, out)
            expect_loc = None
            if loc_from:
                expect_loc = new.loc_token_for(gate, str(gate), target_assert_line(src_lines, loc_from))
            r_old = old.kill_identity_ok(rc, out, nodeid, msg)
            v_new, why = new.kill_identity(rc, out, nodeid, msg, gate_file=gate, expect_loc=expect_loc)
            r_new = v_new.startswith("KILLED")
            ok = (r_old == want_old) and (r_new == want_new)
            bad += 0 if ok else 1
            print(f"── {name}")
            print(f"   rc={rc} nodeid={nodeid}")
            print(f"   expect_msg={msg!r} expect_loc={expect_loc!r}")
            print(f"   旧版 kill_identity_ok = {r_old}   (期望 {want_old} = {'放行' if want_old else '拒'})")
            print(f"   新版 verdict          = {v_new} ⇒ {r_new}   (期望 {want_new})")
            print(f"   新版理由: {why}")
            print(f"   ⇒ {'PASS' if ok else '⛔FAIL'}")
            print()

        # ── D 段：`--show-capture=no` 这道**独立**防线的对照
        _, out_with = run_gate(gate, "test_n2_forged_summary_line", OLD_FLAGS)
        _, out_without = run_gate(gate, "test_n2_forged_summary_line", new.judge_flags())  # noqa: E501
        forged = "FAILED negctl_gate.py::test_n2_forged_summary_line - AssertionError: 不得再推进水位线"
        a, b = forged in out_with, forged in out_without
        ok_d = a and not b
        bad += 0 if ok_d else 1
        print("── D `--show-capture=no` 独立防线对照（与解析收紧分开算）")
        print(f"   不带该开关：伪造行出现在输出里 = {a}（= 旧版的实际工作条件，也是负控输入）")
        print(f"   带该开关  ：伪造行出现在输出里 = {b}（= judge_flags() 的默认）")
        print(f"   ⇒ {'PASS' if ok_d else '⛔FAIL'}")
        print()
        print(f"VERDICT: {'PASS' if bad == 0 else f'FAIL({bad})'}")
        return 0 if bad == 0 else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
