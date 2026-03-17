<script lang="ts">
  /**
   * Canvas Learning System - ExamLauncher Component
   * Story 5.4: FSRS Review Dashboard (AC-4)
   *
   * Exam launch entry point. Renders a modal with exam mode options.
   * This is a visual placeholder - full exam launch logic will be
   * implemented in Story 6.1/6.2 (ExamModeSelector + exam creation).
   *
   * Modes: point-to-point | comprehensive | mixed
   * Each mode option shows a description; clicking shows a "coming soon" message.
   *
   * CSS: cl-dash-launcher-* prefix, Obsidian CSS variables, scoped.
   */

  interface Props {
    boardName: string;
    nodeCount: number;
    isOpen: boolean;
    onclose: () => void;
  }

  let { boardName, nodeCount, isOpen, onclose }: Props = $props();

  let selectedMode = $state<string | null>(null);
  let showComingSoon = $state(false);

  const examModes = [
    {
      id: 'point-to-point',
      name: '点对点考察',
      description: '逐个节点深入考察，适合精确检验每个知识点',
    },
    {
      id: 'comprehensive',
      name: '综合题考察',
      description: '跨节点综合出题，检验知识间的联系和应用',
    },
    {
      id: 'mixed',
      name: '混合考察',
      description: '结合两种模式，全面评估掌握程度',
    },
  ];

  function selectMode(modeId: string) {
    selectedMode = modeId;
    showComingSoon = true;
  }

  function handleClose() {
    selectedMode = null;
    showComingSoon = false;
    onclose();
  }

  function handleBackdropClick(e: MouseEvent) {
    if ((e.target as HTMLElement).classList.contains('cl-dash-launcher-overlay')) {
      handleClose();
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      handleClose();
    }
  }
</script>

{#if isOpen}
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div
    class="cl-dash-launcher-overlay"
    onclick={handleBackdropClick}
    onkeydown={handleKeyDown}
    role="dialog"
    aria-modal="true"
    aria-label="选择考察模式"
  >
    <div class="cl-dash-launcher-modal">
      <div class="cl-dash-launcher-header">
        <h3 class="cl-dash-launcher-title">开始考察</h3>
        <button class="cl-dash-launcher-close" onclick={handleClose} aria-label="关闭">
          \u2715
        </button>
      </div>

      <div class="cl-dash-launcher-info">
        <span class="cl-dash-launcher-board">{boardName}</span>
        <span class="cl-dash-launcher-count">{nodeCount} 个知识节点</span>
      </div>

      {#if showComingSoon}
        <div class="cl-dash-launcher-coming-soon">
          <p>考察功能将在后续版本启用</p>
          <p class="cl-dash-launcher-coming-soon-hint">
            已选择：{examModes.find((m) => m.id === selectedMode)?.name}
          </p>
          <button class="cl-dash-launcher-back-btn" onclick={() => { showComingSoon = false; selectedMode = null; }}>
            返回
          </button>
        </div>
      {:else}
        <div class="cl-dash-launcher-modes">
          {#each examModes as mode}
            <button
              class="cl-dash-launcher-mode"
              onclick={() => selectMode(mode.id)}
            >
              <span class="cl-dash-launcher-mode-name">{mode.name}</span>
              <span class="cl-dash-launcher-mode-desc">{mode.description}</span>
            </button>
          {/each}
        </div>
      {/if}

      <div class="cl-dash-launcher-tip">
        推荐：使用混合模式进行全面评估
      </div>
    </div>
  </div>
{/if}

<style>
  .cl-dash-launcher-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .cl-dash-launcher-modal {
    background: var(--background-primary);
    border: 1px solid var(--background-modifier-border);
    border-radius: 8px;
    width: 320px;
    max-width: 90vw;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    overflow: hidden;
  }

  .cl-dash-launcher-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 16px;
    border-bottom: 1px solid var(--background-modifier-border);
  }

  .cl-dash-launcher-title {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
    color: var(--text-normal);
  }

  .cl-dash-launcher-close {
    background: none;
    border: none;
    font-size: 16px;
    color: var(--text-muted);
    cursor: pointer;
    padding: 2px 6px;
    border-radius: 3px;
    transition: background 0.15s ease;
  }

  .cl-dash-launcher-close:hover {
    background: var(--background-modifier-hover);
    color: var(--text-normal);
  }

  .cl-dash-launcher-info {
    display: flex;
    justify-content: space-between;
    padding: 10px 16px;
    font-size: 12px;
    color: var(--text-muted);
    background: var(--background-secondary);
  }

  .cl-dash-launcher-board {
    font-weight: 500;
    color: var(--text-normal);
  }

  .cl-dash-launcher-modes {
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .cl-dash-launcher-mode {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 10px 12px;
    background: var(--background-secondary);
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    cursor: pointer;
    text-align: left;
    transition: border-color 0.15s ease, background 0.15s ease;
  }

  .cl-dash-launcher-mode:hover {
    border-color: var(--interactive-accent);
    background: var(--background-modifier-hover);
  }

  .cl-dash-launcher-mode-name {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-normal);
  }

  .cl-dash-launcher-mode-desc {
    font-size: 11px;
    color: var(--text-muted);
    line-height: 1.4;
  }

  .cl-dash-launcher-coming-soon {
    padding: 20px 16px;
    text-align: center;
    color: var(--text-muted);
    font-size: 13px;
  }

  .cl-dash-launcher-coming-soon-hint {
    font-size: 11px;
    margin-top: 4px;
  }

  .cl-dash-launcher-back-btn {
    margin-top: 12px;
    padding: 6px 16px;
    font-size: 12px;
    background: var(--background-secondary);
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    color: var(--text-normal);
    cursor: pointer;
  }

  .cl-dash-launcher-back-btn:hover {
    background: var(--background-modifier-hover);
  }

  .cl-dash-launcher-tip {
    padding: 8px 16px;
    font-size: 11px;
    color: var(--text-faint);
    text-align: center;
    border-top: 1px solid var(--background-modifier-border);
  }
</style>
