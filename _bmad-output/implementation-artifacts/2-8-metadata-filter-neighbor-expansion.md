# Story 2.8: Phase 2 — 元数据过滤与邻居扩展

Status: ready-for-dev

## Story

As a 用户,
I want 搜索能按课程/标签过滤范围，并自动扩展到相关链接的笔记,
so that 搜索结果更精准且不遗漏关联内容。

## Acceptance Criteria

1. **AC-1: Frontmatter 元数据解析与 LanceDB 列存储**
   - **Given** 用户的笔记有 YAML Frontmatter（如 `course: CS188`、`tags: [search, AI]`）
   - **When** 索引管道处理笔记文件
   - **Then** 正确解析 Frontmatter 中的 `course`、`tags`、`category` 等字段
   - **And** 解析结果作为 LanceDB 表的独立列存储（非嵌入 metadata_json）
   - **And** 不含 Frontmatter 的笔记正常索引（元数据字段为空/默认值）
   - **And** Frontmatter 格式异常时（语法错误）跳过元数据提取但仍索引内容，记录 warning 日志

2. **AC-2: 按课程/标签前置过滤**
   - **Given** 用户在某个学科白板中搜索
   - **When** 搜索请求携带 `course_id` 和/或 `tags` 过滤参数
   - **Then** LanceDB 搜索时使用 `where` 子句前置过滤（不是后置过滤）
   - **And** 过滤后再执行向量搜索和关键词搜索
   - **And** 无过滤参数时搜索全量数据（不影响现有行为）
   - **And** 过滤条件组合：course 精确匹配 AND tags 包含匹配

3. **AC-3: 渐进范围搜索（4 阶段级联）**
   - **Given** 用户在课程 CS188 中搜索
   - **When** 同课程搜索结果不足（低于阈值数量）
   - **Then** 自动级联扩展搜索范围：
     1. 阶段 1：同课程（`course = 'CS188'`）
     2. 阶段 2：相关课程（Tag Jaccard 相似度 > 0.3 的课程）
     3. 阶段 3：同学科大类（手动分类或推断）
     4. 阶段 4：全库搜索（无过滤）
   - **And** 每个阶段的结果带有 `scope_level` 标记（便于融合时加权）
   - **And** 当某阶段结果已充足（>= min_results）时停止扩展

4. **AC-4: Wiki-links 1-hop 邻居扩展**
   - **Given** 搜索返回笔记 A，且 A 中包含 `[[笔记B]]` 和 `[[笔记C]]` 的 Wiki-links
   - **When** 邻居扩展执行
   - **Then** 自动将笔记 B 和 C 的相关分块纳入候选结果（1-hop 扩展）
   - **And** 邻居分块的分数进行衰减（如乘以 0.7），避免邻居结果排在直接命中之前
   - **And** 最多扩展 N 个邻居文件（默认 5，可配置），防止结果爆炸
   - **And** 邻居扩展结果在搜索结果中标记 `source_type: "neighbor_expansion"`

5. **AC-5: 跨课程 Tag Jaccard 桥接**
   - **Given** 用户开启跨课程桥接（配置项）
   - **When** 搜索执行
   - **Then** 计算当前课程与其他课程的 Tag Jaccard 相似度
   - **And** Jaccard 系数 > 0.3 的课程纳入相关课程范围
   - **And** 桥接功能可在配置中关闭（默认关闭，用户手动开启）

## Tasks / Subtasks

