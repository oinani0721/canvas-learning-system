# S5-Review 验收标准 — A3 新功能方案对抗性审查

**审查者:** S5-Review 独立验证 session
**日期:** 2026-03-14
**来源文档:** `brainstorming-session-S5-A3-new-features-2026-03-13.md`
**审查方法:** 3 个并行独立 agent（代码对抗性审查 + 社区调研 + 论文条件验证）

---

## 审查总评

| 维度 | 评价 |
|------|------|
| S5 技术选型方向 | **大体正确** — 核心方案（RRF、LABEL_LIST、prefix embedding）均有社区/学术支撑 |
| S5 代码审查质量 | **中等偏宽松** — 3/5 评级准确，1 个事实性错误，多处遗漏 |
| S5 论文引用准确性 | **基本准确** — 但存在 3 处过度简化声明 |
| 最大系统性风险 | **中文 metadata prefix 效果是完全未验证的盲区** |

### S5 事实性错误（⛔ 必须修正）

1. **lancedb_client.py "跳过 frontmatter"** — 事实上该文件没有任何 frontmatter 处理逻辑，YAML metadata 被当作普通文本内容索引。这不是"跳过"，而是"错误索引"。
2. **"零成本"** — ECIR 2026 论文原文明确指出 prefix 方案在 metadata 更新时需要重新 embedding 全部索引，并非零成本。
3. **"零新依赖"** — python-frontmatter 是新依赖（虽然是小依赖）。

### S5 过度简化声明（需限定 scope）

1. **"无需调参"** — RRF k=60 是安全默认值，但论文指出 k 在不同数据分布上泛化不佳。
2. **"不需要图数据库"** — 仅在当前 tag 过滤场景成立。若未来需要前置知识链路推理，将需要图结构。
3. **"1-hop 足够"** — 综述推断而非实验结论，教育前置知识链可能需要 2-hop。

### S5 代码审查遗漏

| # | 遗漏内容 | 严重程度 |
|---|---------|---------|
| 1 | lancedb_client.py 无 frontmatter 剥离 — YAML 被当内容索引（非"跳过"） | **CRITICAL** |
| 2 | backend 已有完整 CrossCanvasService — S5 仅审查了 agentic_rag 的 stub | **HIGH** |
| 3 | subject_resolver vs subject_config 命名规范不一致（hyphens vs underscores） | **HIGH** |
| 4 | context_enrichment_service.py cache stampede bug（锁在 fetch 前释放） | **MEDIUM** |
| 5 | subject 解析逻辑跨模块重复，无共享代码 | **MEDIUM** |

---

## 验收标准

### AC-S5-01: Metadata Prefix 中文检索质量 A/B 对比

**关联决策:** D1 (Frontmatter metadata-as-text prefix)
**验证维度:** 算法效果 — 在真实中文数据上的检索质量影响

- **测试方法:** 对 CS188 vault 中有 frontmatter 的笔记，分两组索引：
  - A 组: plain-text chunks（无 prefix）
  - B 组: metadata-as-text prefix chunks（`Course:{course} Tags:{tags}\n{content}`）
  - 选取 20 个代表性中文查询，对比两组 top-5 命中率和相似度分数分布
- **测试数据:** CS188 vault 真实笔记（必须有 frontmatter 的子集，至少 30 篇）
- **PASS 条件:**
  - B 组 top-5 准确率 >= A 组（不降质）
  - B 组相关/不相关 chunk 的相似度分数间距 >= A 组（区分度不下降）
- **FAIL 条件:**
  - B 组 top-5 准确率比 A 组下降 > 5%
  - 或 B 组的相似度分数分布反而更混淆（相关和不相关 chunk 更难区分）

### AC-S5-02: Metadata Prefix 语言选择验证

**关联决策:** D1
**验证维度:** 中文 vs 英文 metadata prefix 的 embedding 质量差异（**论文未覆盖的盲区**）

- **测试方法:** 对同一批笔记，分三组：
  - A: 英文 prefix (`Course:CS188 Tags:search,AI`)
  - B: 中文 prefix (`课程:CS188 标签:搜索,AI`)
  - C: 中英混合 prefix (`Course:CS188 标签:搜索,AI`)
  - 用 20 个中文查询测试 top-5 命中率
- **测试数据:** 同 AC-S5-01
- **PASS 条件:** 三组中至少有一组 top-5 准确率 >= 无 prefix 的 baseline
- **FAIL 条件:** 所有 prefix 格式都导致中文检索质量下降

