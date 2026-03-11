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
  ItemView,
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
import { ApiError } from '../api/types';
import { AgentErrorHandler } from '../errors';

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
  /** Execute comparison table - Story 12.F.2 */
  executeComparisonTable?: MenuActionCallback;
  // Story 25.1: Cross-Canvas UI Entry Points
  /** Open Cross-Canvas association modal */
  openCrossCanvasModal?: MenuActionCallback;
  /** View associated Canvas files */
  viewAssociatedCanvas?: MenuActionCallback;
  // 5 Additional Learning Agents
  /** Execute deep decomposition */
  executeDeepDecomposition?: MenuActionCallback;
  /** Execute clarification path */
  executeClarificationPath?: MenuActionCallback;
  /** Execute example teaching */
  executeExampleTeaching?: MenuActionCallback;
  /** Execute memory anchor */
  executeMemoryAnchor?: MenuActionCallback;
  /** Generate verification questions */
  generateVerificationQuestions?: MenuActionCallback;
  // Story 12.A.6: Question Decomposition Agent
  /** Decompose question into sub-questions */
  decomposeQuestion?: MenuActionCallback;
  // Story 35.5: Attach Media to Node
  /** Attach media file to node (opens AttachMediaModal) */
  attachMedia?: MenuActionCallback;
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
  // Epic 21.5.2: Canvas context缓存，修复getCurrentContext()返回错误路径问题
  private cachedCanvasContext: MenuContext | null = null;
  // Story 12.G.5: Unified Agent error handler
  private agentErrorHandler: AgentErrorHandler;

  constructor(
    app: App,
    backupProtectionManager: BackupProtectionManager,
    settings?: Partial<ContextMenuSettings>
  ) {
    this.app = app;
    this.backupProtectionManager = backupProtectionManager;
    this.settings = { ...DEFAULT_CONTEXT_MENU_SETTINGS, ...settings };
    // Story 12.G.5: Initialize Agent error handler
    this.agentErrorHandler = new AgentErrorHandler({ debug: false });
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
      const editorMenuRef = (this.app.workspace as any).on(
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
    if (this.settings.enableEditorMenu && 'registerDomEvent' in plugin) {
      (plugin as any).registerDomEvent(
        document,
        'contextmenu',
        (evt: MouseEvent) => {
          this.handleCanvasNodeContextMenu(evt);
        },
        true  // Use capture phase to intercept before Obsidian's handler
      );
      this.log('ContextMenuManager: Canvas DOM contextmenu event registered');
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
   * Get action registry for retry callbacks
   * @source Story 21.5.5 - AC 3: 可重试错误提供重试按钮
   */
  getActionRegistry(): MenuActionRegistry {
    return this.actionRegistry;
  }

  /**
   * Enable/disable debug mode
   */
  setDebugMode(enabled: boolean): void {
    this.debugMode = enabled;
  }

  /**
   * Set status bar element for error state display
   * @source Story 12.G.5: AC 5 - 错误状态持续展示
   */
  setStatusBarEl(el: HTMLElement): void {
    this.agentErrorHandler.setStatusBarEl(el);
  }

  /**
   * Get the Agent error handler instance
   * @source Story 12.G.5
   */
  getAgentErrorHandler(): AgentErrorHandler {
    return this.agentErrorHandler;
  }

  // ============================================================================
  // Built-in Menu Items
  // ============================================================================

  /**
   * Register built-in menu items
   */
  private registerBuiltInMenuItems(): void {
    // Primary actions - Decomposition
    // Epic 12.L: All actions now receive context directly instead of calling getCurrentContext()
    this.registerMenuItem({
      id: 'decompose-node',
      title: '拆解此节点 🔍',
      icon: 'git-branch',
      section: 'primary',
      description: '将复杂概念拆解为子问题',
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.executeDecomposition) {
          await this.actionRegistry.executeDecomposition(ctx);
        } else {
          console.error('[Story 12.K] executeDecomposition not registered!');
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
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.executeOralExplanation) {
          await this.actionRegistry.executeOralExplanation(ctx);
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
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.executeFourLevelExplanation) {
          await this.actionRegistry.executeFourLevelExplanation(ctx);
        } else {
          new Notice('四层次解答功能尚未初始化');
        }
      },
    }, ['editor', 'canvas-node'], 85);

    // Primary actions - Deep Decomposition
    this.registerMenuItem({
      id: 'deep-decomposition',
      title: '深度拆解 🔥',
      icon: 'flame',
      section: 'primary',
      description: '对复杂概念进行深度拆解分析',
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.executeDeepDecomposition) {
          await this.actionRegistry.executeDeepDecomposition(ctx);
        } else {
          console.error('[Story 12.K] executeDeepDecomposition not registered!');
          new Notice('深度拆解功能尚未初始化');
        }
      },
    }, ['editor', 'canvas-node'], 95);

    // Primary actions - Clarification Path
    this.registerMenuItem({
      id: 'clarification-path',
      title: '澄清路径 📈',
      icon: 'trending-up',
      section: 'primary',
      description: '生成系统化澄清路径',
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.executeClarificationPath) {
          await this.actionRegistry.executeClarificationPath(ctx);
        } else {
          new Notice('澄清路径功能尚未初始化');
        }
      },
    }, ['editor', 'canvas-node'], 82);

    // Secondary actions - Scoring
    this.registerMenuItem({
      id: 'score-node',
      title: '评分此节点 ⭐',
      icon: 'star',
      section: 'secondary',
      description: '对节点内容进行4维评分',
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.executeScoring) {
          await this.actionRegistry.executeScoring(ctx);
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
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.generateComparisonTable) {
          await this.actionRegistry.generateComparisonTable(ctx);
        } else {
          new Notice('对比表生成功能尚未初始化');
        }
      },
    }, ['editor', 'canvas-node'], 75);

    // Secondary actions - Example Teaching
    this.registerMenuItem({
      id: 'example-teaching',
      title: '例题教学 📝',
      icon: 'book-open',
      section: 'secondary',
      description: '生成例题和详细解答',
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.executeExampleTeaching) {
          await this.actionRegistry.executeExampleTeaching(ctx);
        } else {
          new Notice('例题教学功能尚未初始化');
        }
      },
    }, ['editor', 'canvas-node'], 72);

    // Secondary actions - Memory Anchor
    this.registerMenuItem({
      id: 'memory-anchor',
      title: '记忆锚点 🎯',
      icon: 'anchor',
      section: 'secondary',
      description: '生成生动类比和记忆法',
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.executeMemoryAnchor) {
          await this.actionRegistry.executeMemoryAnchor(ctx);
        } else {
          new Notice('记忆锚点功能尚未初始化');
        }
      },
    }, ['editor', 'canvas-node'], 70);

    // Secondary actions - Verification Questions
    this.registerMenuItem({
      id: 'verification-questions',
      title: '生成检验问题 ❓',
      icon: 'help-circle',
      section: 'secondary',
      description: '生成深度检验问题测试理解',
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.generateVerificationQuestions) {
          await this.actionRegistry.generateVerificationQuestions(ctx);
        } else {
          new Notice('检验问题功能尚未初始化');
        }
      },
    }, ['editor', 'canvas-node'], 68);

    // Story 12.A.6: Question Decomposition
    this.registerMenuItem({
      id: 'decompose-question',
      title: '问题拆解 🔀',
      icon: 'split',
      section: 'secondary',
      description: '将检验问题拆解为子问题',
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.decomposeQuestion) {
          await this.actionRegistry.decomposeQuestion(ctx);
        } else {
          new Notice('问题拆解功能尚未初始化');
        }
      },
    }, ['editor', 'canvas-node'], 66);

    // Utility actions - Node History
    this.registerMenuItem({
      id: 'view-history',
      title: '查看节点历史 🕐',
      icon: 'history',
      section: 'utility',
      description: '查看此节点的学习历史',
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.viewNodeHistory) {
          await this.actionRegistry.viewNodeHistory(ctx);
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
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.addToReviewPlan) {
          await this.actionRegistry.addToReviewPlan(ctx);
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
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.openReviewDashboard) {
          await this.actionRegistry.openReviewDashboard(ctx);
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
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.generateVerificationCanvas) {
          await this.actionRegistry.generateVerificationCanvas(ctx);
        } else {
          new Notice('检验白板功能尚未初始化');
        }
      },
    }, ['file'], 90);

    // =========================================================================
    // Story 25.1: Cross-Canvas UI Entry Points
    // =========================================================================

    // Cross-Canvas - Associate to Other Canvas
    // AC1: Right-click menu "关联到其他Canvas"
    this.registerMenuItem({
      id: 'cross-canvas-associate',
      title: '关联到其他Canvas 🔗',
      icon: 'link',
      section: 'utility',
      description: '创建与其他Canvas的关联',
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.openCrossCanvasModal) {
          await this.actionRegistry.openCrossCanvasModal(ctx);
        } else {
          new Notice('跨Canvas关联功能尚未初始化');
        }
      },
    }, ['editor', 'canvas-node', 'file'], 40);

    // Cross-Canvas - View Associated Canvas
    // AC2: Right-click menu "查看关联Canvas"
    this.registerMenuItem({
      id: 'view-associated-canvas',
      title: '查看关联Canvas 📋',
      icon: 'external-link',
      section: 'utility',
      description: '查看并跳转到关联的Canvas',
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.viewAssociatedCanvas) {
          await this.actionRegistry.viewAssociatedCanvas(ctx);
        } else {
          new Notice('查看关联功能尚未初始化');
        }
      },
    }, ['editor', 'canvas-node', 'file'], 35);

    // =========================================================================
    // Story 35.5: Attach Media to Node
    // AC 35.5.1: Right-click menu "附加媒体文件"
    // =========================================================================
    this.registerMenuItem({
      id: 'attach-media',
      title: '附加媒体文件 📎',
      icon: 'paperclip',
      section: 'utility',
      description: '附加图片/PDF/音视频到此节点',
      condition: (ctx: MenuContext) => ctx.nodeType === 'text',
      action: async (ctx: MenuContext) => {
        if (this.actionRegistry.attachMedia) {
          await this.actionRegistry.attachMedia(ctx);
        } else {
          new Notice('附加媒体功能尚未初始化');
        }
      },
    }, ['canvas-node'], 30);

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
  private async handleEditorMenu(menu: Menu, editor: Editor, view: MarkdownView): Promise<void> {
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
        if (entry.config.condition) {
          const result = entry.config.condition(context);
          const shouldShow = result instanceof Promise ? await result : result;
          if (!shouldShow) continue;
        }
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

    const activeLeaf = this.app.workspace.activeLeaf;
    if (!activeLeaf) {
      return null;
    }

    const view = activeLeaf.view;

    // FIX: Use view.file instead of getActiveFile()
    // getActiveFile() returns the embedded note, not the canvas file itself!
    // view.file correctly returns the canvas file being viewed
    const file = (view as any)?.file as TFile | undefined;

    // Check if it's a Canvas file
    if (!file || file.extension !== 'canvas') {
      return null;
    }

    // Access Canvas internal API (undocumented but stable since v1.1)
    const canvas = (view as any)?.canvas;

    if (!canvas) {
      return null;
    }

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

    // Walk up the DOM tree to find the canvas node element
    let current: HTMLElement | null = element;

    while (current && !current.classList.contains('canvas-node')) {
      current = current.parentElement;
    }

    if (!current) {
      return null;
    }

    // Get Canvas view first
    const canvasView = this.getActiveCanvasView();
    if (!canvasView) {
      return null;
    }

    // Method 1: Try data-node-id attribute first
    const dataNodeId = current.getAttribute('data-node-id');
    if (dataNodeId) {
      const nodeData = canvasView.canvas.nodes.get(dataNodeId);
      if (nodeData) {
        return { nodeId: dataNodeId, nodeEl: current, nodeData };
      }
    }

    // Method 2: Match DOM element to canvas.nodes by their nodeEl property

    // canvas.nodes is a Map<string, CanvasNode>
    // Each CanvasNode has a nodeEl property pointing to its DOM element
    for (const [nodeId, nodeData] of canvasView.canvas.nodes) {

      // Check if the node's DOM element matches or contains our clicked element
      const nodeEl = (nodeData as any)?.nodeEl as HTMLElement | undefined;
      if (nodeEl && (nodeEl === current || nodeEl.contains(current) || current.contains(nodeEl))) {
        return { nodeId, nodeEl: current, nodeData };
      }
    }

    // Method 3: Check canvas.selection for currently selected nodes
    const selection = canvasView.canvas.selection;

    if (selection && selection.size > 0) {
      // Get first selected node
      const selectedNode = selection.values().next().value;
      if (selectedNode) {
        const selectedNodeEl = (selectedNode as any)?.nodeEl as HTMLElement | undefined;

        if (selectedNodeEl && (selectedNodeEl === current || selectedNodeEl.contains(current) || current.contains(selectedNodeEl))) {
          const nodeId = (selectedNode as any)?.id || 'unknown';
          return { nodeId, nodeEl: current, nodeData: selectedNode };
        }
      }
    }

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
  private async handleCanvasNodeContextMenu(evt: MouseEvent): Promise<void> {

    const target = evt.target as HTMLElement;
    if (!target) {
      return;
    }

    // Check if we're in a Canvas view
    const canvasView = this.getActiveCanvasView();
    if (!canvasView) {
      return;
    }

    // Check if clicked element is inside a Canvas node
    const nodeInfo = this.getNodeFromElement(target);
    if (!nodeInfo) {
      return;
    }

    this.log(`ContextMenuManager: Canvas node right-click detected - ${nodeInfo.nodeId}`);

    // Prevent default context menu and stop propagation
    evt.preventDefault();
    evt.stopPropagation();

    // Story 12.F.3: Support both TEXT and FILE node types
    // ✅ FIX: Obsidian Canvas internal node object doesn't have 'type' property
    // Must detect type by checking existence of 'file' or 'text' properties
    let nodeContent: string | undefined;
    let detectedNodeType: 'text' | 'file' | undefined = undefined;

    // ✅ FIX: Check for 'file' property first (TFile object or path string)
    if (nodeInfo.nodeData?.file) {
      detectedNodeType = 'file';
      // FILE type: Read linked MD file content
      // nodeData.file can be a TFile object or a path string
      const fileRef = nodeInfo.nodeData.file;
      let filePath: string;

      if (typeof fileRef === 'string') {
        filePath = fileRef;
      } else if (fileRef && typeof fileRef === 'object' && 'path' in fileRef) {
        // TFile object has 'path' property
        filePath = (fileRef as any).path;
      } else {
        console.warn('[Story 12.F.3] Cannot determine file path from:', fileRef);
        filePath = '';
      }

      if (filePath) {
        // Check if file is an image/binary — don't read binary, use embed syntax instead
        const IMAGE_EXTS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'];
        const lowerPath = filePath.toLowerCase();
        const isImage = IMAGE_EXTS.some(ext => lowerPath.endsWith(ext));

        if (isImage) {
          // Image file: use ![[embed]] syntax so backend MarkdownImageExtractor can resolve it
          nodeContent = `![[${filePath}]]`;
          console.log(`[Story 12.F.3] Image file node: using embed syntax for ${filePath}`);
        } else {
          const abstractFile = this.app.vault.getAbstractFileByPath(filePath);
          if (abstractFile instanceof TFile) {
            try {
              // Use cachedRead for text files (md, pdf, etc.)
              nodeContent = await this.app.vault.cachedRead(abstractFile);
            } catch (error) {
              console.error(`[Story 12.F.3] Failed to read FILE node: ${filePath}`, error);
              nodeContent = `![[${filePath}]]`;  // Fallback to embed syntax
            }
          } else {
            console.warn(`[Story 12.F.3] File not found in vault: ${filePath}`);
            nodeContent = `![[${filePath}]]`;  // Fallback to embed syntax
          }
        }
      }
    } else if (nodeInfo.nodeData?.text !== undefined) {
      // TEXT type: Read directly from node data
      detectedNodeType = 'text';
      nodeContent = nodeInfo.nodeData.text;
    }

    // Build context with node information
    // Story 12.F.3: Use detectedNodeType instead of nodeInfo.nodeData?.type
    const context: MenuContext = {
      type: 'canvas-node',
      filePath: canvasView.file.path,
      nodeId: nodeInfo.nodeId,
      nodeColor: nodeInfo.nodeData?.color as CanvasNodeColor,
      nodeType: detectedNodeType,  // Story 12.F.3: Use detected type
      nodeContent: nodeContent,  // Story 12.B.2: Pass real-time content
    };

    // Epic 21.5.2: Cache canvas context for use in action handlers
    this.cachedCanvasContext = context;
    this.log(`ContextMenuManager: Canvas context cache set - filePath=${context.filePath}`);

    // Create menu
    const menu = new Menu();

    // Epic 21.5.2: Register menu hide callback for cache cleanup
    menu.onHide(() => {
      this.cachedCanvasContext = null;
      this.log('ContextMenuManager: Canvas context cache cleared (menu hidden)');
    });

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
        if (entry.config.condition) {
          const result = entry.config.condition(context);
          const shouldShow = result instanceof Promise ? await result : result;
          if (!shouldShow) continue;
        }
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

      // Story 12.G.5: Unified Agent error handling with retry support
      // Epic 12.L: Pass context directly to action to fix cache race condition
      item.onClick(async () => {
        try {
          this.log(`ContextMenuManager: Menu item clicked - ${config.id}`);
          await config.action(context);
        } catch (error) {
          // Story 12.G.5: Use AgentErrorHandler for ApiError instances
          if (error instanceof ApiError) {
            await this.agentErrorHandler.handleError(error, async () => {
              // Retry callback: re-execute the same action with same context
              await config.action(context);
            });
          } else {
            // Fallback for non-ApiError errors
            const message = error instanceof Error ? error.message : '未知错误';
            console.error(`Menu action failed: ${config.id}`, error);
            new Notice(`操作失败: ${message}`);
          }
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
   * Epic 21.5.2: Returns cached canvas context if available, otherwise falls back to editor context
   */
  private getCurrentContext(): MenuContext {
    // Epic 21.5.2: Prioritize returning cached canvas context
    if (this.cachedCanvasContext) {
      const cached = this.cachedCanvasContext;
      this.cachedCanvasContext = null; // Clear after use to prevent pollution
      this.log(`ContextMenuManager: Using cached canvas context - filePath=${cached.filePath}`);
      return cached;
    }

    // Fallback to original logic for editor context
    this.log('ContextMenuManager: No cached context, using getActiveFile()');
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
      console.debug(message);
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
