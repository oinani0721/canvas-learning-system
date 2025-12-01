/**
 * Context Menu Manager
 * Story 13.5: 右键菜单和快捷键 - Tasks 1, 2
 *
 * Manages context menus for Canvas nodes and files.
 * Integrates with Obsidian's editor-menu and file-menu events.
 *
 * ✅ Verified from @obsidian-canvas Skill (Plugin Development - Event Registration)
 * ✅ Verified from Story 13.5 Dev Notes - Context Menu Architecture
 */

import {
  App,
  Menu,
  TFile,
  TAbstractFile,
  Editor,
  MarkdownView,
  Notice,
  EventRef,
} from 'obsidian';
import type {
  MenuItemConfig,
  MenuContext,
  MenuContextType,
  MenuRegistryEntry,
  ContextMenuSettings,
  CanvasNodeColor,
} from '../types/menu';
import {
  DEFAULT_CONTEXT_MENU_SETTINGS,
  CANVAS_COLOR_NAMES,
} from '../types/menu';
import { BackupProtectionManager } from './BackupProtectionManager';
import { BACKUP_FOLDER } from '../utils/canvas-helpers';

// ============================================================================
// Types
// ============================================================================

/**
 * Callback type for menu item actions
 */
export type MenuActionCallback = (context: MenuContext) => void | Promise<void>;

/**
 * Menu action registry for external command integration
 */
export interface MenuActionRegistry {
  /** Execute decomposition on a node */
  executeDecomposition?: MenuActionCallback;
  /** Execute scoring on nodes */
  executeScoring?: MenuActionCallback;
  /** Execute oral explanation */
  executeOralExplanation?: MenuActionCallback;
  /** Execute four-level explanation */
  executeFourLevelExplanation?: MenuActionCallback;
  /** Open review dashboard */
  openReviewDashboard?: MenuActionCallback;
  /** Generate verification canvas */
  generateVerificationCanvas?: MenuActionCallback;
  /** View node history */
  viewNodeHistory?: MenuActionCallback;
  /** Add to review plan */
  addToReviewPlan?: MenuActionCallback;
  /** Generate comparison table */
  generateComparisonTable?: MenuActionCallback;
}

// ============================================================================
// Context Menu Manager
// ============================================================================

/**
 * Manages context menus for the Canvas Learning System
 *
 * Story 13.5: AC 1, 2 - Context menu integration
 *
 * Features:
 * - Editor context menu for Canvas nodes
 * - File context menu for .canvas files
 * - Backup protection menu items
 * - Dynamic menu generation based on node color
 */
export class ContextMenuManager {
  private app: App;
  private settings: ContextMenuSettings;
  private backupProtectionManager: BackupProtectionManager;
  private menuItems: Map<string, MenuRegistryEntry> = new Map();
  private actionRegistry: MenuActionRegistry = {};
  private eventRefs: EventRef[] = [];
  private debugMode: boolean = false;

  constructor(
    app: App,
    backupProtectionManager: BackupProtectionManager,
    settings?: Partial<ContextMenuSettings>
  ) {
    this.app = app;
    this.backupProtectionManager = backupProtectionManager;
    this.settings = { ...DEFAULT_CONTEXT_MENU_SETTINGS, ...settings };
  }

  // ============================================================================
  // Initialization
  // ============================================================================

  /**
   * Initialize context menu handlers
   *
   * ✅ Verified from @obsidian-canvas Skill (README.md - registerEvent pattern)
   *
   * @param plugin - Plugin instance for event registration
   */
  initialize(plugin: { registerEvent: (ref: EventRef) => void }): void {
    // Register built-in menu items
    this.registerBuiltInMenuItems();

    // Register editor-menu event
    // ✅ Verified from @obsidian-canvas Skill (Plugin Development - Event Registration)
    if (this.settings.enableEditorMenu) {
      const editorMenuRef = this.app.workspace.on(
        'editor-menu',
        (menu: Menu, editor: Editor, view: MarkdownView) => {
          this.handleEditorMenu(menu, editor, view);
        }
      );
      plugin.registerEvent(editorMenuRef);
      this.eventRefs.push(editorMenuRef);
    }

    // Register file-menu event
    // ✅ Verified from @obsidian-canvas Skill (Plugin Development - Event Registration)
    if (this.settings.enableFileMenu) {
      const fileMenuRef = this.app.workspace.on(
        'file-menu',
        (menu: Menu, file: TAbstractFile, source: string) => {
          this.handleFileMenu(menu, file, source);
        }
      );
      plugin.registerEvent(fileMenuRef);
      this.eventRefs.push(fileMenuRef);
    }

    this.log('ContextMenuManager: Initialized');
  }

