/**
 * Canvas Review System - Settings Type Definitions
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-api (Plugin Settings Interface)
 * ✅ Verified from Story 13.6 Dev Notes: canvas-progress-tracker/docs/obsidian-plugin-prd.md#FR-009
 *
 * @module types/settings
 * @version 2.0.0
 */

/**
 * Plugin settings interface
 *
 * Defines all configurable options for the Canvas Review System plugin.
 * These settings are persisted in the Obsidian data.json file.
 *
 * Settings are organized into sections:
 * - Connection: Claude Code API configuration
 * - Storage: Data storage and backup settings
 * - Interface: Theme and display options
 * - Review: Review preferences and scheduling
 * - Advanced: Debug and developer options
 */
export interface PluginSettings {
    // ========== Connection Settings ==========
    /**
     * Claude Code API service base URL
     * Used for communicating with the backend Canvas analysis service
     * @default 'http://localhost:3005'
     */
    claudeCodeUrl: string;

    /**
     * API key for authentication (optional)
     * Used when the API requires authentication
     * @default ''
     */
    apiKey: string;

    /**
     * Command execution timeout in milliseconds
     * Maximum time to wait for a command to complete
     * @default 30000
     */
    commandTimeout: number;

    /**
     * Number of retry attempts for failed requests
     * @default 3
     */
    retryCount: number;

    /**
     * Enable request caching for performance
     * @default true
     */
    enableCache: boolean;

    /**
     * Log level for API requests
     * @default 'info'
     */
    logLevel: 'none' | 'error' | 'warn' | 'info' | 'debug';

    // ========== Storage Settings ==========
    /**
     * Canvas learning system data storage path
     * Path where Canvas files and learning data are stored
     * @default ''
     */
    dataPath: string;

    /**
     * Enable automatic backup
     * @default true
     */
    autoBackup: boolean;

    /**
     * Backup interval in hours
     * @default 24
     */
    backupInterval: number;

    /**
     * Number of days to retain backups
     * @default 30
     */
    backupRetentionDays: number;

    /**
     * Compress backup files to save space
     * @default false
     */
    compressBackups: boolean;

    /**
     * Auto-sync interval in minutes
     * How often to automatically sync Canvas progress data
     * @default 5
     */
    autoSyncInterval: number;

    /**
     * Conflict resolution strategy for data sync
     * @default 'prompt'
     */
    conflictResolution: 'prompt' | 'local' | 'remote' | 'merge';

    // ========== Interface Settings ==========
    /**
     * UI theme setting
     * Controls the visual appearance of the plugin UI
     * @default 'auto'
     */
    theme: 'light' | 'dark' | 'auto';

    /**
     * Language setting
     * @default 'zh-CN'
     */
    language: string;

    /**
     * Font size scale factor
     * @default 1.0
     */
    fontScale: number;

    /**
     * Enable animations and transitions
     * @default true
     */
    enableAnimations: boolean;

    /**
     * Show tooltips on hover
     * @default true
     */
    showTooltips: boolean;

    /**
     * Compact mode for smaller UI
     * @default false
     */
    compactMode: boolean;

    // ========== Review Settings ==========
    /**
     * Default review duration in minutes
     * @default 30
     */
    defaultReviewDuration: number;

    /**
     * Enable review reminders
     * @default true
     */
    reminderEnabled: boolean;

    /**
     * Reminder time (HH:MM format)
     * @default '09:00'
     */
    reminderTime: string;

    /**
     * Reminder days before review
     * @default [1, 7, 30]
     */
    reminderDays: number[];

    /**
     * Minimum score threshold for passing (0-100)
     * @default 60
     */
    passingScore: number;

    /**
     * Enable spaced repetition algorithm
     * @default true
     */
    enableSpacedRepetition: boolean;

    /**
     * Difficulty weight for scoring
     * @default 1.0
     */
    difficultyWeight: number;

    // ========== Notification Settings (Story 14.7) ==========
    /**
     * Enable daily review notifications
     * @default true
     */
    enableNotifications: boolean;

