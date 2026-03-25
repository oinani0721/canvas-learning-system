/**
 * Canvas Edge API
 * Story 13.2: Canvas API集成 - Task 3
 *
 * Provides edge (connection) operations for Canvas files.
 *
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #5: Creating Edges)
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #8: getConnectedNodes)
 * ✅ Verified from specs/api/canvas-api.openapi.yml#createEdge, #deleteEdge
 */

import {
  CanvasData,
  CanvasNode,
  CanvasEdge,
  CanvasEdgeSide,
  CanvasEdgeEnd,
  CreateEdgeOptions,
} from '../types/canvas';
import { generateId } from '../utils/canvas-helpers';

/**
 * Canvas Edge API
 * Provides CRUD operations for Canvas edges (connections).
 *
 * Story 13.2: AC 3, 6
 */
export class CanvasEdgeAPI {
  // ============================================================================
  // Edge ID Generation
  // ============================================================================

  /**
   * Generate unique edge ID
   * ✅ Verified from @obsidian-canvas Skill (Quick Reference #5)
   *
   * @returns Unique edge ID
   */
  generateEdgeId(): string {
    return generateId();
  }

  // ============================================================================
  // Create Operations
  // ============================================================================

  /**
   * Create an edge between two nodes
   * ✅ Verified from @obsidian-canvas Skill (Quick Reference #5: createEdge)
   *
   * @param fromNodeId - Source node ID
   * @param toNodeId - Target node ID
   * @param options - Optional edge properties
   * @returns Created edge
   */
  createEdge(
    fromNodeId: string,
    toNodeId: string,
    options?: CreateEdgeOptions
  ): CanvasEdge {
    // ✅ Verified from @obsidian-canvas Skill (Quick Reference #5)
    // "function createEdge(fromNodeId, toNodeId, options?) {
    //   return {
    //     id: generateId(),
    //     fromNode: fromNodeId,
    //     toNode: toNodeId,
    //     fromSide: options?.fromSide,
    //     toSide: options?.toSide,
    //     toEnd: options?.toEnd || 'arrow',
    //     label: options?.label,
    //     color: options?.color
    //   };
    // }"
    return {
      id: this.generateEdgeId(),
      fromNode: fromNodeId,
      toNode: toNodeId,
      fromSide: options?.fromSide,
      toSide: options?.toSide,
      toEnd: options?.toEnd ?? 'arrow',
      label: options?.label,
      color: options?.color,
    };
  }

  /**
   * Create an edge with arrow pointing to target
   *
   * @param fromNodeId - Source node ID
   * @param toNodeId - Target node ID
   * @param fromSide - Source connection side
   * @param toSide - Target connection side
   * @returns Created edge with arrow
   */
  createArrowEdge(
    fromNodeId: string,
    toNodeId: string,
    fromSide?: CanvasEdgeSide,
    toSide?: CanvasEdgeSide
  ): CanvasEdge {
    return this.createEdge(fromNodeId, toNodeId, {
      fromSide,
      toSide,
      toEnd: 'arrow',
    });
  }

  /**
   * Create a line edge (no arrow)
   *
   * @param fromNodeId - Source node ID
   * @param toNodeId - Target node ID
   * @param fromSide - Source connection side
   * @param toSide - Target connection side
   * @returns Created edge without arrow
   */
  createLineEdge(
    fromNodeId: string,
    toNodeId: string,
    fromSide?: CanvasEdgeSide,
    toSide?: CanvasEdgeSide
  ): CanvasEdge {
    return this.createEdge(fromNodeId, toNodeId, {
      fromSide,
      toSide,
      toEnd: 'none',
    });
  }

  // ============================================================================
  // Read Operations
  // ============================================================================

  /**
   * Get edge by ID
   *
   * @param canvasData - Canvas data
   * @param edgeId - Edge ID
   * @returns Edge or null if not found
   */
  getEdgeById(canvasData: CanvasData, edgeId: string): CanvasEdge | null {
    return canvasData.edges.find((edge) => edge.id === edgeId) ?? null;
  }

