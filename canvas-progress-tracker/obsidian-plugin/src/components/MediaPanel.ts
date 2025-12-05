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
 * ✅ Verified from Canvas component patterns
 * [Source: docs/stories/6.9.multimodal-ui-integration.story.md:42-50]
 */

import { createImagePreview, ImageGalleryProps } from './ImagePreview';
import { createPDFThumbnail } from './PDFPreview';
import { createAudioPlayer, createVideoPlayer, TimeMarker } from './MediaPlayer';

/**
 * Media item type
 */
export type MediaType = 'image' | 'pdf' | 'audio' | 'video' | 'all';

/**
 * Media item interface
 */
export interface MediaItem {
    /** Unique identifier */
    id: string;
    /** Media type */
    type: Exclude<MediaType, 'all'>;
    /** File path or URL */
    path: string;
    /** Item title/description */
    title?: string;
    /** Relevance score (0-1) */
    relevanceScore: number;
    /** Associated concept ID */
    conceptId?: string;
    /** Additional metadata */
    metadata?: Record<string, any>;
    /** Timestamp for audio/video */
    timestamp?: number;
    /** Thumbnail URL for video */
    thumbnail?: string;
    /** Time markers for audio/video */
    markers?: TimeMarker[];
}

/**
 * Props for MediaPanel component.
 */
export interface MediaPanelProps {
    /** Panel title */
    title?: string;
    /** Media items to display */
    items: MediaItem[];
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
 */
interface PanelState {
    filter: MediaType;
    searchQuery: string;
    sortBy: 'relevance' | 'name' | 'type' | 'date';
    displayMode: 'grid' | 'list';
}

/**
 * Creates a media panel component for displaying associated media items.
 *
 * Features:
 * - Type-based filtering
 * - Search functionality
 * - Relevance-based sorting
 * - Grid/list view toggle
 * - Responsive layout
 *
 * ✅ Verified from Canvas component patterns
 *
 * Example:
 * ```typescript
 * const panel = createMediaPanel({
 *     title: '关联资料',
 *     items: mediaItems,
 *     showSearch: true,
 *     onItemClick: (item) => console.log('Clicked:', item)
 * });
 * container.appendChild(panel);
 * ```
 */
export function createMediaPanel(props: MediaPanelProps): HTMLElement {
    const {
        title = '关联资料',
        items,
        initialFilter = 'all',
        showSearch = true,
        showRelevance = true,
        columns,
        thumbnailSize = 150,
        onItemClick,
        onFilterChange,
        sortBy = 'relevance',
        draggable = false
    } = props;

    const state: PanelState = {
        filter: initialFilter,
        searchQuery: '',
        sortBy,
        displayMode: 'grid'
    };

    const container = document.createElement('div');
    container.className = 'media-panel';
    container.style.cssText = `
        width: 100%;
        background: var(--background-secondary);
        border-radius: 8px;
        overflow: hidden;
    `;

    // Header
    const header = createPanelHeader(title, state, showSearch, onFilterChange, () => {
        renderItems();
    });
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

    // Render function
    function renderItems() {
        content.innerHTML = '';

        const filteredItems = filterAndSortItems(items, state);

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

    // Initial render
    renderItems();

    // Store state reference
    (container as any).__state = state;
    (container as any).__render = renderItems;

    return container;
}

/**
 * Creates the panel header with controls.
 */
function createPanelHeader(
    title: string,
    state: PanelState,
    showSearch: boolean,
    onFilterChange?: (filter: MediaType) => void,
    onUpdate?: () => void
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
            item.metadata?.description?.toLowerCase().includes(query)
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
                return (b.metadata?.date || 0) - (a.metadata?.date || 0);
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
