"""验证 G6-9a 两条新门承重：变异 → 指定用例必须红 → 无条件还原 + sha 对账。"""
import hashlib, pathlib, re, subprocess, sys

TGT = pathlib.Path("tests/regression/test_g6_9_boundary_matrix.py")
ORIG = TGT.read_text(encoding="utf-8")
BASE = hashlib.sha256(ORIG.encode()).hexdigest()
FAIL_RE = re.compile(r"^FAILED (\S+)", re.M)
NODE_TABLE = f"{TGT}::test_known_divergent_table_is_current"

MUTS = [
    ("T1_table_entry_removed",
     '    ("winter-utc1630", "Europe/London"): ("2026-01-15", "2026-01-16"),\n',
     '',
     "登记表少一条（模拟表过期：实测有分叉但表里没有）",
     # ⚠️ 判据改为「表用例必须在失败集合里」而非「失败集合恰好等于它」：
     #    删掉一条登记项有**两个都正确**的后果——①表用例报「只在实测里」；
     #    ②那个组合不再被 xfail，作为普通用例跑并如实失败。初版要求失败集合
     #    严格等于 [表用例] 是判据写严了，把正确行为记成了 SURVIVED。
     "IN:" + NODE_TABLE, "只在实测里（新出现，应登记）"),
    ("T2_table_value_wrong",
     '    ("summer-utc1630", "UTC"): ("2026-07-31", "2026-08-01"),',
     '    ("summer-utc1630", "UTC"): ("2026-07-31", "2099-01-01"),',
     "登记表某条的值写错（模拟抄错/过期）",
     NODE_TABLE, "值不同"),
    ("T3_matrix_stops_calling_runner",
     "    runner_today = _real_runner_today(tmp_path, monkeypatch, tz_name, instant)\n    display_day = _display_day(instant)",
     "    runner_today = _display_day(instant)  # 假装 runner 已被修好\n    display_day = _display_day(instant)",
     "假装两套时钟已统一 ⇒ 8 条 xfail 应变 XPASS，strict 让它们红",
     None, "XPASS"),
]

results = []
try:
    for name, old, new, what, want_node, want_msg in MUTS:
        n = ORIG.count(old)
        assert n == 1, f"{name}: 锚点命中 {n} 次"
        TGT.write_text(ORIG.replace(old, new), encoding="utf-8")
        r = subprocess.run([".venv/bin/pytest", "-q", "-p", "no:cacheprovider", str(TGT), "--tb=line", "-rfX"],
                           capture_output=True, text=True)
        out = r.stdout + r.stderr
        failed = FAIL_RE.findall(out)
        if want_node is None:      # T3: 期望大量 XPASS 导致失败
            ok = r.returncode != 0 and ("xpassed" in out or "XPASS" in out)
            detail = f"rc={r.returncode} | " + (
                [l for l in out.splitlines() if "passed" in l or "failed" in l][-1] if out else "?")
        elif want_node.startswith("IN:"):
            node = want_node[3:]
            hit = node in failed
            ok = r.returncode != 0 and hit and want_msg in out
            detail = (f"rc={r.returncode} | 表用例在失败集合里={'✓' if hit else '✗'} "
                      f"(共 {len(failed)} 条失败) | 消息{'✓' if want_msg in out else '✗'}")
        else:
            ok = r.returncode != 0 and failed == [want_node] and want_msg in out
            detail = (f"rc={r.returncode} | 失败节点={'✓' if failed == [want_node] else '✗ '+str(failed)}"
                      f" | 消息{'✓' if want_msg in out else '✗ 未见 '+repr(want_msg)}")
        results.append((name, ok, what, detail))
finally:
    TGT.write_text(ORIG, encoding="utf-8")

after = hashlib.sha256(TGT.read_text(encoding="utf-8").encode()).hexdigest()
print(f"还原对账: {'OK 逐字节相同' if after == BASE else '*** 未还原 ***'}  sha={BASE[:12]}\n")
bad = [n for n, ok, _, _ in results if not ok]
for name, ok, what, detail in results:
    print(f"  {'KILLED' if ok else 'SURVIVED':<9} {name}")
    print(f"            {what}")
    print(f"            {detail}")
sys.exit(1 if bad or after != BASE else 0)
