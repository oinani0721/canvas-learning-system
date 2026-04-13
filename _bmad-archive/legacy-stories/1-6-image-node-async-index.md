# Story 1.6: 图片节点与异步索引状态

Status: ready-for-dev

## Story

As a 用户,
I want 粘贴图片到白板时生成图片节点，后台异步通过 Vision API 提取文字/公式/概念建立搜索索引，并显示索引状态,
so that 我的图片内容将来可以被 AI 搜索到，同时贴图后立刻可以对话。

## Acceptance Criteria

1. **AC-1: 图片粘贴生成图片节点**
   - **Given** 用户在白板上按 Ctrl+V 粘贴剪贴板中的图片（PNG/JPG/WebP）
   - **When** CanvasView 捕获到 paste 事件且 clipboardData 包含图片
   - **Then** 在鼠标当前位置（或白板中心）创建一个 ImageNode
   - **And** 图片数据以 base64 DataURL 存入 IndexedDB `canvas_nodes` 表的 `imageData` 字段
   - **And** 节点 `type` 字段设为 `'image'`
   - **And** 节点缩略图渲染为 `<img>` 标签，宽度适配节点宽度（默认 240px）
   - **And** 图片节点同时写入 `sync_outbox`（复用 Story 1.5 的 delta sync 管道同步到 Neo4j）

2. **AC-2: 图片拖放创建节点**
   - **Given** 用户从文件管理器或浏览器拖拽图片文件到白板
   - **When** CanvasView 捕获到 drop 事件且 dataTransfer 包含图片文件
   - **Then** 行为与粘贴一致：在 drop 位置创建 ImageNode
   - **And** 支持同时拖入多张图片，每张生成独立节点（水平排列，间距 20px）

3. **AC-3: 索引状态指示——建立中**
   - **Given** 图片节点刚创建
   - **When** 节点渲染
   - **Then** 节点底部显示索引状态条："🔄 索引建立中..."
   - **And** 状态条使用 Obsidian CSS 变量 `--text-muted` 色彩，不喧宾夺主
   - **And** 状态条包含轻微动画（脉冲或旋转图标），暗示后台进行中

4. **AC-4: 后台异步 OCR 提取（不阻塞 UI）**
   - **Given** 图片节点创建后
   - **When** IndexingService 检测到新的 image 类型节点
   - **Then** 后台异步调用后端 `POST /api/v1/index/image` 发送图片数据
   - **And** 后端使用 Vision API（LiteLLM 统一层调用配置的多模态模型）提取文字/公式/概念
   - **And** 提取结果包含：`ocrText`（原文）、`summary`（摘要）、`concepts`（概念列表）
   - **And** 整个 OCR 过程不阻塞白板 UI——用户可以继续拖拽、创建节点、打开对话
   - **And** 单张图片 OCR 处理 < 10s（NFR-PERF-05）

5. **AC-5: OCR 结果回写与索引更新**
   - **Given** 后端 OCR 提取完成返回结果
   - **When** 前端 IndexingService 收到成功响应
   - **Then** 将 `ocrText`/`summary`/`concepts` 写入 IndexedDB 对应节点记录
   - **And** 更新 IndexedDB 节点的 `indexStatus` 从 `'indexing'` 变为 `'indexed'`
   - **And** 同步写入 `sync_outbox`（触发 Story 1.5 delta sync 将 OCR 数据同步到 Neo4j）
   - **And** 后端 sync 接收到包含 OCR 数据的节点更新后，将文本内容写入 LanceDB 向量索引（预留接口，Story 2.9 完整实现检索管道）

6. **AC-6: 索引状态指示——已完成**
   - **Given** OCR 提取完成且 `indexStatus` 更新为 `'indexed'`
   - **When** Dexie liveQuery 触发 UI 更新
   - **Then** 节点底部状态条变为："✅ 已加入搜索索引"
   - **And** 成功状态显示 3 秒后自动淡出（不持续占空间）
   - **And** 用户可在节点上下文菜单（右键）中查看"OCR 提取结果"

