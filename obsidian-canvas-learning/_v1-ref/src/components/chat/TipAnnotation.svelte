<!--
  Canvas Learning System - Tip Annotation Floating Panel
  Story 3.6: Tips Annotation + Error Archiving (AC-1, AC-5)

  Appears above selected text in chat messages.
  Two actions: "Tag" (classify with label) and "Tips" (save to Graphiti).

  Positioning: absolute, calculated from Selection bounding rect.
  Closes on: click outside, selection cleared.

  [Source: _bmad-output/implementation-artifacts/3-6-tips-annotation-error-archiving.md#Task 1]
-->
<script lang="ts">
  import { Notice } from 'obsidian';
  import { TipsService, TIP_TAG_CONFIG } from '../../services/tips-service';
  import type { TipTag, TipData } from '../../services/tips-service';
  import type { ApiClient } from '../../services/api-client';

  let {
    apiClient,
    nodeId = '',
  }: {
    apiClient: ApiClient;
    nodeId?: string;
  } = $props();

  // ── Panel State ────────────────────────────────────────────────────────

  let visible = $state(false);
  let panelTop = $state(0);
  let panelLeft = $state(0);
  let selectedText = $state('');
  let showTipForm = $state(false);
  let showTagSelector = $state(false);

  // ── Tips Form State ────────────────────────────────────────────────────

  let tipTitle = $state('');
  let tipTags: TipTag[] = $state([]);
  let saving = $state(false);

  // ── Services ──────────────────────────────────────────────────────────

  const tipsService = new TipsService(apiClient);

  // ── Selection Detection ───────────────────────────────────────────────

  function handleMouseUp(e: MouseEvent): void {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !selection.toString().trim()) {
      // No selection or empty selection - hide panel
      if (!showTipForm && !showTagSelector) {
        visible = false;
      }
      return;
    }

    // Check if selection is within a chat bubble
    const anchorNode = selection.anchorNode;
    if (!anchorNode) return;
    const chatBubble = (anchorNode.nodeType === Node.TEXT_NODE
      ? anchorNode.parentElement
      : anchorNode as Element)?.closest('.cl-chat-bubble');
    if (!chatBubble) return;

    selectedText = selection.toString().trim();
    if (!selectedText) return;

    // Position panel above selection
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    const panelWidth = 160;
    const panelHeight = 36;
    panelTop = rect.top - panelHeight - 8;
    panelLeft = rect.left + (rect.width - panelWidth) / 2;

    // Ensure panel stays within viewport
    if (panelLeft < 8) panelLeft = 8;
    if (panelTop < 8) panelTop = rect.bottom + 8;

    visible = true;
    showTipForm = false;
    showTagSelector = false;
  }

  function handleClickOutside(e: MouseEvent): void {
    const target = e.target as Element;
    if (target?.closest('.cl-chat-annotation-panel')) return;
    visible = false;
    showTipForm = false;
    showTagSelector = false;
  }

  // ── Tag Action ────────────────────────────────────────────────────────

  function openTagSelector(): void {
    showTagSelector = true;
    showTipForm = false;
  }

  function applyTag(tag: TipTag): void {
    // Dispatch custom event for MessageBubble to handle tag display
    const event = new CustomEvent('cl-tag-applied', {
      bubbles: true,
      detail: { text: selectedText, tag, nodeId },
    });
    document.dispatchEvent(event);

    new Notice(`Tag "${TIP_TAG_CONFIG[tag].label}" applied`, 2000);
    visible = false;
    showTagSelector = false;
  }

  // ── Tips Action ───────────────────────────────────────────────────────

  function openTipForm(): void {
    showTipForm = true;
    showTagSelector = false;
    tipTitle = selectedText.length > 30
      ? selectedText.substring(0, 30) + '...'
      : selectedText;
    tipTags = [];
  }

  function toggleTipTag(tag: TipTag): void {
    if (tipTags.includes(tag)) {
      tipTags = tipTags.filter((t) => t !== tag);
    } else {
      tipTags = [...tipTags, tag];
    }
  }

  async function saveTip(): Promise<void> {
    if (!tipTitle.trim() || !selectedText || saving) return;

    saving = true;

    const tipData: TipData = {
      content: selectedText,
      title: tipTitle.trim(),
      tags: tipTags,
      nodeId,
      sourceTimestamp: new Date().toISOString(),
    };

    const result = await tipsService.saveTip(tipData);

    saving = false;

    if (result.saved) {
      new Notice('Tips saved', 2000);
      visible = false;
      showTipForm = false;
    } else {
      new Notice(`Tips save failed: ${result.message}`, 4000);
    }
  }

  // ── Lifecycle ─────────────────────────────────────────────────────────

  $effect(() => {
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  });
</script>

