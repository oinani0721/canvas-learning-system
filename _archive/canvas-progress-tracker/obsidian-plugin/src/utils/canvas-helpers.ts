/**
 * Canvas Helper Utilities
 * Story 13.2: Canvas API集成 - Task 6
 *
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #3: Creating Canvas Nodes)
 * ✅ Verified from specs/data/canvas-node.schema.json
 */

import { TFile, Vault } from 'obsidian';
import {
  CanvasPresetColor,
  CanvasColor,
  isPresetColor,
  isHexColor,
  CANVAS_COLORS,
} from '../types/canvas';

// ============================================================================
// Constants
// ============================================================================

/**
 * Default backup folder name (hidden in Obsidian file tree)
 * Story 13.2: AC 5 - SCP-003 compliance
 */
export const BACKUP_FOLDER = '.canvas_backups';

/**
 * Default node dimensions
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #3)
 */
export const DEFAULT_NODE_DIMENSIONS = {
  TEXT: { width: 250, height: 60 },
  FILE: { width: 400, height: 300 },
  LINK: { width: 400, height: 300 },
  GROUP: { width: 500, height: 400 },
} as const;

/**
 * Canvas file extension
 */
export const CANVAS_EXTENSION = 'canvas';

// ============================================================================
// ID Generation
// ============================================================================

/**
 * Generate unique ID for canvas elements
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #3: "Generate unique ID")
 *
 * Uses Math.random() to generate alphanumeric ID
 *
 * @returns Unique identifier string
 */
export function generateId(): string {
  // ✅ Verified from @obsidian-canvas Skill (Quick Reference #3)
  // "function generateId(): string {
  //   return Math.random().toString(36).substring(2, 15);
  // }"
  return Math.random().toString(36).substring(2, 15);
}

/**
 * Generate node ID with optional prefix
 *
 * @param prefix - Optional prefix for the ID
 * @returns Prefixed unique identifier
 */
export function generateNodeId(prefix?: string): string {
  const id = generateId();
  return prefix ? `${prefix}-${id}` : id;
}

/**
 * Generate edge ID
 *
 * @returns Unique edge identifier
 */
export function generateEdgeId(): string {
  return generateId();
}

// ============================================================================
// File Validation
// ============================================================================

/**
 * Check if a file is a valid Canvas file
 *
 * @param file - The file to check
 * @returns True if the file is a .canvas file
 */
export function isValidCanvasFile(file: TFile): boolean {
  return (
    file instanceof TFile &&
    file.extension.toLowerCase() === CANVAS_EXTENSION
  );
}

/**
 * Check if a path is a Canvas file path
 *
 * @param path - The file path to check
 * @returns True if path ends with .canvas
 */
export function isCanvasPath(path: string): boolean {
  return path.toLowerCase().endsWith(`.${CANVAS_EXTENSION}`);
}

// ============================================================================
// Backup Path Utilities
// ============================================================================

/**
 * Get the canvas backup folder path
 *
 * @param vault - The Obsidian vault
 * @returns Backup folder path
 */
export function getCanvasBackupFolder(vault: Vault): string {
  return BACKUP_FOLDER;
}

/**
 * Format backup file name
 * Format: originalName-YYYYMMDD-HHMMSS.canvas
 *
 * @param originalName - Original canvas file name (without extension)
 * @param timestamp - Backup timestamp
 * @returns Formatted backup file name
 */
export function formatBackupName(originalName: string, timestamp: Date): string {
  const year = timestamp.getFullYear();
  const month = String(timestamp.getMonth() + 1).padStart(2, '0');
  const day = String(timestamp.getDate()).padStart(2, '0');
  const hour = String(timestamp.getHours()).padStart(2, '0');
  const minute = String(timestamp.getMinutes()).padStart(2, '0');
  const second = String(timestamp.getSeconds()).padStart(2, '0');

  return `${originalName}-${year}${month}${day}-${hour}${minute}${second}.canvas`;
}

/**
 * Parse backup timestamp from backup file name
 *
 * @param fileName - Backup file name
 * @returns Parsed Date or null if invalid format
 */
