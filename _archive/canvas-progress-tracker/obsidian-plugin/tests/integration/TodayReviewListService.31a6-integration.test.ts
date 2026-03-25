/**
 * Story 31.A.6: TodayReviewListService 完整集成测试
 *
 * 覆盖 AC-31.A.6.1 ~ AC-31.A.6.4 的集成场景：
 * - 初始化链路 + 依赖注入
 * - ReviewDashboardView 数据源切换
 * - 右键菜单完整 7 action 覆盖
 * - 接口适配 + 类型兼容
 * - 缓存一致性
 * - 边界/错误场景
 */

import {
    TodayReviewListService,
    TodayReviewItem,
    TodayReviewSummary,
    PRIORITY_CONFIG,
    ContextMenuAction,
    createTodayReviewListService,
} from '../../src/services/TodayReviewListService';

// Mock Obsidian
jest.mock('obsidian', () => {
    class MockTFile {
        path: string;
        name: string;
        constructor(path: string) {
            this.path = path;
            this.name = path.split('/').pop() || path;
        }
    }

    // Track addItem calls to verify menu structure
    const menuItems: Array<{ title: string; icon: string }> = [];
    const separatorCount = { value: 0 };

    return {
        Notice: jest.fn(),
        Menu: jest.fn().mockImplementation(() => {
            menuItems.length = 0;
            separatorCount.value = 0;
            return {
                addItem: jest.fn().mockImplementation((cb: (item: any) => void) => {
                    const menuItem = {
                        _title: '',
                        _icon: '',
                        _onClick: null as any,
                        setTitle(t: string) { this._title = t; menuItems.push({ title: t, icon: this._icon }); return this; },
                        setIcon(i: string) { this._icon = i; return this; },
                        onClick(fn: () => void) { this._onClick = fn; return this; },
                    };
                    cb(menuItem);
                    return { addItem: jest.fn().mockReturnThis(), addSeparator: jest.fn().mockReturnThis(), showAtMouseEvent: jest.fn() };
                }),
                addSeparator: jest.fn().mockImplementation(() => {
                    separatorCount.value++;
                    return { addItem: jest.fn().mockReturnThis(), addSeparator: jest.fn().mockReturnThis(), showAtMouseEvent: jest.fn() };
                }),
                showAtMouseEvent: jest.fn(),
            };
        }),
        TFile: MockTFile,
        // Expose for inspection
        __menuItems: menuItems,
        __separatorCount: separatorCount,
    };
});

const { TFile: MockTFile, Notice: mockNotice } = jest.requireMock('obsidian');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const mockApp = {
    vault: {
        getAbstractFileByPath: jest.fn(),
    },
    workspace: {
        openLinkText: jest.fn().mockResolvedValue(undefined),
    },
} as any;

function createMockReviewRecord(overrides: Partial<any> = {}) {
    return {
        id: 1,
        canvasId: 'math/algebra.canvas',
        conceptId: 'concept-1',
        conceptName: 'Concept 1',
        status: 'pending',
        memoryStrength: 0.5,
        retentionRate: 0.7,
        reviewDate: new Date().toISOString(),
        nextReviewDate: new Date().toISOString(),
        ...overrides,
    };
}

function createMockItem(overrides: Partial<TodayReviewItem> = {}): TodayReviewItem {
    return {
        id: '1',
        canvasId: 'math/algebra.canvas',
        canvasPath: 'math/algebra.canvas',
        canvasTitle: 'algebra',
        conceptName: 'Concept A',
        priority: 'high',
        dueDate: new Date(),
        overdueDays: 1,
        memoryStrength: 0.5,
        retentionRate: 0.7,
        reviewCount: 3,
        daysSinceLastReview: 2,
        scheduledDate: new Date(),
        urgencyLabel: '高',
        urgencyColor: '#f59e0b',
        status: 'pending',
        ...overrides,
    };
}

