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

import ast
import importlib.util
import inspect
import itertools
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
        "_zoneinfo_key_candidates",
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


def _module_level_assignments(path: Path) -> dict[str, str]:
    """用 AST 取一份文件**顶层**赋值语句的 {名字: 源码文本}。

    只看 `tree.body`，函数体 / 类体里的赋值一概不进来（那些已被门 ② 逐行比过）。
    多行赋值（正则那种）按 `lineno..end_lineno` 整段取，不逐行拼。
    """
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines()
    out: dict[str, str] = {}
    for node in ast.parse(src).body:
        targets = (
            [node.target] if isinstance(node, ast.AnnAssign) else node.targets if isinstance(node, ast.Assign) else []
        )
        names = [tg.id for tg in targets if isinstance(tg, ast.Name)]
        if not names:
            continue
        text = "\n".join(ln.rstrip() for ln in lines[node.lineno - 1 : node.end_lineno])
        for n in names:
            out[n] = text
    return out


def test_two_copies_share_identical_module_level_constants():
    """两份副本的**模块级常量**也必须逐字相同（Codex r10 M9）。

    ⛔ 门 ①② 比的是 `inspect.getsource()` 能拿到的东西——函数与类。模块级常量
    `_POSIX_TZ_RE` / `_POSIX_DEFAULT_TRANSITION` **不在**它们的范围内，而解析器的
    整个词法面就在那条正则里。Codex r10 给的反例：只把 `scripts/local_tz.py` 的
    位宽 `1,3` 改成 `1,4`，两份副本的接受域立刻分叉（scripts 收 `AAA0001`、
    backend 拒），而当时**整套门全绿**——包括源同源门和 199 个原测试参数格。

    ⛔ 用 AST 枚举而不是手写名单：手写的两份清单必然漂移，新增常量不会自动进门。
    """
    local_tz = _load_local_tz()
    a = _module_level_assignments(Path(backend_tz.__file__))
    b = _module_level_assignments(REPO_SCRIPTS / "local_tz.py")
    assert a.keys() == b.keys(), (
        "两份副本的模块级常量**名单**不一致 —— 同源副本漂移了。\n"
        f"  只在 backend: {sorted(a.keys() - b.keys())}\n"
        f"  只在 scripts: {sorted(b.keys() - a.keys())}"
    )
    for name in sorted(a):
        assert a[name] == b[name], (
            f"两份副本的模块级常量 {name} 不一致 —— 同源副本漂移了。\n"
            f"  backend: {a[name][:200]!r}\n"
            f"  scripts: {b[name][:200]!r}"
        )
    # 验伪锚：解析器赖以成立的两个常量必须真的在枚举结果里，否则这道门在空集上恒真
    for must in ("_POSIX_TZ_RE", "_POSIX_DEFAULT_TRANSITION"):
        assert must in a, f"模块级常量枚举里没有 {must} —— 门跑在空集上（AST 提取失效）"
    # 验伪锚锚在**命名组**上而不是某个位宽字面量：位宽是会被调整的实现细节
    # （r10 就把 `\\d{1,3}` 放宽成了 `\\d+`），命名组才是这条正则的稳定身份。
    for _grp in ("(?P<std>", "(?P<std_off>", "(?P<dst>", "(?P<start>", "(?P<end>"):
        assert _grp in a["_POSIX_TZ_RE"], f"_POSIX_TZ_RE 的源码文本里没有 {_grp} —— 取到的不是那条正则，验伪锚不成立"
    # 当前两份副本的模块级赋值恰好就是上面两个（`re` / `time` 等是 import 不是赋值）。
    # 门不为常量数量设上限，只保证它不跑在空集上。
    assert len(a) >= 2, f"只枚举到 {len(a)} 个模块级常量，门失去被测对象"


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
    # ⚠️ 作用域订正（Codex r10 L5）: 这条区间限制**只对省略切换规则的串成立** ——
    #   它们要去查 posixrules 那张 tzfile。**带显式规则**的串不查表、直接按规则算,
    #   实测 `AAA0BBB,M3.2.0,M11.1.0` 在 2038 与 2050 的夏季照样给 +1h（DST 生效）,
    #   所以给那一族加样本时不必受 2007..2037 的限制。
    # ⚠️ 但 9999 年是**另一条**边界, 两族都过不去: 同一个显式规则串在 9999-07-01
    #   实测给 +0h（C 库那里 DST 没生效）。所以「显式规则在 9999 年也能实行 DST」
    #   这个说法本机**不成立** —— 加极值年样本前先实测那一年。
    # ⛔ 那条边界的**精确位置与性质**（Codex r11 M8 追问后二分出来的）: 显式规则串在
    #   **2569** 年仍正常实行 DST, **2570** 年起 C 库的取值翻转。判定它是 C 库自己的
    #   溢出而不是时区语义的依据是: 北半球串（`M3.2.0,M11.1.0`）与南半球串
    #   （`M10.1.0,M3.1.0`）在 2570 那一年**同时**翻转 —— 北 +1h→0、南 0→+1h,
    #   正是「季节判断整体颠倒」的特征, 而不是某一族规则失效。本实现按规格外推,
    #   在 2570 之后与 C 库分歧, **不跟**: 跟了等于把 C 库的 64 位溢出复制进来。
    #   （2038 那条分歧不属于这里 —— 实测同年显式规则串仍给 +1h, 它是**省略规则**族
    #   走 posixrules 那张 32 位表的边界, 已由上面 2007..2037 那条声明覆盖。）
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
        # 后红区变成 **142–166 小时/年、31/31 年都红**（实测逐年: 多数年 166 小时,
        # 连续区间 `[01-01T00:00Z, 01-07T22:00Z)`; **闰年后一年**只有 142 小时,
        # 如 2025/2029 是 `[01-01T00:00Z, 01-06T22:00Z)` —— 两处右端**不含端点**,
        # 逐秒实测 `01-06T21:59:59Z` 仍红、`22:00:00Z` 才绿）。
        # ⛔ 端点别写成「到 21:00Z 为止」（初版如此、Codex r8 LOW-1 更正）: 那是最后一个
        #    红的**整点采样**, 不是连续红区的右端 —— 两者差整整一小时。
        # 后人把探针时刻挪几小时时, 前者会静默变哑弹, 后者不会。
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
      ② `Jn` / 裸 `n` 叠 `/N`（POSIX 与本实现都到 `167:59:60` = 整 7 天）；
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

#: 另外两支（无 DST / 带显式规则）的同型输入 —— Codex r8 既有① 的复现串。
_NON_UTF8_TZ_BYTES_ALL_BRANCH = {
    "no-dst": b"<\xff>0",
    "explicit-rules": b"AAA0<\xff>,M3.2.0,M11.1.0",
}


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
    ⛔ 修法**不是** `encode("utf-8", "surrogateescape")`（本卡 r5 试过、被 r6 打回）：
    那样函数确实不抛了，但代理字符留在 `.key` 里，一路进 API 响应、在 `JSONResponse`
    的编码边界**再炸一次** —— 修复只是把失败从启动挪到了响应出口。
    现行修法是**严格** `encode("utf-8")` + `except UnicodeEncodeError: return None`：
    不可严格编码的规格串整个不接受 ⇒ 退 UTC ⇒ `.key` 恒可序列化，与 BASE 逐点同行为。

    ⚠️ 本门钉两件事：`display_tz()` **不抛**，以及返回值的 `.key` 能过**响应序列化**
    （判据打在 `.encode("utf-8")` 那一步 —— `json.dumps` 默认 `ensure_ascii=True` 会把
    代理字符转义成 `\\udcff` 而不抛，用它做判据是假绿）。
    这些串本机 C 库是接受的，换算结果是否与 C 库一致**不在**本门范围。
    ⚠️ 作用域声明**已更新**（Codex r10 L2）：r7 时这段写的是「只适用于省略规则分支，
    无 DST 与显式规则两支是既有缺口、本卡未修」。r9 起用户裁定「既有也要修」，那两支
    的整串属性校验（控制字符 / 可严格 UTF-8 / 名字和式）已经提到**两分支共用位置**，
    三支现在同口径。留着旧措辞会让后人以为还有两个敞着的口子。
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


#: TZ 的**路径**形态（Codex r10 M4/M5）。C 库把 `TZ` 先当文件路径解析，解析不了才
#: 退 POSIX 规格串；本实现原来只试 `env_tz` 与 `env_tz.lstrip(":")` 两个候选。
#: (TZ 值, 期望与 C 库一致的偏移来源说明)
_TZ_PATH_FORMS = [
    (":Asia/Shanghai", "单冒号 + IANA 名"),
    ("::Asia/Shanghai", "**双**冒号：C 库只剥一个，剩下 `:Asia/Shanghai` 当路径打不开 ⇒ UTC"),
    (":::Asia/Shanghai", "三冒号：同上"),
    ("Asia/Shanghai", "裸 IANA 名"),
    ("/usr/share/zoneinfo/Asia/Shanghai", "绝对路径：C 库直接打开该 tzfile"),
    (":/usr/share/zoneinfo/Asia/Shanghai", "冒号 + 绝对路径"),
    ("./Asia/Shanghai", "相对 TZDIR 的路径"),
    ("Asia//Shanghai", "双斜杠"),
    ("Not/AZone", "不存在的名 ⇒ 两边都退 UTC"),
    ("EST5EDT,M3.2.0,M11.1.0", "POSIX 规格串（不是路径）"),
    ("", "空 TZ ⇒ UTC"),
    ("/tmp/whatever", "任意路径：这里两边都退 UTC —— 但**理由不同**，见门内说明"),
    # ⛔ 以下五串是 r12 补的 —— 负控报「路径必须存在」「冒号禁 POSIX 回退」两段假绿才发现
    #    表里缺了它们。变异那两处时行为**确实翻转**（`/does-not-exist/...` 从 UTC 变成
    #    +08:00、`:AAA-1` 从 UTC 变成 +01:00），但没有用例踩得到 ⇒ 门全绿。
    ("/does-not-exist/zoneinfo/Asia/Shanghai", "路径里有 `zoneinfo` 段但**文件不存在** ⇒ C 库给 UTC"),
    ("zoneinfo/Asia/Shanghai", "相对路径且 `/usr/share/zoneinfo/zoneinfo/...` 不存在 ⇒ UTC"),
    (":AAA-1", "**前导冒号**：语义是「这是个路径」，路径找不到就结束，C 库**不再**试规格串"),
    ("::AAA-1BBB,M3.2.0,M11.1.0", "同上，双冒号 + 看起来合法的规格串 ⇒ 仍是 UTC"),
    ("Asia/../Asia/Shanghai", "`..` 路径：C 库接受（`resolve()` 后就是上海）"),
]


@pytest.mark.parametrize("copy_id", _COPY_IDS)
@pytest.mark.parametrize("tz_value,why", _TZ_PATH_FORMS, ids=[w[:24] for _v, w in _TZ_PATH_FORMS])
def test_tz_path_forms_match_libc(tz_env, copy_id, tz_value, why):
    """`TZ` 的各种路径形态，本实现解析出的偏移必须与 C 库相同（r10 M4/M5）。

    ⛔ **误收比误拒危险**：原实现用 `lstrip(":")` 剥掉**全部**前导冒号，于是
    `::Asia/Shanghai` 被剥成合法名给出 +08:00，而 C 库只剥一个冒号、剩下的当路径
    打不开 ⇒ UTC。整整差 8 小时，且方向是「本实现自作主张地认出了一个时区」。

    ⚠️ 如实声明一处**有意的收紧**：绝对路径只认路径里含 `zoneinfo` 段的那种。
    C 库会打开任意路径的 tzfile（`TZ=/tmp/<某个真 tzfile>`），本实现不跟——
    `TZ` 是环境变量，按它去开任意文件是不必要的输入面。上表最后一条两边都给 UTC，
    但本实现是因为这条收紧、C 库是因为 `/tmp/whatever` 不存在；**不要**把这条
    当成「该收紧无副作用」的证据。
    """
    tz_env(tz=tz_value)
    module = backend_tz if copy_id == "backend" else _load_local_tz()
    instant = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)
    libc_off = instant.astimezone().utcoffset()
    mine_off = instant.astimezone(module.display_tz()).utcoffset()
    assert mine_off == libc_off, (
        f"[{copy_id}] TZ={tz_value!r} 下偏移与 C 库不符: 本实现 {mine_off}，C 库 {libc_off}\n  形态: {why}"
    )


