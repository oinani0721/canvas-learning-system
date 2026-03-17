<script lang="ts">
  /**
   * Canvas Learning System - ExamCanvas Component
   * Story 6.1: Exam Board Generation (AC-4)
   *
   * Wraps CanvasView with exam-mode UI overlays:
   *   - Top status bar: exam mode, elapsed time, nodes examined
   *   - ChatPanel in mode="exam"
   *   - Hides "generate exam" button (AC-3: no nesting)
   *
   * Inherits all CanvasView capabilities (AC-2):
   *   Node CRUD, Edge creation, pan/zoom, ChatPanel, skills.
   *
   * CSS: cl-exam-* prefix, Light/Dark theme adaptive.
   */

  import { examState } from '../../stores/exam-state.svelte';

  interface Props {
    examId: string;
  }

  let { examId }: Props = $props();

  // Elapsed timer
  let elapsedMinutes = $state(0);
  let timerInterval: ReturnType<typeof setInterval> | null = null;

  $effect(() => {
    if (examState.isActive) {
      timerInterval = setInterval(() => {
        elapsedMinutes = examState.elapsedMinutes;
      }, 10000);
    }

    return () => {
      if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
      }
    };
  });

  function formatElapsed(minutes: number): string {
    if (minutes < 60) return `${minutes} \u5206\u949F`;
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return `${h} \u5C0F\u65F6 ${m} \u5206\u949F`;
  }

  function getModeLabel(mode: string): string {
    const labels: Record<string, string> = {
      'point_to_point': '\u70B9\u5BF9\u70B9\u8003\u5BDF',
      'comprehensive': '\u7EFC\u5408\u9898\u8003\u5BDF',
      'mixed': '\u6DF7\u5408\u8003\u5BDF',
    };
    return labels[mode] || mode;
  }

  async function handleExitExam() {
    await examState.exitExam();
  }
</script>

<div class="cl-exam-container">
  <!-- Exam status bar (AC-4: exam-specific UI) -->
  <div class="cl-exam-status-bar">
    <div class="cl-exam-status-left">
      <span class="cl-exam-status-badge">\u8003\u5BDF\u4E2D</span>
      <span class="cl-exam-status-mode">{getModeLabel(examState.examMode)}</span>
    </div>
    <div class="cl-exam-status-center">
      <span class="cl-exam-status-timer">{formatElapsed(elapsedMinutes)}</span>
      <span class="cl-exam-status-divider">|</span>
      <span class="cl-exam-status-count">
        \u5DF2\u8003\u5BDF {examState.examinedCount} \u4E2A\u8282\u70B9
      </span>
    </div>
    <div class="cl-exam-status-right">
      <button class="cl-exam-exit-btn" onclick={handleExitExam}>
        \u7ED3\u675F\u8003\u5BDF
      </button>
    </div>
  </div>

  <!-- Canvas viewport area — CanvasView is rendered by the parent via slot/routing -->
  <div class="cl-exam-canvas-area">
    <slot />
  </div>
</div>

<style>
  .cl-exam-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 100%;
  }

  .cl-exam-status-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 14px;
    background: var(--background-secondary);
    border-bottom: 1px solid var(--background-modifier-border);
    flex-shrink: 0;
    min-height: 36px;
  }

  .cl-exam-status-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .cl-exam-status-badge {
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 3px;
    background: var(--interactive-accent);
    color: var(--text-on-accent);
  }

  .cl-exam-status-mode {
    font-size: 12px;
    color: var(--text-muted);
  }

  .cl-exam-status-center {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--text-muted);
  }

  .cl-exam-status-timer {
    font-variant-numeric: tabular-nums;
  }

  .cl-exam-status-divider {
    color: var(--background-modifier-border);
  }

  .cl-exam-status-right {
    display: flex;
    align-items: center;
  }

  .cl-exam-exit-btn {
    padding: 4px 10px;
    font-size: 11px;
    background: none;
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    color: var(--text-muted);
    cursor: pointer;
    transition: background 0.15s ease, color 0.15s ease;
  }

  .cl-exam-exit-btn:hover {
    background: var(--background-modifier-hover);
    color: var(--text-normal);
  }

  .cl-exam-canvas-area {
    flex: 1;
    overflow: hidden;
    position: relative;
  }
</style>
