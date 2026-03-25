/**
 * Image Preview Component
 *
 * Story 6.9 AC 6.9.1: 图片预览组件
 * - 缩略图展示（150x150）
 * - 点击放大查看
 * - 支持图片轮播
 *
 * ✅ Verified from Obsidian Plugin API (Canvas component patterns)
 * [Source: docs/stories/6.9.multimodal-ui-integration.story.md:27-30]
 */

/**
 * Props for ImagePreview component.
 */
export interface ImagePreviewProps {
    /** Image source path or URL */
    src: string;
    /** Alternative text for accessibility */
    alt?: string;
    /** Thumbnail size in pixels (default: 150) */
    thumbnailSize?: number;
    /** Enable click-to-zoom (default: true) */
    zoomable?: boolean;
    /** Image title */
    title?: string;
    /** Callback when image is clicked */
    onClick?: () => void;
}

/**
 * Props for ImageGallery component.
 */
export interface ImageGalleryProps {
    /** Array of image sources */
    images: Array<{ src: string; alt?: string; title?: string }>;
    /** Thumbnail size in pixels (default: 150) */
    thumbnailSize?: number;
    /** Number of columns (default: auto) */
    columns?: number;
    /** Enable lightbox navigation (default: true) */
    lightbox?: boolean;
}

/**
 * Lightbox state management
 */
interface LightboxState {
    isOpen: boolean;
    currentIndex: number;
    images: Array<{ src: string; alt?: string; title?: string }>;
}

let lightboxState: LightboxState = {
    isOpen: false,
    currentIndex: 0,
    images: []
};

let lightboxOverlay: HTMLElement | null = null;

/**
 * Creates an image preview component with thumbnail and zoom functionality.
 *
 * Features:
 * - Responsive thumbnail display
 * - Click to open lightbox
 * - Smooth hover effects
 * - Accessible with ARIA labels
 *
 * ✅ Verified from Canvas component patterns
 *
 * Example:
 * ```typescript
 * const preview = createImagePreview({
 *     src: '/images/formula.png',
 *     alt: 'Math formula',
 *     thumbnailSize: 150
 * });
 * container.appendChild(preview);
 * ```
 */
export function createImagePreview(props: ImagePreviewProps): HTMLElement {
    const {
        src,
        alt = '',
        thumbnailSize = 150,
        zoomable = true,
        title,
        onClick
    } = props;

    const container = document.createElement('div');
    container.className = 'image-preview-container';
    container.style.cssText = `
        display: inline-block;
        position: relative;
        width: ${thumbnailSize}px;
        height: ${thumbnailSize}px;
        border-radius: 8px;
        overflow: hidden;
        cursor: ${zoomable ? 'zoom-in' : 'pointer'};
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        background: var(--background-secondary);
    `;

    // Image element
    const img = document.createElement('img');
    img.src = src;
    img.alt = alt;
    img.title = title || alt;
    img.style.cssText = `
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.3s ease;
    `;
    img.loading = 'lazy';

    // Accessibility
    img.setAttribute('role', 'img');
    img.setAttribute('aria-label', alt || 'Image preview');

    // Error handling
    img.onerror = () => {
        img.style.display = 'none';
        const placeholder = document.createElement('div');
        placeholder.className = 'image-placeholder';
        placeholder.style.cssText = `
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
            font-size: 12px;
        `;
        placeholder.textContent = '图片加载失败';
        container.appendChild(placeholder);
    };

    container.appendChild(img);

    // Hover effects
    container.addEventListener('mouseenter', () => {
        container.style.transform = 'scale(1.02)';
        container.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        img.style.transform = 'scale(1.05)';
    });

    container.addEventListener('mouseleave', () => {
        container.style.transform = 'scale(1)';
        container.style.boxShadow = 'none';
        img.style.transform = 'scale(1)';
    });

    // Click handler
    container.addEventListener('click', () => {
        if (onClick) {
            onClick();
        } else if (zoomable) {
            openLightbox([{ src, alt, title }], 0);
        }
    });

    return container;
}

