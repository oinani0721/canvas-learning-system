/**
 * ExamCanvas — Examination whiteboard main view (Story 6.1/6.2)
 *
 * Full-screen exam view that replaces the normal canvas when an exam is active.
 * Layout:
 *   - Left: ReactFlow blank canvas for the exam session
 *   - Right: ChatPanel in Mode C (exam conversation)
 *   - Top toolbar: mode label, examined nodes count, HintButton, SkipButton,
 *     end exam button
 *
 * Callers:
 * - App.tsx: renders this when useExamStore.isExamActive === true
 *
 * Wiring:
 * - useExamStore (all exam state)
 * - ChatPanel (exam conversation in sidebar)
 * - HintButton (progressive hints)
 * - SkipButton (skip question)
 */

import { useCallback, useState, useRef, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  type Node,
  type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { nodeTypes } from '../nodes/nodeTypes';
import { ChatPanel } from '../ChatPanel';
import { HintButton } from './HintButton';
import { SkipButton } from './SkipButton';
import { useExamStore } from '../../stores/exam-store';
import { ApiClient } from '../../services/api-client';
import { db } from '../../services/dexie-db';
import { dexieNodeToReactFlow, dexieEdgeToReactFlow } from '../../stores/canvas-store';

/** Mode label display mapping. */
const MODE_LABELS: Record<string, string> = {
  point_to_point: 'Point-to-Point',
  comprehensive: 'Comprehensive',
  mixed: 'Mixed',
};

/** Mode badge color mapping (Catppuccin Mocha). */
const MODE_COLORS: Record<string, { bg: string; text: string }> = {
  point_to_point: { bg: 'bg-[#f38ba8]/20', text: 'text-[#f38ba8]' },
  comprehensive: { bg: 'bg-[#89b4fa]/20', text: 'text-[#89b4fa]' },
  mixed: { bg: 'bg-[#cba6f7]/20', text: 'text-[#cba6f7]' },
};

function ExamCanvasInner() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const reactFlowInstance = useReactFlow();

  // Exam store bindings
  const currentExamId = useExamStore((s) => s.currentExamId);
  const sourceCanvasId = useExamStore((s) => s.sourceCanvasId);
  const examMode = useExamStore((s) => s.examMode);
  const examinedNodes = useExamStore((s) => s.examinedNodes);
  const updateStatus = useExamStore((s) => s.updateStatus);
  const recordNodeExamined = useExamStore((s) => s.recordNodeExamined);
  const recordNodeDiscovered = useExamStore((s) => s.recordNodeDiscovered);
  const setCurrentNode = useExamStore((s) => s.setCurrentNode);

  // End exam confirmation
  const [showEndConfirm, setShowEndConfirm] = useState(false);

  // Shared ApiClient ref for API calls
  const apiClientRef = useRef<ApiClient | null>(null);
  if (!apiClientRef.current) {
    apiClientRef.current = new ApiClient();
  }

  // Load exam canvas nodes from Dexie (source canvas nodes)
  useEffect(() => {
    if (!sourceCanvasId) return;
    (async () => {
      const dexieNodes = await db.canvas_nodes
        .where('canvasId')
        .equals(sourceCanvasId)
        .toArray();
      const dexieEdges = await db.canvas_edges
        .where('canvasId')
        .equals(sourceCanvasId)
        .toArray();
      setNodes(dexieNodes.map(dexieNodeToReactFlow));
      setEdges(dexieEdges.map(dexieEdgeToReactFlow));
    })();
  }, [sourceCanvasId, setNodes, setEdges]);

  // Node click handler — select node for examination
  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      setSelectedNode(node);
      setCurrentNode(node.id);
      recordNodeExamined(node.id);
    },
    [setCurrentNode, recordNodeExamined],
  );

  // Pane click — deselect
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  // Double-click on empty canvas — create exam node
  const lastClickTimeRef = useRef<number>(0);
  const lastClickPosRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  const handlePaneClick = useCallback(
    (event: React.MouseEvent) => {
      const now = Date.now();
      const timeDiff = now - lastClickTimeRef.current;
      const dx = Math.abs(event.clientX - lastClickPosRef.current.x);
      const dy = Math.abs(event.clientY - lastClickPosRef.current.y);

      if (timeDiff < 400 && dx < 10 && dy < 10) {
        // Double-click — create blank exam node on canvas
        const position = reactFlowInstance.screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        });
        const newId = `exam-node-${Date.now()}`;
        const newNode: Node = {
          id: newId,
          type: 'knowledge',
          position,
          data: {
            title: 'New Discovery',
            content: '',
            effectiveProficiency: 0,
          },
        };
        setNodes((nds) => [...nds, newNode]);
        setSelectedNode(newNode);
        setCurrentNode(newId);
        recordNodeDiscovered(newId);
        lastClickTimeRef.current = 0;
        return; // Don't call onPaneClick after double-click creation
      } else {
        lastClickTimeRef.current = now;
        lastClickPosRef.current = { x: event.clientX, y: event.clientY };
      }

      onPaneClick();
    },
    [reactFlowInstance, setNodes, setCurrentNode, recordNodeDiscovered, onPaneClick],
  );

  // End exam handler — transitions to 'completed' status.
  // ExamSummary will be shown by App.tsx; exitExam() is called from there
  // after the user clicks "return to dashboard".
  const handleEndExam = useCallback(() => {
    updateStatus('completed');

    // Patch backend status
    if (currentExamId && apiClientRef.current) {
      apiClientRef.current
        .patch(`/api/v1/exam/${currentExamId}/status`, {
          status: 'completed',
        })
        .catch((err: unknown) =>
          console.warn('[ExamCanvas] Failed to update exam status:', err),
        );
    }

    setShowEndConfirm(false);
  }, [currentExamId, updateStatus]);

  // Escape key closes end-exam dialog
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showEndConfirm) {
        setShowEndConfirm(false);
      }
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [showEndConfirm]);

  const modeLabel = MODE_LABELS[examMode] ?? examMode;
  const modeColors = MODE_COLORS[examMode] ?? MODE_COLORS.mixed;

  return (
    <div className="flex h-screen bg-[#1e1e2e]">
      {/* Main exam canvas area */}
      <div className="flex-1 flex flex-col">
        {/* Top toolbar */}
        <div className="flex items-center justify-between px-4 py-2 bg-[#181825] border-b border-[#313244] shrink-0">
          <div className="flex items-center gap-3">
            {/* Exam badge */}
            <div className="flex items-center gap-1.5">
              <svg
                className="w-4 h-4 text-[#f9e2af]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4.26 10.147a60.438 60.438 0 00-.491 6.347A48.62 48.62 0 0112 20.904a48.62 48.62 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.636 50.636 0 00-2.658-.813A59.906 59.906 0 0112 3.493a59.903 59.903 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0112 13.489a50.702 50.702 0 017.74-3.342"
                />
              </svg>
              <span className="text-xs font-semibold text-[#f9e2af]">
                EXAM
              </span>
            </div>

            {/* Mode badge */}
            <span
              className={`text-xs font-medium px-2 py-0.5 rounded-full ${modeColors.bg} ${modeColors.text}`}
            >
              {modeLabel}
            </span>

            {/* Examined nodes counter */}
            <div className="flex items-center gap-1 text-xs text-[#a6adc8]">
              <svg
                className="w-3.5 h-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>{examinedNodes.length} examined</span>
            </div>

          </div>

          <div className="flex items-center gap-2">
            {/* Hint button */}
            <HintButton />

            {/* Skip button */}
            <SkipButton />

            {/* End exam button */}
            <button
              onClick={() => setShowEndConfirm(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-[#f38ba8]/20 text-[#f38ba8] hover:bg-[#f38ba8]/30 transition-colors"
            >
              <svg
                className="w-3.5 h-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5.25 7.5A2.25 2.25 0 017.5 5.25h9a2.25 2.25 0 012.25 2.25v9a2.25 2.25 0 01-2.25 2.25h-9a2.25 2.25 0 01-2.25-2.25v-9z"
                />
              </svg>
              <span>End Exam</span>
            </button>
          </div>
        </div>

        {/* ReactFlow canvas */}
        <div className="flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            onPaneClick={handlePaneClick}
            nodeTypes={nodeTypes}
            deleteKeyCode={null}
            panOnDrag={[1, 2]}
            panOnScroll={false}
            selectionOnDrag={false}
            fitView
            className="bg-[#11111b]"
          >
            <Background color="#313244" gap={20} />
            <Controls />
          </ReactFlow>
        </div>
      </div>

      {/* Right sidebar — Chat Panel (Mode C: exam conversation) */}
      <div className="w-[350px] border-l border-[#313244] flex flex-col bg-[#1e1e2e]">
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#313244] shrink-0">
          <h2 className="text-sm font-semibold text-[#cdd6f4]">
            Exam Chat
          </h2>
          {selectedNode && (
            <span className="text-xs text-[#a6adc8] truncate ml-2">
              {(selectedNode.data as Record<string, unknown>).title as string}
            </span>
          )}
        </div>
        <div className="flex-1 min-h-0">
          <ChatPanel selectedNode={selectedNode} />
        </div>
      </div>

      {/* End exam confirmation dialog */}
      {showEndConfirm && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setShowEndConfirm(false)}
        >
          <div
            className="bg-[#1e1e2e] border border-[#45475a] rounded-lg shadow-xl p-6 w-80"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 mb-3">
              <svg
                className="w-5 h-5 text-[#f38ba8]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
                />
              </svg>
              <h3 className="text-sm font-medium text-[#cdd6f4]">
                End Exam?
              </h3>
            </div>
            <p className="text-xs text-[#a6adc8] mb-2 leading-relaxed">
              You have examined{' '}
              <span className="text-[#cdd6f4] font-medium">
                {examinedNodes.length}
              </span>{' '}
              node{examinedNodes.length !== 1 ? 's' : ''} in this session.
            </p>
            <p className="text-xs text-[#585b70] mb-4">
              Your mastery scores will be updated based on exam performance.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowEndConfirm(false)}
                className="px-3 py-1.5 text-xs text-[#a6adc8] hover:text-[#cdd6f4] hover:bg-[#313244] rounded-md transition-colors"
              >
                Continue
              </button>
              <button
                onClick={handleEndExam}
                className="px-3 py-1.5 text-xs font-medium bg-[#f38ba8] text-[#1e1e2e] rounded-md hover:bg-[#eba0ac] transition-colors"
              >
                End Exam
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function ExamCanvas() {
  return (
    <ReactFlowProvider>
      <ExamCanvasInner />
    </ReactFlowProvider>
  );
}
