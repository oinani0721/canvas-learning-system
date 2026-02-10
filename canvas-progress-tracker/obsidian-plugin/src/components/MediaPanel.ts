/**
 * Media Panel Component
 *
 * Story 6.9 AC 6.9.4: 关联资料面板
 * - 显示概念关联的所有资料
 * - 按相关度排序
 * - 支持筛选和搜索
 *
 * Story 6.9 AC 6.9.5: 移动端适配
 * - 响应式布局
 * - 触摸手势支持
 * - 适配小屏幕
 *
 * Story 35.4: MediaPanel后端集成
 * - 从ApiClient获取动态数据
 * - 支持概念切换刷新
 * - 加载状态和错误处理UI
 * - 刷新功能
 *
 * ✅ Verified from Canvas component patterns
 * [Source: docs/stories/6.9.multimodal-ui-integration.story.md:42-50]
 * [Source: docs/stories/35.4.story.md]
 */

import { createImagePreview, ImageGalleryProps } from './ImagePreview';
import { createPDFThumbnail } from './PDFPreview';
import { createAudioPlayer, createVideoPlayer, TimeMarker } from './MediaPlayer';
import { ApiClient } from '../api/ApiClient';
import { ApiError, MediaType as ApiMediaType, MediaItem as ApiMediaItem } from '../api/types';

/**
 * Media filter type - extends API MediaType with 'all' for UI filtering
 */
export type MediaType = ApiMediaType | 'all';

/**
 * Media item interface - extends API MediaItem with UI-specific fields
 */
export interface MediaItem extends ApiMediaItem {
    /** Override type to exclude 'all' filter value */
    type: ApiMediaType;
    /** Timestamp for audio/video */
    timestamp?: number;
    /** Time markers for audio/video */
    markers?: TimeMarker[];
}

/**
 * Props for MediaPanel component.
 *
 * Story 35.4: Extended props for dynamic data fetching
 * - apiClient: API client for backend calls
 * - conceptId: Concept ID for dynamic data loading
 * - onRefresh: Callback after refresh completes
 */
export interface MediaPanelProps {
    /** Panel title */
    title?: string;
    /** Media items to display (static mode) */
    items?: MediaItem[];
    /** Initial filter type (default: 'all') */
    initialFilter?: MediaType;
    /** Show search box (default: true) */
    showSearch?: boolean;
    /** Show relevance scores (default: true) */
    showRelevance?: boolean;
    /** Grid columns (default: auto) */
    columns?: number;
    /** Item thumbnail size (default: 150) */
    thumbnailSize?: number;
    /** Callback when item is clicked */
    onItemClick?: (item: MediaItem) => void;
    /** Callback when filter changes */
    onFilterChange?: (filter: MediaType) => void;
    /** Sort order */
    sortBy?: 'relevance' | 'name' | 'type' | 'date';
    /** Enable drag and drop (default: false) */
    draggable?: boolean;
    /** Story 35.4: API client for dynamic data fetching (AC 35.4.1) */
    apiClient?: ApiClient;
    /** Story 35.4: Concept ID for data fetching (AC 35.4.2) */
    conceptId?: string;
    /** Story 35.4: Callback when refresh completes (AC 35.4.5) */
    onRefresh?: (items: MediaItem[], error?: ApiError) => void;
}

/**
 * Props for MediaList component.
 */
export interface MediaListProps {
    /** Media items to display */
    items: MediaItem[];
    /** Display mode */
    mode: 'grid' | 'list';
    /** Thumbnail size */
    thumbnailSize?: number;
    /** Show relevance scores */
    showRelevance?: boolean;
    /** Item click handler */
    onItemClick?: (item: MediaItem) => void;
}

/**
 * Internal panel state
 *
 * Story 35.4: Extended state for dynamic data fetching
 * - isLoading: Whether data is being fetched
 * - error: API error if fetch failed
 * - items: Dynamically loaded items
 */
interface PanelState {
    filter: MediaType;
    searchQuery: string;
    sortBy: 'relevance' | 'name' | 'type' | 'date';
    displayMode: 'grid' | 'list';
    /** Story 35.4 AC 35.4.3: Loading state */
    isLoading: boolean;
    /** Story 35.4 AC 35.4.4: Error state */
    error: ApiError | null;
    /** Story 35.4: Dynamically loaded items */
    items: MediaItem[];
    /** Story 35.4 AC 35.4.2: Current concept ID */
    conceptId: string | null;
    /** Story 35.11 AC 35.11.2: Search mode from backend ("vector" = full, "text" = degraded) */
    searchMode: 'vector' | 'text' | null;
}

