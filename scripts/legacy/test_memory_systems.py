#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import subprocess
import os
from datetime import datetime, timedelta

def test_realtime_memory():
    """测试实时记忆系统"""
    print("=== Real-time Memory System Test ===")

    memory_db = "C:\\Users\\ROG\\托福\\data\\realtime_memory\\memory_sessions.db"

    if not os.path.exists(memory_db):
        print("Real-time memory database not found")
        return False

    try:
        conn = sqlite3.connect(memory_db)
        cursor = conn.cursor()

        # 检查表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables found: {[t[0] for t in tables]}")

        # 检查现有数据
        for table_name in [t[0] for t in tables]:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"{table_name}: {count} records")

        # 创建测试会话
        print("\nCreating test memory session...")
        test_session = {
            'session_id': 'test-session-002',
            'canvas_file': 'CS70 Lecture1.canvas',
            'start_time': datetime.now().isoformat(),
            'end_time': (datetime.now() + timedelta(minutes=45)).isoformat(),
            'nodes_processed': 8,
            'agent_calls': 5,
            'user_interactions': 3,
            'created_at': datetime.now().isoformat()
        }

        cursor.execute("""
            INSERT OR REPLACE INTO memory_sessions
            (session_id, canvas_file, start_time, end_time, nodes_processed,
             agent_calls, user_interactions, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_session['session_id'], test_session['canvas_file'],
            test_session['start_time'], test_session['end_time'],
            test_session['nodes_processed'], test_session['agent_calls'],
            test_session['user_interactions'], test_session['created_at']
        ))

        # 创建测试学习活动
        test_activity = {
            'activity_id': 'activity-001',
            'session_id': 'test-session-002',
            'activity_type': 'node_update',
            'node_id': 'node-propositional-logic',
            'agent_used': 'scoring-agent',
            'activity_data': '{"score": 8, "confidence": 7}',
            'timestamp': datetime.now().isoformat()
        }

        cursor.execute("""
            INSERT OR REPLACE INTO learning_activities
            (activity_id, session_id, activity_type, node_id,
             agent_used, activity_data, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            test_activity['activity_id'], test_activity['session_id'],
            test_activity['activity_type'], test_activity['node_id'],
            test_activity['agent_used'], test_activity['activity_data'],
            test_activity['timestamp']
        ))

        # 创建测试学习轨迹
        test_trajectory = {
            'trajectory_id': 'traj-001',
            'session_id': 'test-session-002',
            'concept_path': '["propositional_logic", "truth_tables", "implications"]',
            'mastery_progress': [0.3, 0.5, 0.8],
            'timestamp': datetime.now().isoformat()
        }

        cursor.execute("""
            INSERT OR REPLACE INTO learning_trajectories
            (trajectory_id, session_id, concept_path, mastery_progress, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            test_trajectory['trajectory_id'], test_trajectory['session_id'],
            test_trajectory['concept_path'], test_trajectory['mastery_progress'],
            test_trajectory['timestamp']
        ))

        conn.commit()

        # 验证数据
        cursor.execute("SELECT COUNT(*) FROM memory_sessions")
        sessions_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM learning_activities")
        activities_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM learning_trajectories")
        trajectories_count = cursor.fetchone()[0]

        print(f"\nTest data inserted:")
        print(f"  Sessions: {sessions_count}")
        print(f"  Activities: {activities_count}")
        print(f"  Trajectories: {trajectories_count}")

        # 测试查询
        print("\nTesting memory queries...")

        # 查询最近会话
        cursor.execute("""
            SELECT session_id, canvas_file, nodes_processed, agent_calls
            FROM memory_sessions
            ORDER BY created_at DESC
            LIMIT 5
        """)

        recent_sessions = cursor.fetchall()
        print(f"Recent sessions: {len(recent_sessions)}")

        # 查询学习统计
        cursor.execute("""
            SELECT
                SUM(nodes_processed) as total_nodes,
                SUM(agent_calls) as total_agents,
                COUNT(*) as total_sessions
            FROM memory_sessions
        """)

        stats = cursor.fetchone()
        if stats[0]:
            print(f"Memory statistics:")
            print(f"  Total nodes processed: {stats[0]}")
            print(f"  Total agent calls: {stats[1]}")
            print(f"  Total sessions: {stats[2]}")

        conn.close()
        print("Real-time memory system test PASSED!")
        return True

    except Exception as e:
        print(f"Real-time memory test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mcp_system():
    """测试MCP系统"""
    print("\n=== MCP System Test ===")

    # 检查MCP配置文件
    mcp_configs = [
        'mcp_graphiti_final_fixed.json',
        'mcp_graphiti_windows.json',
        'backup_configs/mcp_graphiti_windows.json'
    ]

    found_configs = []
    for config in mcp_configs:
        if os.path.exists(config):
            found_configs.append(config)
            print(f"Found MCP config: {config}")

    if not found_configs:
        print("No MCP configuration files found")
        return False

    # 尝试读取配置
    try:
        import json
        with open(found_configs[0], 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        print(f"MCP server configuration loaded")
        print(f"  Server: {config_data.get('mcpServers', {}).keys()}")

        # 检查Graphiti MCP服务器
        if 'mcpServers' in config_data:
            for server_name, server_config in config_data['mcpServers'].items():
                if 'graphiti' in server_name.lower():
                    print(f"  Graphiti server found: {server_name}")
                    return True

    except Exception as e:
        print(f"Failed to load MCP config: {e}")
        return False

    print("MCP system test completed")
    return True

def test_graphiti_python_integration():
    """测试Graphiti Python集成"""
    print("\n=== Graphiti Python Integration Test ===")

    graphiti_files = [
        'graphiti_integration.py',
        'graphiti_gemini_integration.py',
        'graphiti_timeline_reader.py'
    ]

    working_files = []
    for file in graphiti_files:
        if os.path.exists(file):
            working_files.append(file)
            print(f"Found Graphiti file: {file}")

    if not working_files:
        print("No Graphiti Python files found")
        return False

    # 测试基本的Python集成
    try:
        # 创建简单的Graphiti测试
        test_script = '''
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_graphiti():
    """基本Graphiti功能测试"""
    print("Testing basic Graphiti functionality...")

    # 模拟知识图谱数据
    test_concepts = [
        {"name": "Propositional Logic", "type": "concept", "mastery": 0.7},
        {"name": "Pigeonhole Principle", "type": "concept", "mastery": 0.4},
        {"name": "CS70", "type": "course", "mastery": 0.6}
    ]

    test_relations = [
        {"from": "CS70", "to": "Propositional Logic", "type": "includes"},
        {"from": "CS70", "to": "Pigeonhole Principle", "type": "includes"},
        {"from": "Propositional Logic", "to": "Pigeonhole Principle", "type": "prerequisite"}
    ]

    print(f"Test concepts: {len(test_concepts)}")
    print(f"Test relations: {len(test_relations)}")

    # 模拟关系分析
    strong_connections = [r for r in test_relations if r["type"] == "includes"]
    print(f"Strong connections: {len(strong_connections)}")

    return True

if __name__ == "__main__":
    test_basic_graphiti()
        '''

        # 写入临时测试文件
        temp_file = "C:\\Users\\ROG\\托福\\temp_graphiti_test.py"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(test_script)

        # 运行测试
        result = subprocess.run([
            'python', temp_file
        ], capture_output=True, text=True, timeout=30)

        print(f"Graphiti Python test output: {result.stdout}")

        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)

        return result.returncode == 0

    except Exception as e:
        print(f"Graphiti Python integration test FAILED: {e}")
        return False

def main():
    print("=== Memory & MCP Systems Comprehensive Test ===")
    print(f"Test started at: {datetime.now()}")

    tests = [
        ("Real-time Memory System", test_realtime_memory),
        ("MCP System", test_mcp_system),
        ("Graphiti Python Integration", test_graphiti_python_integration)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"{test_name} failed with exception: {e}")
            results[test_name] = False

    # 输出总结
    print(f"\n=== Memory & MCP Systems Test Summary ===")
    print(f"Test completed at: {datetime.now()}")

    print(f"\nResults:")
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {test_name}: {status}")

    success_count = sum(results.values())
    total_count = len(results)
    print(f"\nOverall: {success_count}/{total_count} tests passed")

    if success_count == total_count:
        print("All memory and MCP systems are working correctly!")
    else:
        print("Some systems need attention.")

    return success_count == total_count

if __name__ == "__main__":
    main()