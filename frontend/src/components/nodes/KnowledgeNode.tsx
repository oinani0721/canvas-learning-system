import { memo, useState, useCallback, useRef, useEffect } from 'react';
import { Handle, Position, NodeResizer, useReactFlow, type NodeProps } from '@xyflow/react';
import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import type { KnowledgeNodeData } from '../../types';
import { useCanvasStore } from '../../stores/canvas-store';
import { getMasteryBorderClass, getMasteryColor } from '../../services/mastery-utils';
import { preprocessWikiLinks, markdownComponents, remarkPlugins, rehypeExtraPlugins } from '../markdown/markdown-renderers';

function KnowledgeNodeComponent({ id, data, selected }: NodeProps) {
  const nodeData = data as KnowledgeNodeData;
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(nodeData.title || '');
  const [editContent, setEditContent] = useState(nodeData.content || '');
  const updateNode = useCanvasStore((s) => s.updateNode);
  const { setNodes } = useReactFlow();
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

  // Save to Dexie + update ReactFlow in-memory state
  const saveAndSync = useCallback(
    (title: string, content: string) => {
      updateNode(id, { title, content });
      // Sync ReactFlow node data so view mode shows updated content
      setNodes((nds) =>
        nds.map((n) =>
          n.id === id
            ? { ...n, data: { ...n.data, title, content } }
            : n,
        ),
      );
    },
    [id, updateNode, setNodes],
  );

  // Debounced save (300ms per AC-2)
  const scheduleSave = useCallback(
    (title: string, content: string) => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        saveAndSync(title, content);
      }, 300);
    },
    [saveAndSync],
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

  // Escape key exits editing (matches Obsidian Canvas behavior)
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        if (debounceRef.current) {
          clearTimeout(debounceRef.current);
          debounceRef.current = null;
        }
        saveAndSync(editTitle, editContent);
        setIsEditing(false);
      }
    },
    [editTitle, editContent, saveAndSync],
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
      saveAndSync(editTitle, editContent);
      setIsEditing(false);
    },
    [editTitle, editContent, saveAndSync],
  );

  return (
    <div
      ref={containerRef}
      className={`bg-white rounded-lg shadow-md border-2 ${nodeData.color ? '' : borderColor} ${
        selected ? 'ring-2 ring-blue-500' : ''
      } min-w-[200px] relative w-full h-full flex flex-col group`}
      style={{
        transition: 'border-color 300ms ease-in-out',
        ...(nodeData.color ? { borderColor: nodeData.color } : {}),
      }}
      onDoubleClick={handleDoubleClick}
      onBlur={isEditing ? handleContainerBlur : undefined}
      onKeyDown={isEditing ? handleKeyDown : undefined}
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
            className="nodrag nopan w-full text-sm font-medium text-gray-900 border-none outline-none bg-transparent"
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

      {/* Content area — nowheel enables scroll inside node instead of canvas zoom */}
      <div className={`nowheel px-3 py-2 flex-1 ${isEditing ? 'overflow-hidden' : 'overflow-auto'}`}>
        {isEditing ? (
          <textarea
            className="nodrag nopan nowheel w-full h-full text-sm text-gray-800 border-none outline-none resize-none bg-transparent min-h-[60px] overflow-auto"
            value={editContent}
            onChange={handleContentChange}
            placeholder="Enter content..."
          />
        ) : (
          <div className="min-h-[40px]">
            {nodeData.content ? (
              <div className="prose prose-sm max-w-none break-words text-gray-600 [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
                <ReactMarkdown
                  remarkPlugins={remarkPlugins}
                  rehypePlugins={[...rehypeExtraPlugins, rehypeSanitize]}
                  components={markdownComponents}
                >
                  {preprocessWikiLinks(nodeData.content)}
                </ReactMarkdown>
              </div>
            ) : (
              <span className="text-gray-300 italic text-sm">Double-click to add content...</span>
            )}
          </div>
        )}
      </div>

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

      {/* Handles — hidden by default, visible on hover (matches Obsidian Canvas) */}
      <Handle
        id="top-target"
        type="target"
        position={Position.Top}
        className="!w-2 !h-2 !bg-gray-400 !opacity-0 !pointer-events-none group-hover:!opacity-100 group-hover:!pointer-events-auto !transition-opacity"
      />
      <Handle
        id="bottom-source"
        type="source"
        position={Position.Bottom}
        className="!w-2 !h-2 !bg-gray-400 !opacity-0 !pointer-events-none group-hover:!opacity-100 group-hover:!pointer-events-auto !transition-opacity"
      />
      <Handle
        id="left-target"
        type="target"
        position={Position.Left}
        className="!w-2 !h-2 !bg-gray-400 !opacity-0 !pointer-events-none group-hover:!opacity-100 group-hover:!pointer-events-auto !transition-opacity"
      />
      <Handle
        id="right-source"
        type="source"
        position={Position.Right}
        className="!w-2 !h-2 !bg-gray-400 !opacity-0 !pointer-events-none group-hover:!opacity-100 group-hover:!pointer-events-auto !transition-opacity"
      />
    </div>
  );
}

export const KnowledgeNode = memo(KnowledgeNodeComponent);
