/**
 * Database Manager - Canvas Learning System
 *
 * Manages SQLite-like database operations using Obsidian's FileSystem APIs.
 * Implements Story 14.1: SQLite数据库集成
 *
 * Since Obsidian plugins run in an Electron/browser context, we implement
 * a JSON-based storage layer that provides ACID-like guarantees through
 * careful file handling and transaction management.
 *
 * @module DatabaseManager
 * @version 1.0.0
 *
 * Source: Story 14.1 Dev Notes - DatabaseManager类
 */

import { App, TFile, TFolder } from 'obsidian';
import {
    DatabaseConfig,
    DEFAULT_DATABASE_CONFIG,
    DatabaseError,
    DatabaseEvent,
    DatabaseEventHandler,
} from '../types/DataTypes';

/**
 * Database table structure stored in JSON
 */
interface DatabaseTable<T = any> {
    name: string;
    records: T[];
    autoIncrement: number;
    indexes: Record<string, Record<string, number[]>>;
}

/**
 * Database structure
 */
interface DatabaseStructure {
    version: number;
    tables: Record<string, DatabaseTable>;
    createdAt: string;
    updatedAt: string;
}

/**
 * Transaction operation
 */
interface TransactionOperation {
    type: 'insert' | 'update' | 'delete';
    table: string;
    data?: any;
    id?: number;
}

/**
 * Database Manager - Manages SQLite-like operations
 *
 * Provides:
 * - CRUD operations
 * - Transaction support
 * - Auto-increment IDs
 * - Basic indexing
 * - Persistence via Obsidian's FileSystem
 *
 * ✅ Verified from Story 14.1 Dev Notes: DatabaseManager类实现
 */
export class DatabaseManager {
    private app: App;
    private config: DatabaseConfig;
    private db: DatabaseStructure | null = null;
    private isInitialized: boolean = false;
    private isDirty: boolean = false;
    private eventHandlers: DatabaseEventHandler[] = [];
    private saveTimeout: NodeJS.Timeout | null = null;
    private transactionStack: TransactionOperation[][] = [];

    constructor(app: App, config: Partial<DatabaseConfig> = {}) {
        this.app = app;
        this.config = { ...DEFAULT_DATABASE_CONFIG, ...config };
    }

    /**
     * Initialize the database
     */
    async initialize(): Promise<void> {
        if (this.isInitialized) {
            return;
        }

        try {
            // Ensure data directory exists
            await this.ensureDataDirectory();

            // Load or create database
            await this.loadOrCreateDatabase();

            this.isInitialized = true;
            this.emit('connected');
            console.log('DatabaseManager: Initialized successfully');
        } catch (error) {
            console.error('DatabaseManager: Initialization failed', error);
            throw new DatabaseError(
                'Database initialization failed',
                'CONNECTION_ERROR',
                error as Error
            );
        }
    }

    /**
     * Close the database connection
     */
    async close(): Promise<void> {
        if (!this.isInitialized) {
            return;
        }

        try {
            // Flush any pending writes
            await this.flush();

            // Clear state
            this.db = null;
            this.isInitialized = false;
            this.emit('disconnected');
            console.log('DatabaseManager: Closed');
        } catch (error) {
            console.error('DatabaseManager: Close failed', error);
            throw new DatabaseError(
                'Database close failed',
                'CONNECTION_ERROR',
                error as Error
            );
        }
    }

    /**
     * Check if database is connected/initialized
     */
    isConnected(): boolean {
        return this.isInitialized;
    }

    /**
     * Create a table if it doesn't exist
     */
    async createTable(tableName: string, indexes: string[] = []): Promise<void> {
        this.ensureInitialized();

        if (this.db!.tables[tableName]) {
            return; // Table already exists
        }

        this.db!.tables[tableName] = {
            name: tableName,
            records: [],
            autoIncrement: 1,
            indexes: {},
        };

        // Create indexes
        for (const indexField of indexes) {
            this.db!.tables[tableName].indexes[indexField] = {};
        }

        await this.markDirty();
    }

    /**
     * Drop a table
     */
    async dropTable(tableName: string): Promise<void> {
        this.ensureInitialized();

        if (!this.db!.tables[tableName]) {
            return;
        }

        delete this.db!.tables[tableName];
        await this.markDirty();
    }

