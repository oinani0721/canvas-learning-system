/**
 * Canvas File Manager
 * Story 13.2: Canvas API集成 - Task 1
 *
 * Provides Canvas file read/write operations with validation and error handling.
 *
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #2: Reading a Canvas File)
 * ✅ Verified from @obsidian-canvas Skill (Quick Reference #4: Adding Nodes to Canvas)
 * ✅ Verified from specs/api/canvas-api.openapi.yml#readCanvas
 */

import { TFile, Vault, Notice, Events, TAbstractFile } from 'obsidian';
import {
  CanvasData,
  CanvasNode,
  CanvasEdge,
} from '../types/canvas';
import {
  isValidCanvasFile,
  safeJSONParse,
  formatCanvasJSON,
  deepClone,
} from '../utils/canvas-helpers';

/**
 * Canvas file operation result
 */
export interface CanvasOperationResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * Canvas File Manager
 * Handles all Canvas file read/write operations with validation and error handling.
 *
 * Story 13.2: AC 1, 6, 7
 */
export class CanvasFileManager extends Events {
  private vault: Vault;
  private cache: Map<string, { data: CanvasData; mtime: number }> = new Map();

  constructor(vault: Vault) {
    super();
    this.vault = vault;
  }

  // ============================================================================
  // Read Operations
  // ============================================================================

