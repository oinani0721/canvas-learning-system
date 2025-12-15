#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canvas学习系统v2.0 - 系统状态检查脚本

该脚本会全面检查v2.0所有功能的实现状态、依赖配置和可用性。
运行此脚本可以快速诊断系统问题并获取修复建议。

使用方法:
    python system_status_check.py

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-10-20
"""

import sys
import json
import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# ANSI颜色代码
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(title: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_section(title: str):
    """打印章节标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}[Section] {title}{Colors.END}")
    print(f"{Colors.CYAN}{'-'*50}{Colors.END}")

def check_result(status: bool, name: str, details: str = "") -> None:
    """打印检查结果"""
    if status:
        print(f"  {Colors.GREEN}[OK] {name}{Colors.END}")
        if details:
            print(f"     {Colors.WHITE}{details}{Colors.END}")
    else:
        print(f"  {Colors.RED}[FAIL] {name}{Colors.END}")
        if details:
            print(f"     {Colors.YELLOW}{details}{Colors.END}")

def warning_result(name: str, details: str = "") -> None:
    """打印警告结果"""
    print(f"  {Colors.YELLOW}[WARN] {name}{Colors.END}")
    if details:
        print(f"     {Colors.WHITE}{details}{Colors.END}")

def info_result(name: str, details: str = "") -> None:
    """打印信息结果"""
    print(f"  {Colors.BLUE}[INFO] {name}{Colors.END}")
    if details:
        print(f"     {Colors.WHITE}{details}{Colors.END}")

