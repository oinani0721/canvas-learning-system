import { useState, useEffect, useCallback, useRef } from 'react';
import type { TipItem } from '../../types';

interface SelectionToolbarProps {
  /** The node ID used as localStorage key namespace for tips. */
  nodeId: string;
  /**
   * Callback fired when the user clicks "Pull to Node".
   * The parent component is responsible for creating the canvas node.
   */
  onPullToNode?: (selectedText: string) => void;
}

interface ToolbarPosition {
  top: number;
  left: number;
}

/**
 * Floating toolbar that appears above text selected within AI chat messages.
 *
 * Actions:
 *  - "Add Tip": saves the selected text as a TipItem to localStorage
 *  - "Pull to Node": passes the selected text to a parent callback for
 *    whiteboard node creation
 *
 * The toolbar positions itself centered above the selection rect and
 * auto-hides when the selection is cleared or the user clicks outside.
 */
export function SelectionToolbar({ nodeId, onPullToNode }: SelectionToolbarProps) {
  const [selectedText, setSelectedText] = useState('');
  const [position, setPosition] = useState<ToolbarPosition | null>(null);
  const toolbarRef = useRef<HTMLDivElement>(null);

  const hideToolbar = useCallback(() => {
    setSelectedText('');
    setPosition(null);
  }, []);

  // Listen for selection changes within the document.
  useEffect(() => {
    function handleSelectionChange() {
      const selection = window.getSelection();
      if (!selection || selection.isCollapsed || !selection.toString().trim()) {
        // Delay hide so button clicks can fire before the toolbar unmounts.
        return;
      }

      const text = selection.toString().trim();
      if (!text) return;

      // Only activate when the selection originates inside a chat message container.
      const anchorNode = selection.anchorNode;
      if (!anchorNode) return;
      const parentEl =
        anchorNode instanceof HTMLElement ? anchorNode : anchorNode.parentElement;
      if (!parentEl?.closest('[data-chat-message]')) return;

      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();

      setSelectedText(text);
      setPosition({
        top: rect.top + window.scrollY - 44, // 44px above selection
        left: rect.left + window.scrollX + rect.width / 2,
      });
    }

    document.addEventListener('selectionchange', handleSelectionChange);
    return () => document.removeEventListener('selectionchange', handleSelectionChange);
  }, []);

  // Click-outside handling: hide the toolbar when the user clicks anywhere
  // outside of it (but not when clicking the toolbar buttons themselves).
  useEffect(() => {
    function handleMouseDown(e: MouseEvent) {
      if (
        toolbarRef.current &&
        !toolbarRef.current.contains(e.target as HTMLElement)
      ) {
        // Small delay so the browser can clear the selection first.
        requestAnimationFrame(() => {
          const sel = window.getSelection();
          if (!sel || sel.isCollapsed) {
            hideToolbar();
          }
        });
      }
    }

    document.addEventListener('mousedown', handleMouseDown);
    return () => document.removeEventListener('mousedown', handleMouseDown);
  }, [hideToolbar]);

  // ── Add Tip ──────────────────────────────────────────────────────────

  const handleAddTip = useCallback(() => {
    if (!selectedText) return;

    const storageKey = `tips:${nodeId}`;
    const existing: TipItem[] = JSON.parse(localStorage.getItem(storageKey) || '[]');

    const newTip: TipItem = {
      tipId: crypto.randomUUID(),
      content: selectedText,
      category: 'user',
      annotatedAt: new Date().toISOString(),
      contextMessages: [],
    };

    localStorage.setItem(storageKey, JSON.stringify([...existing, newTip]));

    // Clear browser selection and hide toolbar.
    window.getSelection()?.removeAllRanges();
    hideToolbar();
  }, [selectedText, nodeId, hideToolbar]);

  // ── Pull to Node ─────────────────────────────────────────────────────

  const handlePullToNode = useCallback(() => {
    if (!selectedText || !onPullToNode) return;
    onPullToNode(selectedText);

    window.getSelection()?.removeAllRanges();
    hideToolbar();
  }, [selectedText, onPullToNode, hideToolbar]);

  // ── Render ───────────────────────────────────────────────────────────

  if (!position || !selectedText) return null;

  return (
    <div
      ref={toolbarRef}
      role="toolbar"
      aria-label="Text selection actions"
      className="fixed z-[9999] flex items-center gap-1 rounded-lg bg-gray-900 px-1.5 py-1 shadow-lg"
      style={{
        top: position.top,
        left: position.left,
        transform: 'translateX(-50%)',
      }}
    >
      <button
        type="button"
        onClick={handleAddTip}
        className="rounded px-2.5 py-1 text-xs font-medium text-gray-100 transition-colors hover:bg-gray-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
      >
        Add Tip
      </button>

      <span className="h-4 w-px bg-gray-600" aria-hidden="true" />

      <button
        type="button"
        onClick={handlePullToNode}
        disabled={!onPullToNode}
        className="rounded px-2.5 py-1 text-xs font-medium text-gray-100 transition-colors hover:bg-gray-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 disabled:cursor-not-allowed disabled:opacity-40"
      >
        Pull to Node
      </button>

      {/* Caret pointing down toward the selection */}
      <span
        aria-hidden="true"
        className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 border-x-[6px] border-t-[6px] border-x-transparent border-t-gray-900"
      />
    </div>
  );
}
