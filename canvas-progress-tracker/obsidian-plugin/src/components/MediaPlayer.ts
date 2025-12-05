/**
 * Media Player Component
 *
 * Story 6.9 AC 6.9.3: 音视频播放器
 * - 内嵌播放器
 * - 进度条和控制按钮
 * - 支持时间戳标记
 *
 * ✅ Verified from HTML5 Media API (MDN Standard)
 * [Source: docs/stories/6.9.multimodal-ui-integration.story.md:37-40]
 */

/**
 * Props for AudioPlayer component.
 */
export interface AudioPlayerProps {
    /** Audio file path or URL */
    src: string;
    /** Audio title */
    title?: string;
    /** Show waveform visualization (default: false) */
    showWaveform?: boolean;
    /** Enable loop playback (default: false) */
    loop?: boolean;
    /** Auto play (default: false) */
    autoPlay?: boolean;
    /** Timestamp markers */
    markers?: TimeMarker[];
    /** Callback when playback position changes */
    onTimeUpdate?: (currentTime: number) => void;
    /** Callback when audio ends */
    onEnded?: () => void;
}

/**
 * Props for VideoPlayer component.
 */
export interface VideoPlayerProps {
    /** Video file path or URL */
    src: string;
    /** Video title */
    title?: string;
    /** Poster image URL */
    poster?: string;
    /** Width (default: 100%) */
    width?: string | number;
    /** Height (default: auto) */
    height?: string | number;
    /** Enable loop playback (default: false) */
    loop?: boolean;
    /** Auto play (default: false) */
    autoPlay?: boolean;
    /** Show controls (default: true) */
    controls?: boolean;
    /** Timestamp markers */
    markers?: TimeMarker[];
    /** Callback when playback position changes */
    onTimeUpdate?: (currentTime: number) => void;
    /** Callback when video ends */
    onEnded?: () => void;
}

/**
 * Time marker for timestamping.
 */
export interface TimeMarker {
    /** Time in seconds */
    time: number;
    /** Marker label */
    label: string;
    /** Marker color (default: accent color) */
    color?: string;
}

/**
 * Internal player state
 */
interface PlayerState {
    isPlaying: boolean;
    currentTime: number;
    duration: number;
    volume: number;
    isMuted: boolean;
    playbackRate: number;
}

/**
 * Creates an audio player component with custom controls.
 *
 * Features:
 * - Play/pause button
 * - Progress bar with seek
 * - Volume control
 * - Time display
 * - Timestamp markers
 *
 * ✅ Verified from HTML5 Audio API (MDN Standard)
 *
 * Example:
 * ```typescript
 * const player = createAudioPlayer({
 *     src: '/audio/lecture.mp3',
 *     title: 'Lecture 1',
 *     markers: [{ time: 120, label: '重点概念' }]
 * });
 * container.appendChild(player);
 * ```
 */
