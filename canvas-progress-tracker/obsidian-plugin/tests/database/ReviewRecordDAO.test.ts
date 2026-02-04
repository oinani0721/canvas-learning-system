/**
 * ReviewRecordDAO Unit Tests - Canvas Learning System
 *
 * Tests for Story 32.4: Dashboard统计补全
 * - getReviewCountByConceptId(): 获取概念复习次数
 * - calculateStreakDays(): 计算连续复习天数
 * - getReviewCountBatch(): 批量查询复习次数
 *
 * @module ReviewRecordDAO.test
 * @version 1.0.0
 */

import { ReviewRecordDAO } from '../../src/database/ReviewRecordDAO';
import type { ReviewRecord } from '../../src/types/DataTypes';

// Helper to create mock review records
const createMockReviewRecord = (overrides: Partial<ReviewRecord> = {}): ReviewRecord => ({
    id: Math.floor(Math.random() * 10000),
    canvasId: 'test-canvas.canvas',
    conceptId: 'concept-1',
    reviewDate: new Date(),
    nextReviewDate: new Date(Date.now() + 24 * 60 * 60 * 1000),
    status: 'completed',
    reviewScore: 80,
    memoryStrength: 0.7,
    retentionRate: 0.8,
    difficultyLevel: 'medium',
    ...overrides,
});

// Mock DatabaseManager
const createMockDbManager = (records: ReviewRecord[] = []) => ({
    findAll: jest.fn().mockResolvedValue(records),
    find: jest.fn().mockImplementation((table: string, query: any) => {
        if (query?.where?.id) {
            return Promise.resolve(records.find(r => r.id === query.where.id) || null);
        }
        return Promise.resolve(records[0] || null);
    }),
    insert: jest.fn().mockResolvedValue({ id: records.length + 1 }),
    update: jest.fn().mockResolvedValue(true),
    delete: jest.fn().mockResolvedValue(true),
    query: jest.fn().mockResolvedValue(records),
    isConnected: jest.fn().mockReturnValue(true),
});

