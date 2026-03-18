/**
 * Canvas Learning System - Profile State Store
 * Story 5.3: Learning Profile Panel (AC-1 through AC-6)
 *
 * Svelte 5 reactive store managing the current node's learning profile data.
 *
 * Data flow:
 *   User clicks node -> loadProfile(nodeId)
 *     -> Parallel fetch: summary + tips + weaknesses + qa-highlights
 *     -> $state updates -> LearningProfile.svelte re-renders
 *
 * Integrates with:
 *   - masteryState (Story 5.2): proficiency + FSRS data
 *   - api-client.ts: REST calls to /api/v1/profile/* endpoints
 */

import type {
  ProfileSummary,
  QAHighlightCluster,
  TipItem,
  WeaknessItem,
} from '../types/canvas';
import type { ApiClient } from '../services/api-client';

/** Loading state for the profile panel. */
export type ProfileLoadState = 'idle' | 'loading' | 'loaded' | 'error';

/**
 * Reactive profile state manager.
 * Uses Svelte 5 $state rune for fine-grained reactivity.
 */
class ProfileState {
  /** Current node ID being displayed. */
  currentNodeId = $state<string | null>(null);

  /** Loading state. */
  loadState = $state<ProfileLoadState>('idle');

  /** Error message when loadState is 'error'. */
  errorMessage = $state<string>('');

  /** Mastery summary for the profile header. */
  summary = $state<ProfileSummary | null>(null);

  /** Tips annotations. */
  tips = $state<TipItem[]>(new Array<TipItem>());

  /** Weakness patterns (positive framing). */
  weaknesses = $state<WeaknessItem[]>(new Array<WeaknessItem>());

  /** QA highlight clusters. */
  qaClusters = $state<QAHighlightCluster[]>(new Array<QAHighlightCluster>());

  /** API client reference. */
  private apiClient: ApiClient | null = null;

  /**
   * Initialize with an API client reference.
   * Called once during plugin setup.
   */
  init(apiClient: ApiClient): void {
    this.apiClient = apiClient;
  }

  /**
   * Load the complete learning profile for a node.
   * Fetches all 4 profile sections in parallel for speed.
   * If the node ID hasn't changed, skip reload (cache hit).
   *
   * @param nodeId - The node to load the profile for.
   * @param forceReload - Force reload even if same nodeId.
   */
  async loadProfile(nodeId: string, forceReload = false): Promise<void> {
    if (!this.apiClient) {
      this.loadState = 'error';
      this.errorMessage = 'API client not initialized';
      return;
    }

    // Skip reload if same node and already loaded
    if (
      !forceReload &&
      this.currentNodeId === nodeId &&
      this.loadState === 'loaded'
    ) {
      return;
    }

    this.currentNodeId = nodeId;
    this.loadState = 'loading';
    this.errorMessage = '';

    try {
      // Parallel fetch all profile sections
      const [summaryResult, tipsResult, weaknessResult, qaResult] =
        await Promise.all([
          this.apiClient.getProfileSummary(nodeId),
          this.apiClient.getProfileTips(nodeId),
          this.apiClient.getProfileWeaknesses(nodeId),
          this.apiClient.getProfileQAHighlights(nodeId),
        ]);

      this.summary = summaryResult;
      this.tips = tipsResult.tips;
      this.weaknesses = weaknessResult.weaknesses;
      this.qaClusters = qaResult.clusters;
      this.loadState = 'loaded';
    } catch (err) {
      this.loadState = 'error';
      this.errorMessage =
        err instanceof Error ? err.message : 'Failed to load profile';
      console.warn(
        `[Canvas Learning] Profile load failed for "${nodeId}":`,
        err,
      );
    }
  }

  /**
   * Clear profile data (e.g., when navigating away from a node).
   */
  clear(): void {
    this.currentNodeId = null;
    this.loadState = 'idle';
    this.errorMessage = '';
    this.summary = null;
    this.tips = new Array<TipItem>();
    this.weaknesses = new Array<WeaknessItem>();
    this.qaClusters = new Array<QAHighlightCluster>();
  }
}

/** Singleton profile state store. */
export const profileState = new ProfileState();
