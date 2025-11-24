---
document_type: "Architecture"
version: "1.0.0"
last_modified: "2025-11-23"
status: "draft"
iteration: 5

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

compatible_with:
  prd: "v1.1.8"
  epic: ["Epic 11", "Epic 13"]

changes_from_previous:
  - "Initial WebSocket Real-time Architecture document"
---

# WebSocket实时通信架构

**版本**: v1.0.0
**创建日期**: 2025-11-23
**架构师**: Architect Agent

---

## 1. 概述

本文档定义Canvas Learning System的WebSocket实时通信架构，实现Obsidian插件与FastAPI后端的双向实时通信。

### 1.1 设计目标

- 低延迟双向通信
- 断线自动重连
- 消息队列管理
- 并发请求处理

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                  WebSocket通信架构                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Obsidian Plugin                    FastAPI Backend     │
│  ┌─────────────┐                   ┌─────────────┐     │
│  │ WS Client   │◄──── WebSocket ───►│ WS Server   │     │
│  └──────┬──────┘                   └──────┬──────┘     │
│         │                                 │             │
│  ┌──────▼──────┐                   ┌──────▼──────┐     │
│  │ Message     │                   │ Connection  │     │
│  │ Queue       │                   │ Manager     │     │
│  └──────┬──────┘                   └──────┬──────┘     │
│         │                                 │             │
│  ┌──────▼──────┐                   ┌──────▼──────┐     │
│  │ Event       │                   │ Agent       │     │
│  │ Handler     │                   │ Executor    │     │
│  └─────────────┘                   └─────────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 消息协议

### 3.1 消息格式

```typescript
// 基础消息结构
interface WSMessage {
    id: string;           // 消息唯一ID
    type: MessageType;    // 消息类型
    timestamp: number;    // 时间戳
    payload: any;         // 消息内容
}

type MessageType =
    // 客户端 → 服务端
    | 'analysis_request'      // 分析请求
    | 'batch_analysis_request'// 批量分析
    | 'review_complete'       // 复习完成
    | 'canvas_update'         // Canvas更新
    | 'ping'                  // 心跳

    // 服务端 → 客户端
    | 'analysis_result'       // 分析结果
    | 'analysis_progress'     // 分析进度
    | 'review_reminder'       // 复习提醒
    | 'error'                 // 错误
    | 'pong';                 // 心跳响应
```

### 3.2 请求消息

```typescript
// 分析请求
interface AnalysisRequest {
    nodeId: string;
    content: string;
    context: string[];
    agentId: string;
    options?: {
        depth?: 'shallow' | 'deep';
        outputFormat?: 'text' | 'canvas';
    };
}

// 批量分析请求
interface BatchAnalysisRequest {
    nodes: Array<{
        nodeId: string;
        content: string;
    }>;
    agentId: string;
    parallel: boolean;
}

// Canvas更新通知
interface CanvasUpdateNotification {
    canvasPath: string;
    changeType: 'node_added' | 'node_modified' | 'node_deleted';
    nodeIds: string[];
}
```

### 3.3 响应消息

```typescript
// 分析结果
interface AnalysisResult {
    requestId: string;
    nodeId: string;
    success: boolean;
    result?: {
        content: string;
        newNodes?: CanvasNode[];
        newEdges?: CanvasEdge[];
        colorUpdate?: string;
        score?: number;
    };
    error?: string;
}

// 分析进度
interface AnalysisProgress {
    requestId: string;
    stage: 'queued' | 'processing' | 'generating' | 'completed';
    progress: number;  // 0-100
    message: string;
}
```

---

## 4. FastAPI服务端

### 4.1 WebSocket端点

```python
# ✅ Verified from FastAPI WebSocket Context7 documentation
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict
import json
import asyncio

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()

            # 处理消息
            response = await process_message(client_id, data)

            # 发送响应
            if response:
                await manager.send_message(client_id, response)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
```

### 4.2 消息处理器