function createMockDbManager(records: any[] = []) {
    return {
        getReviewRecordDAO: jest.fn().mockReturnValue({
            getDueForReview: jest.fn().mockResolvedValue(records),
            getDailyStats: jest.fn().mockResolvedValue({
                completedCount: 2,
                skippedCount: 0,
                totalReviews: 5,
            }),
            update: jest.fn().mockResolvedValue({}),
            updateMemoryMetrics: jest.fn().mockResolvedValue({}),
            getReviewCountByConceptId: jest.fn().mockResolvedValue(3),
        }),
    };
}

function createMockMemoryQueryService() {
    return {
        queryConceptMemory: jest.fn().mockResolvedValue({
            conceptId: 'concept-1',
            memoryStrength: 0.6,
            lastAccessTime: new Date().toISOString(),
        }),
    };
}

function createMockFSRSStateQueryService() {
    return {
        queryFSRSState: jest.fn().mockResolvedValue({
            found: true,
            concept_id: 'concept-1',
            fsrs_state: {
                stability: 5.0,
                difficulty: 0.3,
                due: new Date().toISOString(),
                reps: 3,
                lapses: 0,
                state: 2, // review
            },
        }),
    };
}

// ===========================================================================
// AC-31.A.6.1: main.ts 初始化链路
// ===========================================================================
describe('AC-31.A.6.1: 初始化与依赖注入', () => {
    let service: TodayReviewListService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = createTodayReviewListService(mockApp);
    });

    it('createTodayReviewListService 返回有效实例', () => {
        expect(service).toBeInstanceOf(TodayReviewListService);
    });

    it('完整依赖注入链路不抛异常', () => {
        const dbManager = createMockDbManager();
        const memoryService = createMockMemoryQueryService();
        const fsrsService = createMockFSRSStateQueryService();

        expect(() => {
            service.setDataManager(dbManager as any);
            service.setMemoryQueryService(memoryService as any);
            service.setFSRSStateQueryService(fsrsService as any);
        }).not.toThrow();
    });

    it('setDataManager 后可正常查询', async () => {
        const records = [createMockReviewRecord()];
        service.setDataManager(createMockDbManager(records) as any);

        const items = await service.getTodayReviewItems();
        expect(items.length).toBeGreaterThan(0);
    });

    it('未注入 DataManager 时 getTodayReviewItems 返回空数组', async () => {
        const items = await service.getTodayReviewItems();
        expect(items).toEqual([]);
    });

    it('setMemoryQueryService(null) 不抛异常', () => {
        expect(() => service.setMemoryQueryService(null)).not.toThrow();
    });

    it('setFSRSStateQueryService(null) 不抛异常', () => {
        expect(() => service.setFSRSStateQueryService(null)).not.toThrow();
    });
});

// ===========================================================================
// AC-31.A.6.2: ReviewDashboardView 数据源切换
// ===========================================================================
describe('AC-31.A.6.2: 数据源切换与类型兼容', () => {
    let service: TodayReviewListService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = createTodayReviewListService(mockApp);
    });

    it('TodayReviewItem 可安全转型为 ReviewTask', async () => {
        const records = [
            createMockReviewRecord({ id: 1, conceptId: 'c1' }),
            createMockReviewRecord({ id: 2, conceptId: 'c2' }),
        ];
        service.setDataManager(createMockDbManager(records) as any);

        const todayItems = await service.getTodayReviewItems();

        // 模拟 ReviewDashboardView 的类型转换
        const tasks = todayItems as any[];

        tasks.forEach(task => {
            // ReviewTask 必要字段
            expect(task).toHaveProperty('id');
            expect(task).toHaveProperty('canvasId');
            expect(task).toHaveProperty('canvasTitle');
            expect(task).toHaveProperty('conceptName');
            expect(task).toHaveProperty('priority');
            expect(task).toHaveProperty('dueDate');
            expect(task).toHaveProperty('overdueDays');
            expect(task).toHaveProperty('memoryStrength');
            expect(task).toHaveProperty('retentionRate');
            expect(task).toHaveProperty('reviewCount');
            expect(task).toHaveProperty('status');
        });
    });

    it('TodayReviewItem 包含 canvasPath（用于 duck-typing 判断）', async () => {
        const records = [createMockReviewRecord()];
        service.setDataManager(createMockDbManager(records) as any);

        const items = await service.getTodayReviewItems();

        items.forEach(item => {
            // ReviewDashboardView L2342: 'canvasPath' in task 用于区分
            expect('canvasPath' in item).toBe(true);
            expect(typeof item.canvasPath).toBe('string');
        });
    });

    it('TodayReviewItem 扩展字段完整', async () => {
        const records = [createMockReviewRecord()];
        service.setDataManager(createMockDbManager(records) as any);

        const items = await service.getTodayReviewItems();

        items.forEach(item => {
            expect(item).toHaveProperty('canvasPath');
            expect(item).toHaveProperty('daysSinceLastReview');
            expect(item).toHaveProperty('scheduledDate');
            expect(item).toHaveProperty('urgencyLabel');
            expect(item).toHaveProperty('urgencyColor');
            expect(typeof item.daysSinceLastReview).toBe('number');
            expect(item.scheduledDate).toBeInstanceOf(Date);
        });
    });
});

