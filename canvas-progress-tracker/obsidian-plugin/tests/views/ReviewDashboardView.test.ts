/**
 * ReviewDashboardView Unit Tests - Canvas Learning System
 *
 * Tests for the ReviewDashboardView and task card components.
 * Implements Story 14.2 & 14.3: 复习仪表板UI & 任务卡片UI
 *
 * @module ReviewDashboardView.test
 * @version 1.0.0
 */

import {
    ReviewTask,
    TaskPriority,
    DashboardStatistics,
    DEFAULT_DASHBOARD_STATE,
    VerificationCanvasRelation,
    ReviewMode,
} from '../../src/types/UITypes';
import { ReviewDashboardView } from '../../src/views/ReviewDashboardView';

// Mock Obsidian
jest.mock('obsidian', () => ({
    ItemView: class {
        containerEl = { children: [null, { empty: jest.fn(), addClass: jest.fn() }] };
        app = { vault: { getAbstractFileByPath: jest.fn() }, workspace: { openLinkText: jest.fn() } };
        leaf = {};
    },
    WorkspaceLeaf: class {},
    Notice: jest.fn(),
    setIcon: jest.fn(),
}));

// Story 31.9: Mock service modules to enable ReviewDashboardView import
jest.mock('../../src/services/HistoryService', () => ({
    HistoryService: jest.fn(() => ({})),
}));
jest.mock('../../src/services/VerificationHistoryService', () => ({
    createVerificationHistoryService: jest.fn(() => ({})),
    VerificationHistoryService: jest.fn(),
}));
jest.mock('../../src/services/CrossCanvasService', () => ({
    createCrossCanvasService: jest.fn(() => ({})),
    CrossCanvasService: jest.fn(),
}));
jest.mock('../../src/services/TextbookMountService', () => ({
    createTextbookMountService: jest.fn(() => ({})),
    TextbookMountService: jest.fn(),
}));
jest.mock('../../src/services/PriorityCalculatorService', () => ({
    createPriorityCalculatorService: jest.fn(() => ({})),
    PriorityCalculatorService: jest.fn(),
}));

