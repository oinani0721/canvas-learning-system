/**
 * Canvas Review System - Settings Type Definitions
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (Plugin Settings Interface)
 * ✅ Verified from Story 13.1 Dev Notes: canvas-progress-tracker/docs/obsidian-plugin-prd.md#技术栈
 * ✅ Story 13.5: Added context menu and hotkey settings
 *
 * @module types/settings
 * @version 1.1.0
 */

import type {
    ContextMenuSettings,
    HotkeySettings,
    HotkeyPreset,
} from './menu';
import {
    DEFAULT_CONTEXT_MENU_SETTINGS,
    DEFAULT_HOTKEY_SETTINGS,
} from './menu';

/**
 * Plugin settings interface
 *
 * Defines all configurable options for the Canvas Review System plugin.
 * These settings are persisted in the Obsidian data.json file.
 */
export interface PluginSettings {
    /**
     * Claude Code API service base URL
     * Used for communicating with the backend Canvas analysis service
     * @default 'http://localhost:3005'
     */
    claudeCodeUrl: string;

    /**
     * Canvas learning system data storage path
     * Path where Canvas files and learning data are stored
     * @default ''
     */
    dataPath: string;

    /**
     * Auto-sync interval in minutes
     * How often to automatically sync Canvas progress data
     * @default 5
     */
    autoSyncInterval: number;

    /**
     * Enable caching for performance optimization
     * When enabled, Canvas data is cached locally for faster access
     * @default true
     */
    enableCache: boolean;

    /**
     * Command execution timeout in milliseconds
     * Maximum time to wait for a command to complete
     * @default 30000
     */
    commandTimeout: number;

    /**
     * UI theme setting
     * Controls the visual appearance of the plugin UI
     * @default 'auto'
     */
    theme: 'light' | 'dark' | 'auto';

    /**
     * Enable debug logging
     * When enabled, detailed logs are written to the console
     * @default false
     */
    debugMode: boolean;

    /**
     * Maximum number of concurrent operations
     * Limits parallel processing to prevent resource exhaustion
     * @default 5
     */
    maxConcurrentOps: number;

    // ============================================================================
    // Story 13.5: Context Menu and Hotkey Settings
    // ============================================================================

    /**
     * Context menu settings
     * Controls the behavior of right-click context menus
     * @default DEFAULT_CONTEXT_MENU_SETTINGS
     */
    contextMenu: ContextMenuSettings;

    /**
     * Hotkey settings
     * Controls hotkey presets and custom bindings
     * @default DEFAULT_HOTKEY_SETTINGS
     */
    hotkeys: HotkeySettings;

    /**
     * Maximum backups to keep per canvas file
     * Older backups are automatically cleaned up
     * @default 10
     */
    maxBackupsPerFile: number;

    /**
     * Auto-backup before modifications
     * Creates a backup before any canvas operation
     * @default true
     */
    autoBackup: boolean;
}

/**
 * Default plugin settings
 *
 * These values are used when the plugin is first installed
 * or when settings are reset to defaults.
 */
export const DEFAULT_SETTINGS: PluginSettings = {
    claudeCodeUrl: 'http://localhost:3005',
    dataPath: '',
    autoSyncInterval: 5,
    enableCache: true,
    commandTimeout: 30000,
    theme: 'auto',
    debugMode: false,
    maxConcurrentOps: 5,
    // Story 13.5: Context Menu and Hotkey Settings
    contextMenu: DEFAULT_CONTEXT_MENU_SETTINGS,
    hotkeys: DEFAULT_HOTKEY_SETTINGS,
    maxBackupsPerFile: 10,
    autoBackup: true,
};

/**
 * Validation result for settings
 */
export interface SettingsValidationResult {
    isValid: boolean;
    errors: string[];
}

/**
 * Validates plugin settings
 *
 * @param settings - Settings object to validate
 * @returns Validation result with any errors found
 */
export function validateSettings(settings: Partial<PluginSettings>): SettingsValidationResult {
    const errors: string[] = [];

    // Validate claudeCodeUrl
    if (settings.claudeCodeUrl !== undefined) {
        try {
            new URL(settings.claudeCodeUrl);
        } catch {
            errors.push('Claude Code URL must be a valid URL');
        }
    }

    // Validate autoSyncInterval
    if (settings.autoSyncInterval !== undefined) {
        if (settings.autoSyncInterval < 1 || settings.autoSyncInterval > 60) {
            errors.push('Auto-sync interval must be between 1 and 60 minutes');
        }
    }

    // Validate commandTimeout
    if (settings.commandTimeout !== undefined) {
        if (settings.commandTimeout < 5000 || settings.commandTimeout > 300000) {
            errors.push('Command timeout must be between 5000ms and 300000ms');
        }
    }

    // Validate maxConcurrentOps
    if (settings.maxConcurrentOps !== undefined) {
        if (settings.maxConcurrentOps < 1 || settings.maxConcurrentOps > 20) {
            errors.push('Max concurrent operations must be between 1 and 20');
        }
    }

    return {
        isValid: errors.length === 0,
        errors
    };
}
