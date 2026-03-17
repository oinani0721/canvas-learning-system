/**
 * Canvas Learning System - Exam State Service
 *
 * Manages client-side exam session state for the Obsidian plugin:
 *   - Story 6.5: discoveredNodes tracking (recursion depth, provenance)
 *   - Story 6.6: hint level state per node, skipped nodes tracking
 *   - Story 6.7: cognitive load timer with visibility change detection
 *   - Story 6.8: exam completion data aggregation
 *
 * [Source: _bmad-output/implementation-artifacts/6-5 through 6-8]
 *
 * @module ExamStateService
 */

import { requestUrl } from 'obsidian';

// ======================================================================
// Types
// ======================================================================

export interface DiscoveredNode {
    nodeId: string;
    sourceNodeId: string;
    depth: number;
    timestamp: string;
    sourceExamId: string;
}

export interface HintState {
    currentLevel: number; // 0 = no hints used, 1-4 = current level
    maxLevelUsed: number;
    hintTexts: string[];
}

export interface SkippedNode {
    nodeId: string;
    questionId: string;
    timestamp: string;
}

export type ExamStatus = 'idle' | 'in_progress' | 'paused' | 'completed';

export interface CognitiveLoadConfig {
    thresholds: number[]; // minutes
    triggeredThresholds: Set<number>;
}

// Cognitive load threshold messages (Story 6.7 AC-1)
const COGNITIVE_LOAD_MESSAGES: Record<number, string> = {
    15: '\u4f60\u5df2\u7ecf\u8003\u5bdf\u4e86 15 \u5206\u949f\uff0c\u53ef\u4ee5\u4f11\u606f\u4e00\u4e0b',
    25: '\u8fde\u7eed\u8003\u5bdf 25 \u5206\u949f\u4e86\uff0c\u5efa\u8bae\u4f11\u606f 5 \u5206\u949f',
    35: '\u5df2\u6301\u7eed 35 \u5206\u949f\uff0c\u5927\u8111\u9700\u8981\u4f11\u606f\u624d\u80fd\u66f4\u597d\u5438\u6536',
    45: '\u8fde\u7eed 45 \u5206\u949f\u4e86\uff0c\u5f3a\u70c8\u5efa\u8bae\u4f11\u606f\u3002\u4f11\u606f\u540e\u56de\u6765\u6548\u679c\u66f4\u597d',
};

/**
 * ExamStateService - Client-side exam session state management
 *
 * Tracks all exam session data locally and syncs with backend
 * through the REST API endpoints.
 */
export class ExamStateService {
    private baseUrl: string;
    private examId: string = '';
    private sourceCanvasId: string = '';
    private examMode: string = 'comprehensive';
    private status: ExamStatus = 'idle';
    private startTime: number = 0; // Date.now() when exam started
    private activeTimeMs: number = 0; // Accumulated active time
    private lastActiveTimestamp: number = 0;

    // Story 6.5: Discovered nodes tracking
    private discoveredNodes: DiscoveredNode[] = [];

    // Story 6.6: Hint and skip state
    private hintStates: Map<string, HintState> = new Map();
    private skippedNodes: SkippedNode[] = [];

    // Story 6.7: Cognitive load timer
    private timerInterval: ReturnType<typeof setInterval> | null = null;
    private cognitiveLoad: CognitiveLoadConfig = {
        thresholds: [15, 25, 35, 45],
        triggeredThresholds: new Set(),
    };
    private onRestReminder: ((message: string, minutes: number) => void) | null = null;

