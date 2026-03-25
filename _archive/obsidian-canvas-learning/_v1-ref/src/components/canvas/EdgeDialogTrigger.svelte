<!--
  Canvas Learning System - Edge Dialog Trigger
  Story 4.1: Edge 可交互图标与对话触发 (AC-1, AC-2, AC-6, AC-7)
  Story 4.4: Fallback — degraded mode UI (AC-7)

  Renders a clickable icon at the midpoint of a canvas edge.
  Clicking opens Edge dialog (normal mode) or label editor (degraded mode).
  Includes first-time guide tooltip and viewport culling.

  CSS prefix: cl-canvas-edge-trigger (E group — canvas layer)

  [Source: _bmad-output/implementation-artifacts/4-1-edge-dialog-trigger.md#Task 1]
  [Source: _bmad-output/implementation-artifacts/4-4-edge-dialog-fallback.md#Task 2]
-->
<script lang="ts">
  import { chatState, type CurrentEdge } from '../../stores/chat-state.svelte';
  import { systemState } from '../../stores/system-state.svelte';
  import { db } from '../../services/dexie-db';

  // Props
  let {
    edgeId,
    sourceNodeId,
    targetNodeId,
    sourceNodeName,
    targetNodeName,
    midpointX,
    midpointY,
    visible = true,
    onFallbackEdit,
  }: {
    edgeId: string;
    sourceNodeId: string;
    targetNodeId: string;
    sourceNodeName: string;
    targetNodeName: string;
    midpointX: number;
    midpointY: number;
    /** Whether this trigger is within the viewport (Story 4.1 AC-6). */
    visible?: boolean;
    /** Story 4.4 AC-1: Callback to open static label editor in degraded mode. */
    onFallbackEdit?: (edgeId: string) => void;
  } = $props();

  // Local state
  let isHovered = $state(false);
  let showGuide = $state(false);
  let guideTimeout: ReturnType<typeof setTimeout> | null = null;

  // Derived: Agent availability for degraded mode (Story 4.4 AC-7)
  let agentAvailable = $derived(systemState.agentAvailable);

  // Icon dimensions
  const ICON_SIZE = 20;
  const ICON_HALF = ICON_SIZE / 2;

  // ── First-time guide (Story 4.1 AC-2) ─────────────────────────────────

  async function checkAndShowGuide(): Promise<void> {
    try {
      const settings = await db.edge_dialog_settings.toArray();
      if (settings.length === 0 || !settings[0].guideShown) {
        showGuide = true;
        // Auto-dismiss after 3 seconds
        guideTimeout = setTimeout(() => {
          showGuide = false;
        }, 3000);
      }
    } catch {
      // IndexedDB not available, skip guide
    }
  }

  async function dismissGuide(): Promise<void> {
    showGuide = false;
    if (guideTimeout) {
      clearTimeout(guideTimeout);
      guideTimeout = null;
    }
    try {
      const settings = await db.edge_dialog_settings.toArray();
      if (settings.length === 0) {
        await db.edge_dialog_settings.add({ guideShown: true });
      } else {
        await db.edge_dialog_settings.update(settings[0].id!, { guideShown: true });
      }
    } catch {
      // Best-effort persistence
    }
  }

  // Show guide on first render
  $effect(() => {
    checkAndShowGuide();
    return () => {
      if (guideTimeout) clearTimeout(guideTimeout);
    };
  });

  // ── Click handler ─────────────────────────────────────────────────────

  function handleClick(e: MouseEvent): void {
    e.stopPropagation();
    e.preventDefault();

    // Dismiss guide on first click (Story 4.1 AC-2)
    if (showGuide) {
      dismissGuide();
    }

    if (agentAvailable) {
      // Normal mode: open Edge dialog in ChatPanel
      const edge: CurrentEdge = {
        edgeId,
        sourceNodeId,
        targetNodeId,
        sourceNodeName,
        targetNodeName,
      };
      chatState.openEdgeChat(edge);
    } else {
      // Degraded mode (Story 4.4 AC-1): open static label editor
      if (onFallbackEdit) {
        onFallbackEdit(edgeId);
      }
    }
  }

  function handleMouseEnter(): void {
    isHovered = true;
  }

  function handleMouseLeave(): void {
    isHovered = false;
  }
</script>

<!-- Story 4.1 AC-6: Viewport culling — only render when visible -->
{#if visible}
  <g
    class="cl-canvas-edge-trigger"
    class:cl-canvas-edge-trigger--degraded={!agentAvailable}
    class:cl-canvas-edge-trigger--hovered={isHovered}
    transform="translate({midpointX - ICON_HALF}, {midpointY - ICON_HALF})"
  >
    <!-- Clickable area (larger than icon for easy interaction) -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <rect
      x="-4"
      y="-4"
      width={ICON_SIZE + 8}
      height={ICON_SIZE + 8}
      fill="transparent"
      style="cursor: pointer;"
      role="button"
      tabindex="-1"
      aria-label={agentAvailable ? '讨论连线关系' : '手动添加标签'}
      onclick={handleClick}
      onmouseenter={handleMouseEnter}
      onmouseleave={handleMouseLeave}
    />

    <!-- Icon background circle -->
    <circle
      cx={ICON_HALF}
      cy={ICON_HALF}
      r={isHovered ? 12 : 10}
      class="cl-canvas-edge-trigger__bg"
    />

    <!-- Chat bubble icon (normal mode) or pencil icon (degraded mode) -->
    {#if agentAvailable}
      <!-- Chat bubble icon -->
      <path
        d="M4 5C4 4.44772 4.44772 4 5 4H15C15.5523 4 16 4.44772 16 5V13C16 13.5523 15.5523 14 15 14H8L5 17V14H5C4.44772 14 4 13.5523 4 13V5Z"
        class="cl-canvas-edge-trigger__icon"
        fill="none"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    {:else}
      <!-- Pencil icon (degraded mode) -->
      <path
        d="M13.5 4.5L15.5 6.5L7 15H5V13L13.5 4.5Z"
        class="cl-canvas-edge-trigger__icon"
        fill="none"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    {/if}

    <!-- Story 4.1 AC-2: First-time guide tooltip -->
    {#if showGuide}
      <g class="cl-canvas-edge-trigger__guide" transform="translate({ICON_HALF}, -18)">
        <rect
          x="-40"
          y="-14"
          width="80"
          height="18"
          rx="4"
          class="cl-canvas-edge-trigger__guide-bg"
        />
        <text
          x="0"
          y="-2"
          text-anchor="middle"
          class="cl-canvas-edge-trigger__guide-text"
        >
          {agentAvailable ? '点击讨论关系' : '点击添加标签'}
        </text>
      </g>
    {/if}

    <!-- Hover tooltip (when no guide is showing) -->
    {#if isHovered && !showGuide}
      <g transform="translate({ICON_HALF}, -18)">
        <rect
          x="-40"
          y="-14"
          width="80"
          height="18"
          rx="4"
          class="cl-canvas-edge-trigger__tooltip-bg"
        />
        <text
          x="0"
          y="-2"
          text-anchor="middle"
          class="cl-canvas-edge-trigger__tooltip-text"
        >
          {agentAvailable ? '讨论关系' : '手动标签'}
        </text>
      </g>
    {/if}
  </g>
{/if}

<style>
  .cl-canvas-edge-trigger {
    transition: transform 0.15s ease;
  }

  .cl-canvas-edge-trigger--hovered {
    transform: scale(1.1);
  }

  .cl-canvas-edge-trigger__bg {
    fill: var(--background-primary);
    stroke: var(--interactive-accent);
    stroke-width: 1.5;
    transition: r 0.15s ease, fill 0.15s ease;
  }

  .cl-canvas-edge-trigger--hovered .cl-canvas-edge-trigger__bg {
    fill: var(--interactive-accent-hover, rgba(var(--interactive-accent-rgb), 0.1));
    stroke-width: 2;
  }

  /* Story 4.4 AC-7: Degraded mode styling */
  .cl-canvas-edge-trigger--degraded .cl-canvas-edge-trigger__bg {
    stroke: var(--text-muted);
    stroke-dasharray: 3 2;
  }

  .cl-canvas-edge-trigger--degraded.cl-canvas-edge-trigger--hovered .cl-canvas-edge-trigger__bg {
    fill: var(--background-modifier-hover, rgba(0, 0, 0, 0.05));
  }

  .cl-canvas-edge-trigger__icon {
    stroke: var(--interactive-accent);
    pointer-events: none;
  }

  .cl-canvas-edge-trigger--degraded .cl-canvas-edge-trigger__icon {
    stroke: var(--text-muted);
  }

  /* Guide tooltip (Story 4.1 AC-2) */
  .cl-canvas-edge-trigger__guide {
    animation: cl-guide-fade 3s ease forwards;
  }

  .cl-canvas-edge-trigger__guide-bg {
    fill: var(--text-muted);
    opacity: 0.85;
  }

  .cl-canvas-edge-trigger__guide-text {
    font-family: var(--font-interface);
    font-size: 10px;
    fill: var(--background-primary);
    pointer-events: none;
    user-select: none;
  }

  @keyframes cl-guide-fade {
    0%, 80% { opacity: 1; }
    100% { opacity: 0; }
  }

  /* Hover tooltip */
  .cl-canvas-edge-trigger__tooltip-bg {
    fill: var(--background-primary-alt, rgba(0, 0, 0, 0.8));
    stroke: var(--background-modifier-border);
    stroke-width: 0.5;
  }

  .cl-canvas-edge-trigger__tooltip-text {
    font-family: var(--font-interface);
    font-size: 10px;
    fill: var(--text-normal);
    pointer-events: none;
    user-select: none;
  }
</style>
