/**
 * Canvas Node API
 * Story 13.2: Canvas API集成 - Task 2
 *
 * Provides node CRUD operations for Canvas files.
 *
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #3: Creating Canvas Nodes)
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #8: Finding and Filtering Nodes)
 * ✅ Verified from specs/api/canvas-api.openapi.yml#addNode, #getNode, #updateNode, #deleteNode
 */

import {
  CanvasData,
  CanvasNode,
  CanvasTextNode,
  CanvasFileNode,
  CanvasLinkNode,
  CanvasGroupNode,
  CanvasColor,
  CreateTextNodeOptions,
  CreateFileNodeOptions,
  CreateLinkNodeOptions,
  CreateGroupNodeOptions,
  isTextNode,
  isFileNode,
  isLinkNode,
  isGroupNode,
} from '../types/canvas';
import {
  generateId,
  DEFAULT_NODE_DIMENSIONS,
} from '../utils/canvas-helpers';

/**
 * Canvas Node API
 * Provides CRUD operations for Canvas nodes.
 *
 * Story 13.2: AC 2, 6
 */
export class CanvasNodeAPI {
  // ============================================================================
  // Node ID Generation
  // ============================================================================

  /**
   * Generate unique node ID
   * ✅ Verified from @obsidian-canvas Skill (Quick Reference #3)
   * "function generateId(): string {
   *   return Math.random().toString(36).substring(2, 15);
   * }"
   *
   * @returns Unique node ID
   */
  generateNodeId(): string {
    return generateId();
  }

  // ============================================================================
  // Create Operations
  // ============================================================================

  /**
   * Create a text node
   * ✅ Verified from @obsidian-canvas Skill (Quick Reference #3: createTextNode)
   *
   * @param x - X coordinate
   * @param y - Y coordinate
   * @param text - Markdown text content
   * @param options - Optional node properties
   * @returns Created text node
   */
  createTextNode(
    x: number,
    y: number,
    text: string,
    options?: CreateTextNodeOptions
  ): CanvasTextNode {
    // ✅ Verified from @obsidian-canvas Skill (Quick Reference #3)
    return {
      id: this.generateNodeId(),
      type: 'text',
      x,
      y,
      width: options?.width ?? DEFAULT_NODE_DIMENSIONS.TEXT.width,
      height: options?.height ?? DEFAULT_NODE_DIMENSIONS.TEXT.height,
      text,
      color: options?.color,
    };
  }

  /**
   * Create a file node
   * ✅ Verified from @obsidian-canvas Skill (Quick Reference #3: createFileNode)
   *
   * @param x - X coordinate
   * @param y - Y coordinate
   * @param filePath - Path to vault file
   * @param options - Optional node properties
   * @returns Created file node
   */
  createFileNode(
    x: number,
    y: number,
    filePath: string,
    options?: CreateFileNodeOptions
  ): CanvasFileNode {
    // ✅ Verified from @obsidian-canvas Skill (Quick Reference #3)
    return {
      id: this.generateNodeId(),
      type: 'file',
      x,
      y,
      width: options?.width ?? DEFAULT_NODE_DIMENSIONS.FILE.width,
      height: options?.height ?? DEFAULT_NODE_DIMENSIONS.FILE.height,
      file: filePath,
      subpath: options?.subpath,
      color: options?.color,
    };
  }

  /**
   * Create a link node
   * ✅ Verified from @obsidian-canvas Skill (Quick Reference #3: createLinkNode)
   *
   * @param x - X coordinate
   * @param y - Y coordinate
   * @param url - External URL
   * @param options - Optional node properties
   * @returns Created link node
   */
  createLinkNode(
    x: number,
    y: number,
    url: string,
    options?: CreateLinkNodeOptions
  ): CanvasLinkNode {
    // ✅ Verified from @obsidian-canvas Skill (Quick Reference #3)
    return {
      id: this.generateNodeId(),
      type: 'link',
      x,
      y,
      width: options?.width ?? DEFAULT_NODE_DIMENSIONS.LINK.width,
      height: options?.height ?? DEFAULT_NODE_DIMENSIONS.LINK.height,
      url,
      color: options?.color,
    };
  }

