/**
 * InputBar — Chat message input with auto-resize and keyboard shortcuts.
 * Story 3-3 AC-5
 *
 * Features:
 * - Multi-line textarea with auto-expand (1 to 6 lines)
 * - Enter to send, Shift+Enter for new line, Escape to clear
 * - Empty message cannot be sent (button disabled)
 * - Disabled during streaming (prevents double-send)
 * - Emits onSlashTrigger when '/' is typed at start of line (Story 3.5 hook)
 *
 * Callers:
 * - ChatPanel renders this at the bottom of the panel
 *
 * Wiring:
 * - onSend callback triggers useChatStore.sendMessage()
 * - onSlashTrigger is a forward-looking hook for Story 3.5 SkillSelector
 */

import {
  useState,
  useRef,
  useCallback,
  useEffect,
  type KeyboardEvent,
  type FormEvent,
} from 'react';

interface InputBarProps {
  /** Whether a streaming response is in progress — disables input. */
  isStreaming: boolean;
  /** Whether the engine is unavailable (CLI not found, etc.). */
  engineUnavailable: boolean;
  /** Node title for placeholder text. */
  nodeTitle: string;
  /** Called when the user submits a message. */
  onSend: (text: string) => void;
  /**
   * Called when '/' is typed at the start of a line.
   * Provides the current input value for prefix matching.
   * Story 3.5 will consume this event for SkillSelector.
   */
  onSlashTrigger?: (inputValue: string) => void;
  /**
   * Story 3-10: Whether subscription quota is exhausted.
   * When true, shows a placeholder indicating quota exhaustion.
   */
  quotaExhausted?: boolean;
}

/** Maximum number of visible lines before the textarea stops growing. */
const MAX_LINES = 6;
/** Approximate single-line height in px. */
const LINE_HEIGHT = 22;

export function InputBar({
  isStreaming,
  engineUnavailable,
  nodeTitle,
  onSend,
  onSlashTrigger,
  quotaExhausted = false,
}: InputBarProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isDisabled = isStreaming || engineUnavailable || quotaExhausted;
  const canSend = !isDisabled && input.trim().length > 0;

  // ── Auto-resize textarea ──────────────────────────────────────────────

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    // Reset to auto so scrollHeight recalculates from content
    el.style.height = 'auto';
    const maxHeight = LINE_HEIGHT * MAX_LINES;
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
  }, []);

  // Adjust height whenever input changes
  useEffect(() => {
    adjustHeight();
  }, [input, adjustHeight]);

  // ── Submit handler ────────────────────────────────────────────────────

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || isDisabled) return;
    onSend(trimmed);
    setInput('');
    // Reset height after clearing
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [input, isDisabled, onSend]);

  const handleSubmit = useCallback(
    (e: FormEvent) => {
      e.preventDefault();
      handleSend();
    },
    [handleSend],
  );

  // ── Keyboard shortcuts ────────────────────────────────────────────────

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
        return;
      }

      if (e.key === 'Escape') {
        e.preventDefault();
        setInput('');
        return;
      }
    },
    [handleSend],
  );

  // ── Input change with slash detection ─────────────────────────────────

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const value = e.target.value;
      setInput(value);

      // Detect '/' at start of input for skill selector trigger (Story 3.5)
      if (onSlashTrigger && value.startsWith('/')) {
        onSlashTrigger(value);
      }
    },
    [onSlashTrigger],
  );

  // ── Render ────────────────────────────────────────────────────────────

  const placeholder = quotaExhausted
    ? '额度已用完，请等待重置或切换 API Key...'
    : engineUnavailable
      ? 'Claude Code not available...'
      : `Ask about "${nodeTitle}"...`;

  return (
    <form
      onSubmit={handleSubmit}
      className="shrink-0 border-t border-gray-200 px-3 py-2"
    >
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isDisabled}
          rows={1}
          className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm
                     focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400
                     disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed
                     placeholder:text-gray-400"
        />
        <button
          type="submit"
          disabled={!canSend}
          className="shrink-0 px-3 py-2 bg-blue-500 text-white text-sm font-medium rounded-lg
                     hover:bg-blue-600 transition-colors
                     disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {isStreaming ? (
            <svg
              className="w-4 h-4 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
          ) : (
            'Send'
          )}
        </button>
      </div>
      <p className="text-[10px] text-gray-400 mt-1">
        Enter to send, Shift+Enter for new line, Escape to clear
      </p>
    </form>
  );
}
