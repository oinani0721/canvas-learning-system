/**
 * Association Config Service - Canvas Learning System Cross-Canvas Associations
 *
 * Service for managing .canvas-links.json configuration files.
 * Implements Story 16.2: .canvas-links.json配置管理
 *
 * @module AssociationConfigService
 * @version 1.0.0
 *
 * ✅ Verified from @obsidian-canvas Skill (Vault API, TFile, TFolder)
 * ✅ Verified from Story 16.2 Dev Notes (Config file structure)
 */

import { App, TFile, TFolder, Notice } from 'obsidian';
import type {
    CanvasAssociation,
    CanvasLinksConfig,
    CanvasLinksSettings,
    CanvasLinksMetadata
} from '../types/AssociationTypes';
import { DEFAULT_CANVAS_LINKS_CONFIG } from '../types/AssociationTypes';

/**
 * Config file constants
 */
const CONFIG_FILE_NAME = '.canvas-links.json';
const CONFIG_VERSION = '1.0.0';

/**
 * Service for managing .canvas-links.json configuration
 *
 * ✅ Verified from @obsidian-canvas Skill (Vault.read, Vault.modify, Vault.create)
 */
export class AssociationConfigService {
    private app: App;
    private configCache: Map<string, CanvasLinksConfig> = new Map();
    private dirtyFlags: Set<string> = new Set();

    /**
     * Creates a new AssociationConfigService
     *
     * @param app - Obsidian App instance
     */
    constructor(app: App) {
        this.app = app;
    }

    /**
     * Get the config file path for a Canvas file
     *
     * @param canvasPath - Path to the Canvas file
     * @returns Path to the .canvas-links.json file
     */
    getConfigPath(canvasPath: string): string {
        // Config file is in the same directory as the Canvas file
        const dir = canvasPath.substring(0, canvasPath.lastIndexOf('/'));
        return dir ? `${dir}/${CONFIG_FILE_NAME}` : CONFIG_FILE_NAME;
    }

    /**
     * Load configuration for a Canvas file
     *
     * ✅ Verified from @obsidian-canvas Skill (Vault.adapter.read)
     *
     * @param canvasPath - Path to the Canvas file
     * @returns Promise<CanvasLinksConfig>
     */
    async loadConfig(canvasPath: string): Promise<CanvasLinksConfig> {
        const configPath = this.getConfigPath(canvasPath);

        // Check cache first
        if (this.configCache.has(configPath) && !this.dirtyFlags.has(configPath)) {
            return this.configCache.get(configPath)!;
        }

        try {
            const configFile = this.app.vault.getAbstractFileByPath(configPath);

            if (configFile instanceof TFile) {
                const content = await this.app.vault.read(configFile);
                const config = JSON.parse(content) as CanvasLinksConfig;

                // Validate and migrate if needed
                const validatedConfig = this.validateAndMigrate(config);
                this.configCache.set(configPath, validatedConfig);
                this.dirtyFlags.delete(configPath);

                return validatedConfig;
            }
        } catch (error) {
            console.warn('[AssociationConfigService] Failed to load config, using defaults:', error);
        }

        // Return default config if file doesn't exist
        const defaultConfig = this.createDefaultConfig();
        this.configCache.set(configPath, defaultConfig);
        return defaultConfig;
    }

    /**
     * Save configuration for a Canvas file
     *
     * ✅ Verified from @obsidian-canvas Skill (Vault.modify, Vault.create)
     *
     * @param canvasPath - Path to the Canvas file
     * @param config - Configuration to save
     * @returns Promise<void>
     */
    async saveConfig(canvasPath: string, config: CanvasLinksConfig): Promise<void> {
        const configPath = this.getConfigPath(canvasPath);

        // Update metadata
        config.metadata = {
            created_at: config.metadata?.created_at || new Date().toISOString(),
            updated_at: new Date().toISOString(),
            update_count: (config.metadata?.update_count || 0) + 1
        };

        const content = JSON.stringify(config, null, 2);

        try {
            const existingFile = this.app.vault.getAbstractFileByPath(configPath);

            if (existingFile instanceof TFile) {
                await this.app.vault.modify(existingFile, content);
            } else {
                // Ensure directory exists
                await this.ensureDirectoryExists(configPath);
                await this.app.vault.create(configPath, content);
            }

            // Update cache
            this.configCache.set(configPath, config);
            this.dirtyFlags.delete(configPath);

        } catch (error) {
            console.error('[AssociationConfigService] Failed to save config:', error);
            throw new Error(`Failed to save config: ${(error as Error).message}`);
        }
    }