  /**
   * Create a group node
   * ✅ Verified from @obsidian-canvas Skill (Quick Reference #3: createGroupNode)
   *
   * @param x - X coordinate
   * @param y - Y coordinate
   * @param width - Group width
   * @param height - Group height
   * @param options - Optional node properties
   * @returns Created group node
   */
  createGroupNode(
    x: number,
    y: number,
    width: number,
    height: number,
    options?: CreateGroupNodeOptions
  ): CanvasGroupNode {
    // ✅ Verified from @obsidian-canvas Skill (Quick Reference #3)
    return {
      id: this.generateNodeId(),
      type: 'group',
      x,
      y,
      width: width || DEFAULT_NODE_DIMENSIONS.GROUP.width,
      height: height || DEFAULT_NODE_DIMENSIONS.GROUP.height,
      label: options?.label,
      background: options?.background,
      backgroundStyle: options?.backgroundStyle,
      color: options?.color,
    };
  }

  /**
   * Create a node of any type
   *
   * @param type - Node type
   * @param x - X coordinate
   * @param y - Y coordinate
   * @param content - Content (text, file path, or URL)
   * @param options - Type-specific options
   * @returns Created node
   */
  createNode(
    type: 'text',
    x: number,
    y: number,
    content: string,
    options?: CreateTextNodeOptions
  ): CanvasTextNode;
  createNode(
    type: 'file',
    x: number,
    y: number,
    content: string,
    options?: CreateFileNodeOptions
  ): CanvasFileNode;
  createNode(
    type: 'link',
    x: number,
    y: number,
    content: string,
    options?: CreateLinkNodeOptions
  ): CanvasLinkNode;
  createNode(
    type: 'group',
    x: number,
    y: number,
    content: string,
    options?: CreateGroupNodeOptions & { width?: number; height?: number }
  ): CanvasGroupNode;
  createNode(
    type: string,
    x: number,
    y: number,
    content: string,
    options?: Record<string, unknown>
  ): CanvasNode {
    switch (type) {
      case 'text':
        return this.createTextNode(x, y, content, options as CreateTextNodeOptions);
      case 'file':
        return this.createFileNode(x, y, content, options as CreateFileNodeOptions);
      case 'link':
        return this.createLinkNode(x, y, content, options as CreateLinkNodeOptions);
      case 'group':
        const groupOpts = options as CreateGroupNodeOptions & {
          width?: number;
          height?: number;
        };
        return this.createGroupNode(
          x,
          y,
          groupOpts?.width ?? DEFAULT_NODE_DIMENSIONS.GROUP.width,
          groupOpts?.height ?? DEFAULT_NODE_DIMENSIONS.GROUP.height,
          groupOpts
        );
      default:
        throw new Error(`Unknown node type: ${type}`);
    }
  }

  // ============================================================================
  // Read Operations
  // ============================================================================

  /**
   * Get node by ID
   * Story 13.2: AC 2 - getNodeById
   *
   * @param canvasData - Canvas data
   * @param nodeId - Node ID to find
   * @returns Node or null if not found
   */
  getNodeById(canvasData: CanvasData, nodeId: string): CanvasNode | null {
    return canvasData.nodes.find((node) => node.id === nodeId) ?? null;
  }

  /**
   * Get nodes by color
   * ✅ Verified from @obsidian-canvas Skill (Quick Reference #8: getNodesByColor)
   *
   * @param canvasData - Canvas data
   * @param color - Color to filter by
   * @returns Array of nodes with matching color
   */
  getNodesByColor(canvasData: CanvasData, color: CanvasColor): CanvasNode[] {
    // ✅ Verified from @obsidian-canvas Skill (Quick Reference #8)
    // "return canvasData.nodes.filter(node => node.color === color);"
    return canvasData.nodes.filter((node) => node.color === color);
  }

