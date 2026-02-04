/**
 * @jest-environment jsdom
 */

/**
 * Canvas Learning System - MediaPanel Component Tests
 *
 * Story 35.4: MediaPanel后端集成
 * Tests for dynamic data fetching, loading/error states,
 * concept change handling, and refresh functionality.
 *
 * @source Story 35.4 - MediaPanel后端集成
 * @verified 2026-01-20
 */

import {
  createMediaPanel,
  updateMediaPanelConcept,
  cleanupMediaPanel,
  isMediaPanelLoading,
  getMediaPanelError,
  refreshMediaPanel,
  MediaItem,
  MediaPanelProps,
} from '../../src/components/MediaPanel';
import { ApiClient } from '../../src/api/ApiClient';
import { ApiError } from '../../src/api/types';

// ===========================================================================
// Mock Setup
// ===========================================================================

// Mock ApiClient
const mockGetMediaByConceptId = jest.fn();
const mockApiClient = {
  getMediaByConceptId: mockGetMediaByConceptId,
} as unknown as ApiClient;

// Mock media items
const mockMediaItems: MediaItem[] = [
  {
    id: 'media-1',
    type: 'image',
    path: '/images/concept1.png',
    title: 'Test Image',
    relevanceScore: 0.95,
    conceptId: 'concept-1',
  },
  {
    id: 'media-2',
    type: 'pdf',
    path: '/docs/concept1.pdf',
    title: 'Test PDF',
    relevanceScore: 0.87,
    conceptId: 'concept-1',
  },
];

// Helper to wait for async operations (works in jsdom with real timers)
const flushPromises = () => new Promise(resolve => {
  // Use setTimeout to ensure we yield to the event loop
  setTimeout(resolve, 0);
});

// Helper to advance fake timers and flush promises
const advanceTimersAndFlush = async (ms: number) => {
  // Advance fake timers
  jest.advanceTimersByTime(ms);
  // Let any pending promise callbacks run
  await Promise.resolve();
  // Run any microtasks
  await Promise.resolve();
};

// Helper to wait a short time for async operations
const waitForAsync = (ms = 50) => new Promise(resolve => setTimeout(resolve, ms));

beforeEach(() => {
  mockGetMediaByConceptId.mockReset();
  document.body.innerHTML = '';
});

afterEach(() => {
  jest.useRealTimers();
});

// ===========================================================================
// AC 35.4.1: MediaPanel从后端获取数据
// ===========================================================================

describe('MediaPanel Data Fetching (Story 35.4 AC1)', () => {
  test('should fetch media items on mount when apiClient and conceptId provided', async () => {
    mockGetMediaByConceptId.mockResolvedValueOnce(mockMediaItems);

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    // Wait for async fetch
    await flushPromises();

    expect(mockGetMediaByConceptId).toHaveBeenCalledWith('concept-1');
    expect(mockGetMediaByConceptId).toHaveBeenCalledTimes(1);
  });

  test('should NOT fetch when no apiClient provided (static mode)', async () => {
    const panel = createMediaPanel({
      items: mockMediaItems,
    });
    document.body.appendChild(panel);

    await flushPromises();

    expect(mockGetMediaByConceptId).not.toHaveBeenCalled();

    // Should render static items
    const items = panel.querySelectorAll('.media-item');
    expect(items.length).toBe(2);
  });

  test('should NOT fetch when no conceptId provided', async () => {
    const panel = createMediaPanel({
      apiClient: mockApiClient,
    });
    document.body.appendChild(panel);

    await flushPromises();

    expect(mockGetMediaByConceptId).not.toHaveBeenCalled();
  });

  test('should render fetched items correctly', async () => {
    mockGetMediaByConceptId.mockResolvedValueOnce(mockMediaItems);

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    await flushPromises();

    const items = panel.querySelectorAll('.media-item');
    expect(items.length).toBe(2);
  });

  test('should call onRefresh callback after successful fetch', async () => {
    mockGetMediaByConceptId.mockResolvedValueOnce(mockMediaItems);
    const onRefresh = jest.fn();

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
      onRefresh,
    });
    document.body.appendChild(panel);

    await flushPromises();

    expect(onRefresh).toHaveBeenCalledWith(mockMediaItems);
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});

// ===========================================================================
// AC 35.4.2: 支持概念切换刷新
// ===========================================================================

