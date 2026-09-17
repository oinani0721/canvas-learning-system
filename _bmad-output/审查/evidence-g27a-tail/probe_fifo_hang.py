#!/usr/bin/env python3
"""CARD-G2-7a-TAIL 承重探针: hotkeys.json 是**无写端 FIFO** 时 verify 会不会挂在打开阶段。

用法: python3 probe_fifo_hang.py <repo_root> [timeout_seconds]

两段，都不依赖 `timeout` CLI（macOS 没有这个命令）:
  A. `subprocess.run(..., timeout=N)`
       改前期望: 抛 TimeoutExpired（阻塞 open 永远不返回，外层 except 到不了）。
       改后期望: 正常返回 rc=2（mismatch），报告里 hotkeys 归 unreadable。
  B. `-X faulthandler` + 超时后 SIGABRT
       让子进程自报栈，把「挂在哪一行」钉死，而不是只知道「某处挂了」。
       改前期望: 栈顶在 verify_vault_install.py 的 _check_hotkeys 读 hotkeys 那一行。
       改后期望: B 段根本等不到超时（进程早已正常退出），打印 "no-hang"。

清理: FIFO 与临时目录在 finally 里无条件删，防后面别的读者被同一个 FIFO 挂住。
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import tempfile


def _build_fifo_vault(tmp: str) -> str:
    """最小 target vault: 只有 .obsidian/hotkeys.json，且它是无写端 FIFO。"""
    obs = os.path.join(tmp, ".obsidian")
    os.makedirs(obs, exist_ok=True)
    fifo = os.path.join(obs, "hotkeys.json")
    os.mkfifo(fifo)
    return fifo


def main() -> int:
    repo = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    verifier = os.path.join(repo, "scripts", "verify_vault_install.py")
    manifest = os.path.join(repo, "scripts", "vault-install-manifest.json")
    report_txt = None
    tmp = tempfile.mkdtemp(prefix="g27a-tail-fifo-")
    # ⚠️ 报告落点必须在 --vault 树**外**: verify 的 _check_report_location 按文件系统
    #    身份(st_dev/st_ino)判定, 落在被审树内直接 rc=3(用法错), 探针就跑不到 hotkeys。
    out_dir = tempfile.mkdtemp(prefix="g27a-tail-out-")
    fifo = None
    try:
        fifo = _build_fifo_vault(tmp)
        report_txt = os.path.join(out_dir, "report.txt")
        st = os.lstat(fifo)
        import stat as _stat

        print(f"[setup] repo      = {repo}")
        print(f"[setup] vault     = {tmp}")
        print(f"[setup] hotkeys   = {fifo}")
        print(f"[setup] S_ISFIFO  = {_stat.S_ISFIFO(st.st_mode)}  (无写端)")
        print(f"[setup] timeout   = {budget}s")
        argv = [
            sys.executable,
            verifier,
            "--vault",
            tmp,
            "--manifest",
            manifest,
            "--report",
            report_txt,
        ]
        print(f"[setup] argv      = {argv}")

        print("\n=== A 段: subprocess.run(timeout=%ds) ===" % budget)
        verdict_a = ""
        try:
            done = subprocess.run(argv, capture_output=True, timeout=budget)
            verdict_a = f"returned rc={done.returncode}"
            print(f"[A] {verdict_a}  (没有挂起)")
            stdout_text = done.stdout.decode("utf-8", "replace")
            print("[A] --- stdout 全文 ---")
            print(stdout_text)
            if done.stderr:
                print("[A] --- stderr ---")
                print(done.stderr.decode("utf-8", "replace"))
            if os.path.exists(report_txt):
                print("[A] --- --report 落盘全文 ---")
                with open(report_txt, encoding="utf-8", errors="replace") as fh:
                    print(fh.read())
            else:
                print("[A] --report 没落盘")
        except subprocess.TimeoutExpired:
            verdict_a = "TimeoutExpired"
            print(f"[A] {verdict_a}  <<< 挂住了: {budget}s 内没有返回，阻塞 open 的直接证据")

        print("\n=== B 段: -X faulthandler + 超时 SIGABRT 定位挂点 ===")
        if verdict_a != "TimeoutExpired":
            print("[B] no-hang: A 段已正常返回，无挂点可定位，跳过 SIGABRT")
        else:
            proc = subprocess.Popen(
                [sys.executable, "-X", "faulthandler", *argv[1:]],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                proc.communicate(timeout=budget)
                print("[B] 子进程自己返回了，无挂点")
            except subprocess.TimeoutExpired:
                proc.send_signal(signal.SIGABRT)
                _o, err = proc.communicate(timeout=30)
                print(f"[B] SIGABRT 后子进程退出码 = {proc.returncode}")
                print("[B] --- faulthandler 自报栈 ---")
                print((err or b"").decode("utf-8", "replace"))
        return 0
    finally:
        if fifo and os.path.exists(fifo):
            os.remove(fifo)
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)
        print(f"[cleanup] FIFO 与临时目录已删: {tmp} 存在={os.path.exists(tmp)}; 报告目录 {out_dir} 存在={os.path.exists(out_dir)}")


if __name__ == "__main__":
    raise SystemExit(main())
