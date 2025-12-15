"""
Canvas操作事件监听系统

本模块实现Canvas文件变化的实时监听和事件分发，包括：
- Canvas文件变化检测
- 节点操作事件监听
- 用户交互行为分析
- 实时事件通知

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-25
"""

import asyncio
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import hashlib

# 尝试导入loguru用于企业级日志记录
try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


@dataclass
class CanvasEvent:
    """Canvas事件数据模型"""
    event_id: str
    event_type: str
    timestamp: datetime
    canvas_path: str
    file_hash: str
    changes: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class NodeChangeEvent:
    """节点变化事件"""
    event_type: str  # 'created', 'modified', 'deleted', 'moved'
    node_id: str
    node_type: str
    old_data: Dict[str, Any]
    new_data: Dict[str, Any]
    timestamp: datetime


class CanvasFileHandler(FileSystemEventHandler):
    """Canvas文件变化处理器"""

    def __init__(self, event_dispatcher):
        self.event_dispatcher = event_dispatcher
        self.last_modified = {}
        super().__init__()

    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory:
            return

        if event.src_path.endswith('.canvas'):
            self._handle_canvas_change(event.src_path, 'modified')

    def on_created(self, event):
        """文件创建事件处理"""
        if event.is_directory:
            return

        if event.src_path.endswith('.canvas'):
            self._handle_canvas_change(event.src_path, 'created')

    def on_moved(self, event):
        """文件移动事件处理"""
        if event.is_directory:
            return

        if event.dest_path.endswith('.canvas'):
            self._handle_canvas_move(event.src_path, event.dest_path)

    def on_deleted(self, event):
        """文件删除事件处理"""
        if event.is_directory:
            return

        if event.src_path.endswith('.canvas'):
            self._handle_canvas_change(event.src_path, 'deleted')

    def _handle_canvas_change(self, canvas_path: str, change_type: str):
        """处理Canvas文件变化"""
        try:
            # 防止重复触发
            current_time = time.time()
            if (canvas_path in self.last_modified and
                current_time - self.last_modified[canvas_path] < 1.0):
                return

            self.last_modified[canvas_path] = current_time

            # 读取文件并计算哈希
            try:
                with open(canvas_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    file_hash = hashlib.md5(content.encode()).hexdigest()
                    canvas_data = json.loads(content)
            except Exception as e:
                logger.error(f"读取Canvas文件失败: {canvas_path}, 错误: {e}")
                return

            # 创建事件
            event = CanvasEvent(
                event_id=str(uuid.uuid4()),
                event_type=change_type,
                timestamp=datetime.now(),
                canvas_path=canvas_path,
                file_hash=file_hash,
                changes={},
                metadata={
                    'file_size': len(content),
                    'node_count': len(canvas_data.get('nodes', [])),
                    'edge_count': len(canvas_data.get('edges', []))
                }
            )

            # 分发事件
            self.event_dispatcher.dispatch_event(event)

        except Exception as e:
            logger.error(f"处理Canvas变化失败: {canvas_path}, 错误: {e}")

    def _handle_canvas_move(self, old_path: str, new_path: str):
        """处理Canvas文件移动"""
        event = CanvasEvent(
            event_id=str(uuid.uuid4()),
            event_type='moved',
            timestamp=datetime.now(),
            canvas_path=new_path,
            file_hash="",
            changes={'old_path': old_path, 'new_path': new_path},
            metadata={}
        )

        self.event_dispatcher.dispatch_event(event)


class CanvasEventListener:
    """Canvas事件监听器"""

    def __init__(self, learning_activity_capture=None):
        """初始化Canvas事件监听器

        Args:
            learning_activity_capture: 学习活动捕获器实例
        """
        self.activity_capture = learning_activity_capture
        self.observers: Dict[str, Observer] = {}
        self.event_handlers: List[Callable] = []
        self.canvas_states: Dict[str, Dict] = {}
        self.is_listening = False
        self.event_dispatcher = CanvasEventDispatcher()

        # 注册默认事件处理器
        self.event_dispatcher.register_handler(self._handle_canvas_event)

        logger.info("CanvasEventListener initialized")

    def start_listening(self, watch_paths: List[str] = None) -> bool:
        """开始监听Canvas文件变化

        Args:
            watch_paths: 监听路径列表，默认监听笔记库目录

        Returns:
            bool: 是否成功启动监听
        """
        if self.is_listening:
            logger.warning("监听已在运行中")
            return False

        if watch_paths is None:
            watch_paths = ["笔记库"]

        try:
            for watch_path in watch_paths:
                if not os.path.exists(watch_path):
                    logger.warning(f"监听路径不存在: {watch_path}")
                    continue

                # 创建观察者
                observer = Observer()
                event_handler = CanvasFileHandler(self.event_dispatcher)

                # 递归监听
                observer.schedule(event_handler, watch_path, recursive=True)
                observer.start()

                self.observers[watch_path] = observer

                # 初始化Canvas状态
                self._initialize_canvas_states(watch_path)

            self.is_listening = True
            logger.info(f"Canvas事件监听已启动，监听路径: {watch_paths}")
            return True

        except Exception as e:
            logger.error(f"启动Canvas监听失败: {e}")
            return False

    def stop_listening(self) -> bool:
        """停止监听Canvas文件变化

        Returns:
            bool: 是否成功停止监听
        """
        if not self.is_listening:
            logger.warning("监听未在运行")
            return False

        try:
            # 停止所有观察者
            for path, observer in self.observers.items():
                observer.stop()
                observer.join(timeout=5)
                logger.info(f"已停止监听路径: {path}")

            self.observers.clear()
            self.is_listening = False

            logger.info("Canvas事件监听已停止")
            return True

        except Exception as e:
            logger.error(f"停止Canvas监听失败: {e}")
            return False

    def register_event_handler(self, handler: Callable):
        """注册事件处理器

        Args:
            handler: 事件处理函数
        """
        self.event_handlers.append(handler)
        logger.debug(f"已注册事件处理器: {handler.__name__}")

    def unregister_event_handler(self, handler: Callable):
        """注销事件处理器

        Args:
            handler: 事件处理函数
        """
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)
            logger.debug(f"已注销事件处理器: {handler.__name__}")

    def _initialize_canvas_states(self, watch_path: str):
        """初始化Canvas状态"""
        try:
            for root, dirs, files in os.walk(watch_path):
                for file in files:
                    if file.endswith('.canvas'):
                        canvas_path = os.path.join(root, file)
                        self._load_canvas_state(canvas_path)

        except Exception as e:
            logger.error(f"初始化Canvas状态失败: {e}")

    def _load_canvas_state(self, canvas_path: str):
        """加载Canvas状态"""
        try:
            with open(canvas_path, 'r', encoding='utf-8') as f:
                canvas_data = json.load(f)

            # 提取节点状态
            nodes_state = {}
            for node in canvas_data.get('nodes', []):
                nodes_state[node['id']] = {
                    'text': node.get('text', ''),
                    'color': node.get('color', ''),
                    'x': node.get('x', 0),
                    'y': node.get('y', 0),
                    'width': node.get('width', 0),
                    'height': node.get('height', 0)
                }

            self.canvas_states[canvas_path] = {
                'nodes': nodes_state,
                'last_modified': datetime.now().isoformat(),
                'file_hash': self._calculate_file_hash(canvas_path)
            }

        except Exception as e:
            logger.error(f"加载Canvas状态失败: {canvas_path}, 错误: {e}")

    def _calculate_file_hash(self, canvas_path: str) -> str:
        """计算文件哈希"""
        try:
            with open(canvas_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def _handle_canvas_event(self, event: CanvasEvent):
        """处理Canvas事件（默认处理器）"""
        try:
            if event.event_type in ['modified', 'created']:
                self._analyze_canvas_changes(event)
            elif event.event_type == 'deleted':
                self._handle_canvas_deletion(event)

            # 调用其他注册的事件处理器
            for handler in self.event_handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"事件处理器执行失败: {handler.__name__}, 错误: {e}")

        except Exception as e:
            logger.error(f"处理Canvas事件失败: {e}")

    def _analyze_canvas_changes(self, event: CanvasEvent):
        """分析Canvas变化"""
        try:
            canvas_path = event.canvas_path

            # 加载当前Canvas状态
            with open(canvas_path, 'r', encoding='utf-8') as f:
                current_canvas = json.load(f)

            current_nodes = {node['id']: node for node in current_canvas.get('nodes', [])}

            # 获取之前的状态
            previous_state = self.canvas_states.get(canvas_path, {})
            previous_nodes = previous_state.get('nodes', {})

            # 分析节点变化
            changes = self._detect_node_changes(previous_nodes, current_nodes)

            # 更新状态
            self.canvas_states[canvas_path] = {
                'nodes': {node_id: {
                    'text': node.get('text', ''),
                    'color': node.get('color', ''),
                    'x': node.get('x', 0),
                    'y': node.get('y', 0),
                    'width': node.get('width', 0),
                    'height': node.get('height', 0)
                } for node_id, node in current_nodes.items()},
                'last_modified': event.timestamp.isoformat(),
                'file_hash': event.file_hash
            }

            # 如果有学习活动捕获器，记录变化
            if self.activity_capture and changes:
                self._record_canvas_changes(event, changes)

        except Exception as e:
            logger.error(f"分析Canvas变化失败: {e}")

    def _detect_node_changes(self, previous_nodes: Dict, current_nodes: Dict) -> List[Dict]:
        """检测节点变化"""
        changes = []

        # 检测新增节点
        for node_id, node_data in current_nodes.items():
            if node_id not in previous_nodes:
                changes.append({
                    'type': 'node_created',
                    'node_id': node_id,
                    'node_data': node_data
                })

        # 检测删除节点
        for node_id in previous_nodes:
            if node_id not in current_nodes:
                changes.append({
                    'type': 'node_deleted',
                    'node_id': node_id,
                    'node_data': previous_nodes[node_id]
                })

        # 检测修改节点
        for node_id, current_data in current_nodes.items():
            if node_id in previous_nodes:
                previous_data = previous_nodes[node_id]

                # 检查关键属性变化
                if (current_data.get('text', '') != previous_data.get('text', '') or
                    current_data.get('color', '') != previous_data.get('color', '')):

                    changes.append({
                        'type': 'node_modified',
                        'node_id': node_id,
                        'old_data': previous_data,
                        'new_data': current_data,
                        'changes': {
                            'text_changed': current_data.get('text', '') != previous_data.get('text', ''),
                            'color_changed': current_data.get('color', '') != previous_data.get('color', ''),
                            'position_changed': (
                                current_data.get('x', 0) != previous_data.get('x', 0) or
                                current_data.get('y', 0) != previous_data.get('y', 0)
                            )
                        }
                    })

        return changes

    def _handle_canvas_deletion(self, event: CanvasEvent):
        """处理Canvas删除"""
        if event.canvas_path in self.canvas_states:
            del self.canvas_states[event.canvas_path]
            logger.info(f"Canvas已删除: {event.canvas_path}")

    def _record_canvas_changes(self, event: CanvasEvent, changes: List[Dict]):
        """记录Canvas变化到学习活动"""
        try:
            for change in changes:
                # 这里可以根据变化类型调用不同的记录方法
                if change['type'] == 'node_modified':
                    # 特别是黄色节点（用户理解输入）的变化
                    node_data = change.get('new_data', {})
                    if node_data.get('color') == '6':  # 黄色节点
                        self.activity_capture.capture_node_interaction(
                            user_id="system",  # 需要从上下文获取实际用户ID
                            canvas_path=event.canvas_path,
                            node_id=change['node_id'],
                            interaction_type="text_input",
                            details={
                                "text_length": len(node_data.get('text', '')),
                                "timestamp": event.timestamp.isoformat(),
                                "change_type": "content_update"
                            }
                        )

        except Exception as e:
            logger.error(f"记录Canvas变化失败: {e}")

    def get_canvas_state(self, canvas_path: str) -> Optional[Dict]:
        """获取Canvas状态"""
        return self.canvas_states.get(canvas_path)

    def get_listening_status(self) -> Dict:
        """获取监听状态"""
        return {
            "is_listening": self.is_listening,
            "watched_paths": list(self.observers.keys()),
            "tracked_canvases": len(self.canvas_states),
            "event_handlers_count": len(self.event_handlers)
        }


