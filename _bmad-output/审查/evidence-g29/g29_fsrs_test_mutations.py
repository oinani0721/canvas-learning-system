"""(c) 两条测试的验伪：原地变异 → 指定断言必须红 → 无条件还原 + sha 对账。"""
import hashlib, pathlib, subprocess, sys

TGT = pathlib.Path("tests/regression/test_g29_dual_vault_fsrs_isolation.py")
PYTEST = "./.venv/bin/pytest"
ORIG = TGT.read_text(encoding="utf-8")
BASE_SHA = hashlib.sha256(ORIG.encode()).hexdigest()

MUTS = [
    ("C1_global_state_file",
     'state = backups / f"daily-review.{vault.name}.state.json"',
     'state = backups / "daily-review.vaultA.state.json"',
     "state 文件退化成全局单例（C1a 修的那个根缺陷）"),
    ("C2_fsrs_due_ignored",
     'FUTURE_DUE = "2099-01-01T00:00:00Z"',
     'FUTURE_DUE = ""',
     "B 的 fsrs_due 被抹掉 ⇒ 变 New 卡即刻到期（FSRS 判定失效）"),
    # ⚠️ C3 第一版写成「把检查面清空」——那是**拆掉断言**而不是制造缺陷，
    #    断言不跑当然不会红，SURVIVED 毫无信息量。改成制造一次真实的交叉
    #    污染：让 A 侧读到 B 的投影目录（模拟 outputs 不按 vault 隔离）。
    ("C3_outputs_not_isolated",
     "texts_a = _projection_texts(vault_a, backups)",
     "texts_a = _projection_texts(vault_b, backups)",
     "A 侧读到 B 的投影（outputs 目录不按 vault 隔离）"),
]

results = []
try:
    for name, old, new, what in MUTS:
        assert ORIG.count(old) == 1, f"{name}: 锚点不唯一/不存在 ({ORIG.count(old)})"
        TGT.write_text(ORIG.replace(old, new), encoding="utf-8")
        r = subprocess.run(
            [PYTEST, "-q", "-p", "no:cacheprovider", str(TGT), "--tb=no"],
            capture_output=True, text=True,
        )
        tail = [ln for ln in r.stdout.splitlines() if "passed" in ln or "failed" in ln]
        results.append((name, r.returncode, tail[-1] if tail else "<无摘要>", what))
finally:
    TGT.write_text(ORIG, encoding="utf-8")

after = hashlib.sha256(TGT.read_text(encoding="utf-8").encode()).hexdigest()
print(f"还原校验: {'OK 逐字节相同' if after == BASE_SHA else '*** 未还原 ***'} ({BASE_SHA[:12]})")
print()
bad = []
for name, rc, tail, what in results:
    verdict = "KILLED" if rc != 0 else "SURVIVED"
    if rc == 0:
        bad.append(name)
    print(f"  {verdict:<9} {name}  rc={rc}")
    print(f"            {what}")
    print(f"            {tail}")
sys.exit(1 if bad or after != BASE_SHA else 0)
