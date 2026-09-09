"""daily_review_run 当天重学卡刷新 (CARD-A3, BATCH-2026-08-24-复习闭环)。

ensure_payload 缓存失效三场景锁定: 当天已生成后, 节点池比 payload 新
(quiz 写侧刚更新 fsrs_due / 新增节点) 必须重扫; 无变动仍复用; 重扫后
同日推送去重 (skip-done) 与 tie-break 语义 (board_last_recommended
每天只在第一个非空榜首落账一次, CARD-D2a) 不被破坏。

只 assert dict / 状态 / runner 状态行, 不 assert 今日复习.md 渲染文本
(与 A2 渲染层解耦)。mtime 全部 os.utime 显式钉死, 不依赖墙钟顺序。
"""

import errno
import fcntl
import hashlib
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, time as dtime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

WT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WT / "scripts"))

import daily_review_pick as picker  # noqa: E402  # pyright: ignore[reportMissingImports]
import daily_review_run as runner  # noqa: E402  # pyright: ignore[reportMissingImports]

#: 本文件全部 --now 与期望值都按 +08:00 写死 (窗口判定、通知 id、落账日期),
#: 故把两侧时钟都钉在同一个字面量上 —— 见 _pin_display_tz。
_FIXED_TZ_NAME = "Asia/Shanghai"


@pytest.fixture(autouse=True)
def _pin_display_tz(monkeypatch):
    """把 runner 与 picker 两侧的时钟都钉在 Asia/Shanghai (CARD-G6-9c)。

    本文件的 `--now` 一律写成 `2026-07-30T10:00:00+08:00` 这类 +08:00 字面量,
    而期望值 (PUSH_WINDOW 09:05-21:00 的窗口判定、通知 id `canvas-review-<date>`、
    state 的 last_generate_date) 全按上海日算。宿主时区一变, 同一个 `--now`
    在本地就是别的钟点 —— 洛杉矶下它是前一天 19:00, 直接落到窗口外。

    ⚠️ **这不是本卡引入的**: da690bf8 上 runner 用裸 `now.astimezone()`(机器本地),
    在 LA 态下同样红这 4 条 (基线对照见 evidence-g69c/la-red-attribution-full.txt)。
    本卡把两侧收敛到同一来源后, 一个夹具就能同时钉住 —— **期望值一字未动**。

    两侧形态不同, 钉法也不同:
      · runner 每次现调 `local_tz.display_tz()` ⇒ setenv CANVAS_TZ 即可;
      · picker 用**模块级常量** `_DISPLAY_TZ`(import 时固化) ⇒ 必须 setattr。
    """
    monkeypatch.setenv("CANVAS_TZ", _FIXED_TZ_NAME)
    monkeypatch.setattr(picker, "_DISPLAY_TZ", ZoneInfo(_FIXED_TZ_NAME))


NOW = datetime(2026, 7, 30, 2, 0, tzinfo=timezone.utc)
TODAY = "2026-07-30"
BASE = 1_700_000_000  # 人工 mtime 基准: 只比大小, 绝对值无意义


def _node(board="普通板", extra=""):
    return f'---\ntype: concept\nsource_board: "[[原白板/{board}]]"\n{extra}---\n真实内容。\n'


def _vault(tmp_path, nodes: dict, name: str = "vault") -> Path:
    vault = tmp_path / name
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)
    for fname, content in nodes.items():
        (vault / "节点" / f"{fname}.md").write_text(content, encoding="utf-8")
    return vault


def _patch_runner(monkeypatch, vault, tmp_path):
    """CARD-C1a: STATE/LOG 常量已函数化为 BACKUPS 派生 (state_path/log_line),
    fixture 只注入 BACKUPS 一处 — 所有 state/log 写入随之进 tmp, 防写真实
    backups/。逐用例检查: 本文件所有落盘路径均经 VAULT (tmp) 或 BACKUPS (tmp)。"""
    monkeypatch.setattr(runner, "VAULT", vault)
    monkeypatch.setattr(runner, "BACKUPS", tmp_path / "backups")


def _set_mtime(path: Path, ts: float):
    os.utime(path, (ts, ts))


def _pin_pool_older_than_payload(vault: Path, payload_ts: float):
    """把 节点/ 目录与现有节点文件全部钉到 payload 之前 (无变动基线)。"""
    for p in (vault / "节点").glob("*.md"):
        _set_mtime(p, payload_ts - 100)
    _set_mtime(vault / "节点", payload_ts - 100)
    _set_mtime(vault / "outputs" / "今日复习.json", payload_ts)


# ── 场景 1: 节点变动 → 同日缓存失效, 重扫结果含该节点 ──


def test_node_change_invalidates_same_day_cache(tmp_path, monkeypatch):
    vault = _vault(tmp_path, {"甲": _node()})
    _patch_runner(monkeypatch, vault, tmp_path)
    st = runner.load_state()
    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
    assert gen1 == "new"
    assert {d["node"] for d in payload1["due_nodes"]} == {"甲"}

    # 写侧模拟: 当天考完甲后新增重学卡乙 (新卡无 fsrs_due = 即刻到期)
    (vault / "节点" / "乙.md").write_text(_node(), encoding="utf-8")
    _pin_pool_older_than_payload(vault, BASE)
    _set_mtime(vault / "节点" / "乙.md", BASE + 200)
    _set_mtime(vault / "节点", BASE + 200)

    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
    assert gen2 == "new", "节点池比 payload 新时必须重扫, 不得整日复用早晨快照"
    assert "乙" in {d["node"] for d in payload2["due_nodes"]}
    assert payload2["schema_version"] == 3  # 只消费 A2 的 v3, 不改 schema


# ── 场景 2: 无变动 → 仍走缓存 (每小时触发不得变成每小时全量重扫) ──


def test_unchanged_pool_still_cached(tmp_path, monkeypatch):
    vault = _vault(tmp_path, {"甲": _node()})
    _patch_runner(monkeypatch, vault, tmp_path)
    st = runner.load_state()
    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
    assert gen1 == "new"

    _pin_pool_older_than_payload(vault, BASE)

    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
    assert gen2 == "cached"
    assert payload2 == payload1  # 复用的是同一份落盘 payload


# ── 场景 3: 重扫后同日推送仍 skip-done (Bark 同 id 去重门不被重扫击穿) ──


def test_rescan_keeps_same_day_push_skip_done(tmp_path, monkeypatch, capsys):
    vault = _vault(tmp_path, {"甲": _node()})
    _patch_runner(monkeypatch, vault, tmp_path)
    now_arg = "2026-07-30T10:00:00+08:00"
    # today 按 runner 同一变换推导: skip-done 门在窗口门之前。
    # ⛔ 不能用裸 astimezone()(机器本地) —— CARD-G6-9c 起 runner 归日走
    #    display_tz(), 由 _pin_display_tz 夹具钉在 _FIXED_TZ_NAME 上。
    today = datetime.fromisoformat(now_arg).astimezone(ZoneInfo(_FIXED_TZ_NAME)).date().isoformat()

    st = runner.load_state()
    _, gen1 = runner.ensure_payload(st, datetime.fromisoformat(now_arg), today)
    assert gen1 == "new"
    st["last_push_accepted_date"] = today  # 早晨那次推送已被服务端接受
    runner.save_state(st)

    (vault / "节点" / "乙.md").write_text(_node(), encoding="utf-8")
    _pin_pool_older_than_payload(vault, BASE)
    _set_mtime(vault / "节点" / "乙.md", BASE + 200)
    _set_mtime(vault / "节点", BASE + 200)

    # 哨兵而非 mock: 该路径下 send 被调用即测试失败 (同日去重门失守)
    def _sentinel(noti):
        raise AssertionError("同日已推送后, 重扫不得再次触发 Bark 发送")

    monkeypatch.setattr(runner.send_bark, "send", _sentinel)
    monkeypatch.setattr(
        sys,
        "argv",
        ["daily_review_run.py", "--now", now_arg, "--vault", str(vault)],
    )
    assert runner.main() == 0
    out = capsys.readouterr().out
    assert "generate:new" in out, "重扫必须真的发生 (否则本场景空转)"
    assert "push:skip-done" in out

    st2 = runner.load_state()
    assert st2["last_push_accepted_date"] == today
    assert st2["last_generate_date"] == today


# ── 内审 HIGH (mutation 缺口): 两条 mtime 失效通道各自单独锁定 ──
# 场景 1/3 同时钉文件+目录 mtime, 任一通道被删测试仍绿; 以下两测各锁一半。


def test_infile_update_alone_triggers_rescan(tmp_path, monkeypatch):
    """只有文件 mtime 变、目录 mtime 钉旧 (APFS 原地更新 fsrs_due 的
    真实形态 — quiz 写侧头号生产场景) 也必须失效缓存。"""
    vault = _vault(tmp_path, {"甲": _node()})
    _patch_runner(monkeypatch, vault, tmp_path)
    st = runner.load_state()
    _, gen1 = runner.ensure_payload(st, NOW, TODAY)
    assert gen1 == "new"

    _pin_pool_older_than_payload(vault, BASE)
    _set_mtime(vault / "节点" / "甲.md", BASE + 200)  # 只 bump 文件, 目录不动

    _, gen2 = runner.ensure_payload(st, NOW, TODAY)
    assert gen2 == "new", "原地更新节点内容 (目录 mtime 不变) 必须触发重扫"


def test_deletion_via_dir_mtime_triggers_rescan(tmp_path, monkeypatch):
    """删除节点不留文件 mtime、只改目录 mtime, 也必须失效缓存,
    且被删节点从投影消失 (否则被删节点整天霸占推荐)。"""
    vault = _vault(tmp_path, {"甲": _node(), "乙": _node()})
    _patch_runner(monkeypatch, vault, tmp_path)
    st = runner.load_state()
    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
    assert gen1 == "new"
    assert {d["node"] for d in payload1["due_nodes"]} == {"甲", "乙"}

    (vault / "节点" / "乙.md").unlink()
    _pin_pool_older_than_payload(vault, BASE)
    _set_mtime(vault / "节点", BASE + 200)  # 只 bump 目录 (删除的真实形态)

    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
    assert gen2 == "new"
    assert {d["node"] for d in payload2["due_nodes"]} == {"甲"}


# ── 内审 MEDIUM (实测复现): 扫描-落盘窗口内的写侧更新不得整天丢失 ──


def test_write_during_scan_window_not_lost(tmp_path, monkeypatch):
    """写侧恰在扫描完成后、payload 落盘前落地一张重学卡: 该卡 mtime 早于
    payload 落盘时刻, 若以落盘时刻为基准则整天 cached 丢卡。基准必须是
    扫描起点。真实 build_payload 照常执行, 仅在其返回后注入竞态写入。"""
    vault = _vault(tmp_path, {"甲": _node()})
    _patch_runner(monkeypatch, vault, tmp_path)
    st = runner.load_state()

    import daily_review_pick as picker  # pyright: ignore[reportMissingImports]

    real_build = picker.build_payload
    fired = []

    def _race_build(*args, **kwargs):
        result = real_build(*args, **kwargs)
        if not fired:  # 只在首轮注入一次
            fired.append(1)
            (vault / "节点" / "竞态.md").write_text(_node(), encoding="utf-8")
        return result

    monkeypatch.setattr(picker, "build_payload", _race_build)
    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
    assert gen1 == "new"
    assert "竞态" not in {d["node"] for d in payload1["due_nodes"]}  # 首轮扫描没看到它

    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
    assert gen2 == "new", "竞态窗口内落地的节点必须在下一轮触发重扫, 不得整天 cached"
    assert "竞态" in {d["node"] for d in payload2["due_nodes"]}


# ── Codex BLOCKER: 时间推进跨过未来 fsrs_due 也必须失效缓存 ──
# 复现链: 09:59 写侧落 fsrs_due=10:09 → 10:05 mtime 重扫 (未到期, 空清单)
# → 11:05 已到期但节点池没再变 → 若只看 mtime 则整天 cached, 当天到期卡
# 丢失 — 恰是卡片档案 :89 警告的「缺陷位移」。


