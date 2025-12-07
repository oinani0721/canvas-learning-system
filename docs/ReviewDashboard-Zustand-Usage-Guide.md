# ReviewDashboard Zustand 开发者使用指南

**Story**: 9.8.6.3 - Review状态管理迁移 - Zustand集成
**版本**: v1.0
**最后更新**: 2025-10-26
**维护者**: Canvas Learning System Team

---

## 📋 概述

`ReviewDashboard` 是基于 Zustand 状态管理的复习仪表板组件，集成了 Chart.js 图表库，为用户提供了全面的复习进度可视化管理功能。本文档为开发者提供详细的使用指南和最佳实践。

---

## 🚀 快速开始

### 基础使用

```typescript
import React from 'react';
import { ReviewDashboardZustand } from './components/review/ReviewDashboardZustand';

function App() {
  return (
    <div className="app">
      <ReviewDashboardZustand
        className="custom-dashboard"
        onReviewSessionStart={(session) => {
          console.log('复习会话开始:', session);
        }}
        onCanvasFileSelect={(filePath) => {
          console.log('选择Canvas文件:', filePath);
        }}
      />
    </div>
  );
}
```

### 基本配置

```typescript
// 1. 确保已安装必要依赖
npm install zustand chart.js react-chartjs-2

// 2. 导入必要的样式
import 'tailwindcss'; // 或其他CSS框架

// 3. 确保store已初始化
import { useReviewStore } from './stores/review-store';
```

---

## 🏗️ 架构概览

### 组件层次结构

```
ReviewDashboardZustand
├── ErrorBoundary                    # 错误边界
├── ReviewStatistics                 # 统计信息组件
├── ReviewCharts                     # 图表组件
│   ├── ForgettingCurveChart        # 遗忘曲线图
│   ├── RetentionDistributionChart  # 记忆保持率分布图
│   ├── WeeklyProgressChart         # 本周进度图
│   └── MemoryDistributionChart     # 记忆节点分布图
├── ReviewTaskList                   # 任务列表组件
└── ReviewSessionManager            # 会话管理组件
```

### 状态管理架构

```
Zustand Store (review-store.ts)
├── State (状态)
│   ├── Data State     # 数据状态 (reviewData, statistics)
│   ├── UI State       # UI状态 (isLoading, error)
│   ├── Chart State    # 图表状态 (forgettingCurveData, etc.)
│   └── Session State  # 会话状态 (activeSession)
├── Actions (操作)
│   ├── Data Actions     # 数据操作 (refreshReviewData)
│   ├── Chart Actions    # 图表操作 (updateChartData)
│   ├── Session Actions  # 会话操作 (startReviewSession)
│   └── UI Actions       # UI操作 (setLoading)
└── Computed Properties # 计算属性 (getFilteredTasks)
```

---

## 📊 Hook 使用指南

### useReviewDashboard Hook

主要的集成Hook，提供ReviewDashboard的所有功能：

```typescript
import { useReviewDashboard } from '../hooks/useReviewDashboard';

function MyComponent() {
  const {
    // 状态数据
    reviewData,
    statistics,
    isLoading,
    error,
    lastUpdated,

    // 图表数据
    chartData,

    // 计算数据
    filteredTasks,
    todayTasks,
    overdueTasks,
    completionRate,

    // 操作方法
    handleTaskSelect,
    handleFilterChange,
    handleManualRefresh,

    // 会话管理
    startReviewSession,
    pauseReviewSession,
    completeReviewSession
  } = useReviewDashboard();

  // 自动初始化数据
  useEffect(() => {
    // Hook会自动加载初始数据
  }, []);

  return (
    <div>
      {isLoading && <div>加载中...</div>}
      {error && <div>错误: {error}</div>}

      {/* 使用数据渲染组件 */}
      <div>完成率: {completionRate}%</div>
      <div>今日任务: {todayTasks.length}</div>
    </div>
  );
}
```

### 选择器Hooks

为性能优化提供的细粒度选择器：

