/**
 * Canvas Learning System - Canvas State Store
 * Story 1.4: Whiteboard CRUD + reactive state (AC-1, AC-2, AC-3, AC-4, AC-6)
 *
 * Manages all canvas data through Dexie.js IndexedDB.
 * Uses Dexie liveQuery for reactive data binding.
 * Components read from this store; writes go through its methods.
 *
 * Architecture boundary: this is the ONLY module that imports dexie-db.
 */

import { liveQuery, type Observable } from 'dexie';
import { db } from '../services/dexie-db';
import { generateId, now } from '../utils/canvas-math';
import type {
  CanvasBoard,
  CanvasEdgeData,
  CanvasNodeData,
  DismissedRecommendation,
  Recommendation,
  ViewRoute,
  Viewport,
} from '../types/canvas';
import type { ApiClient } from '../services/api-client';
import { masteryState } from './mastery-state.svelte';

/** Callback type for state change listeners. */
type Listener = () => void;

/**
 * Central canvas state manager.
 * Uses a simple pub/sub pattern so Svelte components can react to changes.
 */
class CanvasState {
  // ─── State fields ──────────────────────────────────────────────────────
  boards: CanvasBoard[] = [];
  currentBoardId: string | null = null;
  nodes: CanvasNodeData[] = [];
  edges: CanvasEdgeData[] = [];
  selectedNodeIds: Set<string> = new Set();
  selectedEdgeIds: Set<string> = new Set();
  viewport: Viewport = { x: 0, y: 0, zoom: 1 };
  currentRoute: ViewRoute = 'dashboard';

  // ─── Subscriptions ─────────────────────────────────────────────────────
  private boardsSub: { unsubscribe(): void } | null = null;
  private nodesSub: { unsubscribe(): void } | null = null;
  private edgesSub: { unsubscribe(): void } | null = null;
  private listeners: Set<Listener> = new Set();

  // Debounce timers for node updates
  private updateTimers: Map<string, ReturnType<typeof setTimeout>> = new Map();

  // Story 5.2: API client reference for mastery data loading
  private apiClient: ApiClient | null = null;

  /** Subscribe to state changes. Returns an unsubscribe function. */
  subscribe(fn: Listener): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  /** Notify all listeners of a state change. */
  private notify(): void {
    for (const fn of this.listeners) {
      fn();
    }
  }

  // ─── Initialization ────────────────────────────────────────────────────

  /**
   * Initialize: subscribe to boards list via liveQuery.
   * Optionally accepts an ApiClient for mastery data loading (Story 5.2).
   */
  async init(apiClient?: ApiClient): Promise<void> {
    if (apiClient) {
      this.apiClient = apiClient;
    }
    this.subscribeBoardsList();
  }

  /** Dispose all subscriptions. */
  dispose(): void {
    this.boardsSub?.unsubscribe();
    this.nodesSub?.unsubscribe();
    this.edgesSub?.unsubscribe();
    this.boardsSub = null;
    this.nodesSub = null;
    this.edgesSub = null;
    for (const timer of this.updateTimers.values()) {
      clearTimeout(timer);
    }
    this.updateTimers.clear();
  }

  // ─── LiveQuery subscriptions ───────────────────────────────────────────

  private subscribeBoardsList(): void {
    this.boardsSub?.unsubscribe();
    const observable: Observable<CanvasBoard[]> = liveQuery(() =>
      db.canvas_boards.orderBy('updatedAt').reverse().toArray(),
    );
    this.boardsSub = observable.subscribe({
      next: (result) => {
        this.boards = result;
        this.notify();
      },
      error: (err) => {
        console.error('[Canvas Learning] boards liveQuery error:', err);
      },
    });
  }

  private subscribeNodes(boardId: string): void {
    this.nodesSub?.unsubscribe();
    const observable: Observable<CanvasNodeData[]> = liveQuery(() =>
      db.canvas_nodes.where('canvasId').equals(boardId).toArray(),
    );
    this.nodesSub = observable.subscribe({
      next: (result) => {
        this.nodes = result;
        this.notify();
      },
      error: (err) => {
        console.error('[Canvas Learning] nodes liveQuery error:', err);
      },
    });
  }

  private subscribeEdges(boardId: string): void {
    this.edgesSub?.unsubscribe();
    const observable: Observable<CanvasEdgeData[]> = liveQuery(() =>
      db.canvas_edges.where('canvasId').equals(boardId).toArray(),
    );
    this.edgesSub = observable.subscribe({
      next: (result) => {
        this.edges = result;
        this.notify();
      },
      error: (err) => {
        console.error('[Canvas Learning] edges liveQuery error:', err);
      },
    });
  }

