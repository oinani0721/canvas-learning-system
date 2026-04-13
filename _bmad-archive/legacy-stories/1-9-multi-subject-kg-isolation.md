# Story 1.9: 多学科知识图谱隔离

Status: ready-for-dev

## Story

As a 用户,
I want 管理多门课程的知识图谱隔离与切换，在设置中创建/编辑/删除学科，切换白板时自动筛选该学科内容，检索自动 scope 到当前学科，
so that 不同学科的内容互不干扰，同时可选开启跨学科关联发现。

## Acceptance Criteria

1. **AC-1: 设置面板学科 CRUD**
   - **Given** 用户打开 Obsidian 设置 -> Canvas Learning System -> 学科管理区域
   - **When** 用户点击"添加学科"
   - **Then** 可输入学科名称（支持中英文，如 CS188、线性代数、托福听力）
   - **And** 学科保存到 Obsidian 插件本地配置（`plugin.settings.subjects[]`）
   - **And** 可编辑已有学科名称、删除学科（删除前确认对话框）
   - **And** 删除学科不删除该学科下的节点/边数据（数据保留，仅移除学科标签关联）
   - **And** 至少保留一个学科（不允许删除最后一个），系统预设"通用"学科作为默认

2. **AC-2: 白板绑定学科**
   - **Given** 用户创建或打开一个白板
   - **When** 白板创建/首次打开时
   - **Then** 系统尝试自动推断学科（路径推断：取 Canvas 文件路径第一级非跳过目录）
   - **And** 用户可在白板视图顶部或右键菜单手动指定/切换该白板所属学科
   - **And** 白板的 `subjectId` 写入 IndexedDB `canvas_boards` 表和 Neo4j `CanvasBoard` 节点
   - **And** 白板下所有节点和边继承白板的 `subjectId`

3. **AC-3: 白板视图按学科筛选**
   - **Given** 用户在 Dashboard 或白板列表中选择当前学科
   - **When** 学科切换发生
   - **Then** Dashboard 白板列表只显示当前学科的白板
   - **And** 切换学科后 UI 即时刷新（Dexie liveQuery 按 `subjectId` 过滤）
   - **And** 学科切换不影响其他学科的数据（零数据丢失）
   - **And** "全部学科"选项显示所有白板（无过滤）

4. **AC-4: 检索 scope 按学科隔离**
   - **Given** 用户在某学科的白板中进行 AI 对话
   - **When** 后端检索管道执行搜索
   - **Then** LanceDB 搜索自动附加 `subject` 字段过滤条件，只搜索当前学科的笔记索引
   - **And** Neo4j 查询自动附加 `subjectId` 过滤条件
   - **And** Graphiti 检索使用学科对应的 `group_id`
   - **And** 检索结果不会混入其他学科的内容

5. **AC-5: 跨学科 Tag Jaccard 桥接（可选开启）**
   - **Given** 用户在设置中开启"跨学科关联"开关
   - **When** 检索执行时
   - **Then** 系统计算当前学科与其他学科的 Tag Jaccard 相似度
   - **And** 相似度超过阈值（默认 0.3）的学科内容也纳入检索范围
   - **And** 跨学科结果在搜索结果中标注来源学科
   - **And** 默认关闭，用户显式开启后生效
   - **And** 阈值可在设置面板调整（0.0-1.0 滑块）

6. **AC-6: 学科切换数据完整性**
   - **Given** 用户在学科 A 中有白板和节点数据
   - **When** 用户切换到学科 B 再切回学科 A
   - **Then** 学科 A 的所有白板、节点、边、对话历史、精通度数据完整无损
   - **And** 同步到后端的数据通过 `subjectId` 正确隔离
   - **And** 学科切换操作不触发数据重新索引（仅前端过滤）

7. **AC-7: 后端 subject 参数全路径贯通（FR-SYS-07 + FR-OPS-03）**
   - **Given** 前端发送带 `subject_id` 的请求到后端
   - **When** 后端处理请求
   - **Then** `subject_id` 参数贯穿所有数据写入路径（Neo4j MERGE / LanceDB 索引 / Graphiti group_id）
   - **And** `subject_id` 参数贯穿所有查询路径（Neo4j WHERE / LanceDB filter / Graphiti search）
   - **And** 已有 `subject_config.py` 和 `subject_resolver.py` 的 STUB 代码被激活为真实实现
   - **And** `subject_mapping.yaml` 中的 cs188 硬编码默认值替换为用户配置的学科列表

