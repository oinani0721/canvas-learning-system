/**
 * NodeContextMenu — Right-click context menu for canvas nodes.
 * Scene 1.11: Context menu with 7 actions matching Pencil design frame srZRf.
 *
 * Features:
 *   - 7 menu items: 打开对话 / 学习档案 / 重命名(F2) / 设置颜色(>) / 开始考察 / 查看关联 / 删除节点(Del)
 *   - SVG inline icons (Catppuccin Mocha theme)
 *   - Color submenu with 7 color circles on hover
 *   - Keyboard shortcut hints (F2, Del) right-aligned
 *   - Absolute-positioned floating menu at cursor location
 *   - Click-outside / Escape key dismissal
 *
 * Callers:
 *   - App.tsx — rendered conditionally when contextMenuState is set
 *   - Triggered via ReactFlow onNodeContextMenu
 */

import { useEffect, useRef, useCallback, useState } from 'react';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

export interface ContextMenuState {
  nodeId: string;
  nodeTitle: string;
  x: number;
  y: number;
}

/** Supported node colors for the color submenu. */
export type NodeColor = 'red' | 'orange' | 'yellow' | 'green' | 'blue' | 'purple' | 'gray';

interface NodeContextMenuProps {
  state: ContextMenuState;
  onClose: () => void;
  onStartChat: (nodeId: string) => void;
  onViewProfile: (nodeId: string) => void;
  onRename: (nodeId: string) => void;
  onColorChange: (nodeId: string, color: NodeColor) => void;
  onStartExam: (nodeId: string) => void;
  onViewRelations: (nodeId: string) => void;
  onDelete: (nodeId: string) => void;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Color Definitions
// ═══════════════════════════════════════════════════════════════════════════════

interface ColorOption {
  name: NodeColor;
  label: string;
  hex: string;
}

const COLOR_OPTIONS: ColorOption[] = [
  { name: 'red', label: '红色', hex: '#f38ba8' },
  { name: 'orange', label: '橙色', hex: '#fab387' },
  { name: 'yellow', label: '黄色', hex: '#f9e2af' },
  { name: 'green', label: '绿色', hex: '#a6e3a1' },
  { name: 'blue', label: '蓝色', hex: '#89b4fa' },
  { name: 'purple', label: '紫色', hex: '#cba6f7' },
  { name: 'gray', label: '灰色', hex: '#6c7086' },
];

// ═══════════════════════════════════════════════════════════════════════════════
// SVG Icons
// ═══════════════════════════════════════════════════════════════════════════════

function ChatIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M2 3C2 2.44772 2.44772 2 3 2H13C13.5523 2 14 2.44772 14 3V10C14 10.5523 13.5523 11 13 11H5L2 14V3Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ProfileIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5 6H11M5 8.5H9M5 11H7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function RenameIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M11.5 2.5L13.5 4.5L5.5 12.5L2 13.5L3 10L11.5 2.5Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M10 4L12 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function PaletteIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="6" cy="6" r="1" fill="currentColor" />
      <circle cx="10" cy="6" r="1" fill="currentColor" />
      <circle cx="6.5" cy="9.5" r="1" fill="currentColor" />
    </svg>
  );
}

function ExamIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M3 2H13V14L8 11L3 14V2Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M6 6H10M6 8.5H9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function RelationIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="4" cy="4" r="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="12" cy="12" r="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="12" cy="4" r="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5.5 5.5L10.5 10.5M6 4H10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function DeleteIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M3 4H13L12 14H4L3 4Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M2 4H14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M6 2H10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M6.5 7V11M9.5 7V11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function ChevronRightIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4.5 2.5L8 6L4.5 9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Color Submenu
// ═══════════════════════════════════════════════════════════════════════════════

