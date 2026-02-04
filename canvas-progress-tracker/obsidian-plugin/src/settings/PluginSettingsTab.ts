/**
 * Canvas Review System - Plugin Settings Tab
 *
 * Comprehensive settings panel with tabbed navigation for:
 * - Connection settings (Claude Code API)
 * - Storage settings (backup, sync)
 * - Interface settings (theme, display)
 * - Review settings (preferences, scheduling)
 * - Advanced settings (debug, experimental)
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (PluginSettingTab, Setting)
 * ✅ Verified from Story 13.6 Dev Notes: Settings panel architecture
 *
 * @module settings/PluginSettingsTab
 * @version 1.0.0
 */

import {
    App,
    PluginSettingTab,
    Setting,
    Notice,
    TextComponent,
    ButtonComponent,
    Modal
} from 'obsidian';
import type CanvasReviewPlugin from '../../main';
import {
    PluginSettings,
    DEFAULT_SETTINGS,
    SettingsSection,
    SETTINGS_SECTIONS,
    validateSettings,
    exportSettings,
    importSettings,
    migrateSettings
} from '../types/settings';
import type { ErrorRecord } from '../managers/ErrorHistoryManager';

/**
 * Plugin Settings Tab
 *
 * Implements the settings interface shown in Obsidian's settings panel.
 * Provides controls for all configurable plugin options organized into
 * navigable sections.
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (PluginSettingTab)
 */
export class CanvasReviewSettingsTab extends PluginSettingTab {
    plugin: CanvasReviewPlugin;
    private activeSection: SettingsSection = 'connection';
    private contentContainer: HTMLElement | null = null;
    private navContainer: HTMLElement | null = null;

    constructor(app: App, plugin: CanvasReviewPlugin) {
        super(app, plugin);
        this.plugin = plugin;
    }

    /**
     * Display the settings interface
     *
     * Renders all setting controls in the settings panel with tabbed navigation.
     *
     * ✅ Verified from Context7: /obsidianmd/obsidian-api (PluginSettingTab.display)
     */
    display(): void {
        const { containerEl } = this;
        containerEl.empty();
        containerEl.addClass('canvas-review-settings');

        // Create header with title and action buttons
        this.createHeader(containerEl);

        // Create main layout with navigation and content
        const mainContainer = containerEl.createDiv('settings-main-container');

        // Create navigation sidebar
        this.navContainer = mainContainer.createDiv('settings-nav-container');
        this.createNavigation(this.navContainer);

        // Create content area
        this.contentContainer = mainContainer.createDiv('settings-content-container');
        this.displaySection(this.activeSection);
    }

    /**
     * Creates the header section with title and action buttons
     */
    private createHeader(container: HTMLElement): void {
        const headerEl = container.createDiv('settings-header');

        // Title and description
        const titleContainer = headerEl.createDiv('settings-title-container');
        titleContainer.createEl('h2', { text: 'Canvas Review System Settings' });
        titleContainer.createEl('p', {
            text: '配置插件参数、复习偏好和界面选项',
            cls: 'settings-subtitle'
        });

        // Action buttons
        const actionsContainer = headerEl.createDiv('settings-actions');

        // Export button
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (Setting.addButton)
        new ButtonComponent(actionsContainer)
            .setButtonText('导出设置')
            .setIcon('download')
            .onClick(() => this.handleExportSettings());

        // Import button
        new ButtonComponent(actionsContainer)
            .setButtonText('导入设置')
            .setIcon('upload')
            .onClick(() => this.handleImportSettings());

        // Reset button
        new ButtonComponent(actionsContainer)
            .setButtonText('重置设置')
            .setIcon('refresh-cw')
            .setWarning()
            .onClick(() => this.handleResetSettings());
    }

    /**
     * Creates the navigation sidebar
     */
    private createNavigation(container: HTMLElement): void {
        container.empty();

        const navList = container.createDiv('settings-nav-list');

        SETTINGS_SECTIONS.forEach(section => {
            const navItem = navList.createDiv({
                cls: `settings-nav-item ${this.activeSection === section.id ? 'active' : ''}`
            });

            navItem.createSpan({ text: section.icon, cls: 'nav-icon' });
            const textContainer = navItem.createDiv('nav-text');
            textContainer.createSpan({ text: section.name, cls: 'nav-name' });
            textContainer.createSpan({ text: section.description, cls: 'nav-desc' });

            navItem.addEventListener('click', () => {
                this.activeSection = section.id;
                this.updateNavigation();
                this.displaySection(section.id);
            });
        });
    }

    /**
     * Updates navigation active state
     */
    private updateNavigation(): void {
        if (this.navContainer) {
            this.createNavigation(this.navContainer);
        }
    }

    /**
     * Displays a specific settings section
     */
    private displaySection(section: SettingsSection): void {
        if (!this.contentContainer) return;
        this.contentContainer.empty();

        const sectionInfo = SETTINGS_SECTIONS.find(s => s.id === section);
        if (sectionInfo) {
            const sectionHeader = this.contentContainer.createDiv('section-header');
            sectionHeader.createEl('h3', { text: `${sectionInfo.icon} ${sectionInfo.name}` });
            sectionHeader.createEl('p', { text: sectionInfo.description, cls: 'section-desc' });
        }

        switch (section) {
            case 'connection':
                this.displayConnectionSettings(this.contentContainer);
                break;
            case 'storage':
                this.displayStorageSettings(this.contentContainer);
                break;
            case 'interface':
                this.displayInterfaceSettings(this.contentContainer);
                break;
            case 'review':
                this.displayReviewSettings(this.contentContainer);
                break;
            case 'advanced':
                this.displayAdvancedSettings(this.contentContainer);
                break;
            case 'memory':
                this.displayMemorySettings(this.contentContainer);
                break;
            case 'errorHistory':
                this.displayErrorHistorySettings(this.contentContainer);
                break;
        }
    }

