"""独立复现 refute 的承重反例：真缺 PyYAML 时，harness_tree 指向旧树能否写成。

跑法：用 /opt/homebrew/bin/python3 -S（py3.14，find_spec('yaml') is None，零足迹）当写点解释器。
对照组：同机同输入，只把 harness_tree 换成 HEAD 树。
⛔ 只读仓库；一切临时文件落 /tmp/t7a-repro。
"""
import json, os, re, shutil, subprocess, sys, pathlib

WT = pathlib.Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills")
BASE = pathlib.Path("/tmp/t7a-repro")
NOYAML = ["/opt/homebrew/bin/python3", "-S"]

if BASE.exists():
    shutil.rmtree(BASE)
BASE.mkdir(parents=True)

# ── 1. 造旧树（b85a168a 的校验器，零 yaml）──
old = BASE / "oldtree" / "backend" / "scripts"
old.mkdir(parents=True)
src = subprocess.run(["git", "-C", str(WT), "show", "b85a168a:backend/scripts/validate_learning_events.py"],
                     capture_output=True, text=True, check=True).stdout
(old / "validate_learning_events.py").write_text(src, encoding="utf-8")
print("旧树校验器 import yaml 计数:", src.count("import yaml"))

# ── 2. 造 vault 布局（镜像 test fixture）──
def make_vault(name):
    repo = BASE / name
    v = repo / "canvas-vault"
    (v / "节点").mkdir(parents=True)
    (v / ".claude" / "scripts").mkdir(parents=True)
    (repo / "backend" / "scripts").mkdir(parents=True)
    (repo / "backend" / ".venv").symlink_to(WT / "backend" / ".venv", target_is_directory=True)
    (repo / "backend" / "scripts" / "validate_learning_events.py").symlink_to(
        WT / "backend" / "scripts" / "validate_learning_events.py")
    for f in ("fsrs_bridge.py", "decay_beta.py"):
        (v / ".claude" / "scripts" / f).symlink_to(WT / "canvas-vault" / ".claude" / "scripts" / f)
    (v / "节点" / "测试节点.md").write_text(
        '---\ntype: concept\nmastery_score: 0.5\ntitle: 测试节点\nsource_board: "[[原白板/CS 61B]]"\n---\n测试节点正文。\n',
        encoding="utf-8")
    return repo, v

# ── 3. 提取写点 ──
skill = (WT / "canvas-vault/.claude/skills/quiz-answer/SKILL.md").read_text(encoding="utf-8")
CODE = [b for b in re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", skill, re.DOTALL)
        if 'P = "/tmp/quiz-answer-payload.json"' in b][0]

PAYLOAD = {
    "node": "节点/测试节点.md", "grade_norm": 0.752,
    "ts": "2026-08-01T10:00:00Z", "review_time": "2026-08-01T10:00:00Z",
    "event_id": "复现#q1", "exam_board": "检验白板/测试检验-2026-08-01-1000.md",
    "question_id": "q1", "source_board": "[[原白板/CS 61B]]",
    "self_confidence_raw": "半懂", "self_confidence_norm": 0.5,
    "abandoned": False, "callout": "",
}

def run(label, cfg_extra, interp):
    repo, v = make_vault("vault_" + label)
    (v / ".canvas-config.yaml").write_text(
        'vault_id: "demo_vault"\nsubject: cs-61b\n' + cfg_extra, encoding="utf-8")
    pf = repo / "payload.json"
    pf.write_text(json.dumps(PAYLOAD, ensure_ascii=False), encoding="utf-8")
    code = CODE.replace('"/tmp/quiz-answer-payload.json"', json.dumps(str(pf)))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPATH", None)
    r = subprocess.run(interp + ["-c", code], capture_output=True, text=True,
                       timeout=300, cwd=str(v), env=env)
    led = v / "learning_events.jsonl"
    n = len(led.read_text(encoding="utf-8").splitlines()) if led.exists() else 0
    node_now = (v / "节点" / "测试节点.md").read_text(encoding="utf-8")
    mastery = re.search(r"^mastery_score:\s*(\S+)", node_now, re.M)
    tail = " | ".join((r.stderr or "").strip().splitlines()[-2:])[:220]
    print(f"  [{label:22}] rc={r.returncode} 账本行数={n} mastery={mastery.group(1) if mastery else '?'}")
    print(f"      stderr尾: {tail or '(无)'}")
    return r.returncode, n

print("\n=== 解释器自证 ===")
chk = subprocess.run(NOYAML + ["-c", "import importlib.util as u,sys;print('py%d.%d find_spec(yaml)=%s'%(sys.version_info[0],sys.version_info[1],u.find_spec('yaml')))"],
                     capture_output=True, text=True)
print(" ", chk.stdout.strip(), chk.stderr.strip()[:200])

print("\n=== 实验（写点解释器 = 真缺 PyYAML 的 py3.14 -S）===")
rc_old, n_old = run("A: harness→旧树", f"harness_tree: {BASE / 'oldtree'}\n", NOYAML)
rc_head, n_head = run("B: 无 harness(HEAD树)", "", NOYAML)

print("\n=== 对照（同输入，但解释器有 PyYAML）===")
rc_y, n_y = run("C: 有yaml+无harness", "", [str(WT / "backend/.venv/bin/python")])

print("\n=== 结论 ===")
print(f"  A 旧树 缺库: rc={rc_old} 账本={n_old}  ← 若 rc=0 且账本=1，则「缺库必然写不成」被证伪")
print(f"  B HEAD 缺库: rc={rc_head} 账本={n_head}")
print(f"  C HEAD 有库: rc={rc_y} 账本={n_y}  ← 夹具本身有效性对照")
