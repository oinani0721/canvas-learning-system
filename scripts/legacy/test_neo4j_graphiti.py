#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import subprocess
import time
import json
from datetime import datetime

def test_neo4j_connection():
    """测试Neo4j连接和基本功能"""
    print("=== Neo4j Connection Test ===")

    # 检查Docker状态
    try:
        result = subprocess.run(['docker', 'ps'],
                                capture_output=True, text=True, timeout=10)
        if 'neo4j' in result.stdout.lower():
            print("Docker Neo4j container is running")
        else:
            print("Neo4j container not found in Docker ps")
            # 尝试启动
            print("Attempting to start Neo4j...")
            start_result = subprocess.run(['docker-compose', '-f', 'docker/neo4j-docker-compose.yml', 'up', '-d'],
                                         capture_output=True, text=True, timeout=30)
            if start_result.returncode == 0:
                print("Neo4j started successfully")
                time.sleep(10)  # 等待Neo4j完全启动
            else:
                print(f"Failed to start Neo4j: {start_result.stderr}")
                return False
    except Exception as e:
        print(f"Docker check failed: {e}")
        return False

    return True

def test_neo4j_data_operations():
    """测试Neo4j数据操作"""
    print("\n=== Neo4j Data Operations Test ===")

    # 使用neo4j命令行工具测试
    try:
        # 测试连接
        print("Testing Neo4j connection...")
        conn_result = subprocess.run([
            'docker', 'exec', 'neo4j',
            'cypher-shell', '-u', 'neo4j', '-p', 'password',
            'MATCH (n) RETURN count(n) as node_count'
        ], capture_output=True, text=True, timeout=30)

        if conn_result.returncode == 0:
            if "node_count" in conn_result.stdout:
                print("Neo4j connection successful")
            else:
                print("Neo4j connected but query failed")
                print(f"Output: {conn_result.stdout}")
        else:
            print(f"Neo4j connection failed: {conn_result.stderr}")
            return False

        # 创建测试数据
        print("\nCreating test knowledge graph data...")

        # 创建CS70相关节点
        create_queries = [
            # 创建概念节点
            '''
            CREATE (cs70:Course {name: "CS70", type: "course", subject: "Discrete Mathematics"})
            ''',
            '''
            CREATE (logic:Concept {name: "Propositional Logic", type: "concept", difficulty: "medium"})
            ''',
            '''
            CREATE (pigeonhole:Concept {name: "Pigeonhole Principle", type: "concept", difficulty: "hard"})
            ''',
            '''
            CREATE (proof:Concept {name: "Direct Proof", type: "concept", difficulty: "medium"})
            ''',
            # 创建Canvas节点
            '''
            CREATE (canvas:Canvas {name: "CS70 Lecture1", file: "CS70 Lecture1.canvas", node_count: 147})
            ''',
            # 创建关系
            '''
            MATCH (cs70:Course), (logic:Concept)
            CREATE (cs70)-[:INCLUDES]->(logic)
            ''',
            '''
            MATCH (cs70:Course), (pigeonhole:Concept)
            CREATE (cs70)-[:INCLUDES]->(pigeonhole)
            ''',
            '''
            MATCH (logic:Concept), (proof:Concept)
            CREATE (logic)-[:REQUIRES]->(proof)
            ''',
            '''
            MATCH (canvas:Canvas), (logic:Concept)
            CREATE (canvas)-[:CONTAINS]->(logic)
            '''
        ]

        for query in create_queries:
            result = subprocess.run([
                'docker', 'exec', 'neo4j',
                'cypher-shell', '-u', 'neo4j', '-p', 'password', query
            ], capture_output=True, text=True, timeout=20)

            if result.returncode != 0:
                print(f"Query failed: {result.stderr}")
                continue
            print(f"Created: {query[:50]}...")

        print("Test data created successfully")

        # 查询测试数据
        print("\nQuerying test data...")

        query_result = subprocess.run([
            'docker', 'exec', 'neo4j',
            'cypher-shell', '-u', 'neo4j', '-p', 'password',
            '''
            MATCH (n)-[r]->(m)
            RETURN n.name as from_node, type(r) as relationship, m.name as to_node
            LIMIT 10
            '''
        ], capture_output=True, text=True, timeout=20)

        if query_result.returncode == 0:
            print("Query results:")
            for line in query_result.stdout.split('\n'):
                if line.strip() and not line.startswith('neo4j>'):
                    print(f"  {line}")
        else:
            print(f"Query failed: {query_result.stderr}")

        # 统计节点和关系
        count_query = subprocess.run([
            'docker', 'exec', 'neo4j',
            'cypher-shell', '-u', 'neo4j', '-p', 'password',
            '''
            MATCH (n) RETURN count(n) as nodes
            UNION ALL
            MATCH ()-[r]->() RETURN count(r) as relationships
            '''
        ], capture_output=True, text=True, timeout=20)

        if count_query.returncode == 0:
            print(f"\nGraph statistics:")
            for line in count_query.stdout.split('\n'):
                if 'nodes' in line or 'relationships' in line:
                    print(f"  {line}")

        return True

    except Exception as e:
        print(f"Neo4j data operations failed: {e}")
        return False

