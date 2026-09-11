#!/usr/bin/env python3
"""U3-A 两条 HIGH 的门承重验证：拆掉修复本身，指定那条门必须红。"""
import hashlib, subprocess, sys
from pathlib import Path
WT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy")
V, PYTEST, FILE = WT / "scripts/verify_vault_install.py", WT / "backend/.venv/bin/pytest", "tests/unit/test_vault_install_manifest.py"

MUT = [
    ("M-u3a-H1", '''        kind = _resolved_kind(path)
        if kind == "unreadable":
            return None
        return kind == "file"''', "        return path.is_file()",
     "test_kind_file_reports_unreadable_when_symlink_target_is_unqueryable", "链目标查不到必须登记 unreadable"),
    ("M-u3a-H2", '''    if stat.S_ISCHR(st.st_mode) or stat.S_ISBLK(st.st_mode):''', '''    if False:''',
     "test_device_nodes_of_same_type_do_not_collide", "两个不同的字符设备摘要相同"),
]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
orig, base_sha = V.read_bytes(), sha(V)
print("跑前 sha:", base_sha[:12])
results = []
try:
    for name, old, new, node, msg in MUT:
        s = V.read_text(encoding="utf-8")
        assert s.count(old) == 1, f"{name} 锚命中 {s.count(old)}"
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
