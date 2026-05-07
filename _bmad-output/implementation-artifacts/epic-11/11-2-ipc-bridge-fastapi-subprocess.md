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

### AC #6: Multi-Vault Picker UX 完整（2026-05-07 5 Agent 调研补全）

> **背景**：原 AC #3 + Task 4 仅设计"首启 modal + Select Folder 按钮"，缺 Recent vaults / 多 vault 切换 / macOS App Sandbox security-scoped bookmarks / 跨平台 dialog 参数差异。Agent 1 审计标记为 🔴 CRITICAL 缺口；Agent 2 实测 Claude Desktop Code Tab 是反例（Issue #36175）；Agent 3 实测 macOS App Store 发布无 bookmarks 会重启失访权。

- **Given** 用户启动 Desktop App，main window ready
- **When** 检查 `app.getPath('userData') + '/vault-registry.json'`
- **Then** 三种情况分别处理：
  - **首启（registry 不存在）**：弹 Vault Picker Modal 三段（Recent 空 / Open Other / Create New）
  - **有 Recent + lastVault 仍存在**：自动 startAccessingSecurityScopedResource(bookmark) → POST `:8011/api/v1/canvas/vault-config` → 直接进主界面
  - **有 Recent 但 lastVault 失效（被删 / bookmark stale）**：弹 Vault Picker Modal，Recent 列表显示 + 标失效项灰色 + 提供 "Open Other"
- **And** Vault Picker Modal 含三段：
  1. **Recent Vaults 列表**（最多 10 个，按 lastOpened 倒序）：每行 `vault_name | path（缩略）| 最后打开时间相对时间`，点击切换
  2. **"Open Other Folder..." 按钮** → 调 `dialog.showOpenDialog({ properties: ['openDirectory', 'noResolveAliases'], securityScopedBookmarks: true })`
  3. **"Create New Vault..." 按钮** → 二级 picker 选父目录 + input 输入 vault 名 → 创建空目录 + 写空 `.canvas-config.yaml`
- **And** vault-registry.json schema：
  ```json
  { "vaults": [{ "path": "...", "bookmark": "base64...|null", "lastOpened": 1234567890, "platform": "darwin" }], "currentIndex": 0, "maxRecent": 10 }
  ```
- **And** macOS：`result.bookmarks[0]` 持久化；启动时调 `app.startAccessingSecurityScopedResource(bookmark)` 恢复访问权；app `before-quit` 时 stopAccessing；切换 vault 时旧 vault stop + 新 vault start
- **And** 主窗口顶栏显示 Vault Switcher：`[Current: {vault_name} ▼]` 点击展开 Recent dropdown，可不弹 Modal 直接切换（hot swap，复用 Story 1.8 VaultSwitchCoordinator）
- **And** File menu 增加 "Open Recent ▶" 二级菜单 + "Open Other Vault... ⌘O" + "Clear Menu"
- **And** 路径有效性校验（Electron main 进程层）：
  - 必须是目录（非文件）
  - 必须可读 + 可写
  - 必须含至少 1 个 .md 文件 OR 含 `.obsidian/` 子目录 OR 用户在 Modal 选 "Create New" 路径
  - 失败 → toast "No markdown files found" + 留在 Picker
- **And** 跨平台 dialog 行为差异处理：
  - **macOS**：`createDirectory: true`（dialog 内可建文件夹）+ `noResolveAliases: true`（防 symlink 逃逸）+ `securityScopedBookmarks: true`
  - **Windows**：`properties: ['openDirectory']`（IFileDialog 自动 native folder picker）
  - **Linux**：`properties: ['openDirectory']`（GtkFileChooserNative，Wayland/X11 兼容）

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

