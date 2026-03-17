<!--
  Canvas Learning System - Edge Label Editor (Fallback)
  Story 4.4: Edge Dialog Fallback — Static Label Editing (AC-1)

  A lightweight popup input for manual label editing.
  Used when Agent is unavailable (degraded mode).
  Saves label to Edge's label property (IndexedDB → Neo4j delta sync).

  CSS prefix: cl-canvas-edge-label-editor (E group — canvas layer)

  [Source: _bmad-output/implementation-artifacts/4-4-edge-dialog-fallback.md#Task 3]
-->
<script lang="ts">
  import { canvasState } from '../../stores/canvas-state';
  import { Notice } from 'obsidian';

  // Props
  let {
    edgeId,
    currentLabel = '',
    x,
    y,
    onClose,
  }: {
    edgeId: string;
    currentLabel?: string;
    x: number;
    y: number;
    onClose: () => void;
  } = $props();

  // Local state
  let labelValue = $state(currentLabel);
  let inputEl: HTMLInputElement | null = $state(null);

  // Focus the input after mounting
  $effect(() => {
    requestAnimationFrame(() => {
      inputEl?.focus();
    });
  });

  function commitLabel(): void {
    const trimmed = labelValue.trim();
    if (trimmed !== currentLabel) {
      canvasState.updateEdge(edgeId, { label: trimmed });
    }
    onClose();
  }

  function handleKeydown(e: KeyboardEvent): void {
    if (e.key === 'Enter') {
      e.preventDefault();
      commitLabel();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  }

  function handleBlur(): void {
    commitLabel();
  }
</script>

<foreignObject
  x={x - 80}
  y={y - 16}
  width="160"
  height="32"
>
  <div class="cl-canvas-edge-label-editor">
    <!-- Story 4.4 AC-2: Degraded mode notice bar -->
    <div class="cl-canvas-edge-label-editor__notice">
      手动标签模式
    </div>
    <input
      bind:this={inputEl}
      type="text"
      class="cl-canvas-edge-label-editor__input"
      placeholder="输入关系标签..."
      bind:value={labelValue}
      onkeydown={handleKeydown}
      onblur={handleBlur}
    />
  </div>
</foreignObject>

<style>
  .cl-canvas-edge-label-editor {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .cl-canvas-edge-label-editor__notice {
    font-size: 9px;
    color: var(--text-warning, #e2b93d);
    text-align: center;
    line-height: 1;
  }

  .cl-canvas-edge-label-editor__input {
    width: 100%;
    height: 24px;
    font-size: 12px;
    font-family: var(--font-text-theme);
    text-align: center;
    border: 1px solid var(--text-warning, #e2b93d);
    border-radius: var(--radius-s, 4px);
    background: var(--background-primary);
    color: var(--text-normal);
    outline: none;
    padding: 0 4px;
    box-sizing: border-box;
  }

  .cl-canvas-edge-label-editor__input:focus {
    border-color: var(--interactive-accent);
    box-shadow: 0 0 0 2px var(--interactive-accent-hover, rgba(0, 0, 0, 0.1));
  }

  .cl-canvas-edge-label-editor__input::placeholder {
    color: var(--text-faint);
    font-style: italic;
  }
</style>
