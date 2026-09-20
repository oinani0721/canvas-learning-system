# CARD-R-SLO 复核请求 · 第八轮 r8（锁版轮 · BATCH-2026-09-18-第十五批 · 车道 P10 末张）

## ① 背景与最小读取面（写死，请只读这些）

本卡 = 文档/证据卡（零 `.py`）。轮次史：r1 0B/4H/1M/1L；r2 0B/1H/1M/1L；r3 0B/1H/1M/1L；r4（绑 `e4ef1ebf`）0B/0H/0M/2L；r5（绑 `7f6dfeb8`）0B/0H/2M/1L；r6（绑 `e90fc46c`）0B/0H/0M/2L；**r7（绑 `4f80542f`）0B/0H/0M/0L**。

**本轮（r8）= 锁版轮**：用户 2026-09-20 已给出「R-SLO 授权锁版」+ 9 项逐项裁定 + code_sha 裁定（采用候选值），车道已执行锁版。请复核：锁版是否**精确**执行了用户裁定、绑定证据是否扎实、是否引入任何语义/口径回归。

审查绑定：r8 审 `f27531a9`（当前 HEAD）；本卡 PREV=`a03f0ce3`；**锁版增量** = `08cf6bf7`（锁版 commit）与 `f27531a9`（锁版存档）；锁版前哨 = `d0e8b989`。

请读（相对树根；标「真跑」的请真的执行）：
1. 累计全量 diff（真跑）：`git --no-pager diff --no-color a03f0ce3 f27531a9 -- . ':(exclude)_bmad-output'`
2. **锁版增量（真跑）**：`git --no-pager diff 08cf6bf7^..08cf6bf7`（= 锁版 commit 全部；docs 面 + UAT）与 `git --no-pager diff --stat f27531a9^..f27531a9`
3. `docs/release-evidence/slo-manifest.yaml` 全文（重点：`revision/status/decision/environment.code_sha/code_sha_basis/lane_sha/adjudicator`；9×`threshold`（4×locked 值 / 5×null）；9×`degrade_rule` 新句；4×`threshold_source` 更新）
4. `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md`：顶部元数据、§12（签字位 + code_sha 已裁定行）、**§15 锁版记录**（授权原文）
5. `_bmad-output/审查/evidence-rslo/slo-lock-20260920T140356.txt`（锁版执行存档：yaml sha / cat-file / locked_ok / rev_check r2 / validator / legA-B / 地盘门 / schema 指纹 / 脱敏）
6. `_bmad-output/审查/evidence-rslo/code-sha-runtime-tree-20260920T131615.txt` + `…-erratum-20260920T133330.txt`（code_sha 依据）
7. `_bmad-output/审查/codex-review-CARD-R-SLO-r7.md`（上一轮 0/0/0/0 基线，供对照）
8. 上下文（只读）：`../feature-obsidian-hybrid-dev/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md`（§12.5 L592 附近）、`../feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md`（:405-410）

## ② 作者自述请独立核对（逐条给「成立 / 不成立 / 部分」）

- A1 **锁版精确执行用户裁定**：`revision` `slo-manifest@2026-09-19-r1`→`slo-manifest@2026-09-20-r2`；`status` `draft`→`locked`；4 项 measured 指标 `threshold.locked` = 用户照准的 candidate（首屏 ≤500ms / warm ≤5000ms / kg ≤500ms / 重建 ≤30s）；5 项无候选指标 `locked` 保持 `null`（⛔ 不填估计值）；`decision.locked_by/locked_at`、`environment.adjudicator` 填实；`measured` 数字与 draft 完全一致（未改任何实测）。
- A2 **code_sha 绑定扎实**：`environment.code_sha` = `9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680`（用户裁定采用候选值；`git cat-file -t`=commit）；原 `code_sha_null_reason`（null 条件消失）→ `code_sha_basis`（取证据实 + 收窄勘误 + 同进程连续性未证）；「重建项仅脚本 blob 等同」收窄保留。
- A3 **r1→r2 版本化**：`decision.note` 记录 r2 取代 r1（draft 正文见 git 历史 `8e36c412`）；单文件版本化下旧正文以 git 历史保留，与 README 版本化规则相符。
- A4 **配套措辞更新不引语义变化**：锁版 commit 同时把 4×`threshold_source` 的「待用户锁版」改为「2026-09-20 用户锁版照准」、9×`degrade_rule` 的「candidate 锁版前不构成发布判据」改为「锁版后：locked 阈值即发布判据（无候选、locked=null 项维护为 not_measured+owner，新 revision 起草前不计判据）」——**未改任何阈值数字/实测/统计量/导出映射**。
- A5 **门证据齐全**：锁版存档含 locked_ok / rev_check r2（E3 引用可解）/ validator --all rc=0 / legA(partial) rc=1 S9×5 / legB(fail) rc=0 S9×0 / 地盘门（仅 README+yaml；`-` 行=0；禁面=0）/ schema 指纹同 / 脱敏 0。
- A6 **README 与 schema 零改动**（累计面仍仅 README +13/0、yaml 本轮锁版；schema/校验器/J08 未动）。

## ③ 请按重要性重点检查（r8 焦点）

- ⓪ 锁版是否**精确**执行用户裁定（含：5 项 locked=null 的处理是否符合「不填估计值」纪律；`decision.note` 对 9 项的转述是否与 UAT §15 授权原文逐项一致）。
- ① `code_sha_basis` 与 `decision.note` 中关于 code_sha 的表述是否超出取证据实；`lane_sha` 更新是否正确。
- ② `degrade_rule` 新句是否与 README/S9 语义一致、是否引入新歧义（特别「locked=null 项维护为 not_measured+owner」）。
- ③ 锁版后消费语义：`export_shape` 在 locked 下导出（threshold←locked；5 项 (未定)＋not_measured）与 legA/B 结果是否自洽。
- ④ 是否仍有超证据/过期措辞残留（含 UAT 顶部、§11、§12、§15 之间）。
- ⑤ 若发现 HIGH：给最小后续补证（零 `.py`，仅文档/证据面）。

## ④ 输出要求

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级；每条给 `文件:行`（或存档名）与最小证据/复跑思路；对 ② 每条给核验结论；对 ③ 逐条作答；无法核实写 `UNVERIFIED`。不要复述卡片摘要。

## ⑤ 边界

只读复核：不要执行任何写操作、不要改动任何文件。不评阈值数值本身高低（那是用户锁版已裁的事）、不评 G4-14/G2-10/G6-11 runner 设计、不评 P10-A/P10-B 内容。若某文件不可读，如实标注后继续。
