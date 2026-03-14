---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'A5 多模态检索增强 — 视觉嵌入架构升级 + 文档解析框架集成 + 多模态 reranking'
session_goals: '3大任务块完整方案设计、3-Phase 实施蓝图、Decision-Review 审查项'
selected_approach: 'AI-Recommended Techniques'
techniques_used: ['Deep Explore', 'Incremental Questioning', 'Community Validation', 'Adversarial Code Review']
ideas_generated: ['BGE-VL统一嵌入+ColQwen2.5-multilingual视觉检索双路架构', 'MinerU+MarkdownHeaderSplitter文档解析', '混合策略(本地检索+云端理解)', 'Visual RAG Toolkit向量压缩+2-stage检索', 'Jina Reranker M0多模态精排', '3-Phase渐进升级蓝图']
context_file: ''
session_active: false
workflow_completed: true
revision_date: '2026-03-12'
revision_reason: '验证 session deep explore 发现 Docling 中文不可用、ColPali 英文训练限制、BGE-VL CLIP 中文限制'
---

# Brainstorming Session Results — A5 多模态检索增强

**Facilitator:** ROG
**Date:** 2026-03-12
**Session ID:** session-brainstorm-A5-multimodal-2026-03-12

---

## Session Overview

**Topic:** A5 多模态检索增强 — 从"伪多模态"（图像→OCR文本→文本嵌入）升级为真正的视觉嵌入架构

**Goals:**
1. 视觉嵌入模型选型 — 引入原生图像理解能力，不再依赖纯文本代理
2. 文档解析框架升级 — 从简单 PyMuPDF 提取升级为结构化文档解析
3. 多模态 Reranking — 跨模态精排提升检索质量

**方法论:** Deep Explore（6 个并行 agent 两轮调研） + 增量提问模式 + 对抗性代码审查

**关联任务:** A5（独立，★☆☆难度，3 大任务块）

---

## 验证 Session 修正记录（2026-03-12）

> 独立验证 session 对 5 个 Decision-Review 进行了 deep explore 社区最佳实践调研（3 个并行 agent），发现 3 个影响原决策的关键风险，经用户确认后修正如下：

| DR | 修正程度 | 修正内容 | 调研依据 |
|----|---------|---------|---------|
| DR-A5-1 BGE-VL | 补充说明 | 显式声明 CLIP backbone 的中文视觉-文本理解限制，BGE-VL 定位为视觉结构匹配 | CLIP 训练数据以英文为主，无中文视觉检索 benchmark |
| DR-A5-2 ColPali | ⚠️ 中等修正 | ColSmol → **ColQwen2.5-7b-multilingual**；新增 **2-stage 检索**架构 | ColPali 训练 100% 英文；LanceDB MaxSim 线性扩展；社区多语言变体可用 |
| DR-A5-3 文档解析 | ⛔ 重大修正 | Docling → **MinerU**；HybridChunker → **MarkdownHeaderSplitter** | Docling 中文乱码（Issues #225,#748,#2737）；MinerU OmniDocBench CVPR 2025 中文超 GPT-4o |
| DR-A5-4 混合策略 | 无修正 | — | 本地检索+云端理解分工仍然有效 |
| DR-A5-5 3-Phase | 小修正 | P1 任务项更新（Docling→MinerU） | 随 DR-A5-3 修正联动 |

---

## 代码现状诊断 — 对抗性审查结果

> 由独立 agent 执行对抗性代码审查，评级标准：可直接复用 / 需修复后复用 / 需重写

### 多模态管道核心文件审查

