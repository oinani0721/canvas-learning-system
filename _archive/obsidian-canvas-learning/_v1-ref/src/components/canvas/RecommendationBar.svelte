<script lang="ts">
  /**
   * Canvas Learning System - Recommendation Bar Component
   * Story 1.7: Concept-relation recommendation UI (AC-3, AC-4, AC-5)
   *
   * A non-modal bottom bar showing concept relation recommendations.
   * Can be collapsed to a single line or expanded to show details.
   */

  import type { Recommendation } from '../../types/canvas';

  let {
    recommendations,
    onaccept,
    ondismiss,
    onclose,
  }: {
    recommendations: Recommendation[];
    onaccept: (recId: string) => void;
    ondismiss: (recId: string) => void;
    onclose: () => void;
  } = $props();

  let expanded = $state(false);

  function expand() {
    expanded = true;
  }

  function collapse() {
    expanded = false;
  }
</script>

{#if recommendations.length > 0}
  <div class="cl-canvas-recommendation-bar" class:cl-canvas-recommendation-bar--expanded={expanded}>
    {#if !expanded}
      <!-- Collapsed state -->
      <div class="cl-canvas-recommendation-collapsed">
        <span class="cl-canvas-recommendation-badge">{recommendations.length}</span>
        <span>发现 {recommendations.length} 条可能的概念关联</span>
        <button class="cl-canvas-recommendation-expand-btn" onclick={expand}>展开</button>
        <button class="cl-canvas-recommendation-close-btn" onclick={onclose} title="关闭">&times;</button>
      </div>
    {:else}
      <!-- Expanded state -->
      <div class="cl-canvas-recommendation-header">
        <span class="cl-canvas-recommendation-title">概念关联推荐</span>
        <button class="cl-canvas-recommendation-collapse-btn" onclick={collapse}>收起</button>
        <button class="cl-canvas-recommendation-close-btn" onclick={onclose} title="关闭">&times;</button>
      </div>
      <div class="cl-canvas-recommendation-list">
        {#each recommendations as rec (rec.id)}
          <div class="cl-canvas-recommendation-item">
            <span class="cl-canvas-recommendation-nodes">
              {rec.sourceNodeTitle} &#x2194; {rec.targetNodeTitle}
            </span>
            <span class="cl-canvas-recommendation-reason">{rec.reason}</span>
            <button
              class="cl-canvas-recommendation-accept"
              onclick={() => onaccept(rec.id)}
            >
              接受
            </button>
            <button
              class="cl-canvas-recommendation-dismiss"
              onclick={() => ondismiss(rec.id)}
            >
              忽略
            </button>
          </div>
        {/each}
      </div>
    {/if}
  </div>
{/if}

<style>
  .cl-canvas-recommendation-bar {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: var(--background-secondary);
    border-top: 1px solid var(--background-modifier-border);
    z-index: 50;
    font-size: 13px;
    color: var(--text-normal);
  }

  .cl-canvas-recommendation-collapsed {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
  }

  .cl-canvas-recommendation-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 20px;
    height: 20px;
    background: var(--interactive-accent);
    color: var(--text-on-accent);
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    padding: 0 6px;
  }

  .cl-canvas-recommendation-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-bottom: 1px solid var(--background-modifier-border);
  }

  .cl-canvas-recommendation-title {
    flex: 1;
    font-weight: 600;
  }

  .cl-canvas-recommendation-list {
    max-height: 200px;
    overflow-y: auto;
  }

  .cl-canvas-recommendation-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-bottom: 1px solid var(--background-modifier-border-hover, var(--background-modifier-border));
  }

  .cl-canvas-recommendation-item:last-child {
    border-bottom: none;
  }

  .cl-canvas-recommendation-nodes {
    font-weight: 500;
    flex-shrink: 0;
  }

  .cl-canvas-recommendation-reason {
    flex: 1;
    color: var(--text-muted);
    font-size: 12px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .cl-canvas-recommendation-accept,
  .cl-canvas-recommendation-dismiss {
    padding: 2px 8px;
    font-size: 12px;
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
    background: var(--background-primary);
    color: var(--text-normal);
    flex-shrink: 0;
  }

  .cl-canvas-recommendation-accept:hover {
    background: var(--interactive-accent);
    color: var(--text-on-accent);
    border-color: var(--interactive-accent);
  }

  .cl-canvas-recommendation-dismiss:hover {
    background: var(--background-modifier-hover);
  }

  .cl-canvas-recommendation-expand-btn,
  .cl-canvas-recommendation-collapse-btn {
    padding: 2px 8px;
    font-size: 12px;
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
    background: var(--background-primary);
    color: var(--text-normal);
    margin-left: auto;
  }

  .cl-canvas-recommendation-close-btn {
    padding: 2px 6px;
    font-size: 16px;
    line-height: 1;
    border: none;
    background: none;
    color: var(--text-muted);
    cursor: pointer;
  }

  .cl-canvas-recommendation-close-btn:hover {
    color: var(--text-normal);
  }
</style>