  /**
   * Set action registry for command integration
   */
  setActionRegistry(registry: MenuActionRegistry): void {
    this.actionRegistry = { ...this.actionRegistry, ...registry };
  }

  /**
   * Enable/disable debug mode
   */
  setDebugMode(enabled: boolean): void {
    this.debugMode = enabled;
  }

  // ============================================================================
  // Built-in Menu Items
  // ============================================================================

  /**
   * Register built-in menu items
   */
  private registerBuiltInMenuItems(): void {
    // Primary actions - Decomposition
    this.registerMenuItem({
      id: 'decompose-node',
      title: '拆解此节点 🔍',
      icon: 'git-branch',
      section: 'primary',
      description: '将复杂概念拆解为子问题',
      action: async () => {
        if (this.actionRegistry.executeDecomposition) {
          await this.actionRegistry.executeDecomposition(this.getCurrentContext());
        } else {
          new Notice('拆解功能尚未初始化');
        }
      },
    }, ['editor'], 100);

    // Primary actions - Oral Explanation
    this.registerMenuItem({
      id: 'oral-explanation',
      title: '口语化解释 💬',
      icon: 'message-circle',
      section: 'primary',
      description: '生成易于理解的口语化解释',
      action: async () => {
        if (this.actionRegistry.executeOralExplanation) {
          await this.actionRegistry.executeOralExplanation(this.getCurrentContext());
        } else {
          new Notice('口语化解释功能尚未初始化');
        }
      },
    }, ['editor'], 90);

    // Primary actions - Four Level Explanation
    this.registerMenuItem({
      id: 'four-level-explanation',
      title: '四层次解答 📚',
      icon: 'layers',
      section: 'primary',
      description: '从入门到精通的四层次解释',
      action: async () => {
        if (this.actionRegistry.executeFourLevelExplanation) {
          await this.actionRegistry.executeFourLevelExplanation(this.getCurrentContext());
        } else {
          new Notice('四层次解答功能尚未初始化');
        }
      },
    }, ['editor'], 85);

    // Secondary actions - Scoring
    this.registerMenuItem({
      id: 'score-node',
      title: '评分此节点 ⭐',
      icon: 'star',
      section: 'secondary',
      description: '对节点内容进行4维评分',
      action: async () => {
        if (this.actionRegistry.executeScoring) {
          await this.actionRegistry.executeScoring(this.getCurrentContext());
        } else {
          new Notice('评分功能尚未初始化');
        }
      },
    }, ['editor'], 80);

    // Secondary actions - Comparison Table
    this.registerMenuItem({
      id: 'generate-comparison',
      title: '生成对比表 📊',
      icon: 'table',
      section: 'secondary',
      description: '生成概念对比表',
      action: async () => {
        if (this.actionRegistry.generateComparisonTable) {
          await this.actionRegistry.generateComparisonTable(this.getCurrentContext());
        } else {
          new Notice('对比表生成功能尚未初始化');
        }
      },
    }, ['editor'], 75);

    // Utility actions - Node History
    this.registerMenuItem({
      id: 'view-history',
      title: '查看节点历史 🕐',
      icon: 'history',
      section: 'utility',
      description: '查看此节点的学习历史',
      action: async () => {
        if (this.actionRegistry.viewNodeHistory) {
          await this.actionRegistry.viewNodeHistory(this.getCurrentContext());
        } else {
          new Notice('历史记录功能尚未初始化');
        }
      },
    }, ['editor'], 50);

    // Utility actions - Add to Review
    this.registerMenuItem({
      id: 'add-to-review',
      title: '添加到复习计划 📅',
      icon: 'calendar',
      section: 'utility',
      description: '将节点添加到艾宾浩斯复习计划',
      action: async () => {
        if (this.actionRegistry.addToReviewPlan) {
          await this.actionRegistry.addToReviewPlan(this.getCurrentContext());
        } else {
          new Notice('复习计划功能尚未初始化');
        }
      },
    }, ['editor'], 45);

    // File menu - Review Dashboard
    this.registerMenuItem({
      id: 'open-review-dashboard',
      title: '打开复习仪表板 📊',
      icon: 'bar-chart',
      section: 'primary',
      description: '打开Canvas复习仪表板',
      action: async () => {
        if (this.actionRegistry.openReviewDashboard) {
          await this.actionRegistry.openReviewDashboard(this.getCurrentContext());
        } else {
          new Notice('复习仪表板功能尚未初始化');
        }
      },
    }, ['file'], 100);

    // File menu - Generate Verification Canvas
    this.registerMenuItem({
      id: 'generate-verification',
      title: '生成检验白板 ✅',
      icon: 'check-circle',
      section: 'primary',
      description: '生成无提示检验白板',
      action: async () => {
        if (this.actionRegistry.generateVerificationCanvas) {
          await this.actionRegistry.generateVerificationCanvas(this.getCurrentContext());
        } else {
          new Notice('检验白板功能尚未初始化');
        }
      },
    }, ['file'], 90);

    this.log('ContextMenuManager: Built-in menu items registered');
  }

