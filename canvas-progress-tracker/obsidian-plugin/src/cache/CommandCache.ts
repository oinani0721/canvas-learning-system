/**
 * CommandCache - Multi-layer caching system for command results
 *
 * Implements AC-4: Command caching mechanism with 5-minute TTL.
 * Features:
 * - Memory cache (fast access)
 * - Optional persistent cache (IndexedDB)
 * - TTL-based expiration
 * - Cache hit rate statistics
 *
 * @module CommandCache
 * @version 1.0.0
 *
 * Source: Story 13.4 Dev Notes - Cache Strategy
 */

import type { CacheItem, CacheStats } from '../types/ReviewTypes';

// ============================================================================
// Constants
// ============================================================================

/** Default cache TTL: 5 minutes in milliseconds */
const DEFAULT_TTL = 5 * 60 * 1000;

/** Maximum items in memory cache */
const MAX_MEMORY_ITEMS = 100;

/** IndexedDB database name */
const DB_NAME = 'canvas-command-cache';

/** IndexedDB store name */
const STORE_NAME = 'commands';

/** IndexedDB version */
const DB_VERSION = 1;

// ============================================================================
// CommandCache Class
// ============================================================================

/**
 * Multi-layer cache for command results
 *
 * Provides both in-memory and persistent caching with TTL support.
 * Source: Story 13.4 Dev Notes - Multi-layer Cache Design
 */
export class CommandCache {
  private memoryCache: Map<string, CacheItem>;
  private db: IDBDatabase | null = null;
  private dbReady: Promise<void> | null = null;
  private stats: CacheStats;
  private readonly defaultTtl: number;
  private readonly persistentCacheEnabled: boolean;

  /**
   * Create a new CommandCache instance
   *
   * @param options - Cache configuration options
   */
  constructor(options: {
    defaultTtl?: number;
    enablePersistentCache?: boolean;
  } = {}) {
    this.memoryCache = new Map();
    this.defaultTtl = options.defaultTtl ?? DEFAULT_TTL;
    this.persistentCacheEnabled = options.enablePersistentCache ?? false;
    this.stats = {
      hits: 0,
      misses: 0,
      itemCount: 0,
      hitRate: 0,
    };

    // Initialize persistent cache if enabled
    if (this.persistentCacheEnabled && typeof indexedDB !== 'undefined') {
      this.dbReady = this.initializeDatabase();
    }
  }

  // ==========================================================================
  // Public Methods
  // ==========================================================================

  /**
   * Get an item from cache
   *
   * @param key - Cache key
   * @returns Cached data or null if not found/expired
   */
  async get<T>(key: string): Promise<T | null> {
    // 1. Check memory cache first (fastest)
    const memoryItem = this.memoryCache.get(key);
    if (memoryItem && !this.isExpired(memoryItem)) {
      this.recordHit();
      return memoryItem.data as T;
    }

    // Remove expired item from memory
    if (memoryItem) {
      this.memoryCache.delete(key);
    }

    // 2. Check persistent cache if enabled
    if (this.persistentCacheEnabled && this.dbReady) {
      await this.dbReady;
      const persistentItem = await this.getPersistent<T>(key);
      if (persistentItem && !this.isExpired(persistentItem)) {
        // Promote to memory cache
        this.memoryCache.set(key, persistentItem);
        this.recordHit();
        return persistentItem.data;
      }

      // Remove expired item from persistent cache
      if (persistentItem) {
        await this.deletePersistent(key);
      }
    }

    this.recordMiss();
    return null;
  }

  /**
   * Set an item in cache
   *
   * @param key - Cache key
   * @param data - Data to cache
   * @param ttl - Time to live in milliseconds (default: 5 minutes)
   */
  async set<T>(key: string, data: T, ttl: number = this.defaultTtl): Promise<void> {
    const item: CacheItem<T> = {
      data,
      timestamp: Date.now(),
      ttl,
    };

    // Enforce memory cache size limit
    if (this.memoryCache.size >= MAX_MEMORY_ITEMS) {
      this.evictOldest();
    }

    // Write to memory cache
    this.memoryCache.set(key, item);
    this.updateItemCount();

    // Write to persistent cache if enabled
    if (this.persistentCacheEnabled && this.dbReady) {
      await this.dbReady;
      await this.setPersistent(key, item);
    }
  }

