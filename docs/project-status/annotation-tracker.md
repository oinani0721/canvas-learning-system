# Gap Analysis 批注追踪清单

> 来源: docs/project-status/gap-analysis.md 用户批注 (2026-04-03)
> 总计: 108 条批注，分 5 类处理

---

## 第一类：BROKEN — 立刻修复（2 个）

| # | FR ID | 问题 | 根因假设 | 状态 |
|---|-------|------|---------|------|
| 1 | FR-EXAM-01 | 检验白板能生成但考察功能全部卡死 | Sidecar 未连接 / exam API 调用失败 | [ ] 待分析 |
| 2 | FR-CONV-06 | 对话错误提取完全不可见 | error_classifier 未被调用 / 提取结果未回传前端 | [ ] 待分析 |

## 第二类：DEAD_CODE — 简单修复（4 个）

| # | FR ID | 问题 | 根因假设 | 状态 |
|---|-------|------|---------|------|
| 3 | FR-EXAM-17 | 单节点考察入口是死代码 | LearningProfile 的启动考察按钮未接通 | [ ] 待验证 |
| 4 | FR-TRACE-01 | 学习档案面板死代码 | 组件挂载但 API 返回空 / 无数据时不渲染 | [ ] 待验证 |
| 5 | FR-RET-09 | 中文检索可能假实现 | jieba 未 import，bge-m3 内部处理不等于显式分词 | [ ] 待验证 |
| 6 | FR-CONV-04 | 对话框无命令可用 | SkillSelector 渲染条件未满足 / 技能文件不存在 | [ ] 待验证 |

## 第三类：NOT_VISIBLE — 等 Tauri 运行后统一验证（73 个）

**根因**: 前端-后端接线审计确认所有组件已正确挂载和 API 已接通，但需要 Tauri 桌面应用运行环境（非 vanilla Vite server）。

**处理方式**: 修好 Tauri 启动后，逐个验证以下 FR，通过的打勾，不通过的升级为 BROKEN。

### FR-KG
- [ ] FR-KG-04: 节点/连线自动同步后端
- [ ] FR-KG-05: 系统推荐概念关联
- [ ] FR-KG-06: 贴图多模态对话+异步 OCR
- [ ] FR-KG-07: 图片处理状态指示器
- [ ] FR-KG-08: 白板绑定笔记文件夹
- [ ] FR-KG-09: 粘贴图片功能

### FR-CONV
- [ ] FR-CONV-02: 节点独立对话历史跨 session 持久
- [ ] FR-CONV-03: 自动注入 1-hop 邻居学习上下文
- [ ] FR-CONV-07: 三层对话归档
- [ ] FR-CONV-09: 切换节点后台继续生成
- [ ] FR-CONV-10: Edge 语义检索前序节点摘要注入
- [ ] FR-CONV-11: 三层上下文窗口管理
- [ ] FR-CONV-12: /resume 切换对话 session

### FR-EDGE
- [ ] FR-EDGE-01: 连线显示可交互图标
- [ ] FR-EDGE-02: 点击图标触发 AI 对话
- [ ] FR-EDGE-04: EI+SE 双学习策略

### FR-EXAM
- [ ] FR-EXAM-02: FSRS+BKT 选择薄弱节点
- [ ] FR-EXAM-03: ACP 数据包出题
- [ ] FR-EXAM-04: 4 维评分
- [ ] FR-EXAM-05: 对话拖出新节点同步
- [ ] FR-EXAM-06: 递归考察
- [ ] FR-EXAM-07: 检验白板继承基础功能
- [ ] FR-EXAM-11: 三种考察模式
- [ ] FR-EXAM-12: 根据内容推荐模式
- [ ] FR-EXAM-13: 按白板类型定制出题
- [ ] FR-EXAM-15: 评分后准确性反馈
- [ ] FR-EXAM-16: 切换节点隐形评分
- [ ] FR-EXAM-18: 数据变更实时同步
- [ ] FR-EXAM-19: 4 级渐进提示
- [ ] FR-EXAM-20: 永久考察记录
- [ ] FR-EXAM-21: 检验白板不可再生成检验白板
- [ ] FR-EXAM-22: IRT 难度匹配

### FR-MAST
- [ ] FR-MAST-01: BKT+FSRS 精通度
- [ ] FR-MAST-03: 节点颜色精通度指示
- [ ] FR-MAST-04: FSRS 复习提醒
- [ ] FR-MAST-05: Area9 校准追踪
- [ ] FR-MAST-06: 5 信号融合

### FR-SKILL
- [ ] FR-SKILL-01: /命令列表+模糊搜索
- [ ] FR-SKILL-02: 预装学习辅助技能
- [ ] FR-SKILL-03: 用户注册新技能
- [ ] FR-SKILL-04: 技能执行注入学习历史
- [ ] FR-SKILL-05: 技能结果可拖出新节点

### FR-TRACE
- [ ] FR-TRACE-02: Tips 展示+源上下文
- [ ] FR-TRACE-03: 需要加强方向
- [ ] FR-TRACE-04: 关键问答精选
- [ ] FR-TRACE-05: 归档时自动提取

### FR-QA
- [ ] FR-QA-01: 忠实度检查
- [ ] FR-QA-02: Prompt 版本管理
- [ ] FR-QA-03: LLM 调用日志
- [ ] FR-QA-04: Token 消耗追踪
- [ ] FR-QA-05: Prompt 注入防护
- [ ] FR-QA-06: 出题难度匹配
- [ ] FR-QA-07: 结构化提取抽验

