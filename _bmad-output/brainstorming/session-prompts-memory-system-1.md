# Session 启动提示词 — 记忆系统 1 子议题

> 生成自 Session A（记忆系统1深潜），日期 2026-03-11
> 所有 session 通过 Graphiti (`canvas-dev`) 共享信息

---

## Session A1：分块策略 + 嵌入模型（★★★★ P0 阻断项）

**可并行启动，无前置依赖**

```
你是 Session A1，负责 Canvas Learning System 的"分块策略 + 嵌入模型集成"设计与实施。

## 背景（从 Graphiti canvas-dev 搜索获取完整上下文）
- 搜索 "Session A 分块策略 bge-m3" 获取前序 session 的调研结论
- 搜索 "chunking 500 chars all-MiniLM" 获取代码现状
- 搜索 "验收标准 golden test set" 获取质量目标

## 已确定的事实
1. 当前 embedding: all-MiniLM-L6-v2 (384d 英文专用) → 必须换成 bge-m3 (1024d 中文 nDCG@10=63.9)
2. 当前 chunking: 500 chars 硬切 + 50 overlap → 改为 heading 感知 + token 递归分割 (400-512 tokens, overlap 50-80)
3. 推荐管道: Markdown heading 分段 → token 递归分割 → Contextual Retrieval (Anthropic 方法，-49% 检索失败率)
4. MRR 目标从 0.350 提升到 ≥ 0.70

## 本 session 具体任务
1. **bge-m3 集成方案**：
   - 替换 all-MiniLM-L6-v2 的影响范围（3 个文件使用）
   - VRAM 需求评估（RTX 4060 8GB，同时运行 bge-reranker-v2-m3 约 2.2GB）
   - LanceDB 向量维度从 384→1024 的迁移方案
   - 是否需要量化（FP16/INT8）

2. **Obsidian 笔记分块策略**：
   - Markdown heading 层级分段的具体实现（处理 #/##/### 嵌套）
   - 中英混合内容的分词策略（jieba 只处理中文，英文部分怎么办？）
   - 特殊元素保留：LaTeX ($...$)、代码块 (```...```)、Obsidian callout (> [!note])、wikilinks ([[...]])
   - 图片引用 (![[screenshot.png]]) 如何处理——保留引用文本还是丢弃？
   - heading 路径作为 chunk 元数据（如 "Lecture3 > 启发式搜索 > A*算法"）

3. **Contextual Retrieval 实现**：
   - 每个 chunk 前加文档/章节级上下文前缀
   - 用 LLM 生成还是规则拼接（heading 路径 + 文档标题）？
   - 成本/延迟评估（每个 chunk 一次 LLM 调用 vs 规则前缀）

4. **中英混合分词**：
   - jieba 对英文和技术术语的处理方式
   - 是否需要自定义 jieba 词典（CS 术语如 "admissibility"、"backtracking"）
   - BM25 的分词器选择（jieba search 模式 vs 其他）

## 关键代码文件
- `src/agentic_rag/clients/lancedb_client.py` — _chunk_text() (lines 63-76), embedding model (line 128)
- `src/agentic_rag/config.py` — embedding model config (line 48)
- `backend/app/config.py` — VAULT_INDEX_CHUNK_SIZE=500, VAULT_INDEX_OVERLAP=50
- `backend/app/services/lancedb_index_service.py` — 索引管道

## 验收标准
- Precision@5 ≥ 0.70 (在 CS188 笔记上)
- 中文 query 的 Precision@5 不低于英文 query 的 80%
- 端到端索引延迟合理（全量重建 < 5min for ~120 files）

## 输出物
- 分块实现代码
- bge-m3 集成代码
- 分块前后的 MRR/Precision 对比数据
- 将结论记录到 Graphiti canvas-dev（前缀 [Implementation]）
```

---

## Session A2：检索结果组织 + Reranking（★★★ 依赖 A1）

**等 A1 完成 chunking 设计后启动**

