import { useBackendStatus, type BackendConnectionStatus } from '../hooks/useBackendStatus';

const cfg: Record<BackendConnectionStatus, { label: string; dot: string; text: string }> = {
  connected:    { label: 'Connected',    dot: 'bg-green-500',                  text: 'text-green-700' },
  disconnected: { label: 'Disconnected', dot: 'bg-red-500',                    text: 'text-red-700' },
  checking:     { label: 'Checking...',  dot: 'bg-yellow-500 animate-pulse',   text: 'text-yellow-700' },
};

export function StatusBar() {
  const { status, lastChecked } = useBackendStatus();
  const c = cfg[status];

  return (
    <div className="fixed bottom-0 left-0 right-0 h-7 bg-gray-100 border-t border-gray-200 flex items-center justify-between px-4 text-xs z-50">
      <div className="flex items-center gap-2">
        <span className={`inline-block w-2 h-2 rounded-full ${c.dot}`} />
        <span className={c.text}>Backend: {c.label}</span>
      </div>
      {lastChecked && (
        <span className="text-gray-400">{lastChecked.toLocaleTimeString()}</span>
      )}
    </div>
  );
}
