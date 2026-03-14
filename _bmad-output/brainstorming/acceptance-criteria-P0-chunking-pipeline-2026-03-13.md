# P0 Chunking Pipeline — 验收标准文档

**来源 Session:** P0-chunking-验收标准 (brainstorming)
**日期:** 2026-03-13
**状态:** 全部锁定 (All Locked)
**关联 brainstorming:** `brainstorming-session-P0-chunking-pipeline-2026-03-11.md`

---

## 总览

| DR | 主题 | 维度数 | 状态 |
|----|------|--------|------|
| DR-1 | 分块策略升级 | 10 | Locked |
| DR-2 | bge-m3 三阶段迁移 | 11 | Locked |
| DR-3 | Contextual Retrieval + 激活 reranker/query rewriter | 7 | Locked |
| DR-4 | 中英分词（bge-m3 sparse 替代 BM25） | — | **Closed**（被 DR-2 吸收） |

**Golden Test Set:** 混合模式 — Sprint 级别 + DR 级别验收标准并行

---

## DR-1: 分块策略升级（10 维度）

> 决策内容：保留 `_split_md_by_heading()`，重写 `_chunk_text()` 为 bge-m3 AutoTokenizer + 句子边界感知 + 原子保护
> 涉及模块：`lancedb_client.py`

### ① Token 计数器正确性 — BLOCKER

| 项目 | 内容 |
|------|------|
| **通过条件** | 使用 bge-m3 AutoTokenizer (`AutoTokenizer.from_pretrained("BAAI/bge-m3")`) 进行 token 计数，**非** tiktoken `cl100k_base`。两者在中文文本上差异可达 20-40%。 |
| **失败条件** | 使用 tiktoken 或其他非 bge-m3 tokenizer 计数，导致 chunk 实际大小与目标范围偏差 >20% |
| **测试方法** | 对比 bge-m3 tokenizer 与 tiktoken 的 token 计数输出，验证代码使用的是 XLM-RoBERTa tokenizer |

### ② 原子保护扩展版 — Hard Gate

