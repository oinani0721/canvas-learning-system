"""负控：复现 Codex R1 轮 MEDIUM 的三重破坏，验证强化后的探针会变红。

MEMORY reference_mutation_must_disable_all_layers —— 只破坏一层可能被别的
断言兜住，判断不出「这一条断言」是否承重。故三处**各自单独**破坏一次，
再叠加破坏一次，逐一记录探针是否变红。
"""
import subprocess, sys
from pathlib import Path

LANE = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard")
SRC = (LANE / "scripts" / "daily_review_pick.py").read_text(encoding="utf-8")
PROBE = LANE / "_bmad-output" / "审查" / "evidence-g36b-r1" / "g36b_r1_recheck.py"
OUT = Path(sys.argv[1])

BREAKS = {
    # (1) 破坏精确回落值：半份配置时把缺失叶键回落成 0 而不是内置默认
    "回落值不精确": (
        '                print(f"[pick] estimated_minutes.{k} 缺失或非法({v!r}), 用内置默认 {minutes[k]}",\n'
        '                      file=sys.stderr)',
        '                minutes[k] = 0\n'
        '                print(f"[pick] estimated_minutes.{k} 缺失或非法({v!r}), 用内置默认 {minutes[k]}",\n'
        '                      file=sys.stderr)',
    ),
    # (2) implementation SHA 固定为零（算了但不接入真实字节）
    "impl_sha 固定为零": (
        '        "implementation_sha256": _implementation_sha(),',
        '        "implementation_sha256": "0" * 64,',
    ),
    # (3) payload 忽略 manifest 分钟（读出来却不往下传）
    "payload 忽略 manifest 分钟": (
        '    ranked, upcoming, unassigned = rank_boards(nodes, board_last_recommended, now, minutes)',
        '    ranked, upcoming, unassigned = rank_boards(nodes, board_last_recommended, now, None)',
    ),
}

def run(src: str, label: str) -> tuple[bool, str]:
    f = OUT / f"broken_{abs(hash(label))}.py"
    f.write_text(src, encoding="utf-8")
    r = subprocess.run([str(LANE / "backend" / ".venv" / "bin" / "python"), str(PROBE), str(f)],
                       capture_output=True, text=True,
                       env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
                            "HOME": str(Path.home()), "LANG": "en_US.UTF-8"})
    fails = [l for l in r.stdout.splitlines() if l.startswith("[FAIL]")]
    return (r.returncode != 0), (fails[0][:120] if fails else (r.stdout or r.stderr)[-160:])

print("═══ 逐项单独破坏 ═══")
all_caught = True
for label, (old, new) in BREAKS.items():
    assert SRC.count(old) == 1, f"{label} 锚点命中 {SRC.count(old)} 次"
    caught, detail = run(SRC.replace(old, new, 1), label)
    all_caught &= caught
    print(f"[{'✅ 被抓' if caught else '⛔ 漏网'}] {label}\n        {detail}")

print("\n═══ 三处叠加破坏（Codex 原始手法）═══")
src = SRC
for old, new in BREAKS.values():
    src = src.replace(old, new, 1)
caught, detail = run(src, "三重叠加")
all_caught &= caught
print(f"[{'✅ 被抓' if caught else '⛔ 漏网'}] 三重叠加\n        {detail}")

print(f"\n{'=' * 60}\n负控结论: {'✅ 强化后的探针不再假绿' if all_caught else '⛔ 仍有漏网'}")
sys.exit(0 if all_caught else 1)
