"""daily_review_run 当天重学卡刷新 (CARD-A3, BATCH-2026-08-24-复习闭环)。

ensure_payload 缓存失效三场景锁定: 当天已生成后, 节点池比 payload 新
(quiz 写侧刚更新 fsrs_due / 新增节点) 必须重扫; 无变动仍复用; 重扫后
同日推送去重 (skip-done) 与 tie-break 语义 (board_last_recommended
只在首次生成时写) 不被破坏。

只 assert dict / 状态 / runner 状态行, 不 assert 今日复习.md 渲染文本
(与 A2 渲染层解耦)。mtime 全部 os.utime 显式钉死, 不依赖墙钟顺序。
"""

import os
import plistlib
import shutil
import sys
from datetime import datetime, time as dtime, timezone
from pathlib import Path

WT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WT / "scripts"))

import daily_review_run as runner  # noqa: E402

NOW = datetime(2026, 7, 30, 2, 0, tzinfo=timezone.utc)
TODAY = "2026-07-30"
BASE = 1_700_000_000  # 人工 mtime 基准: 只比大小, 绝对值无意义


def _node(board="普通板", extra=""):
    return f'---\ntype: concept\nsource_board: "[[原白板/{board}]]"\n{extra}---\n真实内容。\n'


def _vault(tmp_path, nodes: dict) -> Path:
    vault = tmp_path / "vault"
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)
    for name, content in nodes.items():
        (vault / "节点" / f"{name}.md").write_text(content, encoding="utf-8")
    return vault


def _patch_runner(monkeypatch, vault, tmp_path):
    monkeypatch.setattr(runner, "VAULT", vault)
    monkeypatch.setattr(runner, "STATE", tmp_path / "backups" / "daily-review.state.json")
    monkeypatch.setattr(runner, "LOG", tmp_path / "backups" / "daily-review.log")


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
    # today 按 runner 同一变换推导 (机器时区无关): skip-done 门在窗口门之前
    today = datetime.fromisoformat(now_arg).astimezone().date().isoformat()

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

    import daily_review_pick as picker

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


# ── tie-break 守卫: 重扫路径不写 board_last_recommended (卡片风险条目) ──


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
    # 核心: 重扫换榜也不得把 B板 标成「今天推荐过」— 天级轮转语义只属于首扫
    assert st["board_last_recommended"] == {"A板": TODAY}
