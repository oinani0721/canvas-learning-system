# Epic 9.8.7: 性能和体验优化 (React Query + 代码分割)

## 📋 Epic 概要

**Epic 名称**: 性能和体验优化 - React Query数据缓存与代码分割
**Epic 编号**: 9.8.7
**创建日期**: 2025-10-26
**预计工期**: 2-3周
**优先级**: 高 (P1)
**负责人**: Frontend Team
**依赖关系**: Epic 9.8.6 (基础架构增强)
**Epic 类型**: 性能优化

## 🎯 Epic 目标

在Epic 9.8.6基础上，实施第二阶段的性能优化，通过React Query实现智能数据缓存和管理，结合代码分割和懒加载技术，显著提升应用性能和用户体验。

### 核心目标

1. **数据缓存优化**: 使用React Query实现API数据缓存和同步
2. **代码分割**: 实现路由级和组件级代码分割，减少初始包体积
3. **懒加载机制**: 按需加载组件和资源，提升页面加载速度
4. **用户体验增强**: 优化交互反馈和加载状态，提供流畅体验

## 📊 当前性能基线

### 现有性能指标
- **首次内容绘制 (FCP)**: ~2.8s
- **最大内容绘制 (LCP)**: ~4.2s
- **包体积**: main bundle ~650KB
- **API响应时间**: 平均1.2s
- **页面切换响应**: ~800ms

### 性能瓶颈识别
⚠️ **包体积过大**: Chart.js + Recharts导致初始包体积较大
⚠️ **API重复调用**: 组件级别API调用缺乏缓存机制
⚠️ **全量加载**: 所有组件和资源在启动时全量加载
⚠️ **缺乏优化策略**: 没有预加载和优先级加载机制

## 🏗️ 技术实施方案

### 1. React Query数据缓存系统

#### 1.1 依赖安装和配置
```bash
npm install @tanstack/react-query@^5.17.0
npm install @tanstack/react-query-devtools
```

#### 1.2 Query Client配置
```typescript
// src/lib/query-client.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 数据新鲜度时间 (5分钟)
      staleTime: 5 * 60 * 1000,
      // 缓存时间 (10分钟)
      gcTime: 10 * 60 * 1000,
      // 重试配置
      retry: (failureCount, error: any) => {
        // 4xx错误不重试
        if (error?.status >= 400 && error?.status < 500) {
          return false;
        }
        // 最多重试3次
        return failureCount < 3;
      },
      // 指数退避重试延迟
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
      // 网络状态变化时重新获取
      refetchOnWindowFocus: false,
      // 重新连接时重新获取
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});
```

#### 1.3 数据获取Hooks
```typescript
// src/hooks/useCanvasData.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/api-client';

export const useCanvasList = () => {
  return useQuery({
    queryKey: ['canvas', 'list'],
    queryFn: () => apiClient.get<CanvasFile[]>('/canvas/files'),
    staleTime: 2 * 60 * 1000, // Canvas文件列表相对稳定
  });
};

export const useCanvasFile = (filename: string) => {
  return useQuery({
    queryKey: ['canvas', 'file', filename],
    queryFn: () => apiClient.get<CanvasData>(`/canvas/file/${filename}`),
    enabled: !!filename,
    staleTime: 10 * 60 * 1000, // Canvas内容更稳定
  });
};

export const useCreateCanvas = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateCanvasRequest) =>
      apiClient.post<CanvasFile>('/canvas/create', data),
    onSuccess: (newCanvas) => {
      // 更新Canvas列表缓存
      queryClient.setQueryData(['canvas', 'list'], (old: CanvasFile[] | undefined) =>
        old ? [...old, newCanvas] : [newCanvas]
      );
    },
    onError: (error) => {
      console.error('创建Canvas失败:', error);
    },
  });
};
```

```typescript
// src/hooks/useReviewData.ts
export const useReviewStatistics = () => {
  return useQuery({
    queryKey: ['review', 'statistics'],
    queryFn: () => apiClient.get<ReviewStatistics>('/review/statistics'),
    staleTime: 60 * 1000, // 统计数据变化较频繁
    refetchInterval: 5 * 60 * 1000, // 每5分钟自动刷新
  });
};

export const useReviewSchedule = (days: number = 1) => {
  return useQuery({
    queryKey: ['review', 'schedule', days],
    queryFn: () => apiClient.get<ReviewSchedule>(`/review/schedule?days=${days}`),
    staleTime: 30 * 1000, // 复习计划变化频繁
  });
};

export const useUpdateReviewProgress = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateProgressRequest) =>
      apiClient.post<ReviewProgress>('/review/progress', data),
    onSuccess: () => {
      // 失效相关缓存
      queryClient.invalidateQueries({ queryKey: ['review', 'statistics'] });
      queryClient.invalidateQueries({ queryKey: ['review', 'schedule'] });
    },
  });
};
```

