"""CARD-G6-7 round-1 整改的承重验证: 每条修复各造一个「退回缺陷」的变异体,
断言**指定的那道门**变红, 且红在**指定的那条断言**上 (不是别处红了也算)。
还原无条件 (finally), 跑完逐文件比对 sha —— 变异体绝不许留在生产文件里。
"""
import hashlib
import subprocess
import sys
from pathlib import Path

W = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b")
BE = W / "backend"
PYTEST = str(BE / ".venv" / "bin" / "pytest")

RUN = W / "scripts" / "daily_review_run.py"
OV = BE / "app" / "api" / "v1" / "endpoints" / "review_overview.py"
APP = BE / "app" / "api" / "v1" / "endpoints" / "review_app.py"
TOV = BE / "tests" / "unit" / "test_review_overview.py"
TARGETS = [RUN, OV, APP, TOV]
BASE_SHA = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in TARGETS}

MUTANTS = [
    ("M1 save_state 退回「跟随软链的 write_text」", RUN,
     "    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)",
     "    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)",
     "tests/unit/test_review_overview.py::test_g67_state_write_refuses_preplanted_symlink_at_tmp_path",
     "节点被写动了"),
    ("M2 _load_runner 退回「加载时写字节码」", OV,
     "        prev_dont_write = sys.dont_write_bytecode\n        sys.dont_write_bytecode = True\n",
     "        prev_dont_write = sys.dont_write_bytecode\n",
     "tests/unit/test_review_overview.py::test_g67_cold_load_of_runner_writes_no_bytecode",
     "读路径的模块加载写出了字节码"),
    ("M3 ensure_payload 退回「完成账不影响缓存」", RUN,
     "    done_unchanged = cached_sig == done_sig or (cached_sig is None and not st.get(\"board_done\"))",
     "    done_unchanged = True",
     "tests/regression/test_daily_review_run.py::test_g67_marking_done_invalidates_same_day_cache",
     "标完成后必须重扫"),
    ("M4 onBoardDoneClick 退回「不作废旧刷新 pending」", APP,
     "  delete state.pendingSync[vid];\n  state.doneInflight[key] = true;",
     "  state.doneInflight[key] = true;",
     "tests/unit/test_review_app.py::test_js_g67_stale_refresh_settlement_cannot_overwrite_done_feedback",
     "旧刷新的结算把完成失败改写掉了"),
    ("M5 _fsrs_fingerprint 退回「逐行取 fsrs_ 前缀」", TOV,
     """        raw = md.read_bytes()
        rows = raw.split(b"\\n")""",
     """        raw = md.read_text(encoding="utf-8").encode("utf-8")
        rows = [ln.encode("utf-8") for ln in md.read_text(encoding="utf-8").splitlines()]
        block = [ln for ln in rows if ln.startswith(b"fsrs_")]
        fm[md.name] = ["nosha", *(x.decode("utf-8") for x in block)]
        continue
        rows = raw.split(b"\\n")""",
     "tests/unit/test_review_overview.py::test_g67_fsrs_fingerprint_catches_boundary_and_crlf",
     "DID NOT RAISE"),
]

results = []
for name, path, old, new, nodeid, expect in MUTANTS:
    src = path.read_text(encoding="utf-8")
    if src.count(old) != 1:
        results.append((name, "ANCHOR-MISS", f"锚点命中 {src.count(old)} 次"))
        continue
    path.write_text(src.replace(old, new), encoding="utf-8")
    try:
        # 编译自检: 语法坏掉的变异体会让门因**别的**原因红 = 假杀
        if path.suffix == ".py":
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except SyntaxError as e:
                results.append((name, "SYNTAX-INVALID", str(e)))
                continue
        r = subprocess.run(
            [PYTEST, "-q", "-p", "no:cacheprovider", nodeid, "--tb=line", "-W", "ignore::DeprecationWarning"],
            cwd=BE, capture_output=True, text=True, timeout=300,
            env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": ""},
        )
        out = r.stdout + r.stderr
        if r.returncode == 0:
            results.append((name, "SURVIVED", "门没红 — 这条修复没有承重的门"))
        elif expect in out:
            results.append((name, "KILLED", f"红在指定断言上: {expect!r}"))
        else:
            results.append((name, "KILLED-WRONG-REASON", f"红了但不含 {expect!r}"))
    finally:
        path.write_text(src, encoding="utf-8")

print("=" * 70)
for name, verdict, why in results:
    print(f"{verdict:22} {name}\n{'':22} {why}")
print("=" * 70)
bad = [p.name for p in TARGETS if hashlib.sha256(p.read_bytes()).hexdigest() != BASE_SHA[p]]
print("跑后与跑前 sha 不同的文件 (须为空):", bad)
sys.exit(0 if not bad and all(v == "KILLED" for _, v, _ in results) else 1)
