---
document_type: "PRD"
version: "1.0.0"
last_modified: "2025-12-14"
status: "done"
iteration: 1

authors:
  - name: "PM Agent"
    role: "Product Manager"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  architecture: "v1.0"
  api_spec: "v1.0"

changes_from_previous:
  - "Initial Epic created for Agent reliability fix"

git:
  commit_sha: ""
  tag: ""

metadata:
  project_name: "Canvas Learning System"
  epic_count: 1
  fr_count: 6
  nfr_count: 3
---

# Epic 21.5: Agent端点可靠性修复

**Epic ID**: Epic 21.5
**Epic名称**: Agent端点可靠性修复
**优先级**: P0 (最高) - 核心功能不可用
**预计时间**: 1周 (20小时)
**状态**: ✅ 完成
**创建日期**: 2025-12-14
**负责PM**: PM Agent (John)
**依赖**: Epic 21完成 (代码已实现)
**定位**: Epic 21的补丁，解决运行时可靠性问题

---

## 目录

1. [Epic概述](#epic概述)
2. [问题分析](#问题分析)
3. [技术架构](#技术架构)
4. [Story详细分解](#story详细分解)
5. [验收标准](#验收标准)
6. [开发模式](#开发模式)

---

## Epic概述

### 问题陈述

Epic 21的代码功能已实现（85%），但Agent功能在运行时仍然无法使用：

**用户看到的问题**:
```
POST http://localhost:8002/api/v1/agents/explain/memory net::ERR_FAILED 500 (Internal Server Error)
CORS policy: No 'Access-Control-Allow-Origin' header is present
```

**表面现象**:
- 右键点击"记忆锚点"后显示网络错误
- 所有Agent端点都返回500错误
- 插件无法显示具体错误原因

### 根因分析

| 检查项 | 状态 | 说明 |
|--------|------|------|
| **CORS配置** | ✅ 正确 | `app://obsidian.md` 在允许列表 |
| **端点路由** | ✅ 正确 | `/api/v1/agents/explain/memory` 存在 |
| **请求格式** | ✅ 正确 | `{canvas_name, node_id}` 匹配 |
| **AI配置** | ❌ 可疑 | `AI_MODEL_NAME=[K1]gemini-2.5-pro` 异常前缀 |
| **500时CORS** | ❌ 缺失 | 异常时不返回CORS响应头 |

**真正的问题**:
1. **500错误时CORS头缺失** - FastAPI在未处理异常时，CORS中间件不添加响应头
2. **AI Provider配置问题** - 模型名称格式可能无效
3. **缺少错误可见性** - 用户无法知道具体错误

### 解决方案

1. ✅ 添加全局异常处理器，确保500错误也返回CORS头
2. ✅ 启动时验证AI配置，无效时给出明确提示
3. ✅ 创建Bug追踪日志系统，记录所有错误
4. ✅ 增强健康检查端点，快速诊断问题
5. ✅ 改进插件错误显示，显示具体错误信息

### Epic范围

**包含在Epic 21.5中**:
- ✅ 500错误CORS响应头修复
- ✅ AI Provider配置验证
- ✅ Bug追踪日志系统
- ✅ Agent健康检查增强
- ✅ 插件错误显示增强
- ✅ 增量测试验证流程

**不在Epic 21.5范围内**:
- ❌ 新Agent功能开发
- ❌ UI重新设计
- ❌ 性能优化

---

## 技术架构

### 错误处理流程（修复后）

```
插件发起请求
       ↓
FastAPI接收请求
       ↓
全局异常处理器包装 ←── 新增
       ↓
业务逻辑执行
       ↓
异常发生?
   ├── 否 → 正常响应 + CORS头
   └── 是 → 捕获异常
            ↓
       记录到Bug日志 ←── 新增
            ↓
       返回JSON错误 + CORS头 ←── 修复
            ↓
       插件显示具体错误 ←── 增强
```

### 关键文件

| 文件 | 用途 |
|------|------|
| `backend/app/main.py` | CORS异常处理 |
| `backend/app/config.py` | 配置验证 |
| `backend/app/core/bug_tracker.py` | Bug追踪服务 (新建) |
| `backend/app/api/v1/endpoints/health.py` | 健康检查增强 |
| `canvas-progress-tracker/.../ApiClient.ts` | 错误解析增强 |

---

## Story详细分解

### Story 21.5.1: 500错误CORS响应头修复

**优先级**: P0
**预计时间**: 2小时

**目标**: 确保即使发生500错误也返回正确的CORS头

**修改文件**:
- `backend/app/main.py`

**实现方案**:
```python
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class CORSExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # 确保异常响应也有CORS头
            return JSONResponse(
                status_code=500,
                content={"detail": str(e), "error_type": type(e).__name__},
                headers={
                    "Access-Control-Allow-Origin": "app://obsidian.md",
                    "Access-Control-Allow-Credentials": "true",
                }
            )

# 在CORS中间件之前添加
app.add_middleware(CORSExceptionMiddleware)
```

**验收标准**:
- [ ] 500错误时响应包含 `Access-Control-Allow-Origin` 头
- [ ] 插件能看到具体错误信息而非"网络错误"
- [ ] 错误响应包含 `error_type` 字段

---

### Story 21.5.2: AI Provider配置验证

**优先级**: P0
**预计时间**: 3小时

**目标**: 启动时验证AI配置，防止运行时失败

**修改文件**:
- `backend/app/config.py`
- `backend/app/services/agent_service.py`

**实现方案**:

```python
# config.py
from pydantic import field_validator

class Settings(BaseSettings):
    AI_MODEL_NAME: str = Field(...)

    @field_validator('AI_MODEL_NAME')
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        # 检测异常前缀
        if v.startswith('[') and ']' in v:
            prefix = v[:v.index(']')+1]
            clean_name = v[v.index(']')+1:]
            logger.warning(f"AI_MODEL_NAME contains prefix '{prefix}', using '{clean_name}'")
            return clean_name
        return v
```

```python
# agent_service.py
async def test_ai_connection(self) -> dict:
    """测试AI API连接"""
    try:
        # 发送简单测试请求
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        return {"status": "ok", "model": self.model_name}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

**验收标准**:
- [ ] 启动时检测 `AI_MODEL_NAME` 格式，自动清理异常前缀
- [ ] 无效配置时给出明确错误提示
- [ ] 提供 `/api/v1/health/ai` 端点测试AI连接

---

### Story 21.5.3: Bug追踪日志系统

**优先级**: P1
**预计时间**: 4小时

**目标**: 创建持久化Bug日志，记录用户遇到的所有问题

**新建文件**:
- `backend/app/core/bug_tracker.py`

**实现方案**:

```python
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel

class BugRecord(BaseModel):
    bug_id: str
    timestamp: datetime
    endpoint: str
    error_type: str
    error_message: str
    request_params: dict
    stack_trace: Optional[str] = None
    user_action: Optional[str] = None

class BugTracker:
    def __init__(self, log_path: str = "data/bug_log.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_error(
        self,
        endpoint: str,
        error: Exception,
        request_params: dict,
        user_action: Optional[str] = None
    ) -> str:
        """记录Bug，返回bug_id"""
        bug_id = f"BUG-{uuid.uuid4().hex[:8].upper()}"

        record = BugRecord(
            bug_id=bug_id,
            timestamp=datetime.utcnow(),
            endpoint=endpoint,
            error_type=type(error).__name__,
            error_message=str(error),
            request_params=request_params,
            stack_trace=traceback.format_exc(),
            user_action=user_action
        )

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")

        return bug_id

    def get_recent_bugs(self, limit: int = 50) -> List[BugRecord]:
        """获取最近的Bug记录"""
        if not self.log_path.exists():
            return []

        bugs = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                bugs.append(BugRecord.model_validate_json(line))

        return bugs[-limit:]
```

**验收标准**:
- [ ] 所有500错误自动记录到 `backend/data/bug_log.jsonl`
- [ ] 记录包含：时间戳、端点、请求参数、错误堆栈
- [ ] 提供 `/api/v1/debug/bugs` 端点查看最近Bug

---

### Story 21.5.4: Agent端点健康检查增强

**优先级**: P1
**预计时间**: 3小时

**目标**: 快速诊断Agent功能是否正常

**修改文件**:
- `backend/app/api/v1/endpoints/health.py`

**新增端点**:
```python
@router.get("/health/agents")
async def check_agents_health(agent_service: AgentServiceDep) -> dict:
    """检查所有Agent端点状态"""
    return {
        "status": "ok",
        "agents": {
            "decompose_basic": "available",
            "decompose_deep": "available",
            "explain_oral": "available",
            "explain_memory": "available",
            # ... 其他端点
        }
    }

@router.get("/health/ai")
async def check_ai_health(agent_service: AgentServiceDep) -> dict:
    """测试AI API连接"""
    result = await agent_service.test_ai_connection()
    return result

@router.get("/health/full")
async def full_health_check(
    agent_service: AgentServiceDep,
    canvas_service: CanvasServiceDep
) -> dict:
    """完整系统诊断"""
    return {
        "status": "ok",
        "components": {
            "database": "ok",
            "ai_provider": await agent_service.test_ai_connection(),
            "canvas_service": "ok",
            "cors": {
                "allowed_origins": settings.cors_origins_list
            }
        },
        "config": {
            "ai_model": settings.AI_MODEL_NAME,
            "ai_provider": settings.AI_PROVIDER,
        }
    }
```

**验收标准**:
- [ ] 一次请求即可知道所有服务状态
- [ ] 包含AI API连接测试
- [ ] 返回详细的诊断信息

---

### Story 21.5.5: 插件错误显示增强

**优先级**: P2
**预计时间**: 2小时

**目标**: 插件能显示后端返回的具体错误信息

**修改文件**:
- `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts`
- `canvas-progress-tracker/obsidian-plugin/main.ts`

**实现方案**:

```typescript
// ApiClient.ts - 增强错误解析
private async handleErrorResponse(response: Response): Promise<never> {
    let errorDetail = 'Unknown error';
    let bugId = '';
    let errorType = '';

    try {
        const body = await response.json();
        errorDetail = body.detail || body.message || errorDetail;
        bugId = body.bug_id || '';
        errorType = body.error_type || '';
    } catch {
        errorDetail = response.statusText;
    }

    const error = new ApiError(
        response.status,
        errorDetail,
        bugId,
        errorType
    );
    throw error;
}
```

```typescript
// main.ts - 改进Notice显示
executeMemoryAnchor: async (context: MenuContext) => {
    try {
        new Notice('正在生成记忆锚点...');
        const result = await this.apiClient.explainMemory({...});
        new Notice('记忆锚点生成完成');
    } catch (error) {
        if (error instanceof ApiError) {
            const msg = `${error.errorType}: ${error.detail}`;
            const notice = new Notice(msg, 10000);

            if (error.bugId) {
                console.error(`Bug ID: ${error.bugId}`);
            }
        } else {
            new Notice(`未知错误: ${error.message}`);
        }
    }
}
```

**验收标准**:
- [ ] 500错误时显示后端返回的error detail
- [ ] 显示bug_id供用户报告
- [ ] 错误信息停留时间更长(10秒)

---

### Story 21.5.6: 增量测试验证流程

**优先级**: P2
**预计时间**: 3小时

**目标**: 建立Story开发→测试→验证的标准流程

**新建文件**:
- `scripts/test-agent-endpoint.py`

**实现方案**:

```python
#!/usr/bin/env python3
"""Agent端点测试脚本"""

import argparse
import httpx
import sys
from typing import Optional

ENDPOINTS = {
    "memory": "/api/v1/agents/explain/memory",
    "oral": "/api/v1/agents/explain/oral",
    "four-level": "/api/v1/agents/explain/four-level",
    "basic": "/api/v1/agents/decompose/basic",
    "deep": "/api/v1/agents/decompose/deep",
}

def test_endpoint(base_url: str, endpoint: str, verbose: bool = False) -> bool:
    """测试单个端点"""
    url = f"{base_url}{ENDPOINTS[endpoint]}"
    payload = {
        "canvas_name": "test.canvas",
        "node_id": "test-node-001"
    }

    try:
        response = httpx.post(url, json=payload, timeout=30.0)

        if response.status_code == 200:
            print(f"✅ {endpoint}: SUCCESS")
            return True
        else:
            print(f"❌ {endpoint}: FAILED ({response.status_code})")
            if verbose:
                print(f"   Detail: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ {endpoint}: ERROR - {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", help="Test specific endpoint")
    parser.add_argument("--all", action="store_true", help="Test all endpoints")
    parser.add_argument("--base-url", default="http://localhost:8002")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.endpoint:
        success = test_endpoint(args.base_url, args.endpoint, args.verbose)
        sys.exit(0 if success else 1)

    if args.all:
        results = []
        for name in ENDPOINTS:
            results.append(test_endpoint(args.base_url, name, args.verbose))

        passed = sum(results)
        total = len(results)
        print(f"\n总计: {passed}/{total} 通过")
        sys.exit(0 if all(results) else 1)

if __name__ == "__main__":
    main()
```

**验收标准**:
- [ ] 每个Story完成后可立即测试
- [ ] 测试结果清晰显示成功/失败
- [ ] 失败时显示具体错误

---

## 验收标准

### Epic级别验收标准

| 标准 | 描述 |
|------|------|
| **AC-1** | 所有Agent端点调用成功时返回正确结果 |
| **AC-2** | 所有Agent端点失败时返回明确错误信息+CORS头 |
| **AC-3** | Bug追踪日志记录所有500错误 |
| **AC-4** | 健康检查端点能诊断AI连接状态 |
| **AC-5** | 插件能显示后端返回的具体错误 |

### 功能需求 (FR)

| ID | 需求 | Story |
|----|------|-------|
| FR-1 | 500错误返回CORS头 | 21.5.1 |
| FR-2 | AI配置启动时验证 | 21.5.2 |
| FR-3 | Bug日志自动记录 | 21.5.3 |
| FR-4 | `/health/ai` 端点 | 21.5.4 |
| FR-5 | 插件显示错误详情 | 21.5.5 |
| FR-6 | 测试脚本可用 | 21.5.6 |

### 非功能需求 (NFR)

| ID | 需求 | 指标 |
|----|------|------|
| NFR-1 | 错误响应延迟 | < 100ms |
| NFR-2 | Bug日志文件大小 | < 10MB (自动轮转) |
| NFR-3 | 健康检查响应 | < 500ms |

---

## 开发模式

### 增量开发流程

```
┌─────────────────────────────────────────────────┐
│ 每个Story的开发流程                              │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. SM创建Story → 用户确认                       │
│         ↓                                       │
│  2. Dev实现代码                                  │
│         ↓                                       │
│  3. 构建后端: python start_server.py            │
│         ↓                                       │
│  4. 构建插件: npm run build                      │
│         ↓                                       │
│  5. 复制到Obsidian插件目录                       │
│         ↓                                       │
│  6. 重载Obsidian: Ctrl+P → Reload               │
│         ↓                                       │
│  7. 用户测试: 右键点击Canvas节点                  │
│         ↓                                       │
│  8. 报告Bug → 检查bug_log.jsonl                  │
│         ↓                                       │
│  9. 修复 → 重复步骤3-8 直到通过                  │
│         ↓                                       │
│ 10. 下一个Story                                 │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 测试命令

```bash
# 启动后端
cd backend && python start_server.py

# 测试健康检查
curl http://localhost:8002/api/v1/health

# 测试AI连接
curl http://localhost:8002/api/v1/health/ai

# 测试单个Agent端点
python scripts/test-agent-endpoint.py --endpoint memory

# 测试所有端点
python scripts/test-agent-endpoint.py --all -v

# 查看Bug日志
cat backend/data/bug_log.jsonl | jq
```

---

## 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| AI Provider完全不可用 | 中 | 高 | 提供清晰错误提示，建议检查配置 |
| Bug日志文件过大 | 低 | 中 | 实现日志轮转 (保留最近1000条) |
| CORS中间件顺序问题 | 低 | 高 | 添加集成测试验证 |

---

## 附录

### 相关文档

- Epic 21 PRD: `docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md`
- 架构文档: `docs/architecture/canvas-layer-architecture.md`
- API规范: `specs/api/agent-api.openapi.yml`

### 变更日志

| 日期 | 版本 | 变更 |
|------|------|------|
| 2025-12-14 | 1.0.0 | 初始版本 |
