/**
 * Hotkey Manager
 * Story 13.5: 右键菜单和快捷键 - Tasks 4, 5, 6
 *
 * Manages command registration and hotkey documentation.
 * Provides recommended hotkeys without forcing defaults (Obsidian best practice).
 *
 * ✅ Verified from @obsidian-canvas Skill (Plugin Development - addCommand)
 * ✅ Verified from Story 13.5 Dev Notes - Hotkey Best Practices
 */

import {
  App,
  Plugin,
  Editor,
  MarkdownView,
  Notice,
} from 'obsidian';
import type {
  CommandDefinition,
  CommandRegistryEntry,
  HotkeySettings,
  HotkeyDefinition,
} from '../types/menu';
import { DEFAULT_HOTKEY_SETTINGS } from '../types/menu';

// ============================================================================
// Types
// ============================================================================

/**
 * Command execution callback
 */
export type CommandCallback = () => void | Promise<void>;

/**
 * Editor check callback
 */
export type EditorCheckCallback = (
  checking: boolean,
  editor: Editor,
  view: MarkdownView
) => boolean | void;

// ============================================================================
// Constants - Recommended Hotkeys
// ============================================================================

/**
 * Recommended hotkeys for Canvas Learning System commands
 * These are NOT enforced - users can configure their own hotkeys
 *
 * ✅ Verified from Story 13.5 Dev Notes - Recommended Hotkey Scheme
 */
export const RECOMMENDED_HOTKEYS: Record<string, HotkeyDefinition> = {
  // Decomposition commands
  'canvas-decompose-node': { modifiers: ['Mod', 'Shift'], key: 'D' },
  'canvas-deep-decompose': { modifiers: ['Mod', 'Shift', 'Alt'], key: 'D' },

  // Explanation commands
  'canvas-oral-explain': { modifiers: ['Mod', 'Shift'], key: 'E' },
  'canvas-four-level-explain': { modifiers: ['Mod', 'Shift', 'Alt'], key: 'E' },

  // Scoring commands
  'canvas-score-node': { modifiers: ['Mod', 'Shift'], key: 'S' },
  'canvas-score-all-yellow': { modifiers: ['Mod', 'Shift', 'Alt'], key: 'S' },

  // Review commands
  'canvas-generate-verification': { modifiers: ['Mod', 'Shift'], key: 'V' },
  'canvas-open-dashboard': { modifiers: ['Mod', 'Shift'], key: 'R' },

  // Utility commands
  'canvas-show-hotkey-help': { modifiers: ['Mod', 'Shift'], key: '/' },
};

/**
 * Format hotkey for display
 */
export function formatHotkey(hotkey: HotkeyDefinition): string {
  const modifierNames: Record<string, string> = {
    Mod: navigator.platform.includes('Mac') ? '⌘' : 'Ctrl',
    Ctrl: 'Ctrl',
    Meta: '⌘',
    Shift: '⇧',
    Alt: navigator.platform.includes('Mac') ? '⌥' : 'Alt',
  };

  const parts = hotkey.modifiers.map(m => modifierNames[m] || m);
  parts.push(hotkey.key.toUpperCase());

  return parts.join(' + ');
}

// ============================================================================
// Hotkey Manager
// ============================================================================

/**
 * Manages command registration and hotkey documentation
 *
 * Story 13.5: AC 4, 5, 6 - Hotkey system
 *
 * Features:
 * - Register commands without enforced hotkeys
 * - Provide recommended hotkey documentation
 * - Hotkey cheat sheet command
 * - Canvas view detection for editor commands
 */
export class HotkeyManager {
  private app: App;
  private plugin: Plugin;
  private settings: HotkeySettings;
  private commands: Map<string, CommandRegistryEntry> = new Map();
  private debugMode: boolean = false;

  constructor(app: App, plugin: Plugin, settings?: Partial<HotkeySettings>) {
    this.app = app;
    this.plugin = plugin;
    this.settings = { ...DEFAULT_HOTKEY_SETTINGS, ...settings };
  }

  // ============================================================================
  // Initialization
  // ============================================================================

  /**
   * Initialize the hotkey manager and register all commands
   */
  initialize(): void {
    // Register built-in commands
    this.registerBuiltInCommands();

    // Register hotkey help command
    this.registerHotkeyHelpCommand();

    this.log('HotkeyManager: Initialized');
  }

