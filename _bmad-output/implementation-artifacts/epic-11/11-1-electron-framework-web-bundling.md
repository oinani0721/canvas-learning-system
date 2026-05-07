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

### AC #2: Next.js standalone build 集成

- **Given** DeepTutor fork Next.js 应用已构建为 standalone（`npm run build`）
- **When** Electron app 启动
- **Then** 加载本地 `resources/app/out/` 目录作为静态文件源
- **And** 在 BrowserWindow 中加载 `file:///.../out/index.html`
- **And** 首屏显示 < 3 秒（包含 JS 执行）

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

### Frontend (Next.js Standalone)

- [ ] Task 1: 验证 Next.js standalone build 产物
  - [ ] 1.1: `cd ~/Desktop/canvas/deeptutor-fork/web && npm run build`
  - [ ] 1.2: 验证 `.next/standalone/` 和 `out/` 目录存在
  - [ ] 1.3: 验证 `out/index.html` 可被 file:// 加载

### Electron Setup

- [ ] Task 2: electron-react-boilerplate 初始化
  - [ ] 2.1: Fork `electron-react-boilerplate` 到 `~/Desktop/canvas/deeptutor-fork/desktop/`
  - [ ] 2.2: 删除示例代码（不需要 React demo）
  - [ ] 2.3: 保留 electron + webpack 基础设施

- [ ] Task 3: main.ts 进程编写
  - [ ] 3.1: 导入 `electron` + `path` + `isDev`
  - [ ] 3.2: 编写 `createWindow()` 函数：
    - [ ] 3.2.1: `new BrowserWindow({ width: 1200, height: 800, webPreferences: {...} })`
    - [ ] 3.2.2: 指定 preload 脚本路径
    - [ ] 3.2.3: 禁用 node integration（`nodeIntegration: false`）
  - [ ] 3.3: 编写 app 事件监听：
    - [ ] 3.3.1: `app.on('ready', createWindow)`
    - [ ] 3.3.2: `app.on('window-all-closed', () => app.quit())`
    - [ ] 3.3.3: `app.on('activate', ...)`（macOS reopen）

- [ ] Task 4: preload.ts 隔离脚本编写
  - [ ] 4.1: 导入 `contextBridge` + `ipcRenderer`
  - [ ] 4.2: 暴露 `window.api` 对象（最小版，Story 11.2 扩展 5 命令）
  - [ ] 4.3: 示例命令：`window.api.greet()` → main 返回 "Hello"

- [ ] Task 5: electron-builder 配置
  - [ ] 5.1: 编写 `electron-builder.yml`：
    - [ ] 5.1.1: `appId: com.deeptutor.app`
    - [ ] 5.1.2: `files: ["dist/", "out/"]`（Next.js standalone）
    - [ ] 5.1.3: `mac:` 块配置 code signing
    - [ ] 5.1.4: `win:` + `linux:` 基础配置
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

### 关键决策
- **Next.js standalone vs SSR**: standalone 模式输出纯静态 HTML/CSS/JS，Electron 直接加载，无需 Node.js server
- **preload + contextBridge**: 原生 Electron 模式，避免 v20+ 弃用的 `nodeIntegration`
- **Webpack vs Vite**: electron-react-boilerplate 用 Webpack，后续可迁移（不影响 Day 11 交付）

### 已知陷阱
1. **`file://` 加载 SPA 路由问题**: Next.js standalone 用 `_next/` 子目录，浏览器 `file://` 加载时可能 404。解决：webpack dev server 或 electron-serve 包装
2. **macOS 代码签名密钥来源**: 本地开发用 `codesign -s -`（自签），CI 用 GitHub Secrets
3. **Windows code signing**: 可选（Day 11 跳过，Day 22 发布时补）

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
