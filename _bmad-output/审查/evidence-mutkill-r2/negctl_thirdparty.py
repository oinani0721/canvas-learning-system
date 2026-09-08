#!/usr/bin/env python3
"""负控 N3/N4：信号路径与 `finally` 路径共用同一份「第三方改动存证」比对。

⛔ 这条交互在收口自证里**整个漏掉了**：`negctl_signal.py` 用的是它自己造的
`restore_all`，压根不经过 g32b 的第三方存证那一层，所以「先还原再退出」把那道判据
变成恒真这件事，四道裁判全绿也照不出来（独立复核 2026-09-08 抓到，并用本卡自己的
probe 存档坐实：两份新 `.bak` 里变异标记计数 = 0 ⇒ 存证的是脚本自己的快照）。

矩阵（每条都跑**新旧两版**，只有对照留下差别才说明修复承重）：
  N3 无第三方改动：信号路径先还原 → `finally` 再调一次
     · 旧版：`finally` 读到的已是原文，与「写进去的变异体」不等 ⇒ **伪告警 + 伪存证**
     · 新版：表已清空 ⇒ no-op，无告警无存证
  N4 有第三方改动 T：
     · 旧版：guard 先用原文覆盖 T ⇒ **T 既没被存证也没被保留**，存下来的是原文
     · 新版：比对在第一个碰文件的人那里做 ⇒ 存证内容**逐字节等于 T**
  P2 正控：只走 `finally`（不发信号）时，新版仍能存证真实的 T（不能只在信号路径上对）

⛔ 只在 `tempfile.mkdtemp()` 造的文件上做，不碰任何生产文件。
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import pathlib
import shutil
import sys
import tempfile

TREE = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = TREE / "backend" / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location("g32b_under_test", SCRIPTS / "g32b_mutation_gates.py")
g32b = importlib.util.module_from_spec(spec)
sys.modules["g32b_under_test"] = g32b
spec.loader.exec_module(g32b)

ORIG = b"original body\n"
MUT = b"MUT" + b"ANT body\n"
THIRD = b"third party edit\n"


def _stash_for(tag: str, name: str) -> pathlib.Path:
    return pathlib.Path(f"/private/tmp/g32b-mutation-thirdparty-{tag}-{name}.bak")


# ── 旧实现（收口前形态）：guard 只还原不比对；比对留在 finally 的 _restore_one ──
def old_guard_restore(snapshot: dict) -> None:
    for p, orig in list(snapshot.items()):
        p.write_bytes(orig)
    snapshot.clear()


def old_restore_one(tag, mutated, originals) -> None:
    for p, written in mutated.items():
        now = p.read_bytes()
        if now != written:
            st = _stash_for(tag, p.name)
            st.write_bytes(now)
            print(f"[{tag}] ⚠️ 变异窗口内 {p.name} 被第三方改动 — 其内容已存证到 {st}")
        p.write_bytes(originals[p])


def run_old(tag: str, third_party: bool, signal_first: bool):
    d = pathlib.Path(tempfile.mkdtemp(prefix="mkr2-tp-old-")).resolve()
    try:
        f = d / "target.txt"
        f.write_bytes(ORIG)
        snapshot = {f: ORIG}
        f.write_bytes(MUT)
        if third_party:
            f.write_bytes(THIRD)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            if signal_first:
                old_guard_restore(snapshot)          # 信号路径：先还原
            old_restore_one(tag, {f: MUT}, {f: ORIG})  # finally 路径
        st = _stash_for(tag, "target.txt")
        return {
            "warned": "被第三方改动" in buf.getvalue(),
            "stash_exists": st.exists(),
            "stash_bytes": st.read_bytes() if st.exists() else None,
            "final": f.read_bytes(),
        }
    finally:
        shutil.rmtree(d, ignore_errors=True)
        _stash_for(tag, "target.txt").unlink(missing_ok=True)


def run_new(tag: str, third_party: bool, signal_first: bool):
    d = pathlib.Path(tempfile.mkdtemp(prefix="mkr2-tp-new-")).resolve()
    try:
        f = d / "target.txt"
        f.write_bytes(ORIG)
        g32b._ACTIVE_SNAPSHOT.clear()
        g32b._arm_mutation(tag, {f: (ORIG, MUT)})
        if third_party:
            f.write_bytes(THIRD)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            if signal_first:
                g32b._restore_active()   # 信号路径
            g32b._restore_active()       # finally 路径（同一个函数）
        st = _stash_for(tag, "target.txt")
        return {
            "warned": "被第三方改动" in buf.getvalue(),
            "stash_exists": st.exists(),
            "stash_bytes": st.read_bytes() if st.exists() else None,
            "final": f.read_bytes(),
        }
    finally:
        g32b._ACTIVE_SNAPSHOT.clear()
        shutil.rmtree(d, ignore_errors=True)
        _stash_for(tag, "target.txt").unlink(missing_ok=True)


def show(name, r):
    b = r["stash_bytes"]
    who = "—" if b is None else ("原文(伪存证)" if b == ORIG else ("第三方 T" if b == THIRD else "变异体"))
    print(f"    {name:6} 告警={str(r['warned']):5} 存证={str(r['stash_exists']):5} 存证内容={who:12} 还原后={'原文' if r['final'] == ORIG else '⛔ 不是原文'}")


def run_arm_window(tag: str):
    """#41：`_arm_mutation` 的写盘循环被信号打断（登记了快照、文件还没写）。

    旧逻辑（比对 `now != _written` 即告警）会把「还没写的文件」误报成第三方改动并
    存证一份**其实是原文**的伪 `.bak`；新逻辑 `now == _orig → continue` 静默跳过。
    """
    d = pathlib.Path(tempfile.mkdtemp(prefix="mkr2-tp-arm-")).resolve()
    try:
        f = d / "target.txt"
        f.write_bytes(ORIG)
        g32b._ACTIVE_SNAPSHOT.clear()
        # 手工复现「登记了但还没写」：直接把 (ORIG, MUT) 放进快照而不落盘
        g32b._ACTIVE_TAG[0] = tag
        g32b._ACTIVE_SNAPSHOT[f] = (ORIG, MUT)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            g32b._restore_active()
        st = _stash_for(tag, "target.txt")
        return {
            "warned": "被第三方改动" in buf.getvalue(),
            "stash_exists": st.exists(),
            "final": f.read_bytes(),
        }
    finally:
        g32b._ACTIVE_SNAPSHOT.clear()
        shutil.rmtree(d, ignore_errors=True)
        _stash_for(tag, "target.txt").unlink(missing_ok=True)


def main() -> int:
    bad = 0
    print("── N3 无第三方改动 · 信号路径先还原 → finally 再调一次 ──")
    o = run_old("N3old", third_party=False, signal_first=True)
    n = run_new("N3new", third_party=False, signal_first=True)
    show("旧版", o); show("新版", n)
    ok = o["warned"] and o["stash_bytes"] == ORIG and (not n["warned"]) and (not n["stash_exists"])
    bad += 0 if ok else 1
    print(f"    ⇒ {'PASS（旧版伪告警+伪存证；新版静默 no-op）' if ok else '⛔FAIL'}")

    print("── N4 有第三方改动 T · 信号路径先还原 → finally 再调一次 ──")
    o = run_old("N4old", third_party=True, signal_first=True)
    n = run_new("N4new", third_party=True, signal_first=True)
    show("旧版", o); show("新版", n)
    ok = (o["stash_bytes"] == ORIG) and (n["stash_bytes"] == THIRD) and n["warned"]
    bad += 0 if ok else 1
    print(f"    ⇒ {'PASS（旧版把 T 覆盖掉、存下的是原文；新版存下 T 本身）' if ok else '⛔FAIL'}")

    print("── P2 正控 · 不发信号，只走 finally；新版仍须存证真实的 T ──")
    n = run_new("P2new", third_party=True, signal_first=False)
    show("新版", n)
    ok = n["warned"] and n["stash_bytes"] == THIRD and n["final"] == ORIG
    bad += 0 if ok else 1
    print(f"    ⇒ {'PASS（不是只在信号路径上对）' if ok else '⛔FAIL'}")

    print("── N5 `_arm_mutation` 写盘窗口被打断 · 登记了快照但文件还没写 ──")
    r = run_arm_window("N5new")
    print(f"    告警={str(r['warned']):5} 存证={str(r['stash_exists']):5} 还原后={'原文' if r['final'] == ORIG else '⛔ 非原文'}")
    ok = (not r["warned"]) and (not r["stash_exists"]) and r["final"] == ORIG
    bad += 0 if ok else 1
    print(f"    ⇒ {'PASS（未写的文件不被误报; 旧逻辑这里会存证一份原文的伪 .bak）' if ok else '⛔FAIL'}")

    print("── 验伪锚 · 新旧两份实现必须真的不同（否则上面是拿同一份代码自证）──")
    same = (g32b._restore_active.__code__.co_code == old_restore_one.__code__.co_code)
    bad += 1 if same else 0
    print(f"    两份实现字节码相同={same}  ⇒ {'⛔FAIL' if same else 'PASS'}")

    print(f"VERDICT: {'PASS' if bad == 0 else f'FAIL({bad})'}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
