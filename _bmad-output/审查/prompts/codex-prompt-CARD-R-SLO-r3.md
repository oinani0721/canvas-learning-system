# CARD-R-SLO 复核请求 · 第三轮 r3（BATCH-2026-09-18-第十五批 · 车道 P10 末张）

## ① 背景与最小读取面（写死，请只读这些）

本卡 = 文档/证据卡（零 `.py` 改动）。r1 结论 0B/4H/1M/1L（整改于 A2）；r2 结论 0B/1H/1M/1L（整改于 A3）。请复核 **r2 的三项整改是否到位、有无回归**。

审查绑定：r3 审 `9b2089fb`（A3，当前 HEAD）；PREV=`a03f0ce3`。树根 = 本仓 worktree。

请读（相对树根；标「真跑」的请真的执行）：
1. 本卡全量 diff（真跑）：`git --no-pager diff --no-color a03f0ce3 9b2089fb -- . ':(exclude)_bmad-output'`
2. A3 增量（真跑）：`git --no-pager diff --no-color d89aa591 9b2089fb -- . ':(exclude)_bmad-output'`
3. `docs/release-evidence/slo-manifest.yaml` 全文（重点：`cache_state`、cold `description`、`consumption_note`、`export_shape`）
4. `docs/release-evidence/README.md` 新增小节 + 「已知边界」两条新增 bullet
5. `backend/scripts/validate_release_manifest.py` :430-477、:594-644；`docs/release-evidence/manifest.schema.json` :475-530
6. `_bmad-output/审查/evidence-rslo/`（以最新一组为准）：`negctl-3-20260919T211541.txt`（配对版）、`negctl-1/2-20260919T211541`、`validate-export-e2/e3-20260919T211540.txt`、`yaml-check-20260919T211540.txt`、`rev-check-post-20260919T211540.txt`、`landgate-20260919T211549.txt`、`desens-final-20260919T211549.txt`、`unit-close3-full-*`、`unit-close3-diff-*`、`named-close3-*`；被替换的首版 `negctl-3-20260919T205702.txt` 仍并存
7. `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md` 全文（含 §9b/§9c）
8. 上下文（只读）：`../feature-obsidian-hybrid-dev/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md`（§12.5 L592 附近）、`../feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md`（:405-410）

## ② r2 三项整改的核验（逐条给「已解除 / 未解除 / 部分」）

- H-R2-1：负控 3 重做为**配对演示**（固定 `result=partial`，唯一变量 = 5 个 `not_measured` 项的 `meets`）：A 腿 false ⇒ `[S9]×5` / rc=1；B 腿 true ⇒ 0 条 `[S9]` / rc=0；且 B 腿运行前有断言 `result==partial` 不变量。请核新版存档（`negctl-3-20260919T211541.txt`）是否达到单变量归因。
- M-R2-1：`cache_state` 与 cold `description` 已改述为「19 条未由本卡 warm 环节预跑+1 条已暖；其余 19 条历史命中未证（只读约束拿不到查询历史）」。
- L-R2-1：`consumption_note` 已改述为「measurements 非空；『至少一条真实实测』是消费纪律、非机器门」。

## ③ 请按重要性重点检查（r3 焦点）

- ⓪ 三项整改是否引入新的不一致（与实测数字、与 validator 行为、与 README/UAT 互相之间）。
- ① 配对版负控 3 的 A/B 两腿除了 `meets` 外是否真的同构（同文件、同 result、同其余字段）；`A_S9_count=5 / B_S9_count=0` 是否可复算。
- ② 全套承重裁判在本轮 HEAD 的重跑结果（unit-close3 diff 仅 `<` 1 条既有 flaky；named-close3 208 passed；负控前后 shasum 同、status 0）是否成立。
- ③ 是否仍存在未披露的强主张（对比 r1/r2 已收窄的「只读/零写」措辞与新文案）。

## ④ 输出要求

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级；每条给 `文件:行`（或存档名）与最小证据；不要复述卡片摘要；无法核实的写 `UNVERIFIED` 并说明为什么。对 ② 的每一条给出整改核验结论；对 ③ 逐条作答。

## ⑤ 边界

只读复核：不要执行任何写操作、不要改动任何文件。若某文件不可读，如实标注后继续。
