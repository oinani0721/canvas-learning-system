---
document_type: "Architecture"
version: "1.0.0"
last_modified: "2025-11-23"
status: "draft"
iteration: 5

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

compatible_with:
  prd: "v1.1.8"
  epic: ["Epic 13", "Epic 15", "Epic 17"]

changes_from_previous:
  - "Initial Obsidian Plugin Architecture document"
---

# Obsidian Plugin Architecture

**版本**: v1.0.0
**创建日期**: 2025-11-23
**架构师**: Architect Agent

---

## 1. 概述

本文档定义Canvas Learning System作为Obsidian原生插件的架构设计，确保与Obsidian API的正确集成。

### 1.1 设计目标

- 完全原生Obsidian插件，无外部依赖
- 遵循Obsidian Plugin API最佳实践
- 支持Canvas JSON格式操作
- 与FastAPI后端WebSocket通信

---

## 2. 插件核心结构

### 2.1 主插件类

```typescript
// ✅ Verified from Obsidian Canvas Skill (SKILL.md - Section: Plugin Development)
import { Plugin, WorkspaceLeaf, TFile } from 'obsidian';

export default class CanvasLearningPlugin extends Plugin {
    settings: CanvasLearningSettings;

    async onload() {
        // 加载设置
        await this.loadSettings();

        // 注册命令
        this.addCommand({
            id: 'analyze-canvas-node',
            name: 'Analyze Selected Canvas Node',
            callback: () => this.analyzeSelectedNode()
        });

        // 注册Canvas事件监听
        this.registerEvent(
            this.app.workspace.on('canvas:node-menu', (menu, node) => {
                this.addNodeMenuItems(menu, node);
            })
        );

        // 添加设置面板
        this.addSettingTab(new CanvasLearningSettingTab(this.app, this));
    }

    async onunload() {
        // 清理资源
    }
}
```

### 2.2 设置管理

```typescript
// ✅ Verified from Obsidian Canvas Skill (SKILL.md - Section: Settings Pattern)
interface CanvasLearningSettings {
    backendUrl: string;
    autoAnalyze: boolean;
    colorScheme: 'default' | 'custom';
    reviewInterval: number;
}

const DEFAULT_SETTINGS: CanvasLearningSettings = {
    backendUrl: 'ws://localhost:8000/ws',
    autoAnalyze: false,
    colorScheme: 'default',
    reviewInterval: 24
};

async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
}

async saveSettings() {
    await this.saveData(this.settings);
}
```

---

## 3. Canvas操作层

### 3.1 Canvas文件读写

```typescript
// ✅ Verified from Obsidian Canvas Skill (SKILL.md - Section: Canvas JSON Operations)
interface CanvasData {
    nodes: CanvasNode[];
    edges: CanvasEdge[];
}

interface CanvasNode {
    id: string;
    type: 'text' | 'file' | 'link' | 'group';
    x: number;
    y: number;
    width: number;
    height: number;
    text?: string;
    color?: string;  // "1"-"6" for presets, or hex
}

interface CanvasEdge {
    id: string;
    fromNode: string;
    toNode: string;
    fromSide: 'top' | 'right' | 'bottom' | 'left';
    toSide: 'top' | 'right' | 'bottom' | 'left';
}

class CanvasOperator {
    constructor(private app: App) {}

    // ✅ Verified from Obsidian Canvas Skill
    async readCanvas(file: TFile): Promise<CanvasData> {
        const content = await this.app.vault.read(file);
        return JSON.parse(content);
    }

    // ✅ Verified from Obsidian Canvas Skill
    async writeCanvas(file: TFile, data: CanvasData): Promise<void> {
        await this.app.vault.modify(file, JSON.stringify(data, null, 2));
    }

    // ✅ Verified from Obsidian Canvas Skill
    async addNodes(file: TFile, newNodes: CanvasNode[]): Promise<void> {
        const data = await this.readCanvas(file);
        data.nodes.push(...newNodes);
        await this.writeCanvas(file, data);
    }
}
```

### 3.2 颜色系统映射

