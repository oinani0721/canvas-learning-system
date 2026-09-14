"""单一时区来源 — backend 侧副本 (CARD-G6-9c · 用户裁定 D-18, 2026 年 9 月 7 日)。

⛔ **同源副本, 改一处必改另一处**: 本文件的共享定义与仓根
`scripts/local_tz.py` 逐字相同, 由
`backend/tests/regression/test_g6_9c_single_tz_source.py` 的对照门锁定。

另一份的消费者 (`daily_review_pick.py` / `daily_review_run.py` /
`backend/scripts/vault_lint.py`) 跑在 launchd 与 CLI 环境下, **不能 import
backend**(`app/__init__.py` 在 import 期 `load_dotenv` 会把 `.env` 灌进
`os.environ`) —— 所以需要两份纯 stdlib 副本; 本副本供 backend 进程使用。

D-18 (2026-09-07 用户裁定): 「今天」= 用户当前所在地 = 机器本地时区。
⛔ 消费侧必须**每次调用现取**, 禁止绑成模块级常量或 `lru_cache`。
"""

from __future__ import annotations

import calendar
import os
import re
import time
from datetime import datetime, timedelta, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# POSIX TZ 串 → 规格驱动的 tzinfo（Codex r4 HIGH-1 的根治）
#
# 包装 libc 的方案（_SystemLocalTZ）被否掉的原因: 墙钟→UTC 方向必须走
# `mktime`, 而它对**折叠墙钟**（回拨后重复的那一小时）选哪一侧是实现定义的
# —— 实测 NY `2026-11-01 05:45Z` 被算成 `01:45-05:00`（应为 -04:00）;
# `dst()`/折叠检测依赖的 `time.timezone-altzone` 又只是**当前**跨度,
# 上海 1991、Lord Howe 1985 这类历史跨度全错。POSIX TZ 规格本身是确定性的,
# 直接解析并按规则逐时刻判定, 这一整类歧义从构造上消失。
#
# TZ 解析次序（与 libc 语义对齐, 已实测）:
#   1. 交给 ZoneInfo —— 覆盖裸 IANA 名("America/New_York")、tzfile 简名
#      ("EST5EDT"/"EST") 与前导冒号(":Asia/Shanghai");
#   2. POSIX 规格串("UTC0"/"CST-8"/"EST5EDT,M3.2.0,M11.1.0"/"<+10:30>-10:30…");
#   3. 都不认 ⇒ UTC —— libc 对空串与垃圾 TZ 同样退化为 UTC。
# ---------------------------------------------------------------------------

#: POSIX TZ 语法。名字: ≥3 字母或 <...> 引用(内部可含 +/-/数字); 偏移: 西为正;
#: 日期: Jn(1..365 跳过 2/29) / n(0..365 含闰) / Mm.w.d; 切换时刻缺省 02:02:00。
_POSIX_TZ_RE = re.compile(
    r"^(?P<std>[A-Za-z]{3,}|<[^<>]+>)"
    r"(?P<std_off>[+-]?\d{1,3}(?::\d{1,2}(?::\d{1,2})?)?)?"
    r"(?:(?P<dst>[A-Za-z]{3,}|<[^<>]+>)"
    r"(?P<dst_off>[+-]?\d{1,3}(?::\d{1,2}(?::\d{1,2})?)?)?)?"
    r"(?:,(?P<start>J?\d{1,3}|M\d{1,2}\.\d\.\d)"
    r"(?:/(?P<stime>\d{1,3}(?::\d{1,2}(?::\d{1,2})?)?))?"
    r",(?P<end>J?\d{1,3}|M\d{1,2}\.\d\.\d)"
    r"(?:/(?P<etime>\d{1,3}(?::\d{1,2}(?::\d{1,2})?)?))?)?$"
)

#: POSIX 缺省切换时刻 = 当地 02:00:00（规格明文）。⛔ 曾误写成加两分钟: 切换后头两
#: 分钟的墙钟比 C 库慢一档, 而整点/半点探针一格都踩不到 —— 门必须逐分钟扫切换点。
_POSIX_DEFAULT_TRANSITION = 2 * 3600


