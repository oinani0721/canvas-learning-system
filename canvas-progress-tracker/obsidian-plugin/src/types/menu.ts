/**
 * Menu System Type Definitions
 * Story 13.5: 右键菜单和快捷键
 *
 * Defines types for context menus, hotkeys, and menu configuration.
 *
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference - Plugin Development)
 * ✅ Verified from Obsidian API (obsidian.d.ts - Menu, MenuItem types)
 */

import type { IconName } from 'obsidian';

// ============================================================================
// Menu Item Types
// ============================================================================

/**
 * Menu item configuration
 * Defines a single context menu item
 */
export interface MenuItemConfig {
  /** Unique identifier for the menu item */
  id: string;

  /** Display title (supports emoji) */
  title: string;

  /** Obsidian icon name */
  icon?: IconName;

  /** Section for grouping (adds separator before section) */
  section?: 'primary' | 'secondary' | 'utility';

  /** Condition to check if item should be shown */
  condition?: () => boolean | Promise<boolean>;

  /** Action to execute when clicked - receives MenuContext for Epic 12.L fix */
  action: (context: MenuContext) => void | Promise<void>;

  /** Tooltip/description for hover */
  description?: string;
}

/**
 * Context menu context types
 */
export type MenuContextType = 'editor' | 'file' | 'files' | 'canvas-node';

/**
 * Canvas node color identifiers
 * ✅ Verified from @obsidian-canvas Skill (Canvas Color System)
 */
export type CanvasNodeColor = '1' | '2' | '3' | '4' | '5' | '6';

/**
 * Canvas node color names for display
 * Story 12.B.4: Fixed to match actual Obsidian Canvas colors
 * Verified from docs/issues/canvas-layout-lessons-learned.md
 */
export const CANVAS_COLOR_NAMES: Record<CanvasNodeColor, string> = {
  '1': '灰色',
  '2': '绿色 (完全理解)',
  '3': '紫色 (似懂非懂)',
  '4': '红色 (不理解)',
  '5': '蓝色 (AI解释)',
  '6': '黄色 (个人理解)',
};

/**
 * Context information for menu generation
 */
export interface MenuContext {
  /** Type of context menu */
  type: MenuContextType;

  /** File path (for file/files context) */
  filePath?: string;

  /** Multiple file paths (for files context) */
  filePaths?: string[];

  /** Canvas node ID (for canvas-node context) */
  nodeId?: string;

  /** Canvas node color */
  nodeColor?: CanvasNodeColor;

  /** Canvas node type */
  nodeType?: 'text' | 'file' | 'link' | 'group';

  /**
   * Real-time node text content (Story 12.B.2)
   * Passed directly to backend to avoid stale disk reads
   */
  nodeContent?: string;

  /** Whether in backup folder */
  isBackupFile?: boolean;

  /** Whether backup is protected */
  isProtected?: boolean;
}

// ============================================================================
// Hotkey Types
// ============================================================================

/**
 * Modifier keys supported by Obsidian
 * ✅ Verified from Obsidian API (obsidian.d.ts - Modifier type)
 */
export type HotkeyModifier = 'Mod' | 'Ctrl' | 'Meta' | 'Shift' | 'Alt';

/**
 * Hotkey definition
 */
export interface HotkeyDefinition {
  /** Array of modifier keys */
  modifiers: HotkeyModifier[];

  /** Primary key (letter, number, or special key) */
  key: string;
}

/**
 * Command definition with optional hotkey
 */
export interface CommandDefinition {
  /** Unique command ID (plugin namespace will be prefixed) */
  id: string;

  /** Display name in command palette */
  name: string;

  /** Icon for command palette and menus */
  icon?: IconName;

  /** Suggested hotkey (not enforced, for documentation) */
  suggestedHotkey?: HotkeyDefinition;

  /** Whether command requires Canvas view */
  requiresCanvasView?: boolean;

  /** Whether command requires selected node */
  requiresSelectedNode?: boolean;

  /** Command callback */
  callback?: () => void | Promise<void>;

  /** Editor callback with check function */
  editorCheckCallback?: (checking: boolean) => boolean | void;

