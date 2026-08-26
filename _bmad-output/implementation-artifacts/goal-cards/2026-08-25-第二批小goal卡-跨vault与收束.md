# 第二批小 Goal 卡 — 跨 vault 链 + 欠账清偿 + 信息收集第一刀（待你过目批准）

> **批次 ID**: BATCH-2026-08-25-跨vault与收束
> **日期**: 2026-08-25 · **状态**: 🏁 **批次收官**——六卡完成、合并、live 部署（2026-08-27）
> **收官实录**: 三车道夜间完成（C1a 经 9 轮 Codex 对抗、C3 初审 FAIL 抓真 BLOCKER 除零崩溃、C4 初审 FAIL 抓 HIGH 持久化谎报，全部处置清零）→ 独立复核六卡裁判亲跑全绿 → 合并 88bc2e61/b03747aa/91383b1f 零冲突 → 合并态回归 43+68+62+7 passed、6675 收集无中断 → live 部署四件全验证（state 迁移+wrapper 重装带 vault= 标签、fsrs_bridge 双副本同步过预检门、board-recap 上库 checker 66/66、总览页上线 due 6/积压 8 实时数据）→ push 双远端
> **总览页地址**: http://127.0.0.1:8011/api/v1/review/overview/page（浏览器打开，仅本机可见）
> **拍板项**: 5 项按推荐执行（C4 下线 / C2 独立网页 / 通知每库独立 / C5 薄版裁剪 / A3 两条语义继续挂）
> **移交第三批候选**: C3 发现 fallback serialize datetime 缺陷；C4 的失败信号消费方控制流（评分:1009 / auto-create:2080）；C1b 后端卡状态命名空间化（休眠链）；A3 两条推送语义；C5 的 live 板 blinded forward test 复跑
> **主线**: 收束成"每天可依赖的生产力系统"——你确认的跨 vault Web UI 刚需链启动 + 消灭静默暗坑 + 信息收集从零到一
> **勘探方法**: 6 路只读 agent 并行勘探（与第一批同标准：file:line 证据 + 实测复现，含 curl/docker 实查）
> **上批战绩参照**: BATCH-2026-08-24 五卡一夜收官、跨模型审查拦 1 BLOCKER + 5 HIGH、CI 连续全绿

---

## 一、你只需要看这部分（大白话）

### 卡片速览（6 张，三条车道）

| 卡 | 一句话说明 | 修完你能感觉到什么 | 预计 |
|---|---|---|---|
| **C1a 复习管道的多科目隔离** | 现在的每日复习管道是"全局单例"：状态、锁、手机通知全共用一份——将来开第二个学科库时会互相覆盖（一个库推送过，另一个库当天就永远不推了） | 为"一库一学科"的未来铺轨；今天的单库使用零变化 | ~6h |
| **C2 跨库复习总览网页** | 你确认的刚需第一次落地：浏览器打开一个本地网页，每个学科库一张卡片——今天到期几个、欠了几个定义、推荐复习哪块白板，点击可跳回 Obsidian | **第一个能用浏览器看的复习界面**（只读版，交互复习是后话） | ~6h |
| **C3 历史数据定时炸弹** | 老版本存的复习记录里有个"状态 0"，新算法库读到会直接崩——现在数据里恰好 0 条，但语义裂缝还在，第二批管道一多迟早踩中 | 无感知（拆的是还没爆的雷） | ~4h |
| **C4 假"Graphiti 镜像"下线** | 勘探实锤：代码里调用的那个方法**在整个 git 历史中从未存在过**，而且底层根本不是 Graphiti 是本地文件，从诞生起写入 0 条、日志还谎报"已存入 Graphiti"——教科书级的名实不副 | 日志不再说谎；真接 Graphiti 等主干工程（epic-5a）就位后再做 | ~3.5h |
| **C5 白板回顾 skill（薄版）** | 信息收集闭环第一刀：在侧栏输 `/board-recap`，系统只读你的白板，生成一份回顾报告——覆盖了什么、几个问题没回答（最老的3条）、方向有没有跑偏、下一步做什么。**绝不改你的白板和笔记** | 主 goal 四大 MVP 里最后一个零实现的功能开始能用 | ~8.5h |
| **C6 找回丢失的保护网** | 上批为解锁测试收集临时绕过了一个坏测试，这卡把它按新架构重写、恢复"跨库数据不串写"的自动保护 | 无感知（防护网重新挂上） | ~3h |