```python
from typing import Optional

async def process_message(
    client_id: str,
    message: dict
) -> Optional[dict]:
    """处理WebSocket消息"""
    msg_type = message.get('type')
    msg_id = message.get('id')
    payload = message.get('payload', {})

    if msg_type == 'ping':
        return {
            'id': msg_id,
            'type': 'pong',
            'timestamp': time.time()
        }

    elif msg_type == 'analysis_request':
        # 发送进度更新
        await manager.send_message(client_id, {
            'id': msg_id,
            'type': 'analysis_progress',
            'payload': {
                'requestId': msg_id,
                'stage': 'processing',
                'progress': 10,
                'message': '正在分析...'
            }
        })

        # 执行分析
        result = await execute_analysis(payload)

        return {
            'id': msg_id,
            'type': 'analysis_result',
            'timestamp': time.time(),
            'payload': result
        }

    elif msg_type == 'batch_analysis_request':
        # 批量分析处理
        await handle_batch_analysis(client_id, msg_id, payload)
        return None  # 通过单独的消息返回结果

    return None

async def handle_batch_analysis(
    client_id: str,
    request_id: str,
    payload: dict
):
    """处理批量分析请求"""
    nodes = payload['nodes']
    total = len(nodes)

    if payload.get('parallel', False):
        # 并行处理
        tasks = [
            execute_analysis({
                'nodeId': node['nodeId'],
                'content': node['content'],
                'agentId': payload['agentId']
            })
            for node in nodes
        ]

        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task

            # 发送单个结果
            await manager.send_message(client_id, {
                'id': f"{request_id}_{i}",
                'type': 'analysis_result',
                'payload': result
            })

            # 发送进度
            await manager.send_message(client_id, {
                'id': request_id,
                'type': 'analysis_progress',
                'payload': {
                    'stage': 'processing',
                    'progress': int((i + 1) / total * 100),
                    'message': f'已完成 {i + 1}/{total}'
                }
            })
    else:
        # 顺序处理
        for i, node in enumerate(nodes):
            result = await execute_analysis({
                'nodeId': node['nodeId'],
                'content': node['content'],
                'agentId': payload['agentId']
            })

            await manager.send_message(client_id, {
                'id': f"{request_id}_{i}",
                'type': 'analysis_result',
                'payload': result
            })
```

---

## 5. Obsidian客户端

### 5.1 WebSocket客户端

```typescript
// ✅ Based on WebSocket API patterns
type MessageHandler = (message: WSMessage) => void;

class WebSocketClient {
    private ws: WebSocket | null = null;
    private url: string;
    private clientId: string;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;
    private handlers: Map<string, MessageHandler> = new Map();
    private pendingRequests: Map<string, {
        resolve: Function;
        reject: Function;
        timeout: NodeJS.Timeout;
    }> = new Map();

    constructor(url: string, clientId: string) {
        this.url = url;
        this.clientId = clientId;
    }

    connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            const wsUrl = `${this.url}/${this.clientId}`;
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                this.reconnectAttempts = 0;
                this.startHeartbeat();
                resolve();
            };

            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data) as WSMessage;
                this.handleMessage(message);
            };

            this.ws.onclose = () => {
                this.handleDisconnect();
            };

            this.ws.onerror = (error) => {
                reject(error);
            };
        });
    }

    private handleMessage(message: WSMessage): void {
        // 检查是否是pending request的响应
        if (this.pendingRequests.has(message.id)) {
            const pending = this.pendingRequests.get(message.id)!;
            clearTimeout(pending.timeout);
            this.pendingRequests.delete(message.id);

            if (message.type === 'error') {
                pending.reject(new Error(message.payload.message));
            } else {
                pending.resolve(message.payload);
            }
            return;
        }

        // 调用类型处理器
        const handler = this.handlers.get(message.type);
        if (handler) {
            handler(message);
        }
    }

    async send<T>(
        type: MessageType,
        payload: any,
        timeout: number = 30000
    ): Promise<T> {
        return new Promise((resolve, reject) => {
            const id = this.generateId();

            const message: WSMessage = {
                id,
                type,
                timestamp: Date.now(),
                payload
            };

            // 设置超时
            const timeoutId = setTimeout(() => {
                this.pendingRequests.delete(id);
                reject(new Error('Request timeout'));
            }, timeout);

            // 保存pending request
            this.pendingRequests.set(id, {
                resolve,
                reject,
                timeout: timeoutId
            });

            // 发送消息
            if (this.ws?.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify(message));
            } else {
                this.pendingRequests.delete(id);
                clearTimeout(timeoutId);
                reject(new Error('WebSocket not connected'));
            }
        });
    }

    on(type: MessageType, handler: MessageHandler): void {
        this.handlers.set(type, handler);
    }

    off(type: MessageType): void {
        this.handlers.delete(type);
    }

    private handleDisconnect(): void {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

            setTimeout(() => {
                this.connect().catch(() => {
                    // Reconnection failed, will retry
                });
            }, delay);
        }
    }

    private startHeartbeat(): void {
        setInterval(() => {
            if (this.ws?.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    id: this.generateId(),
                    type: 'ping',
                    timestamp: Date.now()
                }));
            }
        }, 30000);
    }

    private generateId(): string {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    disconnect(): void {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}
```

