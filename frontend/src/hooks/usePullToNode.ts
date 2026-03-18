import { useCallback } from 'react';
import { useReactFlow, type Node, type Edge } from '@xyflow/react';

/**
 * usePullToNode — create a new KnowledgeNode from selected text,
 * positioned to the right of the source node, with an auto-created edge.
 *
 * Must be used inside a <ReactFlowProvider>.
 */
export function usePullToNode() {
  const { getNode, addNodes, addEdges } = useReactFlow();

  /**
   * Create a new knowledge node derived from the given text.
   *
   * @param text      - The selected text to populate the new node.
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

      addNodes(newNode);
      addEdges(newEdge);

      return newId;
    },
    [getNode, addNodes, addEdges],
  );

  return { pullToNode };
}
