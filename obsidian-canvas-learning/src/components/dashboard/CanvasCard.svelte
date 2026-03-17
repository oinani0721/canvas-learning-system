<script lang="ts">
  /**
   * Canvas Learning System - Canvas Card Component
   * Story 1.4: Dashboard board card (AC-7)
   *
   * Displays board name, creation time, and node count.
   */

  import type { CanvasBoard } from '../../types/canvas';
  import { canvasState } from '../../stores/canvas-state';

  let {
    board,
    onselect,
  }: {
    board: CanvasBoard;
    onselect: () => void;
  } = $props();

  // Node count — loaded asynchronously
  let nodeCount = $state(0);

  $effect(() => {
    canvasState.getNodeCount(board.id).then((count) => {
      nodeCount = count;
    });
  });

  function formatDate(iso: string): string {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return iso;
    }
  }

  function handleClick() {
    onselect();
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onselect();
    }
  }
</script>

<div
  class="cl-dash-card"
  onclick={handleClick}
  onkeydown={handleKeyDown}
  role="button"
  tabindex="0"
>
  <div class="cl-dash-card-name">{board.name}</div>
  <div class="cl-dash-card-meta">
    <span class="cl-dash-card-date">{formatDate(board.createdAt)}</span>
    <span class="cl-dash-card-nodes">{nodeCount} 个节点</span>
  </div>
</div>

<style>
  .cl-dash-card {
    padding: 12px 14px;
    background: var(--background-secondary);
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }

  .cl-dash-card:hover {
    border-color: var(--interactive-accent);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  }

  .cl-dash-card:focus-visible {
    outline: 2px solid var(--interactive-accent);
    outline-offset: 2px;
  }

  .cl-dash-card-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-normal);
    margin-bottom: 6px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .cl-dash-card-meta {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: var(--text-muted);
  }
</style>
