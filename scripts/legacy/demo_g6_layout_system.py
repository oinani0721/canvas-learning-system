"""
Canvas学习系统G6智能布局演示脚本

这个脚本演示了完整的G6布局优化和学习流程:
1. 创建测试Canvas文件
2. 应用不同的布局算法
3. 评估布局质量
4. 模拟用户调整和学习偏好
5. 生成最终优化版本

运行方式:
python demo_g6_layout_system.py

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
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
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
                "id": "question-3-application",
                "type": "text",
                "x": 600,
                "y": 400,
                "width": 350,
                "height": 120,
                "color": "4",
                "text": "导数在物理和工程中有哪些应用？\n\n请举例说明瞬时变化率的概念。"
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
                "id": "understanding-3",
                "type": "text",
                "x": 600,
                "y": 550,
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
                "id": "subquestion-1-2",
                "type": "text",
                "x": 1000,
                "y": 270,
                "width": 300,
                "height": 100,
                "color": "4",
                "text": "为什么需要用极限来定义导数？"
            },
            {
                "id": "subquestion-2-1",
                "type": "text",
                "x": 1000,
                "y": 420,
                "width": 300,
                "height": 100,
                "color": "3",
                "text": "如何从几何角度理解导数？"
            },
            {
                "id": "subquestion-3-1",
                "type": "text",
                "x": 1000,
                "y": 570,
                "width": 300,
                "height": 100,
                "color": "4",
                "text": "速度、加速度与导数的关系？"
            },
            {
                "id": "explanation-oral",
                "type": "text",
                "x": 1400,
                "y": 180,
                "width": 280,
                "height": 80,
                "color": "5",
                "text": "🗣️ 导数的口语化解释"
            },
            {
                "id": "explanation-visual",
                "type": "text",
                "x": 1400,
                "y": 280,
                "width": 280,
                "height": 80,
                "color": "5",
                "text": "📊 导数的几何可视化"
            },
            {
                "id": "explanation-memory",
                "type": "text",
                "x": 1400,
                "y": 380,
                "width": 280,
                "height": 80,
                "color": "5",
                "text": "⚓ 导数的记忆技巧"
            }
        ],
        "edges": [
            {"id": "edge-material-q1", "fromNode": "material-calculus", "toNode": "question-1-definition", "label": "拆解自"},
            {"id": "edge-material-q2", "fromNode": "material-calculus", "toNode": "question-2-geometric", "label": "拆解自"},
            {"id": "edge-material-q3", "fromNode": "material-calculus", "toNode": "question-3-application", "label": "拆解自"},
            {"id": "edge-q1-yellow", "fromNode": "question-1-definition", "toNode": "understanding-1", "label": "个人理解"},
            {"id": "edge-q2-yellow", "fromNode": "question-2-geometric", "toNode": "understanding-2", "label": "个人理解"},
            {"id": "edge-q3-yellow", "fromNode": "question-3-application", "toNode": "understanding-3", "label": "个人理解"},
            {"id": "edge-yellow-sub1-1", "fromNode": "understanding-1", "toNode": "subquestion-1-1", "label": "拆解自"},
            {"id": "edge-yellow-sub1-2", "fromNode": "understanding-1", "toNode": "subquestion-1-2", "label": "拆解自"},
            {"id": "edge-yellow-sub2-1", "fromNode": "understanding-2", "toNode": "subquestion-2-1", "label": "拆解自"},
            {"id": "edge-yellow-sub3-1", "fromNode": "understanding-3", "toNode": "subquestion-3-1", "label": "拆解自"},
            {"id": "edge-yellow-oral", "fromNode": "understanding-1", "toNode": "explanation-oral", "label": "补充解释"},
            {"id": "edge-yellow-visual", "fromNode": "understanding-1", "toNode": "explanation-visual", "label": "补充解释"},
            {"id": "edge-yellow-memory", "fromNode": "understanding-2", "toNode": "explanation-memory", "label": "补充解释"}
        ]
    }

    # 保存演示文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    demo_file = f"C:/Users/ROG/托福/笔记库/测试/demo-calculus-{timestamp}.canvas"

    os.makedirs(os.path.dirname(demo_file), exist_ok=True)

    with open(demo_file, 'w', encoding='utf-8') as f:
        json.dump(demo_canvas, f, ensure_ascii=False, indent=2)

    print(f"✅ 演示Canvas文件已创建: {demo_file}")
    return demo_file


def demo_layout_optimization(canvas_file):
    """演示布局优化"""

    print("\n🚀 开始布局优化演示...")

    # 创建优化器
    optimizer = G6CanvasLayoutOptimizer()

    # 读取Canvas文件
    with open(canvas_file, 'r', encoding='utf-8') as f:
        canvas_data = json.load(f)

    print(f"📊 原始Canvas信息:")
    print(f"   节点数量: {len(canvas_data['nodes'])}")
    print(f"   边数量: {len(canvas_data['edges'])}")

    # 测试不同布局算法
    layout_types = ['compactbox', 'mindmap', 'dendrogram']
    optimized_files = {}

    for layout_type in layout_types:
        print(f"\n🎨 应用 {layout_type} 布局...")

        try:
            # 应用布局优化
            optimized_canvas = optimizer.optimize_canvas_layout(canvas_data, layout_type)

            # 保存优化结果
            timestamp = datetime.now().strftime("%H%M%S")
            output_file = canvas_file.replace('.canvas', f'-{layout_type}-optimized-{timestamp}.canvas')

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(optimized_canvas, f, ensure_ascii=False, indent=2)

            optimized_files[layout_type] = output_file
            print(f"✅ {layout_type} 布局完成: {output_file}")

        except Exception as e:
            print(f"❌ {layout_type} 布局失败: {e}")

    return optimized_files


def demo_layout_quality_testing(canvas_file):
    """演示布局质量测试"""

    print("\n🧪 开始布局质量测试...")

    # 创建测试器
    tester = G6LayoutTester()

    try:
        # 运行测试
        test_results = tester.test_layout_optimization(canvas_file)

        # 输出结果
        print("\n📊 测试结果:")
        print("=" * 60)

        for layout_type, result in test_results['results'].items():
            if result['success']:
                metrics = result['quality_metrics']
                print(f"✅ {layout_type.upper()} 布局:")
                print(f"   📈 整体评分: {metrics['overall_score']:.3f}")
                print(f"   🎯 黄色对齐: {metrics['yellow_alignment']:.3f}")
                print(f"   📊 层次清晰: {metrics['hierarchy_clarity']:.3f}")
                print(f"   🚫 无重叠: {metrics['overlap_avoidance']:.3f}")
                print(f"   ⚖️ 对称性: {metrics['symmetry']:.3f}")
                print(f"   📏 空间效率: {metrics['space_efficiency']:.3f}")
                print(f"   📁 输出文件: {os.path.basename(result['output_file'])}")
            else:
                print(f"❌ {layout_type.upper()} 布局: {result['error']}")
            print()

        print(f"🏆 推荐布局: {test_results['recommendation'].upper()}")

        return test_results

    except Exception as e:
        print(f"❌ 质量测试失败: {e}")
        return None


def demo_preference_learning(canvas_file, optimized_files):
    """演示偏好学习"""

    print("\n🧠 开始偏好学习演示...")

    # 创建学习器
    learner = G6LayoutPreferenceLearner()

    # 开始学习会话
    best_layout = list(optimized_files.keys())[0]  # 使用第一个可用的布局
    session_id = learner.start_new_session(canvas_file, best_layout)

    print(f"🎯 学习会话开始: {session_id}")
    print(f"📁 布局类型: {best_layout}")

    # 读取原始和优化后的Canvas
    with open(canvas_file, 'r', encoding='utf-8') as f:
        original_canvas = json.load(f)

    with open(optimized_files[best_layout], 'r', encoding='utf-8') as f:
        optimized_canvas = json.load(f)

    # 模拟用户调整
    print("\n📝 模拟用户调整...")

    # 创建轻微调整的版本（模拟用户微调）
    adjusted_canvas = json.loads(json.dumps(optimized_canvas))  # 深拷贝

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

    print(f"   模拟调整了 {len(adjustments_made)} 个节点")

    # 记录用户调整
    try:
        result = learner.record_user_adjustment(
            session_id=session_id,
            canvas_data_before=optimized_canvas,
            canvas_data_after=adjusted_canvas,
            adjusted_node_ids=adjustments_made
        )

        print(f"✅ 调整记录成功: {result['adjustments_recorded']} 个节点")

        # 学习偏好
        learned_prefs = learner.learn_layout_preferences()
        print(f"🎓 学习到的偏好:")
        print(f"   黄色节点对齐: {learned_prefs['yellow_node_alignment']['preferred_alignment']}")
        print(f"   置信度: {learned_prefs['confidence_scores']['overall']:.3f}")

        # 结束会话
        summary = learner.end_session(session_id)
        print(f"🏁 会话结束:")
        print(f"   总调整次数: {summary['total_adjustments']}")
        print(f"   会话时长: {summary['duration_minutes']:.1f} 分钟")

        # 应用学习到的偏好重新优化
        print(f"\n🔄 应用学习偏好重新优化...")

        # 创建新的优化器并应用偏好
        final_optimizer = G6CanvasLayoutOptimizer()
        final_optimizer.update_preferences(learned_prefs['preferences'])

        final_canvas = final_optimizer.optimize_canvas_layout(original_canvas, best_layout)

        # 保存最终结果
        final_file = canvas_file.replace('.canvas', f'-final-optimized-{datetime.now().strftime("%H%M%S")}.canvas')
        with open(final_file, 'w', encoding='utf-8') as f:
            json.dump(final_canvas, f, ensure_ascii=False, indent=2)

        print(f"✅ 最终优化完成: {final_file}")

        return final_file, summary

    except Exception as e:
        print(f"❌ 偏好学习失败: {e}")
        return None, None


def main():
    """主演示函数"""

    print("Canvas学习系统G6智能布局演示")
    print("=" * 60)

    try:
        # 步骤1: 创建演示Canvas文件
        canvas_file = create_demo_canvas()

        # 步骤2: 布局优化演示
        optimized_files = demo_layout_optimization(canvas_file)

        if not optimized_files:
            print("❌ 布局优化失败，演示终止")
            return

        # 步骤3: 质量测试演示
        test_results = demo_layout_quality_testing(canvas_file)

        # 步骤4: 偏好学习演示
        final_file, learning_summary = demo_preference_learning(canvas_file, optimized_files)

        # 总结
        print("\n🎉 演示完成!")
        print("=" * 60)

        print(f"📁 生成的文件:")
        print(f"   原始文件: {os.path.basename(canvas_file)}")
        for layout_type, file_path in optimized_files.items():
            print(f"   {layout_type}布局: {os.path.basename(file_path)}")
        if final_file:
            print(f"   最终优化: {os.path.basename(final_file)}")

        print(f"\n📊 测试结果摘要:")
        if test_results:
            print(f"   推荐布局: {test_results['recommendation']}")
            best_result = test_results['results'].get(test_results['recommendation'])
            if best_result and best_result['success']:
                print(f"   最佳评分: {best_result['quality_metrics']['overall_score']:.3f}")

        if learning_summary:
            print(f"\n🧠 学习结果:")
            print(f"   学习调整: {learning_summary['total_adjustments']} 次")
            print(f"   主要调整类型: {learning_summary['most_adjusted_type']}")

        print(f"\n💡 下一步:")
        print(f"   1. 在Obsidian中打开生成的Canvas文件")
        print(f"   2. 比较不同布局算法的效果")
        print(f"   3. 手动调整并记录个人偏好")
        print(f"   4. 使用学习系统持续优化布局")

        print(f"\n📖 更多信息请参考: g6_layout_integration_guide.md")

    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()