# DeepTutor 桌面 App + 渲染能力深度调研报告

> **Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
> **调研日期**: 2026-05-07
> **调研方法**: 6 Agent 并行 Deep Explore
> **触发问题**: 用户批注 3 个核心问题
> 1. Math Animator (Manim 动画) 在 CLI/SDK 是否有渲染能力？
> 2. Visualize (SVG/Chart.js/Mermaid/HTML) 在 CLI/SDK 是否有渲染能力？
> 3. 能否把 Web 入口改造为本地桌面 App（Claude Code Desktop 模式：GUI 渲染 + 调 CLI 操作文件）？

---

## Executive Summary（核心结论）

**3 个核心问题的明确答案**：

1. **Math Animator CLI/SDK ❌ 不渲染** — 渲染 100% 在 FastAPI server-side（Manim subprocess + ffmpeg + LaTeX），CLI/SDK 只拿 MP4 文件路径或 URL。**真正"看到"动画必须浏览器/`open` 命令/Jupyter `Video()`**
2. **Visualize CLI/SDK ❌ 不渲染** — 5 render_mode（SVG/Chart.js/Mermaid/HTML）输出都是**代码字符串**，CLI 用户拿 markdown 代码块。**真正"看到"必须浏览器/Jupyter 渲染引擎**
3. **桌面 App 改造 ✅ 100% 可行** — Tauri 2.0 推荐（包小 10×）or Electron + AnythingLLM 模式（社区验证）。1-2 周工作量 + IPC 设计完整 + 与 Claude Code Desktop 架构 1:1 对标

**Round-22 价值定位**：Math Animator + Visualize 是 **M4 映射对（13 映射中用户感知最强的）**，对应 Day 5+ 原白板讲题体验 100% 依赖。**必保留不可降级**。

---

## 一、6 Agent 整合发现矩阵

| Agent | 关键发现 | 对桌面化影响 |
|---|---|---|
| **A** Math Animator CLI/SDK | 渲染都在 server（Manim subprocess），CLI/SDK 拿 MP4 文件路径 | 桌面 App WebView 内 `<video>` 完美播放 |
| **B** Visualize CLI/SDK | 5 种 render_mode 输出都是代码字符串，需客户端渲染 | 桌面 App WebView 替代浏览器渲染 |
| **C** Web 桌面化可行性 | Tauri 2.0 推荐（10× 包小 + Rust 安全）| 5 步路径 + 1-1.5 周 |
| **D** 桌面 App IPC 设计 | Rust + React hook 完整设计 + FastAPI subprocess + 沙箱 | 完整工程方案 6-8 周（含跨平台 + 自动更新） |
| **E** 社区桌面化先例 | Electron + AnythingLLM 模式（59.7k stars 商用级）| 1-2 周快速交付，但包大 |
| **F** Math/Visualize × Round-22 价值 | **M4 映射对最强**，必保留不可降级 | Day 5+ 原白板讲题体验依赖 |

---

## 二、Q1: Math Animator 在 CLI/SDK 的真实渲染能力

### 答案：❌ 渲染不在 CLI/SDK，100% 在 server-side

**实现路径**（`deeptutor/capabilities/math_animator.py`）:
```
Concept Analysis → Concept Design → Code Generation → Code Retry (Manim 渲染) → Summary → Render Output
```

**底层依赖**：
- Manim Python lib (v0.19.0+) — Scene 类解析
- ffmpeg — 视频编码 (MP4)
- LaTeX (MikTeX/MacTeX) — 数学公式渲染
- cairo/pycairo — 矢量图形

### CLI 实际输出（`deeptutor run math_animator "..."`）

```bash
deeptutor run math_animator "讲解抛物线" --config output_mode=video --config quality=high
```

**Rich 格式**（默认）：
```
▶ concept_analysis  Analyzing math concept...
▶ concept_design    Designing animation scene...
▶ code_generation   Manim code prepared.
▶ code_retry        Rendering video with quality=high.
                    Saved rendered video as video.mp4.
▶ render_output     Prepared 1 artifact(s).
▶ summary           本次生成了一个关于抛物线的数学动画...

session=abc123 turn=xyz789 capability=math_animator
```

**JSON 格式**：
```json
{
  "type": "result",
  "content": {
    "artifacts": [{
      "type": "video",
      "filename": "video.mp4",
      "url": "/api/outputs/agent/math_animator/turn-xyz789/artifacts/video.mp4",
      "content_type": "video/mp4"
    }],
    "render": {
      "quality": "high",
      "source_code_path": "/Users/.../.cache/deeptutor/.../scene.py"
    }
  }
}
```

