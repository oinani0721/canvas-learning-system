# Story 9.8.6.4: Command状态管理迁移

**文件位置**: `docs/stories/story-9.8.6.4-command-state-migration.story.md`

**创建日期**: 2025-10-26
**作者**: Frontend Team
**预计工期**: 1-2天
**优先级**: P1 (High)
**Epic**: 9.8.6 前端基础架构增强
**Sprint**: Sprint 1: Zustand集成
**依赖**: Story 9.8.6.1 (Zustand基础设置) ✅

---

## 📋 Story 概要

将CommandExecutorComponent从复杂的useState状态管理模式迁移到基于Zustand的统一状态管理。通过重构组件状态管理逻辑，利用command-store处理命令执行生命周期、历史记录、收藏管理、异步执行等复杂状态，提升组件的可维护性、性能和用户体验。

**关键价值**: 解决CommandExecutorComponent中15+个useState的复杂状态管理问题，通过Zustand实现可预测的状态更新、更好的性能优化和持久化支持。

---

## 🎯 验收标准

### 功能验收标准
- [ ] **状态迁移完整**: 所有CommandExecutorComponent状态成功迁移到command-store
- [ ] **异步命令执行**: executeCommand方法正确处理异步执行和状态更新
- [ ] **历史记录管理**: 命令历史自动保存到localStorage，支持100条记录限制
- [ ] **收藏功能**: 命令收藏状态持久化，支持toggle操作
- [ ] **执行状态管理**: isExecuting状态在命令执行期间正确更新UI
- [ ] **参数管理**: 命令参数状态与表单输入双向绑定
- [ ] **结果处理**: 执行结果正确存储并显示在输出组件中
- [ ] **上下文管理**: ExecutionContext状态正确传递和管理

### 技术验收标准
- [ ] **TypeScript类型安全**: 所有Store操作类型严格，无any类型
- [ ] **性能优化**: 减少不必要的重渲染，使用选择器模式
- [ ] **持久化集成**: localStorage自动同步，错误处理完善
- [ ] **异步操作处理**: Promise/async-await模式正确实现
- [ ] **错误边界**: Store操作错误不影响组件渲染
- [ ] **测试覆盖**: Store操作和组件交互100%测试覆盖

### 用户体验验收标准
- [ ] **响应性**: 命令执行状态实时反映在UI上
- [ ] **数据持久化**: 刷新页面后历史记录和收藏状态保持
- [ ] **流畅交互**: 状态更新无闪烁，UI响应迅速
- [ ] **错误处理**: 执行失败时显示友好错误信息
- [ ] **向后兼容**: 现有功能保持不变，用户无感知迁移

---

## 🏗️ 技术实现详情

### 1. 当前状态复杂度分析

#### 1.1 CommandExecutorComponent状态统计

```typescript
// 当前组件中的状态管理 (15+个状态)
const CommandExecutorComponent: React.FC<CommandExecutorProps> = (props) => {
  // Services (2个)
  const [registryService] = useState(() => new CommandRegistryService());
  const [executionEngine] = useState(() => new CommandExecutionEngine());

  // 核心状态 (9个)
  const [state, setState] = useState<CommandExecutorState>({
    selectedCommand: null,           // 选中的命令
    parameters: {},                  // 命令参数
    isExecuting: false,              // 执行状态
    executionHistory: [],            // 执行历史
    favoriteCommands: new Set(),     // 收藏命令
    lastResult: null,                // 最后执行结果
    availableCommands: [],           // 可用命令列表
    filter: {},                      // 过滤条件
    context: {...}                   // 执行上下文
  });

  // UI状态 (4个)
  const [activeTab, setActiveTab] = useState<'discover' | 'execute' | 'history'>('discover');
  const [showCommandList, setShowCommandList] = useState(true);
  const [executionProgress, setExecutionProgress] = useState<any>(null);
  const [parameterValidation, setParameterValidation] = useState({ isValid: true, errors: [] });

  // 总计: 15个独立状态管理单元
};
```

#### 1.2 状态管理问题分析

**复杂性指标**:
- **状态数量**: 15个独立状态单元
- **状态更新频率**: 每次用户交互触发多个状态更新
- **依赖关系**: 状态间存在复杂依赖 (parameters → parameterValidation → isExecuteDisabled)
- **持久化需求**: executionHistory, favoriteCommands需要localStorage
- **异步操作**: executeCommand涉及6个状态同步更新

**性能问题**:
- 每次setState导致整个组件重渲染
- 大对象状态更新造成内存浪费
- 历史记录增长影响渲染性能
- 无选择器优化，子组件不必要的重渲染

### 2. 扩展Command Store实现

#### 2.1 增强的Command Store接口

**文件**: `src/stores/command-store.ts`

