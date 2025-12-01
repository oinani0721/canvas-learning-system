# Story 13.5: 右键菜单和快捷键

## Status
Pending

## Story

**As a** Canvas学习系统用户,
**I want** 通过右键菜单和快捷键快速访问常用命令,
**so that** 提高学习效率，减少重复操作，提升整体使用体验。

## Acceptance Criteria

1. 在Canvas编辑器中右键点击节点时，显示自定义上下文菜单，包含常用命令（拆解、评分、解释等）
2. 在文件管理器中右键点击.canvas文件时，显示Canvas相关操作菜单
3. 实现SCP-003要求的"保护此备份 🔒"右键菜单选项，用于标记重要备份文件
4. 支持用户在插件设置中自定义快捷键绑定
5. 所有命令均支持通过快捷键触发，提供默认快捷键建议（但不强制设置）
6. 快捷键与上下文菜单命令保持一致性
7. 提供完整的快捷键文档和用户指南

## Tasks / Subtasks

- [ ] Task 1: 实现Editor上下文菜单 (AC: 1)
  - [ ] 注册editor-menu事件监听器
  - [ ] 检测右键点击的Canvas节点类型（文本/文件/链接/组）
  - [ ] 根据节点类型动态生成菜单项（拆解、评分、解释等）
  - [ ] 实现菜单项点击处理，调用对应的命令处理器
  - [ ] 为菜单项添加图标和描述文本

- [ ] Task 2: 实现文件管理器上下文菜单 (AC: 2)
  - [ ] 注册file-menu事件监听器
  - [ ] 检测右键点击的文件是否为.canvas文件
  - [ ] 添加Canvas专属菜单项（打开复习仪表板、批量操作等）
  - [ ] 实现菜单项与后端API的集成
  - [ ] 处理多文件选择情况（files-menu事件）

- [ ] Task 3: 实现SCP-003备份保护功能 (AC: 3)
  - [ ] 在.canvas_backups/目录的文件上下文菜单中添加"保护此备份 🔒"选项
  - [ ] 创建备份元数据管理系统（记录保护状态、创建时间、备注等）
  - [ ] 实现备份文件的锁定标记（添加.protected后缀或使用元数据文件）
  - [ ] 在文件列表中显示保护状态（图标或颜色标识）
  - [ ] 实现"取消保护"功能
  - [ ] 确保清理操作不会删除受保护的备份文件

- [ ] Task 4: 实现命令注册与快捷键绑定 (AC: 4, 5, 6)
  - [ ] 使用addCommand注册所有核心命令
  - [ ] 为每个命令定义唯一的命令ID（使用统一命名规范）
  - [ ] 设置命令的名称、图标和回调函数
  - [ ] 为常用命令提供建议的默认快捷键（遵循Obsidian最佳实践：不强制设置）
  - [ ] 实现checkCallback验证命令是否可用（例如：是否在Canvas视图中）
  - [ ] 确保快捷键与上下文菜单的命令ID一致

- [ ] Task 5: 快捷键设置界面 (AC: 4)
  - [ ] 在插件设置页面添加"快捷键"部分
  - [ ] 显示所有可用命令及其当前快捷键绑定
  - [ ] 提供快捷键冲突检测和警告
  - [ ] 支持快捷键的重置为默认值
  - [ ] 添加快捷键预设方案（初学者/高级用户/自定义）

- [ ] Task 6: 快捷键文档和帮助系统 (AC: 7)
  - [ ] 创建快捷键参考文档（Markdown格式）
  - [ ] 在插件设置中添加"查看快捷键帮助"按钮
  - [ ] 实现快捷键速查命令（显示快捷键备忘单）
  - [ ] 添加上下文帮助提示（hover时显示快捷键）
  - [ ] 创建快捷键冲突解决指南

- [ ] Task 7: 集成测试与用户体验优化 (AC: 1-7)
  - [ ] 测试所有上下文菜单在不同场景下的显示
  - [ ] 验证快捷键在不同操作系统上的兼容性（Mod键适配）
  - [ ] 测试快捷键冲突处理
  - [ ] 优化菜单显示性能（大量节点场景）
  - [ ] 收集用户反馈并迭代优化

## Dev Notes

### 架构上下文

**上下文菜单系统** [Source: Obsidian Plugin Developer Docs - Context Menus]

Obsidian提供了两种主要的上下文菜单扩展机制：