  // ─── Board CRUD ────────────────────────────────────────────────────────

  async createBoard(name: string): Promise<CanvasBoard> {
    const board: CanvasBoard = {
      id: generateId(),
      name,
      createdAt: now(),
      updatedAt: now(),
    };

    await db.canvas_boards.add(board);
    await this.writeOutbox('board', board.id, 'create', board);

    // Auto-switch to the new board
    await this.switchBoard(board.id);
    return board;
  }

  async deleteBoard(id: string): Promise<void> {
    await db.transaction('rw', [db.canvas_boards, db.canvas_nodes, db.canvas_edges, db.sync_outbox], async () => {
      // Delete all nodes and edges belonging to this board
      const nodeIds = await db.canvas_nodes.where('canvasId').equals(id).primaryKeys();
      const edgeIds = await db.canvas_edges.where('canvasId').equals(id).primaryKeys();

      await db.canvas_nodes.bulkDelete(nodeIds);
      await db.canvas_edges.bulkDelete(edgeIds);
      await db.canvas_boards.delete(id);

      await this.writeOutbox('board', id, 'delete', { id });
    });

    // If we deleted the current board, go back to dashboard
    if (this.currentBoardId === id) {
      this.currentBoardId = null;
      this.nodes = [];
      this.edges = [];
      this.nodesSub?.unsubscribe();
      this.edgesSub?.unsubscribe();
      this.nodesSub = null;
      this.edgesSub = null;
      this.currentRoute = 'dashboard';
      this.notify();
    }
  }

  async switchBoard(id: string): Promise<void> {
    this.currentBoardId = id;
    this.selectedNodeIds = new Set();
    this.selectedEdgeIds = new Set();
    this.viewport = { x: 0, y: 0, zoom: 1 };
    this.currentRoute = 'canvas';

    // Re-subscribe liveQueries for the new board
    this.subscribeNodes(id);
    this.subscribeEdges(id);

    // Story 5.2: Load mastery data for the new board (non-blocking)
    this.loadBoardMastery(id);

    this.notify();
  }

  /**
   * Story 5.2: Fetch and load mastery data for a board.
   * Non-blocking — failures are logged but do not prevent board rendering.
   * Degradation (NFR-REL-02): on error, all nodes show default "unlearned" color.
   */
  private async loadBoardMastery(boardId: string): Promise<void> {
    if (!this.apiClient) {
      masteryState.clear();
      return;
    }

    try {
      const masteryData = await this.apiClient.getBoardMastery(boardId);
      masteryState.loadBoardMastery(masteryData);
    } catch (err) {
      console.warn(
        `[Canvas Learning] Mastery load failed for board "${boardId}":`,
        err,
      );
      masteryState.clear();
    }
  }

  navigateToDashboard(): void {
    this.currentBoardId = null;
    this.nodes = [];
    this.edges = [];
    this.selectedNodeIds = new Set();
    this.selectedEdgeIds = new Set();
    this.nodesSub?.unsubscribe();
    this.edgesSub?.unsubscribe();
    this.nodesSub = null;
    this.edgesSub = null;
    this.currentRoute = 'dashboard';

    // Story 5.2: Clear mastery data when leaving canvas
    masteryState.clear();

    this.notify();
  }

  // ─── Node CRUD ─────────────────────────────────────────────────────────

  async addNode(partial: Partial<CanvasNodeData>): Promise<CanvasNodeData> {
    if (!this.currentBoardId) {
      throw new Error('No active board');
    }

    const node: CanvasNodeData = {
      id: generateId(),
      canvasId: this.currentBoardId,
      type: partial.type ?? 'text',
      title: partial.title ?? '',
      content: partial.content ?? '',
      x: partial.x ?? 0,
      y: partial.y ?? 0,
      width: partial.width ?? 200,
      height: partial.height ?? 120,
      createdAt: now(),
      updatedAt: now(),
    };

    await db.canvas_nodes.add(node);
    await this.writeOutbox('node', node.id, 'create', node);

    // Update the board's updatedAt
    await db.canvas_boards.update(this.currentBoardId, { updatedAt: now() });

    // Story 1.7: trigger recommendation analysis after node change
    this.scheduleRecommendationFetch();

    return node;
  }

