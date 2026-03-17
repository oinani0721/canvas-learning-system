/**
 * Canvas Learning System - Obsidian Plugin Entry Point
 * Story 1.1: Plugin scaffold (AC-3, AC-4)
 * Story 1.2: Setup wizard integration (AC-1, AC-5, AC-6)
 * Story 1.3: Settings tab registration + loadSettings/saveSettings (AC-1, AC-8)
 *
 * Registers the MainView, adds a Ribbon icon, checks backend connectivity,
 * auto-shows the setup wizard on first launch, and registers the Settings Tab.
 *
 * [Source: _bmad-output/implementation-artifacts/1-3-model-config-settings-panel.md#Task 1]
 */

import { Notice, Plugin, type WorkspaceLeaf } from 'obsidian';
import { MainView, VIEW_TYPE_CANVAS_LEARNING } from './src/views/main-view';
import { ApiClient } from './src/services/api-client';
import { SetupWizardModal } from './src/components/system/SetupWizardModal';
import { CanvasLearningSettingTab } from './src/settings';
import type { CanvasLearningSettings } from './src/types/settings';
import { DEFAULT_SETTINGS } from './src/types/settings';
import { canvasState } from './src/stores/canvas-state';

/**
 * Extended settings stored in data.json.
 * Includes Story 1.2 setupComplete flag + Story 1.3 model config fields.
 */
interface PluginData extends CanvasLearningSettings {
  setupComplete: boolean;
}

const DEFAULT_PLUGIN_DATA: PluginData = {
  ...DEFAULT_SETTINGS,
  setupComplete: false,
};

export default class CanvasLearningPlugin extends Plugin {
  private apiClient: ApiClient = new ApiClient();
  private backendOnline = false;
  settings: PluginData = DEFAULT_PLUGIN_DATA;

  async onload(): Promise<void> {
    // Load persisted settings from data.json
    await this.loadSettings();

    // Point ApiClient to the configured backend URL (Story 1.3 AC-7)
    this.apiClient.setBaseUrl(this.settings.backendUrl);

    // Story 1.4: Initialize IndexedDB + canvas state (AC-6)
    await canvasState.init(this.apiClient);

    // Register the main view type
    this.registerView(
      VIEW_TYPE_CANVAS_LEARNING,
      (leaf: WorkspaceLeaf) => new MainView(leaf),
    );

    // Add Ribbon icon in the left sidebar
    this.addRibbonIcon('graduation-cap', 'Canvas Learning System', () => {
      this.activateView();
    });

    // Register Settings Tab (Story 1.3 AC-1)
    this.addSettingTab(new CanvasLearningSettingTab(this.app, this));

    // Register command: open setup wizard (AC-1)
    this.addCommand({
      id: 'canvas-learning:open-setup-wizard',
      name: 'Canvas: Open Setup Wizard',
      callback: () => {
        this.openSetupWizard();
      },
    });

    // Auto-show setup wizard on first launch (AC-1)
    if (!this.settings.setupComplete) {
      // Defer to ensure Obsidian workspace is fully loaded
      this.app.workspace.onLayoutReady(() => {
        this.openSetupWizard();
      });
    } else {
      // Non-blocking backend health check for returning users
      this.checkBackendHealth();
      // Sync model config to backend (Story 1.3 AC-8)
      this.syncModelConfigToBackend();
    }
  }

  async onunload(): Promise<void> {
    // Story 1.4: Clean up Dexie subscriptions
    canvasState.dispose();
    // Detach all leaves of this view type
    this.app.workspace.detachLeavesOfType(VIEW_TYPE_CANVAS_LEARNING);
  }

  /**
   * Load settings from data.json, merging with defaults.
   * [Source: Story 1.3 Task 1.4]
   */
  private async loadSettings(): Promise<void> {
    const data = await this.loadData();
    this.settings = Object.assign({}, DEFAULT_PLUGIN_DATA, data);
  }

  /**
   * Save current settings to data.json.
   * API keys are stored here in Obsidian's local plugin data — never logged.
   * [Source: Story 1.3 Task 1.4, AC-6]
   */
  async saveSettings(): Promise<void> {
    await this.saveData(this.settings);
    // Sync to backend whenever settings are saved (AC-8)
    this.syncModelConfigToBackend();
  }

  /**
   * Push current model configuration to the backend's in-memory config.
   * Failures are silent — they do not block local settings persistence.
   * [Source: Story 1.3 AC-8]
   */
  private async syncModelConfigToBackend(): Promise<void> {
    const ok = await this.apiClient.postModelConfig(this.settings);
    if (!ok) {
      console.warn(
        '[Canvas Learning] Failed to sync model config to backend (non-blocking)',
      );
    }
  }

  /**
   * Open the Setup Wizard Modal (AC-1, AC-5).
   * On completion: marks setupComplete, saves settings, activates MainView.
   */
  private openSetupWizard(): void {
    const modal = new SetupWizardModal(
      this.app,
      this.apiClient,
      async () => {
        // Mark setup as complete (AC-5)
        this.settings.setupComplete = true;
        await this.saveSettings();
        // Activate the main sidebar view (AC-5)
        await this.activateView();
        new Notice('Canvas Learning System 已准备就绪！', 3000);
      },
    );
    modal.open();
  }

  /**
   * Open the MainView in the right sidebar panel.
   * If it already exists, reveal it instead of creating a duplicate.
   */
  private async activateView(): Promise<void> {
    const { workspace } = this.app;

    let leaf = workspace.getLeavesOfType(VIEW_TYPE_CANVAS_LEARNING)[0];
    if (!leaf) {
      const rightLeaf = workspace.getRightLeaf(false);
      if (!rightLeaf) return;
      leaf = rightLeaf;
      await leaf.setViewState({
        type: VIEW_TYPE_CANVAS_LEARNING,
        active: true,
      });
    }
    workspace.revealLeaf(leaf);
  }

  /**
   * Check backend system health (AC-4).
   * Sets backendOnline flag and shows a Notice (auto-dismiss 3s).
   */
  private async checkBackendHealth(): Promise<void> {
    const health = await this.apiClient.checkHealth();

    if (health) {
      this.backendOnline = true;
      console.log(
        '[Canvas Learning] Backend online:',
        health.status,
        health.components,
      );
      new Notice('Canvas Learning: Backend connected', 3000);
    } else {
      this.backendOnline = false;
      console.warn(
        '[Canvas Learning] Backend unreachable - plugin will work in offline mode',
      );
      new Notice(
        'Canvas Learning: Backend offline - limited functionality',
        3000,
      );
    }
  }
}
