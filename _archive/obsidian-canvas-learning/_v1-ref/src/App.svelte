<script lang="ts">
  /**
   * Canvas Learning System - Root Application Component
   * Story 1.4: Top-level routing between Dashboard and Canvas views (AC-7, Task 8.2)
   * Story 1.5: SyncIndicator global mount (AC-6, Task 4.4)
   * Story 3.3: ChatPanel view routing (AC-1, Task 6)
   *
   * Routes:
   *   'dashboard' → DashboardView (board list)
   *   'canvas'    → CanvasView (active whiteboard)
   *   'chat'      → ChatPanel (node conversation, Story 3.3)
   */

  import { getContext } from 'svelte';
  import type { App } from 'obsidian';
  import { canvasState } from './stores/canvas-state';
  import DashboardView from './components/dashboard/DashboardView.svelte';
  import CanvasView from './components/canvas/CanvasView.svelte';
  import ChatPanel from './components/chat/ChatPanel.svelte';
  import SyncIndicator from './components/global/SyncIndicator.svelte';

  let { app }: { app?: App } = $props();

  // Force reactivity for route changes
  let stateVersion = $state(0);
  $effect(() => {
    const unsub = canvasState.subscribe(() => {
      stateVersion++;
    });
    return unsub;
  });

  let currentRoute = $derived.by(() => {
    void stateVersion;
    return canvasState.currentRoute;
  });

  let boardName = $derived.by(() => {
    void stateVersion;
    return canvasState.getCurrentBoardName();
  });

  let chatNodeId = $derived.by(() => {
    void stateVersion;
    return canvasState.activeChatNodeId;
  });

  let chatNodeName = $derived.by(() => {
    void stateVersion;
    return canvasState.activeChatNodeName;
  });

  function goToDashboard() {
    canvasState.navigateToDashboard();
  }

  function goBackFromChat() {
    canvasState.navigateBackFromChat();
  }
</script>

<div class="cl-main-view">
  {#if currentRoute === 'chat' && chatNodeId && app}
    <!-- Chat mode: show back button + node name + ChatPanel (Story 3.3) -->
    <div class="cl-main-view__content cl-main-view__content--chat">
      <ChatPanel
        nodeId={chatNodeId}
        nodeName={chatNodeName}
        {app}
      />
    </div>
  {:else if currentRoute === 'canvas'}
    <!-- Canvas mode: show back button + board name + canvas -->
    <div class="cl-main-view__header">
      <button class="cl-nav-back-btn" onclick={goToDashboard} title="返回白板列表">
        ←
      </button>
      <h3 class="cl-main-view__title">{boardName || 'Canvas'}</h3>
      <div class="cl-main-view__spacer"></div>
      <SyncIndicator />
    </div>
    <div class="cl-main-view__content cl-main-view__content--canvas">
      <CanvasView />
    </div>
  {:else}
    <!-- Dashboard mode -->
    <div class="cl-main-view__header">
      <h3 class="cl-main-view__title">Canvas Learning System</h3>
      <div class="cl-main-view__spacer"></div>
      <SyncIndicator />
    </div>
    <div class="cl-main-view__content">
      <DashboardView />
    </div>
  {/if}
</div>

<style>
  .cl-main-view {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: var(--background-primary);
    color: var(--text-normal);
    font-family: var(--font-interface);
  }

  .cl-main-view__header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-bottom: 1px solid var(--background-modifier-border);
    flex-shrink: 0;
  }

  .cl-main-view__title {
    font-size: 1.1em;
    font-weight: 600;
    margin: 0;
  }

  .cl-main-view__spacer {
    flex: 1;
  }

  .cl-main-view__content {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
  }

  .cl-main-view__content--canvas {
    padding: 0;
    overflow: hidden;
  }

  /* Story 3.3: Chat view takes full height, no padding */
  .cl-main-view__content--chat {
    flex: 1;
    padding: 0;
    overflow: hidden;
  }

  .cl-nav-back-btn {
    padding: 2px 8px;
    font-size: 16px;
    background: none;
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    color: var(--text-normal);
    cursor: pointer;
    transition: background 0.15s ease;
    line-height: 1;
  }

  .cl-nav-back-btn:hover {
    background: var(--background-secondary);
  }
</style>
