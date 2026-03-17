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