```typescript
// src/hooks/useCommandData.ts
export const useCommandHistory = (limit: number = 50) => {
  return useQuery({
    queryKey: ['command', 'history', limit],
    queryFn: () => apiClient.get<CommandHistoryItem[]>(`/command/history?limit=${limit}`),
    staleTime: 60 * 60 * 1000, // 历史记录基本不变
  });
};

export const useExecuteCommand = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (command: ExecuteCommandRequest) =>
      apiClient.post<CommandResult>('/command/execute', command),
    onSuccess: () => {
      // 更新命令历史缓存
      queryClient.invalidateQueries({ queryKey: ['command', 'history'] });
    },
  });
};
```

### 2. 代码分割架构

#### 2.1 路由级代码分割
```typescript
// src/pages/index.ts
import { lazy } from 'react';

// 路由级懒加载
export const CanvasPage = lazy(() => import('./CanvasPage').then(module => ({
  default: module.CanvasPage
})));

export const ReviewPage = lazy(() => import('./ReviewPage').then(module => ({
  default: module.ReviewPage
})));

export const CommandPage = lazy(() => import('./CommandPage').then(module => ({
  default: module.CommandPage
})));

export const SettingsPage = lazy(() => import('./SettingsPage').then(module => ({
  default: module.SettingsPage
})));
```

#### 2.2 应用路由配置
```typescript
// src/App.tsx
import { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from '@/lib/query-client';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { PageLayout } from '@/components/layout/PageLayout';

import { CanvasPage, ReviewPage, CommandPage, SettingsPage } from './pages';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <Router>
          <PageLayout>
            <Suspense fallback={<LoadingSpinner size="large" />}>
              <Routes>
                <Route path="/canvas" element={<CanvasPage />} />
                <Route path="/review" element={<ReviewPage />} />
                <Route path="/command" element={<CommandPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/" element={<CanvasPage />} />
              </Routes>
            </Suspense>
          </PageLayout>
        </Router>
      </ErrorBoundary>

      {/* 开发环境调试工具 */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}

export default App;
```

#### 2.3 组件级代码分割
```typescript
// src/components/charts/ChartComponents.ts
import { lazy } from 'react';

// 图表组件懒加载
export const ReviewProgressChart = lazy(() =>
  import('./ReviewProgressChart').then(module => ({
    default: module.ReviewProgressChart
  }))
);

export const EbbinghausCurveChart = lazy(() =>
  import('./EbbinghausCurveChart').then(module => ({
    default: module.EbbinghausCurveChart
  }))
);

export const CommandUsageChart = lazy(() =>
  import('./CommandUsageChart').then(module => ({
    default: module.CommandUsageChart
  }))
);
```

```typescript
// src/components/review/ReviewDashboard.tsx
import { useState, Suspense } from 'react';
import { ReviewProgressChart, EbbinghausCurveChart } from '@/components/charts/ChartComponents';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';

const ReviewDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'progress' | 'curve' | 'stats'>('progress');

  return (
    <div className="review-dashboard">
      <div className="tab-navigation">
        <button
          onClick={() => setActiveTab('progress')}
          className={activeTab === 'progress' ? 'active' : ''}
        >
          复习进度
        </button>
        <button
          onClick={() => setActiveTab('curve')}
          className={activeTab === 'curve' ? 'active' : ''}
        >
          艾宾浩斯曲线
        </button>
        <button
          onClick={() => setActiveTab('stats')}
          className={activeTab === 'stats' ? 'active' : ''}
        >
          统计数据
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'progress' && (
          <Suspense fallback={<LoadingSpinner />}>
            <ReviewProgressChart />
          </Suspense>
        )}

        {activeTab === 'curve' && (
          <Suspense fallback={<LoadingSpinner />}>
            <EbbinghausCurveChart />
          </Suspense>
        )}

        {activeTab === 'stats' && (
          <ReviewStatistics />
        )}
      </div>
    </div>
  );
};
```

### 3. 智能预加载系统

