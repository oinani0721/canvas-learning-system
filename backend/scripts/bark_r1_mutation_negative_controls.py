#!/usr/bin/env python3
"""CARD-TEST-bark-autostub-R1 变异负控: 逐条证明「门是承重的」。

放行门全绿只说明当前实现让它们绿; 要证明某一层防线真的被某道门盯着,
必须把那一层拆掉、看**指定的那道门**变红 (不是「某处有失败」)。
本脚本对每条变异:
  1. 记录目标文件 sha256, 原字节存内存;
  2. 施加一处精确变异 (锚点必须唯一命中, 否则立即中止 —— 锚点漂移
     不能变成静默跳过);
  3. 只跑该变异对应的**指定跑** (`negative_control --only <label>`),
     要求整体判为 FAIL 且输出含指定 sentinel;
  4. 逐字节还原并复算 sha256, 不等即 BLOCKER。

串行执行, 绝不并发 (原地改源码的脚本并发跑会互踩, 而「还原后字节相同」
恰恰是唯一能发现互踩的判据)。try/finally + atexit + SIGINT/SIGTERM 三重
还原钩子: 中途被打断也不留变异体。

M9 另有一层: 它复刻 round-3 实证过的 stdout 伪造绕过, 并**同时**用第八批
那套文本判据 (逐行重写在 _legacy_text_judge 里) 判同一份输出 —— 老判据
判 True、新判据判 FAIL, 才算证明 (e) 真的关掉了一条通路, 而不是自说自话。
"""

import atexit
import re
import signal
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
CONFTEST = BACKEND / "tests/regression/conftest.py"
PROBE = BACKEND / "tests/regression/bark_egress_probe.py"
NEGCTL = "scripts/bark_autostub_negative_control.py"

_INFLIGHT: dict[Path, bytes] = {}


def _restore_all():
    for path, data in list(_INFLIGHT.items()):
        path.write_bytes(data)
        _INFLIGHT.pop(path, None)


atexit.register(_restore_all)
for _sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(_sig, lambda *_a: (_restore_all(), sys.exit(130)))


#: 守卫 _reapply 里各层的精确源码片段 —— 变异按「同一向量的全部防线」成组拆,
#: 只拆一层会被同向量的另一层兜住, 那样门不变红并不能说明门无效
#: (项目教训 reference_mutation_must_disable_all_layers)。
_L5A = "            for var in _bark_proxy_env_names(os.environ):\n                patcher.delenv(var, raising=False)\n"
_L5B = '            patcher.setattr(urllib.request, "getproxies", _no_proxies)\n'
_L5D = '            patcher.setattr(urllib.request, "_opener", _safe_opener)\n'
_L5E = '            patcher.setattr(urllib.request, "proxy_bypass", _always_bypass_proxy)\n'
_L5C = '            for mod, attr, repl in (\n                (urllib.request, "_get_proxies", _no_proxies),\n                (urllib.request, "_get_proxy_settings", _no_proxy_settings),\n                (_scproxy, "_get_proxies", _no_proxies),\n                (_scproxy, "_get_proxy_settings", _no_proxy_settings),\n            ):\n                if mod is not None and hasattr(mod, attr):\n                    patcher.setattr(mod, attr, repl)\n'

