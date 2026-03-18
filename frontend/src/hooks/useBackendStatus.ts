import { useState, useEffect, useCallback } from 'react';

export type BackendConnectionStatus = 'connected' | 'disconnected' | 'checking';

export interface BackendStatus {
  status: BackendConnectionStatus;
  lastChecked: Date | null;
  checkNow: () => void;
}

const POLL_INTERVAL_MS = 30_000;
const DEFAULT_BACKEND_URL = 'http://localhost:8001';

export function useBackendStatus(): BackendStatus {
  const [status, setStatus] = useState<BackendConnectionStatus>('checking');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const performCheck = useCallback(async () => {
    setStatus('checking');
    try {
      const backendUrl = localStorage.getItem('canvas-learning-settings')
        ? JSON.parse(localStorage.getItem('canvas-learning-settings')!).backendUrl || DEFAULT_BACKEND_URL
        : DEFAULT_BACKEND_URL;
      const res = await fetch(`${backendUrl}/api/v1/system/health`, { signal: AbortSignal.timeout(5000) });
      setStatus(res.ok ? 'connected' : 'disconnected');
    } catch {
      setStatus('disconnected');
    }
    setLastChecked(new Date());
  }, []);

  useEffect(() => {
    performCheck();
    const id = setInterval(performCheck, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [performCheck]);

  return { status, lastChecked, checkNow: performCheck };
}
