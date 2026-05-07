---
epic_id: "11"
title: "DeepTutor Desktop App 桌面化（Electron + 跨平台发布）"
prd_id: "canvas-learning-system"
status: "backlog"
priority: "P1"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
round_origin: "round-22"
mvp_window: "12 days (Day 11-22)"
start_date: "2026-05-17"
target_complete: "2026-05-30"
depends_on: ["epic-10"]
trigger_condition: "Epic-10 Day 10 UAT 5 验证场景 S1-S5 全 PASS（Path A 选定）"
---

# Epic-11: DeepTutor Desktop App 桌面化（Electron + 跨平台发布）

> **决策锁定**（D18 - 2026-05-07）: Electron + AnythingLLM 模式 → 社区验证 59.7k ⭐ → 1-2 周快速交付 + 4 周跨平台发布
>
> **触发条件**: Epic-10 Day 10 UAT 5 验证场景 S1-S5 全 PASS（用户选择 **Path A 继续 fork**）
>
> **总工作量**: ~80h（10-14 天一人全职 / 12 天可并行化）

---

## Why（用户痛点 + Round-22 调研收敛）

### 核心痛点（Round-22 6 报告深度调研）

#### P1 Math Animator + Visualize 在 CLI/SDK 不能"看到"（M4 映射对最强）

5 个并行 Agent 验证：
- Math Animator: Manim+ffmpeg → 服务端生成 MP4
- Visualize: 5 render_mode（SVG / Chart.js / Mermaid / HTML / auto）—— 客户端渲染

CLI/SDK 用户只能拿到文件路径或代码字符串，**无法直接展示**。Web 用户必须开浏览器，体验断裂。

**Desktop App 内嵌 WebView = 与 Web 体验 1:1 复刻**，且无浏览器依赖。

#### P2 用户 Day 5+ 原白板讲题依赖视觉化（M4 必保留）

Story 10.5 NodeDetailPanel 双 capability 入口：
- "讲题（Chat Math Animator）" → MP4 内嵌
- "Visualize" → 5 render_mode 内嵌

这些功能在 CLI/SDK 体验降级。**Desktop App 是解锁 CLI 用户视觉化的唯一路径**。

#### P3 用户主权 + 离线（NEG-2 + Round-18 L805）

用户 Round-18 批注："不上传文件，直接访问指定文件夹"。
- Web 默认走 localhost:3782（用户开浏览器）
- Desktop App 通过 IPC 直接读 vault md（OS 沙箱授权）
- 离线 100% 可用（FastAPI subprocess 本地）

### 决策坐标（Round-22 调研矩阵）

| 维度 | 决策 | 根据 |
|---|---|---|
| **技术选型** | Electron 28.x + Node.js subprocess | AnythingLLM 社区先例（59.7k ⭐） + 包大可接受 |
| **API 设计** | IPC Bridge (main ↔ renderer) + FastAPI subprocess | IPC 完整设计 + subprocess health check |
| **渲染验证** | 5 render_mode 全部 WebView 内 | Math Animator/Visualize 不弹外部播放器 |
| **打包** | electron-builder 3 平台 + GitHub Actions | 商用验证 + macOS notarization 成熟 |
| **启动时机** | Day 11（Epic-10 Day 10 验收后）| Path A 触发 |

### 备选方案（D18 已评估）

| 方案 | 包大 | 工期 | 风险 | 选 |
|---|---|---|---|---|
| **Electron + AnythingLLM 模式** | 100+ MB | 1-2 周 + 4 周发布 | 低（社区成熟） | ✅ |
| Tauri 2.0 | 5-10 MB | 1.5 周 | 中（Rust 学习 + macOS 签名坑） | ❌ |

---

## Goals（3 大目标 - 12 天交付）

### Goal 1: GUI 渲染 + Web 包装（Day 11-12）

- Next.js standalone build → Electron BrowserWindow 内嵌
- 双击 `.app`（macOS）/ `.exe`（Windows）/ `.AppImage`（Linux）启动
- 不依赖浏览器，完整离线 UI
- 启动时间 < 3 秒

### Goal 2: 本地文件 IPC + FastAPI subprocess（Day 13-14）

- main 进程 spawn `uvicorn deeptutor.api.main:app --port 0`
- IPC 命令 5 个：`vault_read` / `vault_write` / `vault_list` / `vault_watch` / `vault_unwatch`
- 用户首次选择 vault 目录（`~/.deeptutor-app/vault-path.json` 持久化）
- Health check 5s heartbeat + subprocess 崩溃自愈

