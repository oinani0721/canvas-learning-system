#!/usr/bin/env python3
"""跨车道语义等价核验 v2（r3 H-3 修复）。

按后缀选择比较口径（均双端同口径；无法结构化则字节比较）：
  .py     → ast.dump(ast.parse)  相等
  .yaml/.yml → yaml.safe_load 结构相等
  .json   → json.loads 结构相等
  .ini/.cfg  → configparser 结构相等
  .sh     → `bash -n` 双端语法 OK + 去注释/空行后的行序列相等（换行边界保留）
  其它     → 字节相等
输出：每 lane 先打印 tip SHA；末行 verdict=PASS/FAIL(n)。声明例外（多写者并集面）单列。
"""
import ast, configparser, io, json, subprocess, sys, tempfile, os

W = "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees"
BASE = "9c4e7e82"
C = sys.argv[1] if len(sys.argv) > 1 else f"{W}/batch15-integ"
LANES = {f"p{i}": d for i, d in enumerate(
    ["p1-storage","p2-outbox","p3-deploy","p4-fsrs","p5-review",
     "p6-skills-w","p7-skills-x","p8-backend","p9-testinfra","p10-docs"], 1)}
EXCEPTIONS = {
    "backend/app/clients/neo4j_client.py": "多写者并集面（P1×P2）",
    "backend/app/services/memory_service.py": "多写者并集面（P1×P2）",
    "backend/app/services/episode_worker.py": "多写者并集面（P1×P2）",
    "backend/app/graphiti/canvas_episode.py": "多写者并集面",
    "backend/tests/unit/test_neo4j_client.py": "多写者并集面",
    "docs/release-evidence/README.md": "多写者并集面（P5/P10）",
}

def run(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True).stdout

def blob(cwd, ref, path):
    return subprocess.run(["git", "show", f"{ref}:{path}"], cwd=cwd, capture_output=True).stdout

def _try(fn, b):
    try:
        return fn(b)
    except Exception:
        return None

def equiv(path, a, b):
    if a == b:
        return "BYTES"
    if path.endswith(".py"):
        na = _try(lambda x: ast.dump(ast.parse(x.decode("utf-8"))), a)
        nb = _try(lambda x: ast.dump(ast.parse(x.decode("utf-8"))), b)
        return "AST" if (na is not None and na == nb) else None
    if path.endswith((".yaml", ".yml")):
        import yaml
        na = _try(lambda x: yaml.safe_load(x.decode("utf-8")), a)
        nb = _try(lambda x: yaml.safe_load(x.decode("utf-8")), b)
        return "YAML" if (na is not None and na == nb) else None
    if path.endswith(".json"):
        na = _try(lambda x: json.loads(x.decode("utf-8")), a)
        nb = _try(lambda x: json.loads(x.decode("utf-8")), b)
        return "JSON" if (na is not None and na == nb) else None
    if path.endswith((".ini", ".cfg")):
        def _ini(x):
            cp = configparser.ConfigParser()
            cp.read_string(x.decode("utf-8"))
            return {s: dict(cp.items(s)) for s in cp.sections()}
        na, nb = _try(_ini, a), _try(_ini, b)
        return "INI" if (na is not None and na == nb) else None
    if path.endswith(".sh"):
        def _syntax(x):
            with tempfile.NamedTemporaryFile("wb", suffix=".sh", delete=False) as f:
                f.write(x); p = f.name
            rc = subprocess.run(["bash", "-n", p], capture_output=True).returncode
            os.unlink(p)
            return rc == 0
        if not (_syntax(a) and _syntax(b)):
            return None
        def _lines(x):
            out = []
            for ln in x.decode("utf-8", "replace").splitlines():
                s = ln.strip()
                if not s or s.startswith("#"):
                    continue
                out.append(s)
            return out
        return "SH" if _lines(a) == _lines(b) else None
    return None

equiv_n = exc_n = diff_n = 0
print(f"# candidate={C} head={run(['rev-parse','--short=8','HEAD'],C).decode().strip()}")
for lane, d in LANES.items():
    L = f"{W}/card-{d}"
    tip_full = run(["rev-parse", "HEAD"], L).decode().strip()
    tip = tip_full[:8]
    files = [f for f in run(["diff", "--name-only", "-z", f"{BASE}..HEAD", "--", ".", ":(exclude)_bmad-output"], L).decode("utf-8","surrogateescape").split("\0") if f]
    print(f"## {lane} tip={tip} files={len(files)}")
    for f in files:
        a = blob(C, "HEAD", f); b = blob(L, "HEAD", f)
        how = equiv(f, a, b)
        if how:
            equiv_n += 1
        elif f in EXCEPTIONS:
            exc_n += 1
            print(f"  [EXCEPTION] {f} —— {EXCEPTIONS[f]}")
        else:
            diff_n += 1
            print(f"  [DIFF] {f}（无声明例外，需归因）")
total = equiv_n + exc_n + diff_n
print(f"\nchecked={total} equiv={equiv_n} exceptions={exc_n} undecided_diff={diff_n}")
print(f"verdict={'PASS' if diff_n == 0 else 'FAIL(' + str(diff_n) + ')'}")
