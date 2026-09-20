# CARD-R-SLO 复核请求 · 第六轮 r6（BATCH-2026-09-18-第十五批 · 车道 P10 末张 · 锁版前置整改）

## ① 背景与最小读取面（写死，请只读这些）

本卡 = 文档/证据卡（零 `.py`）。轮次史：r1 0B/4H/1M/1L；r2 0B/1H/1M/1L；r3 0B/1H/1M/1L；r4（绑 `e4ef1ebf`）0B/0H/0M/2L；**r5（绑 `7f6dfeb8`）0B/0H/2M/1L**。本轮（r6）复核 = **r5 三项（2M+1L）整改**是否到位且无回归。**尚未锁版**（`status: draft` 维持，用户口令未至）。

审查绑定：r6 审 `e90fc46c`（当前 HEAD）；本卡 PREV=`a03f0ce3`；r5 整改增量 = `7f6dfeb8..e90fc46c`。树根 = 本仓 worktree。

请读（相对树根；标「真跑」的请真的执行）：
1. 累计全量 diff（真跑）：`git --no-pager diff --no-color a03f0ce3 e90fc46c -- . ':(exclude)_bmad-output'`；并 `git --no-pager diff --numstat a03f0ce3 e90fc46c -- docs/release-evidence`
2. r5 整改增量（真跑）：`git --no-pager diff --no-color 7f6dfeb8 e90fc46c`（含 `_bmad-output`）
3. 新增勘误档全文：`_bmad-output/审查/evidence-rslo/code-sha-runtime-tree-erratum-20260920T133330.txt`；对照原取证档 `_bmad-output/审查/evidence-rslo/code-sha-runtime-tree-20260920T131615.txt`（**未改**，证据不可变）
4. UAT 本轮改动点：`_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md`（顶部元数据 :6、§7 脱敏补充 :172、§11.14 :267、§12 ⚠️ 行、§14 :306 附近）
5. `_bmad-output/审查/codex-review-CARD-R-SLO-r5.md`（r5 原文对照）；`docs/release-evidence/slo-manifest.yaml` 全文（应仍未动：`code_sha: null`、9×`threshold.locked=null`、`status: draft`、`revision` 仍 r1）；`docs/release-evidence/README.md` 新增小节 + 「已知边界」三条新增 bullet
6. 复算抽检（真跑）：`git rev-parse 7f6dfeb8:backend 9c4e7e82:backend`；`git rev-parse 7f6dfeb8:scripts/daily_review_pick.py 9c4e7e82:scripts/daily_review_pick.py`；`git --no-pager diff --name-status 9c4e7e82 7f6dfeb8 -- backend`
7. 上下文（只读）：`../feature-obsidian-hybrid-dev/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md`（§12.5 L592 附近）、`../feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal台账-v2.md`（:405-410）

## ② 作者自述请独立核对（逐条给「成立 / 不成立 / 部分」）

- A1 **r5 M1 处置**：新增勘误档收窄四条（容器连续性未证 / **tracked** 脏文件口径 + ignored 面披露 / 重建项仅脚本 blob / 候选语义收窄）；**未重写原档**；UAT §11.14 与 §12 ⚠️ 行同步收窄。
- A2 **r5 M2 处置**：redacted 表示（`<FE-worktree>/…`、`<repo-root>`）作为消费面；§7 登记「原始档保留绝对路径、消费面以勘误档为准」；README/yaml 零改动、两文件 `/Users/` 命中仍 0。
- A3 **r5 L1 处置**：UAT 顶部元数据更新（A/B 5 commit + 锁版前置 6 + 当前 HEAD 以 `git rev-parse` 为准）；yaml `code_sha_null_reason` 保持测量期 draft 措辞、锁版 commit 按裁定改写（已登记）。
- A4 **无回归**：README 累计纯新增（`-` 行=0）；`yaml/schema/校验器/J08` 零改动（累计 `a03f0ce3..e90fc46c` 内 `docs/release-evidence` 仅 README+yaml 且均为新增）；9×`locked=null`、`status=draft`、`revision=r1` 未动。
- A5 **勘误档自身无新强主张**：每条收窄事实可复算（tree/blob 值、diff 名单、0-commit 区间）；ignored 面 mtime（`llm_call_logs.db` 窗口内 17:15 变动）只读记录、与 UAT §10 第 5 条既有披露一致。

## ③ 请按重要性重点检查（r6 焦点）

- ⓪ r5 三项是否**全部闭环**、是否引入新矛盾/新歧义（尤其 §11.14 收窄后的措辞是否仍超证据；勘误档与原档的消费面关系是否清晰）。
- ① 收窄后的候选语义（「tracked backend 树 == `9c4e7e82:backend`；窗口内连续可用但同进程未证；重建项仅脚本 blob 等同」）是否仍超出可复核证据，或存在更强反例。
- ② 脱敏补充是否充分（消费面定义、原档用途声明）；是否还有其他新增面仍含宿主路径。
- ③ UAT 顶部/§7/§11/§12/§14 是否自洽（含 §14 的 r5 记录与 §6 (f)② 计数口径）。
- ④ 若仍发现 HIGH：给**最小后续补证**（零 `.py`，仅文档/证据面）。

## ④ 输出要求

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级；每条给 `文件:行`（或存档名）与最小证据/复跑思路；对 ② 每一条给核验结论；对 ③ 逐条作答；无法核实的写 `UNVERIFIED` 并说明为什么。不要复述卡片摘要。

## ⑤ 边界

只读复核：不要执行任何写操作、不要改动任何文件。不评阈值数值本身高低（归用户锁版）、不评 G4-14/G2-10/G6-11 的 runner 设计、不评 P10-A/P10-B 内容。若某文件不可读，如实标注后继续。