### 5.2 分析服务

```typescript
class AnalysisService {
    private wsClient: WebSocketClient;

    constructor(wsClient: WebSocketClient) {
        this.wsClient = wsClient;

        // 注册进度处理器
        this.wsClient.on('analysis_progress', (msg) => {
            this.onProgress(msg.payload);
        });
    }

    async analyzeNode(
        nodeId: string,
        content: string,
        agentId: string
    ): Promise<AnalysisResult> {
        return this.wsClient.send<AnalysisResult>(
            'analysis_request',
            {
                nodeId,
                content,
                agentId,
                context: []
            }
        );
    }

    async batchAnalyze(
        nodes: Array<{ nodeId: string; content: string }>,
        agentId: string,
        parallel: boolean = true
    ): Promise<void> {
        await this.wsClient.send(
            'batch_analysis_request',
            {
                nodes,
                agentId,
                parallel
            }
        );
    }

    private onProgress(progress: AnalysisProgress): void {
        // 更新UI进度
        console.log(`Progress: ${progress.progress}% - ${progress.message}`);
    }
}
```

---

## 6. 消息队列

### 6.1 服务端队列

```python
import asyncio
from collections import deque

class MessageQueue:
    def __init__(self, max_size: int = 1000):
        self.queue: deque = deque(maxlen=max_size)
        self.processing = False

    async def enqueue(self, message: dict) -> None:
        self.queue.append(message)
        if not self.processing:
            asyncio.create_task(self.process_queue())

    async def process_queue(self) -> None:
        self.processing = True
        while self.queue:
            message = self.queue.popleft()
            await self.process_message(message)
        self.processing = False

    async def process_message(self, message: dict) -> None:
        # 处理消息逻辑
        pass
```

### 6.2 客户端队列

```typescript
class ClientMessageQueue {
    private queue: WSMessage[] = [];
    private processing = false;
    private wsClient: WebSocketClient;

    constructor(wsClient: WebSocketClient) {
        this.wsClient = wsClient;
    }

    enqueue(message: WSMessage): void {
        this.queue.push(message);
        if (!this.processing) {
            this.processQueue();
        }
    }

    private async processQueue(): Promise<void> {
        this.processing = true;

        while (this.queue.length > 0) {
            const message = this.queue.shift()!;
            try {
                await this.wsClient.send(
                    message.type,
                    message.payload
                );
            } catch (error) {
                // 失败的消息重新入队
                this.queue.unshift(message);
                break;
            }
        }

        this.processing = false;
    }
}
```

---

## 7. 错误处理

### 7.1 错误类型

```typescript
interface WSError {
    code: string;
    message: string;
    details?: any;
}

const ERROR_CODES = {
    CONNECTION_FAILED: 'WS_CONNECTION_FAILED',
    TIMEOUT: 'WS_TIMEOUT',
    INVALID_MESSAGE: 'WS_INVALID_MESSAGE',
    ANALYSIS_FAILED: 'ANALYSIS_FAILED',
    RATE_LIMITED: 'RATE_LIMITED'
};
```

### 7.2 错误处理

```python
# 服务端错误处理
async def safe_process_message(
    client_id: str,
    message: dict
) -> Optional[dict]:
    try:
        return await process_message(client_id, message)
    except ValidationError as e:
        return {
            'type': 'error',
            'payload': {
                'code': 'INVALID_MESSAGE',
                'message': str(e)
            }
        }
    except TimeoutError:
        return {
            'type': 'error',
            'payload': {
                'code': 'TIMEOUT',
                'message': 'Request timed out'
            }
        }
    except Exception as e:
        return {
            'type': 'error',
            'payload': {
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error'
            }
        }
```

---

## 8. 配置

```yaml
# websocket_config.yaml
server:
  host: "0.0.0.0"
  port: 8000
  path: "/ws"
  max_connections: 100

client:
  reconnect_attempts: 5
  reconnect_delay: 1000
  heartbeat_interval: 30000
  request_timeout: 30000

queue:
  max_size: 1000
  batch_size: 10
```

---

## 9. 相关文档

- [FastAPI后端架构](EPIC-11-BACKEND-ARCHITECTURE.md)
- [Obsidian插件架构](obsidian-plugin-architecture.md)
- [UI组件架构](ui-component-architecture.md)

---

**文档版本**: v1.0.0
**最后更新**: 2025-11-23
**维护者**: Architect Agent
