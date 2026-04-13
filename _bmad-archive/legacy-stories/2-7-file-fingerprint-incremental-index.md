# Story 2.7: Phase 1 — 文件指纹增量索引

Status: ready-for-dev

## Story

As a 用户,
I want 修改笔记后只重新索引改动的文件，且同一文件只有一份最新索引,
so that 索引快速且不会出现重复搜索结果。

## Acceptance Criteria

1. **AC-1: 文件指纹（content_hash）变化检测**
   - **Given** vault 中有 100 个 .md 文件，用户修改了其中 3 个
   - **When** 增量索引管道触发
   - **Then** 通过 SHA-256 content_hash 比对，只有 3 个变化的文件进入分块+向量化流程
   - **And** 未变化的 97 个文件完全跳过（不读取内容、不重新分块、不重新 embedding）
   - **And** content_hash 存储在 LanceDB 的 `file_fingerprints` 表中（file_path → content_hash 映射）
   - **And** 新增文件（无历史 hash）视为变化文件，正常处理

2. **AC-2: delete-before-insert 去重索引**
   - **Given** 用户修改了某个 .md 文件的内容
   - **When** 该文件的增量索引执行
   - **Then** 先删除该文件在 `vault_notes` 表中的所有旧 chunks（按 `canvas_file` 字段匹配）
   - **And** 再插入新分块后的 chunks
   - **And** 修改 N 次后，该文件在表中仍然只有 1 份最新索引数据（无重复行）
   - **And** 删除操作对路径中单引号正确 SQL 转义

3. **AC-3: 增量索引性能 < 5s**
   - **Given** vault 有 500+ 笔记，用户修改了 1-3 个文件
   - **When** 增量索引触发
   - **Then** 从检测变化到索引完成，总耗时 < 5 秒（不含 embedding 模型首次加载）
   - **And** 日志记录：跳过 N 个未变化文件、处理 M 个变化文件、耗时 X ms

4. **AC-4: 全量重建按钮**
   - **Given** 用户执行模型迁移（如从旧模型切换到 bge-m3）或索引数据异常
   - **When** 调用全量重建接口（`force_rebuild=True`）
   - **Then** 忽略所有 content_hash 缓存，对 vault 中所有 .md 文件重新分块+向量化+写入
   - **And** 全量重建前清空 `vault_notes` 表（drop + recreate）和 `file_fingerprints` 表
   - **And** 全量重建后重建 FTS 索引
   - **And** 全量重建 < 30s GPU / < 2min CPU（120 文件）

5. **AC-5: FTS 索引在增量更新后保持可用**
   - **Given** 增量索引完成（delete-before-insert）
   - **When** 执行 hybrid search（向量 + 关键词）
   - **Then** FTS 索引在增量更新后重建（`create_fts_index("content", replace=True)`）
   - **And** 新增/更新的文档可通过 FTS 分支命中

6. **AC-6: 文件删除清理**
   - **Given** 用户删除了 vault 中的文件
   - **When** 增量索引管道触发
   - **Then** 检测到 fingerprint 表中有记录但文件系统中不存在的文件
   - **And** 自动清除这些文件在 LanceDB 中的所有分块数据和 fingerprint 记录
   - **And** 清理后搜索不再返回已删除文件的内容

7. **AC-7: index_single_file 路径修复（CRITICAL C8）**
   - **Given** `index_single_file` 当前使用 `os.path.basename(file_path)` 丢失目录路径
   - **When** 索引包含子目录的 vault 文件（如 `notes/chapter1/intro.md`）
   - **Then** 使用 `os.path.relpath(file_path, vault_path)` 保留相对路径
   - **And** 搜索结果中的 `canvas_file` 字段能正确还原到文件完整相对路径

8. **AC-8: State 字段补全（S4 Round 3）**
   - **Given** CanvasRAGState 用于 LangGraph 管道
   - **When** 管道初始化
   - **Then** 所有 State 字段有合理的初始值（通过初始化工厂函数提供默认值）
   - **And** 管道执行过程中不因缺少 State 字段而报 KeyError