class SystemStatusChecker:
    """系统状态检查器"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "working_directory": str(Path.cwd()),
            "checks": {}
        }

    def check_python_environment(self) -> Dict[str, Any]:
        """检查Python环境"""
        print_section("Python环境检查")

        checks = {}

        # Python版本
        version_ok = sys.version_info >= (3, 8)
        checks["python_version"] = version_ok
        check_result(
            version_ok,
            f"Python版本 {sys.version.split()[0]}",
            "推荐3.8+" if version_ok else "需要Python 3.8+"
        )

        # 工作目录
        current_dir = Path.cwd()
        canvas_utils_exists = (current_dir / "canvas_utils.py").exists()
        checks["canvas_utils_exists"] = canvas_utils_exists
        check_result(
            canvas_utils_exists,
            "canvas_utils.py存在",
            f"路径: {current_dir}"
        )

        # 目录结构
        required_dirs = ["笔记库", ".claude", "docs"]
        for dir_name in required_dirs:
            dir_path = current_dir / dir_name
            exists = dir_path.exists()
            checks[f"dir_{dir_name}"] = exists
            check_result(
                exists,
                f"目录 {dir_name}/",
                f"路径: {dir_path}" if exists else f"需要创建: {dir_path}"
            )

        self.results["checks"]["python_environment"] = checks
        return checks

    def check_dependencies(self) -> Dict[str, Any]:
        """检查依赖包"""
        print_section("依赖包检查")

        # 核心依赖
        core_deps = {
            "numpy": {"required": True, "version": "1.20+"},
            "pandas": {"required": True, "version": "1.3+"},
        }

        # v2.0增强依赖
        v2_deps = {
            "loguru": {"required": False, "version": "0.6+", "purpose": "企业级日志"},
            "matplotlib": {"required": False, "version": "3.5+", "purpose": "数据可视化"},
            "seaborn": {"required": False, "version": "0.11+", "purpose": "统计可视化"},
            "graphiti_core": {"required": False, "version": "0.1+", "purpose": "知识图谱"},
            "aiomultiprocess": {"required": False, "version": "0.9+", "purpose": "并发处理"},
        }

        checks = {}

        print(f"\n{Colors.BOLD}核心依赖:{Colors.END}")
        for dep_name, info in core_deps.items():
            try:
                module = importlib.import_module(dep_name)
                version = getattr(module, '__version__', 'unknown')
                checks[f"dep_{dep_name}"] = True
                check_result(
                    True,
                    f"{dep_name} ({version})",
                    f"必需依赖"
                )
            except ImportError:
                checks[f"dep_{dep_name}"] = False
                check_result(
                    False,
                    f"{dep_name}",
                    f"必需依赖，运行: pip install {dep_name}"
                )

        print(f"\n{Colors.BOLD}v2.0增强依赖:{Colors.END}")
        for dep_name, info in v2_deps.items():
            try:
                module = importlib.import_module(dep_name)
                version = getattr(module, '__version__', 'unknown')
                checks[f"dep_{dep_name}"] = True
                check_result(
                    True,
                    f"{dep_name} ({version})",
                    f"v2.0功能: {info['purpose']}"
                )
            except ImportError:
                checks[f"dep_{dep_name}"] = False
                if info["required"]:
                    check_result(
                        False,
                        f"{dep_name}",
                        f"必需: pip install {dep_name}"
                    )
                else:
                    warning_result(
                        f"{dep_name} (未安装)",
                        f"可选功能 {info['purpose']}: pip install {dep_name}"
                    )

        self.results["checks"]["dependencies"] = checks
        return checks

    def check_canvas_implementation(self) -> Dict[str, Any]:
        """检查Canvas实现"""
        print_section("Canvas实现检查")

        checks = {}

        try:
            # 尝试导入canvas_utils
            sys.path.insert(0, str(Path.cwd()))
            import canvas_utils

            checks["canvas_utils_import"] = True
            check_result(True, "canvas_utils.py可导入")

            # 检查v2.0核心类
            v2_classes = {
                "UltraThinkCanvasIntegration": "UltraThink智能分析",
                "CanvasKnowledgeGraph": "Graphiti知识图谱",
                "ConcurrentAgentProcessor": "并发Agent处理",
                "LearningAnalyticsDashboard": "学习分析仪表板",
                "PerformanceOptimizer": "性能优化器",
                "GlobalFeatureControls": "全局功能控制",
            }

            print(f"\n{Colors.BOLD}v2.0核心类检查:{Colors.END}")
            for class_name, description in v2_classes.items():
                if hasattr(canvas_utils, class_name):
                    checks[f"class_{class_name}"] = True
                    check_result(
                        True,
                        f"{class_name}",
                        description
                    )
                else:
                    checks[f"class_{class_name}"] = False
                    check_result(
                        False,
                        f"{class_name}",
                        f"v2.0功能缺失: {description}"
                    )

            # 检查全局实例
            global_instances = {
                "ultrathink_canvas_integration": "UltraThink集成实例",
                "canvas_knowledge_graph": "知识图谱实例",
                "concurrent_agent_processor": "并发处理器实例",
                "analytics_dashboard": "分析仪表板实例",
                "performance_optimizer": "性能优化器实例",
                "global_controls": "全局控制器实例",
            }

            print(f"\n{Colors.BOLD}全局实例检查:{Colors.END}")
            for instance_name, description in global_instances.items():
                if hasattr(canvas_utils, instance_name):
                    checks[f"instance_{instance_name}"] = True
                    check_result(
                        True,
                        f"{instance_name}",
                        description
                    )
                else:
                    checks[f"instance_{instance_name}"] = False
                    check_result(
                        False,
                        f"{instance_name}",
                        f"全局实例缺失: {description}"
                    )

        except ImportError as e:
            checks["canvas_utils_import"] = False
            check_result(
                False,
                "canvas_utils.py导入失败",
                f"错误: {str(e)}"
            )

        self.results["checks"]["canvas_implementation"] = checks
        return checks

    def check_file_structure(self) -> Dict[str, Any]:
        """检查文件结构"""
        print_section("文件结构检查")

        checks = {}

        current_dir = Path.cwd()

        # 必需文件
        required_files = [
            "canvas_utils.py",
            "CLAUDE.md",
            "CANVAS_ERROR_LOG.md",
            "requirements.txt",
        ]

        for file_name in required_files:
            file_path = current_dir / file_name
            exists = file_path.exists()
            checks[f"file_{file_name}"] = exists
            check_result(
                exists,
                f"{file_name}",
                f"大小: {file_path.stat().st_size} bytes" if exists else "文件缺失"
            )

        # 重要目录内容
        important_dirs = {
            ".claude": ["agents", "commands"],
            "docs": ["project-brief.md"],
            "tests": ["test_canvas_utils.py"],
        }

        print(f"\n{Colors.BOLD}重要目录内容:{Colors.END}")
        for dir_name, sub_items in important_dirs.items():
            dir_path = current_dir / dir_name
            if dir_path.exists():
                for sub_item in sub_items:
                    item_path = dir_path / sub_item
                    exists = item_path.exists()
                    checks[f"file_{dir_name}_{sub_item.replace('.', '_')}"] = exists
                    check_result(
                        exists,
                        f"{dir_name}/{sub_item}",
                        "存在" if exists else "建议创建"
                    )
            else:
                warning_result(f"目录 {dir_name}/", "不存在")

        self.results["checks"]["file_structure"] = checks
        return checks

    def check_permissions_config(self) -> Dict[str, Any]:
        """检查权限配置"""
        print_section("Claude Code权限配置检查")

        checks = {}

        settings_file = Path.cwd() / ".claude" / "settings.local.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                checks["settings_file_exists"] = True
                check_result(True, "settings.local.json存在")

                # 检查权限配置
                if "permissions" in settings:
                    permissions = settings["permissions"]
                    if "allow" in permissions:
                        allowed_list = permissions["allow"]

                        # 检查关键权限
                        key_permissions = {
                            "Bash(python:*)": "Python执行",
                            "Read(//c/**)": "文件读取",
                            "mcp__graphiti-memory__": "Graphiti记忆",
                            "mcp__context7-mcp__": "Context7集成",
                        }

                        print(f"\n{Colors.BOLD}关键权限检查:{Colors.END}")
                        for permission, description in key_permissions.items():
                            has_permission = any(permission in allowed_item for allowed_item in allowed_list)
                            checks[f"permission_{permission.replace('(', '_').replace(')', '_').replace('*', 'star')}"] = has_permission
                            check_result(
                                has_permission,
                                f"{permission}",
                                description
                            )

                checks["settings_file_valid"] = True

            except (json.JSONDecodeError, Exception) as e:
                checks["settings_file_valid"] = False
                check_result(
                    False,
                    "settings.local.json解析失败",
                    f"错误: {str(e)}"
                )
        else:
            checks["settings_file_exists"] = False
            check_result(
                False,
                "settings.local.json不存在",
                "需要配置Claude Code权限"
            )

        self.results["checks"]["permissions_config"] = checks
        return checks

    def check_functionality_status(self) -> Dict[str, Any]:
        """检查功能状态"""
        print_section("v2.0功能状态检查")

        checks = {}

        try:
            import canvas_utils
            global_controls = canvas_utils.global_controls

            print(f"\n{Colors.BOLD}功能控制器状态:{Colors.END}")

            # 检查每个功能的初始状态
            features = {
                "ultrathink": "UltraThink智能分析",
                "ebbinghaus_review": "艾宾浩斯复习",
                "concurrent_agents": "并发Agent处理",
                "knowledge_graph": "Graphiti知识图谱",
                "error_monitoring": "错误监控",
                "smart_clipboard": "智能剪贴板",
            }

            for feature, description in features.items():
                try:
                    status = global_controls.is_enabled(feature)
                    checks[f"feature_{feature}"] = {
                        "available": True,
                        "enabled": status
                    }

                    if status:
                        info_result(f"{feature}", f"{description} - 已启用")
                    else:
                        info_result(f"{feature}", f"{description} - 可用，使用*关键词激活")

                except Exception as e:
                    checks[f"feature_{feature}"] = {
                        "available": False,
                        "error": str(e)
                    }
                    check_result(
                        False,
                        f"{feature}",
                        f"功能检查失败: {str(e)}"
                    )

            # 测试功能激活
            print(f"\n{Colors.BOLD}功能激活测试:{Colors.END}")
            test_activation = global_controls.activate_feature("*ultrathink")
            if test_activation.get("success"):
                check_result(
                    True,
                    "功能激活机制",
                    "*关键词激活正常工作"
                )
            else:
                check_result(
                    False,
                    "功能激活机制",
                    f"激活失败: {test_activation.get('message', '未知错误')}"
                )

        except Exception as e:
            check_result(
                False,
                "功能状态检查",
                f"无法访问功能控制器: {str(e)}"
            )

        self.results["checks"]["functionality_status"] = checks
        return checks

    def generate_report(self) -> str:
        """生成检查报告"""
        print_section("生成检查报告")

        # 计算总体状态
        total_checks = 0
        passed_checks = 0

        for category, checks in self.results["checks"].items():
            for check_name, check_result in checks.items():
                if isinstance(check_result, bool):
                    total_checks += 1
                    if check_result:
                        passed_checks += 1
                elif isinstance(check_result, dict) and "available" in check_result:
                    total_checks += 1
                    if check_result.get("available", False):
                        passed_checks += 1

        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0

        # 保存报告
        report_file = Path.cwd() / f"system_status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n{Colors.BOLD}[Summary] 检查总结:{Colors.END}")
        print(f"  总检查项: {total_checks}")
        print(f"  通过项目: {passed_checks}")
        print(f"  成功率: {success_rate:.1f}%")
        print(f"  报告文件: {report_file}")

        # 状态评估
        if success_rate >= 90:
            print(f"\n{Colors.GREEN}[SUCCESS] 系统状态优秀！Canvas学习系统v2.0已就绪。{Colors.END}")
        elif success_rate >= 75:
            print(f"\n{Colors.YELLOW}[GOOD] 系统状态良好，建议优化部分配置。{Colors.END}")
        else:
            print(f"\n{Colors.RED}[NEEDS_CONFIG] 系统需要配置，请参考上述检查结果进行修复。{Colors.END}")

        return str(report_file)

def main():
    """主函数"""
    print_header("Canvas学习系统v2.0 - 系统状态检查")

    print(f"{Colors.CYAN}检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    print(f"{Colors.CYAN}工作目录: {Path.cwd()}{Colors.END}")

    checker = SystemStatusChecker()

    # 执行各项检查
    checker.check_python_environment()
    checker.check_dependencies()
    checker.check_canvas_implementation()
    checker.check_file_structure()
    checker.check_permissions_config()
    checker.check_functionality_status()

    # 生成报告
    report_file = checker.generate_report()

    print(f"\n{Colors.BOLD}{Colors.GREEN}[COMPLETE] 系统状态检查完成！{Colors.END}")
    print(f"{Colors.WHITE}详细报告已保存至: {report_file}{Colors.END}")

    # 下一步建议
    print_section("下一步建议")

    if Path(report_file).exists():
        print(f"{Colors.WHITE}1. 查看详细报告: {report_file}{Colors.END}")
        print(f"{Colors.WHITE}2. 根据检查结果修复问题{Colors.END}")
        print(f"{Colors.WHITE}3. 运行一键启用脚本: python enable_v2_features.py{Colors.END}")
        print(f"{Colors.WHITE}4. 阅读完整使用指南: CANVAS_V2_完整使用指南.md{Colors.END}")
    else:
        print(f"{Colors.YELLOW}[ERROR] 报告生成失败，请检查权限设置{Colors.END}")

if __name__ == "__main__":
    main()