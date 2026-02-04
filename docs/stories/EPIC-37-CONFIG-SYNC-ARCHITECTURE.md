# EPIC-37: 插件配置同步架构重构

## 状态：待实施 (Pending)
## 优先级：P1 (用户分发阻塞项)
## 预估工程量：8-10 小时

---

## 1. 问题描述

### 1.1 核心问题

**插件 UI 中的配置项是"摆设"，不会同步到后端，导致用户困惑和分发困难。**

### 1.2 问题发现过程

在 Epic 30 测试过程中发现：
1. 用户在 Obsidian 插件设置中配置了 Neo4j 连接地址 `bolt://localhost:7687`
2. 后端 `.env` 中配置了 `NEO4J_URI=bolt://localhost:7688`
3. **两套配置完全独立，不同步**
4. 用户以为配置生效了，实际数据写入了错误的数据库

### 1.3 影响范围

| 配置项 | 插件 UI | 后端支持 | 是否同步 | 影响 |
|--------|---------|---------|---------|------|
| `apiBaseUrl` | ✅ 有 | ✅ 使用 | ✅ 直接使用 | 无问题 |
| `neo4jUri` | ✅ 有 | ✅ 从 .env | ❌ 不同步 | **用户困惑** |
| `neo4jUser` | ✅ 有 | ✅ 从 .env | ❌ 不同步 | **用户困惑** |
| `neo4jPassword` | ✅ 有 | ✅ 从 .env | ❌ 不同步 | **安全风险** |
| `graphitiMcpUrl` | ✅ 有 | ❌ 无配置 | ❌ 完全无效 | **功能缺失** |
| `graphitiGroupId` | ✅ 有 | ❌ 无配置 | ❌ 完全无效 | **多租户失效** |

### 1.4 用户分发场景问题

当插件分发给其他用户时：

```
用户 A 部署到 server-a.com:
├── Neo4j: bolt://server-a:7688
├── Graphiti: http://server-a:8001/sse
└── GroupId: user-a-project

当前流程（繁琐且易错）：
1. 用户手动编辑后端 .env 文件
2. 重启后端服务
3. 在插件 UI 中重复输入相同配置（实际无效）
4. 用户困惑：为什么 UI 配置和 .env 要写两遍？

期望流程（简洁）：
1. 用户在插件 UI 中配置
2. 点击"同步到后端"
3. 完成
```

---

## 2. 当前架构分析

### 2.1 数据流图（现状）

