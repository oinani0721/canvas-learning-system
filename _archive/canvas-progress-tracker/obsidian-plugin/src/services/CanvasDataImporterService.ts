/**
 * Canvas Data Importer Service - Canvas Learning System
 *
 * Scans vault for Canvas files and imports nodes as review records.
 * Implements P0 Task #2: CanvasDataImporter服务
 *
 * @module CanvasDataImporterService
 * @version 1.0.0
 *
 * Source: Plan - P0 Task #2: 实现CanvasDataImporter服务
 * Purpose: Solve "database empty" root cause for Dashboard showing 0 data
 */

import { App, Notice, TFile } from 'obsidian';
import type { DataManager } from '../database/DataManager';
import type { ReviewRecord, DifficultyLevel, ReviewStatus } from '../types/DataTypes';

/**
 * Canvas node structure from .canvas JSON file
 * Source: Obsidian Canvas format specification
 */
interface CanvasNode {
    id: string;
    type: 'text' | 'file' | 'link' | 'group';
    x: number;
    y: number;
    width: number;
    height: number;
    text?: string;
    file?: string;
    color?: string;  // Node color: "1"-"6" or hex color
}

/**
 * Canvas file structure
 */
interface CanvasData {
    nodes: CanvasNode[];
    edges: Array<{
        id: string;
        fromNode: string;
        toNode: string;
    }>;
}

/**
 * Import result for tracking
 */
export interface ImportResult {
    canvasPath: string;
    canvasTitle: string;
    totalNodes: number;
    importedNodes: number;
    skippedNodes: number;
    errors: string[];
}

/**
 * Import options
 */
export interface ImportOptions {
    /** Only import green nodes (color = "4") */
    greenNodesOnly?: boolean;
    /** Skip already imported nodes */
    skipExisting?: boolean;
    /** Show progress notices */
    showNotices?: boolean;
    /** Canvas path filter (glob pattern) */
    pathFilter?: string;
}

/**
 * Color mapping from Obsidian Canvas color codes
 * Source: Obsidian Canvas color specification
 */
const CANVAS_COLORS = {
    '1': 'red',      // 🔴 Red - Not understood
    '2': 'orange',   // 🟠 Orange
    '3': 'yellow',   // 🟡 Yellow - Personal understanding area
    '4': 'green',    // 🟢 Green - Mastered
    '5': 'cyan',     // 🔵 Cyan
    '6': 'purple',   // 🟣 Purple - Partial understanding
} as const;

/**
 * Canvas Data Importer Service
 *
 * Provides functionality to:
 * - Scan vault for Canvas files
 * - Parse Canvas JSON structure
 * - Extract nodes as review items
 * - Batch import to database
 *
 * ✅ Verified from Obsidian API documentation
 */
export class CanvasDataImporterService {
    private app: App;
    private dbManager: DataManager | null = null;

    constructor(app: App) {
        this.app = app;
    }

    /**
     * Set data manager (dependency injection)
     * Pattern from TodayReviewListService
     */
    setDataManager(dataManager: DataManager): void {
        this.dbManager = dataManager;
    }

    /**
     * Import all Canvas files from vault
     */
    async importAllCanvases(options: ImportOptions = {}): Promise<ImportResult[]> {
        if (!this.dbManager) {
            console.error('[CanvasDataImporter] Database manager not initialized');
            new Notice('❌ 数据库未初始化，无法导入Canvas数据');
            return [];
        }

        const results: ImportResult[] = [];
        const canvasFiles = this.getCanvasFiles(options.pathFilter);

        if (options.showNotices) {
            new Notice(`📁 发现 ${canvasFiles.length} 个Canvas文件，开始导入...`);
        }

        for (const file of canvasFiles) {
            try {
                const result = await this.importSingleCanvas(file, options);
                results.push(result);
            } catch (error) {
                console.error(`[CanvasDataImporter] Failed to import ${file.path}:`, error);
                results.push({
                    canvasPath: file.path,
                    canvasTitle: file.basename,
                    totalNodes: 0,
                    importedNodes: 0,
                    skippedNodes: 0,
                    errors: [(error as Error).message],
                });
            }
        }

        // Summary notice
        if (options.showNotices) {
            const totalImported = results.reduce((sum, r) => sum + r.importedNodes, 0);
            const totalErrors = results.reduce((sum, r) => sum + r.errors.length, 0);
            new Notice(
                `✅ 导入完成：${totalImported} 个节点\n` +
                `📊 ${results.length} 个Canvas文件\n` +
                (totalErrors > 0 ? `⚠️ ${totalErrors} 个错误` : '')
            );
        }

        return results;
    }

