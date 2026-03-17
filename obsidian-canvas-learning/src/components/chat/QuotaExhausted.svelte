<!--
  Canvas Learning System - Quota Exhausted Component
  Story 3.10: Quota Management & Degradation (AC-2, AC-3)

  Displays when subscription quota is exhausted (429 Rate Limit detected).
  Shows:
  - Friendly message (no technical jargon)
  - Countdown to estimated reset time
  - Two action buttons: "Wait for Reset" and "Use API Key"

  CSS class: .cl-chat-quota-exhausted

  [Source: _bmad-output/implementation-artifacts/3-10-quota-management-degradation.md#Task 3]
-->
<script lang="ts">
  import { onDestroy } from 'svelte';
  import { chatState } from '../../stores/chat-state.svelte';

  /** Callback when user clicks "Wait for Reset" */
  export let onDismiss: () => void;

  /** Callback when user clicks "Use API Key" (opens Settings Tab) */
  export let onSwitchApiKey: () => void;

  // ── Countdown logic (Story 3.10 Task 4) ──────────────────────────────────

  let countdownText = $state('');

  function updateCountdown(): void {
    const resetTime = chatState.quotaResetTime;

    if (!resetTime) {
      countdownText = '通常在每周一重置';
      return;
    }

    const now = Date.now();
    const diff = resetTime.getTime() - now;

    if (diff <= 0) {
      countdownText = '额度可能已恢复，请尝试发送消息';
      return;
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (days > 0) {
      countdownText = `预计 ${days} 天 ${hours} 小时后重置`;
    } else if (hours > 0) {
      countdownText = `预计 ${hours} 小时 ${minutes} 分钟后重置`;
    } else {
      countdownText = `预计 ${minutes} 分钟后重置`;
    }
  }

  // Update countdown every minute (Story 3.10 Task 4.3)
  updateCountdown();
  const countdownInterval = setInterval(updateCountdown, 60_000);

  onDestroy(() => {
    clearInterval(countdownInterval);
  });
</script>

<div class="cl-chat-quota-exhausted">
  <div class="cl-quota-icon">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
  </div>

  <h3 class="cl-quota-title">本周订阅额度已用完</h3>

  <p class="cl-quota-countdown">{countdownText}</p>

  <p class="cl-quota-note">
    白板编辑、复习提醒等功能不受影响，仅 AI 对话暂时不可用。
  </p>

  <div class="cl-quota-actions">
    <button
      class="cl-quota-btn cl-quota-btn-secondary"
      onclick={onDismiss}
    >
      等待重置
    </button>
    <button
      class="cl-quota-btn cl-quota-btn-primary"
      onclick={onSwitchApiKey}
    >
      临时使用 API Key
    </button>
  </div>
</div>

<style>
  .cl-chat-quota-exhausted {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 24px 16px;
    text-align: center;
    border-top: 1px solid var(--background-modifier-border);
    background: var(--background-secondary);
  }

  .cl-quota-icon {
    color: var(--text-warning, #e2b93d);
    opacity: 0.8;
  }

  .cl-quota-title {
    margin: 0;
    font-size: 1.1em;
    font-weight: 600;
    color: var(--text-normal);
  }

  .cl-quota-countdown {
    margin: 0;
    font-size: 0.9em;
    color: var(--text-muted);
  }

  .cl-quota-note {
    margin: 0;
    font-size: 0.8em;
    color: var(--text-faint);
    max-width: 280px;
  }

  .cl-quota-actions {
    display: flex;
    gap: 8px;
    margin-top: 4px;
  }

  .cl-quota-btn {
    padding: 6px 16px;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    font-size: 0.85em;
    font-weight: 500;
    transition: opacity 0.15s;
  }

  .cl-quota-btn:hover {
    opacity: 0.85;
  }

  .cl-quota-btn-secondary {
    background: var(--background-modifier-border);
    color: var(--text-normal);
  }

  .cl-quota-btn-primary {
    background: var(--interactive-accent);
    color: var(--text-on-accent);
  }
</style>
