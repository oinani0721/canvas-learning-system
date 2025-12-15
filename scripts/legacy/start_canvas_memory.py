#!/usr/bin/env python3
"""
Canvas学习记忆系统启动器
一键启动Canvas学习活动记录功能
"""

import os
import sys
import time
import signal
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from realtime_canvas_memory_integration import RealtimeCanvasMemoryIntegration
from learning_activity_capture import LearningActivityCapture
from privacy_manager import PrivacyManager

class CanvasMemorySystem:
    """Canvas学习记忆系统管理器"""

    def __init__(self):
        self.memory_system = None
        self.activity_capture = None
        self.privacy_manager = None
        self.running = False

    def start(self):
        """启动Canvas学习记忆系统"""
        try:
            print("🚀 Canvas学习记忆系统启动中...")
            print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 50)

            # 初始化核心组件
            self.memory_system = RealtimeCanvasMemoryIntegration()
            self.activity_capture = LearningActivityCapture()
            self.privacy_manager = PrivacyManager()

            # 启动活动捕获
            self.activity_capture.start_capture()

            self.running = True
            print("✅ Canvas学习记忆系统已启动")
            print("📊 正在监听Canvas学习活动...")
            print()
            print("🎯 使用说明:")
            print("  1. 打开任何Canvas文件开始学习")
            print("  2. 系统将自动记录您的学习行为")
            print("  3. 按 Ctrl+C 停止记录")
            print()
            print("📈 记录内容包括:")
            print("  • 节点点击和浏览行为")
            print("  • Agent调用记录")
            print("  • 理解输入过程")
            print("  • 评分结果")
            print("  • 学习时间统计")
            print()

            # 监听循环
            self._monitoring_loop()

        except Exception as e:
            print(f"❌ 启动失败: {e}")
            self.stop()

    def _monitoring_loop(self):
        """主监听循环"""
        last_status_time = time.time()

        try:
            while self.running:
                current_time = time.time()

                # 每30秒显示一次状态
                if current_time - last_status_time >= 30:
                    self._show_status()
                    last_status_time = current_time

                time.sleep(5)  # 每5秒检查一次

        except KeyboardInterrupt:
            print("\n🛑 收到停止信号...")
            self.stop()

    def _show_status(self):
        """显示系统状态"""
        try:
            # 获取活跃会话数
            active_sessions = self.memory_system.get_active_sessions()
            session_count = len(active_sessions)

            # 获取缓冲区状态
            buffer_status = self.activity_capture.get_buffer_status()
            buffer_size = buffer_status.get('buffer_size', 0)

            # 显示状态
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"📊 [{timestamp}] 活跃学习会话: {session_count} | 缓冲活动: {buffer_size}")

            # 如果有活跃会话，显示简短信息
            if active_sessions:
                for session in active_sessions[:3]:  # 最多显示3个
                    canvas_name = os.path.basename(session.get('canvas_path', 'Unknown'))
                    print(f"    📚 正在记录: {canvas_name}")

        except Exception as e:
            print(f"⚠️ 状态检查失败: {e}")

    def stop(self):
        """停止系统并保存数据"""
        if not self.running:
            return

        self.running = False

        try:
            print("💾 正在保存学习记录...")

            # 停止活动捕获
            if self.activity_capture:
                self.activity_capture.stop_capture()

            # 强制刷新缓冲区
            if self.activity_capture:
                self.activity_capture.flush_buffer()

            # 获取最终统计
            if self.memory_system:
                final_sessions = self.memory_system.get_active_sessions()
                print(f"✅ 已保存 {len(final_sessions)} 个学习会话")

            print("🎉 Canvas学习记忆系统已安全停止")
            print("📈 所有学习记录已保存到 data/realtime_memory/ 目录")

        except Exception as e:
            print(f"⚠️ 停止过程中出现警告: {e}")

        print("=" * 50)
        print(f"📅 停止时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def signal_handler(signum, frame):
    """信号处理器"""
    print("\n🛑 收到中断信号...")
    if 'system' in globals() and system:
        system.stop()
    sys.exit(0)

def main():
    """主函数"""
    print("🎯 Canvas学习记忆系统 - Story 8.17")
    print("📝 自动记录您的Canvas学习活动")
    print("🧠 智能分析您的学习模式")
    print("🔒 保护您的学习隐私")
    print()

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 创建并启动系统
    global system
    system = CanvasMemorySystem()

    try:
        system.start()
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        print("💡 请检查:")
        print("  1. Python环境是否正确")
        print("  2. 所有依赖库是否已安装")
        print("  3. 配置文件是否存在")

if __name__ == "__main__":
    main()