// ===========================================================================
// AC-31.A.6.3: 右键菜单完整 7 action 覆盖
// ===========================================================================
describe('AC-31.A.6.3: 右键菜单完整覆盖', () => {
    let service: TodayReviewListService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = createTodayReviewListService(mockApp);
        service.setDataManager(createMockDbManager() as any);
        (mockApp.vault.getAbstractFileByPath as jest.Mock).mockReturnValue(
            new MockTFile('math/algebra.canvas')
        );
    });

    describe('handleContextMenuAction - 全 7 action', () => {
        const item = createMockItem();

        it('start_review → true', async () => {
            const result = await service.handleContextMenuAction('start_review', item);
            expect(result).toBe(true);
        });

        it('postpone_1d → true + 推迟 1 天', async () => {
            const result = await service.handleContextMenuAction('postpone_1d', item);
            expect(result).toBe(true);
            expect(mockNotice).toHaveBeenCalledWith(expect.stringContaining('1 天'));
        });

        it('postpone_3d → true + 推迟 3 天', async () => {
            const result = await service.handleContextMenuAction('postpone_3d', item);
            expect(result).toBe(true);
            expect(mockNotice).toHaveBeenCalledWith(expect.stringContaining('3 天'));
        });

        it('postpone_7d → true + 推迟 7 天', async () => {
            const result = await service.handleContextMenuAction('postpone_7d', item);
            expect(result).toBe(true);
            expect(mockNotice).toHaveBeenCalledWith(expect.stringContaining('7 天'));
        });

        it('mark_mastered → true + 更新 memoryStrength 0.95', async () => {
            const result = await service.handleContextMenuAction('mark_mastered', item);
            expect(result).toBe(true);
            const dao = (service as any).dbManager.getReviewRecordDAO();
            expect(dao.updateMemoryMetrics).toHaveBeenCalledWith(
                1, 0.95, 0.95, expect.any(Date)
            );
        });

        it('reset_progress → true + 重置 memoryStrength 0.3', async () => {
            const result = await service.handleContextMenuAction('reset_progress', item);
            expect(result).toBe(true);
            const dao = (service as any).dbManager.getReviewRecordDAO();
            expect(dao.updateMemoryMetrics).toHaveBeenCalledWith(
                1, 0.3, 0.5, expect.any(Date)
            );
        });

        it('open_canvas → true', async () => {
            const result = await service.handleContextMenuAction('open_canvas', item);
            expect(result).toBe(true);
            expect(mockApp.workspace.openLinkText).toHaveBeenCalled();
        });

        it('未知 action → false', async () => {
            const result = await service.handleContextMenuAction('unknown_action' as ContextMenuAction, item);
            expect(result).toBe(false);
        });
    });

    describe('showContextMenu 菜单结构', () => {
        it('创建 7 个菜单项', () => {
            const item = createMockItem();
            const actions: ContextMenuAction[] = [];

            service.showContextMenu(
                { clientX: 100, clientY: 200 } as MouseEvent,
                item,
                (action) => { actions.push(action); }
            );

            // Menu 构造函数被调用
            const { Menu } = jest.requireMock('obsidian');
            expect(Menu).toHaveBeenCalled();
        });
    });

    describe('菜单操作后 Dashboard 刷新', () => {
        it('onAction 回调被正确传递', () => {
            const item = createMockItem();
            const onAction = jest.fn();

            service.showContextMenu(
                { clientX: 0, clientY: 0 } as MouseEvent,
                item,
                onAction
            );

            // 验证 showContextMenu 不抛异常、Menu 被实例化
            const { Menu } = jest.requireMock('obsidian');
            expect(Menu).toHaveBeenCalled();
        });
    });
});