```typescript
import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import {
  CommandState,
  CommandStoreActions,
  CommandExecutorState,
  CommandExecutionRequest,
  CommandExecutionResult,
  CommandHistoryItem,
  CommandMetadata,
  ExecutionContext,
  CommandFilter
} from './types/command.types';
import { CommandRegistryService } from '../components/command/CommandRegistryService';
import { CommandExecutionEngine } from '../components/command/CommandExecutionEngine';

interface CommandStore extends CommandState, CommandStoreActions {
  // 扩展状态
  availableCommands: CommandMetadata[];
  currentParameters: Record<string, any>;
  selectedCommand: CommandMetadata | null;
  executionProgress: any;
  parameterValidation: {
    isValid: boolean;
    errors: string[];
  };

  // UI状态
  activeTab: 'discover' | 'execute' | 'history';
  showCommandList: boolean;

  // 计算属性
  isExecuteDisabled: boolean;
  recentCommands: CommandHistoryItem[];
  favoriteCommandsArray: string[];

  // 高级操作
  initializeCommands: () => Promise<void>;
  selectCommand: (command: CommandMetadata) => void;
  updateParameters: (parameters: Record<string, any>) => void;
  executeCommandWithRequest: (request?: CommandExecutionRequest) => Promise<CommandExecutionResult>;
  validateParameters: (command: CommandMetadata, parameters: Record<string, any>) => void;
  setExecutionProgress: (progress: any) => void;
  clearExecutionProgress: () => void;
  exportHistory: () => void;
  exportOutput: (format: 'json' | 'markdown' | 'csv') => void;
  shareOutput: () => void;
}

const useCommandStore = create<CommandStore>()(
  subscribeWithSelector(
    devtools(
      persist(
        (set, get) => ({
          // 初始状态 (合并原有和新增)
          commandHistory: [],
          favorites: new Set(),
          isExecuting: false,
          currentCommand: null,
          executionResult: null,

          // 新增状态
          availableCommands: [],
          currentParameters: {},
          selectedCommand: null,
          executionProgress: null,
          parameterValidation: { isValid: true, errors: [] },
          activeTab: 'discover',
          showCommandList: true,

          // 计算属性 (getter)
          get isExecuteDisabled() {
            const { selectedCommand, isExecuting, parameterValidation } = get();
            return !selectedCommand || isExecuting || !parameterValidation.isValid;
          },

          get recentCommands() {
            return get().commandHistory.slice(0, 5);
          },

          get favoriteCommandsArray() {
            return Array.from(get().favorites);
          },

          // 核心操作方法
          initializeCommands: async () => {
            try {
              const registryService = new CommandRegistryService();
              const commands = registryService.getAllCommands();

              set({
                availableCommands: commands,
                error: null
              }, false, 'initializeCommands');
            } catch (error) {
              set({
                error: error instanceof Error ? error.message : 'Failed to load commands'
              }, false, 'initializeCommands-error');
            }
          },

          selectCommand: (command: CommandMetadata) => {
            set({
              selectedCommand: command,
              currentParameters: {},
              executionResult: null,
              parameterValidation: { isValid: true, errors: [] },
              activeTab: 'execute',
              showCommandList: false
            }, false, 'selectCommand');
          },

          updateParameters: (parameters: Record<string, any>) => {
            const { selectedCommand } = get();
            set({ currentParameters: parameters }, false, 'updateParameters');

            // 验证参数
            if (selectedCommand) {
              get().validateParameters(selectedCommand, parameters);
            }
          },

          validateParameters: (command: CommandMetadata, parameters: Record<string, any>) => {
            const errors: string[] = [];

            command.parameters.forEach(param => {
              const value = parameters[param.name];

              // 必填验证
              if (param.required && (value === undefined || value === null || value === '')) {
                errors.push(`${param.name} is required`);
                return;
              }

              // 类型验证
              if (value !== undefined && value !== null) {
                switch (param.type) {
                  case 'number':
                    if (isNaN(Number(value))) {
                      errors.push(`${param.name} must be a number`);
                    }
                    break;
                  case 'boolean':
                    if (typeof value !== 'boolean') {
                      errors.push(`${param.name} must be a boolean`);
                    }
                    break;
                  case 'string':
                    if (typeof value !== 'string') {
                      errors.push(`${param.name} must be a string`);
                    } else if (param.validation) {
                      const { minLength, maxLength, pattern } = param.validation;
                      if (minLength && value.length < minLength) {
                        errors.push(`${param.name} must be at least ${minLength} characters`);
                      }
                      if (maxLength && value.length > maxLength) {
                        errors.push(`${param.name} must be at most ${maxLength} characters`);
                      }
                      if (pattern && !new RegExp(pattern).test(value)) {
                        errors.push(`${param.name} format is invalid`);
                      }
                    }
                    break;
                }
              }
            });

            set({
              parameterValidation: {
                isValid: errors.length === 0,
                errors
              }
            }, false, 'validateParameters');
          },

          executeCommandWithRequest: async (request?: CommandExecutionRequest) => {
            const { selectedCommand, currentParameters, currentCommand } = get();

            if (!selectedCommand && !currentCommand) {
              throw new Error('No command selected for execution');
            }

            const actualRequest: CommandExecutionRequest = request || {
              commandName: selectedCommand!.name,
              parameters: currentParameters,
              context: get().executionContext
            };

            // 设置执行状态
            set({
              isExecuting: true,
              currentCommand: actualRequest.commandName,
              executionResult: null,
              executionProgress: null
            }, false, 'executeCommand-start');

            try {
              const executionEngine = new CommandExecutionEngine();

              // 设置进度监听
              const executionId = `exec_${Date.now()}`;
              executionEngine.addEventListener(executionId, (event) => {
                if (event.type === 'progress') {
                  get().setExecutionProgress(event.data);
                }
              });

              // 执行命令
              const result = await executionEngine.executeCommand(actualRequest);

              // 创建历史记录
              const historyItem: CommandHistoryItem = {
                id: result.metadata?.executionId || `hist_${Date.now()}`,
                commandName: actualRequest.commandName,
                command: actualRequest.commandName + Object.entries(actualRequest.parameters)
                  .filter(([_, v]) => v !== undefined && v !== null && v !== '')
                  .map(([k, v]) => ` --${k} ${v}`)
                  .join(''),
                parameters: actualRequest.parameters,
                result,
                timestamp: new Date(),
                executionTime: result.executionTime,
                success: result.success,
                favorited: get().favorites.has(actualRequest.commandName),
                tags: selectedCommand?.tags || []
              };

              // 更新状态
              set((state) => ({
                isExecuting: false,
                executionResult: result,
                commandHistory: [historyItem, ...state.commandHistory].slice(0, 100),
                executionProgress: null
              }), false, 'executeCommand-success');

              return result;

            } catch (error) {
              const errorResult: CommandExecutionResult = {
                success: false,
                output: {
                  raw: `Execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
                  format: 'error_message'
                },
                executionTime: 0,
                timestamp: new Date(),
                command: actualRequest.commandName,
                parameters: actualRequest.parameters,
                error: {
                  code: 'EXECUTION_FAILED',
                  message: error instanceof Error ? error.message : 'Unknown error',
                  recoverable: true
                }
              };

              set({
                isExecuting: false,
                executionResult: errorResult,
                executionProgress: null
              }, false, 'executeCommand-error');

              throw error;
            }
          },

          setExecutionProgress: (progress: any) => {
            set({ executionProgress: progress }, false, 'setExecutionProgress');
          },

          clearExecutionProgress: () => {
            set({ executionProgress: null }, false, 'clearExecutionProgress');
          },

          toggleFavorite: (commandName: string) => {
            set((state) => {
              const newFavorites = new Set(state.favorites);
              if (newFavorites.has(commandName)) {
                newFavorites.delete(commandName);
              } else {
                newFavorites.add(commandName);
              }
              return { favorites: newFavorites };
            }, false, 'toggleFavorite');
          },

          setActiveTab: (tab: 'discover' | 'execute' | 'history') => {
            set({ activeTab: tab }, false, 'setActiveTab');
          },

          setShowCommandList: (show: boolean) => {
            set({ showCommandList: show }, false, 'setShowCommandList');
          },

          clearHistory: () => {
            set({ commandHistory: [] }, false, 'clearHistory');
          },

          deleteHistoryItem: (itemId: string) => {
            set((state) => ({
              commandHistory: state.commandHistory.filter(item => item.id !== itemId)
            }), false, 'deleteHistoryItem');
          },

          exportHistory: () => {
            const { commandHistory } = get();
            const historyData = {
              exportDate: new Date().toISOString(),
              totalCommands: commandHistory.length,
              commands: commandHistory.map(item => ({
                command: item.command,
                commandName: item.commandName,
                parameters: item.parameters,
                timestamp: item.timestamp,
                executionTime: item.executionTime,
                success: item.success,
                tags: item.tags
              }))
            };

            const blob = new Blob([JSON.stringify(historyData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `command-history-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
          },

          exportOutput: (format: 'json' | 'markdown' | 'csv') => {
            const { executionResult } = get();
            if (!executionResult) return;

            let content = '';
            let filename = '';
            let mimeType = '';

            switch (format) {
              case 'json':
                content = JSON.stringify({
                  command: executionResult.command,
                  parameters: executionResult.parameters,
                  output: executionResult.output,
                  metadata: executionResult.metadata
                }, null, 2);
                filename = `command-output-${Date.now()}.json`;
                mimeType = 'application/json';
                break;
              case 'markdown':
                content = `# Command Output\n\n**Command:** ${executionResult.command}\n\n**Execution Time:** ${executionResult.executionTime}ms\n\n## Output\n\n${executionResult.output.raw}`;
                filename = `command-output-${Date.now()}.md`;
                mimeType = 'text/markdown';
                break;
              case 'csv':
                content = `Command,Execution Time,Success,Output Length\n"${executionResult.command}",${executionResult.executionTime},${executionResult.success},${executionResult.output.raw.length}`;
                filename = `command-output-${Date.now()}.csv`;
                mimeType = 'text/csv';
                break;
            }

            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
          },

          shareOutput: () => {
            const { executionResult } = get();
            if (!executionResult) return;

            const shareData = {
              command: executionResult.command,
              parameters: executionResult.parameters,
              output: executionResult.output.raw,
              executionTime: executionResult.executionTime,
              success: executionResult.success,
              timestamp: executionResult.timestamp
            };

            navigator.clipboard.writeText(JSON.stringify(shareData, null, 2))
              .then(() => {
                alert('Command output copied to clipboard!');
              })
              .catch(() => {
                alert('Failed to copy to clipboard');
              });
          }
        }),
        {
          name: 'command-store',
          partialize: (state) => ({
            favorites: Array.from(state.favorites),
            commandHistory: state.commandHistory.slice(0, 20), // 只保存最近20条
            activeTab: state.activeTab,
            showCommandList: state.showCommandList
          }),
          transform: {
            in: (state) => ({
              ...state,
              favorites: new Set(state.favorites || []),
              commandHistory: state.commandHistory?.map(item => ({
                ...item,
                timestamp: new Date(item.timestamp)
              })) || []
            }),
            out: (state) => ({
              ...state,
              favorites: Array.from(state.favorites)
            })
          }
        }
      ),
      {
        name: 'command-store',
      }
    )
  )
);