### Goal 3: 渲染验证 + 跨平台发布（Day 15-22）

- Math Animator MP4 + Visualize 5 render_mode 全部 WebView 内渲染
- wikilink 导航走 IPC（< 100ms 响应）
- 3 平台安装包（macOS DMG + Windows EXE + Linux AppImage）
- macOS Apple notarization（签名 + 公证）
- electron-updater 自动更新

---

## Capabilities（功能层级清单）

### 基础层（Day 11-12）
- electron-react-boilerplate 框架（TS + Webpack）
- main.ts 进程生命周期 + preload.ts IPC 隔离
- Next.js standalone build 打包到 Electron 资源目录

### 深化层（Day 13-14）
- FastAPI subprocess 生命周期（port 0 自动检测 + health check）
- IPC 命令管道：request/response pattern
- Vault 沙箱授权 UI（首次选择 → 持久化 → 后续自动通信）

### 验证层（Day 15-18）
- useVaultFile React hook（自动 read + watch）
- RichMarkdownRenderer wikilink 跳转走 IPC
- Math Animator MP4 HTML5 `<video>` 播放（file:// URL）
- Visualize 5 render_mode（SVG/Chart.js/Mermaid/HTML/auto）全部 WebView 渲染

### 发布层（Day 19-22）
- electron-builder 配置（签名密钥、代码签名证书）
- GitHub Actions CI/CD（3 平台平行构建）
- electron-updater 自动更新机制
- Release notes + 版本管理

---

## Stories 索引（4 个 Story 按 Day 节奏）

| Story ID | 标题 | Day | 工作量 | Status | UAT 验收单 |
|---|---|---|---|---|---|
| **11.1** | Electron 框架 + Web 包装 | Day 11-12 | ~12h | backlog | `验收单/Story-11.1-*.md` |
| **11.2** | IPC Bridge + FastAPI subprocess | Day 13-14 | ~16h | backlog | `验收单/Story-11.2-*.md` |
| **11.3** | Vault 深度集成 + 渲染验证 | Day 15-18 | ~28h | backlog | `验收单/Story-11.3-*.md` |
| **11.4** | 跨平台发布 + 自动更新 | Day 19-22 | ~24h | backlog | `验收单/Story-11.4-*.md` |

---

## Acceptance Criteria（Epic 级 AC）

### AC #1: 3 平台桌面 App 启动

- **Given** GitHub Release 包含 macOS .dmg / Windows .exe / Linux .AppImage
- **When** 用户下载并双击安装/运行
- **Then** 应用启动 < 3 秒（冷启），DeepTutor Web UI 显示
- **And** 进程树：main.js ← 1 renderer (BrowserWindow) ← N FastAPI 子进程

### AC #2: Math Animator + Visualize 桌面内渲染（M4 落地）

- **Given** Math Animator 生成 MP4 + Visualize 输出 SVG/Chart.js 代码
- **When** 用户在 Desktop App 中调用 capability
- **Then** 渲染结果显示在 WebView 内（不弹出系统浏览器）
- **And** 5 render_mode 全部 support
- **And** MP4 通过 `<video src="file://...">` 播放无延迟

### AC #3: Vault 沙箱写入生效

- **Given** 用户首次启动 Desktop App 点击 "Select Vault"
- **When** 选择本地文件夹，Desktop App IPC 通信开始
- **Then** main 进程代理文件读写请求至 FastAPI subprocess
- **And** 用户在 Desktop App 编辑笔记 → 同步至本地 vault 目录文件
- **And** 文件变化自动 watch，wikilink 导航实时更新（< 100ms）

### AC #4: 自动更新通知

- **Given** 新版本发布到 GitHub Releases（Tag 格式 `v0.2.0`）
- **When** 用户运行当前版本 `v0.1.0` Desktop App，检查更新
- **Then** 弹出 update dialog：版本号 + Release notes + "Update Now" 按钮
- **And** 用户点击 "Update Now" → 后台下载 → 自动重启应用

### AC #5: 代码签名完整链（macOS）

- **Given** CI/CD 构建时提供 Apple Developer Team ID + code signing certificate
- **When** electron-builder 打包 macOS .dmg
- **Then** 用户下载 DMG → 双击安装 → gatekeeper 校验通过（无"未识别开发者"警告）
- **And** `codesign -v` 验证签名有效
- **And** 公证状态 `notarytool history` 显示 "Accepted"

