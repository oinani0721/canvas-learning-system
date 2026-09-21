#!/usr/bin/env python3
"""跨车道语义等价核验 v2.5.1（v2.5 + r15-L1：.sh 的 bash -n 前置为硬门 + shell 描述修正 + 版本标签同步）。

按后缀选择比较口径（均双端同口径；无法结构化则字节比较）：
  .py     → ast.dump(ast.parse)  相等
  .yaml/.yml → yaml.safe_load 结构相等
  .json   → json.loads 结构相等
  .ini/.cfg  → configparser 结构相等
  .sh     → 先 `bash -n` 双端语法 OK（硬门：失败即 [sh-syntax] 红，不再短路）；再字节相等（相同字节=SH，不同字节=不等价）
  其它     → 字节相等
输出：每 lane 先打印 tip SHA；末行 verdict=PASS/FAIL(n)。声明例外（多写者并集面）单列。
"""
import ast, configparser, hashlib, io, json, subprocess, sys, tempfile, os
from pathlib import Path

W = "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees"
BASE = "deadbeef"
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
    # r14-M2：J07 manifest 不再走“路径级”通用例外——改由 closeout_exception_ok() 内容谓词限定（仅允许 notes 变更）
}

# r5-H1 修复（fail-closed 三件套）：
#  ① 所有 git 子命令 rc!=0 ⇒ 记 git-fail（不再把空 stdout 当结果）；
#  ② 逐 lane code-face pin（r3 对比轮 tip）：pin..HEAD 的非 _bmad-output 面必须为空，否则 [CODE-DRIFT]；
#     P3 lane 冻结后的 docs-only 前进属 B15 显式排除面（见 b15-freeze-exclusions.json），代码面不动即容忍；
#  ③ 计数下限：每 lane files>0 且 checked>=100，否则红（防空枚举 vacuous PASS）；末尾以退出码传播 verdict。
J07_MANIFEST = "docs/release-evidence/dev-b15-p5/journeys/J07/manifest.json"

def closeout_exception_ok(path, a, b):
    """r14-M2：收口期修正例外的内容谓词——J07 manifest 仅允许 `notes` 键变更；
    其它键/解析失败/非本路径 ⇒ False（fail-closed）。"""
    if path != J07_MANIFEST:
        return False
    try:
        ja = json.loads(a.decode("utf-8"))
        jb = json.loads(b.decode("utf-8"))
    except Exception:
        return False
    if not (isinstance(ja, dict) and isinstance(jb, dict)):
        return False
    keys = set(ja) | set(jb)
    changed = [k for k in sorted(keys) if ja.get(k) != jb.get(k)]
    return changed == ["notes"]

CODE_TIPS = {  # r7-M1：40-hex 全 SHA（禁止 8 位前缀比较）
    "p1": "39144558946094707a5223e4cedbf599e73b2ba7",
    "p2": "ac52e3b8ad7ecaca540153722f7b6aa9d050462e",
    "p3": "32a405a4695cf0f9a63e44a80a7c7fa9c3e84e67",  # 记录值=对比轮车道 tip；P3 属登记排除面（当前 docs-drift 至 1726b695）
    "p4": "aa126e5bbc70cb786b7b49adf5c8ad03b04166c3",
    "p5": "7af5306b3b28764574895aa5b38d952474e01b69",
    "p6": "6346facb8d367f7b3d282e77569cae11289351d9",
    "p7": "eb79868003915e730590a452fbc482913ed9f00c",
    "p8": "447eb50fc25b333362d76ecfb59458a2aa79f57d",
    "p9": "430dcf25501b48887f4ad05ebfc134e16e4c78a9",
    "p10": "d2db49afe15b047e3622519ec5f460c5ff3d44cc",
}
failures = []

def run_checked(args, cwd):
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True)
    if p.returncode != 0:
        failures.append(f"git-fail: git {' '.join(args)} @ {cwd} rc={p.returncode} err={p.stderr.decode('utf-8','replace')[:200]}")
        return b""
    return p.stdout

REGISTRY = os.environ.get("SEM_REGISTRY", os.path.join(os.path.dirname(os.path.abspath(__file__)), "b15-freeze-exclusions.json"))

def empty_failure(path, a, b):
    """r6-H1：零字节 blob 不作等价证据（两侧同空也不行）——任一侧为空即红。"""
    if a == b"" or b == b"":
        return f"empty-blob: {path} candidate_len={len(a)} lane_len={len(b)}（零字节 blob 不作等价证据）"
    return None

