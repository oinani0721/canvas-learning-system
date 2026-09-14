"""跨 vault 复习总览聚合 (CARD-C2, BATCH-2026-08-25-跨vault与收束)。

四类锁定: 聚合正确 / 缺投影显式降级 / 损坏 JSON 不 500 / stale 徽标。
CARD-D1 (BATCH-2026-08-27-Anki化与诚实收尾) 追加: 板级聚合与 stats 自洽 /
due_nodes 脏行 corrupt 降级 / Asia/Shanghai 时间人话化 / 无投影深链降级。
CARD-G3-6a (BATCH-2026-08-29-第六批) 追加: 五桶分层计数消费与跨源门禁。
真实文件 fixture: tmp_path 里建真 vault 目录 (.obsidian + outputs/今日复习.json
真文件), settings 走 reload_settings 真实配置机器 — 禁 mock 文件系统语义。
"""

import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

# 与生产代码同款退化 (Codex-D1 L1): 无 tzdata 环境收集不崩, 仍可验固定 +8 回退
try:
    from zoneinfo import ZoneInfo

    _SH = ZoneInfo("Asia/Shanghai")
except Exception:  # noqa: BLE001
    _SH = timezone(timedelta(hours=8))


@pytest.fixture(autouse=True)
def _pin_display_tz(monkeypatch):
    """把显示时区钉在 Asia/Shanghai —— 本文件大量期望值用 `_SH` 算 (CARD-G6-9c)。

    本卡把显示侧从硬编码 Asia/Shanghai 收敛到 `display_tz()`(缺省 = 机器本地)。
    而本文件的期望值仍按 `_SH`(= 上海) 算 —— 那是**刻意保留**的: 期望值若改成
    按显示时区现算, 就与被测量同源、缺陷会让两边一起退化 (memory「期望值与被
    测量同源」)。故用 CANVAS_TZ 把被测侧钉到与 `_SH` 同一个时区。

    透传链: `_child_env()` 的白名单含 CANVAS_TZ ⇒ refresh 起的**生产器子进程**
    也拿到同一个值, 父子两侧不分叉。

    ⚠ 测时区行为本身的两条用例 (`test_child_env_*` / `test_child_tz_*`) 会显式
    `delenv("CANVAS_TZ")` 把本夹具让开 —— 它们要看的正是缺省档。
    """
    monkeypatch.setenv("CANVAS_TZ", "Asia/Shanghai")


def _now_local() -> datetime:
    return datetime.now().astimezone()


def _utc_z(dt: datetime) -> str:
    """A2 生产器 fsrs_due 形态: UTC 秒级 Z 后缀。"""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


#: bucket 缺省哨兵: 按 due_reason 推导 (生产器构造律 —— due_nodes 行只可能落
#: 到期三桶, 且 new 桶 ⟺ due_reason=="new")。显式传 bucket 的用例不受影响。
_AUTO_BUCKET = "__auto__"


def _due_row(
    node: str,
    board,
    *,
    due_reason: str = "new",
    fsrs_due: str = "",
    bucket: str | None = _AUTO_BUCKET,
    why_due: str = "新卡未排期，视同即刻到期 · 从未考察",
):
    """daily_review_pick.build_payload due_rows 的全字段真形状
    (CARD-G3-6a 起行尾多 bucket/why_due 两个加性字段)。"""
    if bucket == _AUTO_BUCKET:
        bucket = "new" if due_reason == "new" else "due_now"
    return {
        "node": node,
        "board": board,
        "state": "new",
        "pick": 1.0,
        "fsrs_due": fsrs_due,
        "due_reason": due_reason,
        "last_examined": "",
        "difficulty": "",
        "bucket": bucket,
        "why_due": why_due,
    }


def _bucket_row(node: str, board: str, *, fsrs_due: str = "", why: str = "理由"):
    """daily_review_pick buckets 桶内行的真形状 (四字段)。"""
    return {"node": node, "board": board, "why_due": why, "fsrs_due": fsrs_due}


def _projection(
    vault_id: str,
    *,
    generated_at,
    due: list[str] | None = None,
    placeholder: list[str] | None = None,
    board: str | None = "CS 61B",
    stats_due=None,
    **overrides,
) -> dict:
    """schema v3 形状的最小真投影 (字段名与 daily_review_pick.build_payload
    对齐)。stats_due 可与明细长度解耦 (锁定「读 stats 权威计数、不重数明细」);
    overrides 直接覆盖顶层键, 供敌对形状用例注入垃圾。"""
    due = ["节点甲"] if due is None else due
    top_boards = (
        [
            {
                "board": board,
                "top_node": due[0],
                "priority": 1.0,
                "pending": len(due),
                "idle_days": 3,
                "difficulty": "",
                "next_due": "",
            }
        ]
        if board and due
        else []
    )
    payload = {
        "unassigned_nodes": [],
        "schema_version": 3,
        "vault_id": vault_id,
        # date 恒为合法日历日期 (生产器 date().isoformat() 产物): 敌对
        # generated_at 用例不许顺带把 date 弄脏 — date 垃圾有专属用例
        "date": _now_local().date().isoformat(),
        "generated_at": generated_at,
        "top_boards": top_boards,
        "upcoming": [],
        "due_nodes": [
            {
                "node": n,
                "board": board,
                "state": "new",
                "pick": 1.0,
                "fsrs_due": "",
                "due_reason": "new",
                "last_examined": "",
                "difficulty": "",
            }
            for n in due
        ],
        "ineligible": {"placeholder": placeholder or [], "test_excluded": [], "corrupt": []},
        "stats": {"due_nodes": len(due) if stats_due is None else stats_due},
        "notification": None,
    }
    payload.update(overrides)
    return payload


def _mk_vault(root, name: str, projection: dict | None = None, raw: str | None = None):
    """真目录 + 真文件 — 不 mock 任何文件系统语义。幂等: 同名 vault 重复建不炸
    (CARD-G3-6b 垃圾门用例每轮覆盖写投影)。"""
    vault = root / name
    (vault / ".obsidian").mkdir(parents=True, exist_ok=True)
    if raw is not None or projection is not None:
        (vault / "outputs").mkdir(exist_ok=True)
        text = raw if raw is not None else json.dumps(projection, ensure_ascii=False, indent=2)
        (vault / "outputs" / "今日复习.json").write_text(text, encoding="utf-8")
    return vault


@pytest.fixture
def overview_env(tmp_path):
    """VAULTS_ROOT 指向 tmp 的真实 Settings。

    Codex-C2 HIGH: reload_settings 会永久写 os.environ — teardown 必须按
    「键原先是否存在」恢复 (原不存在的键 pop 掉, 不能只回写值), 且用
    try/finally 保证 TestClient 构造失败时同样恢复。
    """
    import os

    import app.config as config_mod
    import app.main as main_mod
    from app.config import reload_settings

    saved = {k: os.environ.get(k) for k in ("VAULTS_ROOT", "ACTIVE_VAULT")}

    def _sync_main_settings():
        # reload_settings 只重绑 app.config.settings; app.main 按值导入了
        # settings (main.py), reload 后两模块指向不同对象 (split-brain,
        # Codex-C2 HIGH round2) — 前后各同步一次, 本 fixture 生命周期内
        # 与 teardown 后两处恒指同一对象
        main_mod.settings = config_mod.settings

    try:
        reload_settings(overrides={"VAULTS_ROOT": str(tmp_path), "ACTIVE_VAULT": "vault-a"})
        _sync_main_settings()
        from app.main import app

        # base_url 用回环地址而非默认 testserver: refresh 端点有 Host 白名单
        # (只放行 localhost 与 IP 字面量, 防 DNS rebinding), 默认的 testserver
        # 是个主机名, 会被正确地挡掉
        yield tmp_path, TestClient(app, base_url="http://127.0.0.1:8011")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        reload_settings()  # 无 overrides: 只按恢复后的 env 重建缓存/全局
        _sync_main_settings()


def test_aggregates_multiple_vaults(overview_env):
    """聚合正确: N=2 真投影 → 每库一条 ok 条目; due_count 取 stats 权威值
    (与明细长度刻意解耦 — 重数明细的错误实现会在 vault-b 上露馅)。"""
    root, client = overview_env
    now_iso = _now_local().isoformat(timespec="seconds")
    _mk_vault(
        root,
        "vault-a",
        _projection(
            "vault-a", generated_at=now_iso, due=["甲", "乙"], placeholder=["积压1", "积压2", "积压3"], board="CS 61B"
        ),
    )
    # stats.due_nodes=7 而明细只有 1 条 — 权威计数在 stats (A2 构造同源)
    _mk_vault(root, "vault-b", _projection("vault-b", generated_at=now_iso, due=["丙"], board="数学", stats_due=7))

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert [v["vault_id"] for v in data["vaults"]] == ["vault-a", "vault-b"]
    a, b = data["vaults"]
    assert a["status"] == "ok" and b["status"] == "ok"
    assert a["projection"]["due_count"] == 2
    assert a["projection"]["placeholder_backlog"] == 3
    assert a["projection"]["recommended_board"] == "CS 61B"
    assert b["projection"]["due_count"] == 7, "必须读 stats 权威计数, 不得重数明细"
    assert b["projection"]["recommended_board"] == "数学"


def test_missing_projection_explicit_degraded_entry(overview_env):
    """缺投影 vault 必须以显式 no_projection 条目出现, 禁静默跳过;
    非 vault 目录 (无 .obsidian) 不进列表。"""
    root, client = overview_env
    _mk_vault(root, "vault-a", _projection("vault-a", generated_at=_now_local().isoformat(timespec="seconds")))
    _mk_vault(root, "vault-new")  # 有 .obsidian, 无投影
    (root / "not-a-vault").mkdir()  # 无 .obsidian → 不枚举

    data = client.get("/api/v1/review/overview").json()
    assert [v["vault_id"] for v in data["vaults"]] == ["vault-a", "vault-new"]
    degraded = data["vaults"][1]
    assert degraded["status"] == "no_projection"
    assert degraded["projection"] is None

    # 降级条目在页面上也必须可见 (显式"无投影"卡片)
    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    assert "vault-new" in page.text and "无投影" in page.text


def test_corrupt_projection_does_not_500(overview_env):
    """损坏 JSON / schema 形状垃圾 → 单库 corrupt 降级, 全局仍 200,
    健康库不受拖累。敌对形状全清单 (Codex-C2 B3): 非 v3 版本、嵌套容器
    垃圾、bool/字符串计数、非标准 JSON 常量——一个都不许发 ok。"""
    root, client = overview_env
    now_iso = _now_local().isoformat(timespec="seconds")
    _mk_vault(root, "vault-a", _projection("vault-a", generated_at=now_iso))
    hostile = {
        "bad-syntax": "{ 这不是合法 JSON",
        "bad-root": '["根节点不是object"]',
        "bad-version": json.dumps(_projection("x", generated_at=now_iso, schema_version=2)),
        "bad-stats-list": json.dumps(_projection("x", generated_at=now_iso, stats=[])),
        "bad-due-nodes": json.dumps(_projection("x", generated_at=now_iso, due_nodes="garbage")),
        "bad-count-bool": json.dumps(_projection("x", generated_at=now_iso, stats_due=True)),
        "bad-count-str": json.dumps(_projection("x", generated_at=now_iso, stats_due="99")),
        "bad-placeholder": json.dumps(
            _projection(
                "x", generated_at=now_iso, ineligible={"placeholder": "abc", "test_excluded": [], "corrupt": []}
            )
        ),
        "bad-nan": json.dumps(_projection("x", generated_at=now_iso)).replace('"pick": 1.0', '"pick": NaN'),
        "bad-genat-num": json.dumps(_projection("x", generated_at=20260825)),
        # round2: 标准数字 1e999 经 parse_float 变 inf — 非有限数拒收
        "bad-inf": json.dumps(_projection("x", generated_at=now_iso)).replace('"pick": 1.0', '"pick": 1e999'),
        # round2: 嵌套元素形状垃圾 (upcoming[0] 非 object 会被透传进响应)
        "bad-upcoming-elem": json.dumps(_projection("x", generated_at=now_iso, upcoming=["not-an-object"])),
        # round3: upcoming[0] 是 object 但内部字段类型垃圾 — 透传面必须
        # 逐字段门禁, 整对象透传即形状垃圾通道
        "bad-upcoming-fields": json.dumps(
            _projection("x", generated_at=now_iso, upcoming=[{"board": [], "next_due": False, "node": {"a": 1}}])
        ),
        "bad-pending-str": json.dumps(
            _projection("x", generated_at=now_iso, top_boards=[{"board": "B", "top_node": "n", "pending": "many"}])
        ),
        # ── CARD-D1 round2 (Codex-D1 H2/H5) ──
        # JSON "\ud800" 转义解出孤立 surrogate — 响应 UTF-8 序列化才炸,
        # 必须在解析层折断 (默认 ensure_ascii=True 才能把它写成合法文件)
        "bad-surrogate": json.dumps(_projection("x", generated_at=now_iso, board="孤\ud800板")),
        # 显式 null 不是"旧投影缺省" — 生产器恒产出数组
        "bad-boards-null": json.dumps(_projection("x", generated_at=now_iso, boards=None)),
        # 重复 due 行会被静默重复计数
        "bad-dup-due": json.dumps(_projection("x", generated_at=now_iso, due=["同名", "同名"])),
        "bad-node-empty": json.dumps(_projection("x", generated_at=now_iso, due_nodes=[_due_row("", "板")])),
        # 重复 top 板会让后续板与非 top 板共享排序优先级
        "bad-dup-top": json.dumps(
            _projection(
                "x",
                generated_at=now_iso,
                top_boards=[
                    {"board": "B", "top_node": "n", "pending": 1},
                    {"board": "B", "top_node": "n", "pending": 1},
                ],
            )
        ),
        "bad-dup-upcoming": json.dumps(
            _projection(
                "x",
                generated_at=now_iso,
                upcoming=[
                    {"board": "U", "next_due": "2026-09-01T00:00:00Z", "node": "a"},
                    {"board": "U", "next_due": "2026-09-02T00:00:00Z", "node": "b"},
                ],
            )
        ),
        "bad-placeholder-elems": json.dumps(
            _projection(
                "x", generated_at=now_iso, ineligible={"placeholder": [123], "test_excluded": [], "corrupt": []}
            )
        ),
        # ── round2 (Codex-D1 复核残留) ──
        "bad-date-garbage": json.dumps(_projection("x", generated_at=now_iso, date="不是日期")),
        "bad-date-month13": json.dumps(_projection("x", generated_at=now_iso, date="2026-13-01")),
        "bad-top-empty-board": json.dumps(
            _projection("x", generated_at=now_iso, top_boards=[{"board": "", "top_node": "n", "pending": 1}])
        ),
        "bad-upcoming-node-empty": json.dumps(
            _projection(
                "x", generated_at=now_iso, upcoming=[{"board": "U", "next_due": "2026-09-01T00:00:00Z", "node": ""}]
            )
        ),
    }
    for name, raw in hostile.items():
        _mk_vault(root, name, raw=raw)
    # 权限拒绝 → corrupt (读文件 OSError 路径)。root/提权 CI 无视权限位,
    # 该场景只在普通用户下有效 — root 时跳过此库
    run_perm_case = os.geteuid() != 0
    if run_perm_case:
        denied = _mk_vault(root, "bad-perm", _projection("x", generated_at=now_iso))
        (denied / "outputs" / "今日复习.json").chmod(0o000)
    # 目录冒充投影文件 → corrupt (IsADirectoryError 路径)
    isdir = root / "bad-isdir"
    (isdir / ".obsidian").mkdir(parents=True)
    (isdir / "outputs" / "今日复习.json").mkdir(parents=True)
    hostile["bad-isdir"] = ""
    if run_perm_case:
        hostile["bad-perm"] = ""

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200
    by_id = {v["vault_id"]: v for v in resp.json()["vaults"]}
    assert by_id["vault-a"]["status"] == "ok", "健康库不得被邻居垃圾拖累"
    for name in hostile:
        assert by_id[name]["status"] == "corrupt", f"{name} 形状垃圾必须 corrupt, 实为 {by_id[name]['status']}"
        assert by_id[name]["error"]

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    assert "投影损坏" in page.text


def test_stale_badge_from_generated_at(overview_env):
    """stale 判定基于投影自带 generated_at (非文件 mtime): 昨天 → stale,
    今天 (mtime 刻意回拨到一周前) → 仍 ok — 证明不读 mtime; 宽松格式
    (纯日期/无时区/畸形/极端溢出值) 一律 stale, 不许冒充今日新鲜
    (Codex-C2 B1/B2), 且极端时区值不得 500。"""
    root, client = overview_env
    now = _now_local()
    today_iso = now.isoformat(timespec="seconds")
    _mk_vault(
        root, "vault-a", _projection("vault-a", generated_at=(now - timedelta(days=1)).isoformat(timespec="seconds"))
    )
    fresh = _mk_vault(root, "vault-b", _projection("vault-b", generated_at=today_iso))
    # runner 会把投影 mtime 回拨到扫描起点 — mtime 一周前 + generated_at
    # 今天, 实现若偷看 mtime 会误判 stale
    week_ago = (now - timedelta(days=7)).timestamp()
    os.utime(fresh / "outputs" / "今日复习.json", (week_ago, week_ago))
    today_naive = now.replace(tzinfo=None).isoformat(timespec="seconds")
    lax = {
        "lax-garbage": "不是时间",
        "lax-date-only": now.date().isoformat(),
        "lax-no-tz": today_naive,
        "lax-overflow": "9999-12-31T23:59:59-23:59",  # astimezone 溢出 → 不得 500
        # round2: 非法 offset 分钟被 fromisoformat 静默归一化 (+08:60→+09:00)
        # — A2 生产器绝不会产出, 必须 stale
        "lax-bad-offset-60": f"{today_naive}+08:60",
        "lax-bad-offset-99": f"{today_naive}+08:99",
        "lax-bad-offset-15h": f"{today_naive}+15:00",
    }
    for name, gen in lax.items():
        _mk_vault(root, name, _projection(name, generated_at=gen))

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200, "极端时区值不得把全局打成 500"
    by_id = {v["vault_id"]: v for v in resp.json()["vaults"]}
    assert by_id["vault-a"]["status"] == "stale"
    assert by_id["vault-b"]["status"] == "ok", "mtime 回拨不得影响判定 (只看 generated_at)"
    for name in lax:
        assert by_id[name]["status"] == "stale", f"{name} 宽松格式必须 stale, 实为 {by_id[name]['status']}"

    page = client.get("/api/v1/review/overview/page").text
    assert "过期投影" in page and "今日投影" in page


def test_readonly_contract_files_untouched(overview_env):
    """只读契约: 两个端点请求前后, 投影文件字节与 mtime 逐一不变。"""
    root, client = overview_env
    vault = _mk_vault(root, "vault-a", _projection("vault-a", generated_at=_now_local().isoformat(timespec="seconds")))
    proj = vault / "outputs" / "今日复习.json"
    pinned = 1_700_000_000
    os.utime(proj, (pinned, pinned))
    before_bytes = proj.read_bytes()

    assert client.get("/api/v1/review/overview").status_code == 200
    assert client.get("/api/v1/review/overview/page").status_code == 200

    assert proj.read_bytes() == before_bytes
    assert proj.stat().st_mtime == pinned, "端点不得触碰投影文件 (含 mtime)"


def test_page_is_self_contained_with_obsidian_links(overview_env):
    """页面硬约束: 零外部 CDN (无外链 script/css/img), obsidian:// 跳转链接,
    text/html 响应头。"""
    root, client = overview_env
    _mk_vault(root, "vault-a", _projection("vault-a", generated_at=_now_local().isoformat(timespec="seconds")))

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    text = page.text
    assert "obsidian://open?vault=vault-a" in text
    # "<script" 含内联脚本 (Codex-D1 L2: 只拦 <script src= 挡不住内联 JS)
    for marker in ("<script", "<link ", 'src="http', "src='http", 'href="http', "href='http"):
        assert marker not in text.lower(), f"外部资源/JS 引用泄漏: {marker}"


# ── CARD-D1: 总览页 Anki 化 (BATCH-2026-08-27-Anki化与诚实收尾) ──


def test_board_table_groupby_matches_stats(overview_env):
    """板级聚合自洽: 到期数由 due_nodes group-by 得出且合计==stats.due_nodes;
    行序 = 有到期板按 top_boards 优先级 (乙板列首位则排前) → 零到期板按
    next_due 垫底; 板名深链 percent-encode 指向 原白板/<板名>.md。"""
    root, client = overview_env
    now = _now_local()
    rows = [
        _due_row("n1", "甲板"),
        _due_row("n2", "甲板", due_reason="scheduled", fsrs_due=_utc_z(now - timedelta(days=3))),
        _due_row("n3", "乙板", due_reason="scheduled", fsrs_due=_utc_z(now - timedelta(days=1))),
    ]
    _mk_vault(
        root,
        "vault-a",
        _projection(
            "vault-a",
            generated_at=now.isoformat(timespec="seconds"),
            due_nodes=rows,
            stats={"due_nodes": 3},
            top_boards=[
                {"board": "乙板", "top_node": "n3", "pending": 1},
                {"board": "甲板", "top_node": "n1", "pending": 2},
            ],
            upcoming=[{"board": "丙板", "next_due": _utc_z(now + timedelta(days=2)), "node": "nx"}],
        ),
    )

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200
    entry = resp.json()["vaults"][0]
    assert entry["status"] == "ok"
    p = entry["projection"]
    assert [r["board"] for r in p["boards"]] == ["乙板", "甲板", "丙板"], "top_boards 优先级先行, 零到期垫底"
    by = {r["board"]: r for r in p["boards"]}
    assert by["甲板"]["due"] == 2 and by["甲板"]["due_new"] == 1
    # 新卡+逾期混板: 最早到期取逾期时间戳 (3 天前比"现在"更紧迫), 不许
    # 被新卡空串 (=现在) 盖掉 — 空串只在全新卡板上成立
    assert by["甲板"]["earliest"] == _utc_z(now - timedelta(days=3))
    assert by["乙板"]["earliest"] == _utc_z(now - timedelta(days=1))
    assert by["乙板"]["due"] == 1 and by["乙板"]["due_new"] == 0
    assert by["丙板"]["due"] == 0 and by["丙板"]["due_new"] == 0
    assert sum(r["due"] for r in p["boards"]) == p["due_count"] == 3, "板级合计必须==stats.due_nodes"
    assert p["due_new_count"] == 1

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    text = page.text
    for col in ("白板名", "到期", "新卡", "待剖析", "最早到期"):
        assert col in text, f"板表格缺列头 {col}"
    for board in ("甲板", "乙板", "丙板"):
        # HTML 属性里 & 合法转义为 &amp; — 断言对齐落页形态
        link = "obsidian://open?vault=vault-a&amp;file=" + quote(f"原白板/{board}.md", safe="")
        assert link in text, f"{board} 深链缺失或未按 percent-encode 约定"


def test_due_nodes_dirty_rows_degrade_corrupt_not_500(overview_env):
    """due_nodes 行级门禁: 行不是 object / board 非法 / due_reason 枚举外 /
    fsrs_due 非生产器形态或日历非法 / due_reason 与 fsrs_due 不自洽 —
    一律按既有 corrupt 语义降级, 全局 200, 健康库不受拖累。"""
    root, client = overview_env
    now_iso = _now_local().isoformat(timespec="seconds")
    _mk_vault(root, "vault-a", _projection("vault-a", generated_at=now_iso))
    dirty = {
        "row-not-object": [["不是对象"]],
        "board-not-str": [_due_row("n", 123)],
        "board-empty": [_due_row("n", "")],
        "reason-garbage": [_due_row("n", "板", due_reason="whenever")],
        "fsrs-offset-form": [_due_row("n", "板", due_reason="scheduled", fsrs_due="2026-08-01T00:00:00+08:00")],
        "fsrs-calendar-invalid": [_due_row("n", "板", due_reason="scheduled", fsrs_due="2026-13-01T00:00:00Z")],
        "reason-fsrs-mismatch": [_due_row("n", "板", due_reason="scheduled", fsrs_due="")],
    }
    for name, rows in dirty.items():
        _mk_vault(root, name, _projection(name, generated_at=now_iso, due_nodes=rows))

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200
    by_id = {v["vault_id"]: v for v in resp.json()["vaults"]}
    assert by_id["vault-a"]["status"] == "ok", "健康库不得被邻居脏行拖累"
    for name in dirty:
        assert by_id[name]["status"] == "corrupt", f"{name} 脏行必须 corrupt, 实为 {by_id[name]['status']}"
        assert by_id[name]["error"]


def test_time_humanization_asia_shanghai(overview_env):
    """时间人话化: 统一转 Asia/Shanghai, 逾期N天/现在/明天/N天后/M月D日;
    页面生成时间显示上海本地时区, UTC 裸串 (+00:00) 不得出现在页面
    (现网容器 UTC 缺陷的回归锁定)。"""
    root, client = overview_env
    now = datetime.now(timezone.utc)
    far = now + timedelta(days=40)
    _mk_vault(
        root,
        "vault-a",
        _projection(
            "vault-a",
            generated_at=now.isoformat(timespec="seconds"),
            due_nodes=[
                _due_row("逾", "逾期板", due_reason="scheduled", fsrs_due=_utc_z(now - timedelta(days=3))),
                _due_row("新", "新卡板"),
                # 日历合法极值: strptime 过门禁但 astimezone(+8) 年份溢出
                # OverflowError — 渲染须降级 "—" 不许 500
                _due_row("极", "极值板", due_reason="scheduled", fsrs_due="9999-12-31T23:59:59Z"),
            ],
            stats={"due_nodes": 3},
            top_boards=[
                {"board": "逾期板", "top_node": "逾", "pending": 1},
                {"board": "新卡板", "top_node": "新", "pending": 1},
            ],
            upcoming=[
                {"board": "明日板", "next_due": _utc_z(now + timedelta(days=1)), "node": "a"},
                {"board": "五日板", "next_due": _utc_z(now + timedelta(days=5)), "node": "b"},
                {"board": "远期板", "next_due": _utc_z(far), "node": "c"},
            ],
        ),
    )

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200, "日历合法极值不得把页面打成 500"
    text = page.text
    assert "极值板" in text  # 溢出值降级 "—" 成行, 不消失也不 500
    assert "逾期3天" in text
    assert "现在" in text  # 新卡板 (fsrs_due 空串 = 即刻到期)
    assert "明天" in text
    assert "5天后" in text
    far_sh = far.astimezone(_SH)
    expected_far = (
        f"{far_sh.month}月{far_sh.day}日"
        if far_sh.year == now.astimezone(_SH).year
        else f"{far_sh.year}年{far_sh.month}月{far_sh.day}日"
    )
    assert expected_far in text, "超过一周的未来到期应显示日历日期"
    assert "(UTC+8)" in text, "页面生成时间必须标注上海本地时区"
    assert now.astimezone(_SH).strftime("%Y-%m-%d") in text
    assert "+00:00" not in text, "UTC 裸串不得漏进页面 (现网缺陷)"


def test_no_projection_degrades_without_fake_deeplink(overview_env):
    """无投影 vault: 显式降级文案, 不做假链接; 页面带"需在 Obsidian 打开过
    该库"提示 (test-vault 死链与同名库跳错的诚实降级)。"""
    root, client = overview_env
    _mk_vault(root, "vault-a", _projection("vault-a", generated_at=_now_local().isoformat(timespec="seconds")))
    _mk_vault(root, "vault-new")  # 有 .obsidian, 无投影

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    text = page.text
    assert "obsidian://open?vault=vault-a" in text
    assert "obsidian://open?vault=vault-new" not in text, "无投影 vault 不得出假链接"
    assert "需在 Obsidian 打开过该库" in text