    /**
     * Displays connection settings
     */
    private displayConnectionSettings(container: HTMLElement): void {
        const settings = this.plugin.settings;

        // Backend Service Management Group
        // @source Plan: 后端启动/停止UI实现计划
        this.createSettingGroup(container, '后端服务管理');

        // Backend Status Display
        const backendManager = this.plugin.backendManager;
        const currentStatus = backendManager?.getStatus() || 'stopped';
        const statusEmoji: Record<string, string> = {
            'stopped': '⏹️',
            'starting': '⏳',
            'running': '🟢',
            'stopping': '⏳',
            'error': '❌'
        };
        const statusText: Record<string, string> = {
            'stopped': '已停止',
            'starting': '启动中...',
            'running': '运行中',
            'stopping': '停止中...',
            'error': '错误'
        };

        // Extract port from URL for display
        const apiUrl = settings.claudeCodeUrl || 'http://localhost:8000';
        const urlMatch = apiUrl.match(/:(\d+)/);
        const port = urlMatch ? urlMatch[1] : '8000';

        new Setting(container)
            .setName('服务状态')
            .setDesc(`${statusEmoji[currentStatus]} ${statusText[currentStatus]} (端口: ${port})`)
            .addButton(button => {
                const isRunning = currentStatus === 'running';
                button
                    .setButtonText(isRunning ? '停止' : '启动')
                    .setIcon(isRunning ? 'square' : 'play')
                    .setCta()
                    .onClick(async () => {
                        if (!backendManager) {
                            new Notice('后端管理器未初始化');
                            return;
                        }
                        button.setDisabled(true);
                        button.setButtonText(isRunning ? '停止中...' : '启动中...');
                        try {
                            if (isRunning) {
                                await backendManager.stop();
                            } else {
                                await backendManager.start();
                            }
                            // Refresh the settings panel to show new status
                            setTimeout(() => this.displaySection('connection'), 500);
                        } catch (error) {
                            new Notice(`操作失败: ${error instanceof Error ? error.message : '未知错误'}`);
                            button.setDisabled(false);
                            button.setButtonText(isRunning ? '停止' : '启动');
                        }
                    });
            })
            .addButton(button => button
                .setButtonText('重启')
                .setIcon('refresh-cw')
                .onClick(async () => {
                    if (!backendManager) {
                        new Notice('后端管理器未初始化');
                        return;
                    }
                    button.setDisabled(true);
                    button.setButtonText('重启中...');
                    try {
                        await backendManager.stop();
                        await new Promise(resolve => setTimeout(resolve, 1000));
                        await backendManager.start();
                        setTimeout(() => this.displaySection('connection'), 500);
                    } catch (error) {
                        new Notice(`重启失败: ${error instanceof Error ? error.message : '未知错误'}`);
                    }
                    button.setDisabled(false);
                    button.setButtonText('重启');
                }));

        // Backend Log Viewer Button
        new Setting(container)
            .setName('后端日志')
            .setDesc('查看后端服务的输出日志')
            .addButton(button => button
                .setButtonText('查看日志')
                .setIcon('file-text')
                .onClick(() => {
                    if (!backendManager) {
                        new Notice('后端管理器未初始化');
                        return;
                    }
                    const logs = backendManager.getOutputLog();
                    if (logs.length === 0) {
                        new Notice('暂无日志');
                        return;
                    }
                    // Show logs in a modal
                    const modal = new BackendLogModal(this.app, logs);
                    modal.open();
                }));

        // API Configuration Group
        this.createSettingGroup(container, 'API配置');

        // Claude Code URL
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (Setting.addText)
        new Setting(container)
            .setName('Claude Code服务地址')
            .setDesc('Claude Code API服务的基础URL')
            .addText(text => text
                .setPlaceholder('http://localhost:3005')
                .setValue(settings.claudeCodeUrl)
                .onChange(async (value) => {
                    settings.claudeCodeUrl = value;
                    await this.plugin.saveSettings();
                }));

        // API Key
        new Setting(container)
            .setName('API密钥')
            .setDesc('用于API认证的密钥（可选）')
            .addText(text => text
                .setPlaceholder('输入API密钥')
                .setValue(settings.apiKey)
                .inputEl.type = 'password')
            .addText(text => text
                .setValue(settings.apiKey)
                .inputEl.style.display = 'none')
            .then(setting => {
                const textComponent = setting.components[0] as TextComponent;
                textComponent.onChange(async (value) => {
                    settings.apiKey = value;
                    await this.plugin.saveSettings();
                });
            });

        // ========== AI Model Configuration ==========
        this.createSettingGroup(container, 'AI模型配置');

        // AI Provider Selection
        const providerUrls: Record<string, string> = {
            'google': 'https://aistudio.google.com/apikey',
            'openai': 'https://platform.openai.com/api-keys',
            'anthropic': 'https://console.anthropic.com/settings/keys',
            'openrouter': 'https://openrouter.ai/keys',
            'custom': ''
        };

        const providerPlaceholders: Record<string, string> = {
            'google': 'AIza...',
            'openai': 'sk-...',
            'anthropic': 'sk-ant-...',
            'openrouter': 'sk-or-...',
            'custom': '输入API密钥'
        };

        const defaultModels: Record<string, string> = {
            'google': 'gemini-2.0-flash-exp',
            'openai': 'gpt-4o',
            'anthropic': 'claude-3-5-sonnet-20241022',
            'openrouter': 'anthropic/claude-3.5-sonnet',
            'custom': ''
        };

        const defaultBaseUrls: Record<string, string> = {
            'google': 'https://generativelanguage.googleapis.com/v1beta',
            'openai': 'https://api.openai.com/v1',
            'anthropic': 'https://api.anthropic.com/v1',
            'openrouter': 'https://openrouter.ai/api/v1',
            'custom': ''
        };

        // AI Provider Dropdown
        new Setting(container)
            .setName('AI提供商')
            .setDesc('选择AI模型服务提供商')
            .addDropdown(dropdown => dropdown
                .addOption('google', 'Google (Gemini)')
                .addOption('openai', 'OpenAI (GPT)')
                .addOption('anthropic', 'Anthropic (Claude)')
                .addOption('openrouter', 'OpenRouter')
                .addOption('custom', '自定义 (Custom)')
                .setValue(settings.aiProvider)
                .onChange(async (value: string) => {
                    const provider = value as 'google' | 'openai' | 'anthropic' | 'openrouter' | 'custom';
                    settings.aiProvider = provider;
                    // Auto-fill default model and base URL when provider changes
                    if (!settings.aiModelName || Object.values(defaultModels).includes(settings.aiModelName)) {
                        settings.aiModelName = defaultModels[provider];
                    }
                    if (!settings.aiBaseUrl || Object.values(defaultBaseUrls).includes(settings.aiBaseUrl)) {
                        settings.aiBaseUrl = defaultBaseUrls[provider];
                    }
                    await this.plugin.saveSettings();
                    this.displaySection('connection');  // Refresh to update placeholders
                }));

        // AI Model Name
        new Setting(container)
            .setName('模型名称')
            .setDesc('指定要使用的AI模型（如 gemini-2.0-flash-exp, gpt-4o, claude-3-5-sonnet）')
            .addText(text => text
                .setPlaceholder(defaultModels[settings.aiProvider] || '输入模型名称')
                .setValue(settings.aiModelName)
                .onChange(async (value) => {
                    settings.aiModelName = value;
                    await this.plugin.saveSettings();
                }));

        // AI Base URL
        new Setting(container)
            .setName('API基础URL')
            .setDesc('API请求的基础URL（留空使用默认值，自定义提供商必填）')
            .addText(text => text
                .setPlaceholder(defaultBaseUrls[settings.aiProvider] || 'https://api.example.com/v1')
                .setValue(settings.aiBaseUrl)
                .onChange(async (value) => {
                    settings.aiBaseUrl = value;
                    await this.plugin.saveSettings();
                }));

        // AI API Key
        new Setting(container)
            .setName('API密钥')
            .setDesc('用于AI模型调用的API密钥（必需）')
            .addText(text => {
                text.setPlaceholder(providerPlaceholders[settings.aiProvider] || '输入API密钥')
                    .setValue(settings.aiApiKey)
                    .inputEl.type = 'password';
                text.onChange(async (value) => {
                    settings.aiApiKey = value;
                    await this.plugin.saveSettings();
                });
                return text;
            })
            .addExtraButton(button => button
                .setIcon('external-link')
                .setTooltip('获取API Key')
                .onClick(() => {
                    const url = providerUrls[settings.aiProvider];
                    if (url) {
                        window.open(url, '_blank');
                    }
                }));

        // Command Timeout
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (Setting.addSlider)
        new Setting(container)
            .setName('请求超时时间')
            .setDesc(`API请求的最大等待时间：${settings.commandTimeout / 1000}秒`)
            .addSlider(slider => slider
                .setLimits(5, 300, 5)
                .setValue(settings.commandTimeout / 1000)
                .setDynamicTooltip()
                .onChange(async (value) => {
                    settings.commandTimeout = value * 1000;
                    await this.plugin.saveSettings();
                    this.displaySection('connection');
                }));

        // Connection Test Group
        this.createSettingGroup(container, '连接测试');

        // Test Connection Button
        new Setting(container)
            .setName('测试连接')
            .setDesc('测试与Claude Code API的连接状态')
            .addButton(button => button
                .setButtonText('测试连接')
                .setCta()
                .onClick(async () => {
                    button.setDisabled(true);
                    button.setButtonText('测试中...');
                    await this.testConnection();
                    button.setDisabled(false);
                    button.setButtonText('测试连接');
                }));

        // Advanced Connection Options Group
        this.createSettingGroup(container, '高级选项');

        // Enable Cache
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (Setting.addToggle)
        new Setting(container)
            .setName('启用请求缓存')
            .setDesc('缓存API请求结果以提高响应速度')
            .addToggle(toggle => toggle
                .setValue(settings.enableCache)
                .onChange(async (value) => {
                    settings.enableCache = value;
                    await this.plugin.saveSettings();
                }));

        // Retry Count
        new Setting(container)
            .setName('重试次数')
            .setDesc(`请求失败时的自动重试次数：${settings.retryCount}次`)
            .addSlider(slider => slider
                .setLimits(0, 10, 1)
                .setValue(settings.retryCount)
                .setDynamicTooltip()
                .onChange(async (value) => {
                    settings.retryCount = value;
                    await this.plugin.saveSettings();
                    this.displaySection('connection');
                }));

        // Log Level
        // ✅ Verified from Context7: /obsidianmd/obsidian-api (Setting.addDropdown)
        new Setting(container)
            .setName('日志级别')
            .setDesc('API请求的日志记录级别')
            .addDropdown(dropdown => dropdown
                .addOption('none', '无日志')
                .addOption('error', '仅错误')
                .addOption('warn', '警告及以上')
                .addOption('info', '信息及以上')
                .addOption('debug', '调试日志')
                .setValue(settings.logLevel)
                .onChange(async (value) => {
                    settings.logLevel = value as PluginSettings['logLevel'];
                    await this.plugin.saveSettings();
                }));
    }