describe('MediaPanel Concept Change (Story 35.4 AC2)', () => {
  test('should fetch new data when concept changes via updateMediaPanelConcept', async () => {
    jest.useFakeTimers();
    mockGetMediaByConceptId
      .mockResolvedValueOnce(mockMediaItems)
      .mockResolvedValueOnce([{ ...mockMediaItems[0], conceptId: 'concept-2' }]);

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    // Initial fetch
    jest.runAllTimers();
    await Promise.resolve();
    await Promise.resolve();
    expect(mockGetMediaByConceptId).toHaveBeenCalledTimes(1);

    // Update concept
    updateMediaPanelConcept(panel, 'concept-2');

    // Wait for debounce (300ms)
    await advanceTimersAndFlush(300);
    await Promise.resolve();

    expect(mockGetMediaByConceptId).toHaveBeenCalledTimes(2);
    expect(mockGetMediaByConceptId).toHaveBeenLastCalledWith('concept-2');
  });

  test('should debounce rapid concept changes (300ms)', async () => {
    jest.useFakeTimers();
    mockGetMediaByConceptId.mockResolvedValue(mockMediaItems);

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    // Initial fetch
    jest.runAllTimers();
    await Promise.resolve();
    await Promise.resolve();
    expect(mockGetMediaByConceptId).toHaveBeenCalledTimes(1);

    // Rapid concept changes
    updateMediaPanelConcept(panel, 'concept-2');
    await advanceTimersAndFlush(100);
    updateMediaPanelConcept(panel, 'concept-3');
    await advanceTimersAndFlush(100);
    updateMediaPanelConcept(panel, 'concept-4');

    // Wait for debounce
    await advanceTimersAndFlush(300);
    await Promise.resolve();

    // Should only fetch once more (for concept-4)
    expect(mockGetMediaByConceptId).toHaveBeenCalledTimes(2);
    expect(mockGetMediaByConceptId).toHaveBeenLastCalledWith('concept-4');
  });

  test('should cancel pending request when concept changes', async () => {
    jest.useFakeTimers();
    // First fetch takes a long time
    let firstResolve: (value: MediaItem[]) => void;
    const firstPromise = new Promise<MediaItem[]>(resolve => {
      firstResolve = resolve;
    });
    mockGetMediaByConceptId
      .mockReturnValueOnce(firstPromise)
      .mockResolvedValueOnce([{ ...mockMediaItems[0], conceptId: 'concept-2' }]);

    const onRefresh = jest.fn();
    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
      onRefresh,
    });
    document.body.appendChild(panel);

    // First fetch starts
    jest.runAllTimers();
    await Promise.resolve();
    expect(mockGetMediaByConceptId).toHaveBeenCalledTimes(1);

    // Change concept before first fetch completes
    updateMediaPanelConcept(panel, 'concept-2');
    await advanceTimersAndFlush(300);

    // Second fetch completes
    await Promise.resolve();
    await Promise.resolve();

    // Resolve first fetch (should be ignored due to abort)
    firstResolve!(mockMediaItems);
    await Promise.resolve();
    await Promise.resolve();

    // onRefresh should only be called once (for concept-2)
    expect(onRefresh).toHaveBeenCalledTimes(1);
    expect(onRefresh).toHaveBeenCalledWith([{ ...mockMediaItems[0], conceptId: 'concept-2' }]);
  });
});

// ===========================================================================
// AC 35.4.3: 加载状态UI
// ===========================================================================

describe('MediaPanel Loading State (Story 35.4 AC3)', () => {
  test('should show loading state initially', async () => {
    // Make the fetch hang
    mockGetMediaByConceptId.mockReturnValue(new Promise(() => {}));

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    // Check loading state immediately
    const loadingEl = panel.querySelector('.media-panel-loading');
    expect(loadingEl).not.toBeNull();

    const spinner = panel.querySelector('.media-panel-spinner');
    expect(spinner).not.toBeNull();
  });

  test('should return true from isMediaPanelLoading during fetch', async () => {
    mockGetMediaByConceptId.mockReturnValue(new Promise(() => {}));

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    expect(isMediaPanelLoading(panel)).toBe(true);
  });

  test('should hide loading state after fetch completes', async () => {
    mockGetMediaByConceptId.mockResolvedValueOnce(mockMediaItems);

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    await flushPromises();

    const loadingEl = panel.querySelector('.media-panel-loading');
    expect(loadingEl).toBeNull();
    expect(isMediaPanelLoading(panel)).toBe(false);
  });

  test('should disable refresh button during loading', async () => {
    mockGetMediaByConceptId.mockReturnValue(new Promise(() => {}));

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    const refreshBtn = panel.querySelector('.media-panel-refresh-btn') as HTMLButtonElement;
    expect(refreshBtn).not.toBeNull();
    expect(refreshBtn.disabled).toBe(true);
    expect(refreshBtn.style.opacity).toBe('0.5');
  });
});

