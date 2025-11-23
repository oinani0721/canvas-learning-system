#!/usr/bin/env python3
"""
简化的测试运行器

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-28
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def run_async_tests():
    """运行异步测试"""
    print("开始运行异步测试...")

    # 导入测试模块
    from test_memory_recorder import (
        TestDataEncryption,
        TestSystemHealthChecker,
        TestFileLogger,
        TestLocalMemoryDB,
        TestMemoryRecorder,
        TestIntegration,
        TestStress
    )

    total_tests = 0
    passed_tests = 0

    # 测试数据加密
    print("\n测试数据加密...")
    encryption_test = TestDataEncryption()
    try:
        await encryption_test.test_encrypt_decrypt_data()
        await encryption_test.test_encrypt_without_cipher()
        await encryption_test.test_key_generation_and_persistence()
        print("✓ 数据加密测试通过 (3/3)")
        passed_tests += 3
    except Exception as e:
        print(f"✗ 数据加密测试失败: {e}")
    total_tests += 3

    # 测试系统健康检查
    print("\n测试系统健康检查...")
    health_test = TestSystemHealthChecker()
    try:
        await health_test.test_initial_health_status()
        await health_test.test_failure_counting()
        print("✓ 系统健康检查测试通过 (2/2)")
        passed_tests += 2
    except Exception as e:
        print(f"✗ 系统健康检查测试失败: {e}")
    total_tests += 2

    # 测试文件日志
    print("\n测试文件日志...")
    file_test = TestFileLogger()
    try:
        await file_test.test_log_record()
        await file_test.test_get_logs()
        await file_test.test_log_rotation()
        print("✓ 文件日志测试通过 (3/3)")
        passed_tests += 3
    except Exception as e:
        print(f"✗ 文件日志测试失败: {e}")
    total_tests += 3

    # 测试本地数据库
    print("\n测试本地数据库...")
    db_test = TestLocalMemoryDB()
    try:
        await db_test.test_database_initialization()
        await db_test.test_record_and_retrieve()
        await db_test.test_database_backup()
        print("✓ 本地数据库测试通过 (3/3)")
        passed_tests += 3
    except Exception as e:
        print(f"✗ 本地数据库测试失败: {e}")
    total_tests += 3

    # 测试记忆记录器
    print("\n测试记忆记录器...")
    recorder_test = TestMemoryRecorder()
    try:
        await recorder_test.test_recorder_initialization()
        await recorder_test.test_record_session_success()
        await recorder_test.test_record_session_with_primary_failure()
        await recorder_test.test_verify_records()
        await recorder_test.test_recover_records()
        await recorder_test.test_get_system_health()
        await recorder_test.test_get_statistics()
        print("✓ 记忆记录器测试通过 (7/7)")
        passed_tests += 7
    except Exception as e:
        print(f"✗ 记忆记录器测试失败: {e}")
    total_tests += 7

    # 测试集成功能
    print("\n测试集成功能...")
    integration_test = TestIntegration()
    try:
        await integration_test.test_create_memory_recorder_function()
        await integration_test.test_quick_record_session_function()
        await integration_test.test_concurrent_recording()
        print("✓ 集成功能测试通过 (3/3)")
        passed_tests += 3
    except Exception as e:
        print(f"✗ 集成功能测试失败: {e}")
    total_tests += 3

    # 测试压力测试
    print("\n测试压力测试...")
    stress_test = TestStress()
    try:
        await stress_test.test_large_volume_recording()
        await stress_test.test_long_running_session()
        print("✓ 压力测试通过 (2/2)")
        passed_tests += 2
    except Exception as e:
        print(f"✗ 压力测试失败: {e}")
    total_tests += 2

    # 打印结果
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {total_tests - passed_tests}")
    print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 所有异步测试通过！")
        return True
    else:
        print(f"\n❌ {total_tests - passed_tests} 个测试失败")
        return False


def run_sync_tests():
    """运行同步测试（学习会话管理器）"""
    print("\n开始运行学习会话管理器测试...")

    import unittest

    # 导入测试模块
    from test_learning_session_manager import (
        TestLearningSession,
        TestLearningSessionManager,
        TestIntegrationWithMemoryRecorder,
        TestConvenienceFunctions
    )

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestLearningSession))
    suite.addTests(loader.loadTestsFromTestCase(TestLearningSessionManager))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationWithMemoryRecorder))
    suite.addTests(loader.loadTestsFromTestCase(TestConvenienceFunctions))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\n学习会话管理器测试结果:")
    print(f"运行: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    return result.wasSuccessful()


async def main():
    """主函数"""
    print("="*60)
    print("Canvas学习系统 - 三级记忆记录系统测试")
    print("="*60)

    # 运行异步测试
    async_success = await run_async_tests()

    # 运行同步测试
    sync_success = run_sync_tests()

    # 总体结果
    print("\n" + "="*60)
    print("总体测试结果")
    print("="*60)

    if async_success and sync_success:
        print("✅ 所有测试通过！")
        print("\n三级记忆记录系统已准备就绪，可以投入使用。")
        return True
    else:
        print("❌ 部分测试失败，请检查上述错误信息。")
        return False


if __name__ == '__main__':
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试运行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)