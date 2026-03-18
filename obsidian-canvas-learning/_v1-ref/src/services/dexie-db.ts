/**
 * Canvas Learning System - IndexedDB via Dexie.js
 * Story 1.4: Schema v1 — canvas_boards, canvas_nodes, canvas_edges, sync_outbox (AC-6)
 *
 * Architecture boundary: only files in stores/ may import this module.
 * Components must go through the canvas-state store.
 */

import Dexie, { type Table } from 'dexie';
import type {
  CanvasBoard,
  CanvasEdgeData,
  CanvasNodeData,
  DismissedRecommendation,
  SyncOutboxEntry,
} from '../types/canvas';

/**
 * Story 4.1 AC-2: Edge dialog guide state.
 * Tracks whether the user has seen the first-time edge dialog tooltip.
 */
export interface EdgeDialogSettings {
  id?: number;
  /** Whether the edge dialog guide tooltip has been shown and dismissed. */
  guideShown: boolean;
}

/**
 * Story 4.4 AC-4: Pending edge rationale for Outbox retry.
 * When dual-write fails, rationale data is stored here for later sync.
 */
export interface PendingEdgeRationale {
  id?: number;
  edgeId: string;
  rationaleData: Record<string, unknown>;
  createdAt: string;
  retryCount: number;
}

/**
 * Story 6.1 AC-5: Exam session record in IndexedDB.
 * Dual-written with backend SQLite/Neo4j via Outbox delta sync.
 */
export interface ExamSessionRecord {
  id: string;
  sourceCanvasId: string;
  examMode: 'point_to_point' | 'comprehensive' | 'mixed';
  status: 'idle' | 'in_progress' | 'paused' | 'completed';
  startTime: string;
  endTime?: string;
  examinedNodes: string;     // JSON-serialized string[]
  discoveredNodes: string;   // JSON-serialized string[]
  targetNodeId?: string;
  currentNodeId?: string;
  createdAt: string;
  updatedAt: string;
}

export class CanvasLearningDB extends Dexie {
  canvas_boards!: Table<CanvasBoard, string>;
  canvas_nodes!: Table<CanvasNodeData, string>;
  canvas_edges!: Table<CanvasEdgeData, string>;
  sync_outbox!: Table<SyncOutboxEntry, number>;
  // Story 1.7: Dismissed recommendations
  dismissed_recommendations!: Table<DismissedRecommendation, number>;
  // Story 4.1: Edge dialog settings
  edge_dialog_settings!: Table<EdgeDialogSettings, number>;
  // Story 4.4: Pending edge rationales for Outbox retry
  pending_edge_rationales!: Table<PendingEdgeRationale, number>;
  // Story 6.1: Exam sessions
  exam_sessions!: Table<ExamSessionRecord, string>;

  constructor() {
    super('CanvasLearningDB');

    this.version(1).stores({
      canvas_boards: 'id, name, subjectId, createdAt, updatedAt',
      canvas_nodes: 'id, canvasId, type, title, x, y, createdAt, updatedAt',
      canvas_edges: 'id, canvasId, sourceNodeId, targetNodeId, createdAt, updatedAt',
      sync_outbox: '++id, entityType, entityId, operation, createdAt, syncedAt',
    });

    // Story 1.6 + 1.7: Schema v2 — image node fields + dismissed recommendations
    this.version(2).stores({
      canvas_boards: 'id, name, subjectId, createdAt, updatedAt',
      canvas_nodes: 'id, canvasId, type, title, x, y, createdAt, updatedAt, indexStatus',
      canvas_edges: 'id, canvasId, sourceNodeId, targetNodeId, createdAt, updatedAt',
      sync_outbox: '++id, entityType, entityId, operation, createdAt, syncedAt',
      dismissed_recommendations: '++id, pairKey, dismissedAt',
    }).upgrade(tx => {
      return tx.table('canvas_nodes').toCollection().modify(node => {
        if (node.type === 'image' && !node.indexStatus) {
          node.indexStatus = 'none';
        }
      });
    });

    // Story 4.1 + 4.4: Schema v3 — edge dialog settings + pending rationales
    this.version(3).stores({
      canvas_boards: 'id, name, subjectId, createdAt, updatedAt',
      canvas_nodes: 'id, canvasId, type, title, x, y, createdAt, updatedAt, indexStatus',
      canvas_edges: 'id, canvasId, sourceNodeId, targetNodeId, createdAt, updatedAt',
      sync_outbox: '++id, entityType, entityId, operation, createdAt, syncedAt',
      dismissed_recommendations: '++id, pairKey, dismissedAt',
      edge_dialog_settings: '++id, guideShown',
      pending_edge_rationales: '++id, edgeId, createdAt, retryCount',
    });

    // Story 6.1: Schema v4 — exam_sessions table
    this.version(4).stores({
      canvas_boards: 'id, name, subjectId, createdAt, updatedAt',
      canvas_nodes: 'id, canvasId, type, title, x, y, createdAt, updatedAt, indexStatus',
      canvas_edges: 'id, canvasId, sourceNodeId, targetNodeId, createdAt, updatedAt',
      sync_outbox: '++id, entityType, entityId, operation, createdAt, syncedAt',
      dismissed_recommendations: '++id, pairKey, dismissedAt',
      edge_dialog_settings: '++id, guideShown',
      pending_edge_rationales: '++id, edgeId, createdAt, retryCount',
      exam_sessions: 'id, sourceCanvasId, examMode, status, startTime, createdAt',
    });
  }
}

/** Singleton database instance. */
export const db = new CanvasLearningDB();