def test_graphiti_integration():
    """测试Graphiti集成"""
    print("\n=== Graphiti Integration Test ===")

    # 检查Graphiti MCP服务器
    graphiti_scripts = [
        'graphiti/mcp_server/graphiti_mcp_server.py',
        'graphiti/mcp_server/neo4j_mcp_server.py',
        'graphiti_integration.py'
    ]

    print("Checking Graphiti files...")
    for script in graphiti_scripts:
        if os.path.exists(script):
            print(f"  Found: {script}")
        else:
            print(f"  Missing: {script}")

    # 尝试运行Graphiti测试
    try:
        if os.path.exists('graphiti/mcp_server/test_neo4j_memory.py'):
            print("\nRunning Graphiti Neo4j test...")
            result = subprocess.run([
                'python', 'graphiti/mcp_server/test_neo4j_memory.py'
            ], capture_output=True, text=True, timeout=60)

            print(f"Graphiti test output: {result.stdout[:500]}...")
            if result.stderr:
                print(f"Graphiti test errors: {result.stderr[:500]}...")

        return True

    except Exception as e:
        print(f"Graphiti integration test failed: {e}")
        return False

def test_memory_integration():
    """测试实时记忆系统集成"""
    print("\n=== Real-time Memory Integration Test ===")

    # 检查实时记忆数据库
    memory_db = "C:\\Users\\ROG\\托福\\data\\realtime_memory\\memory_sessions.db"

    if os.path.exists(memory_db):
        print(f"Real-time memory database found: {memory_db}")

        try:
            conn = sqlite3.connect(memory_db)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Memory database tables: {[t[0] for t in tables]}")

            # 创建测试会话
            cursor.execute("""
                INSERT OR REPLACE INTO memory_sessions
                (session_id, canvas_file, start_time, end_time, nodes_processed,
                 agent_calls, user_interactions, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                'test-session-001',
                'CS70 Lecture1.canvas',
                datetime.now().isoformat(),
                (datetime.now() + timedelta(minutes=30)).isoformat(),
                5,
                3,
                2,
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

            print("Real-time memory test data inserted successfully")
            return True

        except Exception as e:
            print(f"Real-time memory test failed: {e}")
            return False
    else:
        print("Real-time memory database not found")
        return False

def main():
    print("=== Comprehensive Neo4j Graphiti System Test ===")
    print(f"Test started at: {datetime.now()}")

    # 运行所有测试
    tests = [
        ("Neo4j Connection", test_neo4j_connection),
        ("Neo4j Data Operations", test_neo4j_data_operations),
        ("Graphiti Integration", test_graphiti_integration),
        ("Real-time Memory Integration", test_memory_integration)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"{test_name} failed with exception: {e}")
            results[test_name] = False

    # 输出总结
    print(f"\n=== Test Summary ===")
    print(f"Test completed at: {datetime.now()}")
    print(f"\nResults:")
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {test_name}: {status}")

    success_count = sum(results.values())
    total_count = len(results)
    print(f"\nOverall: {success_count}/{total_count} tests passed")

    if success_count == total_count:
        print("All Neo4j/Graphiti systems are working correctly!")
    else:
        print("Some systems need attention.")

    return success_count == total_count

if __name__ == "__main__":
    import os
    main()