### 车道编排（3 个标签页，和上批一样）

```
车道 1（串行链）:  C1a 多科目隔离  →  C2 总览网页     ← C2 要用 C1a 定的字段，必须排队
车道 2（串行）:    C3 拆雷  →  C4 假镜像下线          ← 都在后端复习域，一个 Session 顺序做
车道 3（串行）:    C6 保护网  →  C5 回顾 skill        ← C6 三小时热身，C5 是大头
```

三条车道文件零交集（勘探逐卡核过），可完全并行。**夜间试点建议：车道 2（C3→C4）**——判据最机械（复现命令翻绿 + grep 清零），且不碰你任何日常界面。

### 需要你顺手拍板的 5 个点（不拍就按推荐）

1. **C4 方向**：假镜像**安全下线**（推荐——删幻影调用+修谎报日志，保留真实在用的读功能）还是留着等 epic-5a 接通？勘探证据：接通在今天=违反项目自己的 Graphiti 契约（episode schema 归主干工程独占）。
2. **C2 即 D3 方向确认**：总览网页 = 你批注的"独立 Web UI"路线（方案 B）的第一步。默认按此走。
3. **C1a 手机通知策略**：将来多库时**每库一条独立推送**（推荐本批实现）还是合并成一条摘要（留给 Web UI 正片）？
4. **C5 薄版裁剪**：设计稿里有两项会写你的白板/笔记（问题状态机、往白板追加活动行），**本批明确裁掉**只做只读报告（守 G5 红线）。同意吗？
5. **A3 遗留两条推送语义**（上批挂起）：空首扫日轮转账边界 / 休息日推送后冒出到期卡是否放行同 id 覆盖推送——可这批顺手裁，也可继续挂着。

### 你怎么启动

- **"批准第二批，今晚跑车道 2"** —— 我建好三条车道环境后你开标签页；
- **"批准第二批，白天先跑"** —— 同上但夜间试点等你看过成果；
- 或对任何一张卡说"去掉/改成…"。

---

## 二、技术档案（给 Claude / Codex 读）

### CARD-C1a: 每日复习管道 vault 命名空间化（runner/payload 侧）

- **确认状态**: CONFIRMED。全局单例资产清单（全部实证）：state `backups/daily-review.state.json`（run.py:35，last_push_accepted_date 全局 → vault A 推过 vault B 当日永不推；payload_sha256/next_due_utc 单值 → 双 vault 交替跑 A3 缓存门乒乓失效；first_gen_today 全局 → 污染第二 vault 板轮转）；lock `backups/.daily-review.lock` 全局（push.sh:9）；log 无 vault 标签（run.py:36/228）;Bark id `canvas-review-{date}` 仅日期（pick.py:279）+ group 固定 → 第二 vault 覆盖第一 vault 手机通知。frontmatter/fsrs_bridge/decay_beta 链天然 per-vault 无需改。**后端 fsrs_card_states.json 链近休眠（live 仅 1 条 2026-04 测试残留，生产走 frontmatter）→ 拆出 C1b 推迟，本卡不碰 review_service.py/端点**。
- **方案**: state 文件按 vault key 命名空间化（`backups/daily-review.<vault_key>.state.json`，旧文件迁移 dry-run + .bak）；log 行加 `vault=` 标签；per-vault 锁；Bark 有效 id 在 **send 侧**组合 `{id}-{vault_key}`（payload.notification.id 值不动，尊重 A2 冻结 schema）；payload 加性新增顶层 `vault_id` 字段（schema_version 保持 3）；多 vault 循环留在 wrapper shell 层每 vault 一进程（⚠️ pick.py:345 的 decay_beta import 缓存坑，禁止进程内循环）。
- **完成判据**: ①回归 24 用例适配 + 新增"双 vault 同日各自推送"用例（tmp vault A/B，两次都 push:accepted、两个 state 文件独立、互跑后各自缓存门仍 cached）全绿；②`--vault A` 跑完后 JSON 输出 `3 <vault_id>`；③迁移 dry-run 零写入证明，实迁留 .bak；④单 vault 生产链回归：push.sh 退出 0 且 log 含 vault= 标签。
- **风险**: 测试 fixture monkeypatch 的是模块级常量 STATE/LOG，函数化后 7+ 用例注入方式要跟改（漏改会写真实 backups/）；test_daily_review_pick.py:236 锁死 notification.id 值——send 侧组合方案专门规避此断言；wrapper 装在 git 外（~/Library/Application Support/CanvasReview/bin/），改完须 cp 重装 + kickstart（**待用户确认节**）；当前仅 1 个 live vault，双 vault 端到端只能 tmp 模拟，真第二库等 deploy-vault 后补真机 UAT。
- **并行**: 本批独占 scripts/daily_review_{run,pick}.py、push.sh、wrapper、send_bark.py 与两个回归测试文件；C2 硬依赖本卡 vault_id 字段（同车道串行解决）。backups/ 命名空间规则由本卡定义。