describe('ReviewDashboardView', () => {
    describe('Task Priority Calculation', () => {
        const calculatePriority = (memoryStrength: number): TaskPriority => {
            if (memoryStrength < 0.3) return 'critical';
            if (memoryStrength < 0.5) return 'high';
            if (memoryStrength < 0.7) return 'medium';
            return 'low';
        };

        it('should return critical priority for very low memory strength', () => {
            expect(calculatePriority(0.1)).toBe('critical');
            expect(calculatePriority(0.29)).toBe('critical');
        });

        it('should return high priority for low memory strength', () => {
            expect(calculatePriority(0.3)).toBe('high');
            expect(calculatePriority(0.49)).toBe('high');
        });

        it('should return medium priority for moderate memory strength', () => {
            expect(calculatePriority(0.5)).toBe('medium');
            expect(calculatePriority(0.69)).toBe('medium');
        });

        it('should return low priority for high memory strength', () => {
            expect(calculatePriority(0.7)).toBe('low');
            expect(calculatePriority(0.9)).toBe('low');
            expect(calculatePriority(1.0)).toBe('low');
        });
    });

    describe('Overdue Days Calculation', () => {
        const calculateOverdueDays = (dueDate?: Date): number => {
            if (!dueDate) return 0;
            const now = new Date();
            const due = new Date(dueDate);
            const diff = now.getTime() - due.getTime();
            return Math.floor(diff / (1000 * 60 * 60 * 24));
        };

        it('should return 0 for undefined due date', () => {
            expect(calculateOverdueDays(undefined)).toBe(0);
        });

        it('should return positive days for past due dates', () => {
            const pastDate = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000);
            expect(calculateOverdueDays(pastDate)).toBe(3);
        });

        it('should return 0 for today due date', () => {
            const today = new Date();
            expect(calculateOverdueDays(today)).toBe(0);
        });

        it('should return negative days for future due dates', () => {
            const futureDate = new Date(Date.now() + 5 * 24 * 60 * 60 * 1000);
            expect(calculateOverdueDays(futureDate)).toBeLessThan(0);
        });
    });

    describe('Memory Strength Level', () => {
        const getStrengthLevel = (strength: number): string => {
            if (strength >= 0.7) return 'high';
            if (strength >= 0.4) return 'medium';
            return 'low';
        };

        it('should return low for strength < 0.4', () => {
            expect(getStrengthLevel(0.1)).toBe('low');
            expect(getStrengthLevel(0.39)).toBe('low');
        });

        it('should return medium for 0.4 <= strength < 0.7', () => {
            expect(getStrengthLevel(0.4)).toBe('medium');
            expect(getStrengthLevel(0.69)).toBe('medium');
        });

        it('should return high for strength >= 0.7', () => {
            expect(getStrengthLevel(0.7)).toBe('high');
            expect(getStrengthLevel(1.0)).toBe('high');
        });
    });

    describe('Urgency Level', () => {
        const getUrgencyLevel = (overdueDays: number): { level: string; label: string } => {
            if (overdueDays > 0) {
                return { level: 'urgent', label: '急需复习' };
            }
            if (overdueDays === 0) {
                return { level: 'due', label: '今日到期' };
            }
            if (overdueDays >= -3) {
                return { level: 'soon', label: '即将到期' };
            }
            return { level: 'future', label: '计划中' };
        };

        it('should return urgent for overdue tasks', () => {
            expect(getUrgencyLevel(1).level).toBe('urgent');
            expect(getUrgencyLevel(5).level).toBe('urgent');
        });

        it('should return due for today tasks', () => {
            expect(getUrgencyLevel(0).level).toBe('due');
        });

        it('should return soon for tasks due within 3 days', () => {
            expect(getUrgencyLevel(-1).level).toBe('soon');
            expect(getUrgencyLevel(-3).level).toBe('soon');
        });

        it('should return future for tasks due later', () => {
            expect(getUrgencyLevel(-4).level).toBe('future');
            expect(getUrgencyLevel(-10).level).toBe('future');
        });
    });

    describe('Status Text', () => {
        const getStatusText = (status: string): string => {
            const texts: Record<string, string> = {
                pending: '待复习',
                in_progress: '学习中',
                completed: '已完成',
                postponed: '已推迟',
            };
            return texts[status] || '待复习';
        };

        it('should return correct text for each status', () => {
            expect(getStatusText('pending')).toBe('待复习');
            expect(getStatusText('in_progress')).toBe('学习中');
            expect(getStatusText('completed')).toBe('已完成');
            expect(getStatusText('postponed')).toBe('已推迟');
        });

        it('should return default text for unknown status', () => {
            expect(getStatusText('unknown')).toBe('待复习');
        });
    });

    describe('Relative Date Formatting', () => {
        const formatRelativeDate = (date: Date): string => {
            const now = new Date();
            const diff = date.getTime() - now.getTime();
            const days = Math.ceil(diff / (1000 * 60 * 60 * 24));

            if (days < -1) return `${Math.abs(days)}天前`;
            if (days === -1) return '昨天';
            if (days === 0) return '今天';
            if (days === 1) return '明天';
            if (days < 7) return `${days}天后`;
            return date.toLocaleDateString();
        };

        it('should return 今天 for today', () => {
            expect(formatRelativeDate(new Date())).toBe('今天');
        });

        it('should return 明天 for tomorrow', () => {
            const tomorrow = new Date(Date.now() + 24 * 60 * 60 * 1000);
            expect(formatRelativeDate(tomorrow)).toBe('明天');
        });

        it('should return X天后 for near future', () => {
            const inThreeDays = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000);
            expect(formatRelativeDate(inThreeDays)).toBe('3天后');
        });

        it('should return locale date string for dates > 7 days', () => {
            const farFuture = new Date(Date.now() + 10 * 24 * 60 * 60 * 1000);
            expect(formatRelativeDate(farFuture)).toBe(farFuture.toLocaleDateString());
        });
    });

    describe('Priority Weight', () => {
        const getPriorityWeight = (priority: TaskPriority): number => {
            const weights: Record<TaskPriority, number> = {
                critical: 4,
                high: 3,
                medium: 2,
                low: 1,
            };
            return weights[priority];
        };

        it('should return correct weights for each priority', () => {
            expect(getPriorityWeight('critical')).toBe(4);
            expect(getPriorityWeight('high')).toBe(3);
            expect(getPriorityWeight('medium')).toBe(2);
            expect(getPriorityWeight('low')).toBe(1);
        });
    });

    describe('Task Filtering', () => {
        const mockTasks: ReviewTask[] = [
            {
                id: '1',
                canvasId: 'canvas1',
                canvasTitle: 'Canvas 1',
                conceptName: 'Concept 1',
                priority: 'critical',
                dueDate: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // Overdue
                overdueDays: 2,
                memoryStrength: 0.2,
                retentionRate: 0.3,
                reviewCount: 5,
                status: 'pending',
            },
            {
                id: '2',
                canvasId: 'canvas2',
                canvasTitle: 'Canvas 2',
                conceptName: 'Concept 2',
                priority: 'high',
                dueDate: new Date(), // Today
                overdueDays: 0,
                memoryStrength: 0.4,
                retentionRate: 0.5,
                reviewCount: 3,
                status: 'pending',
            },
            {
                id: '3',
                canvasId: 'canvas3',
                canvasTitle: 'Canvas 3',
                conceptName: 'Concept 3',
                priority: 'low',
                dueDate: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000), // Future
                overdueDays: -5,
                memoryStrength: 0.8,
                retentionRate: 0.9,
                reviewCount: 10,
                status: 'pending',
            },
        ];

        it('should filter overdue tasks', () => {
            const filtered = mockTasks.filter((t) => t.overdueDays > 0);
            expect(filtered).toHaveLength(1);
            expect(filtered[0].id).toBe('1');
        });

        it('should filter today tasks', () => {
            const today = new Date().toDateString();
            const filtered = mockTasks.filter((t) => t.dueDate.toDateString() === today);
            expect(filtered).toHaveLength(1);
            expect(filtered[0].id).toBe('2');
        });

        it('should filter high priority tasks', () => {
            const filtered = mockTasks.filter(
                (t) => t.priority === 'critical' || t.priority === 'high'
            );
            expect(filtered).toHaveLength(2);
        });
    });

    describe('Task Sorting', () => {
        const mockTasks: ReviewTask[] = [
            {
                id: '1',
                canvasId: 'b_canvas',
                canvasTitle: 'B Canvas',
                conceptName: 'Concept B',
                priority: 'medium',
                dueDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000),
                overdueDays: -2,
                memoryStrength: 0.5,
                retentionRate: 0.6,
                reviewCount: 3,
                status: 'pending',
            },
            {
                id: '2',
                canvasId: 'a_canvas',
                canvasTitle: 'A Canvas',
                conceptName: 'Concept A',
                priority: 'critical',
                dueDate: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
                overdueDays: 1,
                memoryStrength: 0.2,
                retentionRate: 0.3,
                reviewCount: 5,
                status: 'pending',
            },
            {
                id: '3',
                canvasId: 'c_canvas',
                canvasTitle: 'C Canvas',
                conceptName: 'Concept C',
                priority: 'low',
                dueDate: new Date(),
                overdueDays: 0,
                memoryStrength: 0.9,
                retentionRate: 0.95,
                reviewCount: 10,
                status: 'pending',
            },
        ];

        const getPriorityWeight = (priority: TaskPriority): number => {
            const weights: Record<TaskPriority, number> = {
                critical: 4,
                high: 3,
                medium: 2,
                low: 1,
            };
            return weights[priority];
        };

        it('should sort by priority descending', () => {
            const sorted = [...mockTasks].sort(
                (a, b) => getPriorityWeight(b.priority) - getPriorityWeight(a.priority)
            );
            expect(sorted[0].priority).toBe('critical');
            expect(sorted[1].priority).toBe('medium');
            expect(sorted[2].priority).toBe('low');
        });

        it('should sort by due date ascending', () => {
            const sorted = [...mockTasks].sort(
                (a, b) => a.dueDate.getTime() - b.dueDate.getTime()
            );
            expect(sorted[0].id).toBe('2'); // Overdue
            expect(sorted[2].id).toBe('1'); // Future
        });

        it('should sort by memory strength ascending', () => {
            const sorted = [...mockTasks].sort(
                (a, b) => a.memoryStrength - b.memoryStrength
            );
            expect(sorted[0].memoryStrength).toBe(0.2);
            expect(sorted[2].memoryStrength).toBe(0.9);
        });

        it('should sort by canvas title alphabetically', () => {
            const sorted = [...mockTasks].sort((a, b) =>
                a.canvasTitle.localeCompare(b.canvasTitle)
            );
            expect(sorted[0].canvasTitle).toBe('A Canvas');
            expect(sorted[2].canvasTitle).toBe('C Canvas');
        });
    });

    describe('Default Dashboard State', () => {
        it('should have correct initial values', () => {
            expect(DEFAULT_DASHBOARD_STATE.tasks).toEqual([]);
            expect(DEFAULT_DASHBOARD_STATE.loading).toBe(true);
            expect(DEFAULT_DASHBOARD_STATE.error).toBeNull();
            expect(DEFAULT_DASHBOARD_STATE.sortBy).toBe('priority');
            expect(DEFAULT_DASHBOARD_STATE.filterBy).toBe('all');
            expect(DEFAULT_DASHBOARD_STATE.lastUpdated).toBeNull();
        });

        it('should have empty statistics', () => {
            const stats = DEFAULT_DASHBOARD_STATE.statistics;
            expect(stats.todayPending).toBe(0);
            expect(stats.todayCompleted).toBe(0);
            expect(stats.masteryDistribution).toEqual([]);
        });
    });
});

