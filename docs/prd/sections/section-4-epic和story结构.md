# 📊 Section 4: Epic和Story结构

### Epic概览

| Epic | 名称 | Story数 | 优先级 | 估算时间 |
|------|------|---------|--------|---------|
| **Epic 0** | **技术文档验证基础设施** | **6** | **P0 (BLOCKER)** | **1天** |
| Epic 11 | FastAPI后端基础架构 | 6 | P0 | 2-3周 |
| Epic 12 | LangGraph多Agent编排 | 7 | P0 | 3-4周 |
| Epic 13 | Obsidian Plugin核心功能 | 7 | P0 | 3-4周 |
| Epic 14 | 艾宾浩斯复习系统迁移+UI集成 **(v1.1.6扩展)** | **12** | P0 | **4-6.5周** (迁移+3层记忆整合) |
| Epic 15 | 检验白板进度追踪 | 5 | P1 | 2周 |
| Epic 16 | 跨Canvas关联学习 | 7 | P1 | 3周 |
| Epic 17 | 性能优化和监控 | 6 | P2 | 2周 |
| Epic 18 | 数据迁移和回滚 | 5 | P1 | 1-2周 |

**总时间估算**: **20.5-24.5周** (5-6个月) - *v1.1.6调整: +2.5周*
**MVP时间**: **10.5-13.5周** (2.5-3.5个月) - *v1.1.6调整: +2.5周*

**v1.1.6变更影响**:
- Epic 14新增4个Story (14.9-14.12): 3层记忆系统整合
- 工作量增加: +2-2.5周
- 核心价值: 实现100%真实数据源，消除模拟数据

---

### Epic 0: 技术文档验证基础设施

**Epic ID**: Epic 0
**优先级**: P0 (BLOCKER)
**预计时间**: 1天 (7小时)
**依赖**: 无
**阻塞**: Epic 11, 12, 13, 15, 16

#### 目标
建立零幻觉开发的技术基础设施，确保所有后续Epic的开发都基于官方文档验证。

#### Story列表

| Story ID | Story名称 | 预计时间 |
|----------|----------|---------|
| Story 0.1 | 验证Context7文档访问 | 0.5小时 |
| Story 0.2 | 验证本地Skills可用性 | 0.5小时 |
| Story 0.3 | 创建技术验证示例Story | 2小时 |
| Story 0.4 | 更新PRD文档 | 1小时 |
| Story 0.5 | 建立开发时的强制验证机制 | 1.5小时 |
| Story 0.6 | Code Review检查清单集成 | 1小时 |

#### 关键交付物
- ✅ Context7文档访问验证报告 (`docs/verification/context7-access-test.md`)
- ✅ 本地Skills验证报告 (`docs/verification/local-skills-test.md`)
- ✅ 示例Story模板 (`docs/examples/story-12-1-verification-demo.md`)
- ✅ 更新后的PRD和README (本文档)

#### 成功标准
- Context7可访问所有必需文档（FastAPI, Neo4j）
- 本地Skills全部可用且返回正确文档
- 示例Story已创建并可作为后续Stories的参考模板
- PRD已更新包含Section 1.X技术验证协议
- 所有Agent（SM/Dev）理解技术验证新流程

**详细文档**: `docs/prd/EPIC-0-TECHNICAL-DOCUMENTATION-SETUP.md`

---

### Epic 11: FastAPI后端基础架构搭建

**Epic ID**: Epic 11
**优先级**: P0
**预计时间**: 2周 (43小时)
**依赖**: Epic 0（技术验证基础设施）
**阻塞**: Epic 12, 13, 14

⚠️ **技术验证要求**: 本Epic所有Stories必须遵守Section 1.X技术验证协议。

**强制文档来源**:
- Context7: `/websites/fastapi_tiangolo` (22,734 snippets)
- 查询主题示例: "dependency injection", "async operations", "APIRouter"

