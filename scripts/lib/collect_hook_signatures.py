#!/usr/bin/env python3
"""DEBT-15 · 汇总全部 hook 面的 git 写副作用签名。

BATCH-2026-08-29-第六批 / CARD-DEBT-15

输出（TAB 分隔，一行一条）：
    <source_key>::<signature>\t<evidence>

特殊 signature（一律 fail-closed，调用方必须判 FAIL）：
    UNREACHABLE   挂载的脚本找不到 —— 看不到内容就不能说「没有写副作用」
    UNPARSEABLE   hooks JSON / plist 解析失败 —— 整个来源会静默逃逸
    UNANALYZABLE  命令解析不了（动态 remote、未知包装器、引号不闭合）

设计要点（对应 Codex round-1 的 BLOCKER/HIGH）：
    B4 递归闭包：脚本 A 调 B，B 的 git 写必须被追到。带 visited set 防环。
    B4 exec-form：settings hook 的 args 数组要拼进命令，不能只读 command。
    B5 扩展名：superpowers 的 hook 入口是 .cmd，不能只认 .sh/.js/.py。
    H6 hooksPath：用 `git rev-parse --git-path hooks` 取**实际**路径，不硬编码。
    H6 lefthook：extends / remotes 会把外部配置合并进来，静态扫不到 ⇒ UNANALYZABLE。
    H6 LaunchAgent：用 plistlib 解析（兼容 binary plist），读 Program 与 ProgramArguments。
"""

import json
import os
import plistlib
import re
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCANNER = os.path.join(HERE, "scan_git_occurrences.py")

# 递归闭包会展开这些扩展名的目标；扩展名之外的（extensionless、.cmd 等）
# 若无法读取则报 UNREACHABLE，可读则照样扫（按 shell 处理）。
SCANNABLE_EXT = {".sh", ".bash", ".zsh", ".js", ".mjs", ".cjs", ".ts", ".py", ".cmd", ".rb", ".pl", ""}

out_lines = []


def emit(source_key, signature, evidence):
    out_lines.append(f"{source_key}::{signature}\t{evidence}")


def short_label(path):
    """脚本路径 → 登记表用的稳定 label。

    必须只有这一处定义：同一个脚本可能经两条路径被扫到
    （settings 的扩展名正则 / 内联命令的 REF 展开），
    两处若各自造 label，登记表会全面失配（实测：auto-sync 的四条签名
    因此从 `main-settings:auto-sync::…` 变成
    `main-settings:stop-auto-sync-to-remote.sh::…`，登记表整片查无此项）。
    """
    return re.sub(r"^stop-|-to-remote|\.(sh|bash|zsh|js|py|cmd|mjs|cjs|ts|rb|pl)$", "", os.path.basename(path))


def run_scanner(path):
    """调用 occurrence 解析器，返回 (occurrences, refs, unanalyzable)。"""
    try:
        res = subprocess.run([sys.executable, SCANNER, path], capture_output=True, text=True, timeout=60)
    except Exception as exc:
        return [], [], [(0, f"scanner failed: {type(exc).__name__}", path)]
    occ, refs, bad = [], [], []
    for line in res.stdout.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        if parts[0] == "OCC" and len(parts) >= 4:
            occ.append((int(parts[1]), parts[2], parts[3]))
        elif parts[0] == "REF" and len(parts) >= 3:
            refs.append((int(parts[1]), parts[2]))
        elif parts[0] == "UNANALYZABLE" and len(parts) >= 3:
            bad.append((int(parts[1]), parts[2], parts[3] if len(parts) > 3 else ""))
    return occ, refs, bad


INTERPRETERS = {
    "bash",
    "sh",
    "zsh",
    "dash",
    "ksh",
    "python",
    "python3",
    "node",
    "nodejs",
    "ruby",
    "perl",
    "env",
    "osascript",
}


def is_binary(path):
    """前 4KB 含 NUL ⇒ 二进制。扫二进制会产出海量垃圾 UNANALYZABLE。"""
    try:
        with open(path, "rb") as fh:
            return b"\x00" in fh.read(4096)
    except Exception:
        return True


