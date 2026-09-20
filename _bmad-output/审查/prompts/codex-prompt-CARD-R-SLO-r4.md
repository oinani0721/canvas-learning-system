# CARD-R-SLO 复核请求 · 第四轮 r4（BATCH-2026-09-18-第十五批 · 车道 P10 末张）

## ① 背景与最小读取面（写死，请只读这些）

本卡 = 文档/证据卡（零 `.py` 改动）。r1 0B/4H/1M/1L（整改 A2）；r2 0B/1H/1M/1L（整改 A3）；r3 0B/1H/1M/1L（整改 A4）。请复核 **r3 三项整改是否到位、有无回归**，并给出本轮最终 B/H/M/L。

审查绑定：r4 审 `e4ef1ebf`（A4，当前 HEAD）；PREV=`a03f0ce3`。树根 = 本仓 worktree。

请读（相对树根；标「真跑」的请真的执行）：
1. 本卡全量 diff（真跑）：`git --no-pager diff --no-color a03f0ce3 e4ef1ebf -- . ':(exclude)_bmad-output'`
2. A4 增量（真跑）：`git --no-pager diff --no-color 9b2089fb e4ef1ebf -- . ':(exclude)_bmad-output'`
3. `docs/release-evidence/slo-manifest.yaml` 全文；`docs/release-evidence/README.md` 新增小节 + 「已知边界」两条新增 bullet（含既有句澄清尾段）
4. `backend/scripts/validate_release_manifest.py` :430-477；`docs/release-evidence/manifest.schema.json` :475-530
5. `_bmad-output/审查/evidence-rslo/`（A4 权威组）：`negctl-3-20260919T213522.txt` + `negctl-3-inputs-A/B-20260919T213522.json`、`negctl-1/2-20260919T213522`、`yaml-check/rev-check-post/validate-export-e2/e3-20260919T213532.txt`、`landgate-20260919T213532.txt`、`desens-final-20260919T213533.txt`、`unit-close4-full-20260919T213539.txt` + `unit-close4-diff-20260919T214207.txt`（修正版；`214133` 版为提取失误的空表对照，作废）、`named-close4-20260919T214207.txt`；历史组（211541/205702 等）仅作对照
6. `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md` 全文（含 §9b/§9c/§9d）
7. 上下文（只读）：`../feature-obsidian-hybrid-dev/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md`（§12.5 L592 附近）、`../feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md`（:405-410）

## ② r3 三项整改的核验（逐条给「已解除 / 未解除 / 部分」）

- H-R3-1：负控 3 已补输入侧证据——生成器 pre-assert 输出、A/B 两份 manifest 落档（`negctl-3-inputs-A/B-*.json`）、双份 sha256、归一化逐字段 diff（应恰好 5 处 `slo.measurements[i].meets` false→true）、两腿 validator 输出与计数（A：`[S9]×5`/rc=1；B：0 条/rc=0）、生成器全文附录。
- M-R3-1：UAT 指针已改指 A3/A4 权威组（首版 `negctl-3-20260919T205702` 明标仅历史对照）。
- L-R3-1：README 既有行不可改（本卡「纯新增」硬约束）；已在新增 bullet 内加澄清尾段 + §10/§11 登记。

## ③ 请按重要性重点检查（r4 焦点）

- ⓪ 负控 3 v3 的输入侧证据是否足以完成单变量归因（A/B 除 5 处 `meets` 外逐字同构；`result=partial` 不变量有 pre-assert；input sha 可复算）。
- ① A4 增量（README 澄清句 / UAT 指针与登记）是否引入新矛盾或新强主张。
- ② 是否仍存任何未披露的强主张、或与前两轮已收窄口径的互相冲突。
- ③ 若仍发现 HIGH：请给出**最小后续补证**（本卡零 `.py`，只允许文档/证据面动作）。

## ④ 输出要求

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级；每条给 `文件:行`（或存档名）与最小证据；不要复述卡片摘要；无法核实的写 `UNVERIFIED` 并说明为什么。对 ② 的每一条给出整改核验结论；对 ③ 逐条作答。

## ⑤ 边界

只读复核：不要执行任何写操作、不要改动任何文件。若某文件不可读，如实标注后继续。
