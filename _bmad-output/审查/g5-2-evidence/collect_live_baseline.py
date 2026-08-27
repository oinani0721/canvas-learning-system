#!/usr/bin/env python3
"""G5-2 — live vault 零修改基线采集器 v2 (Codex 二轮 HIGH-4 加固)。

对 live vault **全部** 324 个文件采集: relpath / 类型 / size / mtime_ns / ctime_ns /
mode / nlink / sha256(全部常规文件, 不再限 md-yaml-json) / symlink 目标 / 目录集合。
输出确定性排序的 TSV — before/after 逐字节 diff 为空 = 所记录投影零净差异。

如实声明的判定边界 (不掩饰):
  - atime 不采集不断言 (只读扫描本身在 atime/relatime 挂载上会更新访问时间);
  - before/after 快照无法排除窗口内「先改后恢复」— 该口径是净差异证明, 非全程监控;
  - xattr/ACL/owner 未采集 (本仓判定面为内容与结构, 不含权限元数据)。

用法: python3 collect_live_baseline.py <vault_path> > baseline.tsv
"""

from __future__ import annotations

import hashlib
import os
import stat as stat_mod
import sys
from pathlib import Path


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    rows: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        dp = Path(dirpath)
        for d in dirnames:
            p = dp / d
            st = p.lstat()
            if stat_mod.S_ISLNK(st.st_mode):
                # 目录 symlink 按 L 记录并带 target (retarget 可见); walk 不跟随
                rows.append(
                    f"L\t{p.relative_to(root)}\ttarget={os.readlink(p)}\tmode={oct(st.st_mode)}"
                )
                continue
            rows.append(f"D\t{p.relative_to(root)}\tmode={oct(st.st_mode)}")
        for f in sorted(filenames):
            p = dp / f
            st = p.lstat()
            rel = p.relative_to(root)
            if stat_mod.S_ISLNK(st.st_mode):
                rows.append(
                    f"L\t{rel}\ttarget={os.readlink(p)}\tmode={oct(st.st_mode)}"
                )
                continue
            sha = hashlib.sha256(p.read_bytes()).hexdigest()
            rows.append(
                f"F\t{rel}\tsha256={sha}\tsize={st.st_size}\tmtime_ns={st.st_mtime_ns}"
                f"\tctime_ns={st.st_ctime_ns}\tmode={oct(st.st_mode)}\tnlink={st.st_nlink}"
            )
    for row in sorted(rows):
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
