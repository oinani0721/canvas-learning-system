/**
 * ExamCard Component (Story 5-4 AC-2, AC-5)
 *
 * Displays a single exam session in the Dashboard's exam tab.
 * Shows: source board, time, status, node count, mastery change summary.
 */

import type { ExamSession } from '../../services/api-client';

interface ExamCardProps {
  session: ExamSession;
  onClick?: (session: ExamSession) => void;
}

export function ExamCard({ session, onClick }: ExamCardProps) {
  const isInProgress = session.status === 'in-progress';
  const statusLabel = isInProgress ? 'In Progress' : 'Completed';
  const statusClass = isInProgress
    ? 'text-blue-600 bg-blue-50'
    : 'text-green-600 bg-green-50';

  return (
    <button
      onClick={() => onClick?.(session)}
      className="w-full text-left p-3 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-sm transition-all"
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-gray-800 truncate">
            {session.sourceBoardName || 'Unknown Board'}
          </div>
          <div className="text-xs text-gray-400 mt-0.5">
            {session.createdAt
              ? new Date(session.createdAt).toLocaleString()
              : ''}
          </div>
        </div>
        <span className={`text-xs px-1.5 py-0.5 rounded shrink-0 ml-2 ${statusClass}`}>
          {statusLabel}
        </span>
      </div>

      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
        <span>Mode: {session.mode}</span>
        <span>{session.nodesExamined} nodes</span>
      </div>

      {session.masteryChangeSummary && (
        <div className="mt-1.5 text-xs text-gray-600">
          {session.masteryChangeSummary}
        </div>
      )}
    </button>
  );
}
