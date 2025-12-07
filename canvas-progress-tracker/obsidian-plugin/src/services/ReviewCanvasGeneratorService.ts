/**
 * ReviewCanvasGeneratorService - Canvas Learning System
 *
 * Story 14.5: 一键生成检验白板 + 复习模式选择
 *
 * Provides one-click verification canvas generation with:
 * - Mode selection (fresh/targeted)
 * - Backend API integration
 * - Graphiti relationship storage
 * - Batch generation support
 * - Progress notifications
 *
 * @module ReviewCanvasGeneratorService
 * @version 1.0.0
 *
 * Source: Story 14.5 Dev Notes
 * API: POST /api/v1/review/generate
 */

import { App, Notice, TFile, requestUrl } from 'obsidian';
import {
    ReviewMode,
    ReviewModeSelectionService,
    ReviewModeSelectionResult,
} from './ReviewModeSelectionService';

/**
 * API request for generating verification canvas
 * [Source: backend/app/models/schemas.py - GenerateReviewRequest]
 */
export interface GenerateReviewRequest {
    source_canvas: string;
    node_ids?: string[];
    review_mode?: ReviewMode;
}

/**
 * API response for generated verification canvas
 * [Source: backend/app/models/schemas.py - GenerateReviewResponse]
 */
export interface GenerateReviewResponse {
    verification_canvas_name: string;
    node_count: int;
}

/**
 * Enhanced response with mode and relationship info
 */
export interface GenerationResult {
    success: boolean;
    sourceCanvas: string;
    generatedCanvas: string;
    nodeCount: number;
    mode: ReviewMode;
    graphitiRelationshipId?: string;
    generationTime: number;
    error?: string;
}

/**
 * Batch generation progress
 */
export interface BatchGenerationProgress {
    total: number;
    completed: number;
    current?: string;
    results: GenerationResult[];
    startTime: Date;
}

/**
 * Generator service settings
 */
export interface GeneratorSettings {
    apiBaseUrl: string;
    timeout: number;
    autoOpenGenerated: boolean;
    storeToGraphiti: boolean;
    defaultMode: ReviewMode;
    showProgressNotifications: boolean;
}

/**
 * Default settings
 */
export const DEFAULT_GENERATOR_SETTINGS: GeneratorSettings = {
    apiBaseUrl: 'http://localhost:8001/api/v1',
    timeout: 30000,
    autoOpenGenerated: true,
    storeToGraphiti: true,
    defaultMode: 'fresh',
    showProgressNotifications: true,
};

/**
 * ReviewCanvasGeneratorService
 *
 * Implements Story 14.5 requirements:
 * - AC 1: "生成检验白板" button in review dashboard
 * - AC 2: Support two review modes (fresh/targeted)
 * - AC 3: Call generate_review_canvas_file() function (via API)
 * - AC 4: Store relationship to Graphiti
 * - AC 5: Auto-open generated canvas
 * - AC 6: Batch generation support
 * - AC 7: Progress notifications
 */
export class ReviewCanvasGeneratorService {
    private app: App;
    private settings: GeneratorSettings;
    private modeSelectionService: ReviewModeSelectionService;
    private batchProgress: BatchGenerationProgress | null = null;

    constructor(
        app: App,
        modeService: ReviewModeSelectionService,
        settings: Partial<GeneratorSettings> = {}
    ) {
        this.app = app;
        this.modeSelectionService = modeService;
        this.settings = {
            ...DEFAULT_GENERATOR_SETTINGS,
            ...settings,
        };
    }

    /**
     * Get current settings
     */
    getSettings(): GeneratorSettings {
        return { ...this.settings };
    }

    /**
     * Update settings
     */
    updateSettings(settings: Partial<GeneratorSettings>): void {
        this.settings = {
            ...this.settings,
            ...settings,
        };
    }

    // =========================================================================
    // AC 1 & 2: Generate verification canvas with mode selection
    // =========================================================================

