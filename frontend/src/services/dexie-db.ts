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
  // Visual customization
  color?: string;            // user-assigned node color (red/orange/yellow/green/blue/purple/gray)
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

/**
 * SyncOutboxEntry — a pending sync operation awaiting the backend.
 *
 * FR-KG-04 Phase 12 Task 12.5: extended with 5 failure-tracking fields so
 * the sync-engine can route each failure into the right retry bucket
 * (permanent / priority / backoff). Optional fields stay backwards
 * compatible with entries written before the schema v6 upgrade — the
 * Dexie upgrade callback backfills defaults where needed.
 */
export interface SyncOutboxEntry {
  id?: number;
  entityType: 'node' | 'edge' | 'board';
  entityId: string;
  operation: 'create' | 'update' | 'delete';
  payload: Record<string, unknown>;
  createdAt: string;
  syncedAt?: string;
  /**
   * FR-KG-04 Phase 12: VALIDATION_ERROR path marks the entry permanently
   * failed so the sync-engine skips it on every future poll. This is how
   * we stop wasting round-trips on payloads that will never succeed
   * (missing fields, oversized content, unique-constraint violations).
   */
  permanentlyFailed?: boolean;
  /**
   * FR-KG-04 Phase 12: the SyncErrorClass the backend returned for the
   * most recent failure. Used to classify UI error messages and for
   * observability/metrics downstream.
   */
  failureClass?: 'VALIDATION_ERROR' | 'DEPENDENCY_MISSING' | 'TRANSIENT_ERROR';
  /**
   * FR-KG-04 Phase 12: DEPENDENCY_MISSING path bumps this to 1 so the
   * entry jumps the queue in the next poll — once its upstream node
   * syncs, the edge retry has the best chance of succeeding. Default 0.
   */
  retryPriority?: number;
  /**
   * FR-KG-04 Phase 12: TRANSIENT_ERROR path schedules the next retry via
   * exponential backoff. ISO-8601 timestamp; the sync-engine skips the
   * entry until current time crosses this value.
   */
  nextRetryAt?: string;
  /**
   * FR-KG-04 Phase 12: the last error message the backend returned,
   * truncated to ≤200 chars. Shown in the UI when the user opens a
   * failed outbox entry for diagnostics.
   */
  lastError?: string;
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

/** Chat message roles. GDR-P0-2: Added tool_use/tool_result for tool call visibility. */
export type ChatMessageRole = 'user' | 'assistant' | 'error' | 'tool_use' | 'tool_result' | 'system';

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
  // ── GDR-P0-2: Tool call fields ──
  /** Tool name (only for role=tool_use). */
  toolName?: string;
  /** Tool call state machine: pending → running → completed | error | blocked. */
  toolCallState?: 'pending' | 'running' | 'completed' | 'error' | 'blocked';
  /** Tool input parameters JSON string (only for role=tool_use). */
  toolInput?: string;
  /** Learning annotation — why this tool was called (Observer-generated). */
  learningAnnotation?: string;
}

/** Valid exam modes (6-1 M2: enum type guard). */
export type ExamModeLocal = 'point_to_point' | 'comprehensive' | 'mixed';
/** Valid exam statuses (6-1 M2: enum type guard). */
export type ExamStatusLocal = 'idle' | 'in_progress' | 'paused' | 'completed';

const VALID_EXAM_MODES: readonly string[] = ['point_to_point', 'comprehensive', 'mixed'];
const VALID_EXAM_STATUSES: readonly string[] = ['idle', 'in_progress', 'paused', 'completed'];

/** Type guard for ExamModeLocal. Returns 'mixed' for invalid values. */
export function toExamMode(value: string): ExamModeLocal {
  return VALID_EXAM_MODES.includes(value) ? (value as ExamModeLocal) : 'mixed';
}

/** Type guard for ExamStatusLocal. Returns 'idle' for invalid values. */
export function toExamStatus(value: string): ExamStatusLocal {
  return VALID_EXAM_STATUSES.includes(value) ? (value as ExamStatusLocal) : 'idle';
}

/**
 * Local exam session record for IndexedDB.
 * Story 6.1 AC-5: exam-state store backed by Dexie liveQuery.
 * 6-1 M2: examMode and status use typed string literals with type guards.
 */
export interface ExamSessionLocal {
  /** Exam session UUID (from backend). */
  id: string;
  /** Source canvas board ID. */
  sourceCanvasId: string;
  /** Exam mode: point_to_point | comprehensive | mixed. */
  examMode: ExamModeLocal;
  /** Session status: idle | in_progress | paused | completed. */
  status: ExamStatusLocal;
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

    // v6: FR-KG-04 Phase 12 Task 12.5-12.6 — sync_outbox gains failure
    // tracking fields (permanentlyFailed, failureClass, retryPriority,
    // nextRetryAt, lastError). Only permanentlyFailed and retryPriority
    // are indexed so the sync-engine's ordering query can use
    // `sync_outbox.where('permanentlyFailed').notEqual(true)` efficiently
    // and sort by retryPriority DESC without a table scan.
    this.version(6)
      .stores({
        canvas_boards: 'id, name, subjectId, createdAt, updatedAt',
        canvas_nodes:
          'id, canvasId, type, title, x, y, indexStatus, createdAt, updatedAt',
        canvas_edges:
          'id, canvasId, sourceNodeId, targetNodeId, createdAt, updatedAt',
        sync_outbox:
          '++id, entityType, entityId, operation, createdAt, syncedAt, permanentlyFailed, retryPriority, nextRetryAt',
        chat_messages: 'id, nodeId, role, createdAt',
        crash_recovery: 'id, nodeId',
        exam_sessions: 'id, sourceCanvasId, status, createdAt',
      })
      .upgrade(async (tx) => {
        // Backfill defaults on every pre-v6 sync_outbox entry so that
        // `where('permanentlyFailed').notEqual(true)` queries find them
        // (Dexie's indexing treats undefined as equal to neither true
        // nor false).
        await tx
          .table<SyncOutboxEntry>('sync_outbox')
          .toCollection()
          .modify((entry) => {
            if (entry.permanentlyFailed === undefined) {
              entry.permanentlyFailed = false;
            }
            if (entry.retryPriority === undefined) {
              entry.retryPriority = 0;
            }
            // failureClass / nextRetryAt / lastError stay undefined on
            // upgrade — they only appear on the next real failure.
          });
      });
  }
}

// Singleton instance
export const db = new CanvasLearningDB();