```typescript
// ✅ Verified from Obsidian Canvas Skill (SKILL.md - Section: Color System)
// Canvas预设颜色: "1"=红, "2"=橙, "3"=黄, "4"=绿, "5"=青, "6"=紫

const COLOR_MAP = {
    RED: "1",      // 未理解
    ORANGE: "2",   // 部分理解
    YELLOW: "3",   // 待评分
    GREEN: "4",    // 已掌握
    CYAN: "5",     // 检验中
    PURPLE: "6"    // 深入理解
};

function getNodeColor(status: string): string {
    switch (status) {
        case 'not_understood': return COLOR_MAP.RED;
        case 'partial': return COLOR_MAP.ORANGE;
        case 'pending_score': return COLOR_MAP.YELLOW;
        case 'mastered': return COLOR_MAP.GREEN;
        case 'verifying': return COLOR_MAP.CYAN;
        case 'deep_understanding': return COLOR_MAP.PURPLE;
        default: return COLOR_MAP.YELLOW;
    }
}
```

---

## 4. 视图层架构

### 4.1 自定义视图

```typescript
// ✅ Verified from Obsidian Canvas Skill (SKILL.md - Section: Custom Views)
import { ItemView, WorkspaceLeaf } from 'obsidian';

export const VIEW_TYPE_LEARNING_PANEL = 'canvas-learning-panel';

export class LearningPanelView extends ItemView {
    constructor(leaf: WorkspaceLeaf) {
        super(leaf);
    }

    getViewType(): string {
        return VIEW_TYPE_LEARNING_PANEL;
    }

    getDisplayText(): string {
        return 'Canvas Learning Panel';
    }

    async onOpen() {
        const container = this.containerEl.children[1];
        container.empty();
        container.createEl('h4', { text: 'Learning Progress' });
        // 渲染UI组件
    }

    async onClose() {
        // 清理
    }
}
```

### 4.2 模态框

```typescript
// ✅ Verified from Obsidian Canvas Skill (SKILL.md - Section: Modals)
import { Modal, App } from 'obsidian';

export class AnalysisResultModal extends Modal {
    result: AnalysisResult;

    constructor(app: App, result: AnalysisResult) {
        super(app);
        this.result = result;
    }

    onOpen() {
        const { contentEl } = this;
        contentEl.createEl('h2', { text: 'Analysis Result' });
        contentEl.createEl('p', { text: this.result.summary });

        // 渲染评分
        const scoreEl = contentEl.createDiv('score-container');
        scoreEl.createEl('span', { text: `Score: ${this.result.score}/100` });
    }

    onClose() {
        this.contentEl.empty();
    }
}
```

---

## 5. 事件系统

### 5.1 Canvas事件监听

```typescript
// ✅ Verified from Obsidian Canvas Skill (SKILL.md - Section: Events)
// 注册Canvas节点右键菜单
this.registerEvent(
    this.app.workspace.on('canvas:node-menu', (menu, node) => {
        menu.addItem((item) => {
            item.setTitle('Analyze Node')
                .setIcon('search')
                .onClick(() => this.analyzeNode(node));
        });

        menu.addItem((item) => {
            item.setTitle('Generate Questions')
                .setIcon('help-circle')
                .onClick(() => this.generateQuestions(node));
        });
    })
);

// 监听Canvas选择变化
this.registerEvent(
    this.app.workspace.on('canvas:selection-menu', (menu, canvas) => {
        const selectedNodes = canvas.selection;
        if (selectedNodes.size > 1) {
            menu.addItem((item) => {
                item.setTitle('Batch Analyze')
                    .onClick(() => this.batchAnalyze(selectedNodes));
            });
        }
    })
);
```

### 5.2 文件事件

```typescript
// ✅ Verified from Obsidian Canvas Skill (SKILL.md - Section: File Events)
// 监听Canvas文件修改
this.registerEvent(
    this.app.vault.on('modify', (file) => {
        if (file.extension === 'canvas') {
            this.onCanvasModified(file as TFile);
        }
    })
);

// 监听文件创建
this.registerEvent(
    this.app.vault.on('create', (file) => {
        if (file instanceof TFile && file.extension === 'canvas') {
            this.onCanvasCreated(file);
        }
    })
);
```

---

## 6. 后端通信层

### 6.1 WebSocket客户端

