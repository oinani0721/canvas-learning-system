#!/usr/bin/env python3
"""CARD-G2-7a-TAIL 补充探针: 形态门对 FIFO 之外的其它非普通文件是否也归 unreadable ⇒ rc=2。

用法: python3 probe_special_kinds.py <repo_root> [timeout_seconds]

每种形态各建一个最小 vault, 把 .obsidian/hotkeys.json 换成该形态, 跑一次 verify,
记退出码 + 报告里 hotkeys 的归桶与 note。全程 subprocess + timeout=, 任何一种若挂住
都会以 TimeoutExpired 显形, 不会卡住探针本身。
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile


def _vault_with(kind: str, tmp: str) -> tuple[str, object]:
    """建一个只有 .obsidian/hotkeys.json 的最小 vault, 该项形态由 kind 决定。"""
    obs = os.path.join(tmp, ".obsidian")
    os.makedirs(obs, exist_ok=True)
    target = os.path.join(obs, "hotkeys.json")
    keep = None
    if kind == "regular":
        with open(target, "w", encoding="utf-8") as fh:
            fh.write("{}\n")
    elif kind == "fifo":
        os.mkfifo(target)
    elif kind == "dir":
        os.makedirs(target)
    elif kind == "symlink-to-chardev":
        os.symlink("/dev/null", target)
    elif kind == "symlink-to-fifo":
        real = os.path.join(tmp, "real.fifo")
        os.mkfifo(real)
        os.symlink(real, target)
    elif kind == "unix-socket":
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(target)
        keep = srv  # 保持存活, 否则 GC 可能提前收掉
    elif kind == "dangling-symlink":
        os.symlink(os.path.join(tmp, "nowhere"), target)
    else:
        raise ValueError(kind)
    return target, keep


def main() -> int:
    repo = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    verifier = os.path.join(repo, "scripts", "verify_vault_install.py")
    manifest = os.path.join(repo, "scripts", "vault-install-manifest.json")
    kinds = [
        "regular",
        "fifo",
        "dir",
        "symlink-to-chardev",
        "symlink-to-fifo",
        "unix-socket",
        "dangling-symlink",
    ]
    rows = []
    for kind in kinds:
        tmp = tempfile.mkdtemp(prefix=f"g27a-kind-{kind}-")
        out_dir = tempfile.mkdtemp(prefix="g27a-kind-out-")
        target = None
        keep = None
        try:
            target, keep = _vault_with(kind, tmp)
            report_txt = os.path.join(out_dir, "report.txt")
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
            try:
                done = subprocess.run(argv, capture_output=True, timeout=budget)
                rc = done.returncode
                err = done.stderr.decode("utf-8", "replace").strip()
            except subprocess.TimeoutExpired:
                rows.append((kind, "TimeoutExpired", "挂住了", "-"))
                continue
            note = "(报告没落盘)"
            bucket = "(报告没落盘)"
            if os.path.exists(report_txt):
                with open(report_txt, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                inside = False
                hits = []
                for line in text.splitlines():
                    if line.startswith("hotkeys "):
                        note = line.split(":", 1)[1].strip()
                    if line.startswith("## "):
                        inside = line.strip() == "## unreadable"
                        continue
                    if inside and line.strip().startswith(".obsidian/hotkeys.json"):
                        hits.append(line.strip())
                bucket = hits[0] if hits else "(不在 unreadable 段)"
            rows.append((kind, str(rc), note, bucket if not err else f"{bucket} | stderr={err[:120]}"))
        finally:
            if keep is not None:
                keep.close()
            if target and os.path.lexists(target) and not os.path.isdir(target):
                os.remove(target)
            shutil.rmtree(tmp, ignore_errors=True)
            shutil.rmtree(out_dir, ignore_errors=True)

    print(f"{'形态':<22} {'rc':<16} {'hotkeys note':<34} unreadable 明细")
    print("-" * 140)
    for kind, rc, note, bucket in rows:
        print(f"{kind:<22} {rc:<16} {note:<34} {bucket}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