def load_allowed_drift():
    """r6-M1：从冻结登记解析「允许 docs-only 前进」的 lane 集合；未登记车道必须 tip 精确相等。"""
    try:
        with open(REGISTRY, encoding="utf-8") as fh:
            reg = json.load(fh)
    except Exception as exc:
        failures.append(f"registry-missing: {REGISTRY}（{type(exc).__name__}: {exc}）")
        return None
    allowed = set()
    for face in reg.get("excluded_faces", []):
        wt = (face.get("worktree") or "").strip()
        for lane, d in LANES.items():
            if wt in (d, f"card-{d}"):
                allowed.add(lane)
    if not allowed:
        failures.append("registry-empty: 排除面为空（无法证明任何 docs-only 容忍的合法性）")
        return None
    return allowed

def run_self_test():
    """--self-test：表驱动自证（空 blob 判定 + shell 字节级口径 + J07 内容谓词）。"""
    ok = True
    cases = [
        ("both-empty", b"", b"", True),
        ("one-empty", b"x", b"", True),
        ("both-nonempty-equal", b"x", b"x", False),
    ]
    for name, a, b, must_fail in cases:
        got = empty_failure(f"self-test/{name}", a, b) is not None
        if got != must_fail:
            ok = False
        print(f"[self-test] {name}: must_fail={must_fail} got={got} -> {'OK' if got == must_fail else 'BAD'}")
    sh_same = b'cat <<PY\n    sys.exit(4)\nPY\n'
    sh_dedent = b'cat <<PY\nsys.exit(4)\nPY\n'
    sh_eq = equiv("self-test/x.sh", sh_same, sh_same) == "SH"
    sh_broken = b"if true; then\n"
    sh_broken_gate = sh_gate_ok(sh_broken, sh_broken) is False   # 相同字节但语法损坏 ⇒ 硬门必须红
    print(f"[self-test] sh-broken-identical: expect=gate-blocked got={sh_broken_gate} -> {'OK' if sh_broken_gate else 'BAD'}")
    ok = ok and sh_broken_gate
    sh_dedent_caught = equiv("self-test/x.sh", sh_same, sh_dedent) is None
    print(f"[self-test] sh-bytes-equal: expect=True got={sh_eq} -> {'OK' if sh_eq else 'BAD'}")
    print(f"[self-test] sh-heredoc-dedent: expect=not-equivalent got={sh_dedent_caught} -> {'OK' if sh_dedent_caught else 'BAD'}")
    ok = ok and sh_eq and sh_dedent_caught
    j_notes = json.dumps({"notes": "x"}, ensure_ascii=False).encode()
    j_notes2 = json.dumps({"notes": "y"}, ensure_ascii=False).encode()
    j_other = json.dumps({"notes": "x", "result": "partial"}, ensure_ascii=False).encode()
    j_other2 = json.dumps({"notes": "x", "result": "pass"}, ensure_ascii=False).encode()
    p1 = closeout_exception_ok(J07_MANIFEST, j_notes, j_notes2) is True
    p2 = closeout_exception_ok(J07_MANIFEST, j_other, j_other2) is False
    p3 = closeout_exception_ok("docs/other.json", j_notes, j_notes2) is False
    for nm, got in [("j07-notes-only", p1), ("j07-other-key-rejected", p2), ("j07-path-scoped", p3)]:
        print(f"[self-test] {nm}: got={got} -> {'OK' if got else 'BAD'}")
    ok = ok and p1 and p2 and p3
    return ok

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

def sh_gate_ok(a, b):
    """r15-L1：.sh 语法硬门——双端 bash -n 必须通过（相同字节也检查）。"""
    return sh_syntax_ok(a) and sh_syntax_ok(b)

def sh_syntax_ok(x):
    with tempfile.NamedTemporaryFile("wb", suffix=".sh", delete=False) as f:
        f.write(x); p = f.name
    try:
        return subprocess.run(["bash", "-n", p], capture_output=True).returncode == 0
    finally:
        os.unlink(p)

def _try(fn, b):
    try:
        return fn(b)
    except Exception:
        return None

def equiv(path, a, b):
    if path.endswith(".sh"):
        # r15-L1：.sh 不走字节短路——先语法门（由调用方 sh_gate_ok 判定），此处仅做字节相等
        return "SH" if a == b else None
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
    return None

