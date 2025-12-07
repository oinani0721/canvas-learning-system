# Canvas进度追踪系统 - 前端开发技术规范

**版本**: 1.0
**创建日期**: 2025年10月24日
**目标**: 为Dev Agent提供完整的前端开发指导

---

## 📋 项目概述

基于Canvas v2.0系统，开发一个学习进度可视化追踪系统的Web界面，提供实时Canvas监控、学习数据可视化和检验白板关联追踪功能。

### 核心功能模块
1. **实时Canvas监控面板** - 显示Canvas文件状态变化
2. **学习进度可视化** - 图表展示学习进展趋势
3. **检验白板追踪** - 原白板与检验白板关联分析
4. **系统配置管理** - 监控参数和界面设置

---

## 🛠️ 技术栈要求

### 核心框架
- **React 18+** - 主前端框架
- **TypeScript 5+** - 类型安全
- **Vite** - 构建工具
- **Tailwind CSS** - 样式框架
- **Ant Design 5+** - UI组件库

### 数据可视化
- **ECharts 5+** - 主要图表库
- **Recharts** - 备选图表库

### 状态管理和通信
- **React Context + useReducer** - 全局状态管理
- **Socket.IO Client** - 实时数据通信
- **Axios** - HTTP客户端

### 路由和导航
- **React Router v6** - 页面路由

---

## 📁 项目结构

```
canvas-progress-tracker/
├── src/
│   ├── components/           # 可复用组件
│   │   ├── common/          # 通用组件
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   └── Layout.tsx
│   │   ├── charts/          # 图表组件
│   │   │   ├── ProgressChart.tsx
│   │   │   ├── ColorDistributionChart.tsx
│   │   │   └── TrendLineChart.tsx
│   │   └── canvas/          # Canvas相关组件
│   │       ├── CanvasMonitor.tsx
│   │       ├── CanvasCard.tsx
│   │       └── NodeStatusIndicator.tsx
│   ├── pages/               # 页面组件
│   │   ├── Dashboard.tsx    # 主仪表盘
│   │   ├── CanvasDetail.tsx # Canvas详情页
│   │   ├── ReviewBoards.tsx # 检验白板页面
│   │   └── Settings.tsx     # 设置页面
│   ├── hooks/               # 自定义Hooks
│   │   ├── useSocket.ts
│   │   ├── useCanvasData.ts
│   │   └── useLocalStorage.ts
│   ├── services/            # API服务
│   │   ├── canvasService.ts
│   │   ├── reviewBoardService.ts
│   │   └── apiClient.ts
│   ├── types/               # TypeScript类型定义
│   │   ├── canvas.ts
│   │   ├── review.ts
│   │   └── common.ts
│   ├── utils/               # 工具函数
│   │   ├── dateUtils.ts
│   │   ├── formatters.ts
│   │   └── validators.ts
│   └── styles/              # 样式文件
│       ├── globals.css
│       └── components.css
├── public/
├── tests/
│   ├── components/
│   ├── pages/
│   └── utils/
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

---

## 🎨 设计规范

### 颜色系统
```css
/* 主色调 */
--primary-blue: #1890ff;      /* 主要交互色 */
--primary-light: #40a9ff;     /* 悬停状态 */
--primary-dark: #096dd9;      /* 按下状态 */

/* Canvas状态色 */
--color-red: #ff4d4f;         /* 不理解状态 */
--color-purple: #722ed1;      /* 似懂非懂状态 */
--color-green: #52c41a;       /* 完全理解状态 */
--color-blue: #1890ff;        /* AI补充解释 */
--color-yellow: #faad14;      /* 个人理解输出 */

/* 中性色 */
--text-primary: #262626;
--text-secondary: #595959;
--text-disabled: #bfbfbf;
--border-color: #d9d9d9;
--background: #fafafa;
```

### 字体系统
```css
/* 字体族 */
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;

/* 字号层级 */
--text-xs: 12px;    /* 辅助信息 */
--text-sm: 14px;    /* 正文小字 */
--text-base: 16px;  /* 基础正文 */
--text-lg: 18px;    /* 正文大字 */
--text-xl: 20px;    /* 小标题 */
--text-2xl: 24px;   /* 标题 */
--text-3xl: 30px;   /* 大标题 */
```

### 间距系统
```css
/* 间距层级 (基于8px网格) */
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
```

---

## 📊 核心组件规范

### 1. 主仪表盘 (Dashboard.tsx)

#### 功能要求
- 显示所有Canvas文件的状态概览
- 实时更新Canvas状态变化
- 提供快速操作入口
- 展示系统性能指标

#### 布局结构
```tsx
<Dashboard>
  <Header>        // 顶部导航栏
    <UserMenu />
    <SystemStatus />
  </Header>

  <MainContent>
    <OverviewCards>  // 概览卡片
      <TotalCanvasCard />
      <CompletionRateCard />
      <ActiveMonitoringCard />
      <SystemPerformanceCard />
    </OverviewCards>

    <ChartsSection>  // 图表区域
      <ProgressTrendChart />
      <ColorDistributionChart />
    </ChartsSection>

    <RecentActivity>  // 最近活动
      <ActivityList />
    </RecentActivity>
  </MainContent>
