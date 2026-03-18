/**
 * Canvas Learning System - Session Store
 * Story 3.1: Claude Code CLI Integration (AC-3, AC-4)
 *
 * Persists the mapping between canvas node IDs and Claude Code session IDs.
 * Uses a JSON file in the plugin data directory (Obsidian-native approach).
 *
 * Schema: nodeId -> { sessionId, createdAt, lastActiveAt }
 *
 * [Source: _bmad-output/implementation-artifacts/3-1-claude-code-cli-per-node-session.md#Task 3]
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import { dirname, join } from 'path';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

interface SessionRecord {
  sessionId: string;
  createdAt: string;
  lastActiveAt: string;
}

interface SessionStoreData {
  version: 1;
  sessions: Record<string, SessionRecord>;
}

// ═══════════════════════════════════════════════════════════════════════════════
// SessionStore
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Manages the nodeId -> sessionId mapping for per-node Claude Code sessions.
 *
 * Story 3.1 AC-3: First-time nodes get a new session (no --resume).
 * Story 3.1 AC-4: Switching nodes preserves sessions (sessionId persisted).
 *
 * Data is stored as a JSON file at:
 *   .obsidian/plugins/canvas-learning-system/node-sessions.json
 */
export class SessionStore {
  private filePath: string;
  private data: SessionStoreData;

  /**
   * Create a SessionStore instance.
   *
   * @param pluginDataDir - Absolute path to the plugin data directory.
   *   Typically: `${vault}/.obsidian/plugins/canvas-learning-system/`
   */
  constructor(pluginDataDir: string) {
    this.filePath = join(pluginDataDir, 'node-sessions.json');
    this.data = this.load();
  }

  /**
   * Get the session ID for a node.
   *
   * @param nodeId - The canvas node identifier.
   * @returns The session ID, or null if no session exists for this node.
   */
  async getSessionId(nodeId: string): Promise<string | null> {
    const record = this.data.sessions[nodeId];
    return record?.sessionId ?? null;
  }

  /**
   * Create a new session mapping for a node.
   *
   * @param nodeId - The canvas node identifier.
   * @param sessionId - The Claude Code session ID (extracted from stream output).
   */
  async createSession(nodeId: string, sessionId: string): Promise<void> {
    const now = new Date().toISOString();
    this.data.sessions[nodeId] = {
      sessionId,
      createdAt: now,
      lastActiveAt: now,
    };
    this.save();
  }

  /**
   * Update the last active timestamp for a node's session.
   *
   * @param nodeId - The canvas node identifier.
   */
  async updateLastActive(nodeId: string): Promise<void> {
    const record = this.data.sessions[nodeId];
    if (record) {
      record.lastActiveAt = new Date().toISOString();
      this.save();
    }
  }

  /**
   * Remove the session mapping for a node.
   *
   * @param nodeId - The canvas node identifier.
   */
  async deleteSession(nodeId: string): Promise<void> {
    delete this.data.sessions[nodeId];
    this.save();
  }

  /**
   * Get all stored session mappings.
   *
   * @returns Record of nodeId to SessionRecord.
   */
  async getAllSessions(): Promise<Record<string, SessionRecord>> {
    return { ...this.data.sessions };
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Persistence
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Load session data from the JSON file.
   * Returns empty data if the file does not exist or is corrupt.
   */
  private load(): SessionStoreData {
    const empty: SessionStoreData = { version: 1, sessions: {} };

    if (!existsSync(this.filePath)) {
      return empty;
    }

    try {
      const raw = readFileSync(this.filePath, 'utf-8');
      const parsed = JSON.parse(raw) as SessionStoreData;

      // Validate structure
      if (parsed.version === 1 && typeof parsed.sessions === 'object') {
        return parsed;
      }
      console.warn(
        '[Canvas Learning] SessionStore: invalid data format, resetting',
      );
      return empty;
    } catch (err) {
      console.warn(
        '[Canvas Learning] SessionStore: failed to load, resetting:',
        err,
      );
      return empty;
    }
  }

  /**
   * Save session data to the JSON file.
   */
  private save(): void {
    try {
      const dir = dirname(this.filePath);
      if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true });
      }
      writeFileSync(
        this.filePath,
        JSON.stringify(this.data, null, 2),
        'utf-8',
      );
    } catch (err) {
      console.error(
        '[Canvas Learning] SessionStore: failed to save:',
        err,
      );
    }
  }
}
