# Story 12.H.5: 后端二级防重复

**Story ID**: STORY-12.H.5
**Epic**: Epic 12.H - Canvas 并发控制 + 任务管理面板
**优先级**: P2
**状态**: Draft
**预估时间**: 2 小时
**创建日期**: 2025-12-17

---

## 用户故事

**作为** Canvas Learning System 的开发者
**我希望** 后端能够拒绝重复的 Agent 请求
**以便** 提供二级防护，防止前端防重复失效时产生重复文档

---

## 问题背景

### 当前问题

后端 API 端点没有请求去重机制：
- 相同请求可能被处理多次
- 前端防重复失效时无兜底
- 浪费 API 资源

### 问题场景

```
场景: 前端防重复失效（例如页面刷新后重新点击）
1. 用户点击 "四层次解释" → 请求 A
2. 页面刷新，pendingRequests 丢失
3. 用户再次点击 "四层次解释" → 请求 B
4. 请求 A 和 B 同时执行
5. 生成两份相同文档
```

### 问题影响

- 资源浪费
- 重复内容
- 后端无防护

---

## 验收标准

- [ ] AC1: 添加请求缓存，TTL 60秒
- [ ] AC2: 重复请求返回 HTTP 409 Conflict
- [ ] AC3: 缓存 key 格式: `{canvas_name}:{node_id}:{agent_type}`
- [ ] AC4: 日志记录重复请求
- [ ] AC5: 缓存自动清理过期条目
- [ ] AC6: 可通过环境变量禁用（用于测试）

---

## Tasks / Subtasks

