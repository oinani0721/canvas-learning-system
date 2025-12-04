/**
 * Circular Progress Component
 *
 * Story 19.5 AC 1: 圆形进度条组件，显示当前检验通过率
 *
 * ✅ Verified from SVG specification (MDN Standard)
 * [Source: docs/stories/19.5.story.md:181-243 - 圆形进度条组件]
 */

/**
 * Props for CircularProgress component.
 */
export interface CircularProgressProps {
    /** Progress percentage (0-100) */
    percentage: number;
    /** Size of the circle in pixels (default: 120) */
    size?: number;
    /** Width of the progress stroke (default: 10) */
    strokeWidth?: number;
    /** Color of the progress arc (default: green) */
    color?: string;
    /** Background color of the circle (default: #e0e0e0) */
    bgColor?: string;
    /** Show percentage text (default: true) */
    showText?: boolean;
    /** Label below the percentage (optional) */
    label?: string;
    /** Enable animation (default: true) */
    animated?: boolean;
}

/**
 * Creates a circular progress indicator using SVG.
 *
 * Features:
 * - Smooth progress arc animation
 * - Customizable colors and sizes
 * - Optional percentage text display
 * - Accessible with ARIA labels
 *
 * ✅ Verified from SVG specification (MDN Standard)
 *
 * Example:
 * ```typescript
 * const progress = createCircularProgress({
 *     percentage: 75,
 *     color: '#4CAF50',
 *     label: '通过率'
 * });
 * container.appendChild(progress);
 * ```
 */
export function createCircularProgress(props: CircularProgressProps): HTMLElement {
    const {
        percentage,
        size = 120,
        strokeWidth = 10,
        color = '#4CAF50',
        bgColor = '#e0e0e0',
        showText = true,
        label,
        animated = true
    } = props;

    // Calculate circle geometry
    // ✅ Verified from SVG specification (MDN): stroke-dasharray, stroke-dashoffset
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const normalizedPercentage = Math.max(0, Math.min(100, percentage));
    const offset = circumference - (normalizedPercentage / 100) * circumference;

    const container = document.createElement('div');
    container.className = 'circular-progress-container';
    container.style.display = 'inline-flex';
    container.style.flexDirection = 'column';
    container.style.alignItems = 'center';

    // Create SVG element
    // ✅ Verified from SVG specification (MDN): createElementNS for SVG
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', String(size));
    svg.setAttribute('height', String(size));
    svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
    svg.setAttribute('role', 'progressbar');
    svg.setAttribute('aria-valuenow', String(Math.round(normalizedPercentage)));
    svg.setAttribute('aria-valuemin', '0');
    svg.setAttribute('aria-valuemax', '100');
    svg.setAttribute('aria-label', `Progress: ${Math.round(normalizedPercentage)}%`);

    // Background circle
    const bgCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    bgCircle.setAttribute('class', 'progress-bg');
    bgCircle.setAttribute('cx', String(size / 2));
    bgCircle.setAttribute('cy', String(size / 2));
    bgCircle.setAttribute('r', String(radius));
    bgCircle.setAttribute('stroke', bgColor);
    bgCircle.setAttribute('stroke-width', String(strokeWidth));
    bgCircle.setAttribute('fill', 'none');
    svg.appendChild(bgCircle);

    // Progress arc
    const progressCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    progressCircle.setAttribute('class', 'progress-bar');
    progressCircle.setAttribute('cx', String(size / 2));
    progressCircle.setAttribute('cy', String(size / 2));
    progressCircle.setAttribute('r', String(radius));
    progressCircle.setAttribute('stroke', color);
    progressCircle.setAttribute('stroke-width', String(strokeWidth));
    progressCircle.setAttribute('fill', 'none');
    progressCircle.setAttribute('stroke-linecap', 'round');
    progressCircle.setAttribute('stroke-dasharray', String(circumference));
    progressCircle.setAttribute('transform', `rotate(-90 ${size / 2} ${size / 2})`);

    if (animated) {
        // Start with full offset (0% progress) and animate to target
        progressCircle.setAttribute('stroke-dashoffset', String(circumference));
        progressCircle.style.transition = 'stroke-dashoffset 0.5s ease-out';
        // Trigger animation after a brief delay
        setTimeout(() => {
            progressCircle.setAttribute('stroke-dashoffset', String(offset));
        }, 50);
    } else {
        progressCircle.setAttribute('stroke-dashoffset', String(offset));
    }

    svg.appendChild(progressCircle);

    // Percentage text
    if (showText) {
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('class', 'progress-text');
        text.setAttribute('x', '50%');
        text.setAttribute('y', '50%');
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('dominant-baseline', 'middle');
        text.setAttribute('font-size', String(size / 5));
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('fill', 'currentColor');
        text.textContent = `${Math.round(normalizedPercentage)}%`;
        svg.appendChild(text);
    }

    container.appendChild(svg);

    // Optional label below the circle
    if (label) {
        const labelEl = document.createElement('span');
        labelEl.className = 'progress-label';
        labelEl.textContent = label;
        labelEl.style.marginTop = '8px';
        labelEl.style.fontSize = '14px';
        labelEl.style.color = 'var(--text-muted)';
        container.appendChild(labelEl);
    }

    return container;
}

/**
 * Get color based on progress percentage.
 *
 * ✅ Verified from Canvas color system (docs/stories/19.5.story.md)
 */
export function getProgressColor(percentage: number): string {
    if (percentage >= 80) return '#4CAF50';  // Green - excellent
    if (percentage >= 60) return '#8BC34A';  // Light green - good
    if (percentage >= 40) return '#FFC107';  // Yellow - moderate
    if (percentage >= 20) return '#FF9800';  // Orange - needs work
    return '#F44336';                         // Red - struggling
}

/**
 * Updates an existing circular progress element.
 */
export function updateCircularProgress(
    container: HTMLElement,
    newPercentage: number,
    animated = true
): void {
    const progressCircle = container.querySelector('.progress-bar') as SVGCircleElement;
    const text = container.querySelector('.progress-text') as SVGTextElement;
    const svg = container.querySelector('svg');

    if (!progressCircle || !svg) return;

    const normalizedPercentage = Math.max(0, Math.min(100, newPercentage));
    const radius = parseFloat(progressCircle.getAttribute('r') || '0');
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (normalizedPercentage / 100) * circumference;

    if (animated) {
        progressCircle.style.transition = 'stroke-dashoffset 0.5s ease-out';
    } else {
        progressCircle.style.transition = 'none';
    }

    progressCircle.setAttribute('stroke-dashoffset', String(offset));

    if (text) {
        text.textContent = `${Math.round(normalizedPercentage)}%`;
    }

    svg.setAttribute('aria-valuenow', String(Math.round(normalizedPercentage)));
    svg.setAttribute('aria-label', `Progress: ${Math.round(normalizedPercentage)}%`);
}