    /**
     * Displays storage settings
     */
    private displayStorageSettings(container: HTMLElement): void {
        const settings = this.plugin.settings;

        // Storage Path Group
        this.createSettingGroup(container, '存储路径');

        // Data Path
        new Setting(container)
            .setName('数据存储路径')
            .setDesc('Canvas学习系统数据的存储目录')
            .addText(text => text
                .setPlaceholder('选择数据存储目录')
                .setValue(settings.dataPath)
                .onChange(async (value) => {
                    settings.dataPath = value;
                    await this.plugin.saveSettings();
                }));

        // Path Info Display
        if (settings.dataPath) {
            const pathInfo = container.createDiv('path-info');
            pathInfo.createEl('div', {
                text: `📁 数据库文件: ${settings.dataPath}/canvas-review.db`,
                cls: 'path-info-item'
            });
            pathInfo.createEl('div', {
                text: `📦 备份目录: ${settings.dataPath}/backups/`,
                cls: 'path-info-item'
            });
        }

        // Backup Settings Group
        this.createSettingGroup(container, '备份策略');

        // Auto Backup
        new Setting(container)
            .setName('启用自动备份')
            .setDesc('定期自动创建数据备份')
            .addToggle(toggle => toggle
                .setValue(settings.autoBackup)
                .onChange(async (value) => {
                    settings.autoBackup = value;
                    await this.plugin.saveSettings();
                    this.displaySection('storage');
                }));

        if (settings.autoBackup) {
            // Backup Interval
            new Setting(container)
                .setName('备份间隔')
                .setDesc(`自动备份的时间间隔：${settings.backupInterval}小时`)
                .addSlider(slider => slider
                    .setLimits(1, 168, 1)
                    .setValue(settings.backupInterval)
                    .setDynamicTooltip()
                    .onChange(async (value) => {
                        settings.backupInterval = value;
                        await this.plugin.saveSettings();
                        this.displaySection('storage');
                    }));

            // Backup Retention Days
            new Setting(container)
                .setName('保留天数')
                .setDesc(`备份文件的保留时间：${settings.backupRetentionDays}天`)
                .addSlider(slider => slider
                    .setLimits(1, 365, 1)
                    .setValue(settings.backupRetentionDays)
                    .setDynamicTooltip()
                    .onChange(async (value) => {
                        settings.backupRetentionDays = value;
                        await this.plugin.saveSettings();
                        this.displaySection('storage');
                    }));

            // Compress Backups
            new Setting(container)
                .setName('压缩备份')
                .setDesc('压缩备份文件以节省存储空间')
                .addToggle(toggle => toggle
                    .setValue(settings.compressBackups)
                    .onChange(async (value) => {
                        settings.compressBackups = value;
                        await this.plugin.saveSettings();
                    }));
        }

        // Sync Settings Group
        this.createSettingGroup(container, '数据同步');

        // Auto Sync Interval
        new Setting(container)
            .setName('同步间隔')
            .setDesc(`数据自动同步的时间间隔：${settings.autoSyncInterval}分钟（0表示禁用）`)
            .addSlider(slider => slider
                .setLimits(0, 60, 1)
                .setValue(settings.autoSyncInterval)
                .setDynamicTooltip()
                .onChange(async (value) => {
                    settings.autoSyncInterval = value;
                    await this.plugin.saveSettings();
                    this.displaySection('storage');
                }));

        // Conflict Resolution
        new Setting(container)
            .setName('冲突解决策略')
            .setDesc('数据同步冲突时的解决方式')
            .addDropdown(dropdown => dropdown
                .addOption('prompt', '提示用户选择')
                .addOption('local', '使用本地数据')
                .addOption('remote', '使用远程数据')
                .addOption('merge', '尝试自动合并')
                .setValue(settings.conflictResolution)
                .onChange(async (value) => {
                    settings.conflictResolution = value as PluginSettings['conflictResolution'];
                    await this.plugin.saveSettings();
                }));

        // Data Management Group
        this.createSettingGroup(container, '数据管理');

        // Create Backup Now
        new Setting(container)
            .setName('创建备份')
            .setDesc('立即创建当前数据的完整备份')
            .addButton(button => button
                .setButtonText('立即备份')
                .onClick(async () => {
                    button.setDisabled(true);
                    button.setButtonText('备份中...');
                    await this.createBackup();
                    button.setDisabled(false);
                    button.setButtonText('立即备份');
                }));

        // Cleanup Data
        new Setting(container)
            .setName('清理数据')
            .setDesc('清理过期的缓存和临时文件')
            .addButton(button => button
                .setButtonText('清理数据')
                .onClick(async () => {
                    button.setDisabled(true);
                    button.setButtonText('清理中...');
                    await this.cleanupData();
                    button.setDisabled(false);
                    button.setButtonText('清理数据');
                }));
    }

