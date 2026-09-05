#!/usr/bin/env python3
"""DEBT-15 · 从一个文件中解析出所有 git 写操作 occurrence。

BATCH-2026-08-29-第六批 / CARD-DEBT-15

为什么不用逐行正则（Codex round-1 的 BLOCKER 1-4 全部源于此）：

  B1 粒度：`git add -A` 与 `git add openapi.json` 必须是**不同**的签名。
           前者覆盖整个工作树，后者只补一个生成物。用 verb 当签名会让
           危险的全量 add 命中窄 add 的 KEEP 登记而放行。
  B2 一行多命令：`git commit -am auto && git push origin HEAD` 是两个
           occurrence。"一行一签名"会让未登记的 commit 被已登记的 push 掩盖。
           行级贪婪正则还会把 `git push rogue HEAD # git push origin HEAD`
           解析成 origin —— 实际执行的却是 rogue。
  B3 命令链与引号：`echo ready && git push rogue HEAD` 不能因首 token 是
           echo 就丢掉整行；`"git" push` 的可执行名带引号；
           `git -C "$REPO" push` 在 verb 前插了 global option。
  B4 递归：A.sh 里 `bash B.sh`，B.sh 的 git push 必须能被追到。

输出（每行一条 occurrence，TAB 分隔）：
    OCC <lineno> <signature> <snippet>
    REF <lineno> <被调用的脚本路径>        # 供调用方做递归闭包
    UNANALYZABLE <lineno> <原因> <snippet> # 解析不了 ⇒ 调用方必须 FAIL（fail-closed）

签名形状：
    add:ALL          git add -A / . / --all / -u        （覆盖整个工作树）
    add:path         git add <具体路径>                  （窄范围）
    commit           git commit …
    push:<remote>    git push <remote> …
    push:DEFAULT     git push（无显式 remote，走默认上游）
"""

import os
import re
import shlex
import sys
import tokenize

# 只把这些当作「可执行 git」。basename 比对，故 /usr/bin/git 亦可。
GIT_NAMES = {"git"}

# git 在 <verb> 之前允许的全局选项。带值的需要多吃一个 token。
GIT_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
GIT_GLOBAL_FLAGS = {
    "--no-pager",
    "--paginate",
    "--bare",
    "--literal-pathspecs",
    "--no-replace-objects",
    "--no-optional-locks",
}

# 递归闭包：这些命令的第一个非选项参数是「另一个待扫描的脚本」
SCRIPT_RUNNERS = {
    "bash",
    "sh",
    "zsh",
    "dash",
    "ksh",
    "source",
    ".",
    "node",
    "nodejs",
    "python",
    "python3",
    "ruby",
    "perl",
}

# 可以出现在真实命令**之前**的 shell 关键字/前缀。必须跳过，否则
#   if ! git commit -m "$MSG"; then …
# 的首 token 是 `if`，整条 commit 逃逸（实测：stop-auto-sync-to-remote.sh:132）。
# 用精确白名单而非「一路找 git」：后者会把 echo "To track: git add <f>"
# 这类文案误当命令（负验证 N6 守此条）。
SHELL_PREFIX = {
    "if",
    "then",
    "else",
    "elif",
    "while",
    "until",
    "do",
    "!",
    "time",
    "command",
    "nohup",
    "exec",
    "eval",
    "builtin",
    "sudo",
    "{",
    "(",
    "&&",
    "||",
}

# python/js 里唯一能真正执行 git 的途径。行内无这些关键词 ⇒ git 只出现在
# 日志/文案字符串里（实测误报：security_reminder_hook.py 的 debug_log(...)）。
# 关键：要求这些名字后面紧跟 `(` 或 `.`，即它确实是**被调用**的，
# 而不是恰好作为字符串元素出现。否则
#   AUDIT_KEYWORDS = ["subprocess", "git", "push", "x"]
# 这种纯数据会被误判成进程调用（实测误报 N24）。
EXEC_API = re.compile(
    r"\b(subprocess|spawnSync|spawn|execSync|execFileSync|execFile|exec|system|Popen|"
    r"check_output|check_call|execa|shelljs|child_process|popen)\s*[.(]"
)

PREFILTER = re.compile(r"\b(git|" + "|".join(re.escape(r) for r in sorted(SCRIPT_RUNNERS)) + r")\b")

SHELL_EXT = {".sh", ".bash", ".zsh", ""}
PY_EXT = {".py"}
JS_EXT = {".js", ".mjs", ".cjs", ".ts"}
YAML_EXT = {".yml", ".yaml"}

