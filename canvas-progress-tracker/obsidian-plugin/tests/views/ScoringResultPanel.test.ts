/**
 * ScoringResultPanel Unit Tests
 *
 * Tests for the recommendation status indicator (Story 31.10):
 * - Online mode: "智能推荐" label with history context
 * - Offline mode: "离线推荐" label with retry button
 * - Retry button behavior: debounce, cache clearing, re-fetch
 *
 * @source Story 31.10 - AC-31.10.1, AC-31.10.2, AC-31.10.3, AC-31.10.8
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

/**
 * Add Obsidian-specific DOM methods (empty, addClass, createEl) to an HTMLElement.
 * Follows the pattern from tests/modals/AttachMediaModal.test.ts.
 */
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

// ===========================================================================
// Test Suites
// ===========================================================================

describe('ScoringResultPanel - Story 31.10: Recommendation Status Indicator', () => {
    let app: App;
    let apiClient: jest.Mocked<ApiClient>;
    let callbacks: ScoringResultCallbacks;

    beforeEach(() => {
        jest.clearAllMocks();
        app = createMockApp();
        apiClient = createMockApiClient() as jest.Mocked<ApiClient>;
        callbacks = createMockCallbacks();
    });

    // ===================================================================
    // AC-31.10.2: Online/Intelligent Recommendation Label
    // ===================================================================

    describe('AC-31.10.2: Online recommendation status', () => {
        it('should render "智能推荐" label when API recommendation succeeds', async () => {
            const result = createMockResult();
            const recommendation = createMockRecommendation();
            apiClient.recommendAction.mockResolvedValue(recommendation);

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            // Wait for async render
            await new Promise((r) => setTimeout(r, 50));

            const contentEl = (panel as any).contentEl as HTMLElement;
            const statusEl = contentEl.querySelector('.recommendation-status-online');
            expect(statusEl).not.toBeNull();

            const label = statusEl!.querySelector('.recommendation-status-label');
            expect(label).not.toBeNull();
            expect(label!.textContent).toContain('智能推荐');
        });

        it('should show history count when history_context is present', async () => {
            const result = createMockResult();
            const recommendation = createMockRecommendation({
                history_context: {
                    recent_scores: [70, 75, 80],
                    average_score: 75,
                    trend: 'improving',
                    consecutive_low_count: 0,
                },
            });
            apiClient.recommendAction.mockResolvedValue(recommendation);

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            const contentEl = (panel as any).contentEl as HTMLElement;
            const infoEl = contentEl.querySelector('.recommendation-status-info');
            expect(infoEl).not.toBeNull();
            expect(infoEl!.textContent).toContain('3 次历史记录');
        });

        it('should NOT show history count when history_context is absent', async () => {
            const result = createMockResult();
            const recommendation = createMockRecommendation();
            apiClient.recommendAction.mockResolvedValue(recommendation);

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            const contentEl = (panel as any).contentEl as HTMLElement;
            const infoEl = contentEl.querySelector('.recommendation-status-info');
            expect(infoEl).toBeNull();
        });
    });

    // ===================================================================
    // AC-31.10.1: Offline/Fallback Recommendation Label
    // ===================================================================

    describe('AC-31.10.1: Offline recommendation status', () => {
        it('should render fallback indicator when API recommendation fails', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockRejectedValue(new Error('Network error'));

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            const contentEl = (panel as any).contentEl as HTMLElement;
            const statusEl = contentEl.querySelector('.fallback-indicator');
            expect(statusEl).not.toBeNull();

            const label = statusEl!.querySelector('.fallback-text');
            expect(label).not.toBeNull();
            expect(label!.textContent).toContain('离线推荐');
        });

        it('should NOT render online status when API fails', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockRejectedValue(new Error('Timeout'));

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            const contentEl = (panel as any).contentEl as HTMLElement;
            const onlineEl = contentEl.querySelector('.recommendation-status-online');
            expect(onlineEl).toBeNull();
        });

        it('should include retry button in offline mode', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockRejectedValue(new Error('Network error'));

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            const contentEl = (panel as any).contentEl as HTMLElement;
            const retryBtn = contentEl.querySelector(
                '.fallback-retry-button'
            ) as HTMLButtonElement;
            expect(retryBtn).not.toBeNull();
            expect(retryBtn!.textContent).toContain('重试');
        });
    });

    // ===================================================================
    // AC-31.10.3: Retry Functionality
    // ===================================================================

    describe('AC-31.10.3: Retry button behavior', () => {
        it('should clear cache and re-fetch on retry click', async () => {
            const result = createMockResult();
            // First call fails, second succeeds
            apiClient.recommendAction
                .mockRejectedValueOnce(new Error('Network error'))
                .mockResolvedValueOnce(createMockRecommendation());

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            // Verify offline state
            let contentEl = (panel as any).contentEl as HTMLElement;
            expect(contentEl.querySelector('.fallback-indicator')).not.toBeNull();

            // Click retry
            const retryBtn = contentEl.querySelector(
                '.fallback-retry-button'
            ) as HTMLButtonElement;
            retryBtn.click();

            await new Promise((r) => setTimeout(r, 100));

            // After successful retry, should show online status
            contentEl = (panel as any).contentEl as HTMLElement;
            expect(contentEl.querySelector('.recommendation-status-online')).not.toBeNull();
            expect(contentEl.querySelector('.fallback-indicator')).toBeNull();

            // API should have been called twice (initial + retry)
            expect(apiClient.recommendAction).toHaveBeenCalledTimes(2);
        });

        it('should show Notice on retry failure', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockRejectedValue(new Error('Server down'));

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            // Click retry
            const contentEl = (panel as any).contentEl as HTMLElement;
            const retryBtn = contentEl.querySelector(
                '.fallback-retry-button'
            ) as HTMLButtonElement;
            retryBtn.click();

            await new Promise((r) => setTimeout(r, 100));

            // Notice should have been called with failure message
            expect(Notice).toHaveBeenCalledWith(
                '后端仍不可用'
            );
        });

        it('should debounce rapid retry clicks (2s window)', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockRejectedValue(new Error('Server down'));

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            const contentEl = (panel as any).contentEl as HTMLElement;
            const retryBtn = contentEl.querySelector(
                '.fallback-retry-button'
            ) as HTMLButtonElement;

            // Click retry twice rapidly
            retryBtn.click();
            retryBtn.click();

            await new Promise((r) => setTimeout(r, 100));

            // Should only have called API twice total (1 initial + 1 retry, second click debounced)
            expect(apiClient.recommendAction).toHaveBeenCalledTimes(2);
        });
    });

    // ===================================================================
    // AC-31.10.5, AC-31.10.6: Integration - No change to existing logic
    // ===================================================================

    describe('AC-31.10.5/6: Existing behavior preserved', () => {
        it('should still render agent buttons in offline mode', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockRejectedValue(new Error('API down'));

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            const contentEl = (panel as any).contentEl as HTMLElement;
            const buttonsSection = contentEl.querySelector('.agent-buttons-section');
            expect(buttonsSection).not.toBeNull();

            // Should have fallback buttons
            const buttons = buttonsSection!.querySelectorAll('.agent-button');
            expect(buttons.length).toBeGreaterThan(0);
        });

        it('should still render agent buttons in online mode', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockResolvedValue(createMockRecommendation());

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            const contentEl = (panel as any).contentEl as HTMLElement;
            const buttonsSection = contentEl.querySelector('.agent-buttons-section');
            expect(buttonsSection).not.toBeNull();
        });

        it('should render scoring header and score details regardless of mode', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockRejectedValue(new Error('fail'));

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            const contentEl = (panel as any).contentEl as HTMLElement;
            expect(contentEl.querySelector('.scoring-header')).not.toBeNull();
            expect(contentEl.querySelector('.total-score-section')).not.toBeNull();
            expect(contentEl.querySelector('.feedback-section')).not.toBeNull();
        });
    });

    // ===================================================================
    // AC-31.10.7: No user experience change when API is available
    // ===================================================================

    describe('AC-31.10.7: Minimal UX impact in online mode', () => {
        it('should not show retry button in online mode', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockResolvedValue(createMockRecommendation());

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            const contentEl = (panel as any).contentEl as HTMLElement;
            const retryBtn = contentEl.querySelector('.fallback-retry-button');
            expect(retryBtn).toBeNull();
        });
    });

    // ===================================================================
    // Code Review Fix: Retry cooldown and stale render protection
    // ===================================================================

    describe('Retry cooldown behavior (Task 3.6)', () => {
        it('should disable new retry button for 5s cooldown after retry failure', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockRejectedValue(new Error('Server down'));

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            // Click retry
            const contentEl = (panel as any).contentEl as HTMLElement;
            const retryBtn = contentEl.querySelector(
                '.fallback-retry-button'
            ) as HTMLButtonElement;
            retryBtn.click();

            await new Promise((r) => setTimeout(r, 100));

            // After failed retry, the NEW retry button should be in cooldown state
            const newContentEl = (panel as any).contentEl as HTMLElement;
            const newRetryBtn = newContentEl.querySelector(
                '.fallback-retry-button'
            ) as HTMLButtonElement;
            expect(newRetryBtn).not.toBeNull();
            expect(newRetryBtn.disabled).toBe(true);
            expect(newRetryBtn.textContent).toBe('冷却中...');
        });

        it('should show retry button enabled initially (no cooldown on first load)', async () => {
            const result = createMockResult();
            apiClient.recommendAction.mockRejectedValue(new Error('API down'));

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            const contentEl = (panel as any).contentEl as HTMLElement;
            const retryBtn = contentEl.querySelector(
                '.fallback-retry-button'
            ) as HTMLButtonElement;
            expect(retryBtn).not.toBeNull();
            expect(retryBtn.disabled).toBe(false);
        });

        it('should not apply cooldown when retry succeeds', async () => {
            const result = createMockResult();
            apiClient.recommendAction
                .mockRejectedValueOnce(new Error('Temp failure'))
                .mockResolvedValueOnce(createMockRecommendation());

            const panel = new ScoringResultPanel(app, [result], apiClient, callbacks);
            panel.onOpen();

            await new Promise((r) => setTimeout(r, 50));

            // Click retry — this time it succeeds
            const contentEl = (panel as any).contentEl as HTMLElement;
            const retryBtn = contentEl.querySelector(
                '.fallback-retry-button'
            ) as HTMLButtonElement;
            retryBtn.click();

            await new Promise((r) => setTimeout(r, 100));

            // Should now be in online mode — no retry button at all
            const newContentEl = (panel as any).contentEl as HTMLElement;
            const newRetryBtn = newContentEl.querySelector('.fallback-retry-button');
            expect(newRetryBtn).toBeNull();
            expect(newContentEl.querySelector('.recommendation-status-online')).not.toBeNull();
        });
    });
});