  /**
   * Get all nodes connected to a specific node
   * ✅ Verified from @obsidian-canvas Skill (Quick Reference #8: getConnectedNodes)
   *
   * @param canvasData - Canvas data
   * @param nodeId - Node ID to find connections for
   * @returns Array of connected nodes
   */
  getConnectedNodes(canvasData: CanvasData, nodeId: string): CanvasNode[] {
    // ✅ Verified from @obsidian-canvas Skill (Quick Reference #8)
    // "function getConnectedNodes(canvasData: any, nodeId: string) {
    //   const connectedIds = new Set();
    //   canvasData.edges.forEach(edge => {
    //     if (edge.fromNode === nodeId) connectedIds.add(edge.toNode);
    //     if (edge.toNode === nodeId) connectedIds.add(edge.fromNode);
    //   });
    //   return canvasData.nodes.filter(node => connectedIds.has(node.id));
    // }"
    const connectedIds = new Set<string>();

    for (const edge of canvasData.edges) {
      if (edge.fromNode === nodeId) {
        connectedIds.add(edge.toNode);
      }
      if (edge.toNode === nodeId) {
        connectedIds.add(edge.fromNode);
      }
    }

    return canvasData.nodes.filter((node) => connectedIds.has(node.id));
  }

  /**
   * Get all edges connected to a node (incoming or outgoing)
   *
   * @param canvasData - Canvas data
   * @param nodeId - Node ID
   * @returns Array of connected edges
   */
  getEdgesByNode(canvasData: CanvasData, nodeId: string): CanvasEdge[] {
    return canvasData.edges.filter(
      (edge) => edge.fromNode === nodeId || edge.toNode === nodeId
    );
  }

  /**
   * Get outgoing edges from a node
   *
   * @param canvasData - Canvas data
   * @param nodeId - Source node ID
   * @returns Array of outgoing edges
   */
  getOutgoingEdges(canvasData: CanvasData, nodeId: string): CanvasEdge[] {
    return canvasData.edges.filter((edge) => edge.fromNode === nodeId);
  }

  /**
   * Get incoming edges to a node
   *
   * @param canvasData - Canvas data
   * @param nodeId - Target node ID
   * @returns Array of incoming edges
   */
  getIncomingEdges(canvasData: CanvasData, nodeId: string): CanvasEdge[] {
    return canvasData.edges.filter((edge) => edge.toNode === nodeId);
  }

  /**
   * Get all edges between two specific nodes
   * Story 13.2: AC 3 - getEdgesBetweenNodes
   *
   * @param canvasData - Canvas data
   * @param nodeId1 - First node ID
   * @param nodeId2 - Second node ID
   * @returns Array of edges between the two nodes (bidirectional)
   */
  getEdgesBetweenNodes(
    canvasData: CanvasData,
    nodeId1: string,
    nodeId2: string
  ): CanvasEdge[] {
    return canvasData.edges.filter(
      (edge) =>
        (edge.fromNode === nodeId1 && edge.toNode === nodeId2) ||
        (edge.fromNode === nodeId2 && edge.toNode === nodeId1)
    );
  }

  /**
   * Check if two nodes are connected
   *
   * @param canvasData - Canvas data
   * @param nodeId1 - First node ID
   * @param nodeId2 - Second node ID
   * @returns True if nodes are connected
   */
  areNodesConnected(
    canvasData: CanvasData,
    nodeId1: string,
    nodeId2: string
  ): boolean {
    return this.getEdgesBetweenNodes(canvasData, nodeId1, nodeId2).length > 0;
  }

  /**
   * Get child nodes (nodes that this node points to)
   *
   * @param canvasData - Canvas data
   * @param nodeId - Parent node ID
   * @returns Array of child nodes
   */
  getChildNodes(canvasData: CanvasData, nodeId: string): CanvasNode[] {
    const childIds = new Set<string>();

    for (const edge of canvasData.edges) {
      if (edge.fromNode === nodeId) {
        childIds.add(edge.toNode);
      }
    }

    return canvasData.nodes.filter((node) => childIds.has(node.id));
  }