    /**
     * Generate verification canvas with mode selection dialog
     *
     * AC 1: "生成检验白板" button handler
     * AC 2: Support two review modes (fresh/targeted)
     *
     * @param sourceCanvasPath - Path to source canvas file
     * @param skipModeSelection - If true, use default mode without dialog
     * @returns Promise<GenerationResult>
     */
    async generateWithModeSelection(
        sourceCanvasPath: string,
        skipModeSelection: boolean = false
    ): Promise<GenerationResult> {
        const startTime = Date.now();

        try {
            // Determine review mode
            let mode: ReviewMode;

            if (skipModeSelection) {
                mode = this.modeSelectionService.getEffectiveMode();
            } else {
                const modeResult = await this.modeSelectionService.showModeSelectionModal();

                if (!modeResult.confirmed) {
                    return {
                        success: false,
                        sourceCanvas: sourceCanvasPath,
                        generatedCanvas: '',
                        nodeCount: 0,
                        mode: 'fresh',
                        generationTime: Date.now() - startTime,
                        error: 'User cancelled mode selection',
                    };
                }

                mode = modeResult.mode;
            }

            // Generate canvas with selected mode
            return await this.generateCanvas(sourceCanvasPath, mode);
        } catch (error) {
            return {
                success: false,
                sourceCanvas: sourceCanvasPath,
                generatedCanvas: '',
                nodeCount: 0,
                mode: 'fresh',
                generationTime: Date.now() - startTime,
                error: (error as Error).message,
            };
        }
    }

    /**
     * Generate verification canvas for a single source
     *
     * AC 3: Call generate_review_canvas_file() function (via API)
     * AC 4: Store relationship to Graphiti
     * AC 5: Auto-open generated canvas
     * AC 7: Progress notifications
     *
     * @param sourceCanvasPath - Path to source canvas file
     * @param mode - Review mode (fresh/targeted)
     * @param nodeIds - Optional specific node IDs to include
     * @returns Promise<GenerationResult>
     */
    async generateCanvas(
        sourceCanvasPath: string,
        mode: ReviewMode,
        nodeIds?: string[]
    ): Promise<GenerationResult> {
        const startTime = Date.now();

        try {
            // Show progress notification
            if (this.settings.showProgressNotifications) {
                new Notice(`正在生成检验白板 (${mode === 'fresh' ? '全新检验' : '针对性复习'})...`, 3000);
            }

            // AC 3: Call backend API
            const request: GenerateReviewRequest = {
                source_canvas: sourceCanvasPath,
                node_ids: nodeIds,
                review_mode: mode,
            };

            const response = await this.callGenerateAPI(request);

            // AC 4: Store relationship to Graphiti
            let graphitiRelationshipId: string | undefined;
            if (this.settings.storeToGraphiti) {
                graphitiRelationshipId = await this.storeGraphitiRelationship(
                    sourceCanvasPath,
                    response.verification_canvas_name,
                    mode
                );
            }

            // AC 5: Auto-open generated canvas
            if (this.settings.autoOpenGenerated) {
                await this.openGeneratedCanvas(response.verification_canvas_name);
            }

            // AC 7: Success notification
            if (this.settings.showProgressNotifications) {
                new Notice(
                    `✅ 检验白板已生成: ${response.verification_canvas_name}\n包含 ${response.node_count} 个检验节点`,
                    5000
                );
            }

            return {
                success: true,
                sourceCanvas: sourceCanvasPath,
                generatedCanvas: response.verification_canvas_name,
                nodeCount: response.node_count,
                mode,
                graphitiRelationshipId,
                generationTime: Date.now() - startTime,
            };
        } catch (error) {
            const errorMessage = (error as Error).message;

            if (this.settings.showProgressNotifications) {
                new Notice(`❌ 生成检验白板失败: ${errorMessage}`, 5000);
            }

            return {
                success: false,
                sourceCanvas: sourceCanvasPath,
                generatedCanvas: '',
                nodeCount: 0,
                mode,
                generationTime: Date.now() - startTime,
                error: errorMessage,
            };
        }
    }

    // =========================================================================
    // AC 6: Batch generation support
    // =========================================================================