  /**
   * Update a node with debounce for content edits.
   * Position updates (from drag) bypass debounce when immediate=true.
   */
  async updateNode(
    id: string,
    changes: Partial<CanvasNodeData>,
    immediate = false,
  ): Promise<void> {
    const doUpdate = async () => {
      const updatedChanges = { ...changes, updatedAt: now() };
      await db.canvas_nodes.update(id, updatedChanges);
      await this.writeOutbox('node', id, 'update', updatedChanges);
    };

    if (immediate) {
      await doUpdate();
    } else {
      // Debounce 300ms for content edits
      const existing = this.updateTimers.get(id);
      if (existing) clearTimeout(existing);
      this.updateTimers.set(
        id,
        setTimeout(() => {
          this.updateTimers.delete(id);
          doUpdate();
        }, 300),
      );
    }
  }

  async deleteNode(id: string): Promise<void> {
    if (!this.currentBoardId) return;

    await db.transaction('rw', [db.canvas_nodes, db.canvas_edges, db.sync_outbox], async () => {
      // Delete all edges connected to this node
      const connectedEdges = await db.canvas_edges
        .where('canvasId')
        .equals(this.currentBoardId!)
        .filter((e) => e.sourceNodeId === id || e.targetNodeId === id)
        .toArray();

      for (const edge of connectedEdges) {
        await db.canvas_edges.delete(edge.id);
        await this.writeOutbox('edge', edge.id, 'delete', { id: edge.id });
      }

      await db.canvas_nodes.delete(id);
      await this.writeOutbox('node', id, 'delete', { id });
    });

    this.selectedNodeIds.delete(id);
    // Story 1.7: trigger recommendation analysis after node change
    this.scheduleRecommendationFetch();
    this.notify();
  }

  // ─── Edge CRUD ─────────────────────────────────────────────────────────

  async addEdge(partial: Partial<CanvasEdgeData>): Promise<CanvasEdgeData> {
    if (!this.currentBoardId) {
      throw new Error('No active board');
    }
    if (!partial.sourceNodeId || !partial.targetNodeId) {
      throw new Error('Edge requires sourceNodeId and targetNodeId');
    }
    // Prevent self-loops
    if (partial.sourceNodeId === partial.targetNodeId) {
      throw new Error('Cannot create self-loop edge');
    }

    const edge: CanvasEdgeData = {
      id: generateId(),
      canvasId: this.currentBoardId,
      sourceNodeId: partial.sourceNodeId,
      targetNodeId: partial.targetNodeId,
      label: partial.label ?? '',
      createdAt: now(),
      updatedAt: now(),
    };

    await db.canvas_edges.add(edge);
    await this.writeOutbox('edge', edge.id, 'create', edge);
    // Story 1.7: trigger recommendation analysis after edge change
    this.scheduleRecommendationFetch();
    return edge;
  }

  async updateEdge(id: string, changes: Partial<CanvasEdgeData>): Promise<void> {
    const updatedChanges = { ...changes, updatedAt: now() };
    await db.canvas_edges.update(id, updatedChanges);
    await this.writeOutbox('edge', id, 'update', updatedChanges);
  }

  async deleteEdge(id: string): Promise<void> {
    await db.canvas_edges.delete(id);
    await this.writeOutbox('edge', id, 'delete', { id });
    this.selectedEdgeIds.delete(id);
    this.notify();
  }

  // ─── Selection ─────────────────────────────────────────────────────────

  selectNode(id: string, additive = false): void {
    if (!additive) {
      this.selectedNodeIds = new Set();
      this.selectedEdgeIds = new Set();
    }
    if (this.selectedNodeIds.has(id)) {
      this.selectedNodeIds.delete(id);
    } else {
      this.selectedNodeIds.add(id);
    }
    this.notify();
  }

  selectEdge(id: string, additive = false): void {
    if (!additive) {
      this.selectedNodeIds = new Set();
      this.selectedEdgeIds = new Set();
    }
    if (this.selectedEdgeIds.has(id)) {
      this.selectedEdgeIds.delete(id);
    } else {
      this.selectedEdgeIds.add(id);
    }
    this.notify();
  }

  selectAll(): void {
    this.selectedNodeIds = new Set(this.nodes.map((n) => n.id));
    this.selectedEdgeIds = new Set(this.edges.map((e) => e.id));
    this.notify();
  }

  clearSelection(): void {
    this.selectedNodeIds = new Set();
    this.selectedEdgeIds = new Set();
    this.notify();
  }

  setSelectedNodeIds(ids: Set<string>): void {
    this.selectedNodeIds = ids;
    this.notify();
  }

  /** Batch delete all selected nodes and edges. */
  async deleteSelected(): Promise<void> {
    const nodeIds = [...this.selectedNodeIds];
    const edgeIds = [...this.selectedEdgeIds];

    for (const id of nodeIds) {
      await this.deleteNode(id);
    }
    for (const id of edgeIds) {
      await this.deleteEdge(id);
    }

    this.selectedNodeIds = new Set();
    this.selectedEdgeIds = new Set();
    this.notify();
  }

