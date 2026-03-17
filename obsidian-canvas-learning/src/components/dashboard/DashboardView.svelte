<script lang="ts">
  /**
   * Canvas Learning System - Dashboard View Component
   * Story 1.4: Minimal Dashboard listing all boards (AC-7)
   *
   * Shows:
   *   - Board list (name + date + node count)
   *   - "New Board" button
   *   - Empty state guidance
   */

  import { canvasState } from '../../stores/canvas-state';
  import CanvasCard from './CanvasCard.svelte';

  // Force reactivity
  let stateVersion = $state(0);
  $effect(() => {
    const unsub = canvasState.subscribe(() => {
      stateVersion++;
    });
    return unsub;
  });

  let boards = $derived.by(() => {
    void stateVersion;
    return canvasState.boards;
  });

  // ── Handlers ─────────────────────────────────────────────────────────

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
</script>

<div class="cl-dash-container">
  <div class="cl-dash-header">
    <h3 class="cl-dash-title">我的白板</h3>
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
      <div class="cl-dash-empty-icon">📋</div>
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
        <CanvasCard {board} onselect={() => openBoard(board.id)} />
      {/each}
    </div>
  {/if}
</div>

<style>
  .cl-dash-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 0;
  }

  .cl-dash-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--background-modifier-border);
    margin-bottom: 12px;
  }

  .cl-dash-title {
    margin: 0;
    font-size: 1.1em;
    font-weight: 600;
    color: var(--text-normal);
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

  .cl-dash-board-list {
    display: flex;
    flex-direction: column;
    gap: var(--size-4-2, 8px);
    overflow-y: auto;
    flex: 1;
  }

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
    margin: 0 0 16px;
  }

  .cl-dash-empty-btn {
    padding: 8px 20px;
    font-size: 14px;
    color: var(--text-on-accent);
    background: var(--interactive-accent);
    border: none;
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
  }

  .cl-dash-empty-btn:hover {
    background: var(--interactive-accent-hover);
  }
</style>
