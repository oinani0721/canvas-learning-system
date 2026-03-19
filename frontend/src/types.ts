/**
 * Canvas Learning System - Type Definitions
 *
 * Adapted from v1-ref canvas.d.ts for ReactFlow-based canvas rendering.
 * ReactFlow structural types are mirrored locally so this file compiles
 * without an @xyflow/react npm dependency (types-only usage).
 *
 * Key design:
 *   - KnowledgeNodeData  = custom `data` payload for ReactFlow Node<TData>
 *   - KnowledgeEdgeData  = custom `data` payload for ReactFlow Edge<TData>
 *   - KnowledgeNode      = Node<KnowledgeNodeData, 'knowledge' | 'image'>
 *   - KnowledgeEdge      = Edge<KnowledgeEdgeData, 'knowledge'>
 *   - WhiteboardFile     = JSON schema for local .json file persistence
 */

// ═══════════════════════════════════════════════════════════════════════════
// ReactFlow structural types (mirrored from @xyflow/react v12)
// These let us define typed nodes/edges without a runtime dependency.
// When @xyflow/react is installed, replace these with direct imports:
//   import type { Node, Edge, Viewport, XYPosition } from '@xyflow/react';
// ═══════════════════════════════════════════════════════════════════════════

/** 2D position used by ReactFlow for node placement. */
export interface XYPosition {
	x: number;
	y: number;
}

/** Viewport state: pan offset + zoom level. */
export interface Viewport {
	x: number;
	y: number;
	zoom: number;
}

/**
 * ReactFlow Node base type (mirrors @xyflow/react Node<TData, TType>).
 * TData = custom data payload, TType = string literal node type.
 */
export interface Node<
	TData extends Record<string, unknown> = Record<string, unknown>,
	TType extends string = string,
> {
	id: string;
	type?: TType;
	position: XYPosition;
	data: TData;
	width?: number;
	height?: number;
	selected?: boolean;
	dragging?: boolean;
	hidden?: boolean;
	measured?: { width?: number; height?: number };
	parentId?: string;
	expandParent?: boolean;
	dragHandle?: string;
	zIndex?: number;
	style?: Record<string, string>;
	className?: string;
}

/**
 * ReactFlow Edge base type (mirrors @xyflow/react Edge<TData, TType>).
 * TData = custom data payload, TType = string literal edge type.
 */
export interface Edge<
	TData extends Record<string, unknown> = Record<string, unknown>,
	TType extends string = string,
