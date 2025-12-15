#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
艾宾浩斯复习系统命令行接口

提供/review, /review-stats等命令的CLI实现，支持：
- 显示今日复习任务
- 显示复习统计数据
- 完成复习并记录结果
- 导出和备份功能

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import argparse
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
from ebbinghaus_review import EbbinghausReviewScheduler

class ReviewCLI:
    """复习系统命令行接口"""

    def __init__(self, db_path: str = "data/review_data.db"):
        """初始化CLI

        Args:
            db_path: 数据库路径
        """
        self.scheduler = EbbinghausReviewScheduler(db_path)

    def show_today_reviews(self, user_id: str = "default", format: str = "table") -> None:
        """显示今日复习任务

        Args:
            user_id: 用户ID
            format: 输出格式 ("table", "json")
        """
        try:
            reviews = self.scheduler.get_today_reviews(user_id)

            if not reviews:
                print("🎉 今日无复习任务！")
                return

            if format == "json":
                print(json.dumps(reviews, ensure_ascii=False, indent=2))
                return

            # 表格格式输出
            print(f"\n📅 今日复习任务 ({len(reviews)}个)")
            print("=" * 80)

            for i, review in enumerate(reviews, 1):
                print(f"\n{i}. {review['concept_name']}")
                print(f"   📁 Canvas文件: {review['canvas_file']}")
                print(f"   🕐 计划复习日期: {review['next_review_date']}")
                print(f"   💪 记忆强度: {review['memory_strength']:.1f}")
                print(f"   📊 记忆保持率: {review['retention_rate']:.1%}")
                print(f"   ⏰ 间隔天数: {review['review_interval_days']}天")
                print(f"   📈 掌握程度: {review['mastery_level']:.1%}")

                if review['recent_history']:
                    latest = review['recent_history'][-1]
                    print(f"   📝 最近评分: {latest['score']}/10")

            print("\n" + "=" * 80)
            print("💡 提示: 使用 'complete' 命令记录复习结果")

        except Exception as e:
            print(f"❌ 获取今日复习任务失败: {e}")

    def show_review_statistics(self, user_id: str = "default", days: int = 30, format: str = "summary") -> None:
        """显示复习统计数据

        Args:
            user_id: 用户ID
            days: 统计天数
            format: 输出格式 ("summary", "detailed", "json")
        """
        try:
            stats = self.scheduler.get_review_statistics(user_id, days)

            if format == "json":
                print(json.dumps(stats, ensure_ascii=False, indent=2))
                return

            print(f"\n📊 复习统计 ({days}天)")
            print("=" * 60)

            # 基本统计
            print(f"\n📈 基本统计:")
            print(f"   总复习次数: {stats['total_reviews']}")
            print(f"   完成复习次数: {stats['completed_reviews']}")
            print(f"   平均评分: {stats['average_score']:.1f}/10")
            print(f"   平均记忆保持率: {stats['average_retention_rate']:.1%}")
            print(f"   已掌握概念: {stats['concepts_mastered']}")
            print(f"   学习中概念: {stats['concepts_in_progress']}")

            # 学习效率
            efficiency = stats['learning_efficiency']
            print(f"\n⚡ 学习效率:")
            print(f"   平均复习时间: {efficiency['time_per_review_minutes']:.1f}分钟")
            print(f"   记忆提升率: {efficiency['retention_improvement_rate']:.1%}")
            print(f"   最佳学习时间: {efficiency['optimal_study_time_identified']}")

            # 主题分布
            if stats['subject_breakdown']:
                print(f"\n📚 主题分布:")
                for subject, data in stats['subject_breakdown'].items():
                    print(f"   {subject}:")
                    print(f"     总概念数: {data['total_concepts']}")
                    print(f"     已掌握: {data['mastered']}")
                    print(f"     学习中: {data['in_progress']}")
                    print(f"     困难: {data['struggling']}")

            print("\n" + "=" * 60)

        except Exception as e:
            print(f"❌ 获取复习统计失败: {e}")

    def complete_review_interactive(self, schedule_id: str = None) -> None:
        """交互式完成复习

        Args:
            schedule_id: 复习计划ID，如果为None则从今日任务中选择
        """
        try:
            # 获取目标复习计划
            if schedule_id is None:
                today_reviews = self.scheduler.get_today_reviews()
                if not today_reviews:
                    print("🎉 今日无复习任务！")
                    return

                print("📋 今日复习任务:")
                for i, review in enumerate(today_reviews, 1):
                    print(f"{i}. {review['concept_name']} (ID: {review['schedule_id'][:8]}...)")

                while True:
                    try:
                        choice = input(f"\n请选择任务 (1-{len(today_reviews)}) 或输入任务ID: ").strip()
                        if choice.isdigit():
                            choice_idx = int(choice) - 1
                            if 0 <= choice_idx < len(today_reviews):
                                schedule_id = today_reviews[choice_idx]['schedule_id']
                                break
                        else:
                            # 尝试作为任务ID处理
                            for review in today_reviews:
                                if review['schedule_id'].startswith(choice):
                                    schedule_id = review['schedule_id']
                                    break
                            else:
                                print("⚠️  无效选择，请重试")
                    except ValueError:
                        print("⚠️  请输入有效数字或ID")
            else:
                # 验证提供的schedule_id
                schedule = self.scheduler.get_review_schedule(schedule_id)
                if not schedule:
                    print(f"❌ 复习计划不存在: {schedule_id}")
                    return

                print(f"📚 复习概念: {schedule['concept_name']}")

            # 获取复习结果
            print(f"\n📝 请记录复习结果:")

            while True:
                try:
                    score = input("💯 满意度评分 (1-10): ").strip()
                    score = int(score)
                    if 1 <= score <= 10:
                        break
                    print("⚠️  评分必须在1-10之间")
                except ValueError:
                    print("⚠️  请输入有效数字")

            while True:
                try:
                    confidence = input("🎯 信心评分 (1-10): ").strip()
                    confidence = int(confidence)
                    if 1 <= confidence <= 10:
                        break
                    print("⚠️  评分必须在1-10之间")
                except ValueError:
                    print("⚠️  请输入有效数字")

            while True:
                try:
                    time_minutes = input("⏰ 复习用时(分钟): ").strip()
                    time_minutes = int(time_minutes)
                    if time_minutes >= 0:
                        break
                    print("⚠️  时间不能为负数")
                except ValueError:
                    print("⚠️  请输入有效数字")

            notes = input("📝 复习笔记(可选): ").strip() or None

            # 提交复习结果
            success = self.scheduler.complete_review(schedule_id, score, confidence, time_minutes, notes)
            if success:
                print(f"\n✅ 复习完成！")
                print(f"   评分: {score}/10")
                print(f"   信心: {confidence}/10")
                print(f"   用时: {time_minutes}分钟")

                # 显示下次复习信息
                updated_schedule = self.scheduler.get_review_schedule(schedule_id)
                if updated_schedule:
                    next_date = updated_schedule['next_review_date']
                    next_interval = updated_schedule['review_interval_days']
                    print(f"   下次复习: {next_date} ({next_interval}天后)")
            else:
                print("❌ 复习记录失败")

        except Exception as e:
            print(f"❌ 复习记录过程出错: {e}")

    def export_data(self, file_path: str, format: str = "json") -> None:
        """导出复习数据

        Args:
            file_path: 导出文件路径
            format: 导出格式 ("json", "csv")
        """
        try:
            success = self.scheduler.export_review_data(file_path, format)
            if success:
                print(f"✅ 数据导出成功: {file_path}")
            else:
                print("❌ 数据导出失败")
        except Exception as e:
            print(f"❌ 导出过程出错: {e}")

    def backup_database(self, backup_path: str = None) -> None:
        """备份数据库

        Args:
            backup_path: 备份文件路径
        """
        try:
            result_path = self.scheduler.backup_database(backup_path)
            print(f"✅ 数据库备份成功: {result_path}")
        except Exception as e:
            print(f"❌ 备份失败: {e}")

    def show_help(self) -> None:
        """显示帮助信息"""
        help_text = """
🧠 艾宾浩斯复习系统命令行工具

📋 可用命令:

  show [user_id] [format]     显示今日复习任务
    user_id: 用户ID (默认: default)
    format: 输出格式 (table|json, 默认: table)

  stats [user_id] [days] [format]  显示复习统计
    user_id: 用户ID (默认: default)
    days: 统计天数 (默认: 30)
    format: 输出格式 (summary|detailed|json, 默认: summary)

  complete [schedule_id]     完成复习 (交互式)
    schedule_id: 复习计划ID (可选，未提供时从今日任务选择)

  export <file_path> [format]  导出复习数据
    file_path: 导出文件路径
    format: 导出格式 (json|csv, 默认: json)

  backup [path]             备份数据库
    path: 备份文件路径 (可选，未提供时自动生成)

  help                      显示此帮助信息

💡 使用示例:
  python review_cli.py show
  python review_cli.py stats user123 7 detailed
  python review_cli.py complete review-abc123def
  python review_cli.py export data/export.json csv
  python review_cli.py backup backups/my_backup.db

📖 更多信息请参考项目文档。
        """
        print(help_text)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="艾宾浩斯复习系统命令行工具",
        add_help=False
    )

    parser.add_argument(
        "command",
        choices=["show", "stats", "complete", "export", "backup", "help"],
        help="要执行的命令"
    )

    parser.add_argument(
        "args",
        nargs="*",
        help="命令参数"
    )

    args = parser.parse_args()

    # 初始化CLI
    cli = ReviewCLI()

    # 执行命令
    if args.command == "show":
        user_id = args.args[0] if len(args.args) > 0 else "default"
        format_type = args.args[1] if len(args.args) > 1 else "table"
        cli.show_today_reviews(user_id, format_type)

    elif args.command == "stats":
        user_id = args.args[0] if len(args.args) > 0 else "default"
        days = int(args.args[1]) if len(args.args) > 1 and args.args[1].isdigit() else 30
        format_type = args.args[2] if len(args.args) > 2 else "summary"
        cli.show_review_statistics(user_id, days, format_type)

    elif args.command == "complete":
        schedule_id = args.args[0] if len(args.args) > 0 else None
        cli.complete_review_interactive(schedule_id)

    elif args.command == "export":
        if len(args.args) < 1:
            print("❌ 导出命令需要指定文件路径")
            sys.exit(1)
        file_path = args.args[0]
        format_type = args.args[1] if len(args.args) > 1 else "json"
        cli.export_data(file_path, format_type)

    elif args.command == "backup":
        backup_path = args.args[0] if len(args.args) > 0 else None
        cli.backup_database(backup_path)

    elif args.command == "help":
        cli.show_help()


if __name__ == "__main__":
    main()