<script lang="ts">
  /**
   * Canvas Learning System - Node Color Indicator
   * Story 5.2: Node Color Mastery Visualization (AC-1, AC-2, AC-3, AC-5)
   *
   * Renders a 4px vertical color bar on the left side of a CanvasNode
   * to visually indicate mastery status. Uses CSS variables for theme
   * adaptation and CSS transitions for smooth color changes.
   *
   * Design rationale (from spec):
   *   - Does NOT change node background → preserves content readability
   *   - Left bar acts as a visual scan anchor (inspired by VS Code gutter)
   *   - Unlearned nodes render nothing → no visual noise
   *   - pointer-events: none → no interference with node interaction
   */

  import { masteryState } from '../../stores/mastery-state.svelte';
  import { getMasteryColorClass } from '../../utils/mastery-color';

  interface Props {
    nodeId: string;
  }

  let { nodeId }: Props = $props();

  /** Derived mastery status from the reactive store. */
  let status = $derived(masteryState.getNodeStatus(nodeId));

  /** CSS class for the indicator bar. */
  let colorClass = $derived(getMasteryColorClass(status));

  /** Only show the indicator for non-unlearned nodes. */
  let showIndicator = $derived(status !== 'unlearned');
</script>

{#if showIndicator}
  <div class="cl-mastery-indicator {colorClass}"></div>
{/if}

<style>
  .cl-mastery-indicator {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    border-radius: 4px 0 0 4px;
    pointer-events: none;
    z-index: 1;
    transition: background-color 300ms ease-in-out;
  }

  .cl-mastery-learning {
    background-color: var(--cl-mastery-learning-bar);
  }

  .cl-mastery-weak {
    background-color: var(--cl-mastery-weak-bar);
  }

  .cl-mastery-mastered {
    background-color: var(--cl-mastery-mastered-bar);
  }

  .cl-mastery-review {
    background-color: var(--cl-mastery-review-bar);
  }
</style>
