---
story_id: "11.2"
epic_id: "11"
prd_id: "canvas-learning-system"
status: "backlog"
priority: "P1"
estimate_hours: 16
depends_on: ["11.1"]
blocks: ["11.3"]
trace: ["FR-DEEP-04", "M11"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
day: "Day 13-14"
target_date: "2026-05-19 ~ 2026-05-20"
uat_sheet: "_bmad-output/验收单/Story-11.2-ipc-bridge-fastapi-subprocess.md"
---

# Story 11.2: IPC Bridge + Docker Compose Supervisor

**Status**: backlog（target Day 13-14, 2026-05-19 ~ 2026-05-20）

> **2026-05-07 对抗性审查 S1 修订（C+ 方案锁定）**：原 spec 设计"Electron spawn 单个 FastAPI subprocess"，但 Epic-10 5 大核心 100% 依赖 Canvas backend (:8011) + Neo4j (:7691)，单 subprocess 无法承接（且 Neo4j 嵌入需 JRE 200MB / sqlite 重写所有 Cypher 推翻 Story 10.2）。修订为：**Electron 当 Docker compose supervisor**，复用 Epic-10 完整 docker-compose 编排（Canvas + DeepTutor + Neo4j），IPC 5 个 vault 命令路由到 Canvas backend HTTP。

## Story（用户故事）

As a 学习者, I want Desktop App to automatically start the Docker compose stack（Canvas + DeepTutor + Neo4j）on launch and provide IPC commands for local file operations, so that I can read/write vault files and trigger AI features through the same backend stack used during MVP — keeping the Day 0-10 verified architecture intact.

> **映射对**: M11（vault 不上传文件，知识库直接访问）+ NEG-2（用户主权 vault 所有权）+ S1 C+（Docker supervisor 不嵌入 Neo4j）

## 通俗化解释（给学习者）

> **一句话说**: Desktop App 启动时，会自动在后台启动一个 DeepTutor AI 引擎。然后 App 和引擎通过"内部通信管道"交换数据。你编辑笔记时，App 自动同步到本地文件，AI 引擎也能访问你的笔记。

**你会遇到的场景**:
- 首次打开 Desktop App，弹出"选择笔记本位置"对话框
- 点击"选择文件夹"，选中你电脑里的笔记目录
- App 记住这个位置
- 之后每次你编辑笔记，都是直接改本地文件（不上传云端）
- 如果你调用"AI 讲解"功能，AI 引擎直接读你本地的笔记，快速响应

**这个功能帮你**:
- 笔记完全在你电脑上（privacy-first）
- AI 处理速度快（本地 subprocess，无网络延迟）
- 可离线工作（除了第一次需要下载 AI 模型）

**用个比喻**: 🚇 就像家里的水管——App 和 AI 引擎在同一栋房子里，水（数据）通过内部水管直接流通，不需要走外面的供水管网（不需要网络）。

## Acceptance Criteria

### AC #1: Docker compose 编排生命周期管理（S1 C+ 修订）

- **Given** Electron app 启动 + 用户已装 Docker Desktop
- **When** main 进程初始化
- **Then** main 进程检测 Docker 运行状态（`docker info` 退出码 0）→ 若未运行，UI dialog 提示用户启动 Docker Desktop
- **And** main 进程调用 `spawn('docker', ['compose', '-f', 'docker-compose.yml', '-f', 'docker-compose.canvas.yml', 'up', '-d'])`（cwd = fork 仓库路径，env 含 `CANVAS_WORKTREE_PATH=<user_vault_path>`）
- **And** 等待 Canvas (:8011) + DeepTutor (:8001) + Neo4j (:7691) 全部 healthy（轮询 health endpoint，超时 60s）
- **And** 服务端口写入 main process 内存 + 通过 IPC 暴露给 renderer（`window.api.getServicePorts()`）

### AC #2: Health check heartbeat + Docker service 恢复

- **Given** Docker compose 已启动
- **When** 每 5 秒执行一次 `GET http://127.0.0.1:8011/api/v1/health` + `GET http://127.0.0.1:8001/api/v1/health`
- **Then** 响应 HTTP 200 + `{"status": "healthy"}`
- **And** 如果连续 3 次失败，自动 `docker compose restart <service>` 单服务重启（不整体重启）
- **And** UI toast 通知用户 "Canvas backend recovering..." / "DeepTutor recovering..." → "Backend online"

### AC #3: Vault 目录首选授权 UI + Canvas backend 同步切 vault（S1 C+ 修订）

- **Given** 用户首次启动 Desktop App，vault 目录未设置
- **When** main window 加载完毕
- **Then** modal dialog 弹出：标题 "Select Your Notebook Location" + 说明文本 + "Select Folder" 按钮 + "Cancel" 按钮
- **And** 用户点击 "Select Folder" → 打开系统文件选择对话框
- **And** 选定后，app 将路径保存至 `~/.deeptutor-app/vault-path.json`
- **And** main 进程通过 HTTP `POST :8011/api/v1/canvas/vault-config { path: <user_path> }` 通知 **Canvas backend** reload + reindex（vault 路径单一真相源在 Canvas backend，不在 main 进程内存）
- **And** Canvas backend 触发 `wikilink_graph_service.build_graph(vault_path)` + LanceDB reindex + Graphiti episodic watcher 重启动
- **And** 切换 vault 时同样通过此 API 通知（运行时可变 vault 支持）

### AC #4: IPC 命令管道（5 个基础命令路由到 Canvas backend，S1 C+ 修订）

- **Given** renderer process 需要读/写文件或 watch 文件变化
- **When** renderer 调用 `window.api.vaultRead(filename)` / `vaultWrite` / `vaultList` / `vaultWatch` / `vaultUnwatch`
- **Then** main 进程代理请求至 **Canvas backend**：`POST http://127.0.0.1:8011/api/v1/vault/{command}`（不是 DeepTutor :8001，也不是新 spawn 的 subprocess）
- **And** renderer 接收 response JSON（含 data / error 字段）
- **And** 5 个命令全部支持 error 回调（如 permission denied）
- **And** vault watch 由 **Canvas backend Python watchdog 单一负责**（不在 main 进程用 chokidar，避免 Story 10.3 Phase B Python watcher 与 Electron Node watcher 双 watcher race condition）

### AC #5: 无外网依赖验证（C+ 方案 localhost-only）

- **Given** 用户网络离线（disable WiFi / 断网线）
- **When** Desktop App 运行 vault_read / AI 特性
- **Then** 所有调用走 Docker compose 内 localhost（`127.0.0.1:8011` / `127.0.0.1:8001` / `127.0.0.1:3782` / `bolt://127.0.0.1:7691`）
- **And** 无外网请求（tcpdump / network monitor 验证）
- **And DocumentAdder vault_mode=True 强制启用**：Story 10.3 Phase B 已实现的 vault_mode 在 Epic-11 同样生效，**禁止上传 vault 文件到 DeepTutor 内部 KB**（NEG-2 落地，不只是"无外网请求"）
- **And** 仅 Claude API 调用时才需网络（提示用户）

## Tasks / Subtasks

### Electron main 进程扩展（S1 C+ 修订 — Docker supervisor）

- [ ] Task 1: Docker compose supervisor
  - [ ] 1.1: 导入 `child_process.spawn / exec` + `os` + `path`
  - [ ] 1.2: 编写 `checkDockerRunning()` 函数：
    - [ ] 1.2.1: `exec('docker info')` 退出码 0 = Docker 运行中
    - [ ] 1.2.2: 失败 → UI dialog "Please start Docker Desktop" + "Quit" 按钮
  - [ ] 1.3: 编写 `startDockerCompose(canvasPath, vaultPath)` 函数：
    - [ ] 1.3.1: cwd = fork 仓库路径
    - [ ] 1.3.2: env = `{ CANVAS_WORKTREE_PATH: vaultPath, ...process.env }`
    - [ ] 1.3.3: `spawn('docker', ['compose', '-f', 'docker-compose.yml', '-f', 'docker-compose.canvas.yml', 'up', '-d'], { cwd, env })`
    - [ ] 1.3.4: 监听 stderr 收集启动错误
  - [ ] 1.4: 编写 `waitForServicesHealthy()` 函数（轮询 60s 超时）：
    - [ ] 1.4.1: poll `http://127.0.0.1:8011/api/v1/health` + `http://127.0.0.1:8001/api/v1/health` 每 2s
    - [ ] 1.4.2: 全部 200 OK → resolve；超时 → reject + UI 错误提示
  - [ ] 1.5: 编写 `stopDockerCompose()` 函数（app 关闭时）：
    - [ ] 1.5.1: `spawn('docker', ['compose', 'down'])`（保留数据卷，不删 vault md / Neo4j data）
    - [ ] 1.5.2: 等待退出 → `app.quit()`

- [ ] Task 2: Health check heartbeat + 单服务恢复
  - [ ] 2.1: 导入 `axios` 或 `fetch`
  - [ ] 2.2: 编写 `startHealthCheck()` 函数（5s interval，并行 ping Canvas + DeepTutor）
  - [ ] 2.3: 失败计数器 + 3 次失败 → `docker compose restart <service>`（仅重启失败的服务，不整体重启）
  - [ ] 2.4: 编写 `notifyRenderer()` 通知 UI（via IPC，区分 Canvas / DeepTutor 哪个 recovering）

- [ ] Task 3: Vault 路径配置存储
  - [ ] 3.1: 导入 `fs.promises` + `electron.app.getPath('userData')`
  - [ ] 3.2: 编写 `loadVaultPath()` 函数（读 `~/.deeptutor-app/vault-path.json`）
  - [ ] 3.3: 编写 `saveVaultPath(path)` 函数（写同一文件）
  - [ ] 3.4: app 启动时检查，缺失则触发 modal（Task 4）

### Electron renderer + UI

- [ ] Task 4: Vault 选择 modal 组件
  - [ ] 4.1: 创建 React 组件 `VaultSelectorModal.tsx`
  - [ ] 4.2: 按钮 "Select Folder" → 调用 `window.api.selectVaultFolder()`
  - [ ] 4.3: IPC handler 返回用户选择的路径
  - [ ] 4.4: 验证路径有效（contains *.md files）→ 保存 → 通知 FastAPI

- [ ] Task 5: IPC bridge (renderer side)
  - [ ] 5.1: 创建 `src/renderer/ipc-client.ts` 模块
  - [ ] 5.2: 导出 5 个函数：
    - [ ] 5.2.1: `vaultRead(filename: string): Promise<string>`
    - [ ] 5.2.2: `vaultWrite(filename: string, content: string): Promise<void>`
    - [ ] 5.2.3: `vaultList(): Promise<string[]>`
    - [ ] 5.2.4: `vaultWatch(filename: string, callback): void`
    - [ ] 5.2.5: `vaultUnwatch(filename: string): void`
  - [ ] 5.3: 所有函数返回 Promise，error 时 reject + console.error + toast UI

### Electron main IPC handlers

- [ ] Task 6: preload 脚本扩展（contextBridge）
  - [ ] 6.1: 在 `src/main/preload.ts` 增加 5 个 IPC 命令暴露
  - [ ] 6.2: 示例：`contextBridge.exposeInMainWorld('api', { vaultRead: (fname) => ipcRenderer.invoke('vault:read', fname) })`
  - [ ] 6.3: 所有命令前缀 `vault:` 保持一致

- [ ] Task 7: main 进程 IPC event handlers
  - [ ] 7.1: 在 main.ts 注册 5 个 `ipcMain.handle('vault:read', ...)` handler
  - [ ] 7.2: 每个 handler 调用相应 FastAPI endpoint（via axios POST）
  - [ ] 7.3: 异常捕获 → 返回 `{ error: "..." }`

- [ ] Task 8: Canvas backend vault router（S1 C+ 修订 — 路由到 Canvas backend，不是 DeepTutor）
  - [ ] 8.1: 创建 `backend/app/api/v1/endpoints/vault_ops.py`（**Canvas backend，不是 DeepTutor**）
  - [ ] 8.2: 5 个 endpoint：
    - [ ] 8.2.1: `POST /api/v1/vault/read { filename }` → 读本地文件返回 content
    - [ ] 8.2.2: `POST /api/v1/vault/write { filename, content }` → 写入本地文件 + 触发 wikilink_graph 增量重建
    - [ ] 8.2.3: `POST /api/v1/vault/list` → 列出 .md 文件
    - [ ] 8.2.4: `GET /api/v1/vault/config` → 返回当前 vault 路径
    - [ ] 8.2.5: `POST /api/v1/canvas/vault-config { path }` → 切 vault（reload + reindex + 重启 watcher）
  - [ ] 8.3: 权限检查（路径必须在授权 vault 目录内，防路径穿越）
  - [ ] 8.4: vault watch 复用 Canvas backend Story 10.3 Phase B 已实现的 Python watchdog daemon（不重新实现）

### Integration + Testing

- [ ] Task 9: 集成测试
  - [ ] 9.1: 启动 Desktop App
  - [ ] 9.2: 验证 FastAPI subprocess 启动成功（日志中看到 port）
  - [ ] 9.3: 选择 vault 文件夹
  - [ ] 9.4: 创建测试文件 `test.md`，写内容
  - [ ] 9.5: 从 renderer 调用 `vaultRead('test.md')`，验证读取内容正确
  - [ ] 9.6: 修改内容，调用 `vaultWrite()`，验证本地文件更新

- [ ] Task 10: 网络隔离测试
  - [ ] 10.1: 断网（disable WiFi）
  - [ ] 10.2: vault_read / vault_write 仍可用
  - [ ] 10.3: 用 network monitor 验证无外网请求

## Dev Notes

### 关键决策（S1 C+ 修订后）
- **Docker supervisor 模式**：Electron 不嵌入 Python / Neo4j / LanceDB / bge-m3，复用 Epic-10 docker-compose.yml + docker-compose.canvas.yml 编排（用户机器需装 Docker Desktop 一次性 600MB）
- **不嵌入 Neo4j 的理由**：Neo4j 是 Java 应用（嵌入需 JRE +200MB），sqlite 替代会推翻 Story 10.2 已实施的 wikilink_proxy 架构 + 重写所有 Cypher 查询
- **vault 单一真相源在 Canvas backend**：Electron main 进程不存 vault 路径状态，每次切 vault 通过 HTTP `POST :8011/api/v1/canvas/vault-config` 通知 Canvas backend，避免 main / backend 状态漂移
- **vault watch 单 owner**：Canvas backend Python watchdog 是唯一 watcher（Story 10.3 Phase B 已实现），Electron main 不用 chokidar / fs.watch（避免双 watcher race + 双 wikilink_graph rebuild）

### 已知陷阱（C+ 方案）
1. **Docker Desktop 未启动**：用户首次开机后第一次开 DeepTutor 可能 Docker 还没起，需 UI dialog 引导
2. **端口冲突**：用户机器可能已占 :8011 / :8001 / :7691（其他项目），需 health check 失败时给具体提示（`lsof -i :8011`）
3. **首次 docker pull 慢**：首次启动需 pull Canvas + DeepTutor + Neo4j 镜像（~2GB），需 UI 进度提示
4. **Vault 路径权限**：`vault:write` 时需验证路径在授权范围内（Canvas backend 已实现，Electron main 不重复检查）
5. **DocumentAdder vault_mode 强制**：Story 10.3 Phase B 已加 vault_mode 参数，Epic-11 必须确保所有 KB 上传调用都传 `vault_mode=True`（否则违反 NEG-2）

### 风险（修订后）
- **R4 → R4'**: Docker compose 服务崩溃 → health check 5s heartbeat + 单服务自动重启（已落到 AC #2）
- **R7（新）**: 用户未装 Docker Desktop → Day 11 启动前用户必须确认（已落到 _README §"用户端必备"）

## UAT 验收

详见 `_bmad-output/验收单/Story-11.2-ipc-bridge-fastapi-subprocess.md`

## References

- Epic-11 _README §"Goals" Goal 2
- Round-22 Day 2 vault 报告 §四（VaultMonitor 设计 + file lock）
- Story 10.3 Round-22 修订段（Phase B vault 直读升级）

## 下一步

→ Story 11.3 Day 15-18 Vault 深度集成 + 渲染验证（Math Animator + Visualize 内嵌）