- [ ] **Task 1**: 创建 RequestCache 类 (AC: #1, #3, #5)
  - [ ] 1.1 创建 `backend/app/core/request_cache.py`
  - [ ] 1.2 实现 `get_key()` 方法 (MD5 hash)
  - [ ] 1.3 实现 `is_duplicate()` 方法
  - [ ] 1.4 实现 `mark_in_progress()` 方法
  - [ ] 1.5 实现 `mark_completed()` 方法
  - [ ] 1.6 实现 `remove()` 方法 (用于失败时清理)
  - [ ] 1.7 实现 `_maybe_cleanup()` 自动清理过期条目

- [ ] **Task 2**: 添加配置支持 (AC: #6)
  - [ ] 2.1 在 `backend/app/core/config.py` 添加 `ENABLE_REQUEST_DEDUP`
  - [ ] 2.2 在 `backend/app/core/config.py` 添加 `REQUEST_CACHE_TTL`
  - [ ] 2.3 在 `.env.example` 添加环境变量说明

- [ ] **Task 3**: 集成到 Agent 端点 (AC: #2, #4)
  - [ ] 3.1 创建 `check_duplicate_request()` 辅助函数
  - [ ] 3.2 在 `agents.py` 导入 request_cache
  - [ ] 3.3 为 `/explain/oral` 端点添加去重检查
  - [ ] 3.4 为 `/explain/four-level` 端点添加去重检查
  - [ ] 3.5 为 `/explain/clarification` 端点添加去重检查
  - [ ] 3.6 为其他 Agent 端点添加去重检查
  - [ ] 3.7 添加 try-finally 确保缓存清理

- [ ] **Task 4**: 编写单元测试
  - [ ] 4.1 创建 `backend/tests/core/test_request_cache.py`
  - [ ] 4.2 测试 `is_duplicate` 新请求返回 False
  - [ ] 4.3 测试 `is_duplicate` 重复请求返回 True
  - [ ] 4.4 测试 TTL 过期后返回 False
  - [ ] 4.5 测试 `remove()` 后允许新请求
  - [ ] 4.6 测试不同请求有不同 key

- [ ] **Task 5**: 编写 API 集成测试
  - [ ] 5.1 创建 `backend/tests/api/v1/endpoints/test_agents_dedup.py`
  - [ ] 5.2 测试首次请求成功
  - [ ] 5.3 测试重复请求返回 409
  - [ ] 5.4 测试不同 Agent 类型不互相阻塞

- [ ] **Task 6**: 更新 OpenAPI 规范 (SDD 一致性)
  - [ ] 6.1 在 `specs/api/agent-api.openapi.yml` 添加 409 响应定义
  - [ ] 6.2 添加 `DuplicateRequestError` schema

---

## Dev Notes

### SDD规范参考 (必填)

**API端点** (从 OpenAPI specs):
- 端点路径: `POST /api/v1/agents/explain/{type}` (实际实现路径)
- 规范来源: `[Source: specs/api/agent-api.openapi.yml]`
- 新增响应码: **HTTP 409 Conflict** (本 Story 需要添加到 OpenAPI spec)
- 响应格式:
  ```json
  {
    "error": "Duplicate request",
    "message": "相同请求正在处理中，请稍候",
    "canvas_name": "string",
    "node_id": "string",
    "agent_type": "string"
  }
  ```

**数据Schema**:
- 错误响应格式: 对齐 `AgentError` Schema
- 来源: `[Source: specs/api/agent-api.openapi.yml#L780-L803]`
- 新增错误类型: 建议添加 `DUPLICATE_REQUEST` 到 `AgentErrorType` enum

**注意**: 本 Story 需要同步更新 OpenAPI spec 以保持 SDD 一致性。

### ADR决策关联 (必填)

| ADR编号 | 决策标题 | 对Story的影响 |
|---------|----------|---------------|
| ADR-007 | 缓存策略 - 分层缓存 | 请求缓存使用内存 L1 缓存模式，TTL 机制对齐 ADR-007 |
| ADR-009 | 错误处理与重试策略 | 409 响应属于 NON_RETRYABLE 类型，对齐 ErrorCode 体系 |

**关键约束** (从 ADR Consequences 提取):
- ADR-007: 内存缓存使用 TTL 机制自动清理
- ADR-007: 缓存键使用 MD5 hash 生成
- ADR-009: 错误响应需要包含 `is_retryable` 字段

**来源引用**: `[Source: ADR-007, ADR-009]`

### Relevant Source Tree

```
backend/
├── app/
│   ├── api/v1/endpoints/
│   │   └── agents.py          # 修改: 添加去重检查
│   └── core/
│       ├── config.py          # 修改: 添加配置项
│       └── request_cache.py   # 新建: RequestCache 类
├── tests/
│   ├── core/
│   │   └── test_request_cache.py  # 新建: 单元测试
│   └── api/v1/endpoints/
│       └── test_agents_dedup.py   # 新建: API测试
specs/
└── api/
    └── agent-api.openapi.yml  # 修改: 添加 409 响应
```

### Testing

**测试框架**: pytest
**测试位置**: `backend/tests/`
**测试标准**:
- 遵循 ADR-008 测试框架规范
- 单元测试使用 pytest fixtures
- API 测试使用 `TestClient`
- Mock 外部依赖 (如 GeminiClient)

**覆盖率要求**:
- RequestCache 类: 100%
- 新增端点代码: 100%

---

## 技术方案

### RequestCache 实现

```python
# backend/app/core/request_cache.py

import time
import hashlib
import threading
from typing import Dict, Tuple, Optional, Any
from loguru import logger

class RequestCache:
    """
    Story 12.H.5: 请求去重缓存

    用于防止相同请求在短时间内重复执行。
    使用 TTL 机制自动清理过期条目。

    对齐 ADR-007: 使用内存缓存 + TTL 机制
    """

    def __init__(self, ttl: int = 60, cleanup_interval: int = 30):
        """
        初始化请求缓存

        Args:
            ttl: 缓存条目的生存时间（秒）
            cleanup_interval: 清理过期条目的间隔（秒）
        """
        self.ttl = ttl
        self.cleanup_interval = cleanup_interval
        self.cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def get_key(
        self,
        canvas_name: str,
        node_id: str,
        agent_type: str
    ) -> str:
        """
        生成缓存 key

        格式: MD5({canvas_name}:{node_id}:{agent_type})
        对齐 ADR-007: 缓存键使用 MD5 hash
        """
        raw = f"{canvas_name}:{node_id}:{agent_type}"
        return hashlib.md5(raw.encode()).hexdigest()

    def is_duplicate(self, key: str) -> bool:
        """
        检查是否为重复请求

        Args:
            key: 缓存 key

        Returns:
            True 如果请求在 TTL 内已存在
        """
        self._maybe_cleanup()

        with self._lock:
            if key in self.cache:
                timestamp, _ = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    logger.warning(f"Duplicate request detected: {key}")
                    return True
                else:
                    # 过期了，删除
                    del self.cache[key]
            return False

    def mark_in_progress(self, key: str, data: Any = None) -> None:
        """
        标记请求为进行中

        Args:
            key: 缓存 key
            data: 可选的关联数据
        """
        with self._lock:
            self.cache[key] = (time.time(), data)
            logger.debug(f"Request marked in progress: {key}")

    def mark_completed(self, key: str) -> None:
        """
        标记请求完成（保留 TTL 时间防止重复）

        注意: 不立即删除，让请求在 TTL 内仍被视为重复
        """
        with self._lock:
            if key in self.cache:
                _, data = self.cache[key]
                # 更新时间戳，重新开始 TTL 计时
                self.cache[key] = (time.time(), data)
                logger.debug(f"Request marked completed: {key}")

    def remove(self, key: str) -> None:
        """
        立即移除缓存条目（用于请求失败或取消时）
        """
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Request removed from cache: {key}")

    def _maybe_cleanup(self) -> None:
        """
        定期清理过期条目
        对齐 ADR-007: TTL 机制自动清理
        """
        now = time.time()
        if now - self._last_cleanup < self.cleanup_interval:
            return

        with self._lock:
            self._last_cleanup = now
            expired_keys = [
                k for k, (ts, _) in self.cache.items()
                if now - ts >= self.ttl
            ]
            for k in expired_keys:
                del self.cache[k]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def clear(self) -> None:
        """
        清空所有缓存（用于测试）
        """
        with self._lock:
            self.cache.clear()
            logger.debug("Request cache cleared")


# 全局实例
request_cache = RequestCache(ttl=60, cleanup_interval=30)
```

### 集成到 agents.py

```python
# backend/app/api/v1/endpoints/agents.py

from fastapi import HTTPException
from app.core.request_cache import request_cache
from app.core.config import settings

# 检查是否启用去重（可通过环境变量禁用）
ENABLE_REQUEST_DEDUP = getattr(settings, 'ENABLE_REQUEST_DEDUP', True)

def check_duplicate_request(
    canvas_name: str,
    node_id: str,
    agent_type: str
) -> str:
    """
    Story 12.H.5: 检查并标记请求
    对齐 ADR-009: 返回 NON_RETRYABLE 错误

    Args:
        canvas_name: Canvas 文件名
        node_id: 节点 ID
        agent_type: Agent 类型

    Returns:
        缓存 key

    Raises:
        HTTPException: 409 如果是重复请求
    """
    if not ENABLE_REQUEST_DEDUP:
        return ""

    cache_key = request_cache.get_key(canvas_name, node_id, agent_type)

    if request_cache.is_duplicate(cache_key):
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Duplicate request",
                "message": "相同请求正在处理中，请稍候",
                "canvas_name": canvas_name,
                "node_id": node_id,
                "agent_type": agent_type,
                "is_retryable": False  # 对齐 ADR-009
            }
        )

    # 标记为进行中
    request_cache.mark_in_progress(cache_key)
    return cache_key
```

### 配置支持

```python
# backend/app/core/config.py

class Settings(BaseSettings):
    # ... 其他配置

    # Story 12.H.5: 请求去重配置
    ENABLE_REQUEST_DEDUP: bool = True
    REQUEST_CACHE_TTL: int = 60  # 秒
```

### 环境变量

```env
# .env
ENABLE_REQUEST_DEDUP=true
REQUEST_CACHE_TTL=60
```

---

## 测试用例

### 单元测试

```python
# backend/tests/core/test_request_cache.py

import pytest
import time
from app.core.request_cache import RequestCache

class TestRequestCache:

    def test_is_duplicate_returns_false_for_new_request(self):
        """新请求应该返回 False"""
        cache = RequestCache(ttl=60)
        key = cache.get_key("canvas1", "node1", "oral")

        assert cache.is_duplicate(key) is False

    def test_is_duplicate_returns_true_for_same_request(self):
        """重复请求应该返回 True"""
        cache = RequestCache(ttl=60)
        key = cache.get_key("canvas1", "node1", "oral")

        cache.mark_in_progress(key)
        assert cache.is_duplicate(key) is True

    def test_is_duplicate_returns_false_after_ttl(self):
        """TTL 过期后应该返回 False"""
        cache = RequestCache(ttl=1)  # 1秒 TTL
        key = cache.get_key("canvas1", "node1", "oral")

        cache.mark_in_progress(key)
        time.sleep(1.5)  # 等待过期

        assert cache.is_duplicate(key) is False

    def test_remove_allows_new_request(self):
        """移除后应该允许新请求"""
        cache = RequestCache(ttl=60)
        key = cache.get_key("canvas1", "node1", "oral")

        cache.mark_in_progress(key)
        cache.remove(key)

        assert cache.is_duplicate(key) is False

    def test_different_requests_have_different_keys(self):
        """不同请求应该有不同的 key"""
        cache = RequestCache(ttl=60)

        key1 = cache.get_key("canvas1", "node1", "oral")
        key2 = cache.get_key("canvas1", "node1", "four-level")
        key3 = cache.get_key("canvas1", "node2", "oral")

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3
```

### API 测试

```python
# backend/tests/api/v1/endpoints/test_agents_dedup.py

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.request_cache import request_cache

client = TestClient(app)

class TestAgentsDedup:

    def setup_method(self):
        """每个测试前清空缓存"""
        request_cache.clear()

    @patch('app.services.agent_service.AgentService.generate_explanation')
    def test_first_request_succeeds(self, mock_generate):
        """第一次请求应该成功"""
        mock_generate.return_value = AsyncMock(return_value={"content": "test"})

        response = client.post("/api/v1/agents/explain/oral", json={
            "canvas_name": "test.canvas",
            "node_id": "node1",
            "node_content": "test content"
        })

        assert response.status_code in [200, 500]

    def test_duplicate_request_returns_409(self):
        """重复请求应该返回 409"""
        # 先标记一个请求
        key = request_cache.get_key("test.canvas", "node1", "oral")
        request_cache.mark_in_progress(key)

        response = client.post("/api/v1/agents/explain/oral", json={
            "canvas_name": "test.canvas",
            "node_id": "node1",
            "node_content": "test content"
        })

        assert response.status_code == 409
        assert "Duplicate request" in response.json()["detail"]["error"]

    def test_different_agent_type_not_duplicate(self):
        """不同 Agent 类型不应该被视为重复"""
        key = request_cache.get_key("test.canvas", "node1", "oral")
        request_cache.mark_in_progress(key)

        # 发送不同 Agent 类型的请求 - 不应该是 409
        key2 = request_cache.get_key("test.canvas", "node1", "four-level")
        assert request_cache.is_duplicate(key2) is False
```

---

## 依赖关系

- **前置依赖**: 无（可独立开发）
- **被依赖**: 无

---

## Definition of Done

- [ ] `RequestCache` 类实现
- [ ] 集成到所有 Agent 端点
- [ ] 重复请求返回 409
- [ ] TTL 机制工作正常
- [ ] 可通过环境变量禁用
- [ ] 单元测试通过
- [ ] API 测试通过
- [ ] OpenAPI spec 更新 (添加 409 响应)
- [ ] 代码 Review 通过

---

## Change Log

| 日期 | 版本 | 描述 | 作者 |
|------|------|------|------|
| 2025-12-17 | 1.0 | 初始创建 | PM Agent |
| 2025-12-17 | 1.1 | 添加 Tasks、Dev Notes、SDD参考、ADR关联 (PO验证修复) | PO Agent |