// ===========================================================================
// AC 35.4.4: 错误状态UI
// ===========================================================================

describe('MediaPanel Error State (Story 35.4 AC4)', () => {
  test('should show error state when fetch fails', async () => {
    const error = new ApiError('Network error', 'NetworkError', 0);
    mockGetMediaByConceptId.mockRejectedValueOnce(error);

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    await flushPromises();

    const errorEl = panel.querySelector('.media-panel-error');
    expect(errorEl).not.toBeNull();
  });

  test('should return error from getMediaPanelError', async () => {
    const error = new ApiError('Network error', 'NetworkError', 0);
    mockGetMediaByConceptId.mockRejectedValueOnce(error);

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    await flushPromises();

    const panelError = getMediaPanelError(panel);
    expect(panelError).not.toBeNull();
    expect(panelError?.type).toBe('NetworkError');
  });

  test('should show retry button for retryable errors', async () => {
    const error = new ApiError('Service unavailable', 'HttpError5xx', 503);
    mockGetMediaByConceptId.mockRejectedValueOnce(error);

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    await flushPromises();

    const retryBtn = panel.querySelector('.media-panel-retry-btn');
    expect(retryBtn).not.toBeNull();
  });

  test('should NOT show retry button for non-retryable errors', async () => {
    const error = new ApiError('Not found', 'HttpError4xx', 404);
    mockGetMediaByConceptId.mockRejectedValueOnce(error);

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    await flushPromises();

    const retryBtn = panel.querySelector('.media-panel-retry-btn');
    expect(retryBtn).toBeNull();
  });

  test('should retry when retry button clicked', async () => {
    const error = new ApiError('Service unavailable', 'HttpError5xx', 503);
    mockGetMediaByConceptId
      .mockRejectedValueOnce(error)
      .mockResolvedValueOnce(mockMediaItems);

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    await flushPromises();
    expect(mockGetMediaByConceptId).toHaveBeenCalledTimes(1);

    // Click retry button
    const retryBtn = panel.querySelector('.media-panel-retry-btn') as HTMLButtonElement;
    retryBtn.click();

    await flushPromises();

    expect(mockGetMediaByConceptId).toHaveBeenCalledTimes(2);

    // Should now show items
    const items = panel.querySelectorAll('.media-item');
    expect(items.length).toBe(2);
  });

  test('should call onRefresh with error on fetch failure', async () => {
    const error = new ApiError('Network error', 'NetworkError', 0);
    mockGetMediaByConceptId.mockRejectedValueOnce(error);
    const onRefresh = jest.fn();

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
      onRefresh,
    });
    document.body.appendChild(panel);

    await flushPromises();

    expect(onRefresh).toHaveBeenCalledWith([], expect.any(ApiError));
  });
});

// ===========================================================================
// AC 35.4.5: 刷新功能
// ===========================================================================

