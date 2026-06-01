"""共享题面 registry — V-10 评分对象漂移修复 (Sprint 2 · S2-1).

## 为什么存在

`generate_question` 生成 `question_text` 后, `score_answer` 评分时需要拿到
**这道题的真实题面**。旧实现 (exam_tools.py:435-462) 没有回读真实题面, 而是用
`find_node_across_canvases(node_id)` 取**节点正文**当题面 → 评分对象漂移 (V-10):
出题用 tip 原话出针对题, 评分却按泛节点概念评 → BKT/FSRS 信号从根源污染。

本 registry 让 `generate_question` 把真实题面存下, `score_answer` 按 `question_id`
回读, 保证评分针对的就是用户看到的那道题。

## 参考成熟案例 (DD-04)

复用 `app.api.v1.endpoints.exam_quick._QUESTION_STORE` 的 ring buffer 模式
(MVP-α 路径已验证可用, exam_grade.py:82 正确回读)。本模块把同一模式提取为
MCP 路径可共享的独立服务。

## 当前边界 + 统一计划 (S2-2)

- in-memory ring buffer, 进程重启清空 (与 MVP-α 一致, MVP 阶段可接受)
- 当前 MCP 路径用本 registry, MVP-α 路径用各自的 `_QUESTION_STORE` (两份并存)
- Sprint 2 · S2-2 (CanvasGraphEpisodeV1 + 持久化 questions_registry) 落地后,
  两路径统一到持久化存储, 重启不丢, 届时可把 V-10 降级路径收紧为 fail-closed
"""

from __future__ import annotations

from threading import Lock
from typing import Any, Dict, Optional

_REGISTRY: Dict[str, Dict[str, Any]] = {}
_MAX_ENTRIES = 500  # ring buffer 上限, 超出按 FIFO 淘汰最旧
_lock = Lock()


def put_question(question_id: str, question_text: str, **meta: Any) -> None:
    """存一道题的真实题面 (供 score_answer 回读).

    Args:
        question_id: generate_question 生成的唯一 ID
        question_text: LLM 生成的真实题面 (含 tip 引用 / wikilink 邻居引用)
        **meta: 可选附加上下文 (node_id / session_id 等), 便于调试追溯
    """
    if not question_id or not question_text:
        return
    with _lock:
        existing = _REGISTRY.get(question_id)
        if existing is not None:
            existing["question_text"] = question_text
            existing.update(meta)
            return
        if len(_REGISTRY) >= _MAX_ENTRIES:
            oldest_key = next(iter(_REGISTRY))
            _REGISTRY.pop(oldest_key, None)
        _REGISTRY[question_id] = {"question_text": question_text, **meta}


def get_question(question_id: str) -> Optional[Dict[str, Any]]:
    """按 question_id 回读真实题面 record. 不存在返回 None.

    Returns:
        含 ``question_text`` 及附加 meta 的 dict, 或 None (registry 未命中)
    """
    if not question_id:
        return None
    with _lock:
        record = _REGISTRY.get(question_id)
        return dict(record) if record is not None else None


def clear_registry() -> None:
    """清空 registry (仅供测试使用)."""
    with _lock:
        _REGISTRY.clear()
