/**
 * Tests for Canvas Helper Utilities
 * Story 13.2: Canvas API集成 - Task 6
 */

import {
  BACKUP_FOLDER,
  DEFAULT_NODE_DIMENSIONS,
  CANVAS_EXTENSION,
  generateId,
  generateNodeId,
  generateEdgeId,
  isCanvasPath,
  formatBackupName,
  parseBackupTimestamp,
  extractOriginalName,
  getColorName,
  normalizeColor,
  getNodeCenter,
  isPointInNode,
  doNodesOverlap,
  safeJSONParse,
  formatCanvasJSON,
  deepClone,
} from '../../src/utils/canvas-helpers';

describe('Canvas Helper Utilities', () => {
  describe('Constants', () => {
    it('should have correct backup folder name', () => {
      expect(BACKUP_FOLDER).toBe('.canvas_backups');
    });

    it('should have correct canvas extension', () => {
      expect(CANVAS_EXTENSION).toBe('canvas');
    });

    it('should have default node dimensions', () => {
      expect(DEFAULT_NODE_DIMENSIONS.TEXT).toEqual({ width: 250, height: 60 });
      expect(DEFAULT_NODE_DIMENSIONS.FILE).toEqual({ width: 400, height: 300 });
      expect(DEFAULT_NODE_DIMENSIONS.LINK).toEqual({ width: 400, height: 300 });
      expect(DEFAULT_NODE_DIMENSIONS.GROUP).toEqual({ width: 500, height: 400 });
    });
  });

  describe('ID Generation', () => {
    describe('generateId', () => {
      it('should generate unique IDs', () => {
        const ids = new Set<string>();
        for (let i = 0; i < 1000; i++) {
          ids.add(generateId());
        }
        expect(ids.size).toBe(1000);
      });

      it('should generate alphanumeric IDs', () => {
        const id = generateId();
        expect(id).toMatch(/^[a-z0-9]+$/);
      });
    });

    describe('generateNodeId', () => {
      it('should generate ID without prefix', () => {
        const id = generateNodeId();
        expect(id).toMatch(/^[a-z0-9]+$/);
      });

      it('should generate ID with prefix', () => {
        const id = generateNodeId('text');
        expect(id).toMatch(/^text-[a-z0-9]+$/);
      });
    });

    describe('generateEdgeId', () => {
      it('should generate unique edge IDs', () => {
        const id1 = generateEdgeId();
        const id2 = generateEdgeId();
        expect(id1).not.toBe(id2);
      });
    });
  });

  describe('File Validation', () => {
    describe('isCanvasPath', () => {
      it('should return true for .canvas paths', () => {
        expect(isCanvasPath('test.canvas')).toBe(true);
        expect(isCanvasPath('path/to/file.canvas')).toBe(true);
        expect(isCanvasPath('FILE.CANVAS')).toBe(true);
      });

      it('should return false for non-canvas paths', () => {
        expect(isCanvasPath('test.md')).toBe(false);
        expect(isCanvasPath('test.json')).toBe(false);
        expect(isCanvasPath('canvas')).toBe(false);
      });
    });
  });

  describe('Backup Name Utilities', () => {
    describe('formatBackupName', () => {
      it('should format backup name correctly', () => {
        const timestamp = new Date(2025, 0, 15, 10, 30, 45); // Jan 15, 2025 10:30:45
        const name = formatBackupName('test-canvas', timestamp);
        expect(name).toBe('test-canvas-20250115-103045.canvas');
      });

      it('should pad single digit values', () => {
        const timestamp = new Date(2025, 0, 5, 8, 5, 9); // Jan 5, 2025 08:05:09
        const name = formatBackupName('file', timestamp);
        expect(name).toBe('file-20250105-080509.canvas');
      });
    });

    describe('parseBackupTimestamp', () => {
      it('should parse valid backup filename', () => {
        const timestamp = parseBackupTimestamp('test-20250115-103045.canvas');
        expect(timestamp).not.toBeNull();
        expect(timestamp?.getFullYear()).toBe(2025);
        expect(timestamp?.getMonth()).toBe(0); // January
        expect(timestamp?.getDate()).toBe(15);
        expect(timestamp?.getHours()).toBe(10);
        expect(timestamp?.getMinutes()).toBe(30);
        expect(timestamp?.getSeconds()).toBe(45);
      });

      it('should return null for invalid format', () => {
        expect(parseBackupTimestamp('test.canvas')).toBeNull();
        expect(parseBackupTimestamp('test-2025-103045.canvas')).toBeNull();
        expect(parseBackupTimestamp('test-20250115.canvas')).toBeNull();
      });
    });

    describe('extractOriginalName', () => {
      it('should extract original name from backup', () => {
        expect(extractOriginalName('test-20250115-103045.canvas')).toBe('test');
        expect(extractOriginalName('my-canvas-20250115-103045.canvas')).toBe('my-canvas');
      });

      it('should return null for invalid format', () => {
        expect(extractOriginalName('test.canvas')).toBeNull();
        expect(extractOriginalName('invalid')).toBeNull();
      });
    });
  });

  describe('Color Utilities', () => {
    describe('getColorName', () => {
      it('should return color names for preset codes', () => {
        expect(getColorName('1')).toBe('Red');
        expect(getColorName('2')).toBe('Orange');
        expect(getColorName('3')).toBe('Yellow');
        expect(getColorName('4')).toBe('Green');
        expect(getColorName('5')).toBe('Cyan');
        expect(getColorName('6')).toBe('Purple');
      });
    });

    describe('normalizeColor', () => {
      it('should return undefined for undefined input', () => {
        expect(normalizeColor(undefined)).toBeUndefined();
      });

      it('should return preset colors as-is', () => {
        expect(normalizeColor('1')).toBe('1');
        expect(normalizeColor('6')).toBe('6');
      });

      it('should uppercase hex colors', () => {
        expect(normalizeColor('#ff0000')).toBe('#FF0000');
        expect(normalizeColor('#aabbcc')).toBe('#AABBCC');
      });

      it('should add # to hex colors without it', () => {
        expect(normalizeColor('FF0000')).toBe('#FF0000');
      });

      it('should return undefined for invalid colors', () => {
        expect(normalizeColor('invalid')).toBeUndefined();
        expect(normalizeColor('7')).toBeUndefined();
      });
    });
  });

  describe('Coordinate Utilities', () => {
    describe('getNodeCenter', () => {
      it('should calculate center point correctly', () => {
        const center = getNodeCenter(0, 0, 100, 50);
        expect(center).toEqual({ x: 50, y: 25 });
      });

      it('should handle negative coordinates', () => {
        const center = getNodeCenter(-50, -25, 100, 50);
        expect(center).toEqual({ x: 0, y: 0 });
      });
    });

    describe('isPointInNode', () => {
      it('should return true when point is inside node', () => {
        expect(isPointInNode(50, 30, 0, 0, 100, 60)).toBe(true);
        expect(isPointInNode(0, 0, 0, 0, 100, 60)).toBe(true); // Corner
        expect(isPointInNode(100, 60, 0, 0, 100, 60)).toBe(true); // Corner
      });

      it('should return false when point is outside node', () => {
        expect(isPointInNode(-1, 30, 0, 0, 100, 60)).toBe(false);
        expect(isPointInNode(101, 30, 0, 0, 100, 60)).toBe(false);
        expect(isPointInNode(50, -1, 0, 0, 100, 60)).toBe(false);
        expect(isPointInNode(50, 61, 0, 0, 100, 60)).toBe(false);
      });
    });

    describe('doNodesOverlap', () => {
      it('should detect overlapping nodes', () => {
        const node1 = { x: 0, y: 0, width: 100, height: 100 };
        const node2 = { x: 50, y: 50, width: 100, height: 100 };
        expect(doNodesOverlap(node1, node2)).toBe(true);
      });

      it('should return false for non-overlapping nodes', () => {
        const node1 = { x: 0, y: 0, width: 100, height: 100 };
        const node2 = { x: 200, y: 200, width: 100, height: 100 };
        expect(doNodesOverlap(node1, node2)).toBe(false);
      });

      it('should handle adjacent nodes (touching but not overlapping)', () => {
        const node1 = { x: 0, y: 0, width: 100, height: 100 };
        const node2 = { x: 100, y: 0, width: 100, height: 100 };
        // Adjacent nodes touch at the edge, which is considered overlapping
        expect(doNodesOverlap(node1, node2)).toBe(true);
      });
    });
  });

  describe('JSON Utilities', () => {
    describe('safeJSONParse', () => {
      it('should parse valid JSON', () => {
        const result = safeJSONParse<{ test: string }>('{"test": "value"}');
        expect(result).toEqual({ test: 'value' });
      });

      it('should return null for invalid JSON', () => {
        expect(safeJSONParse('invalid')).toBeNull();
        expect(safeJSONParse('{broken')).toBeNull();
      });
    });

    describe('formatCanvasJSON', () => {
      it('should format with 2-space indentation', () => {
        const data = { nodes: [], edges: [] };
        const result = formatCanvasJSON(data);
        expect(result).toBe('{\n  "nodes": [],\n  "edges": []\n}');
      });
    });

    describe('deepClone', () => {
      it('should create a deep copy', () => {
        const original = {
          nodes: [{ id: '1', nested: { value: 'test' } }],
          edges: [],
        };
        const clone = deepClone(original);

        expect(clone).toEqual(original);
        expect(clone).not.toBe(original);
        expect(clone.nodes).not.toBe(original.nodes);
        expect(clone.nodes[0]).not.toBe(original.nodes[0]);
        expect(clone.nodes[0].nested).not.toBe(original.nodes[0].nested);
      });
    });
  });
});