| 文件 | 评级 | 关键问题 |
|------|------|---------|
| `processors/multimodal_vectorizer.py` | 需修复后复用 | 使用 `all-MiniLM-L6-v2`(384d)；`_concat_fusion` 实为 weighted_average 命名误导；非确定性 content ID；废弃的 `asyncio.get_event_loop()`；便捷函数每次创建新模型实例 |
| `retrievers/multimodal_retriever.py` | 需修复后复用 | `VectorizerProtocol.vectorize_text()` 返回类型不匹配（声明 `List[float]`，实际返回 `VectorizedContent`）；`LanceDBClientProtocol.similarity_search()` 不存在；空向量 `[]` fallback（line 803）；双重 `MediaType` 枚举 |
| `storage/multimodal_store.py` | **需完全重写** | 几乎所有方法调用不存在的 API：`graphiti_client.add_memory(key=..., content=..., metadata=...)` 实际应为 `add_memory(name=..., episode_body=...)`；`add_relationship()`、`search_facts()`、`delete_memory()`、`list_memories()` 全不存在；score/distance 逻辑反转；`update()` 创建重复 |
| `models/multimodal_content.py` | 需修复后复用 | 硬编码 768 维向量验证（line 167-170）；`to_lancedb_record` 存储零向量 `[0.0]*768` |
| `processors/gemini_vision.py` | **可直接复用**（minor fix） | 使用 `gemini-2.0-flash-exp`；提取 OCR/LaTeX/代码/描述/概念/分类；线性 backoff 标注错误；全局 `genai.configure()` 状态 |
| `processors/image_processor.py` | **可直接复用**（minor fix） | PNG/JPG/GIF/SVG 处理完整；SVG thumbnail 为完整文件；fake async |
| `processors/pdf_processor.py` | **可直接复用**（minor fix） | PyMuPDF 提取完整；fake async；PNG quality 参数被忽略 |
| `fusion/rrf_fusion.py` | 需修复后复用 | `k=60`；多源权重与 `nodes.py` 不一致（DEPRECATED）；变量 k 在 dict comprehension 中被 shadow |
| `clients/lancedb_client.py` | 需增强 | `DEFAULT_EMBEDDING_DIM=384`；固定字符切分（500 chars, 50 overlap）无公式感知；缺失 `search_multimodal()` 方法 |
| `backend/app/services/markdown_image_extractor.py` | 需修复后复用 | 无公式提取/保护；`[[Folder/Image.png]]` vault 路径未处理；路径解析优先级不符合 Obsidian 语义 |

### 5 个系统性断裂点

| # | 断裂点 | 根因 | 修复方案 |
|---|--------|------|---------|
| BP-1 | 向量维度不匹配 | vectorizer 输出 384d，content model 验证 768d，无处匹配 | 统一为 768d（text: `all-mpnet-base-v2`）或直接上 bge-m3 1024d；视觉路径 1024d 独立表 |
| BP-2 | Protocol/Interface 断裂 | `VectorizerProtocol` 和 `LanceDBClientProtocol` 定义的方法签名与实际实现不匹配 | 重新定义 Protocol，对齐实际 API |
| BP-3 | Graphiti API 签名全错 | `multimodal_store.py` 调用 6+ 个不存在的 Graphiti 方法 | 完全重写该文件，使用真实 Graphiti API |
| BP-4 | Fake async | 多个文件中 `async def` 内执行同步 I/O（文件读写、模型推理），阻塞事件循环 | 同步操作包裹 `run_in_executor()` |
| BP-5 | 双重 MediaType 枚举 | `multimodal_content.py` 和 `multimodal_retriever.py` 各有一份 MediaType 定义 | 统一到单一定义 |

### 审查结论

**当前多模态管道无法端到端运行。** 从索引到检索的完整链路存在多处断裂。但处理模块（gemini_vision、image_processor、pdf_processor）质量可靠，可直接复用。实施策略需要：保留处理模块 + 重建集成层 + 新增视觉嵌入路径。

---

## 主题 1：视觉嵌入模型架构

### 方向选择

| 路线 | 方案 | 优势 | 劣势 |
|------|------|------|------|
| A（否决） | 文本代理增强 | 改动小，风险低 | 本质不变，视觉语义丢失 |
| **B（确认）** | **引入视觉嵌入模型** | 原生图像理解，真正多模态 | 需新增模型，VRAM 开销 |

**用户确认状态：** ✅ 路线 B

### 社区验证

| 模型 | 类型 | 特点 | 适用场景 |
|------|------|------|---------|
| **BGE-VL** (BAAI) | 统一嵌入 | ~150M 参数，~0.6GB VRAM，1024d 输出，与 bge-m3 同生态 | 跨模态语义匹配（文本查图、图查文） |
| **ColPali/ColQwen2/ColSmol** | 晚交互检索 | ColBERT 风格多向量嵌入，MaxSim 匹配 | 视觉文档检索（整页理解，保留空间布局） |
| **Visual RAG Toolkit** | 向量压缩 | 训练无关的空间池化，将 ColPali 数千向量压缩到几十个 | 降低存储/检索成本 |

### 确认方案：BGE-VL + ColQwen2.5-multilingual 双路互补架构

> ⚠️ **能力边界声明（验证 session 补充）：** BGE-VL-base 使用 CLIP-vit-base-patch16 backbone，CLIP 主要在英文 web 数据上训练。BGE-VL 的核心价值是**视觉结构相似度匹配**（布局、形状、图表模式），而非图片中中文文本的语义理解。中文文本语义由 Gemini Vision（索引时 OCR+描述）和 bge-m3（文本嵌入）覆盖。

