"""CARD-G6-9a — 时区 / 午夜 / 唤醒补跑边界矩阵（零产品代码取证卡）。

本文件**不修任何东西**。它把三类此前只存在于注释与口头预期里的边界，写成可执行的门：

1. **两套时钟**（`daily_review_run.py:215-216` 的机器本地日 vs 显示口径 Asia/Shanghai）
   —— 在什么条件下它们会给出不同的"今天"。
2. **午夜跨界** —— 23:59 生成的投影在 00:01 复算时，桶归属是否仍自洽。
3. **唤醒补跑** —— 窗口外只落盘、同日第二次只补推送不重生成、隔日重新生成。
4. **Bark 失败** —— 落账字段与"投影先落盘、推送在后"的顺序。

⛔ **发现真缺陷的处置 = 如实红 + 登记不修**（卡文 (e)）。TZ 矩阵里已知会分叉的组合用
``xfail(strict=True)`` 登记：它们此刻红是**如实**，而一旦有人统一了两套时钟，
strict 会让它们 XPASS 报红，提醒把登记项转正（沿第十批 X3 的跨卡交接先例）。

⛔ 本文件禁止触发真实 launchd 档位、禁止真调 Bark、禁止写 live vault：
   所有 runner 用例都在 ``tmp_path`` 造的 vault 上跑，且 ``send_bark.send`` 必被替换。
"""

import json
import os
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

WT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WT / "scripts"))

import daily_review_pick as picker  # noqa: E402  # pyright: ignore[reportMissingImports]
import daily_review_run as runner  # noqa: E402  # pyright: ignore[reportMissingImports]

# 显示口径的**唯一来源**：从生产模块读，不在测试里另写一份字面量
# （两处各写一遍就是下一个漂移点）。
from app.api.v1.endpoints.review_overview import (  # noqa: E402
    _DISPLAY_TZ_NAME,
    _TZ_SHANGHAI,
    _gate_buckets,
    _sh_day,
)

# ══════════════════════════════════════════════════════════════════════════
# (a) 两套时钟：runner 的"今天"用机器本地时区，显示侧用 Asia/Shanghai
# ══════════════════════════════════════════════════════════════════════════

#: 参与矩阵的机器时区。含 **两个夏令时时区**（America/New_York、Europe/London）
#: 与 UTC —— 后者不是凑数：`review_overview.py:1293-1296` 明写后端容器
#: `TZ` 为空、`/etc/localtime -> Etc/UTC`，UTC 是**真实存在的部署形态**。
TZ_MATRIX = ("Asia/Shanghai", "UTC", "America/New_York", "Europe/London")

#: 参照瞬间。UTC 16:30 之后上海已跨日（+8），是暴露分叉的关键刻度；
#: 冬夏各取一组，让 DST 时区在两种偏移下都被跑到。
INSTANT_MATRIX = {
    "summer-utc0330": datetime(2026, 7, 31, 3, 30, tzinfo=timezone.utc),
    "summer-utc1630": datetime(2026, 7, 31, 16, 30, tzinfo=timezone.utc),
    "winter-utc0330": datetime(2026, 1, 15, 3, 30, tzinfo=timezone.utc),
    "winter-utc1630": datetime(2026, 1, 15, 16, 30, tzinfo=timezone.utc),
}

#: ⛔ **已登记的分叉组合**（实测值写在括号里，2026-09-06 于本机 tzdata）。
#:
#: 这份表是**硬编码字面量**，不是由被测公式现算的——期望值与被测量同源时，
#: 缺陷会让两边一起退化、断言假通过（CARD-G2-9 的 M1 就栽在这上面）。
#: 表错了就会有组合意外红/绿，那正是我们要的信号。
#:
#: 根因（`daily_review_run.py:215-216`）：
#:     local = now.astimezone()          # ← 机器本地时区
#:     today = local.date().isoformat()  # ← 它驱动 last_generate_date /
#:                                       #   last_push_accepted_date /
#:                                       #   board_last_recommended 的值
#: 而显示侧（`review_overview.py:80` `_DISPLAY_TZ_NAME`）恒按 Asia/Shanghai 归日。
#: 两者只有在机器时区 == Asia/Shanghai 时才必然一致。
KNOWN_DIVERGENT = {
    # (瞬间, 机器时区): (runner 的今天, 显示侧的今天)
    ("summer-utc0330", "America/New_York"): ("2026-07-30", "2026-07-31"),
    ("summer-utc1630", "UTC"): ("2026-07-31", "2026-08-01"),
    ("summer-utc1630", "America/New_York"): ("2026-07-31", "2026-08-01"),
    ("summer-utc1630", "Europe/London"): ("2026-07-31", "2026-08-01"),
    ("winter-utc0330", "America/New_York"): ("2026-01-14", "2026-01-15"),
    ("winter-utc1630", "UTC"): ("2026-01-15", "2026-01-16"),
    ("winter-utc1630", "America/New_York"): ("2026-01-15", "2026-01-16"),
    ("winter-utc1630", "Europe/London"): ("2026-01-15", "2026-01-16"),
}

