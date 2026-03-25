/**
 * Tests for Canvas Node API
 * Story 13.2: Canvas API集成 - Task 2
 */

import { CanvasNodeAPI } from '../../src/api/CanvasNodeAPI';
import {
  CanvasData,
  CanvasTextNode,
  CanvasFileNode,
  CanvasNode,
} from '../../src/types/canvas';

describe('CanvasNodeAPI', () => {
  let nodeAPI: CanvasNodeAPI;

  beforeEach(() => {
    nodeAPI = new CanvasNodeAPI();
  });

  describe('generateNodeId', () => {
    it('should generate unique IDs', () => {
      const ids = new Set<string>();
      for (let i = 0; i < 100; i++) {
        ids.add(nodeAPI.generateNodeId());
      }
      expect(ids.size).toBe(100);
    });
  });

  describe('Create Operations', () => {
    describe('createTextNode', () => {
      it('should create a text node with default dimensions', () => {
        const node = nodeAPI.createTextNode(100, 200, 'Test content');

        expect(node.type).toBe('text');
        expect(node.x).toBe(100);
        expect(node.y).toBe(200);
        expect(node.text).toBe('Test content');
        expect(node.width).toBe(250);
        expect(node.height).toBe(60);
        expect(node.id).toBeTruthy();
      });

      it('should create a text node with custom options', () => {
        const node = nodeAPI.createTextNode(0, 0, 'Content', {
          width: 300,
          height: 100,
          color: '1',
        });

        expect(node.width).toBe(300);
        expect(node.height).toBe(100);
        expect(node.color).toBe('1');
      });
    });

    describe('createFileNode', () => {
      it('should create a file node with default dimensions', () => {
        const node = nodeAPI.createFileNode(0, 0, 'path/to/file.md');

        expect(node.type).toBe('file');
        expect(node.file).toBe('path/to/file.md');
        expect(node.width).toBe(400);
        expect(node.height).toBe(300);
      });

      it('should create a file node with subpath', () => {
        const node = nodeAPI.createFileNode(0, 0, 'file.md', {
          subpath: '#Section',
        });

        expect(node.subpath).toBe('#Section');
      });
    });

    describe('createLinkNode', () => {
      it('should create a link node', () => {
        const node = nodeAPI.createLinkNode(0, 0, 'https://example.com');

        expect(node.type).toBe('link');
        expect(node.url).toBe('https://example.com');
      });
    });

    describe('createGroupNode', () => {
      it('should create a group node', () => {
        const node = nodeAPI.createGroupNode(0, 0, 500, 400, {
          label: 'Test Group',
        });

        expect(node.type).toBe('group');
        expect(node.width).toBe(500);
        expect(node.height).toBe(400);
        expect(node.label).toBe('Test Group');
      });
    });

    describe('createNode (generic)', () => {
      it('should create node based on type', () => {
        const textNode = nodeAPI.createNode('text', 0, 0, 'Content');
        expect(textNode.type).toBe('text');

        const fileNode = nodeAPI.createNode('file', 0, 0, 'path.md');
        expect(fileNode.type).toBe('file');

        const linkNode = nodeAPI.createNode('link', 0, 0, 'https://example.com');
        expect(linkNode.type).toBe('link');
      });

      it('should throw for unknown type', () => {
        expect(() => {
          nodeAPI.createNode('unknown' as any, 0, 0, 'content');
        }).toThrow('Unknown node type: unknown');
      });
    });
  });

  describe('Read Operations', () => {
    let canvasData: CanvasData;

    beforeEach(() => {
      canvasData = {
        nodes: [
          { id: 'node-1', type: 'text', x: 0, y: 0, width: 100, height: 60, text: 'Text 1', color: '1' },
          { id: 'node-2', type: 'text', x: 100, y: 0, width: 100, height: 60, text: 'Text 2', color: '2' },
          { id: 'node-3', type: 'file', x: 200, y: 100, width: 400, height: 300, file: 'file.md' },
          { id: 'node-4', type: 'link', x: 300, y: 200, width: 400, height: 300, url: 'https://example.com' },
          { id: 'node-5', type: 'group', x: 0, y: 300, width: 500, height: 400, label: 'Group' },
        ] as CanvasNode[],
        edges: [],
      };
    });

    describe('getNodeById', () => {
      it('should find existing node', () => {
        const node = nodeAPI.getNodeById(canvasData, 'node-1');
        expect(node).not.toBeNull();
        expect(node?.id).toBe('node-1');
      });

      it('should return null for non-existing node', () => {
        const node = nodeAPI.getNodeById(canvasData, 'non-existing');
        expect(node).toBeNull();
      });
    });

    describe('getNodesByColor', () => {
      it('should filter nodes by color', () => {
        const redNodes = nodeAPI.getNodesByColor(canvasData, '1');
        expect(redNodes).toHaveLength(1);
        expect(redNodes[0].id).toBe('node-1');
      });

      it('should return empty array for non-matching color', () => {
        const nodes = nodeAPI.getNodesByColor(canvasData, '6');
        expect(nodes).toHaveLength(0);
      });
    });

    describe('getNodesInArea', () => {
      it('should find nodes in specified area', () => {
        const nodes = nodeAPI.getNodesInArea(canvasData, 0, 0, 150, 150);
        expect(nodes.length).toBeGreaterThan(0);
      });

      it('should return empty for area with no nodes', () => {
        const nodes = nodeAPI.getNodesInArea(canvasData, 1000, 1000, 100, 100);
        expect(nodes).toHaveLength(0);
      });
    });

    describe('getTextNodes', () => {
      it('should return only text nodes', () => {
        const textNodes = nodeAPI.getTextNodes(canvasData);
        expect(textNodes).toHaveLength(2);
        textNodes.forEach((node) => {
          expect(node.type).toBe('text');
        });
      });
    });

    describe('getFileNodes', () => {
      it('should return only file nodes', () => {
        const fileNodes = nodeAPI.getFileNodes(canvasData);
        expect(fileNodes).toHaveLength(1);
        expect(fileNodes[0].type).toBe('file');
      });
    });

    describe('getNodesByType', () => {
      it('should return nodes of specified type', () => {
        const linkNodes = nodeAPI.getNodesByType(canvasData, 'link');
        expect(linkNodes).toHaveLength(1);
        expect(linkNodes[0].type).toBe('link');
      });
    });
  });

  describe('Update Operations', () => {
    let canvasData: CanvasData;

    beforeEach(() => {
      canvasData = {
        nodes: [
          { id: 'node-1', type: 'text', x: 0, y: 0, width: 100, height: 60, text: 'Original' },
        ] as CanvasNode[],
        edges: [],
      };
    });

    describe('updateNode', () => {
      it('should update node properties', () => {
        nodeAPI.updateNode(canvasData, 'node-1', { x: 50, y: 50 });

        const node = canvasData.nodes[0];
        expect(node.x).toBe(50);
        expect(node.y).toBe(50);
      });

      it('should preserve id and type', () => {
        nodeAPI.updateNode(canvasData, 'node-1', {
          x: 100,
        } as any);

        const node = canvasData.nodes[0];
        expect(node.id).toBe('node-1');
        expect(node.type).toBe('text');
      });

      it('should throw for non-existing node', () => {
        expect(() => {
          nodeAPI.updateNode(canvasData, 'non-existing', { x: 0 });
        }).toThrow('Node not found: non-existing');
      });
    });

    describe('updateNodeColor', () => {
      it('should update node color', () => {
        nodeAPI.updateNodeColor(canvasData, 'node-1', '1');
        expect(canvasData.nodes[0].color).toBe('1');
      });
    });

    describe('updateNodePosition', () => {
      it('should update node position', () => {
        nodeAPI.updateNodePosition(canvasData, 'node-1', 200, 300);

        const node = canvasData.nodes[0];
        expect(node.x).toBe(200);
        expect(node.y).toBe(300);
      });
    });

    describe('updateNodeSize', () => {
      it('should update node size', () => {
        nodeAPI.updateNodeSize(canvasData, 'node-1', 500, 400);

        const node = canvasData.nodes[0];
        expect(node.width).toBe(500);
        expect(node.height).toBe(400);
      });
    });

    describe('updateTextNodeContent', () => {
      it('should update text content', () => {
        nodeAPI.updateTextNodeContent(canvasData, 'node-1', 'Updated content');
        expect((canvasData.nodes[0] as CanvasTextNode).text).toBe('Updated content');
      });

      it('should throw for non-text node', () => {
        canvasData.nodes[0] = {
          id: 'node-1',
          type: 'file',
          x: 0,
          y: 0,
          width: 100,
          height: 100,
          file: 'test.md',
        };

        expect(() => {
          nodeAPI.updateTextNodeContent(canvasData, 'node-1', 'Content');
        }).toThrow('Node node-1 is not a text node');
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
          { id: 'edge-2', fromNode: 'node-2', toNode: 'node-3' },
        ],
      };
    });

    describe('deleteNode', () => {
      it('should delete node', () => {
        nodeAPI.deleteNode(canvasData, 'node-2');

        expect(canvasData.nodes).toHaveLength(2);
        expect(nodeAPI.getNodeById(canvasData, 'node-2')).toBeNull();
      });

      it('should cascade delete connected edges', () => {
        nodeAPI.deleteNode(canvasData, 'node-2');

        expect(canvasData.edges).toHaveLength(0);
      });

      it('should throw for non-existing node', () => {
        expect(() => {
          nodeAPI.deleteNode(canvasData, 'non-existing');
        }).toThrow('Node not found: non-existing');
      });
    });

    describe('deleteNodes', () => {
      it('should delete multiple nodes', () => {
        nodeAPI.deleteNodes(canvasData, ['node-1', 'node-3']);

        expect(canvasData.nodes).toHaveLength(1);
        expect(canvasData.nodes[0].id).toBe('node-2');
      });

      it('should cascade delete all connected edges', () => {
        nodeAPI.deleteNodes(canvasData, ['node-1', 'node-3']);

        expect(canvasData.edges).toHaveLength(0);
      });
    });
  });

  describe('Add Operations', () => {
    let canvasData: CanvasData;

    beforeEach(() => {
      canvasData = { nodes: [], edges: [] };
    });

    describe('addNode', () => {
      it('should add a node to canvas', () => {
        const node = nodeAPI.createTextNode(0, 0, 'Test');
        nodeAPI.addNode(canvasData, node);

        expect(canvasData.nodes).toHaveLength(1);
        expect(canvasData.nodes[0]).toBe(node);
      });
    });

    describe('addNodes', () => {
      it('should add multiple nodes', () => {
        const nodes = [
          nodeAPI.createTextNode(0, 0, 'Node 1'),
          nodeAPI.createTextNode(100, 0, 'Node 2'),
        ];
        nodeAPI.addNodes(canvasData, nodes);

        expect(canvasData.nodes).toHaveLength(2);
      });
    });
  });

  describe('Utility Methods', () => {
    let canvasData: CanvasData;

    beforeEach(() => {
      canvasData = {
        nodes: [
          { id: 'text-1', type: 'text', x: 0, y: 0, width: 100, height: 60, text: 'Text' },
          { id: 'text-2', type: 'text', x: 100, y: 0, width: 100, height: 60, text: 'Text 2' },
          { id: 'file-1', type: 'file', x: 200, y: 0, width: 400, height: 300, file: 'file.md' },
        ] as CanvasNode[],
        edges: [],
      };
    });

    describe('nodeExists', () => {
      it('should return true for existing node', () => {
        expect(nodeAPI.nodeExists(canvasData, 'text-1')).toBe(true);
      });

      it('should return false for non-existing node', () => {
        expect(nodeAPI.nodeExists(canvasData, 'non-existing')).toBe(false);
      });
    });

    describe('getNodeCount', () => {
      it('should return correct count', () => {
        expect(nodeAPI.getNodeCount(canvasData)).toBe(3);
      });
    });

    describe('getNodeCountByType', () => {
      it('should return counts by type', () => {
        const counts = nodeAPI.getNodeCountByType(canvasData);

        expect(counts.text).toBe(2);
        expect(counts.file).toBe(1);
        expect(counts.link).toBe(0);
        expect(counts.group).toBe(0);
      });
    });

    describe('createNodeIndex', () => {
      it('should create node index map', () => {
        const index = nodeAPI.createNodeIndex(canvasData);

        expect(index.size).toBe(3);
        expect(index.get('text-1')?.id).toBe('text-1');
        expect(index.get('file-1')?.type).toBe('file');
      });
    });
  });
});