**验证检查点**:
- SM Agent编写Story时必须查询并记录API用法
- Dev Agent开发时必须在代码中添加文档引用注释
- Code Review必须验证所有API调用的正确性

#### 目标
搭建高性能、可扩展的FastAPI后端基础架构，作为Canvas学习系统Web化的核心API层。采用4层架构设计（API Layer → Service Layer → Core Layer → Infrastructure Layer），实现19个RESTful API endpoints，集成现有canvas_utils.py，支持异步操作和后台任务。

#### Story列表

| Story ID | Story名称 | 预计时间 | 优先级 |
|----------|----------|---------|--------|
| Story 11.1 | FastAPI应用初始化和基础配置 | 4-6小时 | P0 |
| Story 11.2 | 路由系统和APIRouter配置 | 5-7小时 | P0 |
| Story 11.3 | 依赖注入系统设计 | 6-8小时 | P0 |
| Story 11.4 | 中间件和错误处理 | 5-7小时 | P1 |
| Story 11.5 | 异步操作和后台任务 | 6-9小时 | P1 |
| Story 11.6 | API文档和测试框架 | 4-6小时 | P1 |

**总时间**: 30-43小时

#### 核心架构

**4层架构设计**:
```
backend/
├── app/
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置管理（Pydantic Settings）
│   ├── dependencies.py         # 全局依赖项（DI）
│   ├── api/v1/endpoints/       # API endpoints
│   │   ├── canvas.py           # Canvas操作 (6 endpoints)
│   │   ├── agents.py           # Agent调用 (9 endpoints)
│   │   └── review.py           # 检验白板 (3 endpoints)
│   ├── models/                 # Pydantic模型 (31个)
│   ├── services/               # 业务逻辑层
│   ├── core/                   # 核心层（canvas_utils.py集成）
│   └── middleware/             # 中间件
└── tests/                      # 测试
```

#### 关键交付物

**规划文档** (已完成):
- ✅ Sprint Kick-off: `docs/SPRINT-KICKOFF-EPIC-11.md`
- ✅ Epic 11详细规划: `docs/prd/EPIC-11-FASTAPI-BACKEND-DETAILED.md`
- ✅ 技术架构设计: `docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md`
- ✅ API接口规范: `docs/api/EPIC-11-API-SPECIFICATION.md`
- ✅ 数据模型设计: `docs/architecture/EPIC-11-DATA-MODELS.md`
- ✅ PM-SM交接文档: `docs/PM-TO-SM-HANDOFF-EPIC-11.md`

**代码交付物** (待开发):
- [ ] FastAPI应用核心代码（`app/main.py`, `app/config.py`）
- [ ] 19个API endpoints实现
- [ ] 31个Pydantic数据模型
- [ ] 中间件系统（日志、错误处理、CORS）
- [ ] 异步服务层
- [ ] pytest测试套件（覆盖率 ≥ 85%）

#### API Endpoints概览

**Canvas操作** (6 endpoints):
- `GET /api/v1/canvas/{canvas_name}` - 读取Canvas文件
- `POST /api/v1/canvas/{canvas_name}/nodes` - 创建节点
- `PUT /api/v1/canvas/{canvas_name}/nodes/{node_id}` - 更新节点
- `DELETE /api/v1/canvas/{canvas_name}/nodes/{node_id}` - 删除节点
- `POST /api/v1/canvas/{canvas_name}/edges` - 创建边
- `DELETE /api/v1/canvas/{canvas_name}/edges/{edge_id}` - 删除边

**Agent调用** (9 endpoints):
- `POST /api/v1/agents/decompose/basic` - 基础拆解
- `POST /api/v1/agents/decompose/deep` - 深度拆解
- `POST /api/v1/agents/score` - 评分
- `POST /api/v1/agents/explain/oral` - 口语化解释
- `POST /api/v1/agents/explain/clarification` - 澄清路径
- `POST /api/v1/agents/explain/comparison` - 对比表
- `POST /api/v1/agents/explain/memory` - 记忆锚点
- `POST /api/v1/agents/explain/four-level` - 四层次解释
- `POST /api/v1/agents/explain/example` - 例题教学