_DIVERGENCE_CARD = "移交 CARD-G6-9c（两套时钟统一）—— 本卡零产品代码，只登记不修"


@pytest.fixture
def machine_tz():
    """临时改变**进程看到的本地时区**，teardown 无条件还原。

    ⛔ 用 ``TZ`` 环境变量 + ``time.tzset()``，而不是给 runner 传个参数——
    被测的正是 ``now.astimezone()`` 这个**无参**调用读到的东西
    （`daily_review_run.py:215`）。改传参只会测到我自己造的假；
    ``test_tz_fixture_actually_moves_the_local_clock`` 单独证明这套机制真生效。
    """
    saved = os.environ.get("TZ")

    def _set(tz_name: str) -> None:
        os.environ["TZ"] = tz_name
        time.tzset()

    try:
        yield _set
    finally:
        if saved is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = saved
        time.tzset()


def test_tz_fixture_actually_moves_the_local_clock(machine_tz):
    """机制自证：TZ 夹具确实改变了 ``astimezone()`` 的结果，不只是改了个变量。

    这条是整个 (a) 矩阵的前提。它不成立的话，下面 16 个用例测的是同一个时区，
    全绿也毫无意义（"探针条件 ≠ 真实路径"）。
    """
    instant = INSTANT_MATRIX["summer-utc1630"]
    offsets = {}
    for tz in TZ_MATRIX:
        machine_tz(tz)
        offsets[tz] = instant.astimezone().utcoffset()

    assert offsets["Asia/Shanghai"] == timedelta(hours=8)
    assert offsets["UTC"] == timedelta(0)
    # 夏令时时区在 7 月的偏移必须是夏令时那一档（NY -4 而非 -5，London +1 而非 0）
    assert offsets["America/New_York"] == timedelta(hours=-4)
    assert offsets["Europe/London"] == timedelta(hours=1)
    assert len(set(offsets.values())) == 4, f"四个时区必须给出四个不同偏移，实得 {offsets}"


def _real_runner_today(tmp_path: Path, monkeypatch, tz_name: str, instant: datetime) -> str:
    """在 tmp vault 上**真跑一次 runner**，返回它落账的 `last_generate_date`。

    ⛔ round-1 Codex HIGH-2：初版在这里自己写 `instant.astimezone().date()`——
    那是把 `daily_review_run.py:215-216` **复刻**了一遍，不是调用它。
    改 runner 的那两行，初版矩阵不会有任何反应，等于测了我自己抄的公式。
    现在走真实入口：`runner.main()` → `load_state/save_state` → 磁盘上的 state 文件。
    """
    os.environ["TZ"] = tz_name
    time.tzset()
    name = f"tz{abs(hash((tz_name, instant.isoformat()))) % 10**8}"
    vault = _vault(tmp_path, {"甲": _node_md("时区板")}, name=name)
    backups = tmp_path / f"backups-{name}"
    monkeypatch.setattr(runner, "BACKUPS", backups)
    monkeypatch.setattr(runner, "VAULT", runner.VAULT)
    monkeypatch.setattr(runner.send_bark, "send", lambda noti, vault_id=None: 0)
    monkeypatch.setattr(runner, "osascript_fallback", lambda noti: True)
    monkeypatch.setattr(
        sys,
        "argv",
        ["daily_review_run.py", "--now", instant.strftime("%Y-%m-%dT%H:%M:%SZ"), "--vault", str(vault)],
    )
    assert runner.main() == 0
    st = json.loads((backups / f"daily-review.{name}.state.json").read_text(encoding="utf-8"))
    return st["last_generate_date"]