def test_boards_rollup_consumed_when_present(overview_env):
    """P1 rollup 在场: 待剖析列取板级归属; 零到期板走 rollup 全量 (不再受
    upcoming[:3] 截断); 占位符专属板成行 (最早到期无数据 → null); rollup
    形状垃圾按既有 corrupt 语义降级。rollup 缺省 (旧投影) 时上述回落 P0
    派生路径 — 由其余测试覆盖。"""
    root, client = overview_env
    now = _now_local()
    rollup = [
        {
            "board": "甲板",
            "due": 1,
            "due_new": 1,
            "due_scheduled": 0,
            "future": 0,
            "next_due": "",
            "placeholder": 2,
            "earliest_overdue": "",
        },
        {
            "board": "乙板",
            "due": 0,
            "due_new": 0,
            "due_scheduled": 0,
            "future": 1,
            "next_due": _utc_z(now + timedelta(days=3)),
            "placeholder": 0,
            "earliest_overdue": "",
        },
        {
            "board": "丙板",
            "due": 0,
            "due_new": 0,
            "due_scheduled": 0,
            "future": 1,
            "next_due": _utc_z(now + timedelta(days=2)),
            "placeholder": 0,
            "earliest_overdue": "",
        },
        {
            "board": "丁板",
            "due": 0,
            "due_new": 0,
            "due_scheduled": 0,
            "future": 0,
            "next_due": "",
            "placeholder": 3,
            "earliest_overdue": "",
        },
    ]
    _mk_vault(
        root,
        "vault-a",
        _projection(
            "vault-a",
            generated_at=now.isoformat(timespec="seconds"),
            due_nodes=[_due_row("n1", "甲板")],
            stats={"due_nodes": 1},
            # 扁平 6 条 vs 板级归属 5 (2+3) — 差额 1 = 无 source_board 占位符
            placeholder=[f"p{i}" for i in range(6)],
            top_boards=[{"board": "甲板", "top_node": "n1", "pending": 1}],
            # upcoming 只截到丙板 — 乙板/丁板必须由 rollup 补全
            upcoming=[{"board": "丙板", "next_due": rollup[2]["next_due"], "node": "x"}],
            boards=rollup,
        ),
    )
    _mk_vault(
        root,
        "bad-rollup",
        _projection(
            "bad-rollup",
            generated_at=now.isoformat(timespec="seconds"),
            boards=[{"board": "x", "due": -1}],
        ),
    )
    # 跨源一致性 (Codex-D1 H4): rollup 声称的到期板集合/计数必须与 due_nodes
    # 明细相等; 板级 placeholder 合计不得超过扁平总数
    _mk_vault(
        root,
        "bad-rollup-due-drift",
        _projection(
            "bad-rollup-due-drift",
            generated_at=now.isoformat(timespec="seconds"),
            due_nodes=[_due_row("n1", "甲板")],
            boards=[
                {
                    "board": "甲板",
                    "due": 2,
                    "due_new": 2,
                    "due_scheduled": 0,
                    "future": 0,
                    "next_due": "",
                    "placeholder": 0,
                    "earliest_overdue": "",
                },
            ],
        ),
    )
    _mk_vault(
        root,
        "bad-rollup-ghost-board",
        _projection(
            "bad-rollup-ghost-board",
            generated_at=now.isoformat(timespec="seconds"),
            due_nodes=[_due_row("n1", "甲板")],
            boards=[],  # 声称无到期板但明细有 — 整板会静默消失
        ),
    )
    _mk_vault(
        root,
        "bad-rollup-ph-overflow",
        _projection(
            "bad-rollup-ph-overflow",
            generated_at=now.isoformat(timespec="seconds"),
            due_nodes=[_due_row("n1", "甲板")],
            boards=[
                {
                    "board": "甲板",
                    "due": 1,
                    "due_new": 1,
                    "due_scheduled": 0,
                    "future": 0,
                    "next_due": "",
                    "placeholder": 999,
                    "earliest_overdue": "",
                },
            ],
        ),
    )

    # round2 (Codex-D1 复核残留): 构造律旁路四连 — 全零幽灵板 / future 与
    # next_due 不自洽 / due 三分越界 / due_new 与明细漂移
    _base_row = {
        "due": 0,
        "due_new": 0,
        "due_scheduled": 0,
        "future": 0,
        "next_due": "",
        "placeholder": 0,
        "earliest_overdue": "",
    }
    _good_row = {**_base_row, "board": "甲板", "due": 1, "due_new": 1}
    round2_bad = {
        "bad-rollup-allzero": [_good_row, {**_base_row, "board": "幽灵板"}],
        "bad-rollup-no-nextdue": [_good_row, {**_base_row, "board": "怪板", "future": 2}],
        "bad-rollup-partition": [{**_good_row, "due_new": 1, "due_scheduled": 1}],
        "bad-rollup-new-drift": [{**_good_row, "due_new": 0, "due_scheduled": 1}],
    }
    for name, rollup_rows in round2_bad.items():
        _mk_vault(
            root,
            name,
            _projection(
                name,
                generated_at=now.isoformat(timespec="seconds"),
                due_nodes=[_due_row("n1", "甲板")],
                boards=rollup_rows,
            ),
        )
    # 纯无主占位符 (M1 残留): boards 为空数组但扁平列表有 2 条 —
    # 汇总行必须标注差额, 不许因无板行而错误置零
    _mk_vault(
        root,
        "vault-unattr",
        _projection(
            "vault-unattr",
            generated_at=now.isoformat(timespec="seconds"),
            due_nodes=[],
            stats={"due_nodes": 0},
            top_boards=[],
            upcoming=[],
            placeholder=["无主1", "无主2"],
            boards=[],
        ),
    )

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200
    by_id = {v["vault_id"]: v for v in resp.json()["vaults"]}
    assert by_id["bad-rollup"]["status"] == "corrupt", "rollup 形状垃圾必须 corrupt"
    for name in ("bad-rollup-due-drift", "bad-rollup-ghost-board", "bad-rollup-ph-overflow", *round2_bad):
        assert by_id[name]["status"] == "corrupt", f"{name} 跨源不一致必须 corrupt"
    assert by_id["vault-unattr"]["status"] == "ok"
    assert by_id["vault-unattr"]["projection"]["placeholder_attributed"] == 0
    entry = by_id["vault-a"]
    assert entry["status"] == "ok"
    p = entry["projection"]
    assert [r["board"] for r in p["boards"]] == ["甲板", "丙板", "乙板", "丁板"], (
        "到期板先行, 零到期板按 next_due 升序, 无排期垫底"
    )
    by = {r["board"]: r for r in p["boards"]}
    assert by["甲板"]["placeholder"] == 2 and by["甲板"]["due"] == 1
    assert by["乙板"]["due"] == 0 and by["乙板"]["placeholder"] == 0
    assert by["丁板"]["placeholder"] == 3 and by["丁板"]["earliest"] is None
    assert sum(r["due"] for r in p["boards"]) == p["due_count"] == 1

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    assert "丁板" in page.text and "乙板" in page.text
    # Codex-D1 M1: 无归属占位符差额必须在汇总行标注, 否则汇总 6 vs 板级
    # 合计 5 无法对账; 纯无主占位符 (boards 空) 时差额同样不许被置零
    assert "含未归板 1" in page.text
    assert "含未归板 2" in page.text, "纯无主占位符 vault 的差额注记不许因板行为空而消失"


def test_humanize_due_shanghai_midnight_semantics():
    """跨午夜语义直测 (Codex-D1 M3): now = 上海 2026-08-28 00:30 (UTC 还在
    08-27 16:30) — 上海本地日与 UTC 日错位的窗口, 按 UTC 日判定的实现在
    这三条上必然翻车。纯函数直测, 不经 HTTP 不读时钟, 零闪断。"""
    from app.api.v1.endpoints.review_overview import _humanize_due

    now_sh = datetime(2026, 8, 27, 16, 30, tzinfo=timezone.utc)  # 上海 08-28 00:30
    # due 上海 08-28 01:00: 同上海日 → 现在 (按 UTC 日会误判成逾期)
    assert _humanize_due("2026-08-27T17:00:00Z", now_sh)[0] == "现在"
    # due 上海 08-27 23:00: 上海昨日 → 逾期1天 (按 UTC 日会误判成"现在")
    assert _humanize_due("2026-08-27T15:00:00Z", now_sh)[0] == "逾期1天"
    # due 上海 08-29 00:30 → 明天
    assert _humanize_due("2026-08-28T16:30:00Z", now_sh)[0] == "明天"
    assert _humanize_due("", now_sh)[0] == "现在"
    assert _humanize_due(None, now_sh)[0] == "—"
    assert _humanize_due("9999-12-31T23:59:59Z", now_sh)[0] == "—", "极值溢出降级不炸"


def _sh_at(day, hour: int, minute: int = 0) -> datetime:
    """指定上海本地日的某时刻 (aware) —— 判桶门禁按上海日算, fixture 必须
    显式构造上海日边界, 不能用 now±N 天糊过去 (Codex round-2 D)。"""
    from datetime import time as _time

    return datetime.combine(day, _time(hour, minute), tzinfo=_SH)


def test_buckets_layer_counts_and_cross_source_gate(overview_env):
    """CARD-G3-6a 加性 buckets 消费 (BATCH-2026-08-29-第六批)。

    ① 正常投影: 五桶计数进 JSON (bucket_counts) 与页面「分层」汇总行;
    ② 旧投影无 buckets 键 → 仍 ok 且 bucket_counts=null (加性不倒逼迁移);
    ③ 跨源不一致一律 corrupt 降级 —— 含 Codex round-1/round-2 指出的两类
       身份级旁路: 到期三桶靠与 due_nodes 的成员恒等堵, 非到期两桶在
       due_nodes 里没有对手盘, 改靠「以 generated_at 为参照时钟重算桶判据」
       + 「与 boards rollup 逐板对账」双路堵。

    时钟基准全部由 generated_at 显式给定 (上海今日 08:00), 与运行时刻无关 —
    due_today 取同日 23:00, future 取次日 09:00, 跨午夜运行也不漂。
    """
    root, client = overview_env
    sh_today = datetime.now(_SH).date()
    gen = _sh_at(sh_today, 8)
    gen_iso = gen.isoformat(timespec="seconds")
    overdue = _utc_z(gen - timedelta(days=3))
    today_late = _utc_z(_sh_at(sh_today, 23))
    tomorrow = _utc_z(_sh_at(sh_today + timedelta(days=1), 9))
    W_NEW = "新卡未排期，视同即刻到期 · 从未考察"
    W_LEARN = "学习中 · 已逾期 3 天 · 从未考察"
    W_DUE = "到期待复习 · 已逾期 3 天 · 从未考察"
    rows = [
        _due_row("n1", "甲板"),
        _due_row("n2", "甲板", due_reason="scheduled", fsrs_due=overdue, bucket="learning_queue", why_due=W_LEARN),
        _due_row("n3", "乙板", due_reason="scheduled", fsrs_due=overdue, bucket="due_now", why_due=W_DUE),
    ]
    good = {
        "new": [_bucket_row("n1", "甲板", why=W_NEW)],
        "learning_queue": [_bucket_row("n2", "甲板", fsrs_due=overdue, why=W_LEARN)],
        "due_now": [_bucket_row("n3", "乙板", fsrs_due=overdue, why=W_DUE)],
        "due_today": [_bucket_row("f1", "丙板", fsrs_due=today_late, why="今天 23:00 到期（尚未到点）")],
        "future": [_bucket_row("f2", "丙板", fsrs_due=tomorrow, why="明天 09:00 到期")],
    }
    _blank = {
        "due": 0,
        "due_new": 0,
        "due_scheduled": 0,
        "future": 0,
        "next_due": "",
        "placeholder": 0,
        "earliest_overdue": "",
    }
    rollup = [
        {**_blank, "board": "甲板", "due": 2, "due_new": 1, "due_scheduled": 1, "earliest_overdue": overdue},
        {**_blank, "board": "乙板", "due": 1, "due_scheduled": 1, "earliest_overdue": overdue},
        {**_blank, "board": "丙板", "future": 2, "next_due": today_late},
    ]
    stats = {"due_nodes": 3, "future_nodes": 2}
    tops = [{"board": "甲板", "top_node": "n1", "pending": 2}]
    # 零到期板的最早到期节点 —— 投影内唯一另一处点名非到期节点的地方
    upcoming = [{"board": "丙板", "next_due": today_late, "node": "f1"}]

    def _mk(
        name, *, buckets, due_nodes=rows, st=stats, boards=rollup, generated_at=gen_iso, up=upcoming, drop_boards=False
    ):
        proj = _projection(
            name,
            generated_at=generated_at,
            due_nodes=due_nodes,
            stats=st,
            top_boards=tops,
            upcoming=up,
            boards=boards,
            buckets=buckets,
            # CARD-G6-9c-R2: 现役生产器 (daily_review_pick) **恒写** display_tz, 夹具
            # 跟上它。缺这个键（或值为 null）的投影现在**整份判 corrupt** —— 没有生产者
            # 时区就无法可靠重算归桶, 固定偏移只在 generated_at 那一刻可信。
            # 本用例要测的是五桶计数与跨源一致性, 不是「旧投影无 display_tz 怎么归桶」;
            # 后者由 test_g6_9c_single_tz_source.py 的两条桶位门专门守。
            display_tz="Asia/Shanghai",
        )
        if drop_boards:
            proj.pop("boards")
        _mk_vault(root, name, proj)

    _mk("vault-buckets", buckets=good)
    # 旧投影: 无 buckets 键 → 不降级, 只是没有分层数据
    _mk_vault(root, "vault-nobuckets", _projection("vault-nobuckets", generated_at=gen_iso))

    # ── 形状层旁路 ──
    shape_bad: dict[str, object] = {
        "bad-buckets-null": None,  # 显式 null 不是"旧投影缺省", 是形状垃圾
        "bad-buckets-keys": {k: v for k, v in good.items() if k != "future"},
        "bad-buckets-row": {**good, "due_today": [{**good["due_today"][0], "why_due": ""}]},
        # S1 互斥被打破: n1 同时出现在 new 与 due_now
        "bad-buckets-dup": {**good, "due_now": [*good["due_now"], _bucket_row("n1", "甲板", why=W_NEW)]},
        # 未到期桶的 fsrs_due 不得为空 (空串 ⟹ 恒 due_now)
        "bad-buckets-empty-future-ts": {**good, "due_today": [_bucket_row("f1", "丙板", why="x")]},
        # 非到期两桶合计与 stats.future_nodes 漂移
        "bad-buckets-future-drift": {**good, "future": []},
    }
    for name, b in shape_bad.items():
        _mk(name, buckets=b)

    # ── 到期三桶: 身份/语义层旁路 (Codex round-1 HIGH: 逐板计数全不变, 只换身份) ──
    _mk(
        "bad-buckets-identity",
        buckets={
            **good,
            "new": [_bucket_row("FAKE-1", "甲板", why=W_NEW)],
            "learning_queue": [_bucket_row("FAKE-2", "甲板", fsrs_due=overdue, why=W_LEARN)],
            "due_now": [_bucket_row("FAKE-3", "乙板", fsrs_due=overdue, why=W_DUE)],
        },
    )
    # 行内 bucket 与所在桶矛盾 (n2 在 learning_queue, 行却自称 due_now)
    _mk("bad-buckets-label-conflict", buckets=good, due_nodes=[rows[0], {**rows[1], "bucket": "due_now"}, rows[2]])
    # 行内 why_due 与桶内不一致 (两处表示不同源)
    _mk("bad-buckets-why-conflict", buckets=good, due_nodes=[rows[0], {**rows[1], "why_due": "另一套说法"}, rows[2]])
    # new 桶成员实为已排期卡 (语义反例, 且逐板计数不变)
    _mk(
        "bad-buckets-new-semantics",
        buckets={
            **good,
            "new": [_bucket_row("n2", "甲板", fsrs_due=overdue, why=W_LEARN)],
            "learning_queue": [_bucket_row("n1", "甲板", why=W_NEW)],
        },
        due_nodes=[{**rows[0], "bucket": "learning_queue"}, {**rows[1], "bucket": "new"}, rows[2]],
    )
    # 到期三桶合计与 stats.due_nodes 权威计数漂移
    _mk("bad-buckets-stats-drift", buckets=good, st={"due_nodes": 9, "future_nodes": 2})

    # ── 非到期两桶: 身份/语义层旁路 (Codex round-2 HIGH — 上一轮的残留面) ──
    # 纯时间反例: 身份不变、只把 due_today 的时刻挪到远期 → 违反"同上海日"
    # (Codex round-3 LOW: 与身份反例拆开, 一个失败条件不掩盖另一个)
    _mk(
        "bad-buckets-nondue-wrong-day",
        buckets={
            **good,
            "due_today": [_bucket_row("f1", "丙板", fsrs_due="2099-01-01T00:00:00Z", why="x")],
        },
    )
    # 纯身份反例 (Codex round-3 HIGH): 同板、同时刻、同 why_due, 只换节点名 —
    # 时间判据与逐板对账全部通过, 只有 upcoming 身份对账能挡下
    _mk(
        "bad-buckets-nondue-identity",
        buckets={
            **good,
            "due_today": [_bucket_row("FAKE-4", "丙板", fsrs_due=today_late, why="今天 23:00 到期（尚未到点）")],
        },
    )
    # upcoming 的 next_due 与桶内该节点时刻不一致
    _mk("bad-buckets-upcoming-ts-drift", buckets=good, up=[{"board": "丙板", "next_due": tomorrow, "node": "f1"}])
    # 清空 upcoming 想整体跳过身份对账 (Codex round-4 HIGH): 条数必须由 rollup 复算
    _mk("bad-buckets-upcoming-emptied", buckets=good, up=[])
    # upcoming 换成一个「有到期节点」的板 (甲板) —— 不符合零到期资格
    _mk("bad-buckets-upcoming-wrong-board", buckets=good, up=[{"board": "甲板", "next_due": today_late, "node": "n1"}])
    # 未来时刻伪装成 due_now (两处 fsrs_due 同步改, 逐板计数不变) —
    # 靠到期侧时间逆检查挡下 (Codex round-4 HIGH)
    _mk(
        "bad-buckets-due-future-ts",
        buckets={**good, "due_now": [_bucket_row("n3", "乙板", fsrs_due=today_late, why=W_DUE)]},
        due_nodes=[rows[0], rows[1], {**rows[2], "fsrs_due": today_late}],
    )
    # buckets 在场但 boards 缺席 —— 非任何历史形态 (Codex round-3 HIGH)
    _mk("bad-buckets-no-boards", buckets=good, drop_boards=True)
    # 同名节点跨板各落一桶 (Codex round-5 HIGH): 生产器 stem 全局唯一, 用
    # (板, 节点) 复合键去重会放行这类伪造 —— 它直接违反 S1「恰好一桶」且虚增计数
    _mk(
        "bad-buckets-node-dup-across-boards",
        buckets={**good, "future": [*good["future"], _bucket_row("n1", "丙板", fsrs_due=tomorrow, why="x")]},
        st={"due_nodes": 3, "future_nodes": 3},
        boards=[*rollup[:2], {**_blank, "board": "丙板", "future": 3, "next_due": today_late}],
    )
    # due_nodes 侧同名节点跨板重复 (同一收紧的另一半)
    _mk(
        "bad-due-nodes-node-dup-across-boards",
        buckets=good,
        due_nodes=[
            *rows,
            _due_row("n1", "乙板", due_reason="scheduled", fsrs_due=overdue, bucket="due_now", why_due=W_DUE),
        ],
    )
    # future 桶塞已到期时刻 (应属到期侧)
    _mk("bad-buckets-nondue-past", buckets={**good, "future": [_bucket_row("f2", "丙板", fsrs_due=overdue, why="x")]})
    # future 桶塞同上海日时刻 (应属 due_today)
    _mk(
        "bad-buckets-future-same-day",
        buckets={**good, "future": [_bucket_row("f2", "丙板", fsrs_due=today_late, why="x")]},
    )
    # 与 boards rollup 逐板对账: rollup 声称丙板只有 1 个未到期
    _mk(
        "bad-buckets-rollup-future-drift",
        buckets=good,
        boards=[*rollup[:2], {**_blank, "board": "丙板", "future": 1, "next_due": today_late}],
    )
    # buckets 在场却给不出可信参照时钟 → 无从重算桶判据, 按 corrupt 降级
    _mk("bad-buckets-badgen", buckets=good, generated_at="20260830")

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200
    by_id = {v["vault_id"]: v for v in resp.json()["vaults"]}
    for name in (
        *shape_bad,
        "bad-buckets-identity",
        "bad-buckets-label-conflict",
        "bad-buckets-why-conflict",
        "bad-buckets-new-semantics",
        "bad-buckets-stats-drift",
        "bad-buckets-nondue-wrong-day",
        "bad-buckets-nondue-identity",
        "bad-buckets-upcoming-ts-drift",
        "bad-buckets-upcoming-emptied",
        "bad-buckets-upcoming-wrong-board",
        "bad-buckets-due-future-ts",
        "bad-buckets-no-boards",
        "bad-buckets-node-dup-across-boards",
        "bad-due-nodes-node-dup-across-boards",
        "bad-buckets-nondue-past",
        "bad-buckets-future-same-day",
        "bad-buckets-rollup-future-drift",
        "bad-buckets-badgen",
    ):
        assert by_id[name]["status"] == "corrupt", f"{name} 跨源不一致必须 corrupt 降级"
    assert by_id["vault-nobuckets"]["status"] == "ok"
    assert by_id["vault-nobuckets"]["projection"]["bucket_counts"] is None, "旧投影不伪造分层数字"
    entry = by_id["vault-buckets"]
    assert entry["status"] == "ok", entry.get("error")
    assert entry["projection"]["bucket_counts"] == {
        "new": 1,
        "learning_queue": 1,
        "due_now": 1,
        "due_today": 1,
        "future": 1,
    }
    # 分层三桶合计仍等于权威计数, 分层只是标签不是搬移 (生产器 S2)
    assert entry["projection"]["due_count"] == 3

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    assert "分层 · 新卡 1 · 学习中 1 · 到期 1 · 今天晚些 1 · 未来 1" in page.text
    assert page.text.count("分层 · ") == 1, "无 buckets 的旧投影卡片不出现分层行"


