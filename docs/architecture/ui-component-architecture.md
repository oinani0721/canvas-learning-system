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
  epic: ["Epic 13", "Epic 14", "Epic 15"]

changes_from_previous:
  - "Initial UI Component Architecture document"
---

# UI组件架构

**版本**: v1.0.0
**创建日期**: 2025-11-23
**架构师**: Architect Agent

---

## 1. 概述

本文档定义Canvas Learning System的UI组件架构，包括Obsidian原生组件和TypeScript组件模式。

### 1.1 设计原则

- 基于Obsidian原生API构建
- TypeScript类型安全
- 组件化和可复用性
- 响应式状态管理

---

## 2. 组件层次结构

```
┌─────────────────────────────────────────────────────────┐
│                    UI组件架构                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Application Layer                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ LearningPanel│  │ ReviewPanel │  │ ProgressView│     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │             │
│  Component Layer                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ NodeCard    │  │ ScoreChart  │  │ StatusBadge │     │
│  │ AgentList   │  │ Timeline    │  │ ColorPicker │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │             │
│  Primitive Layer (Obsidian API)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ ItemView    │  │ Modal       │  │ Setting     │     │
│  │ Component   │  │ Menu        │  │ Notice      │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 状态管理

### 3.1 状态类型定义

```typescript
// ✅ Verified from TypeScript Cheatsheets React (patterns_by_usecase.md)
interface UIState {
    currentCanvas: string | null;
    selectedNodes: string[];
    analysisResults: Map<string, AnalysisResult>;
    reviewSchedule: ReviewItem[];
    isLoading: boolean;
    error: string | null;
}

interface AnalysisResult {
    nodeId: string;
    score: number;
    feedback: string;
    dimensions: ScoreDimensions;
    timestamp: Date;
}

interface ScoreDimensions {
    accuracy: number;      // 准确性
    imagery: number;       // 形象性
    completeness: number;  // 完整性
    originality: number;   // 原创性
}
```

### 3.2 状态管理器

```typescript
// ✅ Verified from TypeScript Cheatsheets React (useState hook patterns)
type StateListener<T> = (state: T) => void;

class StateManager<T extends object> {
    private state: T;
    private listeners: Set<StateListener<T>> = new Set();

    constructor(initialState: T) {
        this.state = initialState;
    }

    getState(): Readonly<T> {
        return this.state;
    }

    setState(partial: Partial<T>): void {
        this.state = { ...this.state, ...partial };
        this.notifyListeners();
    }

    subscribe(listener: StateListener<T>): () => void {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    private notifyListeners(): void {
        this.listeners.forEach(listener => listener(this.state));
    }
}

// 全局状态实例
const uiState = new StateManager<UIState>({
    currentCanvas: null,
    selectedNodes: [],
    analysisResults: new Map(),
    reviewSchedule: [],
    isLoading: false,
    error: null
});
```

---

## 4. 核心视图组件

### 4.1 学习面板视图

```typescript
// ✅ Verified from Obsidian Canvas Skill (SKILL.md - Section: Custom Views)
import { ItemView, WorkspaceLeaf } from 'obsidian';

export const VIEW_TYPE_LEARNING_PANEL = 'canvas-learning-panel';

export class LearningPanelView extends ItemView {
    private state: StateManager<UIState>;
    private unsubscribe: (() => void) | null = null;

    constructor(leaf: WorkspaceLeaf, state: StateManager<UIState>) {
        super(leaf);
        this.state = state;
    }

    getViewType(): string {
        return VIEW_TYPE_LEARNING_PANEL;
    }

    getDisplayText(): string {
        return 'Canvas Learning';
    }

    getIcon(): string {
        return 'graduation-cap';
    }

    async onOpen(): Promise<void> {
        const container = this.containerEl.children[1];
        container.empty();
        container.addClass('canvas-learning-panel');

        // 订阅状态变化
        this.unsubscribe = this.state.subscribe(state => {
            this.render(container, state);
        });

        // 初始渲染
        this.render(container, this.state.getState());
    }

