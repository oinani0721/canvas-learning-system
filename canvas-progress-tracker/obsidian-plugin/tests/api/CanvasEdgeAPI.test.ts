/**
 * Tests for Canvas Edge API
 * Story 13.2: Canvas API集成 - Task 3
 */

import { CanvasEdgeAPI } from '../../src/api/CanvasEdgeAPI';
import { CanvasData, CanvasNode, CanvasEdge } from '../../src/types/canvas';

describe('CanvasEdgeAPI', () => {
  let edgeAPI: CanvasEdgeAPI;

  beforeEach(() => {
    edgeAPI = new CanvasEdgeAPI();
  });

  describe('generateEdgeId', () => {
    it('should generate unique IDs', () => {
      const ids = new Set<string>();
      for (let i = 0; i < 100; i++) {
        ids.add(edgeAPI.generateEdgeId());
      }
      expect(ids.size).toBe(100);
    });
  });

  describe('Create Operations', () => {
    describe('createEdge', () => {
      it('should create an edge with default options', () => {
        const edge = edgeAPI.createEdge('node-1', 'node-2');

        expect(edge.fromNode).toBe('node-1');
        expect(edge.toNode).toBe('node-2');
        expect(edge.toEnd).toBe('arrow');
        expect(edge.id).toBeTruthy();
      });

      it('should create an edge with custom options', () => {
        const edge = edgeAPI.createEdge('node-1', 'node-2', {
          fromSide: 'right',
          toSide: 'left',
          toEnd: 'none',
          label: 'Test Label',
          color: '1',
        });

        expect(edge.fromSide).toBe('right');
        expect(edge.toSide).toBe('left');
        expect(edge.toEnd).toBe('none');
        expect(edge.label).toBe('Test Label');
        expect(edge.color).toBe('1');
      });
    });

    describe('createArrowEdge', () => {
      it('should create edge with arrow', () => {
        const edge = edgeAPI.createArrowEdge('node-1', 'node-2');
        expect(edge.toEnd).toBe('arrow');
      });

      it('should set connection sides', () => {
        const edge = edgeAPI.createArrowEdge('node-1', 'node-2', 'bottom', 'top');
        expect(edge.fromSide).toBe('bottom');
        expect(edge.toSide).toBe('top');
      });
    });

    describe('createLineEdge', () => {
      it('should create edge without arrow', () => {
        const edge = edgeAPI.createLineEdge('node-1', 'node-2');
        expect(edge.toEnd).toBe('none');
      });
    });
  });

  describe('Read Operations', () => {
    let canvasData: CanvasData;

    beforeEach(() => {
      canvasData = {
        nodes: [
          { id: 'node-1', type: 'text', x: 0, y: 0, width: 100, height: 60, text: 'Node 1' },
          { id: 'node-2', type: 'text', x: 100, y: 0, width: 100, height: 60, text: 'Node 2' },
          { id: 'node-3', type: 'text', x: 200, y: 0, width: 100, height: 60, text: 'Node 3' },
          { id: 'node-4', type: 'text', x: 300, y: 0, width: 100, height: 60, text: 'Node 4' },
        ] as CanvasNode[],
        edges: [
          { id: 'edge-1', fromNode: 'node-1', toNode: 'node-2' },
          { id: 'edge-2', fromNode: 'node-1', toNode: 'node-3' },
          { id: 'edge-3', fromNode: 'node-2', toNode: 'node-3' },
          { id: 'edge-4', fromNode: 'node-3', toNode: 'node-1' }, // Reverse edge
        ],
      };
    });

    describe('getEdgeById', () => {
      it('should find existing edge', () => {
        const edge = edgeAPI.getEdgeById(canvasData, 'edge-1');
        expect(edge).not.toBeNull();
        expect(edge?.id).toBe('edge-1');
      });

      it('should return null for non-existing edge', () => {
        const edge = edgeAPI.getEdgeById(canvasData, 'non-existing');
        expect(edge).toBeNull();
      });
    });

    describe('getConnectedNodes', () => {
      it('should get all connected nodes', () => {
        const connected = edgeAPI.getConnectedNodes(canvasData, 'node-1');

        // node-1 connects to node-2 (edge-1), node-3 (edge-2, edge-4) = 2 unique nodes
        expect(connected).toHaveLength(2);
        const connectedIds = connected.map((n) => n.id);
        expect(connectedIds).toContain('node-2');
        expect(connectedIds).toContain('node-3');
      });

      it('should return empty array for isolated node', () => {
        const connected = edgeAPI.getConnectedNodes(canvasData, 'node-4');
        expect(connected).toHaveLength(0);
      });
    });

    describe('getEdgesByNode', () => {
      it('should get all edges connected to a node', () => {
        const edges = edgeAPI.getEdgesByNode(canvasData, 'node-1');
        expect(edges).toHaveLength(3);
      });
    });

    describe('getOutgoingEdges', () => {
      it('should get only outgoing edges', () => {
        const edges = edgeAPI.getOutgoingEdges(canvasData, 'node-1');
        expect(edges).toHaveLength(2);
        edges.forEach((edge) => {
          expect(edge.fromNode).toBe('node-1');
        });
      });
    });

    describe('getIncomingEdges', () => {
      it('should get only incoming edges', () => {
        const edges = edgeAPI.getIncomingEdges(canvasData, 'node-1');
        expect(edges).toHaveLength(1);
        expect(edges[0].toNode).toBe('node-1');
      });
    });

    describe('getEdgesBetweenNodes', () => {
      it('should get edges between two nodes (bidirectional)', () => {
        const edges = edgeAPI.getEdgesBetweenNodes(canvasData, 'node-1', 'node-3');
        expect(edges).toHaveLength(2);
      });

      it('should return empty for unconnected nodes', () => {
        const edges = edgeAPI.getEdgesBetweenNodes(canvasData, 'node-1', 'node-4');
        expect(edges).toHaveLength(0);
      });
    });

    describe('areNodesConnected', () => {
      it('should return true for connected nodes', () => {
        expect(edgeAPI.areNodesConnected(canvasData, 'node-1', 'node-2')).toBe(true);
      });

      it('should return false for unconnected nodes', () => {
        expect(edgeAPI.areNodesConnected(canvasData, 'node-1', 'node-4')).toBe(false);
      });
    });

    describe('getChildNodes', () => {
      it('should get nodes pointed to by source node', () => {
        const children = edgeAPI.getChildNodes(canvasData, 'node-1');
        expect(children).toHaveLength(2);
        const childIds = children.map((n) => n.id);
        expect(childIds).toContain('node-2');
        expect(childIds).toContain('node-3');
      });
    });

    describe('getParentNodes', () => {
      it('should get nodes pointing to target node', () => {
        const parents = edgeAPI.getParentNodes(canvasData, 'node-3');
        expect(parents).toHaveLength(2);
        const parentIds = parents.map((n) => n.id);
        expect(parentIds).toContain('node-1');
        expect(parentIds).toContain('node-2');
      });
    });
  });

  describe('Delete Operations', () => {
    let canvasData: CanvasData;

    beforeEach(() => {
      canvasData = {
        nodes: [
          { id: 'node-1', type: 'text', x: 0, y: 0, width: 100, height: 60, text: 'Node 1' },
          { id: 'node-2', type: 'text', x: 100, y: 0, width: 100, height: 60, text: 'Node 2' },
          { id: 'node-3', type: 'text', x: 200, y: 0, width: 100, height: 60, text: 'Node 3' },
        ] as CanvasNode[],
        edges: [
          { id: 'edge-1', fromNode: 'node-1', toNode: 'node-2' },
          { id: 'edge-2', fromNode: 'node-1', toNode: 'node-3' },
          { id: 'edge-3', fromNode: 'node-2', toNode: 'node-3' },
        ],
      };
    });

    describe('deleteEdge', () => {
      it('should delete an edge', () => {
        edgeAPI.deleteEdge(canvasData, 'edge-1');
        expect(canvasData.edges).toHaveLength(2);
        expect(edgeAPI.getEdgeById(canvasData, 'edge-1')).toBeNull();
      });

      it('should throw for non-existing edge', () => {
        expect(() => {
          edgeAPI.deleteEdge(canvasData, 'non-existing');
        }).toThrow('Edge not found: non-existing');
      });
    });

    describe('deleteEdgesByNode', () => {
      it('should delete all edges connected to a node', () => {
        const deleted = edgeAPI.deleteEdgesByNode(canvasData, 'node-1');
        expect(deleted).toBe(2);
        expect(canvasData.edges).toHaveLength(1);
      });
    });

    describe('deleteEdgesBetweenNodes', () => {
      it('should delete edges between two nodes', () => {
        const deleted = edgeAPI.deleteEdgesBetweenNodes(canvasData, 'node-1', 'node-2');
        expect(deleted).toBe(1);
        expect(edgeAPI.areNodesConnected(canvasData, 'node-1', 'node-2')).toBe(false);
      });
    });
  });

  describe('Update Operations', () => {
    let canvasData: CanvasData;

    beforeEach(() => {
      canvasData = {
        nodes: [] as CanvasNode[],
        edges: [{ id: 'edge-1', fromNode: 'node-1', toNode: 'node-2', toEnd: 'arrow' }],
      };
    });

    describe('updateEdge', () => {
      it('should update edge properties', () => {
        edgeAPI.updateEdge(canvasData, 'edge-1', {
          label: 'Updated',
          color: '1',
        });

        const edge = canvasData.edges[0];
        expect(edge.label).toBe('Updated');
        expect(edge.color).toBe('1');
      });

      it('should preserve edge id', () => {
        edgeAPI.updateEdge(canvasData, 'edge-1', {
          label: 'Test',
        } as any);

        expect(canvasData.edges[0].id).toBe('edge-1');
      });

      it('should throw for non-existing edge', () => {
        expect(() => {
          edgeAPI.updateEdge(canvasData, 'non-existing', {});
        }).toThrow('Edge not found: non-existing');
      });
    });

    describe('updateEdgeLabel', () => {
      it('should update edge label', () => {
        edgeAPI.updateEdgeLabel(canvasData, 'edge-1', 'New Label');
        expect(canvasData.edges[0].label).toBe('New Label');
      });
    });

    describe('updateEdgeColor', () => {
      it('should update edge color', () => {
        edgeAPI.updateEdgeColor(canvasData, 'edge-1', '2');
        expect(canvasData.edges[0].color).toBe('2');
      });
    });

    describe('updateEdgeArrow', () => {
      it('should update edge arrow style', () => {
        edgeAPI.updateEdgeArrow(canvasData, 'edge-1', 'none');
        expect(canvasData.edges[0].toEnd).toBe('none');
      });
    });
  });

  describe('Add Operations', () => {
    let canvasData: CanvasData;

    beforeEach(() => {
      canvasData = { nodes: [], edges: [] };
    });

    describe('addEdge', () => {
      it('should add an edge to canvas', () => {
        const edge = edgeAPI.createEdge('node-1', 'node-2');
        edgeAPI.addEdge(canvasData, edge);

        expect(canvasData.edges).toHaveLength(1);
        expect(canvasData.edges[0]).toBe(edge);
      });
    });

    describe('addEdges', () => {
      it('should add multiple edges', () => {
        const edges = [
          edgeAPI.createEdge('node-1', 'node-2'),
          edgeAPI.createEdge('node-2', 'node-3'),
        ];
        edgeAPI.addEdges(canvasData, edges);

        expect(canvasData.edges).toHaveLength(2);
      });
    });

    describe('connectNodes', () => {
      it('should create and add an edge', () => {
        const edge = edgeAPI.connectNodes(canvasData, 'node-1', 'node-2', {
          toEnd: 'arrow',
        });

        expect(canvasData.edges).toHaveLength(1);
        expect(edge.fromNode).toBe('node-1');
        expect(edge.toNode).toBe('node-2');
      });
    });
  });

  describe('Utility Methods', () => {
    let canvasData: CanvasData;

    beforeEach(() => {
      canvasData = {
        nodes: [
          { id: 'node-1', type: 'text', x: 0, y: 0, width: 100, height: 60, text: 'Node 1' },
          { id: 'node-2', type: 'text', x: 100, y: 0, width: 100, height: 60, text: 'Node 2' },
        ] as CanvasNode[],
        edges: [
          { id: 'edge-1', fromNode: 'node-1', toNode: 'node-2' },
          { id: 'edge-2', fromNode: 'node-1', toNode: 'non-existing' },
        ],
      };
    });

    describe('edgeExists', () => {
      it('should return true for existing edge', () => {
        expect(edgeAPI.edgeExists(canvasData, 'edge-1')).toBe(true);
      });

      it('should return false for non-existing edge', () => {
        expect(edgeAPI.edgeExists(canvasData, 'non-existing')).toBe(false);
      });
    });

    describe('getEdgeCount', () => {
      it('should return correct count', () => {
        expect(edgeAPI.getEdgeCount(canvasData)).toBe(2);
      });
    });

    describe('validateEdgeReferences', () => {
      it('should find invalid edge references', () => {
        const invalid = edgeAPI.validateEdgeReferences(canvasData);
        expect(invalid).toHaveLength(1);
        expect(invalid).toContain('edge-2');
      });
    });

    describe('removeOrphanedEdges', () => {
      it('should remove edges with invalid references', () => {
        const removed = edgeAPI.removeOrphanedEdges(canvasData);
        expect(removed).toBe(1);
        expect(canvasData.edges).toHaveLength(1);
      });
    });

    describe('createEdgeIndex', () => {
      it('should create edge index map', () => {
        const index = edgeAPI.createEdgeIndex(canvasData);
        expect(index.size).toBe(2);
        expect(index.get('edge-1')?.fromNode).toBe('node-1');
      });
    });

    describe('createAdjacencyList', () => {
      it('should create bidirectional adjacency list', () => {
        const adjacency = edgeAPI.createAdjacencyList(canvasData);

        expect(adjacency.get('node-1')?.has('node-2')).toBe(true);
        expect(adjacency.get('node-2')?.has('node-1')).toBe(true);
      });
    });
  });
});
