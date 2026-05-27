- FR-CONV-05: 学习者可以在对话中通过 callout 批注标记关键知识点（Tips）
- FR-CONV-06: 系统自动从对话中提取、分类并归档学习者的错误（4 主类 + 2 子类）
- FR-CONV-07: 系统可以在对话结束时自动归档会话到长期记忆
- FR-CONV-08: 学习者可以从对话中选取内容提取为新的知识节点
- FR-CONV-09: 对话消息按时间进行三层归档
- FR-CONV-10: 系统可以通过 Edge 语义检索相关前序笔记讨论摘要
- FR-CONV-11: 系统可以在上下文压缩时保留关键学习数据并通知学习者

**FR-EDGE (Edge 对话) — 4 FRs**
- FR-EDGE-01: 学习者可以选中两个概念之间的关系启动深度讨论
- FR-EDGE-02: 系统在 Edge 讨论中同时激活 EI 和 SE 两种学习策略
- FR-EDGE-03: 系统记录学习者对关系的解释理由，存储为结构化语义标签
- FR-EDGE-04: Edge 讨论自动注入两端概念的掌握度和历史记忆

**FR-EXAM (考察与评估) — 22 FRs**
- FR-EXAM-01: 学习者可以生成完全空白的检验白板考察（信息隔离）
- FR-EXAM-02: 系统基于 BKT/FSRS 自动选出薄弱节点
- FR-EXAM-03: 系统融合三路数据生成个人化题目
- FR-EXAM-04: 系统对回答进行 4 维 4 分制评分
- FR-EXAM-05: 学习者在 md 编辑器中手写答案并手动提交（D14 锁定）
- FR-EXAM-06: 系统静默评分，结果更新掌握度
- FR-EXAM-07: 4 级渐进提示（方向→关键词→框架→脚手架）
- FR-EXAM-08: 跳过题目且不受惩罚
- FR-EXAM-09: 基于 callout 批注触发快速考察
- FR-EXAM-10: 防止在检验白板内再次生成检验白板
- FR-EXAM-11: 三种考察模式
- FR-EXAM-12: 系统根据内容类型推荐考察模式
- FR-EXAM-13: 按白板类型定制出题策略
- FR-EXAM-14: 考中书签式概念提取
- FR-EXAM-15: 考后校准投票
- FR-EXAM-16: 节点切换时自动后台评分
- FR-EXAM-17: 数据变更同步回源白板
- FR-EXAM-18: 考察记录永久保存
- FR-EXAM-19: IRT 连续难度匹配 ≥ 70%
- FR-EXAM-20: 确认的新节点可继续讨论
- FR-EXAM-21: 不限数量的检验白板
- FR-EXAM-22: 三重信息隔离保证
| FR-EDGE-01 | 6 | 6.1 | Edge 讨论触发 |
| FR-EDGE-02 | 6 | 6.2 | EI+SE 双策略 |
| FR-EDGE-03 | 6 | 6.3 | 语义标签存储 |
| FR-EDGE-04 | 6 | 6.1 | Edge 上下文注入 |
| FR-EXAM-01 | 4 | 4.1 | 空白检验白板 |
| FR-EXAM-02 | 4 | 4.2 | 薄弱节点选题 |
| FR-EXAM-03 | 4 | 4.3 | 三路融合出题 |
| FR-EXAM-04 | 4 | 4.6 | 4D4 分评分 |
| FR-EXAM-05 | 4 | 4.5 | MD 答题提交 |
| FR-EXAM-06 | 4 | 4.6 | 静默评分 |
| FR-EXAM-07 | 4 | 4.7 | 渐进提示 |
| FR-EXAM-08 | 4 | 4.7 | 跳过不惩罚 |
| FR-EXAM-09 | 4 | 4.11 | Callout 考察 |
| FR-EXAM-10 | 4 | 4.1 | 防嵌套 |
| FR-EXAM-11 | 4 | 4.4 | 三种考察模式 |
| FR-EXAM-12 | 4 | 4.4 | 模式推荐 |
| FR-EXAM-13 | 4 | 4.3 | 出题策略定制 |
| FR-EXAM-14 | 4 | 4.8 | 书签式提取 |
| FR-EXAM-15 | 4 | 4.9 | 校准投票 |
| FR-EXAM-16 | 4 | 4.6 | 隐形评分 |
| FR-EXAM-17 | 4 | 4.9 | 数据同步回源 |
| FR-EXAM-18 | 4 | 4.10 | 永久记录 |
| FR-EXAM-19 | 4 | 4.11 | IRT 难度匹配 |
| FR-EXAM-20 | 4 | 4.8 | 新节点继续讨论 |
| FR-EXAM-21 | 4 | 4.10 | 不限数量白板 |
| FR-EXAM-22 | 4 | 4.1 | 三重隔离保证 |
| FR-KG-01 | 3 | 3.1 | Wikilink 关系 |
| FR-KG-02 | 3 | 3.1 | 概念提取创建 |
| FR-KG-03 | 3 | 3.2 | Graphify 提取 |
| FR-KG-04 | 3 | 3.4 | 书签式考中提取 |
| FR-KG-05 | 3 | 3.2 | 三级置信度 |
| FR-KG-06 | 3 | 3.3 | frontmatter 关系记录 |
| FR-KG-07 | 3 | 3.3 | 71x 压缩检索 |
| FR-KG-08 | 3 | 3.5 | KG 健康检查 |
| FR-KG-09 | 3 | 3.5 | 图片入图 |
| FR-MAST-01 | 5 | 5.1 | BKT 更新 |
| FR-MAST-02 | 5 | 5.2 | FSRS 间隔 |
| FR-MAST-03 | 5 | 5.3 | 5 信号融合 |
| FR-MAST-04 | 5 | 5.4 | 评分链完整性 |
| FR-MAST-05 | 8 | 8.3 | 2x2 校准矩阵 |
| FR-MAST-06 | 5 | 5.3 | 仅考察更新 |
| FR-MEM-01 | 5 | 5.5 | 错误双写 |
| FR-MEM-02 | 5 | 5.6 | 校准数据 |
| FR-MEM-03 | 5 | 5.6 | 评分投票 |
| FR-MEM-04 | 5 | 5.7 | 3 层检索 |
| FR-MEM-05 | 5 | 5.8 | 异步写入 |
| FR-MEM-06 | 5 | 5.8 | Hot/Warm/Cold |
| FR-VIZ-01 | 8 | 8.1 | Dashboard 三层 |
| FR-VIZ-02 | 8 | 8.2 | 处方性措辞 |
| FR-VIZ-03 | 8 | 8.3 | 2x2 矩阵视图 |
| FR-VIZ-04 | 8 | 8.4 | 一键考察 |
| FR-VIZ-05 | 8 | 8.4 | 概念档案 |
| FR-VIZ-06 | 8 | 8.2 | 正面措辞 |
| FR-SPACE-01 | 7 | 7.2 | NextReview+Bases 提醒 |
| FR-SPACE-02 | 7 | 7.3 | 误解注入 |
| FR-SPACE-03 | 7 | 7.4 | 辨析题 |
| FR-SPACE-04 | 7 | 7.1 | 任务列表 |
| FR-SPACE-05 | 7 | 7.2 | FSRS 时机 |
| FR-SYS-01 | 1 | 1.1 | Templater 模板 |
| FR-SYS-02 | 1 | 1.4 | Hotkey 绑定 |
| FR-SYS-03 | 1 | 1.6 | Git 备份 |
| FR-SYS-04 | 1 | 1.5 | Hotkey 冲突 |
| FR-SYS-05 | 1 | 1.6 | KG 健康检查 |
| FR-SYS-06 | 1 | 1.1 | 安装引导 |
| FR-ADAPT-01 | 1 | 1.2 | 图遍历邻居 |
| FR-ADAPT-02 | 1 | 1.3 | 图上下文组装 |
| FR-ADAPT-03 | 1 | 1.2 | 图热更新 |
| FR-OBS-01 | 8 | 8.5 | 记忆摘要行 |
| FR-OBS-02 | 8 | 8.6 | 连接状态 |
| FR-OBS-03 | 8 | 8.7 | 审计日志 |
| FR-OBS-04 | 8 | 8.6 | 写入失败通知 |
| FR-MM-01 | 2 | 2.8 | 图片识别对话 |
| FR-MM-02 | 2 | 2.8 | 图片 AI 讨论 |
| FR-MM-03 | 9 | 9.1 | 图片考察素材 |

