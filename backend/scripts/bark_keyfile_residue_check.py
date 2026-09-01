#!/usr/bin/env python3
"""(c) 门: 冷启动 + teardown 之后 send_bark.KEY_FILE 不得残留失效临时路径。

判据必须在 fixture teardown **之后**看, 所以不能写成一条 pytest 测试 ——
本脚本在一个全新解释器里:
  1. 先确认 send_bark 尚未加载 (冷启动前提, 否则整条判据空转);
  2. 在进程内跑 `bark_coldstart_probe::test_coldstart_keyfile_redirected`
     (该探针模块顶层不 import scripts, 守卫那次 import 才是本进程首次加载);
  3. 该跑必须绿 —— 绿了才证明冷启动分支真的被走到;
  4. 然后直接读 sys.modules["send_bark"].KEY_FILE, 要求它等于本进程的真实
     默认值, 且不带守卫 tmp 目录痕迹、不指向已消失的目录。

背景 (为什么这道门不是多余的): round-3 提的「冷启动残留」在第八批被改成
「先手动复位真实默认再打桩」, 但复位值是在 `patcher.setenv("BARK_KEY_FILE",
tmp)` **之后**读 `os.environ["BARK_KEY_FILE"]` 拿的 —— 读到的就是 tmp 路径
本身, 复位退化成原地赋值, MonkeyPatch 记下的「原值」仍是 tmp。形态对、语义
空转, 而当时没有任何门能发现。本脚本就是那道门。

全程只比较路径字符串, 从不读取真实 key 文件内容。
"""

import os
import sys
from pathlib import Path

OK = "BARK-KEYFILE-RESIDUE: OK"
BAD = "BARK-KEYFILE-RESIDUE: RESIDUE"
NODEID = "tests/regression/bark_coldstart_probe.py::test_coldstart_keyfile_redirected"


def main() -> int:
    backend = Path(__file__).resolve().parents[1]
    os.chdir(backend)
    if "send_bark" in sys.modules:
        print(f"{BAD} 冷启动前提破坏: 进入本脚本时 send_bark 已加载")
        return 1

    env_before = os.environ.get("BARK_KEY_FILE")
    expected = Path(env_before or Path.home() / ".config" / "canvas-review" / "bark.key")

    import pytest

    rc = pytest.main(["-p", "no:cacheprovider", "-q", NODEID])
    if int(rc) != 0:
        print(f"{BAD} 布防跑未绿 (pytest rc={int(rc)}) — 冷启动分支未被证明走到, 残留判据无意义")
        return 1

    send_bark = sys.modules.get("send_bark")
    if send_bark is None:
        print(f"{BAD} send_bark 未进入 sys.modules — 守卫并没有真的 import 它")
        return 1

    kf = Path(send_bark.KEY_FILE)
    problems = []
    if kf != expected:
        problems.append(f"KEY_FILE={kf} 不等于本进程真实默认 {expected}")
    # 只在「路径本来就不对」时才补报痕迹 —— 合法自定义路径完全可以叫
    # /tmp/legitimate-bark-guard-config/key (round-3 审查实证误报)。
    if kf != expected and "bark-guard-" in str(kf):
        problems.append("KEY_FILE 仍带守卫 tmp 目录痕迹 (bark-guard-*)")
    # 冷启动加载的模块属性: 全局还原对账只比对 collection 期就已存在的模块,
    # 冷启动这一面归本脚本管 (round-3 审查指出的覆盖缺口)。
    if getattr(send_bark._urlopen, "__qualname__", "") != "urlopen":
        problems.append(f"send_bark._urlopen 未恢复 (现为 {send_bark._urlopen!r})")
    runner = sys.modules.get("daily_review_run")
    if runner is not None and getattr(runner.osascript_fallback, "__qualname__", "") != "osascript_fallback":
        problems.append(f"daily_review_run.osascript_fallback 未恢复 (现为 {runner.osascript_fallback!r})")
    # 只在「路径本来就不对」时才补报父目录 —— 合法的自定义配置完全可以指向一个
    # 尚未创建的父目录 (round-2 审查用 BARK_KEY_FILE=/tmp/<不存在>/key 实证误报)。
    if kf != expected and not kf.parent.is_dir():
        problems.append(f"KEY_FILE 的父目录已不存在 ({kf.parent}) — 典型的已删 tmp 残留")
    if os.environ.get("BARK_KEY_FILE") != env_before:
        problems.append(f"env BARK_KEY_FILE 未恢复 (现 {os.environ.get('BARK_KEY_FILE')!r}, 原 {env_before!r})")

    if problems:
        for p in problems:
            print(f"{BAD} {p}")
        return 1
    print(f"{OK} KEY_FILE={kf} (= 真实默认, 无 tmp 残留, env 已恢复)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
