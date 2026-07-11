# Canvas Learning System 全景状态报告（2026-07-12）

> **产出方式**: 9-agent 并行深探（PRD 需求提取 / 后端盘点 / 前端盘点 / Graphiti 真机实证 / 检索对抗审查 / Skill 对抗审查 / 2 路交叉证伪 / 完整性批判），全部结论带 file:line 或真机 curl 证据，关键判断经二次独立证伪。共 471 次工具调用。
> **批注方式**: 每节可用 `**User：**` 直接批注；待拍板问题集中在 §9。

---

## 0 · 五句话 TL;DR

1. **Graphiti 后端已启动且写读全链真机打通**（POST tip → Neo4j 落盘 → search_memories 查回，31 节点全在正确 vault 桶）——你问的这个问题答案是 ✅。
2. **但你实际用的产品不是我们开发的产品**：Obsidian 打开的是主仓 vault（6 月 11 日旧插件 + 无鉴权 hook → enrich-hook 静默 403），近一个月全部开发验证都在 worktree 副本——**部署分裂是当前基本功能的头号阻断**。
3. 「精确返回笔记片段」**管道是真的、"精确"是假的**：RRF 分数压缩使相关性过滤在数学上失效——考 eigenvalue 和问"怎么烤面包"注入完全一样的 10 条材料（真机对照实验）。
4. Skill 体系**工程诚实度高但铁律全是 prompt 级**，且系统唯一的确定性 hook（enrich-hook）在出题轮**反向破坏**信息隔离 d=1.50（把答案正文注进出题对话）。
5. 隐藏数据风险：**Neo4j 519MB 学习记忆寄居在另一个随时可能被清理的旧 worktree 里，零备份**；评分双轨永不合流（backend 评的分被插件丢弃）；FSRS 复习是假闭环（读已废弃的 .canvas 颜色）。

---

## 1 · 核心 Graphiti 后端是否已启动 —— ✅ 已启动（7 项真机实证）

| 检查 | 结果 | 证据 |
|---|---|---|
| 双容器 + health | ✅ PASS | backend :8011 Up 36h healthy；neo4j :7691 Up 42h healthy；health 报 neo4j: ok |
| 图数据分布 | ✅ PASS | 31 节点：Entity×19 + CanvasNode×9 全在 `vault__canvas_vault`，边 RELATES_TO×31 + CANVAS_EDGE×2 |
| **写读全链** | ✅ PASS | POST /api/v1/tips 探针 → Neo4j 真实落盘（RELATES_TO 边）→ 10s 后 search_memories 查回（source=graphiti, relevance=2.0） |
| episode worker | 🟡 DEGRADED | 运行正常零错误；但 add_episode 队列**零流量**（全窗口 'Episode processed' 0 次——主链路已是零 LLM 结构化直写，队列只是 fallback 且从未验证）；shutdown 时抛 Py3.11/3.13 兼容 AttributeError（无害噪音） |
| enrich-hook 检索 | ✅ PASS | 162ms 返回 10 条 supplementary（质量问题见 §5） |
| LanceDB 索引 | 🟡 DEGRADED | 数据真实（canvas_vault_vault_notes 25 行）且在服务；但**两个观测端点全失真**：/health/lancedb 报 0 表、/index/vault/status 因查无前缀表名恒报"未索引"——会诱导不必要的 force rebuild |
| T4 跨节点素材 | ✅ PASS | 考 Fundamentals 返回 UAT 邻居的确认错误 + 增殖原因 |

**结论**: 栈是活的、写通读通（昨天 T1 修复后）。两处 DEGRADED 都是可观测性失真而非功能故障。

---

## 2 · ⛔ 头号发现：部署分裂（你在用的 ≠ 我们在开发的）

**亲自复核过的事实**（非 agent 转述）：