    async onClose(): Promise<void> {
        if (this.unsubscribe) {
            this.unsubscribe();
        }
    }

    private render(container: Element, state: UIState): void {
        container.empty();

        // 头部
        this.renderHeader(container, state);

        // 当前Canvas信息
        if (state.currentCanvas) {
            this.renderCanvasInfo(container, state);
        }

        // 选中节点列表
        if (state.selectedNodes.length > 0) {
            this.renderSelectedNodes(container, state);
        }

        // 复习计划
        this.renderReviewSchedule(container, state);
    }

    private renderHeader(container: Element, state: UIState): void {
        const header = container.createDiv('panel-header');
        header.createEl('h3', { text: 'Canvas Learning System' });

        if (state.isLoading) {
            header.createSpan({ cls: 'loading-indicator', text: '分析中...' });
        }
    }

    private renderCanvasInfo(container: Element, state: UIState): void {
        const info = container.createDiv('canvas-info');
        info.createEl('h4', { text: '当前Canvas' });
        info.createEl('p', { text: state.currentCanvas! });
    }

    private renderSelectedNodes(container: Element, state: UIState): void {
        const section = container.createDiv('selected-nodes');
        section.createEl('h4', { text: `选中节点 (${state.selectedNodes.length})` });

        const list = section.createEl('ul');
        state.selectedNodes.forEach(nodeId => {
            const item = list.createEl('li');
            item.createSpan({ text: nodeId });

            // 分析按钮
            const btn = item.createEl('button', { text: '分析' });
            btn.onclick = () => this.analyzeNode(nodeId);
        });
    }

    private renderReviewSchedule(container: Element, state: UIState): void {
        const section = container.createDiv('review-schedule');
        section.createEl('h4', { text: '复习计划' });

        if (state.reviewSchedule.length === 0) {
            section.createEl('p', { text: '暂无待复习项目' });
            return;
        }

        const list = section.createEl('ul');
        state.reviewSchedule.forEach(item => {
            const li = list.createEl('li');
            li.createSpan({ text: item.content });
            li.createSpan({
                cls: 'due-date',
                text: item.dueDate.toLocaleDateString()
            });
        });
    }

    private analyzeNode(nodeId: string): void {
        // 触发分析
    }
}
```

### 4.2 分析结果模态框

```typescript
// ✅ Verified from Obsidian Canvas Skill (SKILL.md - Section: Modals)
import { Modal, App } from 'obsidian';

export class AnalysisResultModal extends Modal {
    private result: AnalysisResult;

    constructor(app: App, result: AnalysisResult) {
        super(app);
        this.result = result;
    }

    onOpen(): void {
        const { contentEl } = this;
        contentEl.addClass('analysis-result-modal');

        // 标题
        contentEl.createEl('h2', { text: '分析结果' });

        // 总分
        const scoreSection = contentEl.createDiv('score-section');
        scoreSection.createEl('span', {
            cls: 'total-score',
            text: `${this.result.score}/100`
        });
        scoreSection.createEl('span', {
            cls: this.getScoreClass(this.result.score),
            text: this.getScoreLabel(this.result.score)
        });

        // 四维评分
        this.renderDimensions(contentEl);

        // 反馈
        const feedback = contentEl.createDiv('feedback-section');
        feedback.createEl('h3', { text: '详细反馈' });
        feedback.createEl('p', { text: this.result.feedback });

        // 关闭按钮
        const btnContainer = contentEl.createDiv('button-container');
        const closeBtn = btnContainer.createEl('button', { text: '关闭' });
        closeBtn.onclick = () => this.close();
    }

