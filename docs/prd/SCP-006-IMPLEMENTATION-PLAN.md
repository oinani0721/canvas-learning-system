# SCP-006 实施计划：多模态文件关联

**版本**: 1.0
**创建日期**: 2025-11-30
**状态**: 📋 待审批
**关联文档**: SCP-006-MULTIMODAL-ASSOCIATION.md

---

## 1. 执行摘要

### 1.1 决策背景

| 方案 | 技术 | 优势 | 劣势 |
|------|------|------|------|
| Story 12.17 | ImageBind (Meta) | 6模态统一向量空间、本地推理 | 需要CUDA/GPU、2GB模型下载 |
| **SCP-006** ✅ | Gemini 2.0 Flash | 云API无GPU需求、中文优秀、低成本 | 依赖网络 |

**决策**: 采用 SCP-006 方案，放弃 Story 12.17

**理由**:
1. 用户环境不保证有NVIDIA GPU
2. Gemini 2.0 Flash 已在 ADR-001 中选定为主力模型
3. 月度成本仅 ~$0.04，可忽略
4. 中文支持更好，符合项目主要用户群

### 1.2 目标

将多模态内容（图片、PDF、音频、视频）集成到 Canvas Learning System，使用户可以：
- 在概念节点上关联多媒体学习材料
- 自动提取多模态内容的语义信息
- 通过 Agentic RAG 检索多模态相关知识

---

## 2. 依赖分析

### 2.1 前置依赖

| Epic/Story | 状态 | 说明 |
|------------|------|------|
| Epic 12 (Agentic RAG) | ✅ 已完成 | 提供LanceDB、LangGraph、Graphiti基础设施 |
| Story 12.2 (LanceDB POC) | ✅ 已完成 | LanceDB支持多模态向量存储 |
| Story 12.5 (LangGraph StateGraph) | ✅ 已完成 | 多模态检索可复用StateGraph |
| ADR-001 (Gemini选型) | ✅ 已定 | 确认使用Gemini 2.0 Flash |

### 2.2 技术栈确认

```yaml
多模态处理:
  AI模型: Gemini 2.0 Flash (google-generativeai)
  图片处理: Pillow + base64编码
  PDF处理: PyMuPDF (fitz) 或 pdfplumber
  音频转写: Gemini 2.0 Flash (原生支持音频)
  视频处理: Gemini 2.0 Flash + ffmpeg提取帧

向量存储:
  LanceDB:
    multimodal: true  # 关键配置
    embedding_model: Gemini Embedding

知识图谱:
  Graphiti/Neo4j:
    新增节点类型: ImageNode, PDFNode, AudioNode, VideoNode
    新增关系类型: HAS_MEDIA, ILLUSTRATES, REFERENCES
```

---

## 3. 分阶段实施计划

### Phase 1: 基础多模态支持 (P1) - 7天

**目标**: 实现图片和PDF的基础存储、显示和提取

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1 架构                                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────┐     ┌────────────┐     ┌────────────┐      │
│  │ Image File │ ──► │ Processor  │ ──► │ LanceDB    │      │
│  │ (.png/jpg) │     │ (Gemini)   │     │ (vectors)  │      │
│  └────────────┘     └────────────┘     └────────────┘      │
│                                                             │
│  ┌────────────┐     ┌────────────┐     ┌────────────┐      │
│  │ PDF File   │ ──► │ Text       │ ──► │ Neo4j      │      │
│  │ (.pdf)     │     │ Extractor  │     │ (metadata) │      │
│  └────────────┘     └────────────┘     └────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Story 6.1: 图片节点类型支持 (2天)

**User Story**:
> As a Canvas学习用户, I want to 在概念节点上附加图片, so that 我可以关联公式截图、电路图等视觉材料

**验收标准**:
- [ ] AC 6.1.1: Canvas节点可附加PNG/JPG/GIF/SVG图片
- [ ] AC 6.1.2: 图片显示为缩略图（点击放大）
- [ ] AC 6.1.3: 图片元数据存储到Neo4j
- [ ] AC 6.1.4: 支持拖拽上传

