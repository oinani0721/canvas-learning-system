"""
Story 10.11 集成测试
验证诚实状态报告和优雅降级功能

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-30
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from command_handlers.learning_commands import (
    LearningSessionManager,
    check_neo4j_connection,
    check_mcp_server_health
)


async def test_system_detection():
    """测试系统可用性检测"""
    print("\n" + "="*60)
    print("测试1: 系统可用性检测")
    print("="*60)

    # 1. Neo4j检测
    print("\n检测Neo4j连接...")
    neo4j_result = check_neo4j_connection(timeout=2)
    print(f"  - available: {neo4j_result['available']}")
    print(f"  - error: {neo4j_result.get('error', 'None')}")
    print(f"  - suggestion: {neo4j_result.get('suggestion', 'None')}")

    # 2. MCP服务器检测
    print("\n检测MCP服务器健康...")
    mcp_result = await check_mcp_server_health(timeout=2)
    print(f"  - available: {mcp_result['available']}")
    print(f"  - error: {mcp_result.get('error', 'None')}")
    print(f"  - services: {mcp_result['services']}")


async def test_graceful_degradation():
    """测试优雅降级"""
    print("\n" + "="*60)
    print("测试2: 优雅降级机制")
    print("="*60)

    manager = LearningSessionManager()

    print("\n启动学习会话（允许部分启动）...")
    result = await manager.start_session(
        canvas_path="src/tests/fixtures/test.canvas",
        allow_partial_start=True,
        interactive=False
    )

    print(f"\n会话启动结果:")
    print(f"  - success: {result['success']}")
    print(f"  - running_systems: {result['running_systems']}/{result['total_systems']}")
    print(f"  - session_id: {result['session_id']}")

    # 显示状态报告
    print(f"\n状态报告:")
    print(result['status_report'])


async def test_status_report():
    """测试状态报告生成"""
    print("\n" + "="*60)
    print("测试3: 状态报告生成")
    print("="*60)

    manager = LearningSessionManager()

    # 模拟不同状态的系统
    memory_systems = {
        'graphiti': {
            'status': 'running',
            'memory_id': 'mem_test_001',
            'storage': 'Neo4j图数据库',
            'initialized_at': '2025-10-30T19:00:00'
        },
        'temporal': {
            'status': 'unavailable',
            'error': 'Neo4j连接失败',
            'suggestion': '启动Neo4j数据库',
            'attempted_at': '2025-10-30T19:00:01'
        },
        'semantic': {
            'status': 'running',
            'memory_id': 'sem_001',
            'storage': '向量数据库',
            'initialized_at': '2025-10-30T19:00:02'
        }
    }

    session_data = {
        'session_id': 'test_session_integration',
        'canvas_path': 'tests/fixtures/test.canvas',
        'start_time': '2025-10-30T19:00:00'
    }

    report = manager.generate_status_report(memory_systems, session_data)
    print("\n生成的状态报告:")
    print(report)


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("Story 10.11 集成测试")
    print("="*60)

    # 测试1: 系统检测
    await test_system_detection()

    # 测试2: 优雅降级
    await test_graceful_degradation()

    # 测试3: 状态报告
    await test_status_report()

    print("\n" + "="*60)
    print("✅ 所有集成测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