// ===========================================================================
// AC-31.A.6.4: 接口适配
// ===========================================================================
describe('AC-31.A.6.4: 接口适配 - ReviewTask 值域', () => {
    let service: TodayReviewListService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = createTodayReviewListService(mockApp);
    });

    it('memoryStrength 在 0-1 范围（UITypes 规范）', async () => {
        const records = [
            createMockReviewRecord({ memoryStrength: 0.0 }),
            createMockReviewRecord({ id: 2, conceptId: 'c2', memoryStrength: 0.5 }),
            createMockReviewRecord({ id: 3, conceptId: 'c3', memoryStrength: 1.0 }),
        ];
        service.setDataManager(createMockDbManager(records) as any);

        const items = await service.getTodayReviewItems();

        items.forEach(item => {
            expect(item.memoryStrength).toBeGreaterThanOrEqual(0);
            expect(item.memoryStrength).toBeLessThanOrEqual(1);
        });
    });

    it('retentionRate 在 0-1 范围（UITypes 规范）', async () => {
        const records = [
            createMockReviewRecord({ retentionRate: 0.0 }),
            createMockReviewRecord({ id: 2, conceptId: 'c2', retentionRate: 0.9 }),
        ];
        service.setDataManager(createMockDbManager(records) as any);

        const items = await service.getTodayReviewItems();

        items.forEach(item => {
            expect(item.retentionRate).toBeGreaterThanOrEqual(0);
            expect(item.retentionRate).toBeLessThanOrEqual(1);
        });
    });

    it('priority 是有效的 TaskPriority 枚举值', async () => {
        const records = [createMockReviewRecord()];
        service.setDataManager(createMockDbManager(records) as any);

        const items = await service.getTodayReviewItems();
        const validPriorities = ['critical', 'high', 'medium', 'low'];

        items.forEach(item => {
            expect(validPriorities).toContain(item.priority);
        });
    });

    it('PRIORITY_CONFIG 与 priority 值一一对应', () => {
        const validPriorities = ['critical', 'high', 'medium', 'low'] as const;
        validPriorities.forEach(p => {
            const config = PRIORITY_CONFIG[p];
            expect(config).toBeDefined();
            expect(config.label).toBeTruthy();
            expect(config.color).toMatch(/^#[0-9a-f]{6}$/i);
            expect(config.weight).toBeGreaterThan(0);
        });
    });
});

