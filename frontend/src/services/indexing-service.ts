/**
 * IndexingService — Async OCR processing queue
 * Story 1-6: Submits image nodes for Vision API extraction
 *
 * Features:
 * - Queue deduplication (prevents duplicate submissions for same nodeId)
 * - AbortController support for cleanup
 * - Updates Dexie node with OCR results + indexStatus
 * - Retry via 'image-retry-index' custom event from ImageNode
 */
import { db } from './dexie-db';
import { ApiClient } from './api-client';

const MAX_IMAGE_SIZE = 10 * 1024 * 1024; // 10MB

export class IndexingService {
  private apiClient: ApiClient;
  private processing: Set<string> = new Set();
  private abortControllers: Map<string, AbortController> = new Map();

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
    // Listen for retry events from ImageNode
    this.handleRetry = this.handleRetry.bind(this);
    window.addEventListener('image-retry-index', this.handleRetry as EventListener);
  }

  /** Clean up event listeners. */
  destroy() {
    window.removeEventListener('image-retry-index', this.handleRetry as EventListener);
    // Abort all in-flight requests
    for (const controller of this.abortControllers.values()) {
      controller.abort();
    }
    this.abortControllers.clear();
    this.processing.clear();
  }

  /**
   * Submit an image node for OCR indexing.
   * Deduplicates by nodeId — if already processing, skips.
   */
  async submitForIndexing(nodeId: string): Promise<void> {
    if (this.processing.has(nodeId)) return;

    const node = await db.canvas_nodes.get(nodeId);
    if (!node || !node.imageData) return;

    // Validate size
    const sizeEstimate = node.imageData.length * 0.75; // base64 overhead
    if (sizeEstimate > MAX_IMAGE_SIZE) {
      await db.canvas_nodes.update(nodeId, {
        indexStatus: 'failed',
        ocrError: `Image too large (${Math.round(sizeEstimate / 1024 / 1024)}MB > 10MB limit)`,
        updatedAt: new Date().toISOString(),
      });
      return;
    }

    this.processing.add(nodeId);

    // Set indexing status
    await db.canvas_nodes.update(nodeId, {
      indexStatus: 'indexing',
      ocrError: undefined,
      updatedAt: new Date().toISOString(),
    });

    const controller = new AbortController();
    this.abortControllers.set(nodeId, controller);

    try {
      const result = await this.apiClient.indexImage(
        nodeId,
        node.imageData,
        controller.signal,
      );

      // Update Dexie with OCR results
      await db.canvas_nodes.update(nodeId, {
        indexStatus: 'indexed',
        ocrText: result.ocrText,
        ocrSummary: result.summary,
        ocrConcepts: result.concepts,
        ocrError: undefined,
        updatedAt: new Date().toISOString(),
      });

      // Write to sync outbox for Neo4j (exclude imageData)
      await db.sync_outbox.add({
        entityType: 'node',
        entityId: nodeId,
        operation: 'update',
        payload: {
          id: nodeId,
          canvasId: node.canvasId,
          indexStatus: 'indexed',
          ocrText: result.ocrText,
          ocrSummary: result.summary,
          ocrConcepts: result.concepts,
        },
        createdAt: new Date().toISOString(),
      });
    } catch (err) {
      if (controller.signal.aborted) return;

      const errorMsg = err instanceof Error ? err.message : String(err);
      await db.canvas_nodes.update(nodeId, {
        indexStatus: 'failed',
        ocrError: errorMsg,
        updatedAt: new Date().toISOString(),
      });
      console.warn(`[IndexingService] OCR failed for ${nodeId}:`, errorMsg);
    } finally {
      this.processing.delete(nodeId);
      this.abortControllers.delete(nodeId);
    }
  }

  /** Handle retry event from ImageNode component. */
  private handleRetry(event: Event) {
    const detail = (event as CustomEvent).detail;
    if (detail?.nodeId) {
      this.submitForIndexing(detail.nodeId);
    }
  }

  /** Check if a node is currently being processed. */
  isProcessing(nodeId: string): boolean {
    return this.processing.has(nodeId);
  }
}
