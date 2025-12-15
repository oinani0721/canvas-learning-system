# Epic 21.5.2: Context传递机制修复 - Canvas右键菜单上下文缓存

> **状态**: 🔴 In Progress
> **类型**: Brownfield Enhancement (Bug Fix)
> **优先级**: P0 - Critical (所有Agent功能仍阻塞)
> **预计Stories**: 3个
> **创建日期**: 2025-12-14
> **前置Epic**: Epic 21.5.1 (已完成，但Bug未解决)

---

## Epic Goal

修复Canvas右键菜单context传递机制，确保Agent API调用收到正确的`canvas_name`参数。

**核心问题**: Epic 21.5.1的`extractCanvasFileName()`修复已部署，但API仍收到错误的文件路径，因为**问题根源不在提取器，而在context来源**。

---

## Epic Description

### Existing System Context

- **当前功能**: Canvas Learning System通过Obsidian插件右键菜单调用14个AI Agent
- **技术栈**:
  - 前端: TypeScript (Obsidian Plugin)
  - 后端: Python 3.9+ / FastAPI
- **已完成修复**: Epic 21.5.1 添加了`extractCanvasFileName()`从路径提取文件名
- **问题现象**: 修复部署后，错误仍然存在

### 深度调研发现

#### 调研验证结果

| 检查项 | 结果 | 说明 |
|--------|------|------|
| Epic 21.5.1 部署 | ✅ 已部署 | main.js 时间戳同步 |
| extractCanvasFileName 存在 | ✅ 存在 | 14处匹配 |
| 后端验证规则 | ✅ 合理 | 允许单斜杠路径 |
| **context.filePath 值** | ❌ **错误** | 返回节点链接的.md文件而非canvas文件 |

#### 真正的根本原因

**问题调用链**:
```
用户右键点击 Canvas 节点
    ↓
handleCanvasNodeContextMenu() 构建正确的 context
    ├─ context.filePath = "Canvas/Math/lecture5.canvas" ✅ 正确！
    ├─ context.nodeId = "3820ad9e-e32b-4f96-87da-83918ade5c6c"
    └─ context.nodeColor = "1"
    ↓
registerBuiltInMenuItems() 中的 action 函数被调用
    ↓
action 调用 this.getCurrentContext() 而不是使用捕获的 context ❌❌❌
    ↓
getCurrentContext() 返回：
    {
      type: 'editor',
      filePath: "2025_lecture_53_05_corrected_hold.pdf-.../KP13-线性逼近与微分.md" ❌
    }
    ↓
extractCanvasFileName() 提取最后一部分
    ↓
canvas_name = "KP13-线性逼近与微分.md" ❌ (错误的文件名！)
    ↓
API 调用失败: "Path traversal detected" 或 "Canvas not found"
```

#### 问题代码位置

| 位置 | 文件 | 行号 | 问题 |
|------|------|------|------|
| **根源 1** | `ContextMenuManager.ts` | 230-237 | action 调用 `getCurrentContext()` 而非捕获的 context |
| **根源 2** | `ContextMenuManager.ts` | 961-968 | `getCurrentContext()` 返回 `getActiveFile()` 而非 canvas 文件 |
| **根源 3** | `ContextMenuManager.ts` | 891-910 | `addMenuItem()` 接收 context 但未传递给 action |

#### Obsidian API 限制 (社区调研)

**来源**: GitHub obsidian-tasks-group/obsidian-tasks#2971

> "Currently Obsidian is just not giving plugins the file path of the canvas"

- **标签**: "type: third-party change needed"
- **状态**: 等待 Obsidian 团队提供 API 增强
- **影响**: `getActiveFile()` 在 Canvas 视图中返回节点链接的文件，而非 canvas 文件本身

### Enhancement Details

**修复方案: Context 缓存机制**

在 `handleCanvasNodeContextMenu()` 中缓存正确的 context，让 `getCurrentContext()` 优先返回缓存值。

**核心修改**:
```typescript
// 新增私有属性
private cachedCanvasContext: MenuContext | null = null;

// 在 handleCanvasNodeContextMenu 中缓存
this.cachedCanvasContext = context;

// 修改 getCurrentContext()
private getCurrentContext(): MenuContext {
    // Epic 21.5.2: 优先返回缓存的 canvas context
    if (this.cachedCanvasContext) {
        const cached = this.cachedCanvasContext;
        this.cachedCanvasContext = null; // 使用后清除
        return cached;
    }
    // 回退到原有逻辑
    const activeFile = this.app.workspace.getActiveFile();
    return { type: 'editor', filePath: activeFile?.path };
}
```