7. **AC-7: 索引失败处理**
   - **Given** OCR 提取过程中发生错误（Vision API 超时/不可用/图片格式不支持）
   - **When** 前端 IndexingService 收到错误响应
   - **Then** 节点底部状态条变为："⚠️ 索引失败，点击重试"
   - **And** `indexStatus` 设为 `'failed'`
   - **And** 点击状态条触发重新提交 OCR 请求
   - **And** 通过 Obsidian Notice 提示具体错误原因
   - **And** 索引失败不影响图片节点的正常显示和交互

8. **AC-8: 对话功能不受索引状态影响**
   - **Given** 图片节点的 `indexStatus` 为任意状态（`indexing`/`indexed`/`failed`）
   - **When** 用户点击图片节点
   - **Then** 右侧面板正常打开对话窗口（复用 Story 3.1 的 per-node session）
   - **And** 对话层通过 Agent 原生多模态能力直接"看到"图片（base64 传入 Agent prompt）
   - **And** 索引状态仅影响搜索检索能力，不影响对话能力
   - **And** 对话面板中图片以缩略图形式展示在消息上方区域

## Tasks / Subtasks

- [ ] **Task 1: IndexedDB Schema 升级——图片节点字段** (AC: #1, #5)
  - [ ] 1.1 修改 `obsidian-canvas-learning/src/services/dexie-db.ts`：
    - 新增 Schema version 2（不破坏 version 1 的数据）：
      ```typescript
      this.version(2).stores({
        canvas_nodes: 'id, canvasId, type, createdAt, updatedAt, indexStatus'
      }).upgrade(tx => {
        // 为已有节点添加默认 indexStatus
        return tx.table('canvas_nodes').toCollection().modify(node => {
          if (node.type === 'image' && !node.indexStatus) {
            node.indexStatus = 'none';
          }
        });
      });
      ```
  - [ ] 1.2 修改 `obsidian-canvas-learning/src/types/canvas.d.ts`：
    - 扩展 `CanvasNodeData` 类型：
      ```typescript
      interface CanvasNodeData {
        // ... Story 1.4 已有字段 ...
        type: 'text' | 'image';
        imageData?: string;           // base64 DataURL（仅 image 类型）
        indexStatus?: 'none' | 'indexing' | 'indexed' | 'failed';
        ocrText?: string;             // OCR 提取的原文
        ocrSummary?: string;          // OCR 提取的摘要
        ocrConcepts?: string[];       // OCR 提取的概念列表
        ocrError?: string;            // OCR 失败时的错误信息
      }
      ```

- [ ] **Task 2: ImageNode 组件** (AC: #1, #2, #3, #6, #7)
  - [ ] 2.1 创建 `obsidian-canvas-learning/src/components/canvas/ImageNode.svelte`
  - [ ] 2.2 实现图片节点结构：
    ```html
    <div class="cl-canvas-node cl-canvas-node--image"
         class:cl-canvas-node--selected={isSelected}
         style="left: {node.x}px; top: {node.y}px; width: {node.width}px">
      <!-- Header 区域：拖拽手柄（复用 CanvasNode 的拖拽逻辑） -->
      <div class="cl-canvas-node-header" onmousedown={startDrag}>
        {node.title || '图片节点'}
      </div>
      <!-- Body 区域：图片缩略图 -->
      <div class="cl-canvas-node-body cl-canvas-node-body--image">
        <img src={node.imageData}
             alt={node.title}
             class="cl-image-node-thumbnail"
             loading="lazy" />
      </div>
      <!-- 索引状态条 -->
      <div class="cl-image-node-index-status"
           class:cl-image-node-index-status--indexing={node.indexStatus === 'indexing'}
           class:cl-image-node-index-status--indexed={node.indexStatus === 'indexed'}
           class:cl-image-node-index-status--failed={node.indexStatus === 'failed'}
           onclick={node.indexStatus === 'failed' ? retryIndex : undefined}>
        {#if node.indexStatus === 'indexing'}
          <span class="cl-image-node-spinner">🔄</span> 索引建立中...
        {:else if node.indexStatus === 'indexed'}
          <span class="cl-image-node-check">✅</span> 已加入搜索索引
        {:else if node.indexStatus === 'failed'}
          <span class="cl-image-node-warn">⚠️</span> 索引失败，点击重试
        {/if}
      </div>
      <!-- 连线端口（复用 CanvasNode 的端口逻辑） -->
      <div class="cl-canvas-node-port cl-canvas-node-port--right"
           onmousedown={startEdgeDrag} />
    </div>
    ```
  - [ ] 2.3 实现索引完成后的淡出效果：
    - `indexStatus` 变为 `'indexed'` 时启动 3s 定时器
    - 3s 后添加 `cl-image-node-index-status--fadeout` class（CSS transition opacity）
    - 淡出完成后隐藏状态条
  - [ ] 2.4 CSS 样式（Svelte scoped + Obsidian 变量）：
    - 图片缩略图：`max-width: 100%; border-radius: var(--radius-s)`
    - 状态条：`font-size: var(--font-smaller); color: var(--text-muted); padding: 4px 8px`
    - indexing 动画：`@keyframes cl-pulse { 0% { opacity: 0.6 } 50% { opacity: 1 } 100% { opacity: 0.6 } }`
    - failed 样式：`color: var(--text-error); cursor: pointer`
    - fadeout 过渡：`transition: opacity 0.5s ease-out`
    - 适配 Light/Dark 主题

- [ ] **Task 3: CanvasView 图片粘贴与拖放事件处理** (AC: #1, #2)
  - [ ] 3.1 修改 `obsidian-canvas-learning/src/components/canvas/CanvasView.svelte`：
    - 追加 `paste` 事件监听到白板容器
    - 追加 `dragover` + `drop` 事件监听到白板容器
  - [ ] 3.2 实现 paste 事件处理：
    ```typescript
    function handlePaste(event: ClipboardEvent) {
      const items = event.clipboardData?.items;
      if (!items) return;

      for (const item of items) {
        if (item.type.startsWith('image/')) {
          event.preventDefault();
          const blob = item.getAsFile();
          if (blob) createImageNode(blob);
        }
      }
    }
    ```
  - [ ] 3.3 实现 drop 事件处理：
    ```typescript
    function handleDrop(event: DragEvent) {
      event.preventDefault();
      const files = event.dataTransfer?.files;
      if (!files) return;

      let offsetX = 0;
      for (const file of files) {
        if (file.type.startsWith('image/')) {
          const dropPos = screenToCanvas(event.clientX + offsetX, event.clientY);
          createImageNode(file, dropPos);
          offsetX += 260; // 节点宽度 240 + 间距 20
        }
      }
    }
    ```
  - [ ] 3.4 实现 `createImageNode()` 核心函数：
    - 使用 FileReader 将图片 Blob 转换为 base64 DataURL
    - 图片大小限制：> 10MB 时提示用户压缩（Notice 提示）
    - 调用 `canvasState.addNode({ type: 'image', imageData: dataUrl, indexStatus: 'indexing', ... })`
    - 节点创建后立即调用 `indexingService.requestImageIndex(nodeId, dataUrl)`
  - [ ] 3.5 实现 `screenToCanvas()` 坐标转换：
    - 将屏幕坐标转换为白板画布坐标（考虑 viewport.x/y/zoom）

- [ ] **Task 4: CanvasView 条件渲染 ImageNode** (AC: #1)
  - [ ] 4.1 修改 `obsidian-canvas-learning/src/components/canvas/CanvasView.svelte` 节点渲染区域：
    ```html
    {#each visibleNodes as node}
      {#if node.type === 'image'}
        <ImageNode {node} />
      {:else}
        <CanvasNode {node} />
      {/if}
    {/each}
    ```
  - [ ] 4.2 在 CanvasView 中 import ImageNode 组件

- [ ] **Task 5: IndexingService——前端异步索引管理** (AC: #4, #5, #7)
  - [ ] 5.1 创建 `obsidian-canvas-learning/src/services/indexing-service.ts`
  - [ ] 5.2 实现 `IndexingService` class：
    ```typescript
    class IndexingService {
      private pendingQueue: Map<string, AbortController> = new Map();

      async requestImageIndex(nodeId: string, imageData: string): Promise<void> {
        // 已有相同 nodeId 的请求则跳过（防重复提交）
        if (this.pendingQueue.has(nodeId)) return;

        const controller = new AbortController();
        this.pendingQueue.set(nodeId, controller);

        try {
          const result = await apiClient.indexImage(nodeId, imageData, controller.signal);
          // 成功：更新 IndexedDB 节点数据
          await canvasState.updateNode(nodeId, {
            ocrText: result.ocrText,
            ocrSummary: result.summary,
            ocrConcepts: result.concepts,
            indexStatus: 'indexed',
            ocrError: undefined
          });
        } catch (error) {
          if (error.name === 'AbortError') return;
          // 失败：更新错误状态
          await canvasState.updateNode(nodeId, {
            indexStatus: 'failed',
            ocrError: error.message
          });
          new Notice(`图片索引失败: ${error.message}`, 5000);
        } finally {
          this.pendingQueue.delete(nodeId);
        }
      }

      async retryIndex(nodeId: string): Promise<void> {
        // 重置状态为 indexing 并重新请求
        await canvasState.updateNode(nodeId, { indexStatus: 'indexing', ocrError: undefined });
        const node = await db.canvas_nodes.get(nodeId);
        if (node?.imageData) {
          await this.requestImageIndex(nodeId, node.imageData);
        }
      }

      cancelAll(): void {
        for (const controller of this.pendingQueue.values()) {
          controller.abort();
        }
        this.pendingQueue.clear();
      }
    }
    ```
  - [ ] 5.3 导出 singleton `export const indexingService = new IndexingService()`
  - [ ] 5.4 在 Plugin `onunload` 中调用 `indexingService.cancelAll()` 取消未完成的请求

- [ ] **Task 6: API Client 扩展——图片索引 API** (AC: #4)
  - [ ] 6.1 修改 `obsidian-canvas-learning/src/services/api-client.ts`：
    - 追加 `indexImage(nodeId: string, imageData: string, signal?: AbortSignal): Promise<ImageIndexResult>` 方法
    - 请求体：`{ node_id: nodeId, image_data: imageData }`（camelCase 转 snake_case）
    - 响应类型：`ImageIndexResult { ocrText: string; summary: string; concepts: string[] }`
  - [ ] 6.2 追加前端类型定义到 `obsidian-canvas-learning/src/types/api.d.ts`：
    - `ImageIndexRequest`、`ImageIndexResult`

- [ ] **Task 7: 后端图片索引 API 端点** (AC: #4, #5)
  - [ ] 7.1 创建 `backend/app/api/v1/index_image.py`：
    - `POST /api/v1/index/image` 接收图片数据，调用 Vision API，返回提取结果
    ```python
    class ImageIndexRequest(BaseModel):
        node_id: str
        image_data: str  # base64 DataURL

    class ImageIndexResponse(BaseModel):
        node_id: str
        ocr_text: str
        summary: str
        concepts: list[str]
        processing_time_ms: int
    ```
  - [ ] 7.2 实现 Vision API 调用（LiteLLM 统一层）：
    ```python
    async def extract_image_content(image_data: str) -> ImageIndexResponse:
        # 通过 LiteLLM 调用配置的多模态模型
        response = await litellm.acompletion(
            model=settings.vision_model,  # 用户在 Settings 配置的多模态模型
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": EXTRACTION_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_data}}
                ]
            }],
            response_format={"type": "json_object"}
        )
        # 解析结构化输出
        result = json.loads(response.choices[0].message.content)
        return ImageIndexResponse(
            ocr_text=result["ocr_text"],
            summary=result["summary"],
            concepts=result["concepts"]
        )
    ```
  - [ ] 7.3 定义提取 Prompt（结构化输出）：
    ```python
    EXTRACTION_PROMPT = """请分析这张图片，提取以下信息并以 JSON 格式返回：
    {
      "ocr_text": "图片中所有可见文字的完整转录（保留原始格式，公式使用 LaTeX 表示）",
      "summary": "图片内容的一句话摘要",
      "concepts": ["提取的核心概念/术语列表"]
    }
    注意：
    - 数学公式使用 LaTeX 格式（如 $E=mc^2$）
    - 代码块保持原始格式
    - 概念列表提取 3-10 个核心术语"""
    ```
  - [ ] 7.4 超时与错误处理：
    - 单次 Vision API 调用超时 30s（预留网络延迟，目标 < 10s）
    - 图片格式不支持时返回 400 Bad Request + 具体原因
    - Vision API 不可用时返回 503 Service Unavailable
    - base64 解码失败时返回 400 Bad Request
  - [ ] 7.5 在 `backend/app/main.py` 的 FastAPI router 中注册 index_image API

- [ ] **Task 8: 后端 Sync Service 扩展——图片节点 Neo4j 写入** (AC: #1, #5)
  - [ ] 8.1 修改 `backend/app/services/sync_service.py`：
    - 图片节点同步时，Neo4j 节点额外携带 `ocrText`、`ocrSummary`、`ocrConcepts`、`indexStatus` 属性
    - `imageData`（base64）不写入 Neo4j（太大），仅前端 IndexedDB 保存原始图片
    ```cypher
    MERGE (n:CanvasNode {id: $entity_id})
    SET n.title = $title,
        n.type = 'image',
        n.ocrText = $ocr_text,
        n.ocrSummary = $ocr_summary,
        n.ocrConcepts = $ocr_concepts,
        n.indexStatus = $index_status,
        n.canvasId = $canvas_id,
        n.subjectId = $subject_id,
        n.updatedAt = $timestamp
    ON CREATE SET n.createdAt = $timestamp
    ```
  - [ ] 8.2 OCR 数据同步到 Neo4j 后，预留 LanceDB 索引触发接口（Story 2.9 完整实现检索管道）：
    - 在 sync_service 的图片节点处理分支中添加注释标记未来扩展点
    - 当前仅将 OCR 文本写入 Neo4j 属性，向量化索引由 Story 2.9 负责

- [ ] **Task 9: 节点右键菜单——查看 OCR 结果** (AC: #6)
  - [ ] 9.1 修改节点右键菜单（CanvasView 或 ImageNode 中的 contextmenu 处理）：
    - 对 image 类型节点且 `indexStatus === 'indexed'`，追加菜单项"查看 OCR 结果"
    - 使用 Obsidian `Menu` API：
      ```typescript
      menu.addItem(item => {
        item.setTitle('查看 OCR 提取结果');
        item.setIcon('file-text');
        item.onClick(() => showOcrResult(node));
      });
      ```
  - [ ] 9.2 OCR 结果展示：
    - 使用 Obsidian `Modal` 展示 OCR 提取结果
    - 包含三个区域：原文（ocrText）、摘要（ocrSummary）、概念（ocrConcepts 标签列表）

- [ ] **Task 10: 集成与端到端验证** (AC: #1~#8)
  - [ ] 10.1 端到端验证场景——粘贴流程：
    - 复制一张包含公式的课件截图 Ctrl+V 粘贴到白板
    - 确认：ImageNode 出现，显示图片缩略图，底部显示"🔄 索引建立中..."
    - 等待 OCR 完成（< 10s），状态变为"✅ 已加入搜索索引"，3s 后淡出
    - 右键查看 OCR 结果，确认文字和公式正确提取
  - [ ] 10.2 端到端验证场景——拖放流程：
    - 从文件管理器拖入 2 张图片，确认 2 个 ImageNode 并排出现
    - 两个节点各自独立进行 OCR，各自显示索引状态
  - [ ] 10.3 端到端验证场景——失败与重试：
    - 停止后端，粘贴图片，确认显示"⚠️ 索引失败，点击重试"
    - 启动后端，点击重试，确认状态变为"🔄 索引建立中..."，成功后变为"✅ 已加入搜索索引"
  - [ ] 10.4 端到端验证场景——对话不受索引影响：
    - 粘贴图片，索引进行中，点击图片节点打开对话面板
    - 确认对话可正常进行（对话引擎 Story 3.1 实现前，验证右侧面板切换到对话占位 UI）
  - [ ] 10.5 Neo4j 同步验证：
    - 粘贴图片，等待 OCR 完成，等待 delta sync
    - 检查 Neo4j 中节点包含 `type: 'image'`、`ocrText`、`indexStatus: 'indexed'` 属性
    - 确认 `imageData` 不在 Neo4j 中（节省存储）

## Dev Notes

### Brownfield 上下文

Story 1.4 已创建白板 CRUD 核心功能，包含：
- `dexie-db.ts`：IndexedDB Schema v1（`canvas_boards`、`canvas_nodes`、`canvas_edges`、`sync_outbox` 四张表）
- `canvas-state.svelte.ts`：白板状态 Store，`CanvasNodeData` 已有 `type: 'text' | 'image'` 字段
- `CanvasView.svelte`：白板核心渲染组件
- `CanvasNode.svelte`：文本节点组件

Story 1.5 已实现白板数据同步到后端 Neo4j：
- `sync-engine.ts`：SyncEngine 消费 `sync_outbox` 队列，delta sync 到后端
- `sync_service.py`：后端 Neo4j 幂等写入服务
- `sync.py`：后端 Sync API 端点

本 Story 新增 ImageNode 组件和 IndexingService，复用 Story 1.4 的 IndexedDB 基础和 Story 1.5 的 sync 管道。

### 图片双层处理架构（来自 Architecture）

```
图片粘贴到白板
├── 对话层（即时可用，不依赖索引）
│   └── Agent 原生多模态能力直接将 base64 图片传入 Agent prompt
│   └── 用户粘贴后立即可以点击图片节点对话讨论
│
└── 检索层（异步索引，后台处理）
    └── Vision API 执行 OCR 提取文字/公式/概念
    └── 提取结果写入 IndexedDB，delta sync 到 Neo4j
    └── 后续 Story 2.9：提取结果进入 LanceDB bge-m3 向量索引
    └── 索引完成后图片内容可被 RAG 检索到
```

**核心原则**：对话能力（多模态直传）与检索能力（OCR 索引）完全解耦。索引是增值功能，不是前置条件。

### 数据流

```
用户粘贴图片
  -> CanvasView.handlePaste()
  -> FileReader.readAsDataURL(blob)
  -> canvasState.addNode({ type: 'image', imageData, indexStatus: 'indexing' })
  -> IndexedDB 写入 + sync_outbox 写入（Story 1.4/1.5 管道）
  -> indexingService.requestImageIndex(nodeId, imageData)
  -> apiClient.indexImage() -> POST /api/v1/index/image
  -> 后端 Vision API（LiteLLM）提取
  -> 返回 { ocrText, summary, concepts }
  -> canvasState.updateNode(nodeId, { ocrText, ocrSummary, ocrConcepts, indexStatus: 'indexed' })
  -> IndexedDB 更新 + sync_outbox 写入
  -> SyncEngine delta sync -> Neo4j 节点更新（含 OCR 数据）
  -> UI：Dexie liveQuery -> ImageNode 状态条更新
```

### imageData 存储策略

- **IndexedDB**：存储完整 base64 DataURL（前端渲染 + 对话层多模态传入需要）
- **Neo4j**：不存储 imageData（base64 太大，且 Neo4j 不是文件存储）
- **LanceDB**：仅存储 OCR 提取的文本（Story 2.9 实现）
- **图片大小限制**：> 10MB 提示用户压缩；IndexedDB 单条记录无硬性上限但建议 < 5MB

### 命名规范速查（本 Story 涉及）

- 前端组件文件：`PascalCase.svelte`（`ImageNode.svelte`）
- 前端 Service 文件：`kebab-case.ts`（`indexing-service.ts`）
- 后端 API 文件：`snake_case.py`（`index_image.py`）
- CSS 类名：`cl-canvas-node--image`、`cl-image-node-*`（E 组白板）
- API 端点路径：`/api/v1/index/image`（RESTful）

### 不做的事项（防蔓延 DD-10）

- 不实现 LanceDB 向量索引（Story 2.9 图片检索管道负责）
- 不实现对话层的图片多模态传入（Story 3.1 Claude Code CLI 集成负责）
- 不实现图片编辑/裁剪功能
- 不实现图片压缩/格式转换（仅提示用户）
- 不实现批量 OCR 队列管理（单个异步请求足够 MVP）
- 不实现 OCR 结果的编辑/修正功能
- 不修改 Story 1.4 的 CanvasNode 组件（ImageNode 是独立新组件）
- 不修改 `canvas-state.svelte.ts` 的 CRUD 方法签名（复用已有 addNode/updateNode）

### 共享文件编辑规则

| 文件 | 规则 |
|------|------|
| `dexie-db.ts` | 追加 Schema version 2（图片字段 + indexStatus 索引）；保持 version 1 不变 |
| `types/canvas.d.ts` | 扩展 `CanvasNodeData` 接口追加图片相关字段；保持已有字段 |
| `api-client.ts` | 追加 `indexImage()` 方法；保持 Story 1.1/1.5 的方法 |
| `types/api.d.ts` | 追加 Image 相关类型定义；保持已有类型 |
| `CanvasView.svelte` | 追加 paste/drop 事件处理 + ImageNode 条件渲染；保持 Story 1.4 的核心逻辑 |
| `main.ts` | 追加 indexingService 初始化和清理；保持 Story 1.1/1.4/1.5 的逻辑 |
| `sync_service.py` | 扩展图片节点同步逻辑（OCR 字段写入 Neo4j）；保持 Story 1.5 的通用同步逻辑 |
| `main.py`（后端） | 注册 index_image router；保持已有 router |

### Project Structure Notes

本 Story 新增/修改的文件清单：

```
obsidian-canvas-learning/
├── main.ts                                    # [修改] 追加 indexingService 初始化/清理
├── src/
│   ├── components/
│   │   └── canvas/
│   │       ├── CanvasView.svelte              # [修改] 追加 paste/drop 处理 + ImageNode 渲染
│   │       └── ImageNode.svelte               # [新建] 图片节点组件
│   ├── services/
│   │   ├── dexie-db.ts                        # [修改] 追加 Schema v2（图片字段）
│   │   ├── api-client.ts                      # [修改] 追加 indexImage 方法
│   │   └── indexing-service.ts                # [新建] 异步索引管理服务
│   └── types/
│       ├── canvas.d.ts                        # [修改] 扩展 CanvasNodeData 图片字段
│       └── api.d.ts                           # [修改] 追加 Image 索引类型

backend/
├── app/
│   ├── api/v1/
│   │   └── index_image.py                     # [新建] 图片索引 API 端点
│   ├── services/
│   │   └── sync_service.py                    # [修改] 扩展图片节点 Neo4j 写入
│   └── main.py                                # [修改] 注册 index_image router
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.6] — AC 和 Story 需求：图片粘贴生成节点、Vision API 异步 OCR、索引状态指示、对话不受索引影响、OCR < 10s
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements Overview] — 图片双层处理（对话层 Mode D 原生多模态即时对话/检索层 LanceDB 异步 bge-m3 索引+状态指示）
- [Source: _bmad-output/planning-artifacts/architecture.md#Technical Constraints & Dependencies] — NFR-PERF-05 图片 OCR < 10s（异步不阻塞）
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture] — LanceDB 笔记 chunk 语义检索、IndexedDB local-first 存储
- [Source: _bmad-output/planning-artifacts/architecture.md#Naming Patterns] — 前端/后端/CSS 命名规范
- [Source: _bmad-output/planning-artifacts/architecture.md#Integration Points] — 白板操作流：canvasState -> Dexie -> Outbox -> sync-engine -> Neo4j
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Pencil UI 范式 #10] — 图片节点+异步索引 Pencil 场景，FR-KG-06/07
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#旅程 5 图片密集型学习] — 截图->粘贴->立即对话->后台索引->后续检索引用
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy] — E 组白板组件包含 ImageNode
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Implementation Roadmap] — ImageNode 在 Phase 3 实施路线图（可提前到 Epic 1 因为是 FR-KG-06/07 核心功能）
- [Source: _bmad-output/planning-artifacts/epics.md#NFR] — NFR-PERF-05 图片 OCR < 10s（异步不阻塞）
- [Source: _bmad-output/planning-artifacts/epics.md#FR-KG-06] — 用户粘贴图片到白板时，对话层通过 Agent 原生多模态能力立即可对话讨论图片；检索层后台异步提取文字/公式/概念进入搜索索引
- [Source: _bmad-output/planning-artifacts/epics.md#FR-KG-07] — 搜索索引建立过程中显示状态指示（建立中->已完成），对话功能不受索引状态影响
- [Source: _bmad-output/planning-artifacts/epics.md#FR-IDX-06] — 图片 Gemini OCR -> 文本管道索引
- [Source: _bmad-output/implementation-artifacts/1-4-canvas-core-crud-mini-dashboard.md] — Story 1.4 IndexedDB Schema v1 + CanvasNodeData type 字段 + CanvasView 组件
- [Source: _bmad-output/implementation-artifacts/1-5-canvas-data-sync-backend-kg.md] — Story 1.5 SyncEngine + sync_service.py + sync API

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