def scan_closure(source_key, label, entry_path, base_dir, visited=None, depth=0):
    """扫描 entry_path 并沿 REF 递归展开（B4）。"""
    if visited is None:
        visited = set()
    real = os.path.realpath(entry_path)
    if real in visited:
        return
    if depth > 6:
        # Codex round-2 B-05：深度 7 的 writer 原先被静默丢弃 ⇒ exit 0。
        # 看不到就必须报，不能当作「没有写副作用」。
        emit(f"{source_key}:{label}", "UNANALYZABLE", f"{entry_path}（调用链深度超过 6，未继续展开）")
        return
    visited.add(real)

    if not os.path.isfile(entry_path):
        emit(f"{source_key}:{label}", "UNREACHABLE", f"{entry_path}（挂载目标不可达）")
        return
    # 解释器本身（/bin/bash 等）不是待扫脚本——真正的脚本是它的下一个参数
    if os.path.basename(entry_path) in INTERPRETERS:
        return
    if is_binary(entry_path):
        # Codex round-2 B-05：编译后的 .git/hooks/pre-commit 内含
        # execlp("git",...push...)，原先被二进制检测静默跳过 ⇒ exit 0。
        # 静态分析确实读不了二进制，但那正是必须 fail-closed 的理由。
        emit(f"{source_key}:{label}", "UNANALYZABLE", f"{entry_path}（二进制可执行，静态分析无法判断其是否写 git）")
        return

    occ, refs, bad = run_scanner(entry_path)
    base = os.path.basename(entry_path)
    for lineno, sig, snippet in occ:
        emit(f"{source_key}:{label}", sig, f"{base}:{lineno}  {snippet}")
    for lineno, reason, snippet in bad:
        emit(f"{source_key}:{label}", "UNANALYZABLE", f"{base}:{lineno} {reason} — {snippet}")
    for lineno, ref in refs:
        if "$" in ref or "`" in ref:
            emit(f"{source_key}:{label}", "UNANALYZABLE", f"{base}:{lineno} 动态脚本路径无法静态展开 — {ref}")
            continue
        cand = ref if os.path.isabs(ref) else os.path.normpath(os.path.join(base_dir, ref))
        ext = os.path.splitext(cand)[1].lower()
        if ext not in SCANNABLE_EXT:
            emit(f"{source_key}:{label}", "UNANALYZABLE", f"{base}:{lineno} 未知包装器目标 — {ref}")
            continue
        scan_closure(source_key, short_label(cand), cand, os.path.dirname(cand), visited, depth + 1)


def expand_vars(cmd, project_dir, home):
    for var in ("$CLAUDE_PROJECT_DIR", "${CLAUDE_PROJECT_DIR}"):
        cmd = cmd.replace(var, project_dir)
    for var in ("$CLAUDE_PLUGIN_ROOT", "${CLAUDE_PLUGIN_ROOT}"):
        cmd = cmd.replace(var, project_dir)
    return cmd.replace("~", home)


def handle_settings(source_key, path, project_dir, home):
    if not os.path.isfile(path):
        emit(source_key, "UNREACHABLE", f"{path}（来源文件不存在）")
        return
    try:
        with open(path) as fh:
            data = json.load(fh)
    except Exception as exc:
        # 静默 exit 会让整个来源逃逸 —— 必须 fail-closed
        emit(source_key, "UNPARSEABLE", f"{path}（JSON 解析失败: {type(exc).__name__}）")
        return
    hooks = data.get("hooks") or {}
    seen = set()
    for event, entries in hooks.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for h in entry.get("hooks") or []:
                if not isinstance(h, dict):
                    continue
                cmd = h.get("command", "") or ""
                # B4：exec-form 的 args 必须拼进来，否则
                # {"command":"git","args":["push","rogue","HEAD"]} 完全逃逸
                args = h.get("args")
                if isinstance(args, list):
                    # ⚠️ 必须 shlex.quote：朴素 join 会把
                    #   {"command":"sh","args":["-c","git push rogue HEAD"]}
                    # 拼成 `sh -c git push rogue HEAD`，-c 的参数退化成裸的 `git`，
                    # 后面几个词变成 sh 的额外参数，整条内联代码解析不出来（实测 N19 漏报）。
                    cmd = " ".join([cmd] + [shlex.quote(str(a)) for a in args])
                if not cmd.strip():
                    continue
                expanded = expand_vars(cmd, project_dir, home)
                label = f"inline-{event}"
                # 内联 git 写（不经脚本中转）
                occ, inline_refs = parse_inline(expanded)
                for sig, snippet in occ:
                    emit(f"{source_key}:{label}", sig, f"{os.path.basename(path)} hooks.{event}  {snippet}")
                # 内联命令里调用的脚本也要展开（B-05：bash rogue.txt 曾整条逃逸）
                for iref in inline_refs:
                    if "$" in iref or "`" in iref:
                        emit(
                            f"{source_key}:{label}",
                            "UNANALYZABLE",
                            f"{os.path.basename(path)} hooks.{event} 动态脚本路径 — {iref}",
                        )
                        continue
                    icand = (
                        iref if os.path.isabs(iref) else os.path.normpath(os.path.join(project_dir, iref.lstrip("./")))
                    )
                    if icand in seen:
                        continue
                    seen.add(icand)
                    scan_closure(source_key, short_label(icand), icand, os.path.dirname(icand))
                # 脚本中转 → 递归闭包
                for tok in re.findall(
                    r"\S+\.(?:sh|bash|zsh|js|mjs|cjs|ts|py|cmd|rb|pl)", expanded.replace('"', "").replace("'", "")
                ):
                    cand = tok if tok.startswith("/") else os.path.normpath(os.path.join(project_dir, tok.lstrip("./")))
                    if cand in seen:
                        continue
                    seen.add(cand)
                    scan_closure(source_key, short_label(cand), cand, os.path.dirname(cand))