def _posix_offset_seconds(text: str) -> int:
    """POSIX 偏移串 → **UTC 偏移秒**。POSIX 正值=西(EST5 ⇒ UTC-5), 故取负。"""
    sign = -1 if text.startswith("-") else 1
    parts = text.lstrip("+-").split(":")
    secs = 0
    for i, mul in enumerate((3600, 60, 1)):
        if i < len(parts):
            secs += int(parts[i]) * mul
    return -sign * secs


def _strip_name(name: str) -> str:
    return name[1:-1] if name.startswith("<") else name


def _parse_hms(text: str) -> int:
    parts = text.split(":")
    secs = 0
    for i, mul in enumerate((3600, 60, 1)):
        if i < len(parts):
            secs += int(parts[i]) * mul
    return secs


def _parse_rule(date_txt: str, time_txt: str | None):
    """'M3.2.0'/'J100'/'65' (+ 可选 '/hh[:mm[:ss]]') → (kind, a, b, c, secs)。"""
    secs = _POSIX_DEFAULT_TRANSITION
    if time_txt:
        secs = _parse_hms(time_txt)
    if date_txt.startswith("M"):
        mon, week, dow = (int(x) for x in date_txt[1:].split("."))
        if not (1 <= mon <= 12 and 1 <= week <= 5 and 0 <= dow <= 6):
            return None
        return ("M", mon, week, dow, secs)
    jul = date_txt.startswith("J")
    n = int(date_txt[1:] if jul else date_txt)
    # ⛔ 两种写法的取值域不同, 一个范围管两边会放行 J0: `Jn` 是 1..365（不数闰日）,
    #    裸 `n` 是 0..365（数闰日）。C 库对 J0 整串拒收, 混用会让我们比它宽。
    if not ((1 <= n <= 365) if jul else (0 <= n <= 365)):
        return None
    return ("J" if jul else "n", n, None, None, secs)


def _rule_epoch(rule, year: int) -> int:
    """规则在该年的**当地墙钟** epoch 秒（按切换前生效偏移换算由调用方做）。"""
    kind, a, b, c, secs = rule
    if kind == "M":
        mon, week, dow = a, b, c
        first_wd = datetime(year, mon, 1).weekday()  # 0=周一
        pydow = 6 if dow == 0 else dow - 1  # POSIX 0=周日 → Python 0=周一
        day = 1 + (pydow - first_wd) % 7 + 7 * (week - 1)
        if day > calendar.monthrange(year, mon)[1]:
            day -= 7  # 第 5 周 = 该月最后一个
        return calendar.timegm((year, mon, day, 0, 0, 0)) + secs
    yday = a + (1 if (kind == "J" and calendar.isleap(year) and a >= 60) else 0) - (1 if kind == "J" else 0)
    return calendar.timegm((year, 1, 1, 0, 0, 0)) + yday * 86400 + secs