/**
 * Story 35.4: Debounce delay for concept change (AC 35.4.2)
 * Prevents excessive API calls when user rapidly switches nodes
 */
const CONCEPT_CHANGE_DEBOUNCE_MS = 300;

/**
 * Creates a media panel component for displaying associated media items.
 *
 * Features:
 * - Type-based filtering
 * - Search functionality
 * - Relevance-based sorting
 * - Grid/list view toggle
 * - Responsive layout
 * - Story 35.4: Dynamic data fetching from backend
 * - Story 35.4: Loading and error states
 * - Story 35.4: Concept change with debouncing and AbortController
 * - Story 35.4: Manual refresh functionality
 *
 * ✅ Verified from Canvas component patterns
 *
 * Example (static mode):
 * ```typescript
 * const panel = createMediaPanel({
 *     title: '关联资料',
 *     items: mediaItems,
 *     showSearch: true,
 *     onItemClick: (item) => console.log('Clicked:', item)
 * });
 * container.appendChild(panel);
 * ```
 *
 * Example (dynamic mode - Story 35.4):
 * ```typescript
 * const panel = createMediaPanel({
 *     title: '关联资料',
 *     apiClient: myApiClient,
 *     conceptId: 'node-123',
 *     onItemClick: (item) => console.log('Clicked:', item),
 *     onRefresh: (items, error) => console.log('Refresh:', items.length)
 * });
 * container.appendChild(panel);
 *
 * // Update concept when user selects different node
 * updateMediaPanelConcept(panel, 'node-456');
 * ```
 */
