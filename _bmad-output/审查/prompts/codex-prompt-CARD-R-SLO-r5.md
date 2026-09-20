# CARD-R-SLO 复核请求 · 第五轮 r5（BATCH-2026-09-18-第十五批 · 车道 P10 末张 · 锁版前置）

## ① 背景与最小读取面（写死，请只读这些）

本卡 = 文档/证据卡（零 `.py` 改动）。轮次史：r1 0B/4H/1M/1L（整改 A2）；r2 0B/1H/1M/1L（整改 A3）；r3 0B/1H/1M/1L（整改 A4）；**r4 0B/0H/0M/2L**（`codex-review-CARD-R-SLO-r4.md`）。另有 ZCode/GLM-5.3 通道 **0B/0H/0M/3L**（`_bmad-output/审查/zcode-review-CARD-R-SLO-rc.md`）。

本轮（r5）复核对象 = **锁版前置六连 commit** 的 5×LOW 处置（`090dc4b5` → `67d0555c` → `29d578e5` → `9ed914e5` → `f01dc9a3` → `7f6dfeb8`），并确认累计面无回归。**尚未锁版**（用户口令未至，`status: draft` 维持）。

审查绑定：r5 审 `7f6dfeb8`（当前 HEAD）；本卡 PREV=`a03f0ce3`；锁版前置增量区间 = `b0ac7192..7f6dfeb8`。树根 = 本仓 worktree。

请读（相对树根；标「真跑」的请真的执行）：
1. 本卡全量 diff（真跑）：`git --no-pager diff --no-color a03f0ce3 7f6dfeb8 -- . ':(exclude)_bmad-output'`；并 `git --no-pager diff --numstat a03f0ce3 7f6dfeb8 -- docs/release-evidence`
2. 锁版前置增量（真跑）：`git --no-pager diff --no-color b0ac7192 7f6dfeb8 -- . ':(exclude)_bmad-output'` 与 `git --no-pager diff --no-color --stat b0ac7192 7f6dfeb8`
3. `docs/release-evidence/slo-manifest.yaml` 全文；`docs/release-evidence/README.md` 新增小节 + 「已知边界」**三条**新增 bullet（含 r5 前新增的「不做数值比较 vs S9 数值交叉核对并存」条）
4. `backend/scripts/validate_release_manifest.py` :430-477（S9 数值交叉核对行为）；`docs/release-evidence/manifest.schema.json` :475-530
5. `_bmad-output/审查/evidence-rslo/`：**新增档** `measure-stats-summary-v2-20260920T131200.txt`、`slo-prep-20260920T131200.txt`、`code-sha-runtime-tree-20260920T131615.txt`、`jev-triage-f01dc9a3.docs-prelock.json`（已入库，机制实证档）；以及原始档 `measure-review_overview_first_paint-20260919T171124.txt` / `measure-rag_warm-20260919T171144.txt` / `measure-rag_cold-20260919T171226.txt` / `measure-kg_read-20260919T171134.txt` / `measure-review_rebuild-20260919T171556.txt`（供独立重算）；对照档 `measure-stats-summary-20260919T171634.txt`（v1）
6. `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md` 全文（重点 §10 第 12 条、§11 第 9–15 条、§12、§14）
7. 上下文（只读）：`../feature-obsidian-hybrid-dev/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md`（§12.5 L592 附近）、`../feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal台账-v2.md`（:405-410）；如需可再读 `codex-review-CARD-R-SLO-r4.md` 与 `zcode-review-CARD-R-SLO-rc.md` 以核对 LOW 原文

## ② 作者自述请独立核对（逐条给「成立 / 不成立 / 部分」）

- A1 **5×LOW 处置闭环且不越界**：r4 L1 在「本卡新增 bullet」内就地改（`可复跑命令`→`method sketch（owner 补实例/实参后复跑）`）；ZCode L1 以「新增 bullet」澄清（既有行 `:268` 未改）；r4 L2/ZCode L2 以 §5/§7 落地时机（commit B `c2b1fac3`）+ §5 (f)② 终版计数 + §6 A4 evidence index 处置；ZCode L3 以 v2 汇总处置。README 仍纯新增（累计 `-` 行=0）；yaml/schema/校验器/J08 零改动。
- A2 **v2 汇总忠实**：从同一批原始样本重算（不剔除样本）；cold 描述统计仅对 19 条 200 样本、全样本 max=120.0037 单列；5 个 `raw_sha256` 与原始档逐字一致；v1 数字与 v2 吻合。
- A3 **code_sha 取证实证可复核**：8011 = FE 树 `backend/` 的 live bind（docker inspect 输出如实）；FE 树 `67d66672..HEAD` **0 个 commit 触达 `backend`/`src`；`tree(HEAD:backend)==tree(9c4e7e82:backend)==a5cd759a…`；唯一 backend 脏文件 = 测试 fixture（mtime 2026-08-19，早于窗口、非运行时面）；候选 = `9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680`（`git cat-file -t`=commit）。yaml 仍 `code_sha: null`（**未擅自绑定**，等主 session 公布/用户裁定）。
- A4 **JEV 机制实证**：`jev_review_triage.py` 默认 pathspec（代码扩展名）对零代码卡必空；docs-pathspec 跑法产出非空（`code_files/files/usage` 非空）；口径裁定归主 session（UAT §11.15 已登记）。
- A5 **draft 面未被触动**：9×`threshold.locked=null`、`locked_by/at=null`、`status: draft`、`revision` 仍 `r1`。
- A6 **无新增敏感面**：新增 README bullet/UAT/证据档无绝对路径、无 key 值、无 `NEO4J_PASSWORD=`。

## ③ 请按重要性重点检查（r5 焦点）

- ⓪ v2 汇总与原始档/v1 是否逐一吻合（请**独立重算** 4 项 http 指标 + rebuild；并核对 cold 口径声明的强度）。
- ① code_sha 取证链条：是否存在比候选更强的反例，或候选表述超出证据——(a) 0-commit 区间是否真的覆盖 2026-09-19 17:11–17:16 PDT 窗口；(b) 唯一脏文件（测试 fixture）是否真与运行时行为无关；(c) 容器/端口在窗口内的连续性是否如 §11.14 所述（批级 docker-ps 存档 + 窗口内 200 探针）；(d) 「窗口内所服务代码 = 9c4e7e82」的措辞是否应收窄（例如仅绑定到"tracked backend 内容 + 非运行时脏文件"口径）。
- ② 5×LOW 处置是否闭环，是否留下新歧义/新悬空（特别是 README 新增第三条 bullet 与既有句的关系；UAT §14 与 §5/§6/§7/§11 是否自洽）。
- ③ UAT §11.14/§11.15/§12/§14 的每一条事实是否与实测一致（如 (f)②「行 3 / 出现 5」计数口径）。
- ④ 若仍发现 HIGH：给**最小后续补证**（零 `.py`，只允许文档/证据面动作）。

## ④ 输出要求

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级；每条给 `文件:行`（或存档名）与最小证据/复跑思路；对 ② 每一条给核验结论；对 ③ 逐条作答；无法核实的写 `UNVERIFIED` 并说明为什么。不要复述卡片摘要。

## ⑤ 边界

只读复核：不要执行任何写操作、不要改动任何文件。不评阈值数值本身高低（那归用户锁版）、不评 G4-14/G2-10/G6-11 的 runner 设计、不评 P10-A/P10-B 内容。若某文件不可读，如实标注后继续。