    private renderDimensions(container: Element): void {
        const section = container.createDiv('dimensions-section');
        section.createEl('h3', { text: '四维评分' });

        const dimensions = [
            { name: '准确性', value: this.result.dimensions.accuracy },
            { name: '形象性', value: this.result.dimensions.imagery },
            { name: '完整性', value: this.result.dimensions.completeness },
            { name: '原创性', value: this.result.dimensions.originality }
        ];

        dimensions.forEach(dim => {
            const row = section.createDiv('dimension-row');
            row.createSpan({ text: dim.name });

            const bar = row.createDiv('progress-bar');
            const fill = bar.createDiv('progress-fill');
            fill.style.width = `${dim.value}%`;

            row.createSpan({ text: `${dim.value}%` });
        });
    }

    private getScoreClass(score: number): string {
        if (score >= 80) return 'score-excellent';
        if (score >= 60) return 'score-good';
        if (score >= 40) return 'score-fair';
        return 'score-poor';
    }

    private getScoreLabel(score: number): string {
        if (score >= 80) return '优秀';
        if (score >= 60) return '良好';
        if (score >= 40) return '及格';
        return '需改进';
    }

    onClose(): void {
        this.contentEl.empty();
    }
}
```

---

## 5. 可复用组件

### 5.1 节点卡片组件

```typescript
// ✅ Based on TypeScript Cheatsheets React (component patterns)
interface NodeCardProps {
    nodeId: string;
    content: string;
    color: string;
    score?: number;
    onAnalyze?: (nodeId: string) => void;
    onSelect?: (nodeId: string) => void;
}

class NodeCard {
    private props: NodeCardProps;
    private element: HTMLElement;

    constructor(container: HTMLElement, props: NodeCardProps) {
        this.props = props;
        this.element = container.createDiv('node-card');
        this.render();
    }

    private render(): void {
        this.element.empty();
        this.element.addClass(`color-${this.props.color}`);

        // 头部
        const header = this.element.createDiv('card-header');
        header.createSpan({ cls: 'node-id', text: this.props.nodeId });

        if (this.props.score !== undefined) {
            header.createSpan({
                cls: 'score-badge',
                text: `${this.props.score}分`
            });
        }

        // 内容
        const content = this.element.createDiv('card-content');
        content.createEl('p', { text: this.props.content });

        // 操作按钮
        const actions = this.element.createDiv('card-actions');

        if (this.props.onAnalyze) {
            const analyzeBtn = actions.createEl('button', { text: '分析' });
            analyzeBtn.onclick = () => this.props.onAnalyze!(this.props.nodeId);
        }

        if (this.props.onSelect) {
            const selectBtn = actions.createEl('button', { text: '选择' });
            selectBtn.onclick = () => this.props.onSelect!(this.props.nodeId);
        }
    }

    update(newProps: Partial<NodeCardProps>): void {
        this.props = { ...this.props, ...newProps };
        this.render();
    }

    destroy(): void {
        this.element.remove();
    }
}
```

### 5.2 评分图表组件

```typescript
interface ScoreChartProps {
    dimensions: ScoreDimensions;
    size?: number;
}

class ScoreChart {
    private props: ScoreChartProps;
    private canvas: HTMLCanvasElement;
    private ctx: CanvasRenderingContext2D;

    constructor(container: HTMLElement, props: ScoreChartProps) {
        this.props = { size: 200, ...props };
        this.canvas = container.createEl('canvas') as HTMLCanvasElement;
        this.canvas.width = this.props.size!;
        this.canvas.height = this.props.size!;
        this.ctx = this.canvas.getContext('2d')!;
        this.render();
    }

    private render(): void {
        const { dimensions } = this.props;
        const size = this.props.size!;
        const center = size / 2;
        const radius = size * 0.4;

        // 清空画布
        this.ctx.clearRect(0, 0, size, size);

        // 绘制雷达图背景
        this.drawBackground(center, radius);

        // 绘制数据
        this.drawData(center, radius, dimensions);

        // 绘制标签
        this.drawLabels(center, radius);
    }

