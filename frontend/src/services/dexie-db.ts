/**
 * IndexedDB Schema via Dexie.js — Canvas Learning System
 * Story 1-4 AC-6: Local-first persistence with Dexie liveQuery
 * Story 1-6: Added image/OCR fields (Schema v2)
 *
 * Schema v2: canvas_boards, canvas_nodes (+ image/OCR), canvas_edges, sync_outbox
 * Only stores/ directory should import db (architecture boundary)
 */
import Dexie, { type EntityTable } from 'dexie';

// --- Entity Interfaces ---

export interface CanvasBoard {
  id: string;
  name: string;
  subjectId?: string;
  createdAt: string;
  updatedAt: string;
}

export type IndexStatus = 'none' | 'indexing' | 'indexed' | 'failed';

export interface CanvasNode {
  id: string;
  canvasId: string;
  type: 'text' | 'image';
  title: string;
  content: string;
  x: number;
  y: number;
  width: number;
  height: number;
  masteryStatus?: string;
  effectiveProficiency?: number;
  hasExamRecord?: boolean;
  // Image fields (Story 1-6)
  imageData?: string;        // base64 DataURL for image nodes
  indexStatus?: IndexStatus; // OCR processing state
  ocrText?: string;          // extracted text
  ocrSummary?: string;       // one-line summary
  ocrConcepts?: string[];    // extracted concept terms
  ocrError?: string;         // error message on failure
  createdAt: string;
  updatedAt: string;
}

export interface CanvasEdge {
  id: string;
  canvasId: string;
  sourceNodeId: string;
  targetNodeId: string;
  label: string;
  createdAt: string;
  updatedAt: string;
}

export interface SyncOutboxEntry {
  id?: number;
  entityType: 'node' | 'edge' | 'board';
  entityId: string;
  operation: 'create' | 'update' | 'delete';
  payload: Record<string, unknown>;
  createdAt: string;
  syncedAt?: string;
}

/** Chat message roles. */
export type ChatMessageRole = 'user' | 'assistant' | 'error';

/**
 * Persisted chat message entity.
 * Story 3-3 AC-4: Chat history persisted in IndexedDB via Dexie.
 */
export interface ChatMessage {
  /** Unique message ID. */
  id: string;
  /** The node this message belongs to. */
  nodeId: string;
  /** Message role: user, assistant, or error. */
  role: ChatMessageRole;
  /** Message text content (markdown for assistant). */
  content: string;
  /** ISO-8601 creation timestamp. */
  createdAt: string;
  /** Optional metadata (tool usage, cost, session ID, etc.). */
  metadata?: string;
}

// --- Database Class ---

class CanvasLearningDB extends Dexie {
  canvas_boards!: EntityTable<CanvasBoard, 'id'>;
  canvas_nodes!: EntityTable<CanvasNode, 'id'>;
  canvas_edges!: EntityTable<CanvasEdge, 'id'>;
  sync_outbox!: EntityTable<SyncOutboxEntry, 'id'>;
  chat_messages!: EntityTable<ChatMessage, 'id'>;

  constructor() {
    super('CanvasLearningDB');

    this.version(1).stores({
      canvas_boards: 'id, name, subjectId, createdAt, updatedAt',
      canvas_nodes: 'id, canvasId, type, title, x, y, createdAt, updatedAt',
      canvas_edges: 'id, canvasId, sourceNodeId, targetNodeId, createdAt, updatedAt',
      sync_outbox: '++id, entityType, entityId, operation, createdAt, syncedAt',
    });

    // v2: image/OCR fields added to canvas_nodes (no index changes needed,
    // new fields are non-indexed properties stored in the same object store)
    this.version(2).stores({
      canvas_boards: 'id, name, subjectId, createdAt, updatedAt',
      canvas_nodes: 'id, canvasId, type, title, x, y, indexStatus, createdAt, updatedAt',
      canvas_edges: 'id, canvasId, sourceNodeId, targetNodeId, createdAt, updatedAt',
      sync_outbox: '++id, entityType, entityId, operation, createdAt, syncedAt',
    });

    // v3: chat_messages table for persistent conversation history (Story 3-3 AC-4)
    this.version(3).stores({
      canvas_boards: 'id, name, subjectId, createdAt, updatedAt',
      canvas_nodes: 'id, canvasId, type, title, x, y, indexStatus, createdAt, updatedAt',
      canvas_edges: 'id, canvasId, sourceNodeId, targetNodeId, createdAt, updatedAt',
      sync_outbox: '++id, entityType, entityId, operation, createdAt, syncedAt',
      chat_messages: 'id, nodeId, role, createdAt',
    });
  }
}

// Singleton instance
export const db = new CanvasLearningDB();
