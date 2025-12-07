"""
Canvas Learning System - Learning Session Command Handler

实现 /learning start 命令的核心逻辑，真实初始化和启动三个记忆系统：
- Graphiti知识图谱（通过MCP工具）
- 时序记忆管理器（TemporalMemoryManager）
- 语义记忆管理器（SemanticMemoryManager）

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-30
Story: 10.10 - 修复/learning start命令核心逻辑
"""

import asyncio
import json
import os
import platform
import socket
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger
from memory_system.error_formatters import format_startup_report

# 导入MCP健康检查
from memory_system.mcp_health_check import check_mcp_server_health
from memory_system.memory_exceptions import SemanticMemoryError, TemporalMemoryError
from memory_system.semantic_memory_manager import SemanticMemoryManager

# Import system mode detection (Story 10.11.4)
from memory_system.system_mode_detector import SystemModeDetector

# 导入记忆管理器
from memory_system.temporal_memory_manager import TemporalMemoryManager

# =============================================================================
# System Mode Info Storage (Story 10.11.4 Task 3)
# =============================================================================

# Global variable to store current mode info
_current_mode_info = None


def set_mode_info(mode_info):
    global _current_mode_info
    _current_mode_info = mode_info


def get_mode_info():
    return _current_mode_info


# =============================================================================
# 系统可用性检测函数 (Story 10.11)
# =============================================================================

def check_neo4j_connection(
    uri: str = "bolt://localhost:7687",
    username: str = "neo4j",
    password: str = "password",
    timeout: int = 2
) -> Dict[str, Any]:
    """
    检测Neo4j数据库连接状态（Windows兼容）

    Args:
        uri: Neo4j连接URI
        username: 用户名
        password: 密码
        timeout: 超时时间（秒）

    Returns:
        Dict: {'available': bool, 'error': str|None, 'version': str|None, 'suggestion': str|None}
    """
    try:
        # 1. 解析URI
        if "://" in uri:
            host_port = uri.split("//")[1]
            host = host_port.split(":")[0]
            port_str = host_port.split(":")[1].split("/")[0] if ":" in host_port else "7687"
            port = int(port_str)
        else:
            host = "localhost"
            port = 7687

        # 2. 快速检查端口是否可达（Windows兼容）
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        try:
            result = sock.connect_ex((host, port))

            if result != 0:
                # 根据操作系统提供不同的建议
                suggestion = (
                    'Windows: 运行 "neo4j.bat console" 或 "neo4j.bat start" 启动数据库'
                    if platform.system() == 'Windows' else
                    'Unix/Linux: 运行 "neo4j start" 启动数据库'
                )
                return {
                    'available': False,
                    'error': f'Neo4j端口{port}不可达（Connection refused）',
                    'suggestion': suggestion,
                    'version': None
                }
        except socket.error as e:
            return {
                'available': False,
                'error': f'Socket错误: {str(e)}',
                'suggestion': '检查防火墙设置或Neo4j配置文件',
                'version': None
            }
        finally:
            # 确保socket在所有情况下都被关闭
            sock.close()

        # 3. 尝试建立真实连接（验证认证）
        try:
            from neo4j import GraphDatabase
        except ImportError:
            return {
                'available': False,
                'error': 'neo4j Python库未安装',
                'suggestion': '运行 "pip install neo4j" 安装依赖',
                'version': None
            }

        driver = GraphDatabase.driver(uri, auth=(username, password))

        try:
            with driver.session() as session:
                result = session.run("RETURN 1 AS num")
                _ = result.single()

            driver.close()

            return {
                'available': True,
                'error': None,
                'version': 'Neo4j 5.x',  # 可以通过 CALL dbms.components() 获取精确版本
                'suggestion': None
            }
        except Exception as e:
            driver.close()
            return {
                'available': False,
                'error': f'Neo4j认证或查询失败: {str(e)}',
                'suggestion': '检查用户名、密码是否正确，或Neo4j数据库是否正常运行',
                'version': None
            }

    except Exception as e:
        return {
            'available': False,
            'error': f'连接检测失败: {str(e)}',
            'suggestion': '检查Neo4j服务状态和网络连接',
            'version': None
        }