    // Visibility change handler reference for cleanup
    private visibilityHandler: (() => void) | null = null;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
    }

    // ======================================================================
    // Session Lifecycle
    // ======================================================================

    startExam(examId: string, sourceCanvasId: string, examMode: string): void {
        this.examId = examId;
        this.sourceCanvasId = sourceCanvasId;
        this.examMode = examMode;
        this.status = 'in_progress';
        this.startTime = Date.now();
        this.lastActiveTimestamp = Date.now();
        this.activeTimeMs = 0;
        this.discoveredNodes = [];
        this.hintStates.clear();
        this.skippedNodes = [];
        this.cognitiveLoad.triggeredThresholds.clear();

        this.startTimer();
        this.setupVisibilityDetection();
    }

    getExamId(): string {
        return this.examId;
    }

    getStatus(): ExamStatus {
        return this.status;
    }

    getActiveMinutes(): number {
        if (this.status === 'in_progress') {
            return Math.floor((this.activeTimeMs + (Date.now() - this.lastActiveTimestamp)) / 60000);
        }
        return Math.floor(this.activeTimeMs / 60000);
    }

    getActiveSeconds(): number {
        if (this.status === 'in_progress') {
            return Math.floor((this.activeTimeMs + (Date.now() - this.lastActiveTimestamp)) / 1000);
        }
        return Math.floor(this.activeTimeMs / 1000);
    }

    // ======================================================================
    // Story 6.5: Discovered Nodes
    // ======================================================================

    addDiscoveredNode(node: DiscoveredNode): void {
        this.discoveredNodes.push(node);
    }

    getDiscoveredNodes(): DiscoveredNode[] {
        return [...this.discoveredNodes];
    }

    // ======================================================================
    // Story 6.6: Hint State Management
    // ======================================================================

    getHintState(nodeId: string): HintState {
        if (!this.hintStates.has(nodeId)) {
            this.hintStates.set(nodeId, {
                currentLevel: 0,
                maxLevelUsed: 0,
                hintTexts: [],
            });
        }
        return this.hintStates.get(nodeId)!;
    }

    recordHintUsed(nodeId: string, level: number, hintText: string): void {
        const state = this.getHintState(nodeId);
        state.currentLevel = level;
        state.maxLevelUsed = Math.max(state.maxLevelUsed, level);
        state.hintTexts.push(hintText);
    }

    resetHintForNewQuestion(nodeId: string): void {
        this.hintStates.set(nodeId, {
            currentLevel: 0,
            maxLevelUsed: 0,
            hintTexts: [],
        });
    }

    canRequestHint(nodeId: string): boolean {
        const state = this.getHintState(nodeId);
        return state.currentLevel < 4;
    }

    getNextHintLevel(nodeId: string): number {
        const state = this.getHintState(nodeId);
        return Math.min(state.currentLevel + 1, 4);
    }

    // Story 6.6: Skip tracking

    addSkippedNode(nodeId: string, questionId: string): void {
        this.skippedNodes.push({
            nodeId,
            questionId,
            timestamp: new Date().toISOString(),
        });
    }

    getSkippedNodes(): SkippedNode[] {
        return [...this.skippedNodes];
    }

    // ======================================================================
    // Story 6.7: Cognitive Load Timer
    // ======================================================================

    setRestReminderCallback(callback: (message: string, minutes: number) => void): void {
        this.onRestReminder = callback;
    }

    private startTimer(): void {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }

        this.timerInterval = setInterval(() => {
            if (this.status !== 'in_progress') return;

            const elapsed = this.getActiveMinutes();

            // Check thresholds (Story 6.7 AC-1)
            for (const threshold of this.cognitiveLoad.thresholds) {
                if (elapsed >= threshold && !this.cognitiveLoad.triggeredThresholds.has(threshold)) {
                    this.cognitiveLoad.triggeredThresholds.add(threshold);
                    const message = COGNITIVE_LOAD_MESSAGES[threshold];
                    if (message && this.onRestReminder) {
                        this.onRestReminder(message, threshold);
                    }
                }
            }
        }, 10000); // Check every 10 seconds
    }

    private stopTimer(): void {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    // Story 6.7 AC-7: Visibility change detection
    private setupVisibilityDetection(): void {
        this.visibilityHandler = () => {
            if (document.hidden) {
                // Page hidden: accumulate active time and pause
                if (this.status === 'in_progress') {
                    this.activeTimeMs += Date.now() - this.lastActiveTimestamp;
                }
            } else {
                // Page visible: resume timing
                if (this.status === 'in_progress') {
                    this.lastActiveTimestamp = Date.now();
                }
            }
        };
        document.addEventListener('visibilitychange', this.visibilityHandler);
    }

    private cleanupVisibilityDetection(): void {
        if (this.visibilityHandler) {
            document.removeEventListener('visibilitychange', this.visibilityHandler);
            this.visibilityHandler = null;
        }
    }

    // ======================================================================
    // Story 6.7: Pause / Resume
    // ======================================================================

    async pauseExam(): Promise<void> {
        if (this.status !== 'in_progress') return;

        this.activeTimeMs += Date.now() - this.lastActiveTimestamp;
        this.status = 'paused';
        this.stopTimer();

        try {
            await requestUrl({
                url: `${this.baseUrl}/api/v1/exam/${this.examId}/pause`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
        } catch (e) {
            console.warn('[Story 6.7] Failed to sync pause to backend:', e);
        }
    }

    async resumeExam(): Promise<void> {
        if (this.status !== 'paused') return;

        this.status = 'in_progress';
        this.lastActiveTimestamp = Date.now();
        this.startTimer();

        try {
            await requestUrl({
                url: `${this.baseUrl}/api/v1/exam/${this.examId}/resume`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
        } catch (e) {
            console.warn('[Story 6.7] Failed to sync resume to backend:', e);
        }
    }

    // ======================================================================
    // Story 6.8: Exam Completion
    // ======================================================================

    async completeExam(
        scoreHistory: any[],
        conversationLog: any[],
        masteryChanges: any[],
    ): Promise<{ saved: boolean; recordId: string }> {
        if (this.status === 'in_progress') {
            this.activeTimeMs += Date.now() - this.lastActiveTimestamp;
        }
        this.status = 'completed';
        this.stopTimer();
        this.cleanupVisibilityDetection();

        const payload = {
            exam_id: this.examId,
            source_canvas_id: this.sourceCanvasId,
            exam_mode: this.examMode,
            start_time: new Date(this.startTime).toISOString(),
            end_time: new Date().toISOString(),
            active_duration_seconds: Math.floor(this.activeTimeMs / 1000),
            score_history: scoreHistory,
            discovered_nodes: this.discoveredNodes.map(n => ({
                node_id: n.nodeId,
                source_node_id: n.sourceNodeId,
                depth: n.depth,
                timestamp: n.timestamp,
                source_exam_id: n.sourceExamId,
            })),
            skipped_nodes: this.skippedNodes.map(s => ({
                node_id: s.nodeId,
                question_id: s.questionId,
                timestamp: s.timestamp,
            })),
            conversation_log: conversationLog,
            mastery_changes: masteryChanges,
        };

        try {
            const response = await requestUrl({
                url: `${this.baseUrl}/api/v1/exam/${this.examId}/complete`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = JSON.parse(response.text);
            return { saved: data.saved, recordId: data.record_id || this.examId };
        } catch (e) {
            console.error('[Story 6.8] Failed to save exam record:', e);
            return { saved: false, recordId: '' };
        }
    }

    // ======================================================================
    // Cleanup
    // ======================================================================

    destroy(): void {
        this.stopTimer();
        this.cleanupVisibilityDetection();
    }
}