export function createMediaPanel(props: MediaPanelProps): HTMLElement {
    const {
        title = '关联资料',
        items: staticItems = [],
        initialFilter = 'all',
        showSearch = true,
        showRelevance = true,
        columns,
        thumbnailSize = 150,
        onItemClick,
        onFilterChange,
        sortBy = 'relevance',
        draggable = false,
        apiClient,
        conceptId,
        onRefresh
    } = props;

    // Story 35.4 AC 35.4.2: AbortController for request cancellation
    let currentAbortController: AbortController | null = null;
    // Story 35.4 AC 35.4.2: Debounce timer for concept change
    let debounceTimer: ReturnType<typeof setTimeout> | null = null;

    const state: PanelState = {
        filter: initialFilter,
        searchQuery: '',
        sortBy,
        displayMode: 'grid',
        // Story 35.4: Start with isLoading=false; fetchMediaItems will set it to true
        isLoading: false,
        error: null,
        items: staticItems,
        conceptId: conceptId || null,
        // Story 35.11: null = no search performed yet
        searchMode: null
    };

    const container = document.createElement('div');
    container.className = 'media-panel';
    container.style.cssText = `
        width: 100%;
        background: var(--background-secondary);
        border-radius: 8px;
        overflow: hidden;
    `;

    // Header with refresh button (Story 35.4 AC 35.4.5)
    const header = createPanelHeader(
        title,
        state,
        showSearch,
        onFilterChange,
        () => renderItems(),
        apiClient ? () => fetchMediaItems() : undefined // Show refresh button only in dynamic mode
    );
    container.appendChild(header);

    // Content area
    const content = document.createElement('div');
    content.className = 'media-panel-content';
    content.style.cssText = `
        padding: 16px;
        max-height: 600px;
        overflow-y: auto;
    `;
    container.appendChild(content);

    /**
     * Story 35.4 AC 35.4.1: Fetch media items from backend
     * @param isRefresh - Whether this is a manual refresh (show different UI)
     */
    async function fetchMediaItems(isRefresh: boolean = false): Promise<void> {
        if (!apiClient || !state.conceptId) {
            return;
        }

        // Story 35.4 AC 35.4.2: Cancel any pending request
        if (currentAbortController) {
            currentAbortController.abort();
        }
        // Create new controller and capture it for this fetch
        const myAbortController = new AbortController();
        currentAbortController = myAbortController;

        // Story 35.4 AC 35.4.3: Set loading state
        state.isLoading = true;
        state.error = null;
        renderItems();

        try {
            // Story 35.4 AC 35.4.1: Call ApiClient.getMediaByConceptId()
            const mediaItems = await apiClient.getMediaByConceptId(state.conceptId);

            // Check if THIS request was cancelled during fetch (not a later one)
            if (myAbortController.signal.aborted) {
                return;
            }

            // Story 35.4 AC 35.4.1: Map backend response to MediaItem[]
            state.items = mediaItems;
            state.error = null;

            // Story 35.4 AC 35.4.5: Callback after successful refresh
            if (onRefresh) {
                onRefresh(mediaItems);
            }

            console.log(`[MediaPanel] Loaded ${mediaItems.length} items for concept: ${state.conceptId}`);
        } catch (error) {
            // Check if request was cancelled (not a real error)
            if (error instanceof Error && error.name === 'AbortError') {
                return;
            }

            // Also check if this request was aborted during the fetch
            if (myAbortController.signal.aborted) {
                return;
            }

            // Story 35.4 AC 35.4.4: Handle errors
            const apiError = error instanceof ApiError
                ? error
                : new ApiError(
                    error instanceof Error ? error.message : 'Unknown error',
                    'UnknownError',
                    0
                );

            state.error = apiError;
            state.items = [];

            // Story 35.4 AC 35.4.5: Callback with error
            if (onRefresh) {
                onRefresh([], apiError);
            }

            console.error(`[MediaPanel] Error fetching media for concept ${state.conceptId}:`, apiError.message);
        } finally {
            state.isLoading = false;
            currentAbortController = null;
            renderItems();
        }
    }

    /**
     * Story 35.4 AC 35.4.2: Handle concept change with debouncing
     */
    function handleConceptChange(newConceptId: string): void {
        // Cancel any pending debounce
        if (debounceTimer) {
            clearTimeout(debounceTimer);
        }

        // Story 35.4 AC 35.4.2: Cancel ongoing request
        if (currentAbortController) {
            currentAbortController.abort();
            currentAbortController = null;
        }

        // Update concept ID
        state.conceptId = newConceptId;

        // Story 35.4 AC 35.4.2: Debounce the fetch (300ms)
        debounceTimer = setTimeout(() => {
            fetchMediaItems();
            debounceTimer = null;
        }, CONCEPT_CHANGE_DEBOUNCE_MS);
    }

    /**
     * Render function with loading/error states (Story 35.4)
     */
    function renderItems() {
        content.innerHTML = '';

        // Story 35.4 AC 35.4.3: Update refresh button state based on loading
        const refreshBtn = container.querySelector('.media-panel-refresh-btn') as HTMLButtonElement | null;
        if (refreshBtn) {
            refreshBtn.disabled = state.isLoading;
            refreshBtn.style.opacity = state.isLoading ? '0.5' : '1';
            refreshBtn.style.cursor = state.isLoading ? 'not-allowed' : 'pointer';
        }

        // Story 35.4 AC 35.4.3: Show loading state
        if (state.isLoading) {
            content.appendChild(createLoadingState());
            return;
        }

        // Story 35.4 AC 35.4.4: Show error state
        if (state.error) {
            content.appendChild(createErrorState(state.error, () => fetchMediaItems(true)));
            return;
        }

        // Story 35.11 AC 35.11.2: Show degradation notice when search is in text (keyword) mode
        if (state.searchMode === 'text') {
            const notice = document.createElement('div');
            notice.className = 'media-panel-degradation-notice';
            notice.textContent = '当前使用关键字搜索（语义搜索不可用），结果可能不完整';
            content.appendChild(notice);
        }

        const filteredItems = filterAndSortItems(state.items, state);

        if (filteredItems.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'media-panel-empty';
            emptyState.style.cssText = `
                text-align: center;
                padding: 40px;
                color: var(--text-muted);
            `;
            emptyState.textContent = state.searchQuery
                ? `未找到匹配 "${state.searchQuery}" 的资料`
                : '暂无关联资料';
            content.appendChild(emptyState);
            return;
        }

        const list = createMediaList({
            items: filteredItems,
            mode: state.displayMode,
            thumbnailSize,
            showRelevance,
            onItemClick
        });
        content.appendChild(list);
    }

    /**
     * Story 35.11 AC 35.11.2: Update search mode and re-render degradation notice
     */
    function setSearchMode(mode: 'vector' | 'text' | null): void {
        state.searchMode = mode;
        renderItems();
    }

    /**
     * Story 35.11 AC 35.11.1 + AC 35.11.2: Perform backend semantic search
     * and wire search_mode into the degradation notice.
     *
     * This connects ApiClient.searchMultimodal() → MediaPanel.setSearchMode(),
     * ensuring the degradation notice appears when backend falls back to text search.
     */
    async function performApiSearch(
        query: string,
        options?: { limit?: number; media_types?: Array<'image' | 'pdf' | 'audio' | 'video'> }
    ): Promise<void> {
        if (!apiClient) {
            return;
        }

        state.isLoading = true;
        state.error = null;
        renderItems();

        try {
            const result = await apiClient.searchMultimodal(query, options);

            state.items = result.items as MediaItem[];
            state.searchMode = result.searchMode;
            state.error = null;

            console.log(
                `[MediaPanel] Search returned ${result.items.length} items (mode: ${result.searchMode})`
            );
        } catch (error) {
            const apiError = error instanceof ApiError
                ? error
                : new ApiError(
                    error instanceof Error ? error.message : 'Search failed',
                    'UnknownError',
                    0
                );
            state.error = apiError;
            state.items = [];
            state.searchMode = null;
        } finally {
            state.isLoading = false;
            renderItems();
        }
    }

    // Story 35.4: Initial fetch if apiClient and conceptId are provided
    if (apiClient && conceptId) {
        fetchMediaItems();
    } else {
        // Static mode: just render
        renderItems();
    }

    // Store references for external access
    (container as any).__state = state;
    (container as any).__render = renderItems;
    (container as any).__fetchMediaItems = fetchMediaItems;
    (container as any).__handleConceptChange = handleConceptChange;
    (container as any).__setSearchMode = setSearchMode;
    (container as any).__performApiSearch = performApiSearch;
    (container as any).__cleanup = () => {
        // Story 35.4: Cleanup on unmount
        if (currentAbortController) {
            currentAbortController.abort();
        }
        if (debounceTimer) {
            clearTimeout(debounceTimer);
        }
    };

    return container;
}