export { useCommandStore };
export type { CommandStore };
```

#### 2.2 增强的Command Store类型定义

**文件**: `src/stores/types/command.types.ts`

```typescript
import {
  CommandMetadata,
  CommandExecutionRequest,
  CommandExecutionResult,
  CommandHistoryItem,
  ExecutionContext,
  CommandFilter,
  CommandParameter
} from '../../components/command/CommandExecutorInterface';

// 基础状态接口
export interface CommandState {
  commandHistory: CommandHistoryItem[];
  favorites: Set<string>;
  isExecuting: boolean;
  currentCommand: string | null;
  executionResult: CommandExecutionResult | null;
  executionContext: ExecutionContext;
}

// 扩展状态接口 (用于Component)
export interface CommandExecutorState extends CommandState {
  availableCommands: CommandMetadata[];
  currentParameters: Record<string, any>;
  selectedCommand: CommandMetadata | null;
  executionProgress: any;
  parameterValidation: ParameterValidationState;
  activeTab: 'discover' | 'execute' | 'history';
  showCommandList: boolean;
  error?: string;
}

// 参数验证状态
export interface ParameterValidationState {
  isValid: boolean;
  errors: string[];
}

// Store操作接口
export interface CommandStoreActions {
  // 基础操作
  addToHistory: (command: CommandHistoryItem) => void;
  toggleFavorite: (commandName: string) => void;
  setExecuting: (executing: boolean) => void;
  setCurrentCommand: (command: string | null) => void;
  setExecutionResult: (result: CommandExecutionResult | null) => void;
  clearHistory: () => void;
  executeCommand: (command: string, params?: any) => Promise<CommandExecutionResult>;

