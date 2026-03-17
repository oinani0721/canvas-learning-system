/**
 * Canvas Learning System - Canvas Math Utilities
 * Story 1.4: Viewport transforms, bezier curves, culling (AC-5, AC-8)
 *
 * Pure functions — no side effects, no DOM access.
 */

import type { CanvasNodeData, Point, Rect, Viewport } from '../types/canvas';

// ─── Viewport coordinate transforms ────────────────────────────────────────

/**
 * Convert screen (pixel) coordinates to canvas coordinates.
 * Inverse of the CSS transform: translate(vp.x, vp.y) scale(vp.zoom)
 */
export function screenToCanvas(
  screenX: number,
  screenY: number,
  vp: Viewport,
): Point {
  return {
    x: (screenX - vp.x) / vp.zoom,
    y: (screenY - vp.y) / vp.zoom,
  };
}

/**
 * Convert canvas coordinates to screen coordinates.
 */
export function canvasToScreen(
  canvasX: number,
  canvasY: number,
  vp: Viewport,
): Point {
  return {
    x: canvasX * vp.zoom + vp.x,
    y: canvasY * vp.zoom + vp.y,
  };
}

/**
 * Calculate a new viewport after zooming, keeping the mouse position fixed.
 * @param vp      Current viewport
 * @param delta   Scroll delta (positive = zoom out, negative = zoom in)
 * @param mouseX  Mouse screen-X within the viewport container
 * @param mouseY  Mouse screen-Y within the viewport container
 */
export function zoomViewport(
  vp: Viewport,
  delta: number,
  mouseX: number,
  mouseY: number,
): Viewport {
  const zoomFactor = delta > 0 ? 0.9 : 1.1;
  const newZoom = Math.max(0.1, Math.min(5.0, vp.zoom * zoomFactor));

  // Keep the point under the mouse fixed:
  // screenPos = canvasPos * zoom + translate
  // canvasPos = (screenPos - translate) / zoom
  // After zoom change, new translate = screenPos - canvasPos * newZoom
  const canvasX = (mouseX - vp.x) / vp.zoom;
  const canvasY = (mouseY - vp.y) / vp.zoom;

  return {
    x: mouseX - canvasX * newZoom,
    y: mouseY - canvasY * newZoom,
    zoom: newZoom,
  };
}

// ─── Viewport culling ───────────────────────────────────────────────────────

/**
 * Compute the visible canvas-coordinate rectangle from the viewport.
 * @param vp              Current viewport transform
 * @param containerWidth  Pixel width of the viewport container element
 * @param containerHeight Pixel height of the viewport container element
 */
export function getVisibleRect(
  vp: Viewport,
  containerWidth: number,
  containerHeight: number,
): Rect {
  const topLeft = screenToCanvas(0, 0, vp);
  const bottomRight = screenToCanvas(containerWidth, containerHeight, vp);
  return {
    x: topLeft.x,
    y: topLeft.y,
    width: bottomRight.x - topLeft.x,
    height: bottomRight.y - topLeft.y,
  };
}

/** Margin (in canvas units) added to culling rect to avoid pop-in. */
const CULL_MARGIN = 100;

/**
 * Test whether a node is within (or near) the visible rectangle.
 */
export function isNodeVisible(node: CanvasNodeData, visible: Rect): boolean {
  return (
    node.x + node.width >= visible.x - CULL_MARGIN &&
    node.x <= visible.x + visible.width + CULL_MARGIN &&
    node.y + node.height >= visible.y - CULL_MARGIN &&
    node.y <= visible.y + visible.height + CULL_MARGIN
  );
}

/**
 * Test whether an edge is visible by checking if either endpoint node is visible.
 */
export function isEdgeVisible(
  sourceNode: CanvasNodeData | undefined,
  targetNode: CanvasNodeData | undefined,
  visible: Rect,
): boolean {
  if (!sourceNode || !targetNode) return false;
  return isNodeVisible(sourceNode, visible) || isNodeVisible(targetNode, visible);
}

// ─── Bezier curve path calculation ──────────────────────────────────────────

/**
 * Find the closest edge point on a node rectangle to a target point.
 * Returns the point on the node boundary closest to `target`.
 */
export function getNodeEdgePoint(node: CanvasNodeData, target: Point): Point {
  const cx = node.x + node.width / 2;
  const cy = node.y + node.height / 2;
  const dx = target.x - cx;
  const dy = target.y - cy;

  if (dx === 0 && dy === 0) {
    return { x: cx, y: cy };
  }

  const halfW = node.width / 2;
  const halfH = node.height / 2;

  // Compute intersection with the node rectangle edges
  const absDx = Math.abs(dx);
  const absDy = Math.abs(dy);

  let t: number;
  if (absDx * halfH > absDy * halfW) {
    // Intersects left or right edge
    t = halfW / absDx;
  } else {
    // Intersects top or bottom edge
    t = halfH / absDy;
  }

  return {
    x: cx + dx * t,
    y: cy + dy * t,
  };
}