```
┌─────────────────────────────────────────────────────────────────┐
│                     Obsidian 插件                               │
├─────────────────────────────────────────────────────────────────┤
│  设置面板 (PluginSettingsTab.ts)                                │
│  ┌──────────────────┐                                           │
│  │ Neo4j URI        │ → 保存到 Obsidian 本地存储                │
│  │ Neo4j Password   │ → 保存到 Obsidian 本地存储                │
│  │ Graphiti URL     │ → 保存到 Obsidian 本地存储                │
│  │ Graphiti GroupId │ → 保存到 Obsidian 本地存储                │
│  └──────────────────┘                                           │
│           ↓                                                     │
│  这些配置 ❌ 从不发送到后端                                      │
│           ↓                                                     │
│  ApiClient.ts 只使用 apiBaseUrl                                 │
│           ↓                                                     │
│  POST {apiBaseUrl}/memory/episodes/batch                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI 后端                                │
├─────────────────────────────────────────────────────────────────┤
│  config.py 只从 .env 读取配置                                    │
│  ┌──────────────────┐                                           │
│  │ NEO4J_URI        │ ← 从 backend/.env 读取                    │
│  │ NEO4J_PASSWORD   │ ← 从 backend/.env 读取                    │
│  │ (无 Graphiti)    │ ← ❌ 后端不支持此配置                      │
│  └──────────────────┘                                           │
│           ↓                                                     │
│  neo4j_client.py 使用后端配置连接 Neo4j                          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 关键代码位置

| 组件 | 文件路径 | 行号 | 说明 |
|------|---------|------|------|
| 插件设置类型 | `canvas-progress-tracker/obsidian-plugin/src/types/settings.ts` | 311-369 | 定义所有配置字段 |
| 插件设置 UI | `canvas-progress-tracker/obsidian-plugin/src/settings/PluginSettingsTab.ts` | 1086-1277 | Neo4j/Graphiti 配置面板 |
| 插件 API 客户端 | `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts` | 全文 | 只使用 baseUrl |
| 后端配置 | `backend/app/config.py` | 320-387 | Neo4j 配置定义 |
| 后端 Neo4j 客户端 | `backend/app/clients/neo4j_client.py` | 1743-1759 | 使用后端配置 |
| 后端 Graphiti 客户端 | `backend/app/clients/graphiti_client.py` | 全文 | 无动态配置支持 |

---

## 3. 解决方案设计

### 3.1 方案选型

| 方案 | 描述 | 工程量 | 用户体验 | 推荐 |
|------|------|--------|---------|------|
| A | 删除无用配置 + 文档说明 | 2h | ⭐⭐⭐ | 临时方案 |
| B | **添加配置同步 API** | 8h | ⭐⭐⭐⭐⭐ | **✅ 推荐** |
| C | 完整配置管理系统 | 20h+ | ⭐⭐⭐⭐⭐ | 过度设计 |

**选择方案 B：添加配置同步 API**

### 3.2 目标架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Obsidian 插件                               │
├─────────────────────────────────────────────────────────────────┤
│  设置面板 (PluginSettingsTab.ts)                                │
│  ┌──────────────────┐                                           │
│  │ Neo4j URI        │                                           │
│  │ Neo4j Password   │                                           │
│  │ Graphiti URL     │                                           │
│  │ Graphiti GroupId │                                           │
│  └──────────────────┘                                           │
│           ↓                                                     │
│  [同步到后端] 按钮 ← 新增                                        │
│           ↓                                                     │
│  ApiClient.syncConfig() ← 新增方法                              │
│           ↓                                                     │
│  POST {apiBaseUrl}/api/v1/config/sync                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI 后端                                │
├─────────────────────────────────────────────────────────────────┤
│  新增: endpoints/config.py                                      │
│  ┌──────────────────┐                                           │
│  │ POST /config/sync│ ← 接收插件配置                            │
│  │   验证配置有效性  │                                           │
│  │   更新运行时配置  │                                           │
│  │   可选: 持久化   │                                           │
│  └──────────────────┘                                           │
│           ↓                                                     │
│  新增: services/config_sync_service.py                          │
│           ↓                                                     │
│  热更新 Neo4j/Graphiti 客户端配置（无需重启）                    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 API 设计

#### 3.3.1 配置同步端点

```yaml
POST /api/v1/config/sync
Content-Type: application/json

Request Body:
{
  "neo4j": {
    "uri": "bolt://server-a:7688",
    "user": "neo4j",
    "password": "encrypted_or_plain"
  },
  "graphiti": {
    "mcpUrl": "http://server-a:8001/sse",
    "groupId": "user-project-id"
  }
}

Response (200 OK):
{
  "status": "updated",
  "applied": {
    "neo4j": true,
    "graphiti": true
  },
  "warnings": [],
  "restartRequired": false
}

Response (400 Bad Request):
{
  "status": "error",
  "errors": [
    {"field": "neo4j.uri", "message": "无法连接到 Neo4j"}
  ]
}
```

#### 3.3.2 配置查询端点

```yaml
GET /api/v1/config/current

