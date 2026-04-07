/**
 * VerificationModal — Interactive Verification Session modal (EPIC-31 / A4 Runbook)
 *
 * Entry point: User clicks a ReviewItem in the Dashboard → modal opens →
 * modal calls backend to start a verification session → displays first question →
 * user types answer → backend scores via scoring-agent → shows result → next question.
 *
 * Phase 17.1 fail-closed contract:
 *   When backend returns `degraded=true`, display the Chinese `degradedWarning`
 *   prominently in orange so users know their answer is NOT counted toward mastery.
 *
 * Phase 17.2 path traversal contract:
 *   Backend sanitizes `canvas_name` server-side, so the frontend passes
 *   `node.boardName` through without additional validation.
 *
 * State model: MVP — local useState only (no Zustand store). If verification
 * becomes a cross-component concern, refactor into a dedicated `verification-store.ts`.
 *
 * Visual template: ExamModeSelector.tsx (Catppuccin dark theme).
 *
 * Backend wiring:
 *   POST /api/v1/review/session/start            → startVerificationSession
 *   POST /api/v1/review/session/{id}/answer      → submitVerificationAnswer
 */

import { useCallback, useEffect, useState } from 'react';
import type { ReviewNode, SubmitAnswerResponse, VerificationProgress } from '../../types';
import { ApiClient } from '../../services/api-client';

const apiClient = new ApiClient();

interface VerificationModalProps {
  /** The ReviewNode the user clicked in the Dashboard review list. */
  node: ReviewNode;
  /** Dismiss the modal (Cancel button / Escape key / backdrop click). */
  onClose: () => void;
  /** Optional callback when the session reaches terminal `complete` status. */
  onComplete?: (sessionId: string) => void;
}

type ModalStatus =
  | 'loading'      // starting session (first render)
  | 'answering'    // user typing an answer
  | 'scoring'      // waiting for backend to score
  | 'result'       // showing scoring result, waiting for "next" click
  | 'complete'     // session finished — waiting for "close" click
  | 'error';       // backend unreachable (network error / 5xx)