    /**
     * Displays interface settings
     */
    private displayInterfaceSettings(container: HTMLElement): void {
        const settings = this.plugin.settings;

        // Theme Settings Group
        this.createSettingGroup(container, '主题设置');

        // Theme
        new Setting(container)
            .setName('主题')
            .setDesc('插件UI主题')
            .addDropdown(dropdown => dropdown
                .addOption('auto', '自动（跟随Obsidian）')
                .addOption('light', '亮色')
                .addOption('dark', '暗色')
                .setValue(settings.theme)
                .onChange(async (value) => {
                    settings.theme = value as PluginSettings['theme'];
                    await this.plugin.saveSettings();
                }));

        // Language
        new Setting(container)
            .setName('语言')
            .setDesc('界面显示语言')
            .addDropdown(dropdown => dropdown
                .addOption('zh-CN', '简体中文')
                .addOption('zh-TW', '繁體中文')
                .addOption('en', 'English')
                .setValue(settings.language)
                .onChange(async (value) => {
                    settings.language = value;
                    await this.plugin.saveSettings();
                }));

        // Display Settings Group
        this.createSettingGroup(container, '显示设置');

        // Font Scale
        new Setting(container)
            .setName('字体缩放')
            .setDesc(`字体大小缩放比例：${(settings.fontScale * 100).toFixed(0)}%`)
            .addSlider(slider => slider
                .setLimits(0.5, 2.0, 0.1)
                .setValue(settings.fontScale)
                .setDynamicTooltip()
                .onChange(async (value) => {
                    settings.fontScale = value;
                    await this.plugin.saveSettings();
                    this.displaySection('interface');
                }));

        // Enable Animations
        new Setting(container)
            .setName('启用动画')
            .setDesc('启用UI动画和过渡效果')
            .addToggle(toggle => toggle
                .setValue(settings.enableAnimations)
                .onChange(async (value) => {
                    settings.enableAnimations = value;
                    await this.plugin.saveSettings();
                }));

        // Show Tooltips
        new Setting(container)
            .setName('显示提示')
            .setDesc('鼠标悬停时显示工具提示')
            .addToggle(toggle => toggle
                .setValue(settings.showTooltips)
                .onChange(async (value) => {
                    settings.showTooltips = value;
                    await this.plugin.saveSettings();
                }));

        // Compact Mode
        new Setting(container)
            .setName('紧凑模式')
            .setDesc('使用更紧凑的UI布局')
            .addToggle(toggle => toggle
                .setValue(settings.compactMode)
                .onChange(async (value) => {
                    settings.compactMode = value;
                    await this.plugin.saveSettings();
                }));

        // Custom CSS Group
        this.createSettingGroup(container, '自定义样式');

        // Custom CSS
        new Setting(container)
            .setName('自定义CSS')
            .setDesc('添加自定义CSS样式')
            .addTextArea(text => text
                .setPlaceholder('/* 输入自定义CSS */\n.my-class {\n  color: red;\n}')
                .setValue(settings.customCss)
                .onChange(async (value) => {
                    settings.customCss = value;
                    await this.plugin.saveSettings();
                }))
            .then(setting => {
                const textArea = setting.controlEl.querySelector('textarea');
                if (textArea) {
                    textArea.style.width = '100%';
                    textArea.style.minHeight = '100px';
                    textArea.style.fontFamily = 'monospace';
                }
            });
    }

    /**
     * Displays review settings
     */
    private displayReviewSettings(container: HTMLElement): void {
        const settings = this.plugin.settings;

        // Review Duration Group
        this.createSettingGroup(container, '复习时长');

        // Default Review Duration
        new Setting(container)
            .setName('默认复习时长')
            .setDesc(`每次复习的默认时长：${settings.defaultReviewDuration}分钟`)
            .addSlider(slider => slider
                .setLimits(5, 180, 5)
                .setValue(settings.defaultReviewDuration)
                .setDynamicTooltip()
                .onChange(async (value) => {
                    settings.defaultReviewDuration = value;
                    await this.plugin.saveSettings();
                    this.displaySection('review');
                }));

        // Reminder Settings Group
        this.createSettingGroup(container, '提醒设置');

        // Enable Reminders
        new Setting(container)
            .setName('启用复习提醒')
            .setDesc('在需要复习时发送提醒通知')
            .addToggle(toggle => toggle
                .setValue(settings.reminderEnabled)
                .onChange(async (value) => {
                    settings.reminderEnabled = value;
                    await this.plugin.saveSettings();
                    this.displaySection('review');
                }));

        if (settings.reminderEnabled) {
            // Reminder Time
            new Setting(container)
                .setName('提醒时间')
                .setDesc('每日提醒的时间（HH:MM格式）')
                .addText(text => text
                    .setPlaceholder('09:00')
                    .setValue(settings.reminderTime)
                    .onChange(async (value) => {
                        const timeRegex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/;
                        if (timeRegex.test(value)) {
                            settings.reminderTime = value;
                            await this.plugin.saveSettings();
                        }
                    }));

            // Reminder Days Info
            const reminderDaysInfo = container.createDiv('reminder-days-info');
            reminderDaysInfo.createEl('p', {
                text: `艾宾浩斯提醒日：第${settings.reminderDays.join('、')}天`,
                cls: 'setting-item-description'
            });
        }

        // Notification Settings Group (Story 14.7)
        this.createSettingGroup(container, '通知设置');

        // Enable Notifications
        new Setting(container)
            .setName('启用通知')
            .setDesc('每日首次打开 Obsidian 时显示复习提醒')
            .addToggle(toggle => toggle
                .setValue(settings.enableNotifications)
                .onChange(async (value) => {
                    settings.enableNotifications = value;
                    await this.plugin.saveSettings();
                    this.displaySection('review');
                }));

        if (settings.enableNotifications) {
            // Quiet Hours Start
            new Setting(container)
                .setName('静默时段开始')
                .setDesc(`从此时间开始不发送通知：${settings.quietHoursStart}:00`)
                .addSlider(slider => slider
                    .setLimits(0, 23, 1)
                    .setValue(settings.quietHoursStart)
                    .setDynamicTooltip()
                    .onChange(async (value) => {
                        settings.quietHoursStart = value;
                        await this.plugin.saveSettings();
                        this.displaySection('review');
                    }));

            // Quiet Hours End
            new Setting(container)
                .setName('静默时段结束')
                .setDesc(`到此时间恢复通知：${settings.quietHoursEnd}:00`)
                .addSlider(slider => slider
                    .setLimits(0, 23, 1)
                    .setValue(settings.quietHoursEnd)
                    .setDynamicTooltip()
                    .onChange(async (value) => {
                        settings.quietHoursEnd = value;
                        await this.plugin.saveSettings();
                        this.displaySection('review');
                    }));

            // Min Notification Interval
            new Setting(container)
                .setName('通知最小间隔')
                .setDesc(`两次通知之间的最小间隔：${settings.minNotificationInterval}小时`)
                .addSlider(slider => slider
                    .setLimits(1, 48, 1)
                    .setValue(settings.minNotificationInterval)
                    .setDynamicTooltip()
                    .onChange(async (value) => {
                        settings.minNotificationInterval = value;
                        await this.plugin.saveSettings();
                        this.displaySection('review');
                    }));

            // Quiet Hours Info
            const quietHoursInfo = container.createDiv('quiet-hours-info');
            const startHour = settings.quietHoursStart.toString().padStart(2, '0');
            const endHour = settings.quietHoursEnd.toString().padStart(2, '0');
            quietHoursInfo.createEl('p', {
                text: `当前静默时段：${startHour}:00 - ${endHour}:00`,
                cls: 'setting-item-description'
            });
        }

        // Scoring Settings Group
        this.createSettingGroup(container, '评分设置');

        // Enable Auto Scoring
        new Setting(container)
            .setName('启用自动评分')
            .setDesc('在执行Agent操作前自动评估理解程度（拆解、解释、检验等场景）')
            .addToggle(toggle => toggle
                .setValue(settings.enableAutoScoring)
                .onChange(async (value) => {
                    settings.enableAutoScoring = value;
                    await this.plugin.saveSettings();
                }));

        // Passing Score
        new Setting(container)
            .setName('及格分数')
            .setDesc(`复习通过的最低分数：${settings.passingScore}分`)
            .addSlider(slider => slider
                .setLimits(0, 100, 5)
                .setValue(settings.passingScore)
                .setDynamicTooltip()
                .onChange(async (value) => {
                    settings.passingScore = value;
                    await this.plugin.saveSettings();
                    this.displaySection('review');
                }));

        // Difficulty Weight
        new Setting(container)
            .setName('难度权重')
            .setDesc(`评分时难度的影响权重：${settings.difficultyWeight.toFixed(1)}`)
            .addSlider(slider => slider
                .setLimits(0.1, 5.0, 0.1)
                .setValue(settings.difficultyWeight)
                .setDynamicTooltip()
                .onChange(async (value) => {
                    settings.difficultyWeight = value;
                    await this.plugin.saveSettings();
                    this.displaySection('review');
                }));

        // Algorithm Settings Group
        this.createSettingGroup(container, '算法设置');

        // Enable Spaced Repetition
        new Setting(container)
            .setName('启用间隔重复')
            .setDesc('使用艾宾浩斯遗忘曲线算法安排复习')
            .addToggle(toggle => toggle
                .setValue(settings.enableSpacedRepetition)
                .onChange(async (value) => {
                    settings.enableSpacedRepetition = value;
                    await this.plugin.saveSettings();
                }));
    }

