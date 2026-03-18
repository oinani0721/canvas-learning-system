/**
 * RecoveryBanner — Story 3-11: Crash Recovery UI feedback
 *
 * Three states:
 * - recovering: "AI 连接中断，正在恢复..." (with spinner)
 * - failed: "AI 暂时不可用" + manual "Retry" button
 * - circuit_open: "AI 多次异常" + "Check updates" link + manual retry (disabled)
 *
 * Banner appears at the top of the ChatPanel message list.
 * Auto-disappears when recovery succeeds (status returns to 'idle').
 */

import { useChatStore } from '../../stores/chat-store';

// ═══════════════════════════════════════════════════════════════════════════════
// Component
// ═══════════════════════════════════════════════════════════════════════════════

interface RecoveryBannerProps {
  nodeTitle: string;
}

export function RecoveryBanner({ nodeTitle }: RecoveryBannerProps) {
  const recoveryStatus = useChatStore((s) => s.recoveryStatus);
  const manualRetry = useChatStore((s) => s.manualRetry);

  // Don't render when idle
  if (recoveryStatus === 'idle') {
    return null;
  }

  return (
    <div className="mx-3 my-2 rounded-lg border overflow-hidden">
      {/* Recovering: auto-restart in progress */}
      {recoveryStatus === 'recovering' && (
        <div className="p-3 bg-blue-50 border-blue-200">
          <div className="flex items-center gap-2">
            {/* Spinner */}
            <svg className="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span className="text-sm text-blue-700">
              AI 连接中断，正在恢复...
            </span>
          </div>
        </div>
      )}

      {/* Failed: single retry exhausted */}
      {recoveryStatus === 'failed' && (
        <div className="p-3 bg-orange-50 border-orange-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span className="text-sm text-orange-700">
                AI 暂时不可用，请稍后重试
              </span>
            </div>
            <button
              onClick={() => manualRetry(nodeTitle)}
              className="px-3 py-1 text-xs font-medium text-orange-700 bg-orange-100 hover:bg-orange-200 rounded transition-colors"
            >
              重试
            </button>
          </div>
        </div>
      )}

      {/* Circuit open: multiple crashes, stopped retrying */}
      {recoveryStatus === 'circuit_open' && (
        <div className="p-3 bg-red-50 border-red-200">
          <div className="flex items-start gap-2">
            <svg className="h-4 w-4 text-red-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-red-700">
                AI 多次异常，已暂停自动重试
              </p>
              <p className="mt-1 text-xs text-red-500">
                可能需要更新 Claude Code 或重启应用。5 分钟后将自动恢复重试。
              </p>
              <div className="mt-2 flex gap-2">
                <a
                  href="https://docs.anthropic.com/en/docs/claude-code"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1 text-xs font-medium text-red-700 bg-red-100 hover:bg-red-200 rounded transition-colors"
                >
                  检查更新
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
