#!/usr/bin/env python3
"""live fixture 的**显式**刷新脚本 (CARD-维护B-R4 卡文 (b) / 默认裁决 D3)。

## 为什么需要它

`test_live_fixtures_are_byte_identical_to_source` 原先直接读**硬编码的现网绝对
路径**（`/Users/Heishing/.../canvas-vault/outputs`）来证明 fixture 是真报告的
逐字节拷贝。那道门有两个问题：

1. **不可移植** —— 换机器/CI 上只能 skip，于是"诚实性"在最需要它的地方缺席；
2. **它把 live vault 变成测试的隐式输入** —— live 一改，门就红/绿翻转，
   而改 live 的人根本不知道自己动了一道测试门。

⇒ 改成「快照 + 显式刷新」：门只比 fixture 与 `MANIFEST.sha256`；要更新 fixture
必须**有人主动跑这个脚本**，刷新这件事因此变成一次可见的、进 git 的动作。

## ⚠️ 诚实登记：这是一次**诚实性降级**，不是升级

改造前，门证明的是「fixture == 此刻 live 原件」。
改造后，门证明的是「fixture == 录入时的快照」。
**「录入时快照真的来自 live」这一点，此后由 git 历史与本脚本的存在性背书，
不再由每次跑测试来证明。** 这是卡文 D3 明确接受的取舍，不掩饰。

## 用法

    python refresh_from_live.py            # 只对账, 不写 (默认 dry-run)
    python refresh_from_live.py --apply    # 从 live 拷贝并重写 MANIFEST.sha256

⛔ live vault 只读：本脚本**只从 live 读**，从不写 live（G8-7 冻结）。
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "MANIFEST.sha256"
LIVE_DIR = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/outputs")
# 录入时选定的 8 个文件（4 报告 + 4 scan JSON）。新增 fixture 必须显式列进来
# ——用 `iterdir()` 自动发现会让"少拷了一份"表现为门变松而不是变红。
FIXTURE_NAMES = (
    "回顾-CS 61B-2026-08-27.md",
    "回顾-CS188 lecture 2-2026-08-27.md",
    "回顾-特征值与特征向量-2026-08-27.md",
    "回顾-递归与分治 (Recursion & Divide-Conquer)-2026-08-27.md",
    ".recap-scan-CS 61B.json",
    ".recap-scan-CS188 lecture 2.json",
    ".recap-scan-特征值与特征向量.json",
    ".recap-scan-递归与分治 (Recursion & Divide-Conquer).json",
)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_manifest() -> dict[str, str]:
    if not MANIFEST.is_file():
        return {}
    out: dict[str, str] = {}
    for ln in MANIFEST.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        digest, _, name = ln.partition("  ")
        out[name] = digest
    return out


def write_manifest(rows: dict[str, str]) -> None:
    body = [
        "# live fixture 快照清单 —— 由 refresh_from_live.py --apply 生成。",
        "# 每行: <sha256>  <文件名>。手改本文件 = 让诚实性门失去意义。",
    ]
    body += [f"{rows[n]}  {n}" for n in FIXTURE_NAMES]
    MANIFEST.write_text("\n".join(body) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="真的从 live 拷贝并重写清单")
    args = ap.parse_args()

    if not LIVE_DIR.is_dir():
        print(f"⛔ live vault 不在本机此路径, 无法刷新: {LIVE_DIR}")
        return 2

    missing = [n for n in FIXTURE_NAMES if not (LIVE_DIR / n).is_file()]
    if missing:
        print("⛔ live 侧缺少这些原件, 拒绝刷新 (不生成半份快照):")
        for n in missing:
            print(f"   · {n}")
        return 2

    live_hashes = {n: sha256(LIVE_DIR / n) for n in FIXTURE_NAMES}
    drift = [n for n in FIXTURE_NAMES if not (HERE / n).is_file() or sha256(HERE / n) != live_hashes[n]]

    if not args.apply:
        if drift:
            print("以下 fixture 与当前 live 原件不同 (dry-run, 未写任何文件):")
            for n in drift:
                print(f"   · {n}")
            print("\n确认要采纳 live 现状为新快照, 再跑: --apply")
        else:
            print(f"✅ {len(FIXTURE_NAMES)} 份 fixture 与当前 live 原件逐字节相同。")
        stale = read_manifest() != live_hashes
        print(f"MANIFEST 是否需要重写: {'是' if stale or drift else '否'}")
        return 0

    for n in FIXTURE_NAMES:
        shutil.copy2(LIVE_DIR / n, HERE / n)
    write_manifest(live_hashes)
    print(f"✅ 已从 live 刷新 {len(FIXTURE_NAMES)} 份 fixture 并重写 MANIFEST.sha256")
    print("   ⛔ 记得把 fixture 与 MANIFEST 的改动一起 commit —— 刷新必须留痕。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
