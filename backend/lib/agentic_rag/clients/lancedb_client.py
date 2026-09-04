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
import fnmatch
import json
import os
import time
import unicodedata
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


class TableMissingError(RuntimeError):
    """CARD-G2-4: vault 专属表不存在 — 故障, 不是「健康空」。

    引入动机 (BATCH-2026-08-29-第七批 / CARD-G2-4): 删除 B0.7 legacy 回退后,
    ``{vault}_{table}`` 不存在时不再静默落到裸表。此时必须让调用方**知道**
    表缺失, 而不是收到一个与「索引过但真没命中」无法区分的空列表 ——
    后者正是计划书 :48 记的「legacy 表 fail-open」暗坑的另一半。

    继承 ``RuntimeError`` 而非裸 ``Exception`` 的理由 (兼容契约):
    既有窄捕获调用方 (``react_agent.search_vault_notes`` 的两级 except 捕
    ``RuntimeError/ConnectionError/ValueError``、``_search_internal`` 原本就
    抛 ``RuntimeError``) 无需改动即可继续兜住本异常, 行为不劣于改动前;
    而 ``search()`` 内部用 ``isinstance`` 精确放行, 使它**唯一地**穿透
    ``enable_fallback`` 的「任何错 → []」吞噬门 (其余异常契约不变, 防波及)。

    Attributes:
        table_name: 缺失的**已解析**表名 (含 vault 前缀), 供上层写进
            ``reason`` 与 Ops 日志 —— 诊断信息必须能直接对上 LanceDB 里
            该建而未建的那张表。
    """

    def __init__(self, table_name: str, detail: str = ""):
        self.table_name = table_name
        self.detail = detail
        msg = f"LanceDB table '{table_name}' does not exist"
        if detail:
            msg = f"{msg} ({detail})"
        super().__init__(msg)


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


# RAG-S2 T3 (2026-08-09): tiktoken 编码器懒加载 + 模块级共享 —
# _chunk_text 与 _split_md_by_heading 的面包屑条件化都要计 token。
_TIKTOKEN_ENC = None

# RAG-S2 T3 Step4: chunk 正文低于此 token 数时面包屑只留文件名 —
# 侦察 A/B 实测短块完整路径占比过高反客为主, 条件化后短块 +0.091。
_BREADCRUMB_FULL_MIN_TOKENS = 150


def _count_tokens(t: str) -> int:
    """tiktoken cl100k_base token 计数, 异常回退字符估算。"""
    global _TIKTOKEN_ENC
    if _TIKTOKEN_ENC is None:
        try:
            import tiktoken

            _TIKTOKEN_ENC = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Code-Review LOW-4 (2026-08-09): 离线冷缓存首跑 get_encoding 会
            # 下载 BPE 文件, 失败不能炸穿整个索引 — 降级为字符估算。
            _TIKTOKEN_ENC = False
    if _TIKTOKEN_ENC is False:
        return len(t) // 2
    try:
        return len(_TIKTOKEN_ENC.encode(t))
    except ValueError:
        # tiktoken regex backtracking overflow on exotic content —
        # fall back to char-based estimate (1 token ≈ 4 chars for English,
        # ≈ 1.5 chars for Chinese; use conservative 2 chars/token)
        return len(t) // 2