def _display_day(instant: datetime) -> str:
    """显示侧的"今天"。两条独立换算路径互验，避免只是复述被测代码。"""
    # 路径 1：_gate_buckets 的参照时钟口径（review_overview.py:69-71）
    via_offset = (
        datetime.fromisoformat(instant.astimezone(_TZ_SHANGHAI).isoformat(timespec="seconds"))
        .astimezone(_TZ_SHANGHAI)
        .date()
        .isoformat()
    )
    # 路径 2：_sh_day 吃 UTC-Z 串（review_overview.py:340，真实生产 helper）
    via_utc_z = str(_sh_day(instant.strftime("%Y-%m-%dT%H:%M:%SZ")))
    assert via_offset == via_utc_z, f"显示侧两条换算路径自相矛盾：{via_offset} vs {via_utc_z}"
    return via_utc_z


def test_known_divergent_table_is_current(tmp_path, machine_tz, monkeypatch):
    """登记表必须与**当前实测**逐条相符；它过期了就在这里红。

    ⛔ round-1 Codex HIGH-1：初版把这条核验塞在被 xfail 的用例里，于是
    「时钟统一之后」那条用例会**先在登记核验处失败**、继续算 XFAIL ——
    `strict=True` 承诺的"修好了会报红提醒转正"永远不会发生。
    表核验必须住在**不被 xfail 的**用例里，被 xfail 的那条只留不变量断言。
    """
    measured = {}
    for instant_key, instant in INSTANT_MATRIX.items():
        display = _display_day(instant)
        for tz_name in TZ_MATRIX:
            runner_today = _real_runner_today(tmp_path, monkeypatch, tz_name, instant)
            if runner_today != display:
                measured[(instant_key, tz_name)] = (runner_today, display)

    assert measured == KNOWN_DIVERGENT, (
        "分叉登记表与实测不符。\n"
        f"  只在表里（已消失，应转正）: {sorted(set(KNOWN_DIVERGENT) - set(measured))}\n"
        f"  只在实测里（新出现，应登记）: {sorted(set(measured) - set(KNOWN_DIVERGENT))}\n"
        f"  值不同: "
        f"{ {k: (KNOWN_DIVERGENT[k], measured[k]) for k in set(KNOWN_DIVERGENT) & set(measured) if KNOWN_DIVERGENT[k] != measured[k]} }"
    )


@pytest.mark.parametrize("tz_name", TZ_MATRIX)
@pytest.mark.parametrize("instant_key", sorted(INSTANT_MATRIX))
def test_runner_today_agrees_with_display_day(request, tmp_path, machine_tz, monkeypatch, tz_name, instant_key):
    """runner **实际落账**的"今天"与显示侧的"今天"必须是同一天。

    本用例只有**一条**断言（不变量本身）。登记表的新鲜度由
    `test_known_divergent_table_is_current` 单独负责——两件事混在一起，
    `strict=True` 的 XPASS 就永远触发不了（round-1 Codex HIGH-1）。
    """
    expected = KNOWN_DIVERGENT.get((instant_key, tz_name))
    if expected is not None:
        request.node.add_marker(
            pytest.mark.xfail(
                strict=True,
                reason=(
                    f"已登记分叉：机器时区 {tz_name} 在 {instant_key} 时，"
                    f"runner 落账={expected[0]} 而显示侧={expected[1]}。"
                    f"根因 daily_review_run.py:215-216 用机器本地时区归日，"
                    f"显示侧恒用 {_DISPLAY_TZ_NAME}。{_DIVERGENCE_CARD}"
                ),
            )
        )

    instant = INSTANT_MATRIX[instant_key]
    runner_today = _real_runner_today(tmp_path, monkeypatch, tz_name, instant)
    display_day = _display_day(instant)

    assert runner_today == display_day, (
        f"机器时区 {tz_name} 下，runner 落账的今天={runner_today} 与显示侧的今天="
        f"{display_day} 不是同一天（瞬间 {instant.isoformat()}）"
    )