# yaml 里命令写成 `run: git push backup HEAD`，`run:` 会占据首 token 位，
# 使 classify_git_command 看到的 tokens[0] 是 "run:" 而非 "git" ⇒ 整条漏报
# （实测：主仓 lefthook.yml post-commit 的两条 push 全部逃逸）。
# 只剥这几个「命令值」键，不用 seek_git —— 否则 yaml 里的
# `echo "To track: git add <file>"` 文案会被误当命令（负验证 N6 守此条）。
YAML_CMD_KEY = re.compile(r"^\s*-?\s*(run|cmd|command|script|entry|exec)\s*:\s*")


def py_multiline_string_lines(path):
    """python 三引号块占据的行号集合（docstring / 多行 PROMPT = 文档，非代码）。

    判别线取「跨行」而非「所有字符串」：进程式调用的参数
    subprocess.run(["git","push"]) 总在单行内，去掉所有 STRING token 会连它一起抹掉。
    """
    out = set()
    try:
        with open(path, "rb") as fh:
            for tok in tokenize.tokenize(fh.readline):
                if tok.type == tokenize.STRING and tok.start[0] != tok.end[0]:
                    out.update(range(tok.start[0], tok.end[0] + 1))
    except Exception:
        pass
    return out


def quotes_balanced(s):
    """判断一行的引号是否闭合。用于把跨物理行的字符串合并成一条逻辑命令。

    不合并的后果：stop-auto-sync-to-remote.sh 的
        COMMIT_MSG="chore(auto-sync): …
        …多行…
        Co-Authored-By: …"
    会在中途被腰斩，产出 unterminated quote 的 UNANALYZABLE，
    把同文件里真实的 `git commit -m "$COMMIT_MSG"` 签名一并淹没。
    """
    q = None
    i = 0
    while i < len(s):
        c = s[i]
        if q:
            if c == "\\":
                i += 2
                continue
            if c == q:
                q = None
        elif c in ("'", '"'):
            q = c
        elif c == "#" and (i == 0 or s[i - 1].isspace()):
            break
        i += 1
    return q is None


def split_simple_commands(line):
    """把一行拆成若干 simple command，按 && || ; | 与换行分隔。

    在引号外才认操作符；行内 `#` 之后（引号外）视为注释丢弃。
    返回 [(cmd_text, ...)]。解析失败抛异常，由调用方转 UNANALYZABLE。
    """
    parts, buf = [], []
    quote = None
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            elif ch == "\\" and i + 1 < n:
                i += 1
                buf.append(line[i])
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if ch == "#":
            # 引号外的 # 起注释；但 #{ 之类以及紧贴前一个非空白字符的情况
            # （如 URL 里的 fragment）不当注释——保守起见只在前面是空白或行首时切
            if not buf or buf[-1].isspace():
                break
            buf.append(ch)
            i += 1
            continue
        if ch == "\\" and i + 1 < n:
            buf.append(ch)
            i += 1
            buf.append(line[i])
            i += 1
            continue
        two = line[i : i + 2]
        if two in ("&&", "||"):
            parts.append("".join(buf))
            buf = []
            i += 2
            continue
        if ch in (";", "|", "\n"):
            parts.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    if quote:
        raise ValueError("unterminated quote")
    parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def classify_git_command(tokens, seek_git=False):
    """给定一个 simple command 的 token 列表，若是 git 写操作则返回签名，否则 None。

    seek_git=True 用于 python/js 的进程式调用：折平
    subprocess.run(["git","push",…]) 之后，首 token 仍是 `subprocess.run`，
    真正的 `git` 在其后。此时跳过前导 token 直到找到 git。
    shell 场景必须保持 seek_git=False，否则 `echo "see git push docs"`
    这类文案会被误当成命令（shell 侧靠 && || ; | 拆分已足够定位）。

    返回 (signature, None) 或 (None, reason_if_unanalyzable) 或 (None, None)。
    """
    idx = 0
    # 跳过 shell 关键字前缀与前导环境变量赋值：
    #   if ! FOO=bar git push …
    while idx < len(tokens) and (tokens[idx] in SHELL_PREFIX or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[idx])):
        idx += 1
    if idx >= len(tokens):
        return None, None
    if seek_git:
        while idx < len(tokens) and os.path.basename(tokens[idx]) not in GIT_NAMES:
            idx += 1
        if idx >= len(tokens):
            return None, None
    exe = os.path.basename(tokens[idx])
    if exe not in GIT_NAMES:
        return None, None
    idx += 1
    # 跳过 git 的全局选项（B3：git -C "$REPO" push …）
    while idx < len(tokens):
        t = tokens[idx]
        if t in GIT_GLOBAL_WITH_VALUE:
            idx += 2
            continue
        if any(t.startswith(g + "=") for g in GIT_GLOBAL_WITH_VALUE) or t in GIT_GLOBAL_FLAGS:
            idx += 1
            continue
        break
    if idx >= len(tokens):
        return None, "git with no subcommand"
    verb = tokens[idx]
    rest = tokens[idx + 1 :]

    if verb == "add":
        # B1：区分覆盖整个工作树的 add 与只补具体路径的 add
        allish = {"-A", "--all", ".", "-u", "--update", "--no-ignore-removal"}
        positional = [t for t in rest if not t.startswith("-")]
        if any(t in allish for t in rest) or any(p in (".", "./", "*") for p in positional):
            return "add:ALL", None
        if not positional:
            # `git add` 无路径无 -A：交互式/无操作，仍登记为 ALL 以免放宽
            return "add:ALL", None
        if any("$" in p or "`" in p for p in positional):
            return None, "git add with dynamic pathspec"
        return "add:path", None

    if verb == "commit":
        return "commit", None

    if verb == "push":
        remote = None
        skip_next = False
        for t in rest:
            if skip_next:
                skip_next = False
                continue
            if t in ("--repo", "-o", "--push-option", "--receive-pack", "--exec"):
                skip_next = True
                continue
            if t.startswith("--repo="):
                remote = t.split("=", 1)[1]
                break
            if t.startswith("-"):
                continue
            remote = t
            break
        if remote is None:
            return "push:DEFAULT", None
        if "$" in remote or "`" in remote:
            return None, "git push with dynamic remote"
        return f"push:{remote}", None

    return None, None