@pytest.mark.parametrize("copy_id", _COPY_IDS)
def test_fromutc_rejects_foreign_tzinfo(copy_id):
    """`fromutc()` 必须拒绝「tzinfo 不是自己」的 datetime（tzinfo 协议，r10 L7）。

    ⛔ 缺了这道校验不会报错，会**静默给出一个看似合理的结果**：传进来的 naive
    datetime 被当成「本时区的 UTC 读数」换算，调用方拿到的时刻偏一整个偏移量。
    本机 stdlib 的 `timezone.fromutc()` 与 `ZoneInfo.fromutc()` 都按协议抛 ValueError。
    """
    module = backend_tz if copy_id == "backend" else _load_local_tz()
    tz = module.parse_posix_tz("EST5EDT,M3.2.0,M11.1.0")
    assert tz is not None
    for label, bad in (
        ("naive", datetime(2026, 7, 1, 12, 0)),
        ("异 tzinfo", datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)),
    ):
        with pytest.raises(ValueError):
            tz.fromutc(bad)
        # 对照：stdlib 自己也这么做 —— 证明这不是本实现自创的严格
        with pytest.raises(ValueError):
            timezone(timedelta(hours=3)).fromutc(bad)
    # 非 datetime 参数按 tzinfo 协议抛 TypeError（Codex r11 L5：原先撞 `dt.replace`
    # 抛的是 AttributeError，与 stdlib 不一致）
    for bad in (None, 1, "2026-07-01"):
        with pytest.raises(TypeError):
            tz.fromutc(bad)
        with pytest.raises(TypeError):
            timezone(timedelta(hours=3)).fromutc(bad)  # 对照：stdlib 也抛 TypeError
    # 正例：tzinfo 就是自己时必须正常工作（否则「一律抛」也能跑绿）
    ok = datetime(2026, 7, 1, 12, 0, tzinfo=tz)
    assert tz.fromutc(ok).tzinfo is tz


#: ══════════════════════════════════════════════════════════════════════════
#: 接受域**组合**对拍（Codex r10 M1/M2/M3 的根治）
#: ══════════════════════════════════════════════════════════════════════════
#: ⛔ 手写样本会塌到子族 —— 本卡为此栽过四次（507 单名上限把 std 名钉死在 `AAA`；
#:    量纲变异只改一行；NUL 只测引用名外；`AAA-1\n` 的 libc 列写反）。这里改成
#:    **显式列出每一维再取笛卡尔积**，让组合自己去覆盖边界，而不是靠我想得起来。
#: ⛔ 判据是**双向**的，而且两个方向的分量完全不同：
#:      · 误收（本实现收 / C 库拒）⇒ 硬性 **0**，一条都不许有；
#:      · 误拒（C 库收 / 本实现拒）⇒ 必须逐条落在下面 `_declared_narrowing()`
#:        列举的**已声明收紧**里，出现任何一条声明外的误拒就红。
#:    只钉误收会让「一律拒」跑绿；只钉误拒会让「一律收」跑绿。
#: ⛔ 名字这一维在 r12 又补过一次（负控报了三段假绿才发现）: 原表里全是**闭合**引用名
#:    或纯 ASCII 裸名, 于是三类行为在门下不可见 ——
#:    ① `<` 开头**未闭合**（C 库当裸名收, `<AAA1` / `<<AAA1` / `<1`）;
#:    ② 名字里的**非 ASCII 数字**（`ABC٦1` / `ABC１1`, C 库当普通名字字符收）;
#:    ③ `_strip_name` 对未闭合名的剥法（少算两字节 ⇒ 长度边界漂）。
#:    变异这三处时行为**确实翻转了**, 但门里没有能显形的样本 ⇒ 全绿。
#:    教训与本卡前面几次同形: **样本缺席比判据写错更难发现**, 因为两者都表现为「绿」。
_GRID_STD_NAME = [
    "ABC",
    "<ABC>",
    "A",
    "AB",
    "<>",
    "<A B>",
    "<+05>",
    "<-03>",
    "<中>",
    "A" * 300,
    "<AAA",  # ⭐ `<` 开头未闭合 ⇒ C 库当裸名（tzname `_AAA`）
    "<<AAA",  # ⭐ 同上，两个 `<`
    "<",  # ⭐ 名字就是一个 `<`
    "ABC٦",  # ⭐ 阿拉伯数字：C 库当普通名字字符
    "ABC１",  # ⭐ 全角数字：同上
    "<" + "A" * 511,  # ⭐ 未闭合 + 长度边界（512 字节 +NUL = 513 > 512 ⇒ C 库拒）
    "<" + "A" * 510,  # ⭐ 同上但恰好 512 ⇒ C 库收
    # ⛔ r13 再补一批 —— Codex r12 的 4 条 HIGH **全部**落在当时维度表之外：
    #    组合门对它们完全看不见，是外部审查把它们找出来的。
    "<AAA1>",  # ⭐ 闭合引用名里**含数字** ⇒ 后面若还跟 `<…` 必须整串拒（r12 H1）
    "",  # ⭐ **空裸名**：`TZ=1` C 库收（std 名空、off −01:00）（r12 M1）
    "A:",  # ⭐ 名字**含** `:`（C 库收，名字就是 `A:`）
    "AAA" + "0" * 4300,  # ⭐ 超长数字前缀：int() 转换上限那一族（r12 H4）
]
_GRID_STD_OFF = [
    "",
    "1",
    "01",
    "0001",
    "-5",
    "+5",
    "1:30",
    "1:30:45",
    "0",
    "23",
    "24",
    "1:60",
    ":",  # ⭐ 偏移后一个孤立 `:` ⇒ C 库拒（`:` 属于偏移，后面必须跟数字）（r12 H2）
    "1:",  # ⭐ 同上
    "1:30:",  # ⭐ 秒位缺席
    "0" * 4300 + "1",  # ⭐ 4301 位数字：C 库收（给 −01:00），Python int() 会抛（r12 H4）
]
#: ⛔ `None` = 没有 dst 部分；`""` = **dst 名为空但 dst 偏移在场**（`AAA1+2` 这一族，
#:    C 库收）。两者语义不同，判定见生产代码的 `_has_dst()`（r12 M1）。
_GRID_DST_NAME = [None, "", "DEF", "<DEF>", "<>", "D" * 300, "١", "<BBB"]
_GRID_DST_OFF = ["", "2", "-3", "0", "2:30"]
#: ⛔ **规则这一维塌过一次**（Codex r11 M7）：上一版表里全是 `M3.x` 起、`M11.1.0` 止、
#:    星期恒为 `0` 的北半球规则，四个探针上的 DST 状态向量**完全相同**（标准/夏令/夏令/夏令）。
#:    后果是致命的：注释声称探针 `3-20` 能区分「用 TZ 自带规则」与「退默认规则」，
#:    而表里根本没有一条**能被区分**的样本 —— Codex 实测把 1134 个被接受串改用默认规则，
#:    54040 个换算点**全部通过**。探针对了、样本没了，门照样是假的。
#:    现在每一项后面标注它撑开的是哪一维。
_GRID_RULES = [
    None,
    "M3.2.0,M11.1.0",  # 与 posixrules 默认**相同**的规则（对照组）
    "M4.1.0,M10.1.0",  # ⭐ 与默认**不同** —— 唯一能区分「自带 vs 默认」的一族
    "M4.1.0,M10.1.0/3",  # 同上 + 非默认结束切换时刻
    "M10.1.0,M3.1.0",  # ⭐ 南半球方向（start > end）
    "M3.2.3,M11.1.5",  # ⭐ 星期非 0（周三起 / 周五止）、第 5 周 = 末周
    "M1.1.1,M12.5.6",  # ⭐ 月份两端 + 末周 + 星期 6
    "M03.02.00,M11.1.0",  # 前导零
    "J60,J300",
    "J0060,J300",  # 前导零
    "J1,J365",  # ⭐ J 形式两端极值
    "60,300",
    "0060,300",  # 前导零
    "0,365",  # ⭐ 裸数字形式的两端（0 合法、J0 非法）
    "M3.2.0/2,M11.1.0/2",
    "M3.2.0/167,M11.1.0",  # 切换时刻上边界
    "M3.2.0/168,M11.1.0",  # 越界
    "M3.2.0/2:60,M11.1.0",  # 分钟越界
    "M3.2.0/0002,M11.1.0",  # 前导零
    "J0,J300",  # 非法 J0
    "M13.2.0,M11.1.0",  # 非法月
    "M3.6.0,M11.1.0",  # ⭐ 非法周（1..5）
    "M3.2.7,M11.1.0",  # ⭐ 非法星期（0..6）
]


#: 换算对拍的探针时刻。⛔ `3-20` 与 `10-20` 不是凑数：它们落在「TZ 自带规则」与
#: 「posixrules 默认规则」**分歧**的那两段（自带 `M4.1.0..M10.1.0` vs 默认
#: `M3.2.0..M11.1.0`），是唯一能区分「用谁的规则」的两格。只取冬夏两个时刻的话，
#: 「整体退 posixrules」这种错读法会跑绿 —— r10 H1 的修复正是靠 3-20 那格定的向。
_GRID_PROBES = [
    datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),  # 冬（两套规则都不在 DST）
    datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),  # 默认规则已 DST、自带规则未到
    datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc),  # 夏（两套都在 DST）
    datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc),  # 自带规则已结束、默认规则未结束
    # ⛔ **年份也是一维**（Codex r11 列的塌缩清单第一条）：上一版四个探针全在 2026，
    #    非闰年、且落在 C 库 32 位表的覆盖区内。下面三个各撑开一侧。
    datetime(2024, 2, 29, 12, 0, tzinfo=timezone.utc),  # 闰日（J 形式跳闰日的分支）
    datetime(2024, 12, 31, 12, 0, tzinfo=timezone.utc),  # 闰年末（J365 的另一侧）
    datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc),  # 两套规则都在 DST 的另一格
]


#: ⛔ **oracle 分不开的那一族**（Codex r12 M6）：`UTC0` / `<UTC>0` / `UTC` 这类
#:    **本身就等价于 UTC** 的规格串，被接受时的 `time` 四元组与「解析失败退 UTC」
#:    完全相同，任何基于 `time` 模块的探测都分不开。
#:    上一轮我在 `_libc_accepts` 的 docstring 里写了这个例外，却**没有接进判据** ——
#:    真把 `UTC0` 放进组合，阶段一会立刻判「误收」，根本走不到注释声称能兜住它的阶段二。
#:    现在显式跳过阶段一、只让它们走阶段二（行为比对），并由下面的验伪锚保证这张
#:    豁免表不被滥用：表里每一条都必须**真的**是 oracle 分不开的。
#: ⚠️ 表里**不含** `"UTC"`：它没有 std 偏移，被 ⑥ 拒掉，双方都判「拒」⇒ 无分歧可豁免。
#:    我第一版把它写进来了，验伪锚五当场报出来 —— 这正是那道锚存在的意义：
#:    豁免表最容易出的错不是漏，而是**多**（顺手把一条不需要豁免的塞进去，
#:    将来那条真出分歧就被静默放过）。
_ORACLE_BLIND = frozenset({"UTC0", "<UTC>0", "UTC+0", "UTC-0"})


def _grid_specs():
    """笛卡尔积（去掉「没有 dst 部分却有 dst 偏移」这种构造不出来的组合），去重。

    ⚠️ `dn is None` 才是「没有 dst 部分」；`dn == ""` 是**dst 名为空但 dst 偏移在场**
    （`AAA1+2` 这一族，C 库收），两者必须分开（Codex r12 M1）。
    """
    seen = set()
    for sn, so, dn, do, ru in itertools.product(
        _GRID_STD_NAME, _GRID_STD_OFF, _GRID_DST_NAME, _GRID_DST_OFF, _GRID_RULES
    ):
        if dn is None and do:
            continue
        spec = sn + so + (dn + do if dn is not None else "") + ("," + ru if ru else "")
        if spec not in seen:
            seen.add(spec)
            yield spec


