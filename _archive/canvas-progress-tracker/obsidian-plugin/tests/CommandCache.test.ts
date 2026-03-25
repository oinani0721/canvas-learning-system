/**
 * CommandCache Unit Tests
 *
 * Tests for the multi-layer caching system.
 *
 * @module tests/CommandCache
 */

// Jest globals are available (describe, it, expect, beforeEach, afterEach)
import { CommandCache } from '../src/cache/CommandCache';

describe('CommandCache', () => {
  let cache: CommandCache;

  beforeEach(() => {
    cache = new CommandCache({
      defaultTtl: 5000, // 5 seconds for testing
      enablePersistentCache: false,
    });
  });

  afterEach(async () => {
    await cache.close();
  });

  describe('Basic Operations', () => {
    it('should store and retrieve values', async () => {
      await cache.set('key1', { data: 'test' });
      const result = await cache.get('key1');
      expect(result).toEqual({ data: 'test' });
    });

    it('should return null for non-existent keys', async () => {
      const result = await cache.get('non-existent');
      expect(result).toBeNull();
    });

    it('should delete values', async () => {
      await cache.set('key1', 'value1');
      await cache.delete('key1');
      const result = await cache.get('key1');
      expect(result).toBeNull();
    });

    it('should clear all values', async () => {
      await cache.set('key1', 'value1');
      await cache.set('key2', 'value2');
      await cache.clear();
      expect(await cache.get('key1')).toBeNull();
      expect(await cache.get('key2')).toBeNull();
    });

    it('should check if key exists', async () => {
      await cache.set('key1', 'value1');
      expect(await cache.has('key1')).toBe(true);
      expect(await cache.has('key2')).toBe(false);
    });
  });

  describe('TTL and Expiration', () => {
    it('should expire items after TTL', async () => {
      jest.useFakeTimers();

      await cache.set('key1', 'value1', 1000); // 1 second TTL
      expect(await cache.get('key1')).toBe('value1');

      jest.advanceTimersByTime(1500); // Advance past TTL
      expect(await cache.get('key1')).toBeNull();

      jest.useRealTimers();
    });

    it('should use custom TTL when provided', async () => {
      jest.useFakeTimers();

      await cache.set('key1', 'value1', 2000); // 2 seconds
      jest.advanceTimersByTime(1500);
      expect(await cache.get('key1')).toBe('value1');

      jest.advanceTimersByTime(1000);
      expect(await cache.get('key1')).toBeNull();

      jest.useRealTimers();
    });
  });

  describe('Statistics', () => {
    it('should track cache hits', async () => {
      await cache.set('key1', 'value1');
      await cache.get('key1'); // Hit
      await cache.get('key1'); // Hit

      const stats = cache.getStats();
      expect(stats.hits).toBe(2);
    });

    it('should track cache misses', async () => {
      await cache.get('non-existent-1'); // Miss
      await cache.get('non-existent-2'); // Miss

      const stats = cache.getStats();
      expect(stats.misses).toBe(2);
    });

    it('should calculate hit rate', async () => {
      await cache.set('key1', 'value1');
      await cache.get('key1'); // Hit
      await cache.get('key2'); // Miss

      const stats = cache.getStats();
      expect(stats.hitRate).toBe(50);
    });

    it('should track item count', async () => {
      await cache.set('key1', 'value1');
      await cache.set('key2', 'value2');

      const stats = cache.getStats();
      expect(stats.itemCount).toBe(2);
    });

    it('should reset statistics', async () => {
      await cache.set('key1', 'value1');
      await cache.get('key1');
      cache.resetStats();

      const stats = cache.getStats();
      expect(stats.hits).toBe(0);
      expect(stats.misses).toBe(0);
      expect(stats.hitRate).toBe(0);
    });
  });

  describe('Key Generation', () => {
    it('should generate consistent keys', () => {
      const key1 = CommandCache.generateKey('/review show', { limit: 10 });
      const key2 = CommandCache.generateKey('/review show', { limit: 10 });
      expect(key1).toBe(key2);
    });

    it('should generate different keys for different commands', () => {
      const key1 = CommandCache.generateKey('/review show');
      const key2 = CommandCache.generateKey('/review complete');
      expect(key1).not.toBe(key2);
    });

    it('should generate different keys for different options', () => {
      const key1 = CommandCache.generateKey('/review show', { limit: 10 });
      const key2 = CommandCache.generateKey('/review show', { limit: 20 });
      expect(key1).not.toBe(key2);
    });

    it('should handle undefined options', () => {
      const key = CommandCache.generateKey('/review show');
      expect(key).toBeDefined();
      expect(typeof key).toBe('string');
    });
  });

  describe('Memory Limits', () => {
    it('should evict oldest items when limit reached', async () => {
      // Create cache with small limit (testing eviction)
      const smallCache = new CommandCache({ defaultTtl: 60000 });

      // Add many items
      for (let i = 0; i < 150; i++) {
        await smallCache.set(`key-${i}`, `value-${i}`);
      }

      // First items should be evicted
      const stats = smallCache.getStats();
      expect(stats.itemCount).toBeLessThanOrEqual(100);

      await smallCache.close();
    });
  });

  describe('Type Safety', () => {
    it('should preserve type information', async () => {
      interface TestData {
        name: string;
        count: number;
      }

      const data: TestData = { name: 'test', count: 42 };
      await cache.set('typed-key', data);

      const result = await cache.get<TestData>('typed-key');
      expect(result?.name).toBe('test');
      expect(result?.count).toBe(42);
    });

    it('should handle arrays', async () => {
      const data = [1, 2, 3, 4, 5];
      await cache.set('array-key', data);

      const result = await cache.get<number[]>('array-key');
      expect(result).toEqual(data);
    });
  });
});