def parse_inline(command_text):
    """解析一段内联命令文本（不落盘），返回 ([(sig, snippet)], refs)。

    ⚠️ refs 必须回传（Codex round-2 B-05）：原实现丢弃 scanner 返回的 refs，
    于是 settings 里 `bash rogue.txt` 这类内联调用的下游脚本完全没被展开。
    """
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as fh:
        fh.write(command_text + "\n")
        tmp = fh.name
    try:
        occ, refs, bad = run_scanner(tmp)
        res = [(s, sn) for _l, s, sn in occ]
        res += [("UNANALYZABLE", f"{r} — {sn}") for _l, r, sn in bad]
        return res, [r for _l, r in refs]
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def handle_yaml_lefthook(source_key, path):
    if not os.path.isfile(path):
        emit(source_key, "UNREACHABLE", f"{path}（来源文件不存在）")
        return
    try:
        text = open(path, errors="replace").read()
    except Exception as exc:
        emit(source_key, "UNPARSEABLE", f"{path}（读取失败: {type(exc).__name__}）")
        return
    # H6：extends / remotes 会把外部配置合并进来，静态扫本文件看不到那部分
    # ⚠️ 用独立签名后缀（Codex round-2 B-06 实测）：若与「动态 pathspec」共用
    #    `<source>::UNANALYZABLE`，那条 ACK 会把性质完全不同的 extends 外部配置
    #    一并放行——实测 `extends -> rogue-extend.yml` 里的 git push 就是这样逃掉的。
    for key in ("extends:", "remotes:"):
        if re.search(rf"^{key}", text, re.M):
            emit(
                source_key,
                "UNANALYZABLE:EXTERNAL_CONFIG",
                f"{os.path.basename(path)} 含 `{key}`——lefthook 会合并外部配置，"
                f"静态扫描覆盖不到；须以 `lefthook dump` 的合并结果为准",
            )
    occ, _refs, bad = run_scanner(path)
    base = os.path.basename(path)
    for lineno, sig, snippet in occ:
        emit(source_key, sig, f"{base}:{lineno}  {snippet}")
    for lineno, reason, snippet in bad:
        emit(source_key, "UNANALYZABLE", f"{base}:{lineno} {reason} — {snippet}")
    # lefthook-local 覆盖层
    # lefthook 支持多种文件名/后缀，只查 .yml 会漏（B-06 实测：lefthook-local.yaml 逃逸）
    d = os.path.dirname(path)
    for lname in ("lefthook-local.yml", "lefthook-local.yaml", "lefthook.yaml", ".lefthook.yml", ".lefthook.yaml"):
        local = os.path.join(d, lname)
        if not os.path.isfile(local) or os.path.realpath(local) == os.path.realpath(path):
            continue
        ltext = ""
        try:
            ltext = open(local, errors="replace").read()
        except Exception:
            pass
        for key in ("extends:", "remotes:"):
            if re.search(rf"^{key}", ltext, re.M):
                emit(source_key, "UNANALYZABLE:EXTERNAL_CONFIG", f"{lname} 含 `{key}`——合并外部配置，静态扫描覆盖不到")
        occ2, _r2, bad2 = run_scanner(local)
        for lineno, sig, snippet in occ2:
            emit(source_key, sig, f"{lname}:{lineno}  {snippet}")
        for lineno, reason, snippet in bad2:
            emit(source_key, "UNANALYZABLE", f"{lname}:{lineno} {reason} — {snippet}")


