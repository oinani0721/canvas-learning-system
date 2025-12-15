#!/usr/bin/env python3
"""
Canvas学习系统 - 覆盖率分析器
Story 8.13: 提升测试覆盖率和系统稳定性

专门用于分析代码测试覆盖率的工具。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class CoverageAnalyzer:
    """覆盖率分析器"""

    def __init__(self, project_root: str = None):
        """初始化覆盖率分析器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.coverage_data = None

    def run_coverage_analysis(self, modules: List[str] = None) -> Dict:
        """运行覆盖率分析

        Args:
            modules: 要分析的模块列表

        Returns:
            Dict: 覆盖率分析结果
        """
        print("Running coverage analysis...")

        # 构建pytest命令
        cmd = [
            "python", "-m", "pytest",
            "--cov=.",
            "--cov-report=json",
            "--cov-report=term-missing",
            "--cov-report=html"
        ]

        if modules:
            cmd.extend(modules)

        try:
            # 运行覆盖率测试
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300  # 5分钟超时
            )

            # 读取覆盖率报告
            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, 'r', encoding='utf-8') as f:
                    self.coverage_data = json.load(f)

                analysis = self._analyze_coverage_data()
                return analysis
            else:
                return {
                    "error": "Coverage report not generated",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

        except subprocess.TimeoutExpired:
            return {
                "error": "Coverage analysis timed out",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "error": f"Coverage analysis failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def _analyze_coverage_data(self) -> Dict:
        """分析覆盖率数据"""
        if not self.coverage_data:
            return {"error": "No coverage data available"}

        totals = self.coverage_data.get("totals", {})

        overall_metrics = {
            "total_lines_covered": totals.get("covered_lines", 0),
            "total_lines_missing": totals.get("missing_lines", 0),
            "total_statements": totals.get("num_statements", 0),
            "coverage_percentage": round(totals.get("percent_covered", 0), 1),
            "branch_coverage_percentage": self._calculate_branch_coverage(totals)
        }

        # 分析各个文件的覆盖率
        file_analysis = self._analyze_file_coverage()

        # 识别高风险文件
        high_risk_files = self._identify_high_risk_files(file_analysis)

        # 生成覆盖率建议
        recommendations = self._generate_coverage_recommendations(file_analysis)

        return {
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_metrics": overall_metrics,
            "file_coverage_analysis": file_analysis,
            "high_risk_files": high_risk_files,
            "recommendations": recommendations,
            "coverage_summary": self._generate_coverage_summary(overall_metrics, file_analysis)
        }

    def _calculate_branch_coverage(self, totals: Dict) -> float:
        """计算分支覆盖率"""
        covered_branches = totals.get("covered_branches", 0)
        total_branches = totals.get("num_branches", 1)
        return round((covered_branches / total_branches) * 100, 1) if total_branches > 0 else 0.0

    def _analyze_file_coverage(self) -> List[Dict]:
        """分析文件覆盖率"""
        files_data = []
        files = self.coverage_data.get("files", {})

        for file_path, file_data in files.items():
            if file_path.endswith('.py'):
                summary = file_data.get("summary", {})
                lines = file_data.get("lines", {})

                file_info = {
                    "file_path": file_path,
                    "module_name": Path(file_path).stem,
                    "statements": summary.get("num_statements", 0),
                    "covered": summary.get("covered_lines", 0),
                    "missing": summary.get("missing_lines", 0),
                    "coverage_percentage": round(summary.get("percent_covered", 0), 1),
                    "uncovered_lines": self._get_uncovered_lines(lines),
                    "complexity_score": self._estimate_complexity(file_path, summary),
                    "test_priority": self._calculate_test_priority(summary)
                }

                files_data.append(file_info)

        # 按覆盖率排序
        files_data.sort(key=lambda x: x["coverage_percentage"])
        return files_data

    def _get_uncovered_lines(self, lines: Dict) -> List[int]:
        """获取未覆盖的行号"""
        uncovered = []
        for line_num, line_info in lines.items():
            if not line_info:  # False表示未覆盖
                uncovered.append(int(line_num))
        return sorted(uncovered)

    def _estimate_complexity(self, file_path: str, summary: Dict) -> str:
        """估算文件复杂度"""
        statements = summary.get("num_statements", 0)
        missing = summary.get("missing_lines", 0)

        if statements > 500:
            return "high"
        elif statements > 200 or missing > 50:
            return "medium"
        else:
            return "low"

    def _calculate_test_priority(self, summary: Dict) -> str:
        """计算测试优先级"""
        coverage = summary.get("percent_covered", 0)
        statements = summary.get("num_statements", 0)

        if coverage < 50 and statements > 50:
            return "critical"
        elif coverage < 70:
            return "high"
        elif coverage < 85:
            return "medium"
        else:
            return "low"

    def _identify_high_risk_files(self, file_analysis: List[Dict]) -> List[Dict]:
        """识别高风险文件"""
        high_risk = []

        for file_info in file_analysis:
            risk_factors = []

            # 低覆盖率
            if file_info["coverage_percentage"] < 50:
                risk_factors.append("low_coverage")

            # 高复杂度
            if file_info["complexity_score"] == "high":
                risk_factors.append("high_complexity")

            # 核心模块
            if any(keyword in file_info["file_path"].lower()
                   for keyword in ["canvas", "agent", "core"]):
                risk_factors.append("core_module")

            if risk_factors:
                high_risk.append({
                    **file_info,
                    "risk_factors": risk_factors,
                    "risk_level": len(risk_factors)
                })

        # 按风险等级排序
        high_risk.sort(key=lambda x: x["risk_level"], reverse=True)
        return high_risk

    def _generate_coverage_recommendations(self, file_analysis: List[Dict]) -> List[Dict]:
        """生成覆盖率改进建议"""
        recommendations = []

        # 优先处理低覆盖率的核心文件
        core_files = [f for f in file_analysis if "canvas" in f["file_path"].lower()]
        for file_info in core_files[:5]:  # 前5个最需要关注的文件
            if file_info["coverage_percentage"] < 85:
                recommendations.append({
                    "type": "increase_coverage",
                    "file": file_info["file_path"],
                    "current_coverage": file_info["coverage_percentage"],
                    "target_coverage": 85,
                    "uncovered_lines_count": len(file_info["uncovered_lines"]),
                    "priority": file_info["test_priority"],
                    "estimated_effort_hours": self._estimate_test_effort(file_info),
                    "suggested_tests": self._suggest_tests_for_file(file_info)
                })

        # 针对特定模式的建议
        total_files = len(file_analysis)
        low_coverage_files = len([f for f in file_analysis if f["coverage_percentage"] < 70])

        if low_coverage_files > total_files * 0.3:
            recommendations.append({
                "type": "overall_strategy",
                "description": f"超过30%的文件覆盖率低于70%，建议制定全面的测试覆盖计划",
                "affected_files": low_coverage_files,
                "priority": "high"
            })

        return recommendations

    def _estimate_test_effort(self, file_info: Dict) -> int:
        """估算测试工作量（小时）"""
        uncovered_lines = len(file_info["uncovered_lines"])
        complexity_multiplier = {
            "low": 1.0,
            "medium": 1.5,
            "high": 2.0
        }

        multiplier = complexity_multiplier.get(file_info["complexity_score"], 1.0)
        return max(1, int((uncovered_lines / 10) * multiplier))

    def _suggest_tests_for_file(self, file_info: Dict) -> List[str]:
        """为文件建议测试类型"""
        suggestions = []
        file_path = file_info["file_path"].lower()

        if "canvas" in file_path:
            suggestions.extend([
                "文件读写操作测试",
                "Canvas格式验证测试",
                "节点和边的操作测试"
            ])

        if "agent" in file_path:
            suggestions.extend([
                "Agent调用接口测试",
                "参数验证测试",
                "错误处理测试"
            ])

        if "error" in file_path or "logger" in file_path:
            suggestions.extend([
                "错误日志记录测试",
                "错误分类测试",
                "恢复建议生成测试"
            ])

        if not suggestions:
            suggestions = [
                "单元函数测试",
                "边界条件测试",
                "异常处理测试"
            ]

        return suggestions

    def _generate_coverage_summary(self, overall_metrics: Dict, file_analysis: List[Dict]) -> Dict:
        """生成覆盖率摘要"""
        total_files = len(file_analysis)
        files_above_80 = len([f for f in file_analysis if f["coverage_percentage"] >= 80])
        files_below_50 = len([f for f in file_analysis if f["coverage_percentage"] < 50])

        return {
            "total_files_analyzed": total_files,
            "files_with_adequate_coverage": files_above_80,
            "files_with_inadequate_coverage": total_files - files_above_80,
            "files_with_critical_coverage": files_below_50,
            "coverage_distribution": self._calculate_coverage_distribution(file_analysis),
            "quality_assessment": self._assess_coverage_quality(overall_metrics["coverage_percentage"])
        }

    def _calculate_coverage_distribution(self, file_analysis: List[Dict]) -> Dict:
        """计算覆盖率分布"""
        ranges = {
            "90-100%": 0,
            "80-89%": 0,
            "70-79%": 0,
            "50-69%": 0,
            "0-49%": 0
        }

        for file_info in file_analysis:
            coverage = file_info["coverage_percentage"]
            if coverage >= 90:
                ranges["90-100%"] += 1
            elif coverage >= 80:
                ranges["80-89%"] += 1
            elif coverage >= 70:
                ranges["70-79%"] += 1
            elif coverage >= 50:
                ranges["50-69%"] += 1
            else:
                ranges["0-49%"] += 1

        return ranges

    def _assess_coverage_quality(self, overall_coverage: float) -> str:
        """评估覆盖率质量"""
        if overall_coverage >= 90:
            return "excellent"
        elif overall_coverage >= 80:
            return "good"
        elif overall_coverage >= 70:
            return "acceptable"
        elif overall_coverage >= 50:
            return "needs_improvement"
        else:
            return "poor"

    def generate_coverage_report(self, output_format: str = "markdown") -> str:
        """生成覆盖率报告

        Args:
            output_format: 输出格式 ("markdown", "html", "json")

        Returns:
            str: 报告内容
        """
        if not self.coverage_data:
            return "No coverage data available. Run run_coverage_analysis() first."

        analysis = self._analyze_coverage_data()

        if output_format == "json":
            return json.dumps(analysis, indent=2, ensure_ascii=False)
        elif output_format == "html":
            return self._generate_html_report(analysis)
        else:
            return self._generate_markdown_report(analysis)

    def _generate_markdown_report(self, analysis: Dict) -> str:
        """生成Markdown格式的覆盖率报告"""
        timestamp = analysis["analysis_timestamp"]
        overall = analysis["overall_metrics"]
        summary = analysis["coverage_summary"]
        high_risk = analysis["high_risk_files"]
        recommendations = analysis["recommendations"]

        markdown = f"""# 代码覆盖率分析报告

**生成时间**: {timestamp}
**分析工具**: pytest-cov

## 📊 覆盖率概览

### 整体指标
- **总覆盖率**: {overall['coverage_percentage']}%
- **行覆盖**: {overall['total_lines_covered']}/{overall['total_statements']}
- **分支覆盖率**: {overall['branch_coverage_percentage']}%

### 文件统计
- **分析文件数**: {summary['total_files_analyzed']}
- **覆盖率≥80%**: {summary['files_with_adequate_coverage']} 个文件
- **覆盖率<50%**: {summary['files_with_critical_coverage']} 个文件
- **质量评估**: {summary['quality_assessment']}

### 覆盖率分布
"""

        # 添加分布表格
        distribution = summary['coverage_distribution']
        markdown += "| 覆盖率范围 | 文件数量 |\n|-----------|----------|\n"
        for range_name, count in distribution.items():
            markdown += f"| {range_name} | {count} |\n"

        # 添加高风险文件
        if high_risk:
            markdown += f"""
## 🚨 高风险文件

以下文件需要优先关注：

"""
            for file_info in high_risk[:10]:  # 只显示前10个
                markdown += f"""### {file_info['module_name']}
- **文件路径**: {file_info['file_path']}
- **覆盖率**: {file_info['coverage_percentage']}%
- **未覆盖行数**: {len(file_info['uncovered_lines'])}
- **风险因素**: {', '.join(file_info['risk_factors'])}
- **测试优先级**: {file_info['test_priority']}

"""

        # 添加改进建议
        if recommendations:
            markdown += "## 💡 改进建议\n\n"
            for i, rec in enumerate(recommendations[:5], 1):  # 只显示前5个建议
                markdown += f"### {i}. {rec.get('type', '建议').title()}\n"
                if rec.get('file'):
                    markdown += f"- **文件**: {rec['file']}\n"
                if rec.get('current_coverage') is not None:
                    markdown += f"- **当前覆盖率**: {rec['current_coverage']}%\n"
                if rec.get('target_coverage') is not None:
                    markdown += f"- **目标覆盖率**: {rec['target_coverage']}%\n"
                if rec.get('estimated_effort_hours'):
                    markdown += f"- **预计工作量**: {rec['estimated_effort_hours']} 小时\n"
                if rec.get('description'):
                    markdown += f"- **说明**: {rec['description']}\n"
                if rec.get('suggested_tests'):
                    markdown += f"- **建议测试**: {', '.join(rec['suggested_tests'])}\n"
                markdown += "\n"

        markdown += """
---
*此报告由覆盖率分析器自动生成*
"""
        return markdown

    def _generate_html_report(self, analysis: Dict) -> str:
        """生成HTML格式的覆盖率报告"""
        # 简化的HTML报告生成
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>代码覆盖率报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .metric {{ background: #f5f5f5; padding: 10px; margin: 5px 0; border-radius: 5px; }}
        .high-risk {{ background: #ffebee; }}
        .good {{ background: #e8f5e8; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>代码覆盖率分析报告</h1>
    <p><strong>生成时间:</strong> {analysis['analysis_timestamp']}</p>

    <h2>整体指标</h2>
    <div class="metric">
        <strong>总覆盖率:</strong> {analysis['overall_metrics']['coverage_percentage']}%
    </div>
    <div class="metric">
        <strong>分支覆盖率:</strong> {analysis['overall_metrics']['branch_coverage_percentage']}%
    </div>

    <h2>质量评估</h2>
    <div class="metric {'good' if analysis['coverage_summary']['quality_assessment'] == 'excellent' else ''}">
        <strong>质量等级:</strong> {analysis['coverage_summary']['quality_assessment']}
    </div>

</body>
</html>
"""
        return html


if __name__ == "__main__":
    # 示例使用
    analyzer = CoverageAnalyzer()

    print("运行覆盖率分析...")
    result = analyzer.run_coverage_analysis()

    if "error" in result:
        print(f"分析失败: {result['error']}")
    else:
        print("分析完成!")
        print(f"总覆盖率: {result['overall_metrics']['coverage_percentage']}%")

        # 生成报告
        report = analyzer.generate_coverage_report("markdown")
        with open("coverage_report.md", "w", encoding="utf-8") as f:
            f.write(report)
        print("报告已保存到 coverage_report.md")