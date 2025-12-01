/**
 * Canvas Review System - Main Plugin Entry Point
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (Plugin Class, PluginSettingTab, Setting)
 * ✅ Verified from Story 13.1 Dev Notes: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#插件核心类
 * ✅ Verified from Story 13.6: Settings Panel implementation
 *
 * This plugin provides Ebbinghaus-based intelligent Canvas review management
 * integrated with the Canvas Learning System.
 *
 * @module main
 * @version 2.0.0
 */

import {
    App,
    Plugin,
    Notice,
    MarkdownView
} from 'obsidian';
import {
    PluginSettings,
    DEFAULT_SETTINGS,
    validateSettings,
    migrateSettings
} from './src/types/settings';
import { CanvasReviewSettingsTab } from './src/settings/PluginSettingsTab';

/**
 * Canvas Review Plugin - Main Plugin Class
 *
 * Implements the core plugin functionality including:
 * - Plugin lifecycle management (onload/onunload)
 * - Settings management with migration support
 * - Command registration
 * - Manager initialization placeholders
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (Plugin Class - Core Plugin Lifecycle)
 */
export default class CanvasReviewPlugin extends Plugin {
    /** Plugin settings - initialized in onload via loadSettings() */
    settings!: PluginSettings;

    /** Auto-sync interval ID for cleanup */
    private autoSyncIntervalId: number | null = null;

    /**
     * Plugin load lifecycle method
     *
     * Called when the plugin is loaded. Sets up all plugin components:
     * - Loads saved settings (with migration support)
     * - Initializes managers (placeholders for future stories)
     * - Registers commands
     * - Adds settings tab
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Plugin.onload)
     */
    async onload(): Promise<void> {
        console.log('Canvas Review System: Loading plugin...');

        try {
            // Load settings from data.json (with migration support)
            await this.loadSettings();

            // Initialize managers (placeholder for future stories)
            this.initializeManagers();

            // Register commands
            this.registerCommands();

            // Add comprehensive settings tab (Story 13.6)
            // ✅ Verified from Context7: /obsidianmd/obsidian-api (addSettingTab)
            this.addSettingTab(new CanvasReviewSettingsTab(this.app, this));

            // Setup auto-sync if enabled
            this.setupAutoSync();

            // Apply custom CSS if configured
            this.applyCustomCss();

            // Log successful load
            console.log('Canvas Review System: Plugin loaded successfully');

            if (this.settings.debugMode) {
                console.log('Canvas Review System: Debug mode enabled');
                console.log('Canvas Review System: Settings:', this.settings);
            }

        } catch (error) {
            console.error('Canvas Review System: Failed to load plugin:', error);
            new Notice('Canvas Review System failed to load. Check console for details.');
        }
    }

    /**
     * Plugin unload lifecycle method
     *
     * Called when the plugin is disabled. Cleans up all resources:
     * - Stops auto-sync
     * - Cleans up managers
     * - Removes custom CSS
     * - Saves final state
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Plugin.onunload)
     */
    onunload(): void {
        console.log('Canvas Review System: Unloading plugin...');

        try {
            // Stop auto-sync interval
            if (this.autoSyncIntervalId !== null) {
                window.clearInterval(this.autoSyncIntervalId);
                this.autoSyncIntervalId = null;
            }

            // Remove custom CSS
            this.removeCustomCss();

            // Cleanup managers (placeholder for future stories)
            this.cleanupManagers();

            console.log('Canvas Review System: Plugin unloaded successfully');

        } catch (error) {
            console.error('Canvas Review System: Error during unload:', error);
        }
    }

