结论：**FAIL，仍不可锁版、不可开窗。**

- Round‑1 18 项：**11 RESOLVED / 6 PARTIALLY‑RESOLVED / 1 STILL‑OPEN**
- 增量扫描：**4 BLOCKER / 4 HIGH / 4 MEDIUM / LOW 无**
- CARD 状态继续保持 `PARTIAL`；协议保持 `DRAFT / NOT START-READY`。
- 审查基线：`card/s7-dogfood @ 37387a8662e9dd646fad5628841679d777cb7eae`
- 当前协议 SHA-256：`aec639aef2972d42473fd40c238d4eb4ed16e5bdc6cbdb25026c99d033f4e953`，仍为 untracked。

## Round‑1 逐项复核

### BLOCKER 1–5

| 项 | 裁定 | 证据 |
|---|---|---|
| B1 三零可被 closed 洗掉 | **RESOLVED** | 完成式只统计确认违规：[v2 L35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:35)；`violation_status` 与 `closure_status` 已分离且确认不可改写：[v2 L73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:73)、[v2 L77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:77)。新增的“待裁绕过”是另一缺陷，见增量 B2。 |
| B2 连续 14 天可回填/误判 | **PARTIALLY-RESOLVED** | 正向日通过式、payload 按日归档和脚本前置已加入：[v2 L88](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:88)、[v2 L93](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:93)、[v2 L194](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:194)。但 [v2 L89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:89) 称 Git 时间戳 append-only、不可回填并不成立；`GIT_COMMITTER_DATE=2000-01-01… git var GIT_COMMITTER_IDENT` 实测接受回填日期。D1–D14 行预先存在，[v2 L104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:104) 使“commit 版本含 D 行”成为空判据。总完成式也未绑定“14 日全部通过”，见新增 B1。 |
| B3 C6 无法证明 ingest→board | **STILL-OPEN** | 新版诚实承认无法 join：[v2 L151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:151)；生产事件仍为 `payload: {}`：[node-derivation.ts L251](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/frontend/obsidian-plugin/src/node-derivation.ts:251)。但仍允许人工文字计入 ≥5，并明确当前人工口径可开窗：[v2 L195](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:195)。A10 知情只是风险接受，不是完成事实证明。 |
| B4 C8 多 vault ≠ 激活切换 | **RESOLVED** | 已明确多 key 不等于切换，并把“使用两 vault/激活切换两次”设为锁版二选一：[v2 L153](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:153)、[v2 L178](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:178)。选切换时要求 `from/to/time/.env diff` 有序回执；语义未锁不得启动：[v2 L31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:31)。 |
| B5 总账交付未完成却不阻塞 | **RESOLVED** | CARD 已标 PARTIAL、脚本成为开窗前置：[v2 L4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:4)、[v2 L194](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:194)；R‑EVD 报告路径、字段、截止和完成门已给出：[v2 L198](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:198)。与[总账 L379](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:379)要求相符。实际脚本仍未交付，但文档不再冒充 DONE/可启动。 |

### HIGH 1–6