- Obsidian 注册表里 `open: true` 的学习 vault = **主仓** `canvas-learning-system/canvas-vault`
- 主仓插件 main.js build 时间 = **6 月 11 日**（缺一个月更新：S3 死命令清理、annotation_id 稳定批注身份、T5 错误候选命令全都没有；`canvas:start-examination` 还在直调已弃用的 /api/v1/exam/start 旧链）
- 主仓 vault 的 `.claude/settings.json` **无 X-CLS-Internal-Key 鉴权头** → enrich-hook 每次都 403 **静默失败**（你以为有 auto-RAG，实际一直没有）
- 而后端容器挂载、索引、回填、全部 T1-T6 修复和验证 → 都在 **worktree 副本** `.claude/worktrees/feature-obsidian-hybrid-dev/canvas-vault`（未在 Obsidian 注册；且其插件 data.json 缺 backendUrl，默认打向 8001 死端口）
- 两副本内容已分叉（主仓多 CS188/CS189 等文件）

**后果**: 近一个月"已验证 ✅"的功能，在你的日常使用里一个都没生效。这必须最先解决（方案见 §9-Q1）。

**User：请你查询一下我们当时是在哪一个路径使用 claude code ，因为`canvas-learning-system/canvas-vault` 是作为我们当时测试使用 Canvas learning systeam 的仓库**

> **[A1 2026-07-12 → round1]** ✅ 已查证，你的记忆完全正确：主仓 canvas-vault 就是 round-7 契约钦定的测试 vault，你从未用错。分裂根因 = 5 月 3 日创建 worktree 后开发 session 迁入（6-13 起），插件部署目标和后端挂载被隐式带进 worktree 的 vault 副本，从未迁移使用侧——你 6-12 还在主仓学 CS188、7-07 还在主仓用 Claudian。完整时间线详见 [[R1-Q1_部署路径历史查证|📚 R1-Q1]]

---

## 3 · 已开发功能清单（证据分级；✅=真机验证 🟡=部分/带缺陷 ）

### 3.1 真正活着的生产窄链（Hybrid 闭环）

建白板 → Cmd+Shift+D 派生 → Cmd+Shift+A 批注 → /start-exam-board 出题 → 手写答 → /quiz-answer 静默评分 → Dashboard。这条窄链的每一环：

| 环节 | 状态 | 说明 |
|---|---|---|
| ORIG-01/02 扁平架构 + 白板 | ✅ | vault 真实结构佐证 |
| ORIG-04 / MVP-14 派生（Cmd+Shift+D） | ✅ | v4.0 起 100% plugin 本地脚本（零 LLM）+ 静默 POST /tips/relation；**注意：SKILL.md 还描述着已删除的旧管道**（§6-F2） |
| ORIG-07 / MVP-05 批注（Cmd+Shift+A） | ✅ | 本地 callout + POST /api/v1/tips → Neo4j 真持久化 |
| EXAM-01 检验白板生成+信息隔离 | ✅ | v1.1 + 双重对抗审查；**但隔离有两个新发现的破口**（§5/§6） |
| EXAM-02/03/04/05 批注出题/薄弱选题/md 答题/4 维静默评分 | ✅/🟡 | skill 链就绪；**评分管道从未在真实数据上跑过**（唯一检验白板仍 in_progress，全 vault 零 calibration_log） |
| EXAM-09/10 考中拉节点/疑问归纳 | ✅ | EXAM-10 的 wikilink 已于 7-09 补上 |
| MVP-11 bge-m3 检索 | ✅ | 唯一真实检索路（1024d 双语 + jieba FTS） |
| MVP-12/13 Claude Code 订阅引擎 + 8 skills | ✅ | 超配（PRD 要 6 个实有 8 个） |
| Graphiti 写侧（MEM-01） | ✅ | tips→structured_writer→Neo4j 结构化直写，昨日 T1 后读侧也通 |
| T4 跨节点素材（MEM-05 起步） | ✅ | 后端+skill Step 4.5 落地，等你真跑 /start-exam-board mini-UAT |
| T5 错误候选 accept/dispute | ✅ | 命令+端点接线，**但生产侧是空的**（§4） |
| T6 Dashboard 考察历史聚合 | ✅ | dataviewjs 静态契约核对通过（未浏览器实测） |
| LanceDB 索引 + 检验白板黑名单 | ✅ | 25 行零考题泄漏（主路径；旁路见 §5） |
| 鉴权链 | ✅ | 无 key 403 fail-closed，key 三处一致（worktree 侧） |

### 3.2 实现完整但休眠的后端资产（DEAD 调用侧，非删除对象）