    /**
     * Insert a record into a table
     */
    async insert<T extends { id?: number }>(
        tableName: string,
        record: Omit<T, 'id'>
    ): Promise<T> {
        this.ensureInitialized();

        const table = this.getTable(tableName);
        const id = table.autoIncrement++;
        const timestamp = new Date().toISOString();

        const newRecord = {
            ...record,
            id,
            createdAt: timestamp,
            updatedAt: timestamp,
        } as unknown as T;

        table.records.push(newRecord);

        // Update indexes
        this.updateIndexes(tableName, newRecord, 'add');

        // Track for transaction
        if (this.isInTransaction()) {
            this.currentTransaction().push({
                type: 'insert',
                table: tableName,
                data: newRecord,
            });
        }

        await this.markDirty();
        return newRecord;
    }

    /**
     * Insert multiple records
     */
    async insertMany<T extends { id?: number }>(
        tableName: string,
        records: Omit<T, 'id'>[]
    ): Promise<T[]> {
        const results: T[] = [];
        for (const record of records) {
            results.push(await this.insert<T>(tableName, record));
        }
        return results;
    }

    /**
     * Find a record by ID
     */
    async findById<T>(tableName: string, id: number): Promise<T | null> {
        this.ensureInitialized();

        const table = this.getTable(tableName);
        const record = table.records.find((r: any) => r.id === id);
        return record ? this.parseRecord<T>(record) : null;
    }

    /**
     * Find all records matching criteria
     */
    async findAll<T>(
        tableName: string,
        options?: {
            where?: Partial<T>;
            orderBy?: keyof T;
            orderDirection?: 'ASC' | 'DESC';
            limit?: number;
            offset?: number;
        }
    ): Promise<T[]> {
        this.ensureInitialized();

        const table = this.getTable(tableName);
        let results = [...table.records];

        // Filter by where clause
        if (options?.where) {
            results = results.filter((record) =>
                Object.entries(options.where!).every(
                    ([key, value]) => record[key] === value
                )
            );
        }

        // Sort results
        if (options?.orderBy) {
            const direction = options.orderDirection === 'DESC' ? -1 : 1;
            results.sort((a, b) => {
                const aVal = a[options.orderBy as string];
                const bVal = b[options.orderBy as string];
                if (aVal < bVal) return -1 * direction;
                if (aVal > bVal) return 1 * direction;
                return 0;
            });
        }

        // Apply pagination
        if (options?.offset !== undefined) {
            results = results.slice(options.offset);
        }
        if (options?.limit !== undefined) {
            results = results.slice(0, options.limit);
        }

        return results.map((r) => this.parseRecord<T>(r));
    }

    /**
     * Find records using a custom filter function
     */
    async findWhere<T>(
        tableName: string,
        predicate: (record: T) => boolean
    ): Promise<T[]> {
        this.ensureInitialized();

        const table = this.getTable(tableName);
        const results = table.records
            .map((r: any) => this.parseRecord<T>(r))
            .filter(predicate);
        return results;
    }

    /**
     * Count records
     */
    async count(tableName: string, where?: Record<string, any>): Promise<number> {
        this.ensureInitialized();

        const table = this.getTable(tableName);
        if (!where) {
            return table.records.length;
        }

        return table.records.filter((record: any) =>
            Object.entries(where).every(([key, value]) => record[key] === value)
        ).length;
    }

    /**
     * Update a record by ID
     */
    async update<T extends { id?: number }>(
        tableName: string,
        id: number,
        updates: Partial<T>
    ): Promise<T | null> {
        this.ensureInitialized();

        const table = this.getTable(tableName);
        const index = table.records.findIndex((r: any) => r.id === id);

        if (index === -1) {
            return null;
        }

        const oldRecord = table.records[index];
        const updatedRecord = {
            ...oldRecord,
            ...updates,
            id, // Ensure ID doesn't change
            updatedAt: new Date().toISOString(),
        };

        // Update indexes
        this.updateIndexes(tableName, oldRecord, 'remove');
        table.records[index] = updatedRecord;
        this.updateIndexes(tableName, updatedRecord, 'add');

        // Track for transaction
        if (this.isInTransaction()) {
            this.currentTransaction().push({
                type: 'update',
                table: tableName,
                data: { old: oldRecord, new: updatedRecord },
                id,
            });
        }

        await this.markDirty();
        return this.parseRecord<T>(updatedRecord);
    }