### Success Criteria

- [ ] 所有9个Agent端点收到正确的`canvas_name` (仅文件名，如`"lecture5.canvas"`)
- [ ] 子目录下的Canvas文件也能正常工作
- [ ] 无HTTP 500错误
- [ ] 编辑器右键菜单功能不受影响
- [ ] 快速连续右键操作正常工作

---

## Stories

### Story 21.5.2.1: 实现Canvas Context缓存机制 (P0)

**目标**: 在`handleCanvasNodeContextMenu()`中缓存正确的context，让action使用

**验收标准**:
- [ ] AC-1: 添加私有属性`cachedCanvasContext: MenuContext | null`
- [ ] AC-2: 在`handleCanvasNodeContextMenu()`构建context后设置缓存
- [ ] AC-3: 修改`getCurrentContext()`优先返回缓存值
- [ ] AC-4: 缓存使用后立即清除，防止污染其他场景

**修改文件**:
- `canvas-progress-tracker/obsidian-plugin/src/managers/ContextMenuManager.ts`

**代码示例**:
```typescript
// 第1步: 添加属性 (类定义区域)
private cachedCanvasContext: MenuContext | null = null;

// 第2步: 设置缓存 (handleCanvasNodeContextMenu ~第854行后)
const context: MenuContext = {
    type: 'canvas-node',
    filePath: canvasView.file.path,
    nodeId: nodeInfo.nodeId,
    nodeColor: nodeInfo.nodeData?.color as CanvasNodeColor,
    nodeType: nodeInfo.nodeData?.type,
};
// Epic 21.5.2: 缓存当前 canvas context 供 action 使用
this.cachedCanvasContext = context;

// 第3步: 使用缓存 (getCurrentContext ~第961-968行)
private getCurrentContext(): MenuContext {
    // Epic 21.5.2: 优先返回缓存的 canvas context
    if (this.cachedCanvasContext) {
        const cached = this.cachedCanvasContext;
        this.cachedCanvasContext = null;
        return cached;
    }
    const activeFile = this.app.workspace.getActiveFile();
    return { type: 'editor', filePath: activeFile?.path };
}
```

---

### Story 21.5.2.2: 添加缓存清理与边界处理 (P1)

**目标**: 确保缓存机制在各种边界情况下正常工作

**验收标准**:
- [ ] AC-1: 菜单关闭时清除缓存 (防止缓存残留)
- [ ] AC-2: 快速连续右键不同节点时，每次都使用最新的context
- [ ] AC-3: 编辑器右键菜单不受缓存影响
- [ ] AC-4: 添加调试日志，便于问题追踪

**修改文件**:
- `canvas-progress-tracker/obsidian-plugin/src/managers/ContextMenuManager.ts`

**代码示例**:
```typescript
// 菜单关闭时清除缓存
menu.onHide(() => {
    this.cachedCanvasContext = null;
    this.log('ContextMenuManager: Canvas context cache cleared');
});

// 调试日志
this.log(`ContextMenuManager: Context cache set - filePath=${context.filePath}`);
```

---

### Story 21.5.2.3: 端到端测试与部署验证 (P2)

**目标**: 确保修复完整并成功部署

**验收标准**:
- [ ] AC-1: 构建插件 (`npm run build`) 无错误
- [ ] AC-2: 部署到Obsidian插件目录
- [ ] AC-3: 在Obsidian中重载插件
- [ ] AC-4: 测试所有Agent功能 (基础拆解、口语化解释、四层次解释等)
- [ ] AC-5: 验证控制台日志显示正确的`canvas_name`
- [ ] AC-6: 验证后端收到正确的参数 (检查bug_log.jsonl)

**测试场景**:

| 场景 | 预期结果 |
|------|----------|
| 右键Canvas节点 → 选择"基础拆解" | API收到正确的canvas_name |
| 右键Canvas节点 → 关闭菜单 → 右键编辑器 | 编辑器菜单正常工作 |
| 快速连续右键不同节点 | 每次都使用正确的context |
| 子目录下的Canvas文件 | 正常工作，无错误 |