    private drawBackground(center: number, radius: number): void {
        const angles = [0, Math.PI/2, Math.PI, Math.PI*3/2];

        this.ctx.strokeStyle = '#e0e0e0';
        this.ctx.lineWidth = 1;

        // 绘制同心圆
        [0.25, 0.5, 0.75, 1].forEach(scale => {
            this.ctx.beginPath();
            this.ctx.arc(center, center, radius * scale, 0, Math.PI * 2);
            this.ctx.stroke();
        });

        // 绘制轴线
        angles.forEach(angle => {
            this.ctx.beginPath();
            this.ctx.moveTo(center, center);
            this.ctx.lineTo(
                center + Math.cos(angle) * radius,
                center + Math.sin(angle) * radius
            );
            this.ctx.stroke();
        });
    }

    private drawData(center: number, radius: number, dims: ScoreDimensions): void {
        const values = [
            dims.accuracy / 100,
            dims.imagery / 100,
            dims.completeness / 100,
            dims.originality / 100
        ];
        const angles = [0, Math.PI/2, Math.PI, Math.PI*3/2];

        this.ctx.fillStyle = 'rgba(75, 192, 192, 0.5)';
        this.ctx.strokeStyle = 'rgb(75, 192, 192)';
        this.ctx.lineWidth = 2;

        this.ctx.beginPath();
        values.forEach((value, i) => {
            const x = center + Math.cos(angles[i]) * radius * value;
            const y = center + Math.sin(angles[i]) * radius * value;
            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        });
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.stroke();
    }

    private drawLabels(center: number, radius: number): void {
        const labels = ['准确性', '形象性', '完整性', '原创性'];
        const angles = [0, Math.PI/2, Math.PI, Math.PI*3/2];

        this.ctx.fillStyle = '#333';
        this.ctx.font = '12px sans-serif';
        this.ctx.textAlign = 'center';

        labels.forEach((label, i) => {
            const x = center + Math.cos(angles[i]) * (radius + 20);
            const y = center + Math.sin(angles[i]) * (radius + 20);
            this.ctx.fillText(label, x, y);
        });
    }

    update(dimensions: ScoreDimensions): void {
        this.props.dimensions = dimensions;
        this.render();
    }
}
```

### 5.3 状态徽章组件

```typescript
type BadgeStatus = 'success' | 'warning' | 'error' | 'info' | 'pending';

interface StatusBadgeProps {
    status: BadgeStatus;
    text: string;
    icon?: string;
}

class StatusBadge {
    private element: HTMLElement;

    constructor(container: HTMLElement, props: StatusBadgeProps) {
        this.element = container.createSpan({
            cls: `status-badge status-${props.status}`
        });

        if (props.icon) {
            this.element.createSpan({ cls: `icon-${props.icon}` });
        }

        this.element.createSpan({ text: props.text });
    }

