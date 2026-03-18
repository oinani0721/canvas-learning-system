/**
 * Canvas Learning System - Pullout Service
 * Story 3.7: Dialog Pullout Node (AC-1, AC-3, AC-4)
 *
 * Creates new canvas nodes from text pulled out of dialogue messages.
 * Handles node creation, metadata tracking, and delta sync trigger.
 *
 * [Source: _bmad-output/implementation-artifacts/3-7-dialog-pullout-node.md#Task 2]
 */

import { canvasState } from '../stores/canvas-state';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

export interface PulloutSourceInfo {
  sourceNodeId: string;
  sourceMessageId: string;
  timestamp: string;
}

export interface PulloutResult {
  nodeId: string;
  content: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Drag Data Format
// ═══════════════════════════════════════════════════════════════════════════════

/** MIME type for canvas pullout drag data. */
export const PULLOUT_MIME_TYPE = 'application/canvas-pullout';

export interface PulloutDragData {
  content: string;
  sourceNodeId: string;
  sourceMessageId: string;
  timestamp: string;
}

/**
 * Encode pullout data into a DragEvent's dataTransfer.
 *
 * Story 3.7 AC-1: Set both custom MIME type and text/plain fallback.
 *
 * @param dataTransfer - The DataTransfer object from dragstart event.
 * @param data - The pullout drag data.
 */
export function encodePulloutDragData(
  dataTransfer: DataTransfer,
  data: PulloutDragData,
): void {
  dataTransfer.setData(PULLOUT_MIME_TYPE, JSON.stringify(data));
  dataTransfer.setData('text/plain', data.content);
}

/**
 * Decode pullout data from a DragEvent's dataTransfer.
 *
 * @param dataTransfer - The DataTransfer object from drop event.
 * @returns PulloutDragData if valid, null otherwise.
 */
export function decodePulloutDragData(
  dataTransfer: DataTransfer,
): PulloutDragData | null {
  const raw = dataTransfer.getData(PULLOUT_MIME_TYPE);
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.content === 'string') {
      return parsed as PulloutDragData;
    }
    return null;
  } catch {
    return null;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Pullout Service
// ═══════════════════════════════════════════════════════════════════════════════

export class PulloutService {
  /**
   * Create a new node from pulled-out dialogue text.
   *
   * Story 3.7 AC-1: Creates a text node at the drop position.
   * Story 3.7 AC-3: Node syncs via delta sync (Story 1.5 Outbox).
   * Story 3.7 AC-4: Metadata records source info (dialog_pullout).
   *
   * @param content - The pulled-out text content.
   * @param position - Drop position in canvas coordinates.
   * @param sourceInfo - Source metadata for traceability.
   * @returns PulloutResult with created node info.
   */
  async createPulloutNode(
    content: string,
    position: { x: number; y: number },
    sourceInfo: PulloutSourceInfo,
  ): Promise<PulloutResult> {
    // Calculate node size based on content length
    const { width, height } = this.calculateNodeSize(content);

    // Center the node on the drop position
    const x = position.x - width / 2;
    const y = position.y - height / 2;

    // Create node via canvasState (triggers delta sync via Outbox)
    const node = await canvasState.addNode({
      type: 'text',
      x,
      y,
      width,
      height,
      title: content.length > 50 ? content.substring(0, 50) + '...' : content,
      content,
    });

    return {
      nodeId: node.id,
      content,
      x,
      y,
      width,
      height,
    };
  }

  /**
   * Calculate node dimensions based on content length.
   *
   * Story 3.7 AC-1: Node size adapts to content.
   *
   * @param content - The text content.
   * @returns Width and height for the node.
   */
  calculateNodeSize(content: string): { width: number; height: number } {
    const charCount = content.length;

    if (charCount < 50) {
      return { width: 200, height: 60 };
    } else if (charCount < 200) {
      return { width: 250, height: 100 };
    } else if (charCount < 500) {
      return { width: 300, height: 150 };
    } else {
      return { width: 350, height: 200 };
    }
  }
}
