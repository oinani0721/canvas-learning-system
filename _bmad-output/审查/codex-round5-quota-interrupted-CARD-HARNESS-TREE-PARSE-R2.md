> 批次: BATCH-2026-09-18-第十五批 · 车道 P6 · 卡 CARD-HARNESS-TREE-PARSE-R2 round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HARNESS-TREE-PARSE-R2-r5.md)"`
> 审查绑定: `c50b83b0`（送审时 HEAD；代码面与 round-4 整改后的 `a83cd791` 逐字同）
> 会话头自证（抄 `.stderr` 中的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: gpt-6-astra`（第 5 行） / `reasoning effort: ultra`（第 9 行）

---

# ⚠️ 本文件是**车道记录**，不是 Codex 的输出

**round-5 的 stdout 是 0 字节**（`wc -c` 实测 0），原因写在 `.stderr` 末尾：

```
ERROR: You've hit your usage limit. … try again at Sep 23rd, 2026 11:05 AM.
```

`tokens used: 51,556`。0 字节的 `.md` **未入库**（协议：0 字节存档不入 commit）。
**配额已复测**（不继承「重置时间」这一次观测）：2026-09-19 用最小 prompt 重发 → 同样
`rc=1` + 同一条 usage limit ⇒ **真耗尽**。⇒ 按协议「重发一次，再 0 字节 → 主 session
人审替代，不等配额」。

---

## 但它被切断前留下了一条**真发现**，车道已独立验证并修好

`.stderr` 的推理轨迹走到了 `Preparing pure-memory tests → Testing in-memory mutation →
Reviewing preflight writes → Validating harness findings → Reviewing final changes`，
并且**真的跑了一段只读变异实验**。原样抄录（`exec … succeeded in 0ms` 之后的输出）：

```
BASELINE
test_g33r2_step29_precedes_step3 PASS
test_g33r2_preflight_is_the_second_pyeof_block_and_main_stays_single PASS
NEGATIVE: preflight fenced block moved immediately before Step 4, after Step 3 instructions
test_g33r2_step29_precedes_step3 PASS
test_g33r2_preflight_is_the_second_pyeof_block_and_main_stays_single PASS
positions [('## Step 2.9', 9563), ('## Step 3 ·', 10181),
           ("QUIZ_ANSWER_NODE='节点/<concept>.md' python3 - <<'PYEOF'", 10837),
           ('## Step 4', 13907)]
```

### 这条发现是什么

把**可执行的那个预检 fenced block** 单独挪到 Step 3 指令**之后**（`## Step 2.9` 标题留在
原地），**两道结构门都 PASS**：

| 门 | 它实际测的 | 为什么看不见 |
|---|---|---|
| `..._step29_precedes_step3` | `## Step 2.9` **标题**的行号 | 标题没动 |
| `..._preflight_is_the_second_pyeof_block_…` | 块在 **PYEOF 序列里的序号** | 序号没变（A3 第 1、预检第 2、主块第 3） |

⇒ **缺的是第三个维度：块自己在文件里的位置。** 标题在前、块在后，「先拒后写」当场失效，
而两道门都绿。这覆盖的是本卡三大收口之一。

### 车道的处置（**不采信，先独立复现**）

1. **独立验证**（`probe-preflight-block-position-*.txt` + 入档脚本 `negctl-10-mutant-source.py`）：
   把块搬到 Step 3 之后，实测 `## Step 2.9` 在行 189、`## Step 3 ·` 在行 205、
   预检 fence 在行 **215** —— 两道旧门**确实都 PASS**。缺口成立。
2. **加门** `..._preflight_block_precedes_step3`：把三样东西钉在一条线上 ——
   `## Step 2.9` 标题 < **预检 fence** < `## Step 3 ·` 标题；并顺带核那个 fence 之后
   确实有 `quiz-answer/preflight` 标记（否则比的是另一个块）。
3. **负控段⑩** 验证它不是恒绿：同一变异下**只有新门红**，两道旧门仍 PASS ——
   正说明它们测的是别的性质，新门补的是第三个维度。

---

## ⛔ 移交主 session（协议 §1 / D-15）

**本卡状态**：Codex 5 轮（= 卡文轮次上限），其中 round-1 与 round-5 因配额中断 stdout 0 字节
（两轮都在 stderr 里留下了实质发现，车道都独立复现并整改了）。

- **round-4 是完整的一轮**：绑 `3c92b220`（代码面 = `6660e5a1`），`BLOCKER 0 / HIGH 0`，
  正文 `**BLOCKER**` / `**HIGH**` 小节各 0 个。
- round-4 之后车道做了两件事：① 整改 round-4 的 L1/L2/L3（两条门未覆盖 + 一条诚实性）；
  ② 整改 round-5 在 stderr 里留下的那条（预检块位置门）。
  **这两次改动之后的那一轮复核发不出去**。

请主 session 裁定：
1. 以人审替代最后那一轮 —— 可核的输入面 = 本文件 + `probe-preflight-block-position-*.txt` +
   **负控十段**（每段只拆一层、EXIT trap 还原、跑前/还原后 shasum 逐字同）+ 全部代码 commit 的 diff；
2. 或排入配额恢复后的补审（存档名预留 `codex-review-CARD-HARNESS-TREE-PARSE-R2-r6.md`；
   ⚠️ 轮次后缀一律小写 `-rN`，本卡卡号已含 `-R2`）。
   ⚠️ 若走这条，**轮次会超过卡文写的上限 5** —— 需主 session 明确放宽。

**车道未自判通过**：最后那一轮没有分级输出，「BLOCKER = 0、HIGH = 0」**在最终代码上无法
自证**，按未完成登记。

> ⚠️ 附带一条观察，供排批参考：本卡 5 轮里有 **2 轮**因配额中断。两次的 `try again at`
> 分别是 `Sep 24th` 与 `Sep 23rd` —— 第一次报的日期**没有兑现**（约 40 分钟后即恢复），
> 第二次至今未恢复。⇒ 这个字段不能当计划依据，但**也不能据此认定已恢复**：两头都要复测。