    /**
     * Quiet hours start (0-23)
     * Notifications will not be shown during quiet hours
     * @default 23
     */
    quietHoursStart: number;

    /**
     * Quiet hours end (0-23)
     * Notifications will resume after this hour
     * @default 7
     */
    quietHoursEnd: number;

    /**
     * Minimum interval between notifications in hours
     * Prevents notification spam
     * @default 12
     */
    minNotificationInterval: number;

    // ========== Advanced Settings ==========
    /**
     * Enable debug logging
     * When enabled, detailed logs are written to the console
     * @default false
     */
    debugMode: boolean;

    /**
     * Enable performance monitoring
     * @default false
     */
    enablePerformanceMonitoring: boolean;

    /**
     * Maximum number of concurrent operations
     * Limits parallel processing to prevent resource exhaustion
     * @default 5
     */
    maxConcurrentOps: number;

    /**
     * Enable telemetry (anonymous usage data)
     * @default false
     */
    enableTelemetry: boolean;

    /**
     * Enable experimental features
     * @default false
     */
    enableExperimentalFeatures: boolean;

    /**
     * Custom CSS for UI customization
     * @default ''
     */
    customCss: string;

    /**
     * Settings version for migration
     * @default 2
     */
    settingsVersion: number;

    // ========== Association Mode Settings (Story 16.4) ==========
    /**
     * Enable cross-Canvas association mode
     * When enabled, Canvas nodes display association indicators and support cross-Canvas linking
     * @default false
     */
    associationModeEnabled: boolean;
}

/**
 * Default plugin settings
 *
 * These values are used when the plugin is first installed
 * or when settings are reset to defaults.
 */
export const DEFAULT_SETTINGS: PluginSettings = {
    // Connection Settings
    claudeCodeUrl: 'http://localhost:3005',
    apiKey: '',
    commandTimeout: 30000,
    retryCount: 3,
    enableCache: true,
    logLevel: 'info',

    // Storage Settings
    dataPath: '',
    autoBackup: true,
    backupInterval: 24,
    backupRetentionDays: 30,
    compressBackups: false,
    autoSyncInterval: 5,
    conflictResolution: 'prompt',

    // Interface Settings
    theme: 'auto',
    language: 'zh-CN',
    fontScale: 1.0,
    enableAnimations: true,
    showTooltips: true,
    compactMode: false,

    // Review Settings
    defaultReviewDuration: 30,
    reminderEnabled: true,
    reminderTime: '09:00',
    reminderDays: [1, 7, 30],
    passingScore: 60,
    enableSpacedRepetition: true,
    difficultyWeight: 1.0,

    // Notification Settings (Story 14.7)
    enableNotifications: true,
    quietHoursStart: 23,
    quietHoursEnd: 7,
    minNotificationInterval: 12,

    // Advanced Settings
    debugMode: false,
    enablePerformanceMonitoring: false,
    maxConcurrentOps: 5,
    enableTelemetry: false,
    enableExperimentalFeatures: false,
    customCss: '',
    settingsVersion: 2,

    // Association Mode Settings (Story 16.4)
    associationModeEnabled: false
};

/**
 * Settings section identifiers
 */
export type SettingsSection = 'connection' | 'storage' | 'interface' | 'review' | 'advanced';

/**
 * Settings section metadata
 */
export interface SettingsSectionInfo {
    id: SettingsSection;
    name: string;
    description: string;
    icon: string;
}

/**
 * Available settings sections
 */
export const SETTINGS_SECTIONS: SettingsSectionInfo[] = [
    {
        id: 'connection',
        name: '连接设置',
        description: 'Claude Code API连接配置',
        icon: '🔗'
    },
    {
        id: 'storage',
        name: '数据存储',
        description: '数据路径、备份和同步设置',
        icon: '💾'
    },
    {
        id: 'interface',
        name: '界面设置',
        description: '主题、字体和显示选项',
        icon: '🎨'
    },
    {
        id: 'review',
        name: '复习偏好',
        description: '复习时长、提醒和评分设置',
        icon: '📚'
    },
    {
        id: 'advanced',
        name: '高级设置',
        description: '调试、性能和实验性功能',
        icon: '⚙️'
    }
];

