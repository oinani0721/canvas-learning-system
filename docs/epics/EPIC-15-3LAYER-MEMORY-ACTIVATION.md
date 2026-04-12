> **DEPRECATED** - 此Epic已合并到 [Epic 30: Memory System Complete Activation](./EPIC-30-MEMORY-SYSTEM-COMPLETE-ACTIVATION.md)
>
> 合并日期: 2026-01-15 | 请参考Epic 30获取最新实施计划

---

# Epic 15: 3层记忆检索系统启用 - Brownfield Enhancement

**Epic ID**: EPIC-15
**类型**: Brownfield Enhancement
**优先级**: P0 (High)
**预估 Stories**: 3
**状态**: Ready for Implementation
**创建日期**: 2026-01-15
**Epic Owner**: PM (John)

---

## Epic 目标

启用 Canvas 学习系统中已实现但未激活的 3 层记忆检索和 Agentic RAG 功能，使 Obsidian 插件能够实时记录学习行为并获得智能复习建议。

---

## 背景与调研结果

### 现有系统上下文

Canvas Learning System 的 Agentic RAG 架构已在 Epic 12 中完成核心实现：
- ✅ StateGraph 5路并行检索
- ✅ RRF/Weighted/Cascade 融合算法
- ✅ Hybrid Reranking (Local + Cohere)
- ✅ 质量控制循环

### 3层记忆系统实现状态

| 层 | 技术 | 代码位置 | 完成度 | 当前状态 |
|---|---|---|---|---|
| **Layer 1: Graphiti** | Neo4j 知识图谱 | `graphiti_client.py` (933行) | 75% | ⚠️ JSON模拟,需Neo4j |
| **Layer 2: LanceDB** | 语义向量库 | `lancedb_client.py` (789行) | **100%** | ✅ 生产就绪 |
| **Layer 3: Temporal** | FSRS+SQLite | `temporal_memory.py` (470行) | 92% | ✅ 核心完整 |

### 关键发现

1. **MCP graphiti-memory 已可用** ✅ - 在 Claude Code 中已配置并运行
2. **Obsidian 插件已有完整配置框架** ✅ - 只需启用设置
3. **后端 API 已实现** ✅ - `/api/v1/memory/*` 端点就绪
4. **Neo4j 使用 JSON 模拟** ⚠️ - 需要部署 Docker Neo4j

### 插件现有记忆系统设置

```typescript
// 文件: canvas-progress-tracker/obsidian-plugin/src/types/settings.ts
// 默认值 (当前全部禁用):
neo4jUri: 'bolt://localhost:7687',
neo4jUser: 'neo4j',
neo4jPassword: '',
neo4jEnabled: false,          // ← 需要启用

lancedbPath: '',
lancedbCudaEnabled: false,
lancedbEnabled: false,        // ← 需要启用

graphitiGroupId: 'canvas-learning-system',
graphitiMcpUrl: 'http://localhost:8000/sse',
graphitiEnabled: false,       // ← 需要启用
```

---

## 增强详情

### 添加/修改内容

1. 部署 Docker Neo4j 容器
2. 修改 `neo4j_client.py` 为真实 Neo4j 驱动
3. 启用插件记忆系统默认设置
4. 添加学习事件 API 调用到插件

### 集成方式

- **后端**: Neo4j 驱动替换 JSON 模拟
- **插件**: 在 Canvas 事件回调中调用后端 Memory API

### 成功标准

- Neo4j 知识图谱存储学习关系
- 插件能实时记录学习事件到后端
- FSRS 复习调度正常工作
- LanceDB 向量检索响应 < 400ms

---

## Stories

### Story 15.1: 部署 Docker Neo4j 并切换后端到真实驱动

**目标**: 完成 Neo4j 环境配置，使后端能连接真实图数据库

**验收标准**:
- [ ] AC-15.1.1: Docker Neo4j 5.15 容器成功启动
- [ ] AC-15.1.2: `backend/app/config.py` 添加 Neo4j 配置项 (URI/用户名/密码/启用标志)
- [ ] AC-15.1.3: `neo4j_client.py` 重构为真实 Neo4j 驱动，保留 JSON fallback
- [ ] AC-15.1.4: Neo4j Browser (localhost:7474) 可访问并执行测试查询

**技术细节**:
```powershell
docker run -d --name neo4j-canvas -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/canvas2026 \
  -e NEO4J_PLUGINS='["apoc"]' \
  -v neo4j-data:/data \
  neo4j:5.15-community
```

---

### Story 15.2: 启用 Obsidian 插件记忆系统配置

**目标**: 修改插件默认设置并实现学习事件 API 调用

**验收标准**:
- [ ] AC-15.2.1: `settings.ts` 默认值 `neo4jEnabled/lancedbEnabled/graphitiEnabled = true`
- [ ] AC-15.2.2: 实现 `recordLearningEvent()` 方法调用后端 `/api/v1/memory/episodes`
- [ ] AC-15.2.3: Canvas 节点交互时自动触发学习事件记录
- [ ] AC-15.2.4: 插件重新构建并部署到 Obsidian 插件目录

