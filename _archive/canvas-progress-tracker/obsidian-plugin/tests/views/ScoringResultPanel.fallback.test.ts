/**
 * ScoringResultPanel Fallback Indicator Tests
 *
 * Story 31.8: 推荐降级模式 UI 指示器
 * Tests that the fallback indicator correctly appears/disappears
 * based on API availability, and that retry functionality works.
 *
 * @source Story 31.8 - AC-31.8.1, AC-31.8.2, AC-31.8.3, AC-31.8.4, AC-31.8.8
 * @jest-environment jsdom
 */

import { App, Notice } from 'obsidian';
import {
    ScoringResultPanel,
    ScoringResultItem,
    ScoringResultCallbacks,
} from '../../src/views/ScoringResultPanel';
import { ApiClient } from '../../src/api/ApiClient';
import { RecommendActionResponse } from '../../src/api/types';

// ===========================================================================
// Obsidian DOM Helper
// ===========================================================================

function addObsidianMethods(el: HTMLElement): HTMLElement {
    (el as any).empty = function () {
        while (this.firstChild) {
            this.removeChild(this.firstChild);
        }
    };
    (el as any).addClass = function (cls: string) {
        this.classList.add(cls);
    };
    (el as any).removeClass = function (cls: string) {
        this.classList.remove(cls);
    };
    (el as any).createEl = function (
        tag: string,
        options?: { cls?: string; text?: string; type?: string }
    ) {
        const child = document.createElement(tag);
        if (options?.cls) child.className = options.cls;
        if (options?.text) child.textContent = options.text;
        if (options?.type) (child as HTMLInputElement).type = options.type;
        addObsidianMethods(child);
        this.appendChild(child);
        return child;
    };
    return el;
}

// ===========================================================================
// Mock Obsidian Module
// ===========================================================================

jest.mock('obsidian', () => ({
    App: jest.fn(),
    Modal: class MockModal {
        app: any;
        containerEl: HTMLDivElement;
        modalEl: HTMLDivElement;
        contentEl: HTMLDivElement;
        titleEl: HTMLDivElement;

        constructor(app: any) {
            this.app = app;
            this.containerEl = document.createElement('div');
            this.modalEl = document.createElement('div');
            this.contentEl = document.createElement('div');
            this.titleEl = document.createElement('div');

            [this.containerEl, this.modalEl, this.contentEl, this.titleEl].forEach(
                (el: any) => {
                    addObsidianMethods(el);
                }
            );

            this.containerEl.appendChild(this.modalEl);
            this.modalEl.appendChild(this.titleEl);
            this.modalEl.appendChild(this.contentEl);
        }

        open() {}
        close() {}
        onOpen() {}
        onClose() {}
    },
    Notice: jest.fn(),
}));

// ===========================================================================
// Mock ApiClient
// ===========================================================================

jest.mock('../../src/api/ApiClient', () => ({
    ApiClient: jest.fn().mockImplementation(() => ({
        recommendAction: jest.fn(),
        decomposeBasic: jest.fn(),
        explainOral: jest.fn(),
        explainClarification: jest.fn(),
        explainMemory: jest.fn(),
        recordLearningEvent: jest.fn(),
    })),
}));

// ===========================================================================
// Test Helpers
// ===========================================================================

function createMockApp(): App {
    return {} as App;
}

function createMockApiClient(): ApiClient {
    return new ApiClient({} as any) as jest.Mocked<ApiClient>;
}

function createMockResult(overrides?: Partial<ScoringResultItem>): ScoringResultItem {
    return {
        nodeId: 'test-node-001',
        nodeText: '测试概念节点',
        score: {
            accuracy: 20,
            imagery: 18,
            completeness: 20,
            originality: 17,
            total: 75,
        },
        canvasName: '测试Canvas',
        ...overrides,
    };
}

function createMockCallbacks(): ScoringResultCallbacks {
    return {
        onClose: jest.fn(),
        onAgentAction: jest.fn(),
        onNextNode: jest.fn(),
    };
}

function createMockRecommendation(
    overrides?: Partial<RecommendActionResponse>
): RecommendActionResponse {
    return {
        action: 'explain',
        agent: 'oral-explanation',
        reason: '基于历史成绩建议补充解释',
        priority: 1,
        review_suggested: false,
        ...overrides,
    };
}

/** Wait for async operations to complete */
function waitForAsync(ms: number = 50): Promise<void> {
    return new Promise((r) => setTimeout(r, ms));
}

// ===========================================================================
// Story 31.8 Test Suites
// ===========================================================================

