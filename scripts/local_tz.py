"""单一时区来源 — launchd / CLI 侧副本 (CARD-G6-9c · 用户裁定 D-18, 2026 年 9 月 7 日)。

⛔ **同源副本, 改一处必改另一处**: 本文件的 `display_tz()` 与
`backend/app/core/display_tz.py` 的同名函数**函数体逐字相同**, 由
`backend/tests/regression/test_g6_9c_single_tz_source.py` 门 ① 用
`inspect.getsource` 逐行比对锁定。

为什么是两份副本而不是一个模块: 本文件的消费者 `daily_review_pick.py` /
`daily_review_run.py` / `backend/scripts/vault_lint.py` 跑在 launchd 与 CLI
环境下, **不能 import backend**(`app/__init__.py` 在 import 期 `load_dotenv`
把 `.env` 灌进 `os.environ`, 且 `app/core/__init__.py` 连带拉起 agent_memory
与 request_cache) —— 那既是重依赖, 也会让「今天」随 `.env` 漂移。
纯 stdlib 是硬要求。

D-18 (2026-09-07 用户裁定, 推翻此前的 Asia/Shanghai 默认): 「今天」= 用户当前
所在地 = 机器本地时区。此前系统里有**四套**互不相认的时钟 —— review_overview
的 `_TZ_SHANGHAI`、daily_review_pick 的同名常量、vault_lint 的第三份复制、
runner 的机器本地 —— 换个时区跑「今天」就分叉。本函数是收敛后的唯一入口。
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def display_tz():
    """显示/归日/桶位用时区：CANVAS_TZ 显式覆盖 (IANA 名) > 机器本地的 IANA 名
    (TZ 环境变量 → /etc/localtime 软链) > 固定偏移兜底。D-18 2026-09-07。
    无效 CANVAS_TZ 抛 ValueError (配置断裂要说话, 不静默退化)。"""
    name = os.environ.get("CANVAS_TZ")
    if name:
        try:
            return ZoneInfo(name)
        except Exception as e:  # noqa: BLE001 — ZoneInfoNotFoundError / ValueError 同一口径
            raise ValueError(f"CANVAS_TZ 无效: {name!r} ({type(e).__name__})") from e
    env_tz = os.environ.get("TZ")
    if env_tz:
        try:
            return ZoneInfo(env_tz)
        except Exception:  # noqa: BLE001 — TZ 也允许 "UTC0"/"EST5"/":Asia/X" 这类 POSIX 串
            # ⛔ 回落到**进程本地**, 不是 /etc/localtime (Codex r1 HIGH-1):
            #    TZ 已经把 C 库的本地时区改掉了, 去读软链等于无视 TZ ——
            #    实测上海宿主 + TZ=UTC0 时会把 2026-07-31T16:30Z 算成 08-01,
            #    而 C 库本地是 07-31, 静默错一天。
            return datetime.now().astimezone().tzinfo
    try:
        parts = Path("/etc/localtime").resolve().parts
        return ZoneInfo("/".join(parts[parts.index("zoneinfo") + 1 :]))
    except Exception:  # noqa: BLE001 — 无 /etc/localtime (裸容器 / 非类 Unix)
        pass
    return datetime.now().astimezone().tzinfo  # 末档：固定偏移，无 .key