class CanvasEventDispatcher:
    """Canvas事件分发器"""

    def __init__(self):
        self.handlers: List[Callable[[CanvasEvent], None]] = []
        self.event_queue = asyncio.Queue()
        self.is_dispatching = False
        self.dispatch_thread = None

    def register_handler(self, handler: Callable[[CanvasEvent], None]):
        """注册事件处理器"""
        self.handlers.append(handler)

    def unregister_handler(self, handler: Callable[[CanvasEvent], None]):
        """注销事件处理器"""
        if handler in self.handlers:
            self.handlers.remove(handler)

    def dispatch_event(self, event: CanvasEvent):
        """分发事件"""
        try:
            # 异步分发事件
            asyncio.run_coroutine_threadsafe(
                self._async_dispatch_event(event),
                self._get_or_create_event_loop()
            )
        except Exception as e:
            logger.error(f"分发事件失败: {e}")

    async def _async_dispatch_event(self, event: CanvasEvent):
        """异步分发事件"""
        await self.event_queue.put(event)

        if not self.is_dispatching:
            self.is_dispatching = True
            self.dispatch_thread = threading.Thread(
                target=self._dispatch_loop,
                daemon=True
            )
            self.dispatch_thread.start()

    def _dispatch_loop(self):
        """事件分发循环"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def process_events():
            while True:
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=1.0
                    )

                    for handler in self.handlers:
                        try:
                            handler(event)
                        except Exception as e:
                            logger.error(f"事件处理器执行失败: {e}")

                except asyncio.TimeoutError:
                    # 检查是否还有待处理的事件
                    if self.event_queue.empty():
                        break
                except Exception as e:
                    logger.error(f"处理事件队列失败: {e}")

        loop.run_until_complete(process_events())
        loop.close()
        self.is_dispatching = False

    def _get_or_create_event_loop(self):
        """获取或创建事件循环"""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop


# 导入uuid模块
import uuid