  /**
   * Register built-in Canvas Learning System commands
   *
   * ✅ Verified from @obsidian-canvas Skill (README.md - addCommand)
   */
  private registerBuiltInCommands(): void {
    // Decomposition commands
    this.registerCommand({
      id: 'canvas-decompose-node',
      name: '拆解当前节点',
      icon: 'git-branch',
      suggestedHotkey: RECOMMENDED_HOTKEYS['canvas-decompose-node'],
      requiresCanvasView: true,
      category: 'decomposition',
      description: '将当前选中的概念拆解为子问题',
    });

    this.registerCommand({
      id: 'canvas-deep-decompose',
      name: '深度拆解当前节点',
      icon: 'git-merge',
      suggestedHotkey: RECOMMENDED_HOTKEYS['canvas-deep-decompose'],
      requiresCanvasView: true,
      category: 'decomposition',
      description: '生成深层次的理解验证问题',
    });

    // Explanation commands
    this.registerCommand({
      id: 'canvas-oral-explain',
      name: '口语化解释',
      icon: 'message-circle',
      suggestedHotkey: RECOMMENDED_HOTKEYS['canvas-oral-explain'],
      requiresCanvasView: true,
      category: 'explanation',
      description: '生成800-1200字的口语化解释',
    });

    this.registerCommand({
      id: 'canvas-four-level-explain',
      name: '四层次解答',
      icon: 'layers',
      suggestedHotkey: RECOMMENDED_HOTKEYS['canvas-four-level-explain'],
      requiresCanvasView: true,
      category: 'explanation',
      description: '从入门到创新的四层次解释',
    });

    // Scoring commands
    this.registerCommand({
      id: 'canvas-score-node',
      name: '评分当前节点',
      icon: 'star',
      suggestedHotkey: RECOMMENDED_HOTKEYS['canvas-score-node'],
      requiresCanvasView: true,
      category: 'scoring',
      description: '对当前节点进行4维评分',
    });

    this.registerCommand({
      id: 'canvas-score-all-yellow',
      name: '评分所有黄色节点',
      icon: 'stars',
      suggestedHotkey: RECOMMENDED_HOTKEYS['canvas-score-all-yellow'],
      requiresCanvasView: true,
      category: 'scoring',
      description: '批量评分所有个人理解节点',
    });

    // Review commands
    this.registerCommand({
      id: 'canvas-generate-verification',
      name: '生成检验白板',
      icon: 'check-circle',
      suggestedHotkey: RECOMMENDED_HOTKEYS['canvas-generate-verification'],
      requiresCanvasView: true,
      category: 'review',
      description: '生成无提示的检验白板',
    });

    this.registerCommand({
      id: 'canvas-open-dashboard',
      name: '打开复习仪表板',
      icon: 'bar-chart',
      suggestedHotkey: RECOMMENDED_HOTKEYS['canvas-open-dashboard'],
      requiresCanvasView: false,
      category: 'review',
      description: '打开艾宾浩斯复习仪表板',
    });

    // Utility commands
    this.registerCommand({
      id: 'canvas-comparison-table',
      name: '生成对比表',
      icon: 'table',
      requiresCanvasView: true,
      category: 'utility',
      description: '生成概念对比表',
    });

    this.registerCommand({
      id: 'canvas-memory-anchor',
      name: '生成记忆锚点',
      icon: 'anchor',
      requiresCanvasView: true,
      category: 'utility',
      description: '生成记忆锚点和助记符',
    });

    this.registerCommand({
      id: 'canvas-example-teaching',
      name: '例题教学',
      icon: 'book-open',
      requiresCanvasView: true,
      category: 'utility',
      description: '生成完整例题和详解',
    });

    this.log('HotkeyManager: Built-in commands registered');
  }

  /**
   * Register hotkey help command
   */
  private registerHotkeyHelpCommand(): void {
    // ✅ Verified from @obsidian-canvas Skill (README.md - addCommand with callback)
    this.plugin.addCommand({
      id: 'canvas-show-hotkey-help',
      name: 'Canvas: 显示快捷键帮助',
      icon: 'keyboard',
      callback: () => {
        this.showHotkeyCheatSheet();
      },
    });
  }

