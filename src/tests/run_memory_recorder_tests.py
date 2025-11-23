#!/usr/bin/env python3
"""
运行三级记忆记录系统测试

执行所有与记忆记录相关的测试套件，包括：
- test_memory_recorder.py
- test_learning_session_manager.py

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-28
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from test_memory_recorder import TestRunner
# from test_learning_session_manager import LearningSessionTestRunner


async def run_all_memory_tests():
    """运行所有记忆记录相关测试"""
    print("="*80)
    print("🚀 Canvas学习系统 - 三级记忆记录系统测试套件")
    print("="*80)
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    total_tests = 0
    total_passed = 0
    total_failed = 0
    failed_modules = []

    # 1. 运行记忆记录器测试
    print("\n" + "="*60)
    print("📦 测试模块 1/2: MemoryRecorder (test_memory_recorder.py)")
    print("="*60)
    try:
        start_time = time.time()
        memory_test_passed = await TestRunner.run_all_tests()
        duration = time.time() - start_time

        if memory_test_passed:
            print(f"✅ MemoryRecorder 测试通过 ({duration:.1f}秒)")
        else:
            print(f"❌ MemoryRecorder 部分测试失败 ({duration:.1f}秒)")
            failed_modules.append("MemoryRecorder")
    except Exception as e:
        print(f"❌ MemoryRecorder 测试执行失败: {e}")
        failed_modules.append("MemoryRecorder")

    # 2. 运行学习会话管理器测试
    print("\n" + "="*60)
    print("📦 测试模块 2/2: LearningSessionManager (test_learning_session_manager.py)")
    print("="*60)
    try:
        import unittest

        # 创建测试套件
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        # 添加测试类
        from test_learning_session_manager import (
            TestLearningSession,
            TestLearningSessionManager,
            TestIntegrationWithMemoryRecorder,
            TestConvenienceFunctions
        )

        test_classes = [
            TestLearningSession,
            TestLearningSessionManager,
            TestIntegrationWithMemoryRecorder,
            TestConvenienceFunctions
        ]

        for test_class in test_classes:
            suite.addTests(loader.loadTestsFromTestCase(test_class))

        # 运行测试
        start_time = time.time()
        runner = unittest.TextTestRunner(verbosity=1, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        duration = time.time() - start_time

        total_tests += result.testsRun
        total_passed += result.testsRun - len(result.failures) - len(result.errors)
        total_failed += len(result.failures) + len(result.errors)

        if result.wasSuccessful():
            print(f"LearningSessionManager 测试通过 ({duration:.1f}秒) - {result.testsRun}个测试")
        else:
            print(f"LearningSessionManager 部分测试失败 ({duration:.1f}秒)")
            print(f"   失败: {len(result.failures)} | 错误: {len(result.errors)}")
            failed_modules.append("LearningSessionManager")

    except Exception as e:
        print(f"LearningSessionManager 测试执行失败: {e}")
        failed_modules.append("LearningSessionManager")

    # 打印总结
    print("\n" + "="*80)
    print("📊 测试总结报告")
    print("="*80)

    if not failed_modules:
        print("🎉 所有测试模块通过！")
        print("✅ 三级记忆记录系统已准备就绪")
    else:
        print(f"❌ 失败的测试模块: {', '.join(failed_modules)}")
        print("⚠️  请检查上述错误并修复后重新运行")

    print(f"\n📈 测试统计:")
    print(f"   总测试数: {total_tests}")
    print(f"   通过: {total_passed}")
    print(f"   失败: {total_failed}")
    if total_tests > 0:
        print(f"   成功率: {(total_passed/total_tests)*100:.1f}%")

    print(f"\n⏰ 完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    return len(failed_modules) == 0


def check_dependencies():
    """检查测试依赖"""
    print("🔍 检查测试依赖...")

    missing_deps = []

    # 检查必需的包
    required_packages = [
        'asyncio',
        'json',
        'datetime',
        'pathlib',
        'tempfile',
        'unittest',
        'uuid',
        'dataclasses',
        'typing',
        'logging',
        'os',
        'shutil'
    ]

    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - 缺失")
            missing_deps.append(package)

    # 检查可选的第三方包
    optional_packages = [
        ('aiosqlite', 'SQLite异步操作'),
        ('aiofiles', '文件异步操作'),
        ('cryptography', '数据加密'),
        ('pytest', '测试框架（可选）')
    ]

    print("\n📦 检查可选依赖:")
    for package, description in optional_packages:
        try:
            __import__(package)
            print(f"  ✅ {package} - {description}")
        except ImportError:
            print(f"  ⚠️  {package} - {description}（建议安装）")

    if missing_deps:
        print(f"\n❌ 缺失必需依赖: {', '.join(missing_deps)}")
        print("请检查Python环境")
        return False

    print("\n✅ 依赖检查通过")
    return True


async def main():
    """主函数"""
    print("Canvas学习系统 - 三级记忆记录系统测试工具")
    print("="*80)

    # 检查依赖
    if not check_dependencies():
        return False

    print("\n" + "-"*80)

    # 运行测试
    success = await run_all_memory_tests()

    print("\n" + "="*80)

    if success:
        print("🎊 测试完成！系统可以正常使用。")
        print("\n📚 使用文档:")
        print("   - 核心模块: canvas_utils/memory_recorder.py")
        print("   - 会话管理: canvas_utils/learning_session_manager.py")
        print("   - 集成命令: /learning, /intelligent-parallel")
    else:
        print("⚠️  测试未完全通过，请检查并修复问题。")

    return success


if __name__ == '__main__':
    # 运行测试
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 测试运行器崩溃: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)