equiv_n = exc_n = diff_n = missing_n = empty_n = lane_empty_n = 0
ALLOWED_DRIFT = load_allowed_drift()
if "--self-test" in sys.argv:
    ok = run_self_test()
    print(f"self_test={'PASS' if ok else 'FAIL'}")
    raise SystemExit(0 if ok else 1)
print(f"# candidate={C} head={run_checked(['rev-parse','--short=8','HEAD'],C).decode().strip()}")
print(f"# script_sha256={hashlib.sha256(Path(__file__).read_bytes()).hexdigest()} version=v2.5.1")
for lane, d in LANES.items():
    L = f"{W}/card-{d}"
    tip_full = run_checked(["rev-parse", "HEAD"], L).decode().strip()
    tip = tip_full[:8]
    pin = CODE_TIPS.get(lane, "")
    if not pin:
        failures.append(f"pin-missing: {lane} CODE_TIPS 缺键（fail-closed）")
    elif len(pin) != 40 or any(c not in "0123456789abcdef" for c in pin):
        failures.append(f"pin-invalid: {lane} pin={pin!r} 非 40-hex 全 SHA（r7-M1 fail-closed）")
    drift = [x for x in run_checked(["diff", "--name-only", f"{pin}..HEAD", "--", ".", ":(exclude)_bmad-output"], L).decode("utf-8","surrogateescape").splitlines() if x]
    tip_drift = bool(pin) and tip_full != pin
    if ALLOWED_DRIFT is not None and lane in ALLOWED_DRIFT:
        if drift:
            failures.append(f"code-drift: {lane} {pin}..{tip} 非 _bmad-output 面 {len(drift)} 文件: {drift[:3]}")
        elif tip_drift:
            print(f"  [DOCS-DRIFT-ALLOWED] {lane} {pin}..{tip}（登记排除面；代码面零漂移）")
    else:
        if tip_drift:
            failures.append(f"tip-drift: {lane} tip={tip_full} != pin={pin}（未登记排除面的车道必须 tip 精确相等）")
        if drift:
            failures.append(f"code-drift: {lane} {pin}..{tip} 非 _bmad-output 面 {len(drift)} 文件: {drift[:3]}")
    files = [f for f in run_checked(["diff", "--name-only", "-z", f"{BASE}..HEAD", "--", ".", ":(exclude)_bmad-output"], L).decode("utf-8","surrogateescape").split("\0") if f]
    if not files:
        lane_empty_n += 1
        failures.append(f"lane-empty: {lane} tip={tip} 枚举 0 文件（防空枚举 vacuous PASS）")
    print(f"## {lane} tip={tip_full[:8]} pin={pin[:8]} full_pin_ok={(tip_full == pin)} code_drift={len(drift)} files={len(files)}")
    for f in files:
        ok_c, a = blob_checked(C, "HEAD", f); ok_l, b = blob_checked(L, "HEAD", f)
        if not (ok_c and ok_l):
            missing_n += 1
            print(f"  [MISSING] {f}（cat-file -e rc!=0：candidate_ok={ok_c} lane_ok={ok_l}）")
            continue
        if f.endswith(".sh") and not sh_gate_ok(a, b):
            failures.append(f"sh-syntax: {f} 双端 bash -n 未通过（r15-L1 硬门）")
            print(f"  [SH-SYNTAX] {f}（bash -n 失败 ⇒ 红）")
            continue
        ef = empty_failure(f, a, b)
        if ef:
            empty_n += 1
            failures.append(ef)
            print(f"  [EMPTY] {f}（candidate_len={len(a)} lane_len={len(b)}）")
            continue
        how = equiv(f, a, b)
        if how:
            equiv_n += 1
        elif closeout_exception_ok(f, a, b):
            exc_n += 1
            print(f"  [EXCEPTION] {f} —— B15 收口期修正（内容谓词：仅 notes；r14-M2）")
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
clean = (not failures) and diff_n == 0 and missing_n == 0 and empty_n == 0
print(f"\nchecked={total} equiv={equiv_n} exceptions={exc_n} undecided_diff={diff_n} missing={missing_n} empty={empty_n} lane_empty={lane_empty_n} failures={len(failures)}")
print(f"verdict={'PASS' if clean else 'FAIL'}")
raise SystemExit(0 if clean else 1)