    /**
     * Import a single Canvas file
     */
    async importSingleCanvas(file: TFile, options: ImportOptions = {}): Promise<ImportResult> {
        const result: ImportResult = {
            canvasPath: file.path,
            canvasTitle: file.basename,
            totalNodes: 0,
            importedNodes: 0,
            skippedNodes: 0,
            errors: [],
        };

        if (!this.dbManager) {
            result.errors.push('Database manager not initialized');
            return result;
        }

        try {
            // Read and parse Canvas file
            const content = await this.app.vault.read(file);
            const canvasData: CanvasData = JSON.parse(content);

            if (!canvasData.nodes || !Array.isArray(canvasData.nodes)) {
                result.errors.push('Invalid Canvas format: no nodes array');
                return result;
            }

            result.totalNodes = canvasData.nodes.length;

            // Filter nodes based on options
            let nodesToImport = canvasData.nodes.filter(node =>
                node.type === 'text' && node.text && node.text.trim().length > 0
            );

            if (options.greenNodesOnly) {
                nodesToImport = nodesToImport.filter(node => node.color === '4');
            }

            // Check existing records if skipExisting is true
            const reviewRecordDAO = this.dbManager.getReviewRecordDAO();
            let existingNodeIds: Set<string> = new Set();

            if (options.skipExisting) {
                const existingRecords = await reviewRecordDAO.findByCanvasId(file.path);
                existingNodeIds = new Set(existingRecords.map(r => r.conceptId || ''));
            }

            // Prepare records for batch insert
            const recordsToCreate: Omit<ReviewRecord, 'id' | 'createdAt' | 'updatedAt'>[] = [];

            for (const node of nodesToImport) {
                // Skip if already exists
                if (options.skipExisting && existingNodeIds.has(node.id)) {
                    result.skippedNodes++;
                    continue;
                }

                const record = this.nodeToReviewRecord(file, node);
                recordsToCreate.push(record);
            }

            // Batch insert
            if (recordsToCreate.length > 0) {
                await reviewRecordDAO.createBatch(recordsToCreate);
                result.importedNodes = recordsToCreate.length;
            }

            result.skippedNodes = nodesToImport.length - recordsToCreate.length;

        } catch (error) {
            result.errors.push((error as Error).message);
        }

        return result;
    }

    /**
     * Convert Canvas node to ReviewRecord
     */
    private nodeToReviewRecord(
        file: TFile,
        node: CanvasNode
    ): Omit<ReviewRecord, 'id' | 'createdAt' | 'updatedAt'> {
        // Extract concept name from node text (first line or first 50 chars)
        const text = node.text || '';
        const firstLine = text.split('\n')[0].trim();
        const conceptName = firstLine.length > 50
            ? firstLine.substring(0, 47) + '...'
            : firstLine || `Node-${node.id}`;

        // Determine difficulty based on color
        const difficultyLevel = this.colorToDifficulty(node.color);

        // Determine initial status based on color
        const status = this.colorToStatus(node.color);

        // Calculate initial memory strength based on color
        const memoryStrength = this.colorToMemoryStrength(node.color);

        return {
            canvasId: file.path,
            canvasTitle: file.basename,
            conceptName: conceptName,
            conceptId: node.id,
            reviewDate: new Date(),
            reviewDuration: 0,  // Not reviewed yet
            memoryStrength: memoryStrength,
            retentionRate: memoryStrength,  // Initial retention = memory strength
            difficultyLevel: difficultyLevel,
            status: status,
            nextReviewDate: this.calculateNextReviewDate(memoryStrength),
        };
    }

