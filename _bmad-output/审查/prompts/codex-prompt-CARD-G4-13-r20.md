# CARD-G4-13 r20 终轮复核任务书（Codex × GLM-5.3 · 目的：绑最终 HEAD 的 B/H/M/L=0 判定）

> 批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`；车道 `card-p9-testinfra`；复核对象 = **最终 HEAD `64f109bb`**
> （父 `4a24d948`，本 commit = 用户裁定回写 + 签字）。只读复核，**不改任何文件**。

## ① 背景与最小读取面

goal：真人 gold set 用户裁定。用户已在勾选清单上逐条裁定（103 条），本 commit 完成回写 + 升版 + 签字。
请独立核验**终态**是否满足 goal 的全部完成条件，并给出 B/H/M/L 判定。

最小读取面（只读这些）：
- `backend/tests/regression/gold_set_manifest.yaml` 全文（revision=3 / frozen / verdict_counts / revision_history / adjudication）
- `git --no-pager diff --no-color 4a24d948 64f109bb -- backend/tests/regression/vault_gold_set.yaml backend/tests/regression/memory_gold_set.yaml`（裁决回写 diff）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19-裁定清单.md`（用户勾选清单；每条 `<!-- gsid:… -->` + 恰一个 `- [x]`）
- `backend/scripts/gold_set_manifest_tool.py` 的 `apply_verdicts` / `_apply_verdict_edits` / `build_manifest`（bump 段）/ `approve_manifest`
- 证据：`_bmad-output/审查/evidence-g413/r25-*`（尤其 `r25-freeze-all-103-*.txt`、`r25-build-approve-verify-*.txt`、`r25-gate-stateagnostic-*.txt`、`r25-regression-after-verdicts-*.txt`）

## ② 作者自述（逐条独立核对）

1. 回写 103/103（vault 75 / memory 28）：relevant 64 / ambiguous 39 / irrelevant 0；**每条恰 3 行变化**
   （vault 225 行、memory 84 行；shadow 两文件 0 行）。
2. **内容冻结**：全量 103 条中除 `user_verdict`/`verdict_by`/`verdict_at` 外，逐键逐值与前版一致；
   既有 83 条对 `9c4e7e82` 的 10 键 diffs=0；12 个判分函数 AST same=True。
3. manifest：revision 2→3；`verdict_counts` 与勾选一致；`adjudication: approved` + `signed_by: Heishing` +
   `signed_at` + `checklist_path`；升版把旧签名留痕在 `revision_history[].prev_adjudication`（若曾有）。
4. `verify` rc=0；g413 行为门 90 passed（6 个测试改状态无关化后仍判别）；点名套件 47 passed；
   `tests/regression` 目录级 2003 passed / 6 skipped / 1 xfailed 红 0。
5. 未经 AI 代填：全部 verdict 来自用户勾选清单（sha d73430f2…，已同步进本车道）。

## ③ 问题（逐条回答；答不了就答「无可读证据」）

⓪ **裁决完整性**：103 条的 `user_verdict` 是否与清单逐条一致？有没有任何一条的写入超出
   `user_verdict/verdict_by/verdict_at` 三字段（即内容被动过）？shadow 两文件是否确未被本次回写触碰？
① **冻结完整性**：`verify` 的三态语义与 manifest 链（revision 1→2→3、prev_adjudication 留痕）是否自洽？
   还能否构造「verify rc=0 但内容被悄悄改」的输入（针对本次回写路径）？
② **签字语义**：`approved` + 签名 + `checklist_path` 是否足以支撑「用户签字」？有没有哪条路径能在
   主集还有 pending 时签出 approved（含 build 升版后重签的路径）？
③ **门的判别力**：6 个状态无关化后的测试是否仍真判别（不是把断言放宽成恒真）？「每条恰 3 行」的
   证据与断言是否覆盖 103 条全量而不只是样本？
④ **总判定**：列出任何 BLOCKER/HIGH/MEDIUM/LOW（含 file:line 与一句话复现）；并明确回答：
   goal 的完成条件（103/103 非 pending、approved+签字、内容冻结、点名套件绿）是否全部达成。

## ④ 输出格式

逐条 **BLOCKER / HIGH / MEDIUM / LOW**（无则写「未发现」）+ `file:line` + 一句话复现思路；
一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」；末尾「本轮总评：B= / H= / M= / L=」。

## ⑤ 边界

只读；⛔ 不改任何文件；不连 7691/7687/8011；不跑两 runner 非 shadow 模式；不评 G4-14 七指标 / R-SLO schema。
