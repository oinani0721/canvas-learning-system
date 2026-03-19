/**
 * ExamModeSelector — Exam mode selection modal (Story 6.2 AC-5)
 *
 * Displays 3 exam mode cards with descriptions:
 *   - Point-to-Point (point_to_point): Targeted drill on a specific concept
 *   - Comprehensive (comprehensive): Full coverage of related concepts
 *   - Mixed (mixed): AI-recommended blend of both strategies
 *
 * Fetches a smart recommendation from the backend via analyzeCanvas,
 * and shows a "Recommended" badge on the suggested mode.
 *
 * Callers:
 * - App.tsx: triggered when user clicks "Generate Exam" from dashboard or profile
 *
 * Wiring:
 * - ApiClient.analyzeCanvas() for mode recommendation
 * - useExamStore.setExamMode() + createExam() on confirm
 */

import { useState, useEffect, useCallback } from 'react';
import { ApiClient } from '../../services/api-client';
import { useExamStore, type ExamMode } from '../../stores/exam-store';

const apiClient = new ApiClient();

interface ExamModeSelectorProps {
  /** Source canvas board ID to create the exam from. */
  sourceCanvasId: string;
  /** Optional target node ID (for point-to-point from LearningProfile). */
  targetNodeId?: string;
  /** Called when exam is created successfully. */
  onExamCreated: (examId: string) => void;
  /** Called when the modal is dismissed. */
  onCancel: () => void;
}

interface ModeOption {
  mode: ExamMode;
  title: string;
  description: string;
  icon: React.ReactNode;
}

const MODE_OPTIONS: ModeOption[] = [
  {
    mode: 'point_to_point',
    title: 'Point-to-Point',
    description:
      'Targeted drill on a specific concept. Tests precise recall and understanding of individual knowledge points.',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
      </svg>
    ),
  },
  {
    mode: 'comprehensive',
    title: 'Comprehensive',
    description:
      'Full coverage exam across related concepts. Tests breadth of understanding and connections between topics.',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
      </svg>
    ),
  },
  {
    mode: 'mixed',
    title: 'Mixed',
    description:
      'AI-recommended blend combining targeted drills and broad coverage based on your learning patterns.',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
      </svg>
    ),
  },
];

export function ExamModeSelector({
  sourceCanvasId,
  targetNodeId,
  onExamCreated,
  onCancel,
}: ExamModeSelectorProps) {
  const [selectedMode, setSelectedMode] = useState<ExamMode>('mixed');
  const [recommendedMode, setRecommendedMode] = useState<string | null>(null);
  const [recommendConfidence, setRecommendConfidence] = useState<number>(0);
  const [isAnalyzing, setIsAnalyzing] = useState(true);
  const [isCreating, setIsCreating] = useState(false);

  const createExam = useExamStore((s) => s.createExam);

  // Fetch AI recommendation on mount
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setIsAnalyzing(true);
      const result = await apiClient.analyzeCanvas(sourceCanvasId, targetNodeId);
      if (!cancelled && result) {
        setRecommendedMode(result.recommendedMode);
        setRecommendConfidence(result.confidence);
        // Pre-select recommended mode
        const modeMap: Record<string, ExamMode> = {
          point_to_point: 'point_to_point',
          comprehensive: 'comprehensive',
          mixed: 'mixed',
        };
        const mapped = modeMap[result.recommendedMode];
        if (mapped) {
          setSelectedMode(mapped);
        }
      }
      if (!cancelled) {
        setIsAnalyzing(false);
      }
    })();
    return () => { cancelled = true; };
  }, [sourceCanvasId, targetNodeId]);

  const handleConfirm = useCallback(async () => {
    if (isCreating) return;
    setIsCreating(true);
    const examId = await createExam(sourceCanvasId, selectedMode, targetNodeId);
    if (examId) {
      onExamCreated(examId);
    } else {
      setIsCreating(false);
    }
  }, [isCreating, createExam, sourceCanvasId, selectedMode, targetNodeId, onExamCreated]);

  // Close on Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onCancel]);

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
      onClick={onCancel}
    >
      <div
        className="bg-[#1e1e2e] border border-[#45475a] rounded-xl shadow-2xl w-[480px] max-w-[95vw]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#313244]">
          <h2 className="text-lg font-semibold text-[#cdd6f4]">
            Select Exam Mode
          </h2>
          <p className="text-xs text-[#a6adc8] mt-1">
            Choose how you want to be tested on this whiteboard
          </p>
        </div>

        {/* Mode cards */}
        <div className="px-6 py-4 space-y-3">
          {MODE_OPTIONS.map((option) => {
            const isSelected = selectedMode === option.mode;
            const isRecommended = recommendedMode === option.mode;

            return (
              <button
                key={option.mode}
                onClick={() => setSelectedMode(option.mode)}
                className={`w-full text-left p-4 rounded-lg border transition-all ${
                  isSelected
                    ? 'border-[#89b4fa] bg-[#89b4fa]/10'
                    : 'border-[#313244] bg-[#181825] hover:border-[#45475a] hover:bg-[#313244]/50'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`shrink-0 mt-0.5 ${
                      isSelected ? 'text-[#89b4fa]' : 'text-[#585b70]'
                    }`}
                  >
                    {option.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-sm font-medium ${
                          isSelected ? 'text-[#cdd6f4]' : 'text-[#a6adc8]'
                        }`}
                      >
                        {option.title}
                      </span>
                      {isRecommended && !isAnalyzing && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#a6e3a1]/20 text-[#a6e3a1] font-medium">
                          Recommended
                          {recommendConfidence > 0 &&
                            ` (${Math.round(recommendConfidence * 100)}%)`}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-[#585b70] mt-1 leading-relaxed">
                      {option.description}
                    </p>
                  </div>
                  {/* Selection indicator */}
                  <div className="shrink-0 mt-1">
                    <div
                      className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                        isSelected
                          ? 'border-[#89b4fa]'
                          : 'border-[#45475a]'
                      }`}
                    >
                      {isSelected && (
                        <div className="w-2 h-2 rounded-full bg-[#89b4fa]" />
                      )}
                    </div>
                  </div>
                </div>
              </button>
            );
          })}

          {/* Analyzing indicator */}
          {isAnalyzing && (
            <div className="flex items-center gap-2 px-1 py-1">
              <div className="w-3 h-3 border-2 border-[#89b4fa] border-t-transparent rounded-full animate-spin" />
              <span className="text-xs text-[#a6adc8]">
                Analyzing canvas content for recommendation...
              </span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[#313244] flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm text-[#a6adc8] hover:text-[#cdd6f4] hover:bg-[#313244] rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={isCreating}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              isCreating
                ? 'bg-[#45475a] text-[#585b70] cursor-wait'
                : 'bg-[#89b4fa] text-[#1e1e2e] hover:bg-[#74c7ec]'
            }`}
          >
            {isCreating ? 'Creating...' : 'Start Exam'}
          </button>
        </div>
      </div>
    </div>
  );
}
