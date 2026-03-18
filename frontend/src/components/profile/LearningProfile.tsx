/**
 * LearningProfile Panel (Story 5-3)
 *
 * Displays a node's learning profile in the sidebar:
 * - L1: Mastery indicator + prescriptive message + learning stats
 * - L2: Tips list (expandable)
 * - L2: Weakness directions (positive framing)
 * - L3: Key QA highlights (collapsed by default)
 * - FSRS next review date
 * - Start exam button
 */

import { useState, useEffect, useCallback } from 'react';
import {
  getMasteryColor,
  getMasteryLabel,
  masteryLevelToStatus,
  formatRelativeDate,
} from '../../services/mastery-utils';
import type {
  ProfileSummary,
  TipItem,
  WeaknessItem,
  QAHighlightCluster,
} from '../../services/api-client';

interface LearningProfileProps {
  nodeId: string;
  nodeTitle: string;
  backendUrl?: string;
  onStartExam?: (nodeId: string) => void;
  onSwitchToChat?: () => void;
}

type LoadState = 'loading' | 'loaded' | 'error';

// Re-implement a minimal fetch helper to avoid circular dependency with api-client singleton
async function fetchJson<T>(baseUrl: string, path: string): Promise<T | null> {
  try {
    const res = await fetch(`${baseUrl}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export function LearningProfile({
  nodeId,
  nodeTitle: _nodeTitle,
  backendUrl = 'http://localhost:8001',
  onStartExam,
  onSwitchToChat,
}: LearningProfileProps) {
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [summary, setSummary] = useState<ProfileSummary | null>(null);
  const [tips, setTips] = useState<TipItem[]>([]);
  const [weaknesses, setWeaknesses] = useState<WeaknessItem[]>([]);
  const [qaClusters, setQaClusters] = useState<QAHighlightCluster[]>([]);

  // Expanded state for collapsible sections
  const [expandedTip, setExpandedTip] = useState<string | null>(null);
  const [expandedWeakness, setExpandedWeakness] = useState<string | null>(null);
  const [expandedCluster, setExpandedCluster] = useState<string | null>(null);

  const loadProfile = useCallback(async () => {
    setLoadState('loading');
    const encodedId = encodeURIComponent(nodeId);
    const base = `/api/v1`;

    const [summaryData, tipsData, weaknessData, qaData] = await Promise.all([
      fetchJson<ProfileSummary>(backendUrl, `${base}/profile/${encodedId}/summary`),
      fetchJson<{ tips: TipItem[]; total: number }>(backendUrl, `${base}/profile/${encodedId}/tips`),
      fetchJson<{ weaknesses: WeaknessItem[]; total: number }>(backendUrl, `${base}/profile/${encodedId}/weaknesses`),
      fetchJson<{ clusters: QAHighlightCluster[]; total: number }>(backendUrl, `${base}/profile/${encodedId}/qa-highlights`),
    ]);

    if (summaryData) {
      setSummary(summaryData);
      setTips(tipsData?.tips ?? []);
      setWeaknesses(weaknessData?.weaknesses ?? []);
      setQaClusters(qaData?.clusters ?? []);
      setLoadState('loaded');
    } else {
      // Backend unreachable - show degraded state
      setSummary(null);
      setTips([]);
      setWeaknesses([]);
      setQaClusters([]);
      setLoadState('error');
    }
  }, [nodeId, backendUrl]);

  useEffect(() => {
    loadProfile();
    // Reset expanded states when node changes
    setExpandedTip(null);
    setExpandedWeakness(null);
    setExpandedCluster(null);
  }, [loadProfile]);

  if (loadState === 'loading') {
    return (
      <div className="p-4 space-y-3 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4" />
        <div className="h-3 bg-gray-200 rounded w-1/2" />
        <div className="h-20 bg-gray-200 rounded" />
        <div className="h-3 bg-gray-200 rounded w-2/3" />
      </div>
    );
  }

  if (loadState === 'error') {
    return (
      <div className="p-4">
        <div className="text-sm text-gray-500 mb-2">
          Backend service unavailable
        </div>
        <button
          onClick={loadProfile}
          className="text-xs text-blue-500 hover:text-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const masteryStatus = summary
    ? masteryLevelToStatus(summary.masteryLevel)
    : 'unlearned';
  const masteryColor = getMasteryColor(masteryStatus);
  const masteryLabel = summary?.masteryLabel ?? getMasteryLabel(masteryStatus);

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* L1: Mastery Indicator + Summary */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center gap-3 mb-2">
          {/* Color bar indicator */}
          <div
            className="w-1 h-10 rounded-full shrink-0"
            style={{ backgroundColor: masteryColor }}
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span
                className="text-xs font-medium px-2 py-0.5 rounded-full"
                style={{
                  backgroundColor: `${masteryColor}20`,
                  color: masteryColor,
                }}
              >
                {masteryLabel}
              </span>
              {summary?.freshness && summary.freshness !== 'fresh' && (
                <span className="text-xs text-yellow-600 bg-yellow-50 px-1.5 py-0.5 rounded">
                  {summary.freshness === 'overdue'
                    ? 'Overdue'
                    : summary.freshness === 'due'
                      ? 'Due'
                      : ''}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-600 mt-1">
              {summary?.prescriptiveMessage ?? ''}
            </p>
          </div>
        </div>

        {/* Stats row */}
        <div className="flex gap-4 text-xs text-gray-400 mt-2">
          <span>Interactions: {summary?.interactionCount ?? 0}</span>
          <span>Exams: {summary?.examCount ?? 0}</span>
          {summary?.lastExamDate && (
            <span>Last exam: {formatRelativeDate(summary.lastExamDate)}</span>
          )}
        </div>
      </div>

      {/* L2: Tips Section */}
      <div className="border-b border-gray-100">
        <div className="px-4 py-3">
          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Tips ({tips.length})
          </h4>
        </div>
        {tips.length === 0 ? (
          <div className="px-4 pb-3 text-xs text-gray-400">
            No tips yet - select text in a conversation to mark as a tip
          </div>
        ) : (
          <div className="pb-2">
            {tips.map((tip) => (
              <div key={tip.tipId} className="px-4 py-1.5">
                <button
                  onClick={() =>
                    setExpandedTip(expandedTip === tip.tipId ? null : tip.tipId)
                  }
                  className="w-full text-left"
                >
                  <div className="text-xs text-gray-700 line-clamp-2">
                    {tip.content}
                  </div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    {tip.category && (
                      <span className="bg-gray-100 px-1 rounded mr-1">
                        {tip.category}
                      </span>
                    )}
                    {tip.annotatedAt && formatRelativeDate(tip.annotatedAt)}
                  </div>
                </button>
                {expandedTip === tip.tipId && tip.contextMessages.length > 0 && (
                  <div className="mt-1.5 pl-2 border-l-2 border-gray-200 space-y-1">
                    {tip.contextMessages.map((msg, i) => (
                      <div key={i} className="text-xs text-gray-500">
                        {msg}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* L2: Weaknesses Section (positive framing) */}
      <div className="border-b border-gray-100">
        <div className="px-4 py-3">
          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Areas to Strengthen ({weaknesses.length})
          </h4>
        </div>
        {weaknesses.length === 0 ? (
          <div className="px-4 pb-3 text-xs text-gray-400">
            Great progress! No weak areas identified yet
          </div>
        ) : (
          <div className="pb-2">
            {weaknesses.map((w, idx) => (
              <div key={idx} className="px-4 py-1.5">
                <button
                  onClick={() =>
                    setExpandedWeakness(
                      expandedWeakness === w.direction ? null : w.direction,
                    )
                  }
                  className="w-full text-left"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-700">{w.direction}</span>
                    <span className="text-xs text-gray-400 ml-2 shrink-0">
                      {w.frequency}x
                    </span>
                  </div>
                  {w.lastSeen && (
                    <div className="text-xs text-gray-400 mt-0.5">
                      Last seen: {formatRelativeDate(w.lastSeen)}
                    </div>
                  )}
                </button>
                {expandedWeakness === w.direction &&
                  w.relatedExamSummaries.length > 0 && (
                    <div className="mt-1.5 pl-2 border-l-2 border-orange-200 space-y-1">
                      {w.relatedExamSummaries.map((s, i) => (
                        <div key={i} className="text-xs text-gray-500">
                          {s}
                        </div>
                      ))}
                    </div>
                  )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* L3: QA Highlights (collapsed by default) */}
      <div className="border-b border-gray-100">
        <div className="px-4 py-3">
          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Key Q&A
          </h4>
        </div>
        {qaClusters.length === 0 ? (
          <div className="px-4 pb-3 text-xs text-gray-400">
            Have a conversation with AI - great Q&A will appear here
          </div>
        ) : (
          <div className="pb-2">
            {qaClusters.map((cluster) => (
              <div key={cluster.topic} className="px-4 py-1">
                <button
                  onClick={() =>
                    setExpandedCluster(
                      expandedCluster === cluster.topic
                        ? null
                        : cluster.topic,
                    )
                  }
                  className="w-full text-left flex items-center justify-between"
                >
                  <span className="text-xs font-medium text-gray-600">
                    {cluster.topic}
                  </span>
                  <span className="text-xs text-gray-400">
                    {cluster.qaPairs.length} pairs
                  </span>
                </button>
                {expandedCluster === cluster.topic && (
                  <div className="mt-1.5 space-y-2">
                    {cluster.qaPairs.map((qa, i) => (
                      <div
                        key={i}
                        className="pl-2 border-l-2 border-blue-200"
                      >
                        <div className="text-xs text-gray-700 font-medium">
                          Q: {qa.question}
                        </div>
                        {qa.answer && (
                          <div className="text-xs text-gray-500 mt-0.5">
                            A: {qa.answer}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* FSRS Next Review + Start Exam */}
      <div className="p-4 mt-auto">
        {summary?.fsrsDueDate && (
          <div className="text-xs text-gray-500 mb-3">
            <span className="font-medium">Next review: </span>
            <span
              className={
                new Date(summary.fsrsDueDate) <= new Date()
                  ? 'text-yellow-600 font-medium'
                  : ''
              }
            >
              {formatRelativeDate(summary.fsrsDueDate)}
            </span>
          </div>
        )}
        {!summary?.fsrsDueDate && summary?.interactionCount === 0 && (
          <div className="text-xs text-gray-400 mb-3">
            Complete first exam to schedule reviews
          </div>
        )}

        <div className="flex gap-2">
          {onSwitchToChat && (
            <button
              onClick={onSwitchToChat}
              className="flex-1 px-3 py-2 text-xs text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Chat
            </button>
          )}
          <button
            onClick={() => onStartExam?.(nodeId)}
            disabled={!summary || summary.interactionCount === undefined}
            className="flex-1 px-3 py-2 text-xs text-white bg-purple-500 rounded-lg hover:bg-purple-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title={
              !summary
                ? 'Backend service not available'
                : 'Start exam for this node'
            }
          >
            Start Exam
          </button>
        </div>
      </div>
    </div>
  );
}
