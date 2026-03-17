/**
 * Canvas Learning System - Canvas Type Definitions
 * Story 1.4: Whiteboard CRUD + Mini Dashboard (AC-6)
 *
 * IndexedDB schema types for Dexie.js.
 * Table names: snake_case plural. Field names: camelCase.
 */

/** A whiteboard container that holds nodes and edges. */
export interface CanvasBoard {
  id: string;
  name: string;
  subjectId?: string;
  createdAt: string;
  updatedAt: string;
}

/** A visual node on the canvas (text or image). */
export interface CanvasNodeData {
  id: string;
  canvasId: string;
  type: 'text' | 'image';
  title: string;
  content: string;
  x: number;
  y: number;
  width: number;
  height: number;
  createdAt: string;
  updatedAt: string;
  // Story 1.6: Image node fields
  imageData?: string;           // base64 DataURL (image type only)
  indexStatus?: 'none' | 'indexing' | 'indexed' | 'failed';
  ocrText?: string;             // OCR extracted original text
  ocrSummary?: string;          // OCR extracted summary
  ocrConcepts?: string[];       // OCR extracted concept list
  ocrError?: string;            // OCR failure error message
}

/** A directed edge connecting two nodes. */
export interface CanvasEdgeData {
  id: string;
  canvasId: string;
  sourceNodeId: string;
  targetNodeId: string;
  label: string;
  createdAt: string;
  updatedAt: string;
}

/** Outbox entry for delta sync (Story 1.5 will consume). */
export interface SyncOutboxEntry {
  id?: number;
  entityType: 'node' | 'edge' | 'board';
  entityId: string;
  operation: 'create' | 'update' | 'delete';
  payload: Record<string, unknown>;
  createdAt: string;
  syncedAt?: string;
}

/** Viewport state for canvas pan/zoom. */
export interface Viewport {
  x: number;
  y: number;
  zoom: number;
}

/** Rectangle bounds used for culling calculations. */
export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

/** Point in 2D space. */
export interface Point {
  x: number;
  y: number;
}

/** View routing state for App.svelte. */
export type ViewRoute = 'dashboard' | 'canvas';

// ═══════════════════════════════════════════════════════════════════════════
// Story 1.7: Recommendation types
// ═══════════════════════════════════════════════════════════════════════════

/** A single concept-relation recommendation from the backend. */
export interface Recommendation {
  id: string;
  sourceNodeId: string;
  sourceNodeTitle: string;
  targetNodeId: string;
  targetNodeTitle: string;
  confidence: number;
  reason: string;
  suggestedLabel: string;
}

/** Backend response for recommendations API. */
export interface RecommendationResponse {
  recommendations: Recommendation[];
  canvasId: string;
  analyzedAt: string;
}

/** A dismissed recommendation pair stored in IndexedDB. */
export interface DismissedRecommendation {
  id?: number;
  pairKey: string;         // sorted nodeId pair: `${idA}_${idB}`
  dismissedAt: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Story 1.9: Subject types
// ═══════════════════════════════════════════════════════════════════════════

/** A subject (course/discipline) for KG isolation. */
export interface Subject {
  id: string;
  name: string;
  createdAt: string;
  isDefault: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════
// Story 5.3: Profile types
// ═══════════════════════════════════════════════════════════════════════════

/** Profile summary for the learning profile header. */
export interface ProfileSummary {
  conceptId: string;
  name: string;
  masteryLevel: number;
  masteryLabel: string;
  masteryColor: string;
  effectiveProficiency: number;
  prescriptiveMessage: string;
  interactionCount: number;
  examCount: number;
  lastExamDate: string | null;
  fsrsDueDate: string | null;
  freshness: string;
}

/** A single tip annotation. */
export interface TipItem {
  tipId: string;
  content: string;
  category: string;
  annotatedAt: string;
  contextMessages: string[];
}

/** A weakness direction (positive framing). */
export interface WeaknessItem {
  direction: string;
  frequency: number;
  lastSeen: string | null;
  relatedExamSummaries: string[];
}

/** A single Q&A highlight pair. */
export interface QAHighlight {
  question: string;
  answer: string;
  extractedAt: string;
}

/** Q&A pairs grouped by topic. */
export interface QAHighlightCluster {
  topic: string;
  qaPairs: QAHighlight[];
}

// ═══════════════════════════════════════════════════════════════════════════
// Story 5.4: Dashboard types
// ═══════════════════════════════════════════════════════════════════════════

/** An exam session record from the backend. */
export interface ExamSession {
  id: string;
  sourceBoardId: string;
  sourceBoardName: string;
  mode: 'point-to-point' | 'comprehensive' | 'mixed';
  status: 'in-progress' | 'completed';
  nodesExamined: number;
  masteryChangeSummary: string;
  createdAt: string;
  completedAt?: string;
}

/** A node that needs FSRS review, displayed in Dashboard review tab. */
export interface ReviewNode {
  conceptId: string;
  name: string;
  boardId: string;
  boardName: string;
  masteryLevel: number;
  masteryColor: string;
  effectiveProficiency: number;
  freshness: 'fresh' | 'due' | 'overdue' | 'stale';
  lastReviewedAt?: string;
  dueDate?: string;
  overdueDays?: number;
}

/** Response from /mastery/batch endpoint. */
export interface MasteryBatchResponse {
  concepts: MasteryConceptResponse[];
  topicSummary: Record<string, { avgProficiency: number; conceptCount: number; examWeight: number }>;
}

/** A single concept in the mastery batch response. */
export interface MasteryConceptResponse {
  conceptId: string;
  name: string;
  topic: string;
  effectiveProficiency: number;
  masteryLevel: number;
  masteryLabel: string;
  masteryColor: string;
  retrievability: number;
  freshness: string;
  fsrsDueDate: string | null;
  overrideActive: boolean;
  overrideValue: number | null;
  selfAssessValue: number | null;
  falseMasteryRisk: number;
  interactionCount: number;
  fluentCount: number;
  pMastery: number;
  lastInteractionTs: string | null;
}