  /** Description for documentation */
  description?: string;

  /** Category for grouping in documentation */
  category?: 'decomposition' | 'explanation' | 'scoring' | 'review' | 'utility';
}

// ============================================================================
// Backup Protection Types
// ============================================================================

/**
 * Backup metadata structure
 * Story 13.5: AC 3 - SCP-003 backup protection
 */
export interface BackupMetadata {
  /** File path relative to vault */
  filePath: string;

  /** Whether backup is protected */
  protected: boolean;

  /** Timestamp when protection was added */
  protectedAt?: number;

  /** Who protected the backup */
  protectedBy?: string;

  /** User note about why backup is protected */
  note?: string;

  /** Original canvas file name */
  originalName?: string;

  /** Backup creation timestamp */
  backupTimestamp?: number;
}

/**
 * Backup protection metadata file structure
 */
export interface BackupProtectionData {
  /** Version of the metadata format */
  version: number;

  /** Last modified timestamp */
  lastModified: number;

  /** Map of file paths to metadata */
  backups: Record<string, BackupMetadata>;
}

// ============================================================================
// Registry Types
// ============================================================================

/**
 * Menu item registry entry
 */
export interface MenuRegistryEntry {
  /** Menu item configuration */
  config: MenuItemConfig;

  /** Context types where this item appears */
  contexts: MenuContextType[];

  /** Priority for ordering (higher = earlier) */
  priority: number;
}

/**
 * Command registry entry
 */
export interface CommandRegistryEntry {
  /** Command definition */
  definition: CommandDefinition;

  /** Whether command is registered with Obsidian */
  registered: boolean;
}

// ============================================================================
// Settings Types
// ============================================================================

/**
 * Hotkey preset options
 */
export type HotkeyPreset = 'default' | 'advanced' | 'minimal' | 'custom';

/**
 * Hotkey settings configuration
 */
export interface HotkeySettings {
  /** Active preset */
  preset: HotkeyPreset;

  /** Custom hotkey overrides */
  customHotkeys: Record<string, HotkeyDefinition | null>;

  /** Show hotkey hints in menus */
  showHotkeyHints: boolean;
}

/**
 * Context menu settings configuration
 */
export interface ContextMenuSettings {
  /** Enable editor context menu */
  enableEditorMenu: boolean;

  /** Enable file menu */
  enableFileMenu: boolean;

  /** Show icons in menus */
  showMenuIcons: boolean;

  /** Show color-based menu items */
  showColorBasedMenus: boolean;

  /** Maximum items per section */
  maxItemsPerSection: number;
}

// ============================================================================
// Event Types
// ============================================================================

/**
 * Menu item click event data
 */
export interface MenuItemClickEvent {
  /** Menu item ID */
  itemId: string;

  /** Menu context */
  context: MenuContext;

  /** Timestamp of click */
  timestamp: number;
}

/**
 * Command execution event data
 */
export interface CommandExecutionEvent {
  /** Command ID */
  commandId: string;

  /** How command was triggered */
  triggerSource: 'hotkey' | 'menu' | 'palette';

  /** Timestamp of execution */
  timestamp: number;

  /** Whether execution was successful */
  success: boolean;

  /** Error message if failed */
  error?: string;
}

// ============================================================================
// Constants
// ============================================================================

/**
 * Default context menu settings
 */
export const DEFAULT_CONTEXT_MENU_SETTINGS: ContextMenuSettings = {
  enableEditorMenu: true,
  enableFileMenu: true,
  showMenuIcons: true,
  showColorBasedMenus: true,
  maxItemsPerSection: 10,
};

/**
 * Default hotkey settings
 */
export const DEFAULT_HOTKEY_SETTINGS: HotkeySettings = {
  preset: 'default',
  customHotkeys: {},
  showHotkeyHints: true,
};

/**
 * Backup protection metadata file path
 */
export const BACKUP_METADATA_PATH = '.canvas_backups/.protection-metadata.json';

/**
 * Default backup protection data
 */
export const DEFAULT_BACKUP_PROTECTION_DATA: BackupProtectionData = {
  version: 1,
  lastModified: Date.now(),
  backups: {},
};