def parse_posix_tz(spec: str):
    """POSIX TZ 串 → `_PosixTZ`；语法/范围不合法返回 None（调用方决定退化或拒绝）。

    给了夏令时名却**不写切换规则**（`CET-1CEST` / `EST5EDT`）不是非法输入 —— 规格
    把规则留给实现定义。C 库按 tzset(3) 去读 `<zoneinfo>/posixrules` 的规则,「只把
    两侧偏移换成 TZ 里写的值」; 本机实测 `posixrules` 与 `America/New_York` 逐字节
    相同（sha256 一致）, 内嵌规则即 `M3.2.0,M11.1.0`（当地 02:00 = POSIX 缺省切换
    时刻）。故此处按该默认规则补齐, 而不是判整串不可用。
    ⛔ 不要改回 `return None`: 那会让整串退回 UTC（`display_tz()` 的 POSIX 档）,
       `TZ=CET-1CEST` 的机器上每年 603 小时（6.9%）归错日 —— 而且生产者自报的
       `display_tz` 也一并退成 "UTC", 与 generated_at 的 +00:00 自洽, 于是复习总览
       的桶位门自洽校验查不出来, **错得不会报错**, 这才是它危险的地方。
    对齐范围如实声明: **2007..2037** 与 C 库零分歧（7 个规格 × 156 万点逐分钟, 覆盖
    夏令时差 −2h / −1h / +1h / +1.5h / +4h 五族）。区间外**有分歧且不打算对齐**:
    ≤2006 —— C 库在那里用的是 posixrules **整张历史转换表**（America/New_York 的历史,
    例如 1975 年 2 月 23 日那次能源危机提前实施, 根本不是 M3.2.0）; ≥2038 —— C 库的
    32 位表止于 2037-11-01 且不外推, 直接丢掉 DST, 是它自己退化。跟随一张宿主 tzfile
    的历史表会把平台数据引进一个规格驱动的实现, 这里**只跟它在作业区间内的规则形态**。
    ⛔ 给这两份副本加新的「与 C 库逐时刻取值相等」样本时, 年份必须落在 2007..2037,
       否则红的是 C 库的边界而不是本实现的缺陷。
    """
    m = _POSIX_TZ_RE.match(spec)
    if not m:
        return None
    g = m.groupdict()
    std_off = _posix_offset_seconds(g["std_off"]) if g["std_off"] else 0
    if g["dst"] is None:
        return _PosixTZ(spec, _strip_name(g["std"]), std_off, None, None, None, None)
    dst_off = _posix_offset_seconds(g["dst_off"]) if g["dst_off"] else std_off + 3600
    if g["start"] is None or g["end"] is None:
        # 规则整段缺席 ⇒ 补 posixrules 的默认规则。
        # ⛔ 这里**故意**用字面量而不提成模块级常量: 源同源门只逐行比对 shared 名单里的
        #    七个定义（`parse_posix_tz` 在内, 模块级常量**不在**）—— 写在函数体里这几行
        #    才会被门比到; 提成常量就成了静默漂移面。
        # 注: start / end 同属正则里**一个**可选组, 二者必同生共死（125 个结构化样本 +
        #    2 万次随机 fuzz 实测无「只给一侧」形态）, 故本条件等价于「规则整段缺席」。
        # 春季: C 库把前跳钉在当地**标准**时 02:00; 我们的 s = rule_epoch + secs − std_off,
        #   令其相等即 secs = 7200 = POSIX 缺省切换时刻 ⇒ 直接走 _parse_rule 的缺省。
        start = _parse_rule("M3.2.0", None)
        # 秋季: C 库把回拨钉在当地**标准**时 01:00, 而 POSIX 的「/时刻」语义指的是**切换前
        #   生效**的那一侧（end 之前生效的是夏令侧）。我们的 e = rule_epoch + secs − dst_off,
        #   C 库的是 rule_epoch + 3600 − std_off ⇒ secs = 3600 + dst_off − std_off。
        #   ⛔ 不要写死 `_parse_rule("M11.1.0", None)`（= 固定 7200）: 那只在夏令时差恰为
        #      +1 小时时才与本式重合 —— 而那正是「省略 dst 偏移」那一族的特征, 只测那一族
        #      就会把子族结论当成全族结论。实测（2007..2037 秋季回拨窗逐分钟, 156 万点）:
        #      写死 02:00 时 IST-1GMT0(Δ=−1h) 3720 分钟、ABC-1DEF-5(Δ=+4h) 5580、
        #      NZST-12NZDT-13:30(Δ=+1.5h) 930、AAA5BBB7(Δ=−2h) 5580 与 C 库不符;
        #      按本式现算后四者全部归零。secs 可为负（Δ < +1h 时）, `_rule_epoch` 是纯
        #      算术加法, 负值合法; 故直接构造规则元组而不过 `_parse_rule`（它的 `/hh`
        #      文本语法表达不了负时刻）。
        end = ("M", 11, 1, 0, 3600 + dst_off - std_off)
    else:
        start = _parse_rule(g["start"], g["stime"])
        end = _parse_rule(g["end"], g["etime"])
    if start is None or end is None:
        return None
    return _PosixTZ(spec, _strip_name(g["std"]), std_off, _strip_name(g["dst"]), dst_off, start, end)