def inline_shell_code(tokens):
    """若该命令是 `sh -c '<code>'` / `bash -c '<code>'`，返回内联代码。

    Codex round-2 B-05 实测逃逸：settings exec-form 的 `sh -c "git push rogue"`
    整条被忽略（-c 之后被当成「不是路径」就丢掉了），必须回头当命令解析。
    """
    idx = 0
    while idx < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[idx]):
        idx += 1
    if idx >= len(tokens):
        return None
    if os.path.basename(tokens[idx]) not in SCRIPT_RUNNERS:
        return None
    for j in range(idx + 1, len(tokens)):
        if tokens[j] in ("-c", "--command"):
            if j + 1 < len(tokens):
                return tokens[j + 1]
            return None
        if not tokens[j].startswith("-"):
            return None
    return None


def direct_script_call(tokens):
    """首 token 本身就是一个脚本路径（`./helper.sh` / `/abs/helper.sh`），无解释器前缀。

    Codex round-2 B-05 实测逃逸：直接执行 rogue-helper.sh 时递归闭包看不见它。
    """
    idx = 0
    while idx < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[idx]):
        idx += 1
    if idx >= len(tokens):
        return None
    t = tokens[idx]
    if os.path.basename(t) in SCRIPT_RUNNERS or os.path.basename(t) in GIT_NAMES:
        return None
    # 路径 token 不含空格、不以 - 开头。缺这两条会把防护清单里的字符串
    # 字面量误当路径——实测误报：guard-hook.sh 的数组元素含斜杠，
    # 曾被解析成脚本路径并报 UNREACHABLE。
    if not t or " " in t or t.startswith("-"):
        return None
    ext = os.path.splitext(t)[1].lower()
    if ext in (".sh", ".bash", ".zsh", ".py", ".js", ".mjs", ".cjs", ".rb", ".pl", ".cmd"):
        return t
    # 无扩展名时要求明确的路径形态，不认裸词
    if t.startswith("./") or t.startswith("../") or t.startswith("/"):
        return t
    return None


def script_reference(tokens):
    """若该 simple command 是在调用另一个脚本，返回被调脚本路径（供递归闭包）。"""
    idx = 0
    while idx < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[idx]):
        idx += 1
    if idx >= len(tokens):
        return None
    exe = os.path.basename(tokens[idx])
    if exe not in SCRIPT_RUNNERS:
        return None
    for t in tokens[idx + 1 :]:
        # -e / -c / -- 之后是**内联代码**，不是脚本路径
        # （如 perl -e 'exec {$ARGV[0]} @ARGV'、sh -c '…'）
        if t in ("-e", "-c", "--eval", "-E"):
            return None
        if t.startswith("-"):
            continue
        return t
    return None


def normalize_process_call(text):
    """把进程式调用折平：subprocess.run(["git","push",...]) → git push …

    括号/方括号必须一并折：只折引号逗号会得到 "git [push"，依旧不匹配。
    """
    return re.sub(r"[\[\](),]", " ", text)


def emit(kind, lineno, *fields):
    print("\t".join([kind, str(lineno)] + [str(f) for f in fields]))


