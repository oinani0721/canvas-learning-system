#!/usr/bin/env python3
"""
Canvas监控系统演示启动器

演示如何使用带监控的Canvas学习系统
包含简单的启动脚本和状态检查功能

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-25
"""

import os
import sys
import time
import signal
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_banner():
    """打印启动横幅"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                Canvas学习系统 - 监控演示启动器                    ║
║                                                              ║
║  🚀 启动模式: Canvas学习系统 + 智能监控系统                      ║
║  📊 功能: 实时学习追踪 + 个性化分析报告                         ║
║  🎯 目标: 提供完整的智能化学习体验                              ║
║                                                              ║
║  使用方法:                                                    ║
║  1. 保持此窗口开启 (监控系统运行中)                            ║
║  2. 在Claude Code中使用 /canvas --with-monitoring             ║
║  3. 开始你的Canvas学习之旅                                   ║
║                                                              ║
║  按 Ctrl+C 安全停止监控系统                                   ║
╚══════════════════════════════════════════════════════════════╝
    """)

def check_system_requirements():
    """检查系统要求"""
    print("🔍 检查系统要求...")

    # 检查Python版本
    python_version = sys.version_info
    if python_version >= (3, 9):
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python版本过低: {python_version.major}.{python_version.minor}")
        print("需要Python 3.9或更高版本")
        return False

    # 检查依赖
    required_modules = [
        'watchdog',
        'psutil',
        'yaml',
        'pathlib'
    ]

    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} 已安装")
        except ImportError:
            print(f"❌ {module} 未安装")
            missing_modules.append(module)

    if missing_modules:
        print(f"\n请安装缺失的依赖:")
        print(f"pip install {' '.join(missing_modules)}")
        return False

    # 检查目录结构
    required_dirs = [
        'canvas_progress_tracker',
        '笔记库',
        '.claude'
    ]

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✅ 目录存在: {dir_name}")
        else:
            print(f"⚠️ 目录不存在: {dir_name}")

    return True

def start_monitoring_system():
    """启动监控系统"""
    print("\n🚀 正在启动Canvas监控系统...")

    try:
        # 尝试导入监控系统
        from canvas_progress_tracker import CanvasMonitorSystem

        # 创建监控系统实例
        monitor = CanvasMonitorSystem(auto_init=True)

        # 启动监控
        success = monitor.start_monitoring()

        if success:
            print("✅ Canvas监控系统启动成功!")
            print("\n📊 监控系统状态:")
            print("  🟢 状态: 运行中")
            print("  📁 监控路径: ./笔记库")
            print("  📈 监控文件: 所有 *.canvas 文件")
            print("  ⚡ 性能模式: 自适应优化")
            print("  💾 数据存储: 本地加密存储")

            return monitor
        else:
            print("❌ 监控系统启动失败")
            return None

    except ImportError as e:
        print(f"❌ 导入监控系统失败: {e}")
        print("请确保已正确安装所有依赖:")
        print("pip install -r requirements.txt")
        return None
    except Exception as e:
        print(f"❌ 启动监控系统时发生错误: {e}")
        return None

def show_usage_tips():
    """显示使用提示"""
    print("""
🎯 使用提示:

在Claude Code中使用以下命令开始学习:

1. 启动带监控的Canvas系统:
   /canvas --with-monitoring

2. 正常使用Canvas学习功能:
   帮我基础拆解 @笔记库/数学/高数.canvas 中的"极限"
   帮我评分 @笔记库/数学/高数.canvas 所有黄色节点

3. 查看监控状态:
   /monitoring-status

4. 生成学习报告:
   /learning-report

5. 停止监控:
   /stop-monitoring

💡 提示: 所有Canvas操作都会被自动监控和记录
    """)

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n\n📡 接收到停止信号 {signum}")
    print("🛑 正在安全停止Canvas监控系统...")
    print("💾 学习数据已保存")
    print("👋 感谢使用Canvas学习系统!")
    sys.exit(0)

def main():
    """主函数"""
    print_banner()

    # 检查系统要求
    if not check_system_requirements():
        print("\n❌ 系统要求检查失败，请解决问题后重试")
        return

    # 显示使用提示
    show_usage_tips()

    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动监控系统
    monitor = start_monitoring_system()

    if monitor:
        print(f"\n{'='*60}")
        print("🎉 Canvas监控系统已成功启动!")
        print("📚 现在你可以在Claude Code中使用 /canvas --with-monitoring")
        print("🔄 监控系统将在后台持续运行")
        print(f"{'='*60}")
        print("\n按 Ctrl+C 停止监控系统")

        try:
            # 保持运行
            while True:
                time.sleep(10)

                # 可选：定期显示状态
                # status = monitor.get_system_status()
                # print(f"\r⏰ 运行时间: {status['uptime_seconds']:.0f}秒", end="")

        except KeyboardInterrupt:
            print("\n🛑 用户中断，正在停止监控...")
            if monitor:
                monitor.shutdown_system()
            print("✅ 监控系统已安全停止")
    else:
        print("\n❌ 监控系统启动失败")
        print("请检查错误信息并解决问题")

if __name__ == "__main__":
    main()