    static createFromColor(container: HTMLElement, color: string): StatusBadge {
        const colorMap: Record<string, { status: BadgeStatus; text: string }> = {
            '1': { status: 'error', text: '未理解' },
            '2': { status: 'warning', text: '部分理解' },
            '3': { status: 'pending', text: '待评分' },
            '4': { status: 'success', text: '已掌握' },
            '5': { status: 'info', text: '检验中' },
            '6': { status: 'info', text: '深入理解' }
        };

        const config = colorMap[color] || { status: 'info', text: '未知' };
        return new StatusBadge(container, config);
    }
}
```

---

## 6. Agent列表组件

### 6.1 Agent选择器

```typescript
interface AgentInfo {
    id: string;
    name: string;
    description: string;
    icon: string;
    category: 'decompose' | 'explain' | 'score' | 'verify';
}

const AGENTS: AgentInfo[] = [
    { id: 'basic-decomposition', name: '基础拆解', description: '将复杂概念拆解为基础问题', icon: 'scissors', category: 'decompose' },
    { id: 'deep-decomposition', name: '深度拆解', description: '揭示理解盲点', icon: 'search', category: 'decompose' },
    { id: 'question-decomposition', name: '问题拆解', description: '生成突破性问题', icon: 'help-circle', category: 'decompose' },
    { id: 'oral-explanation', name: '口语化解释', description: '教授风格的口语解释', icon: 'message-circle', category: 'explain' },
    { id: 'four-level-explanation', name: '四层次解释', description: '从入门到创新的递进解释', icon: 'layers', category: 'explain' },
    { id: 'clarification-path', name: '澄清路径', description: '系统性澄清文档', icon: 'map', category: 'explain' },
    { id: 'comparison-table', name: '对比表', description: '结构化概念对比', icon: 'table', category: 'explain' },
    { id: 'example-teaching', name: '例题教学', description: '完整例题解答', icon: 'book-open', category: 'explain' },
    { id: 'memory-anchor', name: '记忆锚点', description: '生动类比和助记', icon: 'anchor', category: 'explain' },
    { id: 'scoring-agent', name: '评分Agent', description: '四维评分系统', icon: 'star', category: 'score' },
    { id: 'verification-question', name: '检验问题', description: '生成深度检验问题', icon: 'check-circle', category: 'verify' }
];

class AgentSelector {
    private container: HTMLElement;
    private selectedAgent: string | null = null;
    private onSelect: (agentId: string) => void;

    constructor(
        container: HTMLElement,
        onSelect: (agentId: string) => void
    ) {
        this.container = container;
        this.onSelect = onSelect;
        this.render();
    }

    private render(): void {
        this.container.empty();
        this.container.addClass('agent-selector');

        // 按类别分组
        const categories: Record<string, AgentInfo[]> = {
            decompose: [],
            explain: [],
            score: [],
            verify: []
        };

        AGENTS.forEach(agent => {
            categories[agent.category].push(agent);
        });

        // 渲染每个类别
        const categoryNames: Record<string, string> = {
            decompose: '拆解系列',
            explain: '解释系列',
            score: '评分',
            verify: '检验'
        };

        Object.entries(categories).forEach(([category, agents]) => {
            if (agents.length === 0) return;

            const section = this.container.createDiv('agent-category');
            section.createEl('h4', { text: categoryNames[category] });

            const grid = section.createDiv('agent-grid');
            agents.forEach(agent => {
                this.renderAgentCard(grid, agent);
            });
        });
    }

