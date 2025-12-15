#!/usr/bin/env python3
"""
启动Canvas学习进度仪表板

这个脚本将启动Web服务器并打开浏览器显示仪表板界面。

使用方法:
    python start_dashboard.py

或者直接运行:
    python dashboard_api_server.py

Author: Canvas Learning System Team
Version: 1.0
"""

import asyncio
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    print("检查依赖...")

    required_packages = ['flask', 'flask-cors']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package}")

    if missing_packages:
        print(f"\n缺少依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    print("✅ 所有依赖都已安装\n")
    return True

def start_server():
    """启动API服务器"""
    try:
        print("启动API服务器...")
        # 使用subprocess启动服务器，避免阻塞当前进程
        process = subprocess.Popen([
            sys.executable, "dashboard_api_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 等待服务器启动
        time.sleep(3)

        # 检查服务器是否正常运行
        if process.poll() is None:
            print("✅ API服务器启动成功")
            return process
        else:
            print("❌ API服务器启动失败")
            return None

    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")
        return None

def open_browser():
    """打开浏览器"""
    try:
        print("正在打开浏览器...")
        webbrowser.open('http://localhost:5000')
        print("✅ 浏览器已打开")
    except Exception as e:
        print(f"❌ 无法打开浏览器: {e}")
        print("请手动访问: http://localhost:5000")

def main():
    """主函数"""
    print("=" * 60)
    print("Canvas学习进度仪表板启动器")
    print("=" * 60)

    # 检查文件是否存在
    api_file = Path("dashboard_api_server.py")
    html_file = Path("learning_progress_dashboard.html")

    if not api_file.exists():
        print("❌ 找不到 dashboard_api_server.py 文件")
        return

    if not html_file.exists():
        print("❌ 找不到 learning_progress_dashboard.html 文件")
        return

    # 检查依赖
    if not check_dependencies():
        return

    # 启动服务器
    server_process = start_server()
    if not server_process:
        return

    # 打开浏览器
    open_browser()

    print("\n" + "=" * 60)
    print("📊 Canvas学习进度仪表板")
    print("=" * 60)
    print("服务器运行在: http://localhost:5000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)

    try:
        # 等待用户中断
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        server_process.terminate()
        server_process.wait()
        print("✅ 服务器已停止")

if __name__ == '__main__':
    main()