{#if visible}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="cl-chat-annotation-panel"
    style="top: {panelTop}px; left: {panelLeft}px;"
    onmousedown={(e) => e.stopPropagation()}
  >
    {#if !showTipForm && !showTagSelector}
      <!-- Main action buttons -->
      <button
        class="cl-annotation-btn"
        onclick={openTagSelector}
        title="Tag this text"
      >
        Tag
      </button>
      <button
        class="cl-annotation-btn cl-annotation-btn--primary"
        onclick={openTipForm}
        title="Save as Tip"
      >
        Tips
      </button>
    {:else if showTagSelector}
      <!-- Tag selector -->
      <div class="cl-tag-selector">
        {#each Object.entries(TIP_TAG_CONFIG) as [tag, config]}
          <button
            class="cl-tag-btn"
            style="--tag-color: {config.color};"
            onclick={() => applyTag(tag as TipTag)}
          >
            {config.label}
          </button>
        {/each}
      </div>
    {:else if showTipForm}
      <!-- Tips mini-form -->
      <div class="cl-tip-form">
        <input
          class="cl-tip-title-input"
          type="text"
          placeholder="Tip title..."
          bind:value={tipTitle}
        />
        <div class="cl-tip-tags">
          {#each Object.entries(TIP_TAG_CONFIG) as [tag, config]}
            <label
              class="cl-tip-tag-label"
              class:cl-tip-tag-label--active={tipTags.includes(tag as TipTag)}
              style="--tag-color: {config.color};"
            >
              <input
                type="checkbox"
                checked={tipTags.includes(tag as TipTag)}
                onchange={() => toggleTipTag(tag as TipTag)}
              />
              {config.label}
            </label>
          {/each}
        </div>
        <button
          class="cl-tip-save-btn"
          onclick={saveTip}
          disabled={saving || !tipTitle.trim()}
        >
          {saving ? 'Saving...' : 'Save'}
        </button>
      </div>
    {/if}
  </div>
{/if}

<style>
  .cl-chat-annotation-panel {
    position: fixed;
    z-index: 10000;
    display: flex;
    gap: 4px;
    background: var(--background-primary);
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-m, 8px);
    padding: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }

  .cl-annotation-btn {
    padding: 4px 12px;
    border: none;
    border-radius: var(--radius-s, 4px);
    background: var(--background-secondary);
    color: var(--text-normal);
    cursor: pointer;
    font-size: 0.85em;
    white-space: nowrap;
  }

  .cl-annotation-btn:hover {
    background: var(--background-modifier-hover);
  }

  .cl-annotation-btn--primary {
    background: var(--interactive-accent);
    color: var(--text-on-accent);
  }

  .cl-annotation-btn--primary:hover {
    opacity: 0.9;
  }

  /* Tag selector */
  .cl-tag-selector {
    display: flex;
    gap: 3px;
  }

  .cl-tag-btn {
    padding: 3px 8px;
    border: none;
    border-radius: var(--radius-s, 4px);
    background: var(--tag-color, var(--background-secondary));
    color: white;
    cursor: pointer;
    font-size: 0.8em;
    opacity: 0.85;
  }

  .cl-tag-btn:hover {
    opacity: 1;
  }

  /* Tip form */
  .cl-tip-form {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 200px;
    padding: 4px;
  }

  .cl-tip-title-input {
    width: 100%;
    padding: 4px 8px;
    border: 1px solid var(--background-modifier-border);
    border-radius: var(--radius-s, 4px);
    background: var(--background-primary);
    color: var(--text-normal);
    font-size: 0.85em;
  }

  .cl-tip-tags {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }

  .cl-tip-tag-label {
    display: flex;
    align-items: center;
    gap: 2px;
    padding: 2px 6px;
    border-radius: var(--radius-s, 4px);
    font-size: 0.75em;
    cursor: pointer;
    background: var(--background-secondary);
    color: var(--text-muted);
  }

  .cl-tip-tag-label--active {
    background: var(--tag-color, var(--interactive-accent));
    color: white;
  }

  .cl-tip-tag-label input[type="checkbox"] {
    display: none;
  }

  .cl-tip-save-btn {
    padding: 4px 12px;
    border: none;
    border-radius: var(--radius-s, 4px);
    background: var(--interactive-accent);
    color: var(--text-on-accent);
    cursor: pointer;
    font-size: 0.85em;
  }

  .cl-tip-save-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
