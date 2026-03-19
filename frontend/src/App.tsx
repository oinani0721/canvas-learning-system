import { useCallback, useState, useRef, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  type Connection,
  type Node,
  type Edge,
  type NodeChange,
  type EdgeChange,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { nodeTypes } from './components/nodes/nodeTypes';
import { StatusBar } from './components/StatusBar';
import { Settings } from './components/Settings';
import { ChatPanel } from './components/ChatPanel';
import { useCanvasStore } from './stores/canvas-store';
import { useChatStore, type EdgeContext } from './stores/chat-store';
import { db } from './services/dexie-db';
import { dexieNodeToReactFlow, dexieEdgeToReactFlow } from './stores/canvas-store';
import { SyncEngine } from './services/sync-engine';
import { ApiClient } from './services/api-client';
import { SyncIndicator } from './components/SyncIndicator';
import { IndexingService } from './services/indexing-service';
import { EdgeGuideTooltip } from './components/chat/EdgeGuideTooltip';
import { LearningProfile } from './components/profile/LearningProfile';
import { ReviewItem } from './components/dashboard/ReviewItem';
import { ExamCard } from './components/dashboard/ExamCard';
import { useMasteryStore } from './stores/mastery-store';
import type { ExamSession } from './services/api-client';
import { NodeContextMenu, type ContextMenuState, type NodeColor } from './components/NodeContextMenu';
import { ExamCanvas } from './components/exam/ExamCanvas';
import { ExamSummary } from './components/exam/ExamSummary';
import { ExamModeSelector } from './components/exam/ExamModeSelector';
import { useExamStore } from './stores/exam-store';

// --- Inline input dialog (replaces prompt()) ---

function InlineInput({
  label,
  placeholder,
  onSubmit,
  onCancel,
}: {
  label: string;
  placeholder?: string;
  onSubmit: (value: string) => void;
  onCancel: () => void;
}) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (trimmed) onSubmit(trimmed);
  };

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-80">
        <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSubmit();
            if (e.key === 'Escape') onCancel();
          }}
          placeholder={placeholder}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <div className="flex justify-end gap-2 mt-4">
          <button
            onClick={onCancel}
            className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            OK
          </button>
        </div>
      </div>
    </div>
  );
}

// --- Edge label inline editor ---

function EdgeLabelEditor({
  edgeId,
  currentLabel,
  position,
  onSubmit,
  onCancel,
}: {
  edgeId: string;
  currentLabel: string;
  position: { x: number; y: number };
  onSubmit: (edgeId: string, label: string) => void;
  onCancel: () => void;
}) {
  const [value, setValue] = useState(currentLabel);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, []);

  return (
    <div
      className="fixed z-50"
      style={{ left: position.x - 80, top: position.y - 16 }}
    >
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            onSubmit(edgeId, value.trim());
          }
          if (e.key === 'Escape') onCancel();
        }}
        onBlur={() => onSubmit(edgeId, value.trim())}
        placeholder="Edge label..."
        className="px-2 py-1 text-xs border border-blue-400 rounded shadow-md bg-white focus:outline-none w-40"
      />
    </div>
  );
}

// --- Confirm dialog (replaces confirm()) ---

function ConfirmDialog({
  message,
  onConfirm,
  onCancel,
}: {
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onCancel]);

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50" onClick={onCancel}>
      <div className="bg-white rounded-lg shadow-xl p-6 w-80" onClick={(e) => e.stopPropagation()}>
        <p className="text-sm text-gray-700 mb-4">{message}</p>
        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-3 py-1.5 text-sm bg-red-500 text-white rounded-md hover:bg-red-600"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

// --- Canvas Component ---

