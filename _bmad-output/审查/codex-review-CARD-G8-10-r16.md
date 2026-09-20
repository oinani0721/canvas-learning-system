BLOCKER: 无 / HIGH: 无

**轮次结论：不满足 `B/H/M/L = 0/0/0/0`。我核算为 `B0 / H0 / M2 / L6`，因此本轮不能宣告「复核第十五批 P6」，合并门继续锁定。**

## 只读核对结果

- HEAD / 父提交核对成功：`HEAD = 884af91a66163f63ad6be5a137a28b3b2c63d5e6`，父 = `150ff22b3bcdfc3639fcb3571c76e5d1578452d8`，未 amend。
- r16 develop commit 的 14 个变更路径全部在 `_bmad-output/**`；`git diff 4120e0b6 HEAD -- . ':(exclude)_bmad-output'` 为空。
- 底账 HEAD SHA 独立核对为 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`，与 4120e0b6 相比无 diff。
- 审计器当前 SHA / blob 核对为 `ae8ae103…` / `c9c590e0…`；UAT blob 为 `3f4157aa…`；生成器 SHA 为 `5b3be0b0…`。
- C1–C8 transcript 8/8 `rc=1 assert=yes`，目标标签均命中，`verdict_bad=0`。
- N1–N10 transcript 10/10 `rc=1 assert=yes`，N9 命中 `model-line-count`、N10 命中 `verdict-missing`；T `rc=0` 且 `partial=true`；P1 `rc=0`。
- 逐 REF 审计件与 §九.68 表一致：早期 REF 因 `missing_list` 必然红；`b93812ea = 71/4/67/0`、`0aa87523 = 74/6/68/0` 均无缺口；旧 REF 的 `blob_in_ref=absent` 形态正常。
- HEAD 审计件内部计数自洽：80 names、6 excluded、74 OK、0 MISS，且 `blob_used == blob_in_ref`。
- JEV stdout / JSON / sidecar 三者互相一致：`calls=1`、唯一代码文件为 `g810-r8-sidecar.py`、`+19/-8`、urgency `2.41`、P(review) `0.61`、risk `logic`、verdict `REVIEW`。
- 但当前 HEAD 中，`g810-green-r11-20260920T155050.txt`、`artifact-audit-r12-20260920T155050-89409.txt`、JEV JSON/stdout、sidecar 均为 untracked；这本身符合“收尾 commit 前状态”，但不能被称作已入库。

## BLOCKER

无。

## HIGH

无。

## MEDIUM

1. `_bmad-output/审查/prompts/codex-prompt-CARD-G8-10-r16.md:16` 与 `_bmad-output/审查/prompts/codex-prompt-CARD-G8-10-r16.md:25` — r16 prompt 把 post-commit green 件 `g810-green-r11-20260920T155050.txt` 列在「已入库证据」下，并声称唯一非入库项是 HEAD 审计件，但该 green 件在 `884af91a` 树内不存在。  
   **对照输入**：`git cat-file -e HEAD:_bmad-output/审查/evidence-g810/g810-green-r11-20260920T155050.txt` 返回 128，`git status` 显示该文件为 `??`；这是 r15-M1 同类复发。

2. `_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:114-120` — verdict 所谓“数据行”只约束列形与最终判定词白名单，risk 列是任意 `(\w+)`，且第一个形状兼容行可在 stdout 任意位置被接受，不与 JSON 的 file/churn/risk/数值或后续数据行核对。  
   **未被拦下的输入**：在 otherwise-complete JEV stdout 中放 `fake-row +0/-0 0.1 0.2 0.3 0 PASS` 并删除真实数据行，生成器会写 `verdict="PASS"`、`field_missing=[]` 并 rc=0，而不是 `verdict-missing`。

## LOW

1. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:79-82` — 锚只检查 marker 前最后一个编号项的数字是 28，不要求 28 编号唯一，因此后插入的伪 `28.` 可把名字面起点后移。  
   **未被拦下的输入**：在真实 28 项后放 `ghost.txt`，再插入一行 `28. filler`，然后才是 29 项；`_prev_items[-1]` 取伪 28，早期 `ghost.txt` 不进审计面。

2. `_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:103-111` — 「行首空白」实现只认 ASCII space/tab，不是所有行首空白变体。  
   **未被拦下的输入**：保留一条 clean `Model:` 行，再加一条以 NBSP 或 form-feed 缩进的第二 `Model:` 行；计数仍为 1，解析取 clean 行，隐藏行不触发 `model-line-count`。

