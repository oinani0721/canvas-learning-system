# Agent Tool Executor for Gemini Function Calling
# Phase 2: Executes tool calls requested by the LLM during generation
#
# Wraps existing retrieval clients (LanceDB, Graphiti) as callable tools.
# The LLM decides which tools to call and with what parameters;
# this executor performs the actual search and returns results.
#
# [Source: Agent Architecture Upgrade Plan - Phase 2]

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Executes tool calls from Gemini function calling responses.

    Reuses existing retrieval infrastructure:
    - LanceDB client for vault note vector search
    - Graphiti client for knowledge graph entity search
    - Direct file reads for note content
    """

    def __init__(
        self,
        lancedb_client: Optional[Any] = None,
        graphiti_client: Optional[Any] = None,
        vault_path: Optional[str] = None,
    ):
        """
        Initialize with existing client instances.

        Args:
            lancedb_client: LanceDB client instance (from src/agentic_rag/clients/)
            graphiti_client: Graphiti client instance (from src/agentic_rag/clients/)
            vault_path: Absolute path to the Obsidian vault (CANVAS_BASE_PATH)
        """
        self._lancedb = lancedb_client
        self._graphiti = graphiti_client
        self._vault_path = Path(vault_path) if vault_path else None

    async def execute(self, name: str, args: Dict[str, Any]) -> str:
        """
        Execute a tool call by name with given arguments.

        Args:
            name: Function name (e.g., 'search_vault_notes')
            args: Function arguments dict

        Returns:
            String result formatted for the LLM to consume
        """
        try:
            if name == "search_vault_notes":
                return await self._search_vault_notes(
                    query=args["query"],
                    num_results=args.get("num_results", 5),
                )
            elif name == "search_knowledge_graph":
                return await self._search_knowledge_graph(
                    query=args["query"],
                    entity_types=args.get("entity_types"),
                    num_results=args.get("num_results", 5),
                )
            elif name == "get_note_content":
                return self._get_note_content(
                    file_path=args["file_path"],
                    line_start=args.get("line_start"),
                    line_end=args.get("line_end"),
                )
            else:
                return f"[Error] Unknown tool: {name}"
        except Exception as e:
            logger.error(f"Tool execution error: {name}({args}) -> {e}")
            return f"[Error] Tool '{name}' failed: {str(e)[:200]}"

    # ─────────────────────────────────────────────────
    # Tool implementations
    # ─────────────────────────────────────────────────

    async def _search_vault_notes(
        self,
        query: str,
        num_results: int = 5,
    ) -> str:
        """Search vault notes via LanceDB vector search."""
        if not self._lancedb:
            return "[Error] LanceDB client not available. Vault note search is disabled."

        try:
            results: List[Dict[str, Any]] = await self._lancedb.search(
                query=query,
                table_name="vault_notes",
                num_results=num_results,
            )
        except Exception as e:
            # Fallback: try the default table
            logger.warning(f"vault_notes table search failed ({e}), trying canvas_explanations")
            try:
                results = await self._lancedb.search(
                    query=query,
                    table_name="canvas_explanations",
                    num_results=num_results,
                )
            except Exception as e2:
                return f"[Error] LanceDB search failed: {str(e2)[:200]}"

        if not results:
            return f"[No results] No vault notes found for query: '{query}'"

        return self._format_search_results(results, source_label="Notes")

    async def _search_knowledge_graph(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        num_results: int = 5,
    ) -> str:
        """Search knowledge graph via Graphiti client."""
        if not self._graphiti:
            return "[Error] Graphiti client not available. Knowledge graph search is disabled."

        try:
            results: List[Dict[str, Any]] = await self._graphiti.search_nodes(
                query=query,
                entity_types=entity_types,
                num_results=num_results,
            )
        except Exception as e:
            return f"[Error] Knowledge graph search failed: {str(e)[:200]}"

        if not results:
            return f"[No results] No knowledge graph entities found for query: '{query}'"

        return self._format_search_results(results, source_label="KnowledgeGraph")

    def _get_note_content(
        self,
        file_path: str,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
    ) -> str:
        """Read note file content from vault."""
        if not self._vault_path:
            return "[Error] Vault path not configured."

        # Security: prevent path traversal
        safe_path = self._vault_path / file_path
        try:
            safe_path = safe_path.resolve()
            vault_resolved = self._vault_path.resolve()
            if not str(safe_path).startswith(str(vault_resolved)):
                return "[Error] Access denied: path outside vault directory."
        except (OSError, ValueError):
            return f"[Error] Invalid file path: {file_path}"

        if not safe_path.exists():
            return f"[Error] File not found: {file_path}"

        if not safe_path.is_file():
            return f"[Error] Not a file: {file_path}"

        try:
            content = safe_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            if line_start is not None or line_end is not None:
                start = max(0, (line_start or 1) - 1)  # 1-indexed to 0-indexed
                end = line_end or len(lines)
                selected = lines[start:end]
                # Include line numbers for citation
                numbered = [
                    f"{start + i + 1}: {line}"
                    for i, line in enumerate(selected)
                ]
                return f"[File: {file_path}, lines {start+1}-{end}]\n" + "\n".join(numbered)
            else:
                # Limit to first 200 lines to avoid overwhelming the context
                if len(lines) > 200:
                    truncated = lines[:200]
                    return (
                        f"[File: {file_path}, showing first 200 of {len(lines)} lines]\n"
                        + "\n".join(f"{i+1}: {line}" for i, line in enumerate(truncated))
                        + f"\n\n[... truncated, {len(lines) - 200} more lines]"
                    )
                return (
                    f"[File: {file_path}, {len(lines)} lines]\n"
                    + "\n".join(f"{i+1}: {line}" for i, line in enumerate(lines))
                )

        except UnicodeDecodeError:
            return f"[Error] Cannot read file (not UTF-8): {file_path}"

    # ─────────────────────────────────────────────────
    # Formatting helpers
    # ─────────────────────────────────────────────────

    @staticmethod
    def _format_search_results(
        results: List[Dict[str, Any]],
        source_label: str = "Search",
    ) -> str:
        """Format search results into a readable string for the LLM."""
        formatted_parts = []
        for i, result in enumerate(results, 1):
            content = result.get("content", "")
            score = result.get("score", 0.0)
            metadata = result.get("metadata", {})

            # Build source citation
            source = metadata.get("source", source_label)
            canvas_file = metadata.get("canvas_file", "")
            doc_id = result.get("doc_id", "")

            citation = f"[{source_label}]"
            if canvas_file:
                citation = f"[{source_label}: {canvas_file}]"
            elif doc_id:
                citation = f"[{source_label}: {doc_id}]"

            # Truncate long content
            if len(content) > 500:
                content = content[:500] + "..."

            formatted_parts.append(
                f"### Result {i} (score: {score:.3f}) {citation}\n{content}"
            )

        return "\n\n".join(formatted_parts)