    /**
     * Delete a record by ID
     */
    async delete(tableName: string, id: number): Promise<boolean> {
        this.ensureInitialized();

        const table = this.getTable(tableName);
        const index = table.records.findIndex((r: any) => r.id === id);

        if (index === -1) {
            return false;
        }

        const deletedRecord = table.records[index];

        // Update indexes
        this.updateIndexes(tableName, deletedRecord, 'remove');
        table.records.splice(index, 1);

        // Track for transaction
        if (this.isInTransaction()) {
            this.currentTransaction().push({
                type: 'delete',
                table: tableName,
                data: deletedRecord,
                id,
            });
        }

        await this.markDirty();
        return true;
    }

    /**
     * Delete multiple records matching criteria
     */
    async deleteWhere(tableName: string, where: Record<string, any>): Promise<number> {
        this.ensureInitialized();

        const table = this.getTable(tableName);
        const toDelete = table.records.filter((record: any) =>
            Object.entries(where).every(([key, value]) => record[key] === value)
        );

        for (const record of toDelete) {
            await this.delete(tableName, record.id);
        }

        return toDelete.length;
    }

    /**
     * Begin a transaction
     */
    beginTransaction(): void {
        this.ensureInitialized();
        this.transactionStack.push([]);
    }

    /**
     * Commit the current transaction
     */
    async commitTransaction(): Promise<void> {
        this.ensureInitialized();

        if (!this.isInTransaction()) {
            throw new DatabaseError('No active transaction', 'TRANSACTION_ERROR');
        }

        this.transactionStack.pop();
        await this.flush();
    }

    /**
     * Rollback the current transaction
     */
    async rollbackTransaction(): Promise<void> {
        this.ensureInitialized();

        if (!this.isInTransaction()) {
            throw new DatabaseError('No active transaction', 'TRANSACTION_ERROR');
        }

        const operations = this.transactionStack.pop()!;

        // Reverse operations in reverse order
        for (let i = operations.length - 1; i >= 0; i--) {
            const op = operations[i];
            const table = this.db!.tables[op.table];

            switch (op.type) {
                case 'insert':
                    // Remove inserted record
                    const insertIndex = table.records.findIndex(
                        (r: any) => r.id === op.data.id
                    );
                    if (insertIndex !== -1) {
                        this.updateIndexes(op.table, table.records[insertIndex], 'remove');
                        table.records.splice(insertIndex, 1);
                    }
                    table.autoIncrement--;
                    break;

                case 'update':
                    // Restore old record
                    const updateIndex = table.records.findIndex(
                        (r: any) => r.id === op.id
                    );
                    if (updateIndex !== -1) {
                        this.updateIndexes(op.table, table.records[updateIndex], 'remove');
                        table.records[updateIndex] = op.data.old;
                        this.updateIndexes(op.table, op.data.old, 'add');
                    }
                    break;

                case 'delete':
                    // Restore deleted record
                    table.records.push(op.data);
                    this.updateIndexes(op.table, op.data, 'add');
                    break;
            }
        }

        await this.markDirty();
    }

    /**
     * Execute raw query (limited support for SELECT)
     */
    async query<T>(
        tableName: string,
        queryFn: (records: any[]) => any[]
    ): Promise<T[]> {
        this.ensureInitialized();

        const table = this.getTable(tableName);
        const results = queryFn([...table.records]);
        return results.map((r) => this.parseRecord<T>(r));
    }

    /**
     * Get database statistics
     */
    getStats(): { tables: number; totalRecords: number; version: number } {
        this.ensureInitialized();

        const tables = Object.keys(this.db!.tables).length;
        const totalRecords = Object.values(this.db!.tables).reduce(
            (sum, table) => sum + table.records.length,
            0
        );

        return {
            tables,
            totalRecords,
            version: this.db!.version,
        };
    }

    /**
     * Register event handler
     */
    on(handler: DatabaseEventHandler): void {
        this.eventHandlers.push(handler);
    }

    /**
     * Remove event handler
     */
    off(handler: DatabaseEventHandler): void {
        const index = this.eventHandlers.indexOf(handler);
        if (index !== -1) {
            this.eventHandlers.splice(index, 1);
        }
    }

    /**
     * Flush pending changes to disk
     */
    async flush(): Promise<void> {
        if (!this.isDirty || !this.db) {
            return;
        }

        try {
            this.db.updatedAt = new Date().toISOString();
            const data = JSON.stringify(this.db, null, 2);
            const filePath = this.getDbFilePath();

            // Write to file
            await this.app.vault.adapter.write(filePath, data);

            this.isDirty = false;
            console.log('DatabaseManager: Flushed to disk');
        } catch (error) {
            console.error('DatabaseManager: Flush failed', error);
            throw new DatabaseError(
                'Failed to save database',
                'QUERY_ERROR',
                error as Error
            );
        }
    }