export function createAudioPlayer(props: AudioPlayerProps): HTMLElement {
    const {
        src,
        title,
        showWaveform = false,
        loop = false,
        autoPlay = false,
        markers = [],
        onTimeUpdate,
        onEnded
    } = props;

    const state: PlayerState = {
        isPlaying: false,
        currentTime: 0,
        duration: 0,
        volume: 1,
        isMuted: false,
        playbackRate: 1
    };

    const container = document.createElement('div');
    container.className = 'audio-player-container';
    container.style.cssText = `
        width: 100%;
        background: var(--background-secondary);
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    `;

    // Hidden audio element
    const audio = document.createElement('audio');
    audio.src = src;
    audio.loop = loop;
    audio.preload = 'metadata';
    if (autoPlay) audio.autoplay = true;

    // Title
    if (title) {
        const titleEl = document.createElement('div');
        titleEl.className = 'audio-title';
        titleEl.textContent = title;
        titleEl.style.cssText = `
            font-weight: 600;
            margin-bottom: 12px;
            color: var(--text-normal);
        `;
        container.appendChild(titleEl);
    }

    // Controls row
    const controlsRow = document.createElement('div');
    controlsRow.className = 'audio-controls';
    controlsRow.style.cssText = `
        display: flex;
        align-items: center;
        gap: 12px;
    `;

    // Play/Pause button
    const playBtn = document.createElement('button');
    playBtn.className = 'play-btn';
    playBtn.innerHTML = '▶';
    playBtn.style.cssText = `
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: none;
        background: var(--interactive-accent);
        color: white;
        cursor: pointer;
        font-size: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 0.2s;
    `;
    playBtn.addEventListener('click', () => togglePlay(audio, playBtn, state));
    controlsRow.appendChild(playBtn);

    // Progress container
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress-container';
    progressContainer.style.cssText = `
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 4px;
    `;

    // Progress bar wrapper (for markers)
    const progressWrapper = document.createElement('div');
    progressWrapper.className = 'progress-wrapper';
    progressWrapper.style.cssText = `
        position: relative;
        height: 8px;
        background: var(--background-modifier-border);
        border-radius: 4px;
        cursor: pointer;
    `;

    // Progress bar fill
    const progressFill = document.createElement('div');
    progressFill.className = 'progress-fill';
    progressFill.style.cssText = `
        height: 100%;
        background: var(--interactive-accent);
        border-radius: 4px;
        width: 0%;
        transition: width 0.1s linear;
    `;
    progressWrapper.appendChild(progressFill);

    // Add markers
    markers.forEach(marker => {
        const markerEl = document.createElement('div');
        markerEl.className = 'time-marker';
        markerEl.title = `${marker.label} (${formatTime(marker.time)})`;
        markerEl.style.cssText = `
            position: absolute;
            width: 4px;
            height: 100%;
            background: ${marker.color || 'var(--text-accent)'};
            border-radius: 2px;
            left: 0%;
            top: 0;
            cursor: pointer;
        `;
        markerEl.addEventListener('click', (e) => {
            e.stopPropagation();
            audio.currentTime = marker.time;
        });
        progressWrapper.appendChild(markerEl);
    });

    // Seek on click
    progressWrapper.addEventListener('click', (e) => {
        const rect = progressWrapper.getBoundingClientRect();
        const percent = (e.clientX - rect.left) / rect.width;
        audio.currentTime = percent * audio.duration;
    });

    progressContainer.appendChild(progressWrapper);

    // Time display
    const timeDisplay = document.createElement('div');
    timeDisplay.className = 'time-display';
    timeDisplay.style.cssText = `
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        color: var(--text-muted);
    `;
    const currentTimeEl = document.createElement('span');
    currentTimeEl.textContent = '0:00';
    const durationEl = document.createElement('span');
    durationEl.textContent = '0:00';
    timeDisplay.appendChild(currentTimeEl);
    timeDisplay.appendChild(durationEl);
    progressContainer.appendChild(timeDisplay);

    controlsRow.appendChild(progressContainer);

    // Volume control
    const volumeContainer = document.createElement('div');
    volumeContainer.className = 'volume-container';
    volumeContainer.style.cssText = `
        display: flex;
        align-items: center;
        gap: 4px;
    `;

    const volumeBtn = document.createElement('button');
    volumeBtn.className = 'volume-btn';
    volumeBtn.innerHTML = '🔊';
    volumeBtn.style.cssText = `
        background: none;
        border: none;
        cursor: pointer;
        font-size: 16px;
        padding: 4px;
    `;
    volumeBtn.addEventListener('click', () => {
        state.isMuted = !state.isMuted;
        audio.muted = state.isMuted;
        volumeBtn.innerHTML = state.isMuted ? '🔇' : '🔊';
    });
    volumeContainer.appendChild(volumeBtn);

    const volumeSlider = document.createElement('input');
    volumeSlider.type = 'range';
    volumeSlider.min = '0';
    volumeSlider.max = '1';
    volumeSlider.step = '0.1';
    volumeSlider.value = '1';
    volumeSlider.style.cssText = `
        width: 60px;
        cursor: pointer;
    `;
    volumeSlider.addEventListener('input', () => {
        audio.volume = parseFloat(volumeSlider.value);
        state.volume = audio.volume;
    });
    volumeContainer.appendChild(volumeSlider);

    controlsRow.appendChild(volumeContainer);
    container.appendChild(controlsRow);

    // Audio events
    audio.addEventListener('loadedmetadata', () => {
        state.duration = audio.duration;
        durationEl.textContent = formatTime(audio.duration);
        // Update marker positions
        markers.forEach((marker, i) => {
            const markerEl = progressWrapper.querySelectorAll('.time-marker')[i] as HTMLElement;
            if (markerEl && audio.duration > 0) {
                markerEl.style.left = `${(marker.time / audio.duration) * 100}%`;
            }
        });
    });

    audio.addEventListener('timeupdate', () => {
        state.currentTime = audio.currentTime;
        const percent = (audio.currentTime / audio.duration) * 100;
        progressFill.style.width = `${percent}%`;
        currentTimeEl.textContent = formatTime(audio.currentTime);
        if (onTimeUpdate) onTimeUpdate(audio.currentTime);
    });

    audio.addEventListener('ended', () => {
        state.isPlaying = false;
        playBtn.innerHTML = '▶';
        if (onEnded) onEnded();
    });

    container.appendChild(audio);

    // Store references
    (container as any).__audio = audio;
    (container as any).__state = state;

    return container;
}