def test_launchd_path_does_not_force_display_tz():
    """⛔ **本卡的核心发现**：两条写路径对时区的处置是**非对称**的。

    - **web refresh 路径**：`review_overview.py:1317` `env["TZ"] = _DISPLAY_TZ_NAME`
      —— 强制，注释（:1273、:1291-1305）写明"不接受透传"，并附实测
      "TZ=Asia/Shanghai → date=2026-08-31，TZ=UTC → date=2026-08-30，同一时刻同一个库"。
    - **launchd runner 路径**：wrapper 只 export PATH / HOME / LANG，plist 的
      `EnvironmentVariables` 只有 PATH —— **没有任何一处钉住 TZ**，runner 因此
      继承宿主 `/etc/localtime`。

    ⚠️ **结论边界（round-1 Codex MEDIUM-4 收窄）**：本门证明的是
    「**本 checkout 的这两份资产**未显式设置 TZ」。它**不能**证明"整条已部署链
    没有任何 TZ 固定"——plist 指向的是**已安装**的 wrapper（可能与仓内副本不同），
    而仓内 wrapper 还会调用另一个 worktree 的 `daily-review-push.sh`；这些实际执行
    对象**不在本门的读取面内**。"宿主时区一旦变 runner 会静默产出错日期"这句，
    是由"这两份资产没设 TZ"推出的**结构论证**，不是在真实部署链上跑出来的。

    本用例把这个非对称性钉成门：**它现在是绿的**（如实反映"launchd 路径确实没设 TZ"），
    哪天有人给 wrapper/plist 补上 TZ，它会翻红提醒把这条登记项转正。
    """
    wrapper = WT / "scripts" / "launchd" / "daily-review-wrapper.sh"
    plist = WT / "scripts" / "launchd" / "com.canvas.daily-review.plist"
    assert wrapper.exists() and plist.exists(), "launchd 资产缺失，本门失去被测对象"

    wrapper_text = wrapper.read_text(encoding="utf-8")
    plist_text = plist.read_text(encoding="utf-8")

    # 先证明"能读到该读的东西"，否则下面的"没找到"分不清是缺陷还是读错了文件
    assert "export PATH=" in wrapper_text, "wrapper 里连 PATH 都没读到，锚点错了"
    assert "<key>EnvironmentVariables</key>" in plist_text, "plist 锚点错了"

    forces_tz = ("TZ=" in wrapper_text) or ("<key>TZ</key>" in plist_text)
    assert not forces_tz, (
        "launchd 路径开始强制 TZ 了 —— 这是好事，但意味着本卡登记的非对称性已被消除，"
        f"请把 KNOWN_DIVERGENT 与 {_DIVERGENCE_CARD} 一并转正"
    )

    # 对照面：web 路径确实强制了（证明"强制"这件事在本仓有先例，不是我臆想的形态）
    overview = (WT / "backend" / "app" / "api" / "v1" / "endpoints" / "review_overview.py").read_text(encoding="utf-8")
    assert 'env["TZ"] = _DISPLAY_TZ_NAME' in overview, (
        "web refresh 路径的 TZ 强制不见了 —— 非对称性的另一半没了，本门的论证前提失效"
    )


# ══════════════════════════════════════════════════════════════════════════
# 共用 fixture（形态沿 test_daily_review_run.py:36 / :47，按卡文要求落在本文件）
# ══════════════════════════════════════════════════════════════════════════

#: 上海时区的午夜前后两个参照时刻（UTC 15:59Z = 上海 23:59；16:01Z = 次日 00:01）
SH_2359 = datetime(2026, 7, 31, 15, 59, tzinfo=timezone.utc)
SH_0001 = datetime(2026, 7, 31, 16, 1, tzinfo=timezone.utc)

#: 跨午夜的两颗节点：甲在上海 7/31 23:50 到期（当日）、乙在上海 8/1 00:30 到期（次日）
DUE_BEFORE_MIDNIGHT = "2026-07-31T15:50:00Z"  # 上海 2026-07-31 23:50
DUE_AFTER_MIDNIGHT = "2026-07-31T16:30:00Z"  # 上海 2026-08-01 00:30


def _node_md(board: str, fsrs_due: str = "") -> str:
    extra = f"fsrs_due: {fsrs_due}\n" if fsrs_due else ""
    return f'---\ntype: concept\nsource_board: "[[原白板/{board}]]"\n{extra}---\n真实内容。\n'


def _vault(tmp_path: Path, nodes: dict, name: str = "vault") -> Path:
    """真目录 + 真文件（形态沿 test_daily_review_run.py:36）。"""
    vault = tmp_path / name
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)
    for fname, content in nodes.items():
        (vault / "节点" / f"{fname}.md").write_text(content, encoding="utf-8")
    return vault