### AC-S5-03: LanceDB Pre-filter 性能验证

**关联决策:** D1
**验证维度:** scalar index + LABEL_LIST index 在真实数据量下的查询性能

- **测试方法:**
  - 创建带 `course_id` (scalar index) + `tags` (LABEL_LIST index) 的 LanceDB 表
  - 执行 `.where("course_id = 'CS188'")` + `.search(query_vector)` 组合查询
  - 执行 `.where("array_contains_any(tags, ['搜索', 'AI'])")` + `.search(query_vector)`
  - 测量 P50/P95 延迟
- **测试数据:** 真实 vault 索引后的 LanceDB 表（至少 500 chunks）
- **PASS 条件:** pre-filter + search P95 延迟 < 200ms
- **FAIL 条件:** P95 延迟 > 500ms 或 filter 返回错误结果
- **注意:** 确认 `array_has_any` vs `array_contains_any` 函数名在当前 LanceDB 版本中的正确用法

### AC-S5-04: Frontmatter 解析鲁棒性

**关联决策:** D1
**验证维度:** python-frontmatter 对 Obsidian 笔记的解析成功率

- **测试方法:**
  - 对 vault 中所有 .md 文件运行 python-frontmatter 解析
  - 统计成功/失败比例
  - 对失败文件分析原因（tab 缩进、特殊字符、嵌套 YAML、缺少闭合 `---`）
  - 验证降级策略（路径推断课程名）的准确性
- **测试数据:** CS188 vault 全部 .md 文件
- **PASS 条件:**
  - 解析成功率 >= 95%
  - 降级策略对失败文件的课程推断准确率 >= 90%
- **FAIL 条件:**
  - 解析成功率 < 90%
  - 或降级策略无法正确推断课程名

### AC-S5-05: Wikilink 解析 + List<Utf8> 存储验证

**关联决策:** D2 (Wiki-links LABEL_LIST + 1-hop)
**验证维度:** 端到端解析 → 存储 → 查询的正确性

- **测试方法:**
  - 对 vault 中所有笔记运行 `extract_and_resolve_wikilinks()`
  - 将 outgoing_links 存入 LanceDB `List<Utf8>` 列
  - 创建 LABEL_LIST 索引
  - 执行 `array_contains_any` 查询验证结果
  - 抽样 20 篇笔记人工验证解析准确性
- **测试数据:** CS188 vault 真实笔记
- **PASS 条件:**
  - 解析准确率 >= 95%（抽样人工验证）
  - `array_contains_any` 查询结果与预期一致
  - LABEL_LIST 索引创建无报错
- **FAIL 条件:**
  - 解析准确率 < 90%
  - 或 `array_contains_any` 返回不匹配结果

### AC-S5-06: 1-hop 邻居扩展效果验证

**关联决策:** D2
**验证维度:** 1-hop 扩展对检索质量的实际贡献

- **测试方法:**
  - 选取 15 个查询（5 个简单概念查询 + 5 个跨笔记关联查询 + 5 个前置知识查询）
  - 对比有/无 1-hop 扩展的 recall@10
  - 统计 1-hop 扩展引入的噪音比例（扩展 chunk 中与 query 无关的比例）
- **测试数据:** CS188 vault 真实笔记 + 手工标注的相关性判断
- **PASS 条件:**
  - 跨笔记关联查询的 recall@10 提升 >= 10%
  - 噪音比例 < 25%
- **FAIL 条件:**
  - recall 无提升或下降
  - 或噪音比例 > 40%
- **补充测试:** 对前置知识查询额外测试 2-hop，记录效果差异（为未来架构决策提供数据）

### AC-S5-07: 权重衰减系数合理性

**关联决策:** D2
**验证维度:** 0.7 衰减系数的依据和效果

- **测试方法:** 对比衰减系数 0.5 / 0.7 / 0.9 / 1.0 下的检索质量
- **测试数据:** 同 AC-S5-06
- **PASS 条件:** 0.7 衰减的效果在 top-3 中，且比 1.0（无衰减）效果更好
- **FAIL 条件:** 0.7 的效果显著差于其他系数（说明该值需要调整）

### AC-S5-08: 渐进 Scope 阶段触发分布

**关联决策:** D3 (4阶段 cascade + score threshold)
**验证维度:** threshold 标定和各阶段实际触发比例

