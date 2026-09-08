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


@pytest.mark.parametrize("tz_value", ["UTC0", "EST5", ":America/New_York"])
def test_posix_tz_string_resolves_to_process_local_not_etc_localtime(tz_env, tz_value):
    """`TZ` 是 ZoneInfo 不认、但 C 库认的写法时，算出的日期必须与进程本地一致。

    ⛔ 这三个都是**合法**的 `TZ` 值：POSIX 风格（`UTC0` / `EST5`）与前导冒号
    （`:America/New_York`）。`ZoneInfo` 全部拒绝它们。初版在这里 `pass` 掉、
    继续往下读 `/etc/localtime` —— 而 `/etc/localtime` 是**宿主**时区，压根不看
    `TZ`。于是「设了 TZ 却按宿主时区算」，静默错一天：
    上海宿主 + `TZ=UTC0`，`2026-07-31T16:30Z` 被算成 08-01，而 C 库本地是 07-31。

    判据取「与 C 库本地**同一天**」而不是「等于某个字面量」：这三种写法各自
    对应什么偏移由 tzdata 决定，钉字面量等于把 tzdata 抄进测试。
    """
    instant = datetime(2026, 7, 31, 16, 30, tzinfo=timezone.utc)
    tz_env(tz=tz_value)
    resolved = ro._display_tz()
    process_local = datetime.now().astimezone().tzinfo
    assert instant.astimezone(resolved).date() == instant.astimezone(process_local).date(), (
        f"TZ={tz_value!r} 下 display_tz() 给出的日期与进程本地不一致 —— "
        f"解析器忽略了 TZ 去读 /etc/localtime。"
        f"resolved={resolved!r} 日={instant.astimezone(resolved).date()}; "
        f"进程本地={process_local!r} 日={instant.astimezone(process_local).date()}"
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

    from app.api.v1.endpoints.review_overview import (  # noqa: PLC0415
        _gate_boards_rollup,
        _gate_buckets,
        _gate_due_groups,
        _gate_upcoming,
    )

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
        groups = _gate_due_groups(payload["due_nodes"])
        up = _gate_upcoming(payload["upcoming"])
        _ph, _zero, future_map = _gate_boards_rollup(
            payload["boards"], groups, len(payload["ineligible"]["placeholder"])
        )
        _gate_buckets(payload["buckets"], groups, payload["stats"], payload["generated_at"], future_map, up)

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