  // ============================================================================
  // Menu Registration
  // ============================================================================

  /**
   * Register a menu item
   *
   * @param config - Menu item configuration
   * @param contexts - Context types where item appears
   * @param priority - Priority for ordering (higher = earlier)
   */
  registerMenuItem(
    config: MenuItemConfig,
    contexts: MenuContextType[],
    priority: number = 50
  ): void {
    this.menuItems.set(config.id, {
      config,
      contexts,
      priority,
    });
  }

  /**
   * Unregister a menu item
   *
   * @param id - Menu item ID to remove
   */
  unregisterMenuItem(id: string): void {
    this.menuItems.delete(id);
  }

  // ============================================================================
  // Event Handlers
  // ============================================================================

  /**
   * Handle editor context menu
   *
   * ✅ Verified from @obsidian-canvas Skill (Context Menus - Editor Menu)
   */
  private handleEditorMenu(menu: Menu, editor: Editor, view: MarkdownView): void {
    // Check if this is a Canvas view
    const file = view.file;
    if (!file || file.extension !== 'canvas') {
      return; // Not a Canvas file
    }

    this.log(`ContextMenuManager: Editor menu for ${file.path}`);

    // Build context
    const context: MenuContext = {
      type: 'editor',
      filePath: file.path,
    };

    // Get relevant menu items
    const items = this.getMenuItemsForContext('editor');

    // Group by section
    const sections = this.groupBySection(items);

    // Add items to menu
    let isFirstSection = true;
    for (const [section, sectionItems] of Object.entries(sections)) {
      // Add separator before secondary sections
      if (!isFirstSection) {
        menu.addSeparator();
      }
      isFirstSection = false;

      for (const entry of sectionItems) {
        this.addMenuItem(menu, entry.config, context);
      }
    }
  }

  /**
   * Handle file context menu
   *
   * ✅ Verified from @obsidian-canvas Skill (Context Menus - File Menu)
   */
  private handleFileMenu(menu: Menu, file: TAbstractFile, source: string): void {
    // Only handle TFile instances
    if (!(file instanceof TFile)) {
      return;
    }

    // Check if this is a canvas file
    if (file.extension !== 'canvas') {
      return;
    }

    this.log(`ContextMenuManager: File menu for ${file.path}`);

    // Build context
    const context: MenuContext = {
      type: 'file',
      filePath: file.path,
      isBackupFile: this.backupProtectionManager.isBackupFile(file.path),
    };

    // Get relevant menu items
    const items = this.getMenuItemsForContext('file');

    // Add separator before our items
    menu.addSeparator();

    // Add standard canvas file items
    for (const entry of items) {
      this.addMenuItem(menu, entry.config, context);
    }

    // Add backup protection item if in backup folder
    // Story 13.5: AC 3 - SCP-003 backup protection
    if (context.isBackupFile) {
      this.addBackupProtectionMenuItem(menu, file.path);
    }
  }

