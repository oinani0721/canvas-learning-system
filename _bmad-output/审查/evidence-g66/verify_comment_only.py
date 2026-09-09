"""验证 1ccc9711 → dc6cfb17 是否只改了注释 / docstring —— 行级判据。

前两版判据都失败了，如实记下为什么：
  v1（Python tokenize 代码 token 流）：JS 门写在 Python r-string 里，改 JS 注释
      = STRING token 内容变了 ⇒ 报「有代码改动」。判据没错，粒度看不进字符串。
  v2（先剥 // 行再 tokenize）：有些 `//` 出现在字符串**内容**里，剥掉后引号不配对
      ⇒ tokenize 直接 TokenError 崩掉。

v3：对 diff 的每个 hunk，把 `-` 行与 `+` 行各自去掉注释（Python `#` / JS `//`）后
    取非空的代码残余，比较两个多重集。相同 = 这个 hunk 只动了注释。
    去注释用「最后一个 # 或 // 之前」的朴素规则——对本次改动足够（改动行里没有
    含 # 或 // 的字符串字面量），但这条局限如实写在这里，不当成通用工具。
"""

import re
import subprocess
from collections import Counter

REPO = (
    "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime"
)
A, B = "1ccc9711", "dc6cfb17"

diff = subprocess.run(
    ["git", "-C", REPO, "diff", "--no-color", "-U0", A, B, "--", ".", ":(exclude)_bmad-output"],
    capture_output=True,
    text=True,
    check=True,
).stdout


def code_part(line):
    """去掉行尾注释后的代码残余（strip 过）。纯注释行 → 空串。"""
    body = line[1:]  # 去掉 diff 的 +/-
    body = re.sub(r"\s*#.*$", "", body)
    body = re.sub(r"\s*//.*$", "", body)
    return body.strip()


hunks, cur = [], None
for ln in diff.splitlines():
    if ln.startswith("diff --git"):
        cur = None
    elif ln.startswith("@@"):
        cur = {"minus": [], "plus": [], "head": ln}
        hunks.append(cur)
    elif cur is not None and ln.startswith("-") and not ln.startswith("---"):
        cur["minus"].append(ln)
    elif cur is not None and ln.startswith("+") and not ln.startswith("+++"):
        cur["plus"].append(ln)

print(f"hunk 数: {len(hunks)}")
all_ok = True
for h in hunks:
    m = Counter(c for c in map(code_part, h["minus"]) if c)
    p = Counter(c for c in map(code_part, h["plus"]) if c)
    ok = m == p
    all_ok &= ok
    print(f"  {'✓' if ok else '✗'} {h['head'][:60]}  (-{len(h['minus'])} +{len(h['plus'])}; 代码残余 {sum(m.values())} vs {sum(p.values())})")
    if not ok:
        for k in (m - p) | (p - m):
            print(f"       差异残余: {k!r}")

print()
print(f"结论: 本轮{'每个 hunk 的代码残余都相同 ⇒ 只改了注释 / docstring' if all_ok else '**有真正的代码改动**'}")

# 反例自检: 同一判据跑 BASE→HEAD 必须报「有代码改动」
diff2 = subprocess.run(
    ["git", "-C", REPO, "diff", "--no-color", "-U0", "72ab01ed", B, "--", ".", ":(exclude)_bmad-output"],
    capture_output=True,
    text=True,
    check=True,
).stdout
bad = 0
cur = None
for ln in diff2.splitlines():
    if ln.startswith("@@"):
        cur = {"minus": [], "plus": []}
    elif cur is not None and ln.startswith("-") and not ln.startswith("---"):
        cur["minus"].append(ln)
    elif cur is not None and ln.startswith("+") and not ln.startswith("+++"):
        cur["plus"].append(ln)
        m = Counter(c for c in map(code_part, cur["minus"]) if c)
        p = Counter(c for c in map(code_part, cur["plus"]) if c)
        if m != p:
            bad += 1
print(f"反例自检（BASE→HEAD 跑同一判据）: 有代码改动的 hunk {bad} 个 ⇒ 判据{'不是恒真 ✓' if bad else '**恒真, 无效** ✗'}")
