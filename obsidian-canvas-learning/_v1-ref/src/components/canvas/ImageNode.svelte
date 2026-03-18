<script lang="ts">
  /**
   * Canvas Learning System - Image Node Component
   * Story 1.6: Image node with thumbnail, index status indicator (AC-1~AC-8)
   *
   * Structure:
   *   Header -> drag handle
   *   Body -> image thumbnail
   *   Status bar -> indexing/indexed/failed indicator
   *   Ports -> edge creation anchors
   */

  import type { CanvasNodeData } from '../../types/canvas';
  import { canvasState } from '../../stores/canvas-state';

  // Props
  let {
    node,
    onedgedragstart,
    onretryindex,
  }: {
    node: CanvasNodeData;
    onedgedragstart?: (nodeId: string, e: MouseEvent) => void;
    onretryindex?: (nodeId: string) => void;
  } = $props();

  // Local state
  let isDragging = $state(false);
  let showStatus = $state(true);
  let fadeoutTimer: ReturnType<typeof setTimeout> | null = $state(null);

  // Derived
  let isSelected = $derived(canvasState.selectedNodeIds.has(node.id));

  // Auto-fadeout when indexed
  $effect(() => {
    if (node.indexStatus === 'indexed') {
      fadeoutTimer = setTimeout(() => {
        showStatus = false;
      }, 3000);
    } else {
      showStatus = true;
      if (fadeoutTimer) {
        clearTimeout(fadeoutTimer);
        fadeoutTimer = null;
      }
    }
    return () => {
      if (fadeoutTimer) clearTimeout(fadeoutTimer);
    };
  });

  // ── Node drag (header) ──────────────────────────────────────────────────

  function startDrag(e: MouseEvent) {
    if (e.button !== 0) return;
    e.stopPropagation();
    e.preventDefault();

    if (!canvasState.selectedNodeIds.has(node.id)) {
      canvasState.selectNode(node.id, e.ctrlKey || e.metaKey);
    }

    isDragging = true;

    const startX = e.clientX;
    const startY = e.clientY;
    const zoom = canvasState.viewport.zoom;

    const dragNodes = [...canvasState.selectedNodeIds].map((id) => {
      const n = canvasState.getNodeById(id);
      return n ? { id: n.id, startX: n.x, startY: n.y } : null;
    }).filter(Boolean) as { id: string; startX: number; startY: number }[];

    let rafId: number | null = null;

    function onMouseMove(ev: MouseEvent) {
      if (rafId !== null) return;
      rafId = requestAnimationFrame(() => {
        const dx = (ev.clientX - startX) / zoom;
        const dy = (ev.clientY - startY) / zoom;
        for (const dn of dragNodes) {
          canvasState.updateNode(dn.id, { x: dn.startX + dx, y: dn.startY + dy }, true);
        }
        rafId = null;
      });
    }

    function onMouseUp() {
      isDragging = false;
      if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null; }
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    }

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }

  function handleNodeClick(e: MouseEvent) {
    e.stopPropagation();
    canvasState.selectNode(node.id, e.ctrlKey || e.metaKey);
  }

  function handlePortMouseDown(e: MouseEvent) {
    e.stopPropagation();
    e.preventDefault();
    onedgedragstart?.(node.id, e);
  }

  function handleRetryClick(e: MouseEvent) {
    e.stopPropagation();
    onretryindex?.(node.id);
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div
  class="cl-canvas-node cl-canvas-node--image"
  class:cl-canvas-node--selected={isSelected}
  class:cl-canvas-node--dragging={isDragging}
  style="left: {node.x}px; top: {node.y}px; width: {node.width}px;"
  onclick={handleNodeClick}
  role="group"
  tabindex="-1"
>
  <!-- Header: drag handle -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="cl-canvas-node-header" onmousedown={startDrag}>
    {node.title || '图片节点'}
  </div>

  <!-- Body: image thumbnail -->
  <div class="cl-canvas-node-body cl-canvas-node-body--image">
    {#if node.imageData}
      <img
        src={node.imageData}
        alt={node.title || '图片'}
        class="cl-image-node-thumbnail"
        loading="lazy"
      />
    {/if}
  </div>

  <!-- Index status bar -->
  {#if showStatus && node.indexStatus && node.indexStatus !== 'none'}
    <div
      class="cl-image-node-index-status"
      class:cl-image-node-index-status--indexing={node.indexStatus === 'indexing'}
      class:cl-image-node-index-status--indexed={node.indexStatus === 'indexed'}
      class:cl-image-node-index-status--failed={node.indexStatus === 'failed'}
      class:cl-image-node-index-status--fadeout={node.indexStatus === 'indexed' && !showStatus}
    >
      {#if node.indexStatus === 'indexing'}
        <span class="cl-image-node-spinner">&#x1f504;</span> 索引建立中...
      {:else if node.indexStatus === 'indexed'}
        <span class="cl-image-node-check">&#x2705;</span> 已加入搜索索引
      {:else if node.indexStatus === 'failed'}
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <span class="cl-image-node-warn" onclick={handleRetryClick}>&#x26a0;&#xfe0f; 索引失败，点击重试</span>
      {/if}
    </div>
  {/if}

  <!-- Edge ports -->
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
  .cl-canvas-node--image {
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
  }

  .cl-canvas-node-body--image {
    padding: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .cl-image-node-thumbnail {
    max-width: 100%;
    border-radius: var(--radius-s, 4px);
    display: block;
  }

  .cl-image-node-index-status {
    font-size: var(--font-smaller, 11px);
    color: var(--text-muted);
    padding: 4px 8px;
    border-top: 1px solid var(--background-modifier-border);
    transition: opacity 0.5s ease-out;
  }

  .cl-image-node-index-status--indexing {
    animation: cl-pulse 1.5s ease-in-out infinite;
  }

  .cl-image-node-index-status--failed {
    color: var(--text-error);
    cursor: pointer;
  }

  .cl-image-node-index-status--fadeout {
    opacity: 0;
    pointer-events: none;
  }

  @keyframes cl-pulse {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
  }

  .cl-image-node-spinner {
    display: inline-block;
    animation: cl-spin 2s linear infinite;
  }

  @keyframes cl-spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>