    private renderAgentCard(container: HTMLElement, agent: AgentInfo): void {
        const card = container.createDiv({
            cls: `agent-card ${this.selectedAgent === agent.id ? 'selected' : ''}`
        });

        card.createSpan({ cls: `icon-${agent.icon}` });
        card.createEl('strong', { text: agent.name });
        card.createEl('small', { text: agent.description });

        card.onclick = () => {
            this.selectedAgent = agent.id;
            this.onSelect(agent.id);
            this.render();
        };
    }
}
```

---

## 7. 样式系统

### 7.1 CSS变量

```css
/* styles.css */
.canvas-learning-panel {
    --cl-primary: #7c3aed;
    --cl-success: #10b981;
    --cl-warning: #f59e0b;
    --cl-error: #ef4444;
    --cl-info: #3b82f6;

    --cl-bg-primary: #ffffff;
    --cl-bg-secondary: #f3f4f6;
    --cl-text-primary: #111827;
    --cl-text-secondary: #6b7280;

    --cl-border-radius: 8px;
    --cl-spacing: 16px;
}

.theme-dark .canvas-learning-panel {
    --cl-bg-primary: #1f2937;
    --cl-bg-secondary: #374151;
    --cl-text-primary: #f9fafb;
    --cl-text-secondary: #9ca3af;
}
```

### 7.2 组件样式

```css
/* 节点卡片 */
.node-card {
    background: var(--cl-bg-primary);
    border-radius: var(--cl-border-radius);
    padding: var(--cl-spacing);
    margin-bottom: var(--cl-spacing);
    border-left: 4px solid transparent;
}

.node-card.color-1 { border-left-color: var(--cl-error); }
.node-card.color-2 { border-left-color: var(--cl-warning); }
.node-card.color-3 { border-left-color: #fcd34d; }
.node-card.color-4 { border-left-color: var(--cl-success); }
.node-card.color-5 { border-left-color: var(--cl-info); }
.node-card.color-6 { border-left-color: var(--cl-primary); }

/* 状态徽章 */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 12px;
}

.status-success { background: #d1fae5; color: #065f46; }
.status-warning { background: #fef3c7; color: #92400e; }
.status-error { background: #fee2e2; color: #991b1b; }
.status-info { background: #dbeafe; color: #1e40af; }
.status-pending { background: #fef9c3; color: #713f12; }

/* Agent选择器 */
.agent-selector {
    padding: var(--cl-spacing);
}

.agent-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 8px;
}

.agent-card {
    padding: 12px;
    border-radius: var(--cl-border-radius);
    background: var(--cl-bg-secondary);
    cursor: pointer;
    transition: all 0.2s;
}

.agent-card:hover {
    background: var(--cl-primary);
    color: white;
}

.agent-card.selected {
    background: var(--cl-primary);
    color: white;
}
```

---

## 8. 事件总线

### 8.1 事件类型

```typescript
// ✅ Based on TypeScript Cheatsheets (template literal types)
type UIEventType =
    | 'node:selected'
    | 'node:analyzed'
    | 'canvas:loaded'
    | 'review:scheduled'
    | 'agent:invoked';

interface UIEventPayloads {
    'node:selected': { nodeIds: string[] };
    'node:analyzed': { nodeId: string; result: AnalysisResult };
    'canvas:loaded': { filePath: string };
    'review:scheduled': { items: ReviewItem[] };
    'agent:invoked': { agentId: string; nodeId: string };
}

type UIEventHandler<T extends UIEventType> = (payload: UIEventPayloads[T]) => void;
```

### 8.2 事件总线实现

```typescript
class UIEventBus {
    private handlers: Map<UIEventType, Set<Function>> = new Map();

    on<T extends UIEventType>(
        event: T,
        handler: UIEventHandler<T>
    ): () => void {
        if (!this.handlers.has(event)) {
            this.handlers.set(event, new Set());
        }
        this.handlers.get(event)!.add(handler);

        return () => {
            this.handlers.get(event)?.delete(handler);
        };
    }

    emit<T extends UIEventType>(
        event: T,
        payload: UIEventPayloads[T]
    ): void {
        this.handlers.get(event)?.forEach(handler => {
            handler(payload);
        });
    }

    off<T extends UIEventType>(
        event: T,
        handler: UIEventHandler<T>
    ): void {
        this.handlers.get(event)?.delete(handler);
    }
}

// 全局事件总线
export const uiEventBus = new UIEventBus();
```

---

## 9. 目录结构

```
src/ui/
├── views/
│   ├── LearningPanelView.ts
│   ├── ReviewPanelView.ts
│   └── ProgressView.ts
├── modals/
│   ├── AnalysisResultModal.ts
│   ├── AgentSelectorModal.ts
│   └── ReviewSettingsModal.ts
├── components/
│   ├── NodeCard.ts
│   ├── ScoreChart.ts
│   ├── StatusBadge.ts
│   ├── AgentSelector.ts
│   └── Timeline.ts
├── state/
│   ├── StateManager.ts
│   └── UIState.ts
├── events/
│   └── UIEventBus.ts
└── styles/
    ├── variables.css
    ├── components.css
    └── views.css
```

---

## 10. 相关文档

- [Obsidian插件架构](obsidian-plugin-architecture.md)
- [WebSocket实时架构](websocket-realtime-architecture.md)
- [Epic 13 UI集成](../prd/epic-13-ui-integration.md)

---

**文档版本**: v1.0.0
**最后更新**: 2025-11-23
**维护者**: Architect Agent