```typescript
import {
  useReviewData,
  useReviewStatistics,
  useReviewChartData,
  useFilteredReviewTasks,
  useReviewActions
} from '../stores/review-selectors';

function OptimizedComponent() {
  // 只订阅需要的状态切片
  const reviewData = useReviewData();
  const statistics = useReviewStatistics();
  const chartData = useReviewChartData();
  const filteredTasks = useFilteredReviewTasks();

  // 操作方法选择器
  const { refreshReviewData, setSelectedTask } = useReviewActions();

  return (
    <div>
      <h2>复习数据 ({reviewData?.length} 项)</h2>
      <h3>完成率: {statistics?.completionRate}%</h3>

      <button onClick={refreshReviewData}>
        刷新数据
      </button>
    </div>
  );
}
```

---

## 📈 图表使用指南

### 遗忘曲线图表

基于艾宾浩斯遗忘曲线理论展示记忆保持率：

```typescript
import { useForgettingCurveData } from '../stores/review-selectors';

function ForgettingCurveChart() {
  const forgettingCurveData = useForgettingCurveData();

  const options = {
    responsive: true,
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        title: {
          display: true,
          text: '记忆保持率 (%)'
        }
      },
      x: {
        title: {
          display: true,
          text: '复习间隔 (天)'
        }
      }
    }
  };

  return (
    <div>
      <h3>艾宾浩斯遗忘曲线</h3>
      <Line data={forgettingCurveData} options={options} />
      <p>
        基于您的实际记忆强度数据，显示记忆随时间的衰减规律
      </p>
    </div>
  );
}
```

### 记忆保持率分布图

显示不同记忆强度等级的任务分布：

```typescript
import { useRetentionData } from '../stores/review-selectors';

function RetentionDistributionChart() {
  const retentionData = useRetentionData();

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'right' as const
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((context.parsed / total) * 100).toFixed(1);
            return `${context.label}: ${context.parsed} 项 (${percentage}%)`;
          }
        }
      }
    }
  };

  return (
    <div>
      <h3>记忆强度分布</h3>
      <Doughnut data={retentionData} options={options} />
    </div>
  );
}
```

---

## 🔧 高级用法

### 自定义过滤器

```typescript
function CustomFilters() {
  const { setFilters, filters } = useReviewDashboard();
  const [customFilters, setCustomFilters] = useState({
    difficulty: [1, 2],
    priority: ['urgent'],
    canvasSource: ['math-canvas']
  });

  const applyFilters = () => {
    setFilters(customFilters);
  };

  const clearFilters = () => {
    setFilters({});
  };

  return (
    <div>
      <h3>自定义过滤器</h3>

      {/* 难度过滤 */}
      <select
        multiple
        value={customFilters.difficulty}
        onChange={(e) => {
          const values = Array.from(e.target.selectedOptions, option => Number(option.value));
          setCustomFilters(prev => ({ ...prev, difficulty: values }));
        }}
      >
        <option value={1}>简单</option>
        <option value={2}>中等</option>
        <option value={3}>困难</option>
      </select>

      {/* 优先级过滤 */}
      <select
        multiple
        value={customFilters.priority}
        onChange={(e) => {
          const values = Array.from(e.target.selectedOptions, option => option.value);
          setCustomFilters(prev => ({ ...prev, priority: values }));
        }}
      >
        <option value="urgent">紧急</option>
        <option value="important">重要</option>
        <option value="normal">普通</option>
      </select>

      <button onClick={applyFilters}>应用过滤器</button>
      <button onClick={clearFilters}>清除过滤器</button>
    </div>
  );
}
```

### 搜索功能

```typescript
function TaskSearch() {
  const { setSearchQuery, searchQuery } = useReviewDashboard();

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
  };

  return (
    <div>
      <input
        type="text"
        placeholder="搜索任务概念或Canvas来源..."
        value={searchQuery}
        onChange={handleSearch}
        className="w-full p-2 border rounded"
      />
      {searchQuery && (
        <button onClick={() => setSearchQuery('')}>
          清除搜索
        </button>
      )}
    </div>
  );
}
```

### 会话管理