describe('Task Card Component', () => {
    describe('Card Class Generation', () => {
        const generateCardClasses = (
            priority: TaskPriority,
            status: string,
            isOverdue: boolean,
            isToday: boolean
        ): string[] => {
            return [
                'task-card',
                `priority-${priority}`,
                `status-${status}`,
                isOverdue ? 'overdue' : '',
                isToday && !isOverdue ? 'due-today' : '',
            ].filter(Boolean);
        };

        it('should include all base classes', () => {
            const classes = generateCardClasses('medium', 'pending', false, false);
            expect(classes).toContain('task-card');
            expect(classes).toContain('priority-medium');
            expect(classes).toContain('status-pending');
        });

        it('should include overdue class when overdue', () => {
            const classes = generateCardClasses('critical', 'pending', true, false);
            expect(classes).toContain('overdue');
            expect(classes).not.toContain('due-today');
        });

        it('should include due-today class when due today and not overdue', () => {
            const classes = generateCardClasses('high', 'pending', false, true);
            expect(classes).toContain('due-today');
            expect(classes).not.toContain('overdue');
        });

        it('should not include due-today when overdue takes precedence', () => {
            const classes = generateCardClasses('high', 'pending', true, true);
            expect(classes).toContain('overdue');
            expect(classes).not.toContain('due-today');
        });
    });

    describe('Strength Emoji', () => {
        const getStrengthEmoji = (strength: number): string => {
            if (strength >= 0.9) return '🏆';
            if (strength >= 0.7) return '✅';
            if (strength >= 0.4) return '⚠️';
            return '❌';
        };

        it('should return trophy for excellent strength', () => {
            expect(getStrengthEmoji(0.95)).toBe('🏆');
            expect(getStrengthEmoji(1.0)).toBe('🏆');
        });

        it('should return checkmark for good strength', () => {
            expect(getStrengthEmoji(0.7)).toBe('✅');
            expect(getStrengthEmoji(0.89)).toBe('✅');
        });

        it('should return warning for moderate strength', () => {
            expect(getStrengthEmoji(0.4)).toBe('⚠️');
            expect(getStrengthEmoji(0.69)).toBe('⚠️');
        });

        it('should return X for poor strength', () => {
            expect(getStrengthEmoji(0.1)).toBe('❌');
            expect(getStrengthEmoji(0.39)).toBe('❌');
        });
    });

    describe('Priority Label', () => {
        const getPriorityLabel = (priority: TaskPriority): string => {
            const labels: Record<TaskPriority, string> = {
                critical: '紧急',
                high: '高',
                medium: '中',
                low: '低',
            };
            return labels[priority];
        };

        it('should return correct Chinese labels', () => {
            expect(getPriorityLabel('critical')).toBe('紧急');
            expect(getPriorityLabel('high')).toBe('高');
            expect(getPriorityLabel('medium')).toBe('中');
            expect(getPriorityLabel('low')).toBe('低');
        });
    });

    describe('Score Calculation', () => {
        // Based on FSRS algorithm
        const calculateNewMemoryStrength = (
            currentStrength: number,
            score: number
        ): number => {
            // Score 1-5: 1=forgot, 5=perfect
            const factor = (score - 1) / 4; // Normalize to 0-1
            const delta = factor * 0.15 - (1 - factor) * 0.1;
            return Math.max(0, Math.min(1, currentStrength + delta));
        };

        it('should decrease strength for score 1', () => {
            const newStrength = calculateNewMemoryStrength(0.5, 1);
            expect(newStrength).toBeLessThan(0.5);
        });

        it('should increase strength for score 5', () => {
            const newStrength = calculateNewMemoryStrength(0.5, 5);
            expect(newStrength).toBeGreaterThan(0.5);
        });

        it('should keep strength in bounds', () => {
            const lowStrength = calculateNewMemoryStrength(0.05, 1);
            expect(lowStrength).toBeGreaterThanOrEqual(0);

            const highStrength = calculateNewMemoryStrength(0.95, 5);
            expect(highStrength).toBeLessThanOrEqual(1);
        });
    });

    describe('Next Review Date Calculation', () => {
        const calculateNextReviewDate = (
            currentStrength: number,
            score: number
        ): number => {
            // Simplified interval calculation
            const baseInterval = 1; // days
            const factor = (score - 1) / 4;
            const strengthBonus = currentStrength * 2;
            return Math.ceil(baseInterval * (1 + factor * 6) * (1 + strengthBonus));
        };

        it('should return short interval for low score', () => {
            const interval = calculateNextReviewDate(0.5, 1);
            expect(interval).toBeLessThanOrEqual(3);
        });

        it('should return longer interval for high score', () => {
            const interval = calculateNextReviewDate(0.5, 5);
            expect(interval).toBeGreaterThan(3);
        });

        it('should increase interval with higher memory strength', () => {
            const lowStrengthInterval = calculateNextReviewDate(0.2, 3);
            const highStrengthInterval = calculateNextReviewDate(0.8, 3);
            expect(highStrengthInterval).toBeGreaterThan(lowStrengthInterval);
        });
    });
});

