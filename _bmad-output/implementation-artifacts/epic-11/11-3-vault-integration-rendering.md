---
story_id: "11.3"
epic_id: "11"
prd_id: "canvas-learning-system"
status: "backlog"
priority: "P1"
estimate_hours: 28
depends_on: ["11.2"]
blocks: ["11.4"]
trace: ["FR-DEEP-05", "M4", "M9"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
day: "Day 15-18"
target_date: "2026-05-21 ~ 2026-05-24"
uat_sheet: "_bmad-output/验收单/Story-11.3-vault-integration-rendering.md"
---

# Story 11.3: Vault 深度集成 + 渲染验证

**Status**: backlog（target Day 15-18, 2026-05-21 ~ 2026-05-24）

## Story（用户故事）

As a 学习者, I want to see Math Animator videos and Visualize charts rendered inside the Desktop App window (no browser popup), and I want to click wikilinks to navigate between my notes, so that I can experience the full AI-powered learning flow with all visual elements in one place.

> **映射对**: M4（Whiteboard 讲题视觉化最强映射）+ M9（拆分点 + 双链 → Graphiti）

## 通俗化解释（给学习者）

> **一句话说**: 在 Desktop App 里，你可以看到 AI 生成的数学动画（MP4 视频）和各种图表（折线图、流程图等），还能点击笔记里的 `[[概念]]` 链接跳转。所有东西都在一个窗口里，不会弹出浏览器。

**你会遇到的场景**:
- 在 DeepTutor 里请求"讲解抛物线"→ AI 生成 Manim 动画
- 动画以视频形式显示在结果区（HD 播放，可拖动进度条）
- 请求"画函数图表"→ AI 生成 Chart.js / SVG 图表
- 图表显示在结果区（可交互）
- 在笔记中写 `[[递归概念]]` → 渲染成蓝色链接 → 点击跳转到递归笔记

**这个功能帮你**:
- 学习变得"沉浸式"（一个窗口里所有内容）
- 动画和图表质量不缩水（完整 WebView 渲染）
- 知识网络自动形成（wikilink 导航）

**用个比喻**: 📺 就像把电视、相册、笔记本融合到同一个屏幕——不用切换设备，所有东西都在桌面 App 里。

## Acceptance Criteria

### AC #1: useVaultFile React hook 实现

- **Given** React 组件需要读取 vault 中的 markdown 文件
- **When** 组件 mount 时，hook 初始化
- **Then** hook 返回 `{ content, loading, error, update() }` 对象
- **And** hook 自动调用 `vaultRead(filename)` → 解析 frontmatter + markdown
- **And** hook 自动 watch 文件变化（通过 `vaultWatch()`）
- **And** 文件变化时自动更新 state（触发 re-render）

### AC #2: RichMarkdownRenderer wikilink 跳转走 IPC

- **Given** 用户在笔记中有 `[[recursion]]` 链接，点击
- **When** `<a class="wikilink" href="/notes/recursion">` 触发 click 事件
- **Then** renderer 拦截链接：`event.preventDefault()`
- **And** 调用 `window.api.vaultRead('recursion.md')` 读文件
- **And** 导航至新笔记（更新 URL bar + re-render 内容）
- **And** 导航速度 < 100ms（感觉流畅）

### AC #3: Math Animator MP4 渲染（HTML5 video，S3 修订 — 不暴露 file://）

> **2026-05-07 对抗性审查 S3 修订**：原 spec `<video src="file:///path/...">` 暴露用户电脑绝对路径（隐私风险）+ 与 BrowserWindow 加载 `http://localhost`（S2 修订）的 origin 不一致触发 CORS 问题。修订为 `media://` 自定义协议或 HTTP localhost。

- **Given** AI 生成 MP4 并保存至 FastAPI subprocess 输出目录（如容器内 `~/.cache/deeptutor/agent/math_animator/{turn_id}/video.mp4`）
- **When** 结果区显示该输出
- **Then** 渲染为以下二选一：
  - **方案 A（推荐）**：`<video src="media://math-animator/{turn_id}.mp4" controls>` — Electron main 进程注册 `media://` 协议处理器，映射到容器输出目录（路径白名单防穿越）
  - **方案 B**：`<video src="http://127.0.0.1:8001/api/v1/math-animator/output/{turn_id}" controls>` — 走 DeepTutor backend 静态文件服务（已有 `NEXT_PUBLIC_API_BASE` 机制可复用）
- **And** 视频在 WebView 内完全播放（不弹出系统播放器）
- **And** 支持全屏、速度调整、截图等 HTML5 标准功能
- **And** 用户右键复制视频地址 → 看到 `media://...` 或 `http://localhost:...`，**不暴露 `/Users/<name>/.cache/...` 等绝对路径**

### AC #4: Visualize 5 render_mode 全部支持

- **Given** Visualize capability 输出 5 种 render_mode：SVG / Chart.js / Mermaid / HTML / auto
- **When** 渲染结果
- **Then**:
  - **SVG**: 直接 `dangerouslySetInnerHTML` 或 sanitize 后 inline
  - **Chart.js**: 包装为 `<canvas>` + 动态加载 chart.js 库
  - **Mermaid**: 包装为 `<div class="mermaid">` + 动态加载 mermaid.js
  - **HTML**: 放入 `<iframe sandbox>` 隔离执行
  - **auto**: AI 选择最佳 mode，用上述渲染
- **And** 所有 mode 都在 WebView 内完整显示（无弹窗）

### AC #5: 离线渲染验证

- **Given** Desktop App 启动，网络离线（disable WiFi）
- **When** 用户请求 Math Animator 或 Visualize
- **Then** FastAPI subprocess 可离线调用（本地 Manim / matplotlib / chart.js）
- **And** 动画/图表正常生成、显示
- **And** 无外网请求（tcpdump 验证）

## Tasks / Subtasks

### React Hook + Vault Integration

- [ ] Task 1: useVaultFile hook
  - [ ] 1.1: 创建 `web/hooks/useVaultFile.ts`
  - [ ] 1.2: 签名：`useVaultFile(filename: string): { content, loading, error, update }`
  - [ ] 1.3: 内部用 `useState` + `useEffect` 实现
  - [ ] 1.4: cleanup 时调用 `vaultUnwatch()`

### Wikilink 导航集成

- [ ] Task 2: RichMarkdownRenderer wikilink 点击拦截
  - [ ] 2.1: 修改 `web/components/common/RichMarkdownRenderer.tsx`
  - [ ] 2.2: 添加 event listener 拦截 `.wikilink` click
  - [ ] 2.3: `onWikilinkClick()` 回调：调用 `vaultRead()` → 导航

- [ ] Task 3: 路由集成（Navigation sidebar）
  - [ ] 3.1: 创建 React Router 路由
  - [ ] 3.2: 路由 `/notes/:slug` 显示笔记内容
  - [ ] 3.3: wikilink 导航时修改 URL → re-render
  - [ ] 3.4: 返回按钮 + 面包屑导航

### Math Animator + Visualize 渲染

- [ ] Task 4: HTML5 video 元素（S3 修订 — `media://` 协议）
  - [ ] 4.1: 修改结果渲染组件，检测输出类型是否为 `video/mp4`
  - [ ] 4.2: Electron main 进程注册 `media://` 协议（`protocol.registerFileProtocol('media', ...)`）：
    - [ ] 4.2.1: `media://math-animator/{turn_id}.mp4` → 映射到容器卷挂载位置 `~/.cache/deeptutor/agent/math_animator/{turn_id}/video.mp4`
    - [ ] 4.2.2: 路径白名单（仅允许 `~/.cache/deeptutor/` 子目录）
    - [ ] 4.2.3: 失败 → 返回 404 而不是绝对路径
  - [ ] 4.3: 渲染 `<video src="media://math-animator/{turn_id}.mp4" controls>`（**不是** file://）
  - [ ] 4.4: Renderer 通过 IPC 询问 main 当前 turn_id 对应 mp4 是否存在 + 获取 media:// URL
  - [ ] 4.5: 添加 CSS：`width: 100%; max-width: 800px; border-radius: 8px;`
  - [ ] 4.6: 验证 seekbar + play/pause + fullscreen 功能
  - [ ] 4.7: **fallback 方案 B**：若 `media://` 协议注册失败，降级用 `http://127.0.0.1:8001/api/v1/math-animator/output/{turn_id}`（HTTP localhost，CORS_ORIGINS 已含）

- [ ] Task 5: Visualize renderer（5 modes）
  - [ ] 5.1: 创建 `web/components/VisualizationRenderer.tsx`
  - [ ] 5.2: 根据 `render_mode` 分支渲染（5 modes）
  - [ ] 5.3: SVG / Chart.js canvas / Mermaid / HTML iframe / auto

- [ ] Task 6: CDN 库动态加载
  - [ ] 6.1: 创建 `web/lib/cdn-loader.ts`（Singleton 加载 chart.js / mermaid.js）
  - [ ] 6.2: 首次加载时 `<script>` tag 动态注入
  - [ ] 6.3: 后续调用复用已加载库

### Integration + Verification

- [ ] Task 7: 端到端集成测试
  - [ ] 7.1: 启动 Desktop App，vault 选择完毕
  - [ ] 7.2: 测试 Math Animator：生成 MP4 → 显示 `<video>` → 播放
  - [ ] 7.3: 测试 Visualize（5 modes）：逐个测试
  - [ ] 7.4: 测试 wikilink 导航：< 100ms

- [ ] Task 8: 性能优化
  - [ ] 8.1: 测量首屏时间（笔记加载 → 内容显示）
  - [ ] 8.2: 目标 < 200ms

- [ ] Task 9: 离线渲染测试
  - [ ] 9.1: 断网（disable WiFi）
  - [ ] 9.2: Math Animator + Visualize 调用验证可用
  - [ ] 9.3: network monitor 确认无外网请求

## Dev Notes

### 关键决策
- **HTML5 video vs 自定义播放器**: HTML5 原生足够，无需 Shaka Player
- **Mermaid DSL 和 SVG**: Mermaid 最终也是 SVG，但输出 DSL 时需动态 render
- **iframe sandbox 隔离**: HTML mode 用 sandbox 防恶意代码（XSS 防护）

### 已知陷阱（S3 修订后）
1. **`media://` 自定义协议必须 main 进程注册**：renderer 直接 fetch 不行，需 main 通过 `protocol.registerFileProtocol` 注册（在 `app.whenReady()` 之后）
2. **`media://` 路径白名单**：必须强校验，否则攻击者构造 `media://../../etc/passwd` 可读任意文件
3. **CDN 库 offline fallback**：chart.js 等库从 CDN 加载，离线则失败。考虑本地打包
4. **wikilink 目标不存在时的处理**：`[[nonexistent]]` 点击时 vaultRead 返回 404 → 提示"笔记不存在"
5. **HTTP localhost CORS**：BrowserWindow 走 `http://127.0.0.1:<frontend_port>`（S2 修订）→ fetch `http://127.0.0.1:8001/api/...` 同 origin 父级（localhost），但端口不同仍触发 CORS preflight，Canvas/DeepTutor backend CORS_ORIGINS 必须含 frontend dynamic port（`http://127.0.0.1:*` 或具体注入）

### 风险
- **R2 Manim 依赖打包**: app 仅 Next.js，FastAPI subprocess 动态加载 Manim
- **R10 Visualize 5 mode 浏览器兼容性**: 优先 SVG（最广兼容）

## UAT 验收

详见 `_bmad-output/验收单/Story-11.3-vault-integration-rendering.md`

## References

- Epic-11 _README §"Goals" Goal 3
- Round-22 Desktop 报告 §六（5 render_mode 完整对照）
- Story 10.5 Round-22 修订段（VisualizationRenderer 5 mode 集成）

## 下一步

→ Story 11.4 Day 19-22 跨平台发布 + 自动更新
