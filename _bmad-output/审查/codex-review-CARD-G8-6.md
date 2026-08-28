结论：**FAIL，不可锁版、不可开窗。**

当前状态应标为：

- 协议文档：`DRAFT，可继续修订`
- CARD-G8-6：`PARTIAL / 未满足总账完成判据`
- 14 天窗口：`NOT START-READY`
- 审查基线：`card/s7-dogfood @ 37387a8662e9dd646fad5628841679d777cb7eae`
- 目标协议当前仍是未跟踪文件，HEAD 尚未绑定其 exact bytes

## BLOCKER

1. **三零违规可被“已闭合”洗掉。**

   [完成判定 L14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:14)只拒绝“违规确认且未闭合”，而[事件字段 L49](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:49)把“违规确认/已闭合”放在同一互斥字段。D2 确认数据丢失、D3 修复后改成“已闭合”，即可满足 L14，却违反[不可洗白规则 L51](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:51)。[L52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:52)还明确允许静默假成功闭合后通过，与[计划书 L348](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:348)的“0 静默假成功”冲突。

   修复：拆成不可变的 `violation_status` 与独立 `closure_status`；完成式显式要求三类 `confirmed_count == 0`。若真实政策只是“零未闭合”，必须改名并由用户重新裁定。

2. **14 天连续核对既可事后回填，也会误判正常/失败日。**

   - [L61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:61)称无到期日只做步骤 1、2，跳过[L62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:62)打卡，随后又被[L66①](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:66)判漏日。
   - 当天只有 `generate:FAILED` 时，“无 generate 行”为假，也能绕过 L66②。
   - Markdown 台账没有 `recorded_at` 或不可覆盖回执，D15 一次性补勾 14 行无法被识别。
   - [L68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:68)要求次日中午前核对“昨日 payload”，但 runner 每天覆盖同一个文件：[daily_review_run.py L135-L158](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/daily_review_run.py:135)，而 09:05 已开始次日调度：[plist L23](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/launchd/com.canvas.daily-review.plist:23)。

   修复：落 append-only 每日回执，记录本地日、实际写入时间、正常/补核/超时状态；日通过式改为正向 AND；按 vault+日期归档不可变 payload。脚本落地前禁止启动。

3. **C6 无法证明 ingest→board，最低活动量可被无关文件拼出。**

   [C6 L92](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:92)要求 `node_derived + recap`，但示例命令既不读取事件文件，也没有实际 mtime 过滤或两者关联键。生产 `node_derived` 的 `payload` 为空：[node-derivation.ts L251-L265](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/frontend/obsidian-plugin/src/node-derivation.ts:251)，无法与报告机械 join；该计数却承担[≥5 门槛 L117](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:117)。

   修复：新增稳定完成回执，至少含 `run_id/source_id/report_path/artifact_sha/completed_at`；否则将 C6 标为不可用并阻止开窗。

4. **C8 证明的是“runner 跑过多个 vault”，不是“发生两次 vault 激活切换”。**

   [C8 L94](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:94)把历史日志中两个不同 key 当作切换；实际 wrapper 会依据 `DAILY_REVIEW_VAULTS` 自动循环多个库，无需改变 `ACTIVE_VAULT`：[wrapper L30-L36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/launchd/daily-review-wrapper.sh:30)。`sort -u` 还删除了顺序，无法计算转换次数。合法 key 可含大写和点：[send_bark.py L46-L66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/send_bark.py:46)，而协议正则会把 `vault=Canvas.Vault` 截成 `vault=`。

   修复：先锁定指标是“使用两个 vault”还是“激活转换两次”；后者必须记录有序 `from/to/time/source` 切换回执。

5. **总账必需交付未完成，§8 却声称不阻塞启动。**

   [总账 L379-L383](</private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:379>)要求协议、台账脚本、过去三天补齐和自动标红；[owner 裁定 L969](</private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:969>)还要求计数器和 dogfood 结案报告归档 R-EVD。[协议 L133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:133)同时说“启动前补齐”和“无脚本不阻塞启动”；结案报告也没有路径、模板、字段或完成门。S7 的[纯文档边界 L104-L108](</private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/batch5-runbook.md:104>)解释本批为何不写代码，但不构成对总账的豁免。

   修复：明确标记“文档子交付完成、CARD PARTIAL”；删除“不阻塞启动”；登记具名残余 owner、脚本路径和验收门；补齐 R-EVD 结案报告合同。