def test_time_crossing_future_due_invalidates_cache(tmp_path, monkeypatch):
    vault = _vault(
        tmp_path,
        {"重学卡": _node(extra="fsrs_due: 2026-07-30T02:30:00Z\n")},
    )
    _patch_runner(monkeypatch, vault, tmp_path)
    st = runner.load_state()

    # 02:00 生成: 卡 02:30 才到期, 清单为空 (upcoming 记录了未来到期)
    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
    assert gen1 == "new" and payload1["due_nodes"] == []

    _pin_pool_older_than_payload(vault, BASE)

    # 03:05 (跨过 02:30, 节点池零变动): 必须重扫, 到期卡进清单
    later = datetime(2026, 7, 30, 3, 5, tzinfo=timezone.utc)
    payload2, gen2 = runner.ensure_payload(st, later, TODAY)
    assert gen2 == "new", "时间越过未来到期点必须失效缓存, 不得因节点未变而整天 cached"
    assert {d["node"] for d in payload2["due_nodes"]} == {"重学卡"}

    # 03:06 再跑: 已无未来到期点、池未变 → 回到正常缓存 (不得退化成每轮全扫)
    _pin_pool_older_than_payload(vault, BASE)
    _, gen3 = runner.ensure_payload(st, datetime(2026, 7, 30, 3, 6, tzinfo=timezone.utc), TODAY)
    assert gen3 == "cached"


# ── Codex MEDIUM: plist 12 档 (Hour,Minute) 契约整体锁定 (Hour 计数太弱) ──


def test_plist_hourly_slots_inside_push_window():
    with open(WT / "scripts" / "launchd" / "com.canvas.daily-review.plist", "rb") as f:
        plist = plistlib.load(f)
    slots = plist["StartCalendarInterval"]
    assert slots == [{"Hour": h, "Minute": 5} for h in range(9, 21)]  # 9:05–20:05 共 12 档
    lo, hi = runner.PUSH_WINDOW
    for s in slots:
        assert lo <= dtime(s["Hour"], s["Minute"]) < hi  # 全部落在推送窗内


# ── tie-break 守卫: 当天已落账后, 重扫不补写 board_last_recommended ──