**验证命令**:
```bash
# 构建
cd canvas-progress-tracker/obsidian-plugin
npm run build

# 部署
cp main.js manifest.json styles.css "笔记库/.obsidian/plugins/canvas-review-system/"

# 在Obsidian中
# Ctrl+P → "Reload app without saving"
```

---

## Compatibility Requirements

- [x] 现有APIs接口签名不变
- [x] 无数据库Schema变更
- [x] UI变更遵循现有模式
- [x] 性能影响最小 (仅增加一个指针赋值)

---

## Risk Mitigation

| 风险 | 缓解措施 | 回滚计划 |
|------|----------|----------|
| 缓存可能残留导致错误context | 菜单关闭时清除 + 使用后清除 | 移除缓存逻辑，恢复原代码 |
| 编辑器菜单受影响 | 缓存仅在Canvas右键时设置 | Git revert ContextMenuManager.ts |
| 并发/快速操作问题 | 每次右键都重新设置缓存 | 增加更严格的缓存管理 |

---

## Definition of Done

- [ ] 所有Stories完成且验收标准通过
- [ ] 现有功能通过回归测试
- [ ] 集成点工作正常
- [ ] 文档已更新 (本PRD标记完成)
- [ ] 无功能回归

---

## 与 Epic 21.5.1 的关系

| Epic | 修复内容 | 解决的问题 | 状态 |
|------|----------|------------|------|
| **21.5.1** | `extractCanvasFileName()` | 从路径提取文件名 | ✅ 已完成 |
| **21.5.2** | Context 缓存机制 | 确保传入正确的路径 | 🔴 进行中 |

**为什么需要 21.5.2?**

Epic 21.5.1 修复了"提取器"，但"输入"本身就是错误的。就像修复了一个"水龙头"，但"水管"接错了。

```
Epic 21.5.1 修复:
filePath → extractCanvasFileName() → canvas_name
           ↑ 这个函数OK

Epic 21.5.2 修复:
getCurrentContext() → filePath → extractCanvasFileName() → canvas_name
↑ 这个函数返回错误的filePath
```

---

## 技术分析记录

### 错误信息
```
HTTP 500: Path traversal detected in canvas name:
2025_lecture_53_05_corrected_hold.pdf-3820ad9e-e32b-4f96-87da-83918ade5c6c/KP13-线性逼近与微分.md
```

### 关键代码位置 (ContextMenuManager.ts)

#### 正确构建context的位置 (~第848-854行)
```typescript
const context: MenuContext = {
    type: 'canvas-node',
    filePath: canvasView.file.path,  // ✅ 这里是正确的canvas路径
    nodeId: nodeInfo.nodeId,
    nodeColor: nodeInfo.nodeData?.color as CanvasNodeColor,
    nodeType: nodeInfo.nodeData?.type,
};
```

#### 问题所在: action定义 (~第230-237行)
```typescript
action: async () => {
    if (this.actionRegistry.executeDecomposition) {
        await this.actionRegistry.executeDecomposition(this.getCurrentContext());
        // ↑ 问题: 调用getCurrentContext()而不是使用正确的context
    }
}
```

#### 问题所在: getCurrentContext (~第961-968行)
```typescript
private getCurrentContext(): MenuContext {
    const activeFile = this.app.workspace.getActiveFile();
    // ↑ 问题: getActiveFile()在Canvas中返回节点链接的文件
    return {
        type: 'editor',
        filePath: activeFile?.path,
    };
}
```

### 社区调研参考

- **Obsidian Tasks #2971**: "Obsidian is just not giving plugins the file path of the canvas"
- **Obsidian Forum - Canvas Menus**: 未文档化的`canvas:node-menu`事件可获取正确context

---

## Story Manager Handoff

请为此Brownfield Epic开发详细的用户故事。关键考虑：

- 这是对运行中系统的增强，技术栈为TypeScript (Obsidian Plugin)
- 集成点: `ContextMenuManager.ts` → `main.ts` → `ApiClient.ts` → 后端
- 遵循现有模式: 类似于`handleCanvasNodeContextMenu()`的context构建
- 关键兼容性要求: 编辑器菜单功能不受影响
- 每个story必须包含验证现有功能完整性的测试

Epic目标是在保持系统完整性的同时，修复Canvas右键菜单的context传递问题。
