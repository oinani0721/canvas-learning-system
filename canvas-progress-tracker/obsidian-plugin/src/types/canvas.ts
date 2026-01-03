/**
 * Canvas Data Type Definitions
 * Story 13.2: Canvas API集成
 *
 * ✅ Verified from @obsidian-canvas Skill (SKILL.md - Basic Canvas File Structure)
 * ✅ Verified from specs/data/canvas-node.schema.json
 * ✅ Verified from specs/data/canvas-edge.schema.json
 * ✅ Verified from JSON Canvas Spec 1.0 (https://jsoncanvas.org/spec/1.0/)
 */

// ============================================================================
// Canvas Color Types
// ============================================================================

/**
 * Preset colors (strings "1" through "6")
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #6: Canvas Color System)
 */
export type CanvasPresetColor = '1' | '2' | '3' | '4' | '5' | '6';

/**
 * Hex color format
 */
export type CanvasHexColor = `#${string}`;

/**
 * Combined color type - preset or hex
 */
export type CanvasColor = CanvasPresetColor | CanvasHexColor;

/**
 * Canvas color mapping
 * ✅ Verified from menu.ts CANVAS_COLOR_NAMES and canvas_utils.py (权威来源)
 * ✅ 已通过实际 Obsidian Canvas 渲染验证
 */
export const CANVAS_COLORS: Record<CanvasPresetColor, string> = {
  '1': 'Gray',    // 灰色 - 无特殊含义
  '2': 'Green',   // 绿色 - 完全理解 (≥80分)
  '3': 'Purple',  // 紫色 - 似懂非懂 (60-79分)
  '4': 'Red',     // 红色 - 不理解 (<60分)
  '5': 'Blue',    // 蓝色 - AI解释
  '6': 'Yellow',  // 黄色 - 个人理解
} as const;

/**
 * Learning system semantic colors
 * ✅ Verified from menu.ts CANVAS_COLOR_NAMES and canvas_utils.py (权威来源)
 * Project-specific color semantics for Canvas Learning System
 */
export const LEARNING_COLORS = {
  NOT_UNDERSTOOD: '4' as CanvasPresetColor,        // Red - 不理解 (<60分)
  PARTIAL: '3' as CanvasPresetColor,               // Purple - 似懂非懂 (60-79分)
  UNDERSTOOD: '2' as CanvasPresetColor,            // Green - 已理解 (≥80分)
  PERSONAL_UNDERSTANDING: '6' as CanvasPresetColor, // Yellow - 个人理解 (颜色不变)
  AI_EXPLANATION: '5' as CanvasPresetColor,        // Blue - AI解释节点 (评分后变色)
} as const;

// ============================================================================
// Node Types
// ============================================================================

/**
 * Canvas node type
 * ✅ Verified from @obsidian-canvas Skill (SKILL.md - Node Types)
 */
export type CanvasNodeType = 'text' | 'file' | 'link' | 'group';

/**
 * Base node properties shared by all node types
 * ✅ Verified from specs/data/canvas-node.schema.json
 */
export interface CanvasNodeBase {
  /** Unique node identifier */
  id: string;
  /** Node type */
  type: CanvasNodeType;
  /** X coordinate */
  x: number;
  /** Y coordinate */
  y: number;
  /** Node width */
  width: number;
  /** Node height */
  height: number;
  /** Optional color (preset "1"-"6" or hex) */
  color?: CanvasColor;
}

/**
 * Text node - contains Markdown text
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #3: Creating Canvas Nodes)
 */
export interface CanvasTextNode extends CanvasNodeBase {
  type: 'text';
  /** Markdown text content */
  text: string;
}

/**
 * File node - references a vault file
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #3)
 */
export interface CanvasFileNode extends CanvasNodeBase {
  type: 'file';
  /** File path relative to vault */
  file: string;
  /** Optional subpath (e.g., #Section) */
  subpath?: string;
}

/**
 * Link node - external URL
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #3)
 */
export interface CanvasLinkNode extends CanvasNodeBase {
  type: 'link';
  /** External URL */
  url: string;
}

/**
 * Group node - container for other nodes
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #3)
 */
export interface CanvasGroupNode extends CanvasNodeBase {
  type: 'group';
  /** Group label */
  label?: string;
  /** Background image path */
  background?: string;
  /** Background style */
  backgroundStyle?: 'cover' | 'ratio' | 'repeat';
}