    /**
     * Get all associations for a Canvas file
     *
     * @param canvasPath - Path to the Canvas file
     * @returns Promise<CanvasAssociation[]>
     */
    async getAssociations(canvasPath: string): Promise<CanvasAssociation[]> {
        const config = await this.loadConfig(canvasPath);
        return config.associations.filter(a =>
            a.source_canvas === canvasPath || a.target_canvas === canvasPath
        );
    }

    /**
     * Get associations where this Canvas is the source
     *
     * @param canvasPath - Path to the Canvas file
     * @returns Promise<CanvasAssociation[]>
     */
    async getOutgoingAssociations(canvasPath: string): Promise<CanvasAssociation[]> {
        const config = await this.loadConfig(canvasPath);
        return config.associations.filter(a => a.source_canvas === canvasPath);
    }

    /**
     * Get associations where this Canvas is the target
     *
     * @param canvasPath - Path to the Canvas file
     * @returns Promise<CanvasAssociation[]>
     */
    async getIncomingAssociations(canvasPath: string): Promise<CanvasAssociation[]> {
        const config = await this.loadConfig(canvasPath);
        return config.associations.filter(a => a.target_canvas === canvasPath);
    }

    /**
     * Add a new association
     *
     * @param association - Association to add
     * @returns Promise<void>
     */
    async addAssociation(association: CanvasAssociation): Promise<void> {
        const config = await this.loadConfig(association.source_canvas);

        // Check for duplicates
        const exists = config.associations.some(a =>
            a.source_canvas === association.source_canvas &&
            a.target_canvas === association.target_canvas &&
            a.association_type === association.association_type
        );

        if (exists) {
            throw new Error('Association already exists');
        }

        config.associations.push(association);
        await this.saveConfig(association.source_canvas, config);

        // Handle bidirectional association
        if (association.bidirectional) {
            await this.addReverseAssociation(association);
        }
    }

    /**
     * Update an existing association
     *
     * @param association - Association to update
     * @returns Promise<void>
     */
    async updateAssociation(association: CanvasAssociation): Promise<void> {
        const config = await this.loadConfig(association.source_canvas);

        const index = config.associations.findIndex(a =>
            a.association_id === association.association_id
        );

        if (index === -1) {
            throw new Error('Association not found');
        }

        // Update the association
        association.updated_at = new Date().toISOString();
        config.associations[index] = association;

        await this.saveConfig(association.source_canvas, config);
    }

    /**
     * Delete an association
     *
     * @param associationId - ID of the association to delete
     * @param canvasPath - Path to the Canvas file containing the association
     * @returns Promise<void>
     */
    async deleteAssociation(associationId: string, canvasPath: string): Promise<void> {
        const config = await this.loadConfig(canvasPath);

        const index = config.associations.findIndex(a =>
            a.association_id === associationId
        );

        if (index === -1) {
            throw new Error('Association not found');
        }

        const association = config.associations[index];
        config.associations.splice(index, 1);

        await this.saveConfig(canvasPath, config);

        // Remove reverse association if bidirectional
        if (association.bidirectional) {
            await this.removeReverseAssociation(association);
        }
    }

    /**
     * Get association count for a Canvas
     *
     * @param canvasPath - Path to the Canvas file
     * @returns Promise<number>
     */
    async getAssociationCount(canvasPath: string): Promise<number> {
        const associations = await this.getAssociations(canvasPath);
        return associations.length;
    }

    /**
     * Get settings from config
     *
     * @param canvasPath - Path to any Canvas file (settings are shared per directory)
     * @returns Promise<CanvasLinksSettings>
     */
    async getSettings(canvasPath: string): Promise<CanvasLinksSettings> {
        const config = await this.loadConfig(canvasPath);
        return config.settings || {
            auto_detect: false,
            min_confidence: 0.6,
            auto_sync: true
        };
    }

    /**
     * Update settings
     *
     * @param canvasPath - Path to any Canvas file
     * @param settings - New settings
     * @returns Promise<void>
     */
    async updateSettings(canvasPath: string, settings: Partial<CanvasLinksSettings>): Promise<void> {
        const config = await this.loadConfig(canvasPath);
        config.settings = {
            auto_detect: config.settings?.auto_detect ?? true,
            min_confidence: config.settings?.min_confidence ?? 0.5,
            auto_sync: config.settings?.auto_sync ?? true,
            ...settings
        };
        await this.saveConfig(canvasPath, config);
    }