| 项目 | 内容 |
|------|------|
| **通过条件** | 以下单元不可被切分：代码块（\`\`\`）、Mermaid 图、LaTeX 公式（`$$...$$`、`\begin{}\end{}`）、表格、图片+标题、列表、"定义-例子-解答"连续块 |
| **失败条件** | 任何原子单元被切断到两个不同 chunk 中 |
| **测试方法** | 全量扫描所有 ~2500 chunks：\`\`\` 配对（必须偶数）、`$$` 配对、`|---|` 表格完整性、`\begin{X}` 与 `\end{X}` 在同一 chunk |

### ③ 面包屑正确性 — Hard Gate

| 项目 | 内容 |
|------|------|
| **通过条件** | 每个 chunk 的前缀精确匹配原文档的 heading 层级。格式：`"文档 > H1 > H2 > H3"` |
| **失败条件** | 面包屑与原始文档的 heading 路径不匹配 |
| **测试方法** | 解析原始 Markdown AST → 构建 heading 树 → 比对每个 chunk 的面包屑字段。Edge case：第一个 heading 前的内容使用文档标题 |

### ④ 下游检索不退步 — Core Value

| 项目 | 内容 |
|------|------|
| **通过条件** | 新分块的 Recall@10 ≥ 旧分块的 Recall@10 |
| **失败条件** | 新分块导致检索质量回退 |
| **测试方法** | Golden test set 查询在新旧 chunk 上分别运行，对比 Recall@10 |

### ⑤ 内容零丢失 — Recommended

| 项目 | 内容 |
|------|------|
| **通过条件** | 拼接所有 chunk（去除面包屑前缀）可还原原始文本，无内容缺失 |
| **失败条件** | 拼接后与原文对比存在缺失内容 |
| **测试方法** | Strip breadcrumb prefix → join all chunks → diff vs original document |

### ⑥ 中英混合句子边界 — Recommended

| 项目 | 内容 |
|------|------|
| **通过条件** | Edge case 测试集 100% 通过。覆盖：纯中文句子、纯英文（含缩写 "Dr."/"e.g."、小数 "3.14"）、中英混合、代码块内不切、LaTeX 公式内不切 |
| **失败条件** | 任何 edge case 失败 |
| **测试方法** | 创建 ≥30 条句子边界 edge case 测试用例，全部必须通过 |

### ⑦ 退化 chunk 检测 + 抽样可读性 — Recommended

| 项目 | 内容 |
|------|------|
| **通过条件** | 无空 chunk。每个 chunk 最低 50 tokens。抽样 10 个 chunk 人工判断自包含性 |
| **失败条件** | 存在空 chunk 或 <50 token 的 chunk |
| **测试方法** | 自动扫描空/过小 chunk + 随机抽样 10 个人工审核 |

### ⑧ 大小分布合理性 — Suggested

| 项目 | 内容 |
|------|------|
| **通过条件** | Chunk 大小分布集中在目标范围（400-512 tokens），无大量离群值 |
| **失败条件** | 大量 chunk 偏离目标范围 |
| **测试方法** | 生成 chunk 大小直方图，验证多数落在目标范围内 |

### ⑨ Chunk ID 稳定性 — Recommended

| 项目 | 内容 |
|------|------|
| **通过条件** | 对文档做小幅编辑后，未修改内容的 chunk ID 保持不变。使用 content-hash（`SHA256(heading_path + chunk_content)`）而非 index-based ID |
| **失败条件** | 小幅编辑导致大量 chunk ID 变化 |
| **测试方法** | 修改文档中间部分 → 重新分块 → 验证未修改部分的 chunk ID 不变 |

### ⑩ 增量索引更新 — Recommended（补充维度）

| 项目 | 内容 |
|------|------|
| **通过条件** | 修改笔记后：旧 chunk 被移除、新 chunk 正确入库、搜索不返回过期内容 |
| **失败条件** | 旧 chunk 残留、新 chunk 缺失、搜索结果包含过期数据 |
| **测试方法** | 修改一篇笔记 → 触发重索引 → 验证：旧 chunk 已删、新 chunk 存在、搜索无陈旧结果 |
| **来源** | DR-4 关闭验证 deep explore 发现的覆盖 Gap A |

---

## DR-2: bge-m3 三阶段迁移（11 维度）

> 决策内容：MiniLM → bge-m3 Dense + LanceDB BM25 FTS + ColBERT 渐进迁移
> 涉及模块：`multimodal_vectorizer.py`, `lancedb_client.py`, `config.py`, `reranking.py`
> 重要变更：Phase 2 从"bge-m3 sparse"变更为"LanceDB BM25 FTS + jieba 预分词"（原因：LanceDB 不支持原生稀疏向量，GitHub issue #1930）

### ① Phase 1 Dense Embedding 质量

| 项目 | 内容 |
|------|------|
| **通过条件** | bge-m3 dense 在 golden test set 上的检索质量比 MiniLM 提升 ≥5%（Stretch goal: +10%） |
| **失败条件** | 相比 MiniLM 出现回退 |
| **测试方法** | A/B 对比：相同查询 + 相同 chunk，MiniLM 384d vs bge-m3 1024d。对比 Recall@10, NDCG@5 |

### ② Phase 2 Hybrid Search 效果

| 项目 | 内容 |
|------|------|
| **通过条件** | Dense + LanceDB BM25 FTS 混合搜索 ≥ 纯 Dense 搜索 |
| **失败条件** | 混合搜索差于纯 Dense |
| **测试方法** | 运行受益于关键词精确匹配的查询（如 "minimax alpha-beta pruning"）；对比 hybrid vs dense-only |

### ③ Phase 3 ColBERT 门槛

| 项目 | 内容 |
|------|------|
| **通过条件** | ColBERT reranking NDCG 提升 >2% **且** 延迟 <200ms。未达标时 fallback 到 CrossEncoder (`bge-reranker-v2-m3`) 可接受 |
| **失败条件** | ColBERT 无可测量提升或延迟 >200ms，且无 fallback 路径 |
| **测试方法** | Golden test set 上 benchmark ColBERT reranking；测量 NDCG delta 和 p95 延迟 |

### ④ ONNX int8 量化性能

| 项目 | 内容 |
|------|------|
| **通过条件** | 模型大小 ≤600MB、单查询 embedding 延迟 ≤50ms（CPU）、内存占用 ≤1.5GB |
| **失败条件** | 任一阈值超标且无缓解方案 |
| **测试方法** | 部署 ONNX int8 量化 bge-m3，使用标准化负载 benchmark |

### ⑤ 回滚机制

| 项目 | 内容 |
|------|------|
| **通过条件** | 全量重索引能力 + shadow mode（新旧索引共存）+ feature flag 切换 |
| **失败条件** | 新模型质量下降时无回滚路径 |
| **测试方法** | 验证：可通过 feature flag 切回 MiniLM；旧索引保留；shadow mode 工作正常 |

### ⑥ 资源约束

| 项目 | 内容 |
|------|------|
| **通过条件** | CPU 内存在可接受范围（~650MB int8 / ~2.5GB fp32）。全量索引时间合理。单查询延迟可接受 |
| **失败条件** | 内存超出系统可用资源；索引时间不可接受地长 |
| **测试方法** | 测量峰值内存、~2500 chunks 索引时间、负载下单查询延迟 |

### ⑦ 中文分词质量

| 项目 | 内容 |
|------|------|
| **通过条件** | jieba 预分词 + LanceDB FTS：中文学术术语关键词命中率 ≥90%。含 FTS 预分词正确性测试 + 中英混合查询测试用例 |
| **失败条件** | 中文术语 FTS 搜不到；命中率 <90% |
| **测试方法** | 使用已知中文学术术语测试（如 "马尔可夫决策过程"、"强化学习"），验证 FTS 返回正确结果 |
| **注** | 已因 DR-4 关闭条件②而强化 |

### ⑧ 压缩保真度

| 项目 | 内容 |
|------|------|
| **通过条件** | ONNX int8 量化 vs fp32：相同输入的 cosine similarity ≥0.995 |
| **失败条件** | cosine <0.995，表明量化导致显著质量损失 |
| **测试方法** | 用 fp32 和 int8 模型分别为测试集生成 embedding，计算 pairwise cosine similarity |

### ⑨ 中文专项评估

| 项目 | 内容 |
|------|------|
| **通过条件** | 在真实 CS188 vault 数据上测试（非合成数据）。中文学术内容检索质量已验证 |
| **失败条件** | 仅在合成/英文数据上测试 |
| **测试方法** | 使用真实 vault 笔记作为测试语料；运行中文学术查询；用 RAGAS/DeepEval 评估 |

### ⑩ 迁移数据完整性

| 项目 | 内容 |
|------|------|
| **通过条件** | 迁移过程零数据丢失。所有文档已重索引，chunk 数量符合预期，无孤立记录 |
| **失败条件** | 任何文档或 chunk 在迁移中丢失 |
| **测试方法** | 对比迁移前后：文档数、chunk 数、抽查特定文档 |

### ⑪ 自动术语词典

| 项目 | 内容 |
|------|------|
| **通过条件** | 三层架构：L0（标题/标签/加粗结构提取）准确率 ≥95%；L1（PMI + 左右熵统计新词发现）F1 ≥70%；L2（LLM few-shot 批量提取）准确率 ≥85%（人工审核）。综合：搜索术语精确匹配率 ≥90% |
| **失败条件** | 笔记中的术语在搜索时不被 jieba 识别 |
| **测试方法** | L0：验证标题/标签术语自动添加；L1：在 vault 语料上运行统计新词发现，测 F1；L2：LLM 提取术语，人工抽查 20+ 条 |

---

## DR-3: Contextual Retrieval + 激活 Reranker/Query Rewriter（7 维度）

> 决策内容：Phase 1 rule-based heading prefix + Phase 2 Gemini Flash 上下文生成 + 激活 reranker + query rewriter (Sprint 0)
> 涉及模块：`lancedb_client.py`, `contextual_enricher.py`(新), `nodes.py`, `state_graph.py`

### ① 管道打通性 — Hard Gate

| 项目 | 内容 |
|------|------|
| **通过条件** | Reranker 和 Query Rewriter 在真实查询中被实际调用。日志证明 `reranking.py` LocalReranker 和 `quality/query_rewriter.py` 被调用（而非 nodes.py / state_graph.py 中的 stub） |
| **失败条件** | Stub 仍活跃；reranker 原样返回输入；query rewriter 只是加前缀 "请详细解释:" |
| **测试方法** | 运行真实查询，检查日志中的 reranker 模型推理和 LLM query rewrite 调用。验证输出顺序与输入不同（当文档相关性有差异时） |

### ② 检索质量提升 — Core Value

| 项目 | 内容 |
|------|------|
| **通过条件** | Reranker + Rewriter ON vs OFF：正确 chunk 排名整体提升。Recall@K / NDCG@5 / MRR 在 golden test set 上有改善 |
| **失败条件** | 激活组件后无可测量改善或出现回退 |
| **测试方法** | Before/after A/B 对比，使用 golden test set 查询 |

### ③ 延迟约束 — Baseline

| 项目 | 内容 |
|------|------|
| **通过条件** | P95 端到端检索延迟 < 1 秒（含 reranker + query rewriter） |
| **失败条件** | P95 > 1s |
| **测试方法** | 运行 50+ 查询，测量 p50/p95/p99 延迟 |

### ④ 逐查询回归检测 — Recommended

| 项目 | 内容 |
|------|------|
| **通过条件** | Query rewriter 导致检索质量下降的查询 ≤10% |
| **失败条件** | >10% 查询在改写后结果变差 |
| **测试方法** | 逐查询对比：原始查询 vs 改写查询的检索结果。标记改写后正确 chunk 减少的查询 |
| **依据** | Nexumo 2026, ZenML, RaFe EMNLP 2024 — 聚合指标可掩盖逐查询退化 |

### ⑤ 优雅降级 — Recommended

| 项目 | 内容 |
|------|------|
| **通过条件** | Reranker 故障时：返回未重排的原始结果。Query Rewriter 故障时：使用原始查询。所有故障场景：正常返回结果，无 500 错误 |
| **失败条件** | 组件故障导致系统崩溃或返回错误 |
| **测试方法** | Mock `CROSS_ENCODER_AVAILABLE=False`，验证结果正常返回 + WARNING 日志。Mock LLM 超时，验证使用原始查询 |

### ⑥ Score 归一化 — Suggested

| 项目 | 内容 |
|------|------|
| **通过条件** | 确认 score 使用方式：仅用于排序则 raw logits 可接受；若用于阈值过滤（如 CRAG quality gate score > 0.7），则必须 sigmoid 归一化。`bge-reranker-base` 输出 raw logits（如 -5.65），非 0-1 概率 |
| **失败条件** | 基于阈值过滤时使用未归一化的 raw logits，导致路由决策错误 |
| **测试方法** | Code review：检查 reranker score 的下游消费方式。如基于阈值，验证 sigmoid 已应用 |

### ⑦ Hybrid Search 融合质量 — Recommended（补充维度）

| 项目 | 内容 |
|------|------|
| **通过条件** | 对 BM25 和 Dense 结果不一致的查询，RRF 融合结果优于任一单源 |
| **失败条件** | 融合结果差于最佳单源 |
| **测试方法** | 构造 BM25 与 Dense 结果发散的查询；验证融合结果质量超过任一单源 |
| **来源** | DR-4 关闭验证 deep explore 发现的覆盖 Gap B |

---

## DR-4: 中英分词（bge-m3 sparse 替代 BM25）— CLOSED

### 关闭状态

**状态：** 已关闭，被 DR-2 吸收

### 关闭理由

DR-4 原计划用 bge-m3 sparse 向量替代传统 BM25/FTS 解决中文分词问题，但因 LanceDB 不支持原生稀疏向量（GitHub issue #1930，自 2024 年 12 月 OPEN，官方无明确支持时间表）而变得不可行。

替代方案（LanceDB BM25 FTS + jieba 预分词 + Dense 混合搜索）已被 DR-2 的维度②（Hybrid Search）、⑦（中文分词质量）、⑪（自动术语词典）完全覆盖。

### 关闭条件（全部满足）

| # | 条件 | 状态 |
|---|------|------|
| 1 | 记录未来优化机会 `[TechDebt]` — 当 LanceDB 支持稀疏向量时重新评估 | ✅ 已记录 |
| 2 | 强化 DR-2 维度⑦ — 增加 FTS 预分词正确性测试 + 中英混合查询测试 | ✅ 已纳入 |
| 3 | 监控 LanceDB issues #1930 / #2168 / #2329 — 建议季度检查 | ✅ 已记录 |

### 覆盖 Gap 补充

| Gap | 描述 | 分配到 |
|-----|------|--------|
| Gap A | 增量索引更新 | DR-1 维度⑩ |
| Gap B | Hybrid search 融合质量 | DR-3 维度⑦ |

---

## Sprint 级别验收门控

| Sprint | 必须通过的维度 | 门控条件 |
|--------|--------------|---------|
| S0 | DR-3 ①②③⑤ | 管道打通 + 质量提升 + 延迟达标 + 降级正常 |
| S1 | DR-1 ①②③④⑤⑥⑦⑧⑨⑩ + DR-2 ①⑤⑥⑩ | 分块全部通过 + Dense 质量 + 回滚 + 资源 + 数据完整 |
| S2 | DR-2 ②④⑦⑧⑨⑪ + DR-3 ⑥⑦ | Hybrid search + ONNX + 中文 + 融合质量 |
| S3 | DR-2 ③ + DR-3 ④ | ColBERT 门槛 + 逐查询回归 |

---

## Golden Test Set 要求

- **来源：** 真实 CS188 vault 数据（禁止合成数据）
- **规模：** ≥50 条查询，覆盖中文、英文、中英混合
- **标注：** 每条查询的期望返回 chunk（ground truth）
- **更新策略：** 随 Sprint 迭代扩展（S1 后加 embedding 对比查询，S2 后加关键词精确匹配查询）

---

## 附录：关键技术发现

### LanceDB 限制

| 限制 | GitHub Issue | 影响 | 应对 |
|------|-------------|------|------|
| 不支持原生稀疏向量 | #1930 (OPEN since 2024-12) | Phase 2 计划变更 | BM25 FTS 替代 |
| Tantivy 不支持中文分词 | #2168, #2329 | 中文 FTS 逐字切分 | jieba 预分词 |
| 384→1024 维度迁移需全量重建 | — | 无法原地迁移 | 纳入 Sprint 1 重建 |

### 备选方案：Milvus Lite

> **状态：** 发现阶段，已标记为独立评估 session 主题
>
> Milvus Lite 是嵌入式模式（`pip install pymilvus`），原生支持 jieba 中文分词 + BM25 + 稀疏向量，理论上可解决 LanceDB 的全部 3 个限制。项目已有 Python FastAPI 后端，零额外架构成本。
>
> **当前决策：** 不在本轮 P0 验收中处理，作为未来优化方向独立评估。

### Code Review 结果摘要

| 模块 | 评级 | 关键问题 |
|------|------|---------|
| `lancedb_client.py` | 需修复 | 硬编码 384 维、FTS 索引不全、hybrid search 未激活 |
| `multimodal_vectorizer.py` | 可复用（需配置更新） | 架构清晰可扩展，缺 bge-m3 支持 |
| `multimodal_content.py` | 需修复 | 硬编码 768 维度验证，会拒绝 1024 维 |
| `multimodal_store.py` | 需修复 | 默认 vector_dim=768 |
| `fusion/rrf_fusion.py` | **完全可复用** | 纯算法代码，模型无关 |
| `config.py` | 可复用（需更新） | 缺 1024 维配置 |
| `nodes.py` | 可复用 | `retrieve_lancedb` 默认 `query_type="vector"`，从不用 hybrid |

---

## 变更历史

| 日期 | 变更 |
|------|------|
| 2026-03-11 | Brainstorming session 完成 4 主题方案设计，生成 4 个 DR |
| 2026-03-12 | 验收标准制定开始；DR-1 锁定 9 维；DR-3 锁定 6 维 |
| 2026-03-13 | DR-2 锁定 11 维（含 Phase 2 方向变更）；DR-4 关闭；DR-1 补充至 10 维；DR-3 补充至 7 维 |
| 2026-03-13 | 最终文档生成，全部锁定 |