### CARD-C2: 跨 vault 复习总览页·最小版（D3 方案 B 预演）

- **确认状态**: CONFIRMED。vault 枚举已存在（GET /api/v1/vault/list 实测 200 返回 3 vault）；容器可读全部 vault（docker exec 实测中文文件名 OK）；端口已收口 127.0.0.1:8011 仅本机可见；schema v3 字段对总览页全部够用；backend 无现成模板栈（grep StaticFiles/Jinja2/HTMLResponse 零命中）→ 内联 HTMLResponse 最小改动。诚实缺口：当下仅 canvas-vault 有投影（真实 N=1），聚合循环 N-通用，test-vault 可放 fixture 演示 N=2。
- **方案**: 新建 `backend/app/api/v1/endpoints/review_overview.py`：GET `/api/v1/review/overview`（JSON 聚合：扫各 vault outputs/今日复习.json，含 stale 判定）+ GET `/api/v1/review/overview/page`（内联 HTML：每 vault 一张卡——到期数/待剖析积压/推荐白板/generated_at + stale 徽标 + `obsidian://` 跳转链接）；router.py 加 1 行注册。只读展示，不做交互复习（G6 正片范围）。
- **完成判据**: 新增 `backend/tests/unit/test_review_overview.py` 全绿（聚合正确/缺投影 vault 降级显示/损坏 JSON 不 500/stale 徽标逻辑）；`curl -s http://127.0.0.1:8011/api/v1/review/overview` 返回 200 且 vaults 数组含 canvas-vault 真实数据；page 端点返回 HTML 含每 vault 卡片；重启容器后仍可用。
- **风险**: 依赖 C1a 的 vault_id 字段（车道内串行天然满足）；今日复习.json 缺失的 vault 必须显式"无投影"降级卡片，禁止静默跳过（诚实四态原则）;不碰 A2 冻结 schema（只读消费）。
- **并行**: 独占新文件 + router 1 行；与车道 2/3 零交集。

### CARD-C3: State(0) 历史数据反序列化修复

