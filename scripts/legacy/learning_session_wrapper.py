#!/usr/bin/env python3
"""
Canvas学习会话统一管理系统
命令包装器模式实现

包装现有的 /graph、/memory、/unified-memory 命令
提供统一的学习会话启动和管理体验

Author: Canvas Learning System Team
Version: 1.0
Date: 2025-10-25
"""

import os
import sys
import json
import uuid
import asyncio
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import yaml

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False

# Import RealServiceLauncher
from learning_system.real_service_launcher import RealServiceLauncher

@dataclass
class LearningSession:
    """学习会话数据结构"""
    session_id: str
    user_id: str
    canvas_path: str
    session_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    active_canvases: List[str] = field(default_factory=list)
    memory_systems: Dict[str, bool] = field(default_factory=dict)
    session_metadata: Dict[str, Any] = field(default_factory=dict)
    command_processes: Dict[str, subprocess.Popen] = field(default_factory=dict)

class CommandCoordinator:
    """命令协调器 - 包装现有命令"""

    def __init__(self, config_path: str = "config/learning_session_config.yaml"):
        self.config = self._load_config(config_path)
        self.active_sessions: Dict[str, LearningSession] = {}

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "learning_session": {
                "default_duration_minutes": 60,
                "auto_save_interval_minutes": 5,
                "max_concurrent_canvases": 3,
                "session_timeout_hours": 8
            },
            "memory_systems": {
                "graphiti": {
                    "enabled": True,
                    "command_path": "/graph",
                    "auto_extract_concepts": True,
                    "relationship_depth": 2
                },
                "behavioral": {
                    "enabled": True,
                    "command_path": "/memory-start",
                    "capture_frequency_ms": 100,
                    "auto_analyze_patterns": True
                },
                "semantic": {
                    "enabled": True,
                    "command_prefix": "/unified-memory",
                    "auto_tag_content": True,
                    "similarity_threshold": 0.7
                }
            }
        }