**Coverage: 85/85 FRs mapped (100%)**

---

## Epic List

| Epic | 名称 | Phase | 旅程 | FR 数 | Story 数 |
|------|------|-------|------|-------|---------|
| 1 | 学习环境搭建与冷启动 | 1 | 4 | 9 | 6 |
| 2 | 智能学习对话 | 1 | 1,5 | 13 | 8 |
| 3 | 知识图谱构建 | 1-2 | 1 | 9 | 5 |
| 4 | 检验白板 Active Recall（灵魂） | 1 | 2 | 22 | 11 |
| 5 | 掌握度追踪与记忆管理 | 1-2 | 2,3 | 12 | 8 |
| 6 | Edge 对话与深度剖析 | 2 | 1 | 4 | 3 |
| 7 | 错误修正与间隔复习 | 2 | 3 | 5 | 4 |
| 8 | 学习 Dashboard 与可观测性 | 2 | 6 | 10 | 7 |
| 9 | 多模态增强与持续改进 | 3 | 5 | 1 | 2 |

---

## Epic 1: 学习环境搭建与冷启动
## Epic 4: 检验白板 Active Recall — 灵魂 Epic

学习者可以在完全空白的检验白板中接受个人化考察。系统通过三路融合出题，支持 md 编辑器手写答案、静默评分、4 级渐进提示、跳过不惩罚、书签式概念提取和防嵌套保护。这是产品灵魂——Karpicke 2011 Retrieval Practice d=1.50 的 100% 等价实现。

