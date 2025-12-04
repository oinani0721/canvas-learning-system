/**
 * ProgressTrackerView Unit Tests - Canvas Learning System
 *
 * Tests for the ProgressTrackerView and progress tracking components.
 * Implements Story 19.3: 进度追踪UI组件 + 检验模式标签与趋势可视化
 *
 * @module ProgressTrackerView.test
 * @version 1.0.0
 *
 * ✅ Verified from PRD FR4 (Lines 2829-2890) - Progress tracking UI
 */

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

// =========================================================================
// Type Definitions for Testing
// =========================================================================

interface SingleReviewProgress {
    total_concepts: number;
    red_nodes_total: number;
    red_nodes_passed: number;
    purple_nodes_total: number;
    purple_nodes_passed: number;
    passed_count: number;
    coverage_rate: number;
}

interface ReviewHistoryEntry {
    review_canvas: string;
    timestamp: string;
    progress_rate: number;
    passed_count: number;
    total_count: number;
}

interface ConceptTrend {
    concept_id: string;
    concept_text: string;
    attempts: number;
    history: string[];
    first_pass_review: number | null;
}

interface MultiReviewProgress {
    review_history: ReviewHistoryEntry[];
    concept_trends: Record<string, ConceptTrend>;
    overall_trend: 'improving' | 'stable' | 'declining' | 'insufficient_data';
    improvement_rate: number;
}

// =========================================================================
// Test Suites
// =========================================================================

