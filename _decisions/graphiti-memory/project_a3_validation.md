---
name: A3 四方向深度验证结论
description: A3 检索范围+Wiki-links+Frontmatter+Cross-Canvas 四方向的社区/论文验证 + 代码对抗性审查完整结论（2026-03-13）
type: project
---

## A3 四方向验证结论（2026-03-13）

**Why:** 用户要求对 A3 四方向进行"深度定向 explore（社区调研+成熟论文+代码审查）"后再确认方向。
**How to apply:** 后续实施时参考各方向的可复用代码、需修复项和优先级。

### 验证结论总览

| 方向 | 社区成熟度 | 代码可复用性 | 阻断性问题 |
|------|-----------|-------------|-----------|
| 1. Scope 范围过滤 | 高 — 行业标准 | 可复用（需修2处） | 无 |
| 2. Frontmatter 解析 | 高 — Obsidian RAG 标配 | 可复用（需修1处） | 无 |
| 3. Wiki-links 集成 | 中高 — GraphRAG 研究热点 | 可复用（需修1处+补1处） | 无 |
| 4. Cross-Canvas 桥接 | 中 — 理论扎实，实践少 | 后端可复用/RAG端需重写 | 无 |

### 方向1: Scope 范围过滤
- 论文: Multi-Meta-RAG(2024) 验证准确率提升25%+
- 代码: LanceDB search() 已支持 subject WHERE 过滤
- 需修: YAML frontmatter 污染首chunk + WHERE子句SQL注入风险

### 方向2: Frontmatter 解析
- 社区: 几乎所有 Obsidian RAG 项目都解析 frontmatter（obsidian-notes-rag, Smart Connections等）
- 代码: index_vault_notes() 有清晰拦截点
- 需修: 索引时增加 YAML 解析+剥离逻辑

### 方向3: Wiki-links 集成
- 论文: GraphRAG Survey (ACM TOIS 2024), Microsoft GraphRAG, KG-RAG (Nature 2024)
- 代码: extract_and_resolve_wikilinks() 是真实实现，核心解析正确
- Critical bug: _extract_heading_section 遇任何子标题就截断（应只在同级或更高级截断）
- 需补建: wikilink信息未接入RAG检索层（仅用于上下文增强）

### 方向4: Cross-Canvas 跨课程桥接
- 后端 CrossCanvasService(1368行) = 100%真实实现，Neo4j持久化
- Critical: API路由未注册（所有端点不可访问）
- Critical: RAG端 find_related_canvases() 是TODO空壳(永远返回[])
- Critical: 两个同名CrossCanvasService类完全不相连
- 前端: HTTP方法不匹配(POST vs GET)
- 需修: 注册路由(5min) + 连通RAG retriever与后端服务 + 修前端端点

### 深度论文验证补充（第二轮 agent 结果）

#### 方向1 Scope — 补充发现
- HopRAG (ACL 2025): 1-hop neighbor expansion 在多跳QA上有效，但2-hop以上收益递减
- Anthropic Contextual Retrieval: metadata prepend 减少检索失败率 35-67%
- 对<100k文档规模，pre-filter（LanceDB默认）优于 post-filter

#### 方向3 Wiki-links — 关键补充
- ObsidianRAG (GitHub): **精确模式匹配** — 先hybrid search + CrossEncoder reranking，再沿[[wikilink]]展开上下文
- 建议存 `cited_notes: ["noteA","noteB"]` 到索引metadata，检索后取top-3邻居（按cosine相似度），合并后重排
- Hub notes（链接几十个子笔记的索引页）需特殊处理，否则结果爆炸

#### 方向3 三层渐进范围 — ⚠️ 轻度关注
- "Canvas→Course→All 渐进展开"模式是合理工程设计，但**无直接论文验证**这一特定模式
- 最接近的: FLARE(2023, 生成时触发检索)、Self-RAG(2024, 检索必要性判断) — 都不完全匹配
- 建议用 max_similarity < threshold 作为展开触发器，bge-m3 初始阈值~0.65
- 替代方案: RouterQueryEngine 式前置路由（直接根据查询决定范围，避免失败重试延迟）

#### 方向4 Cross-Canvas — 补充
- 教育KG论文验证: MDKAG(2025), EduKG+PKG(2025), 先修关系学习路径(Nature 2025)
- 逻辑隔离（metadata filter）在<100k文档规模足够，无需物理隔离（单独表）
- 跨课程桥接服务不是可选的，是必须的（否则过度隔离阻碍跨领域发现）

### 建议实施优先级
- P0: 方向1+2（行业标准，改动小，收益确定）
- P1: 方向3（研究热点，代码基础好，修1个bug就能用；三层渐进范围需实测验证）
- P2: 方向4（后端基础好但RAG端需重写，社区实践少）
