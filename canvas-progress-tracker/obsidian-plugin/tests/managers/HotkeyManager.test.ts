// @ts-nocheck - Mock types don't match Obsidian types exactly
/**
 * Tests for Hotkey Manager
 * Story 13.5: 右键菜单和快捷键 - Tasks 4, 5, 6
 *
 * Tests command registration and hotkey documentation.
 */

import {
  HotkeyManager,
  RECOMMENDED_HOTKEYS,
  formatHotkey,
} from '../../src/managers/HotkeyManager';
import type { CommandDefinition, HotkeyDefinition } from '../../src/types/menu';

// Mock Obsidian Notice
jest.mock('obsidian', () => ({
  Notice: jest.fn().mockImplementation((message, duration) => {
    return { message, duration };
  }),
}));

// Mock plugin
class MockPlugin {
  commands: any[] = [];

  addCommand(command: any): void {
    this.commands.push(command);
  }

  getCommands(): any[] {
    return this.commands;
  }

  clearCommands(): void {
    this.commands = [];
  }
}

// Mock app
const mockApp = {
  vault: {},
  workspace: {
    getActiveFile: () => null,
  },
};

describe('HotkeyManager', () => {
  let manager: HotkeyManager;
  let plugin: MockPlugin;

  beforeEach(() => {
    plugin = new MockPlugin();
    manager = new HotkeyManager(mockApp as any, plugin as any);
  });

  afterEach(() => {
    manager.cleanup();
    plugin.clearCommands();
    jest.clearAllMocks();
  });

  // ============================================================================
  // Initialization Tests
  // ============================================================================

  describe('initialize', () => {
    it('should register built-in commands', () => {
      manager.initialize();

      const commands = plugin.getCommands();
      expect(commands.length).toBeGreaterThan(0);
    });

    it('should register decomposition commands', () => {
      manager.initialize();

      const commands = manager.getCommandsByCategory('decomposition');
      expect(commands).toHaveLength(2);
      expect(commands.map(c => c.id)).toContain('canvas-decompose-node');
      expect(commands.map(c => c.id)).toContain('canvas-deep-decompose');
    });

    it('should register explanation commands', () => {
      manager.initialize();

      const commands = manager.getCommandsByCategory('explanation');
      expect(commands).toHaveLength(2);
      expect(commands.map(c => c.id)).toContain('canvas-oral-explain');
      expect(commands.map(c => c.id)).toContain('canvas-four-level-explain');
    });

    it('should register scoring commands', () => {
      manager.initialize();

      const commands = manager.getCommandsByCategory('scoring');
      expect(commands).toHaveLength(2);
      expect(commands.map(c => c.id)).toContain('canvas-score-node');
      expect(commands.map(c => c.id)).toContain('canvas-score-all-yellow');
    });

    it('should register review commands', () => {
      manager.initialize();

      const commands = manager.getCommandsByCategory('review');
      expect(commands).toHaveLength(2);
      expect(commands.map(c => c.id)).toContain('canvas-generate-verification');
      expect(commands.map(c => c.id)).toContain('canvas-open-dashboard');
    });

    it('should register utility commands', () => {
      manager.initialize();

      const commands = manager.getCommandsByCategory('utility');
      expect(commands).toHaveLength(3);
      expect(commands.map(c => c.id)).toContain('canvas-comparison-table');
      expect(commands.map(c => c.id)).toContain('canvas-memory-anchor');
      expect(commands.map(c => c.id)).toContain('canvas-example-teaching');
    });

    it('should register hotkey help command with Obsidian', () => {
      manager.initialize();

      const commands = plugin.getCommands();
      const helpCommand = commands.find(c => c.id === 'canvas-show-hotkey-help');
      expect(helpCommand).toBeDefined();
      expect(helpCommand.name).toBe('Canvas: 显示快捷键帮助');
    });
  });

  // ============================================================================
  // Command Registration Tests
  // ============================================================================

  describe('registerCommand', () => {
    it('should register command with Obsidian', () => {
      const definition: CommandDefinition = {
        id: 'test-command',
        name: 'Test Command',
        callback: () => {},
      };

      manager.registerCommand(definition);

      const obsidianCommands = plugin.getCommands();
      expect(obsidianCommands.find(c => c.id === 'test-command')).toBeDefined();
    });

    it('should store command in internal registry', () => {
      const definition: CommandDefinition = {
        id: 'test-command',
        name: 'Test Command',
        callback: () => {},
      };

      manager.registerCommand(definition);

      const commands = manager.getCommands();
      expect(commands.find(c => c.id === 'test-command')).toBeDefined();
    });

    it('should include icon when provided', () => {
      const definition: CommandDefinition = {
        id: 'test-command',
        name: 'Test Command',
        icon: 'star',
        callback: () => {},
      };

      manager.registerCommand(definition);

      const obsidianCommands = plugin.getCommands();
      const cmd = obsidianCommands.find(c => c.id === 'test-command');
      expect(cmd?.icon).toBe('star');
    });

    it('should use editorCheckCallback for Canvas view commands', () => {
      const definition: CommandDefinition = {
        id: 'canvas-only-command',
        name: 'Canvas Only',
        requiresCanvasView: true,
        callback: jest.fn(),
      };

      manager.registerCommand(definition);

      const obsidianCommands = plugin.getCommands();
      const cmd = obsidianCommands.find(c => c.id === 'canvas-only-command');
      expect(cmd?.editorCheckCallback).toBeDefined();
    });

    it('should use regular callback for non-Canvas commands', () => {
      const callback = jest.fn();
      const definition: CommandDefinition = {
        id: 'regular-command',
        name: 'Regular Command',
        requiresCanvasView: false,
        callback,
      };

      manager.registerCommand(definition);

      const obsidianCommands = plugin.getCommands();
      const cmd = obsidianCommands.find(c => c.id === 'regular-command');
      expect(cmd?.callback).toBeDefined();
    });

    it('should NOT set default hotkeys (Obsidian best practice)', () => {
      const definition: CommandDefinition = {
        id: 'test-command',
        name: 'Test Command',
        suggestedHotkey: { modifiers: ['Mod', 'Shift'], key: 'T' },
        callback: () => {},
      };

      manager.registerCommand(definition);

      const obsidianCommands = plugin.getCommands();
      const cmd = obsidianCommands.find(c => c.id === 'test-command');
      // Hotkeys should NOT be set by default
      expect(cmd?.hotkeys).toBeUndefined();
    });
  });

  describe('setCommandCallback', () => {
    it('should update callback for registered command', () => {
      const originalCallback = jest.fn();
      const newCallback = jest.fn();

      manager.registerCommand({
        id: 'test-command',
        name: 'Test',
        callback: originalCallback,
      });

      manager.setCommandCallback('test-command', newCallback);

      const commands = manager.getCommands();
      const cmd = commands.find(c => c.id === 'test-command');
      expect(cmd?.callback).toBe(newCallback);
    });

    it('should do nothing for non-existent command', () => {
      const callback = jest.fn();

      // Should not throw
      expect(() => manager.setCommandCallback('non-existent', callback)).not.toThrow();
    });
  });

  // ============================================================================
  // Hotkey Help Tests
  // ============================================================================

  describe('showHotkeyCheatSheet', () => {
    it('should display notice with cheat sheet content', async () => {
      const { Notice } = await import('obsidian');

      manager.initialize();
      manager.showHotkeyCheatSheet();

      expect(Notice).toHaveBeenCalled();
      const noticeCall = (Notice as any).mock.calls[0];
      expect(noticeCall[0]).toContain('Canvas Learning System');
      expect(noticeCall[1]).toBe(15000); // 15 seconds
    });
  });

  describe('generateMarkdownDocumentation', () => {
    it('should generate valid Markdown', () => {
      manager.initialize();

      const markdown = manager.generateMarkdownDocumentation();

      expect(markdown).toContain('# Canvas Learning System 快捷键指南');
      expect(markdown).toContain('## 概述');
      expect(markdown).toContain('| 命令 | 建议快捷键 | 说明 |');
    });

    it('should include all command categories', () => {
      manager.initialize();

      const markdown = manager.generateMarkdownDocumentation();

      expect(markdown).toContain('## 拆解命令');
      expect(markdown).toContain('## 解释命令');
      expect(markdown).toContain('## 评分命令');
      expect(markdown).toContain('## 复习命令');
      expect(markdown).toContain('## 工具命令');
    });

    it('should include suggested hotkeys', () => {
      manager.initialize();

      const markdown = manager.generateMarkdownDocumentation();

      // Should contain formatted hotkey suggestions
      expect(markdown).toMatch(/`.*\+.*D`/); // Decompose hotkey
      expect(markdown).toMatch(/`.*\+.*E`/); // Explain hotkey
      expect(markdown).toMatch(/`.*\+.*S`/); // Score hotkey
    });

    it('should include usage tips section', () => {
      manager.initialize();

      const markdown = manager.generateMarkdownDocumentation();

      expect(markdown).toContain('## 使用技巧');
      expect(markdown).toContain('### 如何自定义快捷键');
      expect(markdown).toContain('### 快捷键冲突');
      expect(markdown).toContain('### 跨平台说明');
    });
  });

  // ============================================================================
  // Query Tests
  // ============================================================================

  describe('getCommands', () => {
    it('should return all registered commands', () => {
      manager.initialize();

      const commands = manager.getCommands();

      expect(commands.length).toBeGreaterThanOrEqual(11); // At least 11 built-in commands
    });
  });

  describe('getCommandsByCategory', () => {
    it('should filter commands by category', () => {
      manager.initialize();

      const decomposition = manager.getCommandsByCategory('decomposition');
      const scoring = manager.getCommandsByCategory('scoring');

      expect(decomposition.every(c => c.category === 'decomposition')).toBe(true);
      expect(scoring.every(c => c.category === 'scoring')).toBe(true);
    });

    it('should return empty array for non-existent category', () => {
      manager.initialize();

      const commands = manager.getCommandsByCategory('nonexistent' as any);

      expect(commands).toHaveLength(0);
    });
  });

  describe('getSuggestedHotkey', () => {
    it('should return suggested hotkey for known command', () => {
      const hotkey = manager.getSuggestedHotkey('canvas-decompose-node');

      expect(hotkey).toEqual({ modifiers: ['Mod', 'Shift'], key: 'D' });
    });

    it('should return undefined for unknown command', () => {
      const hotkey = manager.getSuggestedHotkey('unknown-command');

      expect(hotkey).toBeUndefined();
    });
  });

  // ============================================================================
  // Settings Tests
  // ============================================================================

  describe('updateSettings', () => {
    it('should update settings', () => {
      manager.updateSettings({ showHotkeyHints: false });

      const settings = manager.getSettings();
      expect(settings.showHotkeyHints).toBe(false);
    });

    it('should merge with existing settings', () => {
      manager.updateSettings({ preset: 'minimal' });
      manager.updateSettings({ showHotkeyHints: false });

      const settings = manager.getSettings();
      expect(settings.preset).toBe('minimal');
      expect(settings.showHotkeyHints).toBe(false);
    });
  });

  describe('getSettings', () => {
    it('should return copy of settings', () => {
      const settings1 = manager.getSettings();
      const settings2 = manager.getSettings();

      expect(settings1).not.toBe(settings2);
      expect(settings1).toEqual(settings2);
    });
  });

  // ============================================================================
  // Cleanup Tests
  // ============================================================================

  describe('cleanup', () => {
    it('should clear command registry', () => {
      manager.initialize();
      manager.cleanup();

      const commands = manager.getCommands();
      expect(commands).toHaveLength(0);
    });
  });
});