**技术细节**:
```typescript
async recordLearningEvent(canvasPath: string, concept: string, score: number) {
    if (!this.settings.graphitiEnabled) return;
    const response = await fetch(`${this.settings.claudeCodeUrl}/api/v1/memory/episodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: 'default_user',
            canvas_path: canvasPath,
            concept: concept,
            score: score,
            episode_type: 'learning'
        })
    });
}
```

---

### Story 15.3: 端到端验证和文档更新

**目标**: 验证完整记忆系统功能并更新项目文档

**验收标准**:
- [ ] AC-15.3.1: Neo4j 连接测试通过 (Python 驱动 + Cypher 查询)
- [ ] AC-15.3.2: Memory API CRUD 操作验证通过
- [ ] AC-15.3.3: Obsidian 插件 Network 请求到后端成功
- [ ] AC-15.3.4: LanceDB 向量检索 P95 < 400ms
- [ ] AC-15.3.5: FSRS 复习调度 `get_weak_concepts()` 返回正确结果
- [ ] AC-15.3.6: CLAUDE.md 更新记录记忆系统启用状态

---

## 兼容性要求

- [x] 现有 API 保持不变 - Memory API 端点签名无变化
- [x] 数据库 schema 变更向后兼容 - Neo4j 为新增，不影响现有 JSON 存储
- [x] UI 变更遵循现有模式 - 使用现有 "🧠 记忆系统" 设置面板
- [x] 性能影响最小 - Neo4j 查询应 < 50ms，LanceDB 已验证 P95 < 400ms

---

## 风险缓解

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| **主要风险**: Docker Neo4j 启动失败 | 知识图谱不可用 | 保留 JSON 模拟作为 fallback |
| 插件 API 调用超时 | 学习事件丢失 | 本地缓存 + 重试机制 |
| LanceDB 索引损坏 | 向量检索失败 | 提供重建索引脚本 |
| FSRS 参数不优 | 复习效果差 | 月度自动优化 |

**回滚计划**:
- 还原 `neo4j_client.py` 到 JSON 模式
- 通过环境变量 `NEO4J_ENABLED=false` 切换
- 禁用插件记忆设置

---

## Definition of Done

- [ ] Neo4j Docker 容器运行并可通过 Browser 访问
- [ ] 后端 Memory API 使用真实 Neo4j 驱动
- [ ] Obsidian 插件记忆系统设置默认启用
- [ ] 插件能成功调用后端 `/api/v1/memory/episodes`
- [ ] 现有功能通过回归测试验证
- [ ] 集成点工作正常 (插件 → 后端 → Neo4j)
- [ ] CLAUDE.md 文档更新记录启用状态

---

## 验证清单

### 范围验证
- [x] Epic 可在 1-3 个 stories 内完成
- [x] 不需要架构文档 - 使用现有架构
- [x] 增强遵循现有模式 - 记忆系统框架已存在
- [x] 集成复杂性可管理 - 主要是配置和启用

### 风险评估
- [x] 对现有系统的风险较低 - fallback 机制存在
- [x] 回滚计划可行 - 环境变量控制
- [x] 测试方法覆盖现有功能 - 端到端验证脚本
- [x] 团队对集成点有足够了解 - 代码已调研

### 完整性检查
- [x] Epic 目标清晰可实现
- [x] Stories 适当划分
- [x] 成功标准可衡量
- [x] 依赖项已识别 (Docker Desktop)

---

## 文件修改清单

### 必须修改的文件

| 文件 | 修改类型 | 目的 |
|---|---|---|
| `backend/app/config.py` | 添加配置 | Neo4j URI/用户名/密码 |
| `backend/app/clients/neo4j_client.py` | 重构 | 切换到真实 Neo4j 驱动 |
| `obsidian-plugin/src/types/settings.ts` | 修改默认值 | 启用记忆系统 |
| `obsidian-plugin/src/index.ts` | 添加代码 | 学习事件 API 调用 |

### 新增文件

| 文件 | 目的 |
|---|---|
| `backend/app/clients/neo4j_driver.py` | 真实 Neo4j 驱动封装 (可选) |
| `docker-compose.yml` | Neo4j 容器编排 (可选) |

---

## Story Manager 交接

**Story Manager Handoff:**

"请为此棕地 Epic 开发详细的用户故事。关键注意事项:

- 这是对运行 **FastAPI + TypeScript Obsidian 插件** 的现有系统的增强
- 集成点:
  - 后端 Memory API (`/api/v1/memory/*`)
  - Neo4j Bolt 连接 (`bolt://localhost:7687`)
  - MCP graphiti-memory 服务器
- 需要遵循的现有模式:
  - `PluginSettings` 接口配置模式
  - `neo4j_client.py` 客户端封装模式
  - 后端启动事件初始化模式
- 关键兼容性要求:
  - 保持 `NEO4J_ENABLED` 环境变量控制
  - 保留 JSON fallback 模式
- 每个 story 必须包含验证现有功能保持完整的测试

Epic 应在交付 **3层记忆检索 + Agentic RAG 启用** 的同时保持系统完整性。"

---

## 预期结果

启用后，Canvas Learning System 将具备：
- ✅ Neo4j 知识图谱存储学习关系
- ✅ 实时记录学习行为到后端
- ✅ FSRS 算法驱动的智能复习调度
- ✅ LanceDB 向量语义检索
- ✅ 薄弱概念识别和优先排序
- ✅ MCP Graphiti 知识图谱查询
- ✅ 5路并行 Agentic RAG 检索

---

## 相关文档

- **实施计划**: `C:\Users\ROG\.claude\plans\elegant-foraging-forest.md`
- **Epic 12 原始定义**: `docs/epics/EPIC-12-3LAYER-MEMORY-AGENTIC-RAG.md`
- **技术方案**: `docs/architecture/COMPREHENSIVE-TECHNICAL-PLAN-3LAYER-MEMORY-AGENTIC-RAG.md`

## Relations