```
┌──────────────────────────────────────────────────────┐
│  Path 1: BGE-VL 统一嵌入路径                          │
│  → 图像和文本映射到同一 1024d 空间                     │
│  → 视觉结构相似度匹配（非中文文本语义）                 │
│  → ~0.6GB VRAM，推理速度快                             │
├──────────────────────────────────────────────────────┤
│  Path 2: ColQwen2.5-multilingual 视觉文档检索路径      │
│  → 整页视觉理解，保留表格/公式/图表空间布局              │
│  → Qwen2-VL backbone 原生中文 OCR 能力（超 GPT-4o）    │
│  → ColBERT 风格 MaxSim 匹配，细粒度相关性               │
│  → 2-stage: 快速预筛(BM25/向量) + MaxSim rerank        │
│  → Visual RAG Toolkit 池化压缩存储                     │
│  → ~4-5GB VRAM（按需加载）                             │
└──────────────────────────────────────────────────────┘
                        ↓
              RRF 融合（第 7 条并行检索路径）
```

**用户确认状态：** ✅ 已确认（含验证 session 修正）

---

## 主题 2：本地模型 vs 云端模型

### 核心洞察

**检索和理解是两个不同的任务，需要不同的策略：**

| 任务类型 | 推荐策略 | 理由 |
|---------|---------|------|
| **检索**（embedding + 向量匹配） | 本地模型 | 延迟敏感、频繁调用、BGE-VL/ColQwen2.5 质量足够 |
| **理解**（OCR + 内容描述 + 上下文生成） | 云端 API (Gemini) | 一次性索引成本、复杂视觉理解需要大模型能力 |

### 确认方案：混合策略

```
索引时（一次性）：
  图像 → Gemini Vision API → OCR文本 + 描述 + 概念提取
  图像 → BGE-VL（本地） → 1024d 视觉嵌入向量
  文档页 → ColQwen2.5-multilingual（本地） → 多向量嵌入 → Visual RAG Toolkit 池化

检索时（每次查询）：
  查询 → BGE-VL（本地） → 1024d 查询向量 → LanceDB 向量检索
  查询 → ColQwen2.5-multilingual（本地） → 2-stage: 预筛 + MaxSim rerank
  → RRF 融合 → 返回结果
```

**用户确认状态：** ✅ 已确认

---

## 主题 3：文档解析框架（~~Docling~~ → MinerU 集成）

> ⛔ **验证 session 重大修正：** 原方案选择 Docling (IBM)，验证 session deep explore 发现 Docling 中文支持存在系统性问题（GitHub Issues #225, #748, #2737 报告中文乱码、GLYPH 伪影），不适合以中文教育材料为主的场景。MinerU 在 OmniDocBench (CVPR 2025) 上中文表现超过 GPT-4o，MinerU2.5 (1.2B params) 超 Gemini 2.5 Pro。

### 社区验证（修正后）

| 特性 | MinerU (OpenDataLab) | Docling (IBM) ⛔ | 现状 (PyMuPDF) |
|------|---------------------|-----------------|----------------|
| 中文文本 | OmniDocBench SOTA，OCR F1=0.965 | 乱码（Issues #225,#748） | 基础支持 |
| 表格识别 | HTML 表格输出 + 跨页合并 | TableFormer 94%+，但中文 GLYPH | 无结构化表格提取 |
| 公式提取 | LaTeX 公式提取 | LaTeX 公式提取 | 不支持 |
| 布局分析 | 多模型布局检测 | 多模型布局检测 | 仅文本+图片提取 |
| 智能分块 | 输出 Markdown → MarkdownHeaderSplitter | HybridChunker 内置 | 固定字符切分 500 chars |
| 速度 | ~3.3s/页 | 比 PyMuPDF 慢 30-80x | 极快 |

### 确认方案（修正后）：PyMuPDF + MinerU 混合架构

```
保留 PyMuPDF（快速预处理）
  → 文件类型检测、缩略图生成、基础元数据提取

新增 MinerU（深度中文内容提取）
  → 结构化文档解析：表格(HTML) + 公式(LaTeX) + 布局分析
  → 输出 Markdown 格式，保留标题层级
  → PaddleOCR 原生中文 OCR（无需额外配置）

分块策略：MarkdownHeaderSplitter
  → MinerU 输出 markdown → 按标题层级感知分块
  → bge-m3 tokenizer 做 token 预算控制（目标 256 tokens，80% 模型上限）

分工：
  PDF/DOCX/PPTX → MinerU 解析 → Markdown → MarkdownHeaderSplitter → chunks
  图片(PNG/JPG) → image_processor + Gemini Vision → 描述 → BGE-VL 嵌入
  Canvas(.canvas) → 现有 canvas 解析逻辑
```

**风险提示：** MinerU 速度比 PyMuPDF 慢（~3.3s/页），适合索引时批量处理，不适合实时解析。

