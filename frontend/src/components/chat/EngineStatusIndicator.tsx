/**
 * EngineStatusIndicator — Story 3-9: Engine Status UI
 *
 * Displays the current engine mode in the ChatPanel header:
 * - "Claude Code (订阅)" — normal CLI mode, green dot
 * - "API Key (备用)" — fallback API Key mode, amber dot
 *
 * Clicking toggles between engines (when both are available).
 */

import { useChatStore } from '../../stores/chat-store';
import { ApiKeyEngine } from '../../services/api-key-engine';

export function EngineStatusIndicator() {
  const activeEngine = useChatStore((s) => s.activeEngine);
  const switchEngine = useChatStore((s) => s.switchEngine);

  const isClaudeCode = activeEngine === 'claude-code';
  const hasApiKey = ApiKeyEngine.hasApiKey();

  const canSwitch = isClaudeCode ? hasApiKey : true;

  const handleClick = () => {
    if (!canSwitch) return;
    const nextEngine = isClaudeCode ? 'api-key' : 'claude-code';
    switchEngine(nextEngine);
  };

  return (
    <button
      onClick={handleClick}
      disabled={!canSwitch}
      className={`
        inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium
        transition-colors cursor-pointer
        ${isClaudeCode
          ? 'bg-green-50 text-green-700 hover:bg-green-100'
          : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
        }
        ${!canSwitch ? 'opacity-50 cursor-default' : ''}
      `}
      title={canSwitch
        ? `点击切换到${isClaudeCode ? 'API Key' : 'Claude Code'}模式`
        : '未配置备用 API Key'
      }
    >
      {/* Status dot */}
      <span className={`w-1.5 h-1.5 rounded-full ${isClaudeCode ? 'bg-green-500' : 'bg-amber-500'}`} />

      {/* Label */}
      <span>
        {isClaudeCode ? 'Claude Code (订阅)' : 'API Key (备用)'}
      </span>
    </button>
  );
}
