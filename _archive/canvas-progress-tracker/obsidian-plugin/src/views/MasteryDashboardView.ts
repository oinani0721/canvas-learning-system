/**
 * MasteryDashboardView - Canvas Learning System
 *
 * Sidebar dashboard displaying BKT + FSRS hybrid mastery proficiency.
 * Canvas colors are student-controlled; this view shows system-computed mastery.
 *
 * Features:
 * - Collapsible tree: Topic -> Concept
 * - Dual value display: "AI: X% | You: Y%"
 * - Override controls (click level label -> dropdown)
 * - Pin icon for overrides, arrows for self-assess divergence
 * - SVG progress bars with level colors
 * - Overall proficiency at bottom
 */

import { ItemView, WorkspaceLeaf, setIcon, Menu } from 'obsidian';
import type CanvasReviewPlugin from '../../main';
import {
    MasteryService,
    createMasteryService,
    MasteryConceptResponse,
    MasteryBatchResponse,
    MASTERY_LEVELS,
} from '../services/MasteryService';

export const VIEW_TYPE_MASTERY_DASHBOARD = 'mastery-proficiency-dashboard';

// ============================================================================
// MasteryDashboardView
// ============================================================================

export class MasteryDashboardView extends ItemView {
    private plugin: CanvasReviewPlugin;
    private masteryService: MasteryService;
    private data: MasteryBatchResponse | null = null;
    private collapsedTopics: Set<string> = new Set();
    private refreshTimeout: ReturnType<typeof setTimeout> | null = null;

    constructor(leaf: WorkspaceLeaf, plugin: CanvasReviewPlugin) {
        super(leaf);
        this.plugin = plugin;

        const apiBaseUrl = (plugin as any).settings?.claudeCodeUrl || 'http://localhost:8000';
        this.masteryService = createMasteryService({
            apiBaseUrl: `${apiBaseUrl}/api/v1`,
            enableLogging: (plugin as any).settings?.debugMode ?? false,
        });
    }

    getViewType(): string {
        return VIEW_TYPE_MASTERY_DASHBOARD;
    }

    getDisplayText(): string {
        return 'Mastery Dashboard';
    }

    getIcon(): string {
        return 'bar-chart-3';
    }

    async onOpen(): Promise<void> {
        const container = this.containerEl.children[1] as HTMLElement;
        container.empty();
        container.addClass('mastery-dashboard-container');

        this.renderLoading(container);
        await this.refresh();

        // Auto-refresh when mastery data changes (scoring, self-assess, etc.)
        this.registerEvent(
            this.app.workspace.on('mastery-updated' as any, () => this.scheduleRefresh())
        );
    }

