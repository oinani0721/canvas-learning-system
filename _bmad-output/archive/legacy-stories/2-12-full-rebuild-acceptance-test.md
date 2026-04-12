# Story 2.12: 全量重建索引与验收测试

Status: ready-for-dev

## Story

As a 开发者,
I want 用 50+ 真实查询的 Golden Test Set 验收检索管道质量,
so that 确认管道升级后达到生产标准。

## Acceptance Criteria

1. **AC-1: Golden Test Set 构建（50+ 真实查询）**
   - **Given** 需要验收 Phase 0-2 全部升级效果
   - **When** 构建 Golden Test Set
   - **Then** 包含 50+ 真实查询，覆盖以下场景：
     - 中文知识点查询（>= 15 条）
     - 英文知识点查询（>= 15 条）
     - 跨语言混合查询（>= 5 条）
     - 模糊/宽泛查询（>= 5 条）
     - 精确文件定位查询（>= 5 条）
     - 应该触发降级的无关查询（>= 5 条）
   - **And** 每条查询标注 ground truth：期望命中的文件路径 + 分块 heading
   - **And** Golden Test Set 以 JSON/YAML 文件形式持久化到 `tests/golden_test_set.yaml`

2. **AC-2: MRR@10 >= 0.70**
   - **Given** 完成全量重建索引后
   - **When** 对 Golden Test Set 执行批量检索
   - **Then** Mean Reciprocal Rank @10 达到 >= 0.70
   - **And** 即：最相关的结果平均排在前 1-2 位
   - **And** MRR 按中文/英文分别统计，两者均达标

3. **AC-3: Precision@5 >= 0.70**
   - **Given** 完成全量重建索引后
   - **When** 对 Golden Test Set 执行批量检索
   - **Then** Precision @5 达到 >= 0.70
   - **And** 即：搜到的前 5 条结果中，至少 3.5 条是真正相关的
   - **And** Precision 按中文/英文分别统计，两者均达标

4. **AC-4: Recall@10 >= 0.80**
   - **Given** 完成全量重建索引后
   - **When** 对 Golden Test Set 执行批量检索
   - **Then** Recall @10 达到 >= 0.80
   - **And** 即：真正相关的内容，80% 能被搜到
   - **And** Recall 按中文/英文分别统计，两者均达标

5. **AC-5: 全量重建性能**
   - **Given** vault 中有 120 个 markdown 文件
   - **When** 执行全量重建索引
   - **Then** 全量重建 < 30s GPU / < 2min CPU
   - **And** 重建过程有进度日志（每 10 个文件输出一次进度）
   - **And** 重建完成后 FTS 索引正确创建
   - **And** 重建完成后 fingerprint 表完整（120 条记录）

6. **AC-6: Reranker 延迟验收**
   - **Given** 精排管道使用 gte-reranker-modernbert-base
   - **When** 对 top-20 候选文档执行精排
   - **Then** 精排延迟 < 200ms（CPU 环境）
   - **And** 精排后 MRR 相比精排前提升 >= +0.10

7. **AC-7: CRAG 健康触发率验收**
   - **Given** 50+ 查询的验收测试
   - **When** 统计 CRAG 质量门控触发率
   - **Then** CRAG 触发率（判为 "low" 的比例）在 15-30% 之间
   - **And** 无关查询 100% 触发安全降级
   - **And** 相关查询 < 5% 误触发

8. **AC-8: 中文查询效果验收**
   - **Given** Golden Test Set 中的中文查询子集
   - **When** 执行批量检索
   - **Then** 中文查询的 MRR/Precision/Recall 与英文查询无显著差异（差距 < 0.10）
   - **And** jieba 中文分词正确工作（FTS 通道能命中中文关键词）

9. **AC-9: 验收报告输出**
   - **Given** 验收测试执行完成
   - **When** 生成验收报告
   - **Then** 报告包含：总体指标（MRR/Precision/Recall）、分语言指标、分场景指标、Reranker 延迟、CRAG 触发率
   - **And** 报告以 JSON 格式保存到 `tests/acceptance_report.json`
   - **And** 不达标的指标高亮标注

## Tasks / Subtasks

