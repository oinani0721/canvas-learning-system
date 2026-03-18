/**
 * Zustand Canvas Store — CRUD operations with Dexie persistence
 * Story 1-4: Board management, view routing, node/edge CRUD
 *
 * Architecture (GDR-P1-2):
 *   - Zustand: board list, view state, current board, selections
 *   - useLiveQuery (dexie-react-hooks): reactive node/edge reads in components
 *   - This store handles all writes (Dexie + sync_outbox)
 */
import { create } from 'zustand';
import { db, type CanvasBoard, type CanvasNode, type CanvasEdge } from '../services/dexie-db';
import type { KnowledgeNodeData, KnowledgeEdgeData } from '../types';
import type { Node, Edge } from '@xyflow/react';

// --- Dexie ↔ ReactFlow conversion helpers ---

function now(): string {
  return new Date().toISOString();
}

function generateId(): string {
  return crypto.randomUUID();
}

export function dexieNodeToReactFlow(n: CanvasNode): Node<KnowledgeNodeData> {
  const data: KnowledgeNodeData = {
    canvasId: n.canvasId,
    nodeType: n.type,
    title: n.title,
    content: n.content,
    createdAt: n.createdAt,
    updatedAt: n.updatedAt,
    masteryStatus: (n.masteryStatus as KnowledgeNodeData['masteryStatus']) ?? 'unlearned',
    effectiveProficiency: n.effectiveProficiency ?? null,
    hasExamRecord: n.hasExamRecord ?? false,
    hasInteraction: false,
    masteryLevel: null,
    masteryLabel: null,
    fsrs: null,
    indexStatus: (n.indexStatus as KnowledgeNodeData['indexStatus']) ?? 'none',
    imageData: n.imageData,
    ocr: n.ocrText ? { text: n.ocrText, summary: n.ocrSummary ?? '', concepts: n.ocrConcepts ?? [] } : undefined,
    tips: [],
    interactionCount: 0,
    examCount: 0,
  };
  return {
    id: n.id,
    type: n.type === 'image' ? 'image' : 'knowledge',
    position: { x: n.x, y: n.y },
    width: n.width,
    height: n.height,
    data,
  };
}

export function dexieEdgeToReactFlow(e: CanvasEdge): Edge<KnowledgeEdgeData> {
  return {
    id: e.id,
    source: e.sourceNodeId,
    target: e.targetNodeId,
    label: e.label,
    data: {
      canvasId: e.canvasId,
      relationLabel: e.label,
      confidence: null,
      isRecommended: false,
      createdAt: e.createdAt,
      updatedAt: e.updatedAt,
    },
  };
}

// --- Outbox helper ---

async function writeOutbox(
  entityType: 'node' | 'edge' | 'board',
  entityId: string,
  operation: 'create' | 'update' | 'delete',
  payload: Record<string, unknown>,
) {
  await db.sync_outbox.add({
    entityType,
    entityId,
    operation,
    payload,
    createdAt: now(),
  });
}

// --- Store types ---

type ViewMode = 'dashboard' | 'canvas' | 'settings';

interface CanvasStore {
  // State
  boards: CanvasBoard[];
  currentBoardId: string | null;
  currentBoardName: string | null;
  view: ViewMode;
  selectedNodeId: string | null;

  // Board operations
  loadBoards: () => Promise<void>;
  createBoard: (name: string) => Promise<CanvasBoard>;
  deleteBoard: (id: string) => Promise<void>;
  openBoard: (id: string) => Promise<void>;
  goToDashboard: () => void;
  goToSettings: () => void;

  // Node CRUD
  addNode: (position: { x: number; y: number }, title?: string) => Promise<string>;
  addImageNode: (position: { x: number; y: number }, imageData: string, title?: string) => Promise<string>;
  updateNode: (id: string, changes: Partial<Pick<CanvasNode, 'title' | 'content' | 'x' | 'y' | 'width' | 'height'>>) => Promise<void>;
  deleteNodes: (ids: string[]) => Promise<void>;

  // Edge CRUD
  addEdge: (sourceNodeId: string, targetNodeId: string, label?: string) => Promise<string>;
  updateEdge: (id: string, changes: Partial<Pick<CanvasEdge, 'label'>>) => Promise<void>;
  deleteEdges: (ids: string[]) => Promise<void>;

  // Bulk delete selected
  deleteSelected: (nodeIds: string[], edgeIds: string[]) => Promise<void>;

  // Selection
  setSelectedNodeId: (id: string | null) => void;
}