```
上下文菜单架构:
├── editor-menu (编辑器右键菜单)
│   ├── 触发条件: 在Canvas编辑器中右键点击
│   ├── 回调参数: (menu: Menu, editor: Editor, view: MarkdownView)
│   └── 用途: 节点级操作（拆解、评分、解释）
├── file-menu (文件右键菜单)
│   ├── 触发条件: 在文件管理器中右键点击单个文件
│   ├── 回调参数: (menu: Menu, file: TAbstractFile, source: string)
│   └── 用途: 文件级操作（打开复习仪表板、备份保护）
└── files-menu (多文件右键菜单)
    ├── 触发条件: 在文件管理器中右键点击多个文件
    ├── 回调参数: (menu: Menu, files: TAbstractFile[], source: string)
    └── 用途: 批量操作
```

### 技术验证要求

**⚠️ 强制文档来源**: `@obsidian-canvas` Skill

本Story实现的所有Obsidian API调用必须在代码中添加Skill引用注释，格式如下：
```typescript
// ✅ Verified from Obsidian Canvas Skill (README.md - Registering Events)
this.registerEvent(
  this.app.workspace.on('editor-menu', (menu, editor, view) => {
    // 菜单项添加逻辑
  })
);
```

### 核心API参考

**上下文菜单注册** [Source: @obsidian-canvas Skill - README.md, Context Menu Docs]

```typescript
// ✅ Verified from Obsidian Canvas Skill (Context Menus - Editor Menu Integration)
// 注册编辑器上下文菜单
this.registerEvent(
  this.app.workspace.on('editor-menu', (menu, editor, view) => {
    // 检查当前视图是否为Canvas
    if (view.file?.extension !== 'canvas') return;

    // 添加菜单项
    menu.addItem((item) => {
      item
        .setTitle('拆解此节点 🔍')
        .setIcon('git-branch')
        .onClick(async () => {
          // 调用拆解命令
          await this.commandWrapper.executeDecomposition(nodeId);
        });
    });

    menu.addItem((item) => {
      item
        .setTitle('评分 ⭐')
        .setIcon('star')
        .onClick(async () => {
          // 调用评分命令
          await this.commandWrapper.executeScoring(nodeId);
        });
    });
  })
);

// ✅ Verified from Obsidian Canvas Skill (Context Menus - File Menu Integration)
// 注册文件上下文菜单
this.registerEvent(
  this.app.workspace.on('file-menu', (menu, file, source) => {
    // 检查文件类型
    if (!(file instanceof TFile) || file.extension !== 'canvas') return;

    // 添加Canvas专属菜单项
    menu.addItem((item) => {
      item
        .setTitle('打开复习仪表板 📊')
        .setIcon('bar-chart')
        .onClick(async () => {
          await this.openReviewDashboard(file);
        });
    });

    // SCP-003: 备份保护菜单项
    if (file.path.includes('.canvas_backups/')) {
      const isProtected = await this.backupManager.isProtected(file.path);

      menu.addItem((item) => {
        item
          .setTitle(isProtected ? '取消保护 🔓' : '保护此备份 🔒')
          .setIcon(isProtected ? 'unlock' : 'lock')
          .onClick(async () => {
            await this.backupManager.toggleProtection(file.path);
          });
      });
    }
  })
);
```

**命令注册与快捷键** [Source: @obsidian-canvas Skill - README.md; GitHub obsidian-api]

```typescript
// ✅ Verified from Obsidian Canvas Skill (README.md - App Architecture)
// 命令注册（支持快捷键）
this.addCommand({
  id: 'canvas-decompose-node',
  name: '拆解当前节点',
  icon: 'git-branch',
  editorCheckCallback: (checking: boolean, editor: Editor, view: MarkdownView) => {
    // 检查当前是否在Canvas视图中
    const isCanvas = view.file?.extension === 'canvas';

    if (checking) {
      return isCanvas; // 返回命令是否可用
    }

    // 执行命令
    if (isCanvas) {
      this.executeDecomposition();
    }
  },
  // ⚠️ Obsidian最佳实践: 不设置默认快捷键，避免冲突
  // hotkeys: [] // 用户可在设置中自定义
});

// 带有建议快捷键的命令（在文档中说明，但不强制）
this.addCommand({
  id: 'canvas-score-nodes',
  name: '评分所有黄色节点',
  icon: 'star',
  // ⚠️ 不推荐设置默认快捷键
  // 建议在文档中说明: 推荐快捷键 Ctrl+Shift+S (用户自行设置)
  callback: async () => {
    await this.scoreAllYellowNodes();
  }
});
```