    /**
     * Map Canvas color to difficulty level
     */
    private colorToDifficulty(color?: string): DifficultyLevel {
        switch (color) {
            case '4':  // Green - mastered
                return 'easy';
            case '6':  // Purple - partial understanding
                return 'medium';
            case '1':  // Red - not understood
            case '3':  // Yellow - needs work
            default:
                return 'hard';
        }
    }

    /**
     * Map Canvas color to review status
     */
    private colorToStatus(color?: string): ReviewStatus {
        switch (color) {
            case '4':  // Green - mastered, schedule for review
                return 'scheduled';
            case '6':  // Purple - partial, pending review
                return 'pending';
            case '1':  // Red - not understood
            case '3':  // Yellow
            default:
                return 'pending';
        }
    }

    /**
     * Map Canvas color to initial memory strength
     */
    private colorToMemoryStrength(color?: string): number {
        switch (color) {
            case '4':  // Green - mastered
                return 0.8;
            case '6':  // Purple - partial
                return 0.5;
            case '3':  // Yellow
                return 0.3;
            case '1':  // Red - not understood
            default:
                return 0.1;
        }
    }

    /**
     * Calculate next review date based on memory strength (Ebbinghaus curve)
     */
    private calculateNextReviewDate(memoryStrength: number): Date {
        // Days until next review based on memory strength
        // Higher strength = longer interval
        let intervalDays: number;

        if (memoryStrength >= 0.8) {
            intervalDays = 7;  // 1 week
        } else if (memoryStrength >= 0.6) {
            intervalDays = 3;  // 3 days
        } else if (memoryStrength >= 0.4) {
            intervalDays = 1;  // 1 day
        } else {
            intervalDays = 0;  // Today (immediate review)
        }

        const nextDate = new Date();
        nextDate.setDate(nextDate.getDate() + intervalDays);
        return nextDate;
    }

    /**
     * Get all Canvas files from vault
     */
    private getCanvasFiles(pathFilter?: string): TFile[] {
        const allFiles = this.app.vault.getFiles();
        let canvasFiles = allFiles.filter(file => file.extension === 'canvas');

        if (pathFilter) {
            // Simple glob-like filtering
            const pattern = pathFilter.replace(/\*/g, '.*');
            const regex = new RegExp(pattern);
            canvasFiles = canvasFiles.filter(file => regex.test(file.path));
        }

        return canvasFiles;
    }

    /**
     * Get import statistics for a Canvas
     */
    async getCanvasStats(canvasPath: string): Promise<{
        totalRecords: number;
        pendingCount: number;
        completedCount: number;
        averageScore: number | null;
    }> {
        if (!this.dbManager) {
            return { totalRecords: 0, pendingCount: 0, completedCount: 0, averageScore: null };
        }

        const reviewRecordDAO = this.dbManager.getReviewRecordDAO();
        const records = await reviewRecordDAO.findByCanvasId(canvasPath);

        const pendingCount = records.filter(r => r.status === 'pending' || r.status === 'scheduled').length;
        const completedCount = records.filter(r => r.status === 'completed').length;
        const averageScore = await reviewRecordDAO.getAverageScore(canvasPath);

        return {
            totalRecords: records.length,
            pendingCount,
            completedCount,
            averageScore,
        };
    }

    /**
     * Clear all imported data for a Canvas (for re-import)
     */
    async clearCanvasData(canvasPath: string): Promise<number> {
        if (!this.dbManager) {
            console.error('[CanvasDataImporter] Database manager not initialized');
            return 0;
        }

        const reviewRecordDAO = this.dbManager.getReviewRecordDAO();
        return await reviewRecordDAO.deleteByCanvasId(canvasPath);
    }

    /**
     * Quick import button handler - imports all green nodes from all Canvas files
     */
    async quickImport(): Promise<void> {
        new Notice('🔄 开始导入Canvas复习项...');

        const results = await this.importAllCanvases({
            greenNodesOnly: false,  // Import all nodes, not just green
            skipExisting: true,     // Skip already imported
            showNotices: true,
        });

        console.log('[CanvasDataImporter] Import results:', results);
    }
}