```
你是 Session A2，负责 Canvas Learning System 的"检索结果组织 + Reranking 优化"。

## 背景
- 搜索 Graphiti "Session A1 分块" 获取 A1 的 chunking 输出格式
- 搜索 "Reduced RAG Self-RAG CRAG 跨学科精准检索" 获取调研结论
- 搜索 "验收标准 Precision@5" 获取质量目标
- 搜索 "Phase 1 Phase 2 融合架构" 获取代码现状

## 已确定的事实
1. Phase 1 直接暴力拼接 15K token 上下文，绕过所有融合逻辑
2. 已有 UnifiedResult + 多源融合架构（权重配置齐全），但未启用
3. 已有 3 种 Reranker（Local bge-reranker-base, Cohere, Hybrid）
4. grade_documents 节点已存在（agent_graph.py:228-318）但禁用
5. 社区调研：Reduced RAG (top 5-10 证据, 80-90% token 减少), Self-RAG (自判相关性), CRAG (质量低→rewrite query)

## 本 session 具体任务
1. **Phase 1→Phase 2 迁移路径**：
   - 最小改动启用融合框架的方案
   - 是否需要 LangGraph（Phase 3）还是可以在 Phase 1 框架内增强？
   - 渐进式迁移 vs 一次性切换

2. **Reranking 策略优化**：
   - bge-reranker-base → bge-reranker-v2-m3 的切换
   - 阈值截断：score < X 的结果直接丢弃（X 值如何确定？）
   - top-K 选择：top-5 (激进精准) vs top-10 (保守全面)

3. **Self-RAG/CRAG 质量闭环**：
   - 启用 grade_documents 节点的方案
   - 评分低→rewrite query 再检索的循环次数上限
   - 评分维度：相关性、完整性、新鲜度

4. **Reduced RAG 上下文组装**：
   - Signals→Evidence→Constraints 三阶段实现
   - 证据排列顺序（Lost-in-the-middle：重要证据放首尾）
   - "仅基于以下证据回答"约束提示的模板设计
   - heading 路径前缀如何显示在证据中

5. **多源权重调优**：
   - 当前默认权重 graphiti:0.25/lancedb:0.25/textbook:0.20/cross_canvas:0.15/multimodal:0.15
   - 根据 query 类型动态调权的可行性
   - strategy_selector.py 已有 CanvasOperation→FusionStrategy 映射但从未调用

## 关键代码文件
- `backend/app/services/agent_service.py` — call_explanation() (lines 3122-3329), _call_gemini_api() (lines 2152-2301)
- `src/agentic_rag/agent_graph.py` — grade_documents (228-318), analyze_intent (49-138)
- `src/agentic_rag/fusion/strategy_selector.py` — CanvasOperation→FusionStrategy 映射 (58-82)
- `src/agentic_rag/fusion/evaluator.py` — MRR@K 评估
- `backend/app/config.py` — 融合权重配置

## 验收标准
- 上下文 token 数从 15K 降至 ≤ 3K (Reduced RAG 目标)
- Faithfulness ≥ 0.85 (回答基于检索证据)
- Reranker 提升 MRR ≥ +0.10
- 质量闭环触发率 < 20%（大部分 query 首次检索即满足）

## 输出物
- Phase 迁移实施方案
- Reranking + 质量闭环代码
- 上下文组装模板
- 记录到 Graphiti canvas-dev（前缀 [Implementation] 或 [Architecture]）
```

---

## Session A3：检索范围 + Wiki-links + Obsidian 原生能力（★★☆ 可并行）

**可与 A1 并行启动，无依赖**

