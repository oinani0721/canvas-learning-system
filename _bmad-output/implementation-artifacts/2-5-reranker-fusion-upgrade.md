# Story 2.5: Phase 1 — 精排与融合升级

Status: ready-for-dev

## Story

As a 用户,
I want 搜索结果经过精排和智能融合，最相关的内容排在最前面,
so that AI 能用最相关的内容回答我的问题。

## Acceptance Criteria

1. **AC-1: 3 组分层 RRF 融合（Dense 组 / Graph 组 / Personal 组，k=60）+ z-score 跨组归一化**
   - **Given** 6 路搜索通道返回各自结果（Story 2.2 已修复全部通道）
   - **When** 结果进入融合阶段
   - **Then** 6 路结果按语义相似度分为 3 个逻辑组：
     - Dense 组：LanceDB Dense 向量搜索 + LanceDB Sparse 关键词搜索
     - Graph 组：Graphiti 知识图谱搜索 + Obsidian CLI 图遍历（backlinks/links）
     - Personal 组：Vault 笔记搜索 + 图片搜索
   - **And** 每组内部先执行 RRF 融合（k=60），产出组内排序
   - **And** 跨组使用 z-score 归一化：`z = (score - mean) / std`，使三组分数可比
   - **And** 归一化后的跨组分数合并排序，产出最终融合结果
   - **And** 分层融合优于扁平 RRF（验证 F1 提升 >= +1%，参考 HF-RAG 论文 arXiv:2509.02837）
   - **FR 覆盖**: FR-RET-05, FR-RET-P-05

2. **AC-2: bge-reranker fp16 精排，延迟 < 200ms（CPU，top-20）**
   - **Given** 分层 RRF 融合后的候选结果列表（top-20 ~ top-30）
   - **When** rerank_results 节点执行精排
   - **Then** 升级 `LocalReranker` 模型从 bge-reranker-base（102M）到 gte-reranker-modernbert-base（149M，架构文档确认选型）
   - **And** 模型以 fp16 精度加载（`torch.float16`），减少显存占用和推理延迟
   - **And** 使用 `asyncio.to_thread` 包装同步推理调用（替换 `loop.run_in_executor`）
   - **And** 精排延迟 < 200ms（CPU 环境，输入 top-20 候选文档）
   - **And** 模型采用懒加载单例模式（首次调用时加载，后续复用）
   - **And** 精排后结果按 reranker 分数降序排列，score 字段为 reranker 真实分数
   - **And** `sentence-transformers` 未安装时 log warning 并 fallback 为融合排序（不崩溃）
   - **FR 覆盖**: FR-RET-10, FR-RET-P-06

3. **AC-3: Adaptive-k 分数断崖自动截取**
   - **Given** 精排后的有序结果列表（按 reranker 分数降序）
   - **When** Adaptive-k 算法执行
   - **Then** 计算相邻文档分数差（gap_i = score_i - score_{i+1}）
   - **And** 找到最大 gap 位置 max_gap_idx，截取点 = max_gap_idx + 1 + buffer（buffer B=5）
   - **And** 截取点受上下界约束：min_k=3，max_k=15
   - **And** 简单问题（分数集中在高区间）自动少返回（如 3-5 条）
   - **And** 复杂问题（分数分散）自动多返回（如 10-15 条）
   - **And** 所有文档分数相同或差异极小时（max_gap < epsilon），返回 max_k 条
   - **FR 覆盖**: FR-RET-P-07

4. **AC-4: 精排后 MRR 提升 >= +0.10**
   - **Given** 完成分层 RRF + 精排 + Adaptive-k 全链路升级
   - **When** 使用 20+ 真实查询（含中英文）执行 A/B 对比
   - **Then** 精排后 MRR@10 相比精排前（RRF 排序）提升 >= +0.10
   - **And** 中文查询和英文查询的精排提升幅度无显著差异
   - **And** 精排不引入新的延迟瓶颈（总检索延迟仍 < 3s）
   - **FR 覆盖**: FR-RET-05, FR-RET-10

5. **AC-5: 配置化与可观测性**
   - **Given** 精排与融合管道运行中
   - **When** 查看日志和配置
   - **Then** RRF k 值、分组映射、Adaptive-k buffer、reranker 模型名均从 config 读取
   - **And** 每次精排记录日志：输入文档数、输出文档数、延迟 ms、top-3 分数、Adaptive-k 截取点
   - **And** 分层 RRF 每组的文档数和组内 top-1 分数有日志记录
   - **And** 配置变更无需重启服务（下次搜索自动生效）

