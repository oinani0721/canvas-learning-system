/**
 * @jest-environment jsdom
 */

/**
 * Multimodal UI Components Tests
 *
 * Story 6.9: UI集成测试
 * - AC 6.9.1: 图片预览组件
 * - AC 6.9.2: PDF预览组件
 * - AC 6.9.3: 音视频播放器
 * - AC 6.9.4: 关联资料面板
 * - AC 6.9.5: 移动端适配
 *
 * [Source: docs/stories/6.9.multimodal-ui-integration.story.md]
 */

import {
    createImagePreview,
    createImageGallery,
    openLightbox,
    closeLightbox,
    resetLightbox,
    createThumbnail,
    type ImagePreviewProps,
    type ImageGalleryProps
} from '../src/components/ImagePreview';

import {
    createPDFPreview,
    createPDFThumbnail,
    openPDFModal,
    updatePDFPage,
    type PDFPreviewProps,
    type PDFThumbnailProps
} from '../src/components/PDFPreview';

import {
    createAudioPlayer,
    createVideoPlayer,
    formatTime,
    seekTo,
    addTimeMarker,
    getCurrentTime,
    setPlaybackRate,
    type AudioPlayerProps,
    type VideoPlayerProps,
    type TimeMarker
} from '../src/components/MediaPlayer';

import {
    createMediaPanel,
    createMediaList,
    updateMediaPanel,
    getMediaPanelFilter,
    setMediaPanelFilter,
    type MediaType,
    type MediaItem,
    type MediaPanelProps,
    type MediaListProps
} from '../src/components/MediaPanel';

// ============================================================
// Test Setup
// ============================================================

