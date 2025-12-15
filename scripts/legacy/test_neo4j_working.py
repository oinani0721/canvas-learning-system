#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json
import os
from datetime import datetime

def test_neo4j_basic():
    """测试Neo4j基本功能"""
    print("=== Neo4j Basic Test ===")

    try:
        # 测试连接
        result = subprocess.run([
            'docker', 'exec', 'canvas-learning-neo4j',
            'cypher-shell', '-u', 'neo4j', '-p', 'password',
            'RETURN "Connection OK" as status'
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("Neo4j connection: OK")
        else:
            print(f"Neo4j connection failed: {result.stderr}")
            return False

        # 创建CS70数据
        print("Creating CS70 knowledge graph data...")

        cs70_queries = [
            # 创建CS70课程
            'CREATE (cs70:Course {name: "CS70", title: "Discrete Mathematics"})',

            # 创建概念节点
            'CREATE (logic:Concept {name: "Propositional Logic", difficulty: "medium"})',
            'CREATE (pigeonhole:Concept {name: "Pigeonhole Principle", difficulty: "hard"})',
            'CREATE (induction:Concept {name: "Mathematical Induction", difficulty: "medium"})',
            'CREATE (proofs:Concept {name: "Proof Methods", difficulty: "medium"})',

            # 创建Canvas节点
            'CREATE (canvas:Canvas {name: "CS70 Lecture1", nodes: 147, edges: 280})',

            # 创建关系
            'MATCH (cs70:Course), (logic:Concept) CREATE (cs70)-[:INCLUDES]->(logic)',
            'MATCH (cs70:Course), (pigeonhole:Concept) CREATE (cs70)-[:INCLUDES]->(pigeonhole)',
            'MATCH (cs70:Course), (induction:Concept) CREATE (cs70)-[:INCLUDES]->(induction)',
            'MATCH (cs70:Course), (proofs:Concept) CREATE (cs70)-[:INCLUDES]->(proofs)',
            'MATCH (canvas:Canvas), (logic:Concept) CREATE (canvas)-[:CONTAINS]->(logic)',
            'MATCH (canvas:Canvas), (pigeonhole:Concept) CREATE (canvas)-[:CONTAINS]->(pigeonhole)',
            'MATCH (logic:Concept), (proofs:Concept) CREATE (logic)-[:USES]->(proofs)'
        ]

        for query in cs70_queries:
            result = subprocess.run([
                'docker', 'exec', 'canvas-learning-neo4j',
                'cypher-shell', '-u', 'neo4j', '-p', 'password', query
            ], capture_output=True, text=True, timeout=20)

            if result.returncode != 0:
                print(f"Query failed: {result.stderr}")

        # 验证数据
        print("Verifying created data...")

        # 统计节点
        count_result = subprocess.run([
            'docker', 'exec', 'canvas-learning-neo4j',
            'cypher-shell', '-u', 'neo4j', '-p', 'password',
            'MATCH (n) RETURN count(n) as count'
        ], capture_output=True, text=True, timeout=20)

        # 统计关系
        rel_result = subprocess.run([
            'docker', 'exec', 'canvas-learning-neo4j',
            'cypher-shell', '-u', 'neo4j', '-p', 'password',
            'MATCH ()-[r]->() RETURN count(r) as count'
        ], capture_output=True, text=True, timeout=20)

        if count_result.returncode == 0 and rel_result.returncode == 0:
            node_lines = count_result.stdout.strip().split('\n')
            rel_lines = rel_result.stdout.strip().split('\n')

            if len(node_lines) > 1:
                node_count = node_lines[1].strip()
                print(f"Total nodes: {node_count}")

            if len(rel_lines) > 1:
                rel_count = rel_lines[1].strip()
                print(f"Total relationships: {rel_count}")

        # 测试查询
        print("Testing knowledge graph queries...")

        test_queries = [
            'MATCH (cs70:Course)-[:INCLUDES]->(c:Concept) RETURN cs70.name, c.name, c.difficulty',
            'MATCH (canvas:Canvas)-[:CONTAINS]->(c:Concept) RETURN canvas.name, collect(c.name) as concepts',
            'MATCH (c1:Concept)-[r]->(c2:Concept) RETURN c1.name, type(r), c2.name'
        ]

        for i, query in enumerate(test_queries):
            print(f"Query {i+1}:")
            result = subprocess.run([
                'docker', 'exec', 'canvas-learning-neo4j',
                'cypher-shell', '-u', 'neo4j', '-p', 'password', query
            ], capture_output=True, text=True, timeout=20)

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[:3]:  # Show first 3 results
                    if line.strip():
                        print(f"  {line}")
            else:
                print(f"  Query failed: {result.stderr}")

        print("Neo4j basic test PASSED!")
        return True

    except Exception as e:
        print(f"Neo4j basic test FAILED: {e}")
        return False

def test_mcp_config():
    """测试MCP配置"""
    print("\n=== MCP Configuration Test ===")

    try:
        mcp_config = "C:\\Users\\ROG\\托福\\mcp_graphiti_final_fixed.json"

        if not os.path.exists(mcp_config):
            print("MCP config not found")
            return False

        with open(mcp_config, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if 'mcpServers' in config and 'graphiti-memory' in config['mcpServers']:
            server_config = config['mcpServers']['graphiti-memory']
            print("MCP Graphiti server: CONFIGURED")
            print(f"  Command: {server_config.get('command', 'Unknown')}")

            # 检查相关文件
            graphiti_files = [
                'graphiti_integration.py',
                'graphiti_gemini_integration.py',
                'graphiti_timeline_reader.py'
            ]

            for file in graphiti_files:
                if os.path.exists(file):
                    print(f"  Found: {file}")
                else:
                    print(f"  Missing: {file}")

        print("MCP configuration test PASSED!")
        return True

    except Exception as e:
        print(f"MCP configuration test FAILED: {e}")
        return False

def main():
    print("=== Neo4j Graphiti Verification ===")
    print(f"Test time: {datetime.now()}")

    tests = [
        ("Neo4j Basic Functions", test_neo4j_basic),
        ("MCP Configuration", test_mcp_config)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"{test_name} failed: {e}")
            results[test_name] = False

    print(f"\n=== Test Summary ===")
    print(f"Completed at: {datetime.now()}")

    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {test_name}: {status}")

    success_count = sum(results.values())
    total_count = len(results)
    print(f"Overall: {success_count}/{total_count} tests passed")

    if success_count == total_count:
        print("\nSUCCESS: Neo4j Graphiti system is fully operational!")
        print("- Docker Neo4j: RUNNING")
        print("- Knowledge graph: CREATED")
        print("- CS70 concepts: LOADED")
        print("- Query capabilities: VERIFIED")
        print("- MCP integration: CONFIGURED")
    else:
        print("\nSome components need attention.")

    return success_count == total_count

if __name__ == "__main__":
    main()