```
你是 Session A3，负责 Canvas Learning System 的"检索范围设计 + Wiki-links 增强 + Obsidian 原生能力集成"。

## 背景
- 搜索 Graphiti "检索范围 course_tag Multi-tenant" 获取调研结论
- 搜索 "Wiki-links backlinks Obsidian CLI" 获取代码现状
- 搜索 "frontmatter tags 索引" 获取已知缺陷
- 搜索 "AI 解释文件 -explanations" 获取过滤策略

## 已确定的事实
1. 当前索引范围：Canvas nodes + Vault notes + Multimodal，跳过 .obsidian/.git/.trash
2. Obsidian frontmatter/tags 未被索引为独立实体
3. Obsidian CLI (search_obsidian_cli) 已完整实现：search:context + outline + backlinks
4. CLI 结果过滤已自动排除 -explanations/、/chunks/、解释- 等
5. Wiki-links 仅在查询时通过 CLI backlinks 使用，索引管道中完全未处理
6. 社区调研：Silo(课程独立)/Pool(共享索引)/Bridge(跨课程语义桥接)三种模式
7. 用户当前一门课一个 vault，未来可能多课程共存

## 本 session 具体任务
1. **索引范围策略**：
   - 当前单 vault (CS188) 全量索引的过滤规则细化
   - 未来多课程 vault 时的 course_tag 元数据设计
   - LanceDB WHERE 过滤实现（Silo→Pool→Bridge 渐进）
   - Canvas 文件 (.canvas JSON) 是否应该索引？（目前已索引 Canvas nodes）

2. **AI 解释文件索引决策**：
   - 30+ AI 生成的解释文件 (*-explanations/ 目录)
   - CLI 已过滤，但向量索引端未过滤
   - 索引 AI 解释 = 更多候选但引入二手内容
   - 不索引 = 可能丢失已精炼的理解
   - 建议：带 source_type="ai_generated" 标签索引，检索时降权

3. **Wiki-links 图谱增强**：
   - 在索引阶段提取 [[...]] 链接，构建笔记间的关系图
   - 检索时利用关系图：命中一个 chunk → 关联 wikilink 指向的 chunks 也作为候选
   - 与 Obsidian CLI backlinks 的分工：索引时（图谱） vs 查询时（CLI）
   - 链接类型区分：概念链接 vs 导航链接

4. **Obsidian frontmatter/tags 索引**：
   - 解析 YAML frontmatter（tags, aliases, date, course 等）
   - tags 作为 LanceDB 元数据列（支持 WHERE 过滤）
   - aliases 用于 query 扩展（"A*" → "A-star", "A star algorithm"）

5. **Bridge 跨课程检索**：
   - 何时触发跨课程检索（query 中有跨领域关键词？用户显式指定？）
   - 跨课程结果的权重降低策略
   - 概念桥接检测（"线性代数的特征值" 在 CS188 中被引用）

## 关键代码文件
- `backend/app/services/lancedb_index_service.py` — 索引管道
- `backend/app/services/react_agent.py` — search_obsidian_cli() (line 331), find_backlinks() (line 390)
- `backend/app/config.py` — VAULT_INDEX_SKIP_DIRS, 融合权重
- `src/agentic_rag/clients/lancedb_client.py` — LanceDB schema

## 验收标准
- frontmatter tags 可用于 WHERE 过滤
- Wiki-links 关联提升 Recall@10 ≥ 5%
- 跨课程检索不引入 > 30% 无关结果
- AI 解释文件在非指定查询中不出现在 top-3

## 输出物
- 索引范围 + 元数据设计文档
- Wiki-links 提取 + 图谱构建代码
- frontmatter 解析代码
- 记录到 Graphiti canvas-dev（前缀 [Architecture] 或 [Implementation]）
```

---

## Session A4：索引管道 + Context Enrichment + 触发时机（★★☆ 依赖 A1）

**等 A1 完成 chunking 设计后启动**