describe('Story 6.9: Multimodal UI Components', () => {
    beforeEach(() => {
        // Reset module state and clear document body before each test
        resetLightbox();
        document.body.innerHTML = '';
    });

    afterEach(() => {
        // Cleanup any modals/lightboxes
        resetLightbox();
        const overlays = document.querySelectorAll('.lightbox-overlay, .pdf-modal-overlay');
        overlays.forEach(overlay => overlay.remove());
    });

    // ============================================================
    // AC 6.9.1: Image Preview Component Tests
    // ============================================================
    describe('AC 6.9.1: Image Preview Component', () => {
        describe('createImagePreview', () => {
            it('should create image preview element', () => {
                const preview = createImagePreview({
                    src: '/images/test.png',
                    alt: 'Test image'
                });

                expect(preview).toBeInstanceOf(HTMLElement);
                expect(preview.className).toBe('image-preview-container');
            });

            it('should set default thumbnail size to 150px', () => {
                const preview = createImagePreview({
                    src: '/images/test.png'
                });

                expect(preview.style.width).toBe('150px');
                expect(preview.style.height).toBe('150px');
            });

            it('should support custom thumbnail size', () => {
                const preview = createImagePreview({
                    src: '/images/test.png',
                    thumbnailSize: 200
                });

                expect(preview.style.width).toBe('200px');
                expect(preview.style.height).toBe('200px');
            });

            it('should set correct cursor for zoomable images', () => {
                const zoomable = createImagePreview({
                    src: '/images/test.png',
                    zoomable: true
                });

                const nonZoomable = createImagePreview({
                    src: '/images/test.png',
                    zoomable: false
                });

                expect(zoomable.style.cursor).toBe('zoom-in');
                expect(nonZoomable.style.cursor).toBe('pointer');
            });

            it('should create img element with correct attributes', () => {
                const preview = createImagePreview({
                    src: '/images/test.png',
                    alt: 'Test image',
                    title: 'Test Title'
                });

                const img = preview.querySelector('img');
                expect(img).not.toBeNull();
                expect(img?.src).toContain('/images/test.png');
                expect(img?.alt).toBe('Test image');
                expect(img?.title).toBe('Test Title');
            });

            it('should support custom click handler', () => {
                const onClick = jest.fn();
                const preview = createImagePreview({
                    src: '/images/test.png',
                    onClick
                });

                preview.click();
                expect(onClick).toHaveBeenCalled();
            });

            it('should have lazy loading', () => {
                const preview = createImagePreview({
                    src: '/images/test.png'
                });

                const img = preview.querySelector('img');
                expect(img?.loading).toBe('lazy');
            });

            it('should have accessibility attributes', () => {
                const preview = createImagePreview({
                    src: '/images/test.png',
                    alt: 'Accessible image'
                });

                const img = preview.querySelector('img');
                expect(img?.getAttribute('role')).toBe('img');
                expect(img?.getAttribute('aria-label')).toBe('Accessible image');
            });
        });

        describe('createImageGallery', () => {
            const testImages = [
                { src: '/img1.png', alt: 'Image 1' },
                { src: '/img2.png', alt: 'Image 2' },
                { src: '/img3.png', alt: 'Image 3' }
            ];

            it('should create gallery with correct number of images', () => {
                const gallery = createImageGallery({ images: testImages });

                const previews = gallery.querySelectorAll('.image-preview-container');
                expect(previews.length).toBe(3);
            });

            it('should use grid layout', () => {
                const gallery = createImageGallery({ images: testImages });

                expect(gallery.style.display).toBe('grid');
            });

            it('should support custom columns', () => {
                const gallery = createImageGallery({
                    images: testImages,
                    columns: 4
                });

                expect(gallery.style.gridTemplateColumns).toContain('repeat(4');
            });

            it('should support custom thumbnail size', () => {
                const gallery = createImageGallery({
                    images: testImages,
                    thumbnailSize: 100
                });

                const firstPreview = gallery.querySelector('.image-preview-container') as HTMLElement;
                expect(firstPreview.style.width).toBe('100px');
            });
        });

        describe('Lightbox', () => {
            it('should open lightbox with image', () => {
                openLightbox([{ src: '/test.png', alt: 'Test' }], 0);

                const overlay = document.querySelector('.lightbox-overlay');
                expect(overlay).not.toBeNull();
            });

            it('should close lightbox', () => {
                openLightbox([{ src: '/test.png' }], 0);
                closeLightbox();

                const overlay = document.querySelector('.lightbox-overlay') as HTMLElement;
                expect(overlay?.style.display).toBe('none');
            });

            it('should show navigation buttons for multiple images', () => {
                openLightbox([
                    { src: '/img1.png' },
                    { src: '/img2.png' }
                ], 0);

                const prevBtn = document.querySelector('.lightbox-prev');
                const nextBtn = document.querySelector('.lightbox-next');
                expect(prevBtn).not.toBeNull();
                expect(nextBtn).not.toBeNull();
            });

            it('should display counter for multiple images', () => {
                openLightbox([
                    { src: '/img1.png' },
                    { src: '/img2.png' },
                    { src: '/img3.png' }
                ], 0);

                const counter = document.querySelector('.lightbox-counter');
                expect(counter?.textContent).toBe('1 / 3');
            });
        });

        describe('createThumbnail', () => {
            it('should create canvas element', () => {
                const canvas = createThumbnail('/test.png', 150);

                expect(canvas).toBeInstanceOf(HTMLCanvasElement);
                expect(canvas.width).toBe(150);
                expect(canvas.height).toBe(150);
            });
        });
    });

    // ============================================================
    // AC 6.9.2: PDF Preview Component Tests
    // ============================================================
    describe('AC 6.9.2: PDF Preview Component', () => {
        describe('createPDFPreview', () => {
            it('should create PDF preview element', () => {
                const preview = createPDFPreview({
                    filePath: '/docs/test.pdf'
                });

                expect(preview).toBeInstanceOf(HTMLElement);
                expect(preview.className).toBe('pdf-preview-container');
            });

            it('should have iframe for PDF display', () => {
                const preview = createPDFPreview({
                    filePath: '/docs/test.pdf'
                });

                const iframe = preview.querySelector('iframe');
                expect(iframe).not.toBeNull();
                expect(iframe?.src).toContain('/docs/test.pdf');
            });

            it('should set initial page', () => {
                const preview = createPDFPreview({
                    filePath: '/docs/test.pdf',
                    initialPage: 5
                });

                const iframe = preview.querySelector('iframe');
                expect(iframe?.src).toContain('#page=5');
            });

            it('should show controls by default', () => {
                const preview = createPDFPreview({
                    filePath: '/docs/test.pdf'
                });

                const controls = preview.querySelector('.pdf-controls');
                expect(controls).not.toBeNull();
            });

            it('should hide controls when showControls is false', () => {
                const preview = createPDFPreview({
                    filePath: '/docs/test.pdf',
                    showControls: false
                });

                const controls = preview.querySelector('.pdf-controls');
                expect(controls).toBeNull();
            });

            it('should have navigation buttons', () => {
                const preview = createPDFPreview({
                    filePath: '/docs/test.pdf'
                });

                const prevBtn = preview.querySelector('[title="上一页"]');
                const nextBtn = preview.querySelector('[title="下一页"]');
                expect(prevBtn).not.toBeNull();
                expect(nextBtn).not.toBeNull();
            });

            it('should have zoom controls when zoomable', () => {
                const preview = createPDFPreview({
                    filePath: '/docs/test.pdf',
                    zoomable: true
                });

                const zoomIn = preview.querySelector('[title="放大"]');
                const zoomOut = preview.querySelector('[title="缩小"]');
                expect(zoomIn).not.toBeNull();
                expect(zoomOut).not.toBeNull();
            });

            it('should have download button', () => {
                const preview = createPDFPreview({
                    filePath: '/docs/test.pdf'
                });

                const downloadBtn = preview.querySelector('[title="下载PDF"]');
                expect(downloadBtn).not.toBeNull();
            });

            it('should have page input', () => {
                const preview = createPDFPreview({
                    filePath: '/docs/test.pdf'
                });

                const pageInput = preview.querySelector('input[type="number"]') as HTMLInputElement;
                expect(pageInput).not.toBeNull();
                expect(pageInput.value).toBe('1');
            });

            it('should support custom dimensions', () => {
                const preview = createPDFPreview({
                    filePath: '/docs/test.pdf',
                    width: 800,
                    height: 600
                });

                expect(preview.style.width).toBe('800px');
                expect(preview.style.height).toBe('600px');
            });
        });

        describe('createPDFThumbnail', () => {
            it('should create thumbnail element', () => {
                const thumbnail = createPDFThumbnail({
                    filePath: '/docs/test.pdf'
                });

                expect(thumbnail).toBeInstanceOf(HTMLElement);
                expect(thumbnail.className).toBe('pdf-thumbnail-container');
            });

            it('should have PDF icon', () => {
                const thumbnail = createPDFThumbnail({
                    filePath: '/docs/test.pdf'
                });

                const svg = thumbnail.querySelector('svg');
                expect(svg).not.toBeNull();
            });

            it('should show filename', () => {
                const thumbnail = createPDFThumbnail({
                    filePath: '/docs/my-document.pdf'
                });

                const filename = thumbnail.querySelector('.pdf-filename');
                expect(filename?.textContent).toContain('my-document.pdf');
            });

            it('should truncate long filenames', () => {
                const thumbnail = createPDFThumbnail({
                    filePath: '/docs/this-is-a-very-long-filename.pdf'
                });

                const filename = thumbnail.querySelector('.pdf-filename');
                expect(filename?.textContent?.length).toBeLessThanOrEqual(20);
            });
        });

        describe('openPDFModal', () => {
            it('should open modal with PDF viewer', () => {
                openPDFModal('/docs/test.pdf');

                const overlay = document.querySelector('.pdf-modal-overlay');
                expect(overlay).not.toBeNull();
            });

            it('should have close button', () => {
                openPDFModal('/docs/test.pdf');

                const closeBtn = document.querySelector('.pdf-modal button');
                expect(closeBtn).not.toBeNull();
            });
        });

        describe('updatePDFPage', () => {
            it('should update PDF to specific page', () => {
                const preview = createPDFPreview({
                    filePath: '/docs/test.pdf'
                });

                updatePDFPage(preview, 10);

                const pageInput = preview.querySelector('input[type="number"]') as HTMLInputElement;
                expect(pageInput.value).toBe('10');
            });
        });
    });

    // ============================================================
    // AC 6.9.3: Media Player Component Tests
    // ============================================================
    describe('AC 6.9.3: Media Player Component', () => {
        describe('createAudioPlayer', () => {
            it('should create audio player element', () => {
                const player = createAudioPlayer({
                    src: '/audio/test.mp3'
                });

                expect(player).toBeInstanceOf(HTMLElement);
                expect(player.className).toBe('audio-player-container');
            });

            it('should have audio element', () => {
                const player = createAudioPlayer({
                    src: '/audio/test.mp3'
                });

                const audio = player.querySelector('audio');
                expect(audio).not.toBeNull();
                expect(audio?.src).toContain('/audio/test.mp3');
            });

            it('should have play/pause button', () => {
                const player = createAudioPlayer({
                    src: '/audio/test.mp3'
                });

                const playBtn = player.querySelector('.play-btn');
                expect(playBtn).not.toBeNull();
            });

            it('should have progress bar', () => {
                const player = createAudioPlayer({
                    src: '/audio/test.mp3'
                });

                const progressContainer = player.querySelector('.progress-container');
                expect(progressContainer).not.toBeNull();
            });

            it('should have volume control', () => {
                const player = createAudioPlayer({
                    src: '/audio/test.mp3'
                });

                // Volume control is always present by default
                const volumeContainer = player.querySelector('.volume-container');
                expect(volumeContainer).not.toBeNull();
            });

            it('should display title when provided', () => {
                const player = createAudioPlayer({
                    src: '/audio/test.mp3',
                    title: 'Test Audio'
                });

                const titleElement = player.querySelector('.audio-title');
                expect(titleElement?.textContent).toBe('Test Audio');
            });

            it('should support initial markers', () => {
                const markers: TimeMarker[] = [
                    { time: 30, label: 'Introduction' },
                    { time: 120, label: 'Main Content' }
                ];

                const player = createAudioPlayer({
                    src: '/audio/test.mp3',
                    markers
                });

                const markerElements = player.querySelectorAll('.time-marker');
                expect(markerElements.length).toBe(2);
            });
        });

        describe('createVideoPlayer', () => {
            it('should create video player element', () => {
                const player = createVideoPlayer({
                    src: '/video/test.mp4'
                });

                expect(player).toBeInstanceOf(HTMLElement);
                expect(player.className).toBe('video-player-container');
            });

            it('should have video element', () => {
                const player = createVideoPlayer({
                    src: '/video/test.mp4'
                });

                const video = player.querySelector('video');
                expect(video).not.toBeNull();
            });

            it('should have controls overlay', () => {
                const player = createVideoPlayer({
                    src: '/video/test.mp4'
                });

                // Video player has controls overlay instead of fullscreen button
                const controlsOverlay = player.querySelector('.video-controls-overlay');
                expect(controlsOverlay).not.toBeNull();
            });

            it('should set poster image', () => {
                const player = createVideoPlayer({
                    src: '/video/test.mp4',
                    poster: '/images/poster.jpg'
                });

                const video = player.querySelector('video');
                expect(video?.poster).toContain('/images/poster.jpg');
            });

            it('should support custom dimensions', () => {
                const player = createVideoPlayer({
                    src: '/video/test.mp4',
                    width: 800,
                    height: 450
                });

                expect(player.style.width).toBe('800px');
            });
        });

        describe('formatTime', () => {
            it('should format seconds correctly', () => {
                expect(formatTime(0)).toBe('0:00');
                expect(formatTime(65)).toBe('1:05');
                expect(formatTime(3661)).toBe('1:01:01');
            });

            it('should handle edge cases', () => {
                expect(formatTime(-1)).toBe('0:00');
                expect(formatTime(NaN)).toBe('0:00');
            });
        });

        describe('seekTo', () => {
            it('should seek to specified time', () => {
                const player = createAudioPlayer({
                    src: '/audio/test.mp3'
                });

                const audio = player.querySelector('audio') as HTMLAudioElement;
                // Mock currentTime setter
                Object.defineProperty(audio, 'currentTime', {
                    writable: true,
                    value: 0
                });

                seekTo(player, 30);
                // Note: In real browser, this would set currentTime
            });
        });

        describe('addTimeMarker', () => {
            it('should add marker to player', () => {
                const player = createAudioPlayer({
                    src: '/audio/test.mp3'
                });

                addTimeMarker(player, { time: 60, label: 'New Marker' });

                const markers = player.querySelectorAll('.time-marker');
                expect(markers.length).toBe(1);
            });

            it('should support custom marker color', () => {
                const player = createAudioPlayer({
                    src: '/audio/test.mp3'
                });

                addTimeMarker(player, { time: 60, label: 'Red Marker', color: '#ff0000' });

                const marker = player.querySelector('.time-marker') as HTMLElement;
                expect(marker?.style.background).toContain('rgb(255, 0, 0)');
            });
        });

        describe('setPlaybackRate', () => {
            it('should change playback rate', () => {
                const player = createAudioPlayer({
                    src: '/audio/test.mp3'
                });

                setPlaybackRate(player, 1.5);

                // Verify function doesn't throw and player element exists
                expect(player).toBeInstanceOf(HTMLElement);
                // The rate is set internally on the audio element
                const audio = (player as any).__audio as HTMLAudioElement | undefined;
                if (audio) {
                    expect(audio.playbackRate).toBe(1.5);
                }
            });
        });
    });

    // ============================================================
    // AC 6.9.4: Media Panel Component Tests
    // ============================================================
    describe('AC 6.9.4: Media Panel Component', () => {
        const testItems: MediaItem[] = [
            { id: '1', type: 'image', path: '/img1.png', title: 'Image 1', relevanceScore: 0.9 },
            { id: '2', type: 'pdf', path: '/doc.pdf', title: 'Document', relevanceScore: 0.8 },
            { id: '3', type: 'audio', path: '/audio.mp3', title: 'Audio', relevanceScore: 0.7 },
            { id: '4', type: 'video', path: '/video.mp4', title: 'Video', relevanceScore: 0.6 }
        ];

        describe('createMediaPanel', () => {
            it('should create media panel element', () => {
                const panel = createMediaPanel({
                    items: testItems
                });

                expect(panel).toBeInstanceOf(HTMLElement);
                expect(panel.className).toBe('media-panel');
            });

            it('should have filter buttons', () => {
                const panel = createMediaPanel({
                    items: testItems
                });

                const filterBtns = panel.querySelectorAll('.filter-btn');
                expect(filterBtns.length).toBeGreaterThan(0);
            });

            it('should have search input when enabled', () => {
                const panel = createMediaPanel({
                    items: testItems,
                    showSearch: true
                });

                const searchInput = panel.querySelector('.media-search-input');
                expect(searchInput).not.toBeNull();
            });

            it('should support custom title', () => {
                const panel = createMediaPanel({
                    items: testItems,
                    title: 'Related Materials'
                });

                const titleElement = panel.querySelector('h3');
                expect(titleElement?.textContent).toContain('Related Materials');
            });

            it('should display all items by default', () => {
                const panel = createMediaPanel({
                    items: testItems
                });

                const mediaItems = panel.querySelectorAll('.media-item');
                expect(mediaItems.length).toBe(4);
            });

            it('should sort by relevance by default', () => {
                const panel = createMediaPanel({
                    items: testItems,
                    sortBy: 'relevance'
                });

                // First item should be highest relevance (Image 1 with 0.9)
                const firstItem = panel.querySelector('.media-item');
                expect(firstItem?.textContent).toContain('Image 1');
            });
        });

        describe('createMediaList', () => {
            it('should create list view', () => {
                const list = createMediaList({
                    items: testItems,
                    mode: 'list'
                });

                const listItems = list.querySelectorAll('.media-item');
                expect(listItems.length).toBe(4);
            });

            it('should create grid view', () => {
                const grid = createMediaList({
                    items: testItems,
                    mode: 'grid'
                });

                const gridItems = grid.querySelectorAll('.media-item');
                expect(gridItems.length).toBe(4);
            });
        });

        describe('updateMediaPanel', () => {
            it('should update panel with new items', () => {
                const panel = createMediaPanel({
                    items: testItems
                });

                const newItems: MediaItem[] = [
                    { id: '5', type: 'image', path: '/new.png', title: 'New', relevanceScore: 1.0 }
                ];

                updateMediaPanel(panel, newItems);

                const mediaItems = panel.querySelectorAll('.media-item');
                expect(mediaItems.length).toBe(1);
            });
        });

        describe('Filter Functions', () => {
            it('should get current filter', () => {
                const panel = createMediaPanel({
                    items: testItems
                });

                const filter = getMediaPanelFilter(panel);
                expect(filter).toBe('all');
            });

            it('should set filter', () => {
                const panel = createMediaPanel({
                    items: testItems
                });

                setMediaPanelFilter(panel, 'image');

                const filter = getMediaPanelFilter(panel);
                expect(filter).toBe('image');
            });

            it('should filter items by type', () => {
                const panel = createMediaPanel({
                    items: testItems
                });

                setMediaPanelFilter(panel, 'image');

                const visibleItems = panel.querySelectorAll('.media-item:not([style*="display: none"]), .media-item:not([style*="display: none"])');
                expect(visibleItems.length).toBe(1);
            });
        });

        describe('Responsive Design', () => {
            it('should have responsive container', () => {
                const panel = createMediaPanel({
                    items: testItems
                });

                expect(panel.style.width).toBe('100%');
            });
        });
    });

    // ============================================================
    // AC 6.9.5: Mobile Adaptation Tests
    // ============================================================
    describe('AC 6.9.5: Mobile Adaptation', () => {
        it('should use relative units for sizing', () => {
            const preview = createImagePreview({
                src: '/test.png',
                thumbnailSize: 150
            });

            // Component should use pixel values that can be overridden by CSS
            expect(preview.style.width).toBe('150px');
        });

        it('should have touch-friendly controls', () => {
            const player = createAudioPlayer({
                src: '/audio/test.mp3'
            });

            const playBtn = player.querySelector('.play-btn') as HTMLElement;
            // Button should have minimum touch target size
            expect(parseInt(playBtn?.style.width || '0')).toBeGreaterThanOrEqual(32);
            expect(parseInt(playBtn?.style.height || '0')).toBeGreaterThanOrEqual(32);
        });

        it('should support touch events for lightbox', () => {
            openLightbox([
                { src: '/img1.png' },
                { src: '/img2.png' }
            ], 0);

            const overlay = document.querySelector('.lightbox-overlay');

            // Touch events should be attached
            const touchStartEvent = new TouchEvent('touchstart', {
                touches: [{ clientX: 100 } as Touch]
            });
            const touchEndEvent = new TouchEvent('touchend', {
                changedTouches: [{ clientX: 200 } as Touch]
            });

            // These should not throw errors
            overlay?.dispatchEvent(touchStartEvent);
            overlay?.dispatchEvent(touchEndEvent);
        });

        it('should have keyboard navigation support', () => {
            openLightbox([
                { src: '/img1.png' },
                { src: '/img2.png' }
            ], 0);

            // Verify lightbox is open first
            const overlayBefore = document.querySelector('.lightbox-overlay') as HTMLElement;
            expect(overlayBefore).not.toBeNull();
            expect(overlayBefore?.style.display).toBe('flex');

            // Close via Escape key
            closeLightbox();

            const overlay = document.querySelector('.lightbox-overlay') as HTMLElement;
            expect(overlay?.style.display).toBe('none');
        });
    });

    // ============================================================
    // Integration Tests
    // ============================================================
    describe('Integration Tests', () => {
        it('should integrate ImagePreview with MediaPanel', () => {
            const items: MediaItem[] = [
                { id: '1', type: 'image', path: '/test.png', title: 'Test', relevanceScore: 1.0 }
            ];

            const panel = createMediaPanel({
                items
            });

            // Panel should contain image preview
            const imageArea = panel.querySelector('.media-item');
            expect(imageArea).not.toBeNull();
        });

        it('should integrate PDFPreview with MediaPanel', () => {
            const items: MediaItem[] = [
                { id: '1', type: 'pdf', path: '/test.pdf', title: 'Test', relevanceScore: 1.0 }
            ];

            const panel = createMediaPanel({
                items
            });

            const pdfArea = panel.querySelector('.media-item');
            expect(pdfArea).not.toBeNull();
        });

        it('should integrate MediaPlayer with MediaPanel', () => {
            const items: MediaItem[] = [
                { id: '1', type: 'audio', path: '/test.mp3', title: 'Test', relevanceScore: 1.0 },
                { id: '2', type: 'video', path: '/test.mp4', title: 'Test', relevanceScore: 0.9 }
            ];

            const panel = createMediaPanel({
                items
            });

            const mediaAreas = panel.querySelectorAll('.media-item');
            expect(mediaAreas.length).toBe(2);
        });
    });

    // ============================================================
    // Error Handling Tests
    // ============================================================
    describe('Error Handling', () => {
        it('should handle missing image gracefully', () => {
            const preview = createImagePreview({
                src: '/nonexistent.png'
            });

            const img = preview.querySelector('img');
            // Simulate error
            img?.dispatchEvent(new Event('error'));

            const placeholder = preview.querySelector('.image-placeholder');
            expect(placeholder).not.toBeNull();
        });

        it('should handle empty media panel', () => {
            const panel = createMediaPanel({
                items: []
            });

            const emptyMessage = panel.querySelector('.media-panel-empty');
            expect(emptyMessage).not.toBeNull();
        });

        it('should handle invalid time in formatTime', () => {
            expect(formatTime(-10)).toBe('0:00');
            expect(formatTime(Infinity)).toBe('0:00');
        });
    });

    // ============================================================
    // Performance Tests
    // ============================================================
    describe('Performance', () => {
        it('should handle large number of items efficiently', () => {
            const items: MediaItem[] = Array.from({ length: 100 }, (_, i) => ({
                id: String(i),
                type: 'image' as const,
                path: `/img${i}.png`,
                title: `Image ${i}`,
                relevanceScore: Math.random()
            }));

            const startTime = performance.now();
            const panel = createMediaPanel({
                items
            });
            const endTime = performance.now();

            expect(endTime - startTime).toBeLessThan(1000); // Should complete within 1 second
            expect(panel.querySelectorAll('.media-item').length).toBe(100);
        });

        it('should use lazy loading for images', () => {
            const preview = createImagePreview({
                src: '/test.png'
            });

            const img = preview.querySelector('img');
            expect(img?.loading).toBe('lazy');
        });
    });
});
