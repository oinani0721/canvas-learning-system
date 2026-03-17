/**
 * Canvas Learning System - Obsidian Plugin Entry Point
 * Story 1.1: Plugin scaffold (AC-3, AC-4)
 *
 * Registers the MainView, adds a Ribbon icon, and checks
 * backend connectivity on load.
 */

import { Notice, Plugin, type WorkspaceLeaf } from 'obsidian';
import { MainView, VIEW_TYPE_CANVAS_LEARNING } from './src/views/main-view';
import { ApiClient } from './src/services/api-client';

export default class CanvasLearningPlugin extends Plugin {
  private apiClient: ApiClient = new ApiClient();
  private backendOnline = false;

  async onload(): Promise<void> {
    // Register the main view type
    this.registerView(
      VIEW_TYPE_CANVAS_LEARNING,
      (leaf: WorkspaceLeaf) => new MainView(leaf),
    );

    // Add Ribbon icon in the left sidebar
    this.addRibbonIcon('graduation-cap', 'Canvas Learning System', () => {
      this.activateView();
    });

    // Non-blocking backend health check
    this.checkBackendHealth();
  }

  async onunload(): Promise<void> {
    // Detach all leaves of this view type
    this.app.workspace.detachLeavesOfType(VIEW_TYPE_CANVAS_LEARNING);
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
