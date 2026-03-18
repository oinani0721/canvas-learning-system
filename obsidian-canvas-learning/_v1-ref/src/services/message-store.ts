/**
 * Canvas Learning System - Message Store
 * Story 3.3: ChatPanel UI (AC-4, Task 5)
 *
 * Persists chat messages to a JSON file for cross-session history.
 * Uses the plugin data directory for storage.
 *
 * Schema per message:
 *   id, nodeId, role, content, createdAt, metadata
 *
 * Design note: Uses a JSON file approach consistent with SessionStore (Story 3.1).
 * SQLite would be ideal but Obsidian plugins run in a renderer process where
 * native modules (better-sqlite3) are not available. JSON file is the pragmatic
 * choice for MVP, with lazy-loading via offset/limit parameters.
 *
 * [Source: _bmad-output/implementation-artifacts/3-3-chat-panel-ui-streaming.md#Task 5]
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import { dirname, join } from 'path';

import type { ChatMessage } from '../stores/chat-state.svelte';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

interface StoredMessage {
  id: string;
  nodeId: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
  metadata?: string;
}

interface MessageStoreData {
  version: 1;
  messages: StoredMessage[];
}

// ═══════════════════════════════════════════════════════════════════════════════
// MessageStore
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Manages persistent storage of chat messages across Obsidian sessions.
 *
 * Story 3.3 AC-4: Messages survive plugin/Obsidian restarts.
 * Messages are stored per node, with lazy-loading support.
 */
export class MessageStore {
  private filePath: string;
  private data: MessageStoreData;

  /**
   * @param pluginDataDir - Plugin data directory path.
   */
  constructor(pluginDataDir: string) {
    this.filePath = join(pluginDataDir, '.obsidian', 'plugins', 'canvas-learning-system', 'chat-messages.json');
    this.data = this.load();
  }

  /**
   * Save a single message.
   *
   * @param nodeId - The node this message belongs to.
   * @param message - The ChatMessage to persist.
   */
  async saveMessage(nodeId: string, message: ChatMessage): Promise<void> {
    // Avoid duplicates
    if (this.data.messages.some((m) => m.id === message.id)) {
      return;
    }

    const stored: StoredMessage = {
      id: message.id,
      nodeId,
      role: message.role,
      content: message.content,
      createdAt: new Date(message.timestamp).toISOString(),
      metadata: message.toolEvents
        ? JSON.stringify(message.toolEvents)
        : undefined,
    };

    this.data.messages.push(stored);
    this.save();
  }

  /**
   * Load messages for a specific node with pagination.
   *
   * Returns messages ordered by createdAt descending (newest first).
   *
   * @param nodeId - The node to load messages for.
   * @param limit - Maximum number of messages to return.
   * @param offset - Number of messages to skip (for pagination).
   * @returns Array of ChatMessage objects.
   */
  async loadMessages(
    nodeId: string,
    limit: number,
    offset: number,
  ): Promise<ChatMessage[]> {
    // Filter messages for this node, sort by createdAt descending
    const nodeMessages = this.data.messages
      .filter((m) => m.nodeId === nodeId)
      .sort(
        (a, b) =>
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
      );

    const page = nodeMessages.slice(offset, offset + limit);

    return page.map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      timestamp: new Date(m.createdAt).getTime(),
      toolEvents: m.metadata ? JSON.parse(m.metadata) : undefined,
    }));
  }

  /**
   * Delete all messages for a node.
   *
   * @param nodeId - The node whose messages to delete.
   */
  async deleteNodeMessages(nodeId: string): Promise<void> {
    this.data.messages = this.data.messages.filter((m) => m.nodeId !== nodeId);
    this.save();
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Persistence
  // ═══════════════════════════════════════════════════════════════════════════

  private load(): MessageStoreData {
    const empty: MessageStoreData = { version: 1, messages: [] };

    if (!existsSync(this.filePath)) {
      return empty;
    }

    try {
      const raw = readFileSync(this.filePath, 'utf-8');
      const parsed = JSON.parse(raw) as MessageStoreData;

      if (parsed.version === 1 && Array.isArray(parsed.messages)) {
        return parsed;
      }
      console.warn(
        '[Canvas Learning] MessageStore: invalid data format, resetting',
      );
      return empty;
    } catch (err) {
      console.warn(
        '[Canvas Learning] MessageStore: failed to load, resetting:',
        err,
      );
      return empty;
    }
  }

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
        '[Canvas Learning] MessageStore: failed to save:',
        err,
      );
    }
  }
}