def _libc_accepts(spec: str) -> bool:
    """问一次 C 库：它收不收这个规格串。判据是**四元组**全部等于 UTC 的退化态。

    ⛔ 不能只看 `tm_gmtoff == 0`：`std_off=0` 的串被**接受**时 gmtoff 也是 0。
    ⛔ 也不能只看 `time.tzname == ('UTC','UTC')`（本卡 r10 用的就是这个，Codex r11 M6
       抓到）：`TZ=UTC-1` 是**合法**的 +01:00 时区，而它的 tzname 同样是 `('UTC','UTC')`
       ⇒ 那个判据把一个被接受的串读成「拒」。`UTC+5` 同理。
    ⚠️ 如实声明一处**观测上不可区分**的情形：`UTC0` / `<UTC>0` / `UTC` 这类**本身就等价
       于 UTC** 的规格串，四元组与「解析失败退 UTC」完全相同，任何基于 `time` 模块的
       探测都分不开。这不影响判据的正确性——那种情形下两种解释**行为相同**，
       而行为正是第二阶段直接比对的东西。
    """
    saved = os.environb.get(b"TZ")
    try:
        os.environb[b"TZ"] = spec.encode("utf-8")
        try:
            time.tzset()
        except RuntimeError:
            # ⛔ `time.tzset()` 会**抛**（扩维度后才撞上）：CPython 的 time 模块对 libc
            #    交回的 `tm_gmtoff` 有范围检查，超出即 `RuntimeError: invalid GMT offset`。
            #    实测 `ABC-25` 正常（−25 h），`ABC-51` / `ABC-52` / `ABC52` 抛。
            #    语义上这类串「本机无法表示成一个时区」⇒ 与退 UTC 同归为「拒」。
            #    ⚠️ 不加这层 try，整道门在第一个这种组合上直接崩溃 —— 而「门崩了」与
            #    「门发现分歧」是两回事，读日志的人会误以为是被测实现出了问题。
            return False
        degenerate = time.tzname == ("UTC", "UTC") and time.timezone == 0 and time.altzone == 0 and time.daylight == 0
        return not degenerate
    finally:
        if saved is None:
            os.environb.pop(b"TZ", None)
        else:
            os.environb[b"TZ"] = saved
        try:
            time.tzset()
        except RuntimeError:  # 还原时也可能抛（外层 TZ 本身就是坏串）
            os.environb.pop(b"TZ", None)
            time.tzset()


def _libc_utcoffset(spec: str, naive_dt: datetime):
    """问一次 C 库：`TZ=spec` 下、把 `naive_dt` 当**当地墙钟**时的 UTC 偏移。

    与 `_libc_accepts` 同族，但问的是「偏移是多少」而不是「收不收」。
    用它替代写死的偏移常量 —— 常量会在规则改动时静默失效，而且同一族里
    不同规则的串偏移本来就不同（本卡在 H4 扩展入口上栽过：`AAA1,J…,J365`
    几乎全年 DST，冬季该给 dst 偏移而不是 std 的 −01:00）。

    ⛔ **口径必须是「当地墙钟」，不是「UTC 瞬时」**（本卡第一版写反了，自审抓出）：
       调用方比的是 `tz.utcoffset(dt)`，而 `tzinfo.utcoffset(dt)` 按协议接收的是
       **当地墙钟**的 naive datetime。第一版写成
       `naive_dt.replace(tzinfo=timezone.utc).astimezone().utcoffset()`
       —— 那是把 `naive_dt` 当成 UTC 瞬时再换算，两侧差一个「该时刻的偏移」的位移。
       当前门里那两条串恰好不跨切换点所以对得上；**跨切换点就会把正确实现判红**。
       实测反例：`AAA5,J15/9,J300` 在 2026-01-15 12:00 上，
       实现与墙钟口径都给 −20:00，写反的 oracle 给 −19:00。
       ⚠️ 引入这个 helper 的理由是「写死常量会在规则改动时失效」，
          而写反口径只是把「立刻会响的错」换成了「要等探针跨切换点才响的错」——
          后者更糟，因为它红的是**正确的实现**。
    ⛔ 两处 `time.tzset()` 都要兜 `RuntimeError`（照抄 `_libc_accepts` :1055/:1072-1075）：
       CPython 对 libc 交回的 `tm_gmtoff` 有范围检查，`ABC-51` / `ABC52` 这类串会抛。
       不兜的话「门崩了」会被读成「门发现分歧」；还原路径抛出去还会把进程 libc
       时区状态留脏（`_libc_accepts` 的 docstring 已经把这条教训写过一遍）。
    """
    saved = os.environb.get(b"TZ")
    try:
        os.environb[b"TZ"] = spec.encode("utf-8")
        try:
            time.tzset()
        except RuntimeError:
            # 本机无法把这条串表示成时区（同 `_libc_accepts` 的「拒」）⇒ 没有偏移可言
            return None
        # 当地墙钟 → 用 mktime 反推该时刻生效的 tm_gmtoff（与 tzinfo.utcoffset 同口径）
        return timedelta(seconds=time.localtime(time.mktime(naive_dt.timetuple())).tm_gmtoff)
    finally:
        if saved is None:
            os.environb.pop(b"TZ", None)
        else:
            os.environb[b"TZ"] = saved
        try:
            time.tzset()
        except RuntimeError:  # 还原时也可能抛（外层 TZ 本身就是坏串）
            os.environb.pop(b"TZ", None)
            time.tzset()


def _declared_narrowing(spec: str) -> str | None:
    """这条误拒是否属于**已声明**的收紧；是则返回理由，否则 None（⇒ 门红）。

    三条收紧都写在生产代码的注释里，这里只是把它们变成可执行的判据，
    让「声明」和「实际拒的是什么」不能悄悄脱节。

    ⚠️ CARD-G6-9c-R3：`std_off` 在正则里改成**必填**之后，下面那句
    `if not g["std_off"]: return None` 已**不可达**（3723 条匹配成功的样本里
    std_off 为空的有 0 条）。留着它不是忘了 —— 它现在的职责换成了**类型收窄**：
    `groupdict()` 的值是 `str | None`，紧接着那行 `_posix_offset_seconds(g["std_off"])`
    需要 `str`。生产代码那边的同名检查（⑥）已经删掉，因为那边没有这个需求；
    两边处置不同是因为**理由不同**，不是标准不一致。
    """
    m = backend_tz._POSIX_TZ_RE.match(spec)
    if m is None:
        return "词法：正则不认（控制字符等）" if any(ord(c) < 0x20 for c in spec) else None
    g = m.groupdict()
    if not g["std_off"]:  # 见 docstring：当前正则下不可达，留作类型收窄
        return None
    std_off = backend_tz._posix_offset_seconds(g["std_off"])
    if abs(std_off) >= 86400:
        return "⑧ |std_off| ≥ 24h：Python tzinfo 不可表示（注释已声明，非 C 库口径）"
    # ⛔ 必须与生产代码同口径用 `_has_dst()`：名字量词改成可空之后，`g["dst"] is not None`
    #    对「没有 dst」的串也成立（空名匹配成 `""`），这里若还用旧判据，判定就和被测
    #    代码分叉了 —— 表现为「明明是已声明收紧，门却报声明外分歧」（r13 那 323 条里
    #    的一部分就是这么来的，`ABC1:30:2:30` 的 dst 偏移其实是 −30 h）。
    if backend_tz._has_dst(g) or g["start"] is not None:
        dst_off = backend_tz._posix_offset_seconds(g["dst_off"]) if g["dst_off"] else std_off + 3600
        if abs(dst_off) >= 86400:
            return "⑧ |dst_off| ≥ 24h：同上"
        if abs(dst_off - std_off) >= 86400:
            return "两侧之差 ≥ 24h：dst() / timetuple() 会抛（过度拒绝，注释已声明）"
    return None


def test_accepted_domain_grid_matches_libc(tz_env):
    """组合对拍，**两个阶段**：① 接受域（误收 0、误拒只许落在已声明的收紧里）；
    ② 对两边都接受的串逐时刻比**换算结果**。

    只对 backend 那一份跑 —— 两份副本逐字节同源已由门 ①②③ 分别锁住
    （函数体 / 类体 / 模块级常量），在这里再跑一遍 scripts 副本只是把耗时翻倍。
    """
    total = over_accept = 0
    undeclared: list[str] = []
    narrowed: dict[str, int] = {}
    blind_seen = 0
    for spec in _grid_specs():
        total += 1
        if spec in _ORACLE_BLIND:
            # oracle 分不开这一族（见 `_ORACLE_BLIND`），阶段一跳过、阶段二照比行为
            blind_seen += 1
            continue
        libc_ok = _libc_accepts(spec)
        impl_ok = backend_tz.parse_posix_tz(spec) is not None
        if libc_ok == impl_ok:
            continue
        if impl_ok:
            over_accept += 1
            undeclared.append(f"[误收] {spec[:70]!r}")
        else:
            why = _declared_narrowing(spec)
            if why is None:
                undeclared.append(f"[误拒·未声明] {spec[:70]!r}")
            else:
                narrowed[why] = narrowed.get(why, 0) + 1
    assert not undeclared, (
        f"接受域对拍失败（{total} 个组合，误收 {over_accept} 条，"
        f"声明外的分歧 {len(undeclared)} 条）：\n"
        + "\n".join("  " + x for x in undeclared[:25])
        + (f"\n  … 另有 {len(undeclared) - 25} 条" if len(undeclared) > 25 else "")
        + "\n  误收方向尤其危险：它让本实现接受 C 库拒绝的串，从而与机器本地时区归日不同。"
    )
    # 验伪锚一：门必须真的跑在**上万**个组合上，而不是被某个维度塌成空集
    assert total > 20000, f"只枚举到 {total} 个组合 —— 维度表被削过，门失去覆盖面"
    # ⛔ 验伪锚五（Codex r12 M6）：`_ORACLE_BLIND` 是一张**豁免**表，必须防它被滥用 ——
    #    表里每一条都得**真的**是 oracle 分不开的（被接受时的四元组 == 退 UTC 时的四元组），
    #    否则就是拿豁免掩盖一条真分歧。判据：该串必须被本实现接受、且 oracle 判它「拒」。
    for _b in _ORACLE_BLIND:
        _impl = backend_tz.parse_posix_tz(_b) is not None
        assert _impl and not _libc_accepts(_b), (
            f"{_b!r} 不属于「oracle 分不开」那一族（本实现{'收' if _impl else '拒'}、"
            f"oracle 判{'收' if _libc_accepts(_b) else '拒'}），不该在豁免表里。"
            "豁免只对「被接受时与退 UTC 行为完全相同」的串成立。"
        )
    # 验伪锚二：三条已声明收紧必须**都有实例命中**，否则说明对应维度没取到边界值
    assert len(narrowed) >= 2, (
        f"只有 {len(narrowed)} 类已声明收紧被命中：{sorted(narrowed)}。"
        "维度表里的 24h 越界样本（`24` / `23`+`-3`）必须留着，否则这条门对那两条收紧是盲的。"
    )

    # ── 第二阶段：**换算结果** ──────────────────────────────────────
    # ⛔ 只比「收不收」对「收了但算错」这一整类缺陷是全盲的 —— r11 负控实测：
    #    把「无 dst 名但带规则」那一支改回早退后，串**仍被接受**（接受域门全绿），
    #    只是夏季偏移少了整整一小时。收/拒相同 ≠ 行为相同。
    points = mismatches = 0
    bad_points: list[str] = []
    for spec in _grid_specs():
        tz = backend_tz.parse_posix_tz(spec)
        if tz is None:
            continue
        saved = os.environb.get(b"TZ")
        try:
            os.environb[b"TZ"] = spec.encode("utf-8")
            try:
                time.tzset()
            except RuntimeError:
                # 同 `_libc_accepts`：本机表示不了这个时区，没有可比的 libc 侧取值。
                # ⚠️ 这不是「跳过一条分歧」—— 阶段一已经把它按「libc 拒」判过了；
                #    本实现若接受它，那条误收在阶段一就红了，轮不到这里。
                continue
            for probe in _GRID_PROBES:
                points += 1
                libc_off = probe.astimezone().utcoffset()
                mine_off = probe.astimezone(tz).utcoffset()
                if libc_off != mine_off:
                    mismatches += 1
                    if len(bad_points) < 20:
                        bad_points.append(f"{spec[:56]!r} @ {probe:%m-%d}: C 库 {libc_off} / 本实现 {mine_off}")
        finally:
            if saved is None:
                os.environb.pop(b"TZ", None)
            else:
                os.environb[b"TZ"] = saved
            try:
                time.tzset()
            except RuntimeError:
                os.environb.pop(b"TZ", None)
                time.tzset()
    assert not bad_points, (
        f"换算对拍失败（{points} 个「串 × 时刻」点，不符 {mismatches} 个）：\n"
        + "\n".join("  " + x for x in bad_points)
        + "\n  这些串两边**都接受**，只是算出来的偏移不同 —— 接受域门对这一类是盲的。"
    )
    # 验伪锚三：第二阶段必须真的比到了上万个点（被接受的串不能塌成一小撮）
    assert points > 40000, f"换算对拍只跑了 {points} 个点 —— 被接受的串太少，门失去覆盖面"
    # ⛔ 验伪锚四（Codex r11 M7）：规则维度必须真的撑开了「四个探针上的 DST 状态向量」——
    #    上一版表里全部规则给出**同一个**向量，于是「把自带规则换成默认规则」的错误实现
    #    照样全绿。这里直接断言向量的种类数，塌回去就红。
    vectors = set()
    for rule in _GRID_RULES:
        if rule is None:
            continue
        spec = "AAA-1BBB," + rule
        tz = backend_tz.parse_posix_tz(spec)
        if tz is None:
            continue
        base = backend_tz.parse_posix_tz("AAA-1BBB")  # 无规则 ⇒ 走默认规则
        assert base is not None
        vectors.add(tuple(p.astimezone(tz).utcoffset() != p.astimezone(base).utcoffset() for p in _GRID_PROBES))
    assert len(vectors) >= 3, (
        f"规则维度只撑开 {len(vectors)} 种「与默认规则是否同步」的向量：{sorted(vectors)}。"
        "全都与默认规则同步的话，「退默认规则」这种错误实现在本门下是不可见的"
        "（Codex r11 M7 实测：1134 个串改用默认规则，54040 点全部通过）。"
    )