describe('Story 31.8: Fallback Indicator UI', () => {
    let app: App;
    let apiClient: jest.Mocked<ApiClient>;
    let callbacks: ScoringResultCallbacks;
    let consoleWarnSpy: jest.SpyInstance;

    beforeEach(() => {
        jest.clearAllMocks();
        app = createMockApp();
        apiClient = createMockApiClient() as jest.Mocked<ApiClient>;
        callbacks = createMockCallbacks();
        consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
    });

    afterEach(() => {
        consoleWarnSpy.mockRestore();
    });

    // ===================================================================
    // AC-31.8.1: Fallback indicator when API fails
    // ===================================================================

    describe('AC-31.8.1: Fallback indicator display', () => {
        it('should show .fallback-indicator when fetchRecommendation fails', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockRejectedValue(new Error('Network error'));

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();
            await waitForAsync();

            const contentEl = (panel as any).contentEl as HTMLElement;
            const indicator = contentEl.querySelector('.fallback-indicator');
            expect(indicator).not.toBeNull();
        });

        it('should display correct fallback text', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockRejectedValue(new Error('Server down'));

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();
            await waitForAsync();

            const contentEl = (panel as any).contentEl as HTMLElement;
            const textEl = contentEl.querySelector('.fallback-text');
            expect(textEl).not.toBeNull();
            expect(textEl!.textContent).toContain('离线推荐');
            expect(textEl!.textContent).toContain('后端不可用');
            expect(textEl!.textContent).toContain('本地规则');
        });
    });

    // ===================================================================
    // AC-31.8.2: Retry button functionality
    // ===================================================================

    describe('AC-31.8.2: Retry button', () => {
        it('should remove fallback indicator after successful retry', async () => {
            const result = createMockResult();
            // First call fails, second call succeeds
            apiClient.recommendAction
                .mockRejectedValueOnce(new Error('Network error'))
                .mockResolvedValueOnce(createMockRecommendation());

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();
            await waitForAsync();

            // Verify fallback indicator is present
            let contentEl = (panel as any).contentEl as HTMLElement;
            expect(contentEl.querySelector('.fallback-indicator')).not.toBeNull();

            // Click retry button
            const retryBtn = contentEl.querySelector('.fallback-retry-button') as HTMLButtonElement;
            expect(retryBtn).not.toBeNull();
            retryBtn.click();
            await waitForAsync(100);

            // After successful retry, fallback indicator should be gone
            contentEl = (panel as any).contentEl as HTMLElement;
            expect(contentEl.querySelector('.fallback-indicator')).toBeNull();
        });

        it('should show Notice "后端仍不可用" when retry also fails', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockRejectedValue(new Error('Server down'));

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();
            await waitForAsync();

            // Click retry
            const contentEl = (panel as any).contentEl as HTMLElement;
            const retryBtn = contentEl.querySelector('.fallback-retry-button') as HTMLButtonElement;
            retryBtn.click();
            await waitForAsync(100);

            // Notice should be called with "后端仍不可用"
            expect(Notice).toHaveBeenCalledWith('后端仍不可用');
        });
    });

    // ===================================================================
    // AC-31.8.3: No indicator when API succeeds
    // ===================================================================

    describe('AC-31.8.3: No fallback indicator when API works', () => {
        it('should NOT show .fallback-indicator when API returns recommendation', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockResolvedValue(createMockRecommendation());

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();
            await waitForAsync();

            const contentEl = (panel as any).contentEl as HTMLElement;
            expect(contentEl.querySelector('.fallback-indicator')).toBeNull();
        });
    });

    // ===================================================================
    // AC-31.8.4: console.warn logging
    // ===================================================================

    describe('AC-31.8.4: Console warn logging', () => {
        it('should log console.warn when using fallback recommendations', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockRejectedValue(new Error('API down'));

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();
            await waitForAsync();

            expect(consoleWarnSpy).toHaveBeenCalledWith(
                expect.stringContaining('Story 31.8')
            );
        });
    });

    // ===================================================================
    // AC-31.8.5, AC-31.8.6: Existing functionality preserved
    // ===================================================================

    describe('AC-31.8.5/6: Existing functionality not affected', () => {
        it('should still render score details and agent buttons in fallback mode', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockRejectedValue(new Error('fail'));

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();
            await waitForAsync();

            const contentEl = (panel as any).contentEl as HTMLElement;
            // Score details should still render
            expect(contentEl.querySelector('.total-score-section')).not.toBeNull();
            expect(contentEl.querySelector('.dimensions-section')).not.toBeNull();
            expect(contentEl.querySelector('.feedback-section')).not.toBeNull();
            // Agent buttons should still render
            expect(contentEl.querySelector('.agent-buttons-section')).not.toBeNull();
        });
    });

    // ===================================================================
    // AC-31.8.7: Navigation works in fallback mode
    // ===================================================================

    describe('AC-31.8.7: Navigation in fallback mode', () => {
        it('should independently check API for each node when navigating', async () => {
            const result1 = createMockResult({ nodeId: 'node-1', nodeText: '概念1' });
            const result2 = createMockResult({ nodeId: 'node-2', nodeText: '概念2' });
            // Node 1 fails, Node 2 succeeds
            apiClient.recommendAction
                .mockRejectedValueOnce(new Error('fail'))
                .mockResolvedValueOnce(createMockRecommendation());

            const panel = new ScoringResultPanel(app, [result1, result2], apiClient, callbacks);
            panel.onOpen();
            await waitForAsync();

            // Node 1 should show fallback
            let contentEl = (panel as any).contentEl as HTMLElement;
            expect(contentEl.querySelector('.fallback-indicator')).not.toBeNull();

            // Navigate to next node
            const nextBtn = contentEl.querySelector('.next-button') as HTMLButtonElement;
            expect(nextBtn).not.toBeNull();
            nextBtn.click();
            await waitForAsync(100);

            // Node 2 should NOT show fallback (API succeeds)
            contentEl = (panel as any).contentEl as HTMLElement;
            expect(contentEl.querySelector('.fallback-indicator')).toBeNull();
        });
    });
});
