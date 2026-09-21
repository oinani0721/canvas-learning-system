#!/usr/bin/env python3
"""跨车道语义等价核验 v2.2（r3 H-3 + r4-L2 + r5-H1：Git rc 检查 + 退出码传播 + code-face pin + 计数下限）。

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

# r5-H1 修复（fail-closed 三件套）：
#  ① 所有 git 子命令 rc!=0 ⇒ 记 git-fail（不再把空 stdout 当结果）；
#  ② 逐 lane code-face pin（r3 对比轮 tip）：pin..HEAD 的非 _bmad-output 面必须为空，否则 [CODE-DRIFT]；
#     P3 lane 冻结后的 docs-only 前进属 B15 显式排除面（见 b15-freeze-exclusions.json），代码面不动即容忍；
#  ③ 计数下限：每 lane files>0 且 checked>=100，否则红（防空枚举 vacuous PASS）；末尾以退出码传播 verdict。
CODE_TIPS = {
    "p1": "39144558", "p2": "ac52e3b8", "p3": "32a405a4", "p4": "aa126e5b", "p5": "7af5306b",
    "p6": "6346facb", "p7": "eb798680", "p8": "447eb50f", "p9": "430dcf25", "p10": "d2db49af",
}
failures = []

def run_checked(args, cwd):
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True)
    if p.returncode != 0:
        failures.append(f"git-fail: git {' '.join(args)} @ {cwd} rc={p.returncode} err={p.stderr.decode('utf-8','replace')[:200]}")
        return b""
    return p.stdout

def run(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True).stdout

def blob_checked(cwd, ref, path):
    """r4-L2 修复：先 `git cat-file -e <ref>:<path>` 断言路径存在，再取 blob；
    任一 git 子命令失败 ⇒ ok=False（不把“路径缺失”与“空 blob”混同为 b''）。"""
    exists = subprocess.run(["git", "cat-file", "-e", f"{ref}:{path}"], cwd=cwd, capture_output=True)
    if exists.returncode != 0:
        return False, b""
    show = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=cwd, capture_output=True)
    if show.returncode != 0:
        return False, b""
    return True, show.stdout

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

equiv_n = exc_n = diff_n = missing_n = empty_n = lane_empty_n = 0
print(f"# candidate={C} head={run_checked(['rev-parse','--short=8','HEAD'],C).decode().strip()}")
for lane, d in LANES.items():
    L = f"{W}/card-{d}"
    tip_full = run_checked(["rev-parse", "HEAD"], L).decode().strip()
    tip = tip_full[:8]
    pin = CODE_TIPS.get(lane, "")
    drift = [x for x in run_checked(["diff", "--name-only", f"{pin}..HEAD", "--", ".", ":(exclude)_bmad-output"], L).decode("utf-8","surrogateescape").splitlines() if x]
    if pin and drift:
        failures.append(f"code-drift: {lane} {pin}..{tip} 非 _bmad-output 面 {len(drift)} 文件: {drift[:3]}")
    files = [f for f in run_checked(["diff", "--name-only", "-z", f"{BASE}..HEAD", "--", ".", ":(exclude)_bmad-output"], L).decode("utf-8","surrogateescape").split("\0") if f]
    if not files:
        lane_empty_n += 1
        failures.append(f"lane-empty: {lane} tip={tip} 枚举 0 文件（防空枚举 vacuous PASS）")
    print(f"## {lane} tip={tip} pin={pin} code_drift={len(drift)} files={len(files)}")
    for f in files:
        ok_c, a = blob_checked(C, "HEAD", f); ok_l, b = blob_checked(L, "HEAD", f)
        if not (ok_c and ok_l):
            missing_n += 1
            print(f"  [MISSING] {f}（cat-file -e rc!=0：candidate_ok={ok_c} lane_ok={ok_l}）")
            continue
        if a == b"" or b == b"":
            empty_n += 1
            print(f"  [EMPTY] {f}（零字节 blob：candidate_len={len(a)} lane_len={len(b)}）")
        how = equiv(f, a, b)
        if how:
            equiv_n += 1
        elif f in EXCEPTIONS:
            exc_n += 1
            print(f"  [EXCEPTION] {f} —— {EXCEPTIONS[f]}")
        else:
            diff_n += 1
            print(f"  [DIFF] {f}（无声明例外，需归因）")
total = equiv_n + exc_n + diff_n + missing_n
if total < 100:
    failures.append(f"count-guard: checked={total} < 100（防空枚举）")
for _f in failures:
    print(f"[FAIL] {_f}")
clean = (not failures) and diff_n == 0 and missing_n == 0
print(f"\nchecked={total} equiv={equiv_n} exceptions={exc_n} undecided_diff={diff_n} missing={missing_n} empty={empty_n} lane_empty={lane_empty_n} failures={len(failures)}")
print(f"verdict={'PASS' if clean else 'FAIL'}")
raise SystemExit(0 if clean else 1)