- **确认状态**: CONFIRMED（实测 `State(0)` 抛 ValueError；全部 live 存储现存 state:0 记录 = 0 条——是封堵潜伏脚枪不是止血，价值在 fsrs_bridge:92 与 mastery 标量默认 0 的语义裂缝会被后续投影/镜像管道踩中）。
- **方案**: 4 个改动点——fsrs_manager.py 读取层 0→Learning(1) 映射（fsrs v6 官方语义：v6 删除 New 态）+ serialize/card_to_state 写侧 `else 0` 兜底改 1（:286/:367 区域）+ fsrs_bridge.py:92 防御映射；docstring 注明 "legacy pre-v6 state:0 → Learning" 是对 A1 严格 roundtrip 原则的显式例外。
- **完成判据**: ①复现命令翻绿（deserialize state:0 → State.Learning，当前 ValueError）；②新建 `backend/tests/regression/test_fsrs_legacy_state_zero.py` 全绿（独立文件，不混入 A1 的 None 语义文件）+ test_fsrs_bridge.py 增例；③存量 FSRS 套件（A1 裁判 6 文件）不回归。
- **风险**: fsrs_bridge.py 属 live vault 用户日常写侧——worktree 改完须双副本 cp 部署（wrapper cmp 门会拦版本偏差），**部署待用户确认节**；不动 review_service 的静默 except（那是未来"静默降级根治"卡）。
- **并行**: 与 C4 同车道串行（文件零交集但同域）；与未来 G3 在 fsrs_manager.py 同文件——本卡体量最小先落地，后者 rebase。

### CARD-C4: 假 Graphiti 镜像安全下线（DD-13 名实归位）

- **确认状态**: CONFIRMED，双重 G-FAKE 实锤——①`git log -S "def add_learning_memory" --all` 为空：该方法**全历史从未定义**，真实 API 是 `add_learning_episode(LearningMemory)` 且 dataclass 无 card_data 字段，改名也存不下；②LearningMemoryClient 根本不是 Graphiti，是本地 JSON（learning_memories.json，dev+live 实测均 0 条记录 110 字节空壳）；③异常被吞后 **return True 谎报成功**，日志 "Saved card state to Graphiti" 名实全假；④失败计数器无任何暴露，没人看。
- **方案（方向 b，推荐）**: 删除 review_service.py 两处幻影调用（:2065/:2166）+ `_persist_auto_created_card` 后台任务（约 80 行）+ 读侧死块（:1981-2014，永远返回 None）+ 计数器 :309；修正虚假日志；**保留 get_learning_history**（6 处读路径真实在用）与 LearningMemoryClient 本体；处置记录写 known-gotchas（防复发）。"真接 Graphiti"=独立新卡且必须等 epic-5a（C-1 episode schema 归 Session B 独占，现在接通违反契约）。
- **完成判据**: ①`grep -rn "add_learning_memory" backend/app` 0 命中；②虚假日志 grep 0 命中；③3 个测试文件（test_fsrs_state_query / test_review_service_fsrs / test_review_singleton_di）适配后 0 fail；④新 concept 调 fsrs-state 后无 persist 失败 warning 且文件通道正常写入。
- **风险**: `_get_state_cancelling_bg` 帮助函数需同步简化（防留下针对已删代码的防御逻辑误导后人）；计数器被 2 个测试断言，连改；不删 client 本体。
- **并行**: 独占 review_service.py :1975-2185 + :309 区段；与所有其他卡零交集。

### CARD-C5: board-recap 薄版 skill（信息收集第一刀）

- **确认状态**: CONFIRMED（grep 全仓 recap 零实现，纯设计态）。数据可得性 3 板实测全通（get_board_manifest MCP 已上线，curl 实测 ok/degraded 字段正常）。⚠️ 设计稿 v2 有两项越 G5 红线（research_questions 状态机写节点 YAML、Recent Activity 追加写原板）——**本卡明确裁掉**（拍板项 4）。
- **方案**: `canvas-vault/.claude/skills/board-recap/`（SKILL.md 带 ROUTING 块逐字节抄 canonical + scripts/recap_scan.py 确定性收集器）。分工：脚本做 manifest 解析/种子派生分流/未答计数+最老3条/source revision/上次回顾 diff 原料/规模门；LLM 只做三维审查叙述与动作句（白名单模板）。报告落 `outputs/回顾-*.md`，frontmatter 必写 `type: recap`（防旧回顾以实测口吻回流 RAG/对话）。守门人登记：check_skill_routing_block.py EXPECTED_SKILLS +1（8→9）。
- **完成判据**: ①checker PASS 且 9 skill（CANVAS_BASE_PATH 指向 worktree 副本跑）；②零静默修改：3 块真实板 shasum 前后一致 + 3 份报告生成且含规定段落；③诚实降级：假板名显式拒绝、停 backend 走 FALLBACK 且报告头声明；④幂等：同板同日二跑询问续读/覆盖，二份对一份有 diff 标记；⑤blinded forward test 用全新 agent 最小上下文执行。开发/测试全程用 **worktree 副本 vault**；live 部署（skill 目录 cp + live 板 forward test）**待用户确认节**。
- **风险**: 范围蔓延是最大风险（薄版边界写进 SKILL.md 头部声明）；ROUTING 块手打必挂 C3 检查，必须逐字节抄；tips added_at 是最后变更时间非首次批注（时序结论措辞留意）。
- **并行**: 独占新 skill 目录 + checker 1 行；与 C6 同车道串行。

