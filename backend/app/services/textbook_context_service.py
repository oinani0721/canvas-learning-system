# Canvas Learning System - Textbook Context Service
# Story FIX-3.1: Python版TextbookContextService
"""
Textbook Context Service for Canvas Learning System.

Provides textbook reference context injection for AI agents.
Reads .canvas-links.json configuration files to find associated
textbook Canvas files and searches for relevant content.

[Source: docs/prd/sprint-change-proposal-20251208.md - Phase 3]
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TextbookContext:
    """
    Textbook context result.

    Attributes:
        textbook_canvas: Path to the textbook Canvas file
        section_name: Name of the matched section
        node_id: ID of the matched node
        relevance_score: Relevance score (0.0-1.0)
        content_preview: Preview of matched content
        page_number: PDF page number (None for non-PDF files)
        file_type: File type - "canvas", "markdown", or "pdf"

    [Source: Story 28.3 - PDF页码链接支持]
    """
    textbook_canvas: str
    section_name: str
    node_id: str
    relevance_score: float
    content_preview: str
    # Story 28.3: PDF page link support
    page_number: Optional[int] = None
    file_type: str = "canvas"  # "canvas" | "markdown" | "pdf"


@dataclass
class Prerequisite:
    """
    Prerequisite concept.

    Attributes:
        concept_name: Name of the prerequisite concept
        source_canvas: Canvas containing the prerequisite
        node_id: Node ID of the prerequisite
        importance: 'required', 'recommended', or 'optional'
    """
    concept_name: str
    source_canvas: str
    node_id: str
    importance: str  # 'required', 'recommended', 'optional'


@dataclass
class FullTextbookContext:
    """
    Full context result including textbooks and prerequisites.

    Attributes:
        contexts: List of textbook contexts (supports PDF page_number and file_type)
        prerequisites: List of prerequisite concepts
        query_time_ms: Time taken for query in milliseconds
        timed_out: Whether the query timed out

    Note:
        Each TextbookContext in contexts may have:
        - page_number: PDF page number for direct page links
        - file_type: "canvas", "markdown", or "pdf"

    [Source: Story 28.3 - PDF页码链接支持]
    """
    contexts: List[TextbookContext] = field(default_factory=list)
    prerequisites: List[Prerequisite] = field(default_factory=list)
    query_time_ms: float = 0.0
    timed_out: bool = False


@dataclass
class TextbookContextConfig:
    """
    Service configuration.

    Attributes:
        timeout: Query timeout in seconds
        max_results: Maximum number of results
        min_relevance_score: Minimum relevance score threshold
    """
    timeout: float = 1.0  # 1 second timeout
    max_results: int = 3
    min_relevance_score: float = 0.5


class TextbookContextService:
    """
    Service for retrieving textbook context from associated Canvas files.

    Implements textbook reference injection for Agent context.
    Reads .canvas-links.json configuration files to find associations.

    [Source: FIX-3.1 Python版TextbookContextService]
    """

    def __init__(
        self,
        canvas_base_path: str,
        config: Optional[TextbookContextConfig] = None
    ):
        """
        Initialize TextbookContextService.

        Args:
            canvas_base_path: Base path to Canvas files (e.g., 笔记库 path)
            config: Optional configuration
        """
        self._base_path = Path(canvas_base_path)
        self._config = config or TextbookContextConfig()
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        logger.debug(f"TextbookContextService initialized with base_path={canvas_base_path}")

    async def get_textbook_context(
        self,
        canvas_path: str,
        query: str
    ) -> Optional[FullTextbookContext]:
        """
        Get textbook context for a query.

        Uses timeout protection for graceful degradation.

        Args:
            canvas_path: Path to the current Canvas file
            query: User query or node content to search for

        Returns:
            FullTextbookContext or None if error occurred
        """
        import time
        start_time = time.time()

        try:
            # Use timeout protection
            result = await asyncio.wait_for(
                self._fetch_context(canvas_path, query),
                timeout=self._config.timeout
            )
            result.query_time_ms = (time.time() - start_time) * 1000
            return result

        except asyncio.TimeoutError:
            logger.warning(f"[TextbookContextService] Query timed out for: {canvas_path}")
            return FullTextbookContext(
                contexts=[],
                prerequisites=[],
                query_time_ms=(time.time() - start_time) * 1000,
                timed_out=True
            )
        except Exception as e:
            logger.warning(f"[TextbookContextService] Error fetching context: {e}")
            return None

    async def _fetch_context(
        self,
        canvas_path: str,
        query: str
    ) -> FullTextbookContext:
        """
        Fetch context from associated Canvas files.

        Args:
            canvas_path: Current Canvas path
            query: Search query

        Returns:
            FullTextbookContext with results
        """
        contexts: List[TextbookContext] = []
        prerequisites: List[Prerequisite] = []

        # 1. Load .canvas-links.json configuration
        associations = await self._get_associations(canvas_path)

        # 2. Filter for 'references' type (教材关联)
        textbook_associations = [
            a for a in associations
            if a.get('association_type') == 'references'
        ]

        # 3. Search in each textbook Canvas
        for assoc in textbook_associations:
            target_canvas = assoc.get('target_canvas', '')
            if target_canvas:
                textbook_contexts = await self._search_in_canvas(
                    target_canvas, query
                )
                contexts.extend(textbook_contexts)

        # 4. Get prerequisites
        prereq_associations = [
            a for a in associations
            if a.get('association_type') == 'prerequisite'
        ]

        for assoc in prereq_associations:
            target_canvas = assoc.get('target_canvas', '')
            prerequisites.append(Prerequisite(
                concept_name=self._get_canvas_display_name(target_canvas),
                source_canvas=target_canvas,
                node_id=assoc.get('association_id', ''),
                importance='required'
            ))

        # 5. Sort and limit results
        sorted_contexts = sorted(
            contexts,
            key=lambda c: c.relevance_score,
            reverse=True
        )[:self._config.max_results]

        return FullTextbookContext(
            contexts=sorted_contexts,
            prerequisites=prerequisites,
            query_time_ms=0.0,
            timed_out=False
        )

    async def _get_associations(self, canvas_path: str) -> List[Dict[str, Any]]:
        """
        Load associations from .canvas-links.json.

        Args:
            canvas_path: Path to Canvas file

        Returns:
            List of association dictionaries
        """
        config = await self._load_config(canvas_path)
        return config.get('associations', [])

    async def _load_config(self, canvas_path: str) -> Dict[str, Any]:
        """
        Load .canvas-links.json configuration.

        Args:
            canvas_path: Path to Canvas file

        Returns:
            Configuration dictionary
        """
        config_path = self._get_config_path(canvas_path)

        # Check cache
        if config_path in self._config_cache:
            return self._config_cache[config_path]

        try:
            full_path = self._base_path / config_path
            if full_path.exists():
                content = full_path.read_text(encoding='utf-8')
                config = json.loads(content)
                self._config_cache[config_path] = config
                return config
        except Exception as e:
            logger.warning(f"[TextbookContextService] Failed to load config: {e}")

        # Return empty config if file doesn't exist
        return {'version': '1.0.0', 'associations': [], 'settings': {}}

    def _get_config_path(self, canvas_path: str) -> str:
        """
        Get the .canvas-links.json path for a Canvas file.

        Args:
            canvas_path: Canvas file path

        Returns:
            Config file path
        """
        # Config file is in the same directory as the Canvas file
        canvas_p = Path(canvas_path)
        if canvas_p.parent == Path('.'):
            return '.canvas-links.json'
        return str(canvas_p.parent / '.canvas-links.json')

    async def _search_in_canvas(
        self,
        canvas_path: str,
        query: str
    ) -> List[TextbookContext]:
        """
        Search for relevant content in a Canvas file.

        Args:
            canvas_path: Path to Canvas file
            query: Search query

        Returns:
            List of TextbookContext results
        """
        contexts: List[TextbookContext] = []

        try:
            full_path = self._base_path / canvas_path
            if not full_path.exists():
                return []

            # Read Canvas JSON
            content = full_path.read_text(encoding='utf-8')
            canvas_data = json.loads(content)

            nodes = canvas_data.get('nodes', [])
            if not isinstance(nodes, list):
                return []

            # Search nodes for query match
            query_lower = query.lower()
            for node in nodes:
                if node.get('type') != 'text':
                    continue

                node_text = node.get('text', '')
                node_lower = node_text.lower()

                # Check if query is in node text
                if query_lower in node_lower:
                    relevance = self._calculate_relevance(query, node_text)

                    if relevance >= self._config.min_relevance_score:
                        contexts.append(TextbookContext(
                            textbook_canvas=canvas_path,
                            section_name=self._extract_section_name(node_text),
                            node_id=node.get('id', ''),
                            relevance_score=relevance,
                            content_preview=node_text[:100]
                        ))

        except Exception as e:
            logger.warning(f"[TextbookContextService] Failed to search canvas {canvas_path}: {e}")

        return contexts

    def _calculate_relevance(self, query: str, text: str) -> float:
        """
        Calculate relevance score between query and text.

        Args:
            query: Search query
            text: Text to match against

        Returns:
            Relevance score (0.0-1.0)
        """
        query_lower = query.lower()
        text_lower = text.lower()

        # Exact match
        if text_lower == query_lower:
            return 1.0

        # Contains full query
        if query_lower in text_lower:
            # Higher score for shorter text (more focused)
            length_factor = min(1.0, 100 / len(text))
            return 0.7 + (0.2 * length_factor)

        # Word overlap
        query_words = query_lower.split()
        text_words = set(text_lower.split())

        match_count = 0
        for word in query_words:
            if word in text_words or any(word in tw for tw in text_words):
                match_count += 1

        if query_words:
            return match_count / len(query_words)

        return 0.0

    def _extract_section_name(self, text: str) -> str:
        """
        Extract section name from node text.

        Args:
            text: Node text

        Returns:
            Section name
        """
        import re

        # Try to find a header pattern
        header_match = re.search(r'^#+\s*(.+)$', text, re.MULTILINE)
        if header_match:
            return header_match.group(1).strip()

        # Use first line as section name
        first_line = text.split('\n')[0] if text else ''
        if len(first_line) > 50:
            return first_line[:47] + '...'

        return first_line or 'Unknown Section'

    def _get_canvas_display_name(self, path: str) -> str:
        """
        Get display name from Canvas path.

        Args:
            path: Canvas file path

        Returns:
            Display name
        """
        name = Path(path).name
        return name.replace('.canvas', '')

    def build_agent_prompt(
        self,
        base_prompt: str,
        context: Optional[FullTextbookContext]
    ) -> str:
        """
        Build Agent prompt with textbook context.

        Args:
            base_prompt: Original Agent prompt
            context: Textbook context

        Returns:
            Enhanced prompt with context
        """
        if not context or (len(context.contexts) == 0 and len(context.prerequisites) == 0):
            return base_prompt

        context_section = '\n\n## 相关教材参考\n'

        # Add textbook contexts
        for ctx in context.contexts:
            display_name = self._get_canvas_display_name(ctx.textbook_canvas)
            context_section += f'- {display_name} > {ctx.section_name}\n'
            context_section += f'  内容预览: {ctx.content_preview}...\n'

        # Add prerequisites
        if context.prerequisites:
            context_section += '\n## 建议先复习\n'
            for prereq in context.prerequisites:
                display_name = self._get_canvas_display_name(prereq.source_canvas)
                context_section += f'- {prereq.concept_name} ({display_name})\n'

        # Add instruction for Agent
        context_section += '''
请在回答中适当引用上述教材内容，格式为"参见教材: {教材名} > {章节名}"。
如果识别到需要前置知识，请提示"建议先复习: {概念名}({来源Canvas})"。
'''

        return base_prompt + context_section

    def format_textbook_ref(self, context: TextbookContext) -> str:
        """
        Format textbook reference for node metadata.

        Args:
            context: Textbook context

        Returns:
            Formatted reference string
        """
        display_name = self._get_canvas_display_name(context.textbook_canvas)
        return f'参见教材: {display_name} > {context.section_name}'

    def invalidate_cache(self, canvas_path: Optional[str] = None) -> None:
        """
        Invalidate configuration cache.

        Args:
            canvas_path: Specific Canvas path to invalidate, or None for all
        """
        if canvas_path:
            config_path = self._get_config_path(canvas_path)
            self._config_cache.pop(config_path, None)
        else:
            self._config_cache.clear()

    async def sync_mounted_textbook(
        self,
        canvas_path: str,
        association: Dict[str, Any]
    ) -> str:
        """
        Sync a mounted textbook to .canvas-links.json.

        Creates or updates the configuration file with the new association.
        This bridges the frontend localStorage to backend filesystem.

        Args:
            canvas_path: Path to the Canvas file
            association: Association dictionary with textbook info

        Returns:
            Path to the .canvas-links.json file

        [Source: 方案A - 前端同步到后端]
        """
        config_path = self._get_config_path(canvas_path)
        full_path = self._base_path / config_path

        # Load existing config or create new
        try:
            if full_path.exists():
                content = full_path.read_text(encoding='utf-8')
                config = json.loads(content)
            else:
                config = {
                    'version': '1.0.0',
                    'associations': [],
                    'settings': {'auto_link': True}
                }
        except Exception as e:
            logger.warning(f"[TextbookContextService] Failed to load config, creating new: {e}")
            config = {
                'version': '1.0.0',
                'associations': [],
                'settings': {'auto_link': True}
            }

        # Check if association already exists (by ID)
        associations = config.get('associations', [])
        existing_idx = None
        for i, a in enumerate(associations):
            if a.get('association_id') == association.get('association_id'):
                existing_idx = i
                break

        if existing_idx is not None:
            # Update existing
            associations[existing_idx] = association
        else:
            # Add new
            associations.append(association)

        config['associations'] = associations

        # Ensure directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write config file
        full_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        # Invalidate cache
        self._config_cache.pop(config_path, None)

        logger.info(f"[TextbookContextService] Synced textbook to {config_path}")

        return config_path

    async def remove_mounted_textbook(
        self,
        canvas_path: str,
        textbook_id: str
    ) -> bool:
        """
        Remove a mounted textbook from .canvas-links.json.

        Args:
            canvas_path: Path to the Canvas file
            textbook_id: Textbook ID to remove

        Returns:
            True if removed, False if not found

        [Source: 方案A - 前端同步到后端]
        """
        config_path = self._get_config_path(canvas_path)
        full_path = self._base_path / config_path

        if not full_path.exists():
            return False

        try:
            content = full_path.read_text(encoding='utf-8')
            config = json.loads(content)
        except Exception as e:
            logger.warning(f"[TextbookContextService] Failed to load config for removal: {e}")
            return False

        # Find and remove the association
        associations = config.get('associations', [])
        original_count = len(associations)

        # Remove by matching association_id that contains the textbook_id
        associations = [
            a for a in associations
            if not a.get('association_id', '').endswith(textbook_id)
        ]

        if len(associations) == original_count:
            return False  # Nothing removed

        config['associations'] = associations

        # Write back
        full_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        # Invalidate cache
        self._config_cache.pop(config_path, None)

        logger.info(f"[TextbookContextService] Removed textbook {textbook_id} from {config_path}")

        return True


# Singleton instance
_textbook_context_service: Optional[TextbookContextService] = None


def get_textbook_context_service(
    canvas_base_path: Optional[str] = None
) -> TextbookContextService:
    """
    Get or create the TextbookContextService singleton.

    Args:
        canvas_base_path: Base path to Canvas files

    Returns:
        TextbookContextService instance
    """
    global _textbook_context_service

    if _textbook_context_service is None:
        from app.config import settings
        base_path = canvas_base_path or settings.CANVAS_BASE_PATH
        _textbook_context_service = TextbookContextService(base_path)

    return _textbook_context_service


def reset_textbook_context_service() -> None:
    """Reset the TextbookContextService singleton (for testing)."""
    global _textbook_context_service
    _textbook_context_service = None
