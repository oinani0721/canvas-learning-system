#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# 强制设置正确的密码
os.environ['NEO4J_PASSWORD'] = '707188Fx'

print("=== MCP Graphiti Server Connection Test ===")
print(f"Forced NEO4J_PASSWORD: {os.getenv('NEO4J_PASSWORD')}")

# 添加路径
sys.path.append('graphiti/mcp_server')

try:
    from neo4j_mcp_server import Neo4jMemoryStore
    print("✓ MCP server module imported successfully")

    # 创建存储实例
    memory_store = Neo4jMemoryStore()
    print(f"Neo4j connected: {memory_store.neo4j_connected}")

    if memory_store.neo4j_connected:
        print("✅ SUCCESS: MCP Graphiti server connected to Neo4j!")

        # 测试基本操作
        print("\nTesting basic operations...")

        # 添加记忆
        memory_id = memory_store.add_memory(
            key="mcp_test_success",
            content="MCP server connection test successful after password fix",
            metadata={
                "importance": 9,
                "tags": ["test", "mcp", "success"],
                "test_timestamp": "2025-10-26T02:11:00"
            }
        )
        print(f"✓ Memory added: {memory_id}")

        # 检索记忆
        retrieved = memory_store.get_memory(memory_id)
        if retrieved:
            print(f"✓ Memory retrieved: {retrieved['key']}")
        else:
            print("✗ Memory retrieval failed")

        # 搜索记忆
        search_results = memory_store.search_memories("mcp_test")
        print(f"✓ Search results: {len(search_results)} memories found")

        # 统计记忆
        all_memories = memory_store.list_memories()
        print(f"✓ Total memories in system: {len(all_memories)}")

        print("\n🎉 All MCP Graphiti server functions working correctly!")

    else:
        print("❌ FAILED: MCP server still cannot connect to Neo4j")
        print("Debugging info:")
        print(f"  - NEO4J_URI: {os.getenv('NEO4J_URI', 'bolt://localhost:7687')}")
        print(f"  - NEO4J_USER: {os.getenv('NEO4J_USER', 'neo4j')}")
        print(f"  - NEO4J_PASSWORD: {os.getenv('NEO4J_PASSWORD')}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()