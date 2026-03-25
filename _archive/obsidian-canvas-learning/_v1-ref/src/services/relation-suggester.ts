/**
 * Canvas Learning System - Relation Suggester
 * Story 3.7: LLM Relation Suggestion for Pullout Nodes (AC-2)
 *
 * After a new node is pulled out from dialogue, calls the backend
 * LLM API to suggest a relationship type between the original node
 * and the new node. Displays a non-modal toast for user acceptance.
 *
 * [Source: _bmad-output/implementation-artifacts/3-7-dialog-pullout-node.md#Task 3]
 */

import { Notice } from 'obsidian';
import { canvasState } from '../stores/canvas-state';
import type { ApiClient } from './api-client';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

export interface RelationSuggestion {
  relationType: string;
  relationLabel: string;
  confidence: number;
  reason: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Relation Suggester
// ═══════════════════════════════════════════════════════════════════════════════

export class RelationSuggester {
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  /**
   * Suggest a relationship between source and new node content.
   *
   * Story 3.7 AC-2: Calls POST /api/v1/suggestions/relation.
   * Non-blocking: 5s timeout on backend, returns null on failure.
   *
   * @param sourceContent - Content of the original (source) node.
   * @param newContent - Content of the new (pulled-out) node.
   * @param sourceNodeId - Source node ID for reference.
   * @returns RelationSuggestion or null if unavailable.
   */
  async suggestRelation(
    sourceContent: string,
    newContent: string,
    sourceNodeId: string,
  ): Promise<RelationSuggestion | null> {
    try {
      const result = await this.apiClient.post<RelationSuggestion>(
        '/api/v1/suggestions/relation',
        {
          sourceContent,
          newContent,
          sourceNodeId,
        },
      );
      return result;
    } catch {
      console.warn('[Canvas Learning] Relation suggestion failed (non-blocking)');
      return null;
    }
  }

  /**
   * Show a non-modal suggestion toast and handle user response.
   *
   * Story 3.7 AC-2: Accept creates an Edge + syncs to backend.
   * Dismiss keeps the node independent.
   *
   * @param suggestion - The relation suggestion from LLM.
   * @param sourceNodeId - ID of the original node.
   * @param sourceNodeTitle - Title of the original node.
   * @param newNodeId - ID of the new pulled-out node.
   */
  showSuggestionToast(
    suggestion: RelationSuggestion,
    sourceNodeId: string,
    sourceNodeTitle: string,
    newNodeId: string,
  ): void {
    if (suggestion.confidence < 0.3) {
      // Low confidence: don't show suggestion
      return;
    }

    const message =
      `Relation: [${sourceNodeTitle}] ${suggestion.relationLabel} ` +
      `(confidence: ${Math.round(suggestion.confidence * 100)}%)` +
      `\nAccept? Click this notice to create the connection.`;

    // Use Obsidian Notice as a non-modal toast (8s duration)
    const notice = new Notice(message, 8000);

    // Add click handler for acceptance
    const noticeEl = (notice as unknown as { noticeEl: HTMLElement }).noticeEl;
    if (noticeEl) {
      noticeEl.style.cursor = 'pointer';

      noticeEl.addEventListener('click', () => {
        this.acceptSuggestion(
          sourceNodeId,
          newNodeId,
          suggestion.relationType,
        );
        notice.hide();
      });
    }
  }

  /**
   * Accept a relation suggestion and create an Edge.
   *
   * Story 3.7 AC-2: Auto-creates Edge + syncs to backend via Outbox.
   *
   * @param sourceNodeId - Source node ID.
   * @param targetNodeId - Target (new) node ID.
   * @param relationType - The edge label/relation type.
   */
  acceptSuggestion(
    sourceNodeId: string,
    targetNodeId: string,
    relationType: string,
  ): void {
    canvasState.addEdge({
      sourceNodeId,
      targetNodeId,
      label: relationType,
    });

    new Notice('Connection created', 2000);
  }
}
