<script lang="ts">
  /**
   * Canvas Learning System - Dashboard View Component
   * Story 1.4: Minimal Dashboard listing all boards (AC-7)
   * Story 5.4: Upgraded with Tab switching, exam sessions, FSRS review (AC-1 through AC-7)
   *
   * Shows:
   *   Tab: 原白板 - Board list (name + date + node count + mastery + exam entry)
   *   Tab: 检验白板 - Exam session cards (time-desc)
   *   Tab: 待复习 - FSRS-sorted review nodes
   *
   * Offline degradation: boards tab works from IndexedDB, others show offline message.
   */

  import { canvasState } from '../../stores/canvas-state';
  import { systemState } from '../../stores/system-state.svelte';
  import { dashboardState, type DashboardTab } from '../../stores/dashboard-state.svelte';
  import CanvasCard from './CanvasCard.svelte';
  import ReviewItem from './ReviewItem.svelte';
  import ExamCard from './ExamCard.svelte';

  // Force reactivity
  let stateVersion = $state(0);
  $effect(() => {
    const unsub = canvasState.subscribe(() => {
      stateVersion++;
    });
    return unsub;
  });

  let sysStateVersion = $state(0);
  $effect(() => {
    const unsub = systemState.subscribe(() => {
      sysStateVersion++;
    });
    return unsub;
  });

  // Story 1.9: Filter boards by active subject
  let boards = $derived.by(() => {
    void stateVersion;
    void sysStateVersion;
    const all = canvasState.boards;
    const activeId = systemState.activeSubjectId;
    if (!activeId) return all;
    return all.filter(b => b.subjectId === activeId || !b.subjectId);
  });

  let subjects = $derived.by(() => {
    void sysStateVersion;
    return systemState.subjects;
  });

  function handleSubjectChange(e: Event) {
    const value = (e.target as HTMLSelectElement).value;
    systemState.setActiveSubject(value || null);
  }

  // Dashboard state reactive reads
  let activeTab = $derived(dashboardState.activeTab);
  let examSessions = $derived(dashboardState.examSessions);
  let reviewNodes = $derived(dashboardState.reviewNodes);
  let isLoading = $derived(dashboardState.isLoading);
  let backendOffline = $derived(dashboardState.backendOffline);
  let overdueCount = $derived(dashboardState.overdueCount);
  let dueCount = $derived(dashboardState.dueCount);
  let weakCount = $derived(dashboardState.weakCount);

  // Load dashboard data on mount
  $effect(() => {
    dashboardState.refreshAll();
  });

  // ── Tab definitions ─────────────────────────────────────────────────────
  const tabs: { id: DashboardTab; label: string }[] = [
    { id: 'boards', label: '原白板' },
    { id: 'exams', label: '检验白板' },
    { id: 'review', label: '待复习' },
  ];

  function switchTab(tab: DashboardTab) {
    dashboardState.setTab(tab);
  }

  /** Review count badge for the tab. */
  let reviewBadge = $derived(overdueCount + dueCount + weakCount);

  // ── Board creation (preserved from Story 1.4) ──────────────────────────
  let isCreating = $state(false);
  let newBoardName = $state('');
  let nameInputEl: HTMLInputElement | null = $state(null);

  function showCreateForm() {
    isCreating = true;
    newBoardName = '';
    requestAnimationFrame(() => {
      nameInputEl?.focus();
    });
  }

  async function confirmCreate() {
    const name = newBoardName.trim();
    if (!name) return;
    isCreating = false;
    await canvasState.createBoard(name);
  }

  function cancelCreate() {
    isCreating = false;
    newBoardName = '';
  }

  function handleCreateKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      e.preventDefault();
      confirmCreate();
    } else if (e.key === 'Escape') {
      cancelCreate();
    }
  }

  function openBoard(boardId: string) {
    canvasState.switchBoard(boardId);
  }

  /**
   * Get exam history for a specific board.
   */
  function getBoardExamHistory(boardId: string) {
    return examSessions.filter((s) => s.sourceBoardId === boardId);
  }
</script>

