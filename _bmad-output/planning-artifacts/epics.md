---
stepsCompleted:
  - step-01-validate-prerequisites
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
---

# Canvas - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Canvas Learning System (Obsidian Hybrid), decomposing the 46 FRs + NFRs from the BMAD PRD and backend-relevant Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: 学习者可以启动 AI 对话，AI 通过 wikilink 图解析库解析 [[wikilinks]] 发现相邻概念，读取 frontmatter 和内容作为对话上下文
FR2: 系统可以在对话中基于个人历史误解主动提醒学习者
FR3: 学习者可以在对话回答中看到可点击的补充学习材料列表（LanceDB hybrid search）
FR4: 学习者可以选中两个概念之间的关系文本启动 EI+SE 双策略深度讨论
FR5: 系统可以在对话结束时自动归档会话到 Graphiti 长期记忆
FR6: 学习者可以启动完全空白的检验白板考察（信息隔离，看不到笔记原文）
FR7: 系统可以基于 BKT/FSRS 掌握度分数自动选出薄弱节点作为考察范围
FR8: 系统可以融合个人记忆（Graphiti）、知识图谱关系（Graphify）和掌握度数据（frontmatter）生成个人化题目
FR9: 学习者可以在 markdown 编辑器中手写答案并手动触发提交
FR10: 系统可以静默评分（学习者不感知评分过程），结果写入 frontmatter
FR11: 学习者可以在答不出时请求 4 级渐进提示（方向 → 关键词 → 框架 → 脚手架）
FR12: 学习者可以跳过题目且不受惩罚
FR13: 学习者可以基于笔记中的 callout 批注触发快速考察
FR14: 系统可以防止在检验白板内再次生成检验白板（防嵌套）
FR15: 学习者可以从对话或考察中提取新概念，自动创建 [[wikilink]] 双向链接的 .md 文件
FR16: 系统可以在考察中提取新概念时不中断当前流程（书签式，考后再深度讨论）
FR17: 系统可以通过 Graphify 从笔记文本中自动提取概念关系，生成独立 AI 检索索引 graph.json
FR18: 系统可以为 Graphify 提取的每个概念标注三级置信度（EXTRACTED / INFERRED / AMBIGUOUS）
FR19: 系统可以使用 BKT 模型实时更新每个概念的掌握概率
FR20: 系统可以使用 FSRS 算法计算最优复习间隔
FR21: 系统可以维护 5 信号融合的掌握度评估
FR22: 系统可以保证评分操作链的顺序完整性（不可跳步）
FR23: 系统可以记录学习者的错误并按 4 类分类存储（双写）
FR24: 系统可以记录学习者的自我评估校准数据
FR25: 学习者可以对 AI 评分投票反馈（准确 / 偏高 / 偏低）
FR26: 系统可以搜索学习者的历史记忆（3 层检索）
FR27: 系统可以异步非阻塞地将学习事件写入知识图谱
FR28: 学习者可以查看全局 Dashboard（Dataview 三层布局）
FR29: 系统可以使用处方性措辞展示学习状态
FR30: 学习者可以查看元认知 2x2 校准矩阵
FR31: 学习者可以从 Dashboard 一键启动检验白板
FR32: 学习者可以查看单个概念的详细档案
FR33: 系统可以在 Day 3 和 Day 7 主动提醒复习误解
FR34: 系统可以在复习时自动注入历史误解上下文
FR35: 系统可以基于历史误解生成辨析题
FR36: 学习者可以查看待复习任务列表
FR37: 学习者可以自定义所有 Skill 的 hotkey 绑定
FR38: 系统可以通过 Templater 模板自动生成标准 frontmatter
FR39: 学习者可以选择性启用 Obsidian Git 自动备份
FR40: 系统可以执行 Graphify health check
FR41: 系统可以在启动时检测 hotkey 冲突并警告
FR42: 系统必须将 context_enrichment 重构为 wikilink 图解析（Phase 1 必修）
FR43: 系统必须支持 wikilink 双向链接邻居发现
FR44: 系统可以在 Skill 结束时附加 Graphiti 操作摘要行
FR45: 系统可以在 vault 内维护 Graphiti 操作审计日志
FR46: 系统可以识别笔记中嵌入的图片并纳入 AI 对话上下文

### NonFunctional Requirements

NFR-PERF-1: LLM 出题/评分 < 5s for 95th percentile
NFR-PERF-2: Dataview Dashboard 刷新 < 1s
NFR-PERF-3: Graphify 全量索引 < 30s for ~100 文件
NFR-PERF-4: LanceDB 增量索引 < 500ms per file
NFR-PERF-5: wikilink 图构建 < 2s
NFR-PERF-6: wikilink 图遍历 < 200ms per N-hop query
NFR-PERF-7: Graphiti search < 3s
NFR-PERF-8: Graphiti 写入队列 < 10s per episode
NFR-INT-1: frontmatter 不可因 Skill 异常损坏
NFR-INT-2: Graphiti 写入原子性
NFR-INT-3: LLM API 只传筛选片段
NFR-INT-4: 全部数据本地存储
NFR-REL-1: Claudian 故障 → CLI 降级
NFR-REL-2: 14 MCP 工具全部可调用
NFR-REL-3: 操作链 5 步完整传递
NFR-REL-4: wikilink 图支持热更新
NFR-REL-5: Graphiti 读在 LLM 前写在操作后
NFR-REL-6: EventBus 级联自动触发 Graphiti 写入
NFR-DEG-1: Claudian 挂掉 → CLI 降级
NFR-DEG-2: Claude API 不可用 → 离线模式
NFR-DEG-3: Graphiti 不可用 → 默认先验出题
NFR-DEG-4: Graphify 失败 → 读 frontmatter + wikilinks
NFR-DEG-5: 检验白板隔离失败 → /quiz_from_callout 降级
NFR-DEG-6: Graphiti 写入失败 → 自动重试 3 次
NFR-OBS-1: Skill 末尾 Graphiti 摘要行
NFR-OBS-2: 状态栏指示灯
NFR-OBS-3: 审计日志全操作记录

### Additional Requirements

From Architecture (backend-relevant, Tauri frontend excluded):
- AR1: Docker 启动顺序：Neo4j → Ollama(bge-m3) → FastAPI → MCP 连接 → 就绪
- AR2: Hot-Warm-Cold 三层时间归档（0-30天/30天-6月/6月+）
- AR3: 4 类错误自动分类器差异化补救路由
- AR4: AutoSCORE 两阶段隐形评分（证据提取 → 4维4分制 × 3次采样多数投票）
- AR5: RAG 增量索引管道（content_hash去重 + 标题智能分块 + 面包屑前缀 + jieba中文）
- AR6: 检索后处理（reranker精排 + Adaptive-k + A-RAG迭代验证）
- AR7: 上下文压缩 15K→3K（句子级提取，公式/代码整块保护）
- AR8: LiteLLM 统一层 + 双层 Key 分离
- AR9: Token 成本追踪 + 按任务统计
- AR10: 离线降级 4 场景
- AR11: context_enrichment 重构为 wikilink 图遍历（与 FR42 对齐）

### FR Coverage Map

{{requirements_coverage_map}}

## Epic List

{{epics_list}}
