"""负控段③ —— 只把 `## Step 2.9` 整段挪到 `## Step 3` 之后（顺序变，内容一字不动）。

这一段拆的是**顺序**这个性质本身：预检块写得再对，排在写分之后也救不了半态白板。
⛔ 只搬位置：段落文本逐字节不变（脚本自证搬前搬后该段 sha256 相同），主写点块不受影响。

期望：..._step29_precedes_step3 FAILED（次序门）；
      §二.4 AST 仍 `main 1`（证明剪动没波及主块）；
      ⚠️ 实测更正（本脚本初版预测错了，按实测改的是预测不是判据）：
      ..._preflight_is_the_second_pyeof_block_and_main_stays_single **仍绿**。
      原因：本段把 Step 2.9 搬到 Step 3↔Step 4 之间，而主写点块在 Step 4c ——
      预检块仍是第 2 个 PYEOF 块。⇒ 两个结构门测的是**正交性质**：
        · 次序门     = 相对 Step 3 的位置（决定半态白板会不会发生）；
        · 块序/过滤门 = 在 PYEOF 序列里的位置（决定 `_MAIN_BLOCKS` 过滤器会不会被污染）。
      一个变异只动得了前者，这正是「各只拆一层」该有的样子。
"""
import hashlib

p = "canvas-vault/.claude/skills/quiz-answer/SKILL.md"
t = open(p, encoding="utf-8").read()

A = "## Step 2.9 "
B = "## Step 3 · "
C = "## Step 4 · "
for m in (A, B, C):
    assert t.count(m) == 1, f"锚 {m!r} 应恰 1 处, 实见 {t.count(m)}"
i29, i3, i4 = t.index(A), t.index(B), t.index(C)
assert i29 < i3 < i4, "前提没成立: 改前次序本就不对"

seg = t[i29:i3]
before = hashlib.sha256(seg.encode()).hexdigest()[:16]
t2 = t[:i29] + t[i3:i4] + seg + t[i4:]
assert len(t2) == len(t), "⛔ 长度变了 = 不只是搬位置"
after = hashlib.sha256(t2[t2.index(A):t2.index(C)].encode()).hexdigest()[:16]
assert before == after, f"⛔ 段落内容被改了: {before} != {after}"
assert t2.index(B) < t2.index(A), "⛔ 没搬成功"
open(p, "w", encoding="utf-8").write(t2)
print(f"段③ 变异已注入：Step 2.9 段搬到 Step 3 之后（段落 sha256[:16]={before}，搬前搬后相同 = 只动位置）")