/**
 * Story 31.9: Verification Methods Tests - Testing ACTUAL ReviewDashboardView code
 *
 * These tests use Object.create(ReviewDashboardView.prototype) to bypass the constructor,
 * then call the actual private methods via (view as any) to verify real DOM output and
 * service interactions. Replaces the 17 self-referential tests from Story 31.7.
 */
describe('ReviewDashboardView - Verification Methods (Story 31.9)', () => {
    // Trackable mock element for Obsidian DOM API
    interface MockElement {
        children: MockElement[];
        textContent: string;
        cls: string;
        tag: string;
        _attrs: Record<string, string>;
        _listeners: Record<string, Function[]>;
        createDiv: jest.Mock;
        createSpan: jest.Mock;
        createEl: jest.Mock;
        setAttribute: jest.Mock;
        addEventListener: jest.Mock;
    }

    function createMockElement(tag = 'div'): MockElement {
        const element: MockElement = {
            children: [],
            textContent: '',
            cls: '',
            tag,
            _attrs: {},
            _listeners: {},
            createDiv: jest.fn(),
            createSpan: jest.fn(),
            createEl: jest.fn(),
            setAttribute: jest.fn(),
            addEventListener: jest.fn(),
        };

        element.createDiv.mockImplementation((opts?: { cls?: string; text?: string }) => {
            const child = createMockElement('div');
            if (opts?.cls) child.cls = opts.cls;
            if (opts?.text) child.textContent = opts.text;
            element.children.push(child);
            return child;
        });

        element.createSpan.mockImplementation((opts?: { cls?: string; text?: string }) => {
            const child = createMockElement('span');
            if (opts?.cls) child.cls = opts.cls;
            if (opts?.text) child.textContent = opts.text;
            element.children.push(child);
            return child;
        });

        element.createEl.mockImplementation((tagName: string, opts?: { cls?: string; text?: string }) => {
            const child = createMockElement(tagName);
            if (opts?.cls) child.cls = opts.cls;
            if (opts?.text) child.textContent = opts.text;
            element.children.push(child);
            return child;
        });

        element.setAttribute.mockImplementation((key: string, value: string) => {
            element._attrs[key] = value;
        });

        element.addEventListener.mockImplementation((event: string, handler: Function) => {
            if (!element._listeners[event]) element._listeners[event] = [];
            element._listeners[event].push(handler);
        });

        return element;
    }

    // Helper: find child by cls substring
    function findByClass(parent: MockElement, cls: string): MockElement | undefined {
        return parent.children.find((c) => c.cls.includes(cls));
    }

    // Helper: find child by text substring
    function findByText(parent: MockElement, text: string): MockElement | undefined {
        return parent.children.find((c) => c.textContent.includes(text));
    }

    // Create view instance bypassing constructor via Object.create
    function createTestView() {
        const view = Object.create(ReviewDashboardView.prototype);
        view.app = {
            vault: { getAbstractFileByPath: jest.fn() },
            workspace: { openLinkText: jest.fn() },
        };
        view.verificationService = {
            deleteRelation: jest.fn().mockResolvedValue(undefined),
            getAllRelations: jest.fn().mockResolvedValue([]),
        };
        view.showConfirmDialog = jest.fn().mockResolvedValue(true);
        view.loadVerificationData = jest.fn().mockResolvedValue(undefined);
        return view;
    }

    // Create test relation data matching VerificationCanvasRelation interface
    function createTestRelation(overrides?: Partial<VerificationCanvasRelation>): VerificationCanvasRelation {
        return {
            id: 'test-relation-1',
            originalCanvasPath: 'path/to/original.canvas',
            originalCanvasTitle: '原始Canvas标题',
            verificationCanvasPath: 'path/to/verification.canvas',
            verificationCanvasTitle: '检验Canvas标题',
            generatedDate: new Date('2026-01-15'),
            reviewMode: 'fresh' as ReviewMode,
            currentScore: 3.5,
            completionRate: 0.75,
            sessionCount: 3,
            sessions: [
                { date: new Date('2026-01-10'), passRate: 0.6, mode: 'fresh' as ReviewMode, conceptsReviewed: 5, weakConceptsCount: 2 },
                { date: new Date('2026-01-13'), passRate: 0.8, mode: 'fresh' as ReviewMode, conceptsReviewed: 5, weakConceptsCount: 1 },
                { date: new Date('2026-01-15'), passRate: 0.7, mode: 'fresh' as ReviewMode, conceptsReviewed: 5, weakConceptsCount: 1 },
            ],
            ...overrides,
        } as VerificationCanvasRelation;
    }

    let view: any;
    let mockSetIcon: jest.Mock;
    let MockNotice: jest.Mock;

    beforeEach(() => {
        jest.clearAllMocks();
        view = createTestView();
        mockSetIcon = jest.requireMock('obsidian').setIcon;
        MockNotice = jest.requireMock('obsidian').Notice;
    });

    describe('renderVerificationItem - DOM Output (AC-31.9.3)', () => {
        it('should render verificationCanvasTitle in item title span', () => {
            const container = createMockElement();
            const relation = createTestRelation();

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const info = item.children[0];
            expect(info.cls).toBe('verification-item-info');
            const titleSpan = info.children[0];
            expect(titleSpan.textContent).toBe('检验Canvas标题');
            expect(titleSpan.cls).toBe('verification-item-title');
        });

        it('should render mode badge as 全新检验 for fresh mode', () => {
            const container = createMockElement();
            const relation = createTestRelation({ reviewMode: 'fresh' as ReviewMode });

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const info = item.children[0];
            const modeBadge = info.children[1];
            expect(modeBadge.textContent).toBe('全新检验');
            expect(modeBadge.cls).toContain('mode-badge');
        });

        it('should render mode badge as 针对性复习 for targeted mode', () => {
            const container = createMockElement();
            const relation = createTestRelation({ reviewMode: 'targeted' as ReviewMode });

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const info = item.children[0];
            const modeBadge = info.children[1];
            expect(modeBadge.textContent).toBe('针对性复习');
        });

        it('should render originalCanvasTitle in source div', () => {
            const container = createMockElement();
            const relation = createTestRelation();

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const info = item.children[0];
            const sourceDiv = info.children[2];
            expect(sourceDiv.textContent).toBe('原始Canvas: 原始Canvas标题');
            expect(sourceDiv.cls).toBe('verification-item-source');
        });

        it('should render completionRate as percentage', () => {
            const container = createMockElement();
            const relation = createTestRelation({ completionRate: 0.75 });

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const stats = item.children[1];
            expect(stats.children[0].textContent).toBe('完成度: 75%');
        });

        it('should render sessionCount', () => {
            const container = createMockElement();
            const relation = createTestRelation({ sessionCount: 3 });

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const stats = item.children[1];
            expect(stats.children[1].textContent).toBe('3次复习');
        });

        it('should calculate and render highest score from sessions', () => {
            const container = createMockElement();
            const relation = createTestRelation({
                sessions: [
                    { date: new Date(), passRate: 0.6, mode: 'fresh' as ReviewMode, conceptsReviewed: 5, weakConceptsCount: 2 },
                    { date: new Date(), passRate: 0.8, mode: 'fresh' as ReviewMode, conceptsReviewed: 5, weakConceptsCount: 1 },
                    { date: new Date(), passRate: 0.7, mode: 'fresh' as ReviewMode, conceptsReviewed: 5, weakConceptsCount: 1 },
                ],
            });

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const stats = item.children[1];
            const highestScoreSpan = findByText(stats, '最高分');
            expect(highestScoreSpan).toBeDefined();
            expect(highestScoreSpan!.textContent).toBe('最高分: 4.0/5');
            expect(highestScoreSpan!.cls).toContain('verification-stat-highest');
        });

        it('should render most recent date from last session', () => {
            const container = createMockElement();
            const lastDate = new Date('2026-01-15');
            const relation = createTestRelation({
                sessions: [
                    { date: new Date('2026-01-10'), passRate: 0.6, mode: 'fresh' as ReviewMode, conceptsReviewed: 5, weakConceptsCount: 2 },
                    { date: lastDate, passRate: 0.7, mode: 'fresh' as ReviewMode, conceptsReviewed: 5, weakConceptsCount: 1 },
                ],
            });

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const stats = item.children[1];
            const recentSpan = findByText(stats, '最近');
            expect(recentSpan).toBeDefined();
            expect(recentSpan!.cls).toContain('verification-stat-recent');
            const expectedDateStr = lastDate.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
            expect(recentSpan!.textContent).toBe(`最近: ${expectedDateStr}`);
        });

        it('should render currentScore when present', () => {
            const container = createMockElement();
            const relation = createTestRelation({ currentScore: 3.5 });

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const stats = item.children[1];
            const scoreSpan = findByText(stats, '平均分');
            expect(scoreSpan).toBeDefined();
            expect(scoreSpan!.textContent).toBe('平均分: 3.5/5');
        });

        it('should not render currentScore when undefined', () => {
            const container = createMockElement();
            const relation = createTestRelation({ currentScore: undefined });

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const stats = item.children[1];
            const scoreSpan = findByText(stats, '平均分');
            expect(scoreSpan).toBeUndefined();
        });

        it('should render generatedDate', () => {
            const container = createMockElement();
            const generatedDate = new Date('2026-01-15');
            const relation = createTestRelation({ generatedDate });

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const stats = item.children[1];
            const expectedDateStr = generatedDate.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
            const dateSpan = findByClass(stats, 'verification-stat-date');
            expect(dateSpan).toBeDefined();
            expect(dateSpan!.textContent).toBe(expectedDateStr);
        });

        it('should not render highest score when sessions are empty', () => {
            const container = createMockElement();
            const relation = createTestRelation({ sessions: [], sessionCount: 0 });

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const stats = item.children[1];
            const highestScoreSpan = findByText(stats, '最高分');
            expect(highestScoreSpan).toBeUndefined();
        });

        it('should not render most recent date when sessions are empty', () => {
            const container = createMockElement();
            const relation = createTestRelation({ sessions: [], sessionCount: 0 });

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const stats = item.children[1];
            const recentSpan = findByText(stats, '最近');
            expect(recentSpan).toBeUndefined();
        });
    });

    describe('renderVerificationItem - Delete Button & Click (AC-31.9.5)', () => {
        it('should set up delete button with trash icon and title', () => {
            const container = createMockElement();
            const relation = createTestRelation();

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const deleteBtn = findByClass(item, 'verification-item-delete');
            expect(deleteBtn).toBeDefined();
            expect(mockSetIcon).toHaveBeenCalledWith(deleteBtn, 'trash-2');
            expect(deleteBtn!._attrs['title']).toBe('删除检验白板记录');
        });

        it('should call stopPropagation when delete button is clicked', () => {
            const container = createMockElement();
            const relation = createTestRelation();

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const deleteBtn = findByClass(item, 'verification-item-delete');
            const mockEvent = { stopPropagation: jest.fn() };
            deleteBtn!._listeners['click'][0](mockEvent);
            expect(mockEvent.stopPropagation).toHaveBeenCalled();
        });

        it('should call confirmDeleteVerification when delete button is clicked', () => {
            const container = createMockElement();
            const relation = createTestRelation();
            (view as any).confirmDeleteVerification = jest.fn().mockResolvedValue(undefined);

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            const deleteBtn = findByClass(item, 'verification-item-delete');
            const mockEvent = { stopPropagation: jest.fn() };
            deleteBtn!._listeners['click'][0](mockEvent);
            expect((view as any).confirmDeleteVerification).toHaveBeenCalledWith(relation);
        });

        it('should open verificationCanvasPath on item click', () => {
            const container = createMockElement();
            const relation = createTestRelation({ verificationCanvasPath: 'path/to/test.canvas' });

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            item._listeners['click'][0]();
            expect(view.app.workspace.openLinkText).toHaveBeenCalledWith('path/to/test.canvas', '', false);
        });

        it('should not call openLinkText when verificationCanvasPath is falsy', () => {
            const container = createMockElement();
            const relation = createTestRelation({ verificationCanvasPath: '' as any });

            (view as any).renderVerificationItem(container, relation);

            const item = container.children[0];
            item._listeners['click'][0]();
            expect(view.app.workspace.openLinkText).not.toHaveBeenCalled();
        });
    });

    describe('confirmDeleteVerification - Service Interaction (AC-31.9.4)', () => {
        it('should call deleteRelation when user confirms', async () => {
            const relation = createTestRelation({ id: 'rel-123' });
            view.showConfirmDialog.mockResolvedValue(true);

            await (view as any).confirmDeleteVerification(relation);

            expect(view.verificationService.deleteRelation).toHaveBeenCalledWith('rel-123');
        });

        it('should show success Notice after delete', async () => {
            const relation = createTestRelation();
            view.showConfirmDialog.mockResolvedValue(true);

            await (view as any).confirmDeleteVerification(relation);

            expect(MockNotice).toHaveBeenCalledWith('检验白板记录已删除');
        });

        it('should call loadVerificationData to refresh after delete', async () => {
            const relation = createTestRelation();
            view.showConfirmDialog.mockResolvedValue(true);

            await (view as any).confirmDeleteVerification(relation);

            expect(view.loadVerificationData).toHaveBeenCalled();
        });

        it('should not call deleteRelation when user cancels', async () => {
            const relation = createTestRelation();
            view.showConfirmDialog.mockResolvedValue(false);

            await (view as any).confirmDeleteVerification(relation);

            expect(view.verificationService.deleteRelation).not.toHaveBeenCalled();
        });

        it('should show error Notice when delete fails', async () => {
            const relation = createTestRelation();
            view.showConfirmDialog.mockResolvedValue(true);
            view.verificationService.deleteRelation.mockRejectedValue(new Error('Network error'));

            await (view as any).confirmDeleteVerification(relation);

            expect(MockNotice).toHaveBeenCalledWith('删除失败，请重试');
        });

        it('should pass correct title and message to showConfirmDialog', async () => {
            const relation = createTestRelation({ verificationCanvasTitle: '测试Canvas名' });

            await (view as any).confirmDeleteVerification(relation);

            expect(view.showConfirmDialog).toHaveBeenCalledWith(
                '删除检验白板记录',
                '确定要删除"测试Canvas名"的检验记录吗？此操作不可撤销。'
            );
        });
    });
});
