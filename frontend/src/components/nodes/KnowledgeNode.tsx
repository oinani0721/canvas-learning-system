import { memo, useState, useCallback, useRef, useEffect } from 'react';
import { Handle, Position, NodeResizer, type NodeProps } from '@xyflow/react';
import type { KnowledgeNodeData } from '../../types';
import { useCanvasStore } from '../../stores/canvas-store';
import { getMasteryBorderClass, getMasteryColor } from '../../services/mastery-utils';

function KnowledgeNodeComponent({ id, data, selected }: NodeProps) {
  const nodeData = data as KnowledgeNodeData;
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(nodeData.title || '');
  const [editContent, setEditContent] = useState(nodeData.content || '');
  const updateNode = useCanvasStore((s) => s.updateNode);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const masteryStatus = nodeData.masteryStatus ?? 'unlearned';
  const borderColor = getMasteryBorderClass(masteryStatus);
  const proficiency = nodeData.effectiveProficiency ?? 0;
  const masteryHex = getMasteryColor(masteryStatus);

  // Sync local state when data changes from outside (e.g. after Dexie reload)
  useEffect(() => {
    if (!isEditing) {
      setEditTitle(nodeData.title || '');
      setEditContent(nodeData.content || '');
    }
  }, [nodeData.title, nodeData.content, isEditing]);

  // DD-11 Wiring: Listen for rename event from context menu
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail?.nodeId === id) {
        setIsEditing(true);
      }
    };
    window.addEventListener('canvas-learning:rename-node', handler);
    return () => window.removeEventListener('canvas-learning:rename-node', handler);
  }, [id]);

  const handleDoubleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
  }, []);

  // Debounced save to Dexie (300ms per AC-2)
  const scheduleSave = useCallback(
    (title: string, content: string) => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        updateNode(id, { title, content });
      }, 300);
    },
    [id, updateNode],
  );

  const handleTitleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newTitle = e.target.value;
      setEditTitle(newTitle);
      scheduleSave(newTitle, editContent);
    },
    [scheduleSave, editContent],
  );

  const handleContentChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const newContent = e.target.value;
      setEditContent(newContent);
      scheduleSave(editTitle, newContent);
    },
    [scheduleSave, editTitle],
  );

  // Container-level blur: only exit editing when focus leaves the entire node
  const handleContainerBlur = useCallback(
    (e: React.FocusEvent) => {
      // Check if the new focus target is still inside this node container
      const relatedTarget = e.relatedTarget as HTMLElement | null;
      if (containerRef.current && relatedTarget && containerRef.current.contains(relatedTarget)) {
        // Focus moved to another input within the node (title → content or vice versa)
        return;
      }
      // Focus left the node entirely — save and exit editing
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
        debounceRef.current = null;
      }
      updateNode(id, { title: editTitle, content: editContent });
      setIsEditing(false);
    },
    [id, editTitle, editContent, updateNode],
  );

  return (
    <div
      ref={containerRef}
      className={`bg-white rounded-lg shadow-md border-2 ${nodeData.color ? '' : borderColor} ${
        selected ? 'ring-2 ring-blue-500' : ''
      } min-w-[200px] relative w-full h-full`}
      style={{
        transition: 'border-color 300ms ease-in-out',
        ...(nodeData.color ? { borderColor: nodeData.color } : {}),
      }}
      onDoubleClick={handleDoubleClick}
      onBlur={isEditing ? handleContainerBlur : undefined}
    >
      {/* Node resize handles — visible when selected */}
      <NodeResizer
        isVisible={selected}
        minWidth={200}
        minHeight={80}
        lineClassName="!border-blue-400"
        handleClassName="!w-2 !h-2 !bg-blue-500 !border-blue-500"
      />
      {/* Story 5-2: Left mastery color bar indicator */}
      {masteryStatus !== 'unlearned' && (
        <div
          className="absolute left-0 top-0 bottom-0 w-1 rounded-l-lg pointer-events-none"
          style={{
            backgroundColor: masteryHex,
            transition: 'background-color 300ms ease-in-out',
          }}
        />
      )}
      {/* Header — drag handle in view mode, title input in edit mode */}
      <div
        className={`px-3 py-2 border-b border-gray-100 ${
          isEditing ? '' : 'cursor-grab active:cursor-grabbing'
        }`}
      >
        {isEditing ? (
          <input
            type="text"
            value={editTitle}
            onChange={handleTitleChange}
            className="w-full text-sm font-medium text-gray-900 border-none outline-none bg-transparent"
            placeholder="Node title..."
            autoFocus
          />
        ) : (
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-900 truncate">
              {nodeData.title || 'Untitled'}
            </span>
            {nodeData.hasExamRecord && (
              <span className="text-xs text-gray-400 ml-2">
                {Math.round(proficiency * 100)}%
              </span>
            )}
          </div>
        )}
      </div>

      {/* Content area — always visible, click to edit */}
      {isEditing ? (
        <div className="px-3 py-2">
          <textarea
            className="w-full text-xs text-gray-800 border-none outline-none resize-y bg-transparent"
            value={editContent}
            onChange={handleContentChange}
            rows={3}
            placeholder="Enter content..."
          />
        </div>
      ) : (
        <div
          className="px-3 py-2 text-xs text-gray-600 min-h-[2rem] cursor-text"
          onClick={(e) => { e.stopPropagation(); setIsEditing(true); }}
        >
          {nodeData.content || <span className="text-gray-300 italic">Click to add content...</span>}
        </div>
      )}

      {/* Mastery bar (Story 5-2: uses mastery status color) */}
      <div className="px-3 pb-2">
        <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{
              width: `${proficiency * 100}%`,
              backgroundColor: masteryHex,
            }}
          />
        </div>
      </div>

      {/* Handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="!w-2 !h-2 !bg-gray-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-2 !h-2 !bg-gray-400"
      />
      <Handle
        type="target"
        position={Position.Left}
        className="!w-2 !h-2 !bg-gray-400"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!w-2 !h-2 !bg-gray-400"
      />
    </div>
  );
}

export const KnowledgeNode = memo(KnowledgeNodeComponent);