Response (200 OK):
{
  "neo4j": {
    "uri": "bolt://localhost:7688",
    "user": "neo4j",
    "enabled": true,
    "connected": true
  },
  "graphiti": {
    "mcpUrl": "http://localhost:8001/sse",
    "groupId": "canvas-learning-system",
    "enabled": false
  }
}
```

### 3.4 安全考虑

1. **密码传输**：使用 HTTPS 或支持加密传输
2. **密码存储**：后端不持久化密码，仅运行时使用
3. **权限控制**：可选添加 API Key 验证
4. **配置验证**：同步前验证配置有效性（尝试连接）

---

## 4. 实施计划

### 4.1 阶段 1：后端支持 (4-5h)

#### Story 37.1: 后端配置模型扩展
- [ ] 在 `config.py` 添加 Graphiti 配置字段
- [ ] 添加 `GRAPHITI_MCP_URL` 环境变量支持
- [ ] 添加 `GRAPHITI_GROUP_ID` 环境变量支持

#### Story 37.2: 配置同步 API 端点
- [ ] 创建 `backend/app/api/v1/endpoints/config.py`
- [ ] 实现 `POST /api/v1/config/sync` 端点
- [ ] 实现 `GET /api/v1/config/current` 端点
- [ ] 添加配置验证逻辑

#### Story 37.3: 配置热更新服务
- [ ] 创建 `backend/app/services/config_sync_service.py`
- [ ] 实现 Neo4j 客户端重连逻辑
- [ ] 实现 Graphiti 配置更新逻辑

### 4.2 阶段 2：插件集成 (3-4h)

#### Story 37.4: ApiClient 扩展
- [ ] 在 `ApiClient.ts` 添加 `syncConfig()` 方法
- [ ] 在 `ApiClient.ts` 添加 `getCurrentConfig()` 方法
- [ ] 添加错误处理和重试逻辑

#### Story 37.5: 设置面板增强
- [ ] 在 `PluginSettingsTab.ts` 添加"同步到后端"按钮
- [ ] 添加同步状态指示器（同步中/已同步/失败）
- [ ] 配置变更时提示用户同步
- [ ] 可选：自动同步模式

#### Story 37.6: 用户引导优化
- [ ] 首次配置向导
- [ ] 配置不同步警告提示
- [ ] 部署文档更新

### 4.3 阶段 3：测试和文档 (1-2h)

#### Story 37.7: 测试
- [ ] 单元测试：配置同步 API
- [ ] 集成测试：插件 → 后端 → Neo4j/Graphiti
- [ ] 端到端测试：配置变更 → 数据写入验证

#### Story 37.8: 文档
- [ ] 更新部署指南
- [ ] 添加配置同步说明
- [ ] 更新 CLAUDE.md

---

## 5. 验收标准

### 5.1 功能验收

- [ ] 用户在插件 UI 修改 Neo4j URI 后，点击同步，后端使用新配置
- [ ] 用户在插件 UI 修改 Graphiti 配置后，点击同步，后端使用新配置
- [ ] 配置同步失败时，显示明确的错误信息
- [ ] 后端重启后，保留用户同步的配置（可选：持久化）

### 5.2 用户体验验收

- [ ] 用户无需手动编辑后端 `.env` 文件
- [ ] 配置流程：打开设置 → 输入配置 → 点击同步 → 完成
- [ ] 同步状态清晰可见

### 5.3 分发验收

- [ ] 新用户部署时，只需配置插件 UI
- [ ] 多用户场景下，每个用户可以有独立的 GroupId
- [ ] 部署文档简洁明了

---

## 6. 风险和缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 配置同步失败 | 用户数据写入错误位置 | 同步前验证配置有效性 |
| 密码泄露 | 安全风险 | HTTPS + 运行时存储 |
| 后端重启丢失配置 | 需要重新同步 | 可选持久化到配置文件 |
| 并发配置冲突 | 配置覆盖 | 添加配置版本号 |

---

## 7. 临时解决方案（在 EPIC-37 实施前）

在完整方案实施前，用户分发时的临时流程：

### 7.1 部署清单

```markdown
## Canvas Learning System 部署指南（临时版）

### 步骤 1: 配置后端
1. 复制 `backend/.env.example` → `backend/.env`
2. 修改以下配置：
   - `NEO4J_URI=bolt://your-server:7688`
   - `NEO4J_PASSWORD=your_secure_password`

### 步骤 2: 启动服务
docker-compose up -d neo4j
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000

### 步骤 3: 配置插件
1. 打开 Obsidian 设置 → Canvas Review System
2. 连接设置：输入后端 API 地址
3. 记忆系统：
   - ⚠️ Neo4j 配置仅供参考，实际配置在后端 .env
   - ⚠️ Graphiti 配置当前无效，待 EPIC-37 实施
```

### 7.2 插件 UI 提示文字（可立即添加）

在 Neo4j 和 Graphiti 配置区域添加警告：

```typescript
// PluginSettingsTab.ts
containerEl.createEl('div', {
    cls: 'setting-item-description',
    text: '⚠️ 注意：此配置仅供参考。实际连接配置由后端 .env 文件管理。'
});
```

---

## 8. 相关文档

- [Epic 30: Memory System Complete Activation](./EPIC-30-MEMORY-SYSTEM-COMPLETE-ACTIVATION.md)
- [Story 30.1: Neo4j Docker Deployment](./30.1.story.md)
- [Story 36.9: Graphiti JSON Dual Write](./36.9.story.md)

---

## 变更历史

| 日期 | 版本 | 变更内容 | 作者 |
|------|------|---------|------|
| 2026-02-03 | 1.0 | 初始版本 | Claude |
