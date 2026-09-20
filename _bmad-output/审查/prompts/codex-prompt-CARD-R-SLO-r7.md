# CARD-R-SLO 复核请求 · 第七轮 r7（BATCH-2026-09-18-第十五批 · 车道 P10 末张 · 锁版前置整改收口）

## ① 背景与最小读取面（写死，请只读这些）

本卡 = 文档/证据卡（零 `.py`）。轮次史：r1 0B/4H/1M/1L；r2 0B/1H/1M/1L；r3 0B/1H/1M/1L；r4（绑 `e4ef1ebf`）0B/0H/0M/2L；r5（绑 `7f6dfeb8`）0B/0H/2M/1L；**r6（绑 `e90fc46c`）0B/0H/0M/2L**。本轮（r7）复核 = **r6 两项 LOW 整改**是否到位且无回归。**尚未锁版**（`status: draft` 维持，用户口令未至）。

审查绑定：r7 审 `4f80542f`（当前 HEAD）；本卡 PREV=`a03f0ce3`；r6 整改增量 = `e90fc46c..4f80542f`。树根 = 本仓 worktree。

请读（相对树根；标「真跑」的请真的执行）：
1. 累计全量 diff（真跑）：`git --no-pager diff --no-color a03f0ce3 e90fc46c -- . ':(exclude)_bmad-output'`；并 `git --no-pager diff --numstat a03f0ce3 e90fc46c -- docs/release-evidence`
2. r6 整改增量（真跑）：`git --no-pager diff --no-color e90fc46c 4f80542f`（含 `_bmad-output`）
3. 新增勘误档全文：`_bmad-output/审查/evidence-rslo/code-sha-runtime-tree-erratum-20260920T133330.txt`；对照原取证档 `_bmad-output/审查/evidence-rslo/code-sha-runtime-tree-20260920T131615.txt`（**未改**，证据不可变）
4. UAT 本轮改动点：`_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md`（顶部元数据 :6-7、§11.14 :267、§12 ⚠️ 行 :277、§14 :308 附近）
5. `_bmad-output/审查/codex-review-CARD-R-SLO-r6.md`（r6 原文对照）；`docs/release-evidence/slo-manifest.yaml` 全文（应仍未动：`code_sha: null`、9×`threshold.locked=null`、`status: draft`、`revision` 仍 r1）；`docs/release-evidence/README.md` 新增小节 + 「已知边界」三条新增 bullet
6. 复算抽检（真跑）：`git rev-parse 7f6dfeb8:backend 9c4e7e82:backend`；`git rev-parse 7f6dfeb8:scripts/daily_review_pick.py 9c4e7e82:scripts/daily_review_pick.py`；`git --no-pager diff --name-status 9c4e7e82 7f6dfeb8 -- backend`
7. 上下文（只读）：`../feature-obsidian-hybrid-dev/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md`（§12.5 L592 附近）、`../feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal台账-v2.md`（:405-410）

## ② 作者自述请独立核对（逐条给「成立 / 不成立 / 部分」）

- A1 **r6 L1 处置**：「窗口内 8011 连续可用」已在 3 处收窄为「各次探测均 200/健康；未做连续 uptime 监控；同进程连续性未证」（勘误档 a)/d) + UAT §11.14 + §12）。
- A2 **r6 L2 处置**：UAT 顶部元数据补全为「A/B 5 + 补审归档 1（`b0ac7192`） + 锁版前置 6 + r5 整改 1 + r6 整改 1」；Codex 轮次行补至 r5/r6（并一句 ZCode 通道）。
- A3 **无回归**：r6 整改增量仅 UAT + 勘误档（+ r6 存档/prompt），README/yaml/schema/校验器/J08 零改动；draft 面未动（9×`locked=null`、`status=draft`、`revision=r1`、`code_sha=null`）。
- A4 **勘误档其余内容未引入新主张**；原取证档自引入以来未改（证据不可变）。

## ③ 请按重要性重点检查（r7 焦点）

- ⓪ r6 两项 LOW 是否**全部闭环**、是否引入新矛盾/新歧义。
- ① UAT 顶部元数据是否与 git 事实逐项一致（commit 列表/计数、Codex 轮次、ZCode 一句、HEAD 兜底句）。
- ② 是否仍有任何超证据表述残留（特别：连续 uptime、tracked 口径、候选语义、ignored 面披露）。
- ③ 若仍发现 HIGH：给**最小后续补证**（零 `.py`，仅文档/证据面）。

## ④ 输出要求

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级；每条给 `文件:行`（或存档名）与最小证据/复跑思路；对 ② 每一条给核验结论；对 ③ 逐条作答；无法核实的写 `UNVERIFIED` 并说明为什么。不要复述卡片摘要。

## ⑤ 边界

只读复核：不要执行任何写操作、不要改动任何文件。不评阈值数值本身高低（归用户锁版）、不评 G4-14/G2-10/G6-11 的 runner 设计、不评 P10-A/P10-B 内容。若某文件不可读，如实标注后继续。
