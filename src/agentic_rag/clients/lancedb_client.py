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
        try:
            return len(enc.encode(t))
        except ValueError:
            # tiktoken regex backtracking overflow on exotic content —
            # fall back to char-based estimate (1 token ≈ 4 chars for English,
            # ≈ 1.5 chars for Chinese; use conservative 2 chars/token)
            return len(t) // 2

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
        timeout_ms: int = 5000,  # Raised from 400ms: Ollama GPU embedding ~300ms + LanceDB search ~100ms
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
        """缓存表信息，并检查向量维度是否与当前模型匹配"""
        if self._db is None:
            return

        try:
            table_names = self._db.table_names()
            for name in table_names:
                try:
                    self._tables_cache[name] = self._db.open_table(name)
                except Exception:
                    pass

            # Story 2.3 Task 6: Auto-detect dimension mismatch on startup
            # Check vector tables against expected embedding_dim
            vector_tables = [t for t in self._tables_cache if t != self.FINGERPRINT_TABLE]
            for tname in vector_tables:
                self._check_and_fix_dimension_mismatch(tname, self.embedding_dim)

        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"Failed to cache tables: {e}")

    # =========================================================================
    # Story 2.7: File Fingerprint Infrastructure
    # =========================================================================

    FINGERPRINT_TABLE = "file_fingerprints"

    @staticmethod
    def _compute_file_hash(file_path: str) -> str:
        """
        Story 2.7 AC-1: Compute SHA-256 content hash of a file.

        Args:
            file_path: Absolute path to the file.

        Returns:
            Hex-encoded SHA-256 hash string.
        """
        import hashlib

        sha = hashlib.sha256()
        with open(file_path, "r", encoding="utf-8") as f:
            sha.update(f.read().encode("utf-8"))
        return sha.hexdigest()

    def _ensure_fingerprint_table(self):
        """
        Story 2.7 Task 1.1: Create or open the file_fingerprints table.

        Schema: file_path (str), content_hash (str), last_indexed (str), chunk_count (int)
        """
        if self._db is None:
            return

        if self.FINGERPRINT_TABLE in self._tables_cache:
            return

        try:
            existing_tables = self._db.table_names()
            if self.FINGERPRINT_TABLE in existing_tables:
                self._tables_cache[self.FINGERPRINT_TABLE] = self._db.open_table(self.FINGERPRINT_TABLE)
        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"[fingerprint] Error checking fingerprint table: {e}")

    def _get_all_fingerprints(self) -> Dict[str, str]:
        """
        Get all stored fingerprints as file_path -> content_hash mapping.

        Returns:
            Dict mapping file_path to content_hash.
        """
        self._ensure_fingerprint_table()

        if self.FINGERPRINT_TABLE not in self._tables_cache:
            # No fingerprint table yet — first run, all files are new
            empty_map: Dict[str, str] = {}
            return empty_map

        try:
            tbl = self._tables_cache[self.FINGERPRINT_TABLE]
            rows = tbl.to_pandas()
            if rows.empty:
                empty_map2: Dict[str, str] = {}
                return empty_map2
            return dict(zip(rows["file_path"], rows["content_hash"]))
        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"[fingerprint] Error reading fingerprints: {e}")
            empty_map3: Dict[str, str] = {}
            return empty_map3

    def _get_changed_files(self, vault_path: str, file_paths: List[str]) -> tuple:
        """
        Story 2.7 Task 1.3: Compare current files against stored fingerprints.

        Args:
            vault_path: Vault root directory for relative path computation.
            file_paths: List of absolute paths to current .md files.

        Returns:
            Tuple of (new_files, changed_files, deleted_files) — all as relative paths.
        """
        stored = self._get_all_fingerprints()

        # Build current hash map (relative path -> hash)
        current_hashes: Dict[str, str] = {}
        for fp in file_paths:
            rel = os.path.relpath(fp, vault_path).replace("\\", "/")
            try:
                h = self._compute_file_hash(fp)
                current_hashes[rel] = h
            except Exception as e:
                if LOGURU_ENABLED:
                    logger.debug(f"[fingerprint] Cannot hash {fp}: {e}")

        new_files: List[str] = []
        changed_files: List[str] = []
        deleted_files: List[str] = []

        # Detect new and changed
        for rel, h in current_hashes.items():
            if rel not in stored:
                new_files.append(rel)
            elif stored[rel] != h:
                changed_files.append(rel)

        # Detect deleted (in stored but not in current)
        current_rel_set = set(current_hashes.keys())
        for stored_rel in stored:
            if stored_rel not in current_rel_set:
                deleted_files.append(stored_rel)

        return new_files, changed_files, deleted_files

    def _update_fingerprint(self, file_path: str, content_hash: str, chunk_count: int):
        """
        Story 2.7 Task 1.4: Update fingerprint record using delete-before-insert.

        Args:
            file_path: Relative file path.
            content_hash: SHA-256 hash.
            chunk_count: Number of chunks indexed for this file.
        """
        if self._db is None:
            return

        record = {
            "file_path": file_path,
            "content_hash": content_hash,
            "last_indexed": datetime.now().isoformat(),
            "chunk_count": chunk_count,
        }

        try:
            if self.FINGERPRINT_TABLE in self._tables_cache:
                tbl = self._tables_cache[self.FINGERPRINT_TABLE]
                # Delete existing record for this file
                escaped = file_path.replace("'", "''")
                try:
                    tbl.delete(f"file_path = '{escaped}'")
                except Exception:
                    pass
                tbl.add([record])
            else:
                # Create table with first record
                tbl = self._db.create_table(self.FINGERPRINT_TABLE, data=[record])
                self._tables_cache[self.FINGERPRINT_TABLE] = tbl
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"[fingerprint] Failed to update fingerprint for {file_path}: {e}")

    def _remove_fingerprint(self, file_path: str):
        """
        Story 2.7 Task 1.5: Delete fingerprint record.

        Args:
            file_path: Relative file path.
        """
        if self.FINGERPRINT_TABLE not in self._tables_cache:
            return

        try:
            tbl = self._tables_cache[self.FINGERPRINT_TABLE]
            escaped = file_path.replace("'", "''")
            tbl.delete(f"file_path = '{escaped}'")
        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"[fingerprint] Failed to remove fingerprint for {file_path}: {e}")

    def _delete_file_chunks(self, table_name: str, file_path: str) -> int:
        """
        Story 2.7 AC-2: Delete all chunks for a file from a LanceDB table.

        Uses canvas_file field to match. Handles single-quote escaping for SQL.

        Args:
            table_name: LanceDB table name.
            file_path: Relative file path (value of canvas_file column).

        Returns:
            1 on success, 0 on failure.
        """
        if self._db is None:
            return 0

        try:
            if table_name in self._tables_cache:
                tbl = self._tables_cache[table_name]
            else:
                try:
                    tbl = self._db.open_table(table_name)
                    self._tables_cache[table_name] = tbl
                except Exception:
                    return 0

            escaped = file_path.replace("'", "''")
            tbl.delete(f"canvas_file = '{escaped}'")
            if LOGURU_ENABLED:
                logger.debug(f"[index] Deleted old chunks for '{file_path}' from '{table_name}'")
            return 1
        except Exception as e:
            if LOGURU_ENABLED:
                logger.warning(f"[index] Failed to delete chunks for '{file_path}': {e}")
            return 0

    async def rebuild_index(
        self,
        vault_path: str,
        table_name: str = "vault_notes",
        subject: str = "",
        max_tokens: int = 512,
        overlap_tokens: int = 50,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Story 2.7 AC-4: Full index rebuild — drop all data and re-index from scratch.

        Used for model migration or data recovery. Ignores all fingerprint caches.

        Args:
            vault_path: Vault root directory.
            table_name: Target LanceDB table name.
            subject: Subject tag for isolation.
            max_tokens: Chunk size in tokens.
            overlap_tokens: Overlap between chunks.
            progress_callback: Optional callable(current, total) for progress reporting.

        Returns:
            Dict with total_files, total_chunks, duration_ms.
        """
        start_time = time.perf_counter()

        if not self._initialized:
            await self.initialize()

        # Drop fingerprint table
        try:
            self._db.drop_table(self.FINGERPRINT_TABLE, ignore_missing=True)
            self._tables_cache.pop(self.FINGERPRINT_TABLE, None)
        except Exception:
            pass

        # Drop main table
        try:
            self._db.drop_table(table_name, ignore_missing=True)
            self._tables_cache.pop(table_name, None)
        except Exception:
            pass

        if LOGURU_ENABLED:
            logger.info(
                f"[REBUILD] Dropped tables '{table_name}' and '{self.FINGERPRINT_TABLE}', starting full rebuild"
            )

        # Re-index all files via index_vault_notes with force_rebuild
        total_chunks = await self.index_vault_notes(
            vault_path=vault_path,
            table_name=table_name,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
            subject=subject,
            force_rebuild=True,
            progress_callback=progress_callback,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Count files
        skip_dirs = [".obsidian", ".git", ".trash", "node_modules"]
        total_files = 0
        for _root, dirs, files in os.walk(vault_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            total_files += sum(1 for f in files if f.endswith(".md"))

        if LOGURU_ENABLED:
            logger.info(f"[REBUILD] Complete: {total_files} files, {total_chunks} chunks in {duration_ms:.0f}ms")

        return {
            "total_files": total_files,
            "total_chunks": total_chunks,
            "duration_ms": round(duration_ms),
        }

    # =========================================================================
    # Story 2.9: Image OCR Content Indexing
    # =========================================================================

    async def index_image_content(
        self,
        node_id: str,
        image_path: str,
        ocr_result: Dict[str, Any],
        table_name: str = "vault_notes",
        subject: str = "",
    ) -> int:
        """
        Story 2.9 AC-2: Index OCR-extracted image content via the text indexing pipeline.

        Combines OCR text + summary + concepts into indexable text,
        vectorizes with bge-m3, writes to LanceDB with source_type="image_ocr".
        Uses delete-before-insert by node_id.

        Args:
            node_id: Canvas node ID of the image.
            image_path: Path to the original image file.
            ocr_result: Structured OCR result dict with keys:
                text, content_type, summary, concepts.
            table_name: Target LanceDB table.
            subject: Subject tag for isolation.

        Returns:
            Number of chunks indexed.
        """
        import hashlib

        if not self._initialized:
            await self.initialize()

        await self._init_vectorizer()
        if self._vectorizer is None:
            if LOGURU_ENABLED:
                logger.warning("Vectorizer not available, skipping image content indexing")
            return 0

        # Build indexable text from OCR result
        text_parts = []
        ocr_text = ocr_result.get("text", "")
        if ocr_text:
            text_parts.append(ocr_text)
        summary = ocr_result.get("summary", "")
        if summary:
            text_parts.append(f"[摘要] {summary}")
        concepts = ocr_result.get("concepts", [])
        if concepts:
            text_parts.append(f"[核心概念] {', '.join(concepts)}")

        combined_text = "\n".join(text_parts)
        if not combined_text.strip():
            if LOGURU_ENABLED:
                logger.debug(f"[IMAGE-INDEX] No text content from OCR for node {node_id}")
            return 0

        # Vectorize
        try:
            vec_result = await self._vectorizer.vectorize_text(combined_text)
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"[IMAGE-INDEX] Vectorization failed for node {node_id}: {e}")
            return 0

        # Build document
        content_type = ocr_result.get("content_type", "text")
        chunk_id = hashlib.md5(f"image_ocr:{node_id}:{combined_text[:100]}".encode()).hexdigest()
        metadata = {
            "file_path": image_path,
            "source": "image_ocr",
            "source_type": "image_ocr",
            "node_id": node_id,
            "content_type": content_type,
            "subject": subject,
        }

        doc = {
            "doc_id": f"img_{chunk_id}",
            "content": combined_text,
            "vector": vec_result.vector,
            "canvas_file": image_path,
            "node_id": node_id,
            "node_type": "image_ocr",
            "color": "",
            "x": 0,
            "y": 0,
            "subject": subject,
            "source_type": "image_ocr",
            "timestamp": datetime.now().isoformat(),
            "metadata_json": json.dumps(metadata, ensure_ascii=False),
        }

        # Delete old image OCR data for this node
        if self._db is not None:
            try:
                if table_name in self._tables_cache:
                    tbl = self._tables_cache[table_name]
                else:
                    try:
                        tbl = self._db.open_table(table_name)
                        self._tables_cache[table_name] = tbl
                    except Exception:
                        tbl = None

                if tbl is not None:
                    escaped_node = node_id.replace("'", "''")
                    try:
                        tbl.delete(f"node_id = '{escaped_node}'")
                    except Exception:
                        pass
            except Exception:
                pass

        count = await self.add_documents(table_name, [doc])

        # Story 2.4: Rebuild FTS index for hybrid search support
        if count > 0:
            self._rebuild_fts_index(table_name)

        if LOGURU_ENABLED:
            logger.info(
                f"[IMAGE-INDEX] Indexed {count} chunks for node {node_id} "
                f"(text={len(ocr_text)} chars, type={content_type})"
            )

        return count

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

    async def _ollama_embed(self, text: str) -> Optional[List[float]]:
        """
        Embed text via Ollama API (GPU-accelerated).

        Uses the bge-m3 model loaded in the Ollama container with GPU passthrough.
        Returns None if Ollama is unavailable, allowing fallback to CPU vectorizer.
        """
        import aiohttp

        ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ollama_url}/api/embed",
                    json={"model": "bge-m3", "input": text},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embeddings = data.get("embeddings")
                        if embeddings and len(embeddings) > 0:
                            return embeddings[0]
                    if LOGURU_ENABLED:
                        logger.debug(f"Ollama embed returned status {resp.status}")
        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"Ollama embed unavailable: {e}")
        return None

    async def _ollama_embed_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Batch embed texts via Ollama API (GPU-accelerated).

        Ollama /api/embed supports batch input natively.
        Returns None if Ollama is unavailable.
        """
        import aiohttp

        ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ollama_url}/api/embed",
                    json={"model": "bge-m3", "input": texts},
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embeddings = data.get("embeddings")
                        if embeddings and len(embeddings) == len(texts):
                            return embeddings
                    if LOGURU_ENABLED:
                        logger.debug(f"Ollama batch embed returned status {resp.status}")
        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"Ollama batch embed unavailable: {e}")
        return None

    async def embed(self, text: str) -> List[float]:
        """
        文本向量化

        Story 2.3: 使用 bge-m3 生成 1024 维 Dense 向量
        优先使用 Ollama GPU embedding，失败时 fallback 到 sentence-transformers CPU。

        Args:
            text: 要向量化的文本

        Returns:
            List[float]: embedding向量 (1024维, bge-m3 Dense)

        Raises:
            RuntimeError: 如果所有 embedding 方式都失败
        """
        # Try Ollama GPU first
        result = await self._ollama_embed(text)
        if result is not None:
            return result

        # Fallback to CPU vectorizer
        await self._init_vectorizer()

        if self._vectorizer is None:
            raise RuntimeError(
                "Vectorizer not available. Neither Ollama nor sentence-transformers is working."
            )

        vec_result = await self._vectorizer.vectorize_text(text)
        return vec_result.vector

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

        # Story 2.4: Rebuild FTS index on content_tokenized for hybrid search support
        if count > 0:
            self._rebuild_fts_index(table_name)

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
        force_rebuild: bool = False,
        progress_callback=None,
    ) -> int:
        """
        Story 2.7: Fingerprint-driven incremental vault indexing.

        Scans vault .md files, compares SHA-256 content hashes against stored
        fingerprints, and only re-indexes new/changed files. Deleted files are
        cleaned up automatically.

        When force_rebuild=True (or on first run), all files are indexed.

        Args:
            vault_path: Vault root directory path.
            skip_dirs: Directories to skip.
            table_name: LanceDB table name.
            max_tokens: Chunk size in tokens (tiktoken cl100k_base).
            overlap_tokens: Token overlap between chunks.
            subject: Subject tag for isolation.
            force_rebuild: If True, skip fingerprint comparison and index all files.
            progress_callback: Optional callable(current, total) for progress.

        Returns:
            int: Total number of chunks indexed.
        """
        index_start = time.perf_counter()

        if not self._initialized:
            await self.initialize()

        # Try CPU vectorizer init (may fail in Docker — Ollama GPU is primary path)
        await self._init_vectorizer()
        # Note: _vectorizer may be None here, but Ollama GPU batch path at
        # _ollama_embed_batch() does not require it. Only bail out if BOTH
        # Ollama and vectorizer are unavailable (checked per-file below).

        if skip_dirs is None:
            skip_dirs = [".obsidian", ".git", ".trash", "node_modules"]

        # Scan all .md files
        md_files: List[str] = []
        for root, dirs, files in os.walk(vault_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for f in files:
                if f.endswith(".md"):
                    md_files.append(os.path.join(root, f))

        if not md_files:
            if LOGURU_ENABLED:
                logger.info(f"No .md files found in {vault_path}")
            return 0

        total_scanned = len(md_files)

        # Story 2.7 AC-1: Fingerprint-based change detection
        if force_rebuild:
            # Force: treat all files as new
            new_files_rel = [os.path.relpath(fp, vault_path).replace("\\", "/") for fp in md_files]
            changed_files_rel: List[str] = []
            deleted_files_rel: List[str] = []
            files_to_index = md_files
        else:
            new_files_rel, changed_files_rel, deleted_files_rel = self._get_changed_files(vault_path, md_files)
            # Build abs paths for files that need indexing
            files_to_index_rel = set(new_files_rel) | set(changed_files_rel)
            files_to_index = [
                fp for fp in md_files if os.path.relpath(fp, vault_path).replace("\\", "/") in files_to_index_rel
            ]

        skipped = total_scanned - len(files_to_index) - len(deleted_files_rel)

        if LOGURU_ENABLED:
            logger.info(
                f"[INDEX] Scanned {total_scanned} files: {len(new_files_rel)} new, "
                f"{len(changed_files_rel)} changed, {len(deleted_files_rel)} deleted, "
                f"{skipped} skipped"
            )

        # Story 2.7 AC-6: Clean up deleted files
        for del_rel in deleted_files_rel:
            self._delete_file_chunks(table_name, del_rel)
            self._remove_fingerprint(del_rel)
            if LOGURU_ENABLED:
                logger.debug(f"[INDEX] Cleaned deleted file: {del_rel}")

        if not files_to_index:
            # Nothing to index — but still rebuild FTS if deletions happened
            if deleted_files_rel:
                self._rebuild_fts_index(table_name)

            duration_ms = (time.perf_counter() - index_start) * 1000
            if LOGURU_ENABLED:
                logger.info(f"[INDEX] No files to index, duration={duration_ms:.0f}ms")
            return 0

        # Process files: chunk + vectorize + delete-before-insert
        import hashlib

        total_chunks_indexed = 0
        for file_idx, md_file in enumerate(files_to_index):
            if progress_callback:
                progress_callback(file_idx + 1, len(files_to_index))

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

            if not chunks:
                continue

            # Batch vectorize chunks for this file (Ollama GPU → CPU fallback)
            texts = [c["content"] for c in chunks]
            ollama_vectors = await self._ollama_embed_batch(texts)
            if ollama_vectors is not None:
                # Wrap in namedtuple-like objects for compatibility
                from types import SimpleNamespace
                vectorized = [SimpleNamespace(vector=v) for v in ollama_vectors]
            else:
                if self._vectorizer is None:
                    if LOGURU_ENABLED:
                        logger.error(f"Both Ollama and CPU vectorizer unavailable, skipping {rel_path}")
                    continue
                try:
                    vectorized = await self._vectorizer.batch_vectorize(texts)
                except Exception as e:
                    if LOGURU_ENABLED:
                        logger.error(f"Vectorization failed for {rel_path}: {e}")
                    continue

            # Build documents
            documents = []
            for chunk, vec_result in zip(chunks, vectorized):
                chunk_id = hashlib.md5(
                    f"{chunk['file_path']}:{chunk.get('heading', '')}:{chunk['content'][:100]}".encode()
                ).hexdigest()

                metadata = {
                    "file_path": chunk["file_path"],
                    "heading": chunk.get("heading", ""),
                    "heading_path": chunk.get("heading_path", []),
                    "line_start": chunk.get("line_start"),
                    "line_end": chunk.get("line_end"),
                    "source": "vault_note",
                    "subject": subject,
                    "source_type": (
                        "video_transcript" if LanceDBClient._is_video_transcript(chunk["file_path"]) else "note"
                    ),
                    # Story 2.8: Frontmatter metadata
                    "course": chunk.get("course", ""),
                    "tags_str": chunk.get("tags_str", ""),
                    "category": chunk.get("category", ""),
                }

                if LanceDBClient._is_video_transcript(chunk["file_path"]):
                    ts_info = LanceDBClient._extract_timestamps_from_section(chunk.get("heading", ""), chunk["content"])
                    metadata.update(ts_info)

                doc = {
                    "doc_id": f"vault_{chunk_id}",
                    "content": chunk["content"],
                    "vector": vec_result.vector,
                    "canvas_file": chunk["file_path"],
                    "node_id": "",
                    "node_type": "vault_note",
                    "color": "",
                    "x": 0,
                    "y": 0,
                    "subject": subject or "",
                    # Story 2.8: Frontmatter columns
                    "course": chunk.get("course", ""),
                    "tags_str": chunk.get("tags_str", ""),
                    "category": chunk.get("category", ""),
                    "timestamp": datetime.now().isoformat(),
                    "metadata_json": json.dumps(metadata, ensure_ascii=False),
                }
                documents.append(doc)

            # Story 2.7 AC-2: delete-before-insert
            self._delete_file_chunks(table_name, rel_path)

            # Insert new chunks
            chunk_count = await self.add_documents(table_name, documents)
            total_chunks_indexed += chunk_count

            # Update fingerprint — use in-memory content to avoid TOCTOU race
            # (file may have changed on disk between read and hash)
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            self._update_fingerprint(rel_path, content_hash, chunk_count)

            if LOGURU_ENABLED:
                logger.debug(f"[INDEX] Indexed {chunk_count} chunks from {rel_path}")

        # Story 2.7 AC-5: Rebuild FTS index after incremental update
        self._rebuild_fts_index(table_name)

        duration_ms = (time.perf_counter() - index_start) * 1000
        if LOGURU_ENABLED:
            logger.info(
                f"[INDEX] Complete: {total_chunks_indexed} chunks from "
                f"{len(files_to_index)} files in {duration_ms:.0f}ms"
            )

        return total_chunks_indexed

    def _rebuild_fts_index(self, table_name: str):
        """
        Story 2.7 AC-5: Rebuild FTS index on content_tokenized after incremental update.
        """
        try:
            tbl = self._db.open_table(table_name)
            tbl.create_fts_index("content_tokenized", replace=True)
            if LOGURU_ENABLED:
                logger.info(
                    f"[INDEX] Rebuilt FTS index on '{table_name}.content_tokenized' (jieba_available={JIEBA_AVAILABLE})"
                )
        except Exception as e:
            if LOGURU_ENABLED:
                logger.warning(f"[INDEX] FTS index rebuild failed: {e}")

    async def index_single_file(
        self,
        file_path: str,
        table_name: str = "vault_notes",
        subject: str = "",
        vault_path: Optional[str] = None,
    ) -> int:
        """
        Story 2.7: Index a single .md file with delete-before-insert dedup + fingerprint.

        Story 2.7 AC-7: Uses os.path.relpath(file_path, vault_path) to preserve
        full directory structure (fixes CRITICAL C8 path loss).

        Args:
            file_path: Absolute path to the .md file.
            table_name: Target table name.
            subject: Optional subject tag.
            vault_path: Vault root directory for computing relative path.
                        If None, falls back to parent directory of file_path.

        Returns:
            Number of chunks indexed.
        """
        import hashlib

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

        # Story 2.7 AC-7: Use relpath to preserve directory structure
        if vault_path:
            rel_path = os.path.relpath(file_path, vault_path).replace("\\", "/")
        else:
            # H2 fix: vault_path=None fallback — use file's parent directory
            # instead of os.path.relpath(file, dirname(file)) which always yields
            # just the filename, losing all directory structure (re-introducing C8 bug).
            vault_path = os.path.dirname(file_path)
            rel_path = os.path.basename(file_path)
            if LOGURU_ENABLED:
                logger.warning(
                    f"[INDEX] vault_path not provided for index_single_file({file_path}), "
                    f"falling back to parent dir: {vault_path}"
                )

        # Check fingerprint — skip if unchanged
        # H1 fix: Compute hash from in-memory content (already read above)
        # to avoid TOCTOU race where file changes between read and hash.
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        stored_fps = self._get_all_fingerprints()
        if rel_path in stored_fps and stored_fps[rel_path] == content_hash:
            if LOGURU_ENABLED:
                logger.debug(f"[INDEX] Skipping unchanged file: {rel_path}")
            return 0

        chunks = self._split_md_by_heading(content, rel_path)

        if not chunks:
            return 0

        # Initialize vectorizer
        await self._init_vectorizer()
        if not self._vectorizer:
            if LOGURU_ENABLED:
                logger.error("Vectorizer not available, cannot index single file")
            return 0

        # Batch vectorize
        texts = [c["content"] for c in chunks]
        vectorized = await self._vectorizer.batch_vectorize(texts)

        if len(vectorized) != len(chunks):
            if LOGURU_ENABLED:
                logger.error(f"Vectorization mismatch: {len(chunks)} chunks vs {len(vectorized)} vectors")
            return 0

        # Build documents
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
                "heading_path": chunk.get("heading_path", []),
                "line_start": chunk.get("line_start", 0),
                "line_end": chunk.get("line_end", 0),
                "source": "vault_note",
                "subject": subject,
                "source_type": ("video_transcript" if LanceDBClient._is_video_transcript(file_path) else "note"),
                # Story 2.8: Frontmatter metadata
                "course": chunk.get("course", ""),
                "tags_str": chunk.get("tags_str", ""),
                "category": chunk.get("category", ""),
            }

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
                # Story 2.8: Frontmatter columns
                "course": chunk.get("course", ""),
                "tags_str": chunk.get("tags_str", ""),
                "category": chunk.get("category", ""),
                "timestamp": datetime.now().isoformat(),
                "metadata_json": json.dumps(metadata, ensure_ascii=False),
            }
            documents.append(doc)

        # Story 2.7 AC-2: delete-before-insert
        self._delete_file_chunks(table_name, rel_path)

        count = await self.add_documents(table_name, documents)

        # Update fingerprint
        self._update_fingerprint(rel_path, content_hash, count)

        # Rebuild FTS index
        self._rebuild_fts_index(table_name)

        if LOGURU_ENABLED:
            logger.info(f"[INDEX] Indexed {count} chunks from {rel_path} (delete-before-insert)")

        return count

    # =========================================================================
    # Story 2.8: Frontmatter Parsing + Wiki-links + Neighbor Expansion
    # =========================================================================

    @staticmethod
    def _parse_frontmatter(content: str) -> tuple:
        """
        Story 2.8 AC-1: Parse YAML Frontmatter from markdown content.

        Returns:
            Tuple of (frontmatter_dict, body_content_without_frontmatter).
            On parse error, returns empty dict + original body with warning log.
        """
        import yaml

        fm: Dict[str, Any] = {}
        body = content

        if not content.startswith("---"):
            return fm, body

        try:
            end_idx = content.find("---", 3)
            if end_idx == -1:
                return fm, body
            yaml_str = content[3:end_idx].strip()
            parsed = yaml.safe_load(yaml_str)
            if isinstance(parsed, dict):
                fm = parsed
            body = content[end_idx + 3 :].lstrip("\n")
        except Exception:
            import logging

            logging.getLogger(__name__).warning(
                "[frontmatter] Failed to parse YAML frontmatter, skipping metadata extraction"
            )
        return fm, body

    @staticmethod
    def _extract_wiki_links(content: str) -> List[str]:
        """
        Story 2.8 AC-4: Extract wiki-link targets from markdown content.
        Handles [[filename]] and [[filename|display text]] patterns.

        Returns:
            List of unique linked file names (without extension).
        """
        import re

        pattern = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
        matches = pattern.findall(content)
        seen: set = set()
        result: List[str] = []
        for m in matches:
            m_clean = m.strip()
            if m_clean and m_clean not in seen:
                seen.add(m_clean)
                result.append(m_clean)
        return result

    async def expand_neighbors(
        self,
        results: List[Dict[str, Any]],
        table_name: str = "vault_notes",
        max_neighbors: int = 5,
        score_decay: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Story 2.8 AC-4: 1-hop wiki-link neighbor expansion.

        For each search result, extract wiki-links and fetch chunks from linked files.
        Neighbor chunks get decayed scores and source_type="neighbor_expansion".
        """
        if not results:
            return results

        linked_files: List[str] = []
        seen_links: set = set()
        for r in results:
            content = r.get("content", "")
            links = self._extract_wiki_links(content)
            for link in links:
                if link not in seen_links:
                    seen_links.add(link)
                    linked_files.append(link)
                    if len(linked_files) >= max_neighbors:
                        break
            if len(linked_files) >= max_neighbors:
                break

        if not linked_files:
            return results

        neighbor_results: List[Dict[str, Any]] = []
        if self._db is None:
            return results

        try:
            if table_name in self._tables_cache:
                tbl = self._tables_cache[table_name]
            else:
                tbl = self._db.open_table(table_name)
                self._tables_cache[table_name] = tbl

            # Collect doc_ids already in results to avoid duplicates
            existing_doc_ids: set = set()
            for r in results:
                existing_doc_ids.add(r.get("doc_id", ""))

            for link_name in linked_files:
                try:
                    escaped_link = self._escape_like(link_name)
                    where_clause = f"canvas_file LIKE '%{escaped_link}%'"
                    rows = tbl.search().where(where_clause).limit(3).to_list()
                    for row in rows:
                        neighbor_doc = dict(row)
                        doc_id = neighbor_doc.get("doc_id", "")
                        if doc_id in existing_doc_ids:
                            continue
                        existing_doc_ids.add(doc_id)
                        orig_score = neighbor_doc.get("_distance", 0.5)
                        decayed_distance = orig_score / score_decay if score_decay > 0 else orig_score
                        neighbor_doc["_distance"] = decayed_distance
                        neighbor_doc["_source_type"] = "neighbor_expansion"
                        neighbor_results.append(neighbor_doc)
                except Exception:
                    continue
        except Exception:
            pass

        if neighbor_results:
            formatted = self._convert_to_search_results(neighbor_results)
            for fr in formatted:
                fr["metadata"]["source_type"] = "neighbor_expansion"
            return list(results) + formatted

        return results

    @staticmethod
    def _compute_tag_jaccard(tags_a: set, tags_b: set) -> float:
        """Story 2.8 AC-5: Compute Jaccard similarity between two tag sets."""
        if not tags_a or not tags_b:
            return 0.0
        intersection = len(tags_a & tags_b)
        union = len(tags_a | tags_b)
        return intersection / union if union > 0 else 0.0

    async def find_related_courses(
        self, current_course: str, table_name: str = "vault_notes", threshold: float = 0.3
    ) -> List[str]:
        """
        Story 2.8 AC-5: Find courses with Tag Jaccard similarity above threshold.
        Scans the table for distinct courses and computes Jaccard similarity
        with the current course's tag set.
        """
        if self._db is None:
            return list()

        try:
            if table_name not in self._tables_cache:
                self._tables_cache[table_name] = self._db.open_table(table_name)
            tbl = self._tables_cache[table_name]
            # Story 2-8 H5: Only select course and tags_str columns to avoid
            # loading full content/vector columns into memory.
            df = tbl.to_pandas(columns=["course", "tags_str"])

            if "course" not in df.columns or "tags_str" not in df.columns:
                return list()

            course_tags: Dict[str, set] = {}
            for _, row in df.iterrows():
                course = row.get("course", "")
                tags_str = row.get("tags_str", "")
                if not course:
                    continue
                if course not in course_tags:
                    course_tags[course] = set()
                if tags_str:
                    course_tags[course].update(t.strip() for t in tags_str.split(",") if t.strip())

            current_tags = course_tags.get(current_course, set())
            if not current_tags:
                return list()

            related: List[str] = []
            for other_course, other_tags in course_tags.items():
                if other_course == current_course:
                    continue
                jaccard = self._compute_tag_jaccard(current_tags, other_tags)
                if jaccard > threshold:
                    related.append(other_course)

            return related
        except Exception:
            return list()

    async def progressive_scope_search(
        self,
        query: str,
        course_id: str,
        table_name: str = "vault_notes",
        num_results: int = 10,
        min_results_threshold: int = 5,
        query_type: str = "hybrid",
        subject: Optional[str] = None,
        canvas_file: Optional[str] = None,
        tag_jaccard_bridge_enabled: bool = False,
        tag_jaccard_threshold: float = 0.3,
        category: Optional[str] = None,
        rrf_k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Story 2.8 AC-3: Progressive 4-stage cascading scope search.

        When searching within a specific course, if insufficient results are found,
        automatically expands to broader scopes:
          Stage 1: Same course (course = course_id)
          Stage 2: Related courses (Tag Jaccard similarity > threshold)
          Stage 3: Same category (category column match)
          Stage 4: Full library (no filter)

        Each result is tagged with scope_level (1-4) in metadata.
        Expansion stops when results >= min_results_threshold.

        Args:
            query: Search query text.
            course_id: Current course ID for initial scope.
            table_name: LanceDB table name.
            num_results: Target number of results.
            min_results_threshold: Stop expanding when this many results found.
            query_type: Search type ("vector" or "hybrid").
            subject: Optional subject filter.
            canvas_file: Optional canvas file filter.
            tag_jaccard_bridge_enabled: Whether to use Tag Jaccard for stage 2.
            tag_jaccard_threshold: Jaccard similarity threshold for related courses.
            category: Optional category for stage 3 filtering.
            rrf_k: RRF fusion k parameter (Story 2.11 configurable, default 60).

        Returns:
            List of search results with scope_level in metadata.
        """
        all_results: List[Dict[str, Any]] = []  # noqa: C408
        seen_doc_ids: set = set()

        def _tag_and_collect(results: List[Dict[str, Any]], scope: int) -> int:
            """Tag results with scope_level and collect unique ones."""
            added = 0
            for r in results:
                doc_id = r.get("doc_id", "")
                if doc_id in seen_doc_ids:
                    continue
                seen_doc_ids.add(doc_id)
                r.setdefault("metadata", {})["scope_level"] = scope
                all_results.append(r)
                added += 1
            return added

        # Stage 1: Same course
        stage1 = await self.search(
            query=query,
            table_name=table_name,
            num_results=num_results,
            query_type=query_type,
            course_id=course_id,
            subject=subject,
            canvas_file=canvas_file,
            rrf_k=rrf_k,
        )
        _tag_and_collect(stage1, scope=1)

        if len(all_results) >= min_results_threshold:
            if LOGURU_ENABLED:
                logger.debug(f"[progressive] Stage 1 sufficient: {len(all_results)} results for course={course_id}")
            return all_results[:num_results]

        # Stage 2: Related courses via Tag Jaccard
        if tag_jaccard_bridge_enabled and course_id:
            related_courses = await self.find_related_courses(
                current_course=course_id,
                table_name=table_name,
                threshold=tag_jaccard_threshold,
            )
            for related_course in related_courses:
                if len(all_results) >= min_results_threshold:
                    break
                stage2 = await self.search(
                    query=query,
                    table_name=table_name,
                    num_results=num_results,
                    query_type=query_type,
                    course_id=related_course,
                    subject=subject,
                    canvas_file=canvas_file,
                    rrf_k=rrf_k,
                )
                _tag_and_collect(stage2, scope=2)

            if LOGURU_ENABLED:
                logger.debug(
                    f"[progressive] Stage 2 done: {len(all_results)} results (related_courses={related_courses})"
                )

            if len(all_results) >= min_results_threshold:
                return all_results[:num_results]

        # Stage 3: Same category
        if category:
            stage3 = await self._search_by_category(
                query=query,
                category=category,
                table_name=table_name,
                num_results=num_results,
                query_type=query_type,
                subject=subject,
                rrf_k=rrf_k,
            )
            _tag_and_collect(stage3, scope=3)

            if LOGURU_ENABLED:
                logger.debug(f"[progressive] Stage 3 done: {len(all_results)} results (category={category})")

            if len(all_results) >= min_results_threshold:
                return all_results[:num_results]

        # Stage 4: Full library (no course/category filter)
        stage4 = await self.search(
            query=query,
            table_name=table_name,
            num_results=num_results,
            query_type=query_type,
            subject=subject,
            canvas_file=canvas_file,
            rrf_k=rrf_k,
        )
        _tag_and_collect(stage4, scope=4)

        if LOGURU_ENABLED:
            logger.debug(f"[progressive] Stage 4 done: {len(all_results)} total results")

        return all_results[:num_results]

    async def _search_by_category(
        self,
        query: str,
        category: str,
        table_name: str = "vault_notes",
        num_results: int = 10,
        query_type: str = "hybrid",
        subject: Optional[str] = None,
        rrf_k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Story 2.8 AC-3 Stage 3: Search by category column.

        Uses a WHERE clause on the 'category' column for pre-filtering.

        Args:
            query: Search query text.
            category: Category value to filter on.
            table_name: LanceDB table name.
            num_results: Number of results to return.
            query_type: Search type.
            subject: Optional subject filter.
            rrf_k: RRF fusion k parameter (Story 2.11 configurable, default 60).

        Returns:
            List of search results filtered by category.
        """
        if self._db is None:
            return self._convert_to_search_results([])

        try:
            if table_name in self._tables_cache:
                table = self._tables_cache[table_name]
            else:
                table = self._db.open_table(table_name)
                self._tables_cache[table_name] = table
        except Exception:
            return self._convert_to_search_results([])

        # Build where clauses: category filter + optional subject
        clauses: List[str] = [f"category = '{self._escape_sql(category)}'"]
        if subject:
            clauses.append(f"subject = '{self._escape_sql(subject)}'")

        all_raw: List[Dict[str, Any]] = []  # noqa: C408

        if query_type == "hybrid" and isinstance(query, str):
            query_vector = await self._get_query_vector(query)
            vector_results: List[Dict] = []  # noqa: C408
            fts_results: List[Dict] = []  # noqa: C408

            if query_vector is not None:
                try:
                    vq = table.search(query_vector).limit(num_results * 2)
                    vq = self._apply_where_clauses(vq, clauses)
                    vector_results = vq.to_list()
                except Exception:
                    pass

            try:
                tokenized_query = _jieba_tokenize(query)
                fq = table.search(tokenized_query, query_type="fts").limit(num_results * 2)
                fq = self._apply_where_clauses(fq, clauses)
                fts_results = fq.to_list()
            except Exception:
                pass

            if vector_results or fts_results:
                all_raw = self._rrf_fuse(vector_results, fts_results, num_results, k=rrf_k)
                return self._convert_to_search_results(all_raw)

        # Fallback to vector search
        query_vector = await self._get_query_vector(query)
        if query_vector is not None:
            try:
                sq = table.search(query_vector).limit(num_results)
                sq = self._apply_where_clauses(sq, clauses)
                all_raw = sq.to_list()
            except Exception:
                pass

        return self._convert_to_search_results(all_raw)

    @staticmethod
    def _split_md_by_heading(
        content: str, file_path: str, max_tokens: int = 512, overlap_tokens: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Story 2.3+2.8: 按 Markdown heading 分段文本 + Frontmatter 解析

        一级切分按 H1-H4 heading，二级切分由 _chunk_text() 按句子边界+原子保护。
        每个 chunk 的 content 前缀注入面包屑路径（文档名 > h1 > h2 > h3），
        heading_path 数组保存在 chunk dict 中供 metadata 使用。
        Story 2.8: 解析 Frontmatter 提取 course/tags/category。

        Args:
            content: Markdown 文件内容
            file_path: 文件相对路径
            max_tokens: 每段目标 token 数（默认 512）
            overlap_tokens: 段落重叠 token 数（默认 50）

        Returns:
            List[Dict]: [{"file_path", "heading", "content", "heading_path",
                          "line_start", "line_end", "course", "tags_str", "category"}]
        """
        import re

        # Story 2.8: Parse frontmatter before chunking
        frontmatter, body = LanceDBClient._parse_frontmatter(content)
        fm_course = str(frontmatter.get("course", ""))
        fm_tags_raw = frontmatter.get("tags", [])
        if isinstance(fm_tags_raw, list):
            fm_tags_str = ",".join(str(t) for t in fm_tags_raw)
        else:
            fm_tags_str = str(fm_tags_raw)
        fm_category = str(frontmatter.get("category", ""))

        heading_pattern = re.compile(r"^(#{1,4})\s+(.+)$")
        chunks = []
        # Use body (frontmatter stripped) for chunking
        lines = body.split("\n")

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
                        # Story 2.8: Frontmatter metadata per chunk
                        "course": fm_course,
                        "tags_str": fm_tags_str,
                        "category": fm_category,
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
        rrf_k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        向量搜索

        ✅ Story 12.2 AC 2.2: 向量检索接口
        ✅ Story 12.2 AC 2.3: P95 < 400ms
        ✅ Story 12.2 AC 2.4: 结果转换
        ✅ Story 2.4: Hybrid 为默认模式 + 课程/标签过滤

        Hybrid search strategy (Story 2.4):
        - Dense branch: bge-m3 1024d cosine similarity
        - FTS branch: Tantivy FTS on jieba-tokenized content (content_tokenized column)
        - Fusion: Reciprocal Rank Fusion (RRF, k=60)
        - Degradation: FTS unavailable → Dense-only; both fail → empty results
        - Note: FTS+jieba serves as sparse vector substitute (LanceDB has no native
          sparse vector column; Tantivy BM25 provides equivalent term-matching capability)

        Args:
            query: 搜索查询 (文本或向量)
            table_name: 表名
            canvas_file: Canvas文件路径(用于过滤)
            subject: 学科标识(用于学科隔离过滤)
            num_results: 返回结果数量
            metric: 距离度量 ("cosine" 或 "L2")
            query_type: 搜索类型 ("vector" 或 "hybrid"). hybrid使用向量+FTS+RRF融合
            course_id: 课程ID (maps to 'course' column, 用于按课程过滤搜索范围)
            tags: 标签列表 (maps to 'tags_str' column, 用于按标签过滤, OR 匹配)
            rrf_k: RRF fusion k parameter (Story 2.11 configurable, default 60)

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
                    rrf_k=rrf_k,
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

    @staticmethod
    def _escape_sql(value: str) -> str:
        """Escape single quotes for SQL WHERE clauses to prevent injection."""
        return value.replace("'", "''")

    @staticmethod
    def _escape_like(value: str) -> str:
        """
        Story 2-8 H4: Escape LIKE wildcards (% and _) in addition to single quotes.

        When a value is used inside a LIKE pattern, literal '%' and '_' characters
        must be escaped to prevent unintended wildcard matching.
        """
        escaped = value.replace("'", "''")
        escaped = escaped.replace("%", "\\%")
        escaped = escaped.replace("_", "\\_")
        return escaped

    def _build_where_filters(
        self,
        canvas_file: Optional[str] = None,
        subject: Optional[str] = None,
        course_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Story 2.4 AC-5: Build SQL WHERE filter clauses for LanceDB queries.

        Supports canvas_file, subject, course_id (maps to 'course' column),
        and tags (maps to 'tags_str' column, OR matching via LIKE).
        Returns list of SQL clause strings to apply via .where().

        Column mapping:
        - course_id param → 'course' column (set by index_vault_notes from frontmatter)
        - tags param → 'tags_str' column (comma-separated tags from frontmatter)
        """
        clauses: List[str] = []
        if canvas_file:
            clauses.append(f"canvas_file = '{self._escape_sql(canvas_file)}'")
        if subject:
            clauses.append(f"subject = '{self._escape_sql(subject)}'")
        if course_id:
            clauses.append(f"course = '{self._escape_sql(course_id)}'")
        if tags:
            # Story 2-8 H4: Use _escape_like for LIKE patterns to escape % and _
            tag_conditions = " OR ".join(f"tags_str LIKE '%{self._escape_like(tag)}%'" for tag in tags)
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
        rrf_k: int = 60,
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
            # Serves as sparse search substitute (LanceDB has no native sparse vector
            # column type; Tantivy FTS + jieba provides equivalent Chinese retrieval).
            try:
                tokenized_query = _jieba_tokenize(query)
                if LOGURU_ENABLED:
                    logger.debug(f"[search] FTS jieba tokenized: '{query[:40]}' -> '{tokenized_query[:60]}'")
                fq = table.search(tokenized_query, query_type="fts").limit(num_results * 2)
                fq = self._apply_where_clauses(fq, where_clauses)
                fts_results = fq.to_list()
            except Exception as e:
                # FTS unavailable (no index yet, no content_tokenized column, etc.)
                # Hybrid degrades to Dense-only — still returns results via vector branch
                if LOGURU_ENABLED:
                    logger.warning(f"[search] FTS branch unavailable, degrading to Dense-only: {e}")

            # Story 2.4 AC-4: RRF fusion with single-path degradation
            # When only one branch has results, RRF still works correctly
            # (single-source ranking = original rank order)
            if vector_results or fts_results:
                all_raw = self._rrf_fuse(vector_results, fts_results, num_results, k=rrf_k)
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
            for key in [
                "concept",
                "agent_type",
                "node_id",
                "metadata_json",
                # Story 2.8: Frontmatter / scope metadata
                "course",
                "tags_str",
                "category",
                # Story 2.9: Image OCR source type
                "source_type",
                # Story 2.8: Neighbor expansion marker
                "_source_type",
            ]:
                if key in item:
                    metadata[key] = item[key]

            # Story 2.8/2.9: Propagate source_type to top-level metadata
            if "_source_type" in item:
                metadata["source_type"] = item["_source_type"]
            elif "source_type" in item:
                metadata["source_type"] = item["source_type"]

            search_results.append({"doc_id": doc_id, "content": content, "score": score, "metadata": metadata})

        return search_results

    def set_embedder(self, embedder):
        """
        设置嵌入器

        Args:
            embedder: 异步函数 async def embed(text: str) -> List[float]
        """
        self._embedder = embedder

    def _check_and_fix_dimension_mismatch(self, table_name: str, new_vector_dim: int) -> bool:
        """
        Story 2.3 Task 6: Detect vector dimension mismatch and auto drop+recreate.

        When migrating from 384d (old model) to 1024d (bge-m3), existing tables
        will have vectors of the wrong dimension. This method inspects the first
        row of an existing table, compares its vector dimension against the new
        expected dimension, and drops the table if mismatched.

        Args:
            table_name: LanceDB table name.
            new_vector_dim: Expected vector dimension (e.g. 1024 for bge-m3).

        Returns:
            True if the table was dropped due to mismatch (caller should create new).
            False if dimensions match or table doesn't exist.
        """
        if self._db is None:
            return False

        if table_name not in self._tables_cache:
            return False

        try:
            tbl = self._tables_cache[table_name]
            # Sample first row to inspect vector dimension
            rows = tbl.head(1).to_pydict()
            vectors = rows.get("vector", [])
            if not vectors or len(vectors) == 0:
                return False

            existing_dim = len(vectors[0])
            if existing_dim == new_vector_dim:
                return False

            # Dimension mismatch detected — drop table
            if LOGURU_ENABLED:
                logger.warning(
                    f"[SCHEMA] Vector dimension mismatch in '{table_name}': "
                    f"existing={existing_dim}, expected={new_vector_dim}. "
                    f"Dropping table for recreation with correct dimensions."
                )

            self._db.drop_table(table_name, ignore_missing=True)
            self._tables_cache.pop(table_name, None)
            return True

        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"[SCHEMA] Dimension check failed for '{table_name}': {e}")
            return False

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
                for key in (
                    "node_id",
                    "node_type",
                    "color",
                    "x",
                    "y",
                    "subject",
                    "course_id",
                    "tags",
                    # Story 2.8: Frontmatter metadata columns
                    "course",
                    "tags_str",
                    "category",
                    # Story 2.9: Image OCR source type
                    "source_type",
                ):
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

            # Story 2.3 Task 6: Check vector dimension mismatch before insert
            if data and table_name in self._tables_cache:
                sample_vector = data[0].get("vector")
                if sample_vector is not None:
                    self._check_and_fix_dimension_mismatch(table_name, len(sample_vector))

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
        rrf_k: int = 60,
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
            rrf_k: RRF fusion k parameter (Story 2.11 configurable, default 60)

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
                    rrf_k=rrf_k,
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