    /**
     * Generate verification canvases for multiple sources (batch)
     *
     * AC 6: Batch generation support
     *
     * @param sourceCanvases - Array of source canvas paths
     * @param mode - Review mode for all canvases
     * @param onProgress - Optional progress callback
     * @returns Promise<GenerationResult[]>
     */
    async generateBatch(
        sourceCanvases: string[],
        mode: ReviewMode,
        onProgress?: (progress: BatchGenerationProgress) => void
    ): Promise<GenerationResult[]> {
        const results: GenerationResult[] = [];

        this.batchProgress = {
            total: sourceCanvases.length,
            completed: 0,
            results: [],
            startTime: new Date(),
        };

        if (this.settings.showProgressNotifications) {
            new Notice(`开始批量生成 ${sourceCanvases.length} 个检验白板...`, 3000);
        }

        for (const canvasPath of sourceCanvases) {
            this.batchProgress.current = canvasPath;

            const result = await this.generateCanvas(canvasPath, mode);
            results.push(result);

            this.batchProgress.completed++;
            this.batchProgress.results.push(result);

            if (onProgress) {
                onProgress({ ...this.batchProgress });
            }
        }

        // Batch complete notification
        if (this.settings.showProgressNotifications) {
            const successCount = results.filter((r) => r.success).length;
            const failCount = results.length - successCount;

            new Notice(
                `批量生成完成: ${successCount} 成功, ${failCount} 失败`,
                5000
            );
        }

        this.batchProgress = null;
        return results;
    }

    /**
     * Get current batch progress
     */
    getBatchProgress(): BatchGenerationProgress | null {
        return this.batchProgress ? { ...this.batchProgress } : null;
    }

    /**
     * Cancel ongoing batch generation
     */
    cancelBatch(): void {
        if (this.batchProgress) {
            this.batchProgress = null;
            new Notice('批量生成已取消', 3000);
        }
    }

    // =========================================================================
    // API Integration
    // =========================================================================

    /**
     * Call backend API to generate verification canvas
     *
     * [Source: backend/app/api/v1/endpoints/review.py - POST /generate]
     */
    private async callGenerateAPI(
        request: GenerateReviewRequest
    ): Promise<GenerateReviewResponse> {
        const url = `${this.settings.apiBaseUrl}/review/generate`;

        try {
            const response = await requestUrl({
                url,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
                throw: false,
            });

            if (response.status === 201) {
                return response.json;
            } else if (response.status === 404) {
                throw new Error(`Canvas not found: ${request.source_canvas}`);
            } else {
                throw new Error(`API error: ${response.status}`);
            }
        } catch (error) {
            if ((error as Error).message.includes('net::ERR')) {
                throw new Error('Backend server not available');
            }
            throw error;
        }
    }

    // =========================================================================
    // AC 4: Graphiti Integration
    // =========================================================================

    /**
     * Store generation relationship to Graphiti
     *
     * Stores: (review_canvas)-[:GENERATED_FROM]->(original_canvas)
     *
     * [Source: Story 14.5 Dev Notes - AC 4]
     */
    private async storeGraphitiRelationship(
        sourceCanvas: string,
        generatedCanvas: string,
        mode: ReviewMode
    ): Promise<string | undefined> {
        const url = `${this.settings.apiBaseUrl}/memory/graphiti/store`;

        try {
            const response = await requestUrl({
                url,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    source_name: generatedCanvas,
                    target_name: sourceCanvas,
                    relationship_type: 'GENERATED_FROM',
                    properties: {
                        mode,
                        generated_at: new Date().toISOString(),
                        generator: 'ReviewCanvasGeneratorService',
                    },
                }),
                throw: false,
            });

            if (response.status === 200 || response.status === 201) {
                return response.json?.relationship_id;
            }