@pytest.fixture
def runner_env(tmp_path, monkeypatch):
    """把 runner 的两个落盘常量都指进 tmp，并**强制**替换掉 Bark 发送。

    ⛔ `send_bark.send` 必须先换掉再跑任何 `runner.main()`：真调它会向手机发推。
    本 fixture 把替换和 VAULT/BACKUPS 重定向绑在一起交付，避免"某个用例忘了换"。
    """
    sent: list[tuple] = []
    monkeypatch.setattr(runner, "BACKUPS", tmp_path / "backups")
    # runner.main 会改写模块全局 VAULT —— 先登记原值，teardown 恢复（C1a M1）
    monkeypatch.setattr(runner, "VAULT", runner.VAULT)
    monkeypatch.setattr(runner.send_bark, "send", lambda noti, vault_id=None: sent.append((noti["id"], vault_id)) or 0)
    # osascript 本地兜底也会弹系统通知，一并堵掉
    monkeypatch.setattr(runner, "osascript_fallback", lambda noti: True)
    return {"sent": sent, "backups": tmp_path / "backups", "monkeypatch": monkeypatch}


def _run_runner(env, vault: Path, now_iso: str) -> int:
    env["monkeypatch"].setattr(sys, "argv", ["daily_review_run.py", "--now", now_iso, "--vault", str(vault)])
    return runner.main()


def _state(env, vault: Path) -> dict:
    return json.loads((env["backups"] / f"daily-review.{vault.name}.state.json").read_text(encoding="utf-8"))


# ══════════════════════════════════════════════════════════════════════════
# (b) 午夜跨界：23:59 生成的投影，用 00:01 复算时桶归属必须仍自洽
# ══════════════════════════════════════════════════════════════════════════


def _gate_payload(payload: dict) -> dict[str, int]:
    """按 `review_overview.py:695-714` 的调用链跑一遍桶门禁（只 import 调用，不改）。"""
    from app.api.v1.endpoints.review_overview import (
        _gate_boards_rollup,
        _gate_due_groups,
        _gate_upcoming,
    )

    groups = _gate_due_groups(payload["due_nodes"])
    up_gated = _gate_upcoming(payload["upcoming"])
    placeholder = payload["ineligible"].get("placeholder")
    _ph, _zero, future_map = _gate_boards_rollup(payload["boards"], groups, len(placeholder))
    assert future_map is not None, "boards rollup 没给出 future_map，门禁无法逐板对账"
    # 集成期适配 (BATCH-2026-09-05-第十二批 主 session): Y2-A CARD-G6-5-R 把 _gate_buckets 的返回
    # 从 dict[str,int] 改成 (counts, passed_rows) 二元组; 本门只消费 counts, 判据不变。
    counts, _rows = _gate_buckets(payload["buckets"], groups, payload["stats"], payload["generated_at"], future_map, up_gated)
    return counts


@pytest.mark.parametrize(
    "moment,label,expect_after_bucket",
    [
        (SH_2359, "上海 2026-07-31 23:59", "future"),
        (SH_0001, "上海 2026-08-01 00:01", "due_today"),
    ],
)
def test_midnight_crossing_bucket_attribution(tmp_path, machine_tz, moment, label, expect_after_bucket):
    """跨午夜时「乙」这颗节点的归属必须随上海日翻面，且门禁两次都放行。

    甲：上海 7/31 23:50 到期 —— 两个时刻都已过期（due_now）。
    乙：上海 8/1 00:30 到期 —— 23:59 时属 future（次日），00:01 时属 due_today（当日）。

    机器时区固定 Asia/Shanghai：本用例锁的是**午夜语义**，时区分叉由 (a) 段单独管，
    两件事混在一个用例里会让红了之后分不清是哪一个坏了。
    """
    machine_tz(_DISPLAY_TZ_NAME)
    vault = _vault(
        tmp_path,
        {
            "甲午夜前": _node_md("边界板", DUE_BEFORE_MIDNIGHT),
            "乙午夜后": _node_md("边界板", DUE_AFTER_MIDNIGHT),
        },
        name="vaultMidnight",
    )
    payload, _ranked = picker.build_payload(vault, moment, {}, picker.load_decay(vault))

    # 门禁必须放行——它自己会复算「due_today 与 generated_at 同一上海日、
    # future 必须晚于该日」（review_overview.py:112-115）
    counts = _gate_payload(payload)
    assert sum(counts.values()) >= 0  # 门禁跑通即已断言，counts 仅作留证

    buckets = payload["buckets"]
    where = {name: [row["node"] for row in rows] for name, rows in buckets.items() if isinstance(rows, list)}
    assert "乙午夜后" in where[expect_after_bucket], f"{label}：乙午夜后应在 {expect_after_bucket} 桶，实际分布 {where}"
    # 甲在两个时刻都已过期，恒不在未来两桶里
    assert "甲午夜前" not in where["due_today"] and "甲午夜前" not in where["future"], (
        f"{label}：甲午夜前已过期，不该出现在未来桶，实际分布 {where}"
    )
    # 参照时钟本身也要落在预期的上海日上（防"我以为它是 23:59 其实不是"）
    ref_day = datetime.fromisoformat(payload["generated_at"]).astimezone(_TZ_SHANGHAI).date()
    assert str(ref_day) == label.split()[1], f"{label}：参照时钟落在 {ref_day}"