    /**
     * Clean orphaned associations (where target Canvas no longer exists)
     *
     * @param canvasPath - Path to the Canvas file
     * @returns Promise<number> - Number of orphans removed
     */
    async cleanOrphanedAssociations(canvasPath: string): Promise<number> {
        const config = await this.loadConfig(canvasPath);
        const originalCount = config.associations.length;

        // Filter out associations where target Canvas doesn't exist
        config.associations = config.associations.filter(a => {
            const targetFile = this.app.vault.getAbstractFileByPath(a.target_canvas);
            return targetFile instanceof TFile;
        });

        const removedCount = originalCount - config.associations.length;

        if (removedCount > 0) {
            await this.saveConfig(canvasPath, config);
        }

        return removedCount;
    }

    /**
     * Invalidate cache for a config path
     *
     * @param canvasPath - Path to the Canvas file
     */
    invalidateCache(canvasPath: string): void {
        const configPath = this.getConfigPath(canvasPath);
        this.dirtyFlags.add(configPath);
    }

    /**
     * Clear all caches
     */
    clearAllCaches(): void {
        this.configCache.clear();
        this.dirtyFlags.clear();
    }

    /**
     * Get all Canvas files that have associations with a given Canvas
     *
     * @param canvasPath - Path to the Canvas file
     * @returns Promise<string[]> - Array of Canvas paths
     */
    async getRelatedCanvasPaths(canvasPath: string): Promise<string[]> {
        const associations = await this.getAssociations(canvasPath);
        const paths = new Set<string>();

        associations.forEach(a => {
            if (a.source_canvas !== canvasPath) {
                paths.add(a.source_canvas);
            }
            if (a.target_canvas !== canvasPath) {
                paths.add(a.target_canvas);
            }
        });

        return Array.from(paths);
    }

    /**
     * Add reverse association for bidirectional links
     */
    private async addReverseAssociation(original: CanvasAssociation): Promise<void> {
        const reverseAssociation: CanvasAssociation = {
            ...original,
            association_id: this.generateUUID(),
            source_canvas: original.target_canvas,
            target_canvas: original.source_canvas,
            bidirectional: false, // Reverse is not marked bidirectional to avoid loops
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };

        const targetConfig = await this.loadConfig(original.target_canvas);

        // Check if reverse already exists
        const exists = targetConfig.associations.some(a =>
            a.source_canvas === reverseAssociation.source_canvas &&
            a.target_canvas === reverseAssociation.target_canvas &&
            a.association_type === reverseAssociation.association_type
        );

        if (!exists) {
            targetConfig.associations.push(reverseAssociation);
            await this.saveConfig(original.target_canvas, targetConfig);
        }
    }

    /**
     * Remove reverse association when original is deleted
     */
    private async removeReverseAssociation(original: CanvasAssociation): Promise<void> {
        try {
            const targetConfig = await this.loadConfig(original.target_canvas);

            targetConfig.associations = targetConfig.associations.filter(a =>
                !(a.source_canvas === original.target_canvas &&
                    a.target_canvas === original.source_canvas &&
                    a.association_type === original.association_type)
            );

            await this.saveConfig(original.target_canvas, targetConfig);
        } catch (error) {
            console.warn('[AssociationConfigService] Failed to remove reverse association:', error);
        }
    }

    /**
     * Ensure directory exists for config file
     */
    private async ensureDirectoryExists(filePath: string): Promise<void> {
        const dir = filePath.substring(0, filePath.lastIndexOf('/'));
        if (!dir) return;

        const folder = this.app.vault.getAbstractFileByPath(dir);
        if (!folder) {
            await this.app.vault.createFolder(dir);
        }
    }

    /**
     * Create default configuration
     */
    private createDefaultConfig(): CanvasLinksConfig {
        return {
            version: CONFIG_VERSION,
            associations: [],
            settings: {
                auto_detect: false,
                min_confidence: 0.6,
                auto_sync: true
            },
            metadata: {
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                update_count: 0
            }
        };
    }

    /**
     * Validate and migrate config to latest version
     */
    private validateAndMigrate(config: CanvasLinksConfig): CanvasLinksConfig {
        // Ensure required fields exist
        if (!config.version) {
            config.version = CONFIG_VERSION;
        }

        if (!Array.isArray(config.associations)) {
            config.associations = [];
        }

        if (!config.settings) {
            config.settings = {
                auto_detect: false,
                min_confidence: 0.6,
                auto_sync: true
            };
        }

        if (!config.metadata) {
            config.metadata = {
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                update_count: 0
            };
        }

        // Version migrations would go here
        // if (config.version === '0.9.0') { ... migrate to 1.0.0 ... }

        return config;
    }

    /**
     * Generate UUID v4
     */
    private generateUUID(): string {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
}
