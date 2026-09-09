#!/usr/bin/env python
"""逐 commit 对照自检 —— 把 Codex 一直在替我做的事变成例行检查。

用法: python self-regression-diff.py <旧 SHA> [新 SHA=工作区]

r23~r26 我连续四轮引入回归, 每次都是 Codex 用「旧版命中、新版 []」的对照找出来的。
这个脚本在**送审之前**自己做一遍: 把两个版本的模块各自加载, 用同一批形态语料跑
全部判据, 逐条比对。任何「旧抓新漏」或「旧静新报」都当场打印。

⚠️ 它不是判据本身, 不进 `tests/skills` —— 放在 evidence 下, 送审前手动跑。
⚠️ 它只**列出差异**, 不判对错: 「旧抓新漏」既可能是新引入的漏检, 也可能是修掉了一个
   **误报**(旧版报的那条本来就不该报)。分类要人做 —— 脚本的价值是让差异**无处躲**,
   不是替我下结论。
⚠️ 对照对象要选**紧邻的上一个 commit**。跨多轮对照会把「本轮引入」和「前几轮修好」
   混在一起, 看不出是谁干的。
"""

import ast
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

REL = "backend/tests/skills/test_skill_portability_lint.py"
GOOD = 'P = "/t" + "mp/cls-exam/x"'
BAD = 'P = "/etc/passwd"'

#: 历代复核给出的形态语料。每条 = (标签, fence info, 正文)。
#: 只放**输入**, 不放期望值 —— 这个脚本比的是两个版本的**差异**, 不是对错。
CORPUS: list[tuple[str, str, str]] = [
    ("r21 相邻两行重赋值", "python", f"{GOOD}\n{BAD}"),
    ("r21 元组解包", "python", f"{GOOD}; P, = ('/etc/passwd',)"),
    ("r22 循环回边", "python", f"for i in (0, 1):\n    if i:\n        {BAD}\n        break\n    {GOOD}"),
    ("r22 两支都合规", "python", "if c:\n    P = '/tmp/cls-exam/a'\nelse:\n    P = '/tmp/cls-exam/b'"),
    ("r22 heredoc", "sh", f"python3 - <<'PYEOF'\n{GOOD}\n{BAD}\nPYEOF"),
    ("r23 if False 里的合规写入", "python", f"{BAD}\nif False:\n    {GOOD}"),
    ("r23 生成器延迟求值", "python", f"g = ((P := '/etc/passwd') for _ in (1,))\n{GOOD}\nnext(g)"),
    ("r23 循环后无条件合规", "python", f"for i in (1,):\n    {BAD}\n{GOOD}"),
    ("r23 nonlocal", "python", f"def outer():\n    {GOOD}\n    def inner():\n        nonlocal P\n        {BAD}\n    inner()\n    return P"),
    ("r23 默认参数", "python", f"{GOOD}\ndef f(x=(P := '/etc/passwd')):\n    pass"),
    ("r23 global", "python", f"def f():\n    global P\n    {BAD}\n{GOOD}\nf()"),
    ("r24 with suppress", "python", f"from contextlib import suppress\n{BAD}\nwith suppress(E):\n    1 / 0\n    {GOOD}"),
    ("r24 裸 return", "python", f"def f():\n    {BAD}\n    return\n    {GOOD}"),
    ("r24 fd 复制 <&3", "sh", f"python3 - 3<<'A' <<'B' <&3\n{GOOD}\n{BAD}\nA\nX=0\nB"),
    ("r24 管道两命令", "sh", f"python3 - <<'A' | cat <<'B'\n{GOOD}\n{BAD}\nA\nX=0\nB"),
    ("r24 </dev/null 覆盖", "sh", f"python3 - <<'A' </dev/null\n{GOOD}\n{BAD}\nA"),
    ("r24 -W ignore", "sh", f"python3 -W ignore <<'A'\n{GOOD}\n{BAD}\nA"),
    ("r24 注释里的假 heredoc", "sh", f"# <<'NO'\npython3 - <<'A'\n{GOOD}\n{BAD}\nA"),
    ("r24 cat heredoc", "sh", f"cat <<'A'\n{GOOD}\n{BAD}\nA"),
    ("r24 globals()[…]=", "python", f"{GOOD}\nglobals()['P'] = '/etc/passwd'"),
    ("r25 引号里的 '<file'", "sh", f"python3 - <<'A' '<not-a-file'\n{GOOD}\n{BAD}\nA"),
    ("r25 -Bc 组合", "sh", f"python3 -Bc '{GOOD}; {BAD}'"),
    ("r25 1 << 2", "python", f"{GOOD}\nN = 1 << 2\n{BAD}"),
    ("r25 元组目标 globals()", "python", f"{GOOD}\n(globals()['P'],) = ('/etc/passwd',)"),
    ("r25 from x import *", "python", f"{GOOD}\nfrom os.path import *"),
    ("r25 仅注解绑定", "python", f"def outer():\n    {GOOD}\n    def middle():\n        P: str\n        def inner():\n            nonlocal P\n            {BAD}\n        inner()\n    middle()\n    return P"),
    ("r26 heredoc 缺结束标记", "sh", f"python3 - <<'END'\n{GOOD}\n{BAD}"),
    ("r26 1 << 2 + bare 2", "python", f"{GOOD}\nN = 1 << 2\n2\n{BAD}"),
    ("r26 -Wignore::Deprecation", "sh", f"python3 -Wignore::DeprecationWarning - <<'END'\n{GOOD}\n{BAD}\nEND"),
    ("r26 (P): str", "python", f"def outer():\n    {GOOD}\n    def middle():\n        (P): str\n        def inner():\n            nonlocal P\n            {BAD}\n        inner()\n    middle()\n    return P"),
    ("r26 sys.modules[…].P =", "python", f"{GOOD}\nimport sys\nsys.modules[__name__].P = '/etc/passwd'"),
    ("r26 page.reload()", "python", f"{GOOD}\npage.reload()"),
    ("r26 config.update(globals())", "python", f"{GOOD}\nconfig = {{}}\nconfig.update(globals())"),
    ("r26 args.__dict__[…]=", "python", f"{GOOD}\nargs.__dict__['verbose'] = True"),
    ("r26 cache[globals()[…]]=", "python", f"{GOOD}\ncache[globals()['P']] = 1"),
]