function ColorSubmenu({
  nodeId,
  onColorChange,
  onClose,
}: {
  nodeId: string;
  onColorChange: (nodeId: string, color: NodeColor) => void;
  onClose: () => void;
}) {
  return (
    <div
      className="absolute left-full top-0 ml-1 rounded-lg shadow-lg border py-2 px-3"
      style={{
        backgroundColor: '#1e1e2e',
        borderColor: '#313244',
      }}
    >
      <div className="flex gap-2">
        {COLOR_OPTIONS.map((opt) => (
          <button
            key={opt.name}
            onClick={() => {
              onColorChange(nodeId, opt.hex as unknown as NodeColor);
              onClose();
            }}
            className="w-5 h-5 rounded-full transition-transform hover:scale-125 focus:outline-none"
            style={{
              backgroundColor: opt.hex,
            }}
            title={opt.label}
          />
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Component
// ═══════════════════════════════════════════════════════════════════════════════

export function NodeContextMenu({
  state,
  onClose,
  onStartChat,
  onViewProfile,
  onRename,
  onColorChange,
  onStartExam,
  onViewRelations,
  onDelete,
}: NodeContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const [showColorSubmenu, setShowColorSubmenu] = useState(false);

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
  const menuWidth = 200;
  const menuHeight = 7 * 36 + 48; // 7 items + header
  const x = Math.min(state.x, window.innerWidth - menuWidth - 8);
  const y = Math.min(state.y, window.innerHeight - menuHeight - 8);

  const handleItemClick = (action: () => void) => {
    action();
    onClose();
  };

  return (
    <div
      ref={menuRef}
      className="fixed z-50 min-w-[200px] rounded-lg shadow-lg border overflow-visible"
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
        {/* 1. 打开对话 */}
        <button
          onClick={() => handleItemClick(() => onStartChat(state.nodeId))}
          className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left transition-colors"
          style={{ color: '#cdd6f4' }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = '#313244';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
          }}
        >
          <span className="w-5 flex justify-center shrink-0"><ChatIcon /></span>
          <span className="flex-1">打开对话</span>
        </button>

        {/* 2. 学习档案 */}
        <button
          onClick={() => handleItemClick(() => onViewProfile(state.nodeId))}
          className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left transition-colors"
          style={{ color: '#cdd6f4' }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = '#313244';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
          }}
        >
          <span className="w-5 flex justify-center shrink-0"><ProfileIcon /></span>
          <span className="flex-1">学习档案</span>
        </button>

        {/* Separator */}
        <div className="my-1 border-t" style={{ borderColor: '#313244' }} />

        {/* 3. 重命名 (F2) */}
        <button
          onClick={() => handleItemClick(() => onRename(state.nodeId))}
          className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left transition-colors"
          style={{ color: '#cdd6f4' }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = '#313244';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
          }}
        >
          <span className="w-5 flex justify-center shrink-0"><RenameIcon /></span>
          <span className="flex-1">重命名</span>
          <span className="text-xs" style={{ color: '#6c7086' }}>F2</span>
        </button>

        {/* 4. 设置颜色 (>) — with hover color submenu */}
        <div
          className="relative"
          onMouseEnter={() => setShowColorSubmenu(true)}
          onMouseLeave={() => setShowColorSubmenu(false)}
        >
          <button
            className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left transition-colors"
            style={{ color: '#cdd6f4' }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.backgroundColor = '#313244';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
            }}
          >
            <span className="w-5 flex justify-center shrink-0"><PaletteIcon /></span>
            <span className="flex-1">设置颜色</span>
            <span className="flex justify-center" style={{ color: '#6c7086' }}><ChevronRightIcon /></span>
          </button>
          {showColorSubmenu && (
            <ColorSubmenu
              nodeId={state.nodeId}
              onColorChange={onColorChange}
              onClose={onClose}
            />
          )}
        </div>

        {/* Separator */}
        <div className="my-1 border-t" style={{ borderColor: '#313244' }} />

        {/* 5. 开始考察 */}
        <button
          onClick={() => handleItemClick(() => onStartExam(state.nodeId))}
          className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left transition-colors"
          style={{ color: '#cdd6f4' }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = '#313244';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
          }}
        >
          <span className="w-5 flex justify-center shrink-0"><ExamIcon /></span>
          <span className="flex-1">开始考察</span>
        </button>

        {/* 6. 查看关联 */}
        <button
          onClick={() => handleItemClick(() => onViewRelations(state.nodeId))}
          className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left transition-colors"
          style={{ color: '#cdd6f4' }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = '#313244';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
          }}
        >
          <span className="w-5 flex justify-center shrink-0"><RelationIcon /></span>
          <span className="flex-1">查看关联</span>
        </button>

        {/* Separator */}
        <div className="my-1 border-t" style={{ borderColor: '#313244' }} />

        {/* 7. 删除节点 (Del) */}
        <button
          onClick={() => handleItemClick(() => onDelete(state.nodeId))}
          className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left transition-colors"
          style={{ color: '#f38ba8' }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = '#313244';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
          }}
        >
          <span className="w-5 flex justify-center shrink-0"><DeleteIcon /></span>
          <span className="flex-1">删除节点</span>
          <span className="text-xs" style={{ color: '#6c7086' }}>Del</span>
        </button>
      </div>
    </div>
  );
}