**检验白板** (3 endpoints):
- `POST /api/v1/review/generate` - 生成检验白板
- `GET /api/v1/review/{canvas_name}/progress` - 获取检验进度
- `POST /api/v1/review/sync` - 同步检验结果

**健康检查** (1 endpoint):
- `GET /api/v1/health` - 健康检查

#### 数据模型概览

**31个Pydantic模型**, 分为4类:
1. **Canvas模型** (10个): `NodeBase`, `NodeCreate`, `NodeUpdate`, `NodeRead`, `EdgeBase`, `EdgeCreate`, `EdgeRead`, `CanvasData`, `CanvasMeta`, `CanvasResponse`
2. **Agent模型** (12个): `DecomposeRequest`, `DecomposeResponse`, `ScoreRequest`, `ScoreResponse`, `ScoreDimensions`, `ScoreFeedback`, `ExplainRequest`, `ExplainResponse`, `AgentType`, `AgentMeta`, `AgentRecommendation`, `ErrorDetail`
3. **Review模型** (5个): `ReviewGenerateRequest`, `ReviewGenerateResponse`, `ReviewProgressResponse`, `ReviewSyncRequest`, `ReviewSyncResponse`
4. **Common模型** (4个): `SuccessResponse`, `ErrorResponse`, `PaginationMeta`, `HealthCheckResponse`

#### 技术栈

**核心框架**:
- FastAPI 0.104+
- Pydantic 2.5+
- Uvicorn 0.24+

**开发工具**:
- pytest 7.4+
- pytest-asyncio
- httpx (async client for testing)
- python-dotenv

**架构模式**:
- 依赖注入（`Depends()`）
- 异步优先（`async/await`）
- API版本控制（`/api/v1/`）
- Pydantic Settings配置管理

#### 成功标准

**功能验收**:
- ✅ 19个API endpoints全部实现并可正常调用
- ✅ 所有endpoints返回符合规范的JSON响应
- ✅ 错误处理覆盖所有预期错误场景（400/404/500）
- ✅ Canvas文件读写操作成功
- ✅ Agent调用成功返回结果

**技术验收**:
- ✅ 所有API调用已通过Context7验证
- ✅ 代码包含文档引用注释
- ✅ 依赖注入系统正常工作
- ✅ 中间件正确处理请求/响应
- ✅ 异步操作无阻塞

**测试验收**:
- ✅ pytest测试覆盖率 ≥ 85%
- ✅ 所有API endpoints有对应的测试用例
- ✅ 异步操作有集成测试
- ✅ 错误处理有单元测试

**文档验收**:
- ✅ FastAPI自动生成的Swagger文档可访问
- ✅ API endpoints有完整的docstring
- ✅ 所有技术实现可追溯到Context7查询

**性能验收**:
- ✅ 单个API请求响应时间 < 500ms
- ✅ Canvas文件读取 < 200ms
- ✅ Agent调用 < 5秒（不含Agent执行时间）

**集成验收**（与Epic 12配合）:
- ✅ FastAPI endpoints可被Epic 12 LangGraph调用
- ✅ 依赖注入系统支持LangGraph集成
- ✅ 异步操作不阻塞LangGraph workflow

**详细文档**: `docs/prd/EPIC-11-FASTAPI-BACKEND-DETAILED.md`

---

### Epic 12: LangGraph多Agent编排系统 (工具配备模式)

⚠️ **技术验证要求**: 本Epic所有Stories必须遵守Section 1.X技术验证协议。

**强制文档来源**:
- Local Skill: `@langgraph` (952页完整文档)
- Local Skill: `@graphiti` (完整框架文档)