            // Graphiti not available - not a critical error
            console.warn('Graphiti relationship storage failed:', response.status);
            return undefined;
        } catch (error) {
            // Graphiti integration is optional
            console.warn('Graphiti unavailable:', (error as Error).message);
            return undefined;
        }
    }

    // =========================================================================
    // AC 5: Canvas Management
    // =========================================================================

    /**
     * Open generated canvas in Obsidian
     */
    private async openGeneratedCanvas(canvasPath: string): Promise<void> {
        try {
            // Get the file from vault
            const file = this.app.vault.getAbstractFileByPath(canvasPath);

            if (file instanceof TFile) {
                await this.app.workspace.getLeaf().openFile(file);
            } else {
                // File might be in a subdirectory - try finding it
                const allFiles = this.app.vault.getFiles();
                const matchingFile = allFiles.find(
                    (f) => f.path.endsWith(canvasPath) || f.name === canvasPath
                );

                if (matchingFile) {
                    await this.app.workspace.getLeaf().openFile(matchingFile);
                } else {
                    console.warn(`Generated canvas not found in vault: ${canvasPath}`);
                }
            }
        } catch (error) {
            console.error('Failed to open generated canvas:', error);
        }
    }

    // =========================================================================
    // Quick Actions
    // =========================================================================

    /**
     * Generate fresh review canvas (quick action)
     */
    async generateFreshReview(sourceCanvasPath: string): Promise<GenerationResult> {
        return this.generateCanvas(sourceCanvasPath, 'fresh');
    }

    /**
     * Generate targeted review canvas (quick action)
     */
    async generateTargetedReview(
        sourceCanvasPath: string,
        weakNodeIds?: string[]
    ): Promise<GenerationResult> {
        return this.generateCanvas(sourceCanvasPath, 'targeted', weakNodeIds);
    }

    /**
     * Generate from current active canvas
     */
    async generateFromActiveCanvas(): Promise<GenerationResult | null> {
        const activeFile = this.app.workspace.getActiveFile();

        if (!activeFile || !activeFile.path.endsWith('.canvas')) {
            new Notice('请先打开一个Canvas文件', 3000);
            return null;
        }

        return this.generateWithModeSelection(activeFile.path);
    }

    // =========================================================================
    // UI Button Creator
    // =========================================================================

    /**
     * Create the "生成检验白板" button element
     *
     * AC 1: "生成检验白板" button in review dashboard
     */
    createGenerateButton(containerEl: HTMLElement, canvasPath: string): HTMLElement {
        const button = containerEl.createEl('button', {
            text: '🎯 生成检验白板',
            cls: 'review-canvas-generate-button mod-cta',
        });

        button.addEventListener('click', async () => {
            button.disabled = true;
            button.textContent = '⏳ 生成中...';

            try {
                await this.generateWithModeSelection(canvasPath);
            } finally {
                button.disabled = false;
                button.textContent = '🎯 生成检验白板';
            }
        });

        return button;
    }

    /**
     * Create quick mode buttons
     */
    createQuickModeButtons(containerEl: HTMLElement, canvasPath: string): HTMLElement {
        const container = containerEl.createDiv('review-canvas-quick-buttons');

        const freshButton = container.createEl('button', {
            text: '🔄 全新检验',
            cls: 'review-canvas-quick-button',
        });

        freshButton.addEventListener('click', async () => {
            freshButton.disabled = true;
            await this.generateFreshReview(canvasPath);
            freshButton.disabled = false;
        });

        const targetedButton = container.createEl('button', {
            text: '🎯 针对性复习',
            cls: 'review-canvas-quick-button',
        });

        targetedButton.addEventListener('click', async () => {
            targetedButton.disabled = true;
            await this.generateTargetedReview(canvasPath);
            targetedButton.disabled = false;
        });

        return container;
    }

    /**
     * Get CSS styles for the generator UI
     */
    getStyles(): string {
        return `
            .review-canvas-generate-button {
                padding: 12px 24px;
                font-size: 16px;
                font-weight: 600;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .review-canvas-generate-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }

            .review-canvas-generate-button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }

            .review-canvas-quick-buttons {
                display: flex;
                gap: 12px;
                margin-top: 12px;
            }

            .review-canvas-quick-button {
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                border: 1px solid var(--background-modifier-border);
                background: var(--background-secondary);
                transition: all 0.2s ease;
            }

            .review-canvas-quick-button:hover {
                background: var(--background-modifier-hover);
            }

            .review-canvas-quick-button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
        `;
    }
}

/**
 * Factory function
 */
export function createReviewCanvasGeneratorService(
    app: App,
    modeService: ReviewModeSelectionService,
    settings?: Partial<GeneratorSettings>
): ReviewCanvasGeneratorService {
    return new ReviewCanvasGeneratorService(app, modeService, settings);
}

/**
 * Type alias for number (TypeScript doesn't have int type)
 */
type int = number;
