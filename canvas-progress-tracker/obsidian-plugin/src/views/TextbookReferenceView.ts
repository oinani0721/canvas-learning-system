/**
 * Textbook Reference View - Canvas Learning System Cross-Canvas Associations
 *
 * UI components for displaying textbook references on Canvas nodes.
 * Implements Story 16.6: 教材引用显示
 *
 * @module views/TextbookReferenceView
 * @version 1.0.0
 *
 * ✅ Verified from @obsidian-canvas Skill (Canvas Nodes, Workspace API)
 * ✅ Verified from Story 16.6 Dev Notes (UI design, navigation)
 */

import { App, TFile, Notice, WorkspaceLeaf } from 'obsidian';

/**
 * Textbook reference structure
 * ✅ Verified from Story 16.6 SDD Schema
 */
export interface TextbookReference {
    textbook_canvas: string;
    textbook_name: string;
    section_name: string;
    node_id: string;
    page_number?: number;
}

/**
 * Canvas View interface for type safety
 * ✅ Verified from @obsidian-canvas Skill (Canvas View)
 */
interface CanvasView {
    canvas: {
        nodes: Map<string, CanvasNode>;
        selectOnly: (node: CanvasNode) => void;
        zoomToSelection: () => void;
    };
}

/**
 * Canvas Node interface
 * ✅ Verified from @obsidian-canvas Skill (Canvas Nodes)
 */
interface CanvasNode {
    id: string;
    nodeEl: HTMLElement;
}

/**
 * Textbook Indicator Component
 *
 * Displays a textbook icon (📖) on nodes that have textbook references.
 *
 * ✅ Verified from @obsidian-canvas Skill (Canvas Nodes - DOM manipulation)
 */
export class TextbookIndicator {
    private nodeEl: HTMLElement;
    private indicatorEl: HTMLElement | null = null;
    private references: TextbookReference[];
    private onHover: (references: TextbookReference[], targetEl: HTMLElement) => void;

    /**
     * Creates a textbook indicator for a node
     *
     * @param nodeEl - The node's DOM element
     * @param references - List of textbook references
     * @param onHover - Callback when indicator is hovered
     */
    constructor(
        nodeEl: HTMLElement,
        references: TextbookReference[],
        onHover: (references: TextbookReference[], targetEl: HTMLElement) => void
    ) {
        this.nodeEl = nodeEl;
        this.references = references;
        this.onHover = onHover;

        if (references.length > 0) {
            this.render();
        }
    }

    /**
     * Render the indicator
     */
    private render(): void {
        this.indicatorEl = document.createElement('div');
        this.indicatorEl.className = 'textbook-indicator';
        this.indicatorEl.textContent = '📖';
        this.indicatorEl.setAttribute('aria-label', `${this.references.length}个教材引用`);

        // Position in top-right corner
        this.indicatorEl.style.cssText = `
            position: absolute;
            top: 4px;
            right: 4px;
            font-size: 14px;
            cursor: pointer;
            opacity: 0.7;
            transition: opacity 0.2s ease;
            z-index: 10;
        `;

        // Hover effects
        this.indicatorEl.addEventListener('mouseenter', (e) => {
            this.indicatorEl!.style.opacity = '1';
            this.onHover(this.references, e.target as HTMLElement);
        });

        this.indicatorEl.addEventListener('mouseleave', () => {
            this.indicatorEl!.style.opacity = '0.7';
        });

        this.nodeEl.style.position = 'relative';
        this.nodeEl.appendChild(this.indicatorEl);
    }

    /**
     * Update references
     */
    updateReferences(references: TextbookReference[]): void {
        this.references = references;

        if (references.length === 0 && this.indicatorEl) {
            this.destroy();
        } else if (references.length > 0 && !this.indicatorEl) {
            this.render();
        }

        if (this.indicatorEl) {
            this.indicatorEl.setAttribute('aria-label', `${references.length}个教材引用`);
        }
    }