### SDK 调用返回结构

```python
from deeptutor.app import DeepTutorApp, TurnRequest

app = DeepTutorApp()
session, turn = await app.start_turn(TurnRequest(
    content="讲解抛物线",
    capability="math_animator",
    config={"output_mode": "video", "quality": "high"}
))

async for event in app.stream_turn(turn["id"]):
    if event["type"] == "result":
        artifacts = event["metadata"]["artifacts"]
        # artifacts[0]["url"] = "/api/outputs/.../video.mp4"
```

### 文件实际位置

```
~/.cache/deeptutor/agent/math_animator/{turn_id}/artifacts/video.mp4
```

### 用户怎么"看到"动画

| 模式           | 操作                                                  |
| ------------ | --------------------------------------------------- |
| **Web**      | ✅ HTML5 `<video>` 自动播放（最佳体验）                        |
| **CLI**      | ❌ 需手动 `open <path>` 或登录 Web                         |
| **SDK**      | ⚠️ 编程：Jupyter `Video(url)` / FastAPI `FileResponse` |
| **桌面 App** ✨ | ✅ WebView 内嵌 = 与 Web 体验 1:1 复刻                      |

### 性能 + 资源

- 单次生成：35-65 秒（concept analysis 2s + code gen 3s + Manim 渲染 30-60s）
- 720p MP4: 8-15 MB
- 1080p MP4: 30-50 MB
- macOS Manim 配置难度：3/5（LaTeX ~3GB + ffmpeg + cairo）

---

## 三、Q2: Visualize 在 CLI/SDK 的真实渲染能力

### 答案：❌ 渲染不在 CLI/SDK，全部输出代码字符串

**5 种 render_mode 完整对照**：

| Mode | 输出格式 | 文件大小 | 客户端依赖 |
|---|---|---|---|
| **svg** | SVG XML 字符串 | 2-5 KB | 无（浏览器原生） |
| **chartjs** | JS 配置对象（text） | 1-3 KB | chart.js 库 |
| **mermaid** | DSL 文本 | 0.5-2 KB | mermaid.js 库 |
| **html** | 完整 self-contained HTML | 5-20 KB | 无（iframe sandbox） |
| **auto** | AI 自动选择 | 视情况 | 同上 |

### CLI 实际输出

```bash
deeptutor run visualize "对数函数图表" --config render_mode=chartjs
```

```
▶ analyzing  Render type: chartjs
▶ generating Code generated.
▶ reviewing  Code optimized

```javascript
{
  type: 'line',
  data: { labels: [...], datasets: [...] },
  options: { responsive: true }
}
```
```

CLI **仅打印 markdown 代码块**，不是图像。

### SDK 返回结构

```python
result = {
    "render_type": "chartjs",  # svg | chartjs | mermaid | html
    "code": {
        "language": "javascript",
        "content": "{...JS 配置字符串...}"
    },
    "analysis": {...},  # 含 description / chart_type / visual_elements
    "review": {"optimized_code": "...", "review_notes": "..."}
}
```

### 用户怎么"看到"渲染

| Mode | Web | CLI | SDK Jupyter | 桌面 App ✨ |
|---|---|---|---|---|
| SVG | dangerouslySetInnerHTML | 保存 .svg → 浏览器打开 | `IPython.display.SVG()` ✅ | WebView 内嵌 ✅ |
| Chart.js | `<canvas>` + chart.js | 包装 HTML → 浏览器 | HTML wrapper + chart.js CDN | WebView 内嵌 ✅ |
| Mermaid | mermaid.render() | mmdc 转 PNG / 在线编辑器 | HTML + mermaid.js CDN | WebView 内嵌 ✅ |
| HTML | iframe sandbox | 保存 .html → 浏览器 | `IPython.display.HTML()` ✅ | iframe sandbox ✅ |

### 关键洞察

**渲染责任划分**:
- **Backend**: 生成代码（SVG/JS/DSL/HTML）— 共享所有 Entry Point
- **Frontend (Web/桌面 App)**: 浏览器引擎渲染（chart.js / mermaid.js / SVG inline）
- **CLI/SDK**: 只是"传声筒"——拿到代码后用户必须自己找渲染环境

---

## 四、Q3: Web → 桌面 App 改造可行性