  // ============================================================================
  // Command Registration
  // ============================================================================

  /**
   * Register a command with optional Canvas view check
   *
   * ✅ Verified from @obsidian-canvas Skill (README.md - editorCheckCallback)
   * ✅ Verified from Obsidian API (obsidian.d.ts - Command interface)
   */
  registerCommand(definition: CommandDefinition): void {
    const entry: CommandRegistryEntry = {
      definition,
      registered: false,
    };

    // Build command options
    const commandOptions: any = {
      id: definition.id,
      name: definition.name,
    };

    if (definition.icon) {
      commandOptions.icon = definition.icon;
    }

    // ⚠️ Obsidian Best Practice: Don't set default hotkeys
    // Users can configure their own hotkeys in Settings > Hotkeys

    // Use editorCheckCallback if Canvas view is required
    if (definition.requiresCanvasView) {
      commandOptions.editorCheckCallback = (
        checking: boolean,
        editor: Editor,
        view: MarkdownView
      ) => {
        // Check if current view is a Canvas file
        const isCanvasView = view.file?.extension === 'canvas';

        if (checking) {
          return isCanvasView;
        }

        if (isCanvasView) {
          // Execute the command
          if (definition.callback) {
            definition.callback();
          } else if (definition.editorCheckCallback) {
            definition.editorCheckCallback(false, editor, view);
          } else {
            this.log(`HotkeyManager: No callback for ${definition.id}`);
          }
        }
      };
    } else if (definition.callback) {
      commandOptions.callback = definition.callback;
    }

    // Register with Obsidian
    this.plugin.addCommand(commandOptions);
    entry.registered = true;

    // Store in registry
    this.commands.set(definition.id, entry);

    this.log(`HotkeyManager: Registered command - ${definition.id}`);
  }

  /**
   * Set callback for a registered command
   */
  setCommandCallback(commandId: string, callback: CommandCallback): void {
    const entry = this.commands.get(commandId);
    if (entry) {
      entry.definition.callback = callback;
    }
  }

  // ============================================================================
  // Hotkey Help
  // ============================================================================

  /**
   * Show hotkey cheat sheet
   *
   * Story 13.5: AC 7 - Hotkey documentation
   */
  showHotkeyCheatSheet(): void {
    const content = this.generateCheatSheetContent();

    // Create a notice with the cheat sheet
    new Notice(content, 15000);

    this.log('HotkeyManager: Displayed hotkey cheat sheet');
  }

  /**
   * Generate cheat sheet content
   */
  private generateCheatSheetContent(): string {
    const lines: string[] = [
      '📋 Canvas Learning System 快捷键参考',
      '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━',
      '',
    ];

    // Group commands by category
    const categories: Record<string, CommandRegistryEntry[]> = {
      decomposition: [],
      explanation: [],
      scoring: [],
      review: [],
      utility: [],
    };

    for (const entry of this.commands.values()) {
      const category = entry.definition.category || 'utility';
      if (!categories[category]) {
        categories[category] = [];
      }
      categories[category].push(entry);
    }

    const categoryNames: Record<string, string> = {
      decomposition: '🔍 拆解命令',
      explanation: '💬 解释命令',
      scoring: '⭐ 评分命令',
      review: '📅 复习命令',
      utility: '🔧 工具命令',
    };

    for (const [category, entries] of Object.entries(categories)) {
      if (entries.length === 0) continue;

      lines.push(categoryNames[category] || category);

      for (const entry of entries) {
        const def = entry.definition;
        const hotkey = def.suggestedHotkey
          ? formatHotkey(def.suggestedHotkey)
          : '(未设置)';

        lines.push(`  ${def.name}: ${hotkey}`);
      }

      lines.push('');
    }

    lines.push('提示: 在设置 > 快捷键中自定义');

    return lines.join('\n');
  }

  /**
   * Get all registered commands
   */
  getCommands(): CommandDefinition[] {
    return Array.from(this.commands.values()).map(e => e.definition);
  }

  /**
   * Get commands by category
   */
  getCommandsByCategory(category: string): CommandDefinition[] {
    return Array.from(this.commands.values())
      .filter(e => e.definition.category === category)
      .map(e => e.definition);
  }