- 检验白板后端全量管道：exam_service 会话流 + ACP（select_target_node/assemble_acp）+ AutoSCORE 4 维评分链 —— S3 删除插件直调后零调用方，生产已转移到 skill 本地出题
- mastery HTTP 端点面 + BKT/FSRS 链
- sync_service .canvas 同步（vault 已 0 个 .canvas 文件）
- graphiti_memory_reader 4 读器中 3 个（P1 frontmatter pivot 后失去调用方）

---

## 4 · 未开发 / 断裂功能清单（按甲方"基本功能"优先级排序）

### 4.1 影响当前基本功能的断裂（修复成本低 → 高）

| # | 问题 | 证据 | 修复成本 |
|---|---|---|---|
| B1 | **exam/grade 评分完全死**：litellm 拼出 `google/gemini-3.1-flash-lite-preview`（应为 `gemini/` 前缀）→ 永远 502；exam/quick 出题同因永远退化为无 LLM 模板题 | exam_grade.py:105-112, question_generator.py:606-612, 真机 502 复现 | **一行**（.env 设 SCORING_MODEL 或改前缀拼接） |
| B2 | **tips 实时写链落错桶**：save_tip 显式传 DEFAULT_GROUP_ID → 实时批注进 `vault__default` 而非当前 vault；靠"下次重启回填"才落对桶 | tips.py:283 | 小（改传当前 vault group） |
| B3 | **双轨评分永不合流**：backend grade 返回的 mastery_delta 被插件丢弃（main.js grep 0 处），真正演化 mastery 的只有 quiz-answer 本地 EMA——两套从不校准 | exam-quick.ts + main.js 实证 | 需决策（§9-Q3） |
| B4 | **错误候选生产侧死**：唯一自动入口 /chat/post-turn-extract 零调用方（GAP-D），全 vault 只有 1 条手造 UAT 候选——T5 修好的消费端操作的是空流水线 | chat.py:627, grep 实证 | 中（需设计触发时机） |
| B5 | **FSRS 复习假闭环**：/review/schedule 读 .canvas 颜色节点（hybrid vault 无此数据）→ 永远空列表；写侧零调用。插件"打开复习队列"命令 = 活着的死管道 | review.py:569-620, 真机空 200 | 中（需改读 frontmatter） |
| B6 | /chat/enrich-context 运行时 500（调用已删除的 search_error_memories）——无调用方所以不阻塞，但属活端点炸裂 | chat.py:296, BUG-3957E968 | 小 |
| B7 | RAG 5 通道融合 0/5（LangGraph fan_out 路由 bug 两月未修）→ "6-source RAG"实为裸 LanceDB 单路兜底 | state_graph.py, note_search_tools.py:143 自述 | 中 |

### 4.2 明确未做（有裁决或待裁决）

- **EXAM-06 三种考察模式** ❌（裁决：C5 复盘后再议）
- **EXAM-07 4 级渐进提示** ❌（静默砍掉无 descope 记录，待你拍板）
- **EXAM-08 跳过选项** ❌（7-10 你已拍板：继续缓）
- **MVP-08 Edge 对话 2 重策略（EI+SE, d=0.80-1.00）** ❌ 换轨后无落点也无 descope 记录——MVP 效应量第二大的设计悬空
- **MEM-04 对话蒸馏 Hot-Warm-Cold** ❌（蒸馏器是 Tauri 组件，已死）
- **MVP-04 节点对话的 session 双层记忆管理** 🟡（剪贴板注入闭环通，历史压缩未做）
- 部署三层/LICENSE/UUID 迁移 ⏸（任务书裁决：基本功能稳定后）

---

## 5 · 对抗审查 ①「精确返回笔记片段」设计 —— 评级 **fragile**

> 结论先行：**管道全部是真的**（索引/hybrid 检索/hook/鉴权 WIRED 且可复现），但"精确"二字当前不成立，且信息隔离存在两个已验证的结构性破口。

### CRITICAL（1 项）