### CARD-C6: 回收 collect_ignore，恢复 memory 写侧隔离覆盖

- **确认状态**: CONFIRMED。孤儿测试原防 wave-5 跨 vault 泄漏 P0；机械翻译不可行（实测：新 `_vault_scoped_group_id` 完全忽略 ContextVar，改读进程级 active vault——旧断言必挂），必须语义重写；dry-run 已验证新口径断言全部能过（patch 目标必须是 `app.config.get_current_vault_id`，函数体内局部 import，patch memory_service 命名空间无效）。
- **方案**: 重写 test_memory_service_contextvar_leak.py（约 80 行：恒 vault: 前缀 ×2 / canvas>subject 二级优先 / patch 双 vault 不碰撞 / deprecated 裸 subject 仍落 vault: 桶，可选 +record_episode 分支 2-3 条）+ 删 conftest.py E0 块 12 行。docstring 显式记录"memory 写侧=进程级单 active vault"契约及其与未来多 vault Web UI 的耦合（不许默默冻结）。
- **完成判据**: ①conftest grep collect_ignore = 0；②全量收集无 Interrupted 且计数 ≥6634；③新测试文件 -v 全绿；④memory lane 无新增失败。
- **并行**: 独占 2 个测试文件；本批无 memory 口径卡，完全并行安全。

### 批次纪律（沿用第一批 + 两条新增）

- 沿用：独立 worktree / 测试当裁判先红后绿 / Codex gpt-5.6-sol **ultra** 只读审查（BLOCKER/HIGH 清零才算完）/ 验收单双段 / commit 带批次标记不 push / live 部署一律待用户确认。
- 新增①：**每张卡（含准备类）都要有独立 codex 审查存档**（补上批 E0 的纪律缺口）。
- 新增②：commit 前自查 commitlint（类型枚举 + header ≤100 字符 + body 行 ≤100）与 guard-hook（rm/pip uninstall 被拦，用 mv/重建绕）——上批实战坑，见 MEMORY。

---

## 三、执行手册（Session 路径 / 模型 / goal 提示词）

模型分工不变：开发全部 **Claude Code（Fable 5）**；审查统一冻结命令 `codex exec --sandbox read-only -m gpt-5.6-sol -c model_reasoning_effort="ultra" "<审查提示词>" > _bmad-output/审查/codex-review-CARD-xx.md`。

### 3.1 Session 路径（批准后 Claude 一键建好 worktree+环境再通知你）

| 车道 | 你在 iTerm 粘贴 | 分支 |
|---|---|---|
| 车道 1 · C1a→C2 | `cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault` ⏎ `claude` | `card/l1-crossvault` |
| 车道 2 · C3→C4（**夜间试点**） | `cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt` ⏎ `claude` | `card/l2-fsrs-debt` |
| 车道 3 · C6→C5 | `cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l3-recap-skill` ⏎ `claude` | `card/l3-recap-skill` |

### 3.2 各车道 `/goal` 提示词（逐字复制）

**车道 1（C1a → C2）：**