```
你是 Session A4，负责 Canvas Learning System 的"索引管道优化 + Context Enrichment + 检索触发时机"。

## 背景
- 搜索 Graphiti "Session A1 分块策略" 获取 A1 确定的 chunking 方案
- 搜索 "索引管道 Story 38.1 去抖 增量" 获取代码现状
- 搜索 "Context Enrichment 父子节点 BFS" 获取已有实现
- 搜索 "记忆系统 1 记忆系统 2 交叉" 获取两个系统的协作设计

## 已确定的事实
1. Story 38.1 已实现：500ms 去抖 + 3x 指数退避重试 + 崩溃恢复 (lancedb_pending_index.jsonl)
2. 当前是全量重建，不是增量索引
3. context_enrichment_service.py 已有 BFS 遍历 (enrich_with_adjacent_nodes, lines 780-929)
4. edge labels 已提取但未用于推理
5. 70% 的上下文推理能力已实现但未启用
6. 记忆系统 1 (全局笔记 RAG) 和记忆系统 2 (Graphiti 学生画像) 目前独立运行

## 本 session 具体任务
1. **增量索引优化**：
   - 文件修改检测（mtime vs content hash）
   - 仅对变更文件重新分块+重新 embed
   - LanceDB 的 upsert/delete 策略（按 file_path 分组）
   - 索引版本管理（避免部分更新导致不一致）

2. **索引触发时机**：
   - Obsidian 文件保存时自动触发？（通过 file watcher）
   - 用户手动触发（API endpoint 已有）？
   - 定时全量重建（兜底）？
   - 新文件加入 vault 时的检测与索引

3. **Context Enrichment 启用**：
   - enrich_with_adjacent_nodes 的启用条件
   - BFS 遍历深度参数（当前是什么？应该是多少？）
   - edge labels 用于推理：parent/child 关系推断概念层级
   - 与检索结果的融合方式（enrichment 结果加入上下文还是仅用于 reranking boost？）

4. **记忆系统 1 & 2 交叉**：
   - 检索笔记片段时，是否同时查询 Graphiti 获取用户对该概念的历史理解？
   - 场景：用户问 "A* 算法"，系统检索笔记 + Graphiti 返回"用户之前对 admissibility 有误解"
   - 交叉信号如何注入 prompt（作为额外 context section？作为 system instruction？）
   - 避免信息过载：何时注入学习历史、何时只返回笔记片段

## 关键代码文件
- `backend/app/services/lancedb_index_service.py` — 索引管道
- `backend/app/services/context_enrichment_service.py` — enrich_with_adjacent_nodes (780-929)
- `backend/app/config.py` — 索引相关配置
- `src/memory/temporal/fsrs_manager.py` — FSRS 复习调度
- `backend/app/services/graphiti_bridge_service.py` — Graphiti 实体类型

## 验收标准
- 增量索引：单文件更新 < 2s（vs 当前全量重建）
- Context Enrichment 提升 answer correctness ≥ 5%
- 记忆系统交叉不增加 > 500ms 延迟
- 索引一致性：部分更新后检索结果无旧数据残留

## 输出物
- 增量索引实现代码
- Context Enrichment 启用 + edge label 推理代码
- 记忆系统 1&2 交叉注入方案
- 记录到 Graphiti canvas-dev
```

---

## Session A5：多模态检索（★☆☆ 低优先级）

**独立，可在其他 session 完成后启动**

```
你是 Session A5，负责 Canvas Learning System 的"多模态检索增强"。

## 背景
- 搜索 Graphiti "多模态 Multimodal 图片 PDF" 获取代码现状
- 搜索 "OCR AI描述 向量化" 获取已有实现

## 已确定的事实
1. 图片向量化已实现：OCR(40%) + AI描述(60%) 加权融合
2. PDF 提取已实现：章节级 TOC 分块
3. 音频/视频：仅有空类定义，无实现
4. 性能目标：≤1s per content piece
5. 多模态权重在融合架构中为 0.15

## 本 session 具体任务
1. **图片检索增强**：
   - 课程截图（PPT slides、手写笔记照片）的 OCR 质量评估
   - AI 描述的 prompt 模板优化（面向课程内容的描述 vs 通用描述）
   - 截图与 Markdown 笔记的关联（![[image.png]] 出现在哪些笔记中）

2. **PDF 课件检索**：
   - 教授课件 PDF 的分块质量评估
   - 公式/图表在 PDF 中的处理
   - PDF 页码 → 笔记章节的映射

3. **音频/视频索引**（可选/未来）：
   - 讲课录音 → whisper 转录 → 分块索引
   - 视频截图 + 字幕双通道索引
   - 与 video-to-canvas pipeline 的集成可能性

## 关键代码文件
- 搜索 "multimodal" "image" "pdf" 相关文件
- 融合权重配置

## 验收标准
- 截图 OCR 中文识别准确率 ≥ 90%
- PDF 公式/图表不丢失关键信息
- 多模态结果在 top-10 中占比合理（不喧宾夺主）

## 输出物
- 多模态检索质量评估报告
- 增强方案设计文档
- 记录到 Graphiti canvas-dev
```

---