async def check_mcp_server_health(timeout: int = 2) -> Dict[str, Any]:
    """
    检测MCP服务器健康状态

    Args:
        timeout: 超时时间（秒）

    Returns:
        Dict: {'available': bool, 'error': str|None, 'services': List[str], 'suggestion': str|None}
    """
    try:
        # 1. 尝试导入MCP工具
        try:
            from claude_tools import mcp__graphiti_memory__list_memories
        except ImportError as e:
            return {
                'available': False,
                'error': f'MCP工具未导入: {str(e)}',
                'suggestion': '检查Claude Code是否正确连接MCP服务器',
                'services': []
            }
        except NameError as e:
            return {
                'available': False,
                'error': f'MCP工具未定义: {str(e)}',
                'suggestion': '检查.claude/settings.local.json中的MCP配置',
                'services': []
            }

        # 2. 测试MCP工具调用（设置超时）
        try:
            # 直接await MCP工具调用，使用asyncio.wait_for设置超时
            result = await asyncio.wait_for(
                mcp__graphiti_memory__list_memories(),
                timeout=timeout
            )

            # 如果成功，MCP服务器可用
            return {
                'available': True,
                'error': None,
                'services': ['graphiti-memory'],
                'suggestion': None
            }

        except asyncio.TimeoutError:
            return {
                'available': False,
                'error': f'MCP服务器响应超时（>{timeout}秒）',
                'suggestion': '检查MCP服务器负载或网络连接',
                'services': []
            }
        except Exception as e:
            return {
                'available': False,
                'error': f'MCP工具调用失败: {str(e)}',
                'suggestion': '重启MCP服务器或检查Graphiti服务状态',
                'services': []
            }

    except Exception as e:
        return {
            'available': False,
            'error': f'MCP健康检查失败: {str(e)}',
            'suggestion': '检查Claude Code和MCP服务器配置',
            'services': []
        }


def log_startup_error_to_debug_log(
    error_type: str,
    error_message: str,
    system_name: str,
    stack_trace: Optional[str] = None
):
    """
    将启动错误记录到debug-log.md

    Args:
        error_type: 错误类型（如"Neo4jConnectionError"）
        error_message: 错误消息
        system_name: 系统名称（如"Graphiti"）
        stack_trace: 堆栈跟踪（可选）
    """
    debug_log_path = Path(".ai/debug-log.md")
    debug_log_path.parent.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = f"""
---

## 学习会话启动错误

**时间**: {timestamp}
**系统**: {system_name}
**错误类型**: {error_type}
**错误消息**: {error_message}

"""

    if stack_trace:
        log_entry += f"""
**堆栈跟踪**:
```
{stack_trace}
```

"""

    # 追加到debug-log.md
    with open(debug_log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)

    logger.info(f"错误已记录到: {debug_log_path}")


# =============================================================================
# LearningSessionManager 类定义
# =============================================================================