def test_buckets_gate_accepts_real_producer_payload(tmp_path, overview_env, monkeypatch):
    """假阳性防线 (Codex round-2 C/D): 不用手搓 fixture —— 直接跑真生产器
    daily_review_pick.build_payload 产出投影, 落成真文件后过总览端点, 必须
    ok 且分层计数与生产器 buckets 逐字相等。门禁若把生产器真实产出判成
    corrupt, 本用例立刻红。"""
    import shutil
    import sys
    from pathlib import Path

    wt = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(wt / "scripts"))
    import daily_review_pick as picker  # pyright: ignore[reportMissingImports]

    # ⛔ 把**生产器侧**的时区也钉在 _SH (CARD-G6-9c)。本用例是两侧同场比对:
    #    picker 产出 buckets、总览端点的 _gate_buckets 复算它。两侧的时区来源
    #    形态不同 —— 端点每次现调 display_tz() (读 CANVAS_TZ, 由 _pin_display_tz
    #    夹具钉住), 而 picker 用**模块级常量** `_DISPLAY_TZ`, 在 `import
    #    daily_review_pick` 那一刻就固化了。
    #    单跑本文件时这里恰好是首次 import (夹具已生效, 两侧同为上海, 绿);
    #    与别的文件合跑时 picker 早在 collection 期就被 import 过 —— 那时还没有
    #    CANVAS_TZ, 常量固化成机器本地 ⇒ 非上海宿主上两侧分叉, 生产器把
    #    「上海今天 23:00」判成 future 而门说它该是 due_today, 端点返回 corrupt。
    #    钉住它, 门比的才是"桶位逻辑", 不是"两侧时区碰巧一样吗"。
    monkeypatch.setattr(picker, "_DISPLAY_TZ", _SH)

    root, client = overview_env
    vault = root / "vault-real"
    (vault / ".obsidian").mkdir(parents=True)
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(wt / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)

    now = datetime.now(_SH).replace(hour=9, minute=0, second=0, microsecond=0)
    sh_today = now.date()

    def _node(board, extra=""):
        return f'---\ntype: concept\nsource_board: "[[原白板/{board}]]"\n{extra}---\n真实内容。\n'

    files = {
        "真新卡": _node("甲板"),
        "学习中": _node("甲板", f"fsrs_due: {_utc_z(now - timedelta(days=2))}\nfsrs_state: 1\n"),
        "普通到期": _node("乙板", f"fsrs_due: {_utc_z(now - timedelta(days=1))}\nfsrs_state: 2\n"),
        "今天晚些": _node("丙板", f"fsrs_due: {_utc_z(_sh_at(sh_today, 23))}\n"),
        "远期": _node("丙板", f"fsrs_due: {_utc_z(_sh_at(sh_today + timedelta(days=5), 9))}\n"),
    }
    # 再造 4 个零到期板 —— 共 5 个候选、upcoming 被生产器截断到 3, 逼真跑通
    # 「条数 == min(3, 候选数)」与「未选中的板不得更早」两条新对账
    # (Codex round-4 B: 这正是最容易误伤真实产物的地方)
    for i, day in enumerate((2, 3, 4, 6), start=1):
        files[f"零到期{i}"] = _node(f"板{i}", f"fsrs_due: {_utc_z(_sh_at(sh_today + timedelta(days=day), 9))}\n")
    for name, content in files.items():
        (vault / "节点" / f"{name}.md").write_text(content, encoding="utf-8")
    payload, _ = picker.build_payload(vault, now, {}, picker.load_decay(vault))
    (vault / "outputs").mkdir()
    (vault / "outputs" / "今日复习.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 防门禁分支空跑: 真产物必须同时带 boards / buckets / 非空 upcoming,
    # 否则 (b)(c) 两条对账在本用例里等于没跑
    assert payload["upcoming"] and payload["boards"] and payload["buckets"]
    assert payload["upcoming"][0]["board"] == "丙板", "零到期板才进 upcoming, 且按 next_due 升序"
    assert len(payload["upcoming"]) == 3, "生产器把 upcoming 截断到 3, 候选实为 5 板"
    zero_due = [r["board"] for r in payload["boards"] if r["due"] == 0 and r["future"] > 0]
    assert len(zero_due) == 5, "截断分支必须真的被触发, 否则新对账等于空跑"

    entry = {v["vault_id"]: v for v in client.get("/api/v1/review/overview").json()["vaults"]}["vault-real"]
    assert entry["status"] == "ok", entry.get("error")
    assert entry["projection"]["bucket_counts"] == {
        b: len(payload["buckets"][b]) for b in ("new", "learning_queue", "due_now", "due_today", "future")
    }
    assert entry["projection"]["bucket_counts"] == {
        "new": 1,
        "learning_queue": 1,
        "due_now": 1,
        "due_today": 1,
        "future": 5,
    }
    assert entry["projection"]["due_count"] == payload["stats"]["due_nodes"] == 3
    # CARD-G6-5-R: 透传行必须在**真生产器产物**上与落盘 buckets 逐字相等 ——
    # 手搓 fixture 只能证"我造的形状能过", 证不了"生产器发的行原样到了页面"
    assert entry["projection"]["bucket_rows"] == {
        b: [{f: r[f] for f in ("node", "board", "why_due", "fsrs_due")} for r in payload["buckets"][b]]
        for b in ("new", "learning_queue", "due_now", "due_today", "future")
    }
    assert [r["node"] for r in entry["projection"]["bucket_rows"]["future"]] == [
        r["node"] for r in payload["buckets"]["future"]
    ], "future 桶节点身份与顺序不得在透传中漂移"


# ════════════════════════════════════════════════════════════════════
# CARD-G6-5-R 队列分层视图 (BATCH-2026-09-05-第十二批)
#
# 本卡新增面 = **透传**与**渲染**; 五桶验形与三方计数是 G3-6a 既有资产
# (:813 用例已含 bad-buckets-stats-drift / bad-buckets-future-drift 两条反例,
# 本节不再造同型)。
# ⚠ 三方计数的参照系, 逐字: 本断言的参照系是 generated_at，不是 now；读侧
# 到点标记不并入本等式的任何被加数。
# ════════════════════════════════════════════════════════════════════

#: 板级 rollup 行的零值底板 (与 :813 用例同形状, 生产器 boards 行全字段)
_ROLLUP_BLANK = {
    "due": 0,
    "due_new": 0,
    "due_scheduled": 0,
    "future": 0,
    "next_due": "",
    "placeholder": 0,
    "earliest_overdue": "",
}


def _layered(root, name: str, *, gen_iso: str, tomorrow: str, buckets=None, stats=None):
    """最小**合法**分层投影: 甲板 1 张新卡到期 + 乙板 1 张明天到期。

    五桶三空两满 —— 空桶不是凑数: 渲染层「空桶也出分区、且不伪造节点」这条
    只有在真有空桶时才被跑到。
    """
    good = {
        "new": [_bucket_row("n1", "甲板", why="新卡未排期，视同即刻到期 · 从未考察")],
        "learning_queue": [],
        "due_now": [],
        "due_today": [],
        "future": [_bucket_row("f2", "乙板", fsrs_due=tomorrow, why="明天 09:00 到期")],
    }
    proj = _projection(
        name,
        generated_at=gen_iso,
        due_nodes=[_due_row("n1", "甲板")],
        stats=stats or {"due_nodes": 1, "future_nodes": 1},
        top_boards=[{"board": "甲板", "top_node": "n1", "pending": 1}],
        upcoming=[{"board": "乙板", "next_due": tomorrow, "node": "f2"}],
        boards=[
            {**_ROLLUP_BLANK, "board": "甲板", "due": 1, "due_new": 1},
            {**_ROLLUP_BLANK, "board": "乙板", "future": 1, "next_due": tomorrow},
        ],
        buckets=good if buckets is None else buckets,
        # CARD-G6-9c-R2: 现役生产器恒写 display_tz, 夹具跟上它。缺这个键的投影现在整份
        # 判 corrupt（没有生产者时区就无法可靠重算归桶 —— 固定偏移只在 generated_at
        # 那一刻可信）。本 helper 造的是**合法分层投影**, 要测的是透传与渲染, 不是
        # 「旧投影怎么归桶」; 后者由 test_g6_9c_single_tz_source.py 的桶位门专门守。
        display_tz="Asia/Shanghai",
    )
    _mk_vault(root, name, proj)
    return good


def test_bucket_rows_passthrough_and_boundary_len_gate(overview_env, monkeypatch):
    """CARD-G6-5-R ①透传 ②边界不变量 ③旧投影缺省 (本卡新增面)。

    ② 是本卡唯一的新硬断言: 透传行的逐桶 len 与 bucket_counts 不等 → corrupt。
    它挡的不是投影数据 (那由 :490-499 的三方计数管), 而是**透传实现本身** ——
    「从别处取行」或「取行后被改」。反例用 monkeypatch 模拟那种未来改动:
    计数照旧、行被掏空一桶。
    """
    root, client = overview_env
    sh_today = datetime.now(_SH).date()
    gen_iso = _sh_at(sh_today, 8).isoformat(timespec="seconds")
    tomorrow = _utc_z(_sh_at(sh_today + timedelta(days=1), 9))
    good = _layered(root, "vault-layered", gen_iso=gen_iso, tomorrow=tomorrow)
    # 桶行带一个门禁没验过的多余字段 —— 白名单必须把它挡在 API 之外
    good_extra = {**good, "future": [{**good["future"][0], "secret": "不该出门的字段"}]}
    _layered(root, "vault-extra-field", gen_iso=gen_iso, tomorrow=tomorrow, buckets=good_extra)
    _mk_vault(root, "vault-old", _projection("vault-old", generated_at=gen_iso))

    by_id = {v["vault_id"]: v for v in client.get("/api/v1/review/overview").json()["vaults"]}

    entry = by_id["vault-layered"]
    assert entry["status"] == "ok", entry.get("error")
    rows = entry["projection"]["bucket_rows"]
    assert list(rows) == ["new", "learning_queue", "due_now", "due_today", "future"], "五键恒在且按桶序"
    assert rows == good, "透传行必须与投影 buckets 逐字相等 (不排序不改写不补字段)"
    # 与计数同源: 逐桶 len 恒等于 bucket_counts (本卡边界不变量的正向面)
    assert {b: len(rows[b]) for b in rows} == entry["projection"]["bucket_counts"]

    extra = by_id["vault-extra-field"]
    assert extra["status"] == "ok", extra.get("error")
    assert set(extra["projection"]["bucket_rows"]["future"][0]) == {"node", "board", "why_due", "fsrs_due"}, (
        "只有 _gate_buckets 验过的四字段可以出门 —— 未验字段进 API 就是没门禁的通道"
    )

    old = by_id["vault-old"]
    assert old["status"] == "ok"
    assert old["projection"]["bucket_rows"] is None, "旧投影不伪造空队列 (与 bucket_counts 同缺省纪律)"
    assert old["projection"]["bucket_counts"] is None

    # ② 边界不变量: 计数不动, 只把透传行掏空一桶
    import app.api.v1.endpoints.review_overview as ro

    real_gate = ro._gate_buckets

    def _rows_from_elsewhere(*args, **kwargs):
        counts, passed = real_gate(*args, **kwargs)
        return counts, {**passed, "future": []}

    monkeypatch.setattr(ro, "_gate_buckets", _rows_from_elsewhere)
    after = {v["vault_id"]: v for v in client.get("/api/v1/review/overview").json()["vaults"]}
    assert after["vault-layered"]["status"] == "corrupt", "透传行与计数脱钩必须 corrupt 降级, 不许照常出页面"
    assert "bucket_rows" in str(after["vault-layered"]["error"]), after["vault-layered"]["error"]
    assert after["vault-old"]["status"] == "ok", "旧投影不过 buckets 分支, 不受本不变量影响"


def test_page_renders_five_bucket_sections_and_omits_them_for_old_projection(overview_env):
    """CARD-G6-5-R (d) 零 JS 页: 五桶分区区块 + 节点级深链; 旧投影整块不出现。"""
    root, client = overview_env
    sh_today = datetime.now(_SH).date()
    gen_iso = _sh_at(sh_today, 8).isoformat(timespec="seconds")
    tomorrow = _utc_z(_sh_at(sh_today + timedelta(days=1), 9))
    _layered(root, "vault-layered", gen_iso=gen_iso, tomorrow=tomorrow)
    _mk_vault(root, "vault-old", _projection("vault-old", generated_at=gen_iso))

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    # 容器标记恰 1 次 = 分层库出一块、旧投影库出 0 块 (缺省整块不出现)
    assert page.text.count("data-queue-layers") == 1, "旧投影卡片不得出现队列区块容器"
    from app.api.v1.endpoints.review_overview import _BUCKET_CN, _BUCKET_ORDER

    for b in _BUCKET_ORDER:
        assert f'data-queue-bucket="{b}"' in page.text, f"{b} 桶必须自成一区 (空桶也出, 不藏)"
        assert _BUCKET_CN[b] in page.text
    # 节点级可见 + obsidian:// 深链 (复用 _node_link, 不新造拼接)
    assert "n1" in page.text and "f2" in page.text
    assert quote("节点/f2.md", safe="") in page.text
    assert "obsidian://open?vault=" + quote("vault-layered", safe="") in page.text
    # 空桶如实显示 0 且不伪造节点: 三个空桶各出一条空态文案, 计数括号里是 0
    assert page.text.count("这一桶今天是空的") == 3, "learning_queue / due_now / due_today 三桶今天为空"
    assert page.text.count("（0）") == 3
    assert "按到期阶段看队列（2 张卡分五块）" in page.text


# ════════════════════════════════════════════════════════════════════
# CARD-G6-1 投影按需重建 (BATCH-2026-08-31-第七批)
#
# 一律真跑: 真 vault 目录 + 真节点 md + 真 subprocess 起真生产器脚本。
# 不 mock 子进程、不 mock 文件系统 —— 本卡要证的恰恰是"写侧只碰了什么"
# 与"并发下落盘不撕裂", 这两条在 mock 下无从证起。
# ════════════════════════════════════════════════════════════════════

_REFRESH_URL = "/api/v1/review/overview/refresh"
_WT = Path(__file__).resolve().parents[3]
_PICK_PATH = _WT / "scripts" / "daily_review_pick.py"
_DECAY_PATH = _WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py"


def _node_md(board: str = "CS 61B", *, fsrs_due: str | None = None, extra: str = "") -> str:
    """真节点 frontmatter (字段名与 daily_review_pick.scan_nodes 消费面对齐)。"""
    fm = f'type: concept\nsource_board: "[[原白板/{board}]]"\n'
    if fsrs_due is not None:
        fm += f"fsrs_due: {fsrs_due}\n"
    return f"---\n{fm}{extra}---\n这是真实的一句定义内容，不是占位符。\n"


def _mk_node_vault(root: Path, name: str, nodes: dict[str, str]) -> Path:
    """可被生产器真扫的 vault: .obsidian + 节点/*.md + vault 内 decay_beta。"""
    vault = root / name
    (vault / ".obsidian").mkdir(parents=True)
    (vault / "节点").mkdir(parents=True)
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy(_DECAY_PATH, scripts)
    for stem, content in nodes.items():
        (vault / "节点" / f"{stem}.md").write_text(content, encoding="utf-8")
    return vault


def _tree(root: Path) -> dict[str, str]:
    """全树指纹: 相对路径 → sha256 (目录记 <dir>)。

    key 集合本身进指纹 —— 只比对已知文件的内容会漏掉"新增了一个文件"
    (vault 内 __pycache__ 正是这种形态), 那样这道门就成了摆设。
    """
    out: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        out[rel] = "<dir>" if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _is_projection_path(rel: str, vault_name: str) -> bool:
    """本端点唯一获准改动的写面: <vault>/outputs/ 与 outputs/今日复习.*"""
    return rel == f"{vault_name}/outputs" or rel.startswith(f"{vault_name}/outputs/今日复习.")


@pytest.fixture
def refresh_env(overview_env, monkeypatch):
    """overview_env + 去抖窗口归零 (去抖本身另有专用用例锁)。

    同时清掉 DAILY_REVIEW_PICK: 否则宿主环境若恰好设了它, 全部用例都会
    去跑别处的脚本, 结果与被测 commit 无关。
    """
    import app.api.v1.endpoints.review_overview as mod

    monkeypatch.delenv(mod._PICK_SCRIPT_ENV, raising=False)
    monkeypatch.setattr(mod, "_REFRESH_TTL_SECONDS", 0.0)
    return overview_env


def test_refresh_rebuilds_projection_and_response_matches_disk(refresh_env):
    """卡文 (c) 第一条: 盘中改一节点 fsrs_due → POST refresh → 响应与盘上
    JSON 一致且含该节点。

    两次真重建对比: 第一次全员未到期 (due=0), 改盘后第二次该节点必须出现
    在盘上 due_nodes 里, 且响应的聚合条目与盘上 JSON 同源自洽。
    """
    root, client = refresh_env
    vault = _mk_node_vault(
        root,
        "vault-r",
        {
            "定义甲": _node_md(fsrs_due='"2099-01-01T00:00:00Z"'),
            "定义乙": _node_md(board="数学", fsrs_due='"2099-01-01T00:00:00Z"'),
        },
    )
    proj = vault / "outputs" / "今日复习.json"

    first = client.post(_REFRESH_URL, data={"vault_id": "vault-r"})
    assert first.status_code == 200, first.text
    assert proj.exists(), "第一次 refresh 就该把投影生成出来 (无投影库的首建路径)"
    assert json.loads(proj.read_text(encoding="utf-8"))["stats"]["due_nodes"] == 0

    # 盘中把一个节点改成已到期 (模拟 quiz 写侧刚落 fsrs_due)
    (vault / "节点" / "定义甲.md").write_text(_node_md(fsrs_due='"2020-01-01T00:00:00Z"'), encoding="utf-8")

    resp = client.post(_REFRESH_URL, data={"vault_id": "vault-r"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["rebuilt"] is True and body["reason"] == "rebuilt"
    assert body["rebuild_count"] == 2 and body["duration_ms"] > 0

    disk = json.loads(proj.read_text(encoding="utf-8"))
    assert [r["node"] for r in disk["due_nodes"]] == ["定义甲"], "盘上明细必须含被改的那个节点"
    proj_summary = body["entry"]["projection"]
    assert body["entry"]["status"] == "ok"
    # 响应与盘上一致: 计数、板、以及点名到该节点
    assert proj_summary["due_count"] == disk["stats"]["due_nodes"] == 1
    assert proj_summary["top_node"] == "定义甲", "响应里点名的正是被改的那个节点"
    assert proj_summary["recommended_board"] == "CS 61B"
    assert proj_summary["generated_at"] == disk["generated_at"]
    assert [r["board"] for r in proj_summary["boards"] if r["due"]] == ["CS 61B"]


def test_refresh_writes_only_projection_and_never_touches_runner_state(refresh_env):
    """卡文 (b)(c): 只写 outputs/今日复习.*; runner state 逐字节不变。

    两态都锁 —— 已存在的 state 文件 shasum 必须不变, 本来不存在的
    state 文件之后也必须仍不存在 ("没有发生"不等于"验证通过", 只查前者
    等于放行"顺手创建一个 state"这条路)。
    全树指纹覆盖整个 VAULTS_ROOT: vault 内 __pycache__ (生产器 import
    decay_beta 的副产物) 会直接在这里露馅。
    """
    root, client = refresh_env
    _vault = _mk_node_vault(root, "vault-w", {"甲": _node_md(), "乙": _node_md(board="数学")})

    backups = root / "backups"  # 非 vault (无 .obsidian) — 不进枚举, 只作写面靶子
    backups.mkdir()
    state = backups / "daily-review.vault-w.state.json"
    state.write_text(
        '{"schema_version": 1, "board_last_recommended": {"CS 61B": "2026-08-01"}}\n',
        encoding="utf-8",
    )
    state_sha = hashlib.sha256(state.read_bytes()).hexdigest()
    absent_state = backups / "daily-review.从未存在.state.json"

    before = _tree(root)
    assert client.post(_REFRESH_URL, data={"vault_id": "vault-w"}).status_code == 200
    after = _tree(root)

    assert hashlib.sha256(state.read_bytes()).hexdigest() == state_sha, "runner state 必须逐字节不变"
    assert not absent_state.exists(), "不得凭空创建 runner state"

    changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    illegal = {k for k in changed if not _is_projection_path(k, "vault-w")}
    assert illegal == set(), f"写面越界: {sorted(illegal)}"
    assert changed == {
        "vault-w/outputs",
        "vault-w/outputs/今日复习.json",
        "vault-w/outputs/今日复习.md",
    }, "写面必须恰好是这三项 (目录 + 两个产物), 多一项少一项都不行"


def test_refresh_and_generator_interleaved_never_yield_unparsable_projection(refresh_env):
    """卡文 (c): 并发 refresh × 生产器 --write 交错, 每轮 JSON 可 parse 且过 _summarize。

    ⚠ 如实声明替换: 卡文写的是 "runner --now"。第二个写者这里用
    `daily_review_pick.py --write` 而非 daily_review_run.py —— 撕裂门的被测
    对象是 **outputs/ 两文件的原子发布**, 而 runner 落盘走的正是
    picker.atomic_write 这同一段 (daily_review_run.ensure_payload 直接调它);
    跑真 runner 还会连带写 backups/ state 与触推送链, 与本卡"不写 runner
    state"的裁判自相矛盾, 且 daily_review_run.py 在本车道硬边界之外。
    """
    root, client = refresh_env
    vault = _mk_node_vault(
        root,
        "vault-c",
        {f"节点{i:02d}": _node_md(board=f"板{i % 4}", fsrs_due=f'"20{20 + i % 5}-01-01T00:00:00Z"') for i in range(48)},
    )
    proj = vault / "outputs" / "今日复习.json"
    assert client.post(_REFRESH_URL, data={"vault_id": "vault-c"}).status_code == 200

    import app.api.v1.endpoints.review_overview as mod

    stop = threading.Event()
    writer_failures: list[str] = []
    writer_rounds = 0

    def _writer():
        nonlocal writer_rounds
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        while not stop.is_set():
            r = subprocess.run(
                [sys.executable, str(_PICK_PATH), "--vault", str(vault), "--write"],
                capture_output=True,
                text=True,
                env=env,
            )
            if r.returncode != 0:
                writer_failures.append(r.stderr[-300:])
                return
            writer_rounds += 1

    thread = threading.Thread(target=_writer, daemon=True)
    thread.start()
    try:
        for _i in range(12):
            resp = client.post(_REFRESH_URL, data={"vault_id": "vault-c"})
            assert resp.status_code == 200, resp.text
            raw = proj.read_text(encoding="utf-8")
            payload = json.loads(raw)  # 撕裂的拼接物在这里就炸
            mod._summarize(payload)  # 且必须过总览端点的全部门禁
            assert resp.json()["entry"]["status"] in ("ok", "stale"), resp.json()["entry"].get("error")
    finally:
        stop.set()
        thread.join(timeout=120)
    assert not writer_failures, f"并发写者自身失败: {writer_failures[:1]}"
    assert not thread.is_alive()
    # ⚠ 反死门: 写者线程一次都没跑完的话, 上面 12 轮"没撕裂"只是因为根本
    # 没有第二个写者 —— 那这道门是空的。必须先证明交错真实发生。
    assert writer_rounds >= 3, f"并发写者只完成 {writer_rounds} 轮, 交错未真实发生, 本门不成立"
    # 交错结束后不得留下任何 tmp 残渣
    assert list((vault / "outputs").glob("*.tmp")) == []


def test_get_endpoints_stay_pure_after_refresh(refresh_env):
    """卡文 (c): GET /overview 与 /page 恒纯 (前后 outputs mtime + shasum 断言)。"""
    root, client = refresh_env
    vault = _mk_node_vault(root, "vault-g", {"甲": _node_md()})
    assert client.post(_REFRESH_URL, data={"vault_id": "vault-g"}).status_code == 200

    outputs = vault / "outputs"

    def _snap():
        return {
            p.name: (p.stat().st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest())
            for p in sorted(outputs.iterdir())
        }

    before = _snap()
    for _ in range(3):
        assert client.get("/api/v1/review/overview").status_code == 200
        assert client.get("/api/v1/review/overview/page").status_code == 200
    assert _snap() == before, "GET 侧任何一次调用都不许改动投影 (mtime 也不许动)"


def test_ttl_debounce_ten_clicks_at_most_one_rebuild(overview_env, monkeypatch):
    """卡文 (b): 短窗 10 连击 ≤1 次真实重建, 重建计数暴露在响应。

    刻意不用 refresh_env —— 这条要跑**默认 TTL**, 归零后就没有可测的东西了。
    """
    import app.api.v1.endpoints.review_overview as mod

    monkeypatch.delenv(mod._PICK_SCRIPT_ENV, raising=False)
    assert mod._REFRESH_TTL_SECONDS > 0, "默认必须有去抖窗口"

    root, client = overview_env
    vault = _mk_node_vault(root, "vault-d", {"甲": _node_md()})
    proj = vault / "outputs" / "今日复习.json"

    bodies = []
    for _ in range(10):
        r = client.post(_REFRESH_URL, data={"vault_id": "vault-d"})
        assert r.status_code == 200, r.text
        bodies.append(r.json())
        if len(bodies) == 1:
            first_sig = (proj.stat().st_mtime_ns, hashlib.sha256(proj.read_bytes()).hexdigest())

    assert bodies[0]["rebuilt"] is True and bodies[0]["reason"] == "rebuilt"
    assert all(b["rebuilt"] is False and b["reason"] == "debounced" for b in bodies[1:])
    assert {b["rebuild_count"] for b in bodies} == {1}, "10 次点击只许有 1 次真实重建"
    assert all(b["retry_after_seconds"] > 0 for b in bodies[1:])
    assert bodies[0]["debounce_ttl_seconds"] == mod._REFRESH_TTL_SECONDS
    assert (proj.stat().st_mtime_ns, hashlib.sha256(proj.read_bytes()).hexdigest()) == first_sig, (
        "被去抖的 9 次不许碰盘"
    )
    # 去抖返回的仍是真实盘上状态, 不是"上次响应的缓存复读"
    assert bodies[-1]["entry"]["projection"]["generated_at"] == json.loads(proj.read_text("utf-8"))["generated_at"]


def test_debounce_window_is_per_vault_not_global(refresh_env, monkeypatch):
    """去抖账按库独立: A 库刚重建过, 不许把 B 库的第一次点击也吞掉。"""
    import app.api.v1.endpoints.review_overview as mod

    monkeypatch.setattr(mod, "_REFRESH_TTL_SECONDS", 300.0)
    root, client = refresh_env
    _mk_node_vault(root, "vault-x", {"甲": _node_md()})
    _mk_node_vault(root, "vault-y", {"乙": _node_md()})

    assert client.post(_REFRESH_URL, data={"vault_id": "vault-x"}).json()["rebuilt"] is True
    assert client.post(_REFRESH_URL, data={"vault_id": "vault-x"}).json()["rebuilt"] is False
    y = client.post(_REFRESH_URL, data={"vault_id": "vault-y"}).json()
    assert y["rebuilt"] is True and y["rebuild_count"] == 1
    assert (root / "vault-y" / "outputs" / "今日复习.json").exists()


def test_second_click_while_rebuild_in_flight_returns_in_progress(refresh_env):
    """同库已有重建在飞 → 立刻回 in_progress, 不排队。

    sync 端点跑在 FastAPI 共享线程池 (默认 40 线程) 里: 阻塞等锁会让连点
    把整池占满, 连只读的 /overview 都被拖住。这里把该库的锁先占住冒充
    "在飞", 端点必须立刻回话而不是卡住 (若它选择阻塞, 本用例会挂死)。
    """
    import app.api.v1.endpoints.review_overview as mod

    root, client = refresh_env
    vault = _mk_node_vault(root, "vault-i", {"甲": _node_md()})
    key = str(Path(root).resolve() / "vault-i")  # 端点侧的 key 是 resolve 过的
    lock = threading.Lock()
    with mod._refresh_guard:
        mod._refresh_locks[key] = lock
    assert lock.acquire(blocking=False)
    try:
        resp = client.post(_REFRESH_URL, data={"vault_id": "vault-i"})
    finally:
        lock.release()

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["rebuilt"] is False and body["reason"] == "in_progress"
    assert not (vault / "outputs").exists(), "在飞时第二个请求不许也去写盘"
    assert body["entry"]["status"] == "no_projection", "在飞时如实报当前盘上状态, 不编造投影"


def test_missing_pick_script_fails_closed_503_without_writing(refresh_env, monkeypatch):
    """卡文 (b): 路径耦合断裂 → 503 fail-closed, 绝不静默假成功。

    关键在于**一个字节都不许写** —— 「找不到生产器就本地重算一份」会当场
    造出 A2 明令禁止的第二套到期裁判。
    """
    import app.api.v1.endpoints.review_overview as mod

    root, client = refresh_env
    _mk_node_vault(root, "vault-f", {"甲": _node_md()})
    monkeypatch.setattr(mod, "_PICK_REL", ("scripts", "根本不存在的生产器.py"))
    monkeypatch.setenv(mod._PICK_SCRIPT_ENV, str(root / "也不存在.py"))

    before = _tree(root)
    resp = client.post(_REFRESH_URL, data={"vault_id": "vault-f"})
    assert resp.status_code == 503
    detail = resp.json()["detail"]
    assert detail["error"] == "pick_script_not_found"
    assert detail["tried"], "必须列出试过的路径 (否则现场无从诊断)"
    assert _tree(root) == before, "fail-closed 路径不许留下任何写入"


def test_pick_nonzero_exit_fails_closed_503(refresh_env, monkeypatch, tmp_path):
    """生产器非零退出 → 503 + stderr 尾部, 不许把旧投影当新的宣称成功。"""
    import app.api.v1.endpoints.review_overview as mod

    root, client = refresh_env
    _mk_node_vault(root, "vault-e", {"甲": _node_md()})
    boom = tmp_path / "boom.py"
    boom.write_text("import sys\nsys.stderr.write('生产器炸了: 边界条件 X\\n')\nsys.exit(3)\n", encoding="utf-8")
    monkeypatch.setenv(mod._PICK_SCRIPT_ENV, str(boom))

    resp = client.post(_REFRESH_URL, data={"vault_id": "vault-e"})
    assert resp.status_code == 503
    detail = resp.json()["detail"]
    assert detail["error"] == "pick_failed" and detail["returncode"] == 3
    assert "生产器炸了" in detail["stderr_tail"]
    assert not (root / "vault-e" / "outputs").exists(), "失败不许留下半个 outputs"


def test_zero_exit_without_projection_is_not_success(refresh_env, monkeypatch, tmp_path):
    """Codex round-1 HIGH-1: 退出码 0 ≠ 重建成功。

    一个 rc=0 却什么都不写的生产器, 若被记成 rebuilt=true, 表单路径再 303
    跳回总览页 —— 用户看到"点了、跳回来了、什么都没变", 静默假成功的完整
    形态。必须 503, 且**不许提交 TTL mark**(否则用户修好前每次点击都被
    去抖吃掉, 永远修不回来)。
    """
    import app.api.v1.endpoints.review_overview as mod

    root, client = refresh_env
    _mk_node_vault(root, "vault-noop", {"甲": _node_md()})
    noop = tmp_path / "noop.py"
    noop.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    monkeypatch.setenv(mod._PICK_SCRIPT_ENV, str(noop))
    monkeypatch.setattr(mod, "_REFRESH_TTL_SECONDS", 300.0)  # 有窗口才测得出"没记 mark"

    for i in (1, 2):
        resp = client.post(_REFRESH_URL, data={"vault_id": "vault-noop"})
        assert resp.status_code == 503, f"第{i}次: rc=0 但无产物必须 503, 实为 {resp.status_code}"
        assert resp.json()["detail"]["error"] == "projection_missing_after_rebuild"
    assert not (root / "vault-noop" / "outputs").exists()

    # 表单路径同样不许降级成 303
    form = client.post(_REFRESH_URL, data={"vault_id": "vault-noop", "redirect": "page"}, follow_redirects=False)
    assert form.status_code == 503 and "刷新失败" in form.text


def test_zero_exit_with_corrupt_projection_is_not_success(refresh_env, monkeypatch, tmp_path):
    """rc=0 但产出过不了 schema v3 门禁 → 同样不算重建成功。"""
    import app.api.v1.endpoints.review_overview as mod

    root, client = refresh_env
    _mk_node_vault(root, "vault-garbage", {"甲": _node_md()})
    faker = tmp_path / "faker.py"
    faker.write_text(
        "import sys, pathlib\n"
        "v = pathlib.Path(sys.argv[sys.argv.index('--vault') + 1])\n"
        "(v / 'outputs').mkdir(parents=True, exist_ok=True)\n"
        "(v / 'outputs' / '今日复习.json').write_text('{\"schema_version\": 2}', encoding='utf-8')\n"
        "(v / 'outputs' / '今日复习.md').write_text('# 假的\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(mod._PICK_SCRIPT_ENV, str(faker))

    resp = client.post(_REFRESH_URL, data={"vault_id": "vault-garbage"})
    assert resp.status_code == 503
    assert resp.json()["detail"]["error"] == "projection_corrupt_after_rebuild"


def test_symlink_aliases_share_one_debounce_ledger(refresh_env, monkeypatch):
    """Codex round-1 BLOCKER-2 附带: 同一物理库的两条软链别名必须共用同一
    把锁与同一本去抖账 —— 用字面路径做 key 会给它们各一份, 同一个物理库
    就能被两条别名并发重建。"""
    import app.api.v1.endpoints.review_overview as mod

    monkeypatch.setattr(mod, "_REFRESH_TTL_SECONDS", 300.0)
    root, client = refresh_env
    _mk_node_vault(root, "物理库", {"甲": _node_md()})
    (root / "别名库").symlink_to(Path(root).resolve() / "物理库", target_is_directory=True)

    first = client.post(_REFRESH_URL, data={"vault_id": "物理库"}).json()
    assert first["rebuilt"] is True
    alias = client.post(_REFRESH_URL, data={"vault_id": "别名库"}).json()
    assert alias["rebuilt"] is False and alias["reason"] == "debounced", "别名必须落进同一本去抖账"
    assert alias["rebuild_count"] == 1


def test_cross_site_form_post_is_blocked(refresh_env):
    """本端点会写文件并起子进程, 而全站无鉴权 —— 别的网页放一个跨站 <form>
    就能借用户的浏览器把它发出去 (CORS 只挡读响应, 挡不住副作用)。

    同源提交与非浏览器客户端 (curl / 验收脚本, 两个头都不带) 必须照常放行。
    """
    root, client = refresh_env
    _mk_node_vault(root, "vault-csrf", {"甲": _node_md()})

    # ⚠ 每个组合只带**一个**会触发拒绝的头 —— 原来第三条同时带了外域 Origin,
    # 而 Origin 分支单独就会 403 且 error 码相同, 于是 same-site 那条分支
    # 被完全遮蔽: 把它改成放行, 测试照样绿（收官审计抓到）。
    for headers in (
        {"Sec-Fetch-Site": "cross-site"},
        # same-site ≠ same-origin: 同注册域下的另一个子域也算 same-site,
        # 它不是"本页发起的提交"。这一条**不带 Origin**, 单独隔离该分支。
        {"Sec-Fetch-Site": "same-site"},
        {"Origin": "https://evil.example.com"},
    ):
        r = client.post(_REFRESH_URL, data={"vault_id": "vault-csrf"}, headers=headers)
        assert r.status_code == 403, f"{headers} 应被拒, 实为 {r.status_code}"
        assert r.json()["detail"]["error"] == "cross_site_blocked"
    assert not (root / "vault-csrf" / "outputs").exists(), "被拒的跨站请求不许留下任何写入"

    # 本页发起的同源提交照常
    ok = client.post(
        _REFRESH_URL,
        data={"vault_id": "vault-csrf"},
        headers={"Sec-Fetch-Site": "same-origin", "Origin": "http://127.0.0.1:8011"},
    )
    assert ok.status_code == 200 and ok.json()["rebuilt"] is True
    # 不带这两个头的客户端 (curl) 照常
    assert client.post(_REFRESH_URL, data={"vault_id": "vault-csrf"}).status_code == 200


def test_symlinked_vault_outside_root_is_refused(refresh_env, tmp_path_factory):
    """VAULTS_ROOT 下指向库外的软链会被 `is_dir()` 当成真库列出来 —— 那时
    refresh 就把东西写到了库外。realpath 归属判定必须挡住它 (Codex 探针
    VAULT_SYMLINK 同型)。"""
    root, client = refresh_env
    outside = tmp_path_factory.mktemp("outside")
    _mk_node_vault(outside, "真身", {"甲": _node_md()})
    (root / "看起来在根里的库").symlink_to(outside / "真身", target_is_directory=True)

    resp = client.post(_REFRESH_URL, data={"vault_id": "看起来在根里的库"})
    assert resp.status_code == 503
    assert resp.json()["detail"]["error"] == "vault_outside_root"
    assert not (outside / "真身" / "outputs").exists(), "拒绝之后不许有任何库外写入"


def test_symlinked_outputs_outside_vault_is_refused(refresh_env, tmp_path_factory):
    """`<vault>/outputs` 指向库外时, "只写 outputs/今日复习.*" 这句话字面
    还成立, 实际写面却已经出了库 (Codex 探针 OUTPUTS_SYMLINK 同型)。"""
    root, client = refresh_env
    vault = _mk_node_vault(root, "outputs被换掉的库", {"甲": _node_md()})
    elsewhere = tmp_path_factory.mktemp("elsewhere") / "落点"
    elsewhere.mkdir()
    (vault / "outputs").symlink_to(elsewhere, target_is_directory=True)

    resp = client.post(_REFRESH_URL, data={"vault_id": "outputs被换掉的库"})
    assert resp.status_code == 503
    assert resp.json()["detail"]["error"] == "outputs_outside_vault"
    assert list(elsewhere.iterdir()) == [], "拒绝之后库外落点必须仍是空的"


def test_child_env_is_allowlisted_not_inherited(refresh_env, monkeypatch):
    """子进程环境是白名单, 不是 `dict(os.environ)`。

    整份继承会让 PYTHONPATH 把 `import decay_beta` 解析到**库外**的另一个
    模块, 那段代码在后端进程权限下执行、想写哪儿写哪儿 (Codex 探针
    INHERITED_ENV 同型)。这里直接查子进程环境的构造。
    """
    import app.api.v1.endpoints.review_overview as mod

    monkeypatch.setenv("PYTHONPATH", "/tmp/注入点")
    monkeypatch.setenv("PYTHONSTARTUP", "/tmp/注入.py")
    monkeypatch.setenv("SOME_SECRET_TOKEN", "sk-不该进子进程")
    monkeypatch.setenv("TZ", "Asia/Shanghai")

    env = mod._child_env()
    assert "PYTHONPATH" not in env and "PYTHONSTARTUP" not in env
    assert "SOME_SECRET_TOKEN" not in env, "后端进程的密钥不该顺手进子进程"
    assert env["PYTHONDONTWRITEBYTECODE"] == "1" and env["PYTHONNOUSERSITE"] == "1"
    assert env.get("TZ") == "Asia/Shanghai", (
        "TZ 必须**透传**(CARD-G6-9c / D-18): 父子两侧看同一个时区视图。"
        "本卡之前这里是被强制赋成一个固定名的, 恰好等于 setenv 的值 —— 那时这条"
        "断言过得去但证不到透传。现在白名单里有 TZ, 它才真的在测透传。"
    )

    # 端到端: 带着注入 env 跑真 refresh 仍要正常出投影 (白名单没砍掉必需项)
    root, client = refresh_env
    _mk_node_vault(root, "vault-env", {"甲": _node_md()})
    resp = client.post(_REFRESH_URL, data={"vault_id": "vault-env"})
    assert resp.status_code == 200 and resp.json()["entry"]["status"] == "ok"


def test_unconfigured_vault_gets_human_hint_not_bare_traceback(refresh_env):
    """只有 .obsidian/ 的库 (被库枚举捞进来但从没配过每日复习): 生产器会抛
    ModuleNotFoundError: decay_beta —— 必须给人话诊断, 不能只甩 traceback。

    实测场景, 不是假想: 库枚举规则只看 .obsidian/, live 上就有这种库。
    """
    root, client = refresh_env
    _mk_vault(root, "光有obsidian的库")  # 无 节点/, 无 .claude/scripts/decay_beta.py

    resp = client.post(_REFRESH_URL, data={"vault_id": "光有obsidian的库"})
    assert resp.status_code == 503
    detail = resp.json()["detail"]
    assert detail["error"] == "pick_failed"
    assert "节点" in detail["hint"] and "decay_beta.py" in detail["hint"]
    # 原始现场不许藏 —— 人话解释旁边仍要有 stderr 尾部
    assert "decay_beta" in detail["stderr_tail"]

    # 配齐的库不该带这条提示 (提示恒挂 = 提示无意义)
    _mk_node_vault(root, "配齐的库", {"甲": _node_md()})
    ok = client.post(_REFRESH_URL, data={"vault_id": "配齐的库"})
    assert ok.status_code == 200 and ok.json()["rebuilt"] is True

    # Codex round-3: 只用 .exists() 判断时, 一个**普通文件**叫「节点」、一个
    # **目录**叫「decay_beta.py」都会被判成"配置齐全" —— 提示消失, 用户只剩
    # 一段 traceback。按类型逐项判才挡得住 (实测确认 .exists() 对两者都为 True)
    weird = _mk_vault(root, "类型错位的库")
    (weird / "节点").write_text("我是个文件不是目录", encoding="utf-8")
    (weird / ".claude" / "scripts" / "decay_beta.py").mkdir(parents=True)
    r = client.post(_REFRESH_URL, data={"vault_id": "类型错位的库"})
    assert r.status_code == 503
    d = r.json()["detail"]
    assert d["error"] == "pick_failed"
    assert "hint" in d, "类型错位同样是'没配好', 必须给人话提示而不是只甩 traceback"
    assert "节点" in d["hint"] and "decay_beta.py" in d["hint"]


def test_form_path_failure_renders_error_page_and_keeps_status(refresh_env):
    """表单路径失败 → 人话 HTML 错误页, **状态码仍是原样的 4xx/5xx**。

    失败时 303 跳回总览页, 用户会看到"页面刷新了但什么都没变"→ 以为成功了,
    那就是静默假成功的浏览器版本。
    """
    root, client = refresh_env
    _mk_vault(root, "没配过的库")

    resp = client.post(_REFRESH_URL, data={"vault_id": "没配过的库", "redirect": "page"}, follow_redirects=False)
    assert resp.status_code == 503, "失败绝不许降级成 3xx/2xx"
    assert resp.headers["content-type"].startswith("text/html")
    assert "刷新失败" in resp.text and "没配过的库" in resp.text
    assert "decay_beta.py" in resp.text  # hint 上页
    assert "回到总览页" in resp.text
    assert "<script" not in resp.text.lower()

    # 未知库走表单也是错误页, 且状态码保持 404
    r404 = client.post(_REFRESH_URL, data={"vault_id": "根本没有这个库", "redirect": "page"}, follow_redirects=False)
    assert r404.status_code == 404 and "刷新失败" in r404.text


def test_error_page_escapes_hostile_vault_name(refresh_env):
    """错误页里的库名同样是外部输入 —— 未转义即 XSS (且这条路径最容易漏)。"""
    root, client = refresh_env
    hostile = 'x"><img src=y onerror=alert(2)>'
    _mk_vault(root, hostile)

    resp = client.post(_REFRESH_URL, data={"vault_id": hostile, "redirect": "page"}, follow_redirects=False)
    assert resp.status_code == 503
    assert "<img src=y onerror=alert(2)>" not in resp.text
    assert "&lt;img src=y onerror=alert(2)&gt;" in resp.text


def test_unknown_vault_id_404_and_broken_root_503(refresh_env, monkeypatch):
    """vault_id 只认枚举出来的真实库名 (天然堵死 ../ 遍历); 根不可用 → 503。"""
    import types

    import app.api.v1.endpoints.review_overview as mod

    root, client = refresh_env
    _mk_node_vault(root, "vault-k", {"甲": _node_md()})

    for bogus in ("不存在的库", "../", "../vault-k", "vault-k/节点"):
        r = client.post(_REFRESH_URL, data={"vault_id": bogus})
        assert r.status_code == 404, f"{bogus!r} 应 404, 实为 {r.status_code}"
        assert r.json()["detail"]["error"] == "vault_not_found"

    monkeypatch.setattr(
        mod,
        "get_settings",
        lambda: types.SimpleNamespace(VAULTS_ROOT=str(root / "没有这个根"), ACTIVE_VAULT="x"),
    )
    r = client.post(_REFRESH_URL, data={"vault_id": "vault-k"})
    assert r.status_code == 503 and r.json()["detail"]["error"] == "vaults_root_invalid"


def test_page_refresh_form_is_zero_js_and_redirects_back(refresh_env):
    """卡文 (a): 页面上的刷新按钮是纯 HTML form POST, 零 JS; PRG 回跳。"""
    root, client = refresh_env
    _mk_node_vault(root, "vault-p", {"甲": _node_md()})
    _mk_vault(root, "vault-empty")  # 无投影库同样要有刷新按钮 (它最需要)

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    assert page.text.count(f'action="{_REFRESH_URL}"') == 2, "两个库各一个刷新表单"
    assert '<input type="hidden" name="vault_id" value="vault-p">' in page.text
    assert '<input type="hidden" name="vault_id" value="vault-empty">' in page.text
    assert 'name="redirect" value="page"' in page.text
    assert "<script" not in page.text.lower() and "onclick" not in page.text.lower()

    resp = client.post(_REFRESH_URL, data={"vault_id": "vault-p", "redirect": "page"}, follow_redirects=False)
    assert resp.status_code == 303, "PRG: 303 回 GET, 浏览器刷新不会重复提交"
    assert resp.headers["location"] == "/api/v1/review/overview/page"
    assert (root / "vault-p" / "outputs" / "今日复习.json").exists()


def test_refresh_form_escapes_hostile_vault_name(refresh_env):
    """库名里的引号/尖括号必须转义 —— 目录名是外部输入, 直接进属性即 XSS。

    敌对名里不能含 `/` (它是路径分隔符, mkdir 会造出两级目录而不是一个
    敌对库名 —— 实测踩过), 故用无斜杠的 img/onerror 载荷。
    """
    root, client = refresh_env
    hostile = 'a"><img src=x onerror=alert(1)>'
    _mk_node_vault(root, hostile, {"甲": _node_md()})

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    assert "<img src=x onerror=alert(1)>" not in page.text, "原样注入即 XSS"
    assert "&lt;img src=x onerror=alert(1)&gt;" in page.text
    assert 'value="a&quot;&gt;&lt;img src=x onerror=alert(1)&gt;"' in page.text
    # 表单能真提交回来 (转义不等于把库名改坏 — 端点仍按原名匹配到该库)
    resp = client.post(_REFRESH_URL, data={"vault_id": hostile}, follow_redirects=False)
    assert resp.status_code == 200, resp.text
    assert resp.json()["vault_id"] == hostile
    assert (root / hostile / "outputs" / "今日复习.json").exists()


def test_missing_vault_id_is_422_not_silent_noop(refresh_env):
    """缺 vault_id → 422 (FastAPI 表单校验), 不许静默重建"某个"库。"""
    root, client = refresh_env
    _mk_node_vault(root, "vault-m", {"甲": _node_md()})
    resp = client.post(_REFRESH_URL, data={})
    assert resp.status_code == 422
    assert not (root / "vault-m" / "outputs").exists()


# ════════════════════════════════════════════════════════════════════
# CARD-G6-4 节点级明细与精确开节点 (BATCH-2026-08-31-第七批)
#
# 8 类探针 (沿 CARD-D1 复核的敌对形状思路):
#   ① 展开结构与顺序 ② 字段渲染 ③ 深链编码 ④ 降级(旧投影/零到期/无投影)
#   ⑤ XSS 转义 ⑥ 形状垃圾门禁 ⑦ JSON 加性契约与同源 ⑧ 窄窗不横溢(结构性)
# 零 schema 改动: 全部字段都已在 due_nodes 行里, 本卡只是把它们渲染出来。
# ════════════════════════════════════════════════════════════════════


def _bucket_tags(page: str) -> list[str]:
    """页面上**桶位小标签**的取值，按渲染顺序。

    收官审计教训: 直接 `assert "新卡" in page` 零区分力 —— 「新卡」还出现在
    板表格列头 `<th>`、卡片汇总行「· 新卡 N」、分层行「分层 · 新卡 N」、以及
    why_due 正文里。要断言标签本身, 就得按标签的**结构**取值。
    这里从生产代码的 `_NODE_TAG` 样式串派生 selector, 样式改了这里跟着变,
    不会变成一条绑死在旧 CSS 上的死断言。
    """
    import app.api.v1.endpoints.review_overview as mod

    return re.findall(rf'<span style="{re.escape(mod._NODE_TAG)}">([^<]*)</span>', page)


def _nodes_projection(vault_id: str, rows: list[dict], *, generated_at=None, top: list | None = None) -> dict:
    """带 bucket/why_due 的 due_nodes 明细投影 (不含顶层 buckets 键 —— 本卡
    只消费行内字段, 顶层分组的跨源对账归 G3-6a 既有用例)。"""
    gen = generated_at or _now_local().isoformat(timespec="seconds")
    boards = sorted({r["board"] for r in rows})
    return _projection(
        vault_id,
        generated_at=gen,
        due_nodes=rows,
        stats={"due_nodes": len(rows)},
        top_boards=top
        if top is not None
        else [{"board": b, "top_node": rows[0]["node"], "pending": 1} for b in boards],
    )


def test_g64_expand_structure_and_urgency_order(overview_env):
    """① 展开结构 + 顺序: 每个有到期节点的板恰好一个 details/summary,
    节点条数 == 该板到期数; 顺序按紧迫度 —— 逾期最久在最前, 新卡("现在")
    排在已逾期节点之后。

    顺序这条不是审美: 字典序把新卡的空串当最小, 会让"逾期 3 天"被"现在"
    盖掉 —— CARD-D1 复核在板级 earliest 上抓过同一个缺陷, 明细里不许重犯。
    """
    root, client = overview_env
    now = _now_local()
    rows = [
        _due_row("新卡节点", "甲板"),  # fsrs_due="" → 现在
        _due_row("逾期3天", "甲板", due_reason="scheduled", fsrs_due=_utc_z(now - timedelta(days=3))),
        _due_row("逾期1天", "甲板", due_reason="scheduled", fsrs_due=_utc_z(now - timedelta(days=1))),
        _due_row("乙板节点", "乙板", due_reason="scheduled", fsrs_due=_utc_z(now - timedelta(days=2))),
    ]
    _mk_vault(root, "vault-a", _nodes_projection("vault-a", rows))

    p = client.get("/api/v1/review/overview").json()["vaults"][0]["projection"]
    by = {b["board"]: b for b in p["boards"]}
    assert [n["node"] for n in by["甲板"]["nodes"]] == ["逾期3天", "逾期1天", "新卡节点"], (
        "逾期最久在前, 新卡(=现在)垫后"
    )
    assert len(by["甲板"]["nodes"]) == by["甲板"]["due"] == 3
    assert [n["node"] for n in by["乙板"]["nodes"]] == ["乙板节点"]

    page = client.get("/api/v1/review/overview/page").text
    assert page.count("<details") == 2, "两个有到期节点的板各一个折叠区"
    assert "展开 3 个到期节点" in page and "展开 1 个到期节点" in page
    # 折叠区必须在整宽行里 (塞进"白板名"单元格会把第一列撑宽挤扁其余四列)
    assert '<td colspan="5"' in page


def test_g64_node_fields_are_rendered_humanized(overview_env):
    """② 字段渲染: 桶位中文标签 / 到期人话 / why_due 原文都上页。"""
    root, client = overview_env
    now = _now_local()
    rows = [
        _due_row(
            "学习中的节点",
            "甲板",
            due_reason="scheduled",
            fsrs_due=_utc_z(now - timedelta(days=5)),
            bucket="learning_queue",
            why_due="10 分钟前答错，回炉重学",
        ),
        _due_row("崭新节点", "甲板", bucket="new", why_due="新卡未排期，视同即刻到期 · 从未考察"),
    ]
    _mk_vault(root, "vault-a", _nodes_projection("vault-a", rows))
    page = client.get("/api/v1/review/overview/page").text

    # ⚠ 曾经写成 `assert "新卡" in page` —— 「新卡」在页面上还出现在**列头 <th>**、
    # 卡片汇总行「· 新卡 N」、分层行「分层 · 新卡 N」和 why_due 正文里, 那条断言
    # 零区分力: 桶位标签一个都不渲染它照样过（收官审计抓到）。
    # 改成按标签的**实际标记**取值来断言。
    # 顺序 = 紧迫度: 已逾期的 learning_queue 在前, 新卡("现在")垫后
    assert _bucket_tags(page) == ["学习中", "新卡"], f"两个节点应各渲染一个桶位标签, 实为 {_bucket_tags(page)}"
    assert "learning_queue" not in page, "机器枚举名不该漏到页面上"
    assert "10 分钟前答错，回炉重学" in page, "why_due 原文照登"
    assert "逾期5天" in page and "现在" in page, "到期时刻要人话化"


def test_g64_node_deeplink_percent_encoding(overview_env):
    """③ 深链编码: obsidian://open?vault=<库>&file=节点%2F<名>.md,
    库名与节点名分别 percent-encode (含中文 / 空格 / & / # / ?)。"""
    root, client = overview_env
    tricky = "A&B #1 ? 递归 base-case"
    rows = [_due_row(tricky, "甲板")]
    _mk_vault(root, "库 名&带符号", _nodes_projection("库 名&带符号", rows))

    page = client.get("/api/v1/review/overview/page").text
    expect = (
        "obsidian://open?vault="
        + quote("库 名&带符号", safe="")
        + "&amp;file="  # HTML 属性里 & 转义为 &amp;
        + quote(f"节点/{tricky}.md", safe="")
    )
    assert expect in page, "节点深链缺失或未按 percent-encode 约定"
    # ⚠ 曾经写成 `assert "%2F" in expect` —— expect 是**本测试自己**用
    # quote(safe="") 拼的, 那条断言恒真、对实现零约束（收官审计抓到）。
    # 要断言的是**页面**里出现了编码后的分隔符, 且没有出现裸斜杠形态。
    assert "%2F" in page, "页面上的节点深链必须把路径分隔符编码成 %2F"
    assert "file=节点/" not in page, "不许出现未编码的裸 `节点/` 形态"
    # 板深链与节点深链指向不同目录, 不许互相串
    assert quote("原白板/甲板.md", safe="") in page


def test_g64_degradations(overview_env):
    """④ 降级三态: 旧投影(无 bucket/why_due)不伪造分层标签 / 零到期板无折叠区 /
    无投影库不出现任何节点深链 (沿 CARD-D1 不做假链接的口径)。"""
    root, client = overview_env
    now_iso = _now_local().isoformat(timespec="seconds")
    # 旧投影: _projection 默认的 due_nodes 行本来就没有 bucket/why_due
    _mk_vault(root, "vault-old", _projection("vault-old", generated_at=now_iso, due=["老节点"]))
    _mk_vault(root, "vault-none")  # 无投影

    data = client.get("/api/v1/review/overview").json()
    old = {v["vault_id"]: v for v in data["vaults"]}["vault-old"]["projection"]
    node = old["boards"][0]["nodes"][0]
    assert node["bucket"] is None and node["why_due"] is None, "缺省就是 None, 不许编"

    page = client.get("/api/v1/review/overview/page").text
    assert "展开 1 个到期节点" in page, "旧投影一样能展开 — 只是少了桶位标签"
    # ⚠ 曾经把这条负断言绑死在一段 CSS 子串上 —— 改一下样式它就恒真了
    # （收官审计抓到）。改用与正向断言**同一个** _bucket_tags 取值器:
    # 正向用例证明它取得到标签, 这里证明旧投影下取到的是空 —— 同一把尺子。
    assert _bucket_tags(page) == [], f"旧投影不许伪造桶位标签, 实为 {_bucket_tags(page)}"
    assert quote("节点/老节点.md", safe="") in page, "旧投影的节点深链照常"
    # 无投影库: 该库卡片里不许有任何节点深链
    assert "vault-none" in page and "该库尚无今日复习投影" in page
    assert page.count(quote("节点/", safe="")) == 1, "只有 vault-old 那一个节点链, 无投影库零链接"


def test_g64_zero_due_board_has_no_expander(overview_env):
    """④(续) 零到期板 (只有未来排期) 没有可展开的到期节点 — 不给空折叠区。"""
    root, client = overview_env
    now = _now_local()
    payload = _projection(
        "vault-a",
        generated_at=now.isoformat(timespec="seconds"),
        due_nodes=[_due_row("甲节点", "甲板")],
        stats={"due_nodes": 1},
        upcoming=[{"board": "零到期板", "next_due": _utc_z(now + timedelta(days=3)), "node": "未来节点"}],
    )
    _mk_vault(root, "vault-a", payload)

    p = client.get("/api/v1/review/overview").json()["vaults"][0]["projection"]
    by = {b["board"]: b for b in p["boards"]}
    assert by["零到期板"]["due"] == 0 and by["零到期板"]["nodes"] == []
    page = client.get("/api/v1/review/overview/page").text
    assert page.count("<details") == 1, "只有甲板一个折叠区"
    assert "零到期板" in page and "未来节点" not in page, "未来节点不在 due_nodes 里, 不该被渲染成到期节点"


def test_g64_hostile_node_strings_are_escaped(overview_env):
    """⑤ XSS 转义: 节点名与 why_due 都是外部输入, 直接进 HTML 即注入。"""
    root, client = overview_env
    payload_node = 'n"><img src=x onerror=1>'
    payload_why = "why<b>粗体</b>&符号"
    rows = [_due_row(payload_node, "甲板", bucket="new", why_due=payload_why)]
    _mk_vault(root, "vault-a", _nodes_projection("vault-a", rows))

    page = client.get("/api/v1/review/overview/page").text
    assert "<img src=x onerror=1>" not in page
    assert "&lt;img src=x onerror=1&gt;" in page
    assert "<b>粗体</b>" not in page and "&lt;b&gt;粗体&lt;/b&gt;" in page
    assert "&amp;符号" in page


def test_g64_dirty_bucket_or_why_degrades_corrupt_not_ok(overview_env):
    """⑥ 形状垃圾门禁: bucket/why_due 此前只在有顶层 buckets 时被 _gate_buckets
    间接核对 —— 旧投影下它们完全没验形。既然本卡要把它们渲染出来, 就必须自己
    门禁, 否则形状垃圾直通页面。

    每一条都必须降级为 corrupt, 且健康库不受拖累。
    """
    root, client = overview_env
    _now_iso = _now_local().isoformat(timespec="seconds")
    _mk_vault(root, "vault-ok", _nodes_projection("vault-ok", [_due_row("好节点", "甲板")]))

    hostile = {
        "bad-bucket-enum": _due_row("n", "甲板", bucket="不是桶名"),
        "bad-bucket-type": _due_row("n", "甲板", bucket=3),  # pyright: ignore[reportArgumentType]
        # Codex-G6-4 round-1: due_nodes 行按构造只可能落到期三桶。放行
        # bucket="future" 会让一个已逾期节点在页面上被标成「未来」——
        # 比不标更坏, 那是主动误导
        "bad-bucket-nondue": _due_row(
            "n", "甲板", due_reason="scheduled", fsrs_due="2020-01-01T00:00:00Z", bucket="future"
        ),
        "bad-bucket-due-today": _due_row(
            "n", "甲板", due_reason="scheduled", fsrs_due="2020-01-01T00:00:00Z", bucket="due_today"
        ),
        # new 桶 ⟺ due_reason=="new" (与 _gate_buckets ④ 同一条构造律的逆检查;
        # 顶层无 buckets 键时那个函数根本不跑)
        "bad-bucket-new-vs-scheduled": _due_row(
            "n", "甲板", due_reason="scheduled", fsrs_due="2020-01-01T00:00:00Z", bucket="new"
        ),
        "bad-bucket-duenow-vs-new": _due_row("n", "甲板", due_reason="new", bucket="due_now"),
        "bad-why-empty": _due_row("n", "甲板", why_due=""),
        "bad-why-type": _due_row("n", "甲板", why_due=["列表"]),  # pyright: ignore[reportArgumentType]
        "bad-why-null-but-bucket": _due_row("n", "甲板", why_due=None),  # pyright: ignore[reportArgumentType]
    }
    for name, row in hostile.items():
        _mk_vault(root, name, _nodes_projection(name, [row]))

    data = client.get("/api/v1/review/overview").json()
    by = {v["vault_id"]: v for v in data["vaults"]}
    assert by["vault-ok"]["status"] == "ok", by["vault-ok"].get("error")
    for name in hostile:
        if name == "bad-why-null-but-bucket":
            # why_due 显式 null = 旧投影缺省形态, 合法 (只是不渲染那一行)
            assert by[name]["status"] == "ok", f"{name} 应放行: {by[name].get('error')}"
            continue
        assert by[name]["status"] == "corrupt", f"{name} 应 corrupt, 实为 {by[name]['status']}"
    assert client.get("/api/v1/review/overview/page").status_code == 200, "脏库不许把页面打成 500"


def test_g64_nodes_are_purely_additive_and_same_source(overview_env):
    """⑦ 加性契约 + 同源: boards 行只多一个 nodes 键, 既有键一个不动;
    nodes 逐条与 due_nodes 明细同源 (身份/reason/fsrs_due/bucket/why_due 全等),
    合计 == 该板 due。"""
    root, client = overview_env
    now = _now_local()
    rows = [
        _due_row(
            "甲1",
            "甲板",
            due_reason="scheduled",
            fsrs_due=_utc_z(now - timedelta(days=2)),
            bucket="due_now",
            why_due="到期了",
        ),
        _due_row("甲2", "甲板", bucket="new", why_due="新卡"),
        _due_row("乙1", "乙板", bucket="new", why_due="新卡"),
    ]
    _mk_vault(root, "vault-a", _nodes_projection("vault-a", rows))

    p = client.get("/api/v1/review/overview").json()["vaults"][0]["projection"]
    for b in p["boards"]:
        assert set(b) == {
            "board",
            "due",
            "due_new",
            "placeholder",
            "earliest",
            "nodes",
            "why_this_board",
            "estimated_minutes",
        }, f"boards 行只许加性追加, 实为 {sorted(b)}"
        assert len(b["nodes"]) == b["due"]
        for n in b["nodes"]:
            assert set(n) == {"node", "due_reason", "fsrs_due", "bucket", "why_due"}
    src = {r["node"]: r for r in rows}
    for b in p["boards"]:
        for n in b["nodes"]:
            o = src[n["node"]]
            assert (n["due_reason"], n["fsrs_due"], n["bucket"], n["why_due"]) == (
                o["due_reason"],
                o["fsrs_due"],
                o["bucket"],
                o["why_due"],
            ), f"{n['node']} 与 due_nodes 明细不同源"
    assert sum(len(b["nodes"]) for b in p["boards"]) == p["due_count"] == 3


def test_g64_narrow_viewport_structural_guarantees(overview_env):
    """⑧ 窄窗不横溢 (结构性断言 —— 真实像素测量属用户 UAT 那一步)。

    锁三条会导致 375px 横向溢出的写法:
      (a) 表格必须仍在 overflow-x:auto 容器里 (宽内容自己滚, 不推 body);
      (b) 节点条目必须允许长词折行 (overflow-wrap/word-break) —— 长节点名或
          长 why_due 不折行就会把整行顶宽;
      (c) 页面里不许出现固定 px 的 width/min-width (相对单位才随窗口缩)。
    """
    root, client = overview_env
    rows = [
        _due_row(
            "一个非常非常长的节点名字用来测试折行行为" * 3,
            "甲板",
            bucket="new",
            why_due="一段很长的理由" * 20,
        )
    ]
    _mk_vault(root, "vault-a", _nodes_projection("vault-a", rows))
    page = client.get("/api/v1/review/overview/page").text

    assert "overflow-x:auto" in page, "(a) 宽表格要有自己的横向滚动容器"
    assert "overflow-wrap:anywhere" in page and "word-break:break-word" in page, "(b) 节点条目必须能折行"
    assert not re.search(r"(?<!max-)width:\s*\d+px", page), "(c) 不许固定 px 宽度"
    # viewport meta 在位 (缺了移动端会按 980px 虚拟视口渲染, 必横溢)
    assert 'name="viewport" content="width=device-width, initial-scale=1"' in page


# ════════════════════════════════════════════════════════════════════
# CARD-G3-6b (BATCH-2026-09-01-第八批): 板级解释加性消费
# 生产器投影内复算落盘, 本端点只门禁 + 渲染, 一个数都不算。
# ════════════════════════════════════════════════════════════════════


def _top_row(board: str, top_node: str, **extra) -> dict:
    """top_boards 行真形状 (旧七字段 + G3-6b 三件套)。extra 注入垃圾用。"""
    row = {
        "board": board,
        "top_node": top_node,
        "priority": 1.0,
        "pending": 1,
        "idle_days": None,
        "difficulty": "",
        "next_due": "",
        "why_this_board": "1 个节点到期 · 最该考的从未考察 · 这块板从未被推荐过",
        "estimated_minutes": 5,
        "factors": {"due_total": 1},
    }
    row.update(extra)
    return row


def test_g36b_board_rows_carry_explain_from_top_boards(overview_env):
    """(d) 消费链路: top_boards 行的解释/分钟按板名挂到 boards 行; 榜外板与
    旧投影 → None。JSON 端先锁数据面。"""
    root, client = overview_env
    rows = [
        _due_row("甲1", "甲板", bucket="new", why_due="新卡"),
        _due_row("乙1", "乙板", bucket="new", why_due="新卡"),
        _due_row("丙1", "丙板", bucket="new", why_due="新卡"),
    ]
    top = [
        _top_row("甲板", "甲1"),
        _top_row("乙板", "乙1"),
        _top_row("丙板", "丙1"),
    ]
    proj = _nodes_projection("vault-a", rows, top=top)
    _mk_vault(root, "vault-a", proj)
    p = client.get("/api/v1/review/overview").json()["vaults"][0]["projection"]
    by = {b["board"]: b for b in p["boards"]}
    assert by["甲板"]["why_this_board"].startswith("1 个节点到期")
    assert by["甲板"]["estimated_minutes"] == 5
    assert by["乙板"]["why_this_board"] and by["乙板"]["estimated_minutes"] == 5


def test_g36b_page_renders_explain_row_and_escapes_hostile(overview_env):
    """(d) 页面渲染: 榜上板行下多一条「为什么是这块板 · 预计 N 分钟」整宽行,
    双字段都 html.escape。敌对串注入不产出任何可执行的标记。"""
    root, client = overview_env
    hostile_why = '到期待复习<script>alert("x")</script>&<b>粗体</b>'
    rows = [_due_row("甲1", "甲板", bucket="new", why_due="新卡")]
    top = [_top_row("甲板", "甲1", why_this_board=hostile_why, estimated_minutes=13)]
    _mk_vault(root, "vault-a", _nodes_projection("vault-a", rows, top=top))
    page = client.get("/api/v1/review/overview/page").text
    assert "为什么是这块板" in page, "解释行整行缺失"
    assert "预计 13 分钟" in page, "预计分钟缺失"
    assert "<script>" not in page and "<b>粗体</b>" not in page, "敌对串必须被转义"
    assert html.escape(hostile_why) in page, "why 原样 escape 后应在场"


def test_g36b_off_rank_and_old_projection_no_explain_row(overview_env):
    """(d) 缺字段整块不出现: 旧投影 (无新字段) 与榜外板都不渲染解释行,
    也不显示可能不可信的零分钟。"""
    root, client = overview_env
    # 旧投影: top_boards 行不带新字段 (_due_row 板只有一行, proj 不注入 top)
    rows = [_due_row("甲1", "甲板", bucket="new", why_due="新卡")]
    _mk_vault(root, "vault-a", _nodes_projection("vault-a", rows))
    page = client.get("/api/v1/review/overview/page").text
    assert "为什么是这块板" not in page, "旧投影不许伪造解释行"

    # 新投影但板数超上限: 第 4 块板不在 top_boards 榜内 → 无解释行
    rows4 = [_due_row(f"节点{i}", f"板{i}", bucket="new", why_due="新卡") for i in range(4)]
    top4 = [_top_row(f"板{i}", f"节点{i}") for i in range(3)]  # 只 3 块上榜
    _mk_vault(root, "vault-b", _nodes_projection("vault-b", rows4, top=top4))
    page_b = client.get("/api/v1/review/overview/page").text
    body_b = page_b[page_b.index("vault-b") :]
    assert body_b.count("为什么是这块板") == 3, f"只有榜上 3 板有解释行, 实得 {body_b.count('为什么是这块板')}"


def test_g36b_one_sided_explain_fields_render_nothing(overview_env):
    """Codex round-1 MEDIUM (原子对): 两字段由生产器成对产出, 单边在场不是
    "降级形态"而是半份配置 —— 解释行整块不出现, 不渲染没分钟的裸解释。"""
    root, client = overview_env
    rows = [_due_row("甲1", "甲板", bucket="new", why_due="新卡")]
    # 只有 why, 缺分钟
    top_why_only = [
        {
            "board": "甲板",
            "top_node": "甲1",
            "priority": 1.0,
            "pending": 1,
            "idle_days": None,
            "difficulty": "",
            "next_due": "",
            "why_this_board": "1 个节点到期 · 最该考的从未考察",
            "factors": {},
        }
    ]
    # 只有分钟, 缺 why
    top_mins_only = [
        {
            "board": "甲板",
            "top_node": "甲1",
            "priority": 1.0,
            "pending": 1,
            "idle_days": None,
            "difficulty": "",
            "next_due": "",
            "estimated_minutes": 5,
            "factors": {},
        }
    ]
    for label, top in (("只有why缺分钟", top_why_only), ("只有分钟缺why", top_mins_only)):
        _mk_vault(root, "vault-a", _nodes_projection("vault-a", rows, top=top))
        resp = client.get("/api/v1/review/overview/page")
        # 200 断言防门空转: 若实现变成半份配置渲染到一半抛异常被中间件兜成
        # 500 错误页, 错误页恰好不含解释行字样 —— 只查子串会把「崩了」误判
        # 成「整块不出现」(M8 变异实测)。单边缺省的正确行为是 200 且无解释行。
        assert resp.status_code == 200, f"{label}: 单边缺省必须正常渲染, 不许 500"
        assert "为什么是这块板" not in resp.text, f"{label}: 单边在场必须整块不出现"
    # 双在场恢复显示
    _mk_vault(root, "vault-a", _nodes_projection("vault-a", rows, top=[_top_row("甲板", "甲1")]))
    resp = client.get("/api/v1/review/overview/page")
    assert resp.status_code == 200
    assert "为什么是这块板" in resp.text and "预计 5 分钟" in resp.text


def test_g36b_garbage_explain_fields_degrade_corrupt_not_ok(overview_env):
    """消费即负责验形: why 非串 / minutes 负数或 bool → ValueError → corrupt,
    不给形状垃圾发 ok (与该文件所有被消费字段同一条纪律)。"""
    root, client = overview_env
    rows = [_due_row("甲1", "甲板", bucket="new", why_due="新卡")]
    clean_top = [_top_row("甲板", "甲1")]
    _mk_vault(root, "vault-a", _nodes_projection("vault-a", rows, top=clean_top))
    assert client.get("/api/v1/review/overview").json()["vaults"][0]["status"] == "ok"
    for label, top in (
        ("why非串", [_top_row("甲板", "甲1", why_this_board=123)]),
        ("why空串", [_top_row("甲板", "甲1", why_this_board="")]),
        ("分钟负数", [_top_row("甲板", "甲1", estimated_minutes=-1)]),
        ("分钟bool", [_top_row("甲板", "甲1", estimated_minutes=True)]),
    ):
        _mk_vault(root, "vault-a", _nodes_projection("vault-a", rows, top=top))
        entry = client.get("/api/v1/review/overview").json()["vaults"][0]
        assert entry["status"] == "corrupt", f"{label}: 垃圾必须走 corrupt 降级"
        # 还原干净投影, 让下一轮断言不被上一轮污染
        _mk_vault(root, "vault-a", _nodes_projection("vault-a", rows, top=clean_top))
        assert client.get("/api/v1/review/overview").json()["vaults"][0]["status"] == "ok"


# ════════════════════════════════════════════════════════════════════
# CARD-G6-1 round-3 整改门 (Codex 复核后加固)
# ════════════════════════════════════════════════════════════════════


def test_zero_exit_without_republishing_is_not_success(refresh_env, monkeypatch, tmp_path):
    """Codex round-3 HIGH: 只查"盘上有一份可消费 JSON"证不了本次重建成功。

    盘上原本就有好投影时, 一个 rc=0 却什么都不写的生产器会被算成成功。
    发布证明 = json 的 (mtime_ns, sha256) 相对本次调用前必须变过。
    """
    import app.api.v1.endpoints.review_overview as mod

    root, client = refresh_env
    vault = _mk_node_vault(root, "vault-nore", {"甲": _node_md()})
    assert client.post(_REFRESH_URL, data={"vault_id": "vault-nore"}).status_code == 200
    good = (vault / "outputs" / "今日复习.json").read_bytes()

    noop = tmp_path / "noop2.py"
    noop.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    monkeypatch.setenv(mod._PICK_SCRIPT_ENV, str(noop))

    resp = client.post(_REFRESH_URL, data={"vault_id": "vault-nore"})
    assert resp.status_code == 503, "盘上有好投影也不能把'什么都没做'算成重建成功"
    assert resp.json()["detail"]["error"] == "projection_not_republished"
    assert (vault / "outputs" / "今日复习.json").read_bytes() == good, "失败路径不许动盘上产物"


def test_zero_exit_with_only_json_is_not_success(refresh_env, monkeypatch, tmp_path):
    """产物不成对 (只有 json 没有 md) 同样不算重建成功 —— md 是人读的那一份,
    缺了它页面看着正常、Obsidian 里却没有今日复习。"""
    import app.api.v1.endpoints.review_overview as mod

    root, client = refresh_env
    _mk_node_vault(root, "vault-jsononly", {"甲": _node_md()})
    half = tmp_path / "half.py"
    half.write_text(
        "import sys, pathlib, json, datetime\n"
        "v = pathlib.Path(sys.argv[sys.argv.index('--vault') + 1])\n"
        "(v / 'outputs').mkdir(parents=True, exist_ok=True)\n"
        "p = {'schema_version': 3, 'vault_id': v.name, 'top_boards': [], 'upcoming': [],\n"
        "     'due_nodes': [], 'ineligible': {'placeholder': [], 'test_excluded': [], 'corrupt': []},\n"
        "     'stats': {'due_nodes': 0}, 'unassigned_nodes': [], 'notification': None,\n"
        "     'date': datetime.date.today().isoformat(),\n"
        "     'generated_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds')}\n"
        "(v / 'outputs' / '今日复习.json').write_text(json.dumps(p, ensure_ascii=False), encoding='utf-8')\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(mod._PICK_SCRIPT_ENV, str(half))

    resp = client.post(_REFRESH_URL, data={"vault_id": "vault-jsononly"})
    assert resp.status_code == 503
    assert resp.json()["detail"]["error"] == "projection_md_missing"


def test_hostname_host_is_refused_ip_and_localhost_pass(refresh_env, monkeypatch):
    """Codex round-3: 期望 Origin 是拿请求自身 Host 拼的 —— DNS rebinding 下
    攻击者的域名解析到本机, Host/Origin/Sec-Fetch-Site 会同时"合法", 整道
    同源门被绕过。rebinding 必须依赖**域名**, 所以只放行 localhost 与 IP 字面量。
    """
    import app.api.v1.endpoints.review_overview as mod

    root, _client = refresh_env
    _mk_node_vault(root, "vault-host", {"甲": _node_md()})
    from fastapi.testclient import TestClient

    from app.main import app

    for base, ok in (
        ("http://127.0.0.1:8011", True),
        ("http://localhost:8011", True),
        # ⚠ 局域网 IP 必须放行 —— 但如实说明: 当前端口只绑 127.0.0.1 (实测局域网
        # 连不上), 这一支现在走不到, 锁的是"将来放开监听时不必改代码"这条纵深防御
        ("http://192.168.1.9:8011", True),
        ("http://evil.example.com", False),
        ("http://my-mac.local:8011", False),
    ):
        c = TestClient(app, base_url=base)
        r = c.post(_REFRESH_URL, data={"vault_id": "vault-host"})
        if ok:
            assert r.status_code == 200, f"{base} 应放行, 实为 {r.status_code} {r.text[:200]}"
        else:
            assert r.status_code == 403, f"{base} 应拒绝, 实为 {r.status_code}"
            assert r.json()["detail"]["error"] == "host_not_allowed"

    # IPv6 回环: TestClient 的 base_url 解析不了 "http://[::1]:8011" (httpx 限制,
    # 非生产缺陷), 所以直接对**生产函数**喂一个 IPv6 回环请求。
    # ⚠ 曾经写成 `assert ipaddress.ip_address("::1")` —— 那是在断言 stdlib,
    # 对被测代码零约束（收官审计抓到）。要走的是 _assert_same_origin 本身。
    from starlette.requests import Request as _Req

    v6 = _Req(
        {
            "type": "http",
            "method": "POST",
            "path": _REFRESH_URL,
            "headers": [(b"host", b"[::1]:8011")],
            "server": ("::1", 8011),
            "scheme": "http",
            "query_string": b"",
        }
    )
    assert v6.url.hostname == "::1", "starlette 会脱掉方括号 — 前提校验"
    mod._assert_same_origin(v6)  # 不抛 = IPv6 回环被放行

    # 部署方显式列出的主机名可放行 (Tailscale MagicDNS / mDNS 名的逃生口)
    monkeypatch.setenv(mod._ALLOWED_HOSTS_ENV, "my-mac.local, another.host")
    c = TestClient(app, base_url="http://my-mac.local:8011")
    assert c.post(_REFRESH_URL, data={"vault_id": "vault-host"}).status_code == 200


def test_form_path_in_progress_shows_notice_not_fake_success(refresh_env):
    """Codex round-3: 在飞时若照常 303 回总览页, 用户看到的与成功一模一样
    (数字没变) —— 又是一次"看起来像成功"。必须给一页如实的等待提示。"""
    import app.api.v1.endpoints.review_overview as mod

    root, client = refresh_env
    vault = _mk_node_vault(root, "vault-prog", {"甲": _node_md()})
    key = str(Path(root).resolve() / "vault-prog")
    lock = threading.Lock()
    with mod._refresh_guard:
        mod._refresh_locks[key] = lock
    assert lock.acquire(blocking=False)
    try:
        resp = client.post(_REFRESH_URL, data={"vault_id": "vault-prog", "redirect": "page"}, follow_redirects=False)
    finally:
        lock.release()

    assert resp.status_code == 200 and resp.headers["content-type"].startswith("text/html")
    assert "正在重建中" in resp.text and "回到总览页" in resp.text
    assert "<script" not in resp.text.lower()
    assert not (vault / "outputs").exists(), "在飞时第二个请求不许也去写盘"


def test_form_path_debounced_shows_notice_not_fake_success(overview_env, monkeypatch):
    """⛔ 收官审计: round-3 只给 in_progress 做了提示页, 把 **debounced 漏在原地**。

    失败场景很日常: 用户刚做完一道题 (写了 fsrs_due), 10 秒内点刷新 → 拿到与成功
    **逐字节相同**的 303 + 相同 Location + 空 body → 页面看着刷新了、数字却没动,
    而他没有任何办法知道"这次根本没重建"。
    纪律: **凡是没真重建的分支, 都不许走那条与成功同形的 303**。
    """
    import app.api.v1.endpoints.review_overview as mod

    monkeypatch.delenv(mod._PICK_SCRIPT_ENV, raising=False)
    monkeypatch.setattr(mod, "_REFRESH_TTL_SECONDS", 300.0)  # 有窗口才测得出 debounced
    root, client = overview_env
    _mk_node_vault(root, "vault-deb", {"甲": _node_md()})

    first = client.post(_REFRESH_URL, data={"vault_id": "vault-deb", "redirect": "page"}, follow_redirects=False)
    assert first.status_code == 303, "第一次是真重建 → PRG 303"

    second = client.post(_REFRESH_URL, data={"vault_id": "vault-deb", "redirect": "page"}, follow_redirects=False)
    assert second.status_code != 303, "被去抖的一次不许与成功同形"
    assert second.status_code == 200 and second.headers["content-type"].startswith("text/html")
    assert "刚刚才刷新过" in second.text
    assert "没有" in second.text and "重新计算" in second.text, "必须明说这次没重建"
    assert "回到总览页" in second.text
    assert "<script" not in second.text.lower()

    # 两条"没真重建"的分支都不许 303 —— 用 rebuilt 而不是逐个 reason 判, 将来
    # 新增第三种 reason 时这条纪律自动覆盖它
    assert second.text != first.text


def test_allowed_hosts_env_is_normalized_like_url_hostname(refresh_env, monkeypatch):
    """⛔ 收官审计: `request.url.hostname` 是 urlsplit 归一过的 —— **小写、不含端口、
    IPv6 去方括号**。白名单原来只 strip 后裸比, 于是用户照着地址栏里看到的东西去配
    (`My-Mac.local` 或 `my-mac.local:8011`) 会继续 403, 而错误信息没说要小写、不带端口
    —— 一个"照做了却还是不行"的坑。
    """
    import app.api.v1.endpoints.review_overview as mod
    from fastapi.testclient import TestClient

    from app.main import app

    root, _client = refresh_env
    _mk_node_vault(root, "vault-hostnorm", {"甲": _node_md()})

    for raw in ("My-Mac.local", "my-mac.local:8011", "  MY-MAC.LOCAL  ", "[::1]:8011,My-Mac.local"):
        monkeypatch.setenv(mod._ALLOWED_HOSTS_ENV, raw)
        assert "my-mac.local" in mod._extra_allowed_hosts(), f"{raw!r} 应归一到 my-mac.local"
        c = TestClient(app, base_url="http://my-mac.local:8011")
        r = c.post(_REFRESH_URL, data={"vault_id": "vault-hostnorm"})
        assert r.status_code == 200, f"配了 {raw!r} 之后应放行, 实为 {r.status_code} {r.text[:200]}"

    # IPv6 带方括号与端口也要能配
    monkeypatch.setenv(mod._ALLOWED_HOSTS_ENV, "[fd00::1]:8011")
    assert mod._extra_allowed_hosts() == frozenset({"fd00::1"})
    # 空 / 纯逗号不许产出空串条目（空串会匹配 hostname 为空的请求）
    monkeypatch.setenv(mod._ALLOWED_HOSTS_ENV, " , ,, ")
    assert mod._extra_allowed_hosts() == frozenset()


def test_review_enabled_markers_constant_is_the_single_source(refresh_env):
    """⛔ 收官审计: `_REVIEW_ENABLED_MARKERS` 一度是**死常量** —— 定义处带着
    "生产器对一个库的最低要求"的注释, 而 `_pick_failure_hint` 内联重写了同一对判据,
    全仓零引用它。以后有人按注释改常量, 提示文案不会跟着变, 且无人报警。

    本用例通过**改常量**来证明它真的是唯一真相源。
    """
    import app.api.v1.endpoints.review_overview as mod

    root, _client = refresh_env
    weird = _mk_vault(root, "改了常量的库")
    (weird / "节点").mkdir()
    (weird / ".claude" / "scripts").mkdir(parents=True)
    (weird / ".claude" / "scripts" / "decay_beta.py").write_text("PRIOR_A=1\n", encoding="utf-8")

    # 常量说还要一个不存在的东西 → 提示必须点名它 (证明提示读的就是这个常量)
    orig = mod._REVIEW_ENABLED_MARKERS
    try:
        mod._REVIEW_ENABLED_MARKERS = orig + (("这个文件根本不存在.md", False),)
        hint = mod._pick_failure_hint(weird)
        assert hint and "这个文件根本不存在.md" in hint, f"提示未跟随常量, 实为 {hint!r}"
    finally:
        mod._REVIEW_ENABLED_MARKERS = orig

    # 还原后该库两项齐全 → 无提示
    assert mod._pick_failure_hint(weird) is None


def test_repeated_refresh_with_zero_changes_still_succeeds(refresh_env):
    """⚠ 覆盖缺口补测: 原地连点、中间**一个字都不改**, 每次都必须成功。

    这条不是理论推演 —— 实测发现 generated_at 是**秒级**精度, 同一秒内的
    多次重建产出**逐字节相同**的 JSON (sha 全等)。也就是说 round-3 的"发布
    证明"在这条最常见的用户路径上, 完全靠 sha 之外的信号撑着。若指纹只用
    sha, 用户连点第二下就会收到 503 —— 一个把正常操作判成失败的 BLOCKER。
    """
    root, client = refresh_env
    vault = _mk_node_vault(root, "vault-nochange", {"甲": _node_md()})
    proj = vault / "outputs" / "今日复习.json"

    sigs = []
    for i in range(5):
        r = client.post(_REFRESH_URL, data={"vault_id": "vault-nochange"})
        # ← 这条才是本用例的承重断言
        assert r.status_code == 200, f"第{i + 1}次连点应成功, 实为 {r.status_code} {r.text[:300]}"
        assert r.json()["rebuilt"] is True
        st = proj.stat()
        sigs.append((st.st_ino, st.st_mtime_ns))

    assert len(set(sigs)) == len(sigs), "inode/mtime 必须每次都变 —— 它们是这条路径上唯一的发布信号"

    # 前提的**确定性**表述: generated_at 是秒级精度 (无小数秒), 因此同一秒内的
    # 两次重建必然产出逐字节相同的 JSON。
    # ⚠ 不要写成"5 次的 sha 全等" —— 循环可能跨过秒边界, 那是一条按时序抽签的
    # flaky 断言 (本用例首次运行就这样红过一次)。结构事实才是可断言的那个。
    gen = json.loads(proj.read_text(encoding="utf-8"))["generated_at"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2}|Z)", gen), (
        f"generated_at 应为秒级精度且无小数秒, 实为 {gen!r} —— 若生产器改成了亚秒精度, "
        f"内容会每次都变, 本用例锁的风险面需重新评估"
    )


def test_publish_fingerprint_uses_three_independent_signals(refresh_env, tmp_path):
    """指纹必须是 (inode, mtime_ns, sha) 三元组。

    三个信号各自都会在某类文件系统上退化 (实测):
      · sha    —— 同一秒内内容逐字节相同
      · mtime  —— 容器 /tmp 的 overlayfs 上 6 次 os.replace 只得 3 个不同值
      · inode  —— 同一 overlayfs 上会被复用 (在两个值间轮换)
    生产挂载 (/vaults VirtioFS) 与宿主 APFS 上 inode 与 mtime 都是每次必变。
    """
    import app.api.v1.endpoints.review_overview as mod

    p = tmp_path / "x.json"
    p.write_text("a", encoding="utf-8")
    fp = mod._publish_fingerprint(p)
    assert isinstance(fp, tuple) and len(fp) == 3, f"指纹应为三元组, 实为 {fp!r}"
    st = p.stat()
    assert fp[0] == st.st_ino and fp[1] == st.st_mtime_ns
    assert fp[2] == hashlib.sha256(b"a").hexdigest()

    # os.replace 换 inode —— 内容与 mtime 都可能不变, inode 是最后一道
    tmp = tmp_path / "x.tmp"
    tmp.write_text("a", encoding="utf-8")
    os.replace(tmp, p)
    assert mod._publish_fingerprint(p) != fp, "os.replace 之后指纹必须不同"

    assert mod._publish_fingerprint(tmp_path / "根本不存在.json") is None


def test_child_tz_is_passed_through_so_parent_and_child_share_one_view(refresh_env, monkeypatch):
    """⛔ 收官审计抓到的真缺陷（CARD-G6-9c / D-18 反转后的形态）: 生产器的
    `payload["date"]` / md 标题 / 通知 id 全走**子进程看到的时区**。父子两侧只要
    看到的时区不同，同一个库的两条生成路径就会给出不同的 date，取决于谁最后写 ——
    而端点照样 rebuilt=true / status=ok，页面上没有任何异常信号。

    G6-9a 时这里是**强制**钉死一个固定显示时区名。D-18 裁定「今天 = 用户当前
    所在地」后，硬编码的强制值本身成了分叉源（用户换时区 ⇒ 页面按机器本地归日、
    refresh 重生成的 payload 仍是旧时区日），故改为**透传**。

    ⚠ 本用例**端到端**验：父进程 TZ 设成什么，真 subprocess 产出的 date 就必须
    按什么算。只断言 `_child_env()` 字典里有那个键是不够的 —— 那证不了子进程
    真按它算日期。
    """
    import app.api.v1.endpoints.review_overview as mod

    root, client = refresh_env

    # ── ① 父进程冒充容器（TZ=UTC，无 CANVAS_TZ）：子进程必须也按 UTC 归日 ──
    monkeypatch.delenv("CANVAS_TZ", raising=False)  # 让开 _pin_display_tz 夹具
    monkeypatch.setenv("TZ", "UTC")
    env = mod._child_env()
    assert env["TZ"] == "UTC", "父进程的 TZ 必须透传给子进程（不再强制覆盖）"
    assert "CANVAS_TZ" not in env, "父进程没设 CANVAS_TZ 时不该凭空出现"

    vault = _mk_node_vault(root, "vault-tz", {"甲": _node_md()})
    assert client.post(_REFRESH_URL, data={"vault_id": "vault-tz"}).status_code == 200
    payload = json.loads((vault / "outputs" / "今日复习.json").read_text(encoding="utf-8"))
    utc_today = datetime.now(timezone.utc).date().isoformat()
    assert payload["date"] == utc_today, (
        f"父进程 TZ=UTC 时 date={payload['date']!r} 应为 UTC 日 {utc_today!r} —— 父子两侧必须是同一个时区视图"
    )
    assert payload["generated_at"].endswith("+00:00"), (
        f"generated_at 应带 +00:00 偏移, 实为 {payload['generated_at']!r}"
    )
    md_head = (vault / "outputs" / "今日复习.md").read_text(encoding="utf-8").splitlines()[0]
    assert utc_today in md_head, f"md 标题也必须同源, 实为 {md_head!r}"
    noti = payload.get("notification")
    if noti:  # 有通知则 id 必须同日（否则会覆盖别一天那条推送）
        assert noti["id"] == f"canvas-review-{utc_today}"

    # ── ② CANVAS_TZ 显式覆盖：压过父进程 TZ，子进程按东京归日 ──
    #    这一段是 ① 的对照：没有它，① 的"UTC 日"分不清是"透传起作用"还是
    #    "这条路径恒用 UTC"。
    monkeypatch.setenv("CANVAS_TZ", "Asia/Tokyo")
    env2 = mod._child_env()
    assert env2["CANVAS_TZ"] == "Asia/Tokyo" and env2["TZ"] == "UTC", (
        f"CANVAS_TZ 与 TZ 都该透传, 实得 {env2.get('CANVAS_TZ')!r} / {env2.get('TZ')!r}"
    )
    vault2 = _mk_node_vault(root, "vault-tz2", {"甲": _node_md()})
    assert client.post(_REFRESH_URL, data={"vault_id": "vault-tz2"}).status_code == 200
    payload2 = json.loads((vault2 / "outputs" / "今日复习.json").read_text(encoding="utf-8"))
    assert payload2["generated_at"].endswith("+09:00"), (
        f"CANVAS_TZ=Asia/Tokyo 应压过 TZ=UTC, 实得 {payload2['generated_at']!r}"
    )

    # 读侧与写侧同一个来源: 端点自己算出来的名字, 就是它透传给子进程的那个
    assert mod._display_tz_name() == "Asia/Tokyo", f"读侧显示时区名与透传给子进程的值漂移了: {mod._display_tz_name()!r}"


# ════════════════════════════════════════════════════════════════════
# CARD-G6-7 完成本板反馈 (BATCH-2026-09-05-第十二批) —— Web UI 第一个写侧动作
# ════════════════════════════════════════════════════════════════════

_BOARD_DONE_URL = "/api/v1/review/overview/board-done"
_PAGE_URL = "/api/v1/review/overview/page"

#: (d) 门失败时打印的固定串。用它把「门红在哪一条」钉死 —— 负控与红跑证据
#: 都按这个字面量核对, 否则"门红了"可能只是夹具坏了 (假杀第二形态)。
_FSRS_GATE_MSG = "FSRS 面被写动"


#: (每个节点 md 的 fsrs_* 行, learning_events 的 (行数, sha) | None)
_FsrsFingerprint = tuple[dict[str, list[str]], "tuple[int, str] | None"]


def _fsrs_fingerprint(vault: Path) -> _FsrsFingerprint:
    """FSRS 调度面的指纹: 每个节点 md 的 **frontmatter 原始字节** + 事件账。

    只取 frontmatter 而不是整文件 sha —— 整文件 sha 会把无关改动 (比如正文
    排版) 也算成"动了 FSRS", 那样门一旦红, 没人知道红的是不是调度面。
    learning_events.jsonl 取 (行数, sha): 追加一行就变, 这正是要挡的那件事。

    ⚠ Codex round-1 LOW 整改: 初版取的是「整份文件里以 fsrs_ 开头的**行**」,
    有两个盲区 —— ① 不分 frontmatter 内外: 把结束 `---` 挪到 fsrs_due 之前
    (字段就此降级成正文, 生产器再也读不到它) 指纹不变; ② `splitlines()` 吃掉
    `\r`: CRLF ↔ LF 互换指纹不变。两者都不是"逐字节相同"。现在记 frontmatter
    块的**原始字节 sha**(管逐字节与边界) + 块内的 fsrs_* 行(让失败消息说得出
    是哪个字段动了)。两条盲区各有一条负控用例。
    """
    fm: dict[str, list[str]] = {}
    for md in sorted((vault / "节点").glob("*.md")):
        raw = md.read_bytes()
        rows = raw.split(b"\n")
        block: list[bytes] = []
        # BOM 容忍与生产消费面同口径: daily_review_pick.scan_nodes 的 frontmatter
        # 正则是 `^\ufeff?---\r?\n`, 明确认 BOM 开头的节点。判据比消费方窄 = 一整类
        # 真实节点在这道门里"没有 frontmatter", block 塌缩成 sha256(b"") —— 改它的
        # fsrs_due 指纹不变。⚠ 这是 round-1 那次收紧**自己引入的**能力净损失:
        # 收紧前的逐行 `startswith(b"fsrs_")` 反而抓得住 BOM 节点 (对抗复核实证)。
        if rows and rows[0].lstrip(b"\xef\xbb\xbf").rstrip(b"\r") == b"---":
            for ln in rows[1:]:
                if ln.rstrip(b"\r") == b"---":
                    break
                block.append(ln)
        joined = b"\n".join(block)
        fm[md.name] = [
            hashlib.sha256(joined).hexdigest(),
            *(ln.decode("utf-8", "surrogateescape") for ln in block if ln.startswith(b"fsrs_")),
        ]
    events = vault / "learning_events.jsonl"
    ev: "tuple[int, str] | None" = None
    if events.exists():
        raw = events.read_bytes()
        ev = (raw.count(b"\n"), hashlib.sha256(raw).hexdigest())
    return fm, ev


def _assert_fsrs_untouched(before: _FsrsFingerprint, after: _FsrsFingerprint) -> None:
    """(d) 唯一承重断言。负控与正例共用同一个函数 —— 两边判据必然同口径。"""
    assert after == before, f"{_FSRS_GATE_MSG}: before={before!r} after={after!r}"


#: 指纹失明时的固定串。⚠ round-2: 原先负控直接用 `pytest.raises(AssertionError)`,
#: 于是变异验证只能拿 pytest 的通用文案 "DID NOT RAISE" 当承重判据 —— 那条串
#: 分不出**是哪一条盲区**没盖住 (对抗复核指出)。改成带轴名的自有串, 每条盲区
#: 各自可被单独钉死。
_FSRS_BLIND_MSG = "指纹对该改动失明"


def _assert_fingerprint_detects(before: _FsrsFingerprint, after: _FsrsFingerprint, axis: str) -> None:
    """指纹必须把 `axis` 这种改动认出来; 认不出就抛一条**带轴名**的错。"""
    try:
        _assert_fsrs_untouched(before, after)
    except AssertionError:
        return
    raise AssertionError(f"{_FSRS_BLIND_MSG}: {axis}")


def _install_contaminating_write_point(monkeypatch, mod, vault: Path):
    """对照实现: 照常写完成账, 但**顺手**改一个节点的 fsrs_due。

    ⛔ 它只拆「不写 FSRS」这一条, 其余路径 (状态码 / PRG / state 内容)
    全部照旧 —— 门若因此变红, 红的只可能是 _assert_fsrs_untouched 那一条,
    不会是"把被测路径弄坏了所以哪里都红"(那种红证明不了门有牙)。
    """
    real = mod._write_board_done

    def contaminated(vault_dir, vaults_root, board, day):
        state_file = real(vault_dir, vaults_root, board, day)
        target = sorted((vault / "节点").glob("*.md"))[0]
        text = target.read_text(encoding="utf-8")
        target.write_text(text.replace("fsrs_due:", "fsrs_due: # 顺手改\nfsrs_due_shadow:"), encoding="utf-8")
        return state_file

    monkeypatch.setattr(mod, "_write_board_done", contaminated)


@pytest.fixture
def board_done_env(refresh_env, monkeypatch):
    """refresh_env + runner 模块的 BACKUPS 改指 tmp。

    ⛔ 必须当场断言补丁真的生效: runner.BACKUPS 的缺省值是**真实仓库**的
    backups/ (CANVAS_REPO 缺省), 一个忘了打补丁的用例会直接往现网 state
    上写。「预置到底有没有产生我以为的那个形态」要断言, 不能靠相信。
    """
    import app.api.v1.endpoints.review_overview as mod

    root, client = refresh_env
    script = mod._runner_script(Path(root))
    assert script is not None, f"找不到 {mod._RUNNER_BASENAME} — 本 fixture 的前提不成立"
    runner = mod._load_runner(script)
    monkeypatch.setattr(runner, "BACKUPS", Path(root) / "backups")
    probe = runner.state_path(Path(root) / "vault-probe")
    assert probe.is_relative_to(Path(root)), f"BACKUPS 补丁没生效 ({probe}) — 用例会写真实仓库"
    return root, client, runner, mod


def _state_of(runner, root: Path, vault_name: str) -> dict:
    return json.loads(runner.state_path(root / vault_name).read_text(encoding="utf-8"))


def test_g67_board_done_writes_only_state_and_never_touches_fsrs(board_done_env, monkeypatch):
    """完成条件 (d): 完成动作前后 fsrs_* 与 learning_events 逐字节相同。

    红/绿证据 (evidence-g67/): 置 G67_FSRS_CONTAMINATE=1 时本用例自己装上
    「顺手写 fsrs_due」的对照写点 → 门必须红在 _FSRS_GATE_MSG 上; 不置则绿。
    两跑之外还有常驻负控 test_g67_fsrs_gate_reddens_under_contaminating_write_point,
    保证这条性质留在 CI 里而不是只活在一次性证据里。

    写面同时锁死: 全树指纹的差集必须恰是 backups 目录 + 那一个 state 文件。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(
        root,
        "vault-fsrs",
        {
            "定义甲": _node_md(fsrs_due='"2099-01-01T00:00:00Z"'),
            "定义乙": _node_md(board="数学", fsrs_due='"2030-06-01T00:00:00Z"'),
        },
    )
    (vault / "learning_events.jsonl").write_text(
        '{"event":"quiz","node":"定义甲","at":"2026-09-01T00:00:00Z"}\n', encoding="utf-8"
    )
    if os.environ.get("G67_FSRS_CONTAMINATE") == "1":
        _install_contaminating_write_point(monkeypatch, mod, vault)

    before_fsrs = _fsrs_fingerprint(vault)
    assert any(x.startswith("fsrs_") for x in before_fsrs[0]["定义甲.md"]), (
        "夹具前提: 节点必须真的带 fsrs_* frontmatter 行, 否则门是空的"
    )
    assert before_fsrs[1] is not None, "夹具前提: 事件账必须真的存在, 否则那一半判据是空的"
    before_tree = _tree(root)

    resp = client.post(_BOARD_DONE_URL, data={"vault_id": "vault-fsrs", "board": "CS 61B"})
    assert resp.status_code == 200, resp.text

    # ⛔ 承重断言排第一: 对照写点让它先红, 而不是被别的断言抢先 (假杀)
    _assert_fsrs_untouched(before_fsrs, _fsrs_fingerprint(vault))

    body = resp.json()
    assert body["board"] == "CS 61B" and body["fsrs_touched"] is False
    assert body["done_date"] == mod._display_today()
    state_file = runner.state_path(vault)
    assert Path(body["state_path"]) == state_file
    assert not state_file.is_relative_to(vault), "完成账不许落在库内 (BACKUPS 在仓库下)"

    st = _state_of(runner, Path(root), "vault-fsrs")
    assert st["board_done"] == {"CS 61B": mod._display_today()}
    assert st["schema_version"] == runner.STATE_SCHEMA_VERSION

    after_tree = _tree(root)
    lock_file = runner.state_lock_path(vault)
    changed = {k for k in set(before_tree) | set(after_tree) if before_tree.get(k) != after_tree.get(k)}
    # CARD-G6-7-R: 允许集由两项扩为三项 —— save_state 现在先取一把跨进程
    # 文件锁, 那个锁文件必然落在 backups/ 里。这不是放宽 (集合仍是**恰好
    # 等于**), 新增的那一项由下面两条断言钉死: 它必须是空的, 且必须在库外。
    # 往锁 fd 里写内容、或把锁挪进 vault, 都会当场红。
    assert changed == {"backups", f"backups/{state_file.name}", f"backups/{lock_file.name}"}, (
        f"写面必须恰是 backups 目录 + 那一个 state 文件 + 那一把锁, 实为 {sorted(changed)}"
    )
    assert lock_file.stat().st_size == 0, "锁文件只做锁, 不许承载任何数据"
    assert not lock_file.is_relative_to(vault), "锁不许落在库内 (与完成账同一条纪律)"
    # 形态落进 -rA 存档: 验收单只引用这几行, 不自述数字
    backups = state_file.parent
    print(f"[g67r-writeface] backups={backups}")
    for entry in sorted(backups.iterdir()):
        print(f"[g67r-writeface]   {entry.name}  size={entry.stat().st_size}")
    assert sorted(p.name for p in backups.iterdir()) == sorted([state_file.name, lock_file.name]), (
        f"backups/ 里恰是 state + 锁两个文件, 实为 {sorted(p.name for p in backups.iterdir())}"
    )


def test_g67_fsrs_gate_reddens_under_contaminating_write_point(board_done_env, monkeypatch):
    """(d) 常驻负控: 换上「顺手写 fsrs_due」的写点, 上面那道门必须红。

    判据绑定到**具体那一条**断言 (_FSRS_GATE_MSG), 不是"某处失败了" ——
    变异体若因语法/路径坏掉而让别的断言先红, 本门同样不放行。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-neg", {"定义甲": _node_md(fsrs_due='"2099-01-01T00:00:00Z"')})
    _install_contaminating_write_point(monkeypatch, mod, vault)

    before = _fsrs_fingerprint(vault)
    resp = client.post(_BOARD_DONE_URL, data={"vault_id": "vault-neg", "board": "CS 61B"})
    assert resp.status_code == 200, "对照写点只污染 FSRS, 不许把请求本身弄坏 (否则红的是别的东西)"
    assert _state_of(runner, Path(root), "vault-neg")["board_done"] == {"CS 61B": mod._display_today()}, (
        "对照写点必须仍然把完成账写对 —— 拆的只是那一条守卫"
    )
    with pytest.raises(AssertionError) as ei:
        _assert_fsrs_untouched(before, _fsrs_fingerprint(vault))
    assert _FSRS_GATE_MSG in str(ei.value), f"红的不是 FSRS 那条断言: {ei.value}"


def test_g67_reuses_both_write_gates_and_writes_nothing_on_refusal(board_done_env):
    """完成条件 (c): 两道写侧门是**复用**不是复制, 且被拒时零写入。

    行为面而非文本面 —— 三种拒绝各一条, 每条都验"state 文件没被创建":
    跨站表单 403 / 库外软链 503 / 未知 vault 404。
    """
    root, client, runner, _mod = board_done_env
    _mk_node_vault(root, "vault-gate", {"甲": _node_md()})
    state_file = runner.state_path(Path(root) / "vault-gate")

    cross = client.post(
        _BOARD_DONE_URL,
        data={"vault_id": "vault-gate", "board": "CS 61B"},
        headers={"origin": "http://evil.example", "sec-fetch-site": "cross-site"},
    )
    assert cross.status_code == 403, cross.text
    assert cross.json()["detail"]["error"] == "cross_site_blocked"
    assert not state_file.exists(), "被同源门拒的请求不许留下任何完成账"

    assert client.post(_BOARD_DONE_URL, data={"vault_id": "不存在的库", "board": "b"}).status_code == 404
    assert not state_file.exists()


def test_g67_symlinked_vault_outside_root_is_refused(board_done_env, tmp_path_factory):
    """(c) 容纳门复用: VAULTS_ROOT 下指向库外的软链 → 503, 且零写入。"""
    root, client, runner, _mod = board_done_env
    outside = tmp_path_factory.mktemp("g67-outside")
    (outside / ".obsidian").mkdir()
    (root / "vault-link").symlink_to(outside, target_is_directory=True)

    resp = client.post(_BOARD_DONE_URL, data={"vault_id": "vault-link", "board": "CS 61B"})
    assert resp.status_code == 503, resp.text
    assert resp.json()["detail"]["error"] == "vault_outside_root"
    assert not runner.state_path(root / "vault-link").exists()


def test_g67_invalid_board_is_422_and_writes_nothing(board_done_env):
    """空板名 / 超长板名 → 422, 不写账 (state 文件不许被凭空创建)。"""
    root, client, runner, mod = board_done_env
    _mk_node_vault(root, "vault-bad", {"甲": _node_md()})
    state_file = runner.state_path(Path(root) / "vault-bad")

    for board in ("", "板" * (mod._BOARD_NAME_MAX + 1)):
        resp = client.post(_BOARD_DONE_URL, data={"vault_id": "vault-bad", "board": board})
        assert resp.status_code == 422, (board[:10], resp.text)
        assert not state_file.exists(), "422 之后不许留下 state"


def test_g67_zero_js_form_path_redirects_and_failure_keeps_status(board_done_env):
    """(c) 零 JS 表单路径: redirect=page → 303 回本页; 失败渲染错误页且状态码原样。

    错误页标题必须说的是**这个**动作 —— 用户刚点「这板做完了」, 页面写着
    「刷新失败」比没有错误页更糟 (他会去找刷新按钮的毛病)。
    """
    root, client, runner, _mod = board_done_env
    _mk_node_vault(root, "vault-form", {"甲": _node_md()})

    ok = client.post(
        _BOARD_DONE_URL,
        data={"vault_id": "vault-form", "board": "CS 61B", "redirect": "page"},
        follow_redirects=False,
    )
    assert ok.status_code == 303
    assert ok.headers["location"] == _PAGE_URL
    assert runner.state_path(Path(root) / "vault-form").exists()

    bad = client.post(
        _BOARD_DONE_URL,
        data={"vault_id": "不存在的库", "board": "CS 61B", "redirect": "page"},
        follow_redirects=False,
    )
    assert bad.status_code == 404, "失败不许伪装成 303 成功"
    assert "标记完成失败" in bad.text and "刷新失败" not in bad.text
    assert "vault_not_found" in bad.text


def _two_board_projection(vault_id: str, gen_iso: str) -> dict:
    """两块板、各一到期节点的最小 v3 投影 (折叠用例要两块板才说明得了问题)。"""
    proj = _projection(vault_id, generated_at=gen_iso, due=["节点甲"], board="CS 61B")
    proj["due_nodes"].append(
        {
            "node": "节点乙",
            "board": "数学",
            "state": "new",
            "pick": 1.0,
            "fsrs_due": "",
            "due_reason": "new",
            "last_examined": "",
            "difficulty": "",
        }
    )
    proj["top_boards"].append(
        {
            "board": "数学",
            "top_node": "节点乙",
            "priority": 0.5,
            "pending": 1,
            "idle_days": 1,
            "difficulty": "",
            "next_due": "",
        }
    )
    proj["stats"]["due_nodes"] = 2
    return proj


def test_g67_page_folds_done_board_without_dropping_it(board_done_env):
    """(c)(f) 零 JS 页: 标完成的板折进「已完成」区 —— **折叠不是删除**。

    三条判据缺一不可:
      ① 完成前两块板都在主表格且各带一个完成钮;
      ② 完成后该板不在主表格, 但仍在页面上 (details 内) —— 若实现改成
         从投影里剔除, 本条红 (那正是卡文硬边界禁止的做法);
      ③ 页面明示「不影响 FSRS」。
    """
    root, client, _runner, _mod = board_done_env
    vault = _mk_vault(
        root, "vault-page", _two_board_projection("vault-page", _now_local().isoformat(timespec="seconds"))
    )
    (vault / "节点").mkdir(exist_ok=True)

    page = client.get(_PAGE_URL).text
    # CARD-G6-6: 与本用例下半段 (G6-7-R) 同一条迁移 —— 原判据 count('name="board"')
    # 在推迟表单也带同名 hidden 之后不再表达"两块板各一个**完成**钮"。按 action
    # 归属判定更强 (每个动作各自可被违反), 不是放宽。
    assert page.count(f'action="{_BOARD_DONE_URL}"') == 2, "两块板各一个完成钮"
    assert page.count(f'action="{_BOARD_SNOOZE_URL}"') == 2, "两块板各一个推迟表单"
    assert "不影响 FSRS" in page
    assert "已完成（" not in page, "还没标完成就不该有已完成区"
    assert "已推迟（" not in page, "还没推迟就不该有已推迟区"

    assert client.post(_BOARD_DONE_URL, data={"vault_id": "vault-page", "board": "CS 61B"}).status_code == 200

    page2 = client.get(_PAGE_URL).text
    i = page2.index("已完成（1）")
    head, fold = page2[:i], page2[i:]
    assert "数学" in head and "CS 61B" not in head, "已完成板应从待做区移出"
    assert "CS 61B" in fold, "已完成板必须仍在页面上 (折叠区内), 不许被剔除"
    # CARD-G6-7-R: 原判据是 page2.count('name="board"') == 1。加了「取消完成」
    # 表单之后, 两个动作的 hidden input 同名, 计数不再表达"已完成板不该再带
    # **完成**钮"这个意图。换成按 action 归属判定 —— 更强 (两个动作各自可被
    # 违反), 不是放宽。撤销钮本身的位置由
    # test_g67r_page_offers_undo_only_in_the_done_section 单独守。
    assert fold.count(f'action="{_BOARD_DONE_URL}"') == 0, "已完成板不该再带完成钮"
    assert head.count(f'action="{_BOARD_DONE_URL}"') == 1, "未完成板仍要带完成钮"
    # JSON 侧同源: entry.board_done 与页面折叠的是同一份判定
    entry = next(v for v in client.get("/api/v1/review/overview").json()["vaults"] if v["vault_id"] == "vault-page")
    assert entry["board_done"] == ["CS 61B"]
    # 投影本体一个数都没动 (硬边界: 禁在投影层压制)
    assert entry["projection"]["due_count"] == 2
    assert sorted(r["board"] for r in entry["projection"]["boards"]) == ["CS 61B", "数学"]


def test_g67_done_expires_next_day_and_is_per_vault(board_done_env):
    """(f) 隔日自然失效 + 双库互不影响。

    「明天」不靠等: 直接把账里的日期改成昨天 —— 判定是 `值 == 今天`,
    所以昨天的值必须表现得和"没标过"完全一样, 且旧键**不删**(加性)。
    """
    root, client, runner, mod = board_done_env
    gen = _now_local().isoformat(timespec="seconds")
    _mk_vault(root, "vault-x", _two_board_projection("vault-x", gen))
    _mk_vault(root, "vault-y", _two_board_projection("vault-y", gen))

    assert client.post(_BOARD_DONE_URL, data={"vault_id": "vault-x", "board": "CS 61B"}).status_code == 200
    data = {v["vault_id"]: v for v in client.get("/api/v1/review/overview").json()["vaults"]}
    assert data["vault-x"]["board_done"] == ["CS 61B"]
    assert data["vault-y"]["board_done"] == [], "另一个库的完成账必须完全独立"
    assert not runner.state_path(root / "vault-y").exists(), "只写被点的那个库的 state"

    # 把日期改成昨天 = 时间往前走了一天
    sf = runner.state_path(root / "vault-x")
    st = json.loads(sf.read_text(encoding="utf-8"))
    yesterday = (datetime.fromisoformat(mod._display_today()) - timedelta(days=1)).date().isoformat()
    st["board_done"]["CS 61B"] = yesterday
    sf.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")

    data2 = {v["vault_id"]: v for v in client.get("/api/v1/review/overview").json()["vaults"]}
    assert data2["vault-x"]["board_done"] == [], "隔日的值必须自然失效"
    assert json.loads(sf.read_text(encoding="utf-8"))["board_done"] == {"CS 61B": yesterday}, "旧键不删 (加性)"
    assert "已完成（" not in client.get(_PAGE_URL).text


def test_g67_read_path_never_writes_even_for_corrupt_state(board_done_env):
    """(b) 读路径纯度: 损坏的 state 遇上 GET, **不许**被隔离改名。

    runner.load_state 对损坏文件的处置是 os.replace 隔离重建 —— 那是一次
    写盘。读侧若图省事复用它, GET /overview 就会改盘, 本模块的只读契约当场
    破掉。这条门盯的就是那个诱惑。
    """
    root, client, runner, _mod = board_done_env
    _mk_vault(root, "vault-corrupt", _two_board_projection("vault-corrupt", _now_local().isoformat(timespec="seconds")))
    sf = runner.state_path(root / "vault-corrupt")
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text('{"board_done": "不是个 dict", 这里还坏了', encoding="utf-8")

    before = _tree(root)
    assert client.get("/api/v1/review/overview").status_code == 200
    assert client.get(_PAGE_URL).status_code == 200
    after = _tree(root)

    assert before == after, "GET 路径动了盘 —— 只读契约被破坏"
    assert not list(sf.parent.glob("*.corrupt-*")), "读路径不许隔离改名"
    entry = next(v for v in client.get("/api/v1/review/overview").json()["vaults"] if v["vault_id"] == "vault-corrupt")
    assert entry["board_done"] == [], "读不出来就是没有完成记录, 不是 500"


def test_g67_write_path_quarantines_corrupt_state_and_rebuilds(board_done_env):
    """(b) 写路径反过来: 复用 runner 的隔离重建 —— 坏账不许把请求打成 500。"""
    root, client, runner, mod = board_done_env
    _mk_node_vault(root, "vault-wq", {"甲": _node_md()})
    sf = runner.state_path(root / "vault-wq")
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text('{"board_done": ["错型"]}', encoding="utf-8")

    resp = client.post(_BOARD_DONE_URL, data={"vault_id": "vault-wq", "board": "CS 61B"})
    assert resp.status_code == 200, resp.text
    assert list(sf.parent.glob("*.corrupt-*")), "错型 state 必须被隔离 (复用 runner 的既有行为)"
    st = json.loads(sf.read_text(encoding="utf-8"))
    assert st["board_done"] == {"CS 61B": mod._display_today()}
    assert st["schema_version"] == runner.STATE_SCHEMA_VERSION


def test_g67_state_path_is_same_source_as_runner(board_done_env, monkeypatch):
    """(b) state 路径派生与 runner 同源 —— 不是"看起来一样"而是同一个函数。

    篡改门 (行为面): 把 runner.state_path 的产出改掉, 端点**实际写的位置**
    必须跟着变。端点里若手拼了第二套命名规则 (哪怕此刻拼出的值恰好相同),
    改了 runner 它不会跟着变 —— 本门立刻红。这比"读源码看它像不像"强,
    因为它不依赖任何措辞。
    """
    root, client, runner, _mod = board_done_env
    _mk_node_vault(root, "vault-同源", {"甲": _node_md()})
    default_path = runner.state_path(Path(root) / "vault-同源")
    moved = Path(root) / "backups" / "被改过的位置.state.json"
    monkeypatch.setattr(runner, "state_path", lambda vault=None: moved)

    resp = client.post(_BOARD_DONE_URL, data={"vault_id": "vault-同源", "board": "CS 61B"})
    assert resp.status_code == 200, resp.text
    assert moved.exists(), "端点没走 runner.state_path —— 疑似手拼了第二套路径规则"
    assert Path(resp.json()["state_path"]) == moved
    assert not default_path.exists(), "同时还往原位置写了一份 = 两套账"


def test_g67_old_state_without_board_done_reads_as_empty(board_done_env):
    """(b) 旧文件兼容读: schema_version 1 且无 board_done → 视同 {}, 不迁移不报错。"""
    root, client, runner, mod = board_done_env
    _mk_vault(root, "vault-old", _two_board_projection("vault-old", _now_local().isoformat(timespec="seconds")))
    sf = runner.state_path(root / "vault-old")
    sf.parent.mkdir(parents=True, exist_ok=True)
    legacy = '{"schema_version": 1, "board_last_recommended": {"CS 61B": "2026-08-01"}}\n'
    sf.write_text(legacy, encoding="utf-8")
    legacy_sha = hashlib.sha256(sf.read_bytes()).hexdigest()

    entry = next(v for v in client.get("/api/v1/review/overview").json()["vaults"] if v["vault_id"] == "vault-old")
    assert entry["board_done"] == []
    assert hashlib.sha256(sf.read_bytes()).hexdigest() == legacy_sha, "只读旧文件不许被顺手升级"

    assert client.post(_BOARD_DONE_URL, data={"vault_id": "vault-old", "board": "CS 61B"}).status_code == 200
    st = json.loads(sf.read_text(encoding="utf-8"))
    assert st["board_last_recommended"] == {"CS 61B": "2026-08-01"}, "既有键的值一个都不许动"
    assert st["board_done"] == {"CS 61B": mod._display_today()}
    assert st["schema_version"] == runner.STATE_SCHEMA_VERSION


def test_g67_runner_script_missing_fails_closed_503(board_done_env, monkeypatch):
    """(c) runner 不可达 → 503 fail-closed, 绝不另起一套账。"""
    root, client, _runner, mod = board_done_env
    _mk_node_vault(root, "vault-nr", {"甲": _node_md()})
    monkeypatch.setattr(mod, "_runner_script", lambda _vaults_root: None)

    resp = client.post(_BOARD_DONE_URL, data={"vault_id": "vault-nr", "board": "CS 61B"})
    assert resp.status_code == 503, resp.text
    assert resp.json()["detail"]["error"] == "runner_script_not_found"
    # 读侧同一情形只是"没有完成记录", 不是 500 (读松写紧)
    assert client.get("/api/v1/review/overview").status_code == 200


# ── CARD-G6-7 · Codex round-1 整改的配套门 ──


def _pin_tmp_name(monkeypatch, runner, state: Path) -> Path:
    """把 save_state 的临时件路径钉死, 好让用例能在那个确切位置上预置东西。

    生产里它是 `<state 名>.<pid>.<8hex>.tmp` —— **不可预测本身就是一层防御**,
    但那是「猜不中」不是「拦得住」。本门要验的是拦得住那一层 (O_EXCL|O_NOFOLLOW),
    所以先让"猜不中"失效。

    ⚠ 补丁打在 `runner._state_tmp_path`(模块级函数) 而不是 os.getpid / uuid.uuid4:
    后两个是**解释器全局**, 打上去会连累同进程里任何别的调用方 —— 初版就是这么写的,
    当场把 bug_tracker 的 BUG-id 生成弄坏, 请求 500 而不是走到被测的那条路上。
    """
    fixed = state.with_name(f"{state.name}.pinned.tmp")
    monkeypatch.setattr(runner, "_state_tmp_path", lambda _state: fixed)
    return fixed


def test_g67_state_write_refuses_preplanted_symlink_at_tmp_path(board_done_env, monkeypatch):
    """Codex round-1 HIGH: 临时件路径被预置成指向库内节点的软链 → 必须拒写。

    这条缺陷本身来自 BASE 的 `save_state`（固定名 + `write_text` 跟随软链），
    本卡一个字节都没改它 —— 但**本卡把它的可达性从「本机 runner 每小时一次」
    变成「浏览器点一下」**，所以它是本卡要负责的面。同款修法在姊妹函数
    `daily_review_pick.atomic_write` 上早就有了，本函数当时漏了。

    判据绑定到「那个节点逐字节没变」+「端点返回 503 而不是 200」——
    只断言 500 或只断言"报错了"都不够: 关键是**没写出去**。
    """
    root, client, runner, _mod = board_done_env
    vault = _mk_node_vault(root, "vault-link-tmp", {"定义甲": _node_md(fsrs_due='"2099-01-01T00:00:00Z"')})
    node = vault / "节点" / "定义甲.md"
    node_before = node.read_bytes()

    state = runner.state_path(vault)
    state.parent.mkdir(parents=True, exist_ok=True)
    tmp = _pin_tmp_name(monkeypatch, runner, state)
    tmp.symlink_to(node)
    assert tmp.is_symlink() and tmp.resolve() == node.resolve(), "夹具前提: 软链必须真的摆在那个确切路径上"

    resp = client.post(_BOARD_DONE_URL, data={"vault_id": "vault-link-tmp", "board": "CS 61B"})
    # ⛔ 承重断言排第一: 退回缺陷的变异体会让这次写"成功"(200), 那时先红的必须是
    # 「节点被写动了」而不是状态码 —— 判据要绑定到"没写出去"这件事本身
    assert node.read_bytes() == node_before, "节点被写动了 —— 软链越界没有被拦住"
    assert resp.status_code == 503, f"落账被拒必须是 503 而不是 200/500: {resp.status_code} {resp.text[:200]}"
    assert resp.json()["detail"]["error"] == "state_write_refused"
    assert not state.exists(), "被拒的这一次不许留下半份完成账"


def test_g67_stale_tmp_residue_neither_blocks_nor_gets_clobbered(board_done_env):
    """配套负控: 拒绝软链**不能顺手把正常路径也拒了**。

    方向安全声明要走完全程 —— 只验"拦住了坏的"、不验"没拦住好的", 是半条判据。
    崩在「写 tmp」与「replace」之间会留下残骸; 唯一名让下一次保存**换一个名字**,
    所以残骸既不会挡住保存, 也不该被我们顺手删掉 (那是别人的文件, 可能是另一个
    写者正在用的 in-flight tmp)。这两条一起才说明这道防御没有副作用。
    """
    root, client, runner, mod = board_done_env
    _mk_node_vault(root, "vault-stale", {"甲": _node_md()})
    state = runner.state_path(Path(root) / "vault-stale")
    state.parent.mkdir(parents=True, exist_ok=True)
    stale = state.with_name(f"{state.name}.999999.deadbeef.tmp")
    stale.write_text("上一次崩在写与 replace 之间留下的半截残骸", encoding="utf-8")
    stale_sha = hashlib.sha256(stale.read_bytes()).hexdigest()

    resp = client.post(_BOARD_DONE_URL, data={"vault_id": "vault-stale", "board": "CS 61B"})
    assert resp.status_code == 200, f"残骸不该挡住保存: {resp.text[:200]}"
    assert json.loads(state.read_text(encoding="utf-8"))["board_done"]["CS 61B"] == mod._display_today()
    assert hashlib.sha256(stale.read_bytes()).hexdigest() == stale_sha, "别人的残骸不许被顺手删改"
    # 本次自己的临时件必须已经被 os.replace 消费掉, 不留新残渣
    ours = [p.name for p in state.parent.glob(f"{state.name}.*.tmp") if p.name != stale.name]
    assert ours == [], f"成功路径留下了临时件残渣: {ours}"


def test_g67_state_write_abandons_both_legacy_fixed_tmp_names(board_done_env):
    """F1 的**第一层**（唯一名）此前零门覆盖 —— 对抗复核抓出的缺口。

    F1 是两层防御：`_state_tmp_path` 的唯一名（pid+uuid8）+ `O_EXCL|O_NOFOLLOW`。
    软链门为了验第二层，把 `_state_tmp_path` 整个 monkeypatch 掉；于是第一层的
    **实现从此没有任何用例执行过**（实测：把它退回固定名，24 条 g67 门与 291 条
    裁判用例全绿）。承重变异 harness 的 M1 也只变 `os.open` 的 flag 行，名字轴从未变异。

    这个缺口有真实代价：BASE 的固定名配的是 truncating write，残骸被无害覆盖；
    round-1 新加的 O_EXCL 把「残骸」从无害变成**硬错误**，唯一名是唯一的中和手段。
    第一层一旦被"以简化为名"退回去，任意一个落在那个可预测路径上的文件都会让
    O_EXCL 恒抛 FileExistsError → 端点恒 503、每小时落账恒失败，**且没有任何清理
    路径会解开它**（本模块明写不做陈旧 tmp 清扫，残骸门还反过来禁止删别人的文件）。

    门形照抄姊妹函数 `test_daily_review_pick.py::test_atomic_write_abandons_legacy_fixed_tmp_name`：
    在两个历史固定名上各放一个**目录** —— 目录让 O_EXCL 与 O_NOFOLLOW 都无法把它
    变成成功写，所以只要实现还在用固定名就必炸。确定性门，不靠赛跑概率。
    两个名字缺一不可：`with_suffix(".tmp")` 与 `with_name(name + ".tmp")` 是两个不同
    的串，只钉一个会放过另一个退化形态。
    """
    root, client, runner, mod = board_done_env
    _mk_node_vault(root, "vault-legacy-tmp", {"甲": _node_md()})
    state = runner.state_path(Path(root) / "vault-legacy-tmp")
    state.parent.mkdir(parents=True, exist_ok=True)
    legacy = [state.with_suffix(".tmp"), state.with_name(state.name + ".tmp")]
    assert len({p.name for p in legacy}) == 2, "前提: 两个历史固定名必须真的是两个不同的串"
    for p in legacy:
        p.mkdir()

    resp = client.post(_BOARD_DONE_URL, data={"vault_id": "vault-legacy-tmp", "board": "CS 61B"})
    assert resp.status_code == 200, f"实现还在用历史固定名 tmp: {resp.text[:300]}"
    assert json.loads(state.read_text(encoding="utf-8"))["board_done"]["CS 61B"] == mod._display_today()
    for p in legacy:
        assert p.is_dir(), f"历史固定名 {p.name} 不该被碰"
    leftovers = [q.name for q in state.parent.glob("*.tmp") if q.name not in {p.name for p in legacy}]
    assert leftovers == [], f"发布后不得残留任何 tmp: {leftovers}"


def test_g67_cold_load_of_runner_writes_no_bytecode(board_done_env, tmp_path_factory):
    """Codex round-1 LOW: **冷加载**下读路径不许写 __pycache__。

    ⚠ 本门的初版是假绿 (自己的变异跑抓出来的): 它盯的是仓库里的
    `scripts/__pycache__`, 而那两个 .pyc 早就被 runner 自己写出来过了 ——
    缓存已是最新, SourceFileLoader 本来就不会再写, 于是"没有新增"这条判据
    与修复在不在**毫无关系**。夹具必须提供一个**可证为空**的缓存面才测得到。

    现在: 把脚本复制到 tmp 里 (连同它 import 的 send_bark), 断言那儿本来没有
    __pycache__, 再从那份副本冷加载。既有夹具都已把 runner 加载过 (命中
    sys.modules), 所以还要显式把模块从表里摘掉、把字节码写入打开。
    """
    _root, _client, _runner, mod = board_done_env
    src_dir = Path(mod._runner_script(Path(_root)) or "").parent
    cold = tmp_path_factory.mktemp("g67-cold") / "scripts"
    cold.mkdir()
    for name in (mod._RUNNER_BASENAME, "send_bark.py"):
        shutil.copy(src_dir / name, cold / name)
    cache = cold / "__pycache__"
    assert not cache.exists(), "夹具前提: 冷加载面必须本来就没有字节码缓存"

    saved = {k: sys.modules.pop(k, None) for k in (mod._RUNNER_MODULE_NAME, "send_bark")}
    prev_flag = sys.dont_write_bytecode
    sys.dont_write_bytecode = False  # 把"环境恰好禁了字节码"这个假绿来源关掉
    prev_path = list(sys.path)
    try:
        fresh = mod._load_runner(cold / mod._RUNNER_BASENAME)
        assert Path(fresh.__file__).parent == cold, "前提: 必须真的从那份副本加载"
    finally:
        sys.dont_write_bytecode = prev_flag
        sys.path[:] = prev_path
        for k, v in saved.items():
            if v is not None:
                sys.modules[k] = v
            else:
                sys.modules.pop(k, None)

    written = sorted(p.name for p in cache.glob("*.pyc")) if cache.exists() else []
    assert written == [], f"读路径的模块加载写出了字节码: {written}"


def _move_frontmatter_end_before_fsrs(node: Path) -> None:
    """把结束 `---` 挪到 fsrs_due 之前 —— 字段就此降级成正文, 生产器再也读不到。"""
    text = node.read_text(encoding="utf-8")
    head, sep, tail = text.partition("fsrs_due:")
    assert sep, "夹具前提: 节点必须真的有 fsrs_due 行"
    node.write_text(head + "---\n" + sep + tail, encoding="utf-8")


def test_g67_fsrs_fingerprint_catches_boundary_and_crlf(board_done_env):
    """Codex round-1 LOW 的两条负控: 指纹此前对这两种改动失明, 现在必须都抓住。

    ① frontmatter 边界: 把结束 `---` 挪到 fsrs_due 之前 —— 逐行取 `fsrs_` 的
       老指纹看不出任何差别, 但那张卡的调度字段已经失效了;
    ② 换行风格: LF → CRLF —— `splitlines()` 吃掉 `\\r`, 老指纹同样不变,
       而"逐字节相同"这句话已经不成立。
    """
    root, _client, _runner, _mod = board_done_env
    vault = _mk_node_vault(root, "vault-fp", {"定义甲": _node_md(fsrs_due='"2099-01-01T00:00:00Z"')})
    node = vault / "节点" / "定义甲.md"
    base = _fsrs_fingerprint(vault)
    original = node.read_bytes()

    _move_frontmatter_end_before_fsrs(node)
    _assert_fingerprint_detects(base, _fsrs_fingerprint(vault), "frontmatter 边界")

    node.write_bytes(original.replace(b"\n", b"\r\n"))
    _assert_fingerprint_detects(base, _fsrs_fingerprint(vault), "CRLF 换行")

    # ③ BOM 开头的节点 (round-2 补): 生产消费面认它, 判据也必须认 ——
    # 否则这一整类真实节点在门里"没有 frontmatter", 改 fsrs_due 指纹不变。
    bom_before = _fsrs_fingerprint(vault)
    node.write_bytes(b"\xef\xbb\xbf" + original)
    assert _fsrs_fingerprint(vault)[0][node.name][1:], "前提: BOM 节点必须仍被认出 fsrs_* 行"
    node.write_bytes(b"\xef\xbb\xbf" + original.replace(b'"2099-', b'"2020-'))
    _assert_fingerprint_detects(bom_before, _fsrs_fingerprint(vault), "BOM 开头节点改 fsrs_due")

    node.write_bytes(original)
    _assert_fsrs_untouched(base, _fsrs_fingerprint(vault))  # 还原后必须回到相等 (防"恒不等"的假门)


# ══════════════════════════════════════════════════════════════════════════
# CARD-G6-7-R: 手动刷新带 board_done · 锁内三方合并 · 「取消完成」入口
# ══════════════════════════════════════════════════════════════════════════

_BOARD_UNDONE_URL = "/api/v1/review/overview/board-undone"


def _install_contaminating_undo_write_point(monkeypatch, mod, vault: Path):
    """对照实现: 照常撤销, 但**顺手**改一个节点的 fsrs_due。

    与 _install_contaminating_write_point 同纪律, 只是包的是撤销那个写点 ——
    ⛔ 不能复用那一个: 它包的是 _write_board_done, 装上之后跑撤销路径什么
    都不会发生, 于是"负控没红"会被读成"门有牙"(实测踩到过, 本门当场
    DID NOT RAISE)。变异必须打在**被验的那条路径**上。
    """
    real = mod._write_board_undone

    def contaminated(vault_dir, vaults_root, board):
        state_file, already = real(vault_dir, vaults_root, board)
        target = sorted((vault / "节点").glob("*.md"))[0]
        text = target.read_text(encoding="utf-8")
        target.write_text(text.replace("fsrs_due:", "fsrs_due: # 顺手改\nfsrs_due_shadow:"), encoding="utf-8")
        return state_file, already

    monkeypatch.setattr(mod, "_write_board_undone", contaminated)


#: 甲板两张 / 乙板一张 —— 无干扰时榜首恒是甲板 (先证明这一点再谈"让位")
_YIELD_NODES = {
    "甲一": _node_md(board="甲板"),
    "甲二": _node_md(board="甲板"),
    "乙一": _node_md(board="乙板"),
}


def _spy_subprocess_run(monkeypatch, mod) -> list:
    """记下每次子进程 argv 后照常跑真的 —— 判据要"生产器实际收到了什么"。"""
    seen: list[list[str]] = []
    real_run = mod.subprocess.run

    def _spy(argv, **kw):
        seen.append(list(argv))
        return real_run(argv, **kw)

    monkeypatch.setattr(mod.subprocess, "run", _spy)
    return seen


def _proj_of(vault: Path) -> dict:
    return json.loads((vault / "outputs" / "今日复习.json").read_text(encoding="utf-8"))


def _write_v2_state(runner, vault: Path, **keys) -> Path:
    """预置一个**已是 v2 形态**的 state (含 board_done 键), 与现网实测同形。

    ⛔ 初版这里写着「v1 文件下补出的空账会**正当地**压过磁盘 —— 那是升版语义
    不是缺陷」。那句话是错的, 而且它描述的正是 Codex round-1 H1 抓到的丢账:
    setdefault 补出来的空账把 Web 刚写成功的完成记录覆盖掉了。现在 base 记在
    归一化之后, 补出来的默认值不算"我改过"; v1 那条路由 runner 侧的
    test_g67r_upgrade_default_account_does_not_clobber_window_write 专门守着。
    这里预置 v2 只是为了让本文件的门贴近现网形态, 不是因为 v1 可以覆盖。
    """
    state_file = runner.state_path(vault)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 2, "board_last_recommended": {}, "board_done": {}}
    payload.update(keys)
    state_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return state_file


def test_g67r_refresh_passes_state_and_done_board_yields_top(board_done_env, monkeypatch):
    """(b) Web 手动刷新走 CLI 时必须带上完成账 (Codex M-1 的另一半)。

    从前 _run_pick 的 argv 里没有 --state, 于是浏览器点「重新算一遍」时
    board_done 根本流不进生产器 —— 页面把板折进已完成区了, 榜首却纹丝不动,
    用户看到的是"标了完成也没用"。

    四条判据缺一不可:
      ① 对照: 无账时榜首确实是甲板 (否则"让位"可能恒真);
      ② 让位后甲板**仍在** boards 且 stats 不变 (折叠不是剔除);
      ③ 子进程 argv 里真的带了 --state <runner 的那个文件> (不是别处的);
      ④ state 文件在 refresh 前后**字节相同** —— 生产器对它只读, 这是
         _rebuild_projection 写侧承诺②的前提。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-yield", _YIELD_NODES)

    assert client.post(_REFRESH_URL, data={"vault_id": "vault-yield"}).status_code == 200
    base_proj = _proj_of(vault)
    # ⛔ 榜首实测取, 不写死板名 (rank_boards 的排序律是本卡硬边界: 门里复刻
    # 一份排序律, 排序律一动门就红在与本卡无关的地方)
    top = base_proj["top_boards"][0]["board"]
    assert len(base_proj["top_boards"]) >= 2, "夹具前提: 至少两块板才谈得上'让给下一块'"

    state_file = _write_v2_state(runner, vault, board_done={top: mod._display_today()})
    before_bytes = state_file.read_bytes()
    seen = _spy_subprocess_run(monkeypatch, mod)

    resp = client.post(_REFRESH_URL, data={"vault_id": "vault-yield"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["state_passed"] is True

    proj = _proj_of(vault)
    assert proj["top_boards"][0]["board"] != top, "已完成的板必须让出榜首"
    assert top in [b["board"] for b in proj["boards"]], "让位不是剔除"
    assert proj["stats"] == base_proj["stats"], "让位只换顺序, 不动任何计数"

    assert seen, "没有起过子进程 —— 本门验的是 argv, 前提不成立"
    argv = seen[-1]
    assert "--state" in argv, f"子进程 argv 里没有 --state: {argv}"
    assert argv[argv.index("--state") + 1] == str(state_file), f"--state 指向了别处: {argv}"
    assert state_file.read_bytes() == before_bytes, "生产器写动了 state —— 只读承诺破了"


def test_g67r_refresh_without_runner_degrades_to_no_state_not_503(board_done_env, monkeypatch):
    """(b) 读松: runner 不可达时不传 --state, 但刷新本身照常成功。

    写侧 (完成账) 拿不到 runner 一律 503 fail-closed; 刷新是**读侧重算**,
    为一个排序细节把整个刷新打死是拿可用性换一个 tie-break, 不划算 ——
    Y2 之前它本来就不传 --state, 那条路必须留着。
    响应用加性字段 state_passed 如实说出走了哪条路, 不静默降级。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-nostate", _YIELD_NODES)
    assert client.post(_REFRESH_URL, data={"vault_id": "vault-nostate"}).status_code == 200
    top = _proj_of(vault)["top_boards"][0]["board"]
    _write_v2_state(runner, vault, board_done={top: mod._display_today()})
    monkeypatch.setattr(mod, "_runner_script", lambda vaults_root: None)
    seen = _spy_subprocess_run(monkeypatch, mod)

    resp = client.post(_REFRESH_URL, data={"vault_id": "vault-nostate"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["state_passed"] is False
    assert seen and "--state" not in seen[-1], f"runner 缺席时不该传 --state: {seen[-1:]}"
    # 拿不到账 ⇒ 让位不发生, 这是如实的降级而不是崩
    assert _proj_of(vault)["top_boards"][0]["board"] == top


def test_g67r_state_passed_is_false_when_no_subprocess_ran(board_done_env, monkeypatch):
    """(b) Codex round-2 L3: state_passed 说的是「本次有没有把账交给生产器」。

    去抖 / 已有重建在飞这两条路根本没起子进程 —— 按"runner 路径可用"去算,
    它们会报 true, 调用方就以为让位已经算过了。字段名说的是这一次做了什么,
    不是环境有没有这个能力。
    """
    import app.api.v1.endpoints.review_overview as mod

    root, client, runner, _mod = board_done_env
    vault = _mk_node_vault(root, "vault-passed", _YIELD_NODES)
    _write_v2_state(runner, vault)

    first = client.post(_REFRESH_URL, data={"vault_id": "vault-passed"})
    assert first.status_code == 200 and first.json()["rebuilt"] is True
    assert first.json()["state_passed"] is True, "真重建且 runner 可达 ⇒ 账交出去了"

    # 去抖窗口拉开 (refresh_env 把它归零了), 第二次必然 debounced
    monkeypatch.setattr(mod, "_REFRESH_TTL_SECONDS", 600.0)
    second = client.post(_REFRESH_URL, data={"vault_id": "vault-passed"})
    assert second.status_code == 200
    body = second.json()
    assert body["rebuilt"] is False and body["reason"] == "debounced"
    assert body["state_passed"] is False, "没起子进程就没把账交出去 —— 不许报 true"

    # ⛔ in_progress 也是"没起子进程"的一种 —— 两条分支各写各的 state_passed,
    # 只守 debounced 那一处的话, 把 in_progress 那处改回 true 本门照样绿
    # (Codex round-3 实测: 上一轮负控确实漏了这一半)。
    monkeypatch.setattr(mod, "_REFRESH_TTL_SECONDS", 0.0)
    key = str(Path(root).resolve() / "vault-passed")  # 端点侧的 key 是 resolve 过的
    inflight = threading.Lock()
    with mod._refresh_guard:
        mod._refresh_locks[key] = inflight
    assert inflight.acquire(blocking=False), "夹具前提: 得先真的把该库的锁占住"
    try:
        third = client.post(_REFRESH_URL, data={"vault_id": "vault-passed"})
    finally:
        inflight.release()
    body3 = third.json()
    assert body3["rebuilt"] is False and body3["reason"] == "in_progress"
    assert body3["state_passed"] is False, "在飞时本次也没起子进程 —— 不许报 true"


def test_g67r_web_write_keeps_keys_runner_wrote_in_the_window(board_done_env, monkeypatch):
    """(c) 门②  Web 向: Web 落账不许吃掉窗口内 runner 写的推送账。

    反向的那半条窄窗: Web 在 :2086 load、:2094 save, 中间 runner 的 :05 档
    把 last_push_accepted_date 落了盘 —— 整写 mine 会让那条推送账消失,
    于是同一天会再推一次 (幂等门的依据没了)。

    直写发生在**真 load_state 返回之后**, 所以 base 快照里没有那个键 ——
    合并律判定"我没改过它" ⇒ 以磁盘为准。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-merge", {"甲": _node_md()})
    state_file = _write_v2_state(runner, vault)
    real_load = runner.load_state

    def _load_then_runner_writes(v=None):
        st = real_load(v)
        cur = json.loads(state_file.read_text(encoding="utf-8"))
        cur["last_push_accepted_date"] = "2026-07-30"
        cur["last_push_kind"] = "due"
        state_file.write_text(json.dumps(cur, ensure_ascii=False), encoding="utf-8")
        return st

    monkeypatch.setattr(runner, "load_state", _load_then_runner_writes)

    resp = client.post(_BOARD_DONE_URL, data={"vault_id": "vault-merge", "board": "CS 61B"})
    assert resp.status_code == 200, resp.text

    st = json.loads(state_file.read_text(encoding="utf-8"))
    assert st["board_done"] == {"CS 61B": mod._display_today()}, "Web 自己改的键必须以 Web 为准"
    assert st["last_push_accepted_date"] == "2026-07-30", "窗口内 runner 落盘的推送账被 Web 整写覆盖了"
    assert st["last_push_kind"] == "due"


def test_g67r_board_undone_round_trips_and_never_touches_fsrs(board_done_env, monkeypatch):
    """(d) 「取消完成」: 点错了当场能回来, 且与「标记完成」同一条零 FSRS 纪律。

    从前这里写着「未做 (如实登记): 没有『取消完成』入口 —— 误点后的恢复
    途径是等明天自动回来」。一天太久了: 板在已完成区折着, 榜首已经让给别人,
    而用户只是手滑。

    写面判据与完成动作同款 (含本卡把允许集扩到三项之后的两条钉住断言) ——
    撤销是第二个写点, 它同样只许动那一个 state 文件加那把锁。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-undo", {"定义甲": _node_md(fsrs_due='"2099-01-01T00:00:00Z"')})
    (vault / "learning_events.jsonl").write_text(
        '{"event":"quiz","node":"定义甲","at":"2026-09-01T00:00:00Z"}\n', encoding="utf-8"
    )
    if os.environ.get("G67_FSRS_CONTAMINATE") == "1":
        _install_contaminating_undo_write_point(monkeypatch, mod, vault)

    assert client.post(_BOARD_DONE_URL, data={"vault_id": "vault-undo", "board": "CS 61B"}).status_code == 200
    entry = next(v for v in client.get("/api/v1/review/overview").json()["vaults"] if v["vault_id"] == "vault-undo")
    assert entry["board_done"] == ["CS 61B"], "前提: 得先真的标上, 撤销才有东西可撤"

    before_fsrs = _fsrs_fingerprint(vault)
    assert any(x.startswith("fsrs_") for x in before_fsrs[0]["定义甲.md"]), "夹具前提: 节点必须真带 fsrs_* 行"
    assert before_fsrs[1] is not None, "夹具前提: 事件账必须真的存在"
    before_tree = _tree(root)

    resp = client.post(_BOARD_UNDONE_URL, data={"vault_id": "vault-undo", "board": "CS 61B"})
    assert resp.status_code == 200, resp.text

    # ⛔ 承重断言排第一 (对照写点要让它先红, 不是被别的断言抢先)
    _assert_fsrs_untouched(before_fsrs, _fsrs_fingerprint(vault))

    body = resp.json()
    assert body["board"] == "CS 61B" and body["undone"] is True
    assert body["already_undone"] is False
    assert body["fsrs_touched"] is False
    state_file = runner.state_path(vault)
    assert Path(body["state_path"]) == state_file
    assert not state_file.is_relative_to(vault), "完成账不许落在库内"

    after = next(v for v in client.get("/api/v1/review/overview").json()["vaults"] if v["vault_id"] == "vault-undo")
    assert after["board_done"] == [], "撤销后该板必须从完成账里出来"
    assert _state_of(runner, Path(root), "vault-undo")["board_done"] == {}, "键要真的被摘掉, 不是留个空值"

    lock_file = runner.state_lock_path(vault)
    after_tree = _tree(root)
    changed = {k for k in set(before_tree) | set(after_tree) if before_tree.get(k) != after_tree.get(k)}
    assert changed <= {"backups", f"backups/{state_file.name}", f"backups/{lock_file.name}"}, (
        f"撤销的写面必须在 backups 目录 + state + 锁三项之内, 实为 {sorted(changed)}"
    )
    assert lock_file.stat().st_size == 0, "锁文件只做锁, 不许承载任何数据"
    assert not lock_file.is_relative_to(vault), "锁不许落在库内"


def test_g67r_board_undone_is_idempotent_200_not_404(board_done_env):
    """(d) 幂等: 板本来就不在账里 → 200 already_undone, 不是 404。

    404 会让零 JS 表单路径给出一页「取消完成失败」—— 而用户想要的结果
    (这块板现在没被标完成) 明明已经成立了。把"已经是目标状态"报成失败,
    是用状态码描述过程而不是结果。

    ⚠ 代价如实登记 (Codex 该问的那条): 幂等 200 会把"板名根本拼错了"也
    答成成功。所以 JSON 里 already_undone 如实分开 —— 调用方要区分得出
    "我撤掉了一条"和"本来就没有"。
    """
    root, client, runner, _mod = board_done_env
    vault = _mk_node_vault(root, "vault-idem", {"甲": _node_md()})
    assert client.post(_BOARD_DONE_URL, data={"vault_id": "vault-idem", "board": "CS 61B"}).status_code == 200

    first = client.post(_BOARD_UNDONE_URL, data={"vault_id": "vault-idem", "board": "CS 61B"})
    assert first.status_code == 200 and first.json()["already_undone"] is False

    state_file = runner.state_path(vault)
    settled = state_file.read_bytes()
    second = client.post(_BOARD_UNDONE_URL, data={"vault_id": "vault-idem", "board": "CS 61B"})
    assert second.status_code == 200, second.text
    assert second.json()["already_undone"] is True, "重复撤销必须如实说'本来就没有'"
    assert second.json()["undone"] is True
    assert state_file.read_bytes() == settled, "无事可做的撤销不该改写 state"

    never = client.post(_BOARD_UNDONE_URL, data={"vault_id": "vault-idem", "board": "从来没标过的板"})
    assert never.status_code == 200 and never.json()["already_undone"] is True
    assert state_file.read_bytes() == settled


def test_g67r_board_undone_reuses_the_same_three_write_gates(board_done_env, tmp_path_factory):
    """(d) 三道写侧门是**复用**不是复制: 同源 403 / 未知库 404 / 库外软链 503 / 板名 422。

    行为面判据 —— 每一条都验"完成账没被动过"。复用的证据在 grep 门那边
    (两个 _assert_* 各仍只定义一次), 这里验的是它们真的挡在撤销这条路上。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-ugate", {"甲": _node_md()})
    assert client.post(_BOARD_DONE_URL, data={"vault_id": "vault-ugate", "board": "CS 61B"}).status_code == 200
    state_file = runner.state_path(vault)
    settled = state_file.read_bytes()

    cross = client.post(
        _BOARD_UNDONE_URL,
        data={"vault_id": "vault-ugate", "board": "CS 61B"},
        headers={"origin": "http://evil.example", "sec-fetch-site": "cross-site"},
    )
    assert cross.status_code == 403 and cross.json()["detail"]["error"] == "cross_site_blocked"
    assert state_file.read_bytes() == settled, "被同源门拒的请求不许动账"

    assert client.post(_BOARD_UNDONE_URL, data={"vault_id": "不存在的库", "board": "b"}).status_code == 404

    outside = tmp_path_factory.mktemp("g67r-outside")
    (outside / ".obsidian").mkdir()
    (root / "vault-ulink").symlink_to(outside, target_is_directory=True)
    link = client.post(_BOARD_UNDONE_URL, data={"vault_id": "vault-ulink", "board": "CS 61B"})
    assert link.status_code == 503 and link.json()["detail"]["error"] == "vault_outside_root"
    assert not runner.state_path(root / "vault-ulink").exists()

    for board in ("", "板" * (mod._BOARD_NAME_MAX + 1)):
        bad = client.post(_BOARD_UNDONE_URL, data={"vault_id": "vault-ugate", "board": board})
        assert bad.status_code == 422, (board[:10], bad.text)
    assert state_file.read_bytes() == settled


def test_g67r_lock_acquisition_failure_is_503_not_500(board_done_env, monkeypatch):
    """(d) Codex round-1 M1: 取锁阶段的 OSError 也要翻成 503, 不能逃逸成 500。

    取锁的 mkdir / open 发生在 save_state **之前**。初版把 state_locked 放在
    try 之外, 于是 backups 被普通文件占位、锁不可写、锁路径是软链被 O_NOFOLLOW
    拒 —— 这几种都从 503 state_write_refused 退化成 500 裸 traceback,
    零 JS 表单路径连动作专属错误页都拿不到。BASE 上这些情形返回的是 503。
    """
    root, client, runner, _mod = board_done_env
    _mk_node_vault(root, "vault-lockfail", {"甲": _node_md()})
    # backups 被一个**普通文件**占位 ⇒ mkdir(parents=True) 抛 FileExistsError
    blocked = Path(root) / "backups-占位"
    blocked.write_text("我不是目录", encoding="utf-8")
    monkeypatch.setattr(runner, "BACKUPS", blocked / "sub")

    for url, label in ((_BOARD_DONE_URL, "标记完成"), (_BOARD_UNDONE_URL, "取消完成")):
        resp = client.post(url, data={"vault_id": "vault-lockfail", "board": "CS 61B"})
        assert resp.status_code == 503, f"{label}: 取锁失败必须 503 而不是 500, 实为 {resp.status_code}"
        assert resp.json()["detail"]["error"] == "state_write_refused"
        form = client.post(
            url, data={"vault_id": "vault-lockfail", "board": "CS 61B", "redirect": "page"}, follow_redirects=False
        )
        assert form.status_code == 503
        assert f"{label}失败" in form.text, f"错误页说的必须是{label}这个动作"


def test_g67r_board_undone_zero_js_form_path(board_done_env):
    """(d) 零 JS 表单路径: 成功 303 回本页; 失败渲染的错误页说的是**这个**动作。

    用户刚点「撤销」, 页面写着「标记完成失败」会把他引到完全错的方向。
    """
    root, client, _runner, _mod = board_done_env
    _mk_node_vault(root, "vault-uform", {"甲": _node_md()})
    assert client.post(_BOARD_DONE_URL, data={"vault_id": "vault-uform", "board": "CS 61B"}).status_code == 200

    ok = client.post(
        _BOARD_UNDONE_URL,
        data={"vault_id": "vault-uform", "board": "CS 61B", "redirect": "page"},
        follow_redirects=False,
    )
    assert ok.status_code == 303 and ok.headers["location"] == _PAGE_URL

    bad = client.post(
        _BOARD_UNDONE_URL,
        data={"vault_id": "不存在的库", "board": "CS 61B", "redirect": "page"},
        follow_redirects=False,
    )
    assert bad.status_code == 404, "失败不许伪装成 303 成功"
    assert "取消完成失败" in bad.text
    assert "标记完成失败" not in bad.text and "刷新失败" not in bad.text
    assert "vault_not_found" in bad.text


def test_g67r_undone_fsrs_gate_reddens_under_contaminating_write_point(board_done_env, monkeypatch):
    """(d) 常驻负控: 换上「顺手写 fsrs_due」的写点, 撤销那道门必须红。

    判据绑到**具体那一条**断言 (_FSRS_GATE_MSG) —— 变异体若因别的原因先红,
    本门同样不放行 (沿 test_g67_fsrs_gate_reddens_under_contaminating_write_point)。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-uneg", {"定义甲": _node_md(fsrs_due='"2099-01-01T00:00:00Z"')})
    assert client.post(_BOARD_DONE_URL, data={"vault_id": "vault-uneg", "board": "CS 61B"}).status_code == 200

    _install_contaminating_undo_write_point(monkeypatch, mod, vault)
    before = _fsrs_fingerprint(vault)
    resp = client.post(_BOARD_UNDONE_URL, data={"vault_id": "vault-uneg", "board": "CS 61B"})
    assert resp.status_code == 200, "对照写点只污染 FSRS, 不许把请求本身弄坏 (否则红的是别的东西)"
    assert _state_of(runner, Path(root), "vault-uneg")["board_done"] == {}, (
        "对照写点必须仍然把撤销做对 —— 拆的只是那一条守卫"
    )
    with pytest.raises(AssertionError) as ei:
        _assert_fsrs_untouched(before, _fsrs_fingerprint(vault))
    assert _FSRS_GATE_MSG in str(ei.value), f"红的不是 FSRS 那条断言: {ei.value}"


def test_g67r_page_offers_undo_only_in_the_done_section(board_done_env):
    """(d) 零 JS 页: 撤销钮只出现在已完成区; 未完成板不带撤销钮。

    ⚠ 本门替代了原先「已完成板不该再带完成钮」那条按 name="board" **计数**
    的判据 —— 加了撤销表单之后, 计数不再表达那个意图 (两个动作的 hidden
    input 同名)。换成按 action 归属判定: 更强, 且两个动作各自可被违反。
    """
    root, client, _runner, _mod = board_done_env
    vault = _mk_vault(
        root, "vault-undopage", _two_board_projection("vault-undopage", _now_local().isoformat(timespec="seconds"))
    )
    (vault / "节点").mkdir(exist_ok=True)

    page = client.get(_PAGE_URL).text
    assert _BOARD_UNDONE_URL not in page, "还没有完成记录就不该有撤销钮"

    assert client.post(_BOARD_DONE_URL, data={"vault_id": "vault-undopage", "board": "CS 61B"}).status_code == 200
    page2 = client.get(_PAGE_URL).text
    i = page2.index("已完成（1）")
    head, fold = page2[:i], page2[i:]

    assert head.count(f'action="{_BOARD_DONE_URL}"') == 1, "未完成板 (数学) 仍带完成钮"
    assert head.count(f'action="{_BOARD_UNDONE_URL}"') == 0, "未完成板不该带撤销钮"
    assert fold.count(f'action="{_BOARD_UNDONE_URL}"') == 1, "已完成板必须带撤销钮"
    assert fold.count(f'action="{_BOARD_DONE_URL}"') == 0, "已完成板不该再带完成钮"
    assert "点错了可以撤销" in page2, "钮旁边要说清误点有救"

    # 点一次撤销 → 折叠区消失, 板回到主表格 (端到端, 不只是渲染)
    assert (
        client.post(
            _BOARD_UNDONE_URL,
            data={"vault_id": "vault-undopage", "board": "CS 61B", "redirect": "page"},
            follow_redirects=False,
        ).status_code
        == 303
    )
    page3 = client.get(_PAGE_URL).text
    assert "已完成（" not in page3
    assert page3.count(f'action="{_BOARD_DONE_URL}"') == 2, "两块板都回到待做区, 各带一个完成钮"


# ══ CARD-G6-6 (BATCH-2026-09-07-第十三批): 板级 snooze 两档「今晚 / 明天」══

_BOARD_SNOOZE_URL = "/api/v1/review/overview/board-snooze"


def test_g66_board_snooze_writes_only_state_and_never_touches_fsrs(board_done_env):
    """(g)①⑤ 推迟的写面恰是 backups + state + 锁, FSRS 调度面一个字节不动。

    写面允许集与 board-done 那条是**同一个集合** —— snooze 走的是同一条
    load→改→save (同一把锁、同一个 state 文件), 写面不该多出任何东西。
    多出来的任何一项都是本卡引入的写面泄漏。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-snooze", {"定义甲": _node_md(fsrs_due='"2099-01-01T00:00:00Z"')})
    (vault / "learning_events.jsonl").write_text(
        '{"event":"quiz","node":"定义甲","at":"2026-09-01T00:00:00Z"}\n', encoding="utf-8"
    )

    before_fsrs = _fsrs_fingerprint(vault)
    assert any(x.startswith("fsrs_") for x in before_fsrs[0]["定义甲.md"]), (
        "夹具前提: 节点必须真的带 fsrs_* frontmatter 行, 否则门是空的"
    )
    assert before_fsrs[1] is not None, "夹具前提: 事件账必须真的存在, 否则那一半判据是空的"
    before_tree = _tree(root)

    resp = client.post(_BOARD_SNOOZE_URL, data={"vault_id": "vault-snooze", "board": "CS 61B", "until": "tomorrow"})
    assert resp.status_code == 200, resp.text

    # ⛔ 承重断言排第一: 对照写点让它先红, 而不是被别的断言抢先 (假杀)
    _assert_fsrs_untouched(before_fsrs, _fsrs_fingerprint(vault))

    body = resp.json()
    assert body["board"] == "CS 61B" and body["fsrs_touched"] is False
    state_file = runner.state_path(vault)
    assert Path(body["state_path"]) == state_file
    assert not state_file.is_relative_to(vault), "推迟账不许落在库内 (BACKUPS 在仓库下)"

    st = _state_of(runner, Path(root), "vault-snooze")
    assert set(st["snoozed"]) == {"CS 61B"}, f"推迟账必须落进 snoozed, 实为 {st.get('snoozed')!r}"
    assert st["snoozed"]["CS 61B"] == body["snoozed_until"]

    after_tree = _tree(root)
    lock_file = runner.state_lock_path(vault)
    changed = {k for k in set(before_tree) | set(after_tree) if before_tree.get(k) != after_tree.get(k)}
    assert changed == {"backups", f"backups/{state_file.name}", f"backups/{lock_file.name}"}, (
        f"写面必须恰是 backups 目录 + 那一个 state 文件 + 那一把锁, 实为 {sorted(changed)}"
    )


_BOARD_UNSNOOZE_URL = "/api/v1/review/overview/board-unsnooze"


def _pin_now(monkeypatch, mod, when: str, tz_name: str = "Asia/Shanghai"):
    """把端点侧的「此刻」钉在一个具体钟点上 (显示时区本地)。

    ⛔ 打的是 mod._display_now 这个**模块级入口**, 不是 datetime.now —— 后者
    是解释器全局, 打上去会连累同进程里任何别的调用方 (本仓实测: 会把
    bug_tracker 的 id 生成一起弄坏)。这也是本卡把那次读数收成单一入口的理由。
    """
    monkeypatch.setenv("CANVAS_TZ", tz_name)
    pinned = datetime.fromisoformat(when).replace(tzinfo=ZoneInfo(tz_name))
    monkeypatch.setattr(mod, "_display_now", lambda: pinned)
    return pinned


def _pin_child_now(monkeypatch, mod, pinned) -> list:
    """把**生产器子进程**的「此刻」也钉到 pinned 上 (走它既有的只读旗标 --now)。

    ⛔ 只钉端点 (_pin_now) 不够: refresh 是 subprocess 起 daily_review_pick.py,
    子进程用 datetime.now(timezone.utc) 自己读钟。端点被钉在一个**绝对**钟点上
    时, 它写出的 until 是一个会随真实时间流逝而过期的时刻 —— 墙钟一旦越过它,
    子进程就判它不活跃, 让位不发生。于是门的真值随墙钟翻转: 钉在
    2026-09-09T10:00 的端到端门写出 until=2026-09-09T20:00+08:00, 到 2026-09-11
    自己红成 `assert 'CS 61B' != 'CS 61B'`, 而**代码一个字没改**。

    ⚠ 「刚过期的 snooze」这个状态在生产里**是可达的**, 而且那时**不让位才是对的**
    (Codex round-6 LOW-1 更正了本注释的初版, 那版说它"生产不可达", 错了: 端点在
    19:59:59.999 算出 until=20:00:00 过了 `until > now_local` 的检查, 写盘落在
    20:00:00.001 就已过期; 何况推迟与刷新本来就是**两个独立请求**, 之间没有任何
    时间上界)。所以这条门要验的不是"过期还让位", 而是"**活跃**的 snooze 让位" ——
    那就必须保证判定发生时 until 确实还活着。两侧钉到同一刻做到了这一点。

    钉住两侧之后判据与真实墙钟无关 —— 同一条性质在相距 79 年的三个 pinned
    值上同绿, 见 test_g66_e2e_snooze_verdict_is_clock_independent。

    ⚠ 这是**测试侧**的修法, 刻意不给生产加旗标。理由 (round-6 已按 Codex 的核对
    收窄, 初版两条都说过了头):
      · payload 的 generated_at 会从**子进程扫描前**的采样变成**父进程请求时**的
        采样。差的是一次 spawn, 不是"生成完成时刻"——初版那么写是夸大;
      · 真正决定性的一条: 接 --now **也统一不了什么**。写推迟账那次请求、刷新那次
        请求、之后 GET 那次渲染, 本来就是三次独立的读钟; 只在 _run_pick 里补一次
        父侧采样只合上其中一道缝。
      · ⛔ 初版还写过「与 launchd runner 那条不传 --now 的调用路分叉」——**事实错误**:
        runner 根本不起 picker 子进程, 它 `import daily_review_pick as picker` 后
        在进程内直调 `picker.build_payload(VAULT, now, ...)`(daily_review_run.py
        :604/:613), 已经在传自己的参照时刻。拿它当"另一条不传旗标的路"是我没读代码
        就写下的类比。
    (父子各读一次钟、当地午夜前后可能分到不同日期这件事是 G6-7/G6-7-R 面的既有
    形态, 非本卡引入, 登记为移交项。)

    脚本名锚在生产常量 mod._PICK_REL 上, 不手抄字面量: 生产改名时本 helper
    跟着失效, 比"改完还静默放行"强。返回 seen, 与 _spy_subprocess_run 同形。
    """
    seen: list[list[str]] = []
    real_run = mod.subprocess.run
    pinned_iso = pinned.isoformat()
    basename = mod._PICK_REL[-1]

    def _run(argv, **kw):
        argv = list(argv)
        if any(str(a).endswith(basename) for a in argv):
            argv += ["--now", pinned_iso]
        seen.append(argv)
        return real_run(argv, **kw)

    monkeypatch.setattr(mod.subprocess, "run", _run)
    return seen


def _assert_child_now_pinned(seen, pinned, *, expected_runs: int) -> None:
    """钉子有没有真的落到**每一次**子进程调用上 —— 要断言, 不能靠相信。

    少了这条, `_pin_child_now` 哪天匹配不上脚本名 (改名 / 换调用形态) 就会
    静默退回单侧钉钟, 而门照样绿到下一次墙钟越线为止。

    ⛔ expected_runs 与「逐条检查」都是 Codex round-6 第 2 点补上的:
    初版只看 `seen[-1]`, 那只证明**最后一次被记下的调用**钉住了。若将来只有第二次
    refresh 绕过这层包装 (直接 Popen / call / 提前绑定的 run 别名 —— stdlib 里
    check_output 走 run 会被包到, 这几个不会), `seen[-1]` 仍是第一次那条合法记录,
    断言照样绿。钉住条数 + 逐条检查之后, 少一次或漏一次都会红。
    """
    assert len(seen) == expected_runs, f"起子进程的次数不是 {expected_runs} 次 (实为 {len(seen)}): {seen}"
    for i, argv in enumerate(seen):
        assert "--now" in argv, f"第 {i + 1} 次子进程 argv 里没有 --now (钉子没落上): {argv}"
        assert argv[argv.index("--now") + 1] == pinned.isoformat(), f"第 {i + 1} 次 --now 钉的不是那一刻: {argv}"


def test_g66_snooze_tonight_lands_on_todays_20_00_display_tz(board_done_env, monkeypatch):
    """(e)(g)① 「今晚」= **当日 20:00 显示时区**, offset 取那一天的实际值。"""
    root, client, runner, mod = board_done_env
    _mk_node_vault(root, "vault-t", {"定义甲": _node_md()})
    pinned = _pin_now(monkeypatch, mod, "2026-09-09T10:00:00")

    resp = client.post(_BOARD_SNOOZE_URL, data={"vault_id": "vault-t", "board": "CS 61B", "until": "tonight"})
    assert resp.status_code == 200, resp.text
    until = datetime.fromisoformat(resp.json()["snoozed_until"])
    assert (until.year, until.month, until.day) == (2026, 9, 9), "「今晚」必须落在当日"
    assert (until.hour, until.minute, until.second) == (20, 0, 0)
    assert until.utcoffset() == pinned.utcoffset(), "offset 必须是显示时区当日的实际值"
    st = _state_of(runner, Path(root), "vault-t")
    assert st["snoozed"]["CS 61B"] == resp.json()["snoozed_until"], "落盘值与响应值必须是同一个串"


def test_g66_snooze_tomorrow_lands_on_next_midnight_display_tz(board_done_env, monkeypatch):
    """(e)(g)③ 「明天」= 次日 00:00 显示时区。"""
    root, client, runner, mod = board_done_env
    _mk_node_vault(root, "vault-m", {"定义甲": _node_md()})
    _pin_now(monkeypatch, mod, "2026-09-09T22:30:00")

    resp = client.post(_BOARD_SNOOZE_URL, data={"vault_id": "vault-m", "board": "CS 61B", "until": "tomorrow"})
    assert resp.status_code == 200, resp.text
    until = datetime.fromisoformat(resp.json()["snoozed_until"])
    assert (until.year, until.month, until.day) == (2026, 9, 10), "「明天」必须落在次日"
    assert (until.hour, until.minute, until.second) == (0, 0, 0), "必须是次日零点整"


def test_g66_tomorrow_survives_dst_transitions(board_done_env, monkeypatch):
    """(g)③ DST 切换日「明天」仍是次日 **00:00**, 不是 01:00 / 23:00。

    ⛔ 这条是 `datetime.combine(date + 1天, 00:00, tz)` 与
    `now + timedelta(hours=24)` 的分水岭: 切换日那一天不是 24 小时, 加满
    24 小时会落到 23:00 或次日 01:00 —— 而用户看到的文案还写着"明天零点"。
    两个方向各一条 (spring forward / fall back)。

    两类 case, 各自守不同的性质:
      · **America/New_York 两组** 守 `hour == 0` —— 它抓得住裸
        `now + timedelta(hours=24)`(实测这三个日期上都给 hour=10)。
        ⚠ 但这两组的 **offset 断言无区分力**: 美国 DST 在**凌晨 02:00** 切换,
        于是「今天白天的 offset」与「次日 00:00 的 offset」恒相同 —— 连"把今天的
        固定偏移硬搬到明天"(`tzinfo=timezone(now.utcoffset())`) 也给出逐字节相同
        的结果。
      · **America/Nuuk 两组** 才是 offset 那条的承重面 (Codex round-2 LOW-2)。
        格陵兰的切换发生在**当地午夜**(2026 春季 = `2026-03-29 01:00Z` → 当地
        `00:00 -01:00`; 秋季 = `2026-10-25 01:00Z`), 于是「今天白天」与「次日
        00:00」分处切换两侧 —— 3/28 10:00 是 -02:00 而次日零点是 **-01:00**,
        10/24 反向。硬搬今天偏移的实现会**晚/早一小时唤醒**, 本组当场红。
        ⚠ Codex round-3 LOW-2 更正: 本卡初版注释写「切换在 UTC 22:00」是**错的**
        —— 22:00Z 时当地才 20:00 -02:00, 尚未切换。照那个数复建 UTC 边界夹具
        会提前三小时、测到还没切换的偏移。期望值与夹具前提断言本身没错, 错的是
        注释里那个 UTC 时刻。
    ⛔ 本卡初版 docstring 断言过「IANA 现行库里没有这样的时区」——**那是错的**,
    Codex round-2 给出了 Nuuk 这个反例, 实测成立。教训: "找不到"不等于"不存在",
    没穷举就不该把它写成事实。
    """
    root, client, runner, mod = board_done_env
    _mk_node_vault(root, "vault-dst", {"定义甲": _node_md()})
    cases = [
        # (时区, 钉住的此刻, 期望的次日, 次日零点那一刻的 UTC 偏移小时数)
        # ── 守 hour == 0 (offset 在这两组上恒真, 见 docstring) ──
        ("America/New_York", "2026-03-08T10:00:00", (2026, 3, 9), -4),  # spring forward 当天
        ("America/New_York", "2026-11-01T10:00:00", (2026, 11, 2), -5),  # fall back 当天
        # ── 守 offset 取**次日**那天的值 (切换在当地午夜, 今天与次日零点不同组) ──
        ("America/Nuuk", "2026-03-28T10:00:00", (2026, 3, 29), -1),  # 切换 2026-03-29T01:00Z
        ("America/Nuuk", "2026-10-24T10:00:00", (2026, 10, 25), -2),  # 切换 2026-10-25T01:00Z
    ]
    for tz_name, when, expect_date, expect_offset_h in cases:
        pinned = _pin_now(monkeypatch, mod, when, tz_name=tz_name)
        resp = client.post(_BOARD_SNOOZE_URL, data={"vault_id": "vault-dst", "board": "CS 61B", "until": "tomorrow"})
        assert resp.status_code == 200, resp.text
        until = datetime.fromisoformat(resp.json()["snoozed_until"])
        assert (until.year, until.month, until.day) == expect_date, f"{when}: 明天不是次日"
        assert (until.hour, until.minute) == (0, 0), (
            f"{when}: DST 切换日的「明天」落到了 {until.hour}:{until.minute:02d} 而不是零点"
        )
        assert until.utcoffset() == timedelta(hours=expect_offset_h), (
            f"{tz_name} {when}: offset 用的不是**次日**那天的值 (把今天的偏移硬搬过去了)"
        )
        if tz_name == "America/Nuuk":
            # 夹具前提: 这一组的今天与次日零点**确实不同组**, 否则本组也是空的
            assert pinned.utcoffset() != until.utcoffset(), (
                f"{tz_name} {when}: 夹具前提不成立 —— 今天与次日零点同 offset, 这组守不住任何东西"
            )


def test_g66_tonight_after_2000_is_422_and_writes_nothing(board_done_env, monkeypatch):
    """(e)(g)④ 20:00 之后点「今晚」→ 422 snooze_until_in_past, state 字节不变。

    ⛔ **不静默夹到下一档**: 用户点的是「今晚」, 悄悄改成「明天」等于替他做了
    一个他没做的决定, 而他看到的反馈还写着"今晚"。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-late", {"定义甲": _node_md()})
    _pin_now(monkeypatch, mod, "2026-09-09T20:05:00")
    state_file = runner.state_path(vault)

    before = state_file.read_bytes() if state_file.exists() else None
    resp = client.post(_BOARD_SNOOZE_URL, data={"vault_id": "vault-late", "board": "CS 61B", "until": "tonight"})
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"]["error"] == "snooze_until_in_past"
    after = state_file.read_bytes() if state_file.exists() else None
    assert after == before, "被拒的请求不许写出任何内容"

    # 同一时刻「明天」仍然合法 —— 拒的是那一档, 不是整个动作
    ok = client.post(_BOARD_SNOOZE_URL, data={"vault_id": "vault-late", "board": "CS 61B", "until": "tomorrow"})
    assert ok.status_code == 200, ok.text


def test_g66_until_outside_the_two_choices_is_422(board_done_env, monkeypatch):
    """(e)(i) 两档枚举之外一律 422 —— 禁自定义天数 / 自由时间 (D-8 甲)。"""
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-enum", {"定义甲": _node_md()})
    _pin_now(monkeypatch, mod, "2026-09-09T10:00:00")
    state_file = runner.state_path(vault)

    # 自定义天数 / 自由时间 / 大小写与空白变体 —— 全部走本端点自己的枚举门
    for bad in ("nextweek", "3d", "2026-09-20T00:00:00+08:00", "TONIGHT", "tonight ", "0"):
        before = state_file.read_bytes() if state_file.exists() else None
        resp = client.post(_BOARD_SNOOZE_URL, data={"vault_id": "vault-enum", "board": "CS 61B", "until": bad})
        assert resp.status_code == 422, f"until={bad!r} 应被拒: {resp.text}"
        assert resp.json()["detail"]["error"] == "snooze_until_invalid", bad
        after = state_file.read_bytes() if state_file.exists() else None
        assert after == before, f"until={bad!r} 被拒后不许写出任何内容"

    # 空串 / 缺字段在 **表单层**就被拒 (Form(...) 是必填) —— 请求根本到不了
    # 端点体内。如实分开写: 拿它去断言 snooze_until_invalid 是在给框架的
    # 校验记本端点的功。两条都是 422 且零写入, 这才是本门要的性质。
    for missing in (
        {"vault_id": "vault-enum", "board": "CS 61B", "until": ""},
        {"vault_id": "vault-enum", "board": "CS 61B"},
    ):
        before = state_file.read_bytes() if state_file.exists() else None
        resp = client.post(_BOARD_SNOOZE_URL, data=missing)
        assert resp.status_code == 422, f"{missing!r} 应被拒: {resp.text}"
        after = state_file.read_bytes() if state_file.exists() else None
        assert after == before, f"{missing!r} 被拒后不许写出任何内容"


def test_g66_snooze_reuses_all_three_write_gates_and_writes_nothing_on_refusal(board_done_env, tmp_path_factory):
    """(g)⑥ 三道写侧门是**复用**不是复制, 且被拒时零写入 (沿 board-done 同名门)。

    行为面而非文本面 —— 跨站表单 403 / 未知 vault 404 / 库外软链 503 /
    空板名与超长板名 422, 每条都验"state 文件没被创建"。
    """
    root, client, runner, mod = board_done_env
    _mk_node_vault(root, "vault-sgate", {"甲": _node_md()})
    state_file = runner.state_path(Path(root) / "vault-sgate")
    ok = {"vault_id": "vault-sgate", "board": "CS 61B", "until": "tomorrow"}

    cross = client.post(
        _BOARD_SNOOZE_URL, data=ok, headers={"origin": "http://evil.example", "sec-fetch-site": "cross-site"}
    )
    assert cross.status_code == 403, cross.text
    assert cross.json()["detail"]["error"] == "cross_site_blocked"
    assert not state_file.exists(), "被同源门拒的请求不许留下任何推迟账"

    assert client.post(_BOARD_SNOOZE_URL, data={**ok, "vault_id": "不存在的库"}).status_code == 404
    assert not state_file.exists()

    # 超长板名走本端点自己的 _assert_board_name (与另外两个写端点同一个函数)
    long_board = "板" * (mod._BOARD_NAME_MAX + 1)
    resp = client.post(_BOARD_SNOOZE_URL, data={**ok, "board": long_board})
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"]["error"] == "board_invalid"
    assert not state_file.exists()
    # 空板名在**表单层**就被拒 (Form(...) 必填, 空串等同缺席) —— 到不了端点体内。
    # 那一半判据只能在函数级验: 门守的是"空名不许过", 不是"HTTP 层回哪种 422"。
    empty = client.post(_BOARD_SNOOZE_URL, data={**ok, "board": ""})
    assert empty.status_code == 422 and not state_file.exists()
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as ei:
        mod._assert_board_name("")
    assert ei.value.status_code == 422 and ei.value.detail["error"] == "board_invalid"

    outside = tmp_path_factory.mktemp("g66-outside")
    (outside / ".obsidian").mkdir()
    (root / "vault-slink").symlink_to(outside, target_is_directory=True)
    link = client.post(_BOARD_SNOOZE_URL, data={**ok, "vault_id": "vault-slink"})
    assert link.status_code == 503, link.text
    assert link.json()["detail"]["error"] == "vault_outside_root"
    assert not runner.state_path(root / "vault-slink").exists()


def test_g66_zero_js_form_path_redirects_and_failure_keeps_status(board_done_env):
    """(g)⑦ 零 JS 表单路径: redirect=page → 303 回本页; 失败渲染**本动作**的错误页。

    用户刚点「明天再说」, 页面写着「刷新失败」比没有错误页更糟。
    """
    root, client, runner, _mod = board_done_env
    _mk_node_vault(root, "vault-sform", {"甲": _node_md()})

    ok = client.post(
        _BOARD_SNOOZE_URL,
        data={"vault_id": "vault-sform", "board": "CS 61B", "until": "tomorrow", "redirect": "page"},
        follow_redirects=False,
    )
    assert ok.status_code == 303
    assert ok.headers["location"] == _PAGE_URL
    assert runner.state_path(Path(root) / "vault-sform").exists()

    bad = client.post(
        _BOARD_SNOOZE_URL,
        data={"vault_id": "不存在的库", "board": "CS 61B", "until": "tomorrow", "redirect": "page"},
        follow_redirects=False,
    )
    assert bad.status_code == 404, "失败不许伪装成 303 成功"
    assert "推迟失败" in bad.text and "刷新失败" not in bad.text and "标记完成失败" not in bad.text
    assert "vault_not_found" in bad.text


def test_g66_get_projects_only_active_snoozes(board_done_env, monkeypatch):
    """(f)(g)② GET 只投影**仍在生效**的推迟 —— 到期的条目对页面已经不存在。

    「到期回队」在读侧的全部依据。⛔ 同时验**不删过期键**: state 里那条记录
    还在 (加性纪律), 只是不再活跃 —— 两件事一起才说明得了"靠现算而不是靠
    清理器"。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-exp", {"甲": _node_md()})
    _pin_now(monkeypatch, mod, "2026-09-09T10:00:00")

    assert (
        client.post(
            _BOARD_SNOOZE_URL, data={"vault_id": "vault-exp", "board": "CS 61B", "until": "tonight"}
        ).status_code
        == 200
    )
    entry = next(v for v in client.get("/api/v1/review/overview").json()["vaults"] if v["vault_id"] == "vault-exp")
    assert set(entry["snoozed"]) == {"CS 61B"}, "活跃推迟必须投影出来"

    # 时钟拨过 20:00 —— 没有任何人去改 state
    _pin_now(monkeypatch, mod, "2026-09-09T20:01:00")
    entry2 = next(v for v in client.get("/api/v1/review/overview").json()["vaults"] if v["vault_id"] == "vault-exp")
    assert entry2["snoozed"] == {}, "过了 until 就不该再投影出来"
    st = _state_of(runner, Path(root), "vault-exp")
    assert "CS 61B" in st["snoozed"], "过期键**不删** —— 活跃是现算的, 不靠清理器"


def test_g66_tonight_available_is_decided_server_side_once(board_done_env, monkeypatch):
    """(e)(g)⑧ 20:00 的判定只在服务端做一次, 以布尔下发; 页面照结论渲染。

    三件事一起钉:
      ① GET 顶层带 tonight_available, 与服务端那一次 now 读数一致;
      ② 未到 20:00: 零 JS 页有「今晚再说」钮;
      ③ 过了 20:00: 页面**不再渲染**那个钮 (留着它只会让人点出一个必然 422
         的请求), 但「明天再说」仍在 —— 关掉的是那一档不是整个动作。
    """
    root, client, runner, mod = board_done_env
    _mk_vault(root, "vault-tz", _two_board_projection("vault-tz", _now_local().isoformat(timespec="seconds")))

    _pin_now(monkeypatch, mod, "2026-09-09T10:00:00")
    data = client.get("/api/v1/review/overview").json()
    assert data["tonight_available"] is True
    page = client.get(_PAGE_URL).text
    assert page.count('value="tonight"') == 2, "未到 20:00, 两块板各一个「今晚」钮"
    assert page.count('value="tomorrow"') == 2

    _pin_now(monkeypatch, mod, "2026-09-09T20:00:00")
    data2 = client.get("/api/v1/review/overview").json()
    assert data2["tonight_available"] is False, "20:00 整点起就不该再给「今晚」"
    page2 = client.get(_PAGE_URL).text
    assert page2.count('value="tonight"') == 0, "过了 20:00 页面不许再渲染「今晚」钮"
    assert page2.count('value="tomorrow"') == 2, "关掉的是那一档, 不是整个动作"


def test_g66_page_folds_snoozed_board_without_dropping_it(board_done_env, monkeypatch):
    """(f)(g)⑧ 零 JS 页: 推迟的板折进「已推迟」区 —— **折叠不是删除**。

    ⛔ 同时钉住 `<details>` 的**条件渲染**: 没有活跃推迟时页面上的折叠区个数
    与推迟之前**完全相同** (无条件输出一个空的第三区会当场打红 g64 那两条
    「恰好等于」的计数断言, 而那两条不该为了本卡被放宽); 推迟一块板之后
    恰好 +1。
    """
    root, client, runner, mod = board_done_env
    _mk_vault(root, "vault-sp", _two_board_projection("vault-sp", _now_local().isoformat(timespec="seconds")))
    _pin_now(monkeypatch, mod, "2026-09-09T10:00:00")

    page = client.get(_PAGE_URL).text
    folds_before = page.count("<details")
    assert "已推迟（" not in page, "还没推迟就不该有已推迟区"

    assert (
        client.post(_BOARD_SNOOZE_URL, data={"vault_id": "vault-sp", "board": "CS 61B", "until": "tonight"}).status_code
        == 200
    )

    page2 = client.get(_PAGE_URL).text
    assert page2.count("<details") == folds_before + 1, "「已推迟」区恰好多出一个折叠区, 不多不少"
    i = page2.index("已推迟（1）")
    head, fold = page2[:i], page2[i:]
    assert "数学" in head and "CS 61B" not in head, "被推迟的板应从待做区移出"
    assert "CS 61B" in fold, "被推迟的板必须仍在页面上 (折叠区内), 不许被剔除"
    assert fold.count(f'action="{_BOARD_SNOOZE_URL}"') == 0, "已推迟的板不该再带推迟钮"
    assert head.count(f'action="{_BOARD_SNOOZE_URL}"') == 1, "未推迟的板仍要带推迟钮"
    assert fold.count(f'action="{_BOARD_UNSNOOZE_URL}"') == 1, "已推迟区必须给一个取回的出口"
    # 投影本体一个数都没动 (硬边界: 禁在投影层压制)
    entry = next(v for v in client.get("/api/v1/review/overview").json()["vaults"] if v["vault_id"] == "vault-sp")
    assert entry["projection"]["due_count"] == 2
    assert sorted(r["board"] for r in entry["projection"]["boards"]) == ["CS 61B", "数学"]


def test_g66_unsnooze_is_idempotent_and_brings_the_board_back(board_done_env, monkeypatch):
    """(h) 取回: 同 board-undone 形态 —— 幂等 200 + already_unsnoozed, 不 404。

    误点之后唯一的恢复途径不该是"等到点"。本来就没有时**不改写 state**:
    一次无事可做的撤销不该动 state 的字节与 mtime。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-un", {"甲": _node_md()})
    _pin_now(monkeypatch, mod, "2026-09-09T10:00:00")
    state_file = runner.state_path(vault)

    # 本来就没有 → 幂等 200, 且 state 不被改写
    before = state_file.read_bytes() if state_file.exists() else None
    first = client.post(_BOARD_UNSNOOZE_URL, data={"vault_id": "vault-un", "board": "CS 61B"})
    assert first.status_code == 200, first.text
    assert first.json()["already_unsnoozed"] is True and first.json()["fsrs_touched"] is False
    after = state_file.read_bytes() if state_file.exists() else None
    assert after == before, "无事可做的取回不许动 state 的字节"

    assert (
        client.post(_BOARD_SNOOZE_URL, data={"vault_id": "vault-un", "board": "CS 61B", "until": "tonight"}).status_code
        == 200
    )
    real = client.post(_BOARD_UNSNOOZE_URL, data={"vault_id": "vault-un", "board": "CS 61B"})
    assert real.status_code == 200 and real.json()["already_unsnoozed"] is False
    assert _state_of(runner, Path(root), "vault-un")["snoozed"] == {}, "取回必须真的摘掉那个键"
    entry = next(v for v in client.get("/api/v1/review/overview").json()["vaults"] if v["vault_id"] == "vault-un")
    assert entry["snoozed"] == {}


def test_g66_snooze_is_per_vault(board_done_env, monkeypatch):
    """(g)⑨ 双库互不影响 (沿 test_g67_done_expires_next_day_and_is_per_vault)。"""
    root, client, runner, mod = board_done_env
    _mk_node_vault(root, "vault-a", {"甲": _node_md()})
    _mk_node_vault(root, "vault-b", {"乙": _node_md()})
    _pin_now(monkeypatch, mod, "2026-09-09T10:00:00")

    assert (
        client.post(_BOARD_SNOOZE_URL, data={"vault_id": "vault-a", "board": "CS 61B", "until": "tonight"}).status_code
        == 200
    )
    vaults = {v["vault_id"]: v for v in client.get("/api/v1/review/overview").json()["vaults"]}
    assert set(vaults["vault-a"]["snoozed"]) == {"CS 61B"}
    assert vaults["vault-b"]["snoozed"] == {}, "另一个库的推迟账必须完全独立"


def test_g66_fsrs_gate_reddens_under_contaminating_snooze_write_point(board_done_env, monkeypatch):
    """(g)⑤ 常驻负控: 换上「顺手写 fsrs_due」的推迟写点, 上面那道门必须红。

    判据绑定到**具体那一条**断言 (_FSRS_GATE_MSG), 不是"某处失败了" ——
    变异体若因语法 / 路径坏掉而让别的断言先红, 本门同样不放行。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-sneg", {"定义甲": _node_md(fsrs_due='"2099-01-01T00:00:00Z"')})

    real = mod._write_board_snooze

    def contaminated(vault_dir, vaults_root, board, until_iso):
        state_file = real(vault_dir, vaults_root, board, until_iso)
        target = sorted((vault / "节点").glob("*.md"))[0]
        text = target.read_text(encoding="utf-8")
        target.write_text(text.replace("fsrs_due:", "fsrs_due: # 顺手改\nfsrs_due_shadow:"), encoding="utf-8")
        return state_file

    monkeypatch.setattr(mod, "_write_board_snooze", contaminated)

    before = _fsrs_fingerprint(vault)
    resp = client.post(_BOARD_SNOOZE_URL, data={"vault_id": "vault-sneg", "board": "CS 61B", "until": "tomorrow"})
    assert resp.status_code == 200, "对照写点只污染 FSRS, 不许把请求本身弄坏 (否则红的是别的东西)"
    assert set(_state_of(runner, Path(root), "vault-sneg")["snoozed"]) == {"CS 61B"}, (
        "对照写点必须仍然把推迟账写对 —— 拆的只是那一条守卫"
    )
    with pytest.raises(AssertionError) as ei:
        _assert_fsrs_untouched(before, _fsrs_fingerprint(vault))
    assert _FSRS_GATE_MSG in str(ei.value), f"红的不是 FSRS 那条断言: {ei.value}"


def test_g66_end_to_end_snooze_yields_top_slot_in_the_real_projection(board_done_env, monkeypatch):
    """(g)① 端到端: 推迟 → refresh → 真投影里让出榜首, 但**行、桶、合计一个不动**。

    这条把 Web 写侧、runner state、生产器让位、页面读侧串成一条 —— 单元门
    各自绿着但接线断了 (M-1 那次: runner 修了、CLI 没修, 于是浏览器上点
    「重新算一遍」榜首不让位) 正是这条要抓的形态。

    ⛔ 硬边界一起验: 让位不许从 boards / stats 里剔行改数 (投影层压制会当场
    撞 _gate_buckets 的「到期三桶合计恒等 stats.due_nodes」)。
    """
    root, client, runner, mod = board_done_env
    monkeypatch.setattr(mod, "_REFRESH_TTL_SECONDS", 0.0)
    vault = _mk_node_vault(
        root,
        "vault-e2e",
        {
            "定义甲": _node_md(board="CS 61B", fsrs_due='"2020-01-01T00:00:00Z"'),
            "定义乙": _node_md(board="CS 61B", fsrs_due='"2020-01-01T00:00:00Z"'),
            "定义丙": _node_md(board="数学", fsrs_due='"2020-01-01T00:00:00Z"'),
        },
    )
    proj_path = vault / "outputs" / "今日复习.json"
    # ⛔ 端点与生产器子进程**两侧一起钉**。初版只钉端点那一侧, 于是写出的
    #    until=2026-09-09T20:00+08:00 在子进程的真实墙钟下 09-11 起已过期 ——
    #    本门 2026-09-11 自己红成 `assert 'CS 61B' != 'CS 61B'`, 代码一字未改。
    #    理由与"为什么不给生产加旗标"见 _pin_child_now 的 docstring。
    pinned = _pin_now(monkeypatch, mod, "2026-09-09T10:00:00")
    seen = _pin_child_now(monkeypatch, mod, pinned)

    assert client.post(_REFRESH_URL, data={"vault_id": "vault-e2e"}).status_code == 200
    before = json.loads(proj_path.read_text(encoding="utf-8"))
    first = before["top_boards"][0]["board"]
    assert len(before["top_boards"]) >= 2, "前提: 榜上要有两块板才谈得上让位"

    assert (
        client.post(_BOARD_SNOOZE_URL, data={"vault_id": "vault-e2e", "board": first, "until": "tonight"}).status_code
        == 200
    )
    assert client.post(_REFRESH_URL, data={"vault_id": "vault-e2e"}).status_code == 200
    _assert_child_now_pinned(seen, pinned, expected_runs=2)

    after = json.loads(proj_path.read_text(encoding="utf-8"))
    assert after["top_boards"][0]["board"] != first, "被推迟的板必须让出榜首"
    assert first in [r["board"] for r in after["top_boards"]], "让位不是除名 —— 它仍在榜上"
    assert after["stats"] == before["stats"], "推迟不许动任何统计口径"
    assert sorted(r["board"] for r in after["boards"]) == sorted(r["board"] for r in before["boards"])
    assert after["buckets"] == before["buckets"], "五桶划分与推迟无关"
    # GET 侧: _gate_buckets 仍 PASS (它是 status ok 的前提), 且数字与盘上同源
    entry = next(v for v in client.get("/api/v1/review/overview").json()["vaults"] if v["vault_id"] == "vault-e2e")
    assert entry["status"] == "ok", f"投影必须仍能通过合计恒等门: {entry.get('error')}"
    assert entry["projection"]["due_count"] == after["stats"]["due_nodes"] == 3
    assert set(entry["snoozed"]) == {first}


@pytest.mark.parametrize("when", ["2020-01-02T10:00:00", "2026-09-09T10:00:00", "2099-12-30T10:00:00"])
def test_g66_e2e_snooze_verdict_is_clock_independent(board_done_env, monkeypatch, when):
    """(g)① 的判定必须与**真实墙钟**无关 —— 这是上面那条门自己红过一次之后的修法证据。

    上面那条端到端门曾经只钉端点一侧: 写出 until=2026-09-09T20:00+08:00, 而
    生产器子进程按真实墙钟判活跃。它 2026-09-09 白天绿、2026-09-11 自己红,
    代码一个字没改 —— 一颗定时哑弹。本门把同一条核心性质放在**相距 79 年**
    的三个 pinned 值上跑: 全绿 ⇒ 判定不依赖"今天是哪天", 那类哑弹装不回来。

    ⚠ 只验让位这一条 (行/桶/合计/GET 侧由上面那条端到端门负责) —— 同一组断言
    写两遍早晚漂移成两份, 代价见 daily_review_run.save_state 的注释。
    ⚠ 夹具 fsrs_due 取 2019: 三个 pinned 值里最早的是 2020, 节点必须在**每**一个
      参照时刻上都已到期, 否则某一参数下"榜上没有两块板"会让本门红在别处。
    """
    # runner 槽本门用不上 —— 下划线前缀是本文件既有写法 (沿 test_g67r_state_passed_*
    # 的 `_mod`), 免得给 pyright 添一条与本门无关的 reportUnusedVariable。
    root, client, _runner, mod = board_done_env
    monkeypatch.setattr(mod, "_REFRESH_TTL_SECONDS", 0.0)
    vault = _mk_node_vault(
        root,
        "vault-clockfree",
        {
            "定义甲": _node_md(board="CS 61B", fsrs_due='"2019-01-01T00:00:00Z"'),
            "定义乙": _node_md(board="CS 61B", fsrs_due='"2019-01-01T00:00:00Z"'),
            "定义丙": _node_md(board="数学", fsrs_due='"2019-01-01T00:00:00Z"'),
        },
    )
    proj_path = vault / "outputs" / "今日复习.json"
    pinned = _pin_now(monkeypatch, mod, when)
    seen = _pin_child_now(monkeypatch, mod, pinned)

    assert client.post(_REFRESH_URL, data={"vault_id": "vault-clockfree"}).status_code == 200
    before = json.loads(proj_path.read_text(encoding="utf-8"))
    first = before["top_boards"][0]["board"]
    assert len(before["top_boards"]) >= 2, f"pinned={when} 前提: 榜上要有两块板才谈得上让位"

    resp = client.post(_BOARD_SNOOZE_URL, data={"vault_id": "vault-clockfree", "board": first, "until": "tonight"})
    assert resp.status_code == 200, resp.text
    assert client.post(_REFRESH_URL, data={"vault_id": "vault-clockfree"}).status_code == 200
    _assert_child_now_pinned(seen, pinned, expected_runs=2)

    after = json.loads(proj_path.read_text(encoding="utf-8"))
    assert after["top_boards"][0]["board"] != first, f"pinned={when}: 被推迟的板必须让出榜首"
    assert first in [r["board"] for r in after["top_boards"]], f"pinned={when}: 让位不是除名"


def test_g66_unencodable_snoozed_key_does_not_500_the_whole_overview(board_done_env, monkeypatch):
    """(Codex round-1 MEDIUM-2) 不可编码的推迟板名不许把**整个**总览 GET 打成 500。

    JSON 的 `\\ud800` 转义解出的是孤立 surrogate —— 它是合格的 `str`, 过得了
    `isinstance` 的门, 却在响应做 UTF-8 序列化时才抛 UnicodeEncodeError。那一刻
    已经出了 `_collect` 的单库兜底（`except Exception` 包的是 `_vault_entry`
    那一层），于是**别的库也一起看不成**。projection 那一侧早有同款门。

    两条一起才说明得了问题:
      ① 请求仍是 200，且**另一个健康的库照常出现**（不是整页降级）;
      ② 坏条目被丢弃，好条目留下（不是把整个 snoozed 清空了事）。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-sur", {"甲": _node_md()})
    _mk_node_vault(root, "vault-ok", {"乙": _node_md()})
    _pin_now(monkeypatch, mod, "2026-09-09T10:00:00")

    state_file = runner.state_path(vault)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        '{"schema_version": 3, "board_last_recommended": {}, "board_done": {}, '
        '"snoozed": {"\\ud800": "2099-09-09T20:00:00+08:00", "CS 61B": "2099-09-09T20:00:00+08:00"}}',
        encoding="utf-8",
    )
    # 夹具前提: 那个键真的是解得出、却编不出 UTF-8 的孤立 surrogate
    raw = json.loads(state_file.read_text(encoding="utf-8"))
    assert any(isinstance(k, str) and not _utf8_encodable(k) for k in raw["snoozed"]), (
        "夹具前提: state 里必须真的有一个编不出 UTF-8 的键, 否则本门是空的"
    )

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200, f"一个坏板名不许把整个总览打成 500: {resp.text[:200]}"
    vaults = {v["vault_id"]: v for v in resp.json()["vaults"]}
    assert "vault-ok" in vaults, "别的库必须照常出现"
    assert set(vaults["vault-sur"]["snoozed"]) == {"CS 61B"}, "坏条目丢弃、好条目留下"

    # 页面路径同样不许 500
    assert client.get(_PAGE_URL).status_code == 200


def _utf8_encodable(s: str) -> bool:
    try:
        s.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def test_g66_encodable_filter_does_not_harm_cjk_or_emoji_board_names(board_done_env, monkeypatch):
    """(Codex round-1 MEDIUM-2 的配套) 那道编码过滤**不许误伤合法的非 ASCII 板名**。

    ⛔ 这条是修复本身的负控。本项目的板名主流就是中文（「图论基础」「数学」），
    修 surrogate 时顺手把非 ASCII 一起挡掉，会是一个**本卡引入的功能性缺陷**，
    而且只在真实数据上才看得见 —— 上面那条门用的是 "CS 61B"（纯 ASCII），
    它绿着证明不了这件事。

    三类各一条: 中文 / emoji / 带重音符的拉丁字母。
    """
    root, client, runner, mod = board_done_env
    vault = _mk_node_vault(root, "vault-cjk", {"甲": _node_md()})
    _pin_now(monkeypatch, mod, "2026-09-09T10:00:00")

    names = ["图论基础", "数学 📐", "Café 复习"]
    until = "2099-09-09T20:00:00+08:00"
    state_file = runner.state_path(vault)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps(
            {
                "schema_version": runner.STATE_SCHEMA_VERSION,
                "board_last_recommended": {},
                "board_done": {},
                "snoozed": {n: until for n in names},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert set(mod._read_snoozed(state_file)) == set(names), "编码过滤误伤了合法的非 ASCII 板名"
    entry = next(v for v in client.get("/api/v1/review/overview").json()["vaults"] if v["vault_id"] == "vault-cjk")
    assert set(entry["snoozed"]) == set(names), "三类非 ASCII 板名都必须原样投影出来"
    # 页面不在本门的作用面内: 「已推迟」区只渲染**投影 boards 里存在**的板, 而本夹具的
    # 投影里没有这三块 —— 那时不渲染是正确行为, 与编码过滤无关。页面侧的板名渲染由
    # test_g66_page_folds_snoozed_board_without_dropping_it 覆盖。
    assert client.get(_PAGE_URL).status_code == 200, "非 ASCII 板名不许把页面打成 500"
