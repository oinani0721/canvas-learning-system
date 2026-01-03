# Epic 29: 视频教材挂载功能 - Brownfield Enhancement

**Epic ID**: EPIC-29
**Epic类型**: 功能增强 (Brownfield Enhancement)
**状态**: Not Started
**优先级**: P1 High
**创建日期**: 2025-12-26
**来源调研**: 视频挂载功能可行性调研
**依赖**: Epic 28 (双向链接功能)

---

## 目录

1. [Epic概述](#epic概述)
2. [现有系统背景](#现有系统背景)
3. [技术可行性](#技术可行性)
4. [Epic目标](#epic目标)
5. [Story概览](#story概览)
6. [技术方案](#技术方案)
7. [验收标准](#验收标准)
8. [兼容性要求](#兼容性要求)
9. [风险与缓解](#风险与缓解)
10. [Definition of Done](#definition-of-done)

---

## Epic概述

### 简述

**实现视频教材挂载功能**，用户可以挂载视频文件作为教材，系统使用Gemini处理视频内容，并在Agent回答中生成可点击的时间戳链接，跳转到视频的特定位置。

### 问题陈述

**用户期望**:
```markdown
# Agent回答
高斯定理表明通过闭合曲面的电通量等于曲面内电荷的代数和除以ε₀。

**视频参考**:
- [[课程/物理.mp4#t=150]] (02:30) - 高斯定理定义
```
点击链接 → 视频跳转到02:30播放

**当前状态**:
- 无视频教材支持
- 视频内容无法被RAG检索
- 无法生成视频时间戳链接

### 核心价值

**用户体验**:
- 支持视频作为教材来源
- 通过时间戳链接快速定位视频内容
- AI自动提取视频知识点

**学习效率提升**:
- 无需手动记录视频时间戳
- 问答时自动关联视频片段
- 视频-文本知识融合

---

## 现有系统背景

### 技术栈

**后端服务**:
- Python 3.9+ / FastAPI
- Gemini API (已集成)
- LanceDB向量存储 (已集成)

**RAG系统**:
- `src/agentic_rag/` - LangGraph RAG系统
- 五源融合检索 (Graphiti, LanceDB, Textbook, CrossCanvas, Multimodal)

**多模态处理**:
- `backend/app/services/gemini_client.py` - Gemini客户端
- `src/agentic_rag/processors/` - 多模态处理器

### 集成点

**复用组件**:
| 组件 | 复用程度 | 说明 |
|------|---------|------|
| GeminiClient | 100% | 复用现有API调用封装 |
| LanceDB存储 | 100% | 复用向量存储 |
| Agent模板 | 80% | 复用Epic 25的引用格式规范 |
| 前端TextbookMount | 60% | 扩展支持视频格式 |

**新增组件**:
| 组件 | 位置 | 说明 |
|------|------|------|
| VideoProcessor | `backend/app/services/video_processor.py` | 视频处理核心 |
| VideoVectorizer | `backend/app/services/video_vectorizer.py` | 视频分块向量化 |
| VideoRetriever | `src/agentic_rag/retrievers/video_retriever.py` | RAG第六源 |

---

## 技术可行性

### 已验证能力

| 组件 | 可行性 | 成熟度 | 来源 |
|------|--------|--------|------|
| **Gemini视频处理** | ✅ 完全可行 | 生产就绪 | [Google AI Docs](https://ai.google.dev/gemini-api/docs/video-understanding) |
| **时间戳提取** | ✅ 完全可行 | 生产就绪 | Gemini 1FPS + 每秒时间戳 |
| **Obsidian视频跳转** | ✅ 完全可行 | 成熟插件 | [Media Extended](https://github.com/aidenlx/media-extended) |
| **RAG视频集成** | ✅ 可行 | 需开发 | [Neo4j Video RAG](https://neo4j.com/blog/developer/youtube-transcripts-knowledge-graphs-rag/) |

### Gemini视频能力

| 能力 | 规格 | 说明 |
|------|------|------|
| 视频上传 | File API | 支持MP4等格式 |
| 视频时长 | 最长2小时 | 2M tokens上下文 |
| 帧采样 | 1 FPS | 可自定义 |
| 时间戳格式 | MM:SS / H:MM:SS | 自动添加 |
| 音频处理 | 1Kbps | 单声道 |

### Obsidian视频支持

**Media Extended插件**:
- 本地MP4播放: ✅
- 时间戳链接跳转: ✅
- 语法: `[[video.mp4#t=秒数]]`

---

## Epic目标

### 主要目标

**目标1: 视频处理服务**
- 实现VideoProcessor服务
- 调用Gemini File API处理视频
- 生成带时间戳的转录内容

**目标2: 视频向量化**
- 实现VideoVectorizer服务
- 按时间分块(每2分钟)
- 保留时间戳元数据存储到LanceDB

**目标3: 视频RAG检索**
- 实现VideoRetriever检索节点
- 作为RAG第六源加入融合
- 返回内容+时间戳链接

**目标4: Agent时间戳输出**
- 扩展Agent引用格式
- 生成`[[video.mp4#t=秒数]]`链接
- 与Epic 25引用规范统一

### 非目标 (Out of Scope)

- 视频在线播放器 (依赖Obsidian Media Extended)
- 视频剪辑/编辑功能
- 实时视频流处理
- 字幕文件(SRT/VTT)导入

### 成功标准

| 标准 | 描述 |
|------|------|
| **SC1** | 可挂载MP4视频文件作为教材 |
| **SC2** | Gemini成功转录视频并提取时间戳 |
| **SC3** | Agent回答包含`[[video#t=秒数]]`链接 |
| **SC4** | Obsidian中点击链接跳转到视频位置 |
| **SC5** | 无回归：现有教材功能不受影响 |

---

## Story概览

本Epic包含 **6个Story**，可在约4天内完成：

| Story ID | 标题 | 依赖 | 工作量 | 优先级 |
|----------|------|------|--------|--------|
| **29.1** | VideoProcessor服务开发 | 无 | 1天 | P0 |
| **29.2** | VideoVectorizer向量化 | 29.1 | 0.5天 | P0 |
| **29.3** | VideoRetriever检索节点 | 29.2 | 0.5天 | P0 |
| **29.4** | Agent时间戳链接输出 | 29.3, Epic 28 | 0.5天 | P0 |
| **29.5** | 前端视频挂载UI | 29.1 | 1天 | P1 |
| **29.6** | 集成测试与文档 | 29.1-5 | 0.5天 | P0 |

**依赖关系**:
```
Epic 28 (双向链接)
       │
       ▼
┌─────────────┐
│   29.1      │
│ VideoProc   │
└──────┬──────┘
       │
       ▼
┌─────────────┐   ┌─────────────┐
│   29.2      │   │   29.5      │
│ Vectorizer  │   │ 前端UI      │
└──────┬──────┘   └─────────────┘
       │
       ▼
┌─────────────┐
│   29.3      │
│ Retriever   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   29.4      │
│ Agent输出   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   29.6      │
│ 集成测试    │
└─────────────┘
```

---

### Story 29.1: VideoProcessor服务开发 [P0]

**目标**: 实现视频处理核心服务，调用Gemini API处理视频

**新建文件**:
- `backend/app/services/video_processor.py`

**实现方案**:
```python
from google import genai
from dataclasses import dataclass
from typing import List, Optional
import asyncio

@dataclass
class VideoChunk:
    """视频分块数据结构"""
    content: str           # 转录文本
    start_time: float      # 开始秒数
    end_time: float        # 结束秒数
    video_path: str        # 视频文件路径
    timestamp_link: str    # "[[video.mp4#t=150]]"

@dataclass
class VideoProcessResult:
    """视频处理结果"""
    video_path: str
    chunks: List[VideoChunk]
    total_duration: float
    processing_time_ms: float

class VideoProcessor:
    """视频处理服务 - 调用Gemini API处理视频"""

    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
        self.chunk_duration = 120  # 每2分钟一块

    async def process_video(self, video_path: str) -> VideoProcessResult:
        """
        处理视频文件，返回带时间戳的分块

        1. 上传视频到Gemini File API
        2. 请求Gemini生成带时间戳的转录
        3. 按时间分块并生成链接
        """
        # 上传视频
        uploaded_file = await self._upload_video(video_path)

        # 生成转录
        transcript = await self._generate_transcript(uploaded_file)

        # 分块处理
        chunks = self._create_chunks(transcript, video_path)

        return VideoProcessResult(
            video_path=video_path,
            chunks=chunks,
            total_duration=self._get_duration(transcript),
            processing_time_ms=...
        )

    async def _upload_video(self, video_path: str):
        """上传视频到Gemini File API"""
        client = genai.Client()
        return client.files.upload(file=video_path)

    async def _generate_transcript(self, uploaded_file) -> str:
        """生成带时间戳的转录"""
        response = await self.gemini_client.generate_content(
            model="gemini-2.0-flash",
            contents=[
                uploaded_file,
                """请为这个视频生成详细的转录，格式要求：
                1. 每段内容标注时间戳 [MM:SS]
                2. 识别知识点和概念
                3. 保持语义连贯性

                输出格式示例:
                [00:00] 本节课我们来学习高斯定理...
                [02:30] 首先，高斯定理的定义是...
                [05:15] 让我们看一个应用示例...
                """
            ]
        )
        return response.text

    def _create_chunks(self, transcript: str, video_path: str) -> List[VideoChunk]:
        """将转录按时间分块"""
        chunks = []
        # 解析时间戳并分块
        # ... 实现细节 ...
        return chunks
```

**验收标准**:
- [ ] 成功上传视频到Gemini File API
- [ ] 获取带时间戳的转录内容
- [ ] 按2分钟分块处理
- [ ] 单元测试覆盖核心逻辑
- [ ] 错误处理和超时机制

**预计工作量**: 1天

---

### Story 29.2: VideoVectorizer向量化 [P0]

**目标**: 将视频分块向量化并存储到LanceDB

**依赖**: Story 29.1

**新建文件**:
- `backend/app/services/video_vectorizer.py`

**实现方案**:
```python
from typing import List
from .video_processor import VideoChunk

class VideoVectorizer:
    """视频分块向量化服务"""

    def __init__(self, embedder, lancedb_client):
        self.embedder = embedder
        self.lancedb = lancedb_client
        self.table_name = "video_chunks"

    async def vectorize_and_store(self, chunks: List[VideoChunk]) -> int:
        """
        向量化视频分块并存储

        Returns: 存储的块数量
        """
        records = []
        for chunk in chunks:
            # 生成向量
            vector = await self.embedder.embed(chunk.content)

            record = {
                "id": self._generate_id(chunk),
                "content": chunk.content,
                "vector": vector,
                "video_path": chunk.video_path,
                "start_time": chunk.start_time,
                "end_time": chunk.end_time,
                "timestamp_link": chunk.timestamp_link,
                "source_type": "video"
            }
            records.append(record)

        # 批量写入LanceDB
        await self.lancedb.add(self.table_name, records)
        return len(records)
```

**验收标准**:
- [ ] 视频块成功向量化
- [ ] 元数据(时间戳、路径)正确存储
- [ ] LanceDB表结构正确
- [ ] 支持增量添加

**预计工作量**: 0.5天

---

### Story 29.3: VideoRetriever检索节点 [P0]

**目标**: 实现视频检索RAG节点，作为第六源加入融合

**依赖**: Story 29.2

**新建文件**:
- `src/agentic_rag/retrievers/video_retriever.py`

**修改文件**:
- `src/agentic_rag/nodes.py` (添加第六源)
- `src/agentic_rag/graph.py` (添加节点)

**实现方案**:
```python
from typing import List
from ..state import RAGState

class VideoRetriever:
    """视频检索节点 - RAG第六源"""

    def __init__(self, lancedb_client, embedder):
        self.lancedb = lancedb_client
        self.embedder = embedder
        self.table_name = "video_chunks"
        self.weight = 0.15  # 权重与Multimodal相同

    async def retrieve(self, query: str, top_k: int = 3) -> List[dict]:
        """检索匹配的视频片段"""
        # 生成查询向量
        query_vector = await self.embedder.embed(query)

        # LanceDB向量搜索
        results = await self.lancedb.search(
            self.table_name,
            query_vector,
            limit=top_k
        )

        # 格式化结果
        return [
            {
                "content": r["content"],
                "video_path": r["video_path"],
                "start_time": r["start_time"],
                "timestamp_link": r["timestamp_link"],
                "source": "video",
                "score": r["_distance"]
            }
            for r in results
        ]

async def video_retrieval_node(state: RAGState, runtime) -> RAGState:
    """LangGraph视频检索节点"""
    retriever = VideoRetriever(runtime.lancedb, runtime.embedder)

    results = await retriever.retrieve(
        state.query,
        top_k=3
    )

    # 合并到state
    state.video_contexts = results
    return state
```

**RAG六源融合权重**:
```python
DEFAULT_SOURCE_WEIGHTS = {
    "graphiti": 0.25,      # 知识图谱
    "lancedb": 0.20,       # 向量检索 (调整)
    "textbook": 0.20,      # 教材上下文
    "cross_canvas": 0.10,  # 跨Canvas (调整)
    "multimodal": 0.10,    # 多模态 (调整)
    "video": 0.15          # 视频 (新增)
}
```

**验收标准**:
- [ ] 视频检索节点正常工作
- [ ] 返回内容包含时间戳链接
- [ ] 六源融合权重配置正确
- [ ] 超时和错误处理完善

**预计工作量**: 0.5天

---

### Story 29.4: Agent时间戳链接输出 [P0]

**目标**: 扩展Agent引用格式，支持视频时间戳链接

**依赖**: Story 29.3, Epic 28

**修改文件**:
- `backend/app/services/context_enrichment_service.py`
- `.claude/agents/*.md` (9个Agent模板)

**实现方案**:

**1. 格式化视频上下文**:
```python
def _format_video_context(self, video_contexts: List[dict]) -> str:
    """格式化视频上下文，包含时间戳链接"""
    if not video_contexts:
        return ""

    sections = []
    for ctx in video_contexts:
        # 格式化时间显示
        minutes = int(ctx["start_time"] // 60)
        seconds = int(ctx["start_time"] % 60)
        time_display = f"{minutes:02d}:{seconds:02d}"

        section = f"""
### 视频参考: {time_display}
- **来源文件**: {ctx["timestamp_link"]}
- **时间位置**: {time_display}
- **内容预览**: {ctx["content"][:200]}...

> 引用此内容时，请使用链接: {ctx["timestamp_link"]}
"""
        sections.append(section)

    return "--- 相关视频参考 (Video References) ---\n" + "\n".join(sections)
```

**2. Agent模板添加视频引用规范** (追加到现有引用规范):
```markdown
### 视频教材
> [引用的内容]
> — 来源: [[视频文件.mp4#t=秒数]] (MM:SS)

### 示例
> 高斯定理表明通过闭合曲面的电通量等于曲面内电荷的代数和除以ε₀。
> — 来源: [[课程/物理.mp4#t=150]] (02:30)
```

**验收标准**:
- [ ] 视频上下文正确格式化
- [ ] Agent生成视频时间戳链接
- [ ] 时间格式统一(MM:SS)
- [ ] 与Epic 25引用格式兼容

**预计工作量**: 0.5天

---

### Story 29.5: 前端视频挂载UI [P1]

**目标**: 扩展教材挂载UI支持视频文件

**依赖**: Story 29.1

**修改文件**:
- `canvas-progress-tracker/obsidian-plugin/src/services/TextbookMountService.ts`
- `canvas-progress-tracker/obsidian-plugin/src/components/TextbookMountModal.ts`

**实现方案**:

**1. 支持视频格式**:
```typescript
// TextbookMountService.ts
private supportedFormats = {
    markdown: ['.md', '.markdown'],
    canvas: ['.canvas'],
    pdf: ['.pdf'],
    image: ['.png', '.jpg', '.jpeg', '.gif', '.svg'],
    video: ['.mp4', '.webm', '.mov']  // 新增
};

async mountTextbook(filePath: string): Promise<MountResult> {
    const ext = path.extname(filePath).toLowerCase();

    if (this.supportedFormats.video.includes(ext)) {
        return await this.mountVideo(filePath);
    }
    // ... 现有逻辑
}

private async mountVideo(filePath: string): Promise<MountResult> {
    // 调用后端视频处理API
    const response = await this.api.post('/api/v1/textbook/process-video', {
        video_path: filePath
    });

    return {
        type: 'video',
        path: filePath,
        chunks: response.chunks,
        status: 'success'
    };
}
```

**2. 挂载进度显示**:
```typescript
// 视频处理需要时间，显示进度
async mountVideoWithProgress(filePath: string): Promise<MountResult> {
    this.showNotice('正在处理视频，这可能需要几分钟...');

    try {
        const result = await this.mountVideo(filePath);
        this.showNotice(`视频处理完成: ${result.chunks.length}个片段`);
        return result;
    } catch (error) {
        this.showError('视频处理失败: ' + error.message);
        throw error;
    }
}
```

**验收标准**:
- [ ] 挂载对话框支持选择视频文件
- [ ] 显示视频处理进度
- [ ] 处理完成后显示片段数量
- [ ] 错误处理和用户提示

**预计工作量**: 1天

---

### Story 29.6: 集成测试与文档 [P0]

**目标**: 端到端测试和用户文档

**依赖**: Story 29.1-5

**测试用例**:

**1. 视频处理测试** (`test_video_processor.py`):
```python
async def test_process_video_success():
    """测试视频处理成功"""
    processor = VideoProcessor(mock_gemini_client)
    result = await processor.process_video("test_video.mp4")
    assert len(result.chunks) > 0
    assert all(c.start_time >= 0 for c in result.chunks)

async def test_video_chunk_has_timestamp_link():
    """测试分块包含时间戳链接"""
    processor = VideoProcessor(mock_gemini_client)
    result = await processor.process_video("test_video.mp4")
    for chunk in result.chunks:
        assert "[[" in chunk.timestamp_link
        assert "#t=" in chunk.timestamp_link
```

**2. 端到端测试**:
```python
async def test_e2e_video_to_agent_link():
    """端到端: 视频挂载到Agent生成链接"""
    # 1. 挂载视频
    mount_result = await mount_video("lecture.mp4")

    # 2. 查询
    response = await agent.query("什么是高斯定理?")

    # 3. 验证回答包含视频链接
    assert "[[lecture.mp4#t=" in response.content
```

**用户文档**:
- 视频挂载使用指南
- Media Extended插件安装说明
- 支持的视频格式列表

**验收标准**:
- [ ] 所有测试通过
- [ ] 覆盖率 >= 80%
- [ ] 用户文档完整
- [ ] 无回归

**预计工作量**: 0.5天

---

## 技术方案

### 数据流架构

```
┌─────────────────────────────────────────────────────────────┐
│                    视频教材挂载流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   用户挂载视频                                               │
│       ↓                                                      │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ VideoProcessor                                      │   │
│   │  - Gemini File API上传                              │   │
│   │  - 生成带时间戳转录                                  │   │
│   │  - 分块 (每2分钟)                                    │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓ VideoChunk[]                                        │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ VideoVectorizer                                     │   │
│   │  - 向量化转录文本                                    │   │
│   │  - 保留时间戳元数据                                  │   │
│   │  - 存储到LanceDB                                     │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓                                                      │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ LanceDB: video_chunks表                             │   │
│   │  - content, vector, video_path                      │   │
│   │  - start_time, end_time, timestamp_link             │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓ (用户提问时)                                        │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ VideoRetriever (RAG第六源)                          │   │
│   │  - 向量检索匹配片段                                  │   │
│   │  - 返回内容 + 时间戳链接                            │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓                                                      │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ ContextEnrichmentService                            │   │
│   │  - 格式化视频上下文                                  │   │
│   │  - 注入Agent Prompt                                 │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓                                                      │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ Agent回答                                           │   │
│   │  - 包含 [[video.mp4#t=秒数]] 链接                   │   │
│   │  - Obsidian中点击跳转                               │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 新建文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/app/services/video_processor.py` | 新建 | 视频处理核心服务 |
| `backend/app/services/video_vectorizer.py` | 新建 | 视频向量化服务 |
| `src/agentic_rag/retrievers/video_retriever.py` | 新建 | 视频检索节点 |
| `backend/tests/services/test_video_processor.py` | 新建 | 视频处理测试 |
| `backend/tests/integration/test_video_e2e.py` | 新建 | 端到端测试 |

### 修改文件清单

| 文件 | 修改内容 |
|------|---------|
| `src/agentic_rag/nodes.py` | 添加video_retrieval_node |
| `src/agentic_rag/graph.py` | 添加视频节点到图 |
| `backend/app/services/context_enrichment_service.py` | 添加_format_video_context |
| `.claude/agents/*.md` | 添加视频引用规范 |
| `canvas-progress-tracker/obsidian-plugin/src/services/TextbookMountService.ts` | 支持视频格式 |

---

## 验收标准

### Epic级验收标准

**AC1: 视频挂载**
- [ ] 支持挂载MP4视频文件
- [ ] 视频处理生成带时间戳的分块

**AC2: RAG集成**
- [ ] 视频内容可被RAG检索
- [ ] 六源融合正常工作

**AC3: 时间戳链接**
- [ ] Agent回答包含`[[video.mp4#t=秒数]]`链接
- [ ] 时间格式正确(MM:SS)

**AC4: Obsidian跳转**
- [ ] Media Extended插件可解析链接
- [ ] 点击跳转到视频正确位置

**AC5: 无回归**
- [ ] 现有教材功能不受影响
- [ ] 现有Agent功能正常

---

## 兼容性要求

### 必须保持兼容

**API兼容性**:
- 现有API端点不变
- 新增`/api/v1/textbook/process-video`端点

**RAG兼容性**:
- 现有五源检索不受影响
- 视频作为可选第六源

**前端兼容性**:
- 现有挂载功能不变
- 视频作为新增格式选项

### 外部依赖

**必须**:
- Gemini API Key (已有)
- LanceDB (已有)

**可选(用户安装)**:
- Obsidian Media Extended插件 (用于视频播放)

---

## 风险与缓解

### 中风险 (P2)

**风险1: 长视频处理耗时**
- **影响**: 用户等待时间长
- **可能性**: 高 (70%)
- **缓解策略**:
  - 后台异步处理
  - 显示处理进度
  - 缓存已处理视频

**风险2: Gemini API限额**
- **影响**: 处理失败
- **可能性**: 低 (20%)
- **缓解策略**:
  - 实现重试机制
  - 缓存处理结果
  - 分批处理长视频

### 低风险 (P3)

**风险3: 视频格式兼容性**
- **影响**: 某些视频无法处理
- **可能性**: 低 (20%)
- **缓解策略**:
  - 限制为MP4格式
  - 提供格式转换建议

### 回滚计划

**场景: 视频功能导致问题**
1. 禁用VideoRetriever节点(权重设为0)
2. 回滚前端视频格式支持
3. 保留已处理数据(不删除)
4. 分析问题并修复

---

## Definition of Done

### Epic级DoD

- [ ] 所有6个Story (29.1-29.6) 完成且验收标准达成
- [ ] 视频可成功挂载和处理
- [ ] RAG六源融合正常工作
- [ ] Agent生成视频时间戳链接
- [ ] Obsidian中链接可点击跳转
- [ ] 所有测试通过 (0回归)
- [ ] 新增测试覆盖率 >= 80%
- [ ] 用户文档完整
- [ ] 代码review通过

---

## 依赖关系

### 外部依赖

**上游依赖**:
- Epic 28 双向链接功能 (**必须先完成**)
- Gemini API (已集成)
- LanceDB (已集成)

**下游影响**:
- 所有9个Agent将支持视频引用
- RAG从五源扩展为六源

---

## 前置条件

**用户端**:
- 安装Obsidian Media Extended插件
- 视频文件为MP4格式
- 视频时长 <= 2小时

**系统端**:
- Gemini API Key配置
- 足够的存储空间(视频转录)

---

## 附录

### 参考来源

- [Google AI Video Understanding](https://ai.google.dev/gemini-api/docs/video-understanding)
- [Gemini Files API](https://ai.google.dev/gemini-api/docs/files)
- [Media Extended Plugin](https://github.com/aidenlx/media-extended)
- [Neo4j Video RAG](https://neo4j.com/blog/developer/youtube-transcripts-knowledge-graphs-rag/)
- [Vimeo Video RAG](https://medium.com/vimeo-engineering-blog/unlocking-knowledge-sharing-for-videos-with-rag-810ab496ae59)

---

## Epic签发

**创建日期**: 2025-12-26
**Epic状态**: Not Started
**优先级**: P1 High
**预计周期**: 4个工作日
**依赖Epic**: Epic 28 (双向链接)

---

**Epic 29 创建完成**
