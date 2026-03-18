/**
 * Reactive hooks for board nodes and edges via Dexie liveQuery.
 * These auto-update when IndexedDB data changes (insert/update/delete).
 */
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../services/dexie-db';
import { dexieNodeToReactFlow, dexieEdgeToReactFlow } from '../stores/canvas-store';
import type { Node, Edge } from '@xyflow/react';
import type { KnowledgeNodeData, KnowledgeEdgeData } from '../types';

// Initial values before first query resolves (standard useLiveQuery pattern)
const EMPTY_NODES: Node<KnowledgeNodeData>[] = [];
const EMPTY_EDGES: Edge<KnowledgeEdgeData>[] = [];

/**
 * Returns reactive ReactFlow nodes for the given board.
 * Automatically re-renders when IndexedDB data changes.
 */
export function useBoardNodes(boardId: string | null): Node<KnowledgeNodeData>[] {
  const result = useLiveQuery(
    () => {
      if (!boardId) return EMPTY_NODES;
      return db.canvas_nodes
        .where('canvasId')
        .equals(boardId)
        .toArray()
        .then(rows => rows.map(dexieNodeToReactFlow));
    },
    [boardId],
    EMPTY_NODES,
  );
  return result;
}

/**
 * Returns reactive ReactFlow edges for the given board.
 * Automatically re-renders when IndexedDB data changes.
 */
export function useBoardEdges(boardId: string | null): Edge<KnowledgeEdgeData>[] {
  const result = useLiveQuery(
    () => {
      if (!boardId) return EMPTY_EDGES;
      return db.canvas_edges
        .where('canvasId')
        .equals(boardId)
        .toArray()
        .then(rows => rows.map(dexieEdgeToReactFlow));
    },
    [boardId],
    EMPTY_EDGES,
  );
  return result;
}