// ============================================================================
// RECOMMENDED_HOTKEYS Tests
// ============================================================================

describe('RECOMMENDED_HOTKEYS', () => {
  it('should define hotkeys for decomposition commands', () => {
    expect(RECOMMENDED_HOTKEYS['canvas-decompose-node']).toBeDefined();
    expect(RECOMMENDED_HOTKEYS['canvas-deep-decompose']).toBeDefined();
  });

  it('should define hotkeys for explanation commands', () => {
    expect(RECOMMENDED_HOTKEYS['canvas-oral-explain']).toBeDefined();
    expect(RECOMMENDED_HOTKEYS['canvas-four-level-explain']).toBeDefined();
  });

  it('should define hotkeys for scoring commands', () => {
    expect(RECOMMENDED_HOTKEYS['canvas-score-node']).toBeDefined();
    expect(RECOMMENDED_HOTKEYS['canvas-score-all-yellow']).toBeDefined();
  });

  it('should define hotkeys for review commands', () => {
    expect(RECOMMENDED_HOTKEYS['canvas-generate-verification']).toBeDefined();
    expect(RECOMMENDED_HOTKEYS['canvas-open-dashboard']).toBeDefined();
  });

  it('should use Mod+Shift as base modifier', () => {
    // All recommended hotkeys should use Mod+Shift to avoid conflicts
    for (const hotkey of Object.values(RECOMMENDED_HOTKEYS)) {
      expect(hotkey.modifiers).toContain('Mod');
      expect(hotkey.modifiers).toContain('Shift');
    }
  });
});