  // 扩展操作
  initializeCommands: () => Promise<void>;
  selectCommand: (command: CommandMetadata) => void;
  updateParameters: (parameters: Record<string, any>) => void;
  executeCommandWithRequest: (request?: CommandExecutionRequest) => Promise<CommandExecutionResult>;
  validateParameters: (command: CommandMetadata, parameters: Record<string, any>) => void;
  setExecutionProgress: (progress: any) => void;
  clearExecutionProgress: () => void;

  // UI操作
  setActiveTab: (tab: 'discover' | 'execute' | 'history') => void;
  setShowCommandList: (show: boolean) => void;

  // 历史记录操作
  deleteHistoryItem: (itemId: string) => void;
  exportHistory: () => void;

  // 输出操作
  exportOutput: (format: 'json' | 'markdown' | 'csv') => void;
  shareOutput: () => void;

  // 上下文操作
  updateExecutionContext: (context: Partial<ExecutionContext>) => void;
  resetExecutionContext: () => void;
}

// 选择器接口
export interface CommandStoreSelectors {
  isExecuteDisabled: boolean;
  recentCommands: CommandHistoryItem[];
  favoriteCommandsArray: string[];
  hasRecentHistory: boolean;
  hasFavorites: boolean;
  isDiscoverTab: boolean;
  isExecuteTab: boolean;
  isHistoryTab: boolean;
}

// 异步操作接口
export interface CommandAsyncActions {
  loadCommandRegistry: () => Promise<void>;
  executeCommandAsync: (request: CommandExecutionRequest) => Promise<CommandExecutionResult>;
  reexecuteCommand: (historyItem: CommandHistoryItem) => Promise<CommandExecutionResult>;
  batchExecuteCommands: (requests: CommandExecutionRequest[]) => Promise<CommandExecutionResult[]>;
}

// 持久化配置
export interface CommandStorePersistConfig {
  favorites: boolean;
  commandHistory: boolean;
  uiState: boolean;
  maxHistoryItems: number;
}

// 订阅事件类型
export type CommandStoreEventType =
  | 'command-selected'
  | 'execution-started'
  | 'execution-completed'
  | 'execution-failed'
  | 'favorite-toggled'
  | 'history-cleared'
  | 'parameters-changed'
  | 'tab-changed';

export interface CommandStoreEvent {
  type: CommandStoreEventType;
  payload: any;
  timestamp: Date;
}

// Store配置接口
export interface CommandStoreConfig {
  maxHistoryItems: number;
  autoSaveFavorites: boolean;
  enableProgressTracking: boolean;
  persistExecutionResults: boolean;
  debounceParameterValidation: number;
}
```

### 3. 重构后的CommandExecutorComponent

#### 3.1 简化的组件实现

**文件**: `src/components/command/CommandExecutorComponent.tsx`

```typescript
/**
 * Command Executor Component - Zustand Migration
 * Story 9.8.6.4: Command状态管理迁移
 *
 * 重构后使用Zustand进行状态管理，大幅简化组件逻辑
 */

import React, { useCallback, useEffect } from 'react';
import { CommandExecutorProps } from './CommandExecutorInterface';
import { useCommandStore } from '../../stores/command-store';
import { shallow } from 'zustand/shallow';

// 导入子组件
import ParameterInputComponent from './ParameterInputComponent';
import CommandDiscoveryComponent from './CommandDiscoveryComponent';
import OutputVisualizationComponent from './OutputVisualizationComponent';
import CommandHistoryComponent from './CommandHistoryComponent';

// 选择器函数 - 避免不必要的重渲染
const commandStoreSelector = (state: any) => ({
  // 核心状态
  selectedCommand: state.selectedCommand,
  currentParameters: state.currentParameters,
  isExecuting: state.isExecuting,
  executionHistory: state.executionHistory,
  executionResult: state.executionResult,
  availableCommands: state.availableCommands,
  favorites: state.favorites,
  executionProgress: state.executionProgress,
  parameterValidation: state.parameterValidation,

  // UI状态
  activeTab: state.activeTab,
  showCommandList: state.showCommandList,

  // 计算属性
  isExecuteDisabled: state.isExecuteDisabled,
  recentCommands: state.recentCommands,
  favoriteCommandsArray: state.favoriteCommandsArray,

  // 操作方法
  selectCommand: state.selectCommand,
  updateParameters: state.updateParameters,
  executeCommandWithRequest: state.executeCommandWithRequest,
  toggleFavorite: state.toggleFavorite,
  setActiveTab: state.setActiveTab,
  setShowCommandList: state.setShowCommandList,
  deleteHistoryItem: state.deleteHistoryItem,
  clearHistory: state.clearHistory,
  exportHistory: state.exportHistory,
  exportOutput: state.exportOutput,
  shareOutput: state.shareOutput,
  initializeCommands: state.initializeCommands
});

