<script lang="ts">
  /**
   * Canvas Learning System - Canvas Edge Component
   * Story 1.4: SVG bezier edge with arrow, label, and selection (AC-4)
   * Story 4.1: EdgeDialogTrigger integration (AC-1, AC-2)
   * Story 4.4: EdgeLabelEditor fallback integration (AC-1)
   */

  import type { CanvasEdgeData, CanvasNodeData } from '../../types/canvas';
  import { canvasState } from '../../stores/canvas-state';
  import {
    calculateBezierPath,
    calculateArrowPoints,
    getBezierMidpoint,
  } from '../../utils/canvas-math';
  import EdgeDialogTrigger from './EdgeDialogTrigger.svelte';
  import EdgeLabelEditor from './EdgeLabelEditor.svelte';

  // Props
  let {
    edge,
    sourceNode,
    targetNode,
  }: {
    edge: CanvasEdgeData;
    sourceNode: CanvasNodeData | undefined;
    targetNode: CanvasNodeData | undefined;
  } = $props();

  // Local state
  let isEditingLabel = $state(false);
  let labelInputValue = $state('');
  let labelInputEl: HTMLInputElement | null = $state(null);
  /** Story 4.4: Whether the fallback label editor is open. */
  let isFallbackEditing = $state(false);

  // Derived
  let isSelected = $derived(canvasState.selectedEdgeIds.has(edge.id));

  let pathD = $derived.by(() => {
    if (!sourceNode || !targetNode) return '';
    return calculateBezierPath(sourceNode, targetNode);
  });

  let arrowPts = $derived.by(() => {
    if (!sourceNode || !targetNode) return '';
    return calculateArrowPoints(sourceNode, targetNode);
  });

  let midpoint = $derived.by(() => {
    if (!sourceNode || !targetNode) return { x: 0, y: 0 };
    return getBezierMidpoint(sourceNode, targetNode);
  });

  // ── Handlers ─────────────────────────────────────────────────────────

  function handleClick(e: MouseEvent) {
    e.stopPropagation();
    canvasState.selectEdge(edge.id, e.ctrlKey || e.metaKey);
  }

  function handleDoubleClick(e: MouseEvent) {
    e.stopPropagation();
    isEditingLabel = true;
    labelInputValue = edge.label;
    // Focus the input after it appears
    requestAnimationFrame(() => {
      labelInputEl?.focus();
    });
  }

  function commitLabel() {
    if (isEditingLabel) {
      isEditingLabel = false;
      canvasState.updateEdge(edge.id, { label: labelInputValue });
    }
  }

  function handleLabelKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      e.preventDefault();
      commitLabel();
    } else if (e.key === 'Escape') {
      isEditingLabel = false;
    }
  }

  /**
   * Story 4.4 AC-1: Open fallback label editor when Agent is unavailable.
   */
  function handleFallbackEdit(_edgeId: string): void {
    isFallbackEditing = true;
  }

  function closeFallbackEditor(): void {
    isFallbackEditing = false;
  }
</script>

{#if sourceNode && targetNode}
  <g class="cl-canvas-edge" class:cl-canvas-edge--selected={isSelected}>
    <!-- Visible bezier curve -->
    <path
      d={pathD}
      class="cl-canvas-edge-path"
      stroke={isSelected ? 'var(--interactive-accent)' : 'var(--text-muted)'}
      fill="none"
      stroke-width={isSelected ? 3 : 2}
    />

    <!-- Arrowhead -->
    {#if arrowPts}
      <polygon
        points={arrowPts}
        fill={isSelected ? 'var(--interactive-accent)' : 'var(--text-muted)'}
      />
    {/if}

    <!-- Invisible wide path for easier clicking -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <path
      d={pathD}
      stroke="transparent"
      fill="none"
      stroke-width="16"
      style="cursor: pointer;"
      onclick={handleClick}
      ondblclick={handleDoubleClick}
      role="button"
      tabindex="-1"
    />

    <!-- Label -->
    {#if edge.label && !isEditingLabel && !isFallbackEditing}
      <text
        x={midpoint.x}
        y={midpoint.y - 8}
        class="cl-canvas-edge-label"
        text-anchor="middle"
        dominant-baseline="auto"
      >
        {edge.label}
      </text>
    {/if}

    <!--
      Story 4.1 AC-1: EdgeDialogTrigger — clickable icon at edge midpoint.
      Positioned slightly below the label area so they don't overlap.
    -->
    {#if !isEditingLabel && !isFallbackEditing}
      <EdgeDialogTrigger
        edgeId={edge.id}
        sourceNodeId={edge.sourceNodeId}
        targetNodeId={edge.targetNodeId}
        sourceNodeName={sourceNode.title || sourceNode.id}
        targetNodeName={targetNode.title || targetNode.id}
        midpointX={midpoint.x}
        midpointY={edge.label ? midpoint.y + 14 : midpoint.y}
        visible={true}
        onFallbackEdit={handleFallbackEdit}
      />
    {/if}
  </g>
{/if}

<!-- Label edit input (positioned via foreignObject or overlay) -->
{#if isEditingLabel}
  <foreignObject
    x={midpoint.x - 60}
    y={midpoint.y - 16}
    width="120"
    height="28"
  >
    <input
      bind:this={labelInputEl}
      type="text"
      class="cl-canvas-edge-label-input"
      bind:value={labelInputValue}
      onkeydown={handleLabelKeydown}
      onblur={commitLabel}
    />
  </foreignObject>
{/if}

<!-- Story 4.4 AC-1: Fallback static label editor -->
{#if isFallbackEditing}
  <EdgeLabelEditor
    edgeId={edge.id}
    currentLabel={edge.label}
    x={midpoint.x}
    y={midpoint.y}
    onClose={closeFallbackEditor}
  />
{/if}

<style>
  .cl-canvas-edge-path {
    transition: stroke 0.15s ease;
  }

  .cl-canvas-edge-label {
    font-family: var(--font-text-theme);
    font-size: 12px;
    fill: var(--text-muted);
    pointer-events: none;
    user-select: none;
  }

  .cl-canvas-edge--selected .cl-canvas-edge-label {
    fill: var(--interactive-accent);
  }

  .cl-canvas-edge-label-input {
    width: 100%;
    height: 24px;
    font-size: 12px;
    font-family: var(--font-text-theme);
    text-align: center;
    border: 1px solid var(--interactive-accent);
    border-radius: var(--radius-s, 4px);
    background: var(--background-primary);
    color: var(--text-normal);
    outline: none;
    padding: 0 4px;
    box-sizing: border-box;
  }
</style>
