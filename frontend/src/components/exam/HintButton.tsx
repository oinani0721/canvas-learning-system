/**
 * HintButton - 4-level progressive hint system for exam questions.
 *
 * Displays the current hint level (1/4) and requests the next hint
 * from the backend. Hint content is delivered via the ChatPanel
 * (the backend appends the hint to the exam conversation).
 *
 * Levels:
 *   1 - Directional nudge
 *   2 - Key concept hint
 *   3 - Partial answer
 *   4 - Full explanation
 *
 * Callers:
 * - ExamCanvas.tsx (top toolbar)
 *
 * Wiring:
 * - POST /api/v1/exam/{examId}/hint
 * - useExamStore.currentExamId
 */

import { useState, useCallback } from 'react';
import { ApiClient } from '../../services/api-client';
import { useExamStore } from '../../stores/exam-store';

const apiClient = new ApiClient();

const HINT_LABELS = [
  'Directional nudge',
  'Key concept hint',
  'Partial answer',
  'Full explanation',
];

export function HintButton() {
  const currentExamId = useExamStore((s) => s.currentExamId);
  const hintLevel = useExamStore((s) => s.hintLevel);
  const incrementHintLevel = useExamStore((s) => s.incrementHintLevel);
  const [isLoading, setIsLoading] = useState(false);
  const maxLevel = 4;

  const requestHint = useCallback(async () => {
    if (!currentExamId || hintLevel >= maxLevel || isLoading) return;

    setIsLoading(true);
    try {
      await apiClient.post(`/api/v1/exam/${currentExamId}/hint`, {
        hint_level: hintLevel + 1,
      });
      incrementHintLevel();
    } catch (err) {
      console.error('[HintButton] Failed to request hint:', err);
    } finally {
      setIsLoading(false);
    }
  }, [currentExamId, hintLevel, isLoading, incrementHintLevel]);

  const isMaxed = hintLevel >= maxLevel;

  return (
    <div className="relative group">
      <button
        onClick={requestHint}
        disabled={isMaxed || isLoading || !currentExamId}
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
          isMaxed
            ? 'bg-[#313244] text-[#585b70] cursor-not-allowed'
            : isLoading
              ? 'bg-[#313244] text-[#a6adc8] cursor-wait'
              : 'bg-[#313244] text-[#f9e2af] hover:bg-[#45475a] hover:text-[#f9e2af]'
        }`}
        title={
          isMaxed
            ? 'All hints used'
            : `Request hint (${hintLevel}/${maxLevel} used)`
        }
      >
        {/* Lightbulb icon */}
        <svg
          className="w-3.5 h-3.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path d="M9.663 17h4.674M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        {isLoading ? (
          <span className="animate-pulse">...</span>
        ) : (
          <span>
            Hint {hintLevel}/{maxLevel}
          </span>
        )}
      </button>

      {/* Tooltip showing next hint level description */}
      {!isMaxed && !isLoading && (
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 px-2 py-1 bg-[#1e1e2e] border border-[#45475a] rounded text-xs text-[#a6adc8] whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
          Next: {HINT_LABELS[hintLevel]}
        </div>
      )}
    </div>
  );
}