**FRs:** FR-EXAM-01~22 (全部 22 条)
**NFRs:** NFR-PERF (LLM < 5s), NFR-INT (frontmatter 安全, 评分链), NFR-REL (评分链 5 步, 级联触发), NFR-DEG (隔离失败 → callout 降级), NFR-MAINT (Prompt 回归)
**Depends on:** Epic 1 (模板), Epic 2 (对话基础), Epic 3 (KG 出题素材)
**Phase:** 1 MVP · 旅程 2（灵魂旅程，95% 守恒）

### Story 4.1: 信息隔离 + 防嵌套

As a 学习者,
I want 检验白板打开时完全看不到笔记原文,
So that 我在纯 Active Recall 环境中学习。

**Acceptance Criteria:**

**Given** 学习者启动检验白板
**When** exam_boards/*.md 打开
**Then** 零 wiki/concepts/ 内容泄漏（三重保证：type 标记 + AI 上下文重置 + Skill prompt 约束 · FR-EXAM-22）
**And** 已在检验白板内时禁止再次生成检验白板（FR-EXAM-10）
**And** 防嵌套检查先于所有其他操作

### Story 4.2: 薄弱节点选题

As a 系统,
I want 基于 BKT/FSRS 掌握度自动选出薄弱节点,
So that 考察聚焦学习者最需要强化的知识。

**Acceptance Criteria:**

**Given** 学习者启动考察
**When** 系统查询掌握度数据
**Then** 选出掌握度最低的 N 个节点作为考察范围
**And** 选题结果排除已完全掌握（≥ 0.90）的节点

### Story 4.3: 三路融合出题 + 出题策略

As a 系统,
I want 融合三路数据生成个人化题目,
So that 考察精准针对学习者的薄弱点。

**Acceptance Criteria:**

**Given** 选定考察节点
**When** 系统生成题目
**Then** 融合个人记忆（Graphiti）+ 知识图谱关系（Graphify）+ 掌握度数据（frontmatter）
**And** 知识点白板侧重定义辨析，题目白板侧重易错点和破题方法（FR-EXAM-13）
**And** LLM 出题 < 5s P95（NFR-PERF）

### Story 4.4: 考察模式选择

As a 学习者,
I want 选择考察模式或接受系统推荐,
So that 考察方式匹配我的学习需求。

**Acceptance Criteria:**

**Given** 学习者启动考察
**When** 进入模式选择
**Then** 提供三种模式：点对点突破 · 综合题考察 · 混合模式
**And** 系统根据白板内容类型推荐模式（可覆盖）

### Story 4.5: MD 编辑器答题 + 提交

As a 学习者,
I want 在 markdown 编辑器中手写答案并手动提交,
So that 答题过程就像写批注（D14 用户哲学选择）。

**Acceptance Criteria:**

**Given** 系统出题完毕
**When** 学习者在 md 编辑器中写完答案
**Then** 手动触发提交（非自动检测）
**And** 答案永久保存在 exam_boards/*.md 中
**And** AI 侧边栏不显示题目/分数/提示等实质学习内容

### Story 4.6: 静默评分 + AutoSCORE

As a 系统,
I want 对学习者的回答静默评分,
So that 评分过程不打断学习 Flow。

**Acceptance Criteria:**

**Given** 学习者提交答案
**When** 系统触发评分
**Then** 执行 AutoSCORE 两阶段评分（证据提取→4维4分制 · AR4）
**And** 学习者不感知评分过程
**And** 结果更新 frontmatter 掌握度数据
**And** 节点切换时自动触发后台评分（FR-EXAM-16）

### Story 4.7: 4 级渐进提示 + 跳过不惩罚

As a 学习者,
I want 答不出时请求渐进提示或跳过,
So that 我既能获得帮助又不被迫回答。

**Acceptance Criteria:**

**Given** 学习者答不出题目
**When** 请求提示
**Then** 提供 4 级渐进提示：方向→关键词→框架→脚手架
**And** 每次点击升一级
**And** 不提供"直接告诉答案"选项

**Given** 学习者选择跳过
**When** 跳过题目
**Then** 标记为未作答，不惩罚 BKT/FSRS

### Story 4.8: 考中书签式概念提取

As a 学习者,
I want 考察中发现新概念时不中断考察,
So that Active Recall 不被打断。

**Acceptance Criteria:**

**Given** 考察中学习者发现不懂的概念
**When** 触发提取
**Then** 插入 `[!discussion_later]+` 书签，不切 Tab
**And** 确认的新节点可继续深入讨论（FR-EXAM-20）
**And** 考后可通过书签回到待讨论概念

### Story 4.9: 校准投票 + 数据同步

As a 学习者,
I want 考后对 AI 评分投票反馈并同步数据到源白板,
So that AI 评分越来越准确。
## Epic 6: Edge 对话与深度剖析

学习者可以选中两个概念之间的关系启动 EI+SE 双策略深度讨论，记录结构化的语义标签。

**FRs:** FR-EDGE-01~04
**NFRs:** NFR-PERF (LLM < 5s)
**Depends on:** Epic 2 (对话基础), Epic 3 (KG Edge 文件)
**Phase:** 2 · 旅程 1（深度剖析）

### Story 6.1: 关系讨论触发 + 上下文

As a 学习者,
I want 选中两个概念间的关系启动深度讨论,
So that 我能理解概念间的连接。

**Acceptance Criteria:**

**Given** 学习者选中两个概念间的关系（通过 frontmatter relationships[]）
**When** 触发 `/edge_discuss`
**Then** 自动注入两端概念的掌握度和历史记忆（从 frontmatter 读取）
**And** AI 询问学习者为何认为这两个概念相关

### Story 6.2: EI+SE 双策略激活

As a 系统,
I want 在 Edge 讨论中同时激活 EI 和 SE 策略,
So that 学习者同时练习精细化追问和自我解释。

**Acceptance Criteria:**

**Given** Edge 讨论进行中
**When** AI 引导讨论
**Then** 同时激活 Elaborative Interrogation（追问"为什么"）和 Self-Explanation（要求解释）
**And** 两种策略自然交替，不生硬

### Story 6.3: 语义标签存储

As a 系统,
I want 记录学习者对关系的解释并存储为结构化标签,
So that 关系解释可被后续检索使用。

**Acceptance Criteria:**

**Given** 关系讨论结束
**When** 系统存储结果
**Then** 解释理由存储为结构化语义标签（概念文件 frontmatter relationships[] 更新）
**And** 语义标签可被 Graphiti 和图遍历检索

---

