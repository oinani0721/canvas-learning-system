<!--
  Canvas Learning System - Chat Panel
  Story 3.3: ChatPanel UI (AC-1 through AC-6, Tasks 1-6)
  Story 3.4: Learning context auto-injection (AC-3, Task 4)
  Story 3.5: Skill command integration (AC-1/AC-2, Task 5)

  Main conversation UI for a single canvas node.
  Three-mode design: 'chat' | 'exam' | 'edge' (only 'chat' in this story).
  Integrates MessageBubble, InputBar, StreamingIndicator, and SkillSelector.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import type { App } from 'obsidian';
  import MessageBubble from './MessageBubble.svelte';
  import InputBar from './InputBar.svelte';
  import StreamingIndicator from './StreamingIndicator.svelte';
  import SkillSelector from './SkillSelector.svelte';
  import QuotaExhausted from './QuotaExhausted.svelte';
  import RecoveryBanner from './RecoveryBanner.svelte';
  import { chatState, type ChatMessage } from '../../stores/chat-state.svelte';
  import { skillRegistry, type Skill } from '../../services/skill-registry';
  import { MessageStore } from '../../services/message-store';

  let {
    mode = 'chat',
    nodeId,
    nodeName = '',
    app,
  }: {
    mode?: 'chat' | 'exam' | 'edge';
    nodeId: string;
    nodeName?: string;
    app: App;
  } = $props();

  let messageListEl: HTMLDivElement | undefined = $state(undefined);
  let inputBarRef: InputBar | undefined = $state(undefined);
  let showSkillSelector = $state(false);
  let skillFilterQuery = $state('');
  let thinkingTimeout: ReturnType<typeof setTimeout> | null = null;
  let showThinking = $state(false);
  let messageStore: MessageStore | null = null;
  let historyLoaded = $state(false);
  let allHistoryLoaded = $state(false);
  let loadingMore = $state(false);
  let sentinelEl: HTMLDivElement | undefined = $state(undefined);
  let observer: IntersectionObserver | null = null;

  const INITIAL_LOAD_LIMIT = 50;
  const PAGE_SIZE = 50;
  let loadedOffset = 0;

  // Reactive bindings to chatState
  let messages = $derived(chatState.messages);
  let status = $derived(chatState.status);
  let isStreaming = $derived(status === 'streaming');
  let lastError = $derived(chatState.lastError);

  // Story 3.9: Engine type indicator
  let activeEngineType = $derived(chatState.activeEngineType);
  // Story 3.10: Quota status
  let quotaStatus = $derived(chatState.quotaStatus);
  // Story 3.11: Recovery status
  let recoveryStatus = $derived(chatState.recoveryStatus);

  // Skills list from registry
  let skills = $derived(skillRegistry.skills);

  // AC-6: 2s timeout for "thinking" indicator
  $effect(() => {
    if (status === 'streaming') {
      if (thinkingTimeout) clearTimeout(thinkingTimeout);
      showThinking = true;
      thinkingTimeout = setTimeout(() => {
        // After 2s, showThinking stays true (the text changes from dots to "正在思考...")
      }, 2000);
    } else {
      if (thinkingTimeout) {
        clearTimeout(thinkingTimeout);
        thinkingTimeout = null;
      }
      showThinking = false;
    }
  });

  // Auto-scroll to bottom when new messages arrive
  $effect(() => {
    void messages.length;
    void status;
    scrollToBottom();
  });

  function scrollToBottom(): void {
    queueMicrotask(() => {
      if (messageListEl) {
        messageListEl.scrollTop = messageListEl.scrollHeight;
      }
    });
  }

  /** Send a message to the chat engine. */
  async function handleSend(message: string): Promise<void> {
    await chatState.sendMessage(message);

    // Persist messages after send+response cycle
    if (messageStore) {
      const msgs = chatState.messages;
      // Save last user message
      const lastUser = msgs.filter((m) => m.role === 'user').pop();
      if (lastUser) {
        await messageStore.saveMessage(nodeId, lastUser);
      }
      // Save last assistant message
      const lastAssistant = msgs.filter((m) => m.role === 'assistant').pop();
      if (lastAssistant) {
        await messageStore.saveMessage(nodeId, lastAssistant);
      }
    }
  }

  /** Handle skill selection from SkillSelector. */
  function handleSkillSelect(skill: Skill): void {
    showSkillSelector = false;
    skillFilterQuery = '';
    inputBarRef?.setInputText(`/${skill.commandName} `);
  }

  function handleSlashTrigger(): void {
    showSkillSelector = true;
    skillFilterQuery = '';
  }

  function handleSlashInput(query: string): void {
    skillFilterQuery = query;
    if (!showSkillSelector) {
      showSkillSelector = true;
    }
  }

  function handleSkillSelectorClose(): void {
    showSkillSelector = false;
    skillFilterQuery = '';
  }

  /** AC-4: Load history from SQLite on mount. */
  async function loadHistory(): Promise<void> {
    if (!messageStore) return;

    const history = await messageStore.loadMessages(nodeId, INITIAL_LOAD_LIMIT, 0);
    if (history.length > 0) {
      // History is returned newest-first; reverse for display
      const reversed = history.reverse();
      chatState.loadHistory(reversed);
      loadedOffset = history.length;
    }
    if (history.length < INITIAL_LOAD_LIMIT) {
      allHistoryLoaded = true;
    }
    historyLoaded = true;
  }

  /** Lazy load more history when scrolling to top. */
  async function loadMoreHistory(): Promise<void> {
    if (loadingMore || allHistoryLoaded || !messageStore) return;
    loadingMore = true;

    const older = await messageStore.loadMessages(nodeId, PAGE_SIZE, loadedOffset);
    if (older.length > 0) {
      const reversed = older.reverse();
      chatState.prependHistory(reversed);
      loadedOffset += older.length;
    }
    if (older.length < PAGE_SIZE) {
      allHistoryLoaded = true;
    }
    loadingMore = false;
  }

  onMount(() => {
    // Initialize message store for history persistence
    const pluginDataDir = (app as unknown as { vault: { adapter: { basePath: string } } })
      .vault.adapter.basePath;
    messageStore = new MessageStore(pluginDataDir);

    // Open the node chat (switches state + restores cache)
    chatState.openNodeChat(nodeId);

    // Load persisted history
    loadHistory();

    // Load skills from the commands directory
    const vaultPath = (app as unknown as { vault: { adapter: { basePath: string } } })
      .vault.adapter.basePath;
    skillRegistry.loadSkills(vaultPath);

    // Set up IntersectionObserver for lazy-loading older messages
    if (sentinelEl) {
      observer = new IntersectionObserver(
        (entries) => {
          if (entries[0]?.isIntersecting && historyLoaded) {
            loadMoreHistory();
          }
        },
        { root: messageListEl, threshold: 0.1 },
      );
      observer.observe(sentinelEl);
    }

    return () => {
      if (observer) {
        observer.disconnect();
        observer = null;
      }
      if (thinkingTimeout) {
        clearTimeout(thinkingTimeout);
      }
    };
  });
