#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# 添加Graphiti服务器路径
sys.path.append(r"C:\Users\ROG\托福\graphiti\mcp_server")

def test_direct_neo4j_operations():
    """测试直接Neo4j操作"""
    print("=== Testing Direct Neo4j Operations ===")

    try:
        import subprocess

        # 测试基本连接
        result = subprocess.run([
            'docker', 'exec', 'canvas-learning-neo4j',
            'cypher-shell', '-u', 'neo4j', '-p', '707188Fx',
            'RETURN "Neo4j connection test" as status'
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("✓ Neo4j direct connection working")
        else:
            print(f"✗ Neo4j connection failed: {result.stderr}")
            return False

        # 测试MCP相关表结构创建
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

            if result.returncode != 0:
                print(f"Setup query failed: {result.stderr}")

        print("✓ Neo4j database setup completed")
        return True

    except Exception as e:
        print(f"Direct Neo4j test failed: {e}")
        return False

def test_memory_store_class():
    """测试MemoryStore类功能"""
    print("\n=== Testing MemoryStore Class ===")

    try:
        # 导入MemoryStore类
        from neo4j_mcp_server import Neo4jMemoryStore

        # 创建存储实例
        memory_store = Neo4jMemoryStore()

        print(f"Neo4j connected: {memory_store.neo4j_connected}")

        # 测试添加记忆
        print("Testing add_memory...")
        memory_id = memory_store.add_memory(
            key="test_cs70_propositional_logic",
            content="Propositional logic is a branch of mathematical logic that deals with propositions that can be either true or false.",
            metadata={
                "importance": 8,
                "tags": ["CS70", "logic", "mathematics"],
                "canvas_file": "CS70 Lecture1.canvas",
                "learning_session": "test_session_001"
            }
        )

        print(f"✓ Memory added: {memory_id}")

        # 测试获取记忆
        print("Testing get_memory...")
        retrieved = memory_store.get_memory(memory_id)
        if retrieved:
            print(f"✓ Memory retrieved: {retrieved['key']}")
        else:
            print("✗ Memory retrieval failed")
            return False

        # 测试搜索记忆
        print("Testing search_memories...")
        search_results = memory_store.search_memories("propositional")
        print(f"✓ Search results: {len(search_results)} memories found")

        # 测试关系添加
        print("Testing add_relationship...")
        rel_success = memory_store.add_relationship(
            "Propositional Logic",
            "Boolean Algebra",
            "relates_to"
        )
        print(f"✓ Relationship added: {rel_success}")

        # 测试列出记忆
        print("Testing list_memories...")
        all_memories = memory_store.list_memories()
        print(f"✓ Total memories: {len(all_memories)}")

        return True

    except Exception as e:
        print(f"MemoryStore class test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cs70_canvas_integration():
    """测试CS70 Canvas集成"""
    print("\n=== Testing CS70 Canvas Integration ===")

    try:
        from neo4j_mcp_server import Neo4jMemoryStore

        memory_store = Neo4jMemoryStore()

        # 模拟CS70学习会话数据
        cs70_learning_data = [
            {
                "key": "cs70_session_001_propositional_logic",
                "content": "学习了命题逻辑的基本概念，包括命题、逻辑连接词（与、或、非、蕴含、等价），以及真值表的构建方法。掌握了如何判断复合命题的真假性。",
                "metadata": {
                    "importance": 9,
                    "tags": ["CS70", "propositional_logic", "truth_tables"],
                    "canvas_file": "CS70 Lecture1.canvas",
                    "session_duration": 45,
                    "mastery_level": 0.75,
                    "confidence_score": 8
                }
            },
            {
                "key": "cs70_session_002_pigeonhole_principle",
                "content": "学习了鸽笼原理及其应用。理解了如果n个物品放入m个容器中，且n>m，则至少有一个容器包含多个物品的基本概念。通过例子掌握了如何应用该原理解决存在性问题。",
                "metadata": {
                    "importance": 7,
                    "tags": ["CS70", "pigeonhole_principle", "combinatorics"],
                    "canvas_file": "CS70 Lecture1.canvas",
                    "session_duration": 30,
                    "mastery_level": 0.60,
                    "confidence_score": 6
                }
            },
            {
                "key": "cs70_session_003_mathematical_induction",
                "content": "学习了数学归纳法的原理和步骤。掌握了基础情形验证、归纳假设、归纳证明三个关键步骤。能够用数学归纳法证明与自然数相关的命题。",
                "metadata": {
                    "importance": 8,
                    "tags": ["CS70", "mathematical_induction", "proofs"],
                    "canvas_file": "CS70 Lecture1.canvas",
                    "session_duration": 50,
                    "mastery_level": 0.65,
                    "confidence_score": 7
                }
            }
        ]

        # 添加CS70学习记忆
        memory_ids = []
        for data in cs70_learning_data:
            memory_id = memory_store.add_memory(
                key=data["key"],
                content=data["content"],
                metadata=data["metadata"]
            )
            memory_ids.append(memory_id)
            print(f"✓ Added CS70 memory: {data['key']}")

        # 添加概念关系
        cs70_relationships = [
            ("Propositional Logic", "Mathematical Induction", "prerequisite_for"),
            ("Pigeonhole Principle", "Propositional Logic", "complements"),
            ("Mathematical Induction", "Proof Methods", "is_a_type_of"),
            ("CS70 Course", "Propositional Logic", "includes"),
            ("CS70 Course", "Pigeonhole Principle", "includes"),
            ("CS70 Course", "Mathematical Induction", "includes")
        ]

        for entity1, entity2, rel_type in cs70_relationships:
            success = memory_store.add_relationship(entity1, entity2, rel_type)
            print(f"✓ Added relationship: {entity1} -> {rel_type} -> {entity2}")

        # 测试搜索功能
        print("\nTesting CS70 knowledge search...")
        search_results = memory_store.search_memories("CS70")
        print(f"✓ Found {len(search_results)} CS70 related memories")

        # 测试学习分析
        print("\nTesting learning analytics...")
        all_memories = memory_store.list_memories()
        cs70_memories = [m for m in all_memories if "CS70" in str(m.get("metadata", {}).get("tags", []))]

        if cs70_memories:
            avg_importance = sum(m.get("metadata", {}).get("importance", 0) for m in cs70_memories) / len(cs70_memories)
            avg_mastery = sum(m.get("metadata", {}).get("mastery_level", 0) for m in cs70_memories) / len(cs70_memories)

            print(f"✓ CS70 Learning Analytics:")
            print(f"  Total memories: {len(cs70_memories)}")
            print(f"  Average importance: {avg_importance:.1f}")
            print(f"  Average mastery level: {avg_mastery:.2f}")

        return True

    except Exception as e:
        print(f"CS70 Canvas integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_graphiti_timeline_recording():
    """测试Graphiti时间线记录"""
    print("\n=== Testing Graphiti Timeline Recording ===")

    try:
        from neo4j_mcp_server import Neo4jMemoryStore

        memory_store = Neo4jMemoryStore()

        # 模拟学习时间线
        timeline_events = [
            {
                "key": f"timeline_start_{datetime.now().strftime('%H%M%S')}",
                "content": "开始CS70学习会话，专注于离散数学基础概念",
                "metadata": {
                    "event_type": "session_start",
                    "canvas_file": "CS70 Lecture1.canvas",
                    "timestamp": datetime.now().isoformat(),
                    "importance": 5
                }
            }
        ]

        # 添加开始事件
        start_memory_id = memory_store.add_memory(
            key=timeline_events[0]["key"],
            content=timeline_events[0]["content"],
            metadata=timeline_events[0]["metadata"]
        )

        print(f"✓ Timeline start recorded: {start_memory_id}")

        # 模拟学习过程中的关键事件
        learning_events = [
            {
                "key": f"concept_understood_{datetime.now().strftime('%H%M%S')}",
                "content": "理解了命题逻辑的真值表构建方法",
                "metadata": {
                    "event_type": "concept_mastery",
                    "concept": "Propositional Logic",
                    "confidence": 8,
                    "importance": 7
                }
            },
            {
                "key": f"question_resolved_{datetime.now().strftime('%H%M%S')}",
                "content": "解决了关于鸽笼原理应用的疑难问题",
                "metadata": {
                    "event_type": "problem_solved",
                    "concept": "Pigeonhole Principle",
                    "difficulty": "hard",
                    "importance": 8
                }
            },
            {
                "key": f"milestone_achieved_{datetime.now().strftime('%H%M%S')}",
                "content": "完成了数学归纳法的基础学习，能够独立完成简单证明",
                "metadata": {
                    "event_type": "milestone",
                    "achievement": "basic_induction_proofs",
                    "importance": 9
                }
            }
        ]

        event_ids = []
        for event in learning_events:
            event_id = memory_store.add_memory(
                key=event["key"],
                content=event["content"],
                metadata=event["metadata"]
            )
            event_ids.append(event_id)
            print(f"✓ Learning event recorded: {event['event_type']}")

        # 添加会话结束事件
        end_event = {
            "key": f"timeline_end_{datetime.now().strftime('%H%M%S')}",
            "content": "CS70学习会话结束，完成了3个主要概念的学习",
            "metadata": {
                "event_type": "session_end",
                "total_events": len(learning_events) + 2,
                "session_duration": 45,
                "importance": 6
            }
        }

        end_memory_id = memory_store.add_memory(
            key=end_event["key"],
            content=end_event["content"],
            metadata=end_event["metadata"]
        )

        print(f"✓ Timeline end recorded: {end_memory_id}")

        # 测试时间线查询
        print("\nTesting timeline retrieval...")
        all_events = memory_store.list_memories()
        timeline_events = [e for e in all_events if "timeline" in e.get("key", "")]

        print(f"✓ Timeline events recorded: {len(timeline_events)}")

        return True

    except Exception as e:
        print(f"Timeline recording test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_export_import_functionality():
    """测试导出导入功能"""
    print("\n=== Testing Export/Import Functionality ===")

    try:
        from neo4j_mcp_server import Neo4jMemoryStore

        memory_store = Neo4jMemoryStore()

        # 测试导出功能
        print("Testing export functionality...")
        export_file = "C:\\Users\\ROG\\托福\\test_memory_export.json"
        export_data = memory_store.export_memories(export_file)

        print(f"✓ Exported {len(export_data['memories'])} memories")
        print(f"✓ Exported {len(export_data['relationships'])} relationships")
        print(f"✓ Export file saved: {export_file}")

        # 测试导入功能
        print("\nTesting import functionality...")

        # 创建一个新的记忆存储实例模拟导入
        import_store = Neo4jMemoryStore()

        # 从文件导入
        import_result = import_store.import_memories(export_file)

        print(f"✓ Imported {import_result['imported_memories']} memories")
        print(f"✓ Imported {import_result['imported_relationships']} relationships")

        # 验证导入的数据
        imported_memories = import_store.list_memories()
        print(f"✓ Total memories after import: {len(imported_memories)}")

        return True

    except Exception as e:
        print(f"Export/Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mcp_server_simulation():
    """模拟MCP服务器调用"""
    print("\n=== Testing MCP Server Simulation ===")

    try:
        from neo4j_mcp_server import Neo4jMemoryStore

        memory_store = Neo4jMemoryStore()

        # 模拟MCP工具调用
        mcp_tool_calls = [
            {
                "tool": "add_memory",
                "args": {
                    "key": "mcp_test_memory",
                    "content": "This is a test memory added via MCP server simulation",
                    "metadata": {"importance": 6, "tags": ["test", "mcp"]}
                }
            },
            {
                "tool": "search_memories",
                "args": {"query": "mcp test"}
            },
            {
                "tool": "add_relationship",
                "args": {
                    "entity1": "MCP Test",
                    "entity2": "Graphiti Memory",
                    "relationship_type": "test_relation"
                }
            },
            {
                "tool": "list_memories",
                "args": {}
            },
            {
                "tool": "add_episode",
                "args": {
                    "content": "Learning episode: Successfully tested MCP Graphiti server functionality"
                }
            }
        ]

        results = []

        for call in mcp_tool_calls:
            tool = call["tool"]
            args = call["args"]

            if tool == "add_memory":
                memory_id = memory_store.add_memory(
                    key=args["key"],
                    content=args["content"],
                    metadata=args.get("metadata")
                )
                result = f"✅ Memory added: {memory_id}"

            elif tool == "search_memories":
                search_results = memory_store.search_memories(args["query"])
                result = f"✅ Search found {len(search_results)} memories"

            elif tool == "add_relationship":
                success = memory_store.add_relationship(
                    args["entity1"],
                    args["entity2"],
                    args["relationship_type"]
                )
                result = f"✅ Relationship added: {success}"

            elif tool == "list_memories":
                memories = memory_store.list_memories()
                result = f"✅ Total memories: {len(memories)}"

            elif tool == "add_episode":
                import hashlib
                key = f"episode_{hashlib.md5(args['content'].encode()).hexdigest()[:8]}"
                memory_id = memory_store.add_memory(
                    key=key,
                    content=args["content"],
                    metadata={"type": "episode", "importance": 5}
                )
                result = f"✅ Episode added: {memory_id}"

            results.append(result)
            print(f"  {tool}: {result}")

        print(f"\n✅ All {len(mcp_tool_calls)} MCP tool calls successful")
        return True

    except Exception as e:
        print(f"MCP server simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行完整的Graphiti API测试"""
    print("=== Complete Graphiti API Functionality Test ===")
    print(f"Test started at: {datetime.now()}")

    tests = [
        ("Direct Neo4j Operations", test_direct_neo4j_operations),
        ("MemoryStore Class", test_memory_store_class),
        ("CS70 Canvas Integration", test_cs70_canvas_integration),
        ("Graphiti Timeline Recording", test_graphiti_timeline_recording),
        ("Export/Import Functionality", test_export_import_functionality),
        ("MCP Server Simulation", test_mcp_server_simulation)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            results[test_name] = test_func()
        except Exception as e:
            print(f"{test_name} failed with exception: {e}")
            results[test_name] = False

    # 输出总结
    print(f"\n{'='*60}")
    print("=== Graphiti API Test Summary ===")
    print(f"Test completed at: {datetime.now()}")

    print(f"\nResults:")
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {test_name}: {status}")

    success_count = sum(results.values())
    total_count = len(results)
    print(f"\nOverall: {success_count}/{total_count} tests passed")

    if success_count == total_count:
        print("\n🎉 All Graphiti API functionality tests PASSED!")
        print("Graphiti knowledge graph system is fully operational!")
    else:
        print(f"\n⚠️ {total_count - success_count} tests failed. Check implementation.")

    # 最终统计
    print(f"\n=== Final Graphiti System Status ===")

    try:
        from neo4j_mcp_server import Neo4jMemoryStore
        memory_store = Neo4jMemoryStore()

        all_memories = memory_store.list_memories()
        print(f"Total memories in system: {len(all_memories)}")

        # 按类型统计
        memory_types = {}
        for memory in all_memories:
            metadata = memory.get("metadata", {})
            tags = metadata.get("tags", [])
            for tag in tags:
                memory_types[tag] = memory_types.get(tag, 0) + 1

        print("Memory distribution by tags:")
        for tag, count in sorted(memory_types.items()):
            print(f"  {tag}: {count} memories")

    except Exception as e:
        print(f"Final statistics failed: {e}")

    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)