import { useCallback } from 'react';
import { useReactFlow, type Node, type Edge } from '@xyflow/react';
import { useCanvasStore } from '../stores/canvas-store';

/**
 * usePullToNode — create a new KnowledgeNode from selected text,
 * positioned to the right of the source node, with an auto-created edge.
 *
 * Writes both to ReactFlow (visual) and Dexie (persistence) via canvas-store.
 * Must be used inside a <ReactFlowProvider>.
 */
export function usePullToNode() {
  const { getNode, addNodes, addEdges } = useReactFlow();
  const canvasAddNode = useCanvasStore((s) => s.addNode);
  const canvasAddEdge = useCanvasStore((s) => s.addEdge);

  /**
   * Create a new knowledge node derived from the given text.
   *
   * @param text        - The selected text to populate the new node.
   * @param sourceNodeId - ID of the node the text was selected from.
   * @returns The new node's ID.
   */
  const pullToNode = useCallback(
    (text: string, sourceNodeId: string): string => {
      const newId = crypto.randomUUID();
      const now = new Date().toISOString();

      // Determine position: offset 300px right from source, or fallback to (100, 100)
      const sourceNode = getNode(sourceNodeId);
      const position = sourceNode
        ? { x: sourceNode.position.x + 300, y: sourceNode.position.y }
        : { x: 100, y: 100 };

      const newNode: Node = {
        id: newId,
        type: 'knowledge',
        position,
        data: {
          canvasId: '',
          nodeType: 'text' as const,
          title: text.slice(0, 30),
          content: text,
          createdAt: now,
          updatedAt: now,
          effectiveProficiency: null,
          hasInteraction: false,
          hasExamRecord: false,
          masteryStatus: 'unlearned',
          masteryLevel: null,
          masteryLabel: null,
          fsrs: null,
          indexStatus: 'none',
          tips: [],
          interactionCount: 0,
          examCount: 0,
        },
      };

      const newEdge: Edge = {
        id: crypto.randomUUID(),
        source: sourceNodeId,
        target: newId,
        label: 'derived from',
      };

      // Add to ReactFlow visual state
      addNodes(newNode);
      addEdges(newEdge);

      // Persist to Dexie via canvas-store (async, fire-and-forget for UI responsiveness)
      canvasAddNode(position, text.slice(0, 30)).then((dexieNodeId) => {
        // The canvas-store generates its own ID; we used newId for ReactFlow.
        // To keep them consistent, we rely on ReactFlow being the source of truth
        // for the current session. The Dexie write ensures persistence.
        // Edge also needs Dexie persistence.
        canvasAddEdge(sourceNodeId, dexieNodeId, 'derived from').catch(() => {
          console.warn('[PullToNode] Failed to persist edge to Dexie');
        });
      }).catch(() => {
        console.warn('[PullToNode] Failed to persist node to Dexie');
      });

      return newId;
    },
    [getNode, addNodes, addEdges, canvasAddNode, canvasAddEdge],
  );

  return { pullToNode };
}
