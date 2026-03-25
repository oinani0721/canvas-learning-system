<script lang="ts">
  /**
   * Canvas Learning System - Canvas Node Component
   * Story 1.4: Text node with header drag, body edit, edge ports (AC-1, AC-2, AC-3, AC-5)
   * Integrates Story 5.2 mastery color indicator (pre-existing).
   *
   * Structure:
   *   Header → drag handle (cursor: grab)
   *   Body → contenteditable text (cursor: text)
   *   Ports → edge creation anchors on four sides
   */

  import type { CanvasNodeData } from '../../types/canvas';
  import { canvasState } from '../../stores/canvas-state';
  import NodeColorIndicator from './NodeColorIndicator.svelte';
  import { masteryState } from '../../stores/mastery-state.svelte';
  import { getMasteryBorderClass } from '../../utils/mastery-color';

  // Props
  let {
    node,
    onedgedragstart,
  }: {
    node: CanvasNodeData;
    onedgedragstart?: (nodeId: string, e: MouseEvent) => void;
  } = $props();

  // Local state
  let isEditing = $state(false);
  let isDragging = $state(false);
  let bodyEl: HTMLDivElement | null = $state(null);

  // Derived
  let isSelected = $derived(canvasState.selectedNodeIds.has(node.id));

  // Story 5.2: mastery border class — empty for unlearned (no border override)
  let masteryStatus = $derived(masteryState.getNodeStatus(node.id));
  let masteryBorderClass = $derived(
    masteryStatus !== 'unlearned' ? getMasteryBorderClass(masteryStatus) : '',
  );

  // ── Node drag (header) ───────────────────────────────────────────────

  function startDrag(e: MouseEvent) {
    if (e.button !== 0) return;
    e.stopPropagation();
    e.preventDefault();

    // If this node isn't selected, select it exclusively
    if (!canvasState.selectedNodeIds.has(node.id)) {
      canvasState.selectNode(node.id, e.ctrlKey || e.metaKey);
    }

    isDragging = true;

    const startX = e.clientX;
    const startY = e.clientY;
    const zoom = canvasState.viewport.zoom;

    // Snapshot starting positions of all selected nodes
    const dragNodes = [...canvasState.selectedNodeIds].map((id) => {
      const n = canvasState.getNodeById(id);
      return n ? { id: n.id, startX: n.x, startY: n.y } : null;
    }).filter(Boolean) as { id: string; startX: number; startY: number }[];

    let rafId: number | null = null;

    function onMouseMove(ev: MouseEvent) {
      if (rafId !== null) return; // throttle to rAF
      rafId = requestAnimationFrame(() => {
        const dx = (ev.clientX - startX) / zoom;
        const dy = (ev.clientY - startY) / zoom;

        for (const dn of dragNodes) {
          canvasState.updateNode(
            dn.id,
            { x: dn.startX + dx, y: dn.startY + dy },
            true, // immediate — no debounce for position
          );
        }
        rafId = null;
      });
    }

    function onMouseUp() {
      isDragging = false;
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    }

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }

  // ── Node selection ────────────────────────────────────────────────────

  function handleNodeClick(e: MouseEvent) {
    e.stopPropagation();
    if (!isEditing) {
      canvasState.selectNode(node.id, e.ctrlKey || e.metaKey);
    }
  }

  // ── Double-click header → open chat panel (Story 3.3) ──────────────

  function handleHeaderDoubleClick(e: MouseEvent) {
    e.stopPropagation();
    e.preventDefault();
    canvasState.openNodeChat(node.id, node.title || node.content.slice(0, 30) || node.id);
  }

  // ── Body editing ──────────────────────────────────────────────────────

  function startEditing(e: MouseEvent) {
    e.stopPropagation();
    isEditing = true;
    // Select this node (non-additive) when clicking body
    if (!canvasState.selectedNodeIds.has(node.id)) {
      canvasState.selectNode(node.id, false);
    }
  }

  function handleBodyInput() {
    if (bodyEl) {
      const content = bodyEl.innerText;
      canvasState.updateNode(node.id, { content }); // debounced
    }
  }

  function handleBodyKeydown(e: KeyboardEvent) {
    // Prevent Delete/Backspace from deleting the node while editing
    if (e.key === 'Delete' || e.key === 'Backspace') {
      e.stopPropagation();
    }
    // Escape exits editing
    if (e.key === 'Escape') {
      isEditing = false;
      bodyEl?.blur();
    }
  }

  function handleBodyBlur() {
    isEditing = false;
  }

  // ── Edge port drag ────────────────────────────────────────────────────

  function handlePortMouseDown(e: MouseEvent) {
    e.stopPropagation();
    e.preventDefault();
    onedgedragstart?.(node.id, e);
  }

  // ── Auto-focus on newly created node ──────────────────────────────────

  $effect(() => {
    if (node.content === '' && node.title === '' && bodyEl && !isEditing) {
      isEditing = true;
      requestAnimationFrame(() => {
        bodyEl?.focus();
      });
    }
  });
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div
  class="cl-canvas-node {masteryBorderClass}"
  class:cl-canvas-node--selected={isSelected}
  class:cl-canvas-node--dragging={isDragging}
  style="left: {node.x}px; top: {node.y}px; width: {node.width}px;"
  onclick={handleNodeClick}
  role="group"
  tabindex="-1"