  /**
   * Add backup protection menu item
   *
   * Story 13.5: AC 3 - SCP-003 backup protection
   */
  private async addBackupProtectionMenuItem(menu: Menu, filePath: string): Promise<void> {
    const isProtected = await this.backupProtectionManager.isProtected(filePath);

    menu.addSeparator();

    // ✅ Verified from @obsidian-canvas Skill (Context Menus - menu.addItem)
    menu.addItem((item) => {
      item
        .setTitle(isProtected ? '取消保护 🔓' : '保护此备份 🔒')
        .setIcon(isProtected ? 'unlock' : 'lock')
        .onClick(async () => {
          try {
            await this.backupProtectionManager.toggleProtection(filePath);
          } catch (error) {
            const message = error instanceof Error ? error.message : '未知错误';
            new Notice(`操作失败: ${message}`);
          }
        });
    });
  }

  // ============================================================================
  // Menu Building Helpers
  // ============================================================================

  /**
   * Add a menu item to the menu
   *
   * ✅ Verified from @obsidian-canvas Skill (Context Menus - menu.addItem API)
   */
  private addMenuItem(menu: Menu, config: MenuItemConfig, context: MenuContext): void {
    menu.addItem((item) => {
      item.setTitle(config.title);

      if (config.icon && this.settings.showMenuIcons) {
        item.setIcon(config.icon);
      }

      item.onClick(async () => {
        try {
          this.log(`ContextMenuManager: Menu item clicked - ${config.id}`);
          await config.action();
        } catch (error) {
          const message = error instanceof Error ? error.message : '未知错误';
          console.error(`Menu action failed: ${config.id}`, error);
          new Notice(`操作失败: ${message}`);
        }
      });
    });
  }

  /**
   * Get menu items for a specific context
   */
  private getMenuItemsForContext(contextType: MenuContextType): MenuRegistryEntry[] {
    const items: MenuRegistryEntry[] = [];

    for (const entry of this.menuItems.values()) {
      if (entry.contexts.includes(contextType)) {
        items.push(entry);
      }
    }

    // Sort by priority (higher first)
    return items.sort((a, b) => b.priority - a.priority);
  }

  /**
   * Group menu items by section
   */
  private groupBySection(
    items: MenuRegistryEntry[]
  ): Record<string, MenuRegistryEntry[]> {
    const groups: Record<string, MenuRegistryEntry[]> = {
      primary: [],
      secondary: [],
      utility: [],
    };

    for (const entry of items) {
      const section = entry.config.section || 'utility';
      if (!groups[section]) {
        groups[section] = [];
      }
      groups[section].push(entry);
    }

    // Remove empty groups
    for (const key of Object.keys(groups)) {
      if (groups[key].length === 0) {
        delete groups[key];
      }
    }

    return groups;
  }

  /**
   * Get current context (for action callbacks)
   */
  private getCurrentContext(): MenuContext {
    const activeFile = this.app.workspace.getActiveFile();

    return {
      type: 'editor',
      filePath: activeFile?.path,
    };
  }

  // ============================================================================
  // Settings
  // ============================================================================

  /**
   * Update settings
   */
  updateSettings(settings: Partial<ContextMenuSettings>): void {
    this.settings = { ...this.settings, ...settings };
  }

  /**
   * Get current settings
   */
  getSettings(): ContextMenuSettings {
    return { ...this.settings };
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
    this.menuItems.clear();
    this.actionRegistry = {};
    this.log('ContextMenuManager: Cleaned up');
  }
}
