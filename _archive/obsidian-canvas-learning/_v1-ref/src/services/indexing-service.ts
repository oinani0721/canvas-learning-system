/**
 * Canvas Learning System - Indexing Service
 * Story 1.6: Async image OCR index management (AC-4, AC-5, AC-7)
 *
 * Manages background OCR requests for image nodes.
 * Does not block the UI — users can continue working while OCR runs.
 */

import { Notice } from 'obsidian';
import type { ApiClient } from './api-client';
import { canvasState } from '../stores/canvas-state';
import { db } from './dexie-db';

export class IndexingService {
  private pendingQueue: Map<string, AbortController> = new Map();
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  /**
   * Request OCR indexing for an image node.
   * Skips if a request for the same nodeId is already in progress.
   */
  async requestImageIndex(nodeId: string, imageData: string): Promise<void> {
    if (this.pendingQueue.has(nodeId)) return;

    const controller = new AbortController();
    this.pendingQueue.set(nodeId, controller);

    try {
      const result = await this.apiClient.indexImage(nodeId, imageData, controller.signal);
      // Success: update IndexedDB node data
      await canvasState.updateNode(nodeId, {
        ocrText: result.ocrText,
        ocrSummary: result.summary,
        ocrConcepts: result.concepts,
        indexStatus: 'indexed',
        ocrError: undefined,
      }, true);
    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') return;
      const message = error instanceof Error ? error.message : 'Unknown error';
      // Failure: update error status
      await canvasState.updateNode(nodeId, {
        indexStatus: 'failed',
        ocrError: message,
      }, true);
      new Notice(`图片索引失败: ${message}`, 5000);
    } finally {
      this.pendingQueue.delete(nodeId);
    }
  }

  /**
   * Retry OCR indexing for a failed image node.
   */
  async retryIndex(nodeId: string): Promise<void> {
    await canvasState.updateNode(nodeId, { indexStatus: 'indexing', ocrError: undefined }, true);
    const node = await db.canvas_nodes.get(nodeId);
    if (node?.imageData) {
      await this.requestImageIndex(nodeId, node.imageData);
    }
  }

  /**
   * Cancel all pending OCR requests. Called on plugin unload.
   */
  cancelAll(): void {
    for (const controller of this.pendingQueue.values()) {
      controller.abort();
    }
    this.pendingQueue.clear();
  }
}
