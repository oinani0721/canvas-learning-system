<!--
  Canvas Learning System - Streaming Indicator
  Story 3.3: ChatPanel UI (AC-2, Task 4.1)

  Displays a typing animation / cursor blink while the Agent is generating
  a streaming response. CSS uses Obsidian variables for theme compatibility.
-->
<script lang="ts">
  /**
   * StreamingIndicator shown inside an assistant bubble while streaming.
   * Three-dot animation using CSS keyframes.
   */
</script>

<div class="cl-chat-streaming" aria-label="Agent is typing">
  <span class="cl-chat-streaming__dot"></span>
  <span class="cl-chat-streaming__dot"></span>
  <span class="cl-chat-streaming__dot"></span>
</div>

<style>
  .cl-chat-streaming {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 8px 12px;
  }

  .cl-chat-streaming__dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--text-muted);
    animation: cl-dot-bounce 1.4s infinite ease-in-out both;
  }

  .cl-chat-streaming__dot:nth-child(1) {
    animation-delay: -0.32s;
  }

  .cl-chat-streaming__dot:nth-child(2) {
    animation-delay: -0.16s;
  }

  .cl-chat-streaming__dot:nth-child(3) {
    animation-delay: 0s;
  }

  @keyframes cl-dot-bounce {
    0%, 80%, 100% {
      transform: scale(0.6);
      opacity: 0.4;
    }
    40% {
      transform: scale(1);
      opacity: 1;
    }
  }
</style>
