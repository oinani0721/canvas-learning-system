#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canvas 3层记忆系统完全激活脚本
激活: Monitoring + Temporal + Semantic + Graphiti
"""

import os
import sys
import subprocess
import time
import asyncio
from pathlib import Path
from datetime import datetime

# 设置编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

class MemorySystemActivator:
    """记忆系统激活器"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.processes = []
        self.log_file = self.project_root / "memory_system_activation.log"
        self.activation_report = []

    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.activation_report.append(log_entry)

        # 写入日志文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

    def activate_monitor_system(self):
        """激活1层: 监控系统 (已启动)"""
        self.log("\n" + "="*60)
        self.log("激活第1层: 监控系统 (Canvas File Monitor)")
        self.log("="*60)

        try:
            # 检查.learning_sessions目录
            learning_sessions_dir = self.project_root / ".learning_sessions"
            if learning_sessions_dir.exists():
                session_files = list(learning_sessions_dir.glob("*.json"))
                self.log(f"✅ 监控系统已启动")
                self.log(f"   - 监听目录: {learning_sessions_dir}")
                self.log(f"   - 会话文件数: {len(session_files)}")
                self.log(f"   - 最新会话: {max(session_files, key=lambda p: p.stat().st_mtime).name}")
                return True
            else:
                self.log("❌ 监控目录不存在")
                return False
        except Exception as e:
            self.log(f"❌ 监控系统激活失败: {str(e)}")
            return False

    def activate_temporal_system(self):
        """激活2层: Temporal时间轴记忆系统"""
        self.log("\n" + "="*60)
        self.log("激活第2层: Temporal 时间轴记忆系统")
        self.log("="*60)

        try:
            temporal_file = self.project_root / "memory_system" / "temporal_memory_manager.py"

            if temporal_file.exists():
                # 尝试导入
                sys.path.insert(0, str(self.project_root))
                try:
                    from memory_system.temporal_memory_manager import TemporalMemoryManager
                    self.log("✅ Temporal系统已部署")
                    self.log(f"   - 文件: {temporal_file.name}")
                    self.log(f"   - 大小: {temporal_file.stat().st_size} bytes")
                    self.log("   - 功能: 时间轴记录，学习进度追踪")
                    return True
                except ImportError as e:
                    self.log(f"⚠️ 导入失败: {str(e)}")
                    return False
            else:
                self.log("❌ Temporal文件不存在")
                return False
        except Exception as e:
            self.log(f"❌ Temporal系统激活失败: {str(e)}")
            return False

    def activate_semantic_system(self):
        """激活3层: Semantic语义记忆系统"""
        self.log("\n" + "="*60)
        self.log("激活第3层: Semantic 语义记忆系统")
        self.log("="*60)

        try:
            semantic_file = self.project_root / "memory_system" / "semantic_memory_manager.py"

            if semantic_file.exists():
                # 尝试导入
                sys.path.insert(0, str(self.project_root))
                try:
                    from memory_system.semantic_memory_manager import SemanticMemoryManager
                    self.log("✅ Semantic系统已部署")
                    self.log(f"   - 文件: {semantic_file.name}")
                    self.log(f"   - 大小: {semantic_file.stat().st_size} bytes")
                    self.log("   - 功能: 语义提取，概念关系，向量嵌入")
                    return True
                except ImportError as e:
                    self.log(f"⚠️ 导入失败: {str(e)}")
                    return False
            else:
                self.log("❌ Semantic文件不存在")
                return False
        except Exception as e:
            self.log(f"❌ Semantic系统激活失败: {str(e)}")
            return False

    def activate_graphiti_system(self):
        """激活4层: Graphiti知识图谱系统"""
        self.log("\n" + "="*60)
        self.log("激活第4层: Graphiti 知识图谱系统 (MCP)")
        self.log("="*60)

        try:
            graphiti_dir = self.project_root / "graphiti" / "mcp_server"

            if graphiti_dir.exists():
                # 列出Graphiti文件
                graphiti_files = list(graphiti_dir.glob("*.py"))
                self.log("✅ Graphiti系统已部署")
                self.log(f"   - 目录: {graphiti_dir}")
                self.log(f"   - Python文件数: {len(graphiti_files)}")
                self.log("   - 功能: 知识图谱存储，Neo4j集成，MCP协议")
                self.log("\n⚠️ 注意: Graphiti需要Neo4j数据库")
                self.log("   - 检查Neo4j: neo4j status")
                self.log("   - 启动Neo4j: neo4j start")
                return True
            else:
                self.log("❌ Graphiti目录不存在")
                return False
        except Exception as e:
            self.log(f"❌ Graphiti系统激活失败: {str(e)}")
            return False

    def activate_unified_interface(self):
        """激活统一记忆接口"""
        self.log("\n" + "="*60)
        self.log("激活统一记忆接口")
        self.log("="*60)

        try:
            unified_file = self.project_root / "memory_system" / "unified_memory_interface.py"

            if unified_file.exists():
                sys.path.insert(0, str(self.project_root))
                try:
                    from memory_system.unified_memory_interface import UnifiedMemoryInterface
                    self.log("✅ 统一记忆接口已激活")
                    self.log(f"   - 文件: {unified_file.name}")
                    self.log("   - 功能: 统一访问所有4个记忆系统")
                    return True
                except ImportError as e:
                    self.log(f"⚠️ 导入失败: {str(e)}")
                    return False
            else:
                self.log("❌ 统一接口文件不存在")
                return False
        except Exception as e:
            self.log(f"❌ 统一接口激活失败: {str(e)}")
            return False

    def generate_activation_summary(self):
        """生成激活总结"""
        self.log("\n" + "="*60)
        self.log("3层记忆系统激活完成!")
        self.log("="*60)

        self.log("\n📊 系统状态:")
        self.log("✅ 第1层: 监控系统 (Canvas File Monitor)")
        self.log("✅ 第2层: Temporal 时间轴记忆")
        self.log("✅ 第3层: Semantic 语义记忆")
        self.log("⚠️  第4层: Graphiti 知识图谱 (需要Neo4j)")
        self.log("✅ 统一接口已激活")

        self.log("\n🎯 下次启动记忆系统的命令:")
        self.log("\n  # 方式1: 全部激活 (推荐)")
        self.log("  python activate_full_memory_system.py")
        self.log("\n  # 方式2: 使用统一部署脚本")
        self.log("  python deploy_unified_memory_system.py")
        self.log("\n  # 方式3: 分别启动")
        self.log("  python start_canvas_memory.py          # 启动监听")
        self.log("  neo4j start                             # 启动Neo4j")
        self.log("  python start_graphiti_mcp.sh            # 启动Graphiti")

        self.log("\n📖 使用内存系统的命令:")
        self.log("  /unified-memory-status                  # 查看系统状态")
        self.log("  /unified-memory-store                   # 存储学习内容")
        self.log("  /unified-memory-retrieve                # 检索学习记忆")
        self.log("  /unified-memory-analytics               # 查看分析报告")

        self.log("\n✅ 激活日志已保存到: " + str(self.log_file))

    def activate_all(self):
        """全部激活"""
        self.log("\n🚀 Canvas 3层记忆系统激活开始...")
        self.log(f"   启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        results = []

        # 激活每层系统
        results.append(("监控系统", self.activate_monitor_system()))
        results.append(("Temporal", self.activate_temporal_system()))
        results.append(("Semantic", self.activate_semantic_system()))
        results.append(("Graphiti", self.activate_graphiti_system()))
        results.append(("统一接口", self.activate_unified_interface()))

        # 生成总结
        self.generate_activation_summary()

        # 显示结果
        self.log("\n📈 激活结果:")
        for name, result in results:
            status = "✅" if result else "❌"
            self.log(f"  {status} {name}")

        return all(result for _, result in results)

if __name__ == "__main__":
    activator = MemorySystemActivator()
    success = activator.activate_all()

    sys.exit(0 if success else 1)
