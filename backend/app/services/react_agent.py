"""
React Agent for Canvas Learning System

Replaces the Phase 2/3 pipeline with a true agentic architecture where
the LLM autonomously decides when and what to retrieve.

Uses LangChain's create_react_agent with 4 tools:
1. search_vault_notes - LanceDB hybrid search on vault_notes
2. search_knowledge_graph - Graphiti search with entity_types filter
3. get_note_content - Read specific note files
4. record_learning_memory - Record misconceptions/traps to knowledge graph
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Definitions (adapted from tool_executor.py)
# ═══════════════════════════════════════════════════════════════════════════════

# Module-level references set by init_react_tools()
_lancedb_client = None
_graphiti_client = None
_vault_path: Optional[Path] = None
_neo4j_client = None


def init_react_tools(
    lancedb_client=None,
    graphiti_client=None,
    vault_path: Optional[str] = None,
    neo4j_client=None,
):
    """Initialize module-level client references for tools."""
    global _lancedb_client, _graphiti_client, _vault_path, _neo4j_client
    _lancedb_client = lancedb_client
    _graphiti_client = graphiti_client
    _vault_path = Path(vault_path) if vault_path else None
    _neo4j_client = neo4j_client


@tool
async def search_vault_notes(query: str, num_results: int = 5) -> str:
    """搜索 Obsidian Vault 笔记（讲义、讨论、考试题等）。

    适用于: 需要教学材料、概念解释、具体笔记内容时使用。
    不适用于: 查找学生个人的错误记录、理解程度评估。

    Args:
        query: 搜索关键词或语义查询
        num_results: 返回结果数量 (默认5)
    """
    if not _lancedb_client:
        return "[Error] LanceDB client not available."

    try:
        results = await _lancedb_client.search(
            query=query,
            table_name="vault_notes",
            num_results=num_results,
            query_type="hybrid",
        )
    except Exception as e:
        # Fallback to vector-only if hybrid not available
        try:
            results = await _lancedb_client.search(
                query=query,
                table_name="vault_notes",
                num_results=num_results,
            )
        except Exception as e2:
            return f"[Error] Search failed: {str(e2)[:200]}"

    if not results:
        return f"[No results] No vault notes found for: '{query}'"

    return _format_results(results, "Notes")


@tool
async def search_knowledge_graph(
    query: str,
    entity_types: Optional[List[str]] = None,
    num_results: int = 5,
) -> str:
    """搜索学生知识图谱（误解记录、做题陷阱、引导思考记录等）。

    适用于: 查找学生之前的误解、错误模式、学习进度。
    entity_types 可选值: Misconception, ProblemTrap, LogicalFallacy,
                        GuidedThinking, Concept, ColorTransition
    不适用于: 查找具体笔记内容或讲义材料。

    Args:
        query: 搜索关键词
        entity_types: 可选的 entity type 过滤列表
        num_results: 返回结果数量 (默认5)
    """
    if not _graphiti_client:
        return "[Error] Graphiti client not available."

    try:
        results = await _graphiti_client.search_nodes(
            query=query,
            entity_types=entity_types,
            num_results=num_results,
        )
    except Exception as e:
        return f"[Error] Knowledge graph search failed: {str(e)[:200]}"

    if not results:
        return f"[No results] No knowledge graph entities found for: '{query}'"

    return _format_results(results, "KnowledgeGraph")


@tool
def get_note_content(
    file_path: str,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
) -> str:
    """读取指定笔记文件的具体内容。

    用于获取搜索结果中某个笔记的完整文本。
    file_path 应为相对于 vault 根目录的路径。

    Args:
        file_path: 笔记文件路径 (相对于vault根目录)
        line_start: 起始行号 (1-indexed, 可选)
        line_end: 结束行号 (可选)
    """
    if not _vault_path:
        return "[Error] Vault path not configured."

    safe_path = _vault_path / file_path
    try:
        safe_path = safe_path.resolve()
        vault_resolved = _vault_path.resolve()
        if not str(safe_path).startswith(str(vault_resolved)):
            return "[Error] Access denied: path outside vault."
    except (OSError, ValueError):
        return f"[Error] Invalid path: {file_path}"

    if not safe_path.exists() or not safe_path.is_file():
        return f"[Error] File not found: {file_path}"

    try:
        content = safe_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        if line_start is not None or line_end is not None:
            start = max(0, (line_start or 1) - 1)
            end = line_end or len(lines)
            selected = lines[start:end]
            numbered = [f"{start + i + 1}: {line}" for i, line in enumerate(selected)]
            return f"[File: {file_path}, lines {start+1}-{end}]\n" + "\n".join(numbered)

        if len(lines) > 200:
            truncated = lines[:200]
            return (
                f"[File: {file_path}, first 200/{len(lines)} lines]\n"
                + "\n".join(f"{i+1}: {line}" for i, line in enumerate(truncated))
            )
        return (
            f"[File: {file_path}, {len(lines)} lines]\n"
            + "\n".join(f"{i+1}: {line}" for i, line in enumerate(lines))
        )
    except UnicodeDecodeError:
        return f"[Error] Cannot read (not UTF-8): {file_path}"


@tool
async def record_learning_memory(
    entity_type: str,
    concept: str,
    topic: str,
    details: Dict[str, str],
) -> str:
    """记录学生的学习记忆到知识图谱。

    当你在解释过程中发现学生存在误解、做题陷阱、逻辑谬误时，
    主动调用此工具记录，每次请求最多调用2次。

    Args:
        entity_type: Misconception | ProblemTrap | LogicalFallacy | GuidedThinking
        concept: 概念名称
        topic: 主题 (Search, CSPs, GameTrees, MDPs, RL)
        details: 详细信息字典，键值取决于 entity_type:
                 Misconception: {error, correct}
                 ProblemTrap: {problem, wrong, correct, insight}
                 LogicalFallacy: {flawed, why, correct}
                 GuidedThinking: {question, answer, correct_answer, grade}
    """
    from app.core.memory_format import (
        build_entity_name,
        build_episode_body,
        get_source_description,
    )

    valid_types = {"Misconception", "ProblemTrap", "LogicalFallacy", "GuidedThinking"}
    if entity_type not in valid_types:
        return f"[Error] Invalid entity_type: {entity_type}. Must be one of {valid_types}"

    if not _neo4j_client:
        return "[Error] Neo4j client not available for memory recording."

    name = build_entity_name(entity_type, concept)
    body = build_episode_body(entity_type, topic=topic, **details)
    source_desc = get_source_description(entity_type)

    try:
        cypher = """
        CREATE (n:EntityNode {
            node_id: $nodeId,
            group_id: $groupId,
            name: $name,
            entity_type: $entityType,
            episode_body: $body,
            text: $body,
            source: 'react_agent',
            source_description: $sourceDesc,
            created_at: $timestamp,
            updated_at: $timestamp
        })
        """
        timestamp = datetime.now().isoformat()
        await _neo4j_client.run_query(
            cypher,
            nodeId=f"agent-{timestamp}",
            groupId="cs188",
            name=name,
            entityType=entity_type,
            body=body,
            sourceDesc=source_desc,
            timestamp=timestamp,
        )
        logger.info(f"React agent recorded memory: {name}")
        return f"[OK] Recorded {entity_type}: {concept}"
    except Exception as e:
        logger.error(f"Failed to record memory: {e}")
        return f"[Error] Recording failed: {str(e)[:200]}"


# ═══════════════════════════════════════════════════════════════════════════════
# Result Formatting (shared with tool_executor.py)
# ═══════════════════════════════════════════════════════════════════════════════

def _format_results(results: List[Dict[str, Any]], source_label: str) -> str:
    """Format search results into readable string for the LLM."""
    parts = []
    for i, result in enumerate(results, 1):
        content = result.get("content", "")
        score = result.get("score", 0.0)
        metadata = result.get("metadata", {})

        citation = f"[{source_label}]"
        canvas_file = metadata.get("canvas_file", "")
        doc_id = result.get("doc_id", "")
        if canvas_file:
            citation = f"[{source_label}: {canvas_file}]"
        elif doc_id:
            citation = f"[{source_label}: {doc_id}]"

        if len(content) > 500:
            content = content[:500] + "..."

        parts.append(f"### Result {i} (score: {score:.3f}) {citation}\n{content}")

    return "\n\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# Agent Runner
# ═══════════════════════════════════════════════════════════════════════════════

REACT_TOOLS = [search_vault_notes, search_knowledge_graph, get_note_content, record_learning_memory]


async def run_react_agent(
    agent_type: str,
    user_prompt: str,
    system_prompt: str,
    model_name: str = "gemini-2.5-flash",
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    thinking_budget: Optional[int] = None,
    recursion_limit: int = 7,
) -> Dict[str, Any]:
    """
    Run the React Agent with LangChain's create_react_agent.

    Args:
        agent_type: Agent type name for logging
        user_prompt: User's input prompt
        system_prompt: System prompt (agent template + context)
        model_name: Gemini model name
        api_key: Google API key
        temperature: Response temperature
        thinking_budget: Gemini thinking tokens budget (None=disabled, -1=dynamic)
        recursion_limit: Max tool call rounds

    Returns:
        Dict with response, tool_calls_made, model
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.prebuilt import create_react_agent

    model_kwargs = {}
    if thinking_budget is not None:
        model_kwargs["thinking_budget"] = thinking_budget

    model = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
        **model_kwargs,
    )

    agent = create_react_agent(model, REACT_TOOLS, prompt=system_prompt)

    logger.info(f"[ReactAgent] Running for {agent_type}, recursion_limit={recursion_limit}")

    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=user_prompt)]},
        config={"recursion_limit": recursion_limit},
    )

    # Extract response from last message
    messages = result.get("messages", [])
    response_text = ""
    tool_calls_made = []

    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls_made.append({
                    "name": tc.get("name", ""),
                    "args": tc.get("args", {}),
                })
        if hasattr(msg, "content") and msg.content:
            response_text = msg.content  # Last content message is the answer

    logger.info(
        f"[ReactAgent] {agent_type} completed: "
        f"{len(tool_calls_made)} tool calls, "
        f"response_len={len(response_text)}"
    )

    return {
        "agent_type": agent_type,
        "response": response_text,
        "model": model_name,
        "tool_calls_made": tool_calls_made,
        "usage": {},  # LangChain doesn't expose token counts easily
    }