```typescript
// ✅ Verified from FastAPI WebSocket Context7 documentation
class WebSocketClient {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;

    constructor(private url: string) {}

    connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                this.reconnectAttempts = 0;
                resolve();
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };

            this.ws.onclose = () => {
                this.handleDisconnect();
            };

            this.ws.onerror = (error) => {
                reject(error);
            };
        });
    }

    send(message: object): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    private handleDisconnect(): void {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => this.connect(), 1000 * this.reconnectAttempts);
        }
    }
}
```

### 6.2 API通信接口

```typescript
interface AnalysisRequest {
    nodeId: string;
    content: string;
    context: string[];
    analysisType: 'decompose' | 'explain' | 'score' | 'verify';
}

interface AnalysisResponse {
    nodeId: string;
    result: any;
    newNodes?: CanvasNode[];
    newEdges?: CanvasEdge[];
    colorUpdate?: string;
}

async function requestAnalysis(request: AnalysisRequest): Promise<AnalysisResponse> {
    return new Promise((resolve) => {
        wsClient.send({
            type: 'analysis_request',
            payload: request
        });

        // 通过事件系统接收响应
        eventEmitter.once(`analysis_response_${request.nodeId}`, resolve);
    });
}
```

---

## 7. 命令注册

### 7.1 全局命令

```typescript
// ✅ Verified from Obsidian Canvas Skill (SKILL.md - Section: Commands)
// 分析当前Canvas
this.addCommand({
    id: 'analyze-current-canvas',
    name: 'Analyze Current Canvas',
    checkCallback: (checking: boolean) => {
        const canvasView = this.app.workspace.getActiveViewOfType(ItemView);
        if (canvasView?.getViewType() === 'canvas') {
            if (!checking) {
                this.analyzeCanvas(canvasView);
            }
            return true;
        }
        return false;
    }
});

// 生成复习计划
this.addCommand({
    id: 'generate-review-schedule',
    name: 'Generate Ebbinghaus Review Schedule',
    callback: () => this.generateReviewSchedule()
});

// 打开学习面板
this.addCommand({
    id: 'open-learning-panel',
    name: 'Open Learning Panel',
    callback: () => {
        this.app.workspace.getRightLeaf(false).setViewState({
            type: VIEW_TYPE_LEARNING_PANEL
        });
    }
});
```

---

## 8. 目录结构

```
canvas-learning-plugin/
├── src/
│   ├── main.ts                    # 插件入口
│   ├── settings.ts                # 设置管理
│   ├── canvas/
│   │   ├── operator.ts            # Canvas JSON操作
│   │   ├── colors.ts              # 颜色系统
│   │   └── types.ts               # Canvas类型定义
│   ├── views/
│   │   ├── LearningPanel.ts       # 学习面板视图
│   │   └── AnalysisModal.ts       # 分析结果模态框
│   ├── services/
│   │   ├── WebSocketClient.ts     # WebSocket通信
│   │   └── AnalysisService.ts     # 分析服务
│   └── commands/
│       └── index.ts               # 命令注册
├── styles.css                     # 样式
├── manifest.json                  # 插件清单
└── package.json
```

---

## 9. 构建配置

### 9.1 manifest.json

```json
{
    "id": "canvas-learning-system",
    "name": "Canvas Learning System",
    "version": "1.0.0",
    "minAppVersion": "1.4.0",
    "description": "AI-assisted learning system using Feynman method",
    "author": "Canvas Learning Team",
    "isDesktopOnly": false
}
```

### 9.2 构建脚本

```json
{
    "scripts": {
        "dev": "node esbuild.config.mjs",
        "build": "tsc -noEmit -skipLibCheck && node esbuild.config.mjs production"
    }
}
```

---

## 10. 技术约束

### 10.1 Obsidian API限制

- 必须使用`this.app.vault`进行文件操作
- Canvas事件通过workspace事件系统
- 不能直接操作DOM，需使用Obsidian组件API

### 10.2 性能考虑

- Canvas文件可能很大，需要增量更新
- WebSocket消息需要队列管理
- 避免阻塞主线程

---

## 11. 相关文档

- [Canvas 3层架构](canvas-3-layer-architecture.md)
- [UI组件架构](ui-component-architecture.md)
- [WebSocket实时架构](websocket-realtime-architecture.md)

---

**文档版本**: v1.0.0
**最后更新**: 2025-11-23
**维护者**: Architect Agent