const CommandExecutorComponent: React.FC<CommandExecutorProps> = ({
  onCommandExecute,
  onCanvasFileSelect,
  initialContext = {},
  className = '',
  autoSaveHistory = true,
  maxHistoryItems = 100,
  enableFavorites = true,
  showAdvanced = false
}) => {
  // 使用Zustand store - 通过选择器优化性能
  const store = useCommandStore(commandStoreSelector, shallow);

  // 初始化命令注册表
  useEffect(() => {
    store.initializeCommands();
  }, [store.initializeCommands]);

  // 处理命令选择
  const handleCommandSelect = useCallback((command: CommandMetadata) => {
    store.selectCommand(command);
  }, [store.selectCommand]);

  // 处理参数变化
  const handleParameterChange = useCallback((parameters: Record<string, any>) => {
    store.updateParameters(parameters);
  }, [store.updateParameters]);

  // 处理命令执行
  const handleExecute = useCallback(async () => {
    try {
      const result = await store.executeCommandWithRequest();

      // 通知父组件
      if (onCommandExecute) {
        onCommandExecute(result);
      }
    } catch (error) {
      console.error('Command execution failed:', error);
      // 错误已经在store中处理，这里只记录日志
    }
  }, [store.executeCommandWithRequest, onCommandExecute]);

  // 处理重新执行
  const handleReexecute = useCallback(async (item: CommandHistoryItem) => {
    try {
      const result = await store.executeCommandWithRequest({
        commandName: item.commandName,
        parameters: item.parameters,
        context: store.executionContext
      });

      if (onCommandExecute) {
        onCommandExecute(result);
      }
    } catch (error) {
      console.error('Command re-execution failed:', error);
    }
  }, [store.executeCommandWithRequest, store.executionContext, onCommandExecute]);

  // 处理收藏切换
  const handleFavoriteToggle = useCallback((commandName: string) => {
    store.toggleFavorite(commandName);
  }, [store.toggleFavorite]);

  // 处理历史管理
  const handleClearHistory = useCallback(() => {
    store.clearHistory();
  }, [store.clearHistory]);

  const handleDeleteHistoryItem = useCallback((itemId: string) => {
    store.deleteHistoryItem(itemId);
  }, [store.deleteHistoryItem]);

  const handleExportHistory = useCallback(() => {
    store.exportHistory();
  }, [store.exportHistory]);

  const handleExportOutput = useCallback((format: 'json' | 'markdown' | 'csv') => {
    store.exportOutput(format);
  }, [store.exportOutput]);

  const handleShare = useCallback(() => {
    store.shareOutput();
  }, [store.shareOutput]);

  // UI事件处理
  const handleTabChange = useCallback((tab: 'discover' | 'execute' | 'history') => {
    store.setActiveTab(tab);
  }, [store.setActiveTab]);

  const handleToggleCommandList = useCallback(() => {
    store.setShowCommandList(!store.showCommandList);
  }, [store.setShowCommandList, store.showCommandList]);

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header - 简化，使用store中的状态 */}
      <div className="border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">Command Executor</h2>
          <div className="flex items-center space-x-2">
            {/* Context indicator */}
            {store.executionContext.userId && (
              <span className="text-xs text-gray-500">
                User: {store.executionContext.userId}
              </span>
            )}
            {store.executionContext.selectedCanvasFile && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Canvas: {store.executionContext.selectedCanvasFile.split('/').pop()}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Navigation Tabs - 使用store状态 */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-4" aria-label="Tabs">
          <button
            onClick={() => handleTabChange('discover')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              store.activeTab === 'discover'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📚 Discover Commands
          </button>
          <button
            onClick={() => handleTabChange('execute')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              store.activeTab === 'execute'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            disabled={!store.selectedCommand}
          >
            ⚡ Execute{store.selectedCommand ? `: ${store.selectedCommand.displayName}` : ''}
          </button>
          <button
            onClick={() => handleTabChange('history')}
            className={`py-2 px-1 border-b-2 font-medium text-sm relative ${
              store.activeTab === 'history'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📋 History
            {store.executionHistory.length > 0 && (
              <span className="ml-1 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                {store.executionHistory.length}
              </span>
            )}
          </button>
        </nav>
      </div>

      {/* Content - 根据tab显示不同内容 */}
      <div className="p-4">
        {/* Discover Commands Tab */}
        {store.activeTab === 'discover' && (
          <CommandDiscoveryComponent
            onCommandSelect={handleCommandSelect}
            recentCommands={store.recentCommands}
            favoriteCommands={store.favorites}
            className="border-0 shadow-none"
          />
        )}

        {/* Execute Command Tab */}
        {store.activeTab === 'execute' && store.selectedCommand && (
          <div className="space-y-6">
            {/* Command Header */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">
                    {store.selectedCommand.displayName}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {store.selectedCommand.description}
                  </p>
                </div>
                <button
                  onClick={handleToggleCommandList}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  {store.showCommandList ? 'Hide Commands' : 'Change Command'}
                </button>
              </div>

              {/* Command tags */}
              <div className="flex flex-wrap gap-1 mt-3">
                {store.selectedCommand.tags.map(tag => (
                  <span
                    key={tag}
                    className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Command List (collapsible) */}
            {store.showCommandList && (
              <CommandDiscoveryComponent
                onCommandSelect={handleCommandSelect}
                favoriteCommands={store.favorites}
                className="border border-gray-200"
                compactMode={true}
              />
            )}

            {/* Parameter Input */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-md font-medium text-gray-900 mb-4">Command Parameters</h4>

              {store.selectedCommand.parameters.length === 0 ? (
                <p className="text-sm text-gray-500">This command has no parameters.</p>
              ) : (
                <div className="space-y-4">
                  {store.selectedCommand.parameters.map(parameter => (
                    <ParameterInputComponent
                      key={parameter.name}
                      parameter={parameter}
                      value={store.currentParameters[parameter.name]}
                      onChange={(value) => handleParameterChange({
                        ...store.currentParameters,
                        [parameter.name]: value
                      })}
                      context={store.executionContext}
                      onValidationChange={(isValid, errors) => {
                        // 验证逻辑已经在store中处理
                      }}
                      showAdvanced={showAdvanced}
                    />
                  ))}
                </div>
              )}

              {/* Validation errors - 使用store状态 */}
              {store.parameterValidation.errors.length > 0 && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                  <h4 className="text-sm font-medium text-red-800">Please fix the following errors:</h4>
                  <ul className="mt-2 text-sm text-red-700 list-disc list-inside">
                    {store.parameterValidation.errors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Execute Button */}
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-500">
                {store.selectedCommand.requiresCanvasFile && (
                  <span className="text-orange-600">⚠️ Canvas file required</span>
                )}
              </div>
              <div className="flex items-center space-x-3">
                {enableFavorites && (
                  <button
                    onClick={() => handleFavoriteToggle(store.selectedCommand!.name)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                  >
                    {store.favorites.has(store.selectedCommand!.name) ? '⭐ Favorited' : '☆ Add to Favorites'}
                  </button>
                )}
                <button
                  onClick={handleExecute}
                  disabled={store.isExecuteDisabled}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {store.isExecuting ? (
                    <>
                      <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                      Executing...
                    </>
                  ) : (
                    <>
                      ⚡ Execute Command
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Execution Progress - 使用store状态 */}
            {store.executionProgress && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-blue-800">Execution Progress</h4>
                  <span className="text-sm text-blue-600">{store.executionProgress.progress}%</span>
                </div>
                <div className="w-full bg-blue-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${store.executionProgress.progress}%` }}
                  ></div>
                </div>
                {store.executionProgress.step && (
                  <p className="text-sm text-blue-700 mt-2">{store.executionProgress.step}</p>
                )}
              </div>
            )}

            {/* Output Visualization */}
            {store.executionResult && (
              <OutputVisualizationComponent
                output={store.executionResult.output}
                command={store.selectedCommand}
                executionTime={store.executionResult.executionTime}
                onExport={handleExportOutput}
                onShare={handleShare}
              />
            )}
          </div>
        )}

        {/* History Tab */}
        {store.activeTab === 'history' && (
          <CommandHistoryComponent
            history={store.executionHistory}
            onReexecute={handleReexecute}
            onFavoriteToggle={handleFavoriteToggle}
            onClearHistory={handleClearHistory}
            onDeleteItem={handleDeleteHistoryItem}
            onExportHistory={handleExportHistory}
            maxItems={maxHistoryItems}
            className="border-0 shadow-none"
          />
        )}
      </div>
    </div>
  );
};