**R1 · 相关性过滤在数学上已死亡。** RRF 融合分数被压缩进 (0.50, 0.508] 的窄带（lancedb_client.py:2888-2943 三重转换），hook 的 min_relevance=0.30 永远滤不掉任何东西。**真机对照实验**：查 "what is an eigenvalue" 返回 rank1=递归笔记(0.504)压过全部特征值笔记；查 "how do I bake sourdough bread"（零相关）同样注入 10 条、同样 0.45-0.51 分数带。你之前观察到的"递归笔记 0.508"其实是这个体系的**满分**。每条 ≥5 字符的 prompt 都被注入 ~5KB 可能完全无关的材料 + "必须 Read"指令。注释自认等 Phase B sigmoid 归一化——从未落地（supplementary_search_service.py:79）。

### HIGH（3 项）

**R2 · 信息隔离反向破口**：hook matcher 为空串匹配一切 prompt，真机复现 `/start-exam-board ...` 出题轮被注入源笔记正文 snippet（Fundamentals 的定义原文）+ "必须先 Read 完整文件"指令——与 HARD-ISO-4"绝不整段 Read 节点"正面互斥。黑名单只防"考题流入检索"，这个破口是"**答案流入出题**"，d=1.50 单向失守。
**R3 · 黑名单单层防御有已验证旁路**：/index/vault/incremental 与 index_single_file 零黑名单检查（真机 POST 检验白板文件被接受），目前只靠一条僵尸指纹的 hash 巧合封住；且考题 type=exam_board 不在查询侧排除清单里——一旦入库直通检索。
**R4 · 索引无任何自动更新触发**：无启动重建/无 watcher/skill 无 reindex 指令，新派生节点对 RAG 永久不可见直到手动 curl。当前索引新鲜纯属最近手动重建的巧合。

### MEDIUM 择要

- R5 观测端点失真（§1 已述），会诱发不必要的 force rebuild（CPU embedding 分钟级 + 无并发锁）
- R6 多 vault 半成品：指纹表全局单表不分 vault；enrich-hook 有 cwd 字段但从未用，vault 身份靠进程级全局值
- R7 **skill 三态路径契约已与 hook 漂移**：hook 恒返回 10 条，而 study-question 判定条件"N < 10"恒假、chat-with-context "N < 8" 同病——决策树无匹配分支，Claude 只能即兴发挥
- R8 "必须 Read 核实"是纯 prompt 约束 + hook 路径无去重（10 名额被同文件 3-4 条 chunk 挤占）

### 做对了的（strengths 择要）

主路径黑名单真实生效（25 行零考题）、鉴权端到端 fail-closed、prompt-injection 四字段 taint 扫描纵深超预期、chunking 设计扎实（heading 切分+代码块原子保护+面包屑）、降级纪律一致。

---

## 6 · 对抗审查 ② Skill 体系设计 —— 评级 **fragile**

> 结论先行：工程诚实度突出（未实现的都标注了、取舍都写明了），防注入意识贯穿全部 skill。但**系统灵魂（信息隔离）没有任何确定性 guard 兜底**，且已发现真实漂移证据。

### HIGH（3 项）

**F1 · 铁律 vs 基础设施正面互斥**：vault 唯一的确定性 hook（enrich-hook）在出题轮反向工作（同 R2，从 skill 侧看）。HARD-ISO×5 / HARD-SILENT / HARD-Q 全部纯 prompt 级，无任何 PreToolUse guard 拦"考试期间 Read 节点正文"。**历史白板已有漂移实锤**：唯一真实产出的检验白板考了"Fundamentals vs Characteristic-Equation 区别"——正是现版 SKILL 明令禁止的父子对比反模式（规则是事后补丁，说明违反真实发生过且不可检测）。
**F2 · ai-linked-doc SKILL 与插件严重契约漂移（G-PIPE）**：SKILL 宣称"plugin 触发+剪贴板注入+AI 生成定义"，实际 v4.0 插件已是 100% 本地脚本派生（零剪贴板、零 skill 调用、节点=讨论容器占位模板）。SKILL 从未被触发；若手动触发会按旧哲学 AI 直写定义正文（与"用户自己写理解"的现行产品哲学相反）并可产生 _2 重复节点。
**F3 · quiz-answer 静态 python 两个数据缺陷（沙盒复现）**：① calibration_log 追加假设它是 frontmatter 最后一个 key——Obsidian Properties 在末尾新增属性（极常见）后，校准事件**静默错档进相邻列表键**（yaml 解析正常通过，零报错）；② 首评分支无 [0,1] 钳制，LLM 把 grade(1-4) 误当 grade_norm 传入 → mastery_score: 3.5 落盘污染全链。