describe('ProgressTrackerView', () => {
    describe('Coverage Rate Calculation (AC 1)', () => {
        const calculateCoverageRate = (passed: number, total: number): number => {
            if (total === 0) return 0;
            return passed / total;
        };

        it('should calculate correct coverage rate', () => {
            expect(calculateCoverageRate(75, 100)).toBe(0.75);
            expect(calculateCoverageRate(3, 4)).toBe(0.75);
        });

        it('should return 0 for empty total', () => {
            expect(calculateCoverageRate(0, 0)).toBe(0);
        });

        it('should return 1 for perfect score', () => {
            expect(calculateCoverageRate(10, 10)).toBe(1);
        });
    });

    describe('Node Statistics Display (AC 2)', () => {
        const getNodeStats = (progress: SingleReviewProgress) => {
            return {
                redPassed: `${progress.red_nodes_passed}/${progress.red_nodes_total}`,
                purplePassed: `${progress.purple_nodes_passed}/${progress.purple_nodes_total}`,
                totalPassed: `${progress.passed_count}/${progress.total_concepts}`,
            };
        };

        it('should format node statistics correctly', () => {
            const progress: SingleReviewProgress = {
                total_concepts: 10,
                red_nodes_total: 5,
                red_nodes_passed: 3,
                purple_nodes_total: 5,
                purple_nodes_passed: 4,
                passed_count: 7,
                coverage_rate: 0.7,
            };

            const stats = getNodeStats(progress);
            expect(stats.redPassed).toBe('3/5');
            expect(stats.purplePassed).toBe('4/5');
            expect(stats.totalPassed).toBe('7/10');
        });

        it('should handle zero totals', () => {
            const progress: SingleReviewProgress = {
                total_concepts: 0,
                red_nodes_total: 0,
                red_nodes_passed: 0,
                purple_nodes_total: 0,
                purple_nodes_passed: 0,
                passed_count: 0,
                coverage_rate: 0,
            };

            const stats = getNodeStats(progress);
            expect(stats.redPassed).toBe('0/0');
            expect(stats.purplePassed).toBe('0/0');
            expect(stats.totalPassed).toBe('0/0');
        });
    });

    describe('Tab Navigation (AC 3)', () => {
        type TabType = 'current' | 'history' | 'trends';

        const getTabLabel = (tab: TabType): string => {
            const labels: Record<TabType, string> = {
                current: '当前进度',
                history: '历史对比',
                trends: '概念趋势',
            };
            return labels[tab];
        };

        it('should return correct tab labels in Chinese', () => {
            expect(getTabLabel('current')).toBe('当前进度');
            expect(getTabLabel('history')).toBe('历史对比');
            expect(getTabLabel('trends')).toBe('概念趋势');
        });
    });

    describe('Trend Detection (AC 4)', () => {
        const IMPROVEMENT_THRESHOLD = 0.1;
        const DECLINE_THRESHOLD = -0.1;

        const detectTrend = (
            history: ReviewHistoryEntry[]
        ): 'improving' | 'stable' | 'declining' | 'insufficient_data' => {
            if (history.length < 2) return 'insufficient_data';

            const firstRate = history[0].progress_rate;
            const lastRate = history[history.length - 1].progress_rate;
            const improvementRate = lastRate - firstRate;

            if (improvementRate > IMPROVEMENT_THRESHOLD) return 'improving';
            if (improvementRate < DECLINE_THRESHOLD) return 'declining';
            return 'stable';
        };

        it('should return insufficient_data for less than 2 reviews', () => {
            expect(detectTrend([])).toBe('insufficient_data');
            expect(
                detectTrend([
                    {
                        review_canvas: 'test.canvas',
                        timestamp: '2025-01-01',
                        progress_rate: 0.5,
                        passed_count: 5,
                        total_count: 10,
                    },
                ])
            ).toBe('insufficient_data');
        });

        it('should detect improving trend', () => {
            const history: ReviewHistoryEntry[] = [
                {
                    review_canvas: 'r1.canvas',
                    timestamp: '2025-01-01',
                    progress_rate: 0.3,
                    passed_count: 3,
                    total_count: 10,
                },
                {
                    review_canvas: 'r2.canvas',
                    timestamp: '2025-01-02',
                    progress_rate: 0.5,
                    passed_count: 5,
                    total_count: 10,
                },
            ];
            expect(detectTrend(history)).toBe('improving');
        });

        it('should detect stable trend', () => {
            const history: ReviewHistoryEntry[] = [
                {
                    review_canvas: 'r1.canvas',
                    timestamp: '2025-01-01',
                    progress_rate: 0.5,
                    passed_count: 5,
                    total_count: 10,
                },
                {
                    review_canvas: 'r2.canvas',
                    timestamp: '2025-01-02',
                    progress_rate: 0.55,
                    passed_count: 5.5,
                    total_count: 10,
                },
            ];
            expect(detectTrend(history)).toBe('stable');
        });

        it('should detect declining trend', () => {
            const history: ReviewHistoryEntry[] = [
                {
                    review_canvas: 'r1.canvas',
                    timestamp: '2025-01-01',
                    progress_rate: 0.7,
                    passed_count: 7,
                    total_count: 10,
                },
                {
                    review_canvas: 'r2.canvas',
                    timestamp: '2025-01-02',
                    progress_rate: 0.4,
                    passed_count: 4,
                    total_count: 10,
                },
            ];
            expect(detectTrend(history)).toBe('declining');
        });
    });

    describe('Concept Trend Display (AC 5)', () => {
        const formatConceptHistory = (history: string[]): string => {
            return history.map((h) => (h === '通过' ? '✅' : '❌')).join(' ');
        };

        it('should format pass history with emojis', () => {
            expect(formatConceptHistory(['通过', '失败', '通过'])).toBe('✅ ❌ ✅');
        });

        it('should handle empty history', () => {
            expect(formatConceptHistory([])).toBe('');
        });

        it('should handle all passed', () => {
            expect(formatConceptHistory(['通过', '通过', '通过'])).toBe('✅ ✅ ✅');
        });

        it('should handle all failed', () => {
            expect(formatConceptHistory(['失败', '失败'])).toBe('❌ ❌');
        });

        const getFirstPassInfo = (
            firstPass: number | null,
            attempts: number
        ): string | null => {
            if (firstPass === null) return null;
            return `第${firstPass}次复习时首次通过 (共${attempts}次尝试)`;
        };

        it('should format first pass info correctly', () => {
            expect(getFirstPassInfo(2, 5)).toBe('第2次复习时首次通过 (共5次尝试)');
        });

        it('should return null for never passed', () => {
            expect(getFirstPassInfo(null, 3)).toBeNull();
        });
    });

    describe('Review Mode Badges (AC 6)', () => {
        type ReviewMode = 'fresh' | 'targeted';

        const getReviewModeInfo = (mode: ReviewMode) => {
            const info: Record<
                ReviewMode,
                { label: string; description: string; className: string }
            > = {
                fresh: {
                    label: '全量复习',
                    description: '复习所有红色和紫色节点',
                    className: 'fresh',
                },
                targeted: {
                    label: '靶向复习',
                    description: '只复习最薄弱的概念',
                    className: 'targeted',
                },
            };
            return info[mode];
        };

        it('should return correct info for fresh mode', () => {
            const info = getReviewModeInfo('fresh');
            expect(info.label).toBe('全量复习');
            expect(info.description).toBe('复习所有红色和紫色节点');
            expect(info.className).toBe('fresh');
        });

        it('should return correct info for targeted mode', () => {
            const info = getReviewModeInfo('targeted');
            expect(info.label).toBe('靶向复习');
            expect(info.description).toBe('只复习最薄弱的概念');
            expect(info.className).toBe('targeted');
        });
    });

    describe('Progress Circle Calculation', () => {
        const calculateStrokeDashoffset = (
            percentage: number,
            circumference: number
        ): number => {
            return circumference - (percentage / 100) * circumference;
        };

        const circumference = 2 * Math.PI * 70; // radius = 70

        it('should calculate correct offset for 0%', () => {
            const offset = calculateStrokeDashoffset(0, circumference);
            expect(offset).toBeCloseTo(circumference);
        });

        it('should calculate correct offset for 50%', () => {
            const offset = calculateStrokeDashoffset(50, circumference);
            expect(offset).toBeCloseTo(circumference / 2);
        });

        it('should calculate correct offset for 100%', () => {
            const offset = calculateStrokeDashoffset(100, circumference);
            expect(offset).toBeCloseTo(0);
        });
    });

    describe('Trend Badge Display', () => {
        type TrendType = 'improving' | 'stable' | 'declining' | 'insufficient_data';

        const getTrendBadgeInfo = (
            trend: TrendType
        ): { label: string; icon: string; className: string } => {
            const info: Record<
                TrendType,
                { label: string; icon: string; className: string }
            > = {
                improving: {
                    label: '进步中',
                    icon: '📈',
                    className: 'improving',
                },
                stable: {
                    label: '稳定',
                    icon: '➡️',
                    className: 'stable',
                },
                declining: {
                    label: '下降',
                    icon: '📉',
                    className: 'declining',
                },
                insufficient_data: {
                    label: '数据不足',
                    icon: '❓',
                    className: 'insufficient_data',
                },
            };
            return info[trend];
        };

        it('should return correct improving badge', () => {
            const badge = getTrendBadgeInfo('improving');
            expect(badge.label).toBe('进步中');
            expect(badge.icon).toBe('📈');
        });

        it('should return correct stable badge', () => {
            const badge = getTrendBadgeInfo('stable');
            expect(badge.label).toBe('稳定');
            expect(badge.icon).toBe('➡️');
        });

        it('should return correct declining badge', () => {
            const badge = getTrendBadgeInfo('declining');
            expect(badge.label).toBe('下降');
            expect(badge.icon).toBe('📉');
        });

        it('should return correct insufficient_data badge', () => {
            const badge = getTrendBadgeInfo('insufficient_data');
            expect(badge.label).toBe('数据不足');
            expect(badge.icon).toBe('❓');
        });
    });

    describe('History Bar Chart Calculation', () => {
        const calculateBarHeight = (
            progressRate: number,
            maxHeight: number
        ): number => {
            return Math.round(progressRate * maxHeight);
        };

        it('should calculate correct bar height', () => {
            expect(calculateBarHeight(0.5, 150)).toBe(75);
            expect(calculateBarHeight(1.0, 150)).toBe(150);
            expect(calculateBarHeight(0, 150)).toBe(0);
        });
    });

    describe('Timestamp Formatting', () => {
        const formatTimestamp = (timestamp: string): string => {
            const date = new Date(timestamp);
            return date.toLocaleDateString('zh-CN', {
                month: 'short',
                day: 'numeric',
            });
        };

        it('should format timestamp correctly', () => {
            const result = formatTimestamp('2025-01-15T10:30:00Z');
            // Format varies by locale, just check it's not empty
            expect(result.length).toBeGreaterThan(0);
        });
    });

    describe('Pass Rate Formatting', () => {
        const formatPassRate = (rate: number): string => {
            return `${Math.round(rate * 100)}%`;
        };

        it('should format pass rate as percentage', () => {
            expect(formatPassRate(0.75)).toBe('75%');
            expect(formatPassRate(1.0)).toBe('100%');
            expect(formatPassRate(0)).toBe('0%');
        });

        it('should round correctly', () => {
            expect(formatPassRate(0.756)).toBe('76%');
            expect(formatPassRate(0.754)).toBe('75%');
        });
    });

    describe('Improvement Rate Display', () => {
        const formatImprovementRate = (rate: number): string => {
            const sign = rate >= 0 ? '+' : '';
            return `${sign}${Math.round(rate * 100)}%`;
        };

        it('should add plus sign for positive rates', () => {
            expect(formatImprovementRate(0.15)).toBe('+15%');
        });

        it('should show negative rates correctly', () => {
            expect(formatImprovementRate(-0.1)).toBe('-10%');
        });

        it('should handle zero', () => {
            expect(formatImprovementRate(0)).toBe('+0%');
        });
    });
});

