<script lang="ts">
  /**
   * Canvas Learning System - Canvas View Component
   * Story 1.4: Main whiteboard viewport (AC-1, AC-3, AC-4, AC-5, AC-8)
   *
   * HTML + SVG mixed rendering:
   *   SVG layer → edges (bezier curves)
   *   HTML layer → nodes (contenteditable DOM)
   *   Overlay layer → selection box, temp edge line
   *
   * Performance: CSS contain, viewport culling, rAF throttle.
   */

  import { Notice } from 'obsidian';
  import type { CanvasNodeData, Point, Rect, Viewport } from '../../types/canvas';
  import { canvasState } from '../../stores/canvas-state';
  import { systemState } from '../../stores/system-state.svelte';
  import {
    screenToCanvas,
    zoomViewport,
    getVisibleRect,
    isNodeVisible,
    isEdgeVisible,
    rectsOverlap,
  } from '../../utils/canvas-math';
  import CanvasNode from './CanvasNode.svelte';
  import CanvasEdge from './CanvasEdge.svelte';
  import ImageNode from './ImageNode.svelte';
  import NodeStatusIndicator from './NodeStatusIndicator.svelte';
  import RecommendationBar from './RecommendationBar.svelte';
  import { decodePulloutDragData } from '../../services/pullout-service';
  import { PulloutService } from '../../services/pullout-service';
  import { getGenerationManager, type GenerationStatus } from '../../services/generation-manager';

  // ── Local state ────────────────────────────────────────────────────────

  let containerEl: HTMLDivElement | null = $state(null);
  let containerWidth = $state(800);
  let containerHeight = $state(600);

  // Pan state
  let isPanning = $state(false);
  let panStartX = $state(0);
  let panStartY = $state(0);
  let panStartVpX = $state(0);
  let panStartVpY = $state(0);

  // Selection box state
  let isBoxSelecting = $state(false);
  let boxStartScreen = $state<Point>({ x: 0, y: 0 });
  let boxCurrentScreen = $state<Point>({ x: 0, y: 0 });

  // Edge drag state
  let isDraggingEdge = $state(false);
  let edgeDragSourceId = $state<string | null>(null);
  let edgeDragStart = $state<Point>({ x: 0, y: 0 });
  let edgeDragEnd = $state<Point>({ x: 0, y: 0 });
  let edgeDragTargetId = $state<string | null>(null);

  // Story 3.7: Pullout service for drag-from-chat-to-canvas
  const pulloutService = new PulloutService();

  // Story 3.8: Generation manager for async status indicators
  const generationManager = getGenerationManager();
  let nodeStatusMap = $state(new Map<string, GenerationStatus>());

  // Subscribe to generation status changes
  $effect(() => {
    const unsub = generationManager.onStatusChange((nodeId, status) => {
      const updated = new Map(nodeStatusMap);
      if (status === 'idle') {
        updated.delete(nodeId);
      } else {
        updated.set(nodeId, status);
      }
      nodeStatusMap = updated;
    });
    return unsub;
  });

  // Force reactivity for canvasState changes
  let stateVersion = $state(0);

  $effect(() => {
    const unsub = canvasState.subscribe(() => {
      stateVersion++;
    });
    return unsub;
  });

  // ── Derived / computed ─────────────────────────────────────────────────

  let vp = $derived.by(() => {
    void stateVersion; // depend on state changes
    return canvasState.viewport;
  });

  let nodes = $derived.by(() => {
    void stateVersion;
    return canvasState.nodes;
  });

  let edges = $derived.by(() => {
    void stateVersion;
    return canvasState.edges;
  });

  // Node lookup map for edge rendering
  let nodesMap = $derived.by(() => {
    const map = new Map<string, CanvasNodeData>();
    for (const n of nodes) {
      map.set(n.id, n);
    }
    return map;
  });

  // Visible rect for culling
  let visibleRect = $derived.by(() => {
    return getVisibleRect(vp, containerWidth, containerHeight);
  });

  // Culled nodes & edges
  let visibleNodes = $derived.by(() => {
    return nodes.filter((n) => isNodeVisible(n, visibleRect));
  });

  let visibleEdges = $derived.by(() => {
    return edges.filter((e) =>
      isEdgeVisible(nodesMap.get(e.sourceNodeId), nodesMap.get(e.targetNodeId), visibleRect),
    );
  });

  // Selection box in canvas coordinates (for display)
  let selectionBoxStyle = $derived.by(() => {
    if (!isBoxSelecting) return '';
    const x = Math.min(boxStartScreen.x, boxCurrentScreen.x);
    const y = Math.min(boxStartScreen.y, boxCurrentScreen.y);
    const w = Math.abs(boxCurrentScreen.x - boxStartScreen.x);
    const h = Math.abs(boxCurrentScreen.y - boxStartScreen.y);
    return `left:${x}px;top:${y}px;width:${w}px;height:${h}px;`;
  });

  // ── Container resize observer ──────────────────────────────────────────

  $effect(() => {
    if (!containerEl) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        containerWidth = entry.contentRect.width;
        containerHeight = entry.contentRect.height;
      }
    });
    ro.observe(containerEl);
    return () => ro.disconnect();
  });

  // ── Mouse wheel zoom ──────────────────────────────────────────────────

  function handleWheel(e: WheelEvent) {
    e.preventDefault();
    if (!containerEl) return;

    const rect = containerEl.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const newVp = zoomViewport(vp, e.deltaY, mouseX, mouseY);
    canvasState.setViewport(newVp);
  }

  // ── Pan (right-click or middle-click drag) ─────────────────────────────

  function handleMouseDown(e: MouseEvent) {
    // Right-click (2) or middle-click (1) → pan
    if (e.button === 2 || e.button === 1) {
      e.preventDefault();
      isPanning = true;
      panStartX = e.clientX;
      panStartY = e.clientY;
      panStartVpX = vp.x;
      panStartVpY = vp.y;

      document.addEventListener('mousemove', handlePanMove);
      document.addEventListener('mouseup', handlePanUp);
      return;
    }

    // Left-click on blank → start box select
    if (e.button === 0 && e.target === containerEl) {
      // Clear selection if not Ctrl-clicking
      if (!e.ctrlKey && !e.metaKey) {
        canvasState.clearSelection();
      }

      isBoxSelecting = true;
      boxStartScreen.x = e.clientX - (containerEl?.getBoundingClientRect().left ?? 0);
      boxStartScreen.y = e.clientY - (containerEl?.getBoundingClientRect().top ?? 0);
      boxCurrentScreen.x = boxStartScreen.x;
      boxCurrentScreen.y = boxStartScreen.y;

      document.addEventListener('mousemove', handleBoxSelectMove);
      document.addEventListener('mouseup', handleBoxSelectUp);
    }
  }

  function handlePanMove(e: MouseEvent) {
    if (!isPanning) return;
    const dx = e.clientX - panStartX;
    const dy = e.clientY - panStartY;
    canvasState.setViewport({
      x: panStartVpX + dx,
      y: panStartVpY + dy,
      zoom: vp.zoom,
    });
  }

  function handlePanUp() {
    isPanning = false;
    document.removeEventListener('mousemove', handlePanMove);
    document.removeEventListener('mouseup', handlePanUp);
  }

  // ── Box selection ──────────────────────────────────────────────────────

  function handleBoxSelectMove(e: MouseEvent) {
    if (!isBoxSelecting || !containerEl) return;
    const rect = containerEl.getBoundingClientRect();
    boxCurrentScreen.x = e.clientX - rect.left;
    boxCurrentScreen.y = e.clientY - rect.top;

    // Compute selection in canvas coords
    const s1 = screenToCanvas(boxStartScreen.x, boxStartScreen.y, vp);
    const s2 = screenToCanvas(boxCurrentScreen.x, boxCurrentScreen.y, vp);

    const selRect: Rect = {
      x: Math.min(s1.x, s2.x),
      y: Math.min(s1.y, s2.y),
      width: Math.abs(s2.x - s1.x),
      height: Math.abs(s2.y - s1.y),
    };

    const selected = new Set<string>();
    for (const n of nodes) {
      const nodeRect: Rect = { x: n.x, y: n.y, width: n.width, height: n.height };
      if (rectsOverlap(selRect, nodeRect)) {
        selected.add(n.id);
      }
    }
    canvasState.setSelectedNodeIds(selected);
  }

  function handleBoxSelectUp() {
    isBoxSelecting = false;
    document.removeEventListener('mousemove', handleBoxSelectMove);
    document.removeEventListener('mouseup', handleBoxSelectUp);
  }

  // ── Double-click → create node ─────────────────────────────────────────

  function handleDoubleClick(e: MouseEvent) {
    if (e.target !== containerEl) return;
    if (!containerEl) return;

    const rect = containerEl.getBoundingClientRect();
    const screenX = e.clientX - rect.left;
    const screenY = e.clientY - rect.top;
    const canvasPos = screenToCanvas(screenX, screenY, vp);

    canvasState.addNode({
      x: canvasPos.x - 100, // center the 200px-wide node
      y: canvasPos.y - 30,
    });
  }

  // ── Edge drag (from node port) ─────────────────────────────────────────

  function handleEdgeDragStart(sourceNodeId: string, e: MouseEvent) {
    if (!containerEl) return;
    isDraggingEdge = true;
    edgeDragSourceId = sourceNodeId;

    const rect = containerEl.getBoundingClientRect();
    const sourceNode = nodesMap.get(sourceNodeId);
    if (sourceNode) {
      edgeDragStart = {
        x: sourceNode.x + sourceNode.width / 2,
        y: sourceNode.y + sourceNode.height / 2,
      };
    }
    edgeDragEnd = screenToCanvas(e.clientX - rect.left, e.clientY - rect.top, vp);
    edgeDragTargetId = null;

    document.addEventListener('mousemove', handleEdgeDragMove);
    document.addEventListener('mouseup', handleEdgeDragUp);
  }

  function handleEdgeDragMove(e: MouseEvent) {
    if (!isDraggingEdge || !containerEl) return;

    const rect = containerEl.getBoundingClientRect();
    const canvasPos = screenToCanvas(e.clientX - rect.left, e.clientY - rect.top, vp);
    edgeDragEnd = canvasPos;

    // Check if hovering over a target node
    edgeDragTargetId = null;
    for (const n of nodes) {
      if (n.id === edgeDragSourceId) continue;
      if (
        canvasPos.x >= n.x &&
        canvasPos.x <= n.x + n.width &&
        canvasPos.y >= n.y &&
        canvasPos.y <= n.y + n.height
      ) {
        edgeDragTargetId = n.id;
        break;
      }
    }
  }

  function handleEdgeDragUp() {
    if (isDraggingEdge && edgeDragSourceId && edgeDragTargetId) {
      canvasState.addEdge({
        sourceNodeId: edgeDragSourceId,
        targetNodeId: edgeDragTargetId,
      });
    }

    isDraggingEdge = false;
    edgeDragSourceId = null;
    edgeDragTargetId = null;
    document.removeEventListener('mousemove', handleEdgeDragMove);
    document.removeEventListener('mouseup', handleEdgeDragUp);
  }

  // ── Keyboard events ────────────────────────────────────────────────────

  function handleKeyDown(e: KeyboardEvent) {
    // Don't handle keys when editing a node body
    const tag = (e.target as HTMLElement)?.tagName;
    const editable = (e.target as HTMLElement)?.isContentEditable;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || editable) return;

    if (e.key === 'Delete' || e.key === 'Backspace') {
      // Stop propagation to prevent Obsidian from intercepting
      e.stopPropagation();
      e.preventDefault();
      canvasState.deleteSelected();
    } else if (e.key === 'a' && (e.ctrlKey || e.metaKey)) {
      e.stopPropagation();
      e.preventDefault();
      canvasState.selectAll();
    } else if (e.key === 'Escape') {
      canvasState.clearSelection();
    }
  }

  // ── Story 1.6: Image paste and drop ──────────────────────────────────

  /** Convert a Blob image to base64 DataURL. */
  function blobToDataUrl(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = () => reject(reader.error);
      reader.readAsDataURL(blob);
    });
  }

  /** Max image size in bytes (10 MB). */
  const MAX_IMAGE_SIZE = 10 * 1024 * 1024;

  async function createImageNode(file: Blob, position?: Point): Promise<void> {
    if (file.size > MAX_IMAGE_SIZE) {
      new Notice('图片过大（> 10MB），请压缩后重试', 5000);
      return;
    }

    const dataUrl = await blobToDataUrl(file);
    const pos = position ?? screenToCanvas(
      containerWidth / 2, containerHeight / 2, vp,
    );

    const node = await canvasState.addNode({
      type: 'image',
      imageData: dataUrl,
      indexStatus: 'indexing',
      x: pos.x - 120,
      y: pos.y - 80,
      width: 240,
      height: 180,
    });

    // Dispatch custom event for IndexingService to pick up
    containerEl?.dispatchEvent(
      new CustomEvent('cl-image-index-request', {
        detail: { nodeId: node.id, imageData: dataUrl },
      }),
    );
  }

  function handlePaste(event: ClipboardEvent) {
    const items = event.clipboardData?.items;
    if (!items) return;

    // Check for text content first — if clipboard has text, let the
    // default contenteditable paste handle it (or create a text node)
    for (const item of items) {
      if (item.type === 'text/plain' || item.type === 'text/html') {
        // Text is present — don't treat as image paste.
        // If the paste target is a contenteditable node body, let it through.
        // If pasting on the canvas background, create a text node.
        const tag = (event.target as HTMLElement)?.tagName;
        const editable = (event.target as HTMLElement)?.isContentEditable;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || editable) {
          return; // let default paste behavior handle it
        }

        // Pasting text on canvas background — create a new text node
        event.preventDefault();
        item.getAsString((text) => {
          if (text.trim()) {
            const pos = screenToCanvas(containerWidth / 2, containerHeight / 2, vp);
            canvasState.addNode({
              content: text,
              x: pos.x - 100,
              y: pos.y - 30,
            });
          }
        });
        return;
      }
    }

    // No text found — check for images
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        event.preventDefault();
        const blob = item.getAsFile();
        if (blob) createImageNode(blob);
      }
    }
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = 'copy';
    }
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    if (!event.dataTransfer || !containerEl) return;

    const rect = containerEl.getBoundingClientRect();

    // Story 3.7: Check for pullout drag data first
    const pulloutData = decodePulloutDragData(event.dataTransfer);
    if (pulloutData) {
      const dropPos = screenToCanvas(
        event.clientX - rect.left,
        event.clientY - rect.top,
        vp,
      );

      pulloutService.createPulloutNode(
        pulloutData.content,
        dropPos,
        {
          sourceNodeId: pulloutData.sourceNodeId,
          sourceMessageId: pulloutData.sourceMessageId,
          timestamp: pulloutData.timestamp,
        },
      ).then((result) => {
        new Notice('Node created from dialogue', 2000);
      }).catch((err) => {
        console.warn('[Canvas Learning] Pullout node creation failed:', err);
      });
      return;
    }

    // Story 1.6: Image file drop handling
    const files = event.dataTransfer.files;
    if (!files) return;

    let offsetX = 0;

    for (const file of files) {
      if (file.type.startsWith('image/')) {
        const dropPos = screenToCanvas(
          event.clientX - rect.left + offsetX,
          event.clientY - rect.top,
          vp,
        );
        createImageNode(file, dropPos);
        offsetX += 260; // 240px width + 20px gap
      }
    }
  }

  // ── Story 1.6: Image index retry ─────────────────────────────────────

  function handleRetryIndex(nodeId: string) {
    containerEl?.dispatchEvent(
      new CustomEvent('cl-image-retry-index', { detail: { nodeId } }),
    );
  }

  // ── Story 1.7: Recommendation handlers ──────────────────────────────

  let recStateVersion = $state(0);
  $effect(() => {
    const unsub = canvasState.subscribe(() => {
      recStateVersion++;
    });
    return unsub;
  });

  let recommendations = $derived.by(() => {
    void recStateVersion;
    return canvasState.recommendations;
  });

  let showRecommendationBar = $derived.by(() => {
    void recStateVersion;
    return canvasState.recommendationBarVisible && !canvasState.dismissedSessionClosed;
  });

  function handleAcceptRecommendation(recId: string) {
    canvasState.acceptRecommendation(recId);
    new Notice('已创建连线', 2000);
  }

  function handleDismissRecommendation(recId: string) {
    canvasState.dismissRecommendation(recId);
  }

  function handleCloseRecommendationBar() {
    canvasState.closeRecommendationBar();
  }

  // ── Context menu prevention (for right-click pan) ──────────────────────

  function handleContextMenu(e: Event) {
    e.preventDefault();
  }
