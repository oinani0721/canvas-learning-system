"""
Canvas学习系统 - 错误分析器
Story 8.11: 集成Canvas专用错误日志系统

本模块提供错误分析和用户查询接口，包括：
- 错误模式识别
- 错误统计分析
- 用户查询命令
- 错误报告生成

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import argparse

# 导入错误日志系统
try:
    from canvas_error_logger import get_canvas_error_logger
    from error_recovery_advisor import get_error_recovery_advisor, diagnose_error_pattern
    ERROR_ANALYZER_ENABLED = True
except ImportError as e:
    ERROR_ANALYZER_ENABLED = False
    print(f"警告: 错误分析器依赖未安装 - {e}")


class ErrorAnalyzer:
    """错误分析器"""

    def __init__(self):
        """初始化错误分析器"""
        if ERROR_ANALYZER_ENABLED:
            self.logger = get_canvas_error_logger()
        else:
            self.logger = None

    def show_recent_errors(self, limit: int = 10, severity: str = None) -> None:
        """显示最近的错误记录

        Args:
            limit: 显示记录数量限制
            severity: 严重性过滤
        """
        if not self.logger:
            print("❌ 错误日志系统未启用")
            return

        errors = self.logger.get_recent_errors(limit, severity)

        if not errors:
            print("✅ 没有找到错误记录")
            return

        print(f"\n🔍 最近 {len(errors)} 条错误记录:")
        print("=" * 80)

        for i, error in enumerate(errors, 1):
            timestamp = error.get("timestamp", "Unknown time")
            operation = error.get("operation_type", "Unknown operation")
            error_msg = error.get("error_information", {}).get("error_message", "No error message")
            error_type = error.get("error_information", {}).get("error_type", "Unknown")

            print(f"\n{i:2d}. ⚠️  {timestamp}")
            print(f"    操作: {operation}")
            print(f"    错误: {error_type}: {error_msg}")

            # 显示恢复建议
            recovery_actions = error.get("error_information", {}).get("recovery_actions", [])
            if recovery_actions:
                print(f"    💡 建议:")
                for action in recovery_actions[:2]:  # 只显示前2个建议
                    print(f"       • {action}")

    def show_error_statistics(self, period_hours: int = 24) -> None:
        """显示错误统计摘要

        Args:
            period_hours: 统计时间范围(小时)
        """
        if not self.logger:
            print("❌ 错误日志系统未启用")
            return

        summary = self.logger.generate_error_summary(period_hours)
        report = summary.get("error_summary_report", {})

        print(f"\n📊 错误统计摘要 (过去 {period_hours} 小时):")
        print("=" * 80)

        # 总体概览
        overview = report.get("error_overview", {})
        total_errors = overview.get("total_errors", 0)
        total_warnings = overview.get("total_warnings", 0)
        total_info = overview.get("total_info_logs", 0)
        error_rate = overview.get("error_rate_percentage", 0)
        most_recent = overview.get("most_recent_error")

        print(f"\n📈 总体概览:")
        print(f"   总操作数: {overview.get('total_logs_analyzed', 0)}")
        print(f"   错误数: {total_errors}")
        print(f"   警告数: {total_warnings}")
        print(f"   信息数: {total_info}")
        print(f"   错误率: {error_rate:.2f}%")
        if most_recent:
            print(f"   最近错误: {most_recent}")

        # 错误分类
        categories = report.get("error_category_breakdown", {})
        if categories:
            print(f"\n📂 错误分类:")
            for category, data in categories.items():
                print(f"   {category}: {data['count']} ({data['percentage']:.1f}%)")

        # 严重性分布
        severity_dist = report.get("severity_distribution", {})
        if severity_dist:
            print(f"\n🎯 严重性分布:")
            for severity, count in severity_dist.items():
                print(f"   {severity}: {count}")

        # 性能影响
        performance = report.get("performance_impact", {})
        stability_score = performance.get("system_stability_score", 100)
        print(f"\n⚡ 系统稳定性: {stability_score:.1f}/100")

        # 建议
        if error_rate > 5:
            print(f"\n⚠️  注意: 错误率较高 ({error_rate:.2f}%)，建议检查系统状态")
        elif error_rate > 1:
            print(f"\n💡 提示: 错误率略高 ({error_rate:.2f}%)，可以关注错误模式")
        else:
            print(f"\n✅ 系统运行良好，错误率正常 ({error_rate:.2f}%)")

    def search_errors(self, query: str, start_hours: int = 24, end_hours: int = 0) -> None:
        """搜索错误日志

        Args:
            query: 搜索关键词
            start_hours: 开始时间(多少小时前)
            end_hours: 结束时间(多少小时前)
        """
        if not self.logger:
            print("❌ 错误日志系统未启用")
            return

        # 计算时间范围
        end_time = datetime.now() - timedelta(hours=end_hours) if end_hours > 0 else None
        start_time = datetime.now() - timedelta(hours=start_hours) if start_hours > 0 else None

        matches = self.logger.search_error_logs(query, start_time, end_time)

        if not matches:
            print(f"🔍 没有找到包含 '{query}' 的错误记录")
            return

        print(f"\n🔍 搜索结果: 找到 {len(matches)} 条包含 '{query}' 的记录")
        print("=" * 80)

        for i, error in enumerate(matches, 1):
            timestamp = error.get("timestamp", "Unknown time")
            operation = error.get("operation_type", "Unknown operation")
            error_msg = error.get("error_information", {}).get("error_message", "No error message")

            print(f"\n{i}. ⚠️  {timestamp}")
            print(f"    操作: {operation}")
            print(f"    错误: {error_msg}")

            # 显示Canvas上下文
            canvas_ctx = error.get("canvas_context", {})
            if canvas_ctx.get("canvas_file_path"):
                print(f"    文件: {canvas_ctx['canvas_file_path']}")

            # 显示Agent上下文
            agent_ctx = error.get("agent_context", {})
            if agent_ctx.get("agent_name"):
                print(f"    Agent: {agent_ctx['agent_name']}")

    def analyze_error_patterns(self, limit: int = 50) -> None:
        """分析错误模式

        Args:
            limit: 分析的错误记录数量限制
        """
        if not self.logger:
            print("❌ 错误日志系统未启用")
            return

        # 获取最近的错误记录
        recent_errors = self.logger.get_recent_errors(limit)

        if not recent_errors:
            print("✅ 没有足够的错误数据进行模式分析")
            return

        # 使用错误恢复建议器进行模式分析
        diagnosis = diagnose_error_pattern(recent_errors)

        print(f"\n🔬 错误模式分析 (基于最近 {len(recent_errors)} 条错误记录):")
        print("=" * 80)

        if not diagnosis.get("pattern_detected"):
            print(diagnosis.get("analysis", "无法分析错误模式"))
            return

        # 显示最频繁的错误
        most_frequent = diagnosis.get("most_frequent_error", {})
        print(f"\n🎯 最频繁错误:")
        print(f"   类型: {most_frequent.get('type', 'Unknown')}")
        print(f"   次数: {most_frequent.get('count', 0)}")
        print(f"   占比: {most_frequent.get('percentage', 0):.1f}%")

        # 显示受影响最大的类别
        most_affected = diagnosis.get("most_affected_category", {})
        print(f"\n📂 受影响最大的类别:")
        print(f"   类别: {most_affected.get('name', 'Unknown')}")
        print(f"   次数: {most_affected.get('count', 0)}")
        print(f"   占比: {most_affected.get('percentage', 0):.1f}%")

        # 显示时间模式
        time_pattern = diagnosis.get("time_pattern", {})
        print(f"\n⏰ 时间模式:")
        print(f"   模式: {time_pattern.get('pattern', 'Unknown')}")
        print(f"   描述: {time_pattern.get('description', 'No description')}")
        if 'average_interval_seconds' in time_pattern:
            avg_interval = time_pattern['average_interval_seconds']
            if avg_interval < 60:
                print(f"   平均间隔: {avg_interval:.1f} 秒 (集中爆发)")
            elif avg_interval < 3600:
                print(f"   平均间隔: {avg_interval/60:.1f} 分钟 (频繁发生)")
            else:
                print(f"   平均间隔: {avg_interval/3600:.1f} 小时 (零星发生)")

        # 显示建议
        recommendations = diagnosis.get("recommendations", [])
        if recommendations:
            print(f"\n💡 改进建议:")
            for rec in recommendations:
                print(f"   • {rec}")

        # 需要关注程度
        needs_attention = diagnosis.get("needs_attention", False)
        if needs_attention:
            print(f"\n⚠️  需要关注: 某种错误类型占比过高，建议优先处理")
        else:
            print(f"\n✅ 错误分布相对均匀，没有明显的问题模式")

    def generate_error_report(self, output_file: str = None, period_hours: int = 24) -> str:
        """生成完整的错误报告

        Args:
            output_file: 输出文件路径 (可选)
            period_hours: 统计时间范围

        Returns:
            str: 报告内容
        """
        if not self.logger:
            return "❌ 错误日志系统未启用"

        # 生成统计摘要
        summary = self.logger.generate_error_summary(period_hours)

        # 获取最近错误
        recent_errors = self.logger.get_recent_errors(20)

        # 模式分析
        pattern_diagnosis = diagnose_error_pattern(recent_errors) if recent_errors else {}

        # 构建报告
        report_lines = [
            "# Canvas学习系统错误报告",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"统计范围: 过去 {period_hours} 小时",
            "",
            "## 📊 统计概览",
            ""
        ]

        # 添加统计信息
        report_data = summary.get("error_summary_report", {})
        overview = report_data.get("error_overview", {})
        report_lines.extend([
            f"- 总操作数: {overview.get('total_logs_analyzed', 0)}",
            f"- 错误数: {overview.get('total_errors', 0)}",
            f"- 警告数: {overview.get('total_warnings', 0)}",
            f"- 错误率: {overview.get('error_rate_percentage', 0):.2f}%",
            f"- 系统稳定性: {report_data.get('performance_impact', {}).get('system_stability_score', 100):.1f}/100",
            ""
        ])

        # 添加错误分类
        categories = report_data.get("error_category_breakdown", {})
        if categories:
            report_lines.extend([
                "## 📂 错误分类",
                ""
            ])
            for category, data in categories.items():
                report_lines.append(f"- **{category}**: {data['count']} ({data['percentage']:.1f}%)")
            report_lines.append("")

        # 添加模式分析
        if pattern_diagnosis.get("pattern_detected"):
            report_lines.extend([
                "## 🔍 错误模式分析",
                ""
            ])

            most_frequent = pattern_diagnosis.get("most_frequent_error", {})
            report_lines.extend([
                f"- **最频繁错误**: {most_frequent.get('type', 'Unknown')} ({most_frequent.get('count', 0)} 次, {most_frequent.get('percentage', 0):.1f}%)",
                ""
            ])

            recommendations = pattern_diagnosis.get("recommendations", [])
            if recommendations:
                report_lines.extend([
                    "## 💡 改进建议",
                    ""
                ])
                for rec in recommendations:
                    report_lines.append(f"- {rec}")
                report_lines.append("")

        # 添加最近错误详情
        if recent_errors:
            report_lines.extend([
                "## 📋 最近错误详情",
                ""
            ])

            for i, error in enumerate(recent_errors[:10], 1):
                timestamp = error.get("timestamp", "Unknown time")
                operation = error.get("operation_type", "Unknown operation")
                error_info = error.get("error_information", {})
                error_type = error_info.get("error_type", "Unknown")
                error_msg = error_info.get("error_message", "No message")

                report_lines.extend([
                    f"### {i}. {error_type}",
                    f"- **时间**: {timestamp}",
                    f"- **操作**: {operation}",
                    f"- **错误**: {error_msg}",
                    ""
                ])

                recovery_actions = error_info.get("recovery_actions", [])
                if recovery_actions:
                    report_lines.append("**恢复建议**:")
                    for action in recovery_actions:
                        report_lines.append(f"- {action}")
                    report_lines.append("")

        report_content = "\n".join(report_lines)

        # 保存到文件
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                print(f"📄 错误报告已保存到: {output_file}")
            except Exception as e:
                print(f"❌ 保存报告失败: {e}")

        return report_content


def main():
    """命令行入口"""
    if not ERROR_ANALYZER_ENABLED:
        print("❌ 错误分析器未启用，请检查依赖安装")
        sys.exit(1)

    analyzer = ErrorAnalyzer()
    parser = argparse.ArgumentParser(description="Canvas学习系统错误分析器")

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # recent 命令
    recent_parser = subparsers.add_parser('recent', help='显示最近的错误')
    recent_parser.add_argument('-n', '--limit', type=int, default=10, help='显示记录数量')
    recent_parser.add_argument('-s', '--severity', help='严重性过滤')

    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='显示错误统计')
    stats_parser.add_argument('-h', '--hours', type=int, default=24, help='统计时间范围(小时)')

    # search 命令
    search_parser = subparsers.add_parser('search', help='搜索错误日志')
    search_parser.add_argument('query', help='搜索关键词')
    search_parser.add_argument('-s', '--start', type=int, default=24, help='开始时间(小时前)')
    search_parser.add_argument('-e', '--end', type=int, default=0, help='结束时间(小时前)')

    # patterns 命令
    patterns_parser = subparsers.add_parser('patterns', help='分析错误模式')
    patterns_parser.add_argument('-n', '--limit', type=int, default=50, help='分析记录数量')

    # report 命令
    report_parser = subparsers.add_parser('report', help='生成错误报告')
    report_parser.add_argument('-o', '--output', help='输出文件路径')
    report_parser.add_argument('-h', '--hours', type=int, default=24, help='统计时间范围(小时)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'recent':
            analyzer.show_recent_errors(args.limit, args.severity)
        elif args.command == 'stats':
            analyzer.show_error_statistics(args.hours)
        elif args.command == 'search':
            analyzer.search_errors(args.query, args.start, args.end)
        elif args.command == 'patterns':
            analyzer.analyze_error_patterns(args.limit)
        elif args.command == 'report':
            analyzer.generate_error_report(args.output, args.hours)
        else:
            print(f"❌ 未知命令: {args.command}")
            parser.print_help()

    except KeyboardInterrupt:
        print("\n👋 操作已取消")
    except Exception as e:
        print(f"❌ 执行命令时出错: {e}")


if __name__ == "__main__":
    main()