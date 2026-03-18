/**
 * Canvas Learning System - Exam State Store
 * Story 6.1: Exam Board Generation (AC-5) — exam lifecycle state
 * Story 6.2: Exam Mode Selection (AC-5) — mode state
 * Story 6.4: AutoSCORE (AC-1, AC-4) — score tracking + node color updates
 *
 * Svelte 5 reactive store managing examination whiteboard state.
 * Authoritative data lives in the backend (Layer 0 principle).
 *
 * Data flow:
 *   Dashboard "Start Exam" -> createExam()
 *     -> POST /api/v1/exam/start
 *     -> examState.$state updates
 *     -> ExamCanvas renders
 *
 *   AutoSCORE completes -> score pushed via WebSocket
 *     -> examState.recordScore()
 *     -> masteryState.updateNodeMastery() -> node color changes
 */

import type { ApiClient } from '../services/api-client';

/** Exam mode options (Story 6.2 AC-1). */
export type ExamMode = 'point_to_point' | 'comprehensive' | 'mixed';

/** Exam lifecycle status (Story 6.1 AC-5). */
export type ExamStatusType = 'idle' | 'in_progress' | 'paused' | 'completed';

/** Content analysis result (Story 6.2 AC-2). */
export interface ContentAnalysis {
  contentType: 'knowledge' | 'problem' | 'mixed';
  recommendedMode: ExamMode;
  confidence: number;
  analysisDetail: string;
}

/** Score record for a node. */
export interface NodeScore {
  nodeId: string;
  grade: number;
  overallScore: number;
  confidence: string;
  scoredAt: string;
}

/**
 * Reactive exam state manager.
 * Uses Svelte 5 $state rune for fine-grained reactivity.
 */
class ExamState {
  /** Current exam session ID (null if not in exam). */
  currentExamId = $state<string | null>(null);

  /** Source canvas board ID. */
  sourceCanvasId = $state<string>('');

  /** Exam mode. */
  examMode = $state<ExamMode>('mixed');

  /** Exam lifecycle status. */
  examStatus = $state<ExamStatusType>('idle');

  /** Exam start time. */
  startTime = $state<string>('');

  /** Nodes that have been examined. */
  examinedNodes = $state<string[]>(new Array<string>());

  /** Nodes discovered during exam. */
  discoveredNodes = $state<string[]>(new Array<string>());

  /** Score history for this session. */
  scoreHistory = $state<NodeScore[]>(new Array<NodeScore>());

  /** Content analysis result. */
  contentAnalysis = $state<ContentAnalysis | null>(null);

  /** Loading state. */
  isLoading = $state<boolean>(false);

  /** Error message. */
  errorMessage = $state<string>('');

  /** Target node for single-node exam (Story 6.2 AC-6). */
  targetNodeId = $state<string | null>(null);

  /** API client reference. */
  private apiClient: ApiClient | null = null;

  /**
   * Initialize with API client.
   */
  setApiClient(client: ApiClient): void {
    this.apiClient = client;
  }

  /**
   * Create a new exam session.
   * Story 6.1 AC-1: POST /api/v1/exam/start.
   */
  async createExam(
    sourceCanvasId: string,
    mode: ExamMode = 'mixed',
    targetNodeId?: string,
  ): Promise<string | null> {
    if (!this.apiClient) {
      this.errorMessage = 'API client not initialized';
      return null;
    }

    this.isLoading = true;
    this.errorMessage = '';

    try {
      const response = await this.apiClient.post<{
        id: string;
        sourceCanvasId: string;
        examMode: ExamMode;
        status: ExamStatusType;
        startTime: string;
      }>('/api/v1/exam/start', {
        sourceCanvasId,
        examMode: mode,
        targetNodeId: targetNodeId || null,
      });

      this.currentExamId = response.id;
      this.sourceCanvasId = sourceCanvasId;
      this.examMode = mode;
      this.examStatus = 'in_progress';
      this.startTime = response.startTime || new Date().toISOString();
      this.examinedNodes = new Array<string>();
      this.discoveredNodes = new Array<string>();
      this.scoreHistory = new Array<NodeScore>();
      this.targetNodeId = targetNodeId || null;

      return response.id;
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      this.errorMessage = msg;
      return null;
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * Analyze canvas content for mode recommendation.
   * Story 6.2 AC-2: POST /api/v1/exam/analyze-canvas.
   */
  async analyzeCanvas(
    canvasId: string,
    targetNodeId?: string,
  ): Promise<ContentAnalysis | null> {
    if (!this.apiClient) return null;

    try {
      const result = await this.apiClient.post<ContentAnalysis>(
        '/api/v1/exam/analyze-canvas',
        {
          canvasId,
          targetNodeId: targetNodeId || null,
        },
      );
      this.contentAnalysis = result;
      return result;
    } catch (error) {
      return null;
    }
  }

  /**
   * Set exam mode after user selection.
   * Story 6.2 AC-5: Update mode in state and backend.
   */
  async setExamMode(mode: ExamMode): Promise<void> {
    this.examMode = mode;

    if (this.currentExamId && this.apiClient) {
      try {
        await this.apiClient.patch(
          `/api/v1/exam/${this.currentExamId}/status`,
          { status: 'in_progress', examMode: mode },
        );
      } catch (error) {
        // Non-fatal: local state is authoritative for mode
      }
    }
  }

  /**
   * Record a score result from AutoSCORE.
   * Story 6.4 AC-4: Score tracking for node color updates.
   */
  recordScore(score: NodeScore): void {
    const updated = [...this.scoreHistory, score];
    this.scoreHistory = updated;

    if (!this.examinedNodes.includes(score.nodeId)) {
      this.examinedNodes = [...this.examinedNodes, score.nodeId];
    }
  }

  /**
   * Exit exam and return to source canvas.
   */
  async exitExam(): Promise<void> {
    if (this.currentExamId && this.apiClient) {
      try {
        await this.apiClient.patch(
          `/api/v1/exam/${this.currentExamId}/status`,
          { status: 'completed' },
        );
      } catch (error) {
        // Non-fatal
      }
    }

    this.examStatus = 'completed';
  }

  /**
   * Reset state (when navigating away from exam).
   */
  reset(): void {
    this.currentExamId = null;
    this.sourceCanvasId = '';
    this.examMode = 'mixed';
    this.examStatus = 'idle';
    this.startTime = '';
    this.examinedNodes = new Array<string>();
    this.discoveredNodes = new Array<string>();
    this.scoreHistory = new Array<NodeScore>();
    this.contentAnalysis = null;
    this.errorMessage = '';
    this.targetNodeId = null;
  }

  /** Whether an exam is currently active. */
  get isActive(): boolean {
    return this.examStatus === 'in_progress';
  }

  /** Number of nodes examined so far. */
  get examinedCount(): number {
    return this.examinedNodes.length;
  }

  /** Elapsed time in minutes since exam started. */
  get elapsedMinutes(): number {
    if (!this.startTime) return 0;
    const start = new Date(this.startTime).getTime();
    const now = Date.now();
    return Math.floor((now - start) / 60000);
  }
}

/** Singleton exam state instance. */
export const examState = new ExamState();
