# Context Menu API 开发文档

## 概述

Canvas Learning System 提供了完整的右键菜单 API，允许开发者注册自定义菜单项。

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                   ContextMenuManager                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ editor-menu  │  │  file-menu   │  │ MenuRegistry │      │
│  │   Handler    │  │   Handler    │  │              │      │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘      │
│         │                 │                                  │
│         ▼                 ▼                                  │
│  ┌──────────────────────────────────────────────────┐       │
│  │              Menu Item Generation                 │       │
│  │  - Dynamic based on node color                   │       │
│  │  - Context-aware visibility                      │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## 核心类

### ContextMenuManager

主要的右键菜单管理类。

```typescript
import { ContextMenuManager } from './managers/ContextMenuManager';

const manager = new ContextMenuManager(
  app,                      // Obsidian App 实例
  backupProtectionManager,  // 备份保护管理器
  settings                  // 可选的设置
);
```

### 初始化

```typescript
// 初始化并注册事件监听
manager.initialize();

// 销毁并移除事件监听
manager.destroy();
```

## 注册菜单项

### 使用 registerMenuItem

```typescript
manager.registerMenuItem({
  id: 'my-custom-action',
  title: '我的自定义操作',
  icon: 'star',
  contexts: ['canvas-node'],  // 或 ['file'], ['canvas-node', 'file']
  order: 100,
  callback: (context) => {
    console.log('执行操作', context);
  }
});
```

### MenuItemConfig 接口

```typescript
interface MenuItemConfig {
  /** 唯一标识符 */
  id: string;

  /** 显示标题 */
  title: string;

  /** 可选图标 (Lucide icon name) */
  icon?: string;

  /** 菜单上下文类型 */
  contexts: MenuContextType[];

  /** 排序顺序 (越小越靠前) */
  order?: number;

  /** 点击回调 */
  callback: MenuActionCallback;

  /** 可选的子菜单 */
  submenu?: MenuItemConfig[];

  /** 条件可见性函数 */
  condition?: (context: MenuContext) => boolean;
}
```

## 上下文类型

### MenuContextType

```typescript
type MenuContextType = 'canvas-node' | 'file' | 'editor';
```

### MenuContext

回调函数接收的上下文对象：

```typescript
interface MenuContext {
  /** 上下文类型 */
  type: MenuContextType;

  /** 触发事件的文件 */
  file?: TFile;

  /** Canvas 节点数据 (如果适用) */
  node?: CanvasNode;

  /** 节点颜色 */
  color?: CanvasNodeColor;

  /** 编辑器实例 */
  editor?: Editor;

  /** 菜单实例 */
  menu: Menu;
}
```

## 节点颜色

Canvas Learning System 使用颜色编码来表示学习进度：

```typescript
type CanvasNodeColor =
  | '1'  // 红色 - 困难/未理解
  | '2'  // 橙色 - 中等难度
  | '3'  // 黄色 - 个人理解区
  | '4'  // 绿色 - 已掌握
  | '5'  // 青色 - 待复习
  | '6'  // 紫色 - 部分理解
  | undefined;  // 无颜色
```

## 条件可见性

使用 `condition` 函数控制菜单项何时可见：

```typescript
manager.registerMenuItem({
  id: 'score-yellow-nodes',
  title: '评分黄色节点',
  contexts: ['canvas-node'],
  condition: (context) => {
    // 只在黄色节点上显示
    return context.color === '3';
  },
  callback: (context) => {
    // 评分逻辑
  }
});
```

## 子菜单

支持嵌套子菜单：

```typescript
manager.registerMenuItem({
  id: 'learning-menu',
  title: '学习操作',
  icon: 'book',
  contexts: ['canvas-node'],
  submenu: [
    {
      id: 'decompose',
      title: '拆解概念',
      icon: 'git-branch',
      callback: (ctx) => { /* ... */ }
    },
    {
      id: 'explain',
      title: '生成解释',
      icon: 'message-circle',
      callback: (ctx) => { /* ... */ }
    }
  ]
});
```

## 动作注册表

使用动作注册表集中管理回调：

```typescript
manager.registerAction('executeDecomposition', async (context) => {
  // 拆解逻辑
});

manager.registerAction('executeScoring', async (context) => {
  // 评分逻辑
});
```

## 备份保护集成

ContextMenuManager 自动集成 BackupProtectionManager：

```typescript
// 备份保护菜单项自动添加到 .canvas 文件的右键菜单
// - 保护/取消保护 Canvas
// - 在保护的 Canvas 上禁用删除
```

## 设置

### ContextMenuSettings

```typescript
interface ContextMenuSettings {
  /** 启用右键菜单 */
  enabled: boolean;

  /** 显示图标 */
  showIcons: boolean;

  /** 在顶级菜单显示 (vs 子菜单) */
  showAtTopLevel: boolean;

  /** 显示分隔符 */
  showSeparators: boolean;

  /** 启用的菜单项 ID */
  enabledItems: string[];
}
```

## 事件生命周期

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  初始化   │ ──► │  注册事件监听 │ ──► │  等待触发     │
└──────────┘     └──────────────┘     └──────────────┘
                                              │
                                              ▼
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  销毁    │ ◄── │  移除事件监听 │ ◄── │  处理菜单事件  │
└──────────┘     └──────────────┘     └──────────────┘
```

## 完整示例

```typescript
import { App, Plugin } from 'obsidian';
import { ContextMenuManager } from './managers/ContextMenuManager';
import { BackupProtectionManager } from './managers/BackupProtectionManager';

export default class MyPlugin extends Plugin {
  private contextMenuManager: ContextMenuManager;

  async onload() {
    const backupManager = new BackupProtectionManager(this.app);

    this.contextMenuManager = new ContextMenuManager(
      this.app,
      backupManager,
      { enabled: true }
    );

    // 注册自定义菜单项
    this.contextMenuManager.registerMenuItem({
      id: 'my-action',
      title: '我的操作',
      icon: 'star',
      contexts: ['canvas-node'],
      callback: async (context) => {
        console.log('节点:', context.node);
        console.log('颜色:', context.color);
      }
    });

    // 初始化
    this.contextMenuManager.initialize();
  }

  onunload() {
    this.contextMenuManager.destroy();
  }
}
```

## 与 HotkeyManager 的协同

ContextMenuManager 和 HotkeyManager 共享相同的命令 ID：

| 命令ID | 右键菜单 | 快捷键 |
|--------|---------|--------|
| `canvas-decompose-node` | ✅ | `Mod+Shift+D` |
| `canvas-score-node` | ✅ | `Mod+Shift+S` |
| `canvas-oral-explain` | ✅ | `Mod+Shift+E` |

这确保了用户可以通过两种方式访问相同功能。

---

**Story 13.5**: AC 1, 2, 6 - 右键菜单实现
**相关文件**:
- `src/managers/ContextMenuManager.ts`
- `src/managers/HotkeyManager.ts`
- `src/types/menu.ts`
