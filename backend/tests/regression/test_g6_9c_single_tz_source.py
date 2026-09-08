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
    """两份 `_SystemLocalTZ` 类体也必须逐行相同（Codex r3 MEDIUM + 自验变异 A）。

    ⛔ 门 ① 只比 `display_tz` 那个**函数**。HIGH-1 的整个修复体是这个 35 行的类
    （`fromutc` / `utcoffset` / `dst` / `tzname` / `_dst_gap`）—— 它不在门 ① 的
    比较范围内。自验实测：把 `scripts/local_tz.py` 的类名改掉（等价于删掉它），
    整个测试文件仍 22 passed，而该副本在运行期会 `NameError`。
    """
    local_tz = _load_local_tz()
    # 先查**存在性**再比内容：类被删/改名时 inspect.getsource 抛的是 AttributeError，
    # 那条 traceback 不带可辨认的身份，变异负控绑不住「是这一条红的」。
    for label, mod in (("backend/app/core/display_tz.py", backend_tz), ("scripts/local_tz.py", local_tz)):
        assert hasattr(mod, "_SystemLocalTZ"), (
            f"{label} 里没有 _SystemLocalTZ —— 同源副本漂移了（类被删或改名）。"
            "该类是 POSIX TZ 分支的整个实现体，缺了它这份副本在运行期会 NameError。"
        )
    a = [ln.rstrip() for ln in textwrap.dedent(inspect.getsource(backend_tz._SystemLocalTZ)).splitlines()]
    b = [ln.rstrip() for ln in textwrap.dedent(inspect.getsource(local_tz._SystemLocalTZ)).splitlines()]
    assert a == b, (
        "两份 _SystemLocalTZ 类体不一致 —— 同源副本漂移了。\n"
        f"  首个差异: {next((f'{i}: {x!r} vs {y!r}' for i, (x, y) in enumerate(zip(a, b)) if x != y), '(长度不同)')}"
    )
    # 验伪锚：类体不能是空壳，且必须含本卡赖以成立的三个方法名
    for must in ("def fromutc", "def utcoffset", "def _dst_gap"):
        assert any(must in ln for ln in a), f"类体里没有 {must} —— 比的不是这个类"


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
    ":America/New_York",
    "EST5EDT,M3.2.0,M11.1.0",
    ":America/Santiago",
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
      · 旧投影（根本没有这个键）⇒ 必须**放行**（加性字段要向后兼容）。

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

    legacy = copy.deepcopy(payload)
    legacy.pop("display_tz")
    _gate(legacy)  # 旧投影没有该键：必须仍能放行（加性字段向后兼容）


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
