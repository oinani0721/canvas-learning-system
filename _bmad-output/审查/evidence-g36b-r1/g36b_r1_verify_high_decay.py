"""独立复现 Codex R1 [HIGH]：改 decay_beta.py 的**函数体**（六常量不动）
→ 排序变而 rank sha 不变。全程纯源码演进，无 pyc / mtime / 运行时替换。"""
import importlib.util, json, sys, tempfile, shutil
from datetime import datetime, timezone
from pathlib import Path

LANE = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard")
PICK = LANE / "scripts" / "daily_review_pick.py"
DECAY = LANE / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py"
NOW = datetime(2026, 7, 30, 1, 0, tzinfo=timezone.utc)

def load(path, name, extra_syspath=None):
    if extra_syspath:
        sys.path.insert(0, str(extra_syspath))
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def node(board, name, a, b, last="2026-07-25T01:00:00Z"):
    return dict(board=board, node=name, mastery_a=a, mastery_b=b, last_examined=last)

with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    # 两个 vault：一个原样 decay，一个只改函数体（六常量逐字不动）
    for tag, mutate in (("base", False), ("mutated", True)):
        sd = tmp / tag / ".claude" / "scripts"; sd.mkdir(parents=True)
        src = DECAY.read_text(encoding="utf-8")
        if mutate:
            old = "    return mu(a, b) - beta * sigma(a, b)"
            new = "    return mu(a, b) + beta * sigma(a, b)"   # 只翻探索项符号
            assert src.count(old) == 1, "锚点未命中"
            src = src.replace(old, new, 1)
        (sd / "decay_beta.py").write_text(src, encoding="utf-8")

    picker = load(PICK, "picker_high")
    results = {}
    for tag in ("base", "mutated"):
        d = load(tmp / tag / ".claude" / "scripts" / "decay_beta.py", f"decay_{tag}")
        # 六常量快照：证明它们逐字未变
        consts = {k: getattr(d, k, None) for k in picker.DECAY_CONSTANT_NAMES}
        # 构造两板，pick 由 decay 函数体算出
        # μ 相同(0.5)、样本量悬殊 → σ 差异大：探索项符号一翻，两板优劣互换
        # A: a=b=20 → σ≈0.078(大样本，窄)   B: a=b=0.5 → σ≈0.354(小样本，宽)
        # μ-βσ: A=0.422 B=0.146 → B 先    μ+βσ: A=0.578 B=0.854 → A 先
        raw = [node("A板", "A", 20.0, 20.0), node("B板", "B", 0.5, 0.5)]
        nodes = []
        for n in raw:
            a_eff, b_eff = d.effective(n["mastery_a"], n["mastery_b"], 0.0)
            nodes.append({"board": n["board"], "node": n["node"],
                          "pick": d.pick_score(a_eff, b_eff), "due_now": True,
                          "idle_days": 5, "difficulty": "", "fsrs_due": "",
                          "due_fail_open": False, "last_examined": n["last_examined"]})
        order = [r["board"] for r in picker.rank_boards(nodes, {}, NOW)[0]]
        sha = picker.build_rank_manifest(d, 1, dict(picker.DEFAULT_MINUTES), {})["sha256"]
        results[tag] = (order, sha, consts, [round(n["pick"], 6) for n in nodes])

    ob, sb, cb, pb = results["base"]
    om, sm, cm, pm = results["mutated"]
    print(f"六常量是否逐字相同: {cb == cm}   ({cb})")
    print(f"pick 值   base={pb}  mutated={pm}")
    print(f"板序      base={ob}  mutated={om}   → 排序改变: {ob != om}")
    print(f"rank sha  base={sb[:16]}…  mutated={sm[:16]}…  → sha 不变: {sb == sm}")
    print()
    verdict = (cb == cm) and (ob != om) and (sb == sm)
    print(f"HIGH 复现: {'✅ 成立 — 纯源码演进下排序变而指纹不变' if verdict else '❌ 未复现'}")
    sys.exit(0 if verdict else 1)
