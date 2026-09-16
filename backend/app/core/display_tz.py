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
#: 日期: Jn(1..365 跳过 2/29) / n(0..365 含闰) / Mm.w.d; 切换时刻缺省 02:00:00
#: （BASE 这里原写 02:02:00, 与下方 `_POSIX_DEFAULT_TRANSITION` 和 `_parse_rule` 的实际
#:  返回值矛盾, 也与它自己 :57 那条注释矛盾 —— Codex r2 点名, 本卡顺手改正）。
#: ⛔ 位宽一律 `\d+`、名字一律 `+`/`*`, **不用** `{1,3}` 这类人为窄口径（Codex r10 M1/M2）。
#: 本机实测: C 库对数字字段的位数**没有上限**（`AAA00000001` = +1h 照收）、前导零随意
#: （`M03.02.00` / `J0001` / `/0002` 全收）、名字可以只有 1 个字符（`A1`）也可以是**空**
#: 引用名（`<>1`）。原来的 `{1,3}` / `{1,2}` / `{3,}` 把这些**合法**串一律拒掉 ⇒ 退 UTC
#: ⇒ 与机器本地时区归日不同。25704 组合的对拍里，正则窄口径一项就占误拒的 95%。
#: ⛔ **裸名不是 `[A-Za-z]+`**: C 库的裸名一直吃到遇见数字 / `+` / `-` / `,` 为止,
#:    中间的任何可打印字符都算名字 —— `ABC<DEF>2` 的名字是 `ABC<DEF>`（它的 tzname
#:    打成 `ABC_DEF_`）、`ABC DEF2` 的名字是 `ABC DEF`。原来的 `[A-Za-z]{3,}` 把这类
#:    整串判无 std 偏移而拒, 占对拍里 240 条误拒。
#:    （⚠️ 这里原本还有一句「控制字符仍排除」—— 那条口径已被下面 L4 那段推翻, 现只排除 NUL。）
#: ⛔ **引用名分支必须排在裸名之前**: 正则的 `|` 是左优先, 裸名字符集含 `<`,
#:    若裸名在前, `<+10:30>-10:30<+11>-11,…` 会被吃成名字 `<` + 偏移 `+10:30`, 整串错解。
#: ⛔ 光排前面**不够**, 还要 `(?!<)` 挡住**回溯**（Codex r11 H2）: 引用名分支在
#:    `<BBB2` 上失败后, 正则会退回裸名分支把 `<BBB` 当名字收下, 而 C 库对
#:    `AAA1<BBB2` / `AAA1<<BBB>>2` / `<<AAA>>1` 一律拒 —— 名字**开头**是 `<` 就必须是
#:    闭合引用名。名字**中间**的 `<` 不受影响（`ABC<DEF>2` C 库接受, 名字是 `ABC<DEF>`）。
#: ⛔ 数字集是 `0-9` 不是 `\d`（Codex r11 M2）: `\d` 连**非 ASCII 数字**一起匹配, 于是
#:    `ABC٦1`（阿拉伯数字）、`ABC１1`（全角）被当成「名字里混进了数字」而整串拒,
#:    而 C 库把它们当普通名字字符收下（tzname 打成 `ABC__`）。分隔语义只认 ASCII 数字。
#: ⛔ 裸名**不排除**控制字符, 只排除 NUL（Codex r11 L4）: 上一版裸名侧写 `\x00-\x1f`
#:    而引用名侧 `[^<>]*` 一直是放行的 —— `AAA\t1` 拒而 `<A\tAA>1` 收, 两边口径打架,
#:    而给出的理由（「不能让 `.key` 带控制字符进 API」）对两侧同样适用, 解释不了这个差异。
#:    C 库两种写法都接受。现统一为**都放行**: `.key` 的安全由 ④（严格 UTF-8 可编码）
#:    与响应序列化门负责, 那才是真正会炸的那一层; 控制字符本身能被 JSON 转义。
#:    NUL 仍排除 —— 它由 ③ 单独守（引用名内部是它唯一的显形位置）。
#: 值域不在正则里判 —— 交给 ⑤（ASCII + 范围）、⑦（名字和式）、⑧（量级）、⑨（规则可解析）。
#: ⛔ 结尾锚是 `\Z` **不是** `$`: Python 的 `$` 在末尾换行**之前**就收尾, 用它的话
#:    `AAA-1BBB,M3.2.0,M11.1.0\n` 照样匹配 ⇒ 误收（C 库对它退 UTC）。`\Z` 才是绝对串尾。
#:    这个差异在本卡咬过两次（r9 为它专门加了一条尾部空白检查, r11 删掉那条后又撞上）。
#: ⛔ 名字字符类里 `0-9` **写在 `\x00` 之后**时要当心: `\x00` 恰好吃两位十六进制,
#:    所以 `[^\x000-9…]` 其实是 `\x00` + `0-9` 两项 —— 语义对但极易读成 `\x000` + `-9`。
#:    这里把 NUL 放到最后, 让每一项都一眼可辨。
#: ⛔ **引用名的内容是 `<` 到第一个 `>` 之间的一切**, 含 `<` 与数字（r12 扩维度后实测）:
#:    `<AAA1<DEF>2` 的名字是 `AAA1<DEF`（C 库 tzname 打成 `AAA1_DEF`）、`<AAA1DEF>2`
#:    的名字是 `AAA1DEF`。原来写 `[^<>]*` 把内容里的 `<` 排除掉, 于是这类串走到裸名
#:    分支被当成 `<AAA` + 偏移 `1` ⇒ **误收 1666 条**（组合对拍扩到 98532 组合才暴露）。
#:    现写 `[^>\x00]*`: 只排除 `>`（它是终止符）与 NUL（③ 单独守）。
#:    与 `<<AAA>>1` 拒并不矛盾 —— 那串的引用名是 `<AAA`, 之后剩下的 `>1` 不是合法偏移。
#: ⛔ 两侧对 `<` 开头的名字**口径不同**, 这不是笔误（Codex r11 M1 追问后逐例实测）:
#:    · **std 侧**: `<` 开头时扫到 `>` 为止 —— 扫得到就按引用名解析（内容含 `<` 或 `>`
#:      即非法）, **扫不到 `>` 就整个当裸名**（`<` 本身计入名字与长度）。
#:      实测: `<AAA1` 收（名字 `<AAA`, tzname `_AAA`）、`<<AAA1` 收、`<A<B1` 收、
#:      `<1` 收（名字就是 `<`）、`<<AAA>>1` **拒**（有 `>` ⇒ 走引用名 ⇒ 内容含 `<`）、
#:      `<AA>A1` **拒**（引用名 `AA` 之后的 `A1` 不是合法偏移）。
#:      故第三支 `<[^>0-9+,\-\x00]*` 专门表达「`<` 开头且其后没有 `>`」。
#:    · **dst 侧**: `<` 开头**必须**闭合, 没有裸名回退。实测 `AAA1<BBB2` / `AAA1<<BBB2`
#:      / `AAA1<2` 全拒, 而 `AAA1<BBB>2` / `AAA1<>2` 收。故 dst 侧保留 `(?!<)`。
_POSIX_TZ_RE = re.compile(
    r"^(?P<std><[^>\x00]*>|(?!<)[^0-9+,\-\x00]+|<[^>0-9+,\-\x00]*)"
    r"(?P<std_off>[+-]?\d+(?::\d+(?::\d+)?)?)?"
    r"(?:(?P<dst><[^>\x00]*>|(?!<)[^0-9+,\-\x00]+)"
    r"(?P<dst_off>[+-]?\d+(?::\d+(?::\d+)?)?)?)?"
    r"(?:,(?P<start>J?\d+|M\d+\.\d+\.\d+)"
    r"(?:/(?P<stime>\d+(?::\d+(?::\d+)?)?))?"
    r",(?P<end>J?\d+|M\d+\.\d+\.\d+)"
    r"(?:/(?P<etime>\d+(?::\d+(?::\d+)?)?))?)?\Z"
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
    """剥掉引用名的尖括号; 裸名原样返回。

    ⛔ 只判 `startswith("<")` 是错的（Codex r11 M1）: `<AAA1` 这种**未闭合**的串会被
    剥成 `AA` —— 首尾各删一个字符, 把名字最后一个字符也吃掉, 于是名字长度少算两个
    字节、接受域边界跟着漂（实测 `<`+`A`*511+`1` C 库拒而本实现收）。
    正则加 `(?!<)` 之后这类串已进不到这里, 但本函数是独立定义、也被同源门单独比对,
    判据要自己站得住。
    """
    if len(name) >= 2 and name.startswith("<") and name.endswith(">"):
        return name[1:-1]
    return name


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


def _zoneinfo_key_candidates(env_tz: str) -> tuple[str, ...]:
    """把 `TZ` 的各种**路径**形态归一成可喂给 `ZoneInfo` 的 IANA 名候选（按优先序）。

    C 库把 `TZ` 先当**文件路径**解析（绝对路径直接打开, 相对路径相对 `TZDIR`,
    默认 `/usr/share/zoneinfo`）, 解析不了才退 POSIX 规格串。本机实测（Codex r10 M4/M5）:

    ========================================  =========  ==========
    TZ                                        C 库        原实现
    ========================================  =========  ==========
    `:Asia/Shanghai`                          +08:00     +08:00
    `::Asia/Shanghai`                         **UTC**    +08:00 ⛔误收
    `/usr/share/zoneinfo/Asia/Shanghai`       +08:00     UTC ⛔误拒
    `./Asia/Shanghai` / `Asia//Shanghai`      +08:00     UTC ⛔误拒
    ========================================  =========  ==========

    ⛔ 冒号只剥**一个**: 原实现用 `lstrip(":")` 剥掉全部前导冒号, 于是
    `::Asia/Shanghai` 被剥成合法名 —— 而 C 库剥一个之后剩下 `:Asia/Shanghai`,
    当作路径打不开, 退 UTC。这是**误收 + 误算**（整整差 8 小时）, 比误拒严重。

    ⚠️ 如实声明一处**有意的收紧**: 绝对路径只接受**路径里含 `zoneinfo` 段**的那种,
    取其后的部分作 IANA 名。C 库会打开任意路径的 tzfile（`TZ=/tmp/whatever`）,
    本实现不跟 —— `TZ` 是环境变量, 按它去开任意文件是不必要的输入面。落在这个
    收紧外的路径退 UTC（= 原行为）。
    """
    raw = env_tz[1:] if env_tz.startswith(":") else env_tz  # C 库只剥一个冒号
    cands = [env_tz, raw]
    # ⛔ 必须**先确认那个文件真的在**（Codex r11 H1）: 上一版只要路径里出现 `zoneinfo`
    #    段就截后缀, 于是 `/does-not-exist/zoneinfo/Asia/Shanghai`、`zoneinfo/Asia/Shanghai`、
    #    `::/usr/share/zoneinfo/Asia/Shanghai` 三串全被认成上海（C 库都给 UTC）——
    #    **误收 + 误算, 整整差 8 小时**。改成先落到文件系统上验一次。
    # ⛔ 顺带修好 `..`（Codex r11 M4）: `Asia/../Asia/Shanghai` C 库接受, 而纯字符串归一
    #    处理不了它。`resolve()` 会把 `..` / `.` / `//` 一并解决, 不必自己拼规则。
    # ⚠️ TZDIR 固定取 `/usr/share/zoneinfo`（本机 C 库的默认值）; 本实现不读 TZDIR 环境
    #    变量, 那是与 C 库的一处窄分歧, 如实登记。
    base = Path(raw) if raw.startswith("/") else Path("/usr/share/zoneinfo") / raw
    try:
        if base.is_file():
            parts = base.resolve().parts
            if "zoneinfo" in parts:
                cands.append("/".join(parts[parts.index("zoneinfo") + 1 :]))
    except OSError:  # 路径过长 / 权限 / 符号链接环 —— 一律按「不是时区文件」处理
        pass
    return tuple(dict.fromkeys(c for c in cands if c))


def parse_posix_tz(spec: str):
    """POSIX TZ 串 → `_PosixTZ`；语法/范围不合法返回 None（调用方决定退化或拒绝）。

    给了夏令时名却**不写切换规则**（`CET-1CEST` / `EST5EDT`）不是非法输入 —— 规格
    把规则留给实现定义。C 库按 tzset(3) 去读 `<zoneinfo>/posixrules` 的规则,「只把
    两侧偏移换成 TZ 里写的值」; 本机实测 `posixrules` 与 `America/New_York` 逐字节
    相同（sha256 一致）, 内嵌规则即 `M3.2.0,M11.1.0`（当地 02:00 = POSIX 缺省切换
    时刻）。故此处按该默认规则补齐, 而不是判整串不可用。
    ⛔ 不要改回 `return None`: 那会让整串退回 UTC（`display_tz()` 的 POSIX 档）,
       `TZ=CET-1CEST` 的机器上平年 603 / 闰年 604 小时（约 6.9%）归错日 —— 而且生产者自报的
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
    # ① 长度上限**已删除**（Codex r11 M5）。r9 加它是为了防 ReDoS: 当时
    #    `"A"*4000 + "!"` 要跑 0.475 s、8000 字符 1.875 s, 最后还只是返回 None。
    #    ⛔ 但 r11 把正则里的 `{1,3}` / `{1,2}` / `{3,}` 一律放宽成 `+` / `*` 之后,
    #       指数回溯**跟着消失了**（同一条 4000 字符坏串现在 0.012 ms, 快了约 40 倍）——
    #       产生灾难性回溯的正是那些**有界**量词的嵌套, 不是串长。
    #    于是 1024 从「性能防线」退化成**纯误拒**: C 库接受 `AAA` + 2000 个 `0` + `1`
    #    这类合法的前导零长串并给 −01:00, 而这条上限把它挡在门外, 换不回任何收益。
    #    ⚠️ 谁要再加长度上限, 先跑一遍那条 4000 字符坏串的计时, 别照抄这段历史。
    m = _POSIX_TZ_RE.match(spec)
    if not m:
        return None
    g = m.groupdict()
    # ② 尾部换行**不再单独拒**（Codex r11 L4 连带推翻）。这条的来历与去处值得留着:
    #    r9 加它是因为正则的 `$` 在**末尾换行之前**收尾 ⇒ `AAA-1BBB,M3.2.0,M11.1.0\n`
    #    能匹配, 而 C 库对它退 UTC。当时给的理由是「不让控制字符进 `.key`」。
    #    ⛔ 但 r11 把裸名的控制字符放行之后（引用名侧本来就放行, 两边口径必须一致）,
    #       那个理由自己站不住了; 而它挡住的 `AAA-1\n` / `AAA-1BBB\n` 恰恰是 C 库
    #       **接受**的（把换行吃进 dst 名）—— 于是它从「防线」变成纯误拒。
    #    现在靠正则本身区分, 而那要求结尾锚是 `\Z` 不是 `$`（见正则上方那条注释）:
    #    **带显式规则**的串尾部多一个换行 ⇒ `\Z` 不匹配 ⇒ 拒, 与 C 库一致;
    #    **无规则**的串尾部换行会被裸名吃掉 ⇒ 收, 也与 C 库一致。
    #    ⛔ 删掉本条之后第一次跑对拍, 红的就是 `…,M11.1.0\n` —— 当时还是 `$`,
    #       它在末尾换行前收尾, 于是那串被误收。两处改动是一组, 不能只做一半。
    #    `.key` 的安全由 ④（严格 UTF-8 可编码）与响应序列化门守, 那才是会炸的那层。
    # ③ NUL: **活的防线, 唯一显形位置是引用名内部**。正则的引用名写作 `<[^<>]+>`,
    #    而 `[^<>]` 是**放行** NUL 的 —— 于是 dst 名或 std 名的尖括号**里面**嵌一个 NUL
    #    的串能一路匹配到这里, 只有这条能拒。反过来, 放在串尾、或放在偏移与 dst 名之间
    #    的 NUL 由正则先拒, 到不了这一层（实测三处位置各自归属见门表）。
    # ⛔ 这条注释本身被写错过一次: 上一版只拿「引用名**外**」的两个位置实测, 就据此
    #    写成了「不可达死分支」—— 样本在「NUL 在名字内 / 名字外」这一维上只取到一个值,
    #    而那一维恰好决定结论。同一形状本轮出现三次（另两次: 名字长度的单名上限 vs 和式、
    #    量纲变异只改 std 名那一行）, 记在这里当路标。
    # 输入面不止环境变量: 桶位门会用本函数重建生产者时区, 而 `display_tz` 是 JSON 自报值,
    #    JSON 字符串可以携带码位 U+0000。
    if "\x00" in spec:
        return None
    # ④ 可严格 UTF-8 编码: 不可编码的串整个不接受。放行会让代理字符留在 `.key` 里,
    #    一路进 API 响应、在 `JSONResponse` 的编码边界抛（本卡 r5→r6 在这里栽过两次:
    #    先是严格 encode 直接抛导致**启动失败**, 再是 surrogateescape 放行把失败挪到
    #    **响应出口** —— 修复只是移位。不接受才是两处都不炸）。
    try:
        spec.encode("utf-8")
    except UnicodeEncodeError:
        return None
    # ⑤ 所有数字字段只收 **ASCII** 数字并逐字段查范围（Codex r9 M5）。Python 的 `\d`
    #    连全角一起匹配, 而 C 库对 `M３.2.0` / `/２` 这类整串拒收（实测退 UTC）。
    #    范围逐条对齐 C 库实测: 切换时刻小时 ≤167（168 拒）、分钟 ≤59（60 拒）、
    #    秒 ≤60（61 拒, 60 接受）; 偏移的小时**不设**上限, 它的取舍见 ⑧。
    for _txt, _hmax in ((g["std_off"], None), (g["dst_off"], None), (g["stime"], 167), (g["etime"], 167)):
        if not _txt:
            continue
        _f = _txt.lstrip("+-").split(":")
        if not all(x.isascii() and x.isdigit() for x in _f):
            return None
        if _hmax is not None and int(_f[0]) > _hmax:
            return None
        if len(_f) > 1 and int(_f[1]) > 59:
            return None
        if len(_f) > 2 and int(_f[2]) > 60:
            return None
    for _txt in (g["start"], g["end"]):
        if _txt is not None and not _txt.lstrip("JM").replace(".", "").isascii():
            return None
    # ⑥ 标准偏移必填: C 库对**所有**缺它的形态整串拒收（实测 `ABC` / `<AAA>` /
    #    `<AAA><BBB>,M3.2.0,M11.1.0` 都退 UTC）。上一轮只在省略规则那一支查, 漏了
    #    另外两支（Codex r9 M3）。
    if not g["std_off"]:
        return None
    # ⑦ 名字长度: C 库把两个名字**连同各自的 NUL 终止符**存进同一个 512 字节缓冲区
    #    (macOS tzcode 的 `TZ_MAX_CHARS`), 所以这是一条**和式**约束而不是单名上限:
    #      带 dst ⇒ len(std) + len(dst) + 2 ≤ 512; 无 dst ⇒ len(std) + 1 ≤ 512。
    #    220 例网格实测零分歧（std 名 × dst 名各取边界两侧, 含多字节名）。
    # ⛔ 上一轮写的「每个名字 ≤507 字节」是把和式**塌成了单名上限** —— 当时的样本
    #    std 名恒为 `AAA`（3 字节）, 507 只是 512−3−2 在**那个子族**里的特例。两个方向
    #    的错都真实发生: `<A×507>-1<B×3>,…` 合法却判超限（误拒）; `<A×512>-1` 这类
    #    无 dst 形态**根本没进**这条检查（误收 —— 本实现接受了 C 库拒绝的串, 比误拒糟）。
    # ⛔ 量纲是**字节**不是字符（本卡第三次栽在这一对上: awk 的 length()、r4 的
    #    `len(spec)`, 现在是这里）。能把两种量纲分开的是 `AAA0<中×170>`:
    #    和(字节) = 3 + 510 + 2 = 515 > 512 ⇒ 拒（与 C 库同）, 和(字符) = 3 + 170 + 2
    #    = 175 ⇒ 收 ⇒ 按字符算会**误收**。
    # ⚠️ `A×504 + 中×1`（507 字节 / 505 字符）**分不开**两种量纲 —— 512 与 510 都 ≤512,
    #    两种算法都给「收」。上一版注释写「按字符算这两条都会判反」是错的（Codex r10 L1）:
    #    一条样本要能证伪某个假设, 得让两个假设在它身上给出**不同**答案; 否则它只是
    #    一条正例, 不是区分点。
    # ⛔ **空名不占缓冲区**（Codex r10 对名字和式的补充, 本机实测）:
    #    `<A×511>-1<>,M3.2.0,M11.1.0` C 库**收**（511 + 1 = 512）, `<A×512>-1<>` 才拒。
    #    机械地给空 dst 名也加一个 NUL（511+0+2 = 513）会把它误拒。
    _name_bytes = sum(
        len(_strip_name(_nm).encode("utf-8")) + 1
        for _nm in (g["std"], g["dst"])
        if _nm is not None and _strip_name(_nm)
    )
    if _name_bytes > 512:
        return None
    std_off = _posix_offset_seconds(g["std_off"])
    # ⑧ 量级: Python 的 `tzinfo` 要求偏移**严格**小于 24 小时。
    #    ⚠️ 归因更正（Codex r9 L4）: C 库**不**拒这些串 —— 实测 `TZ=AAA24BBB` 时
    #    `time.tzset()` **成功**、`tm_gmtoff=-82800`; 抛的是 Python 的 `astimezone()`。
    #    所以这是**本实现为保证全年可表示而做的收紧**, 不能写成「跟随 C 库」。
    if abs(std_off) >= 86400:
        return None
    # ⑨ 规则必须能解析: C 库对 `AAA-1,J0,J0` 整串拒收, **无 dst 形态也一样**。
    #    上一轮在无 dst 分支提前 return, 规则根本没被验（Codex r9 M4）。
    _start_rule = _parse_rule(g["start"], g["stime"]) if g["start"] is not None else None
    _end_rule = _parse_rule(g["end"], g["etime"]) if g["end"] is not None else None
    if (g["start"] is not None and _start_rule is None) or (g["end"] is not None and _end_rule is None):
        return None
    # ⑩ 无 dst 名**且**无规则 ⇒ 真·无 DST。⛔ 只判 `g["dst"] is None` 是错的（Codex r10 H1）:
    #    C 库对 `AAA-1,M3.2.0,M11.1.0` 这类「无 dst 名但**带合法规则**」的串**照常实行 DST**
    #    —— 规则用 TZ **自带的**那套（实测 `AAA-1,M4.1.0,M10.1.0` 在 3/20 给 +1h、4/20 给 +2h,
    #    与带 dst 名的同规则串逐点相同, 而"整体退 posixrules"那种读法会在 3/20 给 +2h）,
    #    只有 dst **名**借 posixrules 的、dst 偏移取默认 std_off + 3600。
    #    漏掉这一支的后果不是误拒而是**误算**: 夏季整整差一小时 ⇒ 归日可能差一天。
    if g["dst"] is None and g["start"] is None:
        return _PosixTZ(spec, _strip_name(g["std"]), std_off, None, None, None, None)
    dst_off = _posix_offset_seconds(g["dst_off"]) if g["dst_off"] else std_off + 3600
    # dst 名: 自带则用自带; 无 dst 名而有规则时借 posixrules 的夏令名（本机实测 "EDT",
    # 与 posixrules ≡ America/New_York 逐字节相同这一事实一致）。
    # ⚠️ 同上: 字面量是历史选择, 模块级常量的同源缺口已由 r10 的 AST 门补上。
    dst_name = _strip_name(g["dst"]) if g["dst"] is not None else "EDT"
    # dst 侧与两侧之**差**同样要 < 24h —— `AAA12BBB-12` 两侧各自合法而差恰为 24h,
    # `utcoffset()` 算得出但 `dst()` / `timetuple()` 会抛。
    # ⚠️ 差值这一条是**过度拒绝**, 如实声明: C 库接受 `AAA12BBB-12,M3.2.0,M11.1.0`
    #    并在冬季给 −12h（那时不算 `dst()`）, 本实现却全年退 UTC。取舍依据: `dst()` 在
    #    夏季抛是**运行时**炸、落点不可预测; 退 UTC 是可预测的降级。
    if abs(dst_off) >= 86400 or abs(dst_off - std_off) >= 86400:
        return None
    if g["start"] is None or g["end"] is None:
        # 规则整段缺席 ⇒ 补 posixrules 的默认规则。
        # ⚠️ 这里写字面量而不提模块级常量, 是 r4 的历史选择: 当时源同源门只比 shared
        #    名单里的七个函数/类定义, 模块级常量**不在门内**, 写进函数体才比得到。
        #    Codex r10 M9 之后那个缺口已补（`test_two_copies_share_identical_module_level_constants`
        #    按 AST 枚举顶层赋值逐字比对）, 所以这条理由**已不成立**; 字面量保留只是
        #    为了不在负控锚点密集区做无行为变化的重构。
        # 春季: C 库把前跳钉在当地**标准**时 02:00, 与 POSIX 缺省一致 ⇒ 走 `_parse_rule` 缺省。
        start = _parse_rule("M3.2.0", None)
        # 秋季: C 库把回拨钉在当地**标准**时 01:00, 而 POSIX 的 `/时刻` 指**切换前生效**
        #   的那一侧（end 之前是夏令侧）⇒ secs = 3600 + dst_off − std_off。
        #   ⛔ 不要写死 `_parse_rule("M11.1.0", None)`（= 固定 7200）: 那只在夏令时差恰为
        #      +1 小时时才与本式重合, 而那正是「省略 dst 偏移」那一族的特征。实测
        #      （2007..2037 秋季回拨窗逐分钟, 156 万点）写死 02:00 时 IST-1GMT0(Δ=−1h)
        #      3720 分钟、ABC-1DEF-5(Δ=+4h) 5580、NZST-12NZDT-13:30(Δ=+1.5h) 930、
        #      AAA5BBB7(Δ=−2h) 5580 与 C 库不符; 按本式现算后四者全部归零。
        #      secs 在 Δ < −1h 时为负（3600 + Δ < 0 ⟺ Δ < −3600; Δ=0 代入得 3600 > 0 可反证）,
        #      `_rule_epoch` 是纯算术加法、负值合法, 故直接构造规则元组。
        end = ("M", 11, 1, 0, 3600 + dst_off - std_off)
    else:
        start, end = _start_rule, _end_rule
    return _PosixTZ(spec, _strip_name(g["std"]), std_off, dst_name, dst_off, start, end)


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
        #   ② `Jn` / 裸 `n` 叠 `/N`（POSIX 与本实现都到 167:59:60）
        #      —— `…,J365/167,J365/167` 红 4433 点;
        #   ③ `Mm.w.d` 落在年末再叠 `/N`, **既无裸 n 也无 Jn** —— `…,M12.5.0/167,M12.5.0/167`
        #      红 2325 点; 且逐年不同（末周日是 12/25 的年份就不滚）。
        #   三者在 y-2 下全部归零。
        # 上下界推导（按**当前接受域**穷举实测, 不是估计; 记 Y0 = 该年元旦）:
        # ⛔ 这段推导 r11 重算过一次（Codex r11 L2）: 旧版引的是「正则放行到 999:99:99」
        #    「|偏移| < 42 天」「省略规则分支 secs ≤ 49 小时」—— 那是 r9 之前的取值域。
        #    现在切换时刻由 ⑤ 卡在 ≤167:59:60、偏移由 ⑧ 卡在 <24 小时, 界**小得多**;
        #    结论不变但余量更大, 而写着失效的数字会让后人以为界是紧的、不敢再收。
        #   `_rule_epoch(r, Y) − Y0 ∈ [0, 373 天]` —— 规则日最多 366 天（裸 `n=365` 在闰年
        #     落到次年元旦, 再加 1）, 切换时刻上限 `167:59:60` = 整 7 天 ⇒ 366 + 7 = 373。
        #     逐条实测的最大值是 `…,365/167,365/167` 的 **371.96 天**, 371.96 < 373 ✓。
        #   `|偏移| < 1 天` —— ⑧ 要求两侧偏移各自 |·| < 24 小时, 省略 dst 偏移时取
        #     `std_off + 3600` 也仍在同一条检查之后（见 `parse_posix_tz` 的顺序）。
        #   ⇒ s(Y), e(Y) ∈ (Y0 − 1 天, Y0 + 374 天)。
        # 反解（⛔ 两个易错点: ① 跨年季度的上端是 **e(Y+1)**, 它相对的是 (Y+1) 的元旦而非 (Y+2) 的;
        #   ② 下界与上界的「够不到」余量**不一样大**, 别都写成 730 天）:
        #   上端 e(Y+1) > ts 需 (Y+1) 元旦 > ts − 374 天 ⇒ Y ≥ y−2
        #     （Y = y−3 时 ts − (y−2) 元旦 ≥ **730 天** > 374, 够不到）;
        #   下端 s(Y) ≤ ts 需 Y 元旦 ≤ ts + 1 天 ⇒ Y ≤ y+1
        #     （Y = y+2 时 (y+2) 元旦 − ts ≥ **365 天** > 1, 够不到 —— 这里是 365 不是 730）。
        # 故 (y−2, y−1, y, y+1) 充分且**紧**（紧: y−2 确有反例需要它, 见上面三条滚年来源）。
        # ⚠️ 「省略切换规则」那条分支的 end 用现算 secs（`3600 + dst_off − std_off`）:
        #   该分支已先把两侧偏移各自卡在 <24 小时, 故 |secs| < 49 小时 ≈ 2.04 天,
        #   仍远在 373 天的界内。
        # 实测佐证: 4088 个规格 × 873 个探针时刻（极端偏移 / `/167:59:59` / Jn·裸 n·Mm.w.d
        # 全组合）与 C 库逐点对照 —— (y−1, y, y+1) 有 17 个规格共 1274 点分歧;
        # (y−2 … y+1) 分歧 0; 再扩到 (y−3 … y+2) 无任何增量。
        # ⛔ 作用域如实声明: 上述对照的采样年份都 ≥ 2007。**1972 以前不作为对齐目标** ——
        #   macOS libc 对 POSIX 规格串的转换表自 EPOCH_YEAR 起算, 1970 之前根本不套用 DST
        #   规则, 那一段无论候选年取多宽都会与规格文本分歧, 红的是 C 库的边界不是本实现。
        y = time.gmtime(ts).tm_year
        for year in (y - 2, y - 1, y, y + 1):  # 规则可滚出名义年, 季度起始年最早到 y-2
            if not 1 <= year <= 9999:
                # `_rule_epoch` 的 M 分支走 `datetime(year, mon, 1)`, year∉[1,9999] 会抛。
                # ⛔ 这条是**本卡扩候选窗带来的新边界**（Codex r3 LOW-1）: BASE 的三年候选
                #    在 ts 落于公元 2 年时算的是 (1,2,3) 全合法, 扩到 y-2 后多出 year=0 ⇒
                #    `ValueError: year must be in 1..9999, not 0`。跳过越界年即与 BASE 同行为。
                # ⛔ 上界只能收到 9999 **不能收到 9998**（Codex r4 LOW-1）: 北半球分支不碰
                #    `year + 1`, 一刀切到 9998 会把合法的 9999 年季度整个跳过 —— 实测
                #    `AAA0BBB,M3.2.0,M11.1.0` 在 9999-07-01T23:30Z 上 BASE 给 +01:00 而
                #    那样改的 HEAD 给 +00:00。需要 `year + 1` 的只有下面的南半球分支,
                #    收窄放在那里。
                continue
            s, e = self._dst_window(year)
            # ⛔ `s <= e` 只说明「本年的 start 早于本年的 end」, **不等于**窗口落在同一
            #    日历年内 —— 反例 `WART4WARST,J1/0,J365/25` 的 2024 窗口是
            #    [2024-01-01T04Z, 2025-01-01T04Z)，s < e 却跨了年界（BASE 的注释也写错了这点）。
            if s <= e:  # 季度由**同一名义年**的两条规则界定（北半球形态）
                if s <= ts < e:
                    return True
            else:  # 跨年季度（南半球形态）= [start(year), end(year+1))
                # 只有这一支要算 `year + 1`（见上方 ⛔ Codex r4 LOW-1 的上界说明）。
                if year >= 9999:
                    # ⛔ 不能整支跳过（Codex r9 L1）: `_dst_window(10000)` 会抛, 但季度**确实**
                    #    从 s(9999) 开始 —— 上一轮写成 `elif year < 9999` 把 9999 年的整个
                    #    南半球季度排除了。实测 `AAA0BBB,M10.1.0,M3.1.0` 在 9999-12-01T23:30Z
                    #    上 C 库给 +01:00, 那版给 +00:00。终点算不出来时按「从 s 起一直到
                    #    可表示范围末尾」处理 —— 那正是 C 库在该段的行为。
                    if s <= ts:
                        return True
                elif s <= ts < self._dst_window(year + 1)[1]:
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
        """夏令名 / 标准名。

        ⚠️ **如实声明一处与 C 库的差异**（Codex r10 L6）: C 库在把名字放进 tzname 时会
        做一层**缩写清理**, 本实现原样返回。本机实测的清理规则（无文档依据, 只能穷举
        字符集测出来）: `/` → `_`, 非 ASCII 按**字节**逐个换成 `_`（`<中>` 给 `___`）,
        而空格 / `.` / `+` / `-` / 数字都原样保留; 超长名还会被截断。
        不跟的理由: 这条差异只落在**显示**上 —— 归日走的是 `utcoffset()`, 与 tzname 无关;
        而要跟就得把那套「哪些字符合法」的平台细节再实测一遍并长期维护。
        """
        if dt is None or self._dst_off is None:
            return self._std_name
        # ⛔ 不能用「实际偏移 == dst_off」判 DST **身份**（Codex r9 L2）: 两侧偏移相等的
        #    规格（`AAA0BBB0,M3.2.0,M11.1.0`）下该式恒真, 冬季也会返回 dst 名 —— C 库
        #    实测给 `AAA`。偏移大小与夏令时身份是两回事（本文件的 fold 处理也一直是按
        #    偏移大小选侧、按 `_in_dst` 判身份）。这里改用 `_in_dst` 直接判, 与 `dst()` 同源。
        off = self._offsets_for_wall(dt)
        wall = calendar.timegm(dt.replace(tzinfo=None).timetuple())
        return self._dst_name if self._in_dst(wall - off) else self._std_name

    def fromutc(self, dt: datetime) -> datetime:
        # tzinfo 协议要求 fromutc 只接受「tzinfo 就是自己」的 aware datetime
        # （`datetime.timezone.fromutc` / `ZoneInfo.fromutc` 本机实测都对 naive 与
        #  异 tzinfo 抛 ValueError）。缺了它, 传 naive 或 `tzinfo=timezone.utc` 的
        #  datetime 会被静默当成本时区的 UTC 读数换算出一个看似合理的结果（Codex r10 L7）。
        if not isinstance(dt, datetime):
            # stdlib 的 `timezone.fromutc()` / `ZoneInfo.fromutc()` 对非 datetime 抛
            # TypeError; 少了这一句会先撞上 `dt.replace` 而抛 AttributeError（Codex r11 L5）。
            raise TypeError("fromutc() requires a datetime argument")
        if dt.tzinfo is not self:
            raise ValueError("fromutc: dt.tzinfo is not self")
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
        for cand in _zoneinfo_key_candidates(env_tz):
            try:
                return ZoneInfo(cand)
            except Exception:  # noqa: BLE001
                pass
        # ⛔ **前导冒号强制按路径解析, 不退 POSIX**（Codex r11 H2）: C 库对 `:AAA-1`、
        #    `:EST5EDT,M3.2.0,M11.1.0` 一律给 UTC —— 冒号前缀的语义就是「这是个路径」,
        #    路径找不到就结束, 不会再试规格串。上一版把整个 `env_tz`（含冒号）喂给
        #    `parse_posix_tz`, 而裸名字符集含 `:` ⇒ 整串被当成合法规格串收下, 误收 + 误算。
        if not env_tz.startswith(":"):
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
