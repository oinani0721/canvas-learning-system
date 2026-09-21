## 绑定与核心复算摘要

- 绑定成立：本地 `HEAD`、本地 `origin/worktree-feature-obsidian-hybrid-dev`、本地 `backup/worktree-feature-obsidian-hybrid-dev` 均为 `c11487c8b324dc16846d33d5d37eb88f979d4123`；与提示中 2026-09-20 22:16:31 活态 ls-remote 自证一致。本轮未连远端/数据库/网络服务。
- `c11487c8^..c11487c8` 恰 7 文件，全部在 `_bmad-output/**`；最终 tracked working tree 干净（`git diff` / staged / modified 均为 0）。
- r8-L1 实质闭合：`UAT-CARD-G4-13-2026-09-19.md:3-10` 与 `:996-999` 已有终态勘误指针；当前 `backend/tests/regression/gold_set_manifest.yaml:83-91` 为 103 主集、`status: approved`、`signed_by: Heishing`；我只读复跑 `gold_set_manifest_tool.py verify`，4 个 SHA 全 OK、rc=0。裁定清单复算为 103 个 gsid、103 个 checked、每个 gsid 恰 1 个 checked。
- r8-L2 实质闭合：基线 33 红 vs `unit-FINALPOSTP9` 32 红的 canonical set-diff 复算为 introduced=`[]`，removed 唯一 `tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`。`test_vault_install_manifest.py::test_digest_is_injective_over_adversarial_leaves` 只出现在 15:16 中间 33 红档，不在终局差集。
- 其他核心面复算：OpenAPI 当前 JSON 为 paths=199 / schemas=357 / operations=211（GET94、POST100、PUT6、DELETE9、PATCH2）；contract 3-file 基线/终局红 nodeid 集合一致；7692 档为 107 passed；semantic v2.4 的 10 个 pin 均 40-hex，6 个负控脚本 SHA 与“一行变异”复算一致，`--self-test` PASS；P3 lane `32a405a4..1726b695` 与 `34c29691..1726b695` 非 `_bmad-output` diff 均为空；G8-10 checker 在最终 HEAD 复跑 `chains=6 obj07=5 failures=0`，digest=`04ac414fb674c77005e51bc1359e0c4f`。
- 台账 §二为 32 张卡；列出的 squash/补关 SHA 均可解析且是 `c11487c8` 祖先。`59e1f494..c11487c8` 为 67 个 first-parent commit、0 merge。
- 未运行会启动应用/数据库/网络服务的测试；unit、pyright、7692、contract 按原始日志加“post-P9 后非 `_bmad-output` 仅 contract 注释且 AST 全等”的代码面不变性复核。

## BLOCKER

无。

## HIGH

无。

## MEDIUM

### M-1 STATUS 的现行“剩余”块仍是裁定/ff 前状态，与同文件、总账和 Git 实况冲突

- **位置**：`_bmad-output/审查/evidence-b15-closeout/STATUS.md:35-39`；对照 `_bmad-output/审查/evidence-b15-closeout/STATUS.md:32-33`、`_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md:1093-1096`、SHA `c11487c8`。
- **复现思路**：读 STATUS 现行区块可见：第 37 行仍写 “G6-13 J07 / G4-13 103 标注：无口令 ⇒ not_run + SKIP”，第 38-39 行仍写 feature 3 处删除处置与 ff-only restore 待办；但同文件第 33 行和总账第 1095 行均已写 G4-13 为 103/103 + approved 补关、J07 窗口 18:23 已开启，且 Git/reflog 显示 ff 已完成，最终树 tracked clean。
- **未被拦下的输入**：只读 STATUS 该“剩余”块的读者会把 G4-13 误判为未裁定/SKIP，把 J07 误判为未开窗，把已完成的 ff 前置误判为仍阻塞。
- **对照输入**：同文件上方 G4-13 追加合入记录、总账 §六、G4-13 manifest/UAT 指针、台账 P9 行均为 approved/已收口；Git 最终分支已越过 `f16c867a` 到 `c11487c8`。
- **负控输入**：`grep -nE 'G4-13|J07|ff-only|restore' STATUS.md` 直接同时命中新旧矛盾口径；无需跑服务。
- **门未覆盖的路径**：现有 OpenAPI/unit/contract/semantic/G8-10/G4-13 manifest 门均不校验 STATUS “剩余”块与权威台账、总账和 Git 状态的交叉一致性。

## LOW

### L-1 r8 汇报行写入 22:20，但包含该行的 commit/push 时间是 22:16，形成不可能时序

- **位置**：`_bmad-output/第十五批-完成的卡-汇报.md:20`；对照 commit `c11487c8b324dc16846d33d5d37eb88f979d4123`。
- **复现思路**：该行声称 “09-20 22:20 D-15 r8 结果”，但它由 `c11487c8` 引入；`git show -s --format=%aI/%cI c11487c8` 均为 `2026-09-20T22:16:17-07:00`，提示中的活态 push 自证为 22:16:31。包含该汇报行的提交不可能早于其声称的事件时间。
- **未被拦下的输入**：信任汇报时间列会推得“r8 结果尚未发生就已入库并推送”的时序矛盾。
- **对照输入**：r7 行为 21:56，r7 commit 为 21:53:07，时序可行；r8 行与 commit/push 时间为负控反例。
- **负控输入**：比较 `git show -s --format='%aI %cI' c11487c8` 与汇报行第一列即可复现，无需网络。
- **门未覆盖的路径**：D-15 文档门未校验“汇报事件时间 ≥ 包含该行的 commit 时间”或同机 commit/push chronology。

### L-2 r8 unit 勘误的误归因存档清单漏列 r5；r5 存档确实写了错误 digest nodeid

- **位置**：`_bmad-output/审查/evidence-b15-closeout/D-15-r8-整改说明.md:6`；对照 `_bmad-output/审查/codex-review-B15-CLOSEOUT-r5.md:73`、`_bmad-output/审查/codex-review-B15-CLOSEOUT-r6.md:54`。
- **复现思路**：r8 勘误列出误归因存档为 “r1/r2/r4/r6/r7”，但 r5 第 73 行也明确写 “unit 33→32 的 canonical nodeid 差集仅移除 digest injective 测试”；正确清单应为 r1/r2/r4/r5/r6/r7，r3 未作该具体归因。
- **未被拦下的输入**：按 r8 勘误清单逐档修读时，r5 仍会被当作无需勘误的权威复算记录，错误 nodeid 归因残留。
- **对照输入**：对基线与终局 FAILED 行做 canonical set-diff，removed 唯一为 candidate_service 422；r5 的 digest 表述与该机械差集不符。
- **负控输入**：`grep -Rsn 'digest_is_injective' codex-review-B15-CLOSEOUT-r*.md` 可同时命中 r1/r2/r4/r5/r6/r7，直接暴露漏列。
- **门未覆盖的路径**：unit 门比较红集合，不把 D-15 勘误说明中的“误归因存档清单”与全部历史存档文本再对账。

清零：否
B/H/M/L = 0/0/1/2
