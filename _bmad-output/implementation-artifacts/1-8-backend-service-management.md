# Story 1.8: 后端服务一键启动与数据管理

Status: ready-for-dev

## Story

As a 用户,
I want 通过 Obsidian 命令面板一键启动/重启后端服务，并能手动触发数据备份和恢复,
so that 我能方便地管理系统运行和数据安全。

## Acceptance Criteria

1. **AC-1: 命令面板——启动后端服务**
   - **Given** 用户打开 Obsidian 命令面板（Ctrl+P）
   - **When** 输入"Canvas: 启动后端"并执行
   - **Then** 插件通过 Node.js `child_process` 执行 `docker-compose up -d`（在项目 backend 目录）
   - **And** 启动过程中显示 Obsidian Notice 进度提示："正在启动后端服务..."
   - **And** 启动成功后显示"后端服务已启动"
   - **And** 启动失败时显示错误原因（如 Docker Desktop 未运行）

2. **AC-2: 命令面板——重启后端服务**
   - **Given** 用户在命令面板输入"Canvas: 重启后端"
   - **When** 执行命令
   - **Then** 执行 `docker-compose restart` 重启所有后端容器
   - **And** 重启过程中显示进度提示："正在重启后端服务..."
   - **And** 重启完成后显示"后端服务已重启"
   - **And** 重启后自动触发健康检查验证各服务就绪

3. **AC-3: 命令面板——停止后端服务**
   - **Given** 用户在命令面板输入"Canvas: 停止后端"
   - **When** 执行命令
   - **Then** 执行 `docker-compose stop` 停止所有后端容器（保留数据卷）
   - **And** 停止完成后显示"后端服务已停止"

4. **AC-4: 命令面板——备份数据**
   - **Given** 用户在命令面板输入"Canvas: 备份数据"
   - **When** 执行命令
   - **Then** 备份 Neo4j 数据目录（`docker/neo4j/data`）+ LanceDB 数据目录 + 插件配置到指定备份目录
   - **And** 备份目录以时间戳命名（如 `backups/2026-03-16T12-00-00/`）
   - **And** 备份过程中显示进度提示："正在备份数据... (1/3) Neo4j / (2/3) LanceDB / (3/3) 配置"
   - **And** 备份完成后显示"备份完成：backups/2026-03-16T12-00-00/"
   - **And** 备份失败时显示错误原因并清理不完整的备份目录

5. **AC-5: 命令面板——恢复数据**
   - **Given** 用户在命令面板输入"Canvas: 恢复数据"
   - **When** 执行命令
   - **Then** 弹出备份列表（列出 backups/ 目录下所有可用备份，按时间倒序）
   - **And** 用户选择备份点后，确认对话框提示"恢复将覆盖当前数据，是否继续？"
   - **And** 确认后停止后端服务 → 恢复 Neo4j + LanceDB + 配置 → 重新启动后端服务
   - **And** 恢复过程中显示进度提示："正在恢复数据... (1/5) 停止服务 / (2/5) 恢复 Neo4j / (3/5) 恢复 LanceDB / (4/5) 恢复配置 / (5/5) 重启服务"
   - **And** 恢复完成后显示"数据恢复完成"
   - **And** 恢复失败时回滚到恢复前状态

6. **AC-6: Docker 环境检测**
   - **Given** 用户执行任何后端服务管理命令
   - **When** 命令执行前
   - **Then** 自动检测 Docker Desktop / Docker Engine 是否运行
   - **And** Docker 未运行时显示"请先启动 Docker Desktop"并阻止执行
   - **And** docker-compose.yml 路径不存在时显示"docker-compose.yml 未找到"并阻止执行

7. **AC-7: 启动后健康检查联动**
   - **Given** 用户执行"Canvas: 启动后端"或"Canvas: 重启后端"
   - **When** docker-compose 命令完成
   - **Then** 自动调用 `/api/v1/system/health` 等待后端 API 就绪（最多等 60s，每 3s 轮询）
   - **And** API 就绪后更新 system-state 的健康状态（联动 Story 1.2 SetupWizard / Story 1.3 HealthPanel）
   - **And** 超时仍未就绪时显示"后端服务启动但 API 未就绪，请检查日志"

