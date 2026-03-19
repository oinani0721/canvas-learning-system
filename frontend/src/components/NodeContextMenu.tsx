/**
 * NodeContextMenu — Right-click context menu for canvas nodes.
 * Scene 1.11: Context menu with Edit / Delete / Start Chat / View Profile actions.
 *
 * Features:
 *   - Absolute-positioned floating menu at cursor location
 *   - Click-outside dismissal
 *   - Escape key dismissal
 *   - Catppuccin Mocha dark theme via Tailwind
 *
 * Callers:
 *   - App.tsx — rendered conditionally when contextMenuState is set
 *   - Triggered via ReactFlow onNodeContextMenu
 *
 * Wiring:
 *   - onEdit: selects the node + enters edit mode (currently = select node)
 *   - onDelete: deletes the node from Dexie + ReactFlow state
 *   - onStartChat: selects the node (opens chat sidebar)
 *   - onViewProfile: selects the node + switches sidebar to profile tab
 */

import { useEffect, useRef, useCallback } from 'react';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

export interface ContextMenuState {
  nodeId: string;
  nodeTitle: string;
  x: number;
  y: number;
}

interface NodeContextMenuProps {
  state: ContextMenuState;
  onClose: () => void;
  onEdit: (nodeId: string) => void;
  onDelete: (nodeId: string) => void;
  onStartChat: (nodeId: string) => void;
  onViewProfile: (nodeId: string) => void;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Menu Items
// ═══════════════════════════════════════════════════════════════════════════════

interface MenuItem {
  label: string;
  icon: string;
  action: 'edit' | 'startChat' | 'viewProfile' | 'delete';
  danger?: boolean;
}

const MENU_ITEMS: MenuItem[] = [
  { label: 'Edit', icon: '\u270F', action: 'edit' },
  { label: 'Start Chat', icon: '\uD83D\uDCAC', action: 'startChat' },
  { label: 'View Profile', icon: '\uD83D\uDCCA', action: 'viewProfile' },
  { label: 'Delete', icon: '\uD83D\uDDD1', action: 'delete', danger: true },
];

// ═══════════════════════════════════════════════════════════════════════════════
// Component
// ═══════════════════════════════════════════════════════════════════════════════

export function NodeContextMenu({
  state,
  onClose,
  onEdit,
  onDelete,
  onStartChat,
  onViewProfile,
}: NodeContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  // Click-outside dismissal
  const handleClickOutside = useCallback(
    (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as HTMLElement)) {
        onClose();
      }
    },
    [onClose],
  );

  // Escape key dismissal
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    },
    [onClose],
  );

  useEffect(() => {
    // Use setTimeout to avoid the context menu event itself triggering close
    const timer = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
    }, 0);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      clearTimeout(timer);
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleClickOutside, handleKeyDown]);

  // Clamp position so menu doesn't overflow viewport
  const menuWidth = 180;
  const menuHeight = MENU_ITEMS.length * 36 + 40; // approximate
  const x = Math.min(state.x, window.innerWidth - menuWidth - 8);
  const y = Math.min(state.y, window.innerHeight - menuHeight - 8);

  const handleAction = (item: MenuItem) => {
    switch (item.action) {
      case 'edit':
        onEdit(state.nodeId);
        break;
      case 'startChat':
        onStartChat(state.nodeId);
        break;
      case 'viewProfile':
        onViewProfile(state.nodeId);
        break;
      case 'delete':
        onDelete(state.nodeId);
        break;
    }
    onClose();
  };

  return (
    <div
      ref={menuRef}
      className="fixed z-50 min-w-[180px] rounded-lg shadow-lg border overflow-hidden"
      style={{
        left: x,
        top: y,
        backgroundColor: '#1e1e2e', // Catppuccin Mocha base
        borderColor: '#313244', // Catppuccin Mocha surface0
      }}
      data-testid="node-context-menu"
    >
      {/* Header: node title */}
      <div
        className="px-3 py-2 text-xs font-medium truncate border-b"
        style={{
          color: '#a6adc8', // Catppuccin Mocha subtext0
          borderColor: '#313244',
        }}
      >
        {state.nodeTitle}
      </div>

      {/* Menu items */}
      <div className="py-1">
        {MENU_ITEMS.map((item) => (
          <button
            key={item.action}
            onClick={() => handleAction(item)}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left transition-colors"
            style={{
              color: item.danger ? '#f38ba8' : '#cdd6f4', // Catppuccin red / text
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.backgroundColor = '#313244';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
            }}
          >
            <span className="text-sm w-5 text-center">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
