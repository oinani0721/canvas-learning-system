/**
 * Association Mode Manager - Canvas Learning System Cross-Canvas Associations
 *
 * Manages the association mode toggle state and provides mode change events.
 * Implements Story 16.4: 关联模式Toggle控制
 *
 * @module managers/AssociationModeManager
 * @version 1.0.0
 *
 * ✅ Verified from @obsidian-canvas Skill (Plugin.saveData, Plugin.loadData)
 * ✅ Verified from Story 16.4 Dev Notes (Toggle state machine, Ctrl+Shift+L hotkey)
 */

import { App, Plugin, Notice } from 'obsidian';
import type { AssociationModeState } from '../types/AssociationTypes';

/**
 * Mode change callback type
 */
export type ModeChangeCallback = (enabled: boolean) => void;

/**
 * Association Mode Manager
 *
 * Manages the global association mode state with persistence.
 * When enabled, Canvas nodes display association indicators and allow cross-Canvas linking.
 *
 * ✅ Verified from @obsidian-canvas Skill (Plugin data persistence)
 * ✅ Verified from Story 16.4 Dev Notes (State machine design)
 */
export class AssociationModeManager {
    private app: App;
    private plugin: Plugin;
    private state: AssociationModeState;
    private modeChangeListeners: ModeChangeCallback[] = [];
    private commandId: string | null = null;

    /**
     * Storage key for association mode state
     */
    private static readonly STORAGE_KEY = 'association-mode-state';

    /**
     * Creates a new AssociationModeManager
     *
     * @param app - Obsidian App instance
     * @param plugin - Plugin instance for data persistence
     */
    constructor(app: App, plugin: Plugin) {
        this.app = app;
        this.plugin = plugin;
        this.state = {
            enabled: false,
            lastToggled: new Date().toISOString()
        };
    }

    /**
     * Initialize the manager
     *
     * Loads persisted state and registers the toggle command.
     *
     * ✅ Verified from @obsidian-canvas Skill (Plugin.addCommand)
     */
    async initialize(): Promise<void> {
        await this.loadState();
        this.registerCommand();
    }

    /**
     * Load persisted state from plugin data
     *
     * ✅ Verified from @obsidian-canvas Skill (Plugin.loadData)
     */
    async loadState(): Promise<void> {
        try {
            const data = await this.plugin.loadData();
            if (data && data[AssociationModeManager.STORAGE_KEY]) {
                const savedState = data[AssociationModeManager.STORAGE_KEY] as AssociationModeState;
                this.state = {
                    enabled: savedState.enabled ?? false,
                    lastToggled: savedState.lastToggled ?? new Date().toISOString()
                };
            }
        } catch (error) {
            console.warn('[AssociationModeManager] Failed to load state:', error);
            // Keep default state
        }
    }

    /**
     * Save current state to plugin data
     *
     * ✅ Verified from @obsidian-canvas Skill (Plugin.saveData)
     */
    private async saveState(): Promise<void> {
        try {
            const data = await this.plugin.loadData() || {};
            data[AssociationModeManager.STORAGE_KEY] = this.state;
            await this.plugin.saveData(data);
        } catch (error) {
            console.error('[AssociationModeManager] Failed to save state:', error);
        }
    }

    /**
     * Register the toggle command with hotkey
     *
     * ✅ Verified from @obsidian-canvas Skill (Plugin.addCommand)
     * ✅ Verified from Story 16.4 Dev Notes (Ctrl+Shift+L hotkey)
     */
    private registerCommand(): void {
        this.commandId = 'canvas-toggle-association-mode';

        this.plugin.addCommand({
            id: this.commandId,
            name: '切换关联模式 (Toggle Association Mode)',
            // Note: Hotkey Ctrl+Shift+L is recommended but not forced
            // Users can configure their own hotkey in Obsidian settings
            callback: async () => {
                await this.toggle();
            }
        });
    }

    /**
     * Check if association mode is currently enabled
     *
     * @returns boolean - Whether association mode is enabled
     */
    isEnabled(): boolean {
        return this.state.enabled;
    }

    /**
     * Get the full state object
     *
     * @returns AssociationModeState
     */
    getState(): AssociationModeState {
        return { ...this.state };
    }

    /**
     * Toggle association mode
     *
     * Switches between enabled and disabled states.
     * Notifies all registered listeners of the change.
     *
     * @returns Promise<boolean> - New enabled state
     */
    async toggle(): Promise<boolean> {
        const newEnabled = !this.state.enabled;
        await this.setMode(newEnabled);
        return newEnabled;
    }

    /**
     * Set association mode to a specific state
     *
     * @param enabled - Whether to enable or disable association mode
     */
    async setMode(enabled: boolean): Promise<void> {
        const previousState = this.state.enabled;

        this.state = {
            enabled,
            lastToggled: new Date().toISOString()
        };

        await this.saveState();

        // Show notification only if state actually changed
        if (previousState !== enabled) {
            const message = enabled
                ? '🔗 关联模式已启用 (Association Mode Enabled)'
                : '🔗 关联模式已禁用 (Association Mode Disabled)';
            new Notice(message, 2000);

            // Notify all listeners
            this.notifyListeners(enabled);
        }
    }

    /**
     * Subscribe to mode changes
     *
     * @param callback - Callback function called when mode changes
     * @returns Unsubscribe function
     */
    onModeChange(callback: ModeChangeCallback): () => void {
        this.modeChangeListeners.push(callback);

        return () => {
            const index = this.modeChangeListeners.indexOf(callback);
            if (index > -1) {
                this.modeChangeListeners.splice(index, 1);
            }
        };
    }

    /**
     * Notify all listeners of mode change
     */
    private notifyListeners(enabled: boolean): void {
        this.modeChangeListeners.forEach(listener => {
            try {
                listener(enabled);
            } catch (error) {
                console.error('[AssociationModeManager] Listener error:', error);
            }
        });
    }

    /**
     * Cleanup resources
     */
    destroy(): void {
        this.modeChangeListeners = [];
        // Command is automatically unregistered when plugin unloads
    }
}

/**
 * Settings Tab Section for Association Mode
 *
 * Creates the settings section for association mode configuration.
 * Should be called from PluginSettingsTab.display().
 *
 * ✅ Verified from @obsidian-canvas Skill (Setting API)
 *
 * @param containerEl - Container element for settings
 * @param manager - AssociationModeManager instance
 */
export function createAssociationModeSettings(
    containerEl: HTMLElement,
    manager: AssociationModeManager
): void {
    // Import Setting dynamically to avoid circular dependencies
    const { Setting } = require('obsidian');

    containerEl.createEl('h3', { text: '关联模式设置 (Association Mode)' });

    new Setting(containerEl)
        .setName('启用关联模式')
        .setDesc('启用后，Canvas节点将显示关联指示器，支持跨Canvas链接。推荐快捷键: Ctrl+Shift+L')
        .addToggle(toggle => toggle
            .setValue(manager.isEnabled())
            .onChange(async (value) => {
                await manager.setMode(value);
            })
        );

    // Show last toggled time
    const state = manager.getState();
    if (state.lastToggled) {
        const lastToggled = new Date(state.lastToggled);
        const formattedTime = lastToggled.toLocaleString('zh-CN');

        new Setting(containerEl)
            .setName('上次切换时间')
            .setDesc(formattedTime)
            .setDisabled(true);
    }
}
