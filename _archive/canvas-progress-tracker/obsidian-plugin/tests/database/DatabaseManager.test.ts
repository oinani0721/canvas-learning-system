/**
 * DatabaseManager Unit Tests - Canvas Learning System
 *
 * Tests for the DatabaseManager class.
 * Implements Story 14.1: SQLite数据库集成
 *
 * @module DatabaseManager.test
 * @version 1.0.0
 */

import { DatabaseManager } from '../../src/database/DatabaseManager';
import { DEFAULT_DATABASE_CONFIG } from '../../src/types/DataTypes';

// Mock Obsidian App
const mockAdapter = {
    read: jest.fn(),
    write: jest.fn(),
    exists: jest.fn(),
    mkdir: jest.fn(),
    remove: jest.fn(),
    stat: jest.fn(),
    list: jest.fn(),
};

const mockApp = {
    vault: {
        adapter: mockAdapter,
    },
} as any;

describe('DatabaseManager', () => {
    let dbManager: DatabaseManager;

    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
        dbManager = new DatabaseManager(mockApp, DEFAULT_DATABASE_CONFIG);

        // Default mock implementations
        mockAdapter.exists.mockResolvedValue(false);
        mockAdapter.mkdir.mockResolvedValue(undefined);
        mockAdapter.write.mockResolvedValue(undefined);
        mockAdapter.read.mockResolvedValue('{}');
    });

    afterEach(async () => {
        jest.useRealTimers();
        if (dbManager.isConnected()) {
            await dbManager.close();
        }
    });

    describe('initialization', () => {
        it('should initialize database successfully', async () => {
            await dbManager.initialize();
            expect(dbManager.isConnected()).toBe(true);
        });

        it('should create directory if not exists', async () => {
            mockAdapter.exists.mockResolvedValue(false);
            await dbManager.initialize();
            expect(mockAdapter.mkdir).toHaveBeenCalled();
        });

        it('should load existing data if file exists', async () => {
            // Existing database with table and records
            const existingData = {
                version: 1,
                tables: {
                    test_table: {
                        name: 'test_table',
                        records: [{ id: 1, name: 'test' }],
                        autoIncrement: 2,
                        indexes: {},
                    },
                },
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
            };
            mockAdapter.exists.mockResolvedValue(true);
            mockAdapter.read.mockResolvedValue(JSON.stringify(existingData));

            await dbManager.initialize();

            const result = await dbManager.findAll('test_table');
            expect(result).toHaveLength(1);
        });
    });

    describe('CRUD operations', () => {
        beforeEach(async () => {
            await dbManager.initialize();
            await dbManager.createTable('users', ['email']);
        });

        it('should create a table', async () => {
            await dbManager.createTable('products', ['sku']);
            // Table creation is implicit, just verify no error
            expect(true).toBe(true);
        });

        it('should insert a record', async () => {
            const record = { name: 'John', email: 'john@example.com' };
            const result = await dbManager.insert('users', record);

            expect(result).toHaveProperty('id');
            expect(result.name).toBe('John');
            expect(result.email).toBe('john@example.com');
        });

        it('should find a record by ID', async () => {
            const record = { name: 'John', email: 'john@example.com' };
            const inserted = await dbManager.insert('users', record);

            const found = await dbManager.findById('users', inserted.id);
            expect(found).not.toBeNull();
            expect(found?.name).toBe('John');
        });

        it('should return null for non-existent ID', async () => {
            const found = await dbManager.findById('users', 9999);
            expect(found).toBeNull();
        });

        it('should find all records', async () => {
            await dbManager.insert('users', { name: 'John' });
            await dbManager.insert('users', { name: 'Jane' });

            const all = await dbManager.findAll('users');
            expect(all).toHaveLength(2);
        });

        it('should find records with where clause', async () => {
            await dbManager.insert('users', { name: 'John', active: true });
            await dbManager.insert('users', { name: 'Jane', active: false });

            const active = await dbManager.findAll('users', { where: { active: true } });
            expect(active).toHaveLength(1);
            expect(active[0].name).toBe('John');
        });

        it('should update a record', async () => {
            const inserted = await dbManager.insert('users', { name: 'John' });
            const updated = await dbManager.update('users', inserted.id, { name: 'Johnny' });

            expect(updated).not.toBeNull();
            expect(updated?.name).toBe('Johnny');
        });

        it('should delete a record', async () => {
            const inserted = await dbManager.insert('users', { name: 'John' });
            const deleted = await dbManager.delete('users', inserted.id);

            expect(deleted).toBe(true);

            const found = await dbManager.findById('users', inserted.id);
            expect(found).toBeNull();
        });

        it('should return false when deleting non-existent record', async () => {
            const deleted = await dbManager.delete('users', 9999);
            expect(deleted).toBe(false);
        });
    });

    describe('transactions', () => {
        beforeEach(async () => {
            await dbManager.initialize();
            await dbManager.createTable('users', ['email']);
        });

        it('should commit transaction successfully', async () => {
            dbManager.beginTransaction();

            await dbManager.insert('users', { name: 'John' });
            await dbManager.insert('users', { name: 'Jane' });

            await dbManager.commitTransaction();

            const all = await dbManager.findAll('users');
            expect(all).toHaveLength(2);
        });

        it('should rollback transaction', async () => {
            // Insert a record before transaction
            await dbManager.insert('users', { name: 'Existing' });

            dbManager.beginTransaction();
            await dbManager.insert('users', { name: 'John' });

            await dbManager.rollbackTransaction();

            const all = await dbManager.findAll('users');
            expect(all).toHaveLength(1);
            expect(all[0].name).toBe('Existing');
        });
    });

    describe('query options', () => {
        beforeEach(async () => {
            await dbManager.initialize();
            await dbManager.createTable('users', ['email']);
            await dbManager.insert('users', { name: 'Alice', age: 30 });
            await dbManager.insert('users', { name: 'Bob', age: 25 });
            await dbManager.insert('users', { name: 'Charlie', age: 35 });
        });

        it('should limit results', async () => {
            const results = await dbManager.findAll('users', { limit: 2 });
            expect(results).toHaveLength(2);
        });

        it('should skip results with offset', async () => {
            const results = await dbManager.findAll('users', { offset: 1 });
            expect(results).toHaveLength(2);
        });

        it('should order results ascending', async () => {
            const results = await dbManager.findAll('users', {
                orderBy: 'age',
                orderDirection: 'ASC',
            });
            expect(results[0].name).toBe('Bob');
            expect(results[2].name).toBe('Charlie');
        });

        it('should order results descending', async () => {
            const results = await dbManager.findAll('users', {
                orderBy: 'age',
                orderDirection: 'DESC',
            });
            expect(results[0].name).toBe('Charlie');
            expect(results[2].name).toBe('Bob');
        });
    });

    describe('persistence', () => {
        it('should flush data to storage', async () => {
            await dbManager.initialize();
            await dbManager.createTable('users', ['email']);
            await dbManager.insert('users', { name: 'John' });

            await dbManager.flush();

            expect(mockAdapter.write).toHaveBeenCalled();
            const writeCall = mockAdapter.write.mock.calls[mockAdapter.write.mock.calls.length - 1];
            const writtenData = JSON.parse(writeCall[1]);
            // Database structure is { tables: { users: { records: [...] } } }
            expect(writtenData.tables.users.records).toHaveLength(1);
        });

        it('should close database properly', async () => {
            await dbManager.initialize();
            await dbManager.createTable('users', ['email']);
            await dbManager.insert('users', { name: 'John' });

            await dbManager.close();

            expect(dbManager.isConnected()).toBe(false);
            expect(mockAdapter.write).toHaveBeenCalled();
        });
    });

    describe('table operations', () => {
        beforeEach(async () => {
            await dbManager.initialize();
            await dbManager.createTable('users', ['email']);
        });

        it('should drop a table', async () => {
            await dbManager.insert('users', { name: 'John' });

            await dbManager.dropTable('users');

            // After dropping, accessing the table should throw
            await expect(dbManager.findAll('users')).rejects.toThrow('does not exist');
        });

        it('should count records in a table', async () => {
            await dbManager.insert('users', { name: 'John' });
            await dbManager.insert('users', { name: 'Jane' });

            const count = await dbManager.count('users');
            expect(count).toBe(2);
        });

        it('should count records with filter', async () => {
            await dbManager.insert('users', { name: 'John', active: true });
            await dbManager.insert('users', { name: 'Jane', active: false });

            const count = await dbManager.count('users', { active: true });
            expect(count).toBe(1);
        });
    });
});
