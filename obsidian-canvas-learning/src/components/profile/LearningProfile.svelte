<script lang="ts">
  /**
   * Canvas Learning System - LearningProfile Main Component
   * Story 5.3: Learning Profile Panel (AC-1, AC-5, AC-6, AC-7, AC-8)
   *
   * Container for the node's learning profile, displaying:
   *   - L1: Mastery indicator + prescriptive message + learning stats
   *   - L2: Tips list (TipCard) + Weaknesses (WeaknessPanel)
   *   - L3: Key Q&A (QACluster) - default collapsed
   *   - Bottom: FSRS next review date + "Start Exam" button
   *
   * CSS: cl-profile-* prefix, Obsidian CSS variables, scoped.
   */

  import { profileState } from '../../stores/profile-state.svelte';
  import { masteryState } from '../../stores/mastery-state.svelte';
  import TipCard from './TipCard.svelte';
  import WeaknessPanel from './WeaknessPanel.svelte';
  import QACluster from './QACluster.svelte';

  interface Props {
    nodeId: string;
    onStartExam?: () => void;
    backendAvailable?: boolean;
  }

  let { nodeId, onStartExam, backendAvailable = true }: Props = $props();

  // Load profile when nodeId changes
  $effect(() => {
    if (nodeId) {
      profileState.loadProfile(nodeId);
    }
  });

  // Derived state from profileState
  let loadState = $derived(profileState.loadState);
  let summary = $derived(profileState.summary);
  let tips = $derived(profileState.tips);
  let weaknesses = $derived(profileState.weaknesses);
  let qaClusters = $derived(profileState.qaClusters);

  // FSRS data from mastery state
  let masteryData = $derived(masteryState.nodeMasteryMap.get(nodeId));
  let fsrsNextReview = $derived(masteryData?.fsrsNextReview ?? null);

  /**
   * Format FSRS due date to user-friendly relative time.
   * AC-5: "3 天后" / "明天" / "2026-03-20" / "建议今天复习"
   */
  function formatDueDate(isoDate: string | null): string {
    if (!isoDate) return '';
    try {
      const due = new Date(isoDate);
      const now = new Date();
      const diffMs = due.getTime() - now.getTime();
      const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

      if (diffDays < 0) return `已逾期 ${Math.abs(diffDays)} 天`;
      if (diffDays === 0) return '建议今天复习';
      if (diffDays === 1) return '明天';
      if (diffDays <= 7) return `${diffDays} 天后`;
      return due.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      });
    } catch {
      return '';
    }
  }

  /** Whether the due date is overdue (urgent state). */
  function isOverdue(isoDate: string | null): boolean {
    if (!isoDate) return false;
    try {
      return new Date(isoDate).getTime() <= Date.now();
    } catch {
      return false;
    }
  }

  /** Get the mastery level bar color style. */
  function getMasteryBarStyle(color: string | undefined): string {
    return `background-color: ${color ?? '#6c757d'}`;
  }

  function handleStartExam() {
    if (onStartExam) {
      onStartExam();
    }
  }
</script>

