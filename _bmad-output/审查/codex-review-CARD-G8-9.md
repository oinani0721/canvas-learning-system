结论：**FAIL。CARD-G8-9 当前不可结卡。**

审查基线：`card/s7-dogfood @ 37387a86`。13/13 行在自定义三态下确实“非空”，但这不等于验收门可机械判定。

## BLOCKER

1. **把“证据/owner/缺口”误作验收结果三态，无法判断 PASS/FAIL/NOT-YET。**

   [底账 L6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:6)及[L41–55](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:41)只定义 `evidence/owner/gap`；13 个 YAML row 全无具体 `criteria` 和 `pass/fail/not-yet`。这与[总账 L395–397](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:395)直接冲突。

   实际反例：多 vault 行被记为 `evidence`，但其引用的真实入口测试仍有两条 strict xfail，明确复现 Concept/LEARNED 跨 vault 写身份覆盖：[test_cypher_contract_gate.py L312](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/backend/tests/integration/test_cypher_contract_gate.py:312)、[L344](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/backend/tests/integration/test_cypher_contract_gate.py:344)。

   修复建议：每个原子判据使用 `outcome: pass|fail|not_yet`，另设 `evidence_coverage: none|partial|complete`、`evidence_refs`、`owner_ids`、`as_of`。缺 outcome 或存在未闭合反例时 fail-closed。

2. **卡片定义要求的独立 YAML、renderer 和状态页未交付，却未把卡明确标为未完成。**

   [底账 L5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:5)及[L64](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:64)承认两项未交付；[总账 L393–397](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:393)却将其列为卡本体和完成判据。文件搜索也只找到该 Markdown 与审查文档。

   [任务书 L104–108](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/batch5-runbook.md:104)的“纯文档”边界没有明文豁免总账 Done。

   修复建议：文首和 §5 明标 `CARD-G8-9 = PARTIAL / NOT COMPLETE` 并保持卡开放；或者取得用户明确的总账改判。独立 YAML、renderer、generated status page 到位前不得结卡。

## HIGH

1. **owner 引用含幽灵 ID、状态别名和不可机械展开的范围。**

   - [底账 L19/L43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:19)：`G7 切片` / `G7-slice`；直接 owner 应为[总账 G7-7 L792](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:792)。
   - [底账 L24/L48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:24)：`G6-12`，但 `rg '^#### G6-12 '` 在总账零命中，仅[裁定 L971](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:971)提到它。
   - [底账 L48–52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:48)：`G8-6-window-pending`、`R-SLO-thresholds`、`G6-1..G6-13`、`G7-1..G7-13` 均非正式卡 ID。

   修复建议：owner 数组只允许总账正式 ID并逐项展开；状态放 `note`。G6-12 在补齐完整卡定义前应标显式缺口。

2. **把未执行状态或愿景草案列为正证据。**

   - [底账 L23](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:23)称 A3 的 12 档 launchd“已部署”；同 SHA 验收单却明确写未执行 `launchctl`、仍运行旧 9:05 单档并等待用户授权：[A3 UAT L66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/验收单/Story-CARD-A3-当天重学卡刷新.md:66)、[L73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/验收单/Story-CARD-A3-当天重学卡刷新.md:73)、[L95–104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/验收单/Story-CARD-A3-当天重学卡刷新.md:95)。
   - [底账 L24/L48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:24)把 G8-6 协议草案列作“14 天无救火”证据；协议本体仍为 `DRAFT`，尚待锁版、启动并实际完成 14 日：[G8-6 L6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:6)、[L13–15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:13)。

   修复建议：A3 改为“仓库实现完成，机器部署未证实”；部署证据须含授权、时间、安装件 hash、`launchctl print` 和运行日志。G8-6 草案仅记 owner/readiness，完整 14 日台账才是结果证据。