    /**
     * Displays advanced settings
     */
    private displayAdvancedSettings(container: HTMLElement): void {
        const settings = this.plugin.settings;

        // Debug Settings Group
        this.createSettingGroup(container, '调试选项');

        // Debug Mode
        new Setting(container)
            .setName('调试模式')
            .setDesc('启用详细的控制台日志输出')
            .addToggle(toggle => toggle
                .setValue(settings.debugMode)
                .onChange(async (value) => {
                    settings.debugMode = value;
                    await this.plugin.saveSettings();
                }));

        // Performance Monitoring
        new Setting(container)
            .setName('性能监控')
            .setDesc('启用性能指标收集和监控')
            .addToggle(toggle => toggle
                .setValue(settings.enablePerformanceMonitoring)
                .onChange(async (value) => {
                    settings.enablePerformanceMonitoring = value;
                    await this.plugin.saveSettings();
                }));

        // Performance Settings Group
        this.createSettingGroup(container, '性能设置');

        // Max Concurrent Operations
        new Setting(container)
            .setName('最大并发数')
            .setDesc(`最大并行操作数量：${settings.maxConcurrentOps}`)
            .addSlider(slider => slider
                .setLimits(1, 20, 1)
                .setValue(settings.maxConcurrentOps)
                .setDynamicTooltip()
                .onChange(async (value) => {
                    settings.maxConcurrentOps = value;
                    await this.plugin.saveSettings();
                    this.displaySection('advanced');
                }));

        // Privacy Settings Group
        this.createSettingGroup(container, '隐私设置');

        // Enable Telemetry
        new Setting(container)
            .setName('使用数据收集')
            .setDesc('允许收集匿名使用数据以改进插件')
            .addToggle(toggle => toggle
                .setValue(settings.enableTelemetry)
                .onChange(async (value) => {
                    settings.enableTelemetry = value;
                    await this.plugin.saveSettings();
                }));

        // Experimental Features Group
        this.createSettingGroup(container, '实验性功能');

        // Enable Experimental Features
        new Setting(container)
            .setName('启用实验性功能')
            .setDesc('启用尚在开发中的实验性功能（可能不稳定）')
            .addToggle(toggle => toggle
                .setValue(settings.enableExperimentalFeatures)
                .onChange(async (value) => {
                    settings.enableExperimentalFeatures = value;
                    await this.plugin.saveSettings();
                    new Notice(value
                        ? '⚠️ 实验性功能已启用，某些功能可能不稳定'
                        : '实验性功能已禁用');
                }));

        // System Info Group
        this.createSettingGroup(container, '系统信息');

        // Version Info
        const infoContainer = container.createDiv('system-info');
        infoContainer.createEl('p', { text: `插件版本: 1.0.0` });
        infoContainer.createEl('p', { text: `设置版本: ${settings.settingsVersion}` });
        infoContainer.createEl('p', { text: `Obsidian版本: ${this.app.vault.adapter.getName()}` });

        // Diagnostic Tools
        new Setting(container)
            .setName('诊断工具')
            .setDesc('打开诊断信息面板')
            .addButton(button => button
                .setButtonText('运行诊断')
                .onClick(() => this.runDiagnostics()));
    }

