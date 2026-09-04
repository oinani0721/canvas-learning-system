"""批次3' 2-4 — 统一学习事件日志 (MEM-FLYWHEEL-2026-07-22, 对账 schema 四要素)。

`<vault>/learning_events.jsonl` append-only: frontmatter 仍是真相源 (不改架构),
日志提供「过程可回放、图可重建」兜底 — 会话记忆层从「丢图即永失」变为可重放。

Schema 四要素 (ChatGPT 对账采纳):
  - event_id: 幂等键 (调用方构造稳定值, 重放/重试不双写)
  - event_version: schema 版本 (当前 1)
  - recorded_at / effective_at: 双时间戳 (记录时刻 vs 业务生效时刻,
    补录历史事件时两者分离)
  - event_type: 限 9 类核心动作 (EVENT_TYPES), 未知类型拒绝 — 防事件膨胀
    (callout_ingested 2026-07-23 对账评审入集后 "8 类" 注释曾未同步)

写点 (批次3' 接入 4 个, node_derived 留批次4' 拆分补强):
  backend: candidate_created (蒸馏) / candidate_accepted / candidate_disputed
           (= dispute 三件套第三件「可追溯」suppression log) / session_archived
  vault:   answer_scored / answer_abandoned (quiz-answer) / exam_created
           (start-exam-board) — SKILL 静态 python 直接 append 同一文件
"""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

EVENT_VERSION = 1

#: 核心动作白名单 — 新增类型必须走对账评审, 不得随手扩
#: (callout_ingested 经 2026-07-23 燃料策略对账批次5' 方案评审加入)
EVENT_TYPES = frozenset(
    {
        "node_derived",
        "exam_created",
        "answer_scored",
        "answer_abandoned",
        "candidate_created",
        "candidate_accepted",
        "candidate_disputed",
        "session_archived",
        "callout_ingested",
    }
)

_write_lock = threading.Lock()


def _log_path() -> Path:
    from app.config import settings

    canvas_base = getattr(settings, "CANVAS_BASE_PATH", None) or "/vaults/canvas-vault"
    return Path(canvas_base) / "learning_events.jsonl"


def append_event(
    event_type: str,
    event_id: str,
    node_id: str = "",
    payload: Optional[dict[str, Any]] = None,
    effective_at: Optional[str] = None,
) -> bool:
    """append-only 落一条学习事件; event_id 已存在 → 幂等跳过。

    永不抛异常 (记录失败不得影响主链) — 返回 False 表示未写入
    (幂等跳过或 IO 失败, 区别见日志)。
    """
    try:
        if event_type not in EVENT_TYPES:
            logger.warning("[learning-events] 拒绝未知 event_type=%r (9 类白名单)", event_type)
            return False
        if not event_id:
            logger.warning("[learning-events] 拒绝空 event_id (幂等键必填)")
            return False

        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        with _write_lock:
            # 幂等: 文件内已有该 event_id → 跳过 (日志量级小, 全文扫描可接受;
            # 大文件时可换尾部 N 行 + 索引)。
            # G3-2 (CARD-G3-2, schema §二/§6.2 A4.5): 查重改为 parsed-field
            # equality — 原子串匹配 (`json.dumps(event_id) in line`) 在任意
            # 历史行 payload 文本恰好含该 JSON 串形时会把新事件误判 duplicate
            # 而**零次落账** (丢一次真实事实)。幂等语义不变 (event_id 唯一),
            # 只修正查重实现的正确性; 无法解析的行不算命中 (留痕后跳过)。
            if path.exists() and path.stat().st_size > 0:
                # (round-2 HIGH: 空文件 seek(-1, SEEK_END) 抛 OSError, 守卫
                # 必须 size>0 才读尾字节 — 否则首事件永远写不进去)
                with open(path, encoding="utf-8") as f:
                    for line in f:
                        try:
                            record = json.loads(line)
                        except ValueError:
                            # 坏行 (截断/损坏) 不构成 duplicate 证据, 但要留痕
                            logger.warning(
                                "[learning-events] 账本存在无法解析的行 (截断/损坏), 查重跳过该行: %r", line[:80]
                            )
                            continue
                        if isinstance(record, dict) and record.get("event_id") == event_id:
                            return False
                # G3-2 LF 守卫 (schema §二 截断自愈): 尾行无换行时先补 LF 再
                # 追加 — 否则新事件粘进坏行连坐损坏 (Codex round-1 HIGH:
                # 预置 partial JSON 后 append 会把两个 JSON 粘成一行坏行)。
                with open(path, "rb") as bf:
                    bf.seek(-1, os.SEEK_END)
                    if bf.read(1) != b"\n":
                        with open(path, "a", encoding="utf-8") as tf:
                            tf.write("\n")
                        logger.warning("[learning-events] 检测到无换行结尾的尾行 (疑似截断), 已补 LF 隔离后再追加")
            now = datetime.now(timezone.utc).isoformat()
            record = {
                "event_id": event_id,
                "event_version": EVENT_VERSION,
                "event_type": event_type,
                "node_id": node_id,
                "recorded_at": now,
                "effective_at": effective_at or now,
                "payload": payload or {},
            }
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception as e:  # noqa: BLE001 — 日志兜底, 不炸主链
        logger.warning("[learning-events] append 失败 (主链不受影响): %s", e)
        return False