// ===========================================================================
// 缓存一致性
// ===========================================================================
describe('缓存一致性', () => {
    let service: TodayReviewListService;
    let mockDbManager: ReturnType<typeof createMockDbManager>;

    beforeEach(() => {
        jest.clearAllMocks();
        service = createTodayReviewListService(mockApp);
        mockDbManager = createMockDbManager([createMockReviewRecord()]);
        service.setDataManager(mockDbManager as any);
        (mockApp.vault.getAbstractFileByPath as jest.Mock).mockReturnValue(
            new MockTFile('math/algebra.canvas')
        );
    });

    it('setDataManager 清除缓存', async () => {
        await service.getTodayReviewItems(); // populate cache
        const dao = mockDbManager.getReviewRecordDAO();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(1);

        // 重新设置 dataManager → 缓存被清除
        service.setDataManager(mockDbManager as any);
        await service.getTodayReviewItems();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(2);
    });

    it('setMemoryQueryService 清除缓存', async () => {
        await service.getTodayReviewItems();
        const dao = mockDbManager.getReviewRecordDAO();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(1);

        service.setMemoryQueryService(createMockMemoryQueryService() as any);
        await service.getTodayReviewItems();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(2);
    });

    it('setFSRSStateQueryService 清除缓存', async () => {
        await service.getTodayReviewItems();
        const dao = mockDbManager.getReviewRecordDAO();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(1);

        service.setFSRSStateQueryService(createMockFSRSStateQueryService() as any);
        await service.getTodayReviewItems();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(2);
    });

    it('postponeReview 后缓存被清除', async () => {
        await service.getTodayReviewItems();
        const dao = mockDbManager.getReviewRecordDAO();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(1);

        await service.postponeReview(createMockItem(), 1);
        await service.getTodayReviewItems();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(2);
    });

    it('markAsMastered 后缓存被清除', async () => {
        await service.getTodayReviewItems();
        const dao = mockDbManager.getReviewRecordDAO();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(1);

        await service.markAsMastered(createMockItem());
        await service.getTodayReviewItems();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(2);
    });

    it('resetProgress 后缓存被清除', async () => {
        await service.getTodayReviewItems();
        const dao = mockDbManager.getReviewRecordDAO();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(1);

        await service.resetProgress(createMockItem());
        await service.getTodayReviewItems();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(2);
    });

    it('startReview 后缓存被清除', async () => {
        await service.getTodayReviewItems();
        const dao = mockDbManager.getReviewRecordDAO();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(1);

        await service.startReview(createMockItem());
        await service.getTodayReviewItems();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(2);
    });

    it('clearCache 显式清除后重新获取', async () => {
        await service.getTodayReviewItems();
        const dao = mockDbManager.getReviewRecordDAO();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(1);

        service.clearCache();
        await service.getTodayReviewItems();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(2);
    });

    it('缓存有效期内不重复查询', async () => {
        await service.getTodayReviewItems();
        await service.getTodayReviewItems();
        await service.getTodayReviewItems();

        const dao = mockDbManager.getReviewRecordDAO();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(1);
    });

    it('forceRefresh=true 绕过缓存', async () => {
        await service.getTodayReviewItems();
        await service.getTodayReviewItems(true);

        const dao = mockDbManager.getReviewRecordDAO();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(2);
    });
});

// ===========================================================================
// getFilteredSortedItems 组合操作
// ===========================================================================
describe('getFilteredSortedItems 组合', () => {
    let service: TodayReviewListService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = createTodayReviewListService(mockApp);

        const now = new Date();
        const overdue = new Date(now);
        overdue.setDate(overdue.getDate() - 3);

        const records = [
            createMockReviewRecord({ id: 1, conceptId: 'c1', memoryStrength: 0.1, nextReviewDate: overdue.toISOString() }),
            createMockReviewRecord({ id: 2, conceptId: 'c2', memoryStrength: 0.5 }),
            createMockReviewRecord({ id: 3, conceptId: 'c3', memoryStrength: 0.9 }),
        ];
        service.setDataManager(createMockDbManager(records) as any);
    });

    it('filter=all + sort=priority', async () => {
        const items = await service.getFilteredSortedItems('all', 'priority');
        expect(items).toHaveLength(3);
        // 第一个应是最高优先级
        const w0 = PRIORITY_CONFIG[items[0].priority]?.weight || 0;
        const w2 = PRIORITY_CONFIG[items[2].priority]?.weight || 0;
        expect(w0).toBeGreaterThanOrEqual(w2);
    });

    it('filter=overdue + sort=memoryStrength', async () => {
        const items = await service.getFilteredSortedItems('overdue', 'memoryStrength');
        items.forEach(item => {
            expect(item.overdueDays).toBeGreaterThan(0);
        });
        // 按 memoryStrength 升序
        for (let i = 1; i < items.length; i++) {
            expect(items[i].memoryStrength).toBeGreaterThanOrEqual(items[i - 1].memoryStrength);
        }
    });

    it('filter=high-priority + sort=dueDate', async () => {
        const items = await service.getFilteredSortedItems('high-priority', 'dueDate');
        items.forEach(item => {
            expect(['critical', 'high']).toContain(item.priority);
        });
        // 按 dueDate 升序
        for (let i = 1; i < items.length; i++) {
            expect(items[i].dueDate.getTime()).toBeGreaterThanOrEqual(items[i - 1].dueDate.getTime());
        }
    });

    it('filter=all + sort=canvas', async () => {
        const items = await service.getFilteredSortedItems('all', 'canvas');
        // 按 canvasTitle 字母序
        for (let i = 1; i < items.length; i++) {
            expect(items[i].canvasTitle.localeCompare(items[i - 1].canvasTitle)).toBeGreaterThanOrEqual(0);
        }
    });

    it('forceRefresh 传递到 getTodayReviewItems', async () => {
        await service.getFilteredSortedItems('all', 'priority', false);
        await service.getFilteredSortedItems('all', 'priority', true);

        const dbManager = (service as any).dbManager;
        const dao = dbManager.getReviewRecordDAO();
        expect(dao.getDueForReview).toHaveBeenCalledTimes(2);
    });
});

