#!/usr/bin/env python3
"""
修复版本的Graphiti Memory MCP Server
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("graphiti-memory")

# 简单的内存存储
class MemoryStore:
    def __init__(self):
        self.memories: Dict[str, Dict[str, Any]] = {}
        self.relationships: Dict[str, List[Dict[str, str]]] = {}
        self.counter = 0
    
    def add_memory(self, key: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加记忆"""
        self.counter += 1
        memory_id = f"mem_{self.counter}"
        
        self.memories[memory_id] = {
            "key": key,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "id": memory_id
        }
        logger.info(f"Added memory: {memory_id} - {key}")
        return memory_id
    
    def get_memory(self, memory_id: str) -> Dict[str, Any] | None:
        """获取记忆"""
        return self.memories.get(memory_id)
    
    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        """搜索记忆"""
        results = []
        query_lower = query.lower()
        
        for memory_id, memory in self.memories.items():
            if (query_lower in memory["key"].lower() or 
                query_lower in memory["content"].lower()):
                results.append(memory)
        
        logger.info(f"Search '{query}' found {len(results)} results")
        return results
    
    def list_memories(self) -> List[Dict[str, Any]]:
        """列出所有记忆"""
        return list(self.memories.values())
    
    def add_relationship(self, entity1: str, entity2: str, relationship_type: str) -> str:
        """添加关系"""
        if entity1 not in self.relationships:
            self.relationships[entity1] = []
        
        relationship = {
            "target": entity2,
            "type": relationship_type,
            "timestamp": datetime.now().isoformat()
        }
        
        self.relationships[entity1].append(relationship)
        logger.info(f"Added relationship: {entity1} -{relationship_type}-> {entity2}")
        return f"Relationship added: {entity1} -{relationship_type}-> {entity2}"

# 初始化内存存储
memory_store = MemoryStore()

# 创建服务器实例
server = Server("graphiti-memory")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """
    列出可用工具
    """
    tools = [
        types.Tool(
            name="add_memory",
            description="Add a new memory to the knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "A unique identifier or title for this memory"
                    },
                    "content": {
                        "type": "string", 
                        "description": "The content or information to store in memory"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Optional metadata associated with this memory",
                        "properties": {
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tags to categorize this memory"
                            },
                            "importance": {
                                "type": "number",
                                "description": "Importance level from 1-10"
                            }
                        }
                    }
                },
                "required": ["key", "content"]
            }
        ),
        types.Tool(
            name="search_memories",
            description="Search through stored memories using keywords",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find relevant memories"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_memory",
            description="Retrieve a specific memory by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "The unique ID of the memory to retrieve"
                    }
                },
                "required": ["memory_id"]
            }
        ),
        types.Tool(
            name="list_memories",
            description="List all stored memories",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="add_relationship",
            description="Add a relationship between two entities in the knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity1": {
                        "type": "string",
                        "description": "The first entity in the relationship"
                    },
                    "entity2": {
                        "type": "string", 
                        "description": "The second entity in the relationship"
                    },
                    "relationship_type": {
                        "type": "string",
                        "description": "The type of relationship (e.g., 'is_related_to', 'depends_on', 'contains')"
                    }
                },
                "required": ["entity1", "entity2", "relationship_type"]
            }
        )
    ]
    
    logger.info(f"Returning {len(tools)} tools")
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> List[types.TextContent]:
    """
    处理工具调用
    """
    try:
        if arguments is None:
            arguments = {}
            
        logger.info(f"Tool called: {name} with arguments: {arguments}")
        
        if name == "add_memory":
            key = arguments.get("key", "")
            content = arguments.get("content", "")
            metadata = arguments.get("metadata", {})
            
            if not key or not content:
                return [types.TextContent(
                    type="text",
                    text="Error: Both 'key' and 'content' are required"
                )]
            
            memory_id = memory_store.add_memory(key, content, metadata)
            
            return [types.TextContent(
                type="text",
                text=f"✅ Memory added successfully!\nID: {memory_id}\nKey: {key}\nContent: {content[:100]}{'...' if len(content) > 100 else ''}"
            )]
        
        elif name == "search_memories":
            query = arguments.get("query", "")
            if not query:
                return [types.TextContent(
                    type="text", 
                    text="Error: 'query' parameter is required"
                )]
            
            results = memory_store.search_memories(query)
            
            if not results:
                return [types.TextContent(
                    type="text",
                    text=f"🔍 No memories found matching '{query}'"
                )]
            
            result_text = f"🔍 Found {len(results)} memories matching '{query}':\n\n"
            for memory in results[:5]:  # Limit to 5 results
                result_text += f"• **{memory['key']}** (ID: {memory['id']})\n"
                result_text += f"  {memory['content'][:150]}{'...' if len(memory['content']) > 150 else ''}\n\n"
            
            if len(results) > 5:
                result_text += f"... and {len(results) - 5} more results"
            
            return [types.TextContent(type="text", text=result_text)]
        
        elif name == "get_memory":
            memory_id = arguments.get("memory_id", "")
            if not memory_id:
                return [types.TextContent(
                    type="text",
                    text="Error: 'memory_id' parameter is required"
                )]
            
            memory = memory_store.get_memory(memory_id)
            if not memory:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Memory with ID '{memory_id}' not found"
                )]
            
            result_text = f"📝 **Memory Details**\n\n"
            result_text += f"**ID:** {memory['id']}\n"
            result_text += f"**Key:** {memory['key']}\n"
            result_text += f"**Content:** {memory['content']}\n"
            result_text += f"**Timestamp:** {memory['timestamp']}\n"
            
            if memory['metadata']:
                result_text += f"**Metadata:** {json.dumps(memory['metadata'], indent=2)}\n"
            
            return [types.TextContent(type="text", text=result_text)]
        
        elif name == "list_memories":
            memories = memory_store.list_memories()
            
            if not memories:
                return [types.TextContent(
                    type="text",
                    text="📝 No memories stored yet. Use 'add_memory' to create some!"
                )]
            
            result_text = f"📝 **All Memories** ({len(memories)} total)\n\n"
            for memory in memories:
                result_text += f"• **{memory['key']}** (ID: {memory['id']})\n"
                result_text += f"  {memory['content'][:100]}{'...' if len(memory['content']) > 100 else ''}\n\n"
            
            return [types.TextContent(type="text", text=result_text)]
        
        elif name == "add_relationship":
            entity1 = arguments.get("entity1", "")
            entity2 = arguments.get("entity2", "")
            relationship_type = arguments.get("relationship_type", "")
            
            if not all([entity1, entity2, relationship_type]):
                return [types.TextContent(
                    type="text",
                    text="Error: 'entity1', 'entity2', and 'relationship_type' are all required"
                )]
            
            result = memory_store.add_relationship(entity1, entity2, relationship_type)
            
            return [types.TextContent(
                type="text",
                text=f"🔗 {result}"
            )]
        
        else:
            return [types.TextContent(
                type="text",
                text=f"❌ Unknown tool: {name}"
            )]
    
    except Exception as e:
        logger.error(f"Error in tool call {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"❌ Error executing {name}: {str(e)}"
        )]

async def main():
    """主函数"""
    # 获取环境变量
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    
    logger.info("🚀 Starting Graphiti Memory MCP Server")
    logger.info(f"Neo4j URI: {neo4j_uri}")
    logger.info("Memory store initialized")
    
    # 启动服务器
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, 
            write_stream, 
            InitializationOptions(
                server_name="graphiti-memory",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            )
        )

if __name__ == "__main__":
    asyncio.run(main()) 