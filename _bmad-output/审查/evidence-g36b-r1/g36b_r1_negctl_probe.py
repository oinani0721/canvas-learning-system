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

# 每条：(锚点, 替换, **必须出现的那条 [FAIL] 的关键词**)
# R1 round-2 Codex MEDIUM：原版把「任意非零退出」都算被抓 —— 空源码让探针
# AttributeError 崩溃、rc=1，也会被记成「✅ 被抓」。必须要求**精确的那条 FAIL**
# 出现、summary 完整、且无 traceback；崩溃/超时一律 INVALID。
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
    # (4) R1 round-2 Codex 的变异：摘要用默认分钟，实际分钟仍用 manifest
    #     → payload 说 24 分钟，指纹却是 3/5 那份的（两者脱钩）
    "摘要与实际分钟脱钩": (
        '    rank_manifest = build_rank_manifest(decay, version, minutes, recorded)',
        '    rank_manifest = build_rank_manifest(decay, version, dict(DEFAULT_MINUTES), recorded)',
    ),
    # (5) R1 round-2 Codex 的变异：让 recorded（登记快照）真去控制截断
    #     → 一边告警「以实际为准」，一边按登记值出 4 块板
    "recorded 反过来控制截断": (
        '        "top_boards": ranked[:TOP_BOARDS_LIMIT],',
        '        "top_boards": ranked[:(recorded.get("limits", {}).get("top_boards") or TOP_BOARDS_LIMIT)],',
    ),
    # (6) R1 round-3 Codex 的变异：只有**第一块板**用 manifest 分钟，后续板回落默认
    #     → 单板 fixture / 只看 top_boards[0] 的断言完全抓不到
    "分钟只对首板生效": (
        '            "estimated_minutes": estimated_minutes(factors, minutes),',
        '            "estimated_minutes": estimated_minutes(factors, minutes if not ranked else DEFAULT_MINUTES),',
    ),
    # (7) R1 round-3 Codex 的变异：recorded 改去控制 **upcoming** 榜的截断
    #     → 到期板 fixture 里 upcoming 恒空，该分支完全没被覆盖
    "recorded 控制 upcoming 截断": (
        '        "upcoming": upcoming[:UPCOMING_LIMIT],',
        '        "upcoming": upcoming[:(recorded.get("limits", {}).get("upcoming") or UPCOMING_LIMIT)],',
    ),
}

# 每条变异必须让**这一条**探针断言变红（不是「某处红了」就算）
EXPECT_FAIL_KEYWORD = {
    "回落值不精确": "回落值精确 + 告警点名",
    "impl_sha 固定为零": "接入最终 rank_manifest.sha256",
    "payload 忽略 manifest 分钟": "每一块板**落盘的分钟",
    "摘要与实际分钟脱钩": "实际生效的那组分钟**同源",
    "recorded 反过来控制截断": "仅 recorded 不同",
    "分钟只对首板生效": "每一块板**落盘的分钟",
    "recorded 控制 upcoming 截断": "两个榜**长度都恒为 3",
}

def run(src: str, label: str, expect_kw: str | None) -> tuple[str, str]:
    """返回 (verdict, detail)。verdict ∈ {CAUGHT, MISSED, INVALID}。

    CAUGHT 的三个条件（缺一不可）：
      a) 探针跑完了 —— stdout 里有 "复核结果:" 这一行 summary；
      b) stderr 里**没有** Traceback（崩溃不是「门抓住了」）；
      c) **指定的那条**断言出现在 [FAIL] 行里（不是「某处有 FAIL」）。
    """
    f = OUT / f"broken_{abs(hash(label))}.py"
    f.write_text(src, encoding="utf-8")
    try:
        r = subprocess.run(
            [str(LANE / "backend" / ".venv" / "bin" / "python"), str(PROBE), str(f)],
            capture_output=True, text=True, timeout=300,
            env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
                 "HOME": str(Path.home()), "LANG": "en_US.UTF-8"})
    except subprocess.TimeoutExpired:
        return "INVALID", "探针超时 —— 不能算「被抓」"

    out, err = r.stdout or "", r.stderr or ""
    if "Traceback" in err:
        return "INVALID", f"探针崩溃（非断言失败）: {err.strip().splitlines()[-1][:110]}"
    if "复核结果:" not in out:
        return "INVALID", f"探针未跑完（无 summary）: {(out or err)[-120:]}"

    fails = [l for l in out.splitlines() if l.startswith("[FAIL]")]
    if expect_kw is None:
        return ("CAUGHT" if fails else "MISSED"), (fails[0][:120] if fails else "全 PASS")
    hit = [l for l in fails if expect_kw in l]
    if hit:
        return "CAUGHT", hit[0][:120]
    if fails:
        return "MISSED", f"红了但不是指定那条: {fails[0][:100]}"
    return "MISSED", "全 PASS —— 该破坏未被任何断言抓住"