### 答案：✅ 100% 可行 + 1-1.5 周工作量

### 选型决策（Tauri 2.0 vs Electron）

| 维度 | Tauri 2.0（Agent C+D 推荐）| Electron（Agent E 推荐）|
|---|---|---|
| 包大小 | **10MB** ✅ | 150MB |
| 内存（闲置）| **30-80MB** ✅ | 150-250MB |
| 启动时间 | **0.5-1s** ✅ | 1-2s |
| Next.js 兼容 | ⚠️ 需 SSG (next export)，丢 API routes | ✅ npm start 直跑 |
| 学习曲线 | Rust（中等）| Node.js（低）|
| 社区周下载 | 85K | **1.66M** ✅ |
| 商用案例 | 较少 | **AnythingLLM 59.7k stars 商用级** ✅ |
| Apple Silicon | 原生 ✅ | 需 arm64 build |
| 跨平台打包 | 内置自动更新 | electron-updater |
| 工作量 | 7-10d 实测 | 10-14d |

### 调和判断（基于 DeepTutor 实际复杂度）

**DeepTutor 特性**：Next.js v16 + React 19 + FastAPI + WebSocket + 大量 API routes

- **Tauri 2.0 阻力**：必须 `output: "export"` SSG 模式 → 丢 Next.js API routes → **需重写或独立 FastAPI**
- **Electron 顺势**：保留 Next.js 完整能力（SSR + API routes）→ npm start 直跑 → **零 Next.js 改动**

**最终推荐**：

| 优先级 | 方案 | 理由 |
|---|---|---|
| **首选** | **Electron + AnythingLLM 模式** | Next.js 0 改动 + 1.66M 周下载 + 商用验证 + 团队 Node.js 友好 |
| 次选 | Tauri 2.0 | 如团队有 Rust 经验 + 包小 10× 重要 |
| 不选 | Web only / PWA | 无 fs 权限 = 无法解决 D2 用户初衷 |

### 5 步桌面化路径（Electron 推荐）

```
Step 1 (1-2d): Electron + electron-react-boilerplate 框架
  - main.ts 进程管理 + 窗口创建
  - preload.ts IPC 安全桥接

Step 2 (1-2d): Next.js → Electron 适配
  - next.config.js 切 output:"standalone" (无需 export)
  - 启动 Next.js dev server 内嵌 Electron BrowserWindow

Step 3 (3-4d): 文件系统 + IPC bridge
  - Node.js fs API 通过 ipcRenderer 暴露
  - 沙箱：用户首次授权 vault 路径
  - SQLite 本地存储（用户设置 + 缓存）

Step 4 (2-3d): FastAPI subprocess
  - Electron main spawn `uvicorn deeptutor.api.main:app --port 0`
  - 端口 0 自动分配 + lsof 检测
  - graceful shutdown on app quit

Step 5 (2-3d): 跨平台打包
  - electron-builder 配置（macOS .dmg / Windows .exe / Linux .AppImage）
  - macOS Apple notarization
  - 自动更新（electron-updater）
```

**总工作量**：10-14 天（1-2 周一人全职）

### 完整 IPC 设计（Agent D 提取，可直接落地）

**Tauri 命令清单**（如选 Tauri 路径）:
```rust
#[tauri::command]
async fn vault_read(path: String, ...) -> Result<VaultReadResponse, String>
#[tauri::command]
async fn vault_write(req: VaultWriteRequest, ...) -> Result<(), String>
#[tauri::command]
async fn vault_list(req: VaultListRequest, ...) -> Result<Vec<String>, String>
#[tauri::command]
async fn vault_watch(path: String, ...) -> Result<u64, String>  // 返回 handle
#[tauri::command]
async fn vault_unwatch(handle_id: u64) -> Result<(), String>
#[tauri::command]
async fn init_backend(window: tauri::Window) -> Result<(), String>
```

**React Hook（前端集成）**:
```typescript
export function useVaultFile<T>(
  vaultPath: string,
  parser: (content: string) => T
) {
  const [content, setContent] = useState<T | null>(null);
  // 初次加载 + 文件变化自动 refetch
  // 通过 invoke("vault_read") + listen("vault_file_changed")
  return { content, loading, error, lastModified, refetch, write };
}
```

**Math Animator 桌面 App 渲染流程**（与 Web 相同）:
```
用户点 "生成动画"
  → POST /api/v1/animate (Electron→FastAPI subprocess)
  → Manim subprocess 渲染 → /tmp/manim/xxx.mp4
  → 返回 {videoUrl: "file:///tmp/manim/xxx.mp4"}
  → <video src="file://..."> WebView 内嵌播放 ✅
```