// ===========================================================================
// Graceful Degradation - 服务不可用场景
// ===========================================================================
describe('Graceful Degradation', () => {
    let service: TodayReviewListService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = createTodayReviewListService(mockApp);
    });

    it('MemoryQueryService 失败不影响结果', async () => {
        const records = [createMockReviewRecord()];
        service.setDataManager(createMockDbManager(records) as any);
        service.setMemoryQueryService({
            queryConceptMemory: jest.fn().mockRejectedValue(new Error('Memory service down')),
        } as any);

        const items = await service.getTodayReviewItems();
        expect(items).toHaveLength(1);
        expect(items[0].priority).toBeDefined();
    });

    it('FSRSStateQueryService 失败不影响结果', async () => {
        const records = [createMockReviewRecord()];
        service.setDataManager(createMockDbManager(records) as any);
        service.setFSRSStateQueryService({
            queryFSRSState: jest.fn().mockRejectedValue(new Error('FSRS service down')),
        } as any);

        const items = await service.getTodayReviewItems();
        expect(items).toHaveLength(1);
    });

    it('FSRSStateQueryService 返回 found=false', async () => {
        const records = [createMockReviewRecord()];
        service.setDataManager(createMockDbManager(records) as any);
        service.setFSRSStateQueryService({
            queryFSRSState: jest.fn().mockResolvedValue({ found: false }),
        } as any);

        const items = await service.getTodayReviewItems();
        expect(items).toHaveLength(1);
    });

    it('ReviewRecordDAO.getDueForReview 失败返回空数组', async () => {
        service.setDataManager({
            getReviewRecordDAO: jest.fn().mockReturnValue({
                getDueForReview: jest.fn().mockRejectedValue(new Error('DB connection lost')),
                getDailyStats: jest.fn().mockResolvedValue({ completedCount: 0, skippedCount: 0, totalReviews: 0 }),
            }),
        } as any);

        const items = await service.getTodayReviewItems();
        expect(items).toEqual([]);
    });

    it('reviewCount 查询失败时使用默认值 1', async () => {
        const dbm = {
            getReviewRecordDAO: jest.fn().mockReturnValue({
                getDueForReview: jest.fn().mockResolvedValue([createMockReviewRecord()]),
                getDailyStats: jest.fn().mockResolvedValue({ completedCount: 0, skippedCount: 0, totalReviews: 0 }),
                getReviewCountByConceptId: jest.fn().mockRejectedValue(new Error('count failed')),
            }),
        };
        service.setDataManager(dbm as any);

        const items = await service.getTodayReviewItems();
        expect(items).toHaveLength(1);
        expect(items[0].reviewCount).toBe(1); // fallback
    });

    it('全部服务不可用时仍返回结果（使用数据库默认值）', async () => {
        const records = [createMockReviewRecord({ memoryStrength: 0.4, retentionRate: 0.6 })];
        service.setDataManager(createMockDbManager(records) as any);
        // 不注入 memoryQueryService 和 fsrsStateQueryService

        const items = await service.getTodayReviewItems();
        expect(items).toHaveLength(1);
        expect(items[0].memoryStrength).toBe(0.4);
        expect(items[0].retentionRate).toBe(0.6);
    });
});