```
/goal 依次完成 CARD-C1a 与 CARD-C2。必读卡片档案：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md 的 CARD-C1a 与 CARD-C2 节（含全部 file:line 证据与方案约束）。
第一步 C1a（完成条件 AND）：(a) scripts/daily_review_run.py：state 文件按 vault key 命名空间化 backups/daily-review.<vault_key>.state.json，log 行加 vault= 标签，first_gen_today/board_last_recommended/next_due_utc 全部 per-vault；(b) scripts/daily_review_pick.py：payload 顶层加性新增 vault_id 字段（schema_version 保持 3，其余字段零改动——A2 冻结契约）；notification.id 的值禁止改动；(c) scripts/send_bark.py：send 侧用顶层 vault_id 组合有效通知 id "{id}-{vault_key}"，group 加 vault 维度；(d) scripts/daily-review-push.sh + scripts/launchd/daily-review-wrapper.sh：per-vault 锁与多 vault shell 层循环（每 vault 一个进程——严禁 Python 进程内循环，pick.py:345 decay_beta import 缓存坑）；只改仓库副本，安装副本 cp 重装写入验收单待确认节；(e) 新增 scripts/migrate_daily_review_state.py：--dry-run 打印旧→新映射且零写入，实迁保留 .bak；(f) 裁判：cd backend && .venv/bin/pytest tests/regression/test_daily_review_run.py tests/regression/test_daily_review_pick.py -q 全绿（适配 monkeypatch fixture——STATE 路径函数化后逐用例检查注入，防写真实 backups/），并新增"双 vault 同日各自推送"用例（tmp vault A/B 两次都 push:accepted、两个 state 文件独立、互跑后各自缓存门仍 cached）；(g) 单 vault 生产回归：python3 scripts/daily_review_run.py --vault <worktree 的 canvas-vault 绝对路径> --now 2026-08-26T10:00:00+08:00 退出 0 且 JSON 含 vault_id。
第二步 C2（完成条件 AND）：(a) 新建 backend/app/api/v1/endpoints/review_overview.py：GET /api/v1/review/overview（JSON 聚合各 vault outputs/今日复习.json，缺投影 vault 显式"无投影"降级条目、损坏 JSON 不 500、stale 判定基于 generated_at）+ GET /api/v1/review/overview/page（内联 HTMLResponse：每 vault 一张卡——到期数/待剖析积压/推荐白板/generated_at+stale 徽标+obsidian:// 链接；无外部 CDN，纯内联样式）；(b) backend/app/api/v1/router.py 加 1 行注册；(c) 可在 test-vault/outputs/ 放一份 fixture 今日复习.json 演示 N=2（标注测试数据）；(d) 裁判：新增 backend/tests/unit/test_review_overview.py 全绿（聚合/降级/损坏/stale 四类用例，真实文件 fixture 禁 mock 文件系统语义）。
两卡各自：Codex 审查（统一命令，档案 §三 开头，重点审 C1a schema 加性与 fixture 注入完整性、C2 降级诚实性）存档 _bmad-output/审查/codex-review-CARD-C1a.md 与 codex-review-CARD-C2.md，BLOCKER/HIGH 清零；各自独立 commit 含 "BATCH-2026-08-25-跨vault与收束 / CARD-C1a"、"/ CARD-C2"；各自小白验收单 ship 到本 worktree _bmad-output/验收单/（C1a 含 wrapper 重装待确认节）。
硬边界：不 push；不碰 live vault 与 ~/Library；不动 backend/app/services/review_service.py 与 fsrs_manager.py（车道 2 地盘）；不动 canvas-vault/.claude/skills/（车道 3 地盘）；commit 前自查 commitlint 行宽/类型，guard-hook 拦 rm 用 mv。
```

**车道 2（C3 → C4，夜间试点）：**