## HIGH

1. **“完成一张板”被降格成“一条答题事件”。**

   [L61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:61)及[C4 L90](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:90)用一条 `answer_scored` 代表完成一板；源码实际每次回答即追加一条事件：[quiz-answer L324-L340](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/canvas-vault/.claude/skills/quiz-answer/SKILL.md:324)，白名单没有 `board_completed`：[learning_event_log.py L35-L47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/backend/app/services/learning_event_log.py:35)。

   修复：增加板完成事件/明确完成条件；或经用户批准把 L613 门改名为“至少完成一题”，不能名实不一。

2. **C1/C2/C3/C9 被标“可用”，示例命令却不能给机械结论。**

   [L87-L95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:87)中的命令存在未定义 cwd/VAULT/key、只打印不比较、未限定 active vault、正常 `fallback:-` 也命中等问题。从当前 worktree 直接执行 C1 命令得到 `exit 2: backups/daily-review.log: No such file or directory`；实际日志由绝对 `REPO/backups` 产生：[runner L31-L38、L95-L100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/daily_review_run.py:31)。

   修复：启动档案冻结 `DEV_REPO/RUNTIME_REPO/VAULT/VAULT_KEY/DAY`，由单一脚本结构化输出每项 PASS/FAIL 和退出码。

3. **fix-forward 的变更源不等于实际运行变更。**

   [L34-L36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:34)仅看 dev 主线日期范围内的 commit；它看不到 `.env`、dirty 文件、已安装 wrapper 副本或旧日期 commit 的 fast-forward 合并，也不能证明 commit 已部署。wrapper 明确读取 `.env` 且 git 副本修改后需重新安装：[wrapper L3-L5、L26-L35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/launchd/daily-review-wrapper.sh:3)。

   修复：每日记录 runtime exact SHA、dirty 状态、非敏感配置 digest、已安装入口 checksum、部署时间和前后 runtime SHA 差分；无 harness 的影响面保持 OPEN/UNVERIFIABLE。

4. **新能力可在 D14 自动纳入并冒充已覆盖 14 天。**

   [L27](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:27)规定“合并即自动纳入”，与[L37](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:37)由用户决定延长/另开，以及[总账 L381](</private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:381>)“后续能力延长或另开”冲突。[C7 L118](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:118)的类数还会自动变化，违反[L129](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:129)锁版。

   修复：启动时冻结能力 manifest；bug fix 可 fix-forward，新能力不得自动获得既往暴露天数，须由用户裁定延长或新开窗口。

5. **“所有 degraded 可见且可恢复”未进入完成门。**

   [计划书 L348](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:348)要求全部 degraded 可见且可恢复；协议完成式、事件类别及[C9 L95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:95)均无恢复证据门。总览源码也只有 `ok/stale/no_projection/corrupt`：[review_overview.py L66-L72](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/backend/app/api/v1/endpoints/review_overview.py:66)。

   修复：增加 degraded 类型、精确枚举、可见面证据、恢复动作与恢复结果，并加入完成 AND。

6. **“消三胞胎”被写成已执行事实，但实际排程源仍保留旧 owner。**

   [协议 L5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:5)称 R-DOG 已删除、引用已全部改指；supplied ledger 仍在[L108](</private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:108>)排程并在[L717-L722](</private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:717>)保留卡文；仓内旧总账也仍保留 G6-12 自带协议与 R-DOG。

   修复：实际 tombstone/remove R-DOG，重写 G6-12 为依赖 G8-6 的消费卡；完成前协议只能写“裁定已作出、迁移待执行”。

## MEDIUM

1. **“≤3 分钟”没有成立的范围。**

   [L57-L62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:57)把完成一板、异常处置及台账登记放在同一清单，耗时无上界。页面也未标 active vault；`active_vault` 只在 JSON 中返回：[overview L233-L237](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/backend/app/api/v1/endpoints/review_overview.py:233)，HTML 未消费该字段。

   修复：改为“健康且无变更日的核对/打卡 overhead ≤3 分钟”，学习、修复和测试重跑排除；提供单一汇总命令并在页面标 active。