/**
 * Creates a video player component with custom controls.
 *
 * Features:
 * - Native video playback
 * - Custom overlay controls
 * - Fullscreen support
 * - Timestamp markers
 *
 * ✅ Verified from HTML5 Video API (MDN Standard)
 *
 * Example:
 * ```typescript
 * const player = createVideoPlayer({
 *     src: '/videos/tutorial.mp4',
 *     poster: '/images/thumbnail.jpg',
 *     markers: [{ time: 60, label: '重要示范' }]
 * });
 * container.appendChild(player);
 * ```
 */
export function createVideoPlayer(props: VideoPlayerProps): HTMLElement {
    const {
        src,
        title,
        poster,
        width = '100%',
        height = 'auto',
        loop = false,
        autoPlay = false,
        controls = true,
        markers = [],
        onTimeUpdate,
        onEnded
    } = props;

    const state: PlayerState = {
        isPlaying: false,
        currentTime: 0,
        duration: 0,
        volume: 1,
        isMuted: false,
        playbackRate: 1
    };

    const container = document.createElement('div');
    container.className = 'video-player-container';
    container.style.cssText = `
        width: ${typeof width === 'number' ? `${width}px` : width};
        position: relative;
        background: #000;
        border-radius: 8px;
        overflow: hidden;
    `;

    // Video element
    const video = document.createElement('video');
    video.src = src;
    video.loop = loop;
    video.preload = 'metadata';
    if (poster) video.poster = poster;
    if (autoPlay) video.autoplay = true;
    video.style.cssText = `
        width: 100%;
        height: ${typeof height === 'number' ? `${height}px` : height};
        display: block;
    `;

    container.appendChild(video);

    if (controls) {
        // Custom controls overlay
        const controlsOverlay = document.createElement('div');
        controlsOverlay.className = 'video-controls-overlay';
        controlsOverlay.style.cssText = `
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.7));
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            opacity: 0;
            transition: opacity 0.3s;
        `;

        // Title bar
        if (title) {
            const titleBar = document.createElement('div');
            titleBar.textContent = title;
            titleBar.style.cssText = `
                color: white;
                font-weight: 600;
                font-size: 14px;
            `;
            controlsOverlay.appendChild(titleBar);
        }

        // Progress bar with markers
        const progressBar = document.createElement('div');
        progressBar.className = 'video-progress';
        progressBar.style.cssText = `
            position: relative;
            height: 6px;
            background: rgba(255,255,255,0.3);
            border-radius: 3px;
            cursor: pointer;
        `;

        const progressFill = document.createElement('div');
        progressFill.className = 'video-progress-fill';
        progressFill.style.cssText = `
            height: 100%;
            background: var(--interactive-accent);
            border-radius: 3px;
            width: 0%;
        `;
        progressBar.appendChild(progressFill);

        // Add markers
        markers.forEach(marker => {
            const markerEl = document.createElement('div');
            markerEl.className = 'video-marker';
            markerEl.title = `${marker.label} (${formatTime(marker.time)})`;
            markerEl.style.cssText = `
                position: absolute;
                width: 4px;
                height: 12px;
                background: ${marker.color || '#FFD700'};
                border-radius: 2px;
                top: -3px;
                cursor: pointer;
            `;
            markerEl.addEventListener('click', (e) => {
                e.stopPropagation();
                video.currentTime = marker.time;
            });
            progressBar.appendChild(markerEl);
        });

        progressBar.addEventListener('click', (e) => {
            const rect = progressBar.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            video.currentTime = percent * video.duration;
        });

        controlsOverlay.appendChild(progressBar);

        // Controls row
        const controlsRow = document.createElement('div');
        controlsRow.style.cssText = `
            display: flex;
            align-items: center;
            gap: 12px;
            color: white;
        `;

        // Play button
        const playBtn = document.createElement('button');
        playBtn.innerHTML = '▶';
        playBtn.style.cssText = `
            background: none;
            border: none;
            color: white;
            font-size: 18px;
            cursor: pointer;
            padding: 4px;
        `;
        playBtn.addEventListener('click', () => togglePlay(video, playBtn, state));
        controlsRow.appendChild(playBtn);

        // Time display
        const timeDisplay = document.createElement('span');
        timeDisplay.style.fontSize = '12px';
        timeDisplay.textContent = '0:00 / 0:00';
        controlsRow.appendChild(timeDisplay);

        // Spacer
        const spacer = document.createElement('div');
        spacer.style.flex = '1';
        controlsRow.appendChild(spacer);

        // Volume
        const volumeBtn = document.createElement('button');
        volumeBtn.innerHTML = '🔊';
        volumeBtn.style.cssText = `
            background: none;
            border: none;
            cursor: pointer;
            font-size: 14px;
        `;
        volumeBtn.addEventListener('click', () => {
            video.muted = !video.muted;
            volumeBtn.innerHTML = video.muted ? '🔇' : '🔊';
        });
        controlsRow.appendChild(volumeBtn);

        // Fullscreen
        const fullscreenBtn = document.createElement('button');
        fullscreenBtn.innerHTML = '⛶';
        fullscreenBtn.style.cssText = `
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            font-size: 16px;
        `;
        fullscreenBtn.addEventListener('click', () => {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                container.requestFullscreen();
            }
        });
        controlsRow.appendChild(fullscreenBtn);

        controlsOverlay.appendChild(controlsRow);
        container.appendChild(controlsOverlay);

        // Show/hide controls on hover
        container.addEventListener('mouseenter', () => {
            controlsOverlay.style.opacity = '1';
        });
        container.addEventListener('mouseleave', () => {
            if (!state.isPlaying) return;
            controlsOverlay.style.opacity = '0';
        });

        // Video events
        video.addEventListener('loadedmetadata', () => {
            state.duration = video.duration;
            timeDisplay.textContent = `0:00 / ${formatTime(video.duration)}`;
            // Update marker positions
            markers.forEach((marker, i) => {
                const markerEl = progressBar.querySelectorAll('.video-marker')[i] as HTMLElement;
                if (markerEl && video.duration > 0) {
                    markerEl.style.left = `${(marker.time / video.duration) * 100}%`;
                }
            });
        });

        video.addEventListener('timeupdate', () => {
            state.currentTime = video.currentTime;
            const percent = (video.currentTime / video.duration) * 100;
            progressFill.style.width = `${percent}%`;
            timeDisplay.textContent = `${formatTime(video.currentTime)} / ${formatTime(video.duration)}`;
            if (onTimeUpdate) onTimeUpdate(video.currentTime);
        });

        video.addEventListener('play', () => {
            state.isPlaying = true;
            playBtn.innerHTML = '⏸';
        });

        video.addEventListener('pause', () => {
            state.isPlaying = false;
            playBtn.innerHTML = '▶';
            controlsOverlay.style.opacity = '1';
        });

        video.addEventListener('ended', () => {
            state.isPlaying = false;
            playBtn.innerHTML = '▶';
            if (onEnded) onEnded();
        });

        // Click video to toggle play
        video.addEventListener('click', () => togglePlay(video, playBtn, state));
    } else {
        video.controls = true;
    }

    // Store references
    (container as any).__video = video;
    (container as any).__state = state;

    return container;
}