export function parseBackupTimestamp(fileName: string): Date | null {
  // Match format: originalName-YYYYMMDD-HHMMSS.canvas
  const match = fileName.match(/-(\d{8})-(\d{6})\.canvas$/);
  if (!match) return null;

  const dateStr = match[1]; // YYYYMMDD
  const timeStr = match[2]; // HHMMSS

  const year = parseInt(dateStr.substring(0, 4), 10);
  const month = parseInt(dateStr.substring(4, 6), 10) - 1;
  const day = parseInt(dateStr.substring(6, 8), 10);
  const hour = parseInt(timeStr.substring(0, 2), 10);
  const minute = parseInt(timeStr.substring(2, 4), 10);
  const second = parseInt(timeStr.substring(4, 6), 10);

  // Validate parsed values
  if (
    isNaN(year) ||
    isNaN(month) ||
    isNaN(day) ||
    isNaN(hour) ||
    isNaN(minute) ||
    isNaN(second)
  ) {
    return null;
  }

  return new Date(year, month, day, hour, minute, second);
}

/**
 * Extract original file name from backup file name
 *
 * @param backupFileName - Backup file name
 * @returns Original file name or null if invalid format
 */
export function extractOriginalName(backupFileName: string): string | null {
  // Match format: originalName-YYYYMMDD-HHMMSS.canvas
  const match = backupFileName.match(/^(.+)-\d{8}-\d{6}\.canvas$/);
  return match ? match[1] : null;
}

// ============================================================================
// Color Utilities
// ============================================================================

/**
 * Get color name from preset color code
 *
 * @param colorCode - Preset color code ("1"-"6")
 * @returns Color name or undefined
 */
export function getColorName(colorCode: CanvasPresetColor): string {
  return CANVAS_COLORS[colorCode];
}

/**
 * Validate and normalize canvas color
 *
 * @param color - Color to validate
 * @returns Normalized color or undefined if invalid
 */
export function normalizeColor(color: string | undefined): CanvasColor | undefined {
  if (!color) return undefined;

  if (isPresetColor(color)) {
    return color;
  }

  // Normalize hex color to uppercase
  if (isHexColor(color)) {
    return color.toUpperCase() as CanvasColor;
  }

  // Try to parse as hex without #
  if (/^[0-9A-Fa-f]{6}$/.test(color)) {
    return `#${color.toUpperCase()}` as CanvasColor;
  }

  return undefined;
}

// ============================================================================
// Coordinate Utilities
// ============================================================================

/**
 * Calculate center point of a node
 *
 * @param x - Node X coordinate (top-left)
 * @param y - Node Y coordinate (top-left)
 * @param width - Node width
 * @param height - Node height
 * @returns Center coordinates
 */
export function getNodeCenter(
  x: number,
  y: number,
  width: number,
  height: number
): { x: number; y: number } {
  return {
    x: x + width / 2,
    y: y + height / 2,
  };
}

/**
 * Check if a point is within a node's bounds
 *
 * @param pointX - Point X coordinate
 * @param pointY - Point Y coordinate
 * @param nodeX - Node X coordinate
 * @param nodeY - Node Y coordinate
 * @param nodeWidth - Node width
 * @param nodeHeight - Node height
 * @returns True if point is within node bounds
 */
export function isPointInNode(
  pointX: number,
  pointY: number,
  nodeX: number,
  nodeY: number,
  nodeWidth: number,
  nodeHeight: number
): boolean {
  return (
    pointX >= nodeX &&
    pointX <= nodeX + nodeWidth &&
    pointY >= nodeY &&
    pointY <= nodeY + nodeHeight
  );
}

/**
 * Check if two nodes overlap
 *
 * @param node1 - First node bounds {x, y, width, height}
 * @param node2 - Second node bounds {x, y, width, height}
 * @returns True if nodes overlap
 */
export function doNodesOverlap(
  node1: { x: number; y: number; width: number; height: number },
  node2: { x: number; y: number; width: number; height: number }
): boolean {
  return !(
    node1.x + node1.width < node2.x ||
    node2.x + node2.width < node1.x ||
    node1.y + node1.height < node2.y ||
    node2.y + node2.height < node1.y
  );
}

// ============================================================================
// JSON Utilities
// ============================================================================

/**
 * Safe JSON parse with error handling
 *
 * @param content - JSON string to parse
 * @returns Parsed object or null on error
 */
export function safeJSONParse<T>(content: string): T | null {
  try {
    return JSON.parse(content) as T;
  } catch {
    return null;
  }
}

/**
 * Format JSON for canvas file (2-space indentation)
 *
 * @param data - Data to stringify
 * @returns Formatted JSON string
 */
export function formatCanvasJSON(data: unknown): string {
  return JSON.stringify(data, null, 2);
}

// ============================================================================
// Deep Clone Utility
// ============================================================================

/**
 * Deep clone canvas data for immutable operations
 *
 * @param data - Data to clone
 * @returns Deep cloned data
 */
export function deepClone<T>(data: T): T {
  return JSON.parse(JSON.stringify(data));
}