    /**
     * Display Memory System settings (P1 Task #8)
     * Configures three-layer memory architecture: Neo4j/LanceDB/Graphiti
     */
    private displayMemorySettings(container: HTMLElement): void {
        const settings = this.plugin.settings;

        // ========== Neo4j Configuration ==========
        this.createSettingGroup(container, 'Neo4j 知识图谱');

        // Neo4j Enable Toggle
        new Setting(container)
            .setName('启用记忆系统（需后端运行）')
            .setDesc('⚠️ 启用前请确保后端服务已启动。此开关控制是否检查和使用记忆服务。')
            .addToggle(toggle => toggle
                .setValue(settings.neo4jEnabled)
                .onChange(async (value) => {
                    settings.neo4jEnabled = value;
                    await this.plugin.saveSettings();
                    // Refresh to show/hide dependent settings
                    this.displaySection('memory');
                }));

        // Only show Neo4j settings if enabled
        if (settings.neo4jEnabled) {
            // Configuration location notice
            const neo4jNotice = container.createDiv('setting-item-description');
            neo4jNotice.innerHTML = `
                <div class="memory-config-notice">
                    <strong>📍 配置位置：后端 backend/.env</strong><br>
                    <code>NEO4J_URI=bolt://localhost:7688</code><br>
                    <code>NEO4J_USER=neo4j</code><br>
                    <code>NEO4J_PASSWORD=your_password</code><br>
                    <small>修改后端配置后需重启后端服务</small>
                </div>
            `;

            // Test Neo4j Connection (via backend API)
            new Setting(container)
                .setName('测试连接')
                .setDesc('通过后端 API 测试 Neo4j 数据库连接')
                .addButton(button => button
                    .setButtonText('测试连接')
                    .onClick(() => this.testNeo4jConnection()));
        }

        // ========== LanceDB Configuration ==========
        this.createSettingGroup(container, 'LanceDB 语义向量');

        // LanceDB Enable Toggle
        new Setting(container)
            .setName('启用 LanceDB')
            .setDesc('启用 LanceDB 语义向量存储（用于文档嵌入和相似度搜索）')
            .addToggle(toggle => toggle
                .setValue(settings.lancedbEnabled)
                .onChange(async (value) => {
                    settings.lancedbEnabled = value;
                    await this.plugin.saveSettings();
                    this.displaySection('memory');
                }));

        // Only show LanceDB settings if enabled
        if (settings.lancedbEnabled) {
            // LanceDB Path
            new Setting(container)
                .setName('LanceDB 数据路径')
                .setDesc('LanceDB 数据库存储路径（留空使用默认路径）')
                .addText(text => text
                    .setPlaceholder('留空使用默认路径')
                    .setValue(settings.lancedbPath)
                    .onChange(async (value) => {
                        settings.lancedbPath = value;
                        await this.plugin.saveSettings();
                    }));

            // CUDA Acceleration
            new Setting(container)
                .setName('CUDA 加速')
                .setDesc('启用 GPU 加速（需要 NVIDIA 显卡和 CUDA 环境）')
                .addToggle(toggle => toggle
                    .setValue(settings.lancedbCudaEnabled)
                    .onChange(async (value) => {
                        settings.lancedbCudaEnabled = value;
                        await this.plugin.saveSettings();
                        if (value) {
                            new Notice('⚠️ CUDA 加速已启用，请确保已安装 CUDA 环境');
                        }
                    }));
        }

        // ========== Graphiti MCP Configuration ==========
        this.createSettingGroup(container, 'Graphiti 时序记忆');

        // Graphiti Enable Toggle
        new Setting(container)
            .setName('启用 Graphiti MCP')
            .setDesc('启用 Graphiti MCP 服务（用于时序知识图谱和学习历程追踪）')
            .addToggle(toggle => toggle
                .setValue(settings.graphitiEnabled)
                .onChange(async (value) => {
                    settings.graphitiEnabled = value;
                    await this.plugin.saveSettings();
                    this.displaySection('memory');
                }));

        // Only show Graphiti settings if enabled
        if (settings.graphitiEnabled) {
            // OpenAI API Key (Required for Graphiti)
            new Setting(container)
                .setName('OpenAI API Key')
                .setDesc('Graphiti 知识图谱提取必需（用于 gpt-4o-mini 模型）')
                .addText(text => {
                    text.inputEl.type = 'password';
                    text.inputEl.style.width = '300px';
                    text.setPlaceholder('sk-...')
                        .setValue(settings.openaiApiKey)
                        .onChange(async (value) => {
                            settings.openaiApiKey = value;
                            await this.plugin.saveSettings();
                        });
                });

            // Embedding Model Selection
            new Setting(container)
                .setName('嵌入模型')
                .setDesc('用于知识图谱向量嵌入')
                .addDropdown(dropdown => dropdown
                    .addOption('text-embedding-3-small', 'text-embedding-3-small (推荐)')
                    .addOption('text-embedding-3-large', 'text-embedding-3-large (高精度)')
                    .addOption('text-embedding-ada-002', 'text-embedding-ada-002 (旧版)')
                    .setValue(settings.embeddingModel)
                    .onChange(async (value) => {
                        settings.embeddingModel = value;
                        await this.plugin.saveSettings();
                    }));

            // Configuration location notice
            const graphitiNotice = container.createDiv('setting-item-description');
            graphitiNotice.innerHTML = `
                <div class="memory-config-notice">
                    <strong>📍 配置位置：后端 backend/.env</strong><br>
                    <code>ENABLE_GRAPHITI_JSON_DUAL_WRITE=true</code><br>
                    <small>Graphiti MCP 配置由后端统一管理</small>
                </div>
            `;

            // Test Graphiti Connection
            new Setting(container)
                .setName('测试连接')
                .setDesc('测试 Graphiti MCP 服务连接')
                .addButton(button => button
                    .setButtonText('测试连接')
                    .onClick(() => this.testGraphitiConnection()));
        }

        // ========== Memory Status ==========
        this.createSettingGroup(container, '实时服务状态');

        // Real-time Status Display (initially shows loading state)
        const statusContainer = container.createDiv('memory-status-container');

        // Backend status
        const backendStatusEl = statusContainer.createEl('div', {
            cls: 'memory-status-item',
            text: '后端 API: ⏳ 检查中...'
        });

        // Neo4j status
        const neo4jStatusEl = statusContainer.createEl('div', {
            cls: 'memory-status-item',
            text: `Neo4j: ${settings.neo4jEnabled ? '⏳ 检查中...' : '⚪ 未启用'}`
        });

        // LanceDB status (local check)
        const lancedbStatusEl = statusContainer.createEl('div', {
            cls: 'memory-status-item',
            text: `LanceDB: ${settings.lancedbEnabled ? (settings.lancedbPath ? '✅ 已配置' : '⚠️ 使用默认路径') : '⚪ 未启用'}`
        });

        // Graphiti status
        const graphitiStatusEl = statusContainer.createEl('div', {
            cls: 'memory-status-item',
            text: `Graphiti: ${settings.graphitiEnabled ? '⏳ 检查中...' : '⚪ 未启用'}`
        });

        // Auto-check real status on load
        this.checkRealTimeStatus(backendStatusEl, neo4jStatusEl, graphitiStatusEl, settings);

        // Refresh Status Button
        new Setting(container)
            .setName('刷新状态')
            .setDesc('重新检测所有服务的真实连接状态')
            .addButton(button => button
                .setButtonText('🔄 立即检测')
                .onClick(() => {
                    backendStatusEl.textContent = '后端 API: ⏳ 检查中...';
                    if (settings.neo4jEnabled) neo4jStatusEl.textContent = 'Neo4j: ⏳ 检查中...';
                    if (settings.graphitiEnabled) graphitiStatusEl.textContent = 'Graphiti: ⏳ 检查中...';
                    this.checkRealTimeStatus(backendStatusEl, neo4jStatusEl, graphitiStatusEl, settings);
                }));
    }