- **测试方法:**
  - 用 50 个真实查询运行 4 阶段 cascade
  - 统计各阶段的触发频率
  - 分析 HIGH=0.7, MED=0.5 阈值是否合理
- **测试数据:** CS188 vault + 50 个真实学生问题（或模拟问题）
- **PASS 条件:**
  - Stage1-2 覆盖 >= 70% 查询（大多数查询不需要跨课程）
  - 每个阶段至少被触发 1 次（证明 4 阶段都有存在价值）
  - threshold 不需要超过 ±0.1 的调整
- **FAIL 条件:**
  - > 50% 查询需要 Stage3-4（说明阈值太严或 Stage1-2 检索质量不足）
  - 或某个阶段从未被触发（说明该阶段多余）

### AC-S5-09: 渐进 Scope 端到端延迟

**关联决策:** D3
**验证维度:** worst-case 4 阶段串行的用户体感

- **测试方法:** 测量从查询发起到最终结果返回的端到端延迟
  - best-case: Stage1 即满足
  - worst-case: 串行到 Stage4
- **测试数据:** 同 AC-S5-08
- **PASS 条件:**
  - best-case P95 < 500ms
  - worst-case P95 < 3s
- **FAIL 条件:**
  - worst-case P95 > 5s（用户不可接受）
  - 或 best-case P95 > 1s（基础延迟过高）

### AC-S5-10: 跨课程 Tag 重叠分析

**关联决策:** D4 (Tag Jaccard similarity)
**验证维度:** Jaccard 方案在当前数据上的可行性

- **测试方法:**
  - 统计真实 vault 中所有课程的 tag 集合
  - 计算课程间的 Jaccard 相似度矩阵
  - 分析有意义的 tag 重叠（排除通用 tag 如 "重要"、"复习"）
- **测试数据:** 多课程 vault（如果当前仅 CS188 单课程，则需说明此测试延后）
- **PASS 条件:**
  - 存在 >= 3 对课程有 Jaccard >= 0.1 的有意义 tag 重叠
  - 桥接发现中 >= 60% 被人工判断为有价值的关联
- **FAIL 条件:**
  - 所有课程对的 Jaccard < 0.05（说明 tag 体系太碎片化）
  - 或发现的关联 >= 50% 是无意义的（误报率过高）
- **前提条件:** 需要多课程数据才有测试意义。若仅单课程，此 AC 标记为 DEFERRED

### AC-S5-11: RRF 融合效果验证

**关联决策:** D5 (LanceDB + CLI + RRF)
**验证维度:** RRF(k=60) 双路融合 vs 单路 LanceDB 的检索质量对比

- **测试方法:**
  - 路径 A: 仅 LanceDB hybrid search
  - 路径 B: LanceDB + CLI 图遍历，RRF(k=60) 融合
  - 用 20 个查询对比 NDCG@10 或 top-5 命中率
- **测试数据:** CS188 vault + 手工标注的相关性判断
- **PASS 条件:** RRF 融合后 top-5 命中率 >= 单路 LanceDB（不降质）
- **FAIL 条件:** RRF 融合导致 top-5 命中率下降 > 5%
- **注意:** 若两路结果数量差距极大（如向量 20 个 vs CLI 3 个），记录是否需要归一化处理

### AC-S5-12: CLI 图遍历延迟验证

**关联决策:** D5
**验证维度:** Obsidian CLI backlinks/links 命令的实际响应时间

- **测试方法:**
  - 对 10 篇笔记分别执行 `backlinks` 和 `links` 命令
  - 测量每次调用的延迟
- **测试数据:** CS188 vault 中链接数不同的笔记（高链接密度 + 低链接密度）
- **PASS 条件:** P95 延迟 < 500ms
- **FAIL 条件:** P95 延迟 > 1s 或频繁超时
- **前提条件:** Obsidian 必须运行且 CLI 可用

### AC-S5-13: Agent links 工具使用效率

**关联决策:** D6 (Agent CLI 工具)
**验证维度:** links 命令是否真的是"图遍历必需"

- **测试方法:**
  - 模拟 20 个不同类型的用户问题，让 Agent 自主选择工具
  - 统计 links 工具的实际调用频率和贡献
- **测试数据:** 20 个覆盖不同复杂度的教育问题
- **PASS 条件:** links 工具在 >= 15% 的查询中被有效使用（>= 3/20）
- **FAIL 条件:** links 工具被使用 < 2 次（说明"必需"判断有误）

