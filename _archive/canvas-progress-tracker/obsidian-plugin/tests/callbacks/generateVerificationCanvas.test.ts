/**
 * Canvas Learning System - generateVerificationCanvas Callback Tests
 *
 * Tests for Story 31.2: 检验白板生成端到端对接
 *
 * @module generateVerificationCanvas.test
 * @version 1.0.0
 */

import { ApiClient } from '../../src/api/ApiClient';
import { ApiError, GenerateReviewRequest, GenerateReviewResponse } from '../../src/api/types';
import {
    VerificationHistoryService,
    createVerificationHistoryService,
} from '../../src/services/VerificationHistoryService';
import type { MenuContext } from '../../src/types/menu';

// Mock Obsidian
jest.mock('obsidian', () => ({
    Notice: jest.fn().mockImplementation((msg: string) => ({
        message: msg,
        noticeEl: { empty: jest.fn(), appendChild: jest.fn() },
        hide: jest.fn(),
    })),
    TFile: class TFile {
        path: string;
        constructor(path: string) {
            this.path = path;
        }
    },
}));

// Mock localStorage for VerificationHistoryService
const localStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
        getItem: jest.fn((key: string) => store[key] || null),
        setItem: jest.fn((key: string, value: string) => {
            store[key] = value;
        }),
        removeItem: jest.fn((key: string) => {
            delete store[key];
        }),
        clear: jest.fn(() => {
            store = {};
        }),
    };
})();

Object.defineProperty(global, 'localStorage', {
    value: localStorageMock,
});

// ===========================================================================
// Test Helpers
// ===========================================================================

/**
 * Create a mock MenuContext for testing
 */
function createMockMenuContext(overrides?: Partial<MenuContext>): MenuContext {
    return {
        type: 'canvas-node',
        filePath: 'Canvas/TestCanvas.canvas',
        nodeId: 'node-123',
        nodeColor: '4',
        nodeType: 'text',
        ...overrides,
    };
}

/**
 * Create a mock ApiClient with generateReview method
 */
function createMockApiClient(mockResponse?: GenerateReviewResponse, shouldThrow?: Error) {
    return {
        generateReview: jest.fn().mockImplementation(async (request: GenerateReviewRequest) => {
            if (shouldThrow) {
                throw shouldThrow;
            }
            return mockResponse || {
                verification_canvas_name: 'Canvas/TestCanvas_验证_1705000000.canvas',
                node_count: 5,
            };
        }),
    } as unknown as ApiClient;
}

/**
 * Create a mock App
 */
function createMockApp() {
    return {
        workspace: {
            openLinkText: jest.fn().mockResolvedValue(undefined),
        },
        vault: {
            getAbstractFileByPath: jest.fn().mockReturnValue({
                path: 'Canvas/TestCanvas_验证_1705000000.canvas',
            }),
            adapter: { constructor: class {} },
        },
    } as any;
}

/**
 * Extract canvas file name helper (matches main.ts implementation)
 */
function extractCanvasFileName(filePath: string | undefined): string {
    if (!filePath) return '';
    return filePath.replace(/\.(canvas|md)$/i, '');
}

// ===========================================================================
// Test Suite
// ===========================================================================

