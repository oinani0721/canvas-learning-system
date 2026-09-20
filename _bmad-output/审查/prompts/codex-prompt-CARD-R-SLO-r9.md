# CARD-R-SLO 复核请求 · 第九轮 r9（锁版整改复核 · BATCH-2026-09-18-第十五批 · 车道 P10 末张）

## ① 背景与最小读取面（写死，请只读这些）

本卡 = 文档/证据卡（零 `.py`）。轮次史：r1 0B/4H/1M/1L；r2 0B/1H/1M/1L；r3 0B/1H/1M/1L；r4（绑 `e4ef1ebf`）0B/0H/0M/2L；r5（绑 `7f6dfeb8`）0B/0H/2M/1L；r6（绑 `e90fc46c`）0B/0H/0M/2L；r7（绑 `4f80542f`）0B/0H/0M/0L；**r8（锁版轮，绑 `f27531a9`）0B/2H/1M/3L**。

本轮（r9）复核 = **r8 的 2H/1M/3L 六项整改**是否闭环且无回归。锁版对象（`slo-manifest.yaml`）在 r8 后**未再改动**（作者自述，请真跑核对）。

审查绑定：r9 审 `90b8db84`（当前 HEAD）；锁版 commit = `08cf6bf7`；锁版前哨 = `d0e8b989`；**r8 整改增量** = `f27531a9..90b8db84`。

请读（相对树根；标「真跑」的请真的执行）：
1. r8 整改增量（真跑）：`git --no-pager diff --no-color f27531a9..90b8db84`（含 `_bmad-output`）与 `git --no-pager diff --no-color --stat f27531a9..90b8db84`
2. **yaml 是否仍与锁版 commit 一致（真跑）**：`git --no-pager diff 08cf6bf7..90b8db84 -- docs/release-evidence/slo-manifest.yaml`（应为空）；`git --no-pager diff --numstat a03f0ce3..90b8db84 -- docs/release-evidence`（应仍 README +13/0、yaml +269/0，README 本 commit 有 +1 行编辑，累计仍 0 删除）
3. `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md`：**§15 全文（:315 起）**、顶部元数据（:6/:8）、§0（:14）、§10（:234 起，条目 1/4/12）、§11（:250 起，条目 1/2/7）、§14 头（:294 起）
4. `docs/release-evidence/README.md:197`（版本化单文件例外句）
5. `_bmad-output/审查/evidence-rslo/slo-lock-20260920T140356-erratum-degrade-rule-20260920T141118.txt`；`slo-lock-legs-inputs-20260920T141118.txt` + `slo-lock-legA/B-input-20260920T141118.json`（sha 复算）
6. `_bmad-output/审查/codex-review-CARD-R-SLO-r8.md`（原文对照）
7. `_bmad-output/审查/evidence-rslo/slo-lock-20260920T140356.txt`（锁版执行存档）

## ② 作者自述请独立核对（逐条给「成立 / 不成立 / 部分」）

- A1 **HIGH-1 处置**：§15 已真实落档（含“首版脚本写错变量”说明、用户授权原文逐字、①-⑨ 逐项对照、code_sha 裁定、yaml 变更、腿结果、r8 整改清单）；§12/§8/存档的所有 §15 指针现可解。
- A2 **HIGH-2 处置**：§0/§10 条目 1/4/12/§11 条目 1/2/7/§14 头 的过期陈述已改为锁版后事实或 as-of 标注；不再存在「未授权/draft/E3 不可达」的活动矛盾。
- A3 **MEDIUM-1 处置**：新增 degrade_rule 口径勘误档（不改 locked 文案，按 r8 建议）；正确读法=「locked=null 项无阈值比较依据，但 not_measured+meets=false 仍走 S9 fail/waiver 链，不得静默 pass」。
- A4 **LOW-1 处置**：README `:197` 版本化 bullet 增补单文件例外句（旧正文以 git 历史保留、superseded_by 语义由 revision 链+decision.note+git 历史承载）；README 累计仍纯新增（0 删除）。
- A5 **LOW-2 处置**：UAT 顶部计数补至锁版存档 commit（`08cf6bf7`/`f27531a9` + 本 commit），不再少计。
- A6 **LOW-3 处置**：r2 消费腿 legA/legB 输入 JSON 落档 + sha256（可字节复现）。
- A7 **无回归**：yaml 锁定对象与 `08cf6bf7` 逐字一致（r8 后未改）；locked_ok/rev_check/validator 结论不变；README 纯新增约束保持。

## ③ 请按重要性重点检查（r9 焦点）

- ⓪ r8 六项是否**全部闭环**、是否引入新矛盾/新歧义（特别是 §15 与 yaml `decision.note`、§12、顶部的一致性）。
- ① §15 的授权原文/逐项对照是否与用户裁定、yaml 9 项 locked/null 逐条相符。
- ② README 例外句是否消解 LOW-1 且未引入与「版本化」的其他冲突。
- ③ 勘误档是否足以消除 MEDIUM-1 的字面歧义（yaml 文案未改，是否会被继续读错）。
- ④ 若仍发现 HIGH：给最小后续补证（零 `.py`，仅文档/证据面）。

## ④ 输出要求

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级；每条给 `文件:行`（或存档名）与最小证据/复跑思路；对 ② 每条给核验结论；对 ③ 逐条作答；无法核实写 `UNVERIFIED`。不要复述卡片摘要。

## ⑤ 边界

只读复核：不要执行任何写操作、不要改动任何文件。不评阈值数值本身高低、不评 runner 设计、不评 P10-A/P10-B 内容。若某文件不可读，如实标注后继续。
