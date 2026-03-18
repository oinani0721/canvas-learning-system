<script lang="ts">
  /**
   * Canvas Learning System - QACluster Component
   * Story 5.3: Learning Profile Panel (AC-4)
   *
   * Displays key Q&A pairs grouped by topic in collapsible sections.
   * Default: all groups collapsed. Click topic header to expand.
   *
   * CSS: cl-profile-qa-* prefix, Obsidian CSS variables, scoped.
   */

  import type { QAHighlightCluster } from '../../types/canvas';

  let { clusters }: { clusters: QAHighlightCluster[] } = $props();

  let expandedTopics = $state<Set<string>>(new Set());

  function toggleTopic(topic: string) {
    const next = new Set(expandedTopics);
    if (next.has(topic)) {
      next.delete(topic);
    } else {
      next.add(topic);
    }
    expandedTopics = next;
  }

  function formatDate(iso: string): string {
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

  function handleKeyDown(e: KeyboardEvent, topic: string) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleTopic(topic);
    }
  }
</script>

<div class="cl-profile-qa-panel">
  <h4 class="cl-profile-qa-title">
    <span class="cl-profile-qa-icon">\u{1F4AC}</span>
    关键问答
  </h4>

  {#if clusters.length === 0}
    <div class="cl-profile-qa-empty">
      和 AI 对话后，精彩问答会自动整理到这里
    </div>
  {:else}
    {#each clusters as cluster}
      <div class="cl-profile-qa-group">
        <div
          class="cl-profile-qa-group-header"
          onclick={() => toggleTopic(cluster.topic)}
          onkeydown={(e) => handleKeyDown(e, cluster.topic)}
          role="button"
          tabindex="0"
          aria-expanded={expandedTopics.has(cluster.topic)}
        >
          <span class="cl-profile-qa-group-name">{cluster.topic}</span>
          <span class="cl-profile-qa-group-count">
            {cluster.qaPairs.length} 条
          </span>
          <span class="cl-profile-qa-group-chevron">
            {expandedTopics.has(cluster.topic) ? '\u25B2' : '\u25BC'}
          </span>
        </div>

        {#if expandedTopics.has(cluster.topic)}
          <div class="cl-profile-qa-group-content">
            {#each cluster.qaPairs as pair}
              <div class="cl-profile-qa-pair">
                <div class="cl-profile-qa-question">
                  <span class="cl-profile-qa-label">Q</span>
                  {pair.question}
                </div>
                {#if pair.answer}
                  <div class="cl-profile-qa-answer">
                    <span class="cl-profile-qa-label">A</span>
                    {pair.answer}
                  </div>
                {/if}
                {#if pair.extractedAt}
                  <div class="cl-profile-qa-time">{formatDate(pair.extractedAt)}</div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/each}
  {/if}
</div>

<style>
  .cl-profile-qa-panel {
    margin-bottom: 12px;
  }

  .cl-profile-qa-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-normal);
    margin: 0 0 8px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .cl-profile-qa-icon {
    font-size: 14px;
  }

  .cl-profile-qa-empty {
    font-size: 13px;
    color: var(--text-muted);
    padding: 12px;
    text-align: center;
    background: var(--background-secondary);
    border-radius: var(--radius-s, 4px);
  }

  .cl-profile-qa-group {
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    margin-bottom: 6px;
    overflow: hidden;
  }

  .cl-profile-qa-group-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    cursor: pointer;
    background: var(--background-secondary);
    transition: background 0.15s ease;
  }

  .cl-profile-qa-group-header:hover {
    background: var(--background-modifier-hover);
  }

  .cl-profile-qa-group-name {
    flex: 1;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-normal);
  }

  .cl-profile-qa-group-count {
    font-size: 11px;
    color: var(--text-muted);
  }

  .cl-profile-qa-group-chevron {
    font-size: 10px;
    opacity: 0.6;
  }

  .cl-profile-qa-group-content {
    padding: 6px 10px;
    border-top: 1px solid var(--background-modifier-border);
    background: var(--background-primary);
    transition: max-height 200ms ease;
  }

  .cl-profile-qa-pair {
    padding: 6px 0;
    border-bottom: 1px dotted var(--background-modifier-border);
  }

  .cl-profile-qa-pair:last-child {
    border-bottom: none;
  }

  .cl-profile-qa-question,
  .cl-profile-qa-answer {
    font-size: 12px;
    line-height: 1.5;
    color: var(--text-normal);
    padding: 2px 0;
  }

  .cl-profile-qa-label {
    display: inline-block;
    width: 18px;
    height: 18px;
    line-height: 18px;
    text-align: center;
    font-size: 10px;
    font-weight: 700;
    border-radius: 3px;
    margin-right: 6px;
    flex-shrink: 0;
  }

  .cl-profile-qa-question .cl-profile-qa-label {
    background: var(--interactive-accent);
    color: var(--text-on-accent);
  }

  .cl-profile-qa-answer .cl-profile-qa-label {
    background: var(--background-modifier-border);
    color: var(--text-muted);
  }

  .cl-profile-qa-answer {
    color: var(--text-muted);
  }

  .cl-profile-qa-time {
    font-size: 10px;
    color: var(--text-faint);
    text-align: right;
    margin-top: 2px;
  }
</style>