  /**
   * Get nodes within a rectangular area
   * ✅ Verified from @obsidian-canvas Skill (Quick Reference #8: getNodesInArea)
   *
   * @param canvasData - Canvas data
   * @param x - Area X coordinate
   * @param y - Area Y coordinate
   * @param width - Area width
   * @param height - Area height
   * @returns Nodes within the area
   */
  getNodesInArea(
    canvasData: CanvasData,
    x: number,
    y: number,
    width: number,
    height: number
  ): CanvasNode[] {
    // ✅ Verified from @obsidian-canvas Skill (Quick Reference #8)
    return canvasData.nodes.filter((node) => {
      return (
        node.x >= x &&
        node.x <= x + width &&
        node.y >= y &&
        node.y <= y + height
      );
    });
  }

  /**
   * Get all text nodes
   * ✅ Verified from @obsidian-canvas Skill (Quick Reference #8: getTextNodes)
   *
   * @param canvasData - Canvas data
   * @returns Array of text nodes
   */
  getTextNodes(canvasData: CanvasData): CanvasTextNode[] {
    return canvasData.nodes.filter(isTextNode);
  }

  /**
   * Get all file nodes
   * ✅ Verified from @obsidian-canvas Skill (Quick Reference #8: getFileNodes)
   *
   * @param canvasData - Canvas data
   * @returns Array of file nodes
   */
  getFileNodes(canvasData: CanvasData): CanvasFileNode[] {
    return canvasData.nodes.filter(isFileNode);
  }

  /**
   * Get all link nodes
   *
   * @param canvasData - Canvas data
   * @returns Array of link nodes
   */
  getLinkNodes(canvasData: CanvasData): CanvasLinkNode[] {
    return canvasData.nodes.filter(isLinkNode);
  }

  /**
   * Get all group nodes
   *
   * @param canvasData - Canvas data
   * @returns Array of group nodes
   */
  getGroupNodes(canvasData: CanvasData): CanvasGroupNode[] {
    return canvasData.nodes.filter(isGroupNode);
  }

  /**
   * Get nodes by type
   *
   * @param canvasData - Canvas data
   * @param type - Node type
   * @returns Array of nodes of specified type
   */
  getNodesByType(
    canvasData: CanvasData,
    type: 'text'
  ): CanvasTextNode[];
  getNodesByType(
    canvasData: CanvasData,
    type: 'file'
  ): CanvasFileNode[];
  getNodesByType(
    canvasData: CanvasData,
    type: 'link'
  ): CanvasLinkNode[];
  getNodesByType(
    canvasData: CanvasData,
    type: 'group'
  ): CanvasGroupNode[];
  getNodesByType(
    canvasData: CanvasData,
    type: string
  ): CanvasNode[] {
    return canvasData.nodes.filter((node) => node.type === type);
  }

  // ============================================================================
  // Update Operations
  // ============================================================================

  /**
   * Update a node's properties
   * Story 13.2: AC 2 - updateNode
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param nodeId - Node ID to update
   * @param updates - Properties to update
   * @throws Error if node not found
   */
  updateNode(
    canvasData: CanvasData,
    nodeId: string,
    updates: Partial<Omit<CanvasNode, 'id' | 'type'>>
  ): void {
    const nodeIndex = canvasData.nodes.findIndex((node) => node.id === nodeId);
    if (nodeIndex === -1) {
      throw new Error(`Node not found: ${nodeId}`);
    }

    // Merge updates, preserving id and type
    canvasData.nodes[nodeIndex] = {
      ...canvasData.nodes[nodeIndex],
      ...updates,
      id: nodeId, // Ensure ID is not modified
      type: canvasData.nodes[nodeIndex].type, // Ensure type is not modified
    } as CanvasNode;
  }

  /**
   * Update node color
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param nodeId - Node ID
   * @param color - New color
   */
  updateNodeColor(
    canvasData: CanvasData,
    nodeId: string,
    color: CanvasColor | undefined
  ): void {
    this.updateNode(canvasData, nodeId, { color });
  }

  /**
   * Update node position
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param nodeId - Node ID
   * @param x - New X coordinate
   * @param y - New Y coordinate
   */
  updateNodePosition(
    canvasData: CanvasData,
    nodeId: string,
    x: number,
    y: number
  ): void {
    this.updateNode(canvasData, nodeId, { x, y });
  }