  /**
   * Get parent nodes (nodes that point to this node)
   *
   * @param canvasData - Canvas data
   * @param nodeId - Child node ID
   * @returns Array of parent nodes
   */
  getParentNodes(canvasData: CanvasData, nodeId: string): CanvasNode[] {
    const parentIds = new Set<string>();

    for (const edge of canvasData.edges) {
      if (edge.toNode === nodeId) {
        parentIds.add(edge.fromNode);
      }
    }

    return canvasData.nodes.filter((node) => parentIds.has(node.id));
  }

  // ============================================================================
  // Delete Operations
  // ============================================================================

  /**
   * Delete an edge by ID
   * Story 13.2: AC 3 - deleteEdge
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param edgeId - Edge ID to delete
   * @throws Error if edge not found
   */
  deleteEdge(canvasData: CanvasData, edgeId: string): void {
    const edgeIndex = canvasData.edges.findIndex((edge) => edge.id === edgeId);
    if (edgeIndex === -1) {
      throw new Error(`Edge not found: ${edgeId}`);
    }
    canvasData.edges.splice(edgeIndex, 1);
  }

  /**
   * Delete all edges connected to a node
   * Story 13.2: AC 3 - deleteEdgesByNode (for cascade delete)
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param nodeId - Node ID
   * @returns Number of edges deleted
   */
  deleteEdgesByNode(canvasData: CanvasData, nodeId: string): number {
    const initialCount = canvasData.edges.length;
    canvasData.edges = canvasData.edges.filter(
      (edge) => edge.fromNode !== nodeId && edge.toNode !== nodeId
    );
    return initialCount - canvasData.edges.length;
  }

  /**
   * Delete all edges between two nodes
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param nodeId1 - First node ID
   * @param nodeId2 - Second node ID
   * @returns Number of edges deleted
   */
  deleteEdgesBetweenNodes(
    canvasData: CanvasData,
    nodeId1: string,
    nodeId2: string
  ): number {
    const initialCount = canvasData.edges.length;
    canvasData.edges = canvasData.edges.filter(
      (edge) =>
        !(edge.fromNode === nodeId1 && edge.toNode === nodeId2) &&
        !(edge.fromNode === nodeId2 && edge.toNode === nodeId1)
    );
    return initialCount - canvasData.edges.length;
  }

  // ============================================================================
  // Update Operations
  // ============================================================================

  /**
   * Update edge properties
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param edgeId - Edge ID
   * @param updates - Properties to update
   * @throws Error if edge not found
   */
  updateEdge(
    canvasData: CanvasData,
    edgeId: string,
    updates: Partial<Omit<CanvasEdge, 'id'>>
  ): void {
    const edgeIndex = canvasData.edges.findIndex((edge) => edge.id === edgeId);
    if (edgeIndex === -1) {
      throw new Error(`Edge not found: ${edgeId}`);
    }

    canvasData.edges[edgeIndex] = {
      ...canvasData.edges[edgeIndex],
      ...updates,
      id: edgeId, // Ensure ID is not modified
    };
  }

  /**
   * Update edge label
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param edgeId - Edge ID
   * @param label - New label
   */
  updateEdgeLabel(
    canvasData: CanvasData,
    edgeId: string,
    label: string | undefined
  ): void {
    this.updateEdge(canvasData, edgeId, { label });
  }

  /**
   * Update edge color
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param edgeId - Edge ID
   * @param color - New color
   */
  updateEdgeColor(
    canvasData: CanvasData,
    edgeId: string,
    color: string | undefined
  ): void {
    this.updateEdge(canvasData, edgeId, { color: color as CanvasEdge['color'] });
  }