/**
 * Story 35.4 AC 35.4.3: Create loading state UI
 *
 * Shows a spinner/skeleton while data is being fetched.
 */
function createLoadingState(): HTMLElement {
    const container = document.createElement('div');
    container.className = 'media-panel-loading';
    container.style.cssText = `
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
        gap: 12px;
    `;

    // Spinner
    const spinner = document.createElement('div');
    spinner.className = 'media-panel-spinner';
    spinner.style.cssText = `
        width: 32px;
        height: 32px;
        border: 3px solid var(--background-modifier-border);
        border-top-color: var(--interactive-accent);
        border-radius: 50%;
        animation: media-panel-spin 1s linear infinite;
    `;
    container.appendChild(spinner);

    // Loading text
    const text = document.createElement('div');
    text.textContent = '加载中...';
    text.style.cssText = `
        color: var(--text-muted);
        font-size: 14px;
    `;
    container.appendChild(text);

    // Add keyframes for spinner animation
    if (!document.getElementById('media-panel-spinner-style')) {
        const style = document.createElement('style');
        style.id = 'media-panel-spinner-style';
        style.textContent = `
            @keyframes media-panel-spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }

    return container;
}

/**
 * Story 35.4 AC 35.4.4: Create error state UI
 *
 * Shows error message with optional retry button.
 * @param error - The API error that occurred
 * @param onRetry - Callback for retry button (only shown if error is retryable)
 */
function createErrorState(error: ApiError, onRetry?: () => void): HTMLElement {
    const container = document.createElement('div');
    container.className = 'media-panel-error';
    container.style.cssText = `
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
        gap: 16px;
        text-align: center;
    `;

    // Error icon
    const icon = document.createElement('div');
    icon.innerHTML = '⚠️';
    icon.style.fontSize = '32px';
    container.appendChild(icon);

    // Error message (user-friendly)
    const message = document.createElement('div');
    message.textContent = error.getUserFriendlyMessage();
    message.style.cssText = `
        color: var(--text-muted);
        font-size: 14px;
        max-width: 300px;
    `;
    container.appendChild(message);

    // Story 35.4 AC 35.4.4: Show retry button for retryable errors
    if (error.isRetryable && onRetry) {
        const retryBtn = document.createElement('button');
        retryBtn.textContent = '重试';
        retryBtn.className = 'media-panel-retry-btn';
        retryBtn.style.cssText = `
            padding: 8px 16px;
            background: var(--interactive-accent);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.2s;
        `;
        retryBtn.addEventListener('click', onRetry);
        retryBtn.addEventListener('mouseenter', () => {
            retryBtn.style.background = 'var(--interactive-accent-hover)';
        });
        retryBtn.addEventListener('mouseleave', () => {
            retryBtn.style.background = 'var(--interactive-accent)';
        });
        container.appendChild(retryBtn);
    }

    // Story 35.4 AC 35.4.4: Error details expandable (development mode)
    // Check if we're in development by looking for Obsidian debug flag
    const isDev = (window as any).DEBUG || (window as any).app?.vault?.adapter?.basePath?.includes('dev');
    if (isDev) {
        const details = document.createElement('details');
        details.style.cssText = `
            margin-top: 8px;
            font-size: 11px;
            color: var(--text-faint);
            max-width: 300px;
            text-align: left;
        `;

        const summary = document.createElement('summary');
        summary.textContent = '错误详情';
        summary.style.cursor = 'pointer';
        details.appendChild(summary);

        const detailsContent = document.createElement('pre');
        detailsContent.style.cssText = `
            white-space: pre-wrap;
            word-break: break-all;
            margin-top: 8px;
            padding: 8px;
            background: var(--background-secondary);
            border-radius: 4px;
        `;
        detailsContent.textContent = JSON.stringify({
            type: error.type,
            statusCode: error.statusCode,
            message: error.message,
            details: error.details,
            bugId: error.bugId
        }, null, 2);
        details.appendChild(detailsContent);

        container.appendChild(details);
    }

    return container;
}

/**
 * Creates the panel header with controls.
 *
 * Story 35.4 AC 35.4.5: Added onRefresh parameter for refresh button
 */
function createPanelHeader(
    title: string,
    state: PanelState,
    showSearch: boolean,
    onFilterChange?: (filter: MediaType) => void,
    onUpdate?: () => void,
    onRefresh?: () => void // Story 35.4: Refresh callback
): HTMLElement {
    const header = document.createElement('div');
    header.className = 'media-panel-header';
    header.style.cssText = `
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        align-items: center;
        padding: 12px 16px;
        background: var(--background-primary);
        border-bottom: 1px solid var(--background-modifier-border);
    `;

    // Title
    const titleEl = document.createElement('h3');
    titleEl.textContent = title;
    titleEl.style.cssText = `
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--text-normal);
    `;
    header.appendChild(titleEl);

    // Spacer
    const spacer = document.createElement('div');
    spacer.style.flex = '1';
    header.appendChild(spacer);

    // Filter buttons
    const filterGroup = document.createElement('div');
    filterGroup.className = 'filter-group';
    filterGroup.style.cssText = `
        display: flex;
        gap: 4px;
    `;

    const filters: { type: MediaType; label: string; icon: string }[] = [
        { type: 'all', label: '全部', icon: '📁' },
        { type: 'image', label: '图片', icon: '🖼️' },
        { type: 'pdf', label: 'PDF', icon: '📄' },
        { type: 'audio', label: '音频', icon: '🎵' },
        { type: 'video', label: '视频', icon: '🎬' }
    ];

    filters.forEach(({ type, label, icon }) => {
        const btn = document.createElement('button');
        btn.className = `filter-btn ${state.filter === type ? 'active' : ''}`;
        btn.innerHTML = `${icon} <span class="filter-label">${label}</span>`;
        btn.title = label;
        btn.style.cssText = `
            padding: 6px 12px;
            border: 1px solid var(--background-modifier-border);
            border-radius: 4px;
            background: ${state.filter === type ? 'var(--interactive-accent)' : 'var(--background-secondary)'};
            color: ${state.filter === type ? 'white' : 'var(--text-normal)'};
            cursor: pointer;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 4px;
            transition: all 0.2s;
        `;

        btn.addEventListener('click', () => {
            // Update all buttons
            filterGroup.querySelectorAll('.filter-btn').forEach(b => {
                (b as HTMLElement).style.background = 'var(--background-secondary)';
                (b as HTMLElement).style.color = 'var(--text-normal)';
                b.classList.remove('active');
            });
            btn.style.background = 'var(--interactive-accent)';
            btn.style.color = 'white';
            btn.classList.add('active');

            state.filter = type;
            if (onFilterChange) onFilterChange(type);
            if (onUpdate) onUpdate();
        });

        filterGroup.appendChild(btn);
    });

    header.appendChild(filterGroup);

    // Search box
    if (showSearch) {
        const searchContainer = document.createElement('div');
        searchContainer.className = 'search-container';
        searchContainer.style.cssText = `
            position: relative;
            width: 200px;
        `;

        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.className = 'media-search-input';
        searchInput.placeholder = '搜索资料...';
        searchInput.style.cssText = `
            width: 100%;
            padding: 8px 12px 8px 32px;
            border: 1px solid var(--background-modifier-border);
            border-radius: 4px;
            background: var(--background-primary);
            color: var(--text-normal);
            font-size: 13px;
        `;

        const searchIcon = document.createElement('span');
        searchIcon.innerHTML = '🔍';
        searchIcon.style.cssText = `
            position: absolute;
            left: 8px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 14px;
            pointer-events: none;
        `;

        searchInput.addEventListener('input', () => {
            state.searchQuery = searchInput.value;
            if (onUpdate) onUpdate();
        });

        searchContainer.appendChild(searchIcon);
        searchContainer.appendChild(searchInput);
        header.appendChild(searchContainer);
    }

    // View toggle
    const viewToggle = document.createElement('div');
    viewToggle.className = 'view-toggle';
    viewToggle.style.cssText = `
        display: flex;
        gap: 4px;
    `;

    const gridBtn = createViewToggleBtn('⊞', '网格视图', state.displayMode === 'grid', () => {
        state.displayMode = 'grid';
        gridBtn.style.background = 'var(--interactive-accent)';
        gridBtn.style.color = 'white';
        listBtn.style.background = 'var(--background-secondary)';
        listBtn.style.color = 'var(--text-normal)';
        if (onUpdate) onUpdate();
    });

    const listBtn = createViewToggleBtn('☰', '列表视图', state.displayMode === 'list', () => {
        state.displayMode = 'list';
        listBtn.style.background = 'var(--interactive-accent)';
        listBtn.style.color = 'white';
        gridBtn.style.background = 'var(--background-secondary)';
        gridBtn.style.color = 'var(--text-normal)';
        if (onUpdate) onUpdate();
    });

    viewToggle.appendChild(gridBtn);
    viewToggle.appendChild(listBtn);
    header.appendChild(viewToggle);

    // Story 35.4 AC 35.4.5: Refresh button (only shown in dynamic mode)
    if (onRefresh) {
        const refreshBtn = document.createElement('button');
        refreshBtn.className = 'media-panel-refresh-btn';
        refreshBtn.innerHTML = '🔄';
        refreshBtn.title = '刷新';
        refreshBtn.style.cssText = `
            width: 32px;
            height: 32px;
            border: 1px solid var(--background-modifier-border);
            border-radius: 4px;
            background: var(--background-secondary);
            color: var(--text-normal);
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        `;

        // Disable during loading
        if (state.isLoading) {
            refreshBtn.disabled = true;
            refreshBtn.style.opacity = '0.5';
            refreshBtn.style.cursor = 'not-allowed';
        }

        refreshBtn.addEventListener('click', () => {
            if (!state.isLoading) {
                onRefresh();
            }
        });

        refreshBtn.addEventListener('mouseenter', () => {
            if (!state.isLoading) {
                refreshBtn.style.background = 'var(--background-modifier-hover)';
            }
        });
        refreshBtn.addEventListener('mouseleave', () => {
            refreshBtn.style.background = 'var(--background-secondary)';
        });

        header.appendChild(refreshBtn);
    }

    return header;
}

/**
 * Creates a view toggle button.
 */
function createViewToggleBtn(
    icon: string,
    title: string,
    active: boolean,
    onClick: () => void
): HTMLButtonElement {
    const btn = document.createElement('button');
    btn.innerHTML = icon;
    btn.title = title;
    btn.style.cssText = `
        width: 32px;
        height: 32px;
        border: 1px solid var(--background-modifier-border);
        border-radius: 4px;
        background: ${active ? 'var(--interactive-accent)' : 'var(--background-secondary)'};
        color: ${active ? 'white' : 'var(--text-normal)'};
        cursor: pointer;
        font-size: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    btn.addEventListener('click', onClick);
    return btn;
}

