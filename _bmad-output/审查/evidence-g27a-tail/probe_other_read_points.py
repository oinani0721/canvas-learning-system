#!/usr/bin/env python3
"""CARD-G2-7a-TAIL 补充探针: 除 hotkeys 外, 还有没有别的读点会在 FIFO 上阻塞 open。

用法: python3 probe_other_read_points.py <repo_root> [timeout_seconds]

覆盖 Codex 问题④ 点名的路径:
  A. main.js 侧      —— 目标 vault 的 .obsidian/plugins/<id>/main.js 换成无写端 FIFO
  B. copy 件, 无 --source —— 某个 copy 项换成无写端 FIFO(只走 missing/extra 分类)
  C. copy 件, 有 --source —— 同上但给 --source(会走 content-drift 的读取/摘要路径)
  D. 源侧 copy 件      —— --source 那一侧的同名项是无写端 FIFO

每格都 subprocess + timeout=, 挂住就以 TimeoutExpired 显形。本探针**只观测, 不修**。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

MAIN_JS_REL = ".obsidian/plugins/canvas-learning-system/main.js"
COPY_REL = ".obsidian/community-plugins.json"


def _mk(root: str, rel: str, *, fifo: bool, body: str = "{}\n") -> str:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if fifo:
        os.mkfifo(path)
    else:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)
    return path


def _run(verifier, manifest, vault, budget, source=None):
    out_dir = tempfile.mkdtemp(prefix="g27a-orp-out-")
    report = os.path.join(out_dir, "report.txt")
    argv = [sys.executable, verifier, "--vault", vault, "--manifest", manifest, "--report", report]
    if source:
        argv += ["--source", source]
    try:
        done = subprocess.run(argv, capture_output=True, timeout=budget)
        text = ""
        if os.path.exists(report):
            with open(report, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        return str(done.returncode), text
    except subprocess.TimeoutExpired:
        return "TimeoutExpired", ""
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


def _line(text, prefix):
    for ln in text.splitlines():
        if ln.startswith(prefix):
            return ln.strip()
    return "(无该行)"


def main() -> int:
    repo = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    verifier = os.path.join(repo, "scripts", "verify_vault_install.py")
    manifest = os.path.join(repo, "scripts", "vault-install-manifest.json")
    with open(manifest, encoding="utf-8") as fh:
        items = {i["path"] for i in json.load(fh)["items"]}
    print(f"[前提] {COPY_REL} 在清单内: {COPY_REL in items}")
    print(f"[前提] {MAIN_JS_REL} 在清单内: {MAIN_JS_REL in items}")
    print()

    rows = []
    made = []
    try:
        # A. main.js 是无写端 FIFO(hotkeys 是正常文件, 确保能走到 main.js 那一段)
        va = tempfile.mkdtemp(prefix="g27a-orp-A-")
        made.append(va)
        _mk(va, ".obsidian/hotkeys.json", fifo=False)
        _mk(va, MAIN_JS_REL, fifo=True)
        rc, txt = _run(verifier, manifest, va, budget)
        rows.append(("A main.js=FIFO", rc, _line(txt, "hotkeys "), _line(txt, "unreadable ")))

        # B. copy 件是无写端 FIFO, 不给 --source
        vb = tempfile.mkdtemp(prefix="g27a-orp-B-")
        made.append(vb)
        _mk(vb, ".obsidian/hotkeys.json", fifo=False)
        _mk(vb, COPY_REL, fifo=True)
        rc, txt = _run(verifier, manifest, vb, budget)
        rows.append(("B copy件=FIFO 无source", rc, _line(txt, "content-drift"), _line(txt, "unreadable ")))

        # C. 同 B, 但给 --source(走 content-drift 读取/摘要路径)
        src = tempfile.mkdtemp(prefix="g27a-orp-src-")
        made.append(src)
        _mk(src, ".obsidian/hotkeys.json", fifo=False)
        _mk(src, COPY_REL, fifo=False, body='["x"]\n')
        rc, txt = _run(verifier, manifest, vb, budget, source=src)
        rows.append(("C copy件=FIFO 有source", rc, _line(txt, "content-drift"), _line(txt, "unreadable ")))

        # D. 源侧那一份是无写端 FIFO, 目标侧是正常文件
        vd = tempfile.mkdtemp(prefix="g27a-orp-D-")
        srcd = tempfile.mkdtemp(prefix="g27a-orp-srcD-")
        made += [vd, srcd]
        _mk(vd, ".obsidian/hotkeys.json", fifo=False)
        _mk(vd, COPY_REL, fifo=False, body='["x"]\n')
        _mk(srcd, ".obsidian/hotkeys.json", fifo=False)
        _mk(srcd, COPY_REL, fifo=True)
        rc, txt = _run(verifier, manifest, vd, budget, source=srcd)
        rows.append(("D 源侧copy件=FIFO", rc, _line(txt, "content-drift"), _line(txt, "unreadable ")))
    finally:
        for d in made:
            for base, _dirs, files in os.walk(d):
                for f in files:
                    fp = os.path.join(base, f)
                    try:
                        if os.path.exists(fp) and os.path.stat and os.path.islink(fp) is False:
                            import stat as _s

                            if _s.S_ISFIFO(os.lstat(fp).st_mode):
                                os.remove(fp)
                    except OSError:
                        pass
            shutil.rmtree(d, ignore_errors=True)

    print(f"{'场景':<26} {'rc':<16} {'相关汇总行':<52} unreadable 计数行")
    print("-" * 150)
    for name, rc, a, b in rows:
        print(f"{name:<26} {rc:<16} {a:<52} {b}")
    print()
    hung = [r[0] for r in rows if r[1] == "TimeoutExpired"]
    print("挂住的场景:", hung if hung else "无（四格都在超时预算内返回）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