**用户确认状态：** ✅ 已确认（验证 session 修正后）

---

## 主题 4：多模态 Reranking

### 社区验证

| 模型 | 类型 | 特点 |
|------|------|------|
| **Jina Reranker M0** | 多模态交叉编码器 | 文本+图像联合排序，mRAG benchmark SOTA |
| **MonoQwen2-VL** | 视觉语言 reranker | 基于 Qwen2-VL，整页图像理解排序 |

### 确认方案

Phase 3 引入 Jina Reranker M0 作为多模态精排层，按需加载（节省 VRAM），配合现有 bge-reranker-base 文本精排形成双层 reranking。

**用户确认状态：** ✅ 已确认（Phase 3）

---

## 3-Phase 实施蓝图（修正后）

### 依赖关系图

```
Phase 1 ─────────────────────────────────────────────────────────────
  修复 5 个断裂点 + 重写 multimodal_store.py + MinerU 集成 + BGE-VL
  │  基础管道恢复端到端运行 | 首次引入真正视觉嵌入
  │
Phase 2 ─────────────────────────────────────────────────────────────
  ColQwen2.5-multilingual + 2-stage 检索 + Visual RAG Toolkit
  │  第 7 条并行检索路径 | 视觉文档检索能力
  │
Phase 3 ─────────────────────────────────────────────────────────────
  Jina Reranker M0 + 性能调优 + 按需加载
     多模态精排 | VRAM 管理优化
```

### Phase 1：基建修复 + 视觉嵌入基础（~3-4 天）

**目标：** 修复管道断裂，引入 MinerU 文档解析和 BGE-VL 视觉嵌入

| 任务 | 文件 | 改动类型 | 覆盖 |
|------|------|---------|------|
| 修复 BP-1: 向量维度统一 | `multimodal_content.py`, `config.py` | 修改 | 断裂修复 |
| 修复 BP-2: Protocol 对齐 | `multimodal_retriever.py` | 修改 | 断裂修复 |
| 修复 BP-3: 重写 multimodal_store.py | `multimodal_store.py` | **完全重写** | 断裂修复 |
| 修复 BP-4: Fake async 修复 | 多文件 | 修改 | 断裂修复 |
| 修复 BP-5: MediaType 统一 | `multimodal_content.py`, `multimodal_retriever.py` | 修改 | 断裂修复 |
| 集成 MinerU + MarkdownHeaderSplitter | 新文件 `processors/mineru_processor.py` | 新建 | 文档解析 |
| 集成 BGE-VL-base | `multimodal_vectorizer.py` | 重构 | 视觉嵌入 |
| LanceDB 视觉向量表 | `lancedb_client.py` | 新增 | 存储 |
| Gemini Vision 小修 | `gemini_vision.py` | minor fix | 处理模块 |
| Image/PDF processor 小修 | `image_processor.py`, `pdf_processor.py` | minor fix | 处理模块 |
| RRF 融合权重修复 | `rrf_fusion.py` | 修改 | 融合 |

**VRAM 预算：** ~1.6GB（BGE-VL ~0.6GB + MinerU ~1GB（仅索引时加载） + overhead）
**索引重建：** 1 次（新向量维度 + 新文档解析）
**交付物：** 多模态管道端到端可运行 + BGE-VL 视觉嵌入 + MinerU 结构化解析

### Phase 2：视觉文档检索（~3-4 天）

**目标：** 新增 ColQwen2.5-multilingual 视觉文档检索路径

| 任务 | 文件 | 改动类型 | 覆盖 |
|------|------|---------|------|
| 集成 ColQwen2.5-multilingual | 新文件 `processors/colpali_processor.py` | 新建 | 视觉检索 |
| LanceDB tensor index (多向量) | `lancedb_client.py` | 新增 | 存储 |
| Visual RAG Toolkit 池化 | `colpali_processor.py` | 新增 | 向量压缩 |
| 2-stage 检索架构 | `retrievers/visual_retriever.py` 新建 | 新建 | 预筛+MaxSim |
| 第 7 条并行检索路径 | `nodes.py`, `state_graph.py` | 修改 | 检索管道 |
| RRF 融合新增视觉路径权重 | `rrf_fusion.py`, `nodes.py` | 修改 | 融合 |

**新增 VRAM：** ~4-5GB（ColQwen2.5-7b ~4GB，按需加载）
**索引重建：** 1 次（新增多向量索引）
**交付物：** 7 路并行检索（含视觉文档检索） + 整页视觉理解能力 + 2-stage 扩展性

### Phase 3：多模态精排 + 优化（~2-3 天）

**目标：** 多模态 reranking + 性能调优 + VRAM 管理

