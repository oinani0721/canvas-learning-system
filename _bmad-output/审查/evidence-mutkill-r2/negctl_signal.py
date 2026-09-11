#!/usr/bin/env python3
"""(h) 信号负控：还原循环中途收到 SIGTERM，全部目标文件仍逐字节还原。

⛔ 只对**本脚本自己造的临时目标文件**发信号打断，绝不对真的 `canvas-vault/**`
做这件事（卡文 (h) 明文）。

对照两跑（只有「新版全还原」一跑的话，「它做对了」与「它根本没被打断」不可区分）：
  · `naive`   —— 复刻 g32b / g32cb / g32ccr1 收口**前**的写法：handler 把信号转成
    异常让 `finally` 跑。信号落在**还原循环内部**时，异常从 finally 里逃出去 ⇒
    剩下的文件**还留着变异体**（部分还原）。
  · `guarded` —— `RestoreGuard.critical()`：还原期收到的信号只记待办、不打断，
    循环跑完再兑现 ⇒ 全部还原，rc=130。

判据：naive **必须**留下残留（否则这条负控不承重、证明不了 guarded 的价值），
guarded **必须**零残留且 rc=130。
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TREE = Path(__file__).resolve().parents[3]
VENV_PY = TREE / "backend" / ".venv" / "bin" / "python"
SCRIPTS = TREE / "backend" / "scripts"

N_TARGETS = 5
BREAK_AT = 2  # 还原到第 3 个文件之前发信号

CHILD = '''\
import os
import signal
import sys
from pathlib import Path

sys.path.insert(0, {scripts!r})
from mutation_kill_identity import RestoreGuard

MODE = sys.argv[1]
DIR = Path(sys.argv[2])
N = {n}
BREAK_AT = {brk}

targets = [DIR / f"target_{{i}}.txt" for i in range(N)]
originals = {{p: p.read_bytes() for p in targets}}
_fired = []


class _Terminated(Exception):
    pass


def restore_loop():
    for i, p in enumerate(targets):
        if i == BREAK_AT and not _fired:
            # 还原到一半时把信号发给自己 —— 这就是 (h) 要防的那一刻。
            # ⚠️ 只发一次：真实形态是「一个信号在还原期到达」。每轮都发的话，
            # 量到的是「反复被 kill」这个别的东西（首版就是这么把 guard 打成递归的）。
            _fired.append(1)
            os.kill(os.getpid(), signal.SIGTERM)
        p.write_bytes(originals[p])


if MODE == "naive":
    # 收口前的写法：handler 抛异常，指望 finally 把还原跑完
    def _handler(signum, _frame):
        raise _Terminated(f"收到信号 {{signum}}")

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, _handler)
    try:
        for p in targets:
            p.write_bytes(b"MUT" + b"ANT-body\\n")
        try:
            pass  # 这里本该是「跑门」
        finally:
            restore_loop()
    except _Terminated as exc:
        print(f"naive: {{exc}} —— 异常从 finally 里逃出去了", flush=True)
        sys.exit(130)
    sys.exit(0)

# 收口后的写法
def restore_all():
    with guard.critical():
        restore_loop()


guard = RestoreGuard(restore_all)
guard.install()
try:
    for p in targets:
        p.write_bytes(b"MUT" + b"ANT-body\\n")
finally:
    restore_all()
sys.exit(0)
'''


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(mode: str) -> tuple[int, dict[str, str], dict[str, str]]:
    d = Path(tempfile.mkdtemp(prefix=f"mutkill-sig-{mode}-")).resolve()
    try:
        for i in range(N_TARGETS):
            (d / f"target_{i}.txt").write_text(f"original body {i}\n", encoding="utf-8")
        before = {p.name: sha(p) for p in sorted(d.glob("target_*.txt"))}
        child = d / "child.py"
        child.write_text(CHILD.format(scripts=str(SCRIPTS), n=N_TARGETS, brk=BREAK_AT), encoding="utf-8")
        r = subprocess.run(
            [str(VENV_PY), str(child), mode, str(d)],
            capture_output=True, text=True, timeout=120,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        after = {p.name: sha(p) for p in sorted(d.glob("target_*.txt"))}
        print(f"   子进程 rc={r.returncode}")
        for ln in (r.stdout + r.stderr).strip().splitlines():
            print(f"   | {ln}")
        return r.returncode, before, after
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main() -> int:
    bad = 0
    print("── naive（收口前写法：handler 抛异常让 finally 跑）——**必须**留下残留")
    rc_n, b_n, a_n = run("naive")
    drift_n = [k for k in b_n if b_n[k] != a_n[k]]
    ok_n = len(drift_n) > 0
    bad += 0 if ok_n else 1
    print(f"   未还原的文件: {drift_n or '∅'}  ⇒ {'PASS（负控承重）' if ok_n else '⛔FAIL（负控不承重，下面那跑证明不了什么）'}")
    print()

    print("── guarded（RestoreGuard.critical：还原期不可打断）——**必须**零残留 + rc=130")
    rc_g, b_g, a_g = run("guarded")
    drift_g = [k for k in b_g if b_g[k] != a_g[k]]
    ok_g = (not drift_g) and rc_g == 130
    bad += 0 if ok_g else 1
    print(f"   未还原的文件: {drift_g or '∅'}   rc={rc_g}（期望 130）")
    print(f"   ⇒ {'PASS' if ok_g else '⛔FAIL'}")
    print()

    print("── 覆盖面自证：RestoreGuard 挂了哪些信号（SIGQUIT 是收口前三套漏掉的那个）")
    out = subprocess.run(
        [str(VENV_PY), "-c",
         f"import sys; sys.path.insert(0, {str(SCRIPTS)!r});"
         "from mutation_kill_identity import RESTORE_SIGNALS;"
         "print([s.name for s in RESTORE_SIGNALS])"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    print(f"   {out}")
    ok_s = "SIGQUIT" in out
    bad += 0 if ok_s else 1
    print(f"   ⇒ {'PASS' if ok_s else '⛔FAIL（SIGQUIT 缺席）'}")
    print()
    print(f"VERDICT: {'PASS' if bad == 0 else f'FAIL({bad})'}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