export default CommandExecutorComponent;
```

### 4. 性能优化策略

#### 4.1 选择器优化

```typescript
// 精细化选择器，避免过度订阅
const useCommandSelector = <T>(selector: (state: CommandStore) => T): T => {
  return useCommandStore(selector, shallow);
};

// 示例：不同的组件使用不同的选择器
const CommandList = () => {
  const commands = useCommandSelector(state => state.availableCommands);
  const onSelect = useCommandSelector(state => state.selectCommand);
  // 只在availableCommands变化时重渲染
};

const ExecuteButton = () => {
  const { isExecuting, isExecuteDisabled, executeCommandWithRequest } = useCommandSelector(state => ({
    isExecuting: state.isExecuting,
    isExecuteDisabled: state.isExecuteDisabled,
    executeCommandWithRequest: state.executeCommandWithRequest
  }));
  // 只在执行状态变化时重渲染
};
```

#### 4.2 计算属性缓存

```typescript
// 在store中实现计算属性
const useComputedCommandState = () => {
  return useCommandStore(
    useCallback((state) => ({
      isReadyToExecute: state.selectedCommand &&
                       state.parameterValidation.isValid &&
                       !state.isExecuting,
      hasRecentHistory: state.commandHistory.length > 0,
      successRate: state.commandHistory.length > 0
        ? state.commandHistory.filter(item => item.success).length / state.commandHistory.length
        : 0,
      averageExecutionTime: state.commandHistory.length > 0
        ? state.commandHistory.reduce((sum, item) => sum + item.executionTime, 0) / state.commandHistory.length
        : 0
    }), [])
  );
};
```

### 5. 异步操作处理模式

#### 5.1 统一的异步状态管理

```typescript
// 异步操作封装
export const AsyncCommandOperations = {
  executeCommand: async (request: CommandExecutionRequest) => {
    const store = useCommandStore.getState();

    try {
      // 设置加载状态
      store.setExecuting(true);

      // 执行命令
      const result = await store.executeCommandWithRequest(request);

      // 处理成功
      return result;
    } catch (error) {
      // 错误已在store中处理
      throw error;
    }
  },

  batchExecute: async (requests: CommandExecutionRequest[]) => {
    const store = useCommandStore.getState();
    const results: CommandExecutionResult[] = [];

    for (const request of requests) {
      try {
        const result = await AsyncCommandOperations.executeCommand(request);
        results.push(result);
      } catch (error) {
        // 继续执行其他命令，记录错误
        console.error(`Failed to execute ${request.commandName}:`, error);
      }
    }

    return results;
  }
};
```

#### 5.2 错误处理和重试机制

```typescript
// 带重试的异步操作
export const retryCommandExecution = async (
  request: CommandExecutionRequest,
  maxRetries: number = 3
): Promise<CommandExecutionResult> => {
  const store = useCommandStore.getState();
  let lastError: Error;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const result = await store.executeCommandWithRequest(request);
      return result;
    } catch (error) {
      lastError = error as Error;

      if (attempt === maxRetries) {
        // 最后一次尝试失败
        throw lastError;
      }

      // 等待一段时间后重试
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
    }
  }

  throw lastError!;
};
```

### 6. 测试策略

#### 6.1 Store单元测试

```typescript
// src/stores/__tests__/command-store.test.ts
import { act, renderHook } from '@testing-library/react';
import { useCommandStore } from '../command-store';

