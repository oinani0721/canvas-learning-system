#!/usr/bin/env python3
"""
测试学习会话真实启动过程
验证Graphiti、Temporal、Semantic三个记忆系统是否真实存储数据
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from command_handlers.learning_commands import LearningSessionManager
from loguru import logger

# 配置logger输出到文件和控制台
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="DEBUG"
)
logger.add(
    "test_learning_session_debug.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="DEBUG",
    mode="w"  # 覆盖模式
)


async def test_learning_session():
    """测试学习会话启动"""

    print("="*80)
    print("🧪 学习会话真实启动测试")
    print("="*80)
    print()

    # 1. 创建测试Canvas文件
    test_canvas_path = "test_session_canvas.canvas"
    test_canvas = {
        "nodes": [
            {
                "id": "test_node_1",
                "type": "text",
                "text": "测试概念：逻辑命题",
                "x": 0,
                "y": 0,
                "width": 250,
                "height": 60,
                "color": "1"
            }
        ],
        "edges": []
    }

    with open(test_canvas_path, 'w', encoding='utf-8') as f:
        json.dump(test_canvas, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ 测试Canvas文件已创建: {test_canvas_path}")

    # 2. 创建LearningSessionManager
    manager = LearningSessionManager(session_dir=".learning_sessions")
    logger.info("✅ LearningSessionManager初始化完成")

    # 3. 启动学习会话
    print()
    print("-"*80)
    print("开始启动学习会话...")
    print("-"*80)
    print()

    try:
        result = await manager.start_session(
            canvas_path=test_canvas_path,
            user_id="test_user",
            session_name="测试会话_验证真实存储",
            allow_partial_start=True,
            interactive=False
        )

        print()
        print("="*80)
        print("📊 启动结果")
        print("="*80)
        print()

        logger.info(f"成功状态: {result['success']}")
        logger.info(f"会话ID: {result['session_id']}")
        logger.info(f"会话文件: {result['session_file']}")
        logger.info(f"运行中的系统: {result['running_systems']}/{result['total_systems']}")

        print()
        print("-"*80)
        print("记忆系统详细状态:")
        print("-"*80)

        for system_name, system_data in result['memory_systems'].items():
            print(f"\n🔹 {system_name.upper()}")
            print(f"   状态: {system_data.get('status')}")

            if 'memory_id' in system_data:
                print(f"   Memory ID: {system_data['memory_id']}")
            if 'session_id' in system_data:
                print(f"   Session ID: {system_data['session_id']}")
            if 'error' in system_data:
                print(f"   ❌ 错误: {system_data['error']}")
            if 'suggestion' in system_data:
                print(f"   💡 建议: {system_data['suggestion']}")

            print(f"   存储位置: {system_data.get('storage', 'N/A')}")
            print(f"   初始化时间: {system_data.get('initialized_at', system_data.get('attempted_at', 'N/A'))}")

        # 4. 读取并显示会话JSON文件
        print()
        print("="*80)
        print("📄 会话JSON文件内容")
        print("="*80)

        session_file = Path(result['session_file'])
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                session_json = json.load(f)

            print(json.dumps(session_json, indent=2, ensure_ascii=False))

        # 5. 验证Graphiti存储
        print()
        print("="*80)
        print("🔍 验证Graphiti知识图谱存储")
        print("="*80)
        print()

        if result['memory_systems']['graphiti']['status'] == 'running':
            graphiti_memory_id = result['memory_systems']['graphiti']['memory_id']
            print(f"✅ Graphiti声称已启动")
            print(f"   Memory ID: {graphiti_memory_id}")
            print()
            print("尝试通过MCP工具查询...")

            try:
                # 尝试导入MCP工具
                try:
                    from mcp__graphiti_memory__search_memories import mcp__graphiti_memory__search_memories
                    from mcp__graphiti_memory__list_memories import mcp__graphiti_memory__list_memories

                    # 查询所有记忆
                    all_memories = await mcp__graphiti_memory__list_memories()
                    print(f"📊 Graphiti中的总记忆数: {len(all_memories) if isinstance(all_memories, list) else 0}")

                    # 搜索会话相关记忆
                    search_result = await mcp__graphiti_memory__search_memories(
                        query=result['session_id']
                    )

                    if search_result:
                        print(f"✅ 找到会话记忆:")
                        print(json.dumps(search_result, indent=2, ensure_ascii=False))
                    else:
                        print(f"❌ 未找到会话记忆（搜索: {result['session_id']}）")

                except ImportError as e:
                    print(f"⚠️ 无法导入MCP工具: {e}")
                    print(f"   MCP工具可能需要在Claude Code环境中运行")

            except Exception as e:
                print(f"❌ 验证Graphiti存储时出错: {e}")
        else:
            print(f"❌ Graphiti未成功启动")
            print(f"   状态: {result['memory_systems']['graphiti']['status']}")
            print(f"   错误: {result['memory_systems']['graphiti'].get('error', 'N/A')}")

        # 6. 验证时序记忆存储
        print()
        print("="*80)
        print("🔍 验证时序记忆数据库存储")
        print("="*80)
        print()

        import sqlite3
        memory_db = Path("data/memory_local.db")

        if memory_db.exists():
            conn = sqlite3.connect(str(memory_db))
            cursor = conn.cursor()

            # 查询记录
            cursor.execute("SELECT COUNT(*) FROM memory_records WHERE session_id LIKE ?",
                          (f"%{result['session_id']}%",))
            count = cursor.fetchone()[0]

            print(f"📊 memory_local.db中与会话相关的记录数: {count}")

            if count > 0:
                cursor.execute("""
                    SELECT id, session_id, timestamp, canvas_path
                    FROM memory_records
                    WHERE session_id LIKE ?
                    LIMIT 3
                """, (f"%{result['session_id']}%",))

                records = cursor.fetchall()
                print("✅ 找到记录:")
                for record in records:
                    print(f"   ID: {record[0]}, Session: {record[1]}, Time: {record[2]}")
            else:
                print("❌ 未找到时序记忆记录")

            conn.close()
        else:
            print(f"❌ 数据库文件不存在: {memory_db}")

        # 7. 验证语义记忆存储
        print()
        print("="*80)
        print("🔍 验证语义记忆存储")
        print("="*80)
        print()

        semantic_db = Path(".semantic_cache.db")

        if semantic_db.exists():
            conn = sqlite3.connect(str(semantic_db))
            cursor = conn.cursor()

            # 查询记录
            cursor.execute("""
                SELECT COUNT(*) FROM semantic_memories
                WHERE content LIKE ? OR metadata LIKE ?
            """, (f"%{result['session_id']}%", f"%{result['session_id']}%"))
            count = cursor.fetchone()[0]

            print(f"📊 semantic_cache.db中与会话相关的记录数: {count}")

            if count > 0:
                cursor.execute("""
                    SELECT id, created_at, content, metadata
                    FROM semantic_memories
                    WHERE content LIKE ? OR metadata LIKE ?
                    LIMIT 3
                """, (f"%{result['session_id']}%", f"%{result['session_id']}%"))

                records = cursor.fetchall()
                print("✅ 找到记录:")
                for record in records:
                    print(f"   ID: {record[0]}")
                    print(f"   Time: {record[1]}")
                    print(f"   Content: {record[2][:100]}...")
                    print(f"   Metadata: {record[3][:100]}...")
                    print()
            else:
                print("❌ 未找到语义记忆记录")

            conn.close()
        else:
            print(f"❌ 数据库文件不存在: {semantic_db}")

        print()
        print("="*80)
        print("✅ 测试完成")
        print("="*80)

        return result

    except Exception as e:
        logger.exception(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print()
    print("🚀 开始运行学习会话真实启动测试...")
    print()

    result = asyncio.run(test_learning_session())

    if result:
        print()
        print("✅ 测试脚本执行成功")
        print(f"📝 详细日志已保存到: test_learning_session_debug.log")
    else:
        print()
        print("❌ 测试脚本执行失败")
        sys.exit(1)