#### 3.1 预加载策略
```typescript
// src/hooks/usePrefetch.ts
import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

export const usePrefetchData = () => {
  const queryClient = useQueryClient();

  // 预加载常用数据
  useEffect(() => {
    // 用户空闲时预加载
    const prefetchOnIdle = () => {
      if ('requestIdleCallback' in window) {
        requestIdleCallback(() => {
          // 预加载Canvas列表
          queryClient.prefetchQuery({
            queryKey: ['canvas', 'list'],
            queryFn: () => apiClient.get('/canvas/files'),
            staleTime: 2 * 60 * 1000,
          });

          // 预加载复习统计
          queryClient.prefetchQuery({
            queryKey: ['review', 'statistics'],
            queryFn: () => apiClient.get('/review/statistics'),
            staleTime: 60 * 1000,
          });
        });
      }
    };

    // 页面加载完成后延迟预加载
    const timer = setTimeout(prefetchOnIdle, 2000);
    return () => clearTimeout(timer);
  }, [queryClient]);
};

// 路由预加载Hook
export const useRoutePrefetch = () => {
  const queryClient = useQueryClient();

  const prefetchRouteData = (route: string) => {
    switch (route) {
      case '/review':
        queryClient.prefetchQuery({
          queryKey: ['review', 'statistics'],
          queryFn: () => apiClient.get('/review/statistics'),
        });
        queryClient.prefetchQuery({
          queryKey: ['review', 'schedule', 7],
          queryFn: () => apiClient.get('/review/schedule?days=7'),
        });
        break;
      case '/command':
        queryClient.prefetchQuery({
          queryKey: ['command', 'history', 50],
          queryFn: () => apiClient.get('/command/history?limit=50'),
        });
        break;
    }
  };

  return { prefetchRouteData };
};
```

#### 3.2 智能组件预加载
```typescript
// src/components/common/SmartLoader.tsx
interface SmartLoaderProps {
  component: React.ComponentType;
  fallback?: React.ReactNode;
  preloadOnHover?: boolean;
  preloadDelay?: number;
}

const SmartLoader: React.FC<SmartLoaderProps> = ({
  component: Component,
  fallback = <LoadingSpinner />,
  preloadOnHover = true,
  preloadDelay = 100
}) => {
  const [LazyComponent, setLazyComponent] = useState<React.ComponentType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const preloadTimeoutRef = useRef<NodeJS.Timeout>();

  const loadComponent = useCallback(() => {
    if (!LazyComponent) {
      setIsLoading(true);
      // 动态导入组件
      import('./ComponentToLoad').then(module => {
        setLazyComponent(() => module.default);
        setIsLoading(false);
      });
    }
  }, [LazyComponent]);

  const handleMouseEnter = useCallback(() => {
    if (preloadOnHover && !LazyComponent) {
      preloadTimeoutRef.current = setTimeout(loadComponent, preloadDelay);
    }
  }, [loadComponent, preloadOnHover, preloadDelay, LazyComponent]);

  const handleMouseLeave = useCallback(() => {
    if (preloadTimeoutRef.current) {
      clearTimeout(preloadTimeoutRef.current);
    }
  }, []);

  if (LazyComponent) {
    return <LazyComponent />;
  }

  if (isLoading) {
    return fallback;
  }

  return (
    <div onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave}>
      {fallback}
    </div>
  );
};
```

### 4. 性能监控和优化