## Tasks / Subtasks

- [ ] **Task 1: 前端学科管理数据模型** (AC: #1, #2, #6)
  - [ ] 1.1 修改 `obsidian-canvas-learning/src/types/canvas.d.ts`：追加 `Subject` 接口定义
    ```typescript
    interface Subject {
      id: string;        // UUID
      name: string;      // 用户可见名称（CS188、线性代数）
      createdAt: string;
      isDefault: boolean; // 默认学科标记
    }
    ```
  - [ ] 1.2 修改 `obsidian-canvas-learning/src/services/dexie-db.ts`：
    - `canvas_boards` 表已有 `subjectId` 字段（Story 1.5 预留）-> 确认字段存在
    - 确认 `canvas_nodes` 和 `canvas_edges` 表通过 `canvasId` 关联到 board 级别的 `subjectId`
  - [ ] 1.3 修改 `obsidian-canvas-learning/src/stores/system-state.svelte.ts`：
    - 追加 `subjects: Subject[] = $state<Subject[]>([])`
    - 追加 `activeSubjectId: string | null = $state(null)`
    - 追加 `crossSubjectEnabled: boolean = $state(false)`
    - 追加 `crossSubjectThreshold: number = $state(0.3)`
    - 追加方法：`addSubject(name)`, `removeSubject(id)`, `updateSubject(id, name)`, `setActiveSubject(id)`

- [ ] **Task 2: Settings Tab 学科管理 UI** (AC: #1)
  - [ ] 2.1 修改 `obsidian-canvas-learning/src/settings.ts`（Story 1.3 已创建 PluginSettingTab）：
    - 在 Settings Tab 中追加"学科管理"区域
    - 学科列表展示：每行显示学科名称 + 编辑按钮 + 删除按钮
    - "添加学科"按钮 -> 输入框 + 确认
    - 删除确认对话框："删除学科不会删除已有数据，确认删除？"
    - 最后一个学科不可删除（灰色禁用删除按钮）
    - 跨学科关联开关 Toggle + Jaccard 阈值 Slider（0.0-1.0，步进 0.05）
  - [ ] 2.2 学科数据持久化到 Obsidian plugin settings：
    ```typescript
    interface CanvasLearningSettings {
      // ... 已有字段
      subjects: Subject[];
      activeSubjectId: string | null;
      crossSubjectEnabled: boolean;
      crossSubjectThreshold: number;
    }
    ```
  - [ ] 2.3 插件加载时从 settings 恢复学科列表到 system-state Store

- [ ] **Task 3: 白板学科绑定与路径推断** (AC: #2)
  - [ ] 3.1 修改 `obsidian-canvas-learning/src/stores/canvas-state.svelte.ts`：
    - 创建/加载白板时调用路径推断逻辑确定默认 `subjectId`
    - 路径推断规则（复用已有 `subject_config.py` 逻辑的前端等价实现）：
      1. 取 Canvas 文件路径第一级非跳过目录（跳过 .obsidian, .git, .trash 等）
      2. 匹配已注册学科名称 -> 绑定
      3. 无匹配 -> 使用默认学科
    - 用户可通过白板顶部下拉菜单手动覆盖学科绑定
  - [ ] 3.2 修改 `obsidian-canvas-learning/src/components/canvas/CanvasView.svelte`：
    - 白板顶部工具栏追加学科选择下拉（小型 Select，不占过多空间）
    - 切换学科 -> 更新 IndexedDB `canvas_boards.subjectId` -> 触发 Outbox sync
  - [ ] 3.3 白板下新建节点/边自动继承白板的 `subjectId`（通过 `canvasId` 关联）

- [ ] **Task 4: Dashboard 学科筛选** (AC: #3)
  - [ ] 4.1 修改 `obsidian-canvas-learning/src/components/dashboard/DashboardView.svelte`（Story 1.4 最小化 Dashboard 已创建）：
    - 顶部追加学科筛选下拉："全部学科" | 学科 A | 学科 B | ...
    - 筛选下拉切换 -> 更新 `systemState.activeSubjectId`
    - 白板列表通过 Dexie liveQuery 按 `subjectId` 过滤查询
  - [ ] 4.2 Dexie 查询优化：
    ```typescript
    // 当 activeSubjectId 为 null 时查全部
    const boards = activeSubjectId
      ? db.canvas_boards.where('subjectId').equals(activeSubjectId).toArray()
      : db.canvas_boards.toArray();
    ```

- [ ] **Task 5: 后端 subject_config 激活** (AC: #7)
  - [ ] 5.1 修改 `backend/app/core/subject_config.py`：
    - 移除 STUB 注释标记
    - `SubjectType` 枚举替换为动态学科列表（从 API 接收，不再硬编码枚举）
    - `get_current_subject()` 改为从请求上下文获取 `subject_id` 参数
    - 保留 `extract_subject_from_canvas_path()` 路径推断逻辑（作为后端兜底）
    - 保留 `build_group_id()` 和 `sanitize_subject_name()` 工具函数
  - [ ] 5.2 修改 `backend/app/services/subject_resolver.py`：
    - 确保 4 级优先级链生效：手动覆盖 -> 配置映射 -> 路径推断 -> 默认值
    - `subject_mapping.yaml` 中 cs188 硬编码默认值替换为 `general`
  - [ ] 5.3 修改 `backend/config/subject_mapping.yaml`：
    - 移除 cs188 硬编码，defaults 改为 `general`
    - 保留 mappings 结构供用户自定义

- [ ] **Task 6: 后端检索 scope 隔离** (AC: #4)
  - [ ] 6.1 修改后端搜索 API（`backend/app/api/v1/search.py` 或对应端点）：
    - 接收 `subject_id` 参数
    - 传递到 LangGraph 管道的 State 中
  - [ ] 6.2 修改 LanceDB 检索节点（`backend/app/agentic_rag/nodes/retriever.py`）：
    - 搜索时附加 `where("subject == '{subject_id}'")` 过滤条件
  - [ ] 6.3 修改 Neo4j 查询（通过 `backend/app/db/neo4j_client.py`）：
    - 查询节点/边时附加 `WHERE n.subjectId = $subject_id` 条件
  - [ ] 6.4 修改 Graphiti 检索：
    - 使用 `group_id = build_group_id(subject_id)` 作为搜索范围

- [ ] **Task 7: 跨学科 Tag Jaccard 桥接** (AC: #5)
  - [ ] 7.1 创建 `backend/app/services/cross_subject_bridge.py`：
    - 实现 `compute_tag_jaccard(subject_a_tags: set, subject_b_tags: set) -> float`
    - Tags 来源：白板节点的标签/关键词、Frontmatter tags
    - Jaccard 系数 = |A intersection B| / |A union B|
  - [ ] 7.2 修改检索管道：
    - 当 `cross_subject_enabled=True` 时，计算当前学科与所有其他学科的 Jaccard
    - 超过阈值的学科加入检索范围（扩展 LanceDB where 条件为 `subject IN [...]`）
    - 跨学科结果标注 `source_subject` 字段
  - [ ] 7.3 前端传递 `cross_subject_enabled` 和 `threshold` 参数到后端 API

- [ ] **Task 8: 后端学科管理 API** (AC: #1, #7)
  - [ ] 8.1 修改 `backend/app/api/v1/system.py`（或创建 `subjects.py`）：
    - `GET /api/v1/subjects/` -> 返回学科列表
    - `POST /api/v1/subjects/` -> 创建学科
    - `PUT /api/v1/subjects/{id}` -> 更新学科名称
    - `DELETE /api/v1/subjects/{id}` -> 删除学科（不删除数据）
  - [ ] 8.2 学科列表持久化到 SQLite（`subjects` 表）或 Neo4j（`:Subject` 标签节点）
  - [ ] 8.3 学科 CRUD API 与前端 Settings Tab 联动

- [ ] **Task 9: Sync API subject 贯通** (AC: #7)
  - [ ] 9.1 修改 `backend/app/services/sync_service.py`（Story 1.5 已创建）：
    - 确认 `SyncBatchRequest.subject_id` 字段已在 Story 1.5 预留
    - sync 写入 Neo4j 时 `subjectId` 属性正确传播
  - [ ] 9.2 修改 LanceDB 索引管道（`backend/app/indexing/pipeline.py`）：
    - 索引写入时附带 `subject` 元数据字段
    - 重建索引时按学科分批处理

- [ ] **Task 10: 集成验证** (AC: #3, #4, #6)
  - [ ] 10.1 端到端验证场景：
    - 创建学科 A（CS188）和学科 B（线性代数）
    - 学科 A 下创建白板和节点 -> 切换到学科 B -> 确认看不到学科 A 的白板
    - 学科 B 下对话 -> 确认检索结果不包含学科 A 的笔记
    - 切回学科 A -> 确认数据完整无损
  - [ ] 10.2 跨学科桥接验证：
    - 学科 A 和 B 有共同标签 -> 开启跨学科关联 -> 确认搜索结果包含相关学科内容
    - 关闭跨学科关联 -> 确认搜索结果仅限当前学科
  - [ ] 10.3 数据完整性验证：
    - 删除学科 -> 确认该学科下的数据仍可通过"全部学科"视图访问
    - 重命名学科 -> 确认关联数据的 `subjectId` 正确更新

## Dev Notes

### Brownfield 上下文

已有代码资产（需激活/修复，非从零开始）：

- **`backend/app/core/subject_config.py`**：STUB 状态，有 `SubjectType` 枚举、路径推断逻辑 `extract_subject_from_canvas_path()`、`build_group_id()` 和 `sanitize_subject_name()` 工具函数。需要移除 STUB 标记，将硬编码枚举改为动态学科列表。
- **`backend/app/services/subject_resolver.py`**：已有 4 级优先级解析链（手动覆盖 -> 配置映射 -> 路径推断 -> 默认值），需要对接前端学科管理 API。
- **`backend/config/subject_mapping.yaml`**：已有映射配置结构，需要移除 cs188 硬编码默认值。
- **`backend/app/services/cross_canvas_service.py`**：已有跨白板服务骨架，可能包含部分可复用逻辑。
- **Story 1.5 预留**：`SyncBatchRequest.subject_id` 字段已存在，Neo4j 节点已有 `subjectId` 属性。

### 架构模式

**数据隔离策略（来自 Architecture 文档 Cross-Cutting Concerns #8）：**

| 存储 | 隔离方式 |
|------|---------|
| IndexedDB | `canvas_boards.subjectId` -> 节点/边通过 `canvasId` 关联 |
| Neo4j | `CanvasNode.subjectId` + `CanvasBoard.subjectId` 属性过滤 |
| LanceDB | `subject` 列字段 + `WHERE subject = ?` 过滤 |
| Graphiti | `group_id` = `build_group_id(subject)` per-subject 隔离 |
| SQLite | 对话 session 通过 `node_id` -> `canvas_id` -> `subject_id` 间接关联 |

**学科标签优先级（来自 Architecture 决策）：**
1. 用户手动打标（最高优先）
2. 系统路径推断（`extract_subject_from_canvas_path()`）
3. 配置文件映射（`subject_mapping.yaml`）
4. 默认学科（"通用"）

**跨学科 Tag Jaccard 桥接：**
- Jaccard(A, B) = |A intersection B| / |A union B|
- Tags 来源：节点关键词 + Frontmatter tags
- 阈值默认 0.3，用户可调
- 默认关闭，需用户显式开启

### 命名规范速查（本 Story 涉及）

- 前端 Settings 文件：`settings.ts`（已有，追加学科管理区域）
- 后端 API 文件：`snake_case.py`（如 `subjects.py` 或在 `system.py` 中追加）
- CSS 类名：`cl-sys-subject-*`（F 组系统管理）
- Neo4j 属性：`subjectId`（camelCase）
- LanceDB 列：`subject`（snake_case）
- API 参数：`subject_id`（snake_case）

### 不做的事项（防蔓延 DD-10）

- 不实现多 Vault 隔离（`vault_id` 参数，独立 Story）
- 不实现学科合并功能（将两个学科的数据合并，远期需求）
- 不实现学科级别的权限控制（单用户无此需求）
- 不实现自动学科检测（LLM 分析内容推断学科，远期 Phase 2+）
- 不修改 Graphiti 的 `group_id` 架构（复用已有 `build_group_id()` 逻辑）
- 不修改 LangGraph 管道核心架构（仅在检索节点添加 subject 过滤）
- 不修改 `dexie-db.ts` Schema 版本（`subjectId` 字段已在 Story 1.4/1.5 预留）

### 共享文件编辑规则

| 文件 | 规则 |
|------|------|
| `settings.ts` | 追加学科管理区域；保持 Story 1.3 的模型配置和健康面板 |
| `system-state.svelte.ts` | 追加 subjects/activeSubjectId 字段；保持已有 sync/health 字段 |
| `canvas-state.svelte.ts` | 追加 subjectId 路径推断逻辑；保持已有 CRUD 逻辑 |
| `DashboardView.svelte` | 追加学科筛选下拉；保持 Story 1.4 的白板列表逻辑 |
| `CanvasView.svelte` | 追加学科选择下拉；保持已有画布操作逻辑 |
| `subject_config.py` | 移除 STUB 激活真实实现；保持工具函数签名不变 |
| `subject_mapping.yaml` | 移除 cs188 硬编码；保持 mappings 结构 |
| `sync_service.py` | 确认 subject_id 贯通；保持 Story 1.5 的同步逻辑 |

### Project Structure Notes

本 Story 新增/修改的文件清单：

```
obsidian-canvas-learning/
  src/
    settings.ts                              # [修改] 追加学科管理区域
    components/
      canvas/
        CanvasView.svelte                    # [修改] 追加学科选择下拉
      dashboard/
        DashboardView.svelte                 # [修改] 追加学科筛选下拉
    stores/
      system-state.svelte.ts                 # [修改] 追加 subjects 相关状态
      canvas-state.svelte.ts                 # [修改] 追加 subjectId 路径推断
    types/
      canvas.d.ts                            # [修改] 追加 Subject 接口

backend/
  config/
    subject_mapping.yaml                     # [修改] 移除 cs188 硬编码默认值
  app/
    core/
      subject_config.py                      # [修改] 激活 STUB 为真实实现
    api/v1/
      system.py                              # [修改] 追加学科管理端点（或新建 subjects.py）
      search.py                              # [修改] 追加 subject_id 参数传递
    services/
      subject_resolver.py                    # [修改] 对接前端学科管理
      sync_service.py                        # [修改] 确认 subject_id 贯通
      cross_subject_bridge.py                # [新建] Tag Jaccard 桥接服务
    agentic_rag/nodes/
      retriever.py                           # [修改] 追加 subject 过滤条件
    db/
      neo4j_client.py                        # [修改] 查询追加 subjectId 过滤
    indexing/
      pipeline.py                            # [修改] 索引写入附带 subject 元数据
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.9] -- AC 和 Story 需求定义
- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns #8] -- 多学科隔离+多Vault隔离：subject 参数+vault_id 参数设计进每个数据写入/查询路径
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Boundaries] -- 5 层存储隔离策略（IndexedDB vault_id+subject / Neo4j vault_id+subject 标签 / LanceDB table per vault+subject / Graphiti group_id per vault / SQLite session_id+node_id）
- [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions] -- 白板分类：软分类（外在学科标签用户打标为主 / 内在内容类型系统分析+用户覆盖），学科标签：用户手动打标为主+系统建议为辅+路径推断兜底
- [Source: _bmad-output/planning-artifacts/prd.md#多学科与扩展性] -- subject 隔离（group_id + LanceDB subject 字段）+ 跨 subject 桥接。代码已有 STUB（subject_config.py），需激活
- [Source: _bmad-output/planning-artifacts/prd.md#FR-SYS-07] -- 用户可以管理多学科的知识图谱隔离与切换
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#FR-OPS-03] -- 多学科支持：subject 字段隔离 + 跨学科 Tag Jaccard 桥接
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#Phase 0] -- cs188 硬编码清理（20+ 处），支持多学科
- [Source: _bmad-output/implementation-artifacts/1-5-canvas-data-sync-backend-kg.md#AC-8] -- 多学科隔离预留：Neo4j 节点携带 subjectId 属性，SyncBatchRequest.subject_id 字段
- [Source: backend/app/core/subject_config.py] -- 已有 STUB 代码：SubjectType 枚举、路径推断、build_group_id、sanitize_subject_name
- [Source: backend/app/services/subject_resolver.py] -- 已有 4 级优先级解析链
- [Source: backend/config/subject_mapping.yaml] -- 已有映射配置结构（含 cs188 硬编码需清理）

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
