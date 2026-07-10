# PRD 对照全景盘点 · Graphiti 运行态 · 检索/Skill 对抗审查

> 你的四问:①已开发哪些/未开发哪些 ②Graphiti 后端是否已启动 ③精确返回笔记片段设计是否成熟 ④Skill 设计是否成熟。
> 方法:9 个并行 agent(6 deep-explore + 3 对抗验证),全部结论带 file:line 或真实命令输出。A1 从 PRD v5(7594 行)+ MVP 14 项 + gap-analysis(99 FR)+ 需求钉板提取 49 项需求;A2-A6 盘代码与运行态;V2 反向复核 13 条"缺失"声明全部成立;V3 完整性批判揪出 15 个盲区。⚠ 诚实声明:G-FAKE 正向猎手 agent 因网络故障 3 次重试后失败,其职责由 V2 反向复核 + 各 agent 交叉佐证 + 本月检验白板 v1.1 双重审查的实测补偿;标"未验证"处如实保留。
> **对每一条你都可以直接用 `**User：**` 批注。**

---

## 零 · 一句话总裁决

**系统有且只有一条端到端能用的主流**(建白板→派生→批注→检验白板→评分→Dashboard,全程可离线);**Graphiti 栈当前没有在跑**(约一周前关停,图里有真数据);**精确检索 = 能用有折扣的下限档**(新发现一个 CRITICAL 接线错误:索引源指向错误的 vault);**Skill 体系两极分化**(新一代考察闭环接近生产可用,2026-05 一代四个 skill 系统性腐化,需要收敛)。

---

## 一 · Graphiti 后端是否已启动?(你的第二问,先答)

**❌ 当前没有在跑,但不是死的——是"关机了的活系统"。**

| 检查项 | 真机结果 |
|---|---|
| Docker daemon | ❌ 离线(`docker.sock` 不存在,无 colima/orbstack 替代) |
| backend :8011 / Neo4j :7691/:7689 / graphiti-mcp :8765 | ❌ 全部拒连 |
| 宿主存活组件 | ✅ 仅 Ollama :11434(bge-m3 本地 embedder,恢复栈时唯一不用重启的依赖) |
| **图里有没有真数据** | ✅ **有**:Neo4j 数据 518MB,最后事务写入 **2026-07-07 00:11**(关停前一直在真实写入) |
| 写侧管道(批注→/tips→Graphiti,P0-P5) | ✅ 代码接线完整,outbox 全空无积压失败 |
| 读侧 | 双轨:后端出题链(exam/quick→QuestionGenerator→graphiti reader)有完整调用方但需栈在跑;检验白板 v1.1 **有意不读**(诚实裁决) |

**⚠ 三个必须知道的坑**:
1. **活跃 Neo4j 数据在 `feature-deeptutor-canvas-mvp` worktree 的 bind-mount 里**——如果你从**本 worktree** 起 `docker compose up`,会得到一张**空图**。恢复前先确认 compose 项目目录。
2. **写侧 group_id 契约裂缝(新发现)**:`memory_service.py:421,550` 写侧仍用 legacy `build_group_id`(subject 格式),不是 CLAUDE.md D16 要求的 `vault:*` 新格式——vault 格式目前只在 endpoints 层用。C-3 隔离契约在写侧真实不一致。
3. **MCP 双图分离**:你的 graphiti-canvas MCP(canvas-dev@7689,开发决策记忆)和后端学习数据(@7691)是**两个 Neo4j 实例、两套 group_id**——MCP 永远读不到学习数据,这是设计而非 bug,但要心里有数。

**恢复三步**:启动 Docker Desktop → 到正确的 compose 目录 `docker compose up -d` → 补跑 cypher 按 group_id 分组计数(本次因停机未能验证的唯一项)。

---

## 二 · 功能盘点矩阵(你的第一问:已开发 vs 未开发)

