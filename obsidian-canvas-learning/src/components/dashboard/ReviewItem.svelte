<script lang="ts">
  /**
   * Canvas Learning System - ReviewItem Component
   * Story 5.4: FSRS Review Dashboard (AC-3)
   *
   * Renders a single review node card with urgency indicators.
   * Visual urgency: overdue (red border) > due (yellow) > weak (orange).
   *
   * CSS: cl-dash-review-item-* prefix, Obsidian CSS variables, scoped.
   */

  import type { ReviewNode } from '../../types/canvas';

  interface Props {
    node: ReviewNode;
    onclick?: () => void;
  }

  let { node, onclick }: Props = $props();

  /** Compute relative time for last review. */
  function relativeTime(iso: string | undefined): string {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      const diffMs = Date.now() - d.getTime();
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

      if (diffDays === 0) return '今天';
      if (diffDays === 1) return '昨天';
      if (diffDays < 7) return `${diffDays} 天前`;
      if (diffDays < 30) return `${Math.floor(diffDays / 7)} 周前`;
      return `${Math.floor(diffDays / 30)} 月前`;
    } catch {
      return '';
    }
  }

  /** Get the urgency label for display. */
  function freshnessLabel(freshness: string, overdueDays?: number): string {
    switch (freshness) {
      case 'overdue':
        return overdueDays ? `已逾期 ${overdueDays} 天` : '已逾期';
      case 'due':
        return '建议今天复习';
      case 'stale':
        return '需要加强';
      default:
        return '';
    }
  }

  function handleClick() {
    if (onclick) onclick();
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      if (onclick) onclick();
    }
  }
</script>

<div
  class="cl-dash-review-item"
  class:cl-dash-review-item--overdue={node.freshness === 'overdue'}
  class:cl-dash-review-item--due={node.freshness === 'due'}
  class:cl-dash-review-item--weak={node.freshness === 'stale'}
  onclick={handleClick}
  onkeydown={handleKeyDown}
  role="button"
  tabindex="0"
>
  <div class="cl-dash-review-item-color" style="background: {node.masteryColor}"></div>
  <div class="cl-dash-review-item-content">
    <span class="cl-dash-review-item-name">{node.name}</span>
    <span class="cl-dash-review-item-board">{node.boardName}</span>
  </div>
  <div class="cl-dash-review-item-meta">
    <span class="cl-dash-review-item-freshness">
      {freshnessLabel(node.freshness, node.overdueDays)}
    </span>
    {#if node.lastReviewedAt}
      <span class="cl-dash-review-item-last-review">
        {relativeTime(node.lastReviewedAt)}
      </span>
    {/if}
  </div>
</div>

<style>
  .cl-dash-review-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    background: var(--background-secondary);
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
    transition: border-color 0.15s ease, background 0.15s ease;
    border-left: 3px solid transparent;
  }

  .cl-dash-review-item:hover {
    background: var(--background-modifier-hover);
  }

  .cl-dash-review-item:focus-visible {
    outline: 2px solid var(--interactive-accent);
    outline-offset: 2px;
  }

  .cl-dash-review-item--overdue {
    border-left-color: #dc3545;
  }

  .cl-dash-review-item--due {
    border-left-color: #ffc107;
  }

  .cl-dash-review-item--weak {
    border-left-color: #fd7e14;
  }

  .cl-dash-review-item-color {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .cl-dash-review-item-content {
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex: 1;
    min-width: 0;
  }

  .cl-dash-review-item-name {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-normal);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .cl-dash-review-item-board {
    font-size: 11px;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .cl-dash-review-item-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 2px;
    flex-shrink: 0;
  }

  .cl-dash-review-item-freshness {
    font-size: 11px;
    font-weight: 500;
    padding: 1px 6px;
    border-radius: 3px;
  }

  .cl-dash-review-item--overdue .cl-dash-review-item-freshness {
    background: rgba(220, 53, 69, 0.15);
    color: #dc3545;
  }

  .cl-dash-review-item--due .cl-dash-review-item-freshness {
    background: rgba(255, 193, 7, 0.15);
    color: #b38600;
  }

  .cl-dash-review-item--weak .cl-dash-review-item-freshness {
    background: rgba(253, 126, 20, 0.15);
    color: #fd7e14;
  }

  .cl-dash-review-item-last-review {
    font-size: 10px;
    color: var(--text-faint);
  }
</style>
