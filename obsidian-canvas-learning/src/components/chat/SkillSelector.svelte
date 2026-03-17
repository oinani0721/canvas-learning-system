<!--
  Canvas Learning System - Skill Selector
  Story 3.5: /command Skill Integration (AC-1, Task 1)

  Floating panel that appears above the InputBar when user types '/'.
  Displays registered skills with fuzzy search, keyboard navigation,
  and click/Enter selection.
-->
<script lang="ts">
  import type { Skill } from '../../services/skill-registry';

  let {
    skills,
    filterQuery = '',
    onSelect,
    onClose,
  }: {
    skills: Skill[];
    filterQuery?: string;
    onSelect: (skill: Skill) => void;
    onClose: () => void;
  } = $props();

  let selectedIndex = $state(0);

  /**
   * Fuzzy match: check if all characters of query appear in order in text.
   * Story 3.5 spec fuzzy search implementation.
   */
  function fuzzyMatch(query: string, text: string): boolean {
    const q = query.toLowerCase();
    const t = text.toLowerCase();
    let qi = 0;
    for (let ti = 0; ti < t.length && qi < q.length; ti++) {
      if (t[ti] === q[qi]) qi++;
    }
    return qi === q.length;
  }

  let filteredSkills = $derived.by(() => {
    if (!filterQuery) return skills;
    return skills.filter(
      (s) => fuzzyMatch(filterQuery, s.name) || fuzzyMatch(filterQuery, s.description),
    );
  });

  // Reset selection when filtered list changes
  $effect(() => {
    if (selectedIndex >= filteredSkills.length) {
      selectedIndex = Math.max(0, filteredSkills.length - 1);
    }
  });

  function handleKeydown(event: KeyboardEvent): void {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        selectedIndex = Math.min(selectedIndex + 1, filteredSkills.length - 1);
        break;
      case 'ArrowUp':
        event.preventDefault();
        selectedIndex = Math.max(selectedIndex - 1, 0);
        break;
      case 'Enter':
        event.preventDefault();
        if (filteredSkills[selectedIndex]) {
          onSelect(filteredSkills[selectedIndex]);
        }
        break;
      case 'Escape':
        event.preventDefault();
        onClose();
        break;
    }
  }

  function handleItemClick(skill: Skill): void {
    onSelect(skill);
  }
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="cl-chat-skill-selector"
  onkeydown={handleKeydown}
  role="listbox"
  aria-label="技能列表"
>
  {#if filteredSkills.length === 0}
    <div class="cl-chat-skill-selector__empty">
      没有匹配的技能
    </div>
  {:else}
    {#each filteredSkills as skill, index}
      <!-- svelte-ignore a11y_click_events_have_key_events -->
      <div
        class="cl-chat-skill-selector__item"
        class:cl-chat-skill-selector__item--selected={index === selectedIndex}
        role="option"
        aria-selected={index === selectedIndex}
        onclick={() => handleItemClick(skill)}
      >
        <span class="cl-chat-skill-selector__icon">{skill.icon}</span>
        <div class="cl-chat-skill-selector__text">
          <span class="cl-chat-skill-selector__name">/{skill.commandName}</span>
          <span class="cl-chat-skill-selector__desc">{skill.description}</span>
        </div>
      </div>
    {/each}
  {/if}
</div>

<style>
  .cl-chat-skill-selector {
    position: absolute;
    bottom: 100%;
    left: 0;
    right: 0;
    max-height: 280px;
    overflow-y: auto;
    background: var(--background-primary);
    border: 1px solid var(--background-modifier-border);
    border-bottom: none;
    border-radius: var(--radius-m, 8px) var(--radius-m, 8px) 0 0;
    box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.15);
    z-index: 100;
  }

  .cl-chat-skill-selector__empty {
    padding: 12px 16px;
    color: var(--text-faint);
    font-size: 0.85em;
    text-align: center;
  }

  .cl-chat-skill-selector__item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    cursor: pointer;
    transition: background 0.1s ease;
  }

  .cl-chat-skill-selector__item:hover,
  .cl-chat-skill-selector__item--selected {
    background: var(--background-secondary);
  }

  .cl-chat-skill-selector__icon {
    font-size: 1.1em;
    flex-shrink: 0;
    width: 24px;
    text-align: center;
  }

  .cl-chat-skill-selector__text {
    display: flex;
    flex-direction: column;
    gap: 1px;
    overflow: hidden;
  }

  .cl-chat-skill-selector__name {
    font-size: 0.9em;
    font-weight: 500;
    color: var(--text-normal);
  }

  .cl-chat-skill-selector__desc {
    font-size: 0.78em;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
</style>