  /**
   * Update edge arrow style
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param edgeId - Edge ID
   * @param toEnd - Arrow style
   */
  updateEdgeArrow(
    canvasData: CanvasData,
    edgeId: string,
    toEnd: CanvasEdgeEnd
  ): void {
    this.updateEdge(canvasData, edgeId, { toEnd });
  }

  // ============================================================================
  // Add Operations
  // ============================================================================

  /**
   * Add an edge to canvas
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param edge - Edge to add
   */
  addEdge(canvasData: CanvasData, edge: CanvasEdge): void {
    canvasData.edges.push(edge);
  }

  /**
   * Add multiple edges to canvas
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param edges - Edges to add
   */
  addEdges(canvasData: CanvasData, edges: CanvasEdge[]): void {
    canvasData.edges.push(...edges);
  }

  /**
   * Connect two nodes with a new edge
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param fromNodeId - Source node ID
   * @param toNodeId - Target node ID
   * @param options - Edge options
   * @returns Created edge
   */
  connectNodes(
    canvasData: CanvasData,
    fromNodeId: string,
    toNodeId: string,
    options?: CreateEdgeOptions
  ): CanvasEdge {
    const edge = this.createEdge(fromNodeId, toNodeId, options);
    this.addEdge(canvasData, edge);
    return edge;
  }

  // ============================================================================
  // Utility Methods
  // ============================================================================

  /**
   * Check if edge exists
   *
   * @param canvasData - Canvas data
   * @param edgeId - Edge ID
   * @returns True if edge exists
   */
  edgeExists(canvasData: CanvasData, edgeId: string): boolean {
    return canvasData.edges.some((edge) => edge.id === edgeId);
  }

  /**
   * Get total edge count
   *
   * @param canvasData - Canvas data
   * @returns Number of edges
   */
  getEdgeCount(canvasData: CanvasData): number {
    return canvasData.edges.length;
  }

  /**
   * Validate edge references (check if connected nodes exist)
   *
   * @param canvasData - Canvas data
   * @returns Array of invalid edge IDs
   */
  validateEdgeReferences(canvasData: CanvasData): string[] {
    const nodeIds = new Set(canvasData.nodes.map((node) => node.id));
    const invalidEdges: string[] = [];

    for (const edge of canvasData.edges) {
      if (!nodeIds.has(edge.fromNode) || !nodeIds.has(edge.toNode)) {
        invalidEdges.push(edge.id);
      }
    }

    return invalidEdges;
  }

  /**
   * Remove orphaned edges (edges pointing to non-existent nodes)
   *
   * @param canvasData - Canvas data (mutated in place)
   * @returns Number of edges removed
   */
  removeOrphanedEdges(canvasData: CanvasData): number {
    const nodeIds = new Set(canvasData.nodes.map((node) => node.id));
    const initialCount = canvasData.edges.length;

    canvasData.edges = canvasData.edges.filter(
      (edge) => nodeIds.has(edge.fromNode) && nodeIds.has(edge.toNode)
    );

    return initialCount - canvasData.edges.length;
  }

  /**
   * Create an edge index map for O(1) lookup
   *
   * @param canvasData - Canvas data
   * @returns Map of edge ID to edge
   */
  createEdgeIndex(canvasData: CanvasData): Map<string, CanvasEdge> {
    const index = new Map<string, CanvasEdge>();
    for (const edge of canvasData.edges) {
      index.set(edge.id, edge);
    }
    return index;
  }

  /**
   * Create adjacency list for graph traversal
   *
   * @param canvasData - Canvas data
   * @returns Adjacency list (nodeId -> connected nodeIds)
   */
  createAdjacencyList(canvasData: CanvasData): Map<string, Set<string>> {
    const adjacency = new Map<string, Set<string>>();

    // Initialize all nodes
    for (const node of canvasData.nodes) {
      adjacency.set(node.id, new Set());
    }

    // Add edges
    for (const edge of canvasData.edges) {
      adjacency.get(edge.fromNode)?.add(edge.toNode);
      adjacency.get(edge.toNode)?.add(edge.fromNode);
    }

    return adjacency;
  }
}
