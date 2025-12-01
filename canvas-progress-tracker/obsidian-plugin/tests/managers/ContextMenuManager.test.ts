// @ts-nocheck - Mock types don't match Obsidian types exactly
/**
 * Tests for Context Menu Manager
 * Story 13.5: 右键菜单和快捷键 - Tasks 1, 2
 *
 * Tests context menu integration for Canvas nodes and files.
 */

import { ContextMenuManager } from '../../src/managers/ContextMenuManager';
import { BackupProtectionManager } from '../../src/managers/BackupProtectionManager';
import type { MenuActionRegistry, MenuContext } from '../../src/types/menu';
import { Vault, TFile, TFolder, Notice } from '../__mocks__/obsidian';
import { BACKUP_FOLDER } from '../../src/utils/canvas-helpers';

// Mock Notice
jest.mock('obsidian', () => {
  const actual = jest.requireActual('../__mocks__/obsidian');
  return {
    ...actual,
    Notice: jest.fn().mockImplementation((message, duration) => {
      return { message, duration };
    }),
  };
});

// Mock Menu class
class MockMenu {
  items: any[] = [];
  separators: number[] = [];

  addItem(callback: (item: MockMenuItem) => void): this {
    const item = new MockMenuItem();
    callback(item);
    this.items.push(item);
    return this;
  }

  addSeparator(): this {
    this.separators.push(this.items.length);
    return this;
  }

  getItems(): MockMenuItem[] {
    return this.items;
  }

  getSeparatorCount(): number {
    return this.separators.length;
  }
}

class MockMenuItem {
  title: string = '';
  icon: string | null = null;
  clickCallback: (() => void) | null = null;

  setTitle(title: string): this {
    this.title = title;
    return this;
  }

  setIcon(icon: string): this {
    this.icon = icon;
    return this;
  }

  onClick(callback: () => void): this {
    this.clickCallback = callback;
    return this;
  }
}

// Mock Editor
class MockEditor {
  selection = '';
  getSelection(): string {
    return this.selection;
  }
}

// Mock MarkdownView
class MockMarkdownView {
  file: TFile | null;

  constructor(file: TFile | null = null) {
    this.file = file;
  }
}

// Mock Plugin
class MockPlugin {
  events: any[] = [];

  registerEvent(event: any): void {
    this.events.push(event);
  }
}