> 49 项需求 × 实现证据。✅ done / 🟡 partial / ❌ missing / ⛔ descoped(已裁决砍) / 💀 dead(代码在但无人调)。

### 原白板剖析(8 项:5✅ 2🟡→仅 1❌ 全缺)

| 需求 | 判定 | 关键证据 |
|---|---|---|
| ORIG-01 扁平架构(原白板/节点/一vault一学科) | ✅ | vault 真实结构 + config,Round-10 你拍板 |
| ORIG-02 建板(从零/从md派生) | ✅ | plugin v4 主路径 + skill fallback |
| ORIG-03 母本剖析流程 | 🟡 | 拉节点/批注/双链全通;"精确笔记片段"环节见 §三;AI 解题=study-question 仅路径 A 可用 |
| ORIG-04 派生节点+双链+关系callout | ✅ | Cmd+Shift+D 全本地,7 类关系双写 |
| ORIG-05 节点 AI 对话 | 🟡 | node-chat 剪贴板注入闭环通;session 双层记忆管理未做 |
| ORIG-06 Edge 对话 EI+SE 双策略(d=0.80-1.00) | ❌ | Hybrid 无任何落点;/tips/relation 只存关系不做对话(MVP#8 效应量第二大的设计,换轨后既没实现也没 descope 记录) |
| ORIG-07 批注系统(7 类 callout) | ✅ | Cmd+Shift+A + tips 后端同步 + frontmatter 镜像 |
| ORIG-08 图片多模态(贴图/OCR) | ❌ | plugin+skills 零 image/OCR 路径,仅 Tauri 时代残留 |

### 检验白板(13 项:7✅ 3🟡 3❌)——完成度最高的域

| 需求 | 判定 | 关键证据 |
|---|---|---|
| EXAM-01 生成+信息隔离+防嵌套+方案A | ✅ | v1.1 + 真机样本 + 双重对抗审查 |
| EXAM-02 批注驱动精确出题 | ✅ | v1.1(质量你说过"有待检验",长期观察) |
| EXAM-03 薄弱节点白板级选题 | ✅ | v1.1 Step3(本地 mastery,三变体兼容) |
| EXAM-04 md 编辑器答题(D14) | ✅ | sentinel 答题区 |
| EXAM-05 4 维评分+静默 | ✅ | v1.1 本地版(后端 AutoSCORE 链完整但休眠) |
| EXAM-06 三种考察模式 | ❌ | v1 单题闭环 |
| EXAM-07 4 级渐进提示 Chain-of-Hints | ❌ | **未裁决缺失**:v1.1 落地时静默砍掉,无 descope 决策记录(V3 盲区 5)→ 需要你拍板 |
| EXAM-08 跳过选项(不惩罚) | ❌ | 同上,未裁决缺失 |
| EXAM-09 考中拉节点书签式回链 | ✅ | v1.1 交付3(selected_node 重定向) |
| EXAM-10 新疑问归纳回原节点 | ✅ | v1.1 路径②(⚠ 归纳 callout 是纯文本非 `[[]]` wikilink,"点击疑惑跳转"差一行,盲区 13) |
| EXAM-11 校准+无计时 | 🟡 | 无计时=done-by-design;校准投票→理解自评+calibration_log 攒燃料替代 |
| EXAM-12 递归考察新节点 | 🟡 | v1.1"未剖析跳过"机制 = 剖析后自动可考(半实现) |
| EXAM-13 永久考察记录 | 🟡 | md 落盘天然永久;Dashboard 历史聚合未做 |

### 熟练度演化(7 项:2 done-by-design,其余全断/砍)——最诚实也最空的域

| 需求 | 判定 | 说明 |
|---|---|---|
| MAST-01 BKT+FSRS 5 信号融合 | ⛔ v1-descoped | B1-B4 四断点裁决,本地 EMA 占位(实际"5 信号"活的只有 2 个) |
| MAST-02 仅考察更新 | ✅ | v1.1 本地链正是如此(只有 /quiz-answer 写 mastery_score) |
| MAST-03 FSRS 复习提醒 | ❌ | 调度三环全断:数据源读 .canvas 旧格式/写回零调用/展示只有 Notice 计数 |
| MAST-04 元认知校准矩阵 | ❌ | v1 只攒 calibration_log 燃料 |
| MAST-05 节点切换隐形评分 | ❌ | 无落点 |
| MAST-06 IRT 难度匹配 | ⛔ | 已裁决砍(epic-4/4-11 DEPRECATED) |
| MAST-07 颜色=个人标记 | ✅ done-by-design | 你的裁决推翻自动着色 |

### 个人记忆 Graphiti(6 项:写侧通、读侧断是主旋律)

| 需求 | 判定 | 说明 |
|---|---|---|
| MEM-01 真 Graphiti 记忆系统 | 🟡 | 写侧 P0-P5+belief 链完整;⚠ group_id legacy 混写;栈停机 |
| MEM-02 强制写入+兜底 | 🟡 | outbox 重放(P2)+诚实失败(A7)已做;hook 强制层未做 |
| MEM-03 错误提取分类闭环 | 🟡→断 | 写侧+展示侧活,**用户确认(accept/dispute)命令从未注册**——backend 端点、plugin payload builder 两头都在,中间断(经典 G-PIPE,候选只能积压 30 天过期) |
| MEM-04 对话蒸馏 Hot-Warm-Cold | ❌ | Hybrid 无落点(蒸馏器是 Tauri 组件) |
| MEM-05 跨节点记忆共享→针对性考察 | ❌ 读侧断 | **你的 S2-2 核心认知"写通读断"**:P0-P5 修好的记忆脊柱在消费端零兑现——v1.1 出题素材永远只有本节点(5-ge-5 facade 未接) |
| MEM-06 vault group_id 隔离 | 🟡 | endpoints 层 vault:* ✓;memory_service 写侧 legacy ✗(见 §一坑2) |

### 精确检索 RAG(7 项)→ 详见 §三

RAG-01 🟡下限档 · RAG-02 ❌(0/5 融合 bug 两月未修) · RAG-03 ✅(bge-m3 单路真实) · RAG-04 🟡(**CRITICAL 接线错误见 §三**) · RAG-05 ❌(无自动增量,纯手动端点且 plugin 零触发) · RAG-06 ❌(jieba 未集成,你怀疑的"假实现"成立) · RAG-07 ❌(上下文压缩无落点)

### Dashboard(3 项:全 🟡)

DASH-01 🟡(列表/按钮活,考察历史聚合缺) · DASH-02 🟡(疑问回链✓,正向跳转差 wikilink,Profile 死代码) · DASH-03 ❌(模型管理面板;后端 embedder 已可切换=partial)

### 基础设施(5 项)

INFRA-01 ✅(Claudian+8 skills 订阅制) · INFRA-02 ❌(命令完整迁移未做) · INFRA-03 ✅超配(PRD 要 6 个 skill,实有 8,缺 review_profile 对应物) · INFRA-04 🟡(19 MCP 工具定义齐,熟练度链 v1 绕开) · INFRA-05 未判(主观判据需转可测代理)

### 💀 死代码/名实不符清单(点了就坑你的)

| 位置 | 问题 |
|---|---|
| plugin `canvas:start-dialog` | 调**不存在**的 /agents/dialog → 必 404 |
| plugin `canvas:extract-concept` | 选中文本被静默丢弃,实际触发**整库 wikilink 重建** |
| plugin `canvas:quiz-from-callout` | 纯别名,零批注逻辑,还走已弃旧链 |
| plugin `canvas:start-examination`(命令面板) | 仍直调断裂的 /exam/start(Dashboard 按钮已修,命令面板漏了——部分修复) |
| 后端 10+ router(mastery/memory/rag/subjects/kg_health/exam_sessions/ws…) | Hybrid 零消费者,死挂载 |
| G-FAKE-006 CONNECTS_TO 死写 | 4 月排期删除至今仍有 2 处运行时调用 |

---

## 三 · 精确返回笔记片段:成熟吗?(你的第三问,对抗审查)

**裁决:能用有折扣——下限档。代码链全部真实非 G-FAKE(7-01 有真机片段实证),但当前实际状态接近"纸面":**

### 🔴 CRITICAL 新发现(7-01 钉板没抓到的)

**索引源 vault 接错线**:`.env:17` 的 `VAULTS_ROOT` 指向**主 repo** 的 canvas-vault,而你 7 月以来的全部活跃学习数据(检验白板 v1.1 产物、Fundamentals、新 skill)在 **worktree** 的另一个已分叉 vault 里(两 vault inode 不同、内容双向分叉:主 repo vault 检验白板/为空、节点停在 6-12)。**即使今天重建索引,RAG 也永远扫不到你正在学习的 vault——且失败是静默的**(检索照样返回旧内容,看起来"能用")。

### 其余折扣(7-01 的 3 个折扣今天全部还在,且加深)

1. **后端停机约一周** → hook 注入/full-RAG/MCP search_notes 三路全不可用,只剩 native Grep;hook 这一周每次提问都在**静默空转**(无告警)。
2. **"Channel health 0/5" 5 路融合 bug 未修**:2026-05-11 标记至今**零修复 commit**(state_graph.py 停在 4-07),生产永远是裸 LanceDB 单路兜底。
3. **索引停在 2026-05-03**:6 月 CS188、7 月检验白板内容全部检索盲区;无自动增量(手动端点 only,且 study-question skill 教你的重建路径 `/api/v1/metadata/index/vault` 是**错的**——实际挂在 `/canvas-meta`,照做必 404)。
4. **设计张力(前瞻)**:索引黑名单不含 `检验白板/`,doc_type 过滤不排 exam_board——索引一旦重建,**考题会回流进学习对话**(信息隔离被 RAG 击穿)。现在没触发只是因为索引停更。

**恢复"能用"最少三动作**:修 VAULTS_ROOT 指向 worktree → 起后端 → 重建索引(顺手把 检验白板/ 加入排除)。

---

## 四 · Skill 设计成熟吗?(你的第四问,对抗审查)

**裁决:两极分化,需要收敛。**

### ✅ 成熟的一极(可作全体范本)
**新一代考察闭环**(ai-linked-doc → start-exam-board → quiz-answer → Dashboard):批注 3-pattern 三处逐字一致、board_stem 契约三方咬合、占位检测串与 plugin 模板逐字匹配、两阶段提交+event_id 幂等+JSON 防注入+变体归一化+诚实声明——审查原话:"证明团队具备写出高一致性 skill 契约的能力,问题不是能力而是旧 skill 无人回头收敛"。

### ❌ 腐化的一极(2026-05 一代:chat-with-context / study-question / exam-quick / node-chat)

| # | 系统性问题 | 要害 |
|---|---|---|
| 1 | **3 个 skill 的"路径 B(plugin 注入)"是虚构的**:Cmd+Shift+E/`<rag_context>`/`<exam_context>`/Cmd+P 解题深度在 plugin 全仓 **0 命中** | chat-with-context 12 条 HARD 里 9 条围绕永远不会到达的输入形态设计 |
| 2 | **vault CLAUDE.md 还在教旧架构**(wiki/concepts/、outputs/exam_boards/) | 每个 session 自动加载,随时可能把新文件写回幽灵目录——单点最高破坏源 |
| 3 | **CS188 硬编码**:HARD-17 强制 Grep `raw/CS188/videos/lectures/`(本 vault 不存在),"2594 chunks"快照固化进通用契约 | 强制约束数学上不可满足 → 逼 skill halt 或幻觉 |
| 4 | **exam-quick 答完三条出路全死**:Cmd+Shift+G 不存在/question_id 必 404/`检验/` 目录名错 | fallback 题的答案是纯死数据 |
| 5 | **mastery 契约漂移**:字段三名并存、study-question 只认 `mastery`(会把全部节点标"未评估")、阈值两套、§7 还教你手改 mastery(与 EMA 所有权冲突) | |
| 6 | **native Grep 自救前缀写错**:`canvas-vault/**/*.md` 在 vault 为 cwd 时永远 0 命中 → "比 MCP 快 2-3 倍"的卖点静默失效,每次都回落 MCP | |
| 7 | **8 处还说"检验白板(未来 Story 6)"**——灵魂功能已上线,4 个对话 skill 却把用户往回带 | |
| 8 | **三套考察系统并存**(plugin quick exam 写 节点/考察-*.md 污染概念池 / exam-quick 不落盘 / 检验白板),"我的考察记录在哪"没有单一答案 | |

---

## 五 · V3 完整性批判的三个 CRITICAL 盲区(对我们自己文档体系的)

1. **MVP 14 项没有任何 Hybrid 时代判定文档**——mvp-plan.md 是 3-24 Tauri 产物,全部证据(App.tsx/sidecar)已作废,承诺的 Hybrid 版重写从未发生。本报告 §二 是第一份 Hybrid 判定矩阵,建议以此为准落盘。
2. **唯一全景盘点(5-27)双向失真**:批注管道已被 P0-P5 修好但仍记"全断";检验白板 v1.1 零覆盖。
3. **"精确笔记片段"此前在所有盘点里零判定**(连 missing 都没人写)——本报告 §三 补上。

---

## 六 · 修复优先级建议(供你批注排期)

**P0(点了就坑你/学习数据正确性)**
1. 修 `.env` VAULTS_ROOT → worktree vault + 重建索引 + 排除 检验白板/(§三 CRITICAL)
2. 重写 vault CLAUDE.md 为扁平架构 + 删 wiki//outputs/ 幽灵目录
3. 清理 4 条死/误导 plugin 命令(start-dialog/extract-concept/quiz-from-callout/命令面板 start-examination 对齐剪贴板引导)

**P1(体验断裂/契约收敛)**
4. 旧一代 4 skill 收敛(虚构路径B降级为规划/CS188 参数化/mastery 统一 mastery_score+阈值/8 处"未来 Story 6"改现状/Grep 前缀修正)——以新一代为范本
5. 错误候选 accept/dispute 命令接线(builder 已就绪只差注册)
6. quiz-answer 归纳 callout 加 `[[检验白板/…]]` wikilink(你的"点击疑惑跳转"差这一行)
7. EXAM-07/08(渐进提示/跳过)要不要进 v1.1.x——**未裁决缺失,请你拍板**

**P2(v2 主题)**
8. Graphiti 读侧接通(5-ge-5 facade → 出题消费"带原因增殖图")= 你 S2-2 的针对性考察燃料
9. memory_service 写侧 group_id 迁移 vault:*
10. 0/5 融合修复或正式裁决接受单路 + FSRS 调度闭环

---

## 附 · 审计可信度

- 9 agents / 335 次工具调用 / 92 万 tokens;A2-A6 全部要求 file:line 级证据;V2 反向复核 13 条缺失声明 **全部成立,零误报**(仅 3 处表述微调)。
- 已知缺口:G-FAKE 正向猎手失败(补偿:V2+交叉佐证+本月实测);Neo4j group_id 分组计数因停机未验证;A6-7(Grep 前缀)标注为强推断未运行时实测。

**User：我的最终目标是要可以一键实现在不同 vault 上一键部署使用 Canvas learning systeam ，然后各个 vault 之间的数据也不会冲突，请你在此基础上给我思考接下来的开发计划，如何收敛清理过时的设计，最后开发符合我学习需求的原白板和检验白板的使用过程**