| 任务 | 文件 | 改动类型 | 覆盖 |
|------|------|---------|------|
| Jina Reranker M0 集成 | `reranking.py` | 新增 | 精排 |
| 按需加载（on-demand loading） | 模型管理模块 | 新建 | VRAM 管理 |
| Post-retrieval 视觉 QA | `nodes.py` | 修改 | 质量增强 |
| 性能调优 + benchmark | 测试文件 | 新建 | 验证 |
| 端到端集成测试 | 测试文件 | 新建 | 验证 |

**Peak VRAM：** ~7-8GB（所有模型同时加载时的峰值，ColQwen2.5 比 ColSmol 大）
**索引重建：** 不需要
**交付物：** 多模态精排 + 优化后的完整多模态检索管道

### 总览（修正后）

| Phase | 天数 | 索引重建 | 核心产出 | VRAM |
|-------|------|---------|---------|------|
| P1 | 3-4 | 1次 | 断裂修复 + MinerU + BGE-VL | ~1.6GB |
| P2 | 3-4 | 1次 | ColQwen2.5-multilingual + 2-stage + 7 路并行 | +~4-5GB |
| P3 | 2-3 | 无 | Jina Reranker + 性能优化 | Peak ~7-8GB |
| **合计** | **8-11** | **2次** | **完整多模态检索增强** | — |

---

## Decision-Review 审查项（修正后）

### DR-A5-1: BGE-VL 视觉嵌入模型选型

- **决策内容：** 选择 BGE-VL-base 作为统一多模态嵌入模型（1024d），与 bge-m3 同生态，用于**视觉结构相似度匹配**（非中文文本语义）
- **能力边界（验证 session 补充）：** CLIP backbone 限制中文视觉-文本理解，中文语义由 Gemini Vision + bge-m3 覆盖
- **否决方案：** 继续使用文本代理（路线 A）；CLIP 系列（生态不匹配）；BGE-VL-MLLM（7.57B，VRAM 过大）
- **涉及模块：** `multimodal_vectorizer.py`, `lancedb_client.py`, `config.py`
- **审查维度：** BGE-VL 在真实教育图片上的视觉结构匹配质量、VRAM 实际占用和推理延迟、与 bge-m3 文本路径的跨模态互补效果
- **验证状态：** PENDING — 待验收标准测试

### DR-A5-2: ColQwen2.5-multilingual 视觉文档检索（修正）

- **决策内容（修正后）：** 引入 **ColQwen2.5-7b-multilingual** 作为视觉文档检索路径，使用 ColBERT 风格多向量嵌入 + **2-stage 检索**（快速预筛 + MaxSim rerank），Visual RAG Toolkit 进行向量压缩
- **修正原因：** ① ColSmol/ColQwen2 训练数据 100% 英文，中文纯 zero-shot；ColQwen2.5-multilingual 为社区多语言变体 ② MaxSim 线性扩展，全量扫描不可行
- **否决方案：** 仅使用 BGE-VL 统一路径（缺少整页视觉理解）；ColSmol（中文能力不足）；直接全量 MaxSim（扩展性差）
- **涉及模块：** 新建 `colpali_processor.py`, `visual_retriever.py`, `lancedb_client.py`
- **审查维度：** ColQwen2.5-multilingual 在中文学术文档上的检索质量（nDCG@5）、2-stage 预筛召回率、Visual RAG Toolkit 池化精度损失、LanceDB tensor index 性能
- **验证状态：** PENDING — 待验收标准测试

### DR-A5-3: MinerU 文档解析框架集成（重大修正）

- **决策内容（修正后）：** 保留 PyMuPDF 快速预处理 + 新增 **MinerU** 深度中文内容提取，**MarkdownHeaderSplitter** 按标题层级分块 + bge-m3 tokenizer 预算
- **修正原因：** Docling 中文支持不是生产就绪（Issues #225,#748,#2737 报告乱码/GLYPH）；MinerU 在 OmniDocBench (CVPR 2025) 中文超 GPT-4o
- **否决方案：** ~~Docling (IBM)~~（中文乱码）；继续使用纯 PyMuPDF（缺少结构化解析）
- **涉及模块：** 新建 `processors/mineru_processor.py`（替代原 `docling_processor.py`）
- **审查维度：** MinerU 在真实中文教科书 PDF 上的解析质量（表格/公式/混合内容）、MarkdownHeaderSplitter 分块质量、与 P0 分块策略的兼容性、相比 PyMuPDF 的改进幅度
- **验证状态：** PENDING — 待验收标准测试

### DR-A5-4: 混合策略（本地检索 + 云端理解）

