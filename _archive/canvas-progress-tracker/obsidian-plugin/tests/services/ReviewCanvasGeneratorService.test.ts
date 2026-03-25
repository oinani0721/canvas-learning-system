/**
 * ReviewCanvasGeneratorService Tests - Canvas Learning System
 *
 * Tests for Story 14.5: 一键生成检验白板 + 复习模式选择
 *
 * @module ReviewCanvasGeneratorService.test
 * @version 1.0.0
 */

import {
    ReviewCanvasGeneratorService,
    GeneratorSettings,
    DEFAULT_GENERATOR_SETTINGS,
    GenerateReviewRequest,
    GenerateReviewResponse,
    GenerationResult,
    BatchGenerationProgress,
    createReviewCanvasGeneratorService,
} from '../../src/services/ReviewCanvasGeneratorService';
import {
    ReviewModeSelectionService,
    ReviewModeSelectionResult,
} from '../../src/services/ReviewModeSelectionService';

// Mock requestUrl from Obsidian
const mockRequestUrl = jest.fn();

// Define MockTFile inside the factory to avoid hoisting issues
jest.mock('obsidian', () => {
    // Create a proper TFile class mock
    class MockTFile {
        path: string;
        name: string;
        constructor(path: string) {
            this.path = path;
            this.name = path.split('/').pop() || path;
        }
    }
    return {
        Notice: jest.fn().mockImplementation((message: string) => ({
            message,
            hide: jest.fn(),
        })),
        TFile: MockTFile,
        requestUrl: (...args: any[]) => mockRequestUrl(...args),
    };
});

// Re-export MockTFile for use in tests
const { TFile: MockTFile } = jest.requireMock('obsidian');

// Mock App
const mockVault = {
    getAbstractFileByPath: jest.fn(),
    getFiles: jest.fn().mockReturnValue([]),
};

const mockWorkspace = {
    getLeaf: jest.fn().mockReturnValue({
        openFile: jest.fn().mockResolvedValue(undefined),
    }),
    getActiveFile: jest.fn(),
};

const mockApp = {
    vault: mockVault,
    workspace: mockWorkspace,
} as any;

// Mock ReviewModeSelectionService
const mockModeService = {
    getEffectiveMode: jest.fn().mockReturnValue('fresh'),
    showModeSelectionModal: jest.fn(),
    setLastUsedMode: jest.fn(),
} as unknown as ReviewModeSelectionService;

