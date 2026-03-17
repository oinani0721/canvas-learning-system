<script lang="ts">
  /**
   * Canvas Learning System - Sync Status Indicator
   * Story 1.5: Sync state visualization (AC-6, Task 4)
   *
   * Three-state display:
   *   IDLE    → hidden (normal state, nothing to show)
   *   SYNCING → spinning icon with "syncing" tooltip
   *   OFFLINE → red dot with "backend offline" warning
   *
   * Uses Obsidian CSS variables for theme compatibility.
   *
   * [Source: _bmad-output/implementation-artifacts/1-5-canvas-data-sync-backend-kg.md#Task 4]
   */

  import { systemState } from '../../stores/system-state.svelte';

  // Force reactivity for system state changes
  let stateVersion = $state(0);
  $effect(() => {
    const unsub = systemState.subscribe(() => {
      stateVersion++;
    });
    return unsub;
  });

  let syncState = $derived.by(() => {
    void stateVersion;
    return systemState.syncState;
  });

  let pendingCount = $derived.by(() => {
    void stateVersion;
    return systemState.pendingSyncCount;
  });
</script>

<div class="cl-global-sync-indicator">
  {#if syncState === 'SYNCING'}
    <span
      class="cl-global-sync-spinning"
      title="正在同步... ({pendingCount} 条待同步)"
    >
      &#x27F3;
    </span>
  {:else if syncState === 'OFFLINE'}
    <span class="cl-global-sync-offline" title="后端不可达，同步已暂停">
      <span class="cl-global-sync-dot cl-global-sync-dot--red"></span>
      后端离线
    </span>
  {/if}
  <!-- IDLE state: no display -->
</div>

<style>
  .cl-global-sync-indicator {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: var(--text-muted);
    user-select: none;
  }

  .cl-global-sync-spinning {
    display: inline-block;
    font-size: 14px;
    animation: cl-spin 1s linear infinite;
    color: var(--text-accent);
  }

  .cl-global-sync-offline {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    color: var(--text-error);
    font-weight: 500;
  }

  .cl-global-sync-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }

  .cl-global-sync-dot--red {
    background: var(--text-error);
    box-shadow: 0 0 4px var(--text-error);
  }

  @keyframes cl-spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>
