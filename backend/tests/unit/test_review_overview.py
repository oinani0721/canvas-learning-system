"""跨 vault 复习总览聚合 (CARD-C2, BATCH-2026-08-25-跨vault与收束)。

四类锁定: 聚合正确 / 缺投影显式降级 / 损坏 JSON 不 500 / stale 徽标。
CARD-D1 (BATCH-2026-08-27-Anki化与诚实收尾) 追加: 板级聚合与 stats 自洽 /
due_nodes 脏行 corrupt 降级 / Asia/Shanghai 时间人话化 / 无投影深链降级。
CARD-G3-6a (BATCH-2026-08-29-第六批) 追加: 五桶分层计数消费与跨源门禁。
真实文件 fixture: tmp_path 里建真 vault 目录 (.obsidian + outputs/今日复习.json
真文件), settings 走 reload_settings 真实配置机器 — 禁 mock 文件系统语义。
"""

import hashlib
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
    """真目录 + 真文件 — 不 mock 任何文件系统语义。"""
    vault = root / name
    (vault / ".obsidian").mkdir(parents=True)
    if raw is not None or projection is not None:
        (vault / "outputs").mkdir()
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


def test_buckets_gate_accepts_real_producer_payload(tmp_path, overview_env):
    """假阳性防线 (Codex round-2 C/D): 不用手搓 fixture —— 直接跑真生产器
    daily_review_pick.build_payload 产出投影, 落成真文件后过总览端点, 必须
    ok 且分层计数与生产器 buckets 逐字相等。门禁若把生产器真实产出判成
    corrupt, 本用例立刻红。"""
    import shutil
    import sys
    from pathlib import Path

    wt = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(wt / "scripts"))
    import daily_review_pick as picker

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
    vault = _mk_node_vault(root, "vault-w", {"甲": _node_md(), "乙": _node_md(board="数学")})

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
        for i in range(12):
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

    for headers in (
        {"Sec-Fetch-Site": "cross-site"},
        {"Origin": "https://evil.example.com"},
        {"Sec-Fetch-Site": "same-site", "Origin": "http://attacker.testserver"},
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
    assert env.get("TZ") == "Asia/Shanghai", "时区要透传 — 本地日语义得与宿主一致"

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

    assert "学习中" in page and "新卡" in page, "桶位要显示中文标签, 不是机器枚举名"
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
    assert "%2F" in expect, "路径分隔符必须编码 (safe='')"
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
    # 桶位小标签有专属样式串; 旧投影下一个都不该出现 (卡片汇总行的"新卡 N"
    # 是另一处文案, 用样式串定位可精确区分)
    assert "border-radius:4px;padding:0 6px;font-size:11px" not in page, "旧投影不许出现伪造的桶位小标签"
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
    now_iso = _now_local().isoformat(timespec="seconds")
    _mk_vault(root, "vault-ok", _nodes_projection("vault-ok", [_due_row("好节点", "甲板")]))

    hostile = {
        "bad-bucket-enum": _due_row("n", "甲板", bucket="不是桶名"),
        "bad-bucket-type": _due_row("n", "甲板", bucket=3),
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
        "bad-why-type": _due_row("n", "甲板", why_due=["列表"]),
        "bad-why-null-but-bucket": _due_row("n", "甲板", why_due=None),
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
        assert set(b) == {"board", "due", "due_new", "placeholder", "earliest", "nodes"}, (
            f"boards 行只许加性追加 nodes, 实为 {sorted(b)}"
        )
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

    root, client = refresh_env
    _mk_node_vault(root, "vault-host", {"甲": _node_md()})
    from fastapi.testclient import TestClient

    from app.main import app

    for base, ok in (
        ("http://127.0.0.1:8011", True),
        ("http://localhost:8011", True),
        ("http://192.168.1.9:8011", True),  # 手机按局域网 IP 打开, 必须照常可用
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
    # 非生产缺陷), 所以直接验判据本身 —— starlette 的 URL.hostname 会把方括号
    # 脱掉给出 "::1", ip_address 认得它
    import ipaddress as _ip

    assert _ip.ip_address("::1")

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
