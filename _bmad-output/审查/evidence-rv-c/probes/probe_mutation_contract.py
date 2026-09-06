"""RV-C：把 Codex p2 的 HIGH-1 / MEDIUM-2 从「静态推演」升级为实测。

问题：TestSelftestAddressClassification 的 6 条测试，在下列变异下是否仍全绿？
  M0 对照 = 原样（必须全绿，否则复刻不忠实）
  M1 = 实现 :476 去掉哨兵比较，只判 `type(host) is str`   （拆判据）
  M2 = 实现 :439 哨兵改成可解析的普通主机名 "localhost"   （改常量）

⛔ 全程只操作 scratchpad 副本；生产文件一行不碰（跑完复核原件 sha）。
"""
import hashlib
import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
ORIG = HERE / "lpg.py"
ORIG_SHA = hashlib.sha256(ORIG.read_bytes()).hexdigest()

SRC = ORIG.read_text(encoding="utf-8")

LINE476 = '    return type(host) is str and host == _SELFTEST_HOST  # noqa: E721 —— str 子类不算'
LINE439 = '_SELFTEST_HOST = "\\x00w4-live-port-guard-selftest"'

VARIANTS = {
    "M0 (control, unmutated)": SRC,
    "M1 (:476 drop sentinel comparison)": SRC.replace(
        LINE476, '    return type(host) is str  # MUTANT M1'
    ),
    "M2 (:439 sentinel -> resolvable host)": SRC.replace(
        LINE439, '_SELFTEST_HOST = "localhost"  # MUTANT M2'
    ),
}

for name, src in VARIANTS.items():
    if name.startswith("M0"):
        continue
    assert src != SRC, f"{name}: mutation anchor did not match — mutation would be invisible"


def load(tag, src):
    p = HERE / f"_mut_{tag}.py"
    p.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"mut_{tag}", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"mut_{tag}"] = m
    spec.loader.exec_module(m)
    return m


def run_six(g):
    """逐字复刻 TestSelftestAddressClassification 的 6 条测试。"""
    results = {}

    def check(name, fn):
        try:
            fn()
            results[name] = "pass"
        except AssertionError as e:
            results[name] = f"FAIL({e or 'assert'})"
        except Exception as e:
            results[name] = f"ERROR({type(e).__name__})"

    check("1 genuine_selftest_address_is_classified",
          lambda: (_ for _ in ()).throw(AssertionError()) if
          g._is_selftest_address((g._SELFTEST_HOST, 7691)) is not True else None)

    def t2():
        class Disguise(tuple):
            def __getitem__(self, i):
                return g._SELFTEST_HOST if i == 0 else super().__getitem__(i)
        addr = Disguise(("127.0.0.1", 7691))
        assert addr[0] == g._SELFTEST_HOST, "前提：表面确实伪装成了哨兵"
        assert tuple.__getitem__(addr, 0) == "127.0.0.1", "前提：底层是真实主机"
        assert g._is_selftest_address(addr) is False
    check("2 tuple_subclass_disguise_is_not_selftest", t2)

    def t3():
        class AlwaysEqual(str):
            def __eq__(self, other):
                return True
            __hash__ = str.__hash__
        addr = (AlwaysEqual("127.0.0.1"), 7691)
        assert addr[0] == g._SELFTEST_HOST, "前提：__eq__ 确实对哨兵返回真"
        assert g._is_selftest_address(addr) is False
    check("3 str_subclass_eq_disguise_is_not_selftest", t3)

    def t4():
        assert g._is_selftest_address("/tmp/sock") is False
        assert g._is_selftest_address(()) is False
    check("4 non_tuple_is_not_selftest", t4)

    def t5():
        addr = ("127.0.0.1", 11434)
        assert g._audit_hook("socket.connect", (None, addr)) is None
    check("5 audit_hook_does_not_block_plain_safe_address", t5)

    def t6():
        try:
            g._audit_hook("socket.connect", (None, (g._SELFTEST_HOST, 7691)))
        except g._SelfTestBlocked:
            return
        raise AssertionError("did not raise _SelfTestBlocked")
    check("6 genuine_selftest_address_reaches_blocking_path", t6)

    return results


print(f"{'variant':40s} | 6 contract assertions | verdict")
print("-" * 96)
for i, (name, src) in enumerate(VARIANTS.items()):
    g = load(f"v{i}", src)
    res = run_six(g)
    npass = sum(1 for v in res.values() if v == "pass")
    if name.startswith("M0"):
        verdict = "baseline OK" if npass == 6 else "⚠ replica unfaithful"
    else:
        verdict = "⛔ SURVIVED (gate does not hold)" if npass == 6 else f"KILLED ({6-npass} red)"
    print(f"{name:40s} | {npass}/6 pass            | {verdict}")
    for k, v in res.items():
        if v != "pass":
            print(f"{'':40s} |   {k}: {v}")

print()
print("=== does the mutated classifier now misclassify a REAL live-port address? ===")
for i, (name, src) in enumerate(VARIANTS.items()):
    g = sys.modules[f"mut_v{i}"]
    real = ("127.0.0.1", 7691)
    print(f"  {name:40s} _is_selftest_address(('127.0.0.1', 7691)) = {g._is_selftest_address(real)}")

print()
print("=== production file untouched? ===")
now = hashlib.sha256(ORIG.read_bytes()).hexdigest()
print(f"  scratchpad lpg.py sha before = {ORIG_SHA[:16]}…")
print(f"  scratchpad lpg.py sha after  = {now[:16]}…  {'SAME' if now == ORIG_SHA else 'CHANGED!'}")