describe('ReviewCanvasGeneratorService', () => {
    let service: ReviewCanvasGeneratorService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = new ReviewCanvasGeneratorService(mockApp, mockModeService);
    });

    describe('Constructor and Settings', () => {
        it('should create with default settings', () => {
            expect(service).toBeDefined();
            const settings = service.getSettings();
            expect(settings.apiBaseUrl).toBe('http://localhost:8000/api/v1');
            expect(settings.timeout).toBe(30000);
            expect(settings.autoOpenGenerated).toBe(true);
            expect(settings.storeToGraphiti).toBe(true);
            expect(settings.defaultMode).toBe('fresh');
            expect(settings.showProgressNotifications).toBe(true);
        });

        it('should merge custom settings with defaults', () => {
            const customService = new ReviewCanvasGeneratorService(mockApp, mockModeService, {
                apiBaseUrl: 'http://custom:9000/api',
                timeout: 15000,
            });

            const settings = customService.getSettings();
            expect(settings.apiBaseUrl).toBe('http://custom:9000/api');
            expect(settings.timeout).toBe(15000);
            expect(settings.autoOpenGenerated).toBe(true); // Default
        });

        it('should update settings', () => {
            service.updateSettings({ autoOpenGenerated: false });
            const settings = service.getSettings();
            expect(settings.autoOpenGenerated).toBe(false);
            expect(settings.storeToGraphiti).toBe(true); // Unchanged
        });
    });

    describe('Generate Canvas with Mode Selection (AC 1 & 2)', () => {
        const mockApiResponse: GenerateReviewResponse = {
            verification_canvas_name: 'test-检验白板-20250115.canvas',
            node_count: 10,
        };

        beforeEach(() => {
            mockRequestUrl.mockResolvedValue({
                status: 201,
                json: mockApiResponse,
            });
        });

        it('should generate canvas with mode selection dialog', async () => {
            const mockModeResult: ReviewModeSelectionResult = {
                mode: 'fresh',
                confirmed: true,
                rememberChoice: false,
            };
            (mockModeService.showModeSelectionModal as jest.Mock).mockResolvedValue(mockModeResult);

            const result = await service.generateWithModeSelection('test.canvas');

            expect(mockModeService.showModeSelectionModal).toHaveBeenCalled();
            expect(result.success).toBe(true);
            expect(result.mode).toBe('fresh');
        });

        it('should skip mode selection when requested', async () => {
            (mockModeService.getEffectiveMode as jest.Mock).mockReturnValue('targeted');

            const result = await service.generateWithModeSelection('test.canvas', true);

            expect(mockModeService.showModeSelectionModal).not.toHaveBeenCalled();
            expect(mockModeService.getEffectiveMode).toHaveBeenCalled();
            expect(result.mode).toBe('targeted');
        });

        it('should return error when user cancels mode selection', async () => {
            const mockModeResult: ReviewModeSelectionResult = {
                mode: 'fresh',
                confirmed: false,
                rememberChoice: false,
            };
            (mockModeService.showModeSelectionModal as jest.Mock).mockResolvedValue(mockModeResult);

            const result = await service.generateWithModeSelection('test.canvas');

            expect(result.success).toBe(false);
            expect(result.error).toBe('User cancelled mode selection');
        });
    });

    describe('Generate Canvas (AC 3, 4, 5, 7)', () => {
        const mockApiResponse: GenerateReviewResponse = {
            verification_canvas_name: 'test-检验白板-20250115.canvas',
            node_count: 10,
        };

        beforeEach(() => {
            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/review/generate')) {
                    return Promise.resolve({
                        status: 201,
                        json: mockApiResponse,
                    });
                }
                if (options.url.includes('/memory/graphiti/store')) {
                    return Promise.resolve({
                        status: 200,
                        json: { relationship_id: 'rel-123' },
                    });
                }
                return Promise.resolve({ status: 404, json: {} });
            });
        });

        it('should call backend API to generate canvas (AC 3)', async () => {
            const result = await service.generateCanvas('test.canvas', 'fresh');

            expect(mockRequestUrl).toHaveBeenCalledWith(
                expect.objectContaining({
                    url: expect.stringContaining('/review/generate'),
                    method: 'POST',
                })
            );
            expect(result.success).toBe(true);
            expect(result.generatedCanvas).toBe('test-检验白板-20250115.canvas');
            expect(result.nodeCount).toBe(10);
        });

        it('should include node_ids in API request when provided', async () => {
            await service.generateCanvas('test.canvas', 'targeted', ['node1', 'node2']);

            expect(mockRequestUrl).toHaveBeenCalledWith(
                expect.objectContaining({
                    body: expect.stringContaining('node1'),
                })
            );
        });

        it('should store relationship to Graphiti (AC 4)', async () => {
            const result = await service.generateCanvas('test.canvas', 'fresh');

            expect(mockRequestUrl).toHaveBeenCalledWith(
                expect.objectContaining({
                    url: expect.stringContaining('/memory/graphiti/store'),
                    method: 'POST',
                })
            );
            expect(result.graphitiRelationshipId).toBe('rel-123');
        });

        it('should skip Graphiti when disabled in settings', async () => {
            service.updateSettings({ storeToGraphiti: false });

            const result = await service.generateCanvas('test.canvas', 'fresh');

            expect(mockRequestUrl).not.toHaveBeenCalledWith(
                expect.objectContaining({
                    url: expect.stringContaining('/memory/graphiti/store'),
                })
            );
            expect(result.graphitiRelationshipId).toBeUndefined();
        });

        it('should handle Graphiti failure gracefully', async () => {
            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/review/generate')) {
                    return Promise.resolve({
                        status: 201,
                        json: mockApiResponse,
                    });
                }
                if (options.url.includes('/memory/graphiti/store')) {
                    return Promise.reject(new Error('Graphiti unavailable'));
                }
                return Promise.resolve({ status: 404, json: {} });
            });

            const result = await service.generateCanvas('test.canvas', 'fresh');

            // Should still succeed even if Graphiti fails
            expect(result.success).toBe(true);
            expect(result.graphitiRelationshipId).toBeUndefined();
        });

        it('should auto-open generated canvas (AC 5)', async () => {
            // Use MockTFile instance so instanceof check passes
            const mockFile = new MockTFile('test-检验白板-20250115.canvas');
            mockVault.getAbstractFileByPath.mockReturnValue(mockFile);

            await service.generateCanvas('test.canvas', 'fresh');

            expect(mockVault.getAbstractFileByPath).toHaveBeenCalled();
            expect(mockWorkspace.getLeaf).toHaveBeenCalled();
        });

        it('should track generation time', async () => {
            const result = await service.generateCanvas('test.canvas', 'fresh');

            expect(result.generationTime).toBeGreaterThanOrEqual(0);
        });

        it('should handle API errors', async () => {
            mockRequestUrl.mockResolvedValue({
                status: 500,
                json: { error: 'Internal server error' },
            });

            const result = await service.generateCanvas('test.canvas', 'fresh');

            expect(result.success).toBe(false);
            expect(result.error).toBe('API error: 500');
        });

        it('should handle canvas not found error', async () => {
            mockRequestUrl.mockResolvedValue({
                status: 404,
                json: {},
            });

            const result = await service.generateCanvas('nonexistent.canvas', 'fresh');

            expect(result.success).toBe(false);
            expect(result.error).toBe('Canvas not found: nonexistent.canvas');
        });

        it('should handle network errors', async () => {
            mockRequestUrl.mockRejectedValue(new Error('net::ERR_CONNECTION_REFUSED'));

            const result = await service.generateCanvas('test.canvas', 'fresh');

            expect(result.success).toBe(false);
            expect(result.error).toBe('Backend server not available');
        });
    });

    describe('Batch Generation (AC 6)', () => {
        const mockApiResponse: GenerateReviewResponse = {
            verification_canvas_name: 'test-检验白板.canvas',
            node_count: 5,
        };

        beforeEach(() => {
            mockRequestUrl.mockResolvedValue({
                status: 201,
                json: mockApiResponse,
            });
        });

        it('should generate multiple canvases in batch', async () => {
            const canvases = ['canvas1.canvas', 'canvas2.canvas', 'canvas3.canvas'];

            const results = await service.generateBatch(canvases, 'fresh');

            expect(results).toHaveLength(3);
            expect(results.every((r) => r.success)).toBe(true);
        });

        it('should report progress during batch generation', async () => {
            const canvases = ['canvas1.canvas', 'canvas2.canvas'];
            const progressCallback = jest.fn();

            await service.generateBatch(canvases, 'targeted', progressCallback);

            expect(progressCallback).toHaveBeenCalledTimes(2);
            expect(progressCallback).toHaveBeenLastCalledWith(
                expect.objectContaining({
                    total: 2,
                    completed: 2,
                })
            );
        });

        it('should track batch progress', async () => {
            // Start batch but check progress mid-way
            const canvases = ['canvas1.canvas'];

            // Before batch
            expect(service.getBatchProgress()).toBeNull();

            // After batch completes
            await service.generateBatch(canvases, 'fresh');
            expect(service.getBatchProgress()).toBeNull(); // Cleared after completion
        });

        it('should cancel batch generation', () => {
            service.cancelBatch();
            // Should not throw and should clear progress
            expect(service.getBatchProgress()).toBeNull();
        });

        it('should continue batch even if one fails', async () => {
            // Disable Graphiti to simplify API call counting
            // (each canvas would make 2 calls: generate + graphiti)
            service.updateSettings({ storeToGraphiti: false });

            let generateCallCount = 0;
            mockRequestUrl.mockImplementation((options: any) => {
                if (options.url.includes('/review/generate')) {
                    generateCallCount++;
                    if (generateCallCount === 2) {
                        // Fail the second canvas generation
                        return Promise.resolve({ status: 500, json: {} });
                    }
                    return Promise.resolve({
                        status: 201,
                        json: mockApiResponse,
                    });
                }
                return Promise.resolve({ status: 404, json: {} });
            });

            const canvases = ['canvas1.canvas', 'canvas2.canvas', 'canvas3.canvas'];
            const results = await service.generateBatch(canvases, 'fresh');

            expect(results).toHaveLength(3);
            expect(results[0].success).toBe(true);
            expect(results[1].success).toBe(false);
            expect(results[2].success).toBe(true);
        });
    });

    describe('Quick Actions', () => {
        const mockApiResponse: GenerateReviewResponse = {
            verification_canvas_name: 'test-检验白板.canvas',
            node_count: 5,
        };

        beforeEach(() => {
            mockRequestUrl.mockResolvedValue({
                status: 201,
                json: mockApiResponse,
            });
        });

        it('should generate fresh review canvas', async () => {
            const result = await service.generateFreshReview('test.canvas');

            expect(result.mode).toBe('fresh');
            expect(result.success).toBe(true);
        });

        it('should generate targeted review canvas', async () => {
            const result = await service.generateTargetedReview('test.canvas');

            expect(result.mode).toBe('targeted');
            expect(result.success).toBe(true);
        });

        it('should generate targeted review with specific node IDs', async () => {
            await service.generateTargetedReview('test.canvas', ['weak1', 'weak2']);

            expect(mockRequestUrl).toHaveBeenCalledWith(
                expect.objectContaining({
                    body: expect.stringContaining('weak1'),
                })
            );
        });

        it('should generate from active canvas', async () => {
            const mockFile = { path: 'active.canvas' };
            mockWorkspace.getActiveFile.mockReturnValue(mockFile);
            (mockModeService.showModeSelectionModal as jest.Mock).mockResolvedValue({
                mode: 'fresh',
                confirmed: true,
                rememberChoice: false,
            });

            const result = await service.generateFromActiveCanvas();

            expect(result).not.toBeNull();
            expect(result?.sourceCanvas).toBe('active.canvas');
        });

        it('should return null when no active canvas', async () => {
            mockWorkspace.getActiveFile.mockReturnValue(null);

            const result = await service.generateFromActiveCanvas();

            expect(result).toBeNull();
        });

        it('should return null when active file is not a canvas', async () => {
            const mockFile = { path: 'document.md' };
            mockWorkspace.getActiveFile.mockReturnValue(mockFile);

            const result = await service.generateFromActiveCanvas();

            expect(result).toBeNull();
        });
    });

    describe('UI Button Creation', () => {
        it('should create generate button', () => {
            const container = {
                createEl: jest.fn().mockReturnValue({
                    addEventListener: jest.fn(),
                }),
            } as any;

            const button = service.createGenerateButton(container, 'test.canvas');

            expect(container.createEl).toHaveBeenCalledWith('button', {
                text: '🎯 生成检验白板',
                cls: 'review-canvas-generate-button mod-cta',
            });
        });

        it('should create quick mode buttons', () => {
            const container = {
                createDiv: jest.fn().mockReturnValue({
                    createEl: jest.fn().mockReturnValue({
                        addEventListener: jest.fn(),
                    }),
                }),
            } as any;

            const buttons = service.createQuickModeButtons(container, 'test.canvas');

            expect(container.createDiv).toHaveBeenCalledWith('review-canvas-quick-buttons');
        });

        it('should return CSS styles', () => {
            const styles = service.getStyles();

            expect(styles).toContain('.review-canvas-generate-button');
            expect(styles).toContain('.review-canvas-quick-buttons');
            expect(styles).toContain('.review-canvas-quick-button');
        });
    });
});