## Tasks / Subtasks

- [ ] **Task 1: Docker 命令执行服务** (AC: #1, #2, #3, #6)
  - [ ] 1.1 创建 `obsidian-canvas-learning/src/services/docker-manager.ts`
  - [ ] 1.2 实现 DockerManager 类：
    ```typescript
    class DockerManager {
      private projectPath: string;  // docker-compose.yml 所在目录

      async checkDockerAvailable(): Promise<{available: boolean; error?: string}>
      async startServices(): Promise<void>
      async restartServices(): Promise<void>
      async stopServices(): Promise<void>
      private async execDockerCompose(args: string[]): Promise<{stdout: string; stderr: string; exitCode: number}>
    }
    ```
  - [ ] 1.3 实现 `checkDockerAvailable()`：
    - 执行 `docker info` 检测 Docker 是否运行
    - 检测 docker-compose.yml 文件是否存在于 projectPath
    - 返回检测结果和错误信息
  - [ ] 1.4 实现 `execDockerCompose(args)` 私有方法：
    - 使用 Node.js `child_process.execFile` 执行 `docker-compose` 命令
    - 设置 cwd 为 projectPath
    - 捕获 stdout/stderr
    - 超时控制：120s（docker-compose up 可能较慢）
    - 处理 Windows/macOS/Linux 的 docker-compose 路径差异（`docker-compose` vs `docker compose`）
  - [ ] 1.5 实现 `startServices()`：调用 `execDockerCompose(['up', '-d'])`
  - [ ] 1.6 实现 `restartServices()`：调用 `execDockerCompose(['restart'])`
  - [ ] 1.7 实现 `stopServices()`：调用 `execDockerCompose(['stop'])`
  - [ ] 1.8 导出 singleton `export const dockerManager = new DockerManager()`

- [ ] **Task 2: 数据备份服务** (AC: #4)
  - [ ] 2.1 创建 `obsidian-canvas-learning/src/services/backup-manager.ts`
  - [ ] 2.2 实现 BackupManager 类：
    ```typescript
    interface BackupProgress {
      step: number;
      totalSteps: number;
      description: string;
    }

    class BackupManager {
      private backupBaseDir: string;  // backups/ 目录路径

      async createBackup(onProgress: (p: BackupProgress) => void): Promise<string>  // 返回备份目录路径
      async listBackups(): Promise<BackupInfo[]>
      async restoreBackup(backupPath: string, onProgress: (p: BackupProgress) => void): Promise<void>
      private async copyDirectory(src: string, dest: string): Promise<void>
    }
    ```
  - [ ] 2.3 实现 `createBackup()`：
    - 创建时间戳命名目录：`backups/YYYY-MM-DDTHH-mm-ss/`
    - Step 1/3：复制 `docker/neo4j/data/` → 备份目录 `neo4j-data/`
    - Step 2/3：复制 LanceDB 数据目录 → 备份目录 `lancedb-data/`
    - Step 3/3：复制插件配置（`data.json`）→ 备份目录 `config/`
    - 写入 `backup-meta.json`（时间戳、版本、文件数）
    - 任何步骤失败 → 清理不完整的备份目录
  - [ ] 2.4 实现 `copyDirectory()` 私有方法：
    - 使用 Node.js `fs.cp`（递归复制目录）
    - 跳过锁文件和临时文件（`.lock`、`.tmp`、`__pycache__`）
  - [ ] 2.5 实现 `listBackups()`：
    - 扫描 `backups/` 目录下所有子目录
    - 读取每个目录中的 `backup-meta.json`
    - 按时间倒序返回 `BackupInfo[]`
  - [ ] 2.6 导出 singleton `export const backupManager = new BackupManager()`

- [ ] **Task 3: 数据恢复服务** (AC: #5)
  - [ ] 3.1 在 `backup-manager.ts` 中实现 `restoreBackup()`：
    - Step 1/5：停止后端服务（调用 `dockerManager.stopServices()`）
    - Step 2/5：备份当前数据到 `backups/_pre-restore-TIMESTAMP/`（恢复前快照）
    - Step 3/5：恢复 Neo4j 数据（清空目标 → 复制备份数据）
    - Step 4/5：恢复 LanceDB 数据（清空目标 → 复制备份数据）
    - Step 5/5：恢复配置 + 重新启动后端服务（调用 `dockerManager.startServices()`）
    - 任何步骤失败 → 回滚：从 `_pre-restore` 快照恢复原始数据
  - [ ] 3.2 恢复前自动创建"恢复前快照"，确保失败时可回滚
  - [ ] 3.3 恢复完成后清理 `_pre-restore` 临时快照

- [ ] **Task 4: Obsidian 命令注册** (AC: #1, #2, #3, #4, #5, #6)
  - [ ] 4.1 修改 `obsidian-canvas-learning/main.ts`：注册 5 个 Obsidian 命令
  - [ ] 4.2 注册命令 `canvas-start-backend`：
    ```typescript
    this.addCommand({
      id: 'canvas-start-backend',
      name: 'Canvas: 启动后端',
      callback: async () => { /* ... */ }
    });
    ```
  - [ ] 4.3 注册命令 `canvas-restart-backend`：`Canvas: 重启后端`
  - [ ] 4.4 注册命令 `canvas-stop-backend`：`Canvas: 停止后端`
  - [ ] 4.5 注册命令 `canvas-backup-data`：`Canvas: 备份数据`
  - [ ] 4.6 注册命令 `canvas-restore-data`：`Canvas: 恢复数据`
  - [ ] 4.7 每个命令的回调实现模式：
    - 前置检查：调用 `dockerManager.checkDockerAvailable()`（备份/恢复也需要 Docker 路径）
    - 执行操作：调用对应 service 方法
    - 进度提示：通过 `new Notice(message, 0)` 创建持久通知，完成后更新或关闭
    - 错误处理：try-catch 捕获异常，通过 Notice 显示错误

- [ ] **Task 5: 恢复命令——备份选择 UI** (AC: #5)
  - [ ] 5.1 恢复命令触发时：
    - 调用 `backupManager.listBackups()` 获取备份列表
    - 使用 Obsidian `SuggestModal` 弹出备份列表供用户选择
    ```typescript
    class BackupSelectModal extends SuggestModal<BackupInfo> {
      getSuggestions(query: string): BackupInfo[]
      renderSuggestion(backup: BackupInfo, el: HTMLElement): void
      onChooseSuggestion(backup: BackupInfo): void
    }
    ```
  - [ ] 5.2 选择后弹出 `ConfirmModal`：
    - 提示"恢复将覆盖当前数据，是否继续？"
    - 确认 → 执行恢复；取消 → 关闭
  - [ ] 5.3 无可用备份时显示 Notice："没有可用的备份点"

- [ ] **Task 6: 启动后健康检查联动** (AC: #7)
  - [ ] 6.1 创建 `obsidian-canvas-learning/src/services/health-poller.ts`（或追加到 docker-manager.ts）
  - [ ] 6.2 实现 `waitForBackendReady()` 方法：
    - 每 3s 调用 `apiClient.get('/api/v1/system/health')`
    - 返回 200 → 后端就绪，更新 systemState 健康状态
    - 超过 60s 未就绪 → 超时，提示用户检查日志
  - [ ] 6.3 在 `startServices()` 和 `restartServices()` 成功后自动调用 `waitForBackendReady()`
  - [ ] 6.4 健康检查成功后更新 `system-state.svelte.ts` 中的 `backendStatus` 字段

- [ ] **Task 7: system-state Store 扩展** (AC: #7)
  - [ ] 7.1 修改 `obsidian-canvas-learning/src/stores/system-state.svelte.ts`：
    - 追加 `backendRunning: boolean = $state(false)`
    - 追加 `lastBackupTime: Date | null = $state(null)`
    - 追加 `dockerAvailable: boolean = $state(false)`
  - [ ] 7.2 DockerManager 状态变化时同步更新 system-state

- [ ] **Task 8: 集成验证** (AC: #1, #2, #3, #4, #5, #6, #7)
  - [ ] 8.1 端到端验证——服务管理：
    - Ctrl+P → "Canvas: 启动后端" → 确认 Docker 容器启动 → 确认健康检查通过
    - Ctrl+P → "Canvas: 重启后端" → 确认容器重启 → 确认健康检查通过
    - Ctrl+P → "Canvas: 停止后端" → 确认容器停止
  - [ ] 8.2 端到端验证——备份/恢复：
    - 创建备份 → 确认备份目录存在且包含正确数据
    - 修改 Neo4j 数据 → 从备份恢复 → 确认数据回滚到备份时间点
    - 恢复过程中故意制造失败（如断电模拟） → 确认回滚机制生效
  - [ ] 8.3 异常场景验证：
    - Docker Desktop 未运行时执行命令 → 确认友好错误提示
    - 备份目录权限不足时 → 确认错误提示
    - 恢复时选择损坏的备份 → 确认回滚机制

## Dev Notes

### Brownfield 上下文

- **docker-compose.yml** 已存在于项目根目录 `canvas-learning-system/docker-compose.yml`，当前仅包含 Neo4j 服务定义。后续 Story 1.1 将完善 FastAPI + Ollama 服务定义
- **端口映射**：Neo4j HTTP 7476（非默认 7474，避免与其他项目冲突），Bolt 7689（非默认 7687）
- **数据卷**：Neo4j 数据存储在 `docker/neo4j/data`、日志在 `docker/neo4j/logs`
- **Story 1.5 依赖**：已完成后端 KG 同步，`/api/v1/system/health` 端点假设由 Story 1.1 创建
- **Story 1.3 依赖**：HealthPanel 在 Settings Tab 中，本 Story 的健康检查更新将联动 HealthPanel 状态

### Docker Compose 启动顺序

```
Docker Desktop → docker-compose up -d → Neo4j(等待就绪) → Ollama(加载bge-m3) → FastAPI(等待Neo4j+Ollama) → 健康检查通过 → Obsidian Plugin 连接就绪
```

[Source: architecture.md#Technical Constraints & Dependencies]

### 跨平台 docker-compose 命令

- **Docker Desktop v2+**（Windows/macOS/Linux）：`docker compose`（无连字符，CLI 插件模式）
- **旧版 Docker Compose**：`docker-compose`（独立二进制）
- **检测策略**：先尝试 `docker compose version`，成功则用 `docker compose`；否则尝试 `docker-compose version`

### 备份范围

| 组件 | 备份路径 | 说明 |
|------|---------|------|
| Neo4j | `docker/neo4j/data/` | 图数据库文件，需停止服务后复制（热备份可能数据不一致） |
| LanceDB | 待定（Story 2.x 确定具体路径） | 向量索引数据，MVP 阶段可全量重建替代恢复 |
| 插件配置 | Obsidian `data.json` | API Key、模型配置、学科设置等 |

**注意**：Neo4j 的安全备份最佳实践是先停服务再复制数据目录。本 Story 的备份命令在复制 Neo4j 数据前自动执行 `docker-compose stop neo4j`，复制完成后重新启动。

### 备份目录结构

```
canvas-learning-system/
└── backups/
    ├── 2026-03-16T12-00-00/
    │   ├── backup-meta.json       # 备份元数据（时间戳、版本、组件列表）
    │   ├── neo4j-data/            # Neo4j 数据目录完整复制
    │   ├── lancedb-data/          # LanceDB 数据目录完整复制
    │   └── config/
    │       └── data.json          # 插件配置
    └── 2026-03-15T18-30-00/
        └── ...
```

### backup-meta.json 格式

```json
{
  "version": "1.0",
  "timestamp": "2026-03-16T12:00:00Z",
  "components": ["neo4j", "lancedb", "config"],
  "neo4jDataSize": 52428800,
  "pluginVersion": "0.1.0"
}
```

### 命令面板命令 ID 规范

| 命令 ID | 显示名称 | docker-compose 命令 |
|---------|---------|-------------------|
| `canvas-start-backend` | Canvas: 启动后端 | `docker-compose up -d` |
| `canvas-restart-backend` | Canvas: 重启后端 | `docker-compose restart` |
| `canvas-stop-backend` | Canvas: 停止后端 | `docker-compose stop` |
| `canvas-backup-data` | Canvas: 备份数据 | 停 Neo4j → 文件复制 → 重启 |
| `canvas-restore-data` | Canvas: 恢复数据 | 停所有 → 文件恢复 → 重启 |

### Notice 进度提示模式

Obsidian `Notice` API 用于向用户显示临时通知。通过 `new Notice(message, 0)` 创建持久通知（不自动消失），完成后通过 `notice.hide()` 关闭。进度更新通过修改 `notice.noticeEl.textContent` 实现。

```typescript
const notice = new Notice('正在启动后端服务...', 0);
try {
  await dockerManager.startServices();
  notice.setMessage('后端服务已启动');
  setTimeout(() => notice.hide(), 3000);
} catch (e) {
  notice.setMessage(`启动失败: ${e.message}`);
  setTimeout(() => notice.hide(), 5000);
}
```

### 不做的事项（防蔓延 DD-10）

- 不实现 Docker 容器日志查看（用户可通过 `docker-compose logs` 手动查看）
- 不实现自动备份调度（MVP 仅手动备份，自动调度留后续迭代）
- 不实现 SQLite 对话历史备份（Story 3.x 对话系统完成后再扩展备份范围）
- 不实现远程备份/云同步（NFR-SEC-01 所有数据存储本地）
- 不实现 Graphiti/Neo4j 在线热备份（MVP 停服备份足够安全）
- 不实现备份压缩（MVP 直接文件复制，后续可加 tar.gz）
- 不修改 docker-compose.yml 服务定义（由 Story 1.1 负责）

### 共享文件编辑规则

| 文件 | 规则 |
|------|------|
| `main.ts` | 追加 5 个命令注册；保持 Story 1.1/1.4/1.5 的初始化逻辑 |
| `system-state.svelte.ts` | 追加 backendRunning/lastBackupTime/dockerAvailable 字段；保持已有字段 |

### Project Structure Notes

本 Story 新增/修改的文件清单：

```
obsidian-canvas-learning/
├── main.ts                                    # [修改] 追加 5 个命令面板命令注册
├── src/
│   ├── stores/
│   │   └── system-state.svelte.ts             # [修改] 追加 Docker/备份相关状态字段
│   └── services/
│       ├── docker-manager.ts                  # [新建] Docker Compose 命令执行服务
│       ├── backup-manager.ts                  # [新建] 数据备份与恢复服务
│       └── health-poller.ts                   # [新建] 启动后健康检查轮询
```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements Overview] — 能力域12系统配置：命令面板一键启动/重启后端(FR-SYS-05) + 数据备份+一键恢复(FR-SYS-06)
- [Source: _bmad-output/planning-artifacts/architecture.md#Technical Constraints & Dependencies] — Docker依赖启动顺序：Docker Desktop → docker-compose up → Neo4j → Ollama → FastAPI → Plugin → Agent → MCP
- [Source: _bmad-output/planning-artifacts/architecture.md#Infrastructure & Deployment] — Docker Compose 本地部署 + 一键启动脚本 + 8步依赖链 + 5步检测向导
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure] — backend/scripts/backup.sh 后端备份脚本位置
- [Source: _bmad-output/planning-artifacts/architecture.md#Architectural Boundaries] — 系统管理 REST `/api/v1/system/` 健康检查、配置、备份
- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns] — 离线降级4场景（Docker未启→引导面板）
- [Source: _bmad-output/planning-artifacts/architecture.md#NFR] — NFR-REL-04 备份可恢复、NFR-SEC-01 所有数据存储本地
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.8] — AC 和 Story 需求定义
- [Source: docker-compose.yml] — Neo4j 容器配置（端口 7476:7474, 7689:7687，数据卷 docker/neo4j/data）

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
