/**
 * Chart Export Utilities
 *
 * Story 19.5 AC 5: 图表导出功能
 *
 * Provides utilities for exporting visualization components as images.
 */

/**
 * Export options for chart images.
 */
export interface ExportOptions {
    /** Image format (default: 'png') */
    format?: 'png' | 'jpeg' | 'svg';
    /** JPEG quality 0-1 (default: 1.0) */
    quality?: number;
    /** Background color (default: transparent for PNG, white for JPEG) */
    backgroundColor?: string;
    /** File name for download (without extension) */
    fileName?: string;
}

/**
 * Export result containing image data.
 */
export interface ExportResult {
    /** Base64 data URL of the image */
    dataUrl: string;
    /** Image format */
    format: string;
    /** File name with extension */
    fileName: string;
}

/**
 * Export a chart as an image.
 *
 * Supports both Chart.js charts (via toBase64Image) and SVG elements.
 *
 * Example:
 * ```typescript
 * const result = await exportChartAsImage(chartInstance, {
 *     format: 'png',
 *     fileName: 'progress-chart'
 * });
 * // result.dataUrl contains the image data URL
 * ```
 */
export async function exportChartAsImage(
    chart: { toBase64Image?: (type?: string, quality?: number) => string } | HTMLElement,
    options: ExportOptions = {}
): Promise<ExportResult> {
    const {
        format = 'png',
        quality = 1.0,
        backgroundColor,
        fileName = 'chart'
    } = options;

    let dataUrl: string;

    // Check if it's a Chart.js chart with toBase64Image method
    if ('toBase64Image' in chart && typeof chart.toBase64Image === 'function') {
        const mimeType = format === 'jpeg' ? 'image/jpeg' : 'image/png';
        dataUrl = chart.toBase64Image(mimeType, quality);
    }
    // Check if it's an SVG element
    else if (chart instanceof HTMLElement) {
        const svg = chart.querySelector('svg') || (chart.tagName === 'svg' ? chart : null);
        if (svg) {
            if (format === 'svg') {
                dataUrl = svgToDataUrl(svg as SVGElement);
            } else {
                dataUrl = await svgToRasterDataUrl(svg as SVGElement, format, quality, backgroundColor);
            }
        } else {
            // Try to find a canvas element
            const canvas = chart.querySelector('canvas');
            if (canvas) {
                const mimeType = format === 'jpeg' ? 'image/jpeg' : 'image/png';
                dataUrl = canvas.toDataURL(mimeType, quality);
            } else {
                throw new Error('No SVG or canvas element found for export');
            }
        }
    }
    else {
        throw new Error('Unsupported chart type for export');
    }

    return {
        dataUrl,
        format,
        fileName: `${fileName}.${format}`
    };
}

/**
 * Export multiple charts and combine them into a single result set.
 */
export async function exportAllCharts(
    charts: Array<{
        name: string;
        chart: { toBase64Image?: () => string } | HTMLElement;
    }>,
    options: ExportOptions = {}
): Promise<ExportResult[]> {
    const results: ExportResult[] = [];

    for (const { name, chart } of charts) {
        const result = await exportChartAsImage(chart, {
            ...options,
            fileName: name
        });
        results.push(result);
    }

    return results;
}

/**
 * Download an exported chart as a file.
 */
export function downloadExportedChart(result: ExportResult): void {
    const link = document.createElement('a');
    link.href = result.dataUrl;
    link.download = result.fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Copy chart image to clipboard.
 */
export async function copyChartToClipboard(
    chart: { toBase64Image?: () => string } | HTMLElement
): Promise<boolean> {
    try {
        const result = await exportChartAsImage(chart, { format: 'png' });

        // Convert data URL to blob
        const response = await fetch(result.dataUrl);
        const blob = await response.blob();

        // Use Clipboard API
        await navigator.clipboard.write([
            new ClipboardItem({
                'image/png': blob
            })
        ]);

        return true;
    } catch (error) {
        console.error('Failed to copy chart to clipboard:', error);
        return false;
    }
}

/**
 * Convert SVG element to data URL.
 */
function svgToDataUrl(svg: SVGElement): string {
    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(svg);
    const base64 = btoa(unescape(encodeURIComponent(svgStr)));
    return `data:image/svg+xml;base64,${base64}`;
}

/**
 * Convert SVG element to raster image data URL.
 */
async function svgToRasterDataUrl(
    svg: SVGElement,
    format: 'png' | 'jpeg',
    quality: number,
    backgroundColor?: string
): Promise<string> {
    return new Promise((resolve, reject) => {
        const svgDataUrl = svgToDataUrl(svg);

        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = parseInt(svg.getAttribute('width') || '600', 10);
            canvas.height = parseInt(svg.getAttribute('height') || '400', 10);

            const ctx = canvas.getContext('2d');
            if (!ctx) {
                reject(new Error('Failed to get canvas 2D context'));
                return;
            }

            // Fill background if specified (or white for JPEG)
            if (backgroundColor || format === 'jpeg') {
                ctx.fillStyle = backgroundColor || '#ffffff';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
            }

            ctx.drawImage(img, 0, 0);

            const mimeType = format === 'jpeg' ? 'image/jpeg' : 'image/png';
            resolve(canvas.toDataURL(mimeType, quality));
        };
        img.onerror = () => {
            reject(new Error('Failed to load SVG image'));
        };
        img.src = svgDataUrl;
    });
}

/**
 * Create a summary report image combining multiple charts.
 */
export async function createSummaryReport(
    charts: Array<{
        title: string;
        dataUrl: string;
    }>,
    options: {
        width?: number;
        padding?: number;
        titleHeight?: number;
        backgroundColor?: string;
    } = {}
): Promise<string> {
    const {
        width = 800,
        padding = 20,
        titleHeight = 30,
        backgroundColor = '#ffffff'
    } = options;

    // Calculate total height
    const chartHeight = 300; // Assume standard chart height
    const totalHeight = padding + charts.length * (titleHeight + chartHeight + padding);

    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = totalHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) {
        throw new Error('Failed to get canvas 2D context');
    }

    // Fill background
    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, width, totalHeight);

    // Draw each chart
    let y = padding;
    for (const chart of charts) {
        // Draw title
        ctx.fillStyle = '#333333';
        ctx.font = 'bold 16px -apple-system, BlinkMacSystemFont, sans-serif';
        ctx.fillText(chart.title, padding, y + 20);
        y += titleHeight;

        // Load and draw chart image
        const img = await loadImage(chart.dataUrl);
        const aspectRatio = img.width / img.height;
        const drawWidth = width - 2 * padding;
        const drawHeight = drawWidth / aspectRatio;

        ctx.drawImage(img, padding, y, drawWidth, Math.min(drawHeight, chartHeight));
        y += chartHeight + padding;
    }

    return canvas.toDataURL('image/png');
}

/**
 * Load an image from a data URL.
 */
function loadImage(dataUrl: string): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = dataUrl;
    });
}
