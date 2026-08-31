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
import hashlib
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

#: 唯一网络出口缝 (CARD-TEST-bark-autostub): 生产路径常规行为不变;
#: 唯一可观察差异 = import 后对 urllib.request.urlopen 的重绑不再被观察
_urlopen = urllib.request.urlopen


#: hash 域后缀形态 — 用于把「原样域」与「hash 域」分开, 保证两域不重叠
_HASH_TAIL = re.compile(r"-[0-9a-f]{16}$")
#: key 主体安全上限 (Codex-C1a HIGH: NAME_MAX=255, 232 字节合法目录名会让
#: daily-review.<key>.state.json 超限; 100 + 1 + 16 + 前后缀 ≪ 255)
_KEY_MAX_BYTES = 100


def vault_key(vault_id: str) -> str:
    """vault 目录名 → 文件名/通知 id 安全 key (CARD-C1a 命名空间规则唯一定义点)。

    两域设计 (Codex-C1a B2/H1 处置):
      原样域 — ASCII 短名 (canvas-vault) 原样返回; 但排除恰好长得像 hash 域
               后缀 (-<16hex> 结尾) 的名字与超长名;
      hash 域 — 其余 (中文库名 / 超长名 / 撞后缀形态) slug 化并追加 sha256
               前 16 hex (64 bit — 8 hex 时 2^16 生日构造即可撞, 已实测)。
    两域互不重叠 → 不同目录名撞 key 只剩 64bit hash 碰撞一条路。state 文件名
    (daily_review_run.state_path) / push.sh 锁 / Bark 有效 id 共用本函数,
    同一 vault 三处 key 恒等 (push.sh 经 python 调用本函数, 不再 basename)。
    """
    # 目录名按字面精确处理, 不裁剪空白 — str.strip() 会吞 Unicode 空白,
    # 令 "foo" 与 "foo\xa0" 两个不同目录名撞 key (Codex-C1a round2 实测)
    raw = str(vault_id or "").rstrip("/").rsplit("/", 1)[-1] or "vault"
    safe = re.sub(r"[^0-9A-Za-z._-]", "-", raw).strip("-.")
    if (safe == raw and not _HASH_TAIL.search(raw)
            and len(raw.encode("utf-8")) <= _KEY_MAX_BYTES):
        return safe
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{(safe or 'vault')[:_KEY_MAX_BYTES]}-{digest}"


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


def send(notification: dict, vault_id: str | None = None) -> int:
    cfg = load_key()
    if cfg is None:
        return 2
    server, device_key = cfg
    noti_id = notification["id"]
    group = notification.get("group", "canvas复习")
    if vault_id:
        # CARD-C1a: vault 维度只在 send 侧组合 — payload.notification.id 的值
        # 是 A2 冻结契约不可改; 有效去重 id / 分组在这里追加 vault, 防第二
        # vault 同日同 id 覆盖第一 vault 的手机通知。vault_id 缺省 (旧 payload)
        # 走原样 id, 加性兼容。
        noti_id = f"{noti_id}-{vault_key(vault_id)}"
        group = f"{group}·{vault_id}"
    body = json.dumps(
        {
            "device_key": device_key,
            "title": notification["title"],
            "body": notification["body"],
            "group": group,
            "id": noti_id,
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
            with _urlopen(req, timeout=TIMEOUT_S) as resp:
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
    return send(noti, payload.get("vault_id"))


if __name__ == "__main__":
    sys.exit(main())