<div class="cl-profile-container">
  {#if loadState === 'loading'}
    <!-- Skeleton loading state -->
    <div class="cl-profile-skeleton">
      <div class="cl-profile-skeleton-bar"></div>
      <div class="cl-profile-skeleton-line"></div>
      <div class="cl-profile-skeleton-line cl-profile-skeleton-line--short"></div>
    </div>
  {:else if loadState === 'error'}
    <div class="cl-profile-error">
      <p>加载学习档案失败</p>
      <button class="cl-profile-retry-btn" onclick={() => profileState.loadProfile(nodeId, true)}>
        重试
      </button>
    </div>
  {:else if summary}
    <!-- L1: Mastery Indicator + Summary (always visible) -->
    <div class="cl-profile-header">
      <div class="cl-profile-mastery-bar" style={getMasteryBarStyle(summary.masteryColor)}></div>
      <div class="cl-profile-mastery-info">
        <span class="cl-profile-mastery-label" style="color: {summary.masteryColor}">
          {summary.masteryLabel}
        </span>
        <span class="cl-profile-prescriptive">{summary.prescriptiveMessage}</span>
      </div>
    </div>

    <div class="cl-profile-stats">
      <div class="cl-profile-stat">
        <span class="cl-profile-stat-value">{summary.interactionCount}</span>
        <span class="cl-profile-stat-label">交互次数</span>
      </div>
      <div class="cl-profile-stat">
        <span class="cl-profile-stat-value">{summary.examCount}</span>
        <span class="cl-profile-stat-label">考察次数</span>
      </div>
      {#if summary.lastExamDate}
        <div class="cl-profile-stat">
          <span class="cl-profile-stat-value">
            {new Date(summary.lastExamDate).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })}
          </span>
          <span class="cl-profile-stat-label">最近考察</span>
        </div>
      {/if}
    </div>

    <!-- L2: Tips (default visible, collapsible) -->
    <div class="cl-profile-section">
      <h4 class="cl-profile-section-title">
        <span class="cl-profile-section-icon">\u{1F4CC}</span>
        Tips
      </h4>
      {#if tips.length === 0}
        <div class="cl-profile-empty-hint">
          对话中选中文字即可标记 Tips
        </div>
      {:else}
        {#each tips as tip (tip.tipId)}
          <TipCard {tip} />
        {/each}
      {/if}
    </div>

    <!-- L2: Weaknesses (positive framing) -->
    <WeaknessPanel {weaknesses} />

    <!-- L3: QA Highlights (default collapsed) -->
    <QACluster clusters={qaClusters} />

    <!-- Bottom: FSRS Review Date + Start Exam -->
    <div class="cl-profile-footer">
      {#if summary.examCount > 0}
        <!-- AC-5: FSRS due date -->
        {#if fsrsNextReview || summary.fsrsDueDate}
          {@const dueDate = fsrsNextReview ?? summary.fsrsDueDate}
          <div
            class="cl-profile-review-date"
            class:cl-profile-review-date--urgent={isOverdue(dueDate)}
          >
            <span class="cl-profile-review-label">下次复习</span>
            <span class="cl-profile-review-value">{formatDueDate(dueDate)}</span>
          </div>
        {/if}
      {:else}
        <div class="cl-profile-review-date">
          <span class="cl-profile-review-hint">完成首次考察后安排复习</span>
        </div>
      {/if}

      <!-- AC-6: Start Exam button -->
      <button
        class="cl-profile-exam-btn"
        onclick={handleStartExam}
        disabled={!backendAvailable}
        title={backendAvailable ? '开始考察' : '后端服务不可用'}
      >
        开始考察
      </button>
    </div>
  {:else}
    <!-- Idle / no data state -->
    <div class="cl-profile-empty">
      <p class="cl-profile-empty-text">选择一个节点查看学习档案</p>
    </div>
  {/if}
</div>

<style>
  .cl-profile-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 12px;
    height: 100%;
    overflow-y: auto;
  }

  /* Skeleton loading */
  .cl-profile-skeleton {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 12px;
  }

  .cl-profile-skeleton-bar {
    height: 6px;
    width: 60%;
    background: var(--background-modifier-border);
    border-radius: 3px;
    animation: cl-profile-pulse 1.5s ease-in-out infinite;
  }

  .cl-profile-skeleton-line {
    height: 14px;
    width: 80%;
    background: var(--background-modifier-border);
    border-radius: 3px;
    animation: cl-profile-pulse 1.5s ease-in-out infinite;
  }

  .cl-profile-skeleton-line--short {
    width: 50%;
  }

  @keyframes cl-profile-pulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 0.8; }
  }

  /* Error state */
  .cl-profile-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 20px;
    color: var(--text-muted);
    font-size: 13px;
  }

  .cl-profile-retry-btn {
    padding: 4px 12px;
    font-size: 12px;
    background: var(--interactive-accent);
    color: var(--text-on-accent);
    border: none;
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
  }

  /* L1: Mastery Header */
  .cl-profile-header {
    display: flex;
    align-items: stretch;
    gap: 10px;
    padding: 10px;
    background: var(--background-secondary);
    border-radius: var(--radius-s, 4px);
  }

  .cl-profile-mastery-bar {
    width: 4px;
    border-radius: 2px;
    flex-shrink: 0;
  }

  .cl-profile-mastery-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .cl-profile-mastery-label {
    font-size: 14px;
    font-weight: 600;
  }

  .cl-profile-prescriptive {
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.4;
  }

  /* Stats row */
  .cl-profile-stats {
    display: flex;
    gap: 12px;
    padding: 8px 0;
    border-bottom: 1px solid var(--background-modifier-border);
  }

  .cl-profile-stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
  }

  .cl-profile-stat-value {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-normal);
  }

  .cl-profile-stat-label {
    font-size: 10px;
    color: var(--text-muted);
  }

  /* Section titles */
  .cl-profile-section {
    margin-bottom: 12px;
  }

  .cl-profile-section-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-normal);
    margin: 0 0 8px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .cl-profile-section-icon {
    font-size: 14px;
  }

  .cl-profile-empty-hint {
    font-size: 12px;
    color: var(--text-muted);
    padding: 10px;
    text-align: center;
    background: var(--background-secondary);
    border-radius: var(--radius-s, 4px);
  }

  /* Footer: FSRS date + exam button */
  .cl-profile-footer {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: auto;
    padding-top: 12px;
    border-top: 1px solid var(--background-modifier-border);
  }

  .cl-profile-review-date {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 10px;
    background: var(--background-secondary);
    border-radius: var(--radius-s, 4px);
    font-size: 13px;
  }

  .cl-profile-review-date--urgent {
    background: rgba(255, 193, 7, 0.15);
    border: 1px solid rgba(255, 193, 7, 0.4);
  }

  .cl-profile-review-label {
    color: var(--text-muted);
  }

  .cl-profile-review-value {
    font-weight: 600;
    color: var(--text-normal);
  }

  .cl-profile-review-date--urgent .cl-profile-review-value {
    color: #ffc107;
  }

  .cl-profile-review-hint {
    color: var(--text-muted);
    font-size: 12px;
  }

  .cl-profile-exam-btn {
    width: 100%;
    padding: 10px;
    font-size: 14px;
    font-weight: 600;
    color: var(--text-on-accent);
    background: var(--interactive-accent);
    border: none;
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
    transition: background 0.15s ease, opacity 0.15s ease;
  }

  .cl-profile-exam-btn:hover:not(:disabled) {
    background: var(--interactive-accent-hover);
  }

  .cl-profile-exam-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Empty state */
  .cl-profile-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    padding: 20px;
  }

  .cl-profile-empty-text {
    color: var(--text-muted);
    font-size: 13px;
  }
</style>