**验证检查点**:
- SM Agent必须激活Skills并记录查询结果
- Dev Agent必须在代码中添加Skill引用注释
- Code Review必须验证StateGraph和节点创建的正确性

---

**Story序列**:
- **Story 12.1**: LangGraph StateGraph定义和写入历史机制 + **LangGraph Checkpointer集成**
  - 定义CanvasLearningState (含write_history字段)
  - 实现WriteHistory类
  - **[新增] 定义LangGraph checkpointer配置**:
    - checkpointer类型选型: PostgresSaver (生产) / InMemorySaver (开发)
    - thread_id生成策略: `canvas_{canvas_name}_{session_id}`
    - config参数结构定义 (包含thread_id, canvas_path, user_id, session_id)
  - **[新增] graph编译配置**:
    ```python
    from langgraph.checkpoint.postgres import PostgresSaver

    DB_URI = "postgresql://user:pass@localhost:5432/canvas_learning"
    checkpointer = PostgresSaver.from_conn_string(DB_URI)

    graph = builder.compile(checkpointer=checkpointer)
    ```
  - 验收:
    - State可正确传递
    - 写入历史正常记录
    - **[新增] checkpointer成功持久化对话状态**
    - **[新增] 可通过thread_id恢复之前的对话上下文**
    - **[SCP-003新增] Canvas备份文件组织规范**:
      - ✅ 备份文件夹`.canvas_backups/`在Vault根目录正确创建
      - ✅ 备份文件按规范命名：`{canvas_name}_{checkpoint_id}.canvas`
      - ✅ 每次checkpoint创建时自动生成对应备份文件
      - ✅ 备份清理机制正常工作：超过50个自动删除最旧的（跳过受保护的）
      - ✅ 备份文件夹在Obsidian文件浏览器中默认隐藏（需Story 13.1配合）
      - ✅ 回滚功能正确：`rollback_to_checkpoint()`能找到并恢复备份
      - ✅ 性能达标：备份创建+清理总耗时 <100ms