describe('MediaPanel Refresh (Story 35.4 AC5)', () => {
  test('should show refresh button in dynamic mode', async () => {
    mockGetMediaByConceptId.mockResolvedValueOnce(mockMediaItems);

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    await flushPromises();

    const refreshBtn = panel.querySelector('.media-panel-refresh-btn');
    expect(refreshBtn).not.toBeNull();
  });

  test('should NOT show refresh button in static mode', async () => {
    const panel = createMediaPanel({
      items: mockMediaItems,
    });
    document.body.appendChild(panel);

    const refreshBtn = panel.querySelector('.media-panel-refresh-btn');
    expect(refreshBtn).toBeNull();
  });

  test('should refresh when refresh button clicked', async () => {
    mockGetMediaByConceptId
      .mockResolvedValueOnce(mockMediaItems)
      .mockResolvedValueOnce([mockMediaItems[0]]);

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    // Wait for initial fetch
    await waitForAsync(10);
    expect(mockGetMediaByConceptId).toHaveBeenCalledTimes(1);

    // Click refresh
    const refreshBtn = panel.querySelector('.media-panel-refresh-btn') as HTMLButtonElement;
    expect(refreshBtn).not.toBeNull();
    expect(refreshBtn.disabled).toBe(false); // Button should be enabled after first fetch
    refreshBtn.click();

    // Wait for the refresh fetch to complete
    await waitForAsync(10);

    expect(mockGetMediaByConceptId).toHaveBeenCalledTimes(2);
  });

  test('should refresh when refreshMediaPanel called', async () => {
    mockGetMediaByConceptId
      .mockResolvedValueOnce(mockMediaItems)
      .mockResolvedValueOnce([mockMediaItems[0]]);

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    await flushPromises();
    expect(mockGetMediaByConceptId).toHaveBeenCalledTimes(1);

    // Call refresh programmatically
    refreshMediaPanel(panel);

    await flushPromises();

    expect(mockGetMediaByConceptId).toHaveBeenCalledTimes(2);
  });

  test('should call onRefresh callback after manual refresh', async () => {
    const newItems = [mockMediaItems[0]];
    mockGetMediaByConceptId
      .mockResolvedValueOnce(mockMediaItems)
      .mockResolvedValueOnce(newItems);

    const onRefresh = jest.fn();
    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
      onRefresh,
    });
    document.body.appendChild(panel);

    await flushPromises();
    expect(onRefresh).toHaveBeenCalledTimes(1);
    onRefresh.mockClear();

    // Refresh
    refreshMediaPanel(panel);
    await flushPromises();

    expect(onRefresh).toHaveBeenCalledTimes(1);
    expect(onRefresh).toHaveBeenCalledWith(newItems);
  });
});

// ===========================================================================
// Cleanup Tests
// ===========================================================================

describe('MediaPanel Cleanup', () => {
  test('should cancel pending requests on cleanup', async () => {
    let resolvePromise: (value: MediaItem[]) => void;
    const pendingPromise = new Promise<MediaItem[]>(resolve => {
      resolvePromise = resolve;
    });
    mockGetMediaByConceptId.mockReturnValue(pendingPromise);

    const onRefresh = jest.fn();
    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
      onRefresh,
    });
    document.body.appendChild(panel);

    // Cleanup before fetch completes
    cleanupMediaPanel(panel);

    // Resolve the promise
    resolvePromise!(mockMediaItems);
    await flushPromises();

    // onRefresh should NOT be called (request was aborted)
    expect(onRefresh).not.toHaveBeenCalled();
  });

  test('should clear debounce timer on cleanup', async () => {
    jest.useFakeTimers();
    mockGetMediaByConceptId.mockResolvedValue(mockMediaItems);

    const panel = createMediaPanel({
      apiClient: mockApiClient,
      conceptId: 'concept-1',
    });
    document.body.appendChild(panel);

    // Initial fetch
    jest.runAllTimers();
    await Promise.resolve();
    await Promise.resolve();
    expect(mockGetMediaByConceptId).toHaveBeenCalledTimes(1);

    // Start a concept change (debounced)
    updateMediaPanelConcept(panel, 'concept-2');

    // Cleanup before debounce fires
    cleanupMediaPanel(panel);

    // Advance timer past debounce
    await advanceTimersAndFlush(500);

    // Should NOT have made a second request
    expect(mockGetMediaByConceptId).toHaveBeenCalledTimes(1);
  });
});

// ===========================================================================
// Static Mode Tests (Backwards Compatibility)
// ===========================================================================

describe('MediaPanel Static Mode', () => {
  test('should render static items without apiClient', () => {
    const panel = createMediaPanel({
      items: mockMediaItems,
    });
    document.body.appendChild(panel);

    const items = panel.querySelectorAll('.media-item');
    expect(items.length).toBe(2);
  });

  test('should NOT show loading state in static mode', () => {
    const panel = createMediaPanel({
      items: mockMediaItems,
    });
    document.body.appendChild(panel);

    const loadingEl = panel.querySelector('.media-panel-loading');
    expect(loadingEl).toBeNull();
    expect(isMediaPanelLoading(panel)).toBe(false);
  });

  test('should show empty state when no items in static mode', () => {
    const panel = createMediaPanel({
      items: [],
    });
    document.body.appendChild(panel);

    const emptyState = panel.querySelector('.media-panel-empty');
    expect(emptyState).not.toBeNull();
    expect(emptyState?.textContent).toContain('暂无关联资料');
  });
});