def test_rescan_does_not_touch_board_last_recommended(tmp_path, monkeypatch):
    vault = _vault(tmp_path, {"a甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    st = runner.load_state()
    _, gen1 = runner.ensure_payload(st, NOW, TODAY)
    assert gen1 == "new"
    assert st["board_last_recommended"] == {"A板": TODAY}

    # 新增 B 板节点后重扫: 同分 tie-break 下 B 板 (从未被推荐) 会登顶
    (vault / "节点" / "b乙.md").write_text(_node(board="B板"), encoding="utf-8")
    _pin_pool_older_than_payload(vault, BASE)
    _set_mtime(vault / "节点" / "b乙.md", BASE + 200)
    _set_mtime(vault / "节点", BASE + 200)

    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
    assert gen2 == "new"
    assert payload2["top_boards"][0]["board"] == "B板"
    # 核心: 重扫换榜也不得把 B板 标成「今天推荐过」— 当天的账已记在 A板
    assert st["board_last_recommended"] == {"A板": TODAY}


# ── CARD-D2a (BATCH-2026-08-27-Anki化与诚实收尾): 空首扫日轮转账修复 ──
# 实测缺陷链: 首扫为空 (休息日/纯空 vault) 时 first_gen_today 已被消耗,
# 同日重扫出的第一个非空榜首永远不落账 → board_last_recommended 全程 {},
# tie-break 第 2 键把空串当「从未推荐」排最前 → 启动期并列时同板霸榜。


def test_rest_day_first_nonempty_top_gets_credit(tmp_path, monkeypatch):
    """休息日形态: 首扫全员未来到期 (榜空) 不落账; 时间跨过到期点后重扫出的
    当天第一个非空榜首必须落账; 同日再重扫换榜不得二次落账 (每天只一次)。"""
    due_extra = "fsrs_due: 2026-07-30T02:30:00Z\n"
    vault = _vault(tmp_path, {"重学卡": _node(board="A板", extra=due_extra)})
    _patch_runner(monkeypatch, vault, tmp_path)
    st = runner.load_state()

    # 02:00 首扫: 卡 02:30 才到期 → 榜空 (休息日形态), 不落账
    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
    assert gen1 == "new" and payload1["top_boards"] == []
    assert st["board_last_recommended"] == {}

    # 03:05 跨过到期点重扫: 当天第一个非空榜首 → 必须落账
    _pin_pool_older_than_payload(vault, BASE)
    later = datetime(2026, 7, 30, 3, 5, tzinfo=timezone.utc)
    payload2, gen2 = runner.ensure_payload(st, later, TODAY)
    assert gen2 == "new"
    assert payload2["top_boards"][0]["board"] == "A板"
    assert st["board_last_recommended"] == {"A板": TODAY}, (
        "空首扫日的第一个非空榜首必须获得轮转账, 否则 tie-break 永远视其从未推荐"
    )
    # Codex-D2a L1: 落账必须已随 save_state 落盘 (跨进程持久化), 第三段
    # 从磁盘重载 state 继续 — 「赋值挪到 save 之后」类回归在此现形
    on_disk = json.loads(runner.state_path().read_text(encoding="utf-8"))
    assert on_disk["board_last_recommended"] == {"A板": TODAY}
    assert on_disk["last_recommend_credit_date"] == TODAY
    st = runner.load_state()

    # 同日再重扫: 同形 B板 节点 (pick 相同) 靠 tie-break 登顶, 也不得补账
    (vault / "节点" / "b乙.md").write_text(_node(board="B板", extra=due_extra), encoding="utf-8")
    _pin_pool_older_than_payload(vault, BASE)
    _set_mtime(vault / "节点" / "b乙.md", BASE + 200)
    _set_mtime(vault / "节点", BASE + 200)
    payload3, gen3 = runner.ensure_payload(st, later, TODAY)
    assert gen3 == "new"
    assert payload3["top_boards"][0]["board"] == "B板"
    assert st["board_last_recommended"] == {"A板": TODAY}, "当日已落账后, 重扫换榜不得把第二个板标成「今天推荐过」"


def test_legacy_state_credited_today_without_marker_not_double_credited(tmp_path, monkeypatch):
    """升级当天兼容 (Codex-D2a H1): 旧版 runner 已在今天落账 (值=today) 但
    state 自然缺 last_recommend_credit_date — 同日换榜重扫不得再次落账,
    否则 A、B 同日均标 today, 突破每日一次上界并污染 tie-break。"""
    vault = _vault(tmp_path, {"a甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    st = runner.load_state()
    _, gen1 = runner.ensure_payload(st, NOW, TODAY)
    assert gen1 == "new"
    assert st["board_last_recommended"] == {"A板": TODAY}
    # 模拟旧版 runner 留下的 state: 当日已落账、自然缺新 marker
    del st["last_recommend_credit_date"]
    runner.save_state(st)
    st = runner.load_state()

    (vault / "节点" / "b乙.md").write_text(_node(board="B板"), encoding="utf-8")
    _pin_pool_older_than_payload(vault, BASE)
    _set_mtime(vault / "节点" / "b乙.md", BASE + 200)
    _set_mtime(vault / "节点", BASE + 200)
    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
    assert gen2 == "new"
    assert payload2["top_boards"][0]["board"] == "B板"
    assert st["board_last_recommended"] == {"A板": TODAY}, (
        "旧 state 无 marker 但值已含 today — 视为当日已落账, 不得给 B 补账"
    )


def test_empty_vault_first_scan_then_new_node_gets_credit(tmp_path, monkeypatch):
    """纯空形态: 空 vault 首扫 (无通知) 不落账; 同日新增真板节点后重扫,
    该榜首必须落账 — 不得因「今天已首扫过」而整天欠账。"""
    vault = _vault(tmp_path, {})
    _patch_runner(monkeypatch, vault, tmp_path)
    st = runner.load_state()

    payload1, gen1 = runner.ensure_payload(st, NOW, TODAY)
    assert gen1 == "new" and payload1["notification"] is None
    assert st["board_last_recommended"] == {}

    (vault / "节点" / "甲.md").write_text(_node(board="真板"), encoding="utf-8")
    _pin_pool_older_than_payload(vault, BASE)
    _set_mtime(vault / "节点" / "甲.md", BASE + 200)
    _set_mtime(vault / "节点", BASE + 200)
    payload2, gen2 = runner.ensure_payload(st, NOW, TODAY)
    assert gen2 == "new"
    assert payload2["top_boards"][0]["board"] == "真板"
    assert st["board_last_recommended"] == {"真板": TODAY}


# ── CARD-C1a (BATCH-2026-08-25-跨vault与收束): 多 vault 命名空间隔离 ──


def test_two_vaults_same_day_push_and_state_isolated(tmp_path, monkeypatch, capsys):
    """全局单例根缺陷的修复锁定: vault A 当日推送后, vault B 同日必须仍能
    推送 (旧 last_push_accepted_date 全局 → B 永远 skip-done); 两个 state
    文件独立; 互跑后各自缓存门仍 cached (旧 payload_sha256 单值 → 乒乓失效)。

    已知局限: 本测两库跑在同一 Python 进程, 证明的是 state 隔离, 不证明
    生产「一库一进程」契约 — 后者由 wrapper shell 层循环保证 (进程内复用
    会踩 pick.load_decay 的 decay_beta import 缓存, 见 wrapper 注释)。"""
    vault_a = _vault(tmp_path, {"甲": _node()}, name="vaultA")
    vault_b = _vault(tmp_path, {"乙": _node()}, name="vaultB")
    monkeypatch.setattr(runner, "BACKUPS", tmp_path / "backups")
    # runner.main 会改写模块全局 VAULT — 先经 monkeypatch 登记原值,
    # teardown 恢复, 防测试顺序依赖 (Codex-C1a M1)
    monkeypatch.setattr(runner, "VAULT", runner.VAULT)
    # 窗口门放行 (机器时区无关): 本测锁 state 隔离, 不锁窗口语义
    monkeypatch.setattr(runner, "PUSH_WINDOW", (dtime(0, 0), dtime(23, 59, 59)))
    sent = []
    monkeypatch.setattr(
        runner.send_bark,
        "send",
        lambda noti, vault_id=None: sent.append((noti["id"], vault_id)) or 0,
    )
    now_arg = "2026-07-30T10:00:00+08:00"

    def _run(vault) -> str:
        monkeypatch.setattr(
            sys,
            "argv",
            ["daily_review_run.py", "--now", now_arg, "--vault", str(vault)],
        )
        assert runner.main() == 0
        return capsys.readouterr().out

    out_a = _run(vault_a)
    assert "generate:new" in out_a and "push:accepted" in out_a
    out_b = _run(vault_b)
    assert "generate:new" in out_b and "push:accepted" in out_b, (
        "vault A 推过后 vault B 同日必须仍可推送 (state 全局单例会误判 skip-done)"
    )
    # send 侧拿到的是各自 payload 的顶层 vault_id (通知 id 值本身不含 vault)
    assert [v for _, v in sent] == ["vaultA", "vaultB"]
    assert all(nid == "canvas-review-2026-07-30" for nid, _ in sent)

    state_a = tmp_path / "backups" / "daily-review.vaultA.state.json"
    state_b = tmp_path / "backups" / "daily-review.vaultB.state.json"
    assert state_a.exists() and state_b.exists(), "两个 vault 必须各有独立 state 文件"
    assert (
        json.loads(state_a.read_text(encoding="utf-8"))["last_push_accepted_date"]
        == json.loads(state_b.read_text(encoding="utf-8"))["last_push_accepted_date"]
    )

    # 互跑第二轮: 各自缓存门仍 cached + 同日去重 skip-done (乒乓失效修复)
    _pin_pool_older_than_payload(vault_a, BASE)
    _pin_pool_older_than_payload(vault_b, BASE)
    out_a2 = _run(vault_a)
    assert "generate:cached" in out_a2 and "push:skip-done" in out_a2
    out_b2 = _run(vault_b)
    assert "generate:cached" in out_b2 and "push:skip-done" in out_b2
    assert len(sent) == 2, "第二轮不得再发推送"

    log_text = (tmp_path / "backups" / "daily-review.log").read_text(encoding="utf-8")
    assert "vault=vaultA" in log_text and "vault=vaultB" in log_text


def test_payload_carries_top_level_vault_id(tmp_path, monkeypatch):
    """C1a 加性契约: payload 顶层新增 vault_id, schema_version 仍 3,
    notification.id 值不动 (A2 冻结 — send 侧才组合 vault 维度)。"""
    vault = _vault(tmp_path, {"甲": _node()}, name="vaultA")
    _patch_runner(monkeypatch, vault, tmp_path)
    st = runner.load_state()
    payload, gen = runner.ensure_payload(st, NOW, TODAY)
    assert gen == "new"
    assert payload["vault_id"] == "vaultA"
    assert payload["schema_version"] == 3
    assert payload["notification"]["id"] == f"canvas-review-{payload['date']}"
    on_disk = json.loads((vault / "outputs" / "今日复习.json").read_text(encoding="utf-8"))
    assert on_disk["vault_id"] == "vaultA"


# ── CARD-C1a: send 侧组合有效通知 id (payload.notification.id 值冻结不动) ──


def _capture_bark_request(monkeypatch, tmp_path) -> dict:
    """网络出口打桩 (仅测试进程内): 截获 send_bark 实际提交给 Bark API 的
    请求体做断言。真发 = 每次跑测试都向真机推真通知, 才是纪律违规;
    仓库既有惯例同源 (本文件场景 3 的 send 哨兵)。"""
    key_file = tmp_path / "bark.key"
    key_file.write_text("testkey-12345678\n", encoding="utf-8")
    monkeypatch.setattr(runner.send_bark, "KEY_FILE", key_file)
    captured = {}

    class _AcceptedResp:
        status = 200

        def read(self):
            return b'{"code":200}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def _capture_urlopen(req, timeout=None):
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _AcceptedResp()

    # CARD-TEST-bark-autostub: patch 模块内唯一出口缝, 不再改全局
    # urllib.request.urlopen (旧写法会波及同进程内一切 urllib 用户)
    monkeypatch.setattr(runner.send_bark, "_urlopen", _capture_urlopen)
    return captured


def test_send_bark_composes_vault_scoped_id_and_group(tmp_path, monkeypatch):
    captured = _capture_bark_request(monkeypatch, tmp_path)
    noti = {"title": "t", "body": "b", "group": "canvas复习", "id": "canvas-review-2026-07-30"}
    assert runner.send_bark.send(noti, "vaultA") == 0
    assert captured["body"]["id"] == "canvas-review-2026-07-30-vaultA"
    assert "vaultA" in captured["body"]["group"]
    # 传入 dict 不被就地改写 (payload 落盘值 = A2 冻结契约)
    assert noti["id"] == "canvas-review-2026-07-30"
    assert noti["group"] == "canvas复习"


def test_send_bark_without_vault_id_keeps_legacy_shape(tmp_path, monkeypatch):
    """迁移前旧 payload (无顶层 vault_id) 走原样 id/group — 加性兼容下界。"""
    captured = _capture_bark_request(monkeypatch, tmp_path)
    noti = {"title": "t", "body": "b", "group": "canvas复习", "id": "canvas-review-2026-07-30"}
    assert runner.send_bark.send(noti) == 0
    assert captured["body"]["id"] == "canvas-review-2026-07-30"
    assert captured["body"]["group"] == "canvas复习"


def test_vault_key_slug_rules():
    """两域设计 (Codex-C1a B2/H1): ASCII 短名原样; 非 ASCII slug+hash16;
    hash 域后缀形态的 ASCII 名强制改道 hash 域 (两域不重叠 → 「数学 的 key
    恰好被某 ASCII 目录名占用」这类直白碰撞不可构造); 超长名截断+hash,
    state 文件名恒在 NAME_MAX 内; 输出恒为文件名/通知 id 安全字符集。"""
    vault_key = runner.send_bark.vault_key
    assert vault_key("canvas-vault") == "canvas-vault"
    k1, k2 = vault_key("数学"), vault_key("物理")
    assert k1 != k2
    for k in (k1, k2):
        assert re.fullmatch(r"[0-9A-Za-z._-]+-[0-9a-f]{16}", k)
    # 域分离: 中文库的 key 本身作为目录名再进来, 必须映射到不同 key
    assert vault_key(k1) != k1
    # 超长合法目录名不得让 daily-review.<key>.state.json 超 NAME_MAX=255
    long_key = vault_key("a" * 232)
    assert len(f"daily-review.{long_key}.state.json".encode("utf-8")) <= 255
    assert long_key != vault_key("a" * 233)
    # 目录名字面精确: Unicode 空白尾巴是另一个库, 不得与裸名撞 key
    assert vault_key("foo ") != vault_key("foo")
    # 路径传入也归约到目录名 (调用方兜底)
    assert vault_key("/tmp/x/canvas-vault/") == "canvas-vault"


# ── CARD-C1a: 旧全局 state 迁移 (dry-run 零写入 / 实迁保留 .bak) ──


def _old_state_fixture(tmp_path) -> Path:
    backups = tmp_path / "backups"
    backups.mkdir()
    old = backups / "daily-review.state.json"
    old.write_text(
        json.dumps({"schema_version": 1, "last_generate_date": "2026-07-29"}, ensure_ascii=False), encoding="utf-8"
    )
    return backups


def _run_migrate(monkeypatch, argv: list[str]) -> int:
    import migrate_daily_review_state as migrate  # pyright: ignore[reportMissingImports]

    monkeypatch.setattr(sys, "argv", ["migrate_daily_review_state.py", *argv])
    return migrate.main()


def test_migrate_dry_run_writes_nothing(tmp_path, monkeypatch, capsys):
    backups = _old_state_fixture(tmp_path)
    before = sorted(p.name for p in backups.iterdir())
    rc = _run_migrate(monkeypatch, ["--vault", "canvas-vault", "--backups", str(backups), "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "daily-review.state.json" in out and "daily-review.canvas-vault.state.json" in out
    assert sorted(p.name for p in backups.iterdir()) == before, "dry-run 必须零写入"
    # Codex-C1a B3: 字面零写含 __pycache__ — 模块必须已挂 bytecode 禁写防线
    assert sys.dont_write_bytecode, "migrate 模块应设 sys.dont_write_bytecode"


def test_migrate_apply_keeps_bak_and_refuses_overwrite(tmp_path, monkeypatch, capsys):
    backups = _old_state_fixture(tmp_path)
    original = (backups / "daily-review.state.json").read_text(encoding="utf-8")
    rc = _run_migrate(monkeypatch, ["--vault", "canvas-vault", "--backups", str(backups)])
    assert rc == 0
    new = backups / "daily-review.canvas-vault.state.json"
    bak = backups / "daily-review.state.json.bak"
    assert new.read_text(encoding="utf-8") == original
    assert bak.read_text(encoding="utf-8") == original, "实迁必须保留 .bak 供回滚"
    assert not (backups / "daily-review.state.json").exists()

    # 二次实迁 (旧文件重新出现) 不得覆盖已存在的新文件
    (backups / "daily-review.state.json").write_text("{}", encoding="utf-8")
    rc2 = _run_migrate(monkeypatch, ["--vault", "canvas-vault", "--backups", str(backups)])
    assert rc2 == 1
    assert new.read_text(encoding="utf-8") == original


def test_migrate_symlink_vault_arg_matches_runner_key(tmp_path, monkeypatch):
    """经 symlink 传 --vault 时, 迁移目标文件名必须与 runner state_path 恒等
    — migrate 取字面名而 runner resolve 的话, 迁移会落到永远不被读的文件。"""
    backups = _old_state_fixture(tmp_path)
    real = _vault(tmp_path, {"甲": _node()}, name="真库")
    link = tmp_path / "alias"
    link.symlink_to(real)

    rc = _run_migrate(monkeypatch, ["--vault", str(link), "--backups", str(backups)])
    assert rc == 0
    monkeypatch.setattr(runner, "VAULT", link)
    monkeypatch.setattr(runner, "BACKUPS", backups)
    assert runner.state_path().exists(), "迁移产出的文件名必须能被 runner 读到"


def test_migrate_crlf_state_byte_identical_and_idempotent(tmp_path, monkeypatch, capsys):
    """Codex-C1a round4: CRLF 换行的合法 state 必须按字节原样迁移 (文本模式
    read_text 会洗成 LF, 令 new≠bak 击穿完成态判据), 且重跑判 '已完成'。"""
    backups = tmp_path / "backups"
    backups.mkdir()
    crlf = b'{\r\n  "schema_version": 1,\r\n  "last_generate_date": "2026-07-29"\r\n}\r\n'
    (backups / "daily-review.state.json").write_bytes(crlf)
    rc = _run_migrate(monkeypatch, ["--vault", "canvas-vault", "--backups", str(backups)])
    assert rc == 0
    new = backups / "daily-review.canvas-vault.state.json"
    assert new.read_bytes() == crlf, "迁移必须逐字节保真 (含 CRLF)"
    rc2 = _run_migrate(monkeypatch, ["--vault", "canvas-vault", "--backups", str(backups)])
    assert rc2 == 0
    assert "已完成" in capsys.readouterr().out


def test_migrate_refuses_non_dict_state(tmp_path, monkeypatch, capsys):
    """Codex-C1a B3: '[]' 是合法 JSON — migrate 结构必须校验到 dict 级,
    拒迁且零写入保数据 (runner load_state 自 D2b-M1 起对错型隔离重建
    不再当场炸, 但重建即丢账 — 迁移侧拒迁仍是第一道防线)。"""
    backups = tmp_path / "backups"
    backups.mkdir()
    (backups / "daily-review.state.json").write_text("[]", encoding="utf-8")
    rc = _run_migrate(monkeypatch, ["--vault", "canvas-vault", "--backups", str(backups)])
    assert rc == 1
    assert not (backups / "daily-review.canvas-vault.state.json").exists()
    assert not (backups / "daily-review.state.json.bak").exists()
    assert (backups / "daily-review.state.json").read_text(encoding="utf-8") == "[]"


def test_migrate_refuses_overwriting_existing_bak(tmp_path, monkeypatch):
    """Codex-C1a B3: 预置 .bak (上次回滚副本/手工备份) 不许被静默覆盖;
    拒迁后原文件与 .bak 双双原样。"""
    backups = _old_state_fixture(tmp_path)
    (backups / "daily-review.state.json.bak").write_text("旧备份", encoding="utf-8")
    rc = _run_migrate(monkeypatch, ["--vault", "canvas-vault", "--backups", str(backups)])
    assert rc == 1
    assert not (backups / "daily-review.canvas-vault.state.json").exists()
    assert (backups / "daily-review.state.json.bak").read_text(encoding="utf-8") == "旧备份"
    assert (backups / "daily-review.state.json").exists()


def test_migrate_interrupted_states_have_explicit_exits(tmp_path, monkeypatch, capsys):
    """Codex-C1a F3 状态机锁定: 仅剩 .bak (写 new 前中止) → rc1 且给出恢复
    指引, 不得谎报 '无需迁移'; new+.bak 双在 (已完成) → rc0 幂等;
    new 损坏 + .bak 在 (写入途中中止) → rc1 指引重迁。"""
    backups = tmp_path / "backups"
    backups.mkdir()
    bak = backups / "daily-review.state.json.bak"
    new = backups / "daily-review.canvas-vault.state.json"

    bak.write_text('{"schema_version": 1}', encoding="utf-8")
    rc = _run_migrate(monkeypatch, ["--vault", "canvas-vault", "--backups", str(backups)])
    assert rc == 1
    assert "恢复" in capsys.readouterr().err

    new.write_text('{"schema_version": 1}', encoding="utf-8")
    rc2 = _run_migrate(monkeypatch, ["--vault", "canvas-vault", "--backups", str(backups)])
    assert rc2 == 0
    assert "已完成" in capsys.readouterr().out

    new.write_text('{"半截', encoding="utf-8")
    rc3 = _run_migrate(monkeypatch, ["--vault", "canvas-vault", "--backups", str(backups)])
    assert rc3 == 1
    assert "重迁" in capsys.readouterr().err


def test_migrate_preplanted_symlink_target_not_overwritten(tmp_path, monkeypatch):
    """Codex-C1a F4/N1: 目标位置被预置成悬空 symlink (指向尚不存在的路径)
    时, mkstemp+rename 发布只替换链接名本身 — 内容绝不被引到 symlink 指向
    的位置落盘, 终点成为常规文件。"""
    backups = _old_state_fixture(tmp_path)
    hijack_target = tmp_path / "劫持目标.json"  # 不存在 → 悬空 symlink 过得了 exists 预检
    new = backups / "daily-review.canvas-vault.state.json"
    new.symlink_to(hijack_target)
    rc = _run_migrate(monkeypatch, ["--vault", "canvas-vault", "--backups", str(backups)])
    assert rc == 0
    assert not hijack_target.exists(), "悬空 symlink 不得被跟随, 在其目标处落文件"
    assert not new.is_symlink() and new.is_file(), "rename 应替换链接名为常规文件"
    assert json.loads(new.read_text(encoding="utf-8"))["last_generate_date"] == "2026-07-29"
    assert (backups / "daily-review.state.json.bak").exists()


# ── CARD-D2b (BATCH-2026-08-27-Anki化与诚实收尾): 休息日反转推送 (方案甲) ──
# 实测缺陷链: 09:06 休息推送 accepted → 14:06 due_crossed 重扫, payload/总览
# 页已更新, 但 last_push_accepted_date==today 门拦推送 (skip-done) → 手机
# 整天停留「今日无到期」。方案甲: 仅放行 rest→due 语义反转一次 (同 id 服务
# 端覆盖 = A4 既有契约, 通知中心不堆叠); state 持久化成立时每天推送上界
# = 2 (rest + due; accepted 后崩溃窗/损坏重建残余 = A4/A7 既有语义, 入档)。


def _push_harness(monkeypatch, tmp_path, vault, rcs):
    """main() 端到端打桩: 窗口门放行 (机器时区无关), send 按 rcs 队列返回并
    截获 (id, title) — 多余的 send 调用会越界报错 (兼当哨兵), osascript
    兜底打桩防真弹通知。"""
    _patch_runner(monkeypatch, vault, tmp_path)
    monkeypatch.setattr(runner, "PUSH_WINDOW", (dtime(0, 0), dtime(23, 59, 59)))
    calls = []

    def _send(noti, vault_id=None):
        calls.append((noti["id"], noti["title"]))
        return rcs[len(calls) - 1]

    monkeypatch.setattr(runner.send_bark, "send", _send)
    monkeypatch.setattr(runner, "osascript_fallback", lambda noti: True)
    return calls


def _run_main(monkeypatch, capsys, vault, now_arg) -> str:
    monkeypatch.setattr(sys, "argv", ["daily_review_run.py", "--now", now_arg, "--vault", str(vault)])
    assert runner.main() == 0
    return capsys.readouterr().out


def test_rest_to_due_reversal_pushes_second_time(tmp_path, monkeypatch, capsys):
    """rest→due 放行一次: 早晨休息推送后, 盘中转出到期 → 第二推放行且与
    首推同 id (服务端覆盖, 手机原地刷新); due 之后恒 skip-done (上界 2)。"""
    vault = _vault(tmp_path, {"重学卡": _node(board="A板", extra="fsrs_due: 2026-07-30T06:00:00Z\n")})
    calls = _push_harness(monkeypatch, tmp_path, vault, rcs=[0, 0])

    out1 = _run_main(monkeypatch, capsys, vault, "2026-07-30T10:00:00+08:00")  # 02:00Z
    assert "generate:new" in out1 and "push:accepted" in out1
    assert runner.load_state()["last_push_kind"] == "rest"
    assert calls[0][1] == "📚 今日无到期节点"

    _pin_pool_older_than_payload(vault, BASE)
    out2 = _run_main(monkeypatch, capsys, vault, "2026-07-30T14:05:00+08:00")  # 06:05Z 跨到期
    assert "generate:new" in out2 and "push:accepted" in out2, (
        "rest→due 语义反转必须放行第二推, 不得让手机整天停留「今日无到期」"
    )
    assert runner.load_state()["last_push_kind"] == "due"
    assert len(calls) == 2 and calls[1][1] == "📚 今日复习 · A板"
    assert calls[1][0] == calls[0][0], "两推必须同 id — 服务端覆盖而非堆叠"

    _pin_pool_older_than_payload(vault, BASE)
    out3 = _run_main(monkeypatch, capsys, vault, "2026-07-30T15:05:00+08:00")
    assert "push:skip-done" in out3
    assert len(calls) == 2, "due 之后不得再推 — 每天推送上界 = 2"


def test_due_to_due_rescan_stays_skip_done(tmp_path, monkeypatch, capsys):
    """due→due 不放行: 早晨到期推送后, 盘中重扫榜更新也 skip-done (与场景 3
    互补 — 那条锁旧 state 无 last_push_kind 的保守回退, 本条锁写入后语义)。"""
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    calls = _push_harness(monkeypatch, tmp_path, vault, rcs=[0])

    out1 = _run_main(monkeypatch, capsys, vault, "2026-07-30T10:00:00+08:00")
    assert "push:accepted" in out1
    assert runner.load_state()["last_push_kind"] == "due"

    (vault / "节点" / "乙.md").write_text(_node(board="B板"), encoding="utf-8")
    _pin_pool_older_than_payload(vault, BASE)
    _set_mtime(vault / "节点" / "乙.md", BASE + 200)
    _set_mtime(vault / "节点", BASE + 200)
    out2 = _run_main(monkeypatch, capsys, vault, "2026-07-30T14:05:00+08:00")
    assert "generate:new" in out2 and "push:skip-done" in out2
    assert len(calls) == 1
    assert runner.load_state()["last_push_kind"] == "due"


def test_rest_to_rest_rescan_stays_skip_done(tmp_path, monkeypatch, capsys):
    """rest→rest 不放行: 休息推送后重扫仍是休息日 (榜仍空) → skip-done,
    反转门只认「转出到期」这一种语义变化。"""
    vault = _vault(tmp_path, {"重学卡": _node(board="A板", extra="fsrs_due: 2026-07-30T12:00:00Z\n")})
    calls = _push_harness(monkeypatch, tmp_path, vault, rcs=[0])

    out1 = _run_main(monkeypatch, capsys, vault, "2026-07-30T10:00:00+08:00")  # 02:00Z
    assert "push:accepted" in out1
    assert runner.load_state()["last_push_kind"] == "rest"

    (vault / "节点" / "乙.md").write_text(
        _node(board="B板", extra="fsrs_due: 2026-07-30T13:00:00Z\n"), encoding="utf-8"
    )
    _pin_pool_older_than_payload(vault, BASE)
    _set_mtime(vault / "节点" / "乙.md", BASE + 200)
    _set_mtime(vault / "节点", BASE + 200)
    out2 = _run_main(monkeypatch, capsys, vault, "2026-07-30T11:05:00+08:00")  # 03:05Z 仍未到期
    assert "generate:new" in out2 and "push:skip-done" in out2
    assert len(calls) == 1
    assert runner.load_state()["last_push_kind"] == "rest"


def test_second_push_failure_retries_next_hour(tmp_path, monkeypatch, capsys):
    """二推失败幂等重试: 反转门只在 accepted 时关闭 (last_push_kind 翻 due),
    失败保持 rest → 次小时 launchd 触发自然重试; 连续失败本地兜底只弹一次
    (Codex-D2b L2); 成功后清错收口。"""
    vault = _vault(tmp_path, {"重学卡": _node(board="A板", extra="fsrs_due: 2026-07-30T06:00:00Z\n")})
    calls = _push_harness(monkeypatch, tmp_path, vault, rcs=[0, 1, 1, 0])
    fallbacks = []
    monkeypatch.setattr(runner, "osascript_fallback", lambda noti: fallbacks.append(noti["title"]) or True)
    today = datetime.fromisoformat("2026-07-30T10:00:00+08:00").astimezone(ZoneInfo(_FIXED_TZ_NAME)).date().isoformat()

    out1 = _run_main(monkeypatch, capsys, vault, "2026-07-30T10:00:00+08:00")
    assert "push:accepted" in out1

    _pin_pool_older_than_payload(vault, BASE)
    out2 = _run_main(monkeypatch, capsys, vault, "2026-07-30T14:05:00+08:00")
    assert "push:failed" in out2 and "fallback:ok" in out2
    st2 = runner.load_state()
    assert st2["last_push_kind"] == "rest", "失败不得翻 due — 否则重试门被永久关闭"
    assert st2["last_result"] == "generated_push_failed"
    assert st2["last_error"] == "bark-send"
    assert st2["last_local_notify_date"] == today
    assert fallbacks == ["📚 今日复习 · A板"]

    _pin_pool_older_than_payload(vault, BASE)
    out3 = _run_main(monkeypatch, capsys, vault, "2026-07-30T15:05:00+08:00")
    assert "push:failed" in out3 and "fallback:-" in out3, "同日本地兜底只弹一次"
    assert len(fallbacks) == 1

    _pin_pool_older_than_payload(vault, BASE)
    out4 = _run_main(monkeypatch, capsys, vault, "2026-07-30T16:05:00+08:00")
    assert "push:accepted" in out4, "次小时必须幂等重试成功"
    st4 = runner.load_state()
    assert st4["last_push_kind"] == "due"
    assert st4["last_result"] == "pushed" and st4["last_error"] == "", "成功后必须清错"
    assert [t for _, t in calls] == [
        "📚 今日无到期节点",
        "📚 今日复习 · A板",
        "📚 今日复习 · A板",
        "📚 今日复习 · A板",
    ]

    _pin_pool_older_than_payload(vault, BASE)
    out5 = _run_main(monkeypatch, capsys, vault, "2026-07-30T17:05:00+08:00")
    assert "push:skip-done" in out5
    assert len(calls) == 4


def test_rest_due_rest_due_oscillation_capped_at_two(tmp_path, monkeypatch, capsys):
    """Codex-D2b M3: 全天 rest→due→rest→due 振荡 — 第二次 accepted (due) 后
    无论语义再怎么翻转, 当日不得出现第三次发送 (rcs 越界哨兵扛门)。防
    「任意已知语义变化均放行」类回归 mutant。"""
    vault = _vault(tmp_path, {"重学卡": _node(board="A板", extra="fsrs_due: 2026-07-30T06:00:00Z\n")})
    calls = _push_harness(monkeypatch, tmp_path, vault, rcs=[0, 0])

    out1 = _run_main(monkeypatch, capsys, vault, "2026-07-30T10:00:00+08:00")
    assert "push:accepted" in out1  # rest
    _pin_pool_older_than_payload(vault, BASE)
    out2 = _run_main(monkeypatch, capsys, vault, "2026-07-30T14:05:00+08:00")
    assert "push:accepted" in out2  # due (反转放行一次)

    # 盘中考完: 卡推到明天 → 榜回空 (due→rest), 不得再推
    (vault / "节点" / "重学卡.md").write_text(
        _node(board="A板", extra="fsrs_due: 2026-07-31T06:00:00Z\n"), encoding="utf-8"
    )
    _pin_pool_older_than_payload(vault, BASE)
    _set_mtime(vault / "节点" / "重学卡.md", BASE + 200)
    _set_mtime(vault / "节点", BASE + 200)
    out3 = _run_main(monkeypatch, capsys, vault, "2026-07-30T15:05:00+08:00")
    assert "generate:new" in out3 and "push:skip-done" in out3

    # 又冒出新到期卡 (第二次 rest→due 形态) — 反转门当日只放行一次
    (vault / "节点" / "新卡.md").write_text(_node(board="B板"), encoding="utf-8")
    _pin_pool_older_than_payload(vault, BASE)
    _set_mtime(vault / "节点" / "新卡.md", BASE + 200)
    _set_mtime(vault / "节点", BASE + 200)
    out4 = _run_main(monkeypatch, capsys, vault, "2026-07-30T16:05:00+08:00")
    assert "generate:new" in out4 and "push:skip-done" in out4
    assert len(calls) == 2, "振荡日 accepted 上界 = 2 (rest + due 各一次)"


def test_structurally_corrupt_state_quarantined_not_crash(tmp_path, monkeypatch, capsys):
    """Codex-D2b M1: 合法 JSON 但结构错型的 state (顶层 [] / 账本 []) 必须
    与语法损坏同等对待 — 隔离重建不炸, 当轮照常生成+推送。已知代价 (如实
    入档): 重建即丢当日推送账, 与既有语法损坏路径同级。"""
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    calls = _push_harness(monkeypatch, tmp_path, vault, rcs=[0, 0])
    state = runner.state_path()
    state.parent.mkdir(parents=True, exist_ok=True)

    state.write_text("[]", encoding="utf-8")  # 顶层非 dict
    out1 = _run_main(monkeypatch, capsys, vault, "2026-07-30T10:00:00+08:00")
    assert "generate:new" in out1 and "push:accepted" in out1
    assert runner.load_state()["last_push_kind"] == "due"
    # Codex-D2b-r2 L2: 错型件必须隔离留档 (防「删 quarantine 直接吞档」回归)
    assert list(state.parent.glob(state.name + ".corrupt-*")), "错型 state 必须隔离留档"

    # 账本错型 (board_last_recommended 非 dict) 同样隔离重建
    state.write_text(json.dumps({"schema_version": 1, "board_last_recommended": []}), encoding="utf-8")
    out2 = _run_main(monkeypatch, capsys, vault, "2026-07-30T11:05:00+08:00")
    assert "generate:new" in out2 and "push:accepted" in out2
    assert len(calls) == 2


def test_legacy_cached_payload_without_top_boards_records_due(tmp_path, monkeypatch, capsys):
    """Codex-D2b M2: 迁移前 legacy 缓存 payload 无 top_boards 键 — 语义未知,
    accepted 落账必须保守记 due (关闭反转门), 不得记 rest 造成 due→due 二推。"""
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    calls = _push_harness(monkeypatch, tmp_path, vault, rcs=[0])
    now_arg = "2026-07-30T10:00:00+08:00"
    today = datetime.fromisoformat(now_arg).astimezone(ZoneInfo(_FIXED_TZ_NAME)).date().isoformat()

    legacy = {
        "schema_version": 3,
        "date": today,
        "notification": {
            "title": "📚 今日复习 · A板",
            "body": "b",
            "group": "canvas复习",
            "id": f"canvas-review-{today}",
        },
    }
    raw = json.dumps(legacy, ensure_ascii=False, indent=2) + "\n"
    out_dir = vault / "outputs"
    out_dir.mkdir(parents=True)
    (out_dir / "今日复习.json").write_text(raw, encoding="utf-8")
    st = runner.load_state()
    st["last_generate_date"] = today
    st["payload_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    runner.save_state(st)
    _pin_pool_older_than_payload(vault, BASE)

    out = _run_main(monkeypatch, capsys, vault, now_arg)
    assert "generate:cached" in out and "push:accepted" in out
    assert len(calls) == 1
    assert runner.load_state()["last_push_kind"] == "due", (
        "legacy payload 语义未知必须保守记 due — 记 rest 会让当日 due 重扫误开反转门"
    )


# ── CARD-G6-7 (BATCH-2026-09-05-第十二批): state 加性扩展 board_done ──


def test_g67_legacy_state_reads_board_done_as_empty_and_bumps_schema(tmp_path, monkeypatch):
    """(b) 旧文件兼容读: 缺 board_done → 视同 {}; 既有键的值一个都不许动。

    schema_version 随形态单调前进 (读回的 dict 恒含 board_done, 那就是 v2 的
    形状) —— 这不是迁移器: 没有独立迁移入口, 也不改任何既有键的值。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    state = runner.state_path()
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "board_last_recommended": {"A板": "2026-07-29"},
                "last_push_accepted_date": "2026-07-29",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    st = runner.load_state()
    assert st["board_done"] == {}, "旧文件缺 board_done 必须视同空账"
    assert st["board_last_recommended"] == {"A板": "2026-07-29"}
    assert st["last_push_accepted_date"] == "2026-07-29"
    assert st["schema_version"] == runner.STATE_SCHEMA_VERSION == 2

    # 单调: 已经比当前版本新的声明不许被降级
    state.write_text(json.dumps({"schema_version": 99, "board_last_recommended": {}}), encoding="utf-8")
    assert runner.load_state()["schema_version"] == 99, "版本号只前进不后退"


def test_g67_wrong_typed_board_done_quarantined_not_crash(tmp_path, monkeypatch, capsys):
    """(b) board_done 错型与 board_last_recommended 错型同等对待: 隔离重建。

    缺这条的话, 一个 "board_done": [] 会让写侧的 dict 下标在半路炸成 500,
    而不是像本文件其余部分那样诚实地隔离重建。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    calls = _push_harness(monkeypatch, tmp_path, vault, rcs=[0])
    state = runner.state_path()
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        json.dumps({"schema_version": 2, "board_last_recommended": {}, "board_done": []}), encoding="utf-8"
    )

    out = _run_main(monkeypatch, capsys, vault, "2026-07-30T10:00:00+08:00")
    assert "generate:new" in out and "push:accepted" in out and len(calls) == 1
    assert list(state.parent.glob(state.name + ".corrupt-*")), "错型 board_done 必须隔离留档"
    assert runner.load_state()["board_done"] == {}


def test_g67_state_path_takes_explicit_vault_without_touching_global(tmp_path, monkeypatch):
    """(b) 可选 vault 参数与全局 VAULT 同规则、互不干扰。

    Web 侧要为**任意一个库**算 state 路径, 而它与 runner 不同进程。给参数
    而不是让调用方临时改模块全局 —— 后者在线程池里跑的同步端点上是竞态。
    本门锁的正是"给了参数就不该碰全局"这件事。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")}, name="vault-本地")
    other = _vault(tmp_path, {"乙": _node(board="B板")}, name="vault-另一个")
    _patch_runner(monkeypatch, vault, tmp_path)

    assert runner.state_path() == runner.state_path(vault), "缺省必须等于显式传全局 VAULT"
    assert runner.state_path(other) != runner.state_path(vault)
    assert runner.state_path(other).name == f"daily-review.{runner.send_bark.vault_key(other.name)}.state.json", (
        "显式路径必须走同一条 vault_key 规则, 不是另拼一套"
    )
    assert runner.VAULT == vault, "算别的库的路径不许改动模块全局"

    # 读写也接受显式 vault, 且落在各自的文件里
    st = runner.load_state(other)
    st["board_done"] = {"B板": "2026-07-30"}
    runner.save_state(st, other)
    assert runner.state_path(other).exists() and not runner.state_path(vault).exists()
    assert runner.load_state(other)["board_done"] == {"B板": "2026-07-30"}
    assert runner.load_state(vault)["board_done"] == {}


def test_g67_runner_hands_board_done_to_picker(tmp_path, monkeypatch, capsys):
    """(e) 接线: runner 把 state 的 board_done 原样交给生产器。

    判据不是"源码里有那个词", 而是**生产器实际收到了什么** —— 拿真调用
    的实参对账, 打桩换名/改写法都骗不过。

    ⚠ 如实说明: 下传的从来不是 None, 而是 {} —— load_state 保证返回的 dict
    恒含 board_done 键 (旧文件缺键时 setdefault 补 {})。生产器侧对 None 与 {}
    的处置逐字相同 (两者都不进分区分支), 所以行为面等价; 但门断言的是**实际
    看到的那个值**, 不是卡文里那句转述。
    """
    import daily_review_pick as picker  # pyright: ignore[reportMissingImports]

    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _push_harness(monkeypatch, tmp_path, vault, rcs=[0, 0])
    seen = []
    real = picker.build_payload
    monkeypatch.setattr(
        picker,
        "build_payload",
        lambda *a, **kw: (seen.append(kw.get("board_done", "缺省")), real(*a, **kw))[1],
    )

    _run_main(monkeypatch, capsys, vault, "2026-07-30T10:00:00+08:00")
    assert seen == [{}], f"新 state 的空账应原样下传, 实为 {seen!r}"

    st = runner.load_state()
    st["board_done"] = {"A板": "2026-07-30"}
    del st["last_generate_date"]  # 逼它重新生成 (不走缓存复用分支)
    runner.save_state(st)
    _run_main(monkeypatch, capsys, vault, "2026-07-30T11:05:00+08:00")
    assert seen[-1] == {"A板": "2026-07-30"}, f"完成账必须原样下传, 实为 {seen[-1]!r}"


def test_g67_two_vaults_board_done_isolated(tmp_path, monkeypatch, capsys):
    """(f) 双库互不影响 (沿 C1a test_two_vaults_same_day_push_and_state_isolated 形态)。"""
    v1 = _vault(tmp_path, {"甲": _node(board="A板")}, name="vault-一")
    v2 = _vault(tmp_path, {"乙": _node(board="B板")}, name="vault-二")
    _push_harness(monkeypatch, tmp_path, v1, rcs=[0, 0])

    st1 = runner.load_state(v1)
    st1["board_done"] = {"A板": "2026-07-30"}
    runner.save_state(st1, v1)

    assert runner.load_state(v2)["board_done"] == {}, "另一个库的完成账必须完全独立"
    _run_main(monkeypatch, capsys, v2, "2026-07-30T10:00:00+08:00")
    assert runner.load_state(v2)["board_done"] == {}
    assert runner.load_state(v1)["board_done"] == {"A板": "2026-07-30"}, "跑另一个库不许动这个库的账"


def test_g67_marking_done_invalidates_same_day_cache(tmp_path, monkeypatch, capsys):
    """Codex round-1 MEDIUM: 完成账变化必须让当日缓存失效。

    复现的是**真实时序**: 早上跑过一轮 (payload 已缓存) → 白天在网页上标完成 →
    节点没动、也没跨到期点。少了这道门, ensure_payload 直接走缓存分支返回旧榜,
    「让出榜首」整天不生效 (实测 how="cached"、榜首与通知都不变)。

    榜首是哪块板**实测得来**, 不由夹具作者猜。
    """
    vault = _vault(tmp_path, {"甲一": _node(board="甲板"), "甲二": _node(board="甲板"), "乙一": _node(board="乙板")})
    _patch_runner(monkeypatch, vault, tmp_path)

    st = runner.load_state()
    p1, how1 = runner.ensure_payload(st, NOW, TODAY)
    assert how1 == "new"
    first = p1["top_boards"][0]["board"]
    assert p1["notification"]["title"].endswith(first)

    # 无变化 → 仍然复用缓存 (防"永远重扫"的过度失效: 那会让本门恒绿而无意义)
    _pin_pool_older_than_payload(vault, BASE)
    _, how_same = runner.ensure_payload(runner.load_state(), NOW, TODAY)
    assert how_same == "cached", "没有任何变化时必须仍然复用缓存"

    st2 = runner.load_state()
    st2["board_done"] = {first: TODAY}
    runner.save_state(st2)
    p2, how2 = runner.ensure_payload(runner.load_state(), NOW, TODAY)
    assert how2 == "new", "标完成后必须重扫, 否则「让出榜首」整天不生效"
    assert p2["top_boards"][0]["board"] != first, "重扫后榜首必须换人"
    assert not p2["notification"]["title"].endswith(first), "通知也必须跟着换"

    # 再跑一次: 完成账没再变 → 回到缓存 (签名门只对**变化**生效)
    _pin_pool_older_than_payload(vault, BASE)
    _, how3 = runner.ensure_payload(runner.load_state(), NOW, TODAY)
    assert how3 == "cached", "完成账没再变就不该反复重扫"


def test_g67_upgrade_day_missing_signature_with_nonempty_account_still_rescans(tmp_path, monkeypatch):
    """缓存签名**缺席**的两种含义必须分开处理 (收紧规则的配套门)。

    ① 缺席 + 账为空 = 本卡之前落盘的普通 state → 照常复用缓存
       (一律当"变了"会打掉 legacy payload 复用那条既有契约);
    ② 缺席 + 账非空 = 升级当天先标了完成、还没重新生成过 → 必须重扫。
    只写①会让升级当天的让位失效; 只写②会打掉既有契约。两条各一个断言。
    """
    vault = _vault(tmp_path, {"甲一": _node(board="甲板"), "甲二": _node(board="甲板"), "乙一": _node(board="乙板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    p1, _ = runner.ensure_payload(runner.load_state(), NOW, TODAY)
    first = p1["top_boards"][0]["board"]
    _pin_pool_older_than_payload(vault, BASE)

    # ① 手工抹掉签名、账留空 —— 模拟本卡之前落盘的 state
    st = runner.load_state()
    st.pop("board_done_sig", None)
    st["board_done"] = {}
    runner.save_state(st)
    _, how_a = runner.ensure_payload(runner.load_state(), NOW, TODAY)
    assert how_a == "cached", "缺签名且账为空 = 旧 state, 不该被当成'变了'"

    # ② 同样没有签名, 但账非空 —— 升级当天先标完成的那一格
    st = runner.load_state()
    st.pop("board_done_sig", None)
    st["board_done"] = {first: TODAY}
    runner.save_state(st)
    p2, how_b = runner.ensure_payload(runner.load_state(), NOW, TODAY)
    assert how_b == "new", "缺签名但账非空 = 从没对过账, 必须重扫"
    assert p2["top_boards"][0]["board"] != first


# ══════════════════════════════════════════════════════════════════════════
# CARD-G6-7-R: 跨进程 state 锁 + 锁内三方合并 + v1→v2 升版行为门
# ══════════════════════════════════════════════════════════════════════════

#: 子进程: 独立进程里对同一个 vault 调一次 save_state, 打印起止时刻。
#: 判据要的是"它什么时候**完成**", 不是"它有没有报错" —— 后者在锁失效时
#: 同样是不报错的 (两个写者各写各的, 谁也不知道对方存在)。
_SAVE_STATE_CHILD = """
import contextlib, errno, fcntl, json, os, sys, time
sys.path.insert(0, sys.argv[1])
from pathlib import Path
import daily_review_run as runner
# argv[3] = 握手标记, argv[4] = 锁文件路径。
# ⚠ Codex round-1 M3 / round-2 M1 / round-3 M1: 握手必须绑在**生产取锁的入口**,
# 而不是 import 之后随便某处。前两版把探测写在模块顶层, 于是「持锁 1.5s 期间
# 子进程没完成」还可以被"它探测完又停了 2 秒"解释掉 —— 量的仍不是锁。
# 这里包住 runner.state_locked 本身: 探测紧挨着真锁, 中间没有任何业务代码。
# 探测报 blocked 且下一行就进真锁 ⇒ 「保存被这把锁挡住」的因果链是闭合的。
_real_locked = runner.state_locked


@contextlib.contextmanager
def _traced(vault=None):
    _lock = runner.state_lock_path(vault)
    _lock.parent.mkdir(parents=True, exist_ok=True)
    _fd = os.open(str(_lock), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.lockf(_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _seen = "free"
        fcntl.lockf(_fd, fcntl.LOCK_UN)
    except BlockingIOError:
        _seen = "blocked"
    os.close(_fd)
    Path(sys.argv[3]).write_text(_seen, encoding="utf-8")
    with _real_locked(vault):
        yield


runner.state_locked = _traced
started = time.time()
runner.save_state(
    {"schema_version": 2, "board_last_recommended": {}, "board_done": {"子进程板": "2026-07-30"}},
    Path(sys.argv[2]),
)
print(json.dumps({"started": started, "finished": time.time()}))
"""

#: 子进程: 对锁文件做一次**非阻塞**探测, 什么都不写。
#: 退出码 1 = 被别人持着 (正文里打 errno 名, 判据绑"被哪一层拒的");
#: 0 = 拿到了锁 (正控用)。
_LOCK_PROBE_CHILD = """
import errno, fcntl, os, sys
fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o644)
try:
    fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError as e:
    print("BLOCKED:" + errno.errorcode.get(e.errno, str(e.errno)))
    sys.exit(1)
except OSError as e:
    print("OTHER:" + errno.errorcode.get(e.errno, str(e.errno)))
    sys.exit(2)
print("ACQUIRED")
fcntl.lockf(fd, fcntl.LOCK_UN)
os.close(fd)
sys.exit(0)
"""


def _child_env(tmp_path: Path) -> dict:
    """子进程的 BACKUPS 与父进程 _patch_runner 同源: 两边都落 tmp_path/backups。

    父进程走 monkeypatch.setattr(runner, "BACKUPS", ...) —— 那是进程内的;
    子进程只能靠 CANVAS_REPO (BACKUPS = REPO / "backups")。两条路必须
    指向同一个目录, 否则"锁住了"只是因为两边根本在动不同的文件。
    """
    env = dict(os.environ)
    env["CANVAS_REPO"] = str(tmp_path)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _probe_lock(lock_path: Path, tmp_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", _LOCK_PROBE_CHILD, str(lock_path)],
        capture_output=True,
        text=True,
        timeout=30,
        env=_child_env(tmp_path),
        check=False,
    )


def test_g67r_runner_save_does_not_clobber_web_written_board_done(tmp_path, monkeypatch, capsys):
    """(c) 门①  runner 向: runner 的整轮 save 不许吃掉窗口内 Web 落盘的完成账。

    窄窗形态 (Y2-B 如实登记的那条): runner main 在 :297 load_state, 扫描要
    几秒, 期间浏览器点了「这板做完了」把 board_done 写进同一个文件; runner
    :264 的 save 若整写 mine, 那次点击就静默消失了。

    ⚠ 本门预置 v2 形态 (含 board_done 键), 与现网实测一致。
    ⛔ 初版这里写着「缺键的 v1 文件下空账会**正当地**压过磁盘 —— 那不是缺陷,
    是升版语义」。那句话是错的, 而且它正是 Codex round-1 H1 抓到的那个丢账:
    v1 文件下 setdefault 补出来的空账把 Web 刚写成功的完成记录覆盖掉了。
    现在 base 记在归一化之后, 补出来的默认值不算"我改过";
    v1 的那条路由 test_g67r_upgrade_default_account_does_not_clobber_window_write
    专门守着。本门只负责 v2 这条路。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _push_harness(monkeypatch, tmp_path, vault, rcs=[0])
    state = runner.state_path()
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        json.dumps({"schema_version": 2, "board_last_recommended": {}, "board_done": {}}, ensure_ascii=False),
        encoding="utf-8",
    )

    real_build = picker.build_payload

    def _web_writes_midway(*a, **kw):
        # 扫描进行到一半 —— 这正是 load(:297) 之后、save(:264) 之前那段窗口
        cur = json.loads(state.read_text(encoding="utf-8"))
        cur["board_done"] = {"A板": TODAY}
        state.write_text(json.dumps(cur, ensure_ascii=False), encoding="utf-8")
        return real_build(*a, **kw)

    monkeypatch.setattr(picker, "build_payload", _web_writes_midway)

    _run_main(monkeypatch, capsys, vault, "2026-07-30T10:00:00+08:00")

    st = json.loads(state.read_text(encoding="utf-8"))
    assert st["board_done"] == {"A板": TODAY}, (
        f"窗口内 Web 落盘的完成账被 runner 整写覆盖了, 实为 {st.get('board_done')!r}"
    )
    # 两侧字段同时保留 —— 合并不是"以磁盘为准"的另一种整写
    assert st["last_generate_date"] == TODAY
    assert st.get("board_done_sig"), "runner 自己改的键必须仍以 runner 为准"
    assert st.get("payload_sha256")


def test_g67r_state_lock_blocks_other_process_until_released(tmp_path, monkeypatch):
    """(c) 门③  锁存在性: 别的进程要等到锁释放才写得成。

    判据是**时间戳**不是"有没有报错" —— 锁失效时两个写者都不报错, 只是后
    写的那个把先写的覆盖掉; 用报错做判据的门在真缺陷下是绿的。
    对照组 (不持锁) 承重: 没有它, 一个"子进程根本没跑起来"的实现同样能让
    "完成时刻 ≥ 释放时刻"成立。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    lock_path = runner.state_lock_path(vault)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    ready_free, ready_held = tmp_path / "ready-free", tmp_path / "ready-held"
    scripts_dir = str(WT / "scripts")

    def _child(ready):
        return [sys.executable, "-c", _SAVE_STATE_CHILD, scripts_dir, str(vault), str(ready), str(lock_path)]

    # ── 对照: 不持锁 ⇒ 子进程一路畅通 ──
    t_spawn = time.time()
    free = subprocess.run(
        _child(ready_free), capture_output=True, text=True, timeout=60, env=_child_env(tmp_path), check=False
    )
    assert free.returncode == 0, f"对照组子进程本身就跑不起来, 本门无效: {free.stderr}"
    free_elapsed = json.loads(free.stdout)["finished"] - t_spawn
    assert free_elapsed < 5.0, f"对照组不该等 (实为 {free_elapsed:.2f}s) —— 阈值放宽到 5s 仍超 = 环境问题"
    assert ready_free.read_text(encoding="utf-8") == "free", (
        "对照组的非阻塞探测应当拿得到锁 —— 拿不到说明有别人在持锁, 对照不成立"
    )
    assert runner.load_state(vault)["board_done"] == {"子进程板": "2026-07-30"}

    # ── 正门: 父进程持锁 1.5s ──
    hold = 1.5
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o644)
    fcntl.lockf(fd, fcntl.LOCK_EX)
    try:
        proc = subprocess.Popen(
            _child(ready_held), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=_child_env(tmp_path)
        )
        # ⚠ Codex round-1 M3: 先等就绪标记 —— 否则"持锁期间没完成"可以被
        # 「子进程还在 import」解释掉, 判据量的就成了启动延迟而不是锁。
        deadline = time.time() + 30
        while not ready_held.exists() and time.time() < deadline:
            assert proc.poll() is None, f"子进程在写出就绪标记前就退出了: {proc.communicate()[1]}"
            time.sleep(0.02)
        assert ready_held.exists(), "子进程 30s 内没到达取锁点 —— 本门的前提不成立"
        # ⚠ Codex round-2 M1: 标记的**内容**才是判据 —— "已经在锁上被拒过一次"。
        # 只看文件在不在, 等于只证明了 import 跑完了。
        assert ready_held.read_text(encoding="utf-8") == "blocked", (
            "子进程到达锁时并没有被挡住 —— 后面那 1.5s 量的就不是锁"
        )
        ready_at = time.time()
        time.sleep(hold)
        assert proc.poll() is None, "子进程在锁被持有期间就完成了 —— 锁没起作用"
        released = time.time()
    finally:
        fcntl.lockf(fd, fcntl.LOCK_UN)
        os.close(fd)
    out, err = proc.communicate(timeout=60)
    assert proc.returncode == 0, f"释放后子进程仍失败: {err}"
    finished = json.loads(out)["finished"]
    assert finished >= released, f"子进程完成时刻 {finished:.3f} 早于释放时刻 {released:.3f} —— 锁形同虚设"
    assert finished - released <= 5.0, f"释放后 {finished - released:.2f}s 才完成, 超出可接受范围"
    assert runner.load_state(vault)["board_done"] == {"子进程板": "2026-07-30"}
    print(
        f"[g67r-lock] ready_at={ready_at:.3f} released={released:.3f} child_finished={finished:.3f} "
        f"blocked_after_ready={released - ready_at:.3f}s wait_after_release={finished - released:.3f}s "
        f"free_elapsed={free_elapsed:.3f}s"
    )


def test_g67r_state_lock_survives_inner_save_state_reentry(tmp_path, monkeypatch):
    """(c) 门④  重入不丢锁: 持锁期间调 save_state 之后, 锁必须还在。

    POSIX 记录锁按「进程 × 文件」释放 —— 内层若对同一路径再 open 一次再
    close, 外层那把锁会被一起丢掉, 而**本进程完全察觉不到**。门③ 只比跨进程
    竞争, 对这种"内层把外层释放了"完全失明。
    两半都承重: 前半 (with 体内探测必失败) 抓丢锁; 后半 (退出后必成功) 是
    正控, 防这门变成恒红。判据绑 errno 身份, 不用"有没有报错"。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    lock_path = runner.state_lock_path(vault)

    with runner.state_locked(vault):
        runner.save_state({"schema_version": 2, "board_last_recommended": {}, "board_done": {"内层": TODAY}}, vault)
        inner = _probe_lock(lock_path, tmp_path)
        assert inner.returncode == 1, (
            f"with 体内 LOCK_NB 探测应被拒 (锁仍在), 实为 rc={inner.returncode} out={inner.stdout!r} err={inner.stderr!r}"
        )
        assert inner.stdout.strip() in ("BLOCKED:EAGAIN", "BLOCKED:EACCES"), f"拒绝的不是记录锁那一层: {inner.stdout!r}"
        print(f"[g67r-lock] in-with probe rc={inner.returncode} {inner.stdout.strip()}")

    outside = _probe_lock(lock_path, tmp_path)
    assert outside.returncode == 0, (
        f"退出 with 后应拿得到锁 (正控: 证明本门不是恒红), 实为 rc={outside.returncode} out={outside.stdout!r}"
    )
    print(f"[g67r-lock] post-with probe rc={outside.returncode} {outside.stdout.strip()}")
    assert runner.load_state(vault)["board_done"] == {"内层": TODAY}


def test_g67r_state_lock_refuses_symlinked_lock_path(tmp_path, monkeypatch):
    """(c) Codex round-1 H3: 锁路径是软链时必须拒绝取锁, 且不在链的目标上留痕。

    两种预置各堵一半:
      ① 锁 → state.json 本身: 拿到的记录锁与 state 同 inode, 之后 load_state
         的读盘 close 会把整个进程在该 inode 上的锁一起释放 (POSIX 记录锁按
         进程 × 文件), 而登记表还以为锁在 —— 互斥凭空消失且无人察觉;
      ② 锁 → 库内一个尚不存在的路径: O_CREAT 会**在库里创建文件**, 破掉
         「完成账不写 vault」这条写面承诺。
    与 save_state 的 tmp 是同一条防线 (O_NOFOLLOW), 当时漏在了锁这一侧。
    判据绑 errno 身份 (ELOOP), 不用"有没有报错"。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    lock_path = runner.state_lock_path(vault)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    state = runner.state_path(vault)
    runner.save_state({"schema_version": 2, "board_last_recommended": {}, "board_done": {"甲板": TODAY}}, vault)
    state_bytes = state.read_bytes()

    # ① 锁指向 state 本身
    lock_path.unlink(missing_ok=True)
    lock_path.symlink_to(state)
    with pytest.raises(OSError) as ei:
        with runner.state_locked(vault):
            pass
    assert ei.value.errno == errno.ELOOP, f"拒绝的不是软链那一层: errno={ei.value.errno}"
    assert state.read_bytes() == state_bytes, "被拒的取锁不许动 state"

    # ② 锁指向库内一个尚不存在的节点路径
    target = vault / "节点" / "不该被创建.md"
    lock_path.unlink()
    lock_path.symlink_to(target)
    with pytest.raises(OSError) as ei2:
        with runner.state_locked(vault):
            pass
    assert ei2.value.errno == errno.ELOOP, f"拒绝的不是软链那一层: errno={ei2.value.errno}"
    assert not target.exists(), "取锁在库内创建了文件 —— 写面承诺破了"

    # 正控: 换回普通路径, 锁必须照常拿得到 (证明本门不是恒红)
    lock_path.unlink()
    with runner.state_locked(vault):
        assert lock_path.is_file() and not lock_path.is_symlink()


def test_g67r_hardlinked_lock_is_refused(tmp_path, monkeypatch):
    """(c) Codex round-2 H2: 锁文件是**硬链接**时必须拒绝取锁。

    O_NOFOLLOW 只拒符号链接。把 <state>.lock 做成 <state>.json 的硬链接,
    两者就是同一个 inode —— 取锁成功之后 load_state 的一次读盘 close 会释放
    本进程在该 inode 上的全部记录锁 (POSIX 记录锁按进程 × 文件), 而登记表
    还报告持锁, 互斥凭空消失且无人察觉。
    判据绑 errno 身份 (EMLINK), 不用"有没有报错"。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    state = runner.state_path(vault)
    runner.save_state({"schema_version": 2, "board_last_recommended": {}, "board_done": {"甲板": TODAY}}, vault)
    state_bytes = state.read_bytes()
    lock_path = runner.state_lock_path(vault)

    lock_path.unlink(missing_ok=True)
    os.link(state, lock_path)  # 硬链接: 同 inode, O_NOFOLLOW 看不见
    assert lock_path.stat().st_ino == state.stat().st_ino, "夹具前提: 必须真的是同一个 inode"
    with pytest.raises(OSError) as ei:
        with runner.state_locked(vault):
            pass
    assert ei.value.errno == errno.EMLINK, f"拒绝的不是硬链接那一层: errno={ei.value.errno}"
    assert state.read_bytes() == state_bytes, "被拒的取锁不许动 state"

    # 正控: 换回独立文件, 锁必须照常拿得到 (证明本门不是恒红)
    lock_path.unlink()
    with runner.state_locked(vault):
        assert lock_path.stat().st_nlink == 1


def test_g67r_corrupt_quarantine_happens_under_the_lock(tmp_path, monkeypatch):
    """(c) Codex round-2 H1: 损坏隔离不许用过期判断移走别人刚写好的文件。

    失败时序 (锁只盖住 save 而不盖住"读+判断+隔离"时成立):
      · runner 读到坏 JSON, 还没执行 os.replace;
      · Web 取到锁, 把坏文件隔离掉、写进完成账 A、返回 200;
      · runner 按早已过期的「坏」判断执行 os.replace, 把**此刻已经有效、含 A
        的文件**移进 .corrupt-*, 再整写一份空账 —— A 从活动 state 里消失。

    本门把「Web 那一手」插在 runner 读盘之后、隔离之前: 用 monkeypatch 包住
    load_state 内部实际读盘用的 Path.read_text, 在它返回坏内容之后立刻替换
    磁盘文件。锁若覆盖了整段读+判断+隔离, 这只手根本插不进来 (它要先拿锁),
    所以本门用"不经锁的直写"模拟, 判据落在最终 state 上。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    state = runner.state_path(vault)
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text("{这是坏的", encoding="utf-8")

    good = json.dumps(
        {"schema_version": 2, "board_last_recommended": {}, "board_done": {"A板": TODAY}}, ensure_ascii=False
    )
    real_read_text = Path.read_text
    swapped = []

    def _read_then_swap(self, *a, **kw):
        out = real_read_text(self, *a, **kw)
        if self == state and not swapped:
            # 「Web 已经把它换成好的了」—— 就在 runner 读完、还没判断完的那一刻
            swapped.append(True)
            state.write_text(good, encoding="utf-8")
        return out

    monkeypatch.setattr(Path, "read_text", _read_then_swap)
    st = runner.load_state(vault)
    monkeypatch.undo()
    assert swapped, "夹具前提: 那一手必须真的插进去了"

    on_disk_now = state.read_text(encoding="utf-8") if state.exists() else None
    quarantined = sorted(state.parent.glob(state.name + ".corrupt-*"))
    assert on_disk_now is not None, (
        f"活动 state 被移走了 —— 用过期判断隔离掉了别人刚写好的文件 (隔离件: {[q.name for q in quarantined]})"
    )
    assert json.loads(on_disk_now)["board_done"] == {"A板": TODAY}, "窗口内写成功的完成账没了"
    st["last_generate_date"] = TODAY
    runner.save_state(st, vault)
    assert json.loads(state.read_text(encoding="utf-8"))["board_done"] == {"A板": TODAY}, "随后的整写又把那笔账抹掉了"


#: 子进程: **守规矩地取锁**之后写一笔完成账。用来验外层锁是不是真的挡得住
#: 一个合规写者 —— 不经锁的直写超出锁的承诺范围, 用它做判据等于在验别的东西。
_LOCK_ABIDING_WRITER = """
import json, sys
sys.path.insert(0, sys.argv[1])
from pathlib import Path
import daily_review_run as runner
vault = Path(sys.argv[2])
with runner.state_locked(vault):
    st = runner.load_state(vault)
    st.setdefault("board_done", {})["A板"] = sys.argv[3]
    runner.save_state(st, vault)
print("written")
"""


def test_g67r_state_and_lock_must_not_share_an_inode(tmp_path, monkeypatch):
    """(c) Codex round-3 H1: 锁与 state 落到同一个 inode 一律拒 —— 两个方向都要。

    前几层拦的是**形态**: O_NOFOLLOW 拒"锁路径是软链", nlink 拒硬链接。危险的
    却是**结果**: 反方向的软链 (state.json → state.lock) 让锁路径本身是普通
    文件、nlink 也是 1, 三层形态判断全过; 而 load_state 的读盘跟随 state 的
    软链打开并关闭锁 inode, 本进程在该文件上的记录锁**整个**被释放, 登记表
    却还报告持锁 —— 互斥凭空消失, 两个写者可以同时合并旧状态再先后发布。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    lock_path = runner.state_lock_path(vault)
    state = runner.state_path(vault)
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # 反向软链: state → lock。锁路径本身是普通空文件, 前三层判断全过。
    lock_path.unlink(missing_ok=True)
    lock_path.write_bytes(b"")
    state.unlink(missing_ok=True)
    state.symlink_to(lock_path)
    assert not lock_path.is_symlink() and lock_path.stat().st_nlink == 1, (
        "夹具前提: 锁路径必须是普通文件且 nlink==1, 否则红的是前几层而不是 inode 那条"
    )
    with pytest.raises(OSError) as ei:
        with runner.state_locked(vault):
            pass
    assert ei.value.errno == errno.EMLINK, f"拒绝的不是 inode 那一层: errno={ei.value.errno}"

    # 正控: 拆掉软链, 锁必须照常拿得到 (证明本门不是恒红)
    state.unlink()
    lock_path.unlink()
    with runner.state_locked(vault):
        assert lock_path.stat().st_ino != (state.stat().st_ino if state.exists() else -1)


def test_g67r_base_snapshot_survives_state_symlink_being_replaced(tmp_path, monkeypatch):
    """(c) Codex round-3 H2: state 原本是软链时, 第一次保存换掉它不许让 base 失效。

    时序 (**所有写者都正确取了锁**, 照样丢账):
      · state.json 是指向 T 的软链, 完成账为空;
      · runner load_state —— 若 base 按 resolve 后的路径存, 键落在 T 上;
      · runner 第一次保存: os.replace 把软链换成一个普通文件 S;
      · Web 守规矩取锁写入完成账 A;
      · runner 第二次保存: 按 S 查 base 查不到 ⇒ 走整写分支 ⇒ A 被空账覆盖。
    修法是 base 按**逻辑路径**存 —— 快照记的本来就是"我这条路径上次读到什么"。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    state = runner.state_path(vault)
    state.parent.mkdir(parents=True, exist_ok=True)
    target = state.parent / "真身.json"
    target.write_text(
        json.dumps({"schema_version": 2, "board_last_recommended": {}, "board_done": {}}, ensure_ascii=False),
        encoding="utf-8",
    )
    state.symlink_to(target)
    assert state.is_symlink(), "夹具前提: state 必须真的是一条软链"

    st = runner.load_state(vault)  # base 记在这一刻
    st["last_generate_date"] = TODAY
    runner.save_state(st, vault)  # os.replace 把软链换成普通文件
    assert not state.is_symlink(), "夹具前提: 第一次保存应当把软链换成普通文件"

    # Web 守规矩地取锁写入完成账
    state.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "board_last_recommended": {},
                "board_done": {"A板": TODAY},
                "last_generate_date": TODAY,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    st["last_push_accepted_date"] = TODAY  # runner 第二次保存 (推送账)
    runner.save_state(st, vault)

    on_disk = json.loads(state.read_text(encoding="utf-8"))
    assert on_disk["board_done"] == {"A板": TODAY}, "第二次保存整写掉了守规矩写进来的完成账"
    assert on_disk["last_push_accepted_date"] == TODAY


def test_g67r_quarantine_lock_blocks_a_lock_abiding_writer(tmp_path, monkeypatch):
    """(c) Codex round-3 M2: load_state 的**外层锁**本身承重。

    上一条隔离门用"不经锁的直写"做插手, 于是撤掉外层锁它照样绿 (第二次读就把
    账救回来了) —— 那条门验的是重读, 不是锁。这条补上锁那一半: 插手者是一个
    **守规矩取锁**的子进程, 放在第二次读之后、隔离之前。
      · 锁在: 子进程被挡在 load_state 之外, 等隔离做完才写 ⇒ 它写的账留得住;
      · 锁不在: 子进程当场写好账, runner 随后按旧判断把它隔离掉 ⇒ 账没了。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    state = runner.state_path(vault)
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text("{这是坏的", encoding="utf-8")

    reads = []
    real_read_text = Path.read_text
    holder = {}

    def _spy(self, *a, **kw):
        out = real_read_text(self, *a, **kw)
        if self == state:
            reads.append(1)
            if len(reads) == 2 and "proc" not in holder:
                # 第二次读 (隔离前重读) 刚回来 —— 隔离还没做。放一个合规写者进来。
                holder["proc"] = subprocess.Popen(
                    [sys.executable, "-c", _LOCK_ABIDING_WRITER, str(WT / "scripts"), str(vault), TODAY],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=_child_env(tmp_path),
                )
                time.sleep(0.6)  # 给它足够时间跑到取锁点 (锁在的话它会停在那里)
        return out

    monkeypatch.setattr(Path, "read_text", _spy)
    runner.load_state(vault)
    monkeypatch.undo()
    assert len(reads) >= 2, "夹具前提: 隔离前必须真的读了第二次"
    proc = holder["proc"]
    out, err = proc.communicate(timeout=60)
    assert proc.returncode == 0, f"合规写者本身跑挂了, 本门无效: {err}"

    on_disk = json.loads(state.read_text(encoding="utf-8"))
    assert on_disk["board_done"] == {"A板": TODAY}, "守规矩取锁写进来的完成账被隔离掉了 —— load_state 的外层锁没挡住它"


def test_g67r_fresh_state_does_not_clobber_account_created_in_the_window(tmp_path, monkeypatch):
    """(c) Codex round-1 H2: 「读时没有文件」不等于「我有权整写」。

    失败时序: runner 首次读 (或刚隔离掉一个坏文件) 拿到一份默认空账; 扫描期间
    Web 创建了 state 并记下 A; runner 保存时若因为"没有 base"就整写自己那份,
    连磁盘都不读一眼, 那次点击就没了。默认值不是"我的修改"。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    state = runner.state_path(vault)
    state.parent.mkdir(parents=True, exist_ok=True)

    for label, prime in (("缺文件", lambda: None), ("损坏隔离", lambda: state.write_text("{坏", encoding="utf-8"))):
        state.unlink(missing_ok=True)
        for q in state.parent.glob(state.name + ".corrupt-*"):
            q.unlink()
        prime()

        st = runner.load_state(vault)  # base = 默认空账 (不是 None)
        assert st["board_done"] == {}, f"[{label}] 前提: 读回来的应是空账"
        # 窗口内: 别人把文件建起来并写了真账
        state.write_text(
            json.dumps(
                {"schema_version": 2, "board_last_recommended": {}, "board_done": {"A板": TODAY}}, ensure_ascii=False
            ),
            encoding="utf-8",
        )
        st["last_generate_date"] = TODAY  # runner 自己改的键
        runner.save_state(st, vault)

        on_disk = json.loads(state.read_text(encoding="utf-8"))
        assert on_disk["board_done"] == {"A板": TODAY}, f"[{label}] 窗口内新建的完成账被整写抹掉了"
        assert on_disk["last_generate_date"] == TODAY, f"[{label}] runner 自己改的键必须仍以 runner 为准"


def test_g67r_upgrade_default_account_does_not_clobber_window_write(tmp_path, monkeypatch):
    """(c) Codex round-1 H1: 升版补出来的空完成账不许覆盖窗口内写成功的记录。

    v1 文件缺 board_done, load_state 用 setdefault 补一个 {}。若把这个补出来的
    默认值算成"本进程改过", 它就有权压过磁盘 —— **加性升级反倒删掉了一次用户
    操作**, 而且只在 v1 文件上发生 (用 v2 预置的那道门看不见)。
    schema_version 仍必须前进: 它是形态声明, 走单调取大而不是三方合并。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    state = runner.state_path(vault)
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        json.dumps({"schema_version": 1, "board_last_recommended": {"A板": "2026-07-29"}}, ensure_ascii=False),
        encoding="utf-8",
    )

    st = runner.load_state(vault)  # 补出 board_done={} 并把声明推到 2
    assert st["board_done"] == {} and st["schema_version"] == 2
    # 窗口内 Web 落账 (它自己也会把文件升成 v2)
    state.write_text(
        json.dumps(
            {"schema_version": 2, "board_last_recommended": {"A板": "2026-07-29"}, "board_done": {"A板": TODAY}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    st["last_generate_date"] = TODAY
    runner.save_state(st, vault)

    on_disk = json.loads(state.read_text(encoding="utf-8"))
    assert on_disk["board_done"] == {"A板": TODAY}, "升版补出的空账覆盖了窗口内写成功的完成记录"
    assert on_disk["schema_version"] == 2, "声明版本仍须前进 (单调取大)"
    assert on_disk["last_generate_date"] == TODAY


def test_g67r_schema_version_never_goes_backwards_on_merge(tmp_path, monkeypatch):
    """(c) 单调取大: 磁盘上更新的声明不许被本进程手上更旧的那个压回去。

    H1 的修法把 base 挪到归一化之后, 于是"升版"本身成了"我没改过" —— 不给
    schema_version 特判, 合并就会以磁盘为准, 把已经前进的声明拉回旧值。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    state = runner.state_path(vault)
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        json.dumps({"schema_version": 2, "board_last_recommended": {}, "board_done": {}}, ensure_ascii=False),
        encoding="utf-8",
    )
    st = runner.load_state(vault)
    state.write_text(
        json.dumps({"schema_version": 99, "board_last_recommended": {}, "board_done": {}}, ensure_ascii=False),
        encoding="utf-8",
    )
    st["last_generate_date"] = TODAY
    runner.save_state(st, vault)
    assert json.loads(state.read_text(encoding="utf-8"))["schema_version"] == 99, "版本号只前进不后退"

    # ⚠ Codex round-2 L1: 上面那半**不依赖** max 特判 —— mine 没改过版本, 普通
    # 合并本来就会选磁盘的 99。真正需要特判的是反方向: 磁盘更旧。
    state.write_text(
        json.dumps({"schema_version": 2, "board_last_recommended": {}, "board_done": {}}, ensure_ascii=False),
        encoding="utf-8",
    )
    st2 = runner.load_state(vault)
    assert st2["schema_version"] == 2
    state.write_text(
        json.dumps({"schema_version": 1, "board_last_recommended": {}, "board_done": {}}, ensure_ascii=False),
        encoding="utf-8",
    )
    st2["last_generate_date"] = TODAY
    runner.save_state(st2, vault)
    assert json.loads(state.read_text(encoding="utf-8"))["schema_version"] == 2, (
        "磁盘上更旧的声明把已经前进的版本拉回去了 —— 单调取大没生效"
    )


def test_g67r_v1_state_load_save_lands_as_v2_with_values_intact(tmp_path, monkeypatch):
    """(e)①  v1 文件经 load→save 落盘为 v2, 既有键逐项等值、不多不少。

    既有 :963 只验 load 回来的**内存 dict**; 本门验**落盘形态** —— 升版
    到底有没有写下去, 是两件事。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    state = runner.state_path()
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "board_last_recommended": {"A板": "2026-07-29"},
                "last_push_accepted_date": "2026-07-29",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    runner.save_state(runner.load_state())

    on_disk = json.loads(state.read_text(encoding="utf-8"))
    assert on_disk["schema_version"] == runner.STATE_SCHEMA_VERSION == 2
    assert on_disk["board_done"] == {}
    assert on_disk["board_last_recommended"] == {"A板": "2026-07-29"}, "既有键的值一个都不许动"
    assert on_disk["last_push_accepted_date"] == "2026-07-29"
    assert set(on_disk) == {
        "schema_version",
        "board_last_recommended",
        "last_push_accepted_date",
        "board_done",
    }, f"升版只加 board_done 一个键, 实为 {sorted(on_disk)}"


def test_g67r_v2_load_save_is_byte_idempotent(tmp_path, monkeypatch):
    """(e)②  再来一次 load→save, 文件字节与上一次落盘完全相同。

    锁内三方合并会重排键 —— 若合并用 set 遍历, 这门就会随机红。字节幂等
    是"升版路径不抖"的最短判据, 也顺带钉住合并的键序稳定。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    state = runner.state_path()
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        json.dumps({"schema_version": 1, "board_last_recommended": {"A板": "2026-07-29"}}, ensure_ascii=False),
        encoding="utf-8",
    )

    runner.save_state(runner.load_state())
    first = state.read_bytes()
    runner.save_state(runner.load_state())
    assert state.read_bytes() == first, "二次 load→save 必须逐字节幂等"
    # 第三次也一样 —— 两次相同可能是巧合, 三次才排掉"每两次翻转一下"
    runner.save_state(runner.load_state())
    assert state.read_bytes() == first


def test_g67r_quarantine_keeps_original_bytes(tmp_path, monkeypatch, capsys):
    """(e)③  错型隔离时 .corrupt-* 必须逐字节保留原文件 (不吞不改写)。

    既有 :996 只验"有没有留档"; 留下一个被改写过的副本, 事后就查不出当时
    到底坏成什么样了 —— 留档的全部价值就在那几个字节上。
    """
    vault = _vault(tmp_path, {"甲": _node(board="A板")})
    _patch_runner(monkeypatch, vault, tmp_path)
    state = runner.state_path()
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        json.dumps({"schema_version": 2, "board_last_recommended": {}, "board_done": []}, ensure_ascii=False),
        encoding="utf-8",
    )
    original = state.read_bytes()

    st = runner.load_state()
    assert st["board_done"] == {}, "错型账必须重建为空账"

    quarantined = sorted(state.parent.glob(state.name + ".corrupt-*"))
    assert len(quarantined) == 1, f"错型必须隔离留档恰一份, 实为 {[p.name for p in quarantined]}"
    assert quarantined[0].read_bytes() == original, "隔离留档被改写了 —— 事后无从查证当时坏成什么样"
    assert not state.exists(), "原文件应已被改名走 (下次 save 才重建)"
