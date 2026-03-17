/**
 * Canvas Learning System - Obsidian Plugin Entry Point
 * Story 1.1: Plugin scaffold (AC-3, AC-4)
 * Story 1.2: Setup wizard integration (AC-1, AC-5, AC-6)
 * Story 1.3: Settings tab registration + loadSettings/saveSettings (AC-1, AC-8)
 * Story 1.5: SyncEngine lifecycle (AC-1, Task 8)
 *
 * Registers the MainView, adds a Ribbon icon, checks backend connectivity,
 * auto-shows the setup wizard on first launch, and registers the Settings Tab.
 *
 * [Source: _bmad-output/implementation-artifacts/1-3-model-config-settings-panel.md#Task 1]
 */

import { Notice, Plugin, SuggestModal, type WorkspaceLeaf } from 'obsidian';
import { MainView, VIEW_TYPE_CANVAS_LEARNING } from './src/views/main-view';
import { ApiClient } from './src/services/api-client';
import { SyncEngine } from './src/services/sync-engine';
import { SetupWizardModal } from './src/components/system/SetupWizardModal';
import { CanvasLearningSettingTab } from './src/settings';
import type { CanvasLearningSettings } from './src/types/settings';
import { DEFAULT_SETTINGS } from './src/types/settings';
import { canvasState } from './src/stores/canvas-state';
import { systemState } from './src/stores/system-state.svelte';
import { IndexingService } from './src/services/indexing-service';
import { DockerManager } from './src/services/docker-manager';
import { BackupManager, type BackupInfo } from './src/services/backup-manager';
import { waitForBackendReady } from './src/services/health-poller';

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

/** Story 1.8: Backup selection modal using Obsidian SuggestModal. */
class BackupSelectModal extends SuggestModal<BackupInfo> {
  private backups: BackupInfo[];
  private onSelect: (backup: BackupInfo) => void;

  constructor(app: import('obsidian').App, backups: BackupInfo[], onSelect: (b: BackupInfo) => void) {
    super(app);
    this.backups = backups;
    this.onSelect = onSelect;
  }

  getSuggestions(query: string): BackupInfo[] {
    const lower = query.toLowerCase();
    return this.backups.filter(b => b.timestamp.toLowerCase().includes(lower));
  }

  renderSuggestion(backup: BackupInfo, el: HTMLElement): void {
    const dateStr = new Date(backup.timestamp).toLocaleString();
    el.createEl('div', { text: dateStr });
    el.createEl('small', { text: `组件: ${backup.components.join(', ')}` });
  }

  onChooseSuggestion(backup: BackupInfo): void {
    this.onSelect(backup);
  }
}

export default class CanvasLearningPlugin extends Plugin {
  private apiClient: ApiClient = new ApiClient();
  private syncEngine: SyncEngine | null = null;
  private indexingService: IndexingService | null = null;
  private dockerManager: DockerManager | null = null;
  private backupManager: BackupManager | null = null;
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

    // Story 1.5: Initialize and start SyncEngine (Task 8.1)
    this.syncEngine = new SyncEngine(this.apiClient);
    this.syncEngine.start();

    // Story 1.6: Initialize IndexingService
    this.indexingService = new IndexingService(this.apiClient);

    // Story 1.8: Initialize Docker and Backup managers
    const vaultPath = (this.app.vault.adapter as any).basePath ?? '';
    const projectPath = vaultPath; // Adjust if needed
    this.dockerManager = new DockerManager(projectPath);
    const pluginDataPath = `${vaultPath}/.obsidian/plugins/canvas-learning-system/data.json`;
    this.backupManager = new BackupManager(projectPath, this.dockerManager, pluginDataPath);

    // Story 1.9: Load subjects from settings into system state
    systemState.loadSubjects(
      this.settings.subjects.map(s => ({ ...s })),
      this.settings.activeSubjectId,
    );
    systemState.setCrossSubjectEnabled(this.settings.crossSubjectEnabled);
    systemState.setCrossSubjectThreshold(this.settings.crossSubjectThreshold);

    // Story 1.8: Register service management commands
    this.registerServiceCommands();

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
    // Story 1.6: Cancel pending OCR requests
    this.indexingService?.cancelAll();
    this.indexingService = null;
    // Story 1.5: Stop SyncEngine (Task 8.1)
    this.syncEngine?.stop();
    this.syncEngine = null;
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

  // ═══════════════════════════════════════════════════════════════════════════
  // Story 1.8: Service Management Commands (AC-1 ~ AC-7)
  // ═══════════════════════════════════════════════════════════════════════════