- **Story 12.2**: 共享Tools实现 (FileLock + 写入历史 + 3层记忆系统集成 + **LangGraph记忆系统协调**)
  - ✅ 实现write_to_canvas工具 (带FileLock和快照)
  - ✅ 实现create_md_file_for_canvas工具 (支持Vault相对路径) - **修复需求1**
  - 实现add_edge_to_canvas工具
  - 实现update_ebbinghaus工具
  - 实现query_graphiti_context工具
  - ✅ 实现store_to_graphiti_memory工具 - **修复需求2**
  - ✅ 实现store_to_temporal_memory工具 - **修复需求2**
  - ✅ 实现store_to_semantic_memory工具 - **修复需求2**
  - ✅ 实现query_graphiti_for_verification工具 - **修复需求3**
  - 跨平台FileLock测试 (Windows/macOS/Linux)
  - ✅ 文件路径可用性测试（验证Obsidian可正常打开生成的.md文件）
  - ✅ 记忆系统调度测试（验证在正确时机触发记忆存储）
  - 验收: 所有工具可并发调用,数据一致性100%

  **⚠️ 记忆系统调度时机矩阵** (修复需求2 + **精确化时序**):

  | Canvas操作 | Graphiti | Temporal | Semantic | LangGraph Checkpointer | 精确时序 |
  |-----------|----------|----------|----------|----------------------|---------|
  | 问题拆解 | ✅ | ✅ | ❌ | ✅ (自动) | 1. write_to_canvas完成 → Canvas文件修改<br>2. store_to_graphiti_memory → 知识图谱更新<br>3. store_to_temporal_memory → 时序事件记录<br>4. Agent返回new_state → LangGraph自动持久化到checkpointer |
  | 评分 | ✅ | ✅ | ❌ | ✅ (自动) | 1. 计算评分<br>2. write_to_canvas更新颜色 → Canvas文件修改<br>3. store_to_graphiti_memory(scoring_result) → 评分存入知识图谱<br>4. store_to_temporal_memory(score_event) → 时序记录<br>5. **track_learning_behavior(operation_type="scoring")** → 记录行为数据<br>6. **如果评分≥60**: EbbinghausReviewSystem.add_concept_for_review()<br>7. Agent返回new_state → LangGraph持久化 |
  | 生成解释文档 | ✅ | ✅ | ✅ | ✅ (自动) | 1. create_md_file_for_canvas → 生成.md文件<br>2. write_to_canvas创建FILE节点 → Canvas引用文件<br>3. store_to_graphiti_memory → 文档关联存入图谱<br>4. store_to_semantic_memory → 文档向量化<br>5. store_to_temporal_memory → 时序记录<br>6. Agent返回new_state → LangGraph持久化 |
  | 生成检验白板 | ✅ (查询+存储) | ✅ | ❌ | ✅ (自动) | 1. query_graphiti_for_verification → 查询上下文<br>2. 传递给verification-question-agent<br>3. write_to_canvas创建检验白板<br>4. store_to_graphiti_memory → 存储<br>5. Agent返回new_state → LangGraph持久化 |
  | **检验历史记录存储** (✅ v1.1.8新增) | ✅ (查询+存储) | ❌ | ❌ | ✅ (自动) | 1. **如果mode="targeted"**: query_review_history_from_graphiti → 查询历史薄弱概念<br>2. **calculate_targeted_review_weights** → 计算针对性权重<br>3. generate_review_canvas_file完成检验白板生成<br>4. **store_review_canvas_relationship** → 创建(review)-[:GENERATED_FROM {mode, results}]->(original)到Graphiti<br>5. Agent返回new_state → LangGraph持久化 |
  | 跨Canvas关联 | ✅ | ✅ | ❌ | ✅ (自动) | 1. 创建关联关系<br>2. store_to_graphiti_memory → 跨Canvas关系存入图谱<br>3. store_to_temporal_memory → 关联事件记录<br>4. Agent返回new_state → LangGraph持久化 |
  | **艾宾浩斯复习触发** (v1.1.6新增) | ✅ (查询) | ✅ (查询) | ✅ (查询) | ❌ | 1. **query_temporal_learning_behavior** → 检测未访问概念<br>2. **query_graphiti_concept_network** → 检测知识断层<br>3. **query_semantic_document_interactions** → 检测隐性需求<br>4. **合并触发列表** → EbbinghausReviewSystem批量添加<br>5. **optimize_fsrs_parameters_from_behavior** → 定期参数优化 |

  **[新增] 工具间协调机制**:

  **LangGraph Checkpointer职责**:
  - ✅ 存储Agent执行的中间状态（CanvasLearningState对象）
  - ✅ 支持多轮对话上下文持久化（thread_id）
  - ✅ 提供回滚能力（通过checkpoint ID和timestamp）
  - ⚠️ **不存储**：Canvas文件内容、知识图谱、学习事件

  **Graphiti知识图谱职责**:
  - ✅ 存储Canvas节点语义关系（概念关联、前置知识）
  - ✅ 支持跨Canvas查询和推荐
  - ⚠️ **不存储**：Agent执行状态、文档向量

  **Temporal时序记忆职责**:
  - ✅ 存储学习事件时间线（拆解时间、评分时间）
  - ✅ 支持学习进度分析和统计
  - ⚠️ **不存储**：文档内容、知识图谱

  **Semantic语义记忆职责**:
  - ✅ 存储AI生成文档的向量表示
  - ✅ 支持语义相似度检索
  - ⚠️ **不存储**：Canvas节点、知识图谱

  **[新增] 错误处理策略**:
  ```python
  def agent_node(state: CanvasLearningState):
      try:
          # Step 1: Canvas操作（关键路径）
          write_to_canvas(...)  # 失败 → 抛出异常，LangGraph回滚

          # Step 2: 记忆存储（非关键路径，最终一致性）
          try:
              store_to_graphiti_memory(...)
              store_to_temporal_memory(...)
          except MemoryStorageError as e:
              # 记录日志，不阻塞Canvas操作
              logger.error(f"Memory storage failed: {e}")
              # 可选：异步重试机制

          return new_state  # LangGraph自动持久化到checkpointer
      except CanvasOperationError as e:
          # Canvas操作失败 → 整个操作失败
          raise
  ```

  **调度规则说明**:
  1. **Graphiti (知识图谱)**: 所有Canvas操作都应存储，用于构建学习知识网络
  2. **Temporal (时序记忆)**: 所有Canvas操作都应存储，用于追踪学习历程
  3. **Semantic (语义记忆)**: 仅存储解释文档，用于文档向量检索
  4. **[新增] LangGraph Checkpointer**: 框架自动持久化Agent State，无需手动调用

  **[新增] 代码集成示例** (basic-decomposition Agent完整实现):
  ```python
  def basic_decomposition_agent_node(state: CanvasLearningState):
      session_id = state.session_id
      canvas_path = state.canvas_path
      config = state.config  # 包含thread_id

      # Step 1: 生成问题
      questions = generate_questions(state.concept)

      # Step 2: 写入Canvas（关键路径）
      for q in questions:
          write_to_canvas(canvas_path, {
              "id": generate_id(),
              "type": "text",
              "text": q,
              "color": "1",  # 红色问题节点
              "x": calc_x(), "y": calc_y()
          }, config)

      # Step 3: 存储到记忆系统（非关键路径）
      try:
          store_to_graphiti_memory(session_id, "decomposition", canvas_path, {
              "concept": state.concept,
              "questions": questions,
              "agent": "basic-decomposition"
          }, config)

          store_to_temporal_memory(session_id, "decomposition_completed",
              datetime.now(), {
                  "concept": state.concept,
                  "question_count": len(questions)
              }, config)
      except Exception as e:
          logger.error(f"Memory storage failed: {e}")

      # Step 4: 返回新State（LangGraph自动持久化到checkpointer）
      return CanvasLearningState(
          ...state,
          last_operation="decomposition",
          decomposition_results=questions
      )
  ```