```
/goal 依次完成 CARD-C3 与 CARD-C4。必读卡片档案：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md 的 CARD-C3 与 CARD-C4 节。
第一步 C3（完成条件 AND）：(a) backend/lib/memory/temporal/fsrs_manager.py：deserialize 读取层 legacy state:0→State.Learning(1) 映射（fsrs v6 官方语义），serialize_card/card_to_state 写侧 else 0 兜底改 1（约 :286/:367 区域，以当前代码为准），docstring 注明"legacy pre-v6 state:0 → Learning，系对 CARD-A1 严格 roundtrip 的显式例外"；(b) canvas-vault/.claude/scripts/fsrs_bridge.py（仅 worktree 副本）:92 附近防御映射，live 双副本 cp 部署写入验收单待确认节；(c) 先红后绿：新建 backend/tests/regression/test_fsrs_legacy_state_zero.py（独立文件，禁混入 A1 的 None 文件）——deserialize state:0→Learning 且 reps/due 保留 / serialize 与 card_to_state 永不写 state=0 / fsrs_bridge 收到 fsrs_state:0 不抛且产出 ≥1；test_fsrs_bridge.py 增例；(d) 裁判：cd backend && .venv/bin/pytest tests/regression/test_fsrs_legacy_state_zero.py tests/regression/test_fsrs_new_card_none_serialization.py tests/unit/test_fsrs_manager.py tests/regression/test_fsrs_bridge.py -q 全绿；复现一行命令（档案 C3 节 done_criteria ①）从 ValueError 翻为输出 State.Learning。
第二步 C4（完成条件 AND，处置方向=安全下线）：(a) backend/app/services/review_service.py：删除 :2065 与 :2166 两处 add_learning_memory 幻影调用、_persist_auto_created_card 后台任务、读侧死块（约 :1981-2014，永远 None）、计数器 :309（行号以当前代码为准）；修正全部 "card state to/from Graphiti" 虚假日志；保留 get_learning_history 与 LearningMemoryClient 本体（6 处读路径真实在用，禁删）；(b) 同步简化 test_fsrs_state_query.py 的 _get_state_cancelling_bg（删除针对已删后台任务的防御逻辑）并适配 test_review_service_fsrs.py / test_review_singleton_di.py 的计数器断言；(c) docs/known-gotchas.md 记 G-FAKE 处置条目（含"真接 Graphiti 须等 epic-5a C-1/C-2 契约"）；(d) 裁判：grep -rn "add_learning_memory" backend/app 0 命中；grep -rn "card state to Graphiti\|card state from Graphiti" backend/app 0 命中；cd backend && .venv/bin/pytest tests/unit/test_fsrs_state_query.py tests/unit/test_review_service_fsrs.py tests/integration/test_review_singleton_di.py -q 0 fail。
两卡各自：Codex 审查（统一命令见档案 §三，C3 重点审 0→1 映射语义与 roundtrip 例外标注、C4 重点审"是否误删真实在用的读路径"）存档 codex-review-CARD-C3.md / codex-review-CARD-C4.md，BLOCKER/HIGH 清零；独立 commit 含 "BATCH-2026-08-25-跨vault与收束 / CARD-C3"、"/ CARD-C4"；验收单各一份。
硬边界：不 push；不碰 live vault；不动 scripts/daily_review_*（车道 1 地盘）与 skills/（车道 3 地盘）；不改 review_service 其他区段的 except 模式（未来卡）；commitlint/guard-hook 注意事项同档案 §二 批次纪律。
```

**车道 3（C6 → C5）：**