# ══════════════════════════════════════════════════════════════════════════
# (c) 唤醒补跑：窗口外只落盘 / 同日只补推送不重生成 / 隔日重新生成
#
# 三条串成一个真实叙事（RunAtLoad 早触发 → 窗口内某档补推 → 次日首档重扫），
# 而不是三个互不相干的片段——补跑语义的要害正是**跨档的状态延续**。
# ══════════════════════════════════════════════════════════════════════════

#: 窗口是 `daily_review_run.py:40` 的 (09:05, 21:00)。这三个时刻**不 monkeypatch
#: PUSH_WINDOW**：窗口判定正是本段要测的东西，改掉它等于把被测物换成我自己的常量。
BEFORE_WINDOW = "2026-07-30T08:00:00+08:00"  # RunAtLoad 早触发
IN_WINDOW = "2026-07-30T10:00:00+08:00"  # 同日窗口内某档
NEXT_DAY = "2026-07-31T10:00:00+08:00"  # 次日首档


def test_wakeup_catchup_sequence(tmp_path, machine_tz, runner_env, capsys):
    """窗口外只落盘 → 同日窗口内补推送且不重生成 → 次日重新生成。"""
    machine_tz(_DISPLAY_TZ_NAME)
    # 无 fsrs_due = New 卡即刻到期；同时让 next_due_utc 为空，
    # 避免「越过最早未来到期点」这道门（:141-145）掺进来干扰缓存判定
    vault = _vault(tmp_path, {"甲": _node_md("补跑板")}, name="vaultCatchup")
    payload_path = vault / "outputs" / "今日复习.json"
    md_path = vault / "outputs" / "今日复习.md"

    # ── ① 窗口外（08:00 < 09:05）：只落盘，不推送 ──
    assert _run_runner(runner_env, vault, BEFORE_WINDOW) == 0
    out1 = capsys.readouterr().out
    assert "push:skip-window" in out1, f"08:00 在窗口外，应 skip-window；实得 {out1!r}"
    assert "generate:new" in out1
    assert payload_path.exists() and md_path.exists(), "窗口外也必须已落盘（:152 之后）"
    assert runner_env["sent"] == [], "窗口外不得发推"
    gen_at_1 = json.loads(payload_path.read_text(encoding="utf-8"))["generated_at"]
    mtime_1 = payload_path.stat().st_mtime

    # ── ② 同日窗口内：走缓存 + 补推送。generated_at 与 mtime 都不得变 ──
    assert _run_runner(runner_env, vault, IN_WINDOW) == 0
    out2 = capsys.readouterr().out
    assert "generate:cached" in out2, f"同日第二次应复用当日 payload；实得 {out2!r}"
    assert "push:accepted" in out2, f"窗口内应补上那次没发成的推送；实得 {out2!r}"
    gen_at_2 = json.loads(payload_path.read_text(encoding="utf-8"))["generated_at"]
    assert gen_at_2 == gen_at_1, f"「只补推送不重生成」不成立：generated_at 从 {gen_at_1} 变成了 {gen_at_2}"
    assert payload_path.stat().st_mtime == mtime_1, (
        "投影文件被重写了（mtime 变化）——即便内容相同也说明走的是重新生成而非缓存"
    )
    assert len(runner_env["sent"]) == 1, "补跑只该发一次"

    # ── ③ 次日首档：first_gen_today 翻转（:136），必须重新生成 ──
    assert _run_runner(runner_env, vault, NEXT_DAY) == 0
    out3 = capsys.readouterr().out
    assert "generate:new" in out3, f"次日必须重扫；实得 {out3!r}"
    gen_at_3 = json.loads(payload_path.read_text(encoding="utf-8"))["generated_at"]
    assert gen_at_3 != gen_at_1, "次日的 generated_at 必须是新的"
    st = _state(runner_env, vault)
    assert st["last_generate_date"] == "2026-07-31", f"落账日期应随之翻面，实得 {st['last_generate_date']}"

    # ── (4) 负向：同日内动了节点池 → 缓存必须失效重扫 ──
    # 没有这一步，(2) 的 "generate:cached" 分不清是「缓存门起作用」还是
    # 「这个分支恒返回 cached」。ensure_payload 有四道门（当日已生成 / sha 匹配 /
    # 未越过 next_due_utc / 节点池不比 payload 新，见 :136-146），(2) 只证明了
    # 四道同时放行；这一步单独把最后一道推翻，证明它确实在承重。
    payload_now = vault / "outputs" / "今日复习.json"
    newer = payload_now.stat().st_mtime + 100
    (vault / "节点" / "乙.md").write_text(_node_md("补跑板"), encoding="utf-8")
    os.utime(vault / "节点" / "乙.md", (newer, newer))
    os.utime(vault / "节点", (newer, newer))
    assert _run_runner(runner_env, vault, "2026-07-31T11:00:00+08:00") == 0
    out4 = capsys.readouterr().out
    assert "generate:new" in out4, (
        f"节点池比 payload 新时必须重扫（:146 的 mtime 门）；实得 {out4!r} —— "
        "若这里还是 cached，说明 (2) 的 cached 不足以证明缓存门在工作"
    )
    reread = json.loads(payload_now.read_text(encoding="utf-8"))
    assert "乙" in {d["node"] for d in reread["due_nodes"]}