- **Story 12.3**: 12个工具配备Agent节点创建
  - 使用create_react_agent创建12个Agent
  - 每个Agent配备shared_tools
  - 配置state_modifier (明确指示立即调用写入工具)
  - 验收: 每个Agent能独立调用工具,首个节点<1秒出现

- **Story 12.4**: canvas-orchestrator (Layer 3) 集成
  - 保留原有自然语言意图识别逻辑
  - 实现execute_with_langgraph方法
  - 将canvas-orchestrator的计划转换为LangGraph State
  - 验收: 用户命令正确路由到对应Agent

- **Story 12.5**: LangGraph Supervisor路由逻辑 (Layer 4) + **Checkpointer集成**
  - 实现supervisor_router函数
  - 支持单Agent和并行Agent调度
  - 实现条件路由 (根据operation类型)
  - **[新增] graph编译时配置checkpointer**:
    ```python
    from langgraph.checkpoint.postgres import PostgresSaver

    checkpointer = PostgresSaver.from_conn_string(DB_URI)
    supervisor_graph = builder.compile(checkpointer=checkpointer)
    ```
  - **[新增] config参数生成**:
    ```python
    def create_langgraph_config(canvas_path: str, user_id: str, session_id: str):
        canvas_name = Path(canvas_path).stem
        thread_id = f"canvas_{canvas_name}_{session_id}"

        return {
            "configurable": {
                "thread_id": thread_id,
                "canvas_path": canvas_path,
                "user_id": user_id,
                "session_id": session_id
            }
        }
    ```
  - **[新增] 多轮对话支持**:
    ```python
    # 第一轮：拆解问题
    config1 = create_langgraph_config("离散数学.canvas", "user123", "session_001")
    supervisor_graph.invoke({"operation": "decomposition", ...}, config1)

    # 第二轮：评分（继承第一轮上下文）
    config2 = create_langgraph_config("离散数学.canvas", "user123", "session_001")  # 相同thread_id
    supervisor_graph.invoke({"operation": "scoring", ...}, config2)
    # ↑ LangGraph自动加载第一轮的checkpoint，恢复上下文
    ```
  - 验收:
    - 路由准确率100%
    - 并行调度无冲突
    - **[新增] 多轮对话上下文正确恢复**

