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
async def search_vault_notes(query: str, num_results: int = 8) -> str:
    """搜索 Obsidian Vault 笔记（讲义、讨论、考试题等）。

    适用于: 需要教学材料、概念解释、具体笔记内容时使用。
    不适用于: 查找学生个人的错误记录、理解程度评估。

    搜索技巧:
    - 用简短的英文关键词 (2-4 个词)，如 "A* search", "MDP value iteration"
    - 避免中文长句，避免过于具体的短语
    - 建议搜索 2 次: 先搜主题 (如 "reinforcement learning")，再搜子概念 (如 "Q-learning exploration")

    返回结果中包含 [[wikilink]] 引用格式，可直接复制到你的回答中。
    结果已按来源优先级排序（讲义 > 讨论 > 真题 > AI解释）。

    Args:
        query: 搜索关键词 (推荐 2-4 个英文词)
        num_results: 返回结果数量 (默认8)
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
        # Fix B4: Check if table exists — empty results may mean table not indexed
        try:
            table_exists = hasattr(_lancedb_client, 'table_exists') and await _lancedb_client.table_exists("vault_notes")
            if not table_exists:
                logger.warning("[ReactAgent] vault_notes table not indexed. Run POST /api/v1/metadata/index/vault")
                return "[Warning] vault_notes table not indexed yet. Use search_obsidian_cli instead, or run POST /api/v1/metadata/index/vault to populate."
        except Exception:
            pass
        return f"[No results] No vault notes found for: '{query}'"

    # Apply source priority weighting (boost lectures, penalize explanations)
    from app.core.reference_config import apply_source_priority
    results = apply_source_priority(results)

    # Filter out explanation files — agent should cite original lecture notes
    import json as _json
    filtered = []
    for r in results:
        meta = r.get("metadata", {})
        path = meta.get("canvas_file", "")
        if not path:
            meta_str = meta.get("metadata_json", "")
            if meta_str and isinstance(meta_str, str):
                try:
                    path = _json.loads(meta_str).get("file_path", "")
                except _json.JSONDecodeError:
                    pass
        if "-explanations/" in path:
            continue  # Skip AI-generated explanation files
        filtered.append(r)

    if not filtered:
        # All results were explanation files — return empty rather than garbage
        return f"[No results] All results for '{query}' were AI-generated explanations. Try search_obsidian_cli for original lecture notes."

    return _format_results(filtered, "Notes")


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
    # Fix B1: Bypass broken GraphitiClient MCP detection — use Neo4j directly
    # GraphitiClient._mcp_available is always False because MCP tools are RPC
    # services, not Python modules, so importlib.util.find_spec() always fails.
    if not _neo4j_client:
        return "[Error] Neo4j client not available for knowledge graph search."

    try:
        # Build entity type filter
        type_filter = ""
        if entity_types:
            types_str = ", ".join(f'"{t}"' for t in entity_types)
            type_filter = f"AND n.entity_type IN [{types_str}]"

        cypher = f"""
        MATCH (n:EntityNode)
        WHERE n.group_id = 'cs188'
          AND (toLower(n.name) CONTAINS toLower($query)
               OR toLower(n.episode_body) CONTAINS toLower($query)
               OR toLower(n.text) CONTAINS toLower($query))
          {type_filter}
        RETURN n.name AS name, n.entity_type AS entity_type,
               n.episode_body AS body, n.created_at AS created_at
        ORDER BY n.updated_at DESC
        LIMIT $limit
        """
        records = await _neo4j_client.run_query(cypher, query=query, limit=num_results)

        if not records:
            return f"[No results] No knowledge graph entities found for: '{query}'"

        # Format as KnowledgeGraph results for _format_results compatibility
        formatted = []
        for r in records:
            formatted.append({
                "name": r.get("name", ""),
                "content": r.get("body", ""),
                "episode_body": r.get("body", ""),
                "score": 1.0,
                "metadata": {
                    "entity_type": r.get("entity_type", "Entity"),
                    "name": r.get("name", ""),
                },
            })

        return _format_results(formatted, "KnowledgeGraph")

    except Exception as e:
        logger.error(f"[ReactAgent] KG search failed: {e}")
        return f"[Error] Knowledge graph search failed: {str(e)[:200]}"


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
# Obsidian CLI Tools (primary search — precise matching via native index)
# ═══════════════════════════════════════════════════════════════════════════════

@tool
async def search_obsidian_cli(query: str, limit: int = 10) -> str:
    """使用 Obsidian CLI 精确搜索 vault 笔记（主搜索工具）。

    优势：利用 Obsidian 原生索引，精确匹配，返回行级上下文。
    适用于：搜索特定算法名 (A*, Q-learning)、公式、定义。
    优先使用此工具，search_vault_notes 仅在此工具结果不足时补充。

    Args:
        query: 搜索关键词
        limit: 返回结果数量 (默认10)
    """
    import os
    import subprocess

    obs_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Obsidian", "Obsidian.com")
    if not os.path.exists(obs_path):
        return "[Error] Obsidian CLI not available. Use search_vault_notes instead."

    try:
        result = subprocess.run(
            [obs_path, "search:context", f'query={query}', 'vault=CS188', f'limit={limit}'],
            capture_output=True, text=True, timeout=5, encoding="utf-8",
        )
        if result.returncode == 0 and result.stdout.strip():
            return _format_cli_results(result.stdout, query)
        return f"[No results] Obsidian CLI found nothing for: '{query}'"
    except subprocess.TimeoutExpired:
        return "[Error] Obsidian CLI timed out. Use search_vault_notes instead."
    except Exception as e:
        return f"[Error] Obsidian CLI failed: {str(e)[:200]}. Use search_vault_notes instead."


@tool
async def get_note_outline(file_name: str) -> str:
    """获取笔记的标题大纲结构，用于了解笔记组织方式后精准定位。

    Args:
        file_name: 笔记文件名（不含路径和 .md 后缀）
    """
    import os
    import subprocess

    obs_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Obsidian", "Obsidian.com")
    if not os.path.exists(obs_path):
        return "[Error] Obsidian CLI not available."

    try:
        result = subprocess.run(
            [obs_path, "outline", f'file={file_name}', 'vault=CS188'],
            capture_output=True, text=True, timeout=5, encoding="utf-8",
        )
        if result.returncode == 0 and result.stdout.strip():
            return f"[Outline: {file_name}]\n{result.stdout.strip()}"
        return f"[No outline] Could not get outline for: '{file_name}'"
    except Exception as e:
        return f"[Error] Outline failed: {str(e)[:200]}"


@tool
async def find_backlinks(file_name: str) -> str:
    """查找链接到指定笔记的所有笔记（反向链接），发现概念间关联。

    Args:
        file_name: 笔记文件名
    """
    import os
    import subprocess

    obs_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Obsidian", "Obsidian.com")
    if not os.path.exists(obs_path):
        return "[Error] Obsidian CLI not available."

    try:
        result = subprocess.run(
            [obs_path, "backlinks", f'file={file_name}', 'vault=CS188'],
            capture_output=True, text=True, timeout=5, encoding="utf-8",
        )
        if result.returncode == 0 and result.stdout.strip():
            return f"[Backlinks: {file_name}]\n{result.stdout.strip()}"
        return f"[No backlinks] No notes link to: '{file_name}'"
    except Exception as e:
        return f"[Error] Backlinks failed: {str(e)[:200]}"


# Paths to exclude from CLI search results
_CLI_EXCLUDED_PATTERNS = ("-explanations/", "/chunks/", "解释-", "四层次解释-")


def _format_cli_results(raw_output: str, query: str) -> str:
    """Parse Obsidian CLI search:context output into structured results."""
    import re

    lines = raw_output.strip().split("\n")
    parts = []
    current_file = ""
    current_heading = ""
    file_lines = []
    skip_file = False

    def flush():
        nonlocal current_file, current_heading, file_lines, skip_file
        if current_file and file_lines and not skip_file:
            display = current_file
            if display.endswith(".md"):
                display = display[:-3]

            if current_heading:
                # Clean heading: remove wikilinks, markdown links, trailing ()
                clean_h = re.sub(r'\[\[.*?\]\]', '', current_heading).strip()
                clean_h = re.sub(r'\[.*?\]\(.*?\)', '', clean_h).strip()
                clean_h = re.sub(r'\(\)\s*$', '', clean_h).strip()
                if clean_h:
                    wikilink = f"[[{display}#{clean_h}|{clean_h}]]"
                else:
                    wikilink = f"[[{display}]]"
            else:
                wikilink = f"[[{display}]]"

            content_preview = "\n".join(file_lines[:10])
            parts.append(f"### {wikilink}\n{content_preview}")
        file_lines = []
        current_heading = ""
        skip_file = False

    for line in lines:
        match = re.match(r'^(.+?\.md):(\d+):\s*(.*)', line)
        if match:
            file_path = match.group(1)
            content = match.group(3)

            if file_path != current_file:
                flush()
                current_file = file_path
                skip_file = any(p in file_path for p in _CLI_EXCLUDED_PATTERNS)

            if skip_file:
                continue

            # Capture first heading as anchor
            heading_match = re.match(r'^(#{1,6})\s+(.+)', content)
            if heading_match and not current_heading:
                current_heading = heading_match.group(2).strip()

            file_lines.append(content)
        elif line.strip() and not skip_file:
            file_lines.append(line.strip())

    flush()

    if not parts:
        return f"[No results] Obsidian CLI found nothing for: '{query}'"
    return f"[Obsidian CLI: {len(parts)} files matched '{query}']\n\n" + "\n\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# Result Formatting (shared with tool_executor.py)
# ═══════════════════════════════════════════════════════════════════════════════

def _format_results(results: List[Dict[str, Any]], source_label: str) -> str:
    """Format search results into readable string for the LLM."""
    import json as _json

    parts = []
    for i, result in enumerate(results, 1):
        content = result.get("content", "")
        score = result.get("score", 0.0)
        metadata = result.get("metadata", {})

        # KG results: use entity_type and name for human-readable citations
        if source_label == "KnowledgeGraph":
            entity_type = metadata.get("entity_type", "Entity")
            name = result.get("name", "") or metadata.get("name", f"KG-{i}")
            body = content or result.get("episode_body", "")
            if len(body) > 600:
                body = body[:600] + "..."
            citation = f"[{entity_type}: {name}]"
            parts.append(f"### Result {i} (score: {score:.3f}) {citation}\n{body}")
            continue

        # Try to extract human-readable file path and heading
        canvas_file = metadata.get("canvas_file", "")
        heading = ""

        # Parse metadata_json if available (vault_notes store file_path + heading there)
        meta_json_str = metadata.get("metadata_json", "")
        source_type = "note"
        if meta_json_str and isinstance(meta_json_str, str):
            try:
                meta_parsed = _json.loads(meta_json_str)
                if not canvas_file:
                    canvas_file = meta_parsed.get("file_path", "")
                heading = meta_parsed.get("heading", "")
                source_type = meta_parsed.get("source_type", "note")
            except _json.JSONDecodeError:
                pass
        type_tag = "[Video] " if source_type == "video_transcript" else ""

        # Build citation as Obsidian wikilink [[file#heading|display]]
        if canvas_file:
            # Strip .md extension for Obsidian wikilinks
            file_display = canvas_file
            if file_display.endswith(".md"):
                file_display = file_display[:-3]

            # Clean heading: remove embedded wikilinks like [[01:19]]
            # and markdown link syntax like [text](url) to prevent nesting
            import re
            if heading:
                heading = re.sub(r'\[\[.*?\]\]', '', heading).strip()
                heading = re.sub(r'\[.*?\]\(.*?\)', '', heading).strip()
                # Remove trailing empty parens
                heading = re.sub(r'\(\)\s*$', '', heading).strip()

            if heading and heading != file_display:
                citation = f"[[{file_display}#{heading}|{heading}]]"
            else:
                citation = f"[[{file_display}]]"
        else:
            doc_id = result.get("doc_id", "")
            citation = f"[{source_label}: {doc_id}]" if doc_id else f"[{source_label}]"

        if len(content) > 500:
            content = content[:500] + "..."

        parts.append(f"### Result {i} (score: {score:.3f}) {type_tag}{citation}\n{content}")

    return "\n\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# Agent Runner
# ═══════════════════════════════════════════════════════════════════════════════

# CLI tools listed first so the agent prefers them over LanceDB search
REACT_TOOLS = [
    search_obsidian_cli,      # Primary search (CLI precise matching)
    search_knowledge_graph,    # Student knowledge graph (Graphiti)
    get_note_content,          # Read specific note content
    find_backlinks,            # Discover note connections
    get_note_outline,          # Note structure overview
    search_vault_notes,        # Semantic fallback (LanceDB embeddings)
    record_learning_memory,    # Record misconceptions/traps
]

# Round 4 Step 3b: Scoring agent needs search tools but not recording
SCORING_TOOLS = [
    search_obsidian_cli,
    search_knowledge_graph,
    get_note_content,
    search_vault_notes,
]


async def run_react_agent(
    agent_type: str,
    user_prompt: str,
    system_prompt: str,
    model_name: str = "gemini-2.5-flash",
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    thinking_budget: Optional[int] = None,
    recursion_limit: int = 10,
    tools: Optional[List] = None,
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
        from app.clients.gemini_client import _get_thinking_config
        config_params = _get_thinking_config(model_name, thinking_budget)
        if config_params:
            model_kwargs.update(config_params)

    model = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
        **model_kwargs,
    )

    agent = create_react_agent(model, tools or REACT_TOOLS, prompt=system_prompt)

    active_tools = tools or REACT_TOOLS
    logger.info(
        f"[ReactAgent] Running for {agent_type}, recursion_limit={recursion_limit}, "
        f"tools={[t.name for t in active_tools]}, "
        f"system_prompt_len={len(system_prompt)}, "
        f"user_prompt_len={len(user_prompt)}"
    )

    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=user_prompt)]},
        config={"recursion_limit": recursion_limit},
    )

    # Extract response from last message
    messages = result.get("messages", [])
    response_text = ""
    tool_calls_made = []
    tool_results = []  # R2a: Collect tool results for programmatic reference building

    for msg in messages:
        logger.debug(f"[ReactAgent] msg type={type(msg).__name__}, has_tool_calls={hasattr(msg, 'tool_calls') and bool(getattr(msg, 'tool_calls', None))}")
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls_made.append({
                    "name": tc.get("name", ""),
                    "args": tc.get("args", {}),
                })
                logger.info(f"[ReactAgent] Tool call: {tc.get('name', '')} args={tc.get('args', {})}")
        # R2a: Collect ToolMessage results (search outputs with real wikilinks)
        if type(msg).__name__ == "ToolMessage" and hasattr(msg, "content") and msg.content:
            tool_results.append({
                "name": getattr(msg, "name", ""),
                "content": msg.content,
            })
        if hasattr(msg, "content") and msg.content and type(msg).__name__ != "ToolMessage":
            response_text = msg.content  # Last non-tool content message is the answer

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
        "tool_results": tool_results,  # R2a: Real search results for programmatic refs
        "usage": {},  # LangChain doesn't expose token counts easily
    }