MUTATIONS = [
    {
        "id": "M1",
        "file": CONFTEST,
        "desc": "(c) 冷启动残留修复退回 round-3 形态 (在 setenv 之后才读 env)",
        "old": '        real_default_key = Path(env_key_file_before or Path.home() / ".config" / "canvas-review" / "bark.key")',
        "new": '        real_default_key = Path(os.environ.get("BARK_KEY_FILE") or Path.home() / ".config" / "canvas-review" / "bark.key")',
        "gate": "G/keyfile-no-residue-after-teardown",
        "sentinel": "BARK-KEYFILE-RESIDUE: RESIDUE",
    },
    {
        "id": "M2",
        "file": CONFTEST,
        "desc": "整层⑤ 全拆 (⑤a~⑤e) — 代理路由这一条向量上五层互相兜底, "
        "在 darwin 上 ⑤c 一层就足以让 bypass 恒真, 所以必须整组拆才判得出门是否承重",
        "old": _L5D,
        "new": "",
        "extras": [(_L5E, ""), (_L5B, ""), (_L5A, ""), (_L5C, "")],
        "gate": "F/armed-proxy-first-hop-loopback",
        "sentinel": "BARK-GATE-F-FIRSTHOP",
    },
    {
        "id": "M3",
        "file": CONFTEST,
        "desc": "层⑤a 拆除: 不再清空代理 env",
        "old": _L5A,
        "new": "",
        "gate": "F2/armed-proxy-state-neutralized",
        "sentinel": "BARK-GATE-F2-ENVPROXY",
    },
    {
        "id": "M5",
        "file": CONFTEST,
        "desc": "层⑤c 拆除: 不再中和 _scproxy / urllib.request._get_proxies",
        "old": """            for mod, attr, repl in (
                (urllib.request, "_get_proxies", _no_proxies),
                (urllib.request, "_get_proxy_settings", _no_proxy_settings),
                (_scproxy, "_get_proxies", _no_proxies),
                (_scproxy, "_get_proxy_settings", _no_proxy_settings),
            ):
                if mod is not None and hasattr(mod, attr):
                    patcher.setattr(mod, attr, repl)
""",
        "new": "",
        "gate": "F2/armed-proxy-state-neutralized",
        "sentinel": "BARK-GATE-F2-SCPROXY",
    },
    {
        "id": "M4",
        "file": CONFTEST,
        "desc": "同向量全拆 — ⑤a(清代理 env) + ⑤b(getproxies) + ⑤c(_scproxy) + ⑤e: "
        "四层都盖着「现场新建 opener 会读到什么代理」这一条",
        "old": _L5B,
        "new": "",
        "extras": [(_L5E, ""), (_L5A, ""), (_L5C, "")],
        "gate": "F/armed-proxy-first-hop-loopback",
        "sentinel": "BARK-GATE-F-FRESHHOP",
    },
    {
        "id": "M6",
        "file": CONFTEST,
        "desc": "层⑥ 拆除: subprocess.run 不再过滤 osascript",
        "old": '            patcher.setattr(subprocess, "run", _guarded_subprocess_run)\n',
        "new": "",
        "gate": "H/armed-osascript-prebound-blocked",
        "sentinel": "BARK-GATE-H-OSASCRIPT-SPAWN",
    },
    {
        "id": "M7",
        "file": CONFTEST,
        "desc": "(a) reload 拒绝退回 round-3 形态 (先 reload 后 raise)",
        "old": """        def _guarded_reload(module):
            if module.__name__ in _BARK_PATCHED_MODULES and not reload_band_active["on"]:
                raise RuntimeError(""",
        "new": """        def _guarded_reload(module):
            _real_reload(module)
            if module.__name__ in _BARK_PATCHED_MODULES and not reload_band_active["on"]:
                raise RuntimeError(""",
        "gate": "S/armed-stale-reload-refused",
        "sentinel": "BARK-GATE-S-MODULE-REEXECUTED",
    },
    {
        "id": "M8",
        "file": CONFTEST,
        "desc": "urllib.request 移出 reload 双保险名单 (round-3 H1 逃逸链第一步)",
        "old": '    "urllib.request",\n',
        "new": "",
        "gate": "E/armed-reload-selfheal",
        "sentinel": "BARK-GATE-E-RELOAD-URLLIB-URLOPEN",
    },
    {
        "id": "M10",
        "file": CONFTEST,
        "desc": "模块门拆除: 守卫对所有 regression 文件恒布防",
        "old": 'def _is_guarded_module(module_name: str) -> bool:\n    last = module_name.rsplit(".", 1)[-1]\n    return last.startswith(_BARK_GUARDED_PREFIX) or last in _BARK_GUARDED_MODULES',
        "new": "def _is_guarded_module(module_name: str) -> bool:\n    return True",
        "gate": "U/armed-unguarded-module-untouched",
        "sentinel": "BARK-GATE-U-IMPORT",
    },
    {
        "id": "M11",
        "file": PROBE,
        "desc": "探针自装的双墙拆除 — 逃逸必须落到总账层被记账并炸红, 否则总账层就是死门",
        "old": '    monkeypatch.setattr(socket, "getaddrinfo", _intercept_getaddrinfo)\n'
        '    monkeypatch.setattr(socket, "create_connection", _intercept_create_connection)\n',
        "new": "",
        "gate": "A/disarmed-probe-egress-attempted",
        "sentinel": "BARK-LEDGER-",
    },
    {
        "id": "M12",
        "file": CONFTEST,
        "desc": "层⑤d 改用 install_opener 直接装 (布防期内行为一样, 但 teardown 不还原) "
        "— 检验全局还原对账是不是真的能看见进程级污染",
        "old": '            patcher.setattr(urllib.request, "_opener", _safe_opener)',
        "new": "            urllib.request.install_opener(_safe_opener)",
        "gate": "E/armed-reload-selfheal",
        "sentinel": "globals 未还原",
    },
    {
        "id": "M14",
        "file": CONFTEST,
        "desc": "subprocess 移出 reload 名单 — round-2 审查实测 reload(subprocess) 会冲掉层⑥",
        "old": '    "subprocess",\n',
        "new": "",
        "gate": "E/armed-reload-selfheal",
        "sentinel": "BARK-GATE-E-RELOAD-SUBPROCESS",
    },
    {
        "id": "M15",
        "file": CONFTEST,
        "desc": "⑤c 的 proxy settings 存根退回「没有例外」语义 — 重载后 proxy_bypass "
        "会判定不 bypass, 别处握持的 opener 重新走代理 (round-2 审查击穿点)",
        "old": '            return {"exclude_simple": True, "exceptions": ["*"]}',
        "new": '            return {"exclude_simple": False, "exceptions": []}',
        "gate": "R/armed-held-opener-after-prebound-reload",
        "sentinel": "BARK-GATE-R-HELDHOP",
    },
    {
        "id": "M16",
        "file": CONFTEST,
        "desc": "层⑥ 判定退回「argv[0] 的 substring」— 误吞面: 名字里带 osascript 的无关命令被静默吞掉",
        "old": '            if _basename(argv[0]) == "osascript":\n                return True\n',
        "new": '            if "osascript" in str(argv[0]):\n                return True\n',
        "gate": "H/armed-osascript-prebound-blocked",
        "sentinel": "BARK-GATE-H-DECOY",
    },
    {
        "id": "M17",
        "file": CONFTEST,
        "desc": "层⑥ 判定退回「只看 argv[0]」(basename 全等但不扫整条 argv) — 漏判面: "
        "/usr/bin/env osascript 这种间接形态会抵达真 spawn",
        "old": '            if _basename(argv[0]) == "env":',
        "new": "            if False:",
        "gate": "H/armed-osascript-prebound-blocked",
        "sentinel": "BARK-GATE-H-INDIRECT",
    },
    {
        "id": "M18",
        "file": CONFTEST,
        "desc": "层⑤a 退回固定枚举清单 — 混合大小写的 Http_Proxy 会活着穿过布防期 "
        "(round-3 审查击穿点: getproxies_environment 是 lower() 之后才判后缀)",
        "old": '    return [k for k in list(environ) if k.lower().endswith("_proxy")]',
        "new": '    return [k for k in ("http_proxy", "HTTP_PROXY", "no_proxy", "NO_PROXY") if k in environ]',
        "gate": "F2/armed-proxy-state-neutralized",
        "sentinel": "BARK-GATE-F2-ENVPROXY",
    },
    {
        "id": "M19",
        "file": CONFTEST,
        "desc": "重打退回「reload 正常返回才执行」— reload 半途抛异常会留下失防模块 "
        "(round-3 审查击穿点, 与第八批 H2 同形)",
        "old": """            try:
                return _real_reload(module)
            finally:
                if module.__name__ in _BARK_PATCHED_MODULES:
                    _reapply()""",
        "new": """            result = _real_reload(module)
            if module.__name__ in _BARK_PATCHED_MODULES:
                _reapply()
            return result""",
        "gate": "X/armed-reapply-after-failed-reload",
        "sentinel": "BARK-GATE-X-REAPPLY-ON-FAILURE",
    },
]