## Session C：验收系统 + Golden Test Set + CI（★★★ 可并行骨架）

**可立即启动骨架搭建，具体测试数据等 A1 后填充**

```
你是 Session C，负责 Canvas Learning System 的"检索质量验收系统 + Golden Test Set + CI 集成"。

## 背景
- 搜索 Graphiti "验收标准 golden test set Session C" 获取 Session A 传递的完整框架
- 搜索 "Precision@5 MRR@10 阈值" 获取质量目标
- 搜索 "evaluator.py Hit Rate MRR" 获取已有评估代码
- 搜索 "GEval DeepEval 自动评分" 获取工具选型

## 已从 Session A 接收的设计
1. Golden Test Set：50-100 query-answer pairs，手工标注自 CS188 vault
2. 6类覆盖比例：概念定义20%/对比分析20%/公式证明15%/代码理解15%/跨章节关联15%/中英混合15%
3. 验收指标阈值：Precision@5≥0.70, Recall@10≥0.80, MRR@10≥0.70, nDCG@10≥0.65, Context Relevance≥0.80, Faithfulness≥0.85
4. 已有 evaluator.py 有 MRR@K + Hit@1/5/10（但目标 0.350 过低）
5. 无中文课程笔记的 RAG benchmark，需自建评测基准

## 本 session 具体任务
1. **Golden Test Set 构建**：
   - 从 CS188 vault 选取代表性 query
   - 手工标注 relevant_chunks（哪些 chunk 是正确答案来源）
   - 标注 irrelevant_but_tricky（容易混淆但不相关的 chunk）
   - expected_answer_contains（答案必须包含的关键信息）
   - 格式设计（YAML/JSON? 存放位置?）

2. **集成测试框架搭建**：
   - tests/integration/test_retrieval_quality.py
   - 测试类：precision, recall, MRR, 中文平等性, 跨章节, reranker 提升, 噪声过滤, 延迟
   - pytest fixtures 加载 golden test set
   - 基线快照机制（记录上次通过的指标）

3. **自动评估工具集成**：
   - RAGAS 评估（context relevance, faithfulness）
   - DeepEval / GEval 集成
   - LLM-as-judge 评估方案（成本 vs 准确性权衡）

4. **CI Pipeline 设计**：
   - 触发条件：修改 chunking/embedding/reranking 代码
   - 步骤：加载 golden set → 运行检索 → 计算指标 → 对比基线 → 回归检测
   - 阈值回归：任一指标下降 > 5% → 阻断
   - GitHub Actions 或本地 pre-commit hook

5. **持续监控仪表板**（可选）：
   - 指标历史趋势可视化
   - 降级告警

## 关键代码文件
- `src/agentic_rag/fusion/evaluator.py` — 已有 MRR@K + Hit Rate
- `backend/app/config.py` — 评估相关配置
- CS188 vault 路径: C:\Users\Heishing\Desktop\spring course 2026\CS188

## 验收标准
- Golden Test Set ≥ 50 条覆盖 6 类
- 集成测试可运行并报告所有指标
- CI pipeline 可自动检测回归
- 文档化评估方法论

## 输出物
- golden_test_set.yaml
- tests/integration/test_retrieval_quality.py
- CI 配置文件
- 评估报告模板
- 记录到 Graphiti canvas-dev（前缀 [Test] 或 [Infrastructure]）
```

---

## 通用注意事项（适用所有 session）

```
## 每个 session 必须遵守的协议

1. **Session 启动**：
   - 搜索 Graphiti "Session-Start" 了解并行 session 状态
   - 搜索本 session 相关关键词获取历史上下文
   - 记录 [Session-Start] 到 Graphiti

2. **每轮对话**：
   - 回复前搜索 Graphiti（用户消息关键词）
   - 回复后记录新发现到 Graphiti

3. **Session 结束**：
   - 记录 [Session-End]（完成/未完成/后续建议）

4. **Graphiti 参数**：
   - group_id: "canvas-dev"
   - source_description: "session-{主题简称}-{YYYY-MM-DD}"

5. **代码修改**：
   - 修改前先 deep explore 确认当前代码状态
   - 修改后检查 LSP diagnostics
   - 大改动先与用户确认
```