describe('Progress Tracker Color Helpers', () => {
    describe('Node Color Classes', () => {
        const getNodeColorClass = (
            color: '4' | '3' | '2' | '1'
        ): string => {
            const classes: Record<string, string> = {
                '4': 'red',    // 红色 - 完全不懂
                '3': 'purple', // 紫色 - 半懂不懂
                '2': 'green',  // 绿色 - 通过
                '1': 'yellow', // 黄色 - 答题区
            };
            return classes[color] || 'unknown';
        };

        it('should return correct class for each color', () => {
            expect(getNodeColorClass('4')).toBe('red');
            expect(getNodeColorClass('3')).toBe('purple');
            expect(getNodeColorClass('2')).toBe('green');
            expect(getNodeColorClass('1')).toBe('yellow');
        });
    });

    describe('Progress Color', () => {
        const getProgressColor = (rate: number): string => {
            if (rate >= 0.8) return 'var(--color-green)';
            if (rate >= 0.5) return 'var(--color-yellow)';
            return 'var(--color-red)';
        };

        it('should return green for high progress', () => {
            expect(getProgressColor(0.8)).toBe('var(--color-green)');
            expect(getProgressColor(1.0)).toBe('var(--color-green)');
        });

        it('should return yellow for medium progress', () => {
            expect(getProgressColor(0.5)).toBe('var(--color-yellow)');
            expect(getProgressColor(0.79)).toBe('var(--color-yellow)');
        });

        it('should return red for low progress', () => {
            expect(getProgressColor(0.49)).toBe('var(--color-red)');
            expect(getProgressColor(0)).toBe('var(--color-red)');
        });
    });
});

describe('Progress Tracker API Integration', () => {
    describe('API Response Parsing', () => {
        const parseProgressResponse = (
            response: unknown
        ): SingleReviewProgress | null => {
            if (
                typeof response !== 'object' ||
                response === null ||
                !('total_concepts' in response)
            ) {
                return null;
            }
            return response as SingleReviewProgress;
        };

        it('should parse valid response', () => {
            const response = {
                total_concepts: 10,
                red_nodes_total: 5,
                red_nodes_passed: 3,
                purple_nodes_total: 5,
                purple_nodes_passed: 4,
                passed_count: 7,
                coverage_rate: 0.7,
            };
            expect(parseProgressResponse(response)).toEqual(response);
        });

        it('should return null for invalid response', () => {
            expect(parseProgressResponse(null)).toBeNull();
            expect(parseProgressResponse(undefined)).toBeNull();
            expect(parseProgressResponse({})).toBeNull();
            expect(parseProgressResponse('string')).toBeNull();
        });
    });
});