export function VerificationModal({ node, onClose, onComplete }: VerificationModalProps) {
  const [status, setStatus] = useState<ModalStatus>('loading');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<string>('');
  const [currentConcept, setCurrentConcept] = useState<string>(node.name);
  const [totalConcepts, setTotalConcepts] = useState<number>(0);
  const [userAnswer, setUserAnswer] = useState<string>('');
  const [lastResult, setLastResult] = useState<SubmitAnswerResponse | null>(null);
  const [progress, setProgress] = useState<VerificationProgress | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // ─────────────────────────────────────────────────────────────────────────
  // Effect: Start session on mount
  // ─────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setStatus('loading');
      setErrorMessage(null);
      const result = await apiClient.startVerificationSession(node.boardName);
      if (cancelled) return;
      if (!result) {
        setErrorMessage('无法启动验证 session — 请检查后端服务是否运行（http://localhost:8001）。');
        setStatus('error');
        return;
      }
      setSessionId(result.sessionId);
      setCurrentQuestion(result.firstQuestion);
      setCurrentConcept(result.currentConcept || node.name);
      setTotalConcepts(result.totalConcepts);
      setStatus('answering');
    })();
    return () => {
      cancelled = true;
    };
  }, [node.boardName, node.name]);

  // ─────────────────────────────────────────────────────────────────────────
  // Effect: Escape key closes modal
  // ─────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  // ─────────────────────────────────────────────────────────────────────────
  // Action: Submit answer
  // ─────────────────────────────────────────────────────────────────────────
  const handleSubmit = useCallback(async () => {
    if (!sessionId || !userAnswer.trim() || status !== 'answering') return;
    setStatus('scoring');
    const result = await apiClient.submitVerificationAnswer(sessionId, userAnswer);
    if (!result) {
      setErrorMessage('提交答案失败 — 后端可能不可达。');
      setStatus('error');
      return;
    }
    setLastResult(result);
    setProgress(result.progress);
    setStatus('result');
  }, [sessionId, userAnswer, status]);

  // ─────────────────────────────────────────────────────────────────────────
  // Action: Advance to next question (or finish the session)
  // ─────────────────────────────────────────────────────────────────────────
  const handleNext = useCallback(() => {
    if (!lastResult) return;
    if (lastResult.action === 'complete') {
      setStatus('complete');
      if (sessionId) onComplete?.(sessionId);
      return;
    }
    if (lastResult.nextQuestion) {
      setCurrentQuestion(lastResult.nextQuestion);
      setCurrentConcept(lastResult.progress.currentConcept || currentConcept);
      setUserAnswer('');
      setLastResult(null);
      setStatus('answering');
    }
  }, [lastResult, sessionId, onComplete, currentConcept]);

  // ─────────────────────────────────────────────────────────────────────────
  // Render helpers
  // ─────────────────────────────────────────────────────────────────────────
  const renderHeader = () => {
    const completed = progress?.completedConcepts ?? 0;
    const total = progress?.totalConcepts ?? totalConcepts;
    return (
      <div className="px-6 py-4 border-b border-[#313244]">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-[#cdd6f4]">Interactive Verification</h2>
            <p className="text-xs text-[#a6adc8] mt-1">
              {node.boardName} · {currentConcept}
            </p>
          </div>
          {total > 0 && (
            <span className="text-xs text-[#89b4fa] font-mono">
              {completed} / {total}
            </span>
          )}
        </div>
      </div>
    );
  };

  const renderLoading = () => (
    <div className="px-6 py-12 flex flex-col items-center gap-3">
      <div className="w-6 h-6 border-2 border-[#89b4fa] border-t-transparent rounded-full animate-spin" />
      <span className="text-sm text-[#a6adc8]">正在启动验证 session…</span>
    </div>
  );

  const renderError = () => (
    <div className="px-6 py-8 flex flex-col items-center gap-3">
      <div className="text-[#f38ba8] text-sm text-center">{errorMessage}</div>
      <button
        onClick={onClose}
        className="mt-2 px-4 py-2 text-sm bg-[#45475a] text-[#cdd6f4] rounded-lg hover:bg-[#585b70] transition-colors"
      >
        关闭
      </button>
    </div>
  );

  const renderAnswering = () => (
    <div className="px-6 py-4 space-y-3">
      <div>
        <div className="text-xs text-[#a6adc8] mb-2 uppercase tracking-wide">Question</div>
        <div className="text-sm text-[#cdd6f4] leading-relaxed whitespace-pre-wrap">
          {currentQuestion}
        </div>
      </div>
      <textarea
        value={userAnswer}
        onChange={(e) => setUserAnswer(e.target.value)}
        disabled={status !== 'answering'}
        placeholder="Type your answer here..."
        className="w-full min-h-[120px] p-3 bg-[#181825] border border-[#313244] rounded-lg text-sm text-[#cdd6f4] placeholder-[#585b70] focus:outline-none focus:border-[#89b4fa] resize-y"
        autoFocus
      />
    </div>
  );

  const renderScoring = () => (
    <div className="px-6 py-8 flex flex-col items-center gap-3">
      <div className="w-6 h-6 border-2 border-[#f9e2af] border-t-transparent rounded-full animate-spin" />
      <span className="text-sm text-[#a6adc8]">评分中…（scoring-agent）</span>
    </div>
  );

  const renderResult = () => {
    if (!lastResult) return null;
    const { quality, score, degraded, degradedWarning, hint, action } = lastResult;

    // Quality color map
    const qualityColor: Record<typeof quality, string> = {
      excellent: 'text-[#a6e3a1] border-[#a6e3a1]/50 bg-[#a6e3a1]/10',
      good: 'text-[#a6e3a1] border-[#a6e3a1]/50 bg-[#a6e3a1]/10',
      partial: 'text-[#f9e2af] border-[#f9e2af]/50 bg-[#f9e2af]/10',
      wrong: 'text-[#f38ba8] border-[#f38ba8]/50 bg-[#f38ba8]/10',
      unknown: 'text-[#a6adc8] border-[#585b70]/50 bg-[#45475a]/10',
    };

    return (
      <div className="px-6 py-4 space-y-3">
        {/* Phase 17.1: Fail-closed warning banner */}
        {degraded && degradedWarning && (
          <div className="p-3 bg-orange-900/30 border border-orange-500/50 rounded-lg">
            <div className="flex items-start gap-2">
              <svg className="w-4 h-4 text-orange-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span className="text-xs text-orange-200 leading-relaxed">{degradedWarning}</span>
            </div>
          </div>
        )}

        {/* Score + Quality */}
        <div className={`p-3 border rounded-lg ${qualityColor[quality]}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium capitalize">{quality}</span>
            <span className="text-lg font-bold font-mono">{score} / 100</span>
          </div>
        </div>

        {/* Hint (if action === 'hint') */}
        {action === 'hint' && hint && (
          <div className="p-3 bg-[#89b4fa]/10 border border-[#89b4fa]/50 rounded-lg">
            <div className="text-xs text-[#89b4fa] mb-1 uppercase tracking-wide">Hint</div>
            <div className="text-sm text-[#cdd6f4]">{hint}</div>
          </div>
        )}

        {/* User's own answer (read-only review) */}
        <details className="text-xs text-[#a6adc8]">
          <summary className="cursor-pointer hover:text-[#cdd6f4]">Your answer</summary>
          <div className="mt-2 p-2 bg-[#181825] border border-[#313244] rounded whitespace-pre-wrap">
            {userAnswer}
          </div>
        </details>
      </div>
    );
  };

  const renderComplete = () => (
    <div className="px-6 py-8 flex flex-col items-center gap-3">
      <svg className="w-10 h-10 text-[#a6e3a1]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div className="text-sm text-[#cdd6f4]">Session 已完成！</div>
      {progress && (
        <div className="text-xs text-[#a6adc8] mt-1">
          已掌握度: {progress.masteryPercentage.toFixed(0)}%
        </div>
      )}
    </div>
  );

  // ─────────────────────────────────────────────────────────────────────────
  // Footer (action buttons)
  // ─────────────────────────────────────────────────────────────────────────
  const renderFooter = () => (
    <div className="px-6 py-4 border-t border-[#313244] flex justify-end gap-3">
      <button
        onClick={onClose}
        className="px-4 py-2 text-sm text-[#a6adc8] hover:text-[#cdd6f4] hover:bg-[#313244] rounded-lg transition-colors"
      >
        {status === 'complete' ? 'Close' : 'Cancel'}
      </button>
      {status === 'answering' && (
        <button
          onClick={handleSubmit}
          disabled={!userAnswer.trim()}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
            userAnswer.trim()
              ? 'bg-[#89b4fa] text-[#1e1e2e] hover:bg-[#74c7ec]'
              : 'bg-[#45475a] text-[#585b70] cursor-not-allowed'
          }`}
        >
          Submit
        </button>
      )}
      {status === 'result' && lastResult && lastResult.action !== 'complete' && (
        <button
          onClick={handleNext}
          className="px-4 py-2 text-sm font-medium bg-[#89b4fa] text-[#1e1e2e] rounded-lg hover:bg-[#74c7ec] transition-colors"
        >
          {lastResult.action === 'hint' ? 'Try Again' : 'Next'}
        </button>
      )}
      {status === 'result' && lastResult?.action === 'complete' && (
        <button
          onClick={handleNext}
          className="px-4 py-2 text-sm font-medium bg-[#a6e3a1] text-[#1e1e2e] rounded-lg hover:bg-[#94e2d5] transition-colors"
        >
          Finish
        </button>
      )}
    </div>
  );

  // ─────────────────────────────────────────────────────────────────────────
  // Body switcher
  // ─────────────────────────────────────────────────────────────────────────
  const renderBody = () => {
    switch (status) {
      case 'loading':
        return renderLoading();
      case 'error':
        return renderError();
      case 'answering':
        return renderAnswering();
      case 'scoring':
        return renderScoring();
      case 'result':
        return renderResult();
      case 'complete':
        return renderComplete();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-[#1e1e2e] border border-[#45475a] rounded-xl shadow-2xl w-[560px] max-w-[95vw] max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {renderHeader()}
        <div className="flex-1 overflow-y-auto">{renderBody()}</div>
        {status !== 'error' && renderFooter()}
      </div>
    </div>
  );
}
