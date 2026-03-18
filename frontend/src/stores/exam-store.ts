/**
 * Exam State Store (Story 6.1 AC-5, Story 6.2 AC-5)
 *
 * Manages examination whiteboard lifecycle state with Dexie persistence.
 *
 * State:
 *   currentExamId, sourceCanvasId, examMode, examStatus,
 *   startTime, examinedNodes, discoveredNodes
 *
 * Actions:
 *   createExam, enterExam, exitExam, setExamMode, updateStatus,
 *   recordNodeExamined, recordNodeDiscovered
 */

import { create } from 'zustand';
import { db, type ExamSessionLocal } from '../services/dexie-db';
import { ApiClient } from '../services/api-client';

export type ExamMode = 'point_to_point' | 'comprehensive' | 'mixed';
export type ExamStatus = 'idle' | 'in_progress' | 'paused' | 'completed';

interface ExamState {
  /** Current active exam session ID (null when not in exam). */
  currentExamId: string | null;
  /** Source canvas board ID for this exam. */
  sourceCanvasId: string | null;
  /** Selected exam mode. */
  examMode: ExamMode;
  /** Current exam status. */
  examStatus: ExamStatus;
  /** ISO-8601 start time. */
  startTime: string | null;
  /** List of examined node IDs. */
  examinedNodes: string[];
  /** List of discovered node IDs. */
  discoveredNodes: string[];
  /** Currently active node being examined. */
  currentNodeId: string | null;
  /** Whether an exam is actively running. */
  isExamActive: boolean;

  // Actions
  createExam: (
    sourceCanvasId: string,
    mode?: ExamMode,
    targetNodeId?: string,
  ) => Promise<string | null>;
  enterExam: (examId: string) => Promise<void>;
  exitExam: () => void;
  setExamMode: (mode: ExamMode) => void;
  updateStatus: (status: ExamStatus) => void;
  recordNodeExamined: (nodeId: string) => void;
  recordNodeDiscovered: (nodeId: string) => void;
  setCurrentNode: (nodeId: string | null) => void;
}

const apiClient = new ApiClient();

export const useExamStore = create<ExamState>((set, get) => ({
  currentExamId: null,
  sourceCanvasId: null,
  examMode: 'mixed',
  examStatus: 'idle',
  startTime: null,
  examinedNodes: [],
  discoveredNodes: [],
  currentNodeId: null,
  isExamActive: false,

  createExam: async (
    sourceCanvasId: string,
    mode: ExamMode = 'mixed',
    targetNodeId?: string,
  ): Promise<string | null> => {
    try {
      const session = await apiClient.startExam(sourceCanvasId, mode, targetNodeId);
      if (!session) {
        console.error('[Story 6.1] Exam creation failed: null response from apiClient');
        return null;
      }
      const examId = session.id as string;
      const nowIso = new Date().toISOString();

      // Persist to IndexedDB
      const localSession: ExamSessionLocal = {
        id: examId,
        sourceCanvasId,
        examMode: mode,
        status: 'in_progress',
        startTime: nowIso,
        examinedNodes: [],
        discoveredNodes: [],
        targetNodeId,
        createdAt: nowIso,
      };
      await db.exam_sessions.put(localSession);

      set({
        currentExamId: examId,
        sourceCanvasId,
        examMode: mode,
        examStatus: 'in_progress',
        startTime: nowIso,
        examinedNodes: [],
        discoveredNodes: [],
        isExamActive: true,
      });

      return examId;
    } catch (err) {
      console.error('[Story 6.1] createExam error:', err);
      return null;
    }
  },

  enterExam: async (examId: string): Promise<void> => {
    // Load from IndexedDB first
    const local = await db.exam_sessions.get(examId);
    if (local) {
      set({
        currentExamId: local.id,
        sourceCanvasId: local.sourceCanvasId,
        examMode: local.examMode as ExamMode,
        examStatus: local.status as ExamStatus,
        startTime: local.startTime,
        examinedNodes: local.examinedNodes,
        discoveredNodes: local.discoveredNodes,
        currentNodeId: local.currentNodeId || null,
        isExamActive: local.status === 'in_progress',
      });
    }
  },

  exitExam: () => {
    set({
      currentExamId: null,
      sourceCanvasId: null,
      examMode: 'mixed',
      examStatus: 'idle',
      startTime: null,
      examinedNodes: [],
      discoveredNodes: [],
      currentNodeId: null,
      isExamActive: false,
    });
  },

  setExamMode: (mode: ExamMode) => {
    const { currentExamId } = get();
    set({ examMode: mode });

    // Sync to backend via ApiClient (respects configured backendUrl)
    if (currentExamId) {
      apiClient.patch(`/api/v1/exam/${currentExamId}/status`, {
        status: 'in_progress',
        examMode: mode,
      }).catch((err) => console.warn('[Story 6.2] Mode sync failed:', err));

      // Update IndexedDB
      db.exam_sessions.update(currentExamId, { examMode: mode }).catch(() => {});
    }
  },

  updateStatus: (status: ExamStatus) => {
    const { currentExamId } = get();
    set({
      examStatus: status,
      isExamActive: status === 'in_progress',
    });

    if (currentExamId) {
      db.exam_sessions.update(currentExamId, { status }).catch(() => {});
    }
  },

  recordNodeExamined: (nodeId: string) => {
    const { examinedNodes, currentExamId } = get();
    if (!examinedNodes.includes(nodeId)) {
      const updated = [...examinedNodes, nodeId];
      set({ examinedNodes: updated, currentNodeId: nodeId });

      if (currentExamId) {
        db.exam_sessions
          .update(currentExamId, {
            examinedNodes: updated,
            currentNodeId: nodeId,
          })
          .catch(() => {});
      }
    }
  },

  recordNodeDiscovered: (nodeId: string) => {
    const { discoveredNodes, currentExamId } = get();
    if (!discoveredNodes.includes(nodeId)) {
      const updated = [...discoveredNodes, nodeId];
      set({ discoveredNodes: updated });

      if (currentExamId) {
        db.exam_sessions
          .update(currentExamId, { discoveredNodes: updated })
          .catch(() => {});
      }
    }
  },

  setCurrentNode: (nodeId: string | null) => {
    const { currentExamId } = get();
    set({ currentNodeId: nodeId });

    if (currentExamId && nodeId) {
      db.exam_sessions
        .update(currentExamId, { currentNodeId: nodeId })
        .catch(() => {});
    }
  },
}));
