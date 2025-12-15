"""
事务性文件操作管理器

提供原子性文件操作，确保Canvas文件更新的安全性。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-24
"""

import os
import shutil
import tempfile
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, Callable, List
import threading
from contextlib import contextmanager

# 平台兼容的文件锁实现
try:
    import fcntl  # Unix系统
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

try:
    import msvcrt  # Windows系统
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


class FileTransactionError(Exception):
    """文件事务异常"""
    pass


class FileTransactionManager:
    """文件事务管理器

    提供原子性文件操作，确保写入操作要么全部成功，
    要么全部失败，不会产生部分写入的情况。
    """

    def __init__(self, use_file_locking: bool = True):
        """初始化事务管理器

        Args:
            use_file_locking: 是否启用文件锁
        """
        self.use_file_locking = use_file_locking
        self._lock_registry = {}  # 文件锁注册表
        self._lock = threading.Lock()

    @contextmanager
    def atomic_write(self, file_path: str, mode: str = 'w', encoding: str = 'utf-8'):
        """原子性写入上下文管理器

        Args:
            file_path: 目标文件路径
            mode: 写入模式
            encoding: 文件编码

        Yields:
            file: 临时文件对象
        """
        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # 创建临时文件
        temp_fd, temp_path = tempfile.mkstemp(
            suffix='.tmp',
            prefix=f"{Path(file_path).stem}_",
            dir=Path(file_path).parent
        )

        try:
            # 获取文件锁（如果启用）
            if self.use_file_locking:
                self._acquire_file_lock(file_path)

            # 打开临时文件进行写入
            with os.fdopen(temp_fd, mode, encoding=encoding) as temp_file:
                yield temp_file

                # 确保数据写入磁盘
                temp_file.flush()
                os.fsync(temp_fd)

            # 原子性移动临时文件到目标位置
            shutil.move(temp_path, file_path)

            logger.debug(f"Atomic write completed for: {file_path}")

        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass

            logger.error(f"Atomic write failed for {file_path}: {e}")
            raise FileTransactionError(f"Failed to write file {file_path}: {e}")

        finally:
            # 释放文件锁（如果启用）
            if self.use_file_locking:
                self._release_file_lock(file_path)

    def atomic_update_json(self, file_path: str, update_func: Callable[[Dict], Dict]) -> Dict:
        """原子性更新JSON文件

        Args:
            file_path: JSON文件路径
            update_func: 更新函数，接收当前数据，返回新数据

        Returns:
            Dict: 更新后的数据
        """
        # 读取当前数据
        current_data = self._read_json_safely(file_path)

        # 应用更新
        updated_data = update_func(current_data)

        # 原子性写入
        with self.atomic_write(file_path, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)

        return updated_data

    def _read_json_safely(self, file_path: str) -> Dict:
        """安全读取JSON文件"""
        if not os.path.exists(file_path):
            return {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            raise FileTransactionError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            raise FileTransactionError(f"Failed to read {file_path}: {e}")

    def create_backup(self, file_path: str, backup_dir: Optional[str] = None) -> str:
        """创建文件备份

        Args:
            file_path: 要备份的文件路径
            backup_dir: 备份目录（可选）

        Returns:
            str: 备份文件路径
        """
        if not os.path.exists(file_path):
            raise FileTransactionError(f"File does not exist: {file_path}")

        if backup_dir is None:
            backup_dir = Path(file_path).parent / "backups"

        # 确保备份目录存在
        Path(backup_dir).mkdir(parents=True, exist_ok=True)

        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{Path(file_path).stem}_backup_{timestamp}{Path(file_path).suffix}"
        backup_path = Path(backup_dir) / backup_name

        # 复制文件
        shutil.copy2(file_path, backup_path)

        logger.info(f"Created backup: {backup_path}")
        return str(backup_path)

    def restore_from_backup(self, file_path: str, backup_path: str) -> bool:
        """从备份恢复文件

        Args:
            file_path: 目标文件路径
            backup_path: 备份文件路径

        Returns:
            bool: 是否恢复成功
        """
        if not os.path.exists(backup_path):
            logger.error(f"Backup file does not exist: {backup_path}")
            return False

        try:
            # 创建当前文件的备份
            if os.path.exists(file_path):
                self.create_backup(file_path)

            # 从备份恢复
            shutil.copy2(backup_path, file_path)

            logger.info(f"Restored {file_path} from {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False

    def _acquire_file_lock(self, file_path: str) -> None:
        """获取文件锁"""
        with self._lock:
            if file_path in self._lock_registry:
                self._lock_registry[file_path] += 1
            else:
                # 实际的文件锁实现
                try:
                    lock_file = f"{file_path}.lock"
                    # 使用不同的锁机制
                    if HAS_FCNTL:
                        # Unix系统
                        lock_fd = os.open(lock_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
                        fcntl.flock(lock_fd, fcntl.LOCK_EX)
                        self._lock_registry[file_path] = {"count": 1, "fd": lock_fd}
                    elif HAS_MSVCRT:
                        # Windows系统
                        lock_fd = os.open(lock_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
                        msvcrt.locking(lock_fd, msvcrt.LK_NBLCK, 1)
                        self._lock_registry[file_path] = {"count": 1, "fd": lock_fd}
                    else:
                        # 无锁支持，使用简单标记
                        self._lock_registry[file_path] = {"count": 1, "fd": None}
                except Exception as e:
                    # 锁获取失败，记录但不阻止执行
                    logger.warning(f"Failed to acquire file lock for {file_path}: {e}")
                    self._lock_registry[file_path] = {"count": 1, "fd": None}

    def _release_file_lock(self, file_path: str) -> None:
        """释放文件锁"""
        with self._lock:
            if file_path in self._lock_registry:
                lock_info = self._lock_registry[file_path]
                lock_info["count"] -= 1

                if lock_info["count"] <= 0:
                    # 实际释放文件锁
                    try:
                        if lock_info.get("fd") is not None:
                            # 关闭文件描述符会自动释放锁
                            os.close(lock_info["fd"])

                        # 删除锁文件
                        lock_file = f"{file_path}.lock"
                        if os.path.exists(lock_file):
                            os.unlink(lock_file)
                    except Exception as e:
                        logger.warning(f"Failed to release file lock for {file_path}: {e}")

                    del self._lock_registry[file_path]

    @contextmanager
    def transaction(self, files: List[str]):
        """多文件事务上下文管理器

        Args:
            files: 涉及的文件列表
        """
        # 获取所有文件的锁
        for file_path in files:
            self._acquire_file_lock(file_path)

        try:
            yield
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise FileTransactionError(f"Transaction failed: {e}")
        finally:
            # 释放所有文件的锁
            for file_path in files:
                self._release_file_lock(file_path)

    def verify_file_integrity(self, file_path: str) -> bool:
        """验证文件完整性

        Args:
            file_path: 文件路径

        Returns:
            bool: 文件是否完整
        """
        try:
            if not os.path.exists(file_path):
                return False

            # 检查文件大小
            if os.path.getsize(file_path) == 0:
                return False

            # 如果是JSON文件，验证格式
            if file_path.endswith('.json') or file_path.endswith('.canvas'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)

            return True

        except Exception as e:
            logger.error(f"File integrity check failed for {file_path}: {e}")
            return False

    def cleanup_old_backups(self, backup_dir: str, max_backups: int = 10) -> int:
        """清理旧备份

        Args:
            backup_dir: 备份目录
            max_backups: 最大备份数量

        Returns:
            int: 删除的备份数量
        """
        if not os.path.exists(backup_dir):
            return 0

        # 获取所有备份文件
        backup_files = []
        for file_path in Path(backup_dir).glob("*_backup_*.canvas"):
            backup_files.append((file_path.stat().st_mtime, file_path))

        # 按时间排序
        backup_files.sort(reverse=True)

        # 删除超出限制的备份
        deleted_count = 0
        for i, (mtime, file_path) in enumerate(backup_files[max_backups:], start=max_backups):
            try:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"Deleted old backup: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete backup {file_path}: {e}")

        return deleted_count


# 全局事务管理器实例
transaction_manager = FileTransactionManager()