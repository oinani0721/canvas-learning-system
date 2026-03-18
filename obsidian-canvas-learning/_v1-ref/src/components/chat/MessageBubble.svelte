<!--
  Canvas Learning System - Message Bubble
  Story 3.3: ChatPanel UI (AC-1, AC-3, Task 2)
  Story 3.4: Learning Context (AC-3, Task 4) - Obsidian wikilink support
  Story 3.7: Dialog Pullout Node (AC-1) - Drag selected text to canvas

  Renders a single chat message as a styled bubble.
  - User messages: right-aligned, accent-colored
  - Assistant messages: left-aligned, secondary-colored, Markdown-rendered
  - Uses Obsidian MarkdownRenderer.render() for assistant messages
  - Supports [[wikilink]] click-to-navigate via Obsidian workspace API
  - Supports dragging selected text to canvas for pullout node creation
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { MarkdownRenderer, Component, type App } from 'obsidian';
  import type { ChatMessage } from '../../stores/chat-state.svelte';
  import { encodePulloutDragData, type PulloutDragData } from '../../services/pullout-service';

  let {
    message,
    app,
    sourcePath = '',
    isStreaming = false,
    nodeId = '',
  }: {
    message: ChatMessage;
    app: App;
    sourcePath?: string;
    isStreaming?: boolean;
    nodeId?: string;
  } = $props();

  let markdownContainer: HTMLDivElement | undefined = $state(undefined);
  let renderComponent: Component | null = null;

  /** Format timestamp to relative time. */
  function formatRelativeTime(ts: number): string {
    const diff = Date.now() - ts;
    const seconds = Math.floor(diff / 1000);
    if (seconds < 10) return '刚刚';
    if (seconds < 60) return `${seconds}秒前`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}分钟前`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}小时前`;
    const days = Math.floor(hours / 24);
    return `${days}天前`;
  }

  /**
   * Render Markdown content using Obsidian's native MarkdownRenderer.
   * This supports code highlighting, math (KaTeX/MathJax), and [[wikilinks]].
   */
  async function renderMarkdown(content: string, container: HTMLElement): Promise<void> {
    // Clean up previous render
    if (renderComponent) {
      renderComponent.unload();
    }
    container.empty();

    renderComponent = new Component();
    renderComponent.load();

    await MarkdownRenderer.render(
      app,
      content,
      container,
      sourcePath,
      renderComponent,
    );

    // Story 3.4 AC-3: Hook click events on internal links for [[wikilink]] navigation
    const internalLinks = container.querySelectorAll('a.internal-link');
    for (const link of internalLinks) {
      link.addEventListener('click', (event: Event) => {
        event.preventDefault();
        const href = (link as HTMLAnchorElement).getAttribute('data-href');
        if (href) {
          app.workspace.openLinkText(href, sourcePath);
        }
      });
    }
  }

  // Render Markdown when the message content changes (assistant messages only)
  $effect(() => {
    if (message.role === 'assistant' && markdownContainer && message.content) {
      renderMarkdown(message.content, markdownContainer);
    }
  });

  // ── Story 3.7: Drag selected text for pullout node ──────────────────

  /**
   * Handle dragstart on message bubble.
   * If text is selected, encode it as pullout drag data.
   *
   * Story 3.7 AC-1: Drag selected text from chat to canvas.
   */
  function handleDragStart(e: DragEvent): void {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !e.dataTransfer) return;

    const selectedText = selection.toString().trim();
    if (!selectedText) return;

    const pulloutData: PulloutDragData = {
      content: selectedText,
      sourceNodeId: nodeId,
      sourceMessageId: message.id,
      timestamp: new Date().toISOString(),
    };

    encodePulloutDragData(e.dataTransfer, pulloutData);
    e.dataTransfer.effectAllowed = 'copy';
  }

  // Cleanup the render component on unmount
  onMount(() => {
    return () => {
      if (renderComponent) {
        renderComponent.unload();
        renderComponent = null;
      }
    };
  });
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="cl-chat-bubble {message.role === 'user' ? 'cl-chat-bubble-user' : 'cl-chat-bubble-agent'}"
  class:cl-chat-bubble--streaming={isStreaming}
  draggable="true"
  ondragstart={handleDragStart}
>
  {#if message.role === 'user'}
    <div class="cl-chat-bubble__content cl-chat-bubble__content--user">
      {message.content}
    </div>
  {:else}
    <div class="cl-chat-bubble__content">
      <div
        class="cl-chat-markdown"
        bind:this={markdownContainer}
      ></div>
    </div>
  {/if}
  <div class="cl-chat-bubble__time">
    {formatRelativeTime(message.timestamp)}
  </div>
</div>

<style>
  .cl-chat-bubble {
    max-width: 85%;
    margin-bottom: 8px;
    display: flex;
    flex-direction: column;
  }

  .cl-chat-bubble-user {
    align-self: flex-end;
    align-items: flex-end;
  }

  .cl-chat-bubble-agent {
    align-self: flex-start;
    align-items: flex-start;
  }

  .cl-chat-bubble__content {
    padding: 8px 12px;
    border-radius: var(--radius-m, 8px);
    line-height: 1.5;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  .cl-chat-bubble-user .cl-chat-bubble__content {
    background: var(--interactive-accent);
    color: var(--text-on-accent);
    border-bottom-right-radius: var(--radius-s, 4px);
  }

  .cl-chat-bubble__content--user {
    white-space: pre-wrap;
  }

  .cl-chat-bubble-agent .cl-chat-bubble__content {
    background: var(--background-secondary);
    color: var(--text-normal);
    border-bottom-left-radius: var(--radius-s, 4px);
  }

  .cl-chat-bubble--streaming .cl-chat-bubble__content {
    border: 1px solid var(--interactive-accent);
  }

  .cl-chat-bubble__time {
    font-size: 0.7em;
    color: var(--text-faint);
    margin-top: 2px;
    padding: 0 4px;
  }

  /* Markdown rendering container - CSS isolation */
  .cl-chat-markdown {
    /* Reset Markdown element margins to fit bubble context */
  }

  .cl-chat-markdown :global(p) {
    margin: 0.4em 0;
  }

  .cl-chat-markdown :global(p:first-child) {
    margin-top: 0;
  }

  .cl-chat-markdown :global(p:last-child) {
    margin-bottom: 0;
  }

  .cl-chat-markdown :global(pre) {
    margin: 0.5em 0;
    padding: 8px;
    border-radius: var(--radius-s, 4px);
    background: var(--background-primary);
    overflow-x: auto;
  }

  .cl-chat-markdown :global(code) {
    font-size: 0.9em;
  }

  .cl-chat-markdown :global(ul),
  .cl-chat-markdown :global(ol) {
    margin: 0.3em 0;
    padding-left: 1.5em;
  }

  .cl-chat-markdown :global(blockquote) {
    margin: 0.4em 0;
    padding-left: 8px;
    border-left: 3px solid var(--interactive-accent);
    color: var(--text-muted);
  }

  /* Internal link styling */
  .cl-chat-markdown :global(a.internal-link) {
    color: var(--text-accent);
    text-decoration: none;
    cursor: pointer;
  }

  .cl-chat-markdown :global(a.internal-link:hover) {
    text-decoration: underline;
  }
</style>
