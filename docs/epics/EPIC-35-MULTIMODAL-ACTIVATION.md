# Epic 35: 多模态功能完整激活 - Brownfield Enhancement

**Status**: Ready for Story Development
**Created**: 2026-01-17
**Priority**: P1 High
**Estimated Duration**: ~23天 (3 Sprints)

---

## Epic Goal

**激活Canvas Learning System中已完成95%的多模态后端引擎**，通过新建API端点和Obsidian插件集成，使用户能够在Canvas节点上附加、管理和检索图片、PDF、音频、视频等多模态内容。

---

## Epic Description

### Existing System Context

- **当前相关功能**:
  - 后端多模态处理器完整 (ImageProcessor, PDFProcessor, GeminiVision, MultimodalVectorizer)
  - 后端存储层完整 (MultimodalStore - LanceDB + Neo4j双数据库)
  - 前端UI组件完整 (ImagePreview, PDFPreview, MediaPanel, MediaPlayer)
  - RAG检索层完整 (MultimodalRetriever)

- **技术栈**:
  - 后端: FastAPI, LanceDB, Neo4j/Graphiti, Gemini 2.0 Flash
  - 前端: TypeScript, Obsidian Plugin API
  - 已有处理器: ~2000行代码可复用

- **集成点**:
  - `backend/app/main.py` - 路由注册
  - `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts` - API客户端
  - `src/agentic_rag/storage/multimodal_store.py` - 存储层接口

### Enhancement Details

- **What's being added/changed**:
  1. 新建后端多模态API端点 (上传、查询、管理)
  2. Obsidian插件ApiClient多模态方法集成
  3. MediaPanel组件连接后端数据源
  4. Canvas节点右键菜单"附加媒体"功能
  5. 音频/视频处理器补齐实现
  6. RAG检索自动包含多模态结果

- **How it integrates**:
  - API端点调用已有MultimodalStore
  - 插件通过HTTP调用后端API
  - 前端组件通过ApiClient获取数据

- **Success criteria**:
  - 用户可在Obsidian中右键Canvas节点附加图片/PDF
  - MediaPanel显示真实后端数据
  - RAG查询自动包含相关多模态内容
  - 音频/视频文件可上传和处理

---

## Stories

### Phase 1: P0 基础层 (Critical) - Sprint 1

#### Story 35.1: 多模态上传/管理API端点
- **优先级**: P0
- **工期**: 3-4天
- **描述**: 创建 `POST /api/v1/multimodal/upload` 等CRUD端点，集成已有MultimodalStore，支持异步处理(缩略图、OCR)
- **验收标准**:
  - AC 35.1.1: `POST /api/v1/multimodal/upload` 接受文件上传 (image/pdf/audio/video, max 50MB)
  - AC 35.1.2: `POST /api/v1/multimodal/upload-url` 接受URL内容
  - AC 35.1.3: `DELETE /api/v1/multimodal/{content_id}` 删除内容
  - AC 35.1.4: `PUT /api/v1/multimodal/{content_id}` 更新元数据
  - AC 35.1.5: `GET /api/v1/multimodal/{content_id}` 获取详情

#### Story 35.2: 多模态查询/搜索API端点
- **优先级**: P0
- **工期**: 2-3天
- **描述**: 创建查询端点，响应格式匹配前端MediaItem接口，支持向量相似度搜索
- **验收标准**:
  - AC 35.2.1: `GET /api/v1/multimodal/by-concept/{concept_id}` 按概念查询
  - AC 35.2.2: `POST /api/v1/multimodal/search` 向量搜索
  - AC 35.2.3: `GET /api/v1/multimodal/list` 分页列表
  - AC 35.2.4: 响应格式匹配前端 `MediaItem` 接口

#### Story 35.3: Obsidian插件ApiClient多模态集成
- **优先级**: P0
- **工期**: 2-3天
- **描述**: 添加多模态方法到ApiClient，使用FormData处理文件上传
- **验收标准**:
  - AC 35.3.1: `uploadMultimodal(file, conceptId)` 方法
  - AC 35.3.2: `getMediaByConceptId(conceptId)` 方法
  - AC 35.3.3: `searchMultimodal(query)` 方法
  - AC 35.3.4: `deleteMultimodal(contentId)` 方法
  - AC 35.3.5: 遵循现有重试/超时模式