### MEDIUM 择要

- F4 "原子写"名不符实（open(w) 直写非 tmpfile+replace；/tmp 固定 payload 路径跨 session 竞态）
- F5 评分管道从未在真实数据上运行（零 calibration_log；本次审查的沙盒是第一次全链执行）+ 用户 Obsidian 编辑缓冲与 skill 写文件 last-writer-wins 竞态
- F6 Step 4.5 vault_id 取"目录名"是**巧合正确**（sanitize 恰好归一到 config 值）；应改读 .canvas-config.yaml，且 curl `|| true` 使鉴权失败/群组错配/真无素材三者不可区分
- F7 同分钟重建同板会静默覆盖 + event_id 复用连锁污染幂等
- F8 掌握度阈值**三套并存**（0.3/0.4/0.5 档界 + 0.7 边界开闭不一）——同一个分数在不同入口被判成不同档位

### 做对了的

后端契约健康（本次逐个验证的端点全部存在且鉴权正确）、T4 服务端隔离纪律比 skill 侧扎实、EMA 数学正确且 event_id 幂等真拦住重放、防注入设计真实有效、版本演进全部有据可查。

---

## 7 · 数据安全与运维风险（完整性批判发现，此前所有探查都没碰）

| # | 风险 | 证据 | 严重度 |
|---|---|---|---|
| D1 | **Neo4j 519MB 学习记忆图寄居在 feature-deeptutor-canvas-mvp 旧 worktree 的 bind-mount 里，git-ignored，零备份**——`git worktree remove` 那个分支 = 记忆全部蒸发 | docker inspect 实证 | ⛔ 最高 |
| D2 | **检验白板内容已泄入 Graphiti 图**：vault_backfill 只跳 .obsidian/templates，不复用 LanceDB 黑名单——图里已出现 'SKILL'、'Dashboard'、检验白板会话实体。信息隔离只在 LanceDB 层成立 | vault_backfill.py:155-157 + Neo4j 实体实查 | HIGH |
| D3 | dev 侧 graphiti-canvas MCP（bolt:7689）已死 2 个月——CLAUDE.md 铁律"每轮 search_memory_facts"静默失效至今 | lsof 无监听 + 容器 Exited | MEDIUM |
| D4 | CI 主干连红后停摆一个月，近期全部修复只有单次手工 curl 证据，无绿色基线回归网 | gh run list | MEDIUM |
| D5 | Dashboard 指引文案教用户搜已被 S3 删除的命令；测试残渣节点混进平均值 | Dashboard.md 静态核对 | LOW |
| D6 | Claudian 订阅是检验白板域的无降级单点（订阅限额/CLI 变更/插件停更任一 = 整域熄火） | data.json 实查 | 登记在案 |

---

## 8 · 综合判定

**「基本功能先实现好」现在到什么程度？**

- **架构与管道层：约 80%** —— 窄链每一环的代码都是真的，昨日 T1-T6 后写读闭环、跨节点素材、错误候选消费端都通了。
- **用户实际体验层：被部署分裂清零** —— 你在用的是 6 月 11 日的插件 + 静默失败的 hook。修好 §2 之前，讨论其他都是纸面功夫。
- **质量与可信层：fragile** —— 检索"精确"未兑现（R1）、隔离铁律两处破口（R2/D2）、评分链一半死一半从未跑过（B1/F5）、唯一不可再生数据零备份（D1）。

**好消息**：P0 修复大多是小改动（一行到几十行），没有需要重写的架构级问题。

---

## 9 · 待你批注/拍板的问题

