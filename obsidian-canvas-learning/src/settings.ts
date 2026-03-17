/**
 * Canvas Learning System - Settings Tab
 * Story 1.3: Model Configuration & System Settings Panel
 *
 * Implements the PluginSettingTab using Obsidian's native Setting API.
 * Contains 6 configuration sections:
 *   1. System health status
 *   2. Chat model
 *   3. Scoring model
 *   4. Embedding model (read-only)
 *   5. Backend connection
 *   6. Data management
 *
 * [Source: _bmad-output/implementation-artifacts/1-3-model-config-settings-panel.md]
 * [Source: architecture.md#Authentication & Security — API Key security]
 */

import { App, Notice, PluginSettingTab, Setting } from 'obsidian';

import type CanvasLearningPlugin from '../main';
import { ApiClient } from './services/api-client';
import type { ComponentStatus } from './types/api';
import type { LLMProvider } from './types/settings';

/** Display labels for LLM providers. */
const PROVIDER_LABELS: Record<LLMProvider, string> = {
  gemini: 'Google Gemini',
  anthropic: 'Anthropic Claude',
  openai: 'OpenAI GPT',
  ollama: 'Local (Ollama / LM Studio)',
};

/** Placeholder hint per provider. */
const MODEL_PLACEHOLDERS: Record<LLMProvider, string> = {
  gemini: 'gemini-2.0-flash',
  anthropic: 'claude-3-5-sonnet-20241022',
  openai: 'gpt-4o',
  ollama: 'llama3',
};

/**
 * Map a component status string to a coloured icon.
 *
 * [Source: Story 1.3 AC-2]
 */
function statusIcon(status: string): string {
  switch (status) {
    case 'healthy':
      return '\u{1F7E2}'; // green circle
    case 'unhealthy':
      return '\u{1F534}'; // red circle
    default:
      return '\u{1F7E1}'; // yellow circle
  }
}

/**
 * Canvas Learning System Settings Tab.
 *
 * [Source: Story 1.3 Task 1 — PluginSettingTab registration]
 */
export class CanvasLearningSettingTab extends PluginSettingTab {
  plugin: CanvasLearningPlugin;
  private apiClient: ApiClient;

  constructor(app: App, plugin: CanvasLearningPlugin) {
    super(app, plugin);
    this.plugin = plugin;
    this.apiClient = new ApiClient(plugin.settings.backendUrl);
  }

  /* ═══════════════════════════════════════════════════════════════════════════
   * display() — main render entry point
   * ═══════════════════════════════════════════════════════════════════════════ */

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    // Ensure the ApiClient points to the latest backend URL
    this.apiClient.setBaseUrl(this.plugin.settings.backendUrl);

    // ── Section 1: System health status ──────────────────────────────────────
    this.renderHealthSection(containerEl);

    // ── Section 2: Chat model ────────────────────────────────────────────────
    this.renderChatModelSection(containerEl);

    // ── Section 3: Scoring model ─────────────────────────────────────────────
    this.renderScoringModelSection(containerEl);

    // ── Section 4: Embedding model (read-only) ───────────────────────────────
    this.renderEmbeddingSection(containerEl);

    // ── Section 5: Backend connection ────────────────────────────────────────
    this.renderBackendSection(containerEl);