```typescript
function ReviewSessionControl() {
  const {
    activeSession,
    startReviewSession,
    pauseReviewSession,
    resumeReviewSession,
    completeReviewSession,
    nextTask,
    previousTask,
    filteredTasks
  } = useReviewDashboard();

  const handleStartSession = () => {
    const tasksForSession = filteredTasks.slice(0, 10); // 选择前10个任务
    startReviewSession(tasksForSession);
  };

  if (!activeSession) {
    return (
      <button onClick={handleStartSession}>
        开始复习会话 ({filteredTasks.length} 个任务)
      </button>
    );
  }

  return (
    <div>
      <h3>复习会话进行中</h3>
      <p>任务 {activeSession.currentIndex + 1} / {activeSession.tasks.length}</p>

      <div>
        <button onClick={previousTask} disabled={activeSession.currentIndex === 0}>
          上一个
        </button>
        <button onClick={nextTask} disabled={activeSession.currentIndex === activeSession.tasks.length - 1}>
          下一个
        </button>
      </div>

      <div>
        <button onClick={pauseReviewSession}>
          暂停
        </button>
        <button onClick={resumeReviewSession}>
          继续
        </button>
        <button onClick={completeReviewSession}>
          完成会话
        </button>
      </div>
    </div>
  );
}
```

---

## 🎨 主题定制

### 颜色方案

```typescript
// 在review-store.ts中自定义颜色
const customForgettingCurve = calculateForgettingCurve(tasks);
customForgettingCurve.borderColor = '#your-brand-color';
customForgettingCurve.backgroundColor = 'rgba(your-color, 0.1)';

// 自定义记忆强度等级颜色
const customStrengthRanges = [
  { label: '优秀', min: 80, max: 100, color: '#10b981' },
  { label: '良好', min: 60, max: 79, color: '#3b82f6' },
  { label: '一般', min: 40, max: 59, color: '#f59e0b' },
  { label: '较差', min: 0, max: 39, color: '#ef4444' }
];
```

### 响应式设计

```typescript
function ResponsiveReviewDashboard() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* 在大屏幕上显示3列，小屏幕上显示1列 */}
      <div className="lg:col-span-2">
        <ReviewCharts />
      </div>
      <div>
        <ReviewTaskList />
      </div>
    </div>
  );
}
```

---

## 🔄 数据同步

### 自动刷新

```typescript
function AutoRefreshDashboard() {
  const { refreshStatistics } = useReviewDashboard();

  useEffect(() => {
    // 每30秒自动刷新统计数据
    const interval = setInterval(() => {
      refreshStatistics();
    }, 30000);

    return () => clearInterval(interval);
  }, [refreshStatistics]);

  return <ReviewDashboardZustand />;
}
```

### 手动刷新

```typescript
function ManualRefreshExample() {
  const { handleManualRefresh, isLoading } = useReviewDashboard();

  return (
    <button
      onClick={handleManualRefresh}
      disabled={isLoading}
      className={`
        px-4 py-2 rounded
        ${isLoading
          ? 'bg-gray-300 cursor-not-allowed'
          : 'bg-blue-600 hover:bg-blue-700 text-white'
        }
      `}
    >
      {isLoading ? '刷新中...' : '刷新数据'}
    </button>
  );
}
```

---

## 🧪 测试指南

### 单元测试示例

```typescript
import { renderHook, act, waitFor } from '@testing-library/react';
import { useReviewDashboard } from '../hooks/useReviewDashboard';

// Mock store
jest.mock('../stores/review-store', () => ({
  useReviewStore: () => ({
    reviewData: mockReviewData,
    statistics: mockStatistics,
    isLoading: false,
    error: null,
    refreshReviewData: jest.fn(),
    refreshStatistics: jest.fn(),
    handleTaskSelect: jest.fn(),
    handleFilterChange: jest.fn(),
    handleManualRefresh: jest.fn()
  })
}));

describe('useReviewDashboard', () => {
  it('应该返回正确的初始状态', () => {
    const { result } = renderHook(() => useReviewDashboard());

    expect(result.current.reviewData).toEqual(mockReviewData);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('应该处理手动刷新', async () => {
    const { result } = renderHook(() => useReviewDashboard());
    const mockRefresh = jest.fn();

    await act(async () => {
      await result.current.handleManualRefresh();
    });

    expect(mockRefresh).toHaveBeenCalled();
  });
});
```

### 组件测试示例

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { ReviewDashboardZustand } from '../ReviewDashboardZustand';

