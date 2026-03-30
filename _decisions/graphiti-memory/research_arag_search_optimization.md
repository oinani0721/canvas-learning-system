---
name: A-RAG 三级验证 + 检索管道优化调研
description: 用户"Grep回源验证"想法被A-RAG论文验证 + 6项管道升级建议（P0-P7）（2026-03-15，待用户确认）
type: project
---

Session：PRD Review | 背景：用户提出 RAG 搜到候选后用 Grep 回源文件验证质量

## 核心发现

### 用户想法的学术定位
- 精确对应 A-RAG [arXiv:2602.03442] 的三级检索架构（keyword → semantic → chunk read）
- HotpotQA 94.5%
- Amazon [2602.23368] 证实 agentic keyword search 达 RAG 90%+ 性能
- 用户想法中"索引过时检测"是学术盲区但实际痛点

### 6 项管道升级建议
- P0: Reranker → gte-reranker-modernbert-base（149M，2026榜首，替换bge-reranker-v2-m3）
- P1: Contextual Retrieval 索引时增强（Session A1 已计划，确认方向正确）
- P2: 智能查询路由（不每次跑7路，按查询类型路由）
- P3: CRAG → 迭代 Retrieve-Verify 循环（最多3次）
- P5: Embedding 评估（bge-m3 仍优秀，Qwen3-8B 过重，不急换）
- P7: Jina-ColBERT-v2（可选补充信号，优先级低）

### 新增架构组件
- Staleness Check：content_hash 与源文件比对，过时→Grep/Read获取最新+触发重索引
- Context Expansion：对top-5中上下文不足的chunk，Read回源文件扩展完整段落
- 迭代 Quality Gate：升级版 CRAG，不达标→分解查询→重搜→交叉验证

**Why:** 用户想优化四层搜索管道，提出了 Grep 回源验证的想法
**How to apply:** 如确认，更新 PRD 加入 A-RAG 三级验证 + P0-P3 优化项
**决策状态：调研结论，待用户确认方向**