    /**
     * Initialize manager instances
     *
     * Placeholder method for future stories (Story 13.2+)
     * Will initialize:
     * - DataManager
     * - CommandWrapper
     * - UIManager
     * - SyncManager
     */
    private initializeManagers(): void {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: Initializing managers (placeholder)');
        }
        // TODO: Story 13.2+ - Initialize DataManager
        // TODO: Story 13.3+ - Initialize CommandWrapper
        // TODO: Story 13.4+ - Initialize UIManager
        // TODO: Story 13.5+ - Initialize SyncManager
    }

    /**
     * Cleanup manager instances
     *
     * Placeholder method for future stories
     */
    private cleanupManagers(): void {
        if (this.settings.debugMode) {
            console.log('Canvas Review System: Cleaning up managers (placeholder)');
        }
        // TODO: Story 13.2+ - Cleanup DataManager
        // TODO: Story 13.3+ - Cleanup CommandWrapper
        // TODO: Story 13.4+ - Cleanup UIManager
        // TODO: Story 13.5+ - Cleanup SyncManager
    }

    /**
     * Register plugin commands
     *
     * Registers commands available in the command palette:
     * - Show Review Dashboard (main command for AC 6)
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Plugin.addCommand)
     */
    private registerCommands(): void {
        // Register "Show Review Dashboard" command (AC 6)
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (addCommand with callback)
        this.addCommand({
            id: 'show-review-dashboard',
            name: 'Show Review Dashboard',
            callback: () => {
                this.showReviewDashboard();
            }
        });

        // Register "Sync Canvas Progress" command
        this.addCommand({
            id: 'sync-canvas-progress',
            name: 'Sync Canvas Progress',
            callback: async () => {
                await this.syncCanvasProgress();
            }
        });

        // Register "Open Settings" command
        this.addCommand({
            id: 'open-settings',
            name: 'Open Canvas Review Settings',
            callback: () => {
                // ✅ Verified from Context7: /obsidianmd/obsidian-api (app.setting.open)
                (this.app as any).setting.open();
                (this.app as any).setting.openTabById('canvas-review-system');
            }
        });

        // Register "Create Backup" command
        this.addCommand({
            id: 'create-backup',
            name: 'Create Canvas Data Backup',
            callback: async () => {
                new Notice('Canvas Review System: Creating backup...');
                // TODO: Implement actual backup in Story 13.2+
                await new Promise(resolve => setTimeout(resolve, 1000));
                new Notice('Canvas Review System: Backup created (placeholder)');
            }
        });

        // Register "Run Diagnostics" command
        this.addCommand({
            id: 'run-diagnostics',
            name: 'Run Canvas Review Diagnostics',
            callback: () => {
                this.runDiagnostics();
            }
        });

        if (this.settings.debugMode) {
            console.log('Canvas Review System: Commands registered');
        }
    }

    /**
     * Show the review dashboard
     *
     * Placeholder implementation for AC 6.
     * Will be fully implemented in Story 13.4+
     */
    private showReviewDashboard(): void {
        // Placeholder implementation
        new Notice('Canvas Review Dashboard: Coming soon in Story 13.4+');

        if (this.settings.debugMode) {
            console.log('Canvas Review System: showReviewDashboard called');
        }

        // TODO: Story 13.4+ - Implement full dashboard UI
        // - Open a new leaf with custom view
        // - Show Canvas progress statistics
        // - Display review schedule
        // - Provide quick actions
    }

    /**
     * Sync Canvas progress data
     *
     * Placeholder implementation.
     * Will be fully implemented in Story 13.2+
     */
    private async syncCanvasProgress(): Promise<void> {
        new Notice('Canvas Review System: Syncing progress...');

        if (this.settings.debugMode) {
            console.log('Canvas Review System: syncCanvasProgress called');
        }

        // TODO: Story 13.2+ - Implement data sync
        // - Connect to Claude Code API
        // - Fetch latest Canvas data
        // - Update local cache
        // - Refresh UI

        // Simulate sync delay for placeholder
        await new Promise(resolve => setTimeout(resolve, 1000));
        new Notice('Canvas Review System: Sync complete (placeholder)');
    }

    /**
     * Setup auto-sync interval
     *
     * Configures periodic syncing based on settings.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (registerInterval)
     */
    private setupAutoSync(): void {
        // Clear existing interval if any
        if (this.autoSyncIntervalId !== null) {
            window.clearInterval(this.autoSyncIntervalId);
            this.autoSyncIntervalId = null;
        }

        if (this.settings.autoSyncInterval > 0) {
            const intervalMs = this.settings.autoSyncInterval * 60 * 1000;

            // ✅ Verified from Context7: /obsidianmd/obsidian-api (registerInterval with setInterval)
            this.autoSyncIntervalId = window.setInterval(() => {
                if (this.settings.debugMode) {
                    console.log('Canvas Review System: Auto-sync triggered');
                }
                this.syncCanvasProgress();
            }, intervalMs);

            // Register for automatic cleanup
            this.registerInterval(this.autoSyncIntervalId);

            if (this.settings.debugMode) {
                console.log(`Canvas Review System: Auto-sync enabled every ${this.settings.autoSyncInterval} minutes`);
            }
        }
    }

    /**
     * Apply custom CSS from settings
     */
    private applyCustomCss(): void {
        if (this.settings.customCss) {
            const styleEl = document.createElement('style');
            styleEl.id = 'canvas-review-custom-css';
            styleEl.textContent = this.settings.customCss;
            document.head.appendChild(styleEl);

            if (this.settings.debugMode) {
                console.log('Canvas Review System: Custom CSS applied');
            }
        }
    }

    /**
     * Remove custom CSS
     */
    private removeCustomCss(): void {
        const styleEl = document.getElementById('canvas-review-custom-css');
        if (styleEl) {
            styleEl.remove();
        }
    }

    /**
     * Run diagnostics and show results
     */
    private runDiagnostics(): void {
        const validation = validateSettings(this.settings);
        let message = 'Canvas Review System Diagnostics:\n\n';

        // Settings validation
        if (validation.isValid) {
            message += '✅ Settings: Valid\n';
        } else {
            message += '❌ Settings: Invalid\n';
            validation.errors.forEach(err => {
                message += `   - ${err}\n`;
            });
        }

        // Warnings
        if (validation.warnings.length > 0) {
            message += '\n⚠️ Warnings:\n';
            validation.warnings.forEach(warn => {
                message += `   - ${warn}\n`;
            });
        }

        // Connection info
        message += `\n📡 Connection:\n`;
        message += `   URL: ${this.settings.claudeCodeUrl || 'Not configured'}\n`;
        message += `   Cache: ${this.settings.enableCache ? 'Enabled' : 'Disabled'}\n`;
        message += `   Timeout: ${this.settings.commandTimeout / 1000}s\n`;

        // Storage info
        message += `\n💾 Storage:\n`;
        message += `   Path: ${this.settings.dataPath || 'Not configured'}\n`;
        message += `   Auto-backup: ${this.settings.autoBackup ? 'Enabled' : 'Disabled'}\n`;
        message += `   Auto-sync: ${this.settings.autoSyncInterval > 0 ? `${this.settings.autoSyncInterval}min` : 'Disabled'}\n`;

        // Debug info
        message += `\n🔧 Debug:\n`;
        message += `   Debug mode: ${this.settings.debugMode ? 'On' : 'Off'}\n`;
        message += `   Performance monitoring: ${this.settings.enablePerformanceMonitoring ? 'On' : 'Off'}\n`;
        message += `   Experimental features: ${this.settings.enableExperimentalFeatures ? 'On' : 'Off'}\n`;

        console.log(message);
        new Notice('Diagnostics complete. Check console for details.');
    }

    /**
     * Load settings from storage with migration support
     *
     * Loads saved settings, merges with defaults, and migrates if needed.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (loadSettings pattern)
     */
    async loadSettings(): Promise<void> {
        const savedData = await this.loadData();

        // Migrate settings if needed (handles version upgrades)
        if (savedData) {
            this.settings = migrateSettings(savedData);

            // Save migrated settings if version changed
            if (savedData.settingsVersion !== this.settings.settingsVersion) {
                await this.saveSettings();
                if (this.settings.debugMode) {
                    console.log('Canvas Review System: Settings migrated to version', this.settings.settingsVersion);
                }
            }
        } else {
            this.settings = { ...DEFAULT_SETTINGS };
        }
    }

    /**
     * Save settings to storage
     *
     * Validates and persists current settings.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (saveSettings pattern)
     */
    async saveSettings(): Promise<void> {
        const validation = validateSettings(this.settings);
        if (!validation.isValid) {
            console.warn('Canvas Review System: Invalid settings:', validation.errors);
        }
        if (validation.warnings.length > 0) {
            console.warn('Canvas Review System: Settings warnings:', validation.warnings);
        }
        await this.saveData(this.settings);

        // Re-apply custom CSS when settings are saved
        this.removeCustomCss();
        this.applyCustomCss();

        // Restart auto-sync with new interval
        this.setupAutoSync();
    }
}