- [ ] Task 4: Multi-Vault Picker UX（AC #6 落地，2026-05-07 拆分为 4a-4e 5 子任务）

  - [ ] **Task 4a: 首启 Vault Picker Modal + dialog.showOpenDialog**
    - [ ] 4a.1: 创建 React 组件 `VaultPickerModal.tsx`（Obsidian 风格三段布局：Recent / Open Other / Create New）
    - [ ] 4a.2: main 进程 `ipcMain.handle('vault:show-picker', ...)` → 触发 modal 显示
    - [ ] 4a.3: "Open Other Folder..." 按钮 → `window.api.selectVaultFolder()` → main 进程调 `dialog.showOpenDialog({ properties: ['openDirectory', 'noResolveAliases'], securityScopedBookmarks: process.platform === 'darwin', createDirectory: true, title: 'Select Vault Folder' })`
    - [ ] 4a.4: 路径有效性校验（fs.statSync + glob `*.md` + 检测 `.obsidian/`）→ 失败 toast "No markdown files found" + 留在 Picker
    - [ ] 4a.5: "Create New Vault..." 按钮 → 二级 picker 选父目录 + input vault 名 → fs.mkdirSync + 写空 `.canvas-config.yaml`

  - [ ] **Task 4b: Vault Switcher（主窗口顶栏 dropdown）**
    - [ ] 4b.1: 创建 React 组件 `VaultSwitcher.tsx`（顶栏组件，显示 `[Current: {vault_name} ▼]`）
    - [ ] 4b.2: 点击展开 Recent dropdown（Cursor 风格 + 不弹 Modal 直接切换）
    - [ ] 4b.3: 切换时调 `window.api.switchVault(path)` → main 进程：
      - macOS: 旧 vault `stopAccessingSecurityScopedResource()` + 新 vault `startAccessingSecurityScopedResource()`
      - 共用：`POST :8011/api/v1/canvas/vault-config { path }` 通知 Canvas backend（hot swap，复用 Story 1.8 VaultSwitchCoordinator）
    - [ ] 4b.4: File menu 增加 "Open Recent ▶" 二级菜单 + "Open Other Vault... ⌘O" + "Clear Menu" + "Switch Vault... ⇧⌘O"

  - [ ] **Task 4c: Recent Vaults 持久化（vault-registry.json）**
    - [ ] 4c.1: 引入 `electron-store@^8.x` 依赖
    - [ ] 4c.2: 定义 schema：`{ vaults: [{ path, bookmark?, lastOpened, platform }], currentIndex, maxRecent: 10 }`
    - [ ] 4c.3: 编写 `loadVaultRegistry()` / `saveVault(path, bookmark?)` / `removeVault(index)` / `getRecentVaults()` helpers
    - [ ] 4c.4: 切换 vault 时 push 新 vault 到 vaults 数组顶部，保留前 10 个；currentIndex = 0
    - [ ] 4c.5: 启动时检查 lastVault 是否仍存在 → 失效项标灰色但保留在 Recent 列表（用户可手动删）

  - [ ] **Task 4d: macOS App Sandbox + security-scoped bookmarks**
    - [ ] 4d.1: dialog.showOpenDialog 启用 `securityScopedBookmarks: true`（仅 darwin）
    - [ ] 4d.2: result.bookmarks[0]（base64 string）保存到 vault-registry.json 对应 vault 的 bookmark 字段
    - [ ] 4d.3: app `ready` 事件：读 lastVault.bookmark → `app.startAccessingSecurityScopedResource(bookmark)` → 保存返回的 stopAccessing 函数
    - [ ] 4d.4: app `before-quit` 事件 + 切换 vault 时：调 stopAccessing()
    - [ ] 4d.5: 失败处理：bookmark stale → 提示用户重新选择 + 标记 vault-registry 该项 invalid
    - [ ] 4d.6: 注：仅在 macOS App Store 发布时严格需要（沙箱 mode），独立签名 DMG 可降级（直接路径访问）但仍建议启用以保前向兼容（Story 11.4 entitlements 章节关联）

  - [ ] **Task 4e: 跨平台 dialog 参数差异处理**
    - [ ] 4e.1: 抽取平台判断 helper：`getDialogOptions(platform)` 返回不同 properties 数组
    - [ ] 4e.2: macOS：`['openDirectory', 'noResolveAliases', 'createDirectory']` + `securityScopedBookmarks: true` + `message: 'Choose a folder for your vault'`（macOS-only message field）
    - [ ] 4e.3: Windows：`['openDirectory']`（IFileDialog 自动支持，不需 createDirectory）
    - [ ] 4e.4: Linux：`['openDirectory']`（GtkFileChooserNative，注意 Wayland/X11 default path 行为差异）
    - [ ] 4e.5: 跨平台测试矩阵（macOS arm64 / macOS x64 / Windows 11 / Ubuntu 22）— Story 11.4 CI/CD 验收

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