- **决策内容：** 检索用本地模型（BGE-VL、ColQwen2.5-multilingual），理解/OCR 用云端 API（Gemini Vision），索引时一次性云端调用
- **否决方案：** 全本地（质量不足）；全云端（延迟和成本过高）
- **涉及模块：** `gemini_vision.py`, `multimodal_vectorizer.py`
- **审查维度：** 本地模型检索质量是否满足教育场景需求、Gemini API 成本和延迟实测、离线场景降级策略
- **验证状态：** PENDING — 待验收标准测试

### DR-A5-5: 3-Phase 渐进升级策略（小修正）

- **决策内容（修正后）：** Phase 1 修复+基础（MinerU+BGE-VL） → Phase 2 视觉检索（ColQwen2.5-multilingual+2-stage） → Phase 3 精排，每阶段独立可交付
- **修正原因：** Phase 1 Docling → MinerU 联动修正
- **否决方案：** 一次性全量升级（风险过高）
- **涉及模块：** 全多模态管道
- **审查维度：** Phase 间依赖是否正确、每阶段独立验收可行性、与 P0 分块/bge-m3 迁移的时序兼容性
- **验证状态：** PENDING — 待验收标准测试

---

## 验收标准

> 由独立验证 session 基于 3 个并行 deep explore agent 的社区调研结果制定。每个标准有明确 PASS/FAIL 判定条件，测试必须使用真实教育材料。

### 通用前置要求

- **测试数据集：** 从用户真实 Obsidian vault 和教科书 PDF 中抽取，禁止合成数据
- **最低测试集规模：** 50 queries（每类至少 10 queries），覆盖：纯文本查询、公式相关查询、图表相关查询、代码截图查询、跨模态查询（文本查图）
- **Baseline 测量：** 修改前先记录当前系统的检索质量指标作为对比基准
- **统计检验：** 使用配对 Wilcoxon 符号秩检验比较新旧系统，显著性 p < 0.05

### AC-A5-1: BGE-VL 视觉嵌入验收标准

| # | 验收项 | PASS 条件 | FAIL 条件 | 测试方法 |
|---|--------|----------|----------|---------|
| 1.1 | 模型初始化 | BGE-VL-base 加载成功，VRAM ≤ 0.8GB，常驻不卸载 | 加载失败或 VRAM > 1GB | `nvidia-smi` 实测 |
| 1.2 | 嵌入生成 | 图像和文本均输出 1024d 向量，非零，范数合理 | 输出维度不一致或零向量 | 单元测试 |
| 1.3 | 视觉结构匹配 | 相似布局的图表（如两张不同内容的流程图）余弦相似度 > 0.6 | 相似图表相似度 < 0.4 | 10 组配对图片实测 |
| 1.4 | 跨模态检索 | 文本描述 → 检索对应图片，Hit@5 ≥ 0.5（在 50 张图片库中） | Hit@5 < 0.3 | 20 条跨模态查询 |
| 1.5 | 推理延迟 | 单张图片嵌入 P95 < 50ms，单条文本嵌入 P95 < 20ms | P95 > 100ms | 100 次推理取 P95 |
| 1.6 | 与 bge-m3 互补 | BGE-VL 视觉路径检索到的结果中，至少 30% 是纯文本路径未检索到的 | 互补结果 < 10%（说明路径冗余） | 50 条查询对比两路径结果 |

### AC-A5-2: ColQwen2.5-multilingual 视觉文档检索验收标准

| # | 验收项 | PASS 条件 | FAIL 条件 | 测试方法 |
|---|--------|----------|----------|---------|
| 2.1 | 中文文档检索 | 中文学术 PDF 页面检索 nDCG@5 ≥ 0.50 | nDCG@5 < 0.35 | 30 条中文查询 + 真实 PDF 页面标注 |
| 2.2 | 表格/公式定位 | 查询"XX公式"或"XX表格"时，包含目标的页面出现在 Top-5 中 ≥ 60% | < 40% | 20 条公式/表格定位查询 |
| 2.3 | 池化精度损失 | Visual RAG Toolkit 池化后 nDCG@5 下降 ≤ 0.02 | 下降 > 0.05 | 同一测试集，池化前后对比 |
| 2.4 | 2-stage 召回 | 预筛阶段 Recall@100 ≥ 0.85（确保 MaxSim 候选集包含正确页面） | Recall@100 < 0.70 | 50 条查询 |
| 2.5 | 检索延迟 | 2-stage 总延迟 P95 < 500ms（预筛 + MaxSim rerank） | P95 > 1s | 100 次查询取 P95 |
| 2.6 | VRAM 管理 | 按需加载/卸载正常，加载后 VRAM ≤ 5.5GB | 内存泄漏或加载失败 | 10 次加载/卸载循环 |

### AC-A5-3: MinerU 文档解析验收标准