# ══════════════════════════════════════════════════════════════════════════
# (d) Bark 失败：落账字段 + 「投影先落盘、推送在后」的顺序
# ══════════════════════════════════════════════════════════════════════════


def test_bark_failure_lands_state_and_projection_written_before_push(tmp_path, machine_tz, runner_env, capsys):
    """推送失败时：state 落 `bark-send` / `generated_push_failed`，且投影**在推送之前**已落盘。

    顺序断言不靠 mtime 比较，而是在**替身 send 里当场检查文件是否已存在**——
    那一刻就是"推送发生时"，比事后看时间戳更贴近要证的因果（推送失败不该让
    用户连今天的复习清单都拿不到）。
    """
    machine_tz(_DISPLAY_TZ_NAME)
    vault = _vault(tmp_path, {"甲": _node_md("失败板")}, name="vaultBarkFail")
    payload_path = vault / "outputs" / "今日复习.json"
    md_path = vault / "outputs" / "今日复习.md"

    seen_at_push: dict[str, object] = {}

    def _failing_send(noti, vault_id=None):
        # ⚠️ 我曾把这两行标成"结构性恒真、不承重"，**那是错的**（round-1 Codex LOW-7
        #    纠正）：`_vault()` 建的 tmp vault **不含 outputs/**，所以 exists() 起始为
        #    False；一旦 ensure_payload 被跳过、或推送被挪到落盘之前，它就会红。
        #    它确实承重。
        seen_at_push["json_exists"] = payload_path.exists()
        seen_at_push["md_exists"] = md_path.exists()
        # 这一行加的是**内容维度**：推送发生时投影不仅在，而且是一份可解析、
        # 含预期节点的清单。⚠️ 不声称它能验证"原子写"——同步直写只要在发送前
        # 完成，这里照样解析得通（同上，Codex LOW-7 纠正了我的过度声称）。
        try:
            doc = json.loads(payload_path.read_text(encoding="utf-8"))
            seen_at_push["parsed_nodes"] = sorted(d["node"] for d in doc["due_nodes"])
        except Exception as exc:  # noqa: BLE001 —— 半写 / 损坏都算这条门抓到
            seen_at_push["parsed_nodes"] = f"<读取失败: {type(exc).__name__}>"
        return 1  # 非 0 且非 2 → 走 :257-259 的失败落账分支

    runner_env["monkeypatch"].setattr(runner.send_bark, "send", _failing_send)

    assert _run_runner(runner_env, vault, IN_WINDOW) == 0, "推送失败不是非 0 退出（唯一非 0 是生成失败）"
    out = capsys.readouterr().out
    assert "push:failed" in out, f"rc=1 应记 failed；实得 {out!r}"

    assert seen_at_push["json_exists"] is True and seen_at_push["md_exists"] is True
    assert seen_at_push["parsed_nodes"] == ["甲"], (
        f"推送发生时投影不是一份完整可解析的清单：{seen_at_push} —— "
        "「推送失败也不该让用户拿不到今天的清单」这条承诺不成立"
    )

    # 推送失败之后投影**仍在盘上**且内容未被回滚（若有人加了失败清理，这条会红）
    after = json.loads(payload_path.read_text(encoding="utf-8"))
    assert sorted(d["node"] for d in after["due_nodes"]) == ["甲"]
    assert md_path.read_text(encoding="utf-8").strip(), "md 在推送失败后变空了"

    st = _state(runner_env, vault)
    assert st["last_error"] == "bark-send", f"实得 last_error={st.get('last_error')!r}"
    assert st["last_result"] == "generated_push_failed", f"实得 last_result={st.get('last_result')!r}"
    assert "last_push_accepted_date" not in st or st["last_push_accepted_date"] != "2026-07-30", (
        "推送失败却落了 accepted 日期 —— 次档的幂等重试会被误判成已推"
    )


