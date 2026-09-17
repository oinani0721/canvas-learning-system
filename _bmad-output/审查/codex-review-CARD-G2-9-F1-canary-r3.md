> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t1-lance · 卡 CARD-G2-9-F1-canary round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `OpenAI Codex v0.153.3`（`codex --version` 实测 `codex-cli 0.153.3`）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-9-F1-canary-r3.md)"`
> 审查绑定: `77e798c2`（送审时 HEAD）。**冻结态**：本轮起跑前工作树已干净（除 T1-A 的 4 个未跟踪残留），运行期间作者未改动任何被审文件——这是为修正 r2 的冻结违例（偏差 B-2）而专设的一轮。
> 会话头自证（按实际行号抄 `.stderr` 中含 codex 版本 / model / reasoning effort 的三行；本轮 L2/L5/L9，与 r2 的 L4/L7/L11 不同——行号逐轮变化，必须按实际行号抄；`.stderr` 本身不入库）:
> `OpenAI Codex v0.153.3`（L2） / `model: gpt-6-astra`（L5） / `reasoning effort: ultra`（L9）

---

## r3 结论：PARTIAL

**绑定 HEAD：`77e798c2413088233c7abe5bac75c519e02e41c1`**  
**BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 4。**

首尾采样中，审查范围内 **64 个文件**的哈希均未变化，且全部与 HEAD 中的内容一致。指定命令：

```sh
git diff --stat 60600433 HEAD -- . ':(exclude)_bmad-output'
```

输出为空、rc=0。当前已跟踪文件相对 HEAD 的 diff 也为空。

验收单为 **579 行**，SHA256：

```text
7289425c4a80edb8e5d399f70d8daf869c619341dda819855a7ca67146420205
```

全程只读，未连接数据库、未复跑 canary 或测试。未读取已有的未跟踪 r3 报告。

下文 **UAT** 指[本轮验收单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/_bmad-output/验收单/UAT-CARD-G2-9-F1-canary-20260915.md)。

## 一、分级发现

### M1 · MEDIUM：两处有效副本仍写“无法构造 FAIL”

**依据：UAT:506、542；对照 UAT:481、563。**

- 正文 481 行已正确收窄为“未提供允许范围内的 FAIL 夹具，也没有 FAIL 的实跑证据”。
- **506 行台账**仍写“零生产改动下无法构造 FAIL”。
- **542 行 r1 整改表**仍写“零生产改动下无法构造”。
- 563 行却声明本轮已经完成该项更正。

因此 **r2 #3 未完全到位**。两处副本仍将“本次未覆盖”扩大为“不可能构造”。

**不恢复原 HIGH**：FAIL→退出码未实证、移交项仅部分落地，已经明确披露。

### M2 · MEDIUM：残留对账的验伪能力证据不足，且摘要误数

**依据：UAT:128、497、564；[残留 evidence:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/_bmad-output/审查/evidence-g29f1-canary/residue-recon-7692-20260915T230907.txt:8)–22。**

该 evidence 保存了节点／关系各 0 行、全库 114 节点、84 个带 `group_id` 的统计，但**没有保存查询正文、参数或执行命令**。无法独立核对：

- 两条前缀是否正确传入；
- 节点和关系分别覆盖什么；
- 所谓“同形查询”是否确实使用同一匹配逻辑。

**全库查询非空，不能证明目标前缀查询不是恒空或条件写错。** UAT 的“证明该查询不是恒空”仍过强。可确认存档报告了这些结果；其覆盖面与验伪能力仍属**证据不足**。

另一个直接矛盾：evidence **17 行实际列出 14 个互异 `group_id`**，UAT 三处却写成 **13**。此误数合并计入本项。

**边界检查：** UAT:498 明确区分了“跑后图侧按该前缀”与“共享容器完全无残留”；(c) 段 129 行结合前句阅读，也保留了该限制。因此不另判一次“共享容器无残留”的外推。但其加粗结论宜同样保留“按该前缀”。

本项**不表示发现了实际残留或越界操作**。

### L1 · LOW：静态证据摘要仍把关键词搜索写成函数调用清点

**依据：UAT:543；对照 UAT:214、486；[静态 evidence:49](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/_bmad-output/审查/evidence-g29f1-canary/negctl-preflight-no-connect-evidence-20260915T230117.txt:49)–57。**

543 行仍写：

> `assert_test_uri_not_blocked` 体内建连调用命中 0

实际证据是**截断片段中的关键词搜索结果**，不能表述为完整函数体的建连调用清点。

正文三重局限登记充分，“未穷举全进程建连点”也恰当；残留在整改摘要中。因此 **r2 #1 为 PARTIAL，残留降为 LOW**。

### L2 · LOW：B-2 的核对证据引用不准确，有利推断应进一步限定

