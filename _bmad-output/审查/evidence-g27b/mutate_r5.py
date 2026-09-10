#!/usr/bin/env python3
"""CARD-G2-7b round-5 整改的回退验证（变异测试）。

判据（记忆里的两条硬教训）：
  ① KILLED 必须证明**我声称的那一条断言**红了，不是「某处失败了」——故每条变异
     只跑它对应的 nodeid，并抓取失败正文里的断言消息片段。
  ② 还原基准是**变异前**的 sha256，不是 HEAD（HEAD 上还有别的未提交改动）。

用法：python3 _bmad-output/审查/evidence-g27b/mutate_r5.py
"""

from __future__ import annotations

import hashlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
FORBID = ROOT / "scripts" / "cls_forbidden_paths.py"
DEPLOY = ROOT / "scripts" / "deploy-vault.sh"
PYTEST = ROOT / "backend" / ".venv" / "bin" / "pytest"
TESTFILE = "tests/unit/test_deploy_vault_sh.py"

# (名字, 文件, 原文片段, 替换成, 应当变红的 nodeid, 失败正文里应出现的消息片段)
MUTANTS = [
    (
        "B-1 前缀退回只留词法 HOME",
        FORBID,
        "    for base in (home, os.path.realpath(home)):",
        "    for base in (home,):",
        "test_forbidden_judge_covers_physical_home_claude_prefix",
        "物理 HOME 下的 .claude-new 未被拦",
    ),
    (
        "B-2 去掉 hits() 里的逐段遍历判据",
        FORBID,
        "    ch = chain_hits(raw_path, targets, claude_prefixes)\n    if ch is not None:\n        return ch\n",
        "",
        "test_forbidden_judge_catches_git_in_ancestor_of_link_target",
        "未拦住链目标祖先里的 .git",
    ),
    (
        "B-2 让 walker 重新词法折叠 ..",
        FORBID,
        "        visited.append(tgt)\n        pending = tgt.split(os.sep) + pending",
        "        tgt = os.path.normpath(tgt)\n        visited.append(tgt)\n        pending = tgt.split(os.sep) + pending",
        "test_forbidden_judge_does_not_fold_dotdot_before_resolving",
        "被提前折叠",
    ),
    (
        "B-3 去掉 HOME 可搜索性检查",
        FORBID,
        "    if not os.access(home, os.R_OK | os.X_OK):\n        enumerate_failed = True",
        "    if False:\n        enumerate_failed = True",
        "test_forbidden_judge_fail_closed_when_home_not_searchable",
        "未 fail-closed",
    ),
    (
        "H-2 去掉 --vault 绝对路径强制",
        DEPLOY,
        '    *) die64 "--vault 必须是绝对路径',
        '    *) : ; # mutated\n    *) die64 "--vault 必须是绝对路径',
        "test_relative_vault_is_rejected_at_entry",
        "相对 --vault 未被入口拒",
    ),
    (
        "B-4 把镜像判据挪到 sed 之后",
        DEPLOY,
        'check_forbidden_paths --outputs "${MIRROR_WRITES[@]}"',
        'false && check_forbidden_paths --outputs "${MIRROR_WRITES[@]}"',
        "test_step4_mirror_files_pass_the_same_judge_before_sed",
        "被就地失效或改写",
    ),
    (
        "H-3 去掉写前 chmod",
        DEPLOY,
        '    if [ -e "$ENV_FILE" ]; then\n        chmod 600 "$ENV_FILE" || { STEP_MSG="写前 chmod 600 失败',
        '    if false; then\n        chmod 600 "$ENV_FILE" || { STEP_MSG="写前 chmod 600 失败',
        "test_env_file_is_chmod_600_before_key_is_written",
        "",
    ),
]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    base = {p: (p.read_bytes(), sha(p)) for p in (FORBID, DEPLOY)}
    print("== 变异前基线 sha256（还原以此为准，不是 HEAD）==")
    for p, (_b, h) in base.items():
        print(f"  {h}  {p.relative_to(ROOT)}")
    print()

    bad = 0
    for name, path, old, new, nodeid, frag in MUTANTS:
        text = path.read_text(encoding="utf-8")
        if old not in text:
            print(f"[SETUP-FAIL] {name}: 原文片段没找到 ⇒ 变异体本身写错了，不计 KILLED")
            bad += 1
            continue
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        try:
            r = subprocess.run(
                [str(PYTEST), "-q", "-p", "no:cacheprovider", f"{TESTFILE}::{nodeid}"],
                cwd=ROOT / "backend",
                capture_output=True,
                text=True,
            )
            out = r.stdout + r.stderr
            red = r.returncode != 0
            frag_ok = (frag in out) if frag else True
            if red and frag_ok:
                print(f"[KILLED]  {name}")
                print(f"           → {nodeid} 变红" + (f"，断言消息含「{frag}」" if frag else ""))
            elif red and not frag_ok:
                print(f"[SUSPECT] {name}: {nodeid} 红了，但**不是**声称的那条断言")
                print(f"           期望片段「{frag}」未出现 ⇒ 可能红在别处")
                bad += 1
            else:
                print(f"[SURVIVED] {name}: {nodeid} 仍绿 ⇒ 该门不承重")
                bad += 1
        finally:
            path.write_bytes(base[path][0])
        assert sha(path) == base[path][1], f"还原失败: {path}"

    print("\n== 还原逐字节核对 ==")
    for p, (_b, h) in base.items():
        now = sha(p)
        print(f"  {'同' if now == h else '⚠️不同'}  {now}  {p.relative_to(ROOT)}")
    print(f"\n结论: {len(MUTANTS) - bad}/{len(MUTANTS)} KILLED, {bad} 有问题")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
