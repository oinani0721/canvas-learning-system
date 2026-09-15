# 复核请求 r2 — CARD-G2-9-F1-canary（复审 r1 整改是否到位）

你是独立复核者。只读，不写，不执行任何连接数据库的命令。

## 一 本轮任务

r1 你给出 **BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 2**，结论 `PARTIAL`。作者**全部接受、零驳回**，已完成整改并提交。本轮请判断：

1. **每一条整改是否真的到位**（不是换个说法继续维持原主张）；
2. **是否还有残留的过强表述**（r1 之外的新发现也请提出）；
3. **整改过程本身有没有引入新问题**（例如收窄一处却在另一处仍按旧结论推理、编号错乱、自相矛盾）。

## 二 最小读取面（写死）

- 验收单：`_bmad-output/验收单/UAT-CARD-G2-9-F1-canary-20260915.md`（整改后版本）
- r1 存档：`_bmad-output/审查/codex-review-CARD-G2-9-F1-canary-r1.md`
- 新增/补跑的 evidence：
  - `_bmad-output/审查/evidence-g29f1-canary/negctl-forbidden-path-rerun-mkdir-check-*.txt`
  - `_bmad-output/审查/evidence-g29f1-canary/negctl-preflight-no-connect-evidence-*.txt`
- 脚本：`backend/scripts/g29_dual_vault_canary.py` 的 `_amain` / `_run_canary_cli` / `probe_schema_drift_side_effect` / `_preflight_neo4j_uri` / `_preflight_lancedb_path`
- 绑定：`git diff --stat 60600433 HEAD -- . ':(exclude)_bmad-output'`（作者主张仍为空）

## 三 r1 七条 ↔ 作者整改，请逐条判定「到位 / 未到位 / 换汤不换药」

| # | r1 问题 | 作者整改 |
|---|---|---|
| 1 (HIGH) | probe 判 FAIL → 退出码未实跑验证，却写「移交项落地」 | 结论改为「**部分落地**」：(i) 关探针不 KeyError 已实证；(ii) FAIL→`EXIT_ISOLATION_FAILED` **未实证**。新增「本卡未证明什么」第 2 条（含三条路径都进不了 FAIL 分支的说明 + 零生产改动下无法构造的理由），台账条目 1 同步收窄，标明需另立卡收口 |
| 2 (MED) | 「负控零 socket」证据不足 | 收窄为「未进入 canary runtime 主流程」；补代码结构依据（`assert_test_uri_not_blocked` 体内建连相关调用命中 0，验伪锚为该文件全文命中 69）并**明确标注这不是运行时网络证据**；新增未证明第 4 条 |
| 3 (MED) | 用 `ATTEMPTS=0` 支持「共享 7692 无并发干扰」 | 该依据已从未证明第 11 条**删除**，并写明账本只盯 7687/7691 |
| 4 (MED) | 「加载速率 ⇒ 零网络」外推 | 撤回该结论（表格该行标为已撤回）；证据只保留「4 次加载各自完成到 100%」；新增未证明第 5 条 |
| 5 (MED) | `purge_left_nothing` 被扩大成「跑后无残留」 | 表格该行含义改写；加注说明它在验伪报告里是**起点前提**（变异 `M11_purge_leaves_residue`）；新增未证明第 12 条 |
| 6 (LOW) | 所称 `test -e` 实测没落在证据里 | **补跑并完整落档**（PRE / canary rc / POST / 父目录 `ls` / 验伪锚），并在验收单如实写明「初稿引用了一条不在证据里的检查」 |
| 7 (LOW) | (i) 行、`PENDING`、「工作树 diff 空」已非当前事实 | (i) 行改为实际状态；`PENDING` 清零；两处加时点标注（= commit `49db0305` 之前的快照） |

## 四 请特别检查的点

0. 第 1 条（HIGH）的整改：「部分落地」这个措辞是否**足够**？验收单其他地方（标题、🎯 段、🚦 验收结果表、Codex 复核记录段）有没有**残留**「移交项已完成」语义的表述？
1. 第 2 条：作者补的代码结构依据本身**是否被恰当限定**？「函数体内 grep 不到建连关键字」能支撑到什么程度？作者有没有把它又悄悄当成运行时证据用？
2. 第 4/5 条：撤回是否彻底？验收单里还有没有别处仍按「零网络」「跑后无残留」推理？
3. 新增的未证明第 4/5/12 条，措辞是否又走到另一个极端（把能证的也说成不能证）？
4. 整改后验收单的**内部一致性**：条目编号（未证明 1–12、实测更正 ①–⑦）有无重复或跳号；表格与正文有无互相矛盾。
5. 是否还有 r1 没提、本轮新发现的过强表述或证据缺口。

## 五 边界

- 只读；不执行任何连接数据库的命令；不需要复跑 canary。
- 不评 `_check_and_fix_dimension_mismatch` 的删表条件设计本身。
- 若某条你无法从给定读取面证实，请直接说「证据不足」，不要推测。
- 按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条写清依据的文件与行。若整改全部到位且无新发现，请明确给出「BLOCKER 0 / HIGH 0」的结论。
