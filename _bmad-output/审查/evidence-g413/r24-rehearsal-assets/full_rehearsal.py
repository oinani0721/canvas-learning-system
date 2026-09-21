"""CARD-G4-13 用户 session 全量彩排（全部在 /tmp 副本内；真金集只读）。

场景 A：103/103 全标（三档混合）→ apply-verdicts → build --bump-revision → approve → verify
场景 B：102/103（留一条 pending）→ apply → build → approve 必须被拒
"""
import importlib.util, shutil, sys
from pathlib import Path

LANE = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra")
SCRIPTS = LANE / "backend" / "scripts"
REAL_REG = LANE / "backend" / "tests" / "regression"
CHECKLIST_SRC = LANE / "_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19-裁定清单.md"
NAMES = ["vault_gold_set.yaml", "memory_gold_set.yaml", "vault_gold_set_shadow.yaml",
         "memory_gold_set_shadow.yaml", "gold_set_manifest.yaml"]


def load_tool(reg_root: Path, manifest: Path):
    spec = importlib.util.spec_from_file_location("gold_set_manifest_tool", SCRIPTS / "gold_set_manifest_tool.py")
    tool = importlib.util.module_from_spec(spec)
    sys.modules["gold_set_manifest_tool"] = tool
    spec.loader.exec_module(tool)
    tool.REPO_ROOT = reg_root
    tool.REGRESSION_DIR = reg_root / "backend" / "tests" / "regression"
    tool.MANIFEST_PATH = manifest
    tool.GOLD_SETS = tuple(
        (tool.REGRESSION_DIR / n, "query_type" if "vault" in n else "category") for n in NAMES[:4]
    )
    tool.MAIN_SETS = (tool.REGRESSION_DIR / NAMES[0], tool.REGRESSION_DIR / NAMES[1])
    return tool


def make_root(tag: str) -> Path:
    root = Path(f"/tmp/g413-r3/rehearse-{tag}").resolve()
    if root.exists():
        shutil.rmtree(root)
    reg = root / "backend" / "tests" / "regression"
    reg.mkdir(parents=True)
    for n in NAMES:
        shutil.copy2(REAL_REG / n, reg / n)
    shutil.copy2(CHECKLIST_SRC, reg / "checklist.md")
    return root


def mark_all(cl: Path, skip: str | None = None) -> tuple[int, dict]:
    """勾满清单（三档混合）；skip 的 id 留空。返回 (勾数, id→verdict)。"""
    lines = cl.read_text(encoding="utf-8").splitlines()
    ids = [ln.split("gsid:", 1)[1].split(" -->", 1)[0] for ln in lines if "<!-- gsid:" in ln]
    picks: dict = {}
    for i, gid in enumerate(ids):
        if skip and gid == skip:
            continue
        v = "irrelevant" if i % 10 == 3 else ("ambiguous" if i % 10 == 7 else "relevant")
        picks[gid] = v
    cur = None
    for i, ln in enumerate(lines):
        if "<!-- gsid:" in ln:
            cur = ln.split("gsid:", 1)[1].split(" -->", 1)[0]
        elif cur and cur in picks and ln.lstrip().startswith("- [ ]") and f"verdict:{picks[cur]}" in ln:
            lines[i] = ln.replace("- [ ]", "- [x]", 1)
    cl.write_text("\n".join(lines), encoding="utf-8")
    return len(picks), picks


def run_scenario(tag: str, skip: str | None, expect_approve_ok: bool) -> None:
    root = make_root(tag)
    reg = root / "backend" / "tests" / "regression"
    mf = reg / "gold_set_manifest.yaml"
    tool = load_tool(root, mf)
    files = [reg / n for n in NAMES[:4]]
    cl = reg / "checklist.md"

    n_marked, picks = mark_all(cl, skip=skip)
    before = {p.name: p.read_bytes() for p in files}

    changed, problems = tool.apply_verdicts(files, cl, verdict_by="user", verdict_at="2026-09-20T18:00:00Z")
    print(f"[{tag}] apply-verdicts: changed={len(changed)} problems={len(problems)} (标了 {n_marked} 条)")
    assert not problems, problems[:3]
    assert set(changed) == set(picks), "changed 与勾选集合不符"

    per_file_marks = {q.name: sum(1 for qq in tool.queries_of(q) if qq.get("id") in picks) for q in files}
    for p in files:
        a, b = before[p.name].split(b"\n"), p.read_bytes().split(b"\n")
        diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        want = per_file_marks[p.name] * 3
        print(f"[{tag}]   {p.name}: lines_changed={len(diff)} (期望 {want} = {per_file_marks[p.name]} 条×3)")
        assert len(diff) == want, f"{p.name} 行变化数不符"

    rc, lines = tool.verify_all(mf)
    print(f"[{tag}] 回写后 verify（应 rc=1：sha 变）: rc={rc}")
    assert rc == 1
    assert tool.build_manifest(mf, "4bf90701", True, "彩排：模拟用户裁定回写") == 0
    man = tool.load_yaml(mf)
    vc = next(e for e in man["files"] if e["path"].endswith(NAMES[0]))["verdict_counts"]
    print(f"[{tag}] build: revision={man['revision']} adjudication.status={man['adjudication']['status']} vault.verdict_counts={vc}")
    assert man["revision"] == 3
    assert tool.verify_all(mf)[0] == 0, "升版后 verify 应 rc=0"

    rc_ap = tool.approve_manifest(mf, "user", signed_at="2026-09-20T18:05:00Z")
    print(f"[{tag}] approve: rc={rc_ap}（期望 {'0' if expect_approve_ok else '非 0'}）")
    if expect_approve_ok:
        assert rc_ap == 0
        assert tool.verify_all(mf)[0] == 0
        man = tool.load_yaml(mf)
        assert man["adjudication"]["status"] == "approved" and man["adjudication"]["signed_by"] == "user"
        print(f"[{tag}] ✅ 场景 A 全通：103/103 → approved+签字 → verify rc=0")
    else:
        assert rc_ap != 0, "留一条 pending 时 approve 必须被拒"
        assert tool.load_yaml(mf)["adjudication"]["status"] == "pending", "被拒时不得签字"
        print(f"[{tag}] ✅ 场景 B 正确拒绝：留 {skip} pending ⇒ 不许签字")


run_scenario("A", None, expect_approve_ok=True)
run_scenario("B", "mem-x03", expect_approve_ok=False)
print("REHEARSAL OK：两场景全通（全部在 /tmp 副本；真金集/真 manifest 只读未动）")