class _PosixTZ(tzinfo):
    """按 POSIX TZ 规格**逐时刻判定**的时区。`key` = 规格串（生产者可自报）。

    折叠（回拨重复墙钟）: fold=0 取第一次出现 = **偏移较大**的一侧, fold=1 取第二次。
    空缺（前跳跳过的墙钟）: fold=0 取切换前 = **偏移较小**的一侧, fold=1 取切换后。
    按偏移大小选侧而非按夏令时身份 —— 负偏移差的规格（标准侧比另一侧偏移大, 如
    `IST-1GMT0,M10.5.0,M3.5.0/1`）两者方向相反, 写死身份会把 fold 语义整个颠倒。
    `fromutc` 只走 epoch→规则判定, 不经 `mktime`。
    """

    __slots__ = ("_spec", "_std_name", "_std_off", "_dst_name", "_dst_off", "_start", "_end")

    def __init__(self, spec, std_name, std_off, dst_name, dst_off, start, end):
        self._spec = spec
        self._std_name = std_name
        self._std_off = std_off
        self._dst_name = dst_name
        self._dst_off = dst_off
        self._start = start
        self._end = end

    @property
    def key(self) -> str:
        return self._spec

    def _dst_window(self, year: int) -> tuple[int, int]:
        # 切换瞬间 = 规则墙钟 − 切换前生效偏移（start 前是 std, end 前是 dst）
        s = _rule_epoch(self._start, year) - self._std_off
        e = _rule_epoch(self._end, year) - self._dst_off
        return s, e

    def _in_dst(self, ts: int) -> bool:
        # 候选年下界是 y-2 而不是 y-1（Codex r5 HIGH-1）: 规则的生效时刻能**滚出名义年**,
        # 于是包住某个元旦的那个跨年季度其名义起始年是 y-2, 三年候选窗够不着它。反例
        # `AAA1BBB0,365/3,365/2` 在 `2024-01-01T00:30Z` 上整整错一天（正确窗口
        # start(2022)=2023-01-01T04:00Z → end(2023)=2024-01-01T02:00Z）, 且**转回 UTC 仍守恒**
        # ⇒ 时刻守恒判据抓不到它, 只有墙钟/归日那一侧能抓。
        # ⛔ 滚年有**三条互相独立**的来源, 别只记住第一条（2007..2037 元旦周逐小时实测红点数）:
        #   ① 平年的裸 `n=365` = 「1月1日 + 365 天」= 次年元旦（`…,365/3,365/2` 红 46 点）;
        #   ② `Jn` / 裸 `n` 叠 `/N`（POSIX 到 167h, 本正则放行到 999:99:99）
        #      —— `…,J365/167,J365/167` 红 4433 点;
        #   ③ `Mm.w.d` 落在年末再叠 `/N`, **既无裸 n 也无 Jn** —— `…,M12.5.0/167,M12.5.0/167`
        #      红 2325 点; 且逐年不同（末周日是 12/25 的年份就不滚）。
        #   三者在 y-2 下全部归零。
        # 上下界推导（按本文件正则**实际允许**的取值域, 不是估计）: `_rule_epoch` 的返回值
        # ∈ [年初, 年初 + 365 天 + 切换时刻]; 切换时刻与偏移都写成
        # `\d{1,3}(?::\d{1,2}(?::\d{1,2})?)?` ⇒ 各 < 42 天 ⇒ 窗口端点偏离名义年 < 84 天。
        # 于是 [s(Y), e(Y+1)) ⊆ (Y 年初 − 84 天, Y+2 年初 + 365 天 + 84 天), 反解得能包住
        # ts 的名义年只可能落在 [y−2, y+1]。
        # 实测佐证: 4088 个规格 × 873 个探针时刻（极端偏移 / `/167:59:59` / Jn·裸 n·Mm.w.d
        # 全组合）与 C 库逐点对照 —— (y−1, y, y+1) 有 17 个规格共 1274 点分歧;
        # (y−2 … y+1) 分歧 0; 再扩到 (y−3 … y+2) 无任何增量。
        # ⛔ 作用域如实声明: 上述对照的采样年份都 ≥ 2007。**1972 以前不作为对齐目标** ——
        #   macOS libc 对 POSIX 规格串的转换表自 EPOCH_YEAR 起算, 1970 之前根本不套用 DST
        #   规则, 那一段无论候选年取多宽都会与规格文本分歧, 红的是 C 库的边界不是本实现。
        y = time.gmtime(ts).tm_year
        for year in (y - 2, y - 1, y, y + 1):  # 规则可滚出名义年, 季度起始年最早到 y-2
            s, e = self._dst_window(year)
            if s <= e:  # 窗口落在同一年内（北半球形态）
                if s <= ts < e:
                    return True
            else:  # 跨年季度（南半球形态）= [start(year), end(year+1))
                if s <= ts < self._dst_window(year + 1)[1]:
                    return True
        return False

    def _offsets_for_wall(self, dt: datetime) -> int:
        dst_off = self._dst_off
        if dst_off is None:
            return self._std_off
        # ⛔ 必须 naive 副本: Py3.14 的 aware timetuple() 会经 tz 协议取 tm_isdst,
        #    直接传 aware dt 会 timetuple→dst→utcoffset→这里→timetuple 无限递归。
        wall = calendar.timegm(dt.replace(tzinfo=None).timetuple())
        d_ok = self._in_dst(wall - dst_off)
        s_ok = not self._in_dst(wall - self._std_off)
        hi = max(self._std_off, dst_off)  # 较大偏移 = 回拨前 / 前跳后
        lo = min(self._std_off, dst_off)
        if d_ok and s_ok:  # 折叠: 第一次出现 = 偏移较大侧
            return hi if not dt.fold else lo
        if d_ok:
            return dst_off
        if s_ok:
            return self._std_off
        return lo if not dt.fold else hi  # 空缺: 切换前 = 偏移较小侧

    def utcoffset(self, dt):
        if dt is None:
            return None
        if self._dst_off is None:
            return timedelta(seconds=self._std_off)
        return timedelta(seconds=self._offsets_for_wall(dt))

    def dst(self, dt):
        if dt is None or self._dst_off is None:
            return timedelta(0)
        off = self.utcoffset(dt)  # 注解上可 None(签名未标), 运行时 dt 恒非 None
        return (off or timedelta(0)) - timedelta(seconds=self._std_off)

    def tzname(self, dt):
        if dt is None or self._dst_off is None:
            return self._std_name
        off = self._offsets_for_wall(dt)
        return self._dst_name if off == self._dst_off else self._std_name

    def fromutc(self, dt: datetime) -> datetime:
        ts = calendar.timegm(dt.replace(tzinfo=None).timetuple())
        dst_off = self._dst_off
        if dst_off is None:
            off, fold = self._std_off, 0
        else:
            in_dst = self._in_dst(ts)
            off = dst_off if in_dst else self._std_off
            other = self._std_off if in_dst else dst_off
            # 折叠只出现在偏移**减小**的那次切换之后: 当前落在较小偏移侧时, 把时刻
            # 倒推两侧之差, 若换到了另一侧, 说明这个墙钟刚以较大偏移出现过 ⇒ 第二次。
            # 判据是偏移大小不是夏令时身份 —— 负偏移差的规格里较小的那个才是 DST 侧。
            fold = 1 if off < other and self._in_dst(ts - (other - off)) != in_dst else 0
        wall = dt.replace(tzinfo=None) + timedelta(seconds=off)  # naive 运算, 不触 tz 协议
        return wall.replace(tzinfo=self, fold=fold)


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
    if env_tz is not None:
        if not env_tz:
            return ZoneInfo("UTC")  # 空 TZ = UTC, 与 libc 一致
        for cand in (env_tz, env_tz.lstrip(":")):  # ":Asia/Shanghai" 与裸 IANA 名
            try:
                return ZoneInfo(cand)
            except Exception:  # noqa: BLE001
                pass
        posix = parse_posix_tz(env_tz)
        if posix is not None:
            return posix  # .key = 规格串 ⇒ 生产者 payload 可自报, 消费侧同源重建
        return ZoneInfo("UTC")  # 垃圾 TZ 当 UTC —— 与 libc 的退化一致
    try:
        parts = Path("/etc/localtime").resolve().parts
        return ZoneInfo("/".join(parts[parts.index("zoneinfo") + 1 :]))
    except Exception:  # noqa: BLE001 — 无 /etc/localtime (裸容器 / 非类 Unix)
        pass
    return datetime.now().astimezone().tzinfo  # 末档：固定偏移，无 .key
