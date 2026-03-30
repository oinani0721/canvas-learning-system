---
name: S27 GDA 全量决策汇总（10项 + 路径A + 设计文档）
description: S27 Superpowers首次测试：路径A确认+16×2轮GDA审计+10项用户批注决策+设计文档Draft完成（2026-03-25）
type: project
---

## S27 Session 全量产出（2026-03-25）

### 路径选择
- **路径 A 确认**：先打通管道再打磨体验（Phase1启动→Phase2 Graphiti→Phase3管道→Phase4 UI）

### 10 项 GDA 决策（全部用户确认）

| # | 决策 | 内容 |
|---|------|------|
| GDA-1 | Neo4j用7691 | Docker容器Neo4j，7688旧实例弃用 |
| GDA-2 | 取消教材+跨Canvas | RAG 6路→4路 |
| GDA-3 | group_id按白板名 | CS188→cs188，白板命名决定检索范围 |
| GDA-4 | prompt禁硬编码 | 5层prompt必须外部文件+成熟案例+用户试用 |
| GDA-5 | 移除CognitiveLoadTimer | 计时功能已抛弃 |
| GDA-6 | Profile优先级 | 跳转最高→疑惑节点→记录/历史延后 |
| GDA-7 | LLM管理放Phase4 | Settings已有基础，Phase4补Dashboard面板 |
| GDA-8 | 评分Bug Phase1修 | 前端×2.5溢出+后端1分变100分 |
| GDA-9 | 考察中/命令可用 | AI引导思考但不暴露答案（Layer4规则） |
| GDA-10 | 疑问节点=正常对话 | 检验白板拉出的新节点进正常对话模式，下次可被考察 |

### 关键产出文件
- 设计文档：`docs/superpowers/specs/2026-03-25-path-a-pipeline-design.md`（DRAFT）
- GDA审计：`_decisions/gda-s27-pipeline-audit.md`
- 决策索引：`_decisions/decision-log.md`（S27-GDA-1~10 条目）

### 待调研项（下个session）
1. Claudian /命令列表
2. Obsidian精确段落跳转
3. PostToolUse hook BEA提取参考案例
4. SDK systemPrompt vs CLAUDE.md 的关系

### GDA2 发现的A类遗漏（需补充到设计文档）
- DE-5 CSP配置、GDR-P0-1事件传输、P0-2状态机、P0-4 SDK版本、评分Bug、补救策略消费

### Phase 1 执行结果（2026-03-26）
- Commits: f20c225(端口) + 5bad2d3(移除Timer) + 1b21584(评分Bug) + 6e478b7(milestone)
- 验证: 基础功能7/7 UI通过，数据管道待Phase2/3
- 发现: /命令无技能文件(P3)、Exam显示旧数据(P3)、Dashboard数据空(P2/3)、Tips详情不显示(P3)
- 启动命令修正: 从项目根目录运行`npm run tauri dev`（非frontend/）

**Why:** S27是Superpowers首次集成测试，通过brainstorming+GDA工作流系统梳理了项目全貌和开发方案
**How to apply:** 下个session：Phase 2 Writing Plans（Graphiti真实接入，9-13h最复杂阶段）