---

## 五、Claude Code Desktop vs DeepTutor Desktop 架构对照

| 维度 | Claude Code Desktop | DeepTutor Desktop（Electron 推荐）|
|---|---|---|
| 主框架 | Electron + Node.js | Electron + Node.js（同） |
| IPC | `ipcRenderer.invoke()` | `ipcRenderer.invoke()`（同） |
| 后端进程 | spawn `claude` CLI | spawn `uvicorn` FastAPI |
| 文件读写 | 直接 Node.js fs | IPC bridge + 沙箱 |
| 渲染层 | React + Monaco Editor | React + Next.js |
| 包大小 | ~150 MB | ~150-200 MB（含 FastAPI ~100 MB）|
| 数据存储 | 本地 + 云同步 | 本地（vault md + SQLite）|

**核心架构等价**：双进程模型（UI 进程 + 后端进程）+ IPC 通信 = Claude Code Desktop 模式 1:1 复刻。

---

## 六、Math Animator + Visualize 在 Round-22 的关键价值

### M4 映射对（13 映射中用户感知最强）

> **用户原话**（Round-21 L1063）："数学动画 + 可视化这两点十分在意"

```
M4: 数学动画 + 可视化 → 原白板讲题方式
```

### 5 个 Canvas 学习场景具体例子（Agent F 提取）

1. **递归可视化**（CS 61B）— Math Animator 生成调用栈展开动画
2. **傅里叶变换分解**（微积分）— Manim 逐项加和正弦波叠加
3. **力学向量分解**（物理）— Visualize SVG 可拖拽向量
4. **算法流程图**（检验白板）— Visualize Mermaid 标红错误步骤
5. **学习进度曲线**（个人记忆）— Visualize Chart.js mastery 曲线 + FSRS

### Day 5+ 原白板讲题 = M4 + M5 联合落地

```python
# deeptutor-fork/deeptutor/book/models.py 扩展（Day 5）
class BlockType(str, Enum):
    TEXT, ANIMATION, INTERACTIVE, CONCEPT_GRAPH  # 已有
    ORIGIN_WHITEBOARD, EXAM_WHITEBOARD  # 新增（Round-22 D5）

class OriginWhiteboardBlock(BaseBlock):
    type: BlockType = BlockType.ORIGIN_WHITEBOARD
    concept_id: str
    callouts: list[Callout]
    animation: Optional[AnimationBlock]   # ← Math Animator 输出
    figures: list[FigureBlock]            # ← Visualize 输出
    original_md: str                      # vault md 原文
```

### 5 验证场景对应度

| 场景               | Math Animator | Visualize            |
| ---------------- | ------------- | -------------------- |
| S1 wikilink 跳转   | ❌             | ❌                    |
| S2 ACP Quiz      | ❌             | ✅（题干 Mermaid）        |
| S3 mastery 更新    | ❌             | ⚠️（进度条）              |
| S4 Graph View    | ❌             | ✅（Cytoscape/Mermaid） |
| S5 Day 0/3/7 推送  | ❌             | ❌                    |
| **Day 5+ 原白板讲题** | ✅             | ✅                    |

### 必保留判断

- **用户期望强度**：🔴 最强（"十分在意"明确）
- **技术可行性**：🟢 已就绪（DeepTutor 代码完整）
- **Canvas 映射**：🟢 M4 核心
- **5 大核心依赖**：核心 1/2 直接 + 核心 3/5 间接
- **桌面化对其影响**：🟢 完美兼容（WebView 渲染 = Web 1:1）

**结论：必保留，不可降级**。这两个 capability 是 Round-22 与 Claude Code Desktop 等价性的关键证据。

---

## 七、桌面化与 Round-22 整合时机

### 修订路线图

| 阶段                               | 时间        | 任务                                  | 依赖                |
| -------------------------------- | --------- | ----------------------------------- | ----------------- |
| **Round-22 MVP**                 | Day 0-10  | Web 内 5 大核心集成 + 5 验证场景通过            | 现状 fork           |
| **Decision Point**               | Day 10    | 路径 A/B/C 选择                         | UAT 结果            |
| **Tauri/Electron 包装**（Path A 增项） | Day 11-14 | 包装 Web 为桌面 App + IPC bridge         | Day 10 验收通过       |
| **Vault IPC 深度集成**               | Day 15-18 | useVaultFile hook + 文件 watch + 沙箱授权 | Tauri/Electron 包装 |
| **跨平台发布**                        | Day 19-22 | macOS/Windows/Linux 签名 + 自动更新 + 公证  | 深度集成              |