  /**
   * Get suggested hotkey for a command
   */
  getSuggestedHotkey(commandId: string): HotkeyDefinition | undefined {
    return RECOMMENDED_HOTKEYS[commandId];
  }

  // ============================================================================
  // Documentation Generation
  // ============================================================================

  /**
   * Generate Markdown documentation for all commands
   *
   * Story 13.5: AC 7 - User documentation
   */
  generateMarkdownDocumentation(): string {
    const lines: string[] = [
      '# Canvas Learning System 快捷键指南',
      '',
      '## 概述',
      '',
      '本文档列出了Canvas Learning System的所有可用命令及其建议快捷键。',
      '',
      '> **注意**: 快捷键是建议值，您可以在 设置 > 快捷键 中自定义。',
      '',
    ];

    // Group commands by category
    const categories: Record<string, CommandRegistryEntry[]> = {
      decomposition: [],
      explanation: [],
      scoring: [],
      review: [],
      utility: [],
    };

    for (const entry of this.commands.values()) {
      const category = entry.definition.category || 'utility';
      if (!categories[category]) {
        categories[category] = [];
      }
      categories[category].push(entry);
    }

    const categoryInfo: Record<string, { name: string; description: string }> = {
      decomposition: {
        name: '拆解命令',
        description: '将复杂概念拆解为更易理解的子问题',
      },
      explanation: {
        name: '解释命令',
        description: '生成各种形式的概念解释',
      },
      scoring: {
        name: '评分命令',
        description: '评估个人理解程度',
      },
      review: {
        name: '复习命令',
        description: '艾宾浩斯复习系统相关功能',
      },
      utility: {
        name: '工具命令',
        description: '其他辅助功能',
      },
    };

    for (const [category, entries] of Object.entries(categories)) {
      if (entries.length === 0) continue;

      const info = categoryInfo[category];
      lines.push(`## ${info.name}`);
      lines.push('');
      lines.push(info.description);
      lines.push('');
      lines.push('| 命令 | 建议快捷键 | 说明 |');
      lines.push('|------|-----------|------|');

      for (const entry of entries) {
        const def = entry.definition;
        const hotkey = def.suggestedHotkey
          ? `\`${formatHotkey(def.suggestedHotkey)}\``
          : '-';
        const desc = def.description || '-';

        lines.push(`| ${def.name} | ${hotkey} | ${desc} |`);
      }

      lines.push('');
    }

    // Add tips section
    lines.push('## 使用技巧');
    lines.push('');
    lines.push('### 如何自定义快捷键');
    lines.push('');
    lines.push('1. 打开 设置 (Ctrl/Cmd + ,)');
    lines.push('2. 点击左侧 "快捷键"');
    lines.push('3. 搜索 "Canvas"');
    lines.push('4. 点击命令旁的 "+" 按钮添加快捷键');
    lines.push('');
    lines.push('### 快捷键冲突');
    lines.push('');
    lines.push('如果快捷键与其他插件冲突，Obsidian会显示警告。');
    lines.push('建议使用 `Mod+Shift` 组合以减少冲突。');
    lines.push('');
    lines.push('### 跨平台说明');
    lines.push('');
    lines.push('- `Mod` 在 macOS 上是 `⌘ (Command)`，在 Windows/Linux 上是 `Ctrl`');
    lines.push('- `Alt` 在 macOS 上是 `⌥ (Option)`');
    lines.push('');

    return lines.join('\n');
  }

  // ============================================================================
  // Settings
  // ============================================================================

  /**
   * Update settings
   */
  updateSettings(settings: Partial<HotkeySettings>): void {
    this.settings = { ...this.settings, ...settings };
  }

  /**
   * Get current settings
   */
  getSettings(): HotkeySettings {
    return { ...this.settings };
  }

  /**
   * Enable/disable debug mode
   */
  setDebugMode(enabled: boolean): void {
    this.debugMode = enabled;
  }

  // ============================================================================
  // Utility
  // ============================================================================

  /**
   * Log message if debug mode is enabled
   */
  private log(message: string): void {
    if (this.debugMode) {
      console.log(message);
    }
  }

  /**
   * Clean up resources
   */
  cleanup(): void {
    this.commands.clear();
    this.log('HotkeyManager: Cleaned up');
  }
}