## Tasks / Subtasks

- [ ] **Task 1: 文件指纹表设计与实现** (AC: #1)
  - [ ] 1.1 在 `src/agentic_rag/clients/lancedb_client.py` 中新增 `_ensure_fingerprint_table()` 方法：创建或打开 `file_fingerprints` 表（schema: `file_path: str`, `content_hash: str`, `last_indexed: str`, `chunk_count: int`）
  - [ ] 1.2 新增 `_compute_file_hash(file_path: str) -> str` 静态方法：使用 `hashlib.sha256` 对文件内容取 UTF-8 编码后的哈希值
  - [ ] 1.3 新增 `_get_changed_files(vault_path: str, file_paths: List[str]) -> Tuple[List[str], List[str], List[str]]` 方法：返回 (新增文件, 变化文件, 已删除文件)，比对 fingerprint 表中的记录与当前文件 hash
  - [ ] 1.4 新增 `_update_fingerprint(file_path: str, content_hash: str, chunk_count: int)` 方法：使用 delete-before-insert 更新 fingerprint 记录
  - [ ] 1.5 新增 `_remove_fingerprint(file_path: str)` 方法：删除 fingerprint 记录

- [ ] **Task 2: delete-before-insert 去重机制** (AC: #2)
  - [ ] 2.1 新增 `_delete_file_chunks(table_name: str, file_path: str) -> int` 方法：删除 LanceDB 表中 `canvas_file == file_path` 的所有行
  - [ ] 2.2 使用 LanceDB 的 `table.delete(f"canvas_file = '{escaped_path}'")` API 实现行级删除，注意对路径中的单引号进行转义
  - [ ] 2.3 在 `index_single_file` 中插入前先调用 `_delete_file_chunks`
  - [ ] 2.4 在 `index_vault_notes` 中为每个变化文件调用 delete-before-insert 逻辑
  - [ ] 2.5 验证：修改同一文件 3 次后，LanceDB 中该文件只有最新一份分块

- [ ] **Task 3: 增量索引流程改造** (AC: #1, #3, #6)
  - [ ] 3.1 重构 `index_vault_notes` 方法：
    - 扫描 vault 目录获取所有 .md 文件路径列表
    - 调用 `_get_changed_files` 获取变化清单（新增 + 变化 + 已删除）
    - 对新增和变化文件执行 delete-before-insert + 向量化 + 写入
    - 对已删除文件执行 `_delete_file_chunks` + `_remove_fingerprint` 清理
    - 更新 fingerprint 表
  - [ ] 3.2 重构 `index_single_file` 方法：集成 delete-before-insert + fingerprint 更新
  - [ ] 3.3 添加增量索引日志：`[INDEX] Scanned {total} files: {new} new, {changed} changed, {deleted} deleted, {skipped} skipped in {duration}ms`
  - [ ] 3.4 增量索引完成后重建 FTS 索引（`create_fts_index("content", replace=True)`）

- [ ] **Task 4: 索引路径修复（CRITICAL C8）** (AC: #7)
  - [ ] 4.1 在 `index_single_file` 中将 `rel_path = os.path.basename(file_path)` 改为 `rel_path = os.path.relpath(file_path, vault_root)`
  - [ ] 4.2 确保 `vault_root` 参数在 `index_single_file` 和 `index_vault_notes` 方法签名中可用
  - [ ] 4.3 确保 `canvas_file` 和 metadata 中的 `file_path` 字段使用一致的相对路径格式
  - [ ] 4.4 搜索结果中的 `file_path` 保持与索引时一致（能正确定位到源文件）

- [ ] **Task 5: 全量重建实现** (AC: #4)
  - [ ] 5.1 新增 `rebuild_index(vault_path: str, table_name: str, subject: str) -> Dict` 方法：
    - 清空 fingerprint 表（drop + recreate）
    - 删除 LanceDB 主表（`db.drop_table(table_name)` 或清空所有行）
    - 重新扫描 vault 所有 .md 文件，逐个分块 + 向量化 + 写入
    - 为每个文件创建 fingerprint 记录
    - 重新创建 FTS 索引
    - 返回统计信息（total_files, total_chunks, duration_ms）
  - [ ] 5.2 支持 `progress_callback(current: int, total: int)` 参数用于进度上报
  - [ ] 5.3 添加日志：`[REBUILD] Complete: {total_files} files, {total_chunks} chunks in {duration}ms`

- [ ] **Task 6: State 字段补全** (AC: #8)
  - [ ] 6.1 审查 `src/agentic_rag/state.py` 的 `CanvasRAGState`，确保所有字段都有默认值
  - [ ] 6.2 新增 `create_initial_state()` 工厂函数（如不存在），返回带默认值的完整 state
  - [ ] 6.3 确保管道执行过程中不因缺少 State 字段而报 KeyError

- [ ] **Task 7: 端到端验证** (AC: #1-#8)
  - [ ] 7.1 准备测试场景：
    - 首次索引 5 个 .md 文件 → 验证全部被索引 + fingerprint 表有 5 条记录
    - 修改 2 个文件 → 增量索引只处理 2 个文件 → 搜索无重复
    - 删除 1 个文件 → 增量索引清理该文件数据 → 搜索不返回已删除内容
    - 全量重建 → 所有数据重新索引 → 搜索正常
  - [ ] 7.2 性能验证：修改 3 个文件的增量索引 < 5 秒
  - [ ] 7.3 去重验证：同一文件修改 5 次后，LanceDB 中该文件只有最新一份分块
  - [ ] 7.4 路径验证：子目录文件的 canvas_file 包含完整相对路径
  - [ ] 7.5 `ruff check src/agentic_rag/` 全量 lint 通过
  - [ ] 7.6 `ruff format --check src/agentic_rag/` 格式检查通过
  - [ ] 7.7 确认无 mock 数据、无 TODO 空函数、无假实现（DD-03）

## Dev Notes

### Brownfield 上下文——已有代码资产

这是 **Brownfield 项目**，索引功能框架已存在但存在两个 CRITICAL 级缺陷：C6（纯 append 无去重）和 C8（路径丢失）。

#### 关键文件清单

| 文件 | 当前状态 | 本 Story 修改内容 |
|------|---------|-----------------|
| `src/agentic_rag/clients/lancedb_client.py` L556-665 | `index_single_file` 纯 append，`os.path.basename` 丢失目录路径（CRITICAL C6/C8） | **重构为 delete-before-insert + 路径修复 + fingerprint 集成** |
| `src/agentic_rag/clients/lancedb_client.py` L405-554 | `index_vault_notes` 全量扫描全量写入，无增量逻辑 | **重构为 fingerprint 驱动的增量索引** |
| `src/agentic_rag/clients/lancedb_client.py` L1158-1232 | `add_documents` 纯 append（table.add） | **不修改**（上层通过 delete-before-insert 保证去重） |
| `src/agentic_rag/state.py` | `CanvasRAGState` TypedDict | **补全默认值，新增初始化工厂** |
| `src/agentic_rag/config.py` | `CanvasRAGConfig` 已有基础配置 | **无需修改**（fingerprint 逻辑内聚在 lancedb_client 中） |

#### 索引去重策略说明

当前 `add_documents` 使用 `table.add()` 是纯 append 模式。每次编辑文件后重新索引，数据累积：

```
编辑 1 次 → 10 个 chunks
编辑 2 次 → 20 个 chunks（10 旧 + 10 新）
编辑 N 次 → N*10 个 chunks（旧数据永远不清理）
```

修复后（delete-before-insert）：
```
编辑 N 次 → 始终 10 个 chunks（先删旧再写新）
```

#### 文件指纹设计（来自后端 PRD）

后端 PRD Phase 1 任务 1.9 确认：**文件指纹增量索引（delete-before-insert）**
- 文件指纹用 SHA-256 content hash（简单可靠，比 mtime 更准确）
- delete-before-insert 而非 merge_insert（merge_insert 的 `when_not_matched_by_source` 会误删其他文件数据——后端 PRD A4 调研确认）
- LanceDB `table.delete(filter)` 支持行级删除（LanceDB v0.4+ 原生支持）

### 依赖关系

- **前置 Story 2.3**（bge-m3 迁移）：向量化使用 bge-m3 模型，本 Story 不修改 embedding 逻辑
- **前置 Story 2.4**（中文搜索）：jieba 预分词已集成，本 Story 不修改分词逻辑
- **后续 Story 2.9**（图片检索管道）：图片索引也需要使用 delete-before-insert 模式，复用本 Story 的 fingerprint 基础设施
- **后续 Story 2.12**（验收测试）：全量重建按钮在此 Story 实现，验收测试使用

### 技术决策

1. **SHA-256 vs mtime**：使用 SHA-256 content hash，比文件修改时间更准确（mtime 在文件复制/git checkout 时可能不准）。
2. **delete-before-insert vs merge_insert**：使用 delete-before-insert（后端 PRD A4 确认，merge_insert 的 `when_not_matched_by_source` 会误删其他文件的数据）。
3. **fingerprint 存储位置**：存在 LanceDB 的独立表中（与索引数据同存储引擎，不引入额外依赖），不用 SQLite。
4. **增量 vs 全量**：默认增量（fingerprint 驱动），提供全量重建作为兜底（模型迁移/异常恢复）。

### 关键代码位置

| 组件 | 文件路径 |
|------|---------|
| 增量索引入口 | `src/agentic_rag/clients/lancedb_client.py` L556（`index_single_file`） |
| 全量索引入口 | `src/agentic_rag/clients/lancedb_client.py` L405（`index_vault_notes`） |
| 文档写入 | `src/agentic_rag/clients/lancedb_client.py` L1158（`add_documents`） |
| 分块逻辑 | `src/agentic_rag/clients/lancedb_client.py` L668（`_split_md_by_heading`） |
| 向量化 | `src/agentic_rag/clients/lancedb_client.py` L267（`embed`） |
| FTS 索引创建 | `src/agentic_rag/clients/lancedb_client.py` L540（`tbl.create_fts_index`） |
| State 定义 | `src/agentic_rag/state.py`（`CanvasRAGState`） |

### 不做的事项（防蔓延 DD-10）

- 不修改分块策略（Story 2.3 已完成标题智能分块）
- 不修改 embedding 模型（Story 2.3 已完成 bge-m3 迁移）
- 不实现图片文件的 fingerprint（Story 2.9 的范围）
- 不实现三阶段自动升级索引策略（5000+ 文件场景为远期需求，当前 120 文件足够）
- 不修改 LangGraph 图结构
- 不修改前端代码（纯后端索引管道升级）
- 不实现前端的"前后端双重触发"移除（Story 2.1 Phase 0 已处理）

### FR 覆盖映射

| FR ID | AC 映射 | 说明 |
|-------|---------|------|
| FR-IDX-01 | AC-1 | 文件指纹增量索引 |
| FR-IDX-07 | AC-2 | delete-before-insert 去重索引 |
| FR-IDX-08 | AC-4 | 全量重建按钮 |
| FR-RET-07 | AC-1, AC-2, AC-6 | 文件指纹增量索引 + 旧索引自动清除 |

### Project Structure Notes

- 本 Story 修改范围主要在 `src/agentic_rag/clients/lancedb_client.py` 和 `src/agentic_rag/state.py`
- fingerprint 表作为 LanceDB 内部表，不引入新的存储依赖
- `add_documents` 方法签名不变，上层通过 delete-before-insert 模式保证去重
- 路径修复（C8）需要 vault_root 参数，确认调用方（`index_vault_notes`、API 端点）传入正确的 vault 路径

### References

- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#Phase 1] — 任务 1.9 文件指纹增量索引
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#CRITICAL 级] — C6 纯 append 无去重、C8 路径丢失
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#关键技术选型] — 索引策略选型依据
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.7] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md] — 增量索引管道设计
- [Source: src/agentic_rag/clients/lancedb_client.py] — 当前索引实现（index_single_file / index_vault_notes / add_documents）

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
