#!/usr/bin/env python3
"""负控裁判的结构化报告插件 (CARD-TEST-bark-autostub-R1 完成条件 (e))。

**为什么不看 stdout**: pytest 的 stdout 里那行 `E   AssertionError: ...`
是被测进程自己的输出流, 被测代码可以逐字打印同一行。round-3 实证过这条
绕过: 「同一探针文件里制造一个无关失败 + captured stdout 打印目标 E 行 +
唯一摘要」就骗过了「E 行正则 + 前 1500 字符窗口找文件名子串」的文本判据;
连 `not_conftest.py` 也因为包含子串 `conftest.py` 而满足来源检查。

本插件改从 pytest 自己的 TestReport 取证并落 JSON:
  - crash_path / crash_lineno — longrepr.reprcrash, 即**异常抛出点所在
    frame** 的文件与行号, 由解释器 traceback 决定, 被测代码 print 不出来;
  - crash_message           — 异常对象自身的首行 (不是 stdout 的一行文本);
  - frames                  — 完整 traceback frame 链的文件/行号。

另落一份**进程级全局还原对账**: 在 collection 结束 (模块都 import 完、
一条测试都还没跑) 与 sessionfinish (所有 fixture 都 teardown 完) 各取一次
守卫会碰的全局快照 —— urlopen / getproxies / _opener / subprocess.run /
importlib.reload / _scproxy._get_proxies / 代理 env。

**为什么不含 sys.path**: `sys.path[0]` 不是守卫拥有的全局 —— 生产代码
(daily_review_run 会把 vault 的 .claude/scripts 插到 0 位) 与 pytest 自己都会
动它, 纳进来会产生与守卫无关的红 (R1 首跑二十跑里十八跑因此误红)。判据要
恰好覆盖被测对象拥有的状态; 守卫对 sys.path 的边界由 bark_unguarded_probe
的 U 门直接断言。
守卫在一次测试里可能反复 _reapply (每次 reload 都重打), 若 MonkeyPatch 的
undo 顺序或某一层的还原方式出问题, 桩就会漏到后续测试里去 —— 这份对账
是唯一能在进程外看见那件事的判据 (裁判在 negative_control 侧比对)。
裁判据此做**路径全等**比对 (不是子串), 于是 not_conftest.py 这类同尾巴
文件名不再蒙混。

用法 (由 bark_autostub_negative_control.py 装配):
    PYTHONPATH=<backend/scripts>  BARK_NEGCTL_REPORT=<out.json>
    pytest -p bark_negctl_report_plugin ...
`--noconftest` 不影响 `-p` 插件加载 —— 卸甲形态同样有结构化取证。

如实边界: 本插件信任 pytest 自己的报告结构。能改写 pytest 内部报告对象的
被测代码 (例如自装 hook 覆盖 pytest_runtest_logreport) 依然能造假; 那属于
「测试进程内故意自解脱绑」, 与守卫的威胁模型同级, 不在本门承诺内。
"""

import json
import os
import pathlib
import subprocess
import sys
import urllib.request

_RECORDS = []
_GLOBALS = {}

#: 守卫 syspath_prepend 的那个确切目录 (<repo>/scripts)。本文件在
#: <repo>/backend/scripts/ 下, 故上溯两级再拼 scripts。
_GUARD_SCRIPTS_DIR = str(pathlib.Path(__file__).resolve().parents[2] / "scripts")

#: 守卫会碰的进程级全局 —— 用于「布防前 vs 全部 teardown 后」的还原对账。
#: 只用 __module__/__qualname__ 与代理配置这类**结构指纹**, 不用 id():
#: 对象回收后 id 可能被复用, 拿它当相等判据是自证 (看起来还原了)。
_PROXY_ENV_KEYS = (
    "http_proxy",
    "https_proxy",
    "ftp_proxy",
    "all_proxy",
    "no_proxy",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "FTP_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "BARK_KEY_FILE",
)


def _fn_id(fn):
    return f"{getattr(fn, '__module__', '?')}.{getattr(fn, '__qualname__', repr(fn))}"


def _opener_fingerprint():
    op = urllib.request._opener
    if op is None:
        return None
    return {
        "handlers": sorted(h.__class__.__name__ for h in op.handlers),
        "proxies": [getattr(h, "proxies", None) for h in op.handlers if h.__class__.__name__ == "ProxyHandler"],
        "addheaders": sorted(map(str, getattr(op, "addheaders", []))),
    }