  /**
   * Read Canvas file and return parsed data
   * ✅ Verified from @obsidian-canvas Skill (Quick Reference #2)
   *
   * @param file - Canvas file to read
   * @returns Canvas data
   * @throws Error if file is invalid or corrupted
   */
  async readCanvas(file: TFile): Promise<CanvasData> {
    // Validate file type
    if (!isValidCanvasFile(file)) {
      throw new Error(`Not a valid canvas file: ${file.path}`);
    }

    try {
      // ✅ Verified from @obsidian-canvas Skill (Quick Reference #2)
      // "const content = await this.app.vault.read(file);"
      const content = await this.vault.read(file);

      // Parse JSON
      const data = safeJSONParse<CanvasData>(content);
      if (!data) {
        throw new Error('Invalid JSON format in canvas file');
      }

      // Validate structure
      if (!this.validateCanvasStructure(data)) {
        throw new Error('Invalid canvas file structure');
      }

      // Update cache
      this.cache.set(file.path, {
        data: deepClone(data),
        mtime: file.stat.mtime,
      });

      return data;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Failed to read canvas ${file.path}:`, error);
      new Notice(`Canvas读取失败: ${message}`);
      throw error;
    }
  }

  /**
   * Read Canvas file with result wrapper (non-throwing)
   *
   * @param file - Canvas file to read
   * @returns Operation result with data or error
   */
  async readCanvasSafe(file: TFile): Promise<CanvasOperationResult<CanvasData>> {
    try {
      const data = await this.readCanvas(file);
      return { success: true, data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Get cached canvas data if available and still valid
   *
   * @param file - Canvas file
   * @returns Cached data or null
   */
  getCachedCanvas(file: TFile): CanvasData | null {
    const cached = this.cache.get(file.path);
    if (cached && cached.mtime === file.stat.mtime) {
      return deepClone(cached.data);
    }
    return null;
  }

  // ============================================================================
  // Write Operations
  // ============================================================================

  /**
   * Write Canvas data to file with transaction safety
   * ✅ Verified from @obsidian-canvas Skill (Quick Reference #4)
   *
   * Story 13.2: AC 6 - Transaction safety with temp file
   *
   * @param file - Canvas file to write
   * @param data - Canvas data to write
   * @throws Error if write fails
   */
  async writeCanvas(file: TFile, data: CanvasData): Promise<void> {
    // Validate data structure before write
    if (!this.validateCanvasStructure(data)) {
      throw new Error('Invalid canvas data structure');
    }

    const tempPath = `${file.path}.tmp`;

    try {
      const content = formatCanvasJSON(data);

      // Transaction Step 1: Write to temp file
      const existingTemp = this.vault.getAbstractFileByPath(tempPath);
      if (existingTemp) {
        await this.vault.delete(existingTemp);
      }
      await this.vault.create(tempPath, content);

      // Transaction Step 2: Verify temp file is readable
      const tempFile = this.vault.getAbstractFileByPath(tempPath) as TFile;
      if (!tempFile) {
        throw new Error('Failed to create temporary file');
      }

      const verifyContent = await this.vault.read(tempFile);
      const verifyData = safeJSONParse<CanvasData>(verifyContent);
      if (!verifyData || !this.validateCanvasStructure(verifyData)) {
        throw new Error('Temp file verification failed');
      }

      // Transaction Step 3: Write to original file
      // ✅ Verified from @obsidian-canvas Skill (Quick Reference #4)
      // "await app.vault.modify(canvasFile, newContent);"
      await this.vault.modify(file, content);

      // Transaction Step 4: Clean up temp file
      await this.vault.delete(tempFile);

      // Update cache
      this.cache.set(file.path, {
        data: deepClone(data),
        mtime: file.stat.mtime,
      });

      // Emit change event
      this.trigger('canvas-modified', file);
    } catch (error) {
      // Clean up temp file on failure
      try {
        const tempFile = this.vault.getAbstractFileByPath(tempPath);
        if (tempFile) {
          await this.vault.delete(tempFile);
        }
      } catch {
        // Ignore cleanup errors
      }

      const message = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Failed to write canvas ${file.path}:`, error);
      new Notice(`Canvas保存失败: ${message}`);
      throw error;
    }
  }

  /**
   * Write Canvas file with result wrapper (non-throwing)
   *
   * @param file - Canvas file to write
   * @param data - Canvas data to write
   * @returns Operation result
   */
  async writeCanvasSafe(file: TFile, data: CanvasData): Promise<CanvasOperationResult<void>> {
    try {
      await this.writeCanvas(file, data);
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  // ============================================================================
  // Validation
  // ============================================================================

  /**
   * Validate Canvas data structure
   * Story 13.2: AC 7 - Canvas file structure validation
   *
   * @param data - Data to validate
   * @returns True if structure is valid
   */
  validateCanvasStructure(data: unknown): data is CanvasData {
    if (!data || typeof data !== 'object') {
      return false;
    }

    const canvasData = data as Record<string, unknown>;

    // Check required arrays exist
    if (!Array.isArray(canvasData.nodes)) {
      return false;
    }
    if (!Array.isArray(canvasData.edges)) {
      return false;
    }

    // Validate node structure
    for (const node of canvasData.nodes as unknown[]) {
      if (!this.validateNodeStructure(node)) {
        return false;
      }
    }

    // Validate edge structure
    for (const edge of canvasData.edges as unknown[]) {
      if (!this.validateEdgeStructure(edge)) {
        return false;
      }
    }

    return true;
  }

  /**
   * Validate node structure
   * ✅ Verified from specs/data/canvas-node.schema.json
   *
   * @param node - Node to validate
   * @returns True if node structure is valid
   */
  private validateNodeStructure(node: unknown): node is CanvasNode {
    if (!node || typeof node !== 'object') {
      return false;
    }

    const n = node as Record<string, unknown>;

    // Required fields: id, type, x, y
    if (typeof n.id !== 'string' || n.id.length === 0) {
      return false;
    }

    if (!['text', 'file', 'link', 'group'].includes(n.type as string)) {
      return false;
    }

    if (typeof n.x !== 'number' || typeof n.y !== 'number') {
      return false;
    }

    // Type-specific validation
    switch (n.type) {
      case 'text':
        if (n.text !== undefined && typeof n.text !== 'string') {
          return false;
        }
        break;
      case 'file':
        if (n.file !== undefined && typeof n.file !== 'string') {
          return false;
        }
        break;
      case 'link':
        if (n.url !== undefined && typeof n.url !== 'string') {
          return false;
        }
        break;
      case 'group':
        if (n.label !== undefined && typeof n.label !== 'string') {
          return false;
        }
        break;
    }

    return true;
  }

  /**
   * Validate edge structure
   * ✅ Verified from specs/data/canvas-edge.schema.json
   *
   * @param edge - Edge to validate
   * @returns True if edge structure is valid
   */
  private validateEdgeStructure(edge: unknown): edge is CanvasEdge {
    if (!edge || typeof edge !== 'object') {
      return false;
    }

    const e = edge as Record<string, unknown>;

    // Required fields: id, fromNode, toNode
    if (typeof e.id !== 'string' || e.id.length === 0) {
      return false;
    }

    if (typeof e.fromNode !== 'string' || e.fromNode.length === 0) {
      return false;
    }

    if (typeof e.toNode !== 'string' || e.toNode.length === 0) {
      return false;
    }

    // Optional field validation
    if (e.fromSide !== undefined) {
      if (!['top', 'right', 'bottom', 'left'].includes(e.fromSide as string)) {
        return false;
      }
    }

    if (e.toSide !== undefined) {
      if (!['top', 'right', 'bottom', 'left'].includes(e.toSide as string)) {
        return false;
      }
    }

    if (e.toEnd !== undefined) {
      if (!['none', 'arrow'].includes(e.toEnd as string)) {
        return false;
      }
    }

    return true;
  }

  // ============================================================================
  // File Change Monitoring
  // ============================================================================

  /**
   * Handle external file modification
   * Story 13.2: AC 7 - Auto-reload mechanism
   *
   * @param file - Modified file
   */
  async handleFileModified(file: TAbstractFile): Promise<void> {
    if (!(file instanceof TFile) || !isValidCanvasFile(file)) {
      return;
    }

    // Invalidate cache
    this.cache.delete(file.path);

    // Emit event for external listeners
    this.trigger('canvas-external-modified', file);
  }

  /**
   * Clear cache for a specific file
   *
   * @param filePath - File path to clear from cache
   */
  clearCache(filePath?: string): void {
    if (filePath) {
      this.cache.delete(filePath);
    } else {
      this.cache.clear();
    }
  }

  // ============================================================================
  // Utility Methods
  // ============================================================================

  /**
   * Check if canvas file exists
   *
   * @param path - File path
   * @returns True if file exists
   */
  canvasExists(path: string): boolean {
    const file = this.vault.getAbstractFileByPath(path);
    return file instanceof TFile && isValidCanvasFile(file);
  }

  /**
   * Get Canvas file by path
   *
   * @param path - File path
   * @returns TFile or null
   */
  getCanvasFile(path: string): TFile | null {
    const file = this.vault.getAbstractFileByPath(path);
    if (file instanceof TFile && isValidCanvasFile(file)) {
      return file;
    }
    return null;
  }

  /**
   * Create a new empty Canvas file
   *
   * @param path - File path
   * @returns Created file
   */
  async createCanvas(path: string): Promise<TFile> {
    const emptyCanvas: CanvasData = {
      nodes: [],
      edges: [],
    };

    const content = formatCanvasJSON(emptyCanvas);
    const file = await this.vault.create(path, content);

    return file;
  }
}
