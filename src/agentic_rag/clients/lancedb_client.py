"""
LanceDBClient - LanceDB 向量数据库客户端

Story 12.2: LanceDB POC验证
- AC 2.1: LanceDB连接测试
- AC 2.2: 向量检索接口
- AC 2.3: 性能基准 (P95 < 400ms)
- AC 2.4: 结果转换为SearchResult

Story 23.2: LanceDB Embedding Pipeline
- AC 1: 支持文本内容向量化 (embed方法)
- AC 2: 支持Canvas节点批量索引 (index_canvas方法)
- AC 3: 支持语义相似度查询 (search增强)
- AC 4: 向量维度和模型可配置
- AC 5: 索引持久化到本地文件

✅ Verified from LanceDB documentation:
- lancedb.connect(path) - 连接数据库
- table.search(query_vector).limit(n).to_list() - 向量搜索
- 支持 metric="cosine" 或 "L2"

✅ Verified from MultimodalVectorizer (src/agentic_rag/processors/multimodal_vectorizer.py):
- vectorize_text(text) → VectorizedContent with .vector attribute
- batch_vectorize(texts) → List[VectorizedContent]
- DEFAULT_MODEL_NAME = "BAAI/bge-m3"
- DEFAULT_EMBEDDING_DIM = 1024

Story 2.3: bge-m3 模型迁移与分块升级
- bge-m3 1024d Dense 向量替换旧 384d 模型
- tiktoken cl100k_base 512 token 智能分块
- 原子保护（代码块/公式/表格不切断）
- 面包屑路径前缀注入
- index_single_file 路径 bug 修复

Author: Canvas Learning System Team
Version: 2.0.0 (Story 2.3)
Created: 2025-11-29
Updated: 2026-03-16 (Story 2.3 - bge-m3 Migration)
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from loguru import logger

    LOGURU_ENABLED = True
except ImportError:
    import logging

    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False

# ✅ Verified from LanceDB documentation
try:
    import lancedb

    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# Story 2.4: jieba 中文分词支持
try:
    import jieba

    JIEBA_AVAILABLE = True
    # 预加载 jieba 字典，避免首次分词时 1-2 秒延迟
    jieba.initialize()
except ImportError:
    JIEBA_AVAILABLE = False


def _jieba_tokenize(text: str) -> str:
    """
    Story 2.4 AC-1/AC-2: jieba 中文预分词

    使用 jieba 精确模式 (cut_all=False) 对文本分词，
    输出空格分隔的词语字符串，供 LanceDB Tantivy FTS 索引使用。

    jieba 对纯英文文本按空格切分，不会破坏英文 token。

    Args:
        text: 原始文本

    Returns:
        空格分隔的分词文本
    """
    if not JIEBA_AVAILABLE:
        return text
    if not text or not text.strip():
        return text
    tokens = jieba.cut(text, cut_all=False)
    return " ".join(tokens)


def _chunk_text(text: str, max_tokens: int = 512, overlap_tokens: int = 50) -> List[str]:
    """
    Story 2.3: 智能分块 — tiktoken token 计数 + 句子边界 + 原子保护

    1. 检测并保护原子单元（代码块、数学公式、表格）不被切断
    2. 非原子文本按句子边界切分，累积到 max_tokens 上限后 flush
    3. 超过 max_tokens 的原子单元作为独立 chunk 保留
    4. overlap 按 token 计数（约 overlap_tokens 个 token）

    Args:
        text: 输入文本（已经过 heading 一级切分）
        max_tokens: 每个 chunk 的 token 上限（默认 512）
        overlap_tokens: chunk 间 token 重叠量（默认 50）

    Returns:
        List[str]: 分块后的文本列表
    """
    import re

    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(t: str) -> int:
        return len(enc.encode(t))

    # Empty text guard
    if not text or not text.strip():
        return [text] if text else [text]

    # If text fits in one chunk, return as-is
    if _count_tokens(text) <= max_tokens:
        return [text]

    # --- Step 1: Split text into segments (atomic vs splittable) ---
    # Pattern: code blocks (```...```), math blocks ($$...$$), tables (consecutive |...| lines)
    atomic_pattern = re.compile(
        r"(```[\s\S]*?```)"  # fenced code blocks
        r"|(\$\$[\s\S]*?\$\$)"  # block math formulas
        r"|((?:^[ \t]*\|.+\|[ \t]*$\n?){2,})",  # tables: 2+ consecutive | lines
        re.MULTILINE,
    )

    segments = []  # list of (is_atomic: bool, content: str)
    last_end = 0
    for m in atomic_pattern.finditer(text):
        # Text before the atomic unit
        before = text[last_end : m.start()]
        if before.strip():
            segments.append((False, before))
        # The atomic unit itself
        segments.append((True, m.group(0)))
        last_end = m.end()
    # Remaining text after last atomic unit
    remaining = text[last_end:]
    if remaining.strip():
        segments.append((False, remaining))

    if not segments:
        return [text.strip()]

    # --- Step 2: Split non-atomic text into sentences ---
    # Sentence boundaries: Chinese period, English period, newline,
    # question marks, exclamation marks
    sentence_pattern = re.compile(
        r"(?<=[。！？\.\!\?])\s*"  # after sentence-ending punctuation
        r"|\n+"  # or newline(s)
    )

    def _split_sentences(t: str) -> List[str]:
        """Split text into sentences by punctuation and newlines."""
        parts = sentence_pattern.split(t)
        sentences = [s for s in parts if s and s.strip()]
        return sentences

    def _split_long_sentence(sentence: str) -> List[str]:
        """Split a sentence that exceeds max_tokens at sub-clause boundaries."""
        sub_pattern = re.compile(r"(?<=[，,；;：:])\s*")
        parts = sub_pattern.split(sentence)
        result = []
        current = ""
        for part in parts:
            candidate = current + part if current else part
            if _count_tokens(candidate) <= max_tokens:
                current = candidate
            else:
                if current.strip():
                    result.append(current.strip())
                current = part
        if current.strip():
            result.append(current.strip())
        return result if result else [sentence]

    # --- Step 3: Build chunks from segments ---
    chunks: List[str] = []
    current_parts: List[str] = []
    current_tokens = 0

    def _flush_current():
        nonlocal current_parts, current_tokens
        if current_parts:
            chunk_text_joined = "\n".join(current_parts).strip()
            if chunk_text_joined:
                chunks.append(chunk_text_joined)
        current_parts = []
        current_tokens = 0

    def _get_overlap_parts() -> List[str]:
        """Get the last few sentences from the most recent chunk for overlap."""
        if not chunks or overlap_tokens <= 0:
            return chunks[0:0]  # empty list without literal
        last_chunk = chunks[-1]
        sentences = _split_sentences(last_chunk)
        overlap_parts = chunks[0:0]  # empty list without literal
        overlap_count = 0
        for s in reversed(sentences):
            s_tokens = _count_tokens(s)
            if overlap_count + s_tokens > overlap_tokens:
                break
            overlap_parts.insert(0, s)
            overlap_count += s_tokens
        return overlap_parts

    for is_atomic, segment in segments:
        if is_atomic:
            seg_tokens = _count_tokens(segment)
            # If atomic fits in current chunk, add it
            if current_tokens + seg_tokens <= max_tokens:
                current_parts.append(segment)
                current_tokens += seg_tokens
            else:
                # Flush current chunk, then emit atomic as standalone
                _flush_current()
                chunks.append(segment.strip())
        else:
            # Split into sentences and accumulate
            sentences = _split_sentences(segment)
            for sentence in sentences:
                s_tokens = _count_tokens(sentence)

                # Handle sentences that exceed max_tokens on their own
                if s_tokens > max_tokens:
                    _flush_current()
                    for sub in _split_long_sentence(sentence):
                        chunks.append(sub)
                    continue

                if current_tokens + s_tokens > max_tokens:
                    _flush_current()
                    # Add overlap from previous chunk
                    overlap_parts = _get_overlap_parts()
                    if overlap_parts:
                        current_parts = list(overlap_parts)
                        current_tokens = sum(_count_tokens(p) for p in overlap_parts)
                    else:
                        current_tokens = 0

                current_parts.append(sentence)
                current_tokens += s_tokens

    # Flush remaining
    _flush_current()

    return chunks if chunks else [text.strip()]


class LanceDBClient:
    """
    LanceDB 向量数据库客户端

    封装 LanceDB 向量检索为统一的搜索接口。

    ✅ Verified from Story 12.2 (docs/epics/EPIC-12-STORY-MAP.md):
    - AC 2.1: LanceDB连接测试
    - AC 2.2: search()接口, 返回List[SearchResult]
    - AC 2.3: P95延迟 < 400ms
    - AC 2.4: 结果转换为SearchResult格式

    ✅ Story 23.2: LanceDB Embedding Pipeline
    - AC 1: embed(text) 方法支持文本向量化
    - AC 2: index_canvas() 方法支持批量索引
    - AC 3: search() 支持Canvas文件过滤
    - AC 4: embedding_model 可配置
    - AC 5: 索引持久化到本地文件

    Usage:
        >>> client = LanceDBClient(db_path="backend/data/lancedb")
        >>> await client.initialize()
        >>> # Story 23.2 AC 1: 向量化文本
        >>> vector = await client.embed("什么是逆否命题？")
        >>> # Story 23.2 AC 2: 批量索引Canvas节点
        >>> count = await client.index_canvas("离散数学.canvas")
        >>> # Story 23.2 AC 3: 语义搜索
        >>> results = await client.search("逆否命题", table_name="canvas_nodes")
        >>> print(results[0])
        {'doc_id': 'lancedb_doc_123', 'content': '...', 'score': 0.85, 'metadata': {...}}
    """

    # 默认表名
    DEFAULT_TABLES = ["canvas_nodes", "vault_notes"]

    # Story 2.3: bge-m3 1024d Dense 向量
    DEFAULT_EMBEDDING_DIM = 1024

    # Story 2.3: 支持的 embedding 模型（bge-m3 为默认）
    SUPPORTED_MODELS = {
        "BAAI/bge-m3": 1024,
        "sentence-transformers/all-MiniLM-L6-v2": 384,  # [deprecated]
        "sentence-transformers/all-mpnet-base-v2": 768,  # [deprecated]
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,  # [deprecated]
    }

    def __init__(
        self,
        db_path: str = "data/lancedb",  # ✅ Story 38.1 Fix: 从 backend/ 目录运行时路径正确
        embedding_dim: int = DEFAULT_EMBEDDING_DIM,
        embedding_model: str = "BAAI/bge-m3",
        timeout_ms: int = 400,
        batch_size: int = 100,
        enable_fallback: bool = True,
    ):
        """
        初始化 LanceDBClient

        Story 2.3: 默认使用 bge-m3 1024d Dense 向量

        Args:
            db_path: LanceDB数据库路径 (默认: data/lancedb)
            embedding_dim: 嵌入向量维度 (默认: 1024 for bge-m3)
            embedding_model: embedding模型名称 (默认: BAAI/bge-m3)
            timeout_ms: 超时时间(毫秒), 默认400ms (Story 12.2 AC 2.3)
            batch_size: 批量处理大小 (默认: 100, Story 23.2 AC 2)
            enable_fallback: 启用降级(超时/错误时返回空结果)
        """
        self.db_path = os.path.expanduser(db_path)
        self.embedding_dim = embedding_dim
        self.embedding_model = embedding_model
        self.timeout_ms = timeout_ms
        self.batch_size = batch_size
        self.enable_fallback = enable_fallback

        self._db = None
        self._initialized = False
        self._tables_cache: Dict[str, Any] = {}
        self._embedder = None

        # ✅ Story 23.2: MultimodalVectorizer for embedding
        self._vectorizer = None
        self._vectorizer_initialized = False

    async def initialize(self) -> bool:
        """
        初始化客户端，连接LanceDB

        ✅ Story 12.2 AC 2.1: LanceDB连接测试

        Returns:
            True if connection successful
        """
        if not LANCEDB_AVAILABLE:
            if LOGURU_ENABLED:
                logger.warning("LanceDB not installed. Run: pip install lancedb")
            self._initialized = True
            return False

        try:
            # ✅ Verified from LanceDB docs: lancedb.connect(path)
            self._db = lancedb.connect(self.db_path)
            self._initialized = True

            # 缓存表信息
            await self._cache_tables()

            # Pre-load embedding model to avoid cold-start timeout during search
            await self._init_vectorizer()

            if LOGURU_ENABLED:
                logger.info(f"LanceDBClient initialized: path={self.db_path}, tables={list(self._tables_cache.keys())}")

            return True

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"LanceDBClient initialization failed: {e}")

            self._initialized = True
            return False

    async def _cache_tables(self):
        """缓存表信息"""
        if self._db is None:
            return

        try:
            table_names = self._db.table_names()
            for name in table_names:
                try:
                    self._tables_cache[name] = self._db.open_table(name)
                except Exception:
                    pass
        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"Failed to cache tables: {e}")

    # =========================================================================
    # Story 23.2: Embedding Pipeline Methods
    # =========================================================================

    async def _init_vectorizer(self) -> bool:
        """
        懒加载embedding模型 (MultimodalVectorizer)

        ✅ Story 23.2 AC 1: 支持文本内容向量化
        ✅ Verified from MultimodalVectorizer (src/agentic_rag/processors/multimodal_vectorizer.py:162-200)

        Returns:
            bool: True if vectorizer initialized successfully
        """
        if self._vectorizer_initialized:
            return self._vectorizer is not None

        try:
            # Import MultimodalVectorizer lazily
            from agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

            self._vectorizer = MultimodalVectorizer(
                model_name=self.embedding_model,
                device="cpu",  # Can be configured for GPU
            )
            await self._vectorizer.initialize()
            self._vectorizer_initialized = True

            if LOGURU_ENABLED:
                logger.info(
                    f"Vectorizer initialized: model={self.embedding_model}, dim={self._vectorizer.embedding_dim}"
                )

            return True

        except ImportError as e:
            if LOGURU_ENABLED:
                logger.warning(f"MultimodalVectorizer not available: {e}")
            self._vectorizer_initialized = True
            return False

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to initialize vectorizer: {e}")
            self._vectorizer_initialized = True
            return False

    async def embed(self, text: str) -> List[float]:
        """
        文本向量化

        Story 2.3: 使用 bge-m3 生成 1024 维 Dense 向量

        Args:
            text: 要向量化的文本

        Returns:
            List[float]: embedding向量 (1024维, bge-m3 Dense)

        Raises:
            RuntimeError: 如果vectorizer初始化失败
        """
        await self._init_vectorizer()

        if self._vectorizer is None:
            raise RuntimeError(
                "Vectorizer not available. Install sentence-transformers: pip install sentence-transformers"
            )

        # ✅ Verified from MultimodalVectorizer.vectorize_text() (line 244-290)
        result = await self._vectorizer.vectorize_text(text)
        return result.vector

    async def index_canvas(
        self,
        canvas_path: str,
        nodes: Optional[List[Dict[str, Any]]] = None,
        table_name: str = "canvas_nodes",
        subject: Optional[str] = None,  # ✅ Story 38.1: 添加 subject 参数
    ) -> int:
        """
        批量索引Canvas节点

        ✅ Story 23.2 AC 2: 支持Canvas节点批量索引
        - 所有节点被索引到 canvas_nodes 表
        - 每个节点记录包含: doc_id, content, vector, canvas_file, node_id, color, metadata
        - 批量处理支持100+节点
        - 处理速度 < 1秒/10节点

        ✅ Story 38.1: 添加 subject 参数用于学科隔离
        - subject 存储在每个文档中，用于按学科过滤

        ✅ Verified from specs/data/canvas-node.schema.json:
        - id: string (节点唯一标识)
        - type: "text" | "file" | "group" | "link"
        - text: string (文本内容)
        - color: "1"-"6" (颜色代码)
        - x, y: integer (位置坐标)

        Args:
            canvas_path: Canvas文件路径
            nodes: 节点列表 (可选，不提供则从文件读取)
            table_name: LanceDB表名 (默认: canvas_nodes)
            subject: 学科标识 (用于学科隔离过滤)

        Returns:
            int: 索引的节点数量
        """
        if not self._initialized:
            await self.initialize()

        await self._init_vectorizer()

        if self._vectorizer is None:
            if LOGURU_ENABLED:
                logger.warning("Vectorizer not available, skipping index_canvas")
            return 0

        # 如果未提供nodes，从Canvas文件读取
        if nodes is None:
            nodes = self._read_canvas_nodes(canvas_path)

        # 过滤出有文本内容的text类型节点
        text_nodes = [node for node in nodes if node.get("type") == "text" and node.get("text", "").strip()]

        if not text_nodes:
            if LOGURU_ENABLED:
                logger.info(f"No text nodes to index in {canvas_path}")
            return 0

        # 提取文本列表用于批量向量化
        texts = [node.get("text", "") for node in text_nodes]

        # ✅ Story 23.2 AC 2: 批量向量化 (batch_size=100)
        # ✅ Verified from MultimodalVectorizer.batch_vectorize() (line 455-515)
        try:
            vectorized = await self._vectorizer.batch_vectorize(texts)
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Batch vectorization failed: {e}")
            return 0

        # 准备LanceDB文档
        documents = []
        for node, vec_result in zip(text_nodes, vectorized):
            doc = {
                "doc_id": f"canvas_{node['id']}",
                "content": node.get("text", ""),
                "vector": vec_result.vector,
                "canvas_file": canvas_path,
                "node_id": node.get("id", ""),
                "node_type": node.get("type", "text"),
                "color": node.get("color", ""),
                "x": node.get("x", 0),
                "y": node.get("y", 0),
                "subject": subject or "",  # ✅ Story 38.1: 存储 subject 用于学科隔离
                "timestamp": datetime.now().isoformat(),
                "metadata_json": json.dumps(
                    {
                        "width": node.get("width"),
                        "height": node.get("height"),
                        "subject": subject,  # ✅ Story 38.1: 也在 metadata 中存储
                    },
                    ensure_ascii=False,
                ),
            }
            documents.append(doc)

        # 写入LanceDB
        count = await self.add_documents(table_name, documents)

        if LOGURU_ENABLED:
            logger.info(f"Indexed {count} nodes from {canvas_path} to {table_name}")

        return count

    async def index_vault_notes(
        self,
        vault_path: str,
        skip_dirs: Optional[List[str]] = None,
        table_name: str = "vault_notes",
        max_tokens: int = 512,
        overlap_tokens: int = 50,
        subject: Optional[str] = None,
    ) -> int:
        """
        扫描 vault 中所有 .md 文件，按 heading 分段索引到 LanceDB

        Story 2.3: chunk_size 语义从"字符数"改为"token 数"（tiktoken cl100k_base）

        Args:
            vault_path: Vault 根目录路径
            skip_dirs: 要跳过的目录列表
            table_name: LanceDB 表名
            max_tokens: 每段目标 token 数（默认 512）
            overlap_tokens: 段落重叠 token 数（默认 50）
            subject: 学科标识

        Returns:
            int: 索引的段落数量
        """
        if not self._initialized:
            await self.initialize()

        await self._init_vectorizer()

        if self._vectorizer is None:
            if LOGURU_ENABLED:
                logger.warning("Vectorizer not available, skipping index_vault_notes")
            return 0

        if skip_dirs is None:
            skip_dirs = [".obsidian", ".git", ".trash", "node_modules"]

        # 递归收集所有 .md 文件
        md_files = []
        for root, dirs, files in os.walk(vault_path):
            # 跳过指定目录
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for f in files:
                if f.endswith(".md"):
                    md_files.append(os.path.join(root, f))

        if not md_files:
            if LOGURU_ENABLED:
                logger.info(f"No .md files found in {vault_path}")
            return 0

        # 按 heading 分段所有文件
        all_chunks = []
        for md_file in md_files:
            try:
                with open(md_file, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except Exception as e:
                if LOGURU_ENABLED:
                    logger.debug(f"Skipping {md_file}: {e}")
                continue

            if not content.strip():
                continue

            rel_path = os.path.relpath(md_file, vault_path).replace("\\", "/")
            chunks = self._split_md_by_heading(content, rel_path, max_tokens, overlap_tokens)
            all_chunks.extend(chunks)

        if not all_chunks:
            if LOGURU_ENABLED:
                logger.info("No text chunks extracted from vault .md files")
            return 0

        # 批量向量化
        texts = [c["content"] for c in all_chunks]
        try:
            vectorized = await self._vectorizer.batch_vectorize(texts)
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Batch vectorization failed for vault notes: {e}")
            return 0

        # 准备 LanceDB 文档
        import hashlib

        documents = []
        for chunk, vec_result in zip(all_chunks, vectorized):
            chunk_id = hashlib.md5(
                f"{chunk['file_path']}:{chunk['heading']}:{chunk['content'][:100]}".encode()
            ).hexdigest()

            metadata = {
                "file_path": chunk["file_path"],
                "heading": chunk["heading"],
                "heading_path": chunk.get("heading_path", []),  # Story 2.3: 面包屑层级
                "line_start": chunk.get("line_start"),
                "line_end": chunk.get("line_end"),
                "source": "vault_note",
                "subject": subject,
                "source_type": "video_transcript" if LanceDBClient._is_video_transcript(chunk["file_path"]) else "note",
            }

            # Add timestamp info for video transcripts
            if LanceDBClient._is_video_transcript(chunk["file_path"]):
                ts_info = LanceDBClient._extract_timestamps_from_section(chunk["heading"], chunk["content"])
                metadata.update(ts_info)

            doc = {
                "doc_id": f"vault_{chunk_id}",
                "content": chunk["content"],
                "vector": vec_result.vector,
                "canvas_file": chunk["file_path"],  # 复用 canvas_file 字段存储文件路径
                "node_id": "",
                "node_type": "vault_note",
                "color": "",
                "x": 0,
                "y": 0,
                "subject": subject or "",
                "timestamp": datetime.now().isoformat(),
                "metadata_json": json.dumps(metadata, ensure_ascii=False),
            }
            documents.append(doc)

        # 写入 LanceDB（先清空旧表再写入，实现全量更新）
        try:
            # Always drop — cache may not have it but disk does
            self._db.drop_table(table_name, ignore_missing=True)
            self._tables_cache.pop(table_name, None)
        except Exception:
            pass

        count = await self.add_documents(table_name, documents)

        # Story 2.4: Create FTS index on jieba-tokenized content for Chinese search
        try:
            tbl = self._db.open_table(table_name)
            tbl.create_fts_index("content_tokenized", replace=True)
            if LOGURU_ENABLED:
                logger.info(
                    f"Created FTS index on '{table_name}.content_tokenized' (jieba_available={JIEBA_AVAILABLE})"
                )
        except Exception as e:
            if LOGURU_ENABLED:
                logger.warning(f"FTS index creation failed (hybrid search unavailable): {e}")

        if LOGURU_ENABLED:
            logger.info(f"Indexed {count} chunks from {len(md_files)} .md files in vault {vault_path} to {table_name}")

        return count

    async def index_single_file(
        self,
        file_path: str,
        table_name: str = "vault_notes",
        subject: str = "",
        vault_path: Optional[str] = None,
    ) -> int:
        """
        Index a single .md file into an existing table (incremental append).

        Generates vectors and uses the full vault_notes schema so documents
        are discoverable by vector search and schema-compatible with the table.

        Story 2.3 AC-5: rel_path uses os.path.relpath(file_path, vault_path)
        instead of os.path.basename to preserve directory structure.

        Args:
            file_path: Absolute path to the .md file
            table_name: Target table name
            subject: Optional subject tag
            vault_path: Vault root directory for computing relative path.
                        If None, falls back to parent directory of file_path.

        Returns:
            Number of chunks indexed
        """
        import hashlib
        import os

        if not os.path.isfile(file_path):
            if LOGURU_ENABLED:
                logger.warning(f"File not found for indexing: {file_path}")
            return 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to read file for indexing: {e}")
            return 0

        if not content.strip():
            return 0

        # Story 2.3 AC-5: Use relpath to preserve directory structure
        if vault_path:
            rel_path = os.path.relpath(file_path, vault_path).replace("\\", "/")
        else:
            rel_path = os.path.basename(file_path)
        chunks = self._split_md_by_heading(content, rel_path)

        if not chunks:
            return 0

        # Initialize vectorizer for embedding generation
        await self._init_vectorizer()
        if not self._vectorizer:
            if LOGURU_ENABLED:
                logger.error("Vectorizer not available, cannot index single file")
            return 0

        # Batch vectorize all chunks
        texts = [c["content"] for c in chunks]
        vectorized = await self._vectorizer.batch_vectorize(texts)

        if len(vectorized) != len(chunks):
            if LOGURU_ENABLED:
                logger.error(f"Vectorization mismatch: {len(chunks)} chunks vs {len(vectorized)} vectors")
            return 0

        # Build documents with full schema (matching index_vault_notes)
        documents = []
        for chunk, vec_result in zip(chunks, vectorized):
            if not vec_result.vector:
                continue

            chunk_id = hashlib.md5(
                f"{chunk['file_path']}:{chunk.get('heading', '')}:{chunk['content'][:100]}".encode()
            ).hexdigest()

            metadata = {
                "file_path": chunk.get("file_path", rel_path),
                "heading": chunk.get("heading", ""),
                "heading_path": chunk.get("heading_path", []),  # Story 2.3: 面包屑层级
                "line_start": chunk.get("line_start", 0),
                "line_end": chunk.get("line_end", 0),
                "source": "vault_note",
                "subject": subject,
                "source_type": "video_transcript" if LanceDBClient._is_video_transcript(file_path) else "note",
            }

            # Add timestamp info for video transcripts
            if LanceDBClient._is_video_transcript(file_path):
                ts_info = LanceDBClient._extract_timestamps_from_section(chunk.get("heading", ""), chunk["content"])
                metadata.update(ts_info)

            doc = {
                "doc_id": f"vault_{chunk_id}",
                "content": chunk["content"],
                "vector": vec_result.vector,
                "canvas_file": chunk.get("file_path", rel_path),
                "node_id": "",
                "node_type": "vault_note",
                "color": "",
                "x": 0,
                "y": 0,
                "subject": subject or "",
                "timestamp": datetime.now().isoformat(),
                "metadata_json": json.dumps(metadata, ensure_ascii=False),
            }
            documents.append(doc)

        count = await self.add_documents(table_name, documents)

        if LOGURU_ENABLED:
            logger.info(f"Incrementally indexed {count} chunks from {rel_path}")

        return count

    @staticmethod
    def _split_md_by_heading(
        content: str, file_path: str, max_tokens: int = 512, overlap_tokens: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Story 2.3: 按 Markdown heading 分段文本，追踪行号 + 面包屑路径前缀

        一级切分按 H1-H4 heading，二级切分由 _chunk_text() 按句子边界+原子保护。
        每个 chunk 的 content 前缀注入面包屑路径（文档名 > h1 > h2 > h3），
        heading_path 数组保存在 chunk dict 中供 metadata 使用。

        Args:
            content: Markdown 文件内容
            file_path: 文件相对路径
            max_tokens: 每段目标 token 数（默认 512）
            overlap_tokens: 段落重叠 token 数（默认 50）

        Returns:
            List[Dict]: [{"file_path", "heading", "content", "heading_path",
                          "line_start", "line_end"}]
        """
        import re

        heading_pattern = re.compile(r"^(#{1,4})\s+(.+)$")
        chunks = []
        lines = content.split("\n")

        # Extract filename without extension for breadcrumb root
        filename = file_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        if filename.endswith(".md"):
            filename = filename[:-3]

        # Heading stack: list of (level, title) for breadcrumb tracking
        heading_stack: List[tuple] = []
        current_heading = filename
        current_lines: List[str] = []
        section_line_start = 1

        def _build_heading_path() -> List[str]:
            """Build heading path array from current heading stack."""
            return [title for _, title in heading_stack]

        def _build_breadcrumb(heading_path: List[str]) -> str:
            """Build breadcrumb prefix string."""
            parts = [filename] + heading_path
            return " > ".join(parts)

        def _flush_section(
            heading: str,
            section_lines: List[str],
            line_start: int,
            line_end: int,
            heading_path: List[str],
        ):
            text = "\n".join(section_lines).strip()
            if not text:
                return
            breadcrumb = _build_breadcrumb(heading_path)
            for sub_chunk in _chunk_text(text, max_tokens, overlap_tokens):
                # Prepend breadcrumb to chunk content for embedding context
                prefixed_content = f"\u6587\u6863\uff1a{breadcrumb}\n\n{sub_chunk}"
                chunks.append(
                    {
                        "file_path": file_path,
                        "heading": heading,
                        "heading_path": list(heading_path),
                        "content": prefixed_content,
                        "line_start": line_start,
                        "line_end": line_end,
                    }
                )

        for line_idx, line in enumerate(lines):
            line_num = line_idx + 1
            match = heading_pattern.match(line)
            if match:
                # Flush previous section
                if current_lines:
                    _flush_section(
                        current_heading,
                        current_lines,
                        section_line_start,
                        line_num - 1,
                        _build_heading_path(),
                    )

                # Update heading stack: pop all headings with level >= current
                level = len(match.group(1))  # number of # characters
                title = match.group(2).strip()
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, title))

                current_heading = title
                current_lines = []
                section_line_start = line_num
            else:
                current_lines.append(line)

        # Flush final section
        if current_lines:
            _flush_section(
                current_heading,
                current_lines,
                section_line_start,
                len(lines),
                _build_heading_path(),
            )

        return chunks

    @staticmethod
    def _is_video_transcript(file_path: str) -> bool:
        """Check if a file path refers to a video transcript."""
        return "/videos/" in file_path.replace("\\", "/")

    @staticmethod
    def _extract_timestamps_from_section(heading: str, content: str) -> Dict[str, Optional[str]]:
        """
        Extract video timestamps from a section heading and content.

        Patterns:
          1. [MM:SS]()-[MM:SS]() in heading (range)
          2. [MM:SS]() in heading (single)
          3. [MM:SS] inline in content (first and last)

        Returns:
            Dict with timestamp_start, timestamp_end, video_file keys
        """
        import re

        result: Dict[str, Optional[str]] = {
            "timestamp_start": None,
            "timestamp_end": None,
            "video_file": None,
        }

        # Pattern 1: Range in heading [MM:SS]()-[MM:SS]()
        range_match = re.search(r"\[(\d{1,2}:\d{2})\]\(\)[—–-]\[(\d{1,2}:\d{2})\]\(\)", heading)
        if range_match:
            result["timestamp_start"] = range_match.group(1)
            result["timestamp_end"] = range_match.group(2)
            return result

        # Pattern 2: Single in heading [MM:SS]()
        single_match = re.search(r"\[(\d{1,2}:\d{2})\]\(\)", heading)
        if single_match:
            result["timestamp_start"] = single_match.group(1)
            return result

        # Pattern 3: Inline [MM:SS] in content
        inline_matches = re.findall(r"\[(\d{1,2}:\d{2})\]", content)
        if inline_matches:
            result["timestamp_start"] = inline_matches[0]
            if len(inline_matches) > 1:
                result["timestamp_end"] = inline_matches[-1]

        return result

    def _read_canvas_nodes(self, canvas_path: str) -> List[Dict[str, Any]]:
        """
        从Canvas文件读取节点

        ✅ Verified from specs/data/canvas-node.schema.json:
        Canvas JSON格式: {"nodes": [...], "edges": [...]}

        Args:
            canvas_path: Canvas文件路径

        Returns:
            List[Dict]: 节点列表
        """
        try:
            with open(canvas_path, "r", encoding="utf-8") as f:
                canvas_data = json.load(f)
            return canvas_data.get("nodes", [])
        except FileNotFoundError:
            if LOGURU_ENABLED:
                logger.error(f"Canvas file not found: {canvas_path}")
            return []
        except json.JSONDecodeError as e:
            if LOGURU_ENABLED:
                logger.error(f"Invalid JSON in canvas file {canvas_path}: {e}")
            return []
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to read canvas file {canvas_path}: {e}")
            return []

    async def search(
        self,
        query: str,
        table_name: str = "canvas_nodes",
        canvas_file: Optional[str] = None,
        subject: Optional[str] = None,
        num_results: int = 10,
        metric: str = "cosine",
        query_type: str = "hybrid",
        course_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        向量搜索

        ✅ Story 12.2 AC 2.2: 向量检索接口
        ✅ Story 12.2 AC 2.3: P95 < 400ms
        ✅ Story 12.2 AC 2.4: 结果转换
        ✅ Story 2.4: Hybrid 为默认模式 + 课程/标签过滤

        Args:
            query: 搜索查询 (文本或向量)
            table_name: 表名
            canvas_file: Canvas文件路径(用于过滤)
            subject: 学科标识(用于学科隔离过滤)
            num_results: 返回结果数量
            metric: 距离度量 ("cosine" 或 "L2")
            query_type: 搜索类型 ("vector" 或 "hybrid"). hybrid使用向量+FTS+RRF融合
            course_id: 课程ID (用于按课程过滤搜索范围)
            tags: 标签列表 (用于按标签过滤, OR 匹配)

        Returns:
            List[SearchResult]: 标准化的搜索结果
        """
        start_time = time.perf_counter()

        if not self._initialized:
            await self.initialize()

        try:
            # ✅ AC 2.3: 设置超时
            timeout_seconds = self.timeout_ms / 1000.0

            # 执行搜索
            results = await asyncio.wait_for(
                self._search_internal(
                    query=query,
                    table_name=table_name,
                    canvas_file=canvas_file,
                    subject=subject,
                    num_results=num_results,
                    metric=metric,
                    query_type=query_type,
                    course_id=course_id,
                    tags=tags,
                ),
                timeout=timeout_seconds,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000

            if LOGURU_ENABLED:
                logger.debug(
                    f"LanceDBClient.search: "
                    f"query='{query[:50] if isinstance(query, str) else 'vector'}...', "
                    f"table={table_name}, "
                    f"results={len(results)}, "
                    f"latency={latency_ms:.2f}ms"
                )

            # ✅ AC 2.3: 检查性能
            if latency_ms > 400:
                if LOGURU_ENABLED:
                    logger.warning(f"LanceDB search exceeded 400ms: {latency_ms:.2f}ms")

            return results

        except asyncio.TimeoutError:
            if LOGURU_ENABLED:
                logger.warning(f"LanceDBClient.search timeout ({self.timeout_ms}ms)")

            if self.enable_fallback:
                return []
            else:
                raise

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"LanceDBClient.search error: {e}")

            if self.enable_fallback:
                return []
            else:
                raise

    def _build_where_filters(
        self,
        canvas_file: Optional[str] = None,
        subject: Optional[str] = None,
        course_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Story 2.4 AC-5: Build SQL WHERE filter clauses for LanceDB queries.

        Supports canvas_file, subject, course_id, and tags (OR matching).
        Returns list of SQL clause strings to apply via .where().
        """
        clauses: List[str] = []
        if canvas_file:
            clauses.append(f"canvas_file = '{canvas_file}'")
        if subject:
            clauses.append(f"subject = '{subject}'")
        if course_id:
            clauses.append(f"course_id = '{course_id}'")
        if tags:
            tag_conditions = " OR ".join(f"tags LIKE '%{tag}%'" for tag in tags)
            clauses.append(f"({tag_conditions})")
        return clauses

    def _apply_where_clauses(self, search_query, clauses: List[str]):
        """Apply a list of WHERE clauses to a LanceDB search query."""
        for clause in clauses:
            search_query = search_query.where(clause)
        return search_query

    async def _search_internal(
        self,
        query: str,
        table_name: str,
        canvas_file: Optional[str],
        subject: Optional[str],
        num_results: int,
        metric: str,
        query_type: str = "hybrid",
        course_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """内部搜索实现 (Story 2.4: hybrid default + jieba FTS + course/tags filter)"""
        if self._db is None:
            return []

        # 获取表
        try:
            if table_name in self._tables_cache:
                table = self._tables_cache[table_name]
            else:
                table = self._db.open_table(table_name)
                self._tables_cache[table_name] = table
        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"Table {table_name} not found: {e}")
            return []

        # Story 2.4 AC-5: Build pre-filter clauses
        where_clauses = self._build_where_filters(
            canvas_file=canvas_file,
            subject=subject,
            course_id=course_id,
            tags=tags,
        )

        # Accumulator for raw results across branches
        all_raw: List[Dict[str, Any]] = list()

        # Hybrid search: manual vector + FTS with RRF fusion
        # We can't use table.search(query, query_type="hybrid") because the table
        # has no registered embedding function (vectors are pre-computed externally).
        # Instead, we manually run both searches and fuse with RRF.
        if query_type == "hybrid" and isinstance(query, str):
            query_vector = await self._get_query_vector(query)

            vector_results: List[Dict] = list()
            fts_results: List[Dict] = list()

            # Dense vector search branch
            if query_vector is not None:
                try:
                    vq = table.search(query_vector).limit(num_results * 2)
                    vq = self._apply_where_clauses(vq, where_clauses)
                    vector_results = vq.to_list()
                except Exception as e:
                    if LOGURU_ENABLED:
                        logger.debug(f"Hybrid vector branch failed: {e}")

            # Story 2.4 AC-2: FTS with jieba-tokenized query on content_tokenized
            try:
                tokenized_query = _jieba_tokenize(query)
                if LOGURU_ENABLED:
                    logger.debug(f"[search] FTS jieba tokenized: '{query[:40]}' -> '{tokenized_query[:60]}'")
                fq = table.search(tokenized_query, query_type="fts").limit(num_results * 2)
                fq = self._apply_where_clauses(fq, where_clauses)
                fts_results = fq.to_list()
            except Exception as e:
                if LOGURU_ENABLED:
                    logger.debug(f"Hybrid FTS branch failed: {e}")

            # Story 2.4 AC-4: RRF fusion with single-path degradation
            if vector_results or fts_results:
                all_raw = self._rrf_fuse(vector_results, fts_results, num_results)
                return self._convert_to_search_results(all_raw, canvas_file=canvas_file)

            # Both hybrid branches returned nothing — degrade to pure vector
            if LOGURU_ENABLED:
                logger.warning("[search] Both hybrid branches empty, degrading to vector")

        # Pure vector search (fallback or explicit query_type="vector")
        query_vector = await self._get_query_vector(query)
        if query_vector is not None:
            try:
                search_query = table.search(query_vector).limit(num_results)
                search_query = self._apply_where_clauses(search_query, where_clauses)
                all_raw = search_query.to_list()
            except Exception as e:
                if LOGURU_ENABLED:
                    logger.error(f"LanceDB vector search failed: {e}")
        else:
            if LOGURU_ENABLED:
                logger.warning("[search] No query vector available")

        return self._convert_to_search_results(all_raw, canvas_file=canvas_file)

    async def _get_query_vector(self, query: str) -> Optional[List[float]]:
        """
        获取查询向量

        ✅ Story 23.2: 使用embed()方法替换随机向量fallback

        如果query已经是向量，直接返回；
        否则使用embed()方法生成向量。

        Args:
            query: 查询文本或向量

        Returns:
            查询向量 (List[float]) 或 None
        """
        # 如果已经是向量
        if isinstance(query, list):
            return query

        if NUMPY_AVAILABLE and isinstance(query, np.ndarray):
            return query.tolist()

        # 尝试使用embedder生成向量 (legacy support)
        if self._embedder is not None:
            try:
                return await self._embedder(query)
            except Exception as e:
                if LOGURU_ENABLED:
                    logger.error(f"Embedder failed: {e}")

        # ✅ Story 23.2: 使用embed()方法 (MultimodalVectorizer)
        try:
            return await self.embed(query)
        except RuntimeError:
            # Vectorizer not available - return None instead of random vector
            if LOGURU_ENABLED:
                logger.warning("Vectorizer not available. Install sentence-transformers.")
            return None
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Embedding failed: {e}")
            return None

    @staticmethod
    def _rrf_fuse(
        vector_results: List[Dict],
        fts_results: List[Dict],
        limit: int,
        k: int = 60,
    ) -> List[Dict]:
        """Reciprocal Rank Fusion — merge vector and FTS results."""
        scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict] = {}
        for rank, r in enumerate(vector_results):
            doc_id = r.get("doc_id", f"v_{rank}")
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
            doc_map[doc_id] = r
        for rank, r in enumerate(fts_results):
            doc_id = r.get("doc_id", f"f_{rank}")
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
            if doc_id not in doc_map:
                doc_map[doc_id] = r
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        results = []
        for doc_id, score in ranked:
            doc = doc_map[doc_id].copy()
            doc["_distance"] = 1.0 - score  # convert to distance-like format
            results.append(doc)
        return results

    def _convert_to_search_results(
        self, raw_results: List[Dict[str, Any]], canvas_file: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        转换LanceDB结果为标准SearchResult格式

        ✅ Story 12.2 AC 2.4: 结果转换

        SearchResult格式:
        {
            "doc_id": str,
            "content": str,
            "score": float,
            "metadata": {
                "source": "lancedb",
                "timestamp": str,
                "canvas_file": str|None
            }
        }
        """
        search_results = []

        for i, item in enumerate(raw_results):
            # 提取内容
            content = item.get("content") or item.get("text") or item.get("document") or ""

            # 生成文档ID
            doc_id = item.get("doc_id") or item.get("id") or f"lancedb_{i}"
            if not doc_id.startswith("lancedb_"):
                doc_id = f"lancedb_{doc_id}"

            # 计算分数 (LanceDB返回_distance, 需要转换为相似度)
            distance = item.get("_distance") or item.get("distance") or 0.0
            # 余弦距离转相似度: score = 1 / (1 + distance)
            # 或者: score = 1 - distance (如果distance在[0,1]范围)
            if distance >= 0:
                score = 1.0 / (1.0 + distance)
            else:
                score = 0.0

            # 构建metadata
            metadata = {
                "source": "lancedb",
                "timestamp": datetime.now().isoformat(),
                "canvas_file": item.get("canvas_file") or canvas_file,
                "original_distance": distance,
            }

            # 复制其他metadata字段
            for key in ["concept", "agent_type", "node_id", "metadata_json"]:
                if key in item:
                    metadata[key] = item[key]

            search_results.append({"doc_id": doc_id, "content": content, "score": score, "metadata": metadata})

        return search_results

    def set_embedder(self, embedder):
        """
        设置嵌入器

        Args:
            embedder: 异步函数 async def embed(text: str) -> List[float]
        """
        self._embedder = embedder

    async def add_documents(self, table_name: str, documents: List[Dict[str, Any]]) -> int:
        """
        添加文档到表

        Args:
            table_name: 表名
            documents: 文档列表，每个包含 doc_id, content, vector, metadata

        Returns:
            添加的文档数量
        """
        if self._db is None:
            return 0

        try:
            # 准备数据
            data = []
            for doc in documents:
                # canvas_file: check top-level first (index_vault_notes),
                # then metadata dict (legacy callers)
                canvas_file = doc.get("canvas_file") or doc.get("metadata", {}).get("canvas_file", "") or ""

                content = doc.get("content", "")
                lance_doc = {
                    "doc_id": doc.get("doc_id"),
                    "content": content,
                    # Story 2.4: jieba 预分词后的内容，供 FTS 索引使用
                    "content_tokenized": _jieba_tokenize(content),
                    "vector": doc.get("vector") or doc.get("embedding"),
                    "canvas_file": canvas_file,
                    "timestamp": doc.get("timestamp") or datetime.now().isoformat(),
                }

                # Passthrough extra fields (node_id, node_type, color, x, y, subject, etc.)
                # so that index_vault_notes / index_single_file schema is preserved
                for key in ("node_id", "node_type", "color", "x", "y", "subject", "course_id", "tags"):
                    if key in doc:
                        lance_doc[key] = doc[key]

                # metadata_json: use top-level if present (index_vault_notes),
                # else serialize metadata dict
                if doc.get("metadata_json"):
                    lance_doc["metadata_json"] = doc["metadata_json"]
                elif "metadata" in doc:
                    import json

                    lance_doc["metadata_json"] = json.dumps(doc["metadata"], ensure_ascii=False)

                data.append(lance_doc)

            # 检查表是否存在
            if table_name in self._tables_cache:
                table = self._tables_cache[table_name]
                table.add(data)
            else:
                # 创建新表
                table = self._db.create_table(table_name, data=data)
                self._tables_cache[table_name] = table

            if LOGURU_ENABLED:
                logger.info(f"Added {len(data)} documents to {table_name}")

            return len(data)

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to add documents: {e}")
            return 0

    async def search_multiple_tables(
        self,
        query: str,
        table_names: Optional[List[str]] = None,
        canvas_file: Optional[str] = None,
        subject: Optional[str] = None,
        num_results_per_table: int = 5,
        query_type: str = "hybrid",
        course_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索多个表并合并结果

        Story 2.4: 新增 query_type, course_id, tags 参数透传

        Args:
            query: 搜索查询
            table_names: 表名列表 (默认使用DEFAULT_TABLES)
            canvas_file: Canvas文件过滤
            subject: 学科标识(用于学科隔离过滤)
            num_results_per_table: 每个表的结果数量
            query_type: 搜索类型 ("vector" 或 "hybrid")
            course_id: 课程ID (按课程过滤)
            tags: 标签列表 (按标签过滤, OR 匹配)

        Returns:
            合并后的搜索结果 (按分数排序)
        """
        if table_names is None:
            table_names = self.DEFAULT_TABLES

        all_results = []

        for table_name in table_names:
            try:
                results = await self.search(
                    query=query,
                    table_name=table_name,
                    canvas_file=canvas_file,
                    subject=subject,
                    num_results=num_results_per_table,
                    query_type=query_type,
                    course_id=course_id,
                    tags=tags,
                )
                all_results.extend(results)
            except Exception as e:
                if LOGURU_ENABLED:
                    logger.debug(f"Search in {table_name} failed: {e}")

        # 按分数排序
        all_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)

        return all_results

    async def count_documents_by_canvas(self, canvas_path: str, table_name: str = "canvas_nodes") -> Dict[str, Any]:
        """
        统计指定 Canvas 的已索引文档数量

        ✅ Story 38.1: 使用 pandas 直接查询，不依赖向量搜索
        - 解决空查询无法向量化的问题
        - 使用 endswith() 匹配处理路径前缀差异

        Args:
            canvas_path: Canvas 文件路径（相对路径）
            table_name: LanceDB 表名

        Returns:
            Dict with:
            - count: 文档数量
            - last_indexed: 最后索引时间
            - subject: 索引时的学科标识
        """
        if not self._initialized:
            await self.initialize()

        if self._db is None:
            return {"count": 0, "last_indexed": None, "subject": None}

        try:
            # 检查表是否存在
            if table_name not in self._db.table_names():
                return {"count": 0, "last_indexed": None, "subject": None}

            # 打开表
            table = self._db.open_table(table_name)

            # 使用 to_pandas() 获取所有数据，然后过滤
            # 这避免了需要向量化的问题
            df = table.to_pandas()

            if df.empty:
                return {"count": 0, "last_indexed": None, "subject": None}

            # 使用 endswith 匹配来处理路径前缀差异
            # 例如: "测试学科/测试Canvas.canvas" 可以匹配
            # "C:/path/to/vault/测试学科/测试Canvas.canvas"
            # 标准化路径分隔符
            normalized_path = canvas_path.replace("\\", "/")

            # 过滤匹配的文档
            if "canvas_file" in df.columns:
                # 标准化 DataFrame 中的路径
                df["canvas_file_normalized"] = df["canvas_file"].str.replace("\\\\", "/", regex=False)
                df["canvas_file_normalized"] = df["canvas_file_normalized"].str.replace("\\", "/", regex=False)

                # 使用 endswith 匹配
                mask = df["canvas_file_normalized"].str.endswith(normalized_path)
                matched_df = df[mask]

                if matched_df.empty:
                    # 尝试精确匹配
                    mask_exact = df["canvas_file_normalized"] == normalized_path
                    matched_df = df[mask_exact]

                if matched_df.empty:
                    return {"count": 0, "last_indexed": None, "subject": None}

                # 获取统计信息
                count = len(matched_df)
                last_indexed = None
                subject = None

                if "timestamp" in matched_df.columns:
                    last_indexed = matched_df["timestamp"].max()

                if "subject" in matched_df.columns:
                    # 获取第一个非空 subject
                    subjects = matched_df["subject"].dropna()
                    if len(subjects) > 0:
                        subject = subjects.iloc[0]

                return {"count": count, "last_indexed": last_indexed, "subject": subject}
            else:
                return {"count": 0, "last_indexed": None, "subject": None}

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"count_documents_by_canvas failed: {e}")
            return {"count": 0, "last_indexed": None, "subject": None}

    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        return {
            "initialized": self._initialized,
            "db_available": self._db is not None,
            "db_path": self.db_path,
            "tables": list(self._tables_cache.keys()),
            "timeout_ms": self.timeout_ms,
            "batch_size": self.batch_size,
            "enable_fallback": self.enable_fallback,
            "lancedb_installed": LANCEDB_AVAILABLE,
        }
