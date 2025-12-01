# Story 13.6: 设置面板

## Status
Pending

## Story

**As a** Canvas学习系统用户,
**I want** 通过设置面板配置插件的各项参数和偏好,
**so that** 我可以根据个人需求自定义插件的行为和外观。

## Acceptance Criteria

1. 实现PluginSettingsTab主设置面板，提供完整的配置选项
2. 创建Claude Code连接配置（API地址、超时设置、认证信息）
3. 实现数据存储配置（数据库路径、备份策略、同步设置）
4. 提供界面和主题配置（主题选择、字体大小、显示选项）
5. 添加复习偏好设置（默认时长、提醒设置、评分标准）
6. 实现设置的保存、加载、重置和导入导出功能

## Tasks / Subtasks

- [ ] Task 1: 创建PluginSettingsTab主框架 (AC: 1)
  - [ ] 设计设置面板的整体布局（侧边导航、内容区域、底部操作）
  - [ ] 实现React组件框架和TypeScript接口定义
  - [ ] 创建设置分类导航（连接、存储、界面、复习、高级）
  - [ ] 实现设置表单的基础组件和验证机制
  - [ ] 添加设置的加载状态和错误处理

- [ ] Task 2: 实现Claude Code连接配置 (AC: 2)
  - [ ] 创建ConnectionSettings组件，配置API连接参数
  - [ ] 实现API地址配置（URL格式验证、连接测试）
  - [ ] 添加超时设置和重试机制配置
  - [ ] 实现认证信息配置（API密钥、令牌管理）
  - [ ] 添加连接状态指示和诊断工具

- [ ] Task 3: 实现数据存储配置 (AC: 3)
  - [ ] 创建StorageSettings组件，配置数据存储参数
  - [ ] 实现数据库路径选择和验证
  - [ ] 添加备份策略配置（自动备份、保留策略、存储位置）
  - [ ] 实现数据同步设置（同步间隔、冲突解决）
  - [ ] 创建数据管理工具（清理、修复、导出）

- [ ] Task 4: 实现界面和主题配置 (AC: 4)
  - [ ] 创建InterfaceSettings组件，配置界面参数
  - [ ] 实现主题选择（亮色、暗色、自动）
  - [ ] 添加字体大小和显示设置
  - [ ] 实现仪表板布局和显示选项配置
  - [ ] 添加动画和交互效果开关

- [ ] Task 5: 实现复习偏好设置 (AC: 5)
  - [ ] 创建ReviewSettings组件，配置复习参数
  - [ ] 实现默认复习时长和难度设置
  - [ ] 添加提醒配置（提醒时间、提醒方式）
  - [ ] 实现评分标准和权重配置
  - [ ] 创建复习计划和策略选项

- [ ] Task 6: 实现设置管理功能 (AC: 6)
  - [ ] 实现设置的实时保存和加载
  - [ ] 添加设置重置功能（重置为默认值）
  - [ ] 实现设置的导入导出（JSON格式）
  - [ ] 创建设置备份和恢复功能
  - [ ] 添加设置版本管理和迁移机制

- [ ] Task 7: 实现高级设置和工具 (AC: 1)
  - [ ] 创建AdvancedSettings组件，提供高级选项
  - [ ] 实现调试模式开关和日志配置
  - [ ] 添加性能监控和统计开关
  - [ ] 实验性功能和开发者选项
  - [ ] 创建系统信息显示和诊断工具

- [ ] Task 8: 组件集成和测试 (ALL AC)
  - [ ] 在主插件中注册设置标签页
  - [ ] 测试所有设置项的保存和加载功能
  - [ ] 验证设置验证和错误处理的正确性
  - [ ] 测试设置界面在不同主题下的显示效果
  - [ ] 进行用户体验测试，优化交互流程

## Dev Notes

### 架构上下文

**设置面板架构** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#UI组件层]

本Story实现插件的设置面板，为用户提供完整的配置管理界面：

```mermaid
graph TB
    subgraph "设置面板组件"
        SETTINGS[PluginSettingsTab] ⭐ 本Story实现
        NAV[SettingsNavigation]
        CONNECTION[ConnectionSettings]
        STORAGE[StorageSettings]
        INTERFACE[InterfaceSettings]
        REVIEW[ReviewSettings]
        ADVANCED[AdvancedSettings]
    end

    subgraph "基础组件"
        FORM[SettingsForm]
        INPUT[SettingInput]
        TOGGLE[SettingToggle]
        SELECT[SettingSelect]
        BUTTON[ActionButton]
    end

    subgraph "Obsidian API"
        SETTING_TAB[PluginSettingTab]
        NOTICE[Notice]
        MODAL[Modal]
    end

    SETTINGS --> NAV
    SETTINGS --> CONNECTION
    SETTINGS --> STORAGE
    SETTINGS --> INTERFACE
    SETTINGS --> REVIEW
    SETTINGS --> ADVANCED
    SETTINGS --> FORM
    FORM --> INPUT
    FORM --> TOGGLE
    FORM --> SELECT
    FORM --> BUTTON
    SETTINGS --> SETTING_TAB
    SETTINGS --> NOTICE
    SETTINGS --> MODAL
```