#### Story 35.9: 端到端验证测试
- **优先级**: P0
- **工期**: 2-3天
- **描述**: 创建E2E测试验证完整流程
- **验收标准**:
  - AC 35.9.1: 上传图片 -> 验证LanceDB + Neo4j存储
  - AC 35.9.2: 关联Canvas节点 -> 验证HAS_MEDIA关系
  - AC 35.9.3: 向量搜索 -> 验证相关度排序
  - AC 35.9.4: 删除内容 -> 验证双数据库清理
  - AC 35.9.5: 性能: 10张图片 < 5秒

---

### Phase 2: P1 用户功能层 (High) - Sprint 2

#### Story 35.4: MediaPanel后端集成
- **优先级**: P1
- **工期**: 2-3天
- **描述**: 修改MediaPanel从ApiClient获取真实数据
- **验收标准**:
  - AC 35.4.1: MediaPanel从后端获取数据
  - AC 35.4.2: 支持概念切换刷新
  - AC 35.4.3: 加载状态UI
  - AC 35.4.4: 错误状态UI
  - AC 35.4.5: 刷新功能

#### Story 35.5: Canvas节点"附加媒体"右键菜单
- **优先级**: P1
- **工期**: 2-3天
- **描述**: 扩展ContextMenuManager，创建AttachMediaModal对话框
- **验收标准**:
  - AC 35.5.1: 右键菜单显示"附加媒体文件"
  - AC 35.5.2: 打开文件选择器对话框
  - AC 35.5.3: 上传文件到后端
  - AC 35.5.4: 成功通知含缩略图预览
  - AC 35.5.5: 节点元数据更新媒体引用计数

#### Story 35.6: 音频处理器实现
- **优先级**: P1
- **工期**: 2-3天
- **描述**: 创建AudioProcessor支持mp3/wav/ogg/m4a/flac
- **验收标准**:
  - AC 35.6.1: 提取音频元数据 (duration, sample_rate, channels)
  - AC 35.6.2: 支持mp3, wav, ogg, m4a, flac, aac格式
  - AC 35.6.3: 生成波形缩略图 (可选)
  - AC 35.6.4: Gemini转录集成 (feature flag)
  - AC 35.6.5: 返回MultimodalContent

#### Story 35.7: 视频处理器实现
- **优先级**: P1
- **工期**: 2-3天
- **描述**: 创建VideoProcessor支持mp4/webm/mkv/avi/mov
- **验收标准**:
  - AC 35.7.1: 提取视频元数据 (duration, resolution, fps)
  - AC 35.7.2: 支持mp4, webm, mkv, avi, mov格式
  - AC 35.7.3: 生成首帧缩略图
  - AC 35.7.4: Gemini视频理解集成 (feature flag)
  - AC 35.7.5: 返回MultimodalContent

---

### Phase 3: P2 增强层 (Medium) - Sprint 3

#### Story 35.8: RAG多模态搜索集成
- **优先级**: P2
- **工期**: 2天
- **描述**: 扩展RAG `/query` 响应包含多模态结果
- **验收标准**:
  - AC 35.8.1: `/query` 响应包含 `multimodal_results` 字段
  - AC 35.8.2: 并行调用 `MultimodalStore.search()`
  - AC 35.8.3: 结果包含缩略图URL
  - AC 35.8.4: RRF融合权重 0.3

---

## Dependency Graph

```
Story 35.1 (上传API) ──┬──> Story 35.3 (ApiClient) ──┬──> Story 35.4 (MediaPanel)
                       │                             │
Story 35.2 (搜索API) ──┘                             └──> Story 35.5 (右键菜单)
                                                              │
Story 35.6 (音频处理) ─────────────────────────────────────────┤
                                                              │
Story 35.7 (视频处理) ─────────────────────────────────────────┤
                                                              v
                                                     Story 35.8 (RAG集成)
                                                              │
                                                              v
                                                     Story 35.9 (E2E测试)
```

---

## Compatibility Requirements

- [x] 现有API保持不变 (新增端点，不修改现有)
- [x] 数据库Schema向后兼容 (复用已有multimodal表)
- [x] UI变更遵循现有模式 (右键菜单扩展)
- [x] 性能影响最小 (异步处理、缓存)

---

## Risk Mitigation

- **Primary Risk**: 大文件上传影响服务器性能
- **Mitigation**:
  - 文件大小限制 (图片50MB, 视频500MB)
  - 异步后台处理
  - 上传进度反馈