**Modifier键跨平台适配** [Source: GitHub obsidian-api/obsidian.d.ts]

```typescript
// ✅ Verified from Obsidian API (obsidian.d.ts - Modifier type)
// Mod键在macOS上映射为Meta(Cmd)，其他平台映射为Ctrl
// 可用的Modifier: 'Mod' | 'Ctrl' | 'Meta' | 'Shift' | 'Alt'

interface Hotkey {
  modifiers: Modifier[];
  key: string;
}

// 示例快捷键定义（用户自定义）
const suggestedHotkeys = {
  'canvas-decompose-node': { modifiers: ['Mod', 'Shift'], key: 'D' },
  'canvas-score-nodes': { modifiers: ['Mod', 'Shift'], key: 'S' },
  'canvas-oral-explain': { modifiers: ['Mod', 'Shift'], key: 'E' }
};
```

### SCP-003备份保护实现

**备份元数据管理** [Source: PRD Epic 13 - Story 13.5]

```typescript
interface BackupMetadata {
  filePath: string;
  protected: boolean;
  protectedAt?: number;
  protectedBy?: string;
  note?: string;
}

class BackupProtectionManager {
  private metadataPath = '.canvas_backups/.metadata.json';
  private metadata: Map<string, BackupMetadata>;

  // ✅ Verified from Obsidian Canvas Skill (README.md - Vault API)
  async loadMetadata(): Promise<void> {
    try {
      const file = this.app.vault.getAbstractFileByPath(this.metadataPath);
      if (file instanceof TFile) {
        const content = await this.app.vault.read(file);
        const data = JSON.parse(content);
        this.metadata = new Map(Object.entries(data));
      }
    } catch (error) {
      console.log('No existing metadata, creating new');
      this.metadata = new Map();
    }
  }

  async toggleProtection(filePath: string): Promise<void> {
    const current = this.metadata.get(filePath);

    if (current?.protected) {
      // 取消保护
      this.metadata.delete(filePath);
      new Notice(`备份已取消保护: ${filePath}`);
    } else {
      // 添加保护
      this.metadata.set(filePath, {
        filePath,
        protected: true,
        protectedAt: Date.now(),
        protectedBy: 'user',
      });
      new Notice(`备份已保护: ${filePath} 🔒`);
    }

    await this.saveMetadata();
  }

  async isProtected(filePath: string): Promise<boolean> {
    return this.metadata.get(filePath)?.protected || false;
  }

  async saveMetadata(): Promise<void> {
    const data = Object.fromEntries(this.metadata);
    const content = JSON.stringify(data, null, 2);

    const file = this.app.vault.getAbstractFileByPath(this.metadataPath);
    if (file instanceof TFile) {
      await this.app.vault.modify(file, content);
    } else {
      await this.app.vault.create(this.metadataPath, content);
    }
  }

  // 清理操作检查
  async canDelete(filePath: string): Promise<boolean> {
    if (await this.isProtected(filePath)) {
      new Notice('⚠️ 此备份已受保护，无法删除', 5000);
      return false;
    }
    return true;
  }
}
```

### 快捷键最佳实践

**Obsidian官方建议** [Source: Web Search - Obsidian Hotkey Best Practices]

1. **不设置默认快捷键**: 避免与用户自定义快捷键或其他插件冲突
2. **在文档中提供建议**: 在README和设置界面中说明推荐的快捷键组合
3. **使用Mod键**: 确保macOS和Windows/Linux的兼容性
4. **提供冲突检测**: 在设置界面中显示潜在冲突
5. **支持重复触发**: 对于需要重复执行的命令设置`repeatable: true`

**推荐快捷键方案** (仅作为文档建议，不强制)

```typescript
// 在插件README和设置界面中展示
const RECOMMENDED_HOTKEYS = {
  'canvas-decompose-node': 'Mod+Shift+D',
  'canvas-score-nodes': 'Mod+Shift+S',
  'canvas-oral-explain': 'Mod+Shift+E',
  'canvas-generate-verification': 'Mod+Shift+V',
  'canvas-open-dashboard': 'Mod+Shift+R',
};
```

### 用户体验考虑

**上下文感知菜单** [Source: Obsidian Canvas Skill - Context Menu Docs]