- [ ] **Task 1: Golden Test Set 构建** (AC: #1)
  - [ ] 1.1 分析当前 vault 中的真实笔记内容，为每个查询场景设计 ground truth
  - [ ] 1.2 构建 YAML 格式的 Golden Test Set：
    ```yaml
    queries:
      - id: "cn-01"
        query: "贝叶斯定理的推导过程"
        language: "zh"
        category: "knowledge_point"
        ground_truth:
          - file: "probability/bayes.md"
            heading: "推导"
          - file: "probability/bayes.md"
            heading: "定义"
    ```
  - [ ] 1.3 确保覆盖 AC-1 中列出的所有场景类型
  - [ ] 1.4 保存到 `tests/golden_test_set.yaml`

- [ ] **Task 2: 验收测试框架** (AC: #2-#4, #8)
  - [ ] 2.1 新增 `tests/test_acceptance.py`：批量执行 Golden Test Set 查询
  - [ ] 2.2 实现 MRR@k 计算函数：
    ```python
    def mrr_at_k(results: List[SearchResult], ground_truth: List[Dict], k: int = 10) -> float
    ```
  - [ ] 2.3 实现 Precision@k 计算函数：
    ```python
    def precision_at_k(results: List[SearchResult], ground_truth: List[Dict], k: int = 5) -> float
    ```
  - [ ] 2.4 实现 Recall@k 计算函数：
    ```python
    def recall_at_k(results: List[SearchResult], ground_truth: List[Dict], k: int = 10) -> float
    ```
  - [ ] 2.5 ground truth 匹配逻辑：搜索结果的 `canvas_file` 包含 ground truth 的 `file`，且 `heading` 匹配（模糊匹配，允许包含关系）
  - [ ] 2.6 按语言和场景分别计算指标

- [ ] **Task 3: 全量重建与性能测试** (AC: #5)
  - [ ] 3.1 调用 Story 2.7 实现的 `rebuild_index` 方法执行全量重建
  - [ ] 3.2 记录重建耗时、文件数、分块数
  - [ ] 3.3 验证 fingerprint 表完整性（记录数 == 文件数）
  - [ ] 3.4 验证 FTS 索引可用（执行关键词搜索确认命中）

- [ ] **Task 4: Reranker 延迟测试** (AC: #6)
  - [ ] 4.1 对 20 个查询分别执行精排，记录每次延迟
  - [ ] 4.2 计算 P50/P95/P99 延迟
  - [ ] 4.3 A/B 对比：精排前后的 MRR 差异
  - [ ] 4.4 验证延迟 < 200ms（CPU 环境）

- [ ] **Task 5: CRAG 触发率测试** (AC: #7)
  - [ ] 5.1 统计所有查询的 CRAG 质量评分结果
  - [ ] 5.2 计算触发率（被判为 "low" 的查询比例）
  - [ ] 5.3 验证无关查询的安全降级行为
  - [ ] 5.4 验证相关查询的误触发率

- [ ] **Task 6: 验收报告生成** (AC: #9)
  - [ ] 6.1 新增 `generate_acceptance_report(results: Dict) -> Dict` 函数
  - [ ] 6.2 报告结构：
    ```json
    {
      "timestamp": "...",
      "overall": {"mrr_10": 0.75, "precision_5": 0.72, "recall_10": 0.83},
      "by_language": {"zh": {...}, "en": {...}},
      "by_category": {"knowledge_point": {...}, "fuzzy": {...}, ...},
      "reranker": {"p50_ms": 120, "p95_ms": 180, "mrr_improvement": 0.12},
      "crag": {"trigger_rate": 0.22, "false_positive_rate": 0.03},
      "rebuild": {"duration_ms": 25000, "total_files": 120, "total_chunks": 1500},
      "pass": true,
      "failed_criteria": []
    }
    ```
  - [ ] 6.3 不达标的指标在 `failed_criteria` 中列出
  - [ ] 6.4 保存到 `tests/acceptance_report.json`

- [ ] **Task 7: 端到端验收执行** (AC: #1-#9)
  - [ ] 7.1 执行完整验收流程：全量重建 → Golden Test Set 批量查询 → 指标计算 → 报告生成
  - [ ] 7.2 验证所有指标达标：
    - MRR@10 >= 0.70
    - Precision@5 >= 0.70
    - Recall@10 >= 0.80
    - 中文/英文指标差距 < 0.10
    - Reranker 延迟 < 200ms
    - CRAG 触发率 15-30%
  - [ ] 7.3 如不达标：分析失败查询，定位问题模块，生成改进建议
  - [ ] 7.4 `ruff check src/agentic_rag/ tests/` 全量 lint 通过
  - [ ] 7.5 确认无 mock 数据、无 TODO 空函数、无假实现（DD-03）

## Dev Notes

### Brownfield 上下文——已有代码资产

这是 **Brownfield 项目**的最终验收 Story。Phase 0-2 的所有修复和升级在此汇总验收。本 Story 主要是测试和验收，不修改管道逻辑。

#### 关键文件清单

| 文件 | 当前状态 | 本 Story 修改内容 |
|------|---------|-----------------|
| 新建 `tests/golden_test_set.yaml` | 不存在 | **新建：Golden Test Set** |
| 新建 `tests/test_acceptance.py` | 不存在 | **新建：验收测试脚本** |
| 新建 `tests/acceptance_report.json` | 不存在 | **新建：验收报告（测试生成）** |
| `src/agentic_rag/clients/lancedb_client.py` | Story 2.7 已实现 rebuild_index | **调用，不修改** |
| `src/agentic_rag/nodes.py` | 完整管道节点 | **不修改，只验收** |

#### 验收标准来源

后端 PRD 验收标准（经过社区/论文验证）：

| 标准 | 来源 | 说明 |
|------|------|------|
| MRR@10 >= 0.70 | RAG 生产验收标准（Session A 调研确认） | 最相关结果平均排前 1-2 位 |
| Precision@5 >= 0.70 | RAG 生产验收标准 | 前 5 条结果中 3.5+ 条相关 |
| Recall@10 >= 0.80 | RAG 生产验收标准 | 相关内容 80% 能被搜到 |
| Reranker 延迟 < 200ms | NFR-RET-PERF-02 | CPU 环境，top-20 输入 |
| 全量重建 < 2min CPU | NFR-RET-PERF-04 | 120 文件 |
| CRAG 触发率 15-30% | 管道健康指标 | 当前 100% 误触发已修复 |

### 依赖关系

- **前置 Story 2.1-2.11**（所有 Phase 0-2 Story）：本 Story 验收全部升级效果
- **关键前置 Story 2.7**：全量重建按钮在 2.7 实现
- **关键前置 Story 2.5**：精排在 2.5 实现
- **关键前置 Story 2.6**：CRAG 在 2.6 实现

### 技术决策

1. **Golden Test Set 格式**：YAML（人类可读 + 可维护），而非硬编码在测试代码中。
2. **指标计算**：自行实现（MRR/Precision/Recall 计算逻辑简单，不引入 RAGAS 等重型依赖）。
3. **验收报告**：JSON 格式（机器可读 + 可追踪），不生成 Markdown 报告（避免 DD-10）。
4. **ground truth 匹配**：模糊匹配（file path 包含 + heading 包含），允许索引路径格式差异。

### 关键代码位置

| 组件 | 文件路径 |
|------|---------|
| 全量重建 | `src/agentic_rag/clients/lancedb_client.py`（`rebuild_index`） |
| 搜索入口 | `src/agentic_rag/clients/lancedb_client.py`（`search`） |
| 完整管道 | `src/agentic_rag/state_graph.py`（`build_canvas_agentic_rag_graph`） |
| 精排 | `src/agentic_rag/nodes.py`（`rerank_results`） |
| CRAG | `src/agentic_rag/nodes.py`（`check_quality`） |
| 配置 | `src/agentic_rag/config.py`（`CanvasRAGConfig`） |

### 不做的事项（防蔓延 DD-10）

- 不修改管道逻辑（本 Story 只做验收测试）
- 不实现自动化 CI/CD 集成（手动执行验收即可）
- 不实现 A/B 测试框架
- 不生成 Markdown 验收文档
- 不修改前端代码
- 如指标不达标，本 Story 只定位问题和生成建议，修复在单独的 bugfix Story 中

### FR 覆盖映射

本 Story 不覆盖新的 FR，而是验收 Story 2.1-2.11 覆盖的所有 FR 的最终效果。

### Project Structure Notes

- 新建文件位于 `tests/` 目录
- Golden Test Set 需要根据实际 vault 内容构建（不能是虚构数据）
- 验收报告是测试产出物，不提交到主分支（或加入 .gitignore）
- 验收测试脚本可独立运行（`python tests/test_acceptance.py`），不依赖 pytest 框架

### References

- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#成功标准] — 检索质量指标定义
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#验收标准来源] — 指标来源（社区/论文）
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#Phase 1 验证门控] — 50+ 真实查询 Golden Test Set
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.12] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md] — 检索管道完整架构
- [Source: src/agentic_rag/] — 完整管道代码

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
