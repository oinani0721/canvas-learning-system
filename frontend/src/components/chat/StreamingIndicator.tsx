/**
 * StreamingIndicator — Visual feedback during AI response streaming.
 * Story 3-3 AC-2 / AC-6
 *
 * Displays:
 * - Bouncing dots + "Claude is thinking..." when waitingForFirstToken AND > 2s
 * - Bouncing dots + "Claude is responding..." once streaming has begun
 *
 * Callers:
 * - ChatPanel renders this below the message list when isStreaming is true
 *
 * Wiring:
 * - Reads isStreaming and waitingForFirstToken from useChatStore
 */

import { useState, useEffect } from 'react';

interface StreamingIndicatorProps {
  /** Whether we are still waiting for the first token. */
  waitingForFirstToken: boolean;
}

/** Timeout (ms) before changing text to "Thinking..." (AC-6: first token < 2s). */
const THINKING_DELAY_MS = 2000;

export function StreamingIndicator({ waitingForFirstToken }: StreamingIndicatorProps) {
  const [showThinking, setShowThinking] = useState(false);

  // Start a timer when waitingForFirstToken is true; after 2s show "thinking" text
  useEffect(() => {
    if (!waitingForFirstToken) {
      setShowThinking(false);
      return;
    }

    const timer = setTimeout(() => {
      setShowThinking(true);
    }, THINKING_DELAY_MS);

    return () => clearTimeout(timer);
  }, [waitingForFirstToken]);

  const label = waitingForFirstToken && showThinking
    ? 'Claude is thinking...'
    : 'Claude is responding...';

  return (
    <div className="flex items-center gap-2 text-xs text-gray-400 pl-1 py-1">
      <span className="inline-flex gap-0.5">
        <span
          className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce"
          style={{ animationDelay: '0ms' }}
        />
        <span
          className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce"
          style={{ animationDelay: '150ms' }}
        />
        <span
          className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce"
          style={{ animationDelay: '300ms' }}
        />
      </span>
      <span>{label}</span>
    </div>
  );
}