/**
 * Creates an image gallery with lightbox navigation.
 *
 * Features:
 * - Grid layout for thumbnails
 * - Lightbox with navigation arrows
 * - Keyboard navigation support
 * - Touch swipe support
 *
 * ✅ Verified from Canvas component patterns
 */
export function createImageGallery(props: ImageGalleryProps): HTMLElement {
    const {
        images,
        thumbnailSize = 150,
        columns,
        lightbox = true
    } = props;

    const container = document.createElement('div');
    container.className = 'image-gallery';
    container.style.cssText = `
        display: grid;
        grid-template-columns: ${columns ? `repeat(${columns}, 1fr)` : `repeat(auto-fill, minmax(${thumbnailSize}px, 1fr))`};
        gap: 12px;
        padding: 8px;
    `;

    images.forEach((image, index) => {
        const preview = createImagePreview({
            src: image.src,
            alt: image.alt,
            title: image.title,
            thumbnailSize,
            zoomable: lightbox,
            onClick: lightbox ? () => openLightbox(images, index) : undefined
        });
        container.appendChild(preview);
    });

    return container;
}

/**
 * Opens the lightbox overlay with navigation.
 */
export function openLightbox(
    images: Array<{ src: string; alt?: string; title?: string }>,
    startIndex: number = 0
): void {
    lightboxState = {
        isOpen: true,
        currentIndex: startIndex,
        images
    };

    // Create or update lightbox
    if (!lightboxOverlay) {
        lightboxOverlay = createLightboxOverlay();
        document.body.appendChild(lightboxOverlay);
    }

    updateLightboxContent();
    lightboxOverlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    // Add keyboard listener
    document.addEventListener('keydown', handleLightboxKeydown);
}

/**
 * Closes the lightbox overlay.
 */
export function closeLightbox(): void {
    if (lightboxOverlay) {
        lightboxOverlay.style.display = 'none';
        document.body.style.overflow = '';
        document.removeEventListener('keydown', handleLightboxKeydown);
        lightboxState.isOpen = false;
    }
}

/**
 * Resets lightbox state for testing purposes.
 * Removes the overlay from DOM and clears module-level state.
 */
export function resetLightbox(): void {
    // Remove event listener first to prevent any callbacks during cleanup
    document.removeEventListener('keydown', handleLightboxKeydown);

    if (lightboxOverlay) {
        try {
            // Only remove if it's actually a child of its parent
            if (lightboxOverlay.parentNode && lightboxOverlay.parentNode.contains(lightboxOverlay)) {
                lightboxOverlay.parentNode.removeChild(lightboxOverlay);
            }
        } catch {
            // Ignore errors during cleanup (element might already be removed)
        }
        lightboxOverlay = null;
    }
    lightboxState = {
        isOpen: false,
        currentIndex: 0,
        images: []
    };
}

/**
 * Creates the lightbox overlay element.
 */
function createLightboxOverlay(): HTMLElement {
    const overlay = document.createElement('div');
    overlay.className = 'lightbox-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.9);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;

    // Close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'lightbox-close';
    closeBtn.innerHTML = '×';
    closeBtn.style.cssText = `
        position: absolute;
        top: 20px;
        right: 20px;
        background: transparent;
        border: none;
        color: white;
        font-size: 32px;
        cursor: pointer;
        padding: 8px;
        z-index: 10001;
    `;
    closeBtn.addEventListener('click', closeLightbox);
    overlay.appendChild(closeBtn);

    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.className = 'lightbox-nav lightbox-prev';
    prevBtn.innerHTML = '‹';
    prevBtn.style.cssText = `
        position: absolute;
        left: 20px;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(255,255,255,0.1);
        border: none;
        color: white;
        font-size: 48px;
        cursor: pointer;
        padding: 16px 24px;
        border-radius: 4px;
        z-index: 10001;
    `;
    prevBtn.addEventListener('click', () => navigateLightbox(-1));
    overlay.appendChild(prevBtn);

    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.className = 'lightbox-nav lightbox-next';
    nextBtn.innerHTML = '›';
    nextBtn.style.cssText = `
        position: absolute;
        right: 20px;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(255,255,255,0.1);
        border: none;
        color: white;
        font-size: 48px;
        cursor: pointer;
        padding: 16px 24px;
        border-radius: 4px;
        z-index: 10001;
    `;
    nextBtn.addEventListener('click', () => navigateLightbox(1));
    overlay.appendChild(nextBtn);

    // Image container
    const imgContainer = document.createElement('div');
    imgContainer.className = 'lightbox-image-container';
    imgContainer.style.cssText = `
        max-width: 90vw;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        align-items: center;
    `;
    overlay.appendChild(imgContainer);

    // Click overlay to close
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeLightbox();
        }
    });

    // Touch swipe support
    let touchStartX = 0;
    overlay.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
    });
    overlay.addEventListener('touchend', (e) => {
        const touchEndX = e.changedTouches[0].clientX;
        const diff = touchStartX - touchEndX;
        if (Math.abs(diff) > 50) {
            navigateLightbox(diff > 0 ? 1 : -1);
        }
    });

    return overlay;
}