    /**
     * Destroy the indicator
     */
    destroy(): void {
        this.indicatorEl?.remove();
        this.indicatorEl = null;
    }
}

/**
 * Textbook Tooltip Component
 *
 * Shows detailed textbook reference information on hover.
 *
 * ✅ Verified from @obsidian-canvas Skill (DOM manipulation)
 */
export class TextbookTooltip {
    private app: App;
    private tooltipEl: HTMLElement | null = null;
    private navigator: CanvasNavigator;

    constructor(app: App) {
        this.app = app;
        this.navigator = new CanvasNavigator(app);
    }

    /**
     * Show tooltip at target element
     *
     * @param references - Textbook references to display
     * @param targetEl - Element to position tooltip near
     */
    show(references: TextbookReference[], targetEl: HTMLElement): void {
        this.hide();

        if (references.length === 0) return;

        this.tooltipEl = document.createElement('div');
        this.tooltipEl.className = 'textbook-tooltip';
        this.tooltipEl.style.cssText = `
            position: fixed;
            background: var(--background-primary);
            border: 1px solid var(--background-modifier-border);
            border-radius: 8px;
            padding: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            min-width: 250px;
            max-width: 350px;
        `;

        // Header
        const header = document.createElement('div');
        header.style.cssText = `
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--text-normal);
        `;
        header.textContent = references.length === 1
            ? '相关教材:'
            : `${references.length}个教材引用:`;
        this.tooltipEl.appendChild(header);

        // Reference list
        const list = document.createElement('div');
        list.style.cssText = `
            display: flex;
            flex-direction: column;
            gap: 8px;
        `;

        // Show max 5 references
        const displayRefs = references.slice(0, 5);

        for (const ref of displayRefs) {
            const item = this.createReferenceItem(ref);
            list.appendChild(item);
        }

        if (references.length > 5) {
            const moreText = document.createElement('div');
            moreText.style.cssText = `
                color: var(--text-muted);
                font-size: 12px;
            `;
            moreText.textContent = `+${references.length - 5} more...`;
            list.appendChild(moreText);
        }

        this.tooltipEl.appendChild(list);

        // Position tooltip
        const rect = targetEl.getBoundingClientRect();
        this.tooltipEl.style.left = `${rect.right + 8}px`;
        this.tooltipEl.style.top = `${rect.top}px`;

        document.body.appendChild(this.tooltipEl);

        // Auto-hide on mouse leave (with delay)
        this.tooltipEl.addEventListener('mouseleave', () => {
            setTimeout(() => this.hide(), 200);
        });
    }

