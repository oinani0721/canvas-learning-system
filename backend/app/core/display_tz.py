"""单一时区来源 — backend 侧副本 (CARD-G6-9c · 用户裁定 D-18, 2026 年 9 月 7 日)。

⛔ **同源副本, 改一处必改另一处**: 本文件的 `display_tz()` 与仓根
`scripts/local_tz.py` 的同名函数**函数体逐字相同**, 由
`backend/tests/regression/test_g6_9c_single_tz_source.py` 门 ① 用
`inspect.getsource` 逐行比对锁定。

为什么是两份副本而不是一个模块: 另一份的消费者 `daily_review_pick.py` /
`daily_review_run.py` / `backend/scripts/vault_lint.py` 跑在 launchd 与 CLI
环境下, **不能 import backend**(`app/__init__.py` 在 import 期 `load_dotenv`
把 `.env` 灌进 `os.environ`, 且 `app/core/__init__.py` 连带拉起 agent_memory
与 request_cache) —— 那既是重依赖, 也会让「今天」随 `.env` 漂移。
纯 stdlib 是硬要求, 本副本同样只用 stdlib。

D-18 (2026-09-07 用户裁定, 推翻此前的 Asia/Shanghai 默认): 「今天」= 用户当前
所在地 = 机器本地时区。此前系统里有**四套**互不相认的时钟 —— review_overview
的 `_TZ_SHANGHAI`、daily_review_pick 的同名常量、vault_lint 的第三份复制、
runner 的机器本地 —— 换个时区跑「今天」就分叉。本函数是收敛后的唯一入口。

⛔ 消费侧必须**每次调用现取**, 禁止把返回值绑成模块级常量或 `lru_cache`:
进程运行期 `TZ` 可被改 (测试夹具 `TZ` + `time.tzset()` 就是这么做的, 且它
**不 reload 模块**), 求值时机一旦固化在 import 那一刻, 后续改时区对显示侧
完全无效 —— 门会恒绿而缺陷照旧。
"""

from __future__ import annotations

import calendar
import os
import time
from datetime import datetime, timedelta, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo


class _SystemLocalTZ(tzinfo):
    """C 库按 TZ **逐时刻**解析的本地时区（含 DST 与历史规则）。

    ZoneInfo 认不出的 TZ 写法（POSIX 串 "EST5EDT,M3.2.0,M11.1.0" / "UTC0"、
    前导冒号 ":Asia/Shanghai"）C 库都认得。两个被否掉的做法：
      · 读 `/etc/localtime` —— 那是宿主时区，压根不看 TZ；
      · `datetime.now().astimezone().tzinfo` —— 只是**此刻**的固定偏移，换算别的
        时刻会在 DST 两侧错一小时（`TZ=EST5EDT,…` 把 `2026-11-02T04:30Z` 算成
        11-02 00:30，C 库是 11-01 23:30）。

    ⛔ **必须自己实现 `fromutc()`**（Codex r3 HIGH-1）：默认实现拿 `utcoffset(dt)`
    去猜，而传进来的 dt 是 **UTC 值**、`_isdst()` 却把它当本地墙钟送进 `mktime()`
    —— 南半球 DST 上直接错日，且**连时刻都不守恒**（`TZ=:America/Santiago`，
    `2026-04-05T03:30Z` 被算成 04-05 00:30−04:00，转回 UTC 成了 04:30Z）。
    这里改为把 UTC 值换成 epoch 秒、直接问 `time.localtime()` —— 那是 C 库
    UTC→本地的正解，DST 与历史规则一并带上。

    ⛔ 不把 `time.timezone` / `time.altzone` 缓存成模块级常量（Python 文档那份
    LocalTimezone 示例就是那么写的）：`tzset()` 之后它们会变，缓存等于把时区
    固化在 import 时刻 —— 与本模块「每次调用现取」的口径直接冲突。

    ⚠️ 如实声明：`utcoffset()` / `dst()` 收到的是**本地墙钟**，DST 折叠时段本身
    有歧义（同一墙钟对应两个时刻），这里按 `mktime(tm_isdst=-1)` 让 C 库选一个，
    不区分 `fold`。本模块的用法是 UTC→本地（走 `fromutc`），不经过这条歧义路径。
    """

    @staticmethod
    def _dst_gap() -> int:
        """本时区 DST 的偏移跨度（秒）。非 DST 时区为 0。"""
        return max(0, time.timezone - time.altzone)

    def fromutc(self, dt: datetime) -> datetime:
        ts = calendar.timegm(dt.timetuple())
        lt = time.localtime(ts)
        # 折叠时段（回拨后重复的那一小时）：同一墙钟对应两个时刻。若把时刻往前
        # 推一个 DST 跨度还得到**相同的墙钟**，说明这是第二次出现 ⇒ fold=1。
        gap = self._dst_gap()
        fold = 1 if gap and time.localtime(ts - gap)[:6] == lt[:6] else 0
        return datetime(*lt[:6], microsecond=dt.microsecond, tzinfo=self, fold=fold)

    def _isdst(self, dt: datetime) -> bool:
        tt = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.weekday(), 0, -1)
        return time.localtime(time.mktime(tt)).tm_isdst > 0

    def utcoffset(self, dt):
        if dt is None:
            return None
        wall = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.weekday(), 0, -1)
        stamp = time.mktime(wall)
        gap = self._dst_gap()
        # mktime 对折叠墙钟返回**较早**那个时刻；dt.fold=1 时要取较晚的那个，
        # 否则 astimezone 回 UTC 会落在原时刻之外（Codex r3 HIGH-1 的
        # :America/Santiago 实测：转回去差了一小时）。
        if dt.fold and gap and time.localtime(stamp + gap)[:6] == wall[:6]:
            stamp += gap
        return timedelta(seconds=calendar.timegm(dt.timetuple()) - stamp)

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
