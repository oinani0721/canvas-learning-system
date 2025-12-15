#!/usr/bin/env python3
"""
快速测试性能修复

测试修复后的性能测试框架是否能正常工作
"""

import os
import sys

def test_imports():
    """测试关键导入"""
    try:
        print("🧪 测试基本导入...")
        import json
        import tempfile
        from pathlib import Path
        from typing import Dict, List, Optional, Tuple, Any
        from dataclasses import dataclass, field
        import psutil
        import time
        import uuid
        from datetime import datetime
        import gc
        print("✅ 基本导入成功")

        print("🧪 测试性能测试框架导入...")
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        # 测试关键模块导入
        from tests.test_canvas_performance import (
            CanvasPerformanceTester,
            TestCanvasGenerator,
            PerformanceTestResult,
            StressTestResult,
            MemoryMonitor
        )
        print("✅ 性能测试框架导入成功")

        print("🧪 测试基准管理器导入...")
        from tests.test_performance_baseline import (
            PerformanceBaselineManager,
            PerformanceBaseline,
            RegressionTestResult
        )
        print("✅ 基准管理器导入成功")

        return True

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except SyntaxError as e:
        print(f"❌ 语法错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    try:
        print("\n🧪 测试Canvas生成器...")
        generator = TestCanvasGenerator()

        # 测试生成简单Canvas
        canvas_path = generator.generate_test_canvas(10, "simple")
        print(f"✅ Canvas生成成功: {canvas_path}")

        # 验证文件存在和内容
        if os.path.exists(canvas_path):
            with open(canvas_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'nodes' in data and len(data['nodes']) == 10:
                    print("✅ Canvas内容验证成功")
                else:
                    print("❌ Canvas内容验证失败")
                    return False
        else:
            print("❌ Canvas文件不存在")
            return False

        # 清理
        try:
            os.remove(canvas_path)
        except:
            pass

        return True

    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False

def test_memory_monitor():
    """测试内存监控"""
    try:
        print("\n🧪 测试内存监控器...")
        monitor = MemoryMonitor()
        monitor.start_monitoring()
        current, peak, growth = monitor.get_memory_usage()
        print(f"✅ 内存监控成功 - 当前: {current:.1f}MB, 峰值: {peak:.1f}MB, 增长: {growth:.1f}MB")
        return True

    except Exception as e:
        print(f"❌ 内存监控测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔧 Canvas性能测试框架 - 修复验证")
    print("=" * 50)

    success_count = 0
    total_tests = 3

    # 测试1: 导入
    if test_imports():
        success_count += 1
    else:
        print("\n⚠️ 导入测试失败，无法继续其他测试")
        return False

    # 测试2: 基本功能
    if test_basic_functionality():
        success_count += 1
    else:
        print("\n⚠️ 基本功能测试失败")

    # 测试3: 内存监控
    if test_memory_monitor():
        success_count += 1
    else:
        print("\n⚠️ 内存监控测试失败")

    # 结果汇总
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {success_count}/{total_tests} 通过")

    if success_count == total_tests:
        print("🎉 所有测试通过！性能测试框架修复成功！")
        print("\n📋 下一步操作:")
        print("1. 运行完整的性能测试:")
        print("   python scripts/performance_test_runner.py stress --nodes 50,100,200 --iterations 1")
        print("2. 运行单元测试:")
        print("   python -m pytest tests/test_performance_framework.py -v")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)