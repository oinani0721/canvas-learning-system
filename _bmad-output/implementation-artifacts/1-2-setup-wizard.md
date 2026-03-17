# Story 1.2: 安装引导向导

Status: ready-for-dev

## Story

As a 新用户,
I want 首次启用插件时自动弹出引导向导，逐步检测 Docker、后端 API、Neo4j、LLM API、LanceDB 五个组件状态，
so that 我知道系统是否就绪，哪里需要修复。

## Acceptance Criteria

1. **AC-1: 首次启用自动弹出**
   - **Given** 用户首次启用插件（或系统检测到未完成初始化——`data.json` 中 `setupComplete` 为 `false` 或不存在）
   - **When** 插件加载完成
   - **Then** 自动弹出安装引导 Modal（Obsidian `Modal` 类）
   - **And** 非首次启用且 `setupComplete === true` 时不弹出
   - **And** 用户可随时通过命令面板 `Canvas: 打开安装引导` 手动重新触发

2. **AC-2: 5 步检测流程**
   - **Given** 安装引导 Modal 已打开
   - **When** 向导按顺序执行检测
   - **Then** Step 1：检测 Docker Desktop 运行状态（通过 `docker info` 命令或 Docker socket）
   - **And** Step 2：检测后端 API 可达（`GET http://localhost:8001/api/v1/system/health` 返回 200）
   - **And** Step 3：检测 Neo4j 连通性（从后端健康检查响应中读取 Neo4j 组件状态）
   - **And** Step 4：检测 LLM API 可用性（从后端健康检查响应中读取 Ollama 组件状态，或用户已配置外部 LLM API Key）
   - **And** Step 5：检测 LanceDB 就绪（从后端健康检查响应中读取 LanceDB 组件状态）
   - **And** 每步检测有明确的"检测中"→"通过/失败"状态过渡

3. **AC-3: 组件状态灯 UI**
   - **Given** 检测流程执行中或执行完成
   - **When** 用户查看 Modal
   - **Then** 每个组件显示状态灯：绿色圆点（就绪）/ 红色圆点（未就绪）/ 旋转图标（检测中）
   - **And** 状态灯旁显示组件名称和简短状态描述
   - **And** UI 使用 Obsidian CSS 变量适配 Light/Dark 主题
   - **And** CSS 类名使用 `cl-sys-` 前缀

4. **AC-4: 未就绪组件提供修复指引**
   - **Given** 某个组件检测为"未就绪"
   - **When** 用户查看该组件的状态行
   - **Then** 显示具体的修复指引文字（如 "请先启动 Docker Desktop"、"请执行 docker-compose up"）
   - **And** Docker 未启动时提供"请安装并启动 Docker Desktop"提示
   - **And** 后端未启动时提供"一键启动后端"按钮（执行 `docker-compose up -d`）
   - **And** 每个错误场景的修复指引都是具体可操作的

5. **AC-5: 全部就绪后引导创建首个白板**
   - **Given** 全部 5 个组件检测为"就绪"
   - **When** 检测完成
   - **Then** Modal 底部显示成功消息 "系统已准备好！"
   - **And** 显示"创建你的第一个白板"引导按钮
   - **And** 点击后关闭 Modal，将 `setupComplete` 标记为 `true` 存入插件 `data.json`
   - **And** 触发右侧面板 MainView 激活（为后续 Story 1.4 白板创建做准备）

6. **AC-6: 重新检测功能**
   - **Given** 向导已显示检测结果（部分或全部失败）
   - **When** 用户点击"重新检测"按钮
   - **Then** 所有组件状态重置为"检测中"并重新执行检测流程
   - **And** 不关闭 Modal

## Tasks / Subtasks

