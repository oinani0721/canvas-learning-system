#!/usr/bin/env python3
"""
测试Graphiti Neo4j连接
"""
import os
import sys

# 设置环境变量
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"

try:
    from neo4j import GraphDatabase
    print("Neo4j driver imported - OK")

    # 测试连接
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "password")
    )

    with driver.session() as session:
        result = session.run("RETURN 1 as test")
        record = result.single()
        print(f"Neo4j connection successful: {record['test']}")

        # 测试创建节点和关系
        session.run("MERGE (a:Test {name: 'Math53'})")
        session.run("MERGE (b:Test {name: 'LevelSet'})")
        session.run("MATCH (a:Test {name: 'Math53'}), (b:Test {name: 'LevelSet'}) MERGE (a)-[:LEARNS]->(b)")
        print("Test nodes and relationship created - OK")

    driver.close()

    # 现在测试Graphiti内存系统
    print("\nTesting Graphiti Memory System...")

    # 添加到Graphiti当前目录
    sys.path.insert(0, r"C:\Users\ROG\托福\graphiti\mcp_server")

    from neo4j_mcp_server import Neo4jMemoryStore

    memory_store = Neo4jMemoryStore()

    if memory_store.neo4j_connected:
        print("Graphiti Memory Store connected to Neo4j - OK")

        # 测试添加记忆
        memory_id = memory_store.add_memory(
            key="test_memory_final",
            content="这是测试Neo4j图关系功能的记忆",
            metadata={"importance": 8, "tags": ["test", "neo4j", "graphiti"]}
        )
        print(f"Memory added with ID: {memory_id} - OK")

        # 测试添加关系
        try:
            success = memory_store.add_relationship(
                entity1="Math53学习会话",
                entity2="LevelSet概念",
                relationship_type="学习主题"
            )
            if success:
                print("Relationship added successfully - OK!")
            else:
                print("Failed to add relationship")
        except Exception as e:
            print(f"Error adding relationship: {e}")

    else:
        print("Graphiti Memory Store not connected to Neo4j - FAILED")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()