import { useState } from 'react';
import type { Recommendation } from '../services/api-client';

interface RecommendationBarProps {
  recommendations: Recommendation[];
  loading: boolean;
  onAccept: (rec: Recommendation) => void;
  onDismiss: (rec: Recommendation) => void;
}

export function RecommendationBar({
  recommendations,
  loading,
  onAccept,
  onDismiss,
}: RecommendationBarProps) {
  const [collapsed, setCollapsed] = useState(false);

  // Hide completely when nothing to show and not loading
  if (recommendations.length === 0 && !loading) return null;

  return (
    <div className="absolute bottom-4 left-4 right-4 z-30 bg-white rounded-lg border border-gray-200 shadow-lg">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-2.5 cursor-pointer select-none"
        onClick={() => setCollapsed((c) => !c)}
      >
        <div className="flex items-center gap-2">
          <span className="text-sm text-yellow-600">&#128161;</span>
          <span className="text-sm font-medium text-gray-700">
            {loading
              ? '正在分析概念关联...'
              : `发现 ${recommendations.length} 组概念可能有关联`}
          </span>
        </div>
        <button
          className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1"
          onClick={(e) => {
            e.stopPropagation();
            setCollapsed((c) => !c);
          }}
        >
          {collapsed ? '展开' : '折叠'}
        </button>
      </div>

      {/* Body */}
      {!collapsed && (
        <div className="px-4 pb-3 space-y-2 max-h-48 overflow-y-auto">
          {loading && recommendations.length === 0 && (
            <div className="flex items-center gap-2 py-2">
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
              <span className="text-sm text-gray-500">分析中...</span>
            </div>
          )}

          {recommendations.map((rec) => (
            <div
              key={rec.id}
              className="flex items-center justify-between p-2.5 bg-gray-50 rounded-lg"
            >
              <div className="flex-1 min-w-0 mr-3">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium text-gray-800 truncate">{rec.sourceNodeTitle}</span>
                  <span className="text-gray-400 shrink-0">&harr;</span>
                  <span className="font-medium text-gray-800 truncate">{rec.targetNodeTitle}</span>
                  <span className="text-xs text-blue-500 font-medium shrink-0">
                    {Math.round(rec.confidence * 100)}%
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-0.5 truncate">{rec.reason}</p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => onAccept(rec)}
                  className="px-3 py-1 text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded hover:bg-green-100 transition-colors"
                >
                  接受连线
                </button>
                <button
                  onClick={() => onDismiss(rec)}
                  className="px-3 py-1 text-xs font-medium text-gray-500 bg-gray-100 border border-gray-200 rounded hover:bg-gray-200 transition-colors"
                >
                  忽略
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
