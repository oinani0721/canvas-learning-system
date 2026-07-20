#!/usr/bin/env python3
"""M3 SessionEnd 归档 hook (2026-07-13, 路线图 v2) — Claude Code 原生环境。

SessionEnd 触发 (原生 CLI 可靠; Claudian 会在 3s 后杀子进程, 故 D-1 切换
是本管道的前置条件)。流程: stdin 读 SessionEnd payload → 解析 transcript
jsonl → 提取 user/assistant 文本轮次 → POST /api/v1/memory/archive/session。

后端双通道落库: 蒸馏结构化 (tips/errors → 主链) + 对话全文 episode
(→ __semantic 影子图, M2 隔离)。全程 best-effort: 任何失败静默退出 0,
绝不阻塞 session 关闭。
"""

import json
import os
import pathlib
import sys
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


def main() -> None:
    payload = json.load(sys.stdin)
    transcript_path = payload.get("transcript_path") or ""
    session_id = payload.get("session_id") or "unknown"
    vault_root = pathlib.Path(
        os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or "."
    )

    transcript = pathlib.Path(transcript_path).expanduser()
    if not transcript.is_file():
        return
    messages = parse_transcript(transcript)
    user_turns = sum(1 for m in messages if m.get("role") == "user")
    if len(messages) < MIN_MESSAGES or user_turns < MIN_USER_MESSAGES:
        return
    messages = messages[-MAX_MESSAGES:]

    key_file = vault_root / ".obsidian" / "cls-internal-key.txt"
    internal_key = key_file.read_text().strip() if key_file.is_file() else ""

    body = json.dumps(
        {
            "session_id": session_id,
            "vault_id": vault_root.name,
            "messages": messages,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        BACKEND_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-CLS-Internal-Key": internal_key,
        },
        method="POST",
    )
    urllib.request.urlopen(request, timeout=TIMEOUT_S)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # best-effort: 归档失败绝不阻塞 session 关闭
    sys.exit(0)
