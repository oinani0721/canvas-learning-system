"""
Canvas学习系统G6智能布局简化演示脚本

运行方式:
python simple_demo.py

Author: Canvas Learning System Team
Version: 2.0 (G6集成版)
Created: 2025-10-18
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 确保能够导入我们的模块
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    from g6_canvas_optimizer import G6CanvasLayoutOptimizer, G6LayoutTester
    from g6_layout_preference_learner import G6LayoutPreferenceLearner
    print("模块导入成功")
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保 g6_canvas_optimizer.py 和 g6_layout_preference_learner.py 文件存在")
    sys.exit(1)


def create_demo_canvas():
    """创建演示Canvas文件"""

    print("创建演示Canvas文件...")

    demo_canvas = {
        "nodes": [
            {
                "id": "material-calculus",
                "type": "text",
                "x": 100,
                "y": 100,
                "width": 400,
                "height": 180,
                "text": "微积分 - 导数概念\n\n导数是微积分中的核心概念，描述函数在某一点的瞬时变化率。几何上表示切线斜率，物理上表示瞬时速度。\n\nf'(x) = lim(h→0) [f(x+h) - f(x)] / h"
            },
            {
                "id": "question-1-definition",
                "type": "text",
                "x": 600,
                "y": 80,
                "width": 350,
                "height": 120,
                "color": "4",
                "text": "什么是导数的严格数学定义？\n\n请解释极限概念在导数定义中的作用。"
            },
            {
                "id": "question-2-geometric",
                "type": "text",
                "x": 600,
                "y": 240,
                "width": 350,
                "height": 120,
                "color": "3",
                "text": "导数的几何意义是什么？\n\n如何理解切线斜率与导数的关系？"
            },
            {
                "id": "understanding-1",
                "type": "text",
                "x": 600,
                "y": 230,
                "width": 300,
                "height": 150,
                "color": "6",
                "text": ""
            },
            {
                "id": "understanding-2",
                "type": "text",
                "x": 600,
                "y": 390,
                "width": 300,
                "height": 150,
                "color": "6",
                "text": ""
            },
            {
                "id": "subquestion-1-1",
                "type": "text",
                "x": 1000,
                "y": 150,
                "width": 300,
                "height": 100,
                "color": "4",
                "text": "极限的ε-δ定义是什么？"
            },
            {
                "id": "explanation-oral",
                "type": "text",
                "x": 1400,
                "y": 180,
                "width": 280,
                "height": 80,
                "color": "5",
                "text": "导数的口语化解释"
            }
        ],
        "edges": [
            {"id": "edge-material-q1", "fromNode": "material-calculus", "toNode": "question-1-definition", "label": "拆解自"},
            {"id": "edge-material-q2", "fromNode": "material-calculus", "toNode": "question-2-geometric", "label": "拆解自"},
            {"id": "edge-q1-yellow", "fromNode": "question-1-definition", "toNode": "understanding-1", "label": "个人理解"},
            {"id": "edge-q2-yellow", "fromNode": "question-2-geometric", "toNode": "understanding-2", "label": "个人理解"},
            {"id": "edge-yellow-sub1-1", "fromNode": "understanding-1", "toNode": "subquestion-1-1", "label": "拆解自"},
            {"id": "edge-yellow-oral", "fromNode": "understanding-1", "toNode": "explanation-oral", "label": "补充解释"}
        ]
    }

    # 保存演示文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    demo_file = f"C:/Users/ROG/托福/笔记库/测试/demo-calculus-{timestamp}.canvas"

    os.makedirs(os.path.dirname(demo_file), exist_ok=True)

    with open(demo_file, 'w', encoding='utf-8') as f:
        json.dump(demo_canvas, f, ensure_ascii=False, indent=2)

    print(f"演示Canvas文件已创建: {os.path.basename(demo_file)}")
    return demo_file


def demo_layout_optimization(canvas_file):
    """演示布局优化"""

    print("\n开始布局优化演示...")

    # 创建优化器
    optimizer = G6CanvasLayoutOptimizer()

    # 读取Canvas文件
    with open(canvas_file, 'r', encoding='utf-8') as f:
        canvas_data = json.load(f)

    print(f"原始Canvas信息:")
    print(f"   节点数量: {len(canvas_data['nodes'])}")
    print(f"   边数量: {len(canvas_data['edges'])}")

    # 测试compactbox布局
    layout_type = 'compactbox'
    print(f"\n应用 {layout_type} 布局...")

    try:
        # 应用布局优化
        optimized_canvas = optimizer.optimize_canvas_layout(canvas_data, layout_type)

        # 保存优化结果
        timestamp = datetime.now().strftime("%H%M%S")
        output_file = canvas_file.replace('.canvas', f'-{layout_type}-optimized-{timestamp}.canvas')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(optimized_canvas, f, ensure_ascii=False, indent=2)

        print(f"{layout_type} 布局完成: {os.path.basename(output_file)}")
        return output_file

    except Exception as e:
        print(f"{layout_type} 布局失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def demo_preference_learning(canvas_file, optimized_file):
    """演示偏好学习"""

    print("\n开始偏好学习演示...")

    try:
        # 创建学习器
        learner = G6LayoutPreferenceLearner()

        # 开始学习会话
        session_id = learner.start_new_session(canvas_file, 'compactbox')

        print(f"学习会话开始: {session_id}")

        # 读取原始和优化后的Canvas
        with open(canvas_file, 'r', encoding='utf-8') as f:
            original_canvas = json.load(f)

        with open(optimized_file, 'r', encoding='utf-8') as f:
            optimized_canvas = json.load(f)

        # 模拟用户调整
        print("模拟用户调整...")

        # 创建轻微调整的版本
        adjusted_canvas = json.loads(json.dumps(optimized_canvas))

        # 模拟几个调整
        adjustments_made = []
        for i, node in enumerate(adjusted_canvas['nodes']):
            if node.get('color') == '6':  # 黄色节点
                # 模拟用户微调黄色节点位置
                node['x'] += 5  # 稍微右移
                node['y'] += 3  # 稍微下移
                adjustments_made.append(node['id'])

                if len(adjustments_made) >= 2:  # 只模拟2个调整
                    break

        print(f"模拟调整了 {len(adjustments_made)} 个节点")

        # 记录用户调整
        result = learner.record_user_adjustment(
            session_id=session_id,
            canvas_data_before=optimized_canvas,
            canvas_data_after=adjusted_canvas,
            adjusted_node_ids=adjustments_made
        )

        print(f"调整记录成功: {result['adjustments_recorded']} 个节点")

        # 学习偏好
        learned_prefs = learner.learn_layout_preferences()
        print(f"学习到的偏好:")
        print(f"   黄色节点对齐: {learned_prefs['yellow_node_alignment']['preferred_alignment']}")
        print(f"   置信度: {learned_prefs['confidence_scores']['overall']:.3f}")

        # 结束会话
        summary = learner.end_session(session_id)
        print(f"会话结束:")
        print(f"   总调整次数: {summary['total_adjustments']}")
        print(f"   会话时长: {summary['duration_minutes']:.1f} 分钟")

        return summary

    except Exception as e:
        print(f"偏好学习失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主演示函数"""

    print("Canvas学习系统G6智能布局演示")
    print("=" * 60)

    try:
        # 步骤1: 创建演示Canvas文件
        canvas_file = create_demo_canvas()

        # 步骤2: 布局优化演示
        optimized_file = demo_layout_optimization(canvas_file)

        if not optimized_file:
            print("布局优化失败，演示终止")
            return

        # 步骤3: 偏好学习演示
        learning_summary = demo_preference_learning(canvas_file, optimized_file)

        # 总结
        print("\n演示完成!")
        print("=" * 60)

        print(f"生成的文件:")
        print(f"   原始文件: {os.path.basename(canvas_file)}")
        print(f"   优化文件: {os.path.basename(optimized_file)}")

        if learning_summary:
            print(f"\n学习结果:")
            print(f"   学习调整: {learning_summary['total_adjustments']} 次")
            print(f"   主要调整类型: {learning_summary['most_adjusted_type']}")

        print(f"\n下一步:")
        print(f"   1. 在Obsidian中打开生成的Canvas文件")
        print(f"   2. 查看布局优化效果")
        print(f"   3. 手动调整并记录个人偏好")

        print(f"\n更多信息请参考: g6_layout_integration_guide.md")

    except Exception as e:
        print(f"演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()