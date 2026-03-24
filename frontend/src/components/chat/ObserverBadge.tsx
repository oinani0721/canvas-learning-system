/**
 * ObserverBadge — Subtle status indicator for learning event recording.
 * GDR-P0-3: Shows Observer activity (how many learning events recorded + Graphiti write status).
 *
 * Callers:
 * - ChatPanel renders this after streaming completes to show Observer activity
 *
 * Wiring:
 * - observerEventCount and graphitiWriteStatus from chat-store
 */

interface ObserverBadgeProps {
  /** Number of learning events recorded in this conversation turn. */
  eventCount: number;
  /** Whether Graphiti write was successful. */
  graphitiStatus: 'pending' | 'success' | 'failed' | 'idle';
  /** List of tool names that were called (for detailed display). */
  toolNames?: string[];
}

export function ObserverBadge({ eventCount, graphitiStatus, toolNames = [] }: ObserverBadgeProps) {
  // Don't show badge if no events and idle
  if (eventCount === 0 && graphitiStatus === 'idle') {
    return null;
  }

  const statusIcon = {
    pending: '⏳',
    success: '✓',
    failed: '✗',
    idle: '',
  }[graphitiStatus];

  const statusColor = {
    pending: 'text-yellow-400',
    success: 'text-green-400',
    failed: 'text-red-400',
    idle: 'text-[#6c7086]',
  }[graphitiStatus];

  return (
    <div className="flex items-center gap-1.5 px-1 py-0.5" data-observer-badge>
      <span className="text-[10px] text-[#6c7086]">👁</span>
      <span className="text-[10px] text-[#6c7086]">
        Observer: {eventCount > 0 ? `已记录 ${eventCount} 个学习事件` : '监听中'}
        {toolNames.length > 0 && (
          <span className="ml-1 text-[#89b4fa]">
            ({[...new Set(toolNames)].map(n => n.replace(/_/g, ' ')).join(', ')})
          </span>
        )}
        {graphitiStatus !== 'idle' && (
          <span className={`ml-1 ${statusColor}`}>
            · Graphiti {statusIcon}
          </span>
        )}
      </span>
    </div>
  );
}