/**
 * Calculate a cubic bezier SVG path between two nodes.
 * Uses adaptive control point distance: short connections are nearly straight,
 * long connections have more pronounced curves.
 */
export function calculateBezierPath(
  sourceNode: CanvasNodeData,
  targetNode: CanvasNodeData,
): string {
  const sourceCenter: Point = {
    x: sourceNode.x + sourceNode.width / 2,
    y: sourceNode.y + sourceNode.height / 2,
  };
  const targetCenter: Point = {
    x: targetNode.x + targetNode.width / 2,
    y: targetNode.y + targetNode.height / 2,
  };

  const start = getNodeEdgePoint(sourceNode, targetCenter);
  const end = getNodeEdgePoint(targetNode, sourceCenter);

  // Adaptive control point offset
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const dist = Math.sqrt(dx * dx + dy * dy);
  const offset = Math.min(dist * 0.4, 120);

  // Determine primary direction for control points
  const absDx = Math.abs(dx);
  const absDy = Math.abs(dy);

  let cp1: Point;
  let cp2: Point;

  if (absDx >= absDy) {
    // Horizontal-dominant: control points extend horizontally
    cp1 = { x: start.x + Math.sign(dx) * offset, y: start.y };
    cp2 = { x: end.x - Math.sign(dx) * offset, y: end.y };
  } else {
    // Vertical-dominant: control points extend vertically
    cp1 = { x: start.x, y: start.y + Math.sign(dy) * offset };
    cp2 = { x: end.x, y: end.y - Math.sign(dy) * offset };
  }

  return `M ${start.x} ${start.y} C ${cp1.x} ${cp1.y}, ${cp2.x} ${cp2.y}, ${end.x} ${end.y}`;
}

/**
 * Calculate the midpoint of a bezier path (for label positioning).
 * Approximates using the average of the two control points.
 */
export function getBezierMidpoint(
  sourceNode: CanvasNodeData,
  targetNode: CanvasNodeData,
): Point {
  const sourceCenter: Point = {
    x: sourceNode.x + sourceNode.width / 2,
    y: sourceNode.y + sourceNode.height / 2,
  };
  const targetCenter: Point = {
    x: targetNode.x + targetNode.width / 2,
    y: targetNode.y + targetNode.height / 2,
  };

  const start = getNodeEdgePoint(sourceNode, targetCenter);
  const end = getNodeEdgePoint(targetNode, sourceCenter);

  // Midpoint of the bezier curve (t=0.5 approximation)
  return {
    x: (start.x + end.x) / 2,
    y: (start.y + end.y) / 2,
  };
}

/**
 * Calculate arrowhead points at the end of an edge.
 * Returns a "points" string for an SVG <polygon>.
 */
export function calculateArrowPoints(
  sourceNode: CanvasNodeData,
  targetNode: CanvasNodeData,
): string {
  const sourceCenter: Point = {
    x: sourceNode.x + sourceNode.width / 2,
    y: sourceNode.y + sourceNode.height / 2,
  };
  const end = getNodeEdgePoint(targetNode, sourceCenter);

  // Direction from source toward target
  const dx = end.x - sourceCenter.x;
  const dy = end.y - sourceCenter.y;
  const len = Math.sqrt(dx * dx + dy * dy);

  if (len === 0) return '';

  const ux = dx / len;
  const uy = dy / len;

  // Arrow parameters
  const arrowLen = 10;
  const arrowWidth = 5;

  // Tip is at `end`, base is `arrowLen` back along the direction
  const baseX = end.x - ux * arrowLen;
  const baseY = end.y - uy * arrowLen;

  // Perpendicular
  const px = -uy * arrowWidth;
  const py = ux * arrowWidth;

  return `${end.x},${end.y} ${baseX + px},${baseY + py} ${baseX - px},${baseY - py}`;
}

/**
 * Test whether a point is inside a rectangle.
 */
export function pointInRect(p: Point, r: Rect): boolean {
  return p.x >= r.x && p.x <= r.x + r.width && p.y >= r.y && p.y <= r.y + r.height;
}

/**
 * Test whether two rectangles overlap (for box-select).
 */
export function rectsOverlap(a: Rect, b: Rect): boolean {
  return (
    a.x < b.x + b.width &&
    a.x + a.width > b.x &&
    a.y < b.y + b.height &&
    a.y + a.height > b.y
  );
}

/**
 * Generate a UUID using the Web Crypto API (available in Electron).
 */
export function generateId(): string {
  return crypto.randomUUID();
}

/**
 * Get current ISO timestamp.
 */
export function now(): string {
  return new Date().toISOString();
}