</script>

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<div
  bind:this={containerEl}
  class="cl-canvas-viewport"
  onwheel={handleWheel}
  onmousedown={handleMouseDown}
  ondblclick={handleDoubleClick}
  onkeydown={handleKeyDown}
  oncontextmenu={handleContextMenu}
  onpaste={handlePaste}
  ondragover={handleDragOver}
  ondrop={handleDrop}
  role="application"
  tabindex="0"
  aria-label="Canvas whiteboard"
>
  <!-- SVG layer: edges -->
  <svg
    class="cl-canvas-edges-layer"
    style="transform: translate({vp.x}px, {vp.y}px) scale({vp.zoom});"
  >
    {#each visibleEdges as edge (edge.id)}
      <CanvasEdge
        {edge}
        sourceNode={nodesMap.get(edge.sourceNodeId)}
        targetNode={nodesMap.get(edge.targetNodeId)}
      />
    {/each}

    <!-- Temp edge while dragging -->
    {#if isDraggingEdge}
      <line
        class="cl-canvas-temp-edge"
        x1={edgeDragStart.x}
        y1={edgeDragStart.y}
        x2={edgeDragEnd.x}
        y2={edgeDragEnd.y}
        stroke="var(--interactive-accent)"
        stroke-width="2"
        stroke-dasharray="6 3"
      />
    {/if}
  </svg>

  <!-- HTML layer: nodes -->
  <div
    class="cl-canvas-nodes-layer"
    style="transform: translate({vp.x}px, {vp.y}px) scale({vp.zoom}); transform-origin: 0 0;"
  >
    {#each visibleNodes as node (node.id)}
      {#if node.type === 'image'}
        <ImageNode {node} onedgedragstart={handleEdgeDragStart} onretryindex={handleRetryIndex} />
      {:else}
        <CanvasNode {node} onedgedragstart={handleEdgeDragStart} />
      {/if}
    {/each}
  </div>

  <!-- Selection box overlay -->
  {#if isBoxSelecting}
    <div class="cl-canvas-selection-box" style={selectionBoxStyle}></div>
  {/if}

  <!-- Story 1.7: Recommendation bar -->
  {#if showRecommendationBar}
    <RecommendationBar
      {recommendations}
      onaccept={handleAcceptRecommendation}
      ondismiss={handleDismissRecommendation}
      onclose={handleCloseRecommendationBar}
    />
  {/if}
</div>

<style>
  .cl-canvas-viewport {
    position: relative;
    width: 100%;
    height: 100%;
    overflow: hidden;
    contain: layout style paint;
    background-color: var(--background-primary);
    /* Dot grid background */
    background-image: radial-gradient(
      circle,
      var(--background-modifier-border) 1px,
      transparent 1px
    );
    background-size: 20px 20px;
    cursor: default;
    outline: none;
  }

  .cl-canvas-edges-layer {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    overflow: visible;
    pointer-events: none;
    transform-origin: 0 0;
  }

  .cl-canvas-edges-layer :global(g),
  .cl-canvas-edges-layer :global(path),
  .cl-canvas-edges-layer :global(polygon),
  .cl-canvas-edges-layer :global(foreignObject) {
    pointer-events: auto;
  }

  .cl-canvas-temp-edge {
    pointer-events: none;
  }

  .cl-canvas-nodes-layer {
    position: absolute;
    top: 0;
    left: 0;
    width: 0;
    height: 0;
  }

  .cl-canvas-selection-box {
    position: absolute;
    background: rgba(var(--interactive-accent-rgb, 68, 128, 255), 0.1);
    border: 1px solid var(--interactive-accent);
    pointer-events: none;
    z-index: 1000;
  }
</style>