describe('CommandStore', () => {
  beforeEach(() => {
    useCommandStore.getState().clearHistory();
  });

  describe('Command Selection', () => {
    it('should select command and reset parameters', () => {
      const { result } = renderHook(() => useCommandStore());
      const mockCommand = {
        name: 'test-command',
        displayName: 'Test Command',
        description: 'Test description',
        parameters: [],
        examples: [],
        tags: [],
        category: 'Utility'
      };

      act(() => {
        result.current.selectCommand(mockCommand);
      });

      expect(result.current.selectedCommand).toEqual(mockCommand);
      expect(result.current.currentParameters).toEqual({});
      expect(result.current.activeTab).toBe('execute');
    });
  });

  describe('Parameter Validation', () => {
    it('should validate required parameters', () => {
      const { result } = renderHook(() => useCommandStore());
      const commandWithRequiredParam = {
        name: 'test-command',
        displayName: 'Test Command',
        description: 'Test',
        parameters: [
          {
            name: 'required',
            type: 'string' as const,
            required: true,
            description: 'Required parameter'
          }
        ],
        examples: [],
        tags: [],
        category: 'Utility'
      };

      act(() => {
        result.current.validateParameters(commandWithRequiredParam, {});
      });

      expect(result.current.parameterValidation.isValid).toBe(false);
      expect(result.current.parameterValidation.errors).toContain('required is required');
    });
  });

  describe('Command Execution', () => {
    it('should handle command execution lifecycle', async () => {
      const { result } = renderHook(() => useCommandStore());
      const mockCommand = {
        name: 'test-command',
        displayName: 'Test Command',
        description: 'Test',
        parameters: [],
        examples: [],
        tags: [],
        category: 'Utility'
      };

      // 选择命令
      act(() => {
        result.current.selectCommand(mockCommand);
      });

      // 执行命令
      let executionPromise: Promise<any>;
      act(() => {
        executionPromise = result.current.executeCommandWithRequest();
      });

      expect(result.current.isExecuting).toBe(true);

      // 等待执行完成
      await act(async () => {
        await executionPromise;
      });

      expect(result.current.isExecuting).toBe(false);
      expect(result.current.executionHistory).toHaveLength(1);
    });
  });

  describe('Favorites Management', () => {
    it('should toggle favorite commands', () => {
      const { result } = renderHook(() => useCommandStore());
      const commandName = 'test-command';

      act(() => {
        result.current.toggleFavorite(commandName);
      });

      expect(result.current.favorites.has(commandName)).toBe(true);

      act(() => {
        result.current.toggleFavorite(commandName);
      });

      expect(result.current.favorites.has(commandName)).toBe(false);
    });
  });
});
```

#### 6.2 组件集成测试

```typescript
// src/components/command/__tests__/CommandExecutorComponent.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CommandExecutorComponent } from '../CommandExecutorComponent';

// Mock store
jest.mock('../../../stores/command-store', () => ({
  useCommandStore: jest.fn()
}));