| 项 | 裁定 | 证据 |
|---|---|---|
| H1 一题冒充一板 | **PARTIALLY-RESOLVED** | [v2 L168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:168) 提供二选一且锁版前 fail-closed；选 `(b)` 改名“一题”可闭合。但 `(a)` 仍以“≥1 `answer_scored` + 人工板名”近似整板完成。白名单仍无 `board_completed`：[learning_event_log.py L35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/backend/app/services/learning_event_log.py:35)，每题都会写事件：[quiz-answer L324](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/canvas-vault/.claude/skills/quiz-answer/SKILL.md:324)。 |
| H2 C1/C2/C3/C9 不可机械裁定 | **PARTIALLY-RESOLVED** | 谓词语法和 exit code 已补：[v2 L142](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:142)。但 A1 把 `RUNTIME_REPO` 定义成 `$WT`：[v2 L17](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:17)，而入口源码将数据根固定为主仓 `REPO`：[daily-review-push.sh L7](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/daily-review-push.sh:7)，runner 日志/state 写 `REPO/backups`：[daily_review_run.py L31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/daily_review_run.py:31)、[L95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/daily_review_run.py:95)。C1/C3/C9 却仍读 `$RUNTIME_REPO/backups`：[v2 L146](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:146)。三项仍指错根。 |
| H3 变更源不等于运行变更 | **PARTIALLY-RESOLVED** | runtime SHA、dirty、env、安装件、部署时间和测试结果字段已加入：[v2 L57](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:57)。但只记 dirty **数量**，不能绑定 dirty exact bytes；容器使用源码 bind mount：[compose L202](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/docker-compose.yml:202)，uvicorn 无 reload：[Dockerfile L27](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/backend/Dockerfile:27)，所以 SHA/“部署时间”不能证明长驻进程加载了新代码。OPEN/UNVERIFIABLE 还未进入完成门，见新增 H2。 |
| H4 新能力自动获得 14 天覆盖 | **RESOLVED** | A8 冻结 manifest：[v2 L24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:24)；新能力不自动纳入、不继承既往暴露天数，C7 类数也冻结：[v2 L50](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:50)。 |
| H5 degraded 未进入完成门 | **PARTIALLY-RESOLVED** | 已加入完成 AND 和恢复三字段：[v2 L36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:36)、[v2 L75](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:75)。但不要求恢复成功/closed，且 C9 漏掉真实 Bark 降级，故仍可假绿。 |
| H6 “消三胞胎”冒充已执行 | **RESOLVED** | 头部已改成“裁定已作出、排程源迁移待执行”并逐项列出现状：[v2 L7](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:7)、[v2 L197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:197)。上游仍保留 R‑DOG：[ledger L108](/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-s7-dogfood/871c2df6-525f-4c03-8d5d-3ff633c8ce81/scratchpad/ledger-v2.md:108)，新版没有再冒充迁移完成。 |

### MEDIUM 1–5 / LOW 1–2

| 项 | 裁定 | 证据 |
|---|---|---|
| M1 ≤3 分钟范围 | **RESOLVED** | 已限定为健康无变更日 overhead，并排除学习、异常处置和测试重跑：[v2 L83](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:83)。 |
| M2 四区模板/exact binding | **RESOLVED** | 四区完整模板在 [v2 L100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:100) 至活动量表；协议 SHA、锁版人/时间和 manifest binding 在 [v2 L24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:24)、[v2 L159](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:159)。 |
| M3 Asia/Shanghai 未钉死 | **PARTIALLY-RESOLVED** | A7 新增宿主/容器实测入档：[v2 L23](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:23)，但不要求一致，只在文档中选择宿主日界。runner 和 overview 仍分别取各自本地时区：[runner L203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/daily_review_run.py:203)、[overview L208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/backend/app/api/v1/endpoints/review_overview.py:208)。`date +%Z` 也不能唯一证明 IANA `Asia/Shanghai`。 |
| M4 RC 冻结与跨 SHA 冲突 | **RESOLVED** | 已明确当前是 rolling candidate soak、按 SHA 分段且不得宣称单一 SHA 14 天；冻结 RC soak 分到后续 E5：[v2 L62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:62)。 |
| M5 L613 原值转录 | **RESOLVED** | 已逐字恢复“有到期项时至少完成一张板”：[v2 L168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:168)，与[计划书 L613](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:613)一致。 |
| L1 C10 漏 59 秒 | **RESOLVED** | 已改次日 `00:00` 排他上界：[v2 L58](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:58)、[v2 L155](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:155)。 |
| L2 visual owner 过笼统 | **RESOLVED** | 已分别指认 exporter/import/diff/writeback/round-trip owners 和二者均 live 触发条件：[v2 L52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:52)、[v2 L186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:186)。 |

## 新版增量缺陷

### BLOCKER

1. **总完成式没有要求 14 日均满足“日通过”。**  
   [v2 L32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:32)只要求回执、活动量和事件门；正常日定义在[v2 L93](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:93)，却未被总式引用。`generate:FAILED` 日若有 commit 和事件解释，既非正常日，也不命中[v2 L96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:96)的漏日条件，仍可能计入完成。

2. **`待裁` 可绕过三零及无救火。**  
   状态允许 `待裁`：[v2 L73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:73)，但完成式只数确认：[v2 L35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:35)、[v2 L37](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:37)。真实丢失或救火事件永久留待裁即可保持 confirmed=0；全文没有 `待裁_count=0` 门。

3. **degraded 只要求字段存在，不要求恢复成功。**  
   [v2 L36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:36)和[v2 L79](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:79)只检查恢复三字段。`closure_status=open，恢复结果=仍失败` 仍字段齐全，可错误满足计划书“全部可恢复”。必须要求 `closed + 成功复测证据`。

