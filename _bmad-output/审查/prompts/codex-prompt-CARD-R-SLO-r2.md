# CARD-R-SLO 复核请求 · 第二轮 r2（BATCH-2026-09-18-第十五批 · 车道 P10 末张）

## ① 背景与最小读取面（写死，请只读这些）

本卡 = 文档/证据卡（零 `.py` 改动）：versioned SLO manifest + README 反向引用 + 一次现网只读实测。
r1（你上一轮）结论：**0 BLOCKER / 4 HIGH / 1 MEDIUM / 1 LOW**。本卡已按 r1 完成整改（commit A2）并重跑承重裁判，现请复核**整改是否到位、有无回归**。

审查绑定：r2 审 `d89aa591`（A2，当前 HEAD）；PREV=`a03f0ce3`。树根 = 本仓 worktree。

请读（相对树根；标「真跑」的请真的执行）：
1. 本卡全量 diff（真跑）：`git --no-pager diff --no-color a03f0ce3 d89aa591 -- . ':(exclude)_bmad-output'`（应只含 `docs/release-evidence/slo-manifest.yaml` 与 `docs/release-evidence/README.md`）
2. r1 之后的整改增量（真跑）：`git --no-pager diff --no-color 8e36c412 d89aa591 -- . ':(exclude)_bmad-output'`
3. `docs/release-evidence/slo-manifest.yaml` 全文（重点：`cache_state`、cold `description`、warm/cold/first-paint/kg `method.command` 的 `-m`、写侧四项 `method sketch` 注记、`export_shape.mapping` 三态与纪律、`consumption_note`）
4. `docs/release-evidence/README.md`：新增小节 + 「已知边界」两条新增 bullet（R-SLO 锁版无机器门 / SLO 导出纪律没有全量机器门）
5. `docs/release-evidence/manifest.schema.json` :475-530；`backend/scripts/validate_release_manifest.py` :76-77、:359-477、:594-644
6. `backend/tests/unit/test_validate_release_manifest.py` :110-130 与 :655-675（revision 字面形态的既有用例；r1 曾标 UNVERIFIED 的 ②#5 读取面）
7. `_bmad-output/审查/evidence-rslo/` 关键存档（以最新一组为准）：`negctl-1/2/3-20260919T2057*.txt`、`validate-export-e2/e3-20260919T205634.txt`、`yaml-check-20260919T205634.txt`、`rev-check-post-20260919T205634.txt`、`landgate-20260919T205712.txt`、`desens-final-20260919T205713.txt`、`unit-close2-*`、`named-close2-*`；另 r1 期存档保留在 `…T204126/T202340/T202346…`
8. `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md` 全文（含 §9b 整改记录表）
9. 上下文（只读）：`../feature-obsidian-hybrid-dev/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md`（§12.5 L592 附近）、`../feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md`（:405-410）

## ② r1 四项 HIGH + 1 MEDIUM + 1 LOW 的整改核验（逐条给「已解除 / 未解除 / 部分」）

- H1：cold 口径已改述为「20 条互异串各一次，实为 19 条首见+1 条已暖」；warm/cold 命令补 `-m 120`（首屏 `-m 60`、kg `-m 30`）。
- H2：README 新段与验收单已把「只读」收窄为「发起命令面 + 已核对锚点」；service 层副作用与缺全量前后 SHA 已列入未证明。
- H3：新增负控段 3（未被拦下的输入：`not_measured+meets=true` 不被 S9 拦，rc=0 落档）；yaml `export_shape` 补两条纪律说明；README「已知边界」新增对应 bullet。
- H4：`export_shape.mapping` 的 threshold 行补「两者皆 null ⇒ `(未定)`」；README 导出 bullet 同步。
- M1：写侧四项 command 均补 `method sketch：实参/实例由 owner 卡在其环境补全` 注记。
- L1：新一轮负控存档内已直接输出还原后 `git status --porcelain -- docs/release-evidence`（0 行）。

## ③ 请按重要性重点检查（r2 焦点）

- ⓪ 整改是否引入**新失实**：三态 `(未定)`、`method sketch` 注记、口径改述与原实测数字之间是否仍有不一致。
- ① 是否仍有「自洽但不实」：本轮核对 r1 未覆盖面——`seed` 字段（20 条构成）、`data_sha` 值、`statistics` 口径与存档数值的逐项一致。
- ② 导出纪律两条（`not_measured ⇒ false`；9 项覆盖）现在是否在 yaml 与 README 同口径，负控 3 的「未被拦下」是否被如实表达（而不是被说成机器门）。
- ③ r1 未决的 ②#5（revision 形态 vs 测试既有用例）本轮读取面已含测试文件，请核。

## ④ 输出要求

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级；每条给 `文件:行`（或存档名）与最小证据；不要复述卡片摘要；无法核实的写 `UNVERIFIED` 并说明为什么。对 ② 的每一条给出整改核验结论；对 ③ 逐条作答。

## ⑤ 边界

只读复核：不要执行任何写操作、不要改动任何文件。若某文件不可读，如实标注后继续。
