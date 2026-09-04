"""未布防模块零副作用探针 (CARD-TEST-bark-autostub-R1 完成条件 (d) 后半句)。

守卫的模块门承诺: 名字不在布防面内的文件, 本 fixture 只实例化 request,
**不** import scripts 模块、不动 sys.path、不改 env、不建临时目录。
这条承诺此前只有「regression collect 计数不变 + pick 37 不变」间接背书 ——
那两个数字在守卫对所有文件都布防时**照样不变** (布防不改变收集与通过),
等于承诺比证据宽。本文件把它变成直接可证伪的断言。

本模块名既不以 test_daily_review 开头、也不在 _BARK_GUARDED_MODULES 内,
所以运行时守卫必须走早退分支; 文件名不带 test_ 前缀 → 默认收集不到,
regression collect 计数不受影响。

篡改门形态: 本门没有 --noconftest 孪生 (卸甲=没有守卫, 断言自然成立,
那种「红不了」的孪生是假门)。它的证伪由变异负控承担 ——
bark_r1_mutation_negative_controls.py 的 M10 把模块门改成恒布防,
本门必须当场变红。
"""

import os
import sys
from pathlib import Path

#: collection 期快照 —— 早于任何 fixture, 因此是「守卫动手之前」的真值。
#: sys.path 存**整份列表**、env 存全部代理相关键 (不只 BARK_KEY_FILE):
#: round-3 审查指出只比 membership 布尔值和单个键, 覆盖不到「重复插入」与
#: 「删掉某个代理变量」这类污染形态。
_SYS_MODULES_AT_IMPORT = {"send_bark", "daily_review_run"} & set(sys.modules)
_SYS_PATH_AT_IMPORT = list(sys.path)


def _proxy_env_snapshot():
    keys = {k for k in os.environ if k.lower().endswith("_proxy")} | {"BARK_KEY_FILE"}
    return {k: os.environ.get(k) for k in sorted(keys)}


_ENV_AT_IMPORT = _proxy_env_snapshot()


def test_guard_leaves_unguarded_modules_untouched():
    """armed conftest + 未布防模块名 → 守卫必须什么都没做。"""
    now = {"send_bark", "daily_review_run"} & set(sys.modules)
    assert now == _SYS_MODULES_AT_IMPORT, (
        f"BARK-GATE-U-IMPORT: 守卫对未布防模块产生了 import 副作用 "
        f"(import 期 {sorted(_SYS_MODULES_AT_IMPORT)} → 测试期 {sorted(now)})"
    )
    env_now = _proxy_env_snapshot()
    assert env_now == _ENV_AT_IMPORT, (
        f"BARK-GATE-U-ENV: 守卫对未布防模块改写了环境变量 (import 期 {_ENV_AT_IMPORT} → 测试期 {env_now})"
    )
    assert list(sys.path) == _SYS_PATH_AT_IMPORT, "BARK-GATE-U-SYSPATH: 守卫对未布防模块改写了 sys.path"