4. **C9 匹配生产代码从不输出的 fallback 值。**  
   协议搜索 `fallback:osascript`：[v2 L154](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:154)；runner 实际输出 `push:failed/skip-nokey` 及 `fallback:ok/fail/-`：[runner L216](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/daily_review_run.py:216)、[runner L232](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/daily_review_run.py:232)、[runner L249](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/daily_review_run.py:249)。实际 fixture 中 `push:failed fallback:ok` 与 `fallback:fail` 均被 C9 错判为无 degraded。

### HIGH

1. **多 vault preflight 失败可被 active vault 成功掩盖。**  
   协议冻结 `DAILY_REVIEW_VAULTS`：[v2 L19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:19)，但每日门只检查 active 卡和 active C1：[v2 L85](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:85)。wrapper 对非法/越界/不可读的单库仅写 BOOTLOG 后继续：[wrapper L52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/launchd/daily-review-wrapper.sh:52)、[wrapper L91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/launchd/daily-review-wrapper.sh:91)。A 成功、B preflight fail 时，daily log 只有 A 的成功行，当前 C1/C9 可全绿。

2. **`OPEN/UNVERIFIABLE` 变更不阻止窗口完成。**  
   [v2 L59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:59)允许变更行保持 OPEN/UNVERIFIABLE，但[v2 L32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:32)的完成 AND 不要求所有变更闭合，rolling soak 可携带未经验证的行为变化宣称完成。

3. **跨 vault 投影缺少身份 binding。**  
   C2 只检查 `generated_at`：[v2 L147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:147)。overview 虽读取 payload `vault_id`：[review_overview.py L131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/backend/app/api/v1/endpoints/review_overview.py:131)，但条目身份取目录名：[review_overview.py L152](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/backend/app/api/v1/endpoints/review_overview.py:152)，没有比较两者。A 的今日 payload 放进 B 路径，C2 可 PASS，B 卡也可显示 ok。

4. **API 端口未冻结且核对 URL 硬编码 8001。**  
   协议固定 8001：[v2 L47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:47)、[v2 L85](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:85)，启动档案却不冻结 `API_PORT`。compose 支持覆盖：[docker-compose.yml L150](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/docker-compose.yml:150)，发行示例配置为 8011：[.env.example L83](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/.env.example:83)。

### MEDIUM

1. **A5 checksum 命令不可执行。** [v2 L21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:21)把 `~` 放进双引号；原命令实跑 `exit 1: No such file or directory`。  
2. **A6 secret 排除正则失效。** [v2 L22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:22)使用 ERE `KEY\|TOKEN\|SECRET`，fixture 中 `API_KEY/ACCESS_TOKEN/CLIENT_SECRET` 全部穿透；所谓非敏感摘要实际把 secret 行纳入哈希输入。  
3. **C2 接受 overview 会降级的时间形状。** `generated_at="2026-08-28"` 被 [v2 L147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:147)判 exit 0；overview 严格要求带时间和时区：[review_overview.py L36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/backend/app/api/v1/endpoints/review_overview.py:36)、[L180](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/backend/app/api/v1/endpoints/review_overview.py:180)。  
4. **A2 未唯一构造 `VAULT_PATH`。** [v2 L18](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:18)只引用 `ACTIVE_VAULT`，但它在示例中只是目录名：[.env.example L61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/.env.example:61)；实际 wrapper 还结合 `VAULTS_ROOT` 并解析物理路径：[wrapper L27](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/launchd/daily-review-wrapper.sh:27)、[wrapper L63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/launchd/daily-review-wrapper.sh:63)。

### LOW

无。

## 判定命令实跑摘要

```text
C1: 无行=1；仅 FAILED=1；FAILED→最终成功=0；成功→最终 FAILED=1；错 key=1
C2: +08:00=0；等价 UTC=0；纯日期畸形值=0（缺陷）
C3: 当日 accepted=0；前一日/缺值=1
C4: 正确按 event_type 字段计数；payload 内同名字符串未误计
C9: generate:FAILED=1；真实 fallback:ok/fail=0（漏报）；虚构 fallback:osascript=1
A5: exit 1
A6: KEY/TOKEN/SECRET fixture 行全部未过滤
```

审查限制：全程只读；未读取 live vault、backups、私有 `.env`，未查询容器/launchctl。生产运行态及 installed wrapper exact bytes 均为 `UNVERIFIABLE`；源码结论基于用户指定 checkout。未修改任何文件。既有审计清单仅用于约束并行证据矩阵、生产入口复核和限制披露，没有复用历史事实作为当前结论。


