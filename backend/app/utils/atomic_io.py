"""Round-23 Story 8.2 · Atomic file I/O helpers.

修复 Round-22/ChatGPT 报告 stage 2 task 2 (JSON fallback 不原子化).

现状: backend 内 4+ 处 json.dump 直接写入 (LearningMemoryClient / neo4j_edge_client /
review / canvas_service) — 写半道崩溃会损坏数据.

修复: 提供原子写入 helpers (tempfile + os.replace + per-file lock).
- ``atomic_write_json`` — 同步原子 JSON 写
- ``atomic_write_text`` — 同步原子文本写
- ``atomic_write_json_async`` / ``atomic_write_text_async`` — async 包装 (asyncio.to_thread)

参考: app/services/candidate_service.py:_atomic_write_frontmatter 模板.

[Source: _bmad-output/research/round-23-chatgpt-dr-result-and-synthesis-2026-05-08.md Stage 2 Task 2]
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# Per-file lock 防并发写竞争 (同 file path → 同 lock)
_file_locks: dict[str, threading.Lock] = {}
_locks_meta_lock = threading.Lock()


def _get_file_lock(file_path: str | Path) -> threading.Lock:
    """获取 per-file 锁 (避免并发写覆盖)."""
    key = str(Path(file_path).resolve())
    with _locks_meta_lock:
        if key not in _file_locks:
            _file_locks[key] = threading.Lock()
        return _file_locks[key]


def atomic_write_text(
    file_path: str | Path,
    content: str,
    *,
    encoding: str = "utf-8",
) -> None:
    """原子写文本到 file_path.

    实现: NamedTemporaryFile (同目录, .tmp 后缀) → os.replace 原子替换.
    保证: 写半道崩溃 → 旧文件保留, 不会出现部分写入.

    Args:
        file_path: 目标文件路径.
        content: 文本内容.
        encoding: 文件编码 (默认 utf-8).

    Raises:
        OSError: 创建 tempfile 或 os.replace 失败.
    """
    p = Path(file_path)
    lock = _get_file_lock(p)

    with lock:
        # NamedTemporaryFile 必须在 file_path 同一文件系统才能 atomic replace
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            delete=False,
            dir=p.parent,
            prefix=f".{p.name}.",
            suffix=".tmp",
        ) as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = tmp.name

        try:
            os.replace(tmp_path, p)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise


def atomic_write_json(
    file_path: str | Path,
    data: Any,
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
    default: Any = None,
) -> None:
    """原子写 JSON 到 file_path.

    Args:
        file_path: 目标文件路径.
        data: JSON 可序列化对象.
        indent: 缩进空格 (默认 2).
        ensure_ascii: True 强制 ASCII 转义 (默认 False 保留中文).
        default: json.dump default 参数 (如 str 转换不可序列化对象).

    Raises:
        TypeError: data 不可 JSON 序列化.
        OSError: 文件 IO 失败.
    """
    serialized = json.dumps(
        data, indent=indent, ensure_ascii=ensure_ascii, default=default
    )
    atomic_write_text(file_path, serialized)


async def atomic_write_text_async(
    file_path: str | Path,
    content: str,
    *,
    encoding: str = "utf-8",
) -> None:
    """async 版 ``atomic_write_text`` (asyncio.to_thread 包装)."""
    await asyncio.to_thread(atomic_write_text, file_path, content, encoding=encoding)


async def atomic_write_json_async(
    file_path: str | Path,
    data: Any,
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
    default: Any = None,
) -> None:
    """async 版 ``atomic_write_json`` (asyncio.to_thread 包装)."""
    await asyncio.to_thread(
        atomic_write_json,
        file_path,
        data,
        indent=indent,
        ensure_ascii=ensure_ascii,
        default=default,
    )