    /**
     * Create a reference item element
     */
    private createReferenceItem(ref: TextbookReference): HTMLElement {
        const item = document.createElement('div');
        item.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px;
            background: var(--background-secondary);
            border-radius: 4px;
        `;

        const info = document.createElement('div');
        info.style.cssText = `
            display: flex;
            flex-direction: column;
            gap: 2px;
        `;

        const name = document.createElement('div');
        name.style.cssText = `
            font-weight: 500;
            color: var(--text-normal);
        `;
        name.textContent = `📖 ${ref.textbook_name}`;
        info.appendChild(name);

        const section = document.createElement('div');
        section.style.cssText = `
            font-size: 12px;
            color: var(--text-muted);
        `;
        section.textContent = `> ${ref.section_name}`;
        info.appendChild(section);

        item.appendChild(info);

        // Jump button
        const jumpBtn = document.createElement('button');
        jumpBtn.style.cssText = `
            padding: 4px 8px;
            background: var(--interactive-accent);
            color: var(--text-on-accent);
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        `;
        jumpBtn.textContent = '跳转 →';
        jumpBtn.addEventListener('click', async () => {
            await this.navigator.navigateToNode(ref.textbook_canvas, ref.node_id);
            this.hide();
        });

        item.appendChild(jumpBtn);

        return item;
    }

    /**
     * Hide the tooltip
     */
    hide(): void {
        this.tooltipEl?.remove();
        this.tooltipEl = null;
    }

    /**
     * Cleanup
     */
    destroy(): void {
        this.hide();
    }
}

/**
 * Canvas Navigator Service
 *
 * Handles cross-Canvas navigation with scroll and highlight.
 *
 * ✅ Verified from @obsidian-canvas Skill (Workspace API, Canvas selectOnly)
 */
export class CanvasNavigator {
    private app: App;
    private sourceCanvas: string | null = null;
    private breadcrumb: NavigationBreadcrumb | null = null;

    constructor(app: App) {
        this.app = app;
    }

    /**
     * Navigate to a specific node in a Canvas
     *
     * @param canvasPath - Path to the target Canvas file
     * @param nodeId - ID of the target node
     */
    async navigateToNode(canvasPath: string, nodeId: string): Promise<void> {
        // Save source canvas for breadcrumb
        const activeFile = this.app.workspace.getActiveFile();
        if (activeFile?.extension === 'canvas') {
            this.sourceCanvas = activeFile.path;
        }

        // Get target file
        const file = this.app.vault.getAbstractFileByPath(canvasPath);
        if (!(file instanceof TFile)) {
            new Notice(`Canvas not found: ${canvasPath}`);
            return;
        }

        try {
            // Open the canvas
            const leaf = this.app.workspace.getLeaf(false);
            await leaf.openFile(file);

            // Wait for canvas to be ready
            await this.waitForCanvasReady(leaf);

            // Select and zoom to node
            const canvasView = leaf.view as unknown as CanvasView;
            const node = canvasView.canvas.nodes.get(nodeId);

            if (node) {
                canvasView.canvas.selectOnly(node);
                canvasView.canvas.zoomToSelection();
                this.highlightNode(node);

                // Show breadcrumb
                if (this.sourceCanvas) {
                    this.showBreadcrumb(this.sourceCanvas, canvasPath);
                }
            } else {
                new Notice(`节点未找到: ${nodeId}`);
            }
        } catch (error) {
            console.error('[CanvasNavigator] Navigation failed:', error);
            new Notice(`导航失败: ${(error as Error).message}`);
        }
    }

    /**
     * Wait for canvas view to be fully loaded
     */
    private async waitForCanvasReady(leaf: WorkspaceLeaf): Promise<void> {
        return new Promise((resolve) => {
            // Poll for canvas readiness
            const checkReady = (): void => {
                const view = leaf.view as unknown as CanvasView;
                if (view.canvas && view.canvas.nodes) {
                    resolve();
                } else {
                    setTimeout(checkReady, 100);
                }
            };

            // Start checking after a short delay
            setTimeout(checkReady, 200);
        });
    }

    /**
     * Highlight a node with pulse animation
     *
     * ✅ Verified from Story 16.6 Dev Notes (2-second highlight)
     */
    private highlightNode(node: CanvasNode): void {
        const el = node.nodeEl;
        el.classList.add('textbook-highlight');

        // Apply inline animation if CSS not loaded
        el.style.animation = 'pulse-highlight 0.5s ease-in-out 4';

        // Remove highlight after 2 seconds
        setTimeout(() => {
            el.classList.remove('textbook-highlight');
            el.style.animation = '';
        }, 2000);
    }

    /**
     * Show navigation breadcrumb
     */
    private showBreadcrumb(sourceCanvas: string, targetCanvas: string): void {
        if (this.breadcrumb) {
            this.breadcrumb.destroy();
        }

        this.breadcrumb = new NavigationBreadcrumb(
            this.app,
            sourceCanvas,
            targetCanvas,
            () => this.navigateBack()
        );
    }

    /**
     * Navigate back to source canvas
     */
    private async navigateBack(): Promise<void> {
        if (!this.sourceCanvas) return;

        const file = this.app.vault.getAbstractFileByPath(this.sourceCanvas);
        if (file instanceof TFile) {
            const leaf = this.app.workspace.getLeaf(false);
            await leaf.openFile(file);
        }

        this.sourceCanvas = null;
        this.breadcrumb?.destroy();
        this.breadcrumb = null;
    }

    /**
     * Get source canvas path
     */
    getSourceCanvas(): string | null {
        return this.sourceCanvas;
    }

    /**
     * Cleanup
     */
    destroy(): void {
        this.breadcrumb?.destroy();
    }
}

/**
 * Navigation Breadcrumb Component
 *
 * Shows navigation path at top of canvas with back button.
 *
 * ✅ Verified from Story 16.6 Dev Notes (breadcrumb design, 3-second fade)
 */
export class NavigationBreadcrumb {
    private app: App;
    private breadcrumbEl: HTMLElement | null = null;
    private fadeTimeout: NodeJS.Timeout | null = null;

    constructor(
        app: App,
        sourceCanvas: string,
        targetCanvas: string,
        onBack: () => void
    ) {
        this.app = app;
        this.render(sourceCanvas, targetCanvas, onBack);
    }

    /**
     * Render the breadcrumb
     */
    private render(sourceCanvas: string, targetCanvas: string, onBack: () => void): void {
        this.breadcrumbEl = document.createElement('div');
        this.breadcrumbEl.className = 'navigation-breadcrumb';
        this.breadcrumbEl.style.cssText = `
            position: fixed;
            top: 50px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--background-primary);
            border: 1px solid var(--background-modifier-border);
            border-radius: 8px;
            padding: 8px 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 999;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: opacity 0.5s ease;
        `;

        // Extract canvas names
        const sourceName = this.getCanvasName(sourceCanvas);
        const targetName = this.getCanvasName(targetCanvas);

        // Back button
        const backBtn = document.createElement('button');
        backBtn.style.cssText = `
            padding: 4px 8px;
            background: var(--background-secondary);
            border: 1px solid var(--background-modifier-border);
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        `;
        backBtn.textContent = '← 返回';
        backBtn.addEventListener('click', onBack);
        this.breadcrumbEl.appendChild(backBtn);

        // Path display
        const pathEl = document.createElement('span');
        pathEl.style.cssText = `
            color: var(--text-muted);
            font-size: 13px;
        `;
        pathEl.innerHTML = `${sourceName} <span style="color: var(--text-faint)">→</span> <strong>${targetName}</strong>`;
        this.breadcrumbEl.appendChild(pathEl);

        // Close button
        const closeBtn = document.createElement('button');
        closeBtn.style.cssText = `
            padding: 2px 6px;
            background: none;
            border: none;
            cursor: pointer;
            color: var(--text-muted);
            font-size: 16px;
        `;
        closeBtn.textContent = '×';
        closeBtn.addEventListener('click', () => this.destroy());
        this.breadcrumbEl.appendChild(closeBtn);

        document.body.appendChild(this.breadcrumbEl);

        // Mouse hover prevents fade
        this.breadcrumbEl.addEventListener('mouseenter', () => {
            this.cancelFade();
            this.breadcrumbEl!.style.opacity = '1';
        });

        this.breadcrumbEl.addEventListener('mouseleave', () => {
            this.startFade();
        });

        // Auto-fade after 3 seconds
        this.startFade();
    }

    /**
     * Extract canvas display name from path
     */
    private getCanvasName(path: string): string {
        const name = path.split('/').pop() || path;
        return name.replace('.canvas', '');
    }

    /**
     * Start fade out timer
     */
    private startFade(): void {
        this.fadeTimeout = setTimeout(() => {
            if (this.breadcrumbEl) {
                this.breadcrumbEl.style.opacity = '0';
                setTimeout(() => this.destroy(), 500);
            }
        }, 3000);
    }

    /**
     * Cancel fade timer
     */
    private cancelFade(): void {
        if (this.fadeTimeout) {
            clearTimeout(this.fadeTimeout);
            this.fadeTimeout = null;
        }
    }

    /**
     * Destroy the breadcrumb
     */
    destroy(): void {
        this.cancelFade();
        this.breadcrumbEl?.remove();
        this.breadcrumbEl = null;
    }
}

/**
 * Textbook Reference View Manager
 *
 * Manages all textbook reference UI components for a Canvas.
 */
export class TextbookReferenceViewManager {
    private app: App;
    private indicators: Map<string, TextbookIndicator> = new Map();
    private tooltip: TextbookTooltip;
    private navigator: CanvasNavigator;

    constructor(app: App) {
        this.app = app;
        this.tooltip = new TextbookTooltip(app);
        this.navigator = new CanvasNavigator(app);
    }

    /**
     * Register a node with its textbook references
     *
     * @param nodeId - Node ID
     * @param nodeEl - Node's DOM element
     * @param references - Textbook references for this node
     */
    registerNode(nodeId: string, nodeEl: HTMLElement, references: TextbookReference[]): void {
        // Remove existing indicator if any
        this.unregisterNode(nodeId);

        if (references.length > 0) {
            const indicator = new TextbookIndicator(
                nodeEl,
                references,
                (refs, targetEl) => this.tooltip.show(refs, targetEl)
            );
            this.indicators.set(nodeId, indicator);
        }
    }

    /**
     * Update references for a node
     */
    updateNode(nodeId: string, references: TextbookReference[]): void {
        const indicator = this.indicators.get(nodeId);
        if (indicator) {
            indicator.updateReferences(references);
        }
    }

    /**
     * Unregister a node
     */
    unregisterNode(nodeId: string): void {
        const indicator = this.indicators.get(nodeId);
        if (indicator) {
            indicator.destroy();
            this.indicators.delete(nodeId);
        }
    }

    /**
     * Navigate to a textbook node
     */
    async navigateTo(canvasPath: string, nodeId: string): Promise<void> {
        await this.navigator.navigateToNode(canvasPath, nodeId);
    }

    /**
     * Cleanup all components
     */
    destroy(): void {
        for (const indicator of this.indicators.values()) {
            indicator.destroy();
        }
        this.indicators.clear();
        this.tooltip.destroy();
        this.navigator.destroy();
    }
}

/**
 * Inject CSS styles for textbook reference components
 *
 * Call this once during plugin initialization.
 */
export function injectTextbookReferenceStyles(): void {
    const styleId = 'textbook-reference-styles';

    // Don't inject twice
    if (document.getElementById(styleId)) return;

    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
        /* Textbook Indicator */
        .textbook-indicator {
            position: absolute;
            top: 4px;
            right: 4px;
            font-size: 14px;
            cursor: pointer;
            opacity: 0.7;
            transition: opacity 0.2s ease;
            z-index: 10;
        }

        .textbook-indicator:hover {
            opacity: 1;
        }

        /* Textbook Tooltip */
        .textbook-tooltip {
            position: fixed;
            background: var(--background-primary);
            border: 1px solid var(--background-modifier-border);
            border-radius: 8px;
            padding: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            min-width: 250px;
            max-width: 350px;
        }

        /* Node Highlight Animation */
        .textbook-highlight {
            animation: pulse-highlight 0.5s ease-in-out 4;
        }

        @keyframes pulse-highlight {
            0%, 100% {
                box-shadow: 0 0 0 0 rgba(var(--interactive-accent-rgb), 0.4);
            }
            50% {
                box-shadow: 0 0 0 8px rgba(var(--interactive-accent-rgb), 0);
            }
        }

        /* Navigation Breadcrumb */
        .navigation-breadcrumb {
            position: fixed;
            top: 50px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--background-primary);
            border: 1px solid var(--background-modifier-border);
            border-radius: 8px;
            padding: 8px 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 999;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: opacity 0.5s ease;
        }

        /* Dark theme adjustments */
        .theme-dark .textbook-tooltip {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .theme-dark .navigation-breadcrumb {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
    `;

    document.head.appendChild(style);
}