/**
 * Filters and sorts media items based on panel state.
 */
function filterAndSortItems(items: MediaItem[], state: PanelState): MediaItem[] {
    let filtered = items;

    // Type filter
    if (state.filter !== 'all') {
        filtered = filtered.filter(item => item.type === state.filter);
    }

    // Search filter
    if (state.searchQuery) {
        const query = state.searchQuery.toLowerCase();
        filtered = filtered.filter(item =>
            item.title?.toLowerCase().includes(query) ||
            item.path.toLowerCase().includes(query) ||
            (item.metadata?.description as string | undefined)?.toLowerCase().includes(query)
        );
    }

    // Sort
    filtered = [...filtered].sort((a, b) => {
        switch (state.sortBy) {
            case 'relevance':
                return b.relevanceScore - a.relevanceScore;
            case 'name':
                return (a.title || a.path).localeCompare(b.title || b.path);
            case 'type':
                return a.type.localeCompare(b.type);
            case 'date':
                return ((b.metadata?.date as number) || 0) - ((a.metadata?.date as number) || 0);
            default:
                return 0;
        }
    });

    return filtered;
}

/**
 * Creates a media list component.
 */
export function createMediaList(props: MediaListProps): HTMLElement {
    const {
        items,
        mode,
        thumbnailSize = 150,
        showRelevance = true,
        onItemClick
    } = props;

    const container = document.createElement('div');
    container.className = `media-list media-list-${mode}`;

    if (mode === 'grid') {
        container.style.cssText = `
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(${thumbnailSize}px, 1fr));
            gap: 16px;
        `;
    } else {
        container.style.cssText = `
            display: flex;
            flex-direction: column;
            gap: 8px;
        `;
    }

    items.forEach(item => {
        const itemEl = createMediaItem(item, mode, thumbnailSize, showRelevance, onItemClick);
        container.appendChild(itemEl);
    });

    return container;
}