  // ─── Viewport ──────────────────────────────────────────────────────────

  setViewport(vp: Viewport): void {
    this.viewport = vp;
    this.notify();
  }

  // ─── Story 1.7: Recommendation state ──────────────────────────────────
  recommendations: Recommendation[] = [];
  recommendationBarVisible = false;
  recommendationBarExpanded = false;
  dismissedSessionClosed = false;
  private recommendationDebounceTimer: ReturnType<typeof setTimeout> | null = null;

  /**
   * Trigger a debounced recommendation fetch after node/edge changes (AC-1).
   * Only fires if >= 5 nodes exist on the current board.
   */
  scheduleRecommendationFetch(): void {
    if (this.recommendationDebounceTimer) {
      clearTimeout(this.recommendationDebounceTimer);
    }
    this.recommendationDebounceTimer = setTimeout(() => {
      this.recommendationDebounceTimer = null;
      this.fetchRecommendationsIfEligible();
    }, 5000);
  }

  private async fetchRecommendationsIfEligible(): Promise<void> {
    if (!this.currentBoardId || !this.apiClient) return;
    if (this.nodes.length < 5) return;

    // Get dismissed pairs from IndexedDB (last 24h)
    const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    const dismissed = await db.dismissed_recommendations
      .where('dismissedAt')
      .above(cutoff)
      .toArray();

    const dismissedPairs = dismissed.map(d => {
      const [a, b] = d.pairKey.split('_');
      return { nodeIdA: a, nodeIdB: b };
    });

    const response = await this.apiClient.fetchRecommendations(
      this.currentBoardId,
      dismissedPairs,
    );

    this.recommendations = response.recommendations;
    if (response.recommendations.length > 0 && !this.dismissedSessionClosed) {
      this.recommendationBarVisible = true;
    } else if (response.recommendations.length === 0) {
      this.recommendationBarVisible = false;
    }
    this.notify();
  }

  /**
   * Accept a recommendation: create edge and remove from list (AC-4).
   */
  async acceptRecommendation(recId: string): Promise<void> {
    const rec = this.recommendations.find(r => r.id === recId);
    if (!rec) return;

    await this.addEdge({
      sourceNodeId: rec.sourceNodeId,
      targetNodeId: rec.targetNodeId,
      label: rec.suggestedLabel,
    });

    this.recommendations = this.recommendations.filter(r => r.id !== recId);
    if (this.recommendations.length === 0) {
      this.recommendationBarVisible = false;
    }
    this.notify();
  }

  /**
   * Dismiss a recommendation: record in IndexedDB and remove from list (AC-5).
   */
  async dismissRecommendation(recId: string): Promise<void> {
    const rec = this.recommendations.find(r => r.id === recId);
    if (!rec) return;

    // Build sorted pair key
    const ids = [rec.sourceNodeId, rec.targetNodeId].sort();
    const pairKey = `${ids[0]}_${ids[1]}`;

    await db.dismissed_recommendations.add({
      pairKey,
      dismissedAt: now(),
    });

    this.recommendations = this.recommendations.filter(r => r.id !== recId);
    if (this.recommendations.length === 0) {
      this.recommendationBarVisible = false;
    }
    this.notify();
  }

  /**
   * Close the recommendation bar for this session (AC-3).
   */
  closeRecommendationBar(): void {
    this.recommendationBarVisible = false;
    this.dismissedSessionClosed = true;
    this.notify();
  }

  // ─── Outbox (for Story 1.5 delta sync) ─────────────────────────────────

  private async writeOutbox(
    entityType: 'node' | 'edge' | 'board',
    entityId: string,
    operation: 'create' | 'update' | 'delete',
    payload: Record<string, unknown>,
  ): Promise<void> {
    await db.sync_outbox.add({
      entityType,
      entityId,
      operation,
      payload,
      createdAt: now(),
    });
  }

  // ─── Helpers ───────────────────────────────────────────────────────────

  /** Get a node by ID from the current in-memory array. */
  getNodeById(id: string): CanvasNodeData | undefined {
    return this.nodes.find((n) => n.id === id);
  }

  /** Get the current board name. */
  getCurrentBoardName(): string {
    if (!this.currentBoardId) return '';
    const board = this.boards.find((b) => b.id === this.currentBoardId);
    return board?.name ?? '';
  }

  /** Count nodes for a given board ID (used in dashboard cards). */
  async getNodeCount(boardId: string): Promise<number> {
    return db.canvas_nodes.where('canvasId').equals(boardId).count();
  }
}

/** Singleton store instance. */
export const canvasState = new CanvasState();