**依据：UAT:363、370、569；[偏差 evidence:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/_bmad-output/审查/evidence-g29f1-canary/deviation-r2-target-mutated-20260915T230646.txt:21)–28；[r2 存档:14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/_bmad-output/审查/codex-review-CARD-G2-9-F1-canary-r2.md:14)–15。**

- UAT:370 称偏差 evidence 包含“工作树 diff 与绑定核对”；实际只有 **diff 统计及代码面空 diff 的 rc**，没有保存 535 行／SHA256 核对记录。
- r2 声明绑定的是**最后读取版本**。事后哈希一致可以支持“最终绑定到修正后的完整版本”，不能进一步排除审查早期曾读取其他版本。

B-2 已明确承认冻结违例，并未撤销偏差；但“没有读到中间态”应限定到**最终绑定版本**。不据此推测作者动机或宣布 r2 内容结论全部无效。

### L3 · LOW：“当前状态”仍停留在旧工作树时点

**依据：UAT:234、272、569。**

- 234、272 行仍称当前验收单存在相对 HEAD 的修改；本轮实测该 diff 为空。
- 569 行仍称“当前文件行数与 SHA256 与 r2 声明完全一致”；当前实际为 **579 行／`7289425c…`**，已非 r2 的 535 行／`062a8145…`。

应明确这些都是**当时的核对结果**。这是 r1 #7 的状态陈述残留，不影响生产文件 diff 为空的结论。

### L4 · LOW：实测更正⑤的“bash 同理”错误

**依据：UAT:429。**

该行说 zsh 默认不对变量展开结果继续做 glob，并括注“bash 同理”。本轮以 `/bin/bash --noprofile --norc` 对现存 evidence 路径做只读验证，未引用变量中的 `*` 被正常展开为实际文件名。

因此，**bash 默认行为并不同理**；应删除该括注。

## 二、r2 五项逐条判定

| # | 判定 | 说明 |
|---|---|---|
| 1 | **PARTIAL** | 有效的“唯一建连”主张及台账旧论证已撤回，三重局限充分；543 行摘要仍有 L1。 |
| 2 | **PASS** | UAT:75、387、392、487、512 已统一为四次加载完成及本次环境下的执行选择。 |
| 3 | **PARTIAL** | 正文及条件更正正确；506、542 行仍有 M1。 |
| 4 | **PARTIAL** | UAT:124、127 已收窄身份主张；新增旁证仍有 M2。 |
| 5 | **PASS** | UAT:395 已正确指向第 9 条，内容位于 491–492 行。 |

`verdict`／`finding` 的更正与[脚本:1283](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/scripts/g29_dual_vault_canary.py:1283)–1286 一致：FAIL 要求 B 表不在 `after`；`CONFIRMED` finding 还要求此前存在。

[AST evidence:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/_bmad-output/审查/evidence-g29f1-canary/ast-rc-guard-structure-20260915T230932.txt:2)–7 的自我限定恰当，结构与脚本 1451–1457 行一致。**未发现其他位置将其当成 FAIL 分支实跑证明。**

## 三、r1 七项及编号复核

按验收单归整的七项编号：

| # | 判定 | 两轮后的状态 |
|---|---|---|
| 1 FAIL→退出码／全部完成 | **PARTIAL** | 未实证已披露，HIGH 不恢复；仍有 M1。 |
| 2 负控零 socket | **PARTIAL** | 主结论到位；摘要仍有 L1。 |
| 3 端口账本支持 7692 无干扰 | **PASS** | UAT:494–495 明确删除该依据。 |
| 4 加载速度→零网络 | **PASS** | 正文与台账已同步收窄。 |
| 5 purge→最终无残留 | **PASS，限原整改** | UAT:118、122、496 已收窄；新增旁证问题见 M2。 |
| 6 缺失 `test -e` evidence | **PASS** | 补跑记录完整，UAT:219–221 正确区分 canary rc=2 与包装组 rc=0。 |
| 7 完成状态／快照 | **PARTIAL** | 章节及占位问题已修，当前状态仍有 L3。 |

**编号结构 PASS：**

- 未证明 **1–12**：UAT:475–498，连续无重复。
- 台账 **1–9**：UAT:504–528，连续无重复。
- 实测更正 **①–⑦**：UAT:376–453；台账副本 512–518 的主题逐项对应。

编号本身没有问题；内容尚有上述副本矛盾和“bash 同理”错误。

**B-1 核心登记到位**：承认工作树非空并保留主 session 裁定。四个 T1-A 路径见 `prereq-20260915T120845.txt:12–15`；其内容、尺寸和产生者在给定读取面内证据不足。同份 status 的 11 行还包含本卡 evidence 目录，不能将整份输出概括为恰好四项。

**最终判断：当前 HEAD 的 BLOCKER/HIGH 均为 0；整改尚未全部到位，维持 PARTIAL。**


