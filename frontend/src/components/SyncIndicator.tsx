/**
 * SyncIndicator — Shows sync state: idle (green), syncing (yellow), offline (red)
 * Story 1-5 AC-6: Sync state visualization
 */
import { useState, useEffect } from 'react';
import type { SyncEngine, SyncState } from '../services/sync-engine';

const STATE_CONFIG: Record<SyncState, { color: string; label: string; animate: boolean }> = {
  idle: { color: 'bg-green-400', label: 'Synced', animate: false },
  syncing: { color: 'bg-yellow-400', label: 'Syncing', animate: true },
  offline: { color: 'bg-red-400', label: 'Offline', animate: false },
};

export function SyncIndicator({ engine }: { engine: SyncEngine | null }) {
  const [syncState, setSyncState] = useState<SyncState>('idle');
  const [pendingCount, setPendingCount] = useState(0);

  useEffect(() => {
    if (!engine) return;
    const unsubscribe = engine.subscribe((state, count) => {
      setSyncState(state);
      setPendingCount(count);
    });
    return unsubscribe;
  }, [engine]);

  const config = STATE_CONFIG[syncState];

  return (
    <div className="flex items-center gap-1.5 text-xs text-gray-500">
      <span
        className={`inline-block w-2 h-2 rounded-full ${config.color} ${
          config.animate ? 'animate-pulse' : ''
        }`}
      />
      <span>{config.label}</span>
      {pendingCount > 0 && (
        <span className="text-gray-400">({pendingCount})</span>
      )}
    </div>
  );
}