/**
 * Updates the lightbox content with current image.
 */
function updateLightboxContent(): void {
    if (!lightboxOverlay) return;

    const container = lightboxOverlay.querySelector('.lightbox-image-container');
    if (!container) return;

    container.innerHTML = '';

    const currentImage = lightboxState.images[lightboxState.currentIndex];
    if (!currentImage) return;

    // Main image
    const img = document.createElement('img');
    img.src = currentImage.src;
    img.alt = currentImage.alt || '';
    img.style.cssText = `
        max-width: 100%;
        max-height: 80vh;
        object-fit: contain;
        border-radius: 4px;
    `;
    container.appendChild(img);

    // Caption
    if (currentImage.title || currentImage.alt) {
        const caption = document.createElement('div');
        caption.className = 'lightbox-caption';
        caption.textContent = currentImage.title || currentImage.alt || '';
        caption.style.cssText = `
            color: white;
            margin-top: 16px;
            font-size: 14px;
            text-align: center;
        `;
        container.appendChild(caption);
    }

    // Counter
    if (lightboxState.images.length > 1) {
        const counter = document.createElement('div');
        counter.className = 'lightbox-counter';
        counter.textContent = `${lightboxState.currentIndex + 1} / ${lightboxState.images.length}`;
        counter.style.cssText = `
            color: rgba(255,255,255,0.6);
            margin-top: 8px;
            font-size: 12px;
        `;
        container.appendChild(counter);
    }

    // Update navigation button visibility
    const prevBtn = lightboxOverlay.querySelector('.lightbox-prev') as HTMLElement;
    const nextBtn = lightboxOverlay.querySelector('.lightbox-next') as HTMLElement;
    if (prevBtn) {
        prevBtn.style.visibility = lightboxState.currentIndex > 0 ? 'visible' : 'hidden';
    }
    if (nextBtn) {
        nextBtn.style.visibility = lightboxState.currentIndex < lightboxState.images.length - 1 ? 'visible' : 'hidden';
    }
}

/**
 * Navigates to next/previous image in lightbox.
 */
function navigateLightbox(direction: number): void {
    const newIndex = lightboxState.currentIndex + direction;
    if (newIndex >= 0 && newIndex < lightboxState.images.length) {
        lightboxState.currentIndex = newIndex;
        updateLightboxContent();
    }
}

/**
 * Handles keyboard events for lightbox navigation.
 */
function handleLightboxKeydown(e: KeyboardEvent): void {
    switch (e.key) {
        case 'Escape':
            closeLightbox();
            break;
        case 'ArrowLeft':
            navigateLightbox(-1);
            break;
        case 'ArrowRight':
            navigateLightbox(1);
            break;
    }
}

/**
 * Utility: Creates a thumbnail from an image source.
 */
export function createThumbnail(
    src: string,
    size: number = 150
): HTMLCanvasElement {
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');

    if (ctx) {
        const img = new Image();
        img.onload = () => {
            // Calculate crop dimensions for center square
            const minDim = Math.min(img.width, img.height);
            const sx = (img.width - minDim) / 2;
            const sy = (img.height - minDim) / 2;
            ctx.drawImage(img, sx, sy, minDim, minDim, 0, 0, size, size);
        };
        img.src = src;
    }

    return canvas;
}