def _module_attr_fingerprint(tracked):
    """守卫直接改过的**模块属性**。只看 collection 期就已加载的模块 ——
    冷启动 (守卫自己那次 import) 让模块从无到有是预期行为, 不是污染;
    那一面由 bark_keyfile_residue_check.py 单独把关。"""
    out = {}
    for name, attrs in (("send_bark", ("KEY_FILE", "_urlopen")), ("daily_review_run", ("osascript_fallback",))):
        if name not in tracked:
            continue
        mod = sys.modules.get(name)
        out[name] = None if mod is None else {a: _fn_id(getattr(mod, a, None)) for a in attrs}
    return out


def _globals_snapshot(tracked=()):
    import importlib

    snap = {
        "module_attrs": _module_attr_fingerprint(tracked),
        "opener": _opener_fingerprint(),
        "urlopen": _fn_id(urllib.request.urlopen),
        "getproxies": _fn_id(urllib.request.getproxies),
        "proxy_bypass": _fn_id(urllib.request.proxy_bypass),
        "subprocess_run": _fn_id(subprocess.run),
        "importlib_reload": _fn_id(importlib.reload),
        "env": {k: os.environ.get(k) for k in _PROXY_ENV_KEYS},
        # 守卫会 syspath_prepend(<repo>/scripts); 数**那一个确切路径**的出现次数。
        # 不能按 "/scripts" 后缀数: 生产代码 daily_review_run 会把 vault 的
        # .claude/scripts 也插进 sys.path, 后缀判定会把它算进来 (首跑 A 误红)。
        # 也不能用 sys.path[0] —— 那一项被生产代码与 pytest 一起搅动。
        "scripts_on_path": sum(1 for p in sys.path if p == _GUARD_SCRIPTS_DIR),
    }
    if sys.platform == "darwin":
        try:
            import _scproxy

            snap["scproxy_get_proxies"] = _fn_id(_scproxy._get_proxies)
            snap["scproxy_get_proxy_settings"] = _fn_id(_scproxy._get_proxy_settings)
        except ImportError:
            pass
    if hasattr(urllib.request, "_get_proxies"):
        snap["urllib_get_proxies"] = _fn_id(urllib.request._get_proxies)
    if hasattr(urllib.request, "_get_proxy_settings"):
        snap["urllib_get_proxy_settings"] = _fn_id(urllib.request._get_proxy_settings)
    return snap


def pytest_collection_finish(session):
    """基线取在「所有测试模块都已 import、但一条测试都还没跑」的时刻 ——
    探针模块自己的 import 期副作用 (敌对代理态) 已经在里面, 于是这条对账
    问的正是「守卫把它动过的东西还回去了没有」, 而不是「进程有没有被改过」。"""
    _GLOBALS["tracked"] = tuple(m for m in ("send_bark", "daily_review_run") if m in sys.modules)
    _GLOBALS["before"] = _globals_snapshot(_GLOBALS["tracked"])


def _fileloc(entry):
    loc = getattr(entry, "reprfileloc", None)
    if loc is None:
        return None
    return {"path": loc.path, "lineno": loc.lineno}


def pytest_runtest_logreport(report):
    rec = {
        "nodeid": report.nodeid,
        "when": report.when,
        "outcome": report.outcome,
    }
    longrepr = getattr(report, "longrepr", None)
    crash = getattr(longrepr, "reprcrash", None)
    if crash is not None:
        rec["crash_path"] = crash.path
        rec["crash_lineno"] = crash.lineno
        rec["crash_message"] = crash.message
    tb = getattr(longrepr, "reprtraceback", None)
    if tb is not None:
        rec["frames"] = [f for f in (_fileloc(e) for e in getattr(tb, "reprentries", [])) if f]
    _RECORDS.append(rec)


def pytest_collectreport(report):
    if report.outcome == "failed":
        _RECORDS.append({"nodeid": report.nodeid, "when": "collect", "outcome": "failed"})


def pytest_sessionfinish(session, exitstatus):
    out = os.environ.get("BARK_NEGCTL_REPORT")
    if not out:
        return
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "exitstatus": int(exitstatus),
                "reports": _RECORDS,
                "globals_before": _GLOBALS.get("before"),
                "globals_after": _globals_snapshot(_GLOBALS.get("tracked", ())),
            },
            fh,
            ensure_ascii=False,
            indent=1,
        )