### D19 决策锁定（2026-05-07 ChatGPT DR 升级后）

ChatGPT Deep Research (effort=max, GitHub connector only) 实读本仓库 Tier 1-5 文件 + 官方文档（Graphiti / Neo4j / Kuzu / Memgraph / Electron / Apple）后**独立得出与本 spec 一致的结论**：保留 C+ Docker Compose Supervisor 是 5-10 人日预算下的最优路径。

- **不需修订 AC / Task**：AC #1 + Task 1 的 Docker Compose Supervisor 设计 = DR 主决策
- **关键修正记录**：`wikilink_graph_service.py` 完全不依赖 Neo4j（obsidiantools + NetworkX 内存图），不是 Neo4j 锁定证据文件。未来 no-Docker spike 应**优先迁出 Memory / Graphiti / Exam 链**，而不是 wikilink
- **未发现 APOC.* 运行期调用**：APOC 仅容器层启用（`NEO4J_PLUGINS=["apoc"]`），目标文件中无显式 `CALL apoc.*`。这降低了未来 Kuzu 迁移的语义复杂度
- **后续 spike**：图访问抽象层（4-6 人日）+ Kuzu spike（5-8 人日）单独立项，**不进 Epic-11**。详见 `_bmad-output/research/spike-graph-store-abstraction-roadmap-2026-05-07.md`
- **关联文档**：
  - `决策批注/D19-desktop-db-stack-2026-05-07.md`（主决策 + 次决策锁定）
  - `research/round-22-desktop-db-decision-deep-research-2026-05-07.md`（DR 报告原文）
  - `research/round-22-chatgpt-dr-prompt-desktop-db-decision-2026-05-07.md`（DR 提示词）

### 关键决策（S1 C+ 修订后）
- **Docker supervisor 模式**：Electron 不嵌入 Python / Neo4j / LanceDB / bge-m3，复用 Epic-10 docker-compose.yml + docker-compose.canvas.yml 编排（用户机器需装 Docker Desktop 一次性 600MB）
- **不嵌入 Neo4j 的理由**：Neo4j 是 Java 应用（嵌入需 JRE +200MB），sqlite 替代会推翻 Story 10.2 已实施的 wikilink_proxy 架构 + 重写所有 Cypher 查询
- **vault 单一真相源在 Canvas backend**：Electron main 进程不存 vault active 路径状态（仅存 Recent vaults registry 用于 UX），每次切 vault 通过 HTTP `POST :8011/api/v1/canvas/vault-config` 通知 Canvas backend，避免 main / backend 状态漂移
- **vault watch 单 owner**：Canvas backend Python watchdog 是唯一 watcher（Story 10.3 Phase B 已实现），Electron main 不用 chokidar / fs.watch（避免双 watcher race + 双 wikilink_graph rebuild）
- **Vault Picker UX 边界划分（AC #6 拆分边界）**：
  - **Electron 持久化**：vault-registry.json（Recent 列表 + bookmarks），跨 session 保留
  - **Canvas backend 持久化**：active vault 路径（reload_settings + LanceDB index + Graphiti group_id）
  - **不重叠**：Recent 列表纯 UX 层（Electron），active vault 状态纯数据层（backend）
- **不抄 AnythingLLM 的根本理由（D18 澄清）**：Agent 4 实测 AnythingLLM 是 HTTP upload-and-embed（用户 upload 文件被 copy 到 app 内部 `/storage/documents/`），与 NEG-2"不上传文件，直接访问指定文件夹"完全冲突。本 Story 数据流：`IPC vault:read/write → main 进程 axios → Canvas backend :8011/api/v1/vault/* → 直接 fs 操作`

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