<div class="cl-dash-container">
  <!-- Tab bar (Story 5.4) -->
  <div class="cl-dash-tab-bar">
    {#each tabs as tab}
      <button
        class="cl-dash-tab"
        class:cl-dash-tab--active={activeTab === tab.id}
        onclick={() => switchTab(tab.id)}
      >
        {tab.label}
        {#if tab.id === 'review' && reviewBadge > 0}
          <span class="cl-dash-tab-badge">{reviewBadge}</span>
        {/if}
      </button>
    {/each}
  </div>

  <!-- Tab content -->
  <div class="cl-dash-content">
    {#if activeTab === 'boards'}
      <!-- ═══ Boards Tab (Story 1.4 original + Story 5.4 upgrades) ═══ -->
      <div class="cl-dash-header">
        <h3 class="cl-dash-title">我的白板</h3>
        <!-- Story 1.9: Subject filter dropdown -->
        {#if subjects.length > 1}
          <select class="cl-dash-subject-filter" onchange={handleSubjectChange} value={systemState.activeSubjectId ?? ''}>
            <option value="">全部学科</option>
            {#each subjects as subject (subject.id)}
              <option value={subject.id}>{subject.name}</option>
            {/each}
          </select>
        {/if}
        <button class="cl-dash-new-btn" onclick={showCreateForm}>
          + 新建白板
        </button>
      </div>

      <!-- Create form -->
      {#if isCreating}
        <div class="cl-dash-create-form">
          <input
            bind:this={nameInputEl}
            type="text"
            class="cl-dash-create-input"
            placeholder="输入白板名称..."
            bind:value={newBoardName}
            onkeydown={handleCreateKeydown}
            onblur={cancelCreate}
          />
          <button class="cl-dash-create-confirm" onmousedown={(e) => { e.preventDefault(); confirmCreate(); }}>
            创建
          </button>
        </div>
      {/if}

      <!-- Board list or empty state -->
      {#if boards.length === 0}
        <div class="cl-dash-empty">
          <div class="cl-dash-empty-icon">&#x1F4CB;</div>
          <p class="cl-dash-empty-text">还没有白板，创建第一个开始学习吧！</p>
          {#if !isCreating}
            <button class="cl-dash-empty-btn" onclick={showCreateForm}>
              创建白板
            </button>
          {/if}
        </div>
      {:else}
        <div class="cl-dash-board-list">
          {#each boards as board (board.id)}
            <CanvasCard
              {board}
              onselect={() => openBoard(board.id)}
              examHistory={getBoardExamHistory(board.id)}
            />
          {/each}
        </div>
      {/if}

    {:else if activeTab === 'exams'}
      <!-- ═══ Exam Sessions Tab (Story 5.4 AC-2) ═══ -->
      {#if backendOffline}
        <div class="cl-dash-offline">
          <p>后端离线，无法加载检验白板数据</p>
        </div>
      {:else if isLoading}
        <div class="cl-dash-loading">
          <div class="cl-dash-skeleton"></div>
          <div class="cl-dash-skeleton"></div>
          <div class="cl-dash-skeleton"></div>
        </div>
      {:else if examSessions.length === 0}
        <div class="cl-dash-empty">
          <p class="cl-dash-empty-text">还没有考察记录</p>
          <p class="cl-dash-empty-hint">在白板中开始考察后，记录会显示在这里</p>
        </div>
      {:else}
        <div class="cl-dash-exam-list">
          {#each examSessions as session (session.id)}
            <ExamCard {session} />
          {/each}
        </div>
      {/if}

    {:else if activeTab === 'review'}
      <!-- ═══ Review Tab (Story 5.4 AC-3) ═══ -->
      {#if backendOffline}
        <div class="cl-dash-offline">
          <p>后端离线，无法加载复习数据</p>
        </div>
      {:else if isLoading}
        <div class="cl-dash-loading">
          <div class="cl-dash-skeleton"></div>
          <div class="cl-dash-skeleton"></div>
          <div class="cl-dash-skeleton"></div>
        </div>
      {:else}
        <!-- Review stats summary -->
        {#if reviewNodes.length > 0}
          <div class="cl-dash-review-summary">
            {#if overdueCount > 0}
              <span class="cl-dash-review-stat cl-dash-review-stat--overdue">
                {overdueCount} 已逾期
              </span>
            {/if}
            {#if dueCount > 0}
              <span class="cl-dash-review-stat cl-dash-review-stat--due">
                {dueCount} 建议复习
              </span>
            {/if}
            {#if weakCount > 0}
              <span class="cl-dash-review-stat cl-dash-review-stat--weak">
                {weakCount} 需要加强
              </span>
            {/if}
          </div>

          <div class="cl-dash-review-list">
            {#each reviewNodes as node (node.conceptId)}
              <ReviewItem {node} />
            {/each}
          </div>
        {:else}
          <div class="cl-dash-empty">
            <p class="cl-dash-empty-text">所有知识点都在掌握中，继续保持！</p>
          </div>
        {/if}
      {/if}
    {/if}
  </div>
</div>

<style>
  .cl-dash-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 0;
  }

  /* Tab bar (Story 5.4) */
  .cl-dash-tab-bar {
    display: flex;
    border-bottom: 1px solid var(--background-modifier-border);
    flex-shrink: 0;
    margin-bottom: 12px;
  }

  .cl-dash-tab {
    flex: 1;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-muted);
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    transition: color 0.15s ease, border-color 0.15s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
  }

  .cl-dash-tab:hover {
    color: var(--text-normal);
  }

  .cl-dash-tab--active {
    color: var(--interactive-accent);
    border-bottom-color: var(--interactive-accent);
  }

  .cl-dash-tab-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 1px 5px;
    border-radius: 8px;
    background: var(--interactive-accent);
    color: var(--text-on-accent);
    min-width: 16px;
    text-align: center;
  }

  /* Content area */
  .cl-dash-content {
    flex: 1;
    overflow-y: auto;
  }

  .cl-dash-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--background-modifier-border);
    margin-bottom: 12px;
    gap: 8px;
  }

  .cl-dash-title {
    margin: 0;
    font-size: 1.1em;
    font-weight: 600;
    color: var(--text-normal);
  }

  .cl-dash-subject-filter {
    padding: 4px 8px;
    font-size: 13px;
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    background: var(--background-primary);
    color: var(--text-normal);
    outline: none;
  }

  .cl-dash-subject-filter:focus {
    border-color: var(--interactive-accent);
  }

  .cl-dash-new-btn {
    padding: 4px 12px;
    font-size: 13px;
    color: var(--text-on-accent);
    background: var(--interactive-accent);
    border: none;
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
    transition: background 0.15s ease;
  }

  .cl-dash-new-btn:hover {
    background: var(--interactive-accent-hover);
  }

  .cl-dash-create-form {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
  }

  .cl-dash-create-input {
    flex: 1;
    padding: 6px 10px;
    font-size: 13px;
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    background: var(--background-primary);
    color: var(--text-normal);
    outline: none;
  }

  .cl-dash-create-input:focus {
    border-color: var(--interactive-accent);
  }

  .cl-dash-create-confirm {
    padding: 6px 14px;
    font-size: 13px;
    color: var(--text-on-accent);
    background: var(--interactive-accent);
    border: none;
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
  }

  .cl-dash-board-list,
  .cl-dash-exam-list,
  .cl-dash-review-list {
    display: flex;
    flex-direction: column;
    gap: var(--size-4-2, 8px);
    overflow-y: auto;
    flex: 1;
  }

  /* Empty state */
  .cl-dash-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    padding: 40px 20px;
    text-align: center;
  }

  .cl-dash-empty-icon {
    font-size: 36px;
    margin-bottom: 12px;
    opacity: 0.6;
  }

  .cl-dash-empty-text {
    color: var(--text-muted);
    font-size: 14px;
    margin: 0 0 8px;
  }

  .cl-dash-empty-hint {
    color: var(--text-faint);
    font-size: 12px;
    margin: 0;
  }

  .cl-dash-empty-btn {
    padding: 8px 20px;
    font-size: 14px;
    color: var(--text-on-accent);
    background: var(--interactive-accent);
    border: none;
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
    margin-top: 8px;
  }

  .cl-dash-empty-btn:hover {
    background: var(--interactive-accent-hover);
  }

  /* Offline state */
  .cl-dash-offline {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    color: var(--text-muted);
    font-size: 14px;
    text-align: center;
  }

  /* Loading skeleton */
  .cl-dash-loading {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px 0;
  }

  .cl-dash-skeleton {
    height: 60px;
    background: var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    animation: cl-dash-pulse 1.5s ease-in-out infinite;
  }

  @keyframes cl-dash-pulse {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 0.6; }
  }

  /* Review summary */
  .cl-dash-review-summary {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
    flex-wrap: wrap;
  }

  .cl-dash-review-stat {
    font-size: 12px;
    font-weight: 500;
    padding: 4px 10px;
    border-radius: var(--radius-s, 4px);
  }

  .cl-dash-review-stat--overdue {
    background: rgba(220, 53, 69, 0.15);
    color: #dc3545;
  }

  .cl-dash-review-stat--due {
    background: rgba(255, 193, 7, 0.15);
    color: #b38600;
  }

  .cl-dash-review-stat--weak {
    background: rgba(253, 126, 20, 0.15);
    color: #fd7e14;
  }
</style>
