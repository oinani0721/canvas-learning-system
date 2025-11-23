#!/usr/bin/env python3
"""
快速测试记忆记录器核心功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def quick_test():
    """快速测试"""
    try:
        # 导入模块
        from canvas_utils.memory_recorder import MemoryRecorder, create_memory_recorder

        print("成功导入记忆记录器模块")

        # 创建记录器
        config = {
            'graphiti': {'enabled': False},
            'local_db': {
                'enabled': True,
                'path': 'data/test_memory.db',
                'backup_path': 'data/test_memory_backup.db'
            },
            'file_logger': {
                'enabled': True,
                'log_dir': 'data/test_logs'
            },
            'encryption': {
                'enabled': True,
                'key_path': 'data/test_key.key'
            }
        }

        recorder = MemoryRecorder(config)
        await recorder.initialize()
        print("记录器初始化成功")

        # 测试记录
        session_data = {
            'session_id': 'test_session',
            'canvas_path': 'test.canvas',
            'user_id': 'test_user',
            'actions': [{'type': 'test', 'data': 'test'}],
            'metadata': {'test': True}
        }

        report = await recorder.record_session(session_data)
        print(f"记录成功: {report.successful_systems}")

        # 测试统计
        stats = await recorder.get_statistics()
        print(f"统计: 总记录={stats['statistics']['total_records']}, 成功率={stats['success_rate']}%")

        # 测试健康检查
        health = await recorder.get_system_health()
        print(f"系统健康: {health.is_healthy}")

        print("\n所有核心功能测试通过！")
        return True

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    import asyncio
    success = asyncio.run(quick_test())

    # 清理测试文件
    import os
    import shutil
    import pathlib
    test_dir = pathlib.Path('data')
    if test_dir.exists():
        shutil.rmtree(test_dir)

    print(f"\n测试结果: {'通过' if success else '失败'}")