def test_push_failure_is_invisible_to_backend_app():
    """⛔ 登记（不修）：`backend/app` 的 Python 文件里，runner 的四个推送落账专属键**零引用**。

    上一条证明了推送失败会落进 runner 的 state 文件。本条扫描 `backend/app`，
    确认没有任何 Python 文件提到那四个键。

    ⚠️ **结论边界（round-1 Codex MEDIUM-5 收窄）**：本门证明的是
    「**这四个字面量**在 `backend/app/**/*.py` 中零引用」。它**不能**替代行为证据
    证明"UI / 响应体完全不可见"——通用的 state 透传、字段别名、或扫描面之外
    （前端、模板、其它服务）的消费都不受本门约束。
    "用户在页面上看不出今天这条提醒没发出去"是由此**推断**的，不是端到端验证的。

    徽标交付移交 **CARD-G6-9b**（本批不排）。本门的价值在于：哪天有人把这些键
    接进 `backend/app`，它会翻红提醒把登记项转正。
    """
    # ⛔ 判据的匹配面不能比消费面宽：初版把裸 `last_error` 也算进来，结果命中了
    #    provider_factory / gemini_client / lancedb_index_service 里三个**同名局部
    #    变量**（LLM 重试循环的 `last_error: Optional[Exception]`），与 runner 的
    #    state 毫无关系。这里只认 **runner 专属**的标识：这些串在本仓只可能来自
    #    daily_review_run 的落账契约。
    RUNNER_ONLY_KEYS = (
        "generated_push_failed",  # runner:258 的 last_result 取值
        "last_push_accepted_date",  # runner:246 的推送去重键
        "last_push_kind",  # runner:250 的语义账
        "last_local_notify_date",  # runner:273 的本地兜底去重
        # ⚠️ 刻意**不**把 state 文件名 "daily-review." 放进来：它在
        #    review_overview.py:1458 有一处命中，而那是一句说"**不碰**
        #    backups/daily-review.*.state.json"的注释——一句否定陈述里当然含有
        #    被否定的那个串。把它当命中就是第二次把匹配面写得比消费面宽
        #    （第一次是裸 last_error 命中了三个同名局部变量）。
        #    这条改由下面的正面佐证断言承担。
    )
    app_dir = WT / "backend" / "app"
    hits = []
    for path in app_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for key in RUNNER_ONLY_KEYS:
            if key in text:
                hits.append(f"{path.relative_to(WT)}:{key}")
    assert hits == [], (
        f"backend/app 开始消费 runner 的推送落账字段了：{hits} —— "
        "这是好事，但意味着 CARD-G6-9b 的前提已变，请把登记项转正"
    )

    # 验伪锚：同样的扫描方式在 **runner 自己** 身上必须命中，否则"零命中"
    # 分不清是"确实没人消费"还是"我扫错了地方 / 关键词已过期"。
    runner_src = (WT / "scripts" / "daily_review_run.py").read_text(encoding="utf-8")
    missing = [k for k in RUNNER_ONLY_KEYS if k not in runner_src]
    assert missing == [], f"这些关键词在 runner 里都找不到，说明它们已过期：{missing}"

    # 正面佐证：端点自己写明了"不碰 state 文件"。它与上面的零命中互相独立——
    # 一个是"扫不到消费代码"，一个是"作者明确声明过不消费"。
    overview = (WT / "backend" / "app" / "api" / "v1" / "endpoints" / "review_overview.py").read_text(encoding="utf-8")
    assert "backups/daily-review.*.state.json" in overview, (
        "端点里那句「不碰 state 文件」的声明不见了 —— 零命中失去了它的佐证"
    )