/**
 * Union type for all canvas nodes
 */
export type CanvasNode =
  | CanvasTextNode
  | CanvasFileNode
  | CanvasLinkNode
  | CanvasGroupNode;

// ============================================================================
// Edge Types
// ============================================================================

/**
 * Edge connection side
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #5: Creating Edges)
 */
export type CanvasEdgeSide = 'top' | 'right' | 'bottom' | 'left';

/**
 * Edge end style
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #5)
 */
export type CanvasEdgeEnd = 'none' | 'arrow';

/**
 * Canvas edge (connection between nodes)
 * ✅ Verified from specs/data/canvas-edge.schema.json
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #5)
 */
export interface CanvasEdge {
  /** Unique edge identifier */
  id: string;
  /** Source node ID */
  fromNode: string;
  /** Target node ID */
  toNode: string;
  /** Source connection side */
  fromSide?: CanvasEdgeSide;
  /** Target connection side */
  toSide?: CanvasEdgeSide;
  /** Arrow style at target end */
  toEnd?: CanvasEdgeEnd;
  /** Optional edge label */
  label?: string;
  /** Optional edge color */
  color?: CanvasColor;
}

// ============================================================================
// Canvas Data Structure
// ============================================================================

/**
 * Complete Canvas data structure
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #1: Basic Canvas File Structure)
 */
export interface CanvasData {
  /** Array of canvas nodes */
  nodes: CanvasNode[];
  /** Array of canvas edges */
  edges: CanvasEdge[];
}

// ============================================================================
// Backup Types
// ============================================================================

/**
 * Backup information
 * Story 13.2: CanvasBackupManager (AC: 4, 5)
 */
export interface BackupInfo {
  /** Full backup file path */
  path: string;
  /** Original canvas file name */
  originalName: string;
  /** Backup creation timestamp */
  timestamp: Date;
  /** File size in bytes */
  size: number;
}

// ============================================================================
// Node Creation Options
// ============================================================================

/**
 * Options for creating a text node
 */
export interface CreateTextNodeOptions {
  width?: number;
  height?: number;
  color?: CanvasColor;
}

/**
 * Options for creating a file node
 */
export interface CreateFileNodeOptions {
  width?: number;
  height?: number;
  subpath?: string;
  color?: CanvasColor;
}

/**
 * Options for creating a link node
 */
export interface CreateLinkNodeOptions {
  width?: number;
  height?: number;
  color?: CanvasColor;
}

/**
 * Options for creating a group node
 */
export interface CreateGroupNodeOptions {
  label?: string;
  background?: string;
  backgroundStyle?: 'cover' | 'ratio' | 'repeat';
  color?: CanvasColor;
}

/**
 * Options for creating an edge
 */
export interface CreateEdgeOptions {
  fromSide?: CanvasEdgeSide;
  toSide?: CanvasEdgeSide;
  toEnd?: CanvasEdgeEnd;
  label?: string;
  color?: CanvasColor;
}

// ============================================================================
// Type Guards
// ============================================================================

/**
 * Type guard for text node
 */
export function isTextNode(node: CanvasNode): node is CanvasTextNode {
  return node.type === 'text';
}

/**
 * Type guard for file node
 */
export function isFileNode(node: CanvasNode): node is CanvasFileNode {
  return node.type === 'file';
}

/**
 * Type guard for link node
 */
export function isLinkNode(node: CanvasNode): node is CanvasLinkNode {
  return node.type === 'link';
}

/**
 * Type guard for group node
 */
export function isGroupNode(node: CanvasNode): node is CanvasGroupNode {
  return node.type === 'group';
}

/**
 * Type guard for preset color
 */
export function isPresetColor(color: string): color is CanvasPresetColor {
  return ['1', '2', '3', '4', '5', '6'].includes(color);
}

/**
 * Type guard for hex color
 */
export function isHexColor(color: string): color is CanvasHexColor {
  return /^#[0-9A-Fa-f]{6}$/.test(color);
}

/**
 * Type guard for valid canvas color
 */
export function isValidCanvasColor(color: string): color is CanvasColor {
  return isPresetColor(color) || isHexColor(color);
}