- **Story 12.6**: 回滚机制和错误恢复
  - 实现rollback_to_timestamp和rollback_n_steps
  - FastAPI /api/canvas/rollback端点
  - Obsidian Plugin回滚UI
  - 验收: 回滚准确率100%,<2秒完成

- **Story 12.7**: 端到端集成测试和性能验证 + **记忆系统一致性测试**
  - 测试12个Agent在真实Canvas上的完整流程
  - 验证Epic 10.2的性能提升（迁移后3-7倍提升）
  - 测试高并发场景 (最多50个节点组，每组最多100个Agent)
  - FileLock压力测试 (模拟500次并发写入)
  - **[新增] 记忆系统一致性测试**:
    - **测试1**: Checkpointer状态与Canvas文件一致性
    - **测试2**: Graphiti知识图谱与Canvas节点关系一致性
    - **测试3**: Temporal事件时间线完整性
    - **测试4**: Semantic向量与文档内容一致性
    - **测试5**: 多轮对话上下文恢复准确性
  - **[新增] 记忆存储失败容错测试**:
    - 模拟Graphiti连接失败 → Canvas操作应成功，记录错误日志
    - 模拟checkpointer写入延迟 → 不影响用户体验
  - 验收:
    - 所有功能可用
    - 性能不退化
    - 并发安全100%
    - **[新增] 记忆系统一致性100%，容错机制有效**

### Epic 13: Obsidian Plugin核心功能

**Story序列**:
- Story 13.1: Plugin项目初始化
- Story 13.2: Canvas API集成
- Story 13.3: API客户端实现
- Story 13.4: 核心命令 (拆解、评分、解释)
- Story 13.5: 右键菜单和快捷键
- Story 13.6: 设置面板
- Story 13.7: 错误处理

### Epic 14: 艾宾浩斯复习系统迁移+UI集成 (v1.1.6扩展)

**Epic性质**: 🔄 **迁移+集成+3层记忆整合** (基于已有ebbinghaus_review.py 870行代码)

**背景说明**:
- **已有实现**: `ebbinghaus_review.py` (870行, 2025-01-22完成)
  - ✅ SQLite数据库 (3表: review_schedules, review_history, user_review_stats)
  - ✅ 经典艾宾浩斯遗忘曲线算法 R(t)=e^(-t/S)
  - ✅ 基础CRUD操作 (添加概念、查询到期、更新复习记录)
- **本Epic目标 (v1.1.6扩展)**:
  1. **算法升级**: 从经典公式迁移到Py-FSRS (准确性提升20-30%)
  2. **Obsidian UI集成**: 创建侧边栏复习面板 (基于FR3.3 Mockup)
  3. **FastAPI接口封装**: 将Python函数封装为REST API
  4. **LangGraph集成**: 复习推送接入LangGraph Supervisor路由
  5. **⭐ v1.1.6新增: 3层记忆系统数据整合**
     - 集成Temporal Memory学习行为数据
     - 集成Graphiti概念关系网络
     - 集成Semantic Memory文档交互数据
     - 实现多维度优先级计算（4维度综合评分）
     - 实现行为监控触发机制（触发点4）
     - 实现FSRS参数自适应优化

**迁移策略**:
```python