// ============================================================================
// formatHotkey Tests
// ============================================================================

describe('formatHotkey', () => {
  it('should format basic hotkey', () => {
    const hotkey: HotkeyDefinition = { modifiers: ['Mod'], key: 'A' };

    const result = formatHotkey(hotkey);

    // Should contain either Ctrl or ⌘ depending on platform
    expect(result).toMatch(/Ctrl|⌘/);
    expect(result).toContain('A');
  });

  it('should format hotkey with Shift', () => {
    const hotkey: HotkeyDefinition = { modifiers: ['Mod', 'Shift'], key: 'S' };

    const result = formatHotkey(hotkey);

    expect(result).toContain('⇧');
    expect(result).toContain('S');
  });

  it('should format hotkey with Alt', () => {
    const hotkey: HotkeyDefinition = { modifiers: ['Mod', 'Alt'], key: 'A' };

    const result = formatHotkey(hotkey);

    // Should contain either Alt or ⌥
    expect(result).toMatch(/Alt|⌥/);
    expect(result).toContain('A');
  });

  it('should format hotkey with multiple modifiers', () => {
    const hotkey: HotkeyDefinition = { modifiers: ['Mod', 'Shift', 'Alt'], key: 'D' };

    const result = formatHotkey(hotkey);

    expect(result).toContain('⇧');
    expect(result).toMatch(/Alt|⌥/);
    expect(result).toContain('D');
    expect(result).toContain(' + ');
  });

  it('should uppercase the key', () => {
    const hotkey: HotkeyDefinition = { modifiers: ['Mod'], key: 'a' };

    const result = formatHotkey(hotkey);

    expect(result).toContain('A');
    expect(result).not.toContain(' a');
  });
});
