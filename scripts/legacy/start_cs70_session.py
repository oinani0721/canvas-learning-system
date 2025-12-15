#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动CS70 Lecture1学习会话
"""

import sys
import os
import asyncio
import io
from datetime import datetime
from pathlib import Path

# 配置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def start_cs70_session():
    """启动CS70学习会话"""

    try:
        from learning_session_wrapper import LearningSessionWrapper

        # Canvas文件路径
        canvas_path = "笔记库/Canvas/CS70/CS70HW1/CS70 Lecture1.canvas"

        # 检查文件是否存在
        full_path = Path(canvas_path)
        if not full_path.exists():
            print(f"❌ Canvas文件不存在: {canvas_path}")
            return False

        print("=" * 70)
        print("🎓 Canvas学习会话启动中...")
        print("=" * 70)
        print(f"📚 课程: CS70 - 离散数学与概率论")
        print(f"📄 文件: {canvas_path}")
        print(f"👤 用户: default")
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()

        # 创建学习会话包装器
        wrapper = LearningSessionWrapper()

        print("🔄 正在启动记忆系统...")
        print("   - Graphiti知识图谱系统")
        print("   - 时序记忆管理器")
        print("   - 语义记忆管理器")
        print()

        # 启动会话（异步调用）
        result = await wrapper.start_session(
            canvas_path=canvas_path,
            user_id="default",
            session_name="CS70 Lecture1 - 离散数学基础"
        )

        if result and result.get('success'):
            print("=" * 70)
            print("✅ 学习会话启动成功！")
            print("=" * 70)
            print()
            print(f"📋 会话信息:")
            print(f"   Session ID: {result['session_id']}")
            print(f"   会话名称: {result['session_name']}")
            print(f"   Canvas: CS70 Lecture1")
            print()

            print("📊 记忆系统状态:")
            memory_systems = result.get('memory_systems', {})
            running_count = 0
            for system_name, system_info in memory_systems.items():
                if isinstance(system_info, dict):
                    status = system_info.get('status', 'unknown')
                    if status == 'running':
                        print(f"   ✅ {system_name}: 运行中")
                        running_count += 1
                    else:
                        print(f"   ⚠️  {system_name}: {status}")
                else:
                    enabled = system_info
                    if enabled:
                        print(f"   ✅ {system_name}: 已启用")
                        running_count += 1
                    else:
                        print(f"   ⚠️  {system_name}: 未启用")

            print()
            print(f"🎯 {running_count}/{len(memory_systems)} 记忆系统运行中")

            if running_count < len(memory_systems):
                print()
                print("⚠️  注意: 部分记忆系统未能启动，但学习可以继续")
                print("💡 提示: 至少时序记忆系统运行即可记录学习活动")

            print()
            print("=" * 70)
            print("🚀 开始学习！")
            print("=" * 70)
            print()
            print("📖 使用指南:")
            print("   1. 在Obsidian中打开Canvas文件")
            print(f"      文件路径: {canvas_path}")
            print()
            print("   2. 使用Canvas学习系统的12个AI Agent:")
            print("      - 基础拆解: 拆解难懂的概念")
            print("      - 深度拆解: 深入理解半懂的概念")
            print("      - 评分系统: 评估你的理解质量")
            print("      - 6种解释Agent: 多角度理解概念")
            print()
            print("   3. 所有学习活动会被自动记录:")
            print("      - Canvas文件修改")
            print("      - 节点颜色变更")
            print("      - Agent使用记录")
            print()
            print("   4. 查看会话状态:")
            print("      使用命令: /learning status")
            print()
            print("   5. 结束会话并生成报告:")
            print("      使用命令: /learning stop")
            print()
            print("=" * 70)
            print("💡 提示: Canvas监控系统也在运行中 (http://127.0.0.1:5678)")
            print("=" * 70)

            return True
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
            print()
            print("=" * 70)
            print("❌ 学习会话启动失败")
            print("=" * 70)
            print(f"错误信息: {error_msg}")
            print()
            print("💡 可能的解决方案:")
            print("   1. 检查Canvas文件是否存在且格式正确")
            print("   2. 检查Neo4j数据库是否运行 (Graphiti需要)")
            print("   3. 查看 .learning_sessions/latest_session_report.txt")
            print("   4. 即使部分系统失败，你仍可以直接使用Canvas学习系统")
            print("=" * 70)
            return False

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ 启动失败")
        print("=" * 70)
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("💡 建议: 直接使用Canvas学习系统，不依赖会话管理")
        print("=" * 70)
        return False

def main():
    """主函数"""
    try:
        success = asyncio.run(start_cs70_session())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