describe('CommandExecutorComponent Integration', () => {
  const mockStore = {
    selectedCommand: null,
    currentParameters: {},
    isExecuting: false,
    executionHistory: [],
    executionResult: null,
    availableCommands: [],
    favorites: new Set(),
    executionProgress: null,
    parameterValidation: { isValid: true, errors: [] },
    activeTab: 'discover' as const,
    showCommandList: true,
    isExecuteDisabled: true,
    recentCommands: [],
    favoriteCommandsArray: [],
    selectCommand: jest.fn(),
    updateParameters: jest.fn(),
    executeCommandWithRequest: jest.fn(),
    toggleFavorite: jest.fn(),
    setActiveTab: jest.fn(),
    setShowCommandList: jest.fn(),
    deleteHistoryItem: jest.fn(),
    clearHistory: jest.fn(),
    exportHistory: jest.fn(),
    exportOutput: jest.fn(),
    shareOutput: jest.fn(),
    initializeCommands: jest.fn()
  };

  beforeEach(() => {
    const { useCommandStore } = require('../../../stores/command-store');
    useCommandStore.mockReturnValue(mockStore);
  });

  it('should render command executor interface', () => {
    render(<CommandExecutorComponent />);

    expect(screen.getByText('Command Executor')).toBeInTheDocument();
    expect(screen.getByText('Discover Commands')).toBeInTheDocument();
    expect(screen.getByText('Execute')).toBeInTheDocument();
    expect(screen.getByText('History')).toBeInTheDocument();
  });

  it('should handle tab navigation', () => {
    render(<CommandExecutorComponent />);

    fireEvent.click(screen.getByText('History'));
    expect(mockStore.setActiveTab).toHaveBeenCalledWith('history');

    fireEvent.click(screen.getByText('Execute'));
    expect(mockStore.setActiveTab).toHaveBeenCalledWith('execute');
  });

  it('should handle command execution', async () => {
    const mockCommand = {
      name: 'test-command',
      displayName: 'Test Command',
      description: 'Test description',
      parameters: [],
      examples: [],
      tags: [],
      category: 'Utility' as const
    };

    mockStore.selectedCommand = mockCommand;
    mockStore.isExecuteDisabled = false;
    mockStore.executeCommandWithRequest.mockResolvedValue({
      success: true,
      output: { raw: 'Success', format: 'plain_text' },
      executionTime: 100,
      timestamp: new Date(),
      command: 'test-command',
      parameters: {}
    });

    render(<CommandExecutorComponent onCommandExecute={jest.fn()} />);

    fireEvent.click(screen.getByText('⚡ Execute Command'));

    await waitFor(() => {
      expect(mockStore.executeCommandWithRequest).toHaveBeenCalled();
    });
  });
});
```

---

## 📚 实现步骤

### Phase 1: 准备工作 (2小时)
1. **代码审查**: 分析现有CommandExecutorComponent状态管理逻辑
2. **依赖确认**: 确保Zustand已安装 (Story 9.8.6.1已完成)
3. **类型定义**: 完善command-types.ts中的接口定义
4. **测试环境**: 准备单元测试和集成测试框架

### Phase 2: Store增强 (4小时)
1. **扩展command-store**: 添加CommandExecutorComponent所需的所有状态
2. **实现操作方法**: 添加selectCommand, updateParameters, executeCommandWithRequest等
3. **参数验证**: 实现validateParameters方法
4. **异步处理**: 完善executeCommandWithRequest的异步状态管理
5. **持久化配置**: 配置localStorage同步和序列化

### Phase 3: 组件重构 (6小时)
1. **状态迁移**: 移除所有useState，替换为useCommandStore
2. **选择器优化**: 实现精细化选择器，避免过度重渲染
3. **事件处理**: 重构所有事件处理函数，使用store方法
4. **计算属性**: 使用store中的计算属性替代组件内计算
5. **生命周期**: 替换useEffect为store初始化逻辑

### Phase 4: 性能优化 (2小时)
1. **选择器优化**: 实现shallow比较和精细化订阅
2. **计算属性缓存**: 优化复杂计算的性能
3. **组件拆分**: 将大型组件拆分为更小的功能组件
4. **内存管理**: 优化历史记录的内存使用

### Phase 5: 测试实现 (4小时)
1. **Store单元测试**: 测试所有store操作和状态变化
2. **组件集成测试**: 测试组件与store的集成
3. **异步操作测试**: 测试命令执行的异步流程
4. **性能测试**: 验证性能优化效果
5. **错误边界测试**: 测试错误处理和恢复机制

### Phase 6: 验证和调优 (2小时)
1. **功能验证**: 确保所有原有功能正常工作
2. **性能对比**: 对比迁移前后的性能指标
3. **用户体验测试**: 验证交互流畅性和响应性
4. **代码审查**: 审查代码质量和架构设计

---

## 🔍 验收检查清单

### 开发者自检
- [ ] 所有useState成功迁移到Zustand store
- [ ] 组件重渲染次数显著减少
- [ ] TypeScript编译无错误
- [ ] ESLint检查通过
- [ ] Store状态可通过devtools查看和调试
- [ ] localStorage持久化功能正常

### 功能验证
- [ ] 命令选择和参数输入功能正常
- [ ] 命令执行流程完整且状态正确
- [ ] 历史记录保存和查看功能正常
- [ ] 收藏功能持久化且状态同步
- [ ] 参数验证错误正确显示
- [ ] 执行进度实时更新
- [ ] 输出导出和分享功能正常

### 性能验证
- [ ] 组件重渲染次数减少50%以上
- [ ] 大型历史记录不影响渲染性能
- [ ] 参数输入响应无延迟
- [ ] 命令执行状态更新及时
- [ ] 内存使用稳定，无内存泄漏

### 用户体验验证
- [ ] 界面交互流畅，无卡顿
- [ ] 状态更新无闪烁或跳跃
- [ ] 错误信息友好且清晰
- [ ] 页面刷新后状态正确恢复
- [ ] 所有快捷键和交互正常工作

---

## 🚨 风险缓解

### 技术风险
1. **状态同步问题**: Store和组件状态可能不同步
   - **缓解**: 使用Zustand的订阅机制，确保状态一致性
2. **性能回归**: 不当的选择器使用可能导致性能下降
   - **缓解**: 仔细设计选择器，使用shallow比较和精细化订阅
3. **异步操作复杂性**: 命令执行的异步状态管理复杂
   - **缓解**: 封装异步操作，提供清晰的错误处理机制

### 业务风险
1. **功能缺失**: 迁移过程中可能遗漏某些功能
   - **缓解**: 详细的功能对比测试，确保100%功能覆盖
2. **用户体验影响**: 迁移可能影响用户使用习惯
   - **缓解**: 保持UI界面不变，只改变内部实现
3. **数据丢失**: 持久化配置错误可能导致数据丢失
   - **缓解**: 仔细测试localStorage同步，提供数据备份机制

---

## 📖 相关文档

- [Zustand官方文档](https://docs.pmnd.rs/zustand/)
- [Command Executor接口文档](../../components/command/CommandExecutorInterface.ts)
- [Story 9.8.6.1: Zustand基础设置](story-9.8.6.1-zustand-basic-setup.story.md)
- [React性能优化最佳实践](../architecture/react-performance-best-practices.md)
- [状态管理设计模式](../architecture/state-management-patterns.md)
- [TypeScript严格模式指南](../architecture/typescript-strict-mode-guide.md)

---

## 🎯 下一步行动

完成此Story后，立即开始:
1. **Story 9.8.6.5**: 状态管理性能监控和优化
2. **Story 9.8.6.6**: 组件状态迁移收尾和文档更新
3. **Epic 9.8.7**: 组件库重构和标准化

---

**Story创建完成**: 2025-10-26
**准备开发**: ✅ 是
**预估工作量**: 1-2天 (16-20小时)
**依赖项**: Story 9.8.6.1 ✅

---

## 📝 备注

**关键设计决策**:
- 保持组件接口不变，只改变内部状态管理实现
- 使用精细化选择器优化性能，避免过度重渲染
- 完善的异步操作处理和错误边界
- 集成localStorage持久化，提升用户体验
- 全面的测试覆盖，确保迁移质量

**成功标准**:
- CommandExecutorComponent的15个useState完全迁移到Zustand
- 组件性能显著提升，重渲染次数减少50%以上
- 所有原有功能保持不变，用户无感知迁移
- 为后续组件状态迁移提供最佳实践模板

**性能指标目标**:
- 组件重渲染次数: 减少50%以上
- 命令执行响应时间: <100ms
- 参数输入响应延迟: <16ms (一帧)
- 内存使用: 减少30%以上
- Store操作性能: <1ms