MARK = {"CAUGHT": "✅ 被抓", "MISSED": "⛔ 漏网", "INVALID": "⚠ INVALID"}

# ── 阶段 -1：关键词防过期校验 ──
# R1 round-3 实践教训：改了某条断言的文案后，这里的期望关键词会**静默过期**，
# 于是「该条没红」被误报成漏网（本轮真实发生过一次）。所以先跑一次未变异探针，
# 要求每个关键词都能在它的输出里找到对应断言 —— 找不到 = 关键词过期，立即停。
print("═══ 阶段 -1：关键词防过期校验（关键词必须对得上现有断言）═══")
_base = OUT / "baseline_probe.py"
_base.write_text(SRC, encoding="utf-8")
_r = subprocess.run([str(LANE / "backend" / ".venv" / "bin" / "python"), str(PROBE), str(_base)],
                    capture_output=True, text=True, timeout=300,
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
                         "HOME": str(Path.home()), "LANG": "en_US.UTF-8"})
_stale = [f"{lbl} → {kw!r}" for lbl, kw in EXPECT_FAIL_KEYWORD.items() if kw not in _r.stdout]
if _stale:
    print("⛔ 关键词已过期（对不上任何现有断言），先修关键词表再跑负控:")
    for item in _stale:
        print(f"     {item}")
    sys.exit(2)
print(f"  ✅ {len(EXPECT_FAIL_KEYWORD)} 个关键词全部命中现有断言\n")

print("═══ 逐项单独破坏（每条必须让**指定的那条**断言变红）═══")
verdicts = []
for label, (old, new) in BREAKS.items():
    assert SRC.count(old) == 1, f"{label} 锚点命中 {SRC.count(old)} 次"
    v, detail = run(SRC.replace(old, new, 1), label, EXPECT_FAIL_KEYWORD.get(label))
    verdicts.append((label, v))
    print(f"[{MARK[v]}] {label}\n        {detail}")

print("\n═══ 全部叠加破坏（要求**每一条**的指定断言都红，不是「有 FAIL 就算」）═══")
# R1 round-3 Codex MEDIUM：原版给叠加项传 expect_kw=None，于是任意一条 [FAIL]
# 都被记成 CAUGHT —— 用一个无关的失败即可骗过它。改为逐关键词核对。
src = SRC
for old, new in BREAKS.values():
    src = src.replace(old, new, 1)
v_all, detail_all = run(src, "全部叠加", None)   # 先拿到 verdict/summary 形态
missing_kw: list[str] = []
if v_all == "CAUGHT":
    f = OUT / f"broken_{abs(hash('全部叠加'))}.py"
    r = subprocess.run([str(LANE / "backend" / ".venv" / "bin" / "python"), str(PROBE), str(f)],
                       capture_output=True, text=True, timeout=300,
                       env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
                            "HOME": str(Path.home()), "LANG": "en_US.UTF-8"})
    fail_text = "\n".join(l for l in r.stdout.splitlines() if l.startswith("[FAIL]"))
    missing_kw = [kw for kw in EXPECT_FAIL_KEYWORD.values() if kw not in fail_text]
    if missing_kw:
        v_all = "MISSED"
        detail_all = f"叠加下这些指定断言没红: {missing_kw}"
    else:
        detail_all = f"全部 {len(EXPECT_FAIL_KEYWORD)} 条指定断言均出现在 [FAIL] 中"
verdicts.append(("全部叠加", v_all))
print(f"[{MARK[v_all]}] 全部叠加\n        {detail_all}")
v, detail = v_all, detail_all

print("\n═══ 验伪锚：探针崩溃**不得**被记成「被抓」═══")
v_crash, d_crash = run("# 空源码\n", "空源码崩溃", None)
print(f"[{MARK[v_crash]}] 空源码（期望 INVALID，若记成 CAUGHT 则本负控本身是假的）"
      f"\n        {d_crash}")

ok = all(v == "CAUGHT" for _l, v in verdicts) and v_crash == "INVALID"
print(f"\n{'=' * 60}")
print(f"负控结论: {'✅ 上述 ' + str(len(verdicts)) + ' 种已知破坏各被其指定断言抓住，且崩溃被正确判 INVALID' if ok else '⛔ 有漏网或验伪锚失效'}")
print("⚠ 边界: 这只证明**这几种已知破坏**被抓，不等于「探针不可能假绿」——")
print("   未枚举的破坏形态仍可能漏网 (R1 round-2 Codex MEDIUM 指出的正是这一点)。")
sys.exit(0 if ok else 1)
