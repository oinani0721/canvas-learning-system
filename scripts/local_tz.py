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
import time
from datetime import datetime, timedelta, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo


class _SystemLocalTZ(tzinfo):
    """C 库按 TZ **逐时刻**解析的本地时区（含 DST 转换规则）。

    ZoneInfo 认不出的 TZ 写法（POSIX 串 "EST5EDT,M3.2.0,M11.1.0" / "UTC0"、
    前导冒号 ":Asia/Shanghai"）C 库都认得。直接返回
    `datetime.now().astimezone().tzinfo` 只是**此刻**的固定偏移 —— 拿它去换算
    别的时刻，会在 DST 切换两侧错一小时，进而错日、错桶（Codex r2 HIGH-1 实测：
    `TZ=EST5EDT,M3.2.0,M11.1.0` 下 `2026-11-02T04:30Z` 被算成 11-02 00:30，
    而 C 库给的是 11-01 23:30 —— 差一天）。

    ⛔ 不把 `time.timezone` / `time.altzone` 缓存成模块级常量（Python 文档那份
    LocalTimezone 示例就是那么写的）：`tzset()` 之后它们会变，缓存等于把时区
    固化在 import 时刻 —— 与本模块「每次调用现取」的口径直接冲突。
    """

    def _isdst(self, dt: datetime) -> bool:
        tt = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.weekday(), 0, -1)
        return time.localtime(time.mktime(tt)).tm_isdst > 0

    def utcoffset(self, dt):
        return timedelta(seconds=-(time.altzone if self._isdst(dt) else time.timezone))

    def dst(self, dt):
        return timedelta(seconds=time.timezone - time.altzone) if self._isdst(dt) else timedelta(0)

    def tzname(self, dt):
        return time.tzname[1 if self._isdst(dt) else 0]


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
            # ⛔ 回落到 C 库**逐时刻**解析的本地时区, 不是 /etc/localtime, 也不是
            #    此刻的固定偏移:
            #    · 读 /etc/localtime 等于无视 TZ (r1 HIGH-1: 上海宿主 + TZ=UTC0
            #      把 2026-07-31T16:30Z 算成 08-01, C 库本地是 07-31);
            #    · datetime.now().astimezone().tzinfo 只是此刻的偏移, 换算别的
            #      时刻会在 DST 两侧错一小时 (r2 HIGH-1)。
            return _SystemLocalTZ()
    try:
        parts = Path("/etc/localtime").resolve().parts
        return ZoneInfo("/".join(parts[parts.index("zoneinfo") + 1 :]))
    except Exception:  # noqa: BLE001 — 无 /etc/localtime (裸容器 / 非类 Unix)
        pass
    return datetime.now().astimezone().tzinfo  # 末档：固定偏移，无 .key
