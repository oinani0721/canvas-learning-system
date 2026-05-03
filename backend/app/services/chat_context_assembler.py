"""Story 2.1 Task 2 — ChatContextAssembler + token 预算压缩。

实施 AC #2（LLM 上下文组装）+ AC #3（token 预算压缩 + 公式/代码块保护）。

使用 tiktoken cl100k_base 编码（Claude 3.5 兼容，已在 backend deps）。

优先级（AC #3）：
  1. 当前笔记全文（最高 — 不可压缩）
  2. 1-hop 邻居 frontmatter + Tips + errors
  3. 1-hop 邻居内容摘要
  4. 2-hop 邻居 frontmatter
  5. 2-hop 邻居内容（最低）

公式保护：
  - LaTeX 块 ($$...$$ / $...$) 视为 atomic
  - 代码块 (```...```) 视为 atomic
  - 压缩时整块保留或整块丢弃，绝不破坏内部结构
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.services.wikilink_context_service import WikilinkNeighborContext

logger = structlog.get_logger(__name__)

DEFAULT_TOKEN_BUDGET = 8192
DEFAULT_ENCODING = "cl100k_base"
ENV_TOKEN_BUDGET = "CHAT_CONTEXT_TOKEN_BUDGET"

ATOMIC_PATTERNS = [
    re.compile(r"```[\s\S]*?```", re.MULTILINE),
    re.compile(r"\$\$[\s\S]*?\$\$"),
    re.compile(r"\$[^\n$]+\$"),
]
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？.!?\n])")


@dataclass
class CurrentNoteContext:
    """当前笔记上下文（assemble_context 输入）。"""

    path: str
    content: str
    frontmatter: dict[str, Any] = field(default_factory=dict)


@dataclass
class AssembledContext:
    """组装结果。"""

    text: str
    used_tokens: int
    budget: int
    truncated: bool = False
    sections_included: list[str] = field(default_factory=list)


def _resolve_token_budget(override: int | None = None) -> int:
    if override is not None and override > 0:
        return override
    env_val = os.environ.get(ENV_TOKEN_BUDGET)
    if env_val and env_val.isdigit():
        return int(env_val)
    return DEFAULT_TOKEN_BUDGET


class _TokenCounter:
    """tiktoken 包装（fallback 到 chars/4 估算）。"""

    def __init__(self, encoding_name: str = DEFAULT_ENCODING) -> None:
        self._encoding = None
        try:
            import tiktoken

            self._encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(
                "chat_context.tiktoken_unavailable",
                error=str(e),
                fallback="chars_div_4",
            )

    def count(self, text: str) -> int:
        if self._encoding is not None:
            return len(self._encoding.encode(text))
        return max(1, len(text) // 4)


def _extract_atomic_blocks(text: str) -> tuple[str, list[str]]:
    """提取 atomic 块（公式 / 代码块）替换为 placeholder。

    Returns:
        (placeholder_text, atomic_blocks_list)
    """
    atomic_blocks: list[str] = []

    def replace_atom(match: re.Match[str]) -> str:
        idx = len(atomic_blocks)
        atomic_blocks.append(match.group(0))
        return f"<<ATOM_{idx}>>"

    placeholder_text = text
    for pattern in ATOMIC_PATTERNS:
        placeholder_text = pattern.sub(replace_atom, placeholder_text)
    return placeholder_text, atomic_blocks


def _restore_atomic_blocks(text: str, atomic_blocks: list[str]) -> str:
    out = text
    for idx, block in enumerate(atomic_blocks):
        out = out.replace(f"<<ATOM_{idx}>>", block)
    return out


def _drop_orphan_placeholders(text: str) -> str:
    return re.sub(r"<<ATOM_\d+>>", "", text)


class ChatContextAssembler:
    """Story 2.1 Task 2 — LLM 上下文组装 + token 预算压缩。"""

    def __init__(
        self,
        token_budget: int | None = None,
        encoding_name: str = DEFAULT_ENCODING,
    ) -> None:
        self.budget = _resolve_token_budget(token_budget)
        self._counter = _TokenCounter(encoding_name)

    def count_tokens(self, text: str) -> int:
        return self._counter.count(text)

    def compress_content(self, text: str, max_tokens: int) -> str:
        """按句子边界压缩，atomic 块整块保留或整块丢弃（AC #3 公式保护）。"""
        if max_tokens <= 0:
            return ""
        if self.count_tokens(text) <= max_tokens:
            return text

        placeholder_text, atomic_blocks = _extract_atomic_blocks(text)
        sentences = [s for s in SENTENCE_SPLIT_PATTERN.split(placeholder_text) if s]

        out_parts: list[str] = []
        used = 0
        for sentence in sentences:
            restored = _restore_atomic_blocks(sentence, atomic_blocks)
            sentence_tokens = self.count_tokens(restored)
            if used + sentence_tokens > max_tokens:
                break
            out_parts.append(restored)
            used += sentence_tokens

        result = "".join(out_parts)
        result = _drop_orphan_placeholders(result)
        return result.rstrip()

    def _format_neighbor_metadata(
        self, neighbor: WikilinkNeighborContext
    ) -> str:
        """格式化 1-hop / 2-hop frontmatter + Tips + errors（高密度小段）。"""
        lines: list[str] = []
        lines.append(f"### [[{neighbor.slug}]] (hop={neighbor.hop_distance})")
        if neighbor.relationship_type:
            lines.append(f"- 关系: {neighbor.relationship_type}")
        fm = neighbor.frontmatter
        if isinstance(fm.get("type"), str):
            lines.append(f"- 类型: {fm['type']}")
        if isinstance(fm.get("mastery_score"), (int, float)):
            lines.append(f"- Mastery: {fm['mastery_score']:.2f}")
        tips = fm.get("tips")
        if isinstance(tips, list) and tips:
            preview = "; ".join(str(t)[:80] for t in tips[:3])
            lines.append(f"- Tips: {preview}")
        errors = fm.get("errors")
        if isinstance(errors, list) and errors:
            preview = "; ".join(str(e)[:80] for e in errors[:3])
            lines.append(f"- Errors: {preview}")
        return "\n".join(lines)

    def _format_neighbor_summary(
        self, neighbor: WikilinkNeighborContext, max_chars: int = 200
    ) -> str:
        """格式化邻居内容摘要。"""
        if not neighbor.content_summary:
            return ""
        snippet = neighbor.content_summary[:max_chars]
        return f"### [[{neighbor.slug}]] 摘要\n{snippet}"

    def assemble_context(
        self,
        current_note: CurrentNoteContext,
        neighbors: list[WikilinkNeighborContext],
        token_budget: int | None = None,
    ) -> AssembledContext:
        """按优先级填充 token 预算（AC #2 + AC #3）。"""
        budget = _resolve_token_budget(token_budget) if token_budget is not None else self.budget
        sections_included: list[str] = []
        truncated = False

        one_hop = [n for n in neighbors if n.hop_distance == 1]
        two_hop = [n for n in neighbors if n.hop_distance >= 2]

        # Priority 1 — 当前笔记全文（不可压缩）
        current_section = (
            f"# 当前笔记: {current_note.path}\n\n{current_note.content}"
        )
        used = self.count_tokens(current_section)
        if used > budget:
            current_section = self.compress_content(current_section, budget)
            used = self.count_tokens(current_section)
            truncated = True
        sections_included.append("current_note")
        parts: list[str] = [current_section]

        # Priority 2 — 1-hop frontmatter + Tips + errors
        if one_hop:
            block_lines = ["\n## 1-hop 邻居 (frontmatter / Tips / errors)"]
            for n in one_hop:
                block_lines.append(self._format_neighbor_metadata(n))
            block = "\n\n".join(block_lines)
            block_tokens = self.count_tokens(block)
            if used + block_tokens <= budget:
                parts.append(block)
                used += block_tokens
                sections_included.append("1hop_fm_tips_errors")
            else:
                truncated = True

        # Priority 3 — 1-hop 内容摘要
        if one_hop and used < budget:
            summaries = [
                self._format_neighbor_summary(n) for n in one_hop if n.content_summary
            ]
            if summaries:
                block = "\n## 1-hop 邻居摘要\n\n" + "\n\n".join(summaries)
                budget_left = budget - used
                if self.count_tokens(block) <= budget_left:
                    parts.append(block)
                    used += self.count_tokens(block)
                    sections_included.append("1hop_summary")
                else:
                    compressed = self.compress_content(block, budget_left)
                    if compressed:
                        parts.append(compressed)
                        used += self.count_tokens(compressed)
                        sections_included.append("1hop_summary_compressed")
                        truncated = True

        # Priority 4 — 2-hop frontmatter
        if two_hop and used < budget:
            block_lines = ["\n## 2-hop 邻居 (frontmatter)"]
            for n in two_hop:
                block_lines.append(self._format_neighbor_metadata(n))
            block = "\n\n".join(block_lines)
            budget_left = budget - used
            if self.count_tokens(block) <= budget_left:
                parts.append(block)
                used += self.count_tokens(block)
                sections_included.append("2hop_fm")
            else:
                truncated = True

        # Priority 5 — 2-hop 内容摘要
        if two_hop and used < budget:
            summaries = [
                self._format_neighbor_summary(n) for n in two_hop if n.content_summary
            ]
            if summaries:
                block = "\n## 2-hop 邻居摘要\n\n" + "\n\n".join(summaries)
                budget_left = budget - used
                if self.count_tokens(block) <= budget_left:
                    parts.append(block)
                    used += self.count_tokens(block)
                    sections_included.append("2hop_summary")
                else:
                    truncated = True

        text = "\n".join(parts)
        return AssembledContext(
            text=text,
            used_tokens=used,
            budget=budget,
            truncated=truncated,
            sections_included=sections_included,
        )
