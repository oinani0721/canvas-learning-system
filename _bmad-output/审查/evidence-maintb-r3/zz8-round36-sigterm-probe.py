"""SIGTERM 防线的行为验证：等变异真的落到生产文件上，再发 SIGTERM，看还原有没有跑。

负控在同一脚本里：先用 SIG_DFL（默认处置）复现"变异体留在文件里"，
再用装了 handler 的版本证明它被还原 —— 两态都测，防"加了防线但其实是别的原因"。
"""
import hashlib, os, pathlib, signal, subprocess, sys, time

ROOT = pathlib.Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix")
TARGET = ROOT / "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py"
SCRIPT = ROOT / "backend/tests/regression/recap_domain_negverify.py"
PY = ROOT / "backend/.venv/bin/python"
TMP = pathlib.Path(sys.argv[1])

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

HEAD = subprocess.run(["git","show","HEAD:canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py"],
                      cwd=ROOT, capture_output=True).stdout
head_sha = hashlib.sha256(HEAD).hexdigest()
print(f"HEAD sha = {head_sha[:16]}")
assert sha(TARGET) == head_sha, "开跑前生产文件就不是 HEAD 态"

def run_case(label, disable_handler):
    # 每例开跑前清锁：被 SIGTERM 打断的上一例**没跑 finally**，锁会留下
    # （这本身就是同一个缺陷的第二个受害者——handler 装上后两处一起好）。
    lock = TMP / "recap-domain-negverify.lock.d"
    if lock.exists():
        os.rmdir(lock); print(f"  [{label}] 清掉上一例遗留的锁")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": str(TMP)}
    if disable_handler:
        env["NEGVERIFY_NO_SIGNAL_GUARD"] = "1"
    p = subprocess.Popen([str(PY), str(SCRIPT)], cwd=ROOT/"backend",
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    # 轮询直到生产文件真的被改（= 变异已落盘），最多等 240s
    mutated_at = None
    for _ in range(2400):
        time.sleep(0.1)
        if p.poll() is not None:
            print(f"  [{label}] 子进程提前退出 rc={p.returncode}"); return None
        try:
            if sha(TARGET) != head_sha:
                mutated_at = time.time(); break
        except OSError:
            pass
    if mutated_at is None:
        p.kill(); print(f"  [{label}] 240s 内没观察到变异落盘"); return None
    os.kill(p.pid, signal.SIGTERM)
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill(); p.wait()
    time.sleep(0.5)
    after = sha(TARGET)
    ok = after == head_sha
    lock_left = lock.exists()
    print(f"  [{label}] SIGTERM 后 sha={after[:16]} → {'已还原 ✅' if ok else '⛔ 变异体残留'}"
          f" | 锁{'残留 ⛔' if lock_left else '已清 ✅'}")
    if not ok:
        TARGET.write_bytes(HEAD); print(f"  [{label}] 已手工还原")
    return ok

print("\n=== 负控：禁掉 handler（应当残留，证明这道防线确实承重）===")
neg = run_case("no-guard", True)
print("\n=== 正例：handler 在位（应当还原）===")
pos = run_case("guarded", False)
print(f"\n判定: 负控残留={neg is False} / 正例还原={pos is True}"
      f" → {'✅ 防线承重' if (neg is False and pos is True) else '⛔ 未证明'}")