#: 解析器的**接受域**必须逐条对齐 C 库（Codex r9 M1–M5）。每条都在本机三方实测过
#: （BASE / HEAD / libc），判据是「本实现接受 ⟺ C 库接受」。
#: ⛔ C 库「拒」的自证锚是 `time.tzname` 变成 `('UTC','UTC')`，**不能**用 `tm_gmtoff == 0`
#:    —— `std_off=0` 的串被接受时 off 也是 0，那个判据会把接受读成拒。
#: (spec, 本实现应否接受, 依据)
_ACCEPTANCE_DOMAIN_CASES = [
    # ——— C 库收 / 本实现也收 ———
    ("<A\nAA>-1", True, True, "引用名**内部**换行：C 库接受"),
    ("AAA0<B\nBB>,M3.2.0,M11.1.0", True, True, "同上，带显式规则的形态"),
    ("<A AA>-1", True, True, "引用名内部空格：C 库接受"),
    ("A" * 254 + "-1", True, True, "256 字节整串、名字 254 字节：远未到名字缓冲区上限"),
    ("AAA0<" + "中" * 169 + ">", True, True, "3 + 507 + 2 = **512**：和式上边界（多字节名字侧）"),
    (
        "<" + "A" * 507 + ">-1<BBB>,M3.2.0,M11.1.0",
        True,
        True,
        "507 + 3 + 2 = **512**：std 名占满时 dst 名仍可有 3 字节 —— 旧的「每名 ≤507」口径在这条上误拒",
    ),
    ("<" + "A" * 511 + ">-1", True, True, "无 dst 形态 511 + 1 = **512**：该侧上边界"),
    ("AAA0BBB,M3.2.0/167,M11.1.0", True, True, "切换时刻 167 小时：C 库接受的上边界"),
    ("AAA0BBB,M3.2.0/2:00:60,M11.1.0", True, True, "切换时刻秒 60：C 库接受（61 才拒）"),
    # ——— C 库拒 / 本实现也拒 ———
    (
        "AAA-1\n",
        True,
        True,
        "C 库把尾部换行**吃进 dst 名**并实行 DST（tzname 给 `('AAA','_')`），本实现现已跟随。"
        "⛔ 这条曾是登记的「⚠️分歧」，理由是「不让控制字符进 `.key`」——但 r11 发现引用名侧"
        "一直放行同样的控制字符（`<A\\nAA>-1` 收），同一个理由解释不了两侧不同的口径"
        "（Codex r11 L4）。现统一为都放行；`.key` 的安全由严格 UTF-8 可编码那条与响应"
        "序列化门负责，那才是真会炸的一层。",
    ),
    ("<AAA><BBB>,M3.2.0,M11.1.0", False, False, "缺 std 偏移：C 库对**所有**形态整串拒收（r9 M3）"),
    ("<AAA>", False, False, "同上，无 dst 形态也拒"),
    ("AAA-1,J0,J0", False, False, "非法规则 J0：C 库拒，**无 dst 形态也要验规则**（r9 M4）"),
    ("AAA0BBB,M3.2.0/2:60,M11.1.0", False, False, "切换时刻分钟 60：C 库拒（r9 M5）"),
    ("AAA0BBB,M3.2.0/2:00:61,M11.1.0", False, False, "切换时刻秒 61：C 库拒（60 接受、61 拒，两侧都在表里）"),
    ("AAA0BBB,M3.2.0/168,M11.1.0", False, False, "切换时刻 168 小时：越过 C 库的 167 上界（r9 M5）"),
    ("AAA0BBB,M３.2.0,M11.1.0", False, False, "规则含**全角**数字：Python 的 `\\d` 匹配它而 C 库拒（r9 M5）"),
    ("AAA0BBB,M3.2.0/２,M11.1.0", False, False, "切换时刻含全角数字：同上"),
    # ⛔ 上面两条**都被两条检查同时拦着**（数字字段的 ASCII 检查 + 规则文本的 ASCII 检查），
    #    于是拆掉任一条，它们照样红不了 —— r12 负控报这两段假绿正是因为探针选在了
    #    「两道防线都覆盖」的串上。下面两条各自只有**一条**检查能拦，才是区分点。
    (
        "AAA0BBB,M3.2.0/2:３0,M11.1.0",
        False,
        False,
        "全角数字落在**切换时刻的分钟字段** —— 只有数字字段的 ASCII 检查能拦"
        "（规则文本检查看的是 `start`/`end`，不含 `/` 之后的时刻）",
    ),
    (
        "AAA0BBB,J３60,M11.1.0",
        False,
        False,
        "全角数字落在**规则文本**里 —— 只有规则文本的 ASCII 检查能拦（数字字段检查看的是偏移与切换时刻，不含规则本身）",
    ),
    ("AAA0<" + "中" * 170 + ">", False, False, "3 + 510 + 2 = 515 > 512：越过和式上界（多字节名字侧）"),
    ("<" + "A" * 508 + ">-1<BBB>,M3.2.0,M11.1.0", False, False, "508 + 3 + 2 = 513 > 512：和式上界外一字节"),
    (
        "<" + "A" * 512 + ">-1",
        False,
        False,
        "无 dst 形态 512 + 1 = 513 > 512 —— 旧口径**根本没检查**这一支，于是误收了 C 库拒绝的串",
    ),
    (
        "<" + "A" * 507 + ">-1<" + "B" * 507 + ">,M3.2.0,M11.1.0",
        False,
        False,
        "两个名字**各自**都 ≤507 却和 = 1016 > 512：单名上限口径在这条上误收，和式口径才拒",
    ),
    # ——— 以下为 Codex r10 新增。⛔ 一律**追加在末尾**：负控段按 `accept-N`/`reject-N`
    #     绑定 id，在中间插入会让所有绑定静默错位（红仍是红，但红的不是声称的那条）。
    (
        "AAA-1,M3.2.0,M11.1.0",
        True,
        True,
        "**无 dst 名但带合法规则**：C 库照常实行 DST，规则用**自带的**那套、dst 名借 posixrules 的、"
        "dst 偏移取 std_off+3600。只判 `dst is None` 就早退会**误算**整整一小时（r10 H1）",
    ),
    ("AAA-1,J60,J300", True, True, "同上，J 形式规则"),
    ("AAA0001", True, True, "前导零偏移：C 库数字字段**无位数上限**（`AAA00000001` 也收）（r10 M2）"),
    ("AAA1BBB,M03.02.00,M11.1.0", True, True, "规则字段前导零：C 库收（r10 M2）"),
    ("AAA1BBB,J0001,J0200", True, True, "儒略日前导零：同上"),
    ("A1", True, True, "**单字符**名：C 库不要求 POSIX 的「≥3 字符」（r10 M1）"),
    ("<>1", True, True, "**空**引用名：C 库接受（r10 M1）"),
    (
        "ABC<DEF>2",
        True,
        True,
        "裸名一直吃到遇见数字为止 ⇒ 名字是 `ABC<DEF>`（C 库 tzname 打成 `ABC_DEF_`）。"
        "原 `[A-Za-z]{3,}` 会把它判成「缺 std 偏移」而整串拒（r10 M1）",
    ),
    ("ABC DEF2", True, True, "同上，名字里带空格"),
    (
        "<" + "A" * 511 + ">-1<>,M3.2.0,M11.1.0",
        True,
        True,
        "511 + **空** dst 名 = 512：空名**不占**缓冲区、不加 NUL。机械地按 511+0+2=513 算会误拒",
    ),
    ("<" + "A" * 512 + ">-1<>,M3.2.0,M11.1.0", False, False, "512 + 1 = 513 > 512：空 dst 名侧的上界外一字节"),
    (
        "AAA-1BBB\n",
        True,
        True,
        "同上条：C 库把尾部换行吃进 dst 名（tzname `('AAA','BBB_')`），本实现现已跟随。",
    ),
    (
        "AAA-1BBB,M3.2.0,M11.1.0\n",
        False,
        False,
        "对照组：**带显式规则**时尾部换行两边都拒。⛔ 这条是 `\\Z` 锚的守门样本 —— "
        "正则结尾若写 `$`，Python 的 `$` 在末尾换行**之前**收尾，这串会被误收"
        "（删掉那条尾部空白检查后第一次跑对拍，红的就是它）。",
    ),
    (
        "AAA24BBB",
        True,
        False,
        "⚠️分歧: |std_off| = 24h。C 库**接受**（实测 `tzset()` 成功、`tm_gmtoff=-86400`），"
        "但 Python 的 `tzinfo` 要求偏移严格 < 24h，接受它 `utcoffset()` 会抛。"
        "这是本实现为保证全年可表示做的收紧，**不是**跟随 C 库（r9 L4 的归因更正）。",
    ),
    (
        "AAA12BBB-12,M3.2.0,M11.1.0",
        True,
        False,
        "⚠️分歧: 两侧各自合法而**差**恰为 24h。C 库接受并在冬季给 −12h，本实现全年退 UTC。"
        "取舍: `dst()` / `timetuple()` 在夏季抛是**运行时**炸、落点不可预测（模板渲染 / 序列化 / 日志）；"
        "退 UTC 是可预测的降级。",
    ),
]