    // ── Section 6: Data management ───────────────────────────────────────────
    this.renderDataManagementSection(containerEl);
  }

  /* ═══════════════════════════════════════════════════════════════════════════
   * Section 1: System Health Status (AC-2)
   * ═══════════════════════════════════════════════════════════════════════════ */

  private renderHealthSection(containerEl: HTMLElement): void {
    containerEl.createEl('h2', { text: '\u{2764}\u{FE0F} System Status' });

    // Container for status rows — will be repopulated on refresh
    const statusContainer = containerEl.createDiv({
      cls: 'cls-health-status-container',
    });

    // Initial fetch
    this.refreshHealthStatus(statusContainer);

    // "Refresh" button
    new Setting(containerEl).addButton((btn) =>
      btn.setButtonText('Refresh').onClick(() => {
        this.refreshHealthStatus(statusContainer);
      }),
    );
  }

  /**
   * Fetch health data and render 5 component rows.
   *
   * [Source: Story 1.3 Task 2.2 — call checkHealth()]
   * [Source: Story 1.3 Task 2.5 — backend unreachable → all red]
   */
  private async refreshHealthStatus(container: HTMLElement): Promise<void> {
    container.empty();
    container.createEl('p', {
      text: 'Checking...',
      cls: 'cls-health-loading',
    });

    const health = await this.apiClient.checkHealth();

    container.empty();

    if (!health) {
      // Backend unreachable — all red
      const components = [
        'Docker',
        'Backend API',
        'Neo4j',
        'LLM API',
        'LanceDB',
      ];
      for (const name of components) {
        this.renderStatusRow(container, name, 'unhealthy', 'Unreachable');
      }
      return;
    }

    // Backend is reachable → Docker and Backend API are healthy
    this.renderStatusRow(container, 'Docker', 'healthy', 'Running');
    this.renderStatusRow(container, 'Backend API', 'healthy', 'Connected');

    // Map remaining components from health response
    const componentMap = new Map<string, ComponentStatus>();
    for (const c of health.components) {
      componentMap.set(c.name, c);
    }

    const neo4j = componentMap.get('neo4j');
    this.renderStatusRow(
      container,
      'Neo4j',
      neo4j?.status ?? 'unknown',
      neo4j?.message ?? '',
    );

    const ollama = componentMap.get('ollama');
    this.renderStatusRow(
      container,
      'LLM API',
      ollama?.status ?? 'unknown',
      ollama?.message ?? '',
    );

    const lancedb = componentMap.get('lancedb');
    this.renderStatusRow(
      container,
      'LanceDB',
      lancedb?.status ?? 'unknown',
      lancedb?.message ?? '',
    );
  }

  /** Render a single status row: icon + name + message. */
  private renderStatusRow(
    container: HTMLElement,
    name: string,
    status: string,
    message: string,
  ): void {
    const row = container.createDiv({ cls: 'cls-health-row' });
    row.style.display = 'flex';
    row.style.alignItems = 'center';
    row.style.gap = '8px';
    row.style.padding = '4px 0';

    row.createSpan({ text: statusIcon(status) });
    const label = row.createSpan({ text: name });
    label.style.fontWeight = '600';
    label.style.minWidth = '100px';

    if (message) {
      const msg = row.createSpan({ text: message });
      msg.style.color = 'var(--text-muted)';
      msg.style.fontSize = '0.85em';
    }
  }

  /* ═══════════════════════════════════════════════════════════════════════════
   * Section 2: Chat Model (AC-3)
   * ═══════════════════════════════════════════════════════════════════════════ */

  private renderChatModelSection(containerEl: HTMLElement): void {
    containerEl.createEl('h2', { text: 'Chat Model' });
    containerEl.createEl('p', {
      text: 'Model used for Agent conversations with you.',
      cls: 'setting-item-description',
    });

    this.renderModelConfig(containerEl, 'chat');
  }

  /* ═══════════════════════════════════════════════════════════════════════════
   * Section 3: Scoring Model (AC-4)
   * ═══════════════════════════════════════════════════════════════════════════ */

  private renderScoringModelSection(containerEl: HTMLElement): void {
    containerEl.createEl('h2', { text: 'Scoring Model' });
    containerEl.createEl('p', {
      text: 'Model used for AutoSCORE grading and knowledge extraction (independent from chat).',
      cls: 'setting-item-description',
    });

    this.renderModelConfig(containerEl, 'scoring');
  }

  /** Helper: get the current provider for a role. */
  private getProvider(role: 'chat' | 'scoring'): LLMProvider {
    return role === 'chat'
      ? this.plugin.settings.chatProvider
      : this.plugin.settings.scoringProvider;
  }

  /** Helper: get the current model name for a role. */
  private getModel(role: 'chat' | 'scoring'): string {
    return role === 'chat'
      ? this.plugin.settings.chatModel
      : this.plugin.settings.scoringModel;
  }

  /** Helper: get the current API key for a role. */
  private getApiKey(role: 'chat' | 'scoring'): string {
    return role === 'chat'
      ? this.plugin.settings.chatApiKey
      : this.plugin.settings.scoringApiKey;
  }

  /** Helper: set provider for a role. */
  private setProvider(role: 'chat' | 'scoring', val: string): void {
    if (role === 'chat') {
      this.plugin.settings.chatProvider = val as LLMProvider;
    } else {
      this.plugin.settings.scoringProvider = val as LLMProvider;
    }
  }

  /** Helper: set model name for a role. */
  private setModel(role: 'chat' | 'scoring', val: string): void {
    if (role === 'chat') {
      this.plugin.settings.chatModel = val;
    } else {
      this.plugin.settings.scoringModel = val;
    }
  }

  /** Helper: set API key for a role. */
  private setApiKey(role: 'chat' | 'scoring', val: string): void {
    if (role === 'chat') {
      this.plugin.settings.chatApiKey = val;
    } else {
      this.plugin.settings.scoringApiKey = val;
    }
  }

  /**
   * Reusable UI block for chat / scoring model configuration.
   * Renders: provider dropdown + model name + API key (password) + test button.
   *
   * [Source: Story 1.3 Task 3 / Task 4]
   */
  private renderModelConfig(
    containerEl: HTMLElement,
    role: 'chat' | 'scoring',
  ): void {
    // ── Provider dropdown ────────────────────────────────────────────────────
    new Setting(containerEl)
      .setName('Provider')
      .setDesc('Select LLM provider')
      .addDropdown((dd) => {
        for (const [value, label] of Object.entries(PROVIDER_LABELS)) {
          dd.addOption(value, label);
        }
        dd.setValue(this.getProvider(role));
        dd.onChange(async (val) => {
          this.setProvider(role, val);
          await this.plugin.saveSettings();
          // Re-render to update placeholder
          this.display();
        });
      });

    // ── Model name ───────────────────────────────────────────────────────────
    new Setting(containerEl)
      .setName('Model Name')
      .setDesc('Model identifier sent to the provider')
      .addText((text) => {
        text
          .setPlaceholder(
            MODEL_PLACEHOLDERS[this.getProvider(role)] ?? '',
          )
          .setValue(this.getModel(role))
          .onChange(async (val) => {
            this.setModel(role, val);
            await this.plugin.saveSettings();
          });
      });

    // ── API Key (password + toggle) ──────────────────────────────────────────
    // [Source: Story 1.3 AC-6 — password type, toggle, first-time notice]
    const apiKeySetting = new Setting(containerEl)
      .setName('API Key')
      .setDesc('Provider API key (stored locally only)');

    apiKeySetting.addText((text) => {
      text.inputEl.type = 'password';
      text.inputEl.style.width = '260px';
      text
        .setPlaceholder('sk-...')
        .setValue(this.getApiKey(role))
        .onChange(async (val) => {
          // Show first-time security notice (AC-6)
          if (!this.plugin.settings.apiKeyNoticeShown && val.length > 0) {
            new Notice(
              'Security notice: conversation content will be sent to the selected LLM API provider.',
              8000,
            );
            this.plugin.settings.apiKeyNoticeShown = true;
          }
          this.setApiKey(role, val);
          await this.plugin.saveSettings();
        });

      // Eye toggle for show/hide
      const toggleBtn = apiKeySetting.controlEl.createEl('button', {
        text: 'Show',
        cls: 'cls-api-key-toggle',
      });
      toggleBtn.style.marginLeft = '8px';
      toggleBtn.addEventListener('click', () => {
        if (text.inputEl.type === 'password') {
          text.inputEl.type = 'text';
          toggleBtn.textContent = 'Hide';
        } else {
          text.inputEl.type = 'password';
          toggleBtn.textContent = 'Show';
        }
      });
    });

    // ── Test Connection button ───────────────────────────────────────────────
    // [Source: Story 1.3 AC-3 — test connection, green/red feedback]
    const testSetting = new Setting(containerEl).setName('');

    const feedbackEl = testSetting.controlEl.createSpan({
      cls: 'cls-test-feedback',
    });
    feedbackEl.style.marginRight = '8px';

    testSetting.addButton((btn) =>
      btn.setButtonText('Test Connection').onClick(async () => {
        feedbackEl.textContent = 'Testing...';
        feedbackEl.style.color = 'var(--text-muted)';

        const result = await this.apiClient.testLlmConnection(
          this.getProvider(role),
          this.getModel(role),
          this.getApiKey(role),
        );

        if (result.status === 'success') {
          feedbackEl.textContent = '\u2713 Connected';
          feedbackEl.style.color = 'var(--text-success, #4caf50)';
        } else {
          feedbackEl.textContent = `\u2717 ${result.error ?? 'Failed'}`;
          feedbackEl.style.color = 'var(--text-error, #f44336)';
        }
      }),
    );
  }

  /* ═══════════════════════════════════════════════════════════════════════════
   * Section 4: Embedding Model — Read-only (AC-5)
   * ═══════════════════════════════════════════════════════════════════════════ */

  private renderEmbeddingSection(containerEl: HTMLElement): void {
    containerEl.createEl('h2', { text: 'Embedding Model' });

    const statusEl = containerEl.createDiv({ cls: 'cls-embedding-status' });
    statusEl.style.padding = '8px 0';

    // Derive Ollama status from the latest health check
    this.apiClient.checkHealth().then((health) => {
      const ollama = health?.components.find((c) => c.name === 'ollama');
      const icon =
        ollama?.status === 'healthy'
          ? '\u{1F7E2}'
          : '\u{1F534}';
      const label =
        ollama?.status === 'healthy' ? 'Ready' : 'Not Ready';

      statusEl.textContent = `bge-m3 \u00B7 Ollama \u00B7 ${icon} ${label}`;
    });
  }

  /* ═══════════════════════════════════════════════════════════════════════════
   * Section 5: Backend Connection (AC-7)
   * ═══════════════════════════════════════════════════════════════════════════ */

  private renderBackendSection(containerEl: HTMLElement): void {
    containerEl.createEl('h2', { text: 'Backend Connection' });

    new Setting(containerEl)
      .setName('Backend API Address')
      .setDesc('FastAPI backend URL')
      .addText((text) =>
        text
          .setPlaceholder('http://localhost:8001')
          .setValue(this.plugin.settings.backendUrl)
          .onChange(async (val) => {
            this.plugin.settings.backendUrl = val;
            this.apiClient.setBaseUrl(val);
            await this.plugin.saveSettings();
          }),
      );

    new Setting(containerEl)
      .setName('Neo4j Address')
      .setDesc('Neo4j Bolt connection URI')
      .addText((text) =>
        text
          .setPlaceholder('bolt://localhost:7689')
          .setValue(this.plugin.settings.neo4jUrl)
          .onChange(async (val) => {
            this.plugin.settings.neo4jUrl = val;
            await this.plugin.saveSettings();
          }),
      );
  }

  /* ═══════════════════════════════════════════════════════════════════════════
   * Section 6: Data Management — placeholders (AC-1 / Task 8)
   * ═══════════════════════════════════════════════════════════════════════════ */

  private renderDataManagementSection(containerEl: HTMLElement): void {
    containerEl.createEl('h2', { text: 'Data Management' });

    new Setting(containerEl)
      .setName('Manual Backup')
      .setDesc('Create a backup of all learning data')
      .addButton((btn) =>
        btn.setButtonText('Backup').onClick(() => {
          new Notice('Backup will be available in Story 1.8');
        }),
      );

    new Setting(containerEl)
      .setName('Rebuild Index')
      .setDesc('Re-index all canvas files for search')
      .addButton((btn) =>
        btn.setButtonText('Rebuild').onClick(() => {
          new Notice('Index rebuild will be available in Story 2.7');
        }),
      );
  }
}
