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

    // Register Canvas node context menu via DOM event interception
    // Story 13.5 Fix: Canvas views don't trigger 'editor-menu' event
    // We must intercept contextmenu DOM events directly
    // ✅ Verified from @obsidian-canvas Skill (Plugin Development - registerDomEvent)
    console.log('[DEBUG-CANVAS] Checking DOM event registration conditions:', {
      enableEditorMenu: this.settings.enableEditorMenu,
      hasRegisterDomEvent: 'registerDomEvent' in plugin
    });
    if (this.settings.enableEditorMenu && 'registerDomEvent' in plugin) {
      console.log('[DEBUG-CANVAS] Registering DOM contextmenu event listener');
      (plugin as any).registerDomEvent(
        document,
        'contextmenu',
        (evt: MouseEvent) => {
          console.log('[DEBUG-CANVAS] DOM contextmenu event received');
          this.handleCanvasNodeContextMenu(evt);
        },
        true  // Use capture phase to intercept before Obsidian's handler
      );
      this.log('ContextMenuManager: Canvas DOM contextmenu event registered');
      console.log('[DEBUG-CANVAS] DOM contextmenu event registered successfully');
    } else {
      console.log('[DEBUG-CANVAS] SKIP: DOM event not registered', {
        enableEditorMenu: this.settings.enableEditorMenu,
        hasRegisterDomEvent: 'registerDomEvent' in plugin
      });
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
    }, ['editor', 'canvas-node'], 100);

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
    }, ['editor', 'canvas-node'], 90);

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
    }, ['editor', 'canvas-node'], 85);

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
    }, ['editor', 'canvas-node'], 80);

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
    }, ['editor', 'canvas-node'], 75);

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
    }, ['editor', 'canvas-node'], 50);

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
    }, ['editor', 'canvas-node'], 45);

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
    // Use synchronous method to avoid timing issues with menu display
    if (context.isBackupFile) {
      this.addBackupProtectionMenuItemSync(menu, file.path);
    }
  }

  /**
   * Add backup protection menu item (async version)
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

  /**
   * Add backup protection menu item (synchronous version)
   * Uses sync protection check to avoid timing issues with menu display.
   *
   * Story 13.5: AC 3 - SCP-003 backup protection
   */
  private addBackupProtectionMenuItemSync(menu: Menu, filePath: string): void {
    // Use synchronous check - returns false if data not loaded yet
    const isProtected = this.backupProtectionManager.isProtectedSync(filePath);

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
  // Canvas Node Detection (Story 13.5 - Canvas DOM Event Fix)
  // ============================================================================

  /**
   * Get active Canvas view if current view is a Canvas
   *
   * Uses internal Canvas API to access node data.
   * ✅ Verified from @obsidian-canvas Skill (Canvas Internal API)
   */
  private getActiveCanvasView(): { view: any; canvas: any; file: TFile } | null {
    console.log('[DEBUG-CANVAS] getActiveCanvasView() called');

    const activeLeaf = this.app.workspace.activeLeaf;
    if (!activeLeaf) {
      console.log('[DEBUG-CANVAS] FAIL: no activeLeaf');
      return null;
    }
    console.log('[DEBUG-CANVAS] activeLeaf exists, viewType:', activeLeaf.view?.getViewType?.());

    const view = activeLeaf.view;

    // FIX: Use view.file instead of getActiveFile()
    // getActiveFile() returns the embedded note, not the canvas file itself!
    // view.file correctly returns the canvas file being viewed
    const file = (view as any)?.file as TFile | undefined;

    // Check if it's a Canvas file
    if (!file || file.extension !== 'canvas') {
      console.log('[DEBUG-CANVAS] FAIL: not canvas file', {
        file: file?.path,
        ext: file?.extension
      });
      return null;
    }
    console.log('[DEBUG-CANVAS] canvas file confirmed:', file.path);

    // Access Canvas internal API (undocumented but stable since v1.1)
    const canvas = (view as any)?.canvas;
    console.log('[DEBUG-CANVAS] view.canvas =', canvas);
    console.log('[DEBUG-CANVAS] view keys:', Object.keys(view || {}));

    if (!canvas) {
      console.log('[DEBUG-CANVAS] FAIL: view.canvas is undefined/null');
      return null;
    }

    console.log('[DEBUG-CANVAS] SUCCESS: getActiveCanvasView()');
    return { view, canvas, file };
  }

  /**
   * Extract node information from a DOM element
   *
   * Walks up the DOM tree to find the canvas-node container
   * and extracts node data from Canvas internal API.
   *
   * FIX: Obsidian Canvas doesn't always use data-node-id attribute.
   * We need to match the DOM element to canvas.nodes entries by their
   * internal nodeEl reference.
   */
  private getNodeFromElement(element: HTMLElement): {
    nodeId: string;
    nodeEl: HTMLElement;
    nodeData: any;
  } | null {
    console.log('[DEBUG-CANVAS] getNodeFromElement() called on:', element?.tagName, element?.className);

    // Walk up the DOM tree to find the canvas node element
    let current: HTMLElement | null = element;

    while (current && !current.classList.contains('canvas-node')) {
      current = current.parentElement;
    }

    if (!current) {
      console.log('[DEBUG-CANVAS] FAIL: no .canvas-node ancestor found');
      return null;
    }
    console.log('[DEBUG-CANVAS] Found .canvas-node element');
    console.log('[DEBUG-CANVAS] .canvas-node attributes:', Array.from(current.attributes).map(a => `${a.name}=${a.value}`));

    // Get Canvas view first
    const canvasView = this.getActiveCanvasView();
    if (!canvasView) {
      console.log('[DEBUG-CANVAS] FAIL: getActiveCanvasView returned null in getNodeFromElement');
      return null;
    }

    // Method 1: Try data-node-id attribute first
    const dataNodeId = current.getAttribute('data-node-id');
    if (dataNodeId) {
      console.log('[DEBUG-CANVAS] Found data-node-id:', dataNodeId);
      const nodeData = canvasView.canvas.nodes.get(dataNodeId);
      if (nodeData) {
        console.log('[DEBUG-CANVAS] SUCCESS: getNodeFromElement() via data-node-id');
        return { nodeId: dataNodeId, nodeEl: current, nodeData };
      }
    }

    // Method 2: Match DOM element to canvas.nodes by their nodeEl property
    console.log('[DEBUG-CANVAS] Trying to match via canvas.nodes iteration');
    console.log('[DEBUG-CANVAS] canvas.nodes type:', typeof canvasView.canvas.nodes);
    console.log('[DEBUG-CANVAS] canvas.nodes size:', canvasView.canvas.nodes?.size);

    // canvas.nodes is a Map<string, CanvasNode>
    // Each CanvasNode has a nodeEl property pointing to its DOM element
    for (const [nodeId, nodeData] of canvasView.canvas.nodes) {
      console.log('[DEBUG-CANVAS] Checking node:', nodeId, 'nodeEl:', nodeData?.nodeEl?.tagName);

      // Check if the node's DOM element matches or contains our clicked element
      const nodeEl = (nodeData as any)?.nodeEl as HTMLElement | undefined;
      if (nodeEl && (nodeEl === current || nodeEl.contains(current) || current.contains(nodeEl))) {
        console.log('[DEBUG-CANVAS] SUCCESS: Matched node via nodeEl reference, id=', nodeId);
        return { nodeId, nodeEl: current, nodeData };
      }
    }

    // Method 3: Check canvas.selection for currently selected nodes
    console.log('[DEBUG-CANVAS] Trying canvas.selection');
    const selection = canvasView.canvas.selection;
    console.log('[DEBUG-CANVAS] canvas.selection:', selection);
    console.log('[DEBUG-CANVAS] canvas.selection size:', selection?.size);

    if (selection && selection.size > 0) {
      // Get first selected node
      const selectedNode = selection.values().next().value;
      if (selectedNode) {
        const selectedNodeEl = (selectedNode as any)?.nodeEl as HTMLElement | undefined;
        console.log('[DEBUG-CANVAS] Selected node element:', selectedNodeEl?.tagName, selectedNodeEl?.className);

        if (selectedNodeEl && (selectedNodeEl === current || selectedNodeEl.contains(current) || current.contains(selectedNodeEl))) {
          const nodeId = (selectedNode as any)?.id || 'unknown';
          console.log('[DEBUG-CANVAS] SUCCESS: Matched via canvas.selection, id=', nodeId);
          return { nodeId, nodeEl: current, nodeData: selectedNode };
        }
      }
    }

    console.log('[DEBUG-CANVAS] FAIL: Could not match DOM element to any canvas node');
    return null;
  }

  /**
   * Handle context menu on Canvas nodes (DOM interception)
   *
   * Since Obsidian doesn't expose canvas-node-menu event,
   * we intercept contextmenu DOM events and check if target
   * is a Canvas node.
   *
   * Story 13.5: Canvas node right-click menu fix
   */
  private handleCanvasNodeContextMenu(evt: MouseEvent): void {
    console.log('[DEBUG-CANVAS] ====== handleCanvasNodeContextMenu TRIGGERED ======');
    console.log('[DEBUG-CANVAS] evt.target:', evt.target);

    const target = evt.target as HTMLElement;
    if (!target) {
      console.log('[DEBUG-CANVAS] FAIL: no target');
      return;
    }
    console.log('[DEBUG-CANVAS] target element:', target.tagName, target.className);

    // Check if we're in a Canvas view
    const canvasView = this.getActiveCanvasView();
    if (!canvasView) {
      console.log('[DEBUG-CANVAS] FAIL: not in canvas view, skipping custom menu');
      return;
    }

    // Check if clicked element is inside a Canvas node
    const nodeInfo = this.getNodeFromElement(target);
    if (!nodeInfo) {
      console.log('[DEBUG-CANVAS] FAIL: target not in a canvas node, skipping custom menu');
      return;
    }

    console.log('[DEBUG-CANVAS] SUCCESS: All checks passed, showing custom menu');
    this.log(`ContextMenuManager: Canvas node right-click detected - ${nodeInfo.nodeId}`);

    // Prevent default context menu and stop propagation
    evt.preventDefault();
    evt.stopPropagation();

    // Build context with node information
    const context: MenuContext = {
      type: 'canvas-node',
      filePath: canvasView.file.path,
      nodeId: nodeInfo.nodeId,
      nodeColor: nodeInfo.nodeData?.color as CanvasNodeColor,
      nodeType: nodeInfo.nodeData?.type,
    };

    // Create menu
    const menu = new Menu();

    // Get relevant menu items for canvas-node context
    const items = this.getMenuItemsForContext('canvas-node');

    // Group by section
    const sections = this.groupBySection(items);

    // Add items to menu
    let isFirstSection = true;
    for (const [section, sectionItems] of Object.entries(sections)) {
      if (!isFirstSection) {
        menu.addSeparator();
      }
      isFirstSection = false;

      for (const entry of sectionItems) {
        this.addMenuItem(menu, entry.config, context);
      }
    }

    // Show menu at mouse position
    menu.showAtMouseEvent(evt);
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