- [ ] **Task 1: Frontmatter 解析与 LanceDB Schema 扩展** (AC: #1)
  - [ ] 1.1 在 `src/agentic_rag/clients/lancedb_client.py` 的 `_split_md_by_heading` 或索引流程中新增 Frontmatter 解析逻辑：使用 Python `yaml.safe_load` 解析文件开头的 `---` 块
  - [ ] 1.2 提取字段：`course: str`、`tags: List[str]`（存为逗号分隔字符串）、`category: str`
  - [ ] 1.3 扩展 `add_documents` 中的 lance_doc schema，新增 `course`、`tags_str`、`category` 列
  - [ ] 1.4 Frontmatter 解析异常保护：`try/except` 包裹 yaml 解析，异常时 warning 日志 + 使用空默认值
  - [ ] 1.5 确保新增列不破坏已有表的向后兼容性（LanceDB 支持 schema evolution 或需要 migrate）

- [ ] **Task 2: 按课程/标签前置过滤** (AC: #2)
  - [ ] 2.1 修改 `src/agentic_rag/clients/lancedb_client.py` 的 `search` 和 `_search_internal` 方法：新增 `course_filter: Optional[str]` 和 `tags_filter: Optional[List[str]]` 参数
  - [ ] 2.2 构建 LanceDB `where` 子句：`course = '{course_filter}'` AND/OR `tags_str LIKE '%{tag}%'`
  - [ ] 2.3 在 LanceDB 向量搜索 API 中传入 `where` 参数实现前置过滤
  - [ ] 2.4 在 FTS 搜索中同样应用过滤条件
  - [ ] 2.5 无过滤参数时不附加 `where` 子句（保持现有行为）

- [ ] **Task 3: 渐进范围搜索** (AC: #3)
  - [ ] 3.1 新增 `_progressive_scope_search` 方法：按 4 阶段级联执行搜索
  - [ ] 3.2 实现阶段退出逻辑：当某阶段结果数 >= `min_results_threshold`（默认 5）时停止扩展
  - [ ] 3.3 每个阶段返回的结果附带 `scope_level: int`（1-4）标记
  - [ ] 3.4 在 LanceDB Dense 和 Sparse 搜索节点中集成渐进范围逻辑
  - [ ] 3.5 渐进范围参数从 config 读取：`progressive_scope_enabled: bool`（默认 True）、`min_results_threshold: int`（默认 5）

- [ ] **Task 4: Wiki-links 解析与邻居扩展** (AC: #4)
  - [ ] 4.1 新增 `_extract_wiki_links(content: str) -> List[str]` 工具方法：正则提取 `[[文件名]]` 和 `[[文件名|显示文本]]` 格式的链接
  - [ ] 4.2 新增 `_expand_neighbors(results: List[SearchResult], table_name: str, max_neighbors: int = 5) -> List[SearchResult]` 方法：
    - 从搜索结果的文档内容中提取 wiki-links
    - 在 LanceDB 中查找这些链接文件的分块
    - 对邻居分块的分数乘以衰减系数（默认 0.7）
    - 标记 `source_type: "neighbor_expansion"`
  - [ ] 4.3 在精排前的融合阶段调用邻居扩展（扩展后的结果一起参与 RRF 融合）
  - [ ] 4.4 邻居扩展参数从 config 读取：`neighbor_expansion_enabled: bool`（默认 True）、`neighbor_max_count: int`（默认 5）、`neighbor_score_decay: float`（默认 0.7）

- [ ] **Task 5: Tag Jaccard 桥接** (AC: #5)
  - [ ] 5.1 新增 `_compute_tag_jaccard(tags_a: Set[str], tags_b: Set[str]) -> float` 工具方法
  - [ ] 5.2 新增 `_find_related_courses(current_course: str, threshold: float = 0.3) -> List[str]` 方法：扫描 fingerprint 表或索引表中的 course 列，计算 Jaccard 相似度
  - [ ] 5.3 在渐进范围搜索的阶段 2 中使用 `_find_related_courses` 确定相关课程
  - [ ] 5.4 桥接功能默认关闭（config `tag_jaccard_bridge_enabled: bool = False`），用户可手动开启

- [ ] **Task 6: 配置更新与集成** (AC: #1-#5)
  - [ ] 6.1 更新 `src/agentic_rag/config.py` 的 `CanvasRAGConfig`，新增：
    - `progressive_scope_enabled: bool`（默认 True）
    - `min_results_threshold: int`（默认 5）
    - `neighbor_expansion_enabled: bool`（默认 True）
    - `neighbor_max_count: int`（默认 5）
    - `neighbor_score_decay: float`（默认 0.7）
    - `tag_jaccard_bridge_enabled: bool`（默认 False）
    - `tag_jaccard_threshold: float`（默认 0.3）
  - [ ] 6.2 更新 `DEFAULT_CONFIG` 中的默认值
  - [ ] 6.3 确保新增配置字段通过 `merge_config()` 正确合并

- [ ] **Task 7: 端到端验证** (AC: #1-#5)
  - [ ] 7.1 准备测试场景：
    - 含 Frontmatter 的笔记正确解析 course/tags 字段
    - 按 course 过滤搜索只返回对应课程的结果
    - 修改笔记删除 Frontmatter 后重新索引不报错
    - Wiki-links 邻居扩展返回 neighbor_expansion 标记的结果
    - 渐进范围搜索在结果不足时正确扩展
  - [ ] 7.2 `ruff check src/agentic_rag/` 全量 lint 通过
  - [ ] 7.3 `ruff format --check src/agentic_rag/` 格式检查通过
  - [ ] 7.4 确认无 mock 数据、无 TODO 空函数、无假实现（DD-03）

## Dev Notes

### Brownfield 上下文——已有代码资产

这是 **Brownfield 项目**，搜索框架已存在但不支持元数据过滤和邻居扩展。后端 PRD S5 功能 1-4 定义了完整的新功能需求。

#### 关键文件清单

| 文件 | 当前状态 | 本 Story 修改内容 |
|------|---------|-----------------|
| `src/agentic_rag/clients/lancedb_client.py` | search/index 方法无 Frontmatter 解析和 course/tags 过滤 | **新增 Frontmatter 解析 + where 过滤 + 邻居扩展** |
| `src/agentic_rag/nodes.py` | `fan_out_retrieval` 分发搜索请求，无范围过滤 | **集成渐进范围搜索逻辑** |
| `src/agentic_rag/config.py` | `CanvasRAGConfig` 无元数据过滤相关配置 | **新增过滤/扩展/桥接配置项** |
| `src/agentic_rag/state.py` | `SearchResult` 无 scope_level / source_type 字段 | **扩展 SearchResult 字段** |

#### Frontmatter 格式参考

```yaml
---
course: CS188
tags: [search, AI, heuristic]
category: lecture-notes
---
# 笔记内容...
```

### 依赖关系

- **前置 Story 2.7**（文件指纹增量索引）：索引流程已支持 delete-before-insert，本 Story 在此基础上扩展 schema
- **前置 Story 2.5**（精排与融合升级）：邻居扩展的结果需要参与 RRF 融合
- **后续 Story 2.11**（参数可配置化）：本 Story 新增的过滤/扩展参数纳入完整配置体系

### 技术决策

1. **前置过滤 vs 后置过滤**：使用 LanceDB `where` 前置过滤（减少向量搜索空间，性能更优），而非搜索后过滤。
2. **tags 存储**：tags 存为逗号分隔字符串（LanceDB 列类型限制），使用 LIKE 匹配。如 LanceDB 后续支持 Array 列类型可升级。
3. **邻居扩展时机**：在精排前执行（扩展后的结果一起参与 RRF + reranker），而非精排后。
4. **渐进范围**：4 阶段级联而非一次全库搜索，减少不相关结果干扰。

### 关键代码位置

| 组件 | 文件路径 |
|------|---------|
| 搜索入口 | `src/agentic_rag/clients/lancedb_client.py`（`search` / `_search_internal`） |
| 搜索分发 | `src/agentic_rag/nodes.py`（`fan_out_retrieval`） |
| 配置 | `src/agentic_rag/config.py`（`CanvasRAGConfig`） |
| State | `src/agentic_rag/state.py`（`SearchResult` / `CanvasRAGState`） |
| 索引入口 | `src/agentic_rag/clients/lancedb_client.py`（`index_vault_notes` / `index_single_file`） |

### 不做的事项（防蔓延 DD-10）

- 不修改 embedding 模型或分块策略
- 不实现前端过滤 UI（Epic 3 前端集成范围）
- 不修改 LangGraph 图结构（只修改节点实现）
- 不实现全文本搜索的中文优化（Story 2.4 已完成）
- 不实现多 vault 隔离（当前只支持单 vault）

### FR 覆盖映射

| FR ID | AC 映射 | 说明 |
|-------|---------|------|
| FR-RET-P-02 | AC-2 | 按课程/标签过滤 |
| FR-RET-P-03 | AC-3 | 渐进范围扩展搜索 |
| FR-RET-P-04 | AC-4 | Wiki-links 1-hop 邻居扩展 |
| FR-OPS-03 | AC-5 | 多学科 subject 隔离 + Tag Jaccard 桥接 |

### Project Structure Notes

- 本 Story 修改范围限于 `src/agentic_rag/` 目录
- LanceDB schema 扩展需要注意与已有数据的兼容性
- Wiki-links 解析使用 Obsidian 标准格式 `[[filename]]` 和 `[[filename|alias]]`
- YAML 解析使用 `pyyaml`（确认在依赖中已包含）

### References

- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#Phase 2] — 任务 2.1-2.4 元数据过滤、邻居检索、渐进范围、跨课程桥接
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#能力域 2：笔记检索] — FR-RET-P-02/03/04 定义
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#能力域 4：配置与运维] — FR-OPS-03 多学科隔离
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.8] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md] — 四层路由 + 六路物理通道架构
- [Source: src/agentic_rag/clients/lancedb_client.py] — 当前搜索和索引实现

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