describe('ReviewRecordDAO - Story 32.4', () => {
    describe('getReviewCountByConceptId', () => {
        it('should return 0 for concept with no reviews', async () => {
            const mockDb = createMockDbManager([]);
            const dao = new ReviewRecordDAO(mockDb as any);

            const count = await dao.getReviewCountByConceptId('non-existent-concept');
            expect(count).toBe(0);
        });

        it('should return correct count for concept with single review', async () => {
            const records = [
                createMockReviewRecord({ conceptId: 'concept-1' }),
            ];
            const mockDb = createMockDbManager(records);
            const dao = new ReviewRecordDAO(mockDb as any);

            const count = await dao.getReviewCountByConceptId('concept-1');
            expect(count).toBe(1);
        });

        it('should return correct count for concept with multiple reviews', async () => {
            const records = [
                createMockReviewRecord({ conceptId: 'concept-1', reviewDate: new Date('2024-01-01') }),
                createMockReviewRecord({ conceptId: 'concept-1', reviewDate: new Date('2024-01-02') }),
                createMockReviewRecord({ conceptId: 'concept-1', reviewDate: new Date('2024-01-03') }),
                createMockReviewRecord({ conceptId: 'concept-2', reviewDate: new Date('2024-01-01') }),
            ];
            const mockDb = createMockDbManager(records);
            const dao = new ReviewRecordDAO(mockDb as any);

            const count = await dao.getReviewCountByConceptId('concept-1');
            expect(count).toBe(3);
        });

        it('should not count reviews from other concepts', async () => {
            const records = [
                createMockReviewRecord({ conceptId: 'concept-1' }),
                createMockReviewRecord({ conceptId: 'concept-2' }),
                createMockReviewRecord({ conceptId: 'concept-2' }),
            ];
            const mockDb = createMockDbManager(records);
            const dao = new ReviewRecordDAO(mockDb as any);

            const count = await dao.getReviewCountByConceptId('concept-1');
            expect(count).toBe(1);
        });

        it('should handle empty conceptId gracefully', async () => {
            const records = [createMockReviewRecord({ conceptId: 'concept-1' })];
            const mockDb = createMockDbManager(records);
            const dao = new ReviewRecordDAO(mockDb as any);

            const count = await dao.getReviewCountByConceptId('');
            expect(count).toBe(0);
        });
    });

    describe('calculateStreakDays', () => {
        it('should return 0 when no reviews exist', async () => {
            const mockDb = createMockDbManager([]);
            const dao = new ReviewRecordDAO(mockDb as any);

            const streak = await dao.calculateStreakDays();
            expect(streak).toBe(0);
        });

        it('should return 1 when only today has reviews', async () => {
            const today = new Date();
            const records = [
                createMockReviewRecord({ reviewDate: today }),
            ];
            const mockDb = createMockDbManager(records);
            const dao = new ReviewRecordDAO(mockDb as any);

            const streak = await dao.calculateStreakDays();
            expect(streak).toBe(1);
        });

        it('should return correct streak for consecutive days', async () => {
            const today = new Date();
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);
            const twoDaysAgo = new Date(today);
            twoDaysAgo.setDate(twoDaysAgo.getDate() - 2);

            const records = [
                createMockReviewRecord({ reviewDate: today }),
                createMockReviewRecord({ reviewDate: yesterday }),
                createMockReviewRecord({ reviewDate: twoDaysAgo }),
            ];
            const mockDb = createMockDbManager(records);
            const dao = new ReviewRecordDAO(mockDb as any);

            const streak = await dao.calculateStreakDays();
            expect(streak).toBe(3);
        });

        it('should break streak when a day is missed', async () => {
            const today = new Date();
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);
            // Skip 2 days ago
            const threeDaysAgo = new Date(today);
            threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);

            const records = [
                createMockReviewRecord({ reviewDate: today }),
                createMockReviewRecord({ reviewDate: yesterday }),
                createMockReviewRecord({ reviewDate: threeDaysAgo }),
            ];
            const mockDb = createMockDbManager(records);
            const dao = new ReviewRecordDAO(mockDb as any);

            const streak = await dao.calculateStreakDays();
            expect(streak).toBe(2); // Only today + yesterday count
        });

        it('should handle multiple reviews on same day', async () => {
            const today = new Date();
            const records = [
                createMockReviewRecord({ reviewDate: today, conceptId: 'concept-1' }),
                createMockReviewRecord({ reviewDate: today, conceptId: 'concept-2' }),
                createMockReviewRecord({ reviewDate: today, conceptId: 'concept-3' }),
            ];
            const mockDb = createMockDbManager(records);
            const dao = new ReviewRecordDAO(mockDb as any);

            const streak = await dao.calculateStreakDays();
            expect(streak).toBe(1); // Still just 1 day
        });

        it('should return 0 if no review today', async () => {
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);

            const records = [
                createMockReviewRecord({ reviewDate: yesterday }),
            ];
            const mockDb = createMockDbManager(records);
            const dao = new ReviewRecordDAO(mockDb as any);

            const streak = await dao.calculateStreakDays();
            expect(streak).toBe(0); // Streak broken - no review today
        });

        it('should handle records without reviewDate', async () => {
            const today = new Date();
            const records = [
                createMockReviewRecord({ reviewDate: today }),
                { ...createMockReviewRecord(), reviewDate: undefined as any },
            ];
            const mockDb = createMockDbManager(records);
            const dao = new ReviewRecordDAO(mockDb as any);

            const streak = await dao.calculateStreakDays();
            expect(streak).toBe(1);
        });
    });

    describe('getReviewCountBatch', () => {
        it('should return correct counts for multiple concepts', async () => {
            const records = [
                createMockReviewRecord({ conceptId: 'c1' }),
                createMockReviewRecord({ conceptId: 'c1' }),
                createMockReviewRecord({ conceptId: 'c2' }),
                createMockReviewRecord({ conceptId: 'c3' }),
                createMockReviewRecord({ conceptId: 'c3' }),
                createMockReviewRecord({ conceptId: 'c3' }),
            ];
            const mockDb = createMockDbManager(records);
            const dao = new ReviewRecordDAO(mockDb as any);

            const counts = await dao.getReviewCountBatch(['c1', 'c2', 'c3', 'c4']);

            expect(counts.get('c1')).toBe(2);
            expect(counts.get('c2')).toBe(1);
            expect(counts.get('c3')).toBe(3);
            expect(counts.get('c4')).toBe(0); // Not in records
        });

        it('should return 0 for concepts not in database', async () => {
            const mockDb = createMockDbManager([]);
            const dao = new ReviewRecordDAO(mockDb as any);

            const counts = await dao.getReviewCountBatch(['c1', 'c2']);

            expect(counts.get('c1')).toBe(0);
            expect(counts.get('c2')).toBe(0);
        });

        it('should handle empty conceptIds array', async () => {
            const records = [createMockReviewRecord({ conceptId: 'c1' })];
            const mockDb = createMockDbManager(records);
            const dao = new ReviewRecordDAO(mockDb as any);

            const counts = await dao.getReviewCountBatch([]);

            expect(counts.size).toBe(0);
        });

        it('should only count concepts in the requested list', async () => {
            const records = [
                createMockReviewRecord({ conceptId: 'c1' }),
                createMockReviewRecord({ conceptId: 'c2' }),
                createMockReviewRecord({ conceptId: 'c3' }),
            ];
            const mockDb = createMockDbManager(records);
            const dao = new ReviewRecordDAO(mockDb as any);

            const counts = await dao.getReviewCountBatch(['c1']); // Only request c1

            expect(counts.get('c1')).toBe(1);
            expect(counts.has('c2')).toBe(false); // c2 not requested
            expect(counts.has('c3')).toBe(false); // c3 not requested
        });
    });

    // =========================================================================
    // Story 32.4 QA Improvement: Streak Cache Tests
    // Added by: Quinn (Test Architect)
    // =========================================================================
    describe('calculateStreakDays - Cache Mechanism', () => {
        it('should use cached value on subsequent calls within TTL', async () => {
            const today = new Date();
            const records = [
                createMockReviewRecord({ reviewDate: today }),
            ];
            const mockDb = createMockDbManager(records);
            const dao = new ReviewRecordDAO(mockDb as any);

            // First call - should query database
            const streak1 = await dao.calculateStreakDays();
            expect(streak1).toBe(1);

            // Second call - should use cache (findAll not called again)
            const streak2 = await dao.calculateStreakDays();
            expect(streak2).toBe(1);

            // Verify findAll was only called once (cache hit on second call)
            expect(mockDb.findAll).toHaveBeenCalledTimes(1);
        });

        it('should invalidate cache after create operation', async () => {
            const today = new Date();
            const records = [
                createMockReviewRecord({ reviewDate: today }),
            ];
            const mockDb = createMockDbManager(records);
            // Mock insert to simulate successful create
            mockDb.insert = jest.fn().mockResolvedValue({ id: 2 });
            const dao = new ReviewRecordDAO(mockDb as any);

            // First call - populate cache
            await dao.calculateStreakDays();
            expect(mockDb.findAll).toHaveBeenCalledTimes(1);

            // Create new record - should invalidate cache
            await dao.create({
                canvasId: 'test.canvas',
                conceptId: 'concept-new',
                reviewDate: today,
                nextReviewDate: new Date(),
                status: 'completed',
                memoryStrength: 0.5,
                retentionRate: 0.6,
                reviewDuration: 60,
            } as any);

            // Next calculateStreakDays call should hit database again
            await dao.calculateStreakDays();
            expect(mockDb.findAll).toHaveBeenCalledTimes(2);
        });

        it('should invalidate cache after update operation', async () => {
            const today = new Date();
            const records = [
                createMockReviewRecord({ id: 1, reviewDate: today }),
            ];
            const mockDb = createMockDbManager(records);
            mockDb.update = jest.fn().mockResolvedValue({ id: 1 });
            const dao = new ReviewRecordDAO(mockDb as any);

            // First call - populate cache
            await dao.calculateStreakDays();
            expect(mockDb.findAll).toHaveBeenCalledTimes(1);

            // Update record - should invalidate cache
            await dao.update(1, { memoryStrength: 0.9 });

            // Next calculateStreakDays call should hit database again
            await dao.calculateStreakDays();
            expect(mockDb.findAll).toHaveBeenCalledTimes(2);
        });

        it('should invalidate cache after delete operation', async () => {
            const today = new Date();
            const records = [
                createMockReviewRecord({ id: 1, reviewDate: today }),
            ];
            const mockDb = createMockDbManager(records);
            mockDb.delete = jest.fn().mockResolvedValue(true);
            const dao = new ReviewRecordDAO(mockDb as any);

            // First call - populate cache
            await dao.calculateStreakDays();
            expect(mockDb.findAll).toHaveBeenCalledTimes(1);

            // Delete record - should invalidate cache
            await dao.delete(1);

            // Next calculateStreakDays call should hit database again
            await dao.calculateStreakDays();
            expect(mockDb.findAll).toHaveBeenCalledTimes(2);
        });

        it('should cache zero value correctly', async () => {
            const mockDb = createMockDbManager([]);
            const dao = new ReviewRecordDAO(mockDb as any);

            // First call - should return 0 and cache it
            const streak1 = await dao.calculateStreakDays();
            expect(streak1).toBe(0);

            // Second call - should use cached 0
            const streak2 = await dao.calculateStreakDays();
            expect(streak2).toBe(0);

            // Verify findAll only called once
            expect(mockDb.findAll).toHaveBeenCalledTimes(1);
        });
    });
});