## Tasks / Subtasks

- [ ] **Task 1: 分层 RRF 融合重构** (AC: #1)
  - [ ] 1.1 在 `src/agentic_rag/nodes.py` 中新增 `_fuse_layered_rrf()` 函数，替换现有 `_fuse_rrf_multi_source()`：
    - 定义 3 组映射：`FUSION_GROUPS = {"dense": ["lancedb_dense", "lancedb_sparse"], "graph": ["graphiti", "cross_canvas"], "personal": ["vault_notes", "multimodal"]}`
    - 组映射从 config 读取，支持运行时调整
  - [ ] 1.2 实现组内 RRF 融合：对每组内的通道结果执行 `score = sum(1/(k+rank))`，k=60，组内结果按 RRF 分数降序排列
  - [ ] 1.3 实现 z-score 跨组归一化：
    - 对每组的 RRF 分数集合计算 mean 和 std
    - `z_score = (rrf_score - mean) / std`（std=0 时设 z_score=0，避免除零）
    - 三组归一化后的结果合并排序
  - [ ] 1.4 在 `fuse_results` 节点中根据 `fusion_strategy` 路由：`"layered_rrf"` 调用新函数，`"rrf"` 保留旧实现作为 fallback
  - [ ] 1.5 更新 `CanvasRAGConfig` 添加 `fusion_strategy: "layered_rrf"` 作为新的默认值
  - [ ] 1.6 添加分层融合日志：记录每组文档数、组内 top-1 RRF 分数、归一化后 top-1 z-score

- [ ] **Task 2: Reranker 模型升级** (AC: #2)
  - [ ] 2.1 修改 `src/agentic_rag/reranking.py` 中 `LocalReranker.__init__` 的默认模型参数：
    - 从 `"BAAI/bge-reranker-base"` 改为 `"Alibaba-NLP/gte-reranker-modernbert-base"`（架构文档确认选型，149M 参数）
    - 添加 `torch_dtype` 参数，默认 `torch.float16`
  - [ ] 2.2 修改 `CrossEncoder` 初始化，传入 `model_args={"torch_dtype": torch.float16}` 启用 fp16 推理
  - [ ] 2.3 替换 `loop.run_in_executor` 为 `asyncio.to_thread`（Python 3.9+ 标准方式，更简洁安全）
  - [ ] 2.4 实现懒加载单例：模块级 `_reranker_instance: Optional[LocalReranker] = None` + `get_reranker()` 工厂函数
  - [ ] 2.5 在 `_rerank_local` 函数中（`nodes.py`）调用 `get_reranker().rerank_search_results()`，确认 Story 2.2 已完成基础接入
  - [ ] 2.6 模型名从 `CanvasRAGConfig` 读取（新增 `reranker_model_name` 字段），支持运行时切换
  - [ ] 2.7 添加启动日志：模型名、设备（CPU/CUDA）、精度（fp16/fp32）、参数量

- [ ] **Task 3: Adaptive-k 动态截取** (AC: #3)
  - [ ] 3.1 在 `src/agentic_rag/nodes.py` 新增 `_adaptive_k_truncate()` 函数：
    ```python
    def _adaptive_k_truncate(
        results: List[SearchResult],
        buffer: int = 5,
        min_k: int = 3,
        max_k: int = 15,
        epsilon: float = 0.01
    ) -> List[SearchResult]:
    ```
  - [ ] 3.2 实现最大 gap 检测算法：
    - 计算相邻分数差 `gaps = [results[i]["score"] - results[i+1]["score"] for i in range(len-1)]`
    - 找到 `max_gap_idx = argmax(gaps)`
    - 截取点 `cut = min(max(max_gap_idx + 1 + buffer, min_k), max_k)`
  - [ ] 3.3 处理边界情况：
    - 结果数 <= min_k：全部返回
    - 所有 gap < epsilon：返回 max_k 条（分数无显著断崖）
    - 只有 1 个结果：直接返回
  - [ ] 3.4 在 `rerank_results` 节点中，精排后调用 `_adaptive_k_truncate()` 截取最终结果
  - [ ] 3.5 Adaptive-k 的 buffer、min_k、max_k 参数从 config 读取（新增 `adaptive_k_buffer`、`adaptive_k_min`、`adaptive_k_max` 字段）
  - [ ] 3.6 添加日志：截取点位置、max_gap 值、最终返回数量

- [ ] **Task 4: 配置更新与集成** (AC: #5)
  - [ ] 4.1 更新 `src/agentic_rag/config.py` 的 `CanvasRAGConfig`，新增字段：
    - `reranker_model_name: str`（默认 `"Alibaba-NLP/gte-reranker-modernbert-base"`）
    - `reranker_torch_dtype: str`（默认 `"float16"`）
    - `fusion_groups: Dict[str, List[str]]`（默认 3 组映射）
    - `adaptive_k_buffer: int`（默认 5）
    - `adaptive_k_min: int`（默认 3）
    - `adaptive_k_max: int`（默认 15）
  - [ ] 4.2 更新 `DEFAULT_CONFIG` 中的默认值
  - [ ] 4.3 更新 `fusion_strategy` Literal 类型，添加 `"layered_rrf"` 选项
  - [ ] 4.4 确保新增配置字段通过 `merge_config()` 正确合并

- [ ] **Task 5: 端到端验证** (AC: #1-#5)
  - [ ] 5.1 准备 20+ 测试查询（含中英文混合），执行完整管道（6 路搜索 → 分层 RRF → 精排 → Adaptive-k）
  - [ ] 5.2 A/B 对比验证：
    - 分层 RRF vs 扁平 RRF：验证 F1 提升 >= +1%
    - 精排后 vs 精排前：验证 MRR@10 提升 >= +0.10
  - [ ] 5.3 Adaptive-k 行为验证：
    - 简单查询（明确匹配）：返回 3-5 条
    - 复杂查询（模糊匹配）：返回 10-15 条
    - 记录每个查询的截取点和 max_gap
  - [ ] 5.4 性能验证：
    - 精排延迟 < 200ms（CPU，top-20 输入）
    - 总检索延迟 < 3s（NFR-PERF-04）
  - [ ] 5.5 `ruff check src/agentic_rag/` 全量 lint 通过
  - [ ] 5.6 `ruff format --check src/agentic_rag/` 格式检查通过
  - [ ] 5.7 确认无 mock 数据、无 TODO 空函数、无假实现（DD-03）

## Dev Notes

### Brownfield 上下文——已有代码资产

这是 **Brownfield 项目**，精排和融合的框架已存在但功能不完整。Story 2.2 已完成基础修复（reranker 接入、CRAG 修复），本 Story 在此基础上升级。

#### 关键文件清单

| 文件 | 当前状态（Story 2.2 完成后） | 本 Story 修改 |
|------|---------------------------|--------------|
| `src/agentic_rag/nodes.py` | `_rerank_local` 已接入 `LocalReranker`（bge-reranker-base），`fuse_results` 使用扁平 RRF | 重构融合为分层 RRF + 新增 Adaptive-k 截取 |
| `src/agentic_rag/reranking.py` | `LocalReranker` 使用 bge-reranker-base（102M） | 升级模型为 gte-reranker-modernbert-base（149M，fp16），懒加载单例 |
| `src/agentic_rag/config.py` | `CanvasRAGConfig` 有 `fusion_strategy`、`reranking_strategy` | 新增 reranker 模型名、fusion_groups、Adaptive-k 参数 |
| `src/agentic_rag/state.py` | `SearchResult` TypedDict 和 `CanvasRAGState` 定义完整 | **无需修改** |
| `src/agentic_rag/state_graph.py` | LangGraph 图构建完整 | **无需修改**（图结构不变，只修改节点实现） |

#### Reranker 选型说明

**架构文档（2026-03-16）确认选型**：`gte-reranker-modernbert-base`（Alibaba-NLP，149M 参数）
- 相比后端 PRD 中的 `bge-reranker-v2-m3`（568M），模型更轻量（149M vs 568M），推理更快
- Hit@1=83%（架构文档数据），延迟 424ms（架构文档数据，CPU 环境），fp16 可进一步加速
- 备选方案：Qwen3-4B（架构文档记录），性能更强但显存需求更高，Phase 2 评估
- 后端 PRD 中的 `bge-reranker-v2-m3` 作为中间方案保留参考

**注意**：后端 PRD（任务 1.6）写的是 `bge-reranker-v2-m3 fp16`，但架构文档（决策 #2）已更新为 `gte-reranker-modernbert-base`。以架构文档为准。如果 gte-reranker 在真实数据上表现不佳（AC-4 不达标），可回退到 bge-reranker-v2-m3。

#### 分层 RRF 分组原理

| 组名 | 搜索通道 | 语义定位 |
|------|---------|---------|
| Dense 组 | LanceDB Dense + LanceDB Sparse | 笔记内容的语义和关键词匹配 |
| Graph 组 | Graphiti + Obsidian CLI | 知识图谱结构和链接关系 |
| Personal 组 | Vault 笔记搜索 + 图片搜索 | 用户个人笔记和多模态内容 |

分层优于扁平的原因：同组内的通道语义相近（如 Dense+Sparse 都是笔记内容匹配），组内 RRF 融合合理；不同组的通道语义差异大（笔记内容 vs 知识图谱 vs 个人数据），直接扁平 RRF 会导致分数域不匹配。z-score 归一化解决跨组分数可比性问题。

参考：HF-RAG 论文 arXiv:2509.02837 验证分层融合优于扁平 +3% F1。

#### Adaptive-k 原理

传统固定 top-5 的问题：简单问题返回太多无关结果（浪费 token），复杂问题返回太少（遗漏相关内容）。

Adaptive-k 通过分数断崖检测自动决定返回数量：
- 分数断崖（大 gap）= 相关与不相关的自然分界
- buffer（B=5）提供容错余量
- min_k=3 / max_k=15 防止极端情况

参考：EMNLP 2025 Megagon Labs 验证 Adaptive-k 减少 99% 无用 token。

### 依赖关系

- **前置 Story 2.2**（搜索通道修复）：必须先完成，确保 6/6 通道返回数据、reranker 基础接入可工作
- **前置 Story 2.3**（bge-m3 迁移）：建议先完成，确保 Dense 向量为 1024d，但非强制依赖（本 Story 不修改 embedding）
- **前置 Story 2.4**（中文搜索）：建议先完成，确保 Sparse 通道有中文支持，但非强制依赖
- **后续 Story 2.6**（CRAG 质量门控）：依赖本 Story 的精排分数作为质量评估输入
- **后续 Story 2.11**（参数可配置化）：扩展本 Story 新增的配置项到完整可配置体系

### 不做的事项（防蔓延 DD-10）

- 不修改 embedding 模型（Story 2.3 的范围）
- 不修改分块策略（Story 2.3 的范围）
- 不实现 CRAG 质量门控升级（Story 2.6 的范围）
- 不实现上下文压缩（Story 2.10 的范围）
- 不实现文件指纹增量索引（Story 2.7 的范围）
- 不修改前端代码（纯后端管道升级）
- 不修改 LangGraph 图结构（只修改节点实现）
- 不实现 ColBERT 三模态评估（Phase 2+ 范围）
- 不实现查询改写升级（Story 2.6 的范围）

### Project Structure Notes

- 本 Story 修改范围限于 `src/agentic_rag/` 目录（nodes.py、reranking.py、config.py）
- `src/agentic_rag/state.py` 和 `src/agentic_rag/state_graph.py` 不需要修改
- gte-reranker-modernbert-base 模型需要确认 `requirements.txt` 中 `sentence-transformers` 版本 >= 3.0（支持 ModernBERT 架构）
- 新增的 `fusion_groups` 配置项为加法编辑，不影响现有配置兼容性
- Adaptive-k 是新增功能模块，不修改任何已有函数签名

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#已确定的技术基础] — Reranker 选型：gte-reranker-modernbert-base（149M）
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision Priority Analysis] — Reranker Important Decision 确认
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#Phase 1] — 任务 1.6（Reranker 升级）、1.8（分层融合）
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#关键技术选型] — 融合策略：3 组分层 RRF k=60 + z-score
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#关键技术选型] — Adaptive-k：EMNLP 2025 Megagon Labs
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.5] — Story 需求和 AC
- [Source: _bmad-output/brainstorming/brainstorming-session-S3-pipeline-postprocessing-2026-03-12.md] — S3 分层融合和 Reranker 升级方案
- [Source: _bmad-output/brainstorming/brainstorming-session-S7-A2-reranking-crag-2026-03-13.md] — A2 Reranker 接入细节
- [Source: _bmad-output/brainstorming/a2-review-verification-report-2026-03-13.md] — bge-reranker-v2-m3 社区验证报告
- [Source: src/agentic_rag/nodes.py] — 核心节点实现（fuse_results + rerank_results）
- [Source: src/agentic_rag/reranking.py] — 已实现的 LocalReranker / CohereReranker / HybridReranker
- [Source: src/agentic_rag/config.py] — CanvasRAGConfig 定义
- [Source: src/agentic_rag/state.py] — SearchResult TypedDict 定义

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
