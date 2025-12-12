---
document_type: "PRD"
version: "1.0.0"
last_modified: "2025-12-11"
status: "draft"
iteration: 1

authors:
  - name: "PM Agent"
    role: "Product Manager"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: false

compatible_with:
  architecture: "v1.0"
  api_spec: "v1.0"

changes_from_previous:
  - "Initial Epic created for backend stability and multi-provider support"

git:
  commit_sha: ""
  tag: ""

metadata:
  project_name: "Canvas Learning System"
  epic_count: 1
  fr_count: 4
  nfr_count: 3
---

# Epic 20: 后端稳定性与多Provider支持

**Epic ID**: Epic 20
**Epic名称**: 后端稳定性与多Provider支持
**优先级**: P0 (最高)
**预计时间**: 1周 (20小时)
**状态**: 准备启动
**创建日期**: 2025-12-11
**负责PM**: PM Agent (John)
**依赖**: Epic 11完成 (FastAPI基础架构) ✅
**阻塞**: Epic 21 (Agent端到端流程)、Epic 22 (记忆系统)、Epic 23 (RAG系统)

---

## 目录

1. [Epic概述](#epic概述)
2. [问题分析 (Bug 1详解)](#问题分析-bug-1详解)
3. [业务价值和目标](#业务价值和目标)
4. [技术架构](#技术架构)
5. [Story详细分解](#story详细分解)
6. [验收标准](#验收标准)
7. [风险评估](#风险评估)

---

## Epic概述

### 问题陈述

Canvas Learning System 后端在使用 Agent 功能时存在严重的稳定性问题：

1. **外部API依赖**: 当前 `.env` 配置使用非官方API端点 (`https://dapang.cervus.top/v1`)
2. **非标准模型名**: 模型名包含前缀 `[K1]gemini-2.5-pro`，可能导致解析错误
3. **单点故障**: 无Provider切换机制，一旦当前Provider不可用，整个系统瘫痪
4. **API密钥管理**: `.env` 文件可能包含敏感信息但未被正确保护
5. **健康检查缺失**: 无法实时感知AI Provider的可用性状态

### 解决方案

**构建多Provider架构**，支持多个AI服务商无缝切换，提供故障转移能力：

**核心特性**:
- ✅ 支持多Provider配置 (Google, OpenAI, Anthropic, OpenRouter, Custom)
- ✅ 智能Provider切换机制
- ✅ API密钥安全管理
- ✅ Provider健康检查与故障转移
- ✅ 响应时间监控

### Epic范围

**包含在Epic 20中**:
- ✅ 多Provider架构设计与实现
- ✅ Provider工厂模式
- ✅ 动态Provider切换
- ✅ API密钥安全存储
- ✅ Provider健康检查端点
- ✅ 自动故障转移机制

**不包含在Epic 20中** (后续Epic):
- ❌ Agent上下文管理优化 (Epic 21)
- ❌ 记忆系统集成 (Epic 22)
- ❌ RAG智能推理 (Epic 23)

---

## 问题分析 (Bug 1详解)

### 根因分析

```
Bug 1: FastAPI后端启动不稳定
                │
                ▼
┌─────────────────────────────────────────────────────────┐
│ 根因1: 外部API依赖                                       │
│ ─────────────────────────────────────────────────────── │
│ .env: AI_BASE_URL="https://dapang.cervus.top/v1"       │
│ 问题: 非官方API，稳定性无保障                            │
└─────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────┐
│ 根因2: 非标准模型名                                      │
│ ─────────────────────────────────────────────────────── │
│ .env: AI_MODEL_NAME="[K1]gemini-2.5-pro"               │
│ 问题: 包含前缀[K1]，可能导致API调用失败                  │
└─────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────┐
│ 根因3: 单点故障                                          │
│ ─────────────────────────────────────────────────────── │
│ 代码: 只有一个Provider，无备用选项                       │
│ 问题: Provider不可用时整个系统瘫痪                       │
└─────────────────────────────────────────────────────────┘
```

### 现有代码分析

**config.py 当前状态** (已有基础结构):
```python
# backend/app/config.py - 现有配置
AI_PROVIDER: str = Field(default="google", ...)
AI_MODEL_NAME: str = Field(default="gemini-2.0-flash-exp", ...)
AI_BASE_URL: str = Field(default="", ...)
AI_API_KEY: str = Field(default="", ...)
```

**问题**: 虽然有配置项，但缺少:
1. Provider工厂模式
2. 多Provider并行配置
3. 健康检查机制
4. 自动故障转移

---

## 业务价值和目标

### 业务价值

| 价值项 | 重要性 | 说明 |
|--------|--------|------|
| **系统可用性** | ⭐⭐⭐⭐⭐ | 多Provider保障，单个Provider故障不影响服务 |
| **用户体验** | ⭐⭐⭐⭐⭐ | 无感知切换，Agent调用始终成功 |
| **运维成本** | ⭐⭐⭐⭐ | 自动故障转移，减少人工干预 |
| **安全合规** | ⭐⭐⭐⭐ | API密钥安全存储，防止泄露 |

### 目标

#### 短期目标 (Epic 20完成后)
- [ ] 支持至少3个AI Provider配置
- [ ] Provider健康检查响应时间 < 500ms
- [ ] 故障转移时间 < 2s
- [ ] API密钥不再明文存储在版本控制中

#### 中期目标 (Epic 21-23完成后)
- [ ] 所有Agent调用成功率 > 99.5%
- [ ] 平均响应时间 < 3s

---

## 技术架构

### 多Provider架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (Obsidian Plugin)                   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Provider Manager (新增)                     │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  • Provider注册表                                        │   │
│  │  • 健康检查调度器                                         │   │
│  │  • 故障转移控制器                                         │   │
│  │  • 响应时间监控                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│            ┌─────────────┼─────────────┐                        │
│            ▼             ▼             ▼                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Google       │ │ OpenAI       │ │ Anthropic    │            │
│  │ Provider     │ │ Provider     │ │ Provider     │            │
│  │ (Primary)    │ │ (Backup 1)   │ │ (Backup 2)   │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Provider工厂模式

```python
# 新增: backend/app/clients/provider_factory.py

class ProviderFactory:
    """AI Provider工厂类"""

    _providers: Dict[str, AIProvider] = {}
    _health_status: Dict[str, ProviderHealth] = {}

    @classmethod
    def get_provider(cls, name: str = None) -> AIProvider:
        """获取可用的Provider，支持自动故障转移"""
        if name:
            return cls._providers.get(name)

        # 按优先级返回健康的Provider
        for provider_name in cls._priority_order:
            if cls._health_status[provider_name].is_healthy:
                return cls._providers[provider_name]

        raise NoHealthyProviderError("所有Provider均不可用")
```

---

## Story详细分解

### Story 20.1: 多Provider架构设计

**Story ID**: Story-20.1
**标题**: 多Provider架构设计
**优先级**: P0
**预计时间**: 4小时
**状态**: 待开发

#### 用户故事
```
作为系统管理员
我希望能够配置多个AI Provider
以便在一个Provider不可用时自动切换到备用Provider
```

#### 验收标准 (AC)
- [ ] AC-20.1.1: 支持配置至少3个Provider (Google, OpenAI, Anthropic)
- [ ] AC-20.1.2: 每个Provider可独立配置API密钥和端点
- [ ] AC-20.1.3: 支持设置Provider优先级顺序
- [ ] AC-20.1.4: 配置变更无需重启服务

#### 技术任务
1. **扩展config.py配置结构**
   - 添加 `AI_PROVIDERS` 列表配置
   - 每个Provider包含: name, api_key, base_url, model, priority

2. **创建Provider基类**
   - `backend/app/clients/base_provider.py`
   - 定义统一接口: `complete()`, `health_check()`, `get_usage()`

3. **实现具体Provider**
   - `backend/app/clients/google_provider.py`
   - `backend/app/clients/openai_provider.py`
   - `backend/app/clients/anthropic_provider.py`

#### 关键文件
- `backend/app/config.py` (修改)
- `backend/app/clients/base_provider.py` (新增)
- `backend/app/clients/google_provider.py` (新增)
- `backend/app/clients/openai_provider.py` (新增)
- `backend/app/clients/anthropic_provider.py` (新增)

---

### Story 20.2: Provider切换机制

**Story ID**: Story-20.2
**标题**: Provider切换机制实现
**优先级**: P0
**预计时间**: 6小时
**状态**: 待开发

#### 用户故事
```
作为Agent服务
我希望在调用AI时能够自动选择最佳Provider
以便获得最快的响应和最高的可用性
```

#### 验收标准 (AC)
- [ ] AC-20.2.1: ProviderFactory实现Provider注册和获取
- [ ] AC-20.2.2: 支持按优先级自动选择健康Provider
- [ ] AC-20.2.3: Provider切换时间 < 100ms
- [ ] AC-20.2.4: 切换日志记录完整

#### 技术任务
1. **实现ProviderFactory**
   - `backend/app/clients/provider_factory.py`
   - 单例模式管理所有Provider实例

2. **实现选择策略**
   - 优先级策略 (默认)
   - 轮询策略 (可选)
   - 响应时间最优策略 (可选)

3. **集成到AgentService**
   - 修改 `backend/app/services/agent_service.py`
   - 使用ProviderFactory替换直接Provider调用

#### 关键文件
- `backend/app/clients/provider_factory.py` (新增)
- `backend/app/services/agent_service.py` (修改)

---

### Story 20.3: API密钥安全管理

**Story ID**: Story-20.3
**标题**: API密钥安全管理
**优先级**: P0
**预计时间**: 4小时
**状态**: 待开发

#### 用户故事
```
作为系统管理员
我希望API密钥被安全存储和管理
以便防止敏感信息泄露
```

#### 验收标准 (AC)
- [ ] AC-20.3.1: `.env`文件不包含在git版本控制中
- [ ] AC-20.3.2: 提供`.env.example`模板文件
- [ ] AC-20.3.3: API密钥在日志中自动脱敏
- [ ] AC-20.3.4: 支持环境变量覆盖配置

#### 技术任务
1. **更新.gitignore**
   - 确保`.env`被忽略
   - 确保所有`*.key`文件被忽略

2. **创建.env.example**
   - 提供完整配置模板
   - 包含所有Provider配置示例

3. **实现密钥脱敏**
   - 日志中密钥显示为`****`
   - API响应中不返回密钥

#### 关键文件
- `backend/.gitignore` (修改)
- `backend/.env.example` (新增)
- `backend/app/utils/security.py` (新增)

---

### Story 20.4: 健康检查与故障转移

**Story ID**: Story-20.4
**标题**: 健康检查与故障转移
**优先级**: P0
**预计时间**: 6小时
**状态**: 待开发

#### 用户故事
```
作为运维人员
我希望能够实时监控Provider健康状态
以便在故障发生前主动切换Provider
```

#### 验收标准 (AC)
- [ ] AC-20.4.1: 每个Provider有独立健康检查端点
- [ ] AC-20.4.2: 健康检查间隔可配置 (默认30秒)
- [ ] AC-20.4.3: 连续3次失败后自动标记为不健康
- [ ] AC-20.4.4: 不健康Provider自动从选择池中移除
- [ ] AC-20.4.5: Provider恢复后自动重新加入选择池

#### 技术任务
1. **实现健康检查服务**
   - `backend/app/services/health_check_service.py`
   - 后台定时任务检查所有Provider

2. **扩展健康检查API**
   - `GET /api/v1/health/providers` - 获取所有Provider状态
   - `GET /api/v1/health/providers/{name}` - 获取单个Provider状态

3. **实现故障转移逻辑**
   - 自动检测Provider故障
   - 触发切换到备用Provider
   - 发送告警通知 (可选)

4. **实现恢复检测**
   - 定期重试不健康Provider
   - 恢复后自动重新加入

#### 关键文件
- `backend/app/services/health_check_service.py` (新增)
- `backend/app/api/v1/endpoints/health.py` (修改)
- `backend/app/models/schemas.py` (修改 - 添加ProviderHealth模型)

---

## 验收标准

### Epic级别验收标准

| ID | 验收标准 | 验证方法 |
|----|----------|----------|
| AC-20.E1 | 至少支持3个AI Provider配置 | 检查配置文件和代码 |
| AC-20.E2 | Provider故障后2秒内自动切换 | 性能测试 |
| AC-20.E3 | API密钥不在git历史中出现 | `git log -p \| grep -i api_key` |
| AC-20.E4 | 健康检查端点响应时间<500ms | API性能测试 |
| AC-20.E5 | 所有Provider切换有日志记录 | 日志审查 |

### 测试计划

1. **单元测试**
   - Provider基类测试
   - ProviderFactory测试
   - 健康检查服务测试

2. **集成测试**
   - 多Provider切换测试
   - 故障转移测试
   - 恢复检测测试

3. **性能测试**
   - Provider响应时间基准
   - 切换延迟测试

---

## 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 所有Provider同时不可用 | 低 | 高 | 本地缓存策略，友好错误提示 |
| 频繁切换导致不稳定 | 中 | 中 | 设置切换冷却时间 |
| API密钥泄露 | 低 | 高 | 严格的gitignore规则，密钥轮换机制 |
| Provider API变更 | 中 | 中 | 抽象接口层，版本锁定 |

---

## 依赖关系

### 上游依赖
- Epic 11: FastAPI基础架构 ✅ (已完成)

### 下游依赖
- Epic 21: Agent端到端流程修复 (需要稳定的Provider)
- Epic 22: 记忆系统 (Neo4j/Graphiti)
- Epic 23: RAG智能推理系统

---

## 附录

### A. 配置示例

```env
# .env.example

# Primary Provider (Google)
AI_PROVIDER_1_NAME=google
AI_PROVIDER_1_API_KEY=your-google-api-key
AI_PROVIDER_1_MODEL=gemini-2.0-flash-exp
AI_PROVIDER_1_PRIORITY=1

# Backup Provider 1 (OpenAI)
AI_PROVIDER_2_NAME=openai
AI_PROVIDER_2_API_KEY=your-openai-api-key
AI_PROVIDER_2_MODEL=gpt-4o
AI_PROVIDER_2_PRIORITY=2

# Backup Provider 2 (Anthropic)
AI_PROVIDER_3_NAME=anthropic
AI_PROVIDER_3_API_KEY=your-anthropic-api-key
AI_PROVIDER_3_MODEL=claude-3-5-sonnet-20241022
AI_PROVIDER_3_PRIORITY=3

# Health Check Settings
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=5
HEALTH_CHECK_FAILURE_THRESHOLD=3
```

### B. API端点规范

```yaml
# Provider Health API

GET /api/v1/health/providers:
  description: 获取所有Provider健康状态
  response:
    providers:
      - name: google
        status: healthy
        latency_ms: 120
        last_check: "2025-12-11T10:00:00Z"
      - name: openai
        status: healthy
        latency_ms: 180
        last_check: "2025-12-11T10:00:00Z"
      - name: anthropic
        status: unhealthy
        latency_ms: null
        last_check: "2025-12-11T10:00:00Z"
        error: "Connection timeout"
    active_provider: google
```