### FR-DASH
- [ ] FR-DASH-04: 查看历史检验白板

### FR-MCP
- [ ] FR-MCP-01: MCP 暴露核心算法工具
- [ ] FR-MCP-02: 防篡改顺序验证
- [ ] FR-MCP-03: 审计守护层

### FR-AGENT
- [ ] FR-AGENT-01: Agent Sidecar
- [ ] FR-AGENT-02: Per-node 独立 Session
- [ ] FR-AGENT-03: Agent 引擎可替换

### FR-SYS
- [ ] FR-SYS-01: 安装引导向导
- [ ] FR-SYS-02: LLM 供应商设置
- [ ] FR-SYS-03: 不同任务不同模型
- [ ] FR-SYS-04: 系统健康显示
- [ ] FR-SYS-05: 一键启动后端
- [ ] FR-SYS-06: 数据备份恢复
- [ ] FR-SYS-07: 多学科 KG 隔离
- [ ] FR-SYS-08: 切换 Agent 账号
- [ ] FR-SYS-09: /命令切换模型

## 第四类：NEEDS_RESEARCH — 在 Deep Research 中处理（25 个）

| # | FR ID | 用户问题摘要 | Deep Research 主题 |
|---|-------|------------|-------------------|
| 1 | FR-CONV-03 | 多节点上下文怎么处理 | 上下文压缩算法 |
| 2 | FR-CONV-10 | 这个功能到底要实现什么 | 对话继承设计 |
| 3 | FR-CONV-11 | 上下文窗口=上下文压缩？Claude Code 泄漏算法 | 上下文压缩算法 |
| 4 | FR-CONV-13 | 这个需求指什么 | 上下文压缩算法 |
| 5 | FR-MAST-02 | "考察更新"什么意思 | 精通度更新机制 |
| 6 | FR-MAST-06 | 5 维融合函数怎么设计，可信度？ | 信号融合算法 |
| 7 | FR-RET-01 | 指的是个人记忆系统吗 | 个人记忆 vs 笔记 RAG |
| 8 | FR-RET-02 | 检索什么，引用什么，笔记精确返回 | 个人记忆 vs 笔记 RAG |
| 9 | FR-RET-03 | 算法硬编码靠不靠谱，有 A/B 测试吗 | 评估框架 |
| 10 | FR-RET-04 | LangGraph 管道设计不靠谱 | 笔记 RAG 管道 |
| 11 | FR-RET-05 | 融合检索的是笔记还是记忆 | 个人记忆 vs 笔记 RAG |
| 12 | FR-RET-06 | 增量索引是否符合项目 | 笔记 RAG 管道 |
| 13 | FR-RET-08 | 涉及笔记 ARAG | 笔记 RAG 管道 |
| 14 | FR-RET-11 | 这个功能指什么 | 笔记 RAG 管道 |
| 15 | FR-RET-12 | 三种压缩+Claude Code 泄漏算法 | 上下文压缩算法 |
| 16 | FR-RET-13 | Obsidian 原生支持？前端需求？ | 双向链接设计 |
| 17 | FR-QA-01 | 前端算法靠谱吗 | 评估框架 |
| 18 | Tech #3 | AutoSCORE 未验证 | AutoSCORE 评分 |
| 19 | Tech #4 | Area9 校准未验证 | 校准追踪 |
| 20 | Tech #9 | RRF 融合测笔记还是记忆？ | 个人记忆 vs 笔记 RAG |
| 21 | Tech #10 | Agentic RAG 意义不明 | 个人记忆 vs 笔记 RAG |
| 22 | Tech #11/ACP | 3K token 为何这么小？组装逻辑？ | ACP 出题数据包 |
| 23 | Critical #1 | 个人记忆系统算法流程 | 个人记忆系统 |
| 24 | Critical #3 | 引入 Auto Research 量化迭代 | 评估框架 |
| 25 | Session Q3 | RAG 杂糅+Claude Code 梦记忆算法 | 上下文压缩算法 |

### Deep Research 主题聚合

| 主题 | 涉及批注数 | 对应算法子系统 |
|------|----------|--------------|
| 个人记忆 vs 笔记 RAG | 7 | #1 个人记忆 + #3 笔记 RAG |
| 上下文压缩算法 | 5 | #6 上下文压缩 |
| 笔记 RAG 管道 | 4 | #3 笔记 RAG |
| 评估框架 | 3 | 新增：Auto Research |
| 信号融合算法 | 1 | #2 信号融合 |
| ACP 出题数据包 | 1 | #7 ACP |
| 其他（功能定义澄清） | 4 | 需在 Deep Research 中澄清 |

## 第五类：TECH_UPDATE — 等 Deep Research 后决定（6 个）

| # | FR ID | Deep Research 推荐 | 当前实现 |
|---|-------|-------------------|---------|
| 1 | FR-EXAM-02 | 节点选择策略更新 | 硬编码 0.4/0.3/0.3 权重 |
| 2 | FR-EXAM-22 | 技术框架更新 | IRT 连续难度 |
| 3 | FR-MAST-01 | BKT 替代方案 | 标准 BKT 后验更新 |
| 4 | Tech #1 | BKT 技术更新 | 同上 |
| 5 | Tech #2 | FSRS 技术更新 | fsrs>=6.0.0 |
| 6 | Session Q3 | Claude Code 上下文压缩算法 | 未实现 |
