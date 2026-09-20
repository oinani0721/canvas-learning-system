"""负控段⑩ —— 只把**预检的 fenced block**挪到 Step 3 指令之后（`## Step 2.9` 标题留在原地）。

round-5 复核在 stderr 里留下的发现：次序门测的是「`## Step 2.9` **标题**的行号」，
块序门测的是「在 PYEOF 序列里的**序号**」—— **没有一道测「可执行的那个块本身是否排在
写分指令之前」**。标题留在原地、块挪到 Step 3 之后，「先拒后写」就失效了，而门全绿。

期望（加门之前）：两道结构门**都 PASS** ⇒ 缺口确认；
      （加门之后）：新门 `..._preflight_block_precedes_step3` **红**。
"""
p = "canvas-vault/.claude/skills/quiz-answer/SKILL.md"
t = open(p, encoding="utf-8").read()

FENCE_START = "```bash\nQUIZ_ANSWER_NODE='节点/<concept>.md' python3 - <<'PYEOF'\n"
i = t.index(FENCE_START)
j = t.index("\nPYEOF\n```\n", i) + len("\nPYEOF\n```\n")
block = t[i:j]
assert "quiz-answer/preflight" in block, "⛔ 切出来的不是预检块"

STEP4 = "## Step 4 · "
assert t.count(STEP4) == 1, f"Step 4 锚应恰 1 处, 实见 {t.count(STEP4)}"

rest = t[:i] + t[j:]
k = rest.index(STEP4)
t2 = rest[:k] + block + "\n" + rest[k:]

assert t2 != t, "变异没生效"
assert t2.count("## Step 2.9") == 1, "⛔ 标题被波及 —— 本段只搬块，不搬标题"
assert t2.index("## Step 2.9") < t2.index("## Step 3 · "), "⛔ 标题应仍在 Step 3 之前"
assert t2.index(FENCE_START) > t2.index("## Step 3 · "), "⛔ 块没搬到 Step 3 之后"
assert t2.count("quiz-answer/preflight") == t.count("quiz-answer/preflight"), "⛔ 块内容变了"
open(p, "w", encoding="utf-8").write(t2)
print("段⑩ 变异已注入：预检 fenced block 搬到 Step 3 之后（标题留在原地）")
