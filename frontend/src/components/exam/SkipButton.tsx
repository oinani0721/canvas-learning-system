/**
 * SkipButton — Skip current exam question with confirmation dialog.
 *
 * Shows a confirmation dialog before posting to the backend.
 * Skipping a question is recorded as a non-answer in the exam session.
 *
 * Callers:
 * - ExamCanvas.tsx (top toolbar)
 *
 * Wiring:
 * - POST /api/v1/exam/{examId}/skip
 * - useExamStore.currentExamId, currentNodeId
 */

import { useState, useCallback } from 'react';
import { ApiClient } from '../../services/api-client';
import { useExamStore } from '../../stores/exam-store';

const apiClient = new ApiClient();

interface SkipButtonProps {
  /** Called after the skip is successfully recorded. */
  onSkipped?: () => void;
}

export function SkipButton({ onSkipped }: SkipButtonProps) {
  const currentExamId = useExamStore((s) => s.currentExamId);
  const currentNodeId = useExamStore((s) => s.currentNodeId);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSkip = useCallback(async () => {
    if (!currentExamId || isLoading) return;

    setIsLoading(true);
    try {
      await apiClient.post(`/api/v1/exam/${currentExamId}/skip`, {
        node_id: currentNodeId,
      });
      setShowConfirm(false);
      onSkipped?.();
    } catch (err) {
      console.error('[SkipButton] Failed to skip question:', err);
    } finally {
      setIsLoading(false);
    }
  }, [currentExamId, currentNodeId, isLoading, onSkipped]);

  return (
    <>
      <button
        onClick={() => setShowConfirm(true)}
        disabled={!currentExamId}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium bg-[#313244] text-[#a6adc8] hover:bg-[#45475a] hover:text-[#cdd6f4] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title="Skip current question"
      >
        {/* Forward/skip icon */}
        <svg
          className="w-3.5 h-3.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3 8.688c0-.864.933-1.405 1.683-.977l7.108 4.062a1.125 1.125 0 010 1.953l-7.108 4.062A1.125 1.125 0 013 16.81V8.688zM12.75 8.688c0-.864.933-1.405 1.683-.977l7.108 4.062a1.125 1.125 0 010 1.953l-7.108 4.062a1.125 1.125 0 01-1.683-.977V8.688z"
          />
        </svg>
        <span>Skip</span>
      </button>

      {/* Confirmation dialog */}
      {showConfirm && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setShowConfirm(false)}
        >
          <div
            className="bg-[#1e1e2e] border border-[#45475a] rounded-lg shadow-xl p-5 w-80"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 mb-3">
              <svg
                className="w-5 h-5 text-[#f9e2af]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                />
              </svg>
              <h3 className="text-sm font-medium text-[#cdd6f4]">
                Skip Question?
              </h3>
            </div>
            <p className="text-xs text-[#a6adc8] mb-4 leading-relaxed">
              Skipping will record this as unanswered. The question may appear
              again in future exam sessions to reinforce your learning.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-3 py-1.5 text-xs text-[#a6adc8] hover:text-[#cdd6f4] hover:bg-[#313244] rounded-md transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSkip}
                disabled={isLoading}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  isLoading
                    ? 'bg-[#45475a] text-[#585b70] cursor-wait'
                    : 'bg-[#fab387] text-[#1e1e2e] hover:bg-[#eba0ac]'
                }`}
              >
                {isLoading ? 'Skipping...' : 'Skip Question'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
