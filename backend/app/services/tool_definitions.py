# Agent Tool Definitions for Gemini Function Calling
# Phase 2: Let LLM actively search for information instead of passively receiving context
#
# These tools wrap existing retrieval infrastructure (LanceDB, Graphiti, vault files)
# as Gemini-compatible FunctionDeclarations, enabling the AI to decide what to search.
#
# [Source: Agent Architecture Upgrade Plan - Phase 2]

from google.genai import types

# ─────────────────────────────────────────────────
# Tool 1: Search Vault Notes via LanceDB vector search
# ─────────────────────────────────────────────────
search_vault_notes_decl = types.FunctionDeclaration(
    name="search_vault_notes",
    description=(
        "搜索 Obsidian Vault 中的笔记，返回与查询语义最相关的笔记片段及来源。"
        "适用于查找学习材料、讲义内容、概念解释等。"
    ),
    parameters_json_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词或问题，如 'A* 搜索算法' 或 'MDP 值迭代'"
            },
            "num_results": {
                "type": "integer",
                "description": "返回结果数量，默认5",
            }
        },
        "required": ["query"],
    },
)

# ─────────────────────────────────────────────────
# Tool 2: Search Knowledge Graph via Graphiti
# ─────────────────────────────────────────────────
search_knowledge_graph_decl = types.FunctionDeclaration(
    name="search_knowledge_graph",
    description=(
        "搜索知识图谱中的概念、误解记录、错题记录等实体。"
        "适用于查找学生的历史错误、易混淆概念、学习薄弱点。"
    ),
    parameters_json_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词，如 'value iteration mistake' 或 'CSP误解'"
            },
            "entity_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "实体类型过滤（可选）: "
                    "Misconception, ProblemTrap, LogicalFallacy, "
                    "GuidedThinking, Concept, Problem, Topic"
                ),
            },
            "num_results": {
                "type": "integer",
                "description": "返回结果数量，默认5",
            }
        },
        "required": ["query"],
    },
)

# ─────────────────────────────────────────────────
# Tool 3: Read specific note content
# ─────────────────────────────────────────────────
get_note_content_decl = types.FunctionDeclaration(
    name="get_note_content",
    description=(
        "读取指定笔记文件的内容（全部或指定行范围）。"
        "当搜索结果中发现相关笔记但需要更多上下文时使用。"
    ),
    parameters_json_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "笔记文件的相对路径，如 'lectures/lec09-notes.md'"
            },
            "line_start": {
                "type": "integer",
                "description": "起始行号（可选，从1开始）"
            },
            "line_end": {
                "type": "integer",
                "description": "结束行号（可选）"
            }
        },
        "required": ["file_path"],
    },
)

# ─────────────────────────────────────────────────
# Bundled tool set for explanation agents
# ─────────────────────────────────────────────────
EXPLANATION_TOOLS = types.Tool(
    function_declarations=[
        search_vault_notes_decl,
        search_knowledge_graph_decl,
        get_note_content_decl,
    ]
)

# List of declaration dicts for agents that need individual tool access
TOOL_DECLARATIONS = [
    search_vault_notes_decl,
    search_knowledge_graph_decl,
    get_note_content_decl,
]