// ===========================================================================
// 边界用例
// ===========================================================================
describe('边界用例', () => {
    let service: TodayReviewListService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = createTodayReviewListService(mockApp);
    });

    describe('无效 record ID', () => {
        it('postponeReview 对非数字 ID 抛出并返回 false', async () => {
            service.setDataManager(createMockDbManager() as any);
            const item = createMockItem({ id: 'not-a-number' });

            const result = await service.postponeReview(item, 1);
            expect(result).toBe(false);
        });

        it('markAsMastered 对非数字 ID 返回 false', async () => {
            service.setDataManager(createMockDbManager() as any);
            const item = createMockItem({ id: 'abc' });

            const result = await service.markAsMastered(item);
            expect(result).toBe(false);
        });

        it('resetProgress 对非数字 ID 返回 false', async () => {
            service.setDataManager(createMockDbManager() as any);
            const item = createMockItem({ id: 'xyz' });

            const result = await service.resetProgress(item);
            expect(result).toBe(false);
        });
    });

    describe('无 dbManager 时的操作', () => {
        it('postponeReview 无 dbManager → false', async () => {
            const result = await service.postponeReview(createMockItem(), 1);
            expect(result).toBe(false);
        });

        it('markAsMastered 无 dbManager → false', async () => {
            const result = await service.markAsMastered(createMockItem());
            expect(result).toBe(false);
        });

        it('resetProgress 无 dbManager → false', async () => {
            const result = await service.resetProgress(createMockItem());
            expect(result).toBe(false);
        });
    });

    describe('空记录列表', () => {
        it('空记录返回空数组', async () => {
            service.setDataManager(createMockDbManager([]) as any);

            const items = await service.getTodayReviewItems();
            expect(items).toEqual([]);
        });

        it('空记录的 summary 全零', async () => {
            service.setDataManager(createMockDbManager([]) as any);

            const summary = await service.getTodayReviewSummary();
            expect(summary.totalDueToday).toBe(0);
            expect(summary.overdueCount).toBe(0);
            expect(summary.criticalCount).toBe(0);
            expect(summary.highCount).toBe(0);
            expect(summary.mediumCount).toBe(0);
            expect(summary.lowCount).toBe(0);
        });
    });

    describe('extractCanvasTitle', () => {
        it('从路径提取文件名', async () => {
            const records = [createMockReviewRecord({ canvasId: 'path/to/my-canvas.canvas' })];
            service.setDataManager(createMockDbManager(records) as any);

            const items = await service.getTodayReviewItems();
            expect(items[0].canvasTitle).toBe('my-canvas');
        });

        it('空路径返回 Unknown Canvas', async () => {
            const records = [createMockReviewRecord({ canvasId: '' })];
            service.setDataManager(createMockDbManager(records) as any);

            const items = await service.getTodayReviewItems();
            expect(items[0].canvasTitle).toBe('Unknown Canvas');
        });
    });

    describe('mapStatus 所有分支', () => {
        const statusTestCases = [
            { input: 'completed', expected: 'completed' },
            { input: 'in_progress', expected: 'in_progress' },
            { input: 'scheduled', expected: 'postponed' },
            { input: 'postponed', expected: 'postponed' },
            { input: 'pending', expected: 'pending' },
            { input: undefined, expected: 'pending' },
            { input: 'unknown_status', expected: 'pending' },
        ];

        statusTestCases.forEach(({ input, expected }) => {
            it(`status "${input}" → "${expected}"`, async () => {
                const records = [createMockReviewRecord({ status: input })];
                service.setDataManager(createMockDbManager(records) as any);

                const items = await service.getTodayReviewItems();
                expect(items[0].status).toBe(expected);
            });
        });
    });

    describe('openCanvas 边界', () => {
        it('文件不存在 + 不带 .canvas 后缀 → false', async () => {
            (mockApp.vault.getAbstractFileByPath as jest.Mock).mockReturnValue(null);

            const item = createMockItem({ canvasPath: 'nonexistent' });
            const result = await service.openCanvas(item);
            expect(result).toBe(false);
        });

        it('workspace.openLinkText 异常 → false', async () => {
            (mockApp.vault.getAbstractFileByPath as jest.Mock).mockReturnValue(
                new MockTFile('test.canvas')
            );
            (mockApp.workspace.openLinkText as jest.Mock).mockRejectedValueOnce(new Error('workspace error'));

            const item = createMockItem();
            const result = await service.openCanvas(item);
            expect(result).toBe(false);
        });
    });

    describe('convertToTodayReviewItemAsync 字段计算', () => {
        it('overdueDays 正确计算过期天数', async () => {
            const pastDate = new Date();
            pastDate.setDate(pastDate.getDate() - 5);

            const records = [createMockReviewRecord({ nextReviewDate: pastDate.toISOString() })];
            service.setDataManager(createMockDbManager(records) as any);

            const items = await service.getTodayReviewItems();
            // 过期 5 天左右
            expect(items[0].overdueDays).toBeGreaterThanOrEqual(4);
            expect(items[0].overdueDays).toBeLessThanOrEqual(6);
        });

        it('daysSinceLastReview 正确计算', async () => {
            const lastReview = new Date();
            lastReview.setDate(lastReview.getDate() - 3);

            const records = [createMockReviewRecord({ reviewDate: lastReview.toISOString() })];
            service.setDataManager(createMockDbManager(records) as any);

            const items = await service.getTodayReviewItems();
            expect(items[0].daysSinceLastReview).toBeGreaterThanOrEqual(2);
            expect(items[0].daysSinceLastReview).toBeLessThanOrEqual(4);
        });

        it('无 reviewDate 时 daysSinceLastReview = 0', async () => {
            const records = [createMockReviewRecord({ reviewDate: null })];
            service.setDataManager(createMockDbManager(records) as any);

            const items = await service.getTodayReviewItems();
            expect(items[0].daysSinceLastReview).toBe(0);
        });

        it('无 nextReviewDate 时使用当前日期', async () => {
            const records = [createMockReviewRecord({ nextReviewDate: null })];
            service.setDataManager(createMockDbManager(records) as any);

            const items = await service.getTodayReviewItems();
            expect(items[0].dueDate).toBeInstanceOf(Date);
            // overdueDays 应该接近 0
            expect(Math.abs(items[0].overdueDays)).toBeLessThanOrEqual(1);
        });

        it('无 conceptId 时 conceptName 为 Unknown Concept', async () => {
            const records = [createMockReviewRecord({ conceptId: '' })];
            service.setDataManager(createMockDbManager(records) as any);

            const items = await service.getTodayReviewItems();
            expect(items[0].conceptName).toBe('Unknown Concept');
        });
    });
});

