#!/usr/bin/env python3
"""CARD-G2-7b round-6 整改的回退验证（变异测试）。

⛔ 相对 `mutate_r5.py` 堵上两个洞 —— **两个都是 Codex r6 亲自拆穿的**：

  · **空期望片段被当成通过**（r6 MEDIUM-3）：r5 版允许 `frag=""`，此时 `frag_ok`
    直接取 True，于是 H-3 那条「红在 `.index()` 抛 ValueError 而非顺序断言」被记成
    KILLED。⇒ 本版 `frag` **必填非空**，加载时就断言。
  · **变异体自身语法错误被当成 KILLED**（r6 MEDIUM-2）：r5 的 H-2 变异产生
    `*) : ;`（缺 `;;`），测试红的是 rc 2 的语法错，不是入口门。
    ⇒ 本版每次变异后**先做语法检查**（.sh → `bash -n`，.py → `ast.parse`），
    不过就判 SETUP-FAIL，**不计 KILLED**。

其余判据沿用：
  ① KILLED 必须证明**声称的那一条断言**红了（抓失败正文里的消息片段）；
  ② 还原基准是**变异前**的 sha256，不是 HEAD。
"""

from __future__ import annotations

import ast
import hashlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
FORBID = ROOT / "scripts" / "cls_forbidden_paths.py"
DEPLOY = ROOT / "scripts" / "deploy-vault.sh"
PYTEST = ROOT / "backend" / ".venv" / "bin" / "pytest"
TESTFILE = "tests/unit/test_deploy_vault_sh.py"