3. `_bmad-output/审查/evidence-g810/g810-r12-artifact-audit.zsh:38-43` — `blob_in_ref` 只验证 40-hex 字符串，不验证该 OID 真是 blob object。  
   **门未覆盖的路径**：让 REF 树中 runner 路径变成目录/tree 或 submodule，`git rev-parse REF:path` 返回 40-hex tree/commit OID 后仍被写成 `runner_blob_in_ref`。

4. `_bmad-output/审查/evidence-g810/g810-r15-audit-ctl.zsh:2-4` — r16 扩容后的审计控制件标题仍称「审计 v2.6.1 控制组」，而其 C8 与 transcript 实际运行的是 v2.6.2 runner。  
   **对照输入**：读 `_bmad-output/审查/evidence-g810/audit-ctl-r15-20260920T154941-88101.txt:1` 与同件 C4–C8 内嵌的 `runner_sha256=ae8ae103…` / `blob_used=c9c590e0…`，可见控制件标签与实际 runner 版本不一致。

5. `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:416` — UAT 称 P1 为「真实 r15」，但控制件与 transcript 实际使用 `jev-triage-b93812ea.json`、`--round r14`。  
   **对照输入**：读 `_bmad-output/审查/evidence-g810/g810-r15-sidecar-negctl.zsh:88` 与 `_bmad-output/审查/evidence-g810/sidecar-negctl-r15-20260920T154931-87835.txt:37-38`，二者均标为真实 r14。

6. `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:583` — §十一.59 把旧值 `v4.9(docfixed)@0aa87523 = 2291e430…` 称为 r16 digest 链，而当前 r16 green 件已经给出 `@884af91a = 768c1ff36352b77438898fa35897b318`，且该 green 件仍未入库。  
   **对照输入**：读 `_bmad-output/审查/evidence-g810/g810-green-r11-20260920T155050.txt:9-13`，再对 `884af91a` 树查该文件存在性；PENDING-R16 收尾前，该台账不能作为最终 digest 闭合。

## r15 六项闭合判定

| r15 项 | 本轮判定 | 结论 |
|---|---|---|
| M-1 文书「未入库称入库」 | **PARTIAL** | r15 那件确已入库，但 r16 prompt 对 green 155050 复发同类错误。 |
| M-2 Model/标记行缩进计数 | **PARTIAL** | ASCII space/tab 目标修复且 N9 红；Unicode/非 ASCII 行首空白仍逃逸。 |
| M-3 verdict 表头 fallback | **PARTIAL** | 表头-only 已由 N10 证明红；伪造形状兼容“数据行”仍可恒绿。 |
| L-1 28/29 间隙进面 | **PARTIAL** | 原始间隙攻击已修复且 C8 红；重复 28 编号仍可截断名字面。 |
| L-2 `blob_in_ref` 单一 absent | **基本修复，有 LOW 残余** | REF 缺 runner 时不再混入错误回显；但 40-hex tree/submodule OID 会误标为 blob。 |
| L-3 版本标签统一 | **PARTIAL** | 审计器本体统一 v2.6.2；审计控制件 / transcript 仍回显 v2.6.1。 |

## 声明边界判定

- 我判定为**可接受、无需本轮扩面**的既有边界：basename-only 不证路径归属 / 内容哈希（§十.46、53）、排除名单理由需人工复核（§十.49、51）、PARTIAL 只记录上游自述（§十.57）、未来新 verdict 词 fail-closed（§十.59）、同一行内重复 `Model:` 不计数（§十.60）、未合并 / 未跑集成门 / 未验证现网（§十.61）。
- 仍需计为问题的边界错位：verdict risk 列与数据行相关性未声明也未实现、Unicode 行首空白超出 `[ \t]` 实现口径、重复 28 未被 §十.56 的“伪造整段结构”边界准确覆盖、`blob_in_ref` 未验证 object type。

## 收口判定

- 技术主链没有 BLOCKER/HIGH，且 commit 范围、底账、 hashes、控制件、逐 REF 审计、HEAD 审计、JEV/sidecar 内容基本互证。
- 但 `MEDIUM = 2`、`LOW = 6`，所以 **`0/0/0/0` 不满足**。
- PENDING-R16 仍是合法状态：green、HEAD audit、JEV、sidecar、r16 review、UAT 回填与最终 SHA 必须随收尾 commit 入库并重新绑定；在那之前不得释放合并门。
