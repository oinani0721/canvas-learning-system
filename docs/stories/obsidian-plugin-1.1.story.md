# Story Obsidian-Plugin-1.1: Obsidian插件核心框架搭建

## Status
Pending

## Story

**As a** Canvas学习系统开发者,
**I want** 搭建Obsidian插件的核心框架结构,
**so that** 为后续的命令包装、数据持久化和UI组件开发奠定坚实的基础。

## Acceptance Criteria

1. 创建完整的Obsidian插件项目结构，包含manifest.json、package.json、main.ts等核心文件
2. 实现CanvasReviewPlugin主类，包含插件生命周期管理（onload/onunload）
3. 配置TypeScript编译环境和esbuild构建工具
4. 实现基础插件设置界面（PluginSettingsTab）
5. 插件能够在Obsidian中成功加载和卸载，无错误日志
6. 创建基础的命令注册框架（注册"显示复习仪表板"命令）

## Tasks / Subtasks

- [ ] Task 1: 创建插件项目基础结构 (AC: 1)
  - [ ] 在canvas-progress-tracker目录下创建obsidian-plugin子目录
  - [ ] 创建manifest.json，配置插件基本信息（版本1.0.0，依赖Obsidian v0.15+）
  - [ ] 创建package.json，配置开发依赖（TypeScript, esbuild, obsidian等）
  - [ ] 创建main.ts作为插件入口文件
  - [ ] 创建styles.css用于插件样式

- [ ] Task 2: 实现CanvasReviewPlugin主类 (AC: 2, 5)
  - [ ] 定义PluginSettings接口（claudeCodeUrl, dataPath, autoSyncInterval等）
  - [ ] 实现CanvasReviewPlugin类继承自Plugin
  - [ ] 实现onload()方法，设置默认配置、注册事件、加载设置
  - [ ] 实现onunload()方法，清理资源、保存设置
  - [ ] 添加完整的错误处理和日志记录

- [ ] Task 3: 配置TypeScript和构建环境 (AC: 3)
  - [ ] 创建tsconfig.json配置TypeScript编译选项
  - [ ] 创建esbuild.config.mjs配置构建脚本
  - [ ] 配置package.json的scripts（dev, build, version命令）
  - [ ] 设置开发环境的热重载功能
  - [ ] 确保构建产物符合Obsidian插件规范

- [ ] Task 4: 实现插件设置界面 (AC: 4)
  - [ ] 创建PluginSettingsTab类继承自PluginSettingTab
  - [ ] 实现设置界面布局（Claude Code连接配置、数据存储路径等）
  - [ ] 添加设置保存和加载功能
  - [ ] 实现设置验证和错误提示
  - [ ] 美化设置界面，符合Obsidian原生设计风格

- [ ] Task 5: 实现基础命令注册框架 (AC: 6)
  - [ ] 在onload()中注册"显示复习仪表板"命令
  - [ ] 创建命令处理函数的占位实现
  - [ ] 添加命令的图标和快捷键支持
  - [ ] 实现命令状态管理和错误处理
  - [ ] 测试命令在Obsidian命令面板中的显示和执行

- [ ] Task 6: 插件集成测试 (AC: 5)
  - [ ] 在Obsidian中测试插件加载
  - [ ] 验证插件卸载时无内存泄漏
  - [ ] 测试设置界面的完整功能
  - [ ] 验证命令注册和执行
  - [ ] 确保所有控制台日志正常，无错误信息

## Dev Notes

### 架构上下文

**Obsidian插件架构** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#系统架构概览]

本Story实现插件的核心框架，为后续的命令包装器、数据管理层和UI组件层奠定基础：

```
Obsidian插件层架构:
├── PluginCore (CanvasReviewPlugin) ← 本Story实现
├── CommandWrapper (命令包装层)
├── DataManager (数据管理层)
└── UIManager (UI组件层)
```