```typescript
// 根据节点状态动态生成菜单项
this.registerEvent(
  this.app.workspace.on('editor-menu', (menu, editor, view) => {
    if (view.file?.extension !== 'canvas') return;

    // 获取当前节点状态
    const nodeColor = this.getCurrentNodeColor(editor);

    // 根据颜色显示不同菜单项
    if (nodeColor === '1' || nodeColor === 'red') {
      // 红色节点: 提供拆解和解释
      menu.addItem((item) => {
        item.setTitle('拆解此概念 🔍').onClick(() => {/* ... */});
      });
      menu.addItem((item) => {
        item.setTitle('口语化解释 💬').onClick(() => {/* ... */});
      });
    } else if (nodeColor === '3' || nodeColor === 'yellow') {
      // 黄色节点: 提供评分和对比
      menu.addItem((item) => {
        item.setTitle('评分此节点 ⭐').onClick(() => {/* ... */});
      });
      menu.addItem((item) => {
        item.setTitle('生成对比表 📊').onClick(() => {/* ... */});
      });
    } else if (nodeColor === '4' || nodeColor === 'green') {
      // 绿色节点: 提供复习和导出
      menu.addItem((item) => {
        item.setTitle('添加到复习计划 📅').onClick(() => {/* ... */});
      });
    }

    // 通用菜单项（所有节点）
    menu.addSeparator();
    menu.addItem((item) => {
      item.setTitle('查看节点历史 🕐').onClick(() => {/* ... */});
    });
  })
);
```

### 性能优化

**菜单生成性能** [Source: Obsidian Plugin Best Practices]

```typescript
// 缓存常用数据，避免重复计算
class ContextMenuManager {
  private nodeCache = new Map<string, any>();

  // ✅ Verified from Obsidian Canvas Skill (README.md - registerEvent)
  registerMenus(): void {
    // 使用registerEvent确保自动清理
    this.registerEvent(
      this.app.workspace.on('editor-menu', (menu, editor, view) => {
        // 快速检查，避免不必要的处理
        if (view.file?.extension !== 'canvas') return;

        // 异步获取节点数据（不阻塞菜单显示）
        this.addMenuItems(menu, editor, view);
      })
    );
  }

  private addMenuItems(menu: Menu, editor: Editor, view: MarkdownView): void {
    // 添加菜单项（同步操作，快速完成）
    menu.addItem((item) => {
      item
        .setTitle('拆解节点')
        .setIcon('git-branch')
        .onClick(async () => {
          // 点击后再执行耗时操作
          await this.performDecomposition();
        });
    });
  }
}
```

### 编码规范

**TypeScript类型安全** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md]

```typescript
// 严格的类型定义
interface MenuItemConfig {
  title: string;
  icon: IconName;
  condition?: () => boolean;
  action: () => Promise<void>;
}

class CanvasMenuRegistry {
  private menuItems: Map<string, MenuItemConfig> = new Map();

  registerMenuItem(id: string, config: MenuItemConfig): void {
    this.menuItems.set(id, config);
  }

  // ✅ Verified from Obsidian Canvas Skill (Context Menus - menu.addItem API)
  buildMenu(menu: Menu, context: 'editor' | 'file'): void {
    this.menuItems.forEach((config, id) => {
      // 检查条件
      if (config.condition && !config.condition()) return;

      menu.addItem((item) => {
        item
          .setTitle(config.title)
          .setIcon(config.icon)
          .onClick(async () => {
            try {
              await config.action();
            } catch (error) {
              console.error(`Menu action failed: ${id}`, error);
              new Notice(`操作失败: ${error.message}`);
            }
          });
      });
    });
  }
}
```

### 测试要求

**跨平台测试** [Source: PRD Epic 13 - 兼容性需求]

1. **操作系统**: Windows, macOS, Linux
2. **Mod键映射**: 验证Mod在不同平台的行为
3. **快捷键冲突**: 测试与Obsidian核心快捷键的冲突
4. **性能**: 测试大量节点时的菜单响应速度

**测试场景**:
```typescript
// 测试用例示例
describe('Context Menu', () => {
  test('编辑器右键菜单在Canvas视图中显示', async () => {
    // 打开Canvas文件
    // 触发editor-menu事件
    // 验证菜单项存在
  });

  test('SCP-003备份保护菜单项正确显示', async () => {
    // 打开.canvas_backups/目录中的文件
    // 触发file-menu事件
    // 验证"保护此备份"菜单项存在
  });

  test('快捷键在macOS和Windows上正确工作', async () => {
    // 模拟Mod+Shift+D
    // 验证命令执行
  });
});
```

### 集成考虑

**与Story 13.4的集成** [Source: PRD Epic 13]