- [ ] **Task 1: 扩展插件设置数据类型** (AC: #1, #5)
  - [ ] 1.1 在 `main.ts`（或独立 `src/types/settings.d.ts`）中扩展 `CanvasLearningSettings` 接口，添加 `setupComplete: boolean` 字段，默认值 `false`
  - [ ] 1.2 在 `main.ts` 的 `onload()` 中读取 `this.loadData()` 判断 `setupComplete` 状态
  - [ ] 1.3 `setupComplete === false` 或首次安装时自动实例化 SetupWizardModal

- [ ] **Task 2: 创建 SetupWizardModal 类** (AC: #1, #2, #6)
  - [ ] 2.1 创建 `obsidian-canvas-learning/src/components/system/SetupWizardModal.ts`：继承 Obsidian `Modal`
  - [ ] 2.2 在 `onOpen()` 中使用 Svelte 5 `mount()` 将 `SetupWizard.svelte` 挂载到 `contentEl`
  - [ ] 2.3 在 `onClose()` 中使用 `unmount()` 清理 Svelte 组件
  - [ ] 2.4 向 Svelte 组件传递 props：`app`（Obsidian App 实例）、`onComplete` 回调、`apiClient`（API 服务实例）

- [ ] **Task 3: 创建 SetupWizard.svelte 组件** (AC: #2, #3, #4, #5, #6)
  - [ ] 3.1 创建 `obsidian-canvas-learning/src/components/system/SetupWizard.svelte`
  - [ ] 3.2 定义 5 个检测步骤的状态模型：
    ```typescript
    type CheckStatus = 'pending' | 'checking' | 'success' | 'error';
    interface ComponentCheck {
      id: string;           // 'docker' | 'backend' | 'neo4j' | 'llm' | 'lancedb'
      name: string;         // 显示名称
      status: CheckStatus;
      message: string;      // 状态描述或错误提示
      fixAction?: () => void;  // 修复操作（如一键启动）
      fixLabel?: string;    // 修复按钮文字
    }
    ```
  - [ ] 3.3 实现 `runAllChecks()` 方法：按顺序执行 5 步检测
  - [ ] 3.4 组件挂载后自动调用 `runAllChecks()`
  - [ ] 3.5 实现"重新检测"按钮逻辑

- [ ] **Task 4: 实现 5 步检测逻辑** (AC: #2)
  - [ ] 4.1 **Step 1 — Docker 检测**：通过 Node.js `child_process.exec` 执行 `docker info`，exit code 0 为成功；不可用时提示"请安装并启动 Docker Desktop"
  - [ ] 4.2 **Step 2 — 后端 API 检测**：调用 `api-client.checkHealth()` 即 `GET http://localhost:8001/api/v1/system/health`，200 为成功；不可达时提供"一键启动后端"按钮
  - [ ] 4.3 **Step 3 — Neo4j 检测**：从 Step 2 的健康检查响应中解析 `components` 数组，找到 `name === "neo4j"` 的组件状态；如果 Step 2 失败则也标记 Neo4j 未就绪
  - [ ] 4.4 **Step 4 — LLM API 检测**：从健康检查响应中解析 Ollama 组件状态（bge-m3 embedding 模型可用性）；未来 Story 1.3 将扩展为外部 LLM API Key 验证
  - [ ] 4.5 **Step 5 — LanceDB 检测**：从健康检查响应中解析 LanceDB 组件状态（数据目录存在且可写）

- [ ] **Task 5: 实现"一键启动后端"操作** (AC: #4)
  - [ ] 5.1 创建 `obsidian-canvas-learning/src/services/docker-service.ts`
  - [ ] 5.2 实现 `startBackend()` 方法：通过 Node.js `child_process.exec` 执行 `docker-compose -f <compose-path> up -d`
  - [ ] 5.3 compose 文件路径从插件配置或相对路径推断（`backend/docker-compose.yml` 或根目录 `docker-compose.yml`）
  - [ ] 5.4 启动后等待 5-10 秒再自动触发重新检测
  - [ ] 5.5 启动过程中按钮显示"启动中..."加载状态

- [ ] **Task 6: 注册命令面板命令** (AC: #1)
  - [ ] 6.1 在 `main.ts` 的 `onload()` 中注册 Obsidian Command：`canvas-learning:open-setup-wizard`，名称"Canvas: 打开安装引导"
  - [ ] 6.2 命令执行时实例化并打开 `SetupWizardModal`

- [ ] **Task 7: 编写组件样式** (AC: #3)
  - [ ] 7.1 在 `SetupWizard.svelte` 中使用 Svelte scoped CSS
  - [ ] 7.2 所有 CSS 类名使用 `cl-sys-` 前缀（如 `cl-sys-wizard`, `cl-sys-status-dot`, `cl-sys-check-row`）
  - [ ] 7.3 颜色使用 Obsidian CSS 变量：`--text-success` (绿色), `--text-error` (红色), `--text-muted` (灰色), `--background-modifier-border`, `--interactive-accent`
  - [ ] 7.4 验证 Light/Dark 主题下视觉效果

- [ ] **Task 8: 验证与测试** (AC: #1-#6)
  - [ ] 8.1 首次启用场景：清除插件 data → 重启 Obsidian → 验证 Modal 自动弹出
  - [ ] 8.2 全部就绪场景：Docker + docker-compose up → 打开向导 → 5 个绿灯
  - [ ] 8.3 部分失败场景：Docker 未启动 → 验证红灯 + 修复指引
  - [ ] 8.4 一键启动场景：后端未启动 → 点击"一键启动"按钮 → 验证自动重检
  - [ ] 8.5 重新检测场景：点击"重新检测" → 所有状态重置并重新检测
  - [ ] 8.6 命令面板场景：`Ctrl+P` → 输入"Canvas: 打开安装引导" → Modal 打开
  - [ ] 8.7 非首次启用场景：`setupComplete === true` → 验证不自动弹出
  - [ ] 8.8 运行 TypeScript 编译确认无错误

## Dev Notes

### Obsidian Modal API 用法

`SetupWizardModal` 继承 Obsidian `Modal` 类，核心 API：

```typescript
import { App, Modal } from 'obsidian';
import { mount, unmount } from 'svelte';
import SetupWizard from '../components/system/SetupWizard.svelte';

export class SetupWizardModal extends Modal {
    private svelteComponent: ReturnType<typeof mount> | null = null;

    constructor(
        app: App,
        private apiClient: ApiClient,
        private onSetupComplete: () => void
    ) {
        super(app);
    }

    onOpen() {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('cl-sys-wizard-modal');

        this.svelteComponent = mount(SetupWizard, {
            target: contentEl,
            props: {
                app: this.app,
                apiClient: this.apiClient,
                onComplete: () => {
                    this.onSetupComplete();
                    this.close();
                }
            }
        });
    }

    onClose() {
        if (this.svelteComponent) {
            unmount(this.svelteComponent);
            this.svelteComponent = null;
        }
        const { contentEl } = this;
        contentEl.empty();
    }
}
```

### Docker 检测实现（Electron/Node.js 环境）

Obsidian 运行在 Electron 中，可使用 Node.js `child_process` API：

```typescript
// src/services/docker-service.ts
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export class DockerService {
    async isDockerRunning(): Promise<boolean> {
        try {
            await execAsync('docker info');
            return true;
        } catch {
            return false;
        }
    }

    async startBackend(composePath: string): Promise<void> {
        await execAsync(`docker-compose -f "${composePath}" up -d`);
    }
}
```

### 后端健康检查响应格式

依赖 Story 1.1 的 `GET /api/v1/system/health` 端点返回格式：

```json
{
    "data": {
        "status": "healthy | degraded | unhealthy",
        "components": [
            {"name": "neo4j", "status": "healthy | unhealthy | unknown", "message": "..."},
            {"name": "ollama", "status": "healthy | unhealthy | unknown", "message": "..."},
            {"name": "lancedb", "status": "healthy | unhealthy | unknown", "message": "..."}
        ],
        "timestamp": "2026-03-17T12:00:00Z"
    },
    "meta": {"timestamp": "2026-03-17T12:00:00Z"}
}
```

向导从这个单一端点获取 Neo4j / Ollama(LLM) / LanceDB 三个组件的状态，避免前端直接连接后端内部服务。

### 5 步检测流程逻辑

```
Step 1: Docker Desktop → exec("docker info") → 成功/失败
    ↓ (通过后才检测后续步骤)
Step 2: 后端 API → GET :8001/health → 成功/失败
    ↓ (通过后从响应解析子组件状态)
Step 3: Neo4j → 从 Step 2 响应解析 → 成功/失败
Step 4: LLM (Ollama) → 从 Step 2 响应解析 → 成功/失败
Step 5: LanceDB → 从 Step 2 响应解析 → 成功/失败
```

Step 1 失败时，Step 2-5 自动标记为"未就绪"（Docker 是前提依赖）。
Step 2 失败时，Step 3-5 自动标记为"未就绪"（需要后端才能检测子组件）。

### FR 覆盖

| FR | 覆盖范围 | 说明 |
|----|---------|------|
| FR-SYS-01 | 完整覆盖 | 首次启用安装引导向导 |
| FR-SYS-04 | 部分覆盖 | 向导中的 5 组件状态灯（常驻健康面板在 Story 1.3 Settings Tab 中实现） |

### 依赖关系

- **依赖 Story 1.1**：需要 Docker Compose 配置、FastAPI 健康检查端点、前端插件骨架（`main.ts`, `api-client.ts`, `manifest.json`）、项目目录结构
- **被 Story 1.3 依赖**：Settings Tab 中的常驻系统健康面板复用本 Story 的检测逻辑

### 不做的事项（防蔓延）

- 不实现 Settings Tab / 模型配置（Story 1.3）
- 不实现 LLM API Key 配置和验证（Story 1.3，本 Story 仅检测 Ollama bge-m3 是否可用）
- 不实现 Canvas 白板渲染（Story 1.4）
- 不实现常驻健康面板（Story 1.3 Settings Tab 顶部区域）
- 不实现数据备份/恢复功能（Story 1.8）
- 不实现 WebSocket 连接
- "创建你的第一个白板"按钮点击后仅关闭 Modal + 标记 setupComplete + 激活 MainView，实际白板创建交互在 Story 1.4

### CSS 设计指引

```css
/* 状态灯样式参考 */
.cl-sys-status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
}
.cl-sys-status-dot--success {
    background-color: var(--text-success);
}
.cl-sys-status-dot--error {
    background-color: var(--text-error);
}
.cl-sys-status-dot--checking {
    /* 旋转动画 */
    border: 2px solid var(--text-muted);
    border-top-color: var(--interactive-accent);
    animation: cl-sys-spin 0.8s linear infinite;
}
.cl-sys-status-dot--pending {
    background-color: var(--text-muted);
}

@keyframes cl-sys-spin {
    to { transform: rotate(360deg); }
}

/* Modal 内容区 */
.cl-sys-wizard-modal {
    max-width: 480px;
}
.cl-sys-check-row {
    display: flex;
    align-items: center;
    gap: var(--size-4-2);
    padding: var(--size-4-2) 0;
    border-bottom: 1px solid var(--background-modifier-border);
}
```

### Project Structure Notes

- `SetupWizardModal.ts` 放在 `obsidian-canvas-learning/src/components/system/`（F 组系统管理组件）
- `SetupWizard.svelte` 放在同目录
- `docker-service.ts` 放在 `obsidian-canvas-learning/src/services/`
- 扩展 `src/types/api.d.ts` 中 `HealthResponse` 类型（Story 1.1 已创建基础定义）
- 扩展 `src/services/api-client.ts` 中已有的 `checkHealth()` 方法（返回完整响应而非仅 boolean）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#Technical Constraints & Dependencies] — Obsidian Plugin API（ItemView/Modal/Setting 原生 API）、组件启动顺序、首次引导 5 步检测链
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries] — `system/SetupWizard.svelte` 文件位置、`settings.ts` PluginSettingTab
- [Source: _bmad-output/planning-artifacts/architecture.md#Infrastructure & Deployment] — 8 步依赖链 + 5 步检测向导 + 健康面板
- [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns] — `GET /api/v1/system/health` 健康检查端点
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns] — CSS cl- 前缀、Svelte 5 mount/unmount、命名规范
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy] — F 组 SetupWizard 组件、Obsidian Modal 原生组件
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Settings Tab 布局] — 系统状态区域：5 个组件状态灯 + 重新检测按钮
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#User Journey Flows#旅程 4] — 新用户初次使用流程图
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#UX Consistency Patterns#模态框] — 最少使用模态框，仅安装引导和考察模式选择用

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
