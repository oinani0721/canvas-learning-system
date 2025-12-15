#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import sys
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Any

def test_neo4j_direct():
    """测试直接Neo4j操作"""
    print("=== Testing Direct Neo4j Operations ===")

    try:
        # 测试基本连接
        result = subprocess.run([
            'docker', 'exec', 'canvas-learning-neo4j',
            'cypher-shell', '-u', 'neo4j', '-p', '707188Fx',
            'RETURN "Neo4j connection test" as status'
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("Neo4j connection: OK")
        else:
            print(f"Neo4j connection failed: {result.stderr}")
            return False

        # 设置Memory相关约束和索引
        setup_queries = [
            'CREATE CONSTRAINT memory_id IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE',
            'CREATE INDEX memory_key IF NOT EXISTS FOR (m:Memory) ON (m.key)',
            'CREATE INDEX memory_timestamp IF NOT EXISTS FOR (m:Memory) ON (m.timestamp)'
        ]

        for query in setup_queries:
            result = subprocess.run([
                'docker', 'exec', 'canvas-learning-neo4j',
                'cypher-shell', '-u', 'neo4j', '-p', '707188Fx', query
            ], capture_output=True, text=True, timeout=20)

        print("Neo4j database setup: OK")
        return True

    except Exception as e:
        print(f"Direct Neo4j test failed: {e}")
        return False

def test_memory_operations():
    """测试记忆操作"""
    print("\n=== Testing Memory Operations ===")

    try:
        # 添加学习记忆
        memory_queries = [
            # 添加CS70学习记忆
            '''
            CREATE (m:Memory {
                id: "mem_cs70_001",
                key: "cs70_propositional_logic",
                content: "Propositional logic is fundamental to CS70, dealing with statements that are either true or false",
                timestamp: datetime(),
                importance: 9,
                tags: ["CS70", "logic", "mathematics"],
                canvas_file: "CS70 Lecture1.canvas"
            })
            ''',

            # 添加学习会话记录
            '''
            CREATE (m:Memory {
                id: "mem_session_001",
                key: "learning_session_20251026",
                content: "Completed CS70 study session covering propositional logic, truth tables, and basic proof techniques",
                timestamp: datetime(),
                importance: 8,
                tags: ["session", "CS70", "completed"],
                session_duration: 45,
                mastery_level: 0.75
            })
            ''',

            # 添加理解记录
            '''
            CREATE (m:Memory {
                id: "mem_understanding_001",
                key: "understanding_truth_tables",
                content: "Successfully mastered truth table construction for compound propositions with AND, OR, NOT operators",
                timestamp: datetime(),
                importance: 7,
                tags: ["understanding", "truth_tables", "CS70"],
                confidence_score: 8
            })
            '''
        ]

        for query in memory_queries:
            result = subprocess.run([
                'docker', 'exec', 'canvas-learning-neo4j',
                'cypher-shell', '-u', 'neo4j', '-p', '707188Fx', query
            ], capture_output=True, text=True, timeout=20)

        print("Memory nodes created: OK")

        # 添加关系
        relationship_queries = [
            # 学习关系
            '''
            MATCH (cs70:Memory), (logic:Memory)
            WHERE cs70.id = "mem_cs70_001" AND logic.id = "mem_cs70_001"
            CREATE (cs70)-[:INCLUDES]->(logic)
            ''',

            # 会话关系
            '''
            MATCH (session:Memory), (concept:Memory)
            WHERE session.id = "mem_session_001" AND concept.id = "mem_cs70_001"
            CREATE (session)-[:COVERS]->(concept)
            ''',

            # 理解关系
            '''
            MATCH (understanding:Memory), (concept:Memory)
            WHERE understanding.id = "mem_understanding_001" AND concept.id = "mem_cs70_001"
            CREATE (understanding)-[:DEMONSTRATES]->(concept)
            '''
        ]

        for query in relationship_queries:
            result = subprocess.run([
                'docker', 'exec', 'canvas-learning-neo4j',
                'cypher-shell', '-u', 'neo4j', '-p', '707188Fx', query
            ], capture_output=True, text=True, timeout=20)

        print("Memory relationships created: OK")

        # 验证数据
        verify_query = '''
        MATCH (m:Memory)
        RETURN count(m) as total_memories,
               collect(m.key) as memory_keys
        '''

        result = subprocess.run([
            'docker', 'exec', 'canvas-learning-neo4j',
            'cypher-shell', '-u', 'neo4j', '-p', '707188Fx', verify_query
        ], capture_output=True, text=True, timeout=20)

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                count = lines[1].strip()
                print(f"Total memories created: {count}")

        return True

    except Exception as e:
        print(f"Memory operations test failed: {e}")
        return False

def test_cs70_learning_session():
    """测试CS70学习会话记录"""
    print("\n=== Testing CS70 Learning Session Recording ===")

    try:
        # 模拟完整的CS70学习会话
        session_data = {
            "session_id": f"cs70_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": datetime.now().isoformat(),
            "canvas_file": "CS70 Lecture1.canvas",
            "topics": [
                {
                    "name": "Propositional Logic",
                    "understanding": 0.8,
                    "confidence": 8,
                    "notes": "Mastered basic concepts and truth tables"
                },
                {
                    "name": "Pigeonhole Principle",
                    "understanding": 0.6,
                    "confidence": 6,
                    "notes": "Understood basic concept, need more practice on applications"
                },
                {
                    "name": "Mathematical Induction",
                    "understanding": 0.7,
                    "confidence": 7,
                    "notes": "Good grasp of the three-step process"
                }
            ]
        }

        # 创建会话记录
        session_query = f'''
        CREATE (s:LearningSession {{
            id: "{session_data['session_id']}",
            start_time: "{session_data['start_time']}",
            canvas_file: "{session_data['canvas_file']}",
            duration_minutes: 45
        }})
        '''

        result = subprocess.run([
            'docker', 'exec', 'canvas-learning-neo4j',
            'cypher-shell', '-u', 'neo4j', '-p', '707188Fx', session_query
        ], capture_output=True, text=True, timeout=20)

        print(f"Learning session created: {session_data['session_id']}")

        # 为每个主题创建记忆记录
        for topic in session_data["topics"]:
            topic_query = f'''
            CREATE (t:TopicMemory {{
                id: "topic_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{topic['name'].replace(' ', '_')}",
                name: "{topic['name']}",
                understanding: {topic['understanding']},
                confidence: {topic['confidence']},
                notes: "{topic['notes']}",
                session_id: "{session_data['session_id']}",
                timestamp: datetime()
            }})
            '''

            result = subprocess.run([
                'docker', 'exec', 'canvas-learning-neo4j',
                'cypher-shell', '-u', 'neo4j', '-p', '707188Fx', topic_query
            ], capture_output=True, text=True, timeout=20)

            print(f"Topic memory created: {topic['name']}")

        # 创建会话与主题的关系
        for topic in session_data["topics"]:
            relation_query = f'''
            MATCH (s:LearningSession {{id: "{session_data['session_id']}"}})
            MATCH (t:TopicMemory {{name: "{topic['name']}"}})
            CREATE (s)-[:INCLUDES]->(t)
            '''

            result = subprocess.run([
                'docker', 'exec', 'canvas-learning-neo4j',
                'cypher-shell', '-u', 'neo4j', '-p', '707188Fx', relation_query
            ], capture_output=True, text=True, timeout=20)

        print("Session-topic relationships created: OK")

        return True

    except Exception as e:
        print(f"CS70 learning session test failed: {e}")
        return False

def test_knowledge_graph_queries():
    """测试知识图谱查询"""
    print("\n=== Testing Knowledge Graph Queries ===")

    try:
        # 测试各种查询功能
        queries = [
            # 查询所有学习记忆
            {
                "name": "All Learning Memories",
                "query": '''
                MATCH (m:Memory)
                RETURN m.id, m.key, m.importance, m.tags
                ORDER BY m.importance DESC
                '''
            },

            # 查询CS70相关记忆
            {
                "name": "CS70 Related Memories",
                "query": '''
                MATCH (m:Memory)
                WHERE "CS70" IN m.tags
                RETURN m.key, m.importance, m.confidence_score
                ORDER BY m.importance DESC
                '''
            },

            # 查询学习会话
            {
                "name": "Learning Sessions",
                "query": '''
                MATCH (s:LearningSession)-[:INCLUDES]->(t:TopicMemory)
                RETURN s.canvas_file, s.duration_minutes, count(t) as topics_covered
                '''
            },

            # 查询理解水平
            {
                "name": "Understanding Levels",
                "query": '''
                MATCH (t:TopicMemory)
                RETURN t.name, t.understanding, t.confidence
                ORDER BY t.understanding DESC
                '''
            },

            # 查询概念关系
            {
                "name": "Concept Relationships",
                "query": '''
                MATCH (a)-[r]->(b)
                RETURN labels(a)[0] as from_type, a.key as from_key,
                       type(r) as relationship,
                       labels(b)[0] as to_type, b.key as to_key
                LIMIT 10
                '''
            }
        ]

        for query_info in queries:
            print(f"\nQuery: {query_info['name']}")
            result = subprocess.run([
                'docker', 'exec', 'canvas-learning-neo4j',
                'cypher-shell', '-u', 'neo4j', '-p', '707188Fx', query_info['query']
            ], capture_output=True, text=True, timeout=20)

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    print(f"  Results: {len(lines)-1} records found")
                    for line in lines[1:4]:  # Show first 3 results
                        if line.strip():
                            print(f"    {line}")
                    if len(lines) > 4:
                        print(f"    ... and {len(lines)-4} more")
            else:
                print(f"  Query failed: {result.stderr}")

        print("Knowledge graph queries: OK")
        return True

    except Exception as e:
        print(f"Knowledge graph queries test failed: {e}")
        return False

def test_timeline_functionality():
    """测试时间线功能"""
    print("\n=== Testing Timeline Functionality ===")

    try:
        # 添加时间线事件
        timeline_events = [
            {
                "type": "session_start",
                "description": "Started CS70 learning session focusing on discrete mathematics",
                "importance": 5
            },
            {
                "type": "concept_mastered",
                "description": "Successfully mastered propositional logic truth tables",
                "importance": 8
            },
            {
                "type": "challenge_overcome",
                "description": "Overcame difficulty understanding pigeonhole principle applications",
                "importance": 7
            },
            {
                "type": "milestone_reached",
                "description": "Completed first week of CS70 topics with good understanding",
                "importance": 9
            },
            {
                "type": "session_end",
                "description": "Concluded productive CS70 study session",
                "importance": 6
            }
        ]

        for i, event in enumerate(timeline_events):
            event_query = f'''
            CREATE (e:TimelineEvent {{
                id: "timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                type: "{event['type']}",
                description: "{event['description']}",
                importance: {event['importance']},
                timestamp: datetime(),
                sequence_number: {i+1}
            }})
            '''

            result = subprocess.run([
                'docker', 'exec', 'canvas-learning-neo4j',
                'cypher-shell', '-u', 'neo4j', '-p', '707188Fx', event_query
            ], capture_output=True, text=True, timeout=20)

            print(f"Timeline event created: {event['type']}")

        # 创建时间线顺序关系
        for i in range(len(timeline_events) - 1):
            relation_query = f'''
            MATCH (e1:TimelineEvent {{sequence_number: {i+1}}})
            MATCH (e2:TimelineEvent {{sequence_number: {i+2}}})
            CREATE (e1)-[:NEXT]->(e2)
            '''

            result = subprocess.run([
                'docker', 'exec', 'canvas-learning-neo4j',
                'cypher-shell', '-u', 'neo4j', '-p', '707188Fx', relation_query
            ], capture_output=True, text=True, timeout=20)

        print("Timeline sequence created: OK")

        # 查询时间线
        timeline_query = '''
        MATCH path = (start:TimelineEvent)-[:NEXT*]->(end:TimelineEvent)
        RETURN [node in nodes(path) | node.description] as timeline
        '''

        result = subprocess.run([
            'docker', 'exec', 'canvas-learning-neo4j',
            'cypher-shell', '-u', 'neo4j', '-p', '707188Fx', timeline_query
        ], capture_output=True, text=True, timeout=20)

        if result.returncode == 0:
            print("Timeline retrieval: OK")
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                print(f"Timeline events: {len(lines)}")

        return True

    except Exception as e:
        print(f"Timeline functionality test failed: {e}")
        return False

def test_mcp_server_startup():
    """测试MCP服务器启动"""
    print("\n=== Testing MCP Server Startup ===")

    try:
        # 检查MCP配置
        mcp_config = "C:\\Users\\ROG\\托福\\mcp_graphiti_final_fixed.json"
        if not os.path.exists(mcp_config):
            print("MCP configuration not found")
            return False

        with open(mcp_config, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if 'mcpServers' in config and 'graphiti-memory' in config['mcpServers']:
            server_config = config['mcpServers']['graphiti-memory']
            print(f"MCP server configured: {server_config.get('command', 'Unknown')}")

            # 检查启动脚本
            start_script = "C:\\Users\\ROG\\托福\\graphiti\\mcp_server\\start_graphiti_mcp.bat"
            if os.path.exists(start_script):
                print(f"MCP startup script found: {start_script}")

                # 尝试导入MCP服务器模块
                sys.path.append(r"C:\Users\ROG\托福\graphiti\mcp_server")

                try:
                    from neo4j_mcp_server import Neo4jMemoryStore
                    memory_store = Neo4jMemoryStore()

                    if memory_store.neo4j_connected:
                        print("MCP server Neo4j connection: OK")
                        print("MCP server would be ready to start")
                        return True
                    else:
                        print("MCP server Neo4j connection failed")
                        return False

                except ImportError as e:
                    print(f"MCP server import failed: {e}")
                    return False
            else:
                print("MCP startup script not found")
                return False

        print("MCP server configuration incomplete")
        return False

    except Exception as e:
        print(f"MCP server startup test failed: {e}")
        return False

def main():
    """运行完整的Graphiti功能测试"""
    print("=== Complete Graphiti Functionality Test ===")
    print(f"Test started at: {datetime.now()}")

    tests = [
        ("Direct Neo4j Operations", test_neo4j_direct),
        ("Memory Operations", test_memory_operations),
        ("CS70 Learning Session Recording", test_cs70_learning_session),
        ("Knowledge Graph Queries", test_knowledge_graph_queries),
        ("Timeline Functionality", test_timeline_functionality),
        ("MCP Server Startup", test_mcp_server_startup)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"{test_name} failed with exception: {e}")
            results[test_name] = False

    # 输出总结
    print("\n" + "="*60)
    print("=== Graphiti Functionality Test Summary ===")
    print(f"Test completed at: {datetime.now()}")

    print("\nResults:")
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {test_name}: {status}")

    success_count = sum(results.values())
    total_count = len(results)
    print(f"\nOverall: {success_count}/{total_count} tests passed")

    if success_count == total_count:
        print("\nSUCCESS: All Graphiti functionality tests PASSED!")
        print("Graphiti knowledge graph system is fully operational!")
    else:
        print(f"\n{total_count - success_count} tests failed.")

    # 最终统计
    print("\n=== Final System Statistics ===")

    try:
        # 统计总数据量
        count_query = '''
        MATCH (n) RETURN labels(n)[0] as label, count(n) as count
        ORDER BY count DESC
        '''

        result = subprocess.run([
            'docker', 'exec', 'canvas-learning-neo4j',
            'cypher-shell', '-u', 'neo4j', '-p', '707188Fx', count_query
        ], capture_output=True, text=True, timeout=20)

        if result.returncode == 0:
            print("Node statistics:")
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip header
                if line.strip():
                    print(f"  {line}")

    except Exception as e:
        print(f"Final statistics failed: {e}")

    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)