class LearningSessionManager:
    """学习会话管理器 - 负责启动和管理学习会话

    Story 10.13 Task 4: 添加启动缓存机制，减少重复初始化开销
    性能目标: 缓存命中时启动<2秒
    """

    # 类级缓存 (Story 10.13 Task 4 - AC 4)
    _instance_cache: Dict[str, 'LearningSessionManager'] = {}
    _cache_lock = asyncio.Lock()

    def __init__(self, session_dir: str = ".learning_sessions"):
        """
        初始化学习会话管理器

        Args:
            session_dir: 会话JSON存储目录
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.current_session: Optional[Dict] = None
        # Story 10.11.4: Store manager instances for mode detection
        self.temporal_manager = None
        self.semantic_manager = None
        self.graphiti_available = False
        # Story 10.13 Task 4: 计算配置哈希用于缓存键
        self._config_hash = self._compute_config_hash()

    def _compute_config_hash(self) -> str:
        """计算配置哈希值用于缓存键

        Story 10.13 Task 4: 基于session_dir生成唯一缓存键

        Returns:
            str: MD5哈希值（32字符十六进制）
        """
        import hashlib
        config_str = f"{self.session_dir}"
        return hashlib.md5(config_str.encode()).hexdigest()

    @classmethod
    async def get_instance(cls, session_dir: str = ".learning_sessions") -> 'LearningSessionManager':
        """获取缓存的管理器实例（工厂方法）

        Story 10.13 Task 4 - AC 4实现:
        - 首次调用: 创建新实例并缓存
        - 后续调用: 直接返回缓存实例（<2秒）
        - 线程安全: 使用asyncio.Lock防止竞态条件

        Args:
            session_dir: 会话目录路径

        Returns:
            LearningSessionManager: 缓存的或新创建的管理器实例

        Example:
            # 首次调用（完整初始化）
            manager1 = await LearningSessionManager.get_instance()

            # 后续调用（缓存命中，<2秒）
            manager2 = await LearningSessionManager.get_instance()
            assert manager1 is manager2  # 同一实例
        """
        async with cls._cache_lock:
            cache_key = session_dir

            if cache_key not in cls._instance_cache:
                logger.info("🔧 创建新的LearningSessionManager实例（缓存未命中）")
                cls._instance_cache[cache_key] = cls(session_dir=session_dir)
            else:
                logger.info("⚡ 复用已缓存的LearningSessionManager实例（缓存命中）")

            return cls._instance_cache[cache_key]

    @classmethod
    def clear_cache(cls):
        """清除实例缓存（配置变更时使用）

        Story 10.13 Task 4: 支持强制刷新缓存

        使用场景:
        - 配置文件变更后需要重新初始化
        - 测试环境下需要隔离实例
        - 内存清理（长期运行的服务）

        Example:
            # 变更配置后清除缓存
            LearningSessionManager.clear_cache()

            # 下次调用将创建新实例
            manager = await LearningSessionManager.get_instance()
        """
        cls._instance_cache.clear()
        logger.info("🧹 LearningSessionManager缓存已清除")

    async def start_session(
        self,
        canvas_path: str,
        user_id: str = "default",
        session_name: Optional[str] = None,
        allow_partial_start: bool = True,
        interactive: bool = False
    ) -> Dict[str, Any]:
        """
        启动学习会话，真实初始化所有记忆系统（支持优雅降级）

        Args:
            canvas_path: Canvas文件路径
            user_id: 用户ID
            session_name: 会话名称（可选）
            allow_partial_start: 是否允许部分系统启动（默认True）
            interactive: 是否启用交互式提示（默认False，CLI环境下可设为True）

        Returns:
            Dict: 启动结果，包含各系统状态和状态报告
        """
        # 0. 预检测系统可用性（可选，提高用户体验）
        logger.info("开始预检测系统可用性...")
        pre_check = await self.detect_systems_before_start()

        # 如果所有系统都不可用，提前警告用户
        if not pre_check['neo4j']['available'] and not pre_check['mcp_server']['available']:
            logger.warning("⚠️ 所有主要系统都不可用，会话可能无法启动")

        # 1. 生成会话ID和名称
        session_id = self._generate_session_id()
        session_name = session_name or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"开始启动学习会话: {session_id}")

        # 2. MCP服务器健康检查（早期检测，提供友好错误消息）
        logger.info("执行MCP服务器健康检查...")
        mcp_health = await check_mcp_server_health(timeout=2)
        graphiti_unavailable = False  # 降级模式标记

        if not mcp_health['available']:
            # MCP服务器不可用，显示友好错误消息
            logger.warning("❌ Graphiti知识图谱功能不可用")
            logger.warning("MCP服务器未连接")
            logger.warning("")
            logger.warning(f"原因: {mcp_health['error']}")
            logger.warning("")
            logger.warning("自动启动命令:")
            logger.warning("  deployment\\start_all_mcp_servers.bat")
            logger.warning("")
            logger.warning("或手动启动:")
            logger.warning("  cd graphiti/mcp_server")
            logger.warning("  start_graphiti_mcp.bat")
            logger.warning("")
            logger.warning("预计时间: 30秒")
            logger.warning("")
            logger.warning("💡 系统将继续以降级模式启动（Graphiti功能不可用）")
            logger.warning("   时序记忆和语义记忆仍将正常工作")
            logger.warning("")

            # 设置降级模式标记
            graphiti_unavailable = True

        # 3. 初始化会话数据结构
        session_data = {
            "session_id": session_id,
            "session_name": session_name,
            "user_id": user_id,
            "start_time": datetime.now().isoformat(),
            "canvas_path": os.path.abspath(canvas_path),
            "memory_systems": {},
            "degradation_mode": {
                "graphiti_unavailable": graphiti_unavailable
            }
        }

        # 4. 真实启动三个记忆系统（并行执行，互不阻塞）
        # Story 10.13 Task 3: 并行化记忆系统初始化
        # 性能优化：从串行60-120秒降为并行20-40秒
        import time
        import traceback

        logger.info("🚀 并行启动三个记忆系统...")
        parallel_start_time = time.time()

        # 4.1 使用asyncio.gather并行执行（AC 3要求）
        results_list = await asyncio.gather(
            self._start_graphiti(canvas_path, session_id),
            self._start_temporal(canvas_path, session_id),
            self._start_semantic(canvas_path, session_id),
            return_exceptions=True  # 捕获异常但不中断其他任务（错误隔离）
        )

        # 4.2 处理并行执行结果
        results = {}
        system_configs = [
            {
                'name': 'graphiti',
                'display_name': 'Graphiti知识图谱',
                'storage': 'Neo4j图数据库 (Direct Python SDK)',
                'suggestion': "检查Neo4j数据库是否启动，或安装 'pip install graphiti-core'"
            },
            {
                'name': 'temporal',
                'display_name': '时序记忆管理器',
                'storage': '本地SQLite数据库',
                'suggestion': "检查Graphiti库是否安装，或Neo4j数据库是否可用"
            },
            {
                'name': 'semantic',
                'display_name': '语义记忆管理器',
                'storage': '向量数据库',
                'suggestion': "检查MCP语义服务是否连接，或重启MCP服务器"
            }
        ]

        for idx, (system_config, result) in enumerate(zip(system_configs, results_list)):
            system_name = system_config['name']
            display_name = system_config['display_name']

            if isinstance(result, Exception):
                # 启动失败（异常情况）
                error_msg = str(result)
                logger.error(f"❌ {display_name}启动失败: {error_msg}")

                results[system_name] = {
                    'status': 'unavailable',
                    'error': error_msg,
                    'suggestion': system_config['suggestion'],
                    'attempted_at': datetime.now().isoformat(),
                    'storage': system_config['storage']
                }

                # 记录错误日志
                log_startup_error_to_debug_log(
                    error_type=type(result).__name__,
                    error_message=error_msg,
                    system_name=display_name,
                    stack_trace=traceback.format_exception(type(result), result, result.__traceback__)
                )
            else:
                # 启动成功
                results[system_name] = result
                status = result.get('status', 'unknown')
                if status == 'running':
                    logger.info(f"✅ {display_name}启动成功")
                else:
                    logger.warning(f"⚠️ {display_name}状态: {status}")

        # 4.3 性能计时（验证优化效果）
        parallel_elapsed = time.time() - parallel_start_time
        logger.info(f"⏱️ 三系统并行启动完成，耗时: {parallel_elapsed:.2f}秒")

        # AC 3验证：并行启动应<40秒（vs 串行60-120秒）
        if parallel_elapsed < 40:
            logger.success("🎯 性能目标达成: 并行启动<40秒 ✓")
        else:
            logger.warning(f"⚠️ 并行启动耗时{parallel_elapsed:.2f}秒超过40秒目标")

        # 4.4 检测系统运行模式并显示启动横幅 (Story 10.11.4)
        try:
            # 为mode detection创建默认manager实例（如果尚未创建）
            if self.temporal_manager is None:
                self.temporal_manager = type('TempObj', (), {
                    'is_initialized': False,
                    'mode': 'unavailable'
                })()
            if self.semantic_manager is None:
                self.semantic_manager = type('TempObj', (), {
                    'is_initialized': False,
                    'mode': 'unavailable'
                })()

            # 检测系统模式
            mode_info = SystemModeDetector.detect_mode(
                temporal_manager=self.temporal_manager,
                graphiti_available=self.graphiti_available,
                semantic_manager=self.semantic_manager
            )

            # 生成并显示启动横幅
            startup_banner = format_startup_report(mode_info)
            print()  # 空行分隔
            print(startup_banner)
            print()  # 空行分隔

            # 存储mode_info供后续命令使用
            set_mode_info(mode_info)

            # 记录模式信息到session_data
            session_data['system_mode'] = mode_info

            logger.info(f"系统运行模式: {mode_info['mode']}")
        except Exception as e:
            logger.warning(f"模式检测失败，继续启动: {e}")
            # 模式检测失败不应阻止会话启动

        # 5. 更新会话数据
        session_data['memory_systems'] = results

        # 6. 统计运行中的系统数量
        running_count = sum(
            1 for system_data in results.values()
            if system_data.get('status') == 'running'
        )

        # 7. 生成状态报告
        status_report = self.generate_status_report(
            memory_systems=results,
            session_data=session_data
        )

        # 8. 输出状态报告到用户
        try:
            print(status_report)
        except UnicodeEncodeError:
            # Windows console encoding issue with emojis - use logger instead
            logger.info("Status report (emojis may not display correctly in console):")
            logger.info(status_report.replace('\U0001f4ca', '[CHART]').replace('\u2705', '[OK]').replace('\u274c', '[X]').replace('\u26a0\ufe0f', '[WARNING]'))

        # 9. 判断是否成功启动
        if running_count == 0:
            # 所有系统都不可用
            logger.warning("⚠️ 所有记忆系统不可用")

            if not allow_partial_start:
                logger.error("❌ 会话启动失败，所有记忆系统都不可用")
                return {
                    'success': False,
                    'error': '所有记忆系统都不可用',
                    'status_report': status_report,
                    'pre_check': pre_check,
                    'running_systems': 0,
                    'total_systems': len(results)
                }

            # 交互式模式：询问用户是否继续使用基础功能
            if interactive:
                print("\n💡 所有记忆系统不可用，但您仍可使用基础Canvas学习功能。")
                print("   基础功能包括：问题拆解、AI解释生成、评分等。")
                print("   限制：无法记录学习历程、无法生成学习报告。")
                print()

                user_choice = input("是否继续使用基础功能模式？(y/n): ").strip().lower()

                if user_choice != 'y':
                    logger.info("用户选择退出")
                    return {
                        'success': False,
                        'error': '用户取消启动',
                        'status_report': status_report,
                        'running_systems': 0,
                        'total_systems': len(results)
                    }

            # 如果允许部分启动或用户确认继续
            logger.info("使用基础功能模式继续")
            session_data['mode'] = 'basic_mode'
            session_data['limitations'] = [
                '无法记录学习历程',
                '无法生成学习报告',
                '无法跨Canvas知识关联'
            ]

        # 10. 保存会话JSON
        session_file = self.session_dir / f"{session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        logger.info(f"会话已保存: {session_file}")
        self.current_session = session_data

        return {
            'success': running_count > 0 or allow_partial_start,
            'session_id': session_id,
            'session_file': str(session_file),
            'running_systems': running_count,
            'total_systems': len(results),
            'status_report': status_report,
            'memory_systems': results,
            'pre_check': pre_check
        }

    async def _start_graphiti(
        self,
        canvas_path: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        真实启动Graphiti知识图谱记录 - 使用DirectGraphitiStorage (纯Python SDK)

        Args:
            canvas_path: Canvas文件路径
            session_id: 会话ID

        Returns:
            Dict: 启动结果 {'status': 'running'/'unavailable', ...}

        Raises:
            RuntimeError: 如果Graphiti初始化失败
            ValueError: 如果返回结果缺少episode_id
        """
        try:
            # 导入DirectGraphitiStorage (不依赖MCP或claude_tools)
            from memory_system.graphiti_storage import DirectGraphitiStorage

            # 获取Neo4j配置
            neo4j_config = {
                'uri': 'bolt://localhost:7687',
                'user': 'neo4j',
                'password': '707188Fx'
            }

            # 创建DirectGraphitiStorage实例
            storage = DirectGraphitiStorage(**neo4j_config)

            if not storage.connected:
                raise RuntimeError("DirectGraphitiStorage连接失败 (graphiti_core可能未安装)")

            # 提取canvas_id
            import os
            canvas_id = os.path.splitext(os.path.basename(canvas_path))[0]

            # 调用add_learning_episode
            episode_id = await storage.add_learning_episode(
                canvas_id=canvas_id,
                session_id=session_id,
                episode_body=f"开始学习会话: {canvas_path}",
                metadata={
                    'canvas_path': canvas_path,
                    'session_type': 'learning'
                }
            )

            # 验证返回结果
            if episode_id:
                # 标记Graphiti为可用
                self.graphiti_available = True
                logger.info(f"✅ Graphiti启动成功 [Direct Neo4j Storage]，episode_id: {episode_id}")
                return {
                    'status': 'running',
                    'memory_id': episode_id,  # 保持兼容性，使用memory_id
                    'episode_id': episode_id,
                    'storage': 'Neo4j图数据库 (Direct Python SDK)',
                    'mode': 'direct_graphiti',
                    'initialized_at': datetime.now().isoformat()
                }
            else:
                raise ValueError("Graphiti返回episode_id为空")

        except ImportError as e:
            logger.warning(f"⚠️ graphiti_core未安装: {e}")
            logger.info("提示: 运行 'pip install graphiti-core' 安装Graphiti支持")
            raise RuntimeError(f"Graphiti初始化失败: graphiti_core未安装 - {e}")

        except Exception as e:
            logger.warning(f"⚠️ Graphiti启动失败: {e}")
            raise

    async def _start_temporal(
        self,
        canvas_path: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        真实初始化并启动时序记忆管理器

        Args:
            canvas_path: Canvas文件路径
            session_id: 会话ID

        Returns:
            Dict: 启动结果 {'status': 'running'/'unavailable', ...}

        Raises:
            TemporalMemoryError: 如果初始化失败
        """
        try:
            # 1. 初始化TemporalMemoryManager
            temporal_manager = TemporalMemoryManager(config={
                'neo4j_uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
                'neo4j_username': os.getenv('NEO4J_USERNAME', 'neo4j'),
                'neo4j_password': os.getenv('NEO4J_PASSWORD', '707188Fx'),
                'database_name': 'ultrathink'
            })

            # Story 10.11.4: Store manager for mode detection
            self.temporal_manager = temporal_manager

            # 2. 检查初始化状态
            if not temporal_manager.is_initialized:
                raise TemporalMemoryError(
                    operation="initialize",
                    details="TemporalMemoryManager初始化失败"
                )

            # 3. 创建学习会话（使用正确的API）
            session = temporal_manager.create_learning_session(
                canvas_id=canvas_path,
                user_id="default_user"
            )

            # 4. 从返回的LearningSession对象获取session_id
            created_session_id = session.session_id

            logger.info(f"✅ 时序记忆管理器启动成功，session_id: {created_session_id}")
            return {
                'status': 'running',
                'session_id': created_session_id,
                'storage': '本地SQLite数据库',
                'initialized_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.warning(f"⚠️ 时序记忆管理器启动失败: {e}")
            raise

    async def _start_semantic(
        self,
        canvas_path: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        真实初始化并启动语义记忆管理器

        Args:
            canvas_path: Canvas文件路径
            session_id: 会话ID

        Returns:
            Dict: 启动结果 {'status': 'running'/'unavailable', ...}

        Raises:
            SemanticMemoryError: 如果MCP语义服务未连接
        """
        try:
            # 1. 初始化SemanticMemoryManager
            semantic_manager = SemanticMemoryManager(config={
                'endpoint': 'local',
                'timeout': 30,
                'fallback_db_path': ':memory:'  # 支持降级模式
            })

            # Story 10.11.4: Store manager for mode detection
            self.semantic_manager = semantic_manager

            # 2. 获取状态信息（Story 10.11.3 AC4）
            status_info = semantic_manager.get_status()
            mode = status_info['mode']  # 'mcp' | 'fallback' | 'unavailable'

            # 3. 检查是否可用
            if not status_info['initialized']:
                raise SemanticMemoryError(
                    operation="initialize",
                    details=f"语义记忆管理器不可用（mode={mode}）"
                )

            # 4. 存储初始记忆
            memory_id = semantic_manager.store_semantic_memory(
                content=f"开始学习会话: {canvas_path}",
                metadata={
                    'canvas': os.path.basename(canvas_path),
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat()
                }
            )

            # 5. 根据mode设置storage描述
            storage_desc = '向量数据库' if mode == 'mcp' else '本地SQLite缓存'

            logger.info(f"✅ 语义记忆管理器启动成功 [模式: {mode}]，memory_id: {memory_id}")

            # 6. 返回完整状态（包含mode和features）
            return {
                'status': 'running' if status_info['initialized'] else 'unavailable',
                'mode': mode,
                'features': status_info['features'],
                'memory_id': memory_id,
                'storage': storage_desc,
                'initialized_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.warning(f"⚠️ 语义记忆管理器启动失败: {e}")
            raise

    def _check_python_dependencies(self) -> Dict[str, Any]:
        """
        检测必需的Python库是否安装

        Returns:
            Dict: {'available': bool, 'missing': List[str], 'suggestion': str|None}
        """
        required_libs = ['neo4j', 'loguru', 'graphiti_core']
        missing = []

        for lib in required_libs:
            try:
                __import__(lib)
            except ImportError:
                missing.append(lib)

        return {
            'available': len(missing) == 0,
            'missing': missing,
            'suggestion': f"运行 'pip install {' '.join(missing)}' 安装缺失依赖" if missing else None
        }

    async def detect_systems_before_start(self) -> Dict[str, Dict]:
        """
        在启动前预检测所有系统的可用性

        Returns:
            Dict: 预检测结果
                {
                    'neo4j': {'available': bool, 'error': str|None},
                    'mcp_server': {'available': bool, 'error': str|None},
                    'dependencies': {'available': bool, 'missing': List[str]}
                }
        """
        logger.info("开始预检测系统可用性...")

        results = {}

        # 1. 检测Neo4j连接
        neo4j_check = check_neo4j_connection(
            uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            username=os.getenv('NEO4J_USERNAME', 'neo4j'),
            password=os.getenv('NEO4J_PASSWORD', '707188Fx')
        )
        results['neo4j'] = neo4j_check
        if neo4j_check['available']:
            logger.info("✅ Neo4j连接正常")
        else:
            logger.warning(f"⚠️ Neo4j不可用: {neo4j_check['error']}")

        # 2. 检测MCP服务器
        mcp_check = await check_mcp_server_health()
        results['mcp_server'] = mcp_check
        if mcp_check['available']:
            logger.info("✅ MCP服务器健康")
        else:
            logger.warning(f"⚠️ MCP服务器不可用: {mcp_check['error']}")

        # 3. 检测Python依赖
        dependencies_check = self._check_python_dependencies()
        results['dependencies'] = dependencies_check
        if dependencies_check['available']:
            logger.info("✅ Python依赖完整")
        else:
            logger.warning(f"⚠️ 缺少依赖: {dependencies_check['missing']}")

        return results

    def generate_status_report(
        self,
        memory_systems: Dict[str, Dict],
        session_data: Dict
    ) -> str:
        """
        生成用户友好的启动状态报告

        Args:
            memory_systems: 记忆系统状态字典
            session_data: 会话数据

        Returns:
            str: 格式化的状态报告（多行字符串）
        """
        report_lines = ["", "📊 学习会话启动报告", ""]

        running_count = 0
        total_count = len(memory_systems)

        # 系统名称映射
        system_names = {
            'graphiti': 'Graphiti知识图谱',
            'temporal': '时序记忆管理器',
            'semantic': '语义记忆管理器'
        }

        # 生成每个系统的状态报告
        for system_key, system_data in memory_systems.items():
            system_name = system_names.get(system_key, system_key)
            status = system_data.get('status')

            if status == 'running':
                running_count += 1
                report_lines.append(f"✅ {system_name}: 运行中")

                # Story 10.11.3 AC4: 显示语义记忆管理器的模式信息
                if system_key == 'semantic' and 'mode' in system_data:
                    mode = system_data['mode']
                    if mode == 'mcp':
                        report_lines.append("   模式: MCP完整模式")
                    elif mode == 'fallback':
                        report_lines.append("   模式: 降级模式 - 本地缓存")
                        report_lines.append("   ⚠️  高级语义搜索不可用，使用关键词搜索")

                    # 显示功能限制
                    if 'features' in system_data:
                        features = system_data['features']
                        if not features.get('advanced_semantic_search', True):
                            disabled_features = []
                            if not features.get('vector_similarity', True):
                                disabled_features.append('向量检索')
                            if not features.get('cross_domain_connections', True):
                                disabled_features.append('跨域连接')
                            if disabled_features:
                                report_lines.append(f"   功能限制: {', '.join(disabled_features)}不可用")

                # 添加详细信息
                if 'memory_id' in system_data:
                    report_lines.append(f"   Memory ID: {system_data['memory_id']}")
                if 'session_id' in system_data:
                    report_lines.append(f"   Session ID: {system_data['session_id']}")
                if 'storage' in system_data:
                    report_lines.append(f"   存储位置: {system_data['storage']}")
                if 'initialized_at' in system_data:
                    report_lines.append(f"   初始化时间: {system_data['initialized_at']}")

            elif status == 'unavailable':
                report_lines.append(f"⚠️ {system_name}: 不可用")

                # 添加错误信息和建议
                if 'error' in system_data:
                    report_lines.append(f"   原因: {system_data['error']}")
                if 'suggestion' in system_data:
                    report_lines.append(f"   建议: {system_data['suggestion']}")
                if 'attempted_at' in system_data:
                    report_lines.append(f"   尝试时间: {system_data['attempted_at']}")

            report_lines.append("")  # 空行

        # 生成总结
        if running_count == total_count:
            report_lines.append(f"✅ 会话已启动，{running_count}/{total_count} 记忆系统正常运行")
        elif running_count > 0:
            report_lines.append(f"✅ 会话已启动，{running_count}/{total_count} 记忆系统正常运行")
            report_lines.append("⚠️ 部分功能受限，但学习可以继续")
        else:
            report_lines.append(f"❌ 会话启动失败，0/{total_count} 记忆系统可用")
            report_lines.append("")
            report_lines.append("💡 建议：")
            report_lines.append("1. 检查系统依赖（Neo4j、MCP服务器）")
            report_lines.append("2. 查看详细错误日志：.ai/debug-log.md")
            report_lines.append("3. 或使用基础功能模式（不记录学习历程）")

        # 添加会话信息
        report_lines.append("")
        report_lines.append(f"会话ID: {session_data['session_id']}")
        report_lines.append(f"Canvas: {session_data['canvas_path']}")
        report_lines.append(f"开始时间: {session_data['start_time']}")

        return "\n".join(report_lines)

    def _generate_session_id(self) -> str:
        """生成唯一的会话ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


# 便捷函数
def create_learning_session_manager(session_dir: str = ".learning_sessions") -> LearningSessionManager:
    """创建学习会话管理器的便捷函数"""
    return LearningSessionManager(session_dir)


# 测试用例
if __name__ == "__main__":
    import asyncio

    async def test_learning_session_manager():
        """测试学习会话管理器"""
        try:
            manager = LearningSessionManager()
            logger.info("学习会话管理器初始化成功")

            # 创建测试会话
            result = await manager.start_session(
                canvas_path="tests/fixtures/test.canvas",
                user_id="test_user"
            )
            logger.info(f"会话启动结果: {result}")

        except Exception as e:
            logger.error(f"学习会话管理器测试失败: {e}")

    # 运行测试
    asyncio.run(test_learning_session_manager())
