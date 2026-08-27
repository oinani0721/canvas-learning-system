"""daily_review_run 当天重学卡刷新 (CARD-A3, BATCH-2026-08-24-复习闭环)。

ensure_payload 缓存失效三场景锁定: 当天已生成后, 节点池比 payload 新
(quiz 写侧刚更新 fsrs_due / 新增节点) 必须重扫; 无变动仍复用; 重扫后
同日推送去重 (skip-done) 与 tie-break 语义 (board_last_recommended
每天只在第一个非空榜首落账一次, CARD-D2a) 不被破坏。

只 assert dict / 状态 / runner 状态行, 不 assert 今日复习.md 渲染文本
(与 A2 渲染层解耦)。mtime 全部 os.utime 显式钉死, 不依赖墙钟顺序。
"""

import json
import os
import plistlib
import re
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

    monkeypatch.setattr(runner.send_bark.urllib.request, "urlopen", _capture_urlopen)
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
    import migrate_daily_review_state as migrate

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
    """Codex-C1a B3: '[]' 是合法 JSON 但 runner load_state 会当场炸 —
    结构必须校验到 dict 级, 拒迁且零写入。"""
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
