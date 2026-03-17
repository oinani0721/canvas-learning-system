<!--
  Canvas Learning System - Recovery Banner Component
  Story 3.11: Crash Recovery (AC-3, AC-4, AC-5)

  Displays at the top of the ChatPanel message list when crash recovery
  is in progress. Three visual states:

  1. recovering: "AI 连接中断，正在恢复..." (with spinner)
  2. failed: "AI 暂时不可用" + manual "Retry" button
  3. circuit_open: "AI 多次异常" + "Check Updates" link

  [Source: _bmad-output/implementation-artifacts/3-11-crash-recovery.md#Task 5]
-->
<script lang="ts">
  import type { RecoveryStatus } from '../../services/crash-recovery';

  /** Current recovery status. */
  export let status: RecoveryStatus;

  /** Callback when user clicks the manual "Retry" button. */
  export let onRetry: () => void;

  const CLAUDE_CODE_INSTALL_URL = 'https://docs.anthropic.com/en/docs/claude-code/overview';
</script>

{#if status === 'recovering'}
  <div class="cl-recovery-banner cl-recovery-recovering">
    <span class="cl-recovery-spinner"></span>
    <span class="cl-recovery-text">AI 连接中断，正在恢复...</span>
  </div>
{:else if status === 'failed'}
  <div class="cl-recovery-banner cl-recovery-failed">
    <span class="cl-recovery-text">AI 暂时不可用，请稍后重试</span>
    <button class="cl-recovery-retry-btn" onclick={onRetry}>
      重试
    </button>
  </div>
{:else if status === 'circuit_open'}
  <div class="cl-recovery-banner cl-recovery-circuit-open">
    <span class="cl-recovery-text">
      AI 多次异常，可能需要更新 Claude Code 或重启系统
    </span>
    <a
      class="cl-recovery-link"
      href={CLAUDE_CODE_INSTALL_URL}
      target="_blank"
      rel="noopener noreferrer"
    >
      检查更新
    </a>
  </div>
{/if}

<style>
  .cl-recovery-banner {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 0.85em;
    margin-bottom: 8px;
  }

  .cl-recovery-recovering {
    background: var(--background-modifier-info, rgba(8, 109, 221, 0.1));
    color: var(--text-normal);
    border: 1px solid var(--background-modifier-border);
  }

  .cl-recovery-failed {
    background: var(--background-modifier-error-hover, rgba(227, 74, 74, 0.1));
    color: var(--text-normal);
    border: 1px solid var(--background-modifier-border);
  }

  .cl-recovery-circuit-open {
    background: var(--background-modifier-error-hover, rgba(227, 74, 74, 0.15));
    color: var(--text-normal);
    border: 1px solid var(--text-error, #e34a4a);
  }

  .cl-recovery-text {
    flex: 1;
  }

  .cl-recovery-spinner {
    width: 14px;
    height: 14px;
    border: 2px solid var(--text-muted);
    border-top-color: var(--interactive-accent);
    border-radius: 50%;
    animation: cl-spin 0.8s linear infinite;
    flex-shrink: 0;
  }

  @keyframes cl-spin {
    to {
      transform: rotate(360deg);
    }
  }

  .cl-recovery-retry-btn {
    padding: 4px 12px;
    border-radius: 4px;
    border: 1px solid var(--background-modifier-border);
    background: var(--interactive-normal);
    color: var(--text-normal);
    cursor: pointer;
    font-size: 0.85em;
    flex-shrink: 0;
    transition: background 0.15s;
  }

  .cl-recovery-retry-btn:hover {
    background: var(--interactive-hover);
  }

  .cl-recovery-link {
    color: var(--text-accent);
    text-decoration: underline;
    cursor: pointer;
    flex-shrink: 0;
    font-size: 0.85em;
  }

  .cl-recovery-link:hover {
    opacity: 0.8;
  }
</style>