- **Rollback Plan**:
  - 新API端点独立于现有功能
  - 可通过移除路由注册快速回滚
  - 前端可切换为硬编码数据模式

---

## Definition of Done

- [ ] 所有9个Stories完成并通过验收标准
- [ ] 现有功能通过回归测试
- [ ] 集成点正常工作 (API<->插件<->存储)
- [ ] 文档更新 (API文档、用户指南)
- [ ] 无现有功能退化

---

## Technical Appendix

### New Files to Create

| Path | Purpose |
|------|---------|
| `backend/app/api/v1/endpoints/multimodal.py` | 多模态API路由 |
| `backend/app/services/multimodal_service.py` | 业务逻辑层 |
| `src/agentic_rag/processors/audio_processor.py` | 音频处理器 |
| `src/agentic_rag/processors/video_processor.py` | 视频处理器 |
| `canvas-progress-tracker/obsidian-plugin/src/modals/AttachMediaModal.ts` | 附加媒体对话框 |
| `backend/tests/e2e/test_multimodal_workflow.py` | E2E测试 |

### Files to Modify

| Path | Changes |
|------|---------|
| `backend/app/main.py` | 注册multimodal_router |
| `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts` | 添加多模态方法 |
| `canvas-progress-tracker/obsidian-plugin/src/api/types.ts` | 添加类型定义 |
| `canvas-progress-tracker/obsidian-plugin/src/components/MediaPanel.ts` | 连接后端 |
| `canvas-progress-tracker/obsidian-plugin/src/managers/ContextMenuManager.ts` | 添加菜单项 |
| `backend/app/api/v1/endpoints/rag.py` | 添加multimodal_results |

### Files to Reuse (Already Completed)

| Path | Function | Lines |
|------|----------|-------|
| `src/agentic_rag/processors/image_processor.py` | 图片处理 | 449 |
| `src/agentic_rag/processors/pdf_processor.py` | PDF处理 | 476 |
| `src/agentic_rag/processors/gemini_vision.py` | Vision AI | 473 |
| `src/agentic_rag/storage/multimodal_store.py` | 存储层 | 511 |
| `src/agentic_rag/retrievers/multimodal_retriever.py` | 检索层 | 200+ |
| `src/agentic_rag/models/multimodal_content.py` | 数据模型 | 286 |

### Dependencies to Add

| Package | Purpose | Install Command |
|---------|---------|-----------------|
| `python-multipart` | 文件上传 | `pip install python-multipart` |
| `pydub` | 音频处理 | `pip install pydub` |
| `moviepy` | 视频处理 | `pip install moviepy` |

---

## Estimated Effort

| Sprint | Stories | Duration |
|--------|---------|----------|
| Sprint 1 (P0) | 35.1, 35.2, 35.3, 35.9 | ~10天 |
| Sprint 2 (P1) | 35.4, 35.5, 35.6, 35.7 | ~10天 |
| Sprint 3 (P2) | 35.8 + 收尾 | ~3天 |
| **Total** | 9 Stories | **~23天** |

---

## API Design Reference

### Upload Endpoint
```python
# POST /api/v1/multimodal/upload
# Request: multipart/form-data
# - file: UploadFile
# - related_concept_id: str
# - canvas_path: Optional[str]

# Response
{
  "id": "uuid",
  "media_type": "image",
  "path": "/vault/images/xxx.png",
  "thumbnail": "base64...",
  "metadata": {...}
}
```

### Frontend Type Definition
```typescript
interface MediaItem {
  id: string;
  type: 'image' | 'pdf' | 'audio' | 'video';
  path: string;
  title?: string;
  relevanceScore: number;
  conceptId?: string;
  metadata?: Record<string, any>;
  thumbnail?: string;
}
```

---

## Story Manager Handoff

> "Please develop detailed user stories for this brownfield epic. Key considerations:
>
> - This is an enhancement to an existing system running **FastAPI + Obsidian Plugin + LanceDB + Neo4j**
> - Integration points: **MultimodalStore, ApiClient, ContextMenuManager, RAG endpoints**
> - Existing patterns to follow: **agents.py endpoint pattern, ApiClient method pattern**
> - Critical compatibility requirements: **API响应格式匹配前端MediaItem接口**
> - Each story must include verification that existing functionality remains intact
>
> The epic should maintain system integrity while delivering **多模态功能的完整用户端到端体验**."

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-17 | 1.0 | Initial Epic creation |