/**
 * Creates a single media item element.
 */
function createMediaItem(
    item: MediaItem,
    mode: 'grid' | 'list',
    thumbnailSize: number,
    showRelevance: boolean,
    onItemClick?: (item: MediaItem) => void
): HTMLElement {
    const container = document.createElement('div');
    container.className = 'media-item';
    container.dataset.id = item.id;
    container.dataset.type = item.type;

    if (mode === 'grid') {
        container.style.cssText = `
            background: var(--background-primary);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        `;

        // Preview area
        const preview = createItemPreview(item, thumbnailSize);
        container.appendChild(preview);

        // Info area
        const info = document.createElement('div');
        info.className = 'media-item-info';
        info.style.cssText = `
            padding: 12px;
        `;

        // Title
        const titleEl = document.createElement('div');
        titleEl.className = 'media-item-title';
        titleEl.textContent = item.title || item.path.split('/').pop() || 'Untitled';
        titleEl.style.cssText = `
            font-size: 13px;
            font-weight: 500;
            color: var(--text-normal);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        `;
        info.appendChild(titleEl);

        // Relevance
        if (showRelevance) {
            const relevanceEl = document.createElement('div');
            relevanceEl.className = 'media-item-relevance';
            relevanceEl.textContent = `相关度: ${Math.round(item.relevanceScore * 100)}%`;
            relevanceEl.style.cssText = `
                font-size: 11px;
                color: var(--text-muted);
                margin-top: 4px;
            `;
            info.appendChild(relevanceEl);
        }

        container.appendChild(info);
    } else {
        // List mode
        container.style.cssText = `
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            background: var(--background-primary);
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;
        `;

        // Type icon
        const icon = document.createElement('span');
        icon.className = 'media-item-icon';
        icon.innerHTML = getTypeIcon(item.type);
        icon.style.fontSize = '24px';
        container.appendChild(icon);

        // Info
        const info = document.createElement('div');
        info.style.cssText = `
            flex: 1;
            min-width: 0;
        `;

        const titleEl = document.createElement('div');
        titleEl.textContent = item.title || item.path.split('/').pop() || 'Untitled';
        titleEl.style.cssText = `
            font-weight: 500;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        `;
        info.appendChild(titleEl);

        const pathEl = document.createElement('div');
        pathEl.textContent = item.path;
        pathEl.style.cssText = `
            font-size: 12px;
            color: var(--text-muted);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        `;
        info.appendChild(pathEl);

        container.appendChild(info);

        // Relevance badge
        if (showRelevance) {
            const badge = document.createElement('span');
            badge.className = 'relevance-badge';
            badge.textContent = `${Math.round(item.relevanceScore * 100)}%`;
            badge.style.cssText = `
                padding: 4px 8px;
                background: var(--interactive-accent);
                color: white;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
            `;
            container.appendChild(badge);
        }
    }

    // Hover effects
    container.addEventListener('mouseenter', () => {
        if (mode === 'grid') {
            container.style.transform = 'translateY(-2px)';
            container.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        } else {
            container.style.background = 'var(--background-modifier-hover)';
        }
    });
    container.addEventListener('mouseleave', () => {
        if (mode === 'grid') {
            container.style.transform = 'none';
            container.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        } else {
            container.style.background = 'var(--background-primary)';
        }
    });

    // Click handler
    container.addEventListener('click', () => {
        if (onItemClick) onItemClick(item);
    });

    return container;
}

