#!/usr/bin/env python3
"""检查当前学习会话状态"""
import json
import os
from pathlib import Path
from datetime import datetime

def check_session_status():
    """检查学习会话状态"""
    session_dir = Path(".learning_sessions")
    
    if not session_dir.exists():
        print("❌ 没有找到学习会话目录")
        return
    
    # 获取最新的会话文件
    session_files = list(session_dir.glob("session_*.json"))
    if not session_files:
        print("❌ 没有找到学习会话文件")
        return
    
    latest_session = max(session_files, key=lambda p: p.stat().st_mtime)
    
    print("=" * 60)
    print("📊 最新学习会话状态")
    print("=" * 60)
    
    try:
        with open(latest_session, 'r', encoding='utf-8') as f:
            # 只读取前1000个字符
            content = f.read(5000)
            session = json.loads(content)
        
        print(f"📁 会话文件: {latest_session.name}")
        print(f"🆔 会话ID: {session.get('session_id', 'N/A')}")
        print(f"👤 用户ID: {session.get('user_id', 'N/A')}")
        print(f"📚 会话名称: {session.get('session_name', 'N/A')}")
        print(f"📍 Canvas路径: {session.get('canvas_path', 'N/A')}")
        print(f"⏰ 开始时间: {session.get('start_time', 'N/A')}")
        
        print("\n📊 记忆系统状态:")
        memory_systems = session.get('memory_systems', {})
        for system_name, system_info in memory_systems.items():
            if isinstance(system_info, dict):
                status = system_info.get('status', 'unknown')
                emoji = "✅" if status == "running" else "⚠️"
                print(f"  {emoji} {system_name}: {status}")
            else:
                print(f"  ⚠️ {system_name}: {system_info}")
        
        print("\n" + "=" * 60)
        
        # 检查文件大小
        file_size = latest_session.stat().st_size
        print(f"📦 文件大小: {file_size / 1024:.1f} KB")
        
        # 检查修改时间
        mtime = datetime.fromtimestamp(latest_session.stat().st_mtime)
        print(f"🕐 最后修改: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON解析错误: {e}")
        print("文件可能太大或格式不正确")
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    check_session_status()