    async onClose(): Promise<void> {
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
            this.refreshTimeout = null;
        }
    }

    /**
     * Debounced refresh — prevents hammering the API during batch operations.
     * 500ms debounce matches NodeColorChangeWatcher's debounce interval.
     */
    private scheduleRefresh(): void {
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
        }
        this.refreshTimeout = setTimeout(() => {
            this.refreshTimeout = null;
            this.refresh();
        }, 500);
    }

    // ========================================================================
    // Data
    // ========================================================================

    async refresh(): Promise<void> {
        this.data = await this.masteryService.getBatchMastery();
        this.render();
    }

    // ========================================================================
    // Render
    // ========================================================================

    private render(): void {
        const container = this.containerEl.children[1] as HTMLElement;
        container.empty();
        container.addClass('mastery-dashboard-container');

        if (!this.data || this.data.concepts.length === 0) {
            this.renderEmpty(container);
            return;
        }

        // Header
        this.renderHeader(container);

        // Topic tree
        const treeEl = container.createDiv({ cls: 'mastery-tree' });
        this.renderTopicTree(treeEl);

        // Footer: overall proficiency
        this.renderFooter(container);
    }

    private renderLoading(container: HTMLElement): void {
        const loadingEl = container.createDiv({ cls: 'mastery-loading' });
        loadingEl.setText('Loading mastery data...');
    }

    private renderEmpty(container: HTMLElement): void {
        const emptyEl = container.createDiv({ cls: 'mastery-empty' });
        emptyEl.setText('No mastery data yet. Start interacting with concepts to see proficiency tracking.');

        const refreshBtn = container.createEl('button', {
            cls: 'mastery-refresh-btn',
            text: 'Refresh',
        });
        refreshBtn.addEventListener('click', () => this.refresh());
    }

    private renderHeader(container: HTMLElement): void {
        const headerEl = container.createDiv({ cls: 'mastery-header' });

        const titleEl = headerEl.createDiv({ cls: 'mastery-header__title' });
        titleEl.setText('Mastery Dashboard');

        const actionsEl = headerEl.createDiv({ cls: 'mastery-header__actions' });
        const refreshBtn = actionsEl.createEl('button', { cls: 'mastery-header__refresh clickable-icon' });
        setIcon(refreshBtn, 'refresh-cw');
        refreshBtn.setAttribute('aria-label', 'Refresh');
        refreshBtn.addEventListener('click', () => this.refresh());
    }

    // ========================================================================
    // Topic Tree
    // ========================================================================

    private renderTopicTree(treeEl: HTMLElement): void {
        if (!this.data) return;

        // Group concepts by topic
        const topicMap = new Map<string, MasteryConceptResponse[]>();
        for (const c of this.data.concepts) {
            const topic = c.topic || 'Unknown';
            if (!topicMap.has(topic)) topicMap.set(topic, []);
            topicMap.get(topic)!.push(c);
        }

        // Sort topics by exam weight (descending)
        const topicEntries = [...topicMap.entries()].sort((a, b) => {
            const wA = this.data!.topic_summary[a[0]]?.exam_weight ?? 0;
            const wB = this.data!.topic_summary[b[0]]?.exam_weight ?? 0;
            return wB - wA;
        });

        for (const [topic, concepts] of topicEntries) {
            this.renderTopicSection(treeEl, topic, concepts);
        }
    }

    private renderTopicSection(
        parent: HTMLElement,
        topic: string,
        concepts: MasteryConceptResponse[],
    ): void {
        const summary = this.data?.topic_summary[topic];
        const avgProf = summary?.avg_proficiency ?? 0;
        const examWeight = summary?.exam_weight ?? 0;
        const isCollapsed = this.collapsedTopics.has(topic);

        // Topic header
        const topicEl = parent.createDiv({ cls: 'mastery-topic' });
        const headerEl = topicEl.createDiv({
            cls: `mastery-topic__header ${isCollapsed ? 'is-collapsed' : ''}`,
        });

        // Collapse toggle
        const toggleEl = headerEl.createSpan({ cls: 'mastery-topic__toggle' });
        setIcon(toggleEl, isCollapsed ? 'chevron-right' : 'chevron-down');

        // Topic name + exam weight
        const nameEl = headerEl.createSpan({ cls: 'mastery-topic__name' });
        nameEl.setText(`${topic}`);
        if (examWeight > 0) {
            const weightEl = headerEl.createSpan({ cls: 'mastery-topic__weight' });
            weightEl.setText(`(${examWeight}pts)`);
        }

        // Topic proficiency
        const profEl = headerEl.createSpan({ cls: 'mastery-topic__prof' });
        const level = this.profToLevel(avgProf);
        const levelMeta = MASTERY_LEVELS[level];
        profEl.setText(`${Math.round(avgProf * 100)}% ${levelMeta.label}`);
        profEl.style.color = levelMeta.color;

        // Progress bar
        this.renderProgressBar(headerEl, avgProf, levelMeta.color);

        // Click to toggle
        headerEl.addEventListener('click', () => {
            if (isCollapsed) {
                this.collapsedTopics.delete(topic);
            } else {
                this.collapsedTopics.add(topic);
            }
            this.render();
        });

        // Concept rows (if not collapsed)
        if (!isCollapsed) {
            const conceptsEl = topicEl.createDiv({ cls: 'mastery-topic__concepts' });
            // Sort concepts by proficiency ascending (weakest first)
            const sorted = [...concepts].sort(
                (a, b) => a.effective_proficiency - b.effective_proficiency,
            );
            for (const concept of sorted) {
                this.renderConceptRow(conceptsEl, concept);
            }
        }
    }

    // ========================================================================
    // Concept Row
    // ========================================================================

    private renderConceptRow(parent: HTMLElement, concept: MasteryConceptResponse): void {
        const rowEl = parent.createDiv({ cls: 'mastery-concept' });

        const level = concept.mastery_level;
        const levelMeta = MASTERY_LEVELS[level];
        const profPct = Math.round(concept.effective_proficiency * 100);

        // Color dot
        const dotEl = rowEl.createSpan({ cls: 'mastery-concept__dot' });
        dotEl.style.backgroundColor = levelMeta.color;

        // Concept name
        const nameEl = rowEl.createSpan({ cls: 'mastery-concept__name' });
        nameEl.setText(concept.name);

        // Proficiency percentage
        const profEl = rowEl.createSpan({ cls: 'mastery-concept__prof' });
        profEl.setText(`${profPct}%`);

        // Progress bar
        this.renderProgressBar(rowEl, concept.effective_proficiency, levelMeta.color);

        // Level label (clickable for override)
        const labelEl = rowEl.createSpan({
            cls: `mastery-concept__label mastery-concept__label--${levelMeta.key}`,
        });
        labelEl.setText(levelMeta.label);
        labelEl.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showOverrideMenu(concept, labelEl);
        });

        // Override pin icon
        if (concept.override_active) {
            const pinEl = rowEl.createSpan({ cls: 'mastery-concept__pin' });
            pinEl.setText('\uD83D\uDCCC'); // 📌
            pinEl.setAttribute('aria-label', 'Override active');
        }

        // Fluent verification checkmark
        if (concept.fluent_count >= 2) {
            const checkEl = rowEl.createSpan({ cls: 'mastery-concept__verified' });
            checkEl.setText('\u2713'); // ✓
            checkEl.setAttribute('aria-label', 'Explanation verified');
        }

        // Dual values row: "AI: X% | You: Y%"
        const dualEl = rowEl.createDiv({ cls: 'mastery-concept__dual' });
        const aiVal = Math.round(concept.p_mastery * 100);
        dualEl.createSpan({ cls: 'mastery-concept__dual-ai', text: `AI: ${aiVal}%` });

        if (concept.self_assess_value !== null) {
            const selfVal = Math.round(concept.self_assess_value * 100);
            const arrow = selfVal > aiVal ? '\u2191' : selfVal < aiVal ? '\u2193' : '';
            dualEl.createSpan({
                cls: 'mastery-concept__dual-self',
                text: ` | You: ${selfVal}%${arrow}`,
            });
        }

        if (concept.override_active && concept.override_value !== null) {
            const overVal = Math.round(concept.override_value * 100);
            dualEl.createSpan({
                cls: 'mastery-concept__dual-override',
                text: ` | Override: ${overVal}%`,
            });
        }
    }

    // ========================================================================
    // Progress Bar (SVG)
    // ========================================================================

    private renderProgressBar(parent: HTMLElement, value: number, color: string): void {
        const barEl = parent.createDiv({ cls: 'mastery-progress' });
        const pct = Math.max(0, Math.min(100, Math.round(value * 100)));

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', '0 0 100 6');
        svg.setAttribute('class', 'mastery-progress__svg');

        // Background track
        const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        bg.setAttribute('x', '0');
        bg.setAttribute('y', '0');
        bg.setAttribute('width', '100');
        bg.setAttribute('height', '6');
        bg.setAttribute('rx', '3');
        bg.setAttribute('fill', 'var(--background-modifier-border)');
        svg.appendChild(bg);

        // Fill
        if (pct > 0) {
            const fill = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            fill.setAttribute('x', '0');
            fill.setAttribute('y', '0');
            fill.setAttribute('width', String(pct));
            fill.setAttribute('height', '6');
            fill.setAttribute('rx', '3');
            fill.setAttribute('fill', color);
            svg.appendChild(fill);
        }

        barEl.appendChild(svg);
    }

    // ========================================================================
    // Override Menu
    // ========================================================================

    private showOverrideMenu(concept: MasteryConceptResponse, targetEl: HTMLElement): void {
        const menu = new Menu();

        // Override options
        for (const level of MASTERY_LEVELS) {
            if (level.level === 0) continue; // Skip "Not Assessed"
            menu.addItem((item) => {
                item.setTitle(`${level.label}`)
                    .setIcon(concept.mastery_level === level.level ? 'check' : '')
                    .onClick(async () => {
                        await this.masteryService.setOverride(concept.concept_id, level.key);
                        await this.refresh();
                    });
            });
        }

        // Separator + Reset
        menu.addSeparator();
        menu.addItem((item) => {
            item.setTitle('Reset to AI')
                .setIcon('rotate-ccw')
                .onClick(async () => {
                    await this.masteryService.resetOverride(concept.concept_id);
                    await this.refresh();
                });
        });

        menu.showAtMouseEvent(new MouseEvent('click', {
            clientX: targetEl.getBoundingClientRect().left,
            clientY: targetEl.getBoundingClientRect().bottom,
        }));
    }

    // ========================================================================
    // Footer
    // ========================================================================

    private renderFooter(container: HTMLElement): void {
        if (!this.data || this.data.concepts.length === 0) return;

        const footerEl = container.createDiv({ cls: 'mastery-footer' });

        // Overall proficiency
        const allProfs = this.data.concepts.map((c) => c.effective_proficiency);
        const overall = allProfs.reduce((a, b) => a + b, 0) / allProfs.length;
        const overallPct = Math.round(overall * 100);
        const overallLevel = this.profToLevel(overall);
        const overallMeta = MASTERY_LEVELS[overallLevel];

        const overallEl = footerEl.createDiv({ cls: 'mastery-footer__overall' });
        overallEl.innerHTML = `<strong>Overall: ${overallPct}% ${overallMeta.label}</strong>`;
        overallEl.style.color = overallMeta.color;

        // Legend
        const legendEl = footerEl.createDiv({ cls: 'mastery-footer__legend' });
        for (const level of MASTERY_LEVELS) {
            const itemEl = legendEl.createSpan({ cls: 'mastery-legend__item' });
            const dot = itemEl.createSpan({ cls: 'mastery-legend__dot' });
            dot.style.backgroundColor = level.color;
            itemEl.createSpan({ text: ` ${level.label}` });
        }

        // Symbol legend
        const symbolEl = footerEl.createDiv({ cls: 'mastery-footer__symbols' });
        symbolEl.setText('\uD83D\uDCCC = Override | \u2191\u2193 = Self-assess divergence | \u2713 = Verified');
    }

    // ========================================================================
    // Helpers
    // ========================================================================

    private profToLevel(prof: number): number {
        if (prof < 0.001) return 0;
        if (prof < 0.40) return 1;
        if (prof < 0.70) return 2;
        if (prof < 0.90) return 3;
        return 4; // Note: true Mastered requires fluent gate, but for display we use 4
    }
}