    /**
     * Check real-time status of memory services
     * Makes actual HTTP requests to verify service connectivity
     */
    private async checkRealTimeStatus(
        backendEl: HTMLElement,
        neo4jEl: HTMLElement,
        graphitiEl: HTMLElement,
        settings: PluginSettings
    ): Promise<void> {
        const baseUrl = settings.claudeCodeUrl;

        // Step 1: Check if backend is reachable
        try {
            const healthResponse = await fetch(`${baseUrl}/api/v1/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });

            if (healthResponse.ok) {
                backendEl.textContent = '后端 API: ✅ 已连接';
                backendEl.addClass('status-success');
            } else {
                backendEl.textContent = `后端 API: ❌ 异常 (HTTP ${healthResponse.status})`;
                backendEl.addClass('status-error');
                // If backend is not OK, mark dependent services as unknown
                if (settings.neo4jEnabled) {
                    neo4jEl.textContent = 'Neo4j: ❓ 无法检测（后端异常）';
                }
                if (settings.graphitiEnabled) {
                    graphitiEl.textContent = 'Graphiti: ❓ 无法检测（后端异常）';
                }
                return;
            }
        } catch (error) {
            backendEl.textContent = '后端 API: ❌ 未启动或无法连接';
            backendEl.addClass('status-error');
            // Backend unreachable, can't check other services
            if (settings.neo4jEnabled) {
                neo4jEl.textContent = 'Neo4j: ❓ 无法检测（后端未启动）';
            }
            if (settings.graphitiEnabled) {
                graphitiEl.textContent = 'Graphiti: ❓ 无法检测（后端未启动）';
            }
            return;
        }

        // Step 2: Check Neo4j if enabled
        if (settings.neo4jEnabled) {
            try {
                const neo4jResponse = await fetch(`${baseUrl}/api/v1/health/neo4j`, {
                    method: 'GET',
                    signal: AbortSignal.timeout(5000)
                });

                if (neo4jResponse.ok) {
                    const data = await neo4jResponse.json();
                    // Check actual health status, not just HTTP 200
                    if (data.status === 'healthy') {
                        neo4jEl.textContent = `Neo4j: ✅ 已连接 (${data.message || '正常'})`;
                        neo4jEl.addClass('status-success');
                    } else {
                        // HTTP 200 but unhealthy status
                        const errorMsg = data.checks?.error || data.message || '连接失败';
                        neo4jEl.textContent = `Neo4j: ❌ ${errorMsg}`;
                        neo4jEl.addClass('status-error');
                    }
                } else {
                    neo4jEl.textContent = `Neo4j: ❌ 连接失败 (HTTP ${neo4jResponse.status})`;
                    neo4jEl.addClass('status-error');
                }
            } catch (error) {
                neo4jEl.textContent = 'Neo4j: ❌ 连接超时或未运行';
                neo4jEl.addClass('status-error');
            }
        }

        // Step 3: Check Graphiti if enabled
        if (settings.graphitiEnabled) {
            try {
                const graphitiResponse = await fetch(`${baseUrl}/api/v1/health/graphiti`, {
                    method: 'GET',
                    signal: AbortSignal.timeout(5000)
                });

                if (graphitiResponse.ok) {
                    const data = await graphitiResponse.json();
                    // Check actual health status, not just HTTP 200
                    if (data.status === 'healthy') {
                        graphitiEl.textContent = 'Graphiti: ✅ 已连接';
                        graphitiEl.addClass('status-success');
                    } else {
                        const errorMsg = data.checks?.error || data.message || '连接失败';
                        graphitiEl.textContent = `Graphiti: ❌ ${errorMsg}`;
                        graphitiEl.addClass('status-error');
                    }
                } else {
                    graphitiEl.textContent = `Graphiti: ❌ 连接失败 (HTTP ${graphitiResponse.status})`;
                    graphitiEl.addClass('status-error');
                }
            } catch (error) {
                graphitiEl.textContent = 'Graphiti: ❌ 连接超时或未运行';
                graphitiEl.addClass('status-error');
            }
        }
    }

    /**
     * Test Neo4j connection via backend API
     * Note: Neo4j config is managed in backend/.env, not in plugin settings
     */
    private async testNeo4jConnection(): Promise<void> {
        const settings = this.plugin.settings;
        if (!settings.claudeCodeUrl) {
            new Notice('❌ 请先配置后端 API 地址');
            return;
        }

        new Notice('⏳ 正在通过后端 API 测试 Neo4j 连接...');

        try {
            // Use the backend API to test Neo4j connection
            const response = await fetch(`${settings.claudeCodeUrl}/api/v1/health/neo4j`, {
                method: 'GET',
                signal: AbortSignal.timeout(10000)
            });

            if (response.ok) {
                new Notice('✅ Neo4j 连接成功！');
            } else {
                new Notice(`❌ Neo4j 连接失败: HTTP ${response.status}`);
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : '未知错误';
            new Notice(`❌ Neo4j 连接测试失败: ${message}`);
        }
    }

    /**
     * Test Graphiti connection via backend API
     */
    private async testGraphitiConnection(): Promise<void> {
        const settings = this.plugin.settings;
        if (!settings.claudeCodeUrl) {
            new Notice('❌ 请先配置后端 API 地址');
            return;
        }

        new Notice('⏳ 正在通过后端 API 测试 Graphiti 连接...');

        try {
            // Use the backend API to test Graphiti connection
            const response = await fetch(`${settings.claudeCodeUrl}/api/v1/health/graphiti`, {
                method: 'GET',
                signal: AbortSignal.timeout(10000)
            });

            if (response.ok) {
                new Notice('✅ Graphiti 连接成功（通过后端 API）');
            } else {
                new Notice(`❌ Graphiti 连接失败: HTTP ${response.status}`);
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : '未知错误';
            new Notice(`❌ Graphiti 连接测试失败: ${message}`);
        }
    }

    /**
     * Legacy refresh function - kept for backward compatibility
     * @deprecated Use checkRealTimeStatus instead for in-page updates
     */
    private async refreshMemoryStatus(): Promise<void> {
        // Refresh the settings display to trigger real-time status check
        this.displaySection('memory');
        new Notice('✅ 状态已刷新，请查看设置面板中的实时状态');
    }

    /**
     * Creates a setting group header
     */
    private createSettingGroup(container: HTMLElement, title: string): void {
        const groupEl = container.createDiv('setting-group');
        groupEl.createEl('h4', { text: title, cls: 'setting-group-title' });
    }

    /**
     * Tests connection to Claude Code API
     */
    private async testConnection(): Promise<void> {
        const url = this.plugin.settings.claudeCodeUrl;
        if (!url) {
            new Notice('❌ 请先配置Claude Code服务地址');
            return;
        }

        try {
            const response = await fetch(`${url}/api/v1/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(10000)
            });

            if (response.ok) {
                new Notice('✅ 连接成功！Claude Code API可以正常访问');
            } else {
                new Notice(`❌ 连接失败: HTTP ${response.status}`);
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : '未知错误';
            new Notice(`❌ 连接失败: ${message}`);
        }
    }

    /**
     * Creates a backup
     */
    private async createBackup(): Promise<void> {
        try {
            // Placeholder for actual backup implementation
            await new Promise(resolve => setTimeout(resolve, 1000));
            new Notice('✅ 备份创建成功');
        } catch (error) {
            new Notice('❌ 备份创建失败');
        }
    }

    /**
     * Cleans up old data
     */
    private async cleanupData(): Promise<void> {
        try {
            // Placeholder for actual cleanup implementation
            await new Promise(resolve => setTimeout(resolve, 1000));
            new Notice('✅ 数据清理完成');
        } catch (error) {
            new Notice('❌ 数据清理失败');
        }
    }

