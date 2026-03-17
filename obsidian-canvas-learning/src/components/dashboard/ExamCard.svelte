<script lang="ts">
  /**
   * Canvas Learning System - ExamCard Component
   * Story 5.4: FSRS Review Dashboard (AC-2, AC-5)
   *
   * Renders a single exam session card showing:
   *   - Source board name
   *   - Exam time
   *   - Status badge (in-progress: blue / completed: green)
   *   - Nodes examined count
   *   - Mastery change summary
   *
   * CSS: cl-dash-exam-* prefix, Obsidian CSS variables, scoped.
   */

  import type { ExamSession } from '../../types/canvas';

  interface Props {
    session: ExamSession;
    onclick?: () => void;
  }

  let { session, onclick }: Props = $props();

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

  function modeLabel(mode: string): string {
    switch (mode) {
      case 'point-to-point':
        return '点对点';
      case 'comprehensive':
        return '综合题';
      case 'mixed':
        return '混合';
      default:
        return mode;
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
  class="cl-dash-exam-card"
  onclick={handleClick}
  onkeydown={handleKeyDown}
  role="button"
  tabindex="0"
>
  <div class="cl-dash-exam-header">
    <span class="cl-dash-exam-board">{session.sourceBoardName || '未命名白板'}</span>
    <span
      class="cl-dash-exam-badge"
      class:cl-dash-exam-badge--active={session.status === 'in-progress'}
      class:cl-dash-exam-badge--done={session.status === 'completed'}
    >
      {session.status === 'in-progress' ? '考察进行中' : '已完成'}
    </span>
  </div>

  <div class="cl-dash-exam-details">
    <span class="cl-dash-exam-time">{formatDate(session.createdAt)}</span>
    <span class="cl-dash-exam-mode">{modeLabel(session.mode)}</span>
    <span class="cl-dash-exam-nodes">{session.nodesExamined} 节点</span>
  </div>

  {#if session.masteryChangeSummary}
    <div class="cl-dash-exam-change">{session.masteryChangeSummary}</div>
  {/if}
</div>

<style>
  .cl-dash-exam-card {
    padding: 10px 12px;
    background: var(--background-secondary);
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }

  .cl-dash-exam-card:hover {
    border-color: var(--interactive-accent);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  }

  .cl-dash-exam-card:focus-visible {
    outline: 2px solid var(--interactive-accent);
    outline-offset: 2px;
  }

  .cl-dash-exam-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }

  .cl-dash-exam-board {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-normal);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .cl-dash-exam-badge {
    font-size: 10px;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 10px;
    flex-shrink: 0;
  }

  .cl-dash-exam-badge--active {
    background: rgba(13, 110, 253, 0.15);
    color: #0d6efd;
  }

  .cl-dash-exam-badge--done {
    background: rgba(25, 135, 84, 0.15);
    color: #198754;
  }

  .cl-dash-exam-details {
    display: flex;
    gap: 12px;
    font-size: 11px;
    color: var(--text-muted);
    margin-bottom: 4px;
  }

  .cl-dash-exam-change {
    font-size: 12px;
    color: var(--text-normal);
    margin-top: 4px;
    padding-top: 4px;
    border-top: 1px dotted var(--background-modifier-border);
  }
</style>