2. **§6 并未交付所称的完整四区模板，锁版也无 exact binding。**

   [L75-L81](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:75)只有一行 `D1 … D14`，没有变更表、事件表或累计表；[L104-L129](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:104)只有复选框，没有最终值、锁版人、时间或 digest。

   修复：补齐四张可复制表和 14 个日期行；锁定 exact values、skill 清单、协议 SHA/digest、锁版人和时间。

3. **Asia/Shanghai“同口径”未在运行环境钉死。**

   [协议 L12](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:12)声称同为上海日界；runner 使用宿主本地时区：[L203-L205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/daily_review_run.py:203)，overview 使用容器本地时区：[L208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/backend/app/api/v1/endpoints/review_overview.py:208)，compose 未设置 `TZ`。当前 live 容器时区未验证，因此该一致性至少是 UNVERIFIABLE。

   修复：显式 `ZoneInfo("Asia/Shanghai")`，或部署统一设定并在启动档案记录验证输出。

4. **“冻结 RC SHA”与跨新 SHA fix-forward 同句冲突。**

   [L38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:38)一面绑定冻结 RC，一面允许修复后新 SHA 延续窗口。

   修复：区分“滚动 candidate soak”与“冻结 RC soak”；若跨 SHA，报告每个 SHA 的暴露天数，不能继续称单一冻结 SHA。

5. **L613 原值栏转录不实。**

   [协议 L109](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:109)写“≥1 板/日”，而[计划书 L613](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:613)原文是“有到期项时至少完成一张板”。

   修复：原值栏逐字改为“有到期项时 ≥1 板”，不要把原义恢复写成校准。

## LOW

1. **C10 日终漏掉最后 59 秒。**

   [L34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:34)的 `--until="23:59"` 被 Git 解析为 `23:59:00`；与 `23:59:59` 的 epoch 实测相差 59 秒。

   修复：使用次日 `00:00` 的排他上界，或明确写 `23:59:59`。

2. **visual 移出项 owner 过于笼统。**

   [L127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:127)仅写“G7 切片”，实际 exporter、回读、回写、round-trip 分属 G7-4/G7-9/G7-10/G7-12。

   修复：分别指认 export/import owner 和“二者均 live 后纳入”的触发条件。

## C1–C10 源码核对矩阵

| 计数器 | 结论 | 核对结果 |
|---|---|---|
| [C1 L87](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:87) | FAIL | 日志字段存在，但命令不筛 active key、不判成功、未核台账，且 cwd 未定义。 |
| [C2 L88](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:88) | FAIL | `generated_at` 真实存在，但示例漏 `<vault>/`，只打印、不比较本地日。 |
| [C3 L89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:89) | PARTIAL | state 路径和 accepted 字段正确；key 无生成方法、`cat` 不判日期、仅保留最近值；当前无 `last_push_kind`。 |
| [C4 L90](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:90) | FAIL | 字符串 grep 可把 payload 中的 `answer_scored` 误计；UTC/上海跨日漏计；事件数不等于完成板数。 |
| [C5 L91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:91) | PARTIAL | 事件源存在，但未选 `recorded_at/effective_at`、时区及 90 分钟边界，自动计数缺失。 |
| [C6 L92](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:92) | FAIL | 无 node→recap 关联键，示例不执行声明的双源/mtime 判定。 |
| [C7 L93](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:93) | FAIL | 无 invocation receipt；文件数不能证明调用次数，board-split 又未 live。 |
| [C8 L94](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:94) | FAIL | 多 vault runner 日志不能证明 active 切换；命令丢顺序并拒绝合法 key。 |
| [C9 L95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:95) | FAIL | 正常行也含 `fallback:-`；页面无 `degraded` 枚举或历史快照；肉眼判不是机械计数。 |
| [C10 L96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:96) | PARTIAL | 能列 commit，但不能证明部署、捕获未提交配置或 fast-forward 当日引入的旧 commit，且日终边界漏 59 秒。 |

已正确落实的部分：fix-forward 主方向及新 SHA 重跑受影响 J、当前三项能力子集、10/5/3/2 数值转录，以及 G6-12 的“无手工救火”消费维度均已有落点；这些不足以抵消上述完成谓词与证据契约缺陷。

审查限制：全程只读，未读取 live vault/backups，未查询运行中容器或 launchctl；Graphiti MCP 本会话不可用。源码结论均在当前 checkout 独立复核，未把历史审查结论当作当前证据，未修改任何文件。