**技术栈选择** [Source: canvas-progress-tracker/docs/obsidian-plugin-prd.md#技术栈]
- 前端框架: React 18.0+ + TypeScript 5.0+
- 构建工具: esbuild (快速构建)
- 插件API: Obsidian v0.15+
- 数据存储: SQLite + JSON文件 + IndexedDB
- 通信方式: HTTP API + 子进程通信

### 插件项目结构

**标准Obsidian插件结构** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#部署与分发]

```
canvas-progress-tracker/obsidian-plugin/
├── manifest.json          # 插件清单文件
├── package.json           # npm配置文件
├── tsconfig.json          # TypeScript配置
├── esbuild.config.mjs     # 构建配置
├── main.ts               # 插件入口文件 ⭐
├── styles.css            # 插件样式文件
├── src/                  # 源代码目录
│   ├── components/       # React组件
│   ├── managers/         # 管理器类
│   ├── types/           # TypeScript类型定义
│   └── utils/           # 工具函数
├── dist/                # 构建输出目录
│   ├── main.js          # 编译后的主文件
│   ├── styles.css       # 处理后的样式
│   └── manifest.json    # 复制的清单文件
└── node_modules/        # 依赖包
```

### 核心文件配置

**manifest.json配置** [Source: canvas-progress-tracker/docs/obsidian-plugin-prd.md#功能需求]
```json
{
  "id": "canvas-review-system",
  "name": "Canvas复习系统",
  "version": "1.0.0",
  "minAppVersion": "0.15.0",
  "description": "基于艾宾浩斯算法的Canvas智能复习管理插件",
  "author": "Canvas Learning System",
  "authorUrl": "https://github.com/canvas-learning-system",
  "fundingUrl": "https://github.com/canvas-learning-system",
  "isDesktopOnly": false
}
```

**package.json依赖** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#构建配置]
```json
{
  "name": "obsidian-canvas-review",
  "version": "1.0.0",
  "description": "Canvas复习系统Obsidian插件",
  "main": "main.js",
  "scripts": {
    "dev": "node esbuild.config.mjs",
    "build": "tsc -noEmit -skipLibCheck && node esbuild.config.mjs production",
    "version": "node version-bump.mjs && git add manifest.json versions.json"
  },
  "devDependencies": {
    "@types/node": "^16.11.6",
    "@typescript-eslint/eslint-plugin": "5.29.0",
    "@typescript-eslint/parser": "5.29.0",
    "builtin-modules": "3.3.0",
    "esbuild": "0.17.3",
    "obsidian": "latest",
    "tslib": "2.4.0",
    "typescript": "4.7.4"
  }
}
```

### 核心类设计

**CanvasReviewPlugin主类** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#插件核心类]
```typescript
interface PluginSettings {
  claudeCodeUrl: string;
  dataPath: string;
  autoSyncInterval: number;
  enableCache: boolean;
  commandTimeout: number;
  theme: 'light' | 'dark' | 'auto';
}

export default class CanvasReviewPlugin extends Plugin {
  settings: PluginSettings;
  dataManager: DataManager;
  commandWrapper: CommandWrapper;
  uiManager: UIManager;
  syncManager: SyncManager;

  async onload(): Promise<void> {
    console.log('Canvas复习系统插件加载中...');

    // 加载设置
    await this.loadSettings();

    // 初始化管理器
    this.initializeManagers();

    // 注册命令
    this.registerCommands();

    // 注册设置界面
    this.addSettingTab(new PluginSettingsTab(this.app, this));

    console.log('Canvas复习系统插件加载完成');
  }

  async onunload(): Promise<void> {
    console.log('Canvas复习系统插件卸载中...');

    // 停止同步管理器
    if (this.syncManager) {
      this.syncManager.stopAutoSync();
    }

    // 清理资源
    this.cleanupResources();

    console.log('Canvas复习系统插件卸载完成');
  }
}
```

**设置界面类** [Source: canvas-progress-tracker/docs/obsidian-plugin-prd.md#基础UI组件]
```typescript
export class PluginSettingsTab extends PluginSettingTab {
  plugin: CanvasReviewPlugin;

  constructor(app: App, plugin: CanvasReviewPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const {containerEl} = this;
    containerEl.empty();

    containerEl.createEl('h2', {text: 'Canvas复习系统设置'});

    // Claude Code连接设置
    new Setting(containerEl)
      .setName('Claude Code服务地址')
      .setDesc('Claude Code API服务的基础URL')
      .addText(text => text
        .setPlaceholder('http://localhost:3005')
        .setValue(this.plugin.settings.claudeCodeUrl)
        .onChange(async (value) => {
          this.plugin.settings.claudeCodeUrl = value;
          await this.plugin.saveSettings();
        }));

    // 数据存储路径设置
    new Setting(containerEl)
      .setName('数据存储路径')
      .setDesc('Canvas学习系统数据的存储路径')
      .addText(text => text
        .setPlaceholder('C:/Users/ROG/托福')
        .setValue(this.plugin.settings.dataPath)
        .onChange(async (value) => {
          this.plugin.settings.dataPath = value;
          await this.plugin.saveSettings();
        }));

    // 更多设置项...
  }
}
```

### 编码规范

**TypeScript编码标准** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#开发规范]
- 使用严格的TypeScript配置（strict: true）
- 明确的类型注解和接口定义
- 使用async/await处理异步操作
- 遵循Obsidian插件API最佳实践

**错误处理原则**
```typescript
// 统一的错误处理模式
try {
  await this.performOperation();
} catch (error) {
  console.error('Canvas复习系统操作失败:', error);
  new Notice('操作失败，请检查设置或重试');
  // 记录详细错误信息用于调试
}
```

### 构建配置

**esbuild配置** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#构建脚本]
```javascript
// esbuild.config.mjs
import esbuild from "esbuild";
import process from "process";
import builtins from "builtin-modules";

const banner = `/*
THIS IS A GENERATED/BUNDLED FILE BY ESBUILD
if you want to view the source, please visit the github repository of this plugin
*/
`;

const prod = (process.argv[2] === 'production');

const context = await esbuild.context({
  banner: { js: banner },
  entryPoints: ['main.ts'],
  bundle: true,
  external: [
    'obsidian',
    'electron',
    '@codemirror/view',
    '@codemirror/state',
    ...builtins],
  format: 'cjs',
  target: 'es2018',
  logLevel: "info",
  sourcemap: prod ? false : 'inline',
  treeShaking: true,
  outfile: 'main.js',
});

if (prod) {
  await context.rebuild();
  process.exit(0);
} else {
  await context.watch();
  console.log("watching for changes...");
}
```

### 测试要求

**开发环境测试** [Source: canvas-progress-tracker/docs/obsidian-plugin-prd.md#兼容性需求]
- 在Obsidian v0.15+中测试插件加载
- 验证设置界面的所有功能
- 测试命令注册和执行
- 确保在不同操作系统上正常工作

**测试步骤**:
1. 启动开发模式：`npm run dev`
2. 在Obsidian中启用插件
3. 检查控制台是否有错误
4. 测试设置界面的保存和加载
5. 验证命令在命令面板中显示
6. 测试插件的卸载和重载

### 集成考虑

**后续开发准备** [Source: canvas-progress-tracker/docs/obsidian-plugin-prd.md#Phase 1 MVP]
- 为下一阶段的命令包装器预留接口
- 数据管理器的占位实现
- React组件的集成准备
- Claude Code API连接的基础框架

**版本控制**
- 使用语义化版本控制（Semantic Versioning）
- 维护详细的变更日志
- 标记每次发布的里程碑

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-27 | 1.0 | 初始Story创建 | PM Agent (Sarah) |

## Dev Agent Record

### Agent Model Used
待开发

### Debug Log References
待开发

### Completion Notes
待开发

### File List
**计划创建的文件：**
- `canvas-progress-tracker/obsidian-plugin/manifest.json` - 插件清单
- `canvas-progress-tracker/obsidian-plugin/package.json` - npm配置
- `canvas-progress-tracker/obsidian-plugin/tsconfig.json` - TypeScript配置
- `canvas-progress-tracker/obsidian-plugin/esbuild.config.mjs` - 构建配置
- `canvas-progress-tracker/obsidian-plugin/main.ts` - 插件主文件
- `canvas-progress-tracker/obsidian-plugin/styles.css` - 样式文件
- `canvas-progress-tracker/obsidian-plugin/src/types/settings.ts` - 设置类型定义
- `canvas-progress-tracker/obsidian-plugin/src/managers/` - 管理器目录（占位）

**修改的文件：**
- 无

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

**本Story完成后，将建立起Obsidian插件的完整开发环境，为后续的命令包装、数据持久化和UI组件开发提供坚实的基础框架。**