#### 4.1 性能指标监控
```typescript
// src/utils/performance-monitor.ts
export interface PerformanceMetrics {
  fcp: number; // First Contentful Paint
  lcp: number; // Largest Contentful Paint
  fid: number; // First Input Delay
  cls: number; // Cumulative Layout Shift
  bundleSize: number;
  apiResponseTime: number;
}

class PerformanceMonitor {
  private metrics: Partial<PerformanceMetrics> = {};
  private observers: PerformanceObserver[] = [];

  startMonitoring() {
    // FCP监控
    this.observeFCP();

    // LCP监控
    this.observeLCP();

    // FID监控
    this.observeFID();

    // CLS监控
    this.observeCLS();

    // API响应时间监控
    this.monitorAPICalls();
  }

  private observeFCP() {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const fcpEntry = entries.find(entry => entry.name === 'first-contentful-paint');
      if (fcpEntry) {
        this.metrics.fcp = fcpEntry.startTime;
        console.log('FCP:', this.metrics.fcp);
      }
    });
    observer.observe({ entryTypes: ['paint'] });
    this.observers.push(observer);
  }

  private observeLCP() {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lcpEntry = entries[entries.length - 1]; // 最大的LCP元素
      if (lcpEntry) {
        this.metrics.lcp = lcpEntry.startTime;
        console.log('LCP:', this.metrics.lcp);
      }
    });
    observer.observe({ entryTypes: ['largest-contentful-paint'] });
    this.observers.push(observer);
  }

  private observeFID() {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach(entry => {
        if (entry.entryType === 'first-input') {
          this.metrics.fid = (entry as PerformanceEventTiming).processingStart - entry.startTime;
          console.log('FID:', this.metrics.fid);
        }
      });
    });
    observer.observe({ entryTypes: ['first-input'] });
    this.observers.push(observer);
  }

  private observeCLS() {
    let clsValue = 0;
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach(entry => {
        if (entry.entryType === 'layout-shift' && !(entry as any).hadRecentInput) {
          clsValue += (entry as any).value;
        }
      });
      this.metrics.cls = clsValue;
      console.log('CLS:', this.metrics.cls);
    });
    observer.observe({ entryTypes: ['layout-shift'] });
    this.observers.push(observer);
  }

  private monitorAPICalls() {
    // 监控fetch请求
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const start = performance.now();
      try {
        const response = await originalFetch(...args);
        const duration = performance.now() - start;
        this.recordAPIMetrics(duration);
        return response;
      } catch (error) {
        const duration = performance.now() - start;
        this.recordAPIMetrics(duration);
        throw error;
      }
    };
  }

  private recordAPIMetrics(duration: number) {
    if (!this.metrics.apiResponseTime || duration > this.metrics.apiResponseTime) {
      this.metrics.apiResponseTime = duration;
    }
  }

  getMetrics(): Partial<PerformanceMetrics> {
    return { ...this.metrics };
  }

  stopMonitoring() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

export const performanceMonitor = new PerformanceMonitor();
```

