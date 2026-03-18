/**
 * ImageNode — ReactFlow custom node for image/visual content
 * Story 1-6: Renders image thumbnail with OCR index status indicator
 */
import { memo, useState, useCallback, useEffect } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { KnowledgeNodeData } from '../../types';

function ImageNodeComponent({ id, data, selected }: NodeProps) {
  const nodeData = data as KnowledgeNodeData;
  const [showStatus, setShowStatus] = useState(true);

  const indexStatus = nodeData.indexStatus ?? 'none';

  // Fadeout after successful indexing (3s)
  useEffect(() => {
    if (indexStatus === 'indexed') {
      const timer = setTimeout(() => setShowStatus(false), 3000);
      return () => clearTimeout(timer);
    }
    setShowStatus(true);
  }, [indexStatus]);

  const statusConfig: Record<string, { text: string; className: string }> = {
    none: { text: '', className: '' },
    indexing: {
      text: '🔄 索引建立中...',
      className: 'text-blue-500 animate-pulse',
    },
    indexed: {
      text: '✅ 已加入搜索索引',
      className: 'text-green-600',
    },
    failed: {
      text: '⚠️ 索引失败，点击重试',
      className: 'text-red-500 cursor-pointer hover:underline',
    },
  };

  const status = statusConfig[indexStatus] ?? statusConfig.none;

  const handleRetry = useCallback(() => {
    if (indexStatus === 'failed') {
      // Dispatch custom event for IndexingService to pick up
      window.dispatchEvent(
        new CustomEvent('image-retry-index', { detail: { nodeId: id } }),
      );
    }
  }, [id, indexStatus]);

  return (
    <div
      className={`bg-white rounded-lg shadow-md border-2 ${
        selected ? 'border-blue-500 ring-2 ring-blue-500' : 'border-gray-200'
      } overflow-hidden min-w-[160px] max-w-[320px]`}
    >
      {/* Header */}
      <div className="px-3 py-1.5 border-b border-gray-100 cursor-grab active:cursor-grabbing">
        <span className="text-xs font-medium text-gray-700 truncate block">
          {nodeData.title || 'Image'}
        </span>
      </div>

      {/* Image thumbnail */}
      {nodeData.imageData ? (
        <div className="relative">
          <img
            src={nodeData.imageData}
            alt={nodeData.title || 'Image node'}
            className="w-full max-h-[200px] object-contain bg-gray-50"
            draggable={false}
          />
        </div>
      ) : (
        <div className="h-[100px] flex items-center justify-center bg-gray-50 text-gray-400 text-xs">
          No image data
        </div>
      )}

      {/* OCR summary preview */}
      {nodeData.ocr?.summary && (
        <div className="px-3 py-1.5 text-xs text-gray-600 border-t border-gray-100 line-clamp-2">
          {nodeData.ocr.summary}
        </div>
      )}

      {/* Index status indicator */}
      {showStatus && status.text && (
        <div
          className={`px-3 py-1 text-xs ${status.className} ${
            indexStatus === 'indexed' ? 'transition-opacity duration-1000' : ''
          }`}
          onClick={indexStatus === 'failed' ? handleRetry : undefined}
        >
          {status.text}
        </div>
      )}

      {/* Handles */}
      <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-gray-400" />
      <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-gray-400" />
      <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-gray-400" />
      <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-gray-400" />
    </div>
  );
}

export const ImageNode = memo(ImageNodeComponent);