### AC-S5-14: Schema 迁移可行性

**关联决策:** D1 + D2 (新 LanceDB schema)
**验证维度:** 从现有 schema 到新 schema 的迁移路径

- **测试方法:**
  - 在测试环境中执行 schema 迁移
  - 验证现有数据完整性
  - 验证新索引（scalar + LABEL_LIST）正确创建
  - 验证旧查询接口不被破坏
- **测试数据:** 现有 LanceDB 数据库的副本
- **PASS 条件:**
  - 迁移后数据完整（行数一致、向量数据无损）
  - 新索引正确创建
  - 旧查询（pure vector search）仍然正常工作
- **FAIL 条件:** 数据丢失、索引创建失败、或旧查询被破坏

---

## 验收标准优先级

### P0 — 实施前必须验证（阻塞性）

| AC | 标题 | 理由 |
|----|------|------|
| AC-S5-01 | 中文 metadata prefix A/B | 核心假设：prefix 在中文上有效。ECIR 2026 仅验证英文。 |
| AC-S5-03 | LanceDB pre-filter 性能 | 基础设施：若 filter 性能不达标，整个分层架构不成立 |
| AC-S5-04 | Frontmatter 解析鲁棒性 | 数据入口：若解析失败率高，后续功能全部受影响 |
| AC-S5-05 | Wikilink 解析 + 存储 | 核心管道：wikilink 数据的正确性影响 D2/D3/D5 |
| AC-S5-14 | Schema 迁移可行性 | 基础设施：新 schema 必须可行且不破坏现有功能 |

### P1 — 实施后验证

| AC | 标题 | 理由 |
|----|------|------|
| AC-S5-02 | Prefix 语言选择 | 优化：确定最佳 prefix 格式 |
| AC-S5-06 | 1-hop 扩展效果 | 效果：验证邻居检索的实际价值 |
| AC-S5-08 | 渐进 Scope 触发分布 | 效果：验证 4 阶段设计的合理性 |
| AC-S5-09 | 渐进 Scope 延迟 | 体验：验证用户可接受的延迟范围 |
| AC-S5-11 | RRF 融合效果 | 效果：验证双路融合的增益 |
| AC-S5-12 | CLI 延迟 | 体验：验证 CLI 调用不拖慢系统 |

### P2 — 可延后

| AC | 标题 | 理由 |
|----|------|------|
| AC-S5-07 | 权重衰减系数 | 优化：可用默认值先上线再调整 |
| AC-S5-10 | 跨课程 Tag 重叠 | 前提：需要多课程数据，单课程无法测试 |
| AC-S5-13 | Agent links 使用效率 | 间接：Agent 行为受 prompt 影响大 |

---

## 待录入 Graphiti 记录清单

> Graphiti MCP 在本 session 不可用，以下记录需在 Graphiti 可用时补录。

