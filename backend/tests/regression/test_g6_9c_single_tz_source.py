"""CARD-G6-9c — 单一时区来源的对照门（D-18 2026-09-07）。

本文件锁六件事，每条都配了负控（见卡文 (j) 的 M1/M2/M3 三个变异）：

① **两份副本同源** —— `app/core/display_tz.py` 与 `scripts/local_tz.py` 的
   `display_tz()` 函数体逐行相同，且两份 docstring 都带 `D-18 2026-09-07`。
   两份副本的存在理由：pick / runner / vault_lint 跑在 launchd 与 CLI 环境下
   **不能 import backend**（`app/__init__.py` 在 import 期 `load_dotenv`，会让
   「今天」随 `.env` 漂移）。副本必然有漂移风险，故用源码级门锁住。
② `CANVAS_TZ` 显式覆盖真的传到了**生产器子进程**（不是只改了显示层）。
③ 无效 `CANVAS_TZ` **抛错**，不静默退化 —— 配置断裂要说话。
④ 不设 `CANVAS_TZ` 时机器本地（`TZ`）真的被读到（②③ 的正控：证明②的
   差异来自 `CANVAS_TZ` 而不是"这条路径根本读不到任何时区"）。
⑤ 显示侧**每次调用求值** —— 同进程改 `TZ` + `tzset()` 后结果必须跟着变，
   全程**不 reload 模块**。这条是 (c) 那个 ⛔ 段的唯一门覆盖。
⑥ 默认配置下 `display_tz()` 必须给出**有名**时区（`.key` 非 None），否则
   下发给前端的 `display_tz` 恒为 null、本卡新建的那条链路一次都用不到。

⛔ 本文件不写 live vault、不连库：所有 vault 都在 `tmp_path` 上造，pick 一律
   **不带 `--write`**（只读 stdout 的 payload）。
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import os
import re
import shutil
import subprocess
import textwrap
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

WT = Path(__file__).resolve().parents[3]
REPO_SCRIPTS = WT / "scripts"

from app.api.v1.endpoints import review_overview as ro  # noqa: E402
from app.core import display_tz as backend_tz  # noqa: E402


def _load_local_tz():
    """加载仓根 `scripts/local_tz.py`（pick / runner / vault_lint 用的那一份）。

    ⛔ 先 `sys.modules[name] = mod` 再 `exec_module`：Python 3.14 的 dataclass
       自省会去 `sys.modules[cls.__module__]` 取字典，不注册就会在别处炸
       （第十批 X6 的教训，见 `.claude/rules/card-batch-protocol.md` §3）。
    """
    name = "_g69c_local_tz_probe"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO_SCRIPTS / "local_tz.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ══════════════════════════════════════════════════════════════════════════
# ① 两份副本同源
# ══════════════════════════════════════════════════════════════════════════


def test_two_copies_share_identical_function_body():
    """两份 `display_tz()` 的源码逐行相同（`dedent` 去公共缩进 + 去行尾空白后比较）。

    比的范围是 `inspect.getsource()` 给出的**整段**——含 `def` 行、签名与函数
    docstring，不含模块 docstring / import（两份文件的模块级说明本来就该各写各的，
    一份对 backend 说话、一份对 launchd 说话）。

    ⛔ **保留行首缩进**（Codex r1 MEDIUM-2）：初版用 `ln.strip()` 逐行剥首尾空白，
    那把 Python 的控制流缩进也剥掉了 —— 把 `env_tz = ...` 多缩进一级塞进
    `if name:` 分支里，比较照样通过，而正常调用会抛 `UnboundLocalError`。
    缩进在 Python 里是语义，判据不能把它抹掉。`dedent` 只去**公共**前缀，
    相对缩进原样保留。

    ⚠️ 如实声明本门**证不到**什么：它比的是源码文本，能挡住"改了一份忘了另一份"
    这类真实漂移，但挡不住"两边同时改成同一个错的写法"。语义等价而写法不同的
    副本（比如把 if 拆成三行）会被它**误报**——那正是想要的：副本就该逐字一致，
    有意的改写必须两边同时做。
    """
    local_tz = _load_local_tz()
    a = [ln.rstrip() for ln in textwrap.dedent(inspect.getsource(backend_tz.display_tz)).splitlines()]
    b = [ln.rstrip() for ln in textwrap.dedent(inspect.getsource(local_tz.display_tz)).splitlines()]
    assert a == b, (
        "两份 display_tz() 函数体不一致 —— 同源副本漂移了。\n"
        f"  backend/app/core/display_tz.py: {len(a)} 行\n"
        f"  scripts/local_tz.py:            {len(b)} 行\n"
        f"  首个差异: {next((f'{i}: {x!r} vs {y!r}' for i, (x, y) in enumerate(zip(a, b)) if x != y), '(长度不同)')}"
    )
    # 验伪锚：函数体不能是空壳（否则"逐行相同"在两边都被掏空时也成立）
    assert len(a) >= 15, f"函数体只剩 {len(a)} 行，门失去被测对象"
    assert any("CANVAS_TZ" in ln for ln in a), "函数体里没有 CANVAS_TZ —— 比的不是这个函数"


def test_two_copies_share_identical_localtz_class():
    """两份副本的**全部共享定义**逐行相同：`_PosixTZ` 类 + `parse_posix_tz` 及其
    辅助函数（Codex r3 MEDIUM + 自验变异 A，r4 重写后扩展）。

    ⛔ 门 ① 只比 `display_tz` 那个**函数**。POSIX TZ 分支的整个实现体是
    `_PosixTZ` 类 + 解析函数族 —— 不在门 ① 的比较范围。自验实测：把
    `scripts/local_tz.py` 的类名改掉（等价于删掉它），当时整个测试文件仍全绿，
    而该副本在运行期会 `NameError`。
    """
    local_tz = _load_local_tz()
    # 先查**存在性**再比内容：定义被删/改名时 inspect.getsource 抛的是 AttributeError，
    # 那条 traceback 不带可辨认的身份，变异负控绑不住「是这一条红的」。
    shared = (
        "_PosixTZ",
        "parse_posix_tz",
        "_posix_offset_seconds",
        "_parse_rule",
        "_rule_epoch",
        "_parse_hms",
        "_strip_name",
    )
    for name in shared:
        for label, mod in (("backend/app/core/display_tz.py", backend_tz), ("scripts/local_tz.py", local_tz)):
            assert hasattr(mod, name), (
                f"{label} 里没有 {name} —— 同源副本漂移了（定义被删或改名）。"
                f"{name} 是 POSIX TZ 分支的实现体，缺了它这份副本在运行期会 NameError。"
            )
        a = [ln.rstrip() for ln in textwrap.dedent(inspect.getsource(getattr(backend_tz, name))).splitlines()]
        b = [ln.rstrip() for ln in textwrap.dedent(inspect.getsource(getattr(local_tz, name))).splitlines()]
        assert a == b, (
            f"两份 {name} 不一致 —— 同源副本漂移了。\n"
            f"  首个差异: {next((f'{i}: {x!r} vs {y!r}' for i, (x, y) in enumerate(zip(a, b)) if x != y), '(长度不同)')}"
        )
    # 验伪锚：类体不能是空壳，且必须含 POSIX tzinfo 赖以成立的方法名
    cls_src = inspect.getsource(backend_tz._PosixTZ)
    for must in ("def fromutc", "def utcoffset", "def dst", "def tzname"):
        assert must in cls_src, f"_PosixTZ 类体里没有 {must} —— 比的不是这个类"


def test_both_copies_carry_the_d18_ruling_date():
    """两份 docstring 都必须带裁定日期字面量 —— 换口径的人得先看见它是谁定的。"""
    local_tz = _load_local_tz()
    for label, fn in (("app/core/display_tz.py", backend_tz.display_tz), ("scripts/local_tz.py", local_tz.display_tz)):
        doc = fn.__doc__ or ""
        assert "D-18 2026-09-07" in doc, f"{label} 的 display_tz docstring 缺 D-18 2026-09-07"


# ══════════════════════════════════════════════════════════════════════════
# ②③④ 生产器子进程：CANVAS_TZ 覆盖 / 无效即抛 / 机器本地正控
# ══════════════════════════════════════════════════════════════════════════

#: UTC 16:30 —— 上海/东京已跨日、洛杉矶还在前一天，是暴露时区差的关键刻度
_INSTANT = "2026-07-30T16:30:00Z"


def _tmp_vault(tmp_path: Path, name: str = "v") -> Path:
    vault = tmp_path / name
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)
    (vault / "节点" / "甲.md").write_text(
        '---\ntype: concept\nsource_board: "[[原白板/时区板]]"\n---\n内容。\n', encoding="utf-8"
    )
    return vault


def _run_pick(vault: Path, **env_over: str | None) -> subprocess.CompletedProcess:
    """跑生产器子进程（**不带 --write**，只读 stdout）。"""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"  # 不许在 vault 里落 __pycache__
    for k, v in env_over.items():
        if v is None:
            env.pop(k, None)
        else:
            env[k] = v
    return subprocess.run(  # noqa: S603 — argv 列表 + 仓内自解析路径，无 shell
        [sys.executable, str(REPO_SCRIPTS / "daily_review_pick.py"), "--vault", str(vault), "--now", _INSTANT],
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
        check=False,
    )


def test_canvas_tz_override_reaches_the_producer_subprocess(tmp_path):
    """② `CANVAS_TZ=Asia/Tokyo` 必须改变生产器落盘的 date 与 generated_at 偏移。

    这条测的是**生产器**（pick）而不是显示层：D-18 要的是「页面、早间提醒、
    清单三处的今天是同一天」，只改显示层等于把分叉挪了个地方。
    """
    vault = _tmp_vault(tmp_path)
    proc = _run_pick(vault, CANVAS_TZ="Asia/Tokyo", TZ=None)
    assert proc.returncode == 0, f"rc={proc.returncode}\nstderr={proc.stderr[-2000:]}"
    payload = json.loads(proc.stdout)
    assert payload["date"] == "2026-07-31", f"UTC 16:30 在东京已是次日；实得 {payload['date']}"
    assert payload["generated_at"].endswith("+09:00"), f"generated_at 偏移不是东京；实得 {payload['generated_at']}"


def test_invalid_canvas_tz_raises_instead_of_silently_falling_back(tmp_path):
    """③ 无效 `CANVAS_TZ` ⇒ 非零退出 + 说出人话，**不静默退化**成别的时区。

    ⛔ 判据绑定**实际异常消息行**（`^ValueError: ...`）而不是 `"CANVAS_TZ 无效" in stderr`：
       traceback 会把 `raise ValueError(f"CANVAS_TZ 无效: {name!r} ...")` 那行**源码**
       原样打出来，子串判据因此对"异常根本没抛、只是别处崩了"同样恒真。
    """
    vault = _tmp_vault(tmp_path)
    before = sorted(p.name for p in (vault / "outputs").iterdir()) if (vault / "outputs").is_dir() else []
    proc = _run_pick(vault, CANVAS_TZ="Not/AZone", TZ=None)

    assert proc.returncode != 0, "无效 CANVAS_TZ 却成功退出 —— 配置断裂被静默吞掉了"
    m = re.search(r"^ValueError: CANVAS_TZ 无效: 'Not/AZone' \(\w+\)$", proc.stderr, re.M)
    assert m is not None, (
        "stderr 里没有那条**实际抛出**的 ValueError（只有源码行不算）。\nstderr 尾部:\n" + proc.stderr[-1500:]
    )
    assert proc.stdout.strip() == "", f"抛错了却还吐了 payload：{proc.stdout[:300]!r}"
    after = sorted(p.name for p in (vault / "outputs").iterdir()) if (vault / "outputs").is_dir() else []
    assert after == before, f"无效配置下写了文件：{set(after) - set(before)}"


def test_machine_local_tz_is_actually_read_when_no_override(tmp_path):
    """④ **正控**：不设 `CANVAS_TZ` 时，机器本地 `TZ` 真的被读到。

    没有这条，② 的"东京日期"分不清是 `CANVAS_TZ` 起作用，还是这条路径恒用某个
    固定时区而东京恰好与它同日。这里用洛杉矶 —— 它与东京、与本机默认都不同日。
    """
    vault = _tmp_vault(tmp_path)
    proc = _run_pick(vault, CANVAS_TZ=None, TZ="America/Los_Angeles")
    assert proc.returncode == 0, f"rc={proc.returncode}\nstderr={proc.stderr[-2000:]}"
    payload = json.loads(proc.stdout)
    assert payload["generated_at"].endswith("-07:00"), (
        f"机器本地 TZ 没被读到（期望洛杉矶夏令时 -07:00）；实得 {payload['generated_at']}"
    )
    assert payload["date"] == "2026-07-30", f"UTC 16:30 在洛杉矶仍是当日；实得 {payload['date']}"


# ══════════════════════════════════════════════════════════════════════════
# ⑤ 显示侧每次调用求值（(c) 的 ⛔ 段的唯一门覆盖）
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def tz_env():
    """改进程时区并**无条件还原**（含 CANVAS_TZ）。"""
    saved_tz, saved_canvas = os.environ.get("TZ"), os.environ.get("CANVAS_TZ")

    def _set(tz: str | None = None, canvas_tz: str | None = None) -> None:
        for key, val in (("TZ", tz), ("CANVAS_TZ", canvas_tz)):
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val
        time.tzset()

    try:
        yield _set
    finally:
        for key, val in (("TZ", saved_tz), ("CANVAS_TZ", saved_canvas)):
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val
        time.tzset()


def test_display_side_reevaluates_every_call(tz_env):
    """⑤ 同进程内改 `TZ` + `tzset()`，显示侧必须跟着变 —— **全程不 reload 模块**。

    这正是 `test_g6_9_boundary_matrix.py` 的 `machine_tz` 夹具做的事（它只改 TZ、
    不 reload）。若显示侧在 import 那一刻就把时区绑成模块级常量 / `lru_cache`，
    这条门会红，而矩阵里那 8 条翻转用例会在去标后重新变成 8 failed。

    ⛔ 刻意**不**用 `importlib.reload`：reload 会让这条门恒真，等于没测。
    """
    tz_env(tz="UTC")
    name_utc = ro._display_tz_name()
    # 16:30Z 在 UTC 与 NY 都还是 07-31（同日），单看它分不出时区有没有换
    same_day_utc = str(ro._display_day("2026-07-31T16:30:00Z"))
    # 03:30Z 在 UTC 是 07-31、在 NY 是前一天 07-30 —— 这是**日期翻转锚**
    flip_utc = str(ro._display_day("2026-07-31T03:30:00Z"))

    tz_env(tz="America/New_York")
    name_ny = ro._display_tz_name()
    same_day_ny = str(ro._display_day("2026-07-31T16:30:00Z"))
    flip_ny = str(ro._display_day("2026-07-31T03:30:00Z"))

    assert name_utc == "UTC" and name_ny == "America/New_York", (
        f"时区名没跟着 TZ 变 —— 显示侧把时区固化在 import 时刻了：{name_utc} → {name_ny}"
    )
    assert same_day_utc == "2026-07-31" and same_day_ny == "2026-07-31", (
        f"同日锚失效（16:30Z 在两个时区都该是 07-31）：{same_day_utc} / {same_day_ny}"
    )
    assert flip_utc == "2026-07-31" and flip_ny == "2026-07-30", (
        f"日期翻转锚失效：03:30Z 在 UTC 应为 07-31、在纽约应为 07-30；实得 {flip_utc} / {flip_ny}"
    )


def test_explicit_override_wins_over_machine_tz(tz_env):
    """⑤ 的对照：`CANVAS_TZ` 在场时，改 `TZ` **不得**影响结果（显式覆盖压过机器本地）。

    与上一条合起来才说明白"每次现取"取的是什么：不是"每次都读 TZ"，而是每次都
    重新走一遍 CANVAS_TZ → TZ → /etc/localtime 这条优先级链。
    """
    tz_env(tz="UTC", canvas_tz="Asia/Tokyo")
    first = (ro._display_tz_name(), str(ro._display_day("2026-07-31T03:30:00Z")))
    tz_env(tz="America/New_York", canvas_tz="Asia/Tokyo")
    second = (ro._display_tz_name(), str(ro._display_day("2026-07-31T03:30:00Z")))

    assert first == second == ("Asia/Tokyo", "2026-07-31"), f"CANVAS_TZ 没压住机器本地 TZ：{first} vs {second}"


# ══════════════════════════════════════════════════════════════════════════
# ⑦ POSIX TZ 串必须落到**进程本地**，不能去读 /etc/localtime（Codex r1 HIGH-1）
# ══════════════════════════════════════════════════════════════════════════


#: ZoneInfo 认不出、但 C 库认得的 TZ 写法。带 DST 规则的那两个是关键 ——
#: 只有**逐时刻**解析才判得对，用「此刻的固定偏移」在 DST 两侧会错一小时。
_POSIX_TZ_VALUES = [
    "UTC0",
    "EST5",
    "CST-8",
    "IST-5:30",
    ":America/New_York",
    ":America/Santiago",
    "EST5EDT,M3.2.0,M11.1.0",
    "PST8PDT,M3.2.0,M11.1.0",
    "<+10:30>-10:30<+11>-11,M10.1.0,M4.1.0/3",  # 引用名 + 半小时 DST + 南半球
    "NZST-12NZDT,M9.5.0,M4.1.0/3",  # 末周规则 + 显式切换时刻
    "WART4WARST,J1/0,J365/25",  # J 儒略日规则 + >24h 的切换时刻
    # ↓ CARD-G6-9c-R2 (Codex r5) 补的三串。**只加非 2026 时刻、不加串 = 装饰**: 上面
    #   11 个串在结构上碰不到下面三条缺陷面 —— 实测 40 年 ×6h 粗扫 + 21 年年界/闰界
    #   逐分钟细扫(每串 341,280 格)全部 0 mismatch。三串各锁一条, 缺哪条那条就无门可守。
    "CET-1CEST",  # dst 名在场、切换规则**省略**: C 库按 tzset(3) 退 `posixrules` 的规则
    #   (本机 posixrules 与 America/New_York 逐字节相同, sha256 一致 ⇒ M3.2.0,M11.1.0,
    #   当地 02:00), 只把两侧偏移换成 TZ 自带值; 本实现曾整体退 UTC ⇒ 全年错一档偏移。
    #   **与时刻无关**, 每个时刻格都红。
    "AAA1BBB0,365/3,365/2",  # 裸 n=365 + 跨年季度: 平年里 n=365 落到**次年元旦**, 于是
    #   包住元旦的那个 DST 季度其名义起始年 = y-2, 三年候选窗 (y-1, y, y+1) 漏掉它。
    #   ⛔ 只在"前一年是平年"的元旦显形: 2024/2023 元旦红, 2025/2021 元旦绿(前一年是闰年,
    #   n=365 落在 12/31 不滚年) —— 年界样本挑错年份就是哑弹。
    "AAA5BBB,J60/2,J300/2",  # Jn 跳闰日: J60 在闰年必须**仍是 3/1**(Jn 不数 2/29)。现有
    #   11 串没有任何一个在 2 月底附近有切换规则, 闰年 2 月末的样本因此无处着力。
]

#: 探测时刻。**必须含折叠窗口内的时刻**（Codex r3 + 自验变异 B/C）：
#: 初版三个时刻全落在折叠窗口之外，于是「删掉自定义 fromutc」「删掉 fold 处理」
#: 两个变异在 12 格里全部存活。折叠时段是这两处实现唯一会显形的地方。
_DST_PROBE_INSTANTS = [
    datetime(2026, 7, 31, 16, 30, tzinfo=timezone.utc),  # 夏令时内
    datetime(2026, 11, 2, 4, 30, tzinfo=timezone.utc),  # 回拨之后
    datetime(2026, 3, 9, 4, 30, tzinfo=timezone.utc),  # 前跳之后
    datetime(2026, 11, 1, 5, 30, tzinfo=timezone.utc),  # 北半球折叠窗口：NY 01:30 EDT（第一次）
    datetime(2026, 11, 1, 6, 30, tzinfo=timezone.utc),  # 同一墙钟第二次：NY 01:30 EST
    datetime(2026, 3, 8, 7, 30, tzinfo=timezone.utc),  # 北半球空缺窗口边缘
    datetime(2026, 4, 5, 3, 30, tzinfo=timezone.utc),  # 南半球折叠：Santiago
    datetime(2026, 4, 5, 4, 30, tzinfo=timezone.utc),
    # ⛔ 以下三个**不在 2026 年**(CARD-G6-9c-R2, Codex r5 MEDIUM): 上面 8 个全落在 2026,
    #   而闰年与跨年两类日期算术只在别的年份显形。每条都配了能压到它的串(见上表), 且都做过
    #   逐格负控 —— 还原对应修复后它们必红, 不是装饰。
    # ⛔⛔ 往本表加样本时年份**必须落在 2007..2037**: 本门比的是「与 C 库逐时刻取值相等」,
    #   而 C 库对**省略切换规则**的串走 posixrules —— ≤2006 用的是那张 tzfile 的整张历史
    #   转换表(例如 1975-02-23 那次能源危机提前实施 DST, 根本不是 M3.2.0), ≥2038 它的
    #   32 位表止于 2037-11-01 且不外推、直接丢掉 DST。区间外红的是 C 库自己的边界,
    #   不是本实现的缺陷（表里现有 `CET-1CEST` 就属该族）。
    datetime(2024, 2, 29, 12, 0, tzinfo=timezone.utc),
    #   闰年 2 月末。压 `_rule_epoch` 的 `calendar.isleap(year) and a >= 60` 分支: 配
    #   `AAA5BBB,J60/2,J300/2`, 删掉跳闰日后 J60 从 3/1 变 2/29, 本时刻墙钟 07:00→08:00。
    datetime(2024, 12, 31, 12, 0, tzinfo=timezone.utc),
    #   闰年年末 12-31。同一分支的另一侧: 配**已有的** `WART4WARST,J1/0,J365/25`,
    #   J365 在闰年必须仍是 12/31; 删掉跳闰日后终点提前一天, 墙钟 09:00→08:00。
    #   ⛔ 这两个闰年时刻**各自不可删**, 不是互为冗余 —— 用区分性变异实测过(负控 ⑥⑦):
    #   把闰日条件改成 `a >= 300` 只坏 J60 ⇒ 只杀 02-29 那格; 改成 `60 <= a < 300` 只坏
    #   J365 ⇒ 只杀 12-31 那格; 只有「删整条跳闰日」才两格同杀。若只跑后一种变异, 会
    #   误以为留一个就够。
    datetime(2024, 1, 1, 0, 30, tzinfo=timezone.utc),
    #   年界 01-01 —— Codex r5 HIGH-1 的逐字反例。配 `AAA1BBB0,365/3,365/2`: 正确窗口是
    #   start(2022)=2023-01-01T04:00Z → end(2023)=2024-01-01T02:00Z, 候选窗只看
    #   (y-1, y, y+1) 就漏掉名义 2022 年 ⇒ 墙钟被算成 2023-12-31 23:30, **直接错日**。
    #   ⚠️ 此例**转回 UTC 仍守恒** ⇒ 判据 2(时刻守恒)抓不到它, 只有判据 1(墙钟)能抓。
]

#: 两份同源副本都要被测 —— 门此前只喂 backend 那份，scripts 副本的 POSIX 分支
#: 从未被任何测试执行过（自验变异 A：改坏 scripts 副本，全文件仍绿）。
_COPY_IDS = ["backend", "scripts"]


def _display_tz_of(copy_id):
    """按副本 id 取 display_tz()。两份是同源副本，门必须都跑。"""
    if copy_id == "backend":
        return ro._display_tz()
    return _load_local_tz().display_tz()


@pytest.mark.parametrize("copy_id", _COPY_IDS)
@pytest.mark.parametrize("tz_value", _POSIX_TZ_VALUES)
def test_posix_tz_string_resolves_to_process_local_not_etc_localtime(tz_env, tz_value, copy_id):
    """`TZ` 是 ZoneInfo 不认、但 C 库认的写法时，换算必须与 C 库**逐时刻**一致。

    ⛔ 这些都是**合法**的 `TZ` 值：POSIX 风格（`UTC0` / `EST5` / 带 DST 规则的
    `EST5EDT,M3.2.0,M11.1.0`）与前导冒号（`:America/New_York` / `:America/Santiago`）。
    `ZoneInfo` 全拒。三个被否掉的实现都在这里翻车：
      · 继续读 `/etc/localtime` —— 那是**宿主**时区、压根不看 `TZ`；
      · 返回 `datetime.now().astimezone().tzinfo` —— 只是**此刻**的固定偏移，
        换算别的时刻会在 DST 两侧错一小时；
      · 用默认的 `tzinfo.fromutc()` —— 它拿 `utcoffset(dt)` 去猜，而 dt 是 UTC 值、
        `_isdst()` 却把它当本地墙钟，南半球 DST 上直接错日。

    两条判据缺一不可：
      1. **墙钟**与 C 库无参 `astimezone()` 逐时刻相同；
      2. **时刻守恒** —— 换算结果转回 UTC 必须等于原时刻。
         没有第 2 条，`fold` 处理是不可击杀的：`datetime.__eq__` 忽略 `fold`，
         折叠时段里墙钟看着对、转回 UTC 却差一小时（自验变异 C）。
    """
    tz_env(tz=tz_value)
    resolved = _display_tz_of(copy_id)
    for instant in _DST_PROBE_INSTANTS:
        got = instant.astimezone(resolved)
        libc = instant.astimezone()
        assert got.replace(tzinfo=None) == libc.replace(tzinfo=None), (
            f"[{copy_id}] TZ={tz_value!r} 在 {instant.isoformat()} 上墙钟与 C 库不一致：\n"
            f"  display_tz() 给 {got.replace(tzinfo=None)}（resolved={resolved!r}）\n"
            f"  C 库逐时刻给 {libc.replace(tzinfo=None)}"
        )
        assert got.astimezone(timezone.utc) == instant, (
            f"[{copy_id}] TZ={tz_value!r} 在 {instant.isoformat()} 上**时刻不守恒**：\n"
            f"  换算得 {got!r}，转回 UTC 是 {got.astimezone(timezone.utc).isoformat()}，"
            f"原时刻是 {instant.isoformat()}\n"
            "  折叠时段没标对 fold，或 utcoffset() 没按 fold 取那一侧。"
        )


#: HIGH-1（CARD-G6-9c-R2）的逐点反例：规则的**实际生效时刻滚进了下一年**，于是包住目标
#: 时刻的那个 DST 季度其**名义起始年 = y-2** —— 三年候选窗 `(y-1, y, y+1)` 够不着它。
#: (spec, UTC 时刻, 为什么偏偏是这一年显形)
_CROSS_YEAR_WINDOW_CASES = [
    (
        "AAA1BBB0,365/3,365/2",
        datetime(2024, 1, 1, 0, 30, tzinfo=timezone.utc),
        "2022 是平年 ⇒ start(2022) 的裸 n=365 落到 2023-01-01T04:00Z, end(2023) 落到 "
        "2024-01-01T02:00Z ⇒ 该季度横跨整个 2023 年并包住 2024 元旦, 名义起始年是 y-2",
    ),
    (
        "AAA1BBB0,365/3,365/2",
        datetime(2023, 1, 1, 0, 30, tzinfo=timezone.utc),
        "同形态的另一年(2021 也是平年) —— 两条一起排除「只是某一年凑巧」",
    ),
    (
        # ⛔ 抗漂移的那一条。`365/3,365/2` 的红区**每年只有 2 小时**、且只在「前一年是
        # 平年」的元旦出现(还原 y-2 后 2007..2037 里 23/31 年红); 把 `/时刻` 拉到 167 小时
        # 后红区变成 **166 小时/年、31/31 年都红**。后人把探针时刻挪几小时时, 前者会静默
        # 变哑弹, 后者不会。
        # ⚠️ 「元旦 + 前一年闰 = 哑弹」是 `365/3` 这个**串**的性质, **不是 HIGH-1 的性质**
        # —— 本串在 2021/2025/2026 元旦同样红。别把那句话读成「HIGH-1 只能靠某些年份测」。
        "AAA1BBB0,365/167,365/166",
        datetime(2024, 1, 1, 0, 30, tzinfo=timezone.utc),
        "同一漏格、红区宽 166 小时且逐年都有 —— 时刻挪动后仍然承重",
    ),
    (
        # 来源 ②：Jn 叠 /167。没有裸 n，证明漏格不是「裸 n 语义」特有的。
        "AAA1BBB0,J365/167,J365/167",
        datetime(2024, 1, 1, 0, 30, tzinfo=timezone.utc),
        "Jn 叠大 /N 同样滚出名义年（2007..2037 元旦周逐小时红 4433 点）",
    ),
    (
        # 来源 ③：Mm.w.d 年末叠 /167 —— **既无裸 n 也无 Jn**。这一条是初版注释里那句
        # 「裸 n=365 是唯一会溢出名义年的写法」的直接反例。
        "AAA1BBB0,M12.5.0/167,M12.5.0/167",
        datetime(2024, 1, 1, 0, 30, tzinfo=timezone.utc),
        "纯 Mm.w.d 规则也能滚年（末周日靠近月末的年份，红 2325 点）",
    ),
]


@pytest.mark.parametrize("copy_id", _COPY_IDS)
@pytest.mark.parametrize("spec,instant,why", _CROSS_YEAR_WINDOW_CASES)
def test_dst_window_candidates_cover_rules_that_roll_into_the_following_year(tz_env, spec, instant, why, copy_id):
    """DST 季度的候选年必须覆盖「规则滚进下一年」的那些季度，否则**直接错日**。

    ⛔ 这条与门⑦ 的判据 2（时刻守恒）互补而**不重叠**：本反例转回 UTC 仍然守恒，
    守恒判据对它完全无感 —— 只有墙钟/归日这一侧能抓。所以不要把本门并进那条。

    为什么表里既有的 11 个串压不到：⛔ **不是因为「季度不跨年」** —— 实测 2024 年
    `NZST-12NZDT,M9.5.0,M4.1.0/3` 的季度是 09-28 → 次年 04-05，
    `WART4WARST,J1/0,J365/25` 是 01-01 → 次年 01-01，
    `<+10:30>-10:30<+11>-11,M10.1.0,M4.1.0/3` 是 10-05 → 次年 04-05，**都跨年**
    （初版注释写成「季度不跨年」，Codex r2 LOW-3 实测证伪）。

    ⛔ **没有一句话的区分点** —— 这一点被两轮审查连续证伪，这里如实写清楚机制：
      · 初版写「`start` 有没有滚出名义年」（r3 LOW-2 证伪）：2024 是闰年，裸 `n=365` 落在
        12-31（+365.17 天）**并没有**滚进下一年；
      · 二版写「季度跨了几个年界」（r4 LOW-2 证伪）：`Y=2022` 的季度是
        `2023-01-01T04Z → 2024-01-01T02Z`，**只跨一个**年界，可它覆盖 `2024-01-01T00:30Z`
        的名义起始年仍是 `2022 = y−2`。

    准确的机制（Codex r5 L2 给的表述，前面两版都被证伪，别再改回去）：**南半球分支的
    季度终点取的是 `e(Y+1)`，而这个端点自己还能滚进 `Y+2` 年** —— 于是覆盖 y 年初的
    季度，其名义起始年可以早到 `y−2`。
    （初版「两段位移累加把季度整体推到 Y+2」也不准：`Y=2024` 的季度是
    `2024-12-31T04Z → 2026-01-01T02Z`，两个端点的位移并没有相加。）
    界的严格推导在 `_in_dst` 的注释里（406.70 / 42 / 448.70 / 365 / 730 五个数）。
    ⛔ **滚出名义年不止一条路**（本卡实测更正了初版注释里「裸 n=365 是唯一写法」那句）：
      ① 平年的裸 `n=365` = `1月1日 + 365 天` = 次年元旦；
      ② `Jn` / 裸 `n` 叠 `/N`（POSIX 允许到 167 小时，本实现的正则更放行到 999:99:99）；
      ③ `Mm.w.d` 落在年末再叠 `/N` —— **既无裸 n 也无 Jn**，且逐年不同（末周日是 12/25
         的年份就不滚）。
    三条来源下面各有一条用例；②③ 的红区比 ① 宽两个数量级（2007..2037 元旦周逐小时：
    ① 46 点、② 4433 点、③ 2325 点），所以它们才是抗漂移的那几条。
    """
    tz_env(tz=spec)
    resolved = _display_tz_of(copy_id)
    got = instant.astimezone(resolved).replace(tzinfo=None)
    libc = instant.astimezone().replace(tzinfo=None)
    assert got == libc, (
        f"[{copy_id}] 候选窗漏格·实得 {got} 应为 {libc}\n"
        f"  TZ={spec!r} 在 {instant.isoformat()}\n"
        f"  {why}\n"
        "  `_in_dst` 的候选年只取名义年 (y-1, y, y+1), 漏掉了起始年更早的那个跨年季度。"
    )
    assert got.date() == libc.date(), (
        f"[{copy_id}] 候选窗漏格·归日错一天: 实得 {got.date()} 应为 {libc.date()}\n"
        f"  TZ={spec!r} 在 {instant.isoformat()} —— D-18 的「今天」在这里就算错了。"
    )


#: HIGH-new（CARD-G6-9c-R2）：`dst` 名在场但切换规则**省略**。C 库按 tzset(3) 用
#: `posixrules` 的规则补齐（本机 posixrules 与 `America/New_York` 逐字节相同 ⇒
#: `M3.2.0,M11.1.0`，当地 02:00），只把两侧偏移换成 TZ 自带值。
#: (spec, 夏令时侧的 UTC 时刻, 标准时侧的 UTC 时刻, 备注)
_OMITTED_RULE_CASES = [
    (
        "EST5EDT",
        datetime(2026, 7, 31, 16, 30, tzinfo=timezone.utc),
        datetime(2026, 1, 15, 16, 30, tzinfo=timezone.utc),
        "有同名 tzfile, 故只有直接调 parse_posix_tz 才够得到本分支",
    ),
    (
        "CET-1CEST",
        datetime(2026, 7, 31, 22, 30, tzinfo=timezone.utc),
        datetime(2026, 1, 15, 22, 30, tzinfo=timezone.utc),
        "Codex r5 的逐字反例: 两副本给 22:30+00:00, libc 给 2026-08-01 00:30+02:00",
    ),
    (
        "XYZ5XYD",
        datetime(2026, 7, 31, 16, 30, tzinfo=timezone.utc),
        datetime(2026, 1, 15, 16, 30, tzinfo=timezone.utc),
        "自造名 —— /usr/share/zoneinfo 下无同名 tzfile, 排除「其实读到了同名文件」这一替代解释",
    ),
]


@pytest.mark.parametrize("copy_id", _COPY_IDS)
@pytest.mark.parametrize("spec,summer,winter,note", _OMITTED_RULE_CASES)
def test_omitted_transition_rules_use_the_libc_default_instead_of_falling_back_to_utc(
    spec, summer, winter, note, copy_id
):
    """给了夏令时名却省略切换规则**不是语法错误**，规格把规则留给实现定义。

    ⛔ 走 `parse_posix_tz` 而**不是** `display_tz()`：`EST5EDT` 有同名 tzfile，
    `display_tz()` 会在更早的 ZoneInfo 档就接住它，根本够不到本分支。卡文 (b)②
    点名的正是这个串，所以判据必须直接打在解析器上。
    """
    module = backend_tz if copy_id == "backend" else _load_local_tz()
    tz = module.parse_posix_tz(spec)
    assert tz is not None, (
        f"[{copy_id}] dst 有名省略规则被退 UTC: parse_posix_tz({spec!r}) 返回 None\n"
        f"  {note}\n"
        "  返回 None 会让 display_tz() 的 POSIX 档整体退回 ZoneInfo('UTC') —— 而 C 库\n"
        "  按 tzset(3) 用 posixrules 的规则补齐, 于是每年有几百小时归错日, 且生产者\n"
        "  自报的 display_tz 也一并退成 'UTC', 与 generated_at 自洽 ⇒ **错得不会报错**。"
    )
    off_summer = summer.astimezone(tz).utcoffset()
    off_winter = winter.astimezone(tz).utcoffset()
    assert off_summer != off_winter, (
        f"[{copy_id}] dst 有名省略规则被退 UTC(或退成了无 DST 的时区): {spec!r} 在夏冬两侧偏移相同\n"
        f"  夏 {summer.isoformat()} -> {off_summer}；冬 {winter.isoformat()} -> {off_winter}\n"
        "  给了夏令时名就必须真的有夏令时 —— 补的是 posixrules 的默认规则, 不是把 DST 抹掉。"
    )


@pytest.mark.parametrize("copy_id", _COPY_IDS)
def test_candidate_year_guard_keeps_extreme_epochs_from_raising(copy_id):
    """候选年扩到 y−2 后，极早/极晚年份不得因 `year` 越界抛异常（Codex r3 LOW-1）。

    ⛔ 这是**本卡扩候选窗带来的新边界**，不是既有问题：BASE 的三年候选在 ts 落于公元 2 年
    时算的是 (1, 2, 3) 全合法；扩到 y−2 后多出 `year=0`，而 `_rule_epoch` 的 M 分支走
    `datetime(year, mon, 1)` ⇒ `ValueError: year must be in 1..9999, not 0`。
    南半球分支还要取 `_dst_window(year + 1)`，所以上界也要留一格（9998）。
    实测 BASE 在 `0002-07-01T12:00Z` 上换算成功而 r3 之前的 HEAD 抛异常。

    ⚠️ 本门钉两件事：极值年份**不抛**，以及上界不被收得过紧（9999 年的北半球季度必须
    仍算得出 +01:00）。它**不**保证这些年份的换算与 C 库一致 —— 它们远在声明的对齐区间
    （2007..2037）之外，C 库自己在那里也不套用 POSIX 规则。
    """
    module = backend_tz if copy_id == "backend" else _load_local_tz()
    tz = module.parse_posix_tz("AAA0BBB,M3.2.0,M11.1.0")
    assert tz is not None, f"[{copy_id}] 前提不成立：这个规格本应解析成功"
    for dt in (
        datetime(2, 7, 1, 12, tzinfo=timezone.utc),  # y−2 = 0，下界
        datetime(3, 1, 1, 12, tzinfo=timezone.utc),
        datetime(9998, 7, 1, 12, tzinfo=timezone.utc),
        datetime(9999, 7, 1, 23, 30, tzinfo=timezone.utc),  # y 本身 = 9999，上界
    ):
        try:
            dt.astimezone(tz)
        except Exception as exc:  # noqa: BLE001 —— 任何异常都是失败，类型不限
            raise AssertionError(
                f"[{copy_id}] 候选年守卫失效: {dt.isoformat()} 换算抛 "
                f"{type(exc).__name__}: {exc}\n"
                "  `_in_dst` 的候选年里有 year∉[1,9999]，`_rule_epoch` 的 `datetime(year, …)` 会抛。"
            ) from exc
    # ⛔ 上界不能只验「不抛」：把守卫写成 `1 <= year <= 9998` 时上面四个时刻**全都不抛**，
    #    但 9999 年的北半球季度被整个跳过、结果从 +01:00 变成 +00:00（Codex r4 LOW-1 实测
    #    该门「没有守住上界」）。所以这里还要钉**换算结果**。
    #    9999-07-01 落在 M3.2.0 → M11.1.0 的夏令时段内 ⇒ 偏移应是 dst 侧的 +01:00。
    late = datetime(9999, 7, 1, 23, 30, tzinfo=timezone.utc).astimezone(tz)
    assert late.utcoffset() == timedelta(hours=1), (
        f"[{copy_id}] 候选年上界收得过紧: 9999-07-01T23:30Z 换算得 {late}（偏移 {late.utcoffset()}），"
        "应为 +01:00 —— 9999 年的北半球季度不需要 year+1，不该被跳过。"
    )
    # ⛔ 上面那个规格走的是**北半球**分支，压不到南支的 `year < 9999` 守卫（Codex r5 L1
    #    实测：把 `elif year < 9999:` 改成 `else:`，整条门仍通过）。南支要算 `year + 1`，
    #    9999 年会算到 10000 ⇒ 必须单独喂一个南半球形态的规格。
    south = module.parse_posix_tz("AAA0BBB,M11.1.0,M3.2.0")  # start 11 月、end 3 月 ⇒ s > e
    assert south is not None, f"[{copy_id}] 前提不成立：南半球规格本应解析成功"
    assert south._dst_window(9999)[0] > south._dst_window(9999)[1], (
        f"[{copy_id}] 前提不成立：该规格在 9999 年不是南半球形态（s > e），压不到南支守卫"
    )
    try:
        datetime(9999, 12, 15, 12, tzinfo=timezone.utc).astimezone(south)
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(
            f"[{copy_id}] 南半球分支的候选年上界失效: 9999-12-15 换算抛 "
            f"{type(exc).__name__}: {exc}\n"
            "  南支要取 `_dst_window(year + 1)`，year=9999 时会算到 10000。"
        ) from exc


#: 这里用标签选、bytes 值放字典里，纯粹是为了让 test id 可读。
#: ⛔ 初版注释把理由写成「bytes 不能直接 parametrize，pytest 生成 id 时会抛」——
#:    **那是错的**（Codex r6 LOW 实测：直接参数化两个非 UTF-8 bytes，Python 3.14.4 +
#:    pytest 9.0.2 下 `2 passed`、rc=0，id 自动转义）。真正让本文件在**收集期** ERROR 的
#:    是 docstring 里写了转义序列的字面拼法 —— 它被 Python 当转义展开成真实代理字符，
#:    编译整份源码时就抛（不需要 pytest rewrite，直接 `compile()` 即可复现）。
_NON_UTF8_TZ_BYTES = {"dst-side": b"AAA0<\xff>", "std-side": b"<\xff>0BBB"}


@pytest.mark.parametrize("copy_id", _COPY_IDS)
@pytest.mark.parametrize("side", sorted(_NON_UTF8_TZ_BYTES))
def test_display_tz_survives_non_utf8_tz_bytes(copy_id, side):
    """`TZ` 是**环境变量**，里面可以有任意字节 —— `display_tz()` 不得因此抛异常。

    ⛔ 这条守的是本卡引入过的一个**启动失败**面（Codex r5 H1）：长度检查改用
    `len(spec.encode("utf-8"))` 之后，Python 会把非法字节读成**代理对**（0xFF 字节读成
    U+DCFF），而严格 `.encode()` 对代理对抛 `UnicodeEncodeError`。
    ⚠️ 本 docstring 里刻意**不写**那个转义序列的字面拼法 —— 它在普通字符串里会被 Python
    当转义展开成真实的代理字符，pytest 的 assertion rewrite 随后编码整份源码时就会抛，
    整个文件在**收集期** ERROR（本卡实测踩过）。
    而 `review_overview` 的**模块级**启动校验就调 `display_tz()` ⇒ 带这种 `TZ` 的宿主上
    应用根本起不来；BASE 在同样输入下只是正常退 UTC。
    修法是 `encode("utf-8", "surrogateescape")` —— 它把代理对编回原字节，
    数出来正是 C 库实际收到的字节数。

    ⚠️ 本门只钉「不抛」。这些串本机 C 库是接受的，换算结果是否与 C 库一致不在本门范围。
    """
    raw_tz = _NON_UTF8_TZ_BYTES[side]
    saved_tz = os.environb.get(b"TZ")
    saved_canvas = os.environ.get("CANVAS_TZ")
    os.environ.pop("CANVAS_TZ", None)
    try:
        os.environb[b"TZ"] = raw_tz
        time.tzset()
        try:
            resolved = _display_tz_of(copy_id)
        except Exception as exc:  # noqa: BLE001 —— 任何异常都是失败
            raise AssertionError(
                f"[{copy_id}] display_tz() 在 TZ={raw_tz!r} 下抛了 "
                f"{type(exc).__name__}: {exc}\n"
                "  环境变量里的非法字节被 Python 读成代理对，严格 encode 会对它抛，\n"
                "  而 review_overview 的模块级启动校验就调这个函数 ⇒ 应用起不来。"
            ) from exc
        # ⛔ 不能只验「不抛」（Codex r6 HIGH）：本卡 r5 就是只满足了这一条 ——
        #    改用 `surrogateescape` 后函数确实不抛了，但 `.key` 带着代理字符一路进
        #    API 响应，在 `JSONResponse` 的编码边界**再炸一次**。修复只是把失败从
        #    启动挪到了响应出口。所以这里一并钉住**出口**。
        key = getattr(resolved, "key", None)
        try:
            json.dumps({"display_tz": key}, ensure_ascii=False).encode("utf-8")
        except Exception as exc:  # noqa: BLE001
            raise AssertionError(
                f"[{copy_id}] TZ={raw_tz!r} 下 display_tz() 没抛，但它的 .key={key!r} "
                f"过不了响应序列化: {type(exc).__name__}: {exc}\n"
                "  不可严格 UTF-8 编码的规格串整个不该被接受（退 None ⇒ 退 UTC，与 BASE 同行为），\n"
                "  而不是用 surrogateescape 放行、把代理字符留在 .key 里。"
            ) from exc
    finally:
        if saved_tz is None:
            os.environb.pop(b"TZ", None)
        else:
            os.environb[b"TZ"] = saved_tz
        if saved_canvas is not None:
            os.environ["CANVAS_TZ"] = saved_canvas
        time.tzset()


#: 省略规则分支**不得扩大错误接受面**（Codex r1 HIGH-2）。下面这些串在 BASE 上就返回
#: `None`（⇒ `display_tz()` 退 UTC）。⛔ 别把这句写成「退 UTC，与 C 库一致」（Codex r5 L3
#: 证伪）：其中若干串 C 库是**接受**的 —— 例如 `AAA12BBB-12` 在 2026-07-01T23:30Z 上
#: C 库给 `07-02 11:30 +12h` 而 BASE/HEAD 都退 UTC 归 07-01。那属于**既有**支持缺口
#: （BASE 同样如此），本门守的是「本卡没有把它们从退 UTC 变成被接受」。补默认规则时
#: 若不先校验偏移，它们会
#: 变成「被接受并参与换算」——`AAA0:60BBB` 直接错一天，`AAA999BBB` 则在 `.isoformat()`
#: 处抛 `ValueError`。⛔ 本门守的是「修复没有顺手放宽别的东西」，不是解析器的取值域本身
#: （后者是上一轮登记的 MEDIUM，本卡不动带显式规则的那条路径）。
#: (spec, 为什么该拒)
_OMITTED_RULE_REJECT_CASES = [
    ("AAA0:60BBB", "分钟 60 越界 —— C 库拒收整串退 UTC（实测 2026-01-20T00:30Z 给 00:30 = UTC）"),
    ("AAA0:0:61BBB", "秒 61 越界 —— C 库拒收；被接受则算出 −00:01:01，与 C 库差 61 秒"),
    ("AAA999BBB", "偏移 999 小时不可表示 —— 被接受后会在 .isoformat() 抛 ValueError"),
    ("AAA24BBB", "std 侧 24h：POSIX 小时字段允许 24，但 Python tzinfo 要求**严格**小于"),
    ("AAA-24BBB", "同上，负向"),
    ("AAA25BBB", "同上，超界"),
    # ⛔ 下面两条各自只让**一侧**越界 —— 没有它们，实现退化成「只检查 std 侧」或
    #    「只检查 dst 侧」时上面那几条照样全绿（Codex r2 MEDIUM-2 实测过这个退化面：
    #    仅删掉 `or abs(dst_off) >= 86400`，5 拒 + 3 正控全部仍绿）。
    ("AAA0BBB24", "dst 侧 −24h 不可表示（std=0 合法）"),
    ("AAA24BBB0", "std 侧 −24h 不可表示（dst=0 合法）"),
    # ⛔ 上面两条**不是**真正的单侧测试：它们的两侧之差也 ≥24h，会被差值检查顺带挡住 ——
    #    只删单侧检查它们照样红（本卡负控 ⑨ 实测过这个盲点）。下面两条才是：
    #    两侧之差 = 1 小时 < 24h，只有对应那一侧的独立检查能拦。
    ("AAA23BBB24", "**只有 dst 侧**检查能拦：std=−23h 合法、差=1h 合法、dst=−24h 不可表示"),
    ("AAA24BBB23", "**只有 std 侧**检查能拦：dst=−23h 合法、差=1h 合法、std=−24h 不可表示"),
    # DST 差恰为 24h：两侧**各自**都在 24h 内，`utcoffset()` 也算得出，但 `dst()` 与
    # `timetuple()` 会抛 ValueError（差值本身不可表示）⇒ 必须单独检查差。
    ("AAA12BBB-12", "两侧各自合法但**差**恰为 24h —— dst() / timetuple() 会抛"),
    # Python 的 `\d` 连全角数字一起匹配；C 库对这串整串拒收。
    ("AAA１BBB", "非 ASCII 数字：正则放行但 C 库拒收，解析出 UTC−1 而 C 库给 UTC"),
    # POSIX 要求 std 名后必须跟偏移；缺了它 C 库整串拒收。
    ("<AAA><BBB>", "标准偏移缺省 —— 补规则后算成 UTC+1，C 库给 UTC，差一整天"),
    # ⛔ 负向差值：`abs()` 少写一层就漏（把 `abs(dst_off - std_off)` 写成
    #    `(dst_off - std_off)` 时，13 拒 + 3 正**全部仍绿**而本串被接受 —— Codex r2
    #    MEDIUM-1 的整改自己也需要一条防退化用例）。
    ("AAA-12BBB12", "DST 差为 **−24h**：两侧各自合法，只有带 abs() 的差值检查能拦"),
    # 正则用 `$` + `.match()`，Python 的 `$` 会在**末尾换行之前**收尾 ⇒ 带 LF 的串能匹配。
    ("AAA0<BBB>\n", "末尾 LF：C 库整串拒收退 UTC，补规则后算成 +01:00 差一整天"),
    # 名字长度在既有正则里无上限。C 库实测: `"A"*507+"0BBB"`（511 字节）接受、
    # `"A"*508+"0BBB"`（512 字节）退 UTC —— 那是**名字**长度的边界、且 507 是平台相关的
    # 魔数，所以本实现改用保守的整串 **255 字节**上限。
    ("A" * 508 + "0BBB", "整串 512 字节：C 库退 UTC（511 字节则接受），本实现按 255 字节上限拒"),
    # ⛔ 长度必须按 **UTF-8 字节**量：`len(spec)` 数的是 Unicode 字符，下面这串只有 176 个
    #    字符却是 516 字节 —— 按字符量会放行，而 C 库拒收退 UTC ⇒ 差一整天（Codex r4 HIGH-1）。
    ("AAA0<" + "中" * 170 + ">", "176 字符 / **516 字节**：按字符量会放行，按字节量才拦得住"),
    ("<" + "中" * 170 + ">0BBB", "同形，落在**标准侧**引用名上"),
    # ⛔ NUL 进不了完整的 C 环境字符串，但**能从 JSON 的 `display_tz` 自报值进来** ——
    #    桶位门会用本函数重建生产者时区（Codex r5 M1：BASE 拒收，补规则后整串放行）。
    ("AAA0<B\x00BB>", "引用名内含 NUL：走 JSON 自报值这条路进来，BASE 拒而补规则后会放行"),
]

#: 正控：秒字段 60 **不该**被这条收紧误伤 —— C 库实测也接受它（`2026-01-20T00:30Z` 给
#: `00:29−00:01`），两边一致。没有这条，「省略规则一律拒」的实现也能把上面五条跑绿。
_OMITTED_RULE_ACCEPT_CASES = [
    ("AAA0:0:60BBB", "秒字段 60：C 库接受并给 −00:01，本实现必须跟随"),
    ("CET-1CEST", "本卡要修的正例"),
    ("XYZ5XYD", "自造名正例"),
]


@pytest.mark.parametrize("copy_id", _COPY_IDS)
@pytest.mark.parametrize("spec,why", _OMITTED_RULE_REJECT_CASES)
def test_omitted_rule_branch_does_not_widen_the_accepted_offset_domain(copy_id, spec, why):
    """补默认规则**不得**把原本退 UTC 的非法偏移串变成有效时区。"""
    module = backend_tz if copy_id == "backend" else _load_local_tz()
    got = module.parse_posix_tz(spec)
    assert got is None, (
        f"[{copy_id}] 省略规则分支扩大了错误接受面: parse_posix_tz({spec!r}) 返回 {got!r}，应为 None\n"
        f"  {why}\n"
        "  补默认规则前必须先校验两侧偏移（分钟 >59 拒、|偏移| ≥24h 拒），否则这条修复\n"
        "  会把一批 C 库都不认的串放进归日链路。"
    )


#: 正控要验的不只是「非 None」，还要验**换算结果**与 C 库逐时刻一致 —— 否则一个
#: 「返回一个随便什么 tzinfo」的实现也能把正控跑绿（Codex r2 MEDIUM-2）。
#: (spec, 探针 UTC 时刻)
_OMITTED_RULE_ACCEPT_PROBES = {
    "AAA0:0:60BBB": datetime(2026, 1, 20, 0, 30, tzinfo=timezone.utc),
    "CET-1CEST": datetime(2026, 7, 31, 22, 30, tzinfo=timezone.utc),
    "XYZ5XYD": datetime(2026, 7, 31, 16, 30, tzinfo=timezone.utc),
}


@pytest.mark.parametrize("copy_id", _COPY_IDS)
@pytest.mark.parametrize("spec,why", _OMITTED_RULE_ACCEPT_CASES)
def test_omitted_rule_offset_guard_does_not_overreach(tz_env, copy_id, spec, why):
    """上一条的正控：偏移收紧不得误伤 C 库接受的串，且换算结果要跟 C 库对齐。"""
    module = backend_tz if copy_id == "backend" else _load_local_tz()
    got = module.parse_posix_tz(spec)
    assert got is not None, (
        f"[{copy_id}] 偏移收紧误伤了合法串: parse_posix_tz({spec!r}) 返回 None\n"
        f"  {why}\n"
        "  没有这条正控，「省略规则一律拒」的实现也能把上面那些拒绝用例跑绿。"
    )
    # 不只看「非 None」：拿 C 库当 oracle 验一个具体时刻的换算
    instant = _OMITTED_RULE_ACCEPT_PROBES[spec]
    tz_env(tz=spec)
    assert instant.astimezone(got).replace(tzinfo=None) == instant.astimezone().replace(tzinfo=None), (
        f"[{copy_id}] {spec!r} 被接受了，但换算结果与 C 库不符: "
        f"本实现给 {instant.astimezone(got).replace(tzinfo=None)}，"
        f"C 库给 {instant.astimezone().replace(tzinfo=None)}"
    )


#: 省略切换规则时，C 库把**秋季回拨**钉在当地**标准**时 01:00 —— 而 POSIX 的 `/时刻`
#: 语义指的是**切换前生效**的那一侧（end 之前生效的是夏令侧）。两者只在夏令时差恰为
#: +1 小时时重合，所以 end 的切换时刻必须按 `3600 + dst_off − std_off` 现算，不能写死
#: 「当地 02:00」。⛔ 写死 02:00 的实现只有在「省略 dst 偏移」那一族（Δ 恒 +1h）上才对 ——
#: 只测那一族就会把子族结论当成全族结论（本卡 r2 实测：156 万点逐分钟里，Δ=+1h 的两个
#: 规格 0 分歧，而 Δ∈{−2h,−1h,+1.5h,+4h} 的四个规格共 15810 分钟与 C 库不符）。
#: ⛔ 年份钉在 2007..2037：见 `_DST_PROBE_INSTANTS` 上方那条区间说明。
#: (spec, 夏令时差, 扫描起点 UTC, 分钟数)
_OMITTED_RULE_TRANSITION_SCANS = [
    ("IST-1GMT0", "-1h", datetime(2026, 10, 31, 23, 30, tzinfo=timezone.utc), 90),
    ("ABC-1DEF-5", "+4h", datetime(2026, 10, 31, 23, 30, tzinfo=timezone.utc), 90),
    ("NZST-12NZDT-13:30", "+1.5h", datetime(2026, 10, 31, 12, 30, tzinfo=timezone.utc), 90),
    ("AAA5BBB7", "-2h", datetime(2026, 11, 1, 5, 30, tzinfo=timezone.utc), 90),
    # 对照组：Δ=+1h 这一族两种写法**本就重合** —— 有它在，「四条红」才能归因到偏移差
    # 那一维上，而不是「省略规则的实现整个是坏的」。
    ("CET-1CEST", "+1h", datetime(2026, 10, 31, 23, 30, tzinfo=timezone.utc), 90),
    # 春季侧正控：前跳钉在当地**标准**时 02:00，两种写法一致 —— 证明本门不是只对秋季敏感，
    # 也证明 start 用 `_parse_rule` 缺省（7200）是对的。
    ("IST-1GMT0", "-1h", datetime(2026, 3, 8, 0, 30, tzinfo=timezone.utc), 90),
    ("ABC-1DEF-5", "+4h", datetime(2026, 3, 8, 0, 30, tzinfo=timezone.utc), 90),
]


@pytest.mark.parametrize("copy_id", _COPY_IDS)
@pytest.mark.parametrize("spec,dst_span,scan_from,minutes", _OMITTED_RULE_TRANSITION_SCANS)
def test_omitted_rule_transition_points_track_the_standard_side_offset(
    tz_env, spec, dst_span, scan_from, minutes, copy_id
):
    """省略规则时补出来的切换点必须与 C 库逐分钟对齐，含**夏令时差 ≠ +1h** 的各族。

    ⛔ 为什么必须逐分钟而不是逐小时：分歧窗宽度 = |Δ − 1h|，`<+10:30>` 这类半小时跨度
    只有 30 分钟宽 —— 逐小时网格恰好采样不到（本卡实测过这个盲点：同一规格逐小时
    mismatch=0、逐分钟 mismatch=30）。仓内规则里「门绿≠锁住修复：探针避开缺陷显形点」
    说的就是这个形态。
    """
    tz_env(tz=spec)
    resolved = _display_tz_of(copy_id)
    for i in range(minutes):
        instant = scan_from + timedelta(minutes=i)
        converted = instant.astimezone(resolved)
        got = converted.replace(tzinfo=None)
        libc = instant.astimezone().replace(tzinfo=None)
        assert got == libc, (
            f"[{copy_id}] 省略规则的切换点与 C 库不符: TZ={spec!r}(夏令时差 {dst_span}) "
            f"在 {instant.isoformat()}\n"
            f"  本实现给 {got}，C 库给 {libc}\n"
            "  end 的切换时刻要按 `3600 + dst_off − std_off` 现算（C 库钉的是当地**标准**时\n"
            "  01:00）；写死「当地 02:00」只在夏令时差恰为 +1 小时时才对。"
        )
        assert converted.astimezone(timezone.utc) == instant, (
            f"[{copy_id}] 省略规则的切换点附近**时刻不守恒**: TZ={spec!r} 在 {instant.isoformat()}\n"
            f"  换算得 {converted!r}，转回 UTC 是 {converted.astimezone(timezone.utc).isoformat()}\n"
            "  折叠/空缺时段的 fold 标错了。"
        )


#: 规则**不写** `/时刻` ⇒ 切换时刻走 POSIX 缺省。逐分钟扫切换点前后。
#: ⛔ 缺省是当地 02:00:00。曾误写成加两分钟，于是切换后头两分钟的墙钟比 C 库慢
#: 一档 —— 而 ⑦ 那 9 个整点/半点探针一格都踩不到，238 组对照全绿仍带着这个缺陷。
#: 「切换点两侧逐分钟」是这类偏移唯一的显形面，只测整点等于没测。
_DEFAULT_TRANSITION_SCANS = [
    ("EST5EDT,M3.2.0,M11.1.0", datetime(2026, 3, 8, 6, 50, tzinfo=timezone.utc), 30),
    ("EST5EDT,M3.2.0,M11.1.0", datetime(2026, 11, 1, 5, 50, tzinfo=timezone.utc), 30),
    ("IST-1GMT0,M10.5.0,M3.5.0/1", datetime(2026, 10, 25, 0, 30, tzinfo=timezone.utc), 60),
]


@pytest.mark.parametrize("copy_id", _COPY_IDS)
@pytest.mark.parametrize("tz_value,scan_from,minutes", _DEFAULT_TRANSITION_SCANS)
def test_default_transition_time_matches_libc_minute_by_minute(tz_env, tz_value, scan_from, minutes, copy_id):
    """规则不写 `/时刻` 时，切换必须落在当地 02:00:00，逐分钟与 C 库对齐。"""
    tz_env(tz=tz_value)
    resolved = _display_tz_of(copy_id)
    for i in range(minutes):
        instant = scan_from + timedelta(minutes=i)
        converted = instant.astimezone(resolved)
        got = converted.replace(tzinfo=None)
        libc = instant.astimezone().replace(tzinfo=None)
        assert got == libc, (
            f"[{copy_id}] TZ={tz_value!r} 在 {instant.isoformat()} 上缺省切换时刻与 C 库不符：\n"
            f"  本实现给 {got}，C 库给 {libc}\n"
            "  规则没写 /时刻 时，切换必须发生在当地 02:00:00。"
        )
        # 墙钟只测 fromutc 的「算成几点」，测不到它给这个墙钟标的 fold 对不对。
        # 切换点两侧恰好是折叠/空缺时段，fold 标错在这里才会让时刻转不回去。
        assert converted.astimezone(timezone.utc) == instant, (
            f"[{copy_id}] TZ={tz_value!r} 在 {instant.isoformat()} 上切换点附近**时刻不守恒**：\n"
            f"  换算得 {converted!r}，转回 UTC 是 {converted.astimezone(timezone.utc).isoformat()}\n"
            "  fromutc 给折叠时段的墙钟标错了 fold。"
        )


#: (规格, 折叠窗口内的墙钟, 空缺窗口内的墙钟)。第三个是**负偏移差**规格：
#: 标准侧 UTC+1 比另一侧 UTC+0 偏移大，fold 的两个方向与前两个正好相反。
_FOLD_CONTRACT_CASES = [
    ("EST5EDT,M3.2.0,M11.1.0", datetime(2026, 11, 1, 1, 30), datetime(2026, 3, 8, 2, 30)),
    ("NZST-12NZDT,M9.5.0,M4.1.0/3", datetime(2026, 4, 5, 2, 30), datetime(2026, 9, 27, 2, 30)),
    ("IST-1GMT0,M10.5.0,M3.5.0/1", datetime(2026, 10, 25, 1, 30), datetime(2026, 3, 29, 1, 30)),
]


@pytest.mark.parametrize("copy_id", _COPY_IDS)
@pytest.mark.parametrize("tz_value,fold_wall,gap_wall", _FOLD_CONTRACT_CASES)
def test_fold_side_is_chosen_by_offset_size_not_summer_time_identity(tz_env, tz_value, fold_wall, gap_wall, copy_id):
    """折叠/空缺的选侧判据是**偏移大小**，不是「哪一侧叫夏令时」。

    Python 的 fold 契约与夏令时身份无关：fold=0 恒指**先发生**的那一次。
      · 折叠（时钟回拨）⇒ 先发生的是偏移**较大**的一侧；
      · 空缺（时钟前跳）⇒ fold=0 取切换**前** = 偏移**较小**的一侧。
    正偏移差的规格里「较大的那侧恰好就是夏令时侧」，按身份写死也能全绿；
    负偏移差的规格两者方向相反，写死身份会把 fold 语义整个颠倒。

    ⛔ 两条断言方向相反，互为对方的验伪锚：若探针墙钟根本不在折叠/空缺窗口内，
    两个 fold 会给出**相同**偏移，两条严格不等式同时失败，门不会恒真。
    ⛔ 这里不与 C 库对照 —— C 库对折叠墙钟取哪一侧是实现定义的，拿它当判据
    等于把判据交给平台。fold 契约本身就是判据。
    """
    tz_env(tz=tz_value)
    resolved = _display_tz_of(copy_id)

    first = fold_wall.replace(tzinfo=resolved, fold=0)
    second = fold_wall.replace(tzinfo=resolved, fold=1)
    assert first.utcoffset() > second.utcoffset(), (
        f"[{copy_id}] TZ={tz_value!r} 折叠墙钟 {fold_wall} 的 fold=0 没取偏移较大的一侧：\n"
        f"  fold=0 给 {first.utcoffset()}，fold=1 给 {second.utcoffset()}\n"
        "  回拨时先发生的是偏移较大那侧；按夏令时身份选侧在负偏移差规格上就是反的。"
    )
    assert first.astimezone(timezone.utc) < second.astimezone(timezone.utc), (
        f"[{copy_id}] TZ={tz_value!r} 折叠墙钟 {fold_wall} 的 fold=0 不是**先发生**的那次：\n"
        f"  fold=0 → {first.astimezone(timezone.utc).isoformat()}，"
        f"fold=1 → {second.astimezone(timezone.utc).isoformat()}"
    )
    assert second.astimezone(timezone.utc) - first.astimezone(timezone.utc) == (
        first.utcoffset() - second.utcoffset()
    ), f"[{copy_id}] TZ={tz_value!r} 折叠墙钟 {fold_wall} 两次出现的间隔不等于偏移差"

    before = gap_wall.replace(tzinfo=resolved, fold=0)
    after = gap_wall.replace(tzinfo=resolved, fold=1)
    assert before.utcoffset() < after.utcoffset(), (
        f"[{copy_id}] TZ={tz_value!r} 空缺墙钟 {gap_wall} 的 fold=0 没取切换**前**的偏移：\n"
        f"  fold=0 给 {before.utcoffset()}，fold=1 给 {after.utcoffset()}\n"
        "  前跳跳过的墙钟，fold=0 按约定取切换前 = 偏移较小那侧。"
    )


#: (规格串, 是否应当解析成功, 依据)。⛔ 判据绑 **POSIX 规格**而不是 C 库：本实现
#: 是规格驱动的，与平台的宽松处有意分歧（如 macOS 接受两字母简名 `AB3`，规格
#: 要求 ≥3 字符 —— 已登记，不跟）。这里钉住的是我们自己的取值域有没有写错。
_RULE_RANGE_CASES = [
    ("EST5EDT,J0,M11.1.0", False, "`Jn` 的下界是 1，不是 0"),
    ("EST5EDT,J1,M11.1.0", True, "`J1` = 1 月 1 日"),
    ("EST5EDT,J365,M11.1.0", True, "`J365` 是上界"),
    ("EST5EDT,J366,M11.1.0", False, "`Jn` 不数闰日，366 越界"),
    ("EST5EDT,0,M11.1.0", True, "裸 `n` 的下界是 0"),
    ("EST5EDT,365,M11.1.0", True, "裸 `n` 的上界是 365"),
    ("EST5EDT,366,M11.1.0", False, "裸 `n` 越界"),
    ("EST5EDT,M13.2.0,M11.1.0", False, "月份 1..12"),
    ("EST5EDT,M3.6.0,M11.1.0", False, "周序 1..5"),
    ("EST5EDT,M3.2.7,M11.1.0", False, "星期 0..6"),
]


@pytest.mark.parametrize("copy_id", _COPY_IDS)
@pytest.mark.parametrize("spec,should_parse,why", _RULE_RANGE_CASES)
def test_posix_rule_ranges_follow_the_spec_not_one_shared_bound(copy_id, spec, should_parse, why):
    """`Jn` 与裸 `n` 的取值域**不同**，一个范围管两边就会放行 `J0`。

    ⛔ 曾把两者合写成 `0 <= n <= 365`：`Jn` 是 1..365（不数闰日），裸 `n` 是
    0..365（数闰日）。C 库对 `J0` 整串拒收，混用会让本实现比它宽——落到一个
    C 库根本不认的规则上算「今天」，而且不报错。
    ⛔ 表里同时有该接受与该拒绝的两侧：只留一侧的话，「恒接受」或「恒拒绝」
    的实现都能把门跑绿。
    """
    module = backend_tz if copy_id == "backend" else _load_local_tz()
    got = module.parse_posix_tz(spec)
    if should_parse:
        assert got is not None, f"[{copy_id}] {spec!r} 应当解析成功（{why}），却被拒绝了"
    else:
        assert got is None, f"[{copy_id}] {spec!r} 应当被拒绝（{why}），却解析成功了：{got!r}"


def test_posix_probe_actually_differs_from_etc_localtime(tz_env):
    """⑦ 的**前提断言**：探针用的 TZ 必须与宿主 `/etc/localtime` 给出不同答案。

    没有这条，⑦ 在「宿主时区恰好与探针 TZ 同解」的机器上会变成恒真 ——
    那时「继续读 /etc/localtime」这条缺陷根本无从暴露（Codex r2 MEDIUM 实测：
    把 `/etc/localtime` 设为 UTC 后 M4 的三个参数全部通过）。
    """
    tz_env(tz=None, canvas_tz=None)
    host = ro._display_tz()  # 无 TZ ⇒ 走 /etc/localtime 那一档
    differing = []
    for tz_value in _POSIX_TZ_VALUES:
        tz_env(tz=tz_value)
        resolved = ro._display_tz()
        if any(
            i.astimezone(resolved).replace(tzinfo=None) != i.astimezone(host).replace(tzinfo=None)
            for i in _DST_PROBE_INSTANTS
        ):
            differing.append(tz_value)
    assert differing, (
        f"本宿主的 /etc/localtime（{host!r}）与全部探针 TZ 在所有探测时刻上给出相同答案 —— "
        "门 ⑦ 在这台机器上无法区分「读了 TZ」与「读了 /etc/localtime」，是恒真的。"
        "⛔ 这是宿主形态问题，须登记并报主 session，不得改判据放行。"
    )


def test_valid_tz_names_still_win_over_process_local(tz_env):
    """⑦ 的正控：`TZ` 是合法 IANA 名时仍走 ZoneInfo（有 `.key`），没被上面那条修复带偏。"""
    tz_env(tz="America/New_York")
    resolved = ro._display_tz()
    assert getattr(resolved, "key", None) == "America/New_York", f"合法 IANA 名应直接解析成有名时区，实得 {resolved!r}"


# ══════════════════════════════════════════════════════════════════════════
# ⑧ 桶位门以投影**自带**的时区为参照，切时区不得把合法投影判成 corrupt
#    （Codex r1 HIGH-2）
# ══════════════════════════════════════════════════════════════════════════


def test_bucket_gate_uses_projection_own_tz_not_current_display_tz(tmp_path, tz_env):
    """一份合法投影，在任何显示时区下复算都必须被放行。

    ⛔ 场景：用户在上海生成了今天的投影（`generated_at` 带 `+08:00`），随后改了
    时区。投影内容一个字节没变、仍然自洽，但门若用**此刻**的显示时区重算参照日，
    就会说「future 桶里那条应该在 due_today」并把整份投影判成 corrupt ——
    页面上显示「投影损坏」，而它其实好好的。

    门的职责是校验「这份产出自不自洽」，参照系必须取 `generated_at` 自带的偏移。
    「投影是不是今天的」是另一件事，由 `_vault_entry` 的 stale 判定负责（那里用
    此刻的时区才对：切时区后它变 stale ⇒ 触发重新生成，是正确行为）。
    """
    sys.path.insert(0, str(REPO_SCRIPTS))
    import daily_review_pick as picker  # noqa: PLC0415  # pyright: ignore[reportMissingImports]

    # ⛔ 走 **_summarize**（_gate_buckets 的唯一生产调用方）而不是自己拼调用：
    #    `producer_tz=payload.get("display_tz")` 那一行接线就在它内部。三处门此前
    #    都自己复刻了那一行 —— 于是把生产侧的接线删掉，门照样全绿（自验实测
    #    变异 D SURVIVED）。这是本文件第二次栽在「复刻而非调用」上。
    from app.api.v1.endpoints.review_overview import _summarize  # noqa: PLC0415

    vault = _tmp_vault(tmp_path, name="vaultGate")
    # 17:00Z 到期：在上海是次日 01:00（future），在 UTC 是当日 17:00（due_today）——
    # 正是「换个时区结论就翻面」的那种节点
    (vault / "节点" / "甲.md").write_text(
        '---\ntype: concept\nsource_board: "[[原白板/板]]"\nfsrs_due: 2026-07-31T17:00:00Z\n---\n内容。\n',
        encoding="utf-8",
    )
    tz_env(canvas_tz="Asia/Shanghai")
    picker_tz_saved = picker._DISPLAY_TZ
    picker._DISPLAY_TZ = ZoneInfo("Asia/Shanghai")
    try:
        moment = datetime(2026, 7, 31, 15, 0, tzinfo=timezone.utc)  # 上海 7/31 23:00
        payload, _ranked = picker.build_payload(vault, moment, {}, picker.load_decay(vault))
    finally:
        picker._DISPLAY_TZ = picker_tz_saved

    assert payload["generated_at"].endswith("+08:00"), f"前提：投影须由上海时区生成，实得 {payload['generated_at']}"
    where = {
        n: b for b, rows in payload["buckets"].items() if isinstance(rows, list) for n in (r["node"] for r in rows)
    }
    assert where.get("甲") == "future", f"前提：上海视角下甲应属 future（次日 01:00 到期），实得 {where}"

    def _gate() -> None:
        _summarize(payload)

    for tz_name in ("Asia/Shanghai", "UTC", "America/Los_Angeles"):
        tz_env(canvas_tz=tz_name)
        try:
            _gate()
        except ValueError as exc:
            raise AssertionError(
                f"显示时区切到 {tz_name} 后，同一份合法投影被门拒绝：{exc}\n"
                "门用了此刻的显示时区当参照日 —— 应改用 generated_at 自带的偏移。"
            ) from exc


# ══════════════════════════════════════════════════════════════════════════
# ⑨ DST 边界上的桶位参照系（Codex r2 HIGH-2：r1 的整改造成了缺陷位移）
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "producer_tz,moment_iso,due_iso,gate_tz,expect_bucket,label",
    [
        # 纽约在 EST 时刻生成、节点在 EDT 时刻到期：只有**完整时区规则**判得对。
        # 拿 generated_at 自带的固定 -05:00 换算，会把次日的到期算成同日 ⇒ 误拒。
        (
            "America/New_York",
            "2026-03-08T05:30:00Z",
            "2026-03-09T04:30:00Z",
            "America/New_York",
            "future",
            "春季前跳·NY 生成 NY 显示",
        ),
        # 秋季回拨：due 在 NY 是 11-01 23:30 EST，与 gen 的 11-01 **同日**；
        # 固定 -04:00 会算成 11-02 ⇒ 误判 future。
        (
            "America/New_York",
            "2026-11-01T04:30:00Z",
            "2026-11-02T04:30:00Z",
            "America/New_York",
            "due_today",
            "秋季回拨·NY 生成 NY 显示",
        ),
        # ⛔ Codex r3 反例：Bogota 与 New_York 在 generated_at 那一刻**同为 -05:00**，
        #    但规则不同（Bogota 恒 -05:00，NY 会进 EDT）。靠"偏移是否匹配"猜生成时区，
        #    这里会猜成 NY，把 Bogota 的合法 due_today 判成 future。
        #    只有生产器**自报**时区名才判得对。
        (
            "America/Bogota",
            "2026-03-08T05:30:00Z",
            "2026-03-09T04:30:00Z",
            "America/New_York",
            "due_today",
            "同偏移不同规则·Bogota 生成 NY 显示",
        ),
        # 切了时区：当前显示时区在 generated_at 那刻的偏移与它自带的不符
        # ⇒ 退回自带偏移，合法投影必须仍被放行（r1 HIGH-2）。
        ("Asia/Shanghai", "2026-07-31T15:00:00Z", "2026-07-31T17:00:00Z", "UTC", "future", "切时区·上海生成 UTC 显示"),
        ("Asia/Shanghai", "2026-07-31T01:00:00Z", "2026-07-31T13:00:00Z", "Asia/Shanghai", "due_today", "同区当日"),
    ],
)
def test_bucket_gate_reference_day_handles_dst_and_tz_switch(
    tmp_path, tz_env, producer_tz, moment_iso, due_iso, gate_tz, expect_bucket, label
):
    """桶位门的参照系必须在 DST 边界与切时区两种情形下都放行合法投影。

    ⛔ **走真实 `_gate_buckets`**，不在测试里复刻那行参照系逻辑：初版就是复刻的，
    结果把参照系改成任一极端（变异 M5 / M7）门都毫无反应 —— 复刻出来的是我自己
    抄的公式，不是被测代码（矩阵文件 round-1 栽过同一个坑）。

    两个极端都被这组用例否掉：
      · 恒用投影自带的固定偏移 ⇒ 两条 DST 用例误判（M5）；
      · 恒用此刻的显示时区 ⇒「切时区」那条误判成 corrupt（M7）。
    """
    sys.path.insert(0, str(REPO_SCRIPTS))
    import daily_review_pick as picker  # noqa: PLC0415  # pyright: ignore[reportMissingImports]

    # ⛔ 走 **_summarize**（_gate_buckets 的唯一生产调用方）而不是自己拼调用：
    #    `producer_tz=payload.get("display_tz")` 那一行接线就在它内部。三处门此前
    #    都自己复刻了那一行 —— 于是把生产侧的接线删掉，门照样全绿（自验实测
    #    变异 D SURVIVED）。这是本文件第二次栽在「复刻而非调用」上。
    from app.api.v1.endpoints.review_overview import _summarize  # noqa: PLC0415

    vault = _tmp_vault(tmp_path, name=f"vaultGate{abs(hash(label)) % 10**6}")
    (vault / "节点" / "甲.md").write_text(
        f'---\ntype: concept\nsource_board: "[[原白板/板]]"\nfsrs_due: {due_iso}\n---\n内容。\n',
        encoding="utf-8",
    )
    # 生产器侧钉在 producer_tz（pick 用模块级常量，setenv 对已 import 的它无效）
    saved = picker._DISPLAY_TZ
    picker._DISPLAY_TZ = ZoneInfo(producer_tz)
    try:
        moment = datetime.fromisoformat(moment_iso.replace("Z", "+00:00"))
        payload, _ranked = picker.build_payload(vault, moment, {}, picker.load_decay(vault))
    finally:
        picker._DISPLAY_TZ = saved

    where = {
        n: b for b, rows in payload["buckets"].items() if isinstance(rows, list) for n in (r["node"] for r in rows)
    }
    assert where.get("甲") == expect_bucket, (
        f"{label}: 前提不成立 —— 生产器（{producer_tz}）把甲归入 {where.get('甲')!r}，"
        f"本用例要测的是它归入 {expect_bucket!r} 的情形。generated_at={payload['generated_at']}"
    )

    # 门在 gate_tz 下复算这份合法投影，必须放行
    tz_env(canvas_tz=gate_tz)
    try:
        _summarize(payload)
    except ValueError as exc:
        raise AssertionError(
            f"{label}: 门在显示时区 {gate_tz} 下拒绝了一份合法投影：{exc}\n"
            f"  generated_at={payload['generated_at']}  甲实际归入 {expect_bucket}\n"
            "  参照系取错了：DST 边界要用完整时区规则，切了时区要退回投影自带的偏移。"
        ) from exc


def test_bucket_gate_rejects_wrong_bucket_and_forged_display_tz(tmp_path, tz_env):
    """⑨ 的负控：门放行合法投影**不等于**它还拦得住坏的。

    r2 那版（参照系恒用 `generated_at` 自带偏移）在 DST 边界不但误拒合法投影，
    还会**放行错误归桶** —— 门比它要替换的那版更弱。所以这条把四种坏输入逐个喂进去：
      · 节点被挪到错误的桶 ⇒ 必须拒；
      · `display_tz` 伪造成与 `generated_at` 偏移不自洽的时区 ⇒ 必须拒；
      · `display_tz` 伪造成不可解析的名字 ⇒ 必须拒；
      · 旧投影（`display_tz` 键缺席或为 null）⇒ **整份拒**（CARD-G6-9c-R2）。

    每条都用 `pytest.raises(match=...)` 绑**具体拒因**，不只看「抛了异常」——
    否则「被更早的防线拒掉」也会被记成通过。
    """
    import copy  # noqa: PLC0415

    sys.path.insert(0, str(REPO_SCRIPTS))
    import daily_review_pick as picker  # noqa: PLC0415  # pyright: ignore[reportMissingImports]

    # ⛔ 走 **_summarize**（_gate_buckets 的唯一生产调用方）而不是自己拼调用：
    #    `producer_tz=payload.get("display_tz")` 那一行接线就在它内部。三处门此前
    #    都自己复刻了那一行 —— 于是把生产侧的接线删掉，门照样全绿（自验实测
    #    变异 D SURVIVED）。这是本文件第二次栽在「复刻而非调用」上。
    from app.api.v1.endpoints.review_overview import _summarize  # noqa: PLC0415

    vault = _tmp_vault(tmp_path, name="vaultNeg")
    (vault / "节点" / "甲.md").write_text(
        '---\ntype: concept\nsource_board: "[[原白板/板]]"\nfsrs_due: 2026-03-09T04:30:00Z\n---\n内容。\n',
        encoding="utf-8",
    )
    saved = picker._DISPLAY_TZ
    picker._DISPLAY_TZ = ZoneInfo("America/New_York")
    try:
        payload, _r = picker.build_payload(
            vault, datetime(2026, 3, 8, 5, 30, tzinfo=timezone.utc), {}, picker.load_decay(vault)
        )
    finally:
        picker._DISPLAY_TZ = saved

    tz_env(canvas_tz="America/New_York")

    def _gate(p):
        _summarize(p)

    _gate(payload)  # 前提：这份是合法的，门放行

    moved = copy.deepcopy(payload)
    moved["buckets"]["due_today"] = moved["buckets"]["future"]
    moved["buckets"]["future"] = []
    with pytest.raises(ValueError, match="非 generated_at 的同一本地日"):
        _gate(moved)

    for fake, pattern in (("Asia/Tokyo", "偏移不自洽"), ("Not/AZone", "不是可解析的时区名")):
        forged = copy.deepcopy(payload)
        forged["display_tz"] = fake
        # ⛔ 不用 pytest.raises(match=...)：它在「压根没抛」时的失败消息是
        #    `DID NOT RAISE`，不含 pattern —— 变异负控没法拿一个稳定的串绑住
        #    「是这一条红了」（memory：承重串别用 DID NOT RAISE）。显式写，
        #    让两种失败各自带可辨认的身份。
        try:
            _gate(forged)
        except ValueError as exc:
            assert re.search(pattern, str(exc)), f"display_tz 伪造成 {fake!r} 后门确实拒了，但拒因不是预期的那条：{exc}"
        else:
            raise AssertionError(
                f"display_tz 伪造成 {fake!r} 后门仍放行 —— payload 自洽校验失效。"
                f"（该值与 generated_at={payload['generated_at']} 的偏移不符，或根本不是可解析的时区名）"
            )

    # 旧投影（`display_tz` 键缺失或为 null）⇒ **整份判 corrupt**（CARD-G6-9c-R2）。
    # ⛔ 原先这里写的是「回退到 generated_at 自带的固定偏移 / Bogota 的 due_today 必须放行 /
    #    NY 的误判是已登记项」—— 那套说法随本卡的收口一起作废，别照抄。
    #    固定偏移只在 generated_at **那一刻**等于生产者的真实偏移；到期时刻跨了 DST 切换
    #    就差一档，而误拒与误放行是同一偏差的两侧，不可能只堵一侧。
    # ⛔ 本卡 r1 曾试过「偏移 ±2h 敏感性复算」的温和版（带内翻转才拒），被 Codex r1 打回：
    #    带宽要同时小到不误拒、大到不漏放行，而 `ABC-1DEF-5`(Δ=+4h) 就在 ±2h 带外。
    #    （Δ 是**有界**的 —— 正则字段位宽定了上界；只是那个界远大于任何实用带宽。）
    # ⚠️ 本门的正控不在下面三条，而在函数开头的 `_gate(payload)`：带 display_tz 的合法
    #    投影必须放行。没有它，「一律拒绝所有投影」的实现也能把下面三条跑绿。
    saved_b = picker._DISPLAY_TZ
    picker._DISPLAY_TZ = ZoneInfo("America/Bogota")
    try:
        bogota_payload, _r2 = picker.build_payload(
            vault, datetime(2026, 3, 8, 5, 30, tzinfo=timezone.utc), {}, picker.load_decay(vault)
        )
    finally:
        picker._DISPLAY_TZ = saved_b
    legacy_bogota = copy.deepcopy(bogota_payload)
    legacy_bogota.pop("display_tz")
    with pytest.raises(ValueError, match="display_tz 缺席或为 null"):
        _gate(legacy_bogota)  # 固定偏移语义的生产者（Bogota 恒 -05:00）也一样拒 —— 消费端分辨不出

    legacy_ny = copy.deepcopy(payload)
    legacy_ny.pop("display_tz")
    with pytest.raises(ValueError, match="display_tz 缺席或为 null"):
        _gate(legacy_ny)  # DST 边界旧投影：拒因从「仍在 generated_at（误拒）」升级为「无可信参照」

    null_ny = copy.deepcopy(payload)
    null_ny["display_tz"] = None
    with pytest.raises(ValueError, match="display_tz 缺席或为 null"):
        # 键在、值为 null —— 现役生产器在**末档宿主**上的正常产出，走的是同一条路。
        # 该形态的可用性损失已在验收单登记为取舍（正确性优先于旧投影兼容）。
        _gate(null_ny)


@pytest.mark.parametrize("legacy_form", ["missing", "null"])
def test_bucket_gate_rejects_wrong_buckets_even_when_display_tz_is_absent(tmp_path, tz_env, legacy_form):
    """旧投影落到固定偏移回退时，**错误归桶也必须被拦住**（CARD-G6-9c-R2 / HIGH-2）。

    ⛔ 这是上一条门漏掉的那一格：它测了「旧投影 + 合法桶」的两个子情形，却从没测过
    「旧投影 + **错误**桶」。Codex r5 的四格表证明这一格在 r4 实现下是**放行**的 ——
    与回退段注释里那句「但不会放行错误归桶」正好相反。

    机理：`generated_at` 自带的固定偏移只在**它自己那一刻**等于生产者的真实偏移。
    到期时刻落在 DST 切换的另一侧时，固定偏移算出的本地日与真实时区差一天 ——
    误拒（合法 future 被判成 due_today）与误放行（伪造的 due_today 被当成合法）
    是**同一个**偏差的两侧，不可能只占一侧。r4 把它登记成「只有兼容性损失」，不成立。

    ⛔ 本卡 r1 曾用「偏移 ±2h 敏感性复算」的温和版收口，被 Codex r1 打回：带宽要同时
    小到不误拒、大到不漏放行，而 `ABC-1DEF-5`(Δ=+4h) 就落在带外、伪造的 due_today
    照样放行。（Δ 是**有界**的 —— 正则字段位宽定了上界 ≈ ±83 天；只是那个界远大于任何
    实用带宽，缺 `display_tz` 时两个要求不可兼得。别写成「Δ 无界」，r2 LOW-2 证伪过。）
    现口径是**整份判 corrupt**，拒因统一为「display_tz 缺席或为 null」。

    两种旧形态都要测：`display_tz` 键缺失（历史投影）与值为 `null`
    （现役生产器在**末档宿主**上的正常产出 —— `local_tz.display_tz()` 落到固定偏移
    兜底时没有 `.key`，`daily_review_pick` 照样恒写这个键、值为 None）。
    """
    import copy  # noqa: PLC0415

    sys.path.insert(0, str(REPO_SCRIPTS))
    import daily_review_pick as picker  # noqa: PLC0415  # pyright: ignore[reportMissingImports]

    # ⛔ 走 _summarize（_gate_buckets 的唯一生产调用方），不自己拼调用 —— 同文件两处
    #    栽过「复刻而非调用」的坑（生产侧接线被删门照样绿）。
    from app.api.v1.endpoints.review_overview import _summarize  # noqa: PLC0415

    vault = _tmp_vault(tmp_path, name=f"vaultLegacy{legacy_form}")
    # NY 春季前跳：gen 在 EST(-05:00)，due 在 EDT(-04:00) ⇒ 真实本地日 = 03-09（future），
    # 固定 -05:00 算出的却是 03-08（= gen 的本地日）。两种解释相差整整一天。
    (vault / "节点" / "甲.md").write_text(
        '---\ntype: concept\nsource_board: "[[原白板/板]]"\nfsrs_due: 2026-03-09T04:30:00Z\n---\n内容。\n',
        encoding="utf-8",
    )
    saved = picker._DISPLAY_TZ
    picker._DISPLAY_TZ = ZoneInfo("America/New_York")
    try:
        payload, _r = picker.build_payload(
            vault, datetime(2026, 3, 8, 5, 30, tzinfo=timezone.utc), {}, picker.load_decay(vault)
        )
    finally:
        picker._DISPLAY_TZ = saved

    # 前提：生产器把它归进 future（这条不成立的话下面测的就不是「错误归桶」了）
    assert [r["node"] for r in payload["buckets"]["future"]] == ["甲"], (
        f"前提不成立 —— 生产器没把甲归进 future: {payload['buckets']}"
    )

    forged = copy.deepcopy(payload)
    if legacy_form == "missing":
        forged.pop("display_tz")
    else:
        forged["display_tz"] = None
    # 错误归桶：把 future 那一行整体搬进 due_today（与上一条门的 `moved` 同法）
    forged["buckets"]["due_today"] = forged["buckets"]["future"]
    forged["buckets"]["future"] = []

    tz_env(canvas_tz="America/New_York")
    try:
        _summarize(forged)
    except ValueError as exc:
        # ⛔ 绑**具体拒因**，不只看「抛了异常」—— 否则「被更早的防线拒掉」也会记成通过。
        assert "display_tz 缺席或为 null" in str(exc), f"门确实拒了，但拒因不是「无可信参照时区规则」那条：{exc}"
    else:
        raise AssertionError(
            f"固定偏移回退误放行·桶 due_today（display_tz {legacy_form}）\n"
            f"  fsrs_due=2026-03-09T04:30:00Z 在生产者时区(America/New_York)是 03-09 00:30 EDT,\n"
            f"  与 generated_at={payload['generated_at']} 的本地日 03-08 **不是同一天** ⇒ 它属 future;\n"
            "  门却用 generated_at 自带的固定 -05:00 把它算成 03-08 23:30, 于是放行了这个伪造的\n"
            "  due_today。这正是 Codex r5 HIGH-2 点名的误放行 —— 与误拒完全对称, 不是「只有\n"
            "  兼容性损失」。"
        )


# ══════════════════════════════════════════════════════════════════════════
# ⑥ 默认配置下必须是**有名**时区
# ══════════════════════════════════════════════════════════════════════════


def test_default_resolution_yields_a_named_zone(tmp_path):
    """⑥ 不设 `CANVAS_TZ` / `TZ` 时，`display_tz()` 仍须给出带 `.key` 的时区。

    为什么这条是硬要求：末档 `datetime.now().astimezone().tzinfo` 返回的是
    `datetime.timezone` 固定偏移实例，**没有 `.key`** ⇒ `_display_tz_name()` 恒
    None ⇒ GET 下发的 `display_tz` 恒 null ⇒ 前端恒退浏览器本地，本卡新建的
    「服务端下发显示时区」这条链路在**不设 CANVAS_TZ 的默认部署里一次都用不到**。
    固定偏移还会在 DST 切换后停在旧偏移上。

    ⚠️ 若某宿主真解析不到（无 `/etc/localtime`、非类 Unix），本门**如实红** ——
    那是要停下来登记的宿主形态，不是改判据放行的理由。
    """
    probe = (
        "import json,sys;"
        f"sys.path.insert(0, {str(REPO_SCRIPTS)!r});"
        "import local_tz;"
        "z = local_tz.display_tz();"
        "print(json.dumps({'key': getattr(z, 'key', None), 'repr': repr(z)}))"
    )
    env = dict(os.environ)
    env.pop("CANVAS_TZ", None)
    env.pop("TZ", None)
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "-c", probe], capture_output=True, text=True, env=env, timeout=60, check=False
    )
    assert proc.returncode == 0, f"探针崩了：{proc.stderr[-1000:]}"
    got = json.loads(proc.stdout)
    assert got["key"] is not None, (
        "默认配置下拿不到 IANA 名，落到了固定偏移末档 —— GET 的 display_tz 会恒 null、"
        f"前端恒退浏览器本地。实得 {got['repr']}。"
        "⛔ 这是宿主形态问题，须登记并报主 session，不得改判据放行。"
    )


def test_get_overview_ships_the_display_tz_name(tmp_path, monkeypatch):
    """⑥ 的另一半：GET 聚合真的把那个名字放进了顶层响应（不是只有函数存在）。

    直接调 `_collect()` 而不起 TestClient —— 后者会拉起 lifespan、可能污染真实
    data 目录（memory「TestClient lifespan 污染真 data」）。
    """
    vaults_root = tmp_path / "vaults"
    (vaults_root / "库甲").mkdir(parents=True)
    monkeypatch.setattr(ro, "get_settings", lambda: SimpleNamespace(VAULTS_ROOT=str(vaults_root), ACTIVE_VAULT="库甲"))
    monkeypatch.setenv("CANVAS_TZ", "Asia/Tokyo")

    out = ro._collect()
    assert out["display_tz"] == "Asia/Tokyo", f"GET 没下发显示时区名；实得 {out.get('display_tz')!r}"
    # 与同一次响应里的 generated_at 自洽（不是随手塞了个常量进去）
    assert datetime.fromisoformat(out["generated_at"]).utcoffset() == timedelta(hours=9), (
        f"generated_at 的偏移与下发的 display_tz 对不上：{out['generated_at']}"
    )
