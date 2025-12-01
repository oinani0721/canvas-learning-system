/**
 * Canvas Review System - Settings Tests
 *
 * Tests for the settings module including:
 * - Default settings values
 * - Settings validation
 * - Settings merge behavior
 *
 * @module tests/settings
 * @version 1.0.0
 */

import {
    PluginSettings,
    DEFAULT_SETTINGS,
    validateSettings,
    SettingsValidationResult
} from '../src/types/settings';

describe('PluginSettings', () => {
    describe('DEFAULT_SETTINGS', () => {
        it('should have correct default claudeCodeUrl', () => {
            expect(DEFAULT_SETTINGS.claudeCodeUrl).toBe('http://localhost:3005');
        });

        it('should have empty default dataPath', () => {
            expect(DEFAULT_SETTINGS.dataPath).toBe('');
        });

        it('should have correct default autoSyncInterval', () => {
            expect(DEFAULT_SETTINGS.autoSyncInterval).toBe(5);
        });

        it('should have enableCache enabled by default', () => {
            expect(DEFAULT_SETTINGS.enableCache).toBe(true);
        });

        it('should have correct default commandTimeout', () => {
            expect(DEFAULT_SETTINGS.commandTimeout).toBe(30000);
        });

        it('should have auto theme by default', () => {
            expect(DEFAULT_SETTINGS.theme).toBe('auto');
        });

        it('should have debugMode disabled by default', () => {
            expect(DEFAULT_SETTINGS.debugMode).toBe(false);
        });

        it('should have correct default maxConcurrentOps', () => {
            expect(DEFAULT_SETTINGS.maxConcurrentOps).toBe(5);
        });

        it('should have all required properties', () => {
            const requiredProps = [
                'claudeCodeUrl',
                'dataPath',
                'autoSyncInterval',
                'enableCache',
                'commandTimeout',
                'theme',
                'debugMode',
                'maxConcurrentOps'
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

            it('should reject empty string URL', () => {
                const result = validateSettings({ claudeCodeUrl: '' });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Claude Code URL must be a valid URL');
            });
        });

        describe('autoSyncInterval validation', () => {
            it('should accept valid interval (1 minute)', () => {
                const result = validateSettings({ autoSyncInterval: 1 });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid interval (60 minutes)', () => {
                const result = validateSettings({ autoSyncInterval: 60 });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid interval (30 minutes)', () => {
                const result = validateSettings({ autoSyncInterval: 30 });
                expect(result.isValid).toBe(true);
            });

            it('should reject interval less than 1', () => {
                const result = validateSettings({ autoSyncInterval: 0 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Auto-sync interval must be between 1 and 60 minutes');
            });

            it('should reject interval greater than 60', () => {
                const result = validateSettings({ autoSyncInterval: 61 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Auto-sync interval must be between 1 and 60 minutes');
            });

            it('should reject negative interval', () => {
                const result = validateSettings({ autoSyncInterval: -5 });
                expect(result.isValid).toBe(false);
                expect(result.errors).toContain('Auto-sync interval must be between 1 and 60 minutes');
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

            it('should accept valid timeout (30000ms)', () => {
                const result = validateSettings({ commandTimeout: 30000 });
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

        describe('maxConcurrentOps validation', () => {
            it('should accept valid value (1)', () => {
                const result = validateSettings({ maxConcurrentOps: 1 });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid value (20)', () => {
                const result = validateSettings({ maxConcurrentOps: 20 });
                expect(result.isValid).toBe(true);
            });

            it('should accept valid value (10)', () => {
                const result = validateSettings({ maxConcurrentOps: 10 });
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

        describe('multiple validations', () => {
            it('should collect multiple errors', () => {
                const result = validateSettings({
                    claudeCodeUrl: 'invalid-url',
                    autoSyncInterval: 0,
                    commandTimeout: 1000,
                    maxConcurrentOps: 100
                });
                expect(result.isValid).toBe(false);
                expect(result.errors.length).toBe(4);
            });

            it('should pass with all valid settings', () => {
                const result = validateSettings({
                    claudeCodeUrl: 'http://localhost:3005',
                    autoSyncInterval: 5,
                    commandTimeout: 30000,
                    maxConcurrentOps: 5
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

            expect(merged).toEqual(fullSettings);
        });
    });
});
