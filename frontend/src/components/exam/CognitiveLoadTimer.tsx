/**
 * CognitiveLoadTimer - Tracks exam duration with cognitive load thresholds.
 *
 * Displays elapsed time (mm:ss) and changes color at thresholds:
 * - 0-15 min: green (normal)
 * - 15-25 min: yellow (mild fatigue)
 * - 25-35 min: orange (moderate fatigue)
 * - 35-45 min: red (high fatigue)
 * - 45+ min: deep red (recommend break)
 *
 * Shows a break suggestion dialog at the 45-minute threshold.
 *
 * Callers:
 * - ExamCanvas.tsx (top toolbar)
 *
 * Wiring:
 * - useExamStore.startTime for elapsed calculation
 */

import { useState, useEffect, useCallback, useRef } from 'react';

interface CognitiveLoadTimerProps {
  /** ISO-8601 start time of the exam session. */
  startTime: string;
}

/** Format seconds into mm:ss. */
function formatTime(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

/** Get the color class based on elapsed minutes. */
function getTimerColor(minutes: number): string {
  if (minutes < 15) return 'text-green-400';
  if (minutes < 25) return 'text-yellow-400';
  if (minutes < 35) return 'text-orange-400';
  if (minutes < 45) return 'text-red-400';
  return 'text-red-600';
}

/** Get the background color class for the container. */
function getTimerBg(minutes: number): string {
  if (minutes < 15) return 'bg-green-900/20';
  if (minutes < 25) return 'bg-yellow-900/20';
  if (minutes < 35) return 'bg-orange-900/20';
  if (minutes < 45) return 'bg-red-900/20';
  return 'bg-red-900/30';
}

export function CognitiveLoadTimer({ startTime }: CognitiveLoadTimerProps) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [showBreakSuggestion, setShowBreakSuggestion] = useState(false);
  const breakShownRef = useRef(false);

  useEffect(() => {
    const startMs = new Date(startTime).getTime();

    const tick = () => {
      const now = Date.now();
      const diff = Math.floor((now - startMs) / 1000);
      setElapsedSeconds(Math.max(0, diff));
    };

    tick(); // immediate
    const interval = window.setInterval(tick, 1000);
    return () => window.clearInterval(interval);
  }, [startTime]);

  // Show break suggestion at 45 minutes (once)
  useEffect(() => {
    const minutes = Math.floor(elapsedSeconds / 60);
    if (minutes >= 45 && !breakShownRef.current) {
      breakShownRef.current = true;
      setShowBreakSuggestion(true);
    }
  }, [elapsedSeconds]);

  const dismissBreak = useCallback(() => {
    setShowBreakSuggestion(false);
  }, []);

  const minutes = Math.floor(elapsedSeconds / 60);
  const colorClass = getTimerColor(minutes);
  const bgClass = getTimerBg(minutes);

  return (
    <>
      <div
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md ${bgClass}`}
        title={`Elapsed: ${formatTime(elapsedSeconds)}`}
      >
        <svg
          className={`w-3.5 h-3.5 ${colorClass}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
        <span className={`text-xs font-mono font-medium ${colorClass}`}>
          {formatTime(elapsedSeconds)}
        </span>
      </div>

      {/* Break suggestion dialog */}
      {showBreakSuggestion && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#1e1e2e] border border-[#45475a] rounded-lg shadow-xl p-6 w-80">
            <div className="flex items-center gap-2 mb-3">
              <svg
                className="w-5 h-5 text-yellow-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-sm font-medium text-[#cdd6f4]">
                Take a Break
              </h3>
            </div>
            <p className="text-xs text-[#a6adc8] mb-4">
              You have been studying for {minutes} minutes. Research shows that
              taking a 5-minute break helps maintain focus and improves retention.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={dismissBreak}
                className="px-3 py-1.5 text-xs text-[#a6adc8] hover:text-[#cdd6f4] hover:bg-[#313244] rounded-md transition-colors"
              >
                Continue Studying
              </button>
              <button
                onClick={dismissBreak}
                className="px-3 py-1.5 text-xs bg-[#89b4fa] text-[#1e1e2e] rounded-md hover:bg-[#74c7ec] transition-colors font-medium"
              >
                OK, I will rest
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