    /**
     * Export database as JSON
     */
    async exportToJson(): Promise<string> {
        this.ensureInitialized();
        return JSON.stringify(this.db, null, 2);
    }

    /**
     * Import database from JSON
     */
    async importFromJson(json: string): Promise<void> {
        this.ensureInitialized();

        try {
            const data = JSON.parse(json) as DatabaseStructure;

            // Validate structure
            if (!data.version || !data.tables) {
                throw new Error('Invalid database structure');
            }

            this.db = data;
            await this.markDirty();
            await this.flush();
        } catch (error) {
            throw new DatabaseError(
                'Import failed',
                'VALIDATION_ERROR',
                error as Error
            );
        }
    }

    // =========================================================================
    // Private Methods
    // =========================================================================

    private getDbFilePath(): string {
        return `${this.app.vault.configDir}/${this.config.path}`;
    }

    private async ensureDataDirectory(): Promise<void> {
        const configDir = this.app.vault.configDir;
        if (!await this.app.vault.adapter.exists(configDir)) {
            await this.app.vault.adapter.mkdir(configDir);
        }
    }

    private async loadOrCreateDatabase(): Promise<void> {
        const filePath = this.getDbFilePath();

        if (await this.app.vault.adapter.exists(filePath)) {
            // Load existing database
            const data = await this.app.vault.adapter.read(filePath);
            this.db = JSON.parse(data) as DatabaseStructure;
            console.log('DatabaseManager: Loaded existing database');
        } else {
            // Create new database
            this.db = {
                version: 1,
                tables: {},
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
            };
            await this.flush();
            console.log('DatabaseManager: Created new database');
        }
    }

    private ensureInitialized(): void {
        if (!this.isInitialized || !this.db) {
            throw new DatabaseError('Database not initialized', 'CONNECTION_ERROR');
        }
    }

    private getTable(tableName: string): DatabaseTable {
        if (!this.db!.tables[tableName]) {
            throw new DatabaseError(
                `Table '${tableName}' does not exist`,
                'NOT_FOUND'
            );
        }
        return this.db!.tables[tableName];
    }

    private parseRecord<T>(record: any): T {
        const parsed = { ...record };

        // Convert date strings back to Date objects
        if (parsed.createdAt) {
            parsed.createdAt = new Date(parsed.createdAt);
        }
        if (parsed.updatedAt) {
            parsed.updatedAt = new Date(parsed.updatedAt);
        }
        if (parsed.reviewDate) {
            parsed.reviewDate = new Date(parsed.reviewDate);
        }
        if (parsed.nextReviewDate) {
            parsed.nextReviewDate = new Date(parsed.nextReviewDate);
        }
        if (parsed.startTime) {
            parsed.startTime = new Date(parsed.startTime);
        }
        if (parsed.endTime) {
            parsed.endTime = new Date(parsed.endTime);
        }
        if (parsed.statDate) {
            parsed.statDate = new Date(parsed.statDate);
        }

        return parsed as T;
    }

    private updateIndexes(
        tableName: string,
        record: any,
        action: 'add' | 'remove'
    ): void {
        const table = this.db!.tables[tableName];

        for (const [field, index] of Object.entries(table.indexes)) {
            const value = String(record[field]);

            if (action === 'add') {
                if (!index[value]) {
                    index[value] = [];
                }
                index[value].push(record.id);
            } else {
                if (index[value]) {
                    const pos = index[value].indexOf(record.id);
                    if (pos !== -1) {
                        index[value].splice(pos, 1);
                    }
                    if (index[value].length === 0) {
                        delete index[value];
                    }
                }
            }
        }
    }

    private isInTransaction(): boolean {
        return this.transactionStack.length > 0;
    }

    private currentTransaction(): TransactionOperation[] {
        return this.transactionStack[this.transactionStack.length - 1];
    }

    private async markDirty(): Promise<void> {
        this.isDirty = true;

        // Debounce saves
        if (this.saveTimeout) {
            clearTimeout(this.saveTimeout);
        }

        this.saveTimeout = setTimeout(async () => {
            await this.flush();
        }, 1000);
    }

    private emit(event: DatabaseEvent, data?: any): void {
        for (const handler of this.eventHandlers) {
            try {
                handler(event, data);
            } catch (error) {
                console.error('DatabaseManager: Event handler error', error);
            }
        }
    }
}