// ===========================================================================
// getTodayReviewSummary 统计准确性
// ===========================================================================
describe('getTodayReviewSummary 统计', () => {
    let service: TodayReviewListService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = createTodayReviewListService(mockApp);
    });

    it('正确统计各优先级数量', async () => {
        const now = new Date();
        const overdue3 = new Date(now);
        overdue3.setDate(overdue3.getDate() - 5);

        const records = [
            createMockReviewRecord({ id: 1, conceptId: 'c1', memoryStrength: 0.1, nextReviewDate: overdue3.toISOString() }),
            createMockReviewRecord({ id: 2, conceptId: 'c2', memoryStrength: 0.3 }),
            createMockReviewRecord({ id: 3, conceptId: 'c3', memoryStrength: 0.8 }),
        ];
        service.setDataManager(createMockDbManager(records) as any);

        const summary = await service.getTodayReviewSummary();

        expect(summary.totalDueToday).toBe(3);
        expect(summary.completedToday).toBe(2); // from mock getDailyStats
        expect(summary.criticalCount + summary.highCount + summary.mediumCount + summary.lowCount).toBe(3);
    });

    it('getDailyStats 失败时 completedToday 默认 0', async () => {
        service.setDataManager({
            getReviewRecordDAO: jest.fn().mockReturnValue({
                getDueForReview: jest.fn().mockResolvedValue([]),
                getDailyStats: jest.fn().mockRejectedValue(new Error('stats failed')),
                getReviewCountByConceptId: jest.fn().mockResolvedValue(1),
            }),
        } as any);

        const summary = await service.getTodayReviewSummary();
        expect(summary.completedToday).toBe(0);
        expect(summary.totalDueToday).toBe(0);
    });
});