/**
 * Validation result for settings
 */
export interface SettingsValidationResult {
    isValid: boolean;
    errors: string[];
    warnings: string[];
}

/**
 * Validates plugin settings
 *
 * @param settings - Settings object to validate
 * @returns Validation result with any errors found
 */
export function validateSettings(settings: Partial<PluginSettings>): SettingsValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Validate claudeCodeUrl
    if (settings.claudeCodeUrl !== undefined) {
        if (settings.claudeCodeUrl.trim() === '') {
            warnings.push('Claude Code URL is empty - API features will not work');
        } else {
            try {
                new URL(settings.claudeCodeUrl);
            } catch {
                errors.push('Claude Code URL must be a valid URL');
            }
        }
    }

    // Validate commandTimeout
    if (settings.commandTimeout !== undefined) {
        if (settings.commandTimeout < 5000 || settings.commandTimeout > 300000) {
            errors.push('Command timeout must be between 5000ms and 300000ms');
        }
    }

    // Validate retryCount
    if (settings.retryCount !== undefined) {
        if (settings.retryCount < 0 || settings.retryCount > 10) {
            errors.push('Retry count must be between 0 and 10');
        }
    }

    // Validate autoSyncInterval
    if (settings.autoSyncInterval !== undefined) {
        if (settings.autoSyncInterval < 0 || settings.autoSyncInterval > 60) {
            errors.push('Auto-sync interval must be between 0 and 60 minutes');
        }
    }

    // Validate backupInterval
    if (settings.backupInterval !== undefined) {
        if (settings.backupInterval < 1 || settings.backupInterval > 168) {
            errors.push('Backup interval must be between 1 and 168 hours');
        }
    }

    // Validate backupRetentionDays
    if (settings.backupRetentionDays !== undefined) {
        if (settings.backupRetentionDays < 1 || settings.backupRetentionDays > 365) {
            errors.push('Backup retention must be between 1 and 365 days');
        }
    }

    // Validate maxConcurrentOps
    if (settings.maxConcurrentOps !== undefined) {
        if (settings.maxConcurrentOps < 1 || settings.maxConcurrentOps > 20) {
            errors.push('Max concurrent operations must be between 1 and 20');
        }
    }

    // Validate fontScale
    if (settings.fontScale !== undefined) {
        if (settings.fontScale < 0.5 || settings.fontScale > 2.0) {
            errors.push('Font scale must be between 0.5 and 2.0');
        }
    }

    // Validate passingScore
    if (settings.passingScore !== undefined) {
        if (settings.passingScore < 0 || settings.passingScore > 100) {
            errors.push('Passing score must be between 0 and 100');
        }
    }

    // Validate difficultyWeight
    if (settings.difficultyWeight !== undefined) {
        if (settings.difficultyWeight < 0.1 || settings.difficultyWeight > 5.0) {
            errors.push('Difficulty weight must be between 0.1 and 5.0');
        }
    }

    // Validate reminderTime format
    if (settings.reminderTime !== undefined) {
        const timeRegex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/;
        if (!timeRegex.test(settings.reminderTime)) {
            errors.push('Reminder time must be in HH:MM format');
        }
    }

    // Validate defaultReviewDuration
    if (settings.defaultReviewDuration !== undefined) {
        if (settings.defaultReviewDuration < 5 || settings.defaultReviewDuration > 180) {
            errors.push('Default review duration must be between 5 and 180 minutes');
        }
    }

    // Validate quietHoursStart (Story 14.7)
    if (settings.quietHoursStart !== undefined) {
        if (settings.quietHoursStart < 0 || settings.quietHoursStart > 23) {
            errors.push('Quiet hours start must be between 0 and 23');
        }
    }

    // Validate quietHoursEnd (Story 14.7)
    if (settings.quietHoursEnd !== undefined) {
        if (settings.quietHoursEnd < 0 || settings.quietHoursEnd > 23) {
            errors.push('Quiet hours end must be between 0 and 23');
        }
    }

    // Validate minNotificationInterval (Story 14.7)
    if (settings.minNotificationInterval !== undefined) {
        if (settings.minNotificationInterval < 1 || settings.minNotificationInterval > 48) {
            errors.push('Minimum notification interval must be between 1 and 48 hours');
        }
    }

    return {
        isValid: errors.length === 0,
        errors,
        warnings
    };
}

