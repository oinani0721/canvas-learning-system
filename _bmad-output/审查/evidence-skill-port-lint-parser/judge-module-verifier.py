"""⚠️ 本脚本会**临时改写**被测模块（结束前用 try/finally + sha 核对还原）。
   重跑前请确认同树没有别的 pytest 长跑在进行（变异窗口不得与长跑重叠）。

(b) 模块依赖验伪锚：改坏**模块**里的判据 → 指定正控必红 → 还原 → 回绿。

⛔ 变异方向只能是「让 check_* 返回**非空** problems」——两条正控的断言都是
   `assert not problems`，判据恒返 [] 只会让它们更绿（假绿），卡文点名禁用。
还原用 finally + 逐字节 sha 核对，保证变异窗口不外溢。
"""

import hashlib, shutil, subprocess, sys
from pathlib import Path

W = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills")
MOD = W / "backend/tests/skills/skill_portability_lint.py"
BAK = Path(__file__).resolve().parent / "_module.bak"  # 脚本同目录，复核者可直接重跑


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


NODES = ["test_layer2_body_counts_match_baseline", "test_managed_files_match_digest_baseline"]
ARGS = ["-q", "-p", "no:cacheprovider"] + [f"tests/skills/test_skill_portability_lint.py::{n}" for n in NODES]


def run():
    return subprocess.run(
        [".venv/bin/python", "-m", "pytest", *ARGS], cwd=W / "backend", capture_output=True, text=True
    )


PRE = sha(MOD)
print(f"module sha PRE  = {PRE}")
shutil.copy2(MOD, BAK)

MUTS = [
    (
        '    """层 2: 返回违规描述列表 (空 = 全绿)。每条含 skill + 指标 + 期望 + 实测。"""',
        '    return ["forced-drift-check_body"]',
        "check_body",
    ),
    (
        '    """第十一条判据: 受管文件集合与整文件摘要**精确相等**。"""',
        '    return ["forced-drift-check_managed_files"]',
        "check_managed_files",
    ),
]
try:
    src = MOD.read_text(encoding="utf-8")
    for anchor, inject, who in MUTS:
        assert src.count(anchor) == 1, f"锚点 {who} 命中 {src.count(anchor)} 次，非唯一"
        src = src.replace(anchor, anchor + "\n" + inject)
    MOD.write_text(src, encoding="utf-8")
    print(f"module sha MUT  = {sha(MOD)}  (已注入 2 处 return 非空 problems)")

    r = run()
    out = r.stdout + r.stderr
    print(f"\n----- 变异轮 pytest rc={r.returncode} -----")
    print(out[-2600:])
    hits = {
        k: out.count(k)
        for k in ("正文指标基线漂移", "受管文件基线漂移", "forced-drift-check_body", "forced-drift-check_managed_files")
    }
    print("\n断言身份 grep:", hits)
    red_ok = (
        r.returncode != 0
        and hits["正文指标基线漂移"] >= 1
        and hits["受管文件基线漂移"] >= 1
        and hits["forced-drift-check_body"] >= 1
        and hits["forced-drift-check_managed_files"] >= 1
    )
    print(
        "变异轮判定:",
        "红在指定断言身份上 ✓" if red_ok else "⛔ 未红/红错地方 = 抽出是假的（test 仍在用文件内旧副本），停下重做",
    )
finally:
    shutil.copy2(BAK, MOD)
    POST = sha(MOD)
    print(f"\nmodule sha POST = {POST}")
    print("还原逐字节相同:", PRE == POST)
    BAK.unlink(missing_ok=True)  # 不留备份垃圾在库内（.bak 未被 .gitignore 覆盖）

r2 = run()
print(f"\n----- 还原轮 pytest rc={r2.returncode} -----")
print((r2.stdout + r2.stderr)[-700:])
ok = red_ok and PRE == POST and r2.returncode == 0
print("\nRESULT:", "PASS (b) 模块依赖验伪锚成立" if ok else "FAIL")
sys.exit(0 if ok else 1)