#: URL 判据的语料(直接传行, 不包 fence)。
URL_CORPUS: list[tuple[str, str]] = [
    ("r20 引号内的 #", 'printf "#"; unset CLS_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'),
    ("r21 ${OTHER:-…}/${VAR}", 'curl "${OTHER:-http://localhost:8011}/${CLS_BACKEND_URL}"'),
    ("r21 env -u OTHER", """env -u OTHER sh -c 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'"""),
    ("r22 ${OTHER:- #}", ': ${OTHER:- #}; unset CLS_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'),
    ("r22 @userinfo", 'curl "${CLS_BACKEND_URL:-http://localhost:8011}@localhost/x"'),
    ("r23 :pw@host", 'curl "${CLS_BACKEND_URL:-http://localhost:8011}":pw@localhost/x'),
    ("r23 builtin printf -v", 'builtin printf -v CLS_BACKEND_URL %s ""; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'),
    ("r23 $(printf %s \"(\")", 'echo "$(printf %s "(")"; # unset CLS_BACKEND_URL'),
    ("r25 转义 \\>&", 'true \\>& printf -v CLS_BACKEND_URL %s ""; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'),
    ("r25 unset C'LS'_…", """unset C'LS'_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x\""""),
    ("r26 printf 里的 unset", """printf '%s %s' unset C'LS'_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x\""""),
    ("r26 unset '-f'", """unset '-f' C'LS'_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x\""""),
    ("正控 整改形态", 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'),
]


def load(source: str, tag: str):
    """把一份源码当模块加载。写临时文件是因为判据里有 `Path(__file__)` 推导。"""
    tmp = Path(tempfile.mkdtemp()) / "lint.py"
    tmp.write_text(source, encoding="utf-8")
    real = Path(REL).resolve()
    spec = importlib.util.spec_from_file_location(f"lint_{tag}", real)
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = str(real)
    sys.modules[f"lint_{tag}"] = mod
    exec(compile(source, str(real), "exec"), mod.__dict__)
    return mod


def probe(mod) -> dict[str, object]:
    out: dict[str, object] = {}
    for label, info, text in CORPUS:
        block = f"```{info}\n{text}\n```"
        for judge in ("escaping_tmp_paths", "suspicious_tmp_lines", "dynamic_tmp_join_lines",
                      "parent_dir_prose_lines", "opaque_tmp_lines", "url_default_overridden_lines",
                      "tmp_block_fingerprints"):
            try:
                out[f"{label}|{judge}"] = repr(getattr(mod, judge)(block))
            except Exception as exc:  # noqa: BLE001
                out[f"{label}|{judge}"] = f"<{type(exc).__name__}>"
    for label, line in URL_CORPUS:
        try:
            out[f"{label}|_url_override_hit"] = repr(mod._url_override_hit(line))
        except Exception as exc:  # noqa: BLE001
            out[f"{label}|_url_override_hit"] = f"<{type(exc).__name__}>"
    return out


def main() -> int:
    old_sha = sys.argv[1]
    new_sha = sys.argv[2] if len(sys.argv) > 2 else None
    old_src = subprocess.run(["git", "show", f"{old_sha}:{REL}"], capture_output=True, text=True, check=True).stdout
    new_src = (
        subprocess.run(["git", "show", f"{new_sha}:{REL}"], capture_output=True, text=True, check=True).stdout
        if new_sha
        else Path(REL).read_text(encoding="utf-8")
    )
    ast.parse(old_src), ast.parse(new_src)
    old, new = probe(load(old_src, "old")), probe(load(new_src, "new"))
    diffs = [(k, old[k], new[k]) for k in sorted(set(old) | set(new)) if old.get(k) != new.get(k)]
    print(f"语料 {len(CORPUS)} 形态 x 7 判据 + {len(URL_CORPUS)} URL 行 = {len(old)} 个观测点")
    print(f"对照 {old_sha} → {new_sha or '工作区'}")
    if not diffs:
        print("✅ 逐条相同 —— 未发现旧抓新漏 / 旧静新报")
        return 0
    print(f"⚠️  {len(diffs)} 处差异:")
    for k, o, nv in diffs:
        arrow = "旧抓新漏" if o != "[]" and nv in ("[]", "False") else ("旧静新报" if o in ("[]", "False") else "变化")
        print(f"  [{arrow}] {k}\n      旧 {o[:90]}\n      新 {nv[:90]}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