**技术实现**:
```python
# src/agentic_rag/processors/image_processor.py
from PIL import Image
import base64
from pathlib import Path

class ImageProcessor:
    """图片处理器 - 提取、压缩、编码"""

    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.svg'}
    MAX_DIMENSION = 1024  # 最大边长

    async def process(self, image_path: Path) -> dict:
        """处理图片，返回元数据和base64编码"""
        # 验证格式
        if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {image_path.suffix}")

        # 读取和压缩
        img = Image.open(image_path)
        img.thumbnail((self.MAX_DIMENSION, self.MAX_DIMENSION))

        # Base64编码（用于Gemini API）
        buffered = BytesIO()
        img.save(buffered, format=img.format or 'PNG')
        b64_data = base64.b64encode(buffered.getvalue()).decode()

        return {
            "path": str(image_path),
            "format": img.format,
            "size": img.size,
            "base64": b64_data,
            "mime_type": f"image/{img.format.lower()}"
        }
```

**文件列表**:
- 创建: `src/agentic_rag/processors/image_processor.py`
- 创建: `src/agentic_rag/models/multimodal_node.py`
- 修改: `src/canvas_utils.py` (添加图片附加功能)
- 创建: `src/tests/test_image_processor.py`

---

#### Story 6.2: PDF节点类型支持 (2天)

**User Story**:
> As a Canvas学习用户, I want to 在概念节点上附加PDF文档, so that 我可以关联教材章节和论文

**验收标准**:
- [ ] AC 6.2.1: Canvas节点可附加PDF文件
- [ ] AC 6.2.2: 显示PDF首页缩略图
- [ ] AC 6.2.3: 支持指定页码范围
- [ ] AC 6.2.4: PDF元数据存储到Neo4j

**技术实现**:
```python
# src/agentic_rag/processors/pdf_processor.py
import fitz  # PyMuPDF
from pathlib import Path

class PDFProcessor:
    """PDF处理器 - 提取文本、生成缩略图"""

    async def process(self, pdf_path: Path, pages: list[int] = None) -> dict:
        """处理PDF，提取文本和元数据"""
        doc = fitz.open(pdf_path)

        # 提取指定页面或全部
        target_pages = pages or range(len(doc))

        extracted_text = []
        for page_num in target_pages:
            page = doc[page_num]
            extracted_text.append({
                "page": page_num + 1,
                "text": page.get_text(),
                "blocks": page.get_text("blocks")
            })

        # 生成首页缩略图
        first_page = doc[0]
        pix = first_page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
        thumbnail_b64 = base64.b64encode(pix.tobytes("png")).decode()

        return {
            "path": str(pdf_path),
            "title": doc.metadata.get("title", pdf_path.stem),
            "author": doc.metadata.get("author", "Unknown"),
            "page_count": len(doc),
            "extracted_pages": extracted_text,
            "thumbnail_base64": thumbnail_b64
        }
```

**文件列表**:
- 创建: `src/agentic_rag/processors/pdf_processor.py`
- 修改: `src/agentic_rag/models/multimodal_node.py`
- 创建: `src/tests/test_pdf_processor.py`

---

#### Story 6.3: 多模态内容存储架构 (3天)

**User Story**:
> As a 系统开发者, I want to 设计统一的多模态存储架构, so that 图片/PDF/音视频可以一致地存储和检索

**验收标准**:
- [ ] AC 6.3.1: LanceDB表支持multimodal=True
- [ ] AC 6.3.2: Neo4j Schema包含多模态节点类型
- [ ] AC 6.3.3: 统一的MultimodalContent接口
- [ ] AC 6.3.4: 文件存储路径规范化

**技术实现**:

```python
# src/agentic_rag/storage/multimodal_store.py
import lancedb
from dataclasses import dataclass
from enum import Enum

class MediaType(Enum):
    IMAGE = "image"
    PDF = "pdf"
    AUDIO = "audio"
    VIDEO = "video"

@dataclass
class MultimodalContent:
    """统一的多模态内容模型"""
    id: str
    media_type: MediaType
    file_path: str
    thumbnail_path: str | None
    extracted_text: str | None
    description: str | None  # AI生成的描述
    vector: list[float] | None  # 多模态向量
    related_concept_id: str  # 关联的Canvas概念节点
    created_at: datetime

class MultimodalStore:
    """多模态存储管理器"""

    def __init__(self, lancedb_uri: str, neo4j_driver):
        self.lance_db = lancedb.connect(lancedb_uri)
        self.neo4j = neo4j_driver

        # 创建或获取多模态表
        self.media_table = self._init_media_table()

    def _init_media_table(self):
        """初始化LanceDB多模态表"""
        schema = pa.schema([
            pa.field("id", pa.string()),
            pa.field("media_type", pa.string()),
            pa.field("file_path", pa.string()),
            pa.field("extracted_text", pa.string()),
            pa.field("description", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), 768)),
            pa.field("related_concept_id", pa.string()),
        ])

        if "multimodal_content" not in self.lance_db.table_names():
            return self.lance_db.create_table("multimodal_content", schema=schema)
        return self.lance_db.open_table("multimodal_content")

    async def store(self, content: MultimodalContent) -> str:
        """存储多模态内容到LanceDB和Neo4j"""
        # 1. 存储向量到LanceDB
        self.media_table.add([{
            "id": content.id,
            "media_type": content.media_type.value,
            "file_path": content.file_path,
            "extracted_text": content.extracted_text,
            "description": content.description,
            "vector": content.vector,
            "related_concept_id": content.related_concept_id,
        }])

        # 2. 存储关系到Neo4j
        query = """
        MATCH (c:Concept {id: $concept_id})
        CREATE (m:Media {
            id: $media_id,
            type: $media_type,
            path: $file_path
        })
        CREATE (c)-[:HAS_MEDIA]->(m)
        RETURN m.id
        """
        await self.neo4j.execute(query, {
            "concept_id": content.related_concept_id,
            "media_id": content.id,
            "media_type": content.media_type.value,
            "file_path": content.file_path
        })

        return content.id
```