describe('ReviewDashboardZustand', () => {
  it('应该渲染仪表板标题', () => {
    render(<ReviewDashboardZustand />);

    expect(screen.getByText('复习仪表板')).toBeInTheDocument();
  });

  it('应该处理刷新按钮点击', () => {
    const mockHandleRefresh = jest.fn();

    render(
      <ReviewDashboardZustand
        onManualRefresh={mockHandleRefresh}
      />
    );

    const refreshButton = screen.getByText('刷新数据');
    fireEvent.click(refreshButton);

    expect(mockHandleRefresh).toHaveBeenCalled();
  });
});
```

---

## ⚡ 性能优化建议

### 使用选择器避免不必要的重渲染

```typescript
// ✅ 好的做法：使用特定选择器
function OptimizedComponent() {
  const chartData = useReviewChartData(); // 只订阅图表数据
  return <div>{/* 只使用图表数据 */}</div>;
}

// ❌ 避免：订阅整个store
function ProblematicComponent() {
  const store = useReviewStore(); // 订阅所有状态
  return <div>{store.chartData.forgettingCurve}</div>;
}
```

### 记忆化计算结果

```typescript
import { useMemo } from 'react';

function ExpensiveCalculation({ tasks }) {
  const expensiveValue = useMemo(() => {
    // 复杂计算逻辑
    return tasks.reduce((sum, task) => sum + task.memoryStrength, 0);
  }, [tasks]);

  return <div>总记忆强度: {expensiveValue}</div>;
}
```

### 延迟加载图表组件

```typescript
import { lazy, Suspense } from 'react';

const ReviewCharts = lazy(() => import('./ReviewCharts'));

function LazyLoadedDashboard() {
  return (
    <Suspense fallback={<div>加载图表中...</div>}>
      <ReviewCharts />
    </Suspense>
  );
}
```

---

## 🐛 常见问题与解决

### Q: 图表不显示数据？

**A:** 检查以下几点：
1. 确保 `reviewData` 不为空
2. 检查 `Chart.js` 是否正确注册
3. 验证数据格式是否符合 Chart.js 要求

```typescript
// 调试代码
const { reviewData, chartData } = useReviewDashboard();
console.log('ReviewData:', reviewData);
console.log('ChartData:', chartData);
```

### Q: 状态更新不生效？

**A:** 确保正确使用 store 的 actions：

```typescript
// ✅ 正确做法
const { setSelectedTask } = useReviewStore();
setSelectedTask(newTask);

// ❌ 错误做法
const store = useReviewStore();
store.selectedTask = newTask; // 不要直接修改状态
```

### Q: 性能问题？

**A:** 使用以下优化策略：

1. 使用 `shallow` 比较避免深度比较
2. 使用细粒度选择器
3. 对昂贵计算使用 `useMemo`
4. 对函数使用 `useCallback`

---

## 📚 API 参考

### ReviewDashboardZustand Props

| Prop | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| className | string | '' | 自定义CSS类名 |
| onReviewSessionStart | (session: any) => void | undefined | 复习会话开始回调 |
| onCanvasFileSelect | (filePath: string) => void | undefined | Canvas文件选择回调 |

### useReviewDashboard 返回值

| 属性 | 类型 | 描述 |
|------|------|------|
| reviewData | ReviewData[] | 复习数据数组 |
| statistics | ReviewStatistics | 统计信息 |
| isLoading | boolean | 加载状态 |
| error | string | 错误信息 |
| chartData | ChartDataBundle | 图表数据包 |
| filteredTasks | ReviewTask[] | 过滤后的任务 |
| todayTasks | ReviewTask[] | 今日任务 |
| overdueTasks | ReviewTask[] | 逾期任务 |
| completionRate | number | 完成率 |
| handleTaskSelect | (task: ReviewTask) => void | 选择任务 |
| handleFilterChange | (filters: Partial<ReviewFilters>) => void | 更新过滤器 |
| handleManualRefresh | () => Promise<void> | 手动刷新 |

---

## 🔗 相关资源

- [Zustand 官方文档](https://docs.pmnd.rs/zustand/)
- [Chart.js React 集成指南](https://www.chartjs.org/docs/latest/developers/react.html)
- [Story 9.8.6.3 完整文档](../stories/story-9.8.6.3-review-state-migration.md)
- [Canvas学习系统架构文档](../architecture/)

---

## 🤝 贡献指南

1. 遵循现有的代码风格和TypeScript最佳实践
2. 为新功能添加适当的JSDoc注释
3. 编写单元测试覆盖新功能
4. 更新此文档以反映API变更

---

**维护者**: Canvas Learning System Team
**最后更新**: 2025-10-26
**版本**: v1.0