/**
 * Creates the preview element for a media item.
 */
function createItemPreview(item: MediaItem, size: number): HTMLElement {
    const preview = document.createElement('div');
    preview.className = 'media-item-preview';
    preview.style.cssText = `
        width: 100%;
        height: ${size}px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--background-secondary);
    `;

    switch (item.type) {
        case 'image':
            const img = document.createElement('img');
            img.src = item.path;
            img.alt = item.title || '';
            img.style.cssText = `
                width: 100%;
                height: 100%;
                object-fit: cover;
            `;
            img.loading = 'lazy';
            preview.appendChild(img);
            break;

        case 'pdf':
            const pdfIcon = document.createElement('div');
            pdfIcon.innerHTML = `
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <text x="7" y="17" font-size="6" fill="currentColor" stroke="none">PDF</text>
                </svg>
            `;
            pdfIcon.style.color = 'var(--text-muted)';
            preview.appendChild(pdfIcon);
            break;

        case 'audio':
            const audioIcon = document.createElement('div');
            audioIcon.innerHTML = '🎵';
            audioIcon.style.fontSize = '48px';
            preview.appendChild(audioIcon);
            break;

        case 'video':
            if (item.thumbnail) {
                const thumb = document.createElement('img');
                thumb.src = item.thumbnail;
                thumb.style.cssText = `
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                `;
                preview.appendChild(thumb);
            } else {
                const videoIcon = document.createElement('div');
                videoIcon.innerHTML = '🎬';
                videoIcon.style.fontSize = '48px';
                preview.appendChild(videoIcon);
            }

            // Play overlay
            const playOverlay = document.createElement('div');
            playOverlay.style.cssText = `
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 48px;
                height: 48px;
                background: rgba(0,0,0,0.6);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 20px;
            `;
            playOverlay.innerHTML = '▶';
            preview.style.position = 'relative';
            preview.appendChild(playOverlay);
            break;
    }

    return preview;
}

