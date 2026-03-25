// @ts-nocheck - Mock types don't match Obsidian types exactly
/**
 * Tests for Canvas File Manager
 * Story 13.2: Canvas API集成 - Task 1
 */

import { CanvasFileManager } from '../../src/managers/CanvasFileManager';
import { Vault, TFile } from '../__mocks__/obsidian';
import { CanvasData } from '../../src/types/canvas';

// Type assertion helper
const asAny = (x: any) => x as any;

describe('CanvasFileManager', () => {
  let fileManager: CanvasFileManager;
  let vault: Vault;

  const validCanvasData: CanvasData = {
    nodes: [
      { id: 'node-1', type: 'text', x: 0, y: 0, width: 100, height: 60, text: 'Test' },
    ],
    edges: [],
  };

  beforeEach(() => {
    vault = new Vault();
    fileManager = new CanvasFileManager(asAny(vault));
  });

  afterEach(() => {
    vault._clear();
  });

  describe('validateCanvasStructure', () => {
    it('should return true for valid canvas data', () => {
      expect(fileManager.validateCanvasStructure(validCanvasData)).toBe(true);
    });

    it('should return false for null data', () => {
      expect(fileManager.validateCanvasStructure(null)).toBe(false);
    });

    it('should return false for non-object data', () => {
      expect(fileManager.validateCanvasStructure('string')).toBe(false);
      expect(fileManager.validateCanvasStructure(123)).toBe(false);
    });

    it('should return false if nodes is not an array', () => {
      expect(fileManager.validateCanvasStructure({ nodes: {}, edges: [] })).toBe(false);
    });

    it('should return false if edges is not an array', () => {
      expect(fileManager.validateCanvasStructure({ nodes: [], edges: {} })).toBe(false);
    });

    it('should return false for invalid node structure', () => {
      const invalidData = {
        nodes: [{ id: 'node-1' }], // Missing required fields
        edges: [],
      };
      expect(fileManager.validateCanvasStructure(invalidData)).toBe(false);
    });

    it('should return false for invalid node type', () => {
      const invalidData = {
        nodes: [{ id: 'node-1', type: 'invalid', x: 0, y: 0 }],
        edges: [],
      };
      expect(fileManager.validateCanvasStructure(invalidData)).toBe(false);
    });

    it('should return false for invalid edge structure', () => {
      const invalidData = {
        nodes: [],
        edges: [{ id: 'edge-1' }], // Missing fromNode and toNode
      };
      expect(fileManager.validateCanvasStructure(invalidData)).toBe(false);
    });

    it('should validate node type-specific fields', () => {
      const textNodeData = {
        nodes: [
          { id: 'node-1', type: 'text', x: 0, y: 0, width: 100, height: 60, text: 'Content' },
        ],
        edges: [],
      };
      expect(fileManager.validateCanvasStructure(textNodeData)).toBe(true);

      const fileNodeData = {
        nodes: [
          { id: 'node-1', type: 'file', x: 0, y: 0, width: 400, height: 300, file: 'path.md' },
        ],
        edges: [],
      };
      expect(fileManager.validateCanvasStructure(fileNodeData)).toBe(true);
    });

    it('should validate edge side values', () => {
      const validData = {
        nodes: [
          { id: 'node-1', type: 'text', x: 0, y: 0, width: 100, height: 60, text: 'A' },
          { id: 'node-2', type: 'text', x: 100, y: 0, width: 100, height: 60, text: 'B' },
        ],
        edges: [
          { id: 'edge-1', fromNode: 'node-1', toNode: 'node-2', fromSide: 'right', toSide: 'left' },
        ],
      };
      expect(fileManager.validateCanvasStructure(validData)).toBe(true);

      const invalidData = {
        nodes: validData.nodes,
        edges: [
          { id: 'edge-1', fromNode: 'node-1', toNode: 'node-2', fromSide: 'invalid' },
        ],
      };
      expect(fileManager.validateCanvasStructure(invalidData)).toBe(false);
    });

    it('should validate edge toEnd values', () => {
      const validData = {
        nodes: [
          { id: 'node-1', type: 'text', x: 0, y: 0, width: 100, height: 60, text: 'A' },
          { id: 'node-2', type: 'text', x: 100, y: 0, width: 100, height: 60, text: 'B' },
        ],
        edges: [
          { id: 'edge-1', fromNode: 'node-1', toNode: 'node-2', toEnd: 'arrow' },
        ],
      };
      expect(fileManager.validateCanvasStructure(validData)).toBe(true);

      const invalidData = {
        nodes: validData.nodes,
        edges: [
          { id: 'edge-1', fromNode: 'node-1', toNode: 'node-2', toEnd: 'invalid' },
        ],
      };
      expect(fileManager.validateCanvasStructure(invalidData)).toBe(false);
    });
  });

  describe('readCanvas', () => {
    it('should read and parse valid canvas file', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', JSON.stringify(validCanvasData));

      const data = await fileManager.readCanvas(file);

      expect(data.nodes).toHaveLength(1);
      expect(data.edges).toHaveLength(0);
    });

    it('should throw for non-canvas file', async () => {
      const file = new TFile('test.md');

      await expect(fileManager.readCanvas(file)).rejects.toThrow(
        'Not a valid canvas file'
      );
    });

    it('should throw for invalid JSON', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', 'invalid json');

      await expect(fileManager.readCanvas(file)).rejects.toThrow(
        'Invalid JSON format'
      );
    });

    it('should throw for invalid canvas structure', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', JSON.stringify({ invalid: 'data' }));

      await expect(fileManager.readCanvas(file)).rejects.toThrow(
        'Invalid canvas file structure'
      );
    });
  });

  describe('readCanvasSafe', () => {
    it('should return success result for valid canvas', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', JSON.stringify(validCanvasData));

      const result = await fileManager.readCanvasSafe(file);

      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.error).toBeUndefined();
    });

    it('should return error result for invalid canvas', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', 'invalid');

      const result = await fileManager.readCanvasSafe(file);

      expect(result.success).toBe(false);
      expect(result.data).toBeUndefined();
      expect(result.error).toBeDefined();
    });
  });

  describe('writeCanvas', () => {
    it('should write valid canvas data', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', '{}'); // Existing file

      await fileManager.writeCanvas(file, validCanvasData);

      const content = await vault.read(file);
      const parsed = JSON.parse(content);
      expect(parsed.nodes).toHaveLength(1);
    });

    it('should throw for invalid canvas data', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', '{}');

      const invalidData = { nodes: 'not-an-array', edges: [] } as any;

      await expect(fileManager.writeCanvas(file, invalidData)).rejects.toThrow(
        'Invalid canvas data structure'
      );
    });
  });

  describe('writeCanvasSafe', () => {
    it('should return success result for valid write', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', '{}');

      const result = await fileManager.writeCanvasSafe(file, validCanvasData);

      expect(result.success).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('should return error result for failed write', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', '{}');

      const invalidData = { nodes: 'invalid', edges: [] } as any;
      const result = await fileManager.writeCanvasSafe(file, invalidData);

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('getCachedCanvas', () => {
    it('should return cached data for unchanged file', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', JSON.stringify(validCanvasData));

      // Read to populate cache
      await fileManager.readCanvas(file);

      // Get from cache
      const cached = fileManager.getCachedCanvas(file);

      expect(cached).not.toBeNull();
      expect(cached?.nodes).toHaveLength(1);
    });

    it('should return null if file not cached', () => {
      const file = new TFile('uncached.canvas');
      const cached = fileManager.getCachedCanvas(file);
      expect(cached).toBeNull();
    });
  });

  describe('clearCache', () => {
    it('should clear specific file from cache', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', JSON.stringify(validCanvasData));

      await fileManager.readCanvas(file);
      expect(fileManager.getCachedCanvas(file)).not.toBeNull();

      fileManager.clearCache('test.canvas');
      expect(fileManager.getCachedCanvas(file)).toBeNull();
    });

    it('should clear all cache when no path provided', async () => {
      const file1 = new TFile('test1.canvas');
      const file2 = new TFile('test2.canvas');
      vault._setFile('test1.canvas', JSON.stringify(validCanvasData));
      vault._setFile('test2.canvas', JSON.stringify(validCanvasData));

      await fileManager.readCanvas(file1);
      await fileManager.readCanvas(file2);

      fileManager.clearCache();

      expect(fileManager.getCachedCanvas(file1)).toBeNull();
      expect(fileManager.getCachedCanvas(file2)).toBeNull();
    });
  });

  describe('canvasExists', () => {
    it('should return true for existing canvas', () => {
      vault._setFile('test.canvas', '{}');
      expect(fileManager.canvasExists('test.canvas')).toBe(true);
    });

    it('should return false for non-existing file', () => {
      expect(fileManager.canvasExists('nonexistent.canvas')).toBe(false);
    });

    it('should return false for non-canvas file', () => {
      vault._setFile('test.md', '# Content');
      expect(fileManager.canvasExists('test.md')).toBe(false);
    });
  });

  describe('getCanvasFile', () => {
    it('should return file for existing canvas', () => {
      vault._setFile('test.canvas', '{}');
      const file = fileManager.getCanvasFile('test.canvas');
      expect(file).not.toBeNull();
      expect(file?.path).toBe('test.canvas');
    });

    it('should return null for non-existing canvas', () => {
      expect(fileManager.getCanvasFile('nonexistent.canvas')).toBeNull();
    });
  });

  describe('createCanvas', () => {
    it('should create new empty canvas', async () => {
      const file = await fileManager.createCanvas('new.canvas');

      expect(file.path).toBe('new.canvas');

      const content = await vault.read(file);
      const data = JSON.parse(content);
      expect(data.nodes).toEqual([]);
      expect(data.edges).toEqual([]);
    });
  });

  describe('handleFileModified', () => {
    it('should clear cache on file modification', async () => {
      const file = new TFile('test.canvas');
      vault._setFile('test.canvas', JSON.stringify(validCanvasData));

      await fileManager.readCanvas(file);
      expect(fileManager.getCachedCanvas(file)).not.toBeNull();

      await fileManager.handleFileModified(file);
      expect(fileManager.getCachedCanvas(file)).toBeNull();
    });

    it('should ignore non-canvas files', async () => {
      const mdFile = new TFile('test.md');
      await fileManager.handleFileModified(mdFile);
      // Should not throw
    });
  });
});
