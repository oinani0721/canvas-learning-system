#!/usr/bin/env python3
"""CARD-TEST-bark-autostub 负控裁判 (A/B/C'/C/D/D'/E/E' 八跑, 串行子进程)。

A  (disarmed): --noconftest 卸下守卫 → test_probe 期望 PASS —— 证明「去掉
   fixture 就会真的尝试外发」(探针自装的 getaddrinfo/create_connection
   双拦截器挡住, 任何情况下不出网);
B  (armed):    正常 conftest → test_probe 期望 FAIL, 且失败必须是指定的
   那道断言 (pytest 输出里整行 `E   AssertionError: Bark egress attempted
   in tests`) —— 拒绝器层在被它验证的逻辑;
C  (armed):    test_keyfile_guarded 期望 PASS —— 守卫层① KEY_FILE 重定向
   的放行门;
C' (disarmed): --noconftest 同 nodeid 期望 FAIL(指定消息) —— 层①篡改门:
   证明 C 真的依赖守卫, 不是恒真;
D  (armed):    test_osascript_guarded 期望 PASS —— 守卫层③ osascript 打桩
   的放行门;
D' (disarmed): --noconftest 同 nodeid 期望 FAIL(指定消息) —— 层③篡改门;
E  (armed):    test_reload_selfheal 期望 PASS —— reload 双保险放行门;
E' (disarmed): --noconftest 同 nodeid 期望 FAIL(指定消息) —— reload 篡改门。

判据口径 (round-3 收紧): 每跑核「退出码 + 摘要唯一性 + 指定断言正则 +
异常来源绑定」——
- 摘要: 全 stdout 中形态为 `= N passed/failed(, N warnings) in Xs =` 的
  摘要行必须**恰好 1 条**且形态精确 (atexit/插件追加的伪摘要 → 2 条 → 拒
  收; `N error` 摘要与 `= ERRORS =` 段一律拒收) (round-2 MEDIUM);
- 指定断言: `^E\\s+...\\s*$` 整行锚定 (round-2: C'/D'/E' 补上行尾锚),
  字符串碰巧出现在 traceback 源码行里不算数;
- 来源绑定 (round-2 MEDIUM): `E ` 行所在 traceback 块 (其前 1500 字符窗
  口) 必须含 src_hint — B 的拒绝异常须真的来自 conftest.py, 探针三条须来
  自探针文件自身; 测试打印同文本却在别处失败无法同时满足。
TimeoutExpired 捕获记 FAIL, 不炸取证面。

exit 0 仅当八跑全部按期望。串行、子进程、-p no:cacheprovider 防并行
session 共享 .pytest_cache 踩踏。
"""

import re
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
PROBE = "tests/regression/bark_egress_probe.py"
#: (label, nodeid, extra_args, expect, pattern, src_hint)
CASES = [
    ("A/disarmed-probe-egress-attempted", f"{PROBE}::test_probe", ["--noconftest"], "pass", None, None),
    (
        "B/armed-probe-refused",
        f"{PROBE}::test_probe",
        [],
        "fail",
        r"^E\s+AssertionError: Bark egress attempted in tests\s*$",
        "conftest.py",
    ),
    ("C/armed-keyfile-guarded", f"{PROBE}::test_keyfile_guarded", [], "pass", None, None),
    (
        "C'/disarmed-keyfile-tamper",
        f"{PROBE}::test_keyfile_guarded",
        ["--noconftest"],
        "fail",
        r"^E\s+AssertionError: 守卫未布防: send_bark\.KEY_FILE 仍指向真实 key 位置\s*$",
        "bark_egress_probe.py",
    ),
    ("D/armed-osascript-guarded", f"{PROBE}::test_osascript_guarded", [], "pass", None, None),
    (
        "D'/disarmed-osascript-tamper",
        f"{PROBE}::test_osascript_guarded",
        ["--noconftest"],
        "fail",
        r"^E\s+AssertionError: 守卫未布防: osascript_fallback 仍是 runner 原始实现\s*$",
        "bark_egress_probe.py",
    ),
    ("E/armed-reload-selfheal", f"{PROBE}::test_reload_selfheal", [], "pass", None, None),
    (
        "E'/disarmed-reload-tamper",
        f"{PROBE}::test_reload_selfheal",
        ["--noconftest"],
        "fail",
        r"^E\s+AssertionError: 守卫未布防或 reload 自愈失效: reload 后 KEY_FILE 回到真实 key 位置\s*$",
        "bark_egress_probe.py",
    ),
]

_SUMMARY = r"=+\s+(.*?)\s+in\s+[\d.]+s\s*=+$"


def _summaries(stdout: str) -> list[str]:
    """全 stdout 中所有 pytest 摘要行正文 (正常恰 1 条; 伪摘要 → 多条)。"""
    return [m.group(1) for line in stdout.splitlines() if (m := re.match(_SUMMARY, line.strip()))]


def _judged(label, nodeid, extra, expect, pattern, src_hint) -> bool:
    cmd = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *extra, nodeid]
    print(f"[{label}] $ {' '.join(cmd)}", flush=True)
    try:
        proc = subprocess.run(cmd, cwd=BACKEND, capture_output=True, text=True, timeout=600)
        rc, out = proc.returncode, proc.stdout
        sys.stdout.write(out)
        sys.stderr.write(proc.stderr)
    except subprocess.TimeoutExpired as e:
        sys.stdout.write(e.stdout or "" if isinstance(e.stdout, str) else "")
        sys.stderr.write(str(e))
        print(f"[{label}] TIMEOUT after 600s")
        return False

    summaries = _summaries(out)
    shape_re = r"1 passed(, \d+ warnings?)?" if expect == "pass" else r"1 failed(, \d+ warnings?)?"
    # 摘要唯一性 + 精确形态 + 无 error 摘要/ERRORS 段 (round-2 MEDIUM)
    shape_ok = (
        len(summaries) == 1
        and re.fullmatch(shape_re, summaries[0]) is not None
        and " no tests ran" not in out
        and "= ERRORS =" not in out
    )
    regex_ok = True
    src_ok = True
    if pattern is not None:
        m = re.search(pattern, out, re.MULTILINE)
        if m is None:
            regex_ok = False
        elif src_hint is not None:
            # 来源绑定: E 行之前的 traceback 窗口必须含来源文件 (round-2 MEDIUM)
            window = out[max(0, m.start() - 1500) : m.start()]
            src_ok = src_hint in window
    rc_ok = rc == (0 if expect == "pass" else 1)
    ok = rc_ok and shape_ok and regex_ok and src_ok
    print(
        f"[{label}] expect {expect.upper()} -> ok={ok} rc={rc} "
        f"n_summaries={len(summaries)} summary='{summaries[0] if summaries else ''}' "
        f"regex={regex_ok} src={src_ok if pattern is not None else 'n/a'}"
    )
    return ok


def main() -> int:
    results = [_judged(*case) for case in CASES]
    for (label, _, _, expect, _, _), ok in zip(CASES, results):
        print(f"{label}: expect {expect.upper()} -> {'ok' if ok else 'MISMATCH'}")
    if all(results):
        print("NEGATIVE-CONTROL: PASS (armed=probe-FAILED-as-expected, disarmed=probe-PASSED-egress-attempted)")
        return 0
    print("NEGATIVE-CONTROL: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