/**
 * Gets the icon for a media type.
 */
function getTypeIcon(type: Exclude<MediaType, 'all'>): string {
    switch (type) {
        case 'image': return '🖼️';
        case 'pdf': return '📄';
        case 'audio': return '🎵';
        case 'video': return '🎬';
        default: return '📁';
    }
}

/**
 * Updates the media panel with new items.
 */
export function updateMediaPanel(container: HTMLElement, items: MediaItem[]): void {
    const render = (container as any).__render;
    if (render) {
        // Store new items and re-render
        const state = (container as any).__state;
        // The render function closes over the original items, so we need to update via DOM
        const content = container.querySelector('.media-panel-content');
        if (content) {
            content.innerHTML = '';
            const list = createMediaList({
                items: filterAndSortItems(items, state),
                mode: state.displayMode,
                showRelevance: true,
                onItemClick: undefined
            });
            content.appendChild(list);
        }
    }
}

/**
 * Gets the current filter state of a media panel.
 */
export function getMediaPanelFilter(container: HTMLElement): MediaType {
    const state = (container as any).__state as PanelState | undefined;
    return state?.filter || 'all';
}

/**
 * Sets the filter for a media panel.
 */
export function setMediaPanelFilter(container: HTMLElement, filter: MediaType): void {
    const state = (container as any).__state as PanelState | undefined;
    const render = (container as any).__render;
    if (state && render) {
        state.filter = filter;
        render();
    }
}

/**
 * Story 35.4 AC 35.4.2: Update the concept ID for a media panel.
 *
 * This triggers a new data fetch with debouncing and cancels any pending requests.
 * Use this when the user selects a different Canvas node.
 *
 * @param container - The MediaPanel container element
 * @param conceptId - The new concept ID to load media for
 *
 * @example
 * ```typescript
 * // When user selects a new node
 * canvas.on('node:selected', (node) => {
 *     updateMediaPanelConcept(mediaPanel, node.id);
 * });
 * ```
 */
export function updateMediaPanelConcept(container: HTMLElement, conceptId: string): void {
    const handleConceptChange = (container as any).__handleConceptChange;
    if (handleConceptChange) {
        handleConceptChange(conceptId);
    }
}

/**
 * Story 35.4: Cleanup media panel resources.
 *
 * Call this when the panel is being unmounted to:
 * - Cancel any pending API requests (AbortController)
 * - Clear any pending debounce timers
 *
 * @param container - The MediaPanel container element
 *
 * @example
 * ```typescript
 * // When panel is being removed
 * cleanupMediaPanel(mediaPanel);
 * mediaPanel.remove();
 * ```
 */
export function cleanupMediaPanel(container: HTMLElement): void {
    const cleanup = (container as any).__cleanup;
    if (cleanup) {
        cleanup();
    }
}

/**
 * Story 35.4: Check if a media panel is currently loading.
 *
 * @param container - The MediaPanel container element
 * @returns true if the panel is loading data
 */
export function isMediaPanelLoading(container: HTMLElement): boolean {
    const state = (container as any).__state as PanelState | undefined;
    return state?.isLoading || false;
}

/**
 * Story 35.4: Get the current error from a media panel.
 *
 * @param container - The MediaPanel container element
 * @returns The current ApiError or null if no error
 */
export function getMediaPanelError(container: HTMLElement): ApiError | null {
    const state = (container as any).__state as PanelState | undefined;
    return state?.error || null;
}

/**
 * Story 35.4: Manually trigger a refresh of the media panel.
 *
 * @param container - The MediaPanel container element
 */
export function refreshMediaPanel(container: HTMLElement): void {
    const fetchMediaItems = (container as any).__fetchMediaItems;
    if (fetchMediaItems) {
        fetchMediaItems(true);
    }
}