**设计原则** [Source: canvas-progress-tracker/docs/obsidian-plugin-prd.md#FR-009]
- **直观性**: 设置选项分类清晰，易于理解和操作
- **即时性**: 设置更改立即生效，提供实时反馈
- **安全性**: 重要设置提供确认机制，防止误操作
- **可恢复性**: 支持设置备份和恢复，防止配置丢失

### PluginSettingsTab主组件实现

**主设置面板** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#插件核心类]
```typescript
import React, { useState, useEffect } from 'react';
import { PluginSettingTab } from 'obsidian';
import CanvasReviewPlugin from '../main';

export class CanvasReviewSettingsTab extends PluginSettingTab {
    plugin: CanvasReviewPlugin;
    settingsComponent: React.ReactElement | null = null;

    constructor(app: App, plugin: CanvasReviewPlugin) {
        super(app, plugin);
        this.plugin = plugin;
    }

    display(): void {
        const { containerEl } = this;
        containerEl.empty();

        // 创建React设置组件的容器
        const reactContainer = containerEl.createDiv('react-settings-container');

        // 渲染React设置组件
        this.settingsComponent = React.createElement(
            SettingsPanel,
            {
                plugin: this.plugin,
                onSettingsChange: this.handleSettingsChange.bind(this),
                onResetSettings: this.handleResetSettings.bind(this),
                onExportSettings: this.handleExportSettings.bind(this),
                onImportSettings: this.handleImportSettings.bind(this)
            }
        );

        // 使用ReactDOM渲染设置组件
        import('react-dom').then(({ render }) => {
            render(this.settingsComponent, reactContainer);
        });
    }

    hide(): void {
        // 清理React组件
        if (this.settingsComponent) {
            import('react-dom').then(({ unmountComponentAtNode }) => {
                const container = this.containerEl.querySelector('.react-settings-container');
                if (container) {
                    unmountComponentAtNode(container);
                }
            });
        }
    }

    private async handleSettingsChange(newSettings: Partial<PluginSettings>): Promise<void> {
        try {
            // 更新插件设置
            Object.assign(this.plugin.settings, newSettings);

            // 保存设置
            await this.plugin.saveSettings();

            // 显示成功提示
            new Notice('✅ 设置已保存');

            // 通知相关组件重新加载
            this.notifySettingsChanged(newSettings);
        } catch (error) {
            new Notice('❌ 设置保存失败: ' + error.message);
        }
    }

    private async handleResetSettings(): Promise<void> {
        const confirmed = await this.showConfirmDialog(
            '重置设置',
            '确定要重置所有设置吗？此操作不可撤销。'
        );

        if (confirmed) {
            try {
                // 重置为默认设置
                this.plugin.settings = this.getDefaultSettings();
                await this.plugin.saveSettings();

                // 重新显示设置面板
                this.display();

                new Notice('✅ 设置已重置为默认值');
            } catch (error) {
                new Notice('❌ 设置重置失败: ' + error.message);
            }
        }
    }

    private async handleExportSettings(): Promise<void> {
        try {
            const settingsData = JSON.stringify(this.plugin.settings, null, 2);
            const blob = new Blob([settingsData], { type: 'application/json' });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `canvas-review-settings-${new Date().toISOString().split('T')[0]}.json`;
            a.click();

            URL.revokeObjectURL(url);
            new Notice('✅ 设置已导出');
        } catch (error) {
            new Notice('❌ 设置导出失败: ' + error.message);
        }
    }

    private async handleImportSettings(file: File): Promise<void> {
        try {
            const text = await file.text();
            const importedSettings = JSON.parse(text);

            // 验证导入的设置
            const validatedSettings = this.validateSettings(importedSettings);

            // 确认导入
            const confirmed = await this.showConfirmDialog(
                '导入设置',
                '确定要导入这些设置吗？当前设置将被覆盖。'
            );

            if (confirmed) {
                Object.assign(this.plugin.settings, validatedSettings);
                await this.plugin.saveSettings();
                this.display();

                new Notice('✅ 设置已导入');
            }
        } catch (error) {
            new Notice('❌ 设置导入失败: ' + error.message);
        }
    }

    private getDefaultSettings(): PluginSettings {
        return {
            claudeCodeUrl: 'http://localhost:3005',
            dataPath: 'C:/Users/ROG/托福',
            autoSyncInterval: 300000, // 5分钟
            enableCache: true,
            commandTimeout: 30000, // 30秒
            theme: 'auto',
            language: 'zh-CN',
            defaultReviewDuration: 30,
            reminderEnabled: true,
            reminderTime: '09:00',
            autoBackup: true,
            backupRetentionDays: 30,
            debugMode: false,
            enableTelemetry: false
        };
    }

    private validateSettings(settings: any): Partial<PluginSettings> {
        // 实现设置验证逻辑
        return settings;
    }

    private notifySettingsChanged(changes: Partial<PluginSettings>): void {
        // 通知插件组件设置已更改
        this.plugin.settingsChanged.emit(changes);
    }

    private async showConfirmDialog(title: string, message: string): Promise<boolean> {
        return new Promise((resolve) => {
            const modal = new ConfirmModal(this.app, title, message, resolve);
            modal.open();
        });
    }
}
```

### SettingsPanel React组件实现

**React设置面板** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#React组件集成]
```typescript
import React, { useState, useCallback } from 'react';
import { PluginSettings } from '../types/SettingsTypes';

interface SettingsPanelProps {
    plugin: CanvasReviewPlugin;
    onSettingsChange: (settings: Partial<PluginSettings>) => Promise<void>;
    onResetSettings: () => Promise<void>;
    onExportSettings: () => Promise<void>;
    onImportSettings: (file: File) => Promise<void>;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
    plugin,
    onSettingsChange,
    onResetSettings,
    onExportSettings,
    onImportSettings
}) => {
    const [activeSection, setActiveSection] = useState('connection');
    const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
    const [importFile, setImportFile] = useState<File | null>(null);

    const settings = plugin.settings;

    const handleSectionChange = useCallback((section: string) => {
        if (hasUnsavedChanges) {
            // 提示用户保存更改
            const confirmLeave = confirm('您有未保存的更改，确定要离开吗？');
            if (!confirmLeave) return;
        }
        setActiveSection(section);
        setHasUnsavedChanges(false);
    }, [hasUnsavedChanges]);

    const handleSettingsChange = useCallback(async (changes: Partial<PluginSettings>) => {
        try {
            await onSettingsChange(changes);
            setHasUnsavedChanges(false);
        } catch (error) {
            console.error('设置更新失败:', error);
        }
    }, [onSettingsChange]);

    const handleImport = useCallback(async () => {
        if (!importFile) return;

        try {
            await onImportSettings(importFile);
            setImportFile(null);
            setHasUnsavedChanges(false);
        } catch (error) {
            console.error('设置导入失败:', error);
        }
    }, [importFile, onImportSettings]);

    const sections = [
        { id: 'connection', label: '连接设置', icon: 'wifi' },
        { id: 'storage', label: '数据存储', icon: 'database' },
        { id: 'interface', label: '界面设置', icon: 'palette' },
        { id: 'review', label: '复习偏好', icon: 'book-open' },
        { id: 'advanced', label: '高级设置', icon: 'settings' }
    ];

    return (
        <div className="settings-panel">
            {/* 设置头部 */}
            <div className="settings-header">
                <div className="header-content">
                    <h1>Canvas复习系统设置</h1>
                    <p className="settings-description">
                        配置插件参数、复习偏好和界面选项
                    </p>
                </div>

                {/* 头部操作按钮 */}
                <div className="header-actions">
                    <button
                        className="action-button secondary"
                        onClick={onExportSettings}
                        title="导出设置"
                    >
                        <Icon name="download" size="small" />
                        导出
                    </button>

                    <label className="action-button secondary" title="导入设置">
                        <Icon name="upload" size="small" />
                        导入
                        <input
                            type="file"
                            accept=".json"
                            style={{ display: 'none' }}
                            onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                        />
                    </label>

                    <button
                        className="action-button danger"
                        onClick={onResetSettings}
                        title="重置所有设置"
                    >
                        <Icon name="refresh-cw" size="small" />
                        重置
                    </button>
                </div>
            </div>

            {/* 设置主体 */}
            <div className="settings-body">
                {/* 侧边导航 */}
                <div className="settings-navigation">
                    <nav className="nav-menu">
                        {sections.map((section) => (
                            <button
                                key={section.id}
                                className={`
                                    nav-item
                                    ${activeSection === section.id ? 'active' : ''}
                                `}
                                onClick={() => handleSectionChange(section.id)}
                            >
                                <Icon name={section.icon} size="small" />
                                <span>{section.label}</span>
                            </button>
                        ))}
                    </nav>
                </div>

                {/* 设置内容区域 */}
                <div className="settings-content">
                    <div className="content-scroll">
                        {activeSection === 'connection' && (
                            <ConnectionSettings
                                settings={settings}
                                onSettingsChange={handleSettingsChange}
                                onChanged={() => setHasUnsavedChanges(true)}
                            />
                        )}

                        {activeSection === 'storage' && (
                            <StorageSettings
                                settings={settings}
                                onSettingsChange={handleSettingsChange}
                                onChanged={() => setHasUnsavedChanges(true)}
                            />
                        )}

                        {activeSection === 'interface' && (
                            <InterfaceSettings
                                settings={settings}
                                onSettingsChange={handleSettingsChange}
                                onChanged={() => setHasUnsavedChanges(true)}
                            />
                        )}

                        {activeSection === 'review' && (
                            <ReviewSettings
                                settings={settings}
                                onSettingsChange={handleSettingsChange}
                                onChanged={() => setHasUnsavedChanges(true)}
                            />
                        )}

                        {activeSection === 'advanced' && (
                            <AdvancedSettings
                                settings={settings}
                                onSettingsChange={handleSettingsChange}
                                onChanged={() => setHasUnsavedChanges(true)}
                            />
                        )}
                    </div>
                </div>
            </div>

            {/* 设置底部 */}
            {hasUnsavedChanges && (
                <div className="settings-footer">
                    <div className="footer-content">
                        <span className="unsaved-indicator">
                            <Icon name="alert-circle" size="small" />
                            您有未保存的更改
                        </span>
                        <div className="footer-actions">
                            <button
                                className="action-button primary"
                                onClick={() => handleSettingsChange({})}
                            >
                                保存更改
                            </button>
                            <button
                                className="action-button ghost"
                                onClick={() => setHasUnsavedChanges(false)}
                            >
                                放弃更改
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* 导入文件提示 */}
            {importFile && (
                <div className="import-prompt">
                    <div className="prompt-content">
                        <p>将导入设置文件: <strong>{importFile.name}</strong></p>
                        <div className="prompt-actions">
                            <button
                                className="action-button primary"
                                onClick={handleImport}
                            >
                                确认导入
                            </button>
                            <button
                                className="action-button ghost"
                                onClick={() => setImportFile(null)}
                            >
                                取消
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
```

### ConnectionSettings组件实现

**连接设置组件** [Source: canvas-progress-tracker/docs/obsidian-plugin-prd.md#FR-009]
```typescript
import React, { useState, useCallback } from 'react';

interface ConnectionSettingsProps {
    settings: PluginSettings;
    onSettingsChange: (changes: Partial<PluginSettings>) => void;
    onChanged: () => void;
}

export const ConnectionSettings: React.FC<ConnectionSettingsProps> = ({
    settings,
    onSettingsChange,
    onChanged
}) => {
    const [testingConnection, setTestingConnection] = useState(false);
    const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
    const [connectionMessage, setConnectionMessage] = useState('');

    const handleUrlChange = useCallback((url: string) => {
        onSettingsChange({ claudeCodeUrl: url });
        onChanged();
    }, [onSettingsChange, onChanged]);

    const handleTimeoutChange = useCallback((timeout: number) => {
        onSettingsChange({ commandTimeout: timeout });
        onChanged();
    }, [onSettingsChange, onChanged]);

    const handleApiKeyChange = useCallback((apiKey: string) => {
        onSettingsChange({ apiKey });
        onChanged();
    }, [onSettingsChange, onChanged]);

    const testConnection = useCallback(async () => {
        setTestingConnection(true);
        setConnectionStatus('testing');
        setConnectionMessage('正在测试连接...');

        try {
            // 测试Claude Code API连接
            const response = await fetch(`${settings.claudeCodeUrl}/health`, {
                method: 'GET',
                timeout: 10000
            });

            if (response.ok) {
                setConnectionStatus('success');
                setConnectionMessage('✅ 连接成功！Claude Code API可以正常访问。');
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            setConnectionStatus('error');
            setConnectionMessage(`❌ 连接失败: ${error.message}`);
        } finally {
            setTestingConnection(false);
        }
    }, [settings.claudeCodeUrl]);

    return (
        <div className="settings-section">
            <div className="section-header">
                <h2>Claude Code连接设置</h2>
                <p className="section-description">
                    配置与Claude Code API的连接参数
                </p>
            </div>

            <div className="settings-form">
                {/* API地址设置 */}
                <SettingGroup title="API配置">
                    <SettingInput
                        label="API地址"
                        description="Claude Code API服务的基础URL"
                        type="url"
                        value={settings.claudeCodeUrl}
                        onChange={handleUrlChange}
                        placeholder="http://localhost:3005"
                        required={true}
                    />

                    <SettingInput
                        label="API密钥"
                        description="用于API认证的密钥（可选）"
                        type="password"
                        value={settings.apiKey || ''}
                        onChange={handleApiKeyChange}
                        placeholder="输入API密钥"
                    />

                    <SettingNumber
                        label="请求超时时间"
                        description="API请求的最大等待时间（秒）"
                        value={settings.commandTimeout / 1000}
                        onChange={(value) => handleTimeoutChange(value * 1000)}
                        min={5}
                        max={300}
                        unit="秒"
                    />
                </SettingGroup>

                {/* 连接测试 */}
                <SettingGroup title="连接测试">
                    <div className="connection-test">
                        <div className="test-status">
                            <div className={`status-indicator ${connectionStatus}`}>
                                {getStatusIcon(connectionStatus)}
                                <span>{getStatusText(connectionStatus)}</span>
                            </div>
                            {connectionMessage && (
                                <p className="connection-message">{connectionMessage}</p>
                            )}
                        </div>

                        <button
                            className="action-button secondary"
                            onClick={testConnection}
                            disabled={testingConnection}
                        >
                            {testingConnection ? (
                                <>
                                    <LoadingSpinner size="small" />
                                    测试中...
                                </>
                            ) : (
                                <>
                                    <Icon name="zap" size="small" />
                                    测试连接
                                </>
                            )}
                        </button>
                    </div>
                </SettingGroup>

                {/* 高级连接选项 */}
                <SettingGroup title="高级选项">
                    <SettingToggle
                        label="启用请求缓存"
                        description="缓存API请求结果以提高响应速度"
                        checked={settings.enableCache}
                        onChange={(checked) => {
                            onSettingsChange({ enableCache: checked });
                            onChanged();
                        }}
                    />

                    <SettingNumber
                        label="重试次数"
                        description="请求失败时的自动重试次数"
                        value={settings.retryCount || 3}
                        onChange={(value) => {
                            onSettingsChange({ retryCount: value });
                            onChanged();
                        }}
                        min={0}
                        max={10}
                    />

                    <SettingSelect
                        label="日志级别"
                        description="API请求的日志记录级别"
                        value={settings.logLevel || 'info'}
                        onChange={(value) => {
                            onSettingsChange({ logLevel: value });
                            onChanged();
                        }}
                        options={[
                            { value: 'none', label: '无日志' },
                            { value: 'error', label: '仅错误' },
                            { value: 'warn', label: '警告及以上' },
                            { value: 'info', label: '信息及以上' },
                            { value: 'debug', label: '调试日志' }
                        ]}
                    />
                </SettingGroup>
            </div>
        </div>
    );
};

// 连接状态图标
const getStatusIcon = (status: string) => {
    const icons = {
        idle: <Icon name="circle" size="small" />,
        testing: <Icon name="loader" size="small" className="animate-spin" />,
        success: <Icon name="check-circle" size="small" />,
        error: <Icon name="x-circle" size="small" />
    };

    return icons[status] || icons.idle;
};

// 连接状态文本
const getStatusText = (status: string) => {
    const texts = {
        idle: '未测试',
        testing: '测试中',
        success: '连接正常',
        error: '连接失败'
    };

    return texts[status] || '未知状态';
};
```

### StorageSettings组件实现

**存储设置组件** [Source: canvas-progress-tracker/docs/obsidian-plugin-prd.md#FR-004]
```typescript
import React, { useState, useCallback } from 'react';

interface StorageSettingsProps {
    settings: PluginSettings;
    onSettingsChange: (changes: Partial<PluginSettings>) => void;
    onChanged: () => void;
}

export const StorageSettings: React.FC<StorageSettingsProps> = ({
    settings,
    onSettingsChange,
    onChanged
}) => {
    const [backupProgress, setBackupProgress] = useState<number | null>(null);
    const [cleanupProgress, setCleanupProgress] = useState<number | null>(null);

    const handleDataPathChange = useCallback((path: string) => {
        onSettingsChange({ dataPath: path });
        onChanged();
    }, [onSettingsChange, onChanged]);

    const handleBackupSettingsChange = useCallback((changes: any) => {
        onSettingsChange(changes);
        onChanged();
    }, [onSettingsChange, onChanged]);

    const createBackup = useCallback(async () => {
        setBackupProgress(0);
        try {
            await plugin.dataManager.createBackup();
            setBackupProgress(100);
            new Notice('✅ 备份创建成功');
        } catch (error) {
            new Notice('❌ 备份创建失败');
        } finally {
            setTimeout(() => setBackupProgress(null), 2000);
        }
    }, [plugin]);

    const cleanupData = useCallback(async () => {
        setCleanupProgress(0);
        try {
            await plugin.dataManager.cleanupOldData();
            setCleanupProgress(100);
            new Notice('✅ 数据清理完成');
        } catch (error) {
            new Notice('❌ 数据清理失败');
        } finally {
            setTimeout(() => setCleanupProgress(null), 2000);
        }
    }, [plugin]);

    return (
        <div className="settings-section">
            <div className="section-header">
                <h2>数据存储设置</h2>
                <p className="section-description">
                    配置数据存储路径、备份策略和数据管理
                </p>
            </div>

            <div className="settings-form">
                {/* 数据路径配置 */}
                <SettingGroup title="存储路径">
                    <SettingPath
                        label="数据存储路径"
                        description="Canvas学习系统数据的存储目录"
                        value={settings.dataPath}
                        onChange={handleDataPathChange}
                        placeholder="选择数据存储目录"
                        required={true}
                    />

                    <div className="path-info">
                        <div className="info-item">
                            <span className="label">数据库文件:</span>
                            <span className="value">
                                {settings.dataPath}/canvas-review.db
                            </span>
                        </div>
                        <div className="info-item">
                            <span className="label">备份目录:</span>
                            <span className="value">
                                {settings.dataPath}/backups/
                            </span>
                        </div>
                    </div>
                </SettingGroup>

                {/* 备份设置 */}
                <SettingGroup title="备份策略">
                    <SettingToggle
                        label="启用自动备份"
                        description="定期自动创建数据备份"
                        checked={settings.autoBackup}
                        onChange={(checked) => handleBackupSettingsChange({ autoBackup: checked })}
                    />

                    {settings.autoBackup && (
                        <>
                            <SettingNumber
                                label="备份间隔"
                                description="自动备份的时间间隔（小时）"
                                value={settings.backupInterval || 24}
                                onChange={(value) => handleBackupSettingsChange({ backupInterval: value })}
                                min={1}
                                max={168}
                                unit="小时"
                            />

                            <SettingNumber
                                label="保留天数"
                                description="备份文件的保留时间"
                                value={settings.backupRetentionDays || 30}
                                onChange={(value) => handleBackupSettingsChange({ backupRetentionDays: value })}
                                min={1}
                                max={365}
                                unit="天"
                            />

                            <SettingToggle
                                label="压缩备份"
                                description="压缩备份文件以节省存储空间"
                                checked={settings.compressBackups || false}
                                onChange={(checked) => handleBackupSettingsChange({ compressBackups: checked })}
                            />
                        </>
                    )}
                </SettingGroup>

                {/* 同步设置 */}
                <SettingGroup title="数据同步">
                    <SettingNumber
                        label="同步间隔"
                        description="数据自动同步的时间间隔（分钟）"
                        value={settings.autoSyncInterval / 60000}
                        onChange={(value) => handleBackupSettingsChange({
                            autoSyncInterval: value * 60000
                        })}
                        min={1}
                        max={1440}
                        unit="分钟"
                    />

                    <SettingSelect
                        label="冲突解决策略"
                        description="数据同步冲突时的解决方式"
                        value={settings.conflictResolution || 'prompt'}
                        onChange={(value) => handleBackupSettingsChange({ conflictResolution: value })}
                        options={[
                            { value: 'prompt', label: '提示用户选择' },
                            { value: 'local', label: '使用本地数据' },
                            { value: 'remote', label: '使用远程数据' },
                            { value: 'merge', label: '尝试自动合并' }
                        ]}
                    />
                </SettingGroup>

                {/* 数据管理 */}
                <SettingGroup title="数据管理">
                    <div className="management-actions">
                        <div className="action-item">
                            <div className="action-info">
                                <h4>创建备份</h4>
                                <p>立即创建当前数据的完整备份</p>
                            </div>
                            <button
                                className="action-button secondary"
                                onClick={createBackup}
                                disabled={backupProgress !== null}
                            >
                                {backupProgress !== null ? (
                                    <>
                                        <LoadingSpinner size="small" />
                                        {backupProgress}%
                                    </>
                                ) : (
                                    <>
                                        <Icon name="download" size="small" />
                                        立即备份
                                    </>
                                )}
                            </button>
                        </div>

                        <div className="action-item">
                            <div className="action-info">
                                <h4>清理数据</h4>
                                <p>清理过期的缓存和临时文件</p>
                            </div>
                            <button
                                className="action-button secondary"
                                onClick={cleanupData}
                                disabled={cleanupProgress !== null}
                            >
                                {cleanupProgress !== null ? (
                                    <>
                                        <LoadingSpinner size="small" />
                                        {cleanupProgress}%
                                    </>
                                ) : (
                                    <>
                                        <Icon name="trash-2" size="small" />
                                        清理数据
                                    </>
                                )}
                            </button>
                        </div>

                        <div className="action-item">
                            <div className="action-info">
                                <h4>导出数据</h4>
                                <p>导出所有学习数据为JSON格式</p>
                            </div>
                            <button
                                className="action-button secondary"
                                onClick={() => {/* 导出数据 */}}
                            >
                                <Icon name="file-text" size="small" />
                                导出数据
                            </button>
                        </div>
                    </div>
                </SettingGroup>

                {/* 存储统计 */}
                <SettingGroup title="存储统计">
                    <StorageStats />
                </SettingGroup>
            </div>
        </div>
    );
};
```

### 设置样式实现

**设置面板样式** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#样式集成]
```css
/* styles/settings-panel.css */

.settings-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: var(--background-primary);
    color: var(--text-normal);
    font-family: var(--font-text);
}

/* 设置头部 */
.settings-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 1.5rem;
    border-bottom: 1px solid var(--background-modifier-border);
    background-color: var(--background-secondary);
}

.header-content h1 {
    margin: 0 0 0.25rem 0;
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text-normal);
}

.settings-description {
    margin: 0;
    color: var(--text-muted);
    font-size: 0.875rem;
}

.header-actions {
    display: flex;
    gap: 0.5rem;
}

/* 设置主体 */
.settings-body {
    display: flex;
    flex: 1;
    overflow: hidden;
}

/* 侧边导航 */
.settings-navigation {
    width: 240px;
    background-color: var(--background-secondary-alt);
    border-right: 1px solid var(--background-modifier-border);
    overflow-y: auto;
}

.nav-menu {
    padding: 1rem 0;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    padding: 0.75rem 1.5rem;
    border: none;
    background: none;
    color: var(--text-muted);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
}

.nav-item:hover {
    background-color: var(--background-modifier-hover);
    color: var(--text-normal);
}

.nav-item.active {
    background-color: var(--interactive-accent);
    color: var(--text-on-accent);
}

/* 设置内容区域 */
.settings-content {
    flex: 1;
    overflow-y: auto;
}

.content-scroll {
    padding: 2rem;
    max-width: 800px;
    margin: 0 auto;
}

/* 设置分组 */
.settings-section {
    margin-bottom: 2rem;
}

.section-header {
    margin-bottom: 1.5rem;
}

.section-header h2 {
    margin: 0 0 0.5rem 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-normal);
}

.section-description {
    margin: 0;
    color: var(--text-muted);
    font-size: 0.875rem;
}

.settings-form {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

/* 设置组 */
.setting-group {
    background-color: var(--background-primary);
    border: 1px solid var(--background-modifier-border);
    border-radius: 8px;
    padding: 1.5rem;
}

.setting-group-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-normal);
    margin: 0 0 1rem 0;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--background-modifier-border);
}

/* 设置项 */
.setting-item {
    margin-bottom: 1rem;
}

.setting-item:last-child {
    margin-bottom: 0;
}

.setting-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 500;
    color: var(--text-normal);
    margin-bottom: 0.25rem;
}

.setting-description {
    font-size: 0.875rem;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
}

/* 输入控件 */
.setting-input {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--background-modifier-border);
    border-radius: 4px;
    background-color: var(--background-primary);
    color: var(--text-normal);
    font-size: 0.875rem;
    transition: border-color 0.2s ease;
}

.setting-input:focus {
    outline: none;
    border-color: var(--interactive-accent);
}

.setting-input:invalid {
    border-color: var(--text-error);
}

.setting-number {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.setting-number input {
    flex: 1;
}

.setting-number .unit {
    font-size: 0.875rem;
    color: var(--text-muted);
    min-width: 3rem;
}

.setting-select {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--background-modifier-border);
    border-radius: 4px;
    background-color: var(--background-primary);
    color: var(--text-normal);
    font-size: 0.875rem;
}

.setting-toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 0;
}

.setting-toggle-content {
    flex: 1;
}

.toggle-switch {
    position: relative;
    width: 44px;
    height: 24px;
    background-color: var(--background-modifier-border);
    border-radius: 12px;
    cursor: pointer;
    transition: background-color 0.2s ease;
}

.toggle-switch.active {
    background-color: var(--interactive-accent);
}

.toggle-switch::after {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    width: 20px;
    height: 20px;
    background-color: white;
    border-radius: 50%;
    transition: transform 0.2s ease;
}

.toggle-switch.active::after {
    transform: translateX(20px);
}

/* 连接测试 */
.connection-test {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    background-color: var(--background-secondary);
    border-radius: 6px;
}

.test-status {
    flex: 1;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 500;
}

.status-indicator.success {
    color: var(--text-success);
}

.status-indicator.error {
    color: var(--text-error);
}

.connection-message {
    margin: 0.5rem 0 0 0;
    font-size: 0.875rem;
}

/* 管理操作 */
.management-actions {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.action-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    background-color: var(--background-secondary);
    border-radius: 6px;
}

.action-info h4 {
    margin: 0 0 0.25rem 0;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-normal);
}

.action-info p {
    margin: 0;
    font-size: 0.75rem;
    color: var(--text-muted);
}

/* 设置底部 */
.settings-footer {
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--background-modifier-border);
    background-color: var(--background-secondary);
}

.footer-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.unsaved-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-warning);
    font-weight: 500;
}

.footer-actions {
    display: flex;
    gap: 0.5rem;
}

/* 导入提示 */
.import-prompt {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.prompt-content {
    background-color: var(--background-primary);
    border: 1px solid var(--background-modifier-border);
    border-radius: 8px;
    padding: 1.5rem;
    max-width: 400px;
    width: 90%;
}

.prompt-content p {
    margin: 0 0 1rem 0;
    color: var(--text-normal);
}

.prompt-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .settings-header {
        flex-direction: column;
        gap: 1rem;
        align-items: stretch;
    }

    .header-actions {
        justify-content: center;
    }

    .settings-body {
        flex-direction: column;
    }

    .settings-navigation {
        width: 100%;
        border-right: none;
        border-bottom: 1px solid var(--background-modifier-border);
    }

    .nav-menu {
        display: flex;
        padding: 0;
        overflow-x: auto;
    }

    .nav-item {
        flex-shrink: 0;
        white-space: nowrap;
        border-bottom: 2px solid transparent;
    }

    .nav-item.active {
        border-bottom-color: var(--interactive-accent);
    }

    .content-scroll {
        padding: 1rem;
    }

    .action-item {
        flex-direction: column;
        gap: 1rem;
        align-items: stretch;
        text-align: center;
    }

    .footer-content {
        flex-direction: column;
        gap: 1rem;
        align-items: stretch;
    }
}

/* 动画效果 */
@keyframes slideIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.settings-section {
    animation: slideIn 0.3s ease;
}

/* 可访问性 */
.nav-item:focus-visible,
.action-button:focus-visible {
    outline: 2px solid var(--interactive-accent);
    outline-offset: 2px;
}

.setting-input:focus-visible,
.setting-select:focus-visible {
    outline: 2px solid var(--interactive-accent);
    outline-offset: 1px;
}
```

### 测试要求

**单元测试**:
- 测试所有设置组件的渲染和交互
- 测试设置验证和错误处理
- 测试设置的保存和加载功能
- 测试连接测试和数据管理功能

**集成测试**:
- 测试设置面板与插件系统的集成
- 测试设置更改的实时生效
- 测试设置的导入导出功能

**用户体验测试**:
- 测试设置的直观性和易用性
- 测试错误提示和帮助信息
- 测试响应式布局在不同设备上的表现

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-27 | 1.0 | 初始Story创建 | PM Agent (Sarah) |

## Dev Agent Record

### Agent Model Used
待开发

### Debug Log References
待开发

### Completion Notes
待开发

### File List
**计划创建的文件：**
- `canvas-progress-tracker/obsidian-plugin/src/settings/PluginSettingsTab.ts` - 主设置标签页
- `canvas-progress-tracker/obsidian-plugin/src/settings/SettingsPanel.tsx` - React设置面板
- `canvas-progress-tracker/obsidian-plugin/src/settings/ConnectionSettings.tsx` - 连接设置组件
- `canvas-progress-tracker/obsidian-plugin/src/settings/StorageSettings.tsx` - 存储设置组件
- `canvas-progress-tracker/obsidian-plugin/src/settings/InterfaceSettings.tsx` - 界面设置组件
- `canvas-progress-tracker/obsidian-plugin/src/settings/ReviewSettings.tsx` - 复习设置组件
- `canvas-progress-tracker/obsidian-plugin/src/settings/AdvancedSettings.tsx` - 高级设置组件
- `canvas-progress-tracker/obsidian-plugin/src/components/Settings/SettingGroup.tsx` - 设置分组组件
- `canvas-progress-tracker/obsidian-plugin/src/components/Settings/SettingInput.tsx` - 输入设置组件
- `canvas-progress-tracker/obsidian-plugin/src/components/Settings/SettingToggle.tsx` - 开关设置组件
- `canvas-progress-tracker/obsidian-plugin/src/components/Settings/SettingSelect.tsx` - 选择设置组件
- `canvas-progress-tracker/obsidian-plugin/src/components/Settings/SettingNumber.tsx` - 数字设置组件
- `canvas-progress-tracker/obsidian-plugin/src/components/Settings/SettingPath.tsx` - 路径设置组件
- `canvas-progress-tracker/obsidian-plugin/src/types/SettingsTypes.ts` - 设置类型定义
- `canvas-progress-tracker/obsidian-plugin/src/styles/settings-panel.css` - 设置面板样式

**修改的文件：**
- `canvas-progress-tracker/obsidian-plugin/main.ts` - 注册设置标签页
- `canvas-progress-tracker/obsidian-plugin/src/types/index.ts` - 扩展设置类型

## QA Results

### Review Date: 待开发

### Reviewed By: 待开发

### Code Quality Assessment
待开发

### Compliance Check
待开发

### Security Review
待开发

### Performance Considerations
待开发

### Architecture & Design Review
待开发

### Test Quality Review
待开发

### Final Status
待开发

---

**本Story完成后，将为用户提供一个功能完整、界面友好的设置面板，实现插件参数的全面配置管理，包括连接设置、数据存储、界面定制、复习偏好和高级选项，确保用户能够根据个人需求完全自定义插件的行为和外观。**
