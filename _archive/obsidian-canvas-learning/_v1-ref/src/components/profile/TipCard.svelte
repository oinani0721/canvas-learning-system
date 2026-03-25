<script lang="ts">
  /**
   * Canvas Learning System - TipCard Component
   * Story 5.3: Learning Profile Panel (AC-2)
   *
   * Renders a single tip annotation with fold/unfold interaction.
   * Default: collapsed (shows content summary + time + category).
   * Expanded: shows source conversation context messages.
   *
   * CSS: cl-profile-tip-* prefix, Obsidian CSS variables, scoped.
   */

  import type { TipItem } from '../../types/canvas';

  let { tip }: { tip: TipItem } = $props();

  let expanded = $state(false);

  function toggle() {
    expanded = !expanded;
  }

  function formatDate(iso: string): string {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      return d.toLocaleDateString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return iso;
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggle();
    }
  }
</script>

<div class="cl-profile-tip-card" class:cl-profile-tip-card--expanded={expanded}>
  <div
    class="cl-profile-tip-header"
    onclick={toggle}
    onkeydown={handleKeyDown}
    role="button"
    tabindex="0"
    aria-expanded={expanded}
  >
    <span class="cl-profile-tip-content">{tip.content}</span>
    <div class="cl-profile-tip-meta">
      {#if tip.category}
        <span class="cl-profile-tip-tag">{tip.category}</span>
      {/if}
      <span class="cl-profile-tip-time">{formatDate(tip.annotatedAt)}</span>
      <span class="cl-profile-tip-chevron">{expanded ? '\u25B2' : '\u25BC'}</span>
    </div>
  </div>

  {#if expanded && tip.contextMessages.length > 0}
    <div class="cl-profile-tip-context">
      {#each tip.contextMessages as msg}
        <div class="cl-profile-tip-context-msg">{msg}</div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .cl-profile-tip-card {
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    overflow: hidden;
    margin-bottom: 6px;
  }

  .cl-profile-tip-header {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 8px 10px;
    cursor: pointer;
    background: var(--background-secondary);
    transition: background 0.15s ease;
  }

  .cl-profile-tip-header:hover {
    background: var(--background-modifier-hover);
  }

  .cl-profile-tip-content {
    font-size: 13px;
    color: var(--text-normal);
    line-height: 1.4;
  }

  .cl-profile-tip-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
    color: var(--text-muted);
  }

  .cl-profile-tip-tag {
    padding: 1px 6px;
    background: var(--background-modifier-border);
    border-radius: 3px;
    font-size: 10px;
  }

  .cl-profile-tip-time {
    flex: 1;
  }

  .cl-profile-tip-chevron {
    font-size: 10px;
    opacity: 0.6;
  }

  .cl-profile-tip-context {
    padding: 8px 10px;
    border-top: 1px solid var(--background-modifier-border);
    background: var(--background-primary);
    transition: max-height 200ms ease;
  }

  .cl-profile-tip-context-msg {
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.5;
    padding: 3px 0;
    border-bottom: 1px dotted var(--background-modifier-border);
  }

  .cl-profile-tip-context-msg:last-child {
    border-bottom: none;
  }
</style>