def handle_hookdir(source_key, repo):
    """H6：用 git 自己解析的实际 hooks 路径，不硬编码 .git/hooks。"""
    hooks_dir = None
    try:
        r = subprocess.run(
            ["git", "-C", repo, "rev-parse", "--git-path", "hooks"], capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            p = r.stdout.strip()
            hooks_dir = p if os.path.isabs(p) else os.path.normpath(os.path.join(repo, p))
    except Exception:
        hooks_dir = None
    if not hooks_dir or not os.path.isdir(hooks_dir):
        emit(source_key, "UNREACHABLE", f"{repo} 的 hooks 目录解析失败（core.hooksPath?）")
        return
    emit(source_key, "__INFO_PATH__", hooks_dir)
    for name in sorted(os.listdir(hooks_dir)):
        if name.endswith(".sample"):
            continue
        f = os.path.join(hooks_dir, name)
        if not os.path.isfile(f):
            continue
        scan_closure(source_key, name, f, hooks_dir)


def handle_launchagents(source_key, d):
    if not os.path.isdir(d):
        emit(source_key, "UNREACHABLE", f"{d}（目录不存在）")
        return
    for name in sorted(os.listdir(d)):
        if not name.endswith(".plist"):
            continue
        path = os.path.join(d, name)
        label = name[:-6]
        try:
            with open(path, "rb") as fh:
                pl = plistlib.load(fh)  # 兼容 binary plist
        except Exception as exc:
            emit(f"{source_key}:{label}", "UNPARSEABLE", f"{name}（plist 解析失败: {type(exc).__name__}）")
            continue
        # ⚠️ 先把 Program + ProgramArguments 当作**一条完整命令**解析
        #    （Codex round-2 B-06 实测逃逸两例）：
        #      ["/usr/bin/git","push","rogue","HEAD"]   ← 逐参数当路径看则完全漏掉
        #      ["/bin/sh","-c","git push rogue HEAD"]   ← 同上
        argv = []
        if isinstance(pl.get("Program"), str):
            argv.append(pl["Program"])
        pa = pl.get("ProgramArguments")
        if isinstance(pa, list):
            argv.extend([a for a in pa if isinstance(a, str)])
        if argv:
            cmdline = " ".join(shlex.quote(a) for a in argv)
            aocc, arefs = parse_inline(cmdline)
            for sig, snippet in aocc:
                emit(f"{source_key}:{label}", sig, f"{name} argv  {snippet}")
            for aref in arefs:
                if os.path.isabs(aref) and os.path.isfile(aref):
                    scan_closure(source_key, label, aref, os.path.dirname(aref))

        targets = list(argv)
        for t in targets:
            if not t.startswith("/"):
                continue
            ext = os.path.splitext(t)[1].lower()
            if ext not in SCANNABLE_EXT:
                continue
            if not os.path.isfile(t):
                emit(f"{source_key}:{label}", "UNREACHABLE", f"{t}（plist 目标不可达）")
                continue
            scan_closure(source_key, label, t, os.path.dirname(t))


def handle_plugins(source_key, plugins_dir):
    if not os.path.isdir(plugins_dir):
        emit(source_key, "UNREACHABLE", f"{plugins_dir}（目录不存在）")
        return
    for root, _dirs, files in os.walk(plugins_dir):
        if "hooks.json" not in files:
            continue
        hj = os.path.join(root, "hooks.json")
        proot = os.path.dirname(root)
        handle_settings(f"{source_key}:{os.path.basename(proot)}", hj, proot, os.path.expanduser("~"))


def main():
    args = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
    main_repo = args.get("main")
    wt_repo = args.get("wt")
    home = args.get("home", os.path.expanduser("~"))

    handle_settings("main-settings", os.path.join(main_repo, ".claude/settings.json"), main_repo, home)
    handle_settings("main-settings-local", os.path.join(main_repo, ".claude/settings.local.json"), main_repo, home)
    handle_settings("wt-settings", os.path.join(wt_repo, ".claude/settings.json"), wt_repo, home)
    handle_settings("wt-settings-local", os.path.join(wt_repo, ".claude/settings.local.json"), wt_repo, home)
    handle_settings("global-settings", os.path.join(home, ".claude/settings.json"), home, home)
    handle_yaml_lefthook("main-lefthook", os.path.join(main_repo, "lefthook.yml"))
    handle_yaml_lefthook("wt-lefthook", os.path.join(wt_repo, "lefthook.yml"))
    handle_hookdir("git-hooks", main_repo)
    handle_launchagents("launch-agents", os.path.join(home, "Library/LaunchAgents"))
    handle_plugins("plugin-hooks", os.path.join(home, ".claude/plugins"))

    for line in out_lines:
        print(line)


if __name__ == "__main__":
    main()