>
  <!-- Story 5.2 mastery color indicator -->
  <NodeColorIndicator nodeId={node.id} />

  <!-- Header: drag handle (double-click → open chat) -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="cl-canvas-node-header"
    onmousedown={startDrag}
    ondblclick={handleHeaderDoubleClick}
  >
    {node.title || '未命名节点'}
  </div>

  <!-- Body: content editing -->
  <div
    bind:this={bodyEl}
    class="cl-canvas-node-body"
    contenteditable={isEditing ? 'true' : 'false'}
    oninput={handleBodyInput}
    onmousedown={startEditing}
    onkeydown={handleBodyKeydown}
    onblur={handleBodyBlur}
    role="textbox"
    tabindex="0"
  >
    {node.content}
  </div>

  <!-- Edge ports (four sides) -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="cl-canvas-node-port cl-canvas-node-port--top" onmousedown={handlePortMouseDown}></div>
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="cl-canvas-node-port cl-canvas-node-port--right" onmousedown={handlePortMouseDown}></div>
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="cl-canvas-node-port cl-canvas-node-port--bottom" onmousedown={handlePortMouseDown}></div>
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="cl-canvas-node-port cl-canvas-node-port--left" onmousedown={handlePortMouseDown}></div>
</div>

<style>
  .cl-canvas-node {
    position: absolute;
    background: var(--background-secondary);
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    min-height: 60px;
    display: flex;
    flex-direction: column;
    contain: layout style paint;
    user-select: none;
    transition: var(--cl-mastery-transition, border-color 0.15s ease);
  }

  .cl-canvas-node--selected {
    border-color: var(--interactive-accent);
    box-shadow: 0 0 0 2px var(--interactive-accent);
  }

  .cl-canvas-node--dragging {
    opacity: 0.85;
    z-index: 100;
  }

  .cl-canvas-node-header {
    padding: 6px 10px;
    font-size: 13px;
    font-weight: 600;
    color: var(--text-normal);
    cursor: grab;
    border-bottom: 1px solid var(--background-modifier-border);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    user-select: none;
  }

  .cl-canvas-node-header:active {
    cursor: grabbing;
  }

  .cl-canvas-node-body {
    flex: 1;
    padding: 8px 10px;
    font-size: 13px;
    color: var(--text-normal);
    cursor: text;
    min-height: 30px;
    outline: none;
    white-space: pre-wrap;
    word-break: break-word;
    user-select: text;
  }

  .cl-canvas-node-body[contenteditable='true'] {
    background: var(--background-primary-alt, var(--background-primary));
  }

  /* Edge connection ports */
  .cl-canvas-node-port {
    position: absolute;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--interactive-accent);
    border: 2px solid var(--background-primary);
    opacity: 0;
    transition: opacity 0.15s ease;
    cursor: crosshair;
    z-index: 10;
  }

  .cl-canvas-node:hover .cl-canvas-node-port {
    opacity: 1;
  }

  .cl-canvas-node-port--top {
    top: -6px;
    left: 50%;
    transform: translateX(-50%);
  }

  .cl-canvas-node-port--right {
    right: -6px;
    top: 50%;
    transform: translateY(-50%);
  }

  .cl-canvas-node-port--bottom {
    bottom: -6px;
    left: 50%;
    transform: translateX(-50%);
  }

  .cl-canvas-node-port--left {
    left: -6px;
    top: 50%;
    transform: translateY(-50%);
  }

  /* Story 5.2 mastery border color overrides */
  .cl-canvas-node:global(.cl-mastery-learning-border) {
    border-color: var(--cl-mastery-learning-border);
  }
  .cl-canvas-node:global(.cl-mastery-weak-border) {
    border-color: var(--cl-mastery-weak-border);
  }
  .cl-canvas-node:global(.cl-mastery-mastered-border) {
    border-color: var(--cl-mastery-mastered-border);
  }
  .cl-canvas-node:global(.cl-mastery-review-border) {
    border-color: var(--cl-mastery-review-border);
  }
</style>