/**
 * Migrates settings from older versions
 *
 * @param settings - Old settings object
 * @returns Migrated settings with defaults for new fields
 */
export function migrateSettings(settings: Partial<PluginSettings>): PluginSettings {
    const migrated = { ...DEFAULT_SETTINGS, ...settings };

    // Handle version 1 to version 2 migration
    if (!settings.settingsVersion || settings.settingsVersion < 2) {
        // Add new fields with defaults
        migrated.apiKey = settings.apiKey ?? '';
        migrated.retryCount = settings.retryCount ?? 3;
        migrated.logLevel = settings.logLevel ?? 'info';
        migrated.backupInterval = settings.backupInterval ?? 24;
        migrated.compressBackups = settings.compressBackups ?? false;
        migrated.conflictResolution = settings.conflictResolution ?? 'prompt';
        migrated.language = settings.language ?? 'zh-CN';
        migrated.fontScale = settings.fontScale ?? 1.0;
        migrated.enableAnimations = settings.enableAnimations ?? true;
        migrated.showTooltips = settings.showTooltips ?? true;
        migrated.compactMode = settings.compactMode ?? false;
        migrated.defaultReviewDuration = settings.defaultReviewDuration ?? 30;
        migrated.reminderEnabled = settings.reminderEnabled ?? true;
        migrated.reminderTime = settings.reminderTime ?? '09:00';
        migrated.reminderDays = settings.reminderDays ?? [1, 7, 30];
        migrated.passingScore = settings.passingScore ?? 60;
        migrated.enableSpacedRepetition = settings.enableSpacedRepetition ?? true;
        migrated.difficultyWeight = settings.difficultyWeight ?? 1.0;
        migrated.enablePerformanceMonitoring = settings.enablePerformanceMonitoring ?? false;
        migrated.enableTelemetry = settings.enableTelemetry ?? false;
        migrated.enableExperimentalFeatures = settings.enableExperimentalFeatures ?? false;
        migrated.customCss = settings.customCss ?? '';
        // Notification Settings (Story 14.7)
        migrated.enableNotifications = settings.enableNotifications ?? true;
        migrated.quietHoursStart = settings.quietHoursStart ?? 23;
        migrated.quietHoursEnd = settings.quietHoursEnd ?? 7;
        migrated.minNotificationInterval = settings.minNotificationInterval ?? 12;
        migrated.settingsVersion = 2;
    }

    return migrated;
}

/**
 * Exports settings to JSON string
 *
 * @param settings - Settings to export
 * @returns JSON string representation
 */
export function exportSettings(settings: PluginSettings): string {
    const exportData = {
        ...settings,
        exportedAt: new Date().toISOString(),
        exportVersion: 2
    };
    return JSON.stringify(exportData, null, 2);
}

/**
 * Imports settings from JSON string
 *
 * @param jsonString - JSON string to import
 * @returns Imported and validated settings
 * @throws Error if JSON is invalid or settings are malformed
 */
export function importSettings(jsonString: string): PluginSettings {
    try {
        const imported = JSON.parse(jsonString);

        // Remove export metadata
        delete imported.exportedAt;
        delete imported.exportVersion;

        // Validate imported settings
        const validation = validateSettings(imported);
        if (!validation.isValid) {
            throw new Error(`Invalid settings: ${validation.errors.join(', ')}`);
        }

        // Migrate if needed
        return migrateSettings(imported);
    } catch (e) {
        if (e instanceof SyntaxError) {
            throw new Error('Invalid JSON format');
        }
        throw e;
    }
}