export const useCanvasStore = create<CanvasStore>((set, get) => ({
  boards: [],
  currentBoardId: null,
  currentBoardName: null,
  view: 'dashboard',
  selectedNodeId: null,

  loadBoards: async () => {
    const boards = await db.canvas_boards.orderBy('updatedAt').reverse().toArray();
    set({ boards });
  },

  createBoard: async (name: string) => {
    const board: CanvasBoard = {
      id: generateId(),
      name,
      createdAt: now(),
      updatedAt: now(),
    };
    await db.canvas_boards.add(board);
    await writeOutbox('board', board.id, 'create', board as unknown as Record<string, unknown>);
    // Refresh boards list and open the new board
    const boards = await db.canvas_boards.orderBy('updatedAt').reverse().toArray();
    set({
      boards,
      currentBoardId: board.id,
      currentBoardName: board.name,
      view: 'canvas',
      selectedNodeId: null,
    });
    return board;
  },

  deleteBoard: async (id: string) => {
    // Delete all nodes and edges for this board
    await db.canvas_nodes.where('canvasId').equals(id).delete();
    await db.canvas_edges.where('canvasId').equals(id).delete();
    await db.canvas_boards.delete(id);
    await writeOutbox('board', id, 'delete', { id });
    const boards = await db.canvas_boards.orderBy('updatedAt').reverse().toArray();
    const state = get();
    set({
      boards,
      currentBoardId: state.currentBoardId === id ? null : state.currentBoardId,
      currentBoardName: state.currentBoardId === id ? null : state.currentBoardName,
      view: state.currentBoardId === id ? 'dashboard' : state.view,
    });
  },

  openBoard: async (id: string) => {
    const board = await db.canvas_boards.get(id);
    if (!board) return;
    set({
      currentBoardId: id,
      currentBoardName: board.name,
      view: 'canvas',
      selectedNodeId: null,
    });
  },

  goToDashboard: () => {
    set({ view: 'dashboard', selectedNodeId: null });
  },

  goToSettings: () => {
    set({ view: 'settings' });
  },

  addNode: async (position, title = 'New Concept') => {
    const boardId = get().currentBoardId;
    if (!boardId) throw new Error('No board selected');
    const id = generateId();
    const ts = now();
    const node: CanvasNode = {
      id,
      canvasId: boardId,
      type: 'text',
      title,
      content: '',
      x: position.x,
      y: position.y,
      width: 240,
      height: 120,
      masteryStatus: 'unlearned',
      effectiveProficiency: 0,
      hasExamRecord: false,
      createdAt: ts,
      updatedAt: ts,
    };
    await db.canvas_nodes.add(node);
    await writeOutbox('node', id, 'create', node as unknown as Record<string, unknown>);
    return id;
  },

  addImageNode: async (position, imageData, title = 'Image') => {
    const boardId = get().currentBoardId;
    if (!boardId) throw new Error('No board selected');
    const id = generateId();
    const ts = now();
    const node: CanvasNode = {
      id,
      canvasId: boardId,
      type: 'image',
      title,
      content: '',
      x: position.x,
      y: position.y,
      width: 280,
      height: 200,
      imageData,
      indexStatus: 'none',
      createdAt: ts,
      updatedAt: ts,
    };
    await db.canvas_nodes.add(node);
    // Outbox excludes imageData (too large for Neo4j)
    const outboxPayload = { ...node, imageData: undefined } as unknown as Record<string, unknown>;
    delete outboxPayload.imageData;
    await writeOutbox('node', id, 'create', outboxPayload);
    return id;
  },

  updateNode: async (id, changes) => {
    await db.canvas_nodes.update(id, { ...changes, updatedAt: now() });
    await writeOutbox('node', id, 'update', { id, ...changes });
    // Update board's updatedAt
    const node = await db.canvas_nodes.get(id);
    if (node) {
      await db.canvas_boards.update(node.canvasId, { updatedAt: now() });
    }
  },

  deleteNodes: async (ids) => {
    // Delete associated edges first
    for (const nodeId of ids) {
      const edges = await db.canvas_edges
        .where('sourceNodeId').equals(nodeId)
        .or('targetNodeId').equals(nodeId)
        .toArray();
      for (const edge of edges) {
        await db.canvas_edges.delete(edge.id);
        await writeOutbox('edge', edge.id, 'delete', { id: edge.id });
      }
    }
    // Delete nodes
    await db.canvas_nodes.bulkDelete(ids);
    for (const id of ids) {
      await writeOutbox('node', id, 'delete', { id });
    }
    const state = get();
    if (state.selectedNodeId && ids.includes(state.selectedNodeId)) {
      set({ selectedNodeId: null });
    }
  },

  addEdge: async (sourceNodeId, targetNodeId, label = '') => {
    const boardId = get().currentBoardId;
    if (!boardId) throw new Error('No board selected');
    const id = generateId();
    const ts = now();
    const edge: CanvasEdge = {
      id,
      canvasId: boardId,
      sourceNodeId,
      targetNodeId,
      label,
      createdAt: ts,
      updatedAt: ts,
    };
    await db.canvas_edges.add(edge);
    await writeOutbox('edge', id, 'create', edge as unknown as Record<string, unknown>);
    return id;
  },

  updateEdge: async (id, changes) => {
    await db.canvas_edges.update(id, { ...changes, updatedAt: now() });
    await writeOutbox('edge', id, 'update', { id, ...changes });
  },

  deleteEdges: async (ids) => {
    await db.canvas_edges.bulkDelete(ids);
    for (const id of ids) {
      await writeOutbox('edge', id, 'delete', { id });
    }
  },

  deleteSelected: async (nodeIds, edgeIds) => {
    if (edgeIds.length > 0) {
      await get().deleteEdges(edgeIds);
    }
    if (nodeIds.length > 0) {
      await get().deleteNodes(nodeIds);
    }
  },

  setSelectedNodeId: (id) => {
    set({ selectedNodeId: id });
  },
}));