def scan(path):
    ext = os.path.splitext(path)[1].lower()
    is_py = ext in PY_EXT
    is_js = ext in JS_EXT
    is_yaml = ext in YAML_EXT
    skip = py_multiline_string_lines(path) if is_py else set()

    try:
        with open(path, "r", errors="replace") as fh:
            raw_lines = fh.readlines()
    except Exception as exc:
        emit("UNANALYZABLE", 0, f"cannot read: {type(exc).__name__}", path)
        return

    # shell 续行合并：末尾反斜杠把下一行接上，否则命令会被腰斩
    merged = []  # (lineno_of_first_physical_line, text)
    buf, start = "", None
    for i, ln in enumerate(raw_lines, 1):
        stripped = ln.rstrip("\n")
        if start is None:
            start = i
        if stripped.endswith("\\") and not is_py and not is_js:
            buf += stripped[:-1] + " "
            continue
        combined = buf + stripped
        # 跨行字符串：引号未闭合就继续吃下一行（上限 40 行防跑飞）
        if not is_py and not is_js and not quotes_balanced(combined) and i - (start or i) < 40:
            buf = combined + "\n"
            continue
        merged.append((start, combined))
        buf, start = "", None
    if buf:
        merged.append((start or len(raw_lines), buf))

    # heredoc 体：`cmd <<'TAG'` 到独立一行 `TAG` 之间全是文本，不是命令。
    # 实测误报 N23：post-tool-router.sh 里 cat <<'DOC' … DOC 的正文被当成 git push。
    heredoc_lines = set()
    if not is_py and not is_js:
        cur_tag = None
        for idx_m, (mln, mtext) in enumerate(merged):
            if cur_tag is not None:
                heredoc_lines.add(mln)
                if mtext.strip() == cur_tag:
                    cur_tag = None
                continue
            m = re.search(r"<<-?\s*([\"']?)([A-Za-z_][A-Za-z0-9_]*)\1", mtext)
            if m:
                cur_tag = m.group(2)

    for lineno, text in merged:
        if lineno in skip or lineno in heredoc_lines:
            continue
        stripped = text.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # 纯字符串字面量行 = 防护清单 / deny 规则 / 描述文案，是写副作用的反面。
        # 例如 settings.json 的 deny 条目、guard-hook.sh 的拦截项数组元素。
        # （负验证 N6 反向哨兵守此条）
        if len(stripped) > 1 and stripped[0] in ('"', "'") and stripped.rstrip(",").endswith(stripped[0]):
            # ⚠️ 只有「引号内含空格的多词短语」才是文案/deny 条目。
            #    引号内是单个无空格 token 的，是带引号的**路径调用**，
            #    如 "/abs/path/helper.sh" —— 不能跳过（实测漏报：N18）。
            inner = stripped.rstrip(",")[1:-1]
            if " " in inner:
                continue
        # 预过滤：既要留住含 git 的行，也要留住「调用其它脚本」的行——
        # 后者是递归闭包的入口（bash ./child.sh 里一个 git 字都没有）。
        if not PREFILTER.search(text):
            continue

        if is_yaml:
            text = YAML_CMD_KEY.sub("", text)

        if is_py or is_js:
            # 这两类文件里 git 的唯一执行途径是进程 API。无关键词 ⇒ 日志/文案。
            if not EXEC_API.search(text):
                continue
            candidate = normalize_process_call(text)
        else:
            candidate = text

        try:
            cmds = split_simple_commands(candidate)
        except Exception as exc:
            emit("UNANALYZABLE", lineno, f"cannot split: {exc}", stripped[:90])
            continue

        for cmd in cmds:
            try:
                tokens = shlex.split(cmd, comments=False, posix=True)
            except ValueError as exc:
                emit("UNANALYZABLE", lineno, f"cannot lex: {exc}", cmd[:90])
                continue
            if not tokens:
                continue
            sig, reason = classify_git_command(tokens, seek_git=(is_py or is_js))
            if reason:
                emit("UNANALYZABLE", lineno, reason, cmd[:90])
            elif sig:
                emit("OCC", lineno, sig, cmd[:90])
            # sh -c '<code>' 的内联代码：当作命令继续拆解
            inline = inline_shell_code(tokens)
            if inline:
                try:
                    for sub in split_simple_commands(inline):
                        subtok = shlex.split(sub, comments=False, posix=True)
                        if not subtok:
                            continue
                        ssig, sreason = classify_git_command(subtok)
                        if sreason:
                            emit("UNANALYZABLE", lineno, sreason, sub[:90])
                        elif ssig:
                            emit("OCC", lineno, ssig, f"[-c] {sub[:80]}")
                        sref = script_reference(subtok) or direct_script_call(subtok)
                        if sref:
                            emit("REF", lineno, sref)
                except Exception as exc:
                    emit("UNANALYZABLE", lineno, f"cannot lex -c payload: {exc}", inline[:90])
            ref = script_reference(tokens) or direct_script_call(tokens)
            if ref:
                emit("REF", lineno, ref)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(0)
    scan(sys.argv[1])
