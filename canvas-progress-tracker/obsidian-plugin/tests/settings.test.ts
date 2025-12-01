/**
 * Canvas Review System - Settings Tests
 *
 * Comprehensive tests for the settings module including:
 * - Default settings values
 * - Settings validation (all fields)
 * - Settings merge behavior
 * - Settings migration
 * - Settings export/import
 * - Settings sections metadata
 *
 * @module tests/settings
 * @version 2.0.0
 */

import {
    PluginSettings,
    DEFAULT_SETTINGS,
    validateSettings,
    migrateSettings,
    exportSettings,
    importSettings,
    SETTINGS_SECTIONS,
    SettingsSection,
    SettingsSectionInfo
} from '../src/types/settings';

describe('PluginSettings', () => {
    describe('DEFAULT_SETTINGS', () => {
        // Connection Settings
        it('should have correct default claudeCodeUrl', () => {
            expect(DEFAULT_SETTINGS.claudeCodeUrl).toBe('http://localhost:3005');
        });

        it('should have empty default apiKey', () => {
            expect(DEFAULT_SETTINGS.apiKey).toBe('');
        });

        it('should have correct default commandTimeout', () => {
            expect(DEFAULT_SETTINGS.commandTimeout).toBe(30000);
        });

        it('should have correct default retryCount', () => {
            expect(DEFAULT_SETTINGS.retryCount).toBe(3);
        });

        it('should have enableCache enabled by default', () => {
            expect(DEFAULT_SETTINGS.enableCache).toBe(true);
        });

        it('should have correct default logLevel', () => {
            expect(DEFAULT_SETTINGS.logLevel).toBe('info');
        });

        // Storage Settings
        it('should have empty default dataPath', () => {
            expect(DEFAULT_SETTINGS.dataPath).toBe('');
        });

        it('should have autoBackup enabled by default', () => {
            expect(DEFAULT_SETTINGS.autoBackup).toBe(true);
        });

        it('should have correct default backupInterval', () => {
            expect(DEFAULT_SETTINGS.backupInterval).toBe(24);
        });

        it('should have correct default backupRetentionDays', () => {
            expect(DEFAULT_SETTINGS.backupRetentionDays).toBe(30);
        });

        it('should have compressBackups disabled by default', () => {
            expect(DEFAULT_SETTINGS.compressBackups).toBe(false);
        });

        it('should have correct default autoSyncInterval', () => {
            expect(DEFAULT_SETTINGS.autoSyncInterval).toBe(5);
        });

        it('should have correct default conflictResolution', () => {
            expect(DEFAULT_SETTINGS.conflictResolution).toBe('prompt');
        });

        // Interface Settings
        it('should have auto theme by default', () => {
            expect(DEFAULT_SETTINGS.theme).toBe('auto');
        });

        it('should have correct default language', () => {
            expect(DEFAULT_SETTINGS.language).toBe('zh-CN');
        });

        it('should have correct default fontScale', () => {
            expect(DEFAULT_SETTINGS.fontScale).toBe(1.0);
        });

        it('should have enableAnimations enabled by default', () => {
            expect(DEFAULT_SETTINGS.enableAnimations).toBe(true);
        });

        it('should have showTooltips enabled by default', () => {
            expect(DEFAULT_SETTINGS.showTooltips).toBe(true);
        });

        it('should have compactMode disabled by default', () => {
            expect(DEFAULT_SETTINGS.compactMode).toBe(false);
        });

        // Review Settings
        it('should have correct default defaultReviewDuration', () => {
            expect(DEFAULT_SETTINGS.defaultReviewDuration).toBe(30);
        });

        it('should have reminderEnabled enabled by default', () => {
            expect(DEFAULT_SETTINGS.reminderEnabled).toBe(true);
        });

        it('should have correct default reminderTime', () => {
            expect(DEFAULT_SETTINGS.reminderTime).toBe('09:00');
        });

        it('should have correct default reminderDays', () => {
            expect(DEFAULT_SETTINGS.reminderDays).toEqual([1, 7, 30]);
        });

        it('should have correct default passingScore', () => {
            expect(DEFAULT_SETTINGS.passingScore).toBe(60);
        });

        it('should have enableSpacedRepetition enabled by default', () => {
            expect(DEFAULT_SETTINGS.enableSpacedRepetition).toBe(true);
        });

        it('should have correct default difficultyWeight', () => {
            expect(DEFAULT_SETTINGS.difficultyWeight).toBe(1.0);
        });

        // Advanced Settings
        it('should have debugMode disabled by default', () => {
            expect(DEFAULT_SETTINGS.debugMode).toBe(false);
        });

        it('should have enablePerformanceMonitoring disabled by default', () => {
            expect(DEFAULT_SETTINGS.enablePerformanceMonitoring).toBe(false);
        });

        it('should have correct default maxConcurrentOps', () => {
            expect(DEFAULT_SETTINGS.maxConcurrentOps).toBe(5);
        });

        it('should have enableTelemetry disabled by default', () => {
            expect(DEFAULT_SETTINGS.enableTelemetry).toBe(false);
        });

        it('should have enableExperimentalFeatures disabled by default', () => {
            expect(DEFAULT_SETTINGS.enableExperimentalFeatures).toBe(false);
        });

        it('should have empty default customCss', () => {
            expect(DEFAULT_SETTINGS.customCss).toBe('');
        });

        it('should have correct settingsVersion', () => {
            expect(DEFAULT_SETTINGS.settingsVersion).toBe(2);
        });

        it('should have all required properties', () => {
            const requiredProps = [
                'claudeCodeUrl', 'apiKey', 'commandTimeout', 'retryCount',
                'enableCache', 'logLevel', 'dataPath', 'autoBackup',
                'backupInterval', 'backupRetentionDays', 'compressBackups',
                'autoSyncInterval', 'conflictResolution', 'theme', 'language',
                'fontScale', 'enableAnimations', 'showTooltips', 'compactMode',
                'defaultReviewDuration', 'reminderEnabled', 'reminderTime',
                'reminderDays', 'passingScore', 'enableSpacedRepetition',
                'difficultyWeight', 'debugMode', 'enablePerformanceMonitoring',
                'maxConcurrentOps', 'enableTelemetry', 'enableExperimentalFeatures',
                'customCss', 'settingsVersion'
            ];
            requiredProps.forEach(prop => {
                expect(DEFAULT_SETTINGS).toHaveProperty(prop);
            });
        });
    });

    describe('validateSettings', () => {
        describe('claudeCodeUrl validation', () => {
            it('should accept valid HTTP URL', () => {
                const result = validateSettings({ claudeCodeUrl: 'http://localhost:3005' });
                expect(result.isValid).toBe(true);
                expect(result.errors).toHaveLength(0);
            });

            it('should accept valid HTTPS URL', () => {
                const result = validateSettings({ claudeCodeUrl: 'https://api.example.com' });
                expect(result.isValid).toBe(true);
                expect(result.errors).toHaveLength(0);
            });

            it('should reject invalid URL', () => {
                const result = validateSettings({ claudeCodeUrl: 'not-a-valid-url' });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Claude Code URL must be a valid URL');
            });

            it('should warn on empty string URL', () => {
                const result = validateSettings({ claudeCodeUrl: '' });
                expect(result.isValid).toBe(true);
                expect(result.warnings).toContain('Claude Code URL is empty - API features will not work');
            });
        });

        describe('commandTimeout validation', () => {
            it('should accept valid timeout (5000ms)', () => {
                const result = validateSettings({ commandTimeout: 5000 });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid timeout (300000ms)', () => {
                const result = validateSettings({ commandTimeout: 300000 });
                expect(result.isValid).toBe(true);
            });

            it('should reject timeout less than 5000ms', () => {
                const result = validateSettings({ commandTimeout: 4999 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Command timeout must be between 5000ms and 300000ms');
            });

            it('should reject timeout greater than 300000ms', () => {
                const result = validateSettings({ commandTimeout: 300001 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Command timeout must be between 5000ms and 300000ms');
            });
        });

        describe('retryCount validation', () => {
            it('should accept valid retryCount (0)', () => {
                const result = validateSettings({ retryCount: 0 });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid retryCount (10)', () => {
                const result = validateSettings({ retryCount: 10 });
                expect(result.isValid).toBe(true);
            });

            it('should reject retryCount greater than 10', () => {
                const result = validateSettings({ retryCount: 11 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Retry count must be between 0 and 10');
            });

            it('should reject negative retryCount', () => {
                const result = validateSettings({ retryCount: -1 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Retry count must be between 0 and 10');
            });
        });

        describe('autoSyncInterval validation', () => {
            it('should accept valid interval (0 - disabled)', () => {
                const result = validateSettings({ autoSyncInterval: 0 });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid interval (60 minutes)', () => {
                const result = validateSettings({ autoSyncInterval: 60 });
                expect(result.isValid).toBe(true);
            });

            it('should reject interval greater than 60', () => {
                const result = validateSettings({ autoSyncInterval: 61 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Auto-sync interval must be between 0 and 60 minutes');
            });

            it('should reject negative interval', () => {
                const result = validateSettings({ autoSyncInterval: -5 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Auto-sync interval must be between 0 and 60 minutes');
            });
        });

        describe('backupInterval validation', () => {
            it('should accept valid interval (1 hour)', () => {
                const result = validateSettings({ backupInterval: 1 });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid interval (168 hours)', () => {
                const result = validateSettings({ backupInterval: 168 });
                expect(result.isValid).toBe(true);
            });

            it('should reject interval less than 1', () => {
                const result = validateSettings({ backupInterval: 0 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Backup interval must be between 1 and 168 hours');
            });

            it('should reject interval greater than 168', () => {
                const result = validateSettings({ backupInterval: 169 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Backup interval must be between 1 and 168 hours');
            });
        });

        describe('backupRetentionDays validation', () => {
            it('should accept valid retention (1 day)', () => {
                const result = validateSettings({ backupRetentionDays: 1 });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid retention (365 days)', () => {
                const result = validateSettings({ backupRetentionDays: 365 });
                expect(result.isValid).toBe(true);
            });

            it('should reject retention less than 1', () => {
                const result = validateSettings({ backupRetentionDays: 0 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Backup retention must be between 1 and 365 days');
            });

            it('should reject retention greater than 365', () => {
                const result = validateSettings({ backupRetentionDays: 366 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Backup retention must be between 1 and 365 days');
            });
        });

        describe('maxConcurrentOps validation', () => {
            it('should accept valid value (1)', () => {
                const result = validateSettings({ maxConcurrentOps: 1 });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid value (20)', () => {
                const result = validateSettings({ maxConcurrentOps: 20 });
                expect(result.isValid).toBe(true);
            });

            it('should reject value less than 1', () => {
                const result = validateSettings({ maxConcurrentOps: 0 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Max concurrent operations must be between 1 and 20');
            });

            it('should reject value greater than 20', () => {
                const result = validateSettings({ maxConcurrentOps: 21 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Max concurrent operations must be between 1 and 20');
            });
        });

        describe('fontScale validation', () => {
            it('should accept valid scale (0.5)', () => {
                const result = validateSettings({ fontScale: 0.5 });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid scale (2.0)', () => {
                const result = validateSettings({ fontScale: 2.0 });
                expect(result.isValid).toBe(true);
            });

            it('should reject scale less than 0.5', () => {
                const result = validateSettings({ fontScale: 0.4 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Font scale must be between 0.5 and 2.0');
            });

            it('should reject scale greater than 2.0', () => {
                const result = validateSettings({ fontScale: 2.1 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Font scale must be between 0.5 and 2.0');
            });
        });

        describe('passingScore validation', () => {
            it('should accept valid score (0)', () => {
                const result = validateSettings({ passingScore: 0 });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid score (100)', () => {
                const result = validateSettings({ passingScore: 100 });
                expect(result.isValid).toBe(true);
            });

            it('should reject score less than 0', () => {
                const result = validateSettings({ passingScore: -1 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Passing score must be between 0 and 100');
            });

            it('should reject score greater than 100', () => {
                const result = validateSettings({ passingScore: 101 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Passing score must be between 0 and 100');
            });
        });

        describe('difficultyWeight validation', () => {
            it('should accept valid weight (0.1)', () => {
                const result = validateSettings({ difficultyWeight: 0.1 });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid weight (5.0)', () => {
                const result = validateSettings({ difficultyWeight: 5.0 });
                expect(result.isValid).toBe(true);
            });

            it('should reject weight less than 0.1', () => {
                const result = validateSettings({ difficultyWeight: 0.05 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Difficulty weight must be between 0.1 and 5.0');
            });

            it('should reject weight greater than 5.0', () => {
                const result = validateSettings({ difficultyWeight: 5.1 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Difficulty weight must be between 0.1 and 5.0');
            });
        });

        describe('reminderTime validation', () => {
            it('should accept valid time format (09:00)', () => {
                const result = validateSettings({ reminderTime: '09:00' });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid time format (23:59)', () => {
                const result = validateSettings({ reminderTime: '23:59' });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid time format (0:00)', () => {
                const result = validateSettings({ reminderTime: '0:00' });
                expect(result.isValid).toBe(true);
            });

            it('should reject invalid time format', () => {
                const result = validateSettings({ reminderTime: '25:00' });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Reminder time must be in HH:MM format');
            });

            it('should reject invalid time format (no colon)', () => {
                const result = validateSettings({ reminderTime: '0900' });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Reminder time must be in HH:MM format');
            });
        });

        describe('defaultReviewDuration validation', () => {
            it('should accept valid duration (5 minutes)', () => {
                const result = validateSettings({ defaultReviewDuration: 5 });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid duration (180 minutes)', () => {
                const result = validateSettings({ defaultReviewDuration: 180 });
                expect(result.isValid).toBe(true);
            });

            it('should reject duration less than 5', () => {
                const result = validateSettings({ defaultReviewDuration: 4 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Default review duration must be between 5 and 180 minutes');
            });

            it('should reject duration greater than 180', () => {
                const result = validateSettings({ defaultReviewDuration: 181 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Default review duration must be between 5 and 180 minutes');
            });
        });

        describe('multiple validations', () => {
            it('should collect multiple errors', () => {
                const result = validateSettings({
                    claudeCodeUrl: 'invalid-url',
                    commandTimeout: 1000,
                    maxConcurrentOps: 100,
                    fontScale: 0.1,
                    passingScore: 200
                });
                expect(result.isValid).toBe(false);
                expect(result.errors.length).toBe(5);
            });

            it('should pass with all valid settings', () => {
                const result = validateSettings({
                    claudeCodeUrl: 'http://localhost:3005',
                    commandTimeout: 30000,
                    maxConcurrentOps: 5,
                    fontScale: 1.0,
                    passingScore: 60
                });
                expect(result.isValid).toBe(true);
                expect(result.errors).toHaveLength(0);
            });

            it('should pass with empty partial settings', () => {
                const result = validateSettings({});
                expect(result.isValid).toBe(true);
                expect(result.errors).toHaveLength(0);
            });
        });
    });

    describe('migrateSettings', () => {
        it('should migrate from version 1 to version 2', () => {
            const oldSettings = {
                claudeCodeUrl: 'http://old-url:3000',
                dataPath: '/old/path',
                autoSyncInterval: 10,
                enableCache: false,
                commandTimeout: 60000,
                theme: 'dark' as const,
                debugMode: true,
                maxConcurrentOps: 10,
                settingsVersion: 1
            };

            const migrated = migrateSettings(oldSettings);

            // Preserved old values
            expect(migrated.claudeCodeUrl).toBe('http://old-url:3000');
            expect(migrated.dataPath).toBe('/old/path');
            expect(migrated.autoSyncInterval).toBe(10);
            expect(migrated.enableCache).toBe(false);
            expect(migrated.commandTimeout).toBe(60000);
            expect(migrated.theme).toBe('dark');
            expect(migrated.debugMode).toBe(true);
            expect(migrated.maxConcurrentOps).toBe(10);

            // New defaults added
            expect(migrated.apiKey).toBe('');
            expect(migrated.retryCount).toBe(3);
            expect(migrated.logLevel).toBe('info');
            expect(migrated.backupInterval).toBe(24);
            expect(migrated.settingsVersion).toBe(2);
        });

        it('should use defaults for missing fields', () => {
            const partialSettings = {
                claudeCodeUrl: 'http://custom:8080'
            };

            const migrated = migrateSettings(partialSettings);

            expect(migrated.claudeCodeUrl).toBe('http://custom:8080');
            expect(migrated.dataPath).toBe('');
            expect(migrated.autoSyncInterval).toBe(5);
            expect(migrated.settingsVersion).toBe(2);
        });

        it('should not modify already version 2 settings', () => {
            const v2Settings = { ...DEFAULT_SETTINGS, settingsVersion: 2 };
            const migrated = migrateSettings(v2Settings);

            expect(migrated).toEqual(v2Settings);
        });
    });

    describe('exportSettings', () => {
        it('should export settings as JSON string', () => {
            const settings = { ...DEFAULT_SETTINGS };
            const exported = exportSettings(settings);

            expect(typeof exported).toBe('string');
            const parsed = JSON.parse(exported);
            expect(parsed.claudeCodeUrl).toBe(settings.claudeCodeUrl);
        });

        it('should include export metadata', () => {
            const settings = { ...DEFAULT_SETTINGS };
            const exported = exportSettings(settings);
            const parsed = JSON.parse(exported);

            expect(parsed).toHaveProperty('exportedAt');
            expect(parsed).toHaveProperty('exportVersion');
            expect(parsed.exportVersion).toBe(2);
        });

        it('should format JSON with indentation', () => {
            const settings = { ...DEFAULT_SETTINGS };
            const exported = exportSettings(settings);

            expect(exported).toContain('\n');
            expect(exported).toContain('  ');
        });
    });

    describe('importSettings', () => {
        it('should import valid settings JSON', () => {
            const settings = { ...DEFAULT_SETTINGS };
            const jsonString = JSON.stringify(settings);
            const imported = importSettings(jsonString);

            expect(imported.claudeCodeUrl).toBe(settings.claudeCodeUrl);
            expect(imported.settingsVersion).toBe(2);
        });

        it('should remove export metadata on import', () => {
            const exportedData = {
                ...DEFAULT_SETTINGS,
                exportedAt: '2024-01-01T00:00:00Z',
                exportVersion: 2
            };
            const jsonString = JSON.stringify(exportedData);
            const imported = importSettings(jsonString);

            expect(imported).not.toHaveProperty('exportedAt');
            expect(imported).not.toHaveProperty('exportVersion');
        });

        it('should throw error for invalid JSON', () => {
            expect(() => importSettings('not valid json')).toThrow('Invalid JSON format');
        });

        it('should throw error for invalid settings', () => {
            const invalidSettings = {
                claudeCodeUrl: 'not-a-url',
                commandTimeout: 1000
            };
            const jsonString = JSON.stringify(invalidSettings);

            expect(() => importSettings(jsonString)).toThrow('Invalid settings');
        });

        it('should migrate imported settings if needed', () => {
            const oldSettings = {
                claudeCodeUrl: 'http://localhost:3005',
                settingsVersion: 1
            };
            const jsonString = JSON.stringify(oldSettings);
            const imported = importSettings(jsonString);

            expect(imported.settingsVersion).toBe(2);
            expect(imported.apiKey).toBe('');
        });
    });

    describe('SETTINGS_SECTIONS', () => {
        it('should have 5 sections', () => {
            expect(SETTINGS_SECTIONS).toHaveLength(5);
        });

        it('should have connection section', () => {
            const connectionSection = SETTINGS_SECTIONS.find(s => s.id === 'connection');
            expect(connectionSection).toBeDefined();
            expect(connectionSection?.name).toBe('连接设置');
        });

        it('should have storage section', () => {
            const storageSection = SETTINGS_SECTIONS.find(s => s.id === 'storage');
            expect(storageSection).toBeDefined();
            expect(storageSection?.name).toBe('数据存储');
        });

        it('should have interface section', () => {
            const interfaceSection = SETTINGS_SECTIONS.find(s => s.id === 'interface');
            expect(interfaceSection).toBeDefined();
            expect(interfaceSection?.name).toBe('界面设置');
        });

        it('should have review section', () => {
            const reviewSection = SETTINGS_SECTIONS.find(s => s.id === 'review');
            expect(reviewSection).toBeDefined();
            expect(reviewSection?.name).toBe('复习偏好');
        });

        it('should have advanced section', () => {
            const advancedSection = SETTINGS_SECTIONS.find(s => s.id === 'advanced');
            expect(advancedSection).toBeDefined();
            expect(advancedSection?.name).toBe('高级设置');
        });

        it('should have required properties for each section', () => {
            SETTINGS_SECTIONS.forEach(section => {
                expect(section).toHaveProperty('id');
                expect(section).toHaveProperty('name');
                expect(section).toHaveProperty('description');
                expect(section).toHaveProperty('icon');
            });
        });
    });

    describe('Settings merge behavior', () => {
        it('should merge partial settings with defaults', () => {
            const partialSettings: Partial<PluginSettings> = {
                claudeCodeUrl: 'http://custom:8080',
                debugMode: true
            };

            const merged: PluginSettings = {
                ...DEFAULT_SETTINGS,
                ...partialSettings
            };

            expect(merged.claudeCodeUrl).toBe('http://custom:8080');
            expect(merged.debugMode).toBe(true);
            expect(merged.autoSyncInterval).toBe(DEFAULT_SETTINGS.autoSyncInterval);
            expect(merged.enableCache).toBe(DEFAULT_SETTINGS.enableCache);
        });

        it('should override all properties when full settings provided', () => {
            const fullSettings: PluginSettings = {
                ...DEFAULT_SETTINGS,
                claudeCodeUrl: 'https://api.example.com',
                dataPath: '/custom/path',
                autoSyncInterval: 10,
                enableCache: false,
                commandTimeout: 60000,
                theme: 'dark',
                debugMode: true,
                maxConcurrentOps: 8
            };

            const merged = { ...DEFAULT_SETTINGS, ...fullSettings };

            expect(merged.claudeCodeUrl).toBe('https://api.example.com');
            expect(merged.theme).toBe('dark');
            expect(merged.debugMode).toBe(true);
        });
    });
});
