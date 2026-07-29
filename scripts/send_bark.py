#!/usr/bin/env python3
"""Bark 推送器 (DAILY-REVIEW-PUSH-2026-07-29, 终审 A5 硬化版)。

安全契约:
  - key 只存 ~/.config/canvas-review/bark.key (600), 不进 URL/argv/日志
  - POST https://api.day.app/push JSON body (非 GET 路径拼接 — 免 URL
    编码地雷 + 免板名进进程参数)
  - 同日稳定 notification id → Bark 端幂等更新 (本地 at-least-once +
    服务端同 id 覆盖, 终审 A4 网络 exactly-once 的正解)
  - 内容形态: 明文具体板名 (用户 2026-07-29 拍板; E2E 加密进 backlog)

退出码: 0 = 服务端明确接受 (HTTP 200 且 body code==200)
        2 = 未配置 key (跳过, 不算错)
        1 = 发送失败 (调用方走 osascript 兜底)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

KEY_FILE = Path(
    os.environ.get("BARK_KEY_FILE")
    or Path.home() / ".config" / "canvas-review" / "bark.key"
)
DEFAULT_SERVER = "https://api.day.app"
TIMEOUT_S = 10
RETRIES = 2


def load_key() -> tuple[str, str] | None:
    """读 key 文件 → (server, device_key)。兼容整段 URL 或裸 key。

    Code-Review L4: 格式不合法 (贴了裸域名/空串) 按未配置处理并给具体
    提示, 不进重试循环报误导性的 net= 错误。
    """
    if not KEY_FILE.exists():
        print("bark skip(未配置) — 写入 ~/.config/canvas-review/bark.key 后启用")
        return None
    raw = KEY_FILE.read_text(encoding="utf-8").strip().rstrip("/")
    if raw.startswith("http"):
        server, _, key = raw.rpartition("/")
    else:
        server, key = DEFAULT_SERVER, raw
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", key) or not server.startswith("http"):
        print("bark skip(key格式不合法 — 应为 Bark app 复制的推送 key)")
        return None
    return (server, key)


def send(notification: dict) -> int:
    cfg = load_key()
    if cfg is None:
        return 2
    server, device_key = cfg
    body = json.dumps(
        {
            "device_key": device_key,
            "title": notification["title"],
            "body": notification["body"],
            "group": notification.get("group", "canvas复习"),
            "id": notification["id"],
        },
        ensure_ascii=False,
    ).encode("utf-8")

    last_err = "unknown"
    for attempt in range(1 + RETRIES):
        if attempt:
            time.sleep(2 * attempt)
        req = urllib.request.Request(
            f"{server}/push", data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                http = resp.status
                try:
                    code = json.loads(resp.read().decode("utf-8")).get("code")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    code = None
            if http == 200 and code == 200:
                print(f"bark accepted http={http} code={code}")
                return 0
            last_err = f"http={http} code={code}"
        except urllib.error.HTTPError as e:
            last_err = f"http={e.code}"
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = f"net={type(e).__name__}"
    print(f"bark failed {last_err}")  # 永不打印 key/URL
    return 1


def main():
    ap = argparse.ArgumentParser(description="Bark 推送 (payload 不进命令行)")
    ap.add_argument("--payload", required=True, help="今日复习.json 路径")
    args = ap.parse_args()
    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    noti = payload.get("notification")
    if not noti:
        print("bark skip(无可推内容)")
        return 2
    return send(noti)


if __name__ == "__main__":
    sys.exit(main())