@pytest.mark.parametrize("copy_id", _COPY_IDS)
@pytest.mark.parametrize(
    "spec,libc_ok,impl_ok,why",
    _ACCEPTANCE_DOMAIN_CASES,
    ids=[f"{'accept' if ok else 'reject'}-{i}" for i, (_s, _l, ok, _w) in enumerate(_ACCEPTANCE_DOMAIN_CASES)],
)
def test_accepted_domain_matches_libc(tz_env, copy_id, spec, libc_ok, impl_ok, why):
    """解析器接受哪些串，必须与 C 库逐条一致——**分歧允许存在，但必须显式声明**。

    ⛔ 表有**四**列而不是两列，因为「C 库收不收」和「本实现收不收」是两件事：
    把它们压成一列，就只能在「假装完全一致」和「把分歧条目从表里删掉」之间选，
    两种做法都会让表失真。Codex r10 M3 抓到的正是前一种——表里 `AAA-1\\n` 标着
    「C 库也拒」，而 C 库**接受**它并实行 DST，测试却全绿，因为它根本没问过 C 库。

    ⛔ 所以这条测试**自己去问 C 库**（`_libc_accepts`），把表里的 libc 列当作
    需要被核验的断言而不是可信输入。手写的那一列再也不可能悄悄写错。
    """
    if "\x00" not in spec:  # 含 NUL 的串进不了环境变量，C 库侧问不到
        assert _libc_accepts(spec) == libc_ok, (
            f"表里的 **libc 列**与实测不符: {spec[:60]!r} 表称 C 库{'收' if libc_ok else '拒'}，"
            f"实测{'收' if not libc_ok else '拒'}。\n"
            f"  依据栏写的是: {why}\n"
            "  —— 这一列是手写的，写错过（r10 M3）。以实测为准，改表。"
        )
    module = backend_tz if copy_id == "backend" else _load_local_tz()
    accepted = module.parse_posix_tz(spec) is not None
    assert accepted == impl_ok, (
        f"[{copy_id}] 本实现的接受域变了: parse_posix_tz({spec[:60]!r}…) "
        f"{'接受了' if accepted else '拒绝了'}，表称应当{'接受' if impl_ok else '拒绝'}\n"
        f"  依据: {why}"
    )
    if libc_ok != impl_ok:
        assert why.startswith("⚠️分歧"), (
            f"{spec[:60]!r} 与 C 库不一致（C 库{'收' if libc_ok else '拒'} / "
            f"本实现{'收' if impl_ok else '拒'}），依据栏必须以「⚠️分歧」开头并写清取舍。\n"
            f"  当前依据: {why}"
        )


@pytest.mark.parametrize("copy_id", _COPY_IDS)
def test_southern_season_in_year_9999_is_not_dropped(tz_env, copy_id):
    """9999 年的**南半球**季度不得被候选年上界整段排除（Codex r9 L1）。

    ⛔ 上一轮把南支写成 `elif year < 9999` —— 那让 9999 年的整个跨年季度消失。
    `_dst_window(10000)` 确实会抛，但季度**确实**从 `s(9999)` 开始；终点算不出来时
    按「从 s 起一直到可表示范围末尾」处理，那正是 C 库在该段的行为。
    """
    spec = "AAA0BBB,M10.1.0,M3.1.0"  # start 10 月、end 3 月 ⇒ 南半球形态
    tz_env(tz=spec)
    resolved = _display_tz_of(copy_id)
    instant = datetime(9999, 12, 1, 23, 30, tzinfo=timezone.utc)
    got = instant.astimezone(resolved).replace(tzinfo=None)
    libc = instant.astimezone().replace(tzinfo=None)
    assert got == libc, (
        f"[{copy_id}] 9999 年南半球季度被丢掉了: 本实现给 {got}，C 库给 {libc}\n"
        "  南支的候选年上界不能写成 `elif year < 9999`——那会把整段季度排除。"
    )


@pytest.mark.parametrize("copy_id", _COPY_IDS)
def test_tzname_uses_dst_membership_not_offset_equality(tz_env, copy_id):
    """`tzname()` 判 DST **身份**要用 `_in_dst`，不能比较偏移（Codex r9 L2）。

    ⛔ 两侧偏移**相等**的规格（`AAA0BBB0,…`）下「实际偏移 == dst_off」恒真，
    冬季也会返回 dst 名。偏移大小与夏令时身份是两回事 —— 本文件的 fold 处理一直是
    「按偏移大小选侧、按 `_in_dst` 判身份」，`tzname` 也该跟同一条。
    """
    spec = "AAA0BBB0,M3.2.0,M11.1.0"  # 两侧偏移都是 0
    tz_env(tz=spec)
    resolved = _display_tz_of(copy_id)
    winter = datetime(2026, 1, 1, 0, 30, tzinfo=timezone.utc).astimezone(resolved)
    summer = datetime(2026, 7, 1, 0, 30, tzinfo=timezone.utc).astimezone(resolved)
    assert winter.tzname() == "AAA", (
        f"[{copy_id}] 冬季 tzname 应为 std 名 'AAA'，实得 {winter.tzname()!r} —— "
        "偏移相等时不能用「偏移 == dst_off」判身份。"
    )
    assert summer.tzname() == "BBB", (
        f"[{copy_id}] 夏季 tzname 应为 dst 名 'BBB'，实得 {summer.tzname()!r}（正控：别改成恒返回 std 名）"
    )


#: 整串属性校验（控制字符 / 可严格编码 / 字节长度 / 偏移范围）对**所有**形态生效，
#: 不只是「省略切换规则」那一支 —— Codex r8 把这两条列为**既有**缺口，本卡一并收口：
#:   ① 无 DST 的 `<非法字节>0` 与带显式规则的 `AAA0<非法字节>,M3.2.0,M11.1.0`
#:      在 BASE 上会把代理字符留在 `.key` 里，在 `JSONResponse` 的编码边界抛；
#:   ② 带显式规则的 `AAA24BBB,M3.2.0,M11.1.0` 在 BASE 上被接受、换算时抛 ValueError。
#: (spec, 该拒的理由, 该形态属于哪一支)
_ALL_BRANCH_REJECT_CASES = [
    ("AAA24BBB,M3.2.0,M11.1.0", "std 侧 −24h 不可表示（⚠️ C 库**接受**它并给 −24h；抛的是 Python）", "显式规则"),
    ("AAA0:60BBB,M3.2.0,M11.1.0", "分钟 60 越界（C 库退 UTC，与本实现一致）", "显式规则"),
    ("AAA0", "无 DST + std 偏移为 0：合法，本条是**正控**位（见下方 accept 表）", None),
]


@pytest.mark.parametrize("copy_id", _COPY_IDS)
@pytest.mark.parametrize(
    "spec,why",
    [(s, w) for s, w, branch in _ALL_BRANCH_REJECT_CASES if branch is not None],
)
def test_offset_domain_is_checked_on_every_branch_not_only_omitted_rules(copy_id, spec, why):
    """偏移取值域的校验必须覆盖**带显式规则**那条路径，不能只管省略规则分支。

    ⛔ 这是 Codex r8 列为「既有」的那条（BASE 同样有），本卡一并收口 ——
    因为校验一旦只加在一个分支上，同一类非法输入换条路就能进来。
    """
    module = backend_tz if copy_id == "backend" else _load_local_tz()
    got = module.parse_posix_tz(spec)
    assert got is None, (
        f"[{copy_id}] 显式规则分支未校验偏移取值域: parse_posix_tz({spec!r}) 返回 {got!r}\n"
        f"  {why}\n"
        "  整串属性与偏移范围的校验要放在两个分支的**共用**位置，不能只写在省略规则那一支里。"
    )