</script>

<div class="cl-chat-panel">
  <!-- Header (Story 3.9 AC-4.1: engine type indicator) -->
  <div class="cl-chat-panel__header">
    <div class="cl-chat-panel__header-title">
      {nodeName || '对话'}
    </div>
    <div class="cl-chat-panel__header-status">
      <!-- Story 3.9: Engine type label -->
      <span
        class="cl-chat-panel__engine-label"
        class:cl-chat-panel__engine-label--fallback={activeEngineType === 'api-key'}
      >
        {activeEngineType === 'claude-code' ? 'Claude Code' : 'API Key'}
      </span>
      {#if isStreaming}
        <span class="cl-chat-panel__status-dot cl-chat-panel__status-dot--active"></span>
        <span>对话中</span>
      {:else if lastError}
        <span class="cl-chat-panel__status-dot cl-chat-panel__status-dot--error"></span>
        <span>错误</span>
      {:else}
        <span class="cl-chat-panel__status-dot cl-chat-panel__status-dot--idle"></span>
        <span>就绪</span>
      {/if}
    </div>
  </div>

  <!-- Messages List -->
  <div class="cl-chat-panel__messages" bind:this={messageListEl}>
    <!-- Story 3.11: Recovery banner at top of message list -->
    {#if recoveryStatus !== 'idle'}
      <RecoveryBanner
        status={recoveryStatus}
        onRetry={() => { /* Manual retry handled via chatState / crashRecovery */ }}
      />
    {/if}

    <!-- Sentinel for lazy-loading older messages -->
    <div bind:this={sentinelEl} class="cl-chat-panel__sentinel">
      {#if loadingMore}
        <span class="cl-chat-panel__loading-more">加载更多...</span>
      {/if}
    </div>

    {#if messages.length === 0 && historyLoaded}
      <div class="cl-chat-panel__empty">
        <p>开始你的学习对话</p>
        <p class="cl-chat-panel__empty-hint">输入 / 查看可用技能</p>
      </div>
    {/if}

    {#each messages as msg (msg.id)}
      <MessageBubble
        message={msg}
        {app}
        sourcePath=""
        isStreaming={isStreaming && msg === messages[messages.length - 1] && msg.role === 'assistant'}
      />
    {/each}

    {#if isStreaming && (messages.length === 0 || messages[messages.length - 1]?.role === 'user')}
      <div class="cl-chat-bubble cl-chat-bubble-agent">
        {#if showThinking}
          <div class="cl-chat-panel__thinking">正在思考...</div>
        {/if}
        <StreamingIndicator />
      </div>
    {/if}

    {#if lastError}
      <div class="cl-chat-panel__error">
        {lastError.message}
      </div>
    {/if}
  </div>

  <!-- Input Area / Quota Exhausted (Story 3.10 AC-3) -->
  {#if quotaStatus === 'exhausted'}
    <QuotaExhausted
      onDismiss={() => chatState.setQuotaAvailable()}
      onSwitchApiKey={() => {
        // Open Obsidian settings for API Key configuration
        (app as any).setting?.open();
      }}
    />
  {:else}
    <div class="cl-chat-panel__input-wrapper">
      {#if showSkillSelector}
        <SkillSelector
          {skills}
          filterQuery={skillFilterQuery}
          onSelect={handleSkillSelect}
          onClose={handleSkillSelectorClose}
        />
      {/if}
      <InputBar
        bind:this={inputBarRef}
        disabled={isStreaming || quotaStatus === 'checking'}
        placeholder={quotaStatus === 'checking' ? '正在检测额度...' : undefined}
        onSend={handleSend}
        onSlashTrigger={handleSlashTrigger}
        onSlashInput={handleSlashInput}
      />
    </div>
  {/if}
</div>

<style>
  .cl-chat-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: var(--background-primary);
    color: var(--text-normal);
    font-family: var(--font-interface);
  }

  /* Header */
  .cl-chat-panel__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-bottom: 1px solid var(--background-modifier-border);
    flex-shrink: 0;
  }

  .cl-chat-panel__header-title {
    font-weight: 600;
    font-size: 0.95em;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .cl-chat-panel__header-status {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.78em;
    color: var(--text-muted);
  }

  /* Story 3.9: Engine type label */
  .cl-chat-panel__engine-label {
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 0.85em;
    background: var(--background-modifier-success, rgba(76, 175, 80, 0.12));
    color: var(--text-success, #4caf50);
    margin-right: 4px;
  }

  .cl-chat-panel__engine-label--fallback {
    background: var(--background-modifier-error-hover, rgba(226, 185, 61, 0.12));
    color: var(--text-warning, #e2b93d);
  }

  .cl-chat-panel__status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }

  .cl-chat-panel__status-dot--idle {
    background: var(--color-green, #4caf50);
  }

  .cl-chat-panel__status-dot--active {
    background: var(--interactive-accent);
    animation: cl-pulse 1.5s infinite;
  }

  .cl-chat-panel__status-dot--error {
    background: var(--color-red, #f44336);
  }

  @keyframes cl-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  /* Messages */
  .cl-chat-panel__messages {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
  }

  .cl-chat-panel__sentinel {
    min-height: 1px;
    flex-shrink: 0;
  }

  .cl-chat-panel__loading-more {
    display: block;
    text-align: center;
    font-size: 0.8em;
    color: var(--text-faint);
    padding: 4px 0;
  }

  .cl-chat-panel__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    color: var(--text-muted);
    text-align: center;
    gap: 4px;
  }

  .cl-chat-panel__empty p {
    margin: 0;
    font-size: 0.95em;
  }

  .cl-chat-panel__empty-hint {
    font-size: 0.82em !important;
    color: var(--text-faint);
  }

  .cl-chat-panel__thinking {
    font-size: 0.82em;
    color: var(--text-muted);
    padding: 4px 12px 0;
  }

  .cl-chat-panel__error {
    background: rgba(244, 67, 54, 0.1);
    color: var(--color-red, #f44336);
    padding: 8px 12px;
    border-radius: var(--radius-s, 4px);
    font-size: 0.85em;
    margin-top: 8px;
  }

  /* Input wrapper: positioned relatively so SkillSelector can anchor above */
  .cl-chat-panel__input-wrapper {
    position: relative;
    flex-shrink: 0;
  }
</style>