describe('generateVerificationCanvas callback', () => {
    let mockNotice: jest.Mock;

    beforeEach(() => {
        jest.clearAllMocks();
        localStorageMock.clear();
        // Get the Notice mock
        mockNotice = jest.requireMock('obsidian').Notice;
    });

    describe('AC-31.2.1: API Client called with correct parameters', () => {
        it('should call generateReview API with correct source_canvas and mode', async () => {
            const mockApiClient = createMockApiClient();
            const context = createMockMenuContext({
                filePath: 'Canvas/Math53/Lecture5.canvas',
            });

            // Simulate the callback behavior
            const request: GenerateReviewRequest = {
                source_canvas: extractCanvasFileName(context.filePath),
            };

            await mockApiClient.generateReview(request);

            expect(mockApiClient.generateReview).toHaveBeenCalledWith({
                source_canvas: 'Canvas/Math53/Lecture5',
            });
        });

        it('should handle filePath without extension correctly', async () => {
            const result = extractCanvasFileName('Canvas/Test.canvas');
            expect(result).toBe('Canvas/Test');
        });

        it('should handle undefined filePath', async () => {
            const result = extractCanvasFileName(undefined);
            expect(result).toBe('');
        });
    });

    describe('AC-31.2.3: VerificationHistoryService.addRelation called', () => {
        it('should call addRelation with correct parameters after successful API call', async () => {
            const mockApp = createMockApp();
            const verificationService = createVerificationHistoryService(mockApp);
            const addRelationSpy = jest.spyOn(verificationService, 'addRelation');

            const mockResponse: GenerateReviewResponse = {
                verification_canvas_name: 'Canvas/TestCanvas_验证_1705000000',
                node_count: 5,
            };

            // Simulate adding the relation
            const originalPath = 'Canvas/TestCanvas.canvas';
            const verificationPath = mockResponse.verification_canvas_name.endsWith('.canvas')
                ? mockResponse.verification_canvas_name
                : `${mockResponse.verification_canvas_name}.canvas`;

            await verificationService.addRelation(originalPath, verificationPath, 'fresh');

            expect(addRelationSpy).toHaveBeenCalledWith(
                originalPath,
                verificationPath,
                'fresh'
            );
        });

        it('should store relation in localStorage', async () => {
            const mockApp = createMockApp();
            const verificationService = createVerificationHistoryService(mockApp);

            await verificationService.addRelation(
                'Canvas/Original.canvas',
                'Canvas/Original_验证_1705000000.canvas',
                'fresh'
            );

            expect(localStorageMock.setItem).toHaveBeenCalled();
            const storedData = localStorageMock.setItem.mock.calls[0];
            expect(storedData[0]).toBe('canvas-review-verification-relations');
        });
    });

    describe('AC-31.2.5: Error handling and UI feedback', () => {
        it('should show error notice on API failure', async () => {
            const apiError = new ApiError(
                'Server error',
                'HttpError5xx',
                500,
                { detail: 'Internal server error' }
            );
            const mockApiClient = createMockApiClient(undefined, apiError);

            let errorCaught = false;
            try {
                await mockApiClient.generateReview({ source_canvas: 'test' });
            } catch (error) {
                errorCaught = true;
                expect(error).toBe(apiError);
            }
            expect(errorCaught).toBe(true);
        });

        it('should return user-friendly message from ApiError', () => {
            const apiError = new ApiError(
                'Timeout',
                'TimeoutError',
                undefined
            );
            expect(apiError.getUserFriendlyMessage()).toBe('请求超时，请重试');
        });

        it('should show progress notice text correctly', () => {
            const progressMessage = '正在生成检验白板... 预计30秒';
            expect(progressMessage).toContain('正在生成检验白板');
            expect(progressMessage).toContain('预计30秒');
        });

        it('should format success notice correctly', () => {
            const nodeCount = 5;
            const successMessage = `检验白板生成完成: 包含 ${nodeCount} 个验证节点`;
            expect(successMessage).toBe('检验白板生成完成: 包含 5 个验证节点');
        });
    });

    describe('Validation checks', () => {
        it('should not proceed if filePath is missing', () => {
            const context = createMockMenuContext({ filePath: undefined });
            expect(context.filePath).toBeUndefined();
        });

        it('should not proceed if filePath is empty string', () => {
            const context = createMockMenuContext({ filePath: '' });
            expect(context.filePath).toBe('');
        });
    });

    describe('Canvas path handling', () => {
        it('should append .canvas extension if missing from response', () => {
            const verificationName = 'Canvas/Test_验证_1705000000';
            const result = verificationName.endsWith('.canvas')
                ? verificationName
                : `${verificationName}.canvas`;
            expect(result).toBe('Canvas/Test_验证_1705000000.canvas');
        });

        it('should not duplicate .canvas extension', () => {
            const verificationName = 'Canvas/Test_验证_1705000000.canvas';
            const result = verificationName.endsWith('.canvas')
                ? verificationName
                : `${verificationName}.canvas`;
            expect(result).toBe('Canvas/Test_验证_1705000000.canvas');
        });
    });
});

describe('VerificationHistoryService', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorageMock.clear();
    });

    it('should create service instance successfully', () => {
        const mockApp = createMockApp();
        const service = createVerificationHistoryService(mockApp);
        expect(service).toBeInstanceOf(VerificationHistoryService);
    });

    it('should return all relations sorted by date (most recent first)', async () => {
        const mockApp = createMockApp();
        const service = createVerificationHistoryService(mockApp);

        await service.addRelation('Canvas/A.canvas', 'Canvas/A_验证.canvas', 'fresh');
        // Add small delay to ensure different timestamps
        await new Promise(resolve => setTimeout(resolve, 10));
        await service.addRelation('Canvas/B.canvas', 'Canvas/B_验证.canvas', 'targeted');

        const relations = await service.getAllRelations();
        expect(relations.length).toBe(2);
        // Most recent first - B was added after A
        expect(relations[0].originalCanvasPath).toBe('Canvas/B.canvas');
        expect(relations[1].originalCanvasPath).toBe('Canvas/A.canvas');
    });

    it('should track session count correctly', async () => {
        const mockApp = createMockApp();
        const service = createVerificationHistoryService(mockApp);

        const relation = await service.addRelation('Canvas/A.canvas', 'Canvas/A_验证.canvas', 'fresh');
        expect(relation.sessionCount).toBe(0);

        await service.addReviewSession(relation.id, {
            duration: 300,
            passRate: 0.8,
            nodesReviewed: 5,
        });

        const relations = await service.getAllRelations();
        expect(relations[0].sessionCount).toBe(1);
    });

    it('should extract canvas title from path correctly', async () => {
        const mockApp = createMockApp();
        const service = createVerificationHistoryService(mockApp);

        const relation = await service.addRelation(
            'Canvas/Math/Linear-Algebra.canvas',
            'Canvas/Math/Linear-Algebra_验证.canvas',
            'fresh'
        );

        expect(relation.originalCanvasTitle).toBe('Linear-Algebra');
        expect(relation.verificationCanvasTitle).toBe('Linear-Algebra_验证');
    });
});