#### 4.2 Bundle分析和优化
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        // 手动代码分割
        manualChunks: {
          // React核心库
          'react-vendor': ['react', 'react-dom'],

          // 图表库 (单独分包)
          'charts': ['chart.js', 'react-chartjs-2', 'recharts'],

          // 路由库
          'router': ['react-router-dom'],

          // 状态管理
          'state': ['zustand', '@tanstack/react-query'],

          // 工具库
          'utils': ['date-fns', 'lodash-es'],

          // Canvas相关
          'canvas': ['fabric'], // 如果使用fabric.js
        },
      },
    },

    // 优化配置
    minify: 'terser',
    sourcemap: false,

    // 分包大小限制
    chunkSizeWarningLimit: 1000,

    // 性能优化
    target: 'es2020',
  },

  plugins: [
    // Bundle分析插件
    visualizer({
      filename: 'dist/stats.html',
      open: true,
      gzipSize: true,
    }),
  ],
});
```

## 📋 任务分解

### Sprint 1: React Query集成 (1周)

#### Story 9.8.7.1: React Query基础设置
- **任务**: 安装React Query，配置Query Client和开发工具
- **验收标准**:
  - @tanstack/react-query 5.17.0成功安装
  - Query Client正确配置
  - React Query Devtools集成
  - 全局缓存策略配置完成

#### Story 9.8.7.2: Canvas数据Hooks开发
- **任务**: 创建Canvas相关的数据获取Hooks
- **验收标准**:
  - useCanvasList Hook实现
  - useCanvasFile Hook实现
  - useCreateCanvas Hook实现
  - 缓存策略正确配置

#### Story 9.8.7.3: Review数据Hooks开发
- **任务**: 创建Review相关的数据获取Hooks
- **验收标准**:
  - useReviewStatistics Hook实现
  - useReviewSchedule Hook实现
  - useUpdateReviewProgress Hook实现
  - 自动刷新机制工作正常

#### Story 9.8.7.4: Command数据Hooks开发
- **任务**: 创建Command相关的数据获取Hooks
- **验收标准**:
  - useCommandHistory Hook实现
  - useExecuteCommand Hook实现
  - 命令执行缓存正确处理
  - 错误重试机制工作正常

### Sprint 2: 代码分割实现 (1-1.5周)

#### Story 9.8.7.5: 路由级代码分割
- **任务**: 实现页面级代码分割和懒加载
- **验收标准**:
  - 所有页面组件改为懒加载
  - Suspense边界正确设置
  - Loading状态友好展示
  - 包体积减少 >20%

#### Story 9.8.7.6: 组件级代码分割
- **任务**: 实现重型组件的代码分割
- **验收标准**:
  - 图表组件懒加载实现
  - Command组件按需加载
  - 动态导入性能优化
  - 组件切换响应时间 <200ms

#### Story 9.8.7.7: 智能预加载系统
- **任务**: 实现数据预加载和组件预加载
- **验收标准**:
  - 用户空闲时预加载数据
  - 路由切换时预加载组件
  - Hover时智能预加载
  - 预加载策略可配置

### Sprint 3: 性能监控和优化 (0.5-1周)

#### Story 9.8.7.8: 性能监控系统
- **任务**: 建立完整的性能监控体系
- **验收标准**:
  - Core Web Vitals监控实现
  - API响应时间监控
  - Bundle大小分析
  - 性能数据上报机制

#### Story 9.8.7.9: 性能优化和调优
- **任务**: 基于监控数据进行性能优化
- **验收标准**:
  - FCP < 2s
  - LCP < 3s
  - FID < 100ms
  - CLS < 0.1

#### Story 9.8.7.10: 集成测试和验证
- **任务**: 完成性能优化集成测试
- **验收标准**:
  - 所有现有功能正常
  - 性能指标达标
  - 用户体验显著改善
  - 性能监控正常运行

## 🔧 技术要求

### 新增依赖包
```json
{
  "dependencies": {
    "@tanstack/react-query": "^5.17.0",
    "@tanstack/react-query-devtools": "^5.17.0",
    "react-router-dom": "^6.20.1"
  },
  "devDependencies": {
    "rollup-plugin-visualizer": "^5.9.2",
    "vite": "^5.0.0"
  }
}
```

### 构建配置
- Vite配置优化
- 代码分割策略
- Bundle分析和监控
- 资源压缩和优化

### 性能标准
- FCP < 2s
- LCP < 3s
- FID < 100ms
- CLS < 0.1
- 包体积减少 >20%

## 🎯 验收标准

### 功能验收
- [ ] React Query缓存机制正常工作
- [ ] 代码分割不影响功能完整性
- [ ] 懒加载体验流畅
- [ ] 预加载策略有效
- [ ] 性能监控数据准确

### 性能验收
- [ ] 页面加载速度提升 >30%
- [ ] API响应时间减少 >40%
- [ ] 包体积减少 >20%
- [ ] 内存使用稳定
- [ ] 切换响应时间 <200ms

### 用户体验验收
- [ ] 加载状态友好
- [ ] 无明显白屏时间
- [ ] 交互响应及时
- [ ] 错误处理完善
- [ ] 移动端体验良好

## 🚨 风险评估

### 高风险
- **React Query学习成本**: 团队需要学习新的数据管理方式
- **缓存一致性问题**: 可能出现数据不一致的情况

### 中风险
- **代码分割复杂性**: 可能引入新的bug和边界情况
- **性能回归**: 优化可能影响现有功能性能

### 缓解措施
- 详细的React Query使用文档和最佳实践
- 完整的测试覆盖，特别是缓存场景
- 渐进式实施，每步充分验证
- 性能基准测试和监控

## 📚 相关文档

- [Epic 9.8.6: 前端基础架构增强](./epic-9.8.6-frontend-architecture-enhancement.md)
- [Epic 9.8.8: 高级功能实现](./epic-9.8.8-advanced-features.md)
- [React Query官方文档](https://tanstack.com/query/latest)
- [代码分割最佳实践](https://web.dev/code-splitting-suspense/)
- [Web Performance Best Practices](https://web.dev/performance/)

## 📊 成功指标

### 性能指标
- 页面加载时间减少 >30%
- API响应时间减少 >40%
- 包体积减少 >20%
- 首屏渲染时间 <2s

### 用户体验指标
- 用户操作响应时间 <200ms
- 页面切换无卡顿
- 加载状态友好
- 错误恢复时间 <1s

### 开发效率指标
- 组件开发效率提升 20%
- Bug调试时间减少 30%
- 代码维护成本降低 25%
- 新功能开发速度提升 15%

---

**Epic 9.8.7 性能和体验优化**将通过React Query智能缓存和代码分割技术，显著提升Canvas Learning System的性能表现，为用户提供更流畅的学习体验。这是实现高性能前端应用的关键优化阶段。 🚀