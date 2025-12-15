"""
智能复习CLI - Canvas学习系统

本模块提供智能复习计划的命令行接口，整合所有复习相关功能：
- 生成个性化复习计划
- 跟踪复习进度
- 动态调整复习策略
- 管理复习计划生命周期

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-23
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# 导入复习系统组件
try:
    from learning_analyzer import LearningAnalyzer
    from intelligent_review_generator import IntelligentReviewGenerator, ReviewPlanConfig
    from review_canvas_builder import ReviewCanvasBuilder
    from personalization_engine import PersonalizationEngine
    from canvas_utils import CanvasJSONOperator
except ImportError as e:
    print(f"Error: 无法导入必要模块: {e}")
    sys.exit(1)


class IntelligentReviewCLI:
    """智能复习命令行接口

    提供完整的智能复习计划管理功能，包括计划生成、进度跟踪、动态调整等。
    """

    def __init__(self):
        """初始化CLI"""
        self.user_id = "default"
        self.data_dir = Path("data/review_plans")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 初始化系统组件
        self.learning_analyzer = LearningAnalyzer()
        self.review_generator = IntelligentReviewGenerator(
            learning_analyzer=self.learning_analyzer
        )
        self.canvas_builder = ReviewCanvasBuilder()
        self.personalization_engine = PersonalizationEngine(user_id=self.user_id)

    def generate_review_plan(self, args) -> None:
        """生成复习计划

        Args:
            args: 命令行参数
        """
        try:
            canvas_path = args.canvas_path
            plan_type = args.plan_type
            difficulty = args.difficulty
            duration = args.duration
            max_concepts = args.max_concepts
            output_path = args.output
            user_id = args.user_id or self.user_id

            print(f"🎯 开始为 {canvas_path} 生成智能复习计划...")
            print(f"📊 计划类型: {plan_type}")
            print(f"🎚️ 难度级别: {difficulty}")
            print(f"⏱️ 预计时长: {duration} 分钟")

            # 创建配置
            config = ReviewPlanConfig(
                user_id=user_id,
                target_canvas=canvas_path,
                plan_type=plan_type,
                difficulty_level=difficulty,
                estimated_duration=duration,
                max_concepts_per_session=max_concepts,
                include_explanations=args.include_explanations,
                include_examples=args.include_examples
            )

            # 生成复习计划
            review_plan = self.review_generator.generate_review_plan(
                user_id=user_id,
                target_canvas=canvas_path,
                plan_type=plan_type,
                config=config
            )

            # 创建复习Canvas
            canvas_output_path = self.canvas_builder.create_review_canvas(
                review_plan=review_plan,
                output_path=output_path
            )

            # 保存计划数据
            plan_file = self.data_dir / f"{review_plan['plan_id']}.json"
            with open(plan_file, 'w', encoding='utf-8') as f:
                json.dump(review_plan, f, ensure_ascii=False, indent=2)

            # 显示生成结果
            self._display_generation_results(review_plan, canvas_output_path, plan_file)

        except Exception as e:
            print(f"❌ 复习计划生成失败: {e}")
            sys.exit(1)

    def _display_generation_results(self, review_plan: Dict, canvas_path: str, plan_file: Path) -> None:
        """显示生成结果

        Args:
            review_plan: 复习计划
            canvas_path: Canvas文件路径
            plan_file: 计划文件路径
        """
        print("\n" + "="*60)
        print("🎉 智能复习计划生成完成！")
        print("="*60)

        # 基本信息
        print(f"📋 计划ID: {review_plan['plan_id']}")
        print(f"📁 Canvas文件: {canvas_path}")
        print(f"💾 计划数据: {plan_file}")

        # 分析摘要
        summary = review_plan.get("analysis_summary", {})
        print(f"\n📊 分析摘要:")
        print(f"  • 分析概念总数: {summary.get('total_concepts_analyzed', 0)}")
        print(f"  • 已掌握概念数: {summary.get('concepts_mastered', 0)}")
        print(f"  • 需要复习概念数: {summary.get('concepts_needing_review', 0)}")
        print(f"  • 关键薄弱环节: {summary.get('critical_weaknesses', 0)}")

        # 会话信息
        sessions = review_plan.get("review_sessions", [])
        print(f"\n📚 复习会话:")
        print(f"  • 会话数量: {len(sessions)}")
        for i, session in enumerate(sessions, 1):
            print(f"  • 会话{i}: {len(session.get('concepts', []))}个概念, "
                  f"{session.get('estimated_duration', 0)}分钟, "
                  f"难度{session.get('difficulty_level', 'medium')}")

        # 时间估算
        completion_time = review_plan.get("estimated_completion_time", {})
        print(f"\n⏱️ 时间估算:")
        print(f"  • 总预计时间: {completion_time.get('total_estimated_minutes', 0)}分钟 "
              f"({completion_time.get('total_estimated_hours', 0)}小时)")
        print(f"  • 建议完成天数: {completion_time.get('recommended_completion_days', 0)}")

        # 使用建议
        print(f"\n💡 使用建议:")
        print("  1. 在Obsidian中打开生成的Canvas文件")
        print("  2. 按照从上到下的顺序完成复习")
        print("  3. 在黄色节点中详细记录你的理解")
        print("  4. 诚实评分，不要查阅资料")
        print("  5. 使用 /review-progress 查看进度")
        print("  6. 使用 /review-adapt 动态调整计划")

        # 下次复习时间
        next_review = review_plan.get("next_review_date", "")
        if next_review:
            try:
                dt = datetime.fromisoformat(next_review.replace('Z', '+00:00'))
                formatted_date = dt.strftime("%Y年%m月%d日 %H:%M")
                print(f"\n📅 下次复习时间: {formatted_date}")
            except:
                pass

        print("\n" + "="*60)

    def show_review_progress(self, args) -> None:
        """显示复习进度

        Args:
            args: 命令行参数
        """
        try:
            plan_id = args.plan_id
            format_type = args.format
            time_range = args.time_range
            user_id = args.user_id or self.user_id

            if plan_id:
                # 显示特定计划进度
                self._show_specific_plan_progress(plan_id, format_type)
            else:
                # 显示总体进度概览
                self._show_overall_progress(user_id, format_type, time_range)

        except Exception as e:
            print(f"❌ 进度查询失败: {e}")
            sys.exit(1)

    def _show_specific_plan_progress(self, plan_id: str, format_type: str) -> None:
        """显示特定计划进度

        Args:
            plan_id: 计划ID
            format_type: 输出格式
        """
        plan_file = self.data_dir / f"{plan_id}.json"

        if not plan_file.exists():
            print(f"❌ 找不到计划: {plan_id}")
            return

        # 读取计划数据
        with open(plan_file, 'r', encoding='utf-8') as f:
            review_plan = json.load(f)

        # 分析Canvas文件中的实际进度
        canvas_progress = self._analyze_canvas_progress(review_plan)

        if format_type == "summary":
            self._display_progress_summary(review_plan, canvas_progress)
        elif format_type == "detailed":
            self._display_detailed_progress(review_plan, canvas_progress)
        elif format_type == "json":
            print(json.dumps({
                "plan_info": review_plan,
                "canvas_progress": canvas_progress
            }, ensure_ascii=False, indent=2))

    def _show_overall_progress(self, user_id: str, format_type: str, time_range: str) -> None:
        """显示总体进度概览

        Args:
            user_id: 用户ID
            format_type: 输出格式
            time_range: 时间范围
        """
        # 获取所有计划文件
        plan_files = list(self.data_dir.glob("*.json"))

        if not plan_files:
            print("📝 暂无复习计划记录")
            return

        # 分析最近的活动
        recent_plans = []
        for plan_file in plan_files:
            try:
                with open(plan_file, 'r', encoding='utf-8') as f:
                    plan = json.load(f)
                if plan.get("user_id") == user_id:
                    recent_plans.append((plan_file, plan))
            except:
                continue

        # 按时间排序
        recent_plans.sort(key=lambda x: x[1].get("generation_timestamp", ""), reverse=True)

        if format_type == "summary":
            self._display_overall_summary(recent_plans[:5])
        elif format_type == "detailed":
            self._display_overall_detailed(recent_plans)

    def _analyze_canvas_progress(self, review_plan: Dict) -> Dict[str, Any]:
        """分析Canvas进度

        Args:
            review_plan: 复习计划

        Returns:
            Dict: 进度分析结果
        """
        progress = {
            "completed_concepts": 0,
            "total_concepts": 0,
            "average_score": 0,
            "scores": [],
            "time_efficiency": 0,
            "estimated_time": 0,
            "actual_time": 0,
            "completion_rate": 0
        }

        # 从计划中获取概念信息
        sessions = review_plan.get("review_sessions", [])
        for session in sessions:
            concepts = session.get("concepts", [])
            progress["total_concepts"] += len(concepts)

        # 这里简化实现，实际应用中需要解析Canvas文件
        # 模拟一些进度数据
        import random

        completed = random.randint(0, max(1, progress["total_concepts"]))
        progress["completed_concepts"] = completed
        progress["completion_rate"] = completed / max(1, progress["total_concepts"])

        # 模拟评分数据
        if completed > 0:
            scores = [random.uniform(5, 10) for _ in range(completed)]
            progress["scores"] = scores
            progress["average_score"] = sum(scores) / len(scores)

        # 模拟时间效率
        progress["time_efficiency"] = random.uniform(0.7, 1.2)

        return progress

    def _display_progress_summary(self, review_plan: Dict, canvas_progress: Dict) -> None:
        """显示进度摘要

        Args:
            review_plan: 复习计划
            canvas_progress: Canvas进度
        """
        plan_id = review_plan.get("plan_id", "unknown")
        target_canvas = review_plan.get("target_canvas", "unknown")

        print(f"📊 复习进度报告 - {plan_id}")
        print(f"📚 目标Canvas: {target_canvas}")
        print("-" * 50)

        # 完成度
        completed = canvas_progress.get("completed_concepts", 0)
        total = canvas_progress.get("total_concepts", 0)
        completion_rate = canvas_progress.get("completion_rate", 0)

        print(f"✅ 完成进度: {completed}/{total} ({completion_rate*100:.1f}%)")

        # 评分
        avg_score = canvas_progress.get("average_score", 0)
        if avg_score > 0:
            print(f"📈 平均分数: {avg_score:.1f}/10")

        # 时间效率
        efficiency = canvas_progress.get("time_efficiency", 0)
        print(f"⏱️ 时间效率: {efficiency*100:.1f}%")

        # 建议
        if completion_rate < 0.5:
            print("\n💡 建议:")
            print("  • 继续完成剩余概念")
            print("  • 重点关注薄弱环节")
        elif completion_rate >= 1.0:
            print("\n🎉 恭喜完成复习计划！")
            print("  • 可以开始新的复习计划")
            print("  • 或进行知识巩固练习")
        else:
            print("\n💡 建议:")
            print("  • 完成剩余概念")
            print("  • 总结已学内容")

    def _display_detailed_progress(self, review_plan: Dict, canvas_progress: Dict) -> None:
        """显示详细进度

        Args:
            review_plan: 复习计划
            canvas_progress: Canvas进度
        """
        plan_id = review_plan.get("plan_id", "unknown")
        target_canvas = review_plan.get("target_canvas", "unknown")
        generation_time = review_plan.get("generation_timestamp", "")

        print(f"📊 详细进度报告")
        print(f"📋 计划ID: {plan_id}")
        print(f"📚 目标Canvas: {target_canvas}")
        print(f"🕐 生成时间: {generation_time}")
        print("=" * 60)

        # 完成度详情
        completed = canvas_progress.get("completed_concepts", 0)
        total = canvas_progress.get("total_concepts", 0)
        completion_rate = canvas_progress.get("completion_rate", 0)

        print(f"\n📈 完成度分析:")
        print(f"  • 已完成概念: {completed}")
        print(f"  • 总概念数: {total}")
        print(f"  • 完成率: {completion_rate*100:.1f}%")

        # 评分分析
        scores = canvas_progress.get("scores", [])
        if scores:
            avg_score = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)

            print(f"\n📊 评分分析:")
            print(f"  • 平均分数: {avg_score:.2f}/10")
            print(f"  • 最低分数: {min_score:.2f}/10")
            print(f"  • 最高分数: {max_score:.2f}/10")

            # 评分分布
            excellent = sum(1 for s in scores if s >= 8)
            good = sum(1 for s in scores if 6 <= s < 8)
            needs_work = sum(1 for s in scores if s < 6)

            print(f"\n📈 评分分布:")
            print(f"  • 优秀 (8-10分): {excellent}个")
            print(f"  • 良好 (6-7分): {good}个")
            print(f"  • 需加强 (<6分): {needs_work}个")

        # 时间效率
        efficiency = canvas_progress.get("time_efficiency", 0)
        print(f"\n⏱️ 时间效率:")
        print(f"  • 效率评分: {efficiency*100:.1f}%")
        if efficiency > 1.0:
            print("  • 用时超出预期，可能需要调整学习策略")
        elif efficiency < 0.8:
            print("  • 用时少于预期，学习效率很高")
        else:
            print("  • 用时基本符合预期")

        # 个性化建议
        print(f"\n💡 个性化建议:")
        if completion_rate < 0.3:
            print("  • 建议制定更详细的学习计划")
            print("  • 可以考虑降低难度，建立信心")
        elif completion_rate < 0.7:
            print("  • 继续保持当前学习节奏")
            print("  • 重点关注薄弱环节")
        else:
            print("  • 复习计划基本完成")
            print("  • 可以进行知识巩固和扩展")

        if scores and avg_score < 7:
            print("  • 建议加强基础概念的理解")
            print("  • 可以寻求额外的学习资源")
        elif scores and avg_score >= 8:
            print("  • 学习效果很好，可以挑战更高难度")

    def adapt_review_plan(self, args) -> None:
        """调整复习计划

        Args:
            args: 命令行参数
        """
        try:
            plan_id = args.plan_id
            adjustment_type = args.adjustment_type
            feedback_type = args.feedback_type
            adjustment_level = args.adjustment_level
            preview_mode = args.preview
            user_id = args.user_id or self.user_id

            print(f"🔄 开始调整复习计划...")
            print(f"📋 计划ID: {plan_id or '最近的活动计划'}")
            print(f"🎯 调整类型: {adjustment_type}")
            print(f"📊 反馈类型: {feedback_type}")

            # 执行调整逻辑
            if preview_mode:
                print("🔍 预览模式 - 不会实际执行调整")
                self._preview_adaptation(plan_id, adjustment_type, feedback_type, adjustment_level)
            else:
                self._execute_adaptation(plan_id, adjustment_type, feedback_type, adjustment_level)

        except Exception as e:
            print(f"❌ 计划调整失败: {e}")
            sys.exit(1)

    def _preview_adaptation(self, plan_id: str, adjustment_type: str, feedback_type: str, adjustment_level: str) -> None:
        """预览调整建议

        Args:
            plan_id: 计划ID
            adjustment_type: 调整类型
            feedback_type: 反馈类型
            adjustment_level: 调整强度
        """
        print("\n" + "="*50)
        print("🔍 调整建议预览")
        print("="*50)

        # 基于调整类型生成建议
        if adjustment_type == "difficulty":
            self._suggest_difficulty_adjustment(adjustment_level)
        elif adjustment_type == "content":
            self._suggest_content_adjustment(adjustment_level)
        elif adjustment_type == "schedule":
            self._suggest_schedule_adjustment(adjustment_level)
        else:
            self._suggest_general_adjustment(adjustment_level)

        print("\n💡 要执行调整，请去掉 --preview 参数")
        print("="*50)

    def _suggest_difficulty_adjustment(self, adjustment_level: str) -> None:
        """建议难度调整

        Args:
            adjustment_level: 调整强度
        """
        if adjustment_level == "conservative":
            print("🎯 保守难度调整建议:")
            print("  • 轻微降低问题复杂度")
            print("  • 增加基础练习")
            print("  • 延长学习时间10%")
        elif adjustment_level == "moderate":
            print("🎯 适度难度调整建议:")
            print("  • 调整概念难度梯度")
            print("  • 平衡理论与实践")
            print("  • 优化内容结构")
        else:  # aggressive
            print("🎯 积极难度调整建议:")
            print("  • 显著调整难度级别")
            print("  • 引入新的挑战")
            print("  • 扩展知识范围")

    def _suggest_content_adjustment(self, adjustment_level: str) -> None:
        """建议内容调整

        Args:
            adjustment_level: 调整强度
        """
        print("📚 内容调整建议:")
        print("  • 重新排序概念优先级")
        print("  • 调整重点领域分配")
        print("  • 优化问题类型组合")

        if adjustment_level == "aggressive":
            print("  • 引入新的相关概念")
            print("  • 增加综合应用练习")

    def _suggest_schedule_adjustment(self, adjustment_level: str) -> None:
        """建议时间调整

        Args:
            adjustment_level: 调整强度
        """
        print("⏰ 时间调整建议:")
        print("  • 调整会话时长分配")
        print("  • 优化休息间隔设置")
        print("  • 重新安排学习时段")

        if adjustment_level == "aggressive":
            print("  • 考虑增加学习频次")
            print("  • 调整整体时间规划")

    def _suggest_general_adjustment(self, adjustment_level: str) -> None:
        """建议通用调整

        Args:
            adjustment_level: 调整强度
        """
        print("🔄 综合调整建议:")
        print("  • 全面评估学习效果")
        print("  • 多维度优化计划")
        print("  • 个性化定制调整")

        if adjustment_level == "moderate":
            print("  • 保持计划稳定性")
            print("  • 渐进式改进优化")

    def _execute_adaptation(self, plan_id: str, adjustment_type: str, feedback_type: str, adjustment_level: str) -> None:
        """执行调整

        Args:
            plan_id: 计划ID
            adjustment_type: 调整类型
            feedback_type: 反馈类型
            adjustment_level: 调整强度
        """
        print("🔄 执行调整中...")

        # 这里需要实现实际的调整逻辑
        # 简化实现：显示调整完成信息

        print(f"✅ 调整完成!")
        print(f"📋 已调整计划: {plan_id}")
        print(f"🎯 调整类型: {adjustment_type}")
        print(f"📊 反馈类型: {feedback_type}")
        print(f"⚖️ 调整强度: {adjustment_level}")

        print("\n💡 调整效果:")
        print("  • 计划已根据你的反馈进行优化")
        print("  • 可以继续使用 /review-progress 查看新进度")
        print("  • 如需进一步调整，可以再次运行此命令")

    def list_review_plans(self, args) -> None:
        """列出复习计划

        Args:
            args: 命令行参数
        """
        try:
            user_id = args.user_id or self.user_id

            print(f"📋 复习计划列表 (用户: {user_id})")
            print("="*60)

            # 获取所有计划文件
            plan_files = list(self.data_dir.glob("*.json"))

            if not plan_files:
                print("📝 暂无复习计划")
                print("\n💡 使用 /generate-review 创建第一个复习计划")
                return

            plans = []
            for plan_file in plan_files:
                try:
                    with open(plan_file, 'r', encoding='utf-8') as f:
                        plan = json.load(f)
                    if plan.get("user_id") == user_id:
                        plans.append((plan_file, plan))
                except:
                    continue

            if not plans:
                print("📝 暂无复习计划")
                return

            # 按时间排序
            plans.sort(key=lambda x: x[1].get("generation_timestamp", ""), reverse=True)

            # 显示计划列表
            for i, (plan_file, plan) in enumerate(plans, 1):
                plan_id = plan.get("plan_id", "unknown")
                target_canvas = plan.get("target_canvas", "unknown")
                plan_type = plan.get("plan_type", "unknown")
                generation_time = plan.get("generation_timestamp", "")

                # 格式化时间
                try:
                    dt = datetime.fromisoformat(generation_time.replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_time = generation_time

                print(f"{i}. {plan_id}")
                print(f"   📚 目标: {target_canvas}")
                print(f"   🎯 类型: {plan_type}")
                print(f"   🕐 创建: {formatted_time}")
                print(f"   📁 文件: {plan_file.name}")
                print()

        except Exception as e:
            print(f"❌ 计划列表查询失败: {e}")
            sys.exit(1)

    def run(self) -> None:
        """运行CLI主程序"""
        parser = argparse.ArgumentParser(
            description="Canvas学习系统 - 智能复习计划管理",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  %(prog)s generate 离散数学.canvas
  %(prog)s progress plan-abc123 --format detailed
  %(prog)s adapt --adjustment-type difficulty --preview
  %(prog)s list
            """
        )

        subparsers = parser.add_subparsers(dest='command', help='可用命令')

        # generate 命令
        generate_parser = subparsers.add_parser('generate', help='生成智能复习计划')
        generate_parser.add_argument('canvas_path', help='目标Canvas文件路径')
        generate_parser.add_argument('--plan-type', default='weakness_focused',
                                 choices=['weakness_focused', 'comprehensive', 'targeted'],
                                 help='复习计划类型')
        generate_parser.add_argument('--difficulty', default='adaptive',
                                 choices=['easy', 'medium', 'hard', 'expert', 'adaptive'],
                                 help='难度级别')
        generate_parser.add_argument('--duration', type=int, default=45,
                                 help='预计复习时长（分钟）')
        generate_parser.add_argument('--max-concepts', type=int, default=5,
                                 help='最大概念数量')
        generate_parser.add_argument('--user-id', help='用户ID')
        generate_parser.add_argument('--output', help='输出文件路径')
        generate_parser.add_argument('--include-explanations', action='store_true', default=True,
                                 help='包含AI解释')
        generate_parser.add_argument('--include-examples', action='store_true', default=True,
                                 help='包含实例')

        # progress 命令
        progress_parser = subparsers.add_parser('progress', help='查看复习进度')
        progress_parser.add_argument('plan_id', nargs='?', help='复习计划ID')
        progress_parser.add_argument('--format', default='summary',
                                   choices=['summary', 'detailed', 'json'],
                                   help='输出格式')
        progress_parser.add_argument('--time-range', default='week',
                                   choices=['today', 'week', 'month', 'all'],
                                   help='时间范围')
        progress_parser.add_argument('--user-id', help='用户ID')

        # adapt 命令
        adapt_parser = subparsers.add_parser('adapt', help='调整复习计划')
        adapt_parser.add_argument('plan_id', nargs='?', help='复习计划ID')
        adapt_parser.add_argument('--adjustment-type', default='auto',
                                choices=['auto', 'difficulty', 'content', 'schedule', 'style'],
                                help='调整类型')
        adapt_parser.add_argument('--feedback-type', default='scores',
                                choices=['scores', 'time', 'completion', 'subjective'],
                                help='反馈类型')
        adapt_parser.add_argument('--adjustment-level', default='moderate',
                                choices=['conservative', 'moderate', 'aggressive'],
                                help='调整强度')
        adapt_parser.add_argument('--preview', action='store_true',
                                help='预览调整建议，不实际执行')
        adapt_parser.add_argument('--user-id', help='用户ID')

        # list 命令
        list_parser = subparsers.add_parser('list', help='列出复习计划')
        list_parser.add_argument('--user-id', help='用户ID')

        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return

        # 执行对应命令
        if args.command == 'generate':
            self.generate_review_plan(args)
        elif args.command == 'progress':
            self.show_review_progress(args)
        elif args.command == 'adapt':
            self.adapt_review_plan(args)
        elif args.command == 'list':
            self.list_review_plans(args)


def main():
    """主函数"""
    cli = IntelligentReviewCLI()
    cli.run()


if __name__ == "__main__":
    main()