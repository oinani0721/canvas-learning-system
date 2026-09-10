#!/usr/bin/env python3
"""U3-A r6 两条修复的门承重验证。"""
import hashlib, subprocess, sys
from pathlib import Path
WT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy")
V, PYTEST, FILE = WT / "scripts/verify_vault_install.py", WT / "backend/.venv/bin/pytest", "tests/unit/test_vault_install_manifest.py"
MUT = [
    # HIGH: 撤掉 extra 消费端的三态透传（回到不传 unreadable）
    ("M-u3a6-H", "        return excluder.is_under_exclusion(vault, rel, kind_unreadable)",
     "        return excluder.is_under_exclusion(vault, rel)",
     "test_extra_scan_propagates_kind_unqueryable_instead_of_allowing", "类型判不了必须登记 unreadable"),
    # HIGH 第二层: 保留透传但只 continue、不登记（缺陷从「放行」变「静默跳过」）
    ("M-u3a6-H2", '''                report.unreadable.append(
                    Finding(
                        path=rel,
                        category="unreadable",
                        action="exclude",
                        role="-",
                        detail="类型条件判不了 (跟随软链后查询失败), 无法证明它该被排除还是清单外",
                    )
                )
                continue''', "                continue",
     "test_extra_scan_propagates_kind_unqueryable_instead_of_allowing", "类型判不了必须登记 unreadable"),
    # MEDIUM: 撤掉 absent 短路（回到我上一轮那个误报）
    ("M-u3a6-M1", '''        if state == "absent":
            # 但**不存在**是确定的否定答案, 不是「问不出来」: 不存在的东西不满足「是文件」。
            # `_resolved_kind` 只有四态、把 ENOENT/ENOTDIR 一律归 unreadable, 直接拿它
            # 判 absent 会把「这条 exclude 本就不在目标里」误报成读取失败(round-6 MEDIUM)。
            return False
''', "",
     "test_absent_exclude_with_kind_file_is_not_reported_unreadable", "不存在的 exclude 项不得报成读取失败"),
]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
orig, base_sha = V.read_bytes(), sha(V)
print("跑前 sha:", base_sha[:12])
results = []
try:
    for name, old, new, node, msg in MUT:
        s = V.read_text(encoding="utf-8")
        if s.count(old) != 1:
            results.append((name, "SYNTAX-INVALID", f"锚命中 {s.count(old)}")); continue
        V.write_text(s.replace(old, new, 1), encoding="utf-8")
        assert sha(V) != base_sha, f"{name} 变异未生效"
        r = subprocess.run([str(PYTEST), "-q", "-p", "no:cacheprovider", f"{FILE}::{node}"], cwd=WT / "backend",
                           capture_output=True, text=True,
                           env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(Path.home())})
        elines = [l for l in r.stdout.splitlines() if l.startswith("E ")]
        hit = any(msg in l for l in elines)
        verdict = "KILLED" if (r.returncode != 0 and hit) else ("SURVIVED" if r.returncode == 0 else "KILLED-OTHER")
        results.append((name, verdict, next((l.strip()[:95] for l in elines if msg in l), (elines[0].strip()[:95] if elines else "无 E 行"))))
        V.write_bytes(orig)
finally:
    V.write_bytes(orig); assert sha(V) == base_sha, "还原失败"
    print("还原后 sha 一致 ✅")
for n, vd, d in results: print(f"{vd:14s} {n}  {d}")
sys.exit(0 if all(vd == "KILLED" for _, vd, _ in results) else 1)
