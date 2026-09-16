> 批次: BATCH-2026-09-11-第十四批 · 车道 T10 · 卡 CARD-RED-HYGIENE round-5（**未完成，0 字节**）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `OpenAI Codex v0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-HYGIENE.md)"`
> 审查绑定: `6d337e96ba270cdb710360092e0503421f5eed31`（送审时的 HEAD）
> 结论: ⛔ **本轮没有结论。** Codex 的 stdout 落盘 **0 字节**，进程 `exit=0`，
> 原因是账户级用量配额在报告生成阶段耗尽（见下 §二）。
> ⇒ **本轮不计入 D-15 轮次配额**（等同协议 §2.1「缺字段 = 该轮不计配额」的同理情形：没有产出就不是一轮审查）。
> ⇒ 终审仍以 **r4（绑 `ef21be2c`，BLOCKER 0 / HIGH 0）+ D-32** 为准，裁定权在主 session（见 §四）。
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，逐行括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: gpt-6-astra`（第 5 行） / `reasoning effort: ultra`（第 9 行）

---

## 一、本文件为什么存在

按协议 §2.2，承重裁判的输出一律落盘。本轮**跑了**，但**没有产出**——
如果不入库，卡的轮次账上会缺一块，后人会以为「r4 之后就没再送过」。
本文件记录的是「送了、跑了、被打断、没有结论」这件事本身，**不是**一份复核报告。

⛔ **本文件不含任何 findings，也不得被当作「r5 通过」或「r5 未通过」引用。**

## 二、失败的确切形态

进程 `exit=0`（**不是**崩溃），stdout `0` 字节，stderr 250,185 字节。
stderr 末尾两行逐字为：

```
ERROR: You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Sep 19th, 2026 8:16 PM.
tokens used
80,230
```

**协议 §1 的「0 字节存档重发一次」已按如下方式执行并如实说明**：
台账记有「外部服务的『重置时间』是一次观测不是不变量」（曾出现 Codex 报「6 天后重置」、
24 分钟后即恢复的实例），所以**没有**直接继承那句 `Sep 19th` 的结论，而是做了复测。
复测用的是**同模型、同端点、`reasoning_effort=low` 的最小请求**（提示词只有「只回一行：OK」）：

```
probe_rc=1   stdout_bytes=0
stderr 末行: ERROR: You've hit your usage limit. ... try again at Sep 19th, 2026 8:16 PM.
```

⇒ 拒绝发生在**账户层**，与请求内容、长度、reasoning effort 都无关。
⚠️ **如实说明口径差异**：协议原文说的是「重发一次」（指重发那份 prompt），
本卡执行的是**等价但更省的最小请求复测**——理由是两者的失败面相同（账户级配额），
重发那份 19KB prompt 只会得到同一行错误。**这是车道的工程判断，不是协议原文，请主 session 核。**

⇒ 依协议 §1 后半句：「再 0 字节 → **主 session 人审替代，不等配额**」。

## 三、r5 在被打断前实际做了什么（如实转述，非裁定）

⚠️ 以下信息抄自**不入库**的 `.stderr`（协议：`*.stderr*` 永不入库），且全部是**中间过程**。
台账明确记过「抢救的推理标题不是裁定」——下面任何一行都**不能**被读成 Codex 的判断。

- `exec` 次数 **18**，其中含 `pytest` ×4、`pyright` ×3、`git` ×多次、`rg` ×6、`python` ×3、`comm` ×1。
  ⇒ 它确实独立跑了判据，不是只读文档。
- 可见的推理阶段标题末尾几个是：`Classifying residual findings` / `Getting full report` /
  `Running direct repro` —— 即**报告生成阶段**被截断。
- ⛔ **不得由「Deciding medium finding counts」推断「只有 MEDIUM、没有 HIGH」。**
  那是推理中途的标题，不是分级结论；它之后还有 `Classifying residual findings` 和
  `Running direct repro` 两步没走完。**r5 的 BLOCKER / HIGH 计数是未知，不是 0。**

### 3.1 一处必须点名的中间输出（防后人误读 stderr）

r5 有一次 `python` 执行打印了：

```
FINAL-R5-unit-close-20260916T204820.txt EPW 34 run 35 EPW_only 34 run_only 35
```

字面读像是「EPW 红集与本卡红集**完全不相交**」，与验收单 §四-A.10 写的「差集 0」直接冲突。
**但这是它自己的提取口径问题，不是新发现**：它对 `epw-unit-close7.nodeids` 用的是
`set(s.splitlines())`（**整行**），对 `*-unit-close-*.txt` 用的是正则提 nodeid（**去前缀**）。
两侧口径不同 ⇒ 交集必然为空，34 与 35 自然全落进 `*_only`。
同一行还打印了 `integ5_minus_EPW 65 / EPW_minus_integ5 34` ——
`65` 恰好等于 integ5 的**全部**条数，同样是两侧口径不一致的产物。

⇒ **该行不构成对验收单的反证。** 主 session 用本卡口径一致的重算见
`evidence-red-hygiene/FINAL-R5-unit-comm-CORRECTED-*.txt`（两侧统一取字段 2，
BASE 复得 64、`'<'` = 30、`'>'` = 1）。
⚠️ 有意思的是，本卡**自己也犯过同型错误**并已登记（首算 comm 时 29 条 ERROR 塌成 1 条，
见 §七.19）——同一个坑，两个独立执行者当天各踩一次。

## 四、对 D-15 终审的影响（请主 session 裁定）

本轮失败**不改变**终审状态，理由与需要复核的点一并列出：

1. **r4 已满足 D-15 的终审条件**：绑 `ef21be2c`，BLOCKER 0 / HIGH 0，
   Codex 自行实测 `git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空、`exit=0`，
   并明写「不要求继续改代码送第 5 轮」。
2. **r4 之后的改动不破坏该绑定**：只有两个 docstring 块（`0bc3baef`）+ 纯 `_bmad-output`
   （`6d337e96` 与本 commit）。按批级裁定 **D-32**「纯注释/docstring 尾巴不占轮次不重置」。
   主 session 已带验伪锚独立复算等价性：去 docstring 后 `ast.dump` 逐字相同、长度同为 43367；
   **不**去 docstring 时两侧 AST 必须不同 —— 实测确为不同，证明该判据没有空转。
3. ⚠️ **但 D-32 的原文是「主 session 逐行等价核并写明」**，而本卡的 session 是**车道**身份。
   车道只提供证据，**不自判**。r5 原本的作用正是让终审在字面上也绑最终 HEAD、
   从而不必依赖 D-32 这条例外——该加强措施**因配额失败**。
   ⇒ **「r4 + D-32 是否构成有效终审」这一裁定，明确留给主 session。**
4. **r5 请复核的三件事因此全部未被外部验证**（prompt ⓪ 段第 1/2/3 项、④ 段第 7/8/9 问）：
   r4 之后新写的 6 条 docstring 主张、两份 guard 探针的版本归属、已撤回措辞的全仓残留。
   这三件只有**主 session 自己的**补证（`FINAL-R5-docstring-claims-*.txt` 等），
   按台账「不入库的复核不作依据」的同一精神，**自证不能替代外审**——如实登记为未经外部复核。

## 五、后续

- 配额恢复后若要补送 r6：prompt 无需改动（它已绑「以 `git rev-parse HEAD` 实取为准」，
  不写死 SHA），只需重跑协议 §2 的命令并按 §2.1 写首部。
- 本卡**不等配额**（协议 §1 明文），按主 session 人审替代收尾。