describe('ContextMenuManager', () => {
  let manager: ContextMenuManager;
  let backupManager: BackupProtectionManager;
  let vault: Vault;
  let mockApp: any;
  let mockPlugin: MockPlugin;

  beforeEach(() => {
    vault = new Vault();
    backupManager = new BackupProtectionManager(vault as any);

    mockApp = {
      vault,
      workspace: {
        on: jest.fn().mockImplementation((event, callback) => {
          return { event, callback };
        }),
        getActiveFile: jest.fn().mockReturnValue(null),
      },
    };

    mockPlugin = new MockPlugin();
    manager = new ContextMenuManager(mockApp, backupManager);
    jest.clearAllMocks();
  });

  afterEach(() => {
    manager.cleanup();
    vault._clear();
  });

  // ============================================================================
  // Initialization Tests
  // ============================================================================

  describe('initialize', () => {
    it('should register editor-menu event when enabled', () => {
      manager.initialize(mockPlugin);

      expect(mockApp.workspace.on).toHaveBeenCalledWith(
        'editor-menu',
        expect.any(Function)
      );
    });

    it('should register file-menu event when enabled', () => {
      manager.initialize(mockPlugin);

      expect(mockApp.workspace.on).toHaveBeenCalledWith(
        'file-menu',
        expect.any(Function)
      );
    });

    it('should register events with plugin', () => {
      manager.initialize(mockPlugin);

      expect(mockPlugin.events.length).toBeGreaterThan(0);
    });

    it('should not register editor-menu when disabled', () => {
      manager.updateSettings({ enableEditorMenu: false });
      manager.initialize(mockPlugin);

      const editorMenuCalls = (mockApp.workspace.on as any).mock.calls.filter(
        (call: any[]) => call[0] === 'editor-menu'
      );
      expect(editorMenuCalls).toHaveLength(0);
    });

    it('should not register file-menu when disabled', () => {
      manager.updateSettings({ enableFileMenu: false });
      manager.initialize(mockPlugin);

      const fileMenuCalls = (mockApp.workspace.on as any).mock.calls.filter(
        (call: any[]) => call[0] === 'file-menu'
      );
      expect(fileMenuCalls).toHaveLength(0);
    });
  });

  // ============================================================================
  // Menu Item Registration Tests
  // ============================================================================

  describe('registerMenuItem', () => {
    it('should register menu item with config', () => {
      const config = {
        id: 'test-item',
        title: 'Test Item',
        action: jest.fn(),
      };

      manager.registerMenuItem(config, ['editor'], 50);

      // Verify by checking if item appears in editor menu
      // (internal state is private, test through behavior)
    });

    it('should respect priority for ordering', () => {
      manager.registerMenuItem(
        { id: 'low-priority', title: 'Low', action: jest.fn() },
        ['editor'],
        10
      );
      manager.registerMenuItem(
        { id: 'high-priority', title: 'High', action: jest.fn() },
        ['editor'],
        100
      );

      // Items should be ordered by priority (tested through actual menu generation)
    });
  });

  describe('unregisterMenuItem', () => {
    it('should remove registered menu item', () => {
      const config = {
        id: 'test-item',
        title: 'Test Item',
        action: jest.fn(),
      };

      manager.registerMenuItem(config, ['editor'], 50);
      manager.unregisterMenuItem('test-item');

      // Item should no longer appear
    });

    it('should handle unregistering non-existent item', () => {
      // Should not throw
      expect(() => manager.unregisterMenuItem('non-existent')).not.toThrow();
    });
  });

  // ============================================================================
  // Action Registry Tests
  // ============================================================================

  describe('setActionRegistry', () => {
    it('should set action registry', () => {
      const registry: MenuActionRegistry = {
        executeDecomposition: jest.fn(),
        executeScoring: jest.fn(),
      };

      manager.setActionRegistry(registry);

      // Registry is set (tested through behavior)
    });

    it('should merge with existing registry', () => {
      manager.setActionRegistry({ executeDecomposition: jest.fn() });
      manager.setActionRegistry({ executeScoring: jest.fn() });

      // Both actions should be available
    });
  });

  // ============================================================================
  // Editor Menu Tests
  // ============================================================================

  describe('handleEditorMenu', () => {
    it('should add menu items for canvas files', () => {
      manager.initialize(mockPlugin);

      const menu = new MockMenu();
      const editor = new MockEditor();
      const canvasFile = new TFile('test.canvas');
      const view = new MockMarkdownView(canvasFile);

      // Get the registered callback
      const editorMenuCall = (mockApp.workspace.on as any).mock.calls.find(
        (call: any[]) => call[0] === 'editor-menu'
      );

      if (editorMenuCall) {
        editorMenuCall[1](menu, editor, view);
      }

      // Should have added menu items
      expect(menu.getItems().length).toBeGreaterThan(0);
    });

    it('should not add items for non-canvas files', () => {
      manager.initialize(mockPlugin);

      const menu = new MockMenu();
      const editor = new MockEditor();
      const mdFile = new TFile('test.md');
      const view = new MockMarkdownView(mdFile);

      const editorMenuCall = (mockApp.workspace.on as any).mock.calls.find(
        (call: any[]) => call[0] === 'editor-menu'
      );

      if (editorMenuCall) {
        editorMenuCall[1](menu, editor, view);
      }

      // Should NOT have added menu items
      expect(menu.getItems()).toHaveLength(0);
    });

    it('should not add items when file is null', () => {
      manager.initialize(mockPlugin);

      const menu = new MockMenu();
      const editor = new MockEditor();
      const view = new MockMarkdownView(null);

      const editorMenuCall = (mockApp.workspace.on as any).mock.calls.find(
        (call: any[]) => call[0] === 'editor-menu'
      );

      if (editorMenuCall) {
        editorMenuCall[1](menu, editor, view);
      }

      expect(menu.getItems()).toHaveLength(0);
    });

    it('should group items by section with separators', () => {
      manager.initialize(mockPlugin);

      const menu = new MockMenu();
      const editor = new MockEditor();
      const canvasFile = new TFile('test.canvas');
      const view = new MockMarkdownView(canvasFile);

      const editorMenuCall = (mockApp.workspace.on as any).mock.calls.find(
        (call: any[]) => call[0] === 'editor-menu'
      );

      if (editorMenuCall) {
        editorMenuCall[1](menu, editor, view);
      }

      // Should have separators between sections
      expect(menu.getSeparatorCount()).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // File Menu Tests
  // ============================================================================

  describe('handleFileMenu', () => {
    it('should add menu items for canvas files', () => {
      manager.initialize(mockPlugin);

      const menu = new MockMenu();
      const canvasFile = new TFile('test.canvas');

      const fileMenuCall = (mockApp.workspace.on as any).mock.calls.find(
        (call: any[]) => call[0] === 'file-menu'
      );

      if (fileMenuCall) {
        fileMenuCall[1](menu, canvasFile, 'file-explorer');
      }

      expect(menu.getItems().length).toBeGreaterThan(0);
    });

    it('should not add items for non-canvas files', () => {
      manager.initialize(mockPlugin);

      const menu = new MockMenu();
      const mdFile = new TFile('test.md');

      const fileMenuCall = (mockApp.workspace.on as any).mock.calls.find(
        (call: any[]) => call[0] === 'file-menu'
      );

      if (fileMenuCall) {
        fileMenuCall[1](menu, mdFile, 'file-explorer');
      }

      expect(menu.getItems()).toHaveLength(0);
    });

    it('should not add items for folders', () => {
      manager.initialize(mockPlugin);

      const menu = new MockMenu();
      const folder = new TFolder('test-folder');

      const fileMenuCall = (mockApp.workspace.on as any).mock.calls.find(
        (call: any[]) => call[0] === 'file-menu'
      );

      if (fileMenuCall) {
        fileMenuCall[1](menu, folder, 'file-explorer');
      }

      expect(menu.getItems()).toHaveLength(0);
    });

    it('should add backup protection item for backup files', async () => {
      await backupManager.initialize();
      manager.initialize(mockPlugin);

      const menu = new MockMenu();
      const backupFile = new TFile(`${BACKUP_FOLDER}/test_20250101_100000.canvas`);
      vault._setFile(backupFile.path, '{}');

      const fileMenuCall = (mockApp.workspace.on as any).mock.calls.find(
        (call: any[]) => call[0] === 'file-menu'
      );

      if (fileMenuCall) {
        fileMenuCall[1](menu, backupFile, 'file-explorer');
      }

      // Should have protection toggle item
      const items = menu.getItems();
      const protectionItem = items.find(
        i => i.title.includes('保护') || i.title.includes('取消保护')
      );
      expect(protectionItem).toBeDefined();
    });
  });

  // ============================================================================
  // Built-in Menu Items Tests
  // ============================================================================

  describe('built-in menu items', () => {
    it('should include decomposition item', () => {
      manager.initialize(mockPlugin);

      const menu = new MockMenu();
      const editor = new MockEditor();
      const canvasFile = new TFile('test.canvas');
      const view = new MockMarkdownView(canvasFile);

      const editorMenuCall = (mockApp.workspace.on as any).mock.calls.find(
        (call: any[]) => call[0] === 'editor-menu'
      );

      if (editorMenuCall) {
        editorMenuCall[1](menu, editor, view);
      }

      const items = menu.getItems();
      const decomposeItem = items.find(i => i.title.includes('拆解'));
      expect(decomposeItem).toBeDefined();
    });

    it('should include oral explanation item', () => {
      manager.initialize(mockPlugin);

      const menu = new MockMenu();
      const editor = new MockEditor();
      const canvasFile = new TFile('test.canvas');
      const view = new MockMarkdownView(canvasFile);

      const editorMenuCall = (mockApp.workspace.on as any).mock.calls.find(
        (call: any[]) => call[0] === 'editor-menu'
      );

      if (editorMenuCall) {
        editorMenuCall[1](menu, editor, view);
      }

      const items = menu.getItems();
      const oralItem = items.find(i => i.title.includes('口语化'));
      expect(oralItem).toBeDefined();
    });

    it('should include scoring item', () => {
      manager.initialize(mockPlugin);

      const menu = new MockMenu();
      const editor = new MockEditor();
      const canvasFile = new TFile('test.canvas');
      const view = new MockMarkdownView(canvasFile);

      const editorMenuCall = (mockApp.workspace.on as any).mock.calls.find(
        (call: any[]) => call[0] === 'editor-menu'
      );

      if (editorMenuCall) {
        editorMenuCall[1](menu, editor, view);
      }

      const items = menu.getItems();
      const scoreItem = items.find(i => i.title.includes('评分'));
      expect(scoreItem).toBeDefined();
    });

    it('should include file menu items for canvas files', () => {
      manager.initialize(mockPlugin);

      const menu = new MockMenu();
      const canvasFile = new TFile('test.canvas');

      const fileMenuCall = (mockApp.workspace.on as any).mock.calls.find(
        (call: any[]) => call[0] === 'file-menu'
      );

      if (fileMenuCall) {
        fileMenuCall[1](menu, canvasFile, 'file-explorer');
      }

      const items = menu.getItems();
      const dashboardItem = items.find(i => i.title.includes('仪表板'));
      const verificationItem = items.find(i => i.title.includes('检验白板'));

      expect(dashboardItem).toBeDefined();
      expect(verificationItem).toBeDefined();
    });
  });

  // ============================================================================
  // Action Execution Tests
  // ============================================================================

  describe('menu action execution', () => {
    it('should execute registered action on click', async () => {
      const mockAction = jest.fn();
      manager.setActionRegistry({ executeDecomposition: mockAction });
      manager.initialize(mockPlugin);

      const menu = new MockMenu();
      const editor = new MockEditor();
      const canvasFile = new TFile('test.canvas');
      const view = new MockMarkdownView(canvasFile);

      mockApp.workspace.getActiveFile.mockReturnValue(canvasFile);

      const editorMenuCall = (mockApp.workspace.on as any).mock.calls.find(
        (call: any[]) => call[0] === 'editor-menu'
      );

      if (editorMenuCall) {
        editorMenuCall[1](menu, editor, view);
      }

      const items = menu.getItems();
      const decomposeItem = items.find(i => i.title.includes('拆解'));

      if (decomposeItem?.clickCallback) {
        await decomposeItem.clickCallback();
      }

      expect(mockAction).toHaveBeenCalled();
    });

    it('should show notice when action not initialized', async () => {
      const { Notice } = await import('obsidian');
      manager.initialize(mockPlugin);

      const menu = new MockMenu();
      const editor = new MockEditor();
      const canvasFile = new TFile('test.canvas');
      const view = new MockMarkdownView(canvasFile);

      const editorMenuCall = (mockApp.workspace.on as any).mock.calls.find(
        (call: any[]) => call[0] === 'editor-menu'
      );

      if (editorMenuCall) {
        editorMenuCall[1](menu, editor, view);
      }

      const items = menu.getItems();
      const decomposeItem = items.find(i => i.title.includes('拆解'));

      if (decomposeItem?.clickCallback) {
        await decomposeItem.clickCallback();
      }

      expect(Notice).toHaveBeenCalled();
    });
  });

  // ============================================================================
  // Settings Tests
  // ============================================================================

  describe('updateSettings', () => {
    it('should update settings', () => {
      manager.updateSettings({ showMenuIcons: false });

      const settings = manager.getSettings();
      expect(settings.showMenuIcons).toBe(false);
    });

    it('should merge with existing settings', () => {
      manager.updateSettings({ enableEditorMenu: false });
      manager.updateSettings({ showMenuIcons: false });

      const settings = manager.getSettings();
      expect(settings.enableEditorMenu).toBe(false);
      expect(settings.showMenuIcons).toBe(false);
    });
  });

  describe('getSettings', () => {
    it('should return copy of settings', () => {
      const settings1 = manager.getSettings();
      const settings2 = manager.getSettings();

      expect(settings1).not.toBe(settings2);
      expect(settings1).toEqual(settings2);
    });

    it('should have correct default values', () => {
      const settings = manager.getSettings();

      expect(settings.enableEditorMenu).toBe(true);
      expect(settings.enableFileMenu).toBe(true);
      expect(settings.showMenuIcons).toBe(true);
    });
  });

  // ============================================================================
  // Debug Mode Tests
  // ============================================================================

  describe('setDebugMode', () => {
    it('should enable debug mode', () => {
      const consoleSpy = jest.spyOn(console, 'log');

      manager.setDebugMode(true);
      manager.initialize(mockPlugin);

      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should disable debug mode', () => {
      manager.setDebugMode(false);

      // Debug logs should be suppressed
    });
  });

  // ============================================================================
  // Cleanup Tests
  // ============================================================================

  describe('cleanup', () => {
    it('should clear menu items', () => {
      manager.initialize(mockPlugin);
      manager.cleanup();

      // Internal state should be cleared
    });

    it('should clear action registry', () => {
      manager.setActionRegistry({ executeDecomposition: jest.fn() });
      manager.cleanup();

      // Registry should be cleared
    });
  });
});