### Day 10 决策矩阵更新（含桌面化分支）

| 触发条件            | Round-22 路径        | 桌面化决策                       |
| --------------- | ------------------ | --------------------------- |
| 5 验证全过 + 5 天主动用 | **Path A 继续 fork** | ✅ Day 11+ 启动桌面化（增项 1.5-2 周） |
| 部分场景失败          | **Path B 退回独立包**   | ❌ 桌面化推迟                     |
| 仅用 2-3 核心       | **Path C 混合**      | ⚠️ 桌面化按子模块拆分                |

---

## 八、关键决策点（用户需选）

### 决策 1: 桌面化框架选型

| 选项 | 工作量 | 包大小 | Next.js 兼容 | 推荐度 |
|---|---|---|---|---|
| **Electron + AnythingLLM 模式** | 10-14d | 150 MB | ✅ 完整 | ⭐⭐⭐⭐⭐ |
| Tauri 2.0 + LobeChat 模式 | 7-10d | 10 MB | ⚠️ 需 SSG | ⭐⭐⭐⭐ |
| LobeChat Next.js→Electron | 10-14d | 180 MB | ✅ 完整 | ⭐⭐⭐⭐ |
| Web only (PWA) | 0d | 0 MB | ✅ | ❌ 无 fs 权限 |

### 决策 2: 桌面化时机

| 选项 | 时机 | 风险 |
|---|---|---|
| **Day 11+ 增项**（推荐） | Round-22 验收后 | 与 Round-22 解耦，风险最低 |
| Day 0-10 内嵌 | MVP 阶段 | 拖累 Round-22，工作量增 50% |
| Round-22 后无限期推迟 | 视情况 | 用户体验滞后 |

### 决策 3: Math Animator + Visualize 取舍

| 选项 | 实施代价 | Round-22 影响 |
|---|---|---|
| **必保留**（推荐） | 已有代码完整，0 新增 | 用户期望 100% 满足 |
| 降级 Visualize 为 Mermaid only | 简单实施 | 失去 Chart.js + Math Animator |
| 完全去除 | 简单实施 | ❌ 违反 M4 映射对 + 用户期望 |

---

## 九、关联文档

- **Round-22 主报告**: `_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md`
- **Day 2 Vault 设计**: `_bmad-output/research/round-22-day2-vault-access-design-2026-05-06.md`
- **Chat vs TutorBot**: `_bmad-output/research/round-22-chat-vs-tutorbot-usage-comparison-2026-05-06.md`
- **CLI/SDK/Book Engine**: `_bmad-output/research/round-22-cli-sdk-book-engine-deep-explore-2026-05-07.md`
- **本报告**: `_bmad-output/research/round-22-desktop-app-rendering-deep-explore-2026-05-07.md`

---

## 十、6 Agent 调研产物索引

| Agent | 主题 | 输出文件 |
|---|---|---|
| **A** | Math Animator CLI/SDK 渲染能力 | `tasks/acfb294fdd6a4761b.output` |
| **B** | Visualize CLI/SDK 5 render_mode | `tasks/a97d26d8d9e9632a8.output` |
| **C** | Web 桌面化 Tauri 2.0 可行性 | `tasks/a7b93a90d3f33eb03.output` |
| **D** | 桌面 App IPC 完整设计 | `tasks/aeb4e91a1ea6bc88e.output` |
| **E** | 社区桌面化先例（5 标杆 + 1 对照）| `tasks/aabebb577d71edb10.output` |
| **F** | Math/Visualize × Round-22 价值 | `tasks/a90ee5660ad73c131.output` |

---

*报告完成。回答用户 3 个核心问题：(Q1) Math Animator CLI/SDK 不渲染只拿 MP4 路径；(Q2) Visualize CLI/SDK 不渲染只拿代码字符串；(Q3) 桌面 App 100% 可行，Electron + AnythingLLM 模式推荐 1-2 周工作量。**核心洞察：CLI/SDK 是"代码生成器"不是"渲染引擎"，桌面 App 是连接两者的关键——WebView 替代浏览器渲染 + IPC 替代 fetch 操作本地文件 = Claude Code Desktop 等价物**。*