def _chunk_text(text: str, max_tokens: int = 512, overlap_tokens: int = 50) -> List[str]:
    """
    Story 2.3 → RAG-S2 T3 (2026-08-09): 三级层次分块 — 段落优先 + 句子降级 + 原子保护

    1. 检测并保护原子单元（代码块、数学公式、表格）不被切断
    2. 非原子文本先按段落块切（空行 / 水平线 / callout 块边界），整段累积到
       max_tokens 后在段落边界 flush — 语义无关句子不再跨段拼进同一大桶
       （T2 侦察实测稀释根因: 追加内容混桶 0.4227 vs 独立成块 0.668）
    3. 单段超 max_tokens → 降级句子级贪心累积；单句超限 → 子句级切分
    4. overlap 段落化: 只取上一 chunk 最后一个完整段落（≤ overlap_tokens 才取），
       装不下则不取 — 杜绝半截上下文拼进新 chunk 制造噪音

    Args:
        text: 输入文本（已经过 heading 一级切分）
        max_tokens: 每个 chunk 的 token 上限（默认 512）
        overlap_tokens: chunk 间 token 重叠量（默认 50）

    Returns:
        List[str]: 分块后的文本列表
    """
    import re

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
    # question marks, exclamation marks.
    # RAG-S2 T2 bug① (2026-08-09): ASCII [.!?] 只在后随空白/行尾才断句 —
    # 旧 pattern 在任意 `!` 后断, 把每个 callout 标记 `> [!question]+` 切成
    # `> [!` + `question]+`(实测全库无一幸免), 小数 `0.88` 切成 `0.`/`88`,
    # 域名 `a.b.org` 切成三段 — 给含批注的 chunk 注入大量语义垃圾, 并毁掉
    # 一切按 callout 边界处理的下游正则。中文全角标点无此歧义, 保持原行为。
    sentence_pattern = re.compile(
        r"(?<=[。！？])\s*"  # after full-width sentence punctuation
        r"|(?<=[.!?])(?=\s|$)\s*"  # ASCII punctuation only before whitespace/EOL
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

    # --- Step 3: Build chunks — 段落优先累积, 超长单段降级句子级 ---
    hr_pattern = re.compile(r"^(-{3,}|\*{3,}|_{3,})\s*$")

    def _split_paragraphs(t: str) -> List[str]:
        """段落块切分: 空行为界; 水平线自成边界(纯记号无语义, 丢弃);
        callout 块(连续 > 开头行)整体成段, 不再被切进正文桶。"""
        paras: List[str] = []
        buf: List[str] = []
        buf_is_callout = False

        def _flush_buf():
            nonlocal buf, buf_is_callout
            block = "\n".join(buf).strip()
            if block:
                paras.append(block)
            buf = []
            buf_is_callout = False

        for line in t.split("\n"):
            stripped = line.strip()
            if not stripped:
                _flush_buf()
                continue
            if hr_pattern.match(stripped):
                _flush_buf()
                continue
            line_is_callout = stripped.startswith(">")
            if buf and line_is_callout != buf_is_callout:
                # callout 块与普通文本互为段落边界
                _flush_buf()
            buf_is_callout = line_is_callout
            buf.append(line)
        _flush_buf()
        return paras

    def _chunk_sentences(t: str) -> List[str]:
        """句子级贪心累积 — T3 后仅作超长单段的降级路径。
        overlap 只取完整句子且限于段内, 不跨段拼接。"""
        out: List[str] = []
        parts: List[str] = []
        part_tokens = 0

        def _flush_parts():
            nonlocal parts, part_tokens
            joined = "\n".join(parts).strip()
            if joined:
                out.append(joined)
            parts = []
            part_tokens = 0

        for sentence in _split_sentences(t):
            s_tokens = _count_tokens(sentence)

            # Handle sentences that exceed max_tokens on their own
            if s_tokens > max_tokens:
                _flush_parts()
                out.extend(_split_long_sentence(sentence))
                continue

            if part_tokens + s_tokens > max_tokens:
                _flush_parts()
                if overlap_tokens > 0 and out:
                    overlap: List[str] = []
                    overlap_count = 0
                    for prev in reversed(_split_sentences(out[-1])):
                        prev_tokens = _count_tokens(prev)
                        if overlap_count + prev_tokens > overlap_tokens:
                            break
                        overlap.insert(0, prev)
                        overlap_count += prev_tokens
                    parts = overlap
                    part_tokens = overlap_count

            parts.append(sentence)
            part_tokens += s_tokens
        _flush_parts()
        return out

    chunks: List[str] = []
    current_parts: List[str] = []  # 段落粒度累积
    current_tokens = 0
    prev_chunk_paras: List[str] = []  # 上一次 flush 的段落列表 (overlap 来源)

    def _flush_current():
        nonlocal current_parts, current_tokens, prev_chunk_paras
        if current_parts:
            joined = "\n\n".join(current_parts).strip()
            if joined:
                chunks.append(joined)
                prev_chunk_paras = list(current_parts)
        current_parts = []
        current_tokens = 0

    def _paragraph_overlap(next_tokens: int) -> List[str]:
        """overlap 段落化: 只取上一 chunk 最后一个完整段落 —
        超 overlap 预算或加上新段后溢出 max_tokens 则不取。"""
        if overlap_tokens <= 0 or not prev_chunk_paras:
            return []
        tail = prev_chunk_paras[-1]
        tail_tokens = _count_tokens(tail)
        if tail_tokens <= overlap_tokens and tail_tokens + next_tokens <= max_tokens:
            return [tail]
        return []

    for is_atomic, segment in segments:
        if is_atomic:
            seg_tokens = _count_tokens(segment)
            # If atomic fits in current chunk, add it
            if current_tokens + seg_tokens <= max_tokens:
                current_parts.append(segment.strip())
                current_tokens += seg_tokens
            else:
                # Flush current chunk, then emit atomic as standalone
                _flush_current()
                chunks.append(segment.strip())
                prev_chunk_paras = [segment.strip()]
            continue

        for para in _split_paragraphs(segment):
            para_tokens = _count_tokens(para)

            if para_tokens > max_tokens:
                # 单段超限 → 降级句子级 (overlap 不跨段落边界)
                _flush_current()
                chunks.extend(_chunk_sentences(para))
                prev_chunk_paras = []
                continue

            if current_tokens + para_tokens > max_tokens:
                _flush_current()
                overlap_paras = _paragraph_overlap(para_tokens)
                if overlap_paras:
                    current_parts = list(overlap_paras)
                    current_tokens = sum(_count_tokens(p) for p in overlap_paras)

            current_parts.append(para)
            current_tokens += para_tokens

    # Flush remaining
    _flush_current()

    return chunks if chunks else [text.strip()]


# R3 (2026-07-12 对抗审查): vault 索引黑名单模块级常量 — index_vault_notes 与
# index_single_file 共用同一份 (旧状态: 只有全量路径有黑名单, 单文件路径零检查,
# incremental 端点构成信息隔离旁路)。app 层 (metadata.py) 传入 config 的
# VAULT_INDEX_SKIP_DIRS 时覆盖本默认; 检验白板/验收单 内置兜底 — 即使调用方
# 忘传, 信息隔离 (d=1.50) 也不破。
DEFAULT_VAULT_SKIP_DIRS = [
    ".obsidian",
    ".git",
    ".trash",
    "node_modules",
    ".claude",
    ".claudian",  # Skill / Claudian 工具文档
    "_bmad-output",  # BMAD 开发文档（若 vault 内含此目录）
    "archive",
    "templates",  # 归档 / 模板目录
    "outputs",  # 验收/导出物
    "*-explanations",  # AI 生成解释（glob，需 fnmatch）
    "Excalidraw",  # 手绘图（无文字检索价值）
    "_misc",  # 杂项 / junk
    "检验白板",  # 信息隔离铁律 — 考题绝不能经 RAG 回流
    "验收单",
    # RAG-S1 (2026-08-03): video-to-canvas 在每个视频目录下产出 chunks/merged.md
    # 与源笔记同内容 — 双份入库互相挤占 top-k (raw/ 冗余行约一半来自此)。
    "chunks",
    # RAG-S1 (2026-08-03): MCP 隔离区 (P0-2 quarantine) 不是学习内容。
    ".quarantine",
    # A-9 (R11-BATCH2-2026-08-17): 收件箱暂存区 — 未分诊碎片不参与检索,
    # 是第 3 批清仓流程 (B-1) 的前置边界。与 config.VAULT_INDEX_SKIP_DIRS
    # 权威源同批追加 (该字段注释写明二者必须保持一致)。
    "_待处理",
    # A-9 同批: 下划线前缀归档区, 与上方无前缀的 archive 并存。
    "_archive",
]

#: ⛔⛔ 不可撤销硬底 (P1-02, Codex 对抗审查 2026-08-19)。
#: 必须与 app/config.py::IMMUTABLE_VAULT_SKIP_DIRS 逐字一致 —— lib 不能 import
#: app, 物理上无法单源, 一致性由 tests/regression 的防漂移锁保证。
#:
#: ⚠️ 与上方 DEFAULT_VAULT_SKIP_DIRS 语义**不同**:
#:   - DEFAULT_VAULT_SKIP_DIRS = 调用方传 None 时的**替换式**兜底
#:     (RAG-S1 M4 刻意选替换而非 union, 避免 env 放宽黑名单时 orchestrator
#:      放行、本函数拒绝且不写指纹, 形成 60s 永动)
#:   - IMMUTABLE_VAULT_SKIP_DIRS = **无条件 union**, 调用方传什么都撤不掉
#:
#: 两者不冲突: 前者管「可配置项的默认值从哪来」, 后者管「哪些边界根本不可配置」。
#: 永动风险只存在于可配置区间; 硬底在 orchestrator 与本模块两侧同时生效, 判定
#: 一致故不产生分歧。
IMMUTABLE_VAULT_SKIP_DIRS = (
    "检验白板",  # 信息隔离铁律 (Karpicke d=1.50) — 考题绝不能经 RAG 回流
    "验收单",  # 同为信息隔离面, 且实测只有单层防御 (读侧 doc_type 不挡)
    "_待处理",  # A-9 收件箱暂存区
    "_archive",  # A-9 下划线前缀归档
    ".git",
    ".obsidian",
    # ── P1-05 复核补入 (Codex 2026-08-19) ──
    ".trash",  # 已删除内容不得重回检索面
    ".quarantine",  # MCP 隔离区, 定义上就是"不该被消费"的内容
    ".claude",  # 含 hooks/settings/**cache/board-manifest 快照本身**
)


def _with_immutable_skip_dirs(skip_dirs: list[str]) -> list[str]:
    """把不可撤销硬底 union 进调用方给的黑名单 (P1-02)。

    保序: 调用方原顺序在前 (不打乱 demote-first 之类的语义), 硬底缺项追加在后。
    """
    merged = list(skip_dirs)
    for hard in IMMUTABLE_VAULT_SKIP_DIRS:
        if hard not in merged:
            merged.append(hard)
    return merged


# RAG-S1 (2026-08-03): 文件名黑名单提升为模块级常量 — 此前只在
# index_vault_notes 函数体内 (工具/工程文档 + 测试残留), index_single_file
# 完全没有这一层, 增量路径可把 CLAUDE.md / UAT-*.md 送入库。两路共用一份。
DEFAULT_VAULT_SKIP_FILES = [
    # 工具/工程文档（非用户学习内容）
    "CLAUDE.md",
    "管道设计.md",
    "Dashboard.md",
    "未命名*.md",
    "Untitled*.md",
    "2111.md",  # 测试残留
    "*.excalidraw.md",  # 手绘图 md 包装
    # Phase A T1.1 followup (2026-05-09): 补测试 + UAT 残留
    "TestConcept*.md",
    "UAT-*.md",
    "*-test.md",
]

#: 只在 vault **根目录**生效的文件黑名单 (P2-02, Codex 对抗审查 2026-08-19)。
#:
#: 与上方 DEFAULT_VAULT_SKIP_FILES 的区别是**作用域**:
#:   - DEFAULT_VAULT_SKIP_FILES: 任意层级 basename 匹配 (fnmatch, 支持通配)
#:   - 本表: 仅当文件位于 vault 根 (rel_path 不含分隔符) 时才匹配
#:
#: 为什么需要分开: A-4 最初把 `excalibrain.md` 放进上表, 于是任意深度的同名
#: 文件都被排除 —— 包括用户完全可能手写的 `节点/excalibrain.md`。根级那一份是
#: ExcaliBrain 插件的运行时产物, 深层同名文件则没有任何理由被判定为工具产物。
#:
#: 匹配规则: **casefold 精确比较**, 不做 fnmatch 通配。
#:   - casefold 是为了挡住 `ExcaliBrain.md` / `EXCALIBRAIN.md` 这类大小写变体
#:     (插件在不同版本/平台上写出的文件名大小写并不稳定);
#:   - 不用通配是为了避免重蹈 `excalibrain*` 会吃掉 `excalibrain-笔记.md` 的覆辙。
DEFAULT_VAULT_SKIP_ROOT_FILES = ("excalibrain.md",)

#: 预计算的归一集合 — 判定热路径上避免每次重算 (P1-05c: 补 NFC)
_SKIP_ROOT_FILES_CASEFOLD = frozenset(unicodedata.normalize("NFC", n).casefold() for n in DEFAULT_VAULT_SKIP_ROOT_FILES)


def _canon_for_match(s: str) -> str:
    """黑名单比较前的归一: NFC + casefold (P1-05c, Codex 三轮 F-01a)。

    macOS APFS 大小写不敏感且 Unicode 归一形不定 —— `.CLAUDE/` 与 `.claude/`
    是**同一个物理目录**, `节点/claude.md` 就是 `节点/CLAUDE.md`; fnmatch 却
    大小写敏感 (macOS 的 os.path.normcase 是 no-op), 实测四类大小写变体全部
    绕过黑名单。所有 fnmatch 判定点必须双侧过本函数, 不许再出现裸 fnmatch。
    """
    return unicodedata.normalize("NFC", s).casefold()


def _fnmatch_canon(name: str, pat: str) -> bool:
    """归一后的 fnmatch — 黑名单判定的唯一匹配原语。"""
    return fnmatch.fnmatch(_canon_for_match(name), _canon_for_match(pat))


def _resolves_outside_vault(file_path: str, vault_path: str) -> bool:
    """P1-05d (Codex 四轮 V2): open 前的 containment 门 — symlink/.. 越界判定。

    实测反例: `节点/escape.md -> vault 外文件` 曾被全量/单文件两条真实入口
    open→嵌入→落库 (词法黑名单只看 rel_path 字符串, 对 symlink 目标不可见)。
    lib 不能 import app (架构约束), 判定自包含; 语义与
    app.core.vault_admission.check_vault_path 的 containment 一致
    (realpath 必须落在 vault 内)。
    """
    try:
        resolved = os.path.realpath(file_path)
        vault_real = os.path.realpath(vault_path)
    except OSError:
        return True  # 解析失败 fail-closed
    return not (resolved == vault_real or resolved.startswith(vault_real + os.sep))


def _is_skipped_vault_file(rel_path: str, skip_files) -> bool:
    """文件名黑名单判定 (P2-02: 任意层级 + 仅根级两套规则)。

    Args:
        rel_path: vault 相对路径; 允许 os.sep 或 '/' 分隔。
        skip_files: 任意层级 basename 黑名单 (fnmatch 通配)。

    两条索引路径 (全量 index_vault_notes / 单文件 index_single_file) 共用本函数,
    避免再次出现「一条路径有黑名单另一条没有」的旁路 (RAG-S1 R3 的教训)。
    P1-05c: 匹配走 _fnmatch_canon (NFC+casefold) — `节点/claude.md` 在 APFS 上
    就是 `节点/CLAUDE.md`, 裸 fnmatch 放行即真实旁路。
    """
    normalized = rel_path.replace(os.sep, "/").strip("/")
    base_name = normalized.rsplit("/", 1)[-1]

    if any(_fnmatch_canon(base_name, pat) for pat in skip_files):
        return True

    # 仅根级: 归一化后不含分隔符 = 直接位于 vault 根
    if "/" not in normalized and _canon_for_match(base_name) in _SKIP_ROOT_FILES_CASEFOLD:
        return True

    return False


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
    # Story 2.3 Fix: vault_notes removed — it has a dedicated retrieve_vault_notes
    # node in state_graph.py. Including it here caused dual-search duplication.
    DEFAULT_TABLES = ["canvas_nodes"]

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
        db_path: Optional[str] = None,  # Story 2.2 Phase A: env-aware (LANCEDB_DATA_PATH); fallback "data/lancedb"
        embedding_dim: int = DEFAULT_EMBEDDING_DIM,
        embedding_model: str = "BAAI/bge-m3",
        timeout_ms: int = 30000,  # Ollama GPU cold start ~15s, warm ~300ms. Must cover cold start.
        batch_size: int = 100,
        enable_fallback: bool = True,
        vault_id: Optional[str] = None,
    ):
        """
        初始化 LanceDBClient

        Story 2.3: 默认使用 bge-m3 1024d Dense 向量
        Story 1.9: vault_id 前缀隔离
        Story 2.2 Phase A: db_path 默认读 LANCEDB_DATA_PATH env（解耦 docker volume mount）

        Args:
            db_path: LanceDB数据库路径
                - 显式传字符串 → 用这个值
                - None（默认）→ 读 env LANCEDB_DATA_PATH，env 未设则 fallback "data/lancedb"
            embedding_dim: 嵌入向量维度 (默认: 1024 for bge-m3)
            embedding_model: embedding模型名称 (默认: BAAI/bge-m3)
            timeout_ms: 超时时间(毫秒), 默认400ms (Story 12.2 AC 2.3)
            batch_size: 批量处理大小 (默认: 100, Story 23.2 AC 2)
            enable_fallback: 启用降级(超时/错误时返回空结果)
            vault_id: Vault namespace (None = dynamic from config)
        """
        if db_path is None:
            db_path = os.getenv("LANCEDB_DATA_PATH", "data/lancedb")
        self.db_path = os.path.expanduser(db_path)
        self.embedding_dim = embedding_dim
        self.embedding_model = embedding_model
        self.timeout_ms = timeout_ms
        self.batch_size = batch_size
        self.enable_fallback = enable_fallback
        self._vault_id_override = vault_id

        self._db = None
        self._initialized = False
        self._tables_cache: Dict[str, Any] = {}
        self._embedder = None

        # ✅ Story 23.2: MultimodalVectorizer for embedding
        self._vectorizer = None
        self._vectorizer_initialized = False

    # =========================================================================
    # Story 1.9: Vault-ID table namespacing
    # =========================================================================

    @property
    def active_vault_id(self) -> str:
        """Resolve effective vault_id for table namespace.

        Resolution order (Wave-2 P0-2 hotfix, 2026-05-12):
        1. ``self._vault_id_override`` — explicit constructor arg (legacy POC tests)
        2. ``app.core.subject_config.get_current_subject_id()`` ContextVar
           — set per-request by ``set_current_subject_id`` in chat / metadata
           endpoints. Strips ``vault:`` prefix and keeps the FIRST segment so
           ``vault:cs_61b:algorithms`` → ``cs_61b``. This is the source of
           truth for multi-vault isolation introduced by Story 2.5.Y.
        3. ``app.config.get_current_vault_id()`` — legacy global active vault.
           Kept as backward-compat fallback for callers that haven't migrated
           to ContextVar (background tasks / CLI / older tests).
        4. ``"default"`` — final fallback when imports fail (e.g. lib used
           standalone outside the FastAPI app).
        """
        if self._vault_id_override is not None:
            return self._vault_id_override

        # Step 2: prefer ContextVar from subject_config (Story 2.5.Y vault wiring).
        # Endpoints call set_current_subject_id(build_vault_group_id(...)) →
        # ContextVar holds "vault:cs_61b" / "vault:cs_61b:algorithms" / etc.
        # We strip the "vault:" prefix and take the first segment as the
        # LanceDB table-namespace key (matches build_vault_group_id contract).
        #
        # Wave-3 hotfix (ChatGPT v4 verdict #3): narrow exception catch — must
        # let BaseException/KeyboardInterrupt/SystemExit propagate; only swallow
        # the specific import/attr/runtime/value failures expected when the
        # `app.core.subject_config` module is unavailable or its ContextVar
        # accessor misbehaves.
        try:
            from app.core.subject_config import (
                DEFAULT_SUBJECT_ID,
                get_current_subject_id,
            )

            ctx_value = get_current_subject_id()
            if ctx_value and ctx_value != DEFAULT_SUBJECT_ID:
                # vault:cs_61b → cs_61b ; vault:cs_61b:algorithms → cs_61b
                derived = ctx_value
                if derived.startswith("vault:"):
                    derived = derived[len("vault:") :]
                # take first segment (drop :subject / :canvas suffix)
                first_seg = derived.split(":", 1)[0].strip()
                if first_seg:
                    logger.debug(
                        "[LanceDB vault wiring] active_vault_id resolved from subject_config ContextVar: %s → %s",
                        ctx_value,
                        first_seg,
                    )
                    return first_seg
        except (ImportError, AttributeError, RuntimeError, ValueError) as e:
            # subject_config not importable (lib used standalone) or accessor
            # broke at runtime → fall through to Level 3. Surface in debug log
            # so Ops can spot wiring regressions without flooding warnings on
            # the legitimate standalone-lib path.
            logger.debug(
                "[LanceDB vault wiring] subject_config ContextVar unavailable (%s: %s) — falling back to app.config",
                type(e).__name__,
                e,
            )

        # Step 3: legacy fallback — global active vault from settings.
        # Same narrow-exception discipline as Level 2.
        try:
            from app.config import get_current_vault_id

            return get_current_vault_id()
        except (ImportError, AttributeError, RuntimeError, ValueError) as e:
            # Level 4 (final): hard fallback to "default" table namespace.
            # ⛔ This is the cross-vault-leak danger zone — warn loudly so Ops
            # see it in production logs. Reaching here means BOTH the request
            # ContextVar AND the legacy global config are unreachable, which
            # should never happen inside a running FastAPI process.
            logger.warning(
                "[LanceDB vault wiring] active_vault_id fell back to 'default' "
                "— both subject_config ContextVar and app.config unavailable "
                "(last error: %s: %s); possible cross-vault leak",
                type(e).__name__,
                e,
            )
            return "default"

    def resolve_table_name(self, table_name: str) -> str:
        """Prefix table_name with vault_id for namespace isolation.

        CARD-G2-4 (BATCH-2026-08-29-第七批): **删除 Phase B0.7 legacy 回退**。

        旧行为 (已删): 若 ``{vid}_{table_name}`` 不存在但裸 ``{table_name}``
        存在 → 返回裸表名。该回退同时污染读写两侧 —— 本方法被 7 处内部
        调用, 其中 6 处是索引/写路径 (``rebuild_index`` / ``index_image_content``
        / ``index_canvas`` / ``index_vault_notes`` / ``index_single_file`` /
        ``add_documents``), 只有 ``search`` 是读侧:
        新 vault 首次索引时 prefixed 表尚未建, 回退会把新 vault 的数据
        **写进裸表**, 与其它 vault 的存量混在一起 (计划书 :113 记的
        「legacy vault_notes 读写共用回退」)。读侧同理: vault A 查不到自己
        的表就去读裸表里 vault B 的行, 且下游无法区分这是回退还是本 vault
        真实数据。

        现行为: 非 default vault 恒返回 prefixed 名。表不存在时由读路径
        抛 :class:`TableMissingError` (故障), 写路径正常建 prefixed 新表 ——
        **不再有任何路径落到裸表**。

        ⚠️ 保留的窄映射 (勿删): ``vid`` 为空或 ``"default"`` → 返回裸表名。
        这不是 legacy 回退, 而是**单 vault 部署的正常命名空间** (裸表就是
        它的表)。删掉会炸单 vault 部署。判据钉死在
        ``tests/unit/test_lancedb_vault_isolation.py:23`` 与 ``:35``。
        """
        vid = self.active_vault_id
        if not vid or vid == "default":
            return table_name
        if table_name.startswith(f"{vid}_"):
            return table_name
        return f"{vid}_{table_name}"

    def _is_table_absent(self, table_name: str) -> bool:
        """CARD-G2-4: 打表失败时判别「表不存在」vs「表在但打不开」。

        分流依据是目录的**实查**, 不做异常文案匹配 —— LanceDB 的
        missing-table 异常类型与文案在 0.x 期间换过多次 (``FileNotFoundError``
        / ``ValueError`` / ``LanceError``), 按文案匹配会在升版时静默失效,
        变成一道恒判 False 的死门。

        ⛔ 必须走 ``list_tables(limit=None)`` 而不是 ``table_names()``
        (Codex round-1 审查抓出, lancedb 0.30.2 实测):
        ``DBConnection.table_names(page_token=None, limit=10)`` —— **默认只返回
        前 10 张表**。库里超过 10 张表时, 第 11 张之后的表会被判成"不存在",
        于是一个明明在的表被本卡的 fail-closed 通道当成缺表抛出去。
        ``list_tables(limit=None)`` 才是全量。

        列举本身失败时返回 ``False`` (fail-safe): 判不出来就当基础设施故障,
        沿用旧 ``RuntimeError`` 契约, **不**误报表缺失 —— 误报会让本卡新增的
        fail-closed 通道去吞一个其实与 vault 隔离无关的故障。
        """
        if self._db is None:
            return False
        try:
            return table_name not in set(self._all_table_names())
        except Exception:
            return False

    def _all_table_names(self) -> list:
        """全量表名 —— 绕开 ``table_names()`` 的 limit=10 默认分页。

        兼容两代 API: 新版 ``list_tables(limit=None)`` 返回
        ``ListTablesResponse(tables=[...])``, 旧版返回 plain list;
        都没有时退回 ``table_names()`` 并**显式**把 limit 调大 (它至少
        比默认 10 诚实)。
        """
        if self._db is None:
            return []
        if hasattr(self._db, "list_tables"):
            raw = self._db.list_tables(limit=None)
            return list(getattr(raw, "tables", raw))
        return list(self._db.table_names(limit=10_000))

    def list_vault_tables(self, vault_id: str | None = None) -> list[str]:
        """Return table names belonging to a specific vault."""
        if self._db is None:
            return []
        prefix = f"{vault_id}_" if vault_id and vault_id != "default" else ""
        all_tables = self._db.table_names()
        if not prefix:
            # RAG-S1 Code-Review H3 (2026-08-03): 精确匹配裸指纹表 —
            # endswith 会把每个 vault 的 {vid}_file_fingerprints 都归入
            # default, DELETE /index/default 一次抹掉全部 vault 的变更检测。
            return [t for t in all_tables if "_" not in t or t == self.FINGERPRINT_TABLE]
        return [t for t in all_tables if t.startswith(prefix)]

    def get_all_vault_stats(self) -> dict[str, dict]:
        """Return per-vault table/row statistics."""
        if self._db is None:
            return {}
        stats: dict[str, dict] = {}
        for tname in self._db.table_names():
            parts = tname.split("_", 1)
            vid = parts[0] if len(parts) >= 2 else "default"
            if vid not in stats:
                stats[vid] = {"tables": 0, "rows": 0}
            stats[vid]["tables"] += 1
            try:
                tbl = self._db.open_table(tname)
                stats[vid]["rows"] += tbl.count_rows()
            except Exception:
                pass
        return stats

    def drop_vault_tables(self, vault_id: str) -> int:
        """Drop all tables for a given vault_id. Returns count of dropped tables."""
        if self._db is None:
            return 0
        tables = self.list_vault_tables(vault_id)
        for tname in tables:
            try:
                self._db.drop_table(tname, ignore_missing=True)
                self._tables_cache.pop(tname, None)
            except Exception:
                pass
        return len(tables)

    def connect_lightweight(self) -> bool:
        """
        RAG-S1 (2026-08-03): connect the DB WITHOUT loading the CPU embedding
        model or running startup dimension checks.

        For write-side callers (index orchestrator) that embed via the Ollama
        batch path: full initialize() preloads bge-m3 CPU weights (~7.4s
        measured) purely as a fallback, and _cache_tables() runs
        _check_and_fix_dimension_mismatch which can DROP an in-construction
        table from a read path. index_single_file / fingerprint methods only
        need a live _db handle — they open tables per call.

        Returns:
            True if connection successful.
        """
        if not LANCEDB_AVAILABLE:
            if LOGURU_ENABLED:
                logger.warning("LanceDB not installed. Run: pip install lancedb")
            self._initialized = True
            return False
        try:
            self._db = lancedb.connect(self.db_path)
            self._initialized = True
            if LOGURU_ENABLED:
                logger.info(f"LanceDBClient connect_lightweight: path={self.db_path}")
            return True
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"LanceDBClient connect_lightweight failed: {e}")
            self._initialized = True
            return False

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
            # RAG-S1 F1 (2026-08-03): endswith — 前缀化后 {vid}_file_fingerprints
            # 也必须跳过, 否则维度检查会把无 vector 列的指纹表 drop 掉
            vector_tables = [t for t in self._tables_cache if not t.endswith(self.FINGERPRINT_TABLE)]
            for tname in vector_tables:
                self._check_and_fix_dimension_mismatch(tname, self.embedding_dim)

        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"Failed to cache tables: {e}")

    # =========================================================================
    # Story 2.7: File Fingerprint Infrastructure
    # =========================================================================

    FINGERPRINT_TABLE = "file_fingerprints"

    @property
    def _fingerprint_table_name(self) -> str:
        """RAG-S1 F1 (2026-08-03): vault-prefixed fingerprint table name.

        The fingerprint table was the ONLY table not going through vault
        prefixing — two vaults sharing one global table meant same-relative-path
        files cross-judged each other as "unchanged" (permanent content loss)
        and rebuild_index() of one vault wiped every vault's change detection.

        Deliberately NO B0.7 legacy fallback here: falling back to the old
        global table would make every file look unchanged and the prefixed
        table would never get populated (bootstrap deadlock). First reconcile
        after this change re-indexes all files once — accepted one-time cost.
        """
        vid = self.active_vault_id
        if not vid or vid == "default":
            return self.FINGERPRINT_TABLE
        return f"{vid}_{self.FINGERPRINT_TABLE}"

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

    def _fingerprint_table_exists(self) -> bool:
        """
        Story 2.7 Task 1.1 / RAG-S1 F1: check the vault-scoped fingerprint
        table exists. Always queries db.table_names() — never trusts
        _tables_cache handles (2026-07-10 T3 stale-handle discipline).

        Schema: file_path (str), content_hash (str), last_indexed (str), chunk_count (int)
        """
        if self._db is None:
            return False
        try:
            return self._fingerprint_table_name in self._db.table_names()
        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"[fingerprint] Error checking fingerprint table: {e}")
            return False

    def _get_all_fingerprints(self) -> Dict[str, str]:
        """
        Get all stored fingerprints as file_path -> content_hash mapping.

        Returns:
            Dict mapping file_path to content_hash.
        """
        if not self._fingerprint_table_exists():
            # No fingerprint table yet — first run, all files are new
            empty_map: Dict[str, str] = {}
            return empty_map

        try:
            tbl = self._db.open_table(self._fingerprint_table_name)
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
            fp_table = self._fingerprint_table_name
            if self._fingerprint_table_exists():
                tbl = self._db.open_table(fp_table)
                # Delete existing record for this file
                escaped = file_path.replace("'", "''")
                try:
                    tbl.delete(f"file_path = '{escaped}'")
                except Exception:
                    pass
                tbl.add([record])
            else:
                # Create table with first record
                tbl = self._db.create_table(fp_table, data=[record])
            self._tables_cache[fp_table] = tbl
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"[fingerprint] Failed to update fingerprint for {file_path}: {e}")

    def _remove_fingerprint(self, file_path: str):
        """
        Story 2.7 Task 1.5: Delete fingerprint record.

        Args:
            file_path: Relative file path.
        """
        if not self._fingerprint_table_exists():
            return

        try:
            tbl = self._db.open_table(self._fingerprint_table_name)
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
            # T3 根治 (2026-07-10): 不读缓存句柄 — rebuild/drop 后旧句柄指向
            # 已删 dataset, 操作静默失败。open_table 轻量 (LanceDB 官方语义),
            # 每次拿最新句柄; 仍写缓存供 create 流程等内部引用。
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
        table_name = self.resolve_table_name(table_name)
        start_time = time.perf_counter()

        if not self._initialized:
            await self.initialize()

        # Drop fingerprint table (RAG-S1 F1: vault-scoped name — dropping the
        # global table here used to wipe every OTHER vault's change detection)
        fp_table = self._fingerprint_table_name
        try:
            self._db.drop_table(fp_table, ignore_missing=True)
            self._tables_cache.pop(fp_table, None)
        except Exception:
            pass

        # Drop main table
        try:
            self._db.drop_table(table_name, ignore_missing=True)
            self._tables_cache.pop(table_name, None)
        except Exception:
            pass

        if LOGURU_ENABLED:
            logger.info(f"[REBUILD] Dropped tables '{table_name}' and '{fp_table}', starting full rebuild")

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
        table_name = self.resolve_table_name(table_name)
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
                # T3 根治 (2026-07-10): 每次 open_table, 不读缓存句柄
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
            from agentic_rag.processors.multimodal_vectorizer import (
                MultimodalVectorizer,
            )

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
            raise RuntimeError("Vectorizer not available. Neither Ollama nor sentence-transformers is working.")

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
        table_name = self.resolve_table_name(table_name)
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
        table_name = self.resolve_table_name(table_name)
        index_start = time.perf_counter()

        if not self._initialized:
            await self.initialize()

        # Try CPU vectorizer init (may fail in Docker — Ollama GPU is primary path)
        await self._init_vectorizer()
        # Note: _vectorizer may be None here, but Ollama GPU batch path at
        # _ollama_embed_batch() does not require it. Only bail out if BOTH
        # Ollama and vectorizer are unavailable (checked per-file below).

        if skip_dirs is None:
            # Phase A T1.1 (2026-05-09): 扩展默认 skip + 加常见 PKM 噪音目录
            # R3 (2026-07-12): 收敛到模块级常量 DEFAULT_VAULT_SKIP_DIRS —
            # index_single_file 与本函数共用, 消除单文件路径的黑名单旁路
            skip_dirs = list(DEFAULT_VAULT_SKIP_DIRS)
        # P1-02 (Codex 审查 2026-08-19): 硬底无条件 union —— 调用方 (metadata
        # 端点 / orchestrator) 传什么都撤不掉信息隔离边界。放在 None 兜底之后,
        # 两条路径都覆盖。
        skip_dirs = _with_immutable_skip_dirs(skip_dirs)

        # Phase A T1.1 (2026-05-09): glob bug 修复 — 用 fnmatch 处理 *-explanations
        # 之前 `d not in skip_dirs` 精确匹配，glob 永不命中 → 41 个 explanations 全进库
        # RAG-S1 (2026-08-03): 收敛到模块级 DEFAULT_VAULT_SKIP_FILES, 与
        # index_single_file 共用 (此前单文件路径无文件名黑名单)。
        skip_files = list(DEFAULT_VAULT_SKIP_FILES)

        def _is_skipped_dir(name: str) -> bool:
            # P1-05c: 归一匹配 — .CLAUDE/_ARCHIVE 等大小写变体在 APFS 上是同一目录
            return any(_fnmatch_canon(name, pat) for pat in skip_dirs)

        def _is_skipped_file(name: str) -> bool:
            return any(_fnmatch_canon(name, pat) for pat in skip_files)

        # Scan all .md files
        md_files: List[str] = []
        for root, dirs, files in os.walk(vault_path):
            dirs[:] = [d for d in dirs if not _is_skipped_dir(d)]
            for f in files:
                if not f.endswith(".md"):
                    continue
                full_path = os.path.join(root, f)
                # P2-02: 传 vault 相对路径而非裸文件名 —— 仅根级黑名单
                # (DEFAULT_VAULT_SKIP_ROOT_FILES) 需要知道文件在不在根,
                # 否则 节点/excalibrain.md 这类深层同名笔记会被误排。
                rel_path = os.path.relpath(full_path, vault_path)
                if _is_skipped_vault_file(rel_path, skip_files):
                    continue
                # P1-05d (V2): symlink 越界在收集期即拒 — 不进 md_files 就
                # 不会被 open/嵌入/落库
                if _resolves_outside_vault(full_path, vault_path):
                    if LOGURU_ENABLED:
                        logger.warning(f"[INDEX] path resolves outside vault, skip: {rel_path}")
                    continue
                md_files.append(full_path)

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
            # RAG-S1 F3 (2026-08-03): force_rebuild 也必须检测 deleted —
            # 旧逻辑写死 [] 使已删文件的指纹与 chunks 在强制重建后永久残留
            # (指纹表单调增长)。
            _, _, deleted_files_rel = self._get_changed_files(vault_path, md_files)
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
                # RAG-S1 (2026-08-03): 空产出也登记指纹 (与单文件路径同修) —
                # 否则每轮增量扫描都把这些文件重判 new。
                self._delete_file_chunks(table_name, rel_path)
                empty_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                self._update_fingerprint(rel_path, empty_hash, 0)
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

                # RAG-P0 A1: doc_type — frontmatter.type wins; video_transcript
                # path overrides only when frontmatter has no explicit type.
                fm_doc_type = chunk.get("doc_type", "note") or "note"
                if fm_doc_type == "note" and LanceDBClient._is_video_transcript(chunk["file_path"]):
                    final_doc_type = "video_transcript"
                else:
                    final_doc_type = fm_doc_type

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
                    # RAG-P0 A1: doc_type for source-aware filter/rerank
                    "doc_type": final_doc_type,
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
                    # RAG-P0 A1: doc_type column for SQL where-clause filtering
                    "doc_type": final_doc_type,
                    "timestamp": datetime.now().isoformat(),
                    "metadata_json": json.dumps(metadata, ensure_ascii=False),
                }
                documents.append(doc)

            # Story 2.7 AC-2: delete-before-insert
            self._delete_file_chunks(table_name, rel_path)

            # Insert new chunks
            chunk_count = await self.add_documents(table_name, documents)
            total_chunks_indexed += chunk_count

            # RAG-S1 Code-Review H2: short write -> skip fingerprint so the
            # next incremental pass retries this file (log, don't abort the
            # whole scan).
            if chunk_count != len(documents):
                if LOGURU_ENABLED:
                    logger.error(
                        f"[INDEX] add_documents wrote {chunk_count}/"
                        f"{len(documents)} for {rel_path}; fingerprint NOT "
                        "updated — will retry next pass"
                    )
                continue

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
        max_tokens: int = 512,
        overlap_tokens: int = 50,
        rebuild_fts: bool = True,
        known_fingerprints: Optional[Dict[str, str]] = None,
        skip_dirs: Optional[List[str]] = None,
    ) -> int:
        """
        Story 2.7: Index a single .md file with delete-before-insert dedup + fingerprint.

        Story 2.7 AC-7: Uses os.path.relpath(file_path, vault_path) to preserve
        full directory structure (fixes CRITICAL C8 path loss).

        RAG-S1 (2026-08-03) drift fixes vs index_vault_notes:
        - max_tokens/overlap_tokens now caller-controlled (was fixed at 512
          while the full-scan path used 500 — same file chunked differently)
        - Ollama GPU batch embedding first, CPU vectorizer as fallback
          (was CPU-only: containers without the CPU model indexed nothing)
        - filename blacklist DEFAULT_VAULT_SKIP_FILES applied (was dir-only)
        - rebuild_fts=False lets batch callers rebuild FTS once per batch
          instead of once per file (full-table rebuild each time)
        - known_fingerprints lets batch callers prefetch the fingerprint map
          once instead of a full table scan per file (F4)

        Args:
            file_path: Absolute path to the .md file.
            table_name: Target table name.
            subject: Optional subject tag.
            vault_path: Vault root directory for computing relative path.
                        If None, falls back to parent directory of file_path.
            max_tokens: Chunk size in tokens (keep in sync with full-scan caller).
            overlap_tokens: Token overlap between chunks.
            rebuild_fts: Rebuild the FTS index after this file (batch callers: False).
            known_fingerprints: Prefetched fingerprint map to avoid per-file scans.

        Returns:
            Number of chunks indexed.
        """
        table_name = self.resolve_table_name(table_name)
        import hashlib

        if not os.path.isfile(file_path):
            if LOGURU_ENABLED:
                logger.warning(f"File not found for indexing: {file_path}")
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

        # R3 修复 (2026-07-12 对抗审查): 单文件路径落黑名单 — 旧状态零检查,
        # /index/vault/incremental 可把 检验白板/ 考题直接送入库 (真机验证过
        # 被接受), 信息隔离黑名单被单文件端点旁路。与全量路径同源。
        # RAG-S1 Code-Review M4 (2026-08-03): skip_dirs 由调用方传 settings
        # 权威值 (orchestrator/端点), 模块常量仅作无参兜底 — 否则 env 放宽
        # 黑名单时 orchestrator 放行、本函数拒绝且不写指纹, 形成 60s 永动。
        # P1-05c (Codex 三轮 F-01b): 黑名单判定整体提到读正文**之前** —— 旧序
        # 先 open/read 再判, 禁区文件正文虽不落库但已被读进进程; 判定用归一匹配。

        # P1-02: 同全量路径 —— 先取调用方值或替换式兜底, 再 union 不可撤销硬底
        effective_skip_dirs = _with_immutable_skip_dirs(
            skip_dirs if skip_dirs is not None else list(DEFAULT_VAULT_SKIP_DIRS)
        )
        for part in rel_path.split("/")[:-1]:
            if any(_fnmatch_canon(part, pat) for pat in effective_skip_dirs):
                if LOGURU_ENABLED:
                    logger.warning(f"[INDEX] blacklisted dir in path, refuse single-file index: {rel_path}")
                return 0

        # RAG-S1 (2026-08-03): filename blacklist — 与全量路径同源
        # DEFAULT_VAULT_SKIP_FILES (此前单文件路径只有目录黑名单,
        # CLAUDE.md / UAT-*.md 可经增量端点入库)。
        # P2-02: 收敛到 _is_skipped_vault_file —— 与全量路径共用同一判定,
        # 同时获得「仅根级」规则 (rel_path 本就是 vault 相对路径, 直接可用)。
        if _is_skipped_vault_file(rel_path, DEFAULT_VAULT_SKIP_FILES):
            if LOGURU_ENABLED:
                logger.warning(f"[INDEX] blacklisted filename, refuse single-file index: {rel_path}")
            return 0

        # P1-05d (V2): containment 门 — symlink/.. 越界一律拒, 目标正文不得被读
        if _resolves_outside_vault(file_path, vault_path):
            if LOGURU_ENABLED:
                logger.warning(f"[INDEX] path resolves outside vault, refuse single-file index: {rel_path}")
            return 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to read file for indexing: {e}")
            return 0

        # RAG-S1 (2026-08-03): 空内容不再提前 return — 必须走到下方的
        # 空产出登记分支写指纹, 否则 reconcile 每轮重判 new (live 实测
        # 6 文件永动循环)。

        # Check fingerprint — skip if unchanged
        # H1 fix: Compute hash from in-memory content (already read above)
        # to avoid TOCTOU race where file changes between read and hash.
        # RAG-S1 F4: batch callers pass known_fingerprints to avoid one full
        # fingerprint-table scan per file.
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        stored_fps = known_fingerprints if known_fingerprints is not None else self._get_all_fingerprints()
        if rel_path in stored_fps and stored_fps[rel_path] == content_hash:
            if LOGURU_ENABLED:
                logger.debug(f"[INDEX] Skipping unchanged file: {rel_path}")
            return 0

        chunks = self._split_md_by_heading(content, rel_path, max_tokens, overlap_tokens) if content.strip() else []

        if not chunks:
            # RAG-S1 (2026-08-03): 空产出也必须登记指纹 — 否则这些文件
            # (空内容 / whiteboard 剥样板后无正文 / 纯媒体引用) 每轮
            # reconcile 都被重判 new, 永动循环 (live 实测 6 文件 * 60s)。
            # 同时清旧行: 内容变空的文件必须停止可检索。
            self._delete_file_chunks(table_name, rel_path)
            self._update_fingerprint(rel_path, content_hash, 0)
            if LOGURU_ENABLED:
                logger.debug(f"[INDEX] No indexable chunks for {rel_path}; fingerprint recorded (0 chunks)")
            return 0

        # RAG-S1 (2026-08-03): Ollama GPU batch first, CPU vectorizer fallback —
        # 与全量路径 (index_vault_notes) 对齐。此前单文件只走 CPU vectorizer,
        # 容器内 CPU 模型缺席时增量索引恒 0。
        texts = [c["content"] for c in chunks]
        ollama_vectors = await self._ollama_embed_batch(texts)
        if ollama_vectors is not None:
            from types import SimpleNamespace

            vectorized = [SimpleNamespace(vector=v) for v in ollama_vectors]
        else:
            await self._init_vectorizer()
            if not self._vectorizer:
                # RAG-S1 Code-Review H1 (2026-08-03): RAISE, never return 0 —
                # a silent 0 here is counted as success by the orchestrator
                # (fingerprint unwritten -> re-enqueued as NEW next pass ->
                # freshness stays green while ZERO rows are written; the
                # "22-day frozen index" failure mode reborn). Raising routes
                # the failure into attempts/backoff + failed_entries telemetry.
                raise RuntimeError(
                    f"embedding unavailable for {rel_path}: Ollama batch and "
                    "CPU vectorizer both down — refusing silent zero-write"
                )
            vectorized = await self._vectorizer.batch_vectorize(texts)

        if len(vectorized) != len(chunks):
            # RAG-S1 Code-Review H1: same reasoning — mismatch is an infra
            # failure, not an empty file.
            raise RuntimeError(
                f"vectorization mismatch for {rel_path}: {len(chunks)} chunks vs {len(vectorized)} vectors"
            )

        # Build documents
        documents = []
        for chunk, vec_result in zip(chunks, vectorized):
            if not vec_result.vector:
                continue

            chunk_id = hashlib.md5(
                f"{chunk['file_path']}:{chunk.get('heading', '')}:{chunk['content'][:100]}".encode()
            ).hexdigest()

            # RAG-P0 A1: doc_type — frontmatter.type wins over path heuristic
            fm_doc_type_2 = chunk.get("doc_type", "note") or "note"
            if fm_doc_type_2 == "note" and LanceDBClient._is_video_transcript(file_path):
                final_doc_type_2 = "video_transcript"
            else:
                final_doc_type_2 = fm_doc_type_2

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
                # RAG-P0 A1: doc_type for source-aware filter/rerank
                "doc_type": final_doc_type_2,
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
                # RAG-P0 A1: doc_type column for SQL where-clause filtering
                "doc_type": final_doc_type_2,
                "timestamp": datetime.now().isoformat(),
                "metadata_json": json.dumps(metadata, ensure_ascii=False),
            }
            documents.append(doc)

        # Story 2.7 AC-2: delete-before-insert
        self._delete_file_chunks(table_name, rel_path)

        count = await self.add_documents(table_name, documents)

        # RAG-S1 Code-Review H2 (2026-08-03): fingerprint is the SOLE basis of
        # reconcile convergence — writing it after a failed/short add would
        # mark the file "indexed" while its rows are gone (old rows already
        # deleted above), losing the content silently until the next edit.
        # add_documents swallows exceptions into 0 — the count guard is the
        # only place this failure is visible.
        if count != len(documents):
            raise RuntimeError(
                f"add_documents wrote {count}/{len(documents)} chunks for "
                f"{rel_path}; fingerprint NOT updated — entry will be retried"
            )

        # Update fingerprint
        self._update_fingerprint(rel_path, content_hash, count)

        # Rebuild FTS index — batch callers pass rebuild_fts=False and rebuild
        # once per batch (per-file rebuild is a full-table operation).
        if rebuild_fts:
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
            import re as _re

            # RAG-S2 T2 bug③ (2026-08-09): 结束标记必须是独立的 `---` 行 —
            # 旧 find("---", 3) 命中 frontmatter 值内的任意 "---" 子串
            # (dispute_reason 等自由文本), 半截 YAML 会被当正文送去 embedding。
            end_match = _re.search(r"^---\s*$", content[3:], _re.MULTILINE)
            if end_match is None:
                return fm, body
            end_idx = 3 + end_match.start()
            yaml_str = content[3:end_idx].strip()
            parsed = yaml.safe_load(yaml_str)
            if isinstance(parsed, dict):
                fm = parsed
            body = content[3 + end_match.end() :].lstrip("\n")
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
        subject: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Story 2.8 AC-4: 1-hop wiki-link neighbor expansion.

        For each search result, extract wiki-links and fetch chunks from linked files.
        Neighbor chunks get decayed scores and source_type="neighbor_expansion".

        CARD-G4-4b (BATCH-2026-09-04-第十批): ``subject`` 收口同 vault 内的**跨学科
        泄漏**。此前 where 只有 ``canvas_file LIKE '%<link>%'``, 匹配的是**整张 vault
        表** —— 一条 math 板的笔记只要写了 ``[[物理板]]``, 扩展就会把 physics 板的行
        带回 math 请求的结果里 (真库反例 ``PHYSICS_SECRET``, G4-4 Codex round-2 发现,
        4a 以 xfail(strict) 锁住并移交本卡)。

        语义 (卡文 (h) / D1): subject 非空时, **不匹配的邻居直接丢弃**, 不是「保留但
        不加分」—— 邻居是被**当作检索结果返回**的, 留下来就是泄漏。

        向后兼容 (卡文 (b) / D2): ``subject=None`` (默认) 时 where 与本卡之前**逐字
        相同**, 不加任何子句。主检索链 (``search``/``search_multiple_tables``) 已各自
        传 subject, 本卡不动它们 (D3)。

        Args:
            subject: 可选学科过滤。非空时 where 并入 ``AND subject = '<escaped>'``,
                值经 :meth:`_escape_sql` 转义 (单引号注入不破 where)。
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
            # T3 根治 (2026-07-10): 每次 open_table, 不读缓存句柄
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
                    # CARD-G4-4b: 同 vault 跨 subject 收口。与 _build_where_clause
                    # (:3211) 同一惯用法: 值经 _escape_sql 转义后等值比较。
                    # subject 为 None/空串时不加子句 —— 与本卡之前逐字一致。
                    if subject:
                        where_clause += f" AND subject = '{self._escape_sql(subject)}'"
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
        self,
        current_course: str,
        table_name: str = "vault_notes",
        threshold: float = 0.3,
    ) -> List[str]:
        """
        Story 2.8 AC-5: Find courses with Tag Jaccard similarity above threshold.
        Scans the table for distinct courses and computes Jaccard similarity
        with the current course's tag set.
        """
        if self._db is None:
            return list()

        try:
            # T3 根治 (2026-07-10): 每次 open_table, 不读缓存句柄
            tbl = self._db.open_table(table_name)
            self._tables_cache[table_name] = tbl
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
            # T3 根治 (2026-07-10): 每次 open_table, 不读缓存句柄
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

    # RAG-S2 T3 Step3 (2026-08-09): callout 三级分级表 — 全库 census + 实例抽查定案。
    # 原则: 用户手写/学习痕迹 = 独立成块; 模板生成 = 剥离; 语义正文 = 保留。
    #   EXTRACT — question(用户提问)/error/error-candidate(错题记录): 抽出独立成
    #             chunk, 不混入正文稀释也不被正文淹没
    #   STRIP   — info(白板/模板说明)/video(播放器嵌入模板)/note(模板): 零检索价值
    #   KEEP    — quote(派生起点=节点语义锚)/tip/tips(含用户勾选学习痕迹)/warning/
    #             success/relation; 未知类型默认 KEEP (宁多勿漏)
    _CALLOUT_EXTRACT_TYPES = frozenset({"question", "error", "error-candidate"})
    _CALLOUT_STRIP_TYPES = frozenset({"info", "video", "note"})
    # 插件脚手架模板 callout 标题标记 (node-derivation.ts buildNodeBody 生成;
    # 与 app/services/vault_backfill.py::_TEMPLATE_MARKERS 同构) — 命中即 STRIP,
    # 覆盖类型分级 (该模板用的是 [!tip], 类型级 KEEP 会放走它)。
    _CALLOUT_TEMPLATE_MARKERS = ("💬 围绕这个概念讨论",)

    @staticmethod
    def _process_callouts(text: str) -> tuple:
        """
        RAG-S2 T3 Step3: Obsidian callout 三级分级器 — 对所有 doc_type 生效。

        Returns:
            Tuple of (处理后正文, EXTRACT 抽出的 callout 块列表)。
            KEEP 类型原位保留; STRIP 类型与模板标记 callout 整块移除。
        """
        import re

        head_pattern = re.compile(r"^\s{0,3}>\s*\[!([^\]]+)\][\+\-]?\s*(.*)$")
        lines = text.split("\n")
        kept: List[str] = []
        extracted: List[str] = []
        i = 0
        n = len(lines)
        while i < n:
            m = head_pattern.match(lines[i])
            if not m:
                kept.append(lines[i])
                i += 1
                continue
            # 收集整个 callout 块 (连续 > 开头行; 空行结束 — Obsidian 语义)。
            # Code-Review MEDIUM-1 (2026-08-09): 后续行再命中 callout 头即断块 —
            # 无空行紧贴的 `[!info]`+`[!question]` 若整体按头行分级, STRIP 会
            # 静默吞掉用户批注 (宁多判一个 callout, 不吞用户批注)。
            block_lines = [lines[i]]
            j = i + 1
            while j < n and lines[j].lstrip().startswith(">") and not head_pattern.match(lines[j]):
                block_lines.append(lines[j])
                j += 1
            i = j
            head_line = block_lines[0]
            ctype = m.group(1).strip().lower()
            if any(marker in head_line for marker in LanceDBClient._CALLOUT_TEMPLATE_MARKERS):
                continue  # 模板 callout → STRIP (任何类型)
            if ctype in LanceDBClient._CALLOUT_EXTRACT_TYPES:
                extracted.append("\n".join(block_lines).strip())
                continue
            if ctype in LanceDBClient._CALLOUT_STRIP_TYPES:
                continue
            kept.extend(block_lines)  # KEEP: 原位保留进正文
        return "\n".join(kept), extracted

    @staticmethod
    def _is_boilerplate_section(text: str) -> bool:
        """
        RAG-S2 T3 Step3: section 是否只含模板样板 (是 → 不产 chunk)。

        派生节点脚手架 (node-derivation.ts buildNodeBody) 留下大量零信息骨架 —
        侦察实测 40%+ chunks 是 `## 核心概念` 占位符等模板样板。占位判据:
        全行（你的…）指导语 / [在此填写] / 空 bullet / 水平线。
        """
        import re

        # Code-Review MEDIUM-2 (2026-08-09): 收紧占位判据防误杀 —
        # （你的…）须含模板指导语签名词 (排除用户真实疑问如「（你的意思是…吗？）」);
        # [在此填写] 须整行独占 (排除正文里的字面引用)。
        placeholder_pattern = re.compile(r"^（你的.*(?:精准定义|是什么|为什么重要).*）$|^\[在此填写\]$")
        bare_bullet_pattern = re.compile(r"^[-*+]\s*$")
        hr_pattern = re.compile(r"^(-{3,}|\*{3,}|_{3,})\s*$")
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            if bare_bullet_pattern.match(stripped):
                continue
            if hr_pattern.match(stripped):
                continue
            if placeholder_pattern.search(stripped):
                continue
            return False
        return True

    @staticmethod
    def _strip_whiteboard_boilerplate(body: str) -> str:
        """
        RAG-P0 A4 (2026-05-10): Strip boilerplate from whiteboard (type: whiteboard) body.

        Whiteboards used as MOC/index typically contain ~95% templated content:
          - ```dataviewjs / ```dataview code blocks (auto-generate mermaid graphs)
          - HTML comments (instructions for skills that maintain the file)
          - `## Recent Activity` section (timestamps, no semantic value)
        Only the H1 title + `## Concepts` section + free-form user prose carry
        learning value. This stripper preserves those and removes the rest, so
        when the indexer later chunks the body, it doesn't generate fake
        chunks like "你在这白板里能做什么\\n选中任意文本→Cmd+Shift+D".

        Idempotent: applying twice is equivalent to applying once.
        """
        import re

        # 1. Strip dataviewjs / dataview fenced code blocks
        body = re.sub(
            r"```(?:dataviewjs|dataview)\b.*?```",
            "",
            body,
            flags=re.DOTALL,
        )

        # 2. Strip HTML comments
        body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)

        # 3. Callouts: RAG-S2 T3 (2026-08-09) 起由 _process_callouts 分级器在
        # _flush_section 内统一处理 (whiteboard 的 question 批注同样 EXTRACT,
        # 携带 doc_type=whiteboard 仍被检索默认排除) — 此处不再无差别剥离。

        # 4. Strip `## Recent Activity` section (heading + content through
        # next H2 or EOF). Common in Canvas whiteboards as a timestamp log.
        body = re.sub(
            r"(?m)^##\s+Recent Activity\b.*?(?=^##\s|\Z)",
            "",
            body,
            flags=re.DOTALL,
        )

        return body

    @staticmethod
    def _split_md_by_heading(
        content: str, file_path: str, max_tokens: int = 512, overlap_tokens: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Story 2.3+2.8: 按 Markdown heading 分段文本 + Frontmatter 解析

        一级切分按 H1-H4 heading，二级切分由 _chunk_text() 段落优先+句子降级+原子保护。
        每个 chunk 的 content 前缀注入面包屑路径（文档名 > h1 > h2 > h3；
        RAG-S2 T3: 短块只留文档名），heading_path 数组保存在 chunk dict 中供 metadata 使用。
        Story 2.8: 解析 Frontmatter 提取 course/tags/category。
        RAG-S2 T3 (2026-08-09): callout 三级分级 (EXTRACT/STRIP/KEEP) + 模板样板
        section 不产 chunk + 考察文件 doc_type 推断 exam_board + 行号补 frontmatter 偏移。

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
        # RAG-S2 T3 Step5 (bug②, 2026-08-09): line_start/line_end 旧值基于
        # frontmatter 剥离后的 body 计数, 引用行锚定整体偏移 (实测偏一个
        # frontmatter 的行数)。body 是 content 的后缀, 换行数差 = 被剥离的行数。
        fm_line_offset = content.count("\n") - body.count("\n")
        fm_course = str(frontmatter.get("course", ""))
        fm_tags_raw = frontmatter.get("tags", [])
        if isinstance(fm_tags_raw, list):
            fm_tags_str = ",".join(str(t) for t in fm_tags_raw)
        else:
            fm_tags_str = str(fm_tags_raw)
        fm_category = str(frontmatter.get("category", ""))
        # RAG-P0 A1 (2026-05-10): doc_type from frontmatter.type, default 'note'.
        # Drives source-aware filter/rerank — see _build_where_filters.
        fm_doc_type = str(frontmatter.get("type", "") or "").lower().strip()
        if not fm_doc_type:
            has_exam_key = "exam_question_id" in frontmatter
            if not frontmatter and content.startswith("---"):
                # Code-Review HIGH-1 (2026-08-09): YAML 解析失败时 fm={} —
                # 生产者 exam-quick.ts 写裸标量, 概念名含 YAML 指示符即炸
                # safe_load, 题面泄漏在该路径复活。对原文头部嗅探键名兜底
                # (误判方向保守: 最坏是普通笔记被检索链排除, 信息隔离不破)。
                has_exam_key = bool(re.search(r"(?m)^exam_question_id\s*:", content[:2000]))
            if has_exam_key:
                # RAG-S2 T3 Step1 (2026-08-09): 检验白板考察文件 (节点/考察-*.md)
                # 的 frontmatter 只有 exam_question_id/source_concept/exam_status,
                # 没有 type: 字段 → 旧 fallback "note" 让完整题面以最高权重入索引
                # = 信息隔离旁路 (Karpicke d=1.50)。推断 exam_board 后, hook 链与
                # MCP 链现有的 doc_type NOT IN (...) 排除自动生效; 文件仍在索引,
                # 未来出题链可定向取。显式 type: 仍最优先。
                fm_doc_type = "exam_board"
            else:
                fm_doc_type = "note"

        # RAG-P0 A4 (2026-05-10): whiteboard differential chunking.
        # Strip dataviewjs/HTML comments/callouts/Recent Activity before
        # heading split — these chunks otherwise rank highly via bge-m3 because
        # they contain learning-domain keywords (节点/wikilink/Concepts) but
        # no real semantic value. After A3 default exclude, whiteboard chunks
        # don't surface in search anyway, but stripping here also saves
        # LanceDB storage and force_rebuild time.
        if fm_doc_type == "whiteboard":
            body = LanceDBClient._strip_whiteboard_boilerplate(body)
            # If nothing remains beyond the H1 title, skip the file entirely
            # (heading-only chunks have no embedding value).
            body_after_h1 = re.sub(r"\A\s*#\s+[^\n]+\n*", "", body, count=1).strip()
            if not body_after_h1:
                return []

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
            # RAG-S2 T3 Step3: callout \u4e09\u7ea7\u5206\u7ea7 \u2014 EXTRACT \u7684\u7528\u6237\u6279\u6ce8\u72ec\u7acb\u6210\u5757,
            # STRIP \u7684\u6a21\u677f callout \u5c31\u5730\u79fb\u9664, KEEP \u7684\u7559\u5728\u6b63\u6587
            text, extracted_callouts = LanceDBClient._process_callouts(text)
            breadcrumb = _build_breadcrumb(heading_path)

            def _append_chunk(sub_chunk: str):
                # RAG-S2 T3 Step4: \u9762\u5305\u5c51\u6761\u4ef6\u5316 \u2014 \u77ed\u5757\u5b8c\u6574\u8def\u5f84\u53cd\u5ba2\u4e3a\u4e3b,
                # \u53ea\u7559\u6587\u4ef6\u540d; \u957f\u5757\u4fdd\u6301\u5b8c\u6574\u8def\u5f84 (\u9762\u5305\u5c51\u540c\u65f6\u6807\u6ce8 EXTRACT \u5757\u6765\u6e90)
                if _count_tokens(sub_chunk) < _BREADCRUMB_FULL_MIN_TOKENS:
                    crumb = filename
                else:
                    crumb = breadcrumb
                chunks.append(
                    {
                        "file_path": file_path,
                        "heading": heading,
                        "heading_path": list(heading_path),
                        "content": f"\u6587\u6863\uff1a{crumb}\n\n{sub_chunk}",
                        # RAG-S2 T3 Step5: \u884c\u53f7\u8865 frontmatter \u5360\u884c\u504f\u79fb
                        "line_start": line_start + fm_line_offset,
                        "line_end": line_end + fm_line_offset,
                        # Story 2.8: Frontmatter metadata per chunk
                        "course": fm_course,
                        "tags_str": fm_tags_str,
                        "category": fm_category,
                        # RAG-P0 A1: doc_type for source-aware filtering
                        "doc_type": fm_doc_type,
                    }
                )

            # RAG-S2 T3 Step3: \u6a21\u677f\u6837\u677f section (\u5360\u4f4d\u6587\u672c/\u7a7a bullet \u9aa8\u67b6) \u4e0d\u4ea7 chunk
            if text.strip() and not LanceDBClient._is_boilerplate_section(text):
                for sub_chunk in _chunk_text(text, max_tokens, overlap_tokens):
                    _append_chunk(sub_chunk)
            for callout_block in extracted_callouts:
                if _count_tokens(callout_block) > max_tokens:
                    for sub_chunk in _chunk_text(callout_block, max_tokens, overlap_tokens):
                        _append_chunk(sub_chunk)
                else:
                    _append_chunk(callout_block)

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
        doc_type: Optional[List[str]] = None,
        exclude_doc_types: Optional[List[str]] = None,
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
        table_name = self.resolve_table_name(table_name)
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
                    doc_type=doc_type,
                    exclude_doc_types=exclude_doc_types,
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

        except TableMissingError:
            # CARD-G2-4: 表缺失是**唯一**穿透 enable_fallback 吞噬门的异常。
            # 删掉 B0.7 回退后, 「vault 专属表不存在」不再被裸表兜底; 若这里
            # 仍吞成 [], 调用方拿到的空列表与「索引正常但真没命中」逐字同形,
            # 故障就又一次伪装成健康空 (计划书 :48 legacy fail-open 的本体)。
            # 其余异常 (超时 / 打不开 / 查询报错) 维持旧「任何错 → []」契约,
            # 防止本卡外溢成全链行为变更。
            if LOGURU_ENABLED:
                logger.warning(
                    f"LanceDBClient.search: table '{table_name}' missing — "
                    "propagating TableMissingError (fail-closed, no legacy fallback)"
                )
            raise

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
        doc_type: Optional[List[str]] = None,
        exclude_doc_types: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Story 2.4 AC-5 + RAG-P0 A2: SQL WHERE filter clauses for LanceDB queries.

        Supports canvas_file, subject, course_id (maps to 'course' column),
        tags (maps to 'tags_str' column, OR matching via LIKE), and source-aware
        doc_type include/exclude filtering (RAG-P0 A2, 2026-05-10).

        Column mapping:
        - course_id param → 'course' column
        - tags param → 'tags_str' column (comma-separated tags from frontmatter)
        - doc_type param → 'doc_type' column IN (include mode)
        - exclude_doc_types param → 'doc_type' column NOT IN (exclude mode)
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
        # RAG-P0 A2: doc_type include/exclude. Pre-A1 rows lack the column;
        # we use IS NULL fallback so legacy data degrades to "treat as note"
        # rather than disappearing from result sets.
        if doc_type:
            quoted = ", ".join(f"'{self._escape_sql(t)}'" for t in doc_type)
            if "note" in doc_type:
                clauses.append(f"(doc_type IN ({quoted}) OR doc_type IS NULL)")
            else:
                clauses.append(f"doc_type IN ({quoted})")
        if exclude_doc_types:
            quoted = ", ".join(f"'{self._escape_sql(t)}'" for t in exclude_doc_types)
            clauses.append(f"(doc_type NOT IN ({quoted}) OR doc_type IS NULL)")
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
        doc_type: Optional[List[str]] = None,
        exclude_doc_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """内部搜索实现 (Story 2.4 + RAG-P0 A2: hybrid + course/tags + doc_type filter)"""
        if self._db is None:
            return []

        # 获取表
        # T3 根治 (2026-07-10): 每次 open_table, 不读缓存句柄 — rebuild 后
        # 旧句柄指向已删 dataset, enrich 静默空 (原靠重启容器绕过)
        try:
            table = self._db.open_table(table_name)
            self._tables_cache[table_name] = table
        except Exception as e:
            # CARD-G2-4: 分流「表不存在」与「表在但打不开」。前者是 vault
            # 专属表未建 (删掉 B0.7 回退后唯一的表现形式), 必须让上层看见
            # 并透出 degraded/unavailable; 后者维持 RAG-S2 T6 的旧契约
            # (RuntimeError → search() 外层 enable_fallback 门吞成 [])。
            absent = self._is_table_absent(table_name)
            if LOGURU_ENABLED:
                logger.debug(f"Table {table_name} open failed (absent={absent}): {e}")
            if absent:
                raise TableMissingError(table_name, f"open_table failed: {e}") from e
            # RAG-S2 T6 审查修复 (2026-08-10): 表打不开是基础设施故障不是
            # 合法空 — raise 让 search() 外层 enable_fallback 门决定吞或抛
            # (enable_fallback=True 调用方在外层照旧吞成 [], 行为不变;
            # False 的调用方 [MCP fast/hook singleton] 得到诚实 error)。
            raise RuntimeError(f"open_table('{table_name}') failed: {e}") from e

        # Story 2.4 AC-5 + RAG-P0 A2: Build pre-filter clauses
        where_clauses = self._build_where_filters(
            canvas_file=canvas_file,
            subject=subject,
            course_id=course_id,
            tags=tags,
            doc_type=doc_type,
            exclude_doc_types=exclude_doc_types,
        )

        # RAG-P0 A5 v2 schema guard (2026-05-11) — drop clauses referencing
        # columns not present in this table's schema. Without this, LanceDB
        # raises LanceError(Schema): No field named X → entire branch fails
        # silently (try/except below returns []). Legacy tables (vault_notes,
        # canvas_vault_vault_notes pre-RAG-P0) lack the 'doc_type' column;
        # the IS NULL fallback in _build_where_filters does NOT help because
        # IS NULL still requires the column to exist in the schema.
        try:
            schema_columns = {f.name for f in table.schema}
            missing_in_schema = []
            for col in ("doc_type", "course", "tags_str"):
                if col not in schema_columns:
                    missing_in_schema.append(col)
            if missing_in_schema:
                filtered = [c for c in where_clauses if not any(col in c for col in missing_in_schema)]
                if len(filtered) < len(where_clauses) and LOGURU_ENABLED:
                    logger.debug(
                        f"[schema-guard] table '{table_name}' missing columns "
                        f"{missing_in_schema}; dropped "
                        f"{len(where_clauses) - len(filtered)} filter clause(s)"
                    )
                where_clauses = filtered
        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"[schema-guard] schema introspection failed: {e}")

        # Accumulator for raw results across branches
        all_raw: List[Dict[str, Any]] = list()

        # RAG-S2 T6 审查修复 (2026-08-10): 分支异常收集 — 此前所有查询分支
        # 异常都被就地吞成 [], 「全分支故障」与「查了但真没有」在返回值上
        # 不可区分, enable_fallback=False 的诚实 error 契约被架空 (T5 HIGH-1
        # 只锁住了 search() 外层)。规则: 最终结果为空 且 有分支异常 且 无
        # 任何分支成功执行 (成功含合法空) → raise; 单分支失败但另一分支
        # 成功的设计性降级保持不变。
        branch_errors: List[str] = []
        branch_ok = False

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
                    branch_ok = True
                except Exception as e:
                    branch_errors.append(f"hybrid-vector: {str(e)[:80]}")
                    if LOGURU_ENABLED:
                        logger.debug(f"Hybrid vector branch failed: {e}")
            else:
                branch_errors.append("hybrid-vector: query embedding unavailable")

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
                branch_ok = True
            except Exception as e:
                # FTS unavailable (no index yet, no content_tokenized column, etc.)
                # Hybrid degrades to Dense-only — still returns results via vector branch
                branch_errors.append(f"hybrid-fts: {str(e)[:80]}")
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
                branch_ok = True
            except Exception as e:
                branch_errors.append(f"vector: {str(e)[:80]}")
                if LOGURU_ENABLED:
                    logger.error(f"LanceDB vector search failed: {e}")
        else:
            branch_errors.append("vector: query embedding unavailable")
            if LOGURU_ENABLED:
                logger.warning("[search] No query vector available")

        # T6 审查修复: 全分支故障 → raise (由 search() 外层 enable_fallback
        # 门决定吞或抛); 有任一分支成功执行过的空结果仍是合法空。
        if not all_raw and branch_errors and not branch_ok:
            raise RuntimeError("all search branches failed: " + " | ".join(branch_errors[:3]))

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
        """Reciprocal Rank Fusion — merge vector and FTS results.

        R1 止血 (2026-07-12 对抗审查): RRF 融合分只决定**排序**, 不再覆盖
        `_distance`。旧实现 `_distance = 1 - rrf_score` 把语义信号压缩进
        (0.50, 0.508] 窄带 —— 下游 min_relevance 过滤在数学上失效, 任何
        查询 (含零相关) 都注入满额材料。现在:
        - vector 通道命中: 保留原始 cosine `_distance` (真实语义幅度)
        - FTS-only 命中 (vector 未确认): `_distance` 设 1.1 (score≈0.476,
          低于 0.50 门槛) —— 第一版给过 0.35 特权值, 真机翻车: 英文
          stop words (how/do/at) 在英文转录语料里海量 BM25 命中, 烤面包
          查询照样注入 10 条 + 虚高分触发 elbow 假悬崖砍掉真 vector 命中。
          纯词面命中不是强信号, **双通道确认才是** (那时用 vector 真实距离,
          FTS 贡献体现在 RRF 排序加成)。
        - 融合排名放 `_rrf_score` 供调试/观测
        """
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
                # FTS-only 命中 (vector 未确认) — 见 docstring: 不给特权,
                # 1.1 → score≈0.476 低于门槛, 不进自动注入
                fts_doc = r.copy()
                if fts_doc.get("_distance") is None:
                    fts_doc["_distance"] = 1.1
                fts_doc["_fts_only"] = True
                doc_map[doc_id] = fts_doc
            # RAG-S2 T6 审查修复 (2026-08-10): 显式记录 FTS 通道成员资格 —
            # 此前下游用 bool(_rrf_score) 当「双通道确认」, 但 _rrf_score 写给
            # **所有**融合行 (含 dense-only), 名实颠倒: dense-only 恒 True、
            # 真词法命中 (FTS-only) 反而 False。_fts_hit = 出现在 FTS 结果中;
            # 双通道确认 = _fts_hit and not _fts_only (消费端组合)。
            doc_map[doc_id]["_fts_hit"] = True
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        results = []
        for doc_id, rrf_score in ranked:
            doc = doc_map[doc_id].copy()
            doc["_rrf_score"] = rrf_score
            # _distance 保留通道原始值 (vector=cosine 距离 / FTS-only=0.35);
            # 极端兜底: 两边都没有 _distance 时给中性值防 KeyError
            if doc.get("_distance") is None:
                doc["_distance"] = 0.5
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
                # RAG-P0 A1: doc_type for source-aware filter/rerank
                "doc_type",
                # RAG-S2 T2 (2026-08-09): retrieval_confidence 地基 — RRF 融合
                # 信号此前被本白名单丢弃, 下游无法区分「双通道确认」与
                # 「dense-only 命中」(confidence 最强的一维, 零成本透传)。
                "_rrf_score",
                "_fts_only",
                # RAG-S2 T6: FTS 通道成员资格 (fts_confirmed 名实修复) —
                # _rrf_score 不承载通道信息, 双通道判定改用 _fts_hit
                "_fts_hit",
            ]:
                if key in item:
                    metadata[key] = item[key]

            # Story 2.8/2.9: Propagate source_type to top-level metadata
            if "_source_type" in item:
                metadata["source_type"] = item["_source_type"]
            elif "source_type" in item:
                metadata["source_type"] = item["source_type"]

            search_results.append(
                {
                    "doc_id": doc_id,
                    "content": content,
                    "score": score,
                    "metadata": metadata,
                }
            )

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
        Story 2.3 Task 6 + RAG-P0 A5 (2026-05-10): Detect schema drift and
        auto drop+recreate. Triggers on:
          - vector dimension mismatch (e.g. 384d → 1024d on bge-m3 upgrade)
          - missing 'doc_type' column (RAG-P0 A1 added this column;
            pre-A1 tables lack it and would reject inserts that include it)

        Args:
            table_name: LanceDB table name.
            new_vector_dim: Expected vector dimension (e.g. 1024 for bge-m3).

        Returns:
            True if the table was dropped (caller should create new). False
            if schema matches or table doesn't exist.
        """
        if self._db is None:
            return False

        try:
            # T3 根治 (2026-07-10): 存在性/句柄都以 db 为准, 不读缓存
            if table_name not in self._db.table_names():
                return False
            tbl = self._db.open_table(table_name)
            # Sample first row to inspect vector dimension
            rows = tbl.head(1).to_pydict()
            vectors = rows.get("vector", [])
            if not vectors or len(vectors) == 0:
                return False

            existing_dim = len(vectors[0])
            dim_mismatch = existing_dim != new_vector_dim

            # RAG-P0 A5: detect missing doc_type column on pre-A1 tables.
            # Use schema reflection rather than row-level inspection so that
            # tables with empty doc_type values still register as compliant.
            doc_type_missing = False
            try:
                col_names = set(tbl.schema.names)
                doc_type_missing = "doc_type" not in col_names
            except Exception:
                # Schema reflection failure is non-fatal — fall back to
                # row inspection
                doc_type_missing = "doc_type" not in rows

            if not dim_mismatch and not doc_type_missing:
                return False

            # Schema drift detected — drop table
            if LOGURU_ENABLED:
                reasons = []
                if dim_mismatch:
                    reasons.append(f"vector dim {existing_dim}!={new_vector_dim}")
                if doc_type_missing:
                    reasons.append("missing 'doc_type' column (pre-RAG-P0)")
                logger.warning(
                    f"[SCHEMA] Drift in '{table_name}': {', '.join(reasons)}. Dropping table for recreation."
                )

            self._db.drop_table(table_name, ignore_missing=True)
            self._tables_cache.pop(table_name, None)
            return True

        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"[SCHEMA] Schema check failed for '{table_name}': {e}")
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
        table_name = self.resolve_table_name(table_name)
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
                    # RAG-P0 A1: doc_type column
                    "doc_type",
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
            # T3 根治 (2026-07-10): 守卫改为 db 权威存在性 (缓存命中 ≠ 表存在)
            if data and table_name in self._db.table_names():
                sample_vector = data[0].get("vector")
                if sample_vector is not None:
                    self._check_and_fix_dimension_mismatch(table_name, len(sample_vector))

            # 检查表是否存在
            # T3 根治 (2026-07-10): 存在性用 table_names() 权威判断, 不再以
            # 缓存命中为准 — 原逻辑对"表存在但不在本实例缓存"会误走
            # create_table 抛错; rebuild 后缓存句柄也已失效
            if table_name in self._db.table_names():
                table = self._db.open_table(table_name)
                self._tables_cache[table_name] = table
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

                return {
                    "count": count,
                    "last_indexed": last_indexed,
                    "subject": subject,
                }
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