**Q1 · 部署统一方向（最急）**：
- **方案 A（推荐）**: 主仓 vault 原地升级——拷最新插件 build + 带鉴权的 settings.json + key 文件到主仓 vault，Obsidian 不用动；后端 CANVAS_BASE_PATH 切回主仓 vault 并重建索引。两副本内容差异需先 diff 合并（主仓多 CS188/CS189 文件）。
- 方案 B: Obsidian 改开 worktree vault（补 data.json backendUrl）——但 worktree 本质是开发区，学习数据住在开发区不健康。
- **User：**请你查询一下我们当时是在哪一个路径使用 claude code ，因为`canvas-learning-system/canvas-vault` 是作为我们当时测试使用 Canvas learning systeam 的仓库**

> **[A1 2026-07-12 → round1]** ✅ 已查证（与 §2 批注同题）：主仓 canvas-vault 是正统使用仓——这实质回答了 Q1 方向 = **方案 A 主仓原地升级**（插件/hook/key/skills 同步到主仓 + 后端挂载切回主仓 + 两副本内容以主仓为基底合并）。详见 [[R1-Q1_部署路径历史查证|📚 R1-Q1]] 的"这对 §9-Q1 意味着什么"节

**Q2 · enrich-hook auto-RAG 何去何从**（R1+R2 连锁）：
- 方案 A: 修分数归一化 + exam-prompt 跳过注入 + 保留 auto-RAG
- 方案 B（更彻底）: auto-RAG 降级为"仅 FTS 强命中才注入"（弱信号不注入，消灭无关材料污染）
- 方案 C: 暂时关闭 hook，检索改全手动（skill 调 MCP search_notes）
- **User：** enrich-hook auto-RAG 请你解释一下这个是什么功能设计出来是干什么的，

> **[A1 2026-07-12 → round1]** ✅ 它是你 5-09 提的需求「对话里相关知识点太频繁，不要每次按快捷键」的落地：你在 Claudian 每发一条消息，系统自动去笔记库搜相关片段悄悄塞给 Claude，让它答题时引用你的真实笔记（带 [[wikilink]] 跳转）而非凭训练数据编。现在的问题是过滤器坏了（垃圾也注入）+ 不分场合（出题轮把答案塞给出题人）。三方案通俗对比和我的推荐（先两个一行止血、保留机关）详见 [[R1-Q2_enrich-hook是什么|📚 R1-Q2]]

**Q3 · 评分主轨确认**：quiz-answer 本地 EMA 是事实上的唯一主轨（backend grade 分数被丢弃 + LLM 死）。确认"本地 EMA 为 v1 主轨、backend 评分链退役封存"？还是修 B1 后合流？
- **User：**
  请你解释一下

> **[A1 2026-07-12 → round1]** ✅ 已解释：系统并存两套互不知情的评分体系——后端大管道（评分 LLM 配置错误必 502 + 就算修好分数也被插件丢弃 = 半死）和 quiz-answer 本地 EMA（活的、为你当前工作流设计、但你还没真实跑过一次）。Q3 要拍的是：承认本地 EMA 为 v1 唯一主轨（推荐，零维护负担），还是花数天修活合流（当前不划算）。两轨来龙去脉详见 [[R1-Q3_评分双轨解释|📚 R1-Q3]]

**Q4 · Neo4j 数据迁移+备份**（D1）：需要停机几分钟做 dump + 把 bind-mount 迁出旧 worktree。现在做还是排到部署统一之后一起做？
- **User：**
部署后统一做

> **[A1 2026-07-12 → round1]** ✅ 收到拍板：**Neo4j 迁移+备份排在部署统一之后一起做**（与 R1-Q1 结论正好排成同一个部署窗口：切主仓挂载 + 索引重建 + Neo4j dump/迁移一次停机完成）。已记入决策。
**Q5 · P0 修复队列确认**（无异议我按此执行）：
1. Q1 拍板后执行部署统一
2. D1 Neo4j dump 备份（迁移可分离）
3. B1 litellm 前缀一行修（即便走 Q3 退役路线，出题模板退化也该修）
4. R2 hook 对 exam prompt 跳过注入（一行过滤救回隔离铁律）
5. D2 vault_backfill 复用黑名单 + 清理图内已泄漏实体
6. F3 quiz-answer clamp + calibration_log 定位插入（几行 python）
7. B2 tips 实时写落当前 vault 桶
8. R3 index_single_file 落黑名单检查 + 查询侧加 exam_board 排除（第二层防御）
- **User：**