function Canvas() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [showNewBoardInput, setShowNewBoardInput] = useState(false);
  const [deletingBoard, setDeletingBoard] = useState<{ id: string; name: string } | null>(null);
  const [editingEdge, setEditingEdge] = useState<{
    id: string;
    label: string;
    position: { x: number; y: number };
  } | null>(null);

  // Story 4-1: Edge dialog — selected edge for sidebar chat
  const [selectedEdgeContext, setSelectedEdgeContext] = useState<EdgeContext | null>(null);
  const chatMode = useChatStore((s) => s.chatMode);
  const exitEdgeMode = useChatStore((s) => s.exitEdgeMode);

  // Story 5-3: Sidebar tab (chat vs profile) when a node is selected
  const [sidebarTab, setSidebarTab] = useState<'chat' | 'profile'>('chat');

  // Scene 1.11: Right-click context menu state
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);

  // Story 5-4: Dashboard tab state
  const [dashboardTab, setDashboardTab] = useState<'boards' | 'exams' | 'review'>('boards');
  const [examSessions, setExamSessions] = useState<ExamSession[]>([]);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [backendOffline, setBackendOffline] = useState(false);
  const reviewNodes = useMasteryStore((s) => s.reviewNodes);
  const loadBatchData = useMasteryStore((s) => s.loadBatchData);

  // Story 6.1/6.2: Exam whiteboard state
  const isExamActive = useExamStore((s) => s.isExamActive);
  const examStatus = useExamStore((s) => s.examStatus);
  const currentExamId = useExamStore((s) => s.currentExamId);
  const exitExam = useExamStore((s) => s.exitExam);
  const enterExam = useExamStore((s) => s.enterExam);
  const [showExamModeSelector, setShowExamModeSelector] = useState(false);
  const [examTargetNodeId, setExamTargetNodeId] = useState<string | undefined>(undefined);
  const [examSourceBoardId, setExamSourceBoardId] = useState<string | null>(null);

  const reactFlowInstance = useReactFlow();

  // Zustand store
  const store = useCanvasStore();
  const {
    boards,
    currentBoardId,
    currentBoardName,
    view,
    selectedNodeId,
    loadBoards,
    createBoard,
    deleteBoard,
    openBoard,
    goToDashboard,
    goToSettings,
    addNode,
    addImageNode,
    updateNode,
    deleteNodes,
    addEdge: storeAddEdge,
    updateEdge,
    deleteEdges,
    setSelectedNodeId,
  } = store;

  // Debounced position sync to Dexie
  const positionSyncRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Shared ApiClient instance
  const apiClientRef = useRef<ApiClient | null>(null);
  if (!apiClientRef.current) {
    apiClientRef.current = new ApiClient();
  }
  const apiClient = apiClientRef.current;

  // SyncEngine — outbox consumer (Story 1-5)
  const syncEngineRef = useRef<SyncEngine | null>(null);
  if (!syncEngineRef.current) {
    syncEngineRef.current = new SyncEngine(apiClient);
  }
  const syncEngine = syncEngineRef.current;

  // IndexingService — async OCR queue (Story 1-6)
  const indexingServiceRef = useRef<IndexingService | null>(null);
  if (!indexingServiceRef.current) {
    indexingServiceRef.current = new IndexingService(apiClient);
  }
  const indexingService = indexingServiceRef.current;

  // Start/stop services on mount/unmount
  useEffect(() => {
    syncEngine.start();
    return () => {
      syncEngine.stop();
      indexingService.destroy();
    };
  }, [syncEngine, indexingService]);

  // Trigger sync after any CRUD operation writes to outbox
  const triggerSync = useCallback(() => {
    syncEngine.triggerSync();
  }, [syncEngine]);

  // Story 5-4: Load dashboard data (exam sessions + mastery batch for review)
  const loadDashboardData = useCallback(async () => {
    setDashboardLoading(true);
    setBackendOffline(false);
    try {
      const [sessions, batch] = await Promise.all([
        apiClient.getExamSessions(),
        apiClient.getMasteryBatch(),
      ]);
      setExamSessions(sessions);
      if (batch) {
        loadBatchData(batch);
      }
    } catch {
      setBackendOffline(true);
    }
    setDashboardLoading(false);
  }, [apiClient, loadBatchData]);

  // Story 6.1: Open exam mode selector (from dashboard or profile)
  const handleStartExamFromProfile = useCallback((nodeId: string) => {
    setExamTargetNodeId(nodeId);
    setExamSourceBoardId(currentBoardId);
    setShowExamModeSelector(true);
  }, [currentBoardId]);

  const handleStartExamFromDashboard = useCallback((boardId: string) => {
    setExamTargetNodeId(undefined);
    setExamSourceBoardId(boardId);
    setShowExamModeSelector(true);
  }, []);

  const handleExamCreated = useCallback(async (examId: string) => {
    setShowExamModeSelector(false);
    await enterExam(examId);
  }, [enterExam]);

  // Return to dashboard from ExamSummary — clean up exam state
  const handleReturnFromExamSummary = useCallback(() => {
    exitExam();
    goToDashboard();
    loadBoards();
  }, [exitExam, goToDashboard, loadBoards]);

  // Load boards on mount
  useEffect(() => {
    loadBoards();
  }, [loadBoards]);

  // Load nodes/edges from Dexie when board changes
  useEffect(() => {
    if (!currentBoardId) return;
    (async () => {
      const dexieNodes = await db.canvas_nodes
        .where('canvasId')
        .equals(currentBoardId)
        .toArray();
      const dexieEdges = await db.canvas_edges
        .where('canvasId')
        .equals(currentBoardId)
        .toArray();
      setNodes(dexieNodes.map(dexieNodeToReactFlow));
      setEdges(dexieEdges.map(dexieEdgeToReactFlow));
    })();
  }, [currentBoardId, setNodes, setEdges]);

  // Sync node position changes to Dexie (debounced)
  const handleNodesChange = useCallback(
    (changes: NodeChange[]) => {
      onNodesChange(changes);

      // Debounce position writes to Dexie
      const positionChanges = changes.filter(
        (c) => c.type === 'position' && c.position && !c.dragging,
      );
      if (positionChanges.length > 0) {
        if (positionSyncRef.current) clearTimeout(positionSyncRef.current);
        positionSyncRef.current = setTimeout(() => {
          for (const change of positionChanges) {
            if (change.type === 'position' && change.position) {
              updateNode(change.id, {
                x: change.position.x,
                y: change.position.y,
              });
            }
          }
        }, 300);
      }
    },
    [onNodesChange, updateNode],
  );

  // Sync edge changes to Dexie
  const handleEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      onEdgesChange(changes);
    },
    [onEdgesChange],
  );

  // Story 4-1 AC-2: Track first-use guide state
  const [showEdgeGuide, setShowEdgeGuide] = useState(false);
  const [edgeGuidePosition, setEdgeGuidePosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Edge creation → Dexie + Story 4-1: show guide on first edge creation
  const onConnect = useCallback(
    async (connection: Connection) => {
      if (!connection.source || !connection.target) return;
      const edgeId = await storeAddEdge(connection.source, connection.target, '');
      const newEdge: Edge = {
        id: edgeId,
        source: connection.source,
        target: connection.target,
        sourceHandle: connection.sourceHandle,
        targetHandle: connection.targetHandle,
        label: '',
      };
      setEdges((eds) => [...eds, newEdge]);
      triggerSync();

      // Story 4-1 AC-2: Show first-use guide if not shown before
      const guideShown = localStorage.getItem('canvas-learning:edge-dialog-guide-shown');
      if (!guideShown) {
        // Show guide tooltip near the center of the viewport
        setEdgeGuidePosition({ x: window.innerWidth / 2, y: window.innerHeight / 2 });
        setShowEdgeGuide(true);
        // Auto-dismiss after 3 seconds
        setTimeout(() => setShowEdgeGuide(false), 3000);
        localStorage.setItem('canvas-learning:edge-dialog-guide-shown', 'true');
      }
    },
    [storeAddEdge, setEdges, triggerSync],
  );

  // Node click → select (and exit edge mode), close context menu
  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      setSelectedNodeId(node.id);
      setSelectedEdgeContext(null);
      setContextMenu(null);
      if (chatMode === 'edge') {
        exitEdgeMode();
      }
    },
    [setSelectedNodeId, chatMode, exitEdgeMode],
  );

  // Scene 1.11: Right-click → show context menu
  const onNodeContextMenu = useCallback(
    (event: React.MouseEvent, node: Node) => {
      event.preventDefault();
      const title =
        ((node.data as Record<string, unknown>)?.title as string) || 'Untitled';
      setContextMenu({
        nodeId: node.id,
        nodeTitle: title,
        x: event.clientX,
        y: event.clientY,
      });
    },
    [],
  );

  // Scene 1.11: Context menu action handlers
  const handleContextMenuStartChat = useCallback(
    (nodeId: string) => {
      setSelectedNodeId(nodeId);
      setSelectedEdgeContext(null);
      setSidebarTab('chat');
    },
    [setSelectedNodeId],
  );

  const handleContextMenuViewProfile = useCallback(
    (nodeId: string) => {
      setSelectedNodeId(nodeId);
      setSelectedEdgeContext(null);
      setSidebarTab('profile');
    },
    [setSelectedNodeId],
  );

  const handleContextMenuRename = useCallback(
    (nodeId: string) => {
      // Select the node and trigger inline editing by dispatching a custom event
      // that KnowledgeNode can listen to, or simulating a double-click.
      // For now: select the node — the KnowledgeNode double-click handler enters edit mode.
      setSelectedNodeId(nodeId);
      setSelectedEdgeContext(null);
      // Dispatch a custom event that KnowledgeNode can pick up to enter rename mode
      window.dispatchEvent(new CustomEvent('canvas-learning:rename-node', { detail: { nodeId } }));
    },
    [setSelectedNodeId],
  );

  const handleContextMenuColorChange = useCallback(
    async (nodeId: string, color: NodeColor) => {
      // Persist color as a non-indexed property on the CanvasNode in Dexie
      await db.canvas_nodes.update(nodeId, { color, updatedAt: new Date().toISOString() });
      // Update ReactFlow node data to reflect the color change visually
      setNodes((nds) =>
        nds.map((n) =>
          n.id === nodeId
            ? { ...n, data: { ...n.data, color } }
            : n,
        ),
      );
      triggerSync();
    },
    [setNodes, triggerSync],
  );

  const handleContextMenuStartExam = useCallback(
    (nodeId: string) => {
      setExamTargetNodeId(nodeId);
      setExamSourceBoardId(currentBoardId);
      setShowExamModeSelector(true);
    },
    [currentBoardId],
  );

  const handleContextMenuViewRelations = useCallback(
    (nodeId: string) => {
      // Select the node so the user sees it highlighted
      setSelectedNodeId(nodeId);
      // Find edges connected to this node and highlight them
      setEdges((eds) =>
        eds.map((e) =>
          e.source === nodeId || e.target === nodeId
            ? { ...e, animated: true, selected: true }
            : { ...e, animated: false, selected: false },
        ),
      );
      console.log(`[查看关联] 节点 ${nodeId} 的关联边已高亮显示。完整关联图功能开发中。`);
    },
    [setSelectedNodeId, setEdges],
  );

  const handleContextMenuDelete = useCallback(
    async (nodeId: string) => {
      const nodeName = nodes.find((n) => n.id === nodeId)?.data?.title || '此节点';
      if (!window.confirm(`确定要删除"${nodeName}"吗？此操作不可撤销。`)) return;
      await deleteNodes([nodeId]);
      triggerSync();
      // Remove from ReactFlow state
      setNodes((nds) => nds.filter((n) => n.id !== nodeId));
      setEdges((eds) =>
        eds.filter((e) => e.source !== nodeId && e.target !== nodeId),
      );
      if (selectedNodeId === nodeId) {
        setSelectedNodeId(null);
      }
    },
    [nodes, deleteNodes, triggerSync, setNodes, setEdges, selectedNodeId, setSelectedNodeId],
  );

  // Story 4-1: Edge click → open edge dialog in sidebar
  const onEdgeClick = useCallback(
    (_event: React.MouseEvent, edge: Edge) => {
      // Look up source and target node titles
      const sourceNode = nodes.find((n) => n.id === edge.source);
      const targetNode = nodes.find((n) => n.id === edge.target);
      const sourceTitle =
        ((sourceNode?.data as Record<string, unknown>)?.title as string) || 'Untitled';
      const targetTitle =
        ((targetNode?.data as Record<string, unknown>)?.title as string) || 'Untitled';

      const edgeCtx: EdgeContext = {
        edgeId: edge.id,
        sourceNodeId: edge.source,
        targetNodeId: edge.target,
        sourceNodeName: sourceTitle,
        targetNodeName: targetTitle,
      };

      setSelectedEdgeContext(edgeCtx);
      setSelectedNodeId(null); // Deselect any node
    },
    [nodes, setSelectedNodeId],
  );

  // Double-click detection on pane → create node in Dexie
  const lastClickTimeRef = useRef<number>(0);
  const lastClickPosRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  const onPaneClick = useCallback(
    async (event: React.MouseEvent) => {
      const now = Date.now();
      const timeDiff = now - lastClickTimeRef.current;
      const dx = Math.abs(event.clientX - lastClickPosRef.current.x);
      const dy = Math.abs(event.clientY - lastClickPosRef.current.y);

      if (timeDiff < 400 && dx < 10 && dy < 10) {
        // Double-click detected → create node
        const position = reactFlowInstance.screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        });
        const nodeId = await addNode(position);
        const dexieNode = await db.canvas_nodes.get(nodeId);
        if (dexieNode) {
          setNodes((nds) => [...nds, dexieNodeToReactFlow(dexieNode)]);
        }
        triggerSync();
        lastClickTimeRef.current = 0;
      } else {
        lastClickTimeRef.current = now;
        lastClickPosRef.current = { x: event.clientX, y: event.clientY };
      }
      setSelectedNodeId(null);
      setSelectedEdgeContext(null);
      setContextMenu(null);
      if (chatMode === 'edge') {
        exitEdgeMode();
      }
    },
    [reactFlowInstance, addNode, setNodes, setSelectedNodeId, chatMode, exitEdgeMode],
  );

  // Delete key → remove selected nodes/edges from Dexie
  const onKeyDown = useCallback(
    async (event: KeyboardEvent) => {
      if (event.key !== 'Delete' && event.key !== 'Backspace') return;
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      )
        return;

      const selectedNodes = nodes.filter((n) => n.selected);
      const selectedEdges = edges.filter((e) => e.selected);
      if (selectedNodes.length === 0 && selectedEdges.length === 0) return;

      const nodeIds = selectedNodes.map((n) => n.id);
      const edgeIds = selectedEdges.map((e) => e.id);

      // Remove from Dexie
      if (edgeIds.length > 0) await deleteEdges(edgeIds);
      if (nodeIds.length > 0) await deleteNodes(nodeIds);
      triggerSync();

      // Remove from ReactFlow state
      const nodeIdSet = new Set(nodeIds);
      const edgeIdSet = new Set(edgeIds);
      setNodes((nds) => nds.filter((n) => !nodeIdSet.has(n.id)));
      setEdges((eds) =>
        eds.filter(
          (e) =>
            !edgeIdSet.has(e.id) &&
            !nodeIdSet.has(e.source) &&
            !nodeIdSet.has(e.target),
        ),
      );
      setSelectedNodeId(null);
    },
    [nodes, edges, deleteNodes, deleteEdges, setNodes, setEdges, setSelectedNodeId],
  );

  useEffect(() => {
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [onKeyDown]);

  // --- Image paste handler (Story 1-6) ---
  const fileToBase64 = useCallback((file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }, []);

  const handleImageFile = useCallback(
    async (file: File, position: { x: number; y: number }) => {
      const MAX_SIZE = 10 * 1024 * 1024;
      if (file.size > MAX_SIZE) {
        console.warn(`Image too large: ${Math.round(file.size / 1024 / 1024)}MB > 10MB`);
        return;
      }
      if (!file.type.startsWith('image/')) return;

      const dataUrl = await fileToBase64(file);
      const nodeId = await addImageNode(position, dataUrl, file.name || 'Image');
      const dexieNode = await db.canvas_nodes.get(nodeId);
      if (dexieNode) {
        setNodes((nds) => [...nds, dexieNodeToReactFlow(dexieNode)]);
      }
      triggerSync();
      // Submit for OCR indexing
      indexingService.submitForIndexing(nodeId);
    },
    [addImageNode, setNodes, triggerSync, indexingService, fileToBase64],
  );

  const onPaste = useCallback(
    async (event: ClipboardEvent) => {
      if (view !== 'canvas') return;
      const items = event.clipboardData?.items;
      if (!items) return;
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          event.preventDefault();
          const file = item.getAsFile();
          if (!file) continue;
          // Place at center of current viewport
          const position = reactFlowInstance.screenToFlowPosition({
            x: window.innerWidth / 2,
            y: window.innerHeight / 2,
          });
          await handleImageFile(file, position);
          break; // Only handle first image
        }
      }
    },
    [view, reactFlowInstance, handleImageFile],
  );

  useEffect(() => {
    document.addEventListener('paste', onPaste);
    return () => document.removeEventListener('paste', onPaste);
  }, [onPaste]);

  // --- Image drop handler (Story 1-6) ---
  const onDrop = useCallback(
    async (event: React.DragEvent) => {
      event.preventDefault();
      const files = event.dataTransfer.files;
      let offsetX = 0;
      for (const file of files) {
        if (!file.type.startsWith('image/')) continue;
        const position = reactFlowInstance.screenToFlowPosition({
          x: event.clientX + offsetX,
          y: event.clientY,
        });
        await handleImageFile(file, position);
        offsetX += 300; // Horizontal spacing for multiple images
      }
    },
    [reactFlowInstance, handleImageFile],
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
  }, []);

  // Edge double-click → inline label editor (replaces prompt())
  const onEdgeDoubleClick = useCallback(
    (_event: React.MouseEvent, edge: Edge) => {
      setEditingEdge({
        id: edge.id,
        label: (edge.label as string) || '',
        position: { x: _event.clientX, y: _event.clientY },
      });
    },
    [],
  );

  const handleEdgeLabelSubmit = useCallback(
    async (edgeId: string, label: string) => {
      await updateEdge(edgeId, { label });
      setEdges((eds) =>
        eds.map((e) => (e.id === edgeId ? { ...e, label } : e)),
      );
      setEditingEdge(null);
      triggerSync();
    },
    [updateEdge, setEdges, triggerSync],
  );

  // Board creation via inline dialog
  const handleCreateBoard = useCallback(
    async (name: string) => {
      await createBoard(name);
      setShowNewBoardInput(false);
      triggerSync();
    },
    [createBoard, triggerSync],
  );

  // Find selected node object for sidebar
  const selectedNode = selectedNodeId
    ? nodes.find((n) => n.id === selectedNodeId) ?? null
    : null;

  // --- Render ---

  // Exam completed — show ExamSummary panel
  if (examStatus === 'completed' && currentExamId) {
    return (
      <ExamSummary
        examId={currentExamId}
        onReturnDashboard={handleReturnFromExamSummary}
      />
    );
  }

  // Story 6.1/6.2: Exam mode — render ExamCanvas when active
  if (isExamActive) {
    return <ExamCanvas />;
  }

  if (view === 'settings') {
    return <Settings onBack={goToDashboard} />;
  }

  if (view === 'dashboard') {
    return (
      <div className="h-screen bg-gray-50 p-8 overflow-y-auto">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900">
              Canvas Learning System
            </h1>
            <div className="flex gap-2">
              <button
                onClick={goToSettings}
                className="px-3 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Settings
              </button>
              <button
                onClick={() => setShowNewBoardInput(true)}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                + New Whiteboard
              </button>
            </div>
          </div>

          {/* Story 5-4: Dashboard Tab Bar */}
          <div className="flex gap-1 mb-6 border-b border-gray-200">
            {(['boards', 'exams', 'review'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => {
                  setDashboardTab(tab);
                  if (tab !== 'boards' && examSessions.length === 0 && reviewNodes.length === 0) {
                    loadDashboardData();
                  }
                }}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  dashboardTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab === 'boards' && 'Whiteboards'}
                {tab === 'exams' && 'Exam History'}
                {tab === 'review' && `Review${reviewNodes.length > 0 ? ` (${reviewNodes.length})` : ''}`}
              </button>
            ))}
          </div>

          {/* Tab Content: Boards */}
          {dashboardTab === 'boards' && (
            <>
              {boards.length === 0 ? (
                <div className="text-center py-20">
                  <p className="text-gray-400 text-lg mb-4">No whiteboards yet</p>
                  <button
                    onClick={() => setShowNewBoardInput(true)}
                    className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                  >
                    Create your first whiteboard
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {boards.map((board) => (
                    <div
                      key={board.id}
                      className="group p-4 bg-white rounded-lg border border-gray-200 hover:border-blue-400 hover:shadow-md transition-all cursor-pointer relative"
                    >
                      <div onClick={() => openBoard(board.id)}>
                        <h3 className="font-medium text-gray-900 mb-1">
                          {board.name}
                        </h3>
                        <p className="text-xs text-gray-400">
                          Created: {new Date(board.createdAt).toLocaleDateString()}
                        </p>
                        <p className="text-xs text-gray-400">
                          Updated: {new Date(board.updatedAt).toLocaleDateString()}
                        </p>
                      </div>
                      {/* Story 6.1: Generate Exam button per board */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStartExamFromDashboard(board.id);
                        }}
                        className="mt-2 w-full px-3 py-1.5 text-xs font-medium text-purple-600 bg-purple-50 rounded-md hover:bg-purple-100 transition-colors opacity-0 group-hover:opacity-100"
                      >
                        Generate Exam
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeletingBoard({ id: board.id, name: board.name });
                        }}
                        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all text-xs px-1.5 py-0.5 rounded hover:bg-red-50"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Tab Content: Exam History (Story 5-4 AC-2) */}
          {dashboardTab === 'exams' && (
            <div>
              {backendOffline ? (
                <div className="text-center py-12 text-gray-400">
                  Backend offline - exam history unavailable
                </div>
              ) : dashboardLoading ? (
                <div className="space-y-3 animate-pulse">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-20 bg-gray-200 rounded-lg" />
                  ))}
                </div>
              ) : examSessions.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  No exam sessions yet. Start an exam from a whiteboard.
                </div>
              ) : (
                <div className="space-y-3">
                  {examSessions.map((session) => (
                    <ExamCard key={session.id} session={session} />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tab Content: Review (Story 5-4 AC-3) */}
          {dashboardTab === 'review' && (
            <div>
              {backendOffline ? (
                <div className="text-center py-12 text-gray-400">
                  Backend offline - review data unavailable
                </div>
              ) : dashboardLoading ? (
                <div className="space-y-2 animate-pulse">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-14 bg-gray-200 rounded" />
                  ))}
                </div>
              ) : reviewNodes.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  All knowledge is fresh! Keep up the great work.
                </div>
              ) : (
                <>
                  {/* Summary stats */}
                  <div className="flex gap-4 mb-4 text-xs">
                    <span className="text-red-500 font-medium">
                      {reviewNodes.filter((n) => n.freshness === 'overdue').length} overdue
                    </span>
                    <span className="text-yellow-500 font-medium">
                      {reviewNodes.filter((n) => n.freshness === 'due').length} due
                    </span>
                    <span className="text-orange-500 font-medium">
                      {reviewNodes.filter((n) => n.freshness !== 'overdue' && n.freshness !== 'due').length} weak
                    </span>
                  </div>
                  <div className="space-y-1 bg-white rounded-lg border border-gray-200 overflow-hidden">
                    {reviewNodes.map((node) => (
                      <ReviewItem key={node.conceptId} node={node} />
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {showNewBoardInput && (
          <InlineInput
            label="Whiteboard Name"
            placeholder="e.g. Linear Algebra, Organic Chemistry..."
            onSubmit={handleCreateBoard}
            onCancel={() => setShowNewBoardInput(false)}
          />
        )}

        {deletingBoard && (
          <ConfirmDialog
            message={`Delete "${deletingBoard.name}" and all its nodes/edges?`}
            onConfirm={() => {
              deleteBoard(deletingBoard.id);
              setDeletingBoard(null);
              triggerSync();
            }}
            onCancel={() => setDeletingBoard(null)}
          />
        )}

        {/* Story 6.1/6.2: Exam mode selector modal */}
        {showExamModeSelector && examSourceBoardId && (
          <ExamModeSelector
            sourceCanvasId={examSourceBoardId}
            targetNodeId={examTargetNodeId}
            onExamCreated={handleExamCreated}
            onCancel={() => setShowExamModeSelector(false)}
          />
        )}
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-white">
      {/* Canvas area */}
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={handleNodesChange}
          onEdgesChange={handleEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onNodeContextMenu={onNodeContextMenu}
          onEdgeClick={onEdgeClick}
          onPaneClick={onPaneClick}
          onEdgeDoubleClick={onEdgeDoubleClick}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          deleteKeyCode={null}
          connectionRadius={12}
          panOnDrag={[1, 2]}
          panOnScroll={false}
          selectionOnDrag
          selectionKeyCode="Shift"
          multiSelectionKeyCode="Control"
          fitView
        >
          <Background />
          <Controls />
        </ReactFlow>

        {editingEdge && (
          <EdgeLabelEditor
            edgeId={editingEdge.id}
            currentLabel={editingEdge.label}
            position={editingEdge.position}
            onSubmit={handleEdgeLabelSubmit}
            onCancel={() => setEditingEdge(null)}
          />
        )}

        {/* Story 4-1 AC-2: First-use edge guide tooltip */}
        {showEdgeGuide && (
          <EdgeGuideTooltip
            position={edgeGuidePosition}
            onDismiss={() => setShowEdgeGuide(false)}
          />
        )}

        {/* Scene 1.11: Node right-click context menu */}
        {contextMenu && (
          <NodeContextMenu
            state={contextMenu}
            onClose={() => setContextMenu(null)}
            onStartChat={handleContextMenuStartChat}
            onViewProfile={handleContextMenuViewProfile}
            onRename={handleContextMenuRename}
            onColorChange={handleContextMenuColorChange}
            onStartExam={handleContextMenuStartExam}
            onViewRelations={handleContextMenuViewRelations}
            onDelete={handleContextMenuDelete}
          />
        )}
      </div>

      {/* Sidebar */}
      <div className="w-[350px] border-l border-gray-200 flex flex-col">
        <div className="flex items-center justify-between p-4 pb-2 shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold">
              {currentBoardName || 'Canvas'}
            </h2>
            <SyncIndicator engine={syncEngine} />
          </div>
          <button
            onClick={() => {
              goToDashboard();
              loadBoards();
            }}
            className="text-xs text-blue-500 hover:text-blue-700"
          >
            &larr; Dashboard
          </button>
        </div>

        {/* Story 4-1: Edge dialog mode in sidebar */}
        {selectedEdgeContext ? (
          <div className="flex flex-col flex-1 min-h-0">
            {/* Edge info header */}
            <div className="px-4 pb-3 border-b border-gray-100 shrink-0">
              <div className="flex items-center gap-2">
                <span className="text-blue-500 text-xs font-medium px-1.5 py-0.5 bg-blue-50 rounded">
                  Edge
                </span>
                <h3 className="font-medium text-gray-900 mb-0 truncate">
                  {selectedEdgeContext.sourceNodeName} &harr; {selectedEdgeContext.targetNodeName}
                </h3>
              </div>
              <p className="text-xs text-gray-400 mt-1">
                Click to discuss the relationship between these concepts
              </p>
            </div>
            {/* Chat panel in edge mode fills remaining space */}
            <div className="flex-1 min-h-0">
              <ChatPanel edgeContext={selectedEdgeContext} />
            </div>
          </div>
        ) : selectedNode ? (
          <div className="flex flex-col flex-1 min-h-0">
            {/* Node info header + Story 5-3: Chat/Profile tab bar */}
            <div className="px-4 pb-0 border-b border-gray-100 shrink-0">
              <h3 className="font-medium text-gray-900 mb-1">
                {(selectedNode.data as Record<string, unknown>).title as string}
              </h3>
              <div className="text-xs text-gray-400 mb-2">
                Mastery:{' '}
                {Math.round(
                  (((selectedNode.data as Record<string, unknown>)
                    .effectiveProficiency as number) ?? 0) * 100,
                )}
                %
              </div>
              {/* Tab bar: Chat | Profile */}
              <div className="flex gap-1">
                <button
                  onClick={() => setSidebarTab('chat')}
                  className={`px-3 py-1.5 text-xs font-medium border-b-2 transition-colors ${
                    sidebarTab === 'chat'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-400 hover:text-gray-600'
                  }`}
                >
                  Chat
                </button>
                <button
                  onClick={() => setSidebarTab('profile')}
                  className={`px-3 py-1.5 text-xs font-medium border-b-2 transition-colors ${
                    sidebarTab === 'profile'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-400 hover:text-gray-600'
                  }`}
                >
                  Profile
                </button>
              </div>
            </div>
            {/* Tab content: Chat or Profile */}
            <div className="flex-1 min-h-0">
              {sidebarTab === 'chat' ? (
                <ChatPanel selectedNode={selectedNode} />
              ) : (
                <LearningProfile
                  nodeId={selectedNode.id}
                  nodeTitle={(selectedNode.data as Record<string, unknown>).title as string}
                  onStartExam={handleStartExamFromProfile}
                  onSwitchToChat={() => setSidebarTab('chat')}
                />
              )}
            </div>
          </div>
        ) : (
          <div className="p-4">
            <p className="text-sm text-gray-500 mb-4">
              Double-click canvas to create a node
            </p>
            <p className="text-xs text-gray-400">
              Click a node to see details
            </p>
            <p className="text-xs text-gray-400">
              Drag from handle to connect nodes
            </p>
            <p className="text-xs text-gray-400">
              Click edge to discuss relationship
            </p>
            <p className="text-xs text-gray-400">
              Double-click edge to add label
            </p>
            <p className="text-xs text-gray-400">
              Select + Delete to remove
            </p>
          </div>
        )}
      </div>

      {/* Story 6.1/6.2: Exam mode selector modal (canvas view) */}
      {showExamModeSelector && examSourceBoardId && (
        <ExamModeSelector
          sourceCanvasId={examSourceBoardId}
          targetNodeId={examTargetNodeId}
          onExamCreated={handleExamCreated}
          onCancel={() => setShowExamModeSelector(false)}
        />
      )}
    </div>
  );
}

// Wrap with ReactFlowProvider for useReactFlow hook
function App() {
  return (
    <ReactFlowProvider>
      <Canvas />
      <StatusBar />
    </ReactFlowProvider>
  );
}

export default App;