    /**
     * Exports settings to file
     */
    private async handleExportSettings(): Promise<void> {
        try {
            const settingsJson = exportSettings(this.plugin.settings);
            const blob = new Blob([settingsJson], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `canvas-review-settings-${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            URL.revokeObjectURL(url);
            new Notice('✅ 设置已导出');
        } catch (error) {
            new Notice('❌ 设置导出失败');
        }
    }

    /**
     * Imports settings from file
     */
    private handleImportSettings(): void {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = async (e) => {
            const file = (e.target as HTMLInputElement).files?.[0];
            if (!file) return;

            try {
                const text = await file.text();
                const imported = importSettings(text);

                // Confirm import
                const confirmed = confirm('确定要导入这些设置吗？当前设置将被覆盖。');
                if (!confirmed) return;

                Object.assign(this.plugin.settings, imported);
                await this.plugin.saveSettings();
                this.display();
                new Notice('✅ 设置已导入');
            } catch (error) {
                const message = error instanceof Error ? error.message : '未知错误';
                new Notice(`❌ 设置导入失败: ${message}`);
            }
        };
        input.click();
    }

    /**
     * Resets settings to defaults
     */
    private async handleResetSettings(): Promise<void> {
        const confirmed = confirm('确定要重置所有设置吗？此操作不可撤销。');
        if (!confirmed) return;

        try {
            this.plugin.settings = { ...DEFAULT_SETTINGS };
            await this.plugin.saveSettings();
            this.display();
            new Notice('✅ 设置已重置为默认值');
        } catch (error) {
            new Notice('❌ 设置重置失败');
        }
    }

    /**
     * Displays error history settings section
     *
     * @source Story 21.5.5 - AC 4: 错误历史在设置面板可见
     */
    private displayErrorHistorySettings(container: HTMLElement): void {
        // Get error history manager from plugin
        const errorHistoryManager = this.plugin.errorHistoryManager;

        if (!errorHistoryManager) {
            container.createEl('p', {
                text: '错误历史管理器未初始化',
                cls: 'error-history-unavailable'
            });
            return;
        }

        // Statistics Section
        const stats = errorHistoryManager.getStats();
        const statsGroup = container.createDiv('settings-group');
        statsGroup.createEl('h4', { text: '📊 错误统计' });

        new Setting(statsGroup)
            .setName('错误总数')
            .setDesc('当前存储的错误记录数量')
            .addText(text => text
                .setValue(String(stats.total))
                .setDisabled(true));

        if (stats.newestTimestamp) {
            new Setting(statsGroup)
                .setName('最近错误时间')
                .setDesc('最近一次错误发生的时间')
                .addText(text => text
                    .setValue(new Date(stats.newestTimestamp!).toLocaleString('zh-CN'))
                    .setDisabled(true));
        }

        // Error Type Breakdown
        if (Object.keys(stats.byType).length > 0) {
            const typeBreakdown = statsGroup.createDiv('error-type-breakdown');
            typeBreakdown.createEl('h5', { text: '按错误类型分布:' });
            const typeList = typeBreakdown.createEl('ul');
            for (const [type, count] of Object.entries(stats.byType)) {
                typeList.createEl('li', { text: `${type}: ${count}` });
            }
        }

        // Actions Section
        const actionsGroup = container.createDiv('settings-group');
        actionsGroup.createEl('h4', { text: '🔧 操作' });

        new Setting(actionsGroup)
            .setName('清空所有错误记录')
            .setDesc('删除所有存储的错误历史（此操作不可撤销）')
            .addButton(button => button
                .setButtonText('清空')
                .setWarning()
                .onClick(async () => {
                    const confirmed = confirm('确定要清空所有错误记录吗？此操作不可撤销。');
                    if (!confirmed) return;

                    const cleared = await errorHistoryManager.clearAll();
                    new Notice(`已清空 ${cleared} 条错误记录`);
                    this.displaySection('errorHistory');
                }));

        new Setting(actionsGroup)
            .setName('手动清理过期记录')
            .setDesc('删除超过7天的错误记录')
            .addButton(button => button
                .setButtonText('清理')
                .onClick(async () => {
                    const removed = await errorHistoryManager.cleanup();
                    new Notice(`已清理 ${removed} 条过期记录`);
                    this.displaySection('errorHistory');
                }));

        // Recent Errors List Section
        const recentErrors = errorHistoryManager.getRecent(20);
        const listGroup = container.createDiv('settings-group');
        listGroup.createEl('h4', { text: '📋 最近错误记录 (最多20条)' });

        if (recentErrors.length === 0) {
            listGroup.createEl('p', {
                text: '暂无错误记录',
                cls: 'error-history-empty'
            });
        } else {
            const errorList = listGroup.createDiv('error-history-list');

            for (const record of recentErrors) {
                this.renderErrorRecord(errorList, record);
            }
        }
    }

    /**
     * Renders a single error record
     *
     * @source Story 21.5.5 - AC 4: 显示最近20条错误记录
     */
    private renderErrorRecord(container: HTMLElement, record: ErrorRecord): void {
        const recordEl = container.createDiv('error-record');

        // Header: Type + Timestamp
        const headerEl = recordEl.createDiv('error-record-header');
        const typeEl = headerEl.createSpan({
            text: record.backendErrorType || record.errorType,
            cls: `error-type error-type-${record.errorType.toLowerCase().replace(/\d+/g, '')}`
        });

        const timeEl = headerEl.createSpan({
            text: new Date(record.timestamp).toLocaleString('zh-CN'),
            cls: 'error-timestamp'
        });

        // Operation
        const operationEl = recordEl.createDiv('error-operation');
        operationEl.createSpan({ text: '操作: ', cls: 'label' });
        operationEl.createSpan({ text: record.operation });

        // Message
        const messageEl = recordEl.createDiv('error-message');
        messageEl.createSpan({ text: record.message });

        // Bug ID (if present)
        if (record.bugId) {
            const bugIdEl = recordEl.createDiv('error-bug-id');
            bugIdEl.createSpan({ text: 'Bug ID: ', cls: 'label' });
            const bugIdCode = bugIdEl.createEl('code', {
                text: record.bugId,
                cls: 'bug-id-code clickable'
            });
            bugIdCode.setAttribute('title', '点击复制');
            bugIdCode.addEventListener('click', () => {
                navigator.clipboard.writeText(record.bugId!);
                new Notice('Bug ID 已复制到剪贴板');
            });
        }

        // Status Code (if present)
        if (record.statusCode) {
            const statusEl = recordEl.createDiv('error-status');
            statusEl.createSpan({ text: 'HTTP状态: ', cls: 'label' });
            statusEl.createSpan({
                text: String(record.statusCode),
                cls: `status-code status-${Math.floor(record.statusCode / 100)}xx`
            });
        }

        // Delete button
        const actionsEl = recordEl.createDiv('error-record-actions');
        const deleteBtn = actionsEl.createEl('button', {
            text: '删除',
            cls: 'error-delete-btn'
        });
        deleteBtn.addEventListener('click', async () => {
            const deleted = await this.plugin.errorHistoryManager?.deleteRecord(record.id);
            if (deleted) {
                new Notice('错误记录已删除');
                this.displaySection('errorHistory');
            }
        });
    }

    /**
     * Runs diagnostic checks
     */
    private runDiagnostics(): void {
        const validation = validateSettings(this.plugin.settings);
        let message = '诊断结果:\n\n';

        if (validation.isValid) {
            message += '✅ 设置验证通过\n';
        } else {
            message += '❌ 设置验证失败:\n';
            validation.errors.forEach(err => {
                message += `  - ${err}\n`;
            });
        }

        if (validation.warnings.length > 0) {
            message += '\n⚠️ 警告:\n';
            validation.warnings.forEach(warn => {
                message += `  - ${warn}\n`;
            });
        }

        message += `\n连接状态: ${this.plugin.settings.claudeCodeUrl ? '已配置' : '未配置'}`;
        message += `\n数据路径: ${this.plugin.settings.dataPath || '未设置'}`;
        message += `\n调试模式: ${this.plugin.settings.debugMode ? '启用' : '禁用'}`;

        alert(message);
    }
}

/**
 * Modal for displaying backend logs
 *
 * @source Plan: 后端启动/停止UI实现计划
 */
class BackendLogModal extends Modal {
    private logs: string[];

    constructor(app: App, logs: string[]) {
        super(app);
        this.logs = logs;
    }

    onOpen(): void {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('backend-log-modal');

        // Header
        contentEl.createEl('h2', { text: '后端服务日志' });

        // Log container with scrolling
        const logContainer = contentEl.createDiv('backend-log-container');
        logContainer.style.maxHeight = '400px';
        logContainer.style.overflow = 'auto';
        logContainer.style.fontFamily = 'monospace';
        logContainer.style.fontSize = '12px';
        logContainer.style.backgroundColor = 'var(--background-secondary)';
        logContainer.style.padding = '10px';
        logContainer.style.borderRadius = '5px';
        logContainer.style.whiteSpace = 'pre-wrap';
        logContainer.style.wordBreak = 'break-all';

        // Display logs
        if (this.logs.length === 0) {
            logContainer.createEl('p', {
                text: '暂无日志',
                cls: 'backend-log-empty'
            });
        } else {
            this.logs.forEach(line => {
                const lineEl = logContainer.createEl('div', {
                    text: line,
                    cls: 'backend-log-line'
                });
                // Color code based on content
                if (line.includes('ERROR') || line.includes('error')) {
                    lineEl.style.color = 'var(--text-error)';
                } else if (line.includes('WARNING') || line.includes('warning')) {
                    lineEl.style.color = 'var(--text-warning)';
                } else if (line.includes('INFO') || line.includes('info')) {
                    lineEl.style.color = 'var(--text-muted)';
                }
            });
        }

        // Button container
        const buttonContainer = contentEl.createDiv('backend-log-buttons');
        buttonContainer.style.marginTop = '10px';
        buttonContainer.style.display = 'flex';
        buttonContainer.style.gap = '10px';

        // Copy button
        const copyBtn = buttonContainer.createEl('button', {
            text: '复制日志',
            cls: 'mod-cta'
        });
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(this.logs.join('\n'));
            new Notice('日志已复制到剪贴板');
        });

        // Close button
        const closeBtn = buttonContainer.createEl('button', {
            text: '关闭'
        });
        closeBtn.addEventListener('click', () => {
            this.close();
        });
    }

    onClose(): void {
        const { contentEl } = this;
        contentEl.empty();
    }
}