# (名字, 文件, 原文片段, 替换成, 应当变红的 nodeid, 失败正文里必须出现的消息片段[必填])
MUTANTS = [
    # ── r5 整改 ────────────────────────────────────────────────────────────
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
        "B-4 镜像判据就地失效（内层）",
        DEPLOY,
        'if check_forbidden_paths --outputs "${MIRROR_WRITES[@]}"; then',
        'if false && check_forbidden_paths --outputs "${MIRROR_WRITES[@]}"; then',
        "test_step4_mirror_files_pass_the_same_judge_before_sed",
        "被就地失效或改写",
    ),
    (
        "B-4 外层守卫被架空（r6 MEDIUM-4）",
        DEPLOY,
        'if [ "${#MIRROR_WRITES[@]}" -gt 0 ]; then',
        "if false; then",
        "test_step4_mirror_files_pass_the_same_judge_before_sed",
        "外层守卫",
    ),
    # ── r6 整改 ────────────────────────────────────────────────────────────
    (
        "H-1(r6) fchmod 挪到 nlink 拒绝分支之前",
        DEPLOY,
        '    st = os.fstat(fd)\n    if st.st_nlink > 1:\n        raise SystemExit(f".env 有 {st.st_nlink}',
        '    st = os.fstat(fd)\n    os.fchmod(fd, 0o600)\n    if st.st_nlink > 1:\n        raise SystemExit(f".env 有 {st.st_nlink}',
        "test_env_key_write_chmods_only_after_nofollow_and_nlink",
        "fchmod 必须在 nlink",
    ),
    (
        "B-2(r6) 根处理**整体**移除（under 特例 + walker 登记根）",
        FORBID,
        "    if tk == os.sep:\n        return True  # 根之下 = 全部",
        "    if False:\n        return True",
        "test_forbidden_judge_handles_protected_target_at_root",
        "保护目标为根时漏拦",
        "    visited: list[str] = [os.sep]",  # 第二处：同一变异里一起移除
        "    visited: list[str] = []",
    ),
    (
        "B-1(r6) chain_resolvable 恒真",
        FORBID,
        "    try:\n        os.stat(entry)\n    except FileNotFoundError:\n        return True\n    except OSError:\n        return False\n    return True",
        "    return True",
        "test_forbidden_judge_fail_closed_when_second_hop_unsearchable",
        "第二跳不可搜索时未 fail-closed",
    ),
    (
        "M-1(r6) 上限退回数段数",
        FORBID,
        "    while pending:\n        seg = pending.pop(0)",
        "    while pending:\n        hops += 1\n        if hops > limit:\n            return visited, True\n        seg = pending.pop(0)",
        "test_forbidden_judge_does_not_block_deep_but_linkless_path",
        "无软链的深段路径被误拦",
    ),
    (
        "H-2 去掉 --vault 绝对路径强制（r6 MEDIUM-2 修正：合法 bash + 多段输入）",
        DEPLOY,
        '    *) die64 "--vault 必须是绝对路径',
        '    *) : ;;\n    *_never_matches_*) die64 "--vault 必须是绝对路径',
        "test_multi_segment_relative_vault_is_rejected_at_entry",
        "多段相对 --vault 未被入口拒",
    ),
    # ── r7 整改 ────────────────────────────────────────────────────────────
    (
        "H-1(r7+r8) 判据步骤**整体**移除（hits(path) 与 hits(parent) 两半一起）",
        FORBID,
        "    why = hits(path, targets, claude_prefixes, skip_env_name=True) or hits(\n        parent, targets, claude_prefixes, skip_env_name=True\n    )",
        "    why = None",
        "test_open_pinned_rejects_ancestor_symlink_into_protected",
        "DID NOT RAISE",
    ),
    (
        "H-1(r7) 叶子打开不再强制 O_NOFOLLOW",
        FORBID,
        "        return os.open(leaf, flags | os.O_NOFOLLOW, mode, dir_fd=dirfd)",
        "        return os.open(leaf, flags, mode, dir_fd=dirfd)",
        "test_every_bash_write_site_has_a_prewrite_recheck",
        "叶子打开必须强制带 O_NOFOLLOW",
    ),
    (
        "M-2(r7) 根路径入口退回空逐段列表",
        FORBID,
        "        if why is None and not segs:\n            segs = [os.sep]",
        "        if False:\n            segs = [os.sep]",
        "test_forbidden_judge_checks_root_path_input",
        "未被判据检查",
    ),
    (
        "M-3(r7) 镜像清单恒空 ⇒ 守卫为假、整块跳过（源码门看不见，端到端才抓得到）",
        DEPLOY,
        '            [ -f "$SRC_MIRROR/$t" ] && MIRROR_WRITES+=("mirror-$t:$SRC_MIRROR/$t")',
        '            false && MIRROR_WRITES+=("mirror-$t:$SRC_MIRROR/$t")',
        "test_step4_mirror_symlink_is_blocked_end_to_end",
        "镜像内软链未被步 4 拦下",
    ),
    # ── r8 整改 ────────────────────────────────────────────────────────────
    (
        "H-1(r8) open_pinned 只判 parent（丢掉沿链 .git 保护）",
        FORBID,
        "    why = hits(path, targets, claude_prefixes, skip_env_name=True) or hits(",
        "    why = None or hits(",
        "test_every_bash_write_site_has_a_prewrite_recheck",
        "原路径**必须过判据",
    ),
    (
        "H-3(r8) chmod_pinned 去掉 nlink 拒绝",
        FORBID,
        '        if st.st_nlink > 1:\n            raise OSError(f"{path} 有 {st.st_nlink} 个硬链接',
        '        if False:\n            raise OSError(f"{path} 有 {st.st_nlink} 个硬链接',
        "test_chmod_pinned_rejects_hardlink_and_nonregular",
        "硬链接",
    ),
    (
        "H-4(r8) 裸 os.write 短写当成功",
        DEPLOY,
        '    write_all(fd, "\\n".join(out).encode("utf-8"))',
        '    os.write(fd, "\\n".join(out).encode("utf-8"))',
        "test_every_bash_write_site_has_a_prewrite_recheck",
        "短写",
    ),
    (
        "H-2(r8) 去掉 PYTHONDONTWRITEBYTECODE",
        DEPLOY,
        "export PYTHONDONTWRITEBYTECODE=1\n",
        "",
        "test_script_disables_bytecode_cache_before_importing_primitives",
        "禁字节码缓存必须在任何 import 之前",
    ),
]

