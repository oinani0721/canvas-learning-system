#!/usr/bin/env python3
"""M3 SessionEnd 归档 hook (2026-07-13, 路线图 v2) — Claude Code 原生环境。

SessionEnd 触发 (原生 CLI 可靠; Claudian 会在 3s 后杀子进程, 故 D-1 切换
是本管道的前置条件)。流程: stdin 读 SessionEnd payload → 解析 transcript
jsonl → 提取 user/assistant 文本轮次 → POST /api/v1/memory/archive/session。

批次0 0-4 (MEM-FLYWHEEL-2026-07-22): 后端不可达时归档请求落本地待发队列
(pending_archives.jsonl, session_id 幂等), 下次 hook 运行时自动补发 —
停机窗口结束的学习会话不再永久丢失。全程 best-effort: 任何失败静默
退出 0, 绝不阻塞 session 关闭。
"""

import json
import os
import pathlib
import sys
import time
import urllib.request

BACKEND_URL = "http://localhost:8011/api/v1/memory/archive/session"
MIN_MESSAGES = 4  # 少于 4 条 = trivial session, 不归档
MIN_USER_MESSAGES = 2  # 归档计数修正 (轨道 B 2026-07-20, UAT D2 ⑥):
# assistant 在工具调用间产生多个 text 片段、各算一条 — 带工具的单轮问答
# 也能凑满 4 条总数 ("1 轮不归档"假设不成立, 召回测试 session 被误归档)。
# 加真实用户轮下限: user 角色 < 2 条不归档。
MAX_MESSAGES = 40  # 只送尾部 40 轮 (近因优先, 与后端 8000 字符截断对齐)
PER_MESSAGE_CHARS = 4000
TIMEOUT_S = 8

# ── 0-4 本地待发队列 ──
QUEUE_FILE = pathlib.Path(__file__).resolve().parent / "pending_archives.jsonl"
DEAD_FILE = pathlib.Path(__file__).resolve().parent / "pending_archives.dead.jsonl"
MAX_DRAIN_PER_RUN = 5  # 单次 hook 最多补发条数, 控制关停耗时
MAX_ATTEMPTS = 30  # 补发上限, 超过转 dead 文件留证


def parse_transcript(path: pathlib.Path) -> list:
    messages = []
    for line in path.read_text(errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if entry.get("isMeta"):
            continue
        etype = entry.get("type")
        if etype not in ("user", "assistant"):
            continue
        msg = entry.get("message") or {}
        content = msg.get("content")
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            # 只取 text block — tool_use/tool_result 不进归档
            text = "\n".join(
                b.get("text", "")
                for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            )
        else:
            continue
        text = text.strip()
        # 过滤 hook/命令注入轮次 (<system-reminder>/<command-name> 等包裹)
        if not text or text.startswith("<"):
            continue
        messages.append(
            {"role": msg.get("role") or etype, "content": text[:PER_MESSAGE_CHARS]}
        )
    return messages


def _post(record: dict, internal_key: str) -> bool:
    """POST 归档 payload。成功 True; 任何网络/HTTP 失败 False。"""
    request = urllib.request.Request(
        BACKEND_URL,
        data=json.dumps(record).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-CLS-Internal-Key": internal_key,
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=TIMEOUT_S)
        return True
    except Exception:
        return False


def _load_queue() -> list:
    if not QUEUE_FILE.is_file():
        return []
    entries = []
    for line in QUEUE_FILE.read_text(errors="replace").splitlines():
        try:
            entries.append(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            continue
    return entries


def _save_queue(entries: list) -> None:
    if not entries:
        QUEUE_FILE.unlink(missing_ok=True)
        return
    QUEUE_FILE.write_text(
        "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries)
    )


def _enqueue(record: dict) -> None:
    """幂等入队: 同 session_id 已在队则跳过。"""
    entries = _load_queue()
    sid = record.get("session_id")
    if any(e.get("record", {}).get("session_id") == sid for e in entries):
        return
    entries.append({"queued_at": time.time(), "attempts": 0, "record": record})
    _save_queue(entries)


def _drain(internal_key: str) -> None:
    """补发积压归档: 成功移除, 失败保留 (attempts+1), 超上限转 dead。"""
    entries = _load_queue()
    if not entries:
        return
    remaining, drained = [], 0
    for entry in entries:
        if drained >= MAX_DRAIN_PER_RUN:
            remaining.append(entry)
            continue
        drained += 1
        if _post(entry.get("record", {}), internal_key):
            continue  # 成功: 不保留
        entry["attempts"] = int(entry.get("attempts", 0)) + 1
        if entry["attempts"] >= MAX_ATTEMPTS:
            with DEAD_FILE.open("a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        else:
            remaining.append(entry)
    _save_queue(remaining)


def main() -> None:
    payload = json.load(sys.stdin)
    transcript_path = payload.get("transcript_path") or ""
    session_id = payload.get("session_id") or "unknown"
    vault_root = pathlib.Path(
        os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or "."
    )

    key_file = vault_root / ".obsidian" / "cls-internal-key.txt"
    internal_key = key_file.read_text().strip() if key_file.is_file() else ""

    # 先补发历史积压 (即使本次 session 不够归档门槛也要补)
    try:
        _drain(internal_key)
    except Exception:
        pass

    transcript = pathlib.Path(transcript_path).expanduser()
    if not transcript.is_file():
        return
    messages = parse_transcript(transcript)
    user_turns = sum(1 for m in messages if m.get("role") == "user")
    if len(messages) < MIN_MESSAGES or user_turns < MIN_USER_MESSAGES:
        return
    messages = messages[-MAX_MESSAGES:]

    record = {
        "session_id": session_id,
        "vault_id": vault_root.name,
        "messages": messages,
    }
    if not _post(record, internal_key):
        # 0-4: 后端不可达 → 落本地队列, 下次 hook 运行补发
        _enqueue(record)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # best-effort: 归档失败绝不阻塞 session 关闭
    sys.exit(0)