3. **CI 证据可跨 SHA 拼绿。**

   [底账 L29/L53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:29)聚合了不同 SHA 的绿灯：

   - `e8e8d034`：[Test Suite 成功](https://github.com/oinani0721/canvas-learning-system/actions/runs/33072968431)，但同 SHA 的 [README Claims 失败](https://github.com/oinani0721/canvas-learning-system/actions/runs/33072968526)。
   - `37387a86`：[README Claims 成功](https://github.com/oinani0721/canvas-learning-system/actions/runs/33118620673)，但没有 Test Suite run。

   因而没有一个候选 SHA 被证明“CI 全绿”。[底账 L11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:11)的人读纪律没有转化成机器约束。

   修复建议：治理行增加唯一 `candidate_sha`；全部 required workflow 必须在该 SHA 上 `triggered + success`，否则为 `FAIL/NOT-YET`。异 SHA 绿灯只能作历史 provenance。

4. **§8 原文被泛化，机械验收范围变弱。**

   - 多 vault：[底账 L20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:20)用“五存储面”替代[计划书 L436](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:436)的五个显式面。
   - 每日 UI：[底账 L24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:24)删去[计划书 L440](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:440)的“卡片与推荐白板”对象。
   - Graphiti：[底账 L26](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:26)删去[计划书 L442](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:442)中 replayable 必须由 rebuild matrix 标记的来源。
   - Skills：[底账 L27](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:27)删去[计划书 L443](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:443)的四类 skill 范围。

   修复建议：`source_criterion` 逐字保留计划书原文；解释或后续裁定放独立字段并附 `supersedes` 行号，不能覆盖原判据。

## MEDIUM

1. **C6 被错挂到 RAG“跨 vault 0”证据。**

   [底账 L25/L49](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:25)引用 `e6f83efd`；实际测试只覆盖 Memory 写侧 resolver，并明示未修写路径、lossy ID 碰撞及单 active-vault 边界：[测试 L19–41](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/backend/tests/unit/test_memory_service_contextvar_leak.py:19)。它不是 RAG 检索真实入口隔离证据；真正 owner 是[总账 G4-4 L506–510](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:506)。

   修复建议：C6 仅保留为“多 vault 写侧局部证据”；RAG 跨 vault 子判据标 `not-yet`，待 G4-4 行为门回填。

2. **数据安全行的 `raw 不自动移动` 实际无精确 owner。**

   [底账 L19/L43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:19)列出的 owner 主要覆盖删除、回滚和视觉写入；直接承接 raw 原地保留的是[总账 G2-7 L452–456](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:452)、[G2-12 L825–829](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:825)及[R-J02 L890–894](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:890)。

   修复建议：把数据安全拆为三个原子 criterion；为 `raw-not-moved` 挂上述 owner，并标 `not-yet`。

3. **“第三批 D 卡已 Codex 清零”措辞夸大。**

   [底账 L12](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:12)没有限定清零级别；实际只是 BLOCKER/HIGH 清零：

   - [D3 审查 L116–143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/_bmad-output/审查/codex-review-CARD-D3.md:116)仍有两项 MEDIUM/待授权。
   - [D4 审查 L6–24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/_bmad-output/审查/codex-review-CARD-D4.md:6)仍有两项 MEDIUM。
   - [D2b 二轮 L1–25](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/_bmad-output/审查/codex-review-CARD-D2b-round2.md:1)仍有两项 MEDIUM。

   修复建议：改为“BLOCKER/HIGH 清零；MEDIUM/LOW/授权项见审查；未合并且不构成过门”。

## LOW

无。

## 核验通过项

- 计划书 12 维均有对应行，另有 observability 预留；13/13 行在当前自定义三态下非空。
- 用户点名路径全部存在；24 个 commit 引用及 8 个箭头范围真实；三枚未合并 SHA 的分支标注正确。
- `test_split_preview.py` 为 34 个测试；README Claims `collect-only` 为 120 项。
- 15 文件 CI 白名单声明真实；两个正向 CI run 的 run ID/SHA/日期/结论分别真实。
- benchmark manifest 未越过 R-SLO 唯一 owner 边界：[底账 L7/L66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:7)与[总账 L405–409](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:405)一致。
- observability 预留范围符合[总账 G8-10 L556–560](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:556)。

全程只读，未修改文件；未访问私人 vault。`graphiti-canvas` 本轮不可用。


