<script lang="ts">
  /**
   * Canvas Learning System - WeaknessPanel Component
   * Story 5.3: Learning Profile Panel (AC-3)
   *
   * Displays "areas to strengthen" using positive supportive language.
   * Each item shows: direction description, frequency, last seen date.
   * Items can be expanded to view related exam record summaries.
   *
   * CSS: cl-profile-weakness-* prefix, Obsidian CSS variables, scoped.
   */

  import type { WeaknessItem } from '../../types/canvas';

  let { weaknesses }: { weaknesses: WeaknessItem[] } = $props();

  let expandedIndex = $state<number | null>(null);

  function toggleExpand(index: number) {
    expandedIndex = expandedIndex === index ? null : index;
  }

  function formatDate(iso: string | null): string {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      return d.toLocaleDateString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
      });
    } catch {
      return '';
    }
  }

  function handleKeyDown(e: KeyboardEvent, index: number) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleExpand(index);
    }
  }
</script>

<div class="cl-profile-weakness-panel">
  <h4 class="cl-profile-weakness-title">
    <span class="cl-profile-weakness-icon">\u{1F4AA}</span>
    需要加强的方向
  </h4>

  {#if weaknesses.length === 0}
    <div class="cl-profile-weakness-empty">
      目前表现不错，继续保持！
    </div>
  {:else}
    {#each weaknesses as item, index}
      <div
        class="cl-profile-weakness-item"
        class:cl-profile-weakness-item--expanded={expandedIndex === index}
      >
        <div
          class="cl-profile-weakness-item-header"
          onclick={() => toggleExpand(index)}
          onkeydown={(e) => handleKeyDown(e, index)}
          role="button"
          tabindex="0"
          aria-expanded={expandedIndex === index}
        >
          <span class="cl-profile-weakness-direction">{item.direction}</span>
          <div class="cl-profile-weakness-meta">
            <span class="cl-profile-weakness-freq">
              {item.frequency} 次考察中涉及
            </span>
            {#if item.lastSeen}
              <span class="cl-profile-weakness-date">
                {formatDate(item.lastSeen)}
              </span>
            {/if}
          </div>
        </div>

        {#if expandedIndex === index && item.relatedExamSummaries.length > 0}
          <div class="cl-profile-weakness-details">
            {#each item.relatedExamSummaries as summary}
              <div class="cl-profile-weakness-exam-summary">{summary}</div>
            {/each}
          </div>
        {/if}
      </div>
    {/each}
  {/if}
</div>

<style>
  .cl-profile-weakness-panel {
    margin-bottom: 12px;
  }

  .cl-profile-weakness-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-normal);
    margin: 0 0 8px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .cl-profile-weakness-icon {
    font-size: 14px;
  }

  .cl-profile-weakness-empty {
    font-size: 13px;
    color: var(--text-muted);
    padding: 12px;
    text-align: center;
    background: var(--background-secondary);
    border-radius: var(--radius-s, 4px);
  }

  .cl-profile-weakness-item {
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    margin-bottom: 6px;
    overflow: hidden;
  }

  .cl-profile-weakness-item-header {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 8px 10px;
    cursor: pointer;
    background: var(--background-secondary);
    transition: background 0.15s ease;
  }

  .cl-profile-weakness-item-header:hover {
    background: var(--background-modifier-hover);
  }

  .cl-profile-weakness-direction {
    font-size: 13px;
    color: var(--text-normal);
    line-height: 1.4;
  }

  .cl-profile-weakness-meta {
    display: flex;
    gap: 8px;
    font-size: 11px;
    color: var(--text-muted);
  }

  .cl-profile-weakness-details {
    padding: 8px 10px;
    border-top: 1px solid var(--background-modifier-border);
    background: var(--background-primary);
    transition: max-height 200ms ease;
  }

  .cl-profile-weakness-exam-summary {
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.5;
    padding: 3px 0;
  }
</style>