---

## Risks（风险 + 缓解）

| # | 风险 | 概率 | 影响 | 缓解策略 |
|---|---|---|---|---|
| **R1** | macOS Apple notarization 流程复杂 | 中 | Day 22 卡壳 | Day 19 提前申请开发者账号 + 测试 notarytool 流程（~2h） |
| **R2** | Manim 依赖打包（LaTeX 3GB） | 中 | .app 包膨胀 | 分离 Manim 依赖：app 仅 Next.js，FastAPI subprocess 动态加载 |
| **R3** | Electron 包大（100MB+） | 低 | 用户下载缓慢 | 接受（与 Tauri 权衡已确认），GitHub Releases delta update |
| **R4** | FastAPI subprocess 崩溃无感知 | 中 | 用户操作卡死 | health check heartbeat 5s，3 次失败自动重启 + UI toast |
| **R5** | Windows Defender 误报 | 低 | 发布初期用户阻挡 | electron-builder 启用 code signing + timestamp authority |

---

## Dependencies（前置 + 外部）

### Epic 级依赖
- **依赖**: Epic-10 Day 10 验收通过（5 验证场景 S1-S5 全 PASS）
- **前置**: DeepTutor fork 仓库代码稳定 + Next.js build 产物可用

### 外部依赖
- **macOS**: Apple Developer Team ID + code signing certificate（存放 GitHub Secrets）
- **Windows**: 代码签名证书（optional，但推荐）
- **GitHub Actions**: 启用 Mac runners（需 GitHub Pro 或付费）

### 库依赖
- `electron@^28.0.0` + `electron-builder@^25.0.0` + `electron-updater@^6.0.0`
- `ipc-main` (Node.js native) + `contextBridge` (Electron preload)
- `fastapi`, `uvicorn`（DeepTutor 既有）

---

## 用户主权约束（NEG 反对批注落地）

- **NEG-1（Round-22 派生）**: ❌ 不绕过用户选 vault（首次必须 modal 选择）
- **NEG-2（Round-18 L805）**: ❌ 不上传 vault 文件，仅 IPC 读写本地
- **NEG-3（Round-22）**: ❌ Desktop App 不强制使用，Web 仍可访问 :3782（双轨并存）
- **NEG-4（D17 派生）**: ❌ MVP 期间不 git pull upstream（与 Epic-10 同源）

---

## 决策矩阵（Day 22 后选路）

| 路径 | 触发条件 | 后续投入 |
|---|---|---|
| **A. 继续 Desktop App + Web 双轨** | 3 平台用户均有人 + 自动更新稳定 | 月度 release（feature + bugfix） |
| **B. 仅保留 macOS Desktop**（非 Win/Linux） | 用户主要是 Mac + Win/Linux 装机率 < 10% | 简化 CI 仅 mac runner |
| **C. 退回纯 Web** | Desktop 包过大 / notarization 卡死 / 用户嫌麻烦 | Epic-11 经验作为研究档案 |

---

## 后续（Day 23+）

- **Day 23-25**: 用户 UAT 验收 + 错误修复（D-Batch 收敛）
- **Day 26-30**: Feature 锁定，进入 Round-23 新阶段
- **可选优化**（Round-23）:
  - Tauri v2 平行研究（对标 1.5 周时间线）
  - desktop/plugins 自动更新分离（避免整体重启）
  - wasm 优化（Web 组件 startup time）

---

## 关联文档

- **决策批注**: `_bmad-output/决策批注/D18-desktop-app-electron-2026-05-07.md`（Path A 后桌面化决策）
- **关联决策**: `_bmad-output/决策批注/D17-round22-fork-mvp-2026-05-06.md`（Round-22 主决策）
- **调研报告**: `_bmad-output/research/round-22-desktop-app-rendering-deep-explore-2026-05-07.md`
- **关联报告**: `_bmad-output/research/round-22-cli-sdk-book-engine-deep-explore-2026-05-07.md`
- **Epic-10 总览**: `_bmad-output/implementation-artifacts/epic-10/_README.md`
- **memory**: `decision_round22_fork_mvp.md` (D17) + 待写 `decision_d18_desktop.md`

---

*Epic-11 锚定文档。所有 Story 必须引用本文件 + 对应 Round-22 报告章节。*

*启动条件: Epic-10 Day 10 UAT 全 PASS（Path A 选定）。Day 11 实际启动日期由用户确认。*