@pytest.mark.parametrize("copy_id", _COPY_IDS)
@pytest.mark.parametrize("side", sorted(_NON_UTF8_TZ_BYTES_ALL_BRANCH))
def test_non_utf8_key_never_reaches_response_on_any_branch(tz_env, copy_id, side):
    """无 DST / 显式规则两支也不得把代理字符留在 `.key` 里（Codex r8 既有①）。

    ⛔ BASE 在这两支上会返回 `key='<U+DCFF>0'` 之类，序列化直接抛 —— 与本卡 r6 修掉的
    省略规则分支是同一个病，只是换了条路进来。判据同样打在**编码到字节**那一步。
    """
    raw_tz = _NON_UTF8_TZ_BYTES_ALL_BRANCH[side]
    saved_tz = os.environb.get(b"TZ")
    saved_canvas = os.environ.get("CANVAS_TZ")
    os.environ.pop("CANVAS_TZ", None)
    try:
        os.environb[b"TZ"] = raw_tz
        time.tzset()
        resolved = _display_tz_of(copy_id)
        key = getattr(resolved, "key", None)
        try:
            json.dumps({"display_tz": key}, ensure_ascii=False).encode("utf-8")
        except Exception as exc:  # noqa: BLE001
            raise AssertionError(
                f"[{copy_id}] TZ={raw_tz!r}（{side}）的 .key={key!r} 过不了响应序列化: "
                f"{type(exc).__name__}: {exc}\n"
                "  整串编码校验要对**所有**形态生效，不能只写在省略规则分支里。"
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
#: （⚠️「本卡不动带显式规则的那条路径」已过时：r9 起用户裁定「既有也要修」，
#:   显式规则那一支的整串属性与偏移校验都已提到两分支共用位置，三支同口径。）
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
    # 名字长度在既有正则里无上限。C 库的真口径是**两个名字连同各自的 NUL 终止符**共用
    # 一个 512 字节缓冲区（macOS tzcode 的 `TZ_MAX_CHARS`）⇒ 这是一条**和式**约束：
    # 带 dst 时 `len(std) + len(dst) + 2 <= 512`。下面这条是**裸名**形态的边界样本，
    # 与引用名形态同口径（实测 `"A"*507+"0BBB"` = 507+3+2 = 512 接受、
    # `"A"*508+"0BBB"` = 508+3+2 = 513 退 UTC）。
    # ⛔ 这段注释曾写「本实现改用保守的整串 255 字节上限」——那个上限早已移除，
    #    留着会让后人以为判据是整串长度，而它其实是名字的和。
    ("A" * 508 + "0BBB", "裸名 508 + dst 名 3 + 2 = 513 > 512：C 库退 UTC，本实现按和式拒"),
    # ⛔ 长度必须按 **UTF-8 字节**量：`len()` 数的是 Unicode 字符，下面这串的引用名只有
    #    170 个字符却是 510 字节 —— 按字符量和式只有 3+170+2 = 175（放行），按字节量是
    #    3+510+2 = 515 > 512 才拦得住（Codex r4 HIGH-1 的量纲教训）。
    ("AAA0<" + "中" * 170 + ">", "dst 名 170 字符 / **510 字节**：按字符量会放行，按字节量才拦得住"),
    ("<" + "中" * 170 + ">0BBB", "同形，落在**标准侧**引用名上（510 + 3 + 2 = 515）"),
    # ⛔ NUL 进不了完整的 C 环境字符串，但**能从 JSON 的 `display_tz` 自报值进来** ——
    #    桶位门会用本函数重建生产者时区（Codex r5 M1：BASE 拒收，补规则后整串放行）。
    # ⛔ 这条用例守的是 `parse_posix_tz` 里那条显式 NUL 检查的**唯一显形位置**：
    #    NUL 在引用名**内部**。正则的引用名是 `<[^<>]+>`，`[^<>]` 放行 NUL ⇒ 能匹配进来，
    #    只有那条检查能拒。放在串尾或放在偏移与 dst 名之间的 NUL 则由正则先拒。
    #    换句话说：删掉这条用例，那条检查就没有任何门守着了。
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
        "  会把一批 C 库都不认的串放进归日链路（⚠️ 这批串里 C 库**认**的那些已在 r11 被放行，"
        "  这里剩下的是双方都拒的）。"
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
#: 是规格驱动的（⚠️ 原文举的 `AB3` 例子已不成立：r11 把裸名放宽到与 C 库同口径后，
#: 两字母甚至单字母简名双方**都接受**；下面留着的是仍然成立的那些分歧），规格
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

    门的职责是校验「这份产出自不自洽」，参照系必须取**投影自报的 `display_tz`**
    那套完整时区规则（不是 `generated_at` 自带的固定偏移 —— 那个只在它自己那一刻
    等于生产者的真实偏移，到期时刻跨了 DST 切换就差一档）。`display_tz` 缺席或为
    null ⇒ 整份判 corrupt，见 `test_bucket_gate_rejects_wrong_buckets_even_when_display_tz_is_absent`。
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
    picker_tz_saved = picker._display_tz
    picker._display_tz = lambda _tz=ZoneInfo("Asia/Shanghai"): _tz
    try:
        moment = datetime(2026, 7, 31, 15, 0, tzinfo=timezone.utc)  # 上海 7/31 23:00
        payload, _ranked = picker.build_payload(vault, moment, {}, picker.load_decay(vault))
    finally:
        picker._display_tz = picker_tz_saved

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
                "门用了此刻的显示时区当参照日 —— 应改用投影自报的 display_tz 规则重算。"
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
        # ⇒ 按投影自报的 display_tz 规则重算，合法投影必须仍被放行（r1 HIGH-2）。
        # ⛔ 这里曾写「退回自带偏移」—— 那是 r1 的旧方案，已被 r5 HIGH-2 推翻
        #    （固定偏移只在 generated_at 那一刻成立）。规范性措辞与现口径不符会
        #    把后人引回旧方案（Codex r10 L3 / r11 L1）。
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
    # 生产器侧钉在 producer_tz（CARD-G6-9c-R3 起 pick 是 `_display_tz()` 现取，
    # 钉法改为替换该函数；直接 setenv 也可行，但替换函数与本文件其余夹具同形）
    saved = picker._display_tz
    picker._display_tz = lambda _tz=ZoneInfo(producer_tz): _tz
    try:
        moment = datetime.fromisoformat(moment_iso.replace("Z", "+00:00"))
        payload, _ranked = picker.build_payload(vault, moment, {}, picker.load_decay(vault))
    finally:
        picker._display_tz = saved

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
            "  参照系取错了：DST 边界要用完整时区规则，切了时区要按投影自报的 display_tz 重算。"
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
    saved = picker._display_tz
    picker._display_tz = lambda _tz=ZoneInfo("America/New_York"): _tz
    try:
        payload, _r = picker.build_payload(
            vault, datetime(2026, 3, 8, 5, 30, tzinfo=timezone.utc), {}, picker.load_decay(vault)
        )
    finally:
        picker._display_tz = saved

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
    saved_b = picker._display_tz
    picker._display_tz = lambda _tz=ZoneInfo("America/Bogota"): _tz
    try:
        bogota_payload, _r2 = picker.build_payload(
            vault, datetime(2026, 3, 8, 5, 30, tzinfo=timezone.utc), {}, picker.load_decay(vault)
        )
    finally:
        picker._display_tz = saved_b
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
    照样放行。（Δ 是**有界**的，但界**不再**是 r2 说的「正则字段位宽给的 ±83 天」——
    r11 把位宽放宽成了 `\\d+`，那条论证随之作废；现在的界来自解析器的量级检查：
    两侧偏移各自 < 24h 且**两侧之差** < 24h ⇒ |Δ| < 24h。界变小了，结论不变：
    24 小时仍远大于任何实用带宽，缺 `display_tz` 时两个要求依旧不可兼得。
    别写成「Δ 无界」——r2 LOW-2 证伪过；也别再引 ±83 天——r10 L4 证伪过。）
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
    saved = picker._display_tz
    picker._display_tz = lambda _tz=ZoneInfo("America/New_York"): _tz
    try:
        payload, _r = picker.build_payload(
            vault, datetime(2026, 3, 8, 5, 30, tzinfo=timezone.utc), {}, picker.load_decay(vault)
        )
    finally:
        picker._display_tz = saved

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


# ══════════════════════════════════════════════════════════════════════════
# CARD-G6-9c-R3 新增段（BATCH-2026-09-18-第十五批）
#
# 上面那些门守的是「解析器与 libc 的接受域对齐」。下面这一段守的是**第十四批
# Codex r12 点名的四条 HIGH** 和**本卡撤掉 3.11+ 正则语法之后新出现的前提**。
#
# ⛔ 一句必须留下的背景，否则后人会以为这四条是本卡修的：r12 四条 HIGH 的修复
#    在移植进来的 `a8cefab4` 里**已经完成**（本卡移植后、改任何一行之前实测四组
#    输入全部与 libc 一致，证据 `evidence-g69cr3/g69cr3-red-high-pre-*.txt`）。
#    本卡在这四条上的贡献是**保住它们**：R2 的修法依赖 Python 3.11+ 的占有量词与
#    原子组，而 launchd 链的兜底解释器是系统自带的 3.9.6 —— 那一版在 3.9.6 上
#    `import` 即 `re.error`，整条复习推送在模块加载阶段就崩。本卡把护栏从**引擎**
#    层（占有量词）换到**文法**层（std_off 必填 ⇒ 名字段贪婪终点唯一），四条 HIGH
#    的行为判据一条不改，同时两个解释器都能加载。
#    所以下面 `r12_h1..h4` 四条用例在本卡是**回归门**而不是修复门 —— 它们要拦的是
#    「有人把正则改回去 / 再引一个歧义分割点」。
# ══════════════════════════════════════════════════════════════════════════


def _parser_of(copy_id):
    """按副本 id 取 `parse_posix_tz`。两份是同源副本，每条门都必须两份都跑。"""
    if copy_id == "backend":
        return backend_tz.parse_posix_tz
    return _load_local_tz().parse_posix_tz


@pytest.mark.parametrize("copy_id", _COPY_IDS)
def test_r12_h1_quoted_name_never_falls_back_to_bare_name(copy_id):
    """r12 H1：引用名扫不到闭合 `>` 时不得回退成裸名（两个方向都断言）。

    libc 对 `<AAA1><BBB2` 全年 UTC。回退成裸名会解析成「名字 `<AAA` + 偏移 1 +
    dst 名 `><BBB` + dst 偏移 2」⇒ 冬 −01:00 夏 −02:00 —— 它**不报错**，只是每天
    把「今天」算偏，而归日偏一天在复习链上等于那天的卡片全部错档。

    ⛔ 反方向同样要钉：`<AAA1` / `<1` / `<<AAA1` 这一族 libc 是**接受**的
       （扫不到 `>` ⇒ 整个当裸名，`<` 本身计入名字）。只断言「该拒的拒了」会让
       「一律拒 `<` 开头」这种过度收紧同样通过 —— 那是误拒，不是修复。
    """
    parse = _parser_of(copy_id)
    assert parse("<AAA1><BBB2") is None, (
        f"[{copy_id}] `<AAA1><BBB2` 被接受 —— libc 对它退 UTC。引用名一旦以 `<` 开头就必须闭合，不能回退成裸名。"
    )
    assert not _libc_accepts("<AAA1><BBB2"), "libc 居然接受 `<AAA1><BBB2` —— oracle 前提变了，先查 libc"
    for spec in ("<AAA1", "<1", "<<AAA1"):
        assert parse(spec) is not None, f"[{copy_id}] {spec!r} 被拒 —— libc **接受**这一族（扫不到 `>` ⇒ 当裸名）。"
        assert _libc_accepts(spec), f"libc 不接受 {spec!r} —— oracle 前提变了"


@pytest.mark.parametrize("copy_id", _COPY_IDS)
def test_r1_dst_quoted_name_never_falls_back_to_bare_name(copy_id):
    """Codex r1 HIGH-1：**dst** 侧的引用名也不得回退成裸名。

    r12 H1 修的是 **std** 侧（第三支加 `(?![<:])` 前瞻），dst 侧漏了。后果：
    `A1<B>>2` 里引用名分支匹配到 `<B>` 后，`>2` 不是合法偏移 ⇒ 该支失败 ⇒
    **回退到裸名分支**把 `<B>>` 整个当 dst 名收下；而 ⑥' 只查「`<` 开头必须以 `>` 结尾」，
    `<B>>` 恰好以 `>` 结尾 ⇒ 放行。libc 对这一族全年 UTC，本实现却给冬 −01:00 夏 −02:00
    （dst 名打成 `B>`）—— 又是**误收 + 误算**。

    ⛔ 这条用例的存在本身是一条教训：**原 H1 的那组输入通过，不代表引用名这一类修完了**。
       r12 H1 给的输入全在 std 侧，本卡移植后实测全绿就以为这一类收口了 ——
       Codex r1 用 3888 规格 × 23328 时刻的对拍找出 dst 侧同型的洞（900 规格 5040 点不同）。
    """
    parse = _parser_of(copy_id)
    # 该拒的：引用名未正常闭合而被裸名分支吃下
    for spec in ("A1<B>>2", "A1<B>C>2", "A1<B><C>2"):
        assert parse(spec) is None, (
            f"[{copy_id}] {spec!r} 被接受 —— libc 对它退 UTC。"
            "dst 引用名匹配失败后不得回退成裸名（裸名分支必须禁 `<` 开头，与 std 第三支同形）。"
        )
        assert not _libc_accepts(spec), f"libc 居然接受 {spec!r} —— oracle 前提变了"
    # 反方向：正常闭合的引用名与空引用名仍须收（修复不能过度收紧）
    for spec in ("A1<B>2", "AAA1<BBB>2", "AAA1<>2"):
        assert parse(spec) is not None, (
            f"[{copy_id}] {spec!r} 被拒 —— libc **接受**它。修 dst 裸名回退不能把合法引用名一起拒掉。"
        )
        assert _libc_accepts(spec), f"libc 不接受 {spec!r} —— oracle 前提变了"
    # dst 名空 + 偏移带符号这一族必须仍收（r12 M1；也是 HIGH-2 修法的边界）
    for spec in ("AAA1+2", "AAA1-2"):
        assert parse(spec) is not None, (
            f"[{copy_id}] {spec!r} 被拒 —— dst 名为空 + 偏移带符号是 C 库接受的合法形态（r12 M1）。"
            "HIGH-2 的修法（空名分支写成 `(?=[+-])`）必须保住它。"
        )


@pytest.mark.parametrize("copy_id", _COPY_IDS)
def test_r12_h2_colon_in_offset_is_not_reinterpreted_as_dst_name(copy_id):
    """r12 H2：偏移里的冒号解析失败后，残形不得被重新分词成 dst 名。

    libc 对 `AAA1:` / `AAA1:30:BBB2` 都退 UTC —— 偏移之后的 `:` 属于偏移，
    后面必须跟数字。而偏移**吃满三段**之后多出来的 `:` 才轮到 dst 名
    （`ABC1:30:2:3` libc 收，tzname 打成 `(':', 'ABC')`）。

    ⛔ 正例不要用 `ABC1:30:2:30`：它的 dst 偏移是 −30 h，会被 ⑧ 的量级检查拒掉，
       那是一条**已声明的收紧**，与 H2 无关（本卡负控第一版在这里假红过一次）。
    """
    parse = _parser_of(copy_id)
    for spec in ("AAA1:", "AAA1:30:", "AAA1:30:BBB2", "AAA1:BBB2"):
        assert parse(spec) is None, (
            f"[{copy_id}] {spec!r} 被接受 —— libc 对它退 UTC。偏移没吃满三段时，"
            "那个 `:` 还属于偏移，不能改判成 dst 名的首字符。"
        )
        assert not _libc_accepts(spec), f"libc 居然接受 {spec!r} —— oracle 前提变了"
    for spec in ("ABC1:30:2:3", "ABC1:2:3:4"):
        assert parse(spec) is not None, (
            f"[{copy_id}] {spec!r} 被拒 —— libc 接受它（dst 名就是 `:`）。"
            "H2 的修复不能把偏移吃满三段之后的那个冒号也一起禁掉。"
        )
        assert _libc_accepts(spec), f"libc 不接受 {spec!r} —— oracle 前提变了"


@pytest.mark.parametrize("copy_id", _COPY_IDS)
def test_r12_h3_tokenizer_stays_linear_in_input_length(copy_id):
    """r12 H3：分词耗时对输入长度线性 —— 本卡的**承重**判据。

    r12 实测的缺陷形态：`parse_posix_tz('A' + '١'*n + '+')` 在 n=50/100/200 上
    0.013 / 0.197 / 3.054 秒，翻倍约 ×16。

    ⛔ 为什么这条在本卡是承重而不是装饰：R2 靠**占有量词**（引擎层面禁止回溯）
       消除它，本卡撤掉占有量词（3.9.6 不支持）之后靠的是**文法**性质 ——
       `std_off` 必填 ⇒ std 名的贪婪终点唯一 ⇒ std 名与 dst 名不能再瓜分同一串。
       换句话说，这道计时门是唯一能证明平方没被放回来的东西。谁把 `std_off`
       改回可选，这里会立刻红（负控段 `H3QUANT` 就是拆这一条）。
    ⚠️ 探针不能用 `'A'*n + '!'`：`!` 是合法名字字符，那串会直接匹配成功，
       量到的是成功路径而不是失败路径（r12 明确点过这一条）。

    ⛔ **判据口径更正（本卡实测，与卡文字面不同，已在验收单登记）**：卡文写的是
       「n=202/404/808 的耗时比 ≤3」，若读成 `t(808)/t(202) ≤ 3` 则**对真正线性的
       实现也会红** —— 长度从 202 到 808 是 **4 倍**，线性耗时本来就该 ≈4 倍。
       本卡基线实测 3.55（min-of-5），落在门限外侧。所以这里按**相邻比**读它
       （线性 ≈1.9 / 平方 ≈3.5~4.0，门限 3 恰好分得开），并**另加一条不依赖比值的
       绝对门**作为主判据：n=3232 ≤ 0.05 s。
       后者的余量才是真正可靠的 —— 基线 0.000094 s（余量 ≈530 倍），
       把 `std_off` 改回可选的平方态 0.527 s（超标 ≈10 倍）。
       ⚠️ 小 n 上的绝对门抓不住平方：平方态 n=808 只要 0.035 s，仍在 0.05 s 以内。
          这就是为什么必须把绝对门推到 n=3232 而不是停在卡文给的 202。
    ⚠️ 计时一律取 **min-of-5**：这几个量级在微秒级，单次采样里调度噪声与被测量同量级，
       比值会在门限附近抖（本卡单采样实测同一代码给出过 2.43 与 3.80 两个值）。
       取最小值是计时基准的常规做法 —— 它测的是「这段代码最快能多快」，噪声只会加不会减。
    """
    parse = _parser_of(copy_id)

    def _best(probe, repeat=5):
        best = float("inf")
        for _ in range(repeat):
            start = time.perf_counter()
            assert parse(probe) is None, f"[{copy_id}] 探针 {probe[:3]!r}… 居然被接受 —— 探针失效"
            best = min(best, time.perf_counter() - start)
        return best

    for label, make in (
        # 名字段长（R2 与本卡 r1 之前唯一覆盖的一维）
        ("name-arabic", lambda n: "A" + "١" * n + "+"),
        ("name-ascii", lambda n: "A" * n + "+"),
        # ⛔ 数字段长（Codex r1 HIGH-2 指出的「门未覆盖的路径」）：
        #    空 dst 名让 std_off 与 dst_off 瓜分同一串数字 —— 与名字段那个歧义点同构。
        #    修之前实测 n=1616 要 0.098 s、n=3232 要 0.40 s，而门只测名字段 ⇒ 全绿。
        ("digits", lambda n: "A" + "1" * n + "+"),
        ("digits-colon", lambda n: "A" + "1" * n + ":" + "1" * n + "+"),
        ("digits-after-name", lambda n: "AAA" + "1" * n + "+"),
    ):
        elapsed = {n: _best(make(n)) for n in (202, 404, 808, 3232)}
        # ① 卡文的原始绝对门（保留）
        assert elapsed[202] <= 0.05, f"[{copy_id}/{label}] n=202 耗时 {elapsed[202]:.6f}s > 0.05s —— 分词在回溯。"
        # ② 主判据：不依赖比值的绝对门，推到平方态一定超标的规模
        assert elapsed[3232] <= 0.05, (
            f"[{copy_id}/{label}] n=3232 耗时 {elapsed[3232]:.6f}s > 0.05s —— 分词不是线性。"
            f"（基线约 0.0001s；把 std_off 改回可选的平方态约 0.53s）"
        )
        # ③ 相邻比：线性 ≈1.9，平方 ≈3.5~4.0
        for smaller, bigger in ((202, 404), (404, 808)):
            ratio = elapsed[bigger] / max(elapsed[smaller], 1e-9)
            assert ratio <= 3.0, (
                f"[{copy_id}/{label}] 长度翻倍耗时比 t({bigger})/t({smaller}) = {ratio:.2f} > 3"
                " —— 不是线性。"
                f"（202:{elapsed[202]:.6f}s 404:{elapsed[404]:.6f}s"
                f" 808:{elapsed[808]:.6f}s 3232:{elapsed[3232]:.6f}s）"
            )


@pytest.mark.parametrize("copy_id", _COPY_IDS)
def test_r12_h4_overlong_digit_fields_do_not_raise(copy_id):
    """r12 H4：超长数字字段不得抛，且要与 libc 同判（收，给 −01:00）。

    Python 3.11+ 对 >4300 位的整数字符串转换直接抛 `ValueError: Exceeds the limit`。
    `AAA` + 4300 个 `0` + `1` 是 C 库**接受**的合法串 —— 不处理的话
    `display_tz()` 整个抛出去，而它在模块级启动路径上被调用。

    ⛔ 修法必须是「剥前导零后再限长」而不是「捕获异常后拒绝」: r12 明说仅捕获会
       留下误拒，因为这条串是合法的。所以这里既断言不抛，也断言**收**并且偏移对。
    ⛔ 防线必须在 `_posix_offset_seconds` / `_parse_hms` **内部**，不能只写在调用方
       的字段校验里 —— 那两个函数在字段校验**之前**就被调用了。
    """
    parse = _parser_of(copy_id)
    spec = "AAA" + "0" * 4300 + "1"
    assert _libc_accepts(spec), "libc 不接受超长前导零串 —— oracle 前提变了，先查 libc"
    try:
        tz = parse(spec)
    except Exception as exc:  # noqa: BLE001 — 抛出来本身就是缺陷
        raise AssertionError(
            f"[{copy_id}] 超长数字字段让解析器抛了 {type(exc).__name__}: {exc} —— "
            "libc 接受这条串，抛异常会让 display_tz() 在启动路径上挂掉。"
        ) from exc
    assert tz is not None, f"[{copy_id}] 超长前导零串被拒 —— libc 接受它，这是误拒不是修复"
    assert tz.utcoffset(datetime(2026, 1, 15, 12)) == timedelta(hours=-1), (
        f"[{copy_id}] 超长前导零串算出 {tz.utcoffset(datetime(2026, 1, 15, 12))}，libc 给 −01:00"
    )
    # 同族的其余入口：切换时刻 / M 规则 / J 规则 / 分钟 / 秒 / etime 都走同一条防线。
    # ⛔ 不能只断言「不抛」（Codex r1 MEDIUM）：那样「让 ⑤ 对超长字段直接 return None」
    #    这种**把合法串误拒**的实现也照样通过 —— 负控实测：在内存里让 ⑤ 对 >4300 位的
    #    切换小时字段返回 None，原用例两个副本参数**仍然全绿**。所以这里要同时断言
    #    「返回非 None」与「偏移与 libc 相同」。
    # ⛔ 探针必须覆盖**每一处** call-site 的剥零防线（本卡自审抓出）：
    #    生产代码里 `lstrip("0")` 共 9 处，其中 5 处是「先剥零再 int()」的防线。
    #    本门第一版只给了 2 条串（stime 小时 + J 规则），逐处摘掉 `.lstrip("0")` 做负控实测：
    #      · L199 `_posix_offset_seconds` / L242 `_nums` 位数 / L253 裸 n / L402 `_digits_ok`
    #        / L421 小时上限  ⇒ 门里那 2 条串**会**红（已覆盖）
    #      · L247 M 规则月份 / L423 分钟 / L425 秒 / L227 `_parse_hms`
    #        ⇒ 门里 3 条串**全无变化**，而它们对 libc 接受的合法串抛 `ValueError`（门未覆盖的路径）
    #    所以下面把每个 call-site 各配一条串。⚠️ L227 那处摘掉后是**静默改行为**
    #    （DST 起点位移）而不是抛 —— 靠下面的「偏移与 libc 相同」那一步接住。
    for other, why in (
        ("AAA1,M3.2.0/" + "0" * 4300 + "2,M11.1.0", "切换时刻小时（L402/L421）"),
        ("AAA1,J" + "0" * 4300 + "1,J365", "J 规则（L242/L253）"),
        ("AAA1,M" + "0" * 4300 + "3.2.0,M11.1.0", "M 规则月份（L247）"),
        ("AAA1,M3.2.0/2:" + "0" * 4300 + "3,M11.1.0", "切换时刻分钟（L423）"),
        ("AAA1,M3.2.0/2:3:" + "0" * 4300 + "4,M11.1.0", "切换时刻秒（L425）"),
        ("AAA1,M3.2.0,M11.1.0/" + "0" * 4300 + "2", "etime（回程规则同族）"),
        ("AAA1,M3.2.0/" + "0" * 4300 + "2:30,M11.1.0", "_parse_hms 内部（L227，摘掉是静默位移不是抛）"),
    ):
        assert _libc_accepts(other), f"libc 不接受 {why} 的超长前导零串 —— oracle 前提变了"
        try:
            tz_other = parse(other)
        except Exception as exc:  # noqa: BLE001
            raise AssertionError(
                f"[{copy_id}] {why}的超长数字让解析器抛了 {type(exc).__name__} —— H4 的防线漏了这两个入口之一。"
            ) from exc
        assert tz_other is not None, (
            f"[{copy_id}] {why}的超长前导零串被**拒**了 —— libc 接受它。"
            "H4 的修法是「剥零后限长」，不是「超长就 return None」（那是误拒）。"
        )
        # ⛔ 逐串问 libc，**不要**写死 −01:00：这些串的规则不同，
        #    `AAA1,J…,J365` 几乎全年 DST，冬季落在窗口**内** ⇒ 该给 dst 偏移 0。
        #    写死常量的版本会把正确实现判红（本卡实测），而且规则一改就失效。
        #    ⚠️ `_libc_utcoffset` 的口径必须是**当地墙钟**（与 `tz.utcoffset` 同）——
        #       本卡第一版写成「把 naive 当 UTC 瞬时」，跨切换点时会把正确实现判红，
        #       见该 helper 的 docstring。
        for _probe in (datetime(2026, 1, 15, 12), datetime(2026, 7, 15, 12)):
            _libc = _libc_utcoffset(other, _probe)
            assert tz_other.utcoffset(_probe) == _libc, (
                f"[{copy_id}] {why} 在 {_probe:%m-%d}：本实现 {tz_other.utcoffset(_probe)}，libc {_libc}"
            )


@pytest.mark.parametrize("copy_id", _COPY_IDS)
def test_r3_leading_colon_is_never_parsed_as_a_posix_spec(copy_id):
    """前导冒号的语义是「这是一条路径」，不是 POSIX 规格串（R2 负控存活段 ①）。

    C 库对 `:AAA-1` / `:EST5EDT,M3.2.0,M11.1.0` 一律给 UTC —— 剥一个冒号当路径找，
    找不到就结束，**不会**再拿整串去试规格。误收的代价是误算：`:AAA-1` 会被算成
    +01:00，整整差一小时。

    ⛔ 判据打在 `parse_posix_tz` 而不是 `display_tz`：后者上面还压着一道
       `if not env_tz.startswith(":")`，两层互为冗余。本卡实测把那道 if 改成
       `if True:` 之后**两层都零观测差异** —— 那正是 R2 负控 COLONPOSIX 段
       「存活」的真因（它拆的不是承载这条性质的那一层）。要问到承载层，
       就得绕开上面那道 if，直接问解析器。
    """
    parse = _parser_of(copy_id)
    for spec in (":AAA-1", ":EST5EDT,M3.2.0,M11.1.0", ":ABC5", "::Asia/Shanghai"):
        assert parse(spec) is None, f"[{copy_id}] {spec!r} 被当成 POSIX 规格串收下 —— C 库对它退 UTC。"


@pytest.mark.parametrize("copy_id", _COPY_IDS)
def test_r3_non_ascii_digits_rejected_in_offset_and_time_fields(copy_id, tmp_path):
    """非 ASCII 数字（全角 / 阿拉伯）不得进偏移与切换时刻（R2 负控存活段 ②）。

    C 库对 `AAA1,M3.2.0/２,M11.1.0` 这一族退 UTC。本实现由**两层**守着：
      第一层 = 正则的数字类写作 `[0-9]`（不是 `\\d`，后者连非 ASCII 数字一起吃）；
      第二层 = ⑤ 里那道 `all(x.isascii() and x.isdigit() ...)`。

    ⛔ 本卡实测：在当前正则下第二层**恒真**（192 条匹配成功的样本里触发 0 次），
       因为交到它手里的每一段本来就只可能是 ASCII 数字。但它**不是死代码** ——
       把第一层放宽成 `\\d` 之后它会接住，删掉它就接不住。所以下面分两段断言：
       端到端一段（守整条性质），纵深一段（单独问第二层，把正则临时放宽再问）。
       只写端到端那一段的话，删掉第二层不会有任何东西变红 —— 那正是 R2 负控
       ASCII 段「存活」的真因。
    """
    parse = _parser_of(copy_id)
    cases = ("AAA1,M3.2.0/２,M11.1.0", "AAA1,M3.2.0/٢,M11.1.0")
    # ── 端到端：整条性质 ──────────────────────────────────────────────
    for spec in cases:
        assert parse(spec) is None, f"[{copy_id}] {spec!r} 被接受 —— libc 对它退 UTC"
        assert not _libc_accepts(spec), f"libc 居然接受 {spec!r} —— oracle 前提变了"
    # ── 纵深：把第一层放宽，单独问第二层 ────────────────────────────────
    widened = _module_with_widened_digit_class(copy_id, tmp_path)
    for spec in cases:
        assert widened.parse_posix_tz(spec) is None, (
            f"[{copy_id}] 正则数字类放宽成 \\d 之后，{spec!r} 没有被 ⑤ 接住 —— "
            "⑤ 是纵深第二层，第一层一放宽它就必须说话。"
        )
    assert widened.parse_posix_tz("AAA1,M3.2.0/2,M11.1.0") is not None, (
        f"[{copy_id}] 放宽后连纯 ASCII 正例也被拒 —— ⑤ 收得过宽"
    )


@pytest.mark.parametrize("copy_id", _COPY_IDS)
def test_r3_non_ascii_digits_rejected_in_rule_fields(copy_id, tmp_path):
    """非 ASCII 数字不得进 `Jn` / `Mm.w.d` 规则字段（R2 负控存活段 ③）。

    与上一条同构：第一层是正则的 `[0-9]`，第二层是规则字段那道 `isascii()`。
    同样分端到端 + 纵深两段，理由见上一条的 ⛔ 段。
    """
    parse = _parser_of(copy_id)
    cases = ("AAA1,J３60,J365", "AAA1,M３.2.0,M11.1.0", "AAA1,３,M11.1.0")
    for spec in cases:
        assert parse(spec) is None, f"[{copy_id}] {spec!r} 被接受 —— libc 对它退 UTC"
        assert not _libc_accepts(spec), f"libc 居然接受 {spec!r} —— oracle 前提变了"
    widened = _module_with_widened_digit_class(copy_id, tmp_path)
    for spec in cases:
        assert widened.parse_posix_tz(spec) is None, (
            f"[{copy_id}] 正则数字类放宽成 \\d 之后，规则字段 {spec!r} 没有被接住"
        )
    assert widened.parse_posix_tz("AAA1,J60,J365") is not None, (
        f"[{copy_id}] 放宽后连纯 ASCII 规则正例也被拒 —— 规则字段校验收得过宽"
    )


def test_r3_both_copies_import_on_the_fallback_interpreter():
    """两份副本必须在 launchd 链的**兜底解释器** `/usr/bin/python3` 上 import 成功。

    ⛔ 这不是洁癖，是一条真实的上线面：`scripts/daily-review-push.sh:10-11` 在
       `$WT/backend/.venv/bin/python` 缺席时改用 `/usr/bin/python3`（本机 3.9.6），
       而 `:149` 直接跑 `$WT/scripts/daily_review_run.py`。移植进来的 `a8cefab4`
       版用了 3.11+ 的占有量词与原子组，在 3.9.6 上 **import 即 `re.error:
       unknown extension ?>`** —— 整条复习推送在模块加载阶段就崩，而且它不会
       表现成「归错日」，只是那一档静默退非零。
    ⚠️ 门跑的是**真的另一个解释器**，不是「检查源码里有没有某个字符串」：
       后者拦不住下一个 3.11+ 语法（比如 `(?<...>)` 的新写法）。
    """
    fallback = Path("/usr/bin/python3")
    if not fallback.exists():  # 非 macOS / 精简系统上没有它 —— 那也就没有这条上线面
        pytest.skip(f"{fallback} 不存在，本机没有这条兜底路径")
    ver = subprocess.run(
        [str(fallback), "-c", "import sys;print('.'.join(map(str,sys.version_info[:3])))"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert ver.startswith("3."), f"兜底解释器版本读不出来: {ver!r}"
    for label, workdir, modname in (
        ("scripts/local_tz.py", REPO_SCRIPTS, "local_tz"),
        ("app/core/display_tz.py", Path(backend_tz.__file__).parent, "display_tz"),
    ):
        proc = subprocess.run(
            [str(fallback), "-c", f"import {modname}; print({modname}.display_tz())"],
            cwd=str(workdir),
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, (
            f"{label} 在兜底解释器 {fallback}（{ver}）上 import 失败 —— "
            f"venv 缺席那天整条复习推送会在这里崩。\n"
            f"  rc={proc.returncode}\n  stderr: {proc.stderr.strip()[-600:]}"
        )
        assert proc.stdout.strip(), f"{label} 在 {ver} 上 import 通过但 display_tz() 没有输出"


def _module_with_widened_digit_class(copy_id, tmp_path):
    """把该副本的源码复制一份、**只**把正则数字类 `[0-9]` 放宽成 `\\d`，加载成独立模块。

    ⛔ 只给下面两条「纵深第二层」用例用。它们守的是「第一层（正则的 ASCII 数字类）
       一旦放宽，第二层（⑤ 与规则字段的 `isascii()`）要接住」—— 不先放宽第一层就
       问不到第二层头上，那正是 R2 负控 ASCII / RULEA 两段「存活」的真因：
       它们拆的是一道当前永远轮不到说话的检查，拆了当然什么都不变。
    ⚠️ 生产文件不落盘：源码读出来、改在内存里、写进 pytest 的 tmp 区加载。
    ⚠️ `sys.modules[name] = mod` 必须在 `exec_module` 之前（dataclass 自省会回查）。
    """
    path = REPO_SCRIPTS / "local_tz.py" if copy_id == "scripts" else Path(backend_tz.__file__)
    src = path.read_text(encoding="utf-8")
    target = None
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "_POSIX_TZ_RE" for t in node.targets):
            target = node
            break
    assert target is not None, f"[{copy_id}] 源码里找不到 _POSIX_TZ_RE 赋值 —— 提取器失效"
    call = target.value
    assert isinstance(call, ast.Call), f"[{copy_id}] _POSIX_TZ_RE 不是 re.compile(...) 调用"
    pattern = ast.literal_eval(call.args[0])
    assert "[0-9]" in pattern, (
        f"[{copy_id}] 正则里没有 `[0-9]` —— 放宽器的前提不成立，这两条纵深用例会跑在错的场景上（而且会**假绿**）"
    )
    mod_name = f"widened_digitclass_{copy_id}"
    mod_path = tmp_path / f"{mod_name}.py"
    mod_path.write_text(src, encoding="utf-8")
    spec_ = importlib.util.spec_from_file_location(mod_name, mod_path)
    assert spec_ is not None and spec_.loader is not None
    mod = importlib.util.module_from_spec(spec_)
    sys.modules[mod_name] = mod
    spec_.loader.exec_module(mod)
    mod._POSIX_TZ_RE = re.compile(pattern.replace("[0-9]", r"\d"))
    return mod


def test_r3_pick_side_reevaluates_display_tz_every_call(tz_env):
    """pick 侧现取门 —— 与上面显示侧的 ⑤ 同形，守的是 D-18 在**生产者**那一端。

    `scripts/daily_review_pick.py` 在本卡之前是全仓唯一把时区绑成**模块级常量**的
    地方（`_DISPLAY_TZ = local_tz.display_tz()`），与两份 TZ 副本 docstring 里那条
    「⛔ 消费侧必须每次调用现取, 禁止绑成模块级常量」直接冲突。本卡把它改成
    `_display_tz()` 每次现取。

    ⛔ 刻意**不**用 `importlib.reload`：reload 会让这条门恒真，等于没测。这里同进程
       改 `TZ` + `tzset()`，直接问 pick 自己的 `_display_tz()` 与 `_today_local()`。
    ⛔ 也**不**用 `spec_from_file_location` 重新加载（本卡第一版就是那么写的，被承重套件
       抓了个正着）：那会用真实模块名覆盖 `sys.modules["daily_review_pick"]`。
       ⚠️ 方向更正（Codex r1 LOW）：持有**旧**实例的是**测试模块自身**（`test_daily_review_run`
       在模块层 `import daily_review_pick as picker` 后一直用那个引用）；`daily_review_run`
       是在函数内 import、取到的反而是**新**实例。两边指向不同对象 ⇒ 夹具钉在测试模块持有的
       那个上、生产路径用另一个，钉法**静默失效**（那条用例只在多文件同跑时红、单跑绿）。
       用普通 `import`：从 `sys.modules` 现取，与本文件其余 4 处同形。
    ⛔ 断言必须带**日期翻转锚**，不能只比时区名：03:30Z 在 UTC 是 07-31、在纽约是
       07-30 —— 归日差一天才是这条门真正要拦的后果（那天的复习卡片会整批错档）。
       只比名字的话，「名字跟着变但归日用的还是旧时区」这种半吊子实现照样通过。
    ⚠️ 行为等价声明：launchd 那条路径上时区在进程生命周期内不变，所以改现取对线上
       产出零变化；这条门守的是「谁把它改回常量」，不是一个已发生的线上缺陷。
    """
    sys.path.insert(0, str(REPO_SCRIPTS))
    import daily_review_pick as picker  # noqa: PLC0415  # pyright: ignore[reportMissingImports]

    flip_instant = datetime(2026, 7, 31, 3, 30, tzinfo=timezone.utc)
    same_instant = datetime(2026, 7, 31, 16, 30, tzinfo=timezone.utc)

    tz_env(tz="UTC")
    key_utc = getattr(picker._display_tz(), "key", None)
    flip_utc = picker._today_local(flip_instant).isoformat()
    same_utc = picker._today_local(same_instant).isoformat()

    tz_env(tz="America/New_York")
    key_ny = getattr(picker._display_tz(), "key", None)
    flip_ny = picker._today_local(flip_instant).isoformat()
    same_ny = picker._today_local(same_instant).isoformat()

    assert (key_utc, key_ny) == ("UTC", "America/New_York"), (
        "pick 的 _display_tz() 没跟着 TZ 变 —— 时区被固化在 import 那一刻了"
        f"（{key_utc} → {key_ny}）。这正是本卡删掉的那个模块级 _DISPLAY_TZ 的病。"
    )
    assert same_utc == same_ny == "2026-07-31", f"同日锚失效（16:30Z 在两个时区都该是 07-31）：{same_utc} / {same_ny}"
    assert (flip_utc, flip_ny) == ("2026-07-31", "2026-07-30"), (
        f"归日翻转锚失效：03:30Z 在 UTC 应为 07-31、在纽约应为 07-30；"
        f"实得 {flip_utc} / {flip_ny} —— 时区名可能变了但归日还在用旧时区。"
    )