  /**
   * Delete an item from cache
   *
   * @param key - Cache key
   */
  async delete(key: string): Promise<void> {
    this.memoryCache.delete(key);
    this.updateItemCount();

    if (this.persistentCacheEnabled && this.dbReady) {
      await this.dbReady;
      await this.deletePersistent(key);
    }
  }

  /**
   * Clear all cached items
   */
  async clear(): Promise<void> {
    this.memoryCache.clear();
    this.updateItemCount();

    if (this.persistentCacheEnabled && this.dbReady) {
      await this.dbReady;
      await this.clearPersistent();
    }
  }

  /**
   * Check if a key exists and is not expired
   *
   * @param key - Cache key
   * @returns True if key exists and is valid
   */
  async has(key: string): Promise<boolean> {
    const value = await this.get(key);
    return value !== null;
  }

  /**
   * Get cache statistics
   *
   * @returns Current cache statistics
   */
  getStats(): CacheStats {
    return { ...this.stats };
  }

  /**
   * Reset cache statistics
   */
  resetStats(): void {
    this.stats = {
      hits: 0,
      misses: 0,
      itemCount: this.memoryCache.size,
      hitRate: 0,
    };
  }

  /**
   * Generate a cache key from command and options
   *
   * @param command - Command string
   * @param options - Command options
   * @returns Generated cache key
   */
  static generateKey(command: string, options?: Record<string, unknown>): string {
    const optionsStr = options ? JSON.stringify(options) : '';
    return `cmd:${command}:${optionsStr}`;
  }

  /**
   * Close the cache and release resources
   */
  async close(): Promise<void> {
    if (this.db) {
      this.db.close();
      this.db = null;
    }
  }

  // ==========================================================================
  // Private Methods - Cache Operations
  // ==========================================================================

  /**
   * Check if a cache item is expired
   */
  private isExpired(item: CacheItem): boolean {
    return Date.now() - item.timestamp > item.ttl;
  }

  /**
   * Evict the oldest item from memory cache
   */
  private evictOldest(): void {
    let oldestKey: string | null = null;
    let oldestTime = Infinity;

    for (const [key, item] of this.memoryCache.entries()) {
      if (item.timestamp < oldestTime) {
        oldestTime = item.timestamp;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.memoryCache.delete(oldestKey);
    }
  }

  /**
   * Update item count statistic
   */
  private updateItemCount(): void {
    this.stats.itemCount = this.memoryCache.size;
  }

  /**
   * Record a cache hit
   */
  private recordHit(): void {
    this.stats.hits++;
    this.updateHitRate();
  }

  /**
   * Record a cache miss
   */
  private recordMiss(): void {
    this.stats.misses++;
    this.updateHitRate();
  }

  /**
   * Update hit rate statistic
   */
  private updateHitRate(): void {
    const total = this.stats.hits + this.stats.misses;
    this.stats.hitRate = total > 0 ? (this.stats.hits / total) * 100 : 0;
  }

  // ==========================================================================
  // Private Methods - IndexedDB Operations
  // ==========================================================================

  /**
   * Initialize IndexedDB database
   */
  private async initializeDatabase(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        console.error('Failed to open IndexedDB:', request.error);
        // Disable persistent cache on error
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create object store if it doesn't exist
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME);
        }
      };
    });
  }

  /**
   * Get item from persistent cache
   */
  private async getPersistent<T>(key: string): Promise<CacheItem<T> | null> {
    if (!this.db) return null;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(STORE_NAME, 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get(key);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result ?? null);
    });
  }

  /**
   * Set item in persistent cache
   */
  private async setPersistent<T>(key: string, item: CacheItem<T>): Promise<void> {
    if (!this.db) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(STORE_NAME, 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.put(item, key);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  /**
   * Delete item from persistent cache
   */
  private async deletePersistent(key: string): Promise<void> {
    if (!this.db) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(STORE_NAME, 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.delete(key);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  /**
   * Clear all items from persistent cache
   */
  private async clearPersistent(): Promise<void> {
    if (!this.db) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(STORE_NAME, 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.clear();

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }
}
