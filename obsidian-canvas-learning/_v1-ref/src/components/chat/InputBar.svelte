<!--
  Canvas Learning System - Input Bar
  Story 3.3: ChatPanel UI (AC-5, Task 3)
  Story 3.5: Skill command integration (AC-1, Task 5)

  Chat input bar with:
  - Multi-line textarea (auto-resize, min 1 / max 6 lines)
  - Enter to send / Shift+Enter for newline / Escape to clear
  - Empty message guard (send button disabled)
  - Streaming guard (input disabled during streaming)
  - '/' trigger emits slashTrigger event for SkillSelector (Story 3.5)
-->
<script lang="ts">
  let {
    disabled = false,
    placeholder,
    onSend,
    onSlashTrigger,
    onSlashInput,
  }: {
    disabled?: boolean;
    placeholder?: string;
    onSend: (message: string) => void;
    onSlashTrigger?: () => void;
    onSlashInput?: (query: string) => void;
  } = $props();

  let defaultPlaceholder = $derived(
    disabled ? '等待回复中...' : '输入消息... (Enter 发送, Shift+Enter 换行)',
  );

  let inputText = $state('');
  let textareaEl: HTMLTextAreaElement | undefined = $state(undefined);

  /** Maximum visible lines before scrolling. */
  const MAX_LINES = 6;
  const LINE_HEIGHT_PX = 20;
  const PADDING_PX = 16; // top + bottom padding

  let isEmpty = $derived(inputText.trim().length === 0);

  function autoResize(): void {
    if (!textareaEl) return;
    // Reset height to allow shrinking
    textareaEl.style.height = 'auto';
    const maxHeight = MAX_LINES * LINE_HEIGHT_PX + PADDING_PX;
    const newHeight = Math.min(textareaEl.scrollHeight, maxHeight);
    textareaEl.style.height = `${newHeight}px`;
  }

  function handleInput(): void {
    autoResize();

    // Story 3.5: Detect '/' at the beginning of input for skill trigger
    if (inputText.startsWith('/')) {
      if (inputText === '/') {
        onSlashTrigger?.();
      } else {
        // Pass the query portion after '/' for fuzzy filtering
        onSlashInput?.(inputText.slice(1));
      }
    }
  }

  function handleKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      send();
    } else if (event.key === 'Escape') {
      inputText = '';
      autoResize();
    }
  }

  function send(): void {
    if (isEmpty || disabled) return;
    const message = inputText.trim();
    inputText = '';
    if (textareaEl) {
      textareaEl.style.height = 'auto';
    }
    onSend(message);
  }

  /**
   * Set the input text programmatically (used by SkillSelector).
   * Preserves focus on the textarea.
   */
  export function setInputText(text: string): void {
    inputText = text;
    // Use microtask to ensure DOM update before resize
    queueMicrotask(() => {
      autoResize();
      textareaEl?.focus();
    });
  }

  /** Focus the textarea. */
  export function focus(): void {
    textareaEl?.focus();
  }
</script>

<div class="cl-chat-input" class:cl-chat-input--disabled={disabled}>
  <textarea
    bind:this={textareaEl}
    bind:value={inputText}
    oninput={handleInput}
    onkeydown={handleKeydown}
    placeholder={placeholder ?? defaultPlaceholder}
    disabled={disabled}
    rows="1"
    class="cl-chat-input__textarea"
  ></textarea>
  <button
    onclick={send}
    disabled={isEmpty || disabled}
    class="cl-chat-input__send"
    title="发送消息"
    aria-label="发送消息"
  >
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M22 2L11 13" />
      <path d="M22 2L15 22L11 13L2 9L22 2Z" />
    </svg>
  </button>
</div>

<style>
  .cl-chat-input {
    display: flex;
    align-items: flex-end;
    gap: 8px;
    padding: 8px 12px;
    border-top: 1px solid var(--background-modifier-border);
    background: var(--background-primary);
  }

  .cl-chat-input--disabled {
    opacity: 0.7;
  }

  .cl-chat-input__textarea {
    flex: 1;
    resize: none;
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    padding: 8px 10px;
    font-family: var(--font-interface);
    font-size: 0.9em;
    line-height: 20px;
    background: var(--background-secondary);
    color: var(--text-normal);
    outline: none;
    min-height: 36px;
    max-height: calc(6 * 20px + 16px);
    overflow-y: auto;
  }

  .cl-chat-input__textarea:focus {
    border-color: var(--interactive-accent);
  }

  .cl-chat-input__textarea::placeholder {
    color: var(--text-faint);
  }

  .cl-chat-input__send {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border: none;
    border-radius: var(--radius-s, 4px);
    background: var(--interactive-accent);
    color: var(--text-on-accent);
    cursor: pointer;
    transition: opacity 0.15s ease;
  }

  .cl-chat-input__send:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .cl-chat-input__send:not(:disabled):hover {
    background: var(--interactive-accent-hover);
  }
</style>
