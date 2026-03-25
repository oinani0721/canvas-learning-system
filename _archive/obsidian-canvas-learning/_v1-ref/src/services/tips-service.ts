/**
 * Canvas Learning System - Tips Service
 * Story 3.6: Tips Writing Logic (AC-2)
 *
 * Handles saving user-annotated tips to the backend Graphiti store.
 * Called when the user selects text in a chat message and clicks "Write Tips".
 *
 * [Source: _bmad-output/implementation-artifacts/3-6-tips-annotation-error-archiving.md#Task 2]
 */

import type { ApiClient } from './api-client';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

export type TipTag = 'important' | 'confused' | 'inspiration' | 'review';

export interface TipData {
  content: string;
  title: string;
  tags: TipTag[];
  nodeId: string;
  sourceTimestamp: string;
}

export interface SaveTipResult {
  tipId: string;
  saved: boolean;
  status: string;
  message: string;
}

// Tag display configuration
export const TIP_TAG_CONFIG: Record<TipTag, { label: string; color: string }> = {
  important: { label: '重要', color: 'var(--color-red)' },
  confused: { label: '困惑', color: 'var(--color-yellow)' },
  inspiration: { label: '灵感', color: 'var(--color-green)' },
  review: { label: '待复习', color: 'var(--color-blue)' },
};

// ═══════════════════════════════════════════════════════════════════════════════
// Tips Service
// ═══════════════════════════════════════════════════════════════════════════════

export class TipsService {
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  /**
   * Save a tip annotation to Graphiti via the backend.
   *
   * Story 3.6 AC-2: POST to /api/v1/tips with tip data.
   *
   * @param tip - The tip data to save.
   * @returns SaveTipResult with tipId and status.
   */
  async saveTip(tip: TipData): Promise<SaveTipResult> {
    try {
      const result = await this.apiClient.post<SaveTipResult>(
        '/api/v1/tips',
        {
          content: tip.content,
          title: tip.title,
          tags: tip.tags,
          nodeId: tip.nodeId,
          sourceTimestamp: tip.sourceTimestamp,
        },
      );
      return result;
    } catch (err) {
      console.warn('[Canvas Learning] Failed to save tip:', err);
      return {
        tipId: '',
        saved: false,
        status: 'error',
        message: err instanceof Error ? err.message : 'Unknown error',
      };
    }
  }
}
