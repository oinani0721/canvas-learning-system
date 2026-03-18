import { useState, useCallback, useEffect } from 'react';
import type { TipItem } from '../../types';

interface TipsListProps {
  /** The node ID whose tips are displayed. */
  nodeId: string;
}

/**
 * Displays all Tips saved for a given node.
 *
 * Tips are read from localStorage under the key `tips:<nodeId>`.
 * Each tip shows its text content and the timestamp it was annotated.
 * Individual tips can be deleted.
 *
 * The component re-reads localStorage whenever `nodeId` changes and
 * also listens for cross-tab `storage` events so it stays in sync if
 * the same node's tips are modified in another window/tab.
 */
export function TipsList({ nodeId }: TipsListProps) {
  const [tips, setTips] = useState<TipItem[]>([]);

  const storageKey = `tips:${nodeId}`;

  // ── Read tips from localStorage ──────────────────────────────────────

  const loadTips = useCallback(() => {
    const raw = localStorage.getItem(storageKey);
    setTips(raw ? (JSON.parse(raw) as TipItem[]) : []);
  }, [storageKey]);

  // Reload when the nodeId changes.
  useEffect(() => {
    loadTips();
  }, [loadTips]);

  // Stay in sync if another tab modifies the same key.
  useEffect(() => {
    function onStorage(e: StorageEvent) {
      if (e.key === storageKey) loadTips();
    }
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, [storageKey, loadTips]);

  // ── Delete a single tip ──────────────────────────────────────────────

  const handleDelete = useCallback(
    (tipId: string) => {
      const updated = tips.filter((t) => t.tipId !== tipId);
      localStorage.setItem(storageKey, JSON.stringify(updated));
      setTips(updated);
    },
    [tips, storageKey],
  );

  // ── Format timestamp for display ────────────────────────────────────

  function formatTime(iso: string): string {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.floor(diffMs / 60000);

    if (diffMin < 1) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;

    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;

    // Fall back to locale date for older tips.
    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  // ── Render ───────────────────────────────────────────────────────────

  if (tips.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-gray-200 px-4 py-6 text-center">
        <p className="text-sm text-gray-400">No tips yet</p>
        <p className="mt-1 text-xs text-gray-300">
          Select text in a chat message and click "Add Tip"
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
        Tips ({tips.length})
      </h4>

      <ul className="space-y-2">
        {tips.map((tip) => (
          <li
            key={tip.tipId}
            className="group rounded-lg border border-gray-100 bg-amber-50 px-3 py-2"
          >
            <div className="flex items-start justify-between gap-2">
              <p className="flex-1 text-sm leading-relaxed text-gray-800">
                {tip.content}
              </p>
              <button
                type="button"
                onClick={() => handleDelete(tip.tipId)}
                aria-label={`Delete tip: ${tip.content.slice(0, 30)}`}
                className="mt-0.5 shrink-0 rounded p-0.5 text-gray-300 opacity-0 transition-opacity hover:text-red-500 focus:opacity-100 group-hover:opacity-100"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="h-4 w-4"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.52.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
            <span className="mt-1 block text-xs text-gray-400">
              {formatTime(tip.annotatedAt)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