  private registerServiceCommands(): void {
    // Command: Start backend
    this.addCommand({
      id: 'canvas-start-backend',
      name: 'Canvas: 启动后端',
      callback: async () => {
        if (!this.dockerManager) return;
        const check = await this.dockerManager.checkDockerAvailable();
        if (!check.available) {
          new Notice(check.error ?? 'Docker 不可用', 5000);
          return;
        }
        const notice = new Notice('正在启动后端服务...', 0);
        try {
          await this.dockerManager.startServices();
          notice.setMessage('后端容器已启动，等待 API 就绪...');
          const ready = await waitForBackendReady(this.apiClient);
          if (ready) {
            notice.setMessage('后端服务已启动');
          } else {
            notice.setMessage('后端服务启动但 API 未就绪，请检查日志');
          }
          setTimeout(() => notice.hide(), 3000);
        } catch (e) {
          notice.setMessage(`启动失败: ${e instanceof Error ? e.message : String(e)}`);
          setTimeout(() => notice.hide(), 5000);
        }
      },
    });

    // Command: Restart backend
    this.addCommand({
      id: 'canvas-restart-backend',
      name: 'Canvas: 重启后端',
      callback: async () => {
        if (!this.dockerManager) return;
        const check = await this.dockerManager.checkDockerAvailable();
        if (!check.available) {
          new Notice(check.error ?? 'Docker 不可用', 5000);
          return;
        }
        const notice = new Notice('正在重启后端服务...', 0);
        try {
          await this.dockerManager.restartServices();
          notice.setMessage('后端容器已重启，等待 API 就绪...');
          const ready = await waitForBackendReady(this.apiClient);
          if (ready) {
            notice.setMessage('后端服务已重启');
          } else {
            notice.setMessage('后端服务重启但 API 未就绪，请检查日志');
          }
          setTimeout(() => notice.hide(), 3000);
        } catch (e) {
          notice.setMessage(`重启失败: ${e instanceof Error ? e.message : String(e)}`);
          setTimeout(() => notice.hide(), 5000);
        }
      },
    });

    // Command: Stop backend
    this.addCommand({
      id: 'canvas-stop-backend',
      name: 'Canvas: 停止后端',
      callback: async () => {
        if (!this.dockerManager) return;
        const check = await this.dockerManager.checkDockerAvailable();
        if (!check.available) {
          new Notice(check.error ?? 'Docker 不可用', 5000);
          return;
        }
        const notice = new Notice('正在停止后端服务...', 0);
        try {
          await this.dockerManager.stopServices();
          systemState.setBackendRunning(false);
          notice.setMessage('后端服务已停止');
          setTimeout(() => notice.hide(), 3000);
        } catch (e) {
          notice.setMessage(`停止失败: ${e instanceof Error ? e.message : String(e)}`);
          setTimeout(() => notice.hide(), 5000);
        }
      },
    });

    // Command: Backup data
    this.addCommand({
      id: 'canvas-backup-data',
      name: 'Canvas: 备份数据',
      callback: async () => {
        if (!this.backupManager) return;
        const notice = new Notice('正在备份数据...', 0);
        try {
          const backupPath = await this.backupManager.createBackup((p) => {
            notice.setMessage(`正在备份数据... (${p.step}/${p.totalSteps}) ${p.description}`);
          });
          systemState.setLastBackupTime(new Date());
          notice.setMessage(`备份完成：${backupPath}`);
          setTimeout(() => notice.hide(), 5000);
        } catch (e) {
          notice.setMessage(`备份失败: ${e instanceof Error ? e.message : String(e)}`);
          setTimeout(() => notice.hide(), 5000);
        }
      },
    });

    // Command: Restore data
    this.addCommand({
      id: 'canvas-restore-data',
      name: 'Canvas: 恢复数据',
      callback: async () => {
        if (!this.backupManager) return;
        const backups = this.backupManager.listBackups();
        if (backups.length === 0) {
          new Notice('没有可用的备份点', 3000);
          return;
        }

        const modal = new BackupSelectModal(this.app, backups, async (selected) => {
          const confirmed = confirm('恢复将覆盖当前数据，是否继续？');
          if (!confirmed) return;

          const notice = new Notice('正在恢复数据...', 0);
          try {
            await this.backupManager!.restoreBackup(selected.path, (p) => {
              notice.setMessage(`正在恢复数据... (${p.step}/${p.totalSteps}) ${p.description}`);
            });
            notice.setMessage('数据恢复完成');
            setTimeout(() => notice.hide(), 3000);
          } catch (e) {
            notice.setMessage(`恢复失败: ${e instanceof Error ? e.message : String(e)}`);
            setTimeout(() => notice.hide(), 5000);
          }
        });
        modal.open();
      },
    });
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
