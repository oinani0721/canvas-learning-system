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

export class CanvasLearningDB extends Dexie {
  canvas_boards!: Table<CanvasBoard, string>;
  canvas_nodes!: Table<CanvasNodeData, string>;
  canvas_edges!: Table<CanvasEdgeData, string>;
  sync_outbox!: Table<SyncOutboxEntry, number>;
  // Story 1.7: Dismissed recommendations
  dismissed_recommendations!: Table<DismissedRecommendation, number>;

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
  }
}

/** Singleton database instance. */
export const db = new CanvasLearningDB();
