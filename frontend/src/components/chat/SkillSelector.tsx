/**
 * SkillSelector — Floating popup for "/" command skill selection.
 * MVP #13: Skill selector integration.
 *
 * Features:
 * - Fetches available skills from GET /api/v1/skills
 * - Filters by query string (real-time search)
 * - Keyboard navigation (ArrowUp/ArrowDown/Enter/Escape)
 * - Click to select a skill
 * - Escape or click-outside to dismiss
 *
 * Callers:
 * - ChatPanel renders this above the InputBar when '/' is typed
 *
 * Wiring:
 * - ApiClient.getSkills() fetches the skill list
 * - onSelect callback sends the skill command to the chat
 * - onDismiss callback hides this component
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { ApiClient, type SkillItem } from '../../services/api-client';
import { useChatStore } from '../../stores/chat-store';

const skillApiClient = new ApiClient();

interface SkillSelectorProps {
  /** Current search query (text after '/') */
  query: string;
  /** Called when a skill is selected. Receives the full command string. */
  onSelect: (command: string) => void;
  /** Called when the selector should be dismissed (Escape, click-outside). */
  onDismiss: () => void;
}

export function SkillSelector({ query, onSelect, onDismiss }: SkillSelectorProps) {
  const [skills, setSkills] = useState<SkillItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeIndex, setActiveIndex] = useState(0);
  const listRef = useRef<HTMLUListElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // SDK slash commands from Agent SDK init message
  const sdkSlashCommands = useChatStore((s) => s.slashCommands);

  // ── Fetch skills on mount + merge SDK slash commands ────────────────

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    skillApiClient.getSkills().then((fetched) => {
      if (!cancelled) {
        // Merge SDK slash commands as SkillItem entries
        const sdkItems: SkillItem[] = sdkSlashCommands.map((cmd) => ({
          id: `sdk-${cmd.name}`,
          name: cmd.name.replace(/^\//, ''),
          command: cmd.name.replace(/^\//, ''),
          description: cmd.description || 'SDK built-in command',
          category: 'SDK',
          // argumentHint available in cmd.argumentHint if needed
        }));
        // Deduplicate: SDK commands take precedence if name conflicts
        const fetchedNames = new Set(sdkItems.map((s) => s.command));
        const merged = [...sdkItems, ...fetched.filter((s) => !fetchedNames.has(s.command))];
        setSkills(merged);
        setLoading(false);
      }
    }).catch(() => {
      // Backend unavailable — show SDK commands only
      if (!cancelled) {
        const sdkItems: SkillItem[] = sdkSlashCommands.map((cmd) => ({
          id: `sdk-${cmd.name}`,
          name: cmd.name.replace(/^\//, ''),
          command: cmd.name.replace(/^\//, ''),
          description: cmd.description || 'SDK built-in command',
          category: 'SDK',
          // argumentHint available in cmd.argumentHint if needed
        }));
        setSkills(sdkItems);
        setLoading(false);
      }
    });
    return () => { cancelled = true; };
  }, [sdkSlashCommands]);

  // ── Filter skills by query ─────────────────────────────────────────

  const filtered = skills.filter((s) => {
    if (!query) return true;
    const q = query.toLowerCase();
    return (
      s.name.toLowerCase().includes(q) ||
      s.command.toLowerCase().includes(q) ||
      (s.description && s.description.toLowerCase().includes(q)) ||
      (s.category && s.category.toLowerCase().includes(q))
    );
  });

  // Reset active index when filter changes
  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  // ── Keyboard navigation ────────────────────────────────────────────

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        onDismiss();
        return;
      }

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveIndex((prev) => Math.min(prev + 1, filtered.length - 1));
        return;
      }

      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveIndex((prev) => Math.max(prev - 1, 0));
        return;
      }

      if (e.key === 'Enter' && filtered.length > 0) {
        e.preventDefault();
        e.stopPropagation();
        const selected = filtered[activeIndex];
        if (selected) {
          onSelect(`/${selected.command}`);
        }
        return;
      }
    },
    [filtered, activeIndex, onSelect, onDismiss],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown, true);
    return () => document.removeEventListener('keydown', handleKeyDown, true);
  }, [handleKeyDown]);

  // ── Click-outside to dismiss ───────────────────────────────────────

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as HTMLElement)) {
        onDismiss();
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [onDismiss]);

  // ── Scroll active item into view ──────────────────────────────────

  useEffect(() => {
    const list = listRef.current;
    if (!list) return;
    const activeEl = list.children[activeIndex] as HTMLElement | undefined;
    if (activeEl) {
      activeEl.scrollIntoView({ block: 'nearest' });
    }
  }, [activeIndex]);

  // ── Render ─────────────────────────────────────────────────────────

  return (
    <div
      ref={containerRef}
      className="shrink-0 border-t border-[#313244] bg-[#1e1e2e] shadow-lg rounded-t-lg max-h-60 overflow-hidden flex flex-col"
    >
      {/* Header */}
      <div className="px-3 py-1.5 border-b border-[#313244] flex items-center justify-between">
        <span className="text-xs font-medium text-[#6c7086]">
          Skills {query && `— "${query}"`}
        </span>
        <button
          type="button"
          onClick={onDismiss}
          className="text-xs text-[#585b70] hover:text-[#a6adc8]"
          aria-label="Dismiss skill selector"
        >
          Esc
        </button>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="px-3 py-4 text-center">
          <span className="text-xs text-[#585b70]">Loading skills...</span>
        </div>
      )}

      {/* Empty state */}
      {!loading && filtered.length === 0 && (
        <div className="px-3 py-4 text-center">
          <span className="text-xs text-[#585b70]">
            {skills.length === 0
              ? 'No skills available from backend'
              : `No skills matching "${query}"`}
          </span>
        </div>
      )}

      {/* Skills list */}
      {!loading && filtered.length > 0 && (
        <ul
          ref={listRef}
          role="listbox"
          className="overflow-y-auto flex-1"
        >
          {filtered.map((skill, idx) => (
            <li
              key={skill.id}
              role="option"
              aria-selected={idx === activeIndex}
              onClick={() => onSelect(`/${skill.command}`)}
              className={`px-3 py-2 cursor-pointer flex items-start gap-2 transition-colors ${
                idx === activeIndex
                  ? 'bg-[#313244] text-[#89b4fa]'
                  : 'text-[#cdd6f4] hover:bg-[#313244]/50'
              }`}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-sm font-medium truncate">
                    /{skill.command}
                  </span>
                  {skill.category && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#313244] text-[#6c7086] shrink-0">
                      {skill.category}
                    </span>
                  )}
                </div>
                {skill.description && (
                  <p className="text-xs text-[#6c7086] mt-0.5 truncate">
                    {skill.description}
                  </p>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* Footer hint */}
      <div className="px-3 py-1 border-t border-[#313244]">
        <span className="text-[10px] text-[#585b70]">
          Arrow keys to navigate, Enter to select, Esc to dismiss
        </span>
      </div>
    </div>
  );
}