**Neo4j Schema更新**:
```cypher
// 新增多模态节点类型
CREATE CONSTRAINT IF NOT EXISTS FOR (m:Media) REQUIRE m.id IS UNIQUE;

// 关系类型
// (Concept)-[:HAS_MEDIA]->(Media)
// (Media)-[:ILLUSTRATES]->(Concept)
// (Media)-[:REFERENCES]->(Media)
```

**文件列表**:
- 创建: `src/agentic_rag/storage/multimodal_store.py`
- 创建: `specs/data/multimodal-content.schema.json`
- 修改: `src/agentic_rag/clients/graphiti_client.py`
- 创建: `scripts/init_multimodal_schema.cypher`

---

### Phase 2: 智能分析 (P2) - 7天

**目标**: 使用Gemini 2.0 Flash进行智能内容提取和向量化

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 2 架构 - Gemini 2.0 Flash 集成                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────┐                                            │
│  │ Image      │────┐                                       │
│  └────────────┘    │                                       │
│                    ▼                                        │
│  ┌────────────┐  ┌─────────────────┐  ┌────────────┐      │
│  │ PDF Text   │──►│ Gemini 2.0     │──►│ Embedding  │      │
│  └────────────┘  │ Flash           │  │ (768-dim)  │      │
│                  │ (Vision + Text) │  └────────────┘      │
│  ┌────────────┐  └─────────────────┘                       │
│  │ Audio      │────┘                                       │
│  └────────────┘                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Story 6.4: 图片OCR与描述生成 (3天)

**User Story**:
> As a Canvas学习用户, I want to 自动提取图片中的文字和公式, so that 文本内容可以被检索

**验收标准**:
- [ ] AC 6.4.1: 图片中的文字自动提取（OCR）
- [ ] AC 6.4.2: AI生成图片内容描述（中文）
- [ ] AC 6.4.3: 数学公式识别为LaTeX格式
- [ ] AC 6.4.4: 处理时间<3秒/张

**技术实现**:
```python
# src/agentic_rag/processors/gemini_vision.py
import google.generativeai as genai
from PIL import Image
import base64

class GeminiVisionProcessor:
    """Gemini 2.0 Flash 视觉处理器"""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    async def analyze_image(self, image_b64: str, mime_type: str) -> dict:
        """分析图片，提取OCR和生成描述"""

        prompt = """请分析这张图片，完成以下任务：

1. **OCR文字提取**: 识别图片中的所有文字，包括：
   - 普通文本
   - 数学公式（输出为LaTeX格式，如 $E=mc^2$）
   - 代码片段（标注语言）

2. **内容描述**: 用中文描述图片内容，包括：
   - 图片类型（截图、手绘、图表等）
   - 主要内容
   - 关键概念

请以JSON格式输出：
{
  "ocr_text": "提取的文字...",
  "latex_formulas": ["$formula1$", "$formula2$"],
  "code_snippets": [{"language": "python", "code": "..."}],
  "description": "图片内容描述...",
  "key_concepts": ["概念1", "概念2"]
}"""

        response = await self.model.generate_content_async([
            {"mime_type": mime_type, "data": image_b64},
            prompt
        ])

        # 解析JSON响应
        import json
        result = json.loads(response.text)

        return result
```

