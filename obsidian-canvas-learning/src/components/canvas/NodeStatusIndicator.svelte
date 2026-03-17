<!--
  Canvas Learning System - Node Status Indicator
  Story 3.8: Node Generation Status Display (AC-4)

  Displays a small status indicator on the top-right corner of canvas nodes:
    - generating: spinning animation (blue)
    - unread: green dot (completed, user hasn't viewed)
    - idle: hidden (no indicator)

  [Source: _bmad-output/implementation-artifacts/3-8-dialog-archive-async-generation.md#Task 5]
-->
<script lang="ts">
  import type { GenerationStatus } from '../../services/generation-manager';

  let {
    status = 'idle' as GenerationStatus,
  }: {
    status?: GenerationStatus;
  } = $props();
</script>

{#if status === 'generating'}
  <div class="cl-node-status cl-node-status--generating" title="AI generating...">
    <svg width="14" height="14" viewBox="0 0 14 14">
      <circle
        cx="7"
        cy="7"
        r="5"
        fill="none"
        stroke="var(--interactive-accent, #4480ff)"
        stroke-width="2"
        stroke-dasharray="20 10"
        class="cl-node-status__spinner"
      />
    </svg>
  </div>
{:else if status === 'unread'}
  <div class="cl-node-status cl-node-status--unread" title="New response available">
    <div class="cl-node-status__dot"></div>
  </div>
{/if}

<style>
  .cl-node-status {
    position: absolute;
    top: -4px;
    right: -4px;
    z-index: 10;
    pointer-events: none;
  }

  /* Generating: spinning circle */
  .cl-node-status--generating {
    animation: cl-pulse 1.5s ease-in-out infinite;
  }

  .cl-node-status__spinner {
    animation: cl-spin 1s linear infinite;
    transform-origin: center;
  }

  @keyframes cl-spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  @keyframes cl-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
  }

  /* Unread: green dot */
  .cl-node-status--unread {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .cl-node-status__dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-green, #4caf50);
    box-shadow: 0 0 4px var(--color-green, #4caf50);
  }
</style>
