/**
 * Canvas Review System - Main Plugin Entry Point
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (Plugin Class, PluginSettingTab, Setting)
 * ✅ Verified from Story 13.1 Dev Notes: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#插件核心类
 *
 * This plugin provides Ebbinghaus-based intelligent Canvas review management
 * integrated with the Canvas Learning System.
 *
 * @module main
 * @version 1.0.0
 */

import {
    App,
    Plugin,
    PluginSettingTab,
    Setting,
    Notice,
    MarkdownView
} from 'obsidian';
import { PluginSettings, DEFAULT_SETTINGS, validateSettings } from './src/types/settings';

/**
 * Canvas Review Plugin - Main Plugin Class
 *
 * Implements the core plugin functionality including:
 * - Plugin lifecycle management (onload/onunload)
 * - Settings management
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
     * - Loads saved settings
     * - Initializes managers (placeholders for future stories)
     * - Registers commands
     * - Adds settings tab
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (Plugin.onload)
     */
    async onload(): Promise<void> {
        console.log('Canvas Review System: Loading plugin...');

        try {
            // Load settings from data.json
            await this.loadSettings();

            // Initialize managers (placeholder for future stories)
            this.initializeManagers();

            // Register commands
            this.registerCommands();

            // Add settings tab
            // ✅ Verified from Context7: /obsidianmd/obsidian-api (addSettingTab)
            this.addSettingTab(new CanvasReviewSettingsTab(this.app, this));

            // Setup auto-sync if enabled
            this.setupAutoSync();

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
     * Load settings from storage
     *
     * Loads saved settings and merges with defaults.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (loadSettings pattern)
     */
    async loadSettings(): Promise<void> {
        this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
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
        await this.saveData(this.settings);
    }
}

/**
 * Plugin Settings Tab
 *
 * Implements the settings interface shown in Obsidian's settings panel.
 * Provides controls for all configurable plugin options.
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (PluginSettingTab, Setting)
 */
class CanvasReviewSettingsTab extends PluginSettingTab {
    plugin: CanvasReviewPlugin;

    constructor(app: App, plugin: CanvasReviewPlugin) {
        super(app, plugin);
        this.plugin = plugin;
    }

    /**
     * Display the settings interface
     *
     * Renders all setting controls in the settings panel.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (PluginSettingTab.display)
     */
    display(): void {
        const { containerEl } = this;
        containerEl.empty();

        // Header
        containerEl.createEl('h2', { text: 'Canvas Review System Settings' });

        // Connection Settings Section
        containerEl.createEl('h3', { text: 'Connection Settings' });

        // Claude Code URL setting
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (Setting.addText)
        new Setting(containerEl)
            .setName('Claude Code Service URL')
            .setDesc('Base URL for the Claude Code API service')
            .addText(text => text
                .setPlaceholder('http://localhost:3005')
                .setValue(this.plugin.settings.claudeCodeUrl)
                .onChange(async (value) => {
                    this.plugin.settings.claudeCodeUrl = value;
                    await this.plugin.saveSettings();
                }));

        // Data path setting
        new Setting(containerEl)
            .setName('Data Storage Path')
            .setDesc('Path where Canvas learning system data is stored')
            .addText(text => text
                .setPlaceholder('C:/Users/YourName/CanvasData')
                .setValue(this.plugin.settings.dataPath)
                .onChange(async (value) => {
                    this.plugin.settings.dataPath = value;
                    await this.plugin.saveSettings();
                }));

        // Sync Settings Section
        containerEl.createEl('h3', { text: 'Sync Settings' });

        // Auto-sync interval
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (Setting.addSlider)
        new Setting(containerEl)
            .setName('Auto-sync Interval')
            .setDesc('Interval in minutes for automatic sync (0 to disable)')
            .addSlider(slider => slider
                .setLimits(0, 60, 1)
                .setValue(this.plugin.settings.autoSyncInterval)
                .setDynamicTooltip()
                .onChange(async (value) => {
                    this.plugin.settings.autoSyncInterval = value;
                    await this.plugin.saveSettings();
                }));

        // Command timeout
        new Setting(containerEl)
            .setName('Command Timeout')
            .setDesc('Maximum time to wait for commands (in seconds)')
            .addSlider(slider => slider
                .setLimits(5, 300, 5)
                .setValue(this.plugin.settings.commandTimeout / 1000)
                .setDynamicTooltip()
                .onChange(async (value) => {
                    this.plugin.settings.commandTimeout = value * 1000;
                    await this.plugin.saveSettings();
                }));

        // Performance Settings Section
        containerEl.createEl('h3', { text: 'Performance Settings' });

        // Enable cache
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (Setting.addToggle)
        new Setting(containerEl)
            .setName('Enable Cache')
            .setDesc('Cache Canvas data locally for faster access')
            .addToggle(toggle => toggle
                .setValue(this.plugin.settings.enableCache)
                .onChange(async (value) => {
                    this.plugin.settings.enableCache = value;
                    await this.plugin.saveSettings();
                }));

        // Max concurrent operations
        new Setting(containerEl)
            .setName('Max Concurrent Operations')
            .setDesc('Maximum number of parallel operations')
            .addSlider(slider => slider
                .setLimits(1, 20, 1)
                .setValue(this.plugin.settings.maxConcurrentOps)
                .setDynamicTooltip()
                .onChange(async (value) => {
                    this.plugin.settings.maxConcurrentOps = value;
                    await this.plugin.saveSettings();
                }));

        // Appearance Settings Section
        containerEl.createEl('h3', { text: 'Appearance' });

        // Theme setting
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (Setting.addDropdown)
        new Setting(containerEl)
            .setName('Theme')
            .setDesc('Plugin UI theme')
            .addDropdown(dropdown => dropdown
                .addOption('auto', 'Auto (Follow Obsidian)')
                .addOption('light', 'Light')
                .addOption('dark', 'Dark')
                .setValue(this.plugin.settings.theme)
                .onChange(async (value) => {
                    // Type assertion since we control the dropdown options
                    this.plugin.settings.theme = value as 'light' | 'dark' | 'auto';
                    await this.plugin.saveSettings();
                }));

        // Debug Settings Section
        containerEl.createEl('h3', { text: 'Debug' });

        // Debug mode
        new Setting(containerEl)
            .setName('Debug Mode')
            .setDesc('Enable detailed logging to console')
            .addToggle(toggle => toggle
                .setValue(this.plugin.settings.debugMode)
                .onChange(async (value) => {
                    this.plugin.settings.debugMode = value;
                    await this.plugin.saveSettings();
                }));

        // Reset Settings Button
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (Setting.addButton)
        new Setting(containerEl)
            .setName('Reset Settings')
            .setDesc('Reset all settings to default values')
            .addButton(button => button
                .setButtonText('Reset')
                .setWarning()
                .onClick(async () => {
                    this.plugin.settings = Object.assign({}, DEFAULT_SETTINGS);
                    await this.plugin.saveSettings();
                    this.display(); // Refresh the settings tab
                    new Notice('Canvas Review System: Settings reset to defaults');
                }));

        // Footer with version info
        containerEl.createEl('hr');
        containerEl.createEl('p', {
            text: 'Canvas Review System v1.0.0',
            cls: 'setting-item-description'
        });
    }
}
