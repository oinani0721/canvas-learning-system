import { memo, useState, useCallback, useRef, useEffect } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { KnowledgeNodeData } from '../../types';
import { useCanvasStore } from '../../stores/canvas-store';

const MASTERY_COLORS: Record<string, string> = {
  unlearned: 'border-gray-300',
  learning: 'border-blue-400',
  weak: 'border-red-400',
  developing: 'border-orange-400',
  proficient: 'border-green-500',
  review: 'border-yellow-400',
};

function KnowledgeNodeComponent({ id, data, selected }: NodeProps) {
  const nodeData = data as KnowledgeNodeData;
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(nodeData.title || '');
  const [editContent, setEditContent] = useState(nodeData.content || '');
  const updateNode = useCanvasStore((s) => s.updateNode);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const borderColor =
    MASTERY_COLORS[nodeData.masteryStatus ?? 'unlearned'] ?? 'border-gray-300';
  const proficiency = nodeData.effectiveProficiency ?? 0;

  // Sync local state when data changes from outside (e.g. after Dexie reload)
  useEffect(() => {
    if (!isEditing) {
      setEditTitle(nodeData.title || '');
      setEditContent(nodeData.content || '');
    }
  }, [nodeData.title, nodeData.content, isEditing]);

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

  const handleBlur = useCallback(() => {
    // Flush any pending debounced save
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
      debounceRef.current = null;
    }
    updateNode(id, { title: editTitle, content: editContent });
    setIsEditing(false);
  }, [id, editTitle, editContent, updateNode]);

  return (
    <div
      className={`bg-white rounded-lg shadow-md border-2 ${borderColor} ${
        selected ? 'ring-2 ring-blue-500' : ''
      } min-w-[200px] max-w-[300px]`}
      onDoubleClick={handleDoubleClick}
    >
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
            onBlur={handleBlur}
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

      {/* Content area */}
      {isEditing ? (
        <div className="px-3 py-2">
          <textarea
            className="w-full text-xs text-gray-800 border-none outline-none resize-none bg-transparent"
            value={editContent}
            onChange={handleContentChange}
            onBlur={handleBlur}
            rows={3}
            placeholder="Enter content..."
          />
        </div>
      ) : (
        nodeData.content && (
          <div className="px-3 py-2 text-xs text-gray-600 line-clamp-3">
            {nodeData.content}
          </div>
        )
      )}

      {/* Mastery bar */}
      <div className="px-3 pb-2">
        <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-current rounded-full transition-all duration-300"
            style={{
              width: `${proficiency * 100}%`,
              color:
                proficiency > 0.8
                  ? '#22c55e'
                  : proficiency > 0.5
                    ? '#f59e0b'
                    : '#ef4444',
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