> {
	id: string;
	type?: TType;
	source: string;
	target: string;
	sourceHandle?: string | null;
	targetHandle?: string | null;
	data?: TData;
	label?: string;
	selected?: boolean;
	hidden?: boolean;
	animated?: boolean;
	zIndex?: number;
	style?: Record<string, string>;
	className?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Mastery & FSRS types
// ═══════════════════════════════════════════════════════════════════════════

/** The five mastery visual states driving node color. */
export type MasteryStatus =
	| 'unlearned'
	| 'learning'
	| 'weak'
	| 'mastered'
	| 'review';

/**
 * FSRS scheduling parameters stored per-node.
 * Mirrors the backend FSRS card fields needed for display and review logic.
 */
export interface FSRSParams {
	/** Stability: expected number of days until retention drops below threshold. */
	stability: number;
	/** Difficulty: [1, 10] range. Higher = harder to recall. */
	difficulty: number;
	/** Current retrievability: probability of recall [0, 1]. */
	retrievability: number;
	/** ISO-8601 timestamp of last review. */
	lastReviewedAt: string | null;
	/** ISO-8601 timestamp of next scheduled review. */
	nextReviewAt: string | null;
	/** Number of FSRS repetitions completed. */
	repetitions: number;
	/** Elapsed days since last review. */
	elapsedDays: number;
	/** Scheduled interval in days. */
	scheduledDays: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// OCR / Image types
// ═══════════════════════════════════════════════════════════════════════════

/** Index status for image nodes after OCR processing. */
export type IndexStatus = 'none' | 'indexing' | 'indexed' | 'failed';

/** OCR extraction results attached to image-type nodes. */
export interface OCRData {
	/** OCR extracted original text. */
	text: string;
	/** OCR extracted summary. */
	summary: string;
	/** OCR extracted concept list. */
	concepts: string[];
	/** OCR failure error message, if any. */
	error?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Tip types
// ═══════════════════════════════════════════════════════════════════════════

/** A single tip annotation associated with a node. */
export interface TipItem {
	tipId: string;
	content: string;
	category: string;
	annotatedAt: string;
	contextMessages: string[];
}

// ═══════════════════════════════════════════════════════════════════════════
// KnowledgeNodeData — ReactFlow custom node data payload
// ═══════════════════════════════════════════════════════════════════════════

/** Node content type discriminator. */
export type KnowledgeNodeType = 'text' | 'image';

/**
 * Custom data payload for ReactFlow knowledge nodes.
 * Passed as `Node<KnowledgeNodeData>.data`.
 *
 * Carries all business fields: content, mastery state, FSRS scheduling,
 * OCR results, and tips. ReactFlow handles position/dimensions separately
 * through its own Node fields (position, width, height).
 */
export interface KnowledgeNodeData extends Record<string, unknown> {
	// ── Identity & content ─────────────────────────────────────────────
	/** Board this node belongs to. */
	canvasId: string;
	/** Content type: 'text' for concept cards, 'image' for visual material. */
	nodeType: KnowledgeNodeType;
	/** Display title shown in the node header. */
	title: string;
	/** Main text content (markdown). */
	content: string;

	// ── Timestamps ─────────────────────────────────────────────────────
	createdAt: string;
	updatedAt: string;

	// ── Mastery state (from backend, cached locally) ───────────────────
	/** Combined proficiency = min(p_mastery, R). null when never examined. */
	effectiveProficiency: number | null;
	/** Whether the user has interacted (opened a conversation). */
	hasInteraction: boolean;
	/** Whether the node has been examined (AutoSCORE graded). */
	hasExamRecord: boolean;
	/** Computed mastery status driving CSS color class. */
	masteryStatus: MasteryStatus;
	/** Backend mastery level [0..5]. null if unassessed. */
	masteryLevel: number | null;
	/** Human-readable mastery label from backend (e.g. "Novice", "Expert"). */
	masteryLabel: string | null;

	// ── FSRS scheduling ────────────────────────────────────────────────
	/** FSRS card parameters. null if no FSRS card exists for this node. */
	fsrs: FSRSParams | null;

	// ── Image / OCR fields ─────────────────────────────────────────────
	/** Base64 DataURL for image-type nodes. */
	imageData?: string;
	/** OCR processing status. */
	indexStatus: IndexStatus;
	/** OCR extraction results. */
	ocr?: OCRData;

	// ── Visual customization ──────────────────────────────────────────
	/** User-assigned node color (from context menu color picker). */
	color?: string;

	// ── Tips ───────────────────────────────────────────────────────────
	/** Tip annotations attached to this node. */
	tips: TipItem[];

	// ── Interaction counts ─────────────────────────────────────────────
	/** Number of chat interactions with this node. */
	interactionCount: number;
	/** Number of exam sessions involving this node. */
	examCount: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// KnowledgeEdgeData — ReactFlow custom edge data payload
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Custom data payload for ReactFlow knowledge edges.
 * Passed as `Edge<KnowledgeEdgeData>.data`.
 *
 * ReactFlow handles source/target/label through its own Edge fields.
 * This payload carries additional business metadata.
 */
export interface KnowledgeEdgeData extends Record<string, unknown> {
	/** Board this edge belongs to. */
	canvasId: string;
	/** Relationship label (e.g. "prerequisite", "extends"). */
	relationLabel: string;
	/** Confidence score from recommendation engine [0, 1]. null if user-created. */
	confidence: number | null;
	/** Whether this edge was auto-suggested by the recommendation engine. */
	isRecommended: boolean;

	// ── Timestamps ─────────────────────────────────────────────────────
	createdAt: string;
	updatedAt: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Concrete ReactFlow node/edge types
// ═══════════════════════════════════════════════════════════════════════════

/** Text concept node. */
export type TextKnowledgeNode = Node<KnowledgeNodeData, 'knowledge'>;
/** Image/visual material node. */
export type ImageKnowledgeNode = Node<KnowledgeNodeData, 'image'>;
/** Union of all custom node types used in the canvas. */
export type AppNode = TextKnowledgeNode | ImageKnowledgeNode;

/** Knowledge relationship edge. */
export type KnowledgeRelationEdge = Edge<KnowledgeEdgeData, 'knowledge'>;
/** Union of all custom edge types used in the canvas. */
export type AppEdge = KnowledgeRelationEdge;

// ═══════════════════════════════════════════════════════════════════════════
// WhiteboardFile — local JSON persistence format
// ═══════════════════════════════════════════════════════════════════════════

/**
 * JSON schema for a whiteboard file stored on disk.
 * Structure mirrors ReactFlow's `toObject()` output with additional metadata.
 *
 * ReactFlow `toObject()` returns `{ nodes, edges, viewport }`.
 * We wrap that with board-level metadata for persistence.
 *
 * File naming: `<boardId>.canvas.json`
 */
export interface WhiteboardFile {
	/** Schema version for forward-compatible migrations. */
	version: number;
	/** Unique board identifier. */
	boardId: string;
	/** Human-readable board name. */
	boardName: string;
	/** Subject/course this board belongs to. */
	subjectId: string | null;
	/** ISO-8601 creation timestamp. */
	createdAt: string;
	/** ISO-8601 last-modified timestamp. */
	updatedAt: string;

	/** ReactFlow nodes with full business data. */
	nodes: AppNode[];
	/** ReactFlow edges with full business data. */
	edges: AppEdge[];
	/** Viewport state (pan + zoom) at time of save. */
	viewport: Viewport;
}

/** Current schema version for WhiteboardFile. */
export const WHITEBOARD_SCHEMA_VERSION = 1;

// ═══════════════════════════════════════════════════════════════════════════
// Conversion helpers (v1-ref CanvasNodeData <-> KnowledgeNodeData)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Shape of the legacy v1-ref CanvasNodeData, used for migration.
 * Retained here so conversion functions can reference both formats.
 */
export interface LegacyCanvasNodeData {
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
	imageData?: string;
	indexStatus?: 'none' | 'indexing' | 'indexed' | 'failed';
	ocrText?: string;
	ocrSummary?: string;
	ocrConcepts?: string[];
	ocrError?: string;
}

/**
 * Shape of the legacy v1-ref CanvasEdgeData, used for migration.
 */
export interface LegacyCanvasEdgeData {
	id: string;
	canvasId: string;
	sourceNodeId: string;
	targetNodeId: string;
	label: string;
	createdAt: string;
	updatedAt: string;
}

/**
 * Convert a legacy v1-ref node to a ReactFlow AppNode.
 * Sets mastery fields to unlearned defaults.
 */
export function legacyNodeToAppNode(legacy: LegacyCanvasNodeData): AppNode {
	const isImage = legacy.type === 'image';

	const data: KnowledgeNodeData = {
		canvasId: legacy.canvasId,
		nodeType: legacy.type,
		title: legacy.title,
		content: legacy.content,
		createdAt: legacy.createdAt,
		updatedAt: legacy.updatedAt,

		// Mastery defaults (unlearned)
		effectiveProficiency: null,
		hasInteraction: false,
		hasExamRecord: false,
		masteryStatus: 'unlearned',
		masteryLevel: null,
		masteryLabel: null,

		// No FSRS card
		fsrs: null,

		// Image / OCR
		imageData: legacy.imageData,
		indexStatus: legacy.indexStatus ?? 'none',
		ocr:
			legacy.ocrText != null
				? {
						text: legacy.ocrText ?? '',
						summary: legacy.ocrSummary ?? '',
						concepts: legacy.ocrConcepts ?? [],
						error: legacy.ocrError,
					}
				: undefined,

		// No tips or interaction history
		tips: [],
		interactionCount: 0,
		examCount: 0,
	};

	return {
		id: legacy.id,
		type: isImage ? 'image' : 'knowledge',
		position: { x: legacy.x, y: legacy.y },
		data,
		width: legacy.width,
		height: legacy.height,
	};
}

/**
 * Convert a legacy v1-ref edge to a ReactFlow AppEdge.
 */
export function legacyEdgeToAppEdge(legacy: LegacyCanvasEdgeData): AppEdge {
	const data: KnowledgeEdgeData = {
		canvasId: legacy.canvasId,
		relationLabel: legacy.label,
		confidence: null,
		isRecommended: false,
		createdAt: legacy.createdAt,
		updatedAt: legacy.updatedAt,
	};

	return {
		id: legacy.id,
		type: 'knowledge',
		source: legacy.sourceNodeId,
		target: legacy.targetNodeId,
		label: legacy.label,
		data,
	};
}

// ═══════════════════════════════════════════════════════════════════════════
// Backend API response types (carried over from v1-ref api.d.ts)
// ═══════════════════════════════════════════════════════════════════════════

/** Standard API response envelope. */
export interface ApiResponse<T> {
	data: T;
	meta: { timestamp: string };
}

/** Standard API error response. */
export interface ApiError {
	error: { code: string; message: string };
}

/** Backend mastery batch response for a board. */
export interface MasteryBatchResponse {
	concepts: MasteryConceptResponse[];
	topicSummary: Record<
		string,
		{ avgProficiency: number; conceptCount: number; examWeight: number }
	>;
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

/** A concept-relation recommendation from the backend. */
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

/** A node due for FSRS review, displayed in the dashboard. */
export interface ReviewNode {
	conceptId: string;
	name: string;
	boardId: string;
	boardName: string;
	masteryLevel: number;
	masteryColor: string;
	effectiveProficiency: number;
	freshness: 'fresh' | 'recent' | 'due' | 'overdue';
	lastReviewedAt?: string;
	dueDate?: string;
	overdueDays?: number;
}

/** System health check response. */
export interface HealthResponse {
	status: 'healthy' | 'degraded' | 'unhealthy';
	components: Array<{
		name: string;
		status: 'healthy' | 'unhealthy' | 'unknown';
		message?: string;
	}>;
	timestamp: string;
}
