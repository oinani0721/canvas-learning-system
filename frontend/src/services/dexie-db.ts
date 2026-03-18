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

/**
 * Crash recovery entry — persists lastSentMessage across plugin restarts.
 * Story 3-11 AC-2: lastSentMessage cached in memory + Dexie.
 */
export interface CrashRecoveryEntry {
  /** Fixed key: 'last_sent' (only one active entry at a time). */
  id: string;
  /** Node ID the message was sent to. */
  nodeId: string;
  /** The user's message content. */
  message: string;
  /** CLI session ID (for --resume on restart). */
  sessionId: string | null;
  /** ISO-8601 timestamp of when the message was sent. */
  timestamp: string;
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

/**
 * Local exam session record for IndexedDB.
 * Story 6.1 AC-5: exam-state store backed by Dexie liveQuery.
 */
export interface ExamSessionLocal {
  /** Exam session UUID (from backend). */
  id: string;
  /** Source canvas board ID. */
  sourceCanvasId: string;
  /** Exam mode: point_to_point | comprehensive | mixed. */
  examMode: string;
  /** Session status: idle | in_progress | paused | completed. */
  status: string;
  /** ISO-8601 start time. */
  startTime: string;
  /** ISO-8601 end time (null if ongoing). */
  endTime?: string;
  /** List of examined node IDs. */
  examinedNodes: string[];
  /** List of discovered node IDs (recursive exam). */
  discoveredNodes: string[];
  /** Optional single-node target. */
  targetNodeId?: string;
  /** Currently active node being examined. */
  currentNodeId?: string;
  /** ISO-8601 creation timestamp. */
  createdAt: string;
}

// --- Database Class ---

class CanvasLearningDB extends Dexie {
  canvas_boards!: EntityTable<CanvasBoard, 'id'>;
  canvas_nodes!: EntityTable<CanvasNode, 'id'>;
  canvas_edges!: EntityTable<CanvasEdge, 'id'>;
  sync_outbox!: EntityTable<SyncOutboxEntry, 'id'>;
  chat_messages!: EntityTable<ChatMessage, 'id'>;
  crash_recovery!: EntityTable<CrashRecoveryEntry, 'id'>;
  exam_sessions!: EntityTable<ExamSessionLocal, 'id'>;

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

    // v4: crash_recovery table for Story 3-11 lastSentMessage persistence
    this.version(4).stores({
      canvas_boards: 'id, name, subjectId, createdAt, updatedAt',
      canvas_nodes: 'id, canvasId, type, title, x, y, indexStatus, createdAt, updatedAt',
      canvas_edges: 'id, canvasId, sourceNodeId, targetNodeId, createdAt, updatedAt',
      sync_outbox: '++id, entityType, entityId, operation, createdAt, syncedAt',
      chat_messages: 'id, nodeId, role, createdAt',
      crash_recovery: 'id, nodeId',
    });

    // v5: exam_sessions table for Story 6.1 AC-5 (exam-state store)
    this.version(5).stores({
      canvas_boards: 'id, name, subjectId, createdAt, updatedAt',
      canvas_nodes: 'id, canvasId, type, title, x, y, indexStatus, createdAt, updatedAt',
      canvas_edges: 'id, canvasId, sourceNodeId, targetNodeId, createdAt, updatedAt',
      sync_outbox: '++id, entityType, entityId, operation, createdAt, syncedAt',
      chat_messages: 'id, nodeId, role, createdAt',
      crash_recovery: 'id, nodeId',
      exam_sessions: 'id, sourceCanvasId, status, createdAt',
    });
  }
}

// Singleton instance
export const db = new CanvasLearningDB();