</Dashboard>
```

#### 数据需求
```typescript
interface DashboardData {
  overview: {
    totalCanvases: number;
    totalNodes: number;
    averageCompletion: number;
    activeMonitorings: number;
  };
  systemStatus: {
    cpuUsage: number;
    memoryUsage: number;
    diskUsage: number;
    monitoringStatus: 'active' | 'paused' | 'error';
  };
  recentActivities: ActivityItem[];
  progressData: ProgressHistoryItem[];
  colorDistribution: ColorDistribution;
}
```

### 2. Canvas监控组件 (CanvasMonitor.tsx)

#### 功能要求
- 实时显示Canvas文件列表
- 显示每个Canvas的节点状态分布
- 提供启动/停止监控控制
- 支持Canvas文件搜索和筛选

#### 组件接口
```typescript
interface CanvasMonitorProps {
  canvases: CanvasInfo[];
  onToggleMonitoring: (canvasId: string) => void;
  onRefreshCanvas: (canvasId: string) => void;
  loading?: boolean;
}

interface CanvasInfo {
  canvasId: string;
  name: string;
  path: string;
  lastModified: Date;
  monitoring: boolean;
  totalNodes: number;
  nodeStates: {
    red: number;
    purple: number;
    green: number;
    blue: number;
    yellow: number;
  };
  completionRate: number;
}
```

### 3. 进度图表组件 (ProgressChart.tsx)

#### 功能要求
- 显示学习进度趋势线图
- 支持时间范围选择 (7天/30天/90天)
- 显示颜色分布饼图
- 支持数据导出功能

#### 图表配置
```typescript
interface ChartConfig {
  trendChart: {
    xAxis: 'date';
    yAxis: ['completionRate', 'totalNodes'];
    timeRange: '7d' | '30d' | '90d';
    showDataLabels: boolean;
  };
  pieChart: {
    data: 'colorDistribution';
    showLegend: true;
    showPercentage: true;
  };
}
```

---

## 🔌 API集成规范

### API基础配置
```typescript
// src/services/apiClient.ts
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3001/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use((config) => {
  // 添加认证token等
  return config;
});

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // 统一错误处理
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);
```

### Canvas API服务
```typescript
// src/services/canvasService.ts
export class CanvasService {
  // 获取所有Canvas列表
  static async getCanvasList(): Promise<CanvasInfo[]> {
    const response = await apiClient.get('/canvases');
    return response.data;
  }

  // 获取Canvas状态
  static async getCanvasState(canvasId: string): Promise<CanvasState> {
    const response = await apiClient.get(`/canvases/${canvasId}/state`);
    return response.data;
  }

  // 获取进度历史
  static async getProgressHistory(
    canvasId: string,
    timeRange: string
  ): Promise<ProgressHistoryItem[]> {
    const response = await apiClient.get(
      `/canvases/${canvasId}/history?range=${timeRange}`
    );
    return response.data;
  }