# MEDIUM-5 探针：不是「必须 KILLED」，而是**如实测量** ancestor_symlink_hits 是否独立承重。
PROBE = (
    "MEDIUM-5 探针：停用 ancestor_symlink_hits",
    FORBID,
    "    return ancestor_symlink_hits(raw_path, targets, claude_prefixes)",
    "    return None",
)


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def syntax_ok(p: pathlib.Path) -> tuple[bool, str]:
    """变异体自身必须语法正确（r6 MEDIUM-2）——否则红的是语法错，不是被测的门。"""
    if p.suffix == ".py":
        try:
            ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError as e:
            return False, f"python 语法错: {e}"
        return True, ""
    r = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
    return r.returncode == 0, f"bash -n rc={r.returncode}: {r.stderr.strip()[:160]}"


def run_nodeid(nodeid: str) -> tuple[bool, str]:
    r = subprocess.run(
        [str(PYTEST), "-q", "-p", "no:cacheprovider", f"{TESTFILE}::{nodeid}"],
        cwd=ROOT / "backend",
        capture_output=True,
        text=True,
    )
    return r.returncode != 0, r.stdout + r.stderr


def main() -> int:
    for _n, _f, _o, _new, _nid, frag, *_x in MUTANTS:
        assert frag, f"变异 {_n!r} 没写期望片段 —— 空片段会让 KILLED 判据形同虚设（r6 MEDIUM-3）"

    base = {p: (p.read_bytes(), sha(p)) for p in (FORBID, DEPLOY)}
    print("== 变异前基线 sha256（还原以此为准，不是 HEAD）==")
    for p, (_b, h) in base.items():
        print(f"  {h}  {p.relative_to(ROOT)}")
    print()

    bad = 0
    for name, path, old, new, nodeid, frag, *extra_ in MUTANTS:
        extra = tuple(extra_) if extra_ else ()
        text = path.read_text(encoding="utf-8")
        if old not in text or (extra and extra[0] not in text):
            print(f"[SETUP-FAIL] {name}: 原文片段没找到 ⇒ 变异体本身写错了，不计 KILLED")
            bad += 1
            continue
        mutated = text.replace(old, new, 1)
        if extra:
            mutated = mutated.replace(extra[0], extra[1], 1)
        path.write_text(mutated, encoding="utf-8")
        try:
            ok, why = syntax_ok(path)
            if not ok:
                print(f"[SETUP-FAIL] {name}: {why} ⇒ 变异体自身语法错，**不计 KILLED**（r6 MEDIUM-2）")
                bad += 1
                continue
            red, out = run_nodeid(nodeid)
            if red and frag in out:
                print(f"[KILLED]  {name}\n           → {nodeid} 变红，断言消息含「{frag}」")
            elif red:
                print(f"[SUSPECT] {name}: {nodeid} 红了，但期望片段「{frag}」未出现 ⇒ 可能红在别处")
                bad += 1
            else:
                print(f"[SURVIVED] {name}: {nodeid} 仍绿 ⇒ 该门不承重")
                bad += 1
        finally:
            path.write_bytes(base[path][0])
        assert sha(path) == base[path][1], f"还原失败: {path}"

    # ── MEDIUM-5 探针（测量，不判分）──────────────────────────────────────
    name, path, old, new = PROBE
    text = path.read_text(encoding="utf-8")
    print()
    if old not in text:
        print(f"[PROBE-SKIP] {name}: 原文片段没找到")
    else:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        try:
            r = subprocess.run(
                [str(PYTEST), "-q", "-p", "no:cacheprovider", TESTFILE],
                cwd=ROOT / "backend",
                capture_output=True,
                text=True,
            )
            tail = [ln for ln in (r.stdout + r.stderr).splitlines() if ln.startswith("FAILED")]
            if r.returncode == 0:
                print(f"[PROBE] {name} → **全绿**")
                print("        ⇒ 该函数在现有用例下**零承重**。如实登记为冗余，")
                print("          不得再宣称「两轴各自承重」（Codex r6 MEDIUM-5 原话）。")
            else:
                print(f"[PROBE] {name} → 有 {len(tail)} 条变红 ⇒ 独立承重成立：")
                for t in tail[:5]:
                    print(f"          {t}")
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
