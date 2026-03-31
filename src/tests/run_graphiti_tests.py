#!/usr/bin/env python3
"""
Graphiti测试运行器

运行所有Graphiti相关的测试并生成报告。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import sys
import time
import unittest
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_all_tests():
    """运行所有Graphiti测试"""
    print("🚀 开始运行Graphiti知识图谱系统测试")
    print("=" * 60)

    # 测试套件
    test_modules = [
        "test_concept_extractor",
        "test_graphiti_integration",
        "test_graphiti_integration_comprehensive",
    ]

    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0

    start_time = time.time()

    for module_name in test_modules:
        print(f"\n📋 运行测试模块: {module_name}")
        print("-" * 40)

        try:
            # 导入测试模块
            module = __import__(module_name)

            # 创建测试套件
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(module)

            # 运行测试
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)

            # 统计结果
            total_tests += result.testsRun
            total_failures += len(result.failures)
            total_errors += len(result.errors)
            total_skipped += len(result.skipped)

            # 打印结果摘要
            print(f"\n📊 {module_name} 测试结果:")
            print(f"   运行: {result.testsRun}")
            print(f"   失败: {len(result.failures)}")
            print(f"   错误: {len(result.errors)}")
            print(f"   跳过: {len(result.skipped)}")

            if result.failures:
                print("\n❌ 失败的测试:")
                for test, traceback in result.failures:
                    print(
                        f"   - {test}: {traceback.split('AssertionError:')[-1].strip() if 'AssertionError:' in traceback else 'Unknown'}"
                    )

            if result.errors:
                print("\n💥 错误的测试:")
                for test, traceback in result.errors:
                    print(
                        f"   - {test}: {traceback.split('Exception:')[-1].strip() if 'Exception:' in traceback else 'Unknown'}"
                    )

        except Exception as e:
            print(f"❌ 运行测试模块 {module_name} 时出错: {e}")
            total_errors += 1

    end_time = time.time()
    duration = end_time - start_time

    # 总体结果
    print("\n" + "=" * 60)
    print("📈 总体测试结果")
    print("=" * 60)
    print(f"总测试数: {total_tests}")
    print(f"成功: {total_tests - total_failures - total_errors - total_skipped}")
    print(f"失败: {total_failures}")
    print(f"错误: {total_errors}")
    print(f"跳过: {total_skipped}")
    print(f"运行时间: {duration:.2f}秒")

    success_rate = (
        ((total_tests - total_failures - total_errors) / total_tests * 100)
        if total_tests > 0
        else 0
    )
    print(f"成功率: {success_rate:.1f}%")

    if total_failures == 0 and total_errors == 0:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print(f"\n⚠️  有 {total_failures + total_errors} 个测试未通过")
        return False


def run_specific_test(test_name):
    """运行特定的测试"""
    print(f"🔍 运行特定测试: {test_name}")
    print("-" * 40)

    try:
        # 尝试作为模块运行
        if test_name.startswith("test_"):
            module = __import__(test_name)
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(module)
        else:
            # 尝试作为测试类运行
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromName(test_name)

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ 运行测试失败: {e}")
        return False


def generate_test_report():
    """生成测试报告"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "system": "Canvas Learning System - Graphiti Knowledge Graph",
        "version": "1.0",
        "test_categories": [
            {
                "name": "概念提取测试",
                "module": "test_concept_extractor",
                "description": "测试概念提取器的各种功能，包括中文分词、关系识别、置信度计算等",
            },
            {
                "name": "Graphiti集成测试",
                "module": "test_graphiti_integration",
                "description": "测试Graphiti知识图谱管理器的核心功能",
            },
            {
                "name": "综合集成测试",
                "module": "test_graphiti_integration_comprehensive",
                "description": "端到端测试，验证整个系统的集成和性能",
            },
        ],
        "coverage_areas": [
            "概念提取和关系识别",
            "知识图谱存储和检索",
            "命令行接口",
            "可视化生成",
            "数据备份和恢复",
            "性能和可扩展性",
            "错误处理和健壮性",
        ],
    }

    report_path = Path(__file__).parent / "test_report.json"
    import json

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"📄 测试报告已生成: {report_path}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 运行特定测试
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        # 运行所有测试
        success = run_all_tests()
        generate_test_report()

    # 退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
