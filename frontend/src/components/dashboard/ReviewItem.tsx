/**
 * ReviewItem Component (Story 5-4 AC-3)
 *
 * Displays a single node that needs review in the Dashboard.
 * Shows: name, topic, mastery level (color), urgency label.
 */

import type { ReviewNode } from '../../types';
import { formatRelativeDate } from '../../services/mastery-utils';

interface ReviewItemProps {
  node: ReviewNode;
  onClick?: (node: ReviewNode) => void;
}

function getFreshnessLabel(node: ReviewNode): { text: string; className: string } {
  if (node.freshness === 'overdue') {
    return {
      text: node.overdueDays ? `Overdue ${node.overdueDays}d` : 'Overdue',
      className: 'text-red-600 bg-red-50',
    };
  }
  if (node.freshness === 'due') {
    return {
      text: 'Review today',
      className: 'text-yellow-600 bg-yellow-50',
    };
  }
  return {
    text: 'Needs practice',
    className: 'text-orange-600 bg-orange-50',
  };
}

function getBorderColor(node: ReviewNode): string {
  if (node.freshness === 'overdue') return 'border-l-red-400';
  if (node.freshness === 'due') return 'border-l-yellow-400';
  return 'border-l-orange-400';
}

export function ReviewItem({ node, onClick }: ReviewItemProps) {
  const freshnessInfo = getFreshnessLabel(node);
  const borderColor = getBorderColor(node);

  return (
    <button
      onClick={() => onClick?.(node)}
      className={`w-full text-left px-3 py-2 border-l-4 ${borderColor} hover:bg-gray-50 transition-colors`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <div
            className="w-2 h-2 rounded-full shrink-0"
            style={{ backgroundColor: node.masteryColor }}
          />
          <span className="text-sm text-gray-800 truncate">{node.name}</span>
        </div>
        <span
          className={`text-xs px-1.5 py-0.5 rounded shrink-0 ml-2 ${freshnessInfo.className}`}
        >
          {freshnessInfo.text}
        </span>
      </div>
      <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
        {node.boardName && <span>{node.boardName}</span>}
        {node.lastReviewedAt && (
          <span>Last: {formatRelativeDate(node.lastReviewedAt)}</span>
        )}
      </div>
    </button>
  );
}