/**
 * Toggles play/pause state.
 */
function togglePlay(
    media: HTMLAudioElement | HTMLVideoElement,
    playBtn: HTMLButtonElement,
    state: PlayerState
): void {
    if (media.paused) {
        media.play();
        state.isPlaying = true;
        playBtn.innerHTML = '⏸';
    } else {
        media.pause();
        state.isPlaying = false;
        playBtn.innerHTML = '▶';
    }
}

/**
 * Formats time in seconds to MM:SS or HH:MM:SS.
 */
export function formatTime(seconds: number): string {
    if (isNaN(seconds) || !isFinite(seconds) || seconds < 0) return '0:00';

    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);

    if (h > 0) {
        return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }
    return `${m}:${s.toString().padStart(2, '0')}`;
}

/**
 * Seeks audio/video to a specific time.
 */
export function seekTo(container: HTMLElement, time: number): void {
    const audio = (container as any).__audio as HTMLAudioElement | undefined;
    const video = (container as any).__video as HTMLVideoElement | undefined;
    const media = audio || video;

    if (media) {
        media.currentTime = Math.max(0, Math.min(time, media.duration || time));
    }
}

/**
 * Adds a time marker to an existing player.
 */
export function addTimeMarker(
    container: HTMLElement,
    marker: TimeMarker
): void {
    const audio = (container as any).__audio as HTMLAudioElement | undefined;
    const video = (container as any).__video as HTMLVideoElement | undefined;
    const media = audio || video;

    if (!media) return;

    const progressWrapper = container.querySelector('.progress-wrapper, .video-progress');
    if (!progressWrapper) return;

    const markerEl = document.createElement('div');
    markerEl.className = audio ? 'time-marker' : 'video-marker';
    markerEl.title = `${marker.label} (${formatTime(marker.time)})`;
    markerEl.style.cssText = `
        position: absolute;
        width: 4px;
        height: ${audio ? '100%' : '12px'};
        background: ${marker.color || (audio ? 'var(--text-accent)' : '#FFD700')};
        border-radius: 2px;
        ${audio ? '' : 'top: -3px;'}
        cursor: pointer;
    `;

    if (media.duration > 0) {
        markerEl.style.left = `${(marker.time / media.duration) * 100}%`;
    }

    markerEl.addEventListener('click', (e) => {
        e.stopPropagation();
        media.currentTime = marker.time;
    });

    progressWrapper.appendChild(markerEl);
}

/**
 * Gets the current playback time.
 */
export function getCurrentTime(container: HTMLElement): number {
    const audio = (container as any).__audio as HTMLAudioElement | undefined;
    const video = (container as any).__video as HTMLVideoElement | undefined;
    const media = audio || video;

    return media?.currentTime || 0;
}

/**
 * Sets playback rate.
 */
export function setPlaybackRate(container: HTMLElement, rate: number): void {
    const audio = (container as any).__audio as HTMLAudioElement | undefined;
    const video = (container as any).__video as HTMLVideoElement | undefined;
    const media = audio || video;

    if (media) {
        media.playbackRate = rate;
    }
}