describe('DEFAULT_GENERATOR_SETTINGS', () => {
    it('should have correct default values', () => {
        expect(DEFAULT_GENERATOR_SETTINGS.apiBaseUrl).toBe('http://localhost:8000/api/v1');
        expect(DEFAULT_GENERATOR_SETTINGS.timeout).toBe(30000);
        expect(DEFAULT_GENERATOR_SETTINGS.autoOpenGenerated).toBe(true);
        expect(DEFAULT_GENERATOR_SETTINGS.storeToGraphiti).toBe(true);
        expect(DEFAULT_GENERATOR_SETTINGS.defaultMode).toBe('fresh');
        expect(DEFAULT_GENERATOR_SETTINGS.showProgressNotifications).toBe(true);
    });
});

describe('createReviewCanvasGeneratorService', () => {
    it('should create service instance', () => {
        const service = createReviewCanvasGeneratorService(mockApp, mockModeService);
        expect(service).toBeInstanceOf(ReviewCanvasGeneratorService);
    });

    it('should create service with custom settings', () => {
        const service = createReviewCanvasGeneratorService(mockApp, mockModeService, {
            apiBaseUrl: 'http://custom:8080',
        });

        expect(service.getSettings().apiBaseUrl).toBe('http://custom:8080');
    });
});