class LearningSessionWrapper:
    """学习会话包装器"""

    def __init__(self):
        self.coordinator = CommandCoordinator()
        self.current_session: Optional[LearningSession] = None
        self.service_launcher = RealServiceLauncher()  # 真实服务启动器

    async def start_session(self,
                           canvas_path: str,
                           user_id: str = "default",
                           session_name: Optional[str] = None,
                           duration_minutes: int = 60,
                           enable_graphiti: bool = True,
                           enable_memory: bool = True,
                           enable_semantic: bool = True) -> Dict[str, Any]:
        """启动学习会话"""

        try:
            # 生成会话ID
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # 生成会话名称
            if not session_name:
                canvas_name = Path(canvas_path).stem
                session_name = f"{canvas_name}_学习会话_{datetime.now().strftime('%m%d')}"

            # 创建会话对象
            session = LearningSession(
                session_id=session_id,
                user_id=user_id,
                canvas_path=canvas_path,
                session_name=session_name,
                start_time=datetime.now(),
                active_canvases=[canvas_path],
                memory_systems={}
            )

            # 使用真实服务启动器启动各个记忆系统
            startup_results = await self.service_launcher.start_all_services(
                canvas_path=canvas_path,
                session=session,
                enable_graphiti=enable_graphiti,
                enable_semantic=enable_semantic,
                enable_behavior=enable_memory  # enable_memory maps to behavior monitor
            )

            # 更新会话的记忆系统状态
            session.memory_systems['graphiti'] = startup_results.get('graphiti', {}).get('success', False)
            session.memory_systems['mcp_semantic'] = startup_results.get('mcp_semantic', {}).get('success', False)
            session.memory_systems['behavior_monitor'] = startup_results.get('behavior_monitor', {}).get('success', False)

            # 存储会话
            self.coordinator.active_sessions[session_id] = session
            self.current_session = session

            return {
                "success": True,
                "session_id": session_id,
                "session_name": session_name,
                "canvas_path": canvas_path,
                "start_time": session.start_time.isoformat(),
                "memory_systems": session.memory_systems,
                "startup_results": startup_results,
                "message": f"学习会话 '{session_name}' 已启动"
            }

        except Exception as e:
            logger.error(f"启动学习会话失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "学习会话启动失败"
            }

    async def stop_session(self, session_id: Optional[str] = None, save_report: bool = True) -> Dict[str, Any]:
        """停止学习会话"""
        try:
            if session_id is None:
                session_id = self.current_session.session_id if self.current_session else None

            if not session_id or session_id not in self.coordinator.active_sessions:
                return {
                    "success": False,
                    "error": "会话不存在或已结束",
                    "message": "无法停止不存在的会话"
                }

            session = self.coordinator.active_sessions[session_id]
            session.end_time = datetime.now()

            # 使用真实服务启动器停止所有记忆系统
            stop_results = await self.service_launcher.stop_all_services()

            # 生成学习报告
            report = None
            if save_report:
                report = await self._generate_report(session)

            # 移除会话
            del self.coordinator.active_sessions[session_id]
            if self.current_session and self.current_session.session_id == session_id:
                self.current_session = None

            duration = (session.end_time - session.start_time).total_seconds()

            return {
                "success": True,
                "session_id": session_id,
                "session_name": session.session_name,
                "duration_seconds": duration,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat(),
                "memory_systems": session.memory_systems,
                "stop_results": stop_results,
                "report": report,
                "message": f"学习会话 '{session.session_name}' 已结束，用时 {duration:.0f} 秒"
            }

        except Exception as e:
            logger.error(f"停止学习会话失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "学习会话停止失败"
            }

    async def get_session_status(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """获取会话状态"""
        try:
            if session_id is None:
                session_id = self.current_session.session_id if self.current_session else None

            if not session_id or session_id not in self.coordinator.active_sessions:
                return {
                    "success": False,
                    "message": "没有活跃的学习会话"
                }

            session = self.coordinator.active_sessions[session_id]
            current_time = datetime.now()
            duration = (current_time - session.start_time).total_seconds()

            # 获取真实的服务状态和健康信息
            services_status = await self.service_launcher.get_services_status()

            return {
                "success": True,
                "session_id": session_id,
                "session_name": session.session_name,
                "canvas_path": session.canvas_path,
                "start_time": session.start_time.isoformat(),
                "duration_seconds": duration,
                "active_canvases": session.active_canvases,
                "memory_systems": session.memory_systems,
                "services_status": services_status,  # 真实的服务状态和健康信息
                "status": "running"
            }

        except Exception as e:
            logger.error(f"获取会话状态失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "获取会话状态失败"
            }

    async def generate_report(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """生成学习报告"""
        try:
            if session_id is None:
                session_id = self.current_session.session_id if self.current_session else None

            if not session_id or session_id not in self.coordinator.active_sessions:
                return {
                    "success": False,
                    "message": "没有活跃的学习会话"
                }

            session = self.coordinator.active_sessions[session_id]
            duration = (datetime.now() - session.start_time).total_seconds()

            report = {
                "session_id": session_id,
                "session_name": session.session_name,
                "canvas_path": session.canvas_path,
                "start_time": session.start_time.isoformat(),
                "duration_seconds": duration,
                "memory_systems": session.memory_systems,
                "status": "completed"
            }

            return {
                "success": True,
                "report": report,
                "message": "学习报告已生成"
            }

        except Exception as e:
            logger.error(f"生成学习报告失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "生成学习报告失败"
            }

    async def _generate_report(self, session: LearningSession) -> Dict[str, Any]:
        """生成学习报告的内部方法"""
        try:
            duration = (datetime.now() - session.start_time).total_seconds()

            report = {
                "session_id": session.session_id,
                "session_name": session.session_name,
                "canvas_path": session.canvas_path,
                "start_time": session.start_time.isoformat(),
                "duration_seconds": duration,
                "memory_systems": session.memory_systems,
                "active_canvases": session.active_canvases,
                "generation_time": datetime.now().isoformat()
            }

            return report
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return {
                "error": str(e),
                "message": "报告生成过程中出错"
            }

# 全局实例
session_wrapper = LearningSessionWrapper()

# 命令处理函数
async def handle_learning_start(args: str) -> str:
    """处理 /learning start 命令"""
    try:
        # 解析参数
        parts = args.split()
        if len(parts) < 1:
            return "❌ 参数不足\n使用方法: /learning start <canvas_path> [选项]"

        canvas_path = parts[0].strip('"')

        # 解析选项
        options = {
            'user_id': 'default',
            'duration_minutes': 60,
            'enable_graphiti': True,
            'enable_memory': True,
            'enable_semantic': True
        }

        for part in parts[1:]:
            if part.startswith('--user-id='):
                options['user_id'] = part.split('=', 1)[1]
            elif part.startswith('--duration='):
                options['duration_minutes'] = int(part.split('=', 1)[1])
            elif part == '--no-graphiti':
                options['enable_graphiti'] = False
            elif part == '--no-memory':
                options['enable_memory'] = False
            elif part == '--no-semantic':
                options['enable_semantic'] = False

        # 启动会话
        result = await session_wrapper.start_session(
            canvas_path=canvas_path,
            **options
        )

        if result['success']:
            return f"""
🚀 学习会话已启动！

📋 会话信息:
- 会话ID: {result['session_id']}
- 会话名称: {result['session_name']}
- Canvas: {result['canvas_path']}
- 开始时间: {result['start_time']}

✅ 记忆系统状态:
"""
        else:
            return f"❌ 启动失败: {result.get('message', '未知错误')}"

    except Exception as e:
        return f"❌ 命令执行失败: {e}"

async def handle_learning_status(args: str) -> str:
    """处理 /learning status 命令"""
    try:
        result = await session_wrapper.get_session_status()

        if result['success']:
            duration_min = result['duration_seconds'] / 60
            systems_status = []
            for system, enabled in result['memory_systems'].items():
                status = "✅ 运行中" if enabled else "❌ 未启用"
                systems_status.append(f"- {system.capitalize()}: {status}")

            return f"""
📊 当前学习会话状态

🎯 会话信息:
- 会话ID: {result['session_id']}
- 会话名称: {result['session_name']}
- Canvas: {result['canvas_path']}
- 开始时间: {result['start_time']}
- 已用时: {duration_min:.1f} 分钟

📚 记忆系统状态:
{chr(10).join(systems_status)}
"""
        else:
            return result['message']

    except Exception as e:
        return f"❌ 获取状态失败: {e}"

async def handle_learning_stop(args: str) -> str:
    """处理 /learning stop 命令"""
    try:
        result = await session_wrapper.stop_session(save_report=True)

        if result['success']:
            duration_min = result['duration_seconds'] / 60
            return f"""
🏁 学习会话已结束！

📋 会话总结:
- 会话ID: {result['session_id']}
- 会话名称: {result['session_name']}
- Canvas: {result['canvas_path']}
- 学习时长: {duration_min:.1f} 分钟
- 开始时间: {result['start_time']}
- 结束时间: {result['end_time']}

📚 记忆系统状态:
{chr(10).join(f"- {k}: {'已停止' if v else '未启用'}" for k, v in result['memory_systems'].items())}

💡 学习报告已自动保存
"""
        else:
            return f"❌ 停止失败: {result.get('message', '未知错误')}"

    except Exception as e:
        return f"❌ 停止命令失败: {e}"

async def handle_learning_report(args: str) -> str:
    """处理 /learning report 命令"""
    try:
        result = await session_wrapper.generate_report()

        if result['success']:
            report = result['report']
            duration_min = report['duration_seconds'] / 60

            return f"""
📊 学习会话报告

📋 基本信息:
- 会话ID: {report['session_id']}
- 会话名称: {report['session_name']}
- Canvas: {report['canvas_path']}
- 学习时长: {duration_min:.1f} 分钟
- 开始时间: {report['start_time']}

📚 记忆系统使用情况:
{chr(10).join(f"- {k}: {'已使用' if v else '未使用'}" for k, v in report['memory_systems'].items())}

✅ 报告生成完成
"""
        else:
            return result['message']

    except Exception as e:
        return f"❌ 生成报告失败: {e}"

# 命令映射
COMMAND_HANDLERS = {
    'start': handle_learning_start,
    'status': handle_learning_status,
    'stop': handle_learning_stop,
    'report': handle_learning_report
}

async def execute_learning_command(command: str, args: str = "") -> str:
    """执行学习会话命令"""
    if command not in COMMAND_HANDLERS:
        available = ", ".join([f"/learning {cmd}" for cmd in COMMAND_HANDLERS.keys()])
        return f"❌ 未知命令: /learning {command}\n可用命令: {available}"

    try:
        return await COMMAND_HANDLERS[command](args)
    except Exception as e:
        return f"❌ 执行命令失败: {e}"

if __name__ == "__main__":
    # 测试代码
    async def test():
        print("=== 测试学习会话包装器 ===")

        # 测试启动会话
        result = await session_wrapper.start_session(
            canvas_path="测试/测试.canvas",
            session_name="测试会话"
        )
        print(f"启动结果: {result}")

        # 测试获取状态
        status = await session_wrapper.get_session_status()
        print(f"状态结果: {status}")

        # 测试停止会话
        stop_result = await session_wrapper.stop_session()
        print(f"停止结果: {stop_result}")

    asyncio.run(test())