  /**
   * Update node size
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param nodeId - Node ID
   * @param width - New width
   * @param height - New height
   */
  updateNodeSize(
    canvasData: CanvasData,
    nodeId: string,
    width: number,
    height: number
  ): void {
    this.updateNode(canvasData, nodeId, { width, height });
  }

  /**
   * Update text node content
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param nodeId - Node ID
   * @param text - New text content
   */
  updateTextNodeContent(
    canvasData: CanvasData,
    nodeId: string,
    text: string
  ): void {
    const node = this.getNodeById(canvasData, nodeId);
    if (!node) {
      throw new Error(`Node not found: ${nodeId}`);
    }
    if (!isTextNode(node)) {
      throw new Error(`Node ${nodeId} is not a text node`);
    }
    this.updateNode(canvasData, nodeId, { text } as Partial<CanvasTextNode>);
  }

  // ============================================================================
  // Delete Operations
  // ============================================================================

  /**
   * Delete a node and its connected edges (cascade delete)
   * Story 13.2: AC 2 - deleteNode with cascade
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param nodeId - Node ID to delete
   * @throws Error if node not found
   */
  deleteNode(canvasData: CanvasData, nodeId: string): void {
    const nodeIndex = canvasData.nodes.findIndex((node) => node.id === nodeId);
    if (nodeIndex === -1) {
      throw new Error(`Node not found: ${nodeId}`);
    }

    // Remove node
    canvasData.nodes.splice(nodeIndex, 1);

    // Cascade delete: Remove all edges connected to this node
    canvasData.edges = canvasData.edges.filter(
      (edge) => edge.fromNode !== nodeId && edge.toNode !== nodeId
    );
  }

  /**
   * Delete multiple nodes and their connected edges
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param nodeIds - Array of node IDs to delete
   */
  deleteNodes(canvasData: CanvasData, nodeIds: string[]): void {
    const nodeIdSet = new Set(nodeIds);

    // Remove nodes
    canvasData.nodes = canvasData.nodes.filter(
      (node) => !nodeIdSet.has(node.id)
    );

    // Cascade delete: Remove all edges connected to deleted nodes
    canvasData.edges = canvasData.edges.filter(
      (edge) => !nodeIdSet.has(edge.fromNode) && !nodeIdSet.has(edge.toNode)
    );
  }

  // ============================================================================
  // Add Operations
  // ============================================================================

  /**
   * Add a node to canvas
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param node - Node to add
   */
  addNode(canvasData: CanvasData, node: CanvasNode): void {
    canvasData.nodes.push(node);
  }

  /**
   * Add multiple nodes to canvas
   *
   * @param canvasData - Canvas data (mutated in place)
   * @param nodes - Nodes to add
   */
  addNodes(canvasData: CanvasData, nodes: CanvasNode[]): void {
    canvasData.nodes.push(...nodes);
  }

  // ============================================================================
  // Utility Methods
  // ============================================================================

  /**
   * Check if node exists
   *
   * @param canvasData - Canvas data
   * @param nodeId - Node ID
   * @returns True if node exists
   */
  nodeExists(canvasData: CanvasData, nodeId: string): boolean {
    return canvasData.nodes.some((node) => node.id === nodeId);
  }

  /**
   * Get total node count
   *
   * @param canvasData - Canvas data
   * @returns Number of nodes
   */
  getNodeCount(canvasData: CanvasData): number {
    return canvasData.nodes.length;
  }

  /**
   * Get node count by type
   *
   * @param canvasData - Canvas data
   * @returns Count object by type
   */
  getNodeCountByType(canvasData: CanvasData): Record<string, number> {
    const counts: Record<string, number> = {
      text: 0,
      file: 0,
      link: 0,
      group: 0,
    };

    for (const node of canvasData.nodes) {
      counts[node.type]++;
    }

    return counts;
  }

  /**
   * Create a node index map for O(1) lookup
   *
   * @param canvasData - Canvas data
   * @returns Map of node ID to node
   */
  createNodeIndex(canvasData: CanvasData): Map<string, CanvasNode> {
    const index = new Map<string, CanvasNode>();
    for (const node of canvasData.nodes) {
      index.set(node.id, node);
    }
    return index;
  }
}