#: M9 单列: 它变异的是探针而非守卫, 且要双判据对比。
M9 = {
    "id": "M9",
    "file": PROBE,
    "desc": "(e) stdout 伪造绕过 (复刻 round-3 实证形态): 同文件无关失败 + 打印伪造的 traceback 行与 E 行",
    "old": "def test_probe(tmp_path, monkeypatch, capsys):\n",
    "new": (
        "def test_probe(tmp_path, monkeypatch, capsys):\n"
        '    print("  tests/regression/conftest.py:335: in _refuse_egress")\n'
        '    print("E   AssertionError: Bark egress attempted in tests")\n'
        '    assert False, "unrelated failure in probe"\n'
    ),
    "gate": "B/armed-probe-refused",
    "sentinel": "异常首行不符",
}

_LEGACY_SUMMARY = r"=+\s+(.*?)\s+in\s+[\d.]+s\s*=+$"
_LEGACY_PATTERN = r"^E\s+AssertionError: Bark egress attempted in tests\s*$"
_LEGACY_SRC_HINT = "conftest.py"


def _legacy_text_judge(rc: int, out: str) -> bool:
    """第八批 (HEAD 2cacbb0c) 的文本判据, 逐行重写用于对照。

    摘要唯一性 + 形态 + `^E ...$` 整行锚定 + 「E 行前 1500 字符窗口含
    conftest.py」。它判 True 而 R1 判 FAIL, 就是 (e) 关掉的那条通路。"""
    summaries = [m.group(1) for line in out.splitlines() if (m := re.match(_LEGACY_SUMMARY, line.strip()))]
    shape_ok = (
        len(summaries) == 1
        and re.fullmatch(r"1 failed(, \d+ warnings?)?", summaries[0]) is not None
        and " no tests ran" not in out
        and "= ERRORS =" not in out
    )
    m = re.search(_LEGACY_PATTERN, out, re.MULTILINE)
    regex_ok = m is not None
    src_ok = bool(m) and _LEGACY_SRC_HINT in out[max(0, m.start() - 1500) : m.start()]
    return rc == 1 and shape_ok and regex_ok and src_ok