  // 启动/停止监控
  static async toggleMonitoring(canvasId: string): Promise<boolean> {
    const response = await apiClient.post(`/canvases/${canvasId}/monitoring/toggle`);
    return response.data.success;
  }
}
```

### 实时通信集成
```typescript
// src/hooks/useSocket.ts
export const useSocket = () => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const newSocket = io(process.env.REACT_APP_SOCKET_URL || 'http://localhost:3001');

    newSocket.on('connect', () => {
      setIsConnected(true);
      console.log('Connected to server');
    });

    newSocket.on('disconnect', () => {
      setIsConnected(false);
      console.log('Disconnected from server');
    });

    newSocket.on('canvas-update', (data: CanvasUpdateEvent) => {
      // 处理Canvas更新事件
      console.log('Canvas update received:', data);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  return { socket, isConnected };
};
```

---

## 📱 响应式设计规范

### 断点定义
```css
/* 断点设置 */
@media (max-width: 640px) { /* Mobile */ }
@media (min-width: 641px) and (max-width: 1024px) { /* Tablet */ }
@media (min-width: 1025px) { /* Desktop */ }
@media (min-width: 1440px) { /* Wide Desktop */ }
```

### 布局适配规则
- **移动端**: 单列布局，折叠侧边栏，简化图表
- **平板端**: 双列布局，可收缩侧边栏，完整图表
- **桌面端**: 三列布局，固定侧边栏，增强交互
- **宽屏**: 最大化内容显示，优化数据密度

---

## ♿ 可访问性要求

### WCAG 2.1 AA 合规
- **颜色对比度**: 文本对比度≥4.5:1，大文本≥3:1
- **键盘导航**: 所有交互元素支持Tab键导航
- **焦点指示器**: 清晰的焦点状态指示
- **屏幕阅读器**: 语义化HTML标签，ARIA标签支持

### 具体实现
```tsx
// 示例：可访问的按钮组件
<button
  type="button"
  className="btn-primary"
  aria-label="启动Canvas监控"
  aria-describedby="monitoring-help"
  disabled={isLoading}
>
  {isLoading ? '启动中...' : '启动监控'}
</button>
<div id="monitoring-help" className="sr-only">
  启动后将实时监控Canvas文件的变化
</div>
```

---

## ⚡ 性能要求

### 加载性能
- **首屏加载时间**: < 3秒
- **交互响应时间**: < 500ms
- **图表渲染时间**: < 2秒
- **实时数据更新延迟**: < 5秒

### 优化策略
- **代码分割**: 路由级别的懒加载
- **组件缓存**: React.memo优化
- **数据缓存**: API响应缓存
- **图片优化**: WebP格式，懒加载
- **Bundle优化**: Tree shaking，压缩

---

## 🧪 测试要求

### 测试覆盖
- **单元测试**: Jest + React Testing Library
- **组件测试**: 关键组件100%覆盖
- **集成测试**: API集成测试
- **E2E测试**: 关键用户流程测试

### 测试文件结构
```
tests/
├── __mocks__/           # Mock文件
├── components/          # 组件测试
│   ├── CanvasMonitor.test.tsx
│   ├── ProgressChart.test.tsx
│   └── Dashboard.test.tsx
├── hooks/              # Hook测试
│   └── useSocket.test.ts
├── services/           # 服务测试
│   └── canvasService.test.ts
└── utils/              # 工具函数测试
    └── dateUtils.test.ts
```

---

## 🚀 部署配置

### 环境变量
```bash
# .env.development
REACT_APP_API_BASE_URL=http://localhost:3001/api
REACT_APP_SOCKET_URL=http://localhost:3001
REACT_APP_ENV=development

# .env.production
REACT_APP_API_BASE_URL=https://api.canvas-tracker.com/api
REACT_APP_SOCKET_URL=https://api.canvas-tracker.com
REACT_APP_ENV=production
```

### 构建配置
```javascript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          antd: ['antd'],
          charts: ['echarts', 'recharts'],
        },
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
    },
  },
});
```

---

## 📋 开发任务清单

### Phase 1: 基础架构 (第1-2周)
- [ ] 项目初始化和基础配置
- [ ] 核心组件库搭建
- [ ] 路由和页面结构
- [ ] API服务层实现
- [ ] 基础样式系统

### Phase 2: 核心功能 (第3-4周)
- [ ] 主仪表盘页面
- [ ] Canvas监控组件
- [ ] 进度图表组件
- [ ] 实时数据集成
- [ ] 响应式布局

### Phase 3: 高级功能 (第5-6周)
- [ ] 检验白板追踪
- [ ] 配置管理界面
- [ ] 数据导出功能
- [ ] 性能优化
- [ ] 错误处理完善

### Phase 4: 测试和优化 (第7周)
- [ ] 单元测试编写
- [ ] 集成测试
- [ ] 性能测试
- [ ] 可访问性测试
- [ ] 用户体验优化

---

## 🎯 关键成功指标

- **功能完整性**: 100%验收标准达成
- **代码质量**: TypeScript严格模式，ESLint无警告
- **测试覆盖率**: >80%代码覆盖率
- **性能指标**: 满足所有性能要求
- **用户体验**: 通过可用性测试

---

**最后更新**: 2025年10月24日
**维护者**: UX Expert (Sally) + Dev Agent (James)

---

## 📞 技术支持

开发过程中如遇到技术问题，请参考：
- Canvas进度追踪系统架构文档
- Canvas v2.0系统API文档
- Ant Design组件文档
- ECharts图表配置文档

记住：所有开发都需要严格遵循TypeScript类型安全，确保代码质量和可维护性。