Story 13.4实现了核心命令的业务逻辑，本Story提供用户交互入口：

```
集成架构:
Story 13.5 (UI层)          Story 13.4 (逻辑层)
├── 上下文菜单         →   ├── CommandWrapper
│   └── 菜单项点击           └── 调用后端API
├── 快捷键绑定         →   └── 命令执行器
│   └── 命令触发
└── 备份保护UI         →   ├── BackupManager
    └── 元数据管理             └── 文件系统操作
```

**调用示例**:
```typescript
// 上下文菜单调用Story 13.4的CommandWrapper
menu.addItem((item) => {
  item
    .setTitle('拆解节点')
    .onClick(async () => {
      // 调用Story 13.4实现的命令包装器
      await this.plugin.commandWrapper.executeDecomposition({
        canvasPath: view.file.path,
        nodeId: currentNodeId,
      });
    });
});
```

### 文档要求

**用户文档** (docs/user-guide/hotkeys.md)

应包含：
1. 所有可用命令列表
2. 推荐的快捷键设置
3. 如何自定义快捷键
4. 如何解决快捷键冲突
5. 上下文菜单使用说明
6. SCP-003备份保护功能说明

**开发者文档** (docs/dev/context-menu-api.md)

应包含：
1. 如何注册新的上下文菜单项
2. 如何添加新命令
3. 菜单项命名规范
4. 图标选择指南

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-27 | 1.0 | 初始Story创建，基于Epic 13和PRD v1.1.8 | SM Agent (Bob) |

## Dev Agent Record

### Agent Model Used
待开发

### Debug Log References
待开发

### Completion Notes
待开发

### File List
**计划创建的文件：**
- `canvas-progress-tracker/obsidian-plugin/src/managers/ContextMenuManager.ts` - 上下文菜单管理器
- `canvas-progress-tracker/obsidian-plugin/src/managers/HotkeyManager.ts` - 快捷键管理器
- `canvas-progress-tracker/obsidian-plugin/src/managers/BackupProtectionManager.ts` - 备份保护管理器
- `canvas-progress-tracker/obsidian-plugin/src/types/menu.ts` - 菜单相关类型定义
- `canvas-progress-tracker/obsidian-plugin/src/utils/hotkey-helper.ts` - 快捷键工具函数
- `canvas-progress-tracker/obsidian-plugin/.canvas_backups/.metadata.json` - 备份元数据（运行时生成）
- `docs/user-guide/hotkeys.md` - 快捷键用户指南
- `docs/dev/context-menu-api.md` - 上下文菜单开发文档

**修改的文件：**
- `canvas-progress-tracker/obsidian-plugin/main.ts` - 注册上下文菜单和快捷键
- `canvas-progress-tracker/obsidian-plugin/src/types/settings.ts` - 添加快捷键配置
- `canvas-progress-tracker/obsidian-plugin/src/components/PluginSettingsTab.tsx` - 添加快捷键设置界面

## QA Results

### Review Date: 待开发

### Reviewed By: 待开发

### Code Quality Assessment
待开发

### Compliance Check
待开发

### Security Review
待开发

### Performance Considerations
待开发

### Architecture & Design Review
待开发

### Test Quality Review
待开发

### Final Status
待开发

---

## 技术验证摘要

**Skill验证**: ✅ @obsidian-canvas

**主要API验证**:
1. ✅ `this.registerEvent()` - 事件注册 (README.md)
2. ✅ `this.app.workspace.on('editor-menu', ...)` - 编辑器菜单 (Context Menu Docs)
3. ✅ `this.app.workspace.on('file-menu', ...)` - 文件菜单 (Context Menu Docs)
4. ✅ `menu.addItem()` - 菜单项添加 (Context Menu Docs)
5. ✅ `this.addCommand()` - 命令注册 (README.md)
6. ✅ `Modifier` 类型 - 快捷键修饰符 (obsidian.d.ts)

**外部参考来源**:
- [Obsidian Context Menus Documentation](https://docs.obsidian.md/Plugins/User+interface/Context+menus)
- [Obsidian Plugin Developer Docs - Context Menus](https://marcusolsson.github.io/obsidian-plugin-docs/user-interface/context-menus)
- [Obsidian API Repository](https://github.com/obsidianmd/obsidian-api)

---

**本Story完成后，用户将能够通过右键菜单和快捷键高效访问所有Canvas学习系统功能，极大提升使用体验。同时，SCP-003备份保护功能确保重要学习进度不会被意外删除。**