| # | 验收项 | PASS 条件 | FAIL 条件 | 测试方法 |
|---|--------|----------|----------|---------|
| 3.1 | 中文文本准确率 | 中文 PDF 文本提取编辑距离 ≤ 5%（vs ground truth） | 编辑距离 > 10% 或出现乱码/GLYPH | 10 页中文教科书 PDF 人工校对 |
| 3.2 | 表格提取 | 简单表格行列数正确率 ≥ 90%；复杂表格（合并单元格） ≥ 70% | 简单表格 < 80% | 10 个简单 + 5 个复杂表格 |
| 3.3 | 公式提取 | LaTeX 公式提取可编译率 ≥ 80% | < 60% | 20 个公式（行内+行间） |
| 3.4 | 分块质量 | MarkdownHeaderSplitter 输出的 chunk 中，90%+ 的 chunk 内容语义连贯（人工判定） | < 80% 连贯 | 随机抽样 30 个 chunk 人工评估 |
| 3.5 | Token 预算 | 95% 的 chunk token 数在目标预算的 80%-120% 范围内 | > 20% 的 chunk 超出 150% 预算 | 统计全量 chunk 的 token 分布 |
| 3.6 | vs PyMuPDF 改进 | 综合评分（文本+表格+公式）相比 PyMuPDF baseline 提升 ≥ 15% | 提升 < 5%（不值得引入复杂度） | 同一测试集双跑对比 |
| 3.7 | 解析速度 | 平均 ≤ 5s/页 | > 10s/页 | 20 页 PDF 计时 |

### AC-A5-4: 混合策略验收标准

| # | 验收项 | PASS 条件 | FAIL 条件 | 测试方法 |
|---|--------|----------|----------|---------|
| 4.1 | 端到端检索管道 | 文本查询 → 检索结果包含文本+图片+文档页面，管道不报错 | 任何环节抛异常或返回空 | 20 条端到端查询 |
| 4.2 | 检索质量 | 多模态检索 Precision@5 ≥ 0.60（含视觉结果） | Precision@5 < 0.40 | 50 条查询 + 人工标注相关性 |
| 4.3 | 检索延迟 | 全管道检索 P95 < 1s（不含 LLM 生成） | P95 > 2s | 100 次查询取 P95 |
| 4.4 | Gemini 索引成本 | 100 张图片索引 API 成本 ≤ $0.50 | > $1.00 | 实测 100 张图片 |
| 4.5 | 离线降级 | Gemini API 不可用时，系统降级为纯本地检索（BGE-VL + bge-m3），不崩溃 | 系统崩溃或无响应 | 断网测试 |
| 4.6 | 多模态增益 | 多模态检索相比纯文本检索，answer correctness 提升 ≥ 5% | 无提升或负增益 | 50 条查询 AB 对比 |

### AC-A5-5: 3-Phase 渐进升级验收标准

| # | 验收项 | PASS 条件 | FAIL 条件 | 测试方法 |
|---|--------|----------|----------|---------|
| 5.1 | Phase 1 独立交付 | P1 完成后管道端到端可运行，BGE-VL + MinerU 工作正常 | 依赖 P2/P3 组件才能运行 | P1 完成后独立测试 |
| 5.2 | Phase 2 独立交付 | P2 完成后 ColQwen2.5 路径可运行，与 P1 路径 RRF 融合正常 | P2 破坏 P1 已有功能 | P2 完成后回归测试 P1 |
| 5.3 | Phase 间无回归 | 每个 Phase 完成后，前序 Phase 的验收标准仍全部 PASS | 任何前序标准 FAIL | 全量回归测试 |
| 5.4 | P0 兼容性 | A5 Phase 1 的 LanceDB schema 变更与 P0 Sprint 1 的 sparse_vector 列兼容 | Schema 冲突导致迁移失败 | Schema 联合测试 |
| 5.5 | 索引重建 | 每次索引重建耗时可预测（文档数 × 单文档时间），无数据丢失 | 重建后文档数少于原始数 | 重建前后文档计数对比 |
| 5.6 | 回滚能力 | 每个 Phase 可独立回滚到前一状态，保留旧索引 | 无法回滚或数据损坏 | 回滚演练 |

---

## 涉及文件清单（修正后）

