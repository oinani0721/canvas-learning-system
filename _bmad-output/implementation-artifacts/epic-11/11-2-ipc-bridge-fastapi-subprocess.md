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

# Story 11.2: IPC Bridge + FastAPI subprocess

**Status**: backlog（target Day 13-14, 2026-05-19 ~ 2026-05-20）

## Story（用户故事）

As a 学习者, I want Desktop App to automatically spawn a local FastAPI server process and communicate with it via IPC (inter-process communication) so that I can read/write vault files and trigger AI features without network calls — giving me true offline operation.

> **映射对**: M11（vault 不上传文件，知识库直接访问）+ NEG-2（用户主权 vault 所有权）

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

### AC #1: FastAPI subprocess 生命周期管理

- **Given** Electron app 启动
- **When** main 进程初始化
- **Then** main 进程调用 `spawn('python', ['-m', 'uvicorn', 'deeptutor.api.main:app', '--port', '0'])`
- **And** 检测 stdout 中的 "Uvicorn running on http://127.0.0.1:XXXX" 消息
- **And** 自动解析 port 号，存储在 main process 内存（不写配置文件）

### AC #2: Health check heartbeat

- **Given** FastAPI subprocess 运行
- **When** 每 5 秒执行一次 `GET /api/v1/health`
- **Then** 响应 HTTP 200 + `{"status": "healthy"}`
- **And** 如果连续 3 次失败，自动重启 subprocess
- **And** UI toast 通知用户 "Backend recovering..." → "Backend online"

### AC #3: Vault 目录首选授权 UI

- **Given** 用户首次启动 Desktop App，vault 目录未设置
- **When** main window 加载完毕
- **Then** modal dialog 弹出：标题 "Select Your Notebook Location" + 说明文本 + "Select Folder" 按钮 + "Cancel" 按钮
- **And** 用户点击 "Select Folder" → 打开系统文件选择对话框
- **And** 选定后，app 将路径保存至 `~/.deeptutor-app/vault-path.json`
- **And** 关闭对话框，main 进程通知 FastAPI subprocess 该 vault 路径

### AC #4: IPC 命令管道（5 个基础命令）

- **Given** renderer process 需要读/写文件或 watch 文件变化
- **When** renderer 调用 `window.api.vaultRead(filename)` / `vault_write` / `vault_list` / `vault_watch` / `vault_unwatch`
- **Then** main 进程代理请求至 FastAPI：`POST /api/v1/vault/{command}`
- **And** renderer 接收 response JSON（含 data / error 字段）
- **And** 5 个命令全部支持 error 回调（如 permission denied）

### AC #5: 无网络依赖验证

- **Given** 用户网络离线（disable WiFi / 断网线）
- **When** Desktop App 运行 vault_read / AI 特性
- **Then** 本地 subprocess 仍可交互（FastAPI 127.0.0.1:port）
- **And** 无外网请求（tcpdump / network monitor 验证）
- **And** 仅 Claude API 调用时才需网络（提示用户）

## Tasks / Subtasks

### Electron main 进程扩展

- [ ] Task 1: FastAPI subprocess spawner
  - [ ] 1.1: 导入 `child_process.spawn` + `os` + `path`
  - [ ] 1.2: 编写 `spawnFastAPIServer()` 函数：
    - [ ] 1.2.1: 确定 Python 可执行路径（`python3` 或 `python`）
    - [ ] 1.2.2: 检查 `deeptutor` 包是否已安装（fallback 路径）
    - [ ] 1.2.3: spawn 进程，监听 stdout，正则匹配 `http://127.0.0.1:(\d+)`
    - [ ] 1.2.4: 提取 port，返回给 IPC handler
  - [ ] 1.3: 编写 `killFastAPIServer()` 函数（app 关闭时）

- [ ] Task 2: Health check heartbeat
  - [ ] 2.1: 导入 `axios` 或 `fetch`
  - [ ] 2.2: 编写 `startHealthCheck()` 函数（5s interval）
  - [ ] 2.3: 失败计数器 + 3 次失败自动重启
  - [ ] 2.4: 编写 `notifyRenderer()` 通知 UI（via IPC）

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

- [ ] Task 8: FastAPI backend 路由
  - [ ] 8.1: 创建 `deeptutor/api/routers/vault_ops.py`
  - [ ] 8.2: 4 个 endpoint：
    - [ ] 8.2.1: `POST /api/v1/vault/read` → 读本地文件返回 content
    - [ ] 8.2.2: `POST /api/v1/vault/write` → 写入本地文件
    - [ ] 8.2.3: `POST /api/v1/vault/list` → 列出 .md 文件
    - [ ] 8.2.4: `GET /api/v1/vault/config` → 返回 vault 路径
  - [ ] 8.3: 权限检查（路径必须在授权 vault 目录内，防路径穿越）

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

### 关键决策
- **Port 0 自动检测** vs 固定端口：port 0 让 OS 分配空闲端口，避免冲突，但需 regex 解析 stdout
- **IPC vs HTTP**: IPC 更安全（本地进程）且快（共享内存），HTTP 则需监听 localhost
- **FastAPI subprocess 定位**：不是"后台服务"，而是 "AI 引擎 sidecar"，仅在 Desktop App 运行时存在

### 已知陷阱
1. **Python 可执行路径**：不同 OS + venv 状态下 `python3` 可能不存在。解决：try `python3` → fallback `python` → `which`
2. **FastAPI 模块导入失败**：deeptutor 包未安装时需 sys.path 注入。解决：`PYTHONPATH=<fork-root> python ...`
3. **Vault 路径权限**：`vaultWrite()` 时需验证路径在授权范围内。解决：每次 write 前 `os.path.normpath()` 检查

### 风险
- **R4 subprocess 崩溃**: health check + 3 次失败自动重启（已落到 AC #2）

## UAT 验收

详见 `_bmad-output/验收单/Story-11.2-ipc-bridge-fastapi-subprocess.md`

## References

- Epic-11 _README §"Goals" Goal 2
- Round-22 Day 2 vault 报告 §四（VaultMonitor 设计 + file lock）
- Story 10.3 Round-22 修订段（Phase B vault 直读升级）

## 下一步

→ Story 11.3 Day 15-18 Vault 深度集成 + 渲染验证（Math Animator + Visualize 内嵌）
