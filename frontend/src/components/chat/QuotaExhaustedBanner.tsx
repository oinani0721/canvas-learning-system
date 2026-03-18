/**
 * QuotaExhaustedBanner — Story 3-10: Quota Management + Degradation
 *
 * Displays a friendly "subscription quota used up" banner with:
 * - Countdown timer to estimated reset (or "usually resets on Mondays")
 * - "Wait for reset" button (dismisses banner, re-checks on next send)
 * - "Use API Key temporarily" button (opens Settings for API Key config)
 *
 * No technical jargon (no "429", "Rate Limit"). Uses everyday language.
 */

import { useState, useEffect } from 'react';
import { useChatStore } from '../../stores/chat-store';

// ═══════════════════════════════════════════════════════════════════════════════
// Countdown helper
// ═══════════════════════════════════════════════════════════════════════════════

function formatCountdown(targetIso: string | null): string {
  if (!targetIso) {
    return '通常在每周一重置';
  }

  const target = new Date(targetIso).getTime();
  const now = Date.now();
  const diffMs = target - now;

  if (diffMs <= 0) {
    return '即将恢复，请重试';
  }

  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

  if (hours >= 24) {
    const days = Math.floor(hours / 24);
    const remainHours = hours % 24;
    return `预计 ${days} 天 ${remainHours} 小时后重置`;
  }

  if (hours > 0) {
    return `预计 ${hours} 小时 ${minutes} 分钟后重置`;
  }

  return `预计 ${minutes} 分钟后重置`;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Component
// ═══════════════════════════════════════════════════════════════════════════════

interface QuotaExhaustedBannerProps {
  onOpenSettings: () => void;
}

export function QuotaExhaustedBanner({ onOpenSettings }: QuotaExhaustedBannerProps) {
  const quotaStatus = useChatStore((s) => s.quotaStatus);
  const quotaResetTime = useChatStore((s) => s.quotaResetTime);
  const dismissQuotaExhausted = useChatStore((s) => s.dismissQuotaExhausted);

  const [countdown, setCountdown] = useState(formatCountdown(quotaResetTime));
  const [dismissed, setDismissed] = useState(false);

  // Update countdown every minute
  useEffect(() => {
    if (quotaStatus !== 'exhausted') return;

    const timer = setInterval(() => {
      setCountdown(formatCountdown(quotaResetTime));
    }, 60_000);

    // Set initial value
    setCountdown(formatCountdown(quotaResetTime));

    return () => clearInterval(timer);
  }, [quotaStatus, quotaResetTime]);

  // Don't render if not exhausted or dismissed
  if (quotaStatus !== 'exhausted' || dismissed) {
    return null;
  }

  return (
    <div className="mx-3 my-2 p-4 bg-amber-50 border border-amber-200 rounded-lg">
      <div className="flex items-start gap-3">
        {/* Clock icon */}
        <div className="shrink-0 w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center">
          <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>

        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-amber-800">
            本周订阅额度已用完
          </h4>
          <p className="mt-1 text-xs text-amber-600">
            {countdown}
          </p>
          <p className="mt-1 text-xs text-amber-500">
            白板编辑、学习提醒等功能仍可正常使用，仅 AI 对话暂停。
          </p>

          <div className="mt-3 flex gap-2">
            <button
              onClick={() => {
                setDismissed(true);
                dismissQuotaExhausted();
              }}
              className="px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-100 hover:bg-amber-200 rounded transition-colors"
            >
              等待重置
            </button>
            <button
              onClick={onOpenSettings}
              className="px-3 py-1.5 text-xs font-medium text-white bg-amber-600 hover:bg-amber-700 rounded transition-colors"
            >
              临时使用 API Key
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
