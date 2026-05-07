---
story_id: "11.1"
epic_id: "11"
prd_id: "canvas-learning-system"
status: "backlog"
priority: "P1"
estimate_hours: 12
depends_on: ["epic-10"]
blocks: ["11.2"]
trace: ["FR-DEEP-03"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
day: "Day 11-12"
target_date: "2026-05-17 ~ 2026-05-18"
uat_sheet: "_bmad-output/验收单/Story-11.1-electron-framework-web-bundling.md"
---

# Story 11.1: Electron 框架 + Web 包装

**Status**: backlog（target Day 11-12, 2026-05-17 ~ 2026-05-18，触发条件：Epic-10 Day 10 UAT 全 PASS + Path A 选定）

## Story（用户故事）

As a 学习者, I want to double-click a Desktop App icon and see DeepTutor Web UI launch in a standalone window, so that I can use DeepTutor without opening a browser tab — giving me a native application feel.

> **映射对**: M4（Whiteboard 讲题视觉化）+ NEG-3（Web 双轨并存）

## 通俗化解释（给学习者）

> **一句话说**: 在你的电脑桌面或应用菜单里，有个 DeepTutor 图标。点击它，DeepTutor 会自动打开成一个独立的应用窗口，就像你用的 VS Code 或 Slack 一样。

**你会遇到的场景**:
- 安装 DeepTutor Desktop App
- 在 macOS 应用库、Windows 开始菜单、或 Linux 应用菜单找到 DeepTutor 图标
- 双击或点击启动
- 等待 2-3 秒，看到一个大窗口打开，里面是熟悉的 DeepTutor 界面

**这个功能帮你**:
- 不用记 localhost:3782 这个奇怪的地址
- 感觉是"真正的应用"，不是在浏览器里跑的网页
- 可以用快捷键、窗口管理、通知等 native 特性

**用个比喻**: 🖥️ 就像 VS Code 是桌面 App 不是网页—— DeepTutor 也变成桌面 App。

## Acceptance Criteria

### AC #1: Electron main 进程生命周期完整

- **Given** Windows BrowserWindow 创建代码运行
- **When** 应用启动
- **Then** main 进程成功初始化、preload 脚本注入、contextBridge 暴露 IPC API
- **And** DevTools (Cmd+Option+I) 可打开（仅 dev mode）
- **And** 应用关闭时主进程正确 cleanup（无僵尸进程）

### AC #2: Next.js standalone SSR 集成（S2 修订 — 不走 file:// SSG）

> **2026-05-07 对抗性审查 S2 修订**：DeepTutor `web/next.config.js` 实际配置 `output: "standalone"`（SSR），`web/package.json` 仅 `next build` / `next start`，无 `next export`。原 spec "file:// + out/ 目录" 是 SSG 模式，与 D18 选 Electron 的根本理由（保 Next.js SSR + API routes）对立，且 next.config.js 不能同时配 `export` + `standalone`。修订为 standalone server 模式。

- **Given** DeepTutor fork Next.js 应用已构建为 standalone（`npm run build` 产出 `.next/standalone/server.js`）
- **When** Electron app 启动
- **Then** main 进程 spawn `node .next/standalone/server.js`，监听 stdout 提取 `Local: http://localhost:<port>` 中的端口（Next 默认 3000，可通过 `PORT=0` 让 OS 分配）
- **And** BrowserWindow 加载 `http://127.0.0.1:<dynamic_frontend_port>`（**不是** `file://...`）
- **And** Next standalone server 完整支持 SSR + API routes（保留 DeepTutor 全部功能）
- **And** 首屏显示 < 5 秒（包含 Node server 启动 + Docker compose health check 等候）

### AC #3: 窗口管理 + UI 完整性

- **Given** BrowserWindow 打开后
- **When** 用户看到界面
- **Then** 窗口尺寸合理（1200x800 或全屏）
- **And** 所有 CSS 资源加载正常（布局、颜色、字体 OK）
- **And** 首屏导航栏可点击（Co-Writer / Books 等按钮可见可交互）
- **And** 无控制台报错（`console.error` 为空）

### AC #4: 代码签名预埋（macOS）

- **Given** electron-builder 配置在 `electron-builder.yml`
- **When** build 流程执行
- **Then** 代码签名密钥从 GitHub Secrets 注入（`CSC_LINK` + `CSC_KEY_PASSWORD`）
- **And** .app 束成功生成（Mach-O 可执行文件）
- **And** `codesign -v dist/DeepTutor.app` 校验通过

## Tasks / Subtasks

### Frontend (Next.js Standalone SSR — S2 修订)

- [ ] Task 1: 验证 Next.js standalone build 产物
  - [ ] 1.1: `cd ~/Desktop/canvas/deeptutor-fork/web && npm run build`
  - [ ] 1.2: 验证 `.next/standalone/server.js` 存在 + `.next/static/` 存在（**不再要求 out/ 目录，next.config.js 不可同时配 export 和 standalone**）
  - [ ] 1.3: 验证 `node .next/standalone/server.js` 可启动 + curl `http://localhost:3000/` 返回 200 + 首屏 HTML 含 DeepTutor 标识

### Electron Setup

- [ ] Task 2: electron-react-boilerplate 初始化
  - [ ] 2.1: Fork `electron-react-boilerplate` 到 `~/Desktop/canvas/deeptutor-fork/desktop/`
  - [ ] 2.2: 删除示例代码（不需要 React demo）
  - [ ] 2.3: 保留 electron + webpack 基础设施

- [ ] Task 3: main.ts 进程编写
  - [ ] 3.1: 导入 `electron` + `child_process.spawn` + `path` + `isDev`
  - [ ] 3.2: 编写 `spawnNextServer()` 函数（S2 修订）：
    - [ ] 3.2.1: `spawn('node', ['.next/standalone/server.js'], { env: { PORT: '0', HOSTNAME: '127.0.0.1' } })`
    - [ ] 3.2.2: 监听 stdout，正则匹配 `http://localhost:(\d+)` 或 `http://127.0.0.1:(\d+)`，提取端口存内存
    - [ ] 3.2.3: 进程 cleanup：`app.on('before-quit', () => nextServerProcess.kill())`
  - [ ] 3.3: 编写 `createWindow()` 函数：
    - [ ] 3.3.1: `new BrowserWindow({ width: 1200, height: 800, webPreferences: { contextIsolation: true, nodeIntegration: false, preload: ... } })`
    - [ ] 3.3.2: `mainWindow.loadURL(\`http://127.0.0.1:${nextPort}\`)`（**不是 file://**）
  - [ ] 3.4: 编写 app 事件监听：
    - [ ] 3.4.1: `app.on('ready', async () => { await spawnNextServer(); createWindow(); })`
    - [ ] 3.4.2: `app.on('window-all-closed', () => { nextServerProcess.kill(); app.quit(); })`
    - [ ] 3.4.3: `app.on('activate', ...)`（macOS reopen）

- [ ] Task 4: preload.ts 隔离脚本编写
  - [ ] 4.1: 导入 `contextBridge` + `ipcRenderer`
  - [ ] 4.2: 暴露 `window.api` 对象（最小版，Story 11.2 扩展 5 命令）
  - [ ] 4.3: 示例命令：`window.api.greet()` → main 返回 "Hello"

- [ ] Task 5: electron-builder 配置（S2 修订）
  - [ ] 5.1: 编写 `electron-builder.yml`：
    - [ ] 5.1.1: `appId: com.deeptutor.app`
    - [ ] 5.1.2: `files: ["dist/", "../web/.next/standalone/", "../web/.next/static/", "../web/public/"]`（standalone server runtime + static assets，**不含 out/**）
    - [ ] 5.1.3: `extraResources: [{ from: "../web/.next/static", to: "app/.next/static" }]`（standalone 需要 static 目录在运行时同位置）
    - [ ] 5.1.4: `mac:` 块配置 code signing
    - [ ] 5.1.5: `win:` + `linux:` 基础配置
  - [ ] 5.2: 添加 GitHub Secrets（`CSC_LINK`, `CSC_KEY_PASSWORD`）

### Build + Packaging

- [ ] Task 6: Webpack 配置修正
  - [ ] 6.1: 修改 `src/main/preload.ts` 引用路径
  - [ ] 6.2: 确保 `contextBridge` 在 Webpack 外部化（不 bundle）

- [ ] Task 7: 本地构建验证（macOS）
  - [ ] 7.1: `npm run build`（前端 Next.js）
  - [ ] 7.2: `npm run electron-build`（Electron 应用）
  - [ ] 7.3: `npm start`（本地运行 dev 版本）
  - [ ] 7.4: 验证 UI 完整性、无 console error

- [ ] Task 8: macOS 代码签名测试
  - [ ] 8.1: 用开发者证书签名 .app：`codesign -s - dist/DeepTutor.app`
  - [ ] 8.2: 验证 `codesign -v dist/DeepTutor.app`

## Dev Notes

### 关键决策（S2 修订后）
- **Next.js standalone SSR**: `output: "standalone"` 产出 `.next/standalone/server.js`（Node SSR runtime + Next.js API routes 完整保留），Electron main spawn 这个 server，BrowserWindow 加载 `http://127.0.0.1:<port>`
- **不走 SSG file://**: 原 spec "out/ 目录 + file://" 是 `next export` 模式（SSG，丢 API routes），与 DeepTutor 实际 next.config.js + D18 决策对立
- **preload + contextBridge**: 原生 Electron 模式，避免 v20+ 弃用的 `nodeIntegration`
- **Webpack vs Vite**: electron-react-boilerplate 用 Webpack，后续可迁移（不影响 Day 11 交付）

### 已知陷阱
1. **Next standalone 端口冲突**: `PORT=0` 让 OS 分配可避免，但需 regex 解析 stdout 提取端口
2. **Next standalone 缺 static 资源**: `.next/static/` 目录必须 cp 或 symlink 到 standalone 运行目录同位置（electron-builder.yml extraResources 处理）
3. **macOS 代码签名密钥来源**: 本地开发用 `codesign -s -`（自签），CI 用 GitHub Secrets
4. **Windows code signing**: 可选（Day 11 跳过，Day 22 发布时补）
5. **Docker compose 启动竞态**: Day 11 Story 11.1 仅启动 Next standalone，**不启 Docker compose**（Docker 编排在 Story 11.2 加入）

### 风险
- **R2 Manim 依赖**: Story 11.1 仅 Next.js 无需 Manim（Story 11.3 后 FastAPI subprocess 才用）
- **R3 Electron 包大**: 接受（VS Code 200+ MB 参照）

## UAT 验收

详见 `_bmad-output/验收单/Story-11.1-electron-framework-web-bundling.md`

## References

- Epic-11 _README §"Goals" Goal 1
- Round-22 Desktop 报告 §四（Electron + AnythingLLM 模式）
- electron-react-boilerplate: https://github.com/electron-react-boilerplate/electron-react-boilerplate

## 下一步

→ Story 11.2 Day 13-14 IPC Bridge + FastAPI subprocess
