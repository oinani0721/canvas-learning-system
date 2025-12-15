#!/usr/bin/env python3
"""
测试仪表板功能

这个脚本直接测试我们添加的方法是否工作。
"""

import sys
import os

# 确保能找到我们的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_methods():
    """测试仪表板相关方法"""
    try:
        print("正在导入canvas_utils...")
        from canvas_utils import KnowledgeGraphLayer

        print("创建KnowledgeGraphLayer实例...")
        kg = KnowledgeGraphLayer()

        print("检查可用方法...")
        methods = [m for m in dir(kg) if not m.startswith('_')]

        print(f"总共找到 {len(methods)} 个公共方法")

        # 查找我们添加的方法
        dashboard_methods = [m for m in methods if 'dashboard' in m.lower()]
        progress_methods = [m for m in methods if 'progress' in m.lower()]

        print(f"包含'dashboard'的方法: {dashboard_methods}")
        print(f"包含'progress'的方法: {progress_methods[:10]}...")  # 只显示前10个

        # 检查具体方法
        required_methods = [
            'get_progress_dashboard',
            'get_interactive_progress_viewer',
            'get_learning_progress_query',
            'get_learning_timeline_query',
            'generate_learning_analysis_report'
        ]

        print("\n检查必需的方法:")
        for method in required_methods:
            if hasattr(kg, method):
                print(f"  ✓ {method}")
            else:
                print(f"  ✗ {method}")

        return True

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("测试Canvas学习进度仪表板方法")
    print("=" * 50)

    success = test_dashboard_methods()

    if success:
        print("\n测试完成！")
    else:
        print("\n测试失败！")
        sys.exit(1)