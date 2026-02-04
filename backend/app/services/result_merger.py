# Canvas Learning System - Result Merger Service
# Story 33.7: Result Merging Strategies
# ✅ Implements AC1-AC6: Supplementary, Hierarchical, Voting strategies
"""
Result Merger Service for multi-Agent batch processing outputs.

Implements three merge strategies:
- Supplementary (补充式): Concatenates all outputs with separators
- Hierarchical (层级式): Organizes by difficulty level
- Voting (投票式): Deduplicates and keeps most relevant

[Source: docs/stories/33.7.story.md]
[Source: docs/architecture/decisions/0004-async-execution-engine.md - async def merge()]
"""

import logging
import os
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List, Optional, Type

from ..models.merge_strategy_models import (
    AgentResult,
    DifficultyLevel,
    MergeConfig,
    MergeOptions,
    MergeRequest,
    MergeResult,
    MergeStrategyType,
    QualityScore,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# [Source: docs/stories/33.7.story.md - AC4, Implementation Notes]
# ═══════════════════════════════════════════════════════════════════════════════

def load_merge_config() -> MergeConfig:
    """
    Load merge configuration from environment variables.

    Environment variables:
    - MERGE_STRATEGY: Default strategy (supplementary|hierarchical|voting)
    - MERGE_QUALITY_THRESHOLD: Warning threshold (0-100, default 60)

    [Source: docs/stories/33.7.story.md - AC4]
    """
    strategy_str = os.getenv("MERGE_STRATEGY", "supplementary").lower()
    try:
        strategy = MergeStrategyType(strategy_str)
    except ValueError:
        logger.warning(
            f"Invalid MERGE_STRATEGY '{strategy_str}', using default 'supplementary'"
        )
        strategy = MergeStrategyType.supplementary

    threshold_str = os.getenv("MERGE_QUALITY_THRESHOLD", "60")
    try:
        threshold = int(threshold_str)
        if not 0 <= threshold <= 100:
            raise ValueError("out of range")
    except ValueError:
        logger.warning(
            f"Invalid MERGE_QUALITY_THRESHOLD '{threshold_str}', using default 60"
        )
        threshold = 60

    return MergeConfig(
        default_strategy=strategy,
        quality_threshold=threshold,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Difficulty Keywords Mapping
# [Source: docs/stories/33.7.story.md - Technical Details]
# ═══════════════════════════════════════════════════════════════════════════════

DIFFICULTY_KEYWORDS: Dict[DifficultyLevel, List[str]] = {
    DifficultyLevel.beginner: ["什么是", "定义", "基础", "入门", "简单", "概念", "初步", "基本"],
    DifficultyLevel.intermediate: ["为什么", "如何", "原理", "应用", "进阶", "实践", "方法"],
    DifficultyLevel.advanced: ["深入", "高级", "复杂", "优化", "深度", "详解", "分析"],
    DifficultyLevel.expert: ["前沿", "研究", "创新", "理论", "学术", "专家", "论文"],
}

DIFFICULTY_ORDER = [
    DifficultyLevel.beginner,
    DifficultyLevel.intermediate,
    DifficultyLevel.advanced,
    DifficultyLevel.expert,
]


# ═══════════════════════════════════════════════════════════════════════════════
# Quality Scorer
# [Source: docs/stories/33.7.story.md - AC5, Task 6]
# ═══════════════════════════════════════════════════════════════════════════════

class QualityScorer:
    """
    Quality scorer for merged results.

    Metrics:
    - Coverage: Source content key concepts in merged result (0-100)
    - Redundancy: Duplicate content ratio (0-100, lower is better)
    - Coherence: Paragraph flow and logical connection (0-100)

    [Source: docs/stories/33.7.story.md - AC5, Task 6]
    """

    # Transition words for coherence scoring (Chinese)
    TRANSITION_WORDS = [
        "因此", "所以", "然而", "但是", "而且", "另外", "此外",
        "首先", "其次", "最后", "总之", "例如", "比如", "换句话说",
        "综上所述", "一方面", "另一方面", "相反", "同样", "类似地",
    ]

    def calculate_coverage(
        self,
        merged: str,
        sources: List[str],
    ) -> float:
        """
        Calculate coverage score: key concepts from sources appearing in merged.

        [Source: docs/stories/33.7.story.md - Technical Details > Quality Scoring Algorithm]
        """
        if not sources or not merged:
            return 0.0

        # Extract key concepts (nouns and noun phrases) from sources
        all_concepts = set()
        for source in sources:
            # Simple extraction: words of 2+ characters (likely meaningful)
            words = re.findall(r'[\u4e00-\u9fff]{2,}', source)
            all_concepts.update(words)

        if not all_concepts:
            return 100.0  # No concepts to cover

        # Check how many appear in merged
        covered = sum(1 for concept in all_concepts if concept in merged)
        return min(100.0, (covered / len(all_concepts)) * 100)

    def calculate_redundancy(
        self,
        merged: str,
        sources: List[str],
    ) -> float:
        """
        Calculate redundancy score: duplicate content ratio (lower is better).

        [Source: docs/stories/33.7.story.md - Technical Details > Quality Scoring Algorithm]
        """
        if not merged or len(sources) <= 1:
            return 0.0

        # Simple approach: check for repeated sentences/phrases
        sentences = re.split(r'[。！？\n]', merged)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not sentences:
            return 0.0

        # Count duplicates
        seen = set()
        duplicates = 0
        for sentence in sentences:
            if sentence in seen:
                duplicates += 1
            else:
                seen.add(sentence)

        return min(100.0, (duplicates / len(sentences)) * 100)

    def calculate_coherence(
        self,
        merged: str,
    ) -> float:
        """
        Calculate coherence score: transition words density.

        [Source: docs/stories/33.7.story.md - Technical Details > Quality Scoring Algorithm]
        """
        if not merged:
            return 0.0

        # Count paragraphs (separated by double newlines or section headers)
        paragraphs = re.split(r'\n\n+|^##', merged)
        paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 20]
        paragraph_count = max(1, len(paragraphs))

        # Count transition words
        transition_count = sum(
            merged.count(word) for word in self.TRANSITION_WORDS
        )

        # Coherence = transition density (capped at 100)
        # Ideal: ~0.5-1 transition per paragraph
        coherence = min(100.0, (transition_count / paragraph_count) * 50)

        # Bonus for having multiple paragraphs with good flow
        if paragraph_count >= 3 and transition_count >= 2:
            coherence = min(100.0, coherence + 20)

        return coherence

    def calculate(
        self,
        merged: str,
        sources: List[str],
        config: Optional[MergeConfig] = None,
    ) -> QualityScore:
        """
        Calculate overall quality score.

        [Source: docs/stories/33.7.story.md - AC5]
        """
        coverage = self.calculate_coverage(merged, sources)
        redundancy = self.calculate_redundancy(merged, sources)
        coherence = self.calculate_coherence(merged)

        score = QualityScore.calculate(coverage, redundancy, coherence)

        # Log warning if quality is low
        threshold = config.quality_threshold if config else 60
        if score.overall < threshold:
            logger.warning(
                f"Low merge quality score: {score.overall:.1f} < {threshold} "
                f"(coverage={coverage:.1f}, redundancy={redundancy:.1f}, coherence={coherence:.1f})"
            )

        return score


# ═══════════════════════════════════════════════════════════════════════════════
# Abstract Base Class
# [Source: docs/stories/33.7.story.md - Task 2]
# [Source: docs/architecture/decisions/0004-async-execution-engine.md]
# ═══════════════════════════════════════════════════════════════════════════════

class ResultMerger(ABC):
    """
    Abstract base class for result merging strategies.

    All merge operations are async per ADR-0004.

    [Source: docs/stories/33.7.story.md - Task 2]
    [Source: docs/architecture/decisions/0004-async-execution-engine.md#L125-L130]
    """

    def __init__(self, config: Optional[MergeConfig] = None):
        """Initialize merger with optional configuration."""
        self.config = config or load_merge_config()
        self.scorer = QualityScorer()

    @property
    @abstractmethod
    def strategy_type(self) -> MergeStrategyType:
        """Return the strategy type this merger implements."""
        pass

    @abstractmethod
    async def merge(
        self,
        results: List[AgentResult],
        options: Optional[MergeOptions] = None,
    ) -> MergeResult:
        """
        Merge multiple Agent results into a single cohesive output.

        Args:
            results: List of AgentResult from batch processing
            options: Optional merge configuration

        Returns:
            MergeResult with merged content and quality score

        [Source: docs/stories/33.7.story.md - Task 2]
        """
        pass

    def _filter_successful(self, results: List[AgentResult]) -> List[AgentResult]:
        """Filter to only successful results."""
        return [r for r in results if r.success and r.result]

    def _handle_empty_input(
        self,
        original_count: int = 0,
        failed_count: int = 0,
    ) -> MergeResult:
        """
        Handle empty input edge case.

        [Source: docs/stories/33.7.story.md - Task 2]
        Return empty MergeResult with quality_score=0 when input list is empty.
        """
        result = MergeResult.empty(self.strategy_type)
        result.source_count = original_count
        result.failed_sources = failed_count
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# Supplementary Strategy (补充式)
# [Source: docs/stories/33.7.story.md - AC1, Task 3]
# ═══════════════════════════════════════════════════════════════════════════════

class SupplementaryMerger(ResultMerger):
    """
    Supplementary merge strategy: concatenates all outputs with separators.

    - Preserves complete content from each Agent
    - Adds clear section separators between Agent outputs
    - Includes source Agent attribution for each section

    [Source: docs/stories/33.7.story.md - AC1, Task 3]
    """

    AGENT_EMOJIS = {
        "oral-explanation": "🎙️",
        "comparison-table": "📊",
        "memory-anchor": "🎯",
        "four-level-explanation": "📚",
        "clarification-path": "🛤️",
        "basic-decomposition": "🧩",
        "deep-decomposition": "🔬",
        "example-teaching": "📝",
        "scoring-agent": "⭐",
        "verification-question-agent": "❓",
        "question-decomposition": "🎓",
        "canvas-orchestrator": "🎨",
    }

    @property
    def strategy_type(self) -> MergeStrategyType:
        return MergeStrategyType.supplementary

    async def merge(
        self,
        results: List[AgentResult],
        options: Optional[MergeOptions] = None,
    ) -> MergeResult:
        """
        Concatenate all results with separators and attribution.

        [Source: docs/stories/33.7.story.md - AC1]
        """
        # Handle empty input
        if not results:
            return self._handle_empty_input()

        successful = self._filter_successful(results)
        failed_count = len(results) - len(successful)
        if not successful:
            return self._handle_empty_input(len(results), failed_count)

        options = options or MergeOptions()
        sections = []

        for result in successful:
            if options.include_attribution:
                emoji = self.AGENT_EMOJIS.get(result.agent_name, "📘")
                header = f"## {emoji} {result.agent_name} 解释\n"
                sections.append(header + result.result)
            else:
                sections.append(result.result)

        # Join with separator
        separator = "\n\n---\n\n" if options.preserve_formatting else "\n\n"
        merged_content = separator.join(sections)

        # Truncate if needed
        if options.max_content_length and len(merged_content) > options.max_content_length:
            merged_content = merged_content[:options.max_content_length] + "\n\n...(内容已截断)"

        # Calculate quality
        source_texts = [r.result for r in successful]
        quality_score = self.scorer.calculate(merged_content, source_texts, self.config)

        return MergeResult(
            merged_content=merged_content,
            strategy_used=self.strategy_type,
            source_count=len(results),
            quality_score=quality_score,
            successful_sources=len(successful),
            failed_sources=len(results) - len(successful),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Hierarchical Strategy (层级式)
# [Source: docs/stories/33.7.story.md - AC2, Task 4]
# ═══════════════════════════════════════════════════════════════════════════════

class HierarchicalMerger(ResultMerger):
    """
    Hierarchical merge strategy: organizes by difficulty level.

    - Sort order: Beginner (入门) → Intermediate (进阶) → Advanced (深入) → Expert (专家)
    - Auto-detect content difficulty based on keywords/complexity
    - Group related content from different Agents by difficulty tier

    [Source: docs/stories/33.7.story.md - AC2, Task 4]
    """

    TIER_HEADERS = {
        DifficultyLevel.beginner: "## 🌱 入门级 (Beginner)",
        DifficultyLevel.intermediate: "## 🌿 进阶级 (Intermediate)",
        DifficultyLevel.advanced: "## 🌲 深入级 (Advanced)",
        DifficultyLevel.expert: "## 🌳 专家级 (Expert)",
    }

    @property
    def strategy_type(self) -> MergeStrategyType:
        return MergeStrategyType.hierarchical

    def _detect_difficulty(self, text: str) -> DifficultyLevel:
        """
        Detect content difficulty based on keyword analysis.

        [Source: docs/stories/33.7.story.md - Task 4]
        """
        scores = {level: 0 for level in DifficultyLevel}

        for level, keywords in DIFFICULTY_KEYWORDS.items():
            for keyword in keywords:
                scores[level] += text.count(keyword)

        # Also consider text complexity (average sentence length)
        sentences = re.split(r'[。！？]', text)
        avg_length = sum(len(s) for s in sentences) / max(1, len(sentences))

        # Longer sentences suggest more advanced content
        if avg_length > 50:
            scores[DifficultyLevel.advanced] += 2
            scores[DifficultyLevel.expert] += 1
        elif avg_length > 30:
            scores[DifficultyLevel.intermediate] += 1

        # Find max score level
        max_score = max(scores.values())
        if max_score == 0:
            return DifficultyLevel.intermediate  # Default

        for level in DIFFICULTY_ORDER:
            if scores[level] == max_score:
                return level

        return DifficultyLevel.intermediate

    async def merge(
        self,
        results: List[AgentResult],
        options: Optional[MergeOptions] = None,
    ) -> MergeResult:
        """
        Organize results by difficulty level.

        [Source: docs/stories/33.7.story.md - AC2]
        """
        if not results:
            return self._handle_empty_input()

        successful = self._filter_successful(results)
        failed_count = len(results) - len(successful)
        if not successful:
            return self._handle_empty_input(len(results), failed_count)

        options = options or MergeOptions()

        # Group by difficulty
        grouped: Dict[DifficultyLevel, List[AgentResult]] = defaultdict(list)
        for result in successful:
            level = self._detect_difficulty(result.result)
            grouped[level].append(result)

        # Build merged content in order
        sections = []
        for level in DIFFICULTY_ORDER:
            if level not in grouped or not grouped[level]:
                continue

            header = self.TIER_HEADERS[level]
            sections.append(header)

            for result in grouped[level]:
                if options.include_attribution:
                    sections.append(f"### 来自 {result.agent_name}")
                sections.append(result.result)

        merged_content = "\n\n".join(sections)

        # Truncate if needed
        if options.max_content_length and len(merged_content) > options.max_content_length:
            merged_content = merged_content[:options.max_content_length] + "\n\n...(内容已截断)"

        # Calculate quality
        source_texts = [r.result for r in successful]
        quality_score = self.scorer.calculate(merged_content, source_texts, self.config)

        return MergeResult(
            merged_content=merged_content,
            strategy_used=self.strategy_type,
            source_count=len(results),
            quality_score=quality_score,
            successful_sources=len(successful),
            failed_sources=len(results) - len(successful),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Voting Strategy (投票式)
# [Source: docs/stories/33.7.story.md - AC3, Task 5]
# ═══════════════════════════════════════════════════════════════════════════════

class VotingMerger(ResultMerger):
    """
    Voting merge strategy: deduplicates and keeps most relevant content.

    - Detect semantic duplicates using text similarity (TF-IDF cosine ≥0.8)
    - Keep content with highest information density
    - Merge overlapping explanations into single comprehensive version

    [Source: docs/stories/33.7.story.md - AC3, Task 5]
    """

    @property
    def strategy_type(self) -> MergeStrategyType:
        return MergeStrategyType.voting

    def _simple_tokenize(self, text: str) -> List[str]:
        """
        Simple Chinese tokenization without jieba dependency.

        Falls back to character-level if jieba not available.
        """
        try:
            import jieba
            return list(jieba.cut(text))
        except ImportError:
            # Fallback: extract Chinese words (2+ chars) and keep single chars
            words = re.findall(r'[\u4e00-\u9fff]+', text)
            return words

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.

        Uses TF-IDF vectorization if scikit-learn available,
        otherwise falls back to Jaccard similarity.

        [Source: docs/stories/33.7.story.md - Task 5]
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            # Use custom tokenizer
            def tokenizer(text: str) -> List[str]:
                return self._simple_tokenize(text)

            vectorizer = TfidfVectorizer(
                tokenizer=tokenizer,
                max_features=5000,
                ngram_range=(1, 2),
            )

            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)

        except ImportError:
            # Fallback to Jaccard similarity
            tokens1 = set(self._simple_tokenize(text1))
            tokens2 = set(self._simple_tokenize(text2))

            if not tokens1 or not tokens2:
                return 0.0

            intersection = len(tokens1 & tokens2)
            union = len(tokens1 | tokens2)
            return intersection / union if union > 0 else 0.0

    def _information_density(self, text: str) -> float:
        """
        Calculate information density: unique concepts per character.
        """
        if not text:
            return 0.0

        # Extract unique meaningful words
        words = set(re.findall(r'[\u4e00-\u9fff]{2,}', text))
        return len(words) / max(1, len(text)) * 100

    def _merge_overlapping(self, text1: str, text2: str) -> str:
        """
        Merge overlapping explanations: keep longer version, add unique details.

        [Source: docs/stories/33.7.story.md - Task 5]
        """
        # Keep longer as base
        if len(text2) > len(text1):
            text1, text2 = text2, text1

        # Find unique sentences in shorter text
        sentences1 = set(re.split(r'[。！？\n]', text1))
        sentences2 = re.split(r'[。！？\n]', text2)

        unique_additions = []
        for sentence in sentences2:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            # Check if this sentence adds new info
            if sentence not in sentences1:
                # Check similarity with all existing sentences
                is_duplicate = False
                for s1 in sentences1:
                    if len(s1) < 10:
                        continue
                    if self._calculate_similarity(sentence, s1) >= 0.7:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_additions.append(sentence)

        # Append unique additions
        if unique_additions:
            text1 = text1.rstrip()
            if not text1.endswith(("。", "！", "？")):
                text1 += "。"
            text1 += "\n\n**补充说明：**\n" + "。".join(unique_additions) + "。"

        return text1

    async def merge(
        self,
        results: List[AgentResult],
        options: Optional[MergeOptions] = None,
    ) -> MergeResult:
        """
        Deduplicate and merge overlapping content.

        [Source: docs/stories/33.7.story.md - AC3]
        """
        if not results:
            return self._handle_empty_input()

        successful = self._filter_successful(results)
        failed_count = len(results) - len(successful)
        if not successful:
            return self._handle_empty_input(len(results), failed_count)

        options = options or MergeOptions()
        threshold = options.dedup_threshold

        # Sort by information density (higher = more valuable)
        sorted_results = sorted(
            successful,
            key=lambda r: self._information_density(r.result),
            reverse=True,
        )

        # Deduplicate
        kept_results: List[AgentResult] = []
        merged_pairs: List[tuple] = []

        for result in sorted_results:
            is_duplicate = False
            merge_target_idx = None

            for i, kept in enumerate(kept_results):
                similarity = self._calculate_similarity(result.result, kept.result)
                if similarity >= threshold:
                    is_duplicate = True
                    merge_target_idx = i
                    break

            if is_duplicate and merge_target_idx is not None:
                # Merge into existing
                merged_pairs.append((merge_target_idx, result))
            else:
                kept_results.append(result)

        # Apply merges
        for target_idx, to_merge in merged_pairs:
            kept_results[target_idx] = AgentResult(
                node_id=kept_results[target_idx].node_id,
                agent_name=f"{kept_results[target_idx].agent_name}+{to_merge.agent_name}",
                result=self._merge_overlapping(
                    kept_results[target_idx].result,
                    to_merge.result,
                ),
                success=True,
            )

        # Build final content
        sections = []
        for result in kept_results:
            if options.include_attribution:
                sections.append(f"## 📘 {result.agent_name} 解释\n{result.result}")
            else:
                sections.append(result.result)

        separator = "\n\n---\n\n" if options.preserve_formatting else "\n\n"
        merged_content = separator.join(sections)

        # Truncate if needed
        if options.max_content_length and len(merged_content) > options.max_content_length:
            merged_content = merged_content[:options.max_content_length] + "\n\n...(内容已截断)"

        # Calculate quality
        source_texts = [r.result for r in successful]
        quality_score = self.scorer.calculate(merged_content, source_texts, self.config)

        # Add warning for deduplication
        warnings = []
        dedup_count = len(successful) - len(kept_results)
        if dedup_count > 0:
            warnings.append(f"Deduplicated {dedup_count} similar content sections")

        return MergeResult(
            merged_content=merged_content,
            strategy_used=self.strategy_type,
            source_count=len(results),
            quality_score=quality_score,
            successful_sources=len(successful),
            failed_sources=len(results) - len(successful),
            warnings=warnings,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Factory
# [Source: docs/stories/33.7.story.md - Task 2]
# ═══════════════════════════════════════════════════════════════════════════════

# Registry of merger classes
_MERGER_REGISTRY: Dict[MergeStrategyType, Type[ResultMerger]] = {
    MergeStrategyType.supplementary: SupplementaryMerger,
    MergeStrategyType.hierarchical: HierarchicalMerger,
    MergeStrategyType.voting: VotingMerger,
}


def get_merger(
    strategy_type: Optional[MergeStrategyType] = None,
    config: Optional[MergeConfig] = None,
) -> ResultMerger:
    """
    Factory function to get appropriate merger instance.

    Args:
        strategy_type: Strategy to use (None = use config default)
        config: Optional configuration (None = load from env)

    Returns:
        ResultMerger instance for the specified strategy

    Raises:
        ValueError: If invalid strategy type provided

    [Source: docs/stories/33.7.story.md - Task 2]
    """
    config = config or load_merge_config()

    if strategy_type is None:
        strategy_type = config.default_strategy

    if strategy_type not in _MERGER_REGISTRY:
        raise ValueError(
            f"Invalid merge strategy: {strategy_type}. "
            f"Valid options: {list(_MERGER_REGISTRY.keys())}"
        )

    merger_class = _MERGER_REGISTRY[strategy_type]
    return merger_class(config=config)


class MergerFactory:
    """
    Factory class for creating merger instances.

    Alternative OOP interface to get_merger() function.

    [Source: docs/stories/33.7.story.md - Implementation Notes]
    """

    def __init__(self, config: Optional[MergeConfig] = None):
        """Initialize factory with optional configuration."""
        self.config = config or load_merge_config()

    def get_merger(
        self,
        strategy_type: Optional[MergeStrategyType] = None,
    ) -> ResultMerger:
        """Get merger instance for specified strategy."""
        return get_merger(strategy_type, self.config)

    @staticmethod
    def available_strategies() -> List[MergeStrategyType]:
        """Return list of available strategies."""
        return list(_MERGER_REGISTRY.keys())