```
/goal 依次完成 CARD-C6 与 CARD-C5。必读卡片档案：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md 的 CARD-C6 与 CARD-C5 节。
第一步 C6（完成条件 AND）：(a) 语义重写 backend/tests/unit/test_memory_service_contextvar_leak.py（机械翻译已被勘探证伪——新 _vault_scoped_group_id 忽略 ContextVar 读进程级 active vault）：断言恒 vault: 前缀 ×2 / canvas_name>subject 二级优先 / patch app.config.get_current_vault_id（注意：函数体内局部 import，patch memory_service 命名空间无效）模拟双 vault 不碰撞 / deprecated 裸 subject 仍落 vault: 桶；docstring 显式记录"memory 写侧=进程级单 active vault"契约及与未来多 vault Web UI 的耦合；(b) 删除 backend/tests/conftest.py 的 CARD-E0 collect_ignore 块（约 :33-44）；(c) 裁判：grep -c collect_ignore backend/tests/conftest.py 为 0；cd backend && .venv/bin/pytest --collect-only -q 2>&1 | tail -1 无 Interrupted 且计数 ≥6634；新测试 -v 全绿；pytest tests/unit -q -k memory 无新增失败。
第二步 C5（完成条件 AND，薄版硬边界=零写侧）：(a) 新建 canvas-vault/.claude/skills/board-recap/SKILL.md（frontmatter 齐全 + ROUTING 块逐字节抄 start-exam-board 的 canonical，手打必挂检查）+ scripts/recap_scan.py（确定性收集器：get_board_manifest JSON 解析、种子/派生分流台账、tips 未答计数+最老3条、source revision=板 SHA+sync 时间戳+manifest freshness、上次回顾"你现在可以做的"段抽取供 diff、规模门计数；LLM 只做三维审查叙述与白名单动作句）；报告写 outputs/回顾-<板名>-<日期>.md，frontmatter 必含 type: recap；明确裁掉设计稿的 research_questions 状态机与 Recent Activity 追加（G5 红线，SKILL.md 头部声明薄版边界）；(b) backend/scripts/check_skill_routing_block.py 的 EXPECTED_SKILLS 登记 board-recap（8→9）；(c) 裁判：CANVAS_BASE_PATH=<本 worktree canvas-vault 绝对路径> python3 backend/scripts/check_skill_routing_block.py 全 PASS 且 9 skill；零静默修改证明：shasum -a 256 worktree canvas-vault 的 原白板/*.md 节点/*.md 存 before.txt → 以全新 agent 最小上下文对 CS188 lecture 2 / 特征值与特征向量 / CS 61B 三板各跑一次 blinded forward test → shasum -c before.txt 全 OK 且 outputs/ 出现 3 份含规定段落的报告；诚实降级：假板名显式拒绝、停 backend 走 FALLBACK 且报告头声明；幂等：同板同日二跑出现续读/覆盖询问。全部用 worktree 副本 vault；live 部署（skill cp + live 板 forward test）写入验收单待确认节。
两卡各自：Codex 审查（统一命令见档案 §三，C6 重点审契约 docstring 是否如实、C5 重点审薄版边界零写侧与 ROUTING 逐字节）存档 codex-review-CARD-C6.md / codex-review-CARD-C5.md，BLOCKER/HIGH 清零；独立 commit 含 "BATCH-2026-08-25-跨vault与收束 / CARD-C6"、"/ CARD-C5"；验收单各一份（C5 含 live 部署待确认节）。
硬边界：不 push；不碰 live vault（含 live 的 .claude/skills/）；不动 memory_service.py 与 config.py 的口径实现（只写测试）；不动车道 1/2 的任何文件；commitlint/guard-hook 注意事项同档案批次纪律。
```

### 3.3 生命周期（与第一批相同）

```
你开标签页粘 /goal → Fable 开发（先红后绿）→ codex ultra 审查清零 → commit（不 push）+ 验收单
  → 独立复核（主 session 组织，亲跑裁判命令）→ 你早上验收 → 合并 → live 部署（逐项待你确认）→ push 看 CI
```

User：![[截屏2026-08-27 上午5.44.36.png]]
**User：这个网页web，制作建议给 ChatGPT 使用浏览器操作审查一下，就想 anki 一样，我需要清晰看到每个 vault，里面需要我复习哪些白板，然后到期时间是什么，这里还是没有给我一个清晰的显示**

> [!note]+ Claude 回复（2026-08-27）：已采纳为第三批头号卡 D1
> 判定为有效缺陷反馈——C2 最小版只做了汇总卡，没做到你要的"库→白板→到期时间"三级清晰视图（数据都在投影文件里，是展示层没做到位）。D1 卡目标=Anki 式层级视图 + 浏览器实测审查进 DoD（Claude 用浏览器自动化亲自走查+截图，另出 ChatGPT 审查任务书供你转贴）。完整回复见 [[2026-08-27-批注回复-C2总览页Anki化需求]]。勘探 workflow 已启动。