| 文件 | Phase | 改动类型 |
|------|-------|---------|
| `src/agentic_rag/storage/multimodal_store.py` | P1 | **完全重写** |
| `src/agentic_rag/processors/multimodal_vectorizer.py` | P1 | 重构 |
| `src/agentic_rag/models/multimodal_content.py` | P1 | 修改 |
| `src/agentic_rag/retrievers/multimodal_retriever.py` | P1 | 修改 |
| `src/agentic_rag/processors/gemini_vision.py` | P1 | minor fix |
| `src/agentic_rag/processors/image_processor.py` | P1 | minor fix |
| `src/agentic_rag/processors/pdf_processor.py` | P1 | minor fix |
| `src/agentic_rag/fusion/rrf_fusion.py` | P1, P2 | 修改 |
| `src/agentic_rag/clients/lancedb_client.py` | P1, P2 | 新增 |
| `src/agentic_rag/config.py` | P1 | 修改 |
| `src/agentic_rag/processors/mineru_processor.py` | P1 | **新建**（替代原 docling_processor.py） |
| `src/agentic_rag/processors/colpali_processor.py` | P2 | **新建** |
| `src/agentic_rag/retrievers/visual_retriever.py` | P2 | **新建**（含 2-stage 逻辑） |
| `src/agentic_rag/nodes.py` | P2, P3 | 修改 |
| `src/agentic_rag/state_graph.py` | P2 | 修改 |
| `src/agentic_rag/reranking.py` | P3 | 新增 |
| `backend/app/services/markdown_image_extractor.py` | P1 | 修改 |
| `requirements.txt` | P1, P2, P3 | 修改 |

---

## 与 P0 管道升级的依赖关系（修正后）

| 依赖项 | 说明 |
|--------|------|
| bge-m3 1024d Dense | P0 Sprint 1 完成后，A5 的文本嵌入维度与 P0 一致 |
| MarkdownHeaderSplitter | MinerU 输出 Markdown → MarkdownHeaderSplitter 分块，与 P0 分块策略需兼容（token 预算、bge-m3 tokenizer） |
| Reranker 激活 | P0 Sprint 0 激活的 reranker 是 A5 Phase 3 多模态精排的前置 |
| LanceDB schema | P0 的 sparse_vector 列和 A5 的 visual_vector 列需在同一 schema 演进路径 |

**建议执行顺序：** P0 Sprint 0-1 → A5 Phase 1 → P0 Sprint 2 → A5 Phase 2 → A5 Phase 3

---

## 参考技术（修正后）

| 技术 | 来源 | 用途 |
|------|------|------|
| BGE-VL (bge-visualized) | BAAI/FlagEmbedding | 统一多模态嵌入（1024d），视觉结构匹配 |
| ColQwen2.5-7b-multilingual | Metric-AI (社区) | 多语言视觉文档检索（ColBERT 风格） |
| Visual RAG Toolkit | Daniel van Strien | ColPali 向量压缩（空间池化） |
| **MinerU** | **OpenDataLab** | **结构化中文文档解析（表格 + 公式 + 布局）** |
| MarkdownHeaderSplitter | LangChain/LlamaIndex | 标题层级感知分块 + token 预算 |
| ~~Docling~~ | ~~IBM Research~~ | ~~已否决：中文支持不足~~ |
| ~~HybridChunker~~ | ~~Docling 内置~~ | ~~已否决：随 Docling 一起替换~~ |
| ~~RapidOCR~~ | ~~PaddleOCR 社区~~ | ~~已否决：MinerU 内置 PaddleOCR~~ |
| Jina Reranker M0 | Jina AI | 多模态交叉编码器精排 |
| MonoQwen2-VL | 社区 | 视觉语言 reranker（备选） |

---

## Session 洞察

### 关键发现

1. **当前多模态管道是"伪多模态"** — 图像被 OCR 为纯文本后用文本嵌入检索，视觉语义完全丢失
2. **管道无法端到端运行** — 对抗性审查发现 5 个系统性断裂点，`multimodal_store.py` 调用的 API 全部不存在
3. **处理模块质量可靠** — `gemini_vision.py`、`image_processor.py`、`pdf_processor.py` 经审查可直接复用
4. **检索 vs 理解需要分治** — 本地模型足以支撑检索质量，云端 API 用于一次性索引时的深度理解
5. **⛔ Docling 中文不可用** — 验证 session 发现系统性乱码问题，已修正为 MinerU
6. **BGE-VL 中文边界明确** — CLIP backbone 限制中文文本理解，但视觉结构匹配仍然有效
7. **ColPali 需要多语言变体** — 原版训练 100% 英文，ColQwen2.5-multilingual 更适合中文场景

### 方法论反思

- 对抗性代码审查极其关键 — 没有审查就默认"已实现可复用"会导致实施时才发现管道不通
- 增量提问模式有效 — 每个主题单独确认，避免信息过载
- 6 agent 并行调研 + 两轮迭代覆盖了足够的技术广度和深度
- **验证 session 的价值** — 独立 session 的 deep explore 发现了原决策 session 未触及的关键风险（Docling 中文、ColPali 训练语言），验证了"决策有效性不由决策 session 自己判定"的原则
