---
name: S27 GDA审计批量决策（4项用户批注确认）
description: 用户在gda-s27-pipeline-audit.md批注确认：Neo4j用7691、取消教材/跨Canvas检索、group_id按白板命名、prompt禁止硬编码（2026-03-25）
type: project
---

## [Decision] S27 GDA 审计 — 用户批注确认 4 项决策

Session: S27 | 日期: 2026-03-25

### 1. Neo4j 端口：用 7691（Docker 内）
- 用户确认 canvas-learning-system docker 容器的 Neo4j（7691）才是正确的
- Phase 0 需改 .env: `NEO4J_URI=bolt://localhost:7691`
- 7688 是外部 CS188 旧实例，不再使用

### 2. 取消教材检索 + 跨 Canvas 检索
- 用户明确说"这两个功能先取消"
- RAG 管道从 6 路缩减为 4 路（LanceDB + Vault + Graphiti + Multimodal）
- 符合 DD-10 防功能蔓延

### 3. group_id 按白板命名
- 用户说"前端可以给白板命名以及索引学科的笔记路径，请按我的命名来"
- group_id 直接使用用户给白板起的名字（如白板叫"CS188" → group_id="cs188"）
- 前端白板命名 + 笔记路径选择决定 Graphiti group_id 和检索范围

### 4. 检验白板 prompt 禁止硬编码
- 用户明确："提示词层面的东西绝对不能硬编码"
- 必须参考高质量成熟案例（DD-04）
- 写成外部文件（backend/prompts/exam/layer*.md）
- 用户需要实际试用后确认是否合适

**Why:** 用户在 GDA 审计报告上直接批注确认，Boris Tane 模式
**How to apply:** Phase 0 改端口 + Phase 2 用白板名做 group_id + Phase 3 调研 prompt 案例写外部文件

**决策状态: [Decision-Review] PENDING — 待验证: Neo4j 7691 连接正常 + group_id 命名规则前后端一致 + prompt 文件质量**