**文件列表**:
- 创建: `src/agentic_rag/processors/gemini_vision.py`
- 创建: `src/tests/test_gemini_vision.py`
- 修改: `src/agentic_rag/processors/image_processor.py`

---

#### Story 6.5: PDF文本提取与结构化 (2天)

**User Story**:
> As a Canvas学习用户, I want to 自动提取PDF的结构化内容, so that 我可以按章节检索

**验收标准**:
- [ ] AC 6.5.1: 提取PDF目录结构
- [ ] AC 6.5.2: 按章节分块提取文本
- [ ] AC 6.5.3: 提取PDF中的图片
- [ ] AC 6.5.4: 处理时间<5秒/页

**技术实现**:
```python
# src/agentic_rag/processors/pdf_extractor.py
import fitz
from dataclasses import dataclass

@dataclass
class PDFChunk:
    """PDF文本块"""
    page_num: int
    heading: str | None
    content: str
    images: list[str]  # base64编码的图片

class PDFExtractor:
    """PDF结构化提取器"""

    async def extract_structured(self, pdf_path: str) -> list[PDFChunk]:
        """提取PDF结构化内容"""
        doc = fitz.open(pdf_path)
        chunks = []

        # 获取目录
        toc = doc.get_toc()

        for page_num, page in enumerate(doc):
            # 提取文本块
            blocks = page.get_text("dict")["blocks"]

            # 提取图片
            images = []
            for img in page.get_images():
                xref = img[0]
                base_image = doc.extract_image(xref)
                images.append(base64.b64encode(base_image["image"]).decode())

            # 识别标题
            heading = self._find_heading(blocks, toc, page_num)

            chunks.append(PDFChunk(
                page_num=page_num + 1,
                heading=heading,
                content=page.get_text(),
                images=images
            ))

        return chunks
```

---

#### Story 6.6: 多模态向量化存储 (2天)

**User Story**:
> As a 系统开发者, I want to 将多模态内容向量化存储到LanceDB, so that 可以进行语义检索

**验收标准**:
- [ ] AC 6.6.1: 图片内容向量化（768维）
- [ ] AC 6.6.2: PDF文本分块向量化
- [ ] AC 6.6.3: 向量与原始内容关联
- [ ] AC 6.6.4: 支持批量处理

**技术实现**:
```python
# src/agentic_rag/embeddings/multimodal_embedder.py
import google.generativeai as genai

class MultimodalEmbedder:
    """多模态内容向量化"""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('models/embedding-001')

    async def embed_text(self, text: str) -> list[float]:
        """文本向量化"""
        result = await genai.embed_content_async(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']

    async def embed_image_description(
        self,
        description: str,
        ocr_text: str,
        key_concepts: list[str]
    ) -> list[float]:
        """图片内容向量化（基于提取的文本和描述）"""
        combined_text = f"""
图片描述: {description}

提取文字: {ocr_text}

关键概念: {', '.join(key_concepts)}
"""
        return await self.embed_text(combined_text)
```

---

### Phase 3: 关联与检索 (P2) - 10天

**目标**: 实现多模态自动关联和Agentic RAG检索

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 3 架构 - 多模态 Agentic RAG                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Query: "傅里叶变换的可视化解释"                        │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────┐                                       │
│  │ Query Analyzer  │                                       │
│  └────────┬────────┘                                       │
│           │ "需要检索：文本 + 图片 + 视频"                   │
│           ▼                                                 │
│  ┌────────────────────────────────────────┐                │
│  │        Parallel Retrieval              │                │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │                │
│  │  │ Text    │ │ Image   │ │ Video   │  │                │
│  │  │ Search  │ │ Search  │ │ Search  │  │                │
│  │  └────┬────┘ └────┬────┘ └────┬────┘  │                │
│  └───────┼───────────┼───────────┼───────┘                │
│          └───────────┼───────────┘                         │
│                      ▼                                      │
│            ┌─────────────────┐                             │
│            │ Fusion & Rank   │                             │
│            └────────┬────────┘                             │
│                     ▼                                       │
│            ┌─────────────────┐                             │
│            │ Multimodal      │                             │
│            │ Response        │                             │
│            └─────────────────┘                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Story 6.7: 多模态自动关联算法 (3天)

**User Story**:
> As a Canvas学习用户, I want to 系统自动发现多模态内容间的关联, so that 我的知识图谱更加完整

**验收标准**:
- [ ] AC 6.7.1: 基于向量相似度自动关联
- [ ] AC 6.7.2: 基于共同概念自动关联
- [ ] AC 6.7.3: 关系存储到Graphiti
- [ ] AC 6.7.4: 关联建议可人工确认/拒绝

---

#### Story 6.8: 多模态Agentic RAG检索 (3天)

**User Story**:
> As a Canvas学习用户, I want to 通过自然语言检索多模态内容, so that 我可以快速找到相关的图片、视频

**验收标准**:
- [ ] AC 6.8.1: 支持"找一张关于XX的图片"查询
- [ ] AC 6.8.2: 检索结果包含文本+多媒体
- [ ] AC 6.8.3: 复用Epic 12的LangGraph StateGraph
- [ ] AC 6.8.4: 检索时间<2秒

**技术实现**:
```python
# src/agentic_rag/graph/multimodal_retrieval_node.py
from langgraph.graph import StateGraph
from langgraph.types import Send

async def multimodal_retrieval_node(state: AgenticRagState):
    """多模态并行检索节点"""
    query = state.query

    # 分析查询意图，决定检索哪些模态
    modalities = await analyze_query_modality(query)

    # 并行发送检索请求
    sends = []
    if "text" in modalities:
        sends.append(Send("text_retrieval", {"query": query}))
    if "image" in modalities:
        sends.append(Send("image_retrieval", {"query": query}))
    if "pdf" in modalities:
        sends.append(Send("pdf_retrieval", {"query": query}))
    if "video" in modalities:
        sends.append(Send("video_retrieval", {"query": query}))

    return sends
```

---

#### Story 6.9: UI集成（预览、播放器）(4天)

**User Story**:
> As a Canvas学习用户, I want to 在Obsidian中预览和播放多媒体内容, so that 我不需要切换应用

**验收标准**:
- [ ] AC 6.9.1: 图片弹窗预览（放大镜）
- [ ] AC 6.9.2: PDF内嵌预览器
- [ ] AC 6.9.3: 音频内嵌播放器
- [ ] AC 6.9.4: 视频内嵌播放器
- [ ] AC 6.9.5: 移动端适配

---

## 4. 时间线

```
┌───────────────────────────────────────────────────────────────────────┐
│ SCP-006 实施时间线                                                     │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Phase 1 (7天)           Phase 2 (7天)           Phase 3 (10天)       │
│  ├────────────────────┤├────────────────────┤├────────────────────────┤│
│  │ 6.1 图片支持 (2d)   ││ 6.4 OCR描述 (3d)   ││ 6.7 自动关联 (3d)      ││
│  │ 6.2 PDF支持 (2d)    ││ 6.5 PDF提取 (2d)   ││ 6.8 多模态RAG (3d)     ││
│  │ 6.3 存储架构 (3d)   ││ 6.6 向量化 (2d)    ││ 6.9 UI集成 (4d)        ││
│  ├────────────────────┤├────────────────────┤├────────────────────────┤│
│                                                                       │
│  总计: 24天 (约5周，考虑buffer为6周)                                   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 5. 成本预算

| 项目 | 月度估算 | 说明 |
|------|----------|------|
| Gemini 2.0 Flash Vision | $0.04 | 500张图片/月 |
| Gemini Embedding | $0.02 | 1000次/月 |
| LanceDB存储 | $0 | 本地存储 |
| Neo4j存储 | $0 | 本地实例 |
| **总计** | **~$0.06/月** | 可忽略 |

---

## 6. 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 大文件处理超时 | 中 | 中 | 异步处理+进度指示 |
| Gemini API限流 | 低 | 低 | 本地缓存+重试机制 |
| PDF格式兼容性 | 中 | 中 | 多解析库fallback |
| 网络依赖 | 中 | 中 | 离线模式降级 |

---

## 7. 审批清单

| 角色 | 状态 | 日期 | 签名 |
|------|------|------|------|
| PM Agent | ⏳ 待审批 | - | - |
| Architect Agent | ⏳ 待审批 | - | - |
| PO Agent | ⏳ 待审批 | - | - |
| Dev Lead | ⏳ 待审批 | - | - |

---

## 8. 下一步行动

1. **立即**: 提交此计划给PO审批
2. **审批后**:
   - 创建Story文件 (6.1-6.9)
   - 安装依赖: `pip install PyMuPDF google-generativeai pillow`
   - 配置Gemini API Key
3. **Phase 1开始前**:
   - 确认Epic 13 Obsidian Plugin基础框架完成
   - 准备测试数据（示例图片、PDF）

---

**文档结束**

**创建人**: SM Agent (Bob)
**创建日期**: 2025-11-30
**版本**: 1.0
