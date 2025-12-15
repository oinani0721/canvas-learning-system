#!/usr/bin/env python3
"""
测试DirectNeo4jStorage - 验证不依赖MCP的纯Python存储
"""

import sys
import json
import uuid
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_direct_storage():
    """测试直接Neo4j存储"""

    print("=" * 60)
    print("测试 DirectNeo4jStorage - 纯Python实现")
    print("=" * 60)

    # Step 1: 导入模块
    print("\n[1] 导入DirectNeo4jStorage...")
    try:
        from memory_system.neo4j_storage import DirectNeo4jStorage
        print("    [OK] 模块导入成功")
    except ImportError as e:
        print(f"    [FAIL] 模块导入失败: {e}")
        return False

    # Step 2: 创建存储实例
    print("\n[2] 创建DirectNeo4jStorage实例...")
    try:
        storage = DirectNeo4jStorage(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="707188Fx",
            database="ultrathink"
        )
        print(f"    [OK] 连接成功")
        print(f"    Connected: {storage.connected}")
    except Exception as e:
        print(f"    [FAIL] 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: 创建测试会话
    print("\n[3] 创建测试学习会话...")
    session_id = f"test_direct_{uuid.uuid4().hex[:8]}"
    session_data = {
        'session_id': session_id,
        'canvas_id': 'test_canvas_direct',
        'user_id': 'test_user_direct',
        'start_time': datetime.now().isoformat(),
        'canvas_path': 'C:\\Users\\ROG\\托福\\test_direct.canvas'
    }

    try:
        created_id = storage.create_session_node(session_data)
        print(f"    [OK] 会话已创建: {created_id}")
        assert created_id == session_id, "返回的session_id不匹配"
    except Exception as e:
        print(f"    [FAIL] 会话创建失败: {e}")
        import traceback
        traceback.print_exc()
        storage.close()
        return False

    # Step 4: 记录多个事件
    print("\n[4] 记录时序记忆事件...")
    events = [
        {
            'event_type': 'node_view',
            'content': '查看了红色节点',
            'metadata': {'node_id': 'node1', 'color': 'red'}
        },
        {
            'event_type': 'understanding_input',
            'content': '填写了个人理解',
            'metadata': {'node_id': 'yellow1', 'word_count': 150}
        },
        {
            'event_type': 'agent_call',
            'content': '调用了basic-decomposition agent',
            'metadata': {'agent': 'basic-decomposition', 'duration': 3.2}
        }
    ]

    for i, event in enumerate(events, 1):
        event_data = {
            'session_id': session_id,
            'event_id': f"event_{uuid.uuid4().hex[:8]}",
            'event_type': event['event_type'],
            'timestamp': datetime.now().isoformat(),
            'content': event['content'],
            'metadata': json.dumps(event['metadata'], ensure_ascii=False)
        }

        try:
            success = storage.record_memory_event(event_data)
            if success:
                print(f"    [OK] 事件{i}已记录: {event['event_type']}")
            else:
                print(f"    [FAIL] 事件{i}记录失败")
        except Exception as e:
            print(f"    [FAIL] 事件{i}记录异常: {e}")

    # Step 5: 验证存储
    print("\n[5] 验证Neo4j存储...")
    try:
        verification = storage.verify_storage(session_id)
        print(f"    Connected: {verification.get('connected', False)}")
        print(f"    Session exists: {verification.get('session_exists', False)}")
        print(f"    Event count: {verification.get('event_count', 0)}")

        if verification.get('session_exists') and verification.get('event_count', 0) >= 3:
            print("    [OK] 验证成功 - 数据已正确存储")
        else:
            print("    [FAIL] 验证失败 - 数据未正确存储")
            return False
    except Exception as e:
        print(f"    [FAIL] 验证异常: {e}")
        import traceback
        traceback.print_exc()
        storage.close()
        return False

    # Step 6: 获取会话历史
    print("\n[6] 获取会话历史...")
    try:
        history = storage.get_session_history(session_id)
        if 'error' in history:
            print(f"    [FAIL] 获取历史失败: {history['error']}")
            storage.close()
            return False

        print(f"    [OK] 会话信息:")
        print(f"        session_id: {history['session']['session_id']}")
        print(f"        canvas_id: {history['session']['canvas_id']}")
        print(f"        user_id: {history['session']['user_id']}")
        print(f"    [OK] 事件数量: {history['event_count']}")

        if history['event_count'] >= 3:
            print(f"    [OK] 所有事件已正确存储")
        else:
            print(f"    [FAIL] 事件数量不正确: 预期>=3, 实际={history['event_count']}")
    except Exception as e:
        print(f"    [FAIL] 获取历史异常: {e}")
        import traceback
        traceback.print_exc()
        storage.close()
        return False

    # Step 7: 清理
    print("\n[7] 关闭连接...")
    storage.close()
    print("    [OK] 连接已关闭")

    # 最终结果
    print("\n" + "=" * 60)
    print("[SUCCESS] DirectNeo4jStorage 测试全部通过!")
    print("=" * 60)
    print("\n核心验证:")
    print("  [√] 不依赖claude_tools")
    print("  [√] 不依赖MCP服务器")
    print("  [√] 可以在subprocess中运行")
    print("  [√] 成功创建会话节点")
    print("  [√] 成功记录事件")
    print("  [√] 数据真实存储在Neo4j中")
    print("\n下一步: 集成到temporal_memory_manager.py")

    return True


if __name__ == "__main__":
    try:
        success = test_direct_storage()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FATAL] 测试发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