def _apply(mut) -> str:
    path: Path = mut["file"]
    original = path.read_bytes()
    before = sha256(original).hexdigest()
    text = original.decode("utf-8")
    n = text.count(mut["old"])
    if n != 1:
        raise SystemExit(f"[{mut['id']}] 锚点命中 {n} 次 (必须恰好 1) — 锚点漂移, 中止")
    mutated = text.replace(mut["old"], mut["new"])
    for i, (eo, en) in enumerate(mut.get("extras", []), start=2):
        n2 = mutated.count(eo)
        if n2 != 1:
            raise SystemExit(f"[{mut['id']}] 第 {i} 个锚点命中 {n2} 次 (必须恰好 1) — 锚点漂移, 中止")
        mutated = mutated.replace(eo, en)
    _INFLIGHT[path] = original
    path.write_text(mutated, encoding="utf-8")
    return before


def _restore(mut, before: str) -> bool:
    path: Path = mut["file"]
    path.write_bytes(_INFLIGHT.pop(path))
    after = sha256(path.read_bytes()).hexdigest()
    same = before == after
    print(f"[{mut['id']}] 还原逐字节一致: {'YES' if same else 'NO!!'} ({after})")
    return same


def _run_negctl(gate: str):
    proc = subprocess.run(
        [sys.executable, NEGCTL, "--only", gate],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        timeout=1800,
        env={**_child_env()},
    )
    return proc.returncode, proc.stdout + proc.stderr


def _child_env():
    import os

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _check(mut) -> bool:
    print(f"\n=== [{mut['id']}] {mut['desc']}")
    print(f"    指定门: {mut['gate']} / 期望 sentinel: {mut['sentinel']}")
    before = _apply(mut)
    try:
        rc, out = _run_negctl(mut["gate"])
        # 元裁判收紧 (round-2 审查 MEDIUM): 「rc!=0 + 输出含 sentinel」会把
        # 「基础设施炸了 + 恰好打印了那串文本」判成「指定门承重」。现在要求
        # rc 恰为 1、负控确实跑完给出总判、且**指定的那道跑**自己判 ok=False。
        gate_line = re.search(r"^\[" + re.escape(mut["gate"]) + r"\].*-> ok=False", out, re.MULTILINE)
        went_red = rc == 1 and "NEGATIVE-CONTROL: FAIL" in out and gate_line is not None
        # sentinel 只在**裁判自己产出的行**里找: 指定跑的 CRASH 行 (来自异常对象)
        # 与 ✗ 问题行。round-3 审查实证: 让被测代码 print 一行 sentinel 再制造
        # 无关失败, 「sentinel 出现在输出任意位置」的判据就会被骗过。
        judged_lines = [
            ln for ln in out.splitlines() if ln.startswith(f"[{mut['gate']}] CRASH ") or ln.lstrip().startswith("✗ ")
        ]
        has_sentinel = any(mut["sentinel"] in ln for ln in judged_lines)
        ok = went_red and has_sentinel
        print(f"[{mut['id']}] 指定门变红={went_red} (negctl rc={rc}); sentinel 命中={has_sentinel}")
        if mut["id"] == "M9":
            legacy = _legacy_text_judge(1, out)
            print(f"[{mut['id']}] 第八批文本判据对同一份输出的判定: {legacy} (True = 老判据会放行, 正是 R1 关掉的通路)")
            ok = ok and legacy
        if not ok:
            print(out[-4000:])
    finally:
        restored = _restore(mut, before)
    return ok and restored


def main() -> int:
    results = []
    for mut in MUTATIONS + [M9]:
        results.append((mut["id"], _check(mut)))
    print()
    for mid, ok in results:
        print(f"{mid}: {'指定门变红 ✓' if ok else 'NOT-RED ✗'}")
    if all(ok for _, ok in results):
        print(f"MUTATION-NEGATIVE-CONTROL: PASS ({len(results)}/{len(results)} 条变异均使指定门变红)")
        return 0
    print("MUTATION-NEGATIVE-CONTROL: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