```
1. add_memory(
     name: "[Session-Start] S5-Review-验证 — A3新功能方案对抗性审查",
     episode_body: "Session：S5-Review | 背景：对S5 brainstorming的6个核心决策进行独立对抗性审查 | 方法：3个并行agent（代码审查+社区调研+论文验证） | 来源文档：brainstorming-session-S5-A3-new-features-2026-03-13.md",
     group_id: "canvas-dev",
     source_description: "session-s5-review-2026-03-14"
   )

2. add_memory(
     name: "[Code-Review] S5代码审查质量评估 — 中等偏宽松，1个事实性错误",
     episode_body: "Session：S5-Review | 背景：独立agent审查S5引用的5个核心文件 | 内容：S5评级3/5准确，lancedb_client.py声称'跳过frontmatter'但实际无任何处理逻辑（CRITICAL），遗漏subject命名规范不一致（HIGH）、cache stampede bug（MEDIUM）、backend已有完整CrossCanvasService（HIGH） | 结论：S5审查为surface级别，不足以支撑adversarial review要求",
     group_id: "canvas-dev",
     source_description: "session-s5-review-2026-03-14"
   )

3. add_memory(
     name: "[Research] S5社区调研验证 — 3处过度简化需修正",
     episode_body: "Session：S5-Review | 内容：独立调研验证6项技术声明。LABEL_LIST/RRF/prefix方向正确但3处过度简化：'零成本'(metadata更新需re-embed)、'无需调参'(k值有数据集敏感性)、'不需要图数据库'(仅限tag过滤场景)。python-frontmatter有Obsidian edge case需处理。1-hop在教育前置知识链场景可能不足。 | 结论：技术选型大方向可行，需在实施中加限定条件",
     group_id: "canvas-dev",
     source_description: "session-s5-review-2026-03-14"
   )

4. add_memory(
     name: "[Research] S5论文验证 — ECIR2026直接用了bge-m3但仅英文",
     episode_body: "Session：S5-Review | 内容：验证5项论文声明。关键发现：ECIR2026论文直接使用bge-m3验证metadata prefix有效（利好），但实验仅限英文SEC文件。GraphRAG Survey的1-hop结论是综述推断非实验结论。Adaptive-RAG三级路由与S5四阶段cascade是不同维度（复杂度vs范围）。中文metadata prefix效果是完全未验证的盲区。 | 结论：论文支撑基本成立但需中文实测",
     group_id: "canvas-dev",
     source_description: "session-s5-review-2026-03-14"
   )

5. add_memory(
     name: "[Acceptance-Criteria] AC-S5-01~14 — A3新功能14项验收标准",
     episode_body: "Session：S5-Review | 内容：为D1~D6六个决策制定14项验收标准。P0阻塞性5项（中文prefix A/B、LanceDB性能、Frontmatter解析、Wikilink存储、Schema迁移），P1实施后6项，P2可延后3项。最关键测试：AC-S5-01中文metadata prefix效果——ECIR2026仅验证英文。 | 文档：acceptance-criteria-S5-A3-new-features-2026-03-14.md",
     group_id: "canvas-dev",
     source_description: "session-s5-review-2026-03-14"
   )

6. add_memory(
     name: "[Session-End] S5-Review-验证 — 完成，14项验收标准已制定",
     episode_body: "Session：S5-Review | 完成：3个并行agent审查完成，14项验收标准已写入文档。 | 未完成：Graphiti记录需补录（MCP不可用）。 | 关键发现：S5有1个事实性错误（frontmatter处理）、3处过度简化、5处代码审查遗漏。 | 后续：实施团队按P0→P1→P2顺序执行验收测试，结果记录[Test]到Graphiti",
     group_id: "canvas-dev",
     source_description: "session-s5-review-2026-03-14"
   )
```

---

## 附录：三方审查 Agent 结果摘要

### Agent 1: 代码对抗性审查

| 文件 | S5评级 | 独立评级 | 一致性 | 关键发现 |
|------|--------|---------|--------|---------|
| context_enrichment_service.py | 🟢 | 🟢(有小问题) | ✅ | cache stampede bug, color mapping 不一致 |
| lancedb_client.py | "跳过frontmatter" | ⛔ 事实错误 | ❌ | 无任何frontmatter处理，YAML当内容索引 |
| cross_canvas_retriever.py | 🔴 | 🔴 | ✅ | backend已有完整CrossCanvasService(S5遗漏) |
| subject_resolver+config | 🟡 | 🟡(有重复) | ⚠️ | hyphens vs underscores命名不一致 |
| planning_utils.py | "20行参考" | 🟢 | ✅ | 是build工具非RAG管道内 |

### Agent 2: 社区调研

| 声明 | 验证 | 风险 | 关键修正 |
|------|------|------|---------|
| LABEL_LIST + array_has_any | 部分支持 | 中 | 函数名确认+scope限定 |
| RRF k=60 无需调参 | 部分支持 | 低 | k=60安全但"无需调参"过于绝对 |
| Metadata prefix 零成本 | 部分支持 | 中 | 效果有支撑但更新需re-embed |
| python-frontmatter | 支持 | 低 | Obsidian edge case需处理 |
| 1-hop足够 | 部分支持 | 中 | 教育前置知识链可能需2-hop |
| RRF替代LLM自选 | 支持 | 低 | 社区共识一致 |

### Agent 3: 论文验证

| 论文 | 验证 | 适用性 | 关键差异 |
|------|------|--------|---------|
| ECIR 2026 prefix | 准确 | 中-高 | **直接用了bge-m3**但仅英文 |
| GraphRAG Survey 1-hop | 部分准确 | 中 | 综述推断非实验结论 |
| Adaptive-RAG 三级 | 准确 | 中 | S5用不同分级维度 |
| bge-m3 兼容性 | 准确 | 中-高 | 中文prefix是未验证盲区 |
| RRF k=60 | 准确 | 高 | 原